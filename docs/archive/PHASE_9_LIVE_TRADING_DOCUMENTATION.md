# Phase 9: Live Trading Infrastructure Documentation

## Overview

This phase implements the complete live trading workflow with three integrated components:

1. **Stock Screener** (`stock_screener.py`) - Identifies trading opportunities
2. **Live Position Tracker** (`live_position_tracker.py`) - Monitors positions in real-time  
3. **Signal Executor** (`signal_executor.py`) - Executes signals end-to-end

Together, they create a production-ready system for automated trading.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    LIVE TRADING SYSTEM                          │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
                    │  STOCK SCREENER  │
                    │  (screener.py)   │
                    └────────┬─────────┘
                             │ [Qualified stocks + scores]
                             ▼
                    ┌──────────────────┐
                    │ SIGNAL EXECUTOR  │
                    │ (signal_exec.py) │
                    └────────┬─────────┘
                             │ [Execution: BUY/SELL signals]
                             ▼
                    ┌──────────────────┐
        ┌──────────►│ ORDER MANAGER    │◄────────┐
        │           │ (existing)       │         │
        │           └────────┬─────────┘         │
        │                    │ [Order execution] │
        │                    ▼                   │
        │           ┌──────────────────┐         │
        │           │ LIVE POSITIONS   │         │
        │  [Track]  │ (tracker.py)     │ [Update]│
        │           │ - Positions      │         │
        │           │ - P&L            │         │
        │           │ - Signals        │         │
        │           └──────────────────┘         │
        │                    │                   │
        └────────[Queries]────┴───────────────┘
                    ▼
            ┌──────────────────┐
            │ RISK MANAGER     │
            │ (existing)       │
            │ - Position size  │
            │ - Stop loss      │
            │ - Target         │
            └──────────────────┘
```

---

## Component 1: Stock Screener

### Purpose
Identifies high-probability trading opportunities from 201 available stocks using 12 different screening strategies.

### Available Screeners

| Screener | Criteria | Use Case |
|----------|----------|----------|
| **MOMENTUM** | RSI>60, Price>MA50, Volume surge, Daily gain>2% | Quick profits from moving stocks |
| **GROWTH** | Revenue>15%, Margin improving, Higher lows, Low debt | Mid-term growth trades |
| **VALUE** | Low P/E, P/B<1.5, 50% below 52W high | Mean reversion plays |
| **DIVIDEND** | Yield>4%, 30-60% payout, 3yr growth | Income + stability |
| **BREAKOUT** | New 52W high, Volume>200% avg, MACD positive | Trend continuation |
| **TECHNICAL_SETUP** | Golden cross, RSI 30-70, Bollinger bands | Technical traders |
| **PENNY** | Price<100, Volume surge, Low cap | Speculative plays |
| **SMALL_CAP** | Market cap<5000 Cr, High growth | Growth at scale |
| **MID_CAP** | Market cap 5K-20K Cr, Balance | Balanced risk/reward |
| **LARGE_CAP** | Market cap>20K Cr, Stable | Blue chips, low volatility |
| **TURNAROUND** | Improving fundamentals, Debt reduction | Recovery trades |
| **SECTOR_LEADERS** | Top 3 in sector, Strong fundamentals | Sector rotation |

### Usage Example

```python
from app.services.stock_screener import StockScreener, ScreenerType

# Initialize screener
screener = StockScreener(breeze_api, risk_manager)

# Run momentum screener on all stocks
results = screener.run_screener(ScreenerType.MOMENTUM, stocks_df)
# Returns: [
#   {'symbol': 'TCS', 'score': 92, 'price': 3500, 'signals': {...}},
#   {'symbol': 'INFY', 'score': 85, 'price': 1850, 'signals': {...}},
#   ...
# ]

# Add qualified stocks to watchlist for monitoring
for stock in results[:5]:  # Top 5 stocks
    screener.add_to_watchlist(
        symbol=stock['symbol'],
        screener_type=ScreenerType.MOMENTUM,
        price=stock['price'],
        target_price=stock['price'] * 1.15,  # 15% upside target
        stop_loss=stock['price'] * 0.95      # 5% downside stop
    )

