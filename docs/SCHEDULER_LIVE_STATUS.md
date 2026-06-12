# ✅ PAPER TRADING SCHEDULER - LIVE NOW

**Started:** June 11, 2026 at 11:13 AM  
**Status:** RUNNING ✅  
**Location:** `logs/scheduler/paper_trading_schedule_20260611_111346.log`

---

## 📊 WHAT'S SCHEDULED FOR TOMORROW (June 12, 2026)

### Execution Times (IST) - 9 Daily Runs

```
09:00 AM  ──→ PRE-MARKET PREP
          └─ Load models & historical data

09:15 AM  ──→ OPENING SURGE #1 ⚡ HIGHEST VOLATILITY
          └─ Capture market open momentum

09:25 AM  ──→ OPENING SURGE #2
          └─ Continuation trades

10:00 AM  ──→ CONSOLIDATION CHECK
          └─ Verify established trend

13:00 PM  ──→ MID-DAY PIVOT
          └─ Reversal point signals

15:00 PM  ──→ PRE-CLOSE SURGE #1 ⚡ SECOND HIGHEST VOLATILITY
          └─ Profit-taking begins

15:15 PM  ──→ PRE-CLOSE SURGE #2
          └─ Final signals

15:30 PM  ──→ CLOSING BELL
          └─ Last orders before close

15:50 PM  ──→ POST-CLOSING
          └─ Closing auction orders
```

---

## 🎯 WHAT RUNS AT EACH EXECUTION

**17 Instruments** (7 indices + 10 stocks):
- Indices: NIFTY50, BANKNIFTY, FINNIFTY, MIDCAPNIFTY, NIFTYNXT50, NIFTYIT, NIFTYPHARMA
- Stocks: TCS, INFY, WIPRO, MARUTI, BAJAJ-AUTO, HDFC, ICICI, SBIN, LT, SUNPHARMA

**Per Execution Process:**
1. Load 719 historical candles per ticker
2. Load live Breeze API data
3. Train ML models (XGBoost, Random Forest, Gradient Boosting)
4. Generate features (31 indicators)
5. Consensus voting (2+ models = signal)
6. Execute paper trades
7. Calculate P&L (Gross - Fees = Net)
8. Save reports to `reports/live_trading/`

**Expected Output per Execution:**
- 5-10 paper trades across 17 instruments
- Trade entry/exit with timestamps
- P&L breakdown: Gross → Fees → Net
- Win rate tracking
- Performance metrics (Sharpe, profit factor)

---

## 📂 MONITORING & LOGS

**Real-time Logs:**
```
Location: logs/scheduler/paper_trading_schedule_20260611_111346.log

View in PowerShell:
  Get-Content logs/scheduler/paper_trading_schedule_*.log -Wait | Select-Object -Last 50
```

**Reports Generated:**
```
Location: reports/live_trading/

Files created per execution:
  ├── training_NIFTY50_*.json
  ├── training_TCS_*.json
  ├── positions_*.json
  ├── trades_*.json
  └── daily_summary_*.json
```

**Check Today's Executions:**
```powershell
Get-ChildItem reports/live_trading/ -Filter "*.json" | 
  Where-Object {$_.LastWriteTime -gt (Get-Date).AddHours(-24)} | 
  Select-Object Name, LastWriteTime
```

---

## ✅ SCHEDULER STATUS

```
Scheduler Process: python schedule_paper_trading_tonight.py
Status: RUNNING (Background)
Terminal ID: 351b29c7-13a3-42ba-8de4-6c0f9c5a9419
Log File: logs/scheduler/paper_trading_schedule_20260611_111346.log

Schedule Type: Trading Sessions (IST optimized)
Executions per day: 9
First execution: Tomorrow 09:00 AM
```

**Configuration:**
```
Engine: expanded_paper_trading_engine.py
Brokerage Plan: ICICI Direct IVALUE
Fee per trade: ~₹20-30 (including exchange fees)
Position size: 10% of capital per trade
Stop loss: -2% per trade
Instruments: 17 (indices + stocks)
```

