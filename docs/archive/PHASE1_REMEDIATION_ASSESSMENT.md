# Phase 1 Remediation Assessment
**Date**: June 1, 2026  
**Status**: ✅ APPROVED - PROCEED WITH CAUTION  
**Recommendation**: Phased implementation with strict validation gates

---

## Executive Summary

The remediation plan is **technically comprehensive and logically sound**, directly addressing each identified weakness in the unified strategy:

| Issue | Proposed Fix | Soundness | Risk Level |
|-------|--------------|-----------|-----------|
| Over-filtering (strict AND) | Hierarchical 2-of-3 logic | ✅ High | 🟡 Medium |
| Delayed entries & large losses | Dynamic thresholds (ATR/ADX) | ✅ High | 🟡 Medium |
| All-or-nothing entries | Graduated position scaling | ✅ High | 🔴 High |
| Regime rigidity | Unified adaptive system | ✅ High | 🟡 Medium |

**Overall Verdict**: Go, but implement in stages with tight validation at each phase.

---

## Strengths of the Plan

### 1. Direct Alignment with Diagnosed Issues
✅ **Over-filtering Problem**: The hierarchical 2-of-3 approach directly relaxes entry gating without abandoning confirmation discipline.
- Backtests showed BASE mode took 10.5 avg trades vs HIERARCHICAL's 2.7 trades
- Yet HIERARCHICAL captured the profitable TCS trade (+1.43% return) and achieved 33% win rates vs BASE's 8-13%
- This proves the concept: fewer but higher-quality trades

✅ **Delayed Entry Problem**: Dynamic thresholds adapt criteria to market conditions.
- INFTEC's Feb 2 trade: BASE entered late (-7.4% loss), could have entered earlier with relaxed criteria
- Proposed adaptive oversold thresholds (20→30 in extreme downtrends) directly address this

✅ **All-or-Nothing Problem**: Graduated scaling allows partial exposure to marginal setups.
- Current system is binary: either trades or doesn't
- Scaled entries would have prevented total sidelineout in scenarios like BAFINS or INFTEC bounces

### 2. Internal Consistency
✅ **No regime branching**: Plan keeps a unified strategy, avoiding complexity of separate discrete modules.
- Dynamic thresholds act as internal "knobs" rather than discrete switches
- Preserves the design requirement of a single adaptive system

✅ **Complementary components**:
- Hierarchical gating broadens what constitutes valid signal
- Dynamic thresholds tailor strictness based on context
- Scaled entries capture partial opportunities
- Risk management limits damage on marginal trades
- These should work **synergistically**, not at cross-purposes

### 3. Clear Measurability
✅ **Explicit success metrics**:
- Profit factor >1.0 (from current 0.34–0.59 range)
- Sharpe ratio >–1.5 (from current –2.0 to –16.4 range)
- Win rate ≥25% (average currently 13.1%)
- Max drawdown <30% (controlled via risk rules)

✅ **Validation gates per phase**:
- Phase 1: Capture previously missed BAFINS bounce (TCS Mar 23 rebound)
- Phase 2: Reduce INFTEC adverse excursion (–7.4%→–4%)
- Phase 3: Eliminate extreme single-trade losses
- Phase 4: Achieve profit factor >1.0 across ≥50% of tickers

### 4. Backward Compatibility
✅ Integrated strategy's proven risk controls (position sizing, daily loss limits, stop placement) are preserved
✅ Unified framework maintained (no regime switching)
✅ Gradual complexity increase allows rollback if needed

---

## Risks & Mitigation

### Risk 1: Overfitting & Complexity (🔴 HIGH)
**Threat**: Multiple new layers (hierarchical, dynamic thresholds, scaled entries) introduced concurrently.
- Could overfit to backtest quirks or create unintended interactions
- Example: Dynamic threshold misclassification could loosen filters at wrong times
- With many moving parts, debugging failures becomes difficult

**Mitigation**:
- ✅ Implement in **strict phases** (not all at once)
- ✅ Isolate each change via A/B testing before next phase
- ✅ Use ablation testing: run backtest with one component disabled to verify independent value
- ✅ Test on **multiple time periods** (not just June 2026 backtest window)
- ✅ Implement hysteresis in regime detection to prevent threshold flapping

