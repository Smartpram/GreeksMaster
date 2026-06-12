# 🚀 TONIGHT'S PAPER TRADING SCHEDULE - START HERE

**Date:** June 11, 2026  
**Status:** Updated System Ready to Deploy  
**Execution:** 9 times tomorrow (June 12) starting at 09:00 AM IST

---

## ⚡ QUICK START (COPY & PASTE)

### Option 1: Run Scheduler Now (Simple)
```powershell
python schedule_paper_trading_tonight.py
```
**What it does:**
- Starts scheduler
- Runs 9 times tomorrow (09:00, 09:15, 09:25, 10:00, 13:00, 15:00, 15:15, 15:30, 15:50)
- Logs all activity to `logs/scheduler/paper_trading_schedule_*.log`
- Keep terminal open (or run in background)

**To run in background (Windows PowerShell):**
```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command `"cd 'c:\Data\GreeksMaster'; python schedule_paper_trading_tonight.py`""
```

---

### Option 2: Schedule with Windows Task Scheduler (Best for Production)

**Step 1: Create scheduled task**
```powershell
$taskName = "PaperTradingScheduler"
$scriptPath = "C:\Data\GreeksMaster\schedule_paper_trading_tonight.py"
$pythonExe = "C:\Data\GreeksMaster\.venv\Scripts\python.exe"

# Create trigger (daily at 08:00 AM IST + 5:30 hours = 1:30 PM UTC = 08:00 PM IST if UTC+5:30)
# Simplified: Just run at 08:00 AM every day
$trigger = New-ScheduledTaskTrigger -Daily -At "08:00 AM"

# Create action
$action = New-ScheduledTaskAction -Execute $pythonExe -Argument $scriptPath -WorkingDirectory "C:\Data\GreeksMaster"

# Create principal (run as SYSTEM)
$principal = New-ScheduledTaskPrincipal -UserID "NT AUTHORITY\SYSTEM" -RunLevel Highest

# Register task
Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Principal $principal -Description "Paper Trading System - 9 executions per day"

Write-Host "✅ Task '$taskName' scheduled successfully"
```

**Step 2: Verify task created**
```powershell
Get-ScheduledTask -TaskName "PaperTradingScheduler" | Get-ScheduledTaskInfo
```

**Step 3: Run task manually (to test)**
```powershell
Start-ScheduledTask -TaskName "PaperTradingScheduler"
```

---

## 📊 WHAT RUNS TOMORROW (June 12)

```
09:00 AM  ──→ PRE-MARKET PREP
          ├─ Load 719 historical candles
          ├─ Load live Breeze API data
          ├─ Train ML models (XGB, RF, GB)
          └─ Status: Model warmup

09:15 AM  ──→ OPENING SURGE #1 ⚡ HIGHEST VOLATILITY
          ├─ Generate opening signals
          ├─ Execute paper trades
          ├─ Record entry price & timestamp
          └─ Status: Momentum capture

09:25 AM  ──→ OPENING SURGE #2 ⚡ CONTINUATION
          ├─ Follow-up signal generation
          ├─ Catch momentum continuation
          └─ Status: Secondary entry

10:00 AM  ──→ CONSOLIDATION CHECK
          ├─ Verify trend after opening
          ├─ Generate consolidation signals
          └─ Status: Trend validation

13:00 PM  ──→ MID-DAY PIVOT
          ├─ Market sentiment shifts
          ├─ Key reversal point
          └─ Status: Reversal signals

15:00 PM  ──→ PRE-CLOSE SURGE #1 ⚡ SECOND HIGHEST VOLATILITY
          ├─ Profit-taking begins
          ├─ Strong momentum trades
          └─ Status: Pre-close prep

15:15 PM  ──→ PRE-CLOSE SURGE #2 ⚡ FINAL SIGNALS
          ├─ Final continuation signals
          ├─ Last entry opportunity
          └─ Status: Final trades

15:30 PM  ──→ CLOSING BELL
          ├─ Last orders before market close
          ├─ Auction orders matched
          └─ Status: End-of-day trades

15:50 PM  ──→ POST-CLOSING
          ├─ Fixed-price closing orders
          ├─ Overnight positioning
          └─ Status: Final consolidation
```

**Total Trades Expected:** ~9-15 paper trades (depends on signal confidence)  
**P&L Tracking:** Real-time with fee-inclusive calculations  
**Reports Generated:** JSON files with full trade details

---

## 📈 SYSTEM INCLUDES (From Last Night's Run)

✅ **17 Instruments Ready**
- Indices (7): NIFTY50, BANKNIFTY, FINNIFTY, MIDCAPNIFTY, NIFTYNXT50, NIFTYIT, NIFTYPHARMA
- Stocks (10): TCS, INFY, WIPRO, MARUTI, BAJAJ-AUTO, HDFC, ICICI, SBIN, LT, SUNPHARMA

✅ **Fee-Aware P&L**
- ICICI Direct IVALUE plan (₹20/trade + exchange fees)
- Gross P&L → Fees → Net P&L calculation
- Real P&L tracking in reports

✅ **ML Model Ensemble**
- XGBoost trained and ready
- Random Forest trained and ready
- Gradient Boosting trained and ready
- Consensus voting: 2+ models agree = SIGNAL

✅ **Risk Management**
- Stop loss configured
- Position sizing rules
- Exit logic on SMA20 breakdown
- Kill switches armed

---

## 📂 OUTPUT LOCATIONS

**Logs:**
```
logs/scheduler/paper_trading_schedule_*.log
  └─ All execution logs, signals, metrics
