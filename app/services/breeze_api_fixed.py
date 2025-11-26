"""
Final Breeze API Service Fix
Addressing the 'appkey is empty' error for portfolio endpoints
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
    """Fixed Breeze API service with working portfolio endpoints"""
    
    def __init__(self):
        self.config = Config()
        self.api_key = self.config.BREEZE_API_KEY
        self.secret_key = self.config.BREEZE_SECRET_KEY
        self.session_token = self.config.BREEZE_SESSION_TOKEN
        self.user_id = self.config.BREEZE_USER_ID
        self.base_url = "https://api.icicidirect.com/breezeapi/api/v1"
        self.authenticated_session_token = None
        self.user_info = None
        self.is_connected = False
        
    def authenticate(self) -> Dict[str, Union[bool, str, Dict]]:
        """Authenticate with Breeze API using working implementation"""
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
                    
                    return {
                        'success': True,
                        'message': 'Authentication successful',
                        'data': {
                            'user_id': success_data.get('idirect_userid'),
                            'user_name': success_data.get('idirect_user_name'),
                            'session_token': self.authenticated_session_token,
                            'segments': success_data.get('segments_allowed', {}),
                            'last_login': success_data.get('idirect_lastlogin_time'),
                            **success_data  # Include all fields
                        }
                    }
                else:
                    return {
                        'success': False,
                        'message': f'Authentication failed: {data.get("Error", "Unknown error")}',
                        'data': data
                    }
            else:
                return {
                    'success': False,
                    'message': f'HTTP Error: {response.status_code}',
                    'data': response.text
                }
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {
                'success': False,
                'message': f'Authentication exception: {str(e)}',
                'data': None
            }
    
    def get_user_info(self) -> Dict:
        """Get user information from authenticated session"""
        if not self.is_connected or not self.user_info:
            return {'success': False, 'message': 'Not authenticated'}
        
        return {
            'success': True,
            'user_name': self.user_info.get('idirect_user_name', 'Unknown'),
            'user_id': self.user_info.get('idirect_userid', 'Unknown'),
            'trading_allowed': self.user_info.get('segments_allowed', {}).get('Trading', 'N') == 'Y',
            'equity_allowed': self.user_info.get('segments_allowed', {}).get('Equity', 'N') == 'Y',
            'derivatives_allowed': self.user_info.get('segments_allowed', {}).get('Derivatives', 'N') == 'Y',
            'last_login': self.user_info.get('idirect_lastlogin_time'),
            'session_token': self.authenticated_session_token
        }

    def _generate_checksum_fixed(self, payload: Dict) -> str:
        """Generate checksum with proper parameter handling for portfolio endpoints"""
        # Create checksum string from sorted parameters
        sorted_items = sorted(payload.items())
        checksum_string = ""
        
        for key, value in sorted_items:
            if key != "checksum":  # Don't include checksum in checksum calculation
                checksum_string += f"{key}={value}"
        
        # Generate SHA256 hash
        return hashlib.sha256(checksum_string.encode()).hexdigest()

    def get_portfolio_fixed(self) -> Dict:
        """Fixed portfolio retrieval with proper parameter format"""
        try:
            if not self.authenticated_session_token:
                return {'success': False, 'message': 'Not authenticated'}
            
            url = f"{self.base_url}/portfolioholdings"
            
            # Use form data approach instead of JSON
            payload = {
                "SessionToken": self.authenticated_session_token,
                "AppKey": self.api_key,
                "UserId": self.user_info.get('idirect_userid')
            }
            
            # Generate checksum
            checksum = self._generate_checksum_fixed(payload)
            payload["checksum"] = checksum
            
            # Try different request methods
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Use form data instead of JSON
            response = requests.post(url, data=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'Success' in data:
                        return {
                            'success': True,
                            'data': data['Success'],
                            'message': 'Portfolio retrieved successfully'
                        }
                    else:
                        return {
                            'success': False,
                            'message': f'API returned error: {data.get("Error", "Unknown error")}',
                            'raw_response': response.text
                        }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'message': 'Invalid JSON response',
                        'raw_response': response.text
                    }
            else:
                return {
                    'success': False,
                    'message': f'HTTP {response.status_code}: Portfolio retrieval failed',
                    'raw_response': response.text
                }
                
        except Exception as e:
            logger.error(f"Portfolio retrieval error: {str(e)}")
            return {
                'success': False,
                'message': f'Portfolio exception: {str(e)}'
            }

    def get_funds_fixed(self) -> Dict:
        """Fixed funds retrieval with proper parameter format"""
        try:
            if not self.authenticated_session_token:
                return {'success': False, 'message': 'Not authenticated'}
            
            url = f"{self.base_url}/funds"
            
            # Use form data approach
            payload = {
                "SessionToken": self.authenticated_session_token,
                "AppKey": self.api_key,
                "UserId": self.user_info.get('idirect_userid')
            }
            
            checksum = self._generate_checksum_fixed(payload)
            payload["checksum"] = checksum
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            response = requests.post(url, data=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'Success' in data:
                        return {
                            'success': True,
                            'data': data['Success'],
                            'message': 'Funds retrieved successfully'
                        }
                    else:
                        return {
                            'success': False,
                            'message': f'API returned error: {data.get("Error", "Unknown error")}',
                            'raw_response': response.text
                        }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'message': 'Invalid JSON response',
                        'raw_response': response.text
                    }
            else:
                return {
                    'success': False,
                    'message': f'HTTP {response.status_code}: Funds retrieval failed',
                    'raw_response': response.text
                }
                
        except Exception as e:
            logger.error(f"Funds retrieval error: {str(e)}")
            return {
                'success': False,
                'message': f'Funds exception: {str(e)}'
            }

    def get_quotes(self, stock_code: str, exchange_code: str = "NSE", product_type: str = "cash") -> Dict:
        """Get live quotes - WORKING METHOD"""
        try:
            if not self.authenticated_session_token:
                return {'success': False, 'message': 'Not authenticated'}
            
            url = f"{self.base_url}/quotes"
            
            payload = {
                "SessionToken": self.authenticated_session_token,
                "AppKey": self.api_key,
                "stock_code": stock_code,
                "exchange_code": exchange_code,
                "product_type": product_type
            }
            
            checksum = self._generate_checksum_fixed(payload)
            payload["checksum"] = checksum
            
            headers = {"Content-Type": "application/json"}
            response = requests.get(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'Success' in data:
                    return {
                        'success': True,
                        'data': data['Success'],
                        'message': f'Quotes retrieved for {stock_code}'
                    }
            
            return {
                'success': False,
                'message': f'Quotes retrieval failed: {response.text}',
                'status_code': response.status_code
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Quotes error: {str(e)}'
            }

    # Keep all other working methods from original implementation
    def _generate_checksum(self, payload: Dict) -> str:
        """Original checksum method for working endpoints"""
        sorted_items = sorted(payload.items())
        checksum_string = ""
        
        for key, value in sorted_items:
            if key != "checksum":
                checksum_string += f"{key}={value}"
        
        return hashlib.sha256(checksum_string.encode()).hexdigest()

    # Legacy methods for compatibility
    def get_portfolio(self) -> Dict:
        """Legacy portfolio method - redirects to fixed version"""
        return self.get_portfolio_fixed()
    
    def get_funds(self) -> Dict:
        """Legacy funds method - redirects to fixed version"""
        return self.get_funds_fixed()