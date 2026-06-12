# Order Polling vs Portfolio Polling

**Comparison and coordination guide for order and portfolio polling services.**

---

## At a Glance

| Aspect | Order Polling | Portfolio Polling |
|--------|---------------|-------------------|
| **Purpose** | Track individual orders | Monitor overall portfolio |
| **Scope** | Single order → all orders | Holdings, positions, P&L, margin |
| **Update Trigger** | Order status changes | Holdings, positions, P&L changes |
| **Typical Interval** | 2-5 seconds | 5-10 seconds |
| **Data Volume** | Small (order details) | Medium (all holdings/positions) |
| **Use Case** | Real-time order confirmation | Dashboard & risk management |

---

## Architecture Comparison

```
ORDER POLLING SERVICE
  └─ Polls individual orders
  └─ Events: SUBMITTED, FILLED, REJECTED, FAILED
  └─ Data: Order status, fills, prices
  └─ Purpose: Execution verification
  └─ Example: Track "Is my buy order filled?"

PORTFOLIO POLLING SERVICE
  └─ Polls holdings & positions
  └─ Events: POSITION_OPENED, POSITION_CLOSED, PNL_UPDATED
  └─ Data: Holdings, positions, P&L, margin
  └─ Purpose: Portfolio health monitoring
  └─ Example: "What's my current P&L?"
```

---

## Workflow Integration

### Scenario: User Places a Trade

```
1. User Signal
   ↓
2. Signal Executor
   ├─ Calculate position size
   ├─ Check risk limits
   └─ Place order
      ↓
3. ORDER POLLING (starts immediately)
   ├─ Event: OrderPoller.ORDER_SUBMITTED
   ├─ Poll every 2 sec: Is order filled?
   └─ Event: OrderPoller.ORDER_FILLED
      ↓
4. PORTFOLIO POLLING (detects automatically)
   ├─ Event: PortfolioPoller.POSITION_OPENED
   ├─ Detects new position in holdings
   └─ Tracks P&L from entry point
      ↓
5. Dashboard Updates
   ├─ Order status (via order poller)
   └─ Portfolio state (via portfolio poller)
```

### Scenario: User Closes a Position

```
1. Manual Close Signal or Exit Rule
   ↓
2. Signal Executor
   └─ Place sell order
      ↓
3. ORDER POLLING (monitors close order)
   ├─ Event: ORDER_SUBMITTED
   ├─ Poll: Checking sell order...
   └─ Event: ORDER_FILLED
      ↓
4. PORTFOLIO POLLING (detects change)
   ├─ Event: POSITION_CLOSED
   ├─ Realizes P&L
   └─ Updates holdings
      ↓
5. Dashboard Updates
   ├─ "Sell order filled at X"
   └─ "Position closed, P&L: Rs Y"
```

---

## Event Coordination

### Order Events → Portfolio Updates

```
OrderPoller Event           → PortfolioPoller Detects
─────────────────────────────────────────────────────
ORDER_FILLED                → POSITION_OPENED (if buy)
                            → POSITION_MODIFIED (if adjustment)
                            → POSITION_CLOSED (if sell)

ORDER_PARTIALLY_FILLED      → POSITION_MODIFIED (quantity changes)

ORDER_REJECTED              → No portfolio impact (order failed)

ORDER_FAILED                → No portfolio impact (order failed)
```

### Timeline Example

```
Time: 09:30:00
├─ Order placed
└─ OrderPoller: EVENT_SUBMITTED

Time: 09:30:02
├─ OrderPoller polls: Still pending...
└─ [No event]

Time: 09:30:05
├─ Order filled by exchange
└─ OrderPoller: EVENT_FILLED ✅
   └─ Signal Executor notified

Time: 09:30:06
├─ PortfolioPoller polls:
├─ Detects new holding (INFTEC)
└─ PortfolioPoller: POSITION_OPENED ✅
   ├─ Event data: symbol, qty, entry_price
   └─ Dashboard updated

Time: 09:30:10
├─ PortfolioPoller polls again:
├─ Calculates P&L (price moved)
└─ PortfolioPoller: PNL_UPDATED ✅
   ├─ Event data: pnl = +250
   └─ Dashboard P&L updated
```

---

## Usage Patterns

### Pattern 1: Verify Execution → Track Position

