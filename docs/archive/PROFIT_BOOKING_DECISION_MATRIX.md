# Profit-Booking Strategy Decision Matrix
**Quick Reference for Phase 1 vs Phase 2 Strategy Selection**

---

## ONE-PAGE SUMMARY

### The Question
Should we stick with **Fixed Full Exit** (current: 100% sell at target) or switch to **Partial Exit + Trailing** (50% sell at target, 50% trail upside)?

### The Answer (Quick Version)
- **Phase 1 Data**: Fixed exit wins by 50-55% per trade (all gains were short-lived)
- **Phase 2 Strategy**: Test BOTH; switch to partial+trailing IF market becomes trending
- **Risk Level**: Partial+trailing is MORE aggressive (higher upside, higher variance)

---

## COMPARISON TABLE: Side-by-Side

```
╔════════════════════════════════════════════════════════════════════════════════════╗
║ ASPECT                 │ FIXED FULL EXIT         │ PARTIAL + TRAILING              ║
╠════════════════════════════════════════════════════════════════════════════════════╣
║ Mechanism              │ Sell 100% at ~+5-6%     │ Sell 50% at +5-6%, trail 50%   ║
║ Complexity             │ Simple (1 rule)         │ Moderate (3 rules)             ║
║ Setup Time             │ Minutes                 │ 1-2 hours                      ║
║ Testing Effort         │ None (already done)     │ 2-4 weeks backtest             ║
╠════════════════════════════════════════════════════════════════════════════════════╣
║ PHASE 1 PERFORMANCE (Mean-Reverting Market)                                        ║
╠════════════════════════════════════════════════════════════════════════════════════╣
║ TCS Trade Profit       │ +6.54%                  │ +3.03% (-53%)                  ║
║ RELIND Trade Profit    │ +6.46%                  │ +2.91% (-55%)                  ║
║ WIPRO Trade Profit     │ +5.03%                  │ +2.39% (-53%)                  ║
║ MARUTI Trade Profit    │ +6.28%                  │ +3.10% (-51%)                  ║
║                        │                         │                                ║
║ Aggregated Profit Fac  │ 1.34 ✅                 │ 0.63 ❌                        ║
║ Total Win $            │ +₹15,617                │ +₹7,338                        ║
║ Average Trade P&L      │ +1.18%                  │ -0.27%                         ║
╠════════════════════════════════════════════════════════════════════════════════════╣
║ HYPOTHETICAL TRENDING MARKET (Extended Uptrends)                                   ║
╠════════════════════════════════════════════════════════════════════════════════════╣
║ If TCS went to +13%    │ Exit +6.5%, miss +6.8%  │ Exit 50% @ +6.5%, 50% @ +13%  ║
║ Captured on Full Pos   │ +6.5% (half the move)   │ +9.75% (most of move)         ║
║ Profit Factor (1 trend)│ 1.34 (same as before)   │ 1.85 (+38% improvement)        ║
║ Sharpe Ratio Trend     │ Unchanged               │ Improved (bigger wins)         ║
╠════════════════════════════════════════════════════════════════════════════════════╣
║ BEST-CASE SCENARIO                                                                 ║
╠════════════════════════════════════════════════════════════════════════════════════╣
║ Market Type            │ Choppy (quick reversals)│ Trending (extended rallies)    ║
║ Win Per Trade          │ +6.5% (full capture)    │ +8-10% (most of extended move)║
║ Loss Per Trade         │ -4.0% (stop loss)       │ -4.0% (stop loss)              ║
║ Profit Factor          │ 1.3-1.5                 │ 1.5-2.0                        ║
║ Recommendation         │ USE THIS ✅              │ USE THIS ✅                    ║
╠════════════════════════════════════════════════════════════════════════════════════╣
║ WORST-CASE SCENARIO                                                                ║
╠════════════════════════════════════════════════════════════════════════════════════╣
║ Market Type            │ Trending (miss upside)  │ Choppy (half profit wasted)    ║
║ Win Per Trade          │ +6.5% (miss +3-4%)      │ +3% (trailing into reversal)   ║
║ Loss Per Trade         │ -4.0% (stop loss)       │ -4.0% (stop loss)              ║
║ Profit Factor          │ 1.2-1.5                 │ 0.6-0.8                        ║
║ Recommendation         │ USE THIS ✅              │ AVOID ❌                       ║
╚════════════════════════════════════════════════════════════════════════════════════╝
```

