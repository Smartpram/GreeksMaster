"""
Probe ICICI Breeze portfolio endpoints with multiple request formats and parameter names.
Tries combinations of: GET/POST, JSON/form, parameter names (userid, client_code, user_id), and headers.
"""
import requests
import json
from app.services.breeze_api import BreezeAPIService

ENDPOINTS = [
    ('dematholdings', 'GET'),
    ('portfoliopositions', 'GET'),
    ('funds', 'GET'),
    ('dematholdings', 'POST'),
    ('portfoliopositions', 'POST'),
    ('funds', 'POST'),
]

PARAM_KEYS = ['userid', 'user_id', 'client_code', 'client_id', 'idirect_userid']


def try_request(base_url, endpoint, method, headers=None, json_payload=None, data_payload=None):
    url = f"{base_url}/{endpoint}"
    try:
        if method == 'GET':
            resp = requests.get(url, headers=headers, json=json_payload, timeout=30)
        else:
            # Try form data first if provided, else json
            if data_payload is not None:
                resp = requests.post(url, headers=headers, data=data_payload, timeout=30)
            else:
                resp = requests.post(url, headers=headers, json=json_payload, timeout=30)
        return resp.status_code, resp.text
    except Exception as e:
        return None, str(e)


def probe():
    api = BreezeAPIService()
    auth = api.authenticate()
    if not auth.get('success'):
        print('Authentication failed:', auth)
        return

    base = api.base_url
    session = api.authenticated_session_token
    apikey = api.api_key
    user = api.user_id or auth.get('user_id') or auth.get('user_id')
    # also read from auth data
    user2 = auth.get('user_id') if isinstance(auth, dict) else None

    print('Authenticated. Probing endpoints...')

    attempts = []

    # Try combinations
    for endpoint, method in ENDPOINTS:
        for key in PARAM_KEYS:
            # JSON payload
            json_payload = {'SessionToken': session, 'AppKey': apikey, key: user}
            headers = {
                'Content-Type': 'application/json',
                'X-AppKey': apikey,
                'X-SessionToken': session
            }
            status, text = try_request(base, endpoint, method, headers=headers, json_payload=json_payload)
            attempts.append((endpoint, method, 'json', key, status, text[:400]))

            # Form payload
            data_payload = {'SessionToken': session, 'AppKey': apikey, key: user}
            headers_form = {'Content-Type': 'application/x-www-form-urlencoded', 'X-AppKey': apikey, 'X-SessionToken': session}
            status, text = try_request(base, endpoint, 'POST', headers=headers_form, json_payload=None, data_payload=data_payload)
            attempts.append((endpoint, 'POST', 'form', key, status, text[:400]))

            # Try without AppKey in payload but in headers
            json_payload2 = {'SessionToken': session, key: user}
            headers2 = {'Content-Type': 'application/json', 'X-AppKey': apikey, 'X-SessionToken': session}
            status, text = try_request(base, endpoint, method, headers=headers2, json_payload=json_payload2)
            attempts.append((endpoint, method, 'json_no_appkey', key, status, text[:400]))

    # Print summary of attempts
    print('\nProbe results (showing status and truncated response):')
    for att in attempts:
        endpoint, method, mode, key, status, text = att
        print(f"{endpoint:20} {method:4} {mode:20} {key:15} -> status: {status} | {text}")

    # Return attempts for programmatic inspection
    return attempts

if __name__ == '__main__':
    probe()
