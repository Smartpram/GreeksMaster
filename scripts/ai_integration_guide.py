"""
AI Integration Guide & Quick Start
===================================

Complete guide for integrating AI into your trading system

Components:
1. ai_trading_engine.py - Core ML and signal generation
2. ai_deployment_production.py - Production deployment
3. This file - Integration examples

Author: GitHub Copilot
Date: May 28, 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

# Import AI components
from ai_trading_engine import (
    FeatureEngineer,
    SignalPredictionModel,
    AnomalyDetector,
    RiskAssessment,
    AISignalGenerator
)

from ai_deployment_production import (
    ProductionAITrader,
    RealTimeSignalMonitor,
    SignalHistory
)


# ============================================================================
# EXAMPLE 1: BASIC SIGNAL GENERATION
# ============================================================================

def example_basic_signal_generation():
    """
    Example 1: Generate AI signals for your data
    
    Use this to:
    - Get AI predictions
    - Check confidence scores
    - See model votes
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 1: BASIC SIGNAL GENERATION")
    print("="*80 + "\n")
    
    # 1. Load or create data
    print("[1] Loading data...")
    # Replace with your actual data
    data = create_sample_data(1000)
    print(f"    Loaded {len(data)} candles")
    
    # 2. Create AI signal generator
    print("[2] Creating AI Signal Generator...")
    ai = AISignalGenerator(data)
    
    # 3. Initialize and train
    print("[3] Training AI models...")
    setup_result = ai.setup()
    
    # 4. Generate signal
    print("[4] Generating signal for latest candle...")
    signal = ai.generate_signal(confidence_threshold=0.65)
    
    # 5. Display results
    print("\n📊 SIGNAL RESULT:")
    print(f"   Signal: {signal.get('signal')}")
    print(f"   Confidence: {signal.get('confidence'):.2%}")
    print(f"   Signal Strength: {signal.get('signal_strength'):.2%}")
    print(f"   Models Agree: {signal.get('models_agree_pct', 0):.0%}")
    print(f"   Is Anomaly: {signal.get('is_anomaly')}")
    print(f"   Valid: {signal.get('valid')}")
    
    if signal.get('model_votes'):
        print("\n🗳️  Model Votes:")
        for model, vote in signal['model_votes'].items():
            print(f"    {model}: {vote['prediction']} ({vote['confidence']:.2%})")
    
    return signal


# ============================================================================
# EXAMPLE 2: FEATURE ENGINEERING
# ============================================================================

