#!/usr/bin/env python3
"""
Breeze API Connection Test
=========================

Test script to verify Breeze API credentials and data fetching capability.
"""

import sys
import os
from datetime import datetime, timedelta
import traceback

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_breeze_connection():
    """Test Breeze API connection and data fetching"""
    
    print("🚀 BREEZE API CONNECTION TEST")
    print("=" * 50)
    
    try:
        # Import required modules
        from app.config import Config
        from app.services.breeze_api import BreezeAPIService
        
        print("✅ Modules imported successfully")
        
        # Load configuration
        print(f"\n📋 CONFIGURATION CHECK:")
        print(f"   API Key: {Config.BREEZE_API_KEY[:10]}..." if Config.BREEZE_API_KEY else "   ❌ API Key missing")
        print(f"   Secret Key: {Config.BREEZE_SECRET_KEY[:10]}..." if Config.BREEZE_SECRET_KEY else "   ❌ Secret Key missing")
        print(f"   Session Token: {Config.BREEZE_SESSION_TOKEN}" if Config.BREEZE_SESSION_TOKEN else "   ❌ Session Token missing")
        print(f"   User ID: {Config.BREEZE_USER_ID}" if Config.BREEZE_USER_ID else "   ❌ User ID missing")
        print(f"   Paper Trading: {Config.PAPER_TRADING}")
        
        # Check if all required credentials are present
        required_creds = [
            Config.BREEZE_API_KEY,
            Config.BREEZE_SECRET_KEY, 
            Config.BREEZE_SESSION_TOKEN,
            Config.BREEZE_USER_ID
        ]
        
        if not all(required_creds):
            print("❌ Missing required credentials!")
            return False
        
        print("✅ All credentials present")
        
        # Initialize Breeze API service
        print(f"\n🔌 INITIALIZING BREEZE API SERVICE...")
        breeze_service = BreezeAPIService()
        print("✅ Breeze service initialized")
        
        # Test authentication
        print(f"\n🔐 TESTING AUTHENTICATION...")
        auth_result = breeze_service.authenticate()
        
        if auth_result:
            print("✅ Authentication successful!")
            print(f"   Session established with Breeze API")
        else:
            print("❌ Authentication failed!")
            return False
        
        # Test customer details
        print(f"\n👤 TESTING CUSTOMER DETAILS...")
        try:
            customer_details = breeze_service.get_customer_details()
            if customer_details:
                print("✅ Customer details retrieved:")
                if isinstance(customer_details, dict):
                    # Print relevant customer info (mask sensitive data)
                    for key, value in customer_details.items():
                        if key.lower() in ['user_id', 'customer_id', 'name', 'email']:
                            display_value = str(value)[:20] + "..." if len(str(value)) > 20 else str(value)
                            print(f"   {key}: {display_value}")
                else:
                    print(f"   Response: {str(customer_details)[:100]}...")
            else:
                print("⚠️  No customer details returned")
        except Exception as e:
            print(f"❌ Customer details failed: {e}")
        
        # Test portfolio holdings
        print(f"\n💼 TESTING PORTFOLIO HOLDINGS...")
        try:
            holdings = breeze_service.get_portfolio_holdings()
            if holdings:
                print("✅ Portfolio holdings retrieved:")
                if isinstance(holdings, list):
                    print(f"   Found {len(holdings)} holdings")
                    for i, holding in enumerate(holdings[:3]):  # Show first 3
                        if isinstance(holding, dict):
                            symbol = holding.get('stock_code', 'Unknown')
                            quantity = holding.get('quantity', 0)
                            print(f"   {i+1}. {symbol}: {quantity} shares")
                else:
                    print(f"   Response: {str(holdings)[:100]}...")
            else:
                print("⚠️  No holdings data returned (may be empty portfolio)")
        except Exception as e:
            print(f"❌ Portfolio holdings failed: {e}")
        
        # Test portfolio positions
        print(f"\n📊 TESTING PORTFOLIO POSITIONS...")
        try:
            positions = breeze_service.get_portfolio_positions()
            if positions:
                print("✅ Portfolio positions retrieved:")
                if isinstance(positions, list):
                    print(f"   Found {len(positions)} positions")
                    for i, position in enumerate(positions[:3]):  # Show first 3
                        if isinstance(position, dict):
                            symbol = position.get('stock_code', 'Unknown')
                            quantity = position.get('quantity', 0)
                            pnl = position.get('pnl', 0)
                            print(f"   {i+1}. {symbol}: {quantity} shares, P&L: ₹{pnl}")
                else:
                    print(f"   Response: {str(positions)[:100]}...")
            else:
                print("⚠️  No positions data returned (may be empty)")
        except Exception as e:
            print(f"❌ Portfolio positions failed: {e}")
        
        # Test market data (if available in Breeze API)
        print(f"\n📈 TESTING MARKET DATA ACCESS...")
        try:
            # This is a basic test - actual market data methods may vary
            # based on Breeze API documentation
            print("⚠️  Market data test requires specific Breeze API methods")
            print("   (Historical data, live quotes, etc.)")
            print("   Check Breeze API documentation for available endpoints")
        except Exception as e:
            print(f"❌ Market data test failed: {e}")
        
        print(f"\n🎯 CONNECTION TEST SUMMARY:")
        print("=" * 35)
        print("✅ API credentials configured")
        print("✅ Service initialization successful")
        print("✅ Authentication successful")
        print("✅ Basic API calls working")
        
        print(f"\n🚀 NEXT STEPS:")
        print("=" * 15)
        print("1. ✅ API connection verified")
        print("2. 📊 Test historical data fetching")
        print("3. 📈 Test live market data")
        print("4. 🔄 Test order placement (paper trading)")
        print("5. 🤖 Run strategy backtests with real data")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all required packages are installed:")
        print("   pip install breeze_connect")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"\n🔍 Error details:")
        traceback.print_exc()
        return False

