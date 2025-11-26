#!/usr/bin/env python3
"""
Trend-Following Strategy Implementation
Uses Moving Averages, MACD, and ADX for trend identification
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TrendFollowingConfig:
    """Configuration for Trend Following Strategy"""
    
    # Moving Average Parameters
    MA_SHORT: int = 20
    MA_LONG: int = 50
    MA_VERY_LONG: int = 200  # Long-term trend filter
    
    # MACD Parameters
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9
    
    # ADX Parameters
    ADX_PERIOD: int = 14
    ADX_THRESHOLD: int = 25  # Strong trend threshold
    
    # Position Management
    MAX_POSITION_SIZE: float = 0.12  # 12% per position
    STOP_LOSS_PCT: float = 0.06      # 6% stop loss
    TARGET_PCT: float = 0.18         # 18% target
    TRAILING_STOP_PCT: float = 0.04  # 4% trailing stop
    
    # Risk Management
    MAX_OPEN_POSITIONS: int = 6
    MIN_TREND_STRENGTH: float = 0.7  # Minimum trend score
    
    # Volume Confirmation
    MIN_VOLUME_RATIO: float = 1.2    # 20% above average

class TrendFollowingStrategy:
    """
    Classic Trend Following Strategy
    
    Entry Conditions:
    1. Short MA > Long MA (bullish trend)
    2. Price > Very Long MA (long-term trend)
    3. MACD > Signal line (momentum confirmation)
    4. ADX > threshold (strong trend)
    5. Volume above average
    
    Exit Conditions:
    1. Moving average crossover reversal
    2. MACD bearish crossover
    3. ADX declining (trend weakening)
    4. Stop loss or target hit
    """
    
    def __init__(self, config: TrendFollowingConfig = None):
        self.config = config or TrendFollowingConfig()
        self.positions = {}
        self.name = "Trend Following Strategy"
        
        logger.info(f"Initialized {self.name}")
        logger.info(f"Parameters: MA({self.config.MA_SHORT},{self.config.MA_LONG}), "
                   f"ADX threshold: {self.config.ADX_THRESHOLD}")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators"""
        
        # Moving Averages
        df['ma_short'] = df['close'].rolling(window=self.config.MA_SHORT).mean()
        df['ma_long'] = df['close'].rolling(window=self.config.MA_LONG).mean()
        df['ma_very_long'] = df['close'].rolling(window=self.config.MA_VERY_LONG).mean()
        
        # MACD
        exp1 = df['close'].ewm(span=self.config.MACD_FAST).mean()
        exp2 = df['close'].ewm(span=self.config.MACD_SLOW).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=self.config.MACD_SIGNAL).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # ADX Calculation
        high_low = df['high'] - df['low']
        high_close_prev = np.abs(df['high'] - df['close'].shift(1))
        low_close_prev = np.abs(df['low'] - df['close'].shift(1))
        
        true_range = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
        atr = true_range.rolling(window=self.config.ADX_PERIOD).mean()
        
        plus_dm = np.where((df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']),
                          np.maximum(df['high'] - df['high'].shift(1), 0), 0)
        minus_dm = np.where((df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)),
                           np.maximum(df['low'].shift(1) - df['low'], 0), 0)
        
        plus_di = 100 * (pd.Series(plus_dm).rolling(window=self.config.ADX_PERIOD).mean() / atr)
        minus_di = 100 * (pd.Series(minus_dm).rolling(window=self.config.ADX_PERIOD).mean() / atr)
        
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        df['adx'] = dx.rolling(window=self.config.ADX_PERIOD).mean()
        df['plus_di'] = plus_di
        df['minus_di'] = minus_di
        
        # Volume Analysis
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Trend Strength Score
        df['trend_score'] = self.calculate_trend_score(df)
        
        return df
    
    def calculate_trend_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate overall trend strength score (0-1)"""
        
        score = pd.Series(0.0, index=df.index)
        
        # MA Alignment (40% weight)
        ma_score = pd.Series(0.0, index=df.index)
        ma_score += (df['close'] > df['ma_short']) * 0.25
        ma_score += (df['ma_short'] > df['ma_long']) * 0.25
        ma_score += (df['ma_long'] > df['ma_very_long']) * 0.25
        ma_score += (df['close'] > df['ma_very_long']) * 0.25
        score += ma_score * 0.4
        
        # MACD Momentum (30% weight)
        macd_score = pd.Series(0.0, index=df.index)
        macd_score += (df['macd'] > df['macd_signal']) * 0.5
        macd_score += (df['macd_histogram'] > df['macd_histogram'].shift(1)) * 0.5
        score += macd_score * 0.3
        
        # ADX Trend Strength (30% weight)
        adx_score = np.minimum(df['adx'] / 50, 1.0)  # Normalize to 0-1
        score += adx_score * 0.3
        
        return score
    
    def should_enter_long(self, symbol: str, row: pd.Series, portfolio_value: float) -> Tuple[bool, str]:
        """Check if should enter long position"""
        
        # Already have position
        if symbol in self.positions:
            return False, "Already have position"
        
        # Max positions check
        if len(self.positions) >= self.config.MAX_OPEN_POSITIONS:
            return False, "Max positions reached"
        
        # Check trend score
        if row['trend_score'] < self.config.MIN_TREND_STRENGTH:
            return False, f"Trend score {row['trend_score']:.2f} below threshold"
        
        # Primary trend conditions
        if not (row['ma_short'] > row['ma_long']):
            return False, "Short MA not above Long MA"
        
        if not (row['close'] > row['ma_very_long']):
            return False, "Price not above long-term MA"
        
        # MACD confirmation
        if not (row['macd'] > row['macd_signal']):
            return False, "MACD not bullish"
        
        # ADX trend strength
        if row['adx'] < self.config.ADX_THRESHOLD:
            return False, f"ADX {row['adx']:.1f} below threshold"
        
        # +DI should be above -DI for bullish trend
        if not (row['plus_di'] > row['minus_di']):
            return False, "+DI not above -DI"
        
        # Volume confirmation
        if row['volume_ratio'] < self.config.MIN_VOLUME_RATIO:
            return False, f"Volume ratio {row['volume_ratio']:.2f} too low"
        
        return True, f"Strong trend signal: {row['trend_score']:.2f}"
    
    def should_exit_position(self, symbol: str, row: pd.Series, position: Dict) -> Tuple[bool, str]:
        """Check if should exit position"""
        
        current_price = row['close']
        entry_price = position['entry_price']
        current_return = (current_price - entry_price) / entry_price
        
        # Stop loss
        if current_return <= -self.config.STOP_LOSS_PCT:
            return True, "stop_loss"
        
        # Target achievement
        if current_return >= self.config.TARGET_PCT:
            return True, "target_achieved"
        
        # Trailing stop
        if 'max_return' not in position:
            position['max_return'] = current_return
        else:
            position['max_return'] = max(position['max_return'], current_return)
            
            if (position['max_return'] > 0.08 and 
                current_return < position['max_return'] - self.config.TRAILING_STOP_PCT):
                return True, "trailing_stop"
        
        # Trend reversal signals
        
        # MA crossover reversal
        if row['ma_short'] < row['ma_long']:
            return True, "ma_crossover_reversal"
        
        # MACD bearish crossover
        if (row['macd'] < row['macd_signal'] and 
            row['macd_histogram'] < 0):
            return True, "macd_bearish_crossover"
        
        # ADX declining trend strength
        if (row['adx'] < self.config.ADX_THRESHOLD and 
            row['adx'] < row.get('adx_prev', row['adx'])):
            return True, "trend_weakening"
        
        # DI crossover (trend direction change)
        if row['plus_di'] < row['minus_di']:
            return True, "directional_reversal"
        
        return False, "hold"
    
    def get_position_size(self, symbol: str, price: float, portfolio_value: float, 
                         trend_score: float) -> int:
        """Calculate position size based on trend strength"""
        
        # Base position size
        base_size = portfolio_value * self.config.MAX_POSITION_SIZE
        
        # Adjust based on trend strength
        trend_multiplier = 0.5 + (trend_score * 0.5)  # 0.5x to 1.0x
        adjusted_size = base_size * trend_multiplier
        
        return max(1, int(adjusted_size / price))
    
    def get_strategy_info(self) -> Dict:
        """Get strategy information"""
        return {
            'name': self.name,
            'type': 'Trend Following',
            'timeframe': 'Medium to Long Term',
            'best_markets': 'Trending markets',
            'parameters': {
                'ma_short': self.config.MA_SHORT,
                'ma_long': self.config.MA_LONG,
                'adx_threshold': self.config.ADX_THRESHOLD,
                'min_trend_strength': self.config.MIN_TREND_STRENGTH
            },
            'current_positions': len(self.positions)
        }