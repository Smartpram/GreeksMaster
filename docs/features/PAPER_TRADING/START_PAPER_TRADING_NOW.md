# 🚀 START PAPER TRADING NOW - Setup Instructions

## ⚡ Quick Start (5 minutes)

### Step 1: Verify Setup
```bash
# Check Python
python --version  # Should be 3.8+

# Check required files exist
ls paper_trading_session_today.py
ls paper_trading_monitor.py
ls logs/
```

### Step 2: Run Paper Trading
**Terminal 1** - Trading Session:
```bash
python paper_trading_session_today.py
```

**Terminal 2** - Live Monitor (optional):
```bash
python paper_trading_monitor.py
```

### Step 3: View Results
```bash
# Check trade report
cat logs/paper_trading_report_*.json | jq .

# View logs
tail -f logs/paper_trading_session.log
```

---

## 📋 Prerequisites

### Required
- ✅ Python 3.8+
- ✅ pandas, numpy
- ✅ `logs/` directory exists
- ✅ Config files in `app/`

### Optional
- ⭐ jq (for JSON viewing): `pip install jq`
- ⭐ colorama (for colored output): `pip install colorama`

### Verify Installation
```bash
python -c "import pandas, numpy, pytz; print('✅ All dependencies OK')"
```

---

## 🎯 What Will Happen

### Session Flow

**1. Initialization (30 seconds)**
```
→ Load configuration
→ Initialize Breeze API (mock)
→ Set up watchlist (20 symbols)
→ Create logs directory
→ Display session info
```

**2. Screening (varies)**
```
→ Fetch intraday data for 20 symbols
→ Calculate MA20, MA50, RSI
→ Detect Golden Cross (BUY) or Death Cross (SELL)
→ Execute paper trades
→ Update portfolio
```

**3. Reporting (10 seconds)**
```
→ Display portfolio status
→ Show all trades executed
→ Calculate P&L
→ Save JSON report
→ Clean exit
```

### Total Time: 2-10 minutes (depending on data)

---

## 📊 Expected Output

### Console Output Example

```
════════════════════════════════════════════════════════════════════════════════
                        PAPER TRADING SESSION START

Market: Indian NSE/BSE | Date: 2026-06-10 | Time: 14:32:45 IST
════════════════════════════════════════════════════════════════════════════════

════════════════════════════════════════════════════════════════════════════════
SCREENING CYCLE STARTED
Time: 2026-06-10 14:32:45 IST
════════════════════════════════════════════════════════════════════════════════

✅ BUY: RELIANCE | Q: 178 @ ₹2,809.12 | Total: ₹500,000.00
   Reasoning: Golden Cross: MA20 (2814.32) > MA50 (2798.76)...
   Remaining Capital: ₹0.00

✅ SELL: TCS | Q: 138 @ ₹3,650.00 | Total: ₹504,300.00
   Entry: ₹3,623.45 | Exit: ₹3,650.00
   P&L: ₹3,656.70 (+1.01%)
   
════════════════════════════════════════════════════════════════════════════════
PORTFOLIO STATUS
════════════════════════════════════════════════════════════════════════════════

Open Positions: 1
  • RELIANCE: 178 @ ₹2,809.12 = ₹500,000.00

Available Capital: ₹4,300.00
Total Capital: ₹500,000.00
Utilization: 99.1%

Trades Executed: 2
  • Buys: 1
  • Sells: 1
  • Realized P&L: ₹3,656.70
```

### Log File Output
```
logs/paper_trading_session.log (live update as trades execute)
logs/paper_trading_report_20260610_143245.json (saved after session)
```

---

## 🔧 Configuration

### Default Settings

| Setting | Value | Purpose |
|---------|-------|---------|
| Capital | ₹5,00,000 | Paper trading capital |
| Position Size | 10% per trade | Risk management |
| Watchlist | 20 symbols | Indian equities |
| Entry Signal | MA20 > MA50 + RSI < 70 | Golden Cross |
| Exit Signal | MA20 < MA50 | Death Cross |
| Timeframe | 5-minute | Intraday |

### Customize (if needed)

Edit `paper_trading_session_today.py`:

```python
# Change capital
self.paper_capital = 1000000  # ₹10,00,000

# Change position size
quantity = int(self.current_capital * 0.05 / price)  # 5% instead of 10%

# Change watchlist
self.watchlist = ['RELIANCE', 'TCS', 'INFY']  # Only 3 symbols
```

---

## 📈 Interpreting Results

### Success Indicators

✅ **Signals Generated**
- 50%+ symbols showing signals = Good
- Multiple BUY/SELL signals = Active market

✅ **P&L Results**
- Positive total P&L = Strategy working
- Win rate > 50% = Profitable
- Clean exits = Good signal detection

✅ **Portfolio Health**
- Capital utilization 50-100% = Optimal
- No errors in logs = Clean execution
- JSON report generated = Complete session

### Warning Signs

