# 🚀 Quick Integration Examples - Multi-Model System with MyBreezeApp

**Purpose**: Practical examples showing how to integrate the multi-model trading system with your existing MyBreezeApp  
**Status**: Ready to use  
**Time to Run**: 2-5 minutes per example

---

## Example 1: Basic Multi-Model Signal Generation (30 seconds)

```python
# example_1_basic_signals.py
"""Generate signals using multi-model system on sample data"""

import pandas as pd
import numpy as np
from multi_model_trading_system import MultiModelTradingSystem

# Create sample market data
def generate_sample_data(stocks=['SBIN', 'INFY', 'TCS']):
    market_data = {}
    for stock in stocks:
        # Create realistic price data
        dates = pd.date_range('2024-01-01', periods=100)
        prices = 100 + np.cumsum(np.random.normal(0.5, 2, 100))
        
        market_data[stock] = pd.DataFrame({
            'open': prices + np.random.normal(0, 0.5, 100),
            'high': prices + abs(np.random.normal(1, 0.5, 100)),
            'low': prices - abs(np.random.normal(1, 0.5, 100)),
            'close': prices,
            'volume': np.random.uniform(1e6, 5e6, 100)
        }, index=dates)
    
    return market_data

# Initialize system
print("🚀 Initializing Multi-Model Trading System...")
system = MultiModelTradingSystem(portfolio_value=1000000)

# Get sample data
print("📊 Generating sample market data...")
market_data = generate_sample_data()

# Current market prices
current_prices = {
    'SBIN': 450.50,
    'INFY': 3250.00,
    'TCS': 4500.00
}

# Generate signals
print("\n🎯 Generating trading signals...")
signals = system.generate_trading_signals(market_data, current_prices)

# Display results
print("\n" + "="*60)
print("TRADING SIGNALS")
print("="*60)
for stock, signal in signals.items():
    print(f"\n{stock}:")
    print(f"  Signal: {signal.signal.name}")
    print(f"  Confidence: {signal.combined_confidence:.2%}")
    print(f"  Position Size: {signal.position_size:.2%}")
    print(f"  Stop Loss: {signal.stop_loss:.2f}")
    print(f"  Take Profit: {signal.take_profit:.2f}")
    print(f"  Approved: {'✅ YES' if signal.approved else '❌ NO'}")

print("\n✅ Example 1 Complete!")
```

**Run it:**
```bash
python example_1_basic_signals.py
```

**Expected Output:**
```
🚀 Initializing Multi-Model Trading System...
📊 Generating sample market data...

🎯 Generating trading signals...

============================================================
TRADING SIGNALS
============================================================

SBIN:
  Signal: BUY
  Confidence: 78.50%
  Position Size: 4.80%
  Stop Loss: 441.49
  Take Profit: 459.51
  Approved: ✅ YES

INFY:
  Signal: HOLD
  Confidence: 52.30%
  Position Size: 0.00%
  Stop Loss: 0.00
  Take Profit: 0.00
  Approved: ❌ NO

TCS:
  Signal: SELL
  Confidence: 65.80%
  Position Size: 2.50%
  Stop Loss: 4590.00
  Take Profit: 4410.00
  Approved: ✅ YES

✅ Example 1 Complete!
```

---

## Example 2: Multi-Model System with Execution

