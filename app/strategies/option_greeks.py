import math
from typing import Tuple

def _std_norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def _std_norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def black_scholes_greeks(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> dict:
    """Compute Black-Scholes option Greeks for European option.

    S: spot
    K: strike
    T: time to expiry in years
    r: risk-free rate (annual)
    sigma: volatility (annual)
    option_type: 'call' or 'put'
    """
    if T <= 0 or sigma <= 0:
        return {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0, 'rho': 0.0}

    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    nd1 = _std_norm_cdf(d1)
    nd2 = _std_norm_cdf(d2)
    npd1 = _std_norm_pdf(d1)

    vega = S * npd1 * math.sqrt(T)
    gamma = npd1 / (S * sigma * math.sqrt(T))

    if option_type.lower().startswith('c'):
        delta = nd1
        theta = - (S * npd1 * sigma) / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * nd2
        rho = K * T * math.exp(-r * T) * nd2
    else:
        delta = nd1 - 1
        theta = - (S * npd1 * sigma) / (2 * math.sqrt(T)) + r * K * math.exp(-r * T) * (1 - nd2)
        rho = -K * T * math.exp(-r * T) * (1 - nd2)

    return {
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega,
        'rho': rho
    }
