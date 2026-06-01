#!/usr/bin/env python3
"""
Filter Hierarchy: Phase 1 Remediation Implementation
Implements hierarchical confluence logic instead of rigid AND conditions
Replaces: "StochRSI AND Fib AND Renko" with context-driven 2-of-3 logic
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classification"""
    EXTREME_DOWNTREND = "extreme_downtrend"      # Steep drops >5% in 3 days
    STRONG_DOWNTREND = "strong_downtrend"        # Clear downtrend
    MILD_DOWNTREND = "mild_downtrend"            # Slight downward pressure
    CONSOLIDATION = "consolidation"              # Range-bound, no clear trend
    MILD_UPTREND = "mild_uptrend"                # Slight upward pressure
    STRONG_UPTREND = "strong_uptrend"            # Clear uptrend
    EXTREME_UPTREND = "extreme_uptrend"          # Steep rallies >5% in 3 days


class FilterConfidence(Enum):
    """Confidence levels for each filter"""
    HIGH = "high"                                 # Filter strongly signals (>75%)
    MEDIUM = "medium"                             # Filter moderately signals (50-75%)
    LOW = "low"                                   # Filter weakly signals (<50%)
    NEUTRAL = "neutral"                           # Filter is neutral/undecided


class RegimeDetector:
    """
    Detects market regime using:
    - Rate of Change (ROC): Detect steep moves
    - Average True Range (ATR): Detect volatility
    - ADX: Detect trend strength
    - Moving averages: Detect trend direction
    """
    
    def __init__(self, df: pd.DataFrame, lookback: int = 20):
        """
        Initialize regime detector
        
        Args:
            df: DataFrame with OHLCV data
            lookback: Period for trend detection
        """
        self.df = df
        self.lookback = lookback
        self._calculate_indicators()
    
    def _calculate_indicators(self):
        """Calculate all regime detection indicators"""
        # ATR for volatility
        high_low = self.df['high'] - self.df['low']
        high_close = (self.df['high'] - self.df['close'].shift()).abs()
        low_close = (self.df['low'] - self.df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        self.atr = tr.rolling(14).mean()
        
        # ADX for trend strength (simplified version)
        # Using DMI components
        up_move = self.df['high'].diff()
        down_move = -self.df['low'].diff()
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        plus_di = 100 * pd.Series(plus_dm).rolling(14).mean() / self.atr
        minus_di = 100 * pd.Series(minus_dm).rolling(14).mean() / self.atr
        
        di_diff = np.abs(plus_di - minus_di)
        di_sum = plus_di + minus_di
        self.adx = 100 * di_diff / (di_sum + 0.0001)
        
        # Moving averages for trend direction
        self.sma_20 = self.df['close'].rolling(20).mean()
        self.sma_50 = self.df['close'].rolling(50).mean()
        
        # Rate of Change for momentum
        self.roc_3d = self.df['close'].pct_change(3) * 100
        self.roc_5d = self.df['close'].pct_change(5) * 100
    
    def get_regime(self, bar_idx: int) -> MarketRegime:
        """
        Classify market regime at given bar
        
        Args:
            bar_idx: Index of current bar
            
        Returns:
            MarketRegime enum value
        """
        if bar_idx < 50:  # Need enough history
            return MarketRegime.CONSOLIDATION
        
        close = self.df['close'].iloc[bar_idx]
        sma_20 = self.sma_20.iloc[bar_idx]
        sma_50 = self.sma_50.iloc[bar_idx]
        roc_3 = self.roc_3d.iloc[bar_idx]
        atr_pct = (self.atr.iloc[bar_idx] / close * 100) if close > 0 else 0
        
        # Classify based on multiple factors
        
        # Extreme downtrend: steep drop + high volatility + below both MAs
        if (roc_3 < -5.0 and 
            atr_pct > 3.0 and 
            close < sma_20 and 
            close < sma_50):
            return MarketRegime.EXTREME_DOWNTREND
        
        # Strong downtrend: below both MAs, negative ROC
        if (close < sma_20 and 
            close < sma_50 and 
            roc_3 < -2.0):
            return MarketRegime.STRONG_DOWNTREND
        
        # Mild downtrend: below SMA50, slightly below SMA20
        if (close < sma_50 and 
            close < sma_20 and 
            roc_3 >= -2.0):
            return MarketRegime.MILD_DOWNTREND
        
        # Extreme uptrend: steep rally + high volatility + above both MAs
        if (roc_3 > 5.0 and 
            atr_pct > 3.0 and 
            close > sma_20 and 
            close > sma_50):
            return MarketRegime.EXTREME_UPTREND
        
        # Strong uptrend: above both MAs, positive ROC
        if (close > sma_20 and 
            close > sma_50 and 
            roc_3 > 2.0):
            return MarketRegime.STRONG_UPTREND
        
        # Mild uptrend: above SMA50, slightly above SMA20
        if (close > sma_50 and 
            close > sma_20 and 
            roc_3 >= 0):
            return MarketRegime.MILD_UPTREND
        
        # Default: consolidation
        return MarketRegime.CONSOLIDATION
    
    def get_adaptive_thresholds(self, regime: MarketRegime) -> Dict:
        """
        Get adaptive filter thresholds based on market regime
        
        Args:
            regime: Current market regime
            
        Returns:
            Dict of adaptive thresholds
        """
        thresholds = {
            MarketRegime.EXTREME_DOWNTREND: {
                'stoch_oversold': 30,        # Relax from 20
                'stoch_overbought': 70,
                'fib_zones': [0.25, 0.75],   # Broader support zones
                'renko_lag_allowed': 1,      # Allow 1-bar lag
                'position_size': 0.67,       # 2/3 size due to risk
                'confidence_threshold': 0.5,  # Need at least 50% confidence
            },
            MarketRegime.STRONG_DOWNTREND: {
                'stoch_oversold': 25,
                'stoch_overbought': 75,
                'fib_zones': [0.38, 0.62],
                'renko_lag_allowed': 0,
                'position_size': 0.80,
                'confidence_threshold': 0.6,
            },
            MarketRegime.MILD_DOWNTREND: {
                'stoch_oversold': 20,        # Standard
                'stoch_overbought': 80,
                'fib_zones': [0.382, 0.618],
                'renko_lag_allowed': 0,
                'position_size': 1.0,
                'confidence_threshold': 0.65,
            },
            MarketRegime.CONSOLIDATION: {
                'stoch_oversold': 20,        # Standard
                'stoch_overbought': 80,
                'fib_zones': [0.382, 0.618],
                'renko_lag_allowed': 0,
                'position_size': 1.0,
                'confidence_threshold': 0.70,  # Stricter in sideways
            },
            MarketRegime.MILD_UPTREND: {
                'stoch_oversold': 15,        # Stricter in uptrend
                'stoch_overbought': 85,
                'fib_zones': [0.236, 0.50],  # Only strongest pulls
                'renko_lag_allowed': 0,
                'position_size': 0.75,
                'confidence_threshold': 0.65,
            },
            MarketRegime.STRONG_UPTREND: {
                'stoch_oversold': 10,
                'stoch_overbought': 90,
                'fib_zones': [0.236, 0.382],
                'renko_lag_allowed': 0,
                'position_size': 0.60,
                'confidence_threshold': 0.70,
            },
            MarketRegime.EXTREME_UPTREND: {
                'stoch_oversold': 5,
                'stoch_overbought': 95,
                'fib_zones': [0.236, 0.382],
                'renko_lag_allowed': 0,
                'position_size': 0.50,
                'confidence_threshold': 0.75,
            },
        }
        return thresholds.get(regime, thresholds[MarketRegime.CONSOLIDATION])


class FilterHierarchy:
    """
    Implements hierarchical confluence logic (2-of-3) instead of rigid AND
    
    Hierarchy:
    Level 1 (Foundation): Price Structure (Fibonacci)
    Level 2 (Context): Trend Confirmation (Renko)
    Level 3 (Timing): Momentum Trigger (Stochastic RSI)
    
    Decision Logic:
    - High price structure + medium-high trend → lower momentum threshold
    - High price structure + decent momentum → allow trade even without perfect renko
    - High trend confirmation + decent momentum → allow trade without perfect fib
    - Otherwise: don't trade
    """
    
    def __init__(self, df: pd.DataFrame, advanced_validator):
        """
        Initialize FilterHierarchy
        
        Args:
            df: DataFrame with OHLCV data
            advanced_validator: AdvancedSignalValidator instance with indicators calculated
        """
        self.df = df
        self.validator = advanced_validator
        self.regime_detector = RegimeDetector(df)
        
        logger.info("✓ FilterHierarchy initialized (2-of-3 hierarchical logic)")
    
    def evaluate_fib_confidence(self, bar_idx: int, signal_type: str = 'BUY') -> Tuple[FilterConfidence, float, Dict]:
        """
        Evaluate Fibonacci filter confidence
        
        Args:
            bar_idx: Current bar index
            signal_type: 'BUY' or 'SELL'
            
        Returns:
            Tuple of (confidence_level, confidence_score, details)
        """
        fib_result = self.validator.validate_entry_with_fibonacci(bar_idx, signal_type)
        
        if fib_result.get('valid'):
            # Fibonacci validation passed
            distance = fib_result.get('distance_to_fib', 100)
            
            if distance < 0.5:
                confidence = FilterConfidence.HIGH
                score = 0.95
            elif distance < 1.0:
                confidence = FilterConfidence.HIGH
                score = 0.85
            elif distance < 2.0:
                confidence = FilterConfidence.MEDIUM
                score = 0.70
            else:
                confidence = FilterConfidence.LOW
                score = 0.40
        else:
            # Check if price is near recent low (alternative)
            recent_low = self.df['low'].iloc[max(0, bar_idx-10):bar_idx].min()
            current_price = self.df['close'].iloc[bar_idx]
            distance_to_low_pct = (current_price - recent_low) / recent_low * 100
            
            if distance_to_low_pct < 1.0:
                # Very close to recent low - medium confidence as alternative support
                confidence = FilterConfidence.MEDIUM
                score = 0.60
            else:
                confidence = FilterConfidence.LOW
                score = 0.25
        
        return confidence, score, fib_result
    
    def evaluate_renko_confidence(self, bar_idx: int) -> Tuple[FilterConfidence, float, Dict]:
        """
        Evaluate Renko filter confidence
        
        Args:
            bar_idx: Current bar index
            
        Returns:
            Tuple of (confidence_level, confidence_score, details)
        """
        renko_result = self.validator.validate_entry_with_renko(bar_idx)
        
        if renko_result.get('valid'):
            confidence = FilterConfidence.HIGH
            score = 0.90
        else:
            # Check if price is moving (even without brick confirmation)
            if bar_idx > 0:
                recent_bars = self.df['close'].iloc[max(0, bar_idx-3):bar_idx]
                momentum = (recent_bars.iloc[-1] - recent_bars.iloc[0]) / recent_bars.iloc[0] * 100
                
                if momentum > 0:
                    confidence = FilterConfidence.MEDIUM
                    score = 0.60
                else:
                    confidence = FilterConfidence.LOW
                    score = 0.30
            else:
                confidence = FilterConfidence.LOW
                score = 0.20
        
        return confidence, score, renko_result
    
    def evaluate_stoch_rsi_confidence(self, bar_idx: int, signal_type: str = 'BUY') -> Tuple[FilterConfidence, float, Dict]:
        """
        Evaluate Stochastic RSI filter confidence
        
        Args:
            bar_idx: Current bar index
            signal_type: 'BUY' or 'SELL'
            
        Returns:
            Tuple of (confidence_level, confidence_score, details)
        """
        stoch_result = self.validator.validate_entry_with_stoch_rsi(bar_idx, signal_type)
        
        if stoch_result.get('valid'):
            # Check how extreme the reading is
            stoch_k = self.validator.stoch_rsi_k.iloc[bar_idx]
            
            if signal_type == 'BUY':
                if stoch_k < 10:
                    confidence = FilterConfidence.HIGH
                    score = 0.95
                elif stoch_k < 25:
                    confidence = FilterConfidence.HIGH
                    score = 0.85
                elif stoch_k < 35:
                    confidence = FilterConfidence.MEDIUM
                    score = 0.65
                else:
                    confidence = FilterConfidence.LOW
                    score = 0.40
            else:  # SELL
                if stoch_k > 90:
                    confidence = FilterConfidence.HIGH
                    score = 0.95
                elif stoch_k > 75:
                    confidence = FilterConfidence.HIGH
                    score = 0.85
                elif stoch_k > 65:
                    confidence = FilterConfidence.MEDIUM
                    score = 0.65
                else:
                    confidence = FilterConfidence.LOW
                    score = 0.40
        else:
            confidence = FilterConfidence.LOW
            score = 0.20
        
        return confidence, score, stoch_result
    
    def should_trade_hierarchical(self, bar_idx: int, signal_type: str = 'BUY') -> Tuple[bool, float, Dict]:
        """
        Make trade decision using hierarchical 2-of-3 logic
        
        Replaces: StochRSI AND Fib AND Renko
        With: Hierarchical context-driven decision
        
        Args:
            bar_idx: Current bar index
            signal_type: 'BUY' or 'SELL'
            
        Returns:
            Tuple of (should_trade, signal_quality, details)
        """
        # Get market regime for adaptive thresholds
        regime = self.regime_detector.get_regime(bar_idx)
        adaptive_thresholds = self.regime_detector.get_adaptive_thresholds(regime)
        
        # Evaluate each filter's confidence
        fib_conf, fib_score, fib_details = self.evaluate_fib_confidence(bar_idx, signal_type)
        renko_conf, renko_score, renko_details = self.evaluate_renko_confidence(bar_idx)
        stoch_conf, stoch_score, stoch_details = self.evaluate_stoch_rsi_confidence(bar_idx, signal_type)
        
        # Hierarchical decision logic
        decisions = []
        
        # Pattern 1: Strong price structure + medium-high trend → lower momentum threshold
        if fib_conf == FilterConfidence.HIGH and renko_conf in [FilterConfidence.HIGH, FilterConfidence.MEDIUM]:
            # Can enter with medium momentum
            if stoch_score > 0.55:
                decisions.append(('Pattern1_FibRenko', True, fib_score * 0.4 + renko_score * 0.4 + stoch_score * 0.2))
        
        # Pattern 2: Strong price structure + decent momentum → allow trade without perfect renko
        if fib_conf == FilterConfidence.HIGH and stoch_score > 0.65:
            decisions.append(('Pattern2_FibStoch', True, fib_score * 0.5 + stoch_score * 0.5))
        
        # Pattern 3: Strong trend confirmation + decent momentum → allow trade without perfect fib
        if renko_conf == FilterConfidence.HIGH and stoch_score > 0.60:
            decisions.append(('Pattern3_RenkoStoch', True, renko_score * 0.5 + stoch_score * 0.5))
        
        # Pattern 4: All three conditions are strong → high confidence full trade
        if fib_conf == FilterConfidence.HIGH and renko_conf == FilterConfidence.HIGH and stoch_conf == FilterConfidence.HIGH:
            decisions.append(('Pattern4_All', True, (fib_score + renko_score + stoch_score) / 3))
        
        # Calculate final decision
        if decisions:
            # Sort by signal quality (descending)
            decisions.sort(key=lambda x: x[2], reverse=True)
            pattern, should_trade, quality = decisions[0]
            
            return True, quality, {
                'regime': regime.value,
                'pattern': pattern,
                'signal_quality': quality,
                'fib': {'confidence': fib_conf.value, 'score': fib_score},
                'renko': {'confidence': renko_conf.value, 'score': renko_score},
                'stoch_rsi': {'confidence': stoch_conf.value, 'score': stoch_score},
                'adaptive_thresholds': adaptive_thresholds,
            }
        else:
            # No pattern matched - don't trade
            return False, 0.0, {
                'regime': regime.value,
                'pattern': 'none',
                'signal_quality': 0.0,
                'fib': {'confidence': fib_conf.value, 'score': fib_score},
                'renko': {'confidence': renko_conf.value, 'score': renko_score},
                'stoch_rsi': {'confidence': stoch_conf.value, 'score': stoch_score},
                'adaptive_thresholds': adaptive_thresholds,
            }


def main():
    """Demo function"""
    logger.info("FilterHierarchy ready for integration")
    logger.info("Implements 2-of-3 hierarchical confluence logic")
    logger.info("Supports: Extreme/Strong/Mild Downtrend, Consolidation, Uptrend regimes")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
