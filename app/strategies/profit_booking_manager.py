"""
Profit Booking Strategy Manager
Implements Fixed Full Exit vs Partial Exit + Trailing Stop strategies
"""
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class ExitStrategy(Enum):
    """Profit booking exit strategies"""
    FIXED_FULL_EXIT = "fixed_full_exit"           # Sell 100% at target
    PARTIAL_EXIT = "partial_exit"                  # Sell 50% at target, trail 50%
    PARTIAL_WITH_TRAILING = "partial_with_trailing"  # Enhanced: partial + trailing
    HYBRID_ADAPTIVE = "hybrid_adaptive"            # Detect regime and adapt


class ExitReason(Enum):
    """Reasons for exiting a position"""
    TARGET_HIT = "target_hit"
    STOP_LOSS_HIT = "stop_loss_hit"
    TRAILING_STOP_HIT = "trailing_stop_hit"
    BREAKEVEN_STOP_HIT = "breakeven_stop_hit"
    REVERSAL_HIT = "reversal_hit"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    MANUAL_EXIT = "manual_exit"


class PositionState:
    """Tracks state of a single position with profit booking"""
    
    def __init__(self, symbol: str, entry_price: float, quantity: int, 
                 position_id: str, exit_strategy: ExitStrategy):
        self.symbol = symbol
        self.entry_price = entry_price
        self.quantity = quantity
        self.position_id = position_id
        self.exit_strategy = exit_strategy
        self.entry_time = datetime.now()
        
        # Core exit prices
        self.stop_loss = 0.0
        self.target = 0.0
        
        # For partial exit strategy
        self.first_exit_qty = 0  # Qty to exit at target
        self.trailing_exit_qty = 0  # Qty to trail
        self.first_exit_done = False
        
        # For trailing stop
        self.highest_price = entry_price
        self.lowest_price = entry_price
        self.trailing_stop = 0.0
        self.breakeven_stop = entry_price
        
        # Trade metrics
        self.max_profit_pct = 0.0
        self.current_profit_pct = 0.0
        self.exit_price = 0.0
        self.exit_reason = None
        self.exit_time = None
        
    def update_price(self, current_price: float):
        """Update position with current price"""
        self.highest_price = max(self.highest_price, current_price)
        self.lowest_price = min(self.lowest_price, current_price)
        self.current_profit_pct = ((current_price - self.entry_price) / self.entry_price) * 100
        self.max_profit_pct = max(self.max_profit_pct, self.current_profit_pct)


