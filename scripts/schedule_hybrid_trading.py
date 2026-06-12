"""
Hybrid ML Trading Scheduler
Schedules 38 daily trading executions with hybrid ML models
Status: Production ready
"""

import os
import json
import time
from datetime import datetime, time as dtime
from typing import List, Dict
from app.trading_engine_hybrid import HybridMLTradingEngine


class HybridMLTradingScheduler:
    """
    Scheduler for hybrid ML trading system
    - 38 executions per day (every 10 minutes, 09:15-15:25 IST)
    - Tracks model versions and performance
    - Manages retraining cycles
    """
    
    def __init__(self, breeze_client, expanded_tickers_config, 
                 brokerage_fees, capital: float = 100000.0):
        self.breeze = breeze_client
        self.config = expanded_tickers_config
        self.fees = brokerage_fees
        self.capital = capital
        
        # Initialize trading engine
        self.engine = HybridMLTradingEngine(
            breeze_client=breeze_client,
            expanded_tickers_config=expanded_tickers_config,
            brokerage_fees=brokerage_fees
        )
        
        # Execution times
        self.execution_times = self._generate_execution_times()
        
        # Session tracking
        self.session_start = datetime.now()
        self.executions_completed = 0
        self.total_trades = 0
        self.session_pnl = 0.0
        
        # Logging
        self.log_dir = "logs/hybrid_scheduler"
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(
            self.log_dir,
            f"hybrid_scheduler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
    
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
        """Log message"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] {message}"
        
        print(log_message)
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_message + "\n")
        except Exception as e:
            print(f"[ERROR] Failed to write log: {e}")
    
    def should_execute_now(self) -> bool:
        """Check if current time matches any execution time"""
        current_time = datetime.now().strftime("%H:%M")
        return current_time in self.execution_times
    
    def execute_trading(self) -> Dict:
        """Execute one trading cycle"""
        try:
            self._log("="*80)
            self._log(f"Execution #{self.executions_completed + 1}/{len(self.execution_times)}")
            self._log("="*80)
            
            # Run trading cycle
            result = self.engine.execute_trading_cycle(
                capital=self.capital,
                trading_tickers=self.config.get_all_tickers()
            )
            
            # Track execution
            self.executions_completed += 1
            
            if result.get('status') == 'SUCCESS':
                trades_count = result.get('trades_executed', 0)
                cycle_pnl = result.get('cycle_pnl', 0)
                daily_pnl = result.get('daily_pnl', 0)
                
                self.total_trades += trades_count
                self.session_pnl += cycle_pnl
                
                self._log(f"✓ Execution completed")
                self._log(f"  Trades executed: {trades_count}")
                self._log(f"  Cycle P&L: ₹{cycle_pnl:,.2f}")
                self._log(f"  Daily P&L: ₹{daily_pnl:,.2f}")
                
                # Log ML model status
                ml_status = result.get('ml_status', {})
                self._log(f"  ML Models:")
                self._log(f"    Global: v{ml_status.get('global', {}).get('version', 0)} " +
                         f"(samples: {ml_status.get('global', {}).get('training_samples', 0)})")
                
                for group_name, group_info in ml_status.get('groups', {}).items():
                    self._log(f"    {group_name}: v{group_info.get('version', 0)} " +
                             f"(samples: {group_info.get('training_samples', 0)})")
                
                for ticker, ticker_info in ml_status.get('tickers', {}).items():
                    if ticker_info.get('ready'):
                        self._log(f"    {ticker}: v{ticker_info.get('version', 0)} " +
                                 f"(samples: {ticker_info.get('training_samples', 0)})")
                
                # Log individual trades
                for trade in result.get('trades', []):
                    self._log(f"  Trade: {trade['ticker']} {trade['direction']} " +
                             f"@ ₹{trade['entry_price']:.2f} " +
                             f"P&L: ₹{trade['pnl']:,.2f} ({trade['pnl_percent']:.2f}%) " +
                             f"Confidence: {trade['confidence']:.2%}")
            
            elif result.get('status') == 'HALTED':
                self._log(f"⚠ Trading halted: {result.get('reason')}")
            
            else:
                self._log(f"✗ Execution failed: {result.get('error', 'Unknown error')}", "ERROR")
            
            return result
        
        except Exception as e:
            self._log(f"Exception during execution: {e}", "ERROR")
            return {'status': 'ERROR', 'error': str(e)}
    
    def run_scheduler(self, test_mode: bool = False):
        """
        Main scheduler loop
        
        Args:
            test_mode: If True, execute once regardless of time
        """
        self._log(f"Hybrid ML Trading Scheduler Started")
        self._log(f"Mode: {'TEST' if test_mode else 'PRODUCTION'}")
        self._log(f"Capital: ₹{self.capital:,}")
        self._log(f"Daily execution times: {len(self.execution_times)}")
        self._log(f"First execution: {self.execution_times[0]} IST")
        self._log(f"Last execution: {self.execution_times[-1]} IST")
        self._log(f"Total tickers: {len(self.config.get_all_tickers())}")
        
        try:
            if test_mode:
                self._log("TEST MODE: Executing once")
                result = self.execute_trading()
                self._log_session_summary()
                return result
            
            # Production mode: run until end of day
            while True:
                current_time = datetime.now()
                current_time_str = current_time.strftime("%H:%M")
                
                # Check if market is closed (after 15:30 IST)
                if current_time.hour >= 15 and current_time.minute >= 30:
                    self._log("Market closed, ending scheduler")
                    self._log_session_summary()
                    break
                
                # Check if it's execution time
                if current_time_str in self.execution_times:
                    self.execute_trading()
                    
                    # Wait to avoid double execution
                    time.sleep(65)
                
                # Sleep briefly before checking again
                time.sleep(10)
        
        except KeyboardInterrupt:
            self._log("Scheduler interrupted by user", "WARN")
            self._log_session_summary()
        
        except Exception as e:
            self._log(f"Scheduler error: {e}", "ERROR")
            self._log_session_summary()
            raise
    
    def _log_session_summary(self):
        """Log end-of-session summary"""
        self._log("="*80)
        self._log("SESSION SUMMARY")
        self._log("="*80)
        
        session_duration = (datetime.now() - self.session_start).total_seconds()
        
        summary = self.engine.get_daily_summary()
        
        self._log(f"Duration: {session_duration:.0f} seconds ({session_duration/60:.1f} minutes)")
        self._log(f"Executions completed: {self.executions_completed}/{len(self.execution_times)}")
        self._log(f"Total trades: {summary.get('total_trades', 0)}")
        self._log(f"  Winning: {summary.get('winning_trades', 0)}")
        self._log(f"  Losing: {summary.get('losing_trades', 0)}")
        self._log(f"  Win rate: {summary.get('win_rate', 0):.1f}%")
        self._log(f"Session P&L: ₹{summary.get('total_pnl', 0):,.2f}")
        self._log(f"Avg P&L/trade: ₹{summary.get('average_pnl_per_trade', 0):,.2f}")
        
        # ML Model status
        ml_status = summary.get('ml_model_status', {})
        self._log("")
        self._log("ML Model Status (End of Session):")
        self._log(f"  Global Model: v{ml_status.get('global', {}).get('version', 0)} " +
                 f"(accuracy: {ml_status.get('global', {}).get('accuracy', 0):.2%})")
        
        for group_name, group_info in ml_status.get('groups', {}).items():
            self._log(f"  {group_name}: v{group_info.get('version', 0)} " +
                     f"(accuracy: {group_info.get('accuracy', 0):.2%})")
        
        for ticker, ticker_info in ml_status.get('tickers', {}).items():
            if ticker_info.get('ready'):
                self._log(f"  {ticker}: v{ticker_info.get('version', 0)} " +
                         f"(accuracy: {ticker_info.get('accuracy', 0):.2%})")
        
        # Save reports
        self._log("")
        self._log("Saving reports...")
        self.engine.save_session_report()
        
        self._log("="*80)
        self._log("Scheduler complete")
    
    def get_execution_schedule(self) -> Dict:
        """Get execution schedule info"""
        return {
            'total_executions': len(self.execution_times),
            'execution_times': self.execution_times,
            'start_time': self.execution_times[0] + " IST",
            'end_time': self.execution_times[-1] + " IST",
            'interval_minutes': 10,
            'market_hours': "09:15 - 15:30 IST",
            'total_tickers': len(self.config.get_all_tickers()),
            'capital': self.capital,
            'status': 'READY'
        }


def main():
    """
    Main entry point for hybrid ML trading scheduler
    """
    print("\n")
    print("="*80)
    print("HYBRID ML TRADING SCHEDULER - INITIALIZATION")
    print("="*80)
    
    try:
        # Import dependencies
        from app.services.breeze_api import BreezeAPIService
        from app.ticker_grouping_config import TickerGroupingConfig
        from app.brokerage_fees import BrokerageFeeCalculator
        
        print("[INFO] Initializing Breeze API client...")
        breeze = BreezeAPIService()
        
        print("[INFO] Loading ticker configuration...")
        config = TickerGroupingConfig()
        
        print("[INFO] Loading brokerage fees...")
        fees = BrokerageFeeCalculator()
        
        print("[INFO] Initializing hybrid ML trading scheduler...")
        scheduler = HybridMLTradingScheduler(
            breeze_client=breeze,
            expanded_tickers_config=config,
            brokerage_fees=fees,
            capital=100000.0
        )
        
        print("\n" + "="*80)
        print("EXECUTION SCHEDULE")
        print("="*80)
        schedule_info = scheduler.get_execution_schedule()
        print(f"Total daily executions: {schedule_info['total_executions']}")
        print(f"Start time: {schedule_info['start_time']}")
        print(f"End time: {schedule_info['end_time']}")
        print(f"Interval: Every {schedule_info['interval_minutes']} minutes")
        print(f"Tickers: {schedule_info['total_tickers']}")
        print(f"Capital: ₹{schedule_info['capital']:,}")
        print("="*80 + "\n")
        
        # Run scheduler
        print("[INFO] Starting production scheduler...")
        print("[INFO] Press Ctrl+C to stop\n")
        
        scheduler.run_scheduler(test_mode=False)
    
    except KeyboardInterrupt:
        print("\n[INFO] Scheduler stopped by user")
    
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
