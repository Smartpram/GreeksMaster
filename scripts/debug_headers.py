#!/usr/bin/env python3
"""
Debug headers being sent to data endpoints
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.breeze_api import BreezeAPIService

def debug_headers():
    """Debug the headers being sent"""
    breeze = BreezeAPIService()
    
    # Authenticate first
    auth_result = breeze.authenticate()
    print(f"Authenticated: {auth_result['success']}")
    print(f"Session Token: {auth_result.get('session_token')}\n")
    
    # Check headers for empty payload
    print("Headers for endpoints with NO payload:")
    print("-" * 70)
    headers_empty = breeze.get_headers("")
    for k, v in headers_empty.items():
        if k == 'X-Checksum':
            print(f"{k}: {v[:50]}...")
        else:
            print(f"{k}: {v}")
    
    # Check headers for payload with parameters
    print("\n\nHeaders for endpoints WITH payload:")
    print("-" * 70)
    payload = {"exchange_code": "NSE"}
    headers_with_payload = breeze.get_headers(payload)
    for k, v in headers_with_payload.items():
        if k == 'X-Checksum':
            print(f"{k}: {v[:50]}...")
        else:
            print(f"{k}: {v}")

if __name__ == "__main__":
    debug_headers()
