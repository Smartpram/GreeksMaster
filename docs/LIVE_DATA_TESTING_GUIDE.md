# OPTIONS SCREENERS - LIVE DATA TESTING GUIDE

## 📋 Current Status

### ✅ What's Complete
- **6 Options Screeners**: Fully implemented (1250 lines)
- **Demo Scripts**: Integration examples (450 lines)
- **Documentation**: Complete guides (1500+ lines)
- **Live Data Test Script**: Ready (test_options_screeners_live.py)

### ⚠️ Current Blocker
- **API Session Token**: Expired - needs refresh

---

## 🔧 How to Fix API Connection

### Step 1: Get Fresh Session Token

```
1. Visit: https://api.icicidirect.com/apiuser/login?api_key=YOUR_API_KEY
2. Login with your ICICI Direct credentials
3. You'll see a session token displayed (long string)
4. Copy the entire token
```

### Step 2: Update .env File

```
Open file: .env (root directory)

Find this line:
  BREEZE_SESSION_TOKEN=old_expired_token

Replace with:
  BREEZE_SESSION_TOKEN=your_fresh_token_here

Save file
```

### Step 3: Verify Connection

```bash
# Run diagnostic
python diagnose_breeze_api.py

# Expected output if successful:
✅ AUTHENTICATION SUCCESSFUL
   User: your_username
   User ID: your_user_id
   Segments: {...}
```

### Step 4: Run Live Data Tests

```bash
# Run the live data test
python test_options_screeners_live.py

# Expected output:
✅ STEP 1: API CONNECTION SUCCESSFUL
✅ STEP 2: IV SCREENER - Found X opportunities
✅ STEP 3: EARNINGS SCREENER - Found X opportunities
✅ STEP 4: THETA SCREENER - Found X opportunities
✅ STEP 5: COMBO SCREENER - Found X opportunities
✅ STEP 6: HEDGING SCREENER - Found X opportunities
✅ STEP 7: DELTA NEUTRAL SCREENER - Found X opportunities

COMPREHENSIVE TEST REPORT - LIVE DATA
Total Screeners Tested: 6
Successful Screeners: 6/6
Total Opportunities Found: X
```

---

## 📊 What the Tests Will Show

### IV Screener Test
- Scans for stocks with IV percentile > 75%
- Output: Top 5 high-IV opportunities
- Metrics: IV percentile, expected move, premium skew

### Earnings Screener Test
- Scans for upcoming earnings (within 14 days)
- Output: Top 5 earnings opportunities
- Metrics: Days to earnings, historical move, expected IV

### Theta Decay Screener Test
- Scans for 3-8 DTE options with high theta
- Output: Top 10 theta decay opportunities
- Metrics: Daily theta, efficiency score, DTE

### Combo Screener Test
- Combines technical signals + favorable Greeks
- Output: Top 5 high-probability setups
- Metrics: Technical score, Greeks favorability, risk/reward

### Hedging Screener Test
- Finds highly correlated stock pairs (correlation > 0.70)
- Output: Top 5 hedging pairs
- Metrics: Correlation, hedge ratio, cost of hedge

### Delta Neutral Screener Test
- Finds butterfly spread setups
- Output: Top 5 delta-neutral opportunities
- Metrics: Combined delta, max profit/loss, efficiency

---

## 🎯 Test Files & Locations

| File | Purpose | Status |
|------|---------|--------|
| `test_options_screeners_live.py` | Main live data test | ✅ Ready |
| `diagnose_breeze_api.py` | Connection diagnostic | ✅ Ready |
| `app/options_screener.py` | Core screeners | ✅ Complete |
| `app/options_screeners_demo.py` | Demo integration | ✅ Complete |
| `.env` | Configuration (needs update) | ⚠️ Update needed |

---

## 📝 Configuration Files

### .env File Location
```
c:\Data\GreeksMaster\.env
```

### Required Variables
```
BREEZE_API_KEY=your_api_key
BREEZE_SECRET_KEY=your_secret_key
BREEZE_USER_ID=your_user_id
BREEZE_SESSION_TOKEN=fresh_token_here
BREEZE_PASSWORD=your_password
```

### Optional Variables
```
OPTIONS_CAPITAL=500000
MAX_OPTION_POSITION_SIZE=0.1
DEBUG=False
PAPER_TRADING=True
```

---

