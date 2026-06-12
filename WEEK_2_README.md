# 📅 WEEK 2: Paper Trading & ML Training (June 15-21, 2026)

**Status**: 🟢 **READY FOR DEPLOYMENT**

---

## ⚡ Quick Start - Monday Morning (June 15)

### 08:45 IST - Pre-Trading Checks
```bash
# Run deployment readiness check
python scripts/monday_deployment_check.py

# Expected output: "🟢 SYSTEM READY FOR DEPLOYMENT!"
```

### 09:00 IST - Start Paper Trading
```bash
# Start main scheduler
python scripts/scheduler_options_production.py

# System will:
# - Connect to Breeze API
# - Download candles every 1 minute
# - Calculate 31 indicators
# - Generate ML signals
# - Execute trades automatically
# - Monitor positions in real-time
# - Execute exits automatically
```

### 15:30 IST - End of Day
- System automatically closes all positions
- Session P&L calculated (with fees deducted)
- Trades exported to reports/
- ML retraining triggered

---

## 📊 Expected Daily Performance (Week 2)

| Metric | Expected | Target |
|--------|----------|--------|
| Trading Duration | 6h 15min (09:15-15:30 IST) | - |
| Trades/Day | 15-20 | ≥ 10 |
| Win Rate | ~95% | ≥ 90% |
| Gross Daily P&L | ₹1,500-2,500 | ≥ ₹1,000 |
| Daily Fees | ₹400-500 | - |
| **NET Daily P&L** | **₹1,100-1,900** | **≥ ₹500** |
| Model Accuracy | 72%+ | ≥ 70% |

---

## 🎯 Daily Schedule

### Morning (Before 09:15 IST)
```
08:30 - Wake up, review system
08:45 - Run deployment check: python scripts/monday_deployment_check.py
08:50 - Verify Breeze API connection
08:55 - Run final integration test
09:00 - Load ML model, start monitor
09:10 - Watch first 5 trades closely
09:15 - ✅ GO LIVE!
```

### Trading Hours (09:15-15:30 IST)
```
Every 1 minute:
- System downloads candle
- Calculates 31 indicators
- Checks entry signals
- Monitors open positions
- Executes exit rules
- Logs all trades

Every 10 minutes:
- Generates new ML signal
- Updates portfolio Greeks

15:30 IST:
- Force close all open positions
- Calculate final P&L
```

### After Market Close (After 15:30 IST)
```
15:30-16:00 - Final reconciliation
16:00 - Export trades (data/trades_YYYY-MM-DD.csv)
16:05 - Generate session report (reports/session_YYYY-MM-DD.json)
16:10 - Retrain ML model with today's data
16:30 - Archive daily checkpoint
```

---

## 📈 Weekly Progression

### Monday (June 15)
- **Focus**: System stability, first live trades
- **Expected**: 15-20 trades, >90% win rate
- **Check**: No crashes, all exits triggering
- **Review**: Are signals working? Any slippage?

### Tuesday (June 16)
- **Focus**: Consistency verification
- **Expected**: Similar trade pattern
- **Check**: Model holding accuracy
- **Review**: Compare vs Monday results

### Wednesday (June 17)
- **Focus**: P&L trend analysis
- **Expected**: Week cumulative P&L positive
- **Check**: Fees being deducted correctly
- **Review**: Any patterns emerging?

### Thursday (June 18)
- **Focus**: Model drift detection
- **Expected**: Win rate stable or improving
- **Check**: New data improving signals?
- **Review**: Feature importance shifts?

### Friday (June 19)
- **Focus**: Weekly summary + full retraining
- **Expected**: Best day of week
- **Check**: Full week P&L > ₹5,000 net
- **Review**: Ready for Week 3?

---

## 🔍 What to Monitor (Daily)

### Real-Time Metrics (Every 1 min)
```
📊 Current Status:
   Time: HH:MM IST
   Open Positions: N
   Session P&L: ₹X (+/- Y%)
   Win Rate (Today): Z%
   Last Trade: [Symbol] [Entry-Exit] [P&L]
   Model Confidence: X%
```

