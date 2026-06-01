"""
CASH FLOW INTEGRATION WITH ORDER MANAGER
==========================================

This shows how to integrate CashFlowManager with the existing OrderManager
to ensure funds are never overspent in production.

Integration Points:
1. Before Order Execution: Validate funds available
2. At Order Execution: Block cash immediately
3. At Trade Close: Release/Settle funds
4. Daily Monitoring: Check limits and cash position
"""

import logging
from typing import Tuple, Dict, Optional
from datetime import datetime
from app.services.cash_flow_manager import (
    CashFlowManager, TransactionType, SettlementType
)

logger = logging.getLogger(__name__)


class OrderManagerWithCashFlow:
    """
    Enhanced Order Manager with integrated Cash Flow Management
    
    This prevents scenarios like:
    - Buying 10 different stocks without checking available funds
    - Not accounting for T+2 settlement delays
    - Overdrawing account during intraday liquidations
    """
    
    def __init__(self, order_manager, cash_flow_manager: CashFlowManager):
        """
        Initialize with existing order manager and cash flow manager
        
        Args:
            order_manager: Existing OrderManager instance
            cash_flow_manager: CashFlowManager instance
        """
        self.order_manager = order_manager
        self.cash_flow = cash_flow_manager
        self.logger = logging.getLogger(__name__)
    
    # =========================================================================
    # DELIVERY ORDERS (Most Important - Where Overspend Happens)
    # =========================================================================
    
    def place_delivery_buy_order(self, symbol: str, quantity: int, 
                                 price: float, order_type: str = "MARKET") -> Tuple[bool, str, Dict]:
        """
        Place a delivery buy order WITH cash validation
        
        CRITICAL VALIDATION:
        1. Check if cash available (funds blocked immediately)
        2. Verify not exceeding daily limits
        3. Only then place actual order
        
        Returns:
            (success, message, details)
        """
        self.logger.info(f"=== DELIVERY BUY: {symbol} {quantity}@₹{price} ===")
        
        # STEP 1: Validate cash availability
        can_buy, reason, details = self.cash_flow.can_buy_delivery(symbol, quantity, price)
        
        if not can_buy:
            self.logger.error(f"REJECTED: {reason}")
            return False, reason, details
        
        self.logger.info(f"Cash validation PASSED: ₹{details['total_cost']:,.2f} available")
        
        # STEP 2: Place order on exchange (if cash validated)
        try:
            # This would call your actual order_manager
            # order_result = self.order_manager.place_order(symbol, quantity, price, order_type)
            
            # For now, simulate successful order
            order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # STEP 3: Record in cash flow system
            brokerage = (quantity * price) * 0.001  # Simulated
            txn_id = self.cash_flow.record_buy_delivery(
                order_id=order_id,
                symbol=symbol,
                quantity=quantity,
                price=price,
                brokerage=brokerage
            )
            
            details.update({
                'order_id': order_id,
                'transaction_id': txn_id,
                'status': 'EXECUTED',
                'cash_position': self.cash_flow.get_cash_position(),
            })
            
            self.logger.info(f"SUCCESS: Order {order_id} placed and cash blocked")
            return True, "Order placed successfully", details
            
        except Exception as e:
            self.logger.error(f"Order placement failed: {str(e)}")
            return False, f"Order failed: {str(e)}", {}
    
    def place_delivery_sell_order(self, symbol: str, quantity: int, 
                                  price: float, enable_tpin: bool = False) -> Tuple[bool, str, Dict]:
        """
        Place a delivery sell order
        
        Key Points:
        - Cash received T+2 (or T+0 if TPIN enabled)
        - Doesn't block capital
        - Validates you have shares to sell (position_tracker)
        
        Args:
            enable_tpin: Set True for T+0 settlement with TPIN
        
        Returns:
            (success, message, details)
        """
        self.logger.info(f"=== DELIVERY SELL: {symbol} {quantity}@₹{price} (TPIN={enable_tpin}) ===")
        
        # STEP 1: Validate shares available
        can_sell, reason, details = self.cash_flow.can_sell_delivery(symbol, quantity, price)
        
        if not can_sell:
            self.logger.error(f"REJECTED: {reason}")
            return False, reason, details
        
        # STEP 2: Place order
        try:
            order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Record in cash flow
            txn_id = self.cash_flow.record_sell_delivery(
                order_id=order_id,
                symbol=symbol,
                quantity=quantity,
                price=price,
                enable_tpin=enable_tpin
            )
            
            settlement_type = "T+0 (TPIN)" if enable_tpin else "T+2"
            details.update({
                'order_id': order_id,
                'transaction_id': txn_id,
                'status': 'EXECUTED',
                'settlement_type': settlement_type,
                'cash_position': self.cash_flow.get_cash_position(),
            })
            
            self.logger.info(f"SUCCESS: Sold {quantity} shares | Settlement: {settlement_type}")
            return True, "Sell order placed successfully", details
            
        except Exception as e:
            self.logger.error(f"Sell order failed: {str(e)}")
            return False, f"Sell failed: {str(e)}", {}
    
    # =========================================================================
    # INTRADAY ORDERS (Margin-based)
    # =========================================================================
    
    def place_intraday_buy_order(self, symbol: str, quantity: int, 
                                 price: float) -> Tuple[bool, str, Dict]:
        """
        Place intraday buy order
        
        Key Differences from Delivery:
        - Blocks margin only (typically 25%)
        - Must be closed same day
        - Margin released EOD
        """
        self.logger.info(f"=== INTRADAY BUY: {symbol} {quantity}@₹{price} ===")
        
        gross_amount = quantity * price
        margin_required = gross_amount * 0.25
        
        if margin_required > self.cash_flow.available_cash:
            reason = f"Insufficient margin. Need ₹{margin_required:,.2f}, Have ₹{self.cash_flow.available_cash:,.2f}"
            return False, reason, {'required': margin_required, 'available': self.cash_flow.available_cash}
        
        try:
            order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
            txn_id = self.cash_flow.record_intraday_buy(
                order_id=order_id,
                symbol=symbol,
                quantity=quantity,
                price=price
            )
            
            return True, "Intraday order placed", {
                'order_id': order_id,
                'transaction_id': txn_id,
                'margin_blocked': round(margin_required, 2),
                'cash_position': self.cash_flow.get_cash_position(),
            }
        except Exception as e:
            return False, f"Order failed: {str(e)}", {}
    
    # =========================================================================
    # MONITORING & CONTROLS
    # =========================================================================
    
    def get_trading_status(self) -> Dict:
        """Get current trading status and limits"""
        cash_pos = self.cash_flow.get_cash_position()
        limits = self.cash_flow.validate_daily_limits()
        settlements = self.cash_flow.get_settlement_schedule()
        
        return {
            'cash_position': cash_pos,
            'daily_limits': limits,
            'settlement_schedule': settlements,
            'can_trade': limits['all_checks_pass'],
            'timestamp': datetime.now().isoformat(),
        }
    
    def check_margin_call(self) -> Tuple[bool, Dict]:
        """
        Check if margin call is triggered
        
        Returns:
            (margin_call_triggered, details)
        """
        limits = self.cash_flow.validate_daily_limits()
        
        margin_check = limits['checks']['margin_call']
        triggered = not margin_check['passed']
        
        return triggered, {
            'triggered': triggered,
            'utilization': margin_check['current'],
            'threshold': margin_check['limit'],
            'message': margin_check['message'],
        }
    
    def liquidate_positions_due_to_margin_call(self) -> Dict:
        """
        Emergency liquidation when margin call triggered
        
        In production, this would:
        1. Get all intraday positions
        2. Sell highest-loss positions first (minimize realized loss)
        3. Continue until margin utilization < threshold
        4. Log all transactions
        """
        self.logger.warning("⚠️ MARGIN CALL TRIGGERED - INITIATING LIQUIDATION")
        
        return {
            'status': 'NOT IMPLEMENTED',
            'message': 'Needs integration with position tracker and signal executor',
            'note': 'This would close positions to restore margin',
        }
    
    # =========================================================================
    # DAILY SETTLEMENT PROCESSING
    # =========================================================================
    
    def process_end_of_day(self) -> Dict:
        """
        Process end-of-day:
        1. Release intraday margins
        2. Update settlement schedule
        3. Generate EOD report
        """
        self.logger.info("=== PROCESSING END OF DAY ===")
        
        # In production, iterate through pending_settlements and release intraday margins
        eod_report = {
            'timestamp': datetime.now().isoformat(),
            'cash_position_before': self.cash_flow.get_cash_position(),
            'intraday_margins_released': 0.0,
            'settlements_processed': 0,
            'cash_position_after': self.cash_flow.get_cash_position(),
        }
        
        self.logger.info("=== EOD PROCESSING COMPLETE ===")
        return eod_report
    
    def process_settlement_date(self, settlement_date: str) -> Dict:
        """
        Process settlements for a specific date
        
        Called when T+2 date is reached
        """
        self.logger.info(f"Processing settlements for {settlement_date}")
        
        # Would iterate through pending_settlements and call process_settlement
        return {
            'settlement_date': settlement_date,
            'processed': 0,
            'remaining': len(self.cash_flow.pending_settlements),
        }


