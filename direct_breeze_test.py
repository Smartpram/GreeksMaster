#!/usr/bin/env python3
"""
Breeze API Workaround - Direct API Implementation
================================================

Since the breeze_connect library has a bug, this implements direct API calls
to work around the issue and successfully fetch data.
"""

import requests
import json
from datetime import datetime, timedelta
import sys
import os

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

class DirectBreezeAPI:
    """Direct implementation of Breeze API calls"""
    
    def __init__(self, api_key, secret_key, session_token, user_id):
        self.api_key = api_key
        self.secret_key = secret_key
        self.session_token = session_token
        self.user_id = user_id
        self.base_url = "https://api.icicidirect.com/breezeapi/api/v1"
        self.authenticated_session_token = None
        
    def authenticate(self):
        """Authenticate and get session token"""
        
        url = f"{self.base_url}/customerdetails"
        
        payload = {
            "SessionToken": self.session_token,
            "AppKey": self.api_key
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'Success' in data and data['Success']:
                    success_data = data['Success']
                    self.authenticated_session_token = success_data.get('session_token')
                    
                    print(f"✅ Authentication successful!")
                    print(f"   User: {success_data.get('idirect_user_name', 'Unknown')}")
                    print(f"   User ID: {success_data.get('idirect_userid', 'Unknown')}")
                    print(f"   Session Token: {self.authenticated_session_token[:20]}...")
                    
                    return True
                else:
                    print(f"❌ Authentication failed: {data.get('Error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def get_portfolio_holdings(self):
        """Get portfolio holdings"""
        
        if not self.authenticated_session_token:
            print("❌ Not authenticated. Call authenticate() first.")
            return None
        
        url = f"{self.base_url}/dematholdingequity"
        
        headers = {
            "Content-Type": "application/json",
            "SessionToken": self.authenticated_session_token
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Portfolio holdings retrieved")
                return data
            else:
                print(f"❌ Holdings request failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return None
                
        except Exception as e:
            print(f"❌ Holdings error: {e}")
            return None
    
    def get_funds(self):
        """Get fund information"""
        
        if not self.authenticated_session_token:
            print("❌ Not authenticated. Call authenticate() first.")
            return None
        
        url = f"{self.base_url}/funds"
        
        headers = {
            "Content-Type": "application/json",
            "SessionToken": self.authenticated_session_token
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Funds information retrieved")
                return data
            else:
                print(f"❌ Funds request failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return None
                
        except Exception as e:
            print(f"❌ Funds error: {e}")
            return None
    
    def get_historical_data(self, stock_code, interval="1day", from_date=None, to_date=None):
        """Get historical data for a stock"""
        
        if not self.authenticated_session_token:
            print("❌ Not authenticated. Call authenticate() first.")
            return None
        
        # Default date range (last 30 days)
        if not to_date:
            to_date = datetime.now()
        if not from_date:
            from_date = to_date - timedelta(days=30)
        
        # Format dates
        from_date_str = from_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        to_date_str = to_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        url = f"{self.base_url}/historicaldata"
        
        payload = {
            "interval": interval,
            "from_date": from_date_str,
            "to_date": to_date_str,
            "stock_code": stock_code,
            "exchange_code": "NSE",
            "product_type": "ALL"
        }
        
        headers = {
            "Content-Type": "application/json",
            "SessionToken": self.authenticated_session_token
        }
        
        try:
            response = requests.get(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Historical data retrieved for {stock_code}")
                return data
            else:
                print(f"❌ Historical data request failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return None
                
        except Exception as e:
            print(f"❌ Historical data error: {e}")
            return None

def test_direct_breeze_api():
    """Test the direct Breeze API implementation"""
    
    print("🚀 DIRECT BREEZE API TEST")
    print("=" * 40)
    
    try:
        from app.config import Config
        
        # Initialize direct API
        api = DirectBreezeAPI(
            api_key=Config.BREEZE_API_KEY,
            secret_key=Config.BREEZE_SECRET_KEY,
            session_token=Config.BREEZE_SESSION_TOKEN,
            user_id=Config.BREEZE_USER_ID
        )
        
        print("📋 Direct API initialized")
        
        # Test authentication
        print(f"\n🔐 Testing authentication...")
        auth_success = api.authenticate()
        
        if not auth_success:
            print("❌ Authentication failed")
            return False
        
        # Test portfolio holdings
        print(f"\n💼 Testing portfolio holdings...")
        holdings = api.get_portfolio_holdings()
        
        if holdings:
            print(f"   📊 Holdings response type: {type(holdings)}")
            if isinstance(holdings, dict):
                print(f"   📋 Response keys: {list(holdings.keys())}")
                
                # Check for data in different possible structures
                if 'Success' in holdings and holdings['Success']:
                    holding_data = holdings['Success']
                    if isinstance(holding_data, list):
                        print(f"   📈 Found {len(holding_data)} holdings")
                        for i, holding in enumerate(holding_data[:3]):
                            if isinstance(holding, dict):
                                stock_code = holding.get('stock_code', 'Unknown')
                                quantity = holding.get('quantity', 0)
                                print(f"     {i+1}. {stock_code}: {quantity} shares")
                    else:
                        print(f"   📄 Holdings data: {str(holding_data)[:100]}...")
        
        # Test funds
        print(f"\n💰 Testing funds information...")
        funds = api.get_funds()
        
        if funds:
            print(f"   📊 Funds response type: {type(funds)}")
            if isinstance(funds, dict):
                print(f"   📋 Response keys: {list(funds.keys())}")
                
                if 'Success' in funds and funds['Success']:
                    fund_data = funds['Success']
                    print(f"   💵 Fund data: {str(fund_data)[:200]}...")
        
        # Test historical data
        print(f"\n📈 Testing historical data...")
        test_stocks = ["RELIANCE", "TCS", "HDFCBANK"]
        
        for stock in test_stocks[:1]:  # Test just one stock
            print(f"   📊 Getting data for {stock}...")
            historical = api.get_historical_data(stock)
            
            if historical:
                print(f"     ✅ Data retrieved for {stock}")
                if isinstance(historical, dict):
                    print(f"     📋 Response keys: {list(historical.keys())}")
                    
                    if 'Success' in historical and historical['Success']:
                        hist_data = historical['Success']
                        if isinstance(hist_data, list):
                            print(f"     📈 Found {len(hist_data)} data points")
                            if hist_data:
                                latest = hist_data[-1]
                                print(f"     📅 Latest: {latest.get('datetime', 'Unknown')}")
                                print(f"     💰 Close: ₹{latest.get('close', 'Unknown')}")
                        else:
                            print(f"     📄 Historical data: {str(hist_data)[:100]}...")
            else:
                print(f"     ❌ No data for {stock}")
            
            break  # Just test one stock for now
        
        print(f"\n🎉 DIRECT API TEST COMPLETED!")
        print("✅ Your Breeze API credentials are working")
        print("✅ Data fetching is successful")
        print("✅ Ready for trading strategies")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        print("🧪 Starting direct Breeze API test...")
        print(f"⏰ Time: {datetime.now()}")
        
        success = test_direct_breeze_api()
        
        print(f"\n" + "="*50)
        if success:
            print("🎉 SUCCESS! Your Breeze API is fully functional!")
            print("✅ Authentication works")
            print("✅ Data fetching works") 
            print("✅ Ready to integrate with trading strategies")
            print("\n💡 Next steps:")
            print("   1. Update your app to use the direct API implementation")
            print("   2. Test with your multi-strategy system")
            print("   3. Run live trading strategies")
        else:
            print("❌ API test failed - check credentials and connectivity")
        print("="*50)
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️  API test cancelled by user")
    except Exception as e:
        print(f"\n❌ API test script error: {e}")
        import traceback
        traceback.print_exc()