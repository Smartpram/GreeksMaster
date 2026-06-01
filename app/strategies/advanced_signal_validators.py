#!/usr/bin/env python3
"""
Advanced Signal Enhancement: Stochastic RSI, Renko Bars, and Fibonacci Retracements
Integration with Enhanced Signal Confirmation System
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class FibonacciLevel(Enum):
    """Standard Fibonacci retracement levels"""
    LEVEL_0 = 0.0
    LEVEL_236 = 0.236
    LEVEL_382 = 0.382
    LEVEL_500 = 0.500
    LEVEL_618 = 0.618
    LEVEL_786 = 0.786
    LEVEL_100 = 1.0
    
    @classmethod
    def major_levels(cls):
        """Return major Fibonacci levels commonly used by traders"""
        return [cls.LEVEL_382, cls.LEVEL_500, cls.LEVEL_618]


class AdvancedIndicatorCalculator:
    """Calculate advanced technical indicators: Stochastic RSI, Renko, Fibonacci"""
    
    @staticmethod
    def calculate_stochastic_rsi(df: pd.DataFrame, rsi_period: int = 14, 
                                stoch_period: int = 14, k_smooth: int = 3, 
                                d_smooth: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic RSI (momentum confirmation indicator)
        
        Args:
            df: DataFrame with 'close' column
            rsi_period: RSI calculation period
            stoch_period: Stochastic period for RSI
            k_smooth: Smoothing period for %K line
            d_smooth: Smoothing period for %D (signal) line
            
        Returns:
            Tuple of (stoch_rsi_k, stoch_rsi_d) Series
        """
        # Calculate RSI first
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Apply Stochastic to RSI
        rsi_low = rsi.rolling(window=stoch_period).min()
        rsi_high = rsi.rolling(window=stoch_period).max()
        
        stoch_rsi = 100 * (rsi - rsi_low) / (rsi_high - rsi_low)
        stoch_rsi = stoch_rsi.fillna(50)  # Fill NaN with 50 (neutral)
        
        # Smooth K and D lines
        stoch_rsi_k = stoch_rsi.rolling(window=k_smooth).mean()
        stoch_rsi_d = stoch_rsi_k.rolling(window=d_smooth).mean()
        
        return stoch_rsi_k, stoch_rsi_d
    
    @staticmethod
    def calculate_renko_bricks(df: pd.DataFrame, brick_size: Optional[float] = None,
                              atr_period: int = 14, atr_multiplier: float = 1.0) -> pd.DataFrame:
        """
        Calculate Renko bars (price-only charting that filters time noise)
        
        Args:
            df: DataFrame with OHLCV data
            brick_size: Fixed brick size in price units. If None, calculate from ATR
            atr_period: Period for ATR calculation (used if brick_size is None)
            atr_multiplier: Multiplier for ATR (e.g., 1.0 means brick_size = ATR)
            
        Returns:
            DataFrame with Renko brick information
        """
        renko_data = []
        
        # Calculate brick size if not provided
        if brick_size is None:
            # Calculate ATR
            high_low = df['high'] - df['low']
            high_close = (df['high'] - df['close'].shift()).abs()
            low_close = (df['low'] - df['close'].shift()).abs()
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(atr_period).mean()
            brick_size = atr.iloc[-1] * atr_multiplier
        
        if brick_size <= 0:
            logger.warning(f"Invalid brick size: {brick_size}, using default 1.0")
            brick_size = 1.0
        
        current_price = df['close'].iloc[0]
        brick_top = current_price
        brick_bottom = current_price
        brick_color = 'neutral'  # 'up', 'down', or 'neutral'
        
        for idx, (date, row) in enumerate(df.iterrows()):
            price = row['close']
            
            # Determine if price has moved enough to form a new brick
            while price >= brick_top + brick_size:
                # Upward brick
                renko_data.append({
                    'date': date,
                    'bar_idx': idx,
                    'brick_color': 'up',
                    'brick_top': brick_top + brick_size,
                    'brick_bottom': brick_top,
                    'price': price
                })
                brick_top += brick_size
                brick_bottom = brick_top - brick_size
                brick_color = 'up'
            
            while price <= brick_bottom - brick_size:
                # Downward brick
                renko_data.append({
                    'date': date,
                    'bar_idx': idx,
                    'brick_color': 'down',
                    'brick_top': brick_bottom,
                    'brick_bottom': brick_bottom - brick_size,
                    'price': price
                })
                brick_bottom -= brick_size
                brick_top = brick_bottom + brick_size
                brick_color = 'down'
        
        return pd.DataFrame(renko_data), brick_size
    
    @staticmethod
    def find_fibonacci_levels(df: pd.DataFrame, swing_idx_start: int, 
                            swing_idx_end: int) -> Dict[str, float]:
        """
        Calculate Fibonacci retracement levels from a swing
        
        Args:
            df: DataFrame with OHLCV data
            swing_idx_start: Start index of the swing (swing low/high)
            swing_idx_end: End index of the swing (swing high/low)
            
        Returns:
            Dict of Fibonacci levels {level_name: price}
        """
        if swing_idx_start >= len(df) or swing_idx_end >= len(df):
            return {}
        
        start_price = df['close'].iloc[swing_idx_start]
        end_price = df['close'].iloc[swing_idx_end]
        
        swing_range = abs(end_price - start_price)
        
        # Determine if it's an upswing or downswing
        if end_price > start_price:
            # Upswing - fib levels are measured downward from top
            levels = {
                '0%': end_price,
                '23.6%': end_price - (swing_range * 0.236),
                '38.2%': end_price - (swing_range * 0.382),
                '50%': end_price - (swing_range * 0.500),
                '61.8%': end_price - (swing_range * 0.618),
                '78.6%': end_price - (swing_range * 0.786),
                '100%': start_price,
            }
        else:
            # Downswing - fib levels are measured upward from bottom
            levels = {
                '0%': end_price,
                '23.6%': end_price + (swing_range * 0.236),
                '38.2%': end_price + (swing_range * 0.382),
                '50%': end_price + (swing_range * 0.500),
                '61.8%': end_price + (swing_range * 0.618),
                '78.6%': end_price + (swing_range * 0.786),
                '100%': start_price,
            }
        
        return levels
    
    @staticmethod
    def find_nearest_fib_level(price: float, fib_levels: Dict[str, float], 
                              threshold_pct: float = 1.0) -> Optional[Tuple[str, float, float]]:
        """
        Find the nearest Fibonacci level to current price
        
        Args:
            price: Current price
            fib_levels: Dict of Fibonacci levels
            threshold_pct: Percentage threshold for "near" level
            
        Returns:
            Tuple of (level_name, level_price, distance_pct) or None
        """
        if not fib_levels:
            return None
        
        nearest = None
        min_distance = float('inf')
        
        for level_name, level_price in fib_levels.items():
            distance_pct = abs(price - level_price) / price * 100
            
            if distance_pct < min_distance:
                min_distance = distance_pct
                nearest = (level_name, level_price, distance_pct)
        
        if nearest and nearest[2] <= threshold_pct:
            return nearest
        
        return None
    
    @staticmethod
    def detect_swing_highs_lows(df: pd.DataFrame, lookback: int = 5) -> Tuple[List[int], List[int]]:
        """
        Detect swing highs and lows using simple pivot detection
        
        Args:
            df: DataFrame with OHLCV data
            lookback: Number of bars to check on each side
            
        Returns:
            Tuple of (swing_high_indices, swing_low_indices)
        """
        highs = []
        lows = []
        
        for i in range(lookback, len(df) - lookback):
            # Check for swing high
            if df['high'].iloc[i] == df['high'].iloc[i-lookback:i+lookback+1].max():
                highs.append(i)
            
            # Check for swing low
            if df['low'].iloc[i] == df['low'].iloc[i-lookback:i+lookback+1].min():
                lows.append(i)
        
        return highs, lows


