"""
SCHEDULE FOR TONIGHT - Paper Trading System Deployment
Updated June 11, 2026

This scheduler deploys the enhanced paper trading system with:
- Fee-aware P&L calculation (ICICI Direct IVALUE plan)
- 17-instrument orchestration
- Real-time Breeze API data
- ML model consensus voting
- Daily P&L tracking and reporting

Execution Times (IST):
├─ 09:00 AM - Pre-market (tomorrow morning)
├─ 09:15 AM - Opening surge #1
├─ 09:25 AM - Opening surge #2
├─ 10:00 AM - Consolidation
├─ 13:00 PM - Mid-day pivot
├─ 15:00 PM - Pre-close surge #1
├─ 15:15 PM - Pre-close surge #2
├─ 15:30 PM - Closing bell
└─ 15:50 PM - Post-closing

Usage:
    python schedule_paper_trading_tonight.py

Or schedule with Windows Task Scheduler:
    python schedule_paper_trading_tonight.py --schedule-task
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

log_file = LOG_DIR / f"paper_trading_schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PaperTradingScheduler:
    """Schedule paper trading pipeline execution with fee-aware P&L"""
    
    def __init__(self, engine_script='expanded_paper_trading_engine.py'):
        self.engine_script = Path(__file__).parent / engine_script
        self.execution_count = 0
        self.logger = logging.getLogger(__name__)
        
        if not self.engine_script.exists():
            self.logger.error(f"Engine script not found: {self.engine_script}")
            sys.exit(1)
        
        self.logger.info("=" * 80)
        self.logger.info("PAPER TRADING SCHEDULER - INITIALIZED")
        self.logger.info("=" * 80)
        self.logger.info(f"Engine: {self.engine_script}")
        self.logger.info(f"Log: {log_file}")
        self.logger.info("")
    
    def run_paper_trading(self):
        """Execute the paper trading engine"""
        try:
            self.execution_count += 1
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.logger.info("")
            self.logger.info("=" * 80)
            self.logger.info(f"[EXECUTION #{self.execution_count}] Paper Trading Pipeline")
            self.logger.info(f"Time: {current_time}")
            self.logger.info(f"Status: STARTING")
            self.logger.info("=" * 80)
            
            # Run the expanded paper trading engine
            result = run(
                [sys.executable, str(self.engine_script)],
                cwd=self.engine_script.parent,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            # Process output
            if result.returncode == 0:
                self.logger.info(f"[SUCCESS] Execution #{self.execution_count} completed")
                
                # Extract and log key metrics
                lines = result.stdout.split('\n')
                for line in lines:
                    if any(keyword in line for keyword in ['[INIT]', '[COMPLETED]', 'Total', 'Gross', 'Net', 'Fees']):
                        self.logger.info(f"   {line.strip()}")
            else:
                self.logger.error(f"[ERROR] Execution #{self.execution_count} failed")
                self.logger.error(f"Return code: {result.returncode}")
                if result.stderr:
                    self.logger.error(f"Error details:\n{result.stderr[:500]}")
            
            self.logger.info(f"Execution #{self.execution_count} completed | Next scheduled execution will begin automatically")
            
        except Exception as e:
            self.logger.error(f"[EXCEPTION] Execution #{self.execution_count}: {str(e)}")
    
    def schedule_trading_sessions(self):
        """
        Schedule optimal trading sessions (IST)
        
        TRADING WINDOWS:
        1. 09:00 AM - PRE-MARKET (Prepare models)
        2. 09:15 AM - OPENING SURGE #1 (Highest volatility)
        3. 09:25 AM - OPENING SURGE #2 (Momentum continuation)
        4. 10:00 AM - CONSOLIDATION (Verify trend)
        5. 13:00 PM - MID-DAY PIVOT (Reversal point)
        6. 15:00 PM - PRE-CLOSE SURGE #1 (Second highest volatility)
        7. 15:15 PM - PRE-CLOSE SURGE #2 (Final signals)
        8. 15:30 PM - CLOSING BELL (Last orders)
        9. 15:50 PM - POST-CLOSING (Auction orders)
        """
        self.logger.info("[SCHEDULER] Setting up OPTIMAL TRADING SESSIONS (IST)")
        self.logger.info("=" * 80)
        self.logger.info("OPENING SURGE TRADES (9:15-9:30 AM)")
        self.logger.info("  09:15 AM - FIRST SIGNAL at market open (highest volatility)")
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
        self.logger.info("=" * 80)
        
        # ===== TOMORROW MORNING =====
        # Pre-market session
        schedule.every().day.at("09:00").do(self.run_paper_trading)
        
        # ===== OPENING SURGE: 9:15-9:30 AM =====
        # Capture the opening momentum - HIGHEST VOLATILITY
        schedule.every().day.at("09:15").do(self.run_paper_trading)
        schedule.every().day.at("09:25").do(self.run_paper_trading)
        
        # ===== INTRADAY TRADES =====
        schedule.every().day.at("10:00").do(self.run_paper_trading)
        schedule.every().day.at("13:00").do(self.run_paper_trading)
        
        # ===== CLOSING SURGE: 3:00-3:45 PM =====
        # Capture the pre-close volatility - SECOND HIGHEST VOLATILITY
        schedule.every().day.at("15:00").do(self.run_paper_trading)
        schedule.every().day.at("15:15").do(self.run_paper_trading)
        schedule.every().day.at("15:30").do(self.run_paper_trading)
        
        # ===== POST-CLOSING SESSION: 3:40-4:00 PM =====
        schedule.every().day.at("15:50").do(self.run_paper_trading)
        
        self.logger.info("")
        self.logger.info(f"[SCHEDULER] Setup complete - 9 executions per trading day")
        self.logger.info(f"[INFO] Optimal volatility windows configured")
        self.logger.info("")
        self.logger.info("Schedule Summary:")
        self.logger.info("   09:00 AM - Pre-market (prepare models)")
        self.logger.info("   09:15 AM - Opening surge #1")
        self.logger.info("   09:25 AM - Opening surge #2")
        self.logger.info("   10:00 AM - Consolidation")
        self.logger.info("   13:00 PM - Mid-day pivot")
        self.logger.info("   15:00 PM - Pre-close surge #1")
        self.logger.info("   15:15 PM - Pre-close surge #2")
        self.logger.info("   15:30 PM - Closing bell")
        self.logger.info("   15:50 PM - Post-closing")
        self.logger.info("")
        
        return self
    
    def run_scheduler(self):
        """Run the scheduler loop"""
        self.logger.info("[SCHEDULER] Starting main loop...")
        self.logger.info("[INFO] Press Ctrl+C to stop")
        self.logger.info("")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)  # Check every second
        except KeyboardInterrupt:
            self.logger.info("\n[SCHEDULER] Shutting down...")
            self.logger.info("[INFO] Scheduler stopped by user")


def main():
    """Main entry point"""
    
    if len(sys.argv) > 1 and sys.argv[1] == '--schedule-task':
        # Setup Windows Task Scheduler
        logger.info("[SETUP] Windows Task Scheduler mode")
        logger.info("[INFO] To create scheduled task, run:")
        logger.info("  powershell -Command \"Set-ExecutionPolicy RemoteSigned -Scope CurrentUser\"")
        logger.info("  python setup_task_scheduler.py")
        return
    
    # Start scheduler
    scheduler = PaperTradingScheduler(engine_script='expanded_paper_trading_engine.py')
    scheduler.schedule_trading_sessions()
    scheduler.run_scheduler()


if __name__ == "__main__":
    main()
