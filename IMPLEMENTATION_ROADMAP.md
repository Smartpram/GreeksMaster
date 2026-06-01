# 🚀 Trading System Implementation Roadmap

**Status**: Ready for Implementation  
**Date**: June 1, 2026  
**Target**: Complete production-ready trading system  

---

## Executive Summary

MyBreezeApp is an **algorithmic trading system** built on a **5-stage decision pipeline**. This document outlines how to implement the complete trading system from components already in place.

### System Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRADING SYSTEM WORKFLOW                       │
└─────────────────────────────────────────────────────────────────┘

[STAGE 1: SIGNAL GENERATION]
├── Module: app/strategies/buy_hold_trend.py
├── Purpose: Scan market for entry opportunities
├── Scans OHLCV data for trend-following setups
└── Output: BuySignal (symbol, price, timestamp, indicators)
           ↓
[STAGE 2: VALIDATION & GUARDRAILS]
├── Modules:
│   ├── app/strategies/production_validator.py (Config checks)
│   ├── app/strategies/regime_monitor.py (Market classification)
│   └── app/strategies/unified_profit_booking.py (Exit strategy selection)
├── Purpose: Ensure signal is safe to trade
├── Checks: Configuration validity, market regime, appropriate exit method
└── Output: ValidationResult (approved? which exit strategy?)
           ↓
[STAGE 3: TRADE EXECUTION]
├── Modules:
│   ├── app/services/order_manager.py (Order placement)
│   ├── app/services/breeze_api.py (API integration)
│   └── app/services/risk_manager.py (Risk checks)
├── Purpose: Place orders with intelligent sizing
├── Enforces: Position size limits, stop-loss placement, risk checks
└── Output: Order (quantity, type, price, status)
           ↓
[STAGE 4: EXIT & POSITION MANAGEMENT]
├── Module: app/strategies/profit_booking_manager.py
├── Purpose: Monitor positions and execute exits
├── Strategies:
│   ├── Fixed Full Exit (100% exit at target)
│   └── Partial + Trailing (50% target + 50% trailing)
└── Output: Trade (entry→exit with P&L)
           ↓
[STAGE 5: RISK MONITORING & FEEDBACK]
├── Modules:
│   ├── app/services/risk_manager.py (Daily P&L, position limits)
│   ├── app/services/live_position_tracker.py (Portfolio status)
│   └── app/services/notifications.py (Alerts)
├── Purpose: Monitor portfolio health, feedback to Stage 2
├── Tracks: Daily P&L, drawdown, position count, regime changes
└── Feedback: ↑ Influences future signal acceptance
```

---

## 🎯 Phase 1: Core Trading Pipeline (Weeks 1-2)

### Goal
Establish end-to-end signal-to-trade execution.

### Task 1.1: Stage 1 - Signal Generation Implementation
**File**: `app/strategies/buy_hold_trend.py`  
**Current Status**: ✅ Exists, needs review  
**Time Estimate**: 4 hours

**Deliverable**:
```python
class BuyHoldTrendStrategy:
    def __init__(self, config: dict):
        # Initialize with configuration
        pass
    
    def scan_market(self, symbol: str, ohlcv_data: pd.DataFrame) -> Optional[BuySignal]:
        """
        Scan for buy signal based on:
        1. Price above 20-period MA (uptrend check)
        2. RSI between 40-80 (momentum validation)
        3. Volume confirmation (optional: volume > 20-day avg)
        
        Returns BuySignal or None
        """
        pass
    
    def calculate_indicators(self, ohlcv_data: pd.DataFrame) -> dict:
        """Calculate MA, RSI, volume indicators"""
        pass
```

**Acceptance Criteria**:
- ✅ Correctly identifies uptrend (price > MA)
- ✅ RSI calculation accurate
- ✅ BuySignal generated with required fields
- ✅ No signals during downtrend
- ✅ Handles missing data gracefully

**Testing**:
```python
# Test with historical data
test_data = load_csv('test_data/TCS_2024.csv')
strategy = BuyHoldTrendStrategy(config)
signals = []
for i in range(20, len(test_data)):
    signal = strategy.scan_market('TCS', test_data[:i])
    if signal:
        signals.append(signal)
