#!/usr/bin/env python3
"""
Complete Breeze API Endpoint Test
================================

Test all known Breeze API endpoints to find the correct ones for data fetching.
Based on ICICI Direct Breeze API documentation.
"""

import requests
import json
from datetime import datetime, timedelta
import sys
import os

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

class CompleteBreezeAPI:
    """Complete Breeze API implementation with correct endpoints"""
    
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
                    print(f"   Trading: {success_data.get('segments_allowed', {}).get('Trading', 'Unknown')}")
                    print(f"   Equity: {success_data.get('segments_allowed', {}).get('Equity', 'Unknown')}")
                    
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
    
    def test_all_endpoints(self):
        """Test all known Breeze API endpoints"""
        
        if not self.authenticated_session_token:
            print("❌ Not authenticated. Call authenticate() first.")
            return
        
        # Common headers for authenticated requests
        headers = {
            "Content-Type": "application/json",
            "SessionToken": self.authenticated_session_token,
            "AppKey": self.api_key
        }
        
        # List of known endpoints to test
        endpoints = [
            # Portfolio endpoints
            {"name": "Portfolio Holdings", "path": "portfolioholdingsequity", "method": "GET"},
            {"name": "Portfolio Holdings Alt", "path": "dematholdingequity", "method": "GET"},
            {"name": "Portfolio Positions", "path": "portfoliopositions", "method": "GET"},
            {"name": "Demat Holdings", "path": "dematholdingequity", "method": "POST"},
            
            # Fund endpoints
            {"name": "Funds", "path": "funds", "method": "GET"},
            {"name": "Margin", "path": "margin", "method": "GET"},
            
            # Market data endpoints
            {"name": "Historical Data", "path": "historicaldata", "method": "GET"},
            {"name": "Historical Charts", "path": "historicalcharts", "method": "GET"},
            {"name": "Live Feeds", "path": "livefeeds", "method": "GET"},
            {"name": "Quote", "path": "getquote", "method": "GET"},
            {"name": "OHLC", "path": "getohlc", "method": "GET"},
            
            # Order endpoints (for reference)
            {"name": "Order Book", "path": "orderbook", "method": "GET"},
            {"name": "Trade Book", "path": "tradebook", "method": "GET"},
        ]
        
        print(f"\n🔍 TESTING ALL KNOWN ENDPOINTS:")
        print("=" * 45)
        
        successful_endpoints = []
        
        for endpoint in endpoints:
            name = endpoint["name"]
            path = endpoint["path"]
            method = endpoint["method"]
            url = f"{self.base_url}/{path}"
            
            print(f"\n📡 Testing {name}:")
            print(f"   URL: {url}")
            print(f"   Method: {method}")
            
            try:
                if method == "GET":
                    response = requests.get(url, headers=headers, timeout=30)
                else:
                    response = requests.post(url, headers=headers, json={}, timeout=30)
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ SUCCESS!")
                    try:
                        data = response.json()
                        print(f"   📊 Response type: {type(data)}")
                        if isinstance(data, dict):
                            print(f"   📋 Keys: {list(data.keys())}")
                        successful_endpoints.append({
                            "name": name,
                            "path": path,
                            "method": method,
                            "url": url
                        })
                    except:
                        print(f"   📄 Response: {response.text[:100]}...")
                        
                elif response.status_code == 404:
                    print(f"   ❌ Not Found (404)")
                elif response.status_code == 403:
                    print(f"   ❌ Forbidden (403)")
                elif response.status_code == 400:
                    print(f"   ❌ Bad Request (400)")
                    print(f"   📄 Error: {response.text[:100]}...")
                else:
                    print(f"   ⚠️  Status {response.status_code}: {response.text[:100]}...")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:50]}...")
        
        print(f"\n🎯 SUCCESSFUL ENDPOINTS SUMMARY:")
        print("=" * 35)
        
        if successful_endpoints:
            for endpoint in successful_endpoints:
                print(f"✅ {endpoint['name']}: {endpoint['method']} {endpoint['path']}")
        else:
            print("❌ No endpoints returned success (200)")
        
        return successful_endpoints
    
    def get_historical_data_with_params(self, stock_code="RELIANCE"):
        """Try historical data with different parameter combinations"""
        
        if not self.authenticated_session_token:
            print("❌ Not authenticated.")
            return None
        
        print(f"\n📈 TESTING HISTORICAL DATA WITH PARAMETERS:")
        print("=" * 45)
        
        # Try different endpoint variations
        endpoints = [
            "historicaldata",
            "historicalcharts", 
            "gethistoricaldata",
            "chartdata"
        ]
        
        # Different parameter combinations
        param_sets = [
            {
                "stock_code": stock_code,
                "exchange_code": "NSE",
                "interval": "1day",
                "from_date": "2025-10-01T00:00:00.000Z",
                "to_date": "2025-11-07T23:59:59.000Z"
            },
            {
                "StockCode": stock_code,
                "ExchangeCode": "NSE", 
                "Interval": "1day",
                "FromDate": "2025-10-01",
                "ToDate": "2025-11-07"
            },
            {
                "symbol": stock_code,
                "exchange": "NSE",
                "interval": "1D",
                "from": "01-10-2025",
                "to": "07-11-2025"
            }
        ]
        
        headers = {
            "Content-Type": "application/json",
            "SessionToken": self.authenticated_session_token,
            "AppKey": self.api_key
        }
        
        for endpoint in endpoints:
            url = f"{self.base_url}/{endpoint}"
            print(f"\n🔍 Testing endpoint: {endpoint}")
            
            for i, params in enumerate(param_sets):
                print(f"   📊 Parameter set {i+1}: {list(params.keys())}")
                
                try:
                    # Try GET with params
                    response = requests.get(url, params=params, headers=headers, timeout=30)
                    print(f"     GET Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"     ✅ GET SUCCESS with params!")
                        data = response.json()
                        print(f"     📊 Data type: {type(data)}")
                        return data
                    
                    # Try POST with JSON body
                    response = requests.post(url, json=params, headers=headers, timeout=30)
                    print(f"     POST Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"     ✅ POST SUCCESS with JSON!")
                        data = response.json()
                        print(f"     📊 Data type: {type(data)}")
                        return data
                    
                    if response.status_code != 404:
                        print(f"     📄 Response: {response.text[:100]}...")
                        
                except Exception as e:
                    print(f"     ❌ Error: {str(e)[:50]}...")
        
        return None

def test_complete_api():
    """Run complete API test"""
    
    print("🚀 COMPLETE BREEZE API ENDPOINT TEST")
    print("=" * 50)
    
    try:
        from app.config import Config
        
        # Initialize API
        api = CompleteBreezeAPI(
            api_key=Config.BREEZE_API_KEY,
            secret_key=Config.BREEZE_SECRET_KEY,
            session_token=Config.BREEZE_SESSION_TOKEN,
            user_id=Config.BREEZE_USER_ID
        )
        
        # Authenticate
        if not api.authenticate():
            return False
        
        # Test all endpoints
        successful_endpoints = api.test_all_endpoints()
        
        # Try historical data specifically 
        historical_data = api.get_historical_data_with_params()
        
        print(f"\n" + "="*50)
        print("🏁 COMPLETE API TEST SUMMARY")
        print("="*50)
        
        print(f"✅ Authentication: SUCCESS")
        print(f"📊 Working endpoints: {len(successful_endpoints)}")
        print(f"📈 Historical data: {'SUCCESS' if historical_data else 'NEEDS MORE TESTING'}")
        
        if successful_endpoints:
            print(f"\n💡 NEXT STEPS:")
            print("   1. Use working endpoints for live data")
            print("   2. Implement portfolio tracking")
            print("   3. Set up trading strategies")
        else:
            print(f"\n🔧 TROUBLESHOOTING NEEDED:")
            print("   1. Check Breeze API documentation")
            print("   2. Contact ICICI support for correct endpoints")
            print("   3. Verify API permissions")
        
        return True
        
    except Exception as e:
        print(f"❌ Complete API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        print("🧪 Starting complete Breeze API endpoint test...")
        print(f"⏰ Time: {datetime.now()}")
        
        success = test_complete_api()
        
        if success:
            print(f"\n🎉 TEST COMPLETED SUCCESSFULLY!")
        else:
            print(f"\n❌ TEST FAILED")
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Test script error: {e}")
        import traceback
        traceback.print_exc()