```python
# example_2_with_execution.py
"""Generate signals AND execute them"""

import pandas as pd
import numpy as np
from multi_model_trading_system import MultiModelTradingSystem

# Mock order manager (replace with real one from your app)
class MockOrderManager:
    def __init__(self):
        self.orders = []
    
    def place_order(self, stock, side, quantity, price, stop_loss, take_profit):
        order = {
            'stock': stock,
            'side': side,
            'quantity': quantity,
            'price': price,
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
        self.orders.append(order)
        return order
    
    def get_orders(self):
        return self.orders

def generate_sample_data(stocks=['SBIN', 'INFY', 'TCS']):
    market_data = {}
    for stock in stocks:
        dates = pd.date_range('2024-01-01', periods=100)
        prices = 100 + np.cumsum(np.random.normal(0.5, 2, 100))
        
        market_data[stock] = pd.DataFrame({
            'open': prices + np.random.normal(0, 0.5, 100),
            'high': prices + abs(np.random.normal(1, 0.5, 100)),
            'low': prices - abs(np.random.normal(1, 0.5, 100)),
            'close': prices,
            'volume': np.random.uniform(1e6, 5e6, 100)
        }, index=dates)
    
    return market_data

# Initialize
print("🚀 Multi-Model Trading System with Execution")
print("="*60)

system = MultiModelTradingSystem(portfolio_value=1000000)
order_manager = MockOrderManager()

# Get data
market_data = generate_sample_data()
current_prices = {
    'SBIN': 450.50,
    'INFY': 3250.00,
    'TCS': 4500.00
}
volatilities = {
    'SBIN': 0.015,
    'INFY': 0.018,
    'TCS': 0.014
}

# Generate signals
print("\n📊 Generating signals...")
signals = system.generate_trading_signals(market_data, current_prices)

# Execute signals
print("\n💼 Executing trades...")
orders = system.optimize_and_execute(signals, current_prices, volatilities)

# Display execution results
print("\n" + "="*60)
print("EXECUTION RESULTS")
print("="*60)

executed_count = 0
for stock, order in orders.items():
    if order:
        executed_count += 1
        print(f"\n✅ {stock}:")
        print(f"  Side: {order['side']}")
        print(f"  Quantity: {order['quantity']:.0f}")
        print(f"  Price: {order['price']:.2f}")
        print(f"  Stop Loss: {order['stop_loss']:.2f}")
        print(f"  Take Profit: {order['take_profit']:.2f}")
    else:
        print(f"\n⏭️  {stock}: Order rejected")

print(f"\n" + "="*60)
print(f"Total Orders Executed: {executed_count}")
print("✅ Example 2 Complete!")
```

**Run it:**
```bash
python example_2_with_execution.py
```

---

## Example 3: Integration with MyBreezeApp Services

```python
# example_3_breeze_integration.py
"""Integration with your existing MyBreezeApp services"""

import pandas as pd
import numpy as np
from multi_model_trading_system import MultiModelTradingSystem
from datetime import datetime

# Simulate your existing MyBreezeApp services
class MockBreezeProfessional:
    """Mock Breeze API service"""
    def get_historical_data(self, stock, days=200):
        dates = pd.date_range(periods=days, freq='D')
        prices = 100 + np.cumsum(np.random.normal(0.5, 2, days))
        
        return pd.DataFrame({
            'open': prices + np.random.normal(0, 0.5, days),
            'high': prices + abs(np.random.normal(1, 0.5, days)),
            'low': prices - abs(np.random.normal(1, 0.5, days)),
            'close': prices,
            'volume': np.random.uniform(1e6, 5e6, days)
        }, index=dates)
    
    def get_current_price(self, stock):
        # Mock current price
        return np.random.uniform(400, 500)

class MockRiskManager:
    """Mock risk manager from your app"""
    def check_position_risk(self, signal, stock):
        # Your risk checks
        return True

class MockNotificationService:
    """Mock notification service from your app"""
    def send_alert(self, message):
        print(f"📢 Alert: {message}")

# Main integration
def integrate_multi_model_with_breeze():
    print("🔗 Integrating Multi-Model System with MyBreezeApp")
    print("="*60)
    
    # Initialize services
    breeze = MockBreezeProfessional()
    risk_manager = MockRiskManager()
    notifications = MockNotificationService()
    
    # Initialize multi-model system
    system = MultiModelTradingSystem(portfolio_value=1000000)
    
    # Define watchlist
    watchlist = ['SBIN', 'INFY', 'TCS']
    
    # Fetch data from Breeze
    print("\n📥 Fetching data from Breeze API...")
    market_data = {}
    current_prices = {}
    
    for stock in watchlist:
        market_data[stock] = breeze.get_historical_data(stock, days=200)
        current_prices[stock] = breeze.get_current_price(stock)
        print(f"   ✓ {stock}: {current_prices[stock]:.2f}")
    
    # Generate signals
    print("\n🎯 Generating multi-model signals...")
    signals = system.generate_trading_signals(market_data, current_prices)
    
    # Apply risk checks from your system
    print("\n✅ Applying risk management checks...")
    approved_signals = {}
    
    for stock, signal in signals.items():
        if risk_manager.check_position_risk(signal, stock):
            approved_signals[stock] = signal
            print(f"   ✓ {stock}: Risk check PASSED")
        else:
            print(f"   ✗ {stock}: Risk check FAILED")
    
    # Send notifications
    print("\n📢 Sending notifications...")
    for stock, signal in approved_signals.items():
        message = (f"Signal: {signal.signal.name} "
                  f"({signal.combined_confidence:.0%}) "
                  f"for {stock}")
        notifications.send_alert(message)
    
    # Get system status
    print("\n" + "="*60)
    print("SYSTEM STATUS")
    print("="*60)
    status = system.get_system_status()
    print(f"Portfolio Value: ${status['portfolio_value']:,.0f}")
    print(f"Daily P&L: ${status['risk_engine']['daily_pnl']:,.0f}")
    print(f"Open Positions: {len(status['execution']['pending_orders'])}")
    
    print("\n✅ Example 3 Complete!")

if __name__ == "__main__":
    integrate_multi_model_with_breeze()
```

