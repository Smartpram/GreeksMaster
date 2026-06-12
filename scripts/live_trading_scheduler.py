"""
Live Paper Trading Scheduler
Runs the live trading pipeline continuously or on a schedule

Supports:
- Continuous background execution
- Scheduled execution (hourly, daily, etc.)
- Real-time monitoring
- Automatic log rotation
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from live_paper_trading_with_retraining import LivePaperTradingPipeline

# Load environment
load_dotenv()

# Setup logging
LOG_DIR = Path(__file__).parent / "logs" / "scheduler"
LOG_DIR.mkdir(parents=True, exist_ok=True)

log_file = LOG_DIR / f"scheduler_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TradingScheduler:
    """Manages scheduled execution of trading pipeline"""
    
    def __init__(self, tickers=None, execution_mode='hourly'):
        """
        Args:
            tickers: List of tickers to trade
            execution_mode: 'continuous', 'hourly', 'daily', or integer (minutes)
        """
        self.tickers = tickers or ['NIFTY-I', 'BANKNIFTY-I', 'FINNIFTY-I']
        self.execution_mode = execution_mode
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.execution_count = 0
        self.start_time = None
    
    def run_trading_pipeline(self):
        """Execute the trading pipeline"""
        try:
            self.execution_count += 1
            self.logger.info(f"\n{'='*80}")
            self.logger.info(f"EXECUTION #{self.execution_count}")
            self.logger.info(f"Time: {datetime.now()}")
            self.logger.info(f"{'='*80}")
            
            pipeline = LivePaperTradingPipeline(
                tickers=self.tickers,
                execution_frequency=self.execution_mode
            )
            pipeline.run()
            
            self.logger.info(f"[SUCCESS] Execution #{self.execution_count} completed")
        
        except Exception as e:
            self.logger.error(f"[ERROR] Execution #{self.execution_count} failed: {str(e)}", exc_info=True)
    
    def schedule_hourly(self):
        """Schedule execution every hour during market hours"""
        self.logger.info("[SCHEDULER] Scheduling hourly execution (9:15 AM - 3:45 PM)")
        
        # Schedule every hour from 9:15 AM to 3:45 PM
        schedule.every().hour.at(":15").do(self.run_trading_pipeline)
        schedule.every().hour.at(":45").do(self.run_trading_pipeline)
        
        return self._run_scheduler()
    
    def schedule_daily(self):
        """Schedule execution once daily"""
        self.logger.info("[SCHEDULER] Scheduling daily execution at 3:30 PM")
        
        schedule.every().day.at("15:30").do(self.run_trading_pipeline)
        
        return self._run_scheduler()
    
    def schedule_interval(self, minutes):
        """Schedule execution at regular intervals"""
        self.logger.info(f"[SCHEDULER] Scheduling execution every {minutes} minutes")
        
        schedule.every(minutes).minutes.do(self.run_trading_pipeline)
        
        return self._run_scheduler()
    
    def run_continuous(self):
        """Run continuously with delay between executions"""
        self.logger.info("[SCHEDULER] Starting continuous execution mode")
        self.is_running = True
        self.start_time = datetime.now()
        
        try:
            while self.is_running:
                self.logger.info(f"\n[CONTINUOUS] Execution at {datetime.now()}")
                self.run_trading_pipeline()
                
                # Wait 1 hour before next execution
                self.logger.info("[CONTINUOUS] Waiting 3600 seconds (1 hour) before next execution...")
                time.sleep(3600)  # 1 hour
        
        except KeyboardInterrupt:
            self.logger.info("[SCHEDULER] Keyboard interrupt received, stopping...")
        except Exception as e:
            self.logger.error(f"[SCHEDULER ERROR] {str(e)}", exc_info=True)
        finally:
            self.is_running = False
            elapsed = datetime.now() - self.start_time
            self.logger.info(f"[SCHEDULER] Stopped after {elapsed} elapsed, {self.execution_count} executions")
    
    def _run_scheduler(self):
        """Run the schedule loop"""
        self.logger.info("[SCHEDULER] Starting schedule loop...")
        self.is_running = True
        self.start_time = datetime.now()
        
        try:
            # Initial run
            self.run_trading_pipeline()
            
            # Schedule loop
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        except KeyboardInterrupt:
            self.logger.info("[SCHEDULER] Keyboard interrupt received, stopping...")
        except Exception as e:
            self.logger.error(f"[SCHEDULER ERROR] {str(e)}", exc_info=True)
        finally:
            self.is_running = False
            elapsed = datetime.now() - self.start_time
            self.logger.info(f"[SCHEDULER] Stopped after {elapsed} elapsed, {self.execution_count} executions")


def main():
    """Main entry point"""
    
    # Configuration
    TICKERS = [
        'NIFTY-I',
        'BANKNIFTY-I',
        'FINNIFTY-I',
    ]
    
    # Choose execution mode
    EXECUTION_MODE = 'hourly'  # Options: 'continuous', 'hourly', 'daily', or integer (minutes)
    
    logger.info(f"\n{'='*80}")
    logger.info(f"LIVE PAPER TRADING SCHEDULER")
    logger.info(f"Start Time: {datetime.now()}")
    logger.info(f"Tickers: {TICKERS}")
    logger.info(f"Execution Mode: {EXECUTION_MODE}")
    logger.info(f"{'='*80}\n")
    
    scheduler = TradingScheduler(tickers=TICKERS, execution_mode=EXECUTION_MODE)
    
    if EXECUTION_MODE == 'continuous':
        scheduler.run_continuous()
    elif EXECUTION_MODE == 'hourly':
        scheduler.schedule_hourly()
    elif EXECUTION_MODE == 'daily':
        scheduler.schedule_daily()
    elif isinstance(EXECUTION_MODE, int):
        scheduler.schedule_interval(EXECUTION_MODE)
    else:
        logger.error(f"Unknown execution mode: {EXECUTION_MODE}")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"SCHEDULER COMPLETE")
    logger.info(f"End Time: {datetime.now()}")
    logger.info(f"Total Executions: {scheduler.execution_count}")
    logger.info(f"{'='*80}\n")


if __name__ == '__main__':
    main()
