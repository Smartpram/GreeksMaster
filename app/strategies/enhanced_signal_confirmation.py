#!/usr/bin/env python3
"""
Enhanced Signal Confirmation with Multiple Indicators & Strategy Layers
Implements regime detection, entry confirmation, volume/volatility filters, and strategy layering
to improve robustness across different market conditions.

Author: AI Trading System
Date: May 2026
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple, List, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classification"""
    STRONG_UPTREND = "strong_uptrend"      # ADX > 25, price > MA, +DI > -DI
    UPTREND = "uptrend"                    # ADX > 20, price > MA
    MILD_UPTREND = "mild_uptrend"          # ADX < 20, price > MA
    SIDEWAYS = "sideways"                  # ADX < 20, price near MA
    MILD_DOWNTREND = "mild_downtrend"      # ADX < 20, price < MA
    DOWNTREND = "downtrend"                # ADX > 20, price < MA
    STRONG_DOWNTREND = "strong_downtrend"  # ADX > 25, price < MA, -DI > +DI
    UNKNOWN = "unknown"


class TechnicalIndicators:
    """Calculate technical indicators for signal confirmation"""
    
    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Average Directional Index (ADX) and directional indicators (+DI, -DI)
        
        Returns:
            Tuple of (ADX, +DI, -DI)
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Calculate true range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        
        # Calculate directional movements
        dm_plus = np.where(high.diff() > low.diff().abs(), high.diff(), 0)
        dm_minus = np.where(low.diff().abs() > high.diff(), low.diff().abs(), 0)
        
        # Calculate directional indicators
        di_plus = 100 * pd.Series(dm_plus).rolling(period).mean() / atr
        di_minus = 100 * pd.Series(dm_minus).rolling(period).mean() / atr
        
        # Calculate ADX
        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus + 1e-10)
        adx = dx.rolling(period).mean()
        
        return adx, di_plus, di_minus
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index (RSI)"""
        if len(prices) < period + 1:
            return pd.Series([50] * len(prices), index=prices.index)
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50)
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands
        
        Returns:
            Tuple of (Middle Band, Upper Band, Lower Band)
        """
        sma = prices.rolling(period).mean()
        std = prices.rolling(period).std()
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return sma, upper, lower
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range (ATR) for volatility measurement"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(period).mean()
        return atr


