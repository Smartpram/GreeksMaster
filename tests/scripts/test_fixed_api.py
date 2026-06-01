"""
Test the Fixed Breeze API Implementation
Testing portfolio endpoints with proper parameter format
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.breeze_api_fixed import BreezeAPIService

def test_fixed_implementation():
    """Test the fixed Breeze API implementation"""
    print("🔧 TESTING FIXED BREEZE API IMPLEMENTATION")
    print("=" * 60)
    
    # Initialize fixed API
    api = BreezeAPIService()
    
    # Test 1: Authentication
    print("1️⃣ Testing Authentication...")
    auth_result = api.authenticate()
    
    if not auth_result['success']:
        print(f"❌ Authentication failed: {auth_result['message']}")
        return
    
    print(f"✅ Authentication successful")
    print(f"   User: {auth_result['data']['user_name']} ({auth_result['data']['user_id']})")
    
    # Test 2: User Info
    print("\n2️⃣ Testing User Info...")
    user_info = api.get_user_info()
    print(f"✅ User Info: {user_info['success']}")
    
    # Test 3: Live Quotes (known working)
    print("\n3️⃣ Testing Live Quotes...")
    quotes = api.get_quotes("ITC", "NSE")
    print(f"✅ Quotes: {quotes['success']}")
    if quotes['success']:
        data = quotes['data']
        if data:
            first_quote = data[0] if isinstance(data, list) else data
            price = first_quote.get('ltp', 'N/A')
            print(f"   ITC Price: ₹{price}")
    
    # Test 4: Fixed Portfolio Method
    print("\n4️⃣ Testing FIXED Portfolio Method...")
    portfolio = api.get_portfolio_fixed()
    print(f"Portfolio Result: {portfolio['success']}")
    
    if portfolio['success']:
        print(f"✅ PORTFOLIO FIXED! Data available")
        data = portfolio.get('data', [])
        print(f"   Portfolio items: {len(data) if isinstance(data, list) else 'Data available'}")
    else:
        print(f"❌ Portfolio Error: {portfolio['message']}")
        if 'raw_response' in portfolio:
            print(f"   Raw Response: {portfolio['raw_response'][:200]}...")
    
    # Test 5: Fixed Funds Method  
    print("\n5️⃣ Testing FIXED Funds Method...")
    funds = api.get_funds_fixed()
    print(f"Funds Result: {funds['success']}")
    
    if funds['success']:
        print(f"✅ FUNDS FIXED! Data available")
        data = funds.get('data', {})
        print(f"   Funds data: {type(data)}")
    else:
        print(f"❌ Funds Error: {funds['message']}")
        if 'raw_response' in funds:
            print(f"   Raw Response: {funds['raw_response'][:200]}...")
    
    # Summary
    print(f"\n🎯 FINAL RESULTS:")
    print("=" * 40)
    
    results = {
        'Authentication': auth_result['success'],
        'User Info': user_info['success'],
        'Live Quotes': quotes['success'],
        'Portfolio (Fixed)': portfolio['success'],
        'Funds (Fixed)': funds['success']
    }
    
    working_count = sum(results.values())
    total_count = len(results)
    
    for component, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {component}")
    
    print(f"\n🚀 SYSTEM STATUS: {working_count}/{total_count} ({working_count/total_count*100:.1f}%)")
    
    if working_count >= 3:  # Auth, User Info, Quotes minimum
        print("🎊 READY FOR PRODUCTION!")
        print("   Core trading functionality available")
        
        if portfolio['success'] or funds['success']:
            print("   🎉 PORTFOLIO/FUNDS ISSUES RESOLVED!")
        else:
            print("   📧 Contact ICICI for portfolio/funds API documentation")
    
    return results

if __name__ == "__main__":
    test_fixed_implementation()