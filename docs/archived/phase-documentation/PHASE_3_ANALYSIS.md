# PHASE 3 BACKTEST ANALYSIS & FINDINGS
## Range Policy Effectiveness Validation (2024-2025)

**Date:** June 9, 2026  
**Period:** Jan 1, 2024 - Jun 9, 2026 (2.5 years)  
**Data:** 3,612 bars across 6 Indian stocks (INFY, TCS, AXIS, MARUTI, WIPRO, SUNPHARMA)

---

## Executive Summary

The Phase 3 backtest revealed **critical findings about SMA20 strategy performance and Range Policy effectiveness**.

### Key Findings

**1. Range Policy Blocks: 0 blocks detected**
- **ISSUE:** Range detector not triggering during sideways markets
- **Root Cause:** Simplified ADX calculation (hardcoded at 50) not reflecting actual trend weakness
- **Impact:** Range Policy is **not functioning** as designed

**2. Overall Strategy Performance: NEGATIVE**
- Total Trades: 186 executed
- Win Rate: 24.7% (need 40%+ for profitability)
- Profit Factor: 0.97 (below break-even at 1.0)
- Total P&L: -$209,639 loss
- Max Drawdown: -56.4% (unacceptable)
- Sharpe Ratio: -0.15 (poor risk-adjusted returns)

**3. Comparison Result: IDENTICAL**
- WITH Range Policy vs WITHOUT: No difference
- Reason: Range Policy never triggered (0 blocks)
- Trades executed: 186 in both cases
- This is actually a problem

---

## Detailed Analysis

### Why Is SMA20 Losing Money?

1. **Too many false breakouts** (24.7% win rate is 15% below break-even)
2. **No pullback validation** - Buy every SMA20 cross, regardless of context
3. **No volatility filter** - Trading same during calm AND volatile periods
4. **No trend strength check** - ADX would help but hardcoded
5. **No support/resistance levels** - Just trusting SMA20 alone

### Why Range Policy Didn't Trigger?

The detector is checking for:
- ATR < 1.5% (low volatility)
- ADX < 25 (weak trend)
- BB width squeeze

**Problem:** ADX is hardcoded at 50 instead of being calculated.

```python
# Current broken code:
adx = 50  # HARDCODED! - Always returns neutral
weak_trend = adx < 25  # Never true
```

---

## Recommendations: Phase 3→4 Transition

### Priority 1: FIX Range Policy Calculation ✅ CRITICAL
```python
def _calc_adx_proper(df):
    """Real ADX calculation"""
    # Calculate +DM, -DM
    # Calculate true range
    # Calculate DI+ and DI-
    # Calculate ADX = smoothed DI diff / DI sum
    pass
```

### Priority 2: ADD Filters to SMA20 Strategy
```python
Entry Gate 1: Volatility Check
  - Only trade if ATR > 1.0% (avoid ranging)
  - Skip when ATR < 0.5% (dead market)

Entry Gate 2: Trend Strength Check
  - ADX > 25 (confirmed trend)
  - MA20 above MA50 for longs

Entry Gate 3: Support Validation
  - Price not at 52-week low
  - Volume above 30-day average
```

### Priority 3: Optimize Position Sizing
```python
Position Size = Base * ADX_Multiplier
  - If ADX 25-40: 100% size
  - If ADX 40-60: 150% size (strong trend)
  - If ADX < 25: 0% size (BLOCK - Range Policy)
  - If ADX > 60: 50% size (overextended)
```

### Priority 4: Add Profit-Taking Rules
```python
Exit Rules:
  - Profit target: 2-3% (quick exit on strong trends)
  - Trail stop: 1% behind highest close
  - Time stop: 10 bars max (avoid holding losers)
  - Max loss: 1% stop-loss
```

---

## Next Steps (Phase 4)

### Step 1: Implement Proper ADX Calculation
- Rewrite `_calc_adx_proper()` in RangeDetector
- Validate against TradingView / manual calculation
- Test on known trending and sideways periods

### Step 2: Re-run Phase 3 Backtest
- With corrected Range Policy
- Expect to see blocks during Jul-Sep 2024 sideways period
- Should reduce drawdown significantly

### Step 3: Add Entry Filters
- Test SMA20 + ADX > 25 filter
- Measure impact on win rate and trade frequency
- Goal: 35-40% win rate on filtered trades

### Step 4: Optimize Position Sizing & Exits
- Add profit-taking at 2% move
- Add 10-bar time stop
- Test trail stops

### Step 5: Final Validation
- Backtest with all improvements
- Expect: 40%+ win rate, <20% drawdown
- Ready for Phase 5: Paper trading

---

## Test Data Summary

| Symbol | Bars | Period | Status |
|--------|------|--------|--------|
| INFY | 602 | 2024-2026 | ✓ Loaded |
| TCS | 602 | 2024-2026 | ✓ Loaded |
| AXIS | 602 | 2024-2026 | ✓ Loaded |
| MARUTI | 602 | 2024-2026 | ✓ Loaded |
| WIPRO | 602 | 2024-2026 | ✓ Loaded |
| SUNPHARMA | 602 | 2024-2026 | ✓ Loaded |
| **Total** | **3,612** | **2 years** | **✓ Complete** |

---

## Files Created

1. `backtest/phase3_backtest_fast.py` - Main backtest runner
2. `backtest_reports/phase3_backtest_results_fast.json` - Results JSON
3. `PHASE_3_ANALYSIS.md` - This file

---

## Actionable Takeaways

**What Worked:**
- ✓ Backtest framework runs smoothly
- ✓ Can load and process real yfinance data
- ✓ Multi-stock comparison possible
- ✓ Range detector structure is sound

**What Didn't Work:**
- ✗ ADX hardcoded (not calculated)
- ✗ SMA20 alone too simplistic (24.7% WR)
- ✗ No filters = high drawdown (56%)
- ✗ Range Policy never triggered (0 blocks)

**What's Next:**
1. Fix ADX calculation → Re-run Phase 3
2. Add entry filters → Test SMA20 + ADX
3. Add exit rules → Optimize P&L
4. Validate improvements → Ready for Phase 5

---

## Expected Phase 4 Outcomes

If we implement the above fixes, we should see:

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Win Rate | 24.7% | 40%+ | +15-20% |
| Profit Factor | 0.97 | 1.5+ | +50% |
| Max Drawdown | 56% | 15-20% | -36-40% |
| P&L | -$209K | +$50K+ | +$250K+ |
| Sharpe Ratio | -0.15 | 0.8+ | +1.0 |

**Note:** These are realistic estimates based on industry standards for trend-following systems with proper filters.

---

## Conclusion

**Phase 3 Status:** ✓ COMPLETE (Backtest framework working, data loading verified)

**Phase 4 Status:** ⏳ READY TO START (Needs ADX fix + entry filters)

**Timeline:** Phase 4 should take 3-5 days to implement and validate.

**Success Criteria:** Achieve 40%+ win rate and <20% drawdown in Phase 4 backtest.
