# Portfolio Polling - Visual Architecture Guide

**Visual diagrams and flowcharts for understanding portfolio polling system.**

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      GREEKSMASTER APP                           │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Main Thread (Flask)                                      │  │
│  │  ├─ Web routes                                            │  │
│  │  ├─ Signal executor                                       │  │
│  │  └─ Order manager                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│       ↓                                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PortfolioPoller (Main Thread)                            │  │
│  │  ├─ Service initialization                                │  │
│  │  ├─ Callback registration                                 │  │
│  │  └─ start_polling() ──→ Launch thread                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│       ↓                                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Background Thread (Daemon)                               │  │
│  │  ├─ Polling loop (every 5 seconds)                        │  │
│  │  ├─ API calls: get_holding(), get_position()             │  │
│  │  ├─ Change detection                                      │  │
│  │  ├─ Event emission                                        │  │
│  │  └─ Callback execution                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│       ↓                                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Connected Services                                       │  │
│  │  ├─ Signal Executor (on_position_opened)                 │  │
│  │  ├─ Risk Manager (on_pnl_updated)                         │  │
│  │  ├─ Dashboard (on_*_updated)                              │  │
│  │  ├─ Logger (all events)                                   │  │
│  │  └─ Alerts (on_margin_changed)                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    BREEZE API                                   │
│  ├─ get_holding()  →  Holdings data                             │
│  ├─ get_position() →  Positions data                            │
│  └─ get_margin()   →  Margin info                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Polling Cycle Diagram

```
MAIN POLL CYCLE (Every 5 seconds)
═══════════════════════════════════════════════════════════════════

[Start Loop]
    ↓
[Call API: get_holding()]  ──→  Returns: [{symbol, qty, price, ...}]
    ↓
[Call API: get_position()]  ──→  Returns: [{symbol, qty, entry, ...}]
    ↓
[Call API: get_margin()]  ──→  Returns: {available, used, balance}
    ↓
[Compare with Previous State]
    ├─ Holdings changed?      ──→ YES ──→ [Emit: HOLDINGS_UPDATED]
    ├─ Positions changed?     ──→ YES ──→ [Emit: POSITION_OPENED/CLOSED/MODIFIED]
    ├─ P&L changed?           ──→ YES ──→ [Emit: PNL_UPDATED]
    └─ Margin changed?        ──→ YES ──→ [Emit: MARGIN_CHANGED]
    ↓
[Execute All Registered Callbacks]
    ├─ on_holdings_changed(data)
    ├─ on_position_opened(data)
    ├─ on_pnl_updated(data)
    └─ on_margin_changed(data)
    ↓
[Update Internal State]
    ├─ holdings = new_holdings
    ├─ positions = new_positions
    ├─ pnl = calculated_pnl
    └─ margin = new_margin
    ↓
[Increment Poll Counter]
    ↓
[Sleep 5 seconds]
    ↓
[Loop Back to: Call API: get_holding()]
```

---

## Event Emission Flow

