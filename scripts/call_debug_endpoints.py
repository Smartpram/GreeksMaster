# Script to call Flask debug endpoints via test client
from app.main import create_app
import json

app = create_app()
client = app.test_client()

resp = client.get('/api/debug/accounts')
print('accounts status', resp.status_code)
try:
    print(json.dumps(resp.get_json(), indent=2))
except Exception:
    print(resp.data)

resp2 = client.get('/api/debug/test_accounts')
print('\ntest_accounts status', resp2.status_code)
try:
    print(json.dumps(resp2.get_json(), indent=2))
except Exception:
    print(resp2.data)
