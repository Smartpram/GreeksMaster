# 🚀 FRAMEWORK EXECUTION SEQUENCE & SCHEDULER

**Date:** June 9, 2026  
**Purpose:** Define how to execute the complete trading framework in sequence  
**Status:** Ready for implementation

---

## 📊 System Architecture (Execution Flow)

```
┌─────────────────────────────────────────────────────────────────┐
│             GREEKSMASTER FRAMEWORK - EXECUTION PIPELINE          │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ PHASE 1: PRE-MARKET PREPARATION (5:30 AM - 8:30 AM IST)            │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                      │
│  5:30 AM ┌─ Load Historical Data                                  │
│          ├─ Refresh Option Chains                                 │
│          ├─ Calculate Greeks (latest snapshot)                    │
│          └─ Run Regime Detection (market classification)          │
│                    ↓                                               │
│  6:00 AM ┌─ Validate Production Configuration                    │
│          ├─ Check API Connectivity (Breeze)                      │
│          ├─ Verify Capital Adequacy                              │
│          ├─ Reset Daily Counters (P&L, trades)                   │
│          └─ Alert: System ready status                           │
│                    ↓                                               │
│  6:30 AM ┌─ Pre-market Backtests (Optional)                      │
│          ├─ Run screener backtest on latest data                 │
│          ├─ Validate parameters                                  │
│          └─ Confidence check before market open                  │
│                    ↓                                               │
│  8:30 AM └─ READY FOR MARKET OPEN                                │
│          Status: ✅ All systems ready                             │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│ PHASE 2: INTRADAY TRADING (9:15 AM - 3:30 PM IST)                   │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                      │
│  9:15 AM ┌─ MARKET OPEN - Start Screener                         │
│          │                                                         │
│  ┌──────────────────────────────────────────────┐               │
│  │ CONTINUOUS LOOP (Every 5 minutes)            │               │
│  │ ──────────────────────────────────────────── │               │
│  │                                              │               │
│  │ 1. Fetch latest OHLCV data                   │               │
│  │ 2. Calculate indicators (SMA20, RSI, ATR)    │               │
│  │ 3. Run screener logic                        │               │
│  │ 4. Generate signals (if conditions met)      │               │
│  │                                              │               │
│  │    ↓ If Signal Generated                     │               │
│  │    ┌──────────────────────────────────────┐ │               │
│  │    │ VALIDATION & GUARDRAILS              │ │               │
│  │    │ ─────────────────────────────────── │ │               │
│  │    │ • Check production config            │ │               │
│  │    │ • Verify market regime               │ │               │
│  │    │ • Assess sentiment (NIFTY)           │ │               │
│  │    │ • AI signal confidence               │ │               │
│  │    │ • Decision: APPROVE / REJECT         │ │               │
│  │    └──────────────────────────────────────┘ │               │
│  │           ↓ APPROVED                         │               │
│  │    ┌──────────────────────────────────────┐ │               │
│  │    │ TRADE EXECUTION                      │ │               │
│  │    │ ─────────────────────────────────── │ │               │
│  │    │ • Calculate position size             │ │               │
│  │    │ • Place market order (Breeze API)     │ │               │
│  │    │ • Set stop-loss                       │ │               │
│  │    │ • Set profit target                   │ │               │
│  │    │ • Record entry                        │ │               │
│  │    │ • Position = OPEN                     │ │               │
│  │    └──────────────────────────────────────┘ │               │
│  │           ↓                                   │               │
│  │    ┌──────────────────────────────────────┐ │               │
│  │    │ POSITION MONITORING (Continuous)     │ │               │
│  │    │ ─────────────────────────────────── │ │               │
│  │    │ For each open position:               │ │               │
│  │    │ • Get real-time price                │ │               │
│  │    │ • Calculate current P&L               │ │               │
│  │    │ • Call Trade Management Layer         │ │               │
│  │    │ • Get exit recommendation             │ │               │
│  │    │                                       │ │               │
│  │    │ Trade Management evaluates:           │ │               │
│  │    │ • SuperTrend trend                    │ │               │
│  │    │ • 4-axis context scores               │ │               │
│  │    │ • Historical pivot patterns           │ │               │
│  │    │ → Recommendation: HOLD/PARTIAL/FULL  │ │               │
│  │    │                                       │ │               │
│  │    │ Exit Actions:                         │ │               │
│  │    │ ├─ FULL_EXIT: Close entire position  │ │               │
│  │    │ ├─ PARTIAL_EXIT: Scale out 25-50%    │ │               │
│  │    │ ├─ TIGHTEN_STOP: Move stop up        │ │               │
│  │    │ └─ HOLD: Wait & monitor              │ │               │
│  │    │                                       │ │               │
│  │    │ Auto-triggers:                        │ │               │
│  │    │ ├─ Profit target hit → Auto exit     │ │               │
│  │    │ ├─ Stop loss hit → Auto close        │ │               │
│  │    │ └─ Max 10 bars → Force exit (safety) │ │               │
│  │    └──────────────────────────────────────┘ │               │
│  │                                              │               │
│  └──────────────────────────────────────────────┘               │
│           Loop continues every 5 minutes                        │
│                    ↓                                             │
│  Every 30 minutes:                                              │
│  ├─ Update daily P&L tracking                                  │
│  ├─ Check daily loss limit (2%)                                │
│  ├─ Update portfolio metrics                                   │
│  └─ Send alerts if limits exceeded                             │
│                    ↓                                             │
│  Every 4 hours:                                                 │
│  ├─ Re-evaluate market regime                                  │
│  ├─ Update strategy selection                                  │
│  └─ Alert if regime has shifted                                │
│                    ↓                                             │
│  3:30 PM ├─ MARKET CLOSE                                       │
│          ├─ Close any remaining positions                      │
│          ├─ Generate end-of-day report                         │
│          └─ Calculate daily metrics                            │
│                                                                 │
└──────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│ PHASE 3: POST-MARKET & ANALYSIS (3:30 PM - 6:00 PM IST)             │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                      │
│  3:30 PM ┌─ End-of-Day Trade Analysis                            │
│          ├─ Calculate P&L per trade                              │
│          ├─ Update trade history                                 │
│          ├─ Calculate daily metrics:                             │
│          │  ├─ Total trades today                                │
│          │  ├─ Winners vs losers                                 │
│          │  ├─ Daily P&L                                         │
│          │  ├─ Win rate                                          │
│          │  └─ Max drawdown today                                │
│          └─ Risk Assessment                                      │
│                    ↓                                             │
│  4:00 PM ┌─ Portfolio Health Check                              │
│          ├─ Verify all positions closed                          │
│          ├─ Check daily loss limit (2%)                          │
│          │  ├─ If hit → Alert + halt tomorrow's trading         │
│          │  └─ If OK → Continue normally                        │
│          ├─ Update max drawdown against historical peak          │
│          └─ Risk feedback for tomorrow                           │
│                    ↓                                             │
│  5:00 PM ┌─ Reporting & Notifications                           │
│          ├─ Generate daily report:                              │
│          │  ├─ Trades executed                                  │
│          │  ├─ P&L breakdown                                    │
│          │  ├─ Risk metrics                                     │
│          │  └─ Regime assessment                                │
│          ├─ Email report to trader                              │
│          ├─ Send Telegram alerts (if enabled)                   │
│          └─ Dashboard update                                    │
│                    ↓                                             │
│  5:30 PM ├─ Paper Trading Signal (If scheduled)                │
│          │  └─ Execute Phase 5 paper trading snapshot           │
│          │     (If in 4-week validation period)                 │
│          └─ Log paper trading results                           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│ PHASE 4: OVERNIGHT & NEXT-DAY PREP (6:00 PM - 5:30 AM IST)          │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                      │
│  6:00 PM ┌─ Data Collection & Updates                            │
│          ├─ Fetch historical data for next day                   │
│          ├─ Download latest option chains                        │
│          ├─ Update Greeks cache                                  │
│          └─ Run overnight backtests (optional)                   │
│                    ↓                                             │
│  Weekly (Every Monday):                                          │
│  ├─ Generate weekly performance report                           │
│  ├─ Strategy parameter review                                   │
│  ├─ Portfolio rebalancing check                                 │
│  └─ Risk limit reassessment                                     │
│                    ↓                                             │
│  Monthly (1st of each month):                                    │
│  ├─ Full month review                                           │
│  ├─ Performance vs targets                                      │
│  ├─ Strategy effectiveness analysis                             │
│  ├─ Parameter optimization                                      │
│  └─ Risk metrics and learning                                   │
│                    ↓                                             │
│  5:30 AM ├─ Back to PHASE 1 (Pre-market Prep)                  │
│          └─ Cycle repeats                                        │
│                                                                  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## ⏰ Execution Schedule (Daily)

| Time | Activity | Duration | Owner | Status |
|------|----------|----------|-------|--------|
| **5:30 AM** | Pre-market data load | 10 min | Auto | ✅ Ready |
| **6:00 AM** | System validation | 10 min | Auto | ✅ Ready |
| **6:30 AM** | Optional backtest | 15 min | Optional | ✅ Ready |
| **8:30 AM** | Final readiness check | 5 min | Auto | ✅ Ready |
| **9:15 AM** | **MARKET OPEN** | - | - | ✅ Ready |
| **9:15 - 3:30 PM** | **INTRADAY LOOP** (Every 5 min) | - | Auto | ✅ Ready |
| **Every 30 min** | P&L tracking, alerts | 2 min | Auto | ✅ Ready |
| **Every 4 hours** | Regime re-assessment | 5 min | Auto | ✅ Ready |
| **3:30 PM** | **MARKET CLOSE** | - | - | ✅ Ready |
| **3:30 - 4:00 PM** | End-of-day analysis | 30 min | Auto | ✅ Ready |
| **4:00 - 5:00 PM** | Risk assessment, reporting | 30 min | Auto | ✅ Ready |
| **5:15 PM** | **Paper Trading Signal** | 5 min | Auto | ✅ Ready (Phase 5) |
| **5:30 PM** | Overnight prep | 30 min | Auto | ✅ Ready |
| **Weekly** | Weekly review (Monday) | 30 min | Manual | ⏳ To implement |
| **Monthly** | Monthly review (1st) | 1 hour | Manual | ⏳ To implement |

---

## 🔧 Implementation: Scheduler Setup

### Option 1: APScheduler (Python - Recommended for local)

**File:** `app/scheduler.py`

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)

def create_scheduler():
    """Create and configure scheduler for GreeksMaster"""
    scheduler = BackgroundScheduler()
    
    # PHASE 1: Pre-market (5:30 AM)
    scheduler.add_job(
        load_historical_data,
        CronTrigger(hour=5, minute=30, day_of_week='mon-fri'),
        id='premarket_data_load',
        name='Pre-market data load'
    )
    
    # PHASE 1: System validation (6:00 AM)
    scheduler.add_job(
        validate_production_config,
        CronTrigger(hour=6, minute=0, day_of_week='mon-fri'),
        id='system_validation',
        name='System validation'
    )
    
    # PHASE 2: Screener loop (Every 5 minutes, 9:15 AM - 3:30 PM)
    scheduler.add_job(
        run_screener_loop,
        CronTrigger(minute='*/5', hour='9-15', day_of_week='mon-fri'),
        id='screener_loop',
        name='Screener loop'
    )
    
    # PHASE 2: Position monitoring (Every 5 minutes, 9:15 AM - 3:30 PM)
    scheduler.add_job(
        monitor_open_positions,
        CronTrigger(minute='*/5', hour='9-15', day_of_week='mon-fri'),
        id='position_monitoring',
        name='Position monitoring'
    )
    
    # PHASE 2: Regime check (Every 4 hours)
    scheduler.add_job(
        update_market_regime,
        CronTrigger(minute=0, hour='9,13', day_of_week='mon-fri'),
        id='regime_check',
        name='Market regime check'
    )
    
    # PHASE 3: End-of-day analysis (3:30 PM)
    scheduler.add_job(
        end_of_day_analysis,
        CronTrigger(hour=15, minute=30, day_of_week='mon-fri'),
        id='eod_analysis',
        name='End-of-day analysis'
    )
    
    # PHASE 3: Paper trading signal (5:15 PM, if in Phase 5)
    scheduler.add_job(
        phase5_paper_trading_signal,
        CronTrigger(hour=17, minute=15, day_of_week='mon-fri'),
        id='paper_trading_signal',
        name='Phase 5 paper trading'
    )
    
    # Weekly review (Mondays, 6:00 PM)
    scheduler.add_job(
        weekly_review,
        CronTrigger(day_of_week='mon', hour=18, minute=0),
        id='weekly_review',
        name='Weekly review'
    )
    
    # Monthly review (1st of month, 6:00 PM)
    scheduler.add_job(
        monthly_review,
        CronTrigger(day=1, hour=18, minute=0),
        id='monthly_review',
        name='Monthly review'
    )
    
    scheduler.start()
    return scheduler
```

