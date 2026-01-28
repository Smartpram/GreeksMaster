from app.main import create_app
import json

app = create_app()
client = app.test_client()

# Valid call
resp = client.get('/api/quotes/ITC?exchange=NSE')
print('VALID STATUS', resp.status_code)
try:
    print(json.dumps(resp.get_json(), indent=2))
except Exception:
    print(resp.data)

# Invalid call: missing stock_code (empty path segment) or invalid exchange
resp2 = client.get('/api/quotes/?exchange=INVALID')
print('\nINVALID STATUS', resp2.status_code)
try:
    print(json.dumps(resp2.get_json(), indent=2))
except Exception:
    print(resp2.data)
