# Phase 3 Plan: Full Period Backtest with Range Policy

## Objective
Complete full historical backtest (2024-2025) with Range Policy enabled to validate capital preservation during sideways markets.

## Current State ✅
- Phase 2 Extended complete: Range Policy & Sentiment Gate implemented
- SMA20 crossover baseline strategy sound
- Range detection working (ATR, ADX, Bollinger Bands)
- Persistence mechanism (5-bar threshold) prevents false signals

## Next Milestones (Prioritized)

### 1. **Full Period Backtest (2024-2025)** ⏳
- Run complete backtest with Range Policy enabled
- Compare: WITH Range Policy vs WITHOUT Range Policy
- Output: Side-by-side metrics comparison
- Focus: Capital preservation during Jul-Sep 2024 (known sideways period)

### 2. **Metrics & Validation** ⏳
- Win rate comparison
- Drawdown analysis (max, average)
- Sharpe ratio comparison
- Capital efficiency
- Number of RANGE blocks vs trades executed

### 3. **Findings Report** ⏳
- Document results
- Identify performance impact
- Recommend threshold adjustments if needed

### 4. **Phase 4: Range Strategy (Option B)** ⏳ (If beneficial)
- Only if Range blocks reduce losses significantly
- Implement range trading strategy (mean reversion)
- Keep as alternative, not default

## Files to Create/Modify

### New: Comprehensive Backtest Runner
- `backtest/phase3_full_period_backtest.py` (600 lines)
  - Load 2024-2025 historical data
  - Run with Range Policy enabled
  - Run without Range Policy (baseline)
  - Compare metrics side-by-side
  - Export results JSON

### New: Analysis & Reporting
- `backtest/phase3_analysis_report.py` (400 lines)
  - Parse backtest results
  - Generate metrics table
  - Create visualizations
  - Validate hypothesis (capital preservation)

### New: Range Policy Validation
- `backtest/validate_range_policy_performance.py` (300 lines)
  - Check RANGE blocks during known periods
  - Verify 5-bar persistence mechanism
  - Measure false positives/negatives

## Success Criteria

✅ Full 2024-2025 backtest completes
✅ Range Policy blocks trades during RANGE periods
✅ Capital preservation verified (lower max drawdown)
✅ Metrics comparison exported
✅ Findings documented

## Timeline
- This session: Create backtest runner + run initial tests
- Next session: Analysis + findings report

## Key Metrics to Track
- Total trades executed vs RANGE blocks
- Win rate (with vs without Range Policy)
- Max drawdown (with vs without)
- Profit factor (with vs without)
- % of time in RANGE regime

## Expected Outcomes
1. Validate Range Policy effectiveness
2. Confirm capital preservation hypothesis
3. Quantify performance impact
4. Decision point: Fine-tune thresholds or proceed to Phase 4
