"""
MyBreezeApp - Algorithmic Trading Application
Main Flask Application Entry Point
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from app.services.breeze_api import BreezeAPIService
from app.services.data_stream import DataStreamService
from app.services.order_manager import OrderManager
from app.services.risk_manager import RiskManager
from app.services.backtesting import BacktestingEngine
from app.services.notifications import NotificationService
from app.services.auth_service import AuthService
from app.strategies.buy_hold_trend import BuyHoldTrendStrategy
from app.config import Config
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize services
    breeze_service = BreezeAPIService()
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
            
            exchange_code = request.args.get('exchange', 'NSE')
            quotes = breeze_service.get_quotes(stock_code, exchange_code)
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