"""
Non-interactive smoke test for Breeze API
Calls: authenticate, customer details, demat holdings, portfolio positions, funds, quotes
"""
from app.services.breeze_api import BreezeAPIService

def pretty_print(title, data):
    print('\n' + '='*60)
    print(title)
    print('-'*60)
    print(data)

if __name__ == '__main__':
    api = BreezeAPIService()

    auth = api.authenticate()
    pretty_print('AUTH RESULT', auth)

    if auth.get('success'):
        cust = api.get_customer_details()
        pretty_print('CUSTOMER DETAILS', cust)

        demat = api.get_demat_holdings()
        pretty_print('DEMAT HOLDINGS', demat)

        pos = api.get_portfolio_positions()
        pretty_print('PORTFOLIO POSITIONS', pos)

        funds = api.get_funds()
        pretty_print('FUNDS', funds)

        quotes = api.get_quotes('ITC', 'NSE')
        pretty_print('QUOTES ITC', quotes)
    else:
        print('\nAuthentication failed; skipping further API calls.')
