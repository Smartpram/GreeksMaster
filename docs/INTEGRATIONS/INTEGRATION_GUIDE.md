# Integration Guide: Unified Profit Booking Strategy

## Overview
This guide shows how to integrate `unified_profit_booking.py` with your existing Buy-and-Hold trend-following strategy in `buy_hold_trend.py`.

**Key Achievement**: Conditional trailing stops that disable automatically in mean-reverting markets.

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Step-by-Step Integration](#step-by-step-integration)
3. [Configuration](#configuration)
4. [Signal Flow Diagram](#signal-flow-diagram)
5. [Testing Checklist](#testing-checklist)
6. [Rollback Plan](#rollback-plan)

---

## Architecture Overview

### Current State (Before Integration)
```
buy_hold_trend.py (Strategy Executor)
    ↓
    Uses: profit_booking_manager.py (Fixed/Trailing hardcoded)
    ↓
    Executes orders directly
```

### Future State (After Integration)
```
buy_hold_trend.py (Strategy Executor)
    ↓
    Uses: unified_profit_booking.py (NEW - Conditional)
    ↓
    Regime Detection Module
    ↓
    Trails Only If: (TRENDING) AND (All 3 conditions pass)
    ↓
    Falls Back To: FIXED_FULL_EXIT (safe default)
    ↓
    Executes orders with automatic safeguards
```

### Components
| Component | File | Role |
|-----------|------|------|
| Strategy Executor | `buy_hold_trend.py` | Entry signal generation, order placement |
| Unified Manager | `unified_profit_booking.py` | **NEW** - Conditional exit logic with regime detection |
| Profit Booking (Legacy) | `profit_booking_manager.py` | Underlying calculations (corrected metrics) |
| Regime Monitor | `strategy_regime_monitor.py` | **NEW** - Daily/weekly trend detection |
| Production Safeguards | `strategy_config_validator.py` | **NEW** - Configuration validation + hard stops |
| Test Suite | `test_unified_strategy.py` | **NEW** - Comprehensive test cases |

---

## Step-by-Step Integration

### Phase 1: Preparation (Before Code Changes)

#### 1.1 Backup Current Configuration
```bash
# Save current settings
cp app/strategies/profit_booking_manager.py app/strategies/profit_booking_manager.py.backup_20260601
cp app/strategies/buy_hold_trend.py app/strategies/buy_hold_trend.py.backup_20260601
```

#### 1.2 Verify Backtest Results
```bash
# Ensure corrected calculations are in place
python backtest_profit_booking_breeze.py
# Should show:
# - Fixed Exit: PF=1.14, Drawdown=-77.91% ✅
# - Partial Trailing: PF=0.57, Drawdown=-528% ✅
```

---

### Phase 2: Deploy New Modules (No Existing Code Changes Yet)

#### 2.1 Add Unified Profit Booking Manager
- **File**: `app/strategies/unified_profit_booking.py` ✅ Already created
- **Status**: Ready to use
- **Dependencies**: pandas, numpy (already in requirements)

#### 2.2 Create Configuration Validator (Step 3 below)

#### 2.3 Create Regime Monitor (Step 4 below)

#### 2.4 Create Test Suite (Step 5 below)

---

### Phase 3: Connect to buy_hold_trend.py

#### 3.1 Import Statement
In `buy_hold_trend.py`, add at the top:
```python
from app.strategies.unified_profit_booking import (
    UnifiedProfitBookingManager,
    ExitStrategy,
    MarketRegime,
)
from app.strategies.strategy_config_validator import (
    StrategyConfigValidator,
    StrategyConfigError,
)
from app.strategies.strategy_regime_monitor import StrategyRegimeMonitor
```

#### 3.2 Initialize Manager in Strategy Class
Replace the old `ProfitBookingManager` initialization:

**BEFORE**:
```python
class BuyHoldTrendStrategy:
    def __init__(self):
        self.profit_manager = ProfitBookingManager()
```

**AFTER**:
```python
class BuyHoldTrendStrategy:
    def __init__(self):
        # New: Unified manager with conditional trailing
        self.unified_manager = UnifiedProfitBookingManager()
        
        # New: Regime detector
        self.regime_monitor = StrategyRegimeMonitor()
        
        # New: Configuration validator
        validator = StrategyConfigValidator()
        validator.validate_on_startup()  # Hard stops misconfiguration
        
        # Fallback for compatibility
        self.profit_manager = None
```

#### 3.3 Update Entry Signal Handler
When entering a trade, use the unified manager:

**BEFORE**:
```python
def execute_entry(self, symbol, entry_price, quantity):
    position = self.profit_manager.create_position(
        symbol=symbol,
        entry_price=entry_price,
        quantity=quantity,
        position_id=f"{symbol}_{timestamp}",
    )
```

**AFTER**:
```python
def execute_entry(self, symbol, entry_price, quantity):
    # Detect current market regime (updated every entry)
    self.regime_monitor.update_regime()
    recent_trades = self.unified_manager.exit_history[-20:]  # Last 20 trades
    self.unified_manager.detect_market_regime(recent_trades)
    
    # Create position with AUTOMATIC strategy selection
    position = self.unified_manager.create_position(
        symbol=symbol,
        entry_price=entry_price,
        quantity=quantity,
        position_id=f"{symbol}_{timestamp}",
        auto_select_strategy=True,  # ✅ Automatic
    )
    
    logger.info(
        f"Entry: {symbol} | Strategy: {position['exit_strategy'].value} | "
        f"Regime: {self.unified_manager.market_regime.value}"
    )
```

#### 3.4 Update Exit Check (Replace Old Logic)
Replace the old exit check loop:

**BEFORE**:
```python
def check_exits(self, current_prices):
    for position_id, current_price in current_prices.items():
        should_exit, exit_price = self.profit_manager.check_exit(position_id, current_price)
        if should_exit:
            self.profit_manager.execute_exit(position_id, exit_price)
```

**AFTER**:
```python
def check_exits(self, current_prices):
    for position_id, current_price in current_prices.items():
        should_exit, reason, details = self.unified_manager.check_exit_conditions(
            position_id, 
            current_price
        )
        
        if should_exit:
            exit_price = details.get('exit_price', current_price)
            exit_qty = details.get('exit_qty', 0)
            
            exit_record = self.unified_manager.execute_exit(
                position_id, 
                exit_price, 
                exit_qty
            )
            
            # Log exit reason (shows if trailing was disallowed)
            logger.info(
                f"Exit: {exit_record['symbol']} | "
                f"Reason: {reason} | "
                f"P&L: {exit_record['pnl_pct']:.2f}% | "
                f"Strategy Used: {exit_record['strategy']}"
            )
```

#### 3.5 Add End-of-Day Regime Check
Add this method to get daily statistics:

```python
def end_of_day_report(self):
    """Called at market close"""
    
    stats = self.unified_manager.get_strategy_stats()
    distribution = self.unified_manager.get_strategy_distribution()
    
    logger.info(
        f"📊 EOD Report:\n"
        f"   Regime: {stats['market_regime']}\n"
        f"   PF: {stats['profit_factor']:.2f}\n"
        f"   Max DD: {stats['max_drawdown']:.2f}%\n"
        f"   Strategy Distribution: {distribution}"
    )
    
    # Check if regime changed (triggers re-backtest alert)
    regime_changed = self.regime_monitor.check_regime_change(
        current_regime=self.unified_manager.market_regime,
        trades=self.unified_manager.exit_history[-20:]
    )
    
    if regime_changed:
        logger.warning("⚠️ REGIME CHANGE DETECTED - Re-backtest recommended!")
```

---

## Configuration

### File: `app/strategies/unified_profit_booking.py` (Already in place)

Key configurable parameters:
```python
self.config = {
    'target_pct': 0.065,              # 6.5% profit target
    'stop_loss_pct': 0.04,            # 4.0% stop loss
    'trailing_stop_pct': 0.02,        # 2.0% trailing (if enabled)
    'partial_exit_ratio': 0.50,       # Exit 50% at target (if trailing used)
}
```

### Regime Thresholds
```python
# In unified_profit_booking.py
if avg_holding > 2.0:
    regime = MarketRegime.TRENDING      # Enable trailing (if conditions allow)
elif avg_holding < 1.0:
    regime = MarketRegime.MEAN_REVERTING # Disable trailing (no exceptions)
```

### Trailing Disallow Thresholds
From `TRAILING_STOPS_DESIGN_RULES.md`:
1. **No Post-Target Extension**: Extension count < 20% of recent trades
2. **Pure Intraday**: avg_holding_days < 1.0 ✅ Current market
3. **High Volatility**: max_drawdown_ratio > 3.0 (or abs(max_dd) > 200%)

---

## Signal Flow Diagram

```
Market Data (OHLC)
    ↓
    [BUY SIGNAL GENERATION]
    ├─ RSI < 30?
    ├─ Price near MA200?
    └─ Volume spike?
    ↓ YES → Entry Signal
    ↓
    ┌─────────────────────────────────────────┐
    │ UNIFIED_PROFIT_BOOKING.CREATE_POSITION  │
    └─────────────────────────────────────────┘
    ├─ Detect Market Regime
    │  ├─ Fetch last 20 trades
    │  ├─ Calculate avg_holding_days
    │  └─ Classify: TRENDING / MEAN_REVERTING
    │
    ├─ Assess Trailing Conditions
    │  ├─ Check: Post-target extension? [NO]
    │  ├─ Check: Pure intraday? [YES]
    │  ├─ Check: High post-target volatility? [YES]
    │  └─ Result: Trailing DISALLOWED
    │
    └─ Select Exit Strategy
       ├─ If MEAN_REVERTING: FIXED_FULL_EXIT ✅
       └─ If TRENDING + conditions pass: PARTIAL_WITH_TRAILING
    ↓
    [POSITION MONITORING LOOP]
    ├─ Check: current_price vs stop_loss?
    ├─ Check: current_price vs target?
    ├─ Check: current_price vs trailing_stop?
    └─ Repeat every tick
    ↓
    ┌─────────────────────────────────────────┐
    │ UNIFIED_PROFIT_BOOKING.CHECK_EXIT_COND  │
    └─────────────────────────────────────────┘
    ├─ Strategy = FIXED_FULL_EXIT
    │  └─ Exit IF: price ≥ target OR price ≤ SL
    │
    OR
    │
    ├─ Strategy = PARTIAL_WITH_TRAILING
    │  ├─ Exit IF: price ≤ SL (exit all)
    │  ├─ Exit IF: price ≥ target (exit 50%, set trailing)
    │  └─ Exit IF: price ≤ trailing_stop (exit remaining)
    ↓
    ┌─────────────────────────────────────────┐
    │ UNIFIED_PROFIT_BOOKING.EXECUTE_EXIT     │
    └─────────────────────────────────────────┘
    ├─ Record P&L
    ├─ Log exit reason
    └─ Track strategy used
    ↓
    [END OF DAY]
    ├─ Calculate stats
    ├─ Check regime change
    └─ Alert if conditions changed
```

---

## Testing Checklist

### Unit Tests (All in `test_unified_strategy.py` - see Step 5)

#### Pre-Integration Tests
- [ ] Test regime detection (mean-reverting vs trending)
- [ ] Test trailing conditions assessment
- [ ] Test strategy selection logic
- [ ] Test position creation
- [ ] Test exit condition checking
- [ ] Test fixed exit vs partial+trailing paths

#### Integration Tests
- [ ] Test end-to-end signal → entry → exit flow
- [ ] Test regime change detection during live trading
- [ ] Test configuration validation (hard stops)
- [ ] Test monitoring alerts trigger correctly

#### Production Tests (Paper Trading)
- [ ] Paper trade for 4 weeks with unified strategy
- [ ] Validate actual P&L vs backtest (₹359,850 baseline)
- [ ] Monitor regime for changes
- [ ] Confirm trailing never executes in mean-reverting regime

---

## Rollback Plan

### If Integration Issues Occur

#### Option 1: Quick Rollback (< 1 hour)
```bash
# Restore old strategy
cp app/strategies/buy_hold_trend.py.backup_20260601 app/strategies/buy_hold_trend.py

# Restart trading system
sudo systemctl restart breeze_trading_service
```

#### Option 2: Hybrid Mode (Safety Net)
Keep unified manager but disable automatic trailing:
```python
# In buy_hold_trend.py
position = self.unified_manager.create_position(
    symbol=symbol,
    entry_price=entry_price,
    quantity=quantity,
    position_id=position_id,
    auto_select_strategy=False,  # Force FIXED_FULL_EXIT
)
```

#### Option 3: Partial Rollback (5% Risk Reduction)
Reduce trailing impact while keeping unified code:
```python
# In unified_profit_booking.py
self.config['trailing_stop_pct'] = 0.03  # Increase from 2.0% to 3.0%
self.config['partial_exit_ratio'] = 0.25  # Reduce from 50% to 25% at target
```

### Testing Before Production

**CRITICAL**: Do NOT deploy to live trading directly. Follow this sequence:

1. **Unit Tests** (Local): Run test suite
2. **Paper Trading** (Simulated): 4 weeks with real market data
3. **Production** (Live): Only after validation

---

## Integration Checklist

### Week 1: Setup
- [ ] Create `strategy_config_validator.py` (Step 4)
- [ ] Create `strategy_regime_monitor.py` (Step 5)
- [ ] Create `test_unified_strategy.py` (Step 6)
- [ ] Run unit tests locally
- [ ] Verify backtest results with corrected calculations

### Week 2: Integration
- [ ] Update `buy_hold_trend.py` imports (Phase 3.1)
- [ ] Replace profit manager initialization (Phase 3.2)
- [ ] Update entry handler (Phase 3.3)
- [ ] Update exit checker (Phase 3.4)
- [ ] Add EOD report (Phase 3.5)
- [ ] Run integration tests

### Week 3: Paper Trading
- [ ] Deploy to paper trading environment
- [ ] Monitor for 7 days (validate exits work correctly)
- [ ] Check regime detection (should stay MEAN_REVERTING)
- [ ] Confirm trailing is disallowed (0% of trades should use trailing)
- [ ] Verify P&L tracking

### Week 4: Production Validation
- [ ] Deploy to production (small position size: 50% of normal)
- [ ] Monitor daily reports
- [ ] Watch for regime changes
- [ ] After 7 days, scale to 100% position size
- [ ] Continue monitoring for 4 weeks

### Month 2+: Ongoing
- [ ] Daily regime checks (automated)
- [ ] Weekly statistics review
- [ ] Monthly re-backtesting if conditions change
- [ ] Alert on trailing re-enablement (if trending regime appears)

---

## Key Integration Points Summary

| Component | Before | After | File |
|-----------|--------|-------|------|
| Manager Init | `ProfitBookingManager()` | `UnifiedProfitBookingManager()` | `buy_hold_trend.py` |
| Entry Logic | Manual position creation | Auto regime + strategy selection | `buy_hold_trend.py` |
| Exit Logic | Fixed-only checks | Conditional fixed/trailing checks | `buy_hold_trend.py` |
| Configuration | Hardcoded | Validated with hard stops | `strategy_config_validator.py` |
| Monitoring | Manual review | Automated daily/weekly checks | `strategy_regime_monitor.py` |
| Testing | Manual backtests | Comprehensive test suite | `test_unified_strategy.py` |

---

## Support & Troubleshooting

### Common Issues

**Issue**: "Trailing stops still executing in mean-reverting"
```
Solution: Check regime detection
1. Verify avg_holding_days calculation (should be < 1.0)
2. Run StrategyConfigValidator to catch misconfiguration
3. Check logs: "Market regime detected: mean_reverting"
4. If not showing, check recent_trades has enough data (20+ trades)
```

**Issue**: "Strategy selection always returns FIXED_FULL_EXIT"
```
Solution: Regime must be TRENDING and all 3 conditions pass
1. Increase avg_holding_days above 2.0 to trigger TRENDING
2. Ensure post-target extension exists (max_profit > target * 1.5)
3. Check volatility (max_drawdown < 200%)
```

**Issue**: "Configuration validation throwing errors"
```
Solution: Check hard stops
1. Ensure trailing_enabled is False in mean-reverting
2. Verify config matches TRAILING_STOPS_DESIGN_RULES.md thresholds
3. See strategy_config_validator.py for full validation rules
```

---

## Success Criteria

✅ Integration is successful when:

1. **Regime Detection Works**
   - Correctly identifies mean-reverting (avg_holding < 1.0d)
   - Correctly identifies trending (avg_holding > 2.0d)

2. **Trailing Is Disallowed**
   - 100% of trades use FIXED_FULL_EXIT in mean-reverting regime
   - 0% of trades use PARTIAL_WITH_TRAILING

3. **Performance Maintained**
   - P&L matches backtest: ₹359,850 ± 5%
   - Profit Factor: 1.14 ± 0.05
   - Max Drawdown: -77.91% ± 5%

4. **Production Ready**
   - Configuration validated at startup (no misconfiguration possible)
   - Daily regime monitoring working
   - Alerts trigger when conditions change
   - Paper trading matches production P&L

---

## Next Steps

1. **Immediately**: Create `strategy_config_validator.py` ✅ See Step 4 below
2. **Immediately**: Create `strategy_regime_monitor.py` ✅ See Step 5 below
3. **Immediately**: Create `test_unified_strategy.py` ✅ See Step 6 below
4. **Day 1**: Run all tests locally
5. **Day 2-3**: Update `buy_hold_trend.py` with integration code
6. **Day 4-7**: Paper trading validation
7. **Week 2**: Production deployment with monitoring
