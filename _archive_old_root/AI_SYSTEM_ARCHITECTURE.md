# PHASE 2 ARCHITECTURE DIAGRAM & FLOW

**Purpose:** Visual reference for Phase 2 system architecture  
**Date:** June 10, 2026

---

## FULL PIPELINE ARCHITECTURE (Phase 2)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         MARKET DATA SOURCES                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  Breeze API  │  OHLC Data  │  Options Chain  │  News Feed (Future)    │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│                    DATA INGESTION & NORMALIZATION                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  app/services/breeze_api.py                                             │ │
│  │  ├─ Fetch historical OHLC                                              │ │
│  │  ├─ Live WebSocket streaming                                           │ │
│  │  └─ Options chain fetching                                             │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│                       FEATURE ENGINEERING (ENHANCED)                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  app/feature_engine.py (NEW)        │  app/strategies/*.py (EXISTING)   │ │
│  │  ├─ MA Ratio                        │  ├─ RSI (14)                     │ │
│  │  ├─ MACD (NEW)                      │  ├─ ATR (14)                     │ │
│  │  ├─ Stochastic RSI (NEW)            │  ├─ Bollinger Bands              │ │
│  │  ├─ Vortex Index (NEW)              │  ├─ ADX                          │ │
│  │  ├─ Put-Call Ratio (NEW)            │  ├─ Volume Ratio                 │ │
│  │  └─ Feature Vector (Aggregated)     │  └─ Momentum                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │ │
│  OUTPUT: pd.DataFrame with all features ready for ML                        │ │
└──────────────────────────────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│                       STAGE 1: SIGNAL GENERATION                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  app/stock_screener.py (Rule-based)                                     │ │
│  │  ├─ SMA20 crossover detection                                          │ │
│  │  ├─ Support/Resistance breaks                                          │ │
│  │  └─ Volume confirmation                                                │ │
│  │                                                                          │ │
│  │  OUTPUT: List of potential buy/sell signals (without confidence)        │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│              STAGE 2: VALIDATION, GATING & ML ENHANCEMENT                    │
│                                                                              │ │
│  ┌─ ML PREDICTION ENGINE (NEW) ──────────────────────────────────────────┐ │
│  │ app/ml_models/prediction_engine.py                                    │ │
│  │ ├─ Input: Feature vector                                             │ │
│  │ ├─ Model: XGBoost (direction + move)                                │ │
│  │ ├─ Output:                                                           │ │
│  │ │  ├─ Direction: UP/DOWN (confidence 0-1)                           │ │
│  │ │  ├─ Expected Move: % (e.g., 2.5%)                                 │ │
│  │ │  ├─ Volatility Forecast: ATR estimate                             │ │
│  │ │  └─ Overall Confidence: 0-1                                       │ │
│  │ └─ Used by: Options strategy selector + Risk manager                │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                              │ │
│  ┌─ VALIDATION LAYER ────────────────────────────────────────────────────┐ │
│  │ app/production_validator.py                                           │ │
│  │ ├─ Position size check                                              │ │
│  │ ├─ Risk/reward ratio check                                          │ │
│  │ ├─ Daily P&L check                                                  │ │
│  │ └─ Reject/Approve signal                                            │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                              │ │
│  ┌─ MARKET REGIME DETECTION ────────────────────────────────────────────┐ │
│  │ app/range_policy.py                                                  │ │
│  │ ├─ Detect RANGE (sideways) regime                                   │ │
│  │ ├─ Detect TREND regime                                              │ │
│  │ └─ Block trades in RANGE (capital preservation)                    │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                              │ │
│  ┌─ SENTIMENT GATE ──────────────────────────────────────────────────────┐ │
│  │ app/market_sentiment_gate.py                                          │ │
│  │ ├─ Check NIFTY trend (macro filter)                                 │ │
│  │ ├─ Adjust confidence based on sentiment                             │ │
│  │ └─ Possible reject if negative sentiment                            │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                              │ │
│  ┌─ KILL-SWITCH CHECK (CRITICAL) ────────────────────────────────────────┐ │
│  │ app/safety/kill_switch.py (NEW)                                      │ │
│  │ ├─ Is kill-switch active?                                           │ │
│  │ │  └─ YES → HALT ALL TRADING                                        │ │
│  │ ├─ Update heartbeats (data feed, API)                               │ │
│  │ └─ Trigger if thresholds hit (done async)                           │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                              │ │
│  OUTPUT: Enhanced signal with ML predictions or REJECTED                    │ │
└──────────────────────────────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│            STAGE 3: OPTIONS STRATEGY SELECTION (PHASE 2 ENHANCED)            │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  app/options_strategy_selector.py (ENHANCED)                            │ │
│  │                                                                          │ │
│  │  INPUT: Signal (BUY/SELL) + ML predictions                             │ │
│  │                                                                          │ │
│  │  PHASE 2 LOGIC:                                                        │ │
│  │  ┌─ Get option chain data                                             │ │
│  │  ├─ Calculate IV percentile                                           │ │
│  │  ├─ Apply rules:                                                      │ │
│  │  │                                                                     │ │
│  │  │  IF IV > 75% (high volatility)                                    │ │
│  │  │    → SELL PREMIUM (spreads)                                       │ │
│  │  │    → Example: Bull Call Spread (buy ATM, sell OTM)               │ │
│  │  │                                                                     │ │
│  │  │  ELSE IF IV < 25% (low volatility)                                │ │
│  │  │    → BUY OPTIONS                                                  │ │
│  │  │    → Example: Long Call                                           │ │
│  │  │                                                                     │ │
│  │  │  IF expected_move > 3%                                            │ │
│  │  │    → Wide strategies / naked options                              │ │
│  │  │                                                                     │ │
│  │  │  IF expected_move < 1%                                            │ │
│  │  │    → Tight spreads (limited risk)                                 │ │
│  │  │                                                                     │ │
│  │  │  Match expiry to signal horizon:                                  │ │
│  │  │    ├─ Short-term signal → Weekly expiry                           │ │
│  │  │    ├─ Medium-term → Monthly expiry                                │ │
│  │  │    └─ Long-term → LEAP or quarterly                               │ │
│  │  │                                                                     │ │
│  │  └─ Select best strike + expiry + quantity                             │ │
│  │                                                                          │ │
│  │  OUTPUT: Trade Plan (specific contracts to buy/sell + quantities)       │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │ │
│  EXAMPLE OUTPUT:                                                             │ │
│  {                                                                           │ │
│    'action': 'BUY',                                                         │ │
│    'legs': [                                                                │ │
│      {'symbol': 'NIFTY26SEP27200C', 'qty': 1},  # Buy ATM call            │ │
│      {'symbol': 'NIFTY26SEP27400C', 'qty': -1}  # Sell OTM call           │ │
│    ],                                                                        │ │
│    'strategy': 'bull_call_spread',                                         │ │
│    'max_profit': 2000,                                                     │ │
│    'max_loss': 8000,                                                       │ │
│    'iv_percentile': 78,                                                    │ │
│    'expected_move': 2.5                                                    │ │
│  }                                                                          │ │
└──────────────────────────────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│         STAGE 4: EXECUTION & ORDER MANAGEMENT (ENHANCED WITH RETRY)          │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  app/services/signal_executor.py (ENHANCED)                             │ │
│  │                                                                          │ │
│  │  FOR EACH LEG IN TRADE PLAN:                                            │ │
│  │  ├─ Attempt 1: Place order via Breeze API                             │ │
│  │  │  ├─ Format order parameters                                         │ │
│  │  │  ├─ Send to broker                                                 │ │
│  │  │  └─ Wait for confirmation (10 sec timeout)                         │ │
│  │  │     ├─ IF filled → Continue to next leg                            │ │
│  │  │     ├─ IF partial → Attempt 2                                      │ │
│  │  │     └─ IF failed → Attempt 2                                       │ │
│  │  │                                                                     │ │
│  │  ├─ Attempt 2: Retry (wait 2 sec, exponential backoff)               │ │
│  │  │  └─ Same flow as Attempt 1                                         │ │
│  │  │                                                                     │ │
│  │  ├─ Attempt 3: Final retry (wait 4 sec)                               │ │
│  │  │  └─ Same flow as Attempt 1                                         │ │
│  │  │                                                                     │ │
│  │  └─ All attempts failed → Log error + abort                            │ │
│  │                                                                          │ │
│  │  TRACK: Order state (NEW → PENDING → FILLED or REJECTED)               │ │
│  │                                                                          │ │
│  │  OUTPUT: Executed trades + order IDs                                    │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│              STAGE 5: POSITION MONITORING & EXIT MANAGEMENT                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  app/live_position_tracker.py + app/profit_booking_manager.py          │ │
│  │  ├─ Track all open positions                                           │ │
│  │  ├─ Calculate real-time P&L                                            │ │
│  │  ├─ Monitor profit targets                                             │ │
│  │  ├─ Apply stop-losses                                                  │ │
│  │  └─ Execute exits (SMA20 breakdown, target hit, stop)                 │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│      STAGE 6: RISK MONITORING, ALERTS & KILL-SWITCH AUTO-TRIGGERS          │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  app/services/risk_manager.py (ENHANCED)                               │ │
│  │  + app/safety/kill_switch.py (NEW - runs continuously)                 │ │
│  │                                                                          │ │
│  │  CONTINUOUS MONITORING (every 1 second):                                │ │
│  │  ├─ Daily P&L vs limit                                                 │ │
│  │  │  └─ IF drawdown > 10% → KILL-SWITCH TRIGGERED                      │ │
│  │  │                                                                     │ │
│  │  ├─ Consecutive losses count                                           │ │
│  │  │  └─ IF >= 5 losses → KILL-SWITCH TRIGGERED                         │ │
│  │  │                                                                     │ │
│  │  ├─ Data feed heartbeat                                                │ │
│  │  │  └─ IF no data > 30 sec → KILL-SWITCH TRIGGERED                    │ │
│  │  │                                                                     │ │
│  │  ├─ Broker API heartbeat                                               │ │
│  │  │  └─ IF no response > 10 sec → KILL-SWITCH TRIGGERED                │ │
│  │  │                                                                     │ │
│  │  ├─ Manual trigger available (always)                                  │ │
│  │  │  └─ User press → KILL-SWITCH TRIGGERED                             │ │
│  │  │                                                                     │ │
│  │  ├─ KILL-SWITCH ACTIVATION ACTIONS:                                    │ │
│  │  │  ├─ Cancel all pending orders                                      │ │
│  │  │  ├─ Close all open positions (market orders)                       │ │
│  │  │  ├─ Halt trading loop                                              │ │
│  │  │  ├─ Alert all stakeholders                                         │ │
│  │  │  ├─ Log event with reason + timestamp                              │ │
│  │  │  └─ REQUIRE MANUAL RESET (not automatic)                           │ │
│  │  │                                                                     │ │
│  │  └─ Send alerts to notification service                                │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│         STAGE 7: LEARNING & MONITORING (NEW AUTOMATED)                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  app/monitoring/performance_monitor.py (NEW)                            │ │
│  │  app/monitoring/metrics_calculator.py (NEW)                             │ │
│  │                                                                          │ │
│  │  COLLECT METRICS:                                                       │ │
│  │  ├─ Win Rate: winning trades / total trades                            │ │
│  │  ├─ Profit Factor: gross profit / abs(gross loss)                     │ │
│  │  ├─ Max Drawdown: peak-to-valley decline                              │ │
│  │  ├─ Sharpe Ratio: risk-adjusted return                                │ │
│  │  ├─ Model Accuracy: % correct directional predictions                 │ │
│  │  ├─ Execution Speed: signal-to-order time                             │ │
│  │  ├─ Fill Rate: orders filled / orders placed                          │ │
│  │  └─ Daily P&L: profit/loss for session                                │ │
│  │                                                                          │ │
│  │  GENERATE REPORTS:                                                      │ │
│  │  ├─ Real-time dashboard (JSON)                                         │ │
│  │  ├─ Daily summary email                                                │ │
│  │  ├─ Weekly performance review                                          │ │
│  │  └─ Monthly trend analysis                                             │ │
│  │                                                                          │ │
│  │  LOG ALL DECISIONS:                                                     │ │
│  │  ├─ Every trade with reasoning                                         │ │
│  │  ├─ Every risk event                                                   │ │
│  │  ├─ Every kill-switch trigger                                          │ │
│  │  ├─ Model predictions vs actuals                                       │ │
│  │  └─ 7-year audit trail (compliance)                                    │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
         ↓
        CYCLE COMPLETE
        (Repeat every 5 minutes or whenever signal generated)
```

---

## COMPONENT INTERACTION MATRIX

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  WHO CALLS WHO - Data Flow                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TradingEngine (Orchestrator)                                               │
│  ├─ Calls: StockScreener → Get signals                                     │
│  ├─ Calls: FeatureEngine → Get features                                    │
│  ├─ Calls: PredictionEngine → Get ML predictions                           │
│  ├─ Calls: ProductionValidator → Validate signals                          │
│  ├─ Calls: RangePolicy → Check market regime                               │
│  ├─ Calls: MarketSentimentGate → Filter by macro                           │
│  ├─ Calls: KillSwitch → Check if active                                    │
│  ├─ Calls: OptionsStrategySelector → Select strategy                       │
│  ├─ Calls: SignalExecutor → Place orders                                   │
│  ├─ Calls: PositionTracker → Get positions                                 │
│  ├─ Calls: ProfitBookingManager → Exit positions                           │
│  ├─ Calls: RiskManager → Check limits                                      │
│  └─ Calls: PerformanceMonitor → Log metrics                                │
│                                                                              │
│  KillSwitch (Parallel Thread)                                               │
│  ├─ Monitors: RiskManager.daily_pnl                                         │
│  ├─ Monitors: RiskManager.consecutive_losses                               │
│  ├─ Monitors: DataFeed heartbeat                                            │
│  ├─ Monitors: BrokerAPI heartbeat                                           │
│  ├─ Calls: SignalExecutor.cancel_all_orders() when triggered               │
│  ├─ Calls: SignalExecutor.close_all_positions() when triggered             │
│  ├─ Calls: NotificationService.alert() when activated                      │
│  └─ Logs: AuditLogger.log_kill_switch_event()                              │
│                                                                              │
│  PredictionEngine                                                            │
│  ├─ Uses: FeatureEngine output (feature vector)                             │
│  ├─ Uses: XGBoost model (loaded at init)                                    │
│  └─ Returns: Prediction object (direction + move + vol + confidence)       │
│                                                                              │
│  OptionsStrategySelector                                                    │
│  ├─ Uses: PredictionEngine predictions                                      │
│  ├─ Uses: OptionChain data (IV, strikes)                                    │
│  ├─ Uses: RiskManager position limits                                       │
│  └─ Returns: TradePlan (legs, quantities, strategy name)                    │
│                                                                              │
│  SignalExecutor                                                             │
│  ├─ Uses: TradePlan from OptionsStrategySelector                            │
│  ├─ Calls: BreezeAPI.place_order()                                          │
│  ├─ Tracks: Order state (NEW → FILLED or REJECTED)                         │
│  ├─ Retries: Up to 3 times with exponential backoff                         │
│  └─ Returns: ExecutionResult (filled/rejected)                              │
│                                                                              │
│  PerformanceMonitor (Parallel Thread)                                        │
│  ├─ Collects: PositionTracker.all_trades                                    │
│  ├─ Calculates: Win rate, profit factor, Sharpe ratio                       │
│  ├─ Compares: ML predictions vs actual outcomes                             │
│  ├─ Generates: Daily reports                                                │
│  └─ Logs: All metrics to AuditLogger                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## STATE MACHINE: KILL-SWITCH STATES

```
                    ┌─────────────────────────┐
                    │   NORMAL OPERATION      │
                    │   (Kill-Switch INACTIVE)│
                    └────────────┬────────────┘
                                 │
                    ┌────────────────────────────────┐
                    │ Automatic Trigger OR Manual    │
                    │ - Drawdown > 10%               │
                    │ - 5+ consecutive losses        │
                    │ - Data feed heartbeat loss     │
                    │ - User presses emergency stop  │
                    └────────────────────────────────┘
                                 │
                                 ↓
                    ┌─────────────────────────┐
                    │ KILL-SWITCH ACTIVATED   │
                    │ ├─ Cancel all orders    │
                    │ ├─ Close all positions  │
                    │ ├─ Halt trading loop    │
                    │ ├─ Alert stakeholders   │
                    │ └─ Log event            │
                    └────────────┬────────────┘
                                 │
                    ┌────────────────────────────────┐
                    │ TRADING HALTED                 │
                    │ (no new trades possible)       │
                    │ (manual reset required)        │
                    └────────────┬───────────────────┘
                                 │
                    ┌────────────────────────────────┐
                    │ Manual Review/Investigation    │
                    │ User investigates & fixes      │
                    └────────────┬───────────────────┘
                                 │
                    ┌────────────────────────────────┐
                    │ User Confirms Reset            │
                    │ (active parameter must be true)│
                    └────────────┬───────────────────┘
                                 │
                                 ↓
                    ┌─────────────────────────┐
                    │   NORMAL OPERATION      │
                    │   (Resume Trading)      │
                    └─────────────────────────┘
```

---

## DATA FLOW: SIGNAL TO EXECUTION

```
TIME: T=0 (Start of cycle)
│
├─ T=0.0s: Signal detected in screener
│           └─ Example: NIFTY SMA20 crosses above SMA50
│
├─ T=0.1s: Feature Engine computes features
│           ├─ MA Ratio: 1.023
│           ├─ RSI: 68.5
│           ├─ MACD: 45.3 (positive)
│           ├─ ATR: 1.52
│           ├─ Put-Call: 0.95
│           └─ [... more features ...]
│
├─ T=0.2s: ML Prediction Engine predicts
│           ├─ Direction: UP (89% confidence)
│           ├─ Expected Move: +2.5%
│           ├─ Volatility: 2.1%
│           └─ Overall Score: 0.85
│
├─ T=0.3s: Validation Layer checks
│           ├─ Position size: OK (within limits)
│           ├─ Risk/Reward: OK (ratio > 1.5)
│           ├─ Daily P&L: OK (not in loss limit)
│           └─ Status: PASS
│
├─ T=0.4s: Range Policy checks market regime
│           ├─ ATR check: 1.52% (not low)
│           ├─ ADX check: 28 (trending)
│           ├─ Persistence: 8 bars
│           └─ Verdict: TRENDING (not RANGE) → PASS
│
├─ T=0.5s: Sentiment Gate checks macro
│           ├─ NIFTY MA20: 25400
│           ├─ NIFTY MA200: 25100
│           ├─ Ratio: 1.012 (slightly bullish)
│           └─ Verdict: ALLOW → PASS
│
├─ T=0.6s: Kill-Switch checks active status
│           ├─ Is active? NO
│           ├─ Check heartbeats? OK (all alive)
│           └─ Verdict: PROCEED
│
├─ T=0.7s: Options Strategy Selector chooses strategy
│           ├─ Get option chain
│           ├─ IV percentile: 72% (fairly high)
│           ├─ Expected move: 2.5%
│           ├─ Selected: Bull Call Spread
│           │  └─ Buy 27200 Call + Sell 27400 Call
│           └─ Trade Plan: READY
│
├─ T=0.8s: Signal Executor Attempt #1
│           ├─ Format order (2 legs)
│           ├─ Leg 1: Buy 27200 Call
│           ├─ Leg 2: Sell 27400 Call
│           ├─ Send to Breeze API
│           └─ Wait for fill (10s timeout)
│
├─ T=0.9s: Breeze API responds
│           ├─ Leg 1: FILLED (premium paid: ₹450)
│           └─ Leg 2: FILLED (premium received: ₹320)
│
├─ T=1.0s: Position Tracker records trade
│           ├─ Net debit: ₹130 (₹450 - ₹320)
│           ├─ Max profit: ₹1870 (if both legs reach max)
│           ├─ Max loss: ₹130 (if spreads worthless)
│           └─ Status: OPEN
│
├─ T=1.1s: Performance Monitor logs
│           ├─ Trade recorded in audit log
│           ├─ Model accuracy: Updated
│           ├─ Execution speed: 1.1 seconds ✅
│           └─ Status: COMPLETE
│
└─ T=1.1s: Cycle complete, wait for next signal or exit condition
```

---

## ERROR HANDLING FLOW

```
                       Order Placement Attempt
                                │
                    ┌───────────────────────────┐
                    │  Try to place order       │
                    │  via Breeze API           │
                    └────────────┬──────────────┘
                                 │
                    ┌────────────────────────────┐
                    │ Wait 10 seconds for response│
                    │ or Timeout                  │
                    └────────────┬───────────────┘
                                 │
                ┌────────────────────────────────┐
                │                                │
         FILLED/OK                          ERROR/TIMEOUT
         (100%)                             (RETRY)
                │                                │
                ↓                                ↓
        Continue                     ┌─────────────────────────┐
        to next leg                  │ Increment retry counter │
                                     │ Wait 2^(attempt-1) sec  │
                                     └────────┬────────────────┘
                                              │
                                    ┌─────────────────────────┐
                                    │ Attempt 1: Wait 1s      │
                                    │ Attempt 2: Wait 2s      │
                                    │ Attempt 3: Wait 4s      │
                                    └────────┬────────────────┘
                                             │
                          ┌──────────────────────────────────┐
                          │                                  │
                    ATTEMPT 1-3                        ATTEMPT > 3
                         │                                   │
                         ↓                                   ↓
                    Retry flow                    ┌────────────────────┐
                    (back to Try)                 │ All retries failed  │
                                                  │ ├─ Log error        │
                                                  │ ├─ Abort order      │
                                                  │ ├─ Alert risk mgr   │
                                                  │ └─ Continue cycle   │
                                                  └────────────────────┘
```

---

## MONITORING & ALERTING FLOW

```
                    ┌───────────────────────────┐
                    │  Every 1 Second Check:    │
                    │  Risk Conditions          │
                    └────────────┬──────────────┘
                                 │
        ┌────────────────────────────────────────┐
        │                                         │
    Check 1: Daily P&L            Check 2: Consecutive Losses
    ├─ Current P&L: -8,000        ├─ Losses: 4
    ├─ Limit: -10,000             ├─ Limit: 5
    ├─ Status: OK (within)         ├─ Status: OK (within)
    └─ NO TRIGGER                  └─ NO TRIGGER
        │                              │
        └──────────────────┬───────────┘
                           │
        ┌────────────────────────────────────────┐
        │                                         │
    Check 3: Data Feed Heartbeat   Check 4: API Heartbeat
    ├─ Last tick: 0.5s ago          ├─ Last response: 0.3s ago
    ├─ Timeout: 30s                 ├─ Timeout: 10s
    ├─ Status: ALIVE                ├─ Status: ALIVE
    └─ NO TRIGGER                   └─ NO TRIGGER
        │                              │
        └──────────────────┬───────────┘
                           │
                ┌──────────────────────┐
                │  ALL CHECKS PASS     │
                │  Continue trading    │
                └──────────────────────┘


        BUT IF ANY CHECK FAILS:
                           │
        ┌──────────────────────────────────────┐
        │  TRIGGER = TRUE                       │
        │  ├─ Log reason                        │
        │  ├─ Activate kill-switch              │
        │  ├─ Cancel all orders                 │
        │  ├─ Close all positions               │
        │  ├─ Alert all recipients              │
        │  └─ Halt trading loop                 │
        └──────────────────────────────────────┘
```

---

**Document Type:** Architecture Reference  
**Last Updated:** June 10, 2026  
**Audience:** Development Team
