# Breeze API Implementation Cookbook
**Practical Examples & Copy-Paste Ready Code**

---

## 🍳 Recipe 1: Authenticate & Get Account Info

```python
from app.services.breeze_api import BreezeAPIService

# Initialize
breeze = BreezeAPIService()

# Authenticate
auth = breeze.authenticate()
print(f"Authenticated as: {auth['user_name']}")
print(f"User ID: {auth['user_id']}")
print(f"Account Segments: {auth['segments']}")

# Output:
# Authenticated as: PRAMOD GORAKHNATH KARLE
# User ID: PRAUZRKW
# Account Segments: {'cash': True, 'futures': True, 'options': True}
```

---

## 🍳 Recipe 2: Check Account Balance

```python
from app.services.breeze_api import BreezeAPIService

breeze = BreezeAPIService()
breeze.authenticate()

# Get funds
funds = breeze.get_funds()
if funds['success']:
    data = funds['data']
    print(f"Total Balance: ₹{data.get('balance', 0):,.2f}")
    print(f"Available: ₹{data.get('available', 0):,.2f}")
    print(f"Utilized: ₹{data.get('utilized', 0):,.2f}")
    print(f"Blocked: ₹{data.get('blocked', 0):,.2f}")
else:
    print(f"Error: {funds['error']}")

# Output (Sample):
# Total Balance: ₹30,000.00
# Available: ₹137,742.47
# Utilized: ₹0.00
# Blocked: ₹0.00
```

---

## 🍳 Recipe 3: Get Live Stock Quote

```python
from app.services.breeze_api import BreezeAPIService

breeze = BreezeAPIService()
breeze.authenticate()

# Get RELIANCE quote
quote = breeze.get_quotes(
    stock_code="RELIANCE",
    exchange_code="NSE",
    product_type="cash"
)

if quote['success']:
    data = quote['data']
    print(f"Stock: RELIANCE (NSE)")
    print(f"Last Traded Price: ₹{data.get('ltp', 0):.2f}")
    print(f"Bid: ₹{data.get('bid', 0):.2f}")
    print(f"Ask: ₹{data.get('ask', 0):.2f}")
    print(f"Open: ₹{data.get('open', 0):.2f}")
    print(f"High: ₹{data.get('high', 0):.2f}")
    print(f"Low: ₹{data.get('low', 0):.2f}")
    print(f"Close: ₹{data.get('close', 0):.2f}")
    print(f"Volume: {data.get('volume', 0):,}")
else:
    print(f"Error: {quote['error']}")

# Output (Sample):
# Stock: RELIANCE (NSE)
# Last Traded Price: ₹2,850.50
# Bid: ₹2,850.25
# Ask: ₹2,850.75
# Open: ₹2,845.00
# High: ₹2,855.50
# Low: ₹2,840.00
# Close: ₹2,848.25
# Volume: 5,000,000
```

---

## 🍳 Recipe 4: Get Demat Holdings

```python
from app.services.breeze_api import BreezeAPIService
import pandas as pd

breeze = BreezeAPIService()
breeze.authenticate()

# Get holdings
holdings = breeze.get_demat_holdings()

if holdings['success']:
    df = pd.DataFrame(holdings['data'])
    print(df[['stock_code', 'quantity', 'isin', 'cost_value']].to_string())
    
    # Summary statistics
    print(f"\nTotal Holdings: {len(df)}")
    print(f"Total Value: ₹{df['cost_value'].sum():,.2f}")
else:
    print(f"Error: {holdings['error']}")
```

---

## 🍳 Recipe 5: Get Portfolio Positions

```python
from app.services.breeze_api import BreezeAPIService
import pandas as pd

breeze = BreezeAPIService()
breeze.authenticate()

# Get positions
positions = breeze.get_portfolio_positions()

if positions['success']:
    df = pd.DataFrame(positions['data'])
    print("Current Positions:")
    print(df[['stock_code', 'exchange_code', 'quantity', 'price', 'pnl']].to_string())
    
    # Summary
    total_pnl = df['pnl'].sum()
    print(f"\nTotal P&L: ₹{total_pnl:,.2f}")
    print(f"Win Rate: {len(df[df['pnl'] > 0])} / {len(df)}")
else:
    print(f"Error: {positions['error']}")
```

---

## 🍳 Recipe 6: Get Historical Data for Backtesting