# =========================================================================
# EXAMPLE USAGE & SCENARIOS
# =========================================================================

def example_production_trading():
    """
    Example of how this would work in production
    """
    
    # Initialize
    cash_flow = CashFlowManager(
        initial_capital=100000,  # ₹1,00,000
        config={
            'brokerage_rate': 0.001,
            'tax_rate': 0.0001,
            'settlement_days': 2,
            'enable_tpin': False,  # Use T+2 by default
        }
    )
    
    # Create enhanced order manager
    from app.services.order_manager import OrderManager
    order_mgr = OrderManager()  # Your existing order manager
    enhanced_mgr = OrderManagerWithCashFlow(order_mgr, cash_flow)
    
    # ===== SCENARIO 1: Normal Delivery Buy =====
    print("\n📊 SCENARIO 1: Buy delivery order")
    success, msg, details = enhanced_mgr.place_delivery_buy_order(
        symbol='RELIANCE',
        quantity=10,
        price=2500.0,
        order_type='MARKET'
    )
    print(f"Result: {success} - {msg}")
    if success:
        print(f"  Blocked: ₹{details['total_cost']:,.2f}")
        print(f"  Settlement: {details['approved']}")
    
    # ===== SCENARIO 2: Check cash position =====
    print("\n💰 SCENARIO 2: Current cash position")
    status = enhanced_mgr.get_trading_status()
    pos = status['cash_position']
    print(f"  Available: ₹{pos['available_cash']:,.2f}")
    print(f"  Blocked: ₹{pos['blocked_cash']:,.2f}")
    print(f"  Pending (T+2): ₹{pos['pending_cash']:,.2f}")
    print(f"  Total Capital: ₹{pos['initial_capital']:,.2f}")
    
    # ===== SCENARIO 3: Try to buy more (might fail) =====
    print("\n📊 SCENARIO 3: Try to buy more (might exceed limits)")
    success, msg, details = enhanced_mgr.place_delivery_buy_order(
        symbol='TCS',
        quantity=20,
        price=3500.0,
    )
    print(f"Result: {success} - {msg}")
    
    # ===== SCENARIO 4: Check settlement schedule =====
    print("\n📅 SCENARIO 4: Settlement schedule (what cash comes when)")
    status = enhanced_mgr.get_trading_status()
    for date, settlement in status['settlement_schedule'].items():
        print(f"\n  Date: {date}")
        print(f"    Inflow: ₹{settlement['expected_inflow']:,.2f}")
        print(f"    Outflow: ₹{settlement['expected_outflow']:,.2f}")
        for txn in settlement['transactions'][:2]:  # Show first 2
            print(f"      - {txn['symbol']}: ₹{txn['amount']:,.2f}")
    
    # ===== SCENARIO 5: Margin call check =====
    print("\n⚠️  SCENARIO 5: Check for margin calls")
    triggered, margin_info = enhanced_mgr.check_margin_call()
    print(f"  Margin call triggered: {triggered}")
    print(f"  Utilization: {margin_info['utilization']:.2f}%")
    print(f"  Threshold: {margin_info['threshold']:.2f}%")
    
    # ===== SCENARIO 6: Export transaction history =====
    print("\n📁 SCENARIO 6: Export transactions")
    export_path = 'reports/cash_flow_history.json'
    cash_flow.export_transactions(export_path)
    print(f"  Exported to: {export_path}")


if __name__ == "__main__":
    example_production_trading()
