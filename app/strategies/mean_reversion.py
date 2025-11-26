#!/usr/bin/env python3
"""
Mean-Reversion Strategy Implementation
Uses Bollinger Bands and RSI for range-bound trading
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MeanReversionConfig:
    """Configuration for Mean Reversion Strategy"""
    
    # Bollinger Bands Parameters
    BB_PERIOD: int = 20
    BB_STD_DEV: float = 2.0
    BB_SQUEEZE_THRESHOLD: float = 0.1  # Volatility squeeze detection
    
    # RSI Parameters
    RSI_PERIOD: int = 14
    RSI_OVERSOLD: int = 25
    RSI_OVERBOUGHT: int = 75
    RSI_EXTREME_OVERSOLD: int = 15
    RSI_EXTREME_OVERBOUGHT: int = 85
    
    # Mean Reversion Parameters
    PRICE_DEVIATION_THRESHOLD: float = 0.02  # 2% from mean
    VOLUME_SPIKE_THRESHOLD: float = 2.0      # 2x average volume
    
    # Position Management
    MAX_POSITION_SIZE: float = 0.08  # 8% per position
    STOP_LOSS_PCT: float = 0.05      # 5% stop loss
    TARGET_PCT: float = 0.10         # 10% target (smaller than trend following)
    
    # Risk Management
    MAX_OPEN_POSITIONS: int = 5
    MIN_REVERSION_SCORE: float = 0.7
    
    # Market Condition Filters
    MAX_TREND_STRENGTH: float = 30   # Avoid trending markets (ADX < 30)

class MeanReversionStrategy:
    """
    Mean Reversion Strategy for Range-Bound Markets
    
    Entry Conditions:
    1. Price touches lower Bollinger Band + RSI oversold
    2. Volume spike confirmation
    3. Not in strong trending market
    4. Price significantly below mean
    
    Exit Conditions:
    1. Price returns to middle Bollinger Band
    2. RSI reaches overbought levels
    3. Stop loss or target hit
    4. Market starts trending strongly
    """
    
    def __init__(self, config: MeanReversionConfig = None):
        self.config = config or MeanReversionConfig()
        self.positions = {}
        self.name = "Mean Reversion Strategy"
        
        logger.info(f"Initialized {self.name}")
        logger.info(f"Parameters: BB({self.config.BB_PERIOD},{self.config.BB_STD_DEV}), "
                   f"RSI({self.config.RSI_OVERSOLD},{self.config.RSI_OVERBOUGHT})")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators"""
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=self.config.BB_PERIOD).mean()
        bb_std = df['close'].rolling(window=self.config.BB_PERIOD).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * self.config.BB_STD_DEV)
        df['bb_lower'] = df['bb_middle'] - (bb_std * self.config.BB_STD_DEV)
        
        # Bollinger Band Width (for squeeze detection)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_squeeze'] = df['bb_width'] < self.config.BB_SQUEEZE_THRESHOLD
        
        # Bollinger Band Position
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.config.RSI_PERIOD).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.config.RSI_PERIOD).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Price deviation from mean
        df['price_deviation'] = (df['close'] - df['bb_middle']) / df['bb_middle']
        
        # Volume analysis
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # ADX for trend detection (to avoid trending markets)
        df = self.calculate_adx(df)
        
        # Mean reversion score
        df['reversion_score'] = self.calculate_reversion_score(df)
        
        return df
    
    def calculate_adx(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate ADX to detect trending markets"""
        
        high_low = df['high'] - df['low']
        high_close_prev = np.abs(df['high'] - df['close'].shift(1))
        low_close_prev = np.abs(df['low'] - df['close'].shift(1))
        
        true_range = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
        atr = true_range.rolling(window=14).mean()
        
        plus_dm = np.where((df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']),
                          np.maximum(df['high'] - df['high'].shift(1), 0), 0)
        minus_dm = np.where((df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)),
                           np.maximum(df['low'].shift(1) - df['low'], 0), 0)
        
        plus_di = 100 * (pd.Series(plus_dm).rolling(window=14).mean() / atr)
        minus_di = 100 * (pd.Series(minus_dm).rolling(window=14).mean() / atr)
        
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        df['adx'] = dx.rolling(window=14).mean()
        
        return df
    
    def calculate_reversion_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate mean reversion opportunity score (0-1)"""
        
        score = pd.Series(0.0, index=df.index)
        
        # Bollinger Band position (40% weight)
        # Higher score when price is at extremes
        bb_score = pd.Series(0.0, index=df.index)
        bb_score = np.where(df['bb_position'] < 0.2, 1.0 - df['bb_position'] * 5, 0)  # Oversold
        bb_score += np.where(df['bb_position'] > 0.8, (df['bb_position'] - 0.8) * 5, 0)  # Overbought
        score += pd.Series(bb_score, index=df.index) * 0.4
        
        # RSI extremes (30% weight)
        rsi_score = pd.Series(0.0, index=df.index)
        rsi_score = np.where(df['rsi'] < self.config.RSI_OVERSOLD, 
                            (self.config.RSI_OVERSOLD - df['rsi']) / self.config.RSI_OVERSOLD, 0)
        rsi_score += np.where(df['rsi'] > self.config.RSI_OVERBOUGHT,
                             (df['rsi'] - self.config.RSI_OVERBOUGHT) / (100 - self.config.RSI_OVERBOUGHT), 0)
        score += pd.Series(rsi_score, index=df.index) * 0.3
        
        # Non-trending market (20% weight) - Higher score in sideways markets
        trend_score = np.maximum(0, (self.config.MAX_TREND_STRENGTH - df['adx']) / self.config.MAX_TREND_STRENGTH)
        score += trend_score * 0.2
        
        # Volume confirmation (10% weight)
        volume_score = np.minimum(df['volume_ratio'] / 3.0, 1.0)  # Normalize to 0-1
        score += volume_score * 0.1
        
        return np.minimum(score, 1.0)  # Cap at 1.0
    
    def should_enter_long(self, symbol: str, row: pd.Series, portfolio_value: float) -> Tuple[bool, str]:
        """Check if should enter long position (buy oversold)"""
        
        # Already have position
        if symbol in self.positions:
            return False, "Already have position"
        
        # Max positions check
        if len(self.positions) >= self.config.MAX_OPEN_POSITIONS:
            return False, "Max positions reached"
        
        # Check reversion score
        if row['reversion_score'] < self.config.MIN_REVERSION_SCORE:
            return False, f"Reversion score {row['reversion_score']:.2f} below threshold"
        
        # Avoid trending markets
        if row['adx'] > self.config.MAX_TREND_STRENGTH:
            return False, f"Market trending too strongly (ADX: {row['adx']:.1f})"
        
        # Primary mean reversion conditions (LONG)
        # Price at lower Bollinger Band
        if row['bb_position'] > 0.2:  # Not in lower 20%
            return False, "Price not near lower Bollinger Band"
        
        # RSI oversold
        if row['rsi'] > self.config.RSI_OVERSOLD:
            return False, f"RSI {row['rsi']:.1f} not oversold"
        
        # Volume spike confirmation
        if row['volume_ratio'] < self.config.VOLUME_SPIKE_THRESHOLD:
            return False, f"Volume ratio {row['volume_ratio']:.2f} too low"
        
        # Price significantly below mean
        if row['price_deviation'] > -self.config.PRICE_DEVIATION_THRESHOLD:
            return False, "Price not sufficiently below mean"
        
        return True, f"Mean reversion BUY signal: {row['reversion_score']:.2f}"
    
    def should_enter_short(self, symbol: str, row: pd.Series, portfolio_value: float) -> Tuple[bool, str]:
        """Check if should enter short position (sell overbought)"""
        
        # Already have position
        if symbol in self.positions:
            return False, "Already have position"
        
        # Max positions check
        if len(self.positions) >= self.config.MAX_OPEN_POSITIONS:
            return False, "Max positions reached"
        
        # Check reversion score
        if row['reversion_score'] < self.config.MIN_REVERSION_SCORE:
            return False, f"Reversion score {row['reversion_score']:.2f} below threshold"
        
        # Avoid trending markets
        if row['adx'] > self.config.MAX_TREND_STRENGTH:
            return False, f"Market trending too strongly (ADX: {row['adx']:.1f})"
        
        # Primary mean reversion conditions (SHORT)
        # Price at upper Bollinger Band
        if row['bb_position'] < 0.8:  # Not in upper 20%
            return False, "Price not near upper Bollinger Band"
        
        # RSI overbought
        if row['rsi'] < self.config.RSI_OVERBOUGHT:
            return False, f"RSI {row['rsi']:.1f} not overbought"
        
        # Volume spike confirmation
        if row['volume_ratio'] < self.config.VOLUME_SPIKE_THRESHOLD:
            return False, f"Volume ratio {row['volume_ratio']:.2f} too low"
        
        # Price significantly above mean
        if row['price_deviation'] < self.config.PRICE_DEVIATION_THRESHOLD:
            return False, "Price not sufficiently above mean"
        
        return True, f"Mean reversion SELL signal: {row['reversion_score']:.2f}"
    
    def should_exit_position(self, symbol: str, row: pd.Series, position: Dict) -> Tuple[bool, str]:
        """Check if should exit position"""
        
        current_price = row['close']
        entry_price = position['entry_price']
        position_type = position.get('type', 'long')
        
        if position_type == 'long':
            current_return = (current_price - entry_price) / entry_price
        else:  # short
            current_return = (entry_price - current_price) / entry_price
        
        # Stop loss
        if current_return <= -self.config.STOP_LOSS_PCT:
            return True, "stop_loss"
        
        # Target achievement
        if current_return >= self.config.TARGET_PCT:
            return True, "target_achieved"
        
        # Mean reversion complete - price returned to mean
        if abs(row['price_deviation']) < 0.005:  # Within 0.5% of mean
            return True, "mean_reversion_complete"
        
        # Position-specific exits
        if position_type == 'long':
            # Exit long when price reaches middle/upper BB
            if row['bb_position'] > 0.6:  # Moved from bottom to upper 40%
                return True, "price_reverted_to_mean"
            
            # RSI overbought (profit taking for long)
            if row['rsi'] > self.config.RSI_OVERBOUGHT:
                return True, "rsi_overbought_exit"
        
        else:  # short position
            # Exit short when price reaches middle/lower BB
            if row['bb_position'] < 0.4:  # Moved from top to lower 40%
                return True, "price_reverted_to_mean"
            
            # RSI oversold (profit taking for short)
            if row['rsi'] < self.config.RSI_OVERSOLD:
                return True, "rsi_oversold_exit"
        
        # Market starts trending strongly (exit all positions)
        if row['adx'] > self.config.MAX_TREND_STRENGTH * 1.5:
            return True, "market_trending_strongly"
        
        # Bollinger Band squeeze ending (volatility expansion)
        if not row['bb_squeeze'] and row.get('bb_squeeze_prev', False):
            return True, "volatility_expansion"
        
        return False, "hold"
    
    def get_position_size(self, symbol: str, price: float, portfolio_value: float, 
                         reversion_score: float) -> int:
        """Calculate position size based on reversion strength"""
        
        # Base position size (smaller than trend following)
        base_size = portfolio_value * self.config.MAX_POSITION_SIZE
        
        # Adjust based on reversion score
        score_multiplier = 0.6 + (reversion_score * 0.4)  # 0.6x to 1.0x
        adjusted_size = base_size * score_multiplier
        
        return max(1, int(adjusted_size / price))
    
    def get_strategy_info(self) -> Dict:
        """Get strategy information"""
        return {
            'name': self.name,
            'type': 'Mean Reversion',
            'timeframe': 'Short to Medium Term',
            'best_markets': 'Range-bound, sideways markets',
            'parameters': {
                'bb_period': self.config.BB_PERIOD,
                'bb_std_dev': self.config.BB_STD_DEV,
                'rsi_oversold': self.config.RSI_OVERSOLD,
                'rsi_overbought': self.config.RSI_OVERBOUGHT,
                'max_trend_strength': self.config.MAX_TREND_STRENGTH
            },
            'current_positions': len(self.positions)
        }