class ProfitBookingManager:
    """Manages profit booking strategies for positions"""
    
    def __init__(self, risk_manager=None):
        self.risk_manager = risk_manager
        self.positions: Dict[str, PositionState] = {}
        self.exit_history = []
        self.default_exit_strategy = ExitStrategy.FIXED_FULL_EXIT
        
        # Strategy configuration
        self.config = {
            'target_pct': 0.06,              # 6% target
            'stop_loss_pct': 0.04,           # 4% stop loss
            'trailing_stop_pct': 0.02,       # 2% trailing distance
            'partial_exit_ratio': 0.50,      # Exit 50% at target
            'partial_trail_ratio': 0.50,     # Trail remaining 50%
            'breakeven_protection': True,    # Protect trailing stop at breakeven
        }
        
    def create_position(self, symbol: str, entry_price: float, quantity: int,
                       position_id: str, exit_strategy: ExitStrategy = None,
                       custom_target: float = None, custom_stop_loss: float = None) -> PositionState:
        """Create a new position with profit booking setup"""
        
        strategy = exit_strategy or self.default_exit_strategy
        pos = PositionState(symbol, entry_price, quantity, position_id, strategy)
        
        # Set exit prices
        target_pct = custom_target or self.config['target_pct']
        stop_loss_pct = custom_stop_loss or self.config['stop_loss_pct']
        
        pos.target = entry_price * (1 + target_pct)
        pos.stop_loss = entry_price * (1 - stop_loss_pct)
        pos.breakeven_stop = entry_price
        
        # Initialize trailing stop
        pos.trailing_stop = pos.stop_loss
        
        # Setup partial exit quantities
        if strategy in [ExitStrategy.PARTIAL_EXIT, ExitStrategy.PARTIAL_WITH_TRAILING]:
            partial_ratio = self.config['partial_exit_ratio']
            pos.first_exit_qty = int(quantity * partial_ratio)
            pos.trailing_exit_qty = quantity - pos.first_exit_qty
        
        self.positions[position_id] = pos
        logger.info(
            f"📍 Position created: {symbol} | Entry: ₹{entry_price:.2f} | "
            f"Target: ₹{pos.target:.2f} | SL: ₹{pos.stop_loss:.2f} | "
            f"Strategy: {strategy.value}"
        )
        
        return pos
    
    def check_exit_conditions(self, position_id: str, current_price: float) -> Tuple[bool, ExitReason, Optional[Dict]]:
        """
        Check if position should exit based on current price
        
        Returns:
            (should_exit, exit_reason, exit_details)
        """
        if position_id not in self.positions:
            return False, None, None
        
        pos = self.positions[position_id]
        pos.update_price(current_price)
        
        # Fixed Full Exit Strategy
        if pos.exit_strategy == ExitStrategy.FIXED_FULL_EXIT:
            return self._check_fixed_full_exit(pos, current_price)
        
        # Partial + Trailing Strategy
        elif pos.exit_strategy in [ExitStrategy.PARTIAL_EXIT, ExitStrategy.PARTIAL_WITH_TRAILING]:
            return self._check_partial_trailing_exit(pos, current_price)
        
        # Default to fixed full exit
        else:
            return self._check_fixed_full_exit(pos, current_price)
    
    def _check_fixed_full_exit(self, pos: PositionState, current_price: float) -> Tuple[bool, ExitReason, Dict]:
        """Check exit for Fixed Full Exit strategy"""
        
        # Check stop loss first (most critical)
        if current_price <= pos.stop_loss:
            pos.exit_price = pos.stop_loss
            pos.exit_reason = ExitReason.STOP_LOSS_HIT
            return True, ExitReason.STOP_LOSS_HIT, {
                'exit_qty': pos.quantity,
                'exit_price': pos.stop_loss,
                'pnl_pct': pos.current_profit_pct,
                'max_profit_pct': pos.max_profit_pct
            }
        
        # Check target
        if current_price >= pos.target:
            pos.exit_price = pos.target
            pos.exit_reason = ExitReason.TARGET_HIT
            return True, ExitReason.TARGET_HIT, {
                'exit_qty': pos.quantity,
                'exit_price': pos.target,
                'pnl_pct': pos.current_profit_pct,
                'max_profit_pct': pos.max_profit_pct
            }
        
        return False, None, None
    
    def _check_partial_trailing_exit(self, pos: PositionState, current_price: float) -> Tuple[bool, ExitReason, Dict]:
        """Check exit for Partial Exit + Trailing Stop strategy"""
        
        # Check stop loss first (critical)
        if current_price <= pos.stop_loss:
            pos.exit_price = pos.stop_loss
            pos.exit_reason = ExitReason.STOP_LOSS_HIT
            return True, ExitReason.STOP_LOSS_HIT, {
                'exit_qty': pos.quantity,
                'exit_price': pos.stop_loss,
                'pnl_pct': pos.current_profit_pct,
                'max_profit_pct': pos.max_profit_pct,
                'first_exit_done': pos.first_exit_done
            }
        
        # Stage 1: Check if first tranche should exit at target
        if not pos.first_exit_done and current_price >= pos.target:
            pos.first_exit_done = True
            pos.exit_reason = ExitReason.TARGET_HIT
            
            return True, ExitReason.TARGET_HIT, {
                'exit_qty': pos.first_exit_qty,
                'remaining_qty': pos.trailing_exit_qty,
                'exit_price': pos.target,
                'pnl_pct': pos.current_profit_pct,
                'max_profit_pct': pos.max_profit_pct,
                'stage': 'first_exit',
                'is_partial': True
            }
        
        # Stage 2: If first exit done, manage trailing stop on remaining quantity
        if pos.first_exit_done and pos.trailing_exit_qty > 0:
            # Update trailing stop as price rises
            trail_pct = self.config['trailing_stop_pct']
            new_trailing = current_price * (1 - trail_pct)
            
            # Update trailing stop (never lower than breakeven)
            if self.config['breakeven_protection']:
                pos.trailing_stop = max(new_trailing, pos.breakeven_stop)
            else:
                pos.trailing_stop = new_trailing
            
            # Check if trailing stop hit
            if current_price <= pos.trailing_stop:
                pos.exit_price = pos.trailing_stop
                pos.exit_reason = ExitReason.TRAILING_STOP_HIT
                
                return True, ExitReason.TRAILING_STOP_HIT, {
                    'exit_qty': pos.trailing_exit_qty,
                    'exit_price': pos.trailing_stop,
                    'pnl_pct': pos.current_profit_pct,
                    'max_profit_pct': pos.max_profit_pct,
                    'stage': 'trailing_exit',
                    'is_partial': True
                }
        
        return False, None, None
    
    def execute_exit(self, position_id: str, exit_price: float, 
                    actual_exit_qty: int = None) -> Dict:
        """Execute exit and record trade results"""
        
        if position_id not in self.positions:
            logger.error(f"Position {position_id} not found")
            return {}
        
        pos = self.positions[position_id]
        exit_qty = actual_exit_qty or pos.quantity
        
        # Calculate P&L
        pnl = (exit_price - pos.entry_price) * exit_qty
        pnl_pct = ((exit_price - pos.entry_price) / pos.entry_price) * 100
        
        # Record exit
        exit_record = {
            'position_id': position_id,
            'symbol': pos.symbol,
            'entry_price': pos.entry_price,
            'exit_price': exit_price,
            'entry_time': pos.entry_time,
            'exit_time': datetime.now(),
            'entry_qty': pos.quantity,
            'exit_qty': exit_qty,
            'holding_days': (pos.exit_time or datetime.now() - pos.entry_time).days,
            'exit_reason': pos.exit_reason,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'max_profit_pct': pos.max_profit_pct,
            'strategy': pos.exit_strategy.value,
            'remaining_qty': pos.quantity - exit_qty
        }
        
        self.exit_history.append(exit_record)
        pos.exit_time = datetime.now()
        
        logger.info(
            f"✅ Exit executed: {pos.symbol} | Exit: ₹{exit_price:.2f} | "
            f"Qty: {exit_qty} | P&L: {pnl_pct:.2f}% | Reason: {pos.exit_reason.value}"
        )
        
        return exit_record
    
    def get_position_summary(self, position_id: str) -> Dict:
        """Get summary of a position"""
        if position_id not in self.positions:
            return {}
        
        pos = self.positions[position_id]
        return {
            'symbol': pos.symbol,
            'entry_price': pos.entry_price,
            'current_price': pos.highest_price,  # Using highest as reference
            'quantity': pos.quantity,
            'exit_strategy': pos.exit_strategy.value,
            'target': pos.target,
            'stop_loss': pos.stop_loss,
            'trailing_stop': pos.trailing_stop if pos.exit_strategy != ExitStrategy.FIXED_FULL_EXIT else None,
            'max_profit_pct': pos.max_profit_pct,
            'current_profit_pct': pos.current_profit_pct,
            'first_exit_done': pos.first_exit_done if hasattr(pos, 'first_exit_done') else None,
        }
    
    def get_strategy_stats(self) -> Dict:
        """Get statistics for all completed trades"""
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
                'max_drawdown': 0
            }
        
        df = pd.DataFrame(self.exit_history)
        
        wins = df[df['pnl'] > 0]
        losses = df[df['pnl'] <= 0]
        
        total_wins = wins['pnl'].sum() if not wins.empty else 0
        total_losses = abs(losses['pnl'].sum()) if not losses.empty else 0
        
        total_trades = len(df)
        winning_trades = len(wins)
        losing_trades = len(losses)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        total_pnl = df['pnl'].sum()
        
        # avg_pnl_pct - average return per trade (as percentage)
        avg_pnl_pct = df['pnl_pct'].mean()
        
        # Sharpe ratio: (mean return - risk free rate) / std dev * sqrt(252)
        # For strategy evaluation, use actual trade returns
        returns = df['pnl_pct'].values / 100  # Convert to decimal (not percentage)
        if len(returns) > 1 and returns.std() > 0:
            sharpe = (returns.mean() / returns.std() * np.sqrt(252))
        else:
            sharpe = 0
        
        # max drawdown calculation - properly calculate rolling max drawdown as percentage
        cumulative_pnl = df['pnl'].cumsum()
        running_max = cumulative_pnl.cummax()
        drawdown_amounts = (cumulative_pnl - running_max)
        # Normalize drawdown to percentage of max cumulative P&L achieved
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
            'avg_holding_days': df['holding_days'].mean() if not df.empty else 0,
        }
    
    def get_exit_history(self) -> List[Dict]:
        """Get history of all exits"""
        return self.exit_history
