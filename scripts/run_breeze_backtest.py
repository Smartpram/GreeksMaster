#!/usr/bin/env python3
"""
Breeze Real Data Backtest Runner
Validates Breeze connection and runs backtest with real market data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from app.config import Config
from app.services.breeze_api import BreezeAPIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_breeze_connection():
    """Verify Breeze API connection"""
    print("\n" + "="*80)
    print("CHECKING BREEZE API CONNECTION")
    print("="*80 + "\n")
    
    config = Config()
    
    # Check required credentials
    required_fields = {
        'BREEZE_API_KEY': config.BREEZE_API_KEY,
        'BREEZE_SECRET_KEY': config.BREEZE_SECRET_KEY,
    }
    
    missing = []
    for field, value in required_fields.items():
        status = "✓" if value else "✗"
        print(f"{status} {field:<30} {'Found' if value else 'MISSING'}")
        if not value:
            missing.append(field)
    
    if missing:
        print(f"\n❌ Missing credentials: {', '.join(missing)}")
        print("\nPlease set these in .env file:")
        for field in missing:
            print(f"  {field}=your_value")
        return False
    
    print("\n✓ All credentials found!")
    
    # Try to initialize Breeze
    try:
        print("\n🔗 Attempting to connect to Breeze API...")
        breeze = BreezeAPIService()
        print("✓ Breeze API initialized successfully!")
        
        # Try a simple call to verify connection
        print("\n🔍 Testing API call...")
        try:
            quote = breeze.get_quotes(stock_code='INFY', exchange_code='NSE')
            if quote and quote.get('Success'):
                print("✓ API call successful!")
                print(f"  Sample data: INFY quote retrieved")
                return True
            else:
                print("⚠ API call executed but returned no data")
                print(f"  Response: {quote}")
                return True  # Still OK if structure is fine
        except Exception as e:
            print(f"⚠ API call failed: {e}")
            print("  This might be due to market hours or API rate limits")
            return True  # Still OK for structure validation
    
    except Exception as e:
        print(f"✗ Failed to initialize Breeze: {e}")
        return False

def main():
    print("\n" + "#"*80)
    print("# BREEZE REAL DATA BACKTEST SETUP")
    print("#"*80 + "\n")
    
    # Check connection
    if not check_breeze_connection():
        print("\n❌ Breeze connection check failed!")
        print("\nTo fix this:")
        print("1. Check your .env file has correct credentials")
        print("2. Verify BREEZE_API_KEY and BREEZE_SECRET_KEY are set")
        print("3. Ensure API keys are valid and not expired")
        sys.exit(1)
    
    # Ask which stocks to test
    print("\n" + "="*80)
    print("SELECT STOCKS FOR BACKTEST")
    print("="*80 + "\n")
    
    print("Available stocks:")
    print("  1. INFY (Infosys)")
    print("  2. RELIANCE (Reliance Industries)")
    print("  3. TCS (Tata Consultancy Services)")
    print("  4. HDFC (HDFC Bank)")
    print("  5. All of above")
    
    choice = input("\nSelect option (1-5) [default: 5]: ").strip() or "5"
    
    stock_map = {
        '1': ['INFY'],
        '2': ['RELIANCE'],
        '3': ['TCS'],
        '4': ['HDFC'],
        '5': ['INFY', 'RELIANCE', 'TCS', 'HDFC']
    }
    
    stocks = stock_map.get(choice, ['INFY', 'RELIANCE', 'TCS', 'HDFC'])
    
    print(f"\n✓ Selected: {', '.join(stocks)}")
    
    # Ask for period
    print("\n" + "="*80)
    print("SELECT BACKTEST PERIOD")
    print("="*80 + "\n")
    
    print("Options:")
    print("  1. 1 month (20 trading days)")
    print("  2. 3 months (60 trading days)")
    print("  3. 6 months (120 trading days)")
    print("  4. 1 year (252 trading days)")
    
    period_choice = input("\nSelect option (1-4) [default: 4]: ").strip() or "4"
    
    period_map = {
        '1': 20,
        '2': 60,
        '3': 120,
        '4': 252
    }
    
    days = period_map.get(period_choice, 252)
    print(f"\n✓ Selected: {days} trading days")
    
    # Confirm
    print("\n" + "="*80)
    print("BACKTEST CONFIGURATION")
    print("="*80)
    print(f"Stocks:          {', '.join(stocks)}")
    print(f"Period:          {days} trading days")
    print(f"Initial Capital: ₹300,000")
    print(f"Strategy:        Buy-Hold-Trend with Market Time Filter")
    print("="*80 + "\n")
    
    confirm = input("Proceed with backtest? (y/n) [default: y]: ").strip().lower() or "y"
    
    if confirm != 'y':
        print("✗ Backtest cancelled")
        sys.exit(0)
    
    # Run backtest
    print("\n🚀 Starting backtest with real Breeze data...\n")
    
    try:
        from backtest_with_breeze_real_data import run_backtest_for_stocks
        run_backtest_for_stocks(stocks, days_back=days)
        
        print("\n" + "="*80)
        print("✓ BACKTEST COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
        print("Results saved to backtest_breeze_*.json files")
        print("Review the output above for detailed analysis")
        
    except Exception as e:
        print(f"\n✗ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
