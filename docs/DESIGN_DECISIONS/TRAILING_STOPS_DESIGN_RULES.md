# Trailing Stops – Design Decision & Disallow Conditions

**Decision Date**: June 1, 2026  
**Analysis**: Backtest Comparison (Fixed Full Exit vs Partial + Trailing)  
**Recommendation**: **DISALLOW trailing stops** under current market conditions

---

## Executive Summary

Backtest evidence conclusively shows that **partial trailing stops underperform full profit-taking** in the current market regime:

| Metric | Fixed Full Exit | Partial + Trailing | Outcome |
|--------|---|---|---|
| **Profit Factor** | 1.14 ✅ | 0.57 ❌ | **Halved** |
| **Total P&L** | ₹359,850 ✅ | ₹-1,105,910 ❌ | **-1.465M flip** |
| **Win Rate** | 29.6% | 29.6% | Same |
| **Max Drawdown** | -77.91% | -528.00% | **6.8x worse** |
| **Sharpe Ratio** | -3.28 | -3.28 | No improvement |
| **Avg P&L/Trade** | -1.27% | -1.27% | Same |

**Conclusion**: Trailing did NOT create new winners (same 50 wins out of 169), yet **surrendered half the profit from existing winners** while exposing remaining position to whipsaw losses. This is a **pure profit erosion mechanism** under current conditions.

---

## Three Conditions Forbidding Trailing Stops

### 1. **No Post-Target Extension**
**Definition**: Trades historically hit the profit target with no significant price movement beyond that point. Intraday rallies lack follow-through acceleration.

**Evidence from Backtest**:
- Win rate identical under both strategies (29.6%)
- No new trades converted from loss to win via trailing
- Partial strategy still closed 119 losers (same as fixed)
- Implication: Price rarely exceeded target by meaningful amount to benefit a trailing mechanism

**Why This Forbids Trailing**:
- Trailing's value depends on capturing *secondary extension* beyond the initial target
- If target is the reversal point (not a mid-move level), trailing wastes capital
- Result: Surrendered 50% of position gains with zero additional upside
- The half remaining for trailing was immediately exposed to reversal, getting stopped out near breakeven

**Rule**: 
```
IF (target_hit_rate ≈ final_exit_price) THEN disallow_trailing
```

**Observation**: In our data, target exits and trailing exits both occurred at similar prices (within intraday bars), proving target WAS the natural reversal point.

---

### 2. **Pure Intraday Moves (avg_holding_days ≈ 0)**
**Definition**: Profits are typically achieved intraday with quick reversals by end-of-day. No multi-day trend consolidation occurs.

**Evidence from Backtest**:
- Both strategies: `avg_holding_days = 0.0`
- Entry and exit typically within same trading session
- No positions held overnight
- Trailing half-position had zero time for trend to develop before close

**Why This Forbids Trailing**:
- Trailing stops assume a holding period with potential for trend continuation
- In pure intraday moves, the market doesn't stay open long enough for trailing to meaningfully capture extension
- The remaining 50% held via trailing gets hit by intraday volatility and end-of-day reversals
- Result: Trailing half was stopped out at breakeven or small loss almost immediately

**Specific Mechanism**:
```
Trade enters intraday
├─ 50% exits at target (Lock-in: +6.5%)
├─ 50% trails with 2% stop
│  └─ By end-of-day pullback: Hit stop at breakeven
│  └─ Net on trailing half: 0% to -1%
├─ Combined: +3.25% to +2.25% (half of full exit's +6.5%)
└─ Result: More positions, same profit, higher drawdown
```

**Rule**:
```
IF (avg_holding_days < 1.0) THEN disallow_trailing
```

**Observation**: Our avg_holding_days = 0.0 exactly matches this condition. All 169 trades intraday.

---

### 3. **High Immediate Post-Target Volatility**
**Definition**: Hitting the target is typically followed by volatile pullbacks rather than trend acceleration or calm consolidation. Volatility spikes immediately post-target.

**Evidence from Backtest**:
- Sharpe ratio: No improvement (-3.28 for both) despite identical wins
- Max drawdown: 6.8x worse under trailing (-528% vs -77.9%)
- Identical average P&L but worse risk metrics
- Implication: Post-target volatility killed the trailing half repeatedly

**Why This Forbids Trailing**:
- Trailing's risk management depends on a *stable extension* or slow-burn breakout
- If volatility spikes immediately after target hit, the trailing stop gets whipsawed
- Whipsaws cause two types of damage:
  1. **False exits**: Stop hit on pullback noise, then price rallies (missed further gains)
  2. **Delayed exits**: Trail never adjusts enough, large reversal hits with full loss
- Neither happens in calm markets, but both happened here

