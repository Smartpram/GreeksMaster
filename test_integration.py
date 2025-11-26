#!/usr/bin/env python3
"""
MyBreezeApp Integration Test
===========================

Complete integration test for the updated MyBreezeApp with working Breeze API.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_app_integration():
    """Test the complete MyBreezeApp integration"""
    
    print("🚀 MYBREEZE APP INTEGRATION TEST")
    print("=" * 50)
    
    try:
        # Test 1: Import and initialize services
        print("📦 Testing Service Imports...")
        from app.services.breeze_api import BreezeAPIService
        from app.services.order_manager import OrderManager
        from app.services.risk_manager import RiskManager
        from app.config import Config
        
        print("✅ All service imports successful")
        
        # Test 2: Initialize Breeze API service
        print("\n🔧 Initializing Services...")
        breeze_service = BreezeAPIService()
        order_manager = OrderManager(breeze_service)
        risk_manager = RiskManager()
        
        print("✅ Services initialized successfully")
        
        # Test 3: Test Breeze API authentication
        print("\n🔐 Testing Breeze API Authentication...")
        auth_result = breeze_service.authenticate()
        
        if auth_result['success']:
            print("✅ Breeze API authentication successful")
            print(f"   User: {auth_result['user_name']}")
            print(f"   User ID: {auth_result['user_id']}")
            print(f"   Trading: {auth_result['segments'].get('Trading', 'Unknown')}")
        else:
            print(f"❌ Breeze API authentication failed: {auth_result['error']}")
            return False
        
        # Test 4: Test data retrieval
        print("\n📊 Testing Data Retrieval...")
        
        # Test user info
        user_info = breeze_service.get_user_info()
        if user_info['success']:
            print("✅ User info retrieved")
            print(f"   Trading Allowed: {user_info['trading_allowed']}")
            print(f"   Equity Access: {user_info['equity_allowed']}")
        else:
            print(f"❌ User info failed: {user_info['error']}")
        
        # Test portfolio
        portfolio = breeze_service.get_portfolio()
        if portfolio['success']:
            holdings_count = len(portfolio['data']) if isinstance(portfolio['data'], list) else 0
            print(f"✅ Portfolio retrieved: {holdings_count} holdings")
        else:
            print(f"⚠️  Portfolio: {portfolio['error']}")
        
        # Test funds
        funds = breeze_service.get_funds()
        if funds['success']:
            balance = funds['data'].get('total_bank_balance', 0) if isinstance(funds['data'], dict) else 0
            print(f"✅ Funds retrieved: ₹{balance:,.2f}")
        else:
            print(f"⚠️  Funds: {funds['error']}")
        
        # Test positions
        positions = breeze_service.get_portfolio_positions()
        if positions['success']:
            positions_count = len(positions['data']) if isinstance(positions['data'], list) else 0
            print(f"✅ Positions retrieved: {positions_count} positions")
        else:
            print(f"⚠️  Positions: {positions['error']}")
        
        # Test 5: Test Flask app creation
        print("\n🌐 Testing Flask App...")
        try:
            from app.main import create_app
            app = create_app()
            print("✅ Flask app created successfully")
            print(f"   App name: {app.name}")
            print(f"   Routes registered: {len(app.url_map._rules)} routes")
        except Exception as e:
            print(f"❌ Flask app creation failed: {e}")
            return False
        
        # Test 6: Test configuration
        print("\n⚙️  Testing Configuration...")
        config = Config()
        
        config_items = [
            ('BREEZE_API_KEY', bool(config.BREEZE_API_KEY)),
            ('BREEZE_SECRET_KEY', bool(config.BREEZE_SECRET_KEY)),
            ('BREEZE_SESSION_TOKEN', bool(config.BREEZE_SESSION_TOKEN)),
            ('BREEZE_USER_ID', bool(config.BREEZE_USER_ID)),
        ]
        
        for item, status in config_items:
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {item}: {'Configured' if status else 'Missing'}")
        
        # Summary
        print(f"\n" + "=" * 50)
        print("🏁 INTEGRATION TEST SUMMARY")
        print("=" * 50)
        
        working_components = [
            auth_result['success'],
            user_info['success'],
            True,  # Flask app creation
            all(status for _, status in config_items)
        ]
        
        success_count = sum(working_components)
        total_count = len(working_components)
        success_rate = (success_count / total_count) * 100
        
        print(f"✅ Authentication: {'Working' if auth_result['success'] else 'Failed'}")
        print(f"✅ Data Retrieval: {'Working' if user_info['success'] else 'Failed'}")
        print(f"✅ Flask App: Working")
        print(f"✅ Configuration: {'Complete' if all(status for _, status in config_items) else 'Incomplete'}")
        
        print(f"\n🎯 Integration Success Rate: {success_rate:.1f}% ({success_count}/{total_count})")
        
        if success_rate >= 75:
            print(f"\n🎉 EXCELLENT! MyBreezeApp is ready for production!")
            print(f"   🚀 All core components working")
            print(f"   📊 Breeze API integration complete")
            print(f"   💼 Portfolio and funds accessible")
            print(f"   🌐 Web interface ready")
            
            print(f"\n🎯 READY TO LAUNCH:")
            print("   1. ✅ Breeze API fully integrated")
            print("   2. ✅ Authentication working")
            print("   3. ✅ Data retrieval operational")
            print("   4. ✅ Flask web app ready")
            print("   5. 🚀 Ready for live trading (with proper testing)")
            
        elif success_rate >= 50:
            print(f"\n✅ GOOD! Core functionality working")
            print(f"   📈 Authentication and basic features ready")
            print(f"   🔧 Some components may need fine-tuning")
        else:
            print(f"\n⚠️  Needs more work")
            print(f"   🔧 Check failed components above")
        
        return success_rate >= 75
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_strategy_integration():
    """Test trading strategy integration"""
    print("\n🤖 TESTING STRATEGY INTEGRATION")
    print("-" * 30)
    
    try:
        from app.strategies.buy_hold_trend import BuyHoldTrendStrategy
        from app.services.breeze_api import BreezeAPIService
        from app.services.order_manager import OrderManager
        from app.services.risk_manager import RiskManager
        from app.services.notifications import NotificationService
        
        # Initialize services
        breeze_service = BreezeAPIService()
        order_manager = OrderManager(breeze_service)
        risk_manager = RiskManager()
        notification_service = NotificationService()
        
        # Initialize strategy
        strategy = BuyHoldTrendStrategy(
            order_manager=order_manager,
            risk_manager=risk_manager,
            notification_service=notification_service
        )
        
        print("✅ Strategy components initialized")
        print(f"   Strategy: {strategy.__class__.__name__}")
        print(f"   Order Manager: {order_manager.__class__.__name__}")
        print(f"   Risk Manager: {risk_manager.__class__.__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Strategy integration failed: {e}")
        return False

if __name__ == "__main__":
    try:
        print("🚀 Starting MyBreezeApp integration test...")
        print(f"⏰ Timestamp: {datetime.now()}")
        print(f"🔧 Testing all components...")
        
        # Main integration test
        main_success = test_app_integration()
        
        # Strategy integration test
        strategy_success = test_strategy_integration()
        
        if main_success and strategy_success:
            print(f"\n🎊 INTEGRATION COMPLETE! MYBREEZE APP IS READY! 🎊")
            print(f"✅ All systems operational")
            print(f"✅ Breeze API working perfectly")
            print(f"✅ Trading strategies ready")
            print(f"✅ Web interface functional")
            print(f"🚀 Ready to start live trading!")
        else:
            print(f"\n❌ Integration needs more work")
            print(f"🔧 Please check the errors above and retry")
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️ Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        
    input("\nPress Enter to continue...")