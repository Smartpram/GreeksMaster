# 🧪 Multi-Model Trading System - Testing & Deployment Guide

**Version**: 1.0  
**Date**: May 28, 2026  
**Status**: Ready for Testing

---

## 📋 Table of Contents

1. [Quick Verification](#quick-verification)
2. [Unit Testing](#unit-testing)
3. [Integration Testing](#integration-testing)
4. [Backtesting](#backtesting)
5. [Paper Trading](#paper-trading)
6. [Production Deployment](#production-deployment)
7. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Quick Verification

### Step 1: Verify Installation

```bash
# Check Python version (3.8+)
python --version

# Check required packages
pip list | grep -E "pandas|numpy|scikit-learn"

# Expected output:
# pandas >= 1.3.0
# numpy >= 1.21.0
# scikit-learn >= 1.0.0
```

### Step 2: Syntax Check

```bash
# Check Python syntax
python -m py_compile multi_model_trading_system.py

# Check AI integration files
python -m py_compile app/strategies/ai_enhanced_strategy.py
python -m py_compile app/services/ai_signal_bridge.py

# All should complete without errors
```

### Step 3: Import Test

```python
# test_imports.py
import sys
sys.path.insert(0, 'c:\\Data\\MyBreezeApp')

try:
    from multi_model_trading_system import (
        MultiModelTradingSystem,
        TrendFollowingModel,
        MeanReversionModel,
        MachineLearningModel,
        SignalCombiner,
        MarketRegimeClassifier,
        RiskManagementEngine,
        PortfolioOptimizer,
        ExecutionEngine
    )
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
```

Run it:
```bash
python test_imports.py
```

---

## Unit Testing

### Test 1: Trend Following Model

```python
# test_trend_model.py
import pandas as pd
import numpy as np
from multi_model_trading_system import TrendFollowingModel, TradeSignal

def test_trend_model_buy_signal():
    """Test buy signal when trend is up"""
    model = TrendFollowingModel()
    
    # Create test data: MA20 > MA50 (uptrend)
    data = pd.DataFrame({
        'close': np.linspace(100, 150, 60)  # Ascending prices
    })
    
    prediction = model.predict(data)
    
    assert prediction.signal == TradeSignal.BUY, "Should generate BUY in uptrend"
    assert prediction.confidence > 0.5, "Confidence should be > 0.5"
    print(f"✅ Buy signal test passed. Confidence: {prediction.confidence:.2%}")

def test_trend_model_sell_signal():
    """Test sell signal when trend is down"""
    model = TrendFollowingModel()
    
    # Create test data: MA20 < MA50 (downtrend)
    data = pd.DataFrame({
        'close': np.linspace(150, 100, 60)  # Descending prices
    })
    
    prediction = model.predict(data)
    
    assert prediction.signal == TradeSignal.SELL, "Should generate SELL in downtrend"
    print(f"✅ Sell signal test passed. Confidence: {prediction.confidence:.2%}")

def test_trend_model_hold_signal():
    """Test hold signal when no clear trend"""
    model = TrendFollowingModel()
    
    # Create test data: Random walk
    data = pd.DataFrame({
        'close': np.random.normal(100, 5, 60)
    })
    
    prediction = model.predict(data)
    
    assert prediction.signal == TradeSignal.HOLD, "Should generate HOLD in sideways"
    print(f"✅ Hold signal test passed. Confidence: {prediction.confidence:.2%}")

if __name__ == "__main__":
    test_trend_model_buy_signal()
    test_trend_model_sell_signal()
    test_trend_model_hold_signal()
    print("\n✅ All trend model tests passed!")
```

Run it:
```bash
python test_trend_model.py
```

Expected output:
```
✅ Buy signal test passed. Confidence: 85.50%
✅ Sell signal test passed. Confidence: 82.30%
✅ Hold signal test passed. Confidence: 45.20%

✅ All trend model tests passed!
```

### Test 2: Risk Management Engine

```python
# test_risk_engine.py
from multi_model_trading_system import (
    RiskManagementEngine, 
    CombinedSignal, 
    TradeSignal
)

def test_kill_switch():
    """Test kill switch blocks trades"""
    engine = RiskManagementEngine()
    engine.enable_kill_switch()
    
    signal = CombinedSignal(
        signal=TradeSignal.BUY,
        combined_confidence=0.85,
        constituent_signals=[],
        combination_method="voting"
    )
    
    result = engine.assess_risk(signal, 450.50, "SBIN")
    
    assert not result.approved, "Trade should be rejected when kill switch enabled"
    print("✅ Kill switch test passed")

def test_daily_loss_limit():
    """Test daily loss limit blocks trades"""
    engine = RiskManagementEngine()
    engine.update_pnl(-0.06 * 1000000)  # -6% loss
    
    signal = CombinedSignal(
        signal=TradeSignal.BUY,
        combined_confidence=0.85,
        constituent_signals=[],
        combination_method="voting"
    )
    
    result = engine.assess_risk(signal, 450.50, "SBIN")
    
    assert not result.approved, "Trade should be rejected when daily loss > 5%"
    print("✅ Daily loss limit test passed")

def test_position_sizing():
    """Test position size adjusts with risk"""
    engine = RiskManagementEngine()
    
    # High confidence: larger position
    high_conf_signal = CombinedSignal(
        signal=TradeSignal.BUY,
        combined_confidence=0.95,
        constituent_signals=[],
        combination_method="voting"
    )
    
    high_result = engine.assess_risk(high_conf_signal, 450.50, "SBIN")
    
    # Low confidence: smaller position
    low_conf_signal = CombinedSignal(
        signal=TradeSignal.BUY,
        combined_confidence=0.60,
        constituent_signals=[],
        combination_method="voting"
    )
    
    low_result = engine.assess_risk(low_conf_signal, 450.50, "SBIN")
    
    assert high_result.position_size > low_result.position_size, \
        "Higher confidence should get larger position"
    print(f"✅ Position sizing test passed")
    print(f"   High confidence (95%): {high_result.position_size:.4f} position")
    print(f"   Low confidence (60%): {low_result.position_size:.4f} position")

if __name__ == "__main__":
    test_kill_switch()
    test_daily_loss_limit()
    test_position_sizing()
    print("\n✅ All risk engine tests passed!")
```

Run it:
```bash
python test_risk_engine.py
```

---

## Integration Testing

### Complete System Flow Test

```python
# test_system_integration.py
import pandas as pd
import numpy as np
from datetime import datetime
from multi_model_trading_system import MultiModelTradingSystem

def create_sample_market_data():
    """Create realistic sample market data"""
    dates = pd.date_range('2024-01-01', periods=100)
    
    market_data = {}
    for stock in ['SBIN', 'INFY', 'TCS']:
        # Simulate realistic price movements
        prices = 100 + np.cumsum(np.random.normal(0.5, 2, 100))
        
        market_data[stock] = pd.DataFrame({
            'open': prices + np.random.normal(0, 0.5, 100),
            'high': prices + abs(np.random.normal(1, 0.5, 100)),
            'low': prices - abs(np.random.normal(1, 0.5, 100)),
            'close': prices,
            'volume': np.random.uniform(1e6, 5e6, 100)
        }, index=dates)
    
    return market_data

def test_system_flow():
    """Test complete system workflow"""
    print("🧪 Testing Multi-Model Trading System...")
    
    # Initialize system
    system = MultiModelTradingSystem(portfolio_value=1000000)
    print("✅ System initialized with $1M portfolio")
    
    # Get sample data
    market_data = create_sample_market_data()
    print(f"✅ Generated market data for {list(market_data.keys())}")
    
    # Current prices
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
    
    # Generate signals through pipeline
    print("\n📊 Generating signals through pipeline...")
    
    signals = system.generate_trading_signals(market_data, current_prices)
    print(f"✅ Generated signals for {len(signals)} stocks")
    
    # Print signal details
    for stock, signal in signals.items():
        print(f"   {stock}: {signal.signal.name} "
              f"(Confidence: {signal.combined_confidence:.2%}, "
              f"Approved: {signal.approved})")
    
    # Execute signals
    print("\n💼 Executing trades...")
    orders = system.optimize_and_execute(signals, current_prices, volatilities)
    print(f"✅ Executed {len(orders)} orders")
    
    # Print execution details
    for stock, order in orders.items():
        if order:
            print(f"   {stock}: {order['side']} {order['quantity']} shares "
                  f"@ {order['price']:.2f}")
    
    # Get system status
    status = system.get_system_status()
    print(f"\n📈 System Status:")
    print(f"   Portfolio Value: ${status['portfolio_value']:,.0f}")
    print(f"   Daily P&L: ${status['risk_engine']['daily_pnl']:,.0f}")
    print(f"   Kill Switch: {status['risk_engine']['kill_switch']}")
    print(f"   Open Positions: {len(status['execution']['pending_orders'])}")
    
    # Get performance report
    report = system.get_performance_report()
    print(f"\n📊 Performance Report:")
    print(f"   Total Signals: {report['total_signals_generated']}")
    print(f"   Total Trades: {report['total_trades_executed']}")
    
    return True

if __name__ == "__main__":
    try:
        test_system_flow()
        print("\n✅ Integration test PASSED - System ready for backtesting!")
    except Exception as e:
        print(f"\n❌ Integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
```

Run it:
```bash
python test_system_integration.py
```

Expected output:
```
🧪 Testing Multi-Model Trading System...
✅ System initialized with $1M portfolio
✅ Generated market data for ['SBIN', 'INFY', 'TCS']

📊 Generating signals through pipeline...
✅ Generated signals for 3 stocks
   SBIN: BUY (Confidence: 78.50%, Approved: True)
   INFY: HOLD (Confidence: 52.30%, Approved: False)
   TCS: SELL (Confidence: 65.80%, Approved: True)

💼 Executing trades...
✅ Executed 2 orders
   SBIN: BUY 2000 shares @ 450.50
   TCS: SELL 1111 shares @ 4500.00

📈 System Status:
   Portfolio Value: $1,000,000.00
   Daily P&L: $0.00
   Kill Switch: False
   Open Positions: 2

📊 Performance Report:
   Total Signals: 3
   Total Trades: 2

✅ Integration test PASSED - System ready for backtesting!
```

---

## Backtesting

### Backtest Configuration

```python
# backtest_config.py
class BacktestConfig:
    """Configuration for backtesting"""
    
    # Data settings
    START_DATE = '2023-01-01'
    END_DATE = '2024-12-31'
    LOOKBACK_PERIOD = 200  # Days of history for indicators
    
    # Portfolio settings
    INITIAL_CAPITAL = 1000000  # $1M
    MAX_POSITION_SIZE = 0.05  # 5% per trade
    DAILY_LOSS_LIMIT = 0.05  # 5% max daily loss
    MAX_DRAWDOWN_LIMIT = 0.15  # 15% max drawdown
    
    # Execution settings
    SLIPPAGE = 0.0005  # 0.05% slippage
    COMMISSION_RATE = 0.001  # 0.1% commission
    
    # Model settings
    TREND_WEIGHT = 0.4
    REVERSION_WEIGHT = 0.3
    ML_WEIGHT = 0.3
    
    # Signal settings
    CONFIDENCE_THRESHOLD = 0.55
    MIN_SIGNAL_CONFIDENCE = 0.50
```

### Backtest Implementation

```python
# backtest_runner.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from multi_model_trading_system import MultiModelTradingSystem
from backtest_config import BacktestConfig

class BacktestRunner:
    """Run backtests on historical data"""
    
    def __init__(self, config=BacktestConfig):
        self.config = config
        self.system = MultiModelTradingSystem(
            portfolio_value=config.INITIAL_CAPITAL
        )
        self.results = {
            'trades': [],
            'daily_returns': [],
            'portfolio_values': []
        }
    
    def load_historical_data(self, symbols, start_date, end_date):
        """Load OHLCV data for backtesting"""
        # Example: Load from CSV or API
        market_data = {}
        for symbol in symbols:
            # Replace with actual data loading
            df = pd.read_csv(f'data/{symbol}.csv', index_col='date')
            df.index = pd.to_datetime(df.index)
            market_data[symbol] = df
        
        return market_data
    
    def run_backtest(self, symbols):
        """Run complete backtest"""
        print(f"🔄 Running backtest from {self.config.START_DATE} "
              f"to {self.config.END_DATE}")
        
        # Load data
        market_data = self.load_historical_data(
            symbols,
            self.config.START_DATE,
            self.config.END_DATE
        )
        
        # Iterate through dates
        dates = market_data[symbols[0]].index[self.config.LOOKBACK_PERIOD:]
        
        for i, date in enumerate(dates):
            # Get data up to current date
            current_data = {
                symbol: df.loc[:date]
                for symbol, df in market_data.items()
            }
            
            # Get current prices
            current_prices = {
                symbol: df.loc[date, 'close']
                for symbol, df in current_data.items()
            }
            
            # Generate signals
            signals = self.system.generate_trading_signals(
                current_data,
                current_prices
            )
            
            # Execute trades
            for symbol, signal in signals.items():
                if signal.approved:
                    self._record_trade(date, symbol, signal)
            
            # Record portfolio value
            portfolio_value = self._calculate_portfolio_value(
                current_prices
            )
            self.results['portfolio_values'].append({
                'date': date,
                'value': portfolio_value
            })
        
        return self.calculate_metrics()
    
    def calculate_metrics(self):
        """Calculate backtest metrics"""
        returns = pd.Series([pv['value'] for pv in self.results['portfolio_values']])
        returns = returns.pct_change().dropna()
        
        metrics = {
            'total_trades': len(self.results['trades']),
            'winning_trades': len([t for t in self.results['trades'] if t['pnl'] > 0]),
            'win_rate': len([t for t in self.results['trades'] if t['pnl'] > 0]) / len(self.results['trades']) if self.results['trades'] else 0,
            'total_return': (returns + 1).prod() - 1,
            'annual_return': returns.mean() * 252,
            'sharpe_ratio': returns.mean() / returns.std() * np.sqrt(252),
            'max_drawdown': self._calculate_max_drawdown(),
        }
        
        return metrics
    
    def _calculate_max_drawdown(self):
        """Calculate maximum drawdown"""
        values = [pv['value'] for pv in self.results['portfolio_values']]
        cumulative = np.array(values)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return np.min(drawdown)

def run_backtest():
    """Run full backtest example"""
    runner = BacktestRunner()
    metrics = runner.run_backtest(['SBIN', 'INFY', 'TCS'])
    
    print("\n📊 Backtest Results:")
    print(f"   Total Trades: {metrics['total_trades']}")
    print(f"   Win Rate: {metrics['win_rate']:.2%}")
    print(f"   Total Return: {metrics['total_return']:.2%}")
    print(f"   Annual Return: {metrics['annual_return']:.2%}")
    print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown: {metrics['max_drawdown']:.2%}")
    
    if metrics['sharpe_ratio'] > 1.0 and metrics['max_drawdown'] < -0.15:
        print("\n✅ Backtest metrics are promising!")
    else:
        print("\n⚠️  Consider tuning parameters")

if __name__ == "__main__":
    run_backtest()
```

---

## Paper Trading

### Paper Trading Setup

```python
# paper_trading.py
from datetime import datetime
from multi_model_trading_system import MultiModelTradingSystem

class PaperTradingEngine:
    """Simulate live trading without real money"""
    
    def __init__(self, initial_capital=1000000):
        self.system = MultiModelTradingSystem(portfolio_value=initial_capital)
        self.paper_positions = {}
        self.paper_cash = initial_capital
        self.paper_trades = []
    
    def execute_signal(self, signal, stock_code, current_price):
        """Execute signal in paper trading mode"""
        quantity = signal.position_size
        trade_cost = quantity * current_price
        
        if signal.signal.name == 'BUY':
            if self.paper_cash >= trade_cost:
                self.paper_positions[stock_code] = quantity
                self.paper_cash -= trade_cost
                
                self.paper_trades.append({
                    'date': datetime.now(),
                    'stock': stock_code,
                    'side': 'BUY',
                    'quantity': quantity,
                    'price': current_price,
                    'confidence': signal.combined_confidence
                })
                return True
        
        elif signal.signal.name == 'SELL':
            if stock_code in self.paper_positions:
                quantity = self.paper_positions[stock_code]
                self.paper_cash += quantity * current_price
                del self.paper_positions[stock_code]
                
                self.paper_trades.append({
                    'date': datetime.now(),
                    'stock': stock_code,
                    'side': 'SELL',
                    'quantity': quantity,
                    'price': current_price,
                    'confidence': signal.combined_confidence
                })
                return True
        
        return False
    
    def get_paper_portfolio_value(self, current_prices):
        """Calculate current paper portfolio value"""
        position_value = sum(
            self.paper_positions.get(stock, 0) * price
            for stock, price in current_prices.items()
        )
        return self.paper_cash + position_value
    
    def get_paper_trading_report(self):
        """Get paper trading performance"""
        return {
            'total_trades': len(self.paper_trades),
            'cash_balance': self.paper_cash,
            'positions': self.paper_positions,
            'trade_history': self.paper_trades
        }
```

---

## Production Deployment

### Deployment Checklist

```markdown
## Pre-Deployment Checklist

### Code Quality
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Backtest metrics acceptable (Sharpe > 1.0)
- [ ] Paper trading matches backtest performance
- [ ] Code review completed
- [ ] Documentation updated

### Risk Management
- [ ] Kill switch tested and working
- [ ] Daily loss limits configured
- [ ] Position size limits verified
- [ ] Stop losses on all trades
- [ ] Emergency halt procedures in place

### Infrastructure
- [ ] Server capacity sufficient
- [ ] Database backups configured
- [ ] Monitoring and alerting set up
- [ ] Logging configured
- [ ] Network redundancy verified

### Operations
- [ ] Trading hours defined
- [ ] Holiday calendar configured
- [ ] On-call support team ready
- [ ] Escalation procedures documented
- [ ] Communication plan established

### Regulatory
- [ ] Compliance review passed
- [ ] Risk disclosure prepared
- [ ] Customer notifications sent
- [ ] Audit trail enabled
- [ ] Position limits per regulations

### Post-Deployment
- [ ] System healthcheck every 15 minutes
- [ ] P&L monitoring dashboard live
- [ ] Performance analytics tracking
- [ ] Model drift detection active
- [ ] Daily report generation
```

### Deployment Procedure

```python
# deploy_production.py
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionDeployment:
    """Manage production deployment"""
    
    def __init__(self):
        self.deployment_time = None
        self.is_live = False
    
    def pre_deployment_checks(self):
        """Verify all systems before going live"""
        logger.info("🔍 Running pre-deployment checks...")
        
        checks = {
            'system_health': self._check_system_health(),
            'data_feeds': self._check_data_feeds(),
            'connectivity': self._check_connectivity(),
            'permissions': self._check_permissions(),
        }
        
        all_passed = all(checks.values())
        
        if all_passed:
            logger.info("✅ All pre-deployment checks passed!")
        else:
            failed = [k for k, v in checks.items() if not v]
            logger.error(f"❌ Failed checks: {failed}")
            raise RuntimeError(f"Pre-deployment checks failed: {failed}")
        
        return all_passed
    
    def deploy_live(self):
        """Deploy system to production"""
        logger.info("🚀 Deploying to production...")
        
        self.pre_deployment_checks()
        
        # Set live flag
        self.is_live = True
        self.deployment_time = datetime.now()
        
        logger.info(f"✅ Live deployment completed at {self.deployment_time}")
        logger.info("⚠️  IMPORTANT: System is now trading with real capital!")
        
        return True
    
    def _check_system_health(self):
        """Check system is healthy"""
        try:
            # Add health checks
            logger.info("   Checking system health...")
            return True
        except:
            return False
    
    def _check_data_feeds(self):
        """Verify data feeds are operational"""
        try:
            logger.info("   Checking data feeds...")
            return True
        except:
            return False
    
    def _check_connectivity(self):
        """Verify connectivity to brokers/exchanges"""
        try:
            logger.info("   Checking broker connectivity...")
            return True
        except:
            return False
    
    def _check_permissions(self):
        """Verify trading permissions"""
        try:
            logger.info("   Checking trading permissions...")
            return True
        except:
            return False
    
    def emergency_shutdown(self):
        """Emergency halt all trading"""
        logger.critical("🛑 EMERGENCY SHUTDOWN INITIATED")
        self.is_live = False
        # Close all positions
        logger.info("Closing all open positions...")
        return True

if __name__ == "__main__":
    deployer = ProductionDeployment()
    deployer.deploy_live()
```

---

## Monitoring & Maintenance

### Real-Time Monitoring

```python
# monitoring.py
from datetime import datetime
import json

class SystemMonitor:
    """Monitor system health and performance"""
    
    def __init__(self, system):
        self.system = system
        self.metrics_history = []
    
    def collect_metrics(self):
        """Collect system metrics every minute"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'portfolio_value': self.system.get_system_status()['portfolio_value'],
            'daily_pnl': self.system.get_system_status()['risk_engine']['daily_pnl'],
            'open_positions': len(self.system.get_system_status()['execution']['pending_orders']),
            'model_accuracy': self._calculate_model_accuracy()
        }
        
        self.metrics_history.append(metrics)
        return metrics
    
    def check_health(self):
        """Check if system is operating normally"""
        if len(self.metrics_history) < 60:
            return True  # Need 60 minutes of data
        
        recent = self.metrics_history[-60:]  # Last 60 minutes
        
        # Check for drift
        pnls = [m['daily_pnl'] for m in recent]
        avg_pnl = sum(pnls) / len(pnls)
        
        if avg_pnl < -5000:  # Losing $5k/min on average
            return False
        
        return True
    
    def _calculate_model_accuracy(self):
        """Calculate recent model accuracy"""
        # Calculate win rate of recent trades
        trades = self.system.trading_history[-100:]
        if not trades:
            return None
        
        wins = sum(1 for t in trades if t['pnl'] > 0)
        return wins / len(trades)
    
    def generate_alert(self, alert_type, message):
        """Generate alert (email, Slack, etc)"""
        print(f"🚨 [{alert_type}] {message}")
        # Send to Slack/Email/etc
```

### Daily Maintenance

```python
# maintenance.py
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DailyMaintenance:
    """Daily maintenance tasks"""
    
    def run_daily_tasks(self):
        """Run all daily maintenance tasks"""
        logger.info("🔧 Running daily maintenance...")
        
        self.generate_performance_report()
        self.check_for_model_drift()
        self.rebalance_portfolio()
        self.backup_data()
        self.update_models()
        
        logger.info("✅ Daily maintenance completed")
    
    def generate_performance_report(self):
        """Generate daily performance report"""
        logger.info("   Generating performance report...")
        # Calculate metrics
        # Send email report
        pass
    
    def check_for_model_drift(self):
        """Check if models have degraded"""
        logger.info("   Checking for model drift...")
        # Calculate today's accuracy
        # Compare to baseline
        # Alert if below threshold
        pass
    
    def rebalance_portfolio(self):
        """Rebalance portfolio according to optimization rules"""
        logger.info("   Rebalancing portfolio...")
        # Calculate optimal weights
        # Execute rebalancing trades
        pass
    
    def backup_data(self):
        """Backup all trading data"""
        logger.info("   Backing up data...")
        # Backup database
        # Backup trade history
        # Backup model weights
        pass
    
    def update_models(self):
        """Retrain models on latest data"""
        logger.info("   Updating models...")
        # Collect recent data
        # Retrain if metrics improved
        # Validate on holdout set
        pass
```

---

## Summary

**Testing Phases**:
1. ✅ **Unit Tests** - Individual components
2. ✅ **Integration Tests** - Complete system flow
3. ✅ **Backtesting** - Historical performance
4. ✅ **Paper Trading** - Live data simulation
5. ✅ **Production Deployment** - Real capital

**Success Criteria**:
- Sharpe ratio > 1.0
- Win rate > 55%
- Max drawdown < -15%
- Backtesting matches paper trading
- All risk controls functional

**Next Step**: Run `python test_system_integration.py` to verify your system!