---

## 🚀 WHAT TO EXPECT TOMORROW

**Morning (09:00-09:30 AM):**
- First two executions generate opening signals
- 10-20 paper trades executed
- Models trained and ready

**Mid-Day (10:00 AM - 01:00 PM):**
- Consolidation and pivot signals
- Trend validation trades
- 5-15 additional trades

**Afternoon/Closing (03:00-03:50 PM):**
- Pre-close surge signals (highest volatility period)
- Final closing trades
- 10-20 trades in closing surge

**Daily Total (Estimated):**
- Total trades: 25-55 across 9 executions
- Gross P&L: ±₹500-₹5,000
- Fees: ₹300-₹500 (real brokerage costs)
- Net P&L: ±₹0-₹4,500
- Win rate: 40-50%

---

## 📊 TRACKING DAILY RESULTS

**To check end-of-day summary:**
```powershell
# Find today's latest summary report
$latest = Get-ChildItem reports/live_trading/daily_summary_*.json | 
  Sort-Object LastWriteTime -Descending | 
  Select-Object -First 1

# View the summary
Get-Content $latest.FullName | ConvertFrom-Json | Format-Table
```

**Expected Summary Format:**
```
Date               : 2026-06-12
Total_Executions   : 9
Total_Trades       : 45
Total_Gross_PnL    : 1250
Total_Fees         : 400
Total_Net_PnL      : 850
Win_Rate           : 0.4778
Profit_Factor      : 1.82
Sharpe_Ratio       : 1.12
Max_Drawdown       : -0.083
```

---

## 🔄 CONTINUOUS OPERATION

**Scheduler will continue:**
- Tomorrow (June 12): All 9 executions
- Day after (June 13): All 9 executions
- And so on for 30+ days (for paper trading validation)

**To keep running:**
- Don't close the terminal
- Or use Windows Task Scheduler for persistence
- Or run as background process

**To stop scheduler:**
```powershell
# In terminal running scheduler:
Ctrl+C

# Or from another terminal:
Stop-Process -Name python -Force
```

---

## 📈 SYSTEM INCLUDES

✅ **Models Ready**
- XGBoost trained
- Random Forest trained
- Gradient Boosting trained
- Ensemble voting working

✅ **17 Instruments Loaded**
- All symbols configured
- Breeze API connections ready
- Data pipelines tested

✅ **Fee Integration Complete**
- ICICI Direct IVALUE plan
- Real P&L calculation
- Gross → Fees → Net breakdown

✅ **Risk Management Active**
- Kill switches armed
- Stop loss configured
- Position sizing rules
- Emergency stops

---

## 📞 SUPPORT

**Check if scheduler is running:**
```powershell
Get-Process python | Where-Object {$_.CommandLine -like '*schedule*'}
```

**View real-time logs:**
```powershell
Get-Content logs/scheduler/paper_trading_schedule_*.log -Wait
```

**Manual execution (for testing):**
```bash
python expanded_paper_trading_engine.py
```

**Check latest results:**
```powershell
Get-ChildItem reports/live_trading/*.json -Tail 10
```

---

## 🎉 SUMMARY

**Your paper trading system is now LIVE and scheduled!**

✅ Scheduler initialized  
✅ 9 daily executions configured  
✅ All times set (09:00-15:50 IST)  
✅ 17 instruments ready  
✅ Fee-aware P&L tracking  
✅ Reports auto-generated  

**Tomorrow June 12:**
- System runs 9 times automatically
- Paper trades executed throughout day
- Reports generated in real-time
- P&L tracked with realistic fees

**Next 30 days:**
- Validate edge consistency
- Accumulate trading data
- Monitor win rate & metrics
- Prepare for live deployment

🚀 **SYSTEM LIVE AND RUNNING!**
