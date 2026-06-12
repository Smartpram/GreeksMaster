"""
Real-Time Feature Engineering Engine
=====================================
Computes comprehensive feature vectors for ML predictions.

Features computed:
- Technical indicators (MA, RSI, MACD, Stochastic)
- Volatility metrics (ATR, Bollinger Bands)
- Volume analysis
- Market structure (higher/lower highs)
- Sentiment indicators
- Options chain data (put/call ratios)

Usage:
    engine = FeatureEngine(data_provider=breeze_api)
    features = engine.compute_all_features('NIFTY50', lookback_bars=100)
    # Returns: Dict with 15+ feature values
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class FeatureVector:
    """Complete feature vector for ML prediction"""
    timestamp: datetime
    symbol: str
    
    # Trend features
    ma_ratio: float  # Close / SMA(20)
    ma_trend: int  # -1, 0, +1 (down, neutral, up)
    ema_slope: float  # EMA(12) slope
    
    # Momentum features
    rsi_14: float  # (0-100)
    rsi_divergence: bool  # Higher low vs price lower low = buy signal
    macd_signal: int  # -1, 0, +1 (bearish, neutral, bullish)
    stoch_rsi: float  # (0-100)
    
    # Volatility features
    atr_14: float  # Average True Range
    atr_ratio: float  # Current ATR / SMA(ATR)
    bb_width: float  # (Upper - Lower) / Close
    bb_position: float  # (Close - Lower) / (Upper - Lower), 0-1
    
    # Volume features
    volume_ratio: float  # Today volume / 20-day avg
    on_balance_volume: float  # OBV momentum
    
    # Market structure
    higher_high: bool  # Price > previous high
    higher_low: bool  # Price > previous low (uptrend confirmation)
    
    # Options chain features (if available)
    put_call_ratio: Optional[float] = None
    implied_volatility: Optional[float] = None
    
    # Aggregated score (for quick decision)
    bullish_score: float = 0.0  # 0-100, composite bullishness


class FeatureEngine:
    """Compute trading features from market data"""
    
    def __init__(self, data_provider, lookback_bars: int = 100):
        """
        Initialize feature engine
        
        Args:
            data_provider: Breeze API or data source
            lookback_bars: Number of historical bars to analyze
        """
        self.data_provider = data_provider
        self.lookback_bars = lookback_bars
        self.cache = {}
        self.last_update = {}
    
    def compute_all_features(self, symbol: str, timeframe: str = "1D") -> FeatureVector:
        """
        Compute complete feature vector for ML prediction
        
        Args:
            symbol: Stock symbol (e.g., 'NIFTY50')
            timeframe: Candle timeframe ('1D', '1H', '15M', etc.)
        
        Returns:
            FeatureVector with all computed features
        """
        try:
            # Get OHLCV data
            df = self.data_provider.get_historical_data(
                symbol, 
                timeframe=timeframe,
                num_candles=self.lookback_bars
            )
            
            if df is None or len(df) < 20:
                logger.warning(f"Insufficient data for {symbol}")
                return None
            
            # Compute all feature groups
            trend_features = self._compute_trend_features(df)
            momentum_features = self._compute_momentum_features(df)
            volatility_features = self._compute_volatility_features(df)
            volume_features = self._compute_volume_features(df)
            structure_features = self._compute_structure_features(df)
            
            # Get latest options data if available
            options_features = self._compute_options_features(symbol)
            
            # Aggregate bullish score
            bullish_score = self._compute_bullish_score({
                **trend_features,
                **momentum_features,
                **volatility_features,
                **volume_features,
                **structure_features,
                **options_features
            })
            
            # Create feature vector
            vector = FeatureVector(
                timestamp=datetime.now(),
                symbol=symbol,
                # Trend
                ma_ratio=trend_features['ma_ratio'],
                ma_trend=trend_features['ma_trend'],
                ema_slope=trend_features['ema_slope'],
                # Momentum
                rsi_14=momentum_features['rsi_14'],
                rsi_divergence=momentum_features['rsi_divergence'],
                macd_signal=momentum_features['macd_signal'],
                stoch_rsi=momentum_features['stoch_rsi'],
                # Volatility
                atr_14=volatility_features['atr_14'],
                atr_ratio=volatility_features['atr_ratio'],
                bb_width=volatility_features['bb_width'],
                bb_position=volatility_features['bb_position'],
                # Volume
                volume_ratio=volume_features['volume_ratio'],
                on_balance_volume=volume_features['on_balance_volume'],
                # Structure
                higher_high=structure_features['higher_high'],
                higher_low=structure_features['higher_low'],
                # Options (optional)
                put_call_ratio=options_features.get('put_call_ratio'),
                implied_volatility=options_features.get('iv'),
                # Score
                bullish_score=bullish_score
            )
            
            logger.debug(f"Features computed for {symbol}: bullish_score={bullish_score:.1f}")
            return vector
            
        except Exception as e:
            logger.error(f"Error computing features for {symbol}: {e}")
            return None
    
    def _compute_trend_features(self, df: pd.DataFrame) -> Dict:
        """Compute trend-based features"""
        close = df['close'].values
        
        # Moving averages
        sma_20 = self._sma(close, 20)
        ema_12 = self._ema(close, 12)
        
        ma_ratio = close[-1] / sma_20[-1] if sma_20[-1] != 0 else 1.0
        
        # MA trend direction
        if sma_20[-1] > sma_20[-2]:
            ma_trend = 1  # Uptrend
        elif sma_20[-1] < sma_20[-2]:
            ma_trend = -1  # Downtrend
        else:
            ma_trend = 0  # Neutral
        
        # EMA slope
        ema_slope = (ema_12[-1] - ema_12[-5]) / ema_12[-5] if len(ema_12) >= 5 else 0.0
        
        return {
            'ma_ratio': float(ma_ratio),
            'ma_trend': int(ma_trend),
            'ema_slope': float(ema_slope),
            'sma_20': float(sma_20[-1]),
            'ema_12': float(ema_12[-1])
        }
    
    def _compute_momentum_features(self, df: pd.DataFrame) -> Dict:
        """Compute momentum-based features"""
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        
        # RSI
        rsi = self._rsi(close, 14)[-1]
        
        # RSI divergence detection
        rsi_divergence = self._detect_divergence(close, rsi)
        
        # MACD
        macd_signal = self._macd_signal(close)
        
        # Stochastic RSI
        stoch_rsi = self._stochastic_rsi(close, 14)
        
        return {
            'rsi_14': float(rsi),
            'rsi_divergence': bool(rsi_divergence),
            'macd_signal': int(macd_signal),  # -1, 0, +1
            'stoch_rsi': float(stoch_rsi)
        }
    
    def _compute_volatility_features(self, df: pd.DataFrame) -> Dict:
        """Compute volatility-based features"""
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        
        # ATR
        atr = self._atr(high, low, close, 14)[-1]
        atr_sma = np.mean([self._atr(high, low, close, 14)[-i] for i in range(1, 6)])
        atr_ratio = atr / atr_sma if atr_sma != 0 else 1.0
        
        # Bollinger Bands
        sma_20 = self._sma(close, 20)
        std_20 = self._std(close, 20)
        
        bb_upper = sma_20[-1] + (2 * std_20[-1])
        bb_lower = sma_20[-1] - (2 * std_20[-1])
        bb_width = (bb_upper - bb_lower) / close[-1] if close[-1] != 0 else 0.0
        bb_position = (close[-1] - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) != 0 else 0.5
        
        return {
            'atr_14': float(atr),
            'atr_ratio': float(atr_ratio),
            'bb_width': float(bb_width),
            'bb_position': float(max(0, min(1, bb_position)))  # Clamp 0-1
        }
    
    def _compute_volume_features(self, df: pd.DataFrame) -> Dict:
        """Compute volume-based features"""
        volume = df['volume'].values
        close = df['close'].values
        
        # Volume ratio
        vol_20_avg = np.mean(volume[-20:])
        volume_ratio = volume[-1] / vol_20_avg if vol_20_avg > 0 else 1.0
        
        # On-Balance Volume
        obv = self._obv(close, volume)
        obv_momentum = (obv[-1] - obv[-5]) / abs(obv[-5]) if obv[-5] != 0 else 0.0
        
        return {
            'volume_ratio': float(volume_ratio),
            'on_balance_volume': float(obv_momentum)
        }
    
    def _compute_structure_features(self, df: pd.DataFrame) -> Dict:
        """Compute market structure features"""
        high = df['high'].values
        low = df['low'].values
        
        # Higher high / Higher low
        higher_high = high[-1] > high[-2]
        higher_low = low[-1] > low[-2]
        
        return {
            'higher_high': bool(higher_high),
            'higher_low': bool(higher_low)
        }
    
    def _compute_options_features(self, symbol: str) -> Dict:
        """Compute options chain features"""
        try:
            # Get options chain data
            options_data = self.data_provider.get_options_chain(symbol)
            if not options_data:
                return {'put_call_ratio': None, 'iv': None}
            
            # Calculate put/call ratio
            put_volume = sum([opt.get('volume', 0) for opt in options_data if opt.get('type') == 'PUT'])
            call_volume = sum([opt.get('volume', 0) for opt in options_data if opt.get('type') == 'CALL'])
            pcr = put_volume / call_volume if call_volume > 0 else 1.0
            
            # Average IV
            iv = np.mean([opt.get('iv', 0) for opt in options_data if opt.get('iv')])
            
            return {
                'put_call_ratio': float(pcr),
                'iv': float(iv)
            }
        except Exception as e:
            logger.debug(f"Could not compute options features: {e}")
            return {'put_call_ratio': None, 'iv': None}
    
    def _compute_bullish_score(self, features: Dict) -> float:
        """
        Compute composite bullishness score (0-100)
        
        Weights based on signal strength:
        - Trend (30%): MA ratio, MA trend
        - Momentum (30%): RSI, MACD, Stochastic
        - Volatility (20%): BB position
        - Volume (10%): Volume ratio
        - Structure (10%): Higher high/low
        """
        score = 0.0
        
        # Trend component (30%)
        ma_ratio_score = min(100, (features.get('ma_ratio', 1.0) - 0.98) * 100)
        ma_trend_score = (features.get('ma_trend', 0) + 1) * 25  # -1→0, 0→25, 1→50
        trend_score = (ma_ratio_score * 0.6 + ma_trend_score * 0.4) * 0.30
        
        # Momentum component (30%)
        rsi = features.get('rsi_14', 50)
        rsi_score = abs(rsi - 50) * 2 if rsi > 50 else max(0, (50 - rsi) * 1.5)
        macd_score = (features.get('macd_signal', 0) + 1) * 33.3
        stoch_score = features.get('stoch_rsi', 50)
        momentum_score = (rsi_score * 0.4 + macd_score * 0.35 + stoch_score * 0.25) * 0.30
        
        # Volatility component (20%) - BB position
        bb_position_score = features.get('bb_position', 0.5) * 100
        volatility_score = bb_position_score * 0.20
        
        # Volume component (10%)
        vol_ratio = min(2.0, features.get('volume_ratio', 1.0))
        volume_score = (vol_ratio - 1.0) * 100 * 0.10
        
        # Structure component (10%)
        struct_score = 0
        if features.get('higher_high'):
            struct_score += 5
        if features.get('higher_low'):
            struct_score += 5
        struct_score = struct_score * 0.10
        
        # Combine components
        score = trend_score + momentum_score + volatility_score + volume_score + struct_score
        
        return max(0, min(100, score))
    
    # ============ INDICATOR CALCULATIONS ============
    
    def _sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """Simple Moving Average"""
        return np.convolve(data, np.ones(period) / period, mode='valid')
    
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Exponential Moving Average"""
        ema = np.zeros(len(data))
        ema[0] = data[0]
        multiplier = 2 / (period + 1)
        for i in range(1, len(data)):
            ema[i] = data[i] * multiplier + ema[i-1] * (1 - multiplier)
        return ema
    
    def _rsi(self, data: np.ndarray, period: int) -> np.ndarray:
        """Relative Strength Index"""
        deltas = np.diff(data)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(data)
        rsi[:period] = 100 - 100 / (1 + rs)
        
        for i in range(period, len(data)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0
            else:
                upval = 0
                downval = -delta
            
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            rs = up / down if down != 0 else 0
            rsi[i] = 100 - 100 / (1 + rs)
        
        return rsi
    
    def _macd_signal(self, data: np.ndarray, fast: int = 12, slow: int = 26) -> int:
        """MACD signal: -1 (bearish), 0 (neutral), 1 (bullish)"""
        ema_fast = self._ema(data, fast)
        ema_slow = self._ema(data, slow)
        macd = ema_fast[-1] - ema_slow[-1] if len(ema_fast) > 0 and len(ema_slow) > 0 else 0
        
        if macd > 0:
            return 1
        elif macd < 0:
            return -1
        else:
            return 0
    
    def _stochastic_rsi(self, data: np.ndarray, period: int = 14) -> float:
        """Stochastic RSI"""
        rsi = self._rsi(data, period)
        if len(rsi) < period:
            return 50.0
        
        rsi_high = np.max(rsi[-period:])
        rsi_low = np.min(rsi[-period:])
        
        if rsi_high == rsi_low:
            return 50.0
        
        stoch = (rsi[-1] - rsi_low) / (rsi_high - rsi_low) * 100
        return float(stoch)
    
    def _atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
        """Average True Range"""
        tr = np.maximum(
            high[1:] - low[1:],
            np.maximum(
                np.abs(high[1:] - close[:-1]),
                np.abs(low[1:] - close[:-1])
            )
        )
        atr = np.zeros(len(high))
        atr[period] = np.mean(tr[:period])
        for i in range(period + 1, len(high)):
            atr[i] = (atr[i-1] * (period - 1) + tr[i-1]) / period
        return atr
    
    def _std(self, data: np.ndarray, period: int) -> np.ndarray:
        """Standard deviation"""
        return np.array([np.std(data[max(0, i-period):i+1]) for i in range(len(data))])
    
    def _obv(self, close: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """On-Balance Volume"""
        obv = np.zeros(len(close))
        obv[0] = volume[0]
        for i in range(1, len(close)):
            if close[i] > close[i-1]:
                obv[i] = obv[i-1] + volume[i]
            elif close[i] < close[i-1]:
                obv[i] = obv[i-1] - volume[i]
            else:
                obv[i] = obv[i-1]
        return obv
    
    def _detect_divergence(self, close: np.ndarray, rsi: float) -> bool:
        """Detect bullish/bearish divergence"""
        if len(close) < 5:
            return False
        
        # Simple: price makes lower low but RSI makes higher low
        price_lower = close[-1] < close[-5]
        # RSI typically higher (> 50 = bullish RSI)
        rsi_higher = rsi > 50
        
        return price_lower and rsi_higher
