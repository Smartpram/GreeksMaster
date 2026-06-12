# Portfolio Polling Quick Reference

**Fast reference for using the portfolio polling service.**

---

## Import

```python
from app.services.portfolio_poller import PortfolioPoller, PortfolioUpdateEvent
```

---

## Initialize

```python
# Create poller
poller = PortfolioPoller(breeze_api, poll_interval=5)

# Start polling
poller.start_polling()

# ... do work ...

# Stop polling
poller.stop_polling_thread()
```

---

## Get Data

```python
# Holdings
holdings = poller.get_holdings()          # Dict[str, dict]
holding = poller.get_holding('INFTEC')    # dict or None

# Positions
positions = poller.get_positions()        # Dict[str, dict]
position = poller.get_position('INFTEC')  # dict or None

# P&L
pnl = poller.get_pnl()                    # dict
# {'total_pnl': X, 'today_pnl': Y, 'pnl_percentage': Z}

# Margin
margin = poller.get_margin()              # dict
# {'available_margin': X, 'utilized_margin': Y, 'balance': Z}

# Status
status = poller.get_status()              # dict
# {'is_polling': True, 'poll_count': X, 'error_count': Y, ...}
```

---

## Events & Callbacks

```python
# Register callback
def on_event(data):
    print(f"Event triggered: {data}")

poller.register_callback(PortfolioUpdateEvent.POSITION_OPENED, on_event)

# Unregister
poller.unregister_callback(PortfolioUpdateEvent.POSITION_OPENED, on_event)

# Available events:
# - HOLDINGS_UPDATED      → Holdings changed
# - POSITION_OPENED       → New position
# - POSITION_CLOSED       → Position closed
# - POSITION_MODIFIED     → Quantity/P&L changed
# - PNL_UPDATED          → Portfolio P&L changed
# - MARGIN_CHANGED       → Margin availability changed
# - ERROR                → Polling error
```

---

## Common Patterns

### Pattern 1: Simple Display

```python
poller = PortfolioPoller(breeze_api)
poller.start_polling()

for i in range(60):
    time.sleep(10)
    pnl = poller.get_pnl()
    print(f"P&L: Rs {pnl['total_pnl']:.2f}")

poller.stop_polling_thread()
```

### Pattern 2: Event Alerts

```python
def on_pnl_update(data):
    if data['total_pnl'] > 10000:
        print("PROFIT TARGET HIT!")
    elif data['total_pnl'] < -5000:
        print("LOSS LIMIT!")

poller = PortfolioPoller(breeze_api)
poller.register_callback(PortfolioUpdateEvent.PNL_UPDATED, on_pnl_update)
poller.start_polling()
```

### Pattern 3: Position Tracking

```python
positions_opened = []

def on_pos_opened(data):
    symbol = data['symbol']
    positions_opened.append(symbol)
    print(f"Tracking: {symbol}")

poller = PortfolioPoller(breeze_api)
poller.register_callback(PortfolioUpdateEvent.POSITION_OPENED, on_pos_opened)
poller.start_polling()
```

### Pattern 4: Error Handling

```python
def on_error(data):
    logger.error(f"Polling error: {data['error']}")
    # Implement retry logic, alerts, etc.

poller = PortfolioPoller(breeze_api)
poller.register_callback(PortfolioUpdateEvent.ERROR, on_error)
poller.start_polling()
```

---

## Data Structures

### Holding

```python
{
    'symbol': 'INFTEC',
    'quantity': 100,
    'price': 250.50,
    'value': 25050.00,
    'pnl': 1200.50,
    'pnl_pct': 4.8,
    'timestamp': datetime(...)
}
```

### Position

```python
{
    'symbol': 'INFTEC',
    'quantity': 100,
    'entry_price': 245.00,
    'current_price': 250.50,
    'pnl': 550.00,
    'pnl_pct': 2.24,
    'timestamp': datetime(...)
}
```

### P&L

```python
{
    'total_pnl': 5500.00,
    'today_pnl': 3200.00,
    'pnl_percentage': 5.2,
    'timestamp': datetime(...)
}
```

### Margin

```python
{
    'available_margin': 50000.00,
    'utilized_margin': 25000.00,
    'balance': 75000.00,
    'timestamp': datetime(...)
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
    'holdings_count': 5,
    'positions_count': 3,
    'total_pnl': 5500.00
}
```

---

## Configuration

```python
# Fast polling (live trading)
poller = PortfolioPoller(breeze_api, poll_interval=2)

# Normal polling (monitoring)
poller = PortfolioPoller(breeze_api, poll_interval=5)

# Slow polling (background watch)
poller = PortfolioPoller(breeze_api, poll_interval=30)
```

---

## Performance

| Metric | Value |
|--------|-------|
| Memory per 100 holdings | ~50-100 KB |
| CPU usage | <1% |
| API calls/hour | 720 (at 5s interval) |
| API safe limit | ~6,000/hour |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Polling not starting | Check `poller.is_polling` or Breeze API connectivity |
| No data updates | Check error count in status, verify API auth |
| High error count | Reduce poll frequency, check network connection |
| Memory leak | Ensure `stop_polling_thread()` is called |

---

## Examples

**Basic dashboard:**
```bash
python scripts/portfolio_polling_examples.py 1
```

**Event callbacks:**
```bash
python scripts/portfolio_polling_examples.py 2
```

**Signal executor integration:**
```bash
python scripts/portfolio_polling_examples.py 3
```

**Monitoring dashboard:**
```bash
python scripts/portfolio_polling_examples.py 4
```

**P&L alerts:**
```bash
python scripts/portfolio_polling_examples.py 5
```

---

## Complete Example

```python
from app.services.portfolio_poller import PortfolioPoller, PortfolioUpdateEvent
import time

# Initialize
breeze_api = BreezeAPIService()
breeze_api.authenticate()

poller = PortfolioPoller(breeze_api, poll_interval=5)

# Define callbacks
def on_position_opened(data):
    print(f"🟢 OPENED: {data['symbol']}")

def on_position_closed(data):
    print(f"🔴 CLOSED: {data['symbol']}")

def on_pnl_updated(data):
    print(f"📊 P&L: Rs {data['total_pnl']:.2f}")

# Register callbacks
poller.register_callback(PortfolioUpdateEvent.POSITION_OPENED, on_position_opened)
poller.register_callback(PortfolioUpdateEvent.POSITION_CLOSED, on_position_closed)
poller.register_callback(PortfolioUpdateEvent.PNL_UPDATED, on_pnl_updated)

# Start polling
poller.start_polling()

# Monitor for 1 minute
for i in range(6):
    time.sleep(10)
    status = poller.get_status()
    print(f"\n[Update {i+1}] Polls: {status['poll_count']}, Errors: {status['error_count']}")

# Cleanup
poller.stop_polling_thread()
print("Done!")
```

---

**Master the patterns. Use the examples. Deploy with confidence!** 🚀
