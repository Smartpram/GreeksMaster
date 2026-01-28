from breeze_connect import BreezeConnect
bc = BreezeConnect(api_key='test')
methods = [m for m in dir(bc) if m.lower().startswith(('subscribe','unsubscribe','session','feeds'))]
print('\n'.join(sorted(methods)))
