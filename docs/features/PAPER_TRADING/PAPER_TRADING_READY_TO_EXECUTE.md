# 📊 PAPER TRADING SESSION SETUP - COMPLETE GUIDE

## ✅ Session Created Successfully

**Date:** June 10, 2026  
**Status:** Ready to Execute  
**Capital:** ₹5,00,000 (Paper Trading)  

---

## 🎯 What's Ready

### Main Scripts
1. **`paper_trading_standalone.py`** - Complete standalone paper trading session
   - No external API dependencies
   - Mock realistic OHLCV data generation
   - Golden Cross entry signals
   - Live portfolio tracking
   - JSON report generation

2. **`paper_trading_session_today.py`** - Full-featured version with Breeze API integration
   - 20 Indian stock symbols
   - Real-time market data (when market is open)
   - Advanced risk management
   - Trade Management Layer integration
   - Phase 5 paper trading compatibility

3. **`paper_trading_monitor.py`** - Real-time monitoring dashboard
   - Live P&L tracking
   - Trade statistics
   - Interactive command interface
   - Portfolio visualization

### Documentation Files
- `PAPER_TRADING_GUIDE_TODAY.md` - Comprehensive trading guide
- `START_PAPER_TRADING_NOW.md` - Quick start instructions

---

## 🚀 Quick Execution

###Step 1: Open Two Terminals

**Terminal 1 - Run Trading:**
```powershell
cd c:\Data\GreeksMaster
python paper_trading_standalone.py
```

**Terminal 2 - Watch Logs (Optional):**
```powershell
cd c:\Data\GreeksMaster
Get-Content -Path logs/paper_trading_session.log -Wait
```

### Step 2: View Results

```powershell
# Check generated report
cat logs/paper_trading_report_*.json | python -m json.tool
```

---

## 📋 What Happens During Execution

```
START
  ↓
Initialize Session (₹5,00,000 capital)
  ↓
Scan 20 Indian Stocks:
  • NIFTY50, BANKNIFTY, INFTEC
  • RELIANCE, TCS, HDFCBANK, ICICIBANK, SBIN, etc.
  ↓
For Each Symbol:
  • Generate 100 5-min candles (realistic data)
  • Calculate MA20, MA50, RSI(14)
  • Detect Golden Cross (MA20 > MA50) + RSI < 70 → BUY
  • Detect Death Cross (MA20 < MA50) + RSI > 30 → SELL
  ↓
Execute Trades:
  • BUY: Enter 10% position, reduce capital
  • SELL: Exit position, calculate P&L
  • Track all transactions
  ↓
Generate Report:
  • Portfolio status
  • All trades (entry/exit prices)
  • P&L per trade
  • Total realized P&L
  • JSON file saved
  ↓
END
```

**Duration:** 2-10 seconds (fast execution with mock data)

---

## 📊 Expected Output Structure

### Console Log
```
================================================================================
STANDALONE PAPER TRADING SESSION INITIALIZED
Paper Capital: 500,000
Market Hours: 9:15 AM - 3:30 PM IST
================================================================================

SCREENING CYCLE STARTED
Time: 2026-06-10 17:16:54 IST
================================================================================

[Processing 20 symbols...]

Screening complete | Signals found: X

================================================================================
PORTFOLIO STATUS
================================================================================
Open Positions: X
Available Capital: X
Total Capital: 500,000
Utilization: X%

Trades Executed: X
  • Buys: X
  • Sells: X
  • Realized P&L: X
```

### JSON Report (`logs/paper_trading_report_YYYYMMDD_HHMMSS.json`)
```json
{
  "session_date": "2026-06-10T17:16:54.xxx+05:30",
  "initial_capital": 500000,
  "remaining_capital": XXXXX,
  "utilization_percent": XX.X,
  "trades": [
    {
      "timestamp": "2026-06-10T...",
      "symbol": "RELIANCE",
      "action": "BUY",
      "quantity": XXX,
      "price": XXXX.XX,
      "total": XXXXX,
      "confidence": 0.8
    },
    {
      "timestamp": "2026-06-10T...",
      "symbol": "TCS",
      "action": "SELL",
      "quantity": XXX,
      "entry_price": XXXX.XX,
      "exit_price": XXXX.XX,
      "pnl": XXXXX,
      "pnl_percent": X.XX,
      "confidence": 0.7
    }
  ],
  "open_positions": {
    "SYMBOL": {
      "quantity": XXX,
      "entry_price": XXXX.XX,
      "entry_time": "2026-06-10T..."
    }
  }
}
```

---

## 🔄 Running Multiple Cycles

### Option 1: Manual Repetition
```powershell
# Run 5 times (simulate 5 screening cycles)
for ($i=1; $i -le 5; $i++) {
    Write-Host "Cycle $i - $(Get-Date)"
    python paper_trading_standalone.py
    Start-Sleep -Seconds 60  # Wait 60 seconds between cycles
}
```

### Option 2: Background Job
```powershell
# Start as background job
Start-Job -ScriptBlock {
    cd c:\Data\GreeksMaster
    for ($i=1; $i -le 10; $i++) {
        python paper_trading_standalone.py
        Start-Sleep -Seconds 300  # 5 minutes between cycles
    }
}
```