**Usage:**
```python
# In app/app.py
scheduler = create_scheduler()

@app.before_first_request
def before_first_request():
    logger.info("Scheduler started")
```

---

### Option 2: Cron (Linux/Mac - Production)

**File:** `/etc/cron.d/greeksmaster`

```cron
# GreeksMaster Trading Framework Schedule

# PHASE 1: Pre-market (5:30 AM)
30 5 * * 1-5 /usr/bin/python3 /opt/greeksmaster/tasks/premarket_prep.py

# PHASE 1: System validation (6:00 AM)
0 6 * * 1-5 /usr/bin/python3 /opt/greeksmaster/tasks/system_validation.py

# PHASE 2: Screener loop (Every 5 minutes, 9:15 AM - 3:30 PM)
*/5 9-15 * * 1-5 /usr/bin/python3 /opt/greeksmaster/tasks/screener_loop.py

# PHASE 2: Position monitoring (Every 5 minutes, 9:15 AM - 3:30 PM)
*/5 9-15 * * 1-5 /usr/bin/python3 /opt/greeksmaster/tasks/position_monitor.py

# PHASE 2: Regime check (Every 4 hours: 9 AM, 1 PM)
0 9,13 * * 1-5 /usr/bin/python3 /opt/greeksmaster/tasks/regime_check.py

# PHASE 3: End-of-day analysis (3:30 PM)
30 15 * * 1-5 /usr/bin/python3 /opt/greeksmaster/tasks/eod_analysis.py

# PHASE 3: Paper trading signal (5:15 PM, Phase 5)
15 17 * * 1-5 /usr/bin/python3 /opt/greeksmaster/tasks/phase5_trading.py

# Weekly review (Monday, 6 PM)
0 18 * * 1 /usr/bin/python3 /opt/greeksmaster/tasks/weekly_review.py

# Monthly review (1st of month, 6 PM)
0 18 1 * * /usr/bin/python3 /opt/greeksmaster/tasks/monthly_review.py
```

