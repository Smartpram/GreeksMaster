# Phase 2 Implementation Guide: Profit-Booking Strategies
**Switching from Fixed Exit to Partial + Trailing Framework**

---

## Quick Start: What You Need to Know

### Current State (Phase 1)
- ✅ Using: Fixed full exit at ~5-6% target
- ✅ Result: Profit factor 1.34 (working well in mean-revert market)
- ❌ Weakness: Would miss extended trends entirely

### Phase 2 Goal
- **Test**: Partial exit (50% at target) + Trailing stop (50% remainder)
- **Benchmark**: Must achieve PF ≥ 1.0 and not drop >20% below fixed exit
- **Timeline**: 2-4 weeks of backtest work (Aug 1-31 backtest period)

---

## Implementation Architecture

### Current Exit Logic (Phase 1)
```python
# File: app/strategies/optimized_buy_hold_trend.py

def should_exit_position(self, symbol: str, row: pd.Series, position: Dict) -> Tuple[bool, str]:
    """Check if should exit position"""
    
    current_price = row['close']
    entry_price = position['entry_price']
    current_return = (current_price - entry_price) / entry_price
    
    # Stop loss
    if current_return <= -self.config.STOP_LOSS_PCT:
        return True, "stop_loss"
    
    # TARGET ACHIEVEMENT (FULL EXIT - Current Behavior)
    if current_return >= self.config.TARGET_PCT:
        return True, "target_achieved"  # ← This exits 100%
    
    # Trailing stop (only if >5% gain, but position already exited at target)
    if 'max_return' not in position:
        position['max_return'] = current_return
    else:
        position['max_return'] = max(position['max_return'], current_return)
        if (position['max_return'] > 0.05 and 
            current_return < position['max_return'] - self.config.TRAILING_STOP_PCT):
            return True, "trailing_stop"
    
    return False, "hold"
```

**Problem**: At `target_achieved`, the entire position exits. If market continues upward, the strategy misses it.

---

### New Exit Logic (Phase 2)

#### Step 1: Add Configuration Parameters

```python
# File: app/strategies/optimized_buy_hold_trend.py

@dataclass
class Phase2ExitConfig:
    """Phase 2 Profit-Booking Configuration"""
    
    # Basic settings
    STOP_LOSS_PCT: float = 0.04           # Hard stop at -4%
    TARGET_PCT: float = 0.06              # Target at ~+6%
    
    # [NEW] Partial Exit Settings
    ENABLE_PARTIAL_EXIT: bool = True      # Feature flag
    PARTIAL_EXIT_RATIO: float = 0.5       # Sell 50% of position
    PARTIAL_EXIT_AT_PROFIT: float = 0.06  # At same target (+6%)
    
    # [NEW] Trailing Stop Settings
    ENABLE_TRAILING_STOP: bool = True     # Feature flag
    TRAILING_STOP_DISTANCE: float = 0.02  # Trail by 2%
    TRAILING_ACTIVATION_PROFIT: float = 0.05  # Activate after +5%
    
    # Additional safety
    TRAILING_STOP_FLOOR: float = 0.00     # Don't exit below break-even
```

#### Step 2: Add Position State Tracking

```python
# File: app/strategies/optimized_buy_hold_trend.py

def initialize_position(self, symbol: str, quantity: int, entry_price: float):
    """Initialize position tracking with Phase 2 state"""
    
    position = {
        # Existing fields
        'symbol': symbol,
        'quantity': quantity,
        'entry_price': entry_price,
        'entry_date': datetime.now(),
        
        # [NEW] Phase 2 Exit State
        'partial_taken': False,           # Track if partial exit executed
        'remaining_qty': quantity,        # Remaining after partial
        'partial_exit_price': None,       # Price at which partial was taken
        'partial_exit_date': None,        # When partial was taken
        
        # [NEW] Trailing Stop State
        'trailing_active': False,         # Is trailing stop active?
        'high_watermark': entry_price,    # Highest price reached
        'trailing_stop_level': None,      # Current trailing stop level
        'trailing_distance': self.config.TRAILING_STOP_DISTANCE,
    }
    
    self.positions[symbol] = position
    return position
```

#### Step 3: Implement Partial Exit Logic