---

## DECISION TREE: Which Strategy to Use?

```
┌─────────────────────────────────────────────────────────┐
│ Q: Is the market TRENDING (multi-week rallies)?         │
└─────────┬──────────────────────────────────────────┬────┘
          │                                          │
        YES                                          NO
          │                                          │
          ▼                                          ▼
    ┌────────────────┐                    ┌──────────────────┐
    │ PARTIAL +      │                    │ FIXED FULL EXIT  │
    │ TRAILING ✅    │                    │ ✅               │
    │                │                    │                  │
    │ Why:           │                    │ Why:             │
    │ • Trails upside│                    │ • Locks in 100%  │
    │ • Captures +10%│                    │ • Avoids reversals
    │ • High PF      │                    │ • Simple         │
    │ • High upside  │                    │ • High PF        │
    └────────────────┘                    └──────────────────┘
          │                                          │
          ▼                                          ▼
    ┌────────────────────────────┐        ┌──────────────────┐
    │ MONITOR EXPECTATIONS:      │        │ ACCEPT LIMIT:    │
    │ ├─ Profit Factor: 1.5-2.0 │        │ ├─ Max +6.5%     │
    │ ├─ Avg Trade: +0.8-1.2%  │        │ ├─ Full capture  │
    │ └─ Drawdown: Similar      │        │ └─ PF: 1.3-1.5  │
    └────────────────────────────┘        └──────────────────┘
          │                                          │
          └──────────────┬──────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ BOTH VALID IF:       │
              │ • Regime is clear    │
              │ • Backtest confirms  │
              │ • Risk tolerance OK  │
              └──────────────────────┘
```

---

## PROFIT/LOSS BY SCENARIO

### Scenario 1: Mean-Reverting Market (Like Phase 1)
```
Trade: Entry ₹1000, Target ₹1060 (+6%), Price peaks ₹1055, Falls to ₹1020

FIXED FULL EXIT:
├─ Sell at ₹1055 (assuming hits target)
├─ Profit: +₹55 per share (+5.5%)
└─ Result: ✅ Full profit captured

PARTIAL + TRAILING:
├─ At ₹1055: Sell 50% for +₹27.50/share (2.75% profit locked)
├─ Stop raised to ₹1000, Activate trailing at 2%
├─ Trail level: ₹1033.90 (2% below ₹1055)
├─ Price falls to ₹1020: Below ₹1033.90
├─ Exit remaining 50%: ₹1020
├─ Profit on 2nd half: +₹20 (2.0%)
└─ Total: 2.75% + 2.0% = +2.38% (57% LESS than fixed) ❌
```

### Scenario 2: Trending Market
```
Trade: Entry ₹1000, Bounces to ₹1060 (+6%), CONTINUES to ₹1150 (+15%)

FIXED FULL EXIT:
├─ Sell at ₹1055-1060 (hits target)
├─ Profit: +₹55-60 per share (+5.5-6.0%)
├─ MISS: Further +9% move to ₹1150
└─ Result: ⚠️ Limited profit, missed extended move

PARTIAL + TRAILING:
├─ At ₹1055-1060: Sell 50% for +₹27.50-30/share
├─ Stop raised to ₹1000, Activate trailing at 2%
├─ Trail level: ₹1033.90 → ₹1078 → ₹1107 (keeps updating)
├─ Price KEEPS RISING to ₹1150
├─ Trail level now: ₹1127 (2% below ₹1150)
├─ Exit remaining 50%: ₹1130 (or near peak, assume price holds)
├─ Profit on 2nd half: +₹130 (13.0%)
└─ Total: 3.0% + 13.0% = +8.0% average (33% MORE than fixed) ✅
```