---

### Option 3: Windows Task Scheduler (Windows - Production)

```powershell
# Create scheduled tasks for GreeksMaster

# PHASE 1: Pre-market (5:30 AM)
$action = New-ScheduledTaskAction -Execute "python" -Argument "premarket_prep.py"
$trigger = New-ScheduledTaskTrigger -Daily -At "05:30"
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U
Register-ScheduledTask -TaskName "GreeksMaster-PreMarket" -Action $action -Trigger $trigger -Principal $principal

# PHASE 2: Screener loop (Every 5 minutes, 9:15 AM - 3:30 PM)
$action = New-ScheduledTaskAction -Execute "python" -Argument "screener_loop.py"
$trigger = New-ScheduledTaskTrigger -Once -At "09:15" -RepetitionInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "GreeksMaster-ScreenerLoop" -Action $action -Trigger $trigger

# ... etc for other tasks
```

---

## 📋 Task Definitions

### Pre-Market Prep (5:30 AM)

```python
# tasks/premarket_prep.py
def load_historical_data():
    """Load latest OHLCV data for all symbols"""
    symbols = ["TCS", "WIPRO", "RELIND", "MARUTI", "INFTEC"]
    
    for symbol in symbols:
        df = load_data_from_api(symbol, days=60)
        cache_data(symbol, df)
    
    logger.info("Historical data loaded")
```

