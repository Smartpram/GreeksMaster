# PHASE 5: LIVE PAPER TRADING - DEPLOYMENT GUIDE
## Ready for 2-4 Week Validation Period

**Date:** June 9, 2026  
**Status:** ✅ Phase 5 System Created & Tested  
**Duration:** 2-4 weeks  
**Objective:** Validate Phase 4 backtest results on live data

---

## 🎯 PHASE 5 OBJECTIVES

### Primary Goal
Generate daily trading signals and track real-world performance to validate backtest results before live trading.

### Success Criteria
✅ Paper trading win rate ≥ 40%  
✅ Real-world drawdown < 5%  
✅ Signals match backtest ±5%  
✅ System stable & reliable  
✅ No technical issues  

### Validation Metrics
- **Signal Quality:** Do signals match Phase 4 expectations?
- **Win Rate:** ≥ 40% (same as backtest)
- **Execution Quality:** Any slippage/liquidity issues?
- **Capital Preservation:** Max drawdown < 5%?
- **System Reliability:** Any errors/crashes?

---

## 🔄 HOW PHASE 5 WORKS

### Daily Workflow (5 PM IST - After Market Close)

```
1. Generate Signals (5 PM)
   ├─ Check all 6 stocks
   ├─ Apply Phase 4 filters (ADX > 25, volume, etc.)
   ├─ Generate BUY/SELL signals
   └─ Log signals to file

2. Track Outcomes (Ongoing)
   ├─ Monitor signal entry prices
   ├─ Update P&L daily
   ├─ Check for profit targets (+2%)
   ├─ Check for stop losses (-1%)
   └─ Close trades at 10-day time stop

3. Generate Reports (End of Day)
   ├─ Daily performance summary
   ├─ Weekly comparison to backtest
   ├─ Monthly validation report
   └─ Alert on deviations

4. Analyze Results (Weekly)
   ├─ Win rate tracking
   ├─ Drawdown analysis
   ├─ Signal quality assessment
   └─ Compare to Phase 4 expectations
```

### Key Dates/Times

**Signal Generation:**
- Time: 5:00 PM IST (after market close)
- Frequency: Daily (weekdays only)
- Method: Automated script

**Signal Closure:**
- Profit Target: +2% (close immediately)
- Stop Loss: -1% (close immediately)
- Time Stop: 10 bars / ~2 weeks (close)

**Reporting:**
- Daily: End of day (5:30 PM)
- Weekly: Every Friday
- Monthly: End of month

---

## 📋 HOW TO RUN PHASE 5

### Option 1: Manual Daily Execution

```bash
# Run at 5 PM IST each trading day
cd C:\Data\GreeksMaster
python backtest/phase5_paper_trading.py
```

**Output:**
- Console logs showing signals
- Daily report with P&L
- Summary metrics

**File saved:**
- `backtest_reports/phase5_signals_<date>.json`
- `backtest_reports/phase5_report_<date>.json`

### Option 2: Automated Daily Execution (Recommended)

Use Windows Task Scheduler to run script automatically at 5:15 PM IST each day:

```
Task: Phase5_DailySignalGeneration
Trigger: Daily at 5:15 PM (17:15)
Action: C:\Python\python.exe
Arguments: C:\Data\GreeksMaster\backtest\phase5_paper_trading.py
```

### Option 3: Real-Time Monitoring (Advanced)

Set up continuous monitoring with Flask web server:

```bash
python backtest/phase5_web_server.py
```

Then access: `http://localhost:5000/paper_trading`

---

## 📊 TRACKING & REPORTING

### Daily Report Template

```
Date: 2026-06-09
Market Close: 3:30 PM

Signals Generated: 2
├─ INFY: BUY (ADX=65, Price=1180)
└─ TCS: SELL (ADX=28, Price=2151)

Closed Signals: 1
├─ WIPRO (from 2026-06-02): WIN +1.8%

Pending Signals: 2
├─ INFY (4 days): +1.2% (tracking)
└─ TCS (1 day): -0.3% (tracking)

Daily Summary:
├─ Win Rate: 100% (1/1 closed)
├─ Total P&L: +1.5%
└─ Max Drawdown: -0.3%

Weekly Comparison:
├─ Backtest Win Rate: 50%
├─ Paper Win Rate: 100% (so far)
├─ Match: ✓ Exceeding expectations
└─ Status: VALIDATED
```