```
POSITION LIFECYCLE
═════════════════════════════════════════════════════════════════

1. User places BUY order for INFTEC
   ↓
2. Order fills (Order Poller detects)
   ↓
3. Portfolio Poller's next cycle (5 seconds)
   ├─ Polls API
   ├─ Detects new position (wasn't there before)
   ├─ Compares with previous state
   ├─ Detects: Holdings added + Position opened
   └─ Emits TWO events:
      ├─ HOLDINGS_UPDATED (new holding added)
      └─ POSITION_OPENED (new position created)
   ↓
4. Registered callbacks execute
   ├─ on_holdings_updated()
   └─ on_position_opened()
   ↓
5. Dashboard updated with new position
   ├─ Adds row to positions table
   └─ Updates portfolio P&L
   ↓
6. 10 seconds later, price moved +Rs 100
   ↓
7. Portfolio Poller's next cycle
   ├─ Polls API
   ├─ Detects: Position quantity same, but P&L changed
   └─ Emits ONE event:
      └─ PNL_UPDATED (P&L = +100)
   ↓
8. Callback executes
   ├─ on_pnl_updated()
   └─ Dashboard P&L meter updated
   ↓
9. User places SELL order to close
   ↓
10. Sell order fills (Order Poller detects)
    ↓
11. Portfolio Poller's next cycle
    ├─ Polls API
    ├─ Detects position gone
    ├─ Detects holding quantity reduced to 0
    └─ Emits TWO events:
       ├─ POSITION_CLOSED (position gone)
       └─ HOLDINGS_UPDATED (holding removed/reduced)
    ↓
12. Callbacks execute
    ├─ on_position_closed()
    ├─ on_holdings_updated()
    └─ Realize P&L: +250 (profit locked in)
    ↓
13. Dashboard updated
    ├─ Removes position from table
    ├─ Updates holdings
    └─ Updates realized P&L counter
```

---

## Data Flow Diagram

```
API RESPONSE PROCESSING
═════════════════════════════════════════════════════════════════

[API Response: get_holding()]
┌────────────────────────────────────────────┐
│ [{                                         │
│   "symbol": "INFTEC",                      │
│   "qty": "100",                            │
│   "price": "250.50",                       │
│   ...                                      │
│ }]                                         │
└────────────────────────────────────────────┘
         ↓ Parse ↓
┌────────────────────────────────────────────┐
│ Holding object {                           │
│   'symbol': 'INFTEC',                      │
│   'quantity': 100,                         │
│   'price': 250.50,                         │
│   'value': 25050.00,                       │
│   'pnl': 1200.50,                          │
│   'pnl_pct': 4.8,                          │
│   'timestamp': datetime.now()              │
│ }                                          │
└────────────────────────────────────────────┘
         ↓ Store ↓
┌────────────────────────────────────────────┐
│ self.holdings['INFTEC'] = {...}            │
└────────────────────────────────────────────┘
         ↓ Return on access ↓
poller.get_holdings()
         →
{
  'INFTEC': {...},
  'NIFTY': {...},
  'RELIANCE': {...}
}
```

---

## Event Types & Conditions

```
EVENT EMISSION CONDITIONS
═════════════════════════════════════════════════════════════════

HOLDINGS_UPDATED
├─ Trigger: Holdings list changes
├─ Condition: New symbol in holdings
│  Example: BUY 100 INFTEC → New holding detected
├─ Condition: Symbol removed from holdings
│  Example: Sell all NIFTY → Holding removed
└─ Condition: Quantity changes
   Example: BUY more INFTEC → Quantity increases

POSITION_OPENED
├─ Trigger: New position created
├─ Condition: Symbol not in positions, now is
└─ Example: Enter a trade → Position opened

POSITION_CLOSED
├─ Trigger: Position eliminated
├─ Condition: Symbol was in positions, now isn't
└─ Example: Exit trade → Position closed

POSITION_MODIFIED
├─ Trigger: Position details changed
├─ Condition: Quantity or P&L changed
└─ Example: Price moved or quantity adjusted

PNL_UPDATED
├─ Trigger: Portfolio P&L changed significantly
├─ Condition: abs(old_pnl - new_pnl) > 0.01
└─ Example: Position price moved → P&L changed

MARGIN_CHANGED
├─ Trigger: Available margin changed significantly
├─ Condition: abs(old_margin - new_margin) > 1000
└─ Example: Margin used for new position

ERROR
├─ Trigger: Exception during polling
├─ Condition: API call failed or parsing failed
└─ Example: API timeout → Error event
```

---

## State Management