# Monitor watchlist and detect entry signals
triggers = screener.check_watchlist_triggers(
    current_prices={'TCS': 3520, 'INFY': 1860}
)
# Returns: {
#   'target_hit': [positions that reached target],
#   'stop_loss_hit': [positions that hit stop loss],
#   'entry_ready': [positions ready for entry]
# }
```

---

## Component 2: Live Position Tracker

### Purpose
Real-time monitoring of all open positions with P&L tracking, signal recording, and status updates.

### Core Concepts

#### Position Lifecycle
```
OPEN → (update prices) → OPEN → (signal) → PARTIAL/EXIT → CLOSED
        ↓ unrealized P&L    ↓ signal triggers    ↓ realized P&L
```

#### Position Status
- `OPEN` - Active position
- `PARTIAL` - Partially filled/exited
- `CLOSING` - Close in progress
- `CLOSED` - Position fully closed
- `PENDING` - Awaiting order fill

#### Signal Triggers
- `TARGET_HIT` - Reached take profit target
- `STOP_LOSS_HIT` - Hit stop loss level
- `ENTRY_READY` - 95-105% of entry price (ready to buy)

### Usage Example

```python
from app.services.live_position_tracker import (
    LivePositionTracker, PositionStatus, SignalType, TriggerType
)

# Initialize tracker
tracker = LivePositionTracker(risk_manager, notifications)

# Open a position
position = tracker.open_position(
    symbol='TCS',
    entry_price=3500,
    quantity=10,
    order_id='ORD123456',
    notes='Momentum screener signal'
)
# Returns position_id

# Update position with latest market price
tracker.update_position_price('position_id', current_price=3520)

# Record a signal on position
signal = SignalTrigger(
    trigger_id='TRIG001',
    signal_type=SignalType.TAKE_PROFIT,
    trigger_type=TriggerType.SCREENER,
    symbol='TCS',
    triggered_at=datetime.now(),
    trigger_price=3650,
    confidence=0.92
)
tracker.record_signal('position_id', signal)

# Partially exit (take 50% profit)
tracker.partial_exit(
    position_id='position_id',
    exit_quantity=5,
    exit_price=3650,
    reason='partial_profit_taking'
)

# Query portfolio summary
summary = tracker.get_portfolio_summary()
# {
#   'open_positions': 3,
#   'total_entry_value': 105000,
#   'total_current_value': 108500,
#   'unrealized_pnl': 3500,
#   'realized_pnl': 2100,
#   'total_pnl': 5600,
#   'total_pnl_percent': 5.33,
#   'win_rate': 75.0,
#   'best_trade': 2500,
#   'worst_trade': -800
# }
```

### Dashboard Metrics

```python
# Get all open positions
positions = tracker.get_all_positions()
# [
#   {
#     'position_id': 'TCS_ORD123_16...',
#     'symbol': 'TCS',
#     'quantity': 10,
#     'entry_price': 3500,
#     'current_price': 3520,
#     'entry_value': 35000,
#     'current_value': 35200,
#     'unrealized_pnl': 200,
#     'unrealized_pnl_percent': 0.57,
#     'days_open': 2,
#     'num_triggers': 1,
#     'status': 'open'
#   },
#   ...
# ]

# Get signals on specific position
signals = tracker.get_signals_log(position_id='TCS_ORD123_16...', hours=24)
# [
#   {
#     'trigger_id': 'TRIG001',
#     'signal_type': 'take_profit',
#     'trigger_price': 3650,
#     'confidence': 92.0,
#     'triggered_at': '2024-01-15T10:30:45',
#     'action_taken': True,
#     'execution_time': '2024-01-15T10:30:50'
#   }
# ]
```

---

## Component 3: Signal Executor

### Purpose
Connects screener signals to position tracking and order execution with support for different automation levels.

### Execution Modes

| Mode | Behavior | Use |
|------|----------|-----|
| **MANUAL** | Alert only, require approval for each trade | Caution/learning |
| **SEMI_AUTO** | Auto-execute + send notification | Balanced |
| **AUTO** | Fully automated with risk validation | High confidence |
| **PAPER** | Simulated trading (default) | Testing |

### Workflow: Screener → Position → Signal → Execution

```
1. SCREENER IDENTIFIES
   Momentum screener finds: TCS (92/100 score, price=3500)
   
