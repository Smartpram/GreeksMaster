#!/usr/bin/env python3
"""
Breakout Strategy Implementation
Uses Pivot Points, Support/Resistance levels, and Volume Analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BreakoutConfig:
    """Configuration for Breakout Strategy"""
    
    # Pivot Point Parameters
    PIVOT_LOOKBACK: int = 20
    SUPPORT_RESISTANCE_STRENGTH: int = 3  # Min touches to confirm level
    
    # Breakout Parameters
    BREAKOUT_THRESHOLD: float = 0.005     # 0.5% beyond S/R level
    VOLUME_CONFIRMATION: float = 2.0      # 2x average volume
    PRICE_MOMENTUM_THRESHOLD: float = 0.02 # 2% price move
    
    # ATR Parameters (for dynamic levels)
    ATR_PERIOD: int = 14
    ATR_MULTIPLIER: float = 1.5
    
    # Position Management
    MAX_POSITION_SIZE: float = 0.10       # 10% per position
    STOP_LOSS_ATR_MULTIPLE: float = 2.0   # 2x ATR below entry
    TARGET_ATR_MULTIPLE: float = 4.0      # 4x ATR target
    
    # Risk Management
    MAX_OPEN_POSITIONS: int = 4
    MIN_BREAKOUT_STRENGTH: float = 0.75
    
    # Time-based filters
    MIN_CONSOLIDATION_DAYS: int = 5       # Min days in range before breakout
    MAX_TIME_IN_POSITION: int = 30        # Max days to hold

class BreakoutStrategy:
    """
    Breakout Strategy for High-Volatility Trading
    
    Entry Conditions:
    1. Price breaks confirmed support/resistance level
    2. High volume confirmation (2x+ average)
    3. Price momentum beyond threshold
    4. ATR-based dynamic stop placement
    
    Exit Conditions:
    1. ATR-based target achieved
    2. ATR-based stop loss hit
    3. Failed breakout (return below S/R level)
    4. Time-based exit
    """
    
    def __init__(self, config: BreakoutConfig = None):
        self.config = config or BreakoutConfig()
        self.positions = {}
        self.support_resistance_levels = {}
        self.name = "Breakout Strategy"
        
        logger.info(f"Initialized {self.name}")
        logger.info(f"Parameters: Volume threshold {self.config.VOLUME_CONFIRMATION}x, "
                   f"ATR stop {self.config.STOP_LOSS_ATR_MULTIPLE}x")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators"""
        
        # ATR for dynamic levels
        high_low = df['high'] - df['low']
        high_close_prev = np.abs(df['high'] - df['close'].shift(1))
        low_close_prev = np.abs(df['low'] - df['close'].shift(1))
        
        true_range = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
        df['atr'] = true_range.rolling(window=self.config.ATR_PERIOD).mean()
        
        # Volume analysis
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Price momentum
        df['price_change_5d'] = df['close'].pct_change(5)
        df['price_change_1d'] = df['close'].pct_change(1)
        
        # Volatility measures
        df['volatility'] = df['close'].rolling(window=20).std() / df['close'].rolling(window=20).mean()
        
        # Support and Resistance levels
        df = self.identify_support_resistance(df)
        
        # Breakout strength score
        df['breakout_score'] = self.calculate_breakout_score(df)
        
        return df
    
    def identify_support_resistance(self, df: pd.DataFrame) -> pd.DataFrame:
        """Identify key support and resistance levels"""
        
        df['pivot_high'] = df['high'].rolling(window=self.config.PIVOT_LOOKBACK*2+1, center=True).max() == df['high']
        df['pivot_low'] = df['low'].rolling(window=self.config.PIVOT_LOOKBACK*2+1, center=True).min() == df['low']
        
        # Get recent pivot levels
        recent_pivots_high = df[df['pivot_high'] == True]['high'].tail(10).values
        recent_pivots_low = df[df['pivot_low'] == True]['low'].tail(10).values
        
        # Identify significant levels (levels that have been tested multiple times)
        resistance_levels = []
        support_levels = []
        
        for level in recent_pivots_high:
            touches = sum(abs(df['high'] - level) / level < 0.01)  # Within 1% of level
            if touches >= self.config.SUPPORT_RESISTANCE_STRENGTH:
                resistance_levels.append(level)
        
        for level in recent_pivots_low:
            touches = sum(abs(df['low'] - level) / level < 0.01)  # Within 1% of level
            if touches >= self.config.SUPPORT_RESISTANCE_STRENGTH:
                support_levels.append(level)
        
        # Store the nearest levels
        current_price = df['close'].iloc[-1]
        
        # Nearest resistance above current price
        resistance_above = [r for r in resistance_levels if r > current_price]
        df['nearest_resistance'] = min(resistance_above) if resistance_above else np.nan
        
        # Nearest support below current price
        support_below = [s for s in support_levels if s < current_price]
        df['nearest_support'] = max(support_below) if support_below else np.nan
        
        # Distance to key levels
        df['distance_to_resistance'] = (df['nearest_resistance'] - df['close']) / df['close']
        df['distance_to_support'] = (df['close'] - df['nearest_support']) / df['close']
        
        return df
    
    def calculate_breakout_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate breakout opportunity score (0-1)"""
        
        score = pd.Series(0.0, index=df.index)
        
        # Volume surge (40% weight)
        volume_score = np.minimum(df['volume_ratio'] / 3.0, 1.0)
        score += volume_score * 0.4
        
        # Price momentum (30% weight)
        momentum_score = np.minimum(abs(df['price_change_1d']) / 0.05, 1.0)  # Normalize to 5% move
        score += momentum_score * 0.3
        
        # Proximity to key levels (20% weight)
        # Higher score when close to S/R levels
        proximity_score = pd.Series(0.0, index=df.index)
        
        # Near resistance (for upward breakout)
        resistance_proximity = np.where(
            df['distance_to_resistance'] < 0.02,  # Within 2% of resistance
            1.0 - (df['distance_to_resistance'] / 0.02),
            0
        )
        
        # Near support (for downward breakout)
        support_proximity = np.where(
            df['distance_to_support'] < 0.02,  # Within 2% of support
            1.0 - (df['distance_to_support'] / 0.02),
            0
        )
        
        proximity_score = pd.Series(np.maximum(resistance_proximity, support_proximity), index=df.index)
        score += proximity_score * 0.2
        
        # Volatility context (10% weight) - Higher score in normal to high volatility
        volatility_score = np.minimum(df['volatility'] / 0.05, 1.0)  # Normalize to 5% volatility
        score += volatility_score * 0.1
        
        return np.minimum(score, 1.0)
    
    def should_enter_long_breakout(self, symbol: str, row: pd.Series, portfolio_value: float) -> Tuple[bool, str]:
        """Check for upward breakout entry"""
        
        # Already have position
        if symbol in self.positions:
            return False, "Already have position"
        
        # Max positions check
        if len(self.positions) >= self.config.MAX_OPEN_POSITIONS:
            return False, "Max positions reached"
        
        # Check breakout score
        if row['breakout_score'] < self.config.MIN_BREAKOUT_STRENGTH:
            return False, f"Breakout score {row['breakout_score']:.2f} below threshold"
        
        # Must have identified resistance level
        if pd.isna(row['nearest_resistance']):
            return False, "No resistance level identified"
        
        # Price must break above resistance with threshold
        breakout_level = row['nearest_resistance'] * (1 + self.config.BREAKOUT_THRESHOLD)
        if row['close'] < breakout_level:
            return False, f"Price {row['close']:.2f} below breakout level {breakout_level:.2f}"
        
        # Volume confirmation - must be significantly above average
        if row['volume_ratio'] < self.config.VOLUME_CONFIRMATION:
            return False, f"Volume ratio {row['volume_ratio']:.2f} insufficient"
        
        # Price momentum confirmation
        if row['price_change_1d'] < self.config.PRICE_MOMENTUM_THRESHOLD:
            return False, f"Price momentum {row['price_change_1d']:.3f} insufficient"
        
        # ATR-based validation (sufficient volatility for meaningful breakout)
        if row['atr'] / row['close'] < 0.01:  # ATR should be at least 1% of price
            return False, "ATR too low for breakout strategy"
        
        return True, f"Upward breakout signal: {row['breakout_score']:.2f}"
    
    def should_enter_short_breakout(self, symbol: str, row: pd.Series, portfolio_value: float) -> Tuple[bool, str]:
        """Check for downward breakout entry"""
        
        # Already have position
        if symbol in self.positions:
            return False, "Already have position"
        
        # Max positions check
        if len(self.positions) >= self.config.MAX_OPEN_POSITIONS:
            return False, "Max positions reached"
        
        # Check breakout score
        if row['breakout_score'] < self.config.MIN_BREAKOUT_STRENGTH:
            return False, f"Breakout score {row['breakout_score']:.2f} below threshold"
        
        # Must have identified support level
        if pd.isna(row['nearest_support']):
            return False, "No support level identified"
        
        # Price must break below support with threshold
        breakdown_level = row['nearest_support'] * (1 - self.config.BREAKOUT_THRESHOLD)
        if row['close'] > breakdown_level:
            return False, f"Price {row['close']:.2f} above breakdown level {breakdown_level:.2f}"
        
        # Volume confirmation
        if row['volume_ratio'] < self.config.VOLUME_CONFIRMATION:
            return False, f"Volume ratio {row['volume_ratio']:.2f} insufficient"
        
        # Price momentum confirmation (negative for breakdown)
        if row['price_change_1d'] > -self.config.PRICE_MOMENTUM_THRESHOLD:
            return False, f"Price momentum {row['price_change_1d']:.3f} insufficient"
        
        # ATR-based validation
        if row['atr'] / row['close'] < 0.01:
            return False, "ATR too low for breakout strategy"
        
        return True, f"Downward breakout signal: {row['breakout_score']:.2f}"
    
    def should_exit_position(self, symbol: str, row: pd.Series, position: Dict) -> Tuple[bool, str]:
        """Check if should exit position"""
        
        current_price = row['close']
        entry_price = position['entry_price']
        position_type = position.get('type', 'long')
        entry_date = position.get('entry_date', datetime.now())
        
        # Calculate return based on position type
        if position_type == 'long':
            current_return = (current_price - entry_price) / entry_price
        else:  # short
            current_return = (entry_price - current_price) / entry_price
        
        # ATR-based stop loss
        atr_stop = row['atr'] * self.config.STOP_LOSS_ATR_MULTIPLE
        if position_type == 'long':
            stop_price = entry_price - atr_stop
            if current_price <= stop_price:
                return True, "atr_stop_loss"
        else:  # short
            stop_price = entry_price + atr_stop
            if current_price >= stop_price:
                return True, "atr_stop_loss"
        
        # ATR-based target
        atr_target = row['atr'] * self.config.TARGET_ATR_MULTIPLE
        target_return = atr_target / entry_price
        if current_return >= target_return:
            return True, "atr_target_achieved"
        
        # Failed breakout - price returns below/above S/R level
        if position_type == 'long':
            if not pd.isna(row['nearest_resistance']):
                # If price falls back below the resistance level it broke
                if current_price < row['nearest_resistance']:
                    return True, "failed_breakout"
        else:  # short
            if not pd.isna(row['nearest_support']):
                # If price rises back above the support level it broke
                if current_price > row['nearest_support']:
                    return True, "failed_breakout"
        
        # Time-based exit
        if isinstance(entry_date, str):
            entry_date = datetime.strptime(entry_date, '%Y-%m-%d')
        days_held = (datetime.now() - entry_date).days
        if days_held >= self.config.MAX_TIME_IN_POSITION:
            return True, "time_exit"
        
        # Volume drying up (breakout losing steam)
        if row['volume_ratio'] < 0.5:  # Very low volume
            return True, "volume_drying_up"
        
        return False, "hold"
    
    def get_position_size(self, symbol: str, price: float, portfolio_value: float, 
                         breakout_score: float, atr: float) -> int:
        """Calculate position size based on breakout strength and volatility"""
        
        # Base position size
        base_size = portfolio_value * self.config.MAX_POSITION_SIZE
        
        # Adjust based on breakout score
        score_multiplier = 0.6 + (breakout_score * 0.4)  # 0.6x to 1.0x
        
        # Adjust based on volatility (smaller size for high volatility)
        volatility_ratio = atr / price
        volatility_multiplier = max(0.5, 1.0 - volatility_ratio * 10)  # Reduce size for high volatility
        
        adjusted_size = base_size * score_multiplier * volatility_multiplier
        
        return max(1, int(adjusted_size / price))
    
    def get_dynamic_levels(self, symbol: str, current_price: float, atr: float) -> Dict:
        """Get dynamic support/resistance levels based on ATR"""
        
        return {
            'dynamic_resistance': current_price + (atr * self.config.ATR_MULTIPLIER),
            'dynamic_support': current_price - (atr * self.config.ATR_MULTIPLIER),
            'stop_loss_long': current_price - (atr * self.config.STOP_LOSS_ATR_MULTIPLE),
            'stop_loss_short': current_price + (atr * self.config.STOP_LOSS_ATR_MULTIPLE),
            'target_long': current_price + (atr * self.config.TARGET_ATR_MULTIPLE),
            'target_short': current_price - (atr * self.config.TARGET_ATR_MULTIPLE)
        }
    
    def get_strategy_info(self) -> Dict:
        """Get strategy information"""
        return {
            'name': self.name,
            'type': 'Breakout/Momentum',
            'timeframe': 'Short to Medium Term',
            'best_markets': 'High volatility, trending breakouts',
            'parameters': {
                'volume_confirmation': self.config.VOLUME_CONFIRMATION,
                'breakout_threshold': self.config.BREAKOUT_THRESHOLD,
                'atr_stop_multiple': self.config.STOP_LOSS_ATR_MULTIPLE,
                'atr_target_multiple': self.config.TARGET_ATR_MULTIPLE
            },
            'current_positions': len(self.positions),
            'support_resistance_levels': len(self.support_resistance_levels)
        }