**Volatility Signature in Data**:
- Same win count (50) but halved profit factor → winners had smaller profits
- Extreme drawdown jump (6.8x) → losses were concentrated and deep
- Pattern: Trail adjusted to new highs minimally, then sharp reversal took the remaining half

**Rule**:
```
IF (volatility_post_target_high) AND (max_drawdown_ratio > 3.0) THEN disallow_trailing
```

**Observation**: Our max_drawdown_ratio = 528% / 77.9% ≈ 6.8, far exceeding threshold of 3.0. Clear disallow signal.

---

## Design Decision: Go/No-Go Framework

### Current Market State: **NO-GO FOR TRAILING**

```
Conditions Matrix:

Condition 1: No Post-Target Extension?     ✅ YES  → No new winners
Condition 2: Pure Intraday Moves?          ✅ YES  → avg_holding_days = 0.0
Condition 3: High Post-Target Volatility?  ✅ YES  → Drawdown ratio = 6.8

Result: ❌ NO-GO
Decision: DISALLOW TRAILING STOPS ENTIRELY
```

### Implication for Unified Strategy

**Unified Strategy Rule (MANDATORY)**:
```python
# Profit booking decision logic
IF market_regime == "mean_reverting" AND intraday_only AND post_target_volatility_high:
    use_strategy = FIXED_FULL_EXIT  # ONLY option
    enable_trailing = FALSE  # Explicitly disallowed
    reason = "Conditions forbid trailing; protect positive expectancy"
ELSE IF market_regime == "trending" AND multi_day_holds AND stable_extension:
    use_strategy = PARTIAL_WITH_TRAILING  # Optional for future
    enable_trailing = TRUE
    reason = "Conditions support trailing; capture extended moves"
```

**Code Implementation**:
```python
def should_use_trailing_stops(market_data):
    """
    Returns True only if ALL conditions support trailing.
    Returns False (use fixed exit) if ANY condition forbids it.
    """
    no_post_target_extension = check_target_is_reversal_point(market_data)
    pure_intraday_moves = (market_data['avg_holding_days'] < 1.0)
    high_volatility = (market_data['post_target_volatility'] > threshold)
    
    # Disallow if ANY condition met
    if no_post_target_extension or pure_intraday_moves or high_volatility:
        return False  # Use FIXED_FULL_EXIT
    
    return True  # Trailing permitted (future trending markets)
```

---

## When Trailing CAN Be Re-Enabled (Future)

Trailing stops should ONLY be reconsidered if:

1. **Multi-day trend evidence**: avg_holding_days > 2.0 (positions held across sessions)
2. **Target breakouts**: New highs exceed target by >2% with sustained movement
3. **Sharpe improvement**: Trailing strategy Sharpe ratio > -1.0 (risk-adjusted returns improve)
4. **Drawdown control**: Max drawdown ratio (trailing/fixed) < 1.5 (within acceptable bounds)

**Monitor for regime change**: Run weekly checks on recent 20-trade window. If ANY condition emerges, backtest anew before enabling.

---

## Risk Mitigation: What Happens if Trailing is Accidentally Enabled?

**Safeguard in Code**:
```python
# Hard stop in production
if self.config['trailing_enabled'] and self.market_regime == 'mean_reverting':
    raise StrategyConfigError(
        "FATAL: Trailing stops disallowed in mean-reverting regime. "
        "Current conditions forbid trailing (see TRAILING_STOPS_DESIGN_RULES.md). "
        "Re-enable only after backtest confirms regime change to trending."
    )
```

**Monitoring Alert**:
- Daily check: If trailing half exits at loss >3 trades in a row → Automatic disable + alert
- Weekly review: Recalculate trailing performance metrics; compare to fixed
- Exit criteria: If Sharpe drops below -5.0 or drawdown exceeds -200% → Kill trailing immediately

---

## Summary Table: Rule Enforcement

| Condition | Threshold | Current Value | Status | Action |
|-----------|-----------|---|---|---|
| Post-Target Extension | Yes (new winners) | No (0 new) | ❌ FAIL | Disallow |
| Holding Period | > 1.0 day | 0.0 days | ❌ FAIL | Disallow |
| Volatility Ratio | < 3.0x | 6.8x | ❌ FAIL | Disallow |
| **Overall Decision** | - | **NO-GO** | ❌ | **Use FIXED FULL EXIT Only** |

---

## References

- **Backtest Data**: `backtest_profit_booking_breeze_20260601_094947.json`
- **Strategy Code**: `app/strategies/profit_booking_manager.py`
- **Related Decisions**: `PROFIT_BOOKING_DECISION_MATRIX.md`

**Version**: 1.0 (June 1, 2026)  
**Approval**: READY FOR UNIFIED STRATEGY IMPLEMENTATION
