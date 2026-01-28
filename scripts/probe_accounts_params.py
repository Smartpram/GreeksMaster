"""Probe different payload keys for funds and portfolio holdings for each stored account.

This script will try a small set of candidate key names for account scoping (ucc, demat, customer_id, account_no)
and call both `get_funds` and `get_portfolio_holdings` via the service factory. Results are printed and fallbacks
are recorded to `debug_store` for later inspection.
"""
import json
import os
from app.services.breeze_service_factory import get_breeze_service

ROOT = os.path.dirname(os.path.dirname(__file__))
ACCOUNTS_PATH = os.path.join(ROOT, 'app', 'data', 'accounts.json')

CANDIDATES = ['ucc', 'demat', 'customer_id', 'account_no', 'accountnumber', 'account']

svc = get_breeze_service()

with open(ACCOUNTS_PATH, 'r', encoding='utf-8') as f:
    accounts = json.load(f)

print('Service type:', type(svc))

for acct in accounts:
    print('\n=== Testing account', acct.get('ucc'), acct.get('demat'))
    for key in CANDIDATES:
        payload = {key: acct.get('ucc') or acct.get('demat')}
        print('\n- Trying payload key:', key)
        try:
            funds = None
            try:
                funds = svc.get_funds(**payload)
            except TypeError:
                funds = svc.get_funds()
            print('funds ->', json.dumps(funds, default=str)[:1000])
        except Exception as e:
            print('funds exception', e)

        try:
            holdings = None
            try:
                holdings = svc.get_portfolio_holdings(**payload)
            except TypeError:
                holdings = svc.get_portfolio_holdings()
            print('holdings ->', json.dumps(holdings, default=str)[:1000])
        except Exception as e:
            print('holdings exception', e)

print('\nProbe finished. Use /api/debug/fallbacks to view recorded fallback events (JSON).')