### Weekly Summary Template

```
Week Ending: 2026-06-09

Signals Generated: 5
Signals Closed: 2
Signals Pending: 3

Performance:
├─ Win Rate: 50% (1/2)
├─ Avg P&L: +0.85%
├─ Total P&L: +1.70%
├─ Max Drawdown: -0.5%
└─ Sharpe: 2.1

Comparison to Backtest:
├─ Backtest Win Rate: 50%
├─ Paper Win Rate: 50% ✓
├─ Match: EXACT
└─ Status: VALIDATING

Issues/Observations:
- INFY signal still pending (profitable so far)
- TCS signal hit stop loss quickly (market volatility)
- No slippage issues observed
- All signals executed as expected
```

---

## 📈 SUCCESS METRICS TRACKING

### Win Rate Tracker

Track win rate evolution over 2-4 weeks:

```
Week 1 (Jun 9-15):    50% WR (1W/1L)
Week 2 (Jun 16-22):   40% WR (2W/3L)
Week 3 (Jun 23-29):   45% WR (5W/6L)
Week 4 (Jun 30-Jul 6): 43% WR (8W/10L)

Target: ≥ 40% WR ✓
```

### Drawdown Tracking

```
Jun 9:    -0.3%
Jun 10:   -0.5% (worst)
Jun 11:   +0.2% (recovery)
Jun 12:   +0.8%
...
Jun 30:   -0.8%

Max Drawdown:   -0.5% ✓
Target:         < 5%  ✓
Status:         EXCELLENT
```

### Comparison to Backtest

| Metric | Phase 4 Backtest | Phase 5 Paper | Match? |
|--------|------------------|---------------|--------|
| Win Rate | 50% | TBD (tracking) | TBD |
| Avg P&L | +$16.5K | TBD (tracking) | TBD |
| Max Drawdown | -3.1% | TBD (tracking) | TBD |
| Avg Days Held | 2.5 | TBD (tracking) | TBD |
| Sharpe Ratio | 2.79 | TBD (tracking) | TBD |

---

## ⚠️ VALIDATION RULES

### When to Consider Phase 5 PASSED

✅ After at least 2 weeks of trading:
- Win rate is 35%+ (slight margin for safety)
- Max drawdown < 5%
- No system errors/crashes
- Signals match Phase 4 logic
- At least 10 closed trades

✅ After 4 weeks of trading:
- Win rate is 40%+
- Max drawdown < 3%
- 20+ closed trades
- Confident in real-world performance

### When to Consider Phase 5 FAILED

❌ If any of these occur:
- Win rate drops below 30%
- Drawdown exceeds 10%
- Multiple system errors/crashes
- Signals diverge from Phase 4 logic
- Slippage/execution issues observed

**Action if Failed:** Investigate root cause, adjust Phase 4 filters, re-run Phase 3-4, start Phase 5 over

---

## 🔧 PHASE 5 SYSTEM COMPONENTS

### File Structure

```
backtest/
  ├─ phase5_paper_trading.py         (Main system)
  ├─ phase5_web_server.py            (Optional: Web UI)
  └─ phase5_daily_scheduler.py       (Optional: Automation)

backtest_reports/
  ├─ phase5_signals_2026_06_09.json  (Daily signals)
  ├─ phase5_report_2026_06_09.json   (Daily report)
  ├─ phase5_weekly_summary.json      (Weekly tracking)
  └─ phase5_validation_log.txt       (Activity log)

PHASE_5_TRACKING.md                  (Manual tracking file)
PHASE_5_WEEKLY_REPORTS.md            (Report archive)
```

### Key Classes

**PaperSignal:**
- Store generated signals
- Track outcomes
- Calculate P&L
- Monitor until closure

