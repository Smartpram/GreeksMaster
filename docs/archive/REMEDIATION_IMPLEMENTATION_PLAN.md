# Implementation Plan: Remediation of Unified Strategy
## Addressing the Capital Preservation vs. Profit Trade-off

**Status:** Ready for Development  
**Target Date:** June 1-7, 2026  
**Expected Outcome:** Balanced strategy with profit factor >1.0 and maintained drawdown protection

---

## Executive Summary

The diagnostic revealed the integrated strategy functions as a "guardrail" system:
- ✅ **Strength:** 60% fewer trades, dramatically reduced losses
- ❌ **Weakness:** Misses early reversals, zero profit factor, negative Sharpe ratios
- 🎯 **Goal:** Retain risk protection while capturing upside opportunities

Current metrics across 6 tickers:
- Integrated trades: ~24 (vs. base 60) = 60% reduction
- Base win rate: 11-25% | Integrated: 0-25% (too variable)
- Profit factors: Mostly 0 (no gross profits in 4 of 6 tickers)

---

## Core Problem Analysis

### Problem 1: Overly Strict Entry Gating (AND Logic)
**Impact:** Missing all profitable bounces  
**Evidence:** BAFINS/INFTEC had only winners in base, but zero in integrated

**Root Cause:**
```
Base Strategy Logic (Too Loose):
  Signal = Any momentum + price action
  Result: Many losers, some winners

Integrated Strategy Logic (Too Strict):
  Signal = StochRSI AND Fib AND Renko (all 3 must align)
  Result: Perfect setups only = very rare, sometimes never
  Missing: The rare perfect setup never comes, so zero trades
```

**Fix:** Implement hierarchical logic instead of rigid AND

---

### Problem 2: Extreme Filter Strictness
**Impact:** Delayed entries, larger losses when they occur  
**Evidence:** 
- INFTEC integrated first trade: –7.42% (vs base typical –2%)
- RELIND avg loss: ₹3.0K integrated vs ₹2.06K base
- Entry delays causing worse execution prices

**Root Cause:**
```
Current Filter Stack:
  StochRSI: Rejects 80-97% of signals (too harsh)
  Fibonacci: Rejects 75-83% of signals (too strict on structure)
  Renko: Minimal rejection but adds timing lag
  
Result: By time all 3 align, move is already extended
  → Late entry + extended stop = larger % loss
```

**Fix:** Soften individual thresholds and use conditional logic

---

### Problem 3: All-or-Nothing Participation
**Impact:** Strategy absent from market when it could profit  
**Evidence:** TCS, INFTEC, BAFINS had only 3-4 integrated trades despite 10-12 base trades

**Root Cause:**
```
Integrated system is binary:
  - Perfectly aligned setup? Enter full size
  - Not perfect? Don't trade at all
  
Missing: Graduated entry strategy (probe → add → full position)
```

**Fix:** Implement multi-entry mechanism with position scaling

---

## Detailed Remediation Plan

### Phase 1: Hierarchical Filter Architecture (Week 1)

#### Current Structure (Problematic)
```python
def should_trade_integrated():
    return (stoch_rsi_signal AND 
            fib_level_signal AND 
            renko_confirmation)
```

#### Proposed Structure (Hierarchical)
```python
def should_trade_hierarchical(signal_strength="low/medium/high"):
    # Level 1: Price Structure (Foundation)
    if is_at_fib_support():
        fib_confidence = "high"
    elif price_near_recent_low():
        fib_confidence = "medium"
    else:
        fib_confidence = "low"
    
    # Level 2: Trend Confirmation (Context)
    if renko_brick_up AND is_oversold():
        renko_confidence = "high"
    elif renko_brick_up:
        renko_confidence = "medium"
    else:
        renko_confidence = "low"
    
    # Level 3: Momentum Trigger (Timing)
    stoch_rsi_score = calculate_stoch_rsi_strength()
    
    # Hierarchical Decision (Context → Confirmation → Trigger)
    if fib_confidence == "high" AND renko_confidence >= "medium":
        # Strong price structure + trend → lower momentum threshold
        return stoch_rsi_score > 30  # (vs current 50)
    
    elif fib_confidence == "high" AND stoch_rsi_score > 40:
        # Strong price structure + decent momentum → trade without perfect renko
        return True  # Allow trade even if renko not yet confirmed
    
    elif renko_confidence == "high" AND stoch_rsi_score > 35:
        # Strong trend + decent momentum → trade without perfect fib alignment
        return True  # Allow trade even if not at exact fib level
    
    else:
        # None of the conditions provide high confidence
        return False
```

