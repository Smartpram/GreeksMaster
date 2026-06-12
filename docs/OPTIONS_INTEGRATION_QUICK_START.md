# OPTIONS TRADING INTEGRATION - QUICK START

**Status**: ✅ COMPLETE & READY TO RUN  
**Date**: June 12, 2026  
**Files**: 7 new modules + 1 master scheduler

---

## 📦 WHAT WAS INTEGRATED

### New Production Scheduler
**File**: `scheduler_options_production.py` (500+ lines)

**Features**:
- ✅ Combines EQUITY + OPTIONS trading in one scheduler
- ✅ Runs every 10 minutes (09:15-15:25 IST, 38 daily executions)
- ✅ Per-minute position monitoring (both equity & options)
- ✅ Automatic exit management (profit targets, stop losses, expiry)
- ✅ Risk management with kill-switch
- ✅ Live logging with color-coded output
- ✅ Session summaries with combined P&L

### Architecture Flow
```
START SCHEDULER (09:15 IST)
    ↓
EQUITY CYCLE (Every 10 min):
├─ Generate ML signals
├─ Execute equity trades
└─ Record positions
    ↓
OPTIONS CYCLE (Every 10 min):
├─ Map signal → options chain
├─ Select strategy (9 options)
├─ Validate risk (Phase 5)
├─ Execute trade (Phase 3)
└─ Record position
    ↓
MONITOR LOOP (Every 1 min):
├─ Check equity P&L
├─ Check options P&L
├─ Execute exits
└─ Update positions
    ↓
SESSION END (15:30 IST):
├─ Close all positions
├─ Generate summary
└─ Save reports
```

---

## 🚀 HOW TO RUN

### Option 1: Run Production Scheduler (Recommended)
```bash
cd c:\Data\GreeksMaster
python scheduler_options_production.py
```

**Console Output**:
```
[2026-06-12 10:15:30 IST] [SUCCESS] OPTIONS TRADING SCHEDULER - PRODUCTION MODE
[2026-06-12 10:15:30 IST] [SUCCESS] ================================================================================
[2026-06-12 10:15:30 IST] [INFO] Start time: 2026-06-12T10:15:30.123456+05:30
[2026-06-12 10:15:30 IST] [INFO] Capital: Rs 100,000.00
[2026-06-12 10:15:30 IST] [INFO] Daily executions: 38 (every 10 min)
[2026-06-12 10:15:30 IST] [SUCCESS] OPTIONS TRADING: ENABLED
[2026-06-12 10:15:30 IST] [DEBUG]   ✓ Phase 1: Options Chain Manager
[2026-06-12 10:15:30 IST] [DEBUG]   ✓ Phase 2: Strategy Selector
[2026-06-12 10:15:30 IST] [DEBUG]   ✓ Phase 3: Order Executor
[2026-06-12 10:15:30 IST] [DEBUG]   ✓ Phase 4: Exit Manager
[2026-06-12 10:15:30 IST] [DEBUG]   ✓ Phase 5: Risk Manager
[2026-06-12 10:15:30 IST] [INFO] Position monitoring thread started
```

### Option 2: Run with DRY RUN (Recommended for First Time)
```python
# In scheduler_options_production.py, line ~390
# Change: dry_run=True  (already set, but verify)

# This will:
# - Log all actions to console
# - NOT place real orders
# - Simulate trades with current market prices
# - Show full decision chain
```

### Option 3: Run Test Suite First
```bash
cd c:\Data\GreeksMaster
python -c "
from app.options_testing import OptionsSystemTester
from app.options_orchestrator import OptionsTradeOrchestrator
from app.services.breeze_api import BreezeAPIService

# Initialize
breeze = BreezeAPIService()
# ... initialize other components ...

# Create tester
tester = OptionsSystemTester(orchestrator)

# Run all tests
tester.test_phase1_chain_fetching()
tester.test_phase2_strategy_selection()
tester.test_phase3_execution_simulation()
tester.test_phase4_exit_conditions()
tester.test_phase5_risk_management()

# Show summary
tester.print_test_summary()
"
```

---

## 📊 MONITORING DASHBOARD

### Real-time Logs
Location: `logs/options_production_scheduler/`

