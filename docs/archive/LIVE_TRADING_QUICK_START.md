# Live Trading Quick Start Guide

**Quick reference for getting started with screeners, position tracking, and signal execution.**

---

## 5-Minute Setup

### 1. Verify Installation

```powershell
# Check Python environment
python --version  # Should be 3.8+

# Verify dependencies
pip list | Select-String "pandas|numpy|requests"

# Test imports
python -c "from app.services.stock_screener import StockScreener; print('✓ OK')"
python -c "from app.services.live_position_tracker import LivePositionTracker; print('✓ OK')"
python -c "from app.services.signal_executor import SignalExecutor; print('✓ OK')"
```

### 2. Load Your Stock Universe

```python
# Get 201 real stock codes (from Phase 8)
from download_security_master import get_stock_universe

stocks_df = get_stock_universe()
print(f"Loaded {len(stocks_df)} stocks")
```

### 3. Initialize Components

```python
from app.services.breeze_api import BreezeAPIService
from app.services.order_manager import OrderManager
from app.services.risk_manager import RiskManager
from app.services.stock_screener import StockScreener
from app.services.live_position_tracker import LivePositionTracker
from app.services.signal_executor import SignalExecutor, ExecutionMode
from app.services.notifications import NotificationService

# Initialize services
breeze = BreezeAPIService()
risk_mgr = RiskManager(capital=100000)
order_mgr = OrderManager(breeze, risk_mgr)
notify = NotificationService()

# Initialize trading system
screener = StockScreener(breeze, risk_mgr)
tracker = LivePositionTracker(risk_mgr, notify)
executor = SignalExecutor(order_mgr, risk_mgr, tracker, notify, 
                         execution_mode=ExecutionMode.PAPER)

print("✓ System initialized")
```

---

## Common Tasks

### Task 1: Find Momentum Stocks

```python
from app.services.stock_screener import ScreenerType

# Run momentum screener
momentum_stocks = screener.run_screener(ScreenerType.MOMENTUM, stocks_df)

print(f"Found {len(momentum_stocks)} momentum stocks")
for stock in momentum_stocks[:5]:
    print(f"  {stock['symbol']}: {stock['score']}/100")

# Output:
#   TCS: 92/100
#   INFY: 85/100
#   WIPRO: 78/100
#   ...
```

### Task 2: Add Stock to Watchlist

```python
# Monitor top stock
top_stock = momentum_stocks[0]

screener.add_to_watchlist(
    symbol=top_stock['symbol'],
    screener_type=ScreenerType.MOMENTUM,
    price=top_stock['price'],
    target_price=top_stock['price'] * 1.15,
    stop_loss=top_stock['price'] * 0.95
)

print(f"✓ Added {top_stock['symbol']} to watchlist")
```

### Task 3: Execute Buy Signal

```python
# Place buy order
result = executor.execute_buy_signal(
    symbol='TCS',
    price=3500,
    confidence=0.92,
    reason='momentum_screener'
)

if result['success']:
    print(f"✓ {result['message']}")
    position_id = result['position_id']
else:
    print(f"✗ {result['message']}")
```

### Task 4: Monitor Position

```python
# Get position details
position = tracker.get_position(position_id)
print(f"Symbol: {position['symbol']}")
print(f"Entry Price: {position['entry_price']}")
print(f"Current Price: {position['current_price']}")
print(f"Unrealized P&L: {position['unrealized_pnl']} ({position['unrealized_pnl_percent']}%)")
```

### Task 5: Update Position Price

```python
# Simulate price update (or get real price from API)
new_price = 3550

tracker.update_position_price(position_id, new_price)

# Get updated position
position = tracker.get_position(position_id)
print(f"Current P&L: {position['unrealized_pnl']}")
```

### Task 6: Execute Exit Signal

```python
# Sell when price reaches target
result = executor.execute_exit_signal(
    symbol='TCS',
    price=3650,
    confidence=0.88,
    reason='target_reached',
    exit_type='full'
)

if result['success']:
    print(f"✓ Position closed: {result['message']}")
```

### Task 7: View Portfolio Summary

