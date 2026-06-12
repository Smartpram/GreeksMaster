"""
ML-Enhanced 10-Minute Trading Scheduler with Online Learning
- Schedule trading every 10 minutes during market hours
- Auto-retrain models every 100 trades
- Track learning progress and model improvements
"""

import os
import sys
import time
import logging
from datetime import datetime, time as datetime_time
from pathlib import Path
import schedule

# Setup logging
log_dir = Path("logs/ml_scheduler")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"ml_scheduler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import the ML-enhanced engine
sys.path.insert(0, str(Path(__file__).parent))
from trading_engine_ml_enhanced import MLEnhancedTradingEngine


class MLTradingScheduler:
    """Schedule ML-enhanced trading with online learning"""
    
    def __init__(self):
        self.engine = MLEnhancedTradingEngine()
        self.execution_count = 0
        self.total_trades_today = 0
        self.total_pnl_today = 0
        self.session_start = datetime.now()
        
    def execute_trading(self):
        """Execute one trading cycle"""
        try:
            logger.info(f"[EXECUTION #{self.execution_count + 1}] Starting trading cycle...")
            
            result = self.engine.execute_ml_trading()
            
            self.execution_count += 1
            self.total_trades_today += result['trades_executed']
            self.total_pnl_today += result['total_pnl']
            
            logger.info(f"[SUMMARY] Execution #{self.execution_count}")
            logger.info(f"  - Signals: {result['signals_generated']}")
            logger.info(f"  - Trades: {result['trades_executed']}")
            logger.info(f"  - P&L: {result['total_pnl']:.2f}")
            logger.info(f"  - Session P&L: {self.total_pnl_today:.2f}")
            logger.info(f"  - Model Version: {self.engine.ml_manager.model_version}")
            logger.info(f"  - Training Samples: {self.engine.ml_manager.training_samples}")
            logger.info(f"  - Buffer Size: {len(self.engine.ml_manager.recent_trades)}")
            
            # Check if models are being retrained
            if self.engine.ml_manager.last_training_time:
                time_since_train = datetime.now() - self.engine.ml_manager.last_training_time
                logger.info(f"  - Last Model Training: {time_since_train.total_seconds():.0f}s ago")
            
        except Exception as e:
            logger.error(f"[ERROR] Trading execution failed: {e}")
            logger.error(f"Traceback: {str(e)}", exc_info=True)
    
    def schedule_10min_executions(self):
        """Schedule all 10-minute execution times during market hours"""
        times = []
        
        # Generate 10-minute intervals from 09:15 to 15:25 IST
        start_hour = 9
        start_min = 15
        end_hour = 15
        end_min = 25
        
        current = start_hour * 60 + start_min
        end = end_hour * 60 + end_min
        
        while current <= end:
            hour = current // 60
            minute = current % 60
            time_str = f"{hour:02d}:{minute:02d}"
            times.append(time_str)
            current += 10
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("ML-ENHANCED 10-MINUTE TRADING SCHEDULER")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Configuration:")
        logger.info("  - Mode: ML-Enhanced with Online Learning")
        logger.info("  - Interval: Every 10 minutes")
        logger.info("  - Market Hours: 09:15 AM - 03:30 PM IST")
        logger.info("  - Daily Executions: " + str(len(times)))
        logger.info("")
        logger.info("Online Learning Config:")
        logger.info("  - Auto-retrain threshold: 100 trades")
        logger.info("  - Models: XGBoost, Random Forest, Gradient Boosting")
        logger.info("  - Feature extraction: 12 technical indicators")
        logger.info("  - Ensemble voting: Average of 3 models")
        logger.info("")
        logger.info("Execution Schedule (IST):")
        logger.info("")
        
        for i, t in enumerate(times, 1):
            schedule.every().day.at(t).do(self.execute_trading)
            logger.info(f"  {i:2d}. {t}")
        
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"Total Daily Executions: {len(times)}")
        logger.info("=" * 80)
        logger.info("")
    
    def run_scheduler(self):
        """Main scheduler loop"""
        logger.info("[SCHEDULER] Starting main event loop...")
        logger.info("[SCHEDULER] Press Ctrl+C to stop")
        logger.info("")
        
        try:
            while True:
                # Run pending jobs
                schedule.run_pending()
                
                # Check every second
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("")
            logger.info("=" * 80)
            logger.info("SCHEDULER STOPPED BY USER")
            logger.info("=" * 80)
            logger.info("")
            logger.info("Session Summary:")
            logger.info(f"  - Total Executions: {self.execution_count}")
            logger.info(f"  - Total Trades: {self.total_trades_today}")
            logger.info(f"  - Session P&L: {self.total_pnl_today:.2f}")
            logger.info(f"  - Final Model Version: {self.engine.ml_manager.model_version}")
            logger.info(f"  - Total Training Samples: {self.engine.ml_manager.training_samples}")
            logger.info("")
            logger.info("=" * 80)


def main():
    """Entry point"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("ML-ENHANCED TRADING SYSTEM WITH ONLINE LEARNING")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Features:")
    logger.info("  1. Real-time Trading")
    logger.info("     - Technical indicators (SMA, RSI, MACD, Bollinger, ATR, ADX)")
    logger.info("     - ML ensemble (XGBoost + Random Forest + Gradient Boosting)")
    logger.info("     - Hybrid confidence scoring")
    logger.info("")
    logger.info("  2. Online Learning")
    logger.info("     - Auto-retrain every 100 trades")
    logger.info("     - Models learn from paper trading results")
    logger.info("     - Automatic model versioning")
    logger.info("     - Performance tracking")
    logger.info("")
    logger.info("  3. Real-time Monitoring")
    logger.info("     - Per-execution reports (JSON)")
    logger.info("     - Cumulative P&L tracking")
    logger.info("     - Model version history")
    logger.info("     - Training progress logs")
    logger.info("")
    logger.info("=" * 80)
    logger.info("")
    
    # Create and run scheduler
    scheduler = MLTradingScheduler()
    scheduler.schedule_10min_executions()
    scheduler.run_scheduler()


if __name__ == "__main__":
    main()
