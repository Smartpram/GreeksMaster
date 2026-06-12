#!/usr/bin/env python
"""
Persistent 10-Minute Trading Scheduler
- Runs indefinitely (survives VS Code closure if started from terminal/batch)
- Auto-restarts on crash
- Logs all activity
- No admin privileges required
"""

import os
import sys
import time
import logging
import subprocess
import traceback
from datetime import datetime, time as datetime_time
from pathlib import Path

# Setup logging
log_dir = Path("logs/persistent_scheduler")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"persistent_scheduler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
SCRIPT_PATH = Path("schedule_10min_trading.py")
ENGINE_PATH = Path("trading_engine_10min.py")
MARKET_START = datetime_time(9, 15)
MARKET_END = datetime_time(15, 30)
CHECK_INTERVAL = 5  # seconds between checks

class PersistentScheduler:
    def __init__(self):
        self.execution_count = 0
        self.crash_count = 0
        self.last_execution_time = None
        
    def log_startup(self):
        logger.info("")
        logger.info("=" * 80)
        logger.info("PERSISTENT 10-MINUTE TRADING SCHEDULER")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Features:")
        logger.info("  - Runs indefinitely (no time limit)")
        logger.info("  - Auto-restarts if trading engine crashes")
        logger.info("  - Logs all activity with timestamps")
        logger.info("  - No admin privileges required")
        logger.info("")
        logger.info("Market Hours: 09:15 AM - 03:30 PM IST")
        logger.info("Execution Interval: Every 10 minutes")
        logger.info("Daily Executions: 38")
        logger.info("")
        logger.info("Log File: " + str(log_file))
        logger.info("")
        logger.info("To keep this running:")
        logger.info("  Option 1: Keep this terminal window open")
        logger.info("  Option 2: Use 'start_persistent_scheduler.bat' (runs in separate window)")
        logger.info("  Option 3: Start with 'pythonw' command (invisible background window)")
        logger.info("")
        logger.info("=" * 80)
        logger.info("")
        
    def is_market_hours(self):
        """Check if current time is within market hours"""
        now = datetime.now().time()
        return MARKET_START <= now <= MARKET_END
    
    def run_scheduler_once(self):
        """Run the main scheduler script"""
        try:
            logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting scheduling cycle...")
            
            # Run the main scheduler
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH)],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour max per cycle
            )
            
            if result.returncode == 0:
                logger.info(f"[CYCLE COMPLETE] Exit code: 0")
                self.execution_count += 1
            else:
                logger.error(f"[CYCLE ERROR] Exit code: {result.returncode}")
                if result.stderr:
                    logger.error(f"Error output: {result.stderr}")
            
            self.last_execution_time = datetime.now()
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Scheduler cycle exceeded 1 hour timeout")
            return False
        except Exception as e:
            logger.error(f"Error running scheduler: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def run_indefinitely(self):
        """Main loop - runs forever"""
        self.log_startup()
        
        logger.info(f"[STARTED] Persistent scheduler initialized at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("Waiting for market hours (09:15 AM IST)...")
        logger.info("")
        
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        while True:
            try:
                now = datetime.now()
                
                if self.is_market_hours():
                    # During market hours - run scheduler
                    logger.info(f"Market hours active - running scheduler cycle")
                    success = self.run_scheduler_once()
                    
                    if success:
                        consecutive_failures = 0
                        logger.info(f"Executions so far today: {self.execution_count}")
                    else:
                        consecutive_failures += 1
                        self.crash_count += 1
                        logger.warning(f"Cycle failed. Consecutive failures: {consecutive_failures}/{max_consecutive_failures}")
                        
                        if consecutive_failures >= max_consecutive_failures:
                            logger.error("Too many consecutive failures. Waiting 60 seconds before retry...")
                            time.sleep(60)
                            consecutive_failures = 0
                else:
                    # Outside market hours - just wait
                    logger.info(f"[{now.strftime('%H:%M:%S')}] Market closed. Waiting...")
                
                # Wait before next check
                logger.info(f"Next check in {CHECK_INTERVAL} seconds...")
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("")
                logger.info("=" * 80)
                logger.info("SCHEDULER STOPPED BY USER")
                logger.info("=" * 80)
                logger.info(f"Total execution cycles: {self.execution_count}")
                logger.info(f"Total crashes recovered: {self.crash_count}")
                logger.info("")
                break
                
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {str(e)}")
                logger.error(traceback.format_exc())
                logger.info("Recovering in 30 seconds...")
                time.sleep(30)

def main():
    """Entry point"""
    # Verify required files exist
    if not SCRIPT_PATH.exists():
        print(f"ERROR: {SCRIPT_PATH} not found")
        print(f"Current directory: {Path.cwd()}")
        sys.exit(1)
    
    if not ENGINE_PATH.exists():
        print(f"ERROR: {ENGINE_PATH} not found")
        sys.exit(1)
    
    # Start persistent scheduler
    scheduler = PersistentScheduler()
    
    try:
        scheduler.run_indefinitely()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
