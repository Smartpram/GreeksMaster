#!/usr/bin/env python3
"""
VWAP-Based Intraday Strategy Implementation
Uses Volume Weighted Average Price for institutional-style execution
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class VWAPConfig:
    """Configuration for VWAP Strategy"""
    
    # VWAP Parameters
    VWAP_PERIOD: int = 20             # Rolling VWAP period
    VWAP_DEVIATION_BANDS: float = 0.5 # Standard deviation bands
    
    # Price-VWAP Relationship
    MIN_PRICE_ABOVE_VWAP: float = 0.002   # Min 0.2% above VWAP for long
    MAX_PRICE_ABOVE_VWAP: float = 0.015   # Max 1.5% above VWAP for entry
    VWAP_TREND_THRESHOLD: float = 0.001   # VWAP trending up by 0.1%
    
    # Volume Parameters
    MIN_VOLUME_RATIO: float = 1.5     # 50% above average volume
    VOLUME_SPIKE_THRESHOLD: float = 3.0 # 3x volume spike confirmation
    
    # Intraday Time Filters
    TRADING_START_HOUR: int = 9       # 9:30 AM
    TRADING_START_MINUTE: int = 30
    TRADING_END_HOUR: int = 15        # 3:00 PM
    TRADING_END_MINUTE: int = 0
    AVOID_FIRST_MINUTES: int = 15     # Avoid first 15 minutes
    AVOID_LAST_MINUTES: int = 30      # Avoid last 30 minutes
    
    # Position Management
    MAX_POSITION_SIZE: float = 0.05   # 5% per position (intraday)
    STOP_LOSS_PCT: float = 0.015      # 1.5% stop loss (tight for intraday)
    TARGET_PCT: float = 0.03          # 3% target (realistic for intraday)
    
    # Risk Management
    MAX_OPEN_POSITIONS: int = 3       # Limited for intraday
    MAX_DAILY_TRADES: int = 5         # Limit overtrading
    MIN_VWAP_SCORE: float = 0.8       # High threshold for quality

class VWAPStrategy:
    """
    VWAP-Based Intraday Strategy for Institutional-Style Execution
    
    Entry Conditions:
    1. Price > VWAP with rising volume
    2. VWAP trending upward
    3. Volume above average with institutional participation
    4. Within trading hours (avoid open/close volatility)
    
    Exit Conditions:
    1. Price falls below VWAP
    2. Volume declining significantly
    3. End of trading day approach
    4. Stop loss or target hit
    """
    
    def __init__(self, config: VWAPConfig = None):
        self.config = config or VWAPConfig()
        self.positions = {}
        self.daily_trades = 0
        self.last_reset_date = datetime.now().date()
        self.name = "VWAP Intraday Strategy"
        
        logger.info(f"Initialized {self.name}")
        logger.info(f"Parameters: VWAP period {self.config.VWAP_PERIOD}, "
                   f"Target {self.config.TARGET_PCT:.1%}")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate VWAP and related indicators"""
        
        # Standard VWAP calculation
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['volume_price'] = df['typical_price'] * df['volume']
        
        # Rolling VWAP
        df['cum_volume_price'] = df['volume_price'].rolling(window=self.config.VWAP_PERIOD).sum()
        df['cum_volume'] = df['volume'].rolling(window=self.config.VWAP_PERIOD).sum()
        df['vwap'] = df['cum_volume_price'] / df['cum_volume']
        
        # Intraday VWAP (reset daily)
        df['date'] = pd.to_datetime(df.index).date if isinstance(df.index, pd.DatetimeIndex) else df.index.date
        
        # Calculate daily VWAP
        df['daily_cum_volume_price'] = df.groupby('date')['volume_price'].cumsum()
        df['daily_cum_volume'] = df.groupby('date')['volume'].cumsum()
        df['daily_vwap'] = df['daily_cum_volume_price'] / df['daily_cum_volume']
        
        # VWAP deviation bands
        df['vwap_std'] = df['typical_price'].rolling(window=self.config.VWAP_PERIOD).std()
        df['vwap_upper'] = df['vwap'] + (df['vwap_std'] * self.config.VWAP_DEVIATION_BANDS)
        df['vwap_lower'] = df['vwap'] - (df['vwap_std'] * self.config.VWAP_DEVIATION_BANDS)
        
        # Price-VWAP relationship
        df['price_vwap_ratio'] = df['close'] / df['vwap']
        df['price_above_vwap'] = (df['close'] - df['vwap']) / df['vwap']
        
        # VWAP trend
        df['vwap_trend'] = df['vwap'].pct_change(5)  # 5-period VWAP trend
        df['vwap_slope'] = df['vwap'].diff() / df['vwap'].shift(1)
        
        # Volume analysis
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Volume-weighted momentum
        df['vw_momentum'] = (df['close'] - df['close'].shift(5)) * df['volume_ratio']
        
        # VWAP cross signals
        df['price_cross_vwap'] = np.where(
            (df['close'] > df['vwap']) & (df['close'].shift(1) <= df['vwap'].shift(1)), 1,
            np.where((df['close'] < df['vwap']) & (df['close'].shift(1) >= df['vwap'].shift(1)), -1, 0)
        )
        
        # Time-based filters
        df = self.add_time_filters(df)
        
        # VWAP score
        df['vwap_score'] = self.calculate_vwap_score(df)
        
        return df
    
    def add_time_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add intraday time-based filters"""
        
        # Add time information (assuming timestamp index or time column)
        if isinstance(df.index, pd.DatetimeIndex):
            df['hour'] = df.index.hour
            df['minute'] = df.index.minute
        else:
            # If no time information, assume all times are valid for backtesting
            df['hour'] = 10  # Default to mid-morning
            df['minute'] = 0
        
        # Trading session filters
        trading_start = self.config.TRADING_START_HOUR * 60 + self.config.TRADING_START_MINUTE
        trading_end = self.config.TRADING_END_HOUR * 60 + self.config.TRADING_END_MINUTE
        current_time = df['hour'] * 60 + df['minute']
        
        # Valid trading time
        df['valid_trading_time'] = (
            (current_time >= trading_start + self.config.AVOID_FIRST_MINUTES) & 
            (current_time <= trading_end - self.config.AVOID_LAST_MINUTES)
        )
        
        # Avoid opening volatility
        df['avoid_open'] = current_time < trading_start + self.config.AVOID_FIRST_MINUTES
        
        # Avoid closing volatility
        df['avoid_close'] = current_time > trading_end - self.config.AVOID_LAST_MINUTES
        
        return df
    
    def calculate_vwap_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate VWAP strategy score (0-1)"""
        
        score = pd.Series(0.0, index=df.index)
        
        # Price-VWAP relationship (40% weight)
        price_vwap_score = pd.Series(0.0, index=df.index)
        
        # Ideal when price is slightly above VWAP (institutional buying interest)
        optimal_above = (df['price_above_vwap'] > self.config.MIN_PRICE_ABOVE_VWAP) & \
                       (df['price_above_vwap'] < self.config.MAX_PRICE_ABOVE_VWAP)
        price_vwap_score = np.where(optimal_above, 1.0, 0)
        
        # Penalty for being too far from VWAP
        too_far = abs(df['price_above_vwap']) > self.config.MAX_PRICE_ABOVE_VWAP
        price_vwap_score = np.where(too_far, 0, price_vwap_score)
        
        score += pd.Series(price_vwap_score, index=df.index) * 0.4
        
        # VWAP trend (25% weight)
        vwap_trend_score = np.where(
            df['vwap_trend'] > self.config.VWAP_TREND_THRESHOLD, 1.0,
            np.where(df['vwap_trend'] > 0, df['vwap_trend'] / self.config.VWAP_TREND_THRESHOLD, 0)
        )
        score += pd.Series(vwap_trend_score, index=df.index) * 0.25
        
        # Volume confirmation (25% weight)
        volume_score = np.minimum(df['volume_ratio'] / 3.0, 1.0)  # Normalize to 3x average
        score += volume_score * 0.25
        
        # Time validity (10% weight)
        time_score = df['valid_trading_time'].astype(float)
        score += time_score * 0.10
        
        return np.minimum(score, 1.0)
    
    def should_enter_long(self, symbol: str, row: pd.Series, portfolio_value: float) -> Tuple[bool, str]:
        """Check if should enter long position"""
        
        # Reset daily trade counter
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_trades = 0
            self.last_reset_date = current_date
        
        # Already have position
        if symbol in self.positions:
            return False, "Already have position"
        
        # Max positions check
        if len(self.positions) >= self.config.MAX_OPEN_POSITIONS:
            return False, "Max positions reached"
        
        # Daily trade limit
        if self.daily_trades >= self.config.MAX_DAILY_TRADES:
            return False, "Daily trade limit reached"
        
        # Check VWAP score
        if row['vwap_score'] < self.config.MIN_VWAP_SCORE:
            return False, f"VWAP score {row['vwap_score']:.2f} below threshold"
        
        # Time filter - must be valid trading time
        if not row['valid_trading_time']:
            return False, "Outside valid trading hours"
        
        # Primary VWAP conditions
        # Price above VWAP but not too far
        if row['price_above_vwap'] < self.config.MIN_PRICE_ABOVE_VWAP:
            return False, f"Price {row['price_above_vwap']:.3f} not sufficiently above VWAP"
        
        if row['price_above_vwap'] > self.config.MAX_PRICE_ABOVE_VWAP:
            return False, f"Price {row['price_above_vwap']:.3f} too far above VWAP"
        
        # VWAP trending upward
        if row['vwap_trend'] < self.config.VWAP_TREND_THRESHOLD:
            return False, f"VWAP trend {row['vwap_trend']:.4f} insufficient"
        
        # Volume confirmation
        if row['volume_ratio'] < self.config.MIN_VOLUME_RATIO:
            return False, f"Volume ratio {row['volume_ratio']:.2f} insufficient"
        
        # Recent VWAP cross (bullish signal)
        if row['price_cross_vwap'] == -1:  # Just crossed below
            return False, "Recent bearish VWAP cross"
        
        return True, f"VWAP long signal: {row['vwap_score']:.2f}"
    
    def should_enter_short(self, symbol: str, row: pd.Series, portfolio_value: float) -> Tuple[bool, str]:
        """Check if should enter short position"""
        
        # Reset daily trade counter
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_trades = 0
            self.last_reset_date = current_date
        
        # Already have position
        if symbol in self.positions:
            return False, "Already have position"
        
        # Max positions check
        if len(self.positions) >= self.config.MAX_OPEN_POSITIONS:
            return False, "Max positions reached"
        
        # Daily trade limit
        if self.daily_trades >= self.config.MAX_DAILY_TRADES:
            return False, "Daily trade limit reached"
        
        # Time filter
        if not row['valid_trading_time']:
            return False, "Outside valid trading hours"
        
        # Primary VWAP conditions for short
        # Price below VWAP
        if row['price_above_vwap'] > -self.config.MIN_PRICE_ABOVE_VWAP:
            return False, f"Price {row['price_above_vwap']:.3f} not sufficiently below VWAP"
        
        # VWAP trending downward
        if row['vwap_trend'] > -self.config.VWAP_TREND_THRESHOLD:
            return False, f"VWAP not trending down sufficiently"
        
        # Volume confirmation
        if row['volume_ratio'] < self.config.MIN_VOLUME_RATIO:
            return False, f"Volume ratio {row['volume_ratio']:.2f} insufficient"
        
        # Recent bearish VWAP cross
        if row['price_cross_vwap'] == 1:  # Just crossed above
            return False, "Recent bullish VWAP cross"
        
        return True, f"VWAP short signal"
    
    def should_exit_position(self, symbol: str, row: pd.Series, position: Dict) -> Tuple[bool, str]:
        """Check if should exit position"""
        
        current_price = row['close']
        entry_price = position['entry_price']
        position_type = position.get('type', 'long')
        
        if position_type == 'long':
            current_return = (current_price - entry_price) / entry_price
        else:  # short
            current_return = (entry_price - current_price) / entry_price
        
        # Stop loss (tight for intraday)
        if current_return <= -self.config.STOP_LOSS_PCT:
            return True, "stop_loss"
        
        # Target achievement
        if current_return >= self.config.TARGET_PCT:
            return True, "target_achieved"
        
        # End of trading day approach
        if row['avoid_close']:
            return True, "end_of_day_exit"
        
        # VWAP-specific exits
        if position_type == 'long':
            # Price crosses below VWAP
            if row['price_cross_vwap'] == -1:
                return True, "vwap_cross_below"
            
            # Price significantly below VWAP
            if row['price_above_vwap'] < -self.config.MIN_PRICE_ABOVE_VWAP:
                return True, "price_below_vwap"
            
            # VWAP trend turning negative
            if row['vwap_trend'] < -self.config.VWAP_TREND_THRESHOLD:
                return True, "vwap_trend_bearish"
        
        else:  # short position
            # Price crosses above VWAP
            if row['price_cross_vwap'] == 1:
                return True, "vwap_cross_above"
            
            # Price significantly above VWAP
            if row['price_above_vwap'] > self.config.MIN_PRICE_ABOVE_VWAP:
                return True, "price_above_vwap"
            
            # VWAP trend turning positive
            if row['vwap_trend'] > self.config.VWAP_TREND_THRESHOLD:
                return True, "vwap_trend_bullish"
        
        # Volume declining (institutional interest waning)
        if row['volume_ratio'] < 0.8:  # Below 80% of average
            return True, "volume_decline"
        
        return False, "hold"
    
    def get_position_size(self, symbol: str, price: float, portfolio_value: float, 
                         vwap_score: float) -> int:
        """Calculate position size (smaller for intraday)"""
        
        # Base position size (smaller for intraday trading)
        base_size = portfolio_value * self.config.MAX_POSITION_SIZE
        
        # Adjust based on VWAP score
        score_multiplier = 0.7 + (vwap_score * 0.3)  # 0.7x to 1.0x
        adjusted_size = base_size * score_multiplier
        
        return max(1, int(adjusted_size / price))
    
    def execute_trade(self, symbol: str, action: str) -> bool:
        """Execute trade and update daily counter"""
        
        # Increment daily trade counter
        self.daily_trades += 1
        
        logger.info(f"VWAP trade executed: {action} {symbol} (Daily trades: {self.daily_trades})")
        return True
    
    def get_vwap_analysis(self, row: pd.Series) -> Dict:
        """Get detailed VWAP analysis"""
        
        return {
            'vwap_score': row['vwap_score'],
            'price_above_vwap': row['price_above_vwap'],
            'vwap_trend': row['vwap_trend'],
            'volume_ratio': row['volume_ratio'],
            'valid_trading_time': row['valid_trading_time'],
            'price_cross_signal': row['price_cross_vwap'],
            'vwap_level': row['vwap'],
            'current_price': row['close']
        }
    
    def get_strategy_info(self) -> Dict:
        """Get strategy information"""
        return {
            'name': self.name,
            'type': 'Intraday/VWAP',
            'timeframe': 'Intraday (minutes to hours)',
            'best_markets': 'High volume, liquid instruments',
            'parameters': {
                'vwap_period': self.config.VWAP_PERIOD,
                'min_price_above_vwap': self.config.MIN_PRICE_ABOVE_VWAP,
                'volume_threshold': self.config.MIN_VOLUME_RATIO,
                'target_pct': self.config.TARGET_PCT
            },
            'current_positions': len(self.positions),
            'daily_trades': self.daily_trades,
            'max_daily_trades': self.config.MAX_DAILY_TRADES
        }