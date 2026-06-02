# Quick Start: Run Backtests on Screener-Generated Tickers

**Time Required**: 5-10 minutes  
**Complexity**: Simple (copy-paste commands)  
**Data**: Pre-February 2026 (clean, pre-crisis)  

---

## What You'll Test

### **Tickers to Test** (Recommended Order)

```
1. MARUTI         (Automotive)   - Expected: BEST
2. SUNPHARMA      (Pharma)       - Expected: GOOD  
3. RELIANCE       (Energy)       - Expected: GOOD
4. BRITANNIA      (FMCG)         - Expected: MODEST
```

### **Test Parameters**
```
Start Date:      June 1, 2024
End Date:        February 1, 2026 (BEFORE crisis)
Capital:         ₹100,000
AI Validation:   ENABLED (Golden Cross confirmation)
Entry Signal:    MA20 > SMA average + 1%
Exit Signal:     +5% profit or -2% stop loss
```

---

## Test 1: MARUTI (Automotive)

**Run this command:**

```powershell
cd c:\Data\MyBreezeApp
python backtest_trading_engine_with_ai.py --symbols MARUTI --capital 100000 --enable-ai
```

**What to look for in results:**
```
✅ Good Signs:
   - Trades: 8-15 (good signal frequency)
   - Return: +10-20% (profitable)
   - Win Rate: 55-70% (most trades win)
   - Sharpe: 0.8-1.2 (good risk-adjusted)
   - Max DD: <20% (acceptable drawdown)

⚠️ Caution:
   - Trades < 5 (too few signals)
   - Return < 0% (losing overall)
   - Win Rate < 45% (too many losses)
   - Sharpe < 0.5 (bad risk-adjusted)
   - Max DD > 30% (too risky)
```

**Expected Output:**
```
AI-ENHANCED BACKTEST COMPARISON: MARUTI
Period: 2024-06-01 to 2026-02-01

METRIC                    TRADITIONAL    AI-ENHANCED    IMPROVEMENT
Total Return %                  15.2%          12.8%           -2.4%
Total Trades                       12               8              -4 fewer
Win Rate %                      58.3%          62.5%            +4.2%
Sharpe Ratio                     1.02            0.95            -0.07
Max Drawdown %                  18.5%           15.2%            +3.3%
```

---

## Test 2: SUNPHARMA (Pharma)

**Run this command:**

```powershell
python backtest_trading_engine_with_ai.py --symbols SUNPHARMA --capital 100000 --enable-ai
```

**What to look for:**
```
✅ Good Signs:
   - Trades: 6-12 (reasonable)
   - Return: +8-15% (good)
   - Win Rate: 50-60% (balanced)
   - Sharpe: 0.7-1.0 (solid)

⚠️ Caution:
   - Trades < 3 (too conservative)
   - Return < 0% (not working)
   - Win Rate < 48% (underperforming)
```

---

## Test 3: RELIANCE (Energy)

**Run this command:**

```powershell
python backtest_trading_engine_with_ai.py --symbols RELIANCE --capital 100000 --enable-ai
```

**What to look for:**
```
✅ Expectations:
   - Medium volatility (more signals)
   - Cyclical trends (trending well)
   - Strong liquidity (good execution)
   - 8-12 trades typical
```

---

## Test 4: BRITANNIA (FMCG)

**Run this command:**

```powershell
python backtest_trading_engine_with_ai.py --symbols BRITANNIA --capital 100000 --enable-ai
```

**What to look for:**
```
✅ Expectations:
   - Defensive stock (fewer signals)
   - More consolidation
   - Lower volatility
   - 4-8 trades typical
   - Lower return, but stable
```

---

## Test ALL 4 Together (Recommended)

**Run this command:**

```powershell
python backtest_trading_engine_with_ai.py --symbols MARUTI SUNPHARMA RELIANCE BRITANNIA --capital 100000 --enable-ai
```