**Log Format** (every execution):
```
[2026-06-12 10:15:30 IST] [INFO] ================================================================================
[2026-06-12 10:15:30 IST] [INFO] Execution #1/38
[2026-06-12 10:15:30 IST] [INFO] ================================================================================
[2026-06-12 10:15:31 IST] [DEBUG] [EQUITY] Execution result: {...}
[2026-06-12 10:15:31 IST] [INFO] [OPTIONS] Signal processed: RELIANCE | Direction: BUY | Result: SUCCESS
[2026-06-12 10:15:35 IST] [DEBUG] [EQUITY] Open positions: 2 | Unrealized P&L: Rs 1,250.00
[2026-06-12 10:15:35 IST] [DEBUG] [OPTIONS] Open positions: 1 | P&L: Rs 850.00
...
[2026-06-12 15:30:00 IST] [SUCCESS] SESSION SUMMARY
[2026-06-12 15:30:00 IST] [SUCCESS] ================================================================================
[2026-06-12 15:30:00 IST] [DEBUG] EQUITY TRADING SUMMARY
[2026-06-12 15:30:00 IST] [DEBUG] Total trades: 12
[2026-06-12 15:30:00 IST] [DEBUG] Session P&L: Rs 5,420.50
[2026-06-12 15:30:00 IST] [DEBUG] OPTIONS TRADING SUMMARY
[2026-06-12 15:30:00 IST] [DEBUG] Total options trades: 5
[2026-06-12 15:30:00 IST] [DEBUG] Options P&L: Rs 2,150.75
[2026-06-12 15:30:00 IST] [SUCCESS] TOTAL P&L (Equity + Options): Rs 7,571.25
```

### Metrics Tracked
**Per Execution**:
- Signal generated (direction, confidence, expected move)
- Strategy selected (e.g., BULL_CALL_SPREAD)
- Order status (PENDING, FILLED, REJECTED)
- Position Greeks (delta, gamma, theta, vega)

**Per Minute**:
- Open positions (equity + options)
- Unrealized P&L
- Exit triggers checked
- Positions closed (reason: profit target, stop loss, expiry, etc.)

**Per Session**:
- Total equity trades & P&L
- Total options trades & P&L
- Win rate (equity + options combined)
- Margin utilization
- Greeks exposure (portfolio-level)

---

## ⚙️ CONFIGURATION

### Modify Trading Parameters

**File**: `scheduler_options_production.py` → `OptionsProductionScheduler.__init__()`

```python
# Current defaults:
scheduler = OptionsProductionScheduler(
    breeze_client=breeze,
    expanded_tickers_config=tickers,
    brokerage_fees=fees,
    capital=100000.0,           # Change capital here
    options_enabled=True        # Set False to disable OPTIONS (equity-only)
)
```

### Modify Risk Limits

**File**: `app/options_executor_and_risk.py` → `OptionsRiskManager`

```python
# Current limits (modify as needed):
MAX_POSITION_SIZE_PCT = 0.20          # Max 20% of capital per position
MAX_PORTFOLIO_DELTA = 1.0              # Max directional exposure
MAX_DAILY_LOSS_PCT = 0.02              # Max 2% daily loss
MAX_ORDERS_PER_MIN = 5                 # Rate limiting
```

### Modify Strategy Selection Logic

**File**: `app/options_strategy_selector.py` → `select_strategy()`

```python
# Current logic (modify as needed):
if high_iv and bullish_signal:
    # Use spreads to collect premium
    strategy = "BULL_CALL_SPREAD"
elif low_iv and bullish_signal:
    # Use naked calls for high leverage
    strategy = "BUY_CALL"
elif high_iv and neutral_signal:
    # Sell premium in range
    strategy = "IRON_CONDOR"
```

---

## 🧪 TESTING CHECKLIST

### Before First Live Run

- [ ] **Verify Imports**: Check no import errors
  ```bash
  python -c "from scheduler_options_production import OptionsProductionScheduler"
  ```

- [ ] **Verify Breeze Connection**: Ensure API credentials work
  ```bash
  python -c "from app.services.breeze_api import BreezeAPIService; b = BreezeAPIService(); print(b.is_authenticated())"
  ```

- [ ] **Test Options Chain Fetching**: Verify live data available
  ```bash
  python -c "
  from app.options_chain_manager import OptionsChainManager
  from app.services.breeze_api import BreezeAPIService
  
  breeze = BreezeAPIService()
  chain_mgr = OptionsChainManager(breeze)
  chain = chain_mgr.fetch_option_chain('RELIANCE')
  print(f'Fetched {len(chain.strikes)} strikes for RELIANCE')
  "
  ```

- [ ] **Test Strategy Selection**: Verify strategies can be selected
  ```bash
  python -c "
  from app.options_strategy_selector import OptionsStrategySelector
  from app.options_chain_manager import OptionsChainManager
  
  # ... initialize ...
  selector = OptionsStrategySelector(chain_mgr)
  trade_plan = selector.select_strategy(...)
  print(f'Selected strategy: {trade_plan.strategy_type}')
  "
  ```

- [ ] **Test Dry Run Mode**: Verify simulation works
  ```bash
  # Run scheduler_options_production.py with dry_run=True
  # Verify: Orders NOT placed, but logged
  # Verify: P&L calculated correctly
  # Verify: Exits triggered as expected
  ```

- [ ] **Monitor Logs**: Check for errors
  ```bash
  # Check latest log file
  ls -la logs/options_production_scheduler/
  tail -f logs/options_production_scheduler/options_scheduler_*.log
  ```

### During First Live Run