```python
# Step 1: Monitor order execution
def on_order_filled(order_data):
    symbol = order_data['symbol']
    quantity = order_data['quantity']
    filled_price = order_data['filled_price']
    
    logger.info(f"Order filled: {symbol} {quantity}@{filled_price}")
    # Don't close yet - let portfolio poller detect it

order_poller.register_callback(OrderPollerEvent.ORDER_FILLED, on_order_filled)

# Step 2: Portfolio poller automatically detects
def on_position_opened(pos_data):
    symbol = pos_data['symbol']
    position = pos_data['position']
    
    logger.info(f"Position opened: {symbol}")
    logger.info(f"Entry: {position['entry_price']}")
    
    # Now track for exits
    track_for_stop_loss(symbol, position['entry_price'])

portfolio_poller.register_callback(
    PortfolioUpdateEvent.POSITION_OPENED, 
    on_position_opened
)
```

### Pattern 2: Risk Management Coordination

```python
# Order poller: Prevent duplicate orders
def on_order_submitted(order_data):
    pending_orders[order_data['symbol']] = order_data

# Portfolio poller: Enforce position limits
def on_position_opened(pos_data):
    symbol = pos_data['symbol']
    
    # Check if we've already opened this today
    if symbol in todays_positions:
        logger.warning(f"Double position: {symbol}")
        # Implement close logic
    
    todays_positions.add(symbol)

# Risk checks using both:
risk_data = {
    'pending_orders': pending_orders,        # From order poller
    'open_positions': positions,              # From portfolio poller
    'portfolio_pnl': portfolio_pnl            # From portfolio poller
}

enforce_risk_limits(risk_data)
```

### Pattern 3: Dashboard Dashboard Sync

```python
# Order poller: Show live order status
def on_order_event(event_type, order_data):
    socketio.emit('order_update', {
        'event': event_type,
        'order': order_data,
        'timestamp': now()
    })

# Portfolio poller: Show live portfolio
def on_portfolio_event(event_type, portfolio_data):
    socketio.emit('portfolio_update', {
        'event': event_type,
        'data': portfolio_data,
        'timestamp': now()
    })

# Frontend receives both streams and updates dashboard
socket.on('order_update', function(data) {
    updateOrderStatus(data);  // "Order filled"
});

socket.on('portfolio_update', function(data) {
    updatePortfolioDisplay(data);  // "Position: +100 INFTEC"
});
```

---

## Key Differences

### Polling Scope

**Order Polling:**
```python
# Polls THIS specific order
orders = breeze.get_order_detail(order_id=12345)
# Returns: [{'order_id': 12345, 'status': 'FILLED', ...}]
```

**Portfolio Polling:**
```python
# Polls ALL holdings and positions
holdings = breeze.get_holding()
# Returns: [
#   {'symbol': 'INFTEC', 'qty': 100, ...},
#   {'symbol': 'NIFTY', 'qty': 50, ...},
#   ...
# ]
```

### Event Granularity

**Order Polling:**
```
SUBMITTED → FILLED
         → REJECTED (fine-grained tracking of single order)
         → FAILED
         → PARTIALLY_FILLED
```

**Portfolio Polling:**
```
POSITION_OPENED    (portfolio-level: "a position opened")
POSITION_CLOSED    (portfolio-level: "a position closed")
PNL_UPDATED        (portfolio-level: "P&L changed")
(coarser: tracks aggregate changes)
```

### Data Freshness

| Metric | Order Polling | Portfolio Polling |
|--------|---------------|-------------------|
| Critical updates | 2 seconds | 5 seconds |
| Typical interval | 2-5 seconds | 5-10 seconds |
| Reason for interval | Order fills fast | Portfolio changes slow |

---

## Coordination Best Practices

### 1. Don't Duplicate Tracking

```python
# ❌ Bad: Both trying to track same position
def on_order_filled(order):
    symbol = order['symbol']
    positions[symbol] = {'status': 'OPEN', ...}  # Order poller

def on_position_opened(pos):
    symbol = pos['symbol']
    positions[symbol] = {'status': 'OPEN', ...}  # Portfolio poller
    # Conflict!

# ✅ Good: Separate responsibilities
def on_order_filled(order):
    logger.info(f"Order {order['id']} filled at {order['filled_price']}")
    # Don't update positions - let portfolio poller do it

def on_position_opened(pos):
    symbol = pos['symbol']
    positions[symbol] = pos  # Portfolio poller is source of truth
```

### 2. Use Portfolio for State, Order for Events

```python
# ✅ Good separation
ORDER_POLLER responsibilities:
  - Notify when orders fill
  - Log execution prices
  - Trigger entry callbacks

PORTFOLIO_POLLER responsibilities:
  - Maintain position state
  - Calculate P&L
  - Enforce risk limits
```

### 3. Coordinate on Error

