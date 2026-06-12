"""
Breeze API Service for ICICIDirect Integration
Updated with working implementation - November 2025
"""
import requests
import json
import logging
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Union
from app.config import Config

logger = logging.getLogger(__name__)

class BreezeAPIService:
    """Production-ready Breeze API service for NON-PINS NRO account (algo trading)"""
    
    def __init__(self):
        """Initialize Breeze API service for NON-PINS NRO account"""
        self.config = Config()
        self.api_key = self.config.BREEZE_API_KEY
        self.secret_key = self.config.BREEZE_SECRET_KEY
        
        # Use single account configuration
        self.session_token = self.config.BREEZE_SESSION_TOKEN
        self.user_id = self.config.BREEZE_USER_ID
        self.password = self.config.BREEZE_PASSWORD
        
        self.base_url = "https://api.icicidirect.com/breezeapi/api/v1"
        self.authenticated_session_token = None
        self.user_info = None
        self.is_connected = False
        
        logger.info(f"BreezeAPIService initialized for NON-PINS NRO account (User: {self.user_id})")
    
    def login(self, user_id: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Union[bool, str, Dict]]:
        """Get login URL for obtaining session token.
        
        According to ICICI Direct Breeze API documentation, session tokens are obtained via web login:
        https://api.icicidirect.com/apiuser/login?api_key=YOUR_API_KEY
        
        This method provides instructions for obtaining a fresh session token.
        
        Returns:
            Dictionary with login URL and instructions
        """
        import urllib.parse
        
        try:
            # Encode API key for URL
            encoded_api_key = urllib.parse.quote_plus(self.api_key)
            login_url = f"https://api.icicidirect.com/apiuser/login?api_key={encoded_api_key}"
            
            logger.info("Session token should be obtained from web login")
            
            return {
                'success': True,
                'login_url': login_url,
                'instructions': 'Visit the login URL in your browser, authenticate, and copy the session token provided',
                'note': 'Session tokens expire after inactivity. Refresh them by visiting the login URL again.'
            }
            
        except Exception as e:
            logger.error(f"Login URL generation exception: {e}")
            return {'success': False, 'error': str(e)}
        
    def authenticate(self) -> Dict[str, Union[bool, str, Dict]]:
        """Authenticate with Breeze API using session token from web login"""
        try:
            url = f"{self.base_url}/customerdetails"
            
            payload = {
                "SessionToken": self.session_token,
                "AppKey": self.api_key
            }
            
            headers = {"Content-Type": "application/json"}
            
            response = requests.get(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'Success' in data and data['Success']:
                    success_data = data['Success']
                    self.authenticated_session_token = success_data.get('session_token')
                    self.user_info = success_data
                    self.is_connected = True
                    
                    logger.info(f"Successfully authenticated: {success_data.get('idirect_user_name', 'Unknown')}")
                    
                    return {
                        'success': True,
                        'user_name': success_data.get('idirect_user_name', 'Unknown'),
                        'user_id': success_data.get('idirect_userid', 'Unknown'),
                        'session_token': self.authenticated_session_token,
                        'segments': success_data.get('segments_allowed', {}),
                        'data': success_data
                    }
                else:
                    error_msg = data.get('Error', 'Unknown error')
                    logger.warning(f"Authentication failed with session token: {error_msg}")
                    
                    # If session token is invalid, provide login URL
                    if 'Resource not available' in error_msg or error_msg == 'Resource not available.':
                        logger.info("Session token may be expired. Get a fresh one from web login.")
                        login_info = self.login()
                        return {
                            'success': False, 
                            'error': error_msg,
                            'login_url': login_info.get('login_url'),
                            'instructions': login_info.get('instructions')
                        }
                    
                    return {'success': False, 'error': error_msg}
            else:
                error_msg = f'HTTP {response.status_code}: {response.text}'
                logger.error(f"Authentication HTTP error: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            logger.error(f"Authentication exception: {e}")
            return {'success': False, 'error': str(e)}
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.authenticated_session_token is not None
    
    def get_user_info(self) -> Dict:
        """Get authenticated user information"""
        if not self.is_authenticated():
            return {'success': False, 'error': 'Not authenticated'}
        
        return {
            'success': True,
            'user_name': self.user_info.get('idirect_user_name', 'Unknown'),
            'user_id': self.user_info.get('idirect_userid', 'Unknown'),
            'trading_allowed': self.user_info.get('segments_allowed', {}).get('Trading', 'N') == 'Y',
            'equity_allowed': self.user_info.get('segments_allowed', {}).get('Equity', 'N') == 'Y',
            'derivatives_allowed': self.user_info.get('segments_allowed', {}).get('Derivatives', 'N') == 'Y',
            'last_login': self.user_info.get('idirect_lastlogin_time', 'Unknown'),
            'session_token': self.authenticated_session_token
        }
    
    def generate_checksum(self, post_data: str = "") -> tuple:
        """Generate checksum for authenticated requests"""
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        # Handle different data types
        if isinstance(post_data, dict):
            # Always stringify dicts to JSON, even if empty
            post_data_str = json.dumps(post_data, separators=(',', ':'))
        else:
            post_data_str = str(post_data) if post_data else ""
        
        # Create checksum string: timestamp + post_data + secret_key
        checksum_string = timestamp + post_data_str + self.secret_key
        
        # Generate SHA256 hash
        checksum = hashlib.sha256(checksum_string.encode()).hexdigest()
        
        return f"token {checksum}", timestamp
    
    def get_headers(self, post_data: str = "") -> Dict[str, str]:
        """Get properly formatted headers for authenticated requests"""
        if not self.is_authenticated():
            return {"Content-Type": "application/json"}
        
        checksum, timestamp = self.generate_checksum(post_data)
        
        return {
            "Content-Type": "application/json",
            "X-Checksum": checksum,
            "X-Timestamp": timestamp,
            "X-AppKey": self.api_key,
            "X-SessionToken": self.authenticated_session_token
        }
    
    def get_customer_details(self) -> Dict:
        """Get customer details (returns authenticated user info)"""
        if not self.is_authenticated():
            auth_result = self.authenticate()
            if not auth_result['success']:
                return auth_result
        
        return self.get_user_info()
    
    def get_portfolio(self) -> Dict:
        """Get portfolio holdings using working implementation"""
        return self.get_demat_holdings()
    
    def get_demat_holdings(self) -> Dict:
        """Get demat holdings (working endpoint)"""
        if not self.is_authenticated():
            return {'success': False, 'error': 'Not authenticated'}
        
        try:
            url = f"{self.base_url}/dematholdings"
            
            # Send empty dict as payload
            payload = {}
            headers = self.get_headers(payload)
            
            response = requests.get(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'Success' in data:
                    logger.info("Successfully retrieved demat holdings")
                    return {'success': True, 'data': data['Success']}
                else:
                    error_msg = data.get('Error', 'Unknown error')
                    logger.error(f"Demat holdings error: {error_msg}")
                    return {'success': False, 'error': error_msg}
            else:
                error_msg = f'HTTP {response.status_code}: {response.text[:200]}'
                logger.error(f"Demat holdings HTTP error: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            logger.error(f"Demat holdings exception: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_portfolio_positions(self) -> Dict:
        """Get portfolio positions (working endpoint)"""
        if not self.is_authenticated():
            return {'success': False, 'error': 'Not authenticated'}
        
        try:
            url = f"{self.base_url}/portfoliopositions"
            
            # Send empty dict as payload
            payload = {}
            headers = self.get_headers(payload)
            
            response = requests.get(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'Success' in data:
                    logger.info("Successfully retrieved portfolio positions")
                    return {'success': True, 'data': data['Success']}
                else:
                    error_msg = data.get('Error', 'Unknown error')
                    logger.error(f"Portfolio positions error: {error_msg}")
                    return {'success': False, 'error': error_msg}
            else:
                error_msg = f'HTTP {response.status_code}: {response.text[:200]}'
                logger.error(f"Portfolio positions HTTP error: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            logger.error(f"Portfolio positions exception: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_funds(self, ucc: Optional[str] = None, demat: Optional[str] = None) -> Dict:
        """Get funds information (working endpoint)"""
        if not self.is_authenticated():
            return {'success': False, 'error': 'Not authenticated'}
        
        try:
            url = f"{self.base_url}/funds"
            # Build payload - always send as dict
            payload = {}
            if ucc:
                payload['ucc'] = ucc
            if demat:
                payload['demat'] = demat

            # Calculate headers with the payload
            headers = self.get_headers(payload)

            response = requests.get(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'Success' in data:
                    logger.info("Successfully retrieved funds information")
                    return {'success': True, 'data': data['Success']}
                else:
                    error_msg = data.get('Error', 'Unknown error')
                    logger.error(f"Funds error: {error_msg}")
                    return {'success': False, 'error': error_msg}
            else:
                error_msg = f'HTTP {response.status_code}: {response.text[:200]}'
                logger.error(f"Funds HTTP error: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            logger.error(f"Funds exception: {e}")
            return {'success': False, 'error': str(e)}

    def get_portfolio_holdings(self, exchange_code: str = "NFO", from_date: Optional[str] = None,
                               to_date: Optional[str] = None, stock_code: str = "", portfolio_type: str = "") -> Dict:
        """Get portfolio holdings (matches documentation)

        Parameters mirror the Breeze documentation sample:
          - exchange_code (e.g. 'NFO')
          - from_date / to_date in ISO format (e.g. '2024-08-01T06:00:00.000Z')
          - stock_code (optional)
          - portfolio_type (optional)
        """
        if not self.is_authenticated():
            return {'success': False, 'error': 'Not authenticated'}

        try:
            url = f"{self.base_url}/portfolioholdings"

            # Default date range = last 30 days if not provided
            now = datetime.utcnow()
            if to_date is None:
                to_date = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            if from_date is None:
                from_dt = now - timedelta(days=30)
                from_date = from_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')

            payload = {
                'exchange_code': exchange_code,
                'from_date': from_date,
                'to_date': to_date,
                'stock_code': stock_code,
                'portfolio_type': portfolio_type
            }

            # support optional account filters
            # under-specification: include ucc/demat if passed via kwargs in future calls
            # if caller passed 'ucc' or 'demat' as attributes on this instance or via kwargs, they'll be added by the caller

            # Headers include checksum/timestamp/session
            headers = self.get_headers(payload)

            response = requests.get(url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if 'Success' in data:
                    logger.info("Successfully retrieved portfolio holdings")
                    return {'success': True, 'data': data['Success']}
                else:
                    error_msg = data.get('Error', 'Unknown error')
                    logger.error(f"Portfolio holdings error: {error_msg}")
                    return {'success': False, 'error': error_msg, 'raw': data}
            else:
                error_msg = f'HTTP {response.status_code}: {response.text[:400]}'
                logger.error(f"Portfolio holdings HTTP error: {error_msg}")
                return {'success': False, 'error': error_msg, 'status_code': response.status_code, 'raw': response.text}

        except Exception as e:
            logger.error(f"Portfolio holdings exception: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_quotes(self, stock_code: str, exchange_code: str = "NSE", product_type: str = "cash") -> Dict:
        """Get live quotes"""
        # Validate inputs using validators module
        try:
            from app.services.validators import validate_quote_params
        except Exception:
            validate_quote_params = None

        params = {
            'stock_code': stock_code,
            'exchange_code': exchange_code,
            'product_type': product_type,
            'expiry_date': '',
            'strike_price': '',
            'right': '',
            'get_exchange_quotes': True,
            'get_market_depth': False,
            'interval': None
        }

        if validate_quote_params:
            ok, err = validate_quote_params(params)
            if not ok:
                return {'success': False, 'error': f'Invalid quote parameters: {err}'}

        if not self.is_authenticated():
            return {'success': False, 'error': 'Not authenticated'}
        
        try:
            url = f"{self.base_url}/quotes"
            
            payload = {
                "stock_code": stock_code,
                "exchange_code": exchange_code,
                "product_type": product_type,
                "expiry_date": "",
                "right": "",
                "strike_price": ""
            }
            
            # For GET requests with payload, calculate checksum with the payload
            headers = self.get_headers(payload)
            
            response = requests.get(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'Success' in data:
                    logger.info(f"Successfully retrieved quotes for {stock_code}")
                    return {'success': True, 'data': data['Success']}
                else:
                    error_msg = data.get('Error', 'Unknown error')
                    logger.error(f"Quotes error: {error_msg}")
                    return {'success': False, 'error': error_msg}
            else:
                error_msg = f'HTTP {response.status_code}: {response.text[:200]}'
                logger.error(f"Quotes HTTP error: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            logger.error(f"Quotes exception: {e}")
            return {'success': False, 'error': str(e)}
    
    def place_order(self, order_params: Dict) -> Dict:
        """Place an order using Breeze API"""
        if not self.is_authenticated():
            return {'success': False, 'error': 'Not authenticated'}
        
        try:
            url = f"{self.base_url}/order"
            
            # Map order parameters to Breeze format
            payload = {
                'stock_code': order_params.get('stock_code'),
                'exchange_code': order_params.get('exchange_code', 'NSE'),
                'product': order_params.get('product', 'cash'),
                'action': order_params.get('action').lower(),  # 'buy' or 'sell'
                'order_type': order_params.get('order_type', 'market').lower(),
                'quantity': str(order_params.get('quantity')),
                'price': str(order_params.get('price', '0')),
                'validity': order_params.get('validity', 'day').lower(),
                'disclosed_quantity': '0'
            }
            
            headers = self.get_headers(payload)
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'Success' in data:
                    logger.info(f"Successfully placed order for {order_params.get('stock_code')}")
                    return {'success': True, 'data': data['Success']}
                else:
                    error_msg = data.get('Error', 'Unknown error')
                    logger.error(f"Order placement error: {error_msg}")
                    return {'success': False, 'error': error_msg}
            else:
                error_msg = f'HTTP {response.status_code}: {response.text[:200]}'
                logger.error(f"Order placement HTTP error: {error_msg}")
                return {'success': False, 'error': error_msg}
            
        except Exception as e:
            logger.error(f"Order placement exception: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_order_list(self, exchange_code: str = "NSE") -> Dict:
        """Get list of orders"""
        if not self.is_authenticated():
            return {'success': False, 'error': 'Not authenticated'}
        
        try:
            url = f"{self.base_url}/order"
            
            # Get orders for today
            from_date = datetime.now().strftime("%Y-%m-%dT00:00:00.000Z")
            to_date = datetime.now().strftime("%Y-%m-%dT23:59:59.000Z")
            
            payload = {
                "exchange_code": exchange_code,
                "from_date": from_date,
                "to_date": to_date
            }
            
            headers = self.get_headers()
            
            response = requests.get(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'Success' in data:
                    logger.info("Successfully retrieved order list")
                    return {'success': True, 'data': data['Success']}
                else:
                    error_msg = data.get('Error', 'Unknown error')
                    logger.error(f"Order list error: {error_msg}")
                    return {'success': False, 'error': error_msg}
            else:
                error_msg = f'HTTP {response.status_code}: {response.text[:200]}'
                logger.error(f"Order list HTTP error: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            logger.error(f"Order list exception: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_trade_list(self, exchange_code: str = "NSE") -> Dict:
        """Get list of trades"""
        if not self.is_authenticated():
            return {'success': False, 'error': 'Not authenticated'}
        
        try:
            url = f"{self.base_url}/trades"
            
            # Get trades for today
            from_date = datetime.now().strftime("%Y-%m-%dT00:00:00.000Z")
            to_date = datetime.now().strftime("%Y-%m-%dT23:59:59.000Z")
            
            payload = {
                "exchange_code": exchange_code,
                "from_date": from_date,
                "to_date": to_date
            }
            
            headers = self.get_headers()
            
            response = requests.get(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'Success' in data:
                    logger.info("Successfully retrieved trade list")
                    return {'success': True, 'data': data['Success']}
                else:
                    error_msg = data.get('Error', 'Unknown error')
                    logger.error(f"Trade list error: {error_msg}")
                    return {'success': False, 'error': error_msg}
            else:
                error_msg = f'HTTP {response.status_code}: {response.text[:200]}'
                logger.error(f"Trade list HTTP error: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            logger.error(f"Trade list exception: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_historical_data(self, stock_code: str, exchange_code: str = "NSE", 
                          product_type: str = "cash", interval: str = "day", 
                          from_date: str = None, to_date: str = None,
                          days_back: int = None, expiry_date: str = None,
                          right: str = None, strike_price: str = None) -> Dict:
        """Get historical data for backtesting using Breeze API format
        
        Args:
            stock_code: Stock symbol (e.g., 'RELIND', 'NIFTY')
            exchange_code: 'NSE' for equity, 'NFO' for futures/options
            product_type: 'cash' for equity, 'futures' or 'options' for derivatives
            interval: 'minute', '5minute', '30minute', 'day' (NOT '1minute', '1day', etc.)
            from_date: ISO 8601 format (e.g., '2025-02-03T09:20:00.000Z'). Auto-calculated if days_back provided.
            to_date: ISO 8601 format (e.g., '2025-02-03T09:22:00.000Z'). Defaults to now.
            days_back: Alternative to from_date - number of days to go back
            expiry_date: For options/futures - expiry date (e.g., '2025-02-06T07:00:00.000Z')
            right: For options - 'call' or 'put'
            strike_price: For options - strike price value
        
        Returns:
            Dict with 'success' and 'data' keys
        """
        if not self.is_authenticated():
            return {'success': False, 'error': 'Not authenticated'}
        
        try:
            # Use v2 endpoint for better features (1second interval support)
            url = f"{self.base_url}/historicalcharts"
            
            # Calculate to_date if not provided
            if to_date is None:
                to_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            # Calculate from_date if not provided
            if from_date is None:
                days = days_back if days_back is not None else 30
                from_datetime = datetime.now() - timedelta(days=days)
                from_date = from_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            # Build payload based on product type
            payload = {
                "interval": interval,
                "from_date": from_date,
                "to_date": to_date,
                "stock_code": stock_code,
                "exchange_code": exchange_code,
                "product_type": product_type
            }
            
            # Add optional parameters for options/futures
            if expiry_date:
                payload["expiry_date"] = expiry_date
            if right:
                payload["right"] = right
            if strike_price:
                payload["strike_price"] = strike_price
            
            # Convert payload to JSON string for checksum calculation
            payload_json = json.dumps(payload, separators=(',', ':'))
            headers = self.get_headers(payload_json)
            
            response = requests.get(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'Success' in data and data['Success']:
                    logger.info(f"[OK] Successfully retrieved {len(data.get('Success', []))} bars for {stock_code} ({interval})")
                    return {'success': True, 'data': data['Success']}
                else:
                    error_msg = data.get('Error', 'No data returned')
                    logger.warning(f"[WARNING] Historical data response: {error_msg}")
                    return {'success': False, 'data': [], 'warning': error_msg}
            else:
                error_msg = f'HTTP {response.status_code}: {response.text[:300]}'
                logger.warning(f"[WARNING] Historical data endpoint error: {error_msg}")
                return {'success': False, 'data': [], 'error': error_msg}
                
        except Exception as e:
            logger.warning(f"⚠️ Historical data exception: {str(e)}")
            return {'success': False, 'data': [], 'error': str(e)}
    
    def get_margin(self, exchange_code: str = "NSE") -> Dict:
        """Get margin details"""
        if not self.is_authenticated():
            return {'success': False, 'error': 'Not authenticated'}
        
        try:
            url = f"{self.base_url}/margin"
            
            payload = {
                "exchange_code": exchange_code
            }
            
            headers = self.get_headers()
            
            response = requests.get(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'Success' in data:
                    logger.info("Successfully retrieved margin information")
                    return {'success': True, 'data': data['Success']}
                else:
                    error_msg = data.get('Error', 'Unknown error')
                    logger.error(f"Margin error: {error_msg}")
                    return {'success': False, 'error': error_msg}
            else:
                error_msg = f'HTTP {response.status_code}: {response.text[:200]}'
                logger.error(f"Margin HTTP error: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            logger.error(f"Margin exception: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_connection(self) -> bool:
        """Test connection to Breeze API"""
        try:
            response = requests.get(
                "https://api.icicidirect.com/breezeapi/documents/index.html",
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def disconnect(self):
        """Disconnect from Breeze API"""
        self.authenticated_session_token = None
        self.user_info = None
        self.is_connected = False
        logger.info("Disconnected from Breeze API")