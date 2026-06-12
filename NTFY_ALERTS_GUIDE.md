📱 ntfy TRADING ALERTS INTEGRATION GUIDE

## Quick Setup

### 1. Download ntfy App
- iOS: App Store - Search "ntfy"
- Android: Google Play - Search "ntfy"
- Desktop: https://ntfy.sh/web (in browser)

### 2. Subscribe to Topic
- Topic Name: **mport** (your personal trading alerts)
- Option A: In app, click "+" → Enter "mport"
- Option B: Visit: https://ntfy.sh/mport

### 3. Start Receiving Alerts
All trading events will now send notifications to your phone/desktop!

---

## Alert Types & Examples

### Entry Signals
```
[BUY] ENTRY: BANKNIFTY
BUY ML Hybrid Signal
Confidence: 85.0%
```

### Profit Target / Stop Loss
```
[PT] PROFIT TARGET HIT: BANKNIFTY
TARGET HIT
Entry: Rs 48,000.00
Exit: Rs 48,500.00
Profit: Rs 1,500.00

[SL] STOP LOSS HIT: TCS
SL HIT
Entry: Rs 3,400.00
Exit: Rs 3,350.00
Loss: Rs 500.00
```

### Position Management
```
[OPEN] POSITION OPENED: NIFTY50
Strategy: Options Bull Call Spread
Entry: Rs 22,000.00
Qty: 2
Risk: Rs 20,000.00

[PROFIT] POSITION CLOSED: NIFTY50
P&L: Rs 2,500.00
Trades: 1
```

### Session Events
```
[START] TRADING SESSION STARTED
Capital: Rs 100,000.00
Max Loss: Rs 5,000.00
Time: 2026-06-15 09:15:00 IST

[END] SESSION ENDED - PROFIT
Trades: 18
Win Rate: 94.0%
Gross P&L: Rs 3,500.00
Fees: Rs 450.00
Net P&L: Rs 3,050.00
```

### Critical Alerts
```
*** KILL SWITCH TRIGGERED ***
Daily loss limit reached
Loss: Rs 5,500.00
Threshold: Rs 5,000.00

[API] ERROR: Breeze API
Cannot connect to Breeze API. Check connection.

[ERROR] Module Import Failed
Cannot import trading_engine module
```

### Market Alerts
```
[RANGE] DETECTED: BANKNIFTY
Market in sideways regime. Reduced position size.

[SENTIMENT] BULLISH
Score: 0.72

[SUMMARY] DAILY RESULTS
Trades: 18
Win Rate: 94.0%
P&L: Rs 3,050.00
Best: Rs 850.00
Worst: Rs -200.00
```

---

## Quick Code Examples

### Send Manual Alert
```python
from ntfy_notification_service import get_notification_service

service = get_notification_service(topic="mport")
service.send_alert(
    title="Manual Alert",
    message="This is a manual alert",
    priority="high"
)
```

### Entry Signal
```python
from ntfy_notification_service import entry_signal

entry_signal(
    symbol="BANKNIFTY",
    direction="BUY",
    confidence=0.85
)
```

### Stop Loss Alert
```python
from ntfy_notification_service import stop_loss_hit

stop_loss_hit(
    symbol="TCS",
    entry=3400,
    exit=3350,
    loss=500
)
```

### Session Summary
```python
service = get_notification_service(topic="mport")
service.session_ended(
    trades=18,
    win_rate=0.94,
    pnl=3500,
    fees=450
)
```

---

## Integration with Trading System

### In scheduler_options_production.py

Add at the top:
```python
from ntfy_notification_service import get_notification_service
ntfy = get_notification_service(topic="mport")
```

### On Entry Signal
```python
ntfy.entry_signal(
    symbol=symbol,
    direction="BUY" if signal['direction'] == 1 else "SELL",
    confidence=signal['confidence']
)
```

### On Exit
```python
ntfy.exit_signal(
    symbol=symbol,
    exit_type=exit_rule,
    pnl=position_pnl,
    reason=exit_reason
)
```

### On Stop Loss
```python
if pnl <= -stop_loss_amount:
    ntfy.stop_loss_hit(
        symbol=symbol,
        entry=entry_price,
        exit=exit_price,
        loss=abs(pnl)
    )
```

### On Session Start
```python
ntfy.session_started(
    capital=CAPITAL,
    max_loss=KILL_SWITCH_THRESHOLD
)
```

