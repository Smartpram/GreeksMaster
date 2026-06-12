"""
RANGE POLICY ENFORCEMENT
========================

Implements capital preservation strategy when market enters RANGE/SIDEWAYS regime.

Policy Summary:
- RANGE detected = NON-TRENDING market, system optimized for trends
- Default (Option A): NO TRADES during RANGE
  - Preserve capital
  - Block all trend signals
  - Resume when trend detected
- Alternate (Option B): Range strategy (IF implemented)
  - Mean reversion signals only
  - Tight stops, small profits
  - Reduced position size

Integration Points:
- Stage 1 (SCREENER): Switch signal generation (trend OFF / range ON)
- Stage 2 (VALIDATION): Validate only active strategy
- Stage 4 (POSITION MANAGEMENT): Enforce tighter exits, smaller size

Safeguards:
- Small positions (e.g., 25-50% of normal)
- Tight stops (e.g., 2-3% instead of 3-4%)
- Detect breakout → switch to trend
- Avoid rapid regime switching (require N persistence bars)

Key Principle:
"Trade only with edge. Else stand down."
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class RangePolicy(Enum):
    """Range trading policy options"""
    NO_TRADE = "no_trade"          # Option A: Default - capital preservation
    RANGE_STRATEGY = "range_strategy"  # Option B: If range strategy implemented


class RangeDetectionMethod(Enum):
    """Methods to detect RANGE regime"""
    BOLLINGER_BANDS = "bollinger_bands"    # Price trapped within bands
    ATR_LOW = "atr_low"                    # Low volatility / narrow ATR
    ADX_LOW = "adx_low"                    # Low trend strength (ADX < 25)
    PRICE_ACTION = "price_action"          # Support/resistance bounces


@dataclass
class RangeContext:
    """Context about current RANGE market"""
    is_range: bool              # True if in RANGE regime
    confidence: float           # 0.0-1.0, confidence in RANGE detection
    volatility: float           # Current ATR/close (0.0-1.0)
    atr: float                  # Actual ATR value
    upper_bound: float          # Estimated resistance
    lower_bound: float          # Estimated support
    persistence_bars: int       # Bars in current RANGE
    detection_method: RangeDetectionMethod
    
    def __repr__(self):
        return (
            f"RangeContext(is_range={self.is_range}, "
            f"confidence={self.confidence:.2f}, "
            f"atr={self.atr:.4f}, "
            f"bounds=[{self.lower_bound:.2f},{self.upper_bound:.2f}], "
            f"bars={self.persistence_bars})"
        )


@dataclass
class RangePolicyDecision:
    """Decision output from Range Policy evaluator"""
    should_trade: bool          # True if should proceed with trade
    policy: RangePolicy         # Active policy (NO_TRADE or RANGE_STRATEGY)
    position_size_factor: float # Adjust position: 1.0 (full) to 0.0 (none)
    stop_loss_tightness: float  # Adjust stops: 1.0 (normal) to 0.5 (tight)
    rationale: str              # Explanation
    
    def __repr__(self):
        return (
            f"RangePolicyDecision(should_trade={self.should_trade}, "
            f"policy={self.policy.value}, "
            f"size={self.position_size_factor:.2f}, "
            f"stops={self.stop_loss_tightness:.2f})"
        )


class RangeDetector:
    """
    Detects RANGE/SIDEWAYS market conditions
    """
    
    def __init__(self,
                 atr_period: int = 14,
                 bb_period: int = 20,
                 bb_std: float = 2.0,
                 adx_period: int = 14,
                 persistence_threshold: int = 5):
        """
        Initialize range detector
        
        Args:
            atr_period: ATR calculation period
            bb_period: Bollinger Bands period
            bb_std: Bollinger Bands std dev
            adx_period: ADX calculation period
            persistence_threshold: Bars to confirm RANGE persistence
        """
        self.atr_period = atr_period
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.adx_period = adx_period
        self.persistence_threshold = persistence_threshold
        
        # State tracking
        self.range_persistence_count = 0
        self.last_range_context = None
    
    def detect_range(self, df: pd.DataFrame) -> RangeContext:
        """
        Detect if market is in RANGE regime
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            RangeContext with detection details
        """
        
        if len(df) < max(self.bb_period, self.atr_period, self.adx_period):
            logger.debug("Insufficient data for range detection")
            return RangeContext(
                is_range=False,
                confidence=0.0,
                volatility=0.5,
                atr=0.0,
                upper_bound=df['close'].iloc[-1] * 1.02,
                lower_bound=df['close'].iloc[-1] * 0.98,
                persistence_bars=0,
                detection_method=RangeDetectionMethod.PRICE_ACTION,
            )
        
        current_price = df['close'].iloc[-1]
        
        # Method 1: ATR-based low volatility detection
        atr, atr_pct = self._calculate_atr(df)
        is_low_volatility = atr_pct < 0.015  # < 1.5% daily range
        
        # Method 2: Bollinger Bands detection
        bb_upper, bb_lower, bb_width = self._calculate_bollinger_bands(df)
        bb_squeeze = bb_width < atr_pct * 1.5  # Bands squeezed
        
        # Method 3: ADX detection
        adx = self._calculate_adx(df)
        weak_trend = adx < 25  # ADX < 25 = weak/no trend
        
        # Composite detection
        range_score = 0.0
        if is_low_volatility:
            range_score += 0.4
        if bb_squeeze:
            range_score += 0.3
        if weak_trend:
            range_score += 0.3
        
        is_range = range_score >= 0.6
        
        # Track persistence
        if is_range:
            self.range_persistence_count += 1
        else:
            self.range_persistence_count = 0
        
        # Determine primary detection method
        if weak_trend:
            method = RangeDetectionMethod.ADX_LOW
        elif is_low_volatility:
            method = RangeDetectionMethod.ATR_LOW
        elif bb_squeeze:
            method = RangeDetectionMethod.BOLLINGER_BANDS
        else:
            method = RangeDetectionMethod.PRICE_ACTION
        
        context = RangeContext(
            is_range=is_range,
            confidence=range_score,
            volatility=atr_pct,
            atr=atr,
            upper_bound=bb_upper,
            lower_bound=bb_lower,
            persistence_bars=self.range_persistence_count,
            detection_method=method,
        )
        
        self.last_range_context = context
        return context
    
    def _calculate_atr(self, df: pd.DataFrame) -> Tuple[float, float]:
        """
        Calculate ATR (Average True Range)
        
        Returns:
            (atr_value, atr_percent)
        """
        df = df.copy()
        
        # True Range
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        
        # ATR
        atr = df['tr'].rolling(self.atr_period).mean().iloc[-1]
        atr_pct = atr / df['close'].iloc[-1] if df['close'].iloc[-1] > 0 else 0.01
        
        return atr, atr_pct
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame) -> Tuple[float, float, float]:
        """
        Calculate Bollinger Bands width
        
        Returns:
            (upper_band, lower_band, width)
        """
        sma = df['close'].rolling(self.bb_period).mean()
        std = df['close'].rolling(self.bb_period).std()
        
        upper = sma + (std * self.bb_std)
        lower = sma - (std * self.bb_std)
        
        upper_val = upper.iloc[-1]
        lower_val = lower.iloc[-1]
        width = upper_val - lower_val
        
        return upper_val, lower_val, width
    
    def _calculate_adx(self, df: pd.DataFrame) -> float:
        """
        Calculate ADX (Average Directional Index)
        
        Returns:
            ADX value (0-100)
        """
        df = df.copy()
        
        # DM (Directional Movement)
        up_move = df['high'].diff()
        down_move = -df['low'].diff()
        
        pos_dm = np.where(
            (up_move > down_move) & (up_move > 0), up_move, 0
        )
        neg_dm = np.where(
            (down_move > up_move) & (down_move > 0), down_move, 0
        )
        
        # TR (True Range)
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        
        # DI (Directional Index)
        tr_sum = df['tr'].rolling(self.adx_period).sum()
        plus_di = 100 * (pd.Series(pos_dm).rolling(self.adx_period).sum() / tr_sum)
        minus_di = 100 * (pd.Series(neg_dm).rolling(self.adx_period).sum() / tr_sum)
        
        # DX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        
        # ADX (EMA of DX)
        adx = dx.rolling(self.adx_period).mean()
        
        return adx.iloc[-1] if len(adx) > 0 else 25.0


class RangePolicyEvaluator:
    """
    Evaluates Range Policy and makes trading decisions
    """
    
    def __init__(self,
                 active_policy: RangePolicy = RangePolicy.NO_TRADE,
                 detector: Optional[RangeDetector] = None,
                 persistence_threshold: int = 5):
        """
        Initialize Range Policy evaluator
        
        Args:
            active_policy: Which policy to use (NO_TRADE or RANGE_STRATEGY)
            detector: RangeDetector instance (will create if None)
            persistence_threshold: Bars to confirm RANGE
        """
        self.active_policy = active_policy
        self.detector = detector or RangeDetector(
            persistence_threshold=persistence_threshold
        )
        self.persistence_threshold = persistence_threshold
    
    def evaluate(self, df: pd.DataFrame, 
                signal_type: str = 'BUY') -> RangePolicyDecision:
        """
        Evaluate if trade should proceed under Range Policy
        
        Args:
            df: DataFrame with price data
            signal_type: 'BUY' or 'SELL'
            
        Returns:
            RangePolicyDecision with trading recommendation
        """
        
        # Detect RANGE
        context = self.detector.detect_range(df)
        
        if not context.is_range:
            # NOT in RANGE - execute normally
            return RangePolicyDecision(
                should_trade=True,
                policy=self.active_policy,
                position_size_factor=1.0,
                stop_loss_tightness=1.0,
                rationale=f"Trending market detected (ADX/volatility normal). Full execution. [Method: {context.detection_method.value}]"
            )
        
        # IN RANGE - apply policy
        if self.active_policy == RangePolicy.NO_TRADE:
            return self._apply_no_trade_policy(context, signal_type)
        else:
            return self._apply_range_strategy_policy(context, signal_type)
    
    def _apply_no_trade_policy(self, context: RangeContext, 
                               signal_type: str) -> RangePolicyDecision:
        """
        Apply Option A: NO TRADE during RANGE
        
        Capital preservation mode
        """
        
        # Require strong persistence to confirm RANGE
        if context.persistence_bars < self.persistence_threshold:
            # Early RANGE detection - still allow trades with caution
            return RangePolicyDecision(
                should_trade=True,
                policy=self.active_policy,
                position_size_factor=0.5,
                stop_loss_tightness=0.8,
                rationale=(
                    f"RANGE detected but not persistent yet "
                    f"({context.persistence_bars}/{self.persistence_threshold} bars). "
                    f"Allowing with REDUCED size. "
                    f"[{context.detection_method.value}, confidence={context.confidence:.2f}]"
                )
            )
        
        # Strong RANGE persistence - block trades
        return RangePolicyDecision(
            should_trade=False,
            policy=self.active_policy,
            position_size_factor=0.0,
            stop_loss_tightness=1.0,
            rationale=(
                f"✗ RANGE confirmed ({context.persistence_bars} bars, "
                f"confidence={context.confidence:.2f}). "
                f"Capital preservation mode: NO TRADES. "
                f"Resume when trend detected. "
                f"[{context.detection_method.value}]"
            )
        )
    
    def _apply_range_strategy_policy(self, context: RangeContext,
                                     signal_type: str) -> RangePolicyDecision:
        """
        Apply Option B: Range strategy (if implemented)
        
        Only if proven range strategy exists
        """
        
        # Current: Range strategy NOT implemented
        # Fallback to NO_TRADE
        logger.warning(
            "Range strategy not yet implemented. "
            "Falling back to NO_TRADE policy (capital preservation)."
        )
        
        return RangePolicyDecision(
            should_trade=False,
            policy=RangePolicy.NO_TRADE,
            position_size_factor=0.0,
            stop_loss_tightness=1.0,
            rationale=(
                f"RANGE strategy not implemented. "
                f"Defaulting to NO_TRADE for capital preservation."
            )
        )
    
    def apply_adjustments(self, base_size: float, base_stop_loss: float,
                         decision: RangePolicyDecision) -> Tuple[float, float]:
        """
        Apply Range Policy adjustments to position size and stops
        
        Args:
            base_size: Normal position size
            base_stop_loss: Normal stop loss (%)
            decision: RangePolicyDecision
            
        Returns:
            (adjusted_size, adjusted_stop_loss)
        """
        
        adjusted_size = base_size * decision.position_size_factor
        
        # Tighter stops = closer to entry (reduce from base)
        adjusted_stop = base_stop_loss * decision.stop_loss_tightness
        
        return adjusted_size, adjusted_stop


# ============================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*70)
    print("RANGE POLICY TEST")
    print("="*70)
    
    # Create test data
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100)
    
    # Scenario 1: Trending market
    print("\n[Scenario 1] Trending Market")
    close_trend = 100 + np.cumsum(np.random.randn(100) * 0.5)
    df_trend = pd.DataFrame({
        'date': dates,
        'open': close_trend + np.random.randn(100) * 0.1,
        'high': close_trend + abs(np.random.randn(100) * 0.2),
        'low': close_trend - abs(np.random.randn(100) * 0.2),
        'close': close_trend,
        'volume': np.random.randint(1000, 10000, 100),
    })
    
    detector = RangeDetector()
    context = detector.detect_range(df_trend)
    print(f"Range Context: {context}")
    
    evaluator = RangePolicyEvaluator()
    decision = evaluator.evaluate(df_trend, 'BUY')
    print(f"Decision: {decision}")
    
    # Scenario 2: Range market (low volatility)
    print("\n[Scenario 2] Range Market (Low Volatility)")
    close_range = np.full(100, 100.0) + np.random.randn(100) * 0.2
    df_range = pd.DataFrame({
        'date': dates,
        'open': close_range + np.random.randn(100) * 0.1,
        'high': close_range + abs(np.random.randn(100) * 0.05),
        'low': close_range - abs(np.random.randn(100) * 0.05),
        'close': close_range,
        'volume': np.random.randint(1000, 10000, 100),
    })
    
    context = detector.detect_range(df_range)
    print(f"Range Context: {context}")
    
    # Simulate persistence
    for _ in range(5):
        context = detector.detect_range(df_range)
    
    decision = evaluator.evaluate(df_range, 'BUY')
    print(f"Decision: {decision}")
    
    # Scenario 3: Apply adjustments
    print("\n[Scenario 3] Position Size & Stop Loss Adjustments")
    base_size = 100
    base_stop = 3.0
    
    adj_size, adj_stop = evaluator.apply_adjustments(base_size, base_stop, decision)
    print(f"Base size: {base_size}, Adjusted: {adj_size}")
    print(f"Base stop: {base_stop}%, Adjusted: {adj_stop}%")
    
    print("\n✅ All Range Policy tests completed!")
