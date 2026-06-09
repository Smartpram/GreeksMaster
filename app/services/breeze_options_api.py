"""
Breeze Options API Service
==========================

Specialized API service for options trading on NON-PINS NRO account

Features:
- Options order placement (buy/sell calls and puts)
- Options position tracking
- Options portfolio management
- Greeks calculation integration
- Options-specific data retrieval
"""

import requests
import json
import logging
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Union
from app.config import Config

logger = logging.getLogger(__name__)


class BreezOptionsAPIService:
    """Options-focused Breeze API service"""
    
    def __init__(self):
        """Initialize Options API service"""
        self.config = Config()
        self.api_key = self.config.BREEZE_API_KEY
        self.secret_key = self.config.BREEZE_SECRET_KEY
        self.session_token = self.config.BREEZE_SESSION_TOKEN
        self.user_id = self.config.BREEZE_USER_ID
        self.password = self.config.BREEZE_PASSWORD
        
        self.base_url = "https://api.icicidirect.com/breezeapi/api/v1"
        self.is_connected = False
        
        logger.info(f"Breeze Options API Service initialized for NON-PINS NRO account (User: {self.user_id})")
    
    def get_headers(self) -> Dict[str, str]:
        """Generate request headers with checksum authentication"""
        try:
            checksum_string = self.user_id + self.session_token + self.secret_key
            checksum = hashlib.sha256(checksum_string.encode()).hexdigest()
            
            headers = {
                'Authorization': f'{self.user_id}:{self.session_token}:{checksum}',
                'Content-Type': 'application/json',
                'X-API-Key': self.api_key
            }
            return headers
        except Exception as e:
            logger.error(f"Error generating headers: {e}")
            return {}
    
    def authenticate(self) -> Dict:
        """Authenticate with Breeze API"""
        try:
            url = f"{self.base_url}/login"
            headers = self.get_headers()
            
            payload = {
                'userId': self.user_id,
                'password': self.password,
                'appId': 'BREEZE'
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('Status') == 200:
                    self.is_connected = True
                    user_info = data.get('Success', {})
                    logger.info(f"✓ Authentication successful: {user_info.get('name', 'User')}")
                    return {'success': True, 'user': user_info}
                else:
                    logger.error(f"Authentication failed: {data.get('Error')}")
                    return {'success': False, 'error': data.get('Error')}
            else:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                return {'success': False, 'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {'success': False, 'error': str(e)}
    
    # ========================================================================
    # OPTIONS ORDER PLACEMENT
    # ========================================================================
    
    def place_options_order(self, symbol: str, strike: float, option_type: str,
                           expiry_date: str, quantity: int, price: float,
                           order_type: str = 'REGULAR', product_type: str = 'MIS',
                           side: str = 'BUY') -> Dict:
        """
        Place an options order
        
        Args:
            symbol: Option underlying (NIFTY, BANKNIFTY, etc.)
            strike: Strike price
            option_type: 'CALL' or 'PUT'
            expiry_date: Expiry date (YYYY-MM-DD or DDMMMYY format)
            quantity: Number of contracts (1 contract = 100 shares)
            price: Premium price
            order_type: 'REGULAR' or 'MARKET'
            product_type: 'MIS', 'CNC', 'NRML'
            side: 'BUY' or 'SELL'
            
        Returns:
            Order response with order ID
        """
        try:
            # Format expiry: NSE uses DDMMMYY format for options
            if len(expiry_date) == 10:  # YYYY-MM-DD
                exp_obj = datetime.strptime(expiry_date, '%Y-%m-%d')
                expiry_formatted = exp_obj.strftime('%d%b%y').upper()
            else:
                expiry_formatted = expiry_date.upper()
            
            # Construct symbol for NFO (National Futures and Options)
            # Format: NIFTY22JUN9100CE (underlying+expiry+strike+type)
            option_symbol = f"{symbol}{expiry_formatted}{int(strike)}{option_type[0]}"
            
            url = f"{self.base_url}/placeOrder"
            headers = self.get_headers()
            
            payload = {
                'symbol': option_symbol,
                'quantity': quantity,
                'price': price,
                'side': side,
                'orderType': order_type,
                'productType': product_type,
                'exchange': 'NFO',  # National Futures and Options
                'disclosedQuantity': 0,
                'validity': 'DAY'
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('Status') == 200:
                    order_id = data.get('Success', {})
                    logger.info(f"✓ Order placed: {option_symbol} {side} {quantity} @ ₹{price} | Order ID: {order_id}")
                    return {'success': True, 'order_id': order_id, 'symbol': option_symbol}
                else:
                    logger.error(f"Order placement failed: {data.get('Error')}")
                    return {'success': False, 'error': data.get('Error')}
            else:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                return {'success': False, 'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {'success': False, 'error': str(e)}
    
    def buy_call(self, symbol: str, strike: float, expiry: str, 
                quantity: int, price: float) -> Dict:
        """Shorthand: Buy a call option"""
        return self.place_options_order(symbol, strike, 'CALL', expiry, quantity, price, side='BUY')
    
    def buy_put(self, symbol: str, strike: float, expiry: str,
               quantity: int, price: float) -> Dict:
        """Shorthand: Buy a put option"""
        return self.place_options_order(symbol, strike, 'PUT', expiry, quantity, price, side='BUY')
    
    def sell_call(self, symbol: str, strike: float, expiry: str,
                 quantity: int, price: float) -> Dict:
        """Shorthand: Sell a call option"""
        return self.place_options_order(symbol, strike, 'CALL', expiry, quantity, price, side='SELL')
    
    def sell_put(self, symbol: str, strike: float, expiry: str,
                quantity: int, price: float) -> Dict:
        """Shorthand: Sell a put option"""
        return self.place_options_order(symbol, strike, 'PUT', expiry, quantity, price, side='SELL')
    
    # ========================================================================
    # OPTIONS PORTFOLIO
    # ========================================================================
    
    def get_portfolio_positions(self) -> Optional[Dict]:
        """Get current options positions"""
        try:
            url = f"{self.base_url}/positions"
            headers = self.get_headers()
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('Status') == 200:
                    positions = data.get('Success', [])
                    
                    # Filter for options only (NFO exchange)
                    options_positions = [
                        pos for pos in (positions if isinstance(positions, list) else [])
                        if 'NFO' in str(pos.get('exchange', '')) or 'CE' in str(pos.get('symbol', '')) or 'PE' in str(pos.get('symbol', ''))
                    ]
                    
                    logger.info(f"✓ Retrieved {len(options_positions)} options positions")
                    return options_positions
                else:
                    logger.warning(f"Error: {data.get('Error')}")
                    return None
            else:
                logger.warning(f"HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return None
    
    def get_order_list(self, symbol: Optional[str] = None) -> Optional[List[Dict]]:
        """Get list of options orders"""
        try:
            url = f"{self.base_url}/orderList"
            headers = self.get_headers()
            
            payload = {}
            if symbol:
                payload['symbol'] = symbol
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('Status') == 200:
                    orders = data.get('Success', [])
                    logger.info(f"✓ Retrieved {len(orders)} orders")
                    return orders
                else:
                    logger.warning(f"Error: {data.get('Error')}")
                    return None
            else:
                logger.warning(f"HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return None
    
    def get_option_chain(self, symbol: str, expiry_date: str) -> Optional[List[Dict]]:
        """Get option chain for a symbol and expiry"""
        try:
            url = f"{self.base_url}/optionChain"
            headers = self.get_headers()
            
            payload = {
                'symbol': symbol,
                'expiryDate': expiry_date
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('Status') == 200:
                    chain = data.get('Success', [])
                    logger.info(f"✓ Retrieved option chain: {symbol} {expiry_date}")
                    return chain
                else:
                    logger.warning(f"Error: {data.get('Error')}")
                    return None
            else:
                logger.warning(f"HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching option chain: {e}")
            return None
    
    # ========================================================================
    # PORTFOLIO ANALYTICS
    # ========================================================================
    
    def get_options_pnl(self) -> Dict:
        """Calculate P&L for all options positions"""
        positions = self.get_portfolio_positions()
        
        if not positions:
            return {'total_pnl': 0, 'positions': []}
        
        total_pnl = 0
        position_pnls = []
        
        for pos in positions:
            symbol = pos.get('symbol', '')
            quantity = int(pos.get('quantity', 0))
            entry_price = float(pos.get('limitPrice', pos.get('price', 0)))
            current_price = float(pos.get('lastPrice', entry_price))
            
            # For options, calculate per-share P&L
            pnl_per_share = (current_price - entry_price)
            total_position_pnl = pnl_per_share * quantity * 100  # 1 option = 100 shares
            
            total_pnl += total_position_pnl
            position_pnls.append({
                'symbol': symbol,
                'quantity': quantity,
                'entry_price': entry_price,
                'current_price': current_price,
                'pnl': total_position_pnl
            })
        
        logger.info(f"✓ Total Options P&L: ₹{total_pnl:,.0f}")
        
        return {
            'total_pnl': total_pnl,
            'positions': position_pnls
        }
    
    def get_options_summary(self) -> Dict:
        """Get summary of options portfolio"""
        positions = self.get_portfolio_positions()
        
        if not positions:
            return {
                'active_positions': 0,
                'calls': 0,
                'puts': 0,
                'total_premium': 0,
                'positions': []
            }
        
        calls = [p for p in positions if 'CE' in str(p.get('symbol', ''))]
        puts = [p for p in positions if 'PE' in str(p.get('symbol', ''))]
        
        total_premium = sum(
            float(p.get('price', 0)) * int(p.get('quantity', 0)) * 100
            for p in positions
        )
        
        return {
            'active_positions': len(positions),
            'calls': len(calls),
            'puts': len(puts),
            'total_premium': total_premium,
            'positions': positions
        }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Initialize service
    api = BreezOptionsAPIService()
    
    # Authenticate
    auth_result = api.authenticate()
    print(f"Authentication: {auth_result}")
    
    if auth_result.get('success'):
        # Get portfolio summary
        summary = api.get_options_summary()
        print(f"\nOptions Portfolio Summary:")
        print(f"Active Positions: {summary['active_positions']}")
        print(f"Calls: {summary['calls']}")
        print(f"Puts: {summary['puts']}")
        print(f"Total Premium at Risk: ₹{summary['total_premium']:,.0f}")
