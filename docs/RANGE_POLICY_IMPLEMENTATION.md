# RANGE POLICY IMPLEMENTATION
## Capital Preservation in Sideways Markets

**Status**: ✅ IMPLEMENTED  
**Date**: 2026-06-01  
**Phase**: Phase 2 Extended (Market Sentiment Gate Enhancement)

---

## Executive Summary

**Key Principle**: *"Trade only with edge. Else stand down."*

### Problem
- System optimized for **trending markets** (SMA20 crossover momentum)
- Loses capital in **RANGE/sideways markets** (whipsaws, false signals)
- Need capital preservation mode when market conditions don't suit trend strategy

### Solution
Implement **Range Policy** (Option A: Default NO TRADE) in Stage 2 validation

### Impact
- **During RANGE**: No trades (0% position size)
- **During TREND**: Execute normally (100% position size)
- **Early RANGE**: Reduced trades (50% position size)

---

## Architecture Integration

### Stage 2: Validation & Risk Gates
```
Trade Signal (SMA20 from Stage 1)
         ↓
    [Stage 2 VALIDATION]
         ├─ Range Policy Check ← NEW
         │  └─ Detect RANGE regime → Block/Allow
         │
         ├─ Market Sentiment Gate
         │  └─ Sentiment (BULLISH/NEUTRAL/BEARISH) → ALLOW/CAUTION/BLOCK
         │
         └─ AI Signal Validator
            └─ Confidence scoring
         ↓
    [Decision: Execute / Caution / Block]
```

### Implementation Flow

**1. Range Detection** (`range_policy.py: RangeDetector`)
```python
detect_range(df) → RangeContext
├─ Method 1: ATR-based (< 1.5% daily range = RANGE)
├─ Method 2: Bollinger Bands squeeze
├─ Method 3: ADX low (< 25 = weak trend)
└─ Composite score ≥ 0.6 = RANGE detected
```

**2. Persistence Confirmation**
- Bars in RANGE tracked: `context.persistence_bars`
- Threshold: 5 bars minimum
- Early detection (< 5 bars): Allow with 50% size
- Confirmed RANGE (≥ 5 bars): Block trades (0% size)

**3. Sentiment Gate Integration** (`market_sentiment_gate.py`)
```python
assess_market(market_data, current_date)
├─ Step 1: Check Range Policy (pre-filter)
│  └─ If RANGE confirmed → return BLOCK decision
├─ Step 2: If not RANGE → eval sentiment normally
└─ Decision: ALLOW/CAUTION/BLOCK
```

---

## Key Components

### 1. `app/range_policy.py` (NEW FILE)

#### RangeDetector
```python
detector = RangeDetector(
    atr_period=14,
    bb_period=20,
    bb_std=2.0,
    adx_period=14,
    persistence_threshold=5
)

context = detector.detect_range(df)
# Returns: RangeContext
#   - is_range: bool
#   - confidence: 0.0-1.0
#   - volatility: ATR as % of price
#   - upper_bound / lower_bound: Support/resistance
#   - persistence_bars: Bars confirmed RANGE
#   - detection_method: ADX_LOW | ATR_LOW | BOLLINGER_BANDS | PRICE_ACTION
```

#### RangePolicyEvaluator
```python
evaluator = RangePolicyEvaluator(
    active_policy=RangePolicy.NO_TRADE  # Option A (default)
)

decision = evaluator.evaluate(df, signal_type='BUY')
# Returns: RangePolicyDecision
#   - should_trade: bool
#   - policy: RangePolicy enum
#   - position_size_factor: 0.0-1.0
#   - stop_loss_tightness: 0.5-1.0
#   - rationale: str

# Apply adjustments
adj_size, adj_stop = evaluator.apply_adjustments(
    base_size=100,
    base_stop_loss=3.0,
    decision=decision
)
```

#### Decision Logic

**NOT in RANGE (Trending)**
```
Decision: should_trade=True, size=1.0, stops=1.0
Rationale: "Trending market detected. Full execution."
```

**Early RANGE (< 5 bars persistence)**
```
Decision: should_trade=True, size=0.5, stops=0.8
Rationale: "RANGE detected but not persistent. Allowing with REDUCED size."
```

**Confirmed RANGE (≥ 5 bars persistence)**
```
Decision: should_trade=False, size=0.0, stops=1.0
Rationale: "✗ RANGE confirmed. Capital preservation mode: NO TRADES."
```

### 2. Market Sentiment Gate Updates

**File**: `app/market_sentiment_gate.py`

**Method**: `assess_market()` - Enhanced with Range Policy check
```python
def assess_market(self, market_data, current_date, stock_sector=None):
    # Step 1: Check Range Policy first (Stage 2 Pre-Filter)
    range_decision = self._check_range_policy(market_data, current_date)
    if range_decision:
        return range_decision  # BLOCK if RANGE detected
    
    # Step 2: Sentiment evaluation (original logic)
    # ... MA20 vs MA200, volatility, etc.
```

**New Method**: `_check_range_policy()`
- Lazy-loads Range Policy module (avoid circular imports)
- Detects RANGE in index/market data
- Returns BLOCK decision if RANGE confirmed
- Returns None if trending (sentiment eval proceeds)