2. SIGNAL EXECUTOR RECEIVES
   execute_buy_signal(
       symbol='TCS',
       price=3500,
       confidence=0.92,
       reason='screener'
   )
   
3. EXECUTOR VALIDATES
   - Signal confidence ≥ 50%? YES ✓
   - Calculate position size? 10 shares ✓
   - Risk validation passed? YES ✓
   
4. EXECUTOR PLACES ORDER
   place_order(
       symbol='TCS',
       side='BUY',
       quantity=10,
       price=3500,
       trigger_price=3325  # 5% stop loss
   )
   
5. EXECUTOR TRACKS
   tracker.open_position(
       symbol='TCS',
       entry_price=3500,
       quantity=10,
       order_id='ORD123456'
   )
   
6. POSITION ACTIVELY MONITORED
   - Update prices every minute
   - Detect signal triggers
   - Execute automatic exits on signals
```

### Usage Example

```python
from app.services.signal_executor import (
    SignalExecutor, ExecutionMode
)

# Initialize executor
executor = SignalExecutor(
    order_manager,
    risk_manager,
    position_tracker,
    notifications,
    execution_mode=ExecutionMode.PAPER  # Start in paper trading
)

# Execute buy signal from screener
result = executor.execute_buy_signal(
    symbol='TCS',
    price=3500,
    confidence=0.92,
    reason='screener',
    metadata={'screener_type': 'momentum', 'score': 92}
)
print(result)
# {
#   'symbol': 'TCS',
#   'signal_type': 'buy',
#   'success': True,
#   'order_id': 'ORD123456',
#   'position_id': 'TCS_ORD123456_...',
#   'quantity': 10,
#   'message': 'Buy order placed: 10 x TCS @ 3500.00'
# }

# Execute batch signals from screener results
screened = [
    {'symbol': 'TCS', 'score': 92, 'price': 3500},
    {'symbol': 'INFY', 'score': 85, 'price': 1850},
    {'symbol': 'WIPRO', 'score': 78, 'price': 450}
]
batch_result = executor.execute_screener_signal(screened, auto_execute=True)
# {
#   'total_signals': 3,
#   'executed': 3,
#   'failed': 0,
#   'pending_approval': 0
# }

# Execute exit signal
result = executor.execute_exit_signal(
    symbol='TCS',
    price=3650,
    confidence=0.88,
    reason='target_hit',
    exit_type='full'  # or 'partial'
)
```

### Approval Workflow (Semi-Auto Mode)

```python
# Set to semi-auto for approval-based trading
executor.set_execution_mode(ExecutionMode.SEMI_AUTO)

# Signal will be queued for approval
result = executor.execute_buy_signal('TCS', 3500, 0.92)
# Returns: {'status': 'pending_approval', 'message': 'Requires approval'}

# Check pending approvals
pending = executor.get_pending_approvals()
# [
#   {
#     'symbol': 'TCS',
#     'action': 'BUY',
#     'quantity': 10,
#     'price': 3500,
#     'confidence': 0.92
#   }
# ]

# Approve the signal
executor.approve_pending_signal('TCS_timestamp')
# Signal now executes

# Or reject
executor.reject_pending_signal('TCS_timestamp')
```

---

## End-to-End Trading Workflow

### Daily Trading Cycle

```
09:15 AM - Market Open
│
├─ Run all screeners
│  └─ Find: TCS (momentum), INFY (breakout), WIPRO (value)
│
├─ Execute entry signals
│  ├─ BUY TCS @ 3500 → Position opened
│  ├─ BUY INFY @ 1850 → Position opened
│  └─ BUY WIPRO @ 450 → Position opened
│
├─ Monitor positions (ongoing)
│  ├─ Update prices every minute
│  ├─ Track unrealized P&L
│  └─ Detect signal triggers
│
├─ Execute exit signals (as triggered)
│  ├─ INFY hits target @ 1920 → SELL (take profit)
│  ├─ WIPRO hits stop @ 427 → SELL (cut loss)
│  └─ TCS shows weakness signal → SELL (technical exit)
│
└─ End of day report
   ├─ Closed 3 positions
   ├─ Total P&L: +1,250
   ├─ Win rate: 67%
   └─ Best trade: +500 (INFY)
