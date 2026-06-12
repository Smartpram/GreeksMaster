#!/usr/bin/env python3
"""
Quick Start: Run Advanced Strategies Backtest with Real Breeze Data
This is the fastest way to get real market data backtesting running.
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_banner():
    """Print startup banner"""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║     ADVANCED STRATEGIES BACKTEST - REAL BREEZE API DATA           ║
║                                                                    ║
║  This will test 8 trading strategies on 2 stocks with real data   ║
║  using REAL market data from ICICIDirect Breeze API               ║
║                                                                    ║
║  Strategies: Gamma Scalping, Order Flow, VCP, PEAD                ║
║              + 4 Options strategies                                ║
║                                                                    ║
║  Symbols: TCS, NIFTY (Available in your Breeze API plan)          ║
║                                                                    ║
║  Total Tests: 16 backtests (2 symbols × 8 strategies)             ║
║  Time: ~5-15 seconds                                               ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
    """)

def check_prerequisites():
    """Check if all prerequisites are met"""
    logger.info("\n📋 Checking prerequisites...")
    
    checks = {
        '✓ Python packages': lambda: check_imports(),
        '✓ Project structure': lambda: check_project_structure(),
        '✓ Breeze credentials': lambda: check_credentials(),
    }
    
    all_passed = True
    for check_name, check_func in checks.items():
        try:
            if check_func():
                logger.info(f"  {check_name}")
            else:
                logger.error(f"  ✗ {check_name} FAILED")
                all_passed = False
        except Exception as e:
            logger.error(f"  ✗ {check_name}: {e}")
            all_passed = False
    
    return all_passed

def check_imports():
    """Verify required Python packages are installed"""
    try:
        import pandas
        import numpy
        import requests
        return True
    except ImportError as e:
        logger.error(f"Missing package: {e}")
        return False

def check_project_structure():
    """Verify project structure exists"""
    required_files = [
        'app/strategies/advanced_strategies_suite.py',
        'app/services/breeze_api.py',
        'run_advanced_strategies_backtest.py',
        'app/config.py',
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            logger.error(f"Missing: {file_path}")
            return False
    
    return True

def check_credentials():
    """Check if Breeze credentials are configured"""
    try:
        from app.config import Config
        
        # Check if at least the critical credentials are present
        has_api_key = bool(Config.BREEZE_API_KEY)
        has_secret = bool(Config.BREEZE_SECRET_KEY)
        has_user_id = bool(Config.BREEZE_USER_ID)
        
        if not (has_api_key and has_secret and has_user_id):
            logger.warning("⚠️  Some Breeze credentials missing (will use synthetic fallback)")
            return True  # Still allow to run with synthetic data
        
        return True
    except Exception as e:
        logger.warning(f"Could not verify credentials: {e}")
        return True  # Allow to run anyway

def display_credentials_status():
    """Display which credentials are set"""
    try:
        from app.config import Config
        
        logger.info("\n🔐 Credential Status:")
        creds = {
            'API_KEY': Config.BREEZE_API_KEY,
            'SECRET_KEY': Config.BREEZE_SECRET_KEY,
            'SESSION_TOKEN': Config.BREEZE_SESSION_TOKEN,
            'USER_ID': Config.BREEZE_USER_ID,
        }
        
        for name, value in creds.items():
            if value:
                masked = value[:8] + '...' if len(str(value)) > 8 else '***'
                logger.info(f"  ✓ {name}: {masked}")
            else:
                logger.info(f"  ✗ {name}: NOT SET (will use synthetic data)")
        
        logger.info("\n  💡 For real data: Set BREEZE_SESSION_TOKEN environment variable")
        logger.info("     See: BREEZE_CREDENTIALS_SETUP.md for instructions")
        
    except Exception as e:
        logger.warning(f"Could not read credentials: {e}")

def run_backtest():
    """Run the advanced strategies backtest"""
    logger.info("\n" + "="*70)
    logger.info("🚀 STARTING BACKTEST")
    logger.info("="*70)
    
    try:
        from run_advanced_strategies_backtest import AdvancedStrategiesBacktester
        
        # Create backtester instance
        backtester = AdvancedStrategiesBacktester()
        
        # Define symbols (stocks available in your Breeze API plan)
        symbols = ['TCS', 'NIFTY']
        
        logger.info(f"\n📊 Testing {len(symbols)} stocks with real Breeze API data...")
        logger.info(f"Symbols: {', '.join(symbols)}")
        logger.info(f"Strategies: 8 (4 Equity + 4 Options)")
        logger.info(f"Total backtests: {len(symbols) * 8}")
        
        # Run backtest
        results = backtester.run_backtest(symbols)
        
        logger.info("\n" + "="*70)
        logger.info("✅ BACKTEST COMPLETED SUCCESSFULLY")
        logger.info("="*70)
        
        logger.info(f"\n📈 Results Summary:")
        logger.info(f"  • Raw results: ADVANCED_STRATEGIES_BACKTEST_RESULTS.json")
        logger.info(f"  • Detailed analysis: ADVANCED_STRATEGIES_BACKTEST_RESULTS.md")
        logger.info(f"  • Executive summary: ADVANCED_STRATEGIES_EXEC_SUMMARY.md")
        
        logger.info(f"\n📋 Next Steps:")
        logger.info(f"  1. Open ADVANCED_STRATEGIES_EXEC_SUMMARY.md")
        logger.info(f"  2. Identify top-performing strategies")
        logger.info(f"  3. Review recommendations")
        logger.info(f"  4. Set up paper trading (next phase)")
        
        return 0
        
    except ImportError as e:
        logger.error(f"❌ Import Error: {e}")
        logger.error("Make sure you're in the correct directory: c:\\Data\\MyBreezeApp")
        return 1
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        logger.error("\nTroubleshooting:")
        logger.error("  1. Check BREEZE_CREDENTIALS_SETUP.md for credential issues")
        logger.error("  2. Verify project structure is intact")
        logger.error("  3. Check Python environment is configured")
        import traceback
        logger.debug(traceback.format_exc())
        return 1

def main():
    """Main entry point"""
    print_banner()
    
    # Check prerequisites
    if not check_prerequisites():
        logger.error("\n❌ Prerequisites check failed")
        logger.info("\nTo fix missing packages, run:")
        logger.info("  pip install pandas numpy requests python-dotenv")
        return 1
    
    # Display credential status
    display_credentials_status()
    
    # Ask for confirmation
    logger.info("\n" + "="*70)
    response = input("Continue with backtest? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y', 'ok']:
        logger.info("Backtest cancelled.")
        return 0
    
    # Run backtest
    return run_backtest()

if __name__ == '__main__':
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    # Run main
    exit_code = main()
    
    if exit_code == 0:
        logger.info("\n✨ Backtest pipeline completed successfully!")
    else:
        logger.error("\n⚠️  Backtest pipeline encountered issues")
    
    sys.exit(exit_code)
