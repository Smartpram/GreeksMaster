"""
CASH FLOW MANAGER TEST SUITE
=============================

Tests for the CashFlowManager with real-world scenarios
Run this to validate cash flow management before production
"""

import logging
import sys
from datetime import datetime, timedelta
from app.services.cash_flow_manager import (
    CashFlowManager, TransactionType, SettlementType
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app/logs/cash_flow_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class CashFlowTest:
    """Test suite for CashFlowManager"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.total = 0
    
    def run_all_tests(self):
        """Run all test scenarios"""
        logger.info("="*80)
        logger.info("CASH FLOW MANAGER TEST SUITE")
        logger.info("="*80)
        
        tests = [
            ("Test 1: Initialize with capital", self.test_initialization),
            ("Test 2: Successful delivery buy", self.test_delivery_buy_success),
            ("Test 3: Reject over-limit buy", self.test_delivery_buy_reject_insufficient),
            ("Test 4: Reject daily limit buy", self.test_delivery_buy_reject_daily_limit),
            ("Test 5: Record delivery sell", self.test_delivery_sell),
            ("Test 6: Intraday buy with margin", self.test_intraday_buy),
            ("Test 7: Cash position snapshot", self.test_cash_position),
            ("Test 8: Settlement schedule", self.test_settlement_schedule),
            ("Test 9: Validate daily limits", self.test_validate_limits),
            ("Test 10: Real scenario - Monday buying spree", self.test_scenario_monday),
            ("Test 11: Real scenario - T+2 settlement", self.test_scenario_settlement),
            ("Test 12: Real scenario - Margin call", self.test_scenario_margin_call),
        ]
        
        for test_name, test_func in tests:
            self.total += 1
            try:
                logger.info(f"\n{'='*80}")
                logger.info(f"▶ {test_name}")
                logger.info(f"{'='*80}")
                test_func()
                self.passed += 1
                logger.info(f"✅ PASSED: {test_name}")
            except AssertionError as e:
                self.failed += 1
                logger.error(f"❌ FAILED: {test_name}")
                logger.error(f"   Error: {str(e)}")
            except Exception as e:
                self.failed += 1
                logger.error(f"❌ ERROR: {test_name}")
                logger.error(f"   Exception: {str(e)}")
        
        self.print_summary()
    
    def test_initialization(self):
        """Test 1: Initialize CashFlowManager"""
        cf = CashFlowManager(initial_capital=100000)
        
        assert cf.initial_capital == 100000, "Initial capital not set"
        assert cf.available_cash == 100000, "Available cash should equal initial capital"
        assert cf.blocked_cash == 0, "Blocked cash should be 0"
        assert cf.pending_cash == 0, "Pending cash should be 0"
        
        logger.info(f"  ✓ Initial capital: ₹{cf.initial_capital:,.2f}")
        logger.info(f"  ✓ Available cash: ₹{cf.available_cash:,.2f}")
    
    def test_delivery_buy_success(self):
        """Test 2: Successful delivery buy"""
        cf = CashFlowManager(initial_capital=100000)
        
        # Should be able to buy (within 10% limit = ₹10,000)
        can_buy, reason, details = cf.can_buy_delivery('RELIANCE', 4, 2500)  # ₹10,000
        assert can_buy, f"Should be able to buy: {reason}"
        
        # Record the buy
        txn_id = cf.record_buy_delivery(
            order_id='ORD001',
            symbol='RELIANCE',
            quantity=4,
            price=2500
        )
        
        # Check cash blocked
        cost = 4 * 2500 * 1.001  # qty * price * (1 + brokerage)
        assert cf.blocked_cash > 0, "Cash should be blocked"
        assert cf.available_cash < 100000, "Available cash should decrease"
        
        logger.info(f"  ✓ Transaction ID: {txn_id}")
        logger.info(f"  ✓ Cost: ₹{cost:,.2f}")
        logger.info(f"  ✓ Blocked: ₹{cf.blocked_cash:,.2f}")
        logger.info(f"  ✓ Available: ₹{cf.available_cash:,.2f}")
    
    def test_delivery_buy_reject_insufficient(self):
        """Test 3: Reject buy if insufficient funds"""
        cf = CashFlowManager(initial_capital=10000)  # Small capital
        
        # Try to buy something expensive
        can_buy, reason, details = cf.can_buy_delivery('TCS', 10, 3500)
        assert not can_buy, "Should reject due to insufficient funds"
        assert "Insufficient funds" in reason, f"Wrong reason: {reason}"
        
        logger.info(f"  ✓ Correctly rejected: {reason}")
        logger.info(f"  ✓ Required: ₹{details['total_cost']:,.2f}")
        logger.info(f"  ✓ Available: ₹{details['available_cash']:,.2f}")
    
    def test_delivery_buy_reject_daily_limit(self):
        """Test 4: Reject buy if exceeds daily limit"""
        cf = CashFlowManager(initial_capital=100000)
        cf.max_daily_outflow = 20000  # Max ₹20,000/day
        
        # First buy: ₹9,000 (OK, within 10% position limit)
        success, reason, details = cf.can_buy_delivery('RELIANCE', 3, 3000)  # 3 * 3000 = 9000
        assert success, "First buy should succeed"
        cf.record_buy_delivery('ORD001', 'RELIANCE', 3, 3000)
        
        # Second buy: ₹6,000 (OK, total ~15,000)
        success, reason, details = cf.can_buy_delivery('TCS', 2, 3000)  # 2 * 3000 = 6000
        if success:
            cf.record_buy_delivery('ORD002', 'TCS', 2, 3000)
        
        # Third buy: ₹10,000 (should fail - total would exceed 20,000)
        success, reason, details = cf.can_buy_delivery('INFY', 2, 5000)  # 2 * 5000 = 10,000 (exceeds limit)
        assert not success, "Third buy should exceed daily limit"
        assert "daily limit" in reason.lower(), f"Wrong reason: {reason}"
        
        logger.info(f"  ✓ Daily limit: ₹{cf.max_daily_outflow:,.2f}")
        logger.info(f"  ✓ Already used: ₹{cf.daily_outflow:,.2f}")
        logger.info(f"  ✓ Correctly rejected: {reason}")
    
    def test_delivery_sell(self):
        """Test 5: Record delivery sell"""
        cf = CashFlowManager(initial_capital=100000)
        
        # First buy something
        cf.record_buy_delivery('ORD001', 'RELIANCE', 10, 2500)
        blocked_after_buy = cf.blocked_cash
        
        # Then sell it
        txn_id = cf.record_sell_delivery(
            order_id='ORD002',
            symbol='RELIANCE',
            quantity=10,
            price=2550,
            enable_tpin=False  # T+2 settlement
        )
        
        # Check pending cash
        assert cf.pending_cash > 0, "Pending cash should be > 0 after sell"
        
        logger.info(f"  ✓ Sell transaction ID: {txn_id}")
        logger.info(f"  ✓ Pending cash (arrives T+2): ₹{cf.pending_cash:,.2f}")
        logger.info(f"  ✓ Settlement date: T+2")
    
    def test_intraday_buy(self):
        """Test 6: Intraday buy with margin"""
        cf = CashFlowManager(initial_capital=100000)
        
        # Intraday requires 25% margin
        txn_id = cf.record_intraday_buy(
            order_id='ORD003',
            symbol='SBIN',
            quantity=20,
            price=500
        )
        
        margin_required = 20 * 500 * 0.25
        assert cf.blocked_cash > 0, "Margin should be blocked"
        assert cf.blocked_cash < margin_required * 1.1, "Margin blocked should be close to requirement"
        
        logger.info(f"  ✓ Intraday transaction ID: {txn_id}")
        logger.info(f"  ✓ Position value: ₹{20*500:,.2f}")
        logger.info(f"  ✓ Margin required: ₹{margin_required:,.2f}")
        logger.info(f"  ✓ Margin blocked: ₹{cf.blocked_cash:,.2f}")
        logger.info(f"  ✓ Released at: EOD")
    
    def test_cash_position(self):
        """Test 7: Get cash position snapshot"""
        cf = CashFlowManager(initial_capital=100000)
        
        # Make some transactions
        cf.record_buy_delivery('ORD001', 'RELIANCE', 10, 2500)
        cf.record_buy_delivery('ORD002', 'TCS', 5, 3000)
        cf.record_sell_delivery('ORD003', 'INFY', 8, 1800, enable_tpin=True)
        
        position = cf.get_cash_position()
        
        assert 'available_cash' in position, "Cash position missing available_cash"
        assert 'blocked_cash' in position, "Cash position missing blocked_cash"
        assert 'pending_cash' in position, "Cash position missing pending_cash"
        assert 'utilization_percent' in position, "Cash position missing utilization"
        
        logger.info(f"\n  Cash Position:")
        logger.info(f"  ├─ Total Capital: ₹{position['initial_capital']:,.2f}")
        logger.info(f"  ├─ Available: ₹{position['available_cash']:,.2f}")
        logger.info(f"  ├─ Blocked: ₹{position['blocked_cash']:,.2f}")
        logger.info(f"  ├─ Pending (T+2): ₹{position['pending_cash']:,.2f}")
        logger.info(f"  ├─ Reserved: ₹{position['reserved_cash']:,.2f}")
        logger.info(f"  └─ Utilization: {position['utilization_percent']:.2f}%")
    
    def test_settlement_schedule(self):
        """Test 8: Settlement schedule"""
        cf = CashFlowManager(initial_capital=100000)
        
        # Create transactions on different days
        cf.record_buy_delivery('ORD001', 'RELIANCE', 10, 2500)
        cf.record_sell_delivery('ORD002', 'TCS', 5, 3000)
        
        schedule = cf.get_settlement_schedule()
        
        assert len(schedule) > 0, "Settlement schedule should not be empty"
        
        logger.info(f"\n  Settlement Schedule:")
        for date, settlement in list(schedule.items())[:3]:  # Show first 3
            logger.info(f"  \n  📅 {date}")
            logger.info(f"  ├─ Expected Inflow: ₹{settlement['expected_inflow']:,.2f}")
            logger.info(f"  └─ Expected Outflow: ₹{settlement['expected_outflow']:,.2f}")
    
    def test_validate_limits(self):
        """Test 9: Validate daily limits"""
        cf = CashFlowManager(initial_capital=100000)
        cf.max_daily_outflow = 30000
        
        # Make some transactions
        cf.record_buy_delivery('ORD001', 'RELIANCE', 5, 2500)
        
        limits = cf.validate_daily_limits()
        
        assert 'all_checks_pass' in limits, "Missing all_checks_pass"
        assert 'checks' in limits, "Missing checks"
        
        logger.info(f"\n  Validation Results:")
        for check_name, check in limits['checks'].items():
            status = "✅ PASS" if check['passed'] else "❌ FAIL"
            logger.info(f"  {status}: {check_name}")
            logger.info(f"       └─ {check['message']}")
    
    def test_scenario_monday(self):
        """Test 10: Real scenario - Monday buying spree"""
        logger.info("\n  Scenario: Moderate buying on Monday")
        
        cf = CashFlowManager(initial_capital=100000)
        
        # 9:15 AM: Buy RELIANCE (within 10% limit)
        success1, msg1, det1 = cf.can_buy_delivery('RELIANCE', 3, 2500)  # ₹7,500
        logger.info(f"  9:15 AM: Buy RELIANCE - {success1}")
        if success1:
            cf.record_buy_delivery('ORD001', 'RELIANCE', 3, 2500)
        else:
            logger.info(f"         Reason: {msg1}")
        
        # 9:30 AM: Buy TCS (within limits)
        success2, msg2, det2 = cf.can_buy_delivery('TCS', 2, 3000)  # ₹6,000
        logger.info(f"  9:30 AM: Buy TCS - {success2}")
        if success2:
            cf.record_buy_delivery('ORD002', 'TCS', 2, 3000)
        else:
            logger.info(f"         Reason: {msg2}")
        
        # 9:45 AM: Try to buy INFY (within limits)
        success3, msg3, det3 = cf.can_buy_delivery('INFY', 5, 1800)  # ₹9,000
        logger.info(f"  9:45 AM: Buy INFY - {success3}")
        if success3:
            cf.record_buy_delivery('ORD003', 'INFY', 5, 1800)
        else:
            logger.info(f"         Reason: {msg3}")
        
        pos = cf.get_cash_position()
        logger.info(f"\n  End of day:")
        logger.info(f"  └─ Available: ₹{pos['available_cash']:,.2f}")
        logger.info(f"  └─ Blocked: ₹{pos['blocked_cash']:,.2f}")
        
        # First buy should definitely succeed since it's well within limits
        assert success1, f"First buy should succeed, reason: {msg1}"
        assert pos['available_cash'] >= 0, "Available cash should never be negative"
    
    def test_scenario_settlement(self):
        """Test 11: Real scenario - T+2 settlement"""
        logger.info("\n  Scenario: Monday buy → Wednesday settlement")
        
        cf = CashFlowManager(initial_capital=100000)
        
        # Monday: Buy
        logger.info("  Monday (T+0): Buy ₹50,000 worth")
        txn_id = cf.record_buy_delivery('ORD001', 'RELIANCE', 20, 2500)
        pos_monday = cf.get_cash_position()
        logger.info(f"    Available: ₹{pos_monday['available_cash']:,.2f}")
        logger.info(f"    Blocked: ₹{pos_monday['blocked_cash']:,.2f}")
        
        # Verify blocked cash is set
        blocked_before = pos_monday['blocked_cash']
        assert blocked_before > 0, "Blocked cash should be > 0 after buy"
        
        # Wednesday: Settlement
        logger.info("  Wednesday (T+2): Settlement processed")
        success, msg = cf.process_settlement(txn_id)
        assert success, f"Settlement should succeed: {msg}"
        
        pos_wednesday = cf.get_cash_position()
        logger.info(f"    Available: ₹{pos_wednesday['available_cash']:,.2f}")
        logger.info(f"    Blocked: ₹{pos_wednesday['blocked_cash']:,.2f}")
        logger.info(f"    Settlement processed: {txn_id} | RELIANCE")
        
        # After settlement, blocked cash for this transaction should be cleared
        assert pos_wednesday['blocked_cash'] == 0, f"Blocked cash should be 0 after settlement, but got {pos_wednesday['blocked_cash']}"
    
    def test_scenario_margin_call(self):
        """Test 12: Real scenario - Margin call trigger"""
        logger.info("\n  Scenario: Heavy buying triggers margin call")
        
        cf = CashFlowManager(initial_capital=100000)
        
        # Set low threshold for testing
        cf.config['margin_call_threshold'] = 0.5  # 50% utilization
        
        # Buy heavily
        logger.info("  Heavy buying to trigger margin call...")
        cf.record_buy_delivery('ORD001', 'RELIANCE', 10, 2500)
        cf.record_buy_delivery('ORD002', 'TCS', 10, 3000)
        cf.record_buy_delivery('ORD003', 'INFY', 10, 1800)
        
        limits = cf.validate_daily_limits()
        margin_check = limits['checks']['margin_call']
        
        logger.info(f"  Margin utilization: {margin_check['current']:.2f}%")
        logger.info(f"  Threshold: {margin_check['limit']:.2f}%")
        logger.info(f"  Margin call: {'YES ⚠️' if not margin_check['passed'] else 'NO'}")
        
        if not margin_check['passed']:
            logger.warning(f"  ⚠️ {margin_check['message']}")
    
    def print_summary(self):
        """Print test summary"""
        logger.info(f"\n{'='*80}")
        logger.info(f"TEST SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"Total: {self.total}")
        logger.info(f"Passed: {self.passed} ✅")
        logger.info(f"Failed: {self.failed} ❌")
        
        if self.failed == 0:
            logger.info(f"\n🎉 ALL TESTS PASSED!")
            logger.info(f"Cash Flow Manager is ready for production use.")
        else:
            logger.info(f"\n⚠️ {self.failed} test(s) failed")
            logger.info(f"Review errors above and fix before deployment.")
        
        logger.info(f"{'='*80}\n")


if __name__ == "__main__":
    test = CashFlowTest()
    test.run_all_tests()
