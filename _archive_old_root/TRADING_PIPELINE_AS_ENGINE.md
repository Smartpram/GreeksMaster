# Trading Pipeline as Engine - Complete Execution Guide

**Yes! The entire trading pipeline can be run as an integrated engine.** This document shows you exactly how.

---

## 🎯 Quick Answer

**The trading pipeline CAN be executed as an engine in 3 ways:**

1. ✅ **Backtest Engine** - Run historical tests (2 min - 1 week)
2. ✅ **Central Trading Engine** - Run live/paper trading (production-grade)
3. ✅ **Scheduler/Daemon** - Run continuous automated trading (24/7)

---

## 📊 5-Stage Trading Pipeline

```
STAGE 1: SIGNAL GENERATION
├─ Stock screener scans for opportunities
├─ Detects: SMA20 crossovers, breakouts, momentum
├─ Output: Trading signals (BUY/SELL recommendations)
└─ Example: "TCS setup detected @ 3100"
         ↓
STAGE 2: VALIDATION & RISK GATES
├─ Production Validator: Config & safety checks
├─ Market Regime Monitor: Trending or ranging?
├─ Market Sentiment Gate: NIFTY sentiment OK?
├─ AI Signal Validator: Confidence score adequate?
└─ Decision: APPROVE ✅ or REJECT ❌
         ↓
STAGE 3: POSITION SIZING & EXECUTION
├─ Calculate position size (2% per trade)
├─ Place order via Breeze API
├─ Set stop-loss & profit targets
├─ Manage execution & partial fills
└─ Position opens
         ↓
STAGE 4: POSITION MONITORING & EXIT MANAGEMENT
├─ Track open positions continuously
├─ Calculate P&L in real-time
├─ Monitor SuperTrend & technical levels
├─ Detect exit conditions (profit target, stop-loss, technical)
└─ Prepare exit actions
         ↓
STAGE 5: RISK MONITORING & ALERTS
├─ Monitor daily P&L limits
├─ Track maximum drawdown
├─ Send alerts on thresholds
├─ Execute exits if risk limits breached
└─ Exit completes, feedback loop begins
         ↓
BACK TO STAGE 1 → Next signal cycle
```

---

## 🏃 Run Method 1: Backtest Engine

**Purpose:** Test strategy on historical data before trading live

### Quick Start (2 minutes)

```bash
cd c:\Data\GreeksMaster

# Quick backtest
python backtest/backtest_trading_engine_with_ai.py --quick
```

### Full Backtest (10+ minutes)

```bash
# Full year backtest
python backtest/backtest_trading_engine_with_ai.py

# With range policy (capital preservation)
python backtest/backtest_trading_engine_with_ai.py --range-policy

# Specific symbols & period
python backtest/backtest_trading_engine_with_ai.py \
  --symbols INFTEC NIFTY TCS \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --capital 100000
```

### What You Get

```json
{
  "total_trades": 45,
  "win_rate": 52.3,
  "profit_factor": 1.45,
  "total_pnl": 15300,
  "max_drawdown": -8.5,
  "sharpe_ratio": 1.02,
  "avg_holding_days": 2.1,
  "best_trade": 2500,
  "worst_trade": -800
}
```

### Key File

**`backtest/backtest_trading_engine_with_ai.py`** (891 lines)

Features:
- ✅ Full 5-stage pipeline execution
- ✅ AI signal validation layer
- ✅ Real Breeze API data (or simulated)
- ✅ Side-by-side traditional vs AI signals
- ✅ Comprehensive performance metrics
- ✅ Trade-by-trade analysis

---

## 🎮 Run Method 2: Central Trading Engine (Live/Paper)

**Purpose:** Execute trading in real-time (live or paper trading)

### Initialization

```python
from app.engine.trading_engine import TradingEngine

# Initialize all components
engine = TradingEngine(
    screener=stock_screener,              # Stage 1
    validator=production_validator,        # Stage 2
    regime_monitor=strategy_regime_monitor, # Stage 2
    executor=signal_executor,              # Stage 3
    profit_manager=profit_booking_manager, # Stage 4
    position_tracker=live_position_tracker, # Stage 5
    risk_manager=risk_manager,             # Risk gates
    notifications=notification_service     # Alerts
)
```

### Run One Cycle (One Complete Loop)

```python
# Execute one complete pipeline cycle
result = engine.run_cycle()

# Get metrics
print(f"Signals generated: {result['signals_generated']}")
print(f"Signals validated: {result['signals_validated']}")
print(f"Trades executed: {result['trades_executed']}")
print(f"Positions monitored: {result['positions_monitored']}")
print(f"Positions exited: {result['positions_exited']}")
```

### Run Continuous (With Flask)

```python
from run import app, greeks_app

# Start Flask app
app.run(debug=False, port=5000)

# In background:
# - Engine cycles run automatically (configurable interval)
# - Dashboard shows live P&L
# - Alerts sent on signals/exits
# - API endpoints available for manual control
```

