# AI-Enabled Indian Options Trading System: Phase Migration Mapping

**Document Date:** June 10, 2026  
**Status:** Active Migration - Phase 1 → Phase 2 → Phase 3  
**Target:** Full AI-Autonomous Options Trading System

---

## Executive Summary

GreeksMaster's existing trading system is **70% aligned** with Phase 1-2 requirements of the AI-Enabled Indian Options Trading System spec. This document maps current components to required modules and outlines a clear implementation roadmap.

**Current State:**
- ✅ Phase 1 (Paper Trading): ~90% Complete
- ✅ Phase 2 (Controlled Live): ~60% Complete  
- ⏳ Phase 3 (Fully Autonomous): 0% (Ready for implementation)

---

## Module Mapping: Existing Code → Spec Requirements

### 1. DATA INGESTION & MANAGEMENT

**Spec Requirement:** Fetch historical/live market & options data, normalize, store

| Spec Requirement | Current Implementation | Status | Gap | Action |
|---|---|---|---|---|
| **Historical Data Loader** | `app/services/breeze_api.py` (Breeze endpoints) | ✅ | None | Use as-is |
| **Live Data Streamer** | `app/services/breeze_api.py` WebSocket + `data_stream.py` | ✅ | Needs async scaling | Enhance for multi-symbol streaming |
| **Data Normalization** | `app/utils/*.py` + pandas transforms | ✅ | Partial | Add standardized schema validation |
| **Time Alignment** | Manual in screeners | ⚠️ | Manual sync | Create `DataAlignmentService` |
| **Storage** | Pandas DataFrames in memory | ✅ Phase 1 | No persistence | Add TimescaleDB option (Phase 3) |

**Phase 1 Status:** ✅ COMPLETE (in-memory sufficient)  
**Phase 2 Status:** ✅ FUNCTIONAL (add caching layer)  
**Phase 3 Action:** Add database persistence + multi-source ingestion

---

### 2. FEATURE ENGINEERING

**Spec Requirement:** Compute technical indicators, statistical features, sentiment

| Spec Requirement | Current Implementation | Status | Gap | Action |
|---|---|---|---|---|
| **Technical Indicators** | `app/strategies/` (MA, RSI, ATR, BB, ADX) | ✅ | Missing some | Add MACD, Stoch, Vortex |
| **Statistical Features** | `range_policy.py` (volume, persistence) | ✅ | Partial | Expand feature vector |
| **Sentiment Indicators** | Not implemented | ❌ | Missing | Create `SentimentFeatureEngine` |
| **Real-time Updates** | Range Policy (rolling calcs) | ⚠️ | Per-cycle only | Add streaming updates |

**Phase 1 Status:** ✅ COMPLETE (batch computation)  
**Phase 2 Status:** ⚠️ PARTIAL (add real-time) → **Action Item**  
**Phase 3 Action:** Sentiment integration + multi-horizon features

---

### 3. AI PREDICTION ENGINE

**Spec Requirement:** ML models (price direction, volatility), inference, ensemble

| Spec Requirement | Current Implementation | Status | Gap | Action |
|---|---|---|---|---|
| **ML Models** | `backtest/backtest_trading_engine_with_ai.py` (basic ML) | ✅ Phase 1 | XGBoost trained offline | Integrate pre-trained models |
| **Model Training** | Notebooks/batch scripts | ⚠️ | Not automated | Create `ModelTrainingPipeline` |
| **Model Inference** | Rules-based (no formal ML inference) | ⚠️ | Missing | Create `PredictionEngine` class |
| **Multiple Models** | Single SMA20 + Range detection | ⚠️ | Limited | Add price/volatility ensemble |
| **Confidence Scores** | Signal confidence (0-1) | ✅ | Present | Leverage existing |

**Phase 1 Status:** ✅ RESEARCH (rules-based sufficient)  
**Phase 2 Status:** ⚠️ NEEDS WORK → **Major Action Item**  
**Phase 3 Action:** Ensemble models + online learning

---

### 4. SIGNAL GENERATION ENGINE

**Spec Requirement:** Fuse predictions + rules into trade signals, rank, filter

