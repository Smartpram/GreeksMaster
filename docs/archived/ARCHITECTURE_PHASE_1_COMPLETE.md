# Complete Architecture: From Signals to Execution

## Overview

Three-layer architecture for automated options trading:

```
Layer 1: Signal Engine (Pure Data Science)
         ├─ Stock screener (backtest_indian_stocks_real_data.py)
         └─ Signal normalizer (signal_normalizer.py)
                ↓
Layer 2: Strategy Selector (Pure Logic)
         ├─ Options strategy selection (options_strategy_selector.py)
         └─ Pre-trade risk checks
                ↓
Layer 3: Execution Engine (Broker-Facing)
         ├─ Breeze API authentication
         ├─ Chain selection & contract filtering
         ├─ Order placement & management
         └─ Position monitoring (TODO - Phase 3)
```

---

## Layer 1: Signal Engine ✅ (COMPLETE)

### A. Stock Screener
**File:** `backtest/backtest_indian_stocks_real_data.py`

Analyzes real Indian stock data and generates signals:
- **Input:** Real NSE stock prices (INFY, TCS, AXIS, etc.) from yfinance
- **Logic:**
  - BREAKOUT: Price > SMA-20 with volume confirmation
  - MOMENTUM: Positive trend + low volatility
  - REVERSAL: Consolidation with high volume
- **Output:** Stock signals with confidence scores

### B. Signal Normalizer
**File:** `app/signal_normalizer.py` ✅ NEW

Converts stock screener output into normalized, options-ready signals:

```python
class NormalizedSignal:
    signal_id: str              # Unique ID
    symbol: str                 # AXIS, INFY, etc.
    signal_type: str            # BREAKOUT, MOMENTUM, REVERSAL
    direction: str              # BULLISH, BEARISH, NEUTRAL
    confidence: int             # 0-100
    confidence_band: str        # LOW, MEDIUM, HIGH, VERY_HIGH
    spot_price: float           # Current price
    features: Dict              # Technical metrics
    expected_move_pct: float    # ATR-based move estimate
    holding_period_days: int    # Recommended hold duration
    volatility: float           # Annual volatility
    atr: float                  # Average True Range
```

**Key Features:**
- ✅ Separates data science from broker logic
- ✅ Normalized format (no Breeze dependencies)
- ✅ Confidence bands (LOW/MEDIUM/HIGH/VERY_HIGH)
- ✅ Technical features extracted
- ✅ Expected move calculated from ATR
- ✅ Holding period determined intelligently
- ✅ Exportable to JSON for analysis

**Example Output:**
```json
{
  "signal_id": "AXIS_BREAKOUT_2026-06-09",
  "symbol": "AXIS",
  "signal_type": "BREAKOUT",
  "direction": "BULLISH",
  "confidence": 70,
  "confidence_band": "HIGH",
  "spot_price": 1292.40,
  "features": {
    "sma20_diff_pct": 1.79,
    "atr": 24.54,
    "trend_pct_20d": 2.9,
    "volatility": 0.20
  },
  "expected_move_pct": 1.9,
  "holding_period_days": 5
}
```

---

## Layer 2: Strategy Selector ✅ (COMPLETE)

### File: `app/options_strategy_selector.py` ✅ NEW

Converts normalized signals into executable strategy recommendations.

**Selection Logic:**

```python
IF direction == BULLISH AND confidence >= 70:
    → BULL_CALL_SPREAD  (defined risk, lower cost, capital efficient)
    
ELIF direction == BULLISH AND confidence >= 50:
    → LONG_CALL  (simple directional, good for learning)
    
ELIF direction == BEARISH AND confidence >= 70:
    → BEAR_PUT_SPREAD  (defined risk, income)
    
ELIF direction == BEARISH AND confidence >= 50:
    → LONG_PUT  (simple directional)
    
ELIF volatility > 0.35 AND confidence >= 60:
    → IRON_CONDOR  (FLAGGED FOR REVIEW - risk controls needed)
    
ELSE:
    → NO_TRADE  (wait for better setup)
```

**Output: StrategyRecommendation**

```python
class StrategyRecommendation:
    strategy_id: str            # Unique ID
    signal_id: str              # Links to signal
    strategy_type: str          # LONG_CALL, BULL_CALL_SPREAD, etc.
    legs: List[StrategyLeg]     # Multi-leg definition
    
    # Risk parameters
    max_risk_per_trade: float   # Dollar or % limit
    max_premium_outlay: float   # Budget cap
    
    # Exit rules
    profit_target_pct: float    # 50% = exit at half max profit
    stop_loss_pct: float        # 30% = exit at loss
    time_stop_days: int         # 3 = exit if thesis fails
    
    # Pre-trade checks (to be verified by execution layer)
    pre_trade_checks: Dict      # Checklist for broker layer
```

