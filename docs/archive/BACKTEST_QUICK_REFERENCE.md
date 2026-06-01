# Quick Reference Card - Advanced Strategies Backtest

## 🚀 Ultra-Quick Start

```powershell
cd c:\Data\MyBreezeApp
python run_backtest_real_data.py
```

**Time:** 20 seconds | **Output:** 3 result files

---

## 📋 One-Page Cheat Sheet

### Running Backtest

```powershell
# Diagnostic check first
python diagnose_backtest_setup.py

# Run with real or synthetic data
python run_backtest_real_data.py

# Advanced runner (custom symbols)
python run_advanced_strategies_backtest.py
```

### Setting Credentials (For Real Data)

```powershell
# Temporary (current session only)
$env:BREEZE_API_KEY = "your_key"
$env:BREEZE_SECRET_KEY = "your_secret"
$env:BREEZE_SESSION_TOKEN = "your_token"
$env:BREEZE_USER_ID = "your_user_id"

# Permanent (create .env file)
@"
BREEZE_API_KEY=your_key
BREEZE_SECRET_KEY=your_secret
BREEZE_SESSION_TOKEN=your_token
BREEZE_USER_ID=your_user_id
"@ > .env
```

### Viewing Results

```powershell
# Executive summary (read this first)
Get-Content ADVANCED_STRATEGIES_EXEC_SUMMARY.md

# Detailed analysis
Get-Content ADVANCED_STRATEGIES_BACKTEST_RESULTS.md

# Raw data (for Excel/Python)
Get-Content ADVANCED_STRATEGIES_BACKTEST_RESULTS.json
```

---

## 🎯 8 Strategies (Quick Reference)

| # | Strategy | Type | Best For | Risk |
|---|----------|------|----------|------|
| 1 | **Gamma Scalping** | Options | Premium capture | Medium |
| 2 | **Order Flow** | Equity | Smart entry | Low |
| 3 | **Vol Harvesting** | Options | Premium short | Medium |
| 4 | **Vol Mean Reversion** | Options | Vol spikes | High |
| 5 | **VCP** | Equity | Volume breaks | Medium |
| 6 | **PEAD** | Equity | Earnings drift | High |
| 7 | **Options Momentum** | Options | Directional | High |
| 8 | **Statistical Arb** | Equity | Pair correlation | Low |

---

## 📊 Interpreting Results

### Performance Levels

🏆 **Excellent:** Return > 20%, Sharpe > 2.0, Win Rate > 70%
→ Deploy to paper trading immediately

✅ **Good:** Return 10-20%, Sharpe 1.0-2.0, Win Rate 50-70%
→ Monitor and optimize

⚠️ **Fair:** Return 0-10%, Sharpe 0.5-1.0, Win Rate 40-50%
→ Needs tuning or more data

❌ **Poor:** Return < 0%, Sharpe < 0.5, Win Rate < 40%
→ Redesign or retire

### Key Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| **Total Return %** | (Final - Initial) / Initial × 100 | +10% to +100% ✅ |
| **Sharpe Ratio** | (Return - Risk-Free) / Volatility | > 2.0 🏆 |
| **Win Rate %** | Winning Trades / Total Trades × 100 | > 70% 🏆 |
| **Max Drawdown %** | Peak Loss / Peak Value × 100 | < 5% 🏆 |
| **Profit Factor** | Gross Profit / Gross Loss | > 2.0 🏆 |

---

## 🔧 Troubleshooting Quick Fixes

| Issue | Solution |
|-------|----------|
| ModuleNotFoundError | `pip install pandas numpy requests python-dotenv` |
| FileNotFoundError | `cd c:\Data\MyBreezeApp && ls` |
| Session Token Expired | Generate new: `python -c "from app.services.breeze_api import BreezeAPIService; print(BreezeAPIService().login())"` |
| No Data Returned | Uses synthetic fallback - this is normal |
| Very Slow | First run slower (fetching), subsequent runs faster |
| Results not created | Check console for error messages |

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `BACKTEST_START_HERE.md` | 📍 Read first (5 min overview) |
| `run_backtest_real_data.py` | 🚀 **RUN THIS** (quick starter) |
| `diagnose_backtest_setup.py` | 🔍 Verify your setup |
| `ADVANCED_STRATEGIES_EXEC_SUMMARY.md` | 📊 Review results here |
| `BREEZE_CREDENTIALS_SETUP.md` | 🔐 API setup instructions |
| `RUNNING_BACKTEST_REAL_DATA.md` | 📖 Full detailed guide |

---

## ⚡ Workflow

```
1. Verify Setup
   └─ python diagnose_backtest_setup.py

2. (Optional) Set Breeze Credentials
   └─ $env:BREEZE_SESSION_TOKEN = "..."

3. Run Backtest
   └─ python run_backtest_real_data.py

4. Review Results
   └─ Get-Content ADVANCED_STRATEGIES_EXEC_SUMMARY.md

5. Paper Trading
   └─ Deploy top strategies

6. Monitor 2 weeks
   └─ Track performance

7. Live Trading
   └─ 10% capital deployment
```

---

## 🎲 Testing Symbols

```
NIFTY          NSE Index
BANKNIFTY      Bank sector index
INFY           Technology stock
RELIANCE       Energy stock
TCS            IT services stock
HDFC           Banking stock
SBIN           Banking stock
ICICIBANK      Banking stock
```

---

## ⏱️ Timing

| Step | Duration |
|------|----------|
| Verify setup | 30 seconds |
| Set credentials | 2 minutes |
| Run backtest | 20 seconds |
| Review results | 5-10 minutes |
| Paper trading setup | 30 minutes |
| **Total** | **~40 minutes** |

---

## 💡 Pro Tips

✅ **Do:**
- Run backtest weekly
- Use real data for final validation
- Monitor paper trading for 2 weeks before live
- Start with 10% capital in live
- Keep credentials in .env file

❌ **Don't:**
- Hardcode credentials in code
- Commit credentials to Git
- Skip paper trading phase
- Deploy without validation
- Use same credentials for multiple apps

---

## 🔐 Credential Management

### Get Credentials

1. Visit: https://www.icicidirect.com/
2. Login → Settings → API Keys
3. Copy: API Key, Secret Key, User ID

### Generate Session Token

```powershell
python -c "from app.services.breeze_api import BreezeAPIService; print(BreezeAPIService().login())"
```

### Set Environment Variables

```powershell
# Current session
$env:BREEZE_SESSION_TOKEN = "token_here"

# Or use .env file
echo "BREEZE_SESSION_TOKEN=token_here" >> .env
```

---

## 🎯 Success Criteria

- [ ] Backtest completes in ~20 seconds
- [ ] 3 result files created
- [ ] Can identify top 3 strategies
- [ ] Metrics make sense (positive return, reasonable Sharpe)
- [ ] Ready for paper trading

✅ All checked? You're production-ready! 🚀

---

## 📞 Support

**Stuck?** See detailed guides:
- `BACKTEST_START_HERE.md` - 5-minute overview
- `RUNNING_BACKTEST_REAL_DATA.md` - Complete guide
- `BREEZE_CREDENTIALS_SETUP.md` - Credential setup

**Questions about strategies?**
- `ADVANCED_STRATEGIES_QUICK_REFERENCE.md`
- `ADVANCED_STRATEGIES_ARCHITECTURE.md`

**Need to integrate into your code?**
- `ADVANCED_STRATEGIES_INTEGRATION_GUIDE.md`

---

**Version:** 2.0 | **Updated:** January 2025 | **Status:** ✅ Production Ready
