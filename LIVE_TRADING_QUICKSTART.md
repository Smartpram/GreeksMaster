# Live Paper Trading with Model Retraining - Quick Start Guide

**Status:** ✅ Ready to Deploy  
**Date:** June 10, 2026  
**Features:** Live data fetching, model retraining, paper trading, logging & reports

---

## 🎯 What's Included

### Core Features
- ✅ **Live data fetching** from Breeze API (1-minute candles)
- ✅ **Real-time feature engineering** (20+ technical indicators)
- ✅ **ML model training** (XGBoost, Random Forest, Gradient Boosting)
- ✅ **Paper trading execution** with consensus signals
- ✅ **Comprehensive logging** to files
- ✅ **Detailed reports** (JSON + CSV)
- ✅ **Multiple tickers** support
- ✅ **Configurable frequency** (hourly, daily, continuous)

### Logs Generated
- `logs/live_trading/paper_trading_YYYYMMDD.log` - Main execution log
- `logs/scheduler/scheduler_YYYYMMDD.log` - Scheduler log
- **All trades, model performance, data fetching logged**

### Reports Generated
- `reports/live_trading/training_*.json` - Model performance metrics
- `reports/live_trading/training_*.csv` - Feature importance
- `reports/live_trading/trades_*.json` - Trading summary
- `reports/live_trading/trades_*.csv` - Trade details

---

## 🚀 Quick Start (30 seconds)

### Step 1: Verify Session Token Updated

Check `.env` file:
```bash
cat .env | grep BREEZE_SESSION_TOKEN
```

Confirm it shows your latest token (should not be "55915080")

### Step 2: Run Single Execution

```powershell
cd c:\Data\GreeksMaster
python live_paper_trading_with_retraining.py
```

**What it does:**
1. Fetches last 30 days of 1-min candles for NIFTY-I, BANKNIFTY-I, FINNIFTY-I
2. Generates 30+ technical features
3. Trains 3 ML models per ticker (XGBoost, RF, GB)
4. Evaluates models on test data
5. Generates trading signals
6. Executes paper trades
7. Creates JSON + CSV reports
8. Logs everything

**Time:** ~2-3 minutes per execution

### Step 3: View Logs

```powershell
# Live tail
Get-Content logs\live_trading\paper_trading_*.log -Wait

# Or view latest
Get-Content logs\live_trading\paper_trading_*.log | tail -50
```

### Step 4: View Reports

```powershell
# Training reports
dir reports\live_trading\training_*.json

# Trading reports
dir reports\live_trading\trades_*.json

# View specific report
Get-Content reports\live_trading\trades_NIFTY-I_*.json | ConvertFrom-Json
```

---

## ⏱️ Scheduling Options

### Option 1: Run Every Hour (Recommended)

```powershell
python live_trading_scheduler.py
# Then set EXECUTION_MODE = 'hourly' in the file
```

**Execution times:** :15 and :45 of every hour (market hours)

### Option 2: Run Daily

```powershell
# Edit live_trading_scheduler.py
# Set: EXECUTION_MODE = 'daily'

python live_trading_scheduler.py
```

**Execution time:** 3:30 PM (after market close)

### Option 3: Run Continuously

```powershell
# Edit live_trading_scheduler.py
# Set: EXECUTION_MODE = 'continuous'

python live_trading_scheduler.py
```

**Execution interval:** Every 1 hour

### Option 4: Run Every N Minutes

```powershell
# Edit live_trading_scheduler.py
# Set: EXECUTION_MODE = 30  # Every 30 minutes

python live_trading_scheduler.py
```

---

## 📊 Expanding Tickers

### Add More Tickers

Edit `live_paper_trading_with_retraining.py` or `live_trading_scheduler.py`:

```python
TICKERS = [
    'NIFTY-I',      # Current
    'BANKNIFTY-I',  # Current
    'FINNIFTY-I',   # Current
    'MIDCAPNIFTY-I', # Add this
    'NIFTYNXT50-I',  # Or this
]
```

**Available tickers:**
- NIFTY-I (Nifty 50)
- BANKNIFTY-I (Bank Nifty)
- FINNIFTY-I (Financial Nifty)
- MIDCAPNIFTY-I (Midcap Nifty)
- NIFTYNXT50-I (Nifty Next 50)
- NIFTYIT-I (Nifty IT)
- NIFTYPHARMA-I (Nifty Pharma)

---

## 📈 Expanding Data

### Increase Historical Lookback

Edit `live_paper_trading_with_retraining.py`:

