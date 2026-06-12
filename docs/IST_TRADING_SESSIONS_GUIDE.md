# Live Paper Trading - IST Trading Sessions Schedule

## 📅 NSE Trading Day Structure (IST)

```
┌─────────────────────────────────────────────────────────────────┐
│                   NSE TRADING DAY (IST)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PRE-OPEN SESSION          REGULAR TRADING      POST-CLOSING   │
│  09:00 - 09:15 AM          09:15 AM - 03:30 PM  03:40 - 04:00 PM
│  ┌─────────────────────────────────────────────┐  ┌──────────┐│
│  │ Orders matched to      │ Continuous trading  │  │ Closing  ││
│  │ determine opening      │ Buy/Sell Orders     │  │ Orders   ││
│  │ price                  │                     │  │          ││
│  └─────────────────────────────────────────────┘  └──────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🤖 Automated Paper Trading Schedule

Your live paper trading system is now scheduled to execute **FIVE times per day** aligned with NSE sessions:

| Time (IST) | Session | Purpose | Action |
|-----------|---------|---------|--------|
| **09:00 AM** | Pre-Open | Prepare models | Load data, train models, warm up |
| **09:15 AM** | Market Open | First Signals | Generate opening signals |
| **01:00 PM** | Mid-Session | Retrain | Update models with intra-day data |
| **03:30 PM** | Close | Final Signals | End-of-day trading signals |
| **03:45 PM** | Post-Close | Post-Closing | Closing session execution |

## ⚙️ What Happens at Each Execution

```
EACH EXECUTION (15-20 seconds):

1. Load Data
   ├─ 719 candles from local CSV (historical baseline)
   └─ 570+ recent candles from Breeze API (live market data)

2. Feature Engineering
   ├─ 31 technical indicators calculated
   ├─ RSI, MACD, Bollinger Bands, ATR, ADX, Stochastic, etc.
   └─ Generate 26 features per ticker

3. Model Training
   ├─ XGBoost trained and evaluated
   ├─ Random Forest trained and evaluated
   └─ Gradient Boosting trained and evaluated

4. Signal Generation
   ├─ Consensus voting: 2+ models agree = SIGNAL
   ├─ Confidence score calculated
   └─ Action: BUY or SELL

5. Paper Trade Execution
   ├─ Record trade with timestamp
   ├─ Position size: 10% of capital (configurable)
   └─ Save to reports

6. Report Generation
   ├─ Training metrics (JSON)
   ├─ Trading signals (JSON)
   └─ Log to file
```

## 📊 Expected Daily Output

### Per Execution
```
Processing 5 tickers × 5 executions = 25 total paper trades

Example:
09:00 AM: NIFTY50 BUY (conf: 0.67), BANKNIFTY SELL (conf: 1.00), FINNIFTY SELL (conf: 1.00)
09:15 AM: NIFTY50 SELL (conf: 0.67), BANKNIFTY BUY (conf: 0.67), ...
01:00 PM: [Mid-day retrain] Updated models
03:30 PM: [End of trading] Final signals
03:45 PM: [Post-closing] Closing session orders
```

### Daily Files Generated
```
logs/
├── scheduler/
│   ├── scheduler_20260610.log          (Main scheduler log)
│   └── background_start_*.log          (Startup info)
└── live_trading/
    └── paper_trading_20260610.log      (All trading activities)

reports/live_trading/
├── training_NIFTY50_090000.json        (Pre-Open: Model metrics)
├── training_NIFTY50_091500.json        (Market Open: Model metrics)
├── training_NIFTY50_130000.json        (Mid-Day: Model metrics)
├── training_NIFTY50_153000.json        (Close: Model metrics)
├── training_NIFTY50_154500.json        (Post-Close: Model metrics)
├── trades_NIFTY50_090000.json          (Trading signals)
├── trades_NIFTY50_091500.json
├── trades_NIFTY50_130000.json
├── trades_NIFTY50_153000.json
└── trades_NIFTY50_154500.json