```

### Implementation Code

```python
from app.services.stock_screener import StockScreener, ScreenerType
from app.services.signal_executor import SignalExecutor, ExecutionMode
from app.services.live_position_tracker import LivePositionTracker
from datetime import datetime
import time

# ============ INITIALIZATION ============
screener = StockScreener(breeze_api, risk_manager)
tracker = LivePositionTracker(risk_manager, notifications)
executor = SignalExecutor(
    order_manager, risk_manager, tracker, 
    notifications, ExecutionMode.PAPER
)

# ============ MORNING: RUN SCREENERS ============
print("🔍 Running screeners...")
momentum = screener.run_screener(ScreenerType.MOMENTUM, stocks_df)
breakout = screener.run_screener(ScreenerType.BREAKOUT, stocks_df)
value = screener.run_screener(ScreenerType.VALUE, stocks_df)

all_results = momentum + breakout + value
print(f"Found {len(all_results)} qualified stocks")

# ============ EXECUTE ENTRY SIGNALS ============
print("📍 Executing entry signals...")
for stock in all_results[:5]:  # Top 5
    result = executor.execute_buy_signal(
        symbol=stock['symbol'],
        price=stock['price'],
        confidence=stock['score'] / 100,
        reason='screener',
        metadata={'screener': stock['screener_type']}
    )
    print(f"  {result['message']}")

# ============ MONITORING LOOP ============
print("👁️  Monitoring positions...")
while True:
    # Update prices
    current_prices = breeze_api.get_current_prices(
        [pos['symbol'] for pos in tracker.get_all_positions()]
    )
    
    for position in tracker.get_all_positions():
        new_price = current_prices.get(position['symbol'])
        if new_price:
            tracker.update_position_price(
                position['position_id'], new_price
            )
    
    # Check for triggers
    for position in tracker.get_all_positions():
        if position['current_price'] >= position['entry_price'] * 1.10:
            # Up 10%, take profit
            result = executor.execute_exit_signal(
                symbol=position['symbol'],
                price=position['current_price'],
                reason='target_hit',
                exit_type='partial'  # Sell half
            )
            print(f"  Exit: {result['message']}")
        
        elif position['current_price'] <= position['entry_price'] * 0.95:
            # Down 5%, stop loss
            result = executor.execute_exit_signal(
                symbol=position['symbol'],
                price=position['current_price'],
                reason='stop_loss',
                exit_type='full'  # Sell all
            )
            print(f"  Exit: {result['message']}")
    
    # Print portfolio summary
    summary = tracker.get_portfolio_summary()
    print(f"  Portfolio PnL: +{summary['total_pnl']:.0f} "
          f"({summary['total_pnl_percent']:.1f}%)")
    
    time.sleep(60)  # Update every minute

# ============ END OF DAY REPORT ============
print("\n📊 End of Day Report")
summary = tracker.get_portfolio_summary()
print(f"Total P&L: {summary['total_pnl']:.0f}")
print(f"Win Rate: {summary['win_rate']:.1f}%")
print(f"Best Trade: {summary['best_trade']:.0f}")
print(f"Worst Trade: {summary['worst_trade']:.0f}")
```

---

## Configuration & Deployment

### Step 1: Paper Trading Validation (REQUIRED)

```powershell
# Run with paper trading for 1-2 days
$env:PAPER_TRADING = "True"
python run_live_trading_system.py
```

### Step 2: Monitor System Health

```python
# Check execution statistics
stats = executor.get_execution_stats()
print(f"Success Rate: {stats['success_rate']}%")
print(f"Pending Approvals: {stats['pending']}")

