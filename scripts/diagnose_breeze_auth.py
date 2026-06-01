"""
Diagnostic script to identify Breeze API authentication issues
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from app.config import Config

config = Config()

print("=" * 70)
print("BREEZE API AUTHENTICATION DIAGNOSTIC")
print("=" * 70)

# 1. Check configuration
print("\n1. CONFIGURATION CHECK")
print("-" * 70)
print(f"   API Key:       {config.BREEZE_API_KEY[:20]}...")
print(f"   Secret Key:    {config.BREEZE_SECRET_KEY[:20]}...")
print(f"   Session Token: {config.BREEZE_SESSION_TOKEN}")
print(f"   User ID:       {config.BREEZE_USER_ID}")
print(f"   Base URL:      https://api.icicidirect.com/breezeapi/api/v1")

# 2. Test connectivity
print("\n2. CONNECTIVITY TEST")
print("-" * 70)
try:
    # Test basic connectivity to the API
    test_url = "https://api.icicidirect.com/breezeapi/documents/index.html"
    resp = requests.head(test_url, timeout=10)
    print(f"   ✓ API Server reachable (HTTP {resp.status_code})")
except Exception as e:
    print(f"   ✗ Cannot reach API server: {e}")

# 3. Test authentication endpoint
print("\n3. AUTHENTICATION ENDPOINT TEST")
print("-" * 70)

url = "https://api.icicidirect.com/breezeapi/api/v1/customerdetails"
payload = {
    "SessionToken": config.BREEZE_SESSION_TOKEN,
    "AppKey": config.BREEZE_API_KEY
}
headers = {"Content-Type": "application/json"}

try:
    print(f"   URL: {url}")
    print(f"   Method: GET")
    print(f"   Payload: {json.dumps(payload, indent=6)}")
    print(f"   Headers: {json.dumps(headers, indent=6)}")
    
    response = requests.get(url, json=payload, headers=headers, timeout=30)
    
    print(f"\n   Response Status: HTTP {response.status_code}")
    print(f"   Response Body:\n{json.dumps(response.json(), indent=6)}")
    
    if response.status_code == 200:
        if 'Success' in response.json():
            print("\n   ✓ AUTHENTICATION SUCCESSFUL")
        else:
            print("\n   ✗ Response received but no Success key")
    else:
        print(f"\n   ✗ HTTP {response.status_code} - {response.reason}")
        
except requests.exceptions.Timeout:
    print("\n   ✗ Request timed out (API not responding)")
except requests.exceptions.ConnectionError as e:
    print(f"\n   ✗ Connection error: {e}")
except Exception as e:
    print(f"\n   ✗ Error: {e}")

# 4. Diagnosis summary
print("\n4. DIAGNOSIS SUMMARY")
print("-" * 70)

print("""
POSSIBLE ISSUES:
  
  1. INVALID SESSION TOKEN
     - The session token '54512344' may be expired or incorrect
     - Solution: Get a fresh session token from ICICI Direct portal
  
  2. INVALID API KEY
     - The AppKey may be incorrect or deactivated
     - Solution: Verify AppKey in ICICI Direct API settings
  
  3. API SERVER DOWN
     - The API endpoint may be temporarily unavailable
     - Solution: Check ICICI Direct system status or try again later
  
  4. NETWORK/FIREWALL ISSUE
     - Your firewall may be blocking access to the API
     - Solution: Check firewall rules or try from different network
  
  5. WRONG USER ID / CREDENTIALS MISMATCH
     - The UserID may not match the API credentials
     - Solution: Verify all credentials are from same ICICI Direct account

RECOMMENDED NEXT STEPS:
  
  ✓ Verify SessionToken is valid (check ICICI Direct portal)
  ✓ Confirm API Key and Secret Key are correct
  ✓ Check if API credentials are still active in your account
  ✓ Test with curl or Postman to isolate the issue
  ✓ Contact ICICI Direct support if credentials are correct
""")

print("=" * 70)
