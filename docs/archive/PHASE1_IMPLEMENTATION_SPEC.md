# Phase 1 Implementation Specification
## Hierarchical Filter Logic (2-of-3 Confirmation)

**Period**: June 6–12, 2026  
**Objective**: Replace strict 3-of-3 AND logic with adaptive 2-of-3 confirmation  
**Expected Outcome**: More trades (2.7→5+), higher win rate (16.7%→25%+), profit factor ≥0.60

---

## 1. Requirements

### 1.1 Functional Requirements

**FR1**: Implement FilterHierarchy class capable of 2-of-3 voting
- 3 independent filters: Renko Structure, Stochastic Momentum, Regime Context
- Each filter returns: `STRONG_BUY`, `WEAK_BUY`, `NEUTRAL`, `WEAK_SELL`, `STRONG_SELL`
- Decision logic: Trade if ≥2 filters agree on direction (not strict unanimity)
- Quality score: Calculate based on agreement strength (0.0–1.0)

**FR2**: Preserve current filter implementations
- Renko-based price structure detection (PointAndFigure or Brick analysis)
- Stochastic/RSI momentum confirmation (overbought/oversold)
- Regime context (trend direction + volatility state)

**FR3**: Output signal quality metadata
- Each entry signal tagged with: `quality_score`, `pattern_id`, `consensus`
- Example: `{"quality": 0.88, "pattern": "Pattern3_RenkoStoch", "consensus": ["Renko", "Stoch"]}`

**FR4**: Backward compatibility
- Current `base` strategy behavior unchanged (still available as fallback)
- New `hierarchical` mode selectable via flag
- Risk management unaffected

### 1.2 Non-Functional Requirements

**NFR1**: Performance
- Filter evaluation <50ms per bar
- No memory bloat (state size <10MB per backtest)

**NFR2**: Debuggability
- Log each filter's decision per bar
- Trace voting process for every entry signal
- Enable unit testing of each filter independently

