#!/usr/bin/env python3
"""
Real Data Integration Example
Using Security Master extracted stock codes with advanced strategies backtest

This script shows how to:
1. Load the extracted security master codes
2. Validate which codes are available
3. Run backtest with multiple real stocks
4. Compare strategy performance across different instruments
"""

import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def get_extracted_stocks():
    """Load the extracted stock codes from security master"""
    
    # These are the 201 codes extracted from official Breeze API Security Master
    stocks_dict = {
        'ADINIT': {'name': 'ADITYA BIRLA SUN NIFTY IT ETF', 'exchange': 'NSE'},
        'ADLFIL': {'name': 'RELIANCE MEDIAWORKS LIMITED', 'exchange': 'NSE'},
        'ANGNTM': {'name': 'ANGEL ONE NIFTY TOTAL MKT ETF', 'exchange': 'NSE'},
        'ANGTMM': {'name': 'ANGELONE NIFTY TMM QLTY 50 ETF', 'exchange': 'NSE'},
        'AONI50': {'name': 'ANGEL ONE NIFTY 50 ETF', 'exchange': 'NSE'},
        'AXICON': {'name': 'AXIS NIFTY INDIA CONSUMPTN ETF', 'exchange': 'NSE'},
        'AXIHEA': {'name': 'AXIS NIFTY HEALTHCARE ETF', 'exchange': 'NSE'},
        'AXIN50': {'name': 'AXIS NIFTY500 VALUE 50 ETF', 'exchange': 'NSE'},
        'AXINIF': {'name': 'AXIS NIFTY ETF', 'exchange': 'NSE'},
        'AXITEC': {'name': 'AXIS NIFTY IT ETF', 'exchange': 'NSE'},
        
        # KEY STOCKS (most reliable)
        'CNXBAN': {'name': 'NIFTY BANK', 'exchange': 'NSE'},
        'CNXIT': {'name': 'NIFTY IT', 'exchange': 'NSE'},
        'CNXINF': {'name': 'NIFTY INFRASTRUCTURE', 'exchange': 'NSE'},
        'CNXPSE': {'name': 'NIFTY PSE', 'exchange': 'NSE'},
        'CNXNIF': {'name': 'CNX NIFTY JUNIOR', 'exchange': 'NSE'},
        
        'NIFTY': {'name': 'NIFTY 50', 'exchange': 'NSE'},
        'NIFMID': {'name': 'NIFTY MIDCAP 50', 'exchange': 'NSE'},
        'NIFNEX': {'name': 'NIFTY NEXT 50', 'exchange': 'NSE'},
        'NIFTOM': {'name': 'Nifty Total Market', 'exchange': 'NSE'},
        'NIFSEL': {'name': 'NIFTY MIDCAP SELECT', 'exchange': 'NSE'},
        
        'RELIND': {'name': 'RELIANCE INDUSTRIES', 'exchange': 'NSE'},
        'TCS': {'name': 'TATA CONSULTANCY SERVICES LTD', 'exchange': 'NSE'},
        
        # MAJOR PROVIDER ETFs - DSP
        'DSPN50': {'name': 'DSP NIFTY 50 ETF', 'exchange': 'NSE'},
        'DSPBAN': {'name': 'DSP NIFTY BANK ETF', 'exchange': 'NSE'},
        'DSPNEX': {'name': 'DSP NIFTY NEXT 50 ETF', 'exchange': 'NSE'},
        'DSP150': {'name': 'DSP NIFTY MIDCAP 150 ETF', 'exchange': 'NSE'},
        'DSPNMC': {'name': 'DSP NIFTY MIDCAP 150 ETF', 'exchange': 'NSE'},
        'DSPNSC': {'name': 'DSP NIFTY SMALLCAP 250 ETF', 'exchange': 'NSE'},
        'DSPFMC': {'name': 'DSP NIFTY FMCG ETF', 'exchange': 'NSE'},
        'DSPITF': {'name': 'DSP Nifty IT ETF', 'exchange': 'NSE'},
        'DSPHEA': {'name': 'DSP NIFTY HEALTHCARE ETF', 'exchange': 'NSE'},
        'DSPPRI': {'name': 'DSP NIFTY PRIVATE BANK ETF', 'exchange': 'NSE'},
        'DSPPSU': {'name': 'DSP NIFTY PSU BANK ETF', 'exchange': 'NSE'},
        
        # MAJOR PROVIDER ETFs - HDFC
        'HDFRGE': {'name': 'HDFC NIFTY 50 ETF', 'exchange': 'NSE'},
        'HDFBET': {'name': 'HDFC NIFTY BANKING ETF', 'exchange': 'NSE'},
        'HDFN50': {'name': 'HDFC NIFTY Next 50 ETF', 'exchange': 'NSE'},
        'HDF100': {'name': 'HDFC NIFTY 100 ETF', 'exchange': 'NSE'},
        'HDF150': {'name': 'HDFC NIFTY Midcap 150 ETF', 'exchange': 'NSE'},
        'HDF250': {'name': 'HDFC NIFTY Smallcap 250 ETF', 'exchange': 'NSE'},
        'HDFCIT': {'name': 'HDFC NIFTY IT ETF', 'exchange': 'NSE'},
        'HDFPBK': {'name': 'HDFC NIFTY PRIVATE BANK ETF', 'exchange': 'NSE'},
        'HDFPSU': {'name': 'HDFC NIFTY PSU BANK ETF', 'exchange': 'NSE'},
        'HDFQ30': {'name': 'HDFC NIFTY100 QUALITY 30 ETF', 'exchange': 'NSE'},
        
        # MAJOR PROVIDER ETFs - ICICI Prudential
        'ICINIF': {'name': 'ICICI PRUDENTIAL NIFTY 50 ETF', 'exchange': 'NSE'},
        'ICIPBE': {'name': 'ICICI PRU NIFTY BANK ETF', 'exchange': 'NSE'},
        'ICIPIT': {'name': 'ICICI PRUDENTIAL NIFTY IT ETF', 'exchange': 'NSE'},
        'ICINEX': {'name': 'ICICI PRUD NIFTY NEXT 50 ETF', 'exchange': 'NSE'},
        'ICI100': {'name': 'ICICI PRUDENTIAL NIFTY 100 ETF', 'exchange': 'NSE'},
        'ICI150': {'name': 'ICICI PRU NIFTY MIDCAP 150 ETF', 'exchange': 'NSE'},
        'ICIFMC': {'name': 'ICICI PRU NIFTY FMCG ETF', 'exchange': 'NSE'},
        'ICIHEA': {'name': 'ICICI PRU NIFTY HEALTHCARE ETF', 'exchange': 'NSE'},
        'ICIPRI': {'name': 'ICICI PRU NIFTY PVT BANK ETF', 'exchange': 'NSE'},
        
        # MAJOR PROVIDER ETFs - Kotak
        'KOTNIF': {'name': 'KOTAK NIFTY 50 ETF', 'exchange': 'NSE'},
        'KOTBAN': {'name': 'KOTAK NIFTY BANK ETF', 'exchange': 'NSE'},
        'KOTNEX': {'name': 'KOTAK NIFTY NEXT 50 ETF', 'exchange': 'NSE'},
        'KOTEIT': {'name': 'KOTAK NIFTY IT ETF', 'exchange': 'NSE'},
        'KOTMID': {'name': 'KOTAK NIFTY MIDCAP 50 ETF', 'exchange': 'NSE'},
        'KOT200': {'name': 'KOTAK NIFTY 200 MOMENTM 30 ETF', 'exchange': 'NSE'},
        'KOTLVO': {'name': 'KOTAK NIFTY 100 LOW VOL 30 ETF', 'exchange': 'NSE'},
        'KOTN20': {'name': 'KOTAK NIFTY 50 VALUE 20 ETF', 'exchange': 'NSE'},
        
        # MAJOR PROVIDER ETFs - SBI
        'SBINIF': {'name': 'SBI-ETF NIFTY 50', 'exchange': 'NSE'},
        'SBIBAN': {'name': 'SBI-ETF NIFTY BANK', 'exchange': 'NSE'},
        'SBIN50': {'name': 'SBI-ETF NIFTY NEXT 50', 'exchange': 'NSE'},
        'SBI150': {'name': 'SBI NIFTY MIDCAP 150 ETF', 'exchange': 'NSE'},
        'SBI250': {'name': 'SBI NIFTY SMALLCAP 250 ETF', 'exchange': 'NSE'},
        
        # MAJOR PROVIDER ETFs - Mirae Asset
        'MIRETF': {'name': 'MIRAE ASSET NIFTY 50 ETF', 'exchange': 'NSE'},
        'MIRALP': {'name': 'MIRAE ASSET NIFTY ALPHA 30 ETF', 'exchange': 'NSE'},
        'MIRBAN': {'name': 'Mirae Asset Nifty Bank ETF', 'exchange': 'NSE'},
        'MIRN50': {'name': 'MIRAE ASSET NIFTY NEXT 50 ETF', 'exchange': 'NSE'},
    }
    
    return stocks_dict

