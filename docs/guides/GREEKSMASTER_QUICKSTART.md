# 🎯 GreeksMaster - Quick Start Guide

## Welcome to GreeksMaster!

**GreeksMaster** is your professional options trading platform powered by ICICIDirect Breeze API.

```
Master the Greeks → Master the Options → Master the Market
```

---

## 📊 What Can GreeksMaster Do?

### ✅ 4 Professional Trading Strategies
```
1. Bull Call Spread   → Buy ATM call + Sell OTM call (bullish, limited risk)
2. Bear Put Spread    → Sell ATM put + Buy OTM put (bearish, income)
3. Straddle          → Buy ATM call + Put (volatility play)
4. Iron Condor       → Sell call spread + Put spread (neutral income)
```

### ✅ Advanced Greeks Management
```
Delta   → Directional exposure control
Gamma   → Risk acceleration management
Theta   → Time decay optimization
Vega    → Volatility positioning
Rho     → Interest rate sensitivity
```

### ✅ Automated Risk Management
```
• Delta exposure limits (max 0.5)
• Vega exposure limits (max 2.0)
• Theta decay monitoring (-₹500/day max)
• Daily loss limits (2% max)
• Expiry proximity alerts
```

### ✅ Real-time Portfolio Tracking
```
• Active positions monitoring
• P&L calculation
• Greeks aggregation
• Risk alerts
• Performance reports
```

---

## 🚀 Quick Start (5 Minutes)

### 1️⃣ Check Configuration
```bash
cat .env
```
Should show:
```
BREEZE_USER_ID=PRAUZRKW
BREEZE_SESSION_TOKEN=55810740
OPTIONS_CAPITAL=500000
```

### 2️⃣ Test in Simulation Mode
```bash
python
>>> from app.options_engine import OptionsEngine
>>> engine = OptionsEngine(capital=500000, use_api=False)
>>> signal = engine.generate_bull_call_spread_signal(
...     symbol='NIFTY',
...     spot_price=22000,
...     confidence=0.80,
...     reason='Test signal'
... )
>>> engine.execute_signal(signal)
>>> engine.print_portfolio_summary()
```

### 3️⃣ Ready for Live Trading
Once you have NON-PINS token:
```bash
python
>>> from app.options_engine import OptionsEngine
>>> engine = OptionsEngine(capital=500000, use_api=True)  # ← Live mode
>>> # Generate and trade...
```

---

## 📚 Core Modules Explained

### `options_engine.py` - Main Trading Brain
```python
# Generate trading signals
signal = engine.generate_bull_call_spread_signal(...)
signal = engine.generate_bear_put_spread_signal(...)
signal = engine.generate_straddle_signal(...)
signal = engine.generate_iron_condor_signal(...)

# Execute trades
trade = engine.execute_signal(signal)

# Monitor portfolio
risk = engine.check_risk_limits()
engine.print_portfolio_summary()
```

### `options_strategy.py` - Greeks Calculator
```python
from app.options_strategy import OptionsTrader

trader = OptionsTrader(capital=500000)

# Find strikes
atm = trader.find_atm_strike('NIFTY', 22000)
otm_calls = trader.find_otm_strikes('NIFTY', 22000, 'CALL', 2)
itm_puts = trader.find_itm_strikes('NIFTY', 22000, 'PUT', 2)

# Calculate Greeks
greeks = trader.calculate_greeks(option_contract)
# Returns: Delta, Gamma, Theta, Vega, Rho

# Build strategies
spreads = trader.build_call_spread(...)
straddle = trader.build_straddle(...)
```

### `breeze_options_api.py` - Breeze API Integration
```python
from app.services.breeze_options_api import BreezOptionsAPIService

api = BreezOptionsAPIService()
api.authenticate()

# Place orders
api.buy_call('NIFTY', 22000, '2026-06-23', 1, 350)
api.sell_put('NIFTY', 21900, '2026-06-23', 1, 400)

# Monitor portfolio
positions = api.get_portfolio_positions()
pnl = api.get_options_pnl()
summary = api.get_options_summary()
```

---

## 🎯 Trading Workflow

```
┌─────────────────────────────────────────────────────┐
│ 1. SIGNAL GENERATION                                 │
│    Generate trading signals based on:               │
│    • Market analysis (price, volume, volatility)    │
│    • Technical indicators                           │
│    • Greeks positioning                             │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ 2. RISK CHECK                                        │
│    Verify constraints:                              │
│    • Delta < 0.5 (directional limit)               │
│    • Vega < 2.0 (volatility limit)                 │
│    • Theta > -500 (decay limit)                    │
│    • Daily loss < 2%                               │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ 3. TRADE EXECUTION                                   │
│    Place orders on Breeze API:                      │
│    • Buy call/put positions                         │
│    • Sell call/put positions                        │
│    • Manage spreads                                 │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ 4. POSITION MONITORING                              │
│    Track in real-time:                              │
│    • Premium paid/received                          │
│    • Current Greeks                                 │
│    • P&L per position                               │
│    • Days to expiry                                 │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ 5. EXIT MANAGEMENT                                  │
│    Close positions on:                              │
│    • Target P&L reached                             │
│    • Stop loss hit                                  │
│    • Expiry approaching (<3 days)                   │
│    • Risk limits exceeded                           │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Greeks Quick Reference

### Delta (Δ) - Directional Exposure
```
What it means:  How much premium changes with ₹1 price move
Range:          -1 to +1
Interpretation: 
  • 0.30  = 30% of the move (ATM call is ~0.5)
  • 0.70  = 70% of the move (ITM call)
  • -0.50 = -50% (ATM put is ~-0.5)