---

## Integration with Backtest Engine

### `backtest_trading_engine_with_ai.py`

**Stage 2 Validation Loop** (existing code):
```python
# Existing sentiment gate call
sentiment_decision = sentiment_gate.assess_market(
    market_data=nifty_data,
    current_date=date_str,
    stock_sector=sector
)

# Already integrated!
# Range Policy check happens INSIDE assess_market()
# No code changes needed in backtest engine
```

**What happens**:
1. Screen finds SMA20 crossover BUY signal
2. Stage 2 calls `assess_market()` for validation
3. Range Policy check runs (inside sentiment evaluator)
4. If RANGE: `sentiment_decision.action = BLOCK` → Trade rejected
5. If TREND: `sentiment_decision.action = ALLOW/CAUTION` → Trade evaluated

**Logging Output**:
```
[INFO] 📊 DAILY BACKTEST: 2024-06-01
[WARNING] 🔄 RANGE POLICY TRIGGERED: Market in ADX_LOW regime (5 bars, confidence=0.68). 
           Blocking new trades for capital preservation.
[INFO] Trade SIGNAL but BLOCKED by Range Policy: INFY
```

---

## Range Detection Methods

### Method 1: ATR-Based (Volatility)
```python
ATR < 1.5% of current price
= Very tight daily ranges
= No directional opportunity
```

### Method 2: Bollinger Bands Squeeze
```python
BB Width < 1.5x ATR
= Bands compressed
= Low volatility environment
```

### Method 3: ADX (Average Directional Index)
```python
ADX < 25
= Weak or no trend
= Price oscillating around support/resistance
```

**Primary Method Selection** (in order):
1. If ADX < 25 → Use ADX_LOW
2. Else if ATR < threshold → Use ATR_LOW
3. Else if BB squeeze → Use BOLLINGER_BANDS
4. Else → Use PRICE_ACTION (support/resistance bounces)

---

## Policy Options

### Option A: NO_TRADE (DEFAULT - IMPLEMENTED)
- **In RANGE**: 0% position size
- **Capital**: Preserved
- **Trades**: Blocked entirely
- **Rationale**: System has no proven edge in ranges
- **Risk**: Miss consolidation breakouts (minimal, trend will resume)

### Option B: RANGE_STRATEGY (NOT IMPLEMENTED)
- **In RANGE**: 50-100% position size
- **Signals**: Mean reversion (RSI, Bollinger Bands)
- **Stops**: Tight (2-3% instead of 3-4%)
- **Rationale**: If proven mean reversion strategy exists
- **Status**: "To be implemented after proving edge"
- **Current Fallback**: Uses Option A (NO_TRADE)

---

## Configuration & Thresholds

### Range Detector Config
```python
RangeDetector(
    atr_period=14,                    # Standard
    bb_period=20,                     # SMA20 + 2 std
    bb_std=2.0,                       # Standard
    adx_period=14,                    # Standard
    persistence_threshold=5           # Bars to confirm
)
```

### Range Policy Evaluator Config
```python
RangePolicyEvaluator(
    active_policy=RangePolicy.NO_TRADE,  # Default
    detector=RangeDetector(...),
    persistence_threshold=5
)
```

### Sentiment Gate Config
```python
MarketSentimentEvaluator(
    index_ma_short=20,
    index_ma_long=200,
    volatility_threshold=0.03,
    check_range_policy=True  # NEW - enable Range Policy
)
```

---

## Testing & Validation

### Unit Tests
Run Range Policy tests:
```bash
python app/range_policy.py
# Tests:
# 1. Scenario 1: Trending market (should allow trades)
# 2. Scenario 2: Range market (should block trades after 5 bars)
# 3. Scenario 3: Position size adjustments
```

### Integration Testing
Backtest with Range Policy enabled:
```bash
python backtest_trading_engine_with_ai.py \
    --start 2024-01-01 \
    --end 2024-12-31 \
    --enable-range-policy
```

**Expected Results**:
- Fewer trades during sideways periods (2024-07 to 2024-09)
- Lower max drawdown
- Better win rate (filtered out low-edge trades)
- Capital preserved during RANGE periods

### Backtest Metrics to Track
```
Metric                  | Without Range Policy | With Range Policy
Avg Holding Days        | 1.5-2.0 d           | 2.0-2.5 d (longer trends only)
Win Rate (%)            | 40-45%              | 50-55% (bias toward good trades)
Max Drawdown (%)        | 25-35%              | 20-25% (capital preserved)
Trades During RANGE     | 30-40               | 5-10 (mostly filtered)
Profit Factor           | 1.0-1.2             | 1.2-1.4 (less noise)
```

---

## Safeguards & Risk Mitigation

### 1. False RANGE Detection
**Risk**: Misclassify breakout as RANGE early
**Mitigation**:
- Persistence threshold = 5 bars
- Allow 50% trades if < 5 bars (early detection)
- Require confirmation before full block

### 2. Breakout Misses
**Risk**: Block trades just before trend resumes
**Mitigation**:
- Reverting to TREND regime immediately unlocks trades
- No lag (regime monitor updates daily)
- Breakout detected via ADX rise or price action