⚠️ **Few or No Signals**
- Market may be quiet
- Check if market hours
- Verify data loading

⚠️ **High Losses**
- Strategy may be entering bad trades
- Check RSI/MA thresholds
- Consider tighter entry criteria

⚠️ **Log Errors**
- Check Internet connection
- Verify Breeze API access
- Check required dependencies

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError"
```bash
# Install missing packages
pip install pandas numpy pytz
```

### Issue: "logs directory not found"
```bash
# Create logs directory
mkdir -p logs
```

### Issue: "No signals generated"
```bash
# Check market hours (9:15 AM - 3:30 PM IST)
# Verify watchlist symbols
# Check data loading in logs
```

### Issue: "Poor P&L performance"
```bash
# Review trade reasoning in logs
# Check MA periods (20, 50 are standard)
# Verify RSI thresholds (70 = overbought, 30 = oversold)
```

### Issue: "Port already in use" (if using monitor)
```bash
# Kill existing process
kill $(lsof -t -i :5000)
# Or change port in monitor.py
```

---

## 📊 Understanding the Output

### Trade Entry
```
✅ BUY: RELIANCE | Q: 178 @ ₹2,809.12 | Total: ₹500,000.00
   ↓                ↓                ↓              ↓
   Action          Symbol         Quantity    Price    Total Capital Used
```

### Trade Exit
```
✅ SELL: TCS | Q: 138 @ ₹3,650.00 | Total: ₹504,300.00
   Entry: ₹3,623.45 | Exit: ₹3,650.00
   P&L: ₹3,656.70 (+1.01%)
   ↓                     ↓              ↓
   Entry Price      Exit Price     Profit/Loss & %
```

### Portfolio Status
```
Utilization: 99.1%
↓
Percentage of capital deployed in positions (0-100%)
```

---

## 🔄 Running Continuous Sessions

### Option 1: Run Multiple Times (Manual)
```bash
# Run 1st session
python paper_trading_session_today.py

# Wait 5 minutes...
# Run 2nd session
python paper_trading_session_today.py

# Continue as needed...
```

### Option 2: Batch Script
Create `run_all_sessions.sh`:
```bash
#!/bin/bash
for i in {1..10}; do
    echo "Running session $i at $(date)"
    python paper_trading_session_today.py
    sleep 300  # Wait 5 minutes
done
```

Then run:
```bash
bash run_all_sessions.sh
```

### Option 3: Scheduled (via EXECUTION_SEQUENCE_SCHEDULER.md)
```python
# APScheduler
scheduler.add_job(
    run_paper_trading,
    CronTrigger(minute='*/5', hour='9-15'),
    name='paper_trading'
)
```

---

## 📝 Next Steps After First Run

### 1. Review Results (5 min)
```bash
# Check if trades executed
cat logs/paper_trading_report_*.json | jq '.trades | length'

# Check P&L
cat logs/paper_trading_report_*.json | jq '.trades[] | select(.action=="SELL") | .pnl'
```

### 2. Compare with Backtesting
- Expected win rate: 50-55%
- Expected avg P&L per trade: ₹200-500
- Sharpe ratio: >0.8

### 3. Decide Next Action
- ✅ **If profitable:** Schedule daily runs
- ⚠️ **If breakeven:** Tweak parameters
- ❌ **If losing:** Review strategy

### 4. Move to Live (Phase 5)
- Use real Breeze API
- Start with 1 symbol
- Monitor closely
- Increase symbols gradually

---

## 🎯 Success Criteria

| Criterion | Target | Status |
|-----------|--------|--------|
| Signals Generated | 10+ | Check logs |
| Trades Executed | 5+ | Check JSON |
| Positive P&L | Yes | Check P&L sum |
| Clean Execution | 0 errors | Check error log |
| Report Generated | Yes | Check files |

---

## 📞 Support

### Quick Checks
1. Is market open? (9:15 AM - 3:30 PM IST)
2. Do logs show data loading?
3. Do signals appear in logs?
4. Does JSON report exist?

### File Locations
- Main script: `paper_trading_session_today.py`
- Monitor: `paper_trading_monitor.py`
- Logs: `logs/paper_trading_session.log`
- Reports: `logs/paper_trading_report_*.json`
- Config: `app/config.py`

---

## ✅ Checklist Before Running

- [ ] Python 3.8+ installed
- [ ] Dependencies installed (pandas, numpy, pytz)
- [ ] `logs/` directory exists
- [ ] `paper_trading_session_today.py` exists
- [ ] Breeze API key in config (or use mock)
- [ ] Market hours checked (9:15-3:30 PM IST)
- [ ] Terminal ready for output

---

## 🚀 Ready? Let's Go!

```bash
# Run this command to start:
python paper_trading_session_today.py

# In another terminal, watch live:
python paper_trading_monitor.py
```

**Expected Duration:** 2-10 minutes  
**Output:** Trade report + JSON file  
**Next:** Review results and schedule daily runs  

Good luck! 📈
