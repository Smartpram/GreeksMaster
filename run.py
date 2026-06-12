"""
MyBreezeApp - Main Application Runner
Features fee-aware paper trading and live trading with realistic P&L calculations
"""
import os
import sys
import logging
from app.main import create_app
from app.config import Config
from app.brokerage_fees import BrokerageFeeCalculator, BrokeragePlan

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mybreeze.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    try:
        # Validate configuration
        Config.validate_config()
        logger.info("Configuration validated successfully")
        
        # Initialize fee calculator and show info
        fee_calc = BrokerageFeeCalculator(plan=BrokeragePlan.IVALUE)
        logger.info("\n📊 Fee Configuration:")
        logger.info("-" * 60)
        logger.info("✓ Fee-Aware Trading Enabled (ICICI Direct)")
        logger.info("  Default Plan: IVALUE (₹299 one-time, ₹20/trade)")
        logger.info("  All P&L calculations include realistic fees")
        logger.info("  Features: Brokerage, Exchange, STT, GST, SEBI, Stamp Duty")
        logger.info("-" * 60)
        
        # Create Flask app
        app = create_app()
        
        # Get port from environment or use default
        port = int(os.environ.get('PORT', 5000))
        host = os.environ.get('HOST', '0.0.0.0')
        debug = os.environ.get('DEBUG', 'False').lower() == 'true'
        
        logger.info(f"\nStarting MyBreezeApp on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        logger.info(f"Paper trading: {Config.PAPER_TRADING}")
        logger.info(f"Fee-aware P&L: ENABLED ✓")
        
        # Run the application
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your .env file and ensure all required variables are set")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()