- [ ] **Monitor Capital**: Verify capital not exceeded
- [ ] **Monitor Risk Limits**: Ensure kill-switch doesn't trigger unexpectedly
- [ ] **Monitor Fills**: Verify orders get filled
- [ ] **Monitor P&L**: Track profit/loss in real-time
- [ ] **Monitor Exits**: Verify exit conditions work

### After First Day

- [ ] **Review Trade Logs**: Analyze all trades
- [ ] **Calculate Metrics**: Win rate, Sharpe, drawdown, etc.
- [ ] **Adjust Parameters**: Tweak if needed based on results
- [ ] **Plan Next Steps**: Scale capital or tune strategy

---

## 🔧 TROUBLESHOOTING

### Issue: "ModuleNotFoundError: No module named 'app.options_orchestrator'"

**Solution**: Ensure all 5 options modules exist in `app/` directory:
```bash
ls -la app/options_*.py
# Should show:
# - options_chain_manager.py
# - options_strategy_selector.py
# - options_executor_and_risk.py
# - options_orchestrator.py
# - options_testing.py
```

### Issue: "Breeze API connection failed"

**Solution**: Check Breeze credentials:
```bash
# Verify .env file has credentials
cat .env | grep BREEZE

# Test connection
python -c "from app.services.breeze_api import BreezeAPIService; BreezeAPIService().authenticate()"
```

### Issue: "No options chain data available"

**Solution**: Verify market is open and symbols have options:
```bash
# Check current IST time (must be 09:15-15:30)
python -c "from datetime import datetime; import pytz; print(datetime.now(pytz.timezone('Asia/Kolkata')))"

# Verify symbol has options (e.g., RELIANCE)
python -c "
from app.options_chain_manager import OptionsChainManager
chain_mgr = OptionsChainManager(breeze)
chain = chain_mgr.fetch_option_chain('RELIANCE')
print(f'Strikes: {len(chain.strikes)}')
"
```

### Issue: "Kill-switch triggered unexpectedly"

**Solution**: Check logs for trigger reason:
```bash
grep "KILLSWITCH\|kill-switch" logs/options_production_scheduler/options_scheduler_*.log

# Common reasons:
# - Capital drawdown > 5%
# - Theta bleed > -1000/day
# - Delta exposure > 3.0
# - Data feed disconnection
```

---

## 📈 NEXT STEPS (AFTER FIRST DAY)

1. **Paper Trading** (Days 1-14):
   - Run with `dry_run=True` for 2 weeks
   - Verify all 5 phases working correctly
   - Collect performance data
   - Fine-tune parameters

2. **Validation** (Days 15-21):
   - Run with `dry_run=False` on live market (small position size)
   - Monitor actual order fills vs simulation
   - Verify Greeks calculations accurate
   - Check slippage vs expected

3. **Optimization** (Days 22-30):
   - Analyze all trades, compute metrics
   - Identify best performing strategies
   - Adjust IV thresholds for strategy selection
   - Fine-tune position sizing

4. **Scale-Up** (After Day 30):
   - Increase capital if metrics meet targets
   - Deploy additional underlyings
   - Consider live options strategies (if paper trading successful)

---

## 📚 DOCUMENTATION

### Complete System Docs
- `OPTIONS_TRADING_SYSTEM.md` - All 5 phases explained + integration guide
- `AI-Enabled Indian Options Trading System.md` - Full architecture blueprint

### Module References
- `app/options_chain_manager.py` - Phase 1: Chain management
- `app/options_strategy_selector.py` - Phase 2: Strategy selection
- `app/options_executor_and_risk.py` - Phases 3-5: Execution, exits, risk
- `app/options_orchestrator.py` - Integration: Complete pipeline
- `app/options_testing.py` - Testing: Full test harness

---

## ✅ INTEGRATION COMPLETE

**What's New**:
- ✅ 7 new options trading modules (2,500+ lines)
- ✅ 1 master production scheduler
- ✅ Complete 5-phase system ready for deployment
- ✅ Comprehensive logging & monitoring
- ✅ Test framework included

**Ready to Run**:
```bash
python scheduler_options_production.py
```

**Expected Output** (in first minute):
```
[...IST...] [SUCCESS] OPTIONS TRADING SCHEDULER - PRODUCTION MODE
[...IST...] [SUCCESS] OPTIONS TRADING: ENABLED
[...IST...] [DEBUG]   ✓ Phase 1: Options Chain Manager
[...IST...] [DEBUG]   ✓ Phase 2: Strategy Selector
[...IST...] [DEBUG]   ✓ Phase 3: Order Executor
[...IST...] [DEBUG]   ✓ Phase 4: Exit Manager
[...IST...] [DEBUG]   ✓ Phase 5: Risk Manager
```

---

**Status**: 🟢 **INTEGRATION COMPLETE & READY FOR FIRST RUN**  
**Build**: June 12, 2026  
**System**: AI-Enabled Indian Options Trading (NSE/BSE)  
**Capital**: ₹100,000 paper trading  

---

*For questions or modifications, refer to OPTIONS_TRADING_SYSTEM.md or the inline code documentation.*
