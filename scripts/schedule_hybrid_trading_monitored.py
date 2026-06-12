"""
Hybrid Trading Scheduler with Per-Minute Position Monitoring
Executes 38 trading cycles daily + monitors open positions every minute
Status: Production ready
Timezone: Managed internally (IST / UTC+5:30) - no system timezone change
"""

import os
import sys
import json
import time
import threading
import pytz
from datetime import datetime, time as dtime, timedelta
from typing import List, Dict

# Ensure UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app.trading_engine_hybrid import HybridMLTradingEngine
from app.position_monitor_realtime import RealTimePositionMonitor


class HybridMLTradingSchedulerWithMonitoring:
    """
    Scheduler for hybrid ML trading with real-time position monitoring
    - 38 executions per day (every 10 minutes, 09:15-15:25 IST)
    - Per-minute monitoring of open positions
    - Automatic exit on stop-loss or profit target
    - Intelligent trailing stops
    """
    
    def __init__(self, breeze_client, expanded_tickers_config, 
                 brokerage_fees, capital: float = 100000.0):
        self.breeze = breeze_client
        self.config = expanded_tickers_config
        self.fees = brokerage_fees
        self.capital = capital
        
        # IST timezone (UTC+5:30) - Initialize first
        self.ist_tz = pytz.timezone('Asia/Kolkata')
        
        # Initialize trading engine
        self.engine = HybridMLTradingEngine(
            breeze_client=breeze_client,
            expanded_tickers_config=expanded_tickers_config,
            brokerage_fees=brokerage_fees
        )
        
        # Initialize position monitor
        self.position_monitor = RealTimePositionMonitor(breeze_client, brokerage_fees)
        
        # Execution times (every 10 minutes, 09:15-15:25 IST)
        self.execution_times = self._generate_execution_times()
        
        # Session tracking
        self.session_start = self._get_ist_time()
        self.executions_completed = 0
        self.total_trades = 0
        self.session_pnl = 0.0
        self.market_closed = False
        
        # Threads
        self.monitoring_thread = None
        self.keep_monitoring = False
        
        # Logging
        self.log_dir = "logs/hybrid_scheduler_monitored"
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(
            self.log_dir,
            f"hybrid_monitored_{self._get_ist_time().strftime('%Y%m%d_%H%M%S')}.log"
        )
    
    def _get_ist_time(self) -> datetime:
        """Get current time in IST (UTC+5:30)"""
        return datetime.now(self.ist_tz)
    
    def _generate_execution_times(self) -> List[str]:
        """Generate 38 execution times (every 10 minutes, 09:15-15:25 IST)"""
        times = []
        start_hour, start_min = 9, 15
        
        for i in range(38):
            total_minutes = start_hour * 60 + start_min + (i * 10)
            hour = total_minutes // 60
            minute = total_minutes % 60
            times.append(f"{hour:02d}:{minute:02d}")
        
        return times
    
    def _log(self, message: str, level: str = "INFO"):
        """Log message with IST timestamp"""
        ist_time = self._get_ist_time()
        timestamp = ist_time.strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp} IST] [{level}] {message}"
        
        print(log_message)
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_message + "\n")
        except Exception as e:
            print(f"[ERROR] Failed to write log: {e}")
    
    def _is_market_open(self) -> bool:
        """Check if market is open (09:15-15:30 IST)"""
        ist_time = self._get_ist_time()
        current_time = ist_time.time()
        market_start = dtime(9, 15)
        market_end = dtime(15, 30)
        
        # Check weekday (Monday=0, Sunday=6)
        weekday = ist_time.weekday()
        is_weekday = weekday < 5  # Monday to Friday
        
        return is_weekday and market_start <= current_time < market_end
    
    def should_execute_now(self) -> bool:
        """Check if current IST time matches any execution time"""
        ist_time = self._get_ist_time()
        current_time = ist_time.strftime("%H:%M")
        return current_time in self.execution_times
    
    def start_position_monitoring(self):
        """Start background thread for per-minute position monitoring"""
        self.keep_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        self._log("Position monitoring thread started (1-minute interval)")
    
    def stop_position_monitoring(self):
        """Stop background monitoring thread"""
        self.keep_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self._log("Position monitoring thread stopped")
    
    def _monitoring_loop(self):
        """Background loop that monitors positions every minute"""
        last_check = datetime.now()
        
        while self.keep_monitoring:
            try:
                current_time = datetime.now()
                
                # Check positions every 60 seconds
                if (current_time - last_check).total_seconds() >= 60:
                    # Check and update all open positions
                    closed_positions = self.position_monitor.check_and_update_positions()
                    
                    # Record closed positions
                    for closed_pos in closed_positions:
                        self.total_trades += 1
                        self.session_pnl += closed_pos['net_pnl']
                        self._log(
                            f"Position closed: {closed_pos['ticker']} | "
                            f"Duration: {closed_pos['duration_minutes']}m | "
                            f"P&L: Rs {closed_pos['net_pnl']:.2f} ({closed_pos['pnl_percent']:.2f}%)"
                        )
                    
                    # Get open positions summary
                    open_summary = self.position_monitor.get_open_positions_summary()
                    if open_summary['total_open'] > 0:
                        self._log(
                            f"Open positions: {open_summary['total_open']} | "
                            f"Unrealized P&L: Rs {open_summary['total_open_pnl']:.2f}"
                        )
                    
                    last_check = current_time
                
                # Small sleep to avoid CPU spinning
                time.sleep(1)
            
            except Exception as e:
                self._log(f"ERROR in monitoring loop: {e}", level="ERROR")
                time.sleep(5)
    
    def execute_trading(self) -> Dict:
        """Execute one trading cycle"""
        try:
            self._log("="*80)
            self._log(f"Execution #{self.executions_completed + 1}/{len(self.execution_times)}")
            self._log("="*80)
            
            # Run trading cycle (generates signals and entries)
            result = self.engine.execute_trading_cycle(
                capital=self.capital,
                trading_tickers=self.config.get_all_tickers()
            )
            
            # Track execution
            self.executions_completed += 1
            
            self._log(f"Execution completed: {json.dumps(result, indent=2)}")
            
            return result
        
        except Exception as e:
            self._log(f"ERROR during execution: {e}", level="ERROR")
            return {'status': 'ERROR', 'reason': str(e)}
    
    def run_production(self):
        """Main production loop"""
        ist_start = self._get_ist_time()
        self._log("="*80)
        self._log("HYBRID ML TRADING SCHEDULER - PRODUCTION MODE (IST)")
        self._log(f"Start time: {ist_start.isoformat()}")
        self._log(f"Capital: Rs {self.capital:,.2f}")
        self._log(f"Daily executions: {len(self.execution_times)}")
        self._log("Market hours: 09:15-15:30 IST")
        self._log("Position monitoring: ENABLED (every minute)")
        self._log("Timezone: IST (Asia/Kolkata / UTC+5:30) - Managed internally")
        self._log("="*80)
        
        # Start position monitoring in background
        self.start_position_monitoring()
        
        try:
            while True:
                ist_time = self._get_ist_time()
                
                # Check market hours (09:15-15:30 IST)
                if ist_time.hour >= 15 and ist_time.minute >= 30:
                    self._log("Market closed (15:30 IST). Ending scheduler.")
                    self._log_session_summary()
                    break
                
                # Check if current IST time matches execution time
                if self.should_execute_now():
                    self.execute_trading()
                    
                    # Wait to avoid duplicate execution at same minute
                    time.sleep(65)
                
                # Sleep for 1 second before next check
                time.sleep(1)
        
        except KeyboardInterrupt:
            self._log("Scheduler interrupted by user")
        
        finally:
            # Stop monitoring
            self.stop_position_monitoring()
            
            # Save final reports
            self._log_session_summary()
            self._save_final_reports()
    
    def _log_session_summary(self):
        """Log session summary"""
        ist_end = self._get_ist_time()
        elapsed = (ist_end - self.session_start.replace(tzinfo=self.ist_tz)).total_seconds() / 60
        
        self._log("="*80)
        self._log("SESSION SUMMARY")
        self._log("="*80)
        self._log(f"End time: {ist_end.isoformat()}")
        self._log(f"Duration: {elapsed:.1f} minutes")
        self._log(f"Executions: {self.executions_completed}/{len(self.execution_times)}")
        self._log(f"Total trades: {self.total_trades}")
        self._log(f"Session P&L: Rs {self.session_pnl:,.2f}")
        
        # Position summary
        open_pos = self.position_monitor.get_open_positions_summary()
        closed_pos = self.position_monitor.get_closed_positions()
        
        self._log(f"Open positions: {open_pos['total_open']}")
        if closed_pos:
            wins = sum(1 for p in closed_pos if p['pnl'] > 0)
            losses = sum(1 for p in closed_pos if p['pnl'] <= 0)
            total_pnl = sum(p['pnl'] for p in closed_pos)
            win_rate = (wins / len(closed_pos) * 100) if closed_pos else 0
            
            self._log(f"Closed positions: {len(closed_pos)}")
            self._log(f"  Winning: {wins} | Losing: {losses} | Win rate: {win_rate:.1f}%")
            self._log(f"  Total P&L: Rs {total_pnl:,.2f}")
        
        self._log("="*80)
    
    def _save_final_reports(self):
        """Save all final reports"""
        try:
            # Trading engine report
            self.engine.save_session_report()
            
            # Position monitor report
            self.position_monitor.save_position_report()
            
            self._log("All reports saved successfully")
        
        except Exception as e:
            self._log(f"ERROR saving reports: {e}", level="ERROR")


def main():
    """Main entry point"""
    # Import required dependencies
    from app.services.breeze_api import BreezeAPIService
    from app.brokerage_fees import BrokerageFeeCalculator
    from app.ticker_grouping_config import TickerGroupingConfig
    
    # Initialize components
    breeze = BreezeAPIService()
    fees = BrokerageFeeCalculator()
    tickers = TickerGroupingConfig()
    
    # Create scheduler
    scheduler = HybridMLTradingSchedulerWithMonitoring(
        breeze_client=breeze,
        expanded_tickers_config=tickers,
        brokerage_fees=fees,
        capital=100000.0
    )
    
    # Run production
    scheduler.run_production()


if __name__ == "__main__":
    main()
