"""
10-Minute Trading Scheduler
Executes trading every 10 minutes during market hours (09:15-15:30 IST)

Schedule:
  09:15, 09:25, 09:35, 09:45... every 10 minutes until 15:30 IST
  Total: ~40 executions per trading day

Features:
- 100x 10-minute candles per ticker (16+ hours of intraday data)
- Optimized indicators for fast signals
- Real-time Breeze API integration
- Fee-aware P&L (ICICI Direct IVALUE plan)
- Cumulative daily P&L tracking

Usage:
    python schedule_10min_trading.py
"""

import os
import sys
import logging
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
from subprocess import run, PIPE
import threading

# Setup logging
LOG_DIR = Path(__file__).parent / "logs" / "10min_scheduler"
LOG_DIR.mkdir(parents=True, exist_ok=True)

log_file = LOG_DIR / f"10min_scheduler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TenMinuteScheduler:
    """Scheduler for 10-minute trading executions"""
    
    def __init__(self):
        self.engine_script = Path(__file__).parent / "trading_engine_10min.py"
        self.execution_count = 0
        self.current_process = None
        self.logger = logging.getLogger(__name__)
        
        if not self.engine_script.exists():
            self.logger.error(f"Engine script not found: {self.engine_script}")
            sys.exit(1)
        
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("10-MINUTE TRADING SCHEDULER - INITIALIZED")
        self.logger.info("=" * 80)
        self.logger.info(f"Engine: {self.engine_script.name}")
        self.logger.info(f"Log: {log_file}")
        self.logger.info(f"Schedule: Every 10 minutes (09:15-15:30 IST)")
        self.logger.info(f"Expected executions per day: 40+")
        self.logger.info("")
    
    def execute_10min_trading(self):
        """Execute 10-minute trading cycle"""
        try:
            self.execution_count += 1
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.logger.info("")
            self.logger.info("=" * 80)
            self.logger.info(f"[EXECUTION #{self.execution_count}] 10-Minute Trading")
            self.logger.info(f"Time: {current_time}")
            self.logger.info("=" * 80)
            
            # Run the trading engine
            result = run(
                [sys.executable, str(self.engine_script)],
                cwd=self.engine_script.parent,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout per execution
            )
            
            if result.returncode == 0:
                self.logger.info(f"[SUCCESS] Execution completed")
                
                # Extract key metrics from output
                lines = result.stdout.split('\n')
                for line in lines:
                    if any(keyword in line for keyword in ['[EXECUTION SUMMARY]', 'Trades:', 'Gross P&L:', 'Net P&L:', 'Cumulative']):
                        if line.strip():
                            self.logger.info(f"  {line.strip()}")
            else:
                self.logger.error(f"[ERROR] Execution failed")
                self.logger.error(f"Return code: {result.returncode}")
                if result.stderr:
                    self.logger.error(f"Error: {result.stderr[:200]}")
            
        except Exception as e:
            self.logger.error(f"[EXCEPTION] {str(e)}")
    
    def schedule_10min_executions(self):
        """Schedule executions every 10 minutes during market hours"""
        self.logger.info("[SCHEDULER] Setting up 10-MINUTE TRADING SESSIONS (IST)")
        self.logger.info("=" * 80)
        self.logger.info("MARKET HOURS: 09:15 AM - 03:30 PM IST")
        self.logger.info("EXECUTION INTERVAL: Every 10 minutes")
        self.logger.info("")
        self.logger.info("Execution Times:")
        
        # Generate execution times every 10 minutes
        start_time = datetime.strptime("09:15", "%H:%M")
        end_time = datetime.strptime("15:30", "%H:%M")
        
        execution_times = []
        current = start_time
        
        while current <= end_time:
            time_str = current.strftime("%H:%M")
            execution_times.append(time_str)
            self.logger.info(f"  {time_str}")
            current += timedelta(minutes=10)
        
        self.logger.info("")
        self.logger.info(f"Total executions: {len(execution_times)}")
        self.logger.info("")
        
        # Schedule each execution time
        for exec_time in execution_times:
            schedule.every().day.at(exec_time).do(self.execute_10min_trading)
        
        self.logger.info("[SCHEDULER] All 10-minute executions scheduled")
        self.logger.info("[INFO] Press Ctrl+C to stop")
        self.logger.info("")
        
        return self
    
    def run_scheduler(self):
        """Run the main scheduler loop"""
        self.logger.info("[SCHEDULER] Starting main loop...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("\n[SCHEDULER] Shutting down...")
            self.logger.info("[INFO] Scheduler stopped by user")
            
            # Kill any running process
            if self.current_process and self.current_process.poll() is None:
                self.current_process.terminate()


def main():
    """Main entry point"""
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("10-MINUTE TRADING SYSTEM")
    logger.info("=" * 80)
    logger.info("Mode: Every 10 minutes (09:15-15:30 IST)")
    logger.info("Candles: 100x 10-minute bars per ticker")
    logger.info("Coverage: ~16+ hours of intraday data")
    logger.info("Fee Plan: ICICI Direct IVALUE")
    logger.info("=" * 80)
    
    # Start scheduler
    scheduler = TenMinuteScheduler()
    scheduler.schedule_10min_executions()
    scheduler.run_scheduler()


if __name__ == "__main__":
    main()