class EnhancedSignalConfirmation:
    """
    Multi-layer signal confirmation system with regime detection,
    momentum validation, volume filters, and strategy adaptation
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with OHLCV data
        
        Args:
            df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
        """
        self.df = df.copy()
        self.ti = TechnicalIndicators()
        
        # Calculate all indicators
        self._calculate_indicators()
    
    def _calculate_indicators(self):
        """Calculate all technical indicators"""
        logger.info("Calculating technical indicators...")
        
        # Trend indicators
        self.df['adx'], self.df['di_plus'], self.df['di_minus'] = self.ti.calculate_adx(self.df, period=14)
        self.df['ma50'] = self.df['close'].rolling(50).mean()
        self.df['ma200'] = self.df['close'].rolling(200).mean()
        
        # Momentum indicators
        self.df['rsi'] = self.ti.calculate_rsi(self.df['close'], period=14)
        self.df['macd'], self.df['macd_signal'], self.df['macd_hist'] = self.ti.calculate_macd(self.df['close'])
        
        # Volatility indicators
        self.df['atr'] = self.ti.calculate_atr(self.df, period=14)
        self.df['bb_mid'], self.df['bb_upper'], self.df['bb_lower'] = self.ti.calculate_bollinger_bands(
            self.df['close'], period=20, std_dev=2
        )
        
        # Volume indicators
        self.df['volume_ma20'] = self.df['volume'].rolling(20).mean()
        self.df['rvol'] = self.df['volume'] / (self.df['volume_ma20'] + 1e-10)
        
        # Volatility regime (normalized ATR)
        self.df['atr_ma'] = self.df['atr'].rolling(14).mean()
        self.df['volatility_ratio'] = self.df['atr'] / (self.df['atr_ma'] + 1e-10)
        
        logger.info("✓ Indicators calculated successfully")
    
    def detect_regime(self, bar_idx: int) -> MarketRegime:
        """
        Detect current market regime based on ADX, price position relative to MA, and DI
        
        Args:
            bar_idx: Index in dataframe to analyze
            
        Returns:
            MarketRegime enum value
        """
        if bar_idx < 200:  # Need enough data
            return MarketRegime.UNKNOWN
        
        row = self.df.iloc[bar_idx]
        
        adx = row['adx']
        price = row['close']
        ma50 = row['ma50']
        ma200 = row['ma200']
        di_plus = row['di_plus']
        di_minus = row['di_minus']
        
        # Determine trend direction
        if price > ma200 and price > ma50:
            if adx > 25:
                if di_plus > di_minus:
                    return MarketRegime.STRONG_UPTREND
                else:
                    return MarketRegime.UPTREND
            elif adx > 20:
                return MarketRegime.UPTREND
            else:
                return MarketRegime.MILD_UPTREND
        
        elif price < ma200 and price < ma50:
            if adx > 25:
                if di_minus > di_plus:
                    return MarketRegime.STRONG_DOWNTREND
                else:
                    return MarketRegime.DOWNTREND
            elif adx > 20:
                return MarketRegime.DOWNTREND
            else:
                return MarketRegime.MILD_DOWNTREND
        
        else:
            # Price between MAs or near one
            if adx < 20:
                return MarketRegime.SIDEWAYS
            elif price > ma50:
                return MarketRegime.MILD_UPTREND
            else:
                return MarketRegime.MILD_DOWNTREND
    
    def validate_entry_signal(self, bar_idx: int, signal_type: str = 'LONG') -> Dict[str, any]:
        """
        Multi-layer entry signal validation
        
        Args:
            bar_idx: Index in dataframe
            signal_type: 'LONG' or 'SHORT'
            
        Returns:
            Dict with validation results and reasoning
        """
        # Only require 20 bars minimum (for MA20 calculation)
        if bar_idx < 20:
            return {
                'valid': False,
                'reason': 'Insufficient data for indicators',
                'regime': MarketRegime.UNKNOWN,
                'scores': {},
                'overall_score': 0.0
            }
        
        row = self.df.iloc[bar_idx]
        regime = self.detect_regime(bar_idx)
        
        scores = {}
        reasons = []
        
        # 1. Regime Check - Price and MA alignment (or reversal from oversold)
        if signal_type == 'LONG':
            # Primary: Price above key MAs
            price_above_mas = row['close'] > row['ma200'] and row['close'] > row['ma50']
            # Secondary: Reversal from oversold (RSI < 30) with bounce
            rsi_reversal = row['rsi'] < 35
            
            if price_above_mas:
                scores['regime'] = 1.0
                reasons.append(f"Uptrend confirmed (price above MA200 & MA50)")
            elif rsi_reversal:
                scores['regime'] = 0.7
                reasons.append(f"Reversal setup from oversold (RSI={row['rsi']:.1f})")
            else:
                scores['regime'] = 0.2
                reasons.append(f"Price below key MAs (potential bounce)")
        else:  # SHORT
            regime_valid = row['close'] < row['ma200'] and row['close'] < row['ma50']
            if regime_valid:
                scores['regime'] = 1.0
            else:
                scores['regime'] = 0.0
                reasons.append(f"Price above key MAs (against downtrend)")
        
        # 2. ADX Trend Strength Check
        adx = row['adx']
        if adx > 25:
            scores['adx'] = 1.0
            reasons.append(f"Strong trend (ADX={adx:.1f})")
        elif adx > 20:
            scores['adx'] = 0.8
            reasons.append(f"Moderate trend (ADX={adx:.1f})")
        elif adx > 15:
            scores['adx'] = 0.5
            reasons.append(f"Weak trend (ADX={adx:.1f})")
        else:
            scores['adx'] = 0.3
            reasons.append(f"Range-bound (ADX={adx:.1f}) - risky for trend entry")
        
        # 3. RSI Momentum Check
        rsi = row['rsi']
        if signal_type == 'LONG':
            if rsi > 50:
                scores['rsi'] = 1.0
                reasons.append(f"Bullish momentum (RSI={rsi:.1f})")
            elif rsi > 40:
                scores['rsi'] = 0.7
                reasons.append(f"Neutral momentum (RSI={rsi:.1f})")
            elif rsi > 30:
                scores['rsi'] = 0.3
                reasons.append(f"Weak momentum (RSI={rsi:.1f}) - below midpoint")
            else:
                scores['rsi'] = 0.0
                reasons.append(f"Oversold extremes (RSI={rsi:.1f}) - risky entry point")
        else:  # SHORT
            if rsi < 50:
                scores['rsi'] = 1.0
                reasons.append(f"Bearish momentum (RSI={rsi:.1f})")
            elif rsi < 60:
                scores['rsi'] = 0.7
                reasons.append(f"Neutral momentum (RSI={rsi:.1f})")
            elif rsi < 70:
                scores['rsi'] = 0.3
                reasons.append(f"Weak momentum (RSI={rsi:.1f}) - above midpoint")
            else:
                scores['rsi'] = 0.0
                reasons.append(f"Overbought extremes (RSI={rsi:.1f}) - risky entry point")
        
        # 4. MACD Momentum Confirmation
        macd_hist = row['macd_hist']
        macd = row['macd']
        macd_signal = row['macd_signal']
        
        if signal_type == 'LONG':
            if macd > macd_signal and macd_hist > 0:
                scores['macd'] = 1.0
                reasons.append(f"MACD bullish (line above signal, positive histogram)")
            elif macd > macd_signal:
                scores['macd'] = 0.7
                reasons.append(f"MACD line above signal (momentum building)")
            else:
                scores['macd'] = 0.2
                reasons.append(f"MACD bearish or weak (line below signal)")
        else:  # SHORT
            if macd < macd_signal and macd_hist < 0:
                scores['macd'] = 1.0
                reasons.append(f"MACD bearish (line below signal, negative histogram)")
            elif macd < macd_signal:
                scores['macd'] = 0.7
                reasons.append(f"MACD line below signal (bearish)")
            else:
                scores['macd'] = 0.2
                reasons.append(f"MACD bullish or weak (line above signal)")
        
        # 5. Volume Filter
        rvol = row['rvol']
        if rvol > 1.5:
            scores['volume'] = 1.0
            reasons.append(f"Strong volume (RVOL={rvol:.2f}x average)")
        elif rvol > 1.0:
            scores['volume'] = 0.7
            reasons.append(f"Decent volume (RVOL={rvol:.2f}x average)")
        else:
            scores['volume'] = 0.3
            reasons.append(f"Low volume (RVOL={rvol:.2f}x average) - lacks conviction")
        
        # 6. Volatility Regime Check
        vol_ratio = row['volatility_ratio']
        if vol_ratio < 0.5:
            scores['volatility'] = 0.2
            reasons.append(f"Extreme low volatility (compressed) - breakout risk")
        elif vol_ratio > 2.0:
            scores['volatility'] = 0.3
            reasons.append(f"Extreme high volatility ({vol_ratio:.2f}x normal) - whipsaw risk")
        else:
            scores['volatility'] = 1.0
            reasons.append(f"Normal volatility regime - suitable for trading")
        
        # Calculate overall score (weighted average)
        weights = {
            'regime': 0.20,
            'adx': 0.20,
            'rsi': 0.15,
            'macd': 0.15,
            'volume': 0.15,
            'volatility': 0.15
        }
        
        overall_score = sum(scores.get(k, 0) * v for k, v in weights.items())
        
        # Decision logic based on composite score
        valid = False
        threshold = 0.50  # Lowered from 0.60 to accommodate current market conditions (bearish regime)
        
        if overall_score >= threshold:
            valid = True
            reasons.append(f"✓ SIGNAL CONFIRMED (Score: {overall_score:.2f}/1.0)")
        else:
            reasons.append(f"✗ SIGNAL REJECTED (Score: {overall_score:.2f}/1.0 < {threshold})")
        
        return {
            'valid': valid,
            'overall_score': overall_score,
            'regime': regime,
            'scores': scores,
            'reasons': reasons,
            'bar_idx': bar_idx,
            'timestamp': row.name if hasattr(row, 'name') else None
        }
    
    def get_position_recommendations(self, bar_idx: int, current_position: Optional[Dict] = None) -> Dict:
        """
        Get trading recommendations based on current conditions
        
        Args:
            bar_idx: Current bar index
            current_position: Current position info (entry price, shares, etc.)
            
        Returns:
            Recommendations dict
        """
        regime = self.detect_regime(bar_idx)
        row = self.df.iloc[bar_idx]
        
        recommendations = {
            'regime': regime,
            'long_setup': self.validate_entry_signal(bar_idx, 'LONG'),
            'short_setup': self.validate_entry_signal(bar_idx, 'SHORT'),
        }
        
        # Exit recommendations if in position
        if current_position:
            entry_price = current_position.get('entry_price')
            current_price = row['close']
            
            if current_position.get('side') == 'LONG':
                # Check for exit signals
                exit_triggers = []
                
                # Exit 1: MACD bearish divergence
                if row['macd'] < row['macd_signal'] and row['macd_hist'] < 0:
                    exit_triggers.append("MACD bearish (line below signal)")
                
                # Exit 2: Price breaks below recent MA
                if current_price < row['ma50']:
                    exit_triggers.append("Price below 50-day MA")
                
                # Exit 3: RSI extreme overbought with divergence
                if row['rsi'] > 70 and row['macd_hist'] < 0:
                    exit_triggers.append("Overbought (RSI>70) with negative MACD divergence")
                
                recommendations['exit_triggers'] = exit_triggers
                recommendations['should_exit'] = len(exit_triggers) > 0
            
            elif current_position.get('side') == 'SHORT':
                exit_triggers = []
                
                # Exit 1: MACD bullish
                if row['macd'] > row['macd_signal'] and row['macd_hist'] > 0:
                    exit_triggers.append("MACD bullish (line above signal)")
                
                # Exit 2: Price breaks above recent MA
                if current_price > row['ma50']:
                    exit_triggers.append("Price above 50-day MA")
                
                # Exit 3: RSI extreme oversold with divergence
                if row['rsi'] < 30 and row['macd_hist'] > 0:
                    exit_triggers.append("Oversold (RSI<30) with positive MACD divergence")
                
                recommendations['exit_triggers'] = exit_triggers
                recommendations['should_exit'] = len(exit_triggers) > 0
        
        return recommendations
    
    def get_strategy_mode(self, bar_idx: int) -> Dict:
        """
        Determine appropriate strategy mode based on regime
        
        Returns:
            Strategy mode recommendations
        """
        regime = self.detect_regime(bar_idx)
        
        mode = {
            'regime': regime,
            'trading_mode': 'UNKNOWN',
            'strategy_emphasis': None,
            'position_sizing': 1.0,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.05,
        }
        
        # Map regime to strategy mode
        if regime in [MarketRegime.STRONG_UPTREND, MarketRegime.UPTREND]:
            mode['trading_mode'] = 'TREND_LONG'
            mode['strategy_emphasis'] = 'Trend-following (aggressive)'
            mode['position_sizing'] = 1.0
            mode['take_profit_pct'] = 0.07  # Higher targets in strong trends
            mode['stop_loss_pct'] = 0.025
        
        elif regime == MarketRegime.MILD_UPTREND:
            mode['trading_mode'] = 'MILD_LONG'
            mode['strategy_emphasis'] = 'Conservative longs / Mean-reversion'
            mode['position_sizing'] = 0.7
            mode['take_profit_pct'] = 0.04
            mode['stop_loss_pct'] = 0.02
        
        elif regime == MarketRegime.SIDEWAYS:
            mode['trading_mode'] = 'RANGE'
            mode['strategy_emphasis'] = 'Mean-reversion (tight targets)'
            mode['position_sizing'] = 0.5
            mode['take_profit_pct'] = 0.02  # Tight targets in ranges
            mode['stop_loss_pct'] = 0.015
        
        elif regime == MarketRegime.MILD_DOWNTREND:
            mode['trading_mode'] = 'MILD_SHORT'
            mode['strategy_emphasis'] = 'Conservative shorts / Stay out'
            mode['position_sizing'] = 0.5
            mode['take_profit_pct'] = 0.03
            mode['stop_loss_pct'] = 0.02
        
        elif regime in [MarketRegime.DOWNTREND, MarketRegime.STRONG_DOWNTREND]:
            mode['trading_mode'] = 'TREND_SHORT'
            mode['strategy_emphasis'] = 'Trend-following shorts (if enabled)'
            mode['position_sizing'] = 0.5  # Reduce if shorts not available
            mode['take_profit_pct'] = 0.05
            mode['stop_loss_pct'] = 0.025
        
        return mode


def create_validation_report(df: pd.DataFrame, validation_result: Dict) -> str:
    """Create a readable validation report"""
    report = f"""
╔══════════════════════════════════════════════════════════════╗
║          ENHANCED SIGNAL VALIDATION REPORT                   ║
╚══════════════════════════════════════════════════════════════╝

Timestamp:           {validation_result.get('timestamp', 'N/A')}
Regime:              {validation_result['regime'].value}
Overall Score:       {validation_result['overall_score']:.2f}/1.00
Valid Signal:        {'✓ YES' if validation_result['valid'] else '✗ NO'}

═══ COMPONENT SCORES ═══
"""
    
    for component, score in validation_result['scores'].items():
        score_pct = score * 100
        bar_length = int(score * 20)
        report += f"\n{component.upper():<15} {score_pct:>5.0f}% {'█' * bar_length}"
    
    report += f"""

═══ VALIDATION REASONS ═══
"""
    for reason in validation_result['reasons']:
        report += f"\n  • {reason}"
    
    report += "\n\n"
    return report
