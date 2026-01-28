import json
import pprint
from app.services.breeze_service_factory import get_breeze_service
from app.services.breeze_api import BreezeAPIService

pp = pprint.PrettyPrinter(indent=2)

svc = get_breeze_service()
print('service_type=', type(svc))
print('has client=', hasattr(svc, 'client'))
client = getattr(svc, 'client', None)
print('client_type=', type(client))

if client is not None:
    try:
        print('\nCalling underlying client.get_quotes(stock_code, exchange_code, product_type)')
        client_res = client.get_quotes('ITC', 'NSE', 'cash')
        print('client.get_quotes returned type:', type(client_res))
        try:
            print(json.dumps(client_res, indent=2, default=str))
        except Exception:
            pp.pprint(client_res)
    except Exception as e:
        print('client.get_quotes exception:', e)

# Call via service wrapper
try:
    print('\nCalling service.get_quotes("ITC","NSE")')
    svc_res = svc.get_quotes('ITC', 'NSE')
    print('service.get_quotes result:')
    try:
        print(json.dumps(svc_res, indent=2, default=str))
    except Exception:
        pp.pprint(svc_res)
except Exception as e:
    print('service.get_quotes exception:', e)

# Call direct HTTP client implementation
print('\nInstantiating BreezeAPIService and authenticating...')
api = BreezeAPIService()
try:
    auth = api.authenticate()
    print('BreezeAPIService.authenticate:', auth)
except Exception as e:
    print('authenticate exception:', e)

print('\nCalling BreezeAPIService.get_quotes("ITC","NSE")')
try:
    api_res = api.get_quotes('ITC', 'NSE')
    try:
        print(json.dumps(api_res, indent=2, default=str))
    except Exception:
        pp.pprint(api_res)
except Exception as e:
    print('BreezeAPIService.get_quotes exception:', e)
