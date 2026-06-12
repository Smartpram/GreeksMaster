"""
Breeze API Session Diagnostic & Refresh Tool
=============================================

Diagnoses connection issues and helps refresh the session token
"""

import logging
from app.services.breeze_api import BreezeAPIService
from app.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def diagnose_connection():
    """Diagnose Breeze API connection"""
    
    print("\n" + "="*100)
    print("BREEZE API CONNECTION DIAGNOSTIC TOOL")
    print("="*100)
    
    config = Config()
    
    # Check configuration
    print("\n1️⃣  CONFIGURATION CHECK")
    print("-" * 100)
    
    print(f"✓ API Key: {config.BREEZE_API_KEY[:20] if config.BREEZE_API_KEY else '❌ NOT SET'}...")
    print(f"✓ Secret Key: {config.BREEZE_SECRET_KEY[:20] if config.BREEZE_SECRET_KEY else '❌ NOT SET'}...")
    print(f"✓ User ID: {config.BREEZE_USER_ID if config.BREEZE_USER_ID else '❌ NOT SET'}")
    print(f"✓ Session Token: {config.BREEZE_SESSION_TOKEN[:30] if config.BREEZE_SESSION_TOKEN else '❌ NOT SET'}...")
    print(f"✓ Password: {'✓ SET' if config.BREEZE_PASSWORD else '❌ NOT SET'}")
    
    # Check missing configs
    missing_configs = []
    if not config.BREEZE_API_KEY:
        missing_configs.append("BREEZE_API_KEY")
    if not config.BREEZE_SECRET_KEY:
        missing_configs.append("BREEZE_SECRET_KEY")
    if not config.BREEZE_USER_ID:
        missing_configs.append("BREEZE_USER_ID")
    if not config.BREEZE_SESSION_TOKEN:
        missing_configs.append("BREEZE_SESSION_TOKEN")
    
    if missing_configs:
        print(f"\n⚠️  MISSING CONFIGURATIONS:")
        for config_name in missing_configs:
            print(f"   - {config_name}")
        print(f"\n📝 Please update .env file with missing values")
        return False
    
    # Try API connection
    print("\n2️⃣  API CONNECTION TEST")
    print("-" * 100)
    
    try:
        api = BreezeAPIService()
        print("✓ BreezeAPIService initialized")
        
        auth_result = api.authenticate()
        
        if auth_result.get('success'):
            print(f"✅ AUTHENTICATION SUCCESSFUL")
            print(f"   User: {auth_result.get('user_name')}")
            print(f"   User ID: {auth_result.get('user_id')}")
            print(f"   Segments: {auth_result.get('segments')}")
            return True
        else:
            print(f"❌ AUTHENTICATION FAILED")
            error = auth_result.get('error', 'Unknown error')
            print(f"   Error: {error}")
            
            if "session" in error.lower() or "expired" in error.lower():
                print(f"\n💡 SESSION TOKEN EXPIRED")
                print(f"   Action: Refresh your session token by visiting:")
                print(f"   https://api.icicidirect.com/apiuser/login?api_key=YOUR_API_KEY")
                print(f"   Then update BREEZE_SESSION_TOKEN in .env file")
                return False
            elif "not available" in error.lower():
                print(f"\n💡 RESOURCE NOT AVAILABLE")
                print(f"   This usually means:")
                print(f"   1. Session token is invalid/expired")
                print(f"   2. Network/firewall blocking API access")
                print(f"   3. API endpoint is down")
                return False
            else:
                print(f"\n💡 UNKNOWN ERROR")
                print(f"   Please check error message above")
                return False
    
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {str(e)}")
        print(f"\n💡 Common causes:")
        print(f"   1. Network connectivity issue")
        print(f"   2. Invalid configuration")
        print(f"   3. API endpoint not accessible")
        return False


def show_session_refresh_instructions():
    """Show instructions for refreshing session token"""
    
    print("\n" + "="*100)
    print("SESSION TOKEN REFRESH INSTRUCTIONS")
    print("="*100)
    
    config = Config()
    
    print("\n📋 STEPS TO GET A FRESH SESSION TOKEN:")
    print("-" * 100)
    
    print("\n1️⃣  VISIT LOGIN URL")
    print(f"   https://api.icicidirect.com/apiuser/login?api_key={config.BREEZE_API_KEY}")
    
    print("\n2️⃣  LOGIN WITH YOUR CREDENTIALS")
    print(f"   User ID: {config.BREEZE_USER_ID}")
    print(f"   Password: (your password)")
    
    print("\n3️⃣  COPY SESSION TOKEN")
    print("   After login, you'll see a session token displayed on the screen")
    print("   Copy the entire token (it's a long string)")
    
    print("\n4️⃣  UPDATE .env FILE")
    print("   Open .env file and update:")
    print("   BREEZE_SESSION_TOKEN=<paste_the_token_here>")
    
    print("\n5️⃣  VERIFY CONNECTION")
    print("   Run this script again to test the new token")
    
    print("\n" + "-" * 100)
    print("⏰ NOTE: Session tokens typically expire after several hours of inactivity")
    print("         Refresh whenever you see 'expired' or 'not available' errors")
    print("=" * 100)


def main():
    """Main execution"""
    
    print("\n")
    
    # Run diagnostic
    is_connected = diagnose_connection()
    
    if not is_connected:
        # Show refresh instructions
        show_session_refresh_instructions()
        
        print("\n" + "="*100)
        print("DIAGNOSTIC COMPLETE - ISSUES FOUND")
        print("="*100)
        print("\n🔧 ACTION REQUIRED:")
        print("   1. Visit the login URL above")
        print("   2. Get a fresh session token")
        print("   3. Update BREEZE_SESSION_TOKEN in .env")
        print("   4. Run the live data test again")
        print("\n")
        return 1
    else:
        print("\n" + "="*100)
        print("DIAGNOSTIC COMPLETE - ALL OK ✅")
        print("="*100)
        print("\n🚀 YOU'RE READY TO TEST SCREENERS!")
        print("   Run: python test_options_screeners_live.py")
        print("\n")
        return 0


if __name__ == "__main__":
    exit_code = main()
    import sys
    sys.exit(exit_code)