### Intraday Screener Loop (Every 5 min, 9:15 AM - 3:30 PM)

```python
# tasks/screener_loop.py
def run_screener_loop():
    """Run screener every 5 minutes"""
    symbols = ["TCS", "WIPRO", "RELIND", "MARUTI", "INFTEC"]
    
    for symbol in symbols:
        df = get_latest_data(symbol)
        signal = screener.analyze(df)
        
        if signal:
            validate_and_execute(signal)
    
    logger.info(f"Screener loop completed: {len(signals)} signals generated")
```

### Position Monitoring Loop (Every 5 min, 9:15 AM - 3:30 PM)

```python
# tasks/position_monitor.py
def monitor_open_positions():
    """Monitor all open positions and apply Trade Management"""
    positions = get_open_positions()
    
    for position in positions:
        # Get latest price
        current_price = get_current_price(position.symbol)
        pnl_pct = ((current_price - position.entry) / position.entry) * 100
        
        # Get Trade Management recommendation
        mgmt_report = trade_manager.analyze_trade(
            df=get_latest_data(position.symbol),
            symbol=position.symbol,
            pnl_pct=pnl_pct,
            entry_price=position.entry
        )
        
        # Execute recommendation
        action = mgmt_report['decision']['exit_action']
        
        if action == "FULL_EXIT":
            close_position(position, current_price, mgmt_report['reason'])
        elif action == "PARTIAL_EXIT":
            scale = mgmt_report['scale_pct'] / 100
            scale_out_position(position, scale, current_price)
        elif action == "TIGHTEN_STOP":
            new_stop = mgmt_report['new_stop']
            update_stop_loss(position, new_stop)
    
    logger.info(f"Monitored {len(positions)} positions")
```