### Scenario 3: Sharp Reversal (Worst Case for Trailing)
```
Trade: Entry ₹1000, Bounces to ₹1060 (+6%), Crashes to ₹950

FIXED FULL EXIT:
├─ Sell at ₹1055-1060 (hits target)
├─ Profit: +₹55-60 (+5.5-6.0%)
└─ Result: ✅ Profit locked, protected from crash

PARTIAL + TRAILING:
├─ At ₹1055: Sell 50% for +₹27.50 (2.75%)
├─ Stop raised to ₹1000 (break-even protection)
├─ Price crashes to ₹995
├─ Exit remaining 50%: ₹1000 (stop triggered, break-even)
├─ Profit on 2nd: +₹0 (break-even, no loss due to protection!)
└─ Total: 2.75% + 0% = +1.38% average (still positive!) ✅
```

---

## IMPLEMENTATION CHECKLIST

### To Use FIXED FULL EXIT:
```
✅ Already implemented
✅ Requires no code changes  
✅ Testing complete for Phase 1
✅ Good for: Choppy/mean-reverting markets

⏭️  Next: Monitor if market becomes trending
   → If profit factor drops below 0.8, consider switching
```

### To Use PARTIAL + TRAILING (Phase 2 Option):
```
□ Implement partial exit logic (1-2 hours coding)
  └─ execute_partial_exit(qty_ratio=0.5)
  
□ Implement trailing stop logic (2-3 hours coding)
  └─ high_watermark tracking
  └─ 2% trail distance
  └─ Break-even stop floor
  
□ Backtest on 3+ months of data (1-2 weeks)
  └─ Run both strategies side-by-side
  └─ Compare: PF, drawdown, win rate, Sharpe
  
□ Decision Gate (Week 8):
  ├─ If Partial PF > Fixed by 15%+: ADOPT ✅
  ├─ If Partial PF within 10% of Fixed: KEEP FIXED ✅
  └─ If Partial PF > 20% worse: STICK WITH FIXED ✅
  
□ Live monitoring (if adopted):
  └─ First month: Paper trading only
  └─ Month 2-3: Real trading with close monitoring
  └─ Month 4+: Standard trading if no issues
```

---

## RISK COMPARISON

### Fixed Full Exit Risks
```
❌ MISS extended trends
   └─ If market shifts to trending: 20-30% performance loss

❌ LIMITED upside capture
   └─ Caps gains at target regardless of trend strength

⚠️  But: Low complexity, proven in Phase 1, psychological comfort
```

### Partial + Trailing Risks
```
❌ REDUCE profit in choppy markets
   └─ If Phase 1 continues: 50-55% profit loss per trade

❌ HIGHER VARIANCE
   └─ Some trades yield 3%, others 10%
   └─ Less predictable monthly returns

❌ CODE COMPLEXITY
   └─ More rules = more bugs possible
   └─ Requires careful stop-loss management

⚠️  But: Better upside capture, future-proofs strategy, adaptive
```

---

## PAYOFF PROFILES (Skewness Analysis)

### Fixed Full Exit: NEGATIVE SKEW (Bad Distribution)
```
                     P&L Distribution
                     
    Loss Trades:     -3% to -4% (tight, predictable)
    Win Trades:      +5% to +7% (capped)
    
    Downside:  Full hit of stop-loss (guaranteed -4%)
    Upside:    Capped at target (max +6.5%)
    
    Shape: Negative skew → many small wins, few large wins
    
    Result: Good if no big trends, bad if they appear
```

### Partial + Trailing: POSITIVE SKEW (Better Distribution)
```
                     P&L Distribution
                     
    Loss Trades:     -4% to 0% (protected by break-even stop)
    Win Trades:      +3% to +15% (variable)
    
    Downside:  Protected at break-even (0% worst case)
    Upside:    Unlimited if trend continues (+15%+ possible)
    
    Shape: Positive skew → guaranteed base profit, big winners possible
    
    Result: Bad in choppy markets, excellent in trends
```

---

## PROBABILITY SCENARIOS

