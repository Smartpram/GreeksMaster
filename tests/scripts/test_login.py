#!/usr/bin/env python3
"""
Test script to validate Breeze API login and authentication
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.breeze_api import BreezeAPIService
import json

def test_login():
    """Test login with credentials"""
    print("=" * 70)
    print("BREEZE API LOGIN TEST")
    print("=" * 70)
    
    # Initialize service
    breeze = BreezeAPIService()
    
    print("\n1. ATTEMPTING LOGIN WITH CREDENTIALS")
    print("-" * 70)
    login_result = breeze.login()
    
    print(f"Result: {json.dumps(login_result, indent=2)}")
    
    if login_result['success']:
        print("\n✓ LOGIN SUCCESSFUL")
        print(f"  User: {login_result.get('user_name')}")
        print(f"  UserID: {login_result.get('user_id')}")
        print(f"  Session Token: {login_result.get('session_token', 'N/A')[:30]}...")
        print(f"  Segments: {login_result.get('segments', {})}")
        
        print("\n2. VERIFYING AUTHENTICATION WITH NEW SESSION TOKEN")
        print("-" * 70)
        auth_result = breeze.authenticate()
        print(f"Result: {json.dumps(auth_result, indent=2)}")
        
        if auth_result['success']:
            print("\n✓ AUTHENTICATION SUCCESSFUL")
            print(f"  User: {auth_result.get('user_name')}")
            return True
        else:
            print("\n✗ AUTHENTICATION FAILED")
            print(f"  Error: {auth_result.get('error')}")
            return False
    else:
        print("\n✗ LOGIN FAILED")
        print(f"  Error: {login_result.get('error')}")
        return False

if __name__ == "__main__":
    success = test_login()
    sys.exit(0 if success else 1)