**Example: Bull Call Spread for AXIS**

```json
{
  "strategy_type": "BULL_CALL_SPREAD",
  "direction": "BULLISH",
  "legs": [
    {
      "position_type": "LONG_CALL",
      "strike_selection": "ATM",
      "expiry_dte": 7,
      "quantity": 1
    },
    {
      "position_type": "SHORT_CALL",
      "strike_selection": "OTM",
      "expiry_dte": 7,
      "quantity": 1
    }
  ],
  "max_risk_per_trade": 25.85,
  "profit_target_pct": 50.0,
  "stop_loss_pct": 100.0,
  "holding_period_days": 5
}
```

**Rationale:**
- Defined risk (max loss = premium paid)
- Defined profit (max gain = spread width - premium)
- Lower capital outlay than naked call
- Better for first automation phase
- Excellent capital efficiency (40-60% return on risk)

---

## Layer 3: Execution Engine (TODO - Phase 3)

Will be implemented in next phase with:

1. **Breeze API Authentication**
   - Session management
   - Token refresh
   - Account validation

2. **Chain Query & Filtering**
   - Fetch options chain from NFO
   - Filter by liquidity (bid-ask, OI, volume)
   - Select contracts per strategy legs

3. **Pre-Trade Risk Checks**
   - Chain liquidity sufficient?
   - Spread too wide?
   - Premium > max budget?
   - Sector concentrated?
   - Margin available?
   - Account health OK?

4. **Order Placement**
   - Build limit orders (not market)
   - Place entry order
   - Place protective stop-loss
   - Place profit target

5. **Position Management**
   - Monitor fills
   - Track P&L
   - Manage exits (SL/PT/time)
   - Close before expiry if needed

6. **Monitoring & Alerts**
   - Websocket streaming
   - Position updates
   - Risk alerts

---

## Data Flow Diagram

```
Real NSE Data (yfinance)
    ↓
backtest_indian_stocks_real_data.py
    ├─ Analyze: SMA, ATR, volatility
    ├─ Detect: Breakout, Momentum, Reversal
    └─ Output: Stock signals
         ↓
    signal_normalizer.py
    ├─ Normalize: Remove broker dependencies
    ├─ Calculate: Expected move, holding period
    ├─ Confidence: Band assignment
    └─ Output: Normalized signals (JSON)
         ↓
    options_strategy_selector.py
    ├─ Select: Strategy based on signal
    ├─ Build: Multi-leg structures
    ├─ Define: Risk & exit rules
    └─ Output: Strategy recommendations (JSON)
         ↓
    [EXECUTION ENGINE - TODO]
    ├─ Query: Options chains via Breeze
    ├─ Filter: Contracts by liquidity
    ├─ Check: Pre-trade risk rules
    ├─ Place: Orders
    └─ Monitor: Positions
         ↓
    Position P&L → Backtest Database
```

---

## Phase Implementation Plan

### Phase 1: Research Mode (Current) ✅
- ✅ Stock screener completed
- ✅ Signal normalizer created
- ✅ Strategy selector created
- ⏳ TODO: Historical options backtesting

### Phase 2: Paper/Shadow Trading (Next)
- Generate live signals daily
- Test strategy recommendations on historical option data
- Validate slippage/spread assumptions
- Compare model vs reality

### Phase 3: Semi-Automated Execution
- Alerts with human approval
- Automated chain selection
- Manual execution via Breeze

### Phase 4: Fully Automated (Spreads Only)
- Defined-risk strategies only
- Strict capital caps
- Kill-switches enabled
- Daily parameter review

### Phase 5: Broader Library
- Volatility strategies
- Portfolio overlays
- Rolling logic
- Multi-leg optimization

---

## File Inventory

### Core Implementation
```
app/
├── signal_normalizer.py           ✅ Normalizes stock signals
├── options_strategy_selector.py   ✅ Converts signals to strategies
└── options_screener.py            ✅ (existing) Live screener

backtest/
├── validate_indian_stocks_real_data.py     ✅ Stock data validator
├── backtest_indian_stocks_real_data.py     ✅ Stock signal generator
└── backtest_execution_engine.py            ⏳ TODO: Execution layer
```

### Outputs
```
backtest_reports/
├── normalized_signals_example.json
├── strategy_recommendations_*.json
└── indian_stocks_backtest_*.json
```

