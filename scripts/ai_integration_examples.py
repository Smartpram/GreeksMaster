"""
AI Integration Example - Complete Working Example
Demonstrates how to integrate AI signals into your trading system
"""

import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_simple_ai_signal_generation():
    """
    Example 1: Simple AI Signal Generation
    Generates a single AI signal for a stock
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Simple AI Signal Generation")
    print("="*60)
    
    try:
        from ai_trading_engine import AISignalGenerator
        import numpy as np
        
        # Create sample OHLCV data
        n_samples = 500
        data = {
            'open': np.random.normal(100, 10, n_samples),
            'high': np.random.normal(102, 10, n_samples),
            'low': np.random.normal(98, 10, n_samples),
            'close': np.random.normal(100, 10, n_samples),
            'volume': np.random.normal(1000000, 100000, n_samples)
        }
        df = pd.DataFrame(data)
        
        # Initialize AI
        print("\n1. Setting up AI Signal Generator...")
        ai = AISignalGenerator(df)
        ai.setup()
        
        # Generate signal
        print("2. Generating signal...")
        signal = ai.generate_signal()
        
        # Display results
        print(f"\n✅ Signal Generated:")
        print(f"   Direction: {signal['signal']}")
        print(f"   Confidence: {signal['confidence']:.2%}")
        print(f"   Valid: {signal['valid']}")
        print(f"   Signal Strength: {signal['signal_strength']:.2%}")
        
        return signal
    
    except Exception as e:
        logger.error(f"Error in example 1: {e}")
        return None


def example_2_ai_strategy_integration():
    """
    Example 2: AI Strategy Integration
    Integrates AI with the AIEnhancedStrategy class
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: AI Strategy Integration")
    print("="*60)
    
    try:
        from app.strategies.ai_enhanced_strategy import AIEnhancedStrategy
        import numpy as np
        
        # Create mock services (in real app, use actual services)
        class MockService:
            def send_notification(self, msg, level):
                print(f"[NOTIFICATION] {msg}")
        
        # Create sample market data
        def create_sample_market_data(stocks=['SBIN', 'INFY', 'TCS']):
            data = {}
            for stock in stocks:
                n = 500
                data[stock] = [{
                    'open': float(100 + i*0.1),
                    'high': float(102 + i*0.1),
                    'low': float(98 + i*0.1),
                    'close': float(100 + i*0.1),
                    'volume': 1000000
                } for i in range(n)]
            return data
        
        # Initialize strategy
        print("\n1. Initializing AI Enhanced Strategy...")
        strategy = AIEnhancedStrategy(
            order_manager=None,
            risk_manager=None,
            notification_service=MockService(),
            enable_ai=True,
            ai_confidence_threshold=0.55
        )
        
        # Set watchlist
        watchlist = ['SBIN', 'INFY', 'TCS']
        strategy.set_watchlist(watchlist)
        print(f"   Watchlist: {watchlist}")
        
        # Get market data
        print("\n2. Fetching market data...")
        market_data = create_sample_market_data(watchlist)
        print(f"   Got data for {len(market_data)} stocks")
        
        # Generate signals
        print("\n3. Generating signals...")
        signals = strategy.generate_signals(market_data)
        
        # Display results
        print(f"\n✅ Signals Generated: {len(signals)}")
        for stock, signal in signals.items():
            print(f"\n   {stock}:")
            print(f"   - Action: {signal['action']}")
            print(f"   - Confidence: {signal['confidence']:.2%}")
            print(f"   - Entry Price: {signal['entry_price']:.2f}")
            print(f"   - Source: {signal['signal_source']}")
        
        # Get AI stats
        stats = strategy.get_ai_stats()
        print(f"\n📊 AI Statistics:")
        print(f"   - AI Enabled: {stats['ai_enabled']}")
        print(f"   - Total Signals: {stats['total_signals_generated']}")
        print(f"   - By Source: {stats['signals_by_source']}")
        
        return signals
    
    except Exception as e:
        logger.error(f"Error in example 2: {e}")
        return None


