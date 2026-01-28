"""Run checks against the Breeze service returned by the factory and print results.

This script is intended to be run locally to capture the raw responses from the
preferred service (breeze_connect adapter if available) for debugging portfolio/funds endpoints.
"""
import json
from pprint import pformat

from app.services.breeze_service_factory import get_breeze_service


def main():
    s = get_breeze_service()
    print('service_type=', type(s))
    client = getattr(s, 'client', None)
    print('client_type=', type(client))

    if client is not None:
        client_methods = [n for n in dir(client) if n.startswith(('get_', 'place_', 'order', 'authenticate', 'login', 'session'))]
    else:
        client_methods = []

    print('client_methods=')
    print(pformat(client_methods))

    endpoints = [
        ('get_customer_details', {}),
        ('get_demat_holdings', {}),
        ('get_portfolio_positions', {}),
        ('get_funds', {}),
        ('get_portfolio_holdings', {'exchange_code': 'NFO', 'from_date': '2024-08-01T06:00:00.000Z', 'to_date': '2024-09-19T06:00:00.000Z'}),
        ('get_quotes', {'stock_code': 'ITC', 'exchange_code': 'NSE'})
    ]

    for name, kwargs in endpoints:
        print('\nCALL', name)
        func = getattr(s, name, None)
        if not func:
            print('NOT_IMPLEMENTED')
            continue

        try:
            res = func(**kwargs) if kwargs else func()
        except TypeError:
            # try calling without kwargs if signature differs
            try:
                res = func()
            except Exception as e:
                res = {'success': False, 'error': str(e)}
        except Exception as e:
            res = {'success': False, 'error': str(e)}

        try:
            print(json.dumps(res, indent=2, default=str))
        except Exception:
            print(repr(res))


if __name__ == '__main__':
    main()