## 🧪 Expected Test Output

### Successful Connection
```
====================================================================================================
LIVE DATA TEST - OPTIONS SCREENERS
Testing with REAL Breeze API Data
Date: 2026-06-09 08:01:54
====================================================================================================

====================================================================================================
STEP 1: TESTING API CONNECTION
====================================================================================================

Initializing Breeze API...
Attempting to authenticate...

✅ API CONNECTION SUCCESSFUL
   User: PRAUZRKW
   User ID: your_user_id
   Session Token: abc123def456...
   Segments Allowed: {'equity': {...}, 'derivatives': {...}}
```

### Screener Results
```
====================================================================================================
STEP 2: TESTING IV SCREENER (High Implied Volatility)
====================================================================================================

Scanning for high IV opportunities (IV percentile > 75%)...

✅ IV SCREENER SUCCESSFUL - Found 5 opportunities

Top 5 Results:
1. NIFTY @ ₹22000
   IV Percentile: 85.5% | Current IV: 28.30%
   Expected Move: ₹550 (2.50%)
   Recommendation: SELL_CALLS
   Score: 85.5/100
```

### Final Summary
```
====================================================================================================
COMPREHENSIVE TEST REPORT - LIVE DATA
====================================================================================================

API CONNECTION STATUS:
  Status: ✅ CONNECTED

SCREENER TEST RESULTS:
✅ IV Screener                          - 5 opportunities found
✅ Earnings Screener                    - 3 opportunities found
✅ Theta Screener                       - 12 opportunities found
✅ Combo Screener                       - 8 opportunities found
✅ Hedging Screener                     - 2 opportunities found
✅ Delta Neutral Screener               - 4 opportunities found

SUMMARY:
  Total Screeners Tested: 6
  Successful Screeners: 6/6
  Total Opportunities Found: 34
  Average per Screener: 5.7
```

---

## 🚀 Quick Reference

### Run Live Data Test
```bash
python test_options_screeners_live.py
```

### Run Diagnostic Only
```bash
python diagnose_breeze_api.py
```

### Run Demo (Mock Data)
```bash
python -m app.options_screeners_demo
```

---

## ❓ Troubleshooting

### Issue: "Resource not available"
**Solution**: Session token is expired. Get a fresh one from login URL.

### Issue: "SessionToken error"
**Solution**: Check that BREEZE_SESSION_TOKEN in .env is correct and recent.

### Issue: "Could not connect to API"
**Solution**: Check network connectivity and firewall settings.

### Issue: "No opportunities found"
**Solution**: This is normal - market conditions determine opportunities. All screeners are working correctly.

### Issue: "AttributeError in screener"
**Solution**: Check that Breeze API is returning data in expected format. Run diagnostic.

---

## 📈 After Successful Testing

Once live data tests pass:

1. **Review Results**: Check which screeners find opportunities
2. **Integrate with Engine**: Use screeners with OptionsEngine
3. **Backtest**: Run historical backtests
4. **Deploy**: Add to trading schedule
5. **Monitor**: Track screener performance

---

## 📚 Documentation References

- **Quick Start**: docs/OPTIONS_SCREENERS_QUICK_REFERENCE.md
- **Full Guide**: docs/OPTIONS_SCREENERS_IMPLEMENTATION.md
- **Strategy**: docs/OPTIONS_SCREENER_STRATEGY_ANALYSIS.md
- **Index**: docs/INDEX_OPTIONS_SCREENERS.md

---

## ✨ Testing Checklist

- [ ] Session token refreshed
- [ ] .env file updated
- [ ] Diagnostic test passed (diagnose_breeze_api.py)
- [ ] Live data test passed (test_options_screeners_live.py)
- [ ] All 6 screeners working
- [ ] Found opportunities in at least one screener
- [ ] Reviewed test output
- [ ] Ready to integrate with trading engine

---

## 🎯 Next Steps After Testing

1. **Immediate**: Refresh session token, run tests
2. **Short Term**: Verify all screeners with real data
3. **Medium Term**: Integrate with OptionsEngine
4. **Long Term**: Backtest and optimize thresholds

---

**Status**: ✅ Code Complete | ⚠️ Testing Blocked by Expired Session Token  
**Action Required**: Refresh BREEZE_SESSION_TOKEN in .env file  
**Estimated Time to Fix**: 5 minutes
