"""
Test get_demat_holdings API to see account/portfolio information
This will show us what Breeze API returns for account identification
"""

import json
import requests
from app.config import Config

def test_demat_holdings():
    """Test demat holdings endpoint and show all returned data"""
    
    config = Config()
    session_token = config.BREEZE_SESSION_TOKEN_PINS
    api_key = config.BREEZE_API_KEY
    
    print("\n" + "="*80)
    print("BREEZE API - DEMAT HOLDINGS TEST")
    print("="*80)
    print(f"Session Token: {session_token}")
    print(f"User ID: {config.BREEZE_USER_ID_PINS}")
    
    try:
        url = "https://api.icicidirect.com/breezeapi/api/v1/dematholdings"
        
        # Call with minimal params first
        payload = {}
        
        headers = {"Content-Type": "application/json"}
        
        print(f"\nCalling: {url}")
        print(f"Payload: {json.dumps(payload)}")
        print(f"Headers: SessionToken={session_token[:20]}..., AppKey={api_key[:20]}...")
        
        response = requests.get(
            url,
            json=payload,
            headers=headers,
            params={"SessionToken": session_token, "AppKey": api_key},
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        data = response.json()
        
        print(f"\n{'='*80}")
        print("FULL API RESPONSE:")
        print(f"{'='*80}")
        print(json.dumps(data, indent=2))
        
        # Parse response
        if 'Success' in data and data['Success']:
            success_data = data['Success']
            
            print(f"\n{'='*80}")
            print("RESPONSE STRUCTURE:")
            print(f"{'='*80}")
            
            if isinstance(success_data, list):
                print(f"\nList of {len(success_data)} items:")
                if len(success_data) > 0:
                    print(f"\nFirst item keys:")
                    for key in success_data[0].keys():
                        print(f"  • {key}")
                    
                    print(f"\nFirst item data:")
                    print(json.dumps(success_data[0], indent=2))
                    
                    print(f"\n{'='*80}")
                    print("KEY FIELDS FOR ACCOUNT IDENTIFICATION:")
                    print(f"{'='*80}")
                    
                    key_fields = [
                        'DP_ID',
                        'DEPOSITORY_ID',
                        'CLIENT_ID',
                        'ACCOUNT_ID',
                        'PORTFOLIO_ID',
                        'DEMAT_ACCOUNT',
                        'ACCOUNT_TYPE',
                        'ACCOUNT_CATEGORY',
                        'profile',
                        'segment',
                        'type'
                    ]
                    
                    for field in key_fields:
                        value = success_data[0].get(field)
                        if value:
                            print(f"  {field}: {value}")
                    
                    print(f"\n{'='*80}")
                    print("ALL FIELDS RETURNED FOR FIRST HOLDING:")
                    print(f"{'='*80}")
                    for key, val in success_data[0].items():
                        print(f"  {key}: {val}")
            
            elif isinstance(success_data, dict):
                print(f"\nResponse is a dict with keys:")
                for key in success_data.keys():
                    print(f"  • {key}")
            else:
                print(f"\nResponse type: {type(success_data)}")
                print(f"Response: {success_data}")
        
        elif 'Error' in data:
            print(f"\n✗ API Error:")
            print(f"Error: {data.get('Error')}")
        
        return data
        
    except Exception as e:
        print(f"\n✗ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    test_demat_holdings()