```python
# Get all-in-one portfolio view
summary = tracker.get_portfolio_summary()

print(f"Open Positions: {summary['open_positions']}")
print(f"Total Entry Value: ${summary['total_entry_value']:.0f}")
print(f"Current Value: ${summary['total_current_value']:.0f}")
print(f"Unrealized P&L: ${summary['unrealized_pnl']:.0f}")
print(f"Realized P&L: ${summary['realized_pnl']:.0f}")
print(f"Total P&L: ${summary['total_pnl']:.0f} ({summary['total_pnl_percent']:.1f}%)")
print(f"Win Rate: {summary['win_rate']:.1f}%")
print(f"Best Trade: ${summary['best_trade']:.0f}")
print(f"Worst Trade: ${summary['worst_trade']:.0f}")
```

### Task 8: Batch Screener Execution

```python
# Run all screeners and execute top results
from app.services.stock_screener import ScreenerType

screener_types = [
    ScreenerType.MOMENTUM,
    ScreenerType.BREAKOUT,
    ScreenerType.VALUE,
    ScreenerType.GROWTH
]

all_results = []
for screener_type in screener_types:
    results = screener.run_screener(screener_type, stocks_df)
    all_results.extend(results)

# Execute buy signals for high-score stocks
high_score = [s for s in all_results if s['score'] >= 80][:5]
batch_result = executor.execute_screener_signal(high_score)

print(f"Executed: {batch_result['executed']}")
print(f"Failed: {batch_result['failed']}")
```

### Task 9: Check Execution History

```python
# View last 24 hours of execution history
history = executor.get_execution_history(hours=24)

for execution in history:
    status = "✓" if execution['success'] else "✗"
    print(f"{status} {execution['symbol']}: {execution['message']}")

# Get statistics
stats = executor.get_execution_stats()
print(f"\nSuccess Rate: {stats['success_rate']}%")
print(f"Total Signals: {stats['total_signals']}")
```

### Task 10: Switch Execution Mode

```python
from app.services.signal_executor import ExecutionMode

# Start in manual mode (approval required)
executor.set_execution_mode(ExecutionMode.MANUAL)
print("✓ Manual mode: All trades require approval")

# Semi-auto (auto-execute + notify)
executor.set_execution_mode(ExecutionMode.SEMI_AUTO)
print("✓ Semi-auto mode: Auto-execute with notifications")

# Fully auto (no approval needed)
executor.set_execution_mode(ExecutionMode.AUTO)
print("✓ Auto mode: Fully automated trading")

# Paper trading (simulated)
executor.set_execution_mode(ExecutionMode.PAPER)
print("✓ Paper mode: Simulated trading")
```

---

## Complete Example: Morning Trading Session

```python
"""
Complete example: Morning momentum trading
- Run screener
- Monitor watchlist
- Execute signals
- Track positions
- Close trades
"""

import time
from datetime import datetime

print("=" * 60)
print("🚀 MORNING MOMENTUM TRADING SESSION")
print("=" * 60)

# Step 1: Run screeners
print("\n[09:15] Running screeners...")
momentum = screener.run_screener(ScreenerType.MOMENTUM, stocks_df)
breakout = screener.run_screener(ScreenerType.BREAKOUT, stocks_df)

print(f"  Momentum: {len(momentum)} stocks")
print(f"  Breakout: {len(breakout)} stocks")

# Step 2: Execute top signals
print("\n[09:20] Executing buy signals...")
top_stocks = (momentum + breakout)[:3]
positions = {}

for stock in top_stocks:
    result = executor.execute_buy_signal(
        symbol=stock['symbol'],
        price=stock['price'],
        confidence=stock['score'] / 100,
        reason='screener'
    )
    
    if result['success']:
        positions[stock['symbol']] = result['position_id']
        print(f"  ✓ {stock['symbol']}: {result['quantity']} shares @ ${stock['price']:.0f}")

# Step 3: Monitoring loop
print(f"\n[09:30] Monitoring {len(positions)} positions...")

for i in range(5):  # Monitor for 5 "minutes" (demo)
    print(f"\n  [Minute {i+1}]")
    
    # Get portfolio snapshot
    summary = tracker.get_portfolio_summary()
    print(f"    Portfolio P&L: +${summary['total_pnl']:.0f} ({summary['total_pnl_percent']:.1f}%)")
    
    # Check each position
    for pos in tracker.get_all_positions():
        pnl_pct = pos['unrealized_pnl_percent']
        status = "📈" if pnl_pct > 0 else "📉"
        print(f"    {pos['symbol']}: {status} {pnl_pct:+.1f}%")
        
        # Auto-exit on target (15% profit)
        if pnl_pct >= 0.15:
            result = executor.execute_exit_signal(
                symbol=pos['symbol'],
                price=pos['current_price'],
                reason='target_hit',
                exit_type='full'
            )
            print(f"      ✓ SOLD at {pnl_pct:+.1f}% gain")

# Step 4: End of session report
print(f"\n[11:30] SESSION COMPLETE")
summary = tracker.get_portfolio_summary()
print(f"  Total P&L: +${summary['total_pnl']:.0f}")
print(f"  Win Rate: {summary['win_rate']:.1f}%")
print(f"  Positions Closed: {summary['closed_positions']}")
```

