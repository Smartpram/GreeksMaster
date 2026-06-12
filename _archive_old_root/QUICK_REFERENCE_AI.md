# QUICK START: PHASE 2 IMPLEMENTATION GUIDE

**For:** GreeksMaster Team  
**Date:** June 10, 2026  
**Objective:** Convert trading system to AI-Enabled Options Trading System

---

## 📊 PHASE MAPPING SUMMARY

Your existing system is **70% aligned** with spec requirements:

```
PHASE 1: Paper Trading       ✅ 90% COMPLETE
PHASE 2: Controlled Live     ⏳ 60% COMPLETE → Needs work
PHASE 3: Fully Autonomous    ❌ 0% (Future)
```

---

## 🔴 PRIORITY 1: DO IMMEDIATELY (This Week)

### 1. Kill-Switch System ✅ CREATED
**File:** `app/safety/kill_switch.py` (500+ lines)

**What it does:**
- Emergency stop button for trading
- Automatic triggers (losses, heartbeat loss, errors)
- Cancels all orders + closes positions
- Requires manual reset

**How to integrate:**
```python
# In app/engine/trading_engine.py
from app.safety.kill_switch import KillSwitchManager

self.kill_switch = KillSwitchManager(
    executor=self.executor,
    risk_manager=self.risk_manager
)

# Before EVERY trade:
if self.kill_switch.is_active():
    raise Exception("Trading halted")

# Register monitors
self.kill_switch.register_monitor('drawdown', monitor_daily_drawdown)
self.kill_switch.register_monitor('losses', monitor_consecutive_losses)
self.kill_switch.start_monitoring()
```

**Status:** COMPLETE - Ready to integrate

---

### 2. ML Prediction Engine ✅ CREATED
**File:** `app/ml_models/prediction_engine.py` (400+ lines)

**What it does:**
- Makes predictions: UP/DOWN, expected move %, volatility
- Outputs confidence scores
- Can load multiple ML models
- Batch predictions supported

**How to use:**
```python
from app.ml_models.prediction_engine import PredictionEngine

engine = PredictionEngine(
    model_paths={
        'price_direction': 'models/price_direction_xgb.pkl',
        'expected_move': 'models/expected_move_xgb.pkl'
    }
)

# Get prediction
pred = engine.predict(features_df, symbol="NIFTY")

# Check if strong signal
if pred.is_strong_signal(confidence_threshold=0.65):
    print(f"Direction: {pred.direction.value}")  # UP or DOWN
    print(f"Expected move: {pred.expected_move_pct}%")
    print(f"Confidence: {pred.overall_confidence:.0%}")
```

**Status:** COMPLETE - Ready to train models

**Next Step:** Create model training script (by June 12)

---

### 3. Feature Engine Expansion ⏳ START NOW
**File:** Create `app/feature_engine.py`

**What to add:**
- MACD indicator
- Stochastic RSI
- Vortex Index
- Put-call ratio (from options data)
- Feature vector aggregator

**Code template:**
```python
# app/feature_engine.py
class FeatureEngine:
    def compute_all_features(self, symbol):
        return {
            'ma_ratio': self._ma_ratio(),
            'rsi': self._rsi(14),
            'macd': self._macd(),           # NEW
            'stoch_rsi': self._stoch_rsi(), # NEW
            'atr': self._atr(14),
            'bb_position': self._bollinger_position(),
            'volume_ratio': self._volume_ratio(),
            'put_call_ratio': self._put_call_ratio(),  # NEW
            'momentum': self._momentum(5)
        }
```

**Timeline:** 2 days (by June 12)

---

## 🟡 PRIORITY 2: THEN DO (Next 5 Days)

### 4. Enhanced Execution System
**File:** Enhance `app/services/signal_executor.py`

**Add:**
- Retry logic (up to 3 times)
- Order state tracking
- Timeout handling (10s)
- Error recovery

**Why:** Current execution too simplistic for live trading

---

### 5. Options Strategy - Phase 2 Logic
**File:** Enhance `app/options_strategy_selector.py`

**Phase 2 Rules:**
```
IF IV > 75% (high volatility)
  → Use SPREADS (sell premium)

IF IV < 25% (low volatility)  
  → Use LONG OPTIONS (buy premium)

IF expected_move > 3%
  → Use WIDE strategies

IF expected_move < 1%
  → Use TIGHT strategies
```

**Why:** Move beyond simple ATM-only selection

---

### 6. Performance Monitoring
**Files:** Create `app/monitoring/`

**Add:**
- Real-time metrics (win rate, profit factor, Sharpe ratio)
- Daily performance reports
- Model accuracy tracking
- Email alerts