**DailyReport:**
- Aggregate signals by day
- Calculate daily metrics
- Compare to backtest
- Track performance trends

**PaperTradingSystem:**
- Main orchestrator
- Generate signals daily
- Update outcomes
- Generate reports

---

## 📞 DECISION POINTS

### After 1 Week (Jun 15)

**Questions:**
- Are signals generating? (Should see 5-10 signals)
- Any system errors? (Should be none)
- Win rate reasonable? (Should be ~50% or close)

**Decision:**
- Continue: Everything normal → Keep going
- Investigate: Few signals → Check filters
- Adjust: Poor performance → Review Phase 4

### After 2 Weeks (Jun 22)

**Questions:**
- Win rate ≥ 35%? (Should be)
- Drawdown < 5%? (Should be)
- Signals match Phase 4? (Should be)

**Decision:**
- Continue: All checks pass → Proceed to week 3-4
- Caution: Some concerns → Investigate
- Stop: Major issues → Go back to Phase 4

### After 4 Weeks (Jul 6)

**Questions:**
- Win rate ≥ 40%? (Should be)
- 20+ closed trades? (Should have)
- Consistently profitable? (Should be)

**Decision:**
- PASS: All criteria met → Ready for Phase 6 (Live Trading)
- FAIL: Criteria not met → Debug and re-test
- INVESTIGATE: Mixed results → Analyze deeper

---

## 🎬 GETTING STARTED

### Day 1: Setup (Jun 9)

```
1. Review this guide (30 min)
2. Understand Phase 5 code (1 hour)
3. Run first test (5 min)
4. Set up tracking spreadsheet (30 min)
5. Configure daily execution (30 min)
6. Ready to go!
```

### Day 2-15: Daily Operations

```
Each trading day at 5:15 PM:
1. Script runs automatically (or manually)
2. Generates today's signals
3. Saves results to JSON
4. Updates tracking spreadsheet
5. Review at end of day (2 min)
```

### Week 2-4: Weekly Reviews

```
Every Friday:
1. Compile weekly report
2. Calculate metrics
3. Compare to Phase 4 backtest
4. Document findings
5. Adjust if needed
```

### Week 5: Final Decision

```
Evaluate:
1. Overall win rate
2. Drawdown control
3. Signal quality
4. System stability
5. Decision: PASS or FAIL?
```

---

## 📋 PHASE 5 CHECKLIST

### Pre-Launch Checklist

- ✅ Phase 5 code created and tested
- ✅ Daily signal generation working
- ✅ Outcome tracking functional
- ✅ Reporting system ready
- ✅ Spreadsheet template prepared
- ✅ Team informed of timeline
- ✅ Notification alerts configured
- ✅ Backup/logging set up

### Weekly Checklist

- ☐ Run daily signals (7 days)
- ☐ Update tracking spreadsheet (daily)
- ☐ Compile weekly report (Friday)
- ☐ Compare to backtest (Friday)
- ☐ Document observations (Friday)
- ☐ Check for system issues (daily)
- ☐ Monitor win rate trend (daily)

### End of Phase 5 Checklist

- ☐ 20+ closed trades documented
- ☐ Win rate calculated (target: 40%+)
- ☐ Max drawdown verified (target: < 5%)
- ☐ Comparison report generated
- ☐ All issues documented/resolved
- ☐ Final decision made (PASS/FAIL)
- ☐ If PASS: Prepare Phase 6

---

## 📚 DOCUMENTATION FILES

**Main Files:**
- `PHASE_5_DEPLOYMENT_GUIDE.md` (This file)
- `backtest/phase5_paper_trading.py` (Code)

**Tracking Files:**
- `PHASE_5_TRACKING.md` (Daily log)
- `PHASE_5_WEEKLY_REPORTS.md` (Weekly summaries)

**Reference:**
- `PHASE_4_COMPLETION_REPORT.md` (What to compare against)
- `QUICKSTART_PHASES_3_4.md` (Quick refresher)

---

## ✅ SUCCESS DEFINITION

**Phase 5 = SUCCESS if:**