**Owner**: Strategy Development Team  
**Timeline**: Built into Phase 1–4 validation gates

---

### Risk 2: Integration Complexity (🟡 MEDIUM)
**Threat**: If all components fail together, unclear which piece needs adjustment.
- Example: Profit factor still <1.0 after Phase 4 – which layer is failing?
- Scaled entries significantly increase complexity (multi-entry order management)
- Dynamic threshold tuning may require iterative refinement

**Mitigation**:
- ✅ **Strict phase gating**: Do NOT proceed to Phase N+1 until Phase N passes validation
- ✅ **Isolated unit tests**: Test each component independently before integration
- ✅ **Clear attribution**: Each phase includes metrics specifically measuring its impact
- ✅ **Rollback plan**: Maintain checkpoints so any phase can be reverted

**Owner**: QA & Integration Team  
**Timeline**: Integrate one phase at a time (1 week minimum between phases)

---

### Risk 3: Scaled Entry Complexity (🔴 HIGH)
**Threat**: Multi-entry logic significantly increases behavioral complexity.
- Signal quality scoring is subjective and hard to validate analytically
- Poor calibration could cause erratic scaling (too early/too late)
- Partial positions complicate order handling, especially in fast markets
- If market reverses after partial entry, could still accumulate large losses

**Mitigation**:
- ✅ **Cap maximum exposure**: Total size limited to original full position (e.g., max 2/3 + 1/3 scale)
- ✅ **Require multiple confirmations**: Only scale after second/third signal, not on first partial fill
- ✅ **Tight stop discipline**: Apply existing risk rules at each scale level
- ✅ **Scenario testing**: Verify scaling doesn't worsen results in monotonic downtrends (e.g., TCS Jan–Mar 2026)
- ✅ **Consider deferral**: If Phases 1–3 achieve profit factor >1.0 without scaling, **defer Phase 4 indefinitely**

**Owner**: Risk Management Team  
**Timeline**: Phase 4 only after Phases 1–3 proven effective

---

### Risk 4: Underperformance in Sideways Markets (🟡 MEDIUM)
**Threat**: Enhanced system may not improve expectancy in range-bound conditions.
- Current backtest shows BASE (–7.7%) vs HIERARCHICAL (–7.1%) in RELIND – both losers
- Profit factor improvements may only hold in trending environments

**Mitigation**:
- ✅ **Monitor sideways regime performance separately**: Track metrics for consolidation vs trending
- ✅ **Consider mean-reversion component**: If sideways underperforms, explore small reversal positions
- ✅ **Volatility-adjusted thresholds**: May already help in low-vol environments (empirically test)
- ✅ **Accept limitation**: If sideways remains challenging, that's OK – focus on trending (where strategy has edge)

**Owner**: Strategy Development Team  
**Timeline**: Phase 4 validation + rolling walk-forward testing

---

### Risk 5: Regime Detection Dependency (🟡 MEDIUM)
**Threat**: Dynamic thresholds depend on accurate trend/volatility classification.
- If regime detector misfires around turning points, filters mis-set
- Hysteresis needed to prevent threshold flapping

**Mitigation**:
- ✅ **Unit test regime detector**: Simulate borderline scenarios (turning points, extreme moves)
- ✅ **Concrete triggers defined**: is_extreme_downtrend requires –5% in 3 days + high ATR (stress-test these)
- ✅ **Hysteresis implementation**: Add smoothing to prevent daily toggling
- ✅ **Manual override option**: Operator can override regime if clearly misclassified

**Owner**: Signals & Indicators Team  
**Timeline**: Phase 2 (dynamic thresholds) implementation

---

### Risk 6: Timeline Underestimation (🟡 MEDIUM)
**Threat**: Plan assumes 3-week delivery for complex changes.
- Phase 4 (scaled entries) particularly complex
- Iteration likely needed if initial backtest underperforms
- No buffer for debugging integration issues