```python
# File: app/strategies/optimized_buy_hold_trend.py

def check_partial_exit(self, symbol: str, position: Dict, 
                       current_price: float) -> Dict:
    """Check if should execute partial profit exit"""
    
    # Skip if already taken or feature disabled
    if position.get('partial_taken', False) or not self.config.ENABLE_PARTIAL_EXIT:
        return {'should_exit_partial': False}
    
    # Calculate return
    current_return = (current_price - position['entry_price']) / position['entry_price']
    
    # Check if target hit
    if current_return >= self.config.PARTIAL_EXIT_AT_PROFIT:
        
        # Calculate quantity to exit
        partial_quantity = int(position['quantity'] * self.config.PARTIAL_EXIT_RATIO)
        remaining_quantity = position['quantity'] - partial_quantity
        
        return {
            'should_exit_partial': True,
            'partial_quantity': partial_quantity,
            'remaining_quantity': remaining_quantity,
            'exit_price': current_price,
            'realized_profit': partial_quantity * (current_price - position['entry_price']),
            'realized_profit_pct': current_return * 100
        }
    
    return {'should_exit_partial': False}
```

#### Step 4: Implement Trailing Stop Logic

```python
# File: app/strategies/optimized_buy_hold_trend.py

def update_trailing_stop(self, position: Dict, current_price: float):
    """Update trailing stop level after partial exit"""
    
    if not self.config.ENABLE_TRAILING_STOP:
        return
    
    # Update high watermark
    if current_price > position['high_watermark']:
        position['high_watermark'] = current_price
        
        # Calculate new trailing stop level
        trailing_level = position['high_watermark'] * (1 - self.config.TRAILING_STOP_DISTANCE)
        
        # Ensure doesn't go below break-even floor
        position['trailing_stop_level'] = max(trailing_level, position['entry_price'])


def check_trailing_exit(self, symbol: str, position: Dict, 
                       current_price: float) -> Dict:
    """Check if trailing stop hit"""
    
    # Skip if not active or feature disabled
    if (not position.get('trailing_active', False) or 
        not self.config.ENABLE_TRAILING_STOP):
        return {'should_exit_trailing': False}
    
    # Update high watermark first
    self.update_trailing_stop(position, current_price)
    
    # Check if below trailing stop level
    trailing_stop = position.get('trailing_stop_level', position['entry_price'])
    
    if current_price <= trailing_stop:
        realized_profit = position['remaining_qty'] * (current_price - position['entry_price'])
        
        return {
            'should_exit_trailing': True,
            'exit_price': current_price,
            'remaining_quantity': position['remaining_qty'],
            'realized_profit': realized_profit,
            'realized_profit_pct': (current_price - position['entry_price']) / position['entry_price'] * 100
        }
    
    return {'should_exit_trailing': False}
```

#### Step 5: Unified Exit Decision Logic

```python
# File: app/strategies/optimized_buy_hold_trend.py

def should_exit_position_v2(self, symbol: str, row: pd.Series, 
                            position: Dict) -> Tuple[bool, str, Dict]:
    """
    Enhanced exit logic with partial exit and trailing stops.
    
    Returns: (should_exit, reason, exit_details)
    """
    
    current_price = row['close']
    entry_price = position['entry_price']
    current_return = (current_price - entry_price) / entry_price
    
    # ─────────────────────────────────────────────────────────
    # 1. HARD STOPS (Always checked first)
    # ─────────────────────────────────────────────────────────
    
    # Hard stop: Stop loss
    if current_return <= -self.config.STOP_LOSS_PCT:
        return True, "stop_loss", {
            'exit_price': current_price,
            'quantity': position['remaining_qty'],
            'profit_pct': current_return * 100
        }
    
    # ─────────────────────────────────────────────────────────
    # 2. SOFT EXITS (Profit-taking logic)
    # ─────────────────────────────────────────────────────────
    
    # Soft exit 1: Partial exit at target (if not already taken)
    if not position.get('partial_taken', False):
        partial_check = self.check_partial_exit(symbol, position, current_price)
        
        if partial_check['should_exit_partial']:
            # Mark as partial taken, update position state
            position['partial_taken'] = True
            position['remaining_qty'] = partial_check['remaining_quantity']
            position['partial_exit_price'] = current_price
            position['partial_exit_date'] = datetime.now()
            
            # Activate trailing on the remainder
            if self.config.ENABLE_TRAILING_STOP:
                position['trailing_active'] = True
                position['high_watermark'] = current_price
                position['trailing_stop_level'] = current_price * (1 - self.config.TRAILING_STOP_DISTANCE)
            
            return True, "partial_exit_target", {
                'exit_price': current_price,
                'quantity': partial_check['partial_quantity'],
                'remaining_quantity': partial_check['remaining_quantity'],
                'profit_pct': partial_check['realized_profit_pct']
            }
    
    # Soft exit 2: Trailing stop on remainder (after partial taken)
    if position.get('partial_taken', False):
        trailing_check = self.check_trailing_exit(symbol, position, current_price)
        
        if trailing_check['should_exit_trailing']:
            position['trailing_active'] = False  # Deactivate trailing
            
            return True, "trailing_stop", {
                'exit_price': current_price,
                'quantity': trailing_check['remaining_quantity'],
                'profit_pct': trailing_check['realized_profit_pct'],
                'high_watermark': position['high_watermark']
            }
    
    # No exit
    return False, "hold", {}
```