```
STATE SNAPSHOT DURING POLL
═════════════════════════════════════════════════════════════════

POLL N-1 (5 seconds ago)
┌─────────────────────────┐
│ holdings: {             │
│   'INFTEC': 100,        │
│   'NIFTY': 50           │
│ }                       │
│ positions: {            │
│   'INFTEC': {...},      │
│   'NIFTY': {...}        │
│ }                       │
│ pnl: +5000              │
│ margin: Rs 50,000       │
└─────────────────────────┘
         (stored)
         ↓ (5 seconds pass)
┌─────────────────────────┐
│ NEW POLL CYCLE:         │
│ 1. Call API             │
│ 2. Get new data         │
│ 3. Compare with old     │
│ 4. Detect changes       │
│ 5. Emit events          │
│ 6. Update state         │
└─────────────────────────┘
         ↓
POLL N (now)
┌─────────────────────────┐
│ holdings: {             │
│   'INFTEC': 100,        │
│   'NIFTY': 50,          │
│   'RELIANCE': 25 ◄──    │ NEW!
│ }                       │
│ positions: {            │
│   'INFTEC': {...},      │
│   'NIFTY': {...},       │
│   'RELIANCE': {...}◄──  │ NEW!
│ }                       │
│ pnl: +5250 ◄── CHANGED! │
│ margin: Rs 48,000 ◄──   │ CHANGED!
└─────────────────────────┘
         (new state stored)
```

---

## Callback Execution Timeline

```
CALLBACK EXECUTION SEQUENCE
═════════════════════════════════════════════════════════════════

Poll cycle completes with 3 changes detected:
  ✓ Holdings updated
  ✓ Position opened
  ✓ P&L updated
         ↓
[Execute HOLDINGS_UPDATED callbacks]
├─ Callback 1: on_holdings_changed
│  └─ Execution time: ~10ms ✓
├─ Callback 2: log_to_database
│  └─ Execution time: ~50ms ✓
├─ Callback 3: update_dashboard
│  └─ Execution time: ~20ms ✓
└─ [Total: ~80ms]
         ↓
[Execute POSITION_OPENED callbacks]
├─ Callback 1: on_position_opened
│  └─ Execution time: ~15ms ✓
├─ Callback 2: setup_stop_loss
│  └─ Execution time: ~5ms ✓
└─ [Total: ~20ms]
         ↓
[Execute PNL_UPDATED callbacks]
├─ Callback 1: on_pnl_updated
│  └─ Execution time: ~10ms ✓
├─ Callback 2: update_dashboard_metrics
│  └─ Execution time: ~5ms ✓
└─ [Total: ~15ms]
         ↓
[All callbacks completed in ~115ms]
         ↓
[Polling thread waits ~4.885 seconds]
         ↓
[Next poll cycle begins]
```

---

## Integration Points

```
CONNECTED SERVICES
═════════════════════════════════════════════════════════════════

┌─────────────────────────────┐
│   PortfolioPoller           │
│   (Central Hub)             │
└──────────────┬──────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ↓          ↓          ↓
Signal      Risk        Dashboard
Executor    Manager     (UI)
    │          │          │
    ├─ Track   ├─ Check   ├─ Display
    │  opens   │  margins │  P&L
    ├─ Set     ├─ Enforce ├─ Show
    │  stops   │  limits  │  holdings
    └─ Size    └─ Alert   └─ Update
       adj.       margin      real-time

                    ↓

            Logger/Database
            (Persistent)
            ├─ Log events
            ├─ Store P&L
            └─ Archive
```

---

## Comparison: Order vs Portfolio Polling