### 3. Rapid Regime Switching
**Risk**: Switch between RANGE/TREND repeatedly → whipsaws
**Mitigation**:
- Persistence threshold (5 bars) prevents noise trading
- Policy stays stable for 5+ bars minimum
- Regime only changes on sustained evidence

### 4. Strategy Switching Risk
**Risk**: Switching to range strategy without edge → drawdown
**Mitigation**:
- Option B (range strategy) NOT implemented
- Default Option A (NO TRADE) used
- Will implement Option B only after backtesting proves edge

---

## Monitoring & Diagnostics

### Log Output Examples

**[NORMAL TREND]**
```
INFO  | assess_market() for 2024-05-01
DEBUG | Range detection: ATR=1.05%, ADX=35.2 → NOT in RANGE
INFO  | Sentiment: BULLISH → ALLOW
```

**[RANGE DETECTED - EARLY]**
```
WARNING | Range detected (1 bar, confidence=0.61, method=ATR_LOW)
INFO   | Allowing with 50% position size (early detection)
```

**[RANGE CONFIRMED - BLOCKED]**
```
WARNING | 🔄 RANGE POLICY TRIGGERED: Market in ADX_LOW regime (5 bars, confidence=0.72)
WARNING | Blocking new trades for capital preservation
ERROR  | Trade SIGNAL but BLOCKED: INFY (SMA20 crossover)
```

**[BREAKOUT DETECTED]**
```
WARNING | Regime change: RANGE → TRENDING
INFO   | ADX risen to 28.5 (from 22.3)
INFO   | Resuming trades (RANGE period ended)
```

### Diagnostic Commands
```python
# Get range context
context = detector.detect_range(df)
print(f"Is Range: {context.is_range}")
print(f"Method: {context.detection_method.value}")
print(f"Confidence: {context.confidence:.2f}")
print(f"Persistence: {context.persistence_bars} bars")

# Get policy decision
decision = evaluator.evaluate(df, 'BUY')
print(f"Should Trade: {decision.should_trade}")
print(f"Position Size Factor: {decision.position_size_factor}")
print(f"Rationale: {decision.rationale}")
```

---

## Next Steps & Future Work

### Phase 2 Completion ✅
- [x] Implement Range Detection (ATR, ADX, Bollinger)
- [x] Create Range Policy Evaluator
- [x] Integrate with Market Sentiment Gate
- [x] Add safeguards (persistence, early detection)
- [x] Document implementation

### Phase 3: Validation (NEXT)
- [ ] Backtest full period (2024-2025) with Range Policy enabled
- [ ] Compare metrics: With vs Without
- [ ] Verify capital preservation during 2024-07 to 2024-09 (known RANGE period)
- [ ] Update test results in `PHASE_2_TEST_RESULTS.md`

### Phase 4: Option B Range Strategy (FUTURE)
- [ ] Implement mean reversion signals (RSI overbought/oversold)
- [ ] Add Bollinger Bands bounce detection
- [ ] Backtest range strategy vs. NO_TRADE
- [ ] Prove > 50% win rate in range conditions
- [ ] Only then enable Option B in production

### Phase 5: Production Deployment (FUTURE)
- [ ] Deploy to live trading with Range Policy active
- [ ] Monitor regime transitions in real-time
- [ ] Generate daily regime reports
- [ ] Track capital preservation success

---

## File References

### New Files
- `app/range_policy.py` - Main Range Policy implementation
  - `RangeDetector` class
  - `RangePolicyEvaluator` class
  - `RangeContext`, `RangePolicyDecision` dataclasses
  - Unit tests included

### Modified Files
- `app/market_sentiment_gate.py`
  - Enhanced `assess_market()` with Range Policy check
  - Added `_check_range_policy()` method
  - Updated docstrings

### No Changes Needed
- `backtest_trading_engine_with_ai.py` - Integration automatic
- `app/strategies/strategy_regime_monitor.py` - Separate concern

---

## Key Principles (Summary)

1. **Capital Preservation** > Aggressive Growth
2. **Trade only with edge** → RANGE is no-edge for our system
3. **Persistence before decision** → 5 bars confirms RANGE
4. **Fail-safe default** → NO_TRADE (Option A) not proven strategies
5. **Rapid recovery** → Trend detected = immediate trade resumption

---

## Questions & Support

**Q: Will we miss opportunities during RANGE?**  
A: Yes, but RANGE has low volatility and our system has no edge there. Low opportunity cost.

**Q: What if we misclassify early?**  
A: We allow 50% trades for first 5 bars. Positions sized down, not blocked.

**Q: When do we switch back to TREND?**  
A: Automatically when regime detector sees ADX > 25 or volatility expands. Same day.

**Q: Can we optimize thresholds?**  
A: Yes, adjust `persistence_threshold` or ADX level. Requires re-backtest. Currently conservative.

**Q: What about different timeframes?**  
A: Current implementation daily. For intraday (5min/15min), adjust periods (e.g., ADX with 5-period).

---

**Implementation Status**: ✅ READY FOR BACKTEST VALIDATION
