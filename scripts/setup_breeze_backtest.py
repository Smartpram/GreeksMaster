#!/usr/bin/env python3
"""
Setup Guide and Starter Script for Real Breeze API Backtest
This script guides you through setting up real Breeze API authentication
and running the advanced strategies backtest with real data.
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_breeze_credentials():
    """Check if Breeze API credentials are configured"""
    from app.config import Config
    
    config = Config()
    
    logger.info("\n" + "="*80)
    logger.info("🔍 CHECKING BREEZE API CREDENTIALS")
    logger.info("="*80)
    
    # Check each credential
    credentials = {
        'API_KEY': config.BREEZE_API_KEY,
        'SECRET_KEY': config.BREEZE_SECRET_KEY,
        'SESSION_TOKEN': config.BREEZE_SESSION_TOKEN,
        'USER_ID': config.BREEZE_USER_ID,
    }
    
    all_set = True
    for cred_name, cred_value in credentials.items():
        if cred_value:
            # Mask sensitive values
            if len(str(cred_value)) > 20:
                masked = str(cred_value)[:8] + '...' + str(cred_value)[-8:]
            else:
                masked = '***SET***'
            logger.info(f"✓ {cred_name}: {masked}")
        else:
            logger.error(f"✗ {cred_name}: NOT SET")
            all_set = False
    
    return all_set


def setup_credentials():
    """Guide user through setting up Breeze credentials"""
    logger.info("\n" + "="*80)
    logger.info("📝 BREEZE API CREDENTIALS SETUP")
    logger.info("="*80)
    
    logger.info("""
To use real Breeze API data, you need to:

1. GET YOUR CREDENTIALS
   ├─ Go to: https://www.icicidirect.com/
   ├─ Login to your account
   ├─ Go to Settings → API Keys
   └─ Copy your API Key and Secret Key

2. GET SESSION TOKEN
   ├─ Run: python -c "from app.services.breeze_api import BreezeAPIService; srv = BreezeAPIService(); print(srv.login())"
   ├─ Visit the login URL provided
   ├─ Authenticate and copy the session token
   └─ The token is valid for 24 hours

3. SET ENVIRONMENT VARIABLES
   On Windows (PowerShell):
   └─ $env:BREEZE_API_KEY = "your_api_key_here"
   └─ $env:BREEZE_SECRET_KEY = "your_secret_key_here"
   └─ $env:BREEZE_SESSION_TOKEN = "your_session_token_here"
   └─ $env:BREEZE_USER_ID = "your_user_id_here"

   OR in .env file:
   └─ BREEZE_API_KEY=your_api_key_here
   └─ BREEZE_SECRET_KEY=your_secret_key_here
   └─ BREEZE_SESSION_TOKEN=your_session_token_here
   └─ BREEZE_USER_ID=your_user_id_here

4. VERIFY SETUP
   └─ Run this script again to verify credentials are loaded
    """)


def run_backtest_with_real_data():
    """Run the advanced strategies backtest with real Breeze data"""
    try:
        from run_advanced_strategies_backtest import AdvancedStrategiesBacktester
        
        logger.info("\n" + "="*80)
        logger.info("🚀 RUNNING BACKTEST WITH REAL BREEZE API DATA")
        logger.info("="*80)
        
        # Initialize backtester
        backtester = AdvancedStrategiesBacktester()
        
        # Run backtest on multiple symbols
        symbols = ['NIFTY', 'INFY', 'RELIANCE', 'HDFC', 'BANKNIFTY', 'TCS', 'SBIN', 'ICICIBANK']
        
        logger.info(f"\nTesting {len(symbols)} symbols...")
        logger.info(f"Symbols: {', '.join(symbols)}\n")
        
        results = backtester.run_backtest(symbols)
        
        logger.info("\n" + "="*80)
        logger.info("✅ BACKTEST COMPLETE WITH REAL DATA")
        logger.info("="*80)
        logger.info(f"Tested {len(results)} symbols")
        logger.info(f"Results saved to: ADVANCED_STRATEGIES_BACKTEST_RESULTS.json")
        logger.info(f"Summary available in: ADVANCED_STRATEGIES_BACKTEST_RESULTS.md")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}", exc_info=True)
        return 1


def main():
    """Main entry point"""
    logger.info("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                 ADVANCED STRATEGIES - REAL DATA BACKTEST                  ║
║                                                                           ║
║  This script will run your 8 advanced trading strategies using REAL       ║
║  market data from the Breeze API (ICICIDirect).                          ║
║                                                                           ║
║  Strategies: Gamma Scalping, Order Flow, VCP, PEAD + Options strategies  ║
║  Symbols: NIFTY, INFY, RELIANCE, HDFC, BANKNIFTY, TCS, SBIN, ICICIBANK   ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Check if credentials are set
    has_credentials = check_breeze_credentials()
    
    if not has_credentials:
        logger.error("\n⚠️  MISSING BREEZE API CREDENTIALS")
        setup_credentials()
        logger.info("\n📌 After setting up credentials, run this script again:")
        logger.info("   python setup_breeze_backtest.py")
        return 1
    
    # Confirm before running backtest
    logger.info("\n" + "="*80)
    logger.info("⚠️  IMPORTANT NOTES:")
    logger.info("="*80)
    logger.info("""
1. REAL API CALLS: This will make real API calls to Breeze
   → Each symbol will fetch 90 days of historical data
   → Expect: ~100-200 API calls total
   → Rate limits: Check your Breeze API plan limits

2. SESSION TOKEN: Your session token is time-limited
   → Valid for 24 hours from generation
   → If it expires, you'll get a fallback to synthetic data
   → Solution: Generate a new session token

3. MARKET DATA: Uses daily (1day) candlestick data
   → More granular data (1min, 5min) may also work
   → Depends on your Breeze API subscription level

4. EXECUTION TIME: ~10-30 seconds for full backtest
   → 8 symbols × 8 strategies = 64 backtests
   → Gamma Scalping is the most time-intensive

5. RESULTS: All results saved to JSON and markdown files
   → ADVANCED_STRATEGIES_BACKTEST_RESULTS.json (raw data)
   → ADVANCED_STRATEGIES_BACKTEST_RESULTS.md (analysis)
    """)
    
    # Ask for confirmation
    response = input("\n✅ Ready to proceed with REAL DATA backtest? (yes/no): ").strip().lower()
    if response not in ['yes', 'y', 'ok']:
        logger.info("Backtest cancelled.")
        return 1
    
    # Run backtest
    return run_backtest_with_real_data()


if __name__ == '__main__':
    sys.exit(main())
