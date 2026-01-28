"""
Breeze Connect adapter

This adapter attempts to use the official `breeze_connect` package if it's installed.
It exposes a small, consistent interface used by the rest of the app. If the package
is not available the adapter reports it's not available and methods return helpful
errors so the application can fall back to the existing `breeze_api` implementation.
"""
import logging
from typing import Any, Dict, Optional

from app.config import Config

logger = logging.getLogger(__name__)


class BreezeConnectAdapter:
    """Adapter around the `breeze_connect` package.

    Usage:
      adapter = BreezeConnectAdapter()
      adapter.authenticate()  # if available
      adapter.get_portfolio_holdings(...)
    """

    def __init__(self):
        self.config = Config()
        self.api_key = self.config.BREEZE_API_KEY
        self.secret_key = self.config.BREEZE_SECRET_KEY
        self.session_token = self.config.BREEZE_SESSION_TOKEN
        self.user_id = self.config.BREEZE_USER_ID
        self.client = None
        self.available = False

        try:
            # try importing the official package
            from breeze_connect import BreezeConnect

            # instantiate client if possible
            try:
                self.client = BreezeConnect(api_key=self.api_key)
                self.available = True
                logger.info("breeze_connect package loaded and client instantiated")
            except Exception as e:
                logger.warning(f"breeze_connect package found but client init failed: {e}")
                # still mark available since methods may be callable after session
                self.available = True

        except ImportError:
            logger.info("breeze_connect package not installed; adapter unavailable")
            self.available = False

    def is_available(self) -> bool:
        return self.available

    def is_authenticated(self) -> bool:
        """Return True if underlying client appears ready/has a session key or a configured session token."""
        try:
            if not self.available or self.client is None:
                return False

            # breeze_connect client may expose session_key attribute after authentication
            sk = getattr(self.client, 'session_key', None)
            if sk:
                return True

            # Fallback: if a session token is configured in env, treat as authenticated for testing
            return bool(self.session_token)
        except Exception:
            return False

    def get_user_info(self) -> Dict[str, Any]:
        """Normalize customer details to the same shape as BreezeAPIService.get_user_info()."""
        res = self.get_customer_details()
        if not res.get('success'):
            return {'success': False, 'error': res.get('error')}

        data = res.get('data') or {}
        return {
            'success': True,
            'user_name': data.get('idirect_user_name', 'Unknown'),
            'user_id': data.get('idirect_userid', 'Unknown'),
            'trading_allowed': data.get('segments_allowed', {}).get('Trading', 'N') == 'Y',
            'equity_allowed': data.get('segments_allowed', {}).get('Equity', 'N') == 'Y',
            'derivatives_allowed': data.get('segments_allowed', {}).get('Derivatives', 'N') == 'Y',
            'last_login': data.get('idirect_lastlogin_time', 'Unknown'),
            'session_token': self.session_token
        }

    def get_portfolio(self) -> Dict[str, Any]:
        """Convenience: return demat holdings via adapter."""
        return self.get_demat_holdings()

    def _call(self, name: str, *args, **kwargs) -> Dict[str, Any]:
        """Dynamically call a method on the underlying client if available."""
        if not self.available or self.client is None:
            return {'success': False, 'error': 'breeze_connect package not available'}

        method = getattr(self.client, name, None)
        if not method:
            return {'success': False, 'error': f'method {name} not found on BreezeConnect client'}

        try:
            result = method(*args, **kwargs)
            # Some breeze_connect methods return None or complex objects. Normalize to dict.
            return {'success': True, 'data': result}
        except Exception as e:
            logger.error(f"Exception calling breeze_connect.{name}: {e}")
            return {'success': False, 'error': str(e)}

    # Convenience wrappers used by the app
    def authenticate(self) -> Dict[str, Any]:
        res = self._call('authenticate')
        # If authentication succeeded, try to capture session token from response or client
        if res.get('success'):
            data = res.get('data') or {}
            # Common keys: 'session_token' in response data or client.session_key
            token = None
            if isinstance(data, dict):
                token = data.get('session_token') or data.get('sessionKey') or data.get('session_key')
            if not token:
                token = getattr(self.client, 'session_key', None)

            if token:
                self.session_token = token
                # store some user info if available
                try:
                    self.user_id = data.get('idirect_userid') or getattr(self, 'user_id', None)
                    self.user_name = data.get('idirect_user_name') or getattr(self, 'user_name', None)
                except Exception:
                    pass

        return res

    def get_customer_details(self) -> Dict[str, Any]:
        return self._call('get_customer_details')

    def get_portfolio_holdings(self, *args, **kwargs) -> Dict[str, Any]:
        # breeze_connect.get_portfolio_holdings signature is:
        # (exchange_code='', from_date='', to_date='', stock_code='', portfolio_type='')
        # Accept flexible kwargs from callers (exchange_code, from_date, to_date, stock_code, portfolio_type,
        # plus optional ucc/demat which the official client does not accept). Map to positional args.
        exchange_code = kwargs.get('exchange_code', '') if kwargs else (args[0] if len(args) > 0 else '')
        from_date = kwargs.get('from_date', '') if kwargs else (args[1] if len(args) > 1 else '')
        to_date = kwargs.get('to_date', '') if kwargs else (args[2] if len(args) > 2 else '')
        stock_code = kwargs.get('stock_code', '') if kwargs else (args[3] if len(args) > 3 else '')
        portfolio_type = kwargs.get('portfolio_type', '') if kwargs else (args[4] if len(args) > 4 else '')

        # Note: breeze_connect client does not accept ucc/demat as filters on this method. We ignore them here.
        return self._call('get_portfolio_holdings', exchange_code, from_date, to_date, stock_code, portfolio_type)

    def get_demat_holdings(self, *args, **kwargs) -> Dict[str, Any]:
        res = self._call('get_demat_holdings', *args, **kwargs)
        if res.get('success') and res.get('data') is None:
            return self._fallback_to_http('dematholdings', func_name='get_demat_holdings')
        return res

    def get_portfolio_positions(self, *args, **kwargs) -> Dict[str, Any]:
        res = self._call('get_portfolio_positions', *args, **kwargs)
        if res.get('success') and res.get('data') is None:
            return self._fallback_to_http('portfoliopositions', func_name='get_portfolio_positions')
        return res

    def get_funds(self, *args, **kwargs) -> Dict[str, Any]:
        # The breeze_connect.get_funds() method accepts no parameters in this client version.
        # If callers pass ucc/demat, we cannot forward them to the client directly — call without args
        # and return a warning indicating account-level filtering isn't supported by the adapter.
        ucc = None
        demat = None
        if kwargs:
            ucc = kwargs.get('ucc') or kwargs.get('UCC')
            demat = kwargs.get('demat') or kwargs.get('Demat')

        res = self._call('get_funds')
        if res.get('success') and res.get('data') is None:
            return self._fallback_to_http('funds', func_name='get_funds', kwargs=kwargs)
        if (ucc or demat) and res.get('success'):
            # Annotate response to indicate account-level filtering wasn't applied by the underlying client
            res = {'success': True, 'data': res.get('data'), 'warning': 'Underlying breeze_connect.get_funds() does not accept ucc/demat filters; returned global funds data.'}
        return res

    def get_quotes(self, *args, **kwargs) -> Dict[str, Any]:
        # Validate inputs if possible
        try:
            from app.services.validators import validate_quote_params
        except Exception:
            validate_quote_params = None

        params = {}
        if args:
            # expected (stock_code, exchange_code)
            params['stock_code'] = args[0] if len(args) > 0 else ''
            params['exchange_code'] = args[1] if len(args) > 1 else ''
        params.update(kwargs)
        if validate_quote_params:
            ok, err = validate_quote_params(params)
            if not ok:
                return {'success': False, 'error': f'Invalid quote parameters: {err}'}

        # Ensure adapter is authenticated so we can transfer session to fallback if needed
        try:
            if not self.is_authenticated():
                self.authenticate()
        except Exception:
            # ignore authentication errors here; the call may still proceed
            pass

        # Map to underlying client call: get_quotes(stock_code, exchange_code, product_type='cash')
        stock_code = params.get('stock_code')
        exchange_code = params.get('exchange_code', 'NSE')
        product_type = params.get('product_type', 'cash')

        res = self._call('get_quotes', stock_code, exchange_code, product_type)

        # If the official client returns None (some client methods return None),
        # fall back to the direct HTTP implementation to retrieve quotes.
        if res.get('success') and res.get('data') is None:
            try:
                # late import to avoid circular imports
                from app.services.breeze_api import BreezeAPIService
                api = BreezeAPIService()
                # ensure authentication transfer: prefer adapter's session token if set
                # Prefer an adapter-captured session token, otherwise fall back to config-provided session token
                token = getattr(self, 'session_token', None) or getattr(self.config, 'BREEZE_SESSION_TOKEN', None)
                if token:
                    # set authenticated_session_token so BreezeAPIService treats it as authenticated
                    api.authenticated_session_token = token
                    # also set user_info minimally
                    try:
                        api.user_info = {'idirect_userid': getattr(self, 'user_id', None), 'idirect_user_name': getattr(self, 'user_name', None)}
                    except Exception:
                        pass
                # call direct HTTP client
                api_res = api.get_quotes(stock_code, exchange_code, product_type)
                # if fallback returned an authentication error, try to authenticate and retry once
                retry_note = None
                if isinstance(api_res, dict) and (not api_res.get('success')):
                    err = str(api_res.get('error', '')).lower()
                    if '401' in err or 'not authenticated' in err or 'appkey is empty' in err:
                        # attempt to authenticate the direct client and retry
                        try:
                            auth_res = api.authenticate()
                            retry_note = {'auth_retry': auth_res}
                            if auth_res.get('success'):
                                api_res = api.get_quotes(stock_code, exchange_code, product_type)
                        except Exception as e:
                            # ignore and return original api_res
                            retry_note = {'auth_retry_exception': str(e)}

                # annotate that this was a fallback
                if isinstance(api_res, dict):
                    api_res['_fallback'] = 'BreezeAPIService used because breeze_connect returned no data'
                    if retry_note:
                        api_res['_fallback_retry'] = retry_note
                return api_res
            except Exception as e:
                # if fallback fails, return original result with error annotation
                res['warning'] = f'fallback to BreezeAPIService failed: {e}'
                return res

        return res

    def _fallback_to_http(self, endpoint_path: str, func_name: str = None, kwargs: dict = None) -> Dict[str, Any]:
        """Generic fallback: instantiate BreezeAPIService, transfer session token, call equivalent method,
        record a debug event, and return the result.

        endpoint_path is the API path (for logging) and func_name is the name of the BreezeAPIService method to call.
        """
        try:
            from app.services.breeze_api import BreezeAPIService
            from app.services.debug_store import record_fallback

            api = BreezeAPIService()
            token = getattr(self, 'session_token', None) or getattr(self.config, 'BREEZE_SESSION_TOKEN', None)
            if token:
                api.authenticated_session_token = token
                try:
                    api.user_info = {'idirect_userid': getattr(self, 'user_id', None), 'idirect_user_name': getattr(self, 'user_name', None)}
                except Exception:
                    pass

            # Call the matching method if available, else do a raw HTTP GET for the endpoint path
            result = None
            if func_name and hasattr(api, func_name):
                try:
                    if kwargs:
                        result = getattr(api, func_name)(**kwargs)
                    else:
                        result = getattr(api, func_name)()
                except Exception as e:
                    result = {'success': False, 'error': str(e)}
            else:
                # raw request path fallback
                try:
                    # Try GET with no body
                    import requests
                    headers = api.get_headers("")
                    url = api.base_url + '/' + endpoint_path
                    resp = requests.get(url, headers=headers, timeout=30)
                    if resp.status_code == 200:
                        data = resp.json()
                        result = {'success': True, 'data': data.get('Success', data)}
                    else:
                        result = {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text}'}
                except Exception as e:
                    result = {'success': False, 'error': str(e)}

            # Record debug info
            try:
                record_fallback({
                    'endpoint': endpoint_path,
                    'func_name': func_name,
                    'kwargs': kwargs or {},
                    'result': result
                })
            except Exception:
                pass

            # If the direct client returned a 401-like error, try authenticating and retry once
            if isinstance(result, dict) and (not result.get('success')):
                err = str(result.get('error', '')).lower()
                if '401' in err or 'not authenticated' in err or 'appkey is empty' in err:
                    try:
                        auth_res = api.authenticate()
                        if auth_res.get('success'):
                            if func_name and hasattr(api, func_name):
                                result = getattr(api, func_name)(**(kwargs or {}))
                            else:
                                # retry raw GET
                                import requests
                                headers = api.get_headers("")
                                url = api.base_url + '/' + endpoint_path
                                resp = requests.get(url, headers=headers, timeout=30)
                                if resp.status_code == 200:
                                    data = resp.json()
                                    result = {'success': True, 'data': data.get('Success', data)}
                                else:
                                    result = {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text}'}
                    except Exception as e:
                        # ignore retry errors
                        pass

            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def place_order(self, *args, **kwargs) -> Dict[str, Any]:
        return self._call('place_order', *args, **kwargs)

    def subscribe_feeds(self, *args, **kwargs) -> Dict[str, Any]:
        """Subscribe to real-time feeds using breeze_connect client if available."""
        try:
            # Basic validation for stock_token or exchange-based subscription
            from app.services.validators import validate_quote_params
        except Exception:
            validate_quote_params = None

        params = {}
        params.update(kwargs)

        if validate_quote_params:
            ok, err = validate_quote_params(params)
            if not ok:
                return {'success': False, 'error': f'Invalid subscription parameters: {err}'}

        # Ensure authentication
        try:
            if not self.is_authenticated():
                self.authenticate()
        except Exception:
            pass

        res = self._call('subscribe_feeds', *args, **kwargs)
        return res

    def unsubscribe_feeds(self, *args, **kwargs) -> Dict[str, Any]:
        try:
            if not self.is_authenticated():
                self.authenticate()
        except Exception:
            pass

        res = self._call('unsubscribe_feeds', *args, **kwargs)
        return res
