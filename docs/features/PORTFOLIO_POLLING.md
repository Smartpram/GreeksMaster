# Portfolio Polling Service

**Real-time portfolio monitoring with continuous background polling of holdings, positions, and P&L.**

---

## Overview

The Portfolio Polling Service continuously monitors your trading portfolio in the background, similar to how the Order Polling Service works. It:

✅ **Polls holdings** - Tracks all your stock holdings  
✅ **Polls positions** - Monitors open trade positions  
✅ **Calculates P&L** - Real-time profit/loss tracking  
✅ **Detects changes** - Identifies when positions open/close/change  
✅ **Emits events** - Triggers callbacks on portfolio updates  
✅ **Provides alerts** - Can alert on P&L thresholds  

---

## Quick Start

### Basic Usage (3 lines)

```python
from app.services.portfolio_poller import PortfolioPoller

# Start polling
poller = PortfolioPoller(breeze_api, poll_interval=5)
poller.start_polling()

# Get current data
holdings = poller.get_holdings()
pnl = poller.get_pnl()
```

### Stop Polling

```python
poller.stop_polling_thread()
```

---

## Features

### 1. Continuous Portfolio Monitoring

```python
# Start background polling (5-second intervals)
poller.start_polling()

# Loop and check data
while True:
    holdings = poller.get_holdings()
    for symbol, holding in holdings.items():
        print(f"{symbol}: {holding['quantity']} @ Rs {holding['price']}")
    time.sleep(10)
```

### 2. Event-Driven Updates

React to portfolio changes with callbacks:

```python
from app.services.portfolio_poller import PortfolioUpdateEvent

# Define callbacks
def on_position_opened(data):
    symbol = data.get('symbol')
    print(f"New position: {symbol}")

def on_position_closed(data):
    symbol = data.get('symbol')
    print(f"Position closed: {symbol}")

# Register callbacks
poller.register_callback(PortfolioUpdateEvent.POSITION_OPENED, on_position_opened)
poller.register_callback(PortfolioUpdateEvent.POSITION_CLOSED, on_position_closed)

# Start polling
poller.start_polling()
```

### 3. Real-time P&L Tracking

```python
# Get portfolio-level P&L
pnl = poller.get_pnl()
print(f"Total P&L: Rs {pnl['total_pnl']:.2f}")
print(f"P&L %: {pnl['pnl_percentage']:.2f}%")

# Get specific position P&L
position = poller.get_position('INFTEC')
print(f"INFTEC P&L: Rs {position['pnl']:.2f}")
```

### 4. Change Detection

Automatically detects and emits events for:
- New positions opened
- Positions closed
- Quantity changes
- P&L changes
- Margin changes

```python
# All these trigger events automatically:
def on_holdings_change(data):
    action = data.get('action')  # 'added', 'removed', or 'modified'
    symbol = data.get('symbol')
    print(f"Holding {action}: {symbol}")

poller.register_callback(PortfolioUpdateEvent.HOLDINGS_UPDATED, on_holdings_change)
```

### 5. Polling Status & Statistics

```python
status = poller.get_status()
print(f"Is polling: {status['is_polling']}")
print(f"Total polls: {status['poll_count']}")
print(f"Last poll: {status['last_poll_time']}")
print(f"Errors: {status['error_count']}")
```

---

## API Reference

### Constructor

```python
PortfolioPoller(breeze_service, position_tracker=None, poll_interval=5)
```

**Parameters:**
- `breeze_service` - BreezeAPIService instance
- `position_tracker` - LivePositionTracker instance (optional)
- `poll_interval` - Seconds between polls (default: 5)

### Polling Control

```python
# Start background polling
poller.start_polling() → bool

# Stop background polling
poller.stop_polling_thread() → bool

# Manual poll (call once)
poller.poll_portfolio() → bool
```

### Get Data

```python
# Current holdings
poller.get_holdings() → Dict

# Current positions
poller.get_positions() → Dict

# Portfolio P&L
poller.get_pnl() → Dict

# Margin information
poller.get_margin() → Dict

# Specific holding
poller.get_holding(symbol) → Dict or None

# Specific position
poller.get_position(symbol) → Dict or None

# Polling status
poller.get_status() → Dict
```

### Events & Callbacks

```python
# Register callback
poller.register_callback(event, callback)

# Unregister callback
poller.unregister_callback(event, callback)

# Available events:
# - PortfolioUpdateEvent.HOLDINGS_UPDATED
# - PortfolioUpdateEvent.POSITION_OPENED
# - PortfolioUpdateEvent.POSITION_CLOSED
# - PortfolioUpdateEvent.POSITION_MODIFIED
# - PortfolioUpdateEvent.PNL_UPDATED
# - PortfolioUpdateEvent.MARGIN_CHANGED
# - PortfolioUpdateEvent.ERROR
```

---

## Usage Examples

### Example 1: Simple Portfolio Dashboard

