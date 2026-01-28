import re
from datetime import datetime
from typing import Tuple, Optional

VALID_EXCHANGES = {"BSE", "NSE", "BFO", "NFO"}
VALID_OHLC_INTERVALS = {"1second", "1minute", "5minute", "30minute"}


def validate_stock_token(stock_token: str) -> Tuple[bool, Optional[str]]:
    if not stock_token:
        return False, "stock_token cannot be empty"
    # expected pattern X.Y!Token e.g. 4.1!38071
    m = re.match(r'^(\d+)\.(\d+)!([0-9]+)$', stock_token)
    if not m:
        return False, "stock_token must match pattern X.Y!Token, e.g. 4.1!38071"

    x = int(m.group(1))
    y = int(m.group(2))
    if x not in (1, 2, 4, 8):
        return False, "stock_token X value must be one of 1,2,4,8"
    if y not in (1, 2):
        return False, "stock_token Y value must be 1 (quote) or 2 (market depth)"

    return True, None


def validate_exchange_code(exchange: str) -> Tuple[bool, Optional[str]]:
    if not exchange:
        return False, "exchange_code cannot be empty"
    if exchange not in VALID_EXCHANGES:
        return False, f"exchange_code must be one of {sorted(VALID_EXCHANGES)}"
    return True, None


def validate_stock_code(code: str) -> Tuple[bool, Optional[str]]:
    if not code:
        return False, "stock_code cannot be empty"
    # simple check: letters/numbers and reasonable length
    if not re.match(r'^[A-Z0-9._-]{1,20}$', code.upper()):
        return False, "stock_code must be alphanumeric (examples: WIPRO, ZEEENT)"
    return True, None


def validate_product_type(product: str, exchange: str) -> Tuple[bool, Optional[str]]:
    if exchange == 'NFO' and (not product or str(product).strip() == ''):
        return False, "product_type is required for exchange NFO"
    # allow 'Futures', 'Options' or any non-empty string
    return True, None


def parse_expiry_date(dt_str: str) -> Optional[datetime]:
    if not dt_str:
        return None
    # Accept case-insensitive month abbreviations by title-casing the string
    try:
        return datetime.strptime(dt_str.strip().title(), '%d-%b-%Y')
    except Exception:
        return None


def validate_expiry_date(expiry: str, exchange: str, product_type: str) -> Tuple[bool, Optional[str]]:
    if exchange == 'NFO' and not expiry:
        return False, "expiry_date is required for NFO exchange"
    if product_type and product_type.lower() == 'options' and not expiry:
        return False, "expiry_date is required for Options"
    if expiry:
        if not parse_expiry_date(expiry):
            return False, "expiry_date must be in DD-MMM-YYYY format (e.g., 01-Jan-2022)"
    return True, None


def validate_strike_price(strike: str, product_type: str) -> Tuple[bool, Optional[str]]:
    if product_type and product_type.lower() == 'options':
        if not strike:
            return False, "strike_price is required for Options"
        try:
            float(strike)
        except Exception:
            return False, "strike_price must be a float value represented as a string"
    else:
        if strike:
            try:
                float(strike)
            except Exception:
                return False, "strike_price must be a float value represented as a string"
    return True, None


def validate_right(right: str, product_type: str) -> Tuple[bool, Optional[str]]:
    if product_type and product_type.lower() == 'options':
        if not right or right not in ('Put', 'Call'):
            return False, "right must be 'Put' or 'Call' for Options"
    else:
        if right and right not in ('Put', 'Call', ''):
            return False, "right must be 'Put', 'Call', or empty"
    return True, None


def validate_exchange_depth_flags(get_exchange_quotes: bool, get_market_depth: bool) -> Tuple[bool, Optional[str]]:
    if not (get_exchange_quotes or get_market_depth):
        return False, "At least one of get_exchange_quotes or get_market_depth must be True"
    return True, None


def validate_ohlcv_interval(interval: str) -> Tuple[bool, Optional[str]]:
    if not interval:
        return False, "OHLCV interval cannot be empty"
    if interval not in VALID_OHLC_INTERVALS:
        return False, f"interval must be one of {sorted(VALID_OHLC_INTERVALS)}"
    return True, None


def validate_quote_params(params: dict) -> Tuple[bool, Optional[str]]:
    # params expected keys: stock_code, exchange_code, product_type, expiry_date, strike_price, right,
    # get_exchange_quotes, get_market_depth, interval, stock_token
    stock_code = params.get('stock_code') or params.get('stock_token')
    exchange = params.get('exchange_code')
    product = params.get('product_type')
    expiry = params.get('expiry_date')
    strike = params.get('strike_price')
    right = params.get('right')
    get_exchange_quotes = params.get('get_exchange_quotes', True)
    get_market_depth = params.get('get_market_depth', False)
    interval = params.get('interval')

    ok, err = validate_exchange_code(exchange)
    if not ok:
        return ok, err

    if stock_code and '!' in stock_code:
        ok, err = validate_stock_token(stock_code)
        if not ok:
            return ok, err
    else:
        ok, err = validate_stock_code(stock_code)
        if not ok:
            return ok, err

    ok, err = validate_product_type(product, exchange)
    if not ok:
        return ok, err

    ok, err = validate_expiry_date(expiry, exchange, product or '')
    if not ok:
        return ok, err

    ok, err = validate_strike_price(strike, product or '')
    if not ok:
        return ok, err

    ok, err = validate_right(right, product or '')
    if not ok:
        return ok, err

    ok, err = validate_exchange_depth_flags(get_exchange_quotes, get_market_depth)
    if not ok:
        return ok, err

    if interval is not None:
        ok, err = validate_ohlcv_interval(interval)
        if not ok:
            return ok, err

    return True, None
