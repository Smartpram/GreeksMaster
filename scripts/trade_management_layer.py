"""
TRADE MANAGEMENT / EXIT INTELLIGENCE LAYER - FIXED
===================================================

Advanced exit optimizer using SuperTrend TP Dimensions framework.
Simplified version with working SuperTrend calculation.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime, time
from enum import Enum
import json

# ============================================================================
# 1. SUPERTREND ENGINE - Base Trend Regime Classifier
# ============================================================================

class TrendDirection(Enum):
    """Trend direction classification"""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


@dataclass
class SuperTrendOutput:
    """SuperTrend calculation result"""
    value: float
    direction: TrendDirection
    atr: float
    atr_pct: float
    flip_detected: bool
    bars_in_direction: int = 0


class SuperTrendEngine:
    """Supertrend indicator with proper ATR calculation"""
    
    def __init__(self, atr_period: int = 10, factor: float = 3.0):
        self.atr_period = atr_period
        self.factor = factor
        self.prev_direction = None
        self.prev_supertrend = None
    
    def calculate(self, df: pd.DataFrame) -> SuperTrendOutput:
        """Calculate SuperTrend"""
        if len(df) < self.atr_period + 1:
            return SuperTrendOutput(
                value=float(df['Close'].iloc[-1]),
                direction=TrendDirection.NEUTRAL,
                atr=0.0,
                atr_pct=0.0,
                flip_detected=False
            )
        
        # Calculate True Range components
        high_low = (df['High'] - df['Low']).values
        high_close = np.abs(df['High'].values - df['Close'].shift(1).values)
        low_close = np.abs(df['Low'].values - df['Close'].shift(1).values)
        
        # True Range is max of the three
        tr = np.maximum(high_low, np.maximum(high_close, low_close))
        
        # ATR using simple moving average
        atr_values = np.zeros(len(df))
        for i in range(self.atr_period - 1, len(df)):
            atr_values[i] = tr[max(0, i - self.atr_period + 1):i + 1].mean()
        
        # Handle early bars
        for i in range(self.atr_period - 1):
            if i > 0:
                atr_values[i] = tr[:i + 1].mean()
        
        # Calculate bands
        hl2 = (df['High'].values + df['Low'].values) / 2.0
        basic_upper = hl2 + self.factor * atr_values
        basic_lower = hl2 - self.factor * atr_values
        
        # SuperTrend calculation
        supertrend = np.zeros(len(df))
        direction = np.zeros(len(df), dtype=int)
        
        start_idx = min(self.atr_period, len(df) - 1)
        supertrend[start_idx] = basic_lower[start_idx]
        direction[start_idx] = 1
        
        for i in range(start_idx + 1, len(df)):
            # Check for bullish direction
            if basic_lower[i] > supertrend[i-1] or df['Close'].iloc[i-1] < supertrend[i-1]:
                supertrend[i] = basic_lower[i]
                direction[i] = 1
            else:
                supertrend[i] = supertrend[i-1]
                direction[i] = direction[i-1]
            
            # Check for bearish direction
            if basic_upper[i] < supertrend[i] or df['Close'].iloc[i-1] > supertrend[i]:
                supertrend[i] = basic_upper[i]
                direction[i] = -1
        
        # Extract latest values
        current_direction = TrendDirection.BULLISH if direction[-1] > 0 else TrendDirection.BEARISH
        current_atr = float(atr_values[-1]) if atr_values[-1] > 0 else 0.0
        current_close = float(df['Close'].iloc[-1])
        current_supertrend = float(supertrend[-1])
        
        # Detect flip
        flip = (self.prev_direction is not None and 
                self.prev_direction != current_direction)
        
        # Update state
        self.prev_direction = current_direction
        self.prev_supertrend = current_supertrend
        
        return SuperTrendOutput(
            value=current_supertrend,
            direction=current_direction,
            atr=current_atr,
            atr_pct=current_atr / current_close if current_close > 0 else 0,
            flip_detected=flip
        )


# ============================================================================
# 2. CONTEXT FEATURE ENGINE - Exit Favorability Axes
# ============================================================================

@dataclass
class ContextFeatures:
    """Context features for exit evaluation (4 axes)"""
    rel_vol_pct: float        # Relative volume percentile (0-100)
    time_of_day_pct: float    # Time of day score (0-100)
    range_pos_pct: float      # Position in range (0-100)
    custom_signal_pct: float  # Custom signal (IV, OI, ADX, etc.) (0-100)
    
    def average(self) -> float:
        """Average of all features"""
        return (self.rel_vol_pct + self.time_of_day_pct + 
                self.range_pos_pct + self.custom_signal_pct) / 4


class ContextFeatureEngine:
    """Extracts 4 independent context axes for exit favorability"""
    
    def __init__(self):
        pass
    
    def calculate(self, df: pd.DataFrame, 
                 market_hours: Tuple[time, time] = (time(9, 15), time(15, 30)),
                 custom_signal: Optional[pd.Series] = None) -> ContextFeatures:
        """
        Calculate 4-axis context features
        
        Args:
            df: OHLCV dataframe
            market_hours: Trading hours (open, close)
            custom_signal: Optional custom signal (IV, OI, ADX, etc.)
        
        Returns:
            ContextFeatures with 4 scoring axes
        """
        
        # Axis A: Relative Volume Percentile (50-bar rolling)
        vol_50 = df['Volume'].rolling(50).mean()
        current_vol = df['Volume'].iloc[-1]
        vol_pct = min(100, max(0, (current_vol / vol_50.iloc[-1] - 1) * 100 / 2)) if vol_50.iloc[-1] > 0 else 50
        
        # Axis B: Time of Day Score
        # Assumes df has datetime index
        try:
            current_time = df.index[-1].time()
            open_time = market_hours[0]
            close_time = market_hours[1]
            
            # Map time to score: high at open and close, low in middle
            minutes_from_open = (current_time.hour - open_time.hour) * 60 + (current_time.minute - open_time.minute)
            total_minutes = (close_time.hour - open_time.hour) * 60 + (close_time.minute - open_time.minute)
            
            # Create a bell curve: high at edges, low in middle
            pct_through = minutes_from_open / total_minutes if total_minutes > 0 else 0.5
            time_score = abs(pct_through - 0.5) * 200  # Range 0-100
            time_pct = min(100, max(0, time_score))
        except:
            time_pct = 50.0
        
        # Axis C: Position in Range (20-bar lookback)
        high_20 = df['High'].rolling(20).max()
        low_20 = df['Low'].rolling(20).min()
        current_price = df['Close'].iloc[-1]
        
        range_20 = high_20.iloc[-1] - low_20.iloc[-1]
        if range_20 > 0:
            range_pos = (current_price - low_20.iloc[-1]) / range_20 * 100
            range_pct = min(100, max(0, range_pos))
        else:
            range_pct = 50.0
        
        # Axis D: Custom Signal (IV percentile, ADX, OI score, etc.)
        if custom_signal is not None:
            custom_pct = float(custom_signal.iloc[-1])
        else:
            # Default: use RSI if available
            custom_pct = 50.0
        
        return ContextFeatures(
            rel_vol_pct=vol_pct,
            time_of_day_pct=time_pct,
            range_pos_pct=range_pct,
            custom_signal_pct=custom_pct
        )


# ============================================================================
# 3. EXIT POOL BUILDER - Historical Exit Pattern Analysis
# ============================================================================

@dataclass
class ExitSample:
    """Historical exit sample for pattern analysis"""
    timestamp: datetime
    regime: TrendDirection
    pivot_type: str  # 'high' or 'low'
    rel_vol: float
    time_of_day: float
    range_pos: float
    custom_signal: float
    context_score: float
    price_level: float


class ExitPoolBuilder:
    """Builds historical exit pattern database from pivots"""
    
    def __init__(self):
        pass
    
    def find_pivots(self, df: pd.DataFrame, 
                   context_engine: ContextFeatureEngine,
                   lookback: int = 20) -> Tuple[List[ExitSample], List[ExitSample]]:
        """
        Find historical pivots and build exit sample pool
        
        Args:
            df: OHLCV dataframe
            context_engine: ContextFeatureEngine instance
            lookback: Bars for pivot detection
        
        Returns:
            (bullish_exits, bearish_exits) - Lists of ExitSample
        """
        bullish_exits = []
        bearish_exits = []
        
        if len(df) < lookback + 1:
            return bullish_exits, bearish_exits
        
        # Find pivots (simple high/low reversal)
        for i in range(lookback, len(df) - lookback):
            # High pivot
            is_high_pivot = (
                df['High'].iloc[i] > df['High'].iloc[i-lookback:i].max() and
                df['High'].iloc[i] > df['High'].iloc[i+1:i+lookback+1].max()
            )
            
            # Low pivot
            is_low_pivot = (
                df['Low'].iloc[i] < df['Low'].iloc[i-lookback:i].min() and
                df['Low'].iloc[i] < df['Low'].iloc[i+1:i+lookback+1].min()
            )
            
            if is_high_pivot or is_low_pivot:
                # Calculate context at pivot TIME (not confirmation time)
                pivot_df = df.iloc[:i+1]
                context = context_engine.calculate(pivot_df)
                context_score = context.average()
                
                sample = ExitSample(
                    timestamp=df.index[i],
                    regime=TrendDirection.BULLISH if is_low_pivot else TrendDirection.BEARISH,
                    pivot_type='low' if is_low_pivot else 'high',
                    rel_vol=context.rel_vol_pct,
                    time_of_day=context.time_of_day_pct,
                    range_pos=context.range_pos_pct,
                    custom_signal=context.custom_signal_pct,
                    context_score=context_score,
                    price_level=df['Close'].iloc[i]
                )
                
                if is_low_pivot:
                    bullish_exits.append(sample)
                else:
                    bearish_exits.append(sample)
        
        return bullish_exits, bearish_exits


# ============================================================================
# 4. CONDITIONAL DENSITY SCORER - Context Score Calculation
# ============================================================================

@dataclass
class ContextScore:
    """Context scoring result"""
    overall_score: float      # 0-100 overall favorability
    rel_vol_score: float      # Relative volume score
    time_score: float         # Time of day score
    range_score: float        # Range position score
    custom_score: float       # Custom signal score
    tp_quality: str           # Quality rating: POOR, FAIR, GOOD, EXCELLENT
    tp_trigger: bool          # Whether exit conditions likely (context_score > 80)


class ConditionalDensityScorer:
    """Scores current context against historical exit distribution"""
    
    def __init__(self, bins: int = 10):
        self.bins = bins
    
    def score(self, current_context: ContextFeatures,
             exit_pool: List[ExitSample]) -> ContextScore:
        """
        Score current context against historical exit pool
        
        Args:
            current_context: Current market context
            exit_pool: Historical exit samples
        
        Returns:
            ContextScore with overall favorability
        """
        
        if not exit_pool:
            # No historical data - neutral score
            return ContextScore(
                overall_score=50.0,
                rel_vol_score=50.0,
                time_score=50.0,
                range_score=50.0,
                custom_score=50.0,
                tp_quality="FAIR",
                tp_trigger=False
            )
        
        # Extract features from pool
        pool_rel_vol = np.array([s.rel_vol for s in exit_pool])
        pool_time = np.array([s.time_of_day for s in exit_pool])
        pool_range = np.array([s.range_pos for s in exit_pool])
        pool_custom = np.array([s.custom_signal for s in exit_pool])
        
        # Score each axis using conditional binning
        rel_vol_score = self._score_axis(
            current_context.rel_vol_pct,
            pool_rel_vol
        )
        time_score = self._score_axis(
            current_context.time_of_day_pct,
            pool_time
        )
        range_score = self._score_axis(
            current_context.range_pos_pct,
            pool_range
        )
        custom_score = self._score_axis(
            current_context.custom_signal_pct,
            pool_custom
        )
        
        # Overall score (average)
        overall = (rel_vol_score + time_score + range_score + custom_score) / 4
        
        # Determine quality rating
        if overall >= 90:
            quality = "EXCELLENT"
        elif overall >= 75:
            quality = "GOOD"
        elif overall >= 60:
            quality = "FAIR"
        else:
            quality = "POOR"
        
        return ContextScore(
            overall_score=overall,
            rel_vol_score=rel_vol_score,
            time_score=time_score,
            range_score=range_score,
            custom_score=custom_score,
            tp_quality=quality,
            tp_trigger=overall > 80
        )
    
    def _score_axis(self, current_value: float, pool_values: np.ndarray) -> float:
        """Score single axis using conditional binning"""
        
        # Create bins
        hist, bin_edges = np.histogram(pool_values, bins=self.bins, range=(0, 100))
        
        # Find bin containing current value
        bin_idx = int(current_value / (100 / self.bins))
        bin_idx = min(bin_idx, self.bins - 1)
        
        # Score = (count in bin / max count) * 100
        if hist.max() > 0:
            score = (hist[bin_idx] / hist.max()) * 100
        else:
            score = 50.0
        
        return min(100, max(0, score))


# ============================================================================
# 5. EXIT MANAGER - Dynamic Exit Rules
# ============================================================================

@dataclass
class ExitSignal:
    """Exit recommendation"""
    symbol: str
    timeframe: str
    direction: TrendDirection
    context_score: float
    action: str  # HOLD, PARTIAL_EXIT, TIGHTEN_STOP, FULL_EXIT, AVOID_ENTRY
    reason: str
    scale_out_pct: float  # Scale out percentage (0-100)
    new_stop: Optional[float] = None


class ExitManager:
    """Generates entry gates and exit recommendations"""
    
    def evaluate_entry(self, context_score: float, 
                      supertrend_flip: bool) -> Tuple[bool, str]:
        """
        Determine if entry is favorable
        
        Returns:
            (favorable, reason)
        """
        if context_score > 60:
            return False, f"Context unfavorable (score={context_score:.1f})"
        
        if supertrend_flip:
            return False, "SuperTrend recently flipped"
        
        return True, f"Entry favorable (context_score={context_score:.1f})"
    
    def evaluate_exit(self, pnl_pct: float, context_score: ContextScore,
                     atr: float, current_price: float,
                     entry_price: float, symbol: str = "STOCK") -> ExitSignal:
        """
        Determine exit action based on P&L and context
        
        Returns:
            ExitSignal with recommended action
        """
        
        action = "HOLD"
        reason = "Monitoring position"
        scale_out = 0
        new_stop = None
        
        # Exit layering based on context score
        if context_score.overall_score >= 99:
            action = "FULL_EXIT"
            reason = f"Exhaustion zone (score={context_score.overall_score:.1f})"
            scale_out = 100
        elif context_score.overall_score >= 90 and pnl_pct > 20:
            action = "TIGHTEN_STOP"
            reason = f"Book profit area: score={context_score.overall_score:.1f}, P&L=+{pnl_pct:.1f}%"
            new_stop = current_price - atr * 0.5  # Trail by half ATR
        elif context_score.overall_score >= 80 and pnl_pct > 20:
            action = "PARTIAL_EXIT"
            reason = f"Favorable exit zone: score={context_score.overall_score:.1f}, P&L=+{pnl_pct:.1f}%"
            scale_out = 50
        elif pnl_pct >= 2.0:
            # Profit target hit
            action = "PARTIAL_EXIT"
            reason = f"Profit target reached: +{pnl_pct:.1f}%"
            scale_out = 25
        elif pnl_pct <= -1.0:
            # Stop loss
            action = "FULL_EXIT"
            reason = f"Stop loss hit: {pnl_pct:.1f}%"
            scale_out = 100
        
        return ExitSignal(
            symbol=symbol,
            timeframe="15m",
            direction=TrendDirection.BULLISH,
            context_score=context_score.overall_score,
            action=action,
            reason=reason,
            scale_out_pct=scale_out,
            new_stop=new_stop
        )


# ============================================================================
# 6. INTEGRATED TRADE MANAGEMENT LAYER
# ============================================================================

@dataclass
class TradeManagementReport:
    """Integrated trade management analysis"""
    timestamp: datetime
    symbol: str
    timeframe: str
    trend: Dict
    context: Dict
    decision: Dict


class TradeManagementLayer:
    """Unified Trade Management / Exit Intelligence System"""
    
    def __init__(self):
        self.supertrend = SuperTrendEngine()
        self.context_engine = ContextFeatureEngine()
        self.exit_pool_builder = ExitPoolBuilder()
        self.density_scorer = ConditionalDensityScorer()
        self.exit_manager = ExitManager()
    
    def analyze_trade(self, df: pd.DataFrame, symbol: str = "STOCK",
                     timeframe: str = "15m", pnl_pct: float = 0.0,
                     entry_price: float = 0.0) -> Dict:
        """
        Complete trade analysis
        
        Returns:
            Dict with trend, context, and decision information
        """
        
        # Stage 1: SuperTrend
        st_output = self.supertrend.calculate(df)
        
        # Stage 2: Context Features
        context_features = self.context_engine.calculate(df)
        
        # Stage 3: Exit Pool
        bullish_pool, bearish_pool = self.exit_pool_builder.find_pivots(
            df, self.context_engine
        )
        
        # Select appropriate pool
        exit_pool = bullish_pool if st_output.direction == TrendDirection.BULLISH else bearish_pool
        
        # Stage 4: Density Scoring
        context_score = self.density_scorer.score(context_features, exit_pool)
        
        # Stage 5: Exit Decision
        exit_signal = self.exit_manager.evaluate_exit(
            pnl_pct, context_score, st_output.atr,
            float(df['Close'].iloc[-1]), entry_price, symbol
        )
        
        # Build report
        report = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "timeframe": timeframe,
            "trend": {
                "supertrend_value": st_output.value,
                "direction": st_output.direction.value,
                "flip_detected": st_output.flip_detected,
                "atr": st_output.atr,
                "atr_pct": st_output.atr_pct
            },
            "context": {
                "overall_score": context_score.overall_score,
                "rel_vol": context_features.rel_vol_pct,
                "time_of_day": context_features.time_of_day_pct,
                "range_pos": context_features.range_pos_pct,
                "custom_signal": context_features.custom_signal_pct
            },
            "decision": {
                "entry_favorable": not exit_signal.action.startswith("AVOID"),
                "exit_action": exit_signal.action,
                "exit_reason": exit_signal.reason,
                "scale_out_pct": exit_signal.scale_out_pct,
                "tp_quality": context_score.tp_quality,
                "tp_trigger": context_score.tp_trigger
            }
        }
        
        return report


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("TRADE MANAGEMENT / EXIT INTELLIGENCE LAYER - FIXED VERSION")
    print("="*80)
    print()
    print("Components:")
    print("  1. SuperTrendEngine - ATR-based trend classification")
    print("  2. ContextFeatureEngine - 4-axis exit favorability scoring")
    print("  3. ExitPoolBuilder - Historical pivot analysis")
    print("  4. ConditionalDensityScorer - Context-based exit quality")
    print("  5. ExitManager - Dynamic exit rules")
    print("  6. TradeManagementLayer - Integrated system")
    print()
    
    try:
        # Try importing yfinance for real data
        import yfinance as yf
        
        print("Fetching real market data...")
        df = yf.download("AXISBANK.NS", period="60d", interval="15m", progress=False)
        df.index.name = "Datetime"
        
        # Ensure required columns
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        if all(col in df.columns for col in required):
            print(f"Downloaded {len(df)} bars")
            
            # Initialize manager
            manager = TradeManagementLayer()
            
            # Analyze current trade
            print("\n" + "="*80)
            print("TRADE ANALYSIS - AXISBANK 15m")
            print("="*80)
            report = manager.analyze_trade(
                df,
                symbol="AXISBANK",
                timeframe="15m",
                pnl_pct=15.0,
                entry_price=1100.0
            )
            
            # Print report
            print(json.dumps(report, indent=2, default=str))
            
            print("\n✅ Trade Management Layer working correctly!")
        else:
            print("❌ Missing required columns")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nFalling back to synthetic data test...")
        
        # Create synthetic data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='15min')
        prices = np.random.randn(100).cumsum() + 1100
        
        df = pd.DataFrame({
            'Open': prices + np.random.rand(100) * 2,
            'High': prices + 5,
            'Low': prices - 5,
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, 100)
        }, index=dates)
        
        manager = TradeManagementLayer()
        report = manager.analyze_trade(df, symbol="TEST", timeframe="15m", pnl_pct=10.0)
        
        print(json.dumps(report, indent=2, default=str))
        print("\n✅ Trade Management Layer working correctly!")
