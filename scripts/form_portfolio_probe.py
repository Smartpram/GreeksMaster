"""Send portfolioholdings request as form-encoded (application/x-www-form-urlencoded).
Checksum will be computed over the form-encoded string (timestamp + form_string + secret_key).
"""
from app.services.breeze_api import BreezeAPIService
import requests
import urllib.parse
import json

svc = BreezeAPIService()
print('Authenticating...')
auth = svc.authenticate()
print('auth result:', auth)

# Build payload
payload = {
    'exchange_code': 'NFO',
    'from_date': '2025-09-01T06:00:00.000Z',
    'to_date': '2025-12-31T06:00:00.000Z',
    'stock_code': '',
    'portfolio_type': '',
    'demat': 'IN302679-34609925'
}

# Form-encode the payload
form_string = urllib.parse.urlencode(payload)
print('Form-encoded payload:', form_string)

# Generate checksum over the form string
checksum, timestamp = svc.generate_checksum(form_string)
print('Generated X-Checksum:', checksum)
print('Generated X-Timestamp:', timestamp)

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Checksum': checksum,
    'X-Timestamp': timestamp,
    'X-AppKey': svc.api_key,
    'X-SessionToken': svc.authenticated_session_token or svc.session_token
}

url = f"{svc.base_url}/portfolioholdings"
print('\nPOST URL:', url)
print('Headers:')
for k,v in headers.items():
    print(f"  {k}: {v}")

try:
    resp = requests.post(url, data=form_string, headers=headers, timeout=30)
    print('\nHTTP status:', resp.status_code)
    try:
        print('Response JSON:\n', json.dumps(resp.json(), indent=2))
    except Exception:
        print('Response text:\n', resp.text)
except Exception as e:
    print('Request exception:', str(e))
