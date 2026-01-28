"""Probe get_portfolio_holdings using actual account identifiers from data/accounts.json.

This will map each account's ucc/demat into candidate parameter names and call the direct
Breeze API client. All attempts are recorded to debug_store.
"""
import time
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from app.services.breeze_api import BreezeAPIService
from app.services.debug_store import record_fallback

SERVICE = BreezeAPIService()

KEYS = ['ucc','demat','customer_id','customerId','custid','client_id']
EXCHANGES = ['NFO','NSE']
DATE_RANGES = [
    ('2025-09-01T06:00:00.000Z','2025-12-31T06:00:00.000Z'),
    ('2025-09-01','2025-12-31'),
    ('2025-11-15T06:00:00.000Z','2025-11-15T06:00:00.000Z'),
]
RATE_DELAY = 0.6

BASE_URL = SERVICE.base_url
TIMEOUT = 15

def make_session():
    s = requests.Session()
    retries = Retry(total=2, backoff_factor=0.5, status_forcelist=[429,500,502,503,504], allowed_methods=frozenset(['GET','POST']))
    adapter = HTTPAdapter(max_retries=retries)
    s.mount('https://', adapter)
    s.mount('http://', adapter)
    return s

def load_accounts():
    import os
    path = os.path.join('app','data','accounts.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def ensure_auth():
    if not SERVICE.is_authenticated():
        SERVICE.authenticate()

def probe():
    accounts = load_accounts()
    ensure_auth()
    summary = []
    session = make_session()
    for acct in accounts:
        for key in KEYS:
            # decide whether to use ucc or demat value
            for val_key in ('ucc','demat'):
                val = acct.get(val_key)
                if not val:
                    continue
                for exch in EXCHANGES:
                    for (fd, td) in DATE_RANGES:
                        req_info = {
                            'endpoint': 'portfolio_holdings',
                            'exchange_code': exch,
                            'from_date': fd,
                            'to_date': td,
                            'param_used': key,
                            'param_value': val,
                            'account_ucc': acct.get('ucc'),
                            'account_demat': acct.get('demat')
                        }
                        try:
                            # Build payload and call endpoint directly using requests so we can include arbitrary keys
                            payload = {
                                'exchange_code': exch,
                                'from_date': fd,
                                'to_date': td,
                                'stock_code': '',
                                'portfolio_type': ''
                            }
                            payload[key] = val
                            headers = SERVICE.get_headers(payload)
                            url = f"{BASE_URL}/portfolioholdings"
                            resp_http = session.post(url, json=payload, headers=headers, timeout=TIMEOUT)

                            try:
                                resp_json = resp_http.json()
                            except Exception:
                                resp_json = {'raw_text': resp_http.text}

                            record_fallback({'probe': True, 'request': req_info, 'http_status': resp_http.status_code, 'response': resp_json})

                            data_present = False
                            if isinstance(resp_json, dict):
                                # Data may be in 'Success' or 'data' depending on implementation
                                if resp_json.get('Success'):
                                    if resp_json['Success']:
                                        data_present = True
                                if resp_json.get('success') and resp_json.get('data'):
                                    data_present = True

                            summary.append({'param': key, 'value_used': val, 'exchange': exch, 'from': fd, 'to': td, 'data_present': data_present, 'status_code': resp_http.status_code, 'response_snippet': str(resp_json)[:400]})
                        except Exception as e:
                            record_fallback({'probe': True, 'request': req_info, 'error': str(e)})
                            summary.append({'param': key, 'value_used': val, 'exchange': exch, 'from': fd, 'to': td, 'data_present': False, 'error': str(e)})
                        time.sleep(RATE_DELAY)

    return summary

if __name__ == '__main__':
    try:
        s = probe()
    except KeyboardInterrupt:
        print('\nProbe interrupted by user. Saving partial results to scripts/account_probe_partial.json')
        # attempt to persist whatever we have in debug store by reading fallbacks is not possible across processes,
        # so instead save an empty placeholder; main probe records per-request via record_fallback in process.
        s = []
        with open('scripts/account_probe_partial.json', 'w', encoding='utf-8') as f:
            json.dump({'note': 'interrupted, partial results may be in in-process debug store'}, f, indent=2)
        raise

    print('Total attempts:', len(s))
    found = [x for x in s if x.get('data_present')]
    print('Found non-empty holdings for', len(found), 'attempts')
    for f in found:
        print(f)
    print('\nSample attempts:')
    for r in s[:10]:
        print(r)