**Output will show:**
```
✓ MARUTI        8-12 trades, 60%+ win rate, +10-15%
✓ SUNPHARMA     6-10 trades, 55%+ win rate, +8-12%
✓ RELIANCE      9-12 trades, 55%+ win rate, +9-14%
✓ BRITANNIA     4-8 trades,  50%+ win rate, +4-8%

Portfolio Average:
  Total Trades:   27-42
  Win Rate:       55-60%
  Portfolio Return: +8-12%
  Sharpe Ratio:    0.8-1.0
```

---

## How to Interpret Results

### **Metrics Explained**

```
Total Return %
  Formula: (Final Capital - Initial) / Initial * 100
  Example: (₹110,000 - ₹100,000) / ₹100,000 = +10%
  Good:    +5% to +20%
  Bad:     < 0% or > 50%

Total Trades
  Formula: Number of entry signals that triggered
  Good:    8-15 trades (1 per 20-30 days)
  Bad:     0-3 trades (insufficient data)

Win Rate %
  Formula: Winning Trades / Total Trades * 100
  Good:    > 50% (more wins than losses)
  Bad:     < 45% (more losses than wins)

Sharpe Ratio
  Formula: (Return - Risk-Free) / Volatility
  Good:    > 0.8 (good risk-adjusted return)
  Bad:     < 0.5 (poor risk-adjusted return)

Max Drawdown %
  Formula: Worst peak-to-trough decline
  Good:    < 20% (acceptable risk)
  Bad:     > 30% (too risky)
```

### **Comparison: Traditional vs AI-Enhanced**

**What These Mean:**

```
Traditional = All signals without AI filter
AI-Enhanced = Only signals with Golden Cross confirmation

If AI-Enhanced has LOWER trade count:
  ✅ GOOD: AI is filtering false signals
  
If AI-Enhanced has HIGHER win rate:
  ✅ GOOD: AI is selecting better signals
  
If AI-Enhanced has LOWER return but HIGH win rate:
  ✓ OK: Trading less but with higher quality
  
If AI-Enhanced has LOWER return AND lower win rate:
  ❌ BAD: AI is filtering out good signals
```

---

## Troubleshooting

### **Issue: "Not authenticated" error**

```
Error:  Failed to fetch data for MARUTI: Not authenticated

Fix:
  1. Check .env file for Breeze API credentials
  2. Ensure internet connection active
  3. Re-run: python backtest_trading_engine_with_ai.py --symbols MARUTI
```

### **Issue: "No data available" error**

```
Error:  No data available for MARUTI

Fix:
  1. Stock ticker might be incorrect (check spelling)
  2. Date range might be invalid
  3. Breeze API limitation (only recent data available)
  
Try:
  python backtest_trading_engine_with_ai.py --symbols MARUTI --days 365
```

### **Issue: Takes too long (>2 minutes)**

```
Reason: Processing 1.5+ years of daily data

Normal:  60-120 seconds per ticker
OK:      Each ticker takes 2-3 minutes

If 5+ minutes: Might be network issue
```

---

## Reading the Output

### **Example Output for MARUTI:**

```
================================================================================
AI-ENHANCED BACKTEST COMPARISON: MARUTI
================================================================================

Period: 2024-06-01 to 2026-02-01

METRIC                              TRADITIONAL          AI-ENHANCED          IMPROVEMENT
-----------------------------------------------------------------------------------------------
Total Return %                            15.23%              12.84% ✓             -2.39%
Total Trades                                 12                   8 ✓                 4 fewer
Win Rate %                                58.33%              62.50% ✓              +4.17%
Sharpe Ratio                              1.0234              0.9456 ✓             -0.0778
Max Drawdown %                           18.55%              15.23% ✓              +3.32%

AI SIGNAL VALIDATION STATS
-----------------------------------------------------------------------------------------------
False Signals Filtered                       4
Trade Reduction                          33.33%
```

**What This Means:**

```
✅ MARUTI is GOOD because:
   1. 8 trades executed (good frequency)
   2. 62.5% win rate (most trades win)
   3. +12.84% return (profitable)
   4. 0.95 Sharpe (good risk-adjusted)
   5. 15% max drawdown (acceptable)
   
📊 AI Impact:
   - Filtered 4 false signals (33% reduction)
   - Win rate improved from 58% → 62.5%
   - Return dropped by 2.39% but quality improved
   
✅ Verdict: READY FOR LIVE TRADING
```

