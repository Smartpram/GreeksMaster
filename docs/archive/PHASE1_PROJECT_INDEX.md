# MyBreezeApp – Phase 1 Remediation Project Index

**Status**: ✅ APPROVED FOR IMPLEMENTATION  
**Project Start**: June 1, 2026  
**Phase 1 Duration**: June 6–12, 2026  
**Overall Timeline**: June 1 – July 10, 2026 (Phases 1–5)

---

## 📋 Document Index

This directory contains the complete Phase 1 Remediation project documentation. All documents are interconnected and should be read in the following order:

### 1. **START HERE** – PHASE1_EXECUTIVE_SUMMARY.md
   - 📄 **Purpose**: High-level overview, decision log, approval matrix
   - 📄 **Audience**: Executive Sponsor, Strategy Lead, Stakeholders
   - 📄 **Length**: ~10 pages
   - 🎯 **Key Takeaway**: Proceed with Phase 1 (hierarchical 2-of-3 voting); expect profit factor 0.59 → 0.70+

### 2. **DEEP DIVE** – PHASE1_REMEDIATION_ASSESSMENT.md
   - 📄 **Purpose**: Comprehensive analysis of plan soundness, risks, mitigations
   - 📄 **Audience**: Strategy Development Team, Risk Management, QA
   - 📄 **Length**: ~30 pages
   - 🎯 **Key Takeaway**: Plan is technically sound but ambitious; phased implementation essential

### 3. **BUILD SPEC** – PHASE1_IMPLEMENTATION_SPEC.md
   - 📄 **Purpose**: Detailed implementation guide, code structure, unit tests, validation gates
   - 📄 **Audience**: Development Team, QA Team
   - 📄 **Length**: ~20 pages
   - 🎯 **Key Takeaway**: 5 development tasks, 8 unit tests, 4 validation gates, 1-week delivery

### 4. **BACKTEST RESULTS** – phase1_remediation_backtest_20260601_091057.json
   - 📄 **Purpose**: Raw backtest data from June 1, 2026 run
   - 📄 **Audience**: Strategy Analysts, Performance Reviewers
   - 📄 **Format**: JSON (structured metrics, per-trade details)
   - 🎯 **Key Takeaway**: TCS +1.43% (hierarchical), profit factor 0.59 (vs 0.34 base)

### 5. **BASELINE** – copilot-instructions.md (Existing)
   - 📄 **Purpose**: Project context, architecture, existing strategy
   - 📄 **Audience**: New team members, architecture review
   - 🎯 **Key Takeaway**: Buy & Hold trend-following with RSI/MA/volume analysis

---

## 🗂️ File Structure

```
c:\Data\MyBreezeApp\
├── PHASE1_EXECUTIVE_SUMMARY.md                         ← START HERE (Decision Log)
├── PHASE1_REMEDIATION_ASSESSMENT.md                    ← Deep Dive (Risk Analysis)
├── PHASE1_IMPLEMENTATION_SPEC.md                       ← Build Spec (Code Tasks)
├── phase1_remediation_backtest_20260601_091057.json    ← Raw Results
├── phase1_backtest_output.txt                          ← Backtest Log
├── .github/copilot-instructions.md                     ← Project Context
│
├── app/
│   └── strategies/
│       ├── enhanced_signal_confirmation.py             (Existing)
│       ├── advanced_signal_validators.py               (To be modified Phase 1)
│       ├── filter_hierarchy.py                         (NEW – Phase 1 Task 1)
│       ├── signal_router.py                            (NEW – Phase 1 Task 3)
│       └── [other strategy modules]
│
└── tests/
    └── test_filter_hierarchy.py                        (NEW – Phase 1 Task 4)
```

---

## 🚀 Quick Start (For Developers)

If you're implementing Phase 1, follow these steps:

### Week 1: June 6–12, 2026

**Monday, June 6**:
```
1. Read: PHASE1_EXECUTIVE_SUMMARY.md (30 min)
2. Read: PHASE1_IMPLEMENTATION_SPEC.md § 1–3 (1 hour)
3. Task: Create FilterHierarchy class (app/strategies/filter_hierarchy.py)
   └─ Reference: Implementation Spec § 3.1 (skeleton provided)
   └─ Definition of Done: 200 lines, docstrings, passes basic syntax check
4. Task: Adapt existing filters for hierarchical mode
   └─ Reference: Implementation Spec § 3.2
   └─ Definition of Done: Each filter returns signal +1/0/-1 + metadata
```