| Spec Requirement | Current Implementation | Status | Gap | Action |
|---|---|---|---|---|
| **Signal Logic** | `app/stock_screener.py` (SMA20 crossover) | ✅ | Simple logic | Enhance multi-factor |
| **Signal Confidence** | Signal object with confidence field | ✅ | Present | Ensure 0-1 range |
| **Signal Ranking** | Manual (not ranked) | ⚠️ | Missing | Add ranking by expected return |
| **Signal Filtering** | `production_validator.py` (pre-trade checks) | ✅ | Present | Use as gating mechanism |
| **Standardized Format** | Dict/dataclass signals | ✅ | Present | Use as-is |

**Phase 1 Status:** ✅ COMPLETE (rule-based signals)  
**Phase 2 Status:** ✅ FUNCTIONAL (add ML signals) → **Action Item**  
**Phase 3 Action:** Complex multi-factor + sentiment filters

---

### 5. OPTIONS STRATEGY SELECTOR

**Spec Requirement:** Map signals → optimal options strategy, strike/expiry selection

| Spec Requirement | Current Implementation | Status | Gap | Action |
|---|---|---|---|---|
| **Strategy Selection** | `app/options_strategy_selector.py` (ATM basic) | ⚠️ | Simplistic | Implement Phase 2 logic |
| **Strike Selection** | ATM strikes only | ⚠️ | Limited | Add volatility-aware selection |
| **Expiry Selection** | Nearest expiry (hardcoded) | ⚠️ | Limited | Add time-horizon matching |
| **Greeks Calculation** | Not implemented | ❌ | Missing | Integrate QuantLib/Black-Scholes |
| **Position Sizing** | `risk_manager.py` (separate) | ✅ | Present | Coordinate with strategy selection |
| **Multi-leg Support** | Not implemented | ❌ | Missing | Create spreads support (Phase 3) |

**Phase 1 Status:** ✅ BASIC (single-leg only)  
**Phase 2 Status:** ⚠️ PARTIAL → **Major Action Item**  
**Phase 3 Action:** AI-optimized multi-leg strategies + Greeks optimization

---

### 6. EXECUTION & ORDER MANAGEMENT

**Spec Requirement:** Place orders via Breeze API, track fills, manage orders

| Spec Requirement | Current Implementation | Status | Gap | Action |
|---|---|---|---|---|
| **Order Placement** | `app/services/signal_executor.py` (via Breeze) | ✅ | Functional | Enhance error handling |
| **Order Tracking** | `live_position_tracker.py` (positions) | ✅ | Partial | Add order state tracking |
| **Partial Fills** | Not handled | ❌ | Missing | Add retry logic |
| **Paper Trading** | `backtest_trading_engine.py` | ✅ | Separate | Unify simulators |
| **Order Rate Limiting** | Not implemented | ❌ | Missing | Add throttling |
| **Error Recovery** | Basic try/except | ⚠️ | Weak | Add robust fallbacks |

**Phase 1 Status:** ✅ SIMULATION COMPLETE (backtest engines)  
**Phase 2 Status:** ✅ LIVE PARTIAL → **Enhance error handling**  
**Phase 3 Action:** Advanced order mgmt + multi-leg orders

---

### 7. RISK MANAGEMENT & KILL-SWITCH

**Spec Requirement:** Pre/post-trade checks, kill-switch, daily limits, heartbeat

| Spec Requirement | Current Implementation | Status | Gap | Action |
|---|---|---|---|---|
| **Pre-trade Checks** | `production_validator.py` (comprehensive) | ✅ | Functional | Use as-is |
| **Max Position Size** | `risk_manager.py` (enforced) | ✅ | Implemented | Already present |
| **Daily Loss Limit** | `risk_manager.py` (daily P&L limit) | ✅ | Implemented | Already present |
| **Kill-Switch** | Not formally implemented | ❌ | Missing | **Create formal kill-switch module** |
| **Order Rate Limit** | Not implemented | ❌ | Missing | Add to risk_manager |
| **Heartbeat Monitor** | Not implemented | ❌ | Missing | Create system monitor thread |
| **Circuit Breaker** | Not implemented | ❌ | Missing | Add market-wide halt detection |
| **Audit Logging** | Basic logging | ⚠️ | Weak | Add immutable audit log |