---

## Execution Modes Explained

### MANUAL Mode
```python
executor.set_execution_mode(ExecutionMode.MANUAL)

# Signal creates pending approval
result = executor.execute_buy_signal('TCS', 3500)
# → Status: pending_approval

# Review signal
pending = executor.get_pending_approvals()
if pending[0]['confidence'] > 0.85:
    executor.approve_pending_signal('TCS_signal_id')
    # → NOW executes
```

### SEMI_AUTO Mode
```python
executor.set_execution_mode(ExecutionMode.SEMI_AUTO)

# Signal executes automatically + sends alert
result = executor.execute_buy_signal('TCS', 3500)
# → Order placed immediately
# → Notification sent

# You can still cancel if needed
executor.reject_pending_signal('TCS_signal_id')  # Cancel before execution
```

### AUTO Mode
```python
executor.set_execution_mode(ExecutionMode.AUTO)

# Signal executes with no intervention
result = executor.execute_buy_signal('TCS', 3500, confidence=0.92)
# → Order placed
# → Position tracked
# → All automated
```

### PAPER Mode
```python
executor.set_execution_mode(ExecutionMode.PAPER)

# Everything simulated (no real money)
result = executor.execute_buy_signal('TCS', 3500)
# → Simulated order
# → Simulated position tracking
# → Safe for testing
```

---

## Dashboard Queries

### Get All Positions
```python
positions = tracker.get_all_positions()
for pos in positions:
    print(f"{pos['symbol']}: {pos['quantity']} @ {pos['entry_price']}")
```

### Get Signals on Position
```python
signals = tracker.get_signals_log(hours=24)
for signal in signals:
    print(f"{signal['signal_type']}: {signal['trigger_price']} ({signal['confidence']}%)")
```

### Get Execution Stats
```python
stats = executor.get_execution_stats()
print(f"Success Rate: {stats['success_rate']}%")
print(f"Success: {stats['successful']}/{stats['total_signals']}")
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Order fails | Check risk_manager.validate_trade() |
| Position not tracked | Verify position_id returned from executor |
| No signals triggered | Check screener criteria and thresholds |
| Price not updating | Call tracker.update_position_price() manually |
| Wrong P&L calculation | Verify entry/exit prices and quantities |
| Trade not executing | Check execution_mode setting |

---

## Real-World Flow

```
┌─ MORNING ──────────────────────────────────┐
│ 09:15 Run all screeners                    │
│ 09:20 Execute buy signals                  │
│ 09:30-11:30 Monitor positions              │
│ 11:30 Close positions on signals           │
│ 12:00 View end-of-session P&L              │
└────────────────────────────────────────────┘

Position Lifecycle:
  1. Screener identifies stock (e.g., TCS momentum=92%)
  2. execute_buy_signal() creates order
  3. tracker.open_position() begins monitoring
  4. tracker.update_position_price() updates P&L every minute
  5. Condition met (e.g., up 15%) → execute_exit_signal()
  6. Position closed, P&L realized
  7. Next iteration: screener → signal → execution → tracking
```

---

## Next Steps

1. **Test in Paper Mode** (1-2 days)
   ```python
   executor.set_execution_mode(ExecutionMode.PAPER)
   # Run full workflow
   ```

2. **Switch to Semi-Auto** (1 week)
   ```python
   executor.set_execution_mode(ExecutionMode.SEMI_AUTO)
   # Review all trades, approve the good ones
   ```

3. **Go Full Auto** (after validation)
   ```python
   executor.set_execution_mode(ExecutionMode.AUTO)
   # Production trading
   ```

---

**Questions? Check the detailed documentation in `PHASE_9_LIVE_TRADING_DOCUMENTATION.md`**