**Tuesday, June 7**:
```
1. Task: Create signal router (signal_router.py)
   └─ Reference: Implementation Spec § 3.3
   └─ Definition of Done: Mode switching logic, backward compatible
2. Task: Write unit tests (tests/test_filter_hierarchy.py)
   └─ Reference: Implementation Spec § 3.4 (8 test cases)
   └─ Definition of Done: All 8 tests pass, ≥95% coverage
3. Code review: Pair review of filter_hierarchy.py with QA lead
```

**Wednesday, June 8**:
```
1. Task: Integration testing
   └─ End-to-end signal flow: data → filter → signal → trade
   └─ Definition of Done: No crashes, expected behavior on known cases
2. Task: Run backtest
   └─ Command: python phase1_remediation_backtest.py --mode hierarchical
   └─ Definition of Done: Complete without errors, results saved to JSON
3. Analysis: Preliminary validation gate assessment
```

**Thursday, June 9**:
```
1. Task: Validation gate assessment
   └─ Compare hierarchical vs base on all 6 stocks
   └─ Gate 1: TCS Mar 23 entry? (YES/NO)
   └─ Gate 2: Profit factor ≥0.59? (YES/NO)
   └─ Gate 3: Win rate ≥20%? (YES/NO)
   └─ Gate 4: Max loss <7.4%? (YES/NO)
2. Decision: Pass ≥2 gates?
   └─ YES → Proceed to Phase 2 kickoff
   └─ NO → Convene recalibration meeting
3. Documentation: Draft PHASE1_VALIDATION_REPORT.md
```

**Friday, June 10** (Contingency):
```
If Phase 1 validation passed:
├─ Finalize code review comments
├─ Update documentation (docstrings, config examples)
├─ Prepare Phase 2 design inputs
└─ Team stand-down/prep for Phase 2

If Phase 1 validation failed:
├─ Root cause analysis
├─ Recalibration plan (adjust quality weights, add hysteresis, etc.)
├─ Retest decision: Continue iteration or escalate?
└─ Timeline adjustment if needed
```

---

## 📊 Success Criteria (Phase 1 Approval)

**Must Pass ≥2 of 4 Gates**:

| Gate | Test | Success Criterion | Status |
|------|------|-------------------|--------|
| **1** | TCS Mar 23 entry capture | Hierarchical produces entry @ ₹2383.80, quality_score ≥0.75 | 🔄 Pending |
| **2** | Profit factor regression | Hierarchical PF ≥0.59 (no regression from baseline) | 🔄 Pending |
| **3** | Win rate improvement | Hierarchical WR ≥20% (up from 16.7% baseline) | 🔄 Pending |
| **4** | Risk controlled | Max single-trade loss <7.4% (same as baseline) | 🔄 Pending |

**Approval Threshold**: ≥2 gates pass → ✅ Phase 2 approved  
**Failure Threshold**: <2 gates pass → ⏸️ Recalibrate or escalate

---

## 🔄 Phase Overview (Phases 1–5)

