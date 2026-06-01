#!/usr/bin/env python3
"""
Diagnostic Script: Verify all components before running backtest
This script checks:
1. Python environment and packages
2. Project structure
3. Breeze API configuration
4. Strategies can be imported
5. Data can be fetched
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def print_header(title):
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def check_python_version():
    """Check Python version"""
    print_header("1. Python Version")
    
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    logger.info(f"Python: {version}")
    
    if sys.version_info >= (3, 8):
        logger.info("✅ Python version is compatible (3.8+)")
        return True
    else:
        logger.error("❌ Python 3.8+ required")
        return False

def check_packages():
    """Check required packages"""
    print_header("2. Required Packages")
    
    required = {
        'pandas': 'Data manipulation',
        'numpy': 'Numerical computing',
        'requests': 'HTTP requests',
        'dotenv': 'Environment variables',
        'flask': 'Web framework',
    }
    
    missing = []
    for package, description in required.items():
        try:
            __import__(package)
            logger.info(f"✅ {package:15} - {description}")
        except ImportError:
            logger.error(f"❌ {package:15} - {description} (MISSING)")
            missing.append(package)
    
    if missing:
        logger.error(f"\n⚠️  Missing packages: {', '.join(missing)}")
        logger.info(f"Install with: pip install {' '.join(missing)}")
        return False
    
    return True

def check_project_structure():
    """Check project structure"""
    print_header("3. Project Structure")
    
    required_files = {
        'app/config.py': 'Configuration module',
        'app/strategies/advanced_strategies_suite.py': 'Advanced strategies (56KB)',
        'app/services/breeze_api.py': 'Breeze API service',
        'app/services/breeze_service_factory.py': 'Service factory',
        'run_advanced_strategies_backtest.py': 'Main backtest script',
        'run_backtest_real_data.py': 'Quick start script',
        'setup_breeze_backtest.py': 'Setup script',
    }
    
    missing = []
    for file_path, description in required_files.items():
        if Path(file_path).exists():
            logger.info(f"✅ {file_path:45} - {description}")
        else:
            logger.error(f"❌ {file_path:45} - {description} (MISSING)")
            missing.append(file_path)
    
    return len(missing) == 0

def check_breeze_credentials():
    """Check Breeze API credentials"""
    print_header("4. Breeze API Credentials")
    
    from app.config import Config
    
    credentials = {
        'BREEZE_API_KEY': 'API Key',
        'BREEZE_SECRET_KEY': 'Secret Key',
        'BREEZE_SESSION_TOKEN': 'Session Token',
        'BREEZE_USER_ID': 'User ID',
    }
    
    all_set = True
    for env_var, description in credentials.items():
        value = getattr(Config, env_var.replace('BREEZE_', 'BREEZE_'), None)
        
        if value:
            # Mask sensitive values
            if len(str(value)) > 20:
                masked = str(value)[:8] + '...' + str(value)[-8:]
            else:
                masked = '***'
            logger.info(f"✅ {description:20} - {masked}")
        else:
            logger.warning(f"⚠️  {description:20} - NOT SET (optional, uses synthetic fallback)")
            all_set = False
    
    if not all_set:
        logger.info("\n💡 For real Breeze data, set environment variables:")
        logger.info("   See: BREEZE_CREDENTIALS_SETUP.md")
    
    return True  # Not critical, uses synthetic fallback

def check_strategies():
    """Check if all strategies can be imported"""
    print_header("5. Strategy Imports")
    
    strategies = {
        'VolatilityContractionPattern': 'VCP (Volume Confirmation Pattern)',
        'StatisticalArbitrage': 'Pairs Trading',
        'OrderFlowMicrostructure': 'Order Flow Analysis',
        'PostEarningsAnnouncementDrift': 'PEAD (Post-Earnings)',
        'DeltaNeutralVolatilityHarvesting': 'Vol Harvesting',
        'VolatilityMeanReversion': 'Vol Mean Reversion',
        'GammaScalping': 'Gamma Scalping',
        'DynamicOptionsMonitorTrendFollowing': 'Options Momentum',
    }
    
    try:
        from app.strategies.advanced_strategies_suite import (
            VolatilityContractionPattern,
            StatisticalArbitrage,
            OrderFlowMicrostructure,
            PostEarningsAnnouncementDrift,
            DeltaNeutralVolatilityHarvesting,
            VolatilityMeanReversion,
            GammaScalping,
            DynamicOptionsMonitorTrendFollowing
        )
        
        strategy_classes = {
            'VolatilityContractionPattern': VolatilityContractionPattern,
            'StatisticalArbitrage': StatisticalArbitrage,
            'OrderFlowMicrostructure': OrderFlowMicrostructure,
            'PostEarningsAnnouncementDrift': PostEarningsAnnouncementDrift,
            'DeltaNeutralVolatilityHarvesting': DeltaNeutralVolatilityHarvesting,
            'VolatilityMeanReversion': VolatilityMeanReversion,
            'GammaScalping': GammaScalping,
            'DynamicOptionsMonitorTrendFollowing': DynamicOptionsMonitorTrendFollowing,
        }
        
        for strategy_name, description in strategies.items():
            if strategy_name in strategy_classes:
                logger.info(f"✅ {strategy_name:45} - {description}")
            else:
                logger.error(f"❌ {strategy_name:45} - {description} (NOT FOUND)")
                return False
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Failed to import strategies: {e}")
        return False

def check_breeze_service():
    """Check if Breeze service can be initialized"""
    print_header("6. Breeze Service")
    
    try:
        from app.services.breeze_service_factory import get_breeze_service
        
        service = get_breeze_service()
        logger.info(f"✅ Breeze service initialized: {type(service).__name__}")
        
        # Check if service has required methods
        required_methods = [
            'get_historical_data',
            'authenticate',
            'is_authenticated',
        ]
        
        for method in required_methods:
            if hasattr(service, method):
                logger.info(f"✅ Method available: {method}()")
            else:
                logger.warning(f"⚠️  Method missing: {method}()")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Breeze service: {e}")
        return False

def check_backtest_script():
    """Check if backtest script can be imported"""
    print_header("7. Backtest Script")
    
    try:
        from run_advanced_strategies_backtest import AdvancedStrategiesBacktester
        
        logger.info("✅ AdvancedStrategiesBacktester class can be imported")
        
        # Try to instantiate
        backtester = AdvancedStrategiesBacktester()
        logger.info("✅ AdvancedStrategiesBacktester can be instantiated")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to load backtest script: {e}")
        return False

def check_data_fetch():
    """Check if we can fetch data"""
    print_header("8. Data Fetch Test")
    
    try:
        from run_advanced_strategies_backtest import AdvancedStrategiesBacktester
        
        backtester = AdvancedStrategiesBacktester()
        
        # Try to fetch data for one symbol
        logger.info("Attempting to fetch data for NIFTY...")
        data = backtester.fetch_breeze_data('NIFTY', days=30, interval='1day')
        
        if data is not None and len(data) > 0:
            logger.info(f"✅ Successfully fetched {len(data)} rows of data")
            logger.info(f"   Columns: {', '.join(data.columns.tolist())}")
            logger.info(f"   Date range: {data.iloc[0,0] if 'DateTime' in data.columns else 'N/A'} to {data.iloc[-1,0] if 'DateTime' in data.columns else 'N/A'}")
            return True
        else:
            logger.warning("⚠️  Data fetch returned empty (this is okay - using fallback)")
            return True
            
    except Exception as e:
        logger.error(f"❌ Data fetch failed: {e}")
        return False

def generate_report(results):
    """Generate diagnostic report"""
    print_header("DIAGNOSTIC SUMMARY")
    
    checks = [
        ('Python Version', results[0]),
        ('Required Packages', results[1]),
        ('Project Structure', results[2]),
        ('Breeze Credentials', results[3]),
        ('Strategy Imports', results[4]),
        ('Breeze Service', results[5]),
        ('Backtest Script', results[6]),
        ('Data Fetch', results[7]),
    ]
    
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status:8} - {check_name}")
    
    print(f"\n{'-'*70}")
    logger.info(f"Overall: {passed}/{total} checks passed")
    print(f"{'-'*70}\n")
    
    if passed == total:
        logger.info("🎉 ALL CHECKS PASSED!")
        logger.info("\nYou're ready to run the backtest:")
        logger.info("  python run_backtest_real_data.py")
        return 0
    elif passed >= 6:
        logger.info("⚠️  MOST CHECKS PASSED")
        logger.info("\nYou can still run the backtest, but some features may be limited:")
        logger.info("  python run_backtest_real_data.py")
        return 0
    else:
        logger.error("❌ SEVERAL CHECKS FAILED")
        logger.error("\nPlease fix the issues above before running backtest")
        logger.error("\nCommon solutions:")
        logger.error("  1. Install packages: pip install pandas numpy requests python-dotenv")
        logger.error("  2. Check project structure is intact")
        logger.error("  3. Set Breeze credentials (optional, will use synthetic data)")
        return 1

def main():
    """Run all diagnostics"""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║          BACKTEST DIAGNOSTIC TOOL                                  ║
║                                                                    ║
║  This script verifies that everything is set up correctly         ║
║  for running the Advanced Strategies backtest.                    ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    logger.info(f"Starting diagnostics at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all checks
    results = [
        check_python_version(),
        check_packages(),
        check_project_structure(),
        check_breeze_credentials(),
        check_strategies(),
        check_breeze_service(),
        check_backtest_script(),
        check_data_fetch(),
    ]
    
    # Generate report
    exit_code = generate_report(results)
    
    return exit_code

if __name__ == '__main__':
    os.chdir(Path(__file__).parent)
    exit_code = main()
    sys.exit(exit_code)
