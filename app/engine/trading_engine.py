"""
Central Trading Engine (Orchestrator)
=====================================
Orchestrates the complete 5-stage trading pipeline:
1. Signal Generation (Stock Screener → Signals)
2. Validation & Risk Guardrails (Production Validator → Regime Monitor)
3. Trade Execution (Order Manager → Breeze API)
4. Exit Management (Profit Booking Manager → Position Tracking)
5. Risk Monitoring & Alerts (Position Tracker → Notifications)

This is the "brain" of the trading system, ensuring all components work in unison
with proper data hand-offs and risk gating.

Usage:
    engine = TradingEngine(
        screener=stock_screener,
        validator=production_validator,
        regime_monitor=strategy_regime_monitor,
        executor=signal_executor,
        profit_manager=profit_booking_manager,
        position_tracker=live_position_tracker,
        risk_manager=risk_manager,
        notifications=notification_service
    )
    
    # Run one complete trading cycle
    result = engine.run_cycle()
    
    # Check cycle performance
    print(f"Signals: {result['signals_generated']}")
    print(f"Executed: {result['trades_executed']}")
    print(f"Exited: {result['positions_exited']}")
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import json
import time

logger = logging.getLogger(__name__)


class CycleStatus(Enum):
    """Status of a trading cycle"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    HALTED = "halted"  # Due to risk breach