```python
# If order poller fails
def on_order_polling_error(error):
    logger.warning(f"Order polling error: {error}")
    # Fall back to portfolio poller for position check
    if portfolio_poller.is_healthy():
        positions = portfolio_poller.get_positions()
        # At least we have current state

# If portfolio poller fails
def on_portfolio_polling_error(error):
    logger.warning(f"Portfolio polling error: {error}")
    # Order poller can't compensate - raise alert
    send_alert("Portfolio monitoring down")
```

---

## Integration Checklist

- [ ] Order poller running (existing)
- [ ] Portfolio poller running (new)
- [ ] Order events NOT updating position state (use portfolio)
- [ ] Portfolio poller NOT duplicating order status tracking
- [ ] Dashboard showing both order status AND portfolio state
- [ ] Risk checks using portfolio poller as source of truth
- [ ] Error handling for both pollers
- [ ] Callbacks non-blocking (no long operations in callbacks)
- [ ] Polling intervals optimized (2-5s for orders, 5-10s for portfolio)
- [ ] Tests covering both pollers working together

---

## Timeline & Dependencies

```
Phase 1: Order Polling (EXISTING)
├─ Status: ✅ WORKING
├─ Tracks: Individual orders
└─ Output: Order status events

Phase 2: Portfolio Polling (NEW)
├─ Status: ✅ JUST CREATED
├─ Tracks: Holdings, positions, P&L
├─ Depends on: Order polling working
└─ Output: Portfolio update events

Phase 3: Coordination (NEXT)
├─ Integrate both into main app
├─ Test end-to-end workflows
└─ Deploy to production
```

---

## Scaling Considerations

### For More Orders

```python
# Order poller can handle:
# - Fast polling (2-5s intervals)
# - Hundreds of orders
# - Multiple symbols simultaneously

# Scale by:
# - Increase polling frequency if needed
# - Use efficient order status queries
# - Batch poll multiple orders
```

### For More Positions

```python
# Portfolio poller can handle:
# - Normal polling (5-10s intervals)
# - Hundreds of holdings/positions
# - Complex P&L calculations

# Scale by:
# - Adjust poll intervals if needed
# - Optimize change detection
# - Cache calculations between polls
```

---

## Example: Complete Trade Lifecycle

```python
# Setup both pollers
order_poller = OrderPoller(breeze_api, poll_interval=2)
portfolio_poller = PortfolioPoller(breeze_api, poll_interval=5)

# Register callbacks
def on_order_filled(data):
    print(f"✅ Order filled: {data['symbol']}")

def on_position_opened(data):
    symbol = data['symbol']
    entry = data['position']['entry_price']
    print(f"📊 Position opened: {symbol} @ {entry}")

def on_pnl_updated(data):
    print(f"💰 P&L: Rs {data['total_pnl']:.2f}")

def on_position_closed(data):
    print(f"🏁 Position closed: {data['symbol']}")

order_poller.register_callback(OrderPollerEvent.ORDER_FILLED, on_order_filled)
portfolio_poller.register_callback(PortfolioUpdateEvent.POSITION_OPENED, on_position_opened)
portfolio_poller.register_callback(PortfolioUpdateEvent.PNL_UPDATED, on_pnl_updated)
portfolio_poller.register_callback(PortfolioUpdateEvent.POSITION_CLOSED, on_position_closed)

# Start both
order_poller.start_polling()
portfolio_poller.start_polling()

# Execute a trade
signal = {'symbol': 'INFTEC', 'qty': 100, 'type': 'BUY'}
order_id = signal_executor.execute_signal(signal)

# Timeline:
# T+2s: Order Polling → ✅ Order filled
# T+5s: Portfolio Polling → 📊 Position opened, 💰 P&L updated
# ...time passes...
# T+12s: Portfolio Polling → 💰 P&L updated (+500)
# ...user closes...
# T+14s: Order Polling → ✅ Sell order filled
# T+17s: Portfolio Polling → 🏁 Position closed

# Cleanup
order_poller.stop_polling_thread()
portfolio_poller.stop_polling_thread()
```

---

## Summary

| Aspect | Order Polling | Portfolio Polling |
|--------|---------------|-------------------|
| **What** | Individual order status | Overall portfolio health |
| **Why** | Verify execution | Monitor performance |
| **When** | During/after order placement | Continuously |
| **Frequency** | 2-5 seconds | 5-10 seconds |
| **Trust** | Order confirmation | Position state |
| **Action** | React to fills | Enforce risk limits |

**Use BOTH together for complete trading system visibility!** 🎯

---

**Complete integration guide. Coordinates both services seamlessly!** 🚀