class AdvancedSignalValidator:
    """Advanced entry/exit validation using Stochastic RSI, Renko, and Fibonacci"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize advanced validator
        
        Args:
            df: DataFrame with OHLCV data
        """
        self.df = df
        self.calculator = AdvancedIndicatorCalculator()
        
        # Calculate indicators
        self.stoch_rsi_k, self.stoch_rsi_d = self.calculator.calculate_stochastic_rsi(df)
        self.renko_bricks, self.brick_size = self.calculator.calculate_renko_bricks(df)
        
        # Find swing points for Fibonacci
        self.swing_highs, self.swing_lows = self.calculator.detect_swing_highs_lows(df)
        
        logger.info(f"✓ Advanced indicators initialized")
        logger.info(f"  Brick size: {self.brick_size:.2f}")
        logger.info(f"  Swing points: {len(self.swing_highs)} highs, {len(self.swing_lows)} lows")
    
    def validate_entry_with_stoch_rsi(self, bar_idx: int, signal_type: str = 'BUY',
                                     oversold_threshold: float = 20,
                                     overbought_threshold: float = 80) -> Dict:
        """
        Validate entry using Stochastic RSI momentum confirmation
        
        Args:
            bar_idx: Current bar index
            signal_type: 'BUY' or 'SELL'
            oversold_threshold: Stoch RSI level for oversold
            overbought_threshold: Stoch RSI level for overbought
            
        Returns:
            Dict with validation results
        """
        if bar_idx >= len(self.df):
            return {'valid': False, 'reason': 'Invalid bar index'}
        
        stoch_k = self.stoch_rsi_k.iloc[bar_idx]
        stoch_d = self.stoch_rsi_d.iloc[bar_idx]
        
        # Get previous values for cross detection
        if bar_idx > 0:
            prev_k = self.stoch_rsi_k.iloc[bar_idx - 1]
            prev_d = self.stoch_rsi_d.iloc[bar_idx - 1]
        else:
            return {'valid': False, 'reason': 'Insufficient data'}
        
        reasons = []
        score = 0.0
        
        if signal_type == 'BUY':
            # For BUY: Look for K crossing above D from oversold territory
            # This signals momentum turning from negative to positive
            is_oversold = stoch_k < oversold_threshold
            k_above_d = stoch_k > stoch_d
            k_crosses_d = (prev_k <= prev_d) and (stoch_k > stoch_d)
            
            if is_oversold and k_crosses_d:
                score = 1.0
                reasons.append(f"Strong: K crosses above D from oversold (K={stoch_k:.1f})")
            elif is_oversold and k_above_d:
                score = 0.8
                reasons.append(f"Good: K above D in oversold zone (K={stoch_k:.1f})")
            elif k_above_d and stoch_k < 50:
                score = 0.6
                reasons.append(f"Moderate: K above D below midpoint (K={stoch_k:.1f})")
            elif stoch_k >= 50:
                score = 0.3
                reasons.append(f"Weak: K above midpoint (already advanced move, K={stoch_k:.1f})")
            else:
                score = 0.0
                reasons.append(f"Invalid: K below D in potential downtrend (K={stoch_k:.1f})")
        
        else:  # SELL
            # For SELL: Look for K crossing below D from overbought territory
            is_overbought = stoch_k > overbought_threshold
            k_below_d = stoch_k < stoch_d
            k_crosses_d = (prev_k >= prev_d) and (stoch_k < stoch_d)
            
            if is_overbought and k_crosses_d:
                score = 1.0
                reasons.append(f"Strong: K crosses below D from overbought (K={stoch_k:.1f})")
            elif is_overbought and k_below_d:
                score = 0.8
                reasons.append(f"Good: K below D in overbought zone (K={stoch_k:.1f})")
            elif k_below_d and stoch_k > 50:
                score = 0.6
                reasons.append(f"Moderate: K below D above midpoint (K={stoch_k:.1f})")
            elif stoch_k <= 50:
                score = 0.3
                reasons.append(f"Weak: K below midpoint (already declined, K={stoch_k:.1f})")
            else:
                score = 0.0
                reasons.append(f"Invalid: K above D in potential uptrend (K={stoch_k:.1f})")
        
        return {
            'valid': score >= 0.5,
            'score': score,
            'stoch_k': stoch_k,
            'stoch_d': stoch_d,
            'reasons': reasons
        }
    
    def validate_entry_with_renko(self, bar_idx: int) -> Dict:
        """
        Validate entry using Renko bar confirmation (trend clarity)
        
        Args:
            bar_idx: Current bar index
            
        Returns:
            Dict with Renko trend validation
        """
        if len(self.renko_bricks) == 0:
            return {'valid': False, 'reason': 'No Renko bricks generated'}
        
        # Get recent Renko bricks
        recent_bricks = self.renko_bricks[self.renko_bricks['bar_idx'] <= bar_idx].tail(10)
        
        if len(recent_bricks) == 0:
            return {'valid': False, 'reason': 'No recent Renko bricks'}
        
        # Count consecutive bricks of same color (trend strength)
        upbricks = (recent_bricks['brick_color'] == 'up').sum()
        downbricks = (recent_bricks['brick_color'] == 'down').sum()
        
        last_brick = recent_bricks.iloc[-1]
        last_color = last_brick['brick_color']
        
        # Analyze trend consistency
        if upbricks > downbricks:
            trend = 'uptrend'
            trend_strength = upbricks / len(recent_bricks)
            score = min(trend_strength, 1.0)
            reason = f"Uptrend confirmed: {upbricks} up vs {downbricks} down bricks"
        elif downbricks > upbricks:
            trend = 'downtrend'
            trend_strength = downbricks / len(recent_bricks)
            score = min(trend_strength, 1.0)
            reason = f"Downtrend confirmed: {downbricks} down vs {upbricks} up bricks"
        else:
            trend = 'ranging'
            score = 0.3
            reason = f"Range-bound market: {upbricks} up vs {downbricks} down bricks"
        
        return {
            'valid': score >= 0.5,
            'score': score,
            'trend': trend,
            'last_brick_color': last_color,
            'reason': reason,
            'brick_size': self.brick_size
        }
    
    def validate_entry_with_fibonacci(self, bar_idx: int, signal_type: str = 'BUY',
                                    proximity_threshold: float = 1.0) -> Dict:
        """
        Validate entry using Fibonacci retracement levels (confluence)
        
        Args:
            bar_idx: Current bar index
            signal_type: 'BUY' or 'SELL'
            proximity_threshold: % distance to be considered "at" a Fib level
            
        Returns:
            Dict with Fibonacci confluence validation
        """
        if len(self.swing_highs) < 1 or len(self.swing_lows) < 1:
            return {'valid': False, 'reason': 'Insufficient swing data for Fibonacci'}
        
        # Get most recent swing for Fibonacci calculation
        recent_high_idx = [h for h in self.swing_highs if h < bar_idx][-1] if any(h < bar_idx for h in self.swing_highs) else None
        recent_low_idx = [l for l in self.swing_lows if l < bar_idx][-1] if any(l < bar_idx for l in self.swing_lows) else None
        
        if recent_high_idx is None or recent_low_idx is None:
            return {'valid': False, 'reason': 'No prior swing found'}
        
        # Determine which swing to use (most recent completed move)
        if recent_high_idx > recent_low_idx:
            # Last major move was downward, so use high to low
            swing_idx_start = recent_high_idx
            swing_idx_end = recent_low_idx
            swing_type = 'downswing'
        else:
            # Last major move was upward, so use low to high
            swing_idx_start = recent_low_idx
            swing_idx_end = recent_high_idx
            swing_type = 'upswing'
        
        # Calculate Fibonacci levels
        fib_levels = self.calculator.find_fibonacci_levels(self.df, swing_idx_start, swing_idx_end)
        current_price = self.df['close'].iloc[bar_idx]
        
        # Find nearest Fibonacci level
        nearest = self.calculator.find_nearest_fib_level(current_price, fib_levels, proximity_threshold)
        
        reasons = []
        score = 0.0
        
        if nearest:
            level_name, level_price, distance = nearest
            reasons.append(f"At Fibonacci {level_name} level (±{distance:.2f}%)")
            
            # BUY at support levels, SELL at resistance
            if signal_type == 'BUY':
                # Better to buy at support (61.8%, 50%, 38.2%)
                if level_name in ['61.8%', '50%', '38.2%']:
                    score = 0.9
                    reasons.append("✓ Classic support level for BUY setup")
                elif level_name in ['78.6%', '23.6%']:
                    score = 0.6
                    reasons.append("~ Moderate support level")
                else:
                    score = 0.3
                    reasons.append("⚠ Weak alignment with Fibonacci support")
            else:  # SELL
                # Better to sell at resistance
                if level_name in ['38.2%', '50%', '61.8%']:
                    score = 0.9
                    reasons.append("✓ Classic resistance level for SELL setup")
                elif level_name in ['23.6%', '78.6%']:
                    score = 0.6
                    reasons.append("~ Moderate resistance level")
                else:
                    score = 0.3
                    reasons.append("⚠ Weak alignment with Fibonacci resistance")
        else:
            score = 0.2
            reasons.append(f"Away from major Fibonacci levels (>±{proximity_threshold}%)")
        
        return {
            'valid': score >= 0.5,
            'score': score,
            'fib_levels': fib_levels,
            'nearest_level': nearest,
            'swing_type': swing_type,
            'reasons': reasons
        }
    
    def multi_indicator_confirmation(self, bar_idx: int, signal_type: str = 'BUY',
                                     weights: Optional[Dict] = None) -> Dict:
        """
        Combine Stochastic RSI, Renko, and Fibonacci for multi-factor confirmation
        
        Args:
            bar_idx: Current bar index
            signal_type: 'BUY' or 'SELL'
            weights: Dict of weights for each indicator {stoch_rsi, renko, fib}
            
        Returns:
            Combined validation score and reasons
        """
        # Default weights
        if weights is None:
            weights = {
                'stoch_rsi': 0.35,
                'renko': 0.35,
                'fib': 0.30
            }
        
        # Get individual validations
        stoch_result = self.validate_entry_with_stoch_rsi(bar_idx, signal_type)
        renko_result = self.validate_entry_with_renko(bar_idx)
        fib_result = self.validate_entry_with_fibonacci(bar_idx, signal_type)
        
        # Calculate weighted score
        total_weight = sum(weights.values())
        composite_score = (
            stoch_result.get('score', 0) * weights.get('stoch_rsi', 0) +
            renko_result.get('score', 0) * weights.get('renko', 0) +
            fib_result.get('score', 0) * weights.get('fib', 0)
        ) / total_weight
        
        all_reasons = []
        all_reasons.extend([f"[Stoch RSI {weights['stoch_rsi']*100:.0f}%] " + r for r in stoch_result.get('reasons', [])])
        all_reasons.extend([f"[Renko {weights['renko']*100:.0f}%] " + renko_result.get('reason', '')])
        all_reasons.extend([f"[Fibonacci {weights['fib']*100:.0f}%] " + r for r in fib_result.get('reasons', [])])
        
        return {
            'valid': composite_score >= 0.50,
            'composite_score': composite_score,
            'stoch_rsi': stoch_result,
            'renko': renko_result,
            'fibonacci': fib_result,
            'all_reasons': all_reasons,
            'weights': weights
        }


def main():
    """Demo/testing function"""
    # This would be integrated with existing backtesting framework
    logger.info("Advanced Signal Validator ready for integration")
    logger.info("Supports: Stochastic RSI, Renko Bars, Fibonacci Retracements")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