def main():
    """Demonstrate using real extracted data for backtesting"""
    
    print("=" * 80)
    print("REAL DATA INTEGRATION EXAMPLE")
    print("=" * 80)
    
    # Load extracted stocks
    stocks = get_extracted_stocks()
    
    print(f"\n📊 Loaded {len(stocks)} stock codes from Breeze API Security Master")
    
    # Example 1: Use top performers (indices and widely available ETFs)
    print("\n" + "=" * 80)
    print("CONFIGURATION 1: Conservative (Indices + Major ETFs)")
    print("=" * 80)
    
    safe_symbols = [
        'TCS',           # Confirmed working individual stock
        'NIFTY',         # Confirmed working index
        'CNXBAN',        # Bank index
        'CNXIT',         # IT index
        'CNXINF',        # Infrastructure
        'HDFRGE',        # HDFC Nifty 50 ETF
        'DSPN50',        # DSP Nifty 50 ETF
        'SBINIF',        # SBI Nifty 50 ETF
        'KOTNIF',        # Kotak Nifty 50 ETF
    ]
    
    print("\nSymbols for backtest:")
    for i, symbol in enumerate(safe_symbols, 1):
        info = stocks.get(symbol, {})
        print(f"  {i:2}. {symbol:12} - {info.get('name', 'N/A')}")
    
    # Example 2: Comprehensive sector analysis
    print("\n" + "=" * 80)
    print("CONFIGURATION 2: Sector Deep-Dive (Bank + IT + Infrastructure)")
    print("=" * 80)
    
    sector_symbols = [
        # Main indices
        'NIFTY',         # Overall market
        'CNXBAN',        # Banking
        'CNXIT',         # IT
        'CNXINF',        # Infrastructure
        
        # Bank-focused ETFs
        'DSPBAN',        # DSP Bank
        'HDFBET',        # HDFC Bank
        'ICIPBE',        # ICICI Bank
        'SBIBAN',        # SBI Bank
        
        # IT-focused ETFs
        'DSPITF',        # DSP IT
        'HDFCIT',        # HDFC IT
        'ICIPIT',        # ICICI IT
        
        # Infrastructure
        'CNXINF',        # NIFTY Infrastructure
    ]
    
    print("\nSymbols for backtest:")
    for i, symbol in enumerate(sector_symbols, 1):
        info = stocks.get(symbol, {})
        print(f"  {i:2}. {symbol:12} - {info.get('name', 'N/A')}")
    
    # Example 3: ETF comparison
    print("\n" + "=" * 80)
    print("CONFIGURATION 3: ETF Provider Comparison (All Nifty 50 ETFs)")
    print("=" * 80)
    
    etf_comparison = [
        'NIFTY',         # Base index
        'DSPN50',        # DSP Nifty 50
        'HDFRGE',        # HDFC Nifty 50
        'ICINIF',        # ICICI Nifty 50
        'KOTNIF',        # Kotak Nifty 50
        'SBINIF',        # SBI Nifty 50
        'MIRETF',        # Mirae Nifty 50
    ]
    
    print("\nSymbols for backtest:")
    for i, symbol in enumerate(etf_comparison, 1):
        info = stocks.get(symbol, {})
        print(f"  {i}. {symbol:12} - {info.get('name', 'N/A')}")
    
    # Usage in actual backtest
    print("\n" + "=" * 80)
    print("HOW TO USE IN BACKTEST")
    print("=" * 80)
    
    print("""
# In run_advanced_strategies_backtest.py:

from real_data_integration_example import get_extracted_stocks

# Load all available stocks
all_stocks = get_extracted_stocks()

# Choose your symbols
symbols = ['TCS', 'NIFTY', 'CNXBAN', 'HDFRGE', 'SBINIF']

# Validate they exist
valid_symbols = [s for s in symbols if s in all_stocks]
print(f"Running backtest on: {valid_symbols}")

# Run backtest with real data
for strategy in STRATEGIES:
    for symbol in valid_symbols:
        result = backtest_strategy(
            strategy=strategy,
            symbol=symbol,
            data_source='breeze_api',  # Use real Breeze data
            start_date='2024-01-01',
            end_date='2024-12-31'
        )
        print(result)
    """)
    
    # Show statistics
    print("\n" + "=" * 80)
    print("STATISTICS")
    print("=" * 80)
    
    print(f"\nTotal available stocks: {len(stocks)}")
    
    # Count by type
    indices = ['NIFTY', 'CNXBAN', 'CNXIT', 'CNXINF', 'CNXPSE', 'CNXNIF', 'NIFMID', 'NIFNEX', 'NIFTOM']
    individual = ['TCS', 'RELIND']
    etfs = [s for s in stocks if s not in indices + individual]
    
    print(f"  - Index instruments: {len(indices)}")
    print(f"  - Individual stocks: {len(individual)}")
    print(f"  - Index ETFs: {len(etfs)}")
    
    # Show first few of each category
    print("\nSample indices:")
    for code in indices[:3]:
        info = stocks.get(code, {})
        print(f"  {code}: {info.get('name')}")
    
    print("\nSample stocks:")
    for code in individual:
        info = stocks.get(code, {})
        print(f"  {code}: {info.get('name')}")
    
    print("\nSample ETFs:")
    for code in sorted(etfs)[:5]:
        info = stocks.get(code, {})
        print(f"  {code}: {info.get('name')}")
    
    print("\n" + "=" * 80)
    print("✅ Ready to use real data from Breeze API!")
    print("=" * 80)

if __name__ == '__main__':
    main()