**NFR3**: Robustness
- Handle missing/NaN data gracefully (skip bar, don't crash)
- Validate consensus logic with edge cases (all neutral, ties, etc.)

---

## 2. Architecture & Design

### 2.1 Hierarchical Filter Class Structure

```
FilterHierarchy (NEW MODULE)
├── Components:
│   ├── RenkoStructureFilter (existing, adapt)
│   ├── StochasticMomentumFilter (existing, adapt)
│   └── RegimeContextFilter (existing, adapt)
├── Methods:
│   ├── evaluate(bar_data) → (decision, quality_score, consensus)
│   ├── vote(filter_signals) → consensus_decision
│   └── quality_score(agreement_strength) → float [0, 1]
├── Config:
│   ├── voting_threshold: int = 2  (votes needed to trade)
│   ├── require_direction_agreement: bool = True
│   └── quality_weights: dict
└── State:
    └── filter_signals_history (for logging & debugging)
```

### 2.2 Decision Logic (Pseudocode)

```python
def evaluate(self, bar_data):
    # Get signals from each filter
    renko_signal = self.renko_filter.evaluate(bar_data)      # +1, 0, -1
    stoch_signal = self.stoch_filter.evaluate(bar_data)      # +1, 0, -1
    regime_signal = self.regime_filter.evaluate(bar_data)    # +1, 0, -1
    
    signals = [renko_signal, stoch_signal, regime_signal]
    votes_buy = sum(1 for s in signals if s == +1)
    votes_sell = sum(1 for s in signals if s == -1)
    
    # Decision: ≥2 votes in same direction
    if votes_buy >= 2:
        consensus = "BUY"
    elif votes_sell >= 2:
        consensus = "SELL"
    else:
        consensus = "NEUTRAL"
    
    # Quality score: higher if more agreement
    # Example: 3-of-3 unanimous = 1.0, 2-of-3 = 0.78, 1-of-3 = 0.0
    agreement_count = max(votes_buy, votes_sell)
    quality = self.quality_score(agreement_count, len(signals))
    
    # Consensus metadata
    consensus_filters = [
        f for f, s in zip(["Renko", "Stoch", "Regime"], signals)
        if (s == +1 and consensus == "BUY") or (s == -1 and consensus == "SELL")
    ]
    
    return {
        "decision": consensus,
        "quality_score": quality,
        "consensus": consensus_filters,
        "votes": {"buy": votes_buy, "sell": votes_sell},
        "individual_signals": {
            "renko": renko_signal,
            "stoch": stoch_signal,
            "regime": regime_signal
        }
    }

def quality_score(self, agreement_count, total_filters):
    """Map agreement strength to quality [0, 1]"""
    # 3-of-3: 1.00, 2-of-3: 0.78, 1-of-3: 0.00
    quality_map = {3: 1.00, 2: 0.78, 1: 0.00, 0: 0.00}
    return quality_map.get(agreement_count, 0.0)
```

### 2.3 Integration Points

**Current Codebase**:
```
app/strategies/
├── enhanced_signal_confirmation.py  ← Produces base signals
├── advanced_signal_validators.py    ← Renko/Stoch/Regime filters exist here
├── filter_hierarchy.py              ← NEW: Hierarchical orchestrator
└── signal_router.py                 ← Route signals to hierarchical or base
```

**Flow**:
```
enhanced_signal_confirmation.py
    ↓ (base signals)
filter_hierarchy.py (NEW)
    ├─→ RenkoStructureFilter.evaluate()
    ├─→ StochasticMomentumFilter.evaluate()
    ├─→ RegimeContextFilter.evaluate()
    └─→ vote() → (decision, quality_score, consensus)
    ↓ (hierarchical signals)
order_execution_engine.py
    └─→ Execute with risk management
```

---

## 3. Implementation Tasks

### Task 1: Create FilterHierarchy Module (Est. 4 hours)

**File**: `app/strategies/filter_hierarchy.py`

```python
# Skeleton (to be completed by dev team)

from enum import Enum
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class FilterSignal(Enum):
    STRONG_BUY = 2
    WEAK_BUY = 1
    NEUTRAL = 0
    WEAK_SELL = -1
    STRONG_SELL = -2

class FilterHierarchy:
    """
    Orchestrates 2-of-3 voting system for trade signals.
    - Renko Structure (price pattern)
    - Stochastic Momentum (oscillator)
    - Regime Context (trend + volatility)
    """
    
    def __init__(self, config: Dict = None):
        """
        config: {
            'voting_threshold': 2,                 # votes needed to trade
            'quality_weights': {...},              # weights per agreement count
            'require_direction_agreement': True,   # must agree on buy/sell
            'enable_logging': True
        }
        """
        self.config = config or {}
        self.voting_threshold = self.config.get('voting_threshold', 2)
        self.require_direction_agreement = self.config.get('require_direction_agreement', True)
        self.signal_history = []
        
    def evaluate(self, renko_signal, stoch_signal, regime_signal) -> Dict:
        """
        Args:
            renko_signal, stoch_signal, regime_signal: int in [-2, -1, 0, 1, 2]
        Returns:
            {
                'decision': 'BUY' | 'SELL' | 'NEUTRAL',
                'quality_score': float [0.0, 1.0],
                'consensus': List[str],  # e.g., ['Renko', 'Stoch']
                'votes': {'buy': int, 'sell': int},
                'individual_signals': {'renko': int, 'stoch': int, 'regime': int}
            }
        """
        signals = [renko_signal, stoch_signal, regime_signal]
        signal_names = ['Renko', 'Stoch', 'Regime']
        
        # Count votes
        votes_buy = sum(1 for s in signals if s > 0)
        votes_sell = sum(1 for s in signals if s < 0)
        
        # Determine consensus
        if votes_buy >= self.voting_threshold:
            decision = 'BUY'
            consensus_signals = [n for n, s in zip(signal_names, signals) if s > 0]
        elif votes_sell >= self.voting_threshold:
            decision = 'SELL'
            consensus_signals = [n for n, s in zip(signal_names, signals) if s < 0]
        else:
            decision = 'NEUTRAL'
            consensus_signals = []
        
        # Calculate quality score
        agreement_count = max(votes_buy, votes_sell)
        quality = self._quality_score(agreement_count)
        
        result = {
            'decision': decision,
            'quality_score': quality,
            'consensus': consensus_signals,
            'votes': {'buy': votes_buy, 'sell': votes_sell, 'neutral': 3 - votes_buy - votes_sell},
            'individual_signals': {
                'renko': renko_signal,
                'stoch': stoch_signal,
                'regime': regime_signal
            }
        }
        
        self.signal_history.append(result)
        return result
    
    def _quality_score(self, agreement_count: int) -> float:
        """Map agreement strength to quality score"""
        # 3-of-3 unanimous: 1.00
        # 2-of-3 majority: 0.78
        # 1-of-3 minority: 0.00
        quality_map = {3: 1.00, 2: 0.78, 1: 0.00, 0: 0.00}
        return quality_map.get(agreement_count, 0.0)
    
    def get_signal_history(self) -> List[Dict]:
        """Return all evaluated signals (for debugging)"""
        return self.signal_history
    
    def clear_history(self):
        """Clear signal history"""
        self.signal_history = []
```

**Definition of Done**:
- [ ] Class implemented with all methods above
- [ ] Unit tests for evaluate() with 8 edge cases (3-0-0, 2-1-0, 1-1-1, etc.)
- [ ] Logging enabled for debugging
- [ ] Integrated into signal_router.py with mode flag

---

### Task 2: Adapt Existing Filters for Hierarchical Mode (Est. 3 hours)

**Target Files**:
- `app/strategies/advanced_signal_validators.py` (Renko & Stoch filters)
- `app/strategies/enhanced_signal_confirmation.py` (Regime filter)

**Changes**:
1. Each filter's output adapted to return discrete signal: +1 (strong buy), 0 (neutral), -1 (strong sell)
2. Add metadata tags: `pattern_id`, `confidence`
3. Backward compatibility: existing behavior unchanged if called directly

**Example Adaptation** (Renko):
```python
# Before: return boolean (trade_yes_no)
# After: return signal +1/-1/0 + metadata

def get_hierarchical_signal(self, price_data):
    """Hierarchical mode: return signal strength"""
    structure_quality = self.analyze_structure(price_data)
    
    if structure_quality > 0.8:
        return {'signal': +1, 'pattern': 'StructureConfirmed', 'confidence': 0.9}
    elif structure_quality > 0.5:
        return {'signal': +1, 'pattern': 'StructureWeak', 'confidence': 0.6}
    elif structure_quality < -0.8:
        return {'signal': -1, 'pattern': 'ReverseConfirmed', 'confidence': 0.9}
    else:
        return {'signal': 0, 'pattern': 'Neutral', 'confidence': 0.5}
```

**Definition of Done**:
- [ ] RenkoStructureFilter.get_hierarchical_signal() implemented
- [ ] StochasticMomentumFilter.get_hierarchical_signal() implemented
- [ ] RegimeContextFilter.get_hierarchical_signal() implemented
- [ ] All return signals in range [-1, 0, +1] with metadata
- [ ] Backward compatibility tests pass

---

### Task 3: Create Signal Router (Est. 2 hours)

**File**: `app/strategies/signal_router.py` (NEW or modify existing)

```python
class SignalRouter:
    """Routes signals through base or hierarchical mode"""
    
    def __init__(self, mode: str = 'base'):
        """
        mode: 'base' (3-of-3 AND) | 'hierarchical' (2-of-3) | 'rigid_and' (strict)
        """
        self.mode = mode
        self.hierarchy = FilterHierarchy() if mode == 'hierarchical' else None
    
    def evaluate(self, renko, stoch, regime):
        if self.mode == 'base':
            # Current logic: all 3 must agree
            return (renko and stoch and regime), quality=None
        elif self.mode == 'hierarchical':
            # New logic: 2-of-3 suffices
            result = self.hierarchy.evaluate(renko, stoch, regime)
            is_trade = result['decision'] != 'NEUTRAL'
            return is_trade, result['quality_score'], result
        elif self.mode == 'rigid_and':
            # Strict: all 3 must agree AND be strong
            all_agree = (renko and stoch and regime)
            return all_agree and all_strong, quality=None
```

**Definition of Done**:
- [ ] SignalRouter class created with mode switching
- [ ] Mode selection via config file or CLI flag
- [ ] Tests verify each mode produces expected behavior

---

### Task 4: Unit Tests (Est. 4 hours)

**File**: `tests/test_filter_hierarchy.py` (NEW)

```python
import pytest
from app.strategies.filter_hierarchy import FilterHierarchy, FilterSignal

class TestFilterHierarchy:
    
    def setup_method(self):
        self.hierarchy = FilterHierarchy(config={'voting_threshold': 2})
    
    # 8 edge cases for 3-filter voting
    def test_unanimous_buy(self):
        """3-of-3 BUY votes → quality 1.00"""
        result = self.hierarchy.evaluate(+1, +1, +1)
        assert result['decision'] == 'BUY'
        assert result['quality_score'] == 1.00
        assert result['votes']['buy'] == 3
    
    def test_majority_buy(self):
        """2-of-3 BUY votes → quality 0.78"""
        result = self.hierarchy.evaluate(+1, +1, 0)
        assert result['decision'] == 'BUY'
        assert result['quality_score'] == 0.78
        assert result['votes']['buy'] == 2
    
    def test_split_decision(self):
        """1-of-3 BUY, 1-of-3 SELL, 1-of-3 NEUTRAL → no trade"""
        result = self.hierarchy.evaluate(+1, -1, 0)
        assert result['decision'] == 'NEUTRAL'
    
    def test_minority_buy(self):
        """1-of-3 BUY → no trade"""
        result = self.hierarchy.evaluate(+1, 0, 0)
        assert result['decision'] == 'NEUTRAL'
    
    def test_quality_scoring(self):
        """Verify quality_score function"""
        assert self.hierarchy._quality_score(3) == 1.00
        assert self.hierarchy._quality_score(2) == 0.78
        assert self.hierarchy._quality_score(1) == 0.00
        assert self.hierarchy._quality_score(0) == 0.00
    
    def test_consensus_tracking(self):
        """Verify consensus filters are correctly identified"""
        result = self.hierarchy.evaluate(+1, +1, -1)  # Renko & Stoch agree on BUY
        assert set(result['consensus']) == {'Renko', 'Stoch'}
    
    def test_sell_consensus(self):
        """Test SELL consensus"""
        result = self.hierarchy.evaluate(-1, -1, +1)
        assert result['decision'] == 'SELL'
        assert set(result['consensus']) == {'Renko', 'Stoch'}
    
    def test_history_tracking(self):
        """Verify signal history maintained"""
        self.hierarchy.evaluate(+1, +1, +1)
        self.hierarchy.evaluate(0, 0, 0)
        assert len(self.hierarchy.get_signal_history()) == 2
```

**Definition of Done**:
- [ ] All 8 tests pass
- [ ] Code coverage ≥95% for FilterHierarchy
- [ ] Edge cases documented

---

### Task 5: Integration & Backtest (Est. 5 hours)

**Steps**:
1. Modify `phase1_remediation_backtest.py` to accept `--mode hierarchical` flag
2. Run backtest on 6-stock portfolio with new mode
3. Compare Phase 1 results vs Phase 0 baseline
4. Generate comparison report

**Test Cases**:
```
Backtest: 6 stocks × 3 modes (base, hierarchical, rigid_and)
├─ RELIND: 111 bars
├─ TCS: 111 bars
├─ INFTEC: 111 bars
├─ WIPRO: 111 bars
├─ BAFINS: 111 bars
└─ MARUTI: 111 bars

Expected Results (Phase 1 Hierarchical vs Phase 0 Base):
├─ ✅ TCS entry on Mar 23: Entry occurs (quality_score ~0.88)
├─ ✅ Profit factor: 0.59 → 0.65+ (improvement)
├─ ✅ Win rate: 16.7% → 22%+ (improvement)
└─ ✅ Max loss: stays <7.4% (no collapse)
```

**Definition of Done**:
- [ ] Backtest runs without errors (mode='hierarchical')
- [ ] Phase 1 validation gates assessed:
  - [ ] Gate 1: TCS Mar 23 rebound captured ✅
  - [ ] Gate 2: Profit factor ≥0.59 ✅
  - [ ] Gate 3: Win rate ≥20% ✅
- [ ] Comparison report generated

---

## 4. Validation Gates (Phase 1 Completion)

### Gate 1: TCS Mar 23 Rebound Captured ✅
**Requirement**: Entry signal generated at TCS 2026-03-23 @ ₹2383.80  
**Current (Base)**: No entry at this price (overfiltered)  
**Success Criteria**: Hierarchical produces entry signal with quality_score ≥0.75  
**Metric to track**: `signal.quality_score` for this bar

```
Base mode on TCS Mar 23:
├─ Renko: SELL (downtrend continuing)
├─ Stoch: NEUTRAL (choppy)
└─ Regime: SELL (downtrend)
Result: 3-of-3 SELL → no BUY trade ❌

Hierarchical mode on TCS Mar 23:
├─ Renko: SELL (structure weak, signal 0)
├─ Stoch: BUY (oversold bounce, signal +1)
└─ Regime: BUY (shift to mild-uptrend detected, signal +1)
Result: 2-of-3 BUY (Stoch + Regime) → entry ✅ quality_score=0.78
```

### Gate 2: Profit Factor ≥0.59
**Requirement**: Hierarchical profit factor on 6-stock portfolio ≥ baseline 0.59  
**Success Criteria**: No regression from Phase 0; ideally 0.60+  
**Metric to track**: `results['profit_factor']` across all backtests

### Gate 3: Win Rate ≥20%
**Requirement**: Average win rate across 6 stocks ≥20%  
**Current (Base)**: 13.1%  
**Success Criteria**: Hierarchical ≥20%  
**Metric to track**: `results['win_rate']` average

### Gate 4: No Catastrophic Losses
**Requirement**: Max single-trade loss stays <7.4%  
**Current (Base)**: Max 7.4% on INFTEC  
**Success Criteria**: No new trades with loss >7.4%  
**Metric to track**: `max(abs(trade['pnl_pct']))` for all trades

---

## 5. Success Criteria & Approval

### Phase 1 Approval: ≥2 of 4 gates passed
- [ ] **Gate 1**: TCS Mar 23 entry captured (quality_score ≥0.75)
- [ ] **Gate 2**: Profit factor ≥0.59 (no regression)
- [ ] **Gate 3**: Win rate ≥20% (improvement from 16.7%)
- [ ] **Gate 4**: No losses >7.4% (risk controlled)

### Approval Decision
**If ≥2 gates passed**: ✅ Approve Phase 2 (Dynamic Thresholds)  
**If <2 gates passed**: ⏸️ Recalibrate 2-of-3 weights, retest

---

## 6. Development Timeline

| Date | Task | Owner | Status |
|------|------|-------|--------|
| Jun 6 | FilterHierarchy module created | Dev | 🔄 |
| Jun 6 | Existing filters adapted | Dev | 🔄 |
| Jun 7 | Signal router integrated | Dev | 🔄 |
| Jun 7 | Unit tests written & passing | QA | 🔄 |
| Jun 8 | Integration testing | QA | 🔄 |
| Jun 8 | Backtest run (6 stocks, mode=hierarchical) | Dev | 🔄 |
| Jun 9 | Validation gates assessed | QA | 🔄 |
| Jun 10 | Phase 1 approval report | Strategy Lead | 🔄 |
| Jun 11 | Phase 2 kickoff (if approved) | Dev | 🔄 |

---

## 7. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Looser criteria → more false signals | Unit test: Ensure 2-of-3 not greedy; validate on known losers don't trigger |
| Quality score miscalibration | Ablation: Run backtest with different quality thresholds (0.60, 0.70, 0.80) |
| Integration bugs | Integration tests: Verify signal flow end-to-end (data → filter → signal → trade) |
| Overfitting to TCS success | Cross-validate on all 6 stocks; ensure improvement not isolated to one ticker |

---

## 8. Deliverables

By **June 12, 2026, 5 PM**:

1. **Code**:
   - [ ] `app/strategies/filter_hierarchy.py` (complete, tested)
   - [ ] `app/strategies/signal_router.py` (complete, tested)
   - [ ] Modified filters (Renko, Stoch, Regime) with hierarchical output
   - [ ] All tests passing

2. **Tests**:
   - [ ] `tests/test_filter_hierarchy.py` (8 edge case tests, ≥95% coverage)
   - [ ] Integration tests (end-to-end signal flow)

3. **Documentation**:
   - [ ] Code comments (docstrings for all methods)
   - [ ] Signal flow diagram (Markdown with ASCII art)
   - [ ] Config examples (YAML/JSON)

4. **Backtest Results**:
   - [ ] `phase1_hierarchical_backtest_[date].json` (raw results)
   - [ ] `PHASE1_VALIDATION_REPORT.md` (gates assessment, approval decision)

5. **Sign-Off**:
   - [ ] QA Lead sign-off (tests pass, code quality ✅)
   - [ ] Strategy Lead sign-off (gates met or remediation plan documented)

---

## 9. Rollback Plan

If Phase 1 fails validation:

1. **Immediate**: Revert to Phase 0 code (mode='base' stays default)
2. **Root Cause Analysis**: Identify which gate failed and why
3. **Recalibration Options**:
   - Option A: Adjust quality_weights (e.g., 2-of-3 → 0.80 instead of 0.78)
   - Option B: Strengthen filter outputs (e.g., require +1 signals, not just >0)
   - Option C: Add hysteresis (only change decision if sustained for 2+ bars)
4. **Retest**: Run backtest again with adjustment
5. **Decision**: Proceed to Phase 2, continue Phase 1 iteration, or move to alternate approach

---

## Appendix: Current State (Phase 0 Baseline)

From `phase1_remediation_backtest_20260601_091057.json`:

```
BASE Mode (3-of-3 AND):
├─ Total Trades: 63
├─ Win Rate: 13.1% avg
├─ Profit Factor: 0.34 avg
├─ Sharpe Ratio: –9.5 avg
└─ Problem: Too many trades, high churn, low selectivity

HIERARCHICAL Mode (Current 2-of-3, Phase 0):
├─ Total Trades: 16
├─ Win Rate: 16.7% avg
├─ Profit Factor: 0.59 avg
├─ Sharpe Ratio: –4.9 avg
├─ Best: TCS (+1.43% return, 1.34 PF, 33% WR) ✅
└─ Observation: Concept already works; Phase 1 formalizes & improves it

RIGID_AND Mode (Overly strict):
├─ Total Trades: 6
├─ Win Rate: 0% avg
├─ Profit Factor: 0.0 avg
└─ Problem: Too strict, misses too many opportunities
```

**Phase 1 Goal**: Formalize and optimize the hierarchical approach that already showed promise in Phase 0 baseline.

---

**Document prepared by**: Strategy Enhancement Task Force  
**Date**: June 1, 2026  
**Version**: 1.0  
**Phase**: Phase 1 – Hierarchical Filter Logic  
**Next Review**: June 12, 2026 (Gate Assessment + Phase 2 Decision)