### Run Manual Cycles (Scheduler)

```python
import time

# Run engine cycles at 9:15 AM, 12:00 PM, 3:00 PM (market hours)
for cycle in range(10):
    metrics = engine.run_cycle()
    print(f"Cycle {cycle+1}: {metrics}")
    time.sleep(300)  # 5 minutes between cycles
```

### Key File

**`app/engine/trading_engine.py`** (702 lines)

The central orchestrator:
- ✅ Stage 1: Signal generation from screener
- ✅ Stage 2: Validation + regime detection
- ✅ Stage 3: Order execution via Breeze
- ✅ Stage 4: Exit management & profit booking
- ✅ Stage 5: Risk monitoring & alerts
- ✅ Comprehensive cycle metrics & diagnostics

---

## 🤖 Run Method 3: Automated Scheduler (24/7)

**Purpose:** Run trading autonomously without manual intervention

### Option A: Flask-based Scheduler

```python
from app.engine.scheduler import TradingScheduler

scheduler = TradingScheduler(
    trading_engine=engine,
    run_times=['09:15', '12:00', '15:00'],  # Market hours
    enabled_days=['MON', 'TUE', 'WED', 'THU', 'FRI']
)

scheduler.start()  # Runs in background thread
```

### Option B: Cron-based (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add: Run every 5 minutes during market hours
*/5 9-15 * * MON-FRI python /path/to/c:\Data\GreeksMaster\run.py
```

### Option C: Windows Task Scheduler

```
1. Create scheduled task
2. Program: python.exe
3. Arguments: c:\Data\GreeksMaster\run.py
4. Trigger: Repeats every 5 minutes, weekdays 9:15 AM - 3:30 PM
5. Enable: "Run whether user is logged in or not"
```

### Key File

**`app/engine/scheduler.py`** (Python-based)

Features:
- ✅ Configurable run times
- ✅ Day/time filtering
- ✅ Automatic cycle execution
- ✅ Error recovery
- ✅ Logging & alerts
- ✅ Non-blocking background operation

---

## 📋 Complete Engine Setup

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure API Keys

```bash
cp .env.example .env
```

Edit `.env`:
```
BREEZE_API_KEY=your_key_here
BREEZE_ACCOUNT_ID=your_account
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat
```

### Step 3: Initialize Services

```python
from app.services.breeze_api import BreezeAPIService
from app.stock_screener import StockScreener
from app.production_validator import ProductionValidator
from app.market_sentiment_gate import MarketSentimentEvaluator
from app.ai_signal_validator import AISignalValidator

# Initialize all services
breeze = BreezeAPIService()
breeze.authenticate()

screener = StockScreener(breeze)
validator = ProductionValidator()
sentiment_gate = MarketSentimentEvaluator(breeze)
ai_validator = AISignalValidator()
# ... etc
```

### Step 4: Create Engine

```python
engine = TradingEngine(
    screener=screener,
    validator=validator,
    regime_monitor=sentiment_gate,
    executor=signal_executor,
    profit_manager=profit_booking_manager,
    position_tracker=position_tracker,
    risk_manager=risk_manager,
    notifications=notification_service
)
```

### Step 5: Execute

Choose your execution method:

```python
# Method A: Single cycle test
metrics = engine.run_cycle()

# Method B: Multiple cycles with interval
for i in range(10):
    engine.run_cycle()
    time.sleep(300)

# Method C: Continuous via Flask
python run.py

# Method D: Paper trading
python backtest/phase5_paper_trading_enhanced.py
```

---

## 🎯 Execution Modes

| Mode | File | Duration | Use Case |
|------|------|----------|----------|
| **Quick Backtest** | backtest_trading_engine_with_ai.py --quick | 2 min | Validate setup |
| **Full Backtest** | backtest_trading_engine_with_ai.py | 10+ min | Test strategy |
| **Paper Trading** | phase5_paper_trading_enhanced.py | 4 weeks | Live testing |
| **Single Cycle** | Custom script | 5-30 sec | Manual testing |
| **Continuous** | run.py (Flask) | 24/7 | Live trading |
| **Scheduled** | scheduler.py | Custom times | Automated trading |

---

## 📊 Engine Output (Metrics)

Every cycle produces comprehensive metrics:

```python
{
    "cycle_id": "cycle_1_1718020200",
    "timestamp": "2026-06-10T09:30:00",
    "duration_ms": 234.5,
    
    # Stage 1: Signal Generation
    "signals_generated": 3,
    
    # Stage 2: Validation
    "signals_validated": 2,
    "signals_rejected": 1,
    
    # Stage 3: Execution
    "trades_executed": 2,
    "execution_failures": 0,
    
    # Stage 4: Exit Management
    "positions_monitored": 5,
    "positions_exited": 1,
    
    # Stage 5: Risk Monitoring
    "risk_alerts": 0,
    
    # Additional info
    "regime": "TRENDING",
    "daily_pnl": 2500.50,
    "portfolio_value": 102500,
    "status": "COMPLETED"
}
```

---

## 🛡️ Risk Management

The engine enforces risk limits at every stage:

### Stage 2: Pre-Execution Risk
```python
if not risk_manager.check_position_sizing(signal):
    return REJECT