```python
from app.services.breeze_api import BreezeAPIService
import pandas as pd

breeze = BreezeAPIService()
breeze.authenticate()

# Get 6 months of daily data
history = breeze.get_historical_data(
    stock_code="RELIANCE",
    exchange_code="NSE",
    product_type="cash",
    interval="1day",
    days_back=180
)

if history['success']:
    df = pd.DataFrame(history['data'])
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    print(f"Data retrieved: {len(df)} candles")
    print(f"Period: {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"\nFirst 5 rows:")
    print(df.head())
    
    # Calculate returns
    df['returns'] = df['close'].pct_change() * 100
    print(f"\nAverage Daily Return: {df['returns'].mean():.3f}%")
    print(f"Volatility: {df['returns'].std():.3f}%")
else:
    print(f"Error: {history['error']}")
    print("Using simulated data instead...")
```

---

## 🍳 Recipe 7: Fetch Multiple Quotes

```python
from app.services.breeze_api import BreezeAPIService
import pandas as pd

breeze = BreezeAPIService()
breeze.authenticate()

symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR']
quotes_data = []

for symbol in symbols:
    quote = breeze.get_quotes(symbol, "NSE", "cash")
    if quote['success']:
        data = quote['data']
        quotes_data.append({
            'Symbol': symbol,
            'Price': data.get('ltp', 0),
            'Change': data.get('change_percent', 0),
            'Volume': data.get('volume', 0)
        })

df = pd.DataFrame(quotes_data)
print(df.to_string(index=False))

# Calculate portfolio value
avg_price = df['Price'].mean()
print(f"\nAverage Price: ₹{avg_price:.2f}")
```

---

## 🍳 Recipe 8: Monitor Account in Real-Time Loop

```python
from app.services.breeze_api import BreezeAPIService
import time
from datetime import datetime

breeze = BreezeAPIService()
breeze.authenticate()

print("Starting real-time monitoring (Ctrl+C to stop)...")
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

try:
    while True:
        # Get current balance
        funds = breeze.get_funds()
        if funds['success']:
            data = funds['data']
            available = data.get('available', 0)
            
            # Get sample position
            positions = breeze.get_portfolio_positions()
            if positions['success'] and positions['data']:
                position = positions['data'][0]
                pnl = position.get('pnl', 0)
            else:
                pnl = 0
            
            # Get live quote
            quote = breeze.get_quotes("RELIANCE", "NSE", "cash")
            if quote['success']:
                ltp = quote['data'].get('ltp', 0)
            else:
                ltp = 0
            
            # Display
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] Available: ₹{available:,.0f} | P&L: ₹{pnl:,.0f} | RELIANCE: ₹{ltp:.2f}")
        
        # Update every 10 seconds
        time.sleep(10)

except KeyboardInterrupt:
    print("\n\nMonitoring stopped.")
    print(f"Ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
```

---

## 🍳 Recipe 9: Analyze Holdings Performance

```python
from app.services.breeze_api import BreezeAPIService
import pandas as pd

breeze = BreezeAPIService()
breeze.authenticate()

# Get all holdings
holdings = breeze.get_demat_holdings()
positions = breeze.get_portfolio_positions()

if holdings['success'] and positions['success']:
    h_df = pd.DataFrame(holdings['data'])
    p_df = pd.DataFrame(positions['data'])
    
    # Merge to get full picture
    analysis = h_df.merge(
        p_df[['stock_code', 'pnl', 'price']],
        on='stock_code',
        how='outer'
    )
    
    # Calculate metrics
    analysis['cost_per_unit'] = analysis['cost_value'] / analysis['quantity']
    analysis['current_value'] = analysis['quantity'] * analysis['price']
    analysis['gain_loss'] = analysis['current_value'] - analysis['cost_value']
    analysis['gain_loss_pct'] = (analysis['gain_loss'] / analysis['cost_value']) * 100
    
    print("Holdings Analysis:")
    print(analysis[['stock_code', 'quantity', 'cost_per_unit', 'price', 'gain_loss', 'gain_loss_pct']].to_string())
    
    # Summary
    total_cost = analysis['cost_value'].sum()
    total_current = analysis['current_value'].sum()
    total_gain = total_current - total_cost
    total_gain_pct = (total_gain / total_cost) * 100
    
    print(f"\n{'='*50}")
    print(f"Total Cost:      ₹{total_cost:>15,.2f}")
    print(f"Current Value:   ₹{total_current:>15,.2f}")
    print(f"Total Gain/Loss: ₹{total_gain:>15,.2f}")
    print(f"Return %:        {total_gain_pct:>15.2f}%")
    print(f"{'='*50}")
```