**Phase 1 Status:** ✅ PARTIAL (basic limits)  
**Phase 2 Status:** ⚠️ NEEDS CRITICAL WORK → **High Priority**  
**Phase 3 Action:** Multi-layer controls + external safeguards

---

### 8. LEARNING & ADAPTATION

**Spec Requirement:** Log trades, compute metrics, retrain models, adapt parameters

| Spec Requirement | Current Implementation | Status | Gap | Action |
|---|---|---|---|---|
| **Trade Logging** | `backtest/backtest_trading_engine_with_ai.py` (detailed) | ✅ | Good | Use existing format |
| **Performance Analytics** | `BACKTEST_ANALYSIS_REPORT.md` generation | ✅ | Manual | Automate reporting |
| **Win-Rate Calculation** | Implemented in backtests | ✅ | Present | Create reusable metrics module |
| **Model Retraining** | Offline/manual | ⚠️ | Manual | Create `AutoRetrainingPipeline` |
| **Parameter Tuning** | Manual tuning via config | ⚠️ | Manual | Add Bayesian optimizer (Phase 3) |
| **Online Learning** | Not implemented | ❌ | Missing | Add incremental learning (Phase 3) |
| **Database** | None (file-based) | ⚠️ | Weak | Add SQLite → PostgreSQL |

**Phase 1 Status:** ✅ MANUAL ANALYSIS (sufficient)  
**Phase 2 Status:** ⚠️ PARTIAL → **Automate reporting & retraining**  
**Phase 3 Action:** Continuous learning loop + RL

---

## Phase Implementation Roadmap

### PHASE 1: RESEARCH & PAPER TRADING ✅ 90% COMPLETE

**Current State:** Trend-following SMA20 crossover with Range Policy capital preservation

**Remaining Work (1 week):**
1. ✅ Complete range detection (done in range_policy.py)
2. ✅ Sentiment gate implementation (done in market_sentiment_gate.py)
3. ✅ Backtest integration (done in backtest_trading_engine_with_ai.py)
4. **Add:** Standardized metrics reporting
5. **Add:** Performance analytics dashboard

**Phase 1 Completion Criteria:**
- ✅ 50+ trades backtested
- ✅ Win rate ≥ 40%
- ✅ Daily backtest running < 2min
- ✅ All signals logged with reasoning

**Deliverables:**
- `app/phase_1_completion_report.md`
- Backtest report (DONE)

---

### PHASE 2: CONTROLLED LIVE TRADING ⏳ 60% COMPLETE

**Current State:** Manual/semi-automated with strong risk controls

**Critical Work (2-3 weeks) - HIGH PRIORITY:**

#### 2.1 AI PREDICTION ENGINE (NEW)
```
Status: 0% - PRIORITY 1
Timeline: 1 week
Deliverable: app/ml_models/prediction_engine.py

- XGBoost model for price direction (+2% in next N bars)
- Volatility forecasting (ATR, BB squeeze detection)
- Model inference in real-time
- Confidence scoring (0-1)
- Performance monitoring vs actuals
```

**Implementation Steps:**
1. Create `app/ml_models/` directory
2. Train XGBoost on historical data (last 2 years NIFTY50)
3. Export model (joblib)
4. Create `PredictionEngine` class
5. Integrate into signal generation

**Code Template:**
```python
# app/ml_models/prediction_engine.py
class PredictionEngine:
    def __init__(self, model_path):
        self.model = joblib.load(model_path)
    
    def predict(self, features: pd.DataFrame) -> dict:
        """
        Returns:
        - direction: 'UP' / 'DOWN'
        - confidence: 0.0-1.0
        - expected_return: float (e.g., 0.02 for +2%)
        """
        proba = self.model.predict_proba(features)[0]
        direction = 'UP' if proba[1] > 0.5 else 'DOWN'
        return {
            'direction': direction,
            'confidence': max(proba),
            'expected_return': self.expected_move_model.predict(features)[0]
        }
```

