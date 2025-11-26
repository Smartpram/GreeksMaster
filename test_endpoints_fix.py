#!/usr/bin/env python3
"""
Quick Breeze API Endpoint Test
=============================

Test the fixed checksum calculation for data endpoints.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from datetime import datetime

def test_fixed_endpoints():
    """Test the fixed Breeze API endpoints"""
    
    print("🔧 TESTING FIXED BREEZE API ENDPOINTS")
    print("=" * 50)
    
    try:
        from app.services.breeze_api import BreezeAPIService
        
        # Initialize API
        breeze_service = BreezeAPIService()
        
        # Test 1: Authentication
        print("🔐 Testing Authentication...")
        auth_result = breeze_service.authenticate()
        
        if not auth_result['success']:
            print(f"❌ Authentication failed: {auth_result['error']}")
            return False
        
        print("✅ Authentication successful")
        print(f"   User: {auth_result['user_name']}")
        
        # Test 2: Test fixed endpoints
        print("\n📊 Testing Fixed Data Endpoints...")
        
        endpoints_to_test = [
            ("Demat Holdings", lambda: breeze_service.get_demat_holdings()),
            ("Funds", lambda: breeze_service.get_funds()),
            ("Portfolio Positions", lambda: breeze_service.get_portfolio_positions()),
            ("Quotes (ITC)", lambda: breeze_service.get_quotes("ITC", "NSE"))
        ]
        
        results = {}
        
        for name, endpoint_func in endpoints_to_test:
            print(f"\n🔍 Testing {name}...")
            try:
                result = endpoint_func()
                results[name] = result
                
                if result['success']:
                    if isinstance(result['data'], list):
                        count = len(result['data'])
                        print(f"   ✅ SUCCESS: Retrieved {count} items")
                    elif isinstance(result['data'], dict):
                        keys = list(result['data'].keys())[:5]
                        print(f"   ✅ SUCCESS: Data keys: {keys}")
                    else:
                        print(f"   ✅ SUCCESS: Data retrieved")
                else:
                    print(f"   ❌ FAILED: {result['error']}")
                    
            except Exception as e:
                print(f"   ❌ EXCEPTION: {e}")
                results[name] = {'success': False, 'error': str(e)}
        
        # Summary
        print(f"\n" + "=" * 50)
        print("🏁 ENDPOINT TEST RESULTS")
        print("=" * 50)
        
        success_count = sum(1 for r in results.values() if r.get('success', False))
        total_count = len(results)
        
        for name, result in results.items():
            status = "✅ SUCCESS" if result.get('success', False) else "❌ FAILED"
            print(f"{status}: {name}")
            if not result.get('success', False):
                print(f"    Error: {result.get('error', 'Unknown')}")
        
        success_rate = (success_count / total_count) * 100
        print(f"\n🎯 Endpoint Success Rate: {success_rate:.1f}% ({success_count}/{total_count})")
        
        if success_rate >= 75:
            print(f"\n🎉 EXCELLENT! Checksum fix successful!")
            print(f"   ✅ Most endpoints now working")
            print(f"   📊 Data retrieval operational")
        elif success_rate >= 50:
            print(f"\n✅ IMPROVED! Some endpoints working")
            print(f"   🔧 Progress made on checksum issue")
        else:
            print(f"\n⚠️ Still needs work")
            print(f"   🔧 Checksum calculation may need more adjustment")
        
        return success_rate >= 50
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        print("🚀 Testing fixed Breeze API endpoints...")
        print(f"⏰ Time: {datetime.now()}")
        
        success = test_fixed_endpoints()
        
        if success:
            print(f"\n🎊 ENDPOINT FIX SUCCESSFUL! 🎊")
            print(f"✅ Checksum calculation improved")
            print(f"✅ Data endpoints working better")
        else:
            print(f"\n❌ Still needs more work on checksum calculation")
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️ Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        
    input("\nPress Enter to continue...")