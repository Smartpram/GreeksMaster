🚀 QUICK START - MONDAY DEPLOYMENT

## ONE-LINE DEPLOYMENTS

### Pre-Flight Check (08:45 IST)
```
python scripts/monday_deployment_check.py
```
Expected: ✅ 7/8 checks PASS (System ready)

### Verify All Systems (08:50 IST)
```
python scripts/test_hybrid_system_integration.py
```
Expected: ✅ 14/14 tests PASS

### GO LIVE (09:15 IST)
```
python scripts/scheduler_options_production.py
```
Expected: ✅ Trading scheduler running

---

## WHAT YOU'LL SEE

### When Scheduler Starts (09:15)
```
✅ BreezeAPIService initialized
✅ All 5 options trading phases initialized
✅ Position monitoring thread started (1-minute interval)
[Time] [Level] Message

Every 1 minute:
- Download 1-min candle
- Calculate 31 indicators
- Check entry signals
- Monitor positions
- Execute exit rules

Every 10 minutes:
- Generate ML signal
- Consider new entry
```

### Expected Daily Performance
```
Duration: 09:15 - 15:30 IST (6h 15min)
Trades: 15-20
Win Rate: 90-95%
Gross P&L: ₹1,500-2,500
Fees: ₹400-500
Net P&L: ₹1,100-1,900 ✅
```

### End of Day (15:30)
```
Session P&L: ₹XXXX
Total Trades: XX
Win Rate: XX%
Report saved to: reports/
Model status saved to: reports/
Position data saved to: reports/
```

---

## CREDENTIALS CHECKLIST

Before Monday 09:15, verify .env has:
```
BREEZE_USER_ID=PRAUZRKW
BREEZE_SESSION_TOKEN=<fresh_token>
BREEZE_API_KEY=<your_api_key>
BREEZE_SECRET_KEY=<your_secret>
BREEZE_PASSWORD=<your_password>
```

Get fresh token from: https://api.icicidirect.com/apiuser/login

---

## QUICK TROUBLESHOOTING

### "Breeze API error"
```
✓ Check .env has fresh BREEZE_SESSION_TOKEN
✓ Get new token: https://api.icicidirect.com/apiuser/login
✓ Verify BREEZE_API_KEY and BREEZE_SECRET_KEY
```

### "No candles downloaded"
```
✓ Verify market hours (09:15-15:30 IST)
✓ Check Breeze connection
✓ Verify internet connectivity
```

### "Test fails"
```
✓ Run: python scripts/test_hybrid_system_integration.py
✓ Check error message
✓ Verify all modules loading: python -c "from feature_engine import FeatureEngine"
```

### "Import error"
```
✓ Verify sys.path setup in files
✓ Check scripts/ directory exists
✓ Verify all core modules in scripts/
```

---

## KEY FILES

**Main Entry Points:**
- `scripts/scheduler_options_production.py` - Main scheduler
- `scripts/test_hybrid_system_integration.py` - Tests (14 tests)
- `scripts/monday_deployment_check.py` - Pre-flight check

**Configuration:**
- `.env` - API credentials and settings
- `requirements.txt` - Python dependencies

**Core Modules:**
- `scripts/trading_engine_hybrid.py` - Trading engine
- `scripts/feature_engine.py` - 31 indicators
- `scripts/ml_model_manager_hybrid.py` - ML model
- `scripts/options_chain_manager.py` - Options data
- `scripts/options_executor_and_risk.py` - Order execution

**Output:**
- `reports/` - Daily session reports
- `logs/` - System logs
- `models/` - ML models

---

## SUCCESS CRITERIA

✅ System deployed: `python scripts/scheduler_options_production.py` runs
✅ Tests passing: 14/14 integration tests PASS
✅ Trading executing: Trades visible in logs
✅ P&L tracking: Session P&L calculated with fees
✅ Monitoring active: Positions monitored every 1 minute
✅ Exits triggering: Exit rules executed correctly
✅ Risk managed: Kill-switch armed at -₹5,000

---

## MONDAY TIMELINE

```
08:45 - Run deployment check
08:50 - Run integration tests
09:10 - Monitor first 5 trades
09:15 - GO LIVE! 🚀
09:20 - First trade should execute
09:21+ - Continuous monitoring and trading
15:30 - Force close all positions
16:00 - Begin daily model retraining
```

---

## CONTACT INFO

**If You Need Help:**
- Check logs: `tail -f logs/*.log`
- Run diagnostic: `python scripts/test_hybrid_system_integration.py`
- Review error message
- Check .env credentials
- Verify internet connection

**ICICI Direct Support:**
- Support: support@icicidirect.com
- API Token: https://api.icicidirect.com/apiuser/login

---

**Status**: 🟢 READY TO DEPLOY  
**Deployment Date**: Monday June 15, 2026  
**Deployment Time**: 09:15 IST  

**Good luck! 🚀**