Goal:           Keep portfolio delta between -0.5 and +0.5
```

### Gamma (Γ) - Delta Acceleration
```
What it means:  How fast delta changes
Interpretation:
  • High gamma = Risky (delta changes quickly)
  • Low gamma = Stable
Goal:           Keep portfolio gamma under control
```

### Theta (Θ) - Time Decay
```
What it means:  Premium loss per day due to time
Interpretation:
  • Positive = You earn from time decay (seller's edge)
  • Negative = You lose from time decay (buyer's burden)
Goal:           Monitor daily decay, close before expiry crush
```

### Vega (ν) - Volatility Sensitivity
```
What it means:  How much premium changes with 1% volatility move
Interpretation:
  • High vega = Profit from volatility increase
  • Low vega = Stable to volatility changes
Goal:           Diversify vega exposure
```

---

## 💡 Example: Bull Call Spread Trade

### Setup (Bullish Signal)
```
Market: NIFTY at ₹22,000
Signal: Bullish technical setup
Confidence: 80%
```

### Strategy
```
BUY  22,000 Call @ ₹350  (Cost: ₹35,000)
SELL 22,100 Call @ ₹300  (Credit: ₹30,000)
─────────────────────────
NET COST: ₹5,000
MAX PROFIT: ₹5,000 (if NIFTY > 22,100 at expiry)
MAX LOSS: ₹5,000 (if NIFTY < 22,000 at expiry)
```

### Greeks Profile
```
Delta:  +0.30  (30% directional exposure)
Theta:  +₹50   (₹50/day profit from time decay)
Vega:   Neutral (limited volatility exposure)
Rho:    Minimal
```

### Code
```python
signal = engine.generate_bull_call_spread_signal(
    symbol='NIFTY',
    spot_price=22000,
    confidence=0.80,
    reason='Bullish technical setup'
)

trade = engine.execute_signal(signal)
print(f"Trade: {trade['strategy']}")
print(f"P&L: ₹{trade['net_premium']}")
```

---

## 🔄 Daily Workflow

### Morning (Before Market Open)
```
1. Review overnight news & global markets
2. Check technical analysis for signals
3. Scan option chains for opportunities
4. Generate trading signals
```

### During Market Hours
```
1. Monitor active positions
2. Check Greeks aggregation
3. Track portfolio P&L
4. Exit near profit targets
5. Adjust positions if needed
```

### Evening (After Market Close)
```
1. Review day's trades
2. Calculate daily P&L
3. Plan next day's trades
4. Update portfolio documentation
```

---

## ⚠️ Risk Management Rules

✅ **Always Follow**
- ✅ Never exceed delta limit (0.5)
- ✅ Never exceed vega limit (2.0)
- ✅ Never hold past 3 DTE (days to expiry)
- ✅ Stop trading if daily loss hits 2%
- ✅ Use spreads (limited risk) not naked positions

❌ **Never Do**
- ❌ Sell naked calls/puts
- ❌ Ignore expiry dates
- ❌ Trade without Greeks monitoring
- ❌ Exceed position size limits
- ❌ Average down on losing trades

---

## 🎓 Learning Resources

### In This Repository
- `OPTIONS_TRADING_SYSTEM.md` - Comprehensive system guide
- `GREEKSMASTER_GUIDE.md` - Detailed tutorial
- `app/options_engine.py` - Implementation details
- `app/options_strategy.py` - Greeks calculations

### Get Started Now
```bash
# Read the main guide
cat OPTIONS_TRADING_SYSTEM.md

# Check the implementation
python -c "from app.options_engine import OptionsEngine; help(OptionsEngine)"

# Run a test trade
python examples/test_bull_call_spread.py
```

---

## 📈 Success Metrics

Track these metrics to measure trading performance:

| Metric | Target | Status |
|--------|--------|--------|
| Win Rate | > 55% | Monitor |
| Avg Win | > Avg Loss | Track |
| Profit Factor | > 1.5 | Optimize |
| Max Drawdown | < 10% | Enforce |
| Sharpe Ratio | > 1.0 | Improve |
| Greeks Control | ✓ Within limits | Daily check |

---

## 🚀 Next Steps

1. **Read the Guides**
   ```bash
   cat OPTIONS_TRADING_SYSTEM.md
   cat GREEKSMASTER_GUIDE.md
   ```

2. **Test in Simulation**
   ```bash
   python -c "from app.options_engine import OptionsEngine; engine = OptionsEngine(use_api=False); ..."
   ```

3. **Get NON-PINS Token**
   - Visit: https://api.icicidirect.com/apiuser/login
   - Login with NON-PINS credentials
   - Copy session token

4. **Update Configuration**
   ```bash
   # Edit .env
   BREEZE_SESSION_TOKEN=<your_token>
   ```

5. **Start Live Trading**
   ```bash
   python
   >>> from app.options_engine import OptionsEngine
   >>> engine = OptionsEngine(use_api=True)
   >>> # Generate and trade!
   ```

---

## 💬 Questions?

- **Understanding Greeks?** → Read Greeks explanation above
- **Want to trade?** → Follow the workflow
- **Need help?** → Check the code comments
- **Implementation details?** → Review `options_engine.py`

---

**GreeksMaster - Master the Greeks, Master the Options** 📈🎯

*Version: 1.0 (June 9, 2026)*  
*Status: Production Ready*  
*Account: NON-PINS NRO (Options Only)*