```
ORDER POLLING                │  PORTFOLIO POLLING
═══════════════════════════════════════════════════════════════
Track: Single order          │  Track: All holdings/positions
Scope: One order             │  Scope: Entire portfolio
Event: FILLED, REJECTED      │  Event: OPENED, CLOSED, PNL_UPDATED
Granularity: Order status    │  Granularity: Portfolio state
Interval: 2-5 seconds        │  Interval: 5-10 seconds
Data: Order details          │  Data: Holdings, positions, P&L
Goal: Verify execution       │  Goal: Monitor portfolio
Use case: During trades      │  Use case: Continuous monitoring

TIMELINE EXAMPLE:
─────────────────────────────────────────────────────────────

T+0:00  User clicks BUY
        └─ Order placed
           ↓
T+0:02  [Order Poller checks]
        └─ ORDER_SUBMITTED
           ↓
T+0:04  [Order Poller checks]
        └─ ORDER_SUBMITTED (still pending)
           ↓
T+0:06  [Order Poller checks]
        └─ ORDER_FILLED ✓
           ↓
T+0:10  [Portfolio Poller checks]
        └─ Detects new position
        └─ POSITION_OPENED ✓
        └─ HOLDINGS_UPDATED ✓
           ↓
T+0:15  [Portfolio Poller checks]
        └─ Price changed
        └─ PNL_UPDATED ✓
           ↓
T+0:20  [Portfolio Poller checks]
        └─ Still open, no changes
        └─ (No event)
```

---

## Scaling Architecture

```
SINGLE PORTFOLIO (Current)
┌──────────────────────────────────┐
│ PortfolioPoller (1 instance)     │
├──────────────────────────────────┤
│ Holdings: ~100 symbols            │
│ Positions: ~10-20 open trades     │
│ API calls/hour: 720               │
│ Processing time: <100ms per poll  │
│ Memory: ~100 KB                   │
│ CPU: <1%                          │
└──────────────────────────────────┘

MULTIPLE ACCOUNTS (Future)
┌──────────────────────────────────┐
│ Account Portfolio Manager         │
├────────────┬─────────────┬────────┤
│ Account 1  │ Account 2   │Account3│
│ Poller     │ Poller     │ Poller │
├────────────┼─────────────┼────────┤
│ Holdings:  │ Holdings:  │Hold... │
│  ~100 sym  │  ~100 sym  │ ~100   │
│ Pos: ~15   │ Pos: ~15   │ ~15    │
└────────────┴─────────────┴────────┘
│
├─ All coordinated by Portfolio Manager
├─ Events from all accounts aggregated
└─ Central dashboard shows all accounts
```

---

## Error Recovery

```
ERROR HANDLING FLOW
═════════════════════════════════════════════════════════════════

Poll cycle executes
    ↓
API call fails (timeout, authentication, etc.)
    ↓
Exception caught in polling loop
    ├─ Log error details
    ├─ Increment error counter
    └─ Emit ERROR event
       └─ on_polling_error(error_data)
    ↓
Callback can:
├─ Send alert/notification
├─ Log to monitoring system
├─ Attempt recovery
└─ Gracefully degrade
    ↓
Polling loop continues
├─ Wait configured interval
└─ Retry next cycle
    ↓
Error rate monitoring:
├─ Track consecutive errors
├─ Alert if error_count > threshold
└─ Consider stopping if >= 10 errors
```

---

## Dashboard Real-time Updates

```
WEBSOCKET REAL-TIME FLOW
═════════════════════════════════════════════════════════════════

Portfolio Poller                          Browser Client
(Backend)                                 (Frontend)
    │                                         │
    ├─ Detects change                         │
    └─ Emits event                            │
       └─ on_pnl_updated(data)                │
          └─ Broadcasts via socketio          │
             ├─ socketio.emit(                │
             │  'portfolio_update',           │
             │  {'pnl': +500}                 │
             │ )                              │
             └────────────────────────────→   │ Receives 'portfolio_update'
                                              │ 
                                              ├─ Parse data
                                              ├─ Update DOM
                                              │  └─ document.getElementById(
                                              │      'totalPnL'
                                              │     ).textContent = 'Rs 500'
                                              │
                                              ├─ Animate change
                                              │  └─ Green highlight (profit)
                                              │
                                              └─ Display updated
                                                 (User sees P&L: Rs +500)
```

---

**Visual guide complete. Use these diagrams to understand the system architecture!** 📊

