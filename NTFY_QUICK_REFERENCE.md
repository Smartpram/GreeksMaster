🚀 NTFY QUICK REFERENCE - TRADING ALERTS

## Setup (2 Minutes)
1. Download ntfy app (iOS/Android) or visit https://ntfy.sh/web
2. Subscribe to topic: **mport**
3. Run test: `python scripts/test_ntfy_alerts.py`
4. ✅ Start receiving alerts!

---

## All Available Alerts

### Trading Events
| Alert | When | Priority | Example |
|-------|------|----------|---------|
| **ENTRY** | Buy/Sell signal generated | high | [BUY] ENTRY: BANKNIFTY |
| **EXIT** | Exit rule triggered | high | [PROFIT] EXIT: BANKNIFTY |
| **STOP LOSS** | SL hit | **max** | [SL] STOP LOSS HIT: TCS |
| **PROFIT TARGET** | PT hit | high | [PT] PROFIT TARGET HIT: BANKNIFTY |

### Position Management
| Alert | When | Priority | Example |
|-------|------|----------|---------|
| **OPENED** | Position opened | high | [OPEN] POSITION OPENED: NIFTY50 |
| **CLOSED** | Position closed | default | [PROFIT] POSITION CLOSED: NIFTY50 |

### Session Management
| Alert | When | Priority | Example |
|-------|------|----------|---------|
| **START** | Trading starts (09:15) | high | [START] TRADING SESSION STARTED |
| **END** | Trading ends (15:30) | high | [END] SESSION ENDED - PROFIT |
| **SUMMARY** | Daily stats | default | [SUMMARY] DAILY RESULTS |

### Critical Alerts
| Alert | When | Priority | Example |
|-------|------|----------|---------|
| **KILL SWITCH** | Loss hits limit | **max** | *** KILL SWITCH TRIGGERED *** |
| **API ERROR** | Connection fails | **max** | [API] ERROR: Breeze API |
| **ERROR** | System error | **max** | [ERROR] Module Import Failed |

### Market Alerts
| Alert | When | Priority | Example |
|-------|------|----------|---------|
| **RANGE** | Sideways market | low | [RANGE] DETECTED: BANKNIFTY |
| **SENTIMENT** | Market sentiment | default | [SENTIMENT] BULLISH |
| **NO SIGNAL** | No trade signal | low | [INFO] NO SIGNAL |

---

## One-Line Usage Examples

### Send Custom Alert
```python
from ntfy_notification_service import send_alert
send_alert("Title", "Message")
```

### Entry Signal
```python
from ntfy_notification_service import entry_signal
entry_signal("BANKNIFTY", "BUY", 0.85)
```

### Stop Loss Alert
```python
from ntfy_notification_service import stop_loss_hit
stop_loss_hit("TCS", 3400, 3350, 500)
```

### Exit Signal
```python
from ntfy_notification_service import exit_signal
exit_signal("BANKNIFTY", "Profit Target", 1500)
```

### Kill Switch
```python
from ntfy_notification_service import kill_switch
kill_switch(-5500, -5000)
```

### Get Service Instance
```python
from ntfy_notification_service import get_notification_service
ntfy = get_notification_service(topic="mport")

# Then use any method:
ntfy.session_started(100000, 5000)
ntfy.position_opened("NIFTY50", "Bull Spread", 22000, 2, 20000)
ntfy.session_ended(18, 0.94, 3500, 450)
```

---

## Integration Checklist

For Monday deployment, add to `scheduler_options_production.py`:

```python
# At the top
from ntfy_notification_service import get_notification_service
ntfy = get_notification_service(topic="mport")

# In OptionsProductionScheduler.__init__:
self.ntfy = ntfy

# When entry signal generated:
self.ntfy.entry_signal(symbol, direction, confidence)

# When exit executed:
self.ntfy.exit_signal(symbol, exit_type, pnl)

# When SL hit:
self.ntfy.stop_loss_hit(symbol, entry, exit, loss)

# When session starts:
self.ntfy.session_started(capital, max_loss)

# When session ends:
self.ntfy.session_ended(trades, win_rate, pnl, fees)

# When kill switch triggered:
self.ntfy.kill_switch_triggered(loss, threshold)
```

---

## Alert Delivery

✓ **Real-time** - Delivered instantly  
✓ **Reliable** - Via ntfy.sh (https://ntfy.sh)  
✓ **No Sign-up** - Just subscribe to topic  
✓ **Secure** - Your topic = your channel  
✓ **Cross-platform** - iOS, Android, Web, Terminal  
✓ **Free** - No cost whatsoever  

---

## Priority Levels & Behavior

| Priority | Behavior | Use For |
|----------|----------|---------|
| **min** | Silent, no notification | (rarely used) |
| **low** | Batched, no sound | Range, No Signal |
| **default** | Normal notification | Session End, Summary |
| **high** | Sound + vibration | Entry, Exit, Session Start |
| **max** | Persistent, urgent | Kill Switch, Errors, SL |

---

## Testing

### Run Full Test
```bash
python scripts/test_ntfy_alerts.py
```

### Send Single Test Alert
```bash
python -c "from ntfy_notification_service import send_alert; send_alert('[TEST]', 'Testing ntfy alerts')"
```

### Monitor Live
Visit: https://ntfy.sh/mport (in browser)

All alerts visible in real-time!

---

## Emergency Contacts

If alerts not working:
1. Check ntfy app is installed
2. Check "mport" topic subscribed
3. Check notifications enabled
4. Check internet connection
5. Visit https://ntfy.sh/mport in browser

If errors occur:
- Check logs: `tail -f logs/*.log`
- Run test: `python scripts/test_ntfy_alerts.py`
- Review error in ntfy service

---

## Example Alert Screens

### Entry Alert
```
[BUY] ENTRY: BANKNIFTY
BUY ML Hybrid Signal
Confidence: 85.0%
[2026-06-15 09:20:15 IST]
```

### Stop Loss Alert
```
[SL] STOP LOSS HIT: TCS
SL HIT
Entry: Rs 3,400.00
Exit: Rs 3,350.00
Loss: Rs 500.00
[2026-06-15 10:30:45 IST]
```

### Session Summary
```
[SUMMARY] DAILY RESULTS
Trades: 18
Win Rate: 94.0%
P&L: Rs 3,050.00
Best: Rs 850.00
Worst: Rs -200.00
[2026-06-15 15:30:00 IST]
```

### Kill Switch Alert
```
*** KILL SWITCH TRIGGERED ***
Daily loss limit reached
Loss: Rs 5,500.00
Threshold: Rs 5,000.00
[2026-06-15 12:15:30 IST]
```

---

## Ready to Deploy! 🚀

✅ ntfy service created  
✅ 20+ alert types ready  
✅ Tested and working  
✅ Documentation complete  
✅ Ready to integrate  

**Next**: Add to scheduler Monday morning!