```python
from app.services.portfolio_poller import PortfolioPoller

# Initialize
breeze_api = BreezeAPIService()
breeze_api.authenticate()

poller = PortfolioPoller(breeze_api, poll_interval=5)
poller.start_polling()

# Display portfolio every 10 seconds
for i in range(60):
    time.sleep(10)
    
    holdings = poller.get_holdings()
    pnl = poller.get_pnl()
    
    print(f"\n--- Portfolio Update #{i+1} ---")
    print(f"Holdings: {len(holdings)}")
    print(f"Total P&L: Rs {pnl['total_pnl']:.2f}")
    
    for symbol, holding in holdings.items():
        print(f"  {symbol}: {holding['quantity']} shares")

poller.stop_polling_thread()
```

### Example 2: Alert on P&L Targets

```python
from app.services.portfolio_poller import PortfolioUpdateEvent

poller = PortfolioPoller(breeze_api)

daily_profit_target = 10000
daily_loss_limit = -5000

def check_pnl_alerts(data):
    pnl = data.get('total_pnl', 0)
    
    if pnl > daily_profit_target:
        print(f"✨ PROFIT TARGET HIT! P&L: Rs {pnl:.2f}")
        # Send notification, close positions, etc.
    
    if pnl < daily_loss_limit:
        print(f"🚨 LOSS LIMIT EXCEEDED! P&L: Rs {pnl:.2f}")
        # Send alert, reduce positions, etc.

poller.register_callback(PortfolioUpdateEvent.PNL_UPDATED, check_pnl_alerts)
poller.start_polling()
```

### Example 3: Track Position Lifecycle

```python
from app.services.portfolio_poller import PortfolioUpdateEvent

poller = PortfolioPoller(breeze_api)

def on_position_opened(data):
    symbol = data['symbol']
    position = data['position']
    print(f"🟢 OPENED: {symbol} - {position['quantity']} shares @ Rs {position['entry_price']}")

def on_position_closed(data):
    symbol = data['symbol']
    print(f"🔴 CLOSED: {symbol}")

def on_position_modified(data):
    symbol = data['symbol']
    old_qty = data['old_quantity']
    new_qty = data['new_quantity']
    print(f"📊 MODIFIED: {symbol} - {old_qty} → {new_qty} shares")

poller.register_callback(PortfolioUpdateEvent.POSITION_OPENED, on_position_opened)
poller.register_callback(PortfolioUpdateEvent.POSITION_CLOSED, on_position_closed)
poller.register_callback(PortfolioUpdateEvent.POSITION_MODIFIED, on_position_modified)

poller.start_polling()
```

### Example 4: Integration with Signal Executor

```python
from app.services.portfolio_poller import PortfolioUpdateEvent
from app.services.signal_executor import SignalExecutor

poller = PortfolioPoller(breeze_api)
executor = SignalExecutor(order_manager, risk_manager, position_tracker)

def on_position_opened(data):
    """Update signal tracking when position opens"""
    symbol = data['symbol']
    position = data['position']
    
    # Add to signal executor's position tracking
    executor.track_position(symbol, position)
    print(f"Position tracked: {symbol}")

def on_position_closed(data):
    """Calculate realized P&L when position closes"""
    symbol = data['symbol']
    
    # Get realized P&L from position tracker
    pnl = position_tracker.get_realized_pnl(symbol)
    print(f"Position closed - Realized P&L: Rs {pnl:.2f}")

poller.register_callback(PortfolioUpdateEvent.POSITION_OPENED, on_position_opened)
poller.register_callback(PortfolioUpdateEvent.POSITION_CLOSED, on_position_closed)

poller.start_polling()
```

---

## Data Structures

### Holdings

```python
{
    'symbol': 'INFTEC',
    'quantity': 100,
    'price': 250.50,
    'value': 25050.00,
    'pnl': 1200.50,
    'pnl_pct': 4.8,
    'timestamp': datetime.now()
}
```

### Positions

```python
{
    'symbol': 'INFTEC',
    'quantity': 100,
    'entry_price': 245.00,
    'current_price': 250.50,
    'pnl': 550.00,
    'pnl_pct': 2.24,
    'timestamp': datetime.now()
}
```

### Portfolio P&L

```python
{
    'total_pnl': 5500.00,
    'today_pnl': 3200.00,
    'pnl_percentage': 5.2,
    'timestamp': datetime.now()
}
```

### Margin

```python
{
    'available_margin': 50000.00,
    'utilized_margin': 25000.00,
    'balance': 75000.00,
    'timestamp': datetime.now()
}
```

### Status

```python
{
    'is_polling': True,
    'poll_interval': 5,
    'poll_count': 247,
    'last_poll_time': '2026-06-10T15:30:45',
    'error_count': 0,
    'last_error': None,
    'holdings_count': 5,
    'positions_count': 3,
    'total_pnl': 5500.00
}
```

---

## Events

### PortfolioUpdateEvent.HOLDINGS_UPDATED
Triggered when:
- New holding added
- Holding removed
- Holding quantity changes

**Data:**
```python
{
    'symbol': 'INFTEC',
    'action': 'added' | 'removed' | 'modified',
    'holding': {...}
}
```

### PortfolioUpdateEvent.POSITION_OPENED
Triggered when: New position is opened

**Data:**
```python
{
    'symbol': 'INFTEC',
    'position': {...}
}
```

