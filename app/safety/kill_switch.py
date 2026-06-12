"""
KILL-SWITCH SAFETY SYSTEM
=========================

Critical emergency stop mechanism for trading system.

Features:
- Manual trigger (API/command)
- Automatic triggers:
  - Daily drawdown threshold exceeded
  - Consecutive losses limit
  - Data feed heartbeat loss
  - System resource exhaustion
- Actions on activation:
  - Cancel all pending orders
  - Close all positions (market orders)
  - Halt trading loop
  - Alert all stakeholders
- Requires manual review/reset

Architecture:
    KillSwitchManager
    ├── Manual Triggers (API endpoints)
    ├── Automatic Triggers (Monitors)
    ├── Actions (Executor integration)
    └── State Management & Audit Log

Integration Points:
- TradingEngine: Check kill-switch status before execution
- RiskManager: Trigger on risk threshold breaches
- Executor: Execute position closing
- Notifications: Alert on activation
- Scheduler: Regular heartbeat checks
"""

import logging
import threading
import json
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable
import time

logger = logging.getLogger(__name__)


class KillSwitchReason(Enum):
    """Reasons for kill-switch activation"""
    # Manual triggers
    MANUAL_USER = "manual_user_trigger"
    MANUAL_API = "manual_api_trigger"
    MANUAL_CRITICAL_ERROR = "manual_critical_error"
    
    # Automatic triggers
    DAILY_DRAWDOWN_EXCEEDED = "daily_drawdown_exceeded"
    CONSECUTIVE_LOSSES = "consecutive_losses_limit"
    HEARTBEAT_LOSS = "data_feed_heartbeat_loss"
    API_CONNECTIVITY_LOSS = "api_connectivity_loss"
    ORDER_EXECUTION_FAILURE = "order_execution_failure"
    POSITION_LOSS_SPIKE = "position_loss_spike"
    SYSTEM_RESOURCE_EXHAUSTION = "system_resource_exhaustion"
    INVALID_SIGNAL_DETECTED = "invalid_signal_detected"
    CIRCUIT_BREAKER_HALT = "exchange_circuit_breaker"


@dataclass
class KillSwitchEvent:
    """Record of a kill-switch event"""
    event_id: str
    timestamp: datetime
    reason: KillSwitchReason
    triggered_by: str  # "manual", "system", "monitor"
    details: Dict
    status_before: str
    orders_cancelled: int
    positions_closed: int
    notification_sent: bool
    
    def to_dict(self):
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'reason': self.reason.value,
            'triggered_by': self.triggered_by,
            'details': self.details,
            'status_before': self.status_before,
            'orders_cancelled': self.orders_cancelled,
            'positions_closed': self.positions_closed,
            'notification_sent': self.notification_sent
        }