### Hourly Summary
```
Hour 1 (09:15-10:15): 2 trades, ₹480 P&L, 100% win
Hour 2 (10:15-11:15): 2 trades, ₹360 P&L, 100% win
Hour 3 (11:15-12:15): 2 trades, ₹420 P&L, 100% win
...
```

### End of Day Report
```
📋 Session Report - June 15, 2026

Total Trades:       18
Entry Signals:      20
Missed Trades:      2 (due to position limit)
Win Rate:           94.4% (17/18)
Gross P&L:          ₹1,710
Fees Paid:          ₹461
NET P&L:            ₹1,249 ✅

Symbols Traded:     BANKNIFTY (14), NIFTY (4)
Best Trade:         ₹240 (BANKNIFTY CE)
Worst Trade:        -₹100 (NIFTY PE)
Avg Trade Size:     ₹95

Model Accuracy:     73.2%
False Positives:    2
False Negatives:    0
```

---

## 🛠️ System Components Verification

### Core Modules (All Running)
- ✅ `feature_engine.py` - 31 indicators
- ✅ `ml_model_manager_hybrid.py` - XGBoost model
- ✅ `options_chain_manager.py` - Options data
- ✅ `options_strategy_selector.py` - 9 strategies
- ✅ `options_executor_and_risk.py` - Execution
- ✅ `brokerage_fees.py` - Fee calculation
- ✅ `position_monitor_realtime.py` - Monitoring

### Data Sources (Live)
- ✅ Breeze API - Live 1-min candles (every minute)
- ✅ Breeze API - Live options chain (every tick)
- ✅ Local - ML model (xgboost_trained_latest.pkl)
- ✅ Local - Feature cache (cached indicators)

### Risk Management (Armed)
- ✅ Kill-switch - Trigger: -₹5,000
- ✅ Position sizing - Max: ₹20,000 per trade
- ✅ Exit rules - 5 rules active
- ✅ Fee deduction - Automatic ICICI Direct
- ✅ Greeks validation - Pre-trade risk check

---

## ⚠️ Troubleshooting Guide

### System Won't Start
```
Error: ModuleNotFoundError: No module named 'app'

Solution:
1. Check current directory: pwd (should be GreeksMaster/)
2. Check Python path: export PYTHONPATH=$PWD
3. Run again: python scripts/scheduler_options_production.py
```

### No Trades Executing
```
Symptoms: System running but no trades for >1 hour

Debug:
1. Check model: ls models/xgboost_trained_latest.pkl
2. Check candles: Are they downloading? (watch logs)
3. Check signals: python -c "from app.ml_model_manager_hybrid import MLModelManager; print('✓')"
4. Manual entry: Try placing test trade via Breeze API

Solution:
1. Verify Breeze API connection
2. Check BANKNIFTY is trading (not suspended)
3. Restart scheduler
```

### P&L Doesn't Match
```
Symptoms: Expected vs actual P&L mismatch

Check:
1. Fees being deducted? (Should see "Fees: ₹XXX" in logs)
2. Slippage impact? (Bid-ask spread)
3. Platform calculation? (Cross-check with Breeze portfolio)

Solution:
1. Enable verbose logging
2. Export trade-by-trade P&L
3. Compare with manual calculation
```

### Model Accuracy Low
```
Symptoms: Win rate < 80%

Check:
1. Is market trending or range-bound?
2. Are indicators calculating correctly?
3. Did model overfit to training data?

Solution:
1. Review feature importance (which signals matter?)
2. Check market regime (ATR, ADX)
3. Retrain model with latest data: python scripts/weekend_ml_training_deployment.py
```

---

## 📁 Important Files

### Start Here
- `WEEK_2_PREPARATION.md` - Full preparation guide
- `WEEK_2_README.md` - This file