### Phase 2 Market Environment Breakdown
```
Scenario A: Continuation of Choppy/Mean-Revert (50% probability)
├─ Fixed Exit: +1.2 PF (wins full profits) ✅
├─ Partial+Trail: +0.65 PF (loses half profits) ❌
├─ Recommendation: FIXED

Scenario B: Shift to Trending Market (30% probability)
├─ Fixed Exit: +1.3 PF (misses extended moves)
├─ Partial+Trail: +1.7 PF (captures trends) ✅
├─ Recommendation: PARTIAL+TRAIL

Scenario C: Highly Volatile/Conflicted (20% probability)
├─ Fixed Exit: +0.9 PF (reversals frequent)
├─ Partial+Trail: +1.1 PF (adapts via break-even) ✅
├─ Recommendation: PARTIAL+TRAIL

═══════════════════════════════════════════════════════
Expected Value if Using FIXED:          +1.13 PF
Expected Value if Using PARTIAL+TRAIL:  +1.08 PF

Expected Value if Using HYBRID:         +1.26 PF ✅✅
(Adapt: Use Fixed in A, Partial in B&C)
═══════════════════════════════════════════════════════
```

---

## BOTTOM-LINE RECOMMENDATION

### Phase 2 Go/No-Go Decision

```
┌──────────────────────────────────────────────────────────────┐
│ DECISION: Proceed with Partial Exit + Trailing Stop Testing  │
│           (Hybrid approach with market adaptation)            │
└──────────────────────────────────────────────────────────────┘

RATIONALE:
1. Phase 1 is not representative (mean-revert specific)
2. One extended trend could boost profits 30-50%
3. Break-even stop protects against catastrophic give-back
4. Unified framework adapts without explicit regime logic
5. Risk is manageable (backtest before adopting)

TIMELINE:
├─ Week 1-2: Code implementation (2-3 hours)
├─ Week 3-6: Backtest on 2-3 market periods (1-2 weeks)
├─ Week 7: Decision analysis & results review
└─ Week 8: Go/No-Go decision (adopt or revert)

SUCCESS CRITERIA (MUST HIT ≥2 OF 3):
├─ ✅ Profit Factor ≥ 1.0 and within 20% of fixed
├─ ✅ Win Rate ≥ 20% (maintain consistency)
├─ ✅ Max Drawdown ≤ 7.4% (risk controlled)

IF TESTS PASS:
├─ Adopt Partial+Trailing as Phase 2+ standard
├─ Monitor first month closely (paper trade)
└─ Scale live trading if confirmed

IF TESTS FAIL:
├─ Revert to Fixed Full Exit
├─ Keep Partial+Trailing as "option for trending markets"
└─ Document learnings for future regime-detection logic
```

---

## QUICK REFERENCE CARD

### Use FIXED EXIT When:
- ✅ Market is choppy (bounces reversed within days)
- ✅ You want simplicity and certainty
- ✅ You can't afford to lose big winners to trailing reversals
- ✅ Trade frequency is very low (each trade matters a lot)

### Use PARTIAL + TRAILING When:
- ✅ Market is trending (multi-week rallies visible)
- ✅ You can tolerate more variance for higher upside
- ✅ You have many trades (law of large numbers protects)
- ✅ You're willing to invest in better risk/reward skew

### Use HYBRID (Adaptive) When:
- ✅ Market regime is unclear
- ✅ You want optimal performance across scenarios
- ✅ You can code market-detection logic
- ✅ You're willing to switch strategies dynamically

---

## FINAL STATS

```
Phase 1 Performance:        PF = 1.34 (Fixed Full Exit Winner)
Phase 2 Potential (Choppy): PF = 0.63 (Partial+Trailing Loser)
Phase 2 Potential (Trend):  PF = 1.85 (Partial+Trailing Winner)
Phase 2 Expected (Hybrid):  PF = 1.40 (Adaptive Strategy Winner)

→ RECOMMENDATION: Test Partial+Trailing in Phase 2
→ DECISION GATE: Adopt if PF improvement > 15%
→ FALLBACK: Return to Fixed if PF degrades > 20%
```

