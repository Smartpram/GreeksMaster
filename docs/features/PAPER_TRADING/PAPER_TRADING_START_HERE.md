# 🎯 PAPER TRADING - START HERE

## ⚡ 30-Second Setup

```bash
# 1. Navigate to project
cd c:\Data\GreeksMaster

# 2. Run paper trading
python paper_trading_standalone.py

# 3. View results
cat logs/paper_trading_report_*.json
```

**Done!** Session completes in 2-10 seconds with full trade report.

---

## 📚 Documentation Map

| Need | Read | Time |
|------|------|------|
| **Just run it** | This file | 1 min |
| **Quick start guide** | `START_PAPER_TRADING_NOW.md` | 5 min |
| **Detailed guide** | `PAPER_TRADING_GUIDE_TODAY.md` | 15 min |
| **Complete setup** | `PAPER_TRADING_READY_TO_EXECUTE.md` | 30 min |
| **Session summary** | `PAPER_TRADING_SESSION_COMPLETE.md` | 10 min |
| **Daily scheduling** | `EXECUTION_SEQUENCE_SCHEDULER.md` | 30 min |

---

## 🎯 What You're Running

**Paper Trading Session for Indian Markets**

```
Stock Symbols: 20 major Indian equities
├─ NIFTY50 (index)
├─ BANKNIFTY (bank index)
├─ 18 individual stocks
└─ (RELIANCE, TCS, HDFC, etc.)

Trading Logic: Golden Cross (Technical Analysis)
├─ Entry: MA20 > MA50 + RSI < 70
├─ Exit: MA20 < MA50 + RSI > 30
└─ Position Size: 10% of capital

Duration: 2-10 seconds
Output: JSON trade report + live logs
Capital: ₹5,00,000 (paper, no real money)
```

---

## 📊 Expected Output

### Console
```
Signals Found: X
BUY: SYMBOL1 @ Price1
SELL: SYMBOL1 @ Price2 | P&L: +/-XXX

Portfolio Status:
- Trades Executed: X
- Realized P&L: +/-XXX
- Utilization: XX%
```

### Files Generated
```
logs/paper_trading_session.log        ← Live log
logs/paper_trading_report_*.json      ← Trade data
```

---

## 🚀 Scripts Available

| Script | Purpose | Command |
|--------|---------|---------|
| **paper_trading_standalone.py** | Main session (✅ use this) | `python paper_trading_standalone.py` |
| paper_trading_session_today.py | Full Breeze API version | `python paper_trading_session_today.py` |
| paper_trading_monitor.py | Live dashboard | `python paper_trading_monitor.py` |

---

## ✅ Pre-Flight Checklist

- [ ] Python 3.8+ installed: `python --version`
- [ ] Required packages: `pip install pandas numpy pytz`
- [ ] logs/ directory exists: `ls logs/`
- [ ] Script file exists: `ls paper_trading_standalone.py`
- [ ] Enough disk space: `dir c:\Data\GreeksMaster`

---

## 🎓 Quick Analysis

After running, check results:

```bash
# View trade report (JSON format)
cat logs/paper_trading_report_*.json

# Count trades
(Select-String -Path logs/paper_trading_session.log "BUY|SELL").Count

# Extract P&L
python -c "import json; r=json.load(open([f for f in __import__('pathlib').Path('logs').glob('paper_trading_report_*.json')][-1])); print(f\"P&L: {sum([t.get('pnl',0) for t in r['trades']])}, Trades: {len([t for t in r['trades'] if t['action']=='SELL'])}\")"
```

---

## 📈 What Happens Step-by-Step

```
START
  ↓
Load Config (₹5,00,000 capital, IST timezone)
  ↓
Scan 20 Indian Stocks (NIFTY50, TCS, RELIANCE, etc.)
  ├─ Generate realistic 5-min candle data
  ├─ Calculate technical indicators (MA, RSI)
  ├─ Check for Golden Cross (buy signal)
  └─ Check for Death Cross (sell signal)
  ↓
Execute Trades
  ├─ BUY when signal found (enter 10% position)
  ├─ SELL when exit signal found (calculate P&L)
  └─ Track all transactions
  ↓
Generate Reports
  ├─ Display portfolio status
  ├─ Save JSON trade report
  └─ Log all activity
  ↓
END (Session complete)
```

**Total Time: 2-10 seconds**

---

## 🎯 Success Looks Like