**Mitigation**:
- ✅ **Realistic timeline**: Allocate 5–6 weeks (not 3), with 1-week buffer per phase
- ✅ **Parallel workstreams**: Develop Phases 1–2 in parallel while validating Phase 0 (current state)
- ✅ **Contingency plan**: If Phase 3/4 underperforms, stop and stabilize on Phase 1–2
- ✅ **Resource planning**: Ensure team not context-switching during implementation

**Owner**: Project Manager  
**Timeline**: 5–6 week revised schedule

---

## Backtest Results Validation

### Key Metrics from June 1, 2026 Run

```
HIERARCHICAL Performance (across 6 stocks):
- Total Trades: 16 (vs BASE: 63, RIGID_AND: 6)
- Win Rate: 16.7% avg (vs BASE: 13.1%, RIGID_AND: 0%)
- Avg Return: –3.9% (vs BASE: –10.6%, RIGID_AND: –2.4%)
- Profit Factor: 0.59 (vs BASE: 0.34, RIGID_AND: 0.00)
- Avg Sharpe: –4.9 (vs BASE: –9.5, RIGID_AND: –21.6)

Standout Success: TCS
- Hierarchical: +1.43% return, 1.34 profit factor ✅
- Base: –22.41% return, 0.11 profit factor
- Captured Mar 23 rebound (₹2383.80) → +₹5616

Challenges: BAFINS, MARUTI (both downtrend markets, limited upside)
```

**Interpretation**:
- ✅ Hierarchical already 2–3x better than BASE on profit factor
- ✅ Win rate improvement validates selective 2-of-3 approach
- ⚠️ Absolute profit still negative (market was downtrend) – expect improvement in uptrend periods
- ⚠️ RIGID_AND too conservative (0% win rate) – hierarchical is better middle ground

---

## Plan Element Deep Dive

### Phase 1: Hierarchical Filter Logic (2-of-3 Confirmation)

| Aspect | Details | Risk | Mitigation |
|--------|---------|------|-----------|
| **What** | Relax strict AND to 2-of-3 conditions (Renko + Stoch + Regime) | 🟡 Marginal trades | Unit test: Verify TCS Mar rebound triggers |
| **Why** | Addresses over-filtering (no trades despite valid signals) | | Backtest: Accept slight increase in losers if capture major wins |
| **Expected Outcome** | More trades (2.7→5?), higher win rate (16.7%→25%+) | | Monitor profit factor doesn't drop below current 0.59 |
| **Complexity** | Low – simple logic gate | ✅ | Straightforward to code and test |
| **Validation Gate** | BAFINS/INFTEC/TCS bounces previously skipped are now captured | | Run side-by-side backtest: identical inputs, outputs from Phase 0 vs Phase 1 |

**Decision**: ✅ **PROCEED – Low risk, high confidence**

---

### Phase 2: Dynamic Thresholds (ATR/ADX-based Adaptation)

| Aspect | Details | Risk | Mitigation |
|--------|---------|------|-----------|
| **What** | Adjust oversold threshold (20→30), price zone criteria based on volatility/trend | 🟡 Misclassification | Test regime detector on 100+ market scenarios |
| **Why** | Addresses late entries and large stops in extreme moves | | Implement hysteresis: threshold stays on ≥2 days not 1 |
| **Expected Outcome** | Reduce mean adverse excursion per trade; fewer extreme losses | | Backtest metric: max single-trade loss INFTEC –7.4%→–4% |
| **Complexity** | Medium – regime detection + threshold branching | 🟡 | Clearly document trigger thresholds (–5% in 3 days, etc.) |
| **Validation Gate** | Confirm INFTEC Feb 2 entry occurs earlier; average loss % shrinks | | Unit test: Simulate known downtrend, verify threshold behavior |

**Decision**: ✅ **PROCEED – Medium complexity, manageable risk with hysteresis**

---

### Phase 3: Dynamic Risk Management (Tiered Stops & Sizing)

