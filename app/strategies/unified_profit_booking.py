"""
UNIFIED PROFIT BOOKING STRATEGY
With embedded design rules forbidding trailing stops in mean-reverting regimes

Implementation of design decision: TRAILING_STOPS_DESIGN_RULES.md
Date: June 1, 2026
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classification"""
    MEAN_REVERTING = "mean_reverting"  # Choppy, quick reversals, intraday
    TRENDING = "trending"               # Multi-day, sustained moves
    UNKNOWN = "unknown"                 # Insufficient data


class ExitStrategy(Enum):
    """Exit strategy types (Updated: Trailing now conditional)"""
    FIXED_FULL_EXIT = "fixed_full_exit"              # Always active
    PARTIAL_WITH_TRAILING = "partial_with_trailing"  # Conditional on regime


@dataclass
class TrailingStopConditions:
    """Conditions that determine if trailing stops are allowed"""
    post_target_extension: bool      # Are targets reversal points or mid-move?
    pure_intraday_moves: bool        # avg_holding_days < 1.0?
    high_post_target_volatility: bool # volatility spike post-target?
    
    @property
    def trailing_allowed(self) -> bool:
        """Trailing is allowed ONLY if NO condition forbids it"""
        # All conditions must be FALSE (not present) to allow trailing
        return not (
            self.post_target_extension or 
            self.pure_intraday_moves or 
            self.high_post_target_volatility
        )
    
    @property
    def disallow_reason(self) -> str:
        """Human-readable reason for disallowing trailing"""
        reasons = []
        if self.post_target_extension:
            reasons.append("Target is reversal point, no extension follows")
        if self.pure_intraday_moves:
            reasons.append("Pure intraday moves (avg_holding_days < 1.0)")
        if self.high_post_target_volatility:
            reasons.append("High post-target volatility (drawdown ratio > 3.0)")
        
        return " + ".join(reasons) if reasons else "Unknown"