```
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 1: Hierarchical Filter Logic (Jun 6–12)                    │
├──────────────────────────────────────────────────────────────────┤
│ ✓ 2-of-3 voting system                                           │
│ ✓ Adaptive quality scoring                                       │
│ ✓ TCS +1.43% already captured in baseline                        │
│ TARGET: Profit Factor 0.59 → 0.70+                              │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 2: Dynamic Thresholds (Jun 13–19) [IF Phase 1 Pass]       │
├──────────────────────────────────────────────────────────────────┤
│ ✓ ATR/ADX-based regime detection                                 │
│ ✓ Adaptive oversold thresholds (20 → 30 in extreme downtrends)  │
│ ✓ Reduce mean adverse excursion                                  │
│ TARGET: Earlier entries, fewer extreme losses                    │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 3: Dynamic Risk Management (Jun 20–26) [IF Phase 2 Pass]  │
├──────────────────────────────────────────────────────────────────┤
│ ✓ Tiered stop-loss logic                                         │
│ ✓ Conditional position sizing                                    │
│ ✓ Trailing stops (only after profit)                             │
│ TARGET: Max loss <5%, Sharpe >–2.0                              │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 4: Scaled Entries [CONDITIONAL] (Jun 27–Jul 3)           │
├──────────────────────────────────────────────────────────────────┤
│ ⏸ Deferred unless Phase 3 profit factor <1.0                    │
│ • 1/3 probe, 2/3 confirmation, 3/3 strength                     │
│ TARGET: Profit factor >1.0, Win rate >25%                       │
│ RISK: High complexity; proceed only if necessary               │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 5: Walk-Forward & Production (Jul 4–10)                   │
├──────────────────────────────────────────────────────────────────┤
│ ✓ 8-week rolling walk-forward testing                            │
│ ✓ Out-of-sample validation                                      │
│ ✓ Paper trading (1 week live sim)                                │
│ ✓ Production deployment (if metrics hold)                        │
│ TARGET: Live trading ready by July 10                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Metrics to Track

### Baseline (Phase 0 – June 1, 2026)
```
BASE Mode (Current):
├─ Profit Factor: 0.34 (6-stock avg)
├─ Win Rate: 13.1%
├─ Trades: 63
├─ Max Loss: 7.4% (INFTEC)
└─ Sharpe: –9.5 avg

HIERARCHICAL Mode (Phase 0 Baseline):
├─ Profit Factor: 0.59 ✅ (already 73% better)
├─ Win Rate: 16.7%
├─ Trades: 16 (78% fewer, but better quality)
├─ Max Loss: 2.6% (INFTEC improved)
└─ Sharpe: –4.9 avg (45% better)
└─ BEST: TCS +1.43%, PF 1.34 ✅
```

### Phase 1 Target (By June 12)
```
TARGET After Phase 1 Optimization:
├─ Profit Factor: 0.70+ (vs 0.59 baseline)
├─ Win Rate: 22%+ (vs 16.7% baseline)
├─ Trades: 15–20 (consistent quality)
├─ Max Loss: <7.4% (no regression)
└─ Sharpe: –3.5+ avg (better risk-adjusted returns)
└─ STABLE: TCS +1.43% still captured
```

### Phases 2–5 Targets (Cumulative)
```
Phase 2: Add dynamic thresholds
├─ Profit Factor: 0.75+ (cumulative improvement)
├─ Win Rate: 24%+
└─ Max Loss: 5% (adverse excursion reduced)

Phase 3: Add dynamic risk management
├─ Profit Factor: 0.85+ (further improvement)
├─ Win Rate: 25%+
├─ Sharpe: –2.0 (significant risk reduction)
└─ Max Loss: <5% (tight risk control)

Phase 4: Add scaled entries (IF NEEDED)
├─ Profit Factor: >1.0 ✅ (breakeven to profit)
├─ Win Rate: 25%+
├─ Sharpe: –1.0+ (acceptable risk-return)
└─ Deployment ready