#### 2.2 FEATURE ENGINEERING EXPANSION (NEW)
```
Status: 50% - PRIORITY 2
Timeline: 5 days
Deliverable: app/feature_engine.py

- Real-time indicator updates (already have: MA, RSI, ATR, BB, ADX)
- Add: MACD, Stochastic RSI, Vortex Index
- Sentiment proxy (put-call ratio from options data)
- Multi-timeframe features (1h, 4h, 1d)
```

**Action Items:**
1. Add MACD, Stoch, Vortex to indicator suite
2. Fetch options chain → compute put-call ratio
3. Create feature vector aggregator

#### 2.3 KILL-SWITCH SYSTEM (CRITICAL)
```
Status: 0% - PRIORITY 1 (CRITICAL FOR LIVE)
Timeline: 3 days
Deliverable: app/safety/kill_switch.py

- Manual trigger via API/UI
- Automatic triggers:
  - Drawdown > 10% daily
  - 5 consecutive losses
  - API connectivity loss > 30s
- Action: Cancel all orders, close positions, halt trading
- Require manual reset
```

**Implementation:**
```python
# app/safety/kill_switch.py
class KillSwitch:
    def __init__(self, executor, risk_manager):
        self.active = False
        self.executor = executor
        self.reason = None
    
    def activate(self, reason: str):
        """Emergency stop"""
        self.active = True
        self.reason = reason
        self.executor.cancel_all_orders()
        self.executor.close_all_positions()
        logger.critical(f"KILLSWITCH ACTIVATED: {reason}")
    
    def check_triggers(self, portfolio_state):
        """Check automatic triggers"""
        if portfolio_state['daily_drawdown'] > 0.10:
            self.activate("Daily drawdown > 10%")
        if len(portfolio_state['consecutive_losses']) >= 5:
            self.activate("5 consecutive losses")
```

#### 2.4 ENHANCED EXECUTION & ORDER MANAGEMENT
```
Status: 60% - PRIORITY 3
Timeline: 1 week
Deliverable: Enhanced app/services/signal_executor.py

- Retry logic for partial fills
- Order state tracking (NEW, PENDING, FILLED, REJECTED)
- Timeout handling
- API error recovery
```

#### 2.5 OPTIONS STRATEGY SELECTOR - PHASE 2
```
Status: 30% - PRIORITY 2
Timeline: 5 days
Deliverable: Enhanced app/options_strategy_selector.py

Phase 2 Logic:
- If IV_percentile > 75% → Use spreads (e.g., bull call spread)
- If IV_percentile < 25% → Buy options (e.g., long call)
- If expected_move < 1% → Use tight spreads
- If expected_move > 3% → Use wide spreads or naked options
- Match expiry to signal timeframe
```

**Code Skeleton:**
```python
class OptionsStrategySelector:
    def select_strategy(self, signal, option_chain, market_metrics):
        """
        signal: {'direction': 'BUY', 'confidence': 0.72, ...}
        option_chain: DataFrame with strikes, IV, etc.
        market_metrics: {'iv_percentile': 85, 'expected_move': 2.5, ...}
        
        Returns: trade_plan with legs
        """
        iv_pct = market_metrics['iv_percentile']
        exp_move = market_metrics['expected_move']
        
        if signal['direction'] == 'BUY':
            if iv_pct > 75:
                return self._bull_call_spread(signal, option_chain)
            elif exp_move < 1:
                return self._tight_spread(signal, option_chain)
            else:
                return self._long_call(signal, option_chain)
```

#### 2.6 AUTOMATED REPORTING & MONITORING
```
Status: 20% - PRIORITY 4
Timeline: 3 days
Deliverable: app/monitoring/performance_monitor.py

- Daily performance summary
- Win rate, profit factor, max drawdown
- Model accuracy vs actuals
- Signal quality metrics
- Email alerts on key events
```

**Phase 2 Completion Criteria:**
- ✅ Kill-switch tested & operational
- ✅ ML model integrated & live testing
- ✅ Feature engine expanded
- ✅ Options strategy selector Phase 2 logic
- ✅ Execution robustness enhanced
- ✅ Daily automated reports
- ✅ 2 weeks of live trading data
- ✅ Model accuracy > 55%

**Phase 2 Timeline:** 2-3 weeks  
**Phase 2 Entry Criteria:** Phase 1 metrics validated, backtest profitable  
**Phase 2 Exit Criteria:** Live paper trading 2+ weeks, key systems tested