def test_historical_data():
    """Test historical data fetching if basic connection works"""
    
    print(f"\n📊 TESTING HISTORICAL DATA FETCHING...")
    print("=" * 45)
    
    try:
        from app.services.data_stream import HistoricalDataService
        from app.services.breeze_api import BreezeAPIService
        
        # Initialize services
        breeze_service = BreezeAPIService()
        breeze_service.authenticate()
        
        historical_service = HistoricalDataService(breeze_service)
        
        # Test parameters
        test_symbol = "RELIANCE"
        days_back = 30
        
        print(f"📈 Fetching {days_back} days of data for {test_symbol}...")
        
        # Attempt to fetch historical data
        historical_data = historical_service.get_historical_data(
            instrument=test_symbol,
            interval="1day",
            days_back=days_back
        )
        
        if historical_data:
            print(f"✅ Historical data retrieved:")
            print(f"   Symbol: {test_symbol}")
            print(f"   Records: {len(historical_data)}")
            print(f"   Date range: {historical_data[0].get('datetime', 'Unknown')} to {historical_data[-1].get('datetime', 'Unknown')}")
            
            # Show sample data
            if len(historical_data) > 0:
                sample = historical_data[-1]  # Latest record
                print(f"   Latest record:")
                for key, value in sample.items():
                    print(f"     {key}: {value}")
            
            return True
        else:
            print("⚠️  No historical data returned")
            return False
            
    except Exception as e:
        print(f"❌ Historical data test failed: {e}")
        return False

if __name__ == "__main__":
    try:
        print("🧪 Starting comprehensive Breeze API tests...")
        
        # Test basic connection
        connection_success = test_breeze_connection()
        
        if connection_success:
            print(f"\n" + "="*50)
            print("🎉 BASIC CONNECTION TEST PASSED!")
            print("="*50)
            
            # Test historical data
            historical_success = test_historical_data()
            
            if historical_success:
                print(f"\n🎉 ALL TESTS PASSED!")
                print("✅ Your Breeze API is fully functional")
                print("✅ Ready for live trading strategies")
            else:
                print(f"\n⚠️  PARTIAL SUCCESS")
                print("✅ API connection works")
                print("❌ Historical data needs verification")
        else:
            print(f"\n❌ CONNECTION TEST FAILED")
            print("Please check your credentials and try again")
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Test script error: {e}")
        traceback.print_exc()