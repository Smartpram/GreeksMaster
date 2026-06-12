"""
AI Trading Engine - Production Deployment
==========================================

Deployment module for live trading with AI signals

Features:
- Real-time signal generation
- Confidence-based trade filtering
- Multi-model ensemble voting
- Signal caching and performance tracking
- Logging and monitoring
- Integration with trading platform

Author: GitHub Copilot
Date: May 28, 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Optional, Tuple
import time
from pathlib import Path

from ai_trading_engine import (
    AISignalGenerator, 
    FeatureEngineer,
    AnomalyDetector,
    RiskAssessment
)


# ============================================================================
# PART 1: SIGNAL CACHE & HISTORY
# ============================================================================

class SignalHistory:
    """Track signal history for performance analysis"""
    
    def __init__(self, max_records: int = 1000):
        self.signals = []
        self.max_records = max_records
        self.logger = logging.getLogger("SignalHistory")
        
    def add_signal(self, signal: Dict, entry_price: float = None, exit_price: float = None):
        """Add signal to history"""
        
        record = {
            'timestamp': datetime.now(),
            'signal': signal.get('signal'),
            'confidence': signal.get('confidence'),
            'valid': signal.get('valid'),
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': (exit_price - entry_price) if (entry_price and exit_price) else None
        }
        
        self.signals.append(record)
        
        # Keep only last N signals
        if len(self.signals) > self.max_records:
            self.signals = self.signals[-self.max_records:]
        
        return record
    
    def get_statistics(self) -> Dict:
        """Get performance statistics"""
        
        if not self.signals:
            return {'total': 0}
        
        df = pd.DataFrame(self.signals)
        
        # Basic stats
        stats = {
            'total_signals': len(df),
            'valid_signals': df['valid'].sum(),
            'signal_validity_rate': df['valid'].mean(),
            'avg_confidence': df['confidence'].mean(),
        }
        
        # PnL stats
        pnl_data = df[df['pnl'].notna()]
        if len(pnl_data) > 0:
            stats['total_trades'] = len(pnl_data)
            stats['total_pnl'] = pnl_data['pnl'].sum()
            stats['avg_pnl'] = pnl_data['pnl'].mean()
            stats['win_rate'] = (pnl_data['pnl'] > 0).mean()
            stats['max_win'] = pnl_data['pnl'].max()
            stats['max_loss'] = pnl_data['pnl'].min()
        
        return stats
    
    def save_to_file(self, filepath: str):
        """Save signal history"""
        
        df = pd.DataFrame(self.signals)
        df.to_csv(filepath, index=False)
        self.logger.info(f"Signal history saved to {filepath}")
    
    def load_from_file(self, filepath: str):
        """Load signal history"""
        
        df = pd.read_csv(filepath)
        self.signals = df.to_dict('records')
        self.logger.info(f"Signal history loaded from {filepath}")


# ============================================================================
# PART 2: PRODUCTION AI TRADER
# ============================================================================

class ProductionAITrader:
    """
    Production deployment of AI trading system
    
    Responsibilities:
    - Generate AI signals in real-time
    - Filter signals by confidence threshold
    - Check for anomalies
    - Assess risk
    - Execute trades (or generate orders)
    - Track performance
    """
    
    def __init__(self, 
                 data: pd.DataFrame,
                 config: Dict = None):
        
        self.data = data.copy()
        self.config = config or self._default_config()
        self.logger = self._setup_logger()
        
        # Components
        self.ai_generator = None
        self.signal_history = SignalHistory()
        self.anomaly_detector = AnomalyDetector(data)
        self.risk_assessment = RiskAssessment(data)
        
        # State
        self.is_trained = False
        self.last_signal = None
        self.signal_cache = {}
        
    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            'confidence_threshold': 0.65,
            'require_high_confidence': True,
            'allow_anomalies': False,
            'max_anomaly_score': 0.5,
            'min_signal_strength': 0.4,
            'position_size_pct': 5,
            'stop_loss_pct': 2.0,
            'take_profit_pct': 5.0,
            'logging_enabled': True
        }
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("ProductionAITrader")
        if not logger.handlers:
            handler = logging.FileHandler('ai_trading_production.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def initialize(self) -> Dict:
        """Initialize and train AI models"""
        
        print("\n" + "="*80)
        print("🚀 INITIALIZING PRODUCTION AI TRADER")
        print("="*80)
        
        try:
            # Create AI generator
            print("\n[1/3] Creating AI Signal Generator...")
            self.ai_generator = AISignalGenerator(self.data)
            
            # Setup (trains models)
            print("[2/3] Training AI Models...")
            setup_result = self.ai_generator.setup()
            
            # Backtest
            print("[3/3] Backtesting AI Signals...")
            backtest_result = self.ai_generator.backtest_signals()
            
            self.is_trained = True
            
            print("\n✅ INITIALIZATION COMPLETE\n")
            print(f"   Features: {setup_result.get('features')}")
            print(f"   Training samples: {setup_result.get('samples')}")
            print(f"   Models trained: {setup_result.get('models_trained')}")
            print(f"   Backtest accuracy: {backtest_result.get('accuracy', 0):.2%}")
            print(f"   High confidence accuracy: {backtest_result.get('high_confidence_accuracy', 0):.2%}\n")
            
            return {
                'status': 'Initialized successfully',
                'setup': setup_result,
                'backtest': backtest_result
            }
        
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            print(f"\n❌ Initialization failed: {e}\n")
            return {'status': 'Error', 'error': str(e)}
    
    def generate_signal(self) -> Dict:
        """
        Generate AI signal for current market state
        
        Returns:
            Dict with signal, confidence, and validity
        """
        
        if not self.is_trained:
            return {'error': 'AI not trained. Run initialize() first.'}
        
        try:
            # Generate raw signal
            signal = self.ai_generator.generate_signal(
                self.config['confidence_threshold']
            )
            
            # Add analysis
            signal['config'] = self.config
            
            # Validate signal
            signal = self._validate_signal(signal)
            
            # Add recommendations
            signal['recommendation'] = self._get_recommendation(signal)
            
            # Cache and log
            self.last_signal = signal
            self.signal_history.add_signal(signal)
            
            self.logger.info(f"Signal generated: {signal['signal']} (conf: {signal['confidence']:.2%})")
            
            return signal
        
        except Exception as e:
            self.logger.error(f"Signal generation failed: {e}")
            return {'error': str(e)}
    
    def _validate_signal(self, signal: Dict) -> Dict:
        """Validate signal against all checks"""
        
        checks = []
        
        # 1. Confidence threshold
        if signal.get('confidence', 0) >= self.config['confidence_threshold']:
            checks.append(True)
        else:
            checks.append(False)
            signal['reason'] = f"Low confidence: {signal.get('confidence', 0):.2%} < {self.config['confidence_threshold']:.2%}"
        
        # 2. Signal strength
        if signal.get('signal_strength', 0) >= self.config['min_signal_strength']:
            checks.append(True)
        else:
            checks.append(False)
            signal['reason'] = f"Weak signal: {signal.get('signal_strength', 0):.2%}"
        
        # 3. Anomaly check
        if self.config['allow_anomalies']:
            checks.append(True)
        else:
            if not signal.get('is_anomaly', False):
                checks.append(True)
            else:
                checks.append(False)
                signal['reason'] = f"Anomaly detected: {signal.get('anomaly_reasons', [])}"
        
        # Final decision
        signal['all_checks_passed'] = all(checks)
        signal['valid'] = all(checks)
        
        return signal
    
    def _get_recommendation(self, signal: Dict) -> Dict:
        """Get trading recommendation"""
        
        if not signal['valid']:
            return {
                'action': 'SKIP',
                'reason': signal.get('reason', 'Signal not valid'),
                'position_size': 0
            }
        
        # Calculate position sizing
        pos_config = self.risk_assessment.recommend_position_size(
            stop_loss_pct=self.config['stop_loss_pct'],
            max_risk_pct=self.config['position_size_pct']
        )
        
        # Create recommendation
        rec = {
            'action': f"{'BUY' if signal['signal'] == 'UP' else 'SELL'}",
            'confidence': signal['confidence'],
            'signal_strength': signal['signal_strength'],
            'position_size': pos_config['position_size'],
            'stop_loss_pct': self.config['stop_loss_pct'],
            'take_profit_pct': self.config['take_profit_pct'],
            'expected_pnl_pct': (signal['confidence'] - 0.5) * 10  # Rough estimate
        }
        
        return rec
    
    def get_market_analysis(self) -> Dict:
        """Get comprehensive market analysis"""
        
        latest_idx = len(self.data) - 1
        
        # Volatility
        returns = self.data['close'].pct_change()
        current_vol = returns.iloc[-20:].std() * 100
        
        # Trend
        sma_50 = self.data['close'].rolling(50).mean().iloc[-1]
        sma_200 = self.data['close'].rolling(200).mean().iloc[-1]
        current_price = self.data['close'].iloc[-1]
        
        trend = "UPTREND" if sma_50 > sma_200 else "DOWNTREND"
        
        # Volume
        current_vol_trade = self.data['volume'].iloc[-1]
        avg_vol = self.data['volume'].iloc[-20:].mean()
        vol_ratio = current_vol_trade / avg_vol
        
        return {
            'current_price': current_price,
            'sma_50': sma_50,
            'sma_200': sma_200,
            'trend': trend,
            'volatility_pct': current_vol,
            'volume_ratio': vol_ratio,
            'volume_confirmation': "HIGH" if vol_ratio > 1.5 else "NORMAL" if vol_ratio > 0.8 else "LOW",
            'price_to_sma50': (current_price / sma_50 - 1) * 100
        }
    
    def get_performance_report(self) -> Dict:
        """Get trading performance report"""
        
        stats = self.signal_history.get_statistics()
        
        return {
            **stats,
            'last_signal': self.last_signal,
            'config': self.config
        }
    
    def update_config(self, new_config: Dict):
        """Update configuration"""
        
        self.config.update(new_config)
        self.logger.info(f"Config updated: {new_config}")
    
    def save_state(self, filepath: str):
        """Save trader state"""
        
        state = {
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'is_trained': self.is_trained,
            'last_signal': self.last_signal
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        self.logger.info(f"State saved to {filepath}")
    
    def load_state(self, filepath: str):
        """Load trader state"""
        
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        self.config = state['config']
        self.is_trained = state['is_trained']
        self.last_signal = state['last_signal']
        
        self.logger.info(f"State loaded from {filepath}")


# ============================================================================
# PART 3: REAL-TIME SIGNAL MONITOR
# ============================================================================

class RealTimeSignalMonitor:
    """
    Monitor signals in real-time (for live trading)
    
    Features:
    - Update data periodically
    - Generate signals
    - Execute trades (interface)
    - Track performance
    - Alert system
    """
    
    def __init__(self, trader: ProductionAITrader):
        self.trader = trader
        self.logger = logging.getLogger("RealTimeMonitor")
        self.is_running = False
        self.alerts = []
        
    def run_live(self, 
                 update_interval_seconds: int = 60,
                 data_fetcher: callable = None):
        """
        Run live signal generation
        
        Args:
            update_interval_seconds: How often to check for new data
            data_fetcher: Function to fetch latest data
        """
        
        self.is_running = True
        print(f"\n🟢 LIVE TRADING STARTED - Checking every {update_interval_seconds}s")
        print("   (Press Ctrl+C to stop)\n")
        
        signal_count = 0
        
        try:
            while self.is_running:
                # Fetch new data
                if data_fetcher:
                    new_data = data_fetcher()
                    if new_data is not None:
                        self.trader.data = new_data
                
                # Generate signal
                signal = self.trader.generate_signal()
                
                if signal.get('valid'):
                    signal_count += 1
                    self._handle_valid_signal(signal, signal_count)
                
                # Wait
                time.sleep(update_interval_seconds)
        
        except KeyboardInterrupt:
            print("\n\n🔴 LIVE TRADING STOPPED")
            self.is_running = False
    
    def _handle_valid_signal(self, signal: Dict, signal_num: int):
        """Handle a valid signal"""
        
        print(f"\n⚡ SIGNAL #{signal_num}")
        print(f"   Time: {signal.get('timestamp')}")
        print(f"   Direction: {signal.get('signal')}")
        print(f"   Confidence: {signal.get('confidence'):.2%}")
        print(f"   Strength: {signal.get('signal_strength'):.2%}")
        
        rec = signal.get('recommendation', {})
        print(f"   Action: {rec.get('action')}")
        print(f"   Position Size: {rec.get('position_size', 0):.0f} shares")
        print(f"   Stop Loss: {rec.get('stop_loss_pct', 0):.2f}%")
        print(f"   Take Profit: {rec.get('take_profit_pct', 0):.2f}%")
        
        self.logger.info(f"Valid signal generated: {signal}")
        
        # Send alert
        self._send_alert(signal)
    
    def _send_alert(self, signal: Dict):
        """Send alert (email, Telegram, etc.)"""
        
        alert = {
            'timestamp': datetime.now(),
            'signal': signal,
            'status': 'sent'
        }
        
        self.alerts.append(alert)
        
        # TODO: Implement actual alerting (email, Telegram, SMS, etc.)
        # For now, just log it
        self.logger.info(f"Alert sent: {signal}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Example usage"""
    
    print("\n" + "="*80)
    print("🤖 AI TRADING ENGINE - PRODUCTION DEPLOYMENT")
    print("="*80 + "\n")
    
    # Example with dummy data
    dates = pd.date_range('2023-01-01', periods=500, freq='D')
    prices = np.cumsum(np.random.randn(500) * 2) + 100
    
    data = pd.DataFrame({
        'open': prices - np.random.rand(500),
        'high': prices + np.random.rand(500),
        'low': prices - np.random.rand(500),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 500)
    }, index=dates)
    
    print("Sample Data:")
    print(f"  Period: {data.index[0].date()} to {data.index[-1].date()}")
    print(f"  Candles: {len(data)}")
    print(f"  Current Price: ${data['close'].iloc[-1]:.2f}\n")
    
    # Initialize trader
    config = {
        'confidence_threshold': 0.65,
        'allow_anomalies': False,
        'position_size_pct': 5.0,
        'stop_loss_pct': 2.0,
        'take_profit_pct': 5.0
    }
    
    trader = ProductionAITrader(data, config)
    init_result = trader.initialize()
    
    if init_result['status'] == 'Initialized successfully':
        # Generate signal
        print("\n" + "="*80)
        print("GENERATING SIGNAL FOR LATEST CANDLE")
        print("="*80 + "\n")
        
        signal = trader.generate_signal()
        
        print(f"Signal: {signal.get('signal')}")
        print(f"Confidence: {signal.get('confidence'):.2%}")
        print(f"Valid: {signal.get('valid')}")
        print(f"Recommendation: {signal.get('recommendation')}")
        
        # Market analysis
        print("\n" + "="*80)
        print("MARKET ANALYSIS")
        print("="*80 + "\n")
        
        analysis = trader.get_market_analysis()
        for k, v in analysis.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.2f}")
            else:
                print(f"  {k}: {v}")
        
        # Performance report
        print("\n" + "="*80)
        print("PERFORMANCE REPORT")
        print("="*80 + "\n")
        
        report = trader.get_performance_report()
        print(f"  Total signals: {report.get('total_signals', 0)}")
        print(f"  Valid signals: {report.get('valid_signals', 0)}")
        print(f"  Avg confidence: {report.get('avg_confidence', 0):.2%}")
    
    print("\n✅ Production deployment demo complete!\n")


if __name__ == "__main__":
    main()