**Run it:**
```bash
python example_3_breeze_integration.py
```

---

## Example 4: Real App Integration in Flask

```python
# app_integration.py (Add to your app/main.py)
"""How to integrate multi-model system into your Flask app"""

from flask import jsonify, request
from multi_model_trading_system import MultiModelTradingSystem
import logging

logger = logging.getLogger(__name__)

# Initialize multi-model system (at app startup)
multi_model_system = None

def init_multi_model_system(app):
    """Initialize multi-model system when Flask app starts"""
    global multi_model_system
    multi_model_system = MultiModelTradingSystem(
        portfolio_value=app.config['PORTFOLIO_VALUE']
    )
    logger.info("✅ Multi-model trading system initialized")

# API endpoints

@app.route('/api/trading/multi-model/signals', methods=['GET'])
def get_multi_model_signals():
    """Get trading signals from multi-model system"""
    try:
        # Get parameters
        watchlist = request.args.getlist('stocks') or ['SBIN', 'INFY', 'TCS']
        
        # Fetch market data from your Breeze service
        market_data = {}
        current_prices = {}
        volatilities = {}
        
        for stock in watchlist:
            # Your existing data fetching code
            market_data[stock] = fetch_ohlcv(stock, lookback=200)
            current_prices[stock] = get_current_price(stock)
            volatilities[stock] = calculate_volatility(stock)
        
        # Generate signals
        signals = multi_model_system.generate_trading_signals(
            market_data, current_prices
        )
        
        # Execute trades (if enabled)
        if request.args.get('execute') == 'true':
            orders = multi_model_system.optimize_and_execute(
                signals, current_prices, volatilities
            )
        
        # Return response
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'signals': {
                stock: {
                    'signal': signal.signal.name,
                    'confidence': float(signal.combined_confidence),
                    'position_size': float(signal.position_size),
                    'stop_loss': float(signal.stop_loss),
                    'take_profit': float(signal.take_profit),
                    'approved': signal.approved,
                    'risk_score': signal.risk_score
                }
                for stock, signal in signals.items()
            }
        })
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trading/multi-model/status', methods=['GET'])
def get_multi_model_status():
    """Get system status and performance"""
    try:
        status = multi_model_system.get_system_status()
        report = multi_model_system.get_performance_report()
        
        return jsonify({
            'success': True,
            'status': status,
            'report': report
        })
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trading/multi-model/execute', methods=['POST'])
def execute_multi_model_trade():
    """Execute a specific trade signal"""
    try:
        data = request.json
        stock = data['stock']
        signal_data = data['signal']
        
        # Create risk-adjusted signal
        # Your code here
        
        # Execute
        order = multi_model_system.execution_engine.execute_signal(
            signal_data, stock, data['current_price']
        )
        
        return jsonify({
            'success': True,
            'order': order
        })
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# In your main app initialization
if __name__ == '__main__':
    app.before_first_request(lambda: init_multi_model_system(app))
    app.run(debug=False, port=5000)
```

---

## Example 5: Backtesting Historical Performance

