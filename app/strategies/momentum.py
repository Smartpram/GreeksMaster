#!/usr/bin/env python3
"""
Momentum Strategy Implementation
Uses RSI, MACD, and Price momentum for momentum-based trading
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MomentumConfig:
    """Configuration for Momentum Strategy"""
    
    # RSI Parameters
    RSI_PERIOD: int = 14
    RSI_MOMENTUM_THRESHOLD: int = 60  # RSI > 60 for bullish momentum
    RSI_STRONG_MOMENTUM: int = 70     # RSI > 70 for strong momentum
    RSI_WEAK_THRESHOLD: int = 40      # RSI < 40 for bearish momentum
    
    # MACD Parameters
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9
    
    # Price Momentum Parameters
    SHORT_MOMENTUM_PERIOD: int = 5    # 5-day momentum
    MEDIUM_MOMENTUM_PERIOD: int = 14  # 14-day momentum
    LONG_MOMENTUM_PERIOD: int = 30    # 30-day momentum
    
    # Momentum Thresholds
    MIN_SHORT_MOMENTUM: float = 0.03  # 3% in 5 days
    MIN_MEDIUM_MOMENTUM: float = 0.08 # 8% in 14 days
    MIN_LONG_MOMENTUM: float = 0.15   # 15% in 30 days
    
    # Volume Momentum
    VOLUME_MOMENTUM_PERIOD: int = 10
    MIN_VOLUME_GROWTH: float = 1.5    # 50% volume increase
    
    # Position Management
    MAX_POSITION_SIZE: float = 0.12   # 12% per position (higher for momentum)
    STOP_LOSS_PCT: float = 0.08       # 8% stop loss (wider for momentum)
    TARGET_PCT: float = 0.25          # 25% target (higher for momentum)
    TRAILING_STOP_PCT: float = 0.05   # 5% trailing stop
    
    # Risk Management
    MAX_OPEN_POSITIONS: int = 5
    MIN_MOMENTUM_SCORE: float = 0.75
    
    # Market Condition Filters
    MIN_VOLATILITY: float = 0.02      # Minimum 2% volatility for momentum

class MomentumStrategy:
    """
    Momentum Strategy for Strong Trending Moves
    
    Entry Conditions:
    1. RSI > 60 (bullish momentum)
    2. MACD bullish crossover with rising histogram
    3. Strong price momentum across multiple timeframes
    4. Volume momentum confirmation
    
    Exit Conditions:
    1. RSI falls below momentum threshold
    2. MACD bearish crossover
    3. Price momentum deteriorating
    4. Stop loss or target hit
    """
    
    def __init__(self, config: MomentumConfig = None):
        self.config = config or MomentumConfig()
        self.positions = {}
        self.name = "Momentum Strategy"
        
        logger.info(f"Initialized {self.name}")
        logger.info(f"Parameters: RSI threshold {self.config.RSI_MOMENTUM_THRESHOLD}, "
                   f"Min momentum {self.config.MIN_SHORT_MOMENTUM:.1%}")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators"""
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.config.RSI_PERIOD).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.config.RSI_PERIOD).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=self.config.MACD_FAST).mean()
        exp2 = df['close'].ewm(span=self.config.MACD_SLOW).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=self.config.MACD_SIGNAL).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Price Momentum (multiple timeframes)
        df['momentum_5d'] = df['close'].pct_change(self.config.SHORT_MOMENTUM_PERIOD)
        df['momentum_14d'] = df['close'].pct_change(self.config.MEDIUM_MOMENTUM_PERIOD)
        df['momentum_30d'] = df['close'].pct_change(self.config.LONG_MOMENTUM_PERIOD)
        
        # Rate of Change (ROC)
        df['roc_5d'] = ((df['close'] - df['close'].shift(5)) / df['close'].shift(5)) * 100
        df['roc_14d'] = ((df['close'] - df['close'].shift(14)) / df['close'].shift(14)) * 100
        
        # Moving Average Momentum
        df['ma_20'] = df['close'].rolling(window=20).mean()
        df['ma_50'] = df['close'].rolling(window=50).mean()
        df['ma_momentum'] = (df['ma_20'] - df['ma_50']) / df['ma_50']
        
        # Volume Momentum
        df['volume_sma'] = df['volume'].rolling(window=self.config.VOLUME_MOMENTUM_PERIOD).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        df['volume_momentum'] = df['volume_ratio'].rolling(window=5).mean()
        
        # Price Acceleration (momentum of momentum)
        df['momentum_acceleration'] = df['momentum_5d'].diff()
        
        # Volatility (for momentum context)
        df['volatility'] = df['close'].rolling(window=20).std() / df['close'].rolling(window=20).mean()
        
        # Momentum Score
        df['momentum_score'] = self.calculate_momentum_score(df)
        
        return df
    
    def calculate_momentum_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate comprehensive momentum score (0-1)"""
        
        score = pd.Series(0.0, index=df.index)
        
        # RSI Momentum (25% weight)
        rsi_score = pd.Series(0.0, index=df.index)
        rsi_score = np.where(df['rsi'] > self.config.RSI_STRONG_MOMENTUM, 1.0,
                    np.where(df['rsi'] > self.config.RSI_MOMENTUM_THRESHOLD, 
                            (df['rsi'] - self.config.RSI_MOMENTUM_THRESHOLD) / 
                            (self.config.RSI_STRONG_MOMENTUM - self.config.RSI_MOMENTUM_THRESHOLD), 0))
        score += pd.Series(rsi_score, index=df.index) * 0.25
        
        # MACD Momentum (25% weight)
        macd_score = pd.Series(0.0, index=df.index)
        macd_score += (df['macd'] > df['macd_signal']) * 0.5  # Bullish crossover
        macd_score += (df['macd_histogram'] > df['macd_histogram'].shift(1)) * 0.5  # Rising histogram
        score += macd_score * 0.25
        
        # Price Momentum Multi-timeframe (30% weight)
        price_momentum_score = pd.Series(0.0, index=df.index)
        
        # Short-term momentum (10%)
        short_score = np.minimum(np.maximum(df['momentum_5d'] / self.config.MIN_SHORT_MOMENTUM, 0), 1.0)
        price_momentum_score += short_score * 0.33
        
        # Medium-term momentum (10%)
        medium_score = np.minimum(np.maximum(df['momentum_14d'] / self.config.MIN_MEDIUM_MOMENTUM, 0), 1.0)
        price_momentum_score += medium_score * 0.33
        
        # Long-term momentum (10%)
        long_score = np.minimum(np.maximum(df['momentum_30d'] / self.config.MIN_LONG_MOMENTUM, 0), 1.0)
        price_momentum_score += long_score * 0.33
        
        score += price_momentum_score * 0.30
        
        # Volume Momentum (15% weight)
        volume_score = np.minimum(df['volume_momentum'] / 2.0, 1.0)  # Normalize to 2x average
        score += volume_score * 0.15
        
        # Momentum Acceleration (5% weight) - Momentum is accelerating
        acceleration_score = np.where(df['momentum_acceleration'] > 0, 1.0, 0)
        score += pd.Series(acceleration_score, index=df.index) * 0.05
        
        return np.minimum(score, 1.0)
    
    def should_enter_long(self, symbol: str, row: pd.Series, portfolio_value: float) -> Tuple[bool, str]:
        """Check if should enter long position (bullish momentum)"""
        
        # Already have position
        if symbol in self.positions:
            return False, "Already have position"
        
        # Max positions check
        if len(self.positions) >= self.config.MAX_OPEN_POSITIONS:
            return False, "Max positions reached"
        
        # Check momentum score
        if row['momentum_score'] < self.config.MIN_MOMENTUM_SCORE:
            return False, f"Momentum score {row['momentum_score']:.2f} below threshold"
        
        # RSI momentum check
        if row['rsi'] < self.config.RSI_MOMENTUM_THRESHOLD:
            return False, f"RSI {row['rsi']:.1f} below momentum threshold"
        
        # MACD bullish momentum
        if not (row['macd'] > row['macd_signal']):
            return False, "MACD not bullish"
        
        # MACD histogram should be rising (momentum accelerating)
        if not (row['macd_histogram'] > row.get('macd_histogram_prev', row['macd_histogram'])):
            return False, "MACD histogram not rising"
        
        # Multi-timeframe momentum check
        if row['momentum_5d'] < self.config.MIN_SHORT_MOMENTUM:
            return False, f"5-day momentum {row['momentum_5d']:.2%} insufficient"
        
        if row['momentum_14d'] < self.config.MIN_MEDIUM_MOMENTUM:
            return False, f"14-day momentum {row['momentum_14d']:.2%} insufficient"
        
        # Volume momentum confirmation
        if row['volume_momentum'] < self.config.MIN_VOLUME_GROWTH:
            return False, f"Volume momentum {row['volume_momentum']:.2f} insufficient"
        
        # Minimum volatility for momentum strategy
        if row['volatility'] < self.config.MIN_VOLATILITY:
            return False, f"Volatility {row['volatility']:.2%} too low"
        
        # Price above key moving averages (trend confirmation)
        if not (row['close'] > row['ma_20'] > row['ma_50']):
            return False, "Price not above key moving averages"
        
        return True, f"Strong bullish momentum: {row['momentum_score']:.2f}"
    
    def should_enter_short(self, symbol: str, row: pd.Series, portfolio_value: float) -> Tuple[bool, str]:
        """Check if should enter short position (bearish momentum)"""
        
        # Already have position
        if symbol in self.positions:
            return False, "Already have position"
        
        # Max positions check
        if len(self.positions) >= self.config.MAX_OPEN_POSITIONS:
            return False, "Max positions reached"
        
        # Check momentum score (for bearish momentum, look for low RSI with strong downward price momentum)
        if row['momentum_score'] > 0.3:  # Should have low momentum score for short
            return False, f"Momentum score {row['momentum_score']:.2f} too high for short"
        
        # RSI bearish momentum
        if row['rsi'] > self.config.RSI_WEAK_THRESHOLD:
            return False, f"RSI {row['rsi']:.1f} not bearish enough"
        
        # MACD bearish momentum
        if not (row['macd'] < row['macd_signal']):
            return False, "MACD not bearish"
        
        # Negative price momentum
        if row['momentum_5d'] > -self.config.MIN_SHORT_MOMENTUM:
            return False, f"5-day momentum {row['momentum_5d']:.2%} not negative enough"
        
        if row['momentum_14d'] > -self.config.MIN_MEDIUM_MOMENTUM:
            return False, f"14-day momentum {row['momentum_14d']:.2%} not negative enough"
        
        # Volume confirmation (should still have volume in downward moves)
        if row['volume_ratio'] < 1.2:
            return False, f"Volume ratio {row['volume_ratio']:.2f} insufficient"
        
        # Price below key moving averages
        if not (row['close'] < row['ma_20'] < row['ma_50']):
            return False, "Price not below key moving averages"
        
        return True, f"Strong bearish momentum detected"
    
    def should_exit_position(self, symbol: str, row: pd.Series, position: Dict) -> Tuple[bool, str]:
        """Check if should exit position"""
        
        current_price = row['close']
        entry_price = position['entry_price']
        position_type = position.get('type', 'long')
        
        if position_type == 'long':
            current_return = (current_price - entry_price) / entry_price
        else:  # short
            current_return = (entry_price - current_price) / entry_price
        
        # Stop loss (wider for momentum)
        if current_return <= -self.config.STOP_LOSS_PCT:
            return True, "stop_loss"
        
        # Target achievement (higher for momentum)
        if current_return >= self.config.TARGET_PCT:
            return True, "target_achieved"
        
        # Trailing stop
        if 'max_return' not in position:
            position['max_return'] = current_return
        else:
            position['max_return'] = max(position['max_return'], current_return)
            
            if (position['max_return'] > 0.10 and 
                current_return < position['max_return'] - self.config.TRAILING_STOP_PCT):
                return True, "trailing_stop"
        
        # Momentum-specific exits
        if position_type == 'long':
            # RSI falling below momentum threshold
            if row['rsi'] < self.config.RSI_MOMENTUM_THRESHOLD:
                return True, "rsi_momentum_loss"
            
            # MACD bearish crossover
            if row['macd'] < row['macd_signal']:
                return True, "macd_bearish_crossover"
            
            # Short-term momentum turning negative
            if row['momentum_5d'] < 0:
                return True, "short_term_momentum_loss"
            
            # Momentum acceleration turning negative
            if row['momentum_acceleration'] < -0.01:  # Momentum decelerating significantly
                return True, "momentum_deceleration"
        
        else:  # short position
            # RSI rising above weak threshold
            if row['rsi'] > self.config.RSI_WEAK_THRESHOLD:
                return True, "rsi_momentum_recovery"
            
            # MACD bullish crossover
            if row['macd'] > row['macd_signal']:
                return True, "macd_bullish_crossover"
            
            # Short-term momentum turning positive
            if row['momentum_5d'] > 0:
                return True, "short_term_momentum_recovery"
        
        # Volume drying up (momentum losing steam)
        if row['volume_ratio'] < 0.7:
            return True, "volume_momentum_loss"
        
        return False, "hold"
    
    def get_position_size(self, symbol: str, price: float, portfolio_value: float, 
                         momentum_score: float) -> int:
        """Calculate position size based on momentum strength"""
        
        # Base position size (larger for momentum strategy)
        base_size = portfolio_value * self.config.MAX_POSITION_SIZE
        
        # Adjust based on momentum score (higher momentum = larger position)
        momentum_multiplier = 0.6 + (momentum_score * 0.4)  # 0.6x to 1.0x
        adjusted_size = base_size * momentum_multiplier
        
        return max(1, int(adjusted_size / price))
    
    def get_momentum_analysis(self, row: pd.Series) -> Dict:
        """Get detailed momentum analysis"""
        
        return {
            'overall_score': row['momentum_score'],
            'rsi_momentum': row['rsi'] > self.config.RSI_MOMENTUM_THRESHOLD,
            'macd_bullish': row['macd'] > row['macd_signal'],
            'short_term_momentum': row['momentum_5d'],
            'medium_term_momentum': row['momentum_14d'],
            'long_term_momentum': row['momentum_30d'],
            'volume_momentum': row['volume_momentum'],
            'momentum_acceleration': row['momentum_acceleration'],
            'trend_alignment': row['close'] > row['ma_20'] > row['ma_50']
        }
    
    def get_strategy_info(self) -> Dict:
        """Get strategy information"""
        return {
            'name': self.name,
            'type': 'Momentum/Trend',
            'timeframe': 'Short to Medium Term',
            'best_markets': 'Strong trending markets with momentum',
            'parameters': {
                'rsi_threshold': self.config.RSI_MOMENTUM_THRESHOLD,
                'min_5d_momentum': self.config.MIN_SHORT_MOMENTUM,
                'min_14d_momentum': self.config.MIN_MEDIUM_MOMENTUM,
                'target_pct': self.config.TARGET_PCT
            },
            'current_positions': len(self.positions)
        }