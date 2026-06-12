"""
Test PINS account and return full API response
"""

import json
import requests
from app.config import Config

def test_pins_account():
    """Test PINS account and show all API response fields"""
    
    config = Config()
    session_token = config.BREEZE_SESSION_TOKEN_PINS
    api_key = config.BREEZE_API_KEY
    
    print("\n" + "="*80)
    print("BREEZE API RESPONSE FOR PINS ACCOUNT")
    print("="*80)
    print(f"Session Token: {session_token}")
    print(f"API Key: {api_key[:20]}...")
    
    try:
        url = "https://api.icicidirect.com/breezeapi/api/v1/customerdetails"
        payload = {
            "SessionToken": session_token,
            "AppKey": api_key
        }
        headers = {"Content-Type": "application/json"}
        
        print(f"\nCalling: {url}")
        response = requests.get(url, json=payload, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}\n")
        
        data = response.json()
        
        if 'Success' in data and data['Success']:
            success_data = data['Success']
            
            print("✓ AUTHENTICATION SUCCESSFUL\n")
            print("FULL API RESPONSE:")
            print("-"*80)
            print(json.dumps(success_data, indent=2))
            
            print("\n" + "-"*80)
            print("KEY FIELDS FOR ACCOUNT IDENTIFICATION:")
            print("-"*80)
            
            key_fields = [
                'idirect_user_name',
                'idirect_userid',
                'idirect_brokerage_name',
                'idirect_brokerage_id',
                'idirect_demat_id',
                'idirect_email',
                'idirect_phone_no',
                'idirect_login_id',
                'idirect_trading_account_type',
                'segments_allowed',
            ]
            
            for field in key_fields:
                value = success_data.get(field)
                if value is not None:
                    print(f"  {field}: {value}")
                else:
                    print(f"  {field}: <NOT PROVIDED>")
            
            print("\n" + "-"*80)
            print("ALL FIELDS RETURNED BY API:")
            print("-"*80)
            for key in sorted(success_data.keys()):
                print(f"  • {key}")
                
            return success_data
        else:
            print(f"✗ Authentication failed")
            print(f"Error: {data.get('Error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"✗ Exception: {e}")
        return None

if __name__ == '__main__':
    test_pins_account()