Plus similar files for BANKNIFTY, FINNIFTY, etc.
```

## 🚀 START THE SCHEDULER TODAY

### Option 1: Direct Python (Recommended)
```bash
cd C:\Data\GreeksMaster
python schedule_live_trading_today.py
```

**The scheduler will:**
- Start immediately
- Display execution times in logs
- Run 5 times daily automatically
- Continue until you press Ctrl+C

### Option 2: Background PowerShell
```powershell
cd C:\Data\GreeksMaster
powershell -ExecutionPolicy Bypass -File start_scheduler_simple.ps1
```

### Option 3: Task Scheduler (Windows - Runs When Locked)

Create a batch file `run_scheduler.bat`:
```batch
@echo off
cd /d C:\Data\GreeksMaster
python schedule_live_trading_today.py
```

Then in Windows Task Scheduler:
1. Create Basic Task → "Live Paper Trading"
2. Trigger: "At system startup"
3. Action: Start program: `C:\path\to\run_scheduler.bat`
4. Check: "Run with highest privileges"
5. Check: "Run whether user is logged in or not"

## 📈 Live Monitoring

### Watch Logs in Real-Time
```powershell
Get-Content logs\scheduler\scheduler_*.log -Tail 50 -Wait
```

### Check Next Scheduled Execution
```powershell
# View the log to see scheduled times
Get-Content logs\scheduler\scheduler_*.log | Select-String "at" | Select-Object -Last 5
```

### View Latest Trading Results
```powershell
# Show most recent trade signals
Get-Content reports\live_trading\trades_*.json | ConvertFrom-Json | Format-Table -AutoSize
```

## 🎯 Trading Session Details

### 09:00 AM - PRE-OPEN SESSION
**Purpose**: Model preparation and validation
- Load full dataset (historical + latest)
- Train/retrain all models
- Generate preliminary signals
- Warm up ML models
- **Use Case**: Debug models, validate data quality

### 09:15 AM - MARKET OPEN
**Purpose**: First trading signals at market open
- Generate consensus signals
- Execute first batch of paper trades
- Capture opening momentum
- **Use Case**: Intraday swing trades, quick momentum plays

### 01:00 PM - MID-SESSION RETRAIN
**Purpose**: Update models with 4+ hours of trading data
- Retrain on fresh market conditions
- Recalibrate indicators
- Generate updated signals
- **Use Case**: Mid-day adjustment, catch trend changes

### 03:30 PM - REGULAR TRADING CLOSE
**Purpose**: Final signals before market close
- Generate end-of-day signals
- Prepare for closing auction
- Finalize positions
- **Use Case**: End-of-day swing trades, position closing

### 03:45 PM - POST-CLOSING SESSION
**Purpose**: Post-closing order execution
- Generate closing session signals
- Place closing orders at fixed price
- Record end-of-day execution
- **Use Case**: Close positions, set closing orders

## 📊 Configuration Options

### Run ALL 5 Sessions (Default)
Already configured in `schedule_live_trading_today.py` with `EXECUTION_MODE = 'trading_sessions'`

### Run ONLY AT MARKET CLOSE (15:30)
```python
EXECUTION_MODE = 'daily'
# Only runs at 15:30 IST
```

### Run HOURLY (During Trading Hours)
```python
EXECUTION_MODE = 'hourly'
# Runs at :15 and :45 every hour (09:15, 10:15, 11:15... 15:15, 15:45)
```

### Run EVERY N MINUTES
```python
EXECUTION_MODE = 'interval'
INTERVAL_MINUTES = 30  # Every 30 minutes
```

### Custom Execution Times
Edit `schedule_live_trading_today.py`, modify `schedule_trading_sessions()` method:
```python
schedule.every().day.at("YOUR_TIME_HH:MM").do(self.run_trading_pipeline)
```

## 📋 Sample Execution Log

```
[SCHEDULER] Live Trading Paper Pipeline - CONTINUOUS MODE
Started: 2026-06-10 09:00:00

