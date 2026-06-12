# Options Trading System - NON-PINS NRO Account

## ✅ System Architecture

```
NON-PINS NRO Account
    ↓
Breeze Options API Service (breeze_options_api.py)
    ├─ Order placement (buy/sell calls & puts)
    ├─ Portfolio tracking
    ├─ P&L calculation
    └─ Option chain retrieval
    ↓
Options Trader (options_strategy.py)
    ├─ Greeks calculation (Black-Scholes)
    ├─ Strike selection (ATM, ITM, OTM)
    ├─ Strategy builders (spreads, straddles)
    └─ Position management
    ↓
Options Engine (options_engine.py)
    ├─ Signal generation
    ├─ Trade execution
    ├─ Risk monitoring (Greeks limits)
    ├─ Portfolio analytics
    └─ Performance reporting
```

## 📊 Implemented Strategies

### 1. BULL CALL SPREAD (Bullish, Limited Risk)
```
Strategy: Buy ATM call + Sell OTM call
Risk: Strike width - net premium
Profit: Net premium received
Max Loss: Fixed at entry
Max Profit: Fixed at entry
Use Case: Moderately bullish, defined risk
```

### 2. BEAR PUT SPREAD (Bearish, Limited Risk)
```
Strategy: Sell ATM put + Buy OTM put
Risk: Strike width - net premium
Profit: Net premium received
Max Loss: Fixed at entry
Max Profit: Fixed at entry
Use Case: Moderately bearish, income strategy
```

### 3. STRADDLE (Neutral, Volatility Play)
```
Strategy: Buy ATM call + Buy ATM put
Risk: Sum of premiums
Profit: From large price move in either direction
Max Loss: Fixed (both premiums)
Max Profit: Unlimited
Use Case: High volatility expected
```

### 4. IRON CONDOR (Neutral, Income Strategy)
```
Strategy: Sell OTM call spread + Sell OTM put spread
Risk: Strike width - premium (per spread)
Profit: Premium collected
Max Loss: Fixed at entry
Max Profit: Premium received
Use Case: Range-bound market, income generation
```

## 🎯 Key Components

### `app/services/breeze_options_api.py`
- **Order Management**: Place buy/sell calls and puts
- **Portfolio Tracking**: Get positions, orders, option chains
- **Analytics**: P&L calculation, portfolio summary
- **Methods**:
  - `place_options_order()` - Place any options order
  - `buy_call()`, `sell_call()`, `buy_put()`, `sell_put()` - Shortcuts
  - `get_portfolio_positions()` - Current holdings
  - `get_order_list()` - Order history
  - `get_option_chain()` - Strike prices and premiums
  - `get_options_pnl()` - P&L by position
  - `get_options_summary()` - Portfolio overview

### `app/options_strategy.py` (700+ lines)
- **Greeks Calculation**: Black-Scholes model
  - Delta, Gamma, Theta, Vega, Rho
- **Strike Selection**: ATM, ITM, OTM finders
- **Expiry Management**: Weekly & monthly options
- **Position Management**: Create, close, track
- **Strategy Builders**: Spreads, straddles
- **Monitoring**: Theta decay tracking

### `app/options_engine.py` (600+ lines)
- **Signal Generation**:
  - Bull call spreads (bullish)
  - Bear put spreads (bearish)
  - Straddles (volatility)
  - Iron condors (neutral)
- **Execution**: Trade placement with Greeks
- **Risk Management**:
  - Delta limits (0.5)
  - Vega limits (2.0)
  - Theta limits (-₹500/day)
  - Expiry proximity alerts
- **Reporting**: Portfolio summary, Greeks aggregation, P&L tracking

## ⚙️ Configuration (.env)

```properties
# Trading
OPTIONS_CAPITAL=500000
MAX_OPTION_POSITION_SIZE=0.1

# Risk Limits
MAX_DELTA_EXPOSURE=0.5      # Max directional exposure
MAX_VEGA_EXPOSURE=2.0       # Max volatility exposure
MAX_THETA_DECAY_PER_DAY=-500 # Max daily time decay loss
MAX_DAILY_LOSS=0.02         # Max daily loss %

# Strategy Defaults
DEFAULT_OPTION_STRATEGY=CALL_SPREAD
PREFERRED_EXPIRY=WEEKLY
USE_ATM_STRIKES=True
SPREAD_WIDTH=100            # Standard spread width
```