class KillSwitchManager:
    """
    Central kill-switch coordinator.
    
    Usage:
        kill_switch = KillSwitchManager(
            executor=signal_executor,
            risk_manager=risk_manager,
            notification_service=notify_service
        )
        
        # Register automatic triggers
        kill_switch.register_monitor('drawdown', monitor_drawdown)
        
        # Start monitoring
        kill_switch.start_monitoring()
        
        # Check before execution
        if kill_switch.is_active():
            raise Exception("Trading halted: Kill-switch active")
        
        # Manual trigger (emergency)
        kill_switch.trigger_manual(reason="Critical error detected")
    """
    
    def __init__(self, executor, risk_manager, notification_service=None):
        """
        Args:
            executor: SignalExecutor instance
            risk_manager: RiskManager instance
            notification_service: Optional notification service
        """
        self.executor = executor
        self.risk_manager = risk_manager
        self.notification_service = notification_service
        
        # State
        self.active = False
        self.activation_time = None
        self.activation_reason = None
        self.manual_reset_required = True
        
        # Monitoring
        self._monitors = {}
        self._monitor_thread = None
        self._monitor_running = False
        self._lock = threading.RLock()
        
        # Event history
        self.events: List[KillSwitchEvent] = []
        self.max_events_history = 1000
        
        # Configuration
        self.config = {
            'daily_drawdown_threshold': 0.10,      # 10%
            'consecutive_losses_threshold': 5,      # 5 losses
            'heartbeat_timeout_sec': 30,           # 30 seconds
            'api_timeout_sec': 10,                 # 10 seconds
            'position_loss_spike_pct': 0.05,       # 5% in single trade
            'check_interval_sec': 1,               # Monitor every 1 second
        }
        
        # Heartbeat tracking
        self._last_heartbeats = {
            'data_feed': time.time(),
            'broker_api': time.time(),
            'system': time.time()
        }
        
        logger.info("KillSwitchManager initialized")
    
    # ==================== STATE QUERIES ====================
    
    def is_active(self) -> bool:
        """Check if kill-switch is currently active"""
        with self._lock:
            return self.active
    
    def get_status(self) -> Dict:
        """Get complete status"""
        with self._lock:
            return {
                'active': self.active,
                'activation_time': self.activation_time.isoformat() if self.activation_time else None,
                'reason': self.activation_reason.value if self.activation_reason else None,
                'manual_reset_required': self.manual_reset_required,
                'events_count': len(self.events),
                'last_event': self.events[-1].to_dict() if self.events else None
            }
    
    # ==================== MANUAL TRIGGERS ====================
    
    def trigger_manual(self, reason: str = "Manual user trigger", triggered_by: str = "user"):
        """
        Manual kill-switch trigger (e.g., from UI/API).
        
        Args:
            reason: Human-readable reason
            triggered_by: Who triggered ("user", "api", "monitoring")
        """
        logger.critical(f"MANUAL KILL-SWITCH TRIGGERED: {reason} (by {triggered_by})")
        
        self._activate(
            reason_enum=KillSwitchReason.MANUAL_USER,
            reason_str=reason,
            triggered_by=triggered_by
        )
    
    def trigger_on_critical_error(self, error_msg: str):
        """Trigger due to critical system error"""
        logger.critical(f"KILL-SWITCH: Critical error: {error_msg}")
        
        self._activate(
            reason_enum=KillSwitchReason.MANUAL_CRITICAL_ERROR,
            reason_str=f"Critical error: {error_msg}",
            triggered_by="system"
        )
    
    # ==================== AUTOMATIC MONITORS ====================
    
    def register_monitor(self, name: str, monitor_func: Callable):
        """
        Register a monitor function that checks conditions.
        
        Monitor function signature:
            def monitor_func(kill_switch) -> (bool, str)
            Returns: (should_activate, reason)
        """
        self._monitors[name] = monitor_func
        logger.info(f"Registered monitor: {name}")
    
    def start_monitoring(self):
        """Start automatic monitoring thread"""
        with self._lock:
            if self._monitor_running:
                logger.warning("Monitoring already running")
                return
            
            self._monitor_running = True
            self._monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True,
                name="KillSwitchMonitor"
            )
            self._monitor_thread.start()
            logger.info("Kill-switch monitoring started")
    
    def stop_monitoring(self):
        """Stop automatic monitoring"""
        with self._lock:
            self._monitor_running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Kill-switch monitoring stopped")
    
    def _monitoring_loop(self):
        """Continuously check automatic triggers"""
        while self._monitor_running:
            try:
                self._check_automatic_triggers()
                time.sleep(self.config['check_interval_sec'])
            except Exception as e:
                logger.error(f"Error in kill-switch monitoring: {e}", exc_info=True)
    
    def _check_automatic_triggers(self):
        """Check all registered automatic triggers"""
        if self.active:
            return  # Already active
        
        for monitor_name, monitor_func in self._monitors.items():
            try:
                should_trigger, reason_str = monitor_func(self)
                if should_trigger:
                    logger.warning(f"Auto trigger from monitor '{monitor_name}': {reason_str}")
                    self._activate(
                        reason_enum=KillSwitchReason.DAILY_DRAWDOWN_EXCEEDED,
                        reason_str=reason_str,
                        triggered_by="monitor:" + monitor_name
                    )
                    break  # Activate and stop checking others
            except Exception as e:
                logger.error(f"Error in monitor '{monitor_name}': {e}")
    
    # ==================== HEARTBEAT MANAGEMENT ====================
    
    def update_heartbeat(self, service: str):
        """Update heartbeat for a service (data_feed, broker_api, system)"""
        with self._lock:
            if service in self._last_heartbeats:
                self._last_heartbeats[service] = time.time()
    
    def check_heartbeats(self) -> Dict[str, bool]:
        """
        Check heartbeat health of all services.
        
        Returns: {'data_feed': True/False, 'broker_api': True/False, ...}
        """
        with self._lock:
            timeout = self.config['heartbeat_timeout_sec']
            now = time.time()
            
            health = {}
            for service, last_beat in self._last_heartbeats.items():
                is_alive = (now - last_beat) < timeout
                health[service] = is_alive
            
            return health
    
    # ==================== INTERNAL ACTIVATION ====================
    
    def _activate(self, reason_enum: KillSwitchReason, reason_str: str, triggered_by: str):
        """
        Internal: Activate kill-switch and execute safety actions.
        """
        with self._lock:
            if self.active:
                logger.warning("Kill-switch already active")
                return
            
            self.active = True
            self.activation_time = datetime.now()
            self.activation_reason = reason_enum
            self.manual_reset_required = True
        
        try:
            # STEP 1: Cancel all pending orders
            logger.info("STEP 1: Cancelling all pending orders...")
            cancelled_count = self._cancel_all_orders()
            
            # STEP 2: Close all open positions
            logger.info("STEP 2: Closing all open positions...")
            closed_count = self._close_all_positions()
            
            # STEP 3: Halt trading loop (already halted by is_active() check)
            logger.warning("STEP 3: Trading loop halted")
            
            # STEP 4: Record event
            event = KillSwitchEvent(
                event_id=f"ks_{int(time.time() * 1000)}",
                timestamp=datetime.now(),
                reason=reason_enum,
                triggered_by=triggered_by,
                details={'reason_text': reason_str},
                status_before="active",
                orders_cancelled=cancelled_count,
                positions_closed=closed_count,
                notification_sent=False
            )
            self.events.append(event)
            if len(self.events) > self.max_events_history:
                self.events.pop(0)
            
            # STEP 5: Send alerts
            logger.critical(f"STEP 4: Sending alerts...")
            event.notification_sent = self._send_alerts(
                reason=reason_str,
                event=event
            )
            
            logger.critical("="*60)
            logger.critical("KILL-SWITCH ACTIVATION COMPLETE")
            logger.critical(f"  Reason: {reason_str}")
            logger.critical(f"  Orders cancelled: {cancelled_count}")
            logger.critical(f"  Positions closed: {closed_count}")
            logger.critical(f"  MANUAL RESET REQUIRED")
            logger.critical("="*60)
            
        except Exception as e:
            logger.error(f"Error during kill-switch activation: {e}", exc_info=True)
    
    def _cancel_all_orders(self) -> int:
        """Cancel all pending orders"""
        try:
            # Executor should have cancel_all method
            if hasattr(self.executor, 'cancel_all_orders'):
                return self.executor.cancel_all_orders()
            else:
                logger.warning("Executor doesn't have cancel_all_orders method")
                return 0
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}", exc_info=True)
            return 0
    
    def _close_all_positions(self) -> int:
        """Close all open positions"""
        try:
            # Executor should have close_all_positions method
            if hasattr(self.executor, 'close_all_positions'):
                return self.executor.close_all_positions()
            else:
                logger.warning("Executor doesn't have close_all_positions method")
                return 0
        except Exception as e:
            logger.error(f"Error closing positions: {e}", exc_info=True)
            return 0
    
    def _send_alerts(self, reason: str, event: KillSwitchEvent) -> bool:
        """Send alerts to notification service"""
        try:
            if self.notification_service:
                self.notification_service.alert(
                    level="CRITICAL",
                    title="KILL-SWITCH ACTIVATED",
                    message=f"Trading system halted!\nReason: {reason}\n"
                            f"Event ID: {event.event_id}\n"
                            f"Orders cancelled: {event.orders_cancelled}\n"
                            f"Positions closed: {event.positions_closed}"
                )
                return True
            else:
                logger.info("No notification service configured")
                return False
        except Exception as e:
            logger.error(f"Error sending alerts: {e}")
            return False
    
    # ==================== MANUAL RESET ====================
    
    def reset(self, confirmed: bool = False) -> bool:
        """
        Manual reset of kill-switch.
        Requires confirmation to prevent accidental resets.
        
        Args:
            confirmed: Must be True to actually reset
        
        Returns: True if reset successful
        """
        if not confirmed:
            logger.warning("Kill-switch reset requires confirmation")
            return False
        
        with self._lock:
            if not self.active:
                logger.warning("Kill-switch not active")
                return False
            
            self.active = False
            self.activation_time = None
            self.activation_reason = None
            self.manual_reset_required = False
        
        logger.warning("KILL-SWITCH RESET - System ready to trade")
        return True
    
    # ==================== HISTORY & AUDIT ====================
    
    def get_event_history(self, last_n: int = 10) -> List[Dict]:
        """Get last N events"""
        with self._lock:
            return [e.to_dict() for e in self.events[-last_n:]]
    
    def export_events_to_file(self, filepath: str):
        """Export all events to JSON file for audit"""
        with self._lock:
            events_list = [e.to_dict() for e in self.events]
        
        with open(filepath, 'w') as f:
            json.dump(events_list, f, indent=2)
        
        logger.info(f"Exported {len(events_list)} kill-switch events to {filepath}")
    
    # ==================== CONFIGURATION ====================
    
    def set_config(self, config_dict: Dict):
        """Update configuration"""
        self.config.update(config_dict)
        logger.info(f"Kill-switch config updated: {config_dict}")
    
    def get_config(self) -> Dict:
        """Get current configuration"""
        return self.config.copy()


