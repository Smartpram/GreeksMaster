"""
MyBreezeApp - Algorithmic Trading Application
Main Flask Application Entry Point
Features realistic fee-aware P&L calculations using ICICI Direct brokerage structure
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from app.services.breeze_service_factory import get_breeze_service
from app.services.data_stream import DataStreamService
from app.services.order_manager import OrderManager
from app.services.risk_manager import RiskManager
from app.services.backtesting import BacktestingEngine
from app.services.notifications import NotificationService
from app.services.auth_service import AuthService
from app.strategies.buy_hold_trend import BuyHoldTrendStrategy
from app.config import Config
from app.brokerage_fees import BrokerageFeeCalculator, BrokeragePlan
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("🚀 MyBreezeApp Starting with Fee-Aware Trading")
logger.info("📊 All P&L calculations include realistic ICICI Direct fees")

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize fee calculator for realistic P&L
    fee_calculator = BrokerageFeeCalculator(plan=BrokeragePlan.IVALUE)
    app.fee_calculator = fee_calculator
    logger.info("✓ Fee calculator initialized (IVALUE Plan)")
    
    # Initialize services (prefer breeze_connect adapter when available)
    breeze_service = get_breeze_service()
    data_stream_service = DataStreamService(breeze_service)
    order_manager = OrderManager(breeze_service)
    risk_manager = RiskManager()
    backtesting_engine = BacktestingEngine()
    notification_service = NotificationService()
    auth_service = AuthService()
    
    # Initialize strategy
    strategy = BuyHoldTrendStrategy(
        order_manager=order_manager,
        risk_manager=risk_manager,
        notification_service=notification_service
    )
    
    @app.route('/')
    def index():
        """Main dashboard"""
        try:
            # Test Breeze API connection and authentication
            if breeze_service.is_authenticated() or breeze_service.authenticate()['success']:
                user_info = breeze_service.get_user_info()
                
                # Get basic portfolio information
                portfolio_data = breeze_service.get_portfolio()
                funds_data = breeze_service.get_funds()
                
                return render_template('dashboard.html', 
                                     user_info=user_info,
                                     portfolio=portfolio_data,
                                     funds=funds_data)
            else:
                return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            return render_template('error.html', error=str(e))
    
    @app.route('/login')
    def login():
        """Login page"""
        return render_template('login.html')
    
    @app.route('/auth/callback')
    def auth_callback():
        """OAuth callback"""
        code = request.args.get('code')
        if code and auth_service.authenticate(code):
            session['authenticated'] = True
            return redirect(url_for('index'))
        return redirect(url_for('login'))
    
    @app.route('/api/authenticate')
    def api_authenticate():
        """Test Breeze API authentication"""
        try:
            auth_result = breeze_service.authenticate()
            return jsonify(auth_result)
        except Exception as e:
            logger.error(f"API Authentication error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/portfolio')
    def get_portfolio():
        """Get portfolio data"""
        try:
            if not breeze_service.is_authenticated():
                auth_result = breeze_service.authenticate()
                if not auth_result['success']:
                    return jsonify({'success': False, 'error': 'Authentication failed'}), 401
            
            portfolio = breeze_service.get_portfolio()
            return jsonify(portfolio)
        except Exception as e:
            logger.error(f"Error fetching portfolio: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/funds')
    def get_funds():
        """Get funds data"""
        try:
            if not breeze_service.is_authenticated():
                auth_result = breeze_service.authenticate()
                if not auth_result['success']:
                    return jsonify({'success': False, 'error': 'Authentication failed'}), 401
            
            funds = breeze_service.get_funds()
            return jsonify(funds)
        except Exception as e:
            logger.error(f"Error fetching funds: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/positions')
    def get_positions():
        """Get portfolio positions"""
        try:
            if not breeze_service.is_authenticated():
                auth_result = breeze_service.authenticate()
                if not auth_result['success']:
                    return jsonify({'success': False, 'error': 'Authentication failed'}), 401
            
            positions = breeze_service.get_portfolio_positions()
            return jsonify(positions)
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/quotes/<stock_code>')
    def get_quotes(stock_code):
        """Get live quotes for a stock"""
        try:
            if not breeze_service.is_authenticated():
                auth_result = breeze_service.authenticate()
                if not auth_result['success']:
                    return jsonify({'success': False, 'error': 'Authentication failed'}), 401
            # Accept extended query parameters for validation and streaming options
            params = {
                'stock_code': request.view_args.get('stock_code'),
                'exchange_code': request.args.get('exchange', 'NSE'),
                'product_type': request.args.get('product_type', ''),
                'expiry_date': request.args.get('expiry_date', ''),
                'strike_price': request.args.get('strike_price', ''),
                'right': request.args.get('right', ''),
                'get_exchange_quotes': request.args.get('get_exchange_quotes', 'true').lower() == 'true',
                'get_market_depth': request.args.get('get_market_depth', 'false').lower() == 'true',
                'interval': request.args.get('interval'),
                'stock_token': request.args.get('stock_token')
            }

            # Validate parameters if validators available (adapter will also validate)
            try:
                from app.services.validators import validate_quote_params
                ok, err = validate_quote_params(params)
                if not ok:
                    return jsonify({'success': False, 'error': f'Invalid quote parameters: {err}'}), 400
            except Exception:
                # validators not available - continue and let adapter/client handle validation
                pass

            # Prefer passing token if provided
            if params.get('stock_token'):
                # when stock_token provided, set stock_code param to token
                stock_arg = params['stock_token']
            else:
                stock_arg = stock_code

            quotes = breeze_service.get_quotes(stock_arg, params['exchange_code'], params['product_type'])
            return jsonify(quotes)
        except Exception as e:
            logger.error(f"Error fetching quotes: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/orders', methods=['GET', 'POST'])
    def orders():
        """Handle orders"""
        try:
            if not breeze_service.is_authenticated():
                auth_result = breeze_service.authenticate()
                if not auth_result['success']:
                    return jsonify({'success': False, 'error': 'Authentication failed'}), 401
        
            if request.method == 'POST':
                order_data = request.json
                result = breeze_service.place_order(order_data)
                return jsonify(result)
            else:
                # GET request - fetch orders
                orders = breeze_service.get_order_list()
                return jsonify(orders)
                
        except Exception as e:
            logger.error(f"Error with orders: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/backtest', methods=['POST'])
    def backtest():
        """Run backtest"""
        if not session.get('authenticated'):
            return jsonify({'error': 'Unauthorized'}), 401
        
        try:
            backtest_params = request.json
            results = backtesting_engine.run_backtest(
                strategy=strategy,
                **backtest_params
            )
            return jsonify(results)
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/stream/start')
    def start_stream():
        """Start data streaming"""
        if not session.get('authenticated'):
            return jsonify({'error': 'Unauthorized'}), 401
        
        try:
            instruments = request.args.getlist('instruments')
            data_stream_service.start_stream(instruments)
            return jsonify({'status': 'Stream started'})
        except Exception as e:
            logger.error(f"Error starting stream: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/stream/stop')
    def stop_stream():
        """Stop data streaming"""
        if not session.get('authenticated'):
            return jsonify({'error': 'Unauthorized'}), 401
        
        try:
            data_stream_service.stop_stream()
            return jsonify({'status': 'Stream stopped'})
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/strategy/toggle', methods=['POST'])
    def toggle_strategy():
        """Toggle strategy on/off"""
        if not session.get('authenticated'):
            return jsonify({'error': 'Unauthorized'}), 401
        
        try:
            action = request.json.get('action')
            if action == 'start':
                strategy.start()
            elif action == 'stop':
                strategy.stop()
            
            return jsonify({'status': f'Strategy {action}ed'})
        except Exception as e:
            logger.error(f"Error toggling strategy: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/performance')
    def get_performance():
        """Get performance metrics"""
        if not session.get('authenticated'):
            return jsonify({'error': 'Unauthorized'}), 401
        
        try:
            performance = strategy.get_performance_metrics()
            return jsonify(performance)
        except Exception as e:
            logger.error(f"Error fetching performance: {e}")
            return jsonify({'error': str(e)}), 500

    # --- Debug endpoints -------------------------------------------------
    @app.route('/api/debug/accounts')
    def debug_accounts():
        """Return locally stored accounts (for debugging/testing)."""
        try:
            accounts_path = os.path.join(app.root_path, 'data', 'accounts.json')
            if not os.path.exists(accounts_path):
                return jsonify({'success': False, 'error': 'accounts.json not found'}), 404

            with open(accounts_path, 'r', encoding='utf-8') as f:
                import json
                accounts = json.load(f)

            return jsonify({'success': True, 'accounts': accounts})
        except Exception as e:
            logger.error(f"Error reading accounts.json: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/debug/test_accounts')
    def debug_test_accounts():
        """Iterate local accounts and call Breeze service for funds and holdings using UCC/demat.

        Returns per-account responses so you can compare whether accounts produce different results.
        """
        try:
            # Load accounts
            accounts_path = os.path.join(app.root_path, 'data', 'accounts.json')
            if not os.path.exists(accounts_path):
                return jsonify({'success': False, 'error': 'accounts.json not found'}), 404

            with open(accounts_path, 'r', encoding='utf-8') as f:
                import json
                accounts = json.load(f)

            results = []

            # Ensure authenticated
            if not breeze_service.is_authenticated():
                auth = breeze_service.authenticate()
                if not auth.get('success'):
                    return jsonify({'success': False, 'error': 'Authentication failed', 'auth': auth}), 401

            for acct in accounts:
                ucc = acct.get('ucc')
                demat = acct.get('demat')

                funds = None
                holdings = None
                try:
                    # Use service methods that accept optional account identifiers
                    funds = breeze_service.get_funds(ucc=ucc, demat=demat)
                except TypeError:
                    # Adapter may not accept parameters - call without
                    funds = breeze_service.get_funds()

                try:
                    holdings = breeze_service.get_portfolio_holdings()
                except TypeError:
                    # Adapter variant may accept kwargs - attempt via getattr
                    func = getattr(breeze_service, 'get_portfolio_holdings', None)
                    if func:
                        try:
                            holdings = func(ucc=ucc, demat=demat)
                        except Exception:
                            holdings = func()

                results.append({'account': acct, 'funds': funds, 'holdings': holdings})

            return jsonify({'success': True, 'results': results})
        except Exception as e:
            logger.error(f"Error testing accounts: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/debug/fallbacks')
    def debug_fallbacks():
        """Return recent adapter fallback events recorded in-memory."""
        try:
            from app.services.debug_store import get_fallbacks
            events = get_fallbacks()
            return jsonify({'success': True, 'fallbacks': events})
        except Exception as e:
            logger.error(f"Error fetching fallbacks: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    # --- GTT ingestion and viewer -------------------------------------
    @app.route('/api/gtt/ingest', methods=['POST'])
    def api_gtt_ingest():
        """Ingest GTT response payload (expects JSON with 'Success' list) and store in DB."""
        try:
            # simple API key protection
            from app.config import Config
            expected_key = Config.INGEST_API_KEY
            provided = request.headers.get('X-API-KEY') or request.args.get('api_key')
            if not provided or provided != expected_key:
                return jsonify({'success': False, 'error': 'Unauthorized - invalid API key'}), 401

            payload = request.json or {}
            success = payload.get('Success')
            if not success:
                return jsonify({'success': False, 'error': 'Missing Success list in payload'}), 400

            from app.services.db import init_db, insert_gtt_records
            init_db()
            inserted = insert_gtt_records(success)
            return jsonify({'success': True, 'inserted': inserted})
        except Exception as e:
            logger.error(f"Error ingesting GTT payload: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/gtt/table')
    def api_gtt_table():
        """Return table-ready GTT payload (expanded legs + summary status)."""
        try:
            from app.services.db import fetch_table_ready_payload, init_db
            init_db()

            # filters: status, instrument, gtt_order_id
            status = request.args.get('status')
            instrument = request.args.get('instrument')
            gtt_id = request.args.get('gtt_order_id')
            page = int(request.args.get('page', '1'))
            per_page = int(request.args.get('per_page', '25'))

            data = fetch_table_ready_payload(limit=200, status=status, instrument=instrument, gtt_order_id=gtt_id, page=page, per_page=per_page)
            return jsonify({'success': True, 'data': data})
        except Exception as e:
            logger.error(f"Error fetching GTT table data: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/gtt')
    def gtt_viewer():
        """Render a simple HTML viewer for GTT orders."""
        try:
            return render_template('gtt_viewer.html')
        except Exception as e:
            logger.error(f"Error rendering GTT viewer: {e}")
            return render_template('error.html', error=str(e))

    @app.route('/api/gtt/escalation')
    def api_gtt_escalation():
        """Return a compact escalation bundle (recent raw payloads + sample requests).

        This can be downloaded and sent to vendor support. No secrets are redacted by default.
        Use ?redact=1 to remove raw session tokens.
        """
        try:
            from app.services.db import fetch_raw_payloads, init_db
            init_db()
            redact = request.args.get('redact', '0') == '1'
            raw = fetch_raw_payloads(limit=50)

            bundle = {
                'generated_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
                'records': [],
                'samples': []
            }

            for r in raw:
                payload = r['raw_payload']
                if redact:
                    # naive redaction of common token fields
                    if isinstance(payload, dict):
                        for key in ['session_token', 'X-SessionToken', 'sessionKey', 'session_key']:
                            if key in payload:
                                payload[key] = 'REDACTED'

                bundle['records'].append({'id': r['id'], 'gtt_order_id': r['gtt_order_id'], 'created_at': r['created_at'], 'raw': payload})

            # sample request text (curl) showing how we posted
            sample_curl = "curl -X POST 'https://your-host/api/gtt/ingest' -H 'Content-Type: application/json' -H 'X-API-KEY: <API_KEY>' -d @sample.json"
            bundle['samples'].append({'curl': sample_curl})

            return jsonify({'success': True, 'bundle': bundle})
        except Exception as e:
            logger.error(f"Error building escalation bundle: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {error}")
        return render_template('500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)