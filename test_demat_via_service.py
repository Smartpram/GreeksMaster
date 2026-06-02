"""
Test demat holdings using BreezeAPIService
This will show what account information is available
"""

import json
from app.services.breeze_api import BreezeAPIService

def test_demat_holdings_via_service():
    """Test demat holdings using the service"""
    
    print("\n" + "="*80)
    print("BREEZE API - DEMAT HOLDINGS (Via Service)")
    print("="*80)
    
    try:
        # Initialize service
        service = BreezeAPIService(account_type='PINS')
        
        print(f"\n1. Authenticating...")
        auth_result = service.authenticate()
        
        if not auth_result['success']:
            print(f"   ✗ Authentication failed: {auth_result.get('error')}")
            return
        
        print(f"   ✓ Authenticated")
        print(f"   User: {auth_result.get('user_name')}")
        print(f"   User ID: {auth_result.get('user_id')}")
        
        print(f"\n2. Calling get_demat_holdings()...")
        result = service.get_demat_holdings()
        
        print(f"\n{'='*80}")
        print("API RESPONSE:")
        print(f"{'='*80}")
        
        if result['success']:
            holdings = result['data']
            
            # Check if it's a list
            if isinstance(holdings, list):
                print(f"\nReturned list of {len(holdings)} items\n")
                
                if len(holdings) > 0:
                    print("FIRST HOLDING STRUCTURE:")
                    print("-"*80)
                    
                    first = holdings[0]
                    print(json.dumps(first, indent=2))
                    
                    print(f"\n{'='*80}")
                    print("ALL FIELDS IN HOLDINGS:")
                    print(f"{'='*80}")
                    
                    all_keys = set()
                    for holding in holdings:
                        all_keys.update(holding.keys())
                    
                    for key in sorted(all_keys):
                        print(f"  • {key}")
                    
                    print(f"\n{'='*80}")
                    print("UNIQUE VALUES FOR ACCOUNT IDENTIFICATION:")
                    print(f"{'='*80}")
                    
                    # Look for unique/identifier fields
                    identifier_candidates = [
                        'BranchCode',
                        'DPId',
                        'DP_ID',
                        'ClientId',
                        'CLIENT_ID',
                        'DematAccount',
                        'DEMAT_ACCOUNT',
                        'DeMatAccount',
                        'AccountType',
                        'ACCOUNT_TYPE',
                        'Profile',
                        'PROFILE',
                        'Segment',
                        'SEGMENT',
                        'PortfolioType',
                        'PORTFOLIO_TYPE'
                    ]
                    
                    found_identifiers = False
                    for field in identifier_candidates:
                        for holding in holdings:
                            if field in holding:
                                value = holding[field]
                                if value:
                                    print(f"  {field}: {value}")
                                    found_identifiers = True
                                break
                    
                    if not found_identifiers:
                        print("  No standard identifier fields found")
                        print("\n  (Check field list above for custom identifiers)")
            else:
                print(f"Response type: {type(holdings)}")
                print(json.dumps(holdings, indent=2))
        else:
            print(f"✗ Error: {result.get('error')}")
            
    except Exception as e:
        print(f"✗ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_demat_holdings_via_service()