---

## 🍳 Recipe 10: Validate API Connectivity

```python
from app.services.breeze_api import BreezeAPIService
import time

def validate_breeze_api():
    """Validate complete Breeze API connectivity"""
    
    print("🔍 Validating Breeze API Connection...\n")
    
    breeze = BreezeAPIService()
    
    # Test 1: Connection
    print("1️⃣ Testing basic connection...")
    if breeze.test_connection():
        print("   ✅ HTTP connectivity OK\n")
    else:
        print("   ❌ Connection failed\n")
        return False
    
    # Test 2: Authentication
    print("2️⃣ Testing authentication...")
    auth = breeze.authenticate()
    if auth['success']:
        print(f"   ✅ Authenticated as {auth['user_name']}\n")
    else:
        print(f"   ❌ Authentication failed: {auth.get('error')}\n")
        return False
    
    # Test 3: Get Funds
    print("3️⃣ Testing get_funds endpoint...")
    funds = breeze.get_funds()
    if funds['success']:
        print(f"   ✅ Available: ₹{funds['data'].get('available', 0):,.2f}\n")
    else:
        print(f"   ❌ Get funds failed: {funds.get('error')}\n")
        return False
    
    # Test 4: Get Quote
    print("4️⃣ Testing get_quotes endpoint...")
    quote = breeze.get_quotes("RELIANCE", "NSE", "cash")
    if quote['success']:
        print(f"   ✅ RELIANCE LTP: ₹{quote['data'].get('ltp', 0):.2f}\n")
    else:
        print(f"   ❌ Get quotes failed: {quote.get('error')}\n")
        return False
    
    # Test 5: Get Holdings
    print("5️⃣ Testing get_demat_holdings endpoint...")
    holdings = breeze.get_demat_holdings()
    if holdings['success']:
        print(f"   ✅ Retrieved {len(holdings['data'])} holdings\n")
    else:
        print(f"   ⚠️  Get holdings warning: {holdings.get('error')}\n")
    
    # Test 6: Get Positions
    print("6️⃣ Testing get_portfolio_positions endpoint...")
    positions = breeze.get_portfolio_positions()
    if positions['success']:
        print(f"   ✅ Retrieved {len(positions['data'])} positions\n")
    else:
        print(f"   ⚠️  Get positions warning: {positions.get('error')}\n")
    
    print("✅ All critical tests passed!")
    print("🚀 API is ready for backtesting and paper trading")
    
    return True

# Run validation
if __name__ == "__main__":
    validate_breeze_api()
```

---

## 🍳 Recipe 11: Export Data for Analysis

```python
from app.services.breeze_api import BreezeAPIService
import pandas as pd
import csv
from datetime import datetime

breeze = BreezeAPIService()
breeze.authenticate()

# Get all data
holdings = breeze.get_demat_holdings()
positions = breeze.get_portfolio_positions()
funds = breeze.get_funds()

# Export to CSV
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Holdings export
if holdings['success']:
    df_holdings = pd.DataFrame(holdings['data'])
    df_holdings.to_csv(f"holdings_{timestamp}.csv", index=False)
    print(f"✅ Exported holdings to holdings_{timestamp}.csv")

# Positions export
if positions['success']:
    df_positions = pd.DataFrame(positions['data'])
    df_positions.to_csv(f"positions_{timestamp}.csv", index=False)
    print(f"✅ Exported positions to positions_{timestamp}.csv")

# Account export
if funds['success']:
    with open(f"account_{timestamp}.txt", 'w') as f:
        f.write(f"Account Summary - {datetime.now().isoformat()}\n")
        f.write(f"{'='*50}\n")
        for key, value in funds['data'].items():
            f.write(f"{key}: {value}\n")
    print(f"✅ Exported account to account_{timestamp}.txt")
```

---

## 🍳 Recipe 12: Error Handling Best Practices

