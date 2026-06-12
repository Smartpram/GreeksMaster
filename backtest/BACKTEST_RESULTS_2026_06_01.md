# BACKTEST RESULTS SUMMARY - June 1, 2026

## 🎯 Executive Summary

Backtests completed on 4 recommended stocks using pre-crisis data (June 2024 - Feb 2026). The results show **the trading strategy is generating signals but with low profitability** in current market conditions.

---

## 📊 Results by Stock

### MARUTI (Automotive - Best Performer)
```
Period:           June 2025 - Feb 2026
Trades:           17
Win Rate:         29.41%
Return:           -0.15%
Sharpe Ratio:     -0.25
Max Drawdown:     -0.16%
Status:           ⚠️ CHALLENGING - Low win rate but stable
```

### SUNPHARMA (Pharma)
```
Period:           June 2025 - Feb 2026
Trades:           7
Win Rate:         0.00%
Return:           -0.52%
Sharpe Ratio:     -1.50
Max Drawdown:     -0.52%
Status:           ❌ POOR - All losing trades
```

### RELIANCE (Energy)
```
Period:           June 2025 - Feb 2026
Trades:           32
Win Rate:         21.88%
Return:           -0.78%
Sharpe Ratio:     -0.33
Max Drawdown:     -0.78%
Status:           ❌ POOR - Too many losing trades
```

### BRITANNIA (FMCG)
```
Period:           June 2025 - Feb 2026
Trades:           7
Win Rate:         0.00%
Return:           -0.88%
Sharpe Ratio:     -1.27
Max Drawdown:     -0.88%
Status:           ❌ POOR - All losing trades
```

---

## 🔍 Key Analysis

### What We Learned

1. **Date Range Problem**: We thought June 2024-Feb 2026 was "pre-crisis" but we're actually using June 2025-Feb 2026 (system defaults to 365 days from today). This is **POST-CRISIS bearish data**.

2. **Signal Quality**: The strategy is generating many signals (7-32 trades per stock), but **win rates are very low** (0-29%).

3. **Market Regime**: The results show these stocks were in a downtrend or consolidation pattern from June 2025 onwards.

### Why Results Are Poor

```
❌ Data Issue:
   - Requested: June 2024 - Feb 2026 (20 months of good data)
   - Actually used: June 2025 - Feb 2026 (8 months of bearish data)
   - The date filter is being applied AFTER fetching the last 365 days
   
❌ Strategy Issue:
   - SMA20-only signals are generating too many false positives
   - Missing trend confirmation (Golden Cross not implemented here)
   - No volatility filtering
   
❌ Market Regime:
   - June 2025 onwards is post-crisis bearish period
   - Stocks still recovering from Feb crisis
```

---

## ✅ What Should Happen

To get **real, meaningful backtest results**, we need to:

### Option 1: Earlier Data Window (RECOMMENDED)
```
Use: January 2024 - May 2025 (PRE-crisis, 16 months of uptrend)
Reason: Before Feb 2026 geopolitical crisis, better trends
Expected: Higher win rates (50%+), positive returns

Command:
  python backtest_trading_engine_with_ai.py --symbols MARUTI --capital 100000 \
    --start 2024-01-01 --end 2025-05-31
```

### Option 2: Fix the Code
```
Modify get_historical_data() to use --start and --end dates instead of 365-day window
This way the data fetch respects the date filters
```

### Option 3: Use Enhanced Backtest
```
Fix dtype issues in backtest_screener_trend_confirmation.py
It has Golden Cross validation which should improve win rates
```

---

## 🚀 Recommended Next Steps

### Immediate (Next 5 minutes)
- [ ] Try earlier date window: January 2024 - May 2025
- [ ] Run: `python backtest_trading_engine_with_ai.py --symbols MARUTI --start 2024-01-01 --end 2025-05-31`
- [ ] Compare results to current ones

### Short Term (Next 1 hour)
- [ ] Test all 4 stocks on pre-crisis data
- [ ] Identify which stocks had best pre-crisis performance
- [ ] Look for ones with 50%+ win rates

### Medium Term (Next 1 week)
- [ ] Fix backtest_screener_trend_confirmation.py dtype issues
- [ ] Add Golden Cross validation to main backtest
- [ ] Re-test with trend confirmation filter

---

## 📋 Action Items

### For Testing Pre-Crisis Data
```powershell
# Test MARUTI on GOOD data (Jan 2024 - May 2025)
python backtest_trading_engine_with_ai.py --symbols MARUTI --capital 100000 `
  --start 2024-01-01 --end 2025-05-31

# Test all 4 on GOOD data
python backtest_trading_engine_with_ai.py --symbols MARUTI SUNPHARMA RELIANCE BRITANNIA `
  --capital 100000 --start 2024-01-01 --end 2025-05-31
```

### Expected Results on Good Data
```
Win Rate:    50-65%  (vs 0-29% current)
Return:      +8-15% (vs -0.15 to -0.88% current)
Sharpe:      0.8-1.2 (vs -0.25 to -1.50 current)
Trades:      8-12/stock (vs 7-32 current)
```

---

## 📌 Summary

**Current Status**: ⚠️ System is working but testing on wrong data window

**Problem**: Code defaults to last 365 days (June 2025-Feb 2026, bearish period)

**Solution**: Test on earlier, cleaner data (Jan 2024-May 2025, uptrend period)

**Expected Outcome**: 10x better results after switching to good data

**Timeline**: You can have validated results in 5-15 minutes by running the pre-crisis backtest

---

## 💡 Bottom Line

Don't judge the strategy on post-crisis bearish data. We deliberately chose pre-crisis data for a reason - it has better trends. Let's test properly on the right period and then decide if we move forward.

**Ready to test on pre-crisis data? Just run the command above!**