[SCHEDULER] Setting up TRADING SESSIONS execution (IST)
  09:00 AM - Pre-Open Session (prepare models)
  09:15 AM - Regular Trading Starts (first signals)
  01:00 PM - Mid-Day Update (retrain models)
  03:30 PM - Regular Trading Ends (final signals)
  03:45 PM - Post-Closing Session (closing signals)

================================================================================
[EXECUTION #1] Starting live trading pipeline
Time: 2026-06-10 09:00:00
================================================================================

[PIPELINE] Processing NIFTY50...
  [TRAINED] xgboost: Acc=0.577, Prec=0.583, Rec=0.590, F1=0.587
  [SIGNAL] SELL (confidence: 0.67)
  [TRADE] NIFTY50 SELL (size: 10%)

[PIPELINE] Processing BANKNIFTY...
  [TRAINED] xgboost: Acc=0.493, Prec=0.523, Rec=0.584, F1=0.552
  [SIGNAL] SELL (confidence: 1.00)
  [TRADE] BANKNIFTY SELL (size: 10%)

================================================================================
[SUCCESS] Execution #1 completed successfully
[NEXT EXECUTION] 2026-06-10 09:15 AM
```

## 🔄 Daily Trading Workflow

```
06:00 AM
  └─ Prep: Update session token if needed

09:00 AM ← EXECUTION #1
  ├─ Pre-Open: Models trained and ready
  ├─ Signals: Generated
  └─ Status: All tickers processed

09:15 AM ← EXECUTION #2
  ├─ Market Opens
  ├─ First signals generated
  └─ Trading begins

10:15 AM - 02:45 PM
  ├─ Continuous trading
  ├─ Models updated hourly (if in hourly mode)
  └─ Intra-day adjustments

01:00 PM ← EXECUTION #3
  ├─ Mid-session retrain
  ├─ Adjust models for afternoon
  └─ New signals generated

03:30 PM ← EXECUTION #4
  ├─ Market closes
  ├─ Final signals
  └─ End-of-day positions

03:45 PM ← EXECUTION #5
  ├─ Post-closing session
  ├─ Closing orders
  └─ Final execution

04:00 PM
  ├─ Market closes
  └─ Day complete

Evening
  ├─ Review logs
  ├─ Analyze reports
  └─ Plan for next day
```

## ✅ Verify Everything is Running

```powershell
# Check scheduler process
Get-Process python | Where-Object {$_.CommandLine -like '*schedule_live_trading*'}

# Check latest log entry
Get-Content logs\scheduler\scheduler_*.log | Select-Object -Last 1

# Count today's reports
(Get-ChildItem reports\live_trading\*.json | Where-Object {$_.LastWriteTime -gt (Get-Date).AddHours(-24)}).Count
```

## 🛑 STOP THE SCHEDULER

```powershell
# Find the process
$proc = Get-Process python | Where-Object {$_.CommandLine -like '*schedule*'}

# Stop it
Stop-Process -Id $proc.Id -Force

# Verify stopped
Get-Process python | Where-Object {$_.CommandLine -like '*schedule*'}
```

## 📞 Troubleshooting

| Issue | Solution |
|-------|----------|
| No logs created | Check if scheduler started, verify Python path |
| Missed execution | Check system time is correct (IST), verify .env token |
| No trading signals | Models may not be converging, check accuracy in logs |
| High model errors | Session token expired, update .env file |
| Reports not saved | Check reports/live_trading/ folder permissions |

---

**Status**: ✅ Ready to execute
**Trading Sessions**: 5 daily (09:00, 09:15, 13:00, 15:30, 15:45 IST)
**Market Hours**: 09:15 AM - 03:30 PM IST
**Version**: 2.0 - IST Trading Sessions Aligned

🚀 **Ready to start trading!**