def example_feature_engineering():
    """
    Example 2: Explore engineered features
    
    Use this to:
    - Understand what features are created
    - See feature statistics
    - Debug feature engineering
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 2: FEATURE ENGINEERING")
    print("="*80 + "\n")
    
    # Load data
    print("[1] Loading data...")
    data = create_sample_data(500)
    
    # Create feature engineer
    print("[2] Creating feature engineer...")
    fe = FeatureEngineer(data)
    
    # Engineer features
    print("[3] Engineering features...")
    features_df = fe.engineer_all_features()
    
    # Display results
    print(f"\n✅ Features created:")
    print(f"   Total features: {len(features_df.columns)}")
    print(f"   Samples: {len(features_df)}")
    
    print("\n📋 Feature Categories:")
    feature_list = fe.get_feature_list()
    print(f"   Momentum: {len([f for f in feature_list if 'rsi' in f or 'macd' in f or 'stochastic' in f])}")
    print(f"   Trend: {len([f for f in feature_list if 'sma' in f or 'ema' in f or 'trend' in f])}")
    print(f"   Volatility: {len([f for f in feature_list if 'atr' in f or 'bb' in f or 'kc' in f])}")
    print(f"   Volume: {len([f for f in feature_list if 'volume' in f or 'obv' in f])}")
    print(f"   Price Action: {len([f for f in feature_list if 'body' in f or 'wick' in f or 'candle' in f])}")
    print(f"   Statistical: {len([f for f in feature_list if 'skew' in f or 'kurt' in f])}")
    
    print("\n🔢 Sample Feature Values (Latest Candle):")
    print(features_df.iloc[-1].head(10).to_string())
    
    return features_df


# ============================================================================
# EXAMPLE 3: MODEL TRAINING & EVALUATION
# ============================================================================

def example_model_training():
    """
    Example 3: Train and evaluate ML models
    
    Use this to:
    - Train different ML models
    - Compare model performance
    - See feature importance
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 3: MODEL TRAINING & EVALUATION")
    print("="*80 + "\n")
    
    # Load data
    print("[1] Loading data and engineering features...")
    data = create_sample_data(500)
    fe = FeatureEngineer(data)
    features_df = fe.engineer_all_features()
    
    # Create target (next candle up/down)
    print("[2] Creating target variable...")
    returns = np.diff(features_df['close'].values) / features_df['close'].values[:-1]
    features_df['target'] = pd.Series((returns > 0).astype(int), index=features_df.index[1:])
    features_df = features_df.dropna()
    
    # Train models
    print("[3] Training multiple models...\n")
    model = SignalPredictionModel(features_df)
    results = model.train_models(test_size=0.2)
    
    # Display results
    print("\n📊 MODEL PERFORMANCE:")
    for model_name, metrics in results.items():
        print(f"\n   {model_name}:")
        print(f"      Accuracy: {metrics['accuracy']:.2%}")
        print(f"      AUC: {metrics['auc']:.3f}")
    
    # Feature importance
    print("\n🔝 TOP 10 IMPORTANT FEATURES (Random Forest):")
    if 'RandomForest' in results and results['RandomForest']['feature_importance']:
        top_features = sorted(
            results['RandomForest']['feature_importance'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        for i, (feat, imp) in enumerate(top_features, 1):
            print(f"   {i}. {feat}: {imp:.2%}")
    
    return model, results


# ============================================================================
# EXAMPLE 4: PRODUCTION DEPLOYMENT
# ============================================================================

def example_production_deployment():
    """
    Example 4: Deploy AI trader to production
    
    Use this to:
    - Initialize production trader
    - Generate signals with full validation
    - Get recommendations
    - Track performance
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 4: PRODUCTION DEPLOYMENT")
    print("="*80 + "\n")
    
    # Load data
    print("[1] Loading data...")
    data = create_sample_data(500)
    
    # Configure
    print("[2] Configuring trader...")
    config = {
        'confidence_threshold': 0.65,
        'require_high_confidence': True,
        'allow_anomalies': False,
        'min_signal_strength': 0.4,
        'position_size_pct': 5.0,
        'stop_loss_pct': 2.0,
        'take_profit_pct': 5.0,
    }
    
    # Initialize trader
    print("[3] Initializing AI trader...")
    trader = ProductionAITrader(data, config)
    init_result = trader.initialize()
    
    # Generate signal
    print("\n[4] Generating trading signal...\n")
    signal = trader.generate_signal()
    
    # Display signal
    print("✅ TRADING SIGNAL:")
    print(f"   Direction: {signal.get('signal')}")
    print(f"   Confidence: {signal.get('confidence'):.2%}")
    print(f"   Valid: {signal.get('valid')}")
    
    # Display recommendation
    if signal.get('valid'):
        rec = signal.get('recommendation', {})
        print(f"\n💡 RECOMMENDATION:")
        print(f"   Action: {rec.get('action')}")
        print(f"   Position Size: {rec.get('position_size', 0):.0f} shares")
        print(f"   Stop Loss: {rec.get('stop_loss_pct', 0):.2f}%")
        print(f"   Take Profit: {rec.get('take_profit_pct', 0):.2f}%")
        print(f"   Expected PnL: {rec.get('expected_pnl_pct', 0):.2f}%")
    else:
        print(f"\n❌ REASON: {signal.get('reason')}")
    
    # Market analysis
    print(f"\n📈 MARKET ANALYSIS:")
    analysis = trader.get_market_analysis()
    print(f"   Trend: {analysis.get('trend')}")
    print(f"   Volatility: {analysis.get('volatility_pct', 0):.2f}%")
    print(f"   Volume Confirmation: {analysis.get('volume_confirmation')}")
    print(f"   Price to SMA50: {analysis.get('price_to_sma50', 0):.2f}%")
    
    return trader, signal


# ============================================================================
# EXAMPLE 5: ANOMALY DETECTION
# ============================================================================

def example_anomaly_detection():
    """
    Example 5: Detect market anomalies
    
    Use this to:
    - Find unusual price movements
    - Identify volume spikes
    - Detect volatility spikes
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 5: ANOMALY DETECTION")
    print("="*80 + "\n")
    
    # Load data
    print("[1] Loading data...")
    data = create_sample_data(500)
    
    # Create detector
    print("[2] Creating anomaly detector...")
    detector = AnomalyDetector(data)
    
    # Detect anomalies
    print("[3] Detecting anomalies...\n")
    
    price_anomalies = detector.detect_price_anomalies()
    volume_anomalies = detector.detect_volume_anomalies()
    vol_spikes = detector.detect_volatility_spike()
    
    print("🚨 ANOMALIES DETECTED:")
    print(f"   Price anomalies: {len(price_anomalies)}")
    print(f"   Volume anomalies: {len(volume_anomalies)}")
    print(f"   Volatility spikes: {len(vol_spikes)}")
    
    # Get scores for latest candles
    print("\n📊 LATEST CANDLES ANOMALY SCORES:")
    for idx in range(len(data)-5, len(data)):
        score = detector.get_anomaly_score(idx)
        is_anom = "⚠️ " if score['is_anomaly'] else "✓"
        print(f"   Bar {idx}: {is_anom} Score: {score['anomaly_score']:.2f} - {score['reasons']}")
    
    return detector


# ============================================================================
# EXAMPLE 6: RISK MANAGEMENT
# ============================================================================

def example_risk_management():
    """
    Example 6: Risk assessment and position sizing
    
    Use this to:
    - Calculate signal strength
    - Assess volatility risk
    - Get position size recommendations
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 6: RISK MANAGEMENT")
    print("="*80 + "\n")
    
    # Load data
    print("[1] Loading data...")
    data = create_sample_data(500)
    
    # Create risk assessor
    print("[2] Creating risk assessment module...")
    risk = RiskAssessment(data)
    
    # Analyze latest candle
    latest_idx = len(data) - 1
    
    print(f"\n[3] Analyzing latest candle (#{latest_idx})...\n")
    
    signal_strength = risk.calculate_signal_strength(latest_idx)
    volatility_risk = risk.calculate_volatility_risk()
    pos_sizing = risk.recommend_position_size(
        stop_loss_pct=2.0,
        max_risk_pct=1.0,
        account_size=100000
    )
    
    print("📊 RISK METRICS:")
    print(f"   Signal Strength: {signal_strength:.2%}")
    print(f"   Volatility Risk: {volatility_risk:.2f}%")
    
    print(f"\n💰 POSITION SIZING (for $100k account):")
    print(f"   Position Size: {pos_sizing['position_size']:.0f} shares")
    print(f"   Max Loss: ${pos_sizing['max_loss']:.2f}")
    print(f"   Stop Loss: {pos_sizing['stop_loss_pct']:.2f}%")
    print(f"   Risk per Trade: {pos_sizing['risk_per_trade_pct']:.2f}%")
    
    return risk


# ============================================================================
# EXAMPLE 7: BACKTESTING
# ============================================================================

def example_backtesting():
    """
    Example 7: Backtest AI signals
    
    Use this to:
    - Test signals on historical data
    - Calculate accuracy
    - Validate strategy
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 7: BACKTESTING AI SIGNALS")
    print("="*80 + "\n")
    
    # Load data
    print("[1] Loading historical data...")
    data = create_sample_data(1000)
    
    # Create AI generator
    print("[2] Creating AI Signal Generator...")
    ai = AISignalGenerator(data)
    
    # Train
    print("[3] Training models...")
    ai.setup()
    
    # Backtest
    print("[4] Backtesting signals...\n")
    backtest_results = ai.backtest_signals()
    
    print("✅ BACKTEST RESULTS:")
    print(f"   Total signals: {backtest_results.get('total_signals', 0)}")
    print(f"   Overall accuracy: {backtest_results.get('accuracy', 0):.2%}")
    print(f"   High confidence signals: {backtest_results.get('high_confidence_signals', 0)}")
    print(f"   High confidence accuracy: {backtest_results.get('high_confidence_accuracy', 0):.2%}")
    
    return backtest_results


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_sample_data(n_candles: int = 500) -> pd.DataFrame:
    """Create sample OHLCV data for testing"""
    
    dates = pd.date_range('2023-01-01', periods=n_candles, freq='D')
    prices = 100 + np.cumsum(np.random.randn(n_candles) * 2)
    
    data = pd.DataFrame({
        'open': prices + np.random.randn(n_candles),
        'high': prices + abs(np.random.randn(n_candles)) + 0.5,
        'low': prices - abs(np.random.randn(n_candles)) - 0.5,
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, n_candles)
    }, index=dates)
    
    return data


# ============================================================================
# MAIN MENU
# ============================================================================

def main_menu():
    """Interactive menu"""
    
    examples = {
        '1': ('Basic Signal Generation', example_basic_signal_generation),
        '2': ('Feature Engineering', example_feature_engineering),
        '3': ('Model Training', example_model_training),
        '4': ('Production Deployment', example_production_deployment),
        '5': ('Anomaly Detection', example_anomaly_detection),
        '6': ('Risk Management', example_risk_management),
        '7': ('Backtesting', example_backtesting),
    }
    
    print("\n" + "="*80)
    print("🤖 AI TRADING ENGINE - EXAMPLES & INTEGRATION GUIDE")
    print("="*80 + "\n")
    
    print("Select an example to run:\n")
    for key, (desc, _) in examples.items():
        print(f"   {key}. {desc}")
    print("   0. Run all examples")
    print("   Q. Quit\n")
    
    choice = input("Enter choice: ").strip().upper()
    
    if choice == 'Q':
        print("\nGoodbye!\n")
        return
    
    if choice == '0':
        for key, (_, func) in examples.items():
            try:
                func()
            except Exception as e:
                print(f"\n❌ Error in example: {e}\n")
    else:
        if choice in examples:
            try:
                examples[choice][1]()
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
        else:
            print("\n❌ Invalid choice\n")


# ============================================================================
# QUICK START
# ============================================================================

def quick_start():
    """Quick start - just get a signal"""
    
    print("\n🚀 QUICK START - AI SIGNAL IN 30 SECONDS\n")
    
    # Create data
    data = create_sample_data(500)
    
    # Initialize
    ai = AISignalGenerator(data)
    ai.setup()
    
    # Get signal
    signal = ai.generate_signal()
    
    # Display
    print(f"✅ Signal: {signal['signal']}")
    print(f"   Confidence: {signal['confidence']:.2%}")
    print(f"   Valid: {signal['valid']}\n")


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'quick':
            quick_start()
        elif sys.argv[1] == 'menu':
            main_menu()
        else:
            print("Usage: python ai_integration_guide.py [quick|menu]")
    else:
        # Default: show menu
        main_menu()
