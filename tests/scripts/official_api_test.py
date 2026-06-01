#!/usr/bin/env python3
"""
Official Breeze API Implementation
=================================

Complete implementation based on official ICICI Direct Breeze API documentation.
Uses correct endpoints, headers, and authentication as per documentation.
"""

import requests
import json
import hashlib
from datetime import datetime, timezone
import sys
import os

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

class OfficialBreezeAPI:
    """Official Breeze API implementation using documented endpoints and headers"""
    
    def __init__(self, api_key, secret_key, session_token, user_id):
        self.api_key = api_key
        self.secret_key = secret_key
        self.session_token = session_token
        self.user_id = user_id
        self.base_url = "https://api.icicidirect.com/breezeapi/api/v1"
        self.authenticated_session_token = None
        
    def generate_checksum(self, post_data="", timestamp=None):
        """Generate checksum as per API documentation: SHA256(timestamp + post_data + secret_key)"""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        # Convert post_data to string if it's a dict
        if isinstance(post_data, dict):
            post_data = json.dumps(post_data)
        
        # Create checksum string: timestamp + post_data + secret_key
        checksum_string = timestamp + post_data + self.secret_key
        
        # Generate SHA256 hash
        checksum = hashlib.sha256(checksum_string.encode()).hexdigest()
        
        return f"token {checksum}", timestamp
    
    def get_common_headers(self, post_data="", session_token=None):
        """Get common headers required for API calls"""
        checksum, timestamp = self.generate_checksum(post_data)
        
        headers = {
            "Content-Type": "application/json",
            "X-Checksum": checksum,
            "X-Timestamp": timestamp,
            "X-AppKey": self.api_key
        }
        
        # Add session token if available (not needed for customerdetails)
        if session_token:
            headers["X-SessionToken"] = session_token
            
        return headers
    
    def authenticate(self):
        """Authenticate using customerdetails endpoint (no headers required for this call)"""
        
        url = f"{self.base_url}/customerdetails"
        
        payload = {
            "SessionToken": self.session_token,
            "AppKey": self.api_key
        }
        
        # CustomerDetails API does not require headers according to documentation
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, json=payload, headers=headers, timeout=30)
            
            print(f"🔍 Authentication Request:")
            print(f"   URL: {url}")
            print(f"   Payload: {json.dumps(payload, indent=2)}")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if 'Success' in data and data['Success']:
                    success_data = data['Success']
                    self.authenticated_session_token = success_data.get('session_token')
                    
                    print(f"✅ Authentication successful!")
                    print(f"   User: {success_data.get('idirect_user_name', 'Unknown')}")
                    print(f"   User ID: {success_data.get('idirect_userid', 'Unknown')}")
                    print(f"   Session Token: {self.authenticated_session_token}")
                    print(f"   Trading: {success_data.get('segments_allowed', {}).get('Trading', 'Unknown')}")
                    print(f"   Equity: {success_data.get('segments_allowed', {}).get('Equity', 'Unknown')}")
                    
                    return True
                else:
                    print(f"❌ Authentication failed: {data.get('Error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def get_demat_holdings(self):
        """Get demat holdings using official endpoint"""
        
        if not self.authenticated_session_token:
            print("❌ Not authenticated. Call authenticate() first.")
            return None
        
        url = f"{self.base_url}/dematholdings"
        
        # Empty payload for GET request
        payload = {}
        
        headers = self.get_common_headers(payload, self.authenticated_session_token)
        
        try:
            print(f"\n📊 Getting Demat Holdings:")
            print(f"   URL: {url}")
            print(f"   Headers: {list(headers.keys())}")
            
            response = requests.get(url, json=payload, headers=headers, timeout=30)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS! Retrieved demat holdings")
                
                if 'Success' in data and isinstance(data['Success'], list):
                    holdings = data['Success']
                    print(f"   📈 Holdings count: {len(holdings)}")
                    
                    # Show first few holdings
                    for i, holding in enumerate(holdings[:3]):
                        print(f"   📋 {i+1}. {holding.get('stock_code', 'Unknown')} - {holding.get('quantity', 0)} shares")
                
                return data
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None
    
    def get_funds(self):
        """Get funds using official endpoint"""
        
        if not self.authenticated_session_token:
            print("❌ Not authenticated. Call authenticate() first.")
            return None
        
        url = f"{self.base_url}/funds"
        
        # Empty payload for GET request
        payload = {}
        
        headers = self.get_common_headers(payload, self.authenticated_session_token)
        
        try:
            print(f"\n💰 Getting Funds:")
            print(f"   URL: {url}")
            
            response = requests.get(url, json=payload, headers=headers, timeout=30)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS! Retrieved funds information")
                
                if 'Success' in data and isinstance(data['Success'], dict):
                    funds = data['Success']
                    print(f"   💳 Bank Account: {funds.get('bank_account', 'Unknown')}")
                    print(f"   💵 Total Balance: ₹{funds.get('total_bank_balance', 0):,.2f}")
                    print(f"   📊 Allocated Equity: ₹{funds.get('allocated_equity', 0):,.2f}")
                
                return data
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None
    
    def get_portfolio_positions(self):
        """Get portfolio positions using official endpoint"""
        
        if not self.authenticated_session_token:
            print("❌ Not authenticated. Call authenticate() first.")
            return None
        
        url = f"{self.base_url}/portfoliopositions"
        
        # Empty payload for GET request
        payload = {}
        
        headers = self.get_common_headers(payload, self.authenticated_session_token)
        
        try:
            print(f"\n📈 Getting Portfolio Positions:")
            print(f"   URL: {url}")
            
            response = requests.get(url, json=payload, headers=headers, timeout=30)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS! Retrieved portfolio positions")
                
                if 'Success' in data and isinstance(data['Success'], list):
                    positions = data['Success']
                    print(f"   📊 Positions count: {len(positions)}")
                    
                    # Show first few positions
                    for i, pos in enumerate(positions[:3]):
                        print(f"   📋 {i+1}. {pos.get('stock_code', 'Unknown')} - {pos.get('quantity', 0)} @ ₹{pos.get('average_price', 0)}")
                
                return data
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None
    
    def get_historical_charts(self, stock_code="ITC", exchange_code="NSE", interval="1day", days_back=7):
        """Get historical charts using official endpoint"""
        
        if not self.authenticated_session_token:
            print("❌ Not authenticated. Call authenticate() first.")
            return None
        
        url = f"{self.base_url}/historicalcharts"
        
        # Calculate date range
        to_date = datetime.now()
        from_date = datetime.now().replace(day=1)  # First day of current month
        
        payload = {
            "interval": interval,
            "from_date": from_date.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            "to_date": to_date.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            "stock_code": stock_code,
            "exchange_code": exchange_code,
            "product_type": "cash"
        }
        
        headers = self.get_common_headers(payload, self.authenticated_session_token)
        
        try:
            print(f"\n📊 Getting Historical Charts:")
            print(f"   URL: {url}")
            print(f"   Stock: {stock_code} ({exchange_code})")
            print(f"   Interval: {interval}")
            print(f"   From: {from_date.strftime('%Y-%m-%d')}")
            print(f"   To: {to_date.strftime('%Y-%m-%d')}")
            
            response = requests.get(url, json=payload, headers=headers, timeout=30)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS! Retrieved historical data")
                
                if 'Success' in data and isinstance(data['Success'], list):
                    candles = data['Success']
                    print(f"   📈 Candles count: {len(candles)}")
                    
                    # Show first few candles
                    for i, candle in enumerate(candles[:3]):
                        print(f"   📋 {i+1}. {candle.get('datetime', 'Unknown')} - O:{candle.get('open', 0)} H:{candle.get('high', 0)} L:{candle.get('low', 0)} C:{candle.get('close', 0)}")
                
                return data
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None
    
    def get_quotes(self, stock_code="ITC", exchange_code="NSE"):
        """Get live quotes using official endpoint"""
        
        if not self.authenticated_session_token:
            print("❌ Not authenticated. Call authenticate() first.")
            return None
        
        url = f"{self.base_url}/quotes"
        
        payload = {
            "stock_code": stock_code,
            "exchange_code": exchange_code,
            "expiry_date": "",
            "product_type": "cash",
            "right": "",
            "strike_price": ""
        }
        
        headers = self.get_common_headers(payload, self.authenticated_session_token)
        
        try:
            print(f"\n📊 Getting Live Quotes:")
            print(f"   URL: {url}")
            print(f"   Stock: {stock_code} ({exchange_code})")
            
            response = requests.get(url, json=payload, headers=headers, timeout=30)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS! Retrieved quotes")
                
                if 'Success' in data and isinstance(data['Success'], list):
                    quotes = data['Success']
                    print(f"   📈 Quotes count: {len(quotes)}")
                    
                    # Show quotes
                    for quote in quotes:
                        print(f"   💰 LTP: ₹{quote.get('ltp', 0)} | Open: ₹{quote.get('open', 0)} | High: ₹{quote.get('high', 0)} | Low: ₹{quote.get('low', 0)}")
                
                return data
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None

def test_official_api():
    """Test the official API implementation"""
    
    print("🚀 OFFICIAL BREEZE API TEST")
    print("=" * 50)
    
    try:
        from app.config import Config
        
        # Initialize API
        api = OfficialBreezeAPI(
            api_key=Config.BREEZE_API_KEY,
            secret_key=Config.BREEZE_SECRET_KEY,
            session_token=Config.BREEZE_SESSION_TOKEN,
            user_id=Config.BREEZE_USER_ID
        )
        
        # Step 1: Authenticate
        print("🔐 STEP 1: AUTHENTICATION")
        print("-" * 30)
        if not api.authenticate():
            return False
        
        # Step 2: Test data endpoints
        print(f"\n📊 STEP 2: DATA ENDPOINTS")
        print("-" * 30)
        
        # Test demat holdings
        holdings = api.get_demat_holdings()
        
        # Test funds
        funds = api.get_funds()
        
        # Test portfolio positions
        positions = api.get_portfolio_positions()
        
        # Test historical data
        historical = api.get_historical_charts("ITC", "NSE", "1day")
        
        # Test quotes
        quotes = api.get_quotes("ITC", "NSE")
        
        # Summary
        print(f"\n" + "="*50)
        print("🏁 OFFICIAL API TEST SUMMARY")
        print("="*50)
        
        print(f"✅ Authentication: SUCCESS")
        print(f"📊 Demat Holdings: {'SUCCESS' if holdings else 'FAILED'}")
        print(f"💰 Funds: {'SUCCESS' if funds else 'FAILED'}")
        print(f"📈 Portfolio Positions: {'SUCCESS' if positions else 'FAILED'}")
        print(f"📊 Historical Data: {'SUCCESS' if historical else 'FAILED'}")
        print(f"💰 Live Quotes: {'SUCCESS' if quotes else 'FAILED'}")
        
        success_count = sum([
            holdings is not None,
            funds is not None,
            positions is not None,
            historical is not None,
            quotes is not None
        ])
        
        print(f"\n🎯 SUCCESS RATE: {success_count}/5 ({success_count*20}%)")
        
        if success_count >= 3:
            print(f"\n🎉 EXCELLENT! Most endpoints working correctly!")
            print(f"   Your Breeze API credentials are valid and working.")
            print(f"   The trading system can now fetch data successfully.")
        else:
            print(f"\n⚠️  Some endpoints need attention, but authentication works!")
        
        return True
        
    except Exception as e:
        print(f"❌ Official API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        print("🧪 Starting official Breeze API test...")
        print(f"⏰ Time: {datetime.now()}")
        
        success = test_official_api()
        
        if success:
            print(f"\n🎉 TEST COMPLETED!")
        else:
            print(f"\n❌ TEST FAILED")
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Test script error: {e}")
        import traceback
        traceback.print_exc()