```python
# In the `run()` method, change:
df = self.data_collector.fetch_live_data(
    ticker, 
    interval='1min', 
    lookback_days=30  # ← Change this value
)

# Options:
# lookback_days=7    # 1 week
# lookback_days=30   # 1 month (default)
# lookback_days=90   # 3 months (more data, slower)
# lookback_days=180  # 6 months (best accuracy, slower)
```

**Trade-off:**
- More data = Better model training (higher accuracy)
- But slower fetching and processing

### Change Candle Interval

```python
# Options:
df = self.data_collector.fetch_live_data(
    ticker,
    interval='1min',    # 1-minute (most data)
    # interval='5min',  # 5-minute
    # interval='15min', # 15-minute
    # interval='hourly',# Hourly
    # interval='daily', # Daily
    lookback_days=30
)
```

---

## 📋 Log Files Generated

### Daily
```
logs/live_trading/paper_trading_20260610.log
logs/scheduler/scheduler_20260610.log
```

### Per Execution
- ✓ Data fetch logs (tickers, candles, errors)
- ✓ Feature generation logs (features count, success)
- ✓ Model training logs (accuracy, metrics for each model)
- ✓ Signal generation logs (confidence, consensus)
- ✓ Trade execution logs (buy/sell, price, quantity)
- ✓ Report generation logs (files saved)

### Log Format
```
2026-06-10 14:30:15 - __main__ - INFO - [LIVE DATA] Fetching NIFTY-I 1min candles (last 30 days)
2026-06-10 14:30:45 - __main__ - INFO - [LIVE DATA] ✓ Fetched 8400 candles for NIFTY-I
2026-06-10 14:30:50 - __main__ - INFO - [FEATURES] Generated 31 features for 8340 candles
2026-06-10 14:31:20 - __main__ - INFO - [TRAINING] XGBoost Accuracy: 0.5340
2026-06-10 14:31:45 - __main__ - INFO - [TRAINING] Random Forest Accuracy: 0.5210
2026-06-10 14:32:10 - __main__ - INFO - [TRAINING] Gradient Boosting Accuracy: 0.5280
2026-06-10 14:32:15 - __main__ - INFO - [TRADE] BUY 32 NIFTY-I @ 22650.50 (confidence: 65.42%)
2026-06-10 14:32:20 - __main__ - INFO - [REPORT] ✓ Training report saved: reports/live_trading/training_NIFTY-I_20260610_143220.json
```

---

## 📊 Reports Generated

### Training Report (JSON)
```json
{
  "timestamp": "2026-06-10T14:32:20",
  "ticker": "NIFTY-I",
  "model_results": {
    "xgboost": {
      "accuracy": 0.5340,
      "precision": 0.5450,
      "recall": 0.5210,
      "f1": 0.5328
    },
    "random_forest": {
      "accuracy": 0.5210,
      ...
    }
  },
  "best_model": "xgboost",
  "best_accuracy": 0.5340
}
```

### Trading Report (JSON)
```json
{
  "timestamp": "2026-06-10T14:32:25",
  "ticker": "NIFTY-I",
  "total_trades": 3,
  "buy_trades": 2,
  "sell_trades": 1,
  "total_volume": 95,
  "avg_confidence": 0.6542,
  "high_confidence_trades": 2
}
```

### Trades CSV
```csv
timestamp,ticker,action,quantity,price,amount,confidence,consensus
2026-06-10 14:32:15,NIFTY-I,BUY,32,22650.50,724816,0.6542,1
2026-06-10 14:32:30,NIFTY-I,SELL,32,22651.75,724856,0.5892,0
```

---

## 🔧 Configuration Options

### Model Parameters

Edit `live_paper_trading_with_retraining.py`, `LiveModelTrainer.train_models()`:

```python
# XGBoost
xgb_model = XGBClassifier(
    n_estimators=100,        # Number of trees
    max_depth=7,             # Tree depth
    learning_rate=0.1,       # Learning rate
    random_state=42
)

# Random Forest
rf_model = RandomForestClassifier(
    n_estimators=100,        # Number of trees
    max_depth=10,            # Tree depth
    random_state=42
)
```

### Trading Parameters

Edit `live_paper_trading_with_retraining.py`, `PaperTradingExecutor.execute_trade()`:

```python
# Confidence threshold (0.5 = 50%)
if signal['confidence'] < 0.55:  # ← Adjust this
    self.logger.debug(f"[TRADE] Low confidence, skipping")
    return None

# Position size (% of portfolio)
trade = self.paper_trader.execute_trade(
    ticker, 
    signal, 
    position_size=0.1  # 10% of portfolio ← Adjust this
)
```

