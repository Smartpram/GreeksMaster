"""Send portfolioholdings request with parameters in the URL query string.
Run two variants:
  1) X-Checksum computed over empty post_data (timestamp + "" + secret_key)
  2) X-Checksum computed over JSON-stringified params (timestamp + json(params) + secret_key)

Compare responses.
"""
from app.services.breeze_api import BreezeAPIService
import requests
import json
import urllib.parse

svc = BreezeAPIService()
print('Authenticating...')
auth = svc.authenticate()
print('auth result:', auth)

params = {
    'exchange_code': 'NFO',
    'from_date': '2025-09-01T06:00:00.000Z',
    'to_date': '2025-12-31T06:00:00.000Z',
    'stock_code': '',
    'portfolio_type': '',
    'ucc': '8501299414'
}

query_string = urllib.parse.urlencode(params)
url = f"{svc.base_url}/portfolioholdings?{query_string}"
print('\nRequest URL:', url)

# Variant A: checksum over empty post_data
headers_a = svc.get_headers("")
print('\nVariant A headers (checksum over empty):')
for k,v in headers_a.items():
    print(f"  {k}: {v}")
try:
    resp_a = requests.get(url, headers=headers_a, timeout=30)
    print('\nVariant A status:', resp_a.status_code)
    try:
        print('Variant A JSON:\n', json.dumps(resp_a.json(), indent=2))
    except Exception:
        print('Variant A text:\n', resp_a.text)
except Exception as e:
    print('Variant A exception:', str(e))

# Variant B: checksum over JSON-stringified params
post_data_json = json.dumps(params, separators=(',', ':'))
checksum_b, timestamp_b = svc.generate_checksum(post_data_json)
headers_b = {
    'Content-Type': 'application/json',
    'X-Checksum': checksum_b,
    'X-Timestamp': timestamp_b,
    'X-AppKey': svc.api_key,
    'X-SessionToken': svc.authenticated_session_token or svc.session_token
}
print('\nVariant B headers (checksum over JSON params):')
for k,v in headers_b.items():
    print(f"  {k}: {v}")

try:
    resp_b = requests.get(url, headers=headers_b, timeout=30)
    print('\nVariant B status:', resp_b.status_code)
    try:
        print('Variant B JSON:\n', json.dumps(resp_b.json(), indent=2))
    except Exception:
        print('Variant B text:\n', resp_b.text)
except Exception as e:
    print('Variant B exception:', str(e))
