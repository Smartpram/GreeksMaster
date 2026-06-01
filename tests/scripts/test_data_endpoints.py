#!/usr/bin/env python3
"""
Test data endpoints with current authentication
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.breeze_api import BreezeAPIService
import json

def test_data_endpoints():
    """Test all data endpoints"""
    print("=" * 70)
    print("DATA ENDPOINTS TEST")
    print("=" * 70)
    
    breeze = BreezeAPIService()
    
    # First authenticate
    print("\n1. AUTHENTICATING...")
    auth_result = breeze.authenticate()
    print(f"Auth: {auth_result['success']}")
    print(f"User: {auth_result.get('user_name')}")
    print(f"Session Token: {auth_result.get('session_token')[:30]}...")
    
    if not auth_result['success']:
        print("Authentication failed!")
        return
    
    # Now test each endpoint
    print("\n2. TESTING DEMAT HOLDINGS")
    print("-" * 70)
    result = breeze.get_demat_holdings()
    print(json.dumps(result, indent=2)[:500])
    
    print("\n3. TESTING PORTFOLIO POSITIONS")
    print("-" * 70)
    result = breeze.get_portfolio_positions()
    print(json.dumps(result, indent=2)[:500])
    
    print("\n4. TESTING FUNDS")
    print("-" * 70)
    result = breeze.get_funds()
    print(json.dumps(result, indent=2)[:500])
    
    print("\n5. TESTING PORTFOLIO HOLDINGS (with date range)")
    print("-" * 70)
    result = breeze.get_portfolio_holdings()
    print(json.dumps(result, indent=2)[:500])

if __name__ == "__main__":
    test_data_endpoints()
