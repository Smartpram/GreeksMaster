"""
Test Multiple Accounts Detection for ICICI Breeze API
Check if multiple accounts are causing portfolio retrieval issues
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.breeze_api import BreezeAPIService
import json
import requests

def test_multiple_accounts():
    """Test and detect multiple accounts under same login"""
    print("🔍 TESTING MULTIPLE ACCOUNTS DETECTION")
    print("=" * 60)
    
    # Initialize API
    api = BreezeAPIService()
    
    # Step 1: Authenticate and get user info
    print("1️⃣ Authenticating...")
    auth_result = api.authenticate()
    
    if not auth_result['success']:
        print(f"❌ Authentication failed: {auth_result['message']}")
        return
    
    print(f"✅ Authentication successful")
    
    # Print available data keys to understand structure
    if 'data' in auth_result:
        data_keys = list(auth_result['data'].keys())
        print(f"   Available data fields: {data_keys}")
        
        # Try to find user identifier
        user_id = auth_result['data'].get('user_id') or auth_result['data'].get('client_code') or auth_result['data'].get('userid')
        user_name = auth_result['data'].get('user_name') or auth_result['data'].get('client_name') or auth_result['data'].get('name')
        
        print(f"   User ID: {user_id}")
        print(f"   User Name: {user_name}")
    
    # Step 2: Check user info for account details
    print("\n2️⃣ Checking User Information for Account Details...")
    user_info = api.get_user_info()
    
    print("📋 Full User Info:")
    print(json.dumps(user_info, indent=2))
    
    # Step 3: Look for account-related fields
    print("\n3️⃣ Analyzing Account Structure...")
    
    # Check both auth result and user info
    all_data = {}
    if 'data' in auth_result:
        all_data.update(auth_result['data'])
    if user_info.get('success') and 'user_id' in user_info:
        all_data.update({
            'user_id': user_info['user_id'],
            'user_name': user_info['user_name']
        })
    
    print("🔍 All Available Fields:")
    for key, value in all_data.items():
        print(f"   📌 {key}: {value}")
    
    # Check for multiple account indicators
    account_indicators = [
        'client_code', 'client_id', 'account_id', 'account_code',
        'trading_code', 'demat_account', 'accounts', 'client_codes',
        'idirect_userid', 'user_id', 'segments_allowed'
    ]
    
    print("\n🔍 Account-related fields analysis:")
    found_accounts = []
    
    for field in account_indicators:
        if field in all_data:
            value = all_data[field]
            print(f"   📌 {field}: {value}")
            if field == 'segments_allowed' and isinstance(value, dict):
                print(f"      Segments: {list(value.keys())}")
            elif isinstance(value, list) and len(value) > 1:
                found_accounts.extend(value)
            elif value and field not in ['segments_allowed']:
                found_accounts.append(str(value))
    
    # Step 4: Test specific account scenarios
    print(f"\n4️⃣ Testing Multiple Account Scenarios...")
    
    # Check if user_id and idirect_userid are different (common multiple account indicator)
    user_id = all_data.get('user_id')
    idirect_id = all_data.get('idirect_userid')
    
    if user_id and idirect_id and user_id != idirect_id:
        print("⚠️  MULTIPLE ACCOUNT INDICATOR FOUND!")
        print(f"   API User ID: {user_id}")
        print(f"   ICICI Direct ID: {idirect_id}")
        print("   These different IDs suggest multiple accounts under same login")
        
        # Test portfolio with both IDs
        print("\n📊 Testing Portfolio with Different Account IDs...")
        
        # Test 1: With API user_id
        print(f"\n   Testing with API User ID ({user_id})...")
        try:
            result = api.get_portfolio_with_account_id(user_id)
            print(f"   Result: {result.get('success', False)}")
            if result.get('success'):
                print(f"   ✅ Portfolio retrieved with API User ID!")
            else:
                print(f"   ❌ Error: {result.get('message', 'Unknown')}")
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
        
        # Test 2: With ICICI Direct ID
        print(f"\n   Testing with ICICI Direct ID ({idirect_id})...")
        try:
            result = api.get_portfolio_with_account_id(idirect_id)
            print(f"   Result: {result.get('success', False)}")
            if result.get('success'):
                print(f"   ✅ Portfolio retrieved with ICICI Direct ID!")
            else:
                print(f"   ❌ Error: {result.get('message', 'Unknown')}")
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
    
    # Step 5: Test standard portfolio call
    print(f"\n📊 Testing Standard Portfolio Call...")
    portfolio = api.get_portfolio()
    print(f"Result: {portfolio.get('success', False)}")
    if not portfolio.get('success'):
        print(f"Error: {portfolio.get('message', 'Unknown error')}")
    else:
        print(f"✅ Portfolio data retrieved successfully!")
    
    # Step 6: Recommendations
    print(f"\n5️⃣ Analysis Results:")
    
    if user_id and idirect_id and user_id != idirect_id:
        print("⚠️  MULTIPLE ACCOUNTS DETECTED!")
        print(f"   This explains portfolio retrieval issues")
        print("\n💡 SOLUTIONS:")
        print("   1. Use specific account_id parameter in portfolio calls")
        print("   2. Test with both user IDs to find the correct one")
        print("   3. Contact ICICI for multi-account API documentation")
        print(f"   4. Try account-specific parameters in API calls")
    else:
        print("✅ Single account scenario - issue might be:")
        print("   1. API permissions for portfolio data")
        print("   2. Data availability timing")
        print("   3. Endpoint-specific parameters needed")
    
    print(f"\n6️⃣ Next Steps:")
    print("   1. If multiple accounts: Get account-specific API documentation")
    print("   2. Test with specific account parameters")
    print("   3. Consider using working endpoints (quotes) for now")

def add_portfolio_with_exchange_method():
    """Add method to test portfolio with exchange parameter"""
    print("\n🔧 Adding portfolio test method with exchange parameter...")
    
    # This will be added to the BreezeAPIService class
    portfolio_method = '''
    def get_portfolio_with_exchange(self, exchange_code: str = "NSE") -> Dict:
        """Get portfolio with specific exchange code"""
        try:
            url = f"{self.base_url}/portfolioholdings"
            
            payload = {
                "SessionToken": self.authenticated_session_token,
                "AppKey": self.api_key,
                "exchange_code": exchange_code
            }
            
            checksum = self._generate_checksum(payload)
            payload["checksum"] = checksum
            
            response = requests.get(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'Success' in data:
                    return {
                        'success': True,
                        'data': data['Success'],
                        'exchange': exchange_code
                    }
            
            return {
                'success': False,
                'message': f'Portfolio retrieval failed for {exchange_code}',
                'status_code': response.status_code
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Portfolio error for {exchange_code}: {str(e)}'
            }
    '''
    
    return portfolio_method

if __name__ == "__main__":
    # Add the portfolio method to API service
    portfolio_method = add_portfolio_with_exchange_method()
    
    # Add method to BreezeAPIService class dynamically
    import types
    
    def get_portfolio_with_exchange(self, exchange_code: str = "NSE"):
        """Get portfolio with specific exchange code"""
        try:
            url = f"{self.base_url}/portfolioholdings"
            
            payload = {
                "SessionToken": self.authenticated_session_token,
                "AppKey": self.api_key,
                "exchange_code": exchange_code
            }
            
            checksum = self._generate_checksum(payload)
            payload["checksum"] = checksum
            
            response = requests.get(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'Success' in data:
                    return {
                        'success': True,
                        'data': data['Success'],
                        'exchange': exchange_code
                    }
            
            return {
                'success': False,
                'message': f'Portfolio retrieval failed for {exchange_code}',
                'status_code': response.status_code
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Portfolio error for {exchange_code}: {str(e)}'
            }
    
    def get_portfolio_with_account_id(self, account_id: str):
        """Get portfolio with specific account ID"""
        try:
            url = f"{self.base_url}/portfolioholdings"
            
            payload = {
                "SessionToken": self.authenticated_session_token,
                "AppKey": self.api_key,
                "client_code": account_id
            }
            
            checksum = self._generate_checksum(payload)
            payload["checksum"] = checksum
            
            response = requests.get(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'Success' in data:
                    return {
                        'success': True,
                        'data': data['Success'],
                        'account_id': account_id
                    }
            
            return {
                'success': False,
                'message': f'Portfolio retrieval failed for account {account_id}',
                'status_code': response.status_code,
                'response': response.text
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Portfolio error for account {account_id}: {str(e)}'
            }
    
    # Add methods to class
    BreezeAPIService.get_portfolio_with_exchange = get_portfolio_with_exchange
    BreezeAPIService.get_portfolio_with_account_id = get_portfolio_with_account_id
    
    # Run the test
    test_multiple_accounts()