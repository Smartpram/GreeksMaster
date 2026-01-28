"""Run one portfolioholdings request that matches the documentation example.
This script uses the BreezeAPIService to build headers (checksum/timestamp) and
performs a single GET request including an example 'ucc' field.
"""
from app.services.breeze_api import BreezeAPIService
import requests
import json

svc = BreezeAPIService()
print('Authenticating...')
auth = svc.authenticate()
print('auth result:', auth)

payload = {
    "exchange_code": "NFO",
    "from_date": "2025-09-01T06:00:00.000Z",
    "to_date": "2025-12-31T06:00:00.000Z",
    "stock_code": "",
    "portfolio_type": "",
    "ucc": "8501299414"
}
headers = svc.get_headers(payload)
print('Generated headers:')
for k, v in headers.items():
    print(f"{k}: {v}")

url = f"{svc.base_url}/portfolioholdings"
print('\nRequest URL:', url)
print('Request payload:', json.dumps(payload))

try:
    resp = requests.get(url, json=payload, headers=headers, timeout=30)
    print('\nHTTP status:', resp.status_code)
    try:
        print('Response JSON:\n', json.dumps(resp.json(), indent=2))
    except Exception:
        print('Response text:\n', resp.text)
except Exception as e:
    print('Request exception:', str(e))
