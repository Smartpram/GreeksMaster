#!/usr/bin/env python3
"""
Comprehensive Breeze API validation test
Tests all fixed functionality end-to-end
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.breeze_api import BreezeAPIService
import json

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_subsection(title):
    print(f"\n  {title}")
    print("  " + "-" * 76)

def format_success(result, show_data=False):
    if result.get('success'):
        if show_data and result.get('data'):
            return f"✅ SUCCESS - {json.dumps(result['data'], indent=2)[:200]}..."
        else:
            return "✅ SUCCESS"
    else:
        error = result.get('error', 'Unknown error')
        return f"❌ FAILED - {error[:100]}"

def main():
    print_section("BREEZE API INTEGRATION TEST SUITE")
    
    breeze = BreezeAPIService()
    test_results = {
        'total': 0,
        'passed': 0,
        'failed': 0
    }
    
    # Test 1: Authentication
    print_subsection("1. Testing Authentication")
    test_results['total'] += 1
    auth_result = breeze.authenticate()
    if auth_result['success']:
        test_results['passed'] += 1
        print(f"  ✅ Authentication successful")
        print(f"     User: {auth_result['user_name']}")
        print(f"     UserID: {auth_result['user_id']}")
        print(f"     Session Token: {auth_result['session_token'][:20]}...")
        print(f"     Trading Allowed: {auth_result['segments'].get('Trading')}")
        print(f"     Equity Allowed: {auth_result['segments'].get('Equity')}")
        print(f"     Derivatives Allowed: {auth_result['segments'].get('Derivatives')}")
    else:
        test_results['failed'] += 1
        print(f"  ❌ Authentication failed: {auth_result.get('error')}")
        print("\n  Hint: Visit the login URL to get a fresh session token:")
        print("  python get_session_token.py")
        return test_results
    
    # Test 2: Get Customer Details
    print_subsection("2. Testing Get Customer Details")
    test_results['total'] += 1
    customer_result = breeze.get_customer_details()
    if customer_result['success']:
        test_results['passed'] += 1
        print(f"  ✅ Customer details retrieved")
        print(f"     Name: {customer_result['user_name']}")
        print(f"     Last Login: {customer_result['last_login']}")
    else:
        test_results['failed'] += 1
        print(f"  ❌ Failed: {customer_result.get('error')}")
    
    # Test 3: Get Funds
    print_subsection("3. Testing Get Funds")
    test_results['total'] += 1
    funds_result = breeze.get_funds()
    if funds_result['success']:
        test_results['passed'] += 1
        funds = funds_result.get('data', {})
        print(f"  ✅ Funds retrieved")
        print(f"     Bank Account: {funds.get('bank_account')}")
        print(f"     Total Balance: ₹{funds.get('total_bank_balance', 0):.2f}")
        print(f"     Unallocated Balance: ₹{funds.get('unallocated_balance', 0)}")
    else:
        test_results['failed'] += 1
        print(f"  ❌ Failed: {funds_result.get('error')}")
    
    # Test 4: Get Demat Holdings
    print_subsection("4. Testing Get Demat Holdings")
    test_results['total'] += 1
    demat_result = breeze.get_demat_holdings()
    if demat_result['success']:
        test_results['passed'] += 1
        holdings = demat_result.get('data')
        if holdings:
            print(f"  ✅ Demat holdings retrieved ({len(holdings)} holdings)")
        else:
            print(f"  ✅ No demat holdings found (account is empty)")
    else:
        test_results['failed'] += 1
        print(f"  ❌ Failed: {demat_result.get('error')}")
    
    # Test 5: Get Portfolio Positions
    print_subsection("5. Testing Get Portfolio Positions")
    test_results['total'] += 1
    positions_result = breeze.get_portfolio_positions()
    if positions_result['success']:
        test_results['passed'] += 1
        positions = positions_result.get('data')
        if positions:
            print(f"  ✅ Portfolio positions retrieved ({len(positions)} positions)")
        else:
            print(f"  ✅ No open positions found (account is empty)")
    else:
        test_results['failed'] += 1
        print(f"  ❌ Failed: {positions_result.get('error')}")
    
    # Test 6: Get Quotes
    print_subsection("6. Testing Get Quotes (ITC)")
    test_results['total'] += 1
    quotes_result = breeze.get_quotes(stock_code="ITC", exchange_code="NSE")
    if quotes_result['success']:
        test_results['passed'] += 1
        quotes = quotes_result.get('data', [])
        if quotes:
            for quote in quotes:
                print(f"  ✅ Quote retrieved for {quote['stock_code']} ({quote['exchange_code']})")
                print(f"     LTP: ₹{quote.get('ltp')}")
                print(f"     Open: ₹{quote.get('open')}")
                print(f"     High: ₹{quote.get('high')}")
                print(f"     Low: ₹{quote.get('low')}")
                print(f"     % Change: {quote.get('ltp_percent_change')}%")
        else:
            print(f"  ⚠️  No quotes found")
    else:
        test_results['failed'] += 1
        print(f"  ❌ Failed: {quotes_result.get('error')}")
    
    # Test 7: Get Portfolio Holdings
    print_subsection("7. Testing Get Portfolio Holdings")
    test_results['total'] += 1
    holdings_result = breeze.get_portfolio_holdings(exchange_code="NSE")
    if holdings_result['success']:
        test_results['passed'] += 1
        holdings = holdings_result.get('data')
        if holdings:
            print(f"  ✅ Portfolio holdings retrieved ({len(holdings)} holdings)")
        else:
            print(f"  ✅ No portfolio holdings found (account is empty)")
    else:
        test_results['failed'] += 1
        print(f"  ❌ Failed: {holdings_result.get('error')}")
    
    # Test 8: Check if authenticated
    print_subsection("8. Testing Authentication Status Check")
    test_results['total'] += 1
    if breeze.is_authenticated():
        test_results['passed'] += 1
        print(f"  ✅ Authentication status: AUTHENTICATED")
    else:
        test_results['failed'] += 1
        print(f"  ❌ Authentication status: NOT AUTHENTICATED")
    
    # Summary
    print_section("TEST SUMMARY")
    print(f"\n  Total Tests: {test_results['total']}")
    print(f"  Passed: {test_results['passed']} ✅")
    print(f"  Failed: {test_results['failed']} ❌")
    success_rate = (test_results['passed'] / test_results['total'] * 100) if test_results['total'] > 0 else 0
    print(f"  Success Rate: {success_rate:.1f}%")
    
    if test_results['failed'] == 0:
        print("\n  🎉 ALL TESTS PASSED! Breeze API is working correctly.")
    else:
        print(f"\n  ⚠️  {test_results['failed']} test(s) failed. Please check the errors above.")
    
    print("\n" + "=" * 80 + "\n")
    
    return test_results

if __name__ == "__main__":
    results = main()
    sys.exit(0 if results['failed'] == 0 else 1)