---

### PHASE 3: FULLY AUTONOMOUS ⏳ 0% - FUTURE

**Vision:** AI-driven decisions with multi-layer safety

**Major Work (4-6 weeks):**

#### 3.1 ENSEMBLE AI MODELS
- Deep learning (LSTM/Transformers for time series)
- Multiple targets (price, volatility, regime)
- Adaptive online learning
- Confidence estimation

#### 3.2 ADVANCED STRATEGY SELECTION
- AI-optimized multi-leg strategies
- Greeks optimization (delta/gamma targeting)
- Probability of profit calculation
- RL agent for parameter optimization

#### 3.3 SENTIMENT INTEGRATION
- News sentiment API integration
- Social media analysis
- Macro-economic triggers
- Sentiment → position size scaling

#### 3.4 SCALABLE DATA PIPELINE
- Kafka/Redis for streaming
- TimescaleDB for historical storage
- Multi-source data ingestion
- Real-time feature updates

#### 3.5 PRODUCTION RISK FRAMEWORK
- Multi-layer pre/post-trade checks
- Dynamic position sizing (volatility-based)
- Portfolio-level Greeks management
- Circuit breaker patterns

#### 3.6 CONTINUOUS LEARNING LOOP
- Automated model retraining (daily/weekly)
- Online learning (streaming updates)
- A/B testing framework
- Parameter optimization via Bayesian search

**Phase 3 Timeline:** 4-6 weeks (post Phase 2 completion)  
**Phase 3 Prerequisites:** Phase 2 fully operational + 4+ weeks performance data

---

## Implementation Priority Matrix

```
PRIORITY 1 (DO FIRST - Weeks 1-2):
├─ Kill-Switch System (CRITICAL)
├─ ML Prediction Engine Integration
└─ Feature Engine Expansion

PRIORITY 2 (Weeks 2-3):
├─ Options Strategy Selector Phase 2 Logic
├─ Enhanced Execution & Error Handling
└─ Automated Performance Reporting

PRIORITY 3 (Weeks 3-4):
├─ Audit Logging & Compliance
├─ Database Integration (SQLite)
└─ System Monitoring & Alerting

PRIORITY 4 (Weeks 4+):
├─ Sentiment Feature Engine
├─ Advanced Order Management
└─ Phase 3 Foundation
```

---

## File Structure - Phase 2 Implementation

```
app/
├── ml_models/                          # NEW
│   ├── __init__.py
│   ├── prediction_engine.py            # NEW - Main ML inference
│   ├── model_trainer.py                # NEW - Offline training
│   └── models/
│       ├── price_direction_xgboost.pkl
│       └── volatility_forecast_xgb.pkl
├── safety/                             # NEW
│   ├── __init__.py
│   ├── kill_switch.py                  # NEW - Emergency stop
│   ├── heartbeat_monitor.py            # NEW - System health
│   └── circuit_breaker.py              # NEW - Market-wide halts
├── monitoring/                         # NEW
│   ├── __init__.py
│   ├── performance_monitor.py          # NEW - Metrics & alerts
│   ├── metrics_calculator.py           # NEW - Win rate, Sharpe, etc.
│   └── reporters/
│       ├── daily_report.py             # NEW
│       └── alert_sender.py             # NEW
├── feature_engine.py                   # ENHANCED
├── engine/
│   ├── trading_engine.py               # ENHANCED with Phase 2 flow
│   └── scheduler.py                    # ENHANCED with monitoring
├── services/
│   ├── signal_executor.py              # ENHANCED - Better error handling
│   └── risk_manager.py                 # ENHANCED - Kill-switch integration
├── options_strategy_selector.py        # ENHANCED - Phase 2 logic
└── production_validator.py             # ENHANCED - Kill-switch triggers
```

---

## Testing Strategy - Phase 2

### Unit Tests
```python
# tests/test_kill_switch.py
def test_kill_switch_manual_trigger()
def test_kill_switch_drawdown_trigger()
def test_kill_switch_closes_positions()

# tests/test_prediction_engine.py
def test_prediction_inference()
def test_confidence_scores()
def test_model_accuracy()

# tests/test_options_strategy.py
def test_bull_call_spread_selection()
def test_iv_based_strategy_selection()
def test_position_sizing()
```