### End-of-Day Analysis (3:30 PM)

```python
# tasks/eod_analysis.py
def end_of_day_analysis():
    """Generate daily analysis and close remaining positions"""
    
    # Close any remaining positions
    close_remaining_positions()
    
    # Calculate daily metrics
    trades_today = get_trades_by_date(date.today())
    
    metrics = {
        'total_trades': len(trades_today),
        'winning_trades': sum(1 for t in trades_today if t.pnl > 0),
        'losing_trades': sum(1 for t in trades_today if t.pnl < 0),
        'total_pnl': sum(t.pnl for t in trades_today),
        'win_rate': (winning / total) * 100,
        'avg_holding': average([t.holding_time for t in trades_today])
    }
    
    # Generate report
    report = generate_eod_report(metrics)
    
    # Send notifications
    send_email_report(report)
    send_telegram_alert(report)
    
    logger.info(f"EOD: {metrics['total_trades']} trades, {metrics['win_rate']:.1f}% win rate")
```

### Paper Trading Signal (5:15 PM)

```python
# tasks/phase5_trading.py
def phase5_paper_trading_signal():
    """Generate daily paper trading signal (Phase 5 validation)"""
    
    if not in_paper_trading_period():
        logger.info("Not in paper trading period")
        return
    
    # Run Phase 5 logic
    signal = generate_paper_trading_signal()
    
    if signal:
        logger.info(f"Paper trading signal: {signal}")
        record_paper_trading(signal)
    
    logger.info("Phase 5 signal generated")
```

