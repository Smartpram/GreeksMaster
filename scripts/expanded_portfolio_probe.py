"""Expanded probe for get_portfolio_holdings permutations.

This script will iterate candidate account parameter names, exchange codes, date formats,
and method variants (POST/GET where applicable). It records every request+response to
the in-memory debug_store and prints a short summary at the end.

Run: python scripts/expanded_portfolio_probe.py
"""
import time
import json
from app.services.breeze_api import BreezeAPIService
from app.services.debug_store import record_fallback

SERVICE = BreezeAPIService()

KEYS = ['ucc','demat','customer_id','customerId','custid','client_id']
EXCHANGES = ['NFO','NSE']
DATE_RANGES = [
    # Quarter: Sep 2025 - Dec 2025 in various common formats
    ('2025-09-01T06:00:00.000Z','2025-12-31T06:00:00.000Z'),
    ('2025-09-01','2025-12-31'),
    # single-day sample within the quarter
    ('2025-11-15T06:00:00.000Z','2025-11-15T06:00:00.000Z'),
]
METHODS = ['POST']  # Breeze API generally expects POST for these endpoints; adapter may wrap GET

RATE_DELAY = 0.6  # seconds between requests to be polite

def ensure_auth():
    if not SERVICE.is_authenticated():
        SERVICE.authenticate()

def probe():
    ensure_auth()
    summary = []
    attempt = 0
    for key in KEYS:
        for exch in EXCHANGES:
            for (fd, td) in DATE_RANGES:
                for method in METHODS:
                    attempt += 1
                    payload = {
                        key: ''  # we'll try empty value first; individual account keys can be added later
                    }
                    # build request info
                    req_info = {
                        'endpoint': 'portfolio_holdings',
                        'method': method,
                        'exchange_code': exch,
                        'from_date': fd,
                        'to_date': td,
                        'param_key': key,
                        'payload': payload,
                    }

                    try:
                        # direct call to BreezeAPIService
                        resp = SERVICE.get_portfolio_holdings(exchange_code=exch, from_date=fd, to_date=td, stock_code='', portfolio_type='')
                        record_fallback({'probe': True, 'request': req_info, 'response': resp})
                        data_present = False
                        if isinstance(resp, dict):
                            # various clients return different shapes
                            if resp.get('success') and resp.get('data'):
                                data_present = True
                            elif resp.get('Success') and resp.get('Data'):
                                data_present = True
                        summary.append({'param_key': key, 'exchange': exch, 'from': fd, 'to': td, 'method': method, 'data_present': data_present, 'response_snippet': str(resp)[:200]})
                    except Exception as e:
                        record_fallback({'probe': True, 'request': req_info, 'error': str(e)})
                        summary.append({'param_key': key, 'exchange': exch, 'from': fd, 'to': td, 'method': method, 'data_present': False, 'error': str(e)})

                    time.sleep(RATE_DELAY)

    return summary

if __name__ == '__main__':
    s = probe()
    print('Probe attempts:', len(s))
    found = [x for x in s if x.get('data_present')]
    print('Found data present for', len(found), 'combinations')
    for f in found:
        print(f)
    # print a short sample
    print('\nSample results (first 10):')
    for r in s[:10]:
        print(r)
