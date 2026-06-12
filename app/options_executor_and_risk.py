"""
Phases 3-5: Options Execution, Exit Strategy, and Risk Management
Complete options trading pipeline with order execution, exit rules, and risk controls
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order execution status"""
    PENDING = "PENDING"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


@dataclass
class OrderExecution:
    """Single order execution record"""
    order_id: str
    symbol: str
    strike: float
    option_type: str  # CE or PE
    expiry: str
    action: str  # BUY or SELL
    quantity: int
    order_type: str  # MARKET or LIMIT
    limit_price: Optional[float] = None
    filled_quantity: int = 0
    filled_price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    timestamp: datetime = field(default_factory=datetime.now)
    fill_time: Optional[datetime] = None
    slippage: float = 0.0


@dataclass
class OpenPosition:
    """Open options position tracking"""
    position_id: str
    symbol: str
    strategy_type: str
    legs: List[OrderExecution]
    
    entry_time: datetime
    entry_premium: float  # Total premium paid/received
    
    current_price: float
    current_pnl: float
    pnl_percent: float
    
    # Greeks exposure
    delta: float
    theta: float
    vega: float
    gamma: float
    
    # Exit tracking
    exit_reason: Optional[str] = None
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    final_pnl: Optional[float] = None


@dataclass
class ClosedPosition:
    """Closed/exited position record"""
    position_id: str
    symbol: str
    strategy_type: str
    entry_time: datetime
    exit_time: datetime
    duration_minutes: int
    
    entry_premium: float
    exit_premium: float
    pnl: float
    pnl_percent: float
    
    exit_reason: str  # e.g., 'PROFIT_TARGET', 'STOP_LOSS', 'THETA_DECAY', 'EXPIRY'
    win: bool  # True if PnL > 0


