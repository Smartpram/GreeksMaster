"""
Test portfolio holdings with all parameters to find account info
"""

import json
from datetime import datetime, timedelta
from app.services.breeze_api import BreezeAPIService

def test_portfolio_holdings_detailed():
    """Test portfolio holdings with various parameters"""
    
    print("\n" + "="*80)
    print("DETAILED PORTFOLIO HOLDINGS TEST")
    print("="*80)
    
    try:
        service = BreezeAPIService(account_type='PINS')
        
        print(f"\n1. Authenticating...")
        auth_result = service.authenticate()
        
        if not auth_result['success']:
            print(f"   ✗ Failed: {auth_result.get('error')}")
            return
        
        print(f"   ✓ Authenticated: {auth_result.get('user_name')}")
        
        # Get dates
        end_date = datetime.now().strftime("%d-%m-%Y")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%d-%m-%Y")
        
        print(f"\n2. Testing get_portfolio_holdings with date range:")
        print(f"   Start: {start_date}")
        print(f"   End: {end_date}")
        
        # Test with different parameters
        params_list = [
            {
                'description': 'NSE Equity only',
                'exchange_code': 'NSE',
                'from_date': start_date,
                'to_date': end_date
            },
            {
                'description': 'All exchanges, no stock filter',
                'exchange_code': 'ALL',
                'from_date': start_date,
                'to_date': end_date
            },
            {
                'description': 'NFO (Derivatives)',
                'exchange_code': 'NFO',
                'from_date': start_date,
                'to_date': end_date
            },
            {
                'description': 'MCX (Commodities)',
                'exchange_code': 'MCX',
                'from_date': start_date,
                'to_date': end_date
            }
        ]
        
        for params in params_list:
            desc = params.pop('description')
            print(f"\n{'-'*80}")
            print(f"Test: {desc}")
            print(f"{'-'*80}")
            
            result = service.get_portfolio_holdings(**params)
            
            print(f"Success: {result.get('success')}")
            
            if result.get('data'):
                data = result['data']
                
                if isinstance(data, list):
                    print(f"Result: List with {len(data)} items")
                    
                    if len(data) > 0:
                        print(f"\nFirst item:")
                        first = data[0]
                        print(json.dumps(first, indent=2))
                        
                        print(f"\nAll fields in response:")
                        all_keys = set()
                        for item in data:
                            all_keys.update(item.keys())
                        
                        for key in sorted(all_keys):
                            print(f"  • {key}")
                else:
                    print(f"Result type: {type(data)}")
                    print(json.dumps(str(data)[:200]))
            else:
                print(f"Data: {result.get('data')}")
                if result.get('error'):
                    print(f"Error: {result.get('error')}")
        
        # Also test order book
        print(f"\n{'='*80}")
        print("3. Testing get_order_book()")
        print(f"{'='*80}")
        
        result = service.get_order_list(exchange_code="NSE")
        
        if result.get('success'):
            data = result['data']
            if isinstance(data, list) and len(data) > 0:
                print(f"Orders: {len(data)} items")
                print(f"\nFirst order:")
                print(json.dumps(data[0], indent=2))
        else:
            print(f"Error: {result.get('error')}")
        
    except Exception as e:
        print(f"✗ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_portfolio_holdings_detailed()