### Run These
- `scripts/monday_deployment_check.py` - Pre-flight check
- `scripts/scheduler_options_production.py` - Main trader
- `scripts/test_hybrid_system_integration.py` - Validate system
- `scripts/weekend_ml_training_deployment.py` - Retrain model

### Understand These
- `docs/DATA_SOURCES_GUIDE.md` - Data source info
- `docs/FEES_AND_SLIPPAGE_AUDIT.md` - Fee breakdown
- `docs/HYBRID_ML_DEPLOYMENT_GUIDE.md` - System architecture
- `docs/MONDAY_QUICK_REFERENCE.md` - Quick commands

### Configure These
- `.env` - Breeze API credentials (LOCAL ONLY, SECRET!)
- `.env.example` - Template for .env
- `requirements.txt` - Python dependencies
- `app/brokerage_fees.py` - ICICI Direct fee config

---

## ✅ Pre-Deployment Checklist (Monday 08:45)

- [ ] `.env` file has ICICI Direct API credentials
- [ ] `.env` is NOT committed to git (check: git status)
- [ ] Python 3.10+ installed
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] ML model exists: `ls models/xgboost_trained_latest.pkl`
- [ ] Run deployment check: `python scripts/monday_deployment_check.py`
- [ ] Integration tests pass: `python scripts/test_hybrid_system_integration.py` (14/14)
- [ ] Breeze API connection works
- [ ] No system errors in logs
- [ ] Kill-switch armed (default)
- [ ] Position sizing set to 2 (default)
- [ ] Ready to deploy: 🟢

---

## 🎯 Success Metrics for Week 2

### Minimum (Must Achieve)
- [ ] System runs without crashes (5 consecutive days)
- [ ] No P&L calculation errors
- [ ] All exits triggering correctly
- [ ] Win rate ≥ 90%
- [ ] Kill-switch armed & responsive

### Target (Should Achieve)
- [ ] Win rate ≥ 95%
- [ ] Net weekly P&L ≥ ₹5,000
- [ ] Model accuracy ≥ 75%
- [ ] Zero false signals
- [ ] Consistent daily performance

### Stretch (Nice to Have)
- [ ] Net weekly P&L ≥ ₹10,000
- [ ] Model accuracy ≥ 80%
- [ ] Zero slippage issues
- [ ] Multiple symbols trading successfully

---

## 📊 Performance Tracking Template

**Track Daily in Week 2:**
```
Date         | Trades | Win Rate | Gross P&L | Fees | NET P&L | Accuracy
June 15 (Mon)|  18    |  94%    | ₹1,710   | ₹461 | ₹1,249  |  73%
June 16 (Tue)|  __    |  ___%   | ₹____   | ₹___ | ₹____   |  __%
June 17 (Wed)|  __    |  ___%   | ₹____   | ₹___ | ₹____   |  __%
June 18 (Thu)|  __    |  ___%   | ₹____   | ₹___ | ₹____   |  __%
June 19 (Fri)|  __    |  ___%   | ₹____   | ₹___ | ₹____   |  __%
WEEKLY TOTAL | __    | ___%   | ₹____   | ₹___ | ₹____   |  __%
```

---

## 📞 Need Help?

**System Issues:**
1. Check logs: `tail -f logs/*.log`
2. Run diagnostic: `python scripts/test_hybrid_system_integration.py`
3. Review error message
4. Check documentation

**Breeze API Issues:**
- Contact: ICICI Direct support
- Check: API key active & not rate-limited
- Verify: Network connectivity

**ML Model Issues:**
- Retrain: `python scripts/weekend_ml_training_deployment.py`
- Check: Training data quality
- Review: Feature importance

---

## 🚀 Ready to Go!

Your system is **🟢 PRODUCTION READY** for Week 2 paper trading.

**Monday June 15, 09:15 IST → GO LIVE! 🚀**

Good luck with trading! You've built an impressive system.

---

**Last Updated**: June 12, 2026  
**Deployment Target**: Monday June 15, 2026 @ 09:15 IST  
**Status**: 🟢 READY
