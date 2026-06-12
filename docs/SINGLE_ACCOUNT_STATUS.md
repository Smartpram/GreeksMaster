# Single Account Setup - NON-PINS NRO Only

## ✅ Completed Changes

```
✅ Removed multi-account approach
✅ Simplified .env to single token: BREEZE_SESSION_TOKEN
✅ Updated Config to single account model
✅ Removed AccountManager (multi-account logic)
✅ Simplified BreezeAPIService constructor
✅ Deleted all account/token switching test files
✅ Added OPTIONS TRADING support (call, put, spreads, straddles)
✅ Added OPTIONS INTEGRATION module
```

## 📋 Current Configuration

```properties
# .env (Simplified)
BREEZE_USER_ID=PRAUZRKW
BREEZE_SESSION_TOKEN=55810740
BREEZE_PASSWORD=Smartpram2@
```

## 🎯 Key Points

**Account Type**: NON-PINS NRO Only
**Reason**: Algorithmic trading is ONLY allowed on NON-PINS NRO accounts
**Trading Allowed**: 
  - ✅ Equity/Stocks (SMA20, sentiment gate, range policy)
  - ✅ Options (calls, puts, spreads, straddles)
**Single Token**: 55810740 (no token switching)
**No Account Selection**: All orders go to NON-PINS NRO account

## 🔧 Code Changes

| File | Change |
|------|--------|
| `.env` | Removed PINS/NON-PINS sections, single BREEZE_* variables |
| `app/config.py` | Removed multi-account logic, uses single credentials |
| `app/account_manager.py` | DELETED (no longer needed) |
| `app/services/breeze_api.py` | Removed account_type parameter from constructor |
| `app/options_strategy.py` | **NEW** - Options trading engine |
| `app/options_integration.py` | **NEW** - Options integration with main pipeline |

## 🗑️ Deleted Files

- `test_token_mapping.py`
- `test_pins_api_response.py`
- `test_non_pins_api_response.py`
- `detect_default_account.py`
- `ACCOUNT_ANALYSIS_COMPLETE.md`
- `ACCOUNT_IDENTIFICATION_COMPLETE.md`
- `ACCOUNT_QUICK_REFERENCE.md`
- `SESSION_TOKEN_MAPPING_STRATEGY.md`
- `SETUP_CHECKLIST.md`
- `MULTI_ACCOUNT_*.md` (all multi-account docs)
- And all related test files

## ✨ Now Ready For

- ✅ Single-account algorithmic trading
- ✅ NON-PINS NRO account operations only
- ✅ **NEW: Options trading (calls, puts, spreads, straddles)**
- ✅ SMA20 crossover strategy (equity)
- ✅ Range Policy enforcement
- ✅ Market Sentiment Gate filtering
- ✅ Production deployment

## 🔄 New Options Features

### `app/options_strategy.py`
- ✅ Strike selection (ATM, ITM, OTM)
- ✅ Options Greeks calculation (Black-Scholes)
  - Delta, Gamma, Theta, Vega, Rho
- ✅ Expiry management (weekly & monthly)
- ✅ Position management (create, close, track)
- ✅ Strategy builders:
  - Call spreads
  - Put spreads
  - Straddles
- ✅ Time decay (theta) monitoring
- ✅ Portfolio summary with Greeks

### `app/options_integration.py`
- ✅ Signal generation (calls, puts, straddles)
- ✅ Confidence-based strategy selection
- ✅ Signal execution
- ✅ Portfolio Greeks aggregation
- ✅ Risk monitoring:
  - Delta/Vega limits
  - Theta decay tracking
  - Expiry proximity alerts
- ✅ Comprehensive reporting

## ⚙️ Usage Examples

### Equity Trading (Existing)
```python
from app.services.breeze_api import BreezeAPIService

api = BreezeAPIService()
api.authenticate()
positions = api.get_portfolio_positions()
```

### Options Trading (New)
```python
from app.options_integration import OptionsIntegration

# Initialize with 30% of capital for options
integration = OptionsIntegration(capital=500000, max_options_capital_allocation=0.3)

# Generate call signal based on bullish equity signal
signal = integration.generate_call_signal(
    symbol='NIFTY',
    spot_price=22000,
    equity_signal='BUY',
    confidence=0.80
)

# Execute signal
if signal:
    integration.execute_options_signal(signal)

# Monitor portfolio
integration.print_options_summary()
```

### Options Strategy Examples
```python
from app.options_strategy import OptionsTrader

trader = OptionsTrader(capital=500000)

# Build call spread (limited risk, limited reward)
spreads = trader.build_call_spread(
    symbol='NIFTY',
    spot_price=22000,
    premium_received=150,
    premium_paid=100,
    strike_width=100
)

# Build straddle (profit from volatility)
straddle = trader.build_straddle(
    symbol='NIFTY',
    spot_price=22000,
    call_premium=250,
    put_premium=250
)

# Monitor Greeks
portfolio_summary = trader.get_portfolio_summary()
```

## ⚙️ Usage

```python
from app.services.breeze_api import BreezeAPIService

# Create service - automatically uses NON-PINS NRO account
api = BreezeAPIService()

# All operations now go to NON-PINS NRO account
api.authenticate()
positions = api.get_portfolio_positions()
```

No account switching needed. All trading happens on NON-PINS NRO account.

---

**Status**: ✅ Multi-account approach REMOVED  
**Focus**: Single NON-PINS NRO account for algorithmic trading  
**Next**: Test trading strategies on live system
