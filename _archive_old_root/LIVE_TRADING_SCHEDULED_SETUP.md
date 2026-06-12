# Live Paper Trading - Scheduled Execution Setup

## 🎯 Overview
Your live paper trading system is now configured to run automatically with expanded tickers!

## 📊 Current Tickers
- ✅ NIFTY50 (Nifty 50 Index)
- ✅ BANKNIFTY (Bank Index)
- ✅ FINNIFTY (Financial Index)
- ⚠️ NIFTYNXT50 (Next 50 - optional, depends on data availability)
- ⚠️ MIDCAPNIFTY (Midcap Index - optional, depends on data availability)

## 🚀 Quick Start - Option 1: PowerShell (Recommended)

```powershell
# Run this command to start the scheduler in background
cd C:\Data\GreeksMaster
.\Start-LiveTradingScheduler.ps1
```

This will:
- Start the scheduler as a background process
- Run daily at 15:30 IST
- Log all activities to `logs\scheduler\`
- Generate reports in `reports\live_trading\`
- Continue running until you manually stop it

## 🚀 Quick Start - Option 2: Batch File

```batch
start_live_trading_today.bat
```

## 🚀 Quick Start - Option 3: Command Line

```bash
python schedule_live_trading_today.py
```

## 📋 Configuration Options

Edit `schedule_live_trading_today.py` line 111-114 to change execution mode:

```python
EXECUTION_MODE = 'daily'  # Options: 'hourly', 'daily', 'continuous', 'interval'
INTERVAL_MINUTES = 60     # If using interval mode
DAILY_TIME = "15:30"      # IST time for daily mode
```

### Execution Modes:

1. **`daily`** (Default)
   - Runs once per day at 15:30 IST
   - Best for end-of-day analysis
   - Command: Keep scheduler running

2. **`hourly`**
   - Runs at :15 and :45 every hour
   - Good for frequent retraining
   - Use for: Intraday trading

3. **`interval`**
   - Runs every N minutes
   - Customize with `INTERVAL_MINUTES`
   - Example: 30 min intervals for rapid updates

4. **`continuous`**
   - Runs immediately, then hourly
   - Use for: Starting fresh, testing

## 📊 What Happens Each Execution

For each ticker:
1. ✅ Load 719 candles from local training data
2. ✅ Fetch ~570 recent candles from Breeze API
3. ✅ Combine = ~1,000+ total candles
4. ✅ Generate 31 technical indicators
5. ✅ Train 3 ML models (XGBoost, Random Forest, Gradient Boosting)
6. ✅ Generate consensus trading signals
7. ✅ Execute paper trades
8. ✅ Save reports (JSON format)

**Total time per execution: ~15-20 seconds**

## 📁 Output Locations

### Logs
```
logs/scheduler/scheduler_20260610.log           # Main scheduler log
logs/scheduler/output_*.log                      # Process output
logs/scheduler/errors_*.log                      # Any errors
logs/live_trading/paper_trading_20260610.log    # Trading logs
```

### Reports (JSON)
```
reports/live_trading/
├── training_NIFTY50_*.json                     # Model metrics
├── training_BANKNIFTY_*.json
├── training_FINNIFTY_*.json
├── trades_NIFTY50_*.json                       # Trading signals
├── trades_BANKNIFTY_*.json
└── trades_FINNIFTY_*.json
```

## 🔍 Monitoring

### View Live Logs (PowerShell)
```powershell
Get-Content logs\scheduler\scheduler_20260610.log -Tail 50 -Wait
```

### View Latest Training Report
```powershell
Get-Content reports\live_trading\training_*.json | ConvertFrom-Json | Format-Table -AutoSize
```

### Check if Scheduler is Running
```powershell
Get-Process python | Where-Object {$_.CommandLine -like '*schedule_live_trading*'}
```

### Stop the Scheduler
```powershell
Stop-Process -Name python -Force  # Stops ALL Python processes
# OR
Stop-Process -Id <PID> -Force     # Stop specific process
```

## 📈 Expected Results Per Execution

### Training Results
- XGBoost Accuracy: 50-58%
- Random Forest Accuracy: 45-55%
- Gradient Boosting Accuracy: 47-53%

### Trading Signals
- Consensus signal when 2+ models agree
- Confidence score: 0.5-1.0
- Action: BUY or SELL based on majority vote

### Reports Include
- Model metrics (Accuracy, Precision, Recall, F1)
- Feature list (26 indicators)
- Trade signals with confidence
- Timestamp of each execution

## ⚙️ Advanced Configuration

### Change Daily Execution Time
Edit `schedule_live_trading_today.py`:
```python
DAILY_TIME = "16:00"  # Change from 15:30 to 16:00 IST
```

### Add More Tickers
Edit `live_paper_trading_hybrid.py`:
```python
TICKERS = [
    ('NIFTY50', 'NIFTY'),
    ('BANKNIFTY', 'BANKNIFTY'),
    ('FINNIFTY', 'FINNIFTY'),
    ('YOUR_TICKER', 'STOCK_CODE'),  # Add here
]
```

### Adjust Position Size
Edit `live_paper_trading_hybrid.py`, method `run()`:
```python
trade = self.paper_trader.execute_trade(ticker_name, signal, position_size=0.1)
# Change 0.1 (10%) to any value you want (0.05 = 5%, 0.2 = 20%)
```

## 🔐 Security Notes

- Session token is read from `.env` file
- Token is loaded at startup, refreshed if expired
- All trades are PAPER trades (no real execution)
- Reports saved locally in `reports/` directory

## 📞 Troubleshooting

### Scheduler doesn't start
- Check Python path: `where python`
- Verify .env file has session token
- Check logs: `logs/scheduler/errors_*.log`

### No data fetched
- Session token might be expired
- Update `.env` with fresh token from Breeze login
- Check API limits (may be rate limited)

### Models not training
- Ensure training CSV files exist in `data/training/`
- Verify column names: timestamp, open, high, low, close, volume
- Check Breeze API is authenticated

### Task Scheduler Integration (Windows)

To make it run even when machine is locked:

1. Create a batch file wrapper: `run_scheduler.bat`
2. Open Task Scheduler
3. Create Basic Task:
   - Name: Live Paper Trading
   - Trigger: Daily at 15:30
   - Action: Start program: `C:\Windows\System32\cmd.exe /c C:\Path\To\run_scheduler.bat`
   - Check: "Run with highest privileges"
   - Check: "Run whether user is logged in or not"

## 📊 Example Output

```
[EXECUTION #1] Starting live trading pipeline
Time: 2026-06-10 23:00:00

[PIPELINE] Processing NIFTY50...
  [TRAINED] xgboost: Acc=0.577, Prec=0.583, Rec=0.538, F1=0.560
  [TRAINED] rf: Acc=0.538, Prec=0.542, Rec=0.500, F1=0.520
  [SIGNAL] SELL (confidence: 0.67)
  [TRADE] NIFTY50 SELL (size: 10%)

[PIPELINE] Processing BANKNIFTY...
  [TRAINED] xgboost: Acc=0.493, Prec=0.523, Rec=0.584, F1=0.552
  [SIGNAL] SELL (confidence: 1.00)
  [TRADE] BANKNIFTY SELL (size: 10%)

PIPELINE COMPLETE
[SUCCESS] Paper trading completed
```

## 🎯 Next Steps

1. **Start scheduler now**: Run PowerShell script above
2. **Monitor execution**: Check logs in `logs/scheduler/`
3. **Review reports**: Check JSON files in `reports/live_trading/`
4. **Tune parameters**: Adjust tickers, time, position size as needed
5. **Integrate with live trading**: When ready, modify to execute real trades

---
**Status**: ✅ Ready for scheduled execution
**Last Updated**: 2026-06-10 23:00 IST
**Version**: 1.0 - Hybrid Data + Expanded Tickers
