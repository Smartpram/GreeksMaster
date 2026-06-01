"""
Signal Executor
Connects screener signals → position tracking → automated execution
Implements end-to-end trading workflow:
1. Stock screener identifies opportunities
2. Signals trigger position actions
3. Risk validation before execution
4. Automatic order placement and tracking
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Execution modes for automated signals"""
    MANUAL = "manual"              # Alert only, require manual confirmation
    SEMI_AUTO = "semi_auto"        # Send alert for approval
    AUTO = "auto"                  # Execute automatically
    PAPER = "paper"                # Paper trading mode


class SignalExecutor:
    """
    Executes trading signals end-to-end:
    - Validates signal quality
    - Checks risk limits
    - Places orders
    - Tracks execution
    """
    
    def __init__(self, order_manager, risk_manager, position_tracker, 
                 notifications, execution_mode=ExecutionMode.PAPER):
        """
        Initialize signal executor
        
        Args:
            order_manager: Order execution service
            risk_manager: Risk validation service
            position_tracker: Live position tracking
            notifications: Alert/notification service
            execution_mode: Auto/manual/paper trading
        """
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.position_tracker = position_tracker
        self.notifications = notifications
        self.execution_mode = execution_mode
        
        self.execution_history: List[Dict] = []
        self.pending_approvals: Dict[str, Dict] = {}  # For semi-auto mode
    
    # ==================== ENTRY SIGNALS ====================
    
    def execute_buy_signal(self, symbol: str, price: float, 
                          confidence: float = 0.8,
                          reason: str = "screener",
                          metadata: Dict = None,
                          quantity: Optional[int] = None) -> Dict:
        """
        Execute buy signal
        
        Args:
            symbol: Stock to buy
            price: Target entry price
            confidence: Signal confidence (0-1)
            reason: Source of signal (screener, ai, technical, etc.)
            metadata: Additional signal metadata
            quantity: Quantity to buy (auto-calculated if None)
            
        Returns:
            Execution result
        """
        result = {
            'symbol': symbol,
            'signal_type': 'buy',
            'price': price,
            'confidence': confidence,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'order_id': None,
            'message': ''
        }
        
        try:
            # Step 1: Validate signal quality
            if confidence < 0.5:
                result['message'] = f'Signal confidence too low: {confidence:.0%}'
                logger.warning(result['message'])
                return result
            
            # Step 2: Calculate position size
            if quantity is None:
                position_size_result = self.risk_manager.validate_trade(
                    symbol=symbol,
                    side='BUY',
                    quantity=None,  # Auto-calculate
                    price=price
                )
                
                if not position_size_result.get('valid'):
                    result['message'] = position_size_result.get('message', 'Risk validation failed')
                    logger.warning(f"Position sizing failed: {result['message']}")
                    return result
                
                quantity = position_size_result.get('position_size', 0)
            
            if quantity <= 0:
                result['message'] = 'Calculated quantity <= 0'
                logger.warning(result['message'])
                return result
            
            # Step 3: Check execution mode
            if self.execution_mode == ExecutionMode.MANUAL:
                self.pending_approvals[f"{symbol}_{datetime.now().timestamp()}"] = {
                    'symbol': symbol,
                    'action': 'BUY',
                    'quantity': quantity,
                    'price': price,
                    'confidence': confidence,
                    'reason': reason,
                    'timestamp': datetime.now(),
                    'metadata': metadata
                }
                result['message'] = 'Signal requires manual approval'
                result['status'] = 'pending_approval'
                logger.info(f"Manual approval required: Buy {symbol} x{quantity} @ {price}")
                
                if self.notifications:
                    self.notifications.send_alert(
                        f"Trade Approval Needed: BUY {symbol}",
                        f"Qty: {quantity} | Price: {price:.2f} | Confidence: {confidence:.0%}",
                        severity='warning'
                    )
                
                return result
            
            elif self.execution_mode == ExecutionMode.SEMI_AUTO:
                # Send alert for confirmation, but also execute
                if self.notifications:
                    self.notifications.send_alert(
                        f"Trade Executing: BUY {symbol}",
                        f"Qty: {quantity} | Price: {price:.2f} | Confidence: {confidence:.0%} | "
                        f"Reason: {reason}",
                        severity='info'
                    )
            
            # Step 4: Place order
            order_result = self.order_manager.place_order(
                symbol=symbol,
                side='BUY',
                quantity=quantity,
                order_type='LIMIT',
                price=price,
                trigger_price=price * 0.95  # 5% stop loss below entry
            )
            
            if not order_result.get('success'):
                result['message'] = order_result.get('message', 'Order placement failed')
                logger.error(f"Order failed: {result['message']}")
                return result
            
            # Step 5: Track position
            order_id = order_result.get('order_id')
            position = self.position_tracker.open_position(
                symbol=symbol,
                entry_price=price,
                quantity=quantity,
                order_id=order_id,
                notes=f"Signal: {reason} (Confidence: {confidence:.0%})"
            )
            
            result['success'] = True
            result['order_id'] = order_id
            result['position_id'] = position.position_id
            result['quantity'] = quantity
            result['message'] = f'Buy order placed: {quantity} x {symbol} @ {price:.2f}'
            
            # Log execution
            self.execution_history.append(result)
            logger.info(f"✅ {result['message']}")
            
        except Exception as e:
            result['message'] = str(e)
            logger.error(f"Buy signal execution error: {e}")
        
        return result
    
    # ==================== EXIT SIGNALS ====================
    
    def execute_exit_signal(self, symbol: str, price: float,
                           confidence: float = 0.8,
                           reason: str = "technical",
                           exit_type: str = "full") -> Dict:
        """
        Execute exit/sell signal
        
        Args:
            symbol: Stock to exit
            price: Exit price
            confidence: Signal confidence
            reason: Exit reason (target, stop_loss, signal, etc.)
            exit_type: "full" or "partial"
            
        Returns:
            Execution result
        """
        result = {
            'symbol': symbol,
            'signal_type': 'sell',
            'price': price,
            'confidence': confidence,
            'reason': reason,
            'exit_type': exit_type,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'message': ''
        }
        
        try:
            # Get all open positions for symbol
            positions = self.position_tracker.get_symbol_positions(symbol)
            
            if not positions:
                result['message'] = f'No open positions for {symbol}'
                logger.warning(result['message'])
                return result
            
            # Execute exit for each position
            closed_positions = 0
            total_pnl = 0
            
            for pos_data in positions:
                pos_id = pos_data['position_id']
                quantity = pos_data['quantity']
                
                if exit_type == "full":
                    success = self.position_tracker.close_position(
                        pos_id, exit_price=price, reason=reason
                    )
                    if success:
                        closed_positions += 1
                        total_pnl += pos_data['unrealized_pnl']
                
                elif exit_type == "partial":
                    partial_qty = quantity // 2
                    success = self.position_tracker.partial_exit(
                        pos_id, exit_quantity=partial_qty,
                        exit_price=price, reason=reason
                    )
                    if success:
                        closed_positions += 1
                        total_pnl += (price - pos_data['entry_price']) * partial_qty
            
            if closed_positions > 0:
                result['success'] = True
                result['positions_closed'] = closed_positions
                result['total_pnl'] = total_pnl
                result['message'] = f'Closed {closed_positions} position(s), PnL: {total_pnl:.2f}'
                
                self.execution_history.append(result)
                logger.info(f"✅ {result['message']}")
                
                if self.notifications:
                    self.notifications.send_alert(
                        f"Positions Closed: {symbol}",
                        f"Closed: {closed_positions} | PnL: {total_pnl:.2f} | "
                        f"Reason: {reason}",
                        severity='info'
                    )
            else:
                result['message'] = 'Failed to close any positions'
                logger.warning(result['message'])
        
        except Exception as e:
            result['message'] = str(e)
            logger.error(f"Exit signal execution error: {e}")
        
        return result
    
    # ==================== TRIGGERED ACTIONS ====================
    
    def execute_screener_signal(self, screened_stocks: List[Dict],
                               auto_execute: bool = False) -> Dict:
        """
        Execute signals from stock screener results
        
        Args:
            screened_stocks: List of screener results with score/metadata
            auto_execute: Automatically buy high-confidence stocks
            
        Returns:
            Batch execution result
        """
        result = {
            'total_signals': len(screened_stocks),
            'executed': 0,
            'pending_approval': 0,
            'failed': 0,
            'executions': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            for stock_data in screened_stocks:
                symbol = stock_data.get('symbol')
                score = stock_data.get('score', 0)  # 0-100
                price = stock_data.get('price', 0)
                
                # Filter by score threshold
                if score < 70:  # Only high-confidence signals
                    continue
                
                # Convert score to confidence (0-1)
                confidence = score / 100
                
                # Execute buy signal
                execution = self.execute_buy_signal(
                    symbol=symbol,
                    price=price,
                    confidence=confidence,
                    reason='screener',
                    metadata={'screener_score': score}
                )
                
                result['executions'].append(execution)
                
                if execution['success']:
                    result['executed'] += 1
                elif execution.get('status') == 'pending_approval':
                    result['pending_approval'] += 1
                else:
                    result['failed'] += 1
            
            logger.info(f"Screener signals: {result['executed']} executed, "
                       f"{result['pending_approval']} pending, "
                       f"{result['failed']} failed")
        
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Screener signal batch execution error: {e}")
        
        return result
    
    def execute_technical_signal(self, symbol: str, 
                                 signal_data: Dict) -> Dict:
        """
        Execute technical analysis signal
        
        Args:
            symbol: Stock symbol
            signal_data: Technical signal data
                - 'type': 'buy' or 'sell'
                - 'price': Trigger price
                - 'indicators': Dict of triggered indicators
                - 'confidence': Confidence score (0-1)
                
        Returns:
            Execution result
        """
        signal_type = signal_data.get('type', 'buy')
        price = signal_data.get('price')
        confidence = signal_data.get('confidence', 0.7)
        indicators = signal_data.get('indicators', {})
        
        if signal_type == 'buy':
            return self.execute_buy_signal(
                symbol=symbol,
                price=price,
                confidence=confidence,
                reason='technical',
                metadata={'indicators': indicators}
            )
        else:  # sell
            return self.execute_exit_signal(
                symbol=symbol,
                price=price,
                confidence=confidence,
                reason='technical'
            )
    
    def execute_risk_signal(self, symbol: str, action: str,
                           reason: str) -> Dict:
        """
        Execute risk management signal
        
        Args:
            symbol: Stock symbol
            action: 'reduce', 'exit', 'hedge'
            reason: Risk reason ('daily_loss_limit', 'max_drawdown', etc.)
            
        Returns:
            Execution result
        """
        result = {
            'symbol': symbol,
            'signal_type': 'risk_management',
            'action': action,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'success': False
        }
        
        try:
            positions = self.position_tracker.get_symbol_positions(symbol)
            
            if not positions:
                result['message'] = f'No positions for {symbol}'
                return result
            
            if action == 'exit':
                # Exit all positions immediately at market
                for pos in positions:
                    self.position_tracker.close_position(
                        pos['position_id'],
                        exit_price=pos['current_price'],
                        reason=f"risk_mgmt: {reason}"
                    )
                result['success'] = True
                result['action_taken'] = 'all_positions_closed'
            
            elif action == 'reduce':
                # Reduce by 50%
                for pos in positions:
                    self.position_tracker.partial_exit(
                        pos['position_id'],
                        exit_quantity=pos['quantity'] // 2,
                        exit_price=pos['current_price'],
                        reason=f"risk_mgmt: {reason}"
                    )
                result['success'] = True
                result['action_taken'] = 'positions_reduced'
            
            if self.notifications:
                self.notifications.send_alert(
                    f"Risk Action: {symbol}",
                    f"Action: {action} | Reason: {reason}",
                    severity='critical'
                )
        
        except Exception as e:
            result['message'] = str(e)
            logger.error(f"Risk signal execution error: {e}")
        
        return result
    
    # ==================== APPROVAL WORKFLOW (SEMI-AUTO MODE) ====================
    
    def approve_pending_signal(self, signal_id: str) -> bool:
        """Approve a pending manual signal"""
        if signal_id not in self.pending_approvals:
            logger.warning(f"Signal {signal_id} not found")
            return False
        
        signal = self.pending_approvals.pop(signal_id)
        
        if signal['action'] == 'BUY':
            result = self.execute_buy_signal(
                symbol=signal['symbol'],
                price=signal['price'],
                confidence=signal['confidence'],
                reason=signal['reason'],
                quantity=signal['quantity']
            )
        elif signal['action'] == 'SELL':
            result = self.execute_exit_signal(
                symbol=signal['symbol'],
                price=signal['price'],
                confidence=signal['confidence'],
                reason=signal['reason']
            )
        
        return result.get('success', False)
    
    def reject_pending_signal(self, signal_id: str) -> bool:
        """Reject a pending manual signal"""
        if signal_id in self.pending_approvals:
            self.pending_approvals.pop(signal_id)
            logger.info(f"Signal {signal_id} rejected")
            return True
        return False
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get all pending approval signals"""
        return list(self.pending_approvals.values())
    
    # ==================== EXECUTION TRACKING ====================
    
    def get_execution_history(self, hours: int = 24,
                             symbol: Optional[str] = None) -> List[Dict]:
        """Get execution history"""
        from datetime import timedelta
        
        cutoff_time = datetime.fromisoformat(
            (datetime.now() - timedelta(hours=hours)).isoformat()
        )
        
        results = []
        for execution in self.execution_history:
            exec_time = datetime.fromisoformat(execution['timestamp'])
            
            if exec_time < cutoff_time:
                continue
            
            if symbol and execution.get('symbol') != symbol:
                continue
            
            results.append(execution)
        
        return results
    
    def get_execution_stats(self) -> Dict:
        """Get execution statistics"""
        if not self.execution_history:
            return {
                'total_signals': 0,
                'successful': 0,
                'failed': 0,
                'pending': len(self.pending_approvals),
                'success_rate': 0
            }
        
        successful = sum(1 for ex in self.execution_history if ex.get('success'))
        total = len(self.execution_history)
        
        return {
            'total_signals': total,
            'successful': successful,
            'failed': total - successful,
            'pending': len(self.pending_approvals),
            'success_rate': round(successful / total * 100, 1),
            'execution_mode': self.execution_mode.value
        }
    
    def set_execution_mode(self, mode: ExecutionMode):
        """Change execution mode at runtime"""
        self.execution_mode = mode
        logger.info(f"Execution mode changed to: {mode.value}")
        
        if self.notifications:
            self.notifications.send_alert(
                "Execution Mode Changed",
                f"New mode: {mode.value}",
                severity='info'
            )