---

## 📁 FILES YOU NEED TO READ/UNDERSTAND

1. **Mapping Document:** `PHASE_MIGRATION_MAPPING.md`
   - Shows what you have vs what's needed
   - Gap analysis for each module

2. **Checklist:** `PHASE_2_IMPLEMENTATION_CHECKLIST.md`
   - Day-by-day breakdown
   - Success criteria
   - Testing strategy

3. **This Document:** `QUICK_REFERENCE_PHASE_2.md`
   - Quick overview (this file)

---

## 🎯 PHASE 2 SUCCESS CRITERIA

**By July 1, 2026:**

✅ Kill-switch working + tested  
✅ ML model integrated (accuracy > 55%)  
✅ Options strategies working (spreads included)  
✅ 2 weeks paper trading: profitable  
✅ Daily reports automated  
✅ All monitoring alerts working  
✅ 0 uncontrolled losses  

---

## 🚀 QUICK INTEGRATION EXAMPLE

Here's how to wire everything together in your `TradingEngine`:

```python
from app.safety.kill_switch import KillSwitchManager, monitor_daily_drawdown
from app.ml_models.prediction_engine import PredictionEngine
from app.feature_engine import FeatureEngine

class TradingEngine:
    def __init__(self, ...):
        # ... existing setup ...
        
        # NEW: Kill-switch
        self.kill_switch = KillSwitchManager(
            executor=self.executor,
            risk_manager=self.risk_manager
        )
        self.kill_switch.register_monitor('drawdown', monitor_daily_drawdown)
        self.kill_switch.start_monitoring()
        
        # NEW: ML Prediction
        self.predictor = PredictionEngine(
            model_paths={
                'price_direction': 'app/ml_models/models/price_direction.pkl',
                'expected_move': 'app/ml_models/models/expected_move.pkl'
            }
        )
        
        # NEW: Feature engine
        self.feature_engine = FeatureEngine(data_provider=self.data)
    
    def run_cycle(self):
        # Check kill-switch FIRST
        if self.kill_switch.is_active():
            logger.warning("Trading halted - kill-switch active")
            return
        
        # Stage 1: Generate signals
        signals = self._stage_1_signal_generation()
        
        # Stage 2: Get ML predictions
        for signal in signals:
            features = self.feature_engine.compute_all_features(signal['symbol'])
            pred = self.predictor.predict(features, signal['symbol'])
            
            # Combine rule-based + ML
            signal['ml_direction'] = pred.direction.value
            signal['ml_confidence'] = pred.overall_confidence
            signal['ml_expected_move'] = pred.expected_move_pct
        
        # Stage 3: Options strategy selection (Phase 2 logic)
        for signal in signals:
            strategy = self._options_strategy_selector.select_strategy(
                signal=signal,
                option_chain=self._get_option_chain(signal['symbol']),
                market_metrics={
                    'iv_percentile': self._get_iv_percentile(signal['symbol']),
                    'expected_move': signal['ml_expected_move']
                }
            )
            signal['strategy'] = strategy
        
        # Stage 4: Execute (with kill-switch check)
        for signal in signals:
            try:
                if self.kill_switch.is_active():
                    break
                result = self.executor.place_order(signal['strategy'])
            except Exception as e:
                logger.error(f"Execution error: {e}")
                # Kill-switch might auto-trigger here
        
        return metrics
```

---

## 📋 TESTING CHECKLIST

Before live trading, verify:

```
Kill-Switch:
☐ Manual trigger works
☐ Auto-trigger on drawdown works
☐ Orders actually get cancelled
☐ Positions actually get closed
☐ Manual reset required (not automatic)

ML Engine:
☐ Predictions load without error
☐ Confidence scores between 0-1
☐ Direction is UP or DOWN
☐ Expected move is positive %

Feature Engine:
☐ All indicators calculated
☐ No NaN values
☐ Feature vector format correct
☐ Real-time updates working

Integration:
☐ Signal → Prediction → Strategy → Execution works end-to-end
☐ Kill-switch can stop execution mid-cycle
☐ Performance monitoring reports working
☐ All logs present
```

---

## 🔗 KEY INTEGRATION POINTS

| Module | File | Integration Task |
|--------|------|-------------------|
| Kill-Switch | `app/safety/kill_switch.py` | Add to `trading_engine.py` |
| Prediction | `app/ml_models/prediction_engine.py` | Load models; call in Stage 2 |
| Features | `app/feature_engine.py` | Compute before prediction |
| Options Strategy | `app/options_strategy_selector.py` | Use IV/move in selection |
| Executor | `app/services/signal_executor.py` | Add retry logic |
| Monitoring | `app/monitoring/` | Aggregate metrics |

