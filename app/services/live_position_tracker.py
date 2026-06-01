"""
Live Position Tracking System
Tracks all open positions in real-time with:
- Entry/Exit management
- P&L calculation
- Risk metrics
- Position status updates
- Signal/Trigger execution
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class PositionStatus(Enum):
    """Position lifecycle status"""
    PENDING = "pending"           # Order placed, waiting execution
    OPEN = "open"                # Position is active
    PARTIAL = "partial"          # Partially filled
    CLOSING = "closing"          # Close order in progress
    CLOSED = "closed"            # Position closed
    CANCELLED = "cancelled"      # Order cancelled
    ERROR = "error"              # Error state


class SignalType(Enum):
    """Types of trading signals"""
    BUY = "buy"
    SELL = "sell"
    EXIT = "exit"
    PARTIAL_EXIT = "partial_exit"
    ADD_POSITION = "add"
    REDUCE_POSITION = "reduce"
    TRAILING_STOP = "trailing_stop"
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"


class TriggerType(Enum):
    """Trigger execution types"""
    TECHNICAL = "technical"      # Technical analysis trigger
    FUNDAMENTAL = "fundamental"  # Fundamental trigger
    RISK_MGMT = "risk_mgmt"     # Risk management trigger
    SCREENER = "screener"        # Stock screener signal
    AI = "ai"                    # AI model signal
    MANUAL = "manual"            # Manual signal
    ALERT = "alert"              # Alert-based trigger


@dataclass
class TradeEntry:
    """Trade entry record"""
    order_id: str
    symbol: str
    entry_price: float
    quantity: int
    entry_time: datetime
    order_status: str = "pending"
    actual_price: float = 0
    actual_quantity: int = 0


@dataclass
class TradeExit:
    """Trade exit record"""
    order_id: str
    exit_price: float
    quantity: int
    exit_time: datetime
    reason: str  # "target", "stop_loss", "manual", "signal"
    pnl: float = 0
    pnl_percent: float = 0


@dataclass
class SignalTrigger:
    """Signal trigger record"""
    trigger_id: str
    signal_type: SignalType
    trigger_type: TriggerType
    symbol: str
    triggered_at: datetime
    trigger_price: float
    confidence: float  # 0-1
    metadata: Dict = None  # Additional context
    action_taken: bool = False
    execution_time: Optional[datetime] = None


@dataclass
class LivePosition:
    """Live position tracking record"""
    position_id: str
    symbol: str
    entry: TradeEntry
    status: PositionStatus
    current_price: float
    current_quantity: int
    entry_value: float  # Entry price * quantity
    current_value: float  # Current price * current quantity
    unrealized_pnl: float
    unrealized_pnl_percent: float
    realized_pnl: float = 0  # PnL from closed portions
    highest_price: float = 0  # For trailing stops
    lowest_price: float = 0  # For stop loss analysis
    days_open: int = 0
    num_triggers: int = 0  # Signal triggers on this position
    triggers: List[SignalTrigger] = None
    partial_exits: List[TradeExit] = None
    notes: str = ""
    
    def to_dict(self):
        return {
            'position_id': self.position_id,
            'symbol': self.symbol,
            'status': self.status.value,
            'quantity': self.current_quantity,
            'entry_price': round(self.entry.actual_price, 2),
            'current_price': round(self.current_price, 2),
            'entry_value': round(self.entry_value, 2),
            'current_value': round(self.current_value, 2),
            'unrealized_pnl': round(self.unrealized_pnl, 2),
            'unrealized_pnl_percent': round(self.unrealized_pnl_percent * 100, 2),
            'realized_pnl': round(self.realized_pnl, 2),
            'days_open': self.days_open,
            'num_triggers': self.num_triggers,
            'highest_price': round(self.highest_price, 2),
            'lowest_price': round(self.lowest_price, 2),
            'entry_time': self.entry.entry_time.isoformat(),
            'notes': self.notes
        }


class LivePositionTracker:
    """
    Tracks all live positions with real-time updates
    """
    
    def __init__(self, risk_manager=None, notifications=None):
        """
        Initialize position tracker
        
        Args:
            risk_manager: Risk manager for validation
            notifications: Notification service
        """
        self.risk_manager = risk_manager
        self.notifications = notifications
        
        self.positions: Dict[str, LivePosition] = {}  # position_id -> LivePosition
        self.symbol_positions: Dict[str, List[str]] = {}  # symbol -> [position_ids]
        self.signal_history: List[SignalTrigger] = []
        self.execution_log: List[Dict] = []
    
    # ==================== POSITION MANAGEMENT ====================
    
    def open_position(self, symbol: str, entry_price: float, quantity: int,
                     order_id: str, notes: str = "") -> LivePosition:
        """
        Open a new trading position
        
        Args:
            symbol: Stock symbol
            entry_price: Entry price
            quantity: Order quantity
            order_id: Order ID from broker
            notes: Additional notes
            
        Returns:
            LivePosition object
        """
        position_id = f"{symbol}_{order_id}_{datetime.now().timestamp()}"
        
        entry = TradeEntry(
            order_id=order_id,
            symbol=symbol,
            entry_price=entry_price,
            quantity=quantity,
            entry_time=datetime.now(),
            actual_price=entry_price,
            actual_quantity=quantity
        )
        
        position = LivePosition(
            position_id=position_id,
            symbol=symbol,
            entry=entry,
            status=PositionStatus.OPEN,
            current_price=entry_price,
            current_quantity=quantity,
            entry_value=entry_price * quantity,
            current_value=entry_price * quantity,
            unrealized_pnl=0,
            unrealized_pnl_percent=0,
            highest_price=entry_price,
            lowest_price=entry_price,
            notes=notes,
            triggers=[],
            partial_exits=[]
        )
        
        # Store position
        self.positions[position_id] = position
        
        # Index by symbol
        if symbol not in self.symbol_positions:
            self.symbol_positions[symbol] = []
        self.symbol_positions[symbol].append(position_id)
        
        logger.info(f"📍 Position opened: {symbol} x{quantity} @ {entry_price} (ID: {position_id})")
        
        if self.notifications:
            self.notifications.send_alert(
                f"Position Opened: {symbol}",
                f"Quantity: {quantity} | Price: {entry_price:.2f}",
                severity='info'
            )
        
        return position
    
    def update_position_price(self, position_id: str, current_price: float) -> bool:
        """
        Update position with latest market price
        
        Returns:
            True if updated, False if position not found
        """
        if position_id not in self.positions:
            return False
        
        position = self.positions[position_id]
        
        # Update price
        position.current_price = current_price
        position.current_value = current_price * position.current_quantity
        
        # Update unrealized PnL
        position.unrealized_pnl = position.current_value - position.entry_value
        position.unrealized_pnl_percent = (position.unrealized_pnl / position.entry_value 
                                          if position.entry_value > 0 else 0)
        
        # Track highest/lowest
        if current_price > position.highest_price:
            position.highest_price = current_price
        if current_price < position.lowest_price:
            position.lowest_price = current_price
        
        # Update days open
        position.days_open = (datetime.now() - position.entry.entry_time).days
        
        return True
    
    def record_signal(self, position_id: str, signal: SignalTrigger) -> bool:
        """
        Record a signal/trigger on a position
        
        Args:
            position_id: Position to apply signal to
            signal: SignalTrigger object
            
        Returns:
            True if recorded
        """
        if position_id not in self.positions:
            logger.warning(f"Position {position_id} not found for signal")
            return False
        
        position = self.positions[position_id]
        position.triggers.append(signal)
        position.num_triggers += 1
        
        self.signal_history.append(signal)
        
        logger.info(f"Signal recorded: {signal.signal_type.value} on {position_id} "
                   f"(Confidence: {signal.confidence:.0%})")
        
        return True
    
    def partial_exit(self, position_id: str, exit_quantity: int, 
                    exit_price: float, reason: str) -> bool:
        """
        Partially close a position
        
        Args:
            position_id: Position to partially close
            exit_quantity: Quantity to exit
            exit_price: Exit price
            reason: Reason for exit ("target", "stop_loss", "signal", etc.)
            
        Returns:
            True if successful
        """
        if position_id not in self.positions:
            return False
        
        position = self.positions[position_id]
        
        if exit_quantity > position.current_quantity:
            logger.error(f"Cannot exit {exit_quantity}, position only has {position.current_quantity}")
            return False
        
        # Calculate exit PnL
        exit_pnl = (exit_price * exit_quantity) - (position.entry.actual_price * exit_quantity)
        
        exit_record = TradeExit(
            order_id=f"exit_{position_id}_{datetime.now().timestamp()}",
            exit_price=exit_price,
            quantity=exit_quantity,
            exit_time=datetime.now(),
            reason=reason,
            pnl=exit_pnl,
            pnl_percent=(exit_pnl / (position.entry.actual_price * exit_quantity)) if exit_quantity > 0 else 0
        )
        
        # Update position
        position.current_quantity -= exit_quantity
        position.current_value = position.current_price * position.current_quantity
        position.realized_pnl += exit_pnl
        position.partial_exits.append(exit_record)
        
        # Update status if fully closed
        if position.current_quantity <= 0:
            position.status = PositionStatus.CLOSED
            logger.info(f"Position closed: {position.symbol} (Reason: {reason}, PnL: {exit_pnl:.2f})")
        else:
            logger.info(f"Partial exit: {position.symbol} x{exit_quantity} @ {exit_price} "
                       f"(PnL: {exit_pnl:.2f})")
        
        if self.notifications:
            self.notifications.send_alert(
                f"Position Exit: {position.symbol}",
                f"Quantity: {exit_quantity} | Price: {exit_price:.2f} | Reason: {reason}",
                severity='info'
            )
        
        return True
    
    def close_position(self, position_id: str, exit_price: float, 
                      reason: str = "manual") -> bool:
        """
        Fully close a position
        
        Args:
            position_id: Position to close
            exit_price: Exit price
            reason: Reason for closure
            
        Returns:
            True if closed
        """
        if position_id not in self.positions:
            return False
        
        position = self.positions[position_id]
        
        # Exit all remaining quantity
        if position.current_quantity > 0:
            return self.partial_exit(position_id, position.current_quantity, 
                                    exit_price, reason)
        
        return True
    
    # ==================== SIGNAL EXECUTION ====================
    
    def execute_signal(self, trigger: SignalTrigger, position_id: str) -> Dict:
        """
        Execute signal/trigger action on a position
        
        Args:
            trigger: Signal trigger to execute
            position_id: Target position
            
        Returns:
            Execution result dictionary
        """
        if position_id not in self.positions:
            return {'success': False, 'error': f'Position {position_id} not found'}
        
        position = self.positions[position_id]
        result = {
            'trigger_id': trigger.trigger_id,
            'signal_type': trigger.signal_type.value,
            'trigger_type': trigger.trigger_type.value,
            'symbol': position.symbol,
            'success': False
        }
        
        try:
            if trigger.signal_type == SignalType.EXIT:
                # Exit entire position
                self.close_position(position_id, trigger.trigger_price, 
                                   reason=trigger.trigger_type.value)
                result['success'] = True
                result['action'] = 'full_exit'
                result['quantity'] = position.current_quantity
                
            elif trigger.signal_type == SignalType.PARTIAL_EXIT:
                # Exit 50% of position
                quantity = position.current_quantity // 2
                self.partial_exit(position_id, quantity, trigger.trigger_price,
                                 reason=trigger.trigger_type.value)
                result['success'] = True
                result['action'] = 'partial_exit'
                result['quantity'] = quantity
                
            elif trigger.signal_type == SignalType.ADD_POSITION:
                # Add to position (pyramid up)
                if position.unrealized_pnl_percent > 0:  # Only add on winners
                    add_quantity = position.entry.actual_quantity
                    result['success'] = True
                    result['action'] = 'add_position'
                    result['quantity'] = add_quantity
                
            elif trigger.signal_type == SignalType.TRAILING_STOP:
                # Move stop loss up (trailing)
                pnl_percent = position.unrealized_pnl_percent
                if pnl_percent > 0.05:  # At least 5% profit
                    new_stop = trigger.trigger_price
                    result['success'] = True
                    result['action'] = 'trailing_stop'
                    result['new_stop_level'] = new_stop
            
            elif trigger.signal_type == SignalType.STOP_LOSS:
                # Hit stop loss
                self.close_position(position_id, trigger.trigger_price, 
                                   reason="stop_loss")
                result['success'] = True
                result['action'] = 'stop_loss'
                result['quantity'] = position.current_quantity
                
            elif trigger.signal_type == SignalType.TAKE_PROFIT:
                # Hit take profit
                self.close_position(position_id, trigger.trigger_price,
                                   reason="take_profit")
                result['success'] = True
                result['action'] = 'take_profit'
                result['quantity'] = position.current_quantity
                result['pnl'] = position.realized_pnl
            
            trigger.action_taken = True
            trigger.execution_time = datetime.now()
            
            logger.info(f"Signal executed: {result}")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Signal execution failed: {e}")
        
        return result
    
    # ==================== QUERIES & REPORTING ====================
    
    def get_all_positions(self) -> List[Dict]:
        """Get all open positions"""
        return [pos.to_dict() for pos in self.positions.values() 
                if pos.status in [PositionStatus.OPEN, PositionStatus.PARTIAL]]
    
    def get_position(self, position_id: str) -> Optional[Dict]:
        """Get specific position details"""
        if position_id in self.positions:
            return self.positions[position_id].to_dict()
        return None
    
    def get_symbol_positions(self, symbol: str) -> List[Dict]:
        """Get all positions for a symbol"""
        if symbol not in self.symbol_positions:
            return []
        
        result = []
        for pos_id in self.symbol_positions[symbol]:
            pos = self.positions.get(pos_id)
            if pos:
                result.append(pos.to_dict())
        
        return result
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio-level summary"""
        open_positions = [pos for pos in self.positions.values() 
                         if pos.status in [PositionStatus.OPEN, PositionStatus.PARTIAL]]
        
        total_entry_value = sum(pos.entry_value for pos in open_positions)
        total_current_value = sum(pos.current_value for pos in open_positions)
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in open_positions)
        total_realized_pnl = sum(pos.realized_pnl for pos in open_positions)
        total_pnl = total_unrealized_pnl + total_realized_pnl
        
        # PnL percentage
        pnl_percent = (total_pnl / total_entry_value * 100) if total_entry_value > 0 else 0
        
        # Win rate
        closed_positions = [pos for pos in self.positions.values() 
                           if pos.status == PositionStatus.CLOSED]
        winners = sum(1 for pos in closed_positions if pos.realized_pnl > 0)
        win_rate = (winners / len(closed_positions) * 100) if closed_positions else 0
        
        return {
            'open_positions': len(open_positions),
            'total_entry_value': round(total_entry_value, 2),
            'total_current_value': round(total_current_value, 2),
            'unrealized_pnl': round(total_unrealized_pnl, 2),
            'realized_pnl': round(total_realized_pnl, 2),
            'total_pnl': round(total_pnl, 2),
            'total_pnl_percent': round(pnl_percent, 2),
            'closed_positions': len(closed_positions),
            'win_rate': round(win_rate, 1),
            'avg_winning_trade': self._calculate_avg_win(),
            'avg_losing_trade': self._calculate_avg_loss(),
            'best_trade': self._calculate_best_trade(),
            'worst_trade': self._calculate_worst_trade()
        }
    
    def _calculate_avg_win(self) -> float:
        """Calculate average winning trade"""
        closed = [pos.realized_pnl for pos in self.positions.values() 
                 if pos.status == PositionStatus.CLOSED and pos.realized_pnl > 0]
        return round(sum(closed) / len(closed), 2) if closed else 0
    
    def _calculate_avg_loss(self) -> float:
        """Calculate average losing trade"""
        closed = [pos.realized_pnl for pos in self.positions.values() 
                 if pos.status == PositionStatus.CLOSED and pos.realized_pnl < 0]
        return round(sum(closed) / len(closed), 2) if closed else 0
    
    def _calculate_best_trade(self) -> float:
        """Calculate best trade PnL"""
        closed = [pos.realized_pnl for pos in self.positions.values() 
                 if pos.status == PositionStatus.CLOSED]
        return round(max(closed), 2) if closed else 0
    
    def _calculate_worst_trade(self) -> float:
        """Calculate worst trade PnL"""
        closed = [pos.realized_pnl for pos in self.positions.values() 
                 if pos.status == PositionStatus.CLOSED]
        return round(min(closed), 2) if closed else 0
    
    def get_signals_log(self, position_id: Optional[str] = None, 
                       hours: int = 24) -> List[Dict]:
        """
        Get signal execution log
        
        Args:
            position_id: Filter by position (optional)
            hours: Hours to look back (default 24)
            
        Returns:
            List of signal records
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        results = []
        for signal in self.signal_history:
            if signal.triggered_at < cutoff_time:
                continue
            
            if position_id and signal.symbol != position_id:
                continue
            
            results.append({
                'trigger_id': signal.trigger_id,
                'signal_type': signal.signal_type.value,
                'trigger_type': signal.trigger_type.value,
                'symbol': signal.symbol,
                'trigger_price': round(signal.trigger_price, 2),
                'confidence': round(signal.confidence * 100, 1),
                'triggered_at': signal.triggered_at.isoformat(),
                'action_taken': signal.action_taken,
                'execution_time': signal.execution_time.isoformat() if signal.execution_time else None
            })
        
        return results
    
    def export_positions(self) -> str:
        """Export positions as JSON"""
        data = {
            'export_time': datetime.now().isoformat(),
            'positions': [pos.to_dict() for pos in self.positions.values()],
            'summary': self.get_portfolio_summary()
        }
        return json.dumps(data, indent=2)
