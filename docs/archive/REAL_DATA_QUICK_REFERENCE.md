# Quick Reference: Using Real Data from Security Master

## 🚀 Quick Start

### Step 1: Extract Stock Codes (Already Done! ✅)
```bash
python download_security_master.py
```
**Output:** 201 stock codes extracted from official Breeze API master file

### Step 2: Update Your Backtest Configuration

Replace in `run_advanced_strategies_backtest.py`:

**Before (Hardcoded symbols):**
```python
symbols = ['TCS', 'NIFTY']  # Limited to 2 symbols
```

**After (Using extracted codes):**
```python
# Use extracted stock codes
symbols = [
    'TCS',        # ✅ Tested working
    'NIFTY',      # ✅ Tested working  
    'RELIND',     # Reliance Industries
    'CNXBAN',     # NIFTY Bank Index
    'CNXIT',      # NIFTY IT Index
    # ... add more from the 201 extracted codes
]
```

### Step 3: Run Backtest with Real Data
```bash
python run_advanced_strategies_backtest.py
```

## 📊 Available Stock Codes (201 Total)

### Most Reliable (Individual Stocks):
- `TCS` - Tata Consultancy Services ✅
- `RELIND` - Reliance Industries
- `SBIN...` - State Bank related instruments
- `HDFCBANK` - HDFC Bank (if in your plan)
- `ICICIBANK` - ICICI Bank (if in your plan)

### Indices:
- `NIFTY` - NIFTY 50 ✅
- `CNXBAN` - NIFTY Bank
- `CNXIT` - NIFTY IT
- `CNXINF` - NIFTY Infrastructure
- `CNXPSE` - NIFTY PSE

### Index ETFs (180+ codes):
All major providers covered:
- `DSP...` - DSP Mutual Fund ETFs
- `HDFRGE`, `HDFN50`, `HDFBET` - HDFC ETFs
- `ICINIF`, `ICIPBE`, `ICIPIT` - ICICI Prudential ETFs
- `KOTNIF`, `KOTBAN`, `KOTNEX` - Kotak ETFs
- `SBINIF`, `SBIBAN`, `SBIN50` - SBI ETFs
- `MIRETF`, `MIRALP`, `MIRBAN` - Mirae Asset ETFs
- And many more...

## 🔍 What Data You Get

With each stock code, Breeze API provides:

**Per-minute data:**
- Open, High, Low, Close prices
- Volume traded
- Open Interest (for derivatives)

**Per-day data:**
- Daily OHLC with intraday high/low
- Daily volume
- Historical patterns for analysis

**Date Range:** 
- Historical data available (exact period depends on stock)
- Real-time streaming available during market hours

## ⚙️ Configuration Integration

### Automatic Stock List Update

Create a file `config/stocks.py`:
```python
# Auto-generated from Security Master
AVAILABLE_STOCKS = {
    'TCS': {'name': 'TATA CONSULTANCY SERVICES LTD', 'exchange': 'NSE'},
    'RELIND': {'name': 'RELIANCE INDUSTRIES', 'exchange': 'NSE'},
    'NIFTY': {'name': 'NIFTY 50', 'exchange': 'NSE'},
    # ... 198 more
}

# Use in strategy:
symbols = list(AVAILABLE_STOCKS.keys())[:10]  # Use top 10
```

### Environment Variable Approach

```bash
# .env file
BACKTEST_SYMBOLS=TCS,NIFTY,RELIND,CNXBAN
```

Use in code:
```python
import os
symbols = os.getenv('BACKTEST_SYMBOLS', 'TCS,NIFTY').split(',')
```

## 🔄 Refresh Schedule

Security Master updates **daily at 8:00 AM IST**

Set up automatic refresh:
```bash
# Every day at 8:05 AM IST
0 5 * * * cd /c/Data/MyBreezeApp && python download_security_master.py >> logs/security_master.log 2>&1
```

## 🛠️ Common Operations