```

**Reports (JSON):**
```
reports/live_trading/
├── training_NIFTY50_*.json
├── training_TCS_*.json
├── positions_*.json
└── trades_*.json
```

**Daily Summary:**
```
reports/live_trading/daily_summary_*.json
  └─ Total trades, gross P&L, fees, net P&L
```

---

## 🎯 TONIGHT'S TASKS

### Immediate (Now - 20 minutes)
- [ ] Choose Option 1 (manual) or Option 2 (Task Scheduler)
- [ ] Run `python schedule_paper_trading_tonight.py`
- [ ] Verify scheduler started successfully
- [ ] Check log file appears

### Tomorrow Morning (09:00 AM)
- [ ] Monitor first execution (pre-market)
- [ ] Check `logs/scheduler/` for output
- [ ] Verify trades appearing in `reports/live_trading/`

### Tomorrow Evening (04:00 PM+)
- [ ] Review daily results
- [ ] Check total P&L (Gross - Fees = Net)
- [ ] Analyze signal generation
- [ ] Document any issues

---

## 📋 MONITORING COMMANDS

**Watch logs in real-time:**
```powershell
Get-Content logs/scheduler/paper_trading_schedule_*.log -Wait | Select-Object -Last 50
```

**Check all reports generated today:**
```powershell
Get-ChildItem reports/live_trading/ -Filter "*.json" | Where-Object {$_.LastWriteTime -gt (Get-Date).AddHours(-24)}
```

**View latest summary:**
```powershell
$latest = Get-ChildItem reports/live_trading/daily_summary_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content $latest.FullName | ConvertFrom-Json | Format-Table
```

**Check system status:**
```bash
python validate_fee_integration.py
```

---

## ✅ SUCCESS CHECKLIST

After running scheduler tonight, verify:

- [ ] Scheduler starts without errors
- [ ] Log file created in `logs/scheduler/`
- [ ] No import errors or missing modules
- [ ] Tomorrow at 09:00 AM - first execution runs
- [ ] Trade reports appearing in `reports/live_trading/`
- [ ] Total P&L shows "Gross | Fees | Net"
- [ ] Metrics calculated (win rate, profit factor)

---

## ⚠️ TROUBLESHOOTING

**Issue: "ModuleNotFoundError"**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

**Issue: "API authentication failed"**
```bash
# Update .env with fresh session token
# Edit: .env (BREEZE_SESSION_TOKEN)
```

**Issue: "Scheduler not running"**
```bash
# Check if another instance is already running
Get-Process python | Where-Object {$_.CommandLine -like '*schedule*'}

# If found, kill it
Stop-Process -Name python -Force
```

**Issue: "Reports not being generated"**
```bash
# Check engine directly
python expanded_paper_trading_engine.py

# Look for errors in output
```

---

## 🎯 EXPECTED RESULTS (TOMORROW)

**Morning Report (09:00 AM execution):**
```
[INIT] Expanded Engine with 17 instruments
  Indices: 7, Stocks: 10
  Brokerage Plan: IVALUE

[1/17] NIFTY50: 708 candles loaded, 3 models trained
  Signal: [SELL or BUY] @ price
  Result: [TRADE EXECUTED]

[COMPLETED] All instruments processed
  Total Trades: 5-10 (depends on confidence)
  Gross P&L: ±₹XXX
  Fees: ₹YYY
  Net P&L: ±₹ZZZ
```

**Throughout the day:**
- More signals at 09:25, 10:00, 13:00, 15:00, 15:15, 15:30, 15:50
- Each execution: 30-60 seconds to complete
- Reports accumulate in `reports/live_trading/`

**End of Day Summary:**
```
Daily Paper Trading Summary (June 12):
├─ Total Executions: 9
├─ Total Trades: 45-90 (9 executions × 5-10 per run)
├─ Total Gross P&L: ±₹1,000-5,000
├─ Total Fees: ₹300-500
├─ Total Net P&L: ±₹500-4,500
├─ Win Rate: 40-50%
└─ Sharpe Ratio: 0.8-1.2
```

---

## 🚀 NEXT STEPS (AFTER TONIGHT)

**Week 1 (This Week):**
- Run paper trading for 5 consecutive days
- Monitor consistency of signals
- Track daily P&L trends

**Week 2:**
- Accumulate 30+ days of results
- Validate win rate consistency
- Compare vs backtest metrics

**Week 3:**
- Prepare live deployment
- Set risk management limits
- Create monitoring dashboard

**Week 4:**
- Go live with $5K capital
- Monitor daily PnL
- Scale strategy

---

## 📞 QUICK REFERENCE

**Start scheduler (Tonight):**
```bash
python schedule_paper_trading_tonight.py
```

**View today's logs:**
```bash
Get-Content logs/scheduler/paper_trading_schedule_*.log -Tail 100
```

**Stop scheduler:**
```bash
Ctrl+C (if running in terminal)
# OR
Stop-ScheduledTask -TaskName "PaperTradingScheduler"
```

**Run one manual execution:**
```bash
python expanded_paper_trading_engine.py
```

---

## 🎉 YOU'RE ALL SET!

**Your paper trading system with 9 daily executions is ready to go live tomorrow!**

✅ Models trained  
✅ Fees integrated  
✅ 17 instruments loaded  
✅ Scheduler configured  
✅ Reports ready  

🚀 **START SCHEDULER NOW:** `python schedule_paper_trading_tonight.py`