# Review P&L
summary = tracker.get_portfolio_summary()
print(f"Total P&L: {summary['total_pnl']}")

# Check execution log
history = executor.get_execution_history(hours=24)
for execution in history:
    print(f"{execution['symbol']}: {execution['message']}")
```

### Step 3: Go Live (When Ready)

```powershell
# Update configuration
$env:PAPER_TRADING = "False"
$env:EXECUTION_MODE = "SEMI_AUTO"  # Start semi-auto, escalate to auto

# Restart system
python run_live_trading_system.py
```

### Risk Controls

```ini
# .env configuration
PAPER_TRADING=False
EXECUTION_MODE=semi_auto  # semi_auto > auto (after 1 week)
DEFAULT_CAPITAL=100000
MAX_POSITION_SIZE=0.1
MAX_OPEN_POSITIONS=5
DAILY_LOSS_LIMIT=-5000
MAX_CONCURRENT_SCREENERS=3
MIN_SIGNAL_CONFIDENCE=0.7
```

---

## Common Use Cases

### Use Case 1: Momentum Trader
```python
# Focus on fast-moving stocks
executor.set_execution_mode(ExecutionMode.AUTO)
results = executor.execute_screener_signal(momentum_stocks)

# Exit quickly on profit or loss
executor.execute_exit_signal(
    symbol='STOCK',
    price=market_price,
    reason='take_profit',  # 10% gain
    exit_type='full'
)
```

### Use Case 2: Conservative Investor
```python
# Manual approval for each trade
executor.set_execution_mode(ExecutionMode.MANUAL)

# Review pending signals
pending = executor.get_pending_approvals()
for signal in pending:
    if signal['confidence'] > 0.85:
        executor.approve_pending_signal(signal['id'])

# Longer holding periods
# Track positions for days/weeks
```

### Use Case 3: Multi-Signal Strategy
```python
# Combine multiple screeners
momentum_result = executor.execute_screener_signal(
    momentum_stocks
)
breakout_result = executor.execute_screener_signal(
    breakout_stocks
)

# Cross-validate signals
combined_positions = tracker.get_all_positions()
for pos in combined_positions:
    num_triggers = pos['num_triggers']
    if num_triggers >= 2:  # Confirmed by 2+ signals
        executor.execute_exit_signal(
            symbol=pos['symbol'],
            price=pos['current_price'],
            reason='multi_signal_confirm'
        )
```

---

## Troubleshooting

### Problem: Orders not executing
**Solution**: Check order_manager logs, validate Breeze API connection

### Problem: Positions not tracking P&L correctly
**Solution**: Verify price updates, check position calculations

### Problem: Signals not triggering
**Solution**: Validate screener criteria, check confidence thresholds

### Problem: Paper trading not switching to live
**Solution**: Verify .env configuration, check account permissions

---

## Next Steps

1. ✅ **Stock Screener** - Complete (12 templates)
2. ✅ **Position Tracker** - Complete (real-time P&L)
3. ✅ **Signal Executor** - Complete (end-to-end execution)
4. ⏳ **Live Dashboard** - Create web UI for monitoring
5. ⏳ **Risk Dashboard** - Real-time risk metrics
6. ⏳ **Paper Trading** - 2-day validation
7. ⏳ **Live Deployment** - Go live

---

## Files Reference

| File | Purpose | Status |
|------|---------|--------|
| `app/services/stock_screener.py` | 12 screener templates + watchlist | ✅ Complete |
| `app/services/live_position_tracker.py` | Real-time position tracking + P&L | ✅ Complete |
| `app/services/signal_executor.py` | Signal execution workflow | ✅ Complete |
| `app/services/order_manager.py` | Order execution (existing) | ✅ Complete |
| `app/services/risk_manager.py` | Risk validation (existing) | ✅ Complete |
| `app/services/ai_signal_bridge.py` | Signal generation (existing) | ✅ Complete |

---

## Support

For issues or questions:
1. Check logs in `app/logs/`
2. Review execution history via `executor.get_execution_history()`
3. Monitor position tracker via `tracker.get_portfolio_summary()`
4. Validate configuration in `.env`
