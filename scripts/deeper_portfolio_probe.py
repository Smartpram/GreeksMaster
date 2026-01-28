"""Deeper probe for portfolioholdings: try different account keys, date ranges and portfolio types.

Saves raw request/response into debug_store and prints a concise summary of successful shapes.
"""
import json
import os
from datetime import datetime, timedelta
import requests

from app.services.breeze_api import BreezeAPIService
from app.services.debug_store import record_fallback

ROOT = os.path.dirname(os.path.dirname(__file__))
ACCOUNTS_PATH = os.path.join(ROOT, 'app', 'data', 'accounts.json')

KEYS = ['ucc', 'demat', 'customer_id']
PORTFOLIO_TYPES = ['', 'Equity', 'FNO']
DAYS = [30, 60, 90]

with open(ACCOUNTS_PATH, 'r', encoding='utf-8') as f:
    accounts = json.load(f)

api = BreezeAPIService()
auth = api.authenticate()
print('authenticate =>', auth)

results = []

for acct in accounts:
    acct_id = acct.get('ucc') or acct.get('demat')
    acct_demat = acct.get('demat')
    for key in KEYS:
        val = acct.get(key) if key in acct else acct_id
        if not val:
            continue

        for ptype in PORTFOLIO_TYPES:
            for days in DAYS:
                to_dt = datetime.utcnow()
                from_dt = to_dt - timedelta(days=days)
                payload = {
                    'exchange_code': 'NFO',
                    'from_date': from_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'to_date': to_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'stock_code': '',
                    'portfolio_type': ptype
                }
                # add account scoping key
                payload[key] = val

                # Prepare headers
                headers = api.get_headers(payload)

                url = api.base_url + '/portfolioholdings'

                try:
                    resp = requests.get(url, json=payload, headers=headers, timeout=30)
                    try:
                        body = resp.json()
                    except Exception:
                        body = resp.text

                    event = {
                        'account_ucc': acct.get('ucc'),
                        'account_demat': acct.get('demat'),
                        'key': key,
                        'key_value': val,
                        'portfolio_type': ptype,
                        'days': days,
                        'status_code': resp.status_code,
                        'request_payload': payload,
                        'request_headers': {k: headers.get(k) for k in ('X-AppKey','X-SessionToken','X-Checksum','X-Timestamp')},
                        'response': body
                    }
                    record_fallback(event)
                    results.append(event)
                    print(f"tried key={key} ptype='{ptype or '<empty>'}' days={days} status={resp.status_code} data_present={bool(body and (isinstance(body, dict) and body.get('Success') or isinstance(body, list)))}")
                except Exception as e:
                    event = {
                        'account_ucc': acct.get('ucc'),
                        'account_demat': acct.get('demat'),
                        'key': key,
                        'key_value': val,
                        'portfolio_type': ptype,
                        'days': days,
                        'error': str(e)
                    }
                    record_fallback(event)
                    results.append(event)
                    print(f"tried key={key} ptype='{ptype or '<empty>'}' days={days} exception={e}")

print('\nProbe finished. Use /api/debug/fallbacks to review recorded raw events.')