```
✅ Paper trading win rate ≥ 40%
   └─ We need 40% to be profitable

✅ Real-world drawdown < 5%
   └─ Backtest was 3.1%, so target realistic range

✅ Signals match Phase 4 ±5%
   └─ Backtest logic should hold in live data

✅ System operates without errors
   └─ No crashes, all signals generated correctly

✅ At least 20 closed trades
   └─ Enough data to validate statistically

✅ Consistent performance across all symbols
   └─ No single stock skewing results
```

**Phase 5 = FAIL if:**

```
❌ Win rate < 30%
   └─ Below profitable threshold

❌ Drawdown > 10%
   └─ Beyond acceptable risk

❌ Signals diverge from Phase 4
   └─ Something wrong with logic

❌ System errors/crashes
   └─ Cannot rely on automated trading

❌ Slippage/execution problems
   └─ Real-world execution issues
```

---

## 🎯 TIMELINE

```
Jun 9 (Now):        Phase 5 launched
Jun 9-15 (Week 1):  Signal generation, tracking
Jun 16-22 (Week 2): Mid-point review, 50% assessment
Jun 23-29 (Week 3): Continued tracking, refinement
Jun 30-Jul 6 (Week 4): Final assessment, decision
Jul 7+ (Phase 6):    Live trading (if Phase 5 passes)
```

---

## 💡 KEY INSIGHTS

### Why Phase 5 is Important

1. **Validates Backtest:** Real data can differ from backtest assumptions
2. **Catches Issues:** System bugs, execution problems discovered early
3. **Builds Confidence:** Live performance > backtest → ready for real capital
4. **Proves Edge:** If paper trading wins 40%+, edge is real
5. **De-risks Transition:** Catches problems before live money at stake

### Why 2-4 Weeks?

- Week 1: Prove signals generate correctly
- Week 2: Gather enough closed trades (10+)
- Week 3: Confirm trend holds (20+ trades)
- Week 4: Final validation, decision

### Why Strict Criteria?

- 40% win rate: Need mathematical edge
- < 5% drawdown: Need capital preservation
- 20+ trades: Need statistical significance
- Match Phase 4: Need confidence in logic

---

## 🚀 NEXT STEPS

### If Phase 5 PASSES (All criteria met)

→ **Proceed to Phase 6: Live Trading**
- Deploy Breeze API integration
- Start with small position size (1% of capital)
- Gradually scale up over 4 weeks
- Monitor continuously

### If Phase 5 FAILS (Criteria not met)

→ **Debug & Re-Test**
- Identify root cause
- Adjust Phase 4 filters if needed
- Re-run Phase 4 backtest
- Start Phase 5 over

### If Phase 5 MIXED (Some criteria met)

→ **Investigate Deeper**
- Run additional analysis
- Test on different time periods
- Adjust filters incrementally
- Get more data (extend Phase 5)

---

## 📞 SUPPORT & TROUBLESHOOTING

### Common Issues

**Q: No signals generating?**
A: Check if stocks have ADX > 25, volume sufficient, ATR > 0.5%. May be in range market.

**Q: Win rate too low?**
A: Compare actual prices to backtest. May need to adjust filters or accept variance.

**Q: System crashes?**
A: Check log file, ensure yfinance data available, test script in isolation.

**Q: Signals not matching Phase 4?**
A: Verify ADX calculation is correct, volume filter working, SMA20 logic identical.

---

## 🎓 FINAL THOUGHTS

Phase 5 is your safety net before live trading. Don't skip it or cut corners.

**If Phase 5 validates → Great! Live trading is next.**  
**If Phase 5 fails → Learn from it, improve, try again.**

The goal is confidence, not speed. Better to be slow and safe than fast and sorry.

---

**Phase 5 Status:** ✅ READY TO LAUNCH  
**Next Action:** Run daily signal generation starting tomorrow  
**Expected Duration:** 2-4 weeks  
**Final Decision Date:** July 6, 2026

---

Created: June 9, 2026  
Last Updated: June 9, 2026  
Status: PHASE 5 READY FOR DEPLOYMENT