assert len(signals) > 0  # Should find some signals
```

---

### Task 1.2: Stage 2 - Validation Layer Implementation
**Files**:
- `app/strategies/production_validator.py`
- `app/strategies/regime_monitor.py`

**Time Estimate**: 6 hours

**Deliverable - Production Validator**:
```python
class ProductionValidator:
    @staticmethod
    def validate_config(config: dict) -> Tuple[bool, List[str]]:
        """
        Check configuration safety:
        1. MAX_POSITION_SIZE exists and > 0
        2. DAILY_LOSS_LIMIT exists and > 0
        3. TARGET_PROFIT_PCT is reasonable (5-20%)
        4. STOP_LOSS_PCT is reasonable (1-5%)
        5. MA_PERIOD, RSI_PERIOD valid
        
        Returns (is_valid, error_messages)
        """
        pass
    
    @staticmethod
    def validate_signal(signal: BuySignal, config: dict) -> Tuple[bool, List[str]]:
        """
        Check signal safety:
        1. Entry price > 0
        2. Timestamp not too old
        3. Indicators present and reasonable
        4. Symbol in trading list
        
        Returns (is_valid, error_messages)
        """
        pass
```

**Deliverable - Regime Monitor**:
```python
class RegimeMonitor:
    @staticmethod
    def classify_regime(ohlcv_data: pd.DataFrame) -> Regime:
        """
        Classify market as TRENDING or MEAN_REVERTING:
        
        TRENDING if:
        - ADX > 25 (strong trend)
        - Price making higher highs or lower lows
        - Applies to: Multi-day moves, partial + trailing exit
        
        MEAN_REVERTING if:
        - ADX < 20 (range-bound)
        - Price oscillating within range
        - Applies to: Intraday bounces, fixed full exit
        
        Returns Regime enum
        """
        pass
    
    @staticmethod
    def select_exit_strategy(regime: Regime) -> str:
        """
        Map regime to exit strategy:
        - TRENDING → "partial_trailing" (50% profit, 50% trailing)
        - MEAN_REVERTING → "fixed_full" (100% at target)
        
        Returns strategy name
        """
        pass
```

**Acceptance Criteria**:
- ✅ All config errors caught
- ✅ Regime classification matches manual inspection
- ✅ Exit strategy selection consistent
- ✅ No false positives (valid configs rejected)
- ✅ Clear error messages for debugging

**Testing**:
```python
# Test bad config
bad_config = {'MAX_POSITION_SIZE': -100}
valid, errors = ProductionValidator.validate_config(bad_config)
assert not valid and len(errors) > 0

