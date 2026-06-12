"""
Options Trading System - Integrated Orchestrator
Phases 1-5 Combined: Complete options trading pipeline
Signal → Options Chain → Strategy Selection → Execution → Exit → Risk Management
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TradingSignal:
    """Input signal from ML engine"""
    underlying: str
    direction: str  # BUY, SELL, NEUTRAL
    confidence: float
    expected_move_pct: float
    timestamp: datetime


class OptionsTradeOrchestrator:
    """
    Complete options trading orchestrator
    Integrates: Chain Manager → Strategy Selector → Executor → Exit → Risk Manager
    """
    
    def __init__(
        self,
        breeze_client,
        chain_manager,
        strategy_selector,
        executor,
        exit_manager,
        risk_manager,
        portfolio_manager
    ):
        """
        Initialize orchestrator with all components
        """
        self.breeze = breeze_client
        self.chain_manager = chain_manager
        self.strategy_selector = strategy_selector
        self.executor = executor
        self.exit_manager = exit_manager
        self.risk_manager = risk_manager
        self.portfolio = portfolio_manager
        
        self.open_positions: List = []
        self.closed_positions: List = []
    
    def process_signal(self, signal: TradingSignal, dry_run: bool = False) -> Tuple[bool, str]:
        """
        Process incoming trading signal through complete pipeline
        
        Pipeline:
        1. Fetch options chain
        2. Select optimal strategy
        3. Validate risk
        4. Execute trade
        5. Track position
        
        Returns:
            (success, message)
        """
        try:
            logger.info(
                f"\n{'='*80}\n"
                f"[SIGNAL] Processing {signal.direction} signal for {signal.underlying}\n"
                f"Confidence: {signal.confidence:.2%}, Expected Move: {signal.expected_move_pct:.2f}%\n"
                f"{'='*80}"
            )
            
            # Step 1: Get current underlying price
            current_price = self._get_current_price(signal.underlying)
            if not current_price:
                return False, f"Cannot fetch price for {signal.underlying}"
            
            logger.info(f"[PRICE] {signal.underlying} = Rs {current_price:.2f}")
            
            # Step 2: Fetch options chain
            logger.info("[PHASE1] Fetching options chain...")
            chain = self.chain_manager.fetch_option_chain(signal.underlying, refresh=True)
            if not chain:
                return False, f"Failed to fetch options chain for {signal.underlying}"
            
            logger.info(
                f"[PHASE1] Chain fetched: {len(chain.calls)} calls, {len(chain.puts)} puts, "
                f"IV Percentile: {chain.iv_percentile:.1f}"
            )
            
            # Step 3: Select strategy
            logger.info("[PHASE2] Selecting optimal options strategy...")
            trade_plan = self.strategy_selector.select_strategy(
                underlying=signal.underlying,
                signal_direction=signal.direction,
                confidence=signal.confidence,
                expected_move_pct=signal.expected_move_pct,
                current_price=current_price,
                time_horizon_days=5,
                max_risk_per_trade=5000.0
            )
            
            if not trade_plan or not trade_plan.is_feasible:
                reason = trade_plan.feasibility_reason if trade_plan else "No feasible strategy"
                logger.warning(f"[PHASE2] Strategy selection failed: {reason}")
                return False, reason
            
            logger.info(
                f"[PHASE2] Strategy selected: {trade_plan.strategy.value}\n"
                f"  Max Gain: Rs {trade_plan.max_gain:.2f}\n"
                f"  Max Loss: Rs {trade_plan.max_loss:.2f}\n"
                f"  PoP: {trade_plan.probability_of_profit:.2%}\n"
                f"  Greeks - Delta: {trade_plan.portfolio_delta:.3f}, "
                f"Theta: {trade_plan.portfolio_theta:.2f}, Vega: {trade_plan.portfolio_vega:.2f}"
            )
            
            # Step 4: Risk validation
            logger.info("[PHASE5] Validating risk constraints...")
            self.risk_manager.update_portfolio_greeks(self.open_positions)
            is_valid, validation_msg = self.risk_manager.validate_trade_plan(
                trade_plan, self.open_positions
            )
            
            if not is_valid:
                logger.warning(f"[PHASE5] Risk validation failed: {validation_msg}")
                return False, validation_msg
            
            logger.info(f"[PHASE5] Risk validation passed: {validation_msg}")
            
            # Step 5: Check kill-switch triggers
            should_killswitch, ks_reason = self.risk_manager.check_risk_triggers(self.open_positions)
            if should_killswitch:
                logger.critical(f"[KILLSWITCH] Trigger detected: {ks_reason}")
                self.risk_manager.activate_kill_switch(ks_reason)
                return False, f"Kill-switch triggered: {ks_reason}"
            
            # Step 6: Execute trade
            logger.info("[PHASE3] Executing trade...")
            success, execution_result = self.executor.execute_trade_plan(trade_plan, dry_run=dry_run)
            
            if not success:
                logger.error(f"[PHASE3] Trade execution failed: {execution_result}")
                return False, execution_result
            
            position_id = execution_result
            logger.info(f"[PHASE3] Trade executed successfully, Position: {position_id}")
            
            # Step 7: Log completion
            logger.info(
                f"\n{'='*80}\n"
                f"[SUCCESS] Trade pipeline completed\n"
                f"Signal → Chain → Strategy → Risk Check → Execution → Position\n"
                f"{'='*80}\n"
            )
            
            return True, f"Trade executed with position {position_id}"
            
        except Exception as e:
            logger.error(f"[ORCHESTRATOR ERROR] {str(e)}", exc_info=True)
            return False, str(e)
    
    def monitor_positions(self) -> Dict:
        """
        Monitor all open positions and check for exits
        Called every minute
        
        Returns:
            Summary of monitoring results
        """
        try:
            logger.info(f"[MONITOR] Checking {len(self.open_positions)} open positions...")
            
            # Update position P&L
            for position in self.open_positions:
                self._update_position_pnl(position)
            
            # Check exit conditions (Phase 4)
            logger.info("[PHASE4] Checking exit conditions...")
            closed = self.exit_manager.check_and_execute_exits(self.open_positions)
            
            if closed:
                logger.info(f"[PHASE4] {len(closed)} positions closed")
                for closed_pos in closed:
                    logger.info(
                        f"  - {closed_pos.position_id}: {closed_pos.exit_reason}, "
                        f"PnL: Rs {closed_pos.pnl:.2f} ({closed_pos.pnl_percent:.2%})"
                    )
                    self.closed_positions.append(closed_pos)
                    self.open_positions.remove(next(
                        p for p in self.open_positions if p.position_id == closed_pos.position_id
                    ))
            
            # Update Greeks
            self.risk_manager.update_portfolio_greeks(self.open_positions)
            
            # Get volatility guidance
            underlyings = set(pos.symbol for pos in self.open_positions)
            for underlying in underlyings:
                iv_guidance = self.risk_manager.get_volatility_regime_guidance(underlying)
                logger.info(
                    f"[IV_REGIME] {underlying}: {iv_guidance['recommendation']} "
                    f"({iv_guidance['reason']})"
                )
            
            return {
                'open_positions': len(self.open_positions),
                'positions_closed': len(closed),
                'portfolio_greeks': self.risk_manager.portfolio_greeks,
                'daily_pnl': sum(pos.current_pnl for pos in self.open_positions)
            }
            
        except Exception as e:
            logger.error(f"[MONITOR ERROR] {str(e)}")
            return {}
    
    def generate_session_summary(self) -> Dict:
        """Generate trading session summary"""
        
        try:
            total_trades = len(self.closed_positions)
            wins = sum(1 for pos in self.closed_positions if pos.win)
            losses = total_trades - wins
            
            total_pnl = sum(pos.pnl for pos in self.closed_positions)
            total_pnl_open = sum(pos.current_pnl for pos in self.open_positions)
            
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
            profit_factor = (
                sum(pos.pnl for pos in self.closed_positions if pos.pnl > 0) /
                abs(sum(pos.pnl for pos in self.closed_positions if pos.pnl < 0))
                if any(pos.pnl < 0 for pos in self.closed_positions) else 0
            )
            
            summary = {
                'timestamp': datetime.now().isoformat(),
                'total_closed_trades': total_trades,
                'wins': wins,
                'losses': losses,
                'win_rate_percent': win_rate,
                'closed_pnl': total_pnl,
                'open_pnl': total_pnl_open,
                'total_pnl': total_pnl + total_pnl_open,
                'profit_factor': profit_factor,
                'open_positions': len(self.open_positions),
                'portfolio_greeks': self.risk_manager.portfolio_greeks
            }
            
            logger.info(
                f"\n{'='*80}\n"
                f"[SESSION SUMMARY]\n"
                f"Closed Trades: {total_trades} (W:{wins} L:{losses}, {win_rate:.1f}%)\n"
                f"Closed P&L: Rs {total_pnl:.2f}\n"
                f"Open P&L: Rs {total_pnl_open:.2f}\n"
                f"Total P&L: Rs {summary['total_pnl']:.2f}\n"
                f"Open Positions: {len(self.open_positions)}\n"
                f"Portfolio Greeks - Delta: {summary['portfolio_greeks']['delta']:.2f}, "
                f"Theta: {summary['portfolio_greeks']['theta']:.2f}\n"
                f"{'='*80}\n"
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"[SUMMARY ERROR] {str(e)}")
            return {}
    
    def _get_current_price(self, underlying: str) -> Optional[float]:
        """Get current price for underlying"""
        try:
            # Could fetch from Breeze or cache
            quote = self.breeze.get_quotes(exchange="NSE", scrip_code=underlying)
            if quote:
                return float(quote.get('LTP', 0))
        except Exception as e:
            logger.error(f"Error fetching price for {underlying}: {e}")
        return None
    
    def _update_position_pnl(self, position):
        """Update P&L for a position"""
        try:
            current_premium = self.exit_manager._get_current_premium(position)
            position.current_pnl = current_premium - position.entry_premium
            position.pnl_percent = (
                position.current_pnl / position.entry_premium
                if position.entry_premium != 0 else 0
            )
            position.current_price = current_premium
            
        except Exception as e:
            logger.error(f"Error updating position {position.position_id}: {e}")


# Example usage / Integration point
def integrate_with_scheduler():
    """
    Integration point with scheduler
    Called from schedule_hybrid_trading_monitored.py
    """
    
    logger.info("[ORCHESTRATOR] Initializing options trading orchestrator...")
    
    # Components already created elsewhere:
    # - breeze_client
    # - chain_manager (OptionsChainManager)
    # - strategy_selector (OptionsStrategySelector)
    # - executor (OptionsOrderExecutor)
    # - exit_manager (OptionsExitManager)
    # - risk_manager (OptionsRiskManager)
    # - portfolio_manager
    
    # Create orchestrator
    # orchestrator = OptionsTradeOrchestrator(
    #     breeze_client,
    #     chain_manager,
    #     strategy_selector,
    #     executor,
    #     exit_manager,
    #     risk_manager,
    #     portfolio_manager
    # )
    
    # Process signal each minute
    # signal = TradingSignal(
    #     underlying="RELIANCE",
    #     direction="BUY",
    #     confidence=0.72,
    #     expected_move_pct=3.2,
    #     timestamp=datetime.now()
    # )
    # success, message = orchestrator.process_signal(signal, dry_run=False)
    
    # Monitor positions every minute
    # summary = orchestrator.monitor_positions()
    
    # Daily summary
    # session_summary = orchestrator.generate_session_summary()
    
    pass
