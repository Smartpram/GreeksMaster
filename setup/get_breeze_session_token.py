#!/usr/bin/env python3
"""
Helper script to get and validate Breeze API Session Token
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import webbrowser
from app.services.breeze_api import BreezeAPIService
from app.config import Config

def main():
    print("\n" + "="*80)
    print("BREEZE API SESSION TOKEN HELPER")
    print("="*80 + "\n")
    
    config = Config()
    breeze = BreezeAPIService()
    
    print("📋 STEP 1: Get Login URL")
    print("-" * 80)
    login_info = breeze.login()
    login_url = login_info['login_url']
    print(f"\nLogin URL: {login_url}")
    print("\nThis URL is required for authentication.")
    
    print("\n" + "="*80)
    print("📋 STEP 2: Complete Web Login")
    print("-" * 80)
    print("\n1. A browser window will open with the ICICI Direct login page")
    print("2. Enter your credentials and log in")
    print("3. After successful login, you'll see your SESSION TOKEN")
    print("4. Copy the entire session token (it's usually 50+ characters long)")
    print("\n⚠️  Session tokens expire after inactivity (typically 24 hours)")
    print("   You'll need to repeat this process if the token expires.\n")
    
    open_browser = input("Open browser now? (y/n) [default: y]: ").strip().lower() or "y"
    
    if open_browser == "y":
        print(f"\n🌐 Opening browser to: {login_url}")
        try:
            webbrowser.open(login_url)
            print("✓ Browser opened. Please complete the login process.")
        except Exception as e:
            print(f"⚠️  Could not open browser automatically: {e}")
            print(f"\nPlease manually visit: {login_url}")
    
    print("\n" + "="*80)
    print("📋 STEP 3: Update Session Token")
    print("-" * 80)
    print("\n✋ After logging in and getting your session token:\n")
    
    new_token = input("Paste your NEW session token here: ").strip()
    
    if not new_token:
        print("\n❌ No token provided. Exiting.")
        return
    
    if len(new_token) < 20:
        print(f"\n⚠️  WARNING: Token seems short ({len(new_token)} characters)")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return
    
    print("\n" + "="*80)
    print("📋 STEP 4: Test Authentication")
    print("-" * 80)
    
    # Update the session token
    breeze.session_token = new_token
    
    print(f"\nTesting authentication with new token...")
    auth_result = breeze.authenticate()
    
    if auth_result['success']:
        print("✓ Authentication SUCCESSFUL!")
        print(f"\nUser Details:")
        print(f"  User Name: {auth_result.get('user_name', 'N/A')}")
        print(f"  User ID: {auth_result.get('user_id', 'N/A')}")
        if auth_result.get('segments'):
            print(f"  Trading Allowed: {auth_result['segments'].get('Trading', 'N') == 'Y'}")
            print(f"  Equity Allowed: {auth_result['segments'].get('Equity', 'N') == 'Y'}")
        
        print("\n" + "="*80)
        print("📋 STEP 5: Save to .env")
        print("-" * 80)
        
        save_choice = input("\nSave this token to .env file? (y/n) [default: y]: ").strip().lower() or "y"
        
        if save_choice == "y":
            env_file = os.path.join(os.path.dirname(__file__), '.env')
            
            # Read current .env
            with open(env_file, 'r') as f:
                env_content = f.read()
            
            # Replace the session token
            import re
            env_content = re.sub(
                r'BREEZE_SESSION_TOKEN=.*',
                f'BREEZE_SESSION_TOKEN={new_token}',
                env_content
            )
            
            # Write updated .env
            with open(env_file, 'w') as f:
                f.write(env_content)
            
            print(f"\n✓ Session token saved to .env file!")
            print(f"\nNow you can run the backtest:")
            print(f"  python run_breeze_backtest.py")
        
    else:
        print("✗ Authentication FAILED!")
        print(f"\nError: {auth_result.get('error', 'Unknown error')}")
        
        if 'login_url' in auth_result:
            print(f"\nPlease get a fresh token from: {auth_result['login_url']}")
        
        print("\nCommon issues:")
        print("1. Token is expired - get a fresh one from web login")
        print("2. Token format is incorrect - verify you copied the entire token")
        print("3. Token is for a different API key - ensure you're using the right account")

if __name__ == "__main__":
    main()