### Option 3: Scheduled Task (Production)
See `EXECUTION_SEQUENCE_SCHEDULER.md` for complete scheduling setup with APScheduler

---

## 📈 Analyzing Results

### Python Analysis Script

Create `analyze_trading.py`:
```python
import json
import pandas as pd
from pathlib import Path

# Load latest report
reports = list(Path('logs').glob('paper_trading_report_*.json'))
if reports:
    latest = max(reports, key=lambda p: p.stat().st_mtime)
    with open(latest) as f:
        data = json.load(f)
    
    # Extract trades
    trades = data['trades']
    completed = [t for t in trades if t['action'] == 'SELL']
    
    if completed:
        wins = sum(1 for t in completed if t.get('pnl', 0) > 0)
        losses = sum(1 for t in completed if t.get('pnl', 0) < 0)
        total_pnl = sum(t.get('pnl', 0) for t in completed)
        
        print(f"Trades Completed: {len(completed)}")
        print(f"Wins: {wins} ({100*wins/len(completed):.1f}%)")
        print(f"Losses: {losses} ({100*losses/len(completed):.1f}%)")
        print(f"Total P&L: Rs {total_pnl:,.0f}")
        print(f"Avg P&L/Trade: Rs {total_pnl/len(completed):,.0f}")
        print(f"Capital Utilized: {data['utilization_percent']:.1f}%")
```

Run analysis:
```powershell
python analyze_trading.py
```

---

## 🎯 Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Signals Generated | 10+ | Check logs |
| Trades Executed | 5+ | Check JSON |
| Win Rate | 50%+ | Calculate |
| Positive P&L | Yes | Check total |
| Capital Efficiency | 50-100% | Check utilization |
| Execution Errors | 0 | Check logs |

---

## 🔧 Troubleshooting

### No Signals Generated
**Cause:** RSI thresholds not met or not enough data  
**Fix:** Adjust thresholds in code:
```python
if rsi < 75:  # Less strict
```

### JSON Not Created
**Cause:** Session crashed before completion  
**Fix:** Check `logs/paper_trading_session.log` for errors

### Incorrect P&L
**Cause:** Entry/exit prices not recorded  
**Fix:** Verify trades list in JSON report has both BUY and SELL

### Import Errors
**Cause:** Missing pandas/numpy  
**Fix:**
```powershell
pip install pandas numpy pytz
```

---

## 🎓 Integration with Scheduler

To run paper trading on schedule (see `EXECUTION_SEQUENCE_SCHEDULER.md`):

```python
# app/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

def run_paper_trading():
    from paper_trading_standalone import StandalonePaperTrading
    session = StandalonePaperTrading()
    session.run()

scheduler = BackgroundScheduler()

# Run every 5 minutes during market hours (9:15-15:30 IST)
scheduler.add_job(
    run_paper_trading,
    CronTrigger(minute='*/5', hour='9-15'),
    name='paper_trading'
)

scheduler.start()
```

---

## 📁 File Structure

```
c:\Data\GreeksMaster\
├── paper_trading_standalone.py          ← Self-contained (no API needed)
├── paper_trading_session_today.py       ← Full version with Breeze API
├── paper_trading_monitor.py             ← Live monitoring dashboard
├── PAPER_TRADING_GUIDE_TODAY.md         ← Detailed usage guide
├── START_PAPER_TRADING_NOW.md           ← Quick start
├── logs/
│   ├── paper_trading_session.log        ← Live session log
│   └── paper_trading_report_*.json      ← Trade reports
└── docs/
    ├── EXECUTION_SEQUENCE_SCHEDULER.md
    └── ... (other documentation)
```

---

## ✨ Next Steps

### Today (Phase 1)
1. ✅ Scripts created
2. Run paper trading session
3. Analyze results
4. Compare with backtesting

### Tomorrow (Phase 2)
1. Schedule daily runs
2. Monitor 5 days of results
3. Validate entry/exit signals
4. Check win rate > 50%

### Week 1 (Phase 3)
1. Integrate with Breeze API
2. Add real market data
3. Monitor live signals
4. Adjust thresholds if needed

### Week 2+ (Phase 4)
1. Go/no-go decision
2. Live trading deployment
3. Risk monitoring
4. Performance tracking

---

## 🎯 Ready to Trade!

**Quick Commands:**

```powershell
# Run session
python paper_trading_standalone.py

# View report
cat logs/paper_trading_report_*.json | python -m json.tool

# Monitor logs live
Get-Content logs/paper_trading_session.log -Wait

# Analyze results
python -c "import json; r=json.load(open([f for f in __import__('pathlib').Path('logs').glob('paper_trading_report_*.json')][-1])); print(f\"Trades: {len(r['trades'])}, P&L: {sum([t.get('pnl',0) for t in r['trades'] if t['action']=='SELL'])}\")"
```

---

**Status:** ✅ **READY TO EXECUTE**  
**Date:** June 10, 2026  
**Market:** NSE/BSE (Indian Equities)  
**Capital:** ₹5,00,000 (Paper)  

Let's Start Trading! 🚀
