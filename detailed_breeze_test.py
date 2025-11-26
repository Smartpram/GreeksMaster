#!/usr/bin/env python3
"""
Detailed Breeze API Diagnostic Test
==================================

This script provides detailed diagnostics for Breeze API connection issues.
"""

import sys
import os
import json
from datetime import datetime

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def detailed_breeze_test():
    """Detailed Breeze API diagnostic test"""
    
    print("🔍 DETAILED BREEZE API DIAGNOSTIC")
    print("=" * 50)
    
    try:
        # Import and check breeze_connect availability
        print("📦 Checking breeze_connect package...")
        try:
            from breeze_connect import BreezeConnect
            print("✅ breeze_connect package imported successfully")
        except ImportError as e:
            print(f"❌ breeze_connect import failed: {e}")
            print("💡 Install with: pip install breeze_connect")
            return False
        
        # Load configuration
        from app.config import Config
        
        print(f"\n📋 CREDENTIALS VALIDATION:")
        creds = {
            "API_KEY": Config.BREEZE_API_KEY,
            "SECRET_KEY": Config.BREEZE_SECRET_KEY, 
            "SESSION_TOKEN": Config.BREEZE_SESSION_TOKEN,
            "USER_ID": Config.BREEZE_USER_ID
        }
        
        for key, value in creds.items():
            if value:
                masked_value = str(value)[:8] + "..." if len(str(value)) > 8 else str(value)
                print(f"   ✅ {key}: {masked_value}")
            else:
                print(f"   ❌ {key}: Missing!")
        
        # Initialize Breeze Connect directly
        print(f"\n🔌 INITIALIZING BREEZE CONNECT...")
        try:
            breeze = BreezeConnect(api_key=Config.BREEZE_API_KEY)
            print("✅ BreezeConnect object created")
        except Exception as e:
            print(f"❌ BreezeConnect initialization failed: {e}")
            return False
        
        # Test session generation with detailed error handling
        print(f"\n🔐 TESTING SESSION GENERATION...")
        try:
            print("   📤 Sending authentication request...")
            print(f"   🔑 Using API Key: {Config.BREEZE_API_KEY[:10]}...")
            print(f"   🔒 Using Secret: {Config.BREEZE_SECRET_KEY[:10]}...")
            print(f"   🎫 Using Session Token: {Config.BREEZE_SESSION_TOKEN}")
            
            response = breeze.generate_session(
                api_secret=Config.BREEZE_SECRET_KEY,
                session_token=Config.BREEZE_SESSION_TOKEN
            )
            
            print(f"   📥 Raw response received:")
            print(f"   Response type: {type(response)}")
            
            if response is None:
                print("   ❌ Response is None - API call failed completely")
                return False
            
            # Print full response for debugging
            print(f"   📄 Full response:")
            if isinstance(response, dict):
                for key, value in response.items():
                    print(f"     {key}: {value}")
            else:
                print(f"     {response}")
            
            # Check response structure
            if isinstance(response, dict):
                if 'Success' in response:
                    if response['Success']:
                        print("   ✅ Authentication successful!")
                        if 'Result' in response:
                            result = response['Result']
                            print(f"   📋 Result: {result}")
                            if isinstance(result, dict) and 'session_token' in result:
                                session_token = result['session_token']
                                print(f"   🎫 Session Token: {session_token[:20]}...")
                            else:
                                print("   ⚠️  Session token not found in result")
                        else:
                            print("   ⚠️  No 'Result' key in response")
                        return True
                    else:
                        print("   ❌ Authentication failed!")
                        if 'Error' in response:
                            print(f"   🚫 Error: {response['Error']}")
                        return False
                else:
                    print("   ❌ Unexpected response format - no 'Success' key")
                    return False
            else:
                print(f"   ❌ Unexpected response type: {type(response)}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception during authentication: {e}")
            print(f"   Exception type: {type(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_breeze_api_version():
    """Check breeze_connect version and documentation"""
    
    print(f"\n📚 BREEZE API VERSION INFO:")
    print("=" * 35)
    
    try:
        import breeze_connect
        if hasattr(breeze_connect, '__version__'):
            print(f"   📦 Version: {breeze_connect.__version__}")
        else:
            print(f"   📦 Version: Unknown")
        
        # Check available methods
        from breeze_connect import BreezeConnect
        breeze_methods = [method for method in dir(BreezeConnect) if not method.startswith('_')]
        print(f"   🔧 Available methods: {len(breeze_methods)}")
        print(f"   📋 Key methods: {breeze_methods[:10]}")
        
    except Exception as e:
        print(f"   ❌ Version check failed: {e}")

def save_diagnostic_report(results):
    """Save diagnostic results to file"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'breeze_diagnostic_{timestamp}.json'
    
    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Diagnostic report saved: {filename}")
    except Exception as e:
        print(f"\n❌ Failed to save report: {e}")

if __name__ == "__main__":
    try:
        print("🧪 Starting detailed Breeze API diagnostics...")
        
        # Run version check
        check_breeze_api_version()
        
        # Run detailed test
        success = detailed_breeze_test()
        
        # Create diagnostic report
        diagnostic_results = {
            "timestamp": datetime.now().isoformat(),
            "test_success": success,
            "python_version": sys.version,
            "platform": sys.platform
        }
        
        save_diagnostic_report(diagnostic_results)
        
        if success:
            print(f"\n🎉 DIAGNOSTIC PASSED!")
            print("✅ Breeze API connection is working")
            print("✅ Ready to proceed with data fetching")
        else:
            print(f"\n❌ DIAGNOSTIC FAILED!")
            print("🔧 Possible solutions:")
            print("   1. Verify credentials with ICICIDirect")
            print("   2. Check if session token is still valid")
            print("   3. Ensure API key is activated")
            print("   4. Check internet connectivity")
            print("   5. Verify IP address is whitelisted")
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Diagnostic cancelled by user")
    except Exception as e:
        print(f"\n❌ Diagnostic script error: {e}")
        import traceback
        traceback.print_exc()