# Test regime classification
trending_data = load_csv('test_data/trending_market.csv')
regime = RegimeMonitor.classify_regime(trending_data)
assert regime == Regime.TRENDING
```

---

### Task 1.3: Stage 3 - Order Execution Implementation
**Files**:
- `app/services/order_manager.py`
- `app/services/breeze_api.py`
- `app/services/risk_manager.py`

**Time Estimate**: 8 hours

**Deliverable - Order Manager**:
```python
class OrderManager:
    def __init__(self, breeze_client, config: dict):
        self.breeze = breeze_client
        self.config = config
        self.orders = []
    
    def place_market_order(self, symbol: str, quantity: int, side: str) -> Order:
        """
        Place market order via Breeze API.
        
        Args:
            symbol: Stock symbol (e.g., 'TCS')
            quantity: Shares to buy
            side: 'BUY' or 'SELL'
        
        Returns:
            Order with order_id, status, fill_price
        
        Raises:
            InsufficientFundsError: If buying would exceed account value
            RiskViolationError: If position size exceeds limits
        """
        pass
    
    def place_limit_order(self, symbol: str, quantity: int, price: float, side: str) -> Order:
        """Place limit order for stop-loss / profit target"""
        pass
    
    def place_stop_loss_order(self, symbol: str, quantity: int, stop_price: float) -> Order:
        """Place stop-loss order"""
        pass
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order"""
        pass
```

**Deliverable - Risk Manager**:
```python
class RiskManager:
    def __init__(self, config: dict):
        self.config = config
        self.daily_trades = []
        self.positions = {}
    
    def check_position_size(self, symbol: str, quantity: int, entry_price: float) -> bool:
        """
        Verify position size:
        1. Position value < MAX_POSITION_SIZE (e.g., 5% of portfolio)
        2. Position count < MAX_POSITIONS (e.g., 5 positions)
        3. Total portfolio not overlevered
        
        Returns True if safe, False otherwise
        """
        pass
    
    def check_daily_loss(self, realized_pnl: float) -> bool:
        """
        Check daily P&L limit:
        - If daily loss > DAILY_LOSS_LIMIT, reject new trades
        - Prevents catastrophic drawdown
        
        Returns True if within limit
        """
        pass
    
    def calculate_position_size(self, entry_price: float, stop_loss_price: float,
                               risk_amount: float) -> int:
        """
        Calculate position size based on risk:
        
        position_size = risk_amount / (entry_price - stop_loss_price)
        
        Example:
        - Risk $1000, entry $100, stop $95
        - Size = 1000 / (100 - 95) = 200 shares
        """
        pass
```

**Acceptance Criteria**:
- ✅ Orders place successfully via Breeze API
- ✅ Position size limits enforced
- ✅ Daily loss limit prevents overtrading
- ✅ Stop-loss orders placed correctly
- ✅ All orders tracked and retrievable

**Testing**:
```python
# Test position sizing
risk_amount = 1000
entry = 100
stop = 95
size = risk_manager.calculate_position_size(entry, stop, risk_amount)
assert size == 200  # 1000 / (100-95)

# Test daily loss limit
risk_manager.daily_trades = [
    {'pnl': -500},
    {'pnl': -400},  # Total: -900
]
# If DAILY_LOSS_LIMIT = 1000, should allow new trades
assert risk_manager.check_daily_loss(-50) == True
# If loss would exceed limit
assert risk_manager.check_daily_loss(-200) == False
```

---

### Task 1.4: Stage 4 - Exit Strategy Implementation
**File**: `app/strategies/profit_booking_manager.py`

**Time Estimate**: 6 hours

**Deliverable**:
```python
class ProfitBookingManager:
    def __init__(self, config: dict):
        self.config = config
        self.positions = {}  # {symbol: Position}
    
    def open_position(self, symbol: str, entry_price: float, 
                     quantity: int, exit_strategy: str) -> Position:
        """
        Record position opening.
        
        Args:
            exit_strategy: "fixed_full" or "partial_trailing"
        
        Returns: Position object
        """
        pass
    
    def monitor_exits(self, current_prices: dict) -> List[ExitDecision]:
        """
        Monitor all positions for exit triggers.
        
        For each position:
        1. Calculate current P&L
        2. Check if target/stop hit
        3. For partial+trailing: Update trailing stop
        4. Return exit decisions
        """
        pass
    
    def execute_fixed_full_exit(self, position: Position, current_price: float) -> Optional[Trade]:
        """
        Execute full position exit:
        
        Exit when:
        - Price hits target: entry * (1 + TARGET_PROFIT_PCT)
        - Price hits stop: entry * (1 - STOP_LOSS_PCT)
        - Max holding time exceeded
        
        Returns completed Trade or None
        """
        pass
    
    def execute_partial_trailing_exit(self, position: Position, current_price: float) -> Optional[Trade]:
        """
        Execute partial + trailing exit:
        
        At 50% profit (TARGET_PROFIT_PCT / 2):
        - Sell 50% of position
        - Move stop to entry (breakeven)
        - Trailing stop on remaining 50%
        
        Trailing stops follow price up but never down.
        Exit when trailing stop hit.
        
        Returns completed Trade or None
        """
        pass
    
    def close_position(self, position_id: str, exit_price: float) -> Trade:
        """Record position closure with P&L"""
        pass
```

**Key Algorithms**:

**Fixed Full Exit** (for mean-reverting markets):
```
Entry: $100
Target: $100 * (1 + 10%) = $110
Stop: $100 * (1 - 2%) = $98

Exit triggers:
1. Price reaches $110 → Sell 100%, Profit = $10/share
2. Price reaches $98 → Sell 100%, Loss = -$2/share
3. Hold 2 hours → Sell at market
```

**Partial + Trailing Exit** (for trending markets):
```
Entry: $100
Target: $100 * (1 + 10%) = $110
Partial exit: $100 * (1 + 5%) = $105

Step 1: At $105, exit 50%
  - Sell 50 shares at $105 (+ $2.50/share profit)
  - Stop moves to $100 (breakeven, was $98)
  - Remaining 50 shares: trailing stop at highest price

Step 2: If trend continues
  - Price goes to $120
  - Trailing stop automatically moves to $118
  - Protecting profits as price climbs

Step 3: Exit remaining 50%
  - Either at trailing stop (if price reverses from $120)
  - Or at max hold time
```

**Acceptance Criteria**:
- ✅ Fixed exit triggers at correct prices
- ✅ Partial exit happens at 50% profit
- ✅ Trailing stop follows price up only
- ✅ P&L calculated correctly
- ✅ Position lifecycle tracked

**Testing**:
```python
# Fixed exit test
position = Position('TCS', entry=100, qty=100, strategy='fixed_full')
# Price reaches 110
trade = booking_mgr.execute_fixed_full_exit(position, 110)
assert trade.exit_price == 110
assert trade.pnl == 1000  # (110-100)*100

# Partial trailing test
position = Position('TCS', entry=100, qty=100, strategy='partial_trailing')
booking_mgr.open_position('TCS', 100, 100, 'partial_trailing')
# Price reaches 105
partial_exit = booking_mgr.execute_partial_trailing_exit(position, 105)
assert len(partial_exit.exits) == 1  # 50% exited
assert position.quantity == 50  # 50% remaining
```

---

### Task 1.5: Stage 5 - Risk Monitoring Implementation
**Files**:
- `app/services/live_position_tracker.py`
- `app/services/risk_manager.py` (extend from Stage 3)
- `app/services/notifications.py`

**Time Estimate**: 4 hours

**Deliverable**:
```python
class LivePositionTracker:
    def __init__(self):
        self.positions = {}  # Active positions
        self.trades = []     # Closed trades
        self.daily_pnl = 0
        self.max_drawdown = 0
    
    def update_prices(self, current_prices: dict) -> None:
        """
        Update all positions with latest prices.
        
        Calculates:
        - Unrealized P&L per position
        - Total portfolio value
        - Win rate, profit factor
        - Days held per position
        """
        pass
    
    def get_portfolio_metrics(self) -> dict:
        """
        Return:
        {
            'total_positions': 3,
            'open_pnl': 5000,
            'closed_pnl': 2000,
            'daily_pnl': 5000,
            'win_rate': 0.65,  # 65% winning trades
            'profit_factor': 2.5,  # Total wins / Total losses
            'max_drawdown': -0.05,  # Worst equity decline
            'portfolio_value': 1005000  # Initial + P&L
        }
        """
        pass
    
    def get_position_metrics(self, symbol: str) -> dict:
        """Return metrics for specific position"""
        pass
```

**Notification System**:
```python
class NotificationService:
    def send_trade_alert(self, trade: Trade) -> None:
        """
        Alert on:
        1. Trade entry
        2. Profit target hit (exit)
        3. Stop-loss hit (exit)
        4. Position held too long
        
        Channels: Email, Telegram, Dashboard
        """
        pass
    
    def send_risk_alert(self, alert_type: str, message: str) -> None:
        """
        Alert on risk events:
        1. Daily loss limit approaching
        2. Position count limit reached
        3. Portfolio margin exceeded
        4. API connection lost
        """
        pass
    
    def send_performance_report(self, metrics: dict) -> None:
        """Daily performance summary"""
        pass
```

**Acceptance Criteria**:
- ✅ Real-time P&L tracking
- ✅ Portfolio metrics calculated correctly
- ✅ Alerts sent on critical events
- ✅ Performance report generated daily
- ✅ Metrics consistent with closed trades

---

## 🔄 Phase 2: Integration & Orchestration (Weeks 3-4)

### Goal
Wire all 5 stages together into one cohesive system.

### Task 2.1: Create Main Trading Engine
**File**: `app/trading_engine.py` (NEW)

**Time Estimate**: 4 hours

**Deliverable**:
```python
class TradingEngine:
    """
    Orchestrates all 5 stages:
    Signal → Validation → Execution → Exit → Monitoring
    """
    
    def __init__(self, config: dict):
        # Initialize all components
        self.strategy = BuyHoldTrendStrategy(config)
        self.validator = ProductionValidator()
        self.regime_monitor = RegimeMonitor()
        self.order_manager = OrderManager(breeze_client, config)
        self.risk_manager = RiskManager(config)
        self.booking_manager = ProfitBookingManager(config)
        self.tracker = LivePositionTracker()
        self.notifications = NotificationService()
    
    def run_trading_cycle(self, symbol: str, ohlcv_data: pd.DataFrame, 
                         current_prices: dict) -> None:
        """
        Execute one complete trading cycle.
        
        Flow:
        1. Generate signal (Stage 1)
        2. Validate signal (Stage 2)
        3. If valid, execute trade (Stage 3)
        4. Monitor position (Stage 4)
        5. Check portfolio health (Stage 5)
        """
        
        # Stage 1: Signal Generation
        signal = self.strategy.scan_market(symbol, ohlcv_data)
        if not signal:
            return  # No setup detected
        
        # Stage 2: Validation
        valid, errors = self.validator.validate_signal(signal, self.config)
        if not valid:
            logger.info(f"Signal rejected: {errors}")
            return
        
        # Classify regime and select exit strategy
        regime = self.regime_monitor.classify_regime(ohlcv_data)
        exit_strategy = self.regime_monitor.select_exit_strategy(regime)
        
        # Stage 3: Risk checks and position sizing
        if not self.risk_manager.check_daily_loss(0):
            logger.warning("Daily loss limit reached, rejecting new trades")
            return
        
        quantity = self.risk_manager.calculate_position_size(
            signal.entry_price,
            signal.entry_price * (1 - 0.02),  # 2% stop
            risk_amount=1000  # Risk $1000 per trade
        )
        
        if not self.risk_manager.check_position_size(symbol, quantity, signal.entry_price):
            logger.warning("Position size exceeds limits")
            return
        
        # Stage 3: Execute trade
        order = self.order_manager.place_market_order(symbol, quantity, 'BUY')
        if order.status != 'FILLED':
            logger.error(f"Order not filled: {order}")
            return
        
        # Stage 4: Open position for monitoring
        position = self.booking_manager.open_position(
            symbol, 
            order.fill_price,
            quantity,
            exit_strategy
        )
        
        self.tracker.add_position(symbol, position)
        self.notifications.send_trade_alert(
            f"Entry: {symbol} @ {order.fill_price}, Qty: {quantity}, Strategy: {exit_strategy}"
        )
    
    def monitor_exits(self, current_prices: dict) -> None:
        """
        Stage 4 & 5: Monitor all positions and execute exits.
        Also track portfolio health.
        """
        
        # Stage 4: Check for exit signals
        exit_decisions = self.booking_manager.monitor_exits(current_prices)
        
        for decision in exit_decisions:
            # Execute the exit
            trade = self.booking_manager.close_position(
                decision.position_id,
                decision.exit_price
            )
            
            # Stage 5: Record and alert
            self.tracker.add_trade(trade)
            self.notifications.send_trade_alert(
                f"Exit: {trade.symbol} @ {trade.exit_price}, P&L: {trade.pnl}"
            )
        
        # Stage 5: Check portfolio health
        metrics = self.tracker.get_portfolio_metrics()
        
        if metrics['daily_pnl'] > 2000:
            self.notifications.send_performance_report(metrics)
        
        if metrics['max_drawdown'] < -0.10:
            self.notifications.send_risk_alert(
                "HIGH_DRAWDOWN",
                f"Max drawdown: {metrics['max_drawdown']:.2%}"
            )
```

---

### Task 2.2: Flask API Integration
**File**: `app/main.py` (extend existing)

**Time Estimate**: 3 hours

**Deliverable**:
```python
from flask import Flask, jsonify, request
from app.trading_engine import TradingEngine

app = Flask(__name__)
trading_engine = None

def init_trading_engine(app):
    """Initialize trading engine on startup"""
    global trading_engine
    config = load_config('.env')
    trading_engine = TradingEngine(config)
    logger.info("Trading engine initialized")

# ============ Trading Endpoints ============

@app.route('/api/trading/status', methods=['GET'])
def get_status():
    """Get current trading status"""
    metrics = trading_engine.tracker.get_portfolio_metrics()
    return jsonify({
        'status': 'running',
        'positions': metrics['total_positions'],
        'daily_pnl': metrics['daily_pnl'],
        'win_rate': metrics['win_rate'],
        'portfolio_value': metrics['portfolio_value']
    })

@app.route('/api/trading/positions', methods=['GET'])
def get_positions():
    """Get all open positions"""
    positions = trading_engine.tracker.get_positions()
    return jsonify([p.to_dict() for p in positions])

@app.route('/api/trading/trades', methods=['GET'])
def get_trades():
    """Get closed trades"""
    trades = trading_engine.tracker.get_trades()
    return jsonify([t.to_dict() for t in trades])

@app.route('/api/trading/metrics', methods=['GET'])
def get_metrics():
    """Get detailed portfolio metrics"""
    metrics = trading_engine.tracker.get_portfolio_metrics()
    return jsonify(metrics)

@app.route('/api/trading/start', methods=['POST'])
def start_trading():
    """Start automated trading"""
    trading_engine.is_trading = True
    return jsonify({'status': 'trading started'})

@app.route('/api/trading/stop', methods=['POST'])
def stop_trading():
    """Stop automated trading (still monitor exits)"""
    trading_engine.is_trading = False
    return jsonify({'status': 'trading stopped'})

# Initialize on app startup
@app.before_first_request
def startup():
    init_trading_engine(app)
```

---

## 🧪 Phase 3: Testing & Validation (Weeks 5-6)

### Goal
Validate all stages work correctly individually and together.

### Task 3.1: Unit Tests
**File**: `tests/unit/test_trading_system.py`

**Coverage**:
- Signal generation (various market conditions)
- Validation (config, regime, signal)
- Order execution (market, limit, stop)
- Position sizing (various risk amounts)
- Exit strategies (fixed full, partial trailing)
- P&L calculation (various scenarios)

**Time Estimate**: 8 hours

---

### Task 3.2: Integration Tests
**File**: `tests/integration/test_full_pipeline.py`

**Scenarios**:
1. Complete trade from signal to exit
2. Multiple simultaneous positions
3. Daily loss limit enforcement
4. Regime change detection
5. Exit strategy switching
6. Position size limits

**Time Estimate**: 8 hours

---

### Task 3.3: Backtesting
**File**: `app/backtesting.py` (extend existing)

**Run backtests on**:
- 2+ years of historical data
- Multiple market regimes
- Different symbols (TCS, INFY, SBIN, etc.)
- Validate expected metrics

**Time Estimate**: 4 hours

---

## 📦 Phase 4: Production Deployment (Weeks 7-8)

### Task 4.1: Paper Trading
Run system on paper (simulated) trading for 2-3 weeks to validate:
- Signal quality
- Exit timing
- Risk management
- Monitoring accuracy

### Task 4.2: Shadow Mode
Generate signals, manually approve trades for 1-2 weeks before full automation

### Task 4.3: Limited Live Trading
Start with small position sizes, gradually scale up

### Task 4.4: Monitoring & Alerting
Ensure all alerts and monitoring working correctly

---

## 📊 Implementation Checklist

### Phase 1: Core Pipeline

#### Stage 1: Signal Generation
- [ ] Implement BuyHoldTrendStrategy.scan_market()
- [ ] Implement indicator calculations (MA, RSI)
- [ ] Test with historical data
- [ ] Validate signal detection accuracy

#### Stage 2: Validation
- [ ] Implement ProductionValidator.validate_config()
- [ ] Implement ProductionValidator.validate_signal()
- [ ] Implement RegimeMonitor.classify_regime()
- [ ] Implement RegimeMonitor.select_exit_strategy()
- [ ] Test with various market conditions

#### Stage 3: Execution
- [ ] Implement OrderManager.place_market_order()
- [ ] Implement RiskManager.check_position_size()
- [ ] Implement RiskManager.check_daily_loss()
- [ ] Implement RiskManager.calculate_position_size()
- [ ] Test with Breeze API (paper trading)

#### Stage 4: Exit Management
- [ ] Implement ProfitBookingManager.execute_fixed_full_exit()
- [ ] Implement ProfitBookingManager.execute_partial_trailing_exit()
- [ ] Implement trailing stop logic
- [ ] Test exit timing accuracy

#### Stage 5: Monitoring
- [ ] Implement LivePositionTracker.update_prices()
- [ ] Implement portfolio metrics calculation
- [ ] Implement NotificationService alerts
- [ ] Test metric accuracy

### Phase 2: Integration
- [ ] Create TradingEngine orchestration
- [ ] Implement main trading cycle
- [ ] Implement exit monitoring cycle
- [ ] Wire Flask API endpoints
- [ ] Test end-to-end flow

### Phase 3: Testing
- [ ] Unit tests (all components)
- [ ] Integration tests (full pipeline)
- [ ] Backtest on historical data
- [ ] Paper trading validation

### Phase 4: Deployment
- [ ] Paper trading (2-3 weeks)
- [ ] Shadow mode (1-2 weeks)
- [ ] Limited live trading
- [ ] Full monitoring setup

---

## 📁 File Structure Summary

```
app/
├── strategies/
│   ├── buy_hold_trend.py                    ✅ (Stage 1)
│   ├── production_validator.py              ✅ (Stage 2)
│   ├── regime_monitor.py                    ✅ (Stage 2)
│   ├── unified_profit_booking.py            ✅ (Stage 2)
│   └── profit_booking_manager.py            ✅ (Stage 4)
│
├── services/
│   ├── breeze_api.py                        ✅ (Stage 3)
│   ├── order_manager.py                     ✅ (Stage 3)
│   ├── risk_manager.py                      ✅ (Stage 3 & 5)
│   ├── live_position_tracker.py             ✅ (Stage 5)
│   └── notifications.py                     ✅ (Stage 5)
│
├── trading_engine.py                        ⬜ (NEW - Phase 2)
└── main.py                                  ✅ (extend with API)

tests/
├── unit/
│   └── test_trading_system.py               ⬜ (NEW - Phase 3)
└── integration/
    └── test_full_pipeline.py                ⬜ (NEW - Phase 3)
```

**Status Legend**:
- ✅ Exists, needs review/integration
- ⬜ Needs to be created

---

## 🎯 Success Criteria

By the end of implementation:

1. **Signal Generation**: System generates 5-10 signals per week
2. **Win Rate**: 60%+ of trades profitable (backtested)
3. **Profit Factor**: > 1.5 (total wins / total losses)
4. **Risk Management**: No daily loss exceeds limit
5. **Execution**: 95%+ of signals executed within 2 min
6. **Monitoring**: All positions tracked real-time
7. **Alerts**: All critical events trigger notifications
8. **Uptime**: 99.9% system availability

---

## 🚀 Getting Started

1. **Review existing code**: Check each Stage 1-5 file
2. **Complete any gaps**: Fill in missing implementations
3. **Write tests**: Unit + integration tests for each stage
4. **Integrate stages**: Wire them together in TradingEngine
5. **Deploy**: Paper trading → Shadow mode → Live trading

---

## 📞 Questions & Support

**For each stage**: Refer to corresponding section in `docs/ARCHITECTURE_DEEP_DIVE.md`

**For code samples**: Check `docs/guides/` for implementation examples

**For debugging**: Check logs/ directory for execution traces

