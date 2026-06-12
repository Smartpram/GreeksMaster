"""
Schedule Live Paper Trading with Hybrid Data
Runs paper trading on a schedule for today and beyond

Modes:
- hourly: Run at :15 and :45 every hour (US market hours)
- daily: Run once daily at 3:30 PM IST
- continuous: Run every 1 hour continuously
- interval: Run every N minutes
"""

import os
import sys
import logging
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
from subprocess import run, PIPE

# Setup logging
LOG_DIR = Path(__file__).parent / "logs" / "scheduler"
LOG_DIR.mkdir(parents=True, exist_ok=True)

log_file = LOG_DIR / f"scheduler_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LiveTradingScheduler:
    """Schedule live trading pipeline execution"""
    
    def __init__(self, script_path='live_paper_trading_hybrid.py'):
        self.script_path = Path(__file__).parent / script_path
        self.execution_count = 0
        self.logger = logging.getLogger(__name__)
        
        if not self.script_path.exists():
            self.logger.error(f"Script not found: {self.script_path}")
            sys.exit(1)
    
    def run_trading_pipeline(self):
        """Execute the live trading pipeline"""
        try:
            self.execution_count += 1
            self.logger.info(f"\n{'='*80}")
            self.logger.info(f"[EXECUTION #{self.execution_count}] Starting live trading pipeline")
            self.logger.info(f"Time: {datetime.now()}")
            self.logger.info(f"{'='*80}\n")
            
            # Run the pipeline
            result = run(
                [sys.executable, str(self.script_path)],
                cwd=self.script_path.parent,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Log output
            if result.returncode == 0:
                self.logger.info(f"[SUCCESS] Execution #{self.execution_count} completed successfully")
                # Show key metrics from output
                for line in result.stdout.split('\n'):
                    if 'TRAINED' in line or 'SIGNAL' in line or 'TRADE' in line:
                        self.logger.info(f"  {line.strip()}")
            else:
                self.logger.error(f"[ERROR] Execution #{self.execution_count} failed")
                self.logger.error(f"Return code: {result.returncode}")
                if result.stderr:
                    self.logger.error(f"Error output:\n{result.stderr[:500]}")
            
            self.logger.info(f"\n[NEXT EXECUTION] Check scheduler logs for next run")
            
        except Exception as e:
            self.logger.error(f"[EXECUTION ERROR] {str(e)}", exc_info=True)
    
    def schedule_hourly(self):
        """Run at :15 and :45 every hour"""
        self.logger.info("[SCHEDULER] Setting up HOURLY execution (:15 and :45 every hour)")
        schedule.every().hour.at(":15").do(self.run_trading_pipeline)
        schedule.every().hour.at(":45").do(self.run_trading_pipeline)
        return self
    
    def schedule_daily(self, time_str="15:30"):
        """Run once daily at specified time (IST)"""
        self.logger.info(f"[SCHEDULER] Setting up DAILY execution at {time_str} IST")
        schedule.every().day.at(time_str).do(self.run_trading_pipeline)
        return self
    
    def schedule_trading_sessions(self):
        """
        Schedule according to NSE trading sessions (IST)
        Focuses on high-volatility, high-opportunity periods
        
        OPTIMAL TRADING WINDOWS:
        1. 09:15-09:30 AM: OPENING SURGE (HIGH VOLATILITY, HIGH VOLUME)
           - Massive price movement at market open
           - Best for momentum trades
           - Heavy volume ensures liquidity
        
        2. 10:00-10:30 AM: OPENING CONSOLIDATION (VERIFY TREND)
           - Market settles after initial surge
           - Confirm opening momentum
           - Early swing traders active
        
        3. 01:00-01:30 PM: MID-DAY PIVOT (TREND REVERSAL)
           - Market sentiment shifts
           - Key reversal point
           - Good for fade trades
        
        4. 03:00-03:30 PM: PRE-CLOSE SURGE (PROFIT-TAKING/COVERING)
           - Highest volatility of the day
           - Traders take profits/cover shorts
           - Strong momentum trades
        
        5. 03:30-03:45 PM: CLOSING BELL (LAST ORDERS)
           - Auction orders matched
           - Final closing price set
           - Last chance for day trades
        
        6. 03:50-04:00 PM: POST-CLOSING SESSION (CLOSING ORDERS)
           - Fixed-price closing orders
           - Overnight positioning
           - End-of-day consolidation
        """
        self.logger.info("[SCHEDULER] Setting up OPTIMAL TRADING SESSIONS (IST)")
        self.logger.info("=" * 70)
        self.logger.info("OPENING SURGE TRADES (9:15-9:30 AM)")
        self.logger.info("  09:15 AM - FIRST SIGNAL at market open")
        self.logger.info("  09:25 AM - FOLLOW-UP (catch continuation)")
        self.logger.info("")
        self.logger.info("INTRADAY TRADES")
        self.logger.info("  10:00 AM - Opening consolidation (verify trend)")
        self.logger.info("  01:00 PM - Mid-day pivot (trend reversal point)")
        self.logger.info("")
        self.logger.info("CLOSING SURGE TRADES (3:00-3:45 PM)")
        self.logger.info("  03:00 PM - Pre-close surge start (profit-taking begins)")
        self.logger.info("  03:15 PM - Pre-close continuation")
        self.logger.info("  03:30 PM - CLOSING BELL (last orders before close)")
        self.logger.info("  03:50 PM - POST-CLOSING (fixed-price orders)")
        self.logger.info("=" * 70)
        
        # ===== OPENING SURGE: 9:15-9:30 AM =====
        # Capture the opening momentum - HIGHEST VOLATILITY
        schedule.every().day.at("09:15").do(self.run_trading_pipeline)  # MARKET OPEN
        schedule.every().day.at("09:25").do(self.run_trading_pipeline)  # Follow continuation
        
        # ===== INTRADAY TRADES =====
        schedule.every().day.at("10:00").do(self.run_trading_pipeline)  # Opening consolidation
        schedule.every().day.at("13:00").do(self.run_trading_pipeline)  # Mid-day pivot
        
        # ===== CLOSING SURGE: 3:00-3:45 PM =====
        # Capture the pre-close volatility - SECOND HIGHEST VOLATILITY
        schedule.every().day.at("15:00").do(self.run_trading_pipeline)  # Pre-close surge START
        schedule.every().day.at("15:15").do(self.run_trading_pipeline)  # Pre-close continuation
        schedule.every().day.at("15:30").do(self.run_trading_pipeline)  # CLOSING BELL - LAST ORDERS
        
        # ===== POST-CLOSING SESSION: 3:40-4:00 PM =====
        schedule.every().day.at("15:50").do(self.run_trading_pipeline)  # Post-closing fixed price
        
        self.logger.info(f"\n[SCHEDULER] Setup complete - 9 executions per trading day")
        self.logger.info(f"[INFO] Optimal volatility windows configured")
        
        return self
    
    def schedule_interval(self, minutes=60):
        """Run every N minutes"""
        self.logger.info(f"[SCHEDULER] Setting up INTERVAL execution every {minutes} minutes")
        schedule.every(minutes).minutes.do(self.run_trading_pipeline)
        return self
    
    def run_continuous(self):
        """Run continuously on schedule"""
        self.logger.info(f"\n{'='*80}")
        self.logger.info("[SCHEDULER] Live Trading Paper Pipeline - CONTINUOUS MODE")
        self.logger.info(f"Started: {datetime.now()}")
        self.logger.info(f"Logs: {LOG_DIR}")
        self.logger.info(f"{'='*80}\n")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every 60 seconds
        
        except KeyboardInterrupt:
            self.logger.info("\n[SCHEDULER] Stopped by user")
            sys.exit(0)


def main():
    """Main entry point"""
    
    scheduler = LiveTradingScheduler('live_paper_trading_hybrid.py')
    
    # ====== IST TRADING SESSIONS ======
    # Pre-Open Session: 09:00 - 09:15 AM IST
    # Regular Trading: 09:15 AM - 03:30 PM IST  
    # Post-Closing: 03:40 PM - 04:00 PM IST
    
    # Configuration options
    EXECUTION_MODE = 'trading_sessions'  # Options: 'trading_sessions', 'daily', 'hourly', 'interval'
    INTERVAL_MINUTES = 60                # If using interval mode
    
    # Setup schedule based on trading sessions
    if EXECUTION_MODE == 'trading_sessions':
        scheduler.schedule_trading_sessions()
    
    elif EXECUTION_MODE == 'daily':
        scheduler.schedule_daily("15:30")  # End of regular trading
    
    elif EXECUTION_MODE == 'hourly':
        scheduler.schedule_hourly()
    
    elif EXECUTION_MODE == 'interval':
        scheduler.schedule_interval(INTERVAL_MINUTES)
    
    # Run the scheduler
    scheduler.run_continuous()


if __name__ == '__main__':
    main()