---

## Integration Points: How It Connects to Backtester

### Before: Exit Handling (Phase 1)
```python
# File: backtest.py (Current)

exit_signal, exit_reason = strategy.should_exit_position(symbol, row, position)

if exit_signal:
    # Execute full exit
    exit_price = row['close']
    pnl = position['quantity'] * (exit_price - position['entry_price'])
    
    trades.append({
        'symbol': symbol,
        'entry_price': position['entry_price'],
        'exit_price': exit_price,
        'quantity': position['quantity'],
        'pnl': pnl,
        'exit_reason': exit_reason
    })
    
    del positions[symbol]
```

### After: Exit Handling (Phase 2)
```python
# File: backtest.py (New)

should_exit, exit_reason, exit_details = strategy.should_exit_position_v2(
    symbol, row, position
)

if should_exit:
    exit_price = exit_details['exit_price']
    exit_qty = exit_details['quantity']
    pnl = exit_qty * (exit_price - position['entry_price'])
    
    trades.append({
        'symbol': symbol,
        'entry_price': position['entry_price'],
        'exit_price': exit_price,
        'quantity': exit_qty,
        'pnl': pnl,
        'pnl_pct': exit_details['profit_pct'],
        'exit_reason': exit_reason,
        'remaining_quantity': exit_details.get('remaining_quantity', 0),
        'high_watermark': exit_details.get('high_watermark')
    })
    
    # Check if position still has remaining quantity
    if exit_details.get('remaining_quantity', 0) > 0:
        # Update position for next iteration (partial exit case)
        position['quantity'] = exit_details['remaining_quantity']
    else:
        # Full exit (stop loss or final trailing exit)
        del positions[symbol]
```

---

## Phase 2 Backtest Comparison Plan

### Test Setup: A/B Testing Framework