---

## Testing Results

### Signal Normalization ✅
```
Input:  AXIS stock signal (BREAKOUT, 70% confidence)
Output: Normalized signal with features, expected move, holding period
Status: ✅ Working
```

### Strategy Selection ✅
```
Input:  AXIS normalized signal
Output: BULL_CALL_SPREAD recommendation
        - Risk: ₹25.85
        - Profit target: 50%
        - Stop loss: 100%
        - Hold: 5 days
Status: ✅ Working
```

---

## Key Design Principles

### 1. Separation of Concerns ✅
- **Layer 1:** Data science (no broker)
- **Layer 2:** Logic (no broker)
- **Layer 3:** Execution (broker-specific)

### 2. Broker Independence ✅
- Signals/strategies are pure JSON
- Can swap brokers without changing Layer 1/2
- Easy to backtest and validate

### 3. Capital Protection 🔒
- Defined-risk strategies first
- Kill-switches designed (in Layer 3)
- Position limits enforced
- Pre-trade checks comprehensive

### 4. Auditability 📋
- Every signal has unique ID
- Every strategy traced to signal
- All decisions logged
- Easy to replay and analyze

### 5. Robustness 💪
- No overfitting (walk-forward validation)
- Parameter stability tested
- Regime-aware (trending vs choppy)
- Risk-adjusted metrics

---

## Capital Protection - The Non-Negotiables

### Position-Level Rules
```
max_risk_per_trade = 2% of account
max_premium_outlay = 1% of account
stop_loss_pct = 30%  (exit if premium drops 30%)
time_stop_days = 3   (exit if thesis fails)
```

### Portfolio-Level Rules
```
max_daily_loss = 5% of account
max_concurrent_positions = 5
max_sector_exposure = 25%
max_expiry_concentration = 30%
```

### Market Condition Rules
```
SKIP if: bid-ask spread > 2%
SKIP if: open interest < 100
SKIP if: volume < 1000 contracts
SKIP if: API quality degraded
```

### Operational Rules
```
all_orders are IDEMPOTENT
all_decisions are LOGGED
sessions are VALIDATED
orders are LIMIT-based (not market)
```

---

## Breeze API Integration Points (Phase 3)

According to official docs, will use:
1. **Session/Auth:** Login, token management
2. **Charts:** Historical OHLC for validation
3. **Option Chain:** NFO option contracts
4. **Quotes:** Real-time prices (websocket)
5. **Orders:** Place limit orders, SL orders
6. **Funds:** Check margin, balance
7. **Positions:** Track open trades
8. **Margin:** Calculate requirement

---

## Next Immediate Actions

### Backtest Historical Options (Phase 2)
1. Get historical option prices (yfinance has some)
2. For each normalized signal, simulate strategy execution
3. Calculate P&L with realistic assumptions:
   - Bid-ask spread cost
   - Slippage
   - Missed fills
   - Partial fills
4. Generate backtest report comparing:
   - With vs without spreads
   - Different expiry horizons
   - Different strike selections

### Build Shadow Trading System
1. Daily: Generate signals
2. Daily: Select strategies
3. Daily: Log to database (NOT execute)
4. Weekly: Compare signals vs actual price action
5. Weekly: Measure signal quality

---

## Success Metrics

### Signal Quality
- Hit rate: % of signals that move >50% of expected
- False positive rate: % wrong direction
- Average move after signal vs expected
- Win rate by confidence band

### Strategy Quality
- Backtest Sharpe ratio
- Profit factor (wins/losses)
- Max drawdown
- Return per unit risk

### Execution Quality (Phase 3+)
- Fill rates: % filled at better/worse prices
- Slippage: actual vs expected
- Execution cost: bid-ask impact
- P&L match: actual vs model

---

## Files to Review

1. `app/signal_normalizer.py` - Creates normalized signal JSON
2. `app/options_strategy_selector.py` - Converts signals to strategies
3. `backtest/backtest_indian_stocks_real_data.py` - Stock screener
4. `backtest_reports/*.json` - Example output files

---

## What's Next

**Highest priority:** Historical options backtesting
- Validate strategy recommendations on past data
- Measure slippage/spread realistic costs
- Build confidence before live trading

**Then:** Paper trading
- Generate signals daily
- Track phantom orders
- Compare model vs reality for 4 weeks

**Then:** Semi-automated
- Alerts + approval
- Automated chain selection
- Manual Breeze execution

---

Generated: 2026-06-09
Status: Phase 1 Research Complete ✅ → Phase 2 Paper Trading (Next)
