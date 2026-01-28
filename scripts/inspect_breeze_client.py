from inspect import signature, getdoc
try:
    from breeze_connect import BreezeConnect
    bc = BreezeConnect(api_key='test')
    for name in ('get_funds','get_portfolio_holdings','get_demat_holdings','get_portfolio_positions'):
        fn = getattr(bc, name, None)
        print('---', name)
        if fn:
            try:
                print('signature:', signature(fn))
            except Exception as e:
                print('signature error:', e)
            doc = getdoc(fn)
            if doc:
                print('doc:', doc.splitlines()[0])
            else:
                print('doc: <no docstring>')
        else:
            print('not found')
except Exception as e:
    print('error importing or instantiating BreezeConnect:', e)