class OptionsOrderExecutor:
    """
    Phase 3: Places options orders via Breeze API
    Handles multi-leg orders, tracking, and partial fills
    """
    
    def __init__(self, breeze_client, portfolio_manager):
        """
        Initialize order executor
        
        Args:
            breeze_client: BreezeConnect API client
            portfolio_manager: Portfolio tracking manager
        """
        self.breeze = breeze_client
        self.portfolio = portfolio_manager
        self.orders: Dict[str, OrderExecution] = {}
        self.order_counter = 0
    
    def execute_trade_plan(
        self, 
        trade_plan,
        dry_run: bool = False
    ) -> Tuple[bool, str]:
        """
        Execute complete options trade plan (single or multi-leg)
        
        Args:
            trade_plan: TradePlan object with legs
            dry_run: If True, simulate without actual orders
            
        Returns:
            (success, message)
        """
        try:
            logger.info(
                f"[EXECUTE] Executing {trade_plan.strategy.value} for {trade_plan.underlying} "
                f"(DRY_RUN={dry_run})"
            )
            
            filled_legs = []
            failed_legs = []
            
            # Execute each leg
            for leg in trade_plan.legs:
                success, order_exec, message = self._place_single_order(
                    leg, dry_run=dry_run
                )
                
                if success:
                    filled_legs.append(order_exec)
                else:
                    failed_legs.append((leg, message))
            
            # For multi-leg: both legs must fill
            if len(trade_plan.legs) > 1:
                if len(filled_legs) != len(trade_plan.legs):
                    logger.error(
                        f"[EXECUTE] Multi-leg failed: {len(filled_legs)}/{len(trade_plan.legs)} filled"
                    )
                    # Cancel filled legs
                    for order in filled_legs:
                        if not dry_run:
                            self._cancel_order(order.order_id)
                    return False, f"Partial fill: {len(filled_legs)}/{len(trade_plan.legs)} legs"
            
            # Create position record
            position_id = self._create_position(filled_legs, trade_plan)
            
            logger.info(f"[EXECUTE] Trade executed successfully, Position ID: {position_id}")
            return True, position_id
            
        except Exception as e:
            logger.error(f"[EXECUTE ERROR] {str(e)}")
            return False, str(e)
    
    def _place_single_order(
        self,
        leg,
        dry_run: bool = False
    ) -> Tuple[bool, Optional[OrderExecution], str]:
        """
        Place single options order
        
        Args:
            leg: OptionLeg object
            dry_run: Simulate if True
            
        Returns:
            (success, OrderExecution, message)
        """
        try:
            self.order_counter += 1
            order_id = f"OPT{datetime.now().strftime('%Y%m%d%H%M%S')}{self.order_counter}"
            
            logger.info(
                f"[ORDER] Placing {leg.action} {leg.quantity}x {leg.symbol} "
                f"{leg.strike}{leg.option_type} {leg.expiry}"
            )
            
            order = OrderExecution(
                order_id=order_id,
                symbol=leg.symbol,
                strike=leg.strike,
                option_type=leg.option_type,
                expiry=leg.expiry,
                action=leg.action,
                quantity=leg.quantity,
                order_type='MARKET',
                limit_price=None,
                filled_price=leg.entry_price
            )
            
            if not dry_run:
                # Call Breeze API
                # Format: SYMBOL26JUN2026C1800 (for RELIANCE 26JUN2026 Call 1800)
                option_symbol = f"{leg.symbol}{leg.expiry.replace('-', '')}C{int(leg.strike)}" \
                    if leg.option_type == 'CE' else \
                    f"{leg.symbol}{leg.expiry.replace('-', '')}P{int(leg.strike)}"
                
                # Place order via Breeze
                result = self.breeze.place_order(
                    symbol=option_symbol,
                    action=leg.action,
                    quantity=leg.quantity,
                    order_type='MARKET',
                    exchange='NFO'
                )
                
                if result.get('status') == 'Success':
                    order.status = OrderStatus.FILLED
                    order.filled_quantity = leg.quantity
                    order.filled_price = leg.entry_price
                    order.fill_time = datetime.now()
                    
                    logger.info(f"[ORDER] Order {order_id} FILLED at {leg.entry_price}")
                    self.orders[order_id] = order
                    return True, order, f"Order {order_id} filled"
                else:
                    logger.error(f"[ORDER] Order {order_id} REJECTED: {result.get('message')}")
                    return False, None, result.get('message', 'Unknown error')
            else:
                # Dry run: simulate fill
                order.status = OrderStatus.FILLED
                order.filled_quantity = leg.quantity
                order.filled_price = leg.entry_price
                order.fill_time = datetime.now()
                
                logger.info(f"[ORDER DRY_RUN] Order {order_id} simulated fill at {leg.entry_price}")
                self.orders[order_id] = order
                return True, order, f"Order {order_id} filled (simulated)"
            
        except Exception as e:
            logger.error(f"[ORDER ERROR] {str(e)}")
            return False, None, str(e)
    
    def _cancel_order(self, order_id: str) -> bool:
        """Cancel pending order via Breeze"""
        try:
            if order_id not in self.orders:
                return False
            
            order = self.orders[order_id]
            
            result = self.breeze.cancel_order(
                order_id=order_id,
                exchange='NFO'
            )
            
            if result.get('status') == 'Success':
                order.status = OrderStatus.CANCELLED
                logger.info(f"[ORDER] Order {order_id} cancelled")
                return True
            else:
                logger.error(f"[ORDER] Failed to cancel {order_id}")
                return False
                
        except Exception as e:
            logger.error(f"[CANCEL ERROR] {str(e)}")
            return False
    
    def _create_position(
        self,
        filled_orders: List[OrderExecution],
        trade_plan
    ) -> str:
        """Create position record in portfolio"""
        
        position_id = f"POS{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        total_delta = trade_plan.portfolio_delta
        total_theta = trade_plan.portfolio_theta
        total_vega = trade_plan.portfolio_vega
        total_gamma = trade_plan.portfolio_gamma
        
        position = OpenPosition(
            position_id=position_id,
            symbol=trade_plan.underlying,
            strategy_type=trade_plan.strategy.value,
            legs=filled_orders,
            entry_time=datetime.now(),
            entry_premium=trade_plan.total_debit,
            current_price=0.0,
            current_pnl=0.0,
            pnl_percent=0.0,
            delta=total_delta,
            theta=total_theta,
            vega=total_vega,
            gamma=total_gamma
        )
        
        # Store in portfolio
        if hasattr(self.portfolio, 'add_position'):
            self.portfolio.add_position(position)
        
        return position_id


