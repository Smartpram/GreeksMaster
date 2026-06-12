"""
Options Strategy Selector
=========================

Converts normalized signals (from signal_normalizer.py) into 
candidate options strategies with selection rationale.

Pure logic layer - NO broker dependency yet.
Output: Strategy recommendation events ready for execution engine.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class StrategyType(Enum):
    """Supported options strategies"""
    LONG_CALL = "LONG_CALL"
    LONG_PUT = "LONG_PUT"
    BULL_CALL_SPREAD = "BULL_CALL_SPREAD"
    BEAR_PUT_SPREAD = "BEAR_PUT_SPREAD"
    COVERED_CALL = "COVERED_CALL"
    PROTECTIVE_PUT = "PROTECTIVE_PUT"
    IRON_CONDOR = "IRON_CONDOR"
    CALENDAR_SPREAD = "CALENDAR_SPREAD"
    LONG_STRADDLE = "LONG_STRADDLE"


class ExpiryHorizon(Enum):
    """Expiry selection horizon"""
    WEEKLY = "WEEKLY"        # 0-7 DTE
    MONTHLY = "MONTHLY"      # 8-30 DTE
    QUARTERLY = "QUARTERLY"  # 31-90 DTE


@dataclass
class StrategyLeg:
    """Single leg of an options strategy"""
    position_type: str  # "LONG_CALL", "SHORT_CALL", "LONG_PUT", "SHORT_PUT"
    strike: Optional[float] = None  # Will be determined during chain query
    strike_selection: str = "ATM"   # ATM, ITM, OTM
    expiry_dte: int = 7            # Days to expiry
    quantity: int = 1


@dataclass
class StrategyRecommendation:
    """Recommended options strategy from normalized signal"""
    
    # Identification
    strategy_id: str
    signal_id: str
    symbol: str
    timestamp: str
    
    # Strategy definition
    strategy_type: str  # LONG_CALL, BULL_CALL_SPREAD, etc.
    direction: str      # BULLISH, BEARISH, NEUTRAL
    
    # Selection rationale
    rationale: str      # Why this strategy was chosen
    selection_reason: Dict = None  # Detailed reasoning
    
    # Strategy parameters
    legs: List[StrategyLeg] = None
    expiry_horizon: str = "MONTHLY"
    
    # Risk and capital
    max_risk_per_trade: float = 0.0    # $ or %
    max_premium_outlay: float = 0.0    # $ 
    
    # Entry recommendation
    entry_condition: str = "MARKET_OPEN"  # When to enter
    holding_period_days: int = 5
    
    # Exit rules
    profit_target_pct: float = 50.0   # Exit at 50% profit
    stop_loss_pct: float = 30.0       # Exit at 30% loss
    time_stop_days: int = 3           # Exit after N days if thesis not playing out
    
    # Pre-trade checklist
    pre_trade_checks: Dict = None
    
    # Metadata
    confidence: int = 0
    expected_return_pct: float = 0.0
    metadata: Dict = None


class OptionsStrategySelector:
    """Selects appropriate options strategy based on normalized signal"""
    
    def __init__(self, max_loss_per_trade_pct: float = 2.0):
        """
        Args:
            max_loss_per_trade_pct: Maximum loss as % of account (for risk sizing)
        """
        self.max_loss_pct = max_loss_per_trade_pct
        self.recommendations = []
        self.logger = logger
    
    def select_strategy(self, signal: Dict) -> StrategyRecommendation:
        """
        Convert normalized signal into strategy recommendation
        
        Args:
            signal: NormalizedSignal as dict (from signal_normalizer.py)
        
        Returns:
            StrategyRecommendation with entry/exit rules
        """
        
        symbol = signal['symbol']
        signal_type = signal['signal_type']
        direction = signal['direction']
        confidence = signal['confidence']
        volatility = signal['volatility']
        expected_move_pct = signal['expected_move_pct']
        holding_period = signal['holding_period_days']
        atr = signal['atr']
        spot_price = signal['spot_price']
        
        strategy_id = f"{symbol}_{signal_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        timestamp = datetime.now().isoformat()
        
        # Strategy selection logic (as per your guidance)
        if direction == "BULLISH" and confidence >= 70:
            # Bullish breakout + high confidence
            # Prefer: Bull Call Spread (defined risk, lower cost)
            rec = self._create_bull_call_spread(
                signal, strategy_id, timestamp, confidence, expected_move_pct
            )
        
        elif direction == "BULLISH" and confidence >= 50:
            # Bullish trend + medium confidence
            # Prefer: Long Call (simpler, good for learning)
            rec = self._create_long_call(
                signal, strategy_id, timestamp, confidence, expected_move_pct
            )
        
        elif direction == "BEARISH" and confidence >= 70:
            # Bearish reversal + high confidence
            # Prefer: Bear Put Spread (defined risk, income)
            rec = self._create_bear_put_spread(
                signal, strategy_id, timestamp, confidence, expected_move_pct
            )
        
        elif direction == "BEARISH" and confidence >= 50:
            # Bearish trend + medium confidence
            # Prefer: Long Put
            rec = self._create_long_put(
                signal, strategy_id, timestamp, confidence, expected_move_pct
            )
        
        elif volatility > 0.35 and confidence >= 60:
            # High IV (range-bound) + decent confidence
            # Prefer: Iron Condor (volatility seller)
            # BUT: Only with strong risk controls (later phase)
            rec = self._create_iron_condor_alert(
                signal, strategy_id, timestamp, confidence
            )
        
        else:
            # Neutral/low confidence - wait or skip
            rec = None
        
        if rec:
            self.recommendations.append(rec)
            self.logger.info(
                f"✓ Strategy Selected: {rec.strategy_type} for {symbol} "
                f"({rec.direction}, Conf: {confidence}%)"
            )
        
        return rec
    
    def _create_long_call(
        self,
        signal: Dict,
        strategy_id: str,
        timestamp: str,
        confidence: int,
        expected_move_pct: float
    ) -> StrategyRecommendation:
        """Long Call: Bullish, unlimited upside, defined risk"""
        
        symbol = signal['symbol']
        spot_price = signal['spot_price']
        holding_period = signal['holding_period_days']
        
        # Sizing
        max_premium_outlay = spot_price * 0.05  # 5% of stock price (example)
        
        rec = StrategyRecommendation(
            strategy_id=strategy_id,
            signal_id=signal['signal_id'],
            symbol=symbol,
            timestamp=timestamp,
            strategy_type=StrategyType.LONG_CALL.value,
            direction="BULLISH",
            rationale="Bullish directional signal with moderate-to-high confidence. "
                     "Long Call provides unlimited upside with defined risk (premium paid).",
            selection_reason={
                "signal_type": signal['signal_type'],
                "confidence": confidence,
                "expected_move_pct": expected_move_pct,
                "why_long_call": "Simplest directional play, good for learning engine behavior",
                "risk_profile": "Defined risk (premium) with unlimited upside"
            },
            legs=[
                StrategyLeg(
                    position_type="LONG_CALL",
                    strike_selection="ATM",  # Near stock price
                    expiry_dte=7 if holding_period <= 5 else 14,
                    quantity=1
                )
            ],
            expiry_horizon="WEEKLY" if holding_period <= 5 else "MONTHLY",
            max_risk_per_trade=max_premium_outlay,
            max_premium_outlay=max_premium_outlay,
            holding_period_days=holding_period,
            profit_target_pct=50.0,
            stop_loss_pct=30.0,  # Exit if premium drops 30%
            time_stop_days=holding_period - 1,
            confidence=confidence,
            expected_return_pct=expected_move_pct,
            metadata={"capital_efficiency": "Medium"}
        )
        
        return rec
    
    def _create_long_put(
        self,
        signal: Dict,
        strategy_id: str,
        timestamp: str,
        confidence: int,
        expected_move_pct: float
    ) -> StrategyRecommendation:
        """Long Put: Bearish, unlimited downside profit, defined risk"""
        
        symbol = signal['symbol']
        spot_price = signal['spot_price']
        holding_period = signal['holding_period_days']
        
        # Sizing
        max_premium_outlay = spot_price * 0.05
        
        rec = StrategyRecommendation(
            strategy_id=strategy_id,
            signal_id=signal['signal_id'],
            symbol=symbol,
            timestamp=timestamp,
            strategy_type=StrategyType.LONG_PUT.value,
            direction="BEARISH",
            rationale="Bearish signal with moderate-to-high confidence. "
                     "Long Put for downside profit with defined risk.",
            selection_reason={
                "signal_type": signal['signal_type'],
                "confidence": confidence,
                "expected_move_pct": -expected_move_pct,
                "why_long_put": "Bearish directional play, mirror of long call"
            },
            legs=[
                StrategyLeg(
                    position_type="LONG_PUT",
                    strike_selection="ATM",
                    expiry_dte=7 if holding_period <= 5 else 14,
                    quantity=1
                )
            ],
            expiry_horizon="WEEKLY" if holding_period <= 5 else "MONTHLY",
            max_risk_per_trade=max_premium_outlay,
            max_premium_outlay=max_premium_outlay,
            holding_period_days=holding_period,
            profit_target_pct=50.0,
            stop_loss_pct=30.0,
            time_stop_days=holding_period - 1,
            confidence=confidence,
            expected_return_pct=-expected_move_pct,
            metadata={"capital_efficiency": "Medium"}
        )
        
        return rec
    
    def _create_bull_call_spread(
        self,
        signal: Dict,
        strategy_id: str,
        timestamp: str,
        confidence: int,
        expected_move_pct: float
    ) -> StrategyRecommendation:
        """
        Bull Call Spread: Bullish, defined risk AND profit, lower premium cost
        Better for capital preservation and consistent returns
        """
        
        symbol = signal['symbol']
        spot_price = signal['spot_price']
        holding_period = signal['holding_period_days']
        
        # Sizing: Lower capital than long call
        max_premium_outlay = spot_price * 0.02  # 2% of stock price
        
        rec = StrategyRecommendation(
            strategy_id=strategy_id,
            signal_id=signal['signal_id'],
            symbol=symbol,
            timestamp=timestamp,
            strategy_type=StrategyType.BULL_CALL_SPREAD.value,
            direction="BULLISH",
            rationale="Bullish breakout with high confidence. Bull Call Spread provides "
                     "defined risk AND defined profit with lower premium outlay. "
                     "Excellent for capital preservation.",
            selection_reason={
                "signal_type": signal['signal_type'],
                "confidence": confidence,
                "expected_move_pct": expected_move_pct,
                "why_spread": "Lower cost than naked call, defined risk, better for first automation",
                "risk_profile": "Defined risk = max premium paid, defined profit = width - premium",
                "capital_efficiency": "High - 40-60% return on capital at risk"
            },
            legs=[
                StrategyLeg(
                    position_type="LONG_CALL",
                    strike_selection="ATM",
                    expiry_dte=7 if holding_period <= 5 else 14,
                    quantity=1
                ),
                StrategyLeg(
                    position_type="SHORT_CALL",
                    strike_selection="OTM",  # Strike = ATM + expected move
                    expiry_dte=7 if holding_period <= 5 else 14,
                    quantity=1
                )
            ],
            expiry_horizon="WEEKLY" if holding_period <= 5 else "MONTHLY",
            max_risk_per_trade=max_premium_outlay,
            max_premium_outlay=max_premium_outlay,
            holding_period_days=holding_period,
            profit_target_pct=50.0,  # 50% of max profit
            stop_loss_pct=100.0,     # Can lose entire premium
            time_stop_days=holding_period - 1,
            confidence=confidence,
            expected_return_pct=(expected_move_pct * 0.5),  # Limited upside
            metadata={
                "capital_efficiency": "High",
                "spread_width": "1-2% of spot",
                "break_even": "Long strike + net premium"
            }
        )
        
        return rec
    
    def _create_bear_put_spread(
        self,
        signal: Dict,
        strategy_id: str,
        timestamp: str,
        confidence: int,
        expected_move_pct: float
    ) -> StrategyRecommendation:
        """
        Bear Put Spread: Bearish, defined risk AND profit, income strategy
        Benefits from price staying above lower strike
        """
        
        symbol = signal['symbol']
        spot_price = signal['spot_price']
        holding_period = signal['holding_period_days']
        
        # Sizing
        max_premium_outlay = spot_price * 0.03  # 3% of stock price
        
        rec = StrategyRecommendation(
            strategy_id=strategy_id,
            signal_id=signal['signal_id'],
            symbol=symbol,
            timestamp=timestamp,
            strategy_type=StrategyType.BEAR_PUT_SPREAD.value,
            direction="BEARISH",
            rationale="Bearish signal with high confidence. Bear Put Spread generates "
                     "income while protecting downside. Defined risk & profit.",
            selection_reason={
                "signal_type": signal['signal_type'],
                "confidence": confidence,
                "expected_move_pct": -expected_move_pct,
                "why_spread": "Income on downside expectation with defined risk",
                "risk_profile": "Defined risk = spread width - premium received",
                "capital_efficiency": "High"
            },
            legs=[
                StrategyLeg(
                    position_type="SHORT_PUT",
                    strike_selection="ATM",
                    expiry_dte=7 if holding_period <= 5 else 14,
                    quantity=1
                ),
                StrategyLeg(
                    position_type="LONG_PUT",
                    strike_selection="OTM",
                    expiry_dte=7 if holding_period <= 5 else 14,
                    quantity=1
                )
            ],
            expiry_horizon="WEEKLY" if holding_period <= 5 else "MONTHLY",
            max_risk_per_trade=max_premium_outlay,
            max_premium_outlay=0.0,  # We collect premium (credit spread)
            holding_period_days=holding_period,
            profit_target_pct=50.0,  # 50% of max profit
            stop_loss_pct=100.0,     # Can lose entire spread width
            time_stop_days=holding_period - 1,
            confidence=confidence,
            expected_return_pct=50.0,  # Income return
            metadata={
                "capital_efficiency": "Very High",
                "trade_type": "Credit Spread",
                "margin_requirement": "Spread width (in rupees)"
            }
        )
        
        return rec
    
    def _create_iron_condor_alert(
        self,
        signal: Dict,
        strategy_id: str,
        timestamp: str,
        confidence: int
    ) -> StrategyRecommendation:
        """
        Iron Condor: For range-bound markets, volatility selling
        NOTE: This is flagged for review - only deploy after strong risk controls built
        """
        
        rec = StrategyRecommendation(
            strategy_id=strategy_id,
            signal_id=signal['signal_id'],
            symbol=signal['symbol'],
            timestamp=timestamp,
            strategy_type=StrategyType.IRON_CONDOR.value,
            direction="NEUTRAL",
            rationale="High volatility with range-bound expectation. Iron Condor profits "
                     "from decay. ALERT: Requires strict risk controls before deployment.",
            selection_reason={
                "volatility": signal['volatility'],
                "why_condor": "Range-bound = sell volatility via iron condor",
                "requirement": "STRONG margin, kill-switches, max-loss containment",
                "status": "FLAGGED FOR REVIEW"
            },
            confidence=confidence,
            metadata={
                "deployment_status": "RESEARCH_ONLY",
                "deployment_condition": "After risk controls built",
                "risk_level": "ADVANCED",
                "note": "Do not deploy without kill-switches and margin limits"
            }
        )
        
        return rec
    
    def get_recommendations_by_strategy(self, strategy_type: str) -> List[StrategyRecommendation]:
        """Get all recommendations of given strategy type"""
        return [r for r in self.recommendations if r.strategy_type == strategy_type]
    
    def get_bullish_recommendations(self) -> List[StrategyRecommendation]:
        """Get all bullish strategies"""
        return [r for r in self.recommendations if r.direction == "BULLISH"]
    
    def export_recommendations_json(self, filename: str = None) -> str:
        """Export strategy recommendations to JSON"""
        if filename is None:
            filename = f"strategy_recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'recommendation_count': len(self.recommendations),
            'recommendations': [asdict(r) for r in self.recommendations]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        self.logger.info(f"✓ Exported {len(self.recommendations)} recommendations to {filename}")
        return filename
    
    def print_summary(self):
        """Print recommendations summary"""
        if not self.recommendations:
            print("No strategy recommendations generated")
            return
        
        print("\n" + "="*80)
        print("STRATEGY RECOMMENDATIONS SUMMARY")
        print("="*80)
        print(f"Total Recommendations: {len(self.recommendations)}\n")
        
        # By strategy type
        print("By Strategy Type:")
        for strategy in [StrategyType.LONG_CALL.value, StrategyType.BULL_CALL_SPREAD.value,
                         StrategyType.LONG_PUT.value, StrategyType.BEAR_PUT_SPREAD.value]:
            recs = self.get_recommendations_by_strategy(strategy)
            if recs:
                print(f"  {strategy}: {len(recs)}")
                for rec in recs:
                    print(f"    • {rec.symbol} - Conf: {rec.confidence}%, "
                          f"Hold: {rec.holding_period_days}d, "
                          f"Risk: {rec.max_risk_per_trade:.0f}")
        
        print("\n" + "="*80)


if __name__ == "__main__":
    # Example: Convert normalized signals to strategy recommendations
    normalizer_signal_example = {
        'signal_id': 'AXIS_BREAKOUT_20260609',
        'symbol': 'AXIS',
        'signal_type': 'BREAKOUT',
        'direction': 'BULLISH',
        'confidence': 70,
        'spot_price': 1292.40,
        'holding_period_days': 5,
        'volatility': 0.20,
        'atr': 24.54,
        'expected_move_pct': 1.9,
    }
    
    selector = OptionsStrategySelector()
    rec = selector.select_strategy(normalizer_signal_example)
    
    print("\n" + "="*80)
    print("EXAMPLE: STRATEGY RECOMMENDATION (Ready for Execution Engine)")
    print("="*80)
    if rec:
        print(json.dumps(asdict(rec), indent=2, default=str))
    
    selector.print_summary()