# ==================== BUILT-IN MONITORS ====================

def monitor_daily_drawdown(kill_switch: KillSwitchManager) -> tuple:
    """Monitor daily drawdown threshold"""
    try:
        # Get portfolio state from risk manager
        portfolio = kill_switch.risk_manager.get_portfolio_state()
        daily_pnl = portfolio.get('daily_pnl', 0)
        starting_capital = portfolio.get('starting_capital', 100000)
        
        drawdown = abs(daily_pnl) / starting_capital if daily_pnl < 0 else 0
        threshold = kill_switch.config['daily_drawdown_threshold']
        
        if drawdown > threshold:
            return True, f"Daily drawdown {drawdown*100:.1f}% exceeds threshold {threshold*100:.1f}%"
        return False, ""
    except Exception as e:
        logger.error(f"Error in drawdown monitor: {e}")
        return False, ""


def monitor_consecutive_losses(kill_switch: KillSwitchManager) -> tuple:
    """Monitor consecutive losses"""
    try:
        portfolio = kill_switch.risk_manager.get_portfolio_state()
        consecutive_losses = portfolio.get('consecutive_losses', 0)
        threshold = kill_switch.config['consecutive_losses_threshold']
        
        if consecutive_losses >= threshold:
            return True, f"Consecutive losses {consecutive_losses} >= threshold {threshold}"
        return False, ""
    except Exception as e:
        logger.error(f"Error in consecutive losses monitor: {e}")
        return False, ""


