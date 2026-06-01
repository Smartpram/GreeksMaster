"""
CASH FLOW MANAGEMENT SYSTEM
===========================

Production-Grade Cash Flow Manager for NSE/BSE Trading
- Handles T+0 (Intraday) and T+2 (Delivery) Settlement
- Tracks Available vs Blocked vs Pending Cash
- Prevents Overdraft Scenarios
- Manages Margin Requirements
- Validates Available Funds for Order Execution

Real-World Scenarios Handled:
1. Delivery Buy (T+2): Cash blocked immediately, available T+2
2. Delivery Sell (T+2): Cash available T+2 (T+0 for TPIN enabled)
3. Intraday Short: Cash blocked for margin, released same day
4. Short Sale: Requires auction or corporate action handling
5. Margin Calls: Insufficient funds detection and prevention
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


class SettlementType(Enum):
    """Settlement cycle types in Indian Markets"""
    INTRADAY = "INTRADAY"      # T+0 (same day)
    DELIVERY = "DELIVERY"      # T+2 (2 business days)
    TPIN = "TPIN"             # T+0 (with TPIN - Delivery)


class TransactionType(Enum):
    """Types of cash flow transactions"""
    BUY_DELIVERY = "BUY_DELIVERY"          # Blocks cash T+0, Settled T+2
    SELL_DELIVERY = "SELL_DELIVERY"        # Receives cash T+2
    SELL_DELIVERY_TPIN = "SELL_DELIVERY_TPIN"  # Receives cash T+0 (with TPIN)
    BUY_INTRADAY = "BUY_INTRADAY"          # Blocks margin, released EOD
    SELL_INTRADAY = "SELL_INTRADAY"        # Delivers shares, releases EOD
    SHORT_SALE = "SHORT_SALE"              # Requires auction handling
    MARGIN_CALL = "MARGIN_CALL"            # Broker call for margin
    DIVIDEND = "DIVIDEND"                  # Dividend credit
    INTEREST = "INTEREST"                  # Interest on margin
    BROKERAGE = "BROKERAGE"                # Brokerage deduction
    TAXES = "TAXES"                        # Tax deduction


@dataclass
class CashFlowTransaction:
    """Individual cash flow transaction record"""
    transaction_id: str
    timestamp: datetime
    transaction_type: TransactionType
    settlement_type: SettlementType
    symbol: str
    quantity: int
    price: float
    gross_amount: float
    
    # Fees and charges
    brokerage: float = 0.0
    taxes: float = 0.0
    transaction_charges: float = 0.0
    net_amount: float = field(default=0.0, init=False)
    
    # Settlement details
    settlement_date: Optional[datetime] = None
    status: str = "PENDING"  # PENDING, BLOCKED, SETTLED, FAILED
    
    # Reference info
    order_id: Optional[str] = None
    trade_id: Optional[str] = None
    notes: str = ""
    
    def __post_init__(self):
        """Calculate net amount"""
        self.net_amount = self.gross_amount - (self.brokerage + self.taxes + self.transaction_charges)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'transaction_id': self.transaction_id,
            'timestamp': self.timestamp.isoformat(),
            'transaction_type': self.transaction_type.value,
            'settlement_type': self.settlement_type.value,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'price': self.price,
            'gross_amount': round(self.gross_amount, 2),
            'brokerage': round(self.brokerage, 2),
            'taxes': round(self.taxes, 2),
            'transaction_charges': round(self.transaction_charges, 2),
            'net_amount': round(self.net_amount, 2),
            'settlement_date': self.settlement_date.isoformat() if self.settlement_date else None,
            'status': self.status,
            'order_id': self.order_id,
            'trade_id': self.trade_id,
            'notes': self.notes
        }


class CashFlowManager:
    """
    Comprehensive Cash Flow Management for NSE/BSE Trading
    
    Key Concepts:
    - Available Cash: Can be used for new trades
    - Blocked Cash: Tied up in pending settlements
    - Pending Cash: Will be available at settlement
    - Reserved Cash: For margin/regulatory requirements
    """
    
    def __init__(self, initial_capital: float, config: Optional[Dict] = None):
        """
        Initialize Cash Flow Manager
        
        Args:
            initial_capital: Starting trading capital
            config: Configuration dictionary with:
                - brokerage_rate: % of transaction value
                - tax_rate: % for taxes
                - max_leverage: Maximum leverage allowed
                - settlement_days: T+N where N is days
                - enable_tpin: Allow T+0 delivery with TPIN
        """
        self.initial_capital = initial_capital
        self.cash_balance = initial_capital
        
        # Configuration
        self.config = config or self._default_config()
        
        # Cash tracking
        self.available_cash = initial_capital  # Can use for new trades
        self.blocked_cash = 0.0               # Tied up in pending trades
        self.pending_cash = 0.0               # Will be available at settlement
        self.reserved_cash = 0.0              # For margin requirements
        
        # Transaction history
        self.transactions: List[CashFlowTransaction] = []
        self.transaction_counter = 0
        
        # Settlement tracking
        self.pending_settlements: Dict[str, CashFlowTransaction] = {}  # By settlement_date
        self.settled_transactions: List[CashFlowTransaction] = []
        
        # Risk metrics
        self.max_daily_outflow = initial_capital * 0.3  # Don't spend > 30% daily
        self.daily_outflow = 0.0
        self.daily_outflow_date = datetime.now().date()
        
        logger.info(f"CashFlowManager initialized with capital: ₹{initial_capital:,.2f}")
    
    @staticmethod
    def _default_config() -> Dict:
        """Default configuration for NSE/BSE trading"""
        return {
            'brokerage_rate': 0.001,           # 0.1% = ₹10 per ₹10,000
            'tax_rate': 0.0001,                # 0.01% STT (varies by segment)
            'transaction_charges': 0.0000,     # Varies by exchange
            'max_leverage': 2.0,               # 2:1 leverage
            'settlement_days': 2,              # T+2
            'enable_tpin': False,              # Allow T+0 delivery
            'margin_call_threshold': 0.75,    # Call margin at 75% utilization
        }
    
    def can_buy_delivery(self, symbol: str, quantity: int, price: float) -> Tuple[bool, str, Dict]:
        """
        Check if we can buy delivery (blocks cash immediately)
        
        Validation:
        1. Sufficient available cash
        2. Not exceeding daily spending limits
        3. Not exceeding position concentration limits
        
        Returns:
            (can_buy, reason, details)
        """
        gross_amount = quantity * price
        total_cost = self._calculate_total_cost(gross_amount, TransactionType.BUY_DELIVERY)
        
        details = {
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'gross_amount': gross_amount,
            'total_cost': total_cost,
            'available_cash': self.available_cash,
            'blocked_cash': self.blocked_cash,
            'reserved_cash': self.reserved_cash,
        }
        
        # Check 1: Sufficient cash
        if total_cost > self.available_cash:
            reason = f"Insufficient funds. Need ₹{total_cost:,.2f}, Have ₹{self.available_cash:,.2f}"
            logger.warning(reason)
            return False, reason, details
        
        # Check 2: Daily spending limit
        if (self.daily_outflow + total_cost) > self.max_daily_outflow:
            reason = f"Exceeds daily limit. Today: ₹{self.daily_outflow:,.2f}, Limit: ₹{self.max_daily_outflow:,.2f}"
            logger.warning(reason)
            return False, reason, details
        
        # Check 3: Position concentration (max 10% per stock)
        max_position_value = self.initial_capital * 0.10
        if gross_amount > max_position_value:
            reason = f"Position too large. Max: ₹{max_position_value:,.2f}, Requested: ₹{gross_amount:,.2f}"
            logger.warning(reason)
            return False, reason, details
        
        details['approved'] = True
        return True, "Approved", details
    
    def can_sell_delivery(self, symbol: str, quantity: int, price: float) -> Tuple[bool, str, Dict]:
        """
        Check if we can sell delivery
        
        Note: For sell, cash availability is T+2 (or T+0 with TPIN)
        Main validation: Do we have the shares to sell?
        
        Returns:
            (can_sell, reason, details)
        """
        # This would check position_tracker for share availability
        # For now, just structural validation
        
        gross_amount = quantity * price
        details = {
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'gross_amount': gross_amount,
            'settlement_type': 'T+2 (or T+0 with TPIN)',
        }
        
        # In production, check with position tracker
        # if not position_tracker.has_shares(symbol, quantity):
        #     return False, "Insufficient shares", details
        
        return True, "Approved for sale", details
    
    def record_buy_delivery(self, order_id: str, symbol: str, quantity: int, 
                           price: float, brokerage: float = 0.0) -> str:
        """
        Record a delivery buy order
        
        Cash Flow:
        - T+0: Cash blocked (available_cash ↓, blocked_cash ↑)
        - T+2: Settlement (blocked_cash ↓, pending_settlements handled)
        
        Args:
            order_id: Order ID from exchange
            symbol: Stock symbol
            quantity: Number of shares
            price: Execution price
            brokerage: Brokerage paid
        
        Returns:
            transaction_id
        """
        gross_amount = quantity * price
        taxes = gross_amount * self.config['tax_rate']
        transaction_charges = gross_amount * self.config['transaction_charges']
        
        if brokerage == 0:
            brokerage = gross_amount * self.config['brokerage_rate']
        
        total_cost = gross_amount + brokerage + taxes + transaction_charges
        
        # Calculate settlement date (T+2 business days)
        settlement_date = self._calculate_settlement_date(datetime.now(), 2)
        
        # Create transaction record
        txn = CashFlowTransaction(
            transaction_id=self._generate_transaction_id(),
            timestamp=datetime.now(),
            transaction_type=TransactionType.BUY_DELIVERY,
            settlement_type=SettlementType.DELIVERY,
            symbol=symbol,
            quantity=quantity,
            price=price,
            gross_amount=gross_amount,
            brokerage=brokerage,
            taxes=taxes,
            transaction_charges=transaction_charges,
            settlement_date=settlement_date,
            status="BLOCKED",  # Cash is blocked
            order_id=order_id,
        )
        
        # Update cash flows
        self.available_cash -= total_cost
        self.blocked_cash += total_cost
        self.daily_outflow += total_cost
        
        # Record transaction
        self.transactions.append(txn)
        self.pending_settlements[txn.transaction_id] = txn
        
        logger.info(f"BUY DELIVERY recorded: {symbol} {quantity}@₹{price} | "
                   f"Cost: ₹{total_cost:,.2f} | Settlement: {settlement_date.date()}")
        
        return txn.transaction_id
    
    def record_sell_delivery(self, order_id: str, symbol: str, quantity: int, 
                            price: float, brokerage: float = 0.0, 
                            enable_tpin: bool = None) -> str:
        """
        Record a delivery sell order
        
        Cash Flow:
        - T+0: Order executed (no cash impact yet)
        - T+2: Settlement - Cash credited (pending_cash ↑)
        - T+0: If TPIN enabled (pending_cash ↑ immediately)
        
        Args:
            order_id: Order ID from exchange
            symbol: Stock symbol
            quantity: Number of shares sold
            price: Execution price
            brokerage: Brokerage paid
            enable_tpin: Override TPIN setting
        
        Returns:
            transaction_id
        """
        if enable_tpin is None:
            enable_tpin = self.config.get('enable_tpin', False)
        
        gross_amount = quantity * price
        taxes = gross_amount * self.config['tax_rate']
        transaction_charges = gross_amount * self.config['transaction_charges']
        
        if brokerage == 0:
            brokerage = gross_amount * self.config['brokerage_rate']
        
        net_proceeds = gross_amount - brokerage - taxes - transaction_charges
        
        # Settlement date
        settlement_days = 0 if enable_tpin else 2
        settlement_date = self._calculate_settlement_date(datetime.now(), settlement_days)
        settlement_type = SettlementType.TPIN if enable_tpin else SettlementType.DELIVERY
        
        # Create transaction
        txn = CashFlowTransaction(
            transaction_id=self._generate_transaction_id(),
            timestamp=datetime.now(),
            transaction_type=TransactionType.SELL_DELIVERY_TPIN if enable_tpin else TransactionType.SELL_DELIVERY,
            settlement_type=settlement_type,
            symbol=symbol,
            quantity=quantity,
            price=price,
            gross_amount=gross_amount,
            brokerage=brokerage,
            taxes=taxes,
            transaction_charges=transaction_charges,
            settlement_date=settlement_date,
            status="PENDING" if not enable_tpin else "SETTLED",
            order_id=order_id,
        )
        
        # Update cash flows
        if enable_tpin:
            # T+0 with TPIN - Cash immediately available
            self.available_cash += net_proceeds
            self.cash_balance += net_proceeds
        else:
            # T+2 - Cash pending settlement
            self.pending_cash += net_proceeds
        
        # Record transaction
        self.transactions.append(txn)
        self.pending_settlements[txn.transaction_id] = txn
        
        settlement_type_str = "T+0 (TPIN)" if enable_tpin else "T+2"
        logger.info(f"SELL DELIVERY recorded: {symbol} {quantity}@₹{price} | "
                   f"Proceeds: ₹{net_proceeds:,.2f} | Settlement: {settlement_type_str}")
        
        return txn.transaction_id
    
    def record_intraday_buy(self, order_id: str, symbol: str, quantity: int, 
                           price: float, brokerage: float = 0.0) -> str:
        """
        Record intraday buy (margin blocked, released EOD)
        
        Cash Flow:
        - T+0: Margin blocked (available_cash ↓, blocked_cash ↑)
        - EOD: Margin released (blocked_cash ↓, available_cash ↑)
        """
        gross_amount = quantity * price
        margin_required = gross_amount * 0.25  # 25% margin requirement (typical)
        
        if brokerage == 0:
            brokerage = gross_amount * self.config['brokerage_rate']
        
        total_cost = margin_required + brokerage
        
        # Settlement at EOD
        settlement_date = datetime.now().replace(hour=16, minute=0, second=0)
        
        txn = CashFlowTransaction(
            transaction_id=self._generate_transaction_id(),
            timestamp=datetime.now(),
            transaction_type=TransactionType.BUY_INTRADAY,
            settlement_type=SettlementType.INTRADAY,
            symbol=symbol,
            quantity=quantity,
            price=price,
            gross_amount=gross_amount,
            brokerage=brokerage,
            settlement_date=settlement_date,
            status="BLOCKED",
            order_id=order_id,
        )
        
        self.available_cash -= total_cost
        self.blocked_cash += total_cost
        self.daily_outflow += total_cost
        
        self.transactions.append(txn)
        self.pending_settlements[txn.transaction_id] = txn
        
        logger.info(f"INTRADAY BUY recorded: {symbol} {quantity}@₹{price} | "
                   f"Margin: ₹{total_cost:,.2f} | Released EOD")
        
        return txn.transaction_id
    
    def process_settlement(self, transaction_id: str) -> Tuple[bool, str]:
        """
        Process settlement of a pending transaction
        
        Called when T+2 date is reached or trades are closed
        
        Returns:
            (success, message)
        """
        if transaction_id not in self.pending_settlements:
            return False, f"Transaction {transaction_id} not found in pending settlements"
        
        txn = self.pending_settlements[transaction_id]
        
        if txn.transaction_type in [TransactionType.BUY_DELIVERY]:
            # Buy settlement - convert blocked to settled
            # Release full amount that was blocked (gross + fees)
            total_blocked = txn.gross_amount + txn.brokerage + txn.taxes + txn.transaction_charges
            self.blocked_cash -= total_blocked
            # Shares are now owned (tracked separately in position tracker)
            
        elif txn.transaction_type in [TransactionType.SELL_DELIVERY]:
            # Sell settlement - move pending to available
            self.pending_cash -= txn.net_amount
            self.available_cash += txn.net_amount
            self.cash_balance += txn.net_amount
        
        elif txn.transaction_type == TransactionType.BUY_INTRADAY:
            # EOD settlement - release margin
            total_margin = txn.gross_amount * 0.25 + txn.brokerage
            self.blocked_cash -= total_margin
            self.available_cash += total_margin
        
        txn.status = "SETTLED"
        self.settled_transactions.append(txn)
        del self.pending_settlements[transaction_id]
        
        logger.info(f"Settlement processed: {transaction_id} | {txn.symbol}")
        return True, f"Settlement processed for {txn.transaction_id}"
    
    def get_cash_position(self) -> Dict:
        """
        Get current cash position snapshot
        
        Returns comprehensive cash breakdown
        """
        # Reset daily counter if date changed
        if datetime.now().date() != self.daily_outflow_date:
            self.daily_outflow = 0.0
            self.daily_outflow_date = datetime.now().date()
        
        utilization = (self.blocked_cash + self.reserved_cash) / self.initial_capital
        margin_call_triggered = utilization >= self.config['margin_call_threshold']
        
        return {
            'timestamp': datetime.now().isoformat(),
            'initial_capital': round(self.initial_capital, 2),
            'cash_balance': round(self.cash_balance, 2),
            'available_cash': round(self.available_cash, 2),
            'blocked_cash': round(self.blocked_cash, 2),
            'pending_cash': round(self.pending_cash, 2),
            'reserved_cash': round(self.reserved_cash, 2),
            'total_committed': round(self.blocked_cash + self.pending_cash + self.reserved_cash, 2),
            'free_capital': round(self.available_cash - self.reserved_cash, 2),
            'utilization_percent': round(utilization * 100, 2),
            'daily_outflow': round(self.daily_outflow, 2),
            'daily_limit': round(self.max_daily_outflow, 2),
            'daily_remaining': round(self.max_daily_outflow - self.daily_outflow, 2),
            'margin_call_threshold': round(self.config['margin_call_threshold'] * 100, 2),
            'margin_call_triggered': margin_call_triggered,
            'pending_settlements_count': len(self.pending_settlements),
        }
    
    def get_settlement_schedule(self) -> Dict:
        """
        Get settlement schedule for pending transactions
        
        Returns settlements grouped by date
        """
        schedule = {}
        for txn_id, txn in self.pending_settlements.items():
            date_key = txn.settlement_date.date().isoformat()
            
            if date_key not in schedule:
                schedule[date_key] = {
                    'date': date_key,
                    'expected_inflow': 0.0,
                    'expected_outflow': 0.0,
                    'transactions': []
                }
            
            if txn.transaction_type == TransactionType.SELL_DELIVERY:
                schedule[date_key]['expected_inflow'] += txn.net_amount
            else:
                schedule[date_key]['expected_outflow'] += txn.net_amount
            
            schedule[date_key]['transactions'].append({
                'txn_id': txn.transaction_id,
                'symbol': txn.symbol,
                'type': txn.transaction_type.value,
                'amount': round(txn.net_amount, 2),
            })
        
        return schedule
    
    def validate_daily_limits(self) -> Dict:
        """
        Validate current position against all limits
        
        Returns: {
            'all_checks_pass': bool,
            'checks': {check_name: {passed, current, limit, message}}
        }
        """
        checks = {}
        
        # Check 1: Daily outflow limit
        daily_remaining = self.max_daily_outflow - self.daily_outflow
        checks['daily_limit'] = {
            'passed': daily_remaining >= 0,
            'current': round(self.daily_outflow, 2),
            'limit': round(self.max_daily_outflow, 2),
            'remaining': round(max(0, daily_remaining), 2),
            'message': f"Daily outflow: ₹{self.daily_outflow:,.2f} / ₹{self.max_daily_outflow:,.2f}"
        }
        
        # Check 2: Available cash
        checks['cash_available'] = {
            'passed': self.available_cash > 0,
            'current': round(self.available_cash, 2),
            'limit': 0.0,
            'message': f"Available cash: ₹{self.available_cash:,.2f}"
        }
        
        # Check 3: Margin utilization
        utilization = (self.blocked_cash + self.reserved_cash) / self.initial_capital
        checks['margin_call'] = {
            'passed': utilization < self.config['margin_call_threshold'],
            'current': round(utilization * 100, 2),
            'limit': round(self.config['margin_call_threshold'] * 100, 2),
            'message': f"Capital utilization: {utilization*100:.2f}%"
        }
        
        # Check 4: Pending settlements
        checks['settlement_risk'] = {
            'passed': len(self.pending_settlements) <= 50,  # Arbitrary limit
            'current': len(self.pending_settlements),
            'limit': 50,
            'message': f"Pending settlements: {len(self.pending_settlements)}"
        }
        
        all_pass = all(check['passed'] for check in checks.values())
        
        return {
            'all_checks_pass': all_pass,
            'checks': checks,
            'timestamp': datetime.now().isoformat(),
        }
    
    def export_transactions(self, filepath: str):
        """Export transaction history to JSON"""
        export_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'initial_capital': self.initial_capital,
                'current_cash_position': self.get_cash_position(),
            },
            'transactions': [txn.to_dict() for txn in self.transactions],
            'pending_settlements': {k: v.to_dict() for k, v in self.pending_settlements.items()},
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Transactions exported to {filepath}")
    
    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        self.transaction_counter += 1
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"TXN{timestamp}{self.transaction_counter:06d}"
    
    def _calculate_total_cost(self, gross_amount: float, txn_type: TransactionType) -> float:
        """Calculate total cost including fees"""
        brokerage = gross_amount * self.config['brokerage_rate']
        taxes = gross_amount * self.config['tax_rate']
        transaction_charges = gross_amount * self.config['transaction_charges']
        
        return gross_amount + brokerage + taxes + transaction_charges
    
    @staticmethod
    def _calculate_settlement_date(start_date: datetime, business_days: int) -> datetime:
        """
        Calculate settlement date (T+N business days, excluding weekends)
        
        Note: In production, also exclude holidays using NSE holiday calendar
        """
        if business_days == 0:
            return start_date
        
        current = start_date
        days_added = 0
        
        while days_added < business_days:
            current += timedelta(days=1)
            # Skip weekends (5=Saturday, 6=Sunday)
            if current.weekday() < 5:
                days_added += 1
        
        return current
