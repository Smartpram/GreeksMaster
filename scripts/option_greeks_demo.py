from app.services.breeze_service_factory import get_breeze_service
from app.strategies.option_greeks import black_scholes_greeks
import time


def main():
    svc = get_breeze_service()
    if not svc.is_available():
        print('breeze_connect adapter not available; try using BreezeAPIService directly')
        return

    if not svc.is_authenticated():
        auth = svc.authenticate()
        print('auth result:', auth)
        if not auth.get('success'):
            print('authentication failed')
            return

    # Example: fetch option chain for NIFTY or a sample stock token
    stock_code = 'NIFTY'  # change to a valid index or underlying
    exchange = 'NFO'
    expiry = '20JAN2026'

    print('Requesting option chain (may return null data if server has none)')
    res = svc._call('get_option_chain_quotes', stock_code, exchange, expiry, 'Options', '', '')

    if not res.get('success'):
        print('Failed to fetch option chain:', res)
        return

    data = res.get('data')
    if not data:
        print('Option chain returned empty data')
        return

    # Data shape varies; attempt to iterate strikes
    strikes = data.get('strikes') if isinstance(data, dict) else None
    if not strikes:
        print('Unexpected option chain format, dumping data:')
        print(data)
        return

    # Use simple assumptions for S, r, sigma
    S = 18000.0
    r = 0.06
    sigma = 0.20
    for s in strikes[:10]:
        K = float(s.get('strike'))
        call_bid = float(s.get('call', {}).get('bid', 0) or 0)
        call_ask = float(s.get('call', {}).get('ask', 0) or 0)
        T = 30.0 / 365.0
        greeks = black_scholes_greeks(S, K, T, r, sigma, 'call')
        print(f"K={K} call_bid={call_bid} call_ask={call_ask} delta={greeks['delta']:.4f} gamma={greeks['gamma']:.6f} vega={greeks['vega']:.3f}")


if __name__ == '__main__':
    main()