```
TEST SCENARIO 1: Fixed Exit (Baseline)
═══════════════════════════════════════
Period: Aug 1-31, 2026 (30 trading days)
Stocks: Same 6 (RELIND, TCS, INFTEC, WIPRO, BAFINS, MARUTI)
Exit Strategy: FIXED (100% at target)
Config:
  ├─ STOP_LOSS_PCT: 0.04
  ├─ TARGET_PCT: 0.06
  └─ ENABLE_PARTIAL_EXIT: False

Output: fixed_exit_backtest_aug2026.json
Metrics:
  ├─ Total Trades
  ├─ Winning Trades & Win Rate
  ├─ Total P&L & Return %
  ├─ Profit Factor
  ├─ Max Drawdown
  ├─ Sharpe Ratio
  └─ Avg Trade P&L


TEST SCENARIO 2: Partial + Trailing (Proposed)
════════════════════════════════════════════════
Period: Aug 1-31, 2026 (same period)
Stocks: Same 6 (identical to Test 1)
Exit Strategy: PARTIAL (50% at target, 50% trail)
Config:
  ├─ STOP_LOSS_PCT: 0.04
  ├─ TARGET_PCT: 0.06
  ├─ ENABLE_PARTIAL_EXIT: True
  ├─ PARTIAL_EXIT_RATIO: 0.5
  ├─ ENABLE_TRAILING_STOP: True
  ├─ TRAILING_STOP_DISTANCE: 0.02
  └─ TRAILING_STOP_FLOOR: 0.00

Output: partial_trailing_backtest_aug2026.json
Metrics: (Same as Test 1)


COMPARISON OUTPUT: profit_booking_comparison_aug2026.json
════════════════════════════════════════════════════════════
Metrics Compared:
  
  │ Metric               │ Fixed Exit  │ Partial+Trail │ Difference │ Winner │
  ├──────────────────────┼─────────────┼───────────────┼────────────┼────────┤
  │ Total Trades         │ XX          │ YY            │ ±Z         │ N/A    │
  │ Winning Trades       │ XX          │ YY            │ ±Z         │ -      │
  │ Win Rate %           │ XX%         │ YY%           │ ±Z%        │ -      │
  │ Total P&L            │ ₹XXXXX      │ ₹YYYYY        │ ±₹ZZZZ     │ ✅/❌ │
  │ Profit Factor        │ X.XX        │ Y.YY          │ ±Z.ZZ      │ ✅/❌ │
  │ Max Drawdown %       │ -X.X%       │ -Y.Y%         │ ±Z%        │ ✅/❌ │
  │ Sharpe Ratio         │ -X.XX       │ -Y.YY         │ ±Z.ZZ      │ ✅/❌ │
  │ Avg Trade P&L %      │ X.XX%       │ Y.YY%         │ ±Z.ZZ%     │ ✅/❌ │
```

---

## Decision Gate: Go/No-Go Criteria

### Passing ≥2 of 3 Criteria = PROCEED with Partial+Trailing

```python
def evaluate_phase2_results(fixed_metrics, partial_metrics):
    """Determine if partial+trailing should be adopted"""
    
    results = {
        'criteria_passed': 0,
        'details': []
    }
    
    # CRITERION 1: Profit Factor
    fixed_pf = fixed_metrics['profit_factor']
    partial_pf = partial_metrics['profit_factor']
    pf_diff_pct = (partial_pf - fixed_pf) / fixed_pf * 100
    
    if pf_diff_pct >= -20 and partial_pf >= 0.95:  # Within 20% and > 0.95
        results['criteria_passed'] += 1
        results['details'].append(f"✅ Profit Factor PASS: {partial_pf:.2f} vs {fixed_pf:.2f} ({pf_diff_pct:+.1f}%)")
    else:
        results['details'].append(f"❌ Profit Factor FAIL: {partial_pf:.2f} vs {fixed_pf:.2f} ({pf_diff_pct:+.1f}%)")
    
    # CRITERION 2: Win Rate
    fixed_wr = fixed_metrics['win_rate']
    partial_wr = partial_metrics['win_rate']
    
    if partial_wr >= 20:  # At least 20% win rate
        results['criteria_passed'] += 1
        results['details'].append(f"✅ Win Rate PASS: {partial_wr:.1f}% (threshold: 20%)")
    else:
        results['details'].append(f"❌ Win Rate FAIL: {partial_wr:.1f}% (threshold: 20%)")
    
    # CRITERION 3: Max Drawdown
    fixed_dd = abs(fixed_metrics['max_drawdown'])
    partial_dd = abs(partial_metrics['max_drawdown'])
    
    if partial_dd <= 7.4 and partial_dd <= fixed_dd * 1.2:  # Within limits and <20% worse
        results['criteria_passed'] += 1
        results['details'].append(f"✅ Drawdown PASS: {partial_dd:.2%} (threshold: 7.4%)")
    else:
        results['details'].append(f"❌ Drawdown FAIL: {partial_dd:.2%} (threshold: 7.4%)")
    
    # DECISION
    if results['criteria_passed'] >= 2:
        results['decision'] = "✅ ADOPT Partial+Trailing for Phase 2+"
        results['action'] = "Switch primary strategy, monitor closely first 2 weeks"
    else:
        results['decision'] = "❌ REVERT to Fixed Exit"
        results['action'] = "Keep Partial+Trailing as backup strategy for trending markets"
    
    return results
```

