"""
Risk Management Service
Enhanced with Market Time Aware volatility adjustments
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from app.config import Config

logger = logging.getLogger(__name__)

class RiskManager:
    """Manages trading risks and position sizing"""
    
    def __init__(self):
        self.config = Config()
        self.daily_pnl = 0.0
        self.total_capital = self.config.DEFAULT_CAPITAL
        self.positions = {}
        self.daily_trades = []
        
    def validate_order(self, order_params: Dict) -> Tuple[bool, str]:
        """Validate order against risk parameters"""
        try:
            # Check daily loss limit
            if self.daily_pnl < 0 and abs(self.daily_pnl) >= (self.total_capital * self.config.MAX_DAILY_LOSS):
                return False, "Daily loss limit exceeded"
            
            # Check position size limits
            stock_code = order_params.get('stock_code')
            quantity = int(order_params.get('quantity', 0))
            price = float(order_params.get('price', 0))
            
            if quantity <= 0:
                return False, "Invalid quantity"
            
            position_value = quantity * price
            max_position_value = self.total_capital * self.config.MAX_POSITION_SIZE
            
            if position_value > max_position_value:
                return False, f"Position size exceeds limit. Max allowed: {max_position_value}"
            
            # Check if we already have a position in this stock
            current_position = self.positions.get(stock_code, {'quantity': 0, 'avg_price': 0})
            action = order_params.get('action', '').upper()
            
            if action == 'BUY':
                new_position_value = (current_position['quantity'] + quantity) * price
                if new_position_value > max_position_value:
                    return False, "Combined position size exceeds limit"
            
            return True, "Order validated successfully"
            
        except Exception as e:
            logger.error(f"Error validating order: {e}")
            return False, f"Validation error: {str(e)}"
    
    def calculate_stop_loss(self, entry_price: float, action: str, 
                           custom_sl_percent: Optional[float] = None) -> float:
        """
        Calculate stop-loss price with market-time aware volatility adjustment
        
        Adjusts stop loss wider during volatile market sessions (opening/closing bells)
        """
        try:
            # Import here to avoid circular imports
            from app.strategies.market_time_filter import MarketTimeFilter
            market_filter = MarketTimeFilter()
            
            sl_percent = custom_sl_percent or self.config.DEFAULT_STOP_LOSS
            
            # Adjust for market session volatility
            adjusted_sl = market_filter.apply_volatility_adjustment(sl_percent)
            
            if action.upper() == 'BUY':
                stop_loss = entry_price * (1 - adjusted_sl)
            else:  # SELL
                stop_loss = entry_price * (1 + adjusted_sl)
            
            # Log adjustment if different from base
            if adjusted_sl != sl_percent:
                session = market_filter.get_current_session()
                logger.info(
                    f"Stop loss adjusted for {session}: {sl_percent*100:.1f}% → {adjusted_sl*100:.1f}% "
                    f"(Entry: {entry_price:.2f}, Stop: {stop_loss:.2f})"
                )
            
            return round(stop_loss, 2)
            
        except Exception as e:
            logger.error(f"Error calculating stop loss: {e}")
            return entry_price
    
    def calculate_target(self, entry_price: float, action: str, 
                        custom_target_percent: Optional[float] = None) -> float:
        """Calculate target price"""
        try:
            target_percent = custom_target_percent or self.config.DEFAULT_TARGET
            
            if action.upper() == 'BUY':
                target = entry_price * (1 + target_percent)
            else:  # SELL
                target = entry_price * (1 - target_percent)
            
            return round(target, 2)
            
        except Exception as e:
            logger.error(f"Error calculating target: {e}")
            return entry_price
    
    def calculate_trailing_stop_loss(self, current_price: float, entry_price: float, 
                                   action: str, highest_price: float = None, 
                                   lowest_price: float = None) -> float:
        """Calculate trailing stop-loss price"""
        try:
            trailing_percent = self.config.TRAILING_STOP_LOSS
            
            if action.upper() == 'BUY':
                # For long positions, trail below the highest price
                reference_price = highest_price if highest_price else current_price
                trailing_sl = reference_price * (1 - trailing_percent)
                
                # Ensure trailing SL is not below original SL
                original_sl = self.calculate_stop_loss(entry_price, action)
                return max(trailing_sl, original_sl)
                
            else:  # SELL
                # For short positions, trail above the lowest price
                reference_price = lowest_price if lowest_price else current_price
                trailing_sl = reference_price * (1 + trailing_percent)
                
                # Ensure trailing SL is not above original SL
                original_sl = self.calculate_stop_loss(entry_price, action)
                return min(trailing_sl, original_sl)
            
        except Exception as e:
            logger.error(f"Error calculating trailing stop loss: {e}")
            return self.calculate_stop_loss(entry_price, action)
    
    def update_position(self, stock_code: str, action: str, quantity: int, 
                       price: float, order_id: str = None) -> None:
        """Update position after order execution"""
        try:
            if stock_code not in self.positions:
                self.positions[stock_code] = {
                    'quantity': 0,
                    'avg_price': 0,
                    'realized_pnl': 0,
                    'unrealized_pnl': 0,
                    'entry_time': datetime.now(),
                    'trades': []
                }
            
            position = self.positions[stock_code]
            
            if action.upper() == 'BUY':
                # Add to position
                total_value = (position['quantity'] * position['avg_price']) + (quantity * price)
                total_quantity = position['quantity'] + quantity
                
                if total_quantity > 0:
                    position['avg_price'] = total_value / total_quantity
                position['quantity'] = total_quantity
                
            else:  # SELL
                # Reduce position
                if position['quantity'] >= quantity:
                    # Calculate realized P&L
                    realized_pnl = quantity * (price - position['avg_price'])
                    position['realized_pnl'] += realized_pnl
                    self.daily_pnl += realized_pnl
                    
                    position['quantity'] -= quantity
                    
                    # Remove position if fully closed
                    if position['quantity'] == 0:
                        position['avg_price'] = 0
                else:
                    logger.warning(f"Insufficient quantity to sell for {stock_code}")
            
            # Record trade
            position['trades'].append({
                'action': action,
                'quantity': quantity,
                'price': price,
                'timestamp': datetime.now(),
                'order_id': order_id
            })
            
        except Exception as e:
            logger.error(f"Error updating position: {e}")
    
    def calculate_unrealized_pnl(self, stock_code: str, current_price: float) -> float:
        """Calculate unrealized P&L for a position"""
        try:
            if stock_code not in self.positions:
                return 0.0
            
            position = self.positions[stock_code]
            if position['quantity'] == 0:
                return 0.0
            
            unrealized_pnl = position['quantity'] * (current_price - position['avg_price'])
            position['unrealized_pnl'] = unrealized_pnl
            
            return unrealized_pnl
            
        except Exception as e:
            logger.error(f"Error calculating unrealized P&L: {e}")
            return 0.0
    
    def get_portfolio_metrics(self) -> Dict:
        """Get portfolio risk metrics"""
        try:
            total_unrealized_pnl = sum(pos['unrealized_pnl'] for pos in self.positions.values())
            total_realized_pnl = sum(pos['realized_pnl'] for pos in self.positions.values())
            total_pnl = total_realized_pnl + total_unrealized_pnl
            
            # Calculate position values
            total_position_value = 0
            for pos in self.positions.values():
                if pos['quantity'] > 0:
                    total_position_value += pos['quantity'] * pos['avg_price']
            
            # Calculate metrics
            portfolio_utilization = (total_position_value / self.total_capital) * 100
            return_percentage = (total_pnl / self.total_capital) * 100
            
            return {
                'total_capital': self.total_capital,
                'total_position_value': total_position_value,
                'portfolio_utilization': portfolio_utilization,
                'total_pnl': total_pnl,
                'realized_pnl': total_realized_pnl,
                'unrealized_pnl': total_unrealized_pnl,
                'return_percentage': return_percentage,
                'daily_pnl': self.daily_pnl,
                'positions_count': len([pos for pos in self.positions.values() if pos['quantity'] > 0]),
                'max_daily_loss': self.total_capital * self.config.MAX_DAILY_LOSS,
                'remaining_daily_loss': self.total_capital * self.config.MAX_DAILY_LOSS - abs(min(0, self.daily_pnl))
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {e}")
            return {}
    
    def check_risk_limits(self) -> Dict:
        """Check all risk limits and return warnings"""
        warnings = []
        
        try:
            # Check daily loss limit
            if self.daily_pnl < 0:
                loss_percentage = abs(self.daily_pnl) / self.total_capital
                if loss_percentage >= self.config.MAX_DAILY_LOSS * 0.8:  # 80% of limit
                    warnings.append(f"Daily loss approaching limit: {loss_percentage:.2%}")
                
                if loss_percentage >= self.config.MAX_DAILY_LOSS:
                    warnings.append("CRITICAL: Daily loss limit exceeded!")
            
            # Check position concentration
            for stock_code, position in self.positions.items():
                if position['quantity'] > 0:
                    position_value = position['quantity'] * position['avg_price']
                    concentration = position_value / self.total_capital
                    
                    if concentration > self.config.MAX_POSITION_SIZE:
                        warnings.append(f"Position {stock_code} exceeds size limit: {concentration:.2%}")
            
            return {
                'status': 'OK' if not warnings else 'WARNING',
                'warnings': warnings,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error checking risk limits: {e}")
            return {'status': 'ERROR', 'warnings': [str(e)]}
    
    def reset_daily_metrics(self):
        """Reset daily metrics (call at start of each trading day)"""
        self.daily_pnl = 0.0
        self.daily_trades = []
        logger.info("Daily risk metrics reset")
    
    def get_position_details(self, stock_code: str = None) -> Dict:
        """Get detailed position information"""
        try:
            if stock_code:
                return self.positions.get(stock_code, {})
            else:
                return self.positions
                
        except Exception as e:
            logger.error(f"Error getting position details: {e}")
            return {}