"""
Test multiple endpoints to find account/portfolio information
"""

import json
from app.services.breeze_api import BreezeAPIService

def test_all_portfolio_endpoints():
    """Test all portfolio-related endpoints"""
    
    print("\n" + "="*80)
    print("BREEZE API - PORTFOLIO ENDPOINTS TEST")
    print("="*80)
    
    try:
        # Initialize service
        service = BreezeAPIService(account_type='PINS')
        
        print(f"\n1. Authenticating...")
        auth_result = service.authenticate()
        
        if not auth_result['success']:
            print(f"   ✗ Failed: {auth_result.get('error')}")
            return
        
        print(f"   ✓ Success")
        print(f"   User: {auth_result.get('user_name')}")
        print(f"   User ID: {auth_result.get('user_id')}")
        
        # Test endpoint 1: Portfolio
        print(f"\n{'='*80}")
        print("2. Testing: get_portfolio()")
        print(f"{'='*80}")
        
        result = service.get_portfolio()
        print(f"Result: {result.get('success')}")
        if result.get('data'):
            print(json.dumps(result['data'], indent=2)[:500])
        else:
            print(f"Data: {result.get('data')}")
        
        # Test endpoint 2: Portfolio Positions
        print(f"\n{'='*80}")
        print("3. Testing: get_portfolio_positions()")
        print(f"{'='*80}")
        
        result = service.get_portfolio_positions()
        print(f"Result: {result.get('success')}")
        if result.get('data'):
            data = result['data']
            if isinstance(data, list) and len(data) > 0:
                print(f"List with {len(data)} items")
                print(f"\nFirst item:")
                print(json.dumps(data[0], indent=2))
            else:
                print(json.dumps(data, indent=2)[:500])
        else:
            print(f"Data: {result.get('data')}")
        
        # Test endpoint 3: Portfolio Holdings
        print(f"\n{'='*80}")
        print("4. Testing: get_portfolio_holdings()")
        print(f"{'='*80}")
        
        result = service.get_portfolio_holdings(exchange_code="NSE")
        print(f"Result: {result.get('success')}")
        if result.get('data'):
            data = result['data']
            if isinstance(data, list) and len(data) > 0:
                print(f"List with {len(data)} items")
                print(f"\nFirst item:")
                print(json.dumps(data[0], indent=2))
                
                print(f"\n{'='*80}")
                print("ALL FIELDS IN RESPONSE:")
                print(f"{'='*80}")
                
                all_keys = set()
                for item in data:
                    all_keys.update(item.keys())
                
                for key in sorted(all_keys):
                    sample_value = data[0].get(key)
                    print(f"  {key}: {sample_value}")
            else:
                print(json.dumps(data, indent=2)[:500])
        else:
            print(f"Data: {result.get('data')}")
        
        # Test endpoint 4: Orders
        print(f"\n{'='*80}")
        print("5. Testing: get_order_list()")
        print(f"{'='*80}")
        
        result = service.get_order_list()
        print(f"Result: {result.get('success')}")
        if result.get('data'):
            data = result['data']
            if isinstance(data, list) and len(data) > 0:
                print(f"List with {len(data)} items")
                print(f"\nFirst order:")
                print(json.dumps(data[0], indent=2))
                
                print(f"\n{'='*80}")
                print("ALL FIELDS IN ORDER:")
                print(f"{'='*80}")
                
                all_keys = set()
                for item in data:
                    all_keys.update(item.keys())
                
                for key in sorted(all_keys):
                    sample_value = data[0].get(key)
                    print(f"  {key}: {sample_value}")
            else:
                print(f"Empty list or single item: {data}")
        else:
            print(f"Data: {result.get('data')}")
        
    except Exception as e:
        print(f"✗ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_all_portfolio_endpoints()