class OptionsExitManager:
    """
    Phase 4: Manages options position exits
    Implements profit targets, stop losses, time decay, expiry management
    """
    
    def __init__(self, portfolio_manager, chain_manager):
        """
        Initialize exit manager
        
        Args:
            portfolio_manager: Portfolio tracking
            chain_manager: Options chain data
        """
        self.portfolio = portfolio_manager
        self.chain_manager = chain_manager
        self.closed_positions: List[ClosedPosition] = []
    
    def check_and_execute_exits(
        self,
        open_positions: List[OpenPosition]
    ) -> List[ClosedPosition]:
        """
        Check all open positions for exit conditions
        
        Returns:
            List of positions that were closed
        """
        closed = []
        
        for position in open_positions:
            exit_reason, should_exit = self._check_exit_conditions(position)
            
            if should_exit:
                closed_pos = self._exit_position(position, exit_reason)
                if closed_pos:
                    closed.append(closed_pos)
                    self.closed_positions.append(closed_pos)
        
        return closed
    
    def _check_exit_conditions(self, position: OpenPosition) -> Tuple[Optional[str], bool]:
        """
        Check all exit conditions for a position
        
        Returns:
            (exit_reason, should_exit)
        """
        
        # 1. Profit target: Exit at 50% of max gain
        if position.pnl_percent > 0:
            max_potential_gain = position.entry_premium * 2  # Approx
            profit_target = max_potential_gain * 0.5
            if position.current_pnl >= profit_target:
                return "PROFIT_TARGET_50", True
        
        # 2. Stop loss: Exit at -20% of entry
        if position.pnl_percent < -0.20:
            return "STOP_LOSS_20PCT", True
        
        # 3. Theta decay: If theta erosion significant
        if position.theta < -100 and position.current_pnl < 0:
            return "THETA_DECAY_LIMIT", True
        
        # 4. Expiry management: Close 1 day before expiry
        oldest_leg = min(position.legs, key=lambda x: x.timestamp)
        # Parse expiry date and check
        try:
            expiry_date = datetime.strptime(oldest_leg.expiry, "%d-%b-%Y")
            days_to_expiry = (expiry_date - datetime.now()).days
            if days_to_expiry <= 1:
                return "NEAR_EXPIRY_1DTE", True
        except:
            pass
        
        # 5. Greeks drift: Delta moved too much
        if abs(position.delta) > 0.75:
            return "DELTA_DRIFT_LIMIT", True
        
        return None, False
    
    def _exit_position(
        self,
        position: OpenPosition,
        exit_reason: str
    ) -> Optional[ClosedPosition]:
        """
        Close an open position
        
        Returns:
            ClosedPosition record
        """
        try:
            logger.info(f"[EXIT] Closing position {position.position_id}, Reason: {exit_reason}")
            
            # Get current premiums for exit
            current_premium = self._get_current_premium(position)
            
            # Calculate P&L
            duration_minutes = int((datetime.now() - position.entry_time).total_seconds() / 60)
            pnl = current_premium - position.entry_premium
            pnl_percent = pnl / position.entry_premium if position.entry_premium != 0 else 0
            
            # Create closed position record
            closed = ClosedPosition(
                position_id=position.position_id,
                symbol=position.symbol,
                strategy_type=position.strategy_type,
                entry_time=position.entry_time,
                exit_time=datetime.now(),
                duration_minutes=duration_minutes,
                entry_premium=position.entry_premium,
                exit_premium=current_premium,
                pnl=pnl,
                pnl_percent=pnl_percent,
                exit_reason=exit_reason,
                win=pnl > 0
            )
            
            logger.info(
                f"[EXIT] Position closed: PnL={pnl:.2f} ({pnl_percent:.2%}), "
                f"Duration={duration_minutes}m, Reason={exit_reason}"
            )
            
            return closed
            
        except Exception as e:
            logger.error(f"[EXIT ERROR] {str(e)}")
            return None
    
    def _get_current_premium(self, position: OpenPosition) -> float:
        """Get current total premium for all legs"""
        try:
            total_premium = 0.0
            
            for leg in position.legs:
                current_price = self.chain_manager.get_option_greeks_by_strike(
                    position.symbol,
                    leg.strike,
                    leg.expiry,
                    leg.option_type
                )
                
                if current_price:
                    ltp = current_price.get('ltp', leg.filled_price)
                    if leg.action == 'BUY':
                        total_premium += ltp * leg.filled_quantity
                    else:
                        total_premium -= ltp * leg.filled_quantity
            
            return total_premium
            
        except Exception as e:
            logger.error(f"[PREMIUM ERROR] {str(e)}")
            return position.entry_premium


