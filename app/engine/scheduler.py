"""
Automated Scheduler for Trading Engine
======================================
Automatically triggers the TradingEngine at appropriate intervals and events.

Features:
- Time-based scheduling (e.g., every 1-5 minutes)
- Market hours awareness (start at market open, stop at close)
- Overlap prevention (ensures one cycle at a time)
- Graceful shutdown handling
- Emergency pause/resume controls
- Integration with risk circuit breakers

Usage:
    scheduler = TradingScheduler(trading_engine)
    scheduler.start()  # Starts background thread
    
    # Pause/resume trading
    scheduler.pause()
    scheduler.resume()
    
    # Stop scheduler
    scheduler.stop()

Configuration via environment variables:
    TRADING_START_TIME='09:15'          # Market open (IST)
    TRADING_END_TIME='15:30'            # Market close (IST)
    CYCLE_INTERVAL_MINUTES=5            # Run every 5 minutes
    ENABLE_MARKET_HOURS_FILTER=true     # Only trade during market hours
"""

import logging
import threading
import time
from datetime import datetime, time as time_obj
from typing import Optional, Callable, Dict
from enum import Enum
import pytz

logger = logging.getLogger(__name__)


class SchedulerStatus(Enum):
    """Status of the scheduler"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


class TradingScheduler:
    """
    Scheduler for the TradingEngine.
    
    Ensures the trading pipeline runs regularly and reliably without manual intervention.
    Responsibilities:
    - Start/stop at predefined times (market hours aware)
    - Run pipeline at configured frequency
    - Ensure no overlapping executions
    - Handle graceful shutdown
    - Integrate with risk circuit breakers
    """
    
    def __init__(self,
                 trading_engine,
                 cycle_interval_minutes: int = 5,
                 start_time: str = '09:15',      # IST market open
                 end_time: str = '15:30',         # IST market close
                 timezone: str = 'Asia/Kolkata',  # India Standard Time
                 enable_market_hours: bool = True,
                 on_cycle_start: Optional[Callable] = None,
                 on_cycle_end: Optional[Callable] = None):
        """
        Initialize the trading scheduler
        
        Args:
            trading_engine: TradingEngine instance
            cycle_interval_minutes: How often to run cycles (in minutes)
            start_time: Market start time (HH:MM format)
            end_time: Market end time (HH:MM format)
            timezone: Timezone for market hours
            enable_market_hours: Only schedule during market hours if True
            on_cycle_start: Optional callback when cycle starts
            on_cycle_end: Optional callback when cycle ends
        """
        self.trading_engine = trading_engine
        self.cycle_interval_seconds = cycle_interval_minutes * 60
        self.timezone = pytz.timezone(timezone)
        self.enable_market_hours = enable_market_hours
        
        # Parse market hours
        start_parts = start_time.split(':')
        end_parts = end_time.split(':')
        self.market_start = time_obj(int(start_parts[0]), int(start_parts[1]))
        self.market_end = time_obj(int(end_parts[0]), int(end_parts[1]))
        
        # Callbacks
        self.on_cycle_start = on_cycle_start
        self.on_cycle_end = on_cycle_end
        
        # Thread management
        self.scheduler_thread: Optional[threading.Thread] = None
        self.status = SchedulerStatus.STOPPED
        self.should_stop = False
        self.is_cycle_running = False
        self.cycle_lock = threading.Lock()
        
        # Metrics
        self.cycles_scheduled = 0
        self.cycles_executed = 0
        self.cycles_skipped = 0
        self.last_cycle_time: Optional[datetime] = None
        self.total_cycle_time_ms = 0.0
        
        logger.info(f"Trading Scheduler initialized: "
                   f"Interval={cycle_interval_minutes}min, "
                   f"Market hours: {start_time}-{end_time} {timezone}, "
                   f"Market hours filter: {enable_market_hours}")
    
    # ==================== LIFECYCLE CONTROL ====================
    
    def start(self) -> None:
        """Start the scheduler (runs in background thread)"""
        if self.status == SchedulerStatus.RUNNING:
            logger.warning("Scheduler is already running")
            return
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            logger.warning("Scheduler thread still running from previous start")
            return
        
        self.should_stop = False
        self.status = SchedulerStatus.RUNNING
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True,
            name="TradingScheduler"
        )
        self.scheduler_thread.start()
        logger.info("Scheduler started")
    
    def stop(self) -> None:
        """Stop the scheduler gracefully"""
        logger.info("Stopping scheduler...")
        self.should_stop = True
        
        # Wait for current cycle to finish
        if self.is_cycle_running:
            logger.info("Waiting for running cycle to complete...")
            max_wait = 300  # Wait max 5 minutes
            start_wait = time.time()
            while self.is_cycle_running and (time.time() - start_wait) < max_wait:
                time.sleep(0.1)
        
        # Wait for thread to finish
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=10)
        
        self.status = SchedulerStatus.STOPPED
        logger.info("Scheduler stopped")
    
    def pause(self) -> None:
        """Pause trading without stopping scheduler"""
        self.status = SchedulerStatus.PAUSED
        self.trading_engine.pause_trading()
        logger.info("Trading paused (scheduler still running)")
    
    def resume(self) -> None:
        """Resume trading"""
        self.trading_engine.resume_trading()
        self.status = SchedulerStatus.RUNNING
        logger.info("Trading resumed")
    
    # ==================== SCHEDULER LOOP ====================
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop (runs in background thread)"""
        logger.info("Scheduler loop started")
        
        try:
            while not self.should_stop:
                # Check if we should run a cycle
                should_run, reason = self._should_run_cycle()
                
                if should_run:
                    self._run_scheduled_cycle()
                else:
                    logger.debug(f"Cycle skipped: {reason}")
                    self.cycles_skipped += 1
                
                # Sleep before checking again
                time.sleep(1)  # Check every second if we should run
        
        except Exception as e:
            logger.error(f"Scheduler loop error: {e}", exc_info=True)
        
        finally:
            logger.info("Scheduler loop ended")
    
    def _should_run_cycle(self) -> tuple[bool, str]:
        """Determine if a cycle should run now"""
        
        # Check if stopped
        if self.should_stop:
            return False, "Scheduler is stopping"
        
        # Check if paused
        if self.status == SchedulerStatus.PAUSED:
            return False, "Scheduler is paused"
        
        # Check if previous cycle still running
        if self.is_cycle_running:
            return False, "Previous cycle still running"
        
        # Check trading engine halt flag
        if self.trading_engine.halt_flag:
            return False, "Trading engine halted (risk limit breach)"
        
        # Check market hours
        if self.enable_market_hours and not self._is_market_open():
            return False, "Market hours filter: outside trading hours"
        
        # Check cycle interval
        if not self._check_cycle_interval():
            return False, "Cycle interval not elapsed"
        
        return True, "Ready to run"
    
    def _run_scheduled_cycle(self) -> None:
        """Run a trading cycle"""
        # Acquire lock to prevent overlapping cycles
        if not self.cycle_lock.acquire(blocking=False):
            logger.warning("Could not acquire cycle lock (overlap detected)")
            return
        
        try:
            self.is_cycle_running = True
            self.cycles_scheduled += 1
            
            # Invoke callback if set
            if self.on_cycle_start:
                try:
                    self.on_cycle_start()
                except Exception as e:
                    logger.warning(f"on_cycle_start callback failed: {e}")
            
            # Run the cycle
            cycle_start = time.time()
            logger.debug(f"[SCHEDULED] Running cycle #{self.cycles_scheduled}")
            
            try:
                result = self.trading_engine.run_cycle()
                
                # Log results
                if result.get('status') == 'completed':
                    self.cycles_executed += 1
                    logger.info(f"[SCHEDULED] Cycle completed: "
                               f"Signals={result.get('signals_generated', 0)}, "
                               f"Trades={result.get('trades_executed', 0)}, "
                               f"Exits={result.get('positions_exited', 0)}")
                elif result.get('status') == 'halted':
                    logger.warning("[SCHEDULED] Cycle halted due to risk")
                else:
                    logger.error(f"[SCHEDULED] Cycle failed: {result.get('errors', [])}")
            
            except Exception as e:
                logger.error(f"[SCHEDULED] Cycle execution error: {e}", exc_info=True)
            
            # Record cycle time
            cycle_duration = (time.time() - cycle_start) * 1000
            self.total_cycle_time_ms += cycle_duration
            self.last_cycle_time = datetime.now(self.timezone)
            
            logger.debug(f"[SCHEDULED] Cycle duration: {cycle_duration:.2f}ms")
            
            # Invoke end callback
            if self.on_cycle_end:
                try:
                    self.on_cycle_end(result)
                except Exception as e:
                    logger.warning(f"on_cycle_end callback failed: {e}")
        
        finally:
            self.is_cycle_running = False
            self.cycle_lock.release()
    
    def _check_cycle_interval(self) -> bool:
        """Check if enough time has elapsed since last cycle"""
        if self.last_cycle_time is None:
            return True  # First cycle, run immediately
        
        time_since_last = (datetime.now(self.timezone) - self.last_cycle_time).total_seconds()
        return time_since_last >= self.cycle_interval_seconds
    
    def _is_market_open(self) -> bool:
        """Check if current time is within market hours"""
        if not self.enable_market_hours:
            return True
        
        # Get current time in configured timezone
        now = datetime.now(self.timezone).time()
        
        # Check if within market hours
        return self.market_start <= now <= self.market_end
    
    # ==================== DIAGNOSTICS ====================
    
    def get_status(self) -> Dict:
        """Get scheduler status and metrics"""
        avg_cycle_time = 0.0
        if self.cycles_executed > 0:
            avg_cycle_time = self.total_cycle_time_ms / self.cycles_executed
        
        return {
            'status': self.status.value,
            'is_running': self.status == SchedulerStatus.RUNNING,
            'is_paused': self.status == SchedulerStatus.PAUSED,
            'cycles_scheduled': self.cycles_scheduled,
            'cycles_executed': self.cycles_executed,
            'cycles_skipped': self.cycles_skipped,
            'last_cycle_time': self.last_cycle_time.isoformat() if self.last_cycle_time else None,
            'avg_cycle_time_ms': round(avg_cycle_time, 2),
            'cycle_interval_seconds': self.cycle_interval_seconds,
            'market_hours_enabled': self.enable_market_hours,
            'market_open': self._is_market_open(),
            'is_cycle_running': self.is_cycle_running,
            'trading_engine_halted': self.trading_engine.halt_flag,
        }
    
    def get_metrics(self) -> Dict:
        """Get performance metrics"""
        return {
            'total_scheduled': self.cycles_scheduled,
            'total_executed': self.cycles_executed,
            'total_skipped': self.cycles_skipped,
            'execution_rate': (
                (self.cycles_executed / self.cycles_scheduled * 100)
                if self.cycles_scheduled > 0 else 0
            ),
            'avg_cycle_time_ms': (
                (self.total_cycle_time_ms / self.cycles_executed)
                if self.cycles_executed > 0 else 0
            ),
            'total_cycle_time_ms': self.total_cycle_time_ms,
        }