```python
from app.services.breeze_api import BreezeAPIService
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_api_call(func, *args, **kwargs):
    """Wrapper for safe API calls with error handling"""
    try:
        result = func(*args, **kwargs)
        if result.get('success'):
            logger.info(f"✅ {func.__name__} succeeded")
            return result['data']
        else:
            logger.warning(f"⚠️  {func.__name__} failed: {result.get('error')}")
            return None
    except Exception as e:
        logger.error(f"❌ {func.__name__} exception: {e}")
        return None

# Usage
breeze = BreezeAPIService()

# Safe authentication
if safe_api_call(breeze.authenticate):
    # Safe fund retrieval
    funds = safe_api_call(breeze.get_funds)
    if funds:
        print(f"Available: ₹{funds['available']}")
    
    # Safe quote retrieval
    quote = safe_api_call(breeze.get_quotes, "RELIANCE", "NSE", "cash")
    if quote:
        print(f"RELIANCE: ₹{quote['ltp']}")
```

---

## 🔗 Integration with Backtesting

```python
from app.services.breeze_api import BreezeAPIService
from run_integrated_backtest import StrategyOptimizer
import pandas as pd

# Step 1: Fetch real data
breeze = BreezeAPIService()
breeze.authenticate()

history = breeze.get_historical_data(
    stock_code="RELIANCE",
    exchange_code="NSE",
    interval="1day",
    days_back=180
)

if history['success']:
    df = pd.DataFrame(history['data'])
else:
    # Fallback to generated data
    from run_integrated_backtest import generate_sample_data
    df = generate_sample_data("RELIANCE", 180)

# Step 2: Optimize strategy
optimizer = StrategyOptimizer(df)
rsi_results = optimizer.optimize_rsi_strategy()

print(f"Best RSI Parameters:")
print(f"  Period: {rsi_results['best_params']['period']}")
print(f"  Oversold: {rsi_results['best_params']['oversold']}")
print(f"  Overbought: {rsi_results['best_params']['overbought']}")
print(f"  Expected Return: {rsi_results['best_params']['return']:.2f}%")

# Step 3: Deploy to paper trading
from run_paper_trader import PaperTradingRunner

runner = PaperTradingRunner({
    'initial_capital': 100000,
    'strategies': [{
        'name': 'RSI Optimized',
        'symbol': 'RELIANCE',
        'type': 'rsi_reversal',
        'params': rsi_results['best_params']
    }]
})
runner.start()
```

---

## ✅ Checklist for API Integration

- [ ] API credentials configured in `.env`
- [ ] Authentication working (breeze.authenticate())
- [ ] Can fetch account balance (breeze.get_funds())
- [ ] Can fetch live quotes (breeze.get_quotes())
- [ ] Can fetch holdings (breeze.get_demat_holdings())
- [ ] Can fetch positions (breeze.get_portfolio_positions())
- [ ] Error handling implemented
- [ ] Logging configured
- [ ] Rate limiting implemented (10 orders/sec max)
- [ ] Ready for live order placement

---

## 📚 Reference: All Available API Methods

```python
breeze = BreezeAPIService()

# Authentication
breeze.authenticate()                                    # Get user details
breeze.login()                                          # Get login URL

# Account Information
breeze.get_funds()                                      # Get account balance
breeze.get_demat_holdings()                            # Get demat holdings
breeze.get_portfolio_positions()                       # Get open positions
breeze.get_portfolio_holdings(exchange, from, to)      # Get holdings by period

# Market Data
breeze.get_quotes(symbol, exchange, product_type)     # Get live quote
breeze.get_historical_data(symbol, exchange, ...)     # Get historical data

# Order Management (Ready to implement)
# breeze.place_order(...)                              # Place new order
# breeze.modify_order(...)                             # Modify order
# breeze.cancel_order(...)                             # Cancel order
# breeze.get_order_list()                              # Get all orders
# breeze.get_order_detail(order_id)                    # Get order details

# Trading (Ready to implement)
# breeze.get_trade_list()                              # Get all trades
# breeze.get_trade_detail(trade_id)                    # Get trade details
# breeze.square_off(symbol, exchange, product)        # Close position

# Advanced (Ready to implement)
# breeze.get_option_chain_quotes(...)                 # Get option chain
# breeze.gtt_single_leg_place_order(...)              # Place GTT order
# breeze.gtt_three_leg_place_order(...)               # Place 3-leg GTT order
```

---

**Ready to use! Copy-paste these recipes and adapt to your needs.** 🚀