```
✅ Script runs without errors
✅ Console shows BUY/SELL signals
✅ JSON report is created
✅ P&L values are calculated
✅ Logs show trading activity
✅ Session completes cleanly
```

---

## 🔧 Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: pandas` | `pip install pandas numpy pytz` |
| `FileNotFoundError: logs/` | `mkdir logs` |
| No signals generated | Check RSI thresholds (normal if quiet) |
| Wrong P&L | Verify entry/exit prices match quantities |
| Script hangs | Press Ctrl+C and check logs |

---

## 📞 Next Steps

1. **Run Session**
   ```bash
   python paper_trading_standalone.py
   ```

2. **Review Results**
   ```bash
   cat logs/paper_trading_report_*.json | python -m json.tool
   ```

3. **Run Again** (for consistency testing)
   ```bash
   python paper_trading_standalone.py
   ```

4. **Schedule Daily** (see EXECUTION_SEQUENCE_SCHEDULER.md)
   ```python
   # APScheduler or Windows Task Scheduler
   ```

5. **Go Live** (Week 2+)
   - Connect Breeze API
   - Use real market data
   - Monitor live signals

---

## 📊 Understanding the JSON Report

```json
{
  "session_date": "2026-06-10T17:16:54+05:30",      ← When session ran
  "initial_capital": 500000,                         ← Starting capital
  "remaining_capital": 507300,                       ← Cash left
  "utilization_percent": 0.0,                        ← % of capital deployed
  "trades": [
    {
      "timestamp": "...",
      "symbol": "RELIANCE",
      "action": "BUY",
      "quantity": 178,
      "price": 2809.12,
      "confidence": 0.8
    },
    {
      "timestamp": "...",
      "symbol": "RELIANCE",
      "action": "SELL",
      "quantity": 178,
      "entry_price": 2809.12,
      "exit_price": 2850.0,
      "pnl": 7286.0,           ← Profit in Rupees
      "pnl_percent": 1.46,     ← Profit %
      "confidence": 0.7
    }
  ],
  "open_positions": {}         ← Any holdings at end
}
```

---

## 🎯 Key Metrics to Track

| Metric | How to Calculate | Good Value |
|--------|------------------|-----------|
| **Win Rate** | Wins / Total Completed Trades | > 50% |
| **Avg P&L** | Total P&L / Completed Trades | > ₹0 |
| **Profit Factor** | Gross Profit / Gross Loss | > 1.0 |
| **Utilization** | Used Capital / Total Capital | 50-100% |
| **Signals** | Count of BUY signals | 5-15 per session |

---

## 🚀 Ready?

### Command:
```bash
python paper_trading_standalone.py
```

### Expected Time: 
⏱️ **2-10 seconds**

### Expected Output:
📊 **Trade report with signals and P&L**

### Next:
📈 **Schedule daily runs or integrate with Breeze API**

---

## 📚 Full Documentation

- 📖 `PAPER_TRADING_GUIDE_TODAY.md` - Complete trading guide
- 📖 `START_PAPER_TRADING_NOW.md` - Detailed setup
- 📖 `PAPER_TRADING_READY_TO_EXECUTE.md` - Comprehensive guide
- 📖 `PAPER_TRADING_SESSION_COMPLETE.md` - Full summary
- 📖 `EXECUTION_SEQUENCE_SCHEDULER.md` - Daily scheduling

---

## ✨ Session Details

| Detail | Value |
|--------|-------|
| **Market** | Indian NSE/BSE |
| **Symbols** | 20 major stocks |
| **Strategy** | Golden Cross (MA20/MA50) |
| **Capital** | ₹5,00,000 (Paper) |
| **Timeframe** | 5-minute candles |
| **Entry Signal** | MA20 > MA50 + RSI < 70 |
| **Exit Signal** | MA20 < MA50 + RSI > 30 |
| **Position Size** | 10% per trade |
| **Execution** | Instant (no slippage) |
| **Date** | June 10, 2026 |

---

## 🎓 Learning Path

1. **Understand** - Read this file (1 min)
2. **Execute** - Run script (10 sec)
3. **Analyze** - Review report (5 min)
4. **Learn** - Read guide (15 min)
5. **Schedule** - Set up daily runs (30 min)
6. **Optimize** - Fine-tune signals (1 hour)
7. **Deploy** - Go live (when ready)

---

**🎯 READY TO START PAPER TRADING!**

```bash
python paper_trading_standalone.py
```

Go! 🚀

---

*Last Updated: June 10, 2026*  
*Status: ✅ Ready*  
*Version: 1.0*
