from inspect import signature, getdoc
from breeze_connect import BreezeConnect
bc = BreezeConnect(api_key='test')
name='get_option_chain_quotes'
fn = getattr(bc, name, None)
print(name, 'exists?', fn is not None)
if fn:
    try:
        print('signature:', signature(fn))
    except Exception as e:
        print('signature error', e)
    doc = getdoc(fn)
    print('doc:', doc.splitlines()[0] if doc else '<no doc>')
