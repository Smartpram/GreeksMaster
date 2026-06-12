"""
Market Sentiment Gate - Stage 2 Risk Guardrail
===============================================

This module implements market-level sentiment analysis to gate trade entries.
Evaluates whether broader market conditions support new long positions before execution.

Architecture: Stage 2 (Validation & Risk) pre-entry filter
Integration: Production Validator → Sentiment Evaluator → Risk Manager
             ↓
          Range Policy Enforcer (Capital Preservation in RANGE regime)

Range Policy Integration:
- Detects RANGE (sideways/low-volatility) markets
- Default: NO TRADES during RANGE (capital preservation)
- Rationale: System optimized for trends, not ranges
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class SentimentState(Enum):
    """Market sentiment classification"""
    BULLISH = "Bullish"      # Risk-on, trend-up
    NEUTRAL = "Neutral"      # Mixed/sideways
    BEARISH = "Bearish"      # Risk-off, trend-down


class SentimentAction(Enum):
    """Decision action from sentiment evaluator"""
    ALLOW = "ALLOW"          # Execute trade normally
    CAUTION = "CAUTION"      # Execute with reduced size/risk
    BLOCK = "BLOCK"          # Do not execute, defer trade


@dataclass
class SentimentDecision:
    """Output from market sentiment evaluation"""
    state: SentimentState
    action: SentimentAction
    confidence: float  # 0.0-1.0, how confident in decision
    rationale: str     # Human-readable explanation
    
    # Metrics used in decision
    index_trend: float
    index_volatility: float
    sector_strength: float
    market_breadth: float
    
    def __repr__(self):
        return f"SentimentDecision(state={self.state.value}, action={self.action.value}, confidence={self.confidence:.2f})"


class MarketSentimentEvaluator:
    """
    Evaluates market-level sentiment using available price data
    Inputs: Index prices, sector data, stock data
    Output: ALLOW/CAUTION/BLOCK decision for trade entries
    
    Integration: Includes Range Policy check before sentiment evaluation
    """
    
    def __init__(self, 
                 index_ma_short: int = 20,
                 index_ma_long: int = 200,
                 volatility_threshold: float = 0.03,
                 check_range_policy: bool = True):
        """
        Initialize sentiment evaluator
        
        Args:
            index_ma_short: Short MA period for index trend (default 20 days)
            index_ma_long: Long MA period for index trend (default 200 days)
            volatility_threshold: ATR volatility threshold for "high" volatility
            check_range_policy: If True, check Range Policy before sentiment eval
        """
        self.index_ma_short = index_ma_short
        self.index_ma_long = index_ma_long
        self.volatility_threshold = volatility_threshold
        self.check_range_policy = check_range_policy
        
        # Lazy import Range Policy to avoid circular deps
        self._range_evaluator = None
    
    def assess_market(self, 
                      market_data: pd.DataFrame,
                      current_date: str,
                      stock_sector: str = None) -> SentimentDecision:
        """
        Evaluate current market sentiment state
        
        Integration Points:
        1. Check Range Policy first (capital preservation in RANGE regime)
        2. If not in RANGE, evaluate sentiment normally
        
        Args:
            market_data: DataFrame with 'date', 'open', 'high', 'low', 'close'
                        (typically index or aggregate stock data)
            current_date: Current date as string (YYYY-MM-DD)
            stock_sector: Optional sector for sector-specific bias check
            
        Returns:
            SentimentDecision with state, action, and rationale
        """
        try:
            # Check Range Policy first (Stage 2 Pre-Filter)
            if self.check_range_policy:
                range_decision = self._check_range_policy(market_data, current_date)
                if range_decision is not None:
                    return range_decision
            
            # Get data up to current date
            market_data['date'] = pd.to_datetime(market_data['date'])
            df = market_data[market_data['date'] <= pd.to_datetime(current_date)].copy()
            
            if len(df) < self.index_ma_long:
                logger.debug(f"Insufficient data ({len(df)} days < {self.index_ma_long} required)")
                # Default to NEUTRAL if not enough data
                return SentimentDecision(
                    state=SentimentState.NEUTRAL,
                    action=SentimentAction.ALLOW,
                    confidence=0.5,
                    rationale="Insufficient data for sentiment analysis",
                    index_trend=0.0,
                    index_volatility=0.0,
                    sector_strength=0.0,
                    market_breadth=0.0
                )
            
            # Calculate market sentiment metrics
            index_trend = self._calculate_trend(df)
            index_volatility = self._calculate_volatility(df)
            sector_strength = self._estimate_sector_strength(df, stock_sector)
            market_breadth = self._calculate_market_breadth(df)
            
            # Determine sentiment state
            state = self._determine_sentiment_state(
                index_trend, index_volatility, sector_strength, market_breadth
            )
            
            # Determine action based on state
            action, confidence = self._determine_action(
                state, index_trend, index_volatility, market_breadth
            )
            
            # Generate rationale
            rationale = self._generate_rationale(
                state, action, index_trend, index_volatility, sector_strength
            )
            
            decision = SentimentDecision(
                state=state,
                action=action,
                confidence=confidence,
                rationale=rationale,
                index_trend=index_trend,
                index_volatility=index_volatility,
                sector_strength=sector_strength,
                market_breadth=market_breadth
            )
            
            logger.debug(f"Market sentiment: {decision}")
            return decision
            
        except Exception as e:
            logger.warning(f"Error in sentiment assessment: {e}. Defaulting to NEUTRAL.")
            return SentimentDecision(
                state=SentimentState.NEUTRAL,
                action=SentimentAction.ALLOW,
                confidence=0.3,
                rationale=f"Error in assessment: {str(e)}",
                index_trend=0.0,
                index_volatility=0.0,
                sector_strength=0.0,
                market_breadth=0.0
            )
    
    def _calculate_trend(self, df: pd.DataFrame) -> float:
        """
        Calculate market trend strength (-1.0 to +1.0)
        
        +1.0 = Strong uptrend
         0.0 = Neutral
        -1.0 = Strong downtrend
        """
        if len(df) < self.index_ma_long:
            return 0.0
        
        close = df['close'].values
        ma_short = df['close'].rolling(self.index_ma_short).mean().iloc[-1]
        ma_long = df['close'].rolling(self.index_ma_long).mean().iloc[-1]
        current = close[-1]
        
        # Trend score: (price - long_ma) / long_ma
        trend_score = (current - ma_long) / ma_long if ma_long > 0 else 0
        
        # Bonus if short MA also above long MA
        if ma_short > ma_long:
            trend_score *= 1.2
        elif ma_short < ma_long:
            trend_score *= 0.8
        
        # Clamp to [-1, 1]
        trend_score = max(-1.0, min(1.0, trend_score))
        
        return trend_score
    
    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """
        Calculate market volatility (0.0 to 1.0)
        
        Uses Average True Range (ATR) as proxy for volatility
        0.0 = Low volatility (calm market)
        1.0 = High volatility (turbulent market)
        """
        if len(df) < 14:
            return 0.5
        
        # Calculate ATR
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        atr = df['tr'].rolling(14).mean().iloc[-1]
        atr_pct = atr / df['close'].iloc[-1] if df['close'].iloc[-1] > 0 else 0
        
        # Normalize volatility: threshold = 3% daily range
        volatility_normalized = min(1.0, atr_pct / self.volatility_threshold)
        
        return volatility_normalized
    
    def _estimate_sector_strength(self, df: pd.DataFrame, sector: str = None) -> float:
        """
        Estimate sector-specific strength
        
        Returns: 0.0 (weak) to 1.0 (strong)
        
        Note: This uses overall market as proxy since sector data may not be available
        A full implementation would fetch actual sector indices
        """
        if sector is None:
            return 0.5  # Neutral if no sector specified
        
        # Placeholder: In production, fetch actual sector index
        # For now, use overall market momentum as proxy
        momentum = (df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5]
        
        # 0.5 (neutral) to 1.0 (strong) mapping
        sector_strength = 0.5 + (momentum * 0.5)
        sector_strength = max(0.0, min(1.0, sector_strength))
        
        return sector_strength
    
    def _calculate_market_breadth(self, df: pd.DataFrame) -> float:
        """
        Calculate market breadth (advance/decline ratio)
        
        Returns: 0.0 (declining) to 1.0 (advancing)
        
        Uses price momentum of recent days as proxy for breadth
        """
        if len(df) < 5:
            return 0.5
        
        # Count days where close > open (bullish days)
        bullish_days = (df['close'] > df['open']).tail(5).sum()
        total_days = 5
        
        breadth = bullish_days / total_days
        
        return breadth
    
    def _determine_sentiment_state(self, trend: float, volatility: float, 
                                   sector_strength: float, breadth: float) -> SentimentState:
        """Determine overall sentiment state from metrics"""
        
        # Composite sentiment score
        # Weight: trend (40%), volatility (25%), sector (20%), breadth (15%)
        composite = (trend * 0.4) + (sector_strength * 0.2) - (volatility * 0.25) + (breadth * 0.15)
        
        # Classification thresholds
        if composite > 0.2:
            return SentimentState.BULLISH
        elif composite < -0.2:
            return SentimentState.BEARISH
        else:
            return SentimentState.NEUTRAL
    
    def _determine_action(self, state: SentimentState, trend: float, 
                         volatility: float, breadth: float) -> Tuple[SentimentAction, float]:
        """
        Determine action (ALLOW/CAUTION/BLOCK) and confidence
        
        Returns: (action, confidence_score)
        """
        
        if state == SentimentState.BULLISH:
            # Bullish: allow trades
            confidence = 0.5 + abs(trend) * 0.5  # Higher trend = more confident
            return SentimentAction.ALLOW, min(1.0, confidence)
        
        elif state == SentimentState.BEARISH:
            # Bearish: block trades
            # Unlesslow volatility suggests stabilizing (CAUTION instead)
            if volatility < 0.3:  # Low volatility despite downtrend = potential reversal
                confidence = 0.6
                return SentimentAction.CAUTION, confidence
            else:  # High volatility downtrend = definite block
                confidence = 0.8
                return SentimentAction.BLOCK, confidence
        
        else:  # NEUTRAL
            # Neutral markets: allow but with caution if high volatility
            if volatility > 0.6:  # High volatility in neutral = risky
                return SentimentAction.CAUTION, 0.6
            else:
                return SentimentAction.ALLOW, 0.5
    
    def _generate_rationale(self, state: SentimentState, action: SentimentAction,
                           trend: float, volatility: float, sector_strength: float) -> str:
        """Generate human-readable rationale for decision"""
        
        trend_desc = "uptrend" if trend > 0 else "downtrend" if trend < 0 else "neutral trend"
        vol_desc = "high" if volatility > 0.6 else "moderate" if volatility > 0.3 else "low"
        sector_desc = "strong" if sector_strength > 0.6 else "weak" if sector_strength < 0.4 else "mixed"
        
        action_desc = {
            SentimentAction.ALLOW: "✓ Market conditions favorable",
            SentimentAction.CAUTION: "⚠ Market conditions mixed, proceed with caution",
            SentimentAction.BLOCK: "✗ Market conditions unfavorable"
        }[action]
        
        rationale = (
            f"{action_desc}. "
            f"Index in {trend_desc} ({trend:+.2f}), "
            f"{vol_desc} volatility ({volatility:.2f}), "
            f"sector {sector_desc} ({sector_strength:.2f})"
        )
        
        return rationale
    
    def apply_position_size_adjustment(self, base_size: float, 
                                       decision: SentimentDecision) -> float:
        """
        Apply sentiment-based position sizing
        
        Args:
            base_size: Normal position size
            decision: Sentiment decision
            
        Returns:
            Adjusted position size
        """
        if decision.action == SentimentAction.ALLOW:
            return base_size  # Full size
        elif decision.action == SentimentAction.CAUTION:
            return base_size * 0.5  # Half size
        else:  # BLOCK
            return 0.0  # No position
    
    def apply_risk_adjustment(self, base_stop_loss: float, 
                            decision: SentimentDecision) -> float:
        """
        Apply sentiment-based risk adjustments (stop-loss)
        
        Args:
            base_stop_loss: Normal stop-loss percentage
            decision: Sentiment decision
            
        Returns:
            Adjusted stop-loss percentage (tighter = more conservative)
        """
        if decision.action == SentimentAction.ALLOW:
            return base_stop_loss  # Normal
        elif decision.action == SentimentAction.CAUTION:
            return base_stop_loss * 1.5  # Tighter stop-loss (1.5x more strict)
        else:  # BLOCK
            return 0.0  # N/A - trade blocked
    
    def _check_range_policy(self, market_data: pd.DataFrame, 
                           current_date: str) -> Optional[SentimentDecision]:
        """
        Stage 2 Pre-Filter: Check Range Policy
        
        If market is in RANGE regime, enforce capital preservation
        (do not allow trades unless range strategy is proven)
        
        Returns:
            SentimentDecision blocking trades, or None if not in RANGE
        """
        try:
            from app.range_policy import RangeDetector, RangePolicyEvaluator
            
            # Get data up to current date
            market_data['date'] = pd.to_datetime(market_data['date'])
            df = market_data[market_data['date'] <= pd.to_datetime(current_date)].copy()
            
            if len(df) < 20:
                return None  # Not enough data
            
            # Detect range
            detector = RangeDetector()
            context = detector.detect_range(df)
            
            # If in RANGE with persistence, block trades
            if context.is_range and context.persistence_bars >= 5:
                logger.warning(
                    f"🔄 RANGE POLICY TRIGGERED: "
                    f"Market in RANGE regime ({context.persistence_bars} bars, "
                    f"confidence={context.confidence:.2f}). "
                    f"Blocking new trades for capital preservation."
                )
                
                return SentimentDecision(
                    state=SentimentState.NEUTRAL,
                    action=SentimentAction.BLOCK,
                    confidence=min(1.0, context.confidence + 0.2),
                    rationale=(
                        f"✗ RANGE POLICY: Market in {context.detection_method.value} regime. "
                        f"No proven range strategy. "
                        f"Preserving capital. Resume when trend detected. "
                        f"[Confidence={context.confidence:.2f}, Bars={context.persistence_bars}]"
                    ),
                    index_trend=0.0,
                    index_volatility=context.volatility,
                    sector_strength=0.5,
                    market_breadth=0.5,
                )
            
            # Not in RANGE or early detection - sentiment eval proceeds
            return None
        
        except Exception as e:
            logger.debug(f"Range policy check failed (continuing with sentiment eval): {e}")
            return None


# Singleton instance
_sentiment_evaluator = None


def get_sentiment_evaluator() -> MarketSentimentEvaluator:
    """Get or create singleton sentiment evaluator"""
    global _sentiment_evaluator
    if _sentiment_evaluator is None:
        _sentiment_evaluator = MarketSentimentEvaluator()
    return _sentiment_evaluator


if __name__ == "__main__":
    # Example usage
    evaluator = MarketSentimentEvaluator()
    
    # Create sample market data
    dates = pd.date_range(start='2024-01-01', periods=250, freq='D')
    prices = 100 + np.cumsum(np.random.randn(250) * 1.5)
    market_data = pd.DataFrame({
        'date': dates,
        'open': prices - np.random.rand(250),
        'high': prices + np.random.rand(250),
        'low': prices - np.random.rand(250) * 2,
        'close': prices
    })
    
    # Assess sentiment for a recent date
    decision = evaluator.assess_market(market_data, '2024-09-08')
    print(f"\nSentiment Decision: {decision}")
    print(f"Rationale: {decision.rationale}")
    print(f"\nPosition size adjustment (base 100): {evaluator.apply_position_size_adjustment(100, decision):.0f}")
    print(f"Stop-loss adjustment (base 2%): {evaluator.apply_risk_adjustment(2.0, decision):.2f}%")