### Integration Tests
```python
# tests/test_phase_2_flow.py
def test_signal_to_execution_flow()
def test_kill_switch_in_live_flow()
def test_performance_monitoring()
```

### Live Testing
```
Week 1: Paper trading with all Phase 2 systems
Week 2: Small capital (₹10k) with demo orders
Week 3: Scale capital based on performance
```

---

## Metrics & Success Criteria

### Phase 2 Success Metrics
- **Model Accuracy:** > 55% directional accuracy on holdout test set
- **Signal Quality:** > 60% winning trades (backtest + paper)
- **System Reliability:** 99.5% uptime during market hours
- **Risk Management:** 0 uncontrolled losses, kill-switch working
- **Execution Speed:** Signal to order < 2 seconds
- **Capital Preservation:** Daily loss limit never exceeded

### Phase 2 Monitoring Dashboard
```
Real-time:
- Active positions count
- Daily P&L
- Model accuracy (current session)
- System status (green/yellow/red)
- Kill-switch status

Daily:
- Win rate
- Profit factor
- Max drawdown
- Sharpe ratio
- Trade count
```

---

## Risk & Mitigation

### Risk 1: Model Accuracy < 55%
**Mitigation:**
- Start with ensemble (use existing rules + ML)
- Backtest extensively before live
- Paper trading validation required

### Risk 2: Kill-Switch Failure
**Mitigation:**
- Thorough unit testing
- Manual kill-switch redundancy
- Broker-level circuit breaker backup

### Risk 3: Execution Failures
**Mitigation:**
- Retry logic with exponential backoff
- Order state tracking
- Manual intervention capability

### Risk 4: Model Drift
**Mitigation:**
- Weekly retraining
- Performance monitoring
- Automatic model rollback on accuracy drop

---

## Dependencies & Libraries - Phase 2

```python
# ML & Data
scikit-learn      # Existing models, ensemble
xgboost           # For new models (if not present)
pandas            # Feature engineering
numpy             # Numerical operations

# TA-Lib Alternative
ta               # Technical indicators (install: pip install ta)

# Options Pricing
numpy-financial  # Financial calculations
scipy            # Black-Scholes if implementing

# Database
sqlalchemy       # ORM for future DB support

# Monitoring
APScheduler      # Scheduled tasks
requests         # API calls for sentiment/news

# Logging
python-json-logger  # Structured logging
```

---

## Next Steps (This Week)

1. **Create Kill-Switch System** (2 days)
   - `app/safety/kill_switch.py`
   - Integration tests
   - Manual trigger UI

2. **Build ML Prediction Engine** (3 days)
   - Train XGBoost model on last 2y data
   - Create `PredictionEngine` class
   - Integration into signal flow

3. **Expand Feature Engineering** (2 days)
   - Add MACD, Stochastic, Vortex
   - Put-call ratio computation
   - Feature vector aggregation

4. **Enhance Options Strategy Selector** (2 days)
   - Phase 2 logic (IV-based selection)
   - Integration with risk manager

5. **Create Monitoring Dashboard** (1 day)
   - Real-time metrics
   - Daily reporting

---

## Success Definition

**Phase 2 "READY FOR PHASE 3" Criteria:**
- ✅ Kill-switch operational & tested
- ✅ ML model integrated with > 55% accuracy
- ✅ Options strategies working (spreads + naked)
- ✅ 2 weeks of profitable live paper trading
- ✅ All risk controls passing stress tests
- ✅ Automated daily reports & alerts
- ✅ Zero uncontrolled losses in live mode
- ✅ Execution speed < 2 seconds consistently

**Estimated Completion:** July 2026

---

## Version Control & Tracking

```
Branch: feature/phase-2-ai-upgrade
Status: Active Development
Target Merge: June 20, 2026
Code Review: Mandatory
Test Coverage: > 80%
```

---

**Document Owner:** GreeksMaster Dev Team  
**Last Updated:** June 10, 2026  
**Next Review:** June 15, 2026