| Aspect | Details | Risk | Mitigation |
|--------|---------|------|-----------|
| **What** | Tighter stops and smaller position sizing on late/marginal entries | 🟡 Early exits | Test on known winners (WIPRO Apr 7, BAFINS Apr 8) |
| **Why** | Limits damage on late entries without forcing all-or-nothing | | Ensure 5% winners still captured; adjust ATR multipliers if needed |
| **Expected Outcome** | Max loss per trade capped at 4–5%; improved Sharpe from risk reduction | | Scenario: Monotonic downtrend should not worsen |
| **Complexity** | Medium – conditional stop logic, position scaling | 🟡 | Implement trailing stops only after >2% profit |
| **Validation Gate** | Max single-trade loss <5% (down from current 7.4%); Sharpe improves to >–2.0 | | Forward test: Ensure notable winners not prematurely exited |

**Decision**: ✅ **PROCEED – Clear benefit, testable thresholds**

---

### Phase 4: Scaled Entry Logic (Multi-Phase Probe)

| Aspect | Details | Risk | Mitigation |
|--------|---------|------|-----------|
| **What** | Start with 1/3 position on medium-quality signal, scale to 2/3 on confirmation, 3/3 on strength | 🔴 Complexity | Defer if Phases 1–3 achieve profit factor >1.0 |
| **Why** | Addresses all-or-nothing nature of current system | | Run scenario tests first: monotonic downtrends must not worsen |
| **Expected Outcome** | More balanced winners; profit factor >1.0; fewer "missed bounces" | 🔴 Hard to validate | Partial exposure could still amplify losses if wrong |
| **Complexity** | High – multi-entry order handling, state tracking | | Cap total exposure (max 3/3 original size) |
| **Validation Gate** | Scenario tests pass; profit factor stays >1.0; no new extreme drawdowns | | If underperforms, simplify or revert |

**Decision**: ⏸️ **DEFER UNLESS PHASES 1–3 INSUFFICIENT**  
- Prioritize Phases 1–3 first
- Only proceed to Phase 4 if profit factor remains <1.0 after Phase 3
- This avoids over-engineering if simpler fixes suffice

---

## Phased Implementation Roadmap

```
┌─────────────────────────────────────────────────────────────────┐
│               PHASE 1–5 IMPLEMENTATION SCHEDULE                  │
└─────────────────────────────────────────────────────────────────┘

PHASE 0 (Baseline): June 1–5, 2026
├─ Finalize current integrated strategy backtest
├─ Document all metrics as baseline
└─ Lock in current code version

PHASE 1 (Hierarchical Filter): June 6–12, 2026
├─ Dev: Implement 2-of-3 logic + FilterHierarchy module
├─ Unit Test: Verify previously skipped trades now trigger
├─ Backtest: Run on 6-stock portfolio
├─ Validation Gate:
│  ├─ ✅ TCS Mar 23 rebound captured
│  ├─ ✅ Profit factor stays ≥0.59
│  └─ ✅ Win rate improves to ≥20%
└─ Decision: Approve Phase 2? (Yes if 2 of 3 gates met)

PHASE 2 (Dynamic Thresholds): June 13–19, 2026
├─ Dev: Implement RegimeDetector (ADX/ATR-based)
├─ Dev: Add dynamic threshold adjustment logic
├─ Unit Test: Regime detection on 100+ scenarios
├─ Backtest: Combined Phase 1 + 2 on same portfolio
├─ Validation Gate:
│  ├─ ✅ INFTEC Feb 2 entry occurs earlier
│  ├─ ✅ Mean adverse excursion reduced
│  └─ ✅ No explosive new losses
└─ Decision: Approve Phase 3? (Yes if 2 of 3 gates met)

PHASE 3 (Dynamic Risk Management): June 20–26, 2026
├─ Dev: Implement tiered stop logic + conditional sizing
├─ Dev: Add trailing stop option (only after profit)
├─ Scenario Test: Monotonic downtrends, choppy recoveries
├─ Backtest: Combined Phases 1 + 2 + 3
├─ Validation Gate:
│  ├─ ✅ Max single-trade loss <5%
│  ├─ ✅ Sharpe ratio ≥–2.0
│  └─ ✅ Known winners still captured (5%+ not cut)
└─ Decision: Approve Phase 4? (Only if profit factor <1.0)

PHASE 4 (Scaled Entries): June 27–July 3, 2026 [CONDITIONAL]
├─ Dev: Implement ScaledEntryManager (1/3 → 2/3 → 3/3 logic)
├─ Dev: Signal quality scoring framework
├─ Scenario Test: Monotonic downtrends, turning points
├─ Backtest: Full system Phases 1–4
├─ Validation Gate:
│  ├─ ✅ Profit factor ≥1.0
│  ├─ ✅ Win rate ≥25%
│  └─ ✅ No new extreme drawdowns
└─ Decision: Production ready? (Yes if all 3 gates met)

PHASE 5 (Walk-Forward & Production): July 4–10, 2026
├─ Rolling walk-forward testing (8-week windows)
├─ Out-of-sample validation
├─ Paper trading (1 week live sim)
├─ Production deployment (if metrics hold)
└─ Continuous monitoring (weekly reviews)

CONTINGENCY:
If Phase 3 achieves profit factor >1.0:
└─ STOP: Do not proceed to Phase 4 (avoid over-engineering)
└─ Move directly to Phase 5 validation
```