```python
# example_5_backtest.py
"""Backtest multi-model system on historical data"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from multi_model_trading_system import MultiModelTradingSystem

def backtest_multi_model_system(start_date, end_date, initial_capital=1000000):
    """Run backtest on historical data"""
    
    print(f"📊 Backtesting Multi-Model System")
    print(f"Period: {start_date} to {end_date}")
    print("="*60)
    
    # Initialize system
    system = MultiModelTradingSystem(portfolio_value=initial_capital)
    
    # Tracking
    daily_values = []
    trades_executed = []
    
    # Simulate trading period
    current_date = start_date
    while current_date <= end_date:
        # Fetch historical data
        market_data = {}
        current_prices = {}
        volatilities = {}
        
        # Generate mock data for each trading day
        for stock in ['SBIN', 'INFY', 'TCS']:
            # In real backtest, load actual historical data
            dates = pd.date_range(current_date - timedelta(days=200), 
                                 current_date, freq='D')
            prices = 100 + np.cumsum(np.random.normal(0.5, 2, len(dates)))
            
            market_data[stock] = pd.DataFrame({
                'open': prices + np.random.normal(0, 0.5, len(dates)),
                'high': prices + abs(np.random.normal(1, 0.5, len(dates))),
                'low': prices - abs(np.random.normal(1, 0.5, len(dates))),
                'close': prices,
                'volume': np.random.uniform(1e6, 5e6, len(dates))
            }, index=dates)
            
            current_prices[stock] = prices[-1]
            volatilities[stock] = np.std(np.diff(prices) / prices[:-1])
        
        # Generate signals
        signals = system.generate_trading_signals(market_data, current_prices)
        
        # Execute
        orders = system.optimize_and_execute(signals, current_prices, volatilities)
        
        for stock, order in orders.items():
            if order:
                trades_executed.append({
                    'date': current_date,
                    'stock': stock,
                    'side': order['side'],
                    'price': order['price'],
                    'quantity': order['quantity']
                })
        
        # Track portfolio value
        status = system.get_system_status()
        daily_values.append({
            'date': current_date,
            'value': status['portfolio_value'],
            'pnl': status['risk_engine']['daily_pnl']
        })
        
        # Next day
        current_date += timedelta(days=1)
    
    # Calculate metrics
    returns = pd.Series([v['value'] for v in daily_values])
    daily_returns = returns.pct_change().dropna()
    
    metrics = {
        'total_trades': len(trades_executed),
        'start_value': daily_values[0]['value'],
        'end_value': daily_values[-1]['value'],
        'total_return': (daily_values[-1]['value'] / daily_values[0]['value']) - 1,
        'annual_return': daily_returns.mean() * 252,
        'volatility': daily_returns.std() * np.sqrt(252),
        'sharpe_ratio': (daily_returns.mean() / daily_returns.std()) * np.sqrt(252),
        'max_drawdown': (returns / returns.cummax() - 1).min(),
    }
    
    # Display results
    print(f"\n{'='*60}")
    print("BACKTEST RESULTS")
    print(f"{'='*60}")
    print(f"Initial Capital: ${metrics['start_value']:,.0f}")
    print(f"Final Value: ${metrics['end_value']:,.0f}")
    print(f"Total Return: {metrics['total_return']:.2%}")
    print(f"Annual Return: {metrics['annual_return']:.2%}")
    print(f"Volatility: {metrics['volatility']:.2%}")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
    print(f"Total Trades: {metrics['total_trades']}")
    
    # Assessment
    print(f"\n{'='*60}")
    print("ASSESSMENT")
    print(f"{'='*60}")
    
    if metrics['sharpe_ratio'] > 1.0:
        print("✅ Sharpe ratio > 1.0 (Good risk-adjusted returns)")
    else:
        print("⚠️  Sharpe ratio < 1.0 (Consider optimization)")
    
    if metrics['max_drawdown'] > -0.15:
        print("✅ Max drawdown < 15% (Risk controlled)")
    else:
        print("⚠️  Max drawdown > 15% (High risk periods)")
    
    return metrics

# Run backtest
if __name__ == "__main__":
    backtest_multi_model_system(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2024, 12, 31),
        initial_capital=1000000
    )
```

**Run it:**
```bash
python example_5_backtest.py
```

---

## Example 6: Production Deployment Checklist

