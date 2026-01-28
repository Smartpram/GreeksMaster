from inspect import signature
from breeze_connect import BreezeConnect
bc = BreezeConnect(api_key='test')
for name in ['session_key']:
    fn = getattr(bc, name, None)
    print(name, '=>', fn)
    if fn:
        try:
            print('sig', signature(fn))
        except Exception as e:
            print('sig error', e)