## 🚀 Usage Examples

### Initialize Engine
```python
from app.options_engine import OptionsEngine

# Simulation mode (no API)
engine = OptionsEngine(capital=500000, use_api=False)

# Production mode (with Breeze API)
engine = OptionsEngine(capital=500000, use_api=True)
```

### Generate & Execute Bull Call Spread
```python
# Generate signal
signal = engine.generate_bull_call_spread_signal(
    symbol='NIFTY',
    spot_price=22000,
    confidence=0.80,
    reason='Bullish RSI divergence'
)

# Execute trade
trade = engine.execute_signal(signal)
```

### Generate & Execute Bear Put Spread
```python
signal = engine.generate_bear_put_spread_signal(
    symbol='BANKNIFTY',
    spot_price=44000,
    confidence=0.70,
    reason='Support at 43500'
)

trade = engine.execute_signal(signal)
```

### Generate & Execute Straddle (High Volatility)
```python
signal = engine.generate_straddle_signal(
    symbol='NIFTY',
    spot_price=22000,
    market_volatility=0.35,  # 35% volatility
    reason='RBI meeting scheduled'
)

trade = engine.execute_signal(signal)
```

### Monitor Portfolio
```python
# Check risk limits
risk_check = engine.check_risk_limits()
print(f"Delta exposure: {risk_check['portfolio_delta']:.2f}")
print(f"Vega exposure: {risk_check['portfolio_vega']:.2f}")

# Print summary
engine.print_portfolio_summary()
```

### Direct API Usage (Advanced)
```python
from app.services.breeze_options_api import BreezOptionsAPIService

api = BreezOptionsAPIService()
api.authenticate()

# Get option chain
chain = api.get_option_chain(symbol='NIFTY', expiry_date='2026-06-23')

# Place order
order = api.buy_call(
    symbol='NIFTY',
    strike=22000,
    expiry='2026-06-23',
    quantity=1,
    price=350
)

# Monitor P&L
pnl = api.get_options_pnl()
```

## 📈 Greeks Explanation

| Greek | Meaning | Effect |
|-------|---------|--------|
| **Delta** | Price sensitivity | How much premium changes per ₹1 move |
| **Gamma** | Delta acceleration | How much delta changes with price |
| **Theta** | Time decay | Premium loss per day (theta burn) |
| **Vega** | Volatility exposure | Premium change with volatility % |
| **Rho** | Interest rate sensitivity | Premium change with interest rate |

## 🎯 Risk Management Features

✅ **Position Size Limits**
- Max 10% of capital per trade
- Prevents over-leveraging

✅ **Greeks Monitoring**
- Delta: Max 0.5 directional exposure
- Vega: Max 2.0 volatility exposure
- Theta: Max -₹500/day decay

✅ **Expiry Management**
- Alerts for positions < 3 days to expiry
- Force close near expiration

✅ **Daily Loss Limits**
- Max 2% daily loss
- Automatic trading halt at limit

## 📊 Backtesting Ready

Can backtest against:
- Historical option chains
- Past volatility data
- Actual trade execution
- Performance metrics

## 🔌 Integration Points

1. **Market Data**: Option chain feeds signal generation
2. **Risk Monitoring**: Greeks check before each trade
3. **Execution**: Order placement via Breeze API
4. **Reporting**: Daily performance tracking

## ✨ Next Steps

1. Get NON-PINS session token
2. Update `.env` with credentials
3. Connect to Breeze API: `api.authenticate()`
4. Generate options signals
5. Execute and monitor trades
6. Track daily P&L

---

**Status**: ✅ Options trading system complete and ready for deployment  
**Account**: NON-PINS NRO only  
**Strategies**: 4 core strategies (bull spreads, bear spreads, straddles, iron condors)  
**Risk Management**: Full Greeks monitoring and limits  
**Reporting**: Comprehensive P&L and risk tracking