---

## 🚀 Deployment Checklist

### Before Going Live

- [ ] **Scheduler Configuration**
  - [ ] Choose scheduler (APScheduler, Cron, or Windows Task)
  - [ ] Configure timezone correctly (IST = UTC+5:30)
  - [ ] Test each cron trigger individually
  - [ ] Verify schedule runs at correct times

- [ ] **Task Verification**
  - [ ] Test `premarket_prep` task
  - [ ] Test `screener_loop` task
  - [ ] Test `position_monitor` task
  - [ ] Test `eod_analysis` task
  - [ ] Test `paper_trading_signal` task

- [ ] **API & Connectivity**
  - [ ] Breeze API connection stable
  - [ ] Historical data loads correctly
  - [ ] Real-time price feeds working
  - [ ] Order placement latency acceptable (<5 sec)

- [ ] **Risk & Safety**
  - [ ] Daily loss limit enforced
  - [ ] Position sizing working
  - [ ] Stop-loss placement automatic
  - [ ] Emergency circuit breaker active

- [ ] **Monitoring & Logging**
  - [ ] Task execution logged
  - [ ] Errors captured and alerted
  - [ ] Dashboard updating in real-time
  - [ ] Email/Telegram alerts working

- [ ] **Paper Trading (Phase 5)**
  - [ ] 4-week validation period set
  - [ ] Daily signals generating
  - [ ] Backtest metrics target set
  - [ ] Decision criteria clear

---

## 📊 Expected Execution Timeline

### Week 1: Initial Setup
- Day 1: Deploy scheduler infrastructure
- Day 2-3: Test individual tasks
- Day 4-5: Full end-to-end testing

### Week 2: Phase 5 Paper Trading
- Starts: Generate daily signals
- Monitor: Win rate, P&L, drawdown
- Adjust: Parameters if needed

### Week 3-4: Continued Paper Trading
- Continue daily signals
- Accumulate 15-20 trades minimum
- Validate success criteria

### Week 5: Go/No-Go Decision
- Analyze Phase 5 results
- If PASS (≥40% WR, <5% DD): Proceed to live
- If FAIL: Debug and iterate

### Week 6+: Live Deployment
- Execute live trading
- Monitor continuously
- Scale if performance good

---

## ✅ Status

| Component | Status | Owner |
|-----------|--------|-------|
| Screener logic | ✅ Ready | Implemented |
| Validator | ✅ Ready | Implemented |
| Execution service | ✅ Ready | Implemented |
| Position monitoring | ✅ Ready | Implemented |
| Trade Management | ✅ Ready | Implemented |
| Scheduler (APScheduler) | ⏳ To implement | Next step |
| Task definitions | ⏳ To implement | Next step |
| End-to-end testing | ⏳ To implement | Next step |

---

## 🎯 Next Steps

1. **Implement APScheduler** (2 hours)
   - Create `app/scheduler.py`
   - Define all cron triggers
   - Register tasks

2. **Create Task Scripts** (3 hours)
   - `tasks/premarket_prep.py`
   - `tasks/screener_loop.py`
   - `tasks/position_monitor.py`
   - `tasks/eod_analysis.py`
   - `tasks/phase5_trading.py`

3. **Test Scheduler** (2 hours)
   - Unit test each task
   - Integration test full sequence
   - Validate time triggers

4. **Deploy & Monitor** (1 hour)
   - Deploy to production
   - Monitor first execution cycle
   - Fix any issues

**Total Effort:** 8 hours  
**Expected Completion:** Today + next day

---

**Created:** June 9, 2026  
**Version:** 1.0  
**Status:** Ready for Implementation ✅