def example_3_ai_signal_bridge():
    """
    Example 3: AI Signal Bridge
    Demonstrates the signal bridge service
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: AI Signal Bridge")
    print("="*60)
    
    try:
        from app.services.ai_signal_bridge import AISignalBridge
        import numpy as np
        
        # Initialize bridge
        print("\n1. Initializing AI Signal Bridge...")
        bridge = AISignalBridge()
        
        # Create sample data
        n = 500
        sample_data = {
            'SBIN': [{
                'open': float(100 + i*0.1),
                'high': float(102 + i*0.1),
                'low': float(98 + i*0.1),
                'close': float(100 + i*0.1),
                'volume': 1000000
            } for i in range(n)]
        }
        
        # Initialize with data
        print("2. Initializing AI with market data...")
        bridge.initialize_ai(sample_data)
        print("   ✅ AI initialized")
        
        # Generate signal
        print("\n3. Generating signal for SBIN...")
        df = pd.DataFrame(sample_data['SBIN'])
        signal = bridge.generate_ai_signal('SBIN', data=df)
        
        if signal:
            print(f"\n✅ Signal Generated:")
            print(f"   Stock: {signal['stock_code']}")
            print(f"   Signal: {signal['signal']}")
            print(f"   Confidence: {signal['confidence']:.2%}")
            print(f"   Entry Price: {signal['entry_price']:.2f}")
            print(f"   Stop Loss: {signal['stop_loss_pct']}%")
            print(f"   Target: {signal['target_pct']}%")
            
            # Validate signal
            print("\n4. Validating signal...")
            is_valid, reason = bridge.validate_signal(signal)
            print(f"   Valid: {is_valid}")
            if not is_valid:
                print(f"   Reason: {reason}")
        else:
            print("   ❌ No signal generated")
        
        # Get performance report
        print("\n5. Getting performance report...")
        report = bridge.get_performance_report()
        print(f"\n📊 Performance Report:")
        print(f"   Total Signals: {report['total_signals']}")
        print(f"   Successful: {report['successful_trades']}")
        print(f"   Failed: {report['failed_trades']}")
        print(f"   Average Confidence: {report['avg_confidence']:.2%}")
        
        return signal
    
    except Exception as e:
        logger.error(f"Error in example 3: {e}")
        return None


def example_4_signal_combination():
    """
    Example 4: Combine Technical + AI Signals
    Shows how technical and AI signals are combined
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: Technical + AI Signal Combination")
    print("="*60)
    
    try:
        from app.strategies.ai_enhanced_strategy import AIEnhancedStrategy
        import numpy as np
        
        # Create sample data
        def create_realistic_market_data(n=500):
            """Create more realistic market data"""
            close = np.random.normal(100, 10, n)
            close = np.cumsum(np.random.normal(0, 0.5, n)) + 100  # Random walk
            
            return pd.DataFrame({
                'open': close * (1 + np.random.normal(0, 0.001, n)),
                'high': close * (1 + abs(np.random.normal(0, 0.01, n))),
                'low': close * (1 - abs(np.random.normal(0, 0.01, n))),
                'close': close,
                'volume': np.random.normal(1000000, 100000, n)
            })
        
        # Initialize strategy
        print("\n1. Setting up AI Enhanced Strategy...")
        
        class MockService:
            def send_notification(self, msg, level):
                pass
        
        strategy = AIEnhancedStrategy(
            order_manager=None,
            risk_manager=None,
            notification_service=MockService(),
            enable_ai=True,
            ai_confidence_threshold=0.55
        )
        
        # Create sample data
        print("2. Creating realistic market data...")
        df = create_realistic_market_data()
        
        # Generate technical signal
        print("3. Generating technical signal...")
        tech_signal = strategy._generate_technical_signal(df, 'SBIN')
        
        if tech_signal:
            print(f"   ✅ Technical Signal:")
            print(f"      Action: {tech_signal['action']}")
            print(f"      Confidence: {tech_signal['confidence']:.2%}")
            print(f"      Conditions: {tech_signal['conditions_met']}")
        else:
            print(f"   ❌ No technical signal")
        
        # Generate AI signal
        print("\n4. Generating AI signal...")
        ai_signal = strategy._generate_ai_signal(df, 'SBIN')
        
        if ai_signal:
            print(f"   ✅ AI Signal:")
            print(f"      Action: {ai_signal['action']}")
            print(f"      Confidence: {ai_signal['confidence']:.2%}")
        else:
            print(f"   ❌ No AI signal")
        
        # Combine signals
        print("\n5. Combining signals...")
        combined = strategy._combine_signals('SBIN', tech_signal, ai_signal)
        
        if combined:
            print(f"\n✅ Combined Signal:")
            print(f"   Action: {combined['action']}")
            print(f"   Source: {combined['signal_source']}")
            print(f"   Technical Confidence: {combined.get('technical_confidence', 0):.2%}")
            print(f"   AI Confidence: {combined.get('ai_confidence', 0):.2%}")
            print(f"   Combined Confidence: {combined['confidence']:.2%}")
        else:
            print(f"\n❌ Signals conflict - no combined signal")
        
        return combined
    
    except Exception as e:
        logger.error(f"Error in example 4: {e}")
        return None