### Get All Available Stocks
```python
from download_security_master import parse_security_master

stocks = parse_security_master()
print(f"Available stocks: {len(stocks)}")
for code, info in stocks.items():
    print(f"  {code}: {info['name']}")
```

### Filter by Exchange
```python
nse_stocks = [code for code, info in stocks.items() 
              if info.get('exchange') == 'NSE']
print(f"NSE stocks: {len(nse_stocks)}")
```

### Check if Stock is Available
```python
if 'TCS' in stocks:
    print("TCS data available")
else:
    print("TCS not in your API plan")
```

## ⚠️ Important Limitations

### Your API Plan Affects Availability
- ✅ TCS: Confirmed working
- ✅ NIFTY: Confirmed working
- ❓ HDFCBANK, ICICIBANK, INFY: May require different plan
- ❓ Individual stocks: Depends on subscription level
- ✅ ETFs/Indices: Generally more accessible

### To Check Actual Availability:
```bash
python test_breeze_historical.py
# Shows which of 201 codes have real data accessible
```

## 📈 Backtest Configuration Examples

### Conservative (2 symbols - Testing)
```python
symbols = ['TCS', 'NIFTY']
```

### Moderate (5 indices)
```python
symbols = ['NIFTY', 'CNXBAN', 'CNXIT', 'CNXINF', 'CNXPSE']
```

### Comprehensive (10+ symbols)
```python
symbols = [
    'NIFTY',      # Main index
    'CNXBAN',     # Bank index
    'CNXIT',      # IT index  
    'RELIND',     # Large cap
    'CNXINF',     # Infra
    'CNXPSE',     # PSU
    'TCS',        # IT stock
    'SBIN150',    # SBI Midcap ETF
    'HDFRGE',     # HDFC Nifty 50 ETF
    'SBINIF',     # SBI Nifty 50 ETF
]
```

### ETF Focus (All major providers)
```python
symbols = [
    # DSP
    'DSPN50', 'DSPBAN', 'DSPIT', 'DSP150',
    # HDFC
    'HDFRGE', 'HDFBET', 'HDFN50', 'HDFLIQ',
    # ICICI
    'ICINIF', 'ICIPBE', 'ICIPIT', 'ICI150',
    # Kotak
    'KOTNIF', 'KOTBAN', 'KOTMID', 'KOTNEX',
    # SBI
    'SBINIF', 'SBIBAN', 'SBIN50', 'SBI150',
]
```

## 🔗 Next Steps

1. **Validate Session Token** - Refresh from https://api.icicidirect.com/apiuser/login
2. **Test Data Availability** - Run `python test_breeze_historical.py`
3. **Choose Stock Symbols** - Pick from the 201 available codes
4. **Run Backtest** - Execute with your chosen symbols
5. **Analyze Results** - Compare performance across multiple stocks

## 📞 Troubleshooting

### "No data returned" Error
- Session token may be expired
- Refresh at: https://api.icicidirect.com/apiuser/login?api_key=YOUR_API_KEY
- Stock may not be in your API plan

### "Stock not found" Error
- Check spelling matches the extraction output exactly (case-sensitive)
- Verify stock is in the 201 extracted codes
- May need different exchange code (NSE vs NFO)

### Backtest Runs Slow
- Reduce number of symbols (start with 2-3)
- Use shorter date ranges (30-90 days instead of 1 year)
- Increase interval (day instead of minute)

## ✅ Verification Checklist

- [ ] Downloaded Security Master (SecurityMaster.zip exists)
- [ ] Ran extraction script (python download_security_master.py)
- [ ] Got 201+ stock codes in output
- [ ] Updated backtest config with real stock codes
- [ ] Session token is fresh (not expired)
- [ ] Test script shows data available for chosen stocks
- [ ] Backtest runs without "stock not found" errors
- [ ] Results show real market data patterns

---
**Status:** 🟢 Real data infrastructure ready for production backtesting!