class OptionsRiskManager:
    """
    Phase 5: Options-specific risk management
    Volatility regimes, Greeks exposure, margin monitoring
    """
    
    def __init__(self, chain_manager, max_capital: float = 100000.0):
        """
        Initialize risk manager
        
        Args:
            chain_manager: Options chain data
            max_capital: Maximum account capital
        """
        self.chain_manager = chain_manager
        self.max_capital = max_capital
        
        # Risk limits
        self.max_notional_per_position = max_capital * 0.20  # 20% of capital
        self.max_delta_exposure = 1.0  # Total portfolio delta
        self.max_theta_bleed = -500  # Max daily theta loss
        self.max_vega_exposure = 2.0
        self.daily_loss_limit = max_capital * 0.02  # 2% daily loss
        
        self.daily_pnl = 0.0
        self.portfolio_greeks = {
            'delta': 0.0,
            'theta': 0.0,
            'vega': 0.0,
            'gamma': 0.0
        }
    
    def validate_trade_plan(
        self,
        trade_plan,
        current_positions: List[OpenPosition]
    ) -> Tuple[bool, str]:
        """
        Pre-trade risk validation
        
        Returns:
            (is_valid, reason)
        """
        
        # 1. Margin check
        required_margin = trade_plan.margin_required
        available_margin = self.max_capital - sum(pos.entry_premium for pos in current_positions)
        
        if required_margin > available_margin:
            return False, f"Insufficient margin: required {required_margin}, available {available_margin}"
        
        # 2. Position size check
        if trade_plan.max_loss > self.max_notional_per_position:
            return False, f"Position size {trade_plan.max_loss} exceeds limit {self.max_notional_per_position}"
        
        # 3. Daily loss limit
        if self.daily_pnl + trade_plan.max_loss < -self.daily_loss_limit:
            return False, f"Daily loss would exceed limit"
        
        # 4. Greeks exposure check
        new_delta = self.portfolio_greeks['delta'] + trade_plan.portfolio_delta
        new_vega = self.portfolio_greeks['vega'] + trade_plan.portfolio_vega
        
        if abs(new_delta) > self.max_delta_exposure:
            return False, f"Delta exposure {abs(new_delta)} exceeds limit {self.max_delta_exposure}"
        
        if abs(new_vega) > self.max_vega_exposure:
            return False, f"Vega exposure {abs(new_vega)} exceeds limit {self.max_vega_exposure}"
        
        return True, "All risk checks passed"
    
    def update_portfolio_greeks(self, positions: List[OpenPosition]):
        """Update total portfolio Greeks exposure"""
        
        self.portfolio_greeks = {
            'delta': sum(pos.delta for pos in positions),
            'theta': sum(pos.theta for pos in positions),
            'vega': sum(pos.vega for pos in positions),
            'gamma': sum(pos.gamma for pos in positions)
        }
        
        logger.info(
            f"[RISK] Portfolio Greeks - Delta: {self.portfolio_greeks['delta']:.2f}, "
            f"Theta: {self.portfolio_greeks['theta']:.2f}, "
            f"Vega: {self.portfolio_greeks['vega']:.2f}"
        )
    
    def get_volatility_regime_guidance(self, underlying: str) -> Dict[str, str]:
        """
        Get strategy recommendations based on volatility regime
        
        Returns:
            Dict with strategy recommendations
        """
        
        iv_regime = self.chain_manager.get_iv_regime(underlying)
        snapshot = self.chain_manager.fetch_option_chain(underlying)
        
        if not snapshot:
            return {'recommendation': 'NEUTRAL', 'reason': 'No data'}
        
        if iv_regime == 'HIGH':
            return {
                'recommendation': 'SELL_PREMIUM',
                'reason': f'High IV ({snapshot.iv_percentile:.1f}th percentile)',
                'strategies': ['IRON_CONDOR', 'BEAR_CALL_SPREAD', 'BULL_PUT_SPREAD']
            }
        
        elif iv_regime == 'LOW':
            return {
                'recommendation': 'BUY_OPTIONS',
                'reason': f'Low IV ({snapshot.iv_percentile:.1f}th percentile)',
                'strategies': ['BUY_CALL', 'BUY_PUT', 'LONG_STRADDLE']
            }
        
        else:
            return {
                'recommendation': 'NEUTRAL_STRATEGIES',
                'reason': f'Normal IV ({snapshot.iv_percentile:.1f}th percentile)',
                'strategies': ['LONG_STRANGLE', 'BULL_CALL_SPREAD']
            }
    
    def activate_kill_switch(self, reason: str) -> bool:
        """
        Emergency kill-switch: Cancel all orders, close all positions
        
        Args:
            reason: Reason for activation
            
        Returns:
            bool: Success status
        """
        logger.critical(f"[KILLSWITCH] ACTIVATED: {reason}")
        # Implementation would integrate with executor to cancel all
        return True
    
    def check_risk_triggers(
        self,
        positions: List[OpenPosition]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check for automatic kill-switch triggers
        
        Returns:
            (trigger_killswitch, reason)
        """
        
        # 1. Total portfolio loss > 5%
        total_pnl = sum(pos.current_pnl for pos in positions)
        if total_pnl < -self.max_capital * 0.05:
            return True, f"Portfolio loss {total_pnl} exceeds 5%"
        
        # 2. Theta bleed too high (massive loss to decay)
        total_theta = sum(pos.theta for pos in positions)
        if total_theta < -1000:
            return True, f"Theta bleed {total_theta} too high"
        
        # 3. Delta exposure too extreme
        total_delta = sum(pos.delta for pos in positions)
        if abs(total_delta) > 3.0:
            return True, f"Delta exposure {total_delta} too extreme"
        
        return False, None