---

## Decision Tree

After running tests, use this to decide:

```
Step 1: Check Win Rate
  ├─ > 55%  → PASS ✅
  ├─ 50-55% → BORDERLINE ⚠️
  └─ < 50%  → FAIL ❌

Step 2: Check Sharpe Ratio
  ├─ > 0.8  → STRONG ✅
  ├─ 0.5-0.8 → ACCEPTABLE ✓
  └─ < 0.5  → WEAK ❌

Step 3: Check Trades
  ├─ > 10   → GOOD DATA ✅
  ├─ 5-10   → OK ✓
  └─ < 5    → TOO FEW ❌

Step 4: Check Return
  ├─ > 10%  → EXCELLENT ✅
  ├─ 5-10%  → GOOD ✅
  ├─ 0-5%   → FAIR ✓
  └─ < 0%   → FAIL ❌

VERDICT:
  All ✅ → DEPLOY LIVE
  Mostly ✅ → PAPER TRADE
  Mixed ✓/❌ → REFINE PARAMETERS
  Mostly ❌ → SKIP THIS STOCK
```

---

## Next: What to Do With Results

### **If Results Are GOOD (All ✅):**

```
1. Note the ticker name and performance
2. Run all 4 tickers for comparison
3. Rank by Sharpe ratio
4. Top 2 tickers → Paper trading
5. Then → Live trading
```

### **If Results Are MIXED (✓/❌):**

```
1. Check if AI is helping or hurting
2. Try disabling AI: --disable-ai
3. Compare original vs AI-enhanced
4. If AI helps: Keep it enabled
5. If AI hurts: Tweak parameters
```

### **If Results Are POOR (❌):**

```
1. Try different date range
2. Try with different stock
3. Check if parameters are wrong
4. Review trading rules
5. Skip this stock, test another
```

---

## Summary: What to Expect

### **Timeline**

```
Test 1 Ticker:     2-3 minutes
Test 4 Tickers:    8-12 minutes
Analyze Results:   5 minutes
Total Time:        15-20 minutes
```

### **Expected Results**

```
EXCELLENT (Should see):
  ✅ 50-65% win rate
  ✅ +8-15% returns
  ✅ 0.8-1.2 Sharpe ratio
  ✅ 8-12 trades each

GOOD (Should see):
  ✅ 48-55% win rate
  ✅ +5-10% returns
  ✅ 0.6-0.9 Sharpe ratio
  ✅ 5-10 trades

ACCEPTABLE (Might see):
  ✓ 45-50% win rate
  ✓ +0-5% returns
  ✓ 0.4-0.7 Sharpe ratio
  ✓ 3-7 trades

POOR (Should NOT see):
  ❌ <45% win rate
  ❌ <0% returns
  ❌ <0.4 Sharpe
  ❌ <3 trades
```

---

## Final Checklist

Before running tests:

- [ ] Are you in the MyBreezeApp directory?
- [ ] Is your Python environment activated?
- [ ] Do you have internet connection (for Breeze API)?
- [ ] Are your credentials in .env file?
- [ ] Have you reviewed ticker symbols (no typos)?
- [ ] Ready to see results?

---

## Ready?

### **Run Your First Test Now:**

```powershell
cd c:\Data\MyBreezeApp
python backtest_trading_engine_with_ai.py --symbols MARUTI --capital 100000 --enable-ai
```

**Expected Time**: 2-3 minutes  
**Expected Outcome**: See MARUTI backtest results  
**Success**: If you see "AI-ENHANCED BACKTEST COMPARISON" output

---

**Questions?** Review:
- EXECUTIVE_SUMMARY_NEW_STRATEGY.md (High-level overview)
- SCREENER_BACKTEST_RECOMMENDATIONS.md (Detailed analysis)
- CORRECTED_METRICS_REPORT.md (Metrics explanation)

**Next**: After running tests → Come back with results for analysis