@dataclass
class CycleMetrics:
    """Metrics from a single trading cycle"""
    cycle_id: str
    timestamp: datetime
    duration_ms: float
    
    # Stage 1: Signal Generation
    signals_generated: int
    signal_details: List[Dict] = None
    
    # Stage 2: Validation & Risk
    signals_validated: int
    signals_rejected: int
    rejection_reasons: List[str] = None
    regime: str = "unknown"
    
    # Stage 3: Trade Execution
    trades_executed: int
    execution_failures: int
    execution_errors: List[str] = None
    
    # Stage 4: Exit Management
    positions_monitored: int
    positions_exited: int
    exit_details: List[Dict] = None
    
    # Stage 5: Risk Monitoring
    risk_alerts: int
    daily_pnl: float = 0.0
    portfolio_value: float = 0.0
    
    # Overall
    status: str = "completed"
    errors: List[str] = None
    
    def to_dict(self):
        """Convert metrics to dictionary"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        d['status'] = d['status'].value if isinstance(d['status'], Enum) else d['status']
        return d
    
    def to_json(self) -> str:
        """Convert metrics to JSON"""
        return json.dumps(self.to_dict(), default=str, indent=2)


class TradingEngine:
    """
    Central orchestrator for the 5-stage trading pipeline.
    
    Responsibilities:
    - Coordinate Stage 1 through Stage 5 in sequence
    - Pass outputs from one stage as inputs to the next
    - Apply risk gating at each stage
    - Halt execution if risk thresholds breached
    - Log all cycle activity and metrics
    - Provide introspection and debugging tools
    """
    
    def __init__(self,
                 screener,                    # Stage 1: Signal Generation
                 validator,                   # Stage 2: Validation
                 regime_monitor,              # Stage 2: Regime Detection
                 executor,                    # Stage 3: Trade Execution
                 profit_manager,              # Stage 4: Exit Management
                 position_tracker,            # Stage 5: Monitoring
                 risk_manager,                # Risk validation service
                 notifications=None):         # Alert service
        """
        Initialize the trading engine
        
        Args:
            screener: Stock screener service (generates signals)
            validator: Production validator (checks signal validity)
            regime_monitor: Regime detector (determines market condition)
            executor: Signal executor (places orders)
            profit_manager: Profit booking manager (handles exits)
            position_tracker: Live position tracker (monitors positions)
            risk_manager: Risk manager (validates risk limits)
            notifications: Notification service (optional, sends alerts)
        """
        self.screener = screener
        self.validator = validator
        self.regime_monitor = regime_monitor
        self.executor = executor
        self.profit_manager = profit_manager
        self.position_tracker = position_tracker
        self.risk_manager = risk_manager
        self.notifications = notifications
        
        # Cycle tracking
        self.cycle_count = 0
        self.cycle_history: List[CycleMetrics] = []
        self.halt_flag = False  # Set to True to halt trading
        self.last_cycle_metrics: Optional[CycleMetrics] = None
        
        # Risk thresholds
        self.daily_loss_limit = getattr(risk_manager.config, 'MAX_DAILY_LOSS', 0.10)  # 10%
        self.daily_pnl_check_enabled = True
        
        logger.info("Trading Engine initialized with all 5-stage pipeline components")
    
    # ==================== MAIN CYCLE ====================
    
    def run_cycle(self) -> Dict:
        """
        Execute one complete trading cycle through all 5 stages.
        
        Pipeline:
        Stage 1 → Get signals from screener
        Stage 2 → Validate and check regime
        Stage 3 → Execute approved signals
        Stage 4 → Manage exits for open positions
        Stage 5 → Monitor positions and send alerts
        
        Returns:
            CycleMetrics with results and diagnostics
        """
        cycle_start = time.time()
        self.cycle_count += 1
        cycle_id = f"cycle_{self.cycle_count}_{int(cycle_start)}"
        
        metrics = CycleMetrics(
            cycle_id=cycle_id,
            timestamp=datetime.now(),
            duration_ms=0,
            signals_generated=0,
            signals_validated=0,
            signals_rejected=0,
            trades_executed=0,
            execution_failures=0,
            positions_monitored=0,
            positions_exited=0,
            risk_alerts=0
        )
        
        try:
            logger.info(f"[{cycle_id}] Starting trading cycle #{self.cycle_count}")
            
            # ===== STAGE 1: SIGNAL GENERATION =====
            logger.debug(f"[{cycle_id}] Stage 1: Generating signals...")
            try:
                signals = self._stage_1_signal_generation(metrics)
            except Exception as e:
                logger.error(f"[{cycle_id}] Stage 1 failed: {e}")
                metrics.errors = metrics.errors or []
                metrics.errors.append(f"Stage 1 Signal Generation failed: {str(e)}")
                metrics.status = "failed"
                return self._finalize_cycle(metrics, cycle_start)
            
            if not signals:
                logger.debug(f"[{cycle_id}] No signals generated, cycle complete")
                metrics.status = "completed"
                return self._finalize_cycle(metrics, cycle_start)
            
            # ===== STAGE 2: VALIDATION & RISK GUARDRAILS =====
            logger.debug(f"[{cycle_id}] Stage 2: Validating signals and checking regime...")
            try:
                approved_signals = self._stage_2_validation_and_risk(signals, metrics)
            except Exception as e:
                logger.error(f"[{cycle_id}] Stage 2 failed: {e}")
                metrics.errors = metrics.errors or []
                metrics.errors.append(f"Stage 2 Validation failed: {str(e)}")
                metrics.status = "failed"
                return self._finalize_cycle(metrics, cycle_start)
            
            if not approved_signals:
                logger.info(f"[{cycle_id}] All signals rejected at validation stage")
                metrics.status = "completed"
                return self._finalize_cycle(metrics, cycle_start)
            
            # Check if trading should be halted due to risk
            if self._check_halt_conditions(metrics):
                logger.warning(f"[{cycle_id}] Trading halted due to risk breach")
                metrics.status = "halted"
                return self._finalize_cycle(metrics, cycle_start)
            
            # ===== STAGE 3: TRADE EXECUTION =====
            logger.debug(f"[{cycle_id}] Stage 3: Executing approved signals...")
            try:
                self._stage_3_trade_execution(approved_signals, metrics)
            except Exception as e:
                logger.error(f"[{cycle_id}] Stage 3 failed: {e}")
                metrics.errors = metrics.errors or []
                metrics.errors.append(f"Stage 3 Trade Execution failed: {str(e)}")
                # Continue to later stages even if execution has errors
            
            # ===== STAGE 4: EXIT MANAGEMENT =====
            logger.debug(f"[{cycle_id}] Stage 4: Managing exits for open positions...")
            try:
                self._stage_4_exit_management(metrics)
            except Exception as e:
                logger.error(f"[{cycle_id}] Stage 4 failed: {e}")
                metrics.errors = metrics.errors or []
                metrics.errors.append(f"Stage 4 Exit Management failed: {str(e)}")
                # Continue to monitoring stage
            
            # ===== STAGE 5: RISK MONITORING & ALERTS =====
            logger.debug(f"[{cycle_id}] Stage 5: Monitoring positions and sending alerts...")
            try:
                self._stage_5_monitoring_and_alerts(metrics)
            except Exception as e:
                logger.error(f"[{cycle_id}] Stage 5 failed: {e}")
                metrics.errors = metrics.errors or []
                metrics.errors.append(f"Stage 5 Monitoring failed: {str(e)}")
                # Continue to finalization
            
            metrics.status = "completed"
            logger.info(f"[{cycle_id}] Cycle completed successfully")
            
        except Exception as e:
            logger.error(f"[{cycle_id}] Unexpected error during cycle: {e}")
            metrics.status = "failed"
            metrics.errors = metrics.errors or []
            metrics.errors.append(f"Unexpected error: {str(e)}")
        
        return self._finalize_cycle(metrics, cycle_start)
    
    # ==================== STAGE IMPLEMENTATIONS ====================
    
    def _stage_1_signal_generation(self, metrics: CycleMetrics) -> List[Dict]:
        """
        Stage 1: Signal Generation
        Screener identifies potential trade opportunities
        """
        try:
            # Get signals from screener
            signals = self.screener.get_signals()
            
            if not signals:
                logger.debug("No signals from screener")
                metrics.signals_generated = 0
                metrics.signal_details = []
                return []
            
            metrics.signals_generated = len(signals)
            metrics.signal_details = [
                {
                    'symbol': s.get('symbol', 'UNKNOWN'),
                    'direction': s.get('direction', 'UNKNOWN'),
                    'confidence': s.get('confidence', 0.0),
                    'reason': s.get('reason', '')
                }
                for s in signals
            ]
            
            logger.info(f"Stage 1 complete: Generated {metrics.signals_generated} signals")
            return signals
            
        except Exception as e:
            logger.error(f"Stage 1 error: {e}")
            raise
    
    def _stage_2_validation_and_risk(self, signals: List[Dict], 
                                     metrics: CycleMetrics) -> List[Dict]:
        """
        Stage 2: Validation & Risk Guardrails
        - Check signal validity with Production Validator
        - Detect market regime with Regime Monitor
        - Apply risk filters
        - Gate signals that don't pass validation
        """
        approved_signals = []
        rejection_reasons = []
        
        try:
            # First, detect current market regime
            regime = self._detect_market_regime(metrics)
            metrics.regime = regime
            logger.info(f"Current market regime: {regime}")
            
            # Validate each signal
            for signal in signals:
                symbol = signal.get('symbol', 'UNKNOWN')
                
                # Check 1: Production Validator
                is_valid, validation_reason = self._validate_signal(signal, regime)
                if not is_valid:
                    rejection_reasons.append(f"{symbol}: {validation_reason}")
                    metrics.signals_rejected += 1
                    logger.debug(f"Signal {symbol} rejected: {validation_reason}")
                    continue
                
                # Check 2: Risk Manager pre-trade checks
                risk_ok, risk_reason = self._check_signal_risk(signal)
                if not risk_ok:
                    rejection_reasons.append(f"{symbol}: Risk check failed - {risk_reason}")
                    metrics.signals_rejected += 1
                    logger.debug(f"Signal {symbol} failed risk check: {risk_reason}")
                    continue
                
                # Check 3: Apply regime-specific exit strategy
                signal['exit_strategy'] = self._select_exit_strategy(regime)
                
                # Signal approved
                approved_signals.append(signal)
                metrics.signals_validated += 1
                logger.debug(f"Signal {symbol} approved for execution")
            
            metrics.rejection_reasons = rejection_reasons
            logger.info(f"Stage 2 complete: {metrics.signals_validated} approved, "
                       f"{metrics.signals_rejected} rejected")
            
            return approved_signals
            
        except Exception as e:
            logger.error(f"Stage 2 error: {e}")
            raise
    
    def _stage_3_trade_execution(self, signals: List[Dict], metrics: CycleMetrics) -> None:
        """
        Stage 3: Trade Execution
        - Place orders for approved signals
        - Perform final pre-trade risk checks
        - Integrate with Risk Manager
        - Execute via Order Manager / Breeze API
        """
        try:
            for signal in signals:
                symbol = signal.get('symbol', 'UNKNOWN')
                direction = signal.get('direction', 'BUY')
                
                try:
                    # Pre-trade risk engine check (final gate)
                    quantity = signal.get('quantity') or self._calculate_position_size(signal)
                    pre_trade_ok, pre_trade_reason = self.risk_manager.validate_order({
                        'stock_code': symbol,
                        'quantity': quantity,
                        'price': signal.get('price', 0.0),
                        'action': direction
                    })
                    
                    if not pre_trade_ok:
                        logger.warning(f"Pre-trade risk check failed for {symbol}: {pre_trade_reason}")
                        metrics.execution_failures += 1
                        metrics.execution_errors = metrics.execution_errors or []
                        metrics.execution_errors.append(f"{symbol}: {pre_trade_reason}")
                        continue
                    
                    # Execute the signal
                    if direction.upper() == 'BUY':
                        result = self.executor.execute_buy_signal(
                            symbol=symbol,
                            price=signal.get('price', 0.0),
                            confidence=signal.get('confidence', 0.8),
                            reason=signal.get('reason', 'screener'),
                            metadata=signal,
                            quantity=quantity
                        )
                    else:  # SELL
                        result = self.executor.execute_sell_signal(
                            symbol=symbol,
                            price=signal.get('price', 0.0),
                            metadata=signal
                        )
                    
                    if result.get('success', False):
                        metrics.trades_executed += 1
                        logger.info(f"Successfully executed {direction} signal for {symbol}")
                    else:
                        metrics.execution_failures += 1
                        error_msg = result.get('error', 'Unknown error')
                        metrics.execution_errors = metrics.execution_errors or []
                        metrics.execution_errors.append(f"{symbol}: {error_msg}")
                        logger.error(f"Execution failed for {symbol}: {error_msg}")
                
                except Exception as e:
                    metrics.execution_failures += 1
                    metrics.execution_errors = metrics.execution_errors or []
                    metrics.execution_errors.append(f"{symbol}: {str(e)}")
                    logger.error(f"Exception executing signal for {symbol}: {e}")
            
            logger.info(f"Stage 3 complete: {metrics.trades_executed} executed, "
                       f"{metrics.execution_failures} failed")
            
        except Exception as e:
            logger.error(f"Stage 3 error: {e}")
            raise
    
    def _stage_4_exit_management(self, metrics: CycleMetrics) -> None:
        """
        Stage 4: Exit Management
        - Hands off open positions to Profit Booking Manager
        - Profit manager decides full capture vs trailing stop
        - Orchestrator listens for exit signals
        - Executes closing orders at target or when stops hit
        """
        try:
            # Get current open positions
            open_positions = self.position_tracker.get_open_positions()
            metrics.positions_monitored = len(open_positions) if open_positions else 0
            
            if not open_positions:
                logger.debug("No open positions to manage exits")
                return
            
            # Process each open position through profit booking manager
            for position in open_positions:
                symbol = position.get('symbol', 'UNKNOWN')
                
                try:
                    # Check if position needs to exit
                    exit_signal = self.profit_manager.check_position_exit(position)
                    
                    if exit_signal:
                        # Execute exit
                        exit_result = self.executor.execute_sell_signal(
                            symbol=symbol,
                            price=exit_signal.get('price', 0.0),
                            metadata={'exit_reason': exit_signal.get('reason', 'profit_booking')}
                        )
                        
                        if exit_result.get('success', False):
                            metrics.positions_exited += 1
                            exit_details = {
                                'symbol': symbol,
                                'reason': exit_signal.get('reason', 'unknown'),
                                'exit_price': exit_signal.get('price', 0.0),
                                'pnl': exit_signal.get('pnl', 0.0),
                                'pnl_pct': exit_signal.get('pnl_pct', 0.0)
                            }
                            metrics.exit_details = metrics.exit_details or []
                            metrics.exit_details.append(exit_details)
                            logger.info(f"Position exited for {symbol}: {exit_signal.get('reason')}")
                        else:
                            logger.error(f"Failed to exit position for {symbol}: "
                                       f"{exit_result.get('error', 'Unknown error')}")
                
                except Exception as e:
                    logger.error(f"Error managing exit for {symbol}: {e}")
            
            logger.info(f"Stage 4 complete: {metrics.positions_exited} positions exited")
            
        except Exception as e:
            logger.error(f"Stage 4 error: {e}")
            raise
    
    def _stage_5_monitoring_and_alerts(self, metrics: CycleMetrics) -> None:
        """
        Stage 5: Risk Monitoring & Alerts
        - Update Position Tracker with latest position metrics
        - Trigger notifications (email/Telegram) about outcomes
        - Log performance metrics
        - Check for risk anomalies
        - Determine if daily loss limit breached
        """
        try:
            # Update position metrics
            portfolio_metrics = self.position_tracker.get_portfolio_metrics()
            metrics.portfolio_value = portfolio_metrics.get('total_value', 0.0)
            metrics.daily_pnl = portfolio_metrics.get('daily_pnl', 0.0)
            
            # Check for risk alerts
            alerts = []
            
            # Check daily loss limit
            if self.daily_pnl_check_enabled:
                daily_loss_pct = abs(metrics.daily_pnl) / max(1, metrics.portfolio_value)
                if metrics.daily_pnl < 0 and daily_loss_pct >= self.daily_loss_limit:
                    alerts.append({
                        'type': 'DAILY_LOSS_LIMIT',
                        'message': f"Daily loss limit reached: {daily_loss_pct*100:.2f}%",
                        'severity': 'HIGH'
                    })
                    self.halt_flag = True  # Halt further trading
            
            # Log alerts
            metrics.risk_alerts = len(alerts)
            
            # Send notifications if available
            if self.notifications and alerts:
                for alert in alerts:
                    try:
                        self.notifications.send_alert(
                            subject=alert['type'],
                            message=alert['message'],
                            severity=alert.get('severity', 'MEDIUM')
                        )
                        logger.info(f"Alert sent: {alert['type']}")
                    except Exception as e:
                        logger.warning(f"Failed to send notification: {e}")
            
            # Log cycle performance
            logger.info(f"Stage 5 complete: Portfolio value: {metrics.portfolio_value:.2f}, "
                       f"Daily P&L: {metrics.daily_pnl:.2f}, "
                       f"Risk alerts: {metrics.risk_alerts}")
            
        except Exception as e:
            logger.error(f"Stage 5 error: {e}")
            raise
    
    # ==================== HELPER METHODS ====================
    
    def _detect_market_regime(self, metrics: CycleMetrics) -> str:
        """Detect current market regime using regime monitor"""
        try:
            if hasattr(self.regime_monitor, 'get_current_regime'):
                return self.regime_monitor.get_current_regime()
            elif hasattr(self.regime_monitor, 'current_regime'):
                return self.regime_monitor.current_regime
            return 'unknown'
        except Exception as e:
            logger.warning(f"Failed to detect regime: {e}")
            return 'unknown'
    
    def _validate_signal(self, signal: Dict, regime: str) -> Tuple[bool, str]:
        """Validate a signal using Production Validator"""
        try:
            if hasattr(self.validator, 'validate_signal'):
                is_valid, reason = self.validator.validate_signal(signal, regime)
            else:
                # Fallback: basic validation
                is_valid = signal.get('confidence', 0) >= 0.5
                reason = "Basic confidence check" if is_valid else "Low confidence"
            
            return is_valid, reason
        except Exception as e:
            logger.warning(f"Validation check failed: {e}")
            return False, str(e)
    
    def _check_signal_risk(self, signal: Dict) -> Tuple[bool, str]:
        """Check risk parameters for a signal"""
        try:
            symbol = signal.get('symbol', 'UNKNOWN')
            quantity = signal.get('quantity', 1)
            price = signal.get('price', 0.0)
            
            # Validate order with risk manager
            is_valid, reason = self.risk_manager.validate_order({
                'stock_code': symbol,
                'quantity': quantity,
                'price': price,
                'action': signal.get('direction', 'BUY')
            })
            
            return is_valid, reason
        except Exception as e:
            logger.warning(f"Risk check failed: {e}")
            return False, str(e)
    
    def _select_exit_strategy(self, regime: str) -> str:
        """Select exit strategy based on market regime"""
        if regime == 'trending':
            return 'partial_with_trailing'
        elif regime == 'mean_reverting':
            return 'fixed_full_exit'
        else:
            return 'hybrid_adaptive'
    
    def _calculate_position_size(self, signal: Dict) -> int:
        """Calculate position size for a signal"""
        try:
            # Use risk manager's position sizing logic
            if hasattr(self.risk_manager, 'calculate_position_size'):
                return self.risk_manager.calculate_position_size(signal)
            else:
                # Default: 1 lot
                return 1
        except Exception as e:
            logger.warning(f"Position sizing failed: {e}")
            return 1
    
    def _check_halt_conditions(self, metrics: CycleMetrics) -> bool:
        """Check if trading should be halted"""
        # Check explicit halt flag
        if self.halt_flag:
            return True
        
        # Check daily loss limit
        if self.daily_pnl_check_enabled and metrics.daily_pnl < 0:
            daily_loss_pct = abs(metrics.daily_pnl) / max(1, metrics.portfolio_value)
            if daily_loss_pct >= self.daily_loss_limit:
                return True
        
        return False
    
    def _finalize_cycle(self, metrics: CycleMetrics, cycle_start: float) -> Dict:
        """Finalize cycle and store metrics"""
        metrics.duration_ms = (time.time() - cycle_start) * 1000
        self.last_cycle_metrics = metrics
        self.cycle_history.append(metrics)
        
        # Keep last 1000 cycles
        if len(self.cycle_history) > 1000:
            self.cycle_history = self.cycle_history[-1000:]
        
        logger.info(f"Cycle {self.cycle_count} finalized in {metrics.duration_ms:.2f}ms "
                   f"(Status: {metrics.status})")
        
        return metrics.to_dict()
    
    # ==================== DIAGNOSTICS & INTROSPECTION ====================
    
    def get_last_cycle_metrics(self) -> Optional[Dict]:
        """Get metrics from the last cycle"""
        if self.last_cycle_metrics:
            return self.last_cycle_metrics.to_dict()
        return None
    
    def get_cycle_history(self, limit: int = 10) -> List[Dict]:
        """Get recent cycle history"""
        return [m.to_dict() for m in self.cycle_history[-limit:]]
    
    def get_cycle_statistics(self) -> Dict:
        """Get aggregate statistics across all cycles"""
        if not self.cycle_history:
            return {
                'total_cycles': 0,
                'total_signals': 0,
                'total_trades': 0,
                'success_rate': 0.0,
                'avg_cycle_time_ms': 0.0
            }
        
        total_signals = sum(m.signals_generated for m in self.cycle_history)
        total_trades = sum(m.trades_executed for m in self.cycle_history)
        total_exits = sum(m.positions_exited for m in self.cycle_history)
        avg_cycle_time = sum(m.duration_ms for m in self.cycle_history) / len(self.cycle_history)
        
        success_cycles = sum(1 for m in self.cycle_history if m.status == 'completed')
        success_rate = (success_cycles / len(self.cycle_history)) * 100
        
        return {
            'total_cycles': len(self.cycle_history),
            'total_signals': total_signals,
            'total_trades': total_trades,
            'total_exits': total_exits,
            'success_rate': success_rate,
            'avg_cycle_time_ms': avg_cycle_time,
            'halt_status': self.halt_flag
        }
    
    def reset_halt(self) -> None:
        """Reset halt flag to resume trading"""
        self.halt_flag = False
        logger.info("Trading halt cleared")
    
    def pause_trading(self) -> None:
        """Pause trading (set halt flag)"""
        self.halt_flag = True
        logger.info("Trading paused")
    
    def resume_trading(self) -> None:
        """Resume trading (clear halt flag)"""
        self.halt_flag = False
        logger.info("Trading resumed")