### PortfolioUpdateEvent.POSITION_CLOSED
Triggered when: Position is closed

**Data:**
```python
{
    'symbol': 'INFTEC'
}
```

### PortfolioUpdateEvent.POSITION_MODIFIED
Triggered when: Position quantity or P&L changes

**Data:**
```python
{
    'symbol': 'INFTEC',
    'old_quantity': 100,
    'new_quantity': 80,
    'holding': {...}
}
```

### PortfolioUpdateEvent.PNL_UPDATED
Triggered when: Portfolio P&L changes significantly

**Data:**
```python
{
    'total_pnl': 5500.00,
    'today_pnl': 3200.00,
    'pnl_percentage': 5.2,
    'timestamp': datetime.now()
}
```

### PortfolioUpdateEvent.MARGIN_CHANGED
Triggered when: Available margin changes significantly

**Data:**
```python
{
    'available_margin': 50000.00,
    'utilized_margin': 25000.00,
    'balance': 75000.00,
    'timestamp': datetime.now()
}
```

### PortfolioUpdateEvent.ERROR
Triggered when: Polling error occurs

**Data:**
```python
{
    'error': 'Connection timeout'
}
```

---

## Configuration

### Poll Interval
```python
# Fast polling (1-2 seconds)
poller = PortfolioPoller(breeze_api, poll_interval=2)

# Normal polling (5 seconds)
poller = PortfolioPoller(breeze_api, poll_interval=5)

# Slow polling (30 seconds)
poller = PortfolioPoller(breeze_api, poll_interval=30)
```

**Recommendations:**
- **Live trading:** 2-5 seconds
- **Monitoring:** 5-10 seconds
- **Background watch:** 30+ seconds

### Change Detection Thresholds

Edit in `portfolio_poller.py`:

```python
# P&L change threshold (ignore small changes)
if abs(old_pnl - new_pnl) > 0.01:  # >Re 0.01
    emit_event()

# Margin change threshold
if abs(old_available - available_margin) > 1000:  # >Rs 1000
    emit_event()
```

---

## Best Practices

### 1. Start Early
```python
# Start polling when strategy initializes
strategy.initialize()
poller.start_polling()  # ← Start immediately
```

### 2. Handle Errors
```python
def on_error(data):
    error = data.get('error')
    logger.error(f"Portfolio polling error: {error}")
    # Take action: retry, alert, gracefully degrade

poller.register_callback(PortfolioUpdateEvent.ERROR, on_error)
```

### 3. Avoid Callbacks Blocking
```python
# Good: Quick callback
def on_pnl_update(data):
    log_to_database(data)  # Fast

# Bad: Long callback
def on_pnl_update(data):
    # This blocks polling thread!
    sleep(5)
    send_email(data)  # Do in separate thread
```

### 4. Set Reasonable Intervals
```python
# Too aggressive: Wastes API quota
poller = PortfolioPoller(breeze_api, poll_interval=1)  # ❌

# Balanced: Good for live trading
poller = PortfolioPoller(breeze_api, poll_interval=5)  # ✅

# Relaxed: For monitoring
poller = PortfolioPoller(breeze_api, poll_interval=30)  # ✅
```

### 5. Clean Up Resources
```python
# Always stop polling on exit
try:
    # ... do work ...
finally:
    poller.stop_polling_thread()
    logger.info("Portfolio polling stopped")
```

---

## Troubleshooting

### "Polling not starting"
```python
if not poller.start_polling():
    print("Failed to start polling")
    print(f"Already polling: {poller.is_polling}")
```

### "No data updates"
```python
# Check polling status
status = poller.get_status()
if status['error_count'] > 0:
    print(f"Polling errors: {status['last_error']}")

# Wait for data
if poller.wait_for_update(timeout=30):
    print("Update received")
```

### "High error count"
```python
# Check if API is accessible
auth = breeze_api.authenticate()
if not auth['success']:
    print("API not accessible")

# Check network
status = poller.get_status()
if status['error_count'] > 5:
    print("Too many errors, check connection")
    poller.stop_polling_thread()
```

---

## Performance Notes

- **Memory:** ~50-100 KB per 100 holdings
- **CPU:** <1% (background thread)
- **API calls:** 1 per poll interval (5 sec = 720/hour = 17,280/day)
- **Within Breeze limits:** Yes (~100 calls/minute = 6000/hour safe)

---

## Examples

See `scripts/portfolio_polling_examples.py` for:
1. Basic portfolio polling
2. Event-driven updates
3. Integration with signal executor
4. Monitoring dashboard
5. P&L threshold alerts

Run:
```bash
python scripts/portfolio_polling_examples.py 1  # Example 1
python scripts/portfolio_polling_examples.py 2  # Example 2
# etc.
```

---

## Next Steps

After implementing portfolio polling:
1. ✅ Start polling on strategy initialization
2. ✅ Register callbacks for key events
3. ✅ Track realized P&L on position close
4. ✅ Alert on P&L thresholds
5. ✅ Log all portfolio changes
6. ✅ Test with paper trading first

---

**Complete! Portfolio polling is ready to use. Start with the examples! 🚀**