---

## 📞 TROUBLESHOOTING

**Problem: Kill-switch not triggering**
- Check monitors are registered
- Check monitoring thread is running
- Verify RiskManager has `get_portfolio_state()` method

**Problem: ML predictions all NEUTRAL**
- Check models loaded in `PredictionEngine.__init__`
- Verify model paths correct
- Check feature vector not empty

**Problem: "Model file not found"**
- Ensure you run model training script
- Models should be at `app/ml_models/models/*.pkl`
- Check paths in PredictionEngine config

**Problem: Kill-switch activated but positions not closed**
- Check Executor has `close_all_positions()` method
- Verify Breeze API connectivity
- Check error logs for API issues

---

## 📈 EXPECTED OUTCOMES - PHASE 2

**Timeline:** 3 weeks (June 10 - July 1)

**Week 1:**
- Kill-switch ✅ DONE
- ML engine ✅ DONE
- Features ⏳ IN PROGRESS
- Integration starts ⏳ IN PROGRESS

**Week 2:**
- Execution enhanced
- Options strategy Phase 2
- Monitoring setup
- Unit tests

**Week 3:**
- Integration tests
- Paper trading (2 weeks)
- Performance validation
- Phase 2 COMPLETE ✅

**After Phase 2:**
- ✅ Ready for Phase 3 (Fully Autonomous)
- ✅ Sentiment integration
- ✅ Advanced multi-leg strategies
- ✅ Ensemble models + online learning

---

## 🎓 LEARNING RESOURCES

**For Kill-Switch:**
- See `app/safety/kill_switch.py` - full examples in `if __name__ == "__main__"`

**For ML Engine:**
- See `app/ml_models/prediction_engine.py` - full examples in `if __name__ == "__main__"`

**For Testing:**
- Look at `PHASE_2_IMPLEMENTATION_CHECKLIST.md` - test templates

---

## 💡 BEST PRACTICES - PHASE 2

1. **Test Early, Test Often**
   - Each component tested in isolation first
   - Integration tests before live

2. **Small Positions First**
   - Start with ₹10k capital in paper trading
   - Verify all systems before scaling

3. **Monitor Everything**
   - Kill-switch status
   - Model accuracy
   - Execution speed
   - Daily P&L

4. **Keep it Simple**
   - Don't add complexity until Phase 2 proves itself
   - Use rules + ML together, not just ML
   - Phase 3 is where advanced AI goes

5. **Log Everything**
   - Every decision should be logged
   - Every error should be logged
   - Every execution should be logged
   - Audit trail is critical

---

## 📞 QUICK HELP

**Q: When should I start Phase 3?**  
A: Only after Phase 2 has 4+ weeks of profitable live data

**Q: Can I use kill-switch for manual trading too?**  
A: Yes! Manual trigger is always available

**Q: What if ML models aren't accurate?**  
A: Use ensemble (rules + ML together) - don't rely on ML alone

**Q: Do I need to retrain models?**  
A: Yes, weekly after Phase 2 goes live

**Q: How do I know Phase 2 is complete?**  
A: See success criteria section above

---

## 📞 NEXT STEPS - STARTING NOW

```
TODAY (June 10):
  1. Read this document
  2. Read PHASE_MIGRATION_MAPPING.md
  3. Create app/ml_models/train_models.py
  4. Create app/feature_engine.py
  
TOMORROW (June 11):
  1. Train models on historical data
  2. Export models to app/ml_models/models/
  3. Start feature engine development
  4. Begin kill-switch integration
  
BY JUNE 12:
  1. Features expansion complete
  2. Models trained & tested
  3. Kill-switch integrated into trading_engine
  4. Prediction engine integrated into signal flow

BY JUNE 14:
  1. Enhanced execution complete
  2. Options strategy Phase 2 complete
  3. Unit tests passing
  4. Ready for integration tests

BY JUNE 21:
  1. All systems integrated
  2. Paper trading live (small capital)
  3. Monitoring collecting data
  4. Bug fixes ongoing

BY JULY 1:
  1. Phase 2 COMPLETE
  2. 2+ weeks profitable trading
  3. All metrics validated
  4. Ready for Phase 3
```

---

**Questions? See PHASE_MIGRATION_MAPPING.md or PHASE_2_IMPLEMENTATION_CHECKLIST.md**

**Version:** 1.0  
**Last Updated:** June 10, 2026  
**Status:** ACTIVE