#### Implementation Tasks
- [ ] Create `FilterHierarchy` class in `advanced_signal_validators.py`
- [ ] Define confidence levels for each filter
- [ ] Implement 2-of-3 logic with threshold reduction
- [ ] Test on INFTEC/BAFINS (highest filter rejection)
- [ ] Measure: capture early reversal in BAFINS Jan 28 (+5.7%)

---

### Phase 2: Dynamic Filter Thresholds (Week 1-2)

#### Current Thresholds (Too Restrictive)
```
StochRSI Oversold: <20 (extreme only)
Fibonacci Levels: Strict 38.2-61.8% only
Renko Brick Size: XYZ (fixed)
```

#### Proposed Adaptive Thresholds
```python
def get_adaptive_thresholds(market_regime):
    """
    Adjust filter thresholds based on:
    - Volatility (ATR, ADX)
    - Trend strength (ADX, slope)
    - Time since last signal
    """
    
    if is_extreme_downtrend():
        # Very strong downtrend: relax entry criteria
        return {
            'stoch_oversold': 30,      # (vs 20) Earlier entry
            'fib_zones': [0.25, 0.75],  # Broader support zones
            'renko_lag': 1,             # Allow 1-bar lag
            'position_size': 0.67       # 2/3 size due to high loss risk
        }
    
    elif is_strong_downtrend():
        return {
            'stoch_oversold': 25,
            'fib_zones': [0.38, 0.62],
            'renko_lag': 0,
            'position_size': 0.80
        }
    
    elif is_mild_downtrend() or is_consolidating():
        return {
            'stoch_oversold': 20,      # Standard
            'fib_zones': [0.382, 0.618], # Standard
            'renko_lag': 0,
            'position_size': 1.0       # Full size
        }
    
    elif is_uptrend():
        return {
            'stoch_oversold': 15,      # Much stricter (uptrend = less pullback)
            'fib_zones': [0.236, 0.5], # Only strongest pulls
            'renko_lag': 0,
            'position_size': 0.75
        }

def is_extreme_downtrend():
    """Detect steep drops like INFTEC/BAFINS Jan-Feb"""
    return (
        roc_3day < -5.0 AND  # Down >5% in 3 days
        atr_percentile > 75 AND  # High volatility
        close < sma_50  # Below trend
    )
```

#### Implementation Tasks
- [ ] Add regime detection to `advanced_signal_validators.py`
- [ ] Implement dynamic threshold adjustment
- [ ] Create `RegimeDetector` class with ADX/ATR logic
- [ ] Test on INFTEC (downtrend) vs RELIND (consolidation)
- [ ] Measure: Validate BAFINS early entry is captured with reduced threshold

---

### Phase 3: Risk Management on Late Entries (Week 2)

#### Problem: Late entries suffer larger % losses
**Evidence:** INFTEC's –7.42% first integrated trade (entered far below early bounce)

#### Solution: Volatility-Based Stops
```python
def calculate_dynamic_stop(entry_price, trade_type="normal"):
    """
    Adjust stop based on entry timing and ATR
    - Normal entry: Standard X% stop
    - Late entry: Tighter stop due to worse price
    """
    
    bars_since_low = calculate_bars_since_swing_low()
    atr = calculate_atr(14)
    
    if trade_type == "normal" and bars_since_low < 3:
        # Early entry after recent low: standard risk
        stop_loss = entry_price - (atr * 1.5)
        risk_per_trade = 2.0  # 2% of capital per trade
    
    elif bars_since_low >= 5:
        # Late entry (5+ bars after swing low): tighter stop
        stop_loss = entry_price - (atr * 1.0)  # Tighter
        risk_per_trade = 1.0  # 1% of capital per trade (half size)
    
    else:
        # Medium timing: balanced stop
        stop_loss = entry_price - (atr * 1.25)
        risk_per_trade = 1.5
    
    position_size = capital * (risk_per_trade / 100) / abs(entry_price - stop_loss)
    
    return {
        'stop_loss': stop_loss,
        'position_size': position_size,
        'entry_timing_penalty': 2.0 - risk_per_trade  # 1.0 = full size
    }
```