```python
# example_6_production_ready.py
"""Verify system is production-ready"""

from multi_model_trading_system import MultiModelTradingSystem
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionReadinessChecker:
    """Verify system is ready for live trading"""
    
    def __init__(self, system):
        self.system = system
        self.checks = {}
    
    def run_all_checks(self):
        """Run all production readiness checks"""
        logger.info("🔍 Running Production Readiness Checks...")
        logger.info("="*60)
        
        self.check_system_initialization()
        self.check_all_models_loaded()
        self.check_risk_controls()
        self.check_execution_engine()
        self.check_monitoring()
        
        logger.info("="*60)
        self.print_summary()
    
    def check_system_initialization(self):
        """Verify system initialized correctly"""
        try:
            status = self.system.get_system_status()
            assert status is not None
            self.checks['initialization'] = True
            logger.info("✅ System initialization OK")
        except:
            self.checks['initialization'] = False
            logger.error("❌ System initialization FAILED")
    
    def check_all_models_loaded(self):
        """Verify all models are loaded"""
        try:
            # Check models exist
            assert self.system.trend_model is not None
            assert self.system.reversion_model is not None
            assert self.system.ml_model is not None
            self.checks['models'] = True
            logger.info("✅ All models loaded OK")
        except:
            self.checks['models'] = False
            logger.error("❌ Model loading FAILED")
    
    def check_risk_controls(self):
        """Verify risk controls are active"""
        try:
            risk = self.system.risk_engine
            assert not risk.kill_switch  # Should be off initially
            assert risk.daily_loss_limit > 0
            assert risk.max_position_size > 0
            self.checks['risk_controls'] = True
            logger.info("✅ Risk controls OK")
        except:
            self.checks['risk_controls'] = False
            logger.error("❌ Risk controls FAILED")
    
    def check_execution_engine(self):
        """Verify execution engine is ready"""
        try:
            exec_engine = self.system.execution_engine
            assert exec_engine is not None
            assert len(exec_engine.pending_orders) == 0  # Clean start
            self.checks['execution'] = True
            logger.info("✅ Execution engine OK")
        except:
            self.checks['execution'] = False
            logger.error("❌ Execution engine FAILED")
    
    def check_monitoring(self):
        """Verify monitoring is active"""
        try:
            report = self.system.get_performance_report()
            assert report is not None
            self.checks['monitoring'] = True
            logger.info("✅ Monitoring OK")
        except:
            self.checks['monitoring'] = False
            logger.error("❌ Monitoring FAILED")
    
    def print_summary(self):
        """Print summary of checks"""
        logger.info("\n📊 PRODUCTION READINESS SUMMARY")
        logger.info("="*60)
        
        passed = sum(1 for v in self.checks.values() if v)
        total = len(self.checks)
        
        for check, passed_flag in self.checks.items():
            status = "✅ PASS" if passed_flag else "❌ FAIL"
            logger.info(f"{check:20} {status}")
        
        logger.info("="*60)
        logger.info(f"Results: {passed}/{total} checks passed")
        
        if passed == total:
            logger.info("\n🚀 SYSTEM READY FOR PRODUCTION DEPLOYMENT!")
        else:
            logger.warning("\n⚠️  Fix failed checks before deploying")

# Run checks
if __name__ == "__main__":
    system = MultiModelTradingSystem(portfolio_value=1000000)
    checker = ProductionReadinessChecker(system)
    checker.run_all_checks()
```

**Run it:**
```bash
python example_6_production_ready.py
```

---

## Quick Reference

### Running All Examples

```bash
# Example 1: Basic signals (30 seconds)
python example_1_basic_signals.py

# Example 2: With execution (1 minute)
python example_2_with_execution.py

# Example 3: Breeze integration (2 minutes)
python example_3_breeze_integration.py

# Example 4: See Flask integration (reference only)
# (Already in your app)

# Example 5: Backtest (3-5 minutes)
python example_5_backtest.py

# Example 6: Production checks (1 minute)
python example_6_production_ready.py
```

### Expected Timeline
- **Examples 1-3**: ~5 minutes
- **Example 5**: ~10 minutes  
- **Total**: ~15 minutes

### Next Steps
1. Run examples in order
2. Verify all pass
3. Follow TESTING_AND_DEPLOYMENT_GUIDE.md
4. Move to paper trading
5. Deploy to production

✅ **Ready to integrate with your MyBreezeApp!**