def monitor_heartbeats(kill_switch: KillSwitchManager) -> tuple:
    """Monitor service heartbeats"""
    try:
        health = kill_switch.check_heartbeats()
        
        for service, is_alive in health.items():
            if not is_alive:
                return True, f"Heartbeat loss: {service}"
        
        return False, ""
    except Exception as e:
        logger.error(f"Error in heartbeat monitor: {e}")
        return False, ""


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    """
    Example usage and testing
    """
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Mock objects for testing
    class MockExecutor:
        def cancel_all_orders(self):
            print("  [Executor] Cancelled 3 pending orders")
            return 3
        
        def close_all_positions(self):
            print("  [Executor] Closed 2 open positions")
            return 2
    
    class MockRiskManager:
        def get_portfolio_state(self):
            return {
                'daily_pnl': -8000,
                'starting_capital': 100000,
                'consecutive_losses': 3
            }
    
    # Initialize
    executor = MockExecutor()
    risk_manager = MockRiskManager()
    kill_switch = KillSwitchManager(executor, risk_manager)
    
    # Register monitors
    kill_switch.register_monitor('drawdown', monitor_daily_drawdown)
    kill_switch.register_monitor('losses', monitor_consecutive_losses)
    kill_switch.register_monitor('heartbeats', monitor_heartbeats)
    
    # Test 1: Manual trigger
    print("\n--- Test 1: Manual Trigger ---")
    kill_switch.trigger_manual(reason="User initiated emergency stop", triggered_by="user")
    print(f"Status: {kill_switch.get_status()}")
    
    # Test 2: Reset
    print("\n--- Test 2: Reset ---")
    success = kill_switch.reset(confirmed=True)
    print(f"Reset successful: {success}")
    print(f"Status: {kill_switch.get_status()}")
    
    # Test 3: Automatic trigger
    print("\n--- Test 3: Automatic Trigger (via monitoring) ---")
    kill_switch.start_monitoring()
    time.sleep(2)  # Let monitor run
    print(f"Active after monitoring: {kill_switch.is_active()}")
    kill_switch.stop_monitoring()
    
    # Test 4: Event history
    print("\n--- Test 4: Event History ---")
    history = kill_switch.get_event_history(last_n=5)
    for event in history:
        print(f"  {event['timestamp']}: {event['reason']} ({event['triggered_by']})")