### On Session End
```python
ntfy.session_ended(
    trades=total_trades,
    win_rate=win_rate,
    pnl=gross_pnl,
    fees=total_fees
)
```

### On Kill Switch
```python
if cumulative_loss <= -KILL_SWITCH_THRESHOLD:
    ntfy.kill_switch_triggered(
        cumulative_loss=cumulative_loss,
        threshold=KILL_SWITCH_THRESHOLD
    )
```

---

## Alert Priorities

### Priority Levels (affecting notification behavior)
- **min** - Silent notification (no sound/vibration)
- **low** - Low priority (batched together)
- **default** - Normal notification
- **high** - High priority (sound + vibration)
- **max** - Maximum priority (persistent notification)

### Used in Trading System
- Entry/Exit: **high**
- Stop Loss/Kill Switch: **max**
- Session Start/End: **high**
- Errors: **max**
- Range Detection: **low**
- Info/No Signal: **low**

---

## Alert Tags (for filtering)

### Categories
- **entry, exit** - Signal events
- **stop-loss, profit-target** - Automated exits
- **position, open, closed** - Position management
- **session, start, end** - Session events
- **kill-switch, critical** - Critical alerts
- **error, alert** - Errors and warnings
- **market, sentiment, range** - Market data
- **summary, daily** - Daily reports

### Filter in ntfy App
1. Open notification
2. Tap "..." (more options)
3. Select "Edit tags" to filter by category

---

## Testing

### Run Full Test Suite
```bash
python scripts/test_ntfy_alerts.py
```

### Send Single Alert
```bash
python -c "from ntfy_notification_service import send_alert; send_alert('Test', 'This is a test alert')"
```

### Check Live Notifications
Visit: https://ntfy.sh/mport (in browser)

---

## Custom Topics

Change topic name in code:
```python
service = get_notification_service(topic="your-custom-topic")
```

Or in environment:
```bash
export NTFY_TOPIC="your-custom-topic"
```

Multiple topics can be subscribed simultaneously in ntfy app!

---

## Troubleshooting

### Not receiving notifications?
1. Check ntfy app is installed and subscribed to "mport"
2. Check notification permissions are enabled
3. Verify internet connection
4. Check firewall (needs access to https://ntfy.sh)

### Encoding errors?
The service now handles non-ASCII characters safely by encoding them.

### Want to customize?
Edit `scripts/ntfy_notification_service.py`:
- Change default topic
- Add new alert types
- Modify priorities
- Add custom tags

### Want to test without sending?
```python
service = get_notification_service()
service.enabled = False  # Disable notifications
```

---

## Full Integration Example

```python
# In your trading scheduler
from ntfy_notification_service import get_notification_service

class TradingScheduler:
    def __init__(self):
        self.ntfy = get_notification_service(topic="mport")
    
    def on_session_start(self):
        self.ntfy.session_started(
            capital=100000,
            max_loss=5000
        )
    
    def on_entry_signal(self, symbol, signal):
        self.ntfy.entry_signal(
            symbol=symbol,
            direction=signal['direction'],
            confidence=signal['confidence']
        )
    
    def on_position_exit(self, symbol, pnl, exit_reason):
        if pnl >= 0:
            self.ntfy.profit_target_hit(...)
        else:
            self.ntfy.stop_loss_hit(...)
    
    def on_kill_switch(self, cumulative_loss):
        self.ntfy.kill_switch_triggered(
            cumulative_loss=cumulative_loss,
            threshold=5000
        )
    
    def on_session_end(self, stats):
        self.ntfy.session_ended(
            trades=stats['total_trades'],
            win_rate=stats['win_rate'],
            pnl=stats['gross_pnl'],
            fees=stats['fees']
        )
```

---

## Platform Support

✓ Works on:
- iOS (ntfy app)
- Android (ntfy app)
- Desktop (web browser at https://ntfy.sh)
- Linux/Mac (terminal client)

✓ No sign-up required
✓ Completely private (you own your topic)
✓ Free to use
✓ Real-time delivery

---

## Next Steps

1. ✅ Download ntfy app
2. ✅ Subscribe to "mport" topic
3. ✅ Run test: `python scripts/test_ntfy_alerts.py`
4. ✅ Integrate into scheduler
5. ✅ Deploy on Monday!

Ready to receive live trading alerts! 🚀