Phase 5: Production validation
├─ Profit Factor: >1.0 (sustained out-of-sample)
├─ Win Rate: 25%+ (consistent)
├─ Live trading commenced
└─ Continuous monitoring
```

---

## ⚠️ Risk Summary

| Risk | Severity | Phase | Mitigation |
|------|----------|-------|-----------|
| Overfitting to backtest | 🟡 Medium | 1–4 | Ablation testing, multiple periods |
| Regime misclassification | 🟡 Medium | 2 | Hysteresis, manual override |
| Scaled entry complexity | 🔴 High | 4 | Scenario testing, deferred if not needed |
| Integration bugs | 🟡 Medium | 1 | Strict phase gating, rollback plan |
| Timeline slippage | 🟡 Medium | All | Realistic schedule, contingency days |
| Underperformance sideways | 🟡 Medium | 2–3 | Monitor separately, mean reversion option |

---

## 📞 Contacts & Approvers

| Role | Name | Email | Phone |
|------|------|-------|-------|
| **Strategy Lead** | [TBD] | [TBD] | [TBD] |
| **QA Lead** | [TBD] | [TBD] | [TBD] |
| **Risk Manager** | [TBD] | [TBD] | [TBD] |
| **Project Manager** | [TBD] | [TBD] | [TBD] |
| **Dev Lead** | [TBD] | [TBD] | [TBD] |

---

## 📅 Key Dates & Milestones

| Date | Milestone | Owner | Status |
|------|-----------|-------|--------|
| **Jun 1** | Phase 1 Remediation Approved | Executive | ✅ Done |
| **Jun 6** | Phase 1 Implementation Starts | Dev | 🔄 Pending |
| **Jun 9** | Phase 1 Backtest Complete | Dev | 🔄 Pending |
| **Jun 12** | Phase 1 Validation & Approval Decision | Strategy | 🔄 Pending |
| **Jun 13** | Phase 2 Kickoff (if approved) | Dev | 🔄 Pending |
| **Jun 26** | Phase 3 Kickoff (if approved) | Dev | 🔄 Pending |
| **Jul 4** | Phase 5 Kickoff (Walk-Forward Testing) | QA | 🔄 Pending |
| **Jul 10** | Phase 5 Complete & Production Ready | All | 🔄 Pending |

---

## 💡 Quick Reference: Where to Find Things

### For **Strategy Leads**:
- Start: `PHASE1_EXECUTIVE_SUMMARY.md` (Decision log, approval matrix)
- Reference: `PHASE1_REMEDIATION_ASSESSMENT.md` (Risk analysis, mitigation)
- Data: `phase1_remediation_backtest_20260601_091057.json` (Backtest results)

### For **Developers**:
- Spec: `PHASE1_IMPLEMENTATION_SPEC.md` (Full build guide)
- Tasks: Sections 3.1–3.5 (5 development tasks with DoD)
- Code Template: Section 3.1 (FilterHierarchy skeleton)

### For **QA / Testing**:
- Test Plan: `PHASE1_IMPLEMENTATION_SPEC.md` § 3.4 (8 unit tests)
- Validation Gates: `PHASE1_EXECUTIVE_SUMMARY.md` § "Validation Gates"
- Metrics: `PHASE1_REMEDIATION_ASSESSMENT.md` § "Plan Element Analysis"

### For **Risk Managers**:
- Risk Summary: `PHASE1_REMEDIATION_ASSESSMENT.md` § "Risks & Mitigation"
- Position Sizing: `PHASE1_IMPLEMENTATION_SPEC.md` § "Risk Management (unchanged)"
- Contingencies: `PHASE1_EXECUTIVE_SUMMARY.md` § "Contingency Plan"

---

## ✅ Approval Checklist

Before Phase 1 implementation begins:

- [ ] **Strategy Lead**: Read EXECUTIVE_SUMMARY, confirm go-ahead
- [ ] **Dev Lead**: Read IMPLEMENTATION_SPEC § 3, confirm feasibility
- [ ] **QA Lead**: Review test plan § 3.4, confirm resources
- [ ] **Risk Manager**: Validate risk mitigation § 4.2, confirm constraints
- [ ] **Project Manager**: Confirm 5–6 week timeline (not 3 weeks)
- [ ] **All**: Attend kickoff meeting (June 5, 2026, 2 PM)

---

## 🎬 Next Steps (Immediate)

1. **Distribute**: Share this index + PHASE1_EXECUTIVE_SUMMARY.md with all stakeholders
2. **Schedule**: Kickoff meeting (June 5, 3 PM) – 1 hour overview + Q&A
3. **Prepare**: Dev team review PHASE1_IMPLEMENTATION_SPEC.md in detail
4. **Confirm**: All approvers sign off by June 5, 5 PM
5. **Begin**: Phase 1 development starts June 6, 9 AM

---

**Document Index Version**: 1.0  
**Date**: June 1, 2026  
**Owner**: Strategy Enhancement Task Force  
**Distribution**: Executive Sponsor, All Team Leads, Project Team  
**Next Update**: June 12, 2026 (Phase 1 Closure)

---

**Last Updated**: June 1, 2026, 09:15 AM  
**Status**: ✅ READY FOR IMPLEMENTATION