def example_5_backtesting():
    """
    Example 5: Backtest AI Signals
    Tests AI signals on historical data
    """
    print("\n" + "="*60)
    print("EXAMPLE 5: Backtesting AI Signals")
    print("="*60)
    
    try:
        from ai_trading_engine import AISignalGenerator
        import numpy as np
        
        # Create historical data
        print("\n1. Creating historical data...")
        n_samples = 500
        close = np.cumsum(np.random.normal(0, 0.5, n_samples)) + 100
        
        df = pd.DataFrame({
            'open': close * (1 + np.random.normal(0, 0.001, n_samples)),
            'high': close * (1 + abs(np.random.normal(0, 0.01, n_samples))),
            'low': close * (1 - abs(np.random.normal(0, 0.01, n_samples))),
            'close': close,
            'volume': np.random.normal(1000000, 100000, n_samples)
        })
        
        print(f"   Created {len(df)} data points")
        
        # Initialize AI
        print("\n2. Setting up AI model...")
        ai = AISignalGenerator(df)
        ai.setup()
        
        # Backtest
        print("\n3. Running backtest...")
        results = ai.backtest_signals(df)
        
        # Display results
        print(f"\n✅ Backtest Results:")
        if results:
            for key, value in results.items():
                if isinstance(value, float):
                    print(f"   {key}: {value:.2%}")
                else:
                    print(f"   {key}: {value}")
        else:
            print("   No backtest results available")
        
        return results
    
    except Exception as e:
        logger.error(f"Error in example 5: {e}")
        return None


def example_6_production_deployment():
    """
    Example 6: Production Deployment
    Shows how to use AI in production with state management
    """
    print("\n" + "="*60)
    print("EXAMPLE 6: Production Deployment")
    print("="*60)
    
    try:
        from ai_deployment_production import ProductionAITrader
        import numpy as np
        
        # Create sample data
        print("\n1. Creating market data...")
        n = 500
        close = np.cumsum(np.random.normal(0, 0.5, n)) + 100
        df = pd.DataFrame({
            'open': close * (1 + np.random.normal(0, 0.001, n)),
            'high': close * (1 + abs(np.random.normal(0, 0.01, n))),
            'low': close * (1 - abs(np.random.normal(0, 0.01, n))),
            'close': close,
            'volume': np.random.normal(1000000, 100000, n)
        })
        
        # Initialize production trader
        print("\n2. Initializing Production AI Trader...")
        trader = ProductionAITrader(df)
        trader.initialize()
        print("   ✅ Production trader initialized")
        
        # Configure
        print("\n3. Configuring trader...")
        config = {
            'confidence_threshold': 0.60,
            'position_size_pct': 2.0,
            'stop_loss_pct': 1.0,
            'take_profit_pct': 2.0
        }
        trader.update_config(config)
        print(f"   ✅ Configuration updated: {config}")
        
        # Generate signal
        print("\n4. Generating production signal...")
        signal = trader.generate_signal()
        
        if signal:
            print(f"\n✅ Production Signal:")
            print(f"   Signal: {signal.get('signal')}")
            print(f"   Confidence: {signal.get('confidence', 0):.2%}")
            print(f"   Valid: {signal.get('valid')}")
            
            # Get recommendation
            print(f"\n5. Getting recommendation...")
            recommendation = signal.get('recommendation', {})
            print(f"   Action: {recommendation.get('action')}")
            print(f"   Position Size: {recommendation.get('position_size_pct')}%")
            print(f"   Stop Loss: {recommendation.get('stop_loss_pct')}%")
            print(f"   Take Profit: {recommendation.get('take_profit_pct')}%")
        else:
            print("   ❌ No signal generated")
        
        # Get performance report
        print("\n6. Getting performance report...")
        report = trader.get_performance_report()
        print(f"\n📊 Performance Report:")
        for key, value in report.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.2%}")
            else:
                print(f"   {key}: {value}")
        
        return signal
    
    except Exception as e:
        logger.error(f"Error in example 6: {e}")
        return None


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("AI INTEGRATION WITH TRADING SYSTEM - EXAMPLES")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    examples = [
        ("Simple Signal Generation", example_1_simple_ai_signal_generation),
        ("AI Strategy Integration", example_2_ai_strategy_integration),
        ("AI Signal Bridge", example_3_ai_signal_bridge),
        ("Signal Combination", example_4_signal_combination),
        ("Backtesting", example_5_backtesting),
        ("Production Deployment", example_6_production_deployment),
    ]
    
    results = {}
    for name, func in examples:
        try:
            print(f"\n📍 Running: {name}")
            result = func()
            results[name] = "✅ Success" if result else "⚠️ No result"
        except Exception as e:
            logger.error(f"Example failed: {e}")
            results[name] = f"❌ Error: {e}"
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, status in results.items():
        print(f"{name}: {status}")
    
    print(f"\n✅ All examples completed!")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