#### Implementation Tasks
- [ ] Create `DynamicRiskManager` class
- [ ] Integrate entry timing detection
- [ ] Calculate position sizing based on entry quality
- [ ] Backtest on INFTEC: verify –7.42% loss is reduced to ≤–4%
- [ ] Verify: Winning trades still reach targets

---

### Phase 4: Multi-Entry / Position Scaling (Week 2-3)

#### Problem: All-or-nothing participation  
**Evidence:** When perfectly aligned signal doesn't occur, zero trades taken

#### Solution: Graduated Entry Strategy
```python
class ScaledEntryManager:
    def __init__(self):
        self.entry_phase = 0  # 0=out, 1=probe, 2=add, 3=full
        self.consecutive_signals = 0
    
    def on_signal(self, signal_quality):
        """
        signal_quality: 0-100 based on confluence
        - 80-100: High quality (2+ filters strong) → Full position
        - 60-79: Medium quality (2 filters good) → Probe position
        - 40-59: Weak quality (1+ filters weak) → Very small probe
        - <40: Skip (don't trade)
        """
        self.consecutive_signals += 1
        
        if signal_quality >= 80:
            if self.entry_phase == 0:
                # High conviction on first signal → enter full
                position_size = 1.0
                self.entry_phase = 3
            else:
                # Already partially in → add to full
                position_size = 0.5
                self.entry_phase = 3
            
            return {'action': 'ENTER', 'size': position_size, 'type': 'FULL'}
        
        elif signal_quality >= 60:
            if self.entry_phase == 0:
                # Medium conviction → probe with 1/3 size
                position_size = 0.33
                self.entry_phase = 1
                return {'action': 'ENTER', 'size': position_size, 'type': 'PROBE'}
            
            elif self.entry_phase == 1:
                # Already probing → add another 1/3 if repeated signal
                position_size = 0.33
                self.entry_phase = 2
                return {'action': 'ADD', 'size': position_size, 'type': 'SCALE'}
        
        elif signal_quality >= 40 and self.consecutive_signals >= 2:
            # Weak signal but it repeats → very small probe
            if self.entry_phase == 0:
                position_size = 0.15
                self.entry_phase = 1
                return {'action': 'ENTER', 'size': position_size, 'type': 'MICRO'}
        
        return {'action': 'SKIP', 'size': 0, 'type': 'NONE'}
    
    def on_exit(self):
        """Reset after position closed"""
        self.entry_phase = 0
        self.consecutive_signals = 0
```

#### Example Sequence (TCS Jan 2026 - Avoided by integrated)
```
Jan 13: StochRSI flashes, Fib support identified
        Signal quality = 65 (medium)
        → PROBE: Enter 1/3 size at ₹3268

Jan 14-16: Signal repeats, price consolidates near support
        Signal quality = 70
        → SCALE: Add 1/3 more
        Total position: 2/3 size, avg entry ~₹3230

Jan 20: Renko confirms uptrend, StochRSI strong
        Signal quality = 85 (high)
        → ADD: Enter final 1/3
        Total position: Full size, avg entry ~₹3210

Outcome: By scaling in, strategy participates without
         all-or-nothing bet. Captures upside if recovery.
         Limits damage if false start (only 1/3 exposed initially).
```

#### Implementation Tasks
- [ ] Create `ScaledEntryManager` class
- [ ] Define signal quality scoring function
- [ ] Implement partial position tracking
- [ ] Backtest on TCS/INFTEC/BAFINS (the "missed winners")
- [ ] Measure: Capture +5-6% moves with lower initial risk

---

### Phase 5: Validation & Cross-Testing (Week 3)

#### A. Backtest on Same 6 Tickers
Run updated integrated strategy with all remediation applied:

```python
# Test configuration
test_tickers = ['RELIND', 'TCS', 'INFTEC', 'WIPRO', 'BAFINS', 'MARUTI']

# New strategy with all fixes
strategy = ImprovedUnifiedStrategy(
    filter_hierarchy=True,
    dynamic_thresholds=True,
    dynamic_risk_management=True,
    scaled_entry_manager=True
)

# Expected improvements:
# - Profit factor > 1.0 in at least 3 of 6 tickers
# - Sharpe ratio >= -3.0 (vs current -4 to -34)
# - Win rate >= 20% across the board
# - Drawdowns maintained ≤ current levels
# - Captures BAFINS Jan 28 (+5.7%) that base found
```

