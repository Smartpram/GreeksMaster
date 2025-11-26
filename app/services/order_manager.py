"""
Order Management Service
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from app.services.breeze_api import BreezeAPIService
from app.config import Config

logger = logging.getLogger(__name__)

class OrderManager:
    """Manages order execution and tracking"""
    
    def __init__(self, breeze_service: BreezeAPIService):
        self.breeze_service = breeze_service
        self.config = Config()
        self.pending_orders = {}
        self.executed_orders = {}
        
    def place_market_order(self, stock_code: str, action: str, quantity: int, 
                          exchange_code: str = "NSE", product: str = "CNC") -> Dict:
        """Place a market order"""
        try:
            order_params = {
                'stock_code': stock_code,
                'exchange_code': exchange_code,
                'product': product,
                'action': action.upper(),
                'order_type': 'MARKET',
                'quantity': quantity,
                'price': '0',
                'validity': 'DAY'
            }
            
            if self.config.PAPER_TRADING:
                return self._simulate_order(order_params)
            else:
                response = self.breeze_service.place_order(order_params)
                if response.get('Success'):
                    order_id = response['Result']['order_id']
                    self.pending_orders[order_id] = {
                        'order_params': order_params,
                        'timestamp': datetime.now(),
                        'status': 'PENDING'
                    }
                return response
                
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            return {'Success': False, 'Error': str(e)}
    
    def place_limit_order(self, stock_code: str, action: str, quantity: int, 
                         price: float, exchange_code: str = "NSE", 
                         product: str = "CNC") -> Dict:
        """Place a limit order"""
        try:
            order_params = {
                'stock_code': stock_code,
                'exchange_code': exchange_code,
                'product': product,
                'action': action.upper(),
                'order_type': 'LIMIT',
                'quantity': quantity,
                'price': str(price),
                'validity': 'DAY'
            }
            
            if self.config.PAPER_TRADING:
                return self._simulate_order(order_params)
            else:
                response = self.breeze_service.place_order(order_params)
                if response.get('Success'):
                    order_id = response['Result']['order_id']
                    self.pending_orders[order_id] = {
                        'order_params': order_params,
                        'timestamp': datetime.now(),
                        'status': 'PENDING'
                    }
                return response
                
        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            return {'Success': False, 'Error': str(e)}
    
    def place_stop_loss_order(self, stock_code: str, action: str, quantity: int, 
                             price: float, trigger_price: float, 
                             exchange_code: str = "NSE", product: str = "CNC") -> Dict:
        """Place a stop-loss order"""
        try:
            order_params = {
                'stock_code': stock_code,
                'exchange_code': exchange_code,
                'product': product,
                'action': action.upper(),
                'order_type': 'STOPLOSS',
                'quantity': quantity,
                'price': str(price),
                'stoploss': str(trigger_price),
                'validity': 'DAY'
            }
            
            if self.config.PAPER_TRADING:
                return self._simulate_order(order_params)
            else:
                response = self.breeze_service.place_order(order_params)
                if response.get('Success'):
                    order_id = response['Result']['order_id']
                    self.pending_orders[order_id] = {
                        'order_params': order_params,
                        'timestamp': datetime.now(),
                        'status': 'PENDING'
                    }
                return response
                
        except Exception as e:
            logger.error(f"Error placing stop-loss order: {e}")
            return {'Success': False, 'Error': str(e)}
    
    def place_bracket_order(self, stock_code: str, action: str, quantity: int,
                           entry_price: float, target_price: float, 
                           stop_loss_price: float, exchange_code: str = "NSE") -> Dict:
        """Place a bracket order with target and stop-loss"""
        try:
            # Place main order
            main_order = self.place_limit_order(
                stock_code=stock_code,
                action=action,
                quantity=quantity,
                price=entry_price,
                exchange_code=exchange_code,
                product="MIS"  # Intraday for bracket orders
            )
            
            if not main_order.get('Success'):
                return main_order
            
            # Place target order (opposite direction)
            target_action = "SELL" if action.upper() == "BUY" else "BUY"
            target_order = self.place_limit_order(
                stock_code=stock_code,
                action=target_action,
                quantity=quantity,
                price=target_price,
                exchange_code=exchange_code,
                product="MIS"
            )
            
            # Place stop-loss order
            stop_loss_order = self.place_stop_loss_order(
                stock_code=stock_code,
                action=target_action,
                quantity=quantity,
                price=stop_loss_price,
                trigger_price=stop_loss_price,
                exchange_code=exchange_code,
                product="MIS"
            )
            
            return {
                'Success': True,
                'Result': {
                    'main_order': main_order,
                    'target_order': target_order,
                    'stop_loss_order': stop_loss_order
                }
            }
            
        except Exception as e:
            logger.error(f"Error placing bracket order: {e}")
            return {'Success': False, 'Error': str(e)}
    
    def modify_order(self, order_id: str, **kwargs) -> Dict:
        """Modify an existing order"""
        try:
            if self.config.PAPER_TRADING:
                return self._simulate_modify_order(order_id, **kwargs)
            else:
                return self.breeze_service.modify_order(order_id, kwargs)
                
        except Exception as e:
            logger.error(f"Error modifying order: {e}")
            return {'Success': False, 'Error': str(e)}
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order"""
        try:
            if self.config.PAPER_TRADING:
                return self._simulate_cancel_order(order_id)
            else:
                response = self.breeze_service.cancel_order(order_id)
                if response.get('Success') and order_id in self.pending_orders:
                    self.pending_orders[order_id]['status'] = 'CANCELLED'
                return response
                
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return {'Success': False, 'Error': str(e)}
    
    def get_orders(self, exchange_code: str = "NSE") -> List[Dict]:
        """Get list of orders"""
        try:
            if self.config.PAPER_TRADING:
                return list(self.pending_orders.values()) + list(self.executed_orders.values())
            else:
                response = self.breeze_service.get_order_list(exchange_code)
                return response.get('Result', [])
                
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return []
    
    def get_trades(self, exchange_code: str = "NSE") -> List[Dict]:
        """Get list of executed trades"""
        try:
            if self.config.PAPER_TRADING:
                return list(self.executed_orders.values())
            else:
                response = self.breeze_service.get_trade_list(exchange_code)
                return response.get('Result', [])
                
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return []
    
    def _simulate_order(self, order_params: Dict) -> Dict:
        """Simulate order execution for paper trading"""
        import uuid
        
        order_id = str(uuid.uuid4())
        
        # Simulate immediate execution for market orders
        if order_params['order_type'] == 'MARKET':
            self.executed_orders[order_id] = {
                'order_id': order_id,
                'order_params': order_params,
                'timestamp': datetime.now(),
                'status': 'EXECUTED',
                'executed_price': 0,  # Would be current market price
                'executed_quantity': order_params['quantity']
            }
            
            logger.info(f"Paper trade executed: {order_params}")
            
        else:
            self.pending_orders[order_id] = {
                'order_id': order_id,
                'order_params': order_params,
                'timestamp': datetime.now(),
                'status': 'PENDING'
            }
        
        return {
            'Success': True,
            'Result': {
                'order_id': order_id,
                'message': 'Order placed successfully (Paper Trading)'
            }
        }
    
    def _simulate_modify_order(self, order_id: str, **kwargs) -> Dict:
        """Simulate order modification for paper trading"""
        if order_id in self.pending_orders:
            self.pending_orders[order_id]['order_params'].update(kwargs)
            return {'Success': True, 'Result': {'message': 'Order modified (Paper Trading)'}}
        else:
            return {'Success': False, 'Error': 'Order not found'}
    
    def _simulate_cancel_order(self, order_id: str) -> Dict:
        """Simulate order cancellation for paper trading"""
        if order_id in self.pending_orders:
            self.pending_orders[order_id]['status'] = 'CANCELLED'
            return {'Success': True, 'Result': {'message': 'Order cancelled (Paper Trading)'}}
        else:
            return {'Success': False, 'Error': 'Order not found'}
    
    def calculate_position_size(self, capital: float, risk_per_trade: float, 
                               entry_price: float, stop_loss_price: float) -> int:
        """Calculate position size based on risk management"""
        try:
            risk_amount = capital * risk_per_trade
            price_risk = abs(entry_price - stop_loss_price)
            
            if price_risk == 0:
                return 0
                
            position_size = int(risk_amount / price_risk)
            
            # Apply maximum position size limit
            max_position_value = capital * self.config.MAX_POSITION_SIZE
            max_quantity = int(max_position_value / entry_price)
            
            return min(position_size, max_quantity)
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0