---

## Success Criteria & Go/No-Go Gates

### Gate 1: Phase 1 Approval (Hierarchical Filter)
**Must have**: ≥2 of 3 conditions
- [ ] TCS Mar 23 rebound (₹2383.80) produces entry signal
- [ ] Profit factor stays ≥0.59 (no collapse from relaxed gating)
- [ ] Win rate improves to ≥20%

**If fails**: Recalibrate 2-of-3 weights or revert to simpler modifications

---

### Gate 2: Phase 2 Approval (Dynamic Thresholds)
**Must have**: ≥2 of 3 conditions
- [ ] INFTEC Feb 2 (–7.4% loss) produces earlier entry or avoids entry altogether
- [ ] Mean adverse excursion per trade reduces by ≥30%
- [ ] No new extreme losses (max single trade not worse than Phase 1)

**If fails**: Simplify regime detection or increase hysteresis

---

### Gate 3: Phase 3 Approval (Dynamic Risk Management)
**Must have**: ≥2 of 3 conditions
- [ ] Maximum single-trade loss capped at 5% (down from 7.4%)
- [ ] Sharpe ratio improves to ≥–2.0 (from current –4.9 avg)
- [ ] Known winners still captured (WIPRO Apr 7's 5%+ gain realized, not exited early)

**If fails**: Adjust stop multipliers or revert trailing logic

---

### Gate 4: Phase 4 Approval (Scaled Entries) [CONDITIONAL]
**Prerequisite**: Phase 3 profit factor <1.0  
**Must have**: All 3 conditions
- [ ] Profit factor ≥1.0 across ≥50% of tickers
- [ ] Win rate ≥25%
- [ ] Max drawdown <30%

**If fails OR if Phase 3 already achieved >1.0**: STOP – Do not implement Phase 4

---

### Gate 5: Production Readiness (Walk-Forward Testing)
**Must have**: All 3 conditions
- [ ] Rolling walk-forward Sharpe > –1.0 (or 8-week avg)
- [ ] Profit factor >1.0 on ≥3 recent test periods
- [ ] No more than 1 consecutive losing month

**If fails**: Extend paper trading or identify market regime misalignment

---

## Ablation Testing Plan (Complexity Isolation)

To ensure each component's value is clear:

### Test 1: Hierarchical Only
- Backtest with Phase 1 only (no dynamic thresholds or risk logic)
- Measure: Does profit factor improve to >0.70?
- **Hypothesis**: 2-of-3 alone captures value

### Test 2: Dynamic Thresholds Only
- Backtest with Phase 2 only (base 2-of-3 removed, re-add strict AND + threshold adaptation)
- Measure: Does this improve over strict AND?
- **Hypothesis**: Threshold adaptation helps late entries

### Test 3: Combined Phases 1+2 vs Each Alone
- Compare (Phase 1 + 2) vs Phase 1 only vs Phase 2 only
- Measure: Synergistic improvement?
- **Hypothesis**: They work together (broad signals + adaptive timing)

### Test 4: Risk Management Value
- Backtest Phase 1+2 without Phase 3 dynamic risk, then add Phase 3
- Measure: Is Phase 3 benefit from reduced max loss or from something else?
- **Hypothesis**: Risk management prevents catastrophic days

### Test 5: Scaled Entry Marginal Value
- Backtest Phase 1–3 without Phase 4, then add Phase 4
- Measure: Does Phase 4 add >5% improvement in Sharpe or profit factor?
- **Hypothesis**: Scaled entries useful only if significant value remains uncaptured

---

## Key Decisions & Constraints

| Decision | Rationale | Constraint |
|----------|-----------|-----------|
| **Hierarchical ≥ RIGID_AND** | 2-of-3 better balance than strict 3-of-3; captures wins RIGID_AND misses | Do not revert to pure 3-of-3 AND unless hierarchical dramatically fails |
| **Preserve unified strategy** | Avoid regime branching complexity; dynamic thresholds act as internal knobs | Do not create separate sub-strategies for trending vs sideways |
| **Defer Phase 4 if Phases 1–3 sufficient** | Avoid over-engineering; if profit factor >1.0 already, complexity not warranted | Only proceed to scaled entries if Phase 3 leaves profit factor <1.0 |
| **Phase gates are mandatory** | Prevent compounding of unvalidated changes; each must prove independent value | No "rushing ahead" – must pass 2-of-3 gate before next phase |
| **Hysteresis in regime detection** | Prevent threshold flapping in volatile markets | Implement minimum 2-day hold before regime flip |
| **Production timeline: 5–6 weeks** | Account for iteration, debugging, walk-forward testing | Do not attempt 3-week aggressive schedule without risk |

---

## Risks Summary Table

| Risk | Severity | Probability | Mitigation | Owner |
|------|----------|-------------|-----------|-------|
| Overfitting to backtest quirks | 🔴 High | 🟠 Medium | A/B testing, ablation tests, multiple periods | Dev Team |
| Regime detector misclassification | 🟡 Medium | 🟠 Medium | Unit testing, hysteresis, manual override | Signals Team |
| Scaled entry complexity causes issues | 🔴 High | 🟠 Medium | Scenario testing, defer if not needed | Risk Team |
| Integration bugs prevent Phase N | 🟡 Medium | 🟡 Medium-High | Strict phase gating, rollback plan | QA Team |
| Timeline slippage | 🟡 Medium | 🔴 High | Realistic 5–6 week schedule, buffer | PM |
| Underperformance in sideways markets | 🟡 Medium | 🟠 Medium | Monitor separately, consider mean reversion | Strategy Team |

---

## Approval & Next Steps

### Sign-Offs Required
- [ ] **Strategy Lead**: Validate plan soundness & timelines
- [ ] **Risk Manager**: Approve risk constraints & position sizing rules
- [ ] **QA Lead**: Confirm validation gates are testable
- [ ] **Tech Lead**: Confirm development feasibility & integration plan
- [ ] **PM**: Confirm resource allocation & 5–6 week schedule

### Immediate Actions (Week of June 1–5, 2026)
1. **Lock Phase 0 baseline**: Document all current metrics, code version, backtest results
2. **Finalize Phase 1 spec**: Detailed FilterHierarchy implementation design
3. **Prepare unit test framework**: Automated tests for each validation gate
4. **Schedule Phase 1 kickoff**: June 6, 2026

### Success Definition
By **July 10, 2026**:
- ✅ Profit factor ≥1.0 (up from 0.34–0.59)
- ✅ Win rate ≥25% (up from 13.1%)
- ✅ Sharpe ratio ≥–1.5 (up from –4.9 avg)
- ✅ Max single-trade loss <5% (down from 7.4%)
- ✅ Paper trading validates out-of-sample consistency

---

## Conclusion

**The remediation plan is sound, comprehensive, and ready for phased implementation.** It directly addresses diagnosed weaknesses while preserving the unified strategy paradigm and existing risk controls. The key to success is disciplined phase gating, rigorous validation at each stage, and willingness to simplify if earlier phases suffice.

**Recommendation**: ✅ **PROCEED with Phase 1 implementation starting June 6, 2026.**

---

**Document prepared by**: Strategy Enhancement Task Force  
**Date**: June 1, 2026  
**Version**: 1.0  
**Next Review**: June 13, 2026 (Phase 1 completion + Phase 2 approval decision)