class UnifiedProfitBookingManager:
    """
    Unified profit booking strategy with conditional trailing stops.
    
    Design Rules:
    1. Fixed Full Exit is ALWAYS available
    2. Trailing stops are CONDITIONAL on market regime and conditions
    3. In mean-reverting intraday moves: Use FIXED_FULL_EXIT (no trailing)
    4. In trending multi-day moves: Use PARTIAL_WITH_TRAILING (if conditions permit)
    """
    
    def __init__(self):
        self.config = {
            'target_pct': 0.065,              # 6.5% profit target
            'stop_loss_pct': 0.04,            # 4.0% stop loss
            'trailing_stop_pct': 0.02,        # 2.0% trailing (if enabled)
            'partial_exit_ratio': 0.50,       # Exit 50% at target (if trailing used)
        }
        
        self.positions = {}
        self.exit_history = []
        
        # Regime detection
        self.market_regime = MarketRegime.UNKNOWN
        self.recent_trades = []  # For regime analysis
        
        logger.info("✅ Unified Profit Booking Manager initialized")
    
    # ========== MARKET REGIME DETECTION ==========
    
    def detect_market_regime(self, recent_trades: list) -> MarketRegime:
        """
        Detect market regime from recent trade history.
        
        Heuristics:
        - avg_holding_days > 2.0 → TRENDING
        - avg_holding_days < 1.0 → MEAN_REVERTING
        """
        if not recent_trades:
            return MarketRegime.UNKNOWN
        
        holding_days = [t.get('holding_days', 0) for t in recent_trades]
        avg_holding = sum(holding_days) / len(holding_days) if holding_days else 0
        
        if avg_holding > 2.0:
            regime = MarketRegime.TRENDING
        elif avg_holding < 1.0:
            regime = MarketRegime.MEAN_REVERTING
        else:
            regime = MarketRegime.UNKNOWN
        
        self.market_regime = regime
        logger.info(f"📊 Market regime detected: {regime.value} (avg_holding={avg_holding:.2f}d)")
        return regime
    
    # ========== TRAILING STOP CONDITIONS ASSESSMENT ==========
    
    def assess_trailing_conditions(self, recent_trades: list) -> TrailingStopConditions:
        """
        Assess whether trailing stops should be allowed based on market conditions.
        
        Returns TrailingStopConditions with flags for each disallow rule.
        """
        
        # Condition 1: Post-Target Extension
        # Check if target is final exit point (no significant extension beyond)
        post_target_extension = self._check_no_extension_beyond_target(recent_trades)
        
        # Condition 2: Pure Intraday Moves
        # Check if avg_holding_days < 1.0
        pure_intraday = self._check_pure_intraday(recent_trades)
        
        # Condition 3: High Post-Target Volatility
        # Check if drawdown spikes after target (volatility increases)
        high_volatility = self._check_high_post_target_volatility(recent_trades)
        
        conditions = TrailingStopConditions(
            post_target_extension=post_target_extension,
            pure_intraday_moves=pure_intraday,
            high_post_target_volatility=high_volatility,
        )
        
        logger.info(
            f"🔍 Trailing Stop Conditions Assessment:\n"
            f"   No Extension Beyond Target: {post_target_extension}\n"
            f"   Pure Intraday Moves: {pure_intraday}\n"
            f"   High Post-Target Volatility: {high_volatility}\n"
            f"   → Trailing Allowed: {conditions.trailing_allowed}"
        )
        
        return conditions
    
    def _check_no_extension_beyond_target(self, recent_trades: list) -> bool:
        """
        Check if targets are reversal points (no new winners with trailing).
        Rule: If win_count is same between fixed and trailing, extension doesn't exist.
        """
        # This would be populated from backtest comparison data
        # For now: assume NO extension if we have evidence from recent trades
        
        if not recent_trades:
            return True  # Conservative: assume no extension
        
        # Check if any trade moved significantly beyond typical target distance
        target_distance = self.config['target_pct']
        extension_count = 0
        
        for trade in recent_trades:
            max_profit = trade.get('max_profit_pct', 0)
            # If max profit was >> target, there was extension
            if max_profit > target_distance * 1.5:  # 50% more than target
                extension_count += 1
        
        # If < 20% of trades show extension, no post-target extension exists
        has_no_extension = (extension_count / len(recent_trades)) < 0.2
        return has_no_extension
    
    def _check_pure_intraday(self, recent_trades: list) -> bool:
        """
        Check if trades are pure intraday (avg_holding_days < 1.0).
        """
        if not recent_trades:
            return True  # Conservative: assume pure intraday
        
        holding_days = [t.get('holding_days', 0) for t in recent_trades]
        avg_holding = sum(holding_days) / len(holding_days)
        
        is_pure_intraday = avg_holding < 1.0
        return is_pure_intraday
    
    def _check_high_post_target_volatility(self, recent_trades: list) -> bool:
        """
        Check if drawdown spikes after target (high post-target volatility).
        Rule: If max_drawdown_ratio > 3.0, volatility is too high.
        """
        if not recent_trades:
            return False  # Not enough data
        
        # This requires comparison of fixed vs trailing results
        # For now: use backtest-derived knowledge
        # From backtest: ratio = 528% / 77.9% ≈ 6.8 > 3.0 threshold
        
        max_drawdown_avg = sum([abs(t.get('max_drawdown', 0)) for t in recent_trades]) / len(recent_trades)
        
        # In mean-reverting markets, typical max_drawdown is 50-100%
        # If we see > 200%, volatility is abnormally high
        has_high_volatility = max_drawdown_avg > 200
        
        return has_high_volatility
    
    # ========== STRATEGY SELECTION (CONDITIONAL) ==========
    
    def select_exit_strategy(self) -> ExitStrategy:
        """
        Select exit strategy based on market regime and conditions.
        
        Algorithm:
        1. If regime is MEAN_REVERTING: Use FIXED_FULL_EXIT (no exceptions)
        2. If regime is TRENDING: Assess trailing conditions, allow if all pass
        3. Otherwise: Default to FIXED_FULL_EXIT
        """
        
        # Default to fixed
        selected = ExitStrategy.FIXED_FULL_EXIT
        reason = "Default safe strategy"
        
        if self.market_regime == MarketRegime.MEAN_REVERTING:
            selected = ExitStrategy.FIXED_FULL_EXIT
            reason = "Mean-reverting regime forbids trailing"
        
        elif self.market_regime == MarketRegime.TRENDING:
            # Check if trailing is allowed
            conditions = self.assess_trailing_conditions(self.recent_trades)
            if conditions.trailing_allowed:
                selected = ExitStrategy.PARTIAL_WITH_TRAILING
                reason = "Trending regime + favorable conditions allow trailing"
            else:
                selected = ExitStrategy.FIXED_FULL_EXIT
                reason = f"Trailing disallowed: {conditions.disallow_reason}"
        
        logger.info(f"🎯 Strategy Selected: {selected.value} ({reason})")
        return selected
    
    # ========== POSITION MANAGEMENT ==========
    
    def create_position(
        self,
        symbol: str,
        entry_price: float,
        quantity: int,
        position_id: str,
        auto_select_strategy: bool = True,
    ) -> Dict:
        """
        Create a new position with automatically selected exit strategy.
        
        Args:
            auto_select_strategy: If True, use unified selection logic
                                 If False, use market regime default
        """
        
        if auto_select_strategy:
            strategy = self.select_exit_strategy()
        else:
            # Fallback to regime default
            strategy = (
                ExitStrategy.FIXED_FULL_EXIT 
                if self.market_regime == MarketRegime.MEAN_REVERTING 
                else ExitStrategy.FIXED_FULL_EXIT
            )
        
        # Calculate exit levels
        target = entry_price * (1 + self.config['target_pct'])
        stop_loss = entry_price * (1 - self.config['stop_loss_pct'])
        trailing_stop = None  # Set when price moves
        
        position = {
            'position_id': position_id,
            'symbol': symbol,
            'entry_price': entry_price,
            'quantity': quantity,
            'entry_time': datetime.now(),
            'exit_strategy': strategy,
            'target': target,
            'stop_loss': stop_loss,
            'trailing_stop': trailing_stop,
            'highest_price': entry_price,
            'max_profit_pct': 0,
            'is_partial_exited': False,
            'remaining_qty': quantity,
        }
        
        self.positions[position_id] = position
        
        strategy_name = strategy.value.replace('_', ' ').title()
        logger.info(
            f"📍 Position created: {symbol} | Entry: ₹{entry_price:.2f} | "
            f"Target: ₹{target:.2f} | SL: ₹{stop_loss:.2f} | "
            f"Strategy: {strategy_name}"
        )
        
        return position
    
    def check_exit_conditions(
        self,
        position_id: str,
        current_price: float,
    ) -> Tuple[bool, Optional[str], Dict]:
        """
        Check if position should exit based on selected strategy.
        
        Returns:
            (should_exit, exit_reason, exit_details)
        """
        
        if position_id not in self.positions:
            return False, None, {}
        
        pos = self.positions[position_id]
        strategy = pos['exit_strategy']
        
        # Update highest price for max profit calculation
        if current_price > pos['highest_price']:
            pos['highest_price'] = current_price
            pos['max_profit_pct'] = ((current_price - pos['entry_price']) / pos['entry_price']) * 100
        
        # Check exit conditions based on strategy
        if strategy == ExitStrategy.FIXED_FULL_EXIT:
            should_exit, reason, details = self._check_fixed_full_exit(pos, current_price)
        
        elif strategy == ExitStrategy.PARTIAL_WITH_TRAILING:
            should_exit, reason, details = self._check_partial_trailing(pos, current_price)
        
        else:
            should_exit, reason, details = False, None, {}
        
        return should_exit, reason, details
    
    def _check_fixed_full_exit(self, pos: Dict, current_price: float) -> Tuple[bool, Optional[str], Dict]:
        """Check fixed full exit strategy"""
        
        # Check stop loss
        if current_price <= pos['stop_loss']:
            return True, "stop_loss_hit", {
                'exit_price': current_price,
                'exit_qty': pos['remaining_qty'],
            }
        
        # Check target
        if current_price >= pos['target']:
            return True, "target_hit", {
                'exit_price': current_price,
                'exit_qty': pos['remaining_qty'],
            }
        
        return False, None, {}
    
    def _check_partial_trailing(self, pos: Dict, current_price: float) -> Tuple[bool, Optional[str], Dict]:
        """Check partial + trailing strategy"""
        
        # First check: Stop loss always exits ALL
        if current_price <= pos['stop_loss']:
            return True, "stop_loss_hit", {
                'exit_price': current_price,
                'exit_qty': pos['remaining_qty'],
            }
        
        # Second check: Target hit on fresh position
        if not pos['is_partial_exited'] and current_price >= pos['target']:
            partial_qty = int(pos['quantity'] * self.config['partial_exit_ratio'])
            pos['is_partial_exited'] = True
            pos['remaining_qty'] = pos['quantity'] - partial_qty
            
            # Set trailing stop on remaining
            pos['trailing_stop'] = current_price * (1 - self.config['trailing_stop_pct'])
            
            return True, "target_hit", {
                'exit_price': current_price,
                'exit_qty': partial_qty,
            }
        
        # Third check: Trailing stop on second half
        if pos['is_partial_exited'] and pos['trailing_stop']:
            if current_price <= pos['trailing_stop']:
                return True, "trailing_stop_hit", {
                    'exit_price': current_price,
                    'exit_qty': pos['remaining_qty'],
                }
            
            # Update trailing stop if price moves higher
            new_trailing = current_price * (1 - self.config['trailing_stop_pct'])
            if new_trailing > pos['trailing_stop']:
                pos['trailing_stop'] = new_trailing
        
        return False, None, {}
    
    def execute_exit(self, position_id: str, exit_price: float, exit_qty: int) -> Dict:
        """Execute exit and record trade"""
        
        if position_id not in self.positions:
            return {}
        
        pos = self.positions[position_id]
        
        # Calculate P&L
        pnl = (exit_price - pos['entry_price']) * exit_qty
        pnl_pct = ((exit_price - pos['entry_price']) / pos['entry_price']) * 100
        
        # Record exit
        exit_record = {
            'position_id': position_id,
            'symbol': pos['symbol'],
            'entry_price': pos['entry_price'],
            'exit_price': exit_price,
            'exit_qty': exit_qty,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'max_profit_pct': pos['max_profit_pct'],
            'strategy': pos['exit_strategy'].value,
            'entry_time': pos['entry_time'],
            'exit_time': datetime.now(),
        }
        
        self.exit_history.append(exit_record)
        
        logger.info(
            f"✅ Exit executed: {pos['symbol']} | Exit: ₹{exit_price:.2f} | "
            f"Qty: {exit_qty} | P&L: {pnl_pct:.2f}% | Strategy: {pos['exit_strategy'].value}"
        )
        
        return exit_record
    
    # ========== STATISTICS & REPORTING ==========
    
    def get_strategy_stats(self) -> Dict:
        """Get comprehensive statistics"""
        
        if not self.exit_history:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'total_pnl': 0,
                'avg_pnl_pct': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'market_regime': self.market_regime.value,
            }
        
        import pandas as pd
        import numpy as np
        
        df = pd.DataFrame(self.exit_history)
        
        wins = df[df['pnl'] > 0]
        losses = df[df['pnl'] <= 0]
        
        total_wins = wins['pnl'].sum() if not wins.empty else 0
        total_losses = abs(losses['pnl'].sum()) if not losses.empty else 1
        
        total_trades = len(df)
        winning_trades = len(wins)
        losing_trades = len(losses)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        total_pnl = df['pnl'].sum()
        avg_pnl_pct = df['pnl_pct'].mean()
        
        # Sharpe ratio
        returns = df['pnl_pct'].values / 100
        sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
        
        # Max drawdown
        cumulative_pnl = df['pnl'].cumsum()
        running_max = cumulative_pnl.cummax()
        drawdown_amounts = (cumulative_pnl - running_max)
        max_cumsum = cumulative_pnl.max() if cumulative_pnl.max() > 0 else 1
        max_drawdown = (drawdown_amounts.min() / max_cumsum) * 100
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_pnl': total_pnl,
            'avg_pnl_pct': avg_pnl_pct,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'market_regime': self.market_regime.value,
        }
    
    def get_strategy_distribution(self) -> Dict:
        """Get breakdown of which strategies were used"""
        
        if not self.exit_history:
            return {}
        
        df_history = pd.DataFrame(self.exit_history)
        strategy_counts = df_history['strategy'].value_counts().to_dict()
        
        total = len(df_history)
        distribution = {
            strategy: {
                'count': count,
                'percentage': (count / total) * 100,
            }
            for strategy, count in strategy_counts.items()
        }
        
        logger.info(
            f"📊 Strategy Distribution:\n"
            f"{distribution}"
        )
        
        return distribution


# ============================================================================
if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    manager = UnifiedProfitBookingManager()
    
    # Simulate mean-reverting regime detection
    sample_trades = [
        {'holding_days': 0.1, 'max_profit_pct': 7.0},
        {'holding_days': 0.2, 'max_profit_pct': 6.5},
        {'holding_days': 0.15, 'max_profit_pct': 7.2},
    ]
    
    manager.detect_market_regime(sample_trades)
    manager.recent_trades = sample_trades
    
    # Create position
    pos = manager.create_position(
        symbol='TCS',
        entry_price=3100,
        quantity=100,
        position_id='TCS_001',
    )
    
    print("\n✅ Unified Strategy initialized and ready for deployment!")
