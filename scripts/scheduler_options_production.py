"""
Options Trading Scheduler - Production Integration
Integrates complete 5-phase options trading system with main scheduler
Status: Production ready (June 12, 2026)
Timezone: IST (Asia/Kolkata / UTC+5:30) - Managed internally
"""

import os
import sys
import json
import time
import threading
import pytz
from datetime import datetime, time as dtime, timedelta
from typing import List, Dict, Tuple

# Ensure UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Import main trading components
from app.trading_engine_hybrid import HybridMLTradingEngine
from app.position_monitor_realtime import RealTimePositionMonitor

# Import OPTIONS TRADING components (5 Phases)
from app.options_chain_manager import OptionsChainManager
from app.options_strategy_selector import OptionsStrategySelector
from app.options_executor_and_risk import (
    OptionsOrderExecutor, OptionsExitManager, OptionsRiskManager
)
from app.options_orchestrator import OptionsTradeOrchestrator, TradingSignal
from app.options_testing import OptionsSystemTester


class OptionsProductionScheduler:
    """
    Production scheduler combining:
    - Equity ML trading (existing)
    - OPTIONS trading pipeline (new - 5 phases)
    
    Architecture:
    ┌─────────────────────────────────────────┐
    │  HYBRID ML TRADING ENGINE (Equity)      │
    │  ├─ Signal Generation                   │
    │  ├─ Feature Engineering                 │
    │  └─ Per-minute Position Monitoring      │
    └─────────────────────────────────────────┘
                      ↓
    ┌─────────────────────────────────────────┐
    │  OPTIONS TRADING ORCHESTRATOR (New)     │
    │  ├─ Phase 1: Options Chain Manager      │
    │  ├─ Phase 2: Strategy Selector          │
    │  ├─ Phase 3: Order Execution            │
    │  ├─ Phase 4: Exit Management            │
    │  └─ Phase 5: Risk Management            │
    └─────────────────────────────────────────┘
                      ↓
    ┌─────────────────────────────────────────┐
    │  POSITION MONITORING (Equity + Options) │
    │  ├─ Real-time P&L tracking              │
    │  ├─ Automatic exit triggers             │
    │  └─ Session summaries                   │
    └─────────────────────────────────────────┘
    """
    
    def __init__(self, breeze_client, expanded_tickers_config, 
                 brokerage_fees, capital: float = 100000.0, 
                 options_enabled: bool = True):
        """
        Initialize production scheduler with OPTIONS support
        
        Args:
            breeze_client: Breeze API client
            expanded_tickers_config: Ticker configuration
            brokerage_fees: Fee calculator
            capital: Trading capital (₹100,000)
            options_enabled: Enable OPTIONS trading (default: True)
        """
        self.breeze = breeze_client
        self.config = expanded_tickers_config
        self.fees = brokerage_fees
        self.capital = capital
        self.options_enabled = options_enabled
        
        # IST timezone (UTC+5:30)
        self.ist_tz = pytz.timezone('Asia/Kolkata')
        
        # ========== EQUITY TRADING COMPONENTS ==========
        self.engine = HybridMLTradingEngine(
            breeze_client=breeze_client,
            expanded_tickers_config=expanded_tickers_config,
            brokerage_fees=brokerage_fees
        )
        
        self.position_monitor = RealTimePositionMonitor(breeze_client, brokerage_fees)
        
        # ========== OPTIONS TRADING COMPONENTS (NEW) ==========
        if self.options_enabled:
            try:
                self._init_options_components()
                self._log("OPTIONS TRADING: Initialized (5 Phases ready)", level="SUCCESS")
            except Exception as e:
                self._log(f"WARNING: OPTIONS initialization failed: {e}", level="WARNING")
                self.options_enabled = False
                self.options_orchestrator = None
        else:
            self.options_orchestrator = None
        
        # Execution times (every 10 minutes, 09:15-15:25 IST)
        self.execution_times = self._generate_execution_times()
        
        # Session tracking
        self.session_start = self._get_ist_time()
        self.executions_completed = 0
        self.total_trades = 0  # Equity trades
        self.session_pnl = 0.0
        self.options_trades = 0
        self.options_pnl = 0.0
        self.market_closed = False
        
        # Threads
        self.monitoring_thread = None
        self.keep_monitoring = False
        
        # Logging
        self.log_dir = "logs/options_production_scheduler"
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(
            self.log_dir,
            f"options_scheduler_{self._get_ist_time().strftime('%Y%m%d_%H%M%S')}.log"
        )
    
    def _init_options_components(self):
        """Initialize all OPTIONS trading components (Phase 1-5)"""
        # Phase 1: Options Chain Manager
        self.options_chain = OptionsChainManager(self.breeze)
        
        # Phase 2: Options Strategy Selector
        self.strategy_selector = OptionsStrategySelector(self.options_chain)
        
        # Phase 3: Order Executor
        self.options_executor = OptionsOrderExecutor(self.breeze, self.position_monitor)
        
        # Phase 4: Exit Manager
        self.options_exit = OptionsExitManager(self.position_monitor, self.options_chain)
        
        # Phase 5: Risk Manager
        self.options_risk = OptionsRiskManager(self.options_chain, max_capital=self.capital)
        
        # Master Orchestrator: Integrates all 5 phases
        self.options_orchestrator = OptionsTradeOrchestrator(
            breeze_client=self.breeze,
            chain_manager=self.options_chain,
            strategy_selector=self.strategy_selector,
            executor=self.options_executor,
            exit_manager=self.options_exit,
            risk_manager=self.options_risk,
            portfolio_manager=self.position_monitor
        )
        
        self._log("[OPTIONS] Phase 1: Chain Manager ✓", level="DEBUG")
        self._log("[OPTIONS] Phase 2: Strategy Selector ✓", level="DEBUG")
        self._log("[OPTIONS] Phase 3: Order Executor ✓", level="DEBUG")
        self._log("[OPTIONS] Phase 4: Exit Manager ✓", level="DEBUG")
        self._log("[OPTIONS] Phase 5: Risk Manager ✓", level="DEBUG")
        self._log("[OPTIONS] Orchestrator: Integration Complete ✓", level="DEBUG")
    
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
        
        # Color coding for terminal
        colors = {
            "INFO": "\033[94m",      # Blue
            "SUCCESS": "\033[92m",   # Green
            "WARNING": "\033[93m",   # Yellow
            "ERROR": "\033[91m",     # Red
            "DEBUG": "\033[96m"      # Cyan
        }
        reset = "\033[0m"
        
        color = colors.get(level, reset)
        log_message = f"{color}[{timestamp} IST] [{level}] {message}{reset}"
        
        print(log_message)
        
        try:
            with open(self.log_file, 'a') as f:
                # Write without ANSI codes to file
                plain_message = f"[{timestamp} IST] [{level}] {message}"
                f.write(plain_message + '\n')
        except Exception:
            pass
    
    def _calculate_trade_fees(self, entry_premium: float, exit_premium: float, 
                             quantity: float = 1, is_sell: bool = False) -> float:
        """
        Calculate total fees for a trade (entry + exit)
        ICICI Direct IVALUE plan: ₹20/trade + exchange charges + GST
        
        Args:
            entry_premium: Entry price per contract
            exit_premium: Exit price per contract
            quantity: Number of contracts traded
            is_sell: Whether this includes a sell transaction (for STT)
        
        Returns:
            Total fees in rupees
        """
        try:
            # Use the brokerage fee calculator if available
            if self.fees:
                fee_dict = self.fees.calculate_options_fee(
                    entry_premium=entry_premium,
                    exit_premium=exit_premium,
                    quantity=quantity,
                    is_sell=is_sell
                )
                return fee_dict.get('total_fee', 0)
        except Exception as e:
            self._log(f"Warning: Fee calculation failed: {e}", level="WARNING")
        
        # Fallback calculation: Conservative estimate
        # Per trade: ₹20 brokerage + exchange charges + GST
        brokerage_per_trade = 20 * 2  # Entry + Exit
        exchange_charges = (entry_premium + exit_premium) * quantity * 0.0003553 / 100  # 0.03553% NSE
        gst = (brokerage_per_trade + exchange_charges) * 0.18  # 18% GST
        
        total_fees = brokerage_per_trade + exchange_charges + gst
        return max(total_fees, 40)  # Minimum ₹40 per round-trip trade
    
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
        self._log("Position monitoring thread started (1-minute interval)", level="INFO")
    
    def stop_position_monitoring(self):
        """Stop background monitoring thread"""
        self.keep_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self._log("Position monitoring thread stopped", level="INFO")
    
    def _monitoring_loop(self):
        """Background loop that monitors positions every minute"""
        last_check = datetime.now()
        last_options_check = datetime.now()
        
        while self.keep_monitoring:
            try:
                current_time = datetime.now()
                
                # ========== EQUITY POSITIONS (Every 60 seconds) ==========
                if (current_time - last_check).total_seconds() >= 60:
                    # Check and update equity positions
                    closed_positions = self.position_monitor.check_and_update_positions()
                    
                    # Record closed equity positions
                    for closed_pos in closed_positions:
                        self.total_trades += 1
                        
                        # Calculate fees for this trade (ICICI Direct brokerage)
                        trade_fees = self._calculate_trade_fees(
                            entry_premium=closed_pos.get('entry_premium', 0),
                            exit_premium=closed_pos.get('exit_premium', 0),
                            quantity=closed_pos.get('quantity', 1),
                            is_sell=True
                        )
                        
                        # Calculate net P&L after fees
                        gross_pnl = closed_pos.get('pnl', closed_pos.get('net_pnl', 0))
                        net_pnl_after_fees = gross_pnl - trade_fees
                        
                        self.session_pnl += net_pnl_after_fees
                        
                        self._log(
                            f"[EQUITY] Position closed: {closed_pos.get('ticker', 'N/A')} | "
                            f"Duration: {closed_pos.get('duration_minutes', 0)}m | "
                            f"Gross P&L: Rs {gross_pnl:.2f} | "
                            f"Fees: Rs {trade_fees:.2f} | "
                            f"Net P&L: Rs {net_pnl_after_fees:.2f}",
                            level="INFO"
                        )
                    
                    # Get equity positions summary
                    open_summary = self.position_monitor.get_open_positions_summary()
                    if open_summary['total_open'] > 0:
                        self._log(
                            f"[EQUITY] Open positions: {open_summary['total_open']} | "
                            f"Unrealized P&L: Rs {open_summary['total_open_pnl']:.2f}",
                            level="DEBUG"
                        )
                    
                    last_check = current_time
                
                # ========== OPTIONS POSITIONS (Every 60 seconds) ==========
                if self.options_enabled and (current_time - last_options_check).total_seconds() >= 60:
                    try:
                        options_summary = self.options_orchestrator.monitor_positions()
                        
                        if options_summary and options_summary.get('positions_closed', 0) > 0:
                            self.options_trades += options_summary.get('positions_closed', 0)
                            self.options_pnl += options_summary.get('daily_pnl', 0)
                            
                            self._log(
                                f"[OPTIONS] Positions closed: {options_summary['positions_closed']} | "
                                f"Open: {options_summary['open_positions']} | "
                                f"P&L: Rs {options_summary['daily_pnl']:.2f}",
                                level="INFO"
                            )
                        elif options_summary and options_summary.get('open_positions', 0) > 0:
                            self._log(
                                f"[OPTIONS] Open positions: {options_summary['open_positions']} | "
                                f"P&L: Rs {options_summary['daily_pnl']:.2f}",
                                level="DEBUG"
                            )
                    
                    except Exception as e:
                        self._log(f"[OPTIONS] Monitoring error: {e}", level="WARNING")
                    
                    last_options_check = current_time
                
                # Small sleep to avoid CPU spinning
                time.sleep(1)
            
            except Exception as e:
                self._log(f"ERROR in monitoring loop: {e}", level="ERROR")
                time.sleep(5)
    
    def execute_trading(self) -> Dict:
        """Execute one trading cycle (Equity + OPTIONS)"""
        try:
            self._log("="*80, level="INFO")
            self._log(f"Execution #{self.executions_completed + 1}/{len(self.execution_times)}", level="INFO")
            self._log("="*80, level="INFO")
            
            # ========== EQUITY TRADING CYCLE ==========
            result_equity = self.engine.execute_trading_cycle(
                capital=self.capital,
                trading_tickers=self.config.get_all_tickers()
            )
            
            self._log(f"[EQUITY] Execution result: {json.dumps(result_equity, indent=2)}", level="DEBUG")
            
            # ========== OPTIONS TRADING CYCLE (NEW) ==========
            result_options = {'status': 'SKIPPED', 'reason': 'OPTIONS trading disabled'}
            
            if self.options_enabled and result_equity.get('status') == 'SUCCESS':
                try:
                    # Extract equity signal and convert to OPTIONS signal
                    equity_signal = result_equity.get('signal', {})
                    
                    if equity_signal and equity_signal.get('signal_type'):
                        # Create OPTIONS trading signal from equity signal
                        options_signal = TradingSignal(
                            underlying=equity_signal.get('ticker', 'NIFTY'),
                            direction=equity_signal.get('direction', 'NEUTRAL'),
                            confidence=equity_signal.get('confidence', 0.5),
                            expected_move_pct=equity_signal.get('expected_move_pct', 1.0),
                            timestamp=self._get_ist_time()
                        )
                        
                        # Process signal through OPTIONS orchestrator
                        success, message = self.options_orchestrator.process_signal(
                            options_signal, 
                            dry_run=True  # Start with dry run
                        )
                        
                        result_options = {
                            'status': 'SUCCESS' if success else 'FAILED',
                            'message': message,
                            'dry_run': True
                        }
                        
                        self._log(
                            f"[OPTIONS] Signal processed: {options_signal.underlying} | "
                            f"Direction: {options_signal.direction} | "
                            f"Result: {result_options['status']}",
                            level="INFO"
                        )
                
                except Exception as e:
                    result_options = {'status': 'ERROR', 'reason': str(e)}
                    self._log(f"[OPTIONS] Execution error: {e}", level="ERROR")
            
            # Track execution
            self.executions_completed += 1
            
            # Combined result
            result = {
                'execution_id': self.executions_completed,
                'equity': result_equity,
                'options': result_options,
                'timestamp': self._get_ist_time().isoformat()
            }
            
            return result
        
        except Exception as e:
            self._log(f"ERROR during execution: {e}", level="ERROR")
            return {'status': 'ERROR', 'reason': str(e)}
    
    def run_production(self):
        """Main production loop (Equity + OPTIONS)"""
        ist_start = self._get_ist_time()
        self._log("="*80, level="SUCCESS")
        self._log("OPTIONS TRADING SCHEDULER - PRODUCTION MODE", level="SUCCESS")
        self._log("="*80, level="SUCCESS")
        self._log(f"Start time: {ist_start.isoformat()}", level="INFO")
        self._log(f"Capital: Rs {self.capital:,.2f}", level="INFO")
        self._log(f"Daily executions: {len(self.execution_times)} (every 10 min)", level="INFO")
        self._log("Market hours: 09:15-15:30 IST", level="INFO")
        self._log("Position monitoring: ENABLED (every minute)", level="INFO")
        self._log("Timezone: IST (Asia/Kolkata / UTC+5:30) - Managed internally", level="INFO")
        self._log("="*80, level="SUCCESS")
        
        if self.options_enabled:
            self._log("OPTIONS TRADING: ENABLED", level="SUCCESS")
            self._log("  ✓ Phase 1: Options Chain Manager", level="DEBUG")
            self._log("  ✓ Phase 2: Strategy Selector", level="DEBUG")
            self._log("  ✓ Phase 3: Order Executor", level="DEBUG")
            self._log("  ✓ Phase 4: Exit Manager", level="DEBUG")
            self._log("  ✓ Phase 5: Risk Manager", level="DEBUG")
        
        # Start position monitoring in background
        self.start_position_monitoring()
        
        try:
            while True:
                ist_time = self._get_ist_time()
                
                # Check market hours (09:15-15:30 IST)
                if ist_time.hour >= 15 and ist_time.minute >= 30:
                    self._log("Market closed (15:30 IST). Ending scheduler.", level="INFO")
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
            self._log("Scheduler interrupted by user", level="WARNING")
        
        finally:
            # Stop monitoring
            self.stop_position_monitoring()
            
            # Save final reports
            self._log_session_summary()
            self._save_final_reports()
    
    def _log_session_summary(self):
        """Log combined session summary (Equity + OPTIONS)"""
        ist_end = self._get_ist_time()
        elapsed = (ist_end - self.session_start.replace(tzinfo=self.ist_tz)).total_seconds() / 60
        
        self._log("="*80, level="SUCCESS")
        self._log("SESSION SUMMARY", level="SUCCESS")
        self._log("="*80, level="SUCCESS")
        self._log(f"End time: {ist_end.isoformat()}", level="INFO")
        self._log(f"Duration: {elapsed:.1f} minutes", level="INFO")
        self._log(f"Executions: {self.executions_completed}/{len(self.execution_times)}", level="INFO")
        
        # Equity summary
        self._log("-" * 80, level="DEBUG")
        self._log("EQUITY TRADING SUMMARY", level="DEBUG")
        self._log(f"Total trades: {self.total_trades}", level="DEBUG")
        self._log(f"Session P&L: Rs {self.session_pnl:,.2f}", level="DEBUG")
        
        # Position summary
        open_pos = self.position_monitor.get_open_positions_summary()
        closed_pos = self.position_monitor.get_closed_positions()
        
        self._log(f"Open positions: {open_pos['total_open']}", level="DEBUG")
        if closed_pos:
            wins = sum(1 for p in closed_pos if p['pnl'] > 0)
            losses = sum(1 for p in closed_pos if p['pnl'] <= 0)
            total_pnl = sum(p['pnl'] for p in closed_pos)
            win_rate = (wins / len(closed_pos) * 100) if closed_pos else 0
            
            self._log(f"Closed positions: {len(closed_pos)}", level="DEBUG")
            self._log(f"  Winning: {wins} | Losing: {losses} | Win rate: {win_rate:.1f}%", level="DEBUG")
            self._log(f"  Total P&L: Rs {total_pnl:,.2f}", level="DEBUG")
        
        # Options summary
        if self.options_enabled:
            self._log("-" * 80, level="DEBUG")
            self._log("OPTIONS TRADING SUMMARY", level="DEBUG")
            self._log(f"Total options trades: {self.options_trades}", level="DEBUG")
            self._log(f"Options P&L: Rs {self.options_pnl:,.2f}", level="DEBUG")
            
            try:
                options_summary = self.options_orchestrator.generate_session_summary()
                if options_summary:
                    self._log(f"Win rate: {options_summary.get('win_rate_percent', 0):.1f}%", level="DEBUG")
                    self._log(f"Greeks exposure - Delta: {options_summary.get('portfolio_delta', 0):.2f}, Theta: {options_summary.get('portfolio_theta', 0):.2f}", level="DEBUG")
            except Exception as e:
                self._log(f"Could not generate options summary: {e}", level="WARNING")
        
        # Grand total
        self._log("-" * 80, level="SUCCESS")
        grand_total = self.session_pnl + self.options_pnl
        self._log(f"TOTAL P&L (Equity + Options): Rs {grand_total:,.2f}", level="SUCCESS")
        self._log("="*80, level="SUCCESS")
    
    def _save_final_reports(self):
        """Save all final reports"""
        try:
            # Trading engine report
            self.engine.save_session_report()
            
            # Position monitor report
            self.position_monitor.save_position_report()
            
            self._log("All reports saved successfully", level="SUCCESS")
        
        except Exception as e:
            self._log(f"ERROR saving reports: {e}", level="ERROR")


def main():
    """Main entry point"""
    from app.services.breeze_api import BreezeAPIService
    from app.brokerage_fees import BrokerageFeeCalculator
    from app.ticker_grouping_config import TickerGroupingConfig
    
    # Initialize components
    breeze = BreezeAPIService()
    fees = BrokerageFeeCalculator()
    tickers = TickerGroupingConfig()
    
    # Create scheduler with OPTIONS enabled
    scheduler = OptionsProductionScheduler(
        breeze_client=breeze,
        expanded_tickers_config=tickers,
        brokerage_fees=fees,
        capital=100000.0,
        options_enabled=True  # Enable OPTIONS trading
    )
    
    # Run production
    scheduler.run_production()


if __name__ == "__main__":
    main()
