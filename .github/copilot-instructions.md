# Copilot Mode: Low-Token Trading App

## Current Phase: Phase 2 Extended - Range Policy (COMPLETE ✅)

### Rules
- concise responses
- default = code only
- no explanations unless asked
- no repetition, no filler

### Project Foundation
- Python + Flask app
- ICICIDirect Breeze API
- algo trading (trend-following with SMA20 crossover)
- indicators: RSI, MA, volume
- **NEW:** Market Sentiment Gate (NIFTY-based macro filtering)
- **NEW:** Range Policy (capital preservation in sideways markets)

### Architecture (5-Stage Pipeline)
```
Stage 1: SCREENER (SMA20 crossover) → Generates buy signals
         ↓
Stage 2: VALIDATION & RISK (Range Policy + Sentiment Gate + AI Validator)
         ├─ Range Policy Check (NO TRADE in RANGE regime)
         │  └─ Detects: ATR low | ADX low | BB squeeze | Persistence
         ├─ Market Sentiment Evaluator (assesses NIFTY trend)
         ├─ Production Validator (approves/rejects based on sentiment)
         └─ Risk Manager (adjusts position size/stops)
         ↓
Stage 3: ORDER EXECUTION → Places trades if all gates pass
         ↓
Stage 4: POSITION MANAGEMENT → Tracks open trades, PnL
         ↓
Stage 5: EXIT STRATEGY → Closes on SMA20 breakdown or stop-loss
```

### Key Files & Responsibilities
| File | Purpose | Status |
|------|---------|--------|
| `backtest_trading_engine_with_ai.py` | Main backtest engine with gates | ✅ ACTIVE |
| `app/market_sentiment_gate.py` | Sentiment evaluator + Range Policy check | ✅ INTEGRATED |
| `app/range_policy.py` | Range detection & policy enforcement | ✅ NEW |
| `app/ai_signal_validator.py` | AI confidence filtering | ✅ INTEGRATED |
| `PHASE_2_TEST_RESULTS.md` | Test results & findings | ✅ GENERATED |
| `RANGE_POLICY_IMPLEMENTATION.md` | Range Policy docs | ✅ NEW |

### Range Policy Logic
```
Price Data → Range Detector
   ├─ Check ATR (< 1.5% = low vol)
   ├─ Check ADX (< 25 = weak trend)
   ├─ Check BB width (squeezed = low vol)
   ├─ Track persistence bars
   └─ Composite score ≥ 0.6 = RANGE
         ↓
   Persistence < 5 bars → ALLOW with 50% size (early)
   Persistence ≥ 5 bars → BLOCK, size = 0% (confirmed)
         ↓
   SentimentDecision.action = BLOCK → Trade rejected
```

### Sentiment Gate Logic
```python
# Updated Decision Flow
Range Policy Check (FIRST)
  ├─ If RANGE confirmed → BLOCK, DONE
  └─ If trending → continue

Index Trend (MA20 vs MA200) + Volatility (ATR)
  ├─ Score > +0.2  → BULLISH → ALLOW (100% position)
  ├─ Score < -0.2  → BEARISH → BLOCK (0% position)
  └─ -0.2 to +0.2  → NEUTRAL → ALLOW or CAUTION (100% or 50%)
```

### Recent Discoveries (Phase 2 Complete)
- ✅ Range Policy detects sideways markets: ATR, ADX, Bollinger Bands
- ✅ Persistence mechanism prevents false RANGE detection (5-bar threshold)
- ✅ Integration with sentiment gate: Range check happens first in Stage 2
- ✅ Capital preservation mode: 0% position size during RANGE
- ✅ Early RANGE detection: 50% position size for first 5 bars
- ⚠️ Option B (range strategy) not implemented - using default NO_TRADE
- ⏳ Next: Backtest full period with Range Policy enabled

### Constraints
- preserve API contracts
- preserve SMA20 baseline strategy (it's sound)
- Range Policy default = NO TRADE (capital preservation)
- Range strategy (Option B) only if edge proven
- avoid over-optimization on historical data

### Output Format
- code | diff | test results only
- no long explanations unless asked
- bullet points OK for findings
- include range policy decisions in backtest output

### Next Work (Priority Order)
1. **Backtest full period (2024-2025)** with Range Policy enabled
2. **Compare metrics** (with vs without Range Policy)
3. **Verify capital preservation** during known RANGE periods (Jul-Sep 2024)
4. **Update test results** in test reports
5. **Phase 3:** Fine-tune RANGE thresholds if needed
6. **Phase 4:** Implement & prove Option B (range strategy) if beneficial
7. **Phase 5:** Live deployment with regime monitoring

### Goal
Build profitable trend-following algo by:
- ✅ Fixing metrics (done)
- ✅ Testing timeframes (done)
- ✅ Implementing sentiment gate (done)
- ✅ Implementing range policy (done)
- ⏳ Backtest range policy integration
- ⏳ Achieve 50%+ win rate with capital preservation during sideways
- ⏳ <1% drawdown or range policy enabled