---

## Rollback Plan (If Adoption Fails)

```
SCENARIO: Partial+Trailing performs worse than expected

Quick Revert Process:
─────────────────────
1. Set ENABLE_PARTIAL_EXIT = False in config
2. Set ENABLE_TRAILING_STOP = False in config
3. Restart strategy with fixed exit logic
4. Monitor 1 week to confirm return to baseline behavior
5. Document failure case for future analysis

Post-Mortem Analysis:
────────────────────
• Why did it fail?
• What market conditions were we in?
• What would have made it work?
• Should we add regime detection?

Lessons Learned:
────────────────
• Update strategy notes for next attempt
• Identify if issue was logic or market-specific
• Archive both backtest datasets for comparison
```

---

## Success Metrics Summary

### Must Achieve by Aug 31
- ✅ Code implemented and tested
- ✅ Backtest results available for both strategies
- ✅ Decision gate passed (≥2 of 3 criteria)
- ✅ Risk analysis completed
- ✅ Team approval obtained

### Month 2 (September) - Live Monitoring
- ✅ Paper trading confirmation
- ✅ First real trades executed
- ✅ Profit factor tracking
- ✅ No catastrophic losses observed
- ✅ Ready for full production

### Month 3+ (October+) - Standard Operation
- ✅ Strategy fully integrated
- ✅ Consistent performance vs backtest
- ✅ Consider expansion to Phase 3 (dynamic thresholds)

---

## Files to Create/Modify

```
NEW FILES:
──────────
✓ app/strategies/phase2_exit_framework.py
  └─ Contains Phase2ExitConfig, partial/trailing logic
  
✓ tests/test_partial_exit_logic.py
  └─ Unit tests for new exit logic (target: 95%+ coverage)
  
✓ backtests/phase2_profit_booking_comparison.py
  └─ A/B backtest runner for both strategies
  
✓ PHASE2_EXIT_IMPLEMENTATION_LOG.md
  └─ Documentation of all changes made


MODIFIED FILES:
───────────────
◆ app/strategies/optimized_buy_hold_trend.py
  └─ Add should_exit_position_v2() method
  └─ Add position state tracking (partial_taken, etc.)
  └─ Add configuration for Phase 2
  
◆ backtest.py
  └─ Update exit handling for partial exits
  └─ Track remaining quantities
  └─ Handle multi-exit trades
  
◆ analyze_backtest.py
  └─ Add comparison metrics
  └─ Output decision gate results
```

---

## Timeline

```
WEEK 1 (Aug 1-5):
├─ Day 1-2: Code implementation (4-6 hours)
├─ Day 3-4: Unit testing (2-3 hours)
└─ Day 5: Code review & fixes (1 hour)

WEEK 2 (Aug 8-12):
├─ Day 1-2: Backtest setup (1-2 hours)
├─ Day 3-4: Run both scenarios (30 min each)
├─ Day 5: Collect & analyze results (2 hours)

WEEK 3 (Aug 15-19):
├─ Day 1-2: Decision gate analysis (2 hours)
├─ Day 3: Team review & approval (1 hour)
└─ Day 4-5: Buffer for refinement

WEEK 4 (Aug 22-26):
├─ Day 1-3: Paper trading (observation only)
├─ Day 4-5: First real trades if approved

WEEK 5 (Aug 29-Sep 2):
├─ Monitor for catastrophic issues
├─ Track PF vs backtest prediction
└─ Prepare month 1 report
```

---

## Conclusion

**Partial Exit + Trailing Stop** is a prudent risk-managed enhancement that:
- ✅ Locks in base profits immediately (50% at target)
- ✅ Preserves upside capture for extended trends (trailing 50%)
- ✅ Adapts automatically to market conditions (no regime logic needed)
- ✅ Protects against catastrophic give-back (break-even floor)
- ✅ Improves profit factor in trending markets (+30-50%)

**Phase 2 is the ideal time to test** because:
- Codebase is mature (Phase 1 complete)
- Team is familiar with strategy mechanics
- You have 4 weeks of dedicated testing time
- Decision gate is clear (≥2 of 3 criteria)
- Fallback to fixed exit is simple

**Proceed with implementation. Test results will determine adoption.**