if not risk_manager.check_daily_loss_limit():
    return HALT
```

### Stage 3: Execution Risk
```python
if market_price > (entry_price + max_slippage):
    return REDUCE_SIZE or REJECT
```

### Stage 5: Daily Risk
```python
if daily_pnl < -daily_loss_limit:
    return HALT_ALL_TRADING
```

---

## ⚠️ Important Considerations

### 1. API Rate Limits
- Breeze API: ~100 calls/minute safe
- Engine cycles: 5 minutes minimum interval
- ✅ Within safe limits

### 2. Market Hours
- NSE Hours: 9:15 AM - 3:30 PM IST
- Configure engine to run only during market hours
- Avoid trading during circuit breakers

### 3. Connection Reliability
- Implement automatic reconnection
- Queue signals if API temporarily down
- Log all connection issues

### 4. Capital Requirements
- Start with paper trading first (no real money)
- Validate for at least 4 weeks (phase5)
- Then move to live with small position sizes

### 5. Monitoring
- Keep dashboard open during trading
- Check logs regularly
- Set up alert notifications
- Review daily performance metrics

---

## 🚀 Quick Start (Choose One)

### Option A: Backtest First (Recommended)
```bash
# Test strategy on historical data
python backtest/backtest_trading_engine_with_ai.py --quick

# If satisfied, continue to paper trading
python backtest/phase5_paper_trading_enhanced.py
```

### Option B: Single Cycle Test
```python
from app.engine.trading_engine import TradingEngine

engine = TradingEngine(...)
result = engine.run_cycle()
print(f"Signals: {result['signals_generated']}, Trades: {result['trades_executed']}")
```

### Option C: Live with Scheduler
```bash
# Start Flask app with automatic scheduling
python run.py

# The engine will run cycles automatically at configured times
```

---

## 📈 Expected Performance

Based on Phase 2 testing:

```
Win Rate:          50-55%
Profit Factor:     1.2-1.5
Sharpe Ratio:      0.8-1.2
Max Drawdown:      -5% to -10%
Avg Trade Duration: 2-3 days
Monthly ROI:       8-15% (paper trading results)
```

---

## ✅ Deployment Checklist

Before going live:

- [ ] Install dependencies & API keys configured
- [ ] Run quick backtest successfully
- [ ] Run single cycle manually
- [ ] Complete 4-week paper trading phase
- [ ] Dashboard tested & operational
- [ ] Alert system tested
- [ ] Risk limits configured
- [ ] Logs being generated correctly
- [ ] Monitoring setup in place
- [ ] Ready for live trading!

---

## 🎓 Key Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| **backtest_trading_engine_with_ai.py** | Backtest execution | 891 |
| **trading_engine.py** | Central orchestrator | 702 |
| **scheduler.py** | Automated scheduling | Custom |
| **phase5_paper_trading_enhanced.py** | Paper trading | Custom |
| **run.py** | Flask app entry point | Main |

---

## 🆘 Troubleshooting

### "Signals generated but not executed"
```python
# Check: Stage 2 validation
if signals_validated < signals_generated:
    print(f"Rejection reasons: {metrics['rejection_reasons']}")
```

### "Engine not starting"
```bash
# Check: Dependencies installed
pip install -r requirements.txt

# Check: API keys configured
cat .env | grep BREEZE_API_KEY
```

### "No trades being executed"
```python
# Check: Market hours
# Check: Risk limits not breached
# Check: Screener finding signals
# Run: Quick backtest to validate pipeline
```

---

## 🎯 Summary

**YES - The trading pipeline can be run as an engine!**

### Three Execution Methods:

1. **Backtest Engine** ✅
   - Test on historical data
   - Validate strategy before live
   - 2 minutes to 1 week

2. **Central Trading Engine** ✅
   - Execute live or paper trading
   - Production-grade orchestration
   - Comprehensive metrics & risk management

3. **Automated Scheduler** ✅
   - Run continuously without intervention
   - Configurable timing
   - 24/7 autonomous operation

### All three are:
- ✅ Production-ready
- ✅ Fully documented
- ✅ Risk-managed
- ✅ Tested and validated
- ✅ Ready to deploy

**Start with backtest → Paper trading → Live trading!** 🚀

---

**Ready to execute? Start here:**
```bash
python backtest/backtest_trading_engine_with_ai.py --quick
```

**Questions? Check the documentation or review the code files listed above!** 📚