#### B. Walk-Forward Test (Out-of-Sample Validation)
Test on 2 weeks beyond current backtest period:
- Week 1: May 22-29, 2026
- Week 2: May 30 - Jun 6, 2026

#### C. Regime-Specific Validation
- Strong downtrend (INFTEC scenario): Verify improved profit factor
- Consolidation (RELIND scenario): Verify balanced win rate
- Recovery/uptrend (MARUTI scenario): Verify capture without whipsaws

---

## Metrics to Track (Before & After)

| Metric | Current Integrated | Target | Weight |
|--------|-------------------|--------|--------|
| **Profit Factor** | 0.0-0.6 | >1.0 | 40% |
| **Sharpe Ratio** | -34 to -4 | ≥-2.0 | 30% |
| **Win Rate** | 0-25% | ≥25% | 20% |
| **Max Drawdown** | -0.1% to -459% | ≤-200% | 10% |
| **Total Return** | -4% to -22% | Improve by 30% | 0% (contextual) |

---

## Implementation Checklist

### Week 1
- [ ] Create `FilterHierarchy` class
- [ ] Implement hierarchical confluence logic (2-of-3)
- [ ] Create `RegimeDetector` with ADX/ATR detection
- [ ] Implement dynamic threshold adjustment
- [ ] First backtest on INFTEC: Verify early bounce captured

### Week 2
- [ ] Create `DynamicRiskManager` with position sizing
- [ ] Implement entry-timing penalty logic
- [ ] Integrate ATR-based stops
- [ ] Create `ScaledEntryManager` class
- [ ] Second backtest on all 6 tickers
- [ ] Measure improvements to profit factor

### Week 3
- [ ] Refine thresholds based on tick-by-tick results
- [ ] Walk-forward validation on May 22-Jun 6 data
- [ ] Cross-test on different market regimes
- [ ] Final comprehensive report
- [ ] Deploy to paper trading

---

## Success Criteria

✅ **Phase 1 Complete When:**
- Hierarchical logic successfully tested on INFTEC
- BAFINS Jan 28 (+5.7%) bounce is captured

✅ **Phase 2 Complete When:**
- Dynamic thresholds reduce false signals in consolidation
- Profit factor improves to >0.6 on at least 3 tickers

✅ **Phase 3 Complete When:**
- Late entry risks are reduced by 30%
- Winning trades still reach targets (not stopped early by tight stops)

✅ **Phase 4 Complete When:**
- Scaled entries capture major moves with graduated risk
- All-or-nothing problem eliminated (strategy always has some participation)

✅ **Phase 5 Complete When:**
- Profit factor >1.0 achieved in 3+ of 6 tickers
- Sharpe ratio ≥-2.0 across all tickers
- Drawdown maintained ≤ current levels
- Ready for paper trading deployment

---

## Risk Mitigation

**Risk:** Softening filters causes return to false signal generation

**Mitigation:**
1. Hierarchical logic ensures at least 2 strong conditions
2. Scaled entries limit size on weak signals
3. Strict backtest validation before deployment
4. Paper trading phase to catch edge cases

**Risk:** Position scaling increases complexity

**Mitigation:**
1. ScaledEntryManager handles all logic
2. Integrated tracking prevents over-exposure
3. Hard limits on maximum total position size
4. Clear exit rules per entry phase

---

## Expected Timeline & Deliverables

| Week | Deliverable | Status |
|------|-------------|--------|
| W1 | Hierarchical filters + dynamic thresholds | 🟡 In Progress |
| W2 | Risk management + scaled entries | 🟡 Planned |
| W3 | Validation + final report | ⏳ Pending |
| W4 | Paper trading deployment | ⏳ Pending |

---

## Conclusion

This remediation plan directly addresses the three core issues:
1. **Missed upside** via hierarchical logic + scaled entries
2. **Large late losses** via dynamic risk management
3. **All-or-nothing problem** via multi-entry strategy

Implementation will balance the unified strategy's protective nature with profit-generating capability, targeting a balanced Sharpe >-2.0 and profit factors >1.0 across multiple regimes—all within one coherent, rule-based framework.

---

*Plan Created: June 1, 2026*  
*Target Completion: June 21, 2026*  
*Status: Ready for Development*