---

## 📈 Features Generated (30+)

### Price Features
- Close price, Open, High, Low
- Log returns
- High/Low ratio
- Close/Open ratio

### Volume Features
- Volume
- Volume MA5
- Volume ratio

### Moving Averages
- SMA 5, 10, 20, 50
- EMA 5, 10, 20, 50

### Momentum Indicators
- RSI (14)
- MACD + Signal + Histogram
- Momentum (10-bar)

### Volatility
- Bollinger Bands (20, 2 std)
- Volatility (20-bar std)

### Total: 31 features per candle

---

## ✅ Daily Monitoring Checklist

### Every Hour (If Running Hourly)
```powershell
# Check if execution happened
Get-Content logs\live_trading\paper_trading_*.log | tail -20

# Any errors?
Select-String -Path logs\live_trading\*.log -Pattern "ERROR"
```

### Every Morning
```powershell
# Previous day executions
(Get-Content logs\live_trading\*.log | Select-String "EXECUTION").Count

# Successful?
Select-String -Path logs\live_trading\*.log -Pattern "SUCCESS"

# Model accuracy
Select-String -Path logs\live_trading\*.log -Pattern "Accuracy"
```

### Weekly
```powershell
# Total trades
(Get-Content logs\live_trading\*.log | Select-String "TRADE").Count

# Success rate
(Get-Content logs\live_trading\*.log | Select-String "SUCCESS").Count

# Model performance trend
dir reports\live_trading\training_*.json
```

---

## 🚨 Troubleshooting

### Issue: "Failed to fetch data"

**Cause:** Session token expired  
**Fix:** Update `.env` with new token from https://api.icicidirect.com/apiuser/login

```bash
# Update in .env
BREEZE_SESSION_TOKEN=your_new_token_here
```

### Issue: "No data received"

**Cause:** Ticker not trading or wrong symbol  
**Fix:** Verify ticker symbol is correct

```python
# Valid tickers
'NIFTY-I', 'BANKNIFTY-I', 'FINNIFTY-I'
# Not valid
'NIFTY', 'BANKNIFTY', 'NIFTY50'
```

### Issue: "Model accuracy < 50%"

**Cause:** Random guessing, model not learning  
**Fix:** 
- Increase lookback_days (more data)
- Adjust model parameters
- Check if features are meaningful

### Issue: Logs not created

**Cause:** Permission issue or directory missing  
**Fix:**
```powershell
# Create directories manually
mkdir logs\live_trading
mkdir logs\scheduler
mkdir reports\live_trading
```

---

## 📊 Performance Expectations

### Data Fetching
- 1,000-10,000 candles per ticker
- ~30-60 seconds per ticker

### Feature Engineering
- 30+ features per candle
- ~10-20 seconds per ticker

### Model Training
- 3 models (XGB, RF, GB) per ticker
- ~30-60 seconds per ticker

### Total Execution Time
- **Per ticker:** 2-3 minutes
- **All 3 tickers:** 6-9 minutes

### Reports
- Generated automatically after each execution
- JSON + CSV formats
- Stored in `reports/live_trading/`

---

## 🎯 Next Steps

### Immediate
1. ✓ Update session token in `.env`
2. ✓ Run single execution: `python live_paper_trading_with_retraining.py`
3. ✓ Check logs: `Get-Content logs\live_trading\*.log`
4. ✓ Review reports: `dir reports\live_trading\`

### This Week
1. Run hourly: `python live_trading_scheduler.py`
2. Monitor logs daily
3. Review model performance
4. Track trading volume

### This Month
1. Evaluate trading edge
2. Adjust parameters based on performance
3. Expand tickers if needed
4. Optimize for better accuracy

---

## 📞 Quick Reference

### Commands
```powershell
# Single run
python live_paper_trading_with_retraining.py

# Scheduled run
python live_trading_scheduler.py

# View logs
Get-Content logs\live_trading\*.log -Wait

# View reports
dir reports\live_trading\*.json

# Count trades
(Get-Content logs\live_trading\*.log | Select-String "TRADE").Count
```

### File Locations
```
Logs:    c:\Data\GreeksMaster\logs\live_trading\
Reports: c:\Data\GreeksMaster\reports\live_trading\
Models:  c:\Data\GreeksMaster\app\ml_models\live\
Data:    c:\Data\GreeksMaster\data\live\
```

---

## ✨ You're All Set!

**Start with:**
```powershell
python live_paper_trading_with_retraining.py
```

**All logs, reports, and models are automatically generated and saved!**

🚀 Happy trading!
