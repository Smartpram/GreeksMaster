"""
AI Signal Bridge Service
Connects AI modules to existing trading services and orchestrates integration
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
from threading import Lock

logger = logging.getLogger(__name__)


class AISignalBridge:
    """
    Bridge between AI trading engine and existing trading system
    
    Responsibilities:
    1. Data transformation (API format → AI format)
    2. Signal generation orchestration
    3. Signal validation and enhancement
    4. Performance tracking
    5. Error handling and fallback
    """
    
    def __init__(self, breeze_service=None, data_stream_service=None):
        """
        Initialize AI Signal Bridge
        
        Args:
            breeze_service: Breeze API service for market data
            data_stream_service: Data streaming service
        """
        self.breeze_service = breeze_service
        self.data_stream_service = data_stream_service
        self.lock = Lock()
        
        # AI components (lazy loaded)
        self.ai_generator = None
        self.ai_trader = None
        self.ai_initialized = False
        
        # Cache for performance
        self.data_cache = {}
        self.signal_cache = {}
        self.performance_metrics = {
            'total_signals': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'accuracy': 0.0,
            'avg_confidence': 0.0,
            'signals_by_source': {}
        }
        
        logger.info("AI Signal Bridge initialized")
    
    def initialize_ai(self, initial_data: Optional[Dict] = None) -> bool:
        """
        Initialize AI models
        
        Args:
            initial_data: Optional initial market data for training
            
        Returns:
            True if initialization successful
        """
        try:
            from ai_trading_engine import AISignalGenerator
            from ai_deployment_production import ProductionAITrader
            
            logger.info("Initializing AI components...")
            
            if initial_data and len(initial_data) > 0:
                # Use provided data
                first_key = list(initial_data.keys())[0]
                data = initial_data[first_key]
                
                if isinstance(data, list) and len(data) > 100:
                    df = pd.DataFrame(data)
                    if all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume']):
                        self.ai_generator = AISignalGenerator(df)
                        self.ai_generator.setup()
                        self.ai_initialized = True
                        logger.info("AI Generator initialized with market data")
            
            # Initialize production trader
            self.ai_trader = ProductionAITrader()
            logger.info("AI Trader initialized")
            
            self.ai_initialized = True
            return True
        
        except ImportError as e:
            logger.warning(f"AI modules not available: {e}")
            self.ai_initialized = False
            return False
        except Exception as e:
            logger.error(f"Failed to initialize AI: {e}")
            self.ai_initialized = False
            return False
    
    def fetch_market_data(self, stock_code: str, timeframe: str = 'daily', 
                         lookback: int = 200) -> Optional[pd.DataFrame]:
        """
        Fetch market data from Breeze API
        
        Args:
            stock_code: Stock code (e.g., 'SBIN')
            timeframe: Timeframe ('intraday', 'daily', 'weekly', 'monthly')
            lookback: Number of candles to fetch
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        try:
            if not self.breeze_service:
                logger.warning("Breeze service not available")
                return None
            
            # Fetch historical data
            data = self.breeze_service.get_historical_data(
                stock_code=stock_code,
                exchange_code='NSE',
                time_period=timeframe,
                count=lookback
            )
            
            if not data or len(data) == 0:
                logger.warning(f"No data fetched for {stock_code}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Normalize column names
            df.columns = [col.lower() for col in df.columns]
            
            # Ensure OHLCV columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Missing OHLCV columns for {stock_code}")
                return None
            
            # Ensure numeric types
            for col in required_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Cache the data
            self.data_cache[stock_code] = df
            
            logger.info(f"Fetched {len(df)} candles for {stock_code}")
            return df
        
        except Exception as e:
            logger.error(f"Error fetching market data for {stock_code}: {e}")
            return None
    
    def generate_ai_signal(self, stock_code: str, data: Optional[pd.DataFrame] = None,
                          confidence_threshold: float = 0.55) -> Optional[Dict]:
        """
        Generate AI signal for a stock
        
        Args:
            stock_code: Stock code
            data: Optional OHLCV DataFrame (fetches from cache or API if not provided)
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            Signal dictionary or None
        """
        try:
            if not self.ai_initialized or self.ai_generator is None:
                logger.warning("AI not initialized")
                return None
            
            # Get data if not provided
            if data is None:
                data = self.data_cache.get(stock_code)
                if data is None:
                    data = self.fetch_market_data(stock_code)
            
            if data is None or len(data) < 100:
                logger.warning(f"Insufficient data for {stock_code}")
                return None
            
            # Generate AI signal
            ai_signal = self.ai_generator.generate_signal()
            
            if ai_signal is None:
                return None
            
            # Filter by confidence
            if ai_signal.get('confidence', 0) < confidence_threshold:
                logger.debug(f"{stock_code}: AI confidence below threshold "
                           f"({ai_signal.get('confidence', 0):.2%} < {confidence_threshold:.2%})")
                return None
            
            # Enhance signal with stock-specific data
            current_price = data['close'].iloc[-1]
            signal = {
                'stock_code': stock_code,
                'timestamp': datetime.now(),
                'signal': ai_signal.get('signal'),  # UP or DOWN
                'confidence': ai_signal.get('confidence', 0),
                'signal_strength': ai_signal.get('signal_strength', 0),
                'validity': ai_signal.get('valid', True),
                'entry_price': current_price,
                'stop_loss_pct': 1.0,  # 1% stop loss
                'target_pct': 2.0,  # 2% target
                'ai_models': ai_signal.get('ai_models', {}),
                'recommendations': ai_signal.get('recommendations', {})
            }
            
            # Cache signal
            self.signal_cache[stock_code] = signal
            
            # Update metrics
            self._update_metrics(signal)
            
            logger.info(f"{stock_code}: AI Signal {signal['signal']} "
                       f"(Confidence: {signal['confidence']:.2%})")
            
            return signal
        
        except Exception as e:
            logger.error(f"Error generating AI signal for {stock_code}: {e}")
            return None
    
    def validate_signal(self, signal: Dict, technical_data: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Validate AI signal with multiple checks
        
        Args:
            signal: Signal dictionary from generate_ai_signal()
            technical_data: Optional technical indicator data for validation
            
        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            if not signal:
                return False, "No signal provided"
            
            # Check confidence
            confidence = signal.get('confidence', 0)
            if confidence < 0.55:
                return False, f"Confidence too low: {confidence:.2%}"
            
            # Check validity flag
            if not signal.get('validity', True):
                return False, "Signal marked invalid"
            
            # Check for anomalies in signal
            signal_strength = signal.get('signal_strength', 0)
            if signal_strength < 0.3:
                return False, f"Signal strength too weak: {signal_strength:.2%}"
            
            # Optional technical validation
            if technical_data:
                if not self._validate_with_technical(signal, technical_data):
                    return False, "Technical indicators do not confirm signal"
            
            return True, "Signal validated"
        
        except Exception as e:
            logger.error(f"Error validating signal: {e}")
            return False, f"Validation error: {e}"
    
    def _validate_with_technical(self, signal: Dict, technical_data: Dict) -> bool:
        """
        Validate AI signal against technical indicators
        
        Args:
            signal: AI signal dictionary
            technical_data: Technical indicator values
            
        Returns:
            True if signal aligns with technical analysis
        """
        try:
            ai_direction = signal.get('signal')  # UP or DOWN
            
            # Check trend agreement
            trend = technical_data.get('trend')
            if trend and trend.lower() != ai_direction.lower():
                logger.debug(f"Trend mismatch: AI={ai_direction}, Technical={trend}")
                return False
            
            # Check RSI range
            rsi = technical_data.get('rsi')
            if rsi:
                if ai_direction == 'UP' and rsi > 70:
                    logger.debug(f"RSI too high for BUY: {rsi}")
                    return False
                if ai_direction == 'DOWN' and rsi < 30:
                    logger.debug(f"RSI too low for SELL: {rsi}")
                    return False
            
            return True
        
        except Exception as e:
            logger.warning(f"Technical validation error: {e}")
            return True  # Allow signal if validation fails
    
    def generate_signals_for_watchlist(self, watchlist: List[str], 
                                      confidence_threshold: float = 0.55) -> Dict[str, Dict]:
        """
        Generate AI signals for a watchlist of stocks
        
        Args:
            watchlist: List of stock codes
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            Dictionary of signals for each stock
        """
        signals = {}
        
        try:
            for stock_code in watchlist:
                signal = self.generate_ai_signal(
                    stock_code, 
                    confidence_threshold=confidence_threshold
                )
                
                if signal:
                    is_valid, reason = self.validate_signal(signal)
                    if is_valid:
                        signals[stock_code] = signal
                    else:
                        logger.debug(f"{stock_code}: Signal validation failed - {reason}")
        
        except Exception as e:
            logger.error(f"Error generating watchlist signals: {e}")
        
        return signals
    
    def backtest_ai_signals(self, stock_code: str, lookback: int = 500,
                           confidence_threshold: float = 0.55) -> Optional[Dict]:
        """
        Backtest AI signals on historical data
        
        Args:
            stock_code: Stock code
            lookback: Number of candles to backtest
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            Backtest results dictionary or None
        """
        try:
            if not self.ai_initialized or self.ai_generator is None:
                logger.warning("AI not initialized")
                return None
            
            # Fetch data
            data = self.fetch_market_data(stock_code, lookback=lookback)
            if data is None or len(data) < 100:
                return None
            
            # Run backtest
            results = self.ai_generator.backtest_signals(data)
            
            logger.info(f"{stock_code} Backtest: {results}")
            return results
        
        except Exception as e:
            logger.error(f"Error backtesting AI signals for {stock_code}: {e}")
            return None
    
    def get_performance_report(self) -> Dict:
        """
        Get AI performance metrics report
        
        Returns:
            Performance metrics dictionary
        """
        return {
            'total_signals': self.performance_metrics['total_signals'],
            'successful_trades': self.performance_metrics['successful_trades'],
            'failed_trades': self.performance_metrics['failed_trades'],
            'accuracy': self.performance_metrics['accuracy'],
            'avg_confidence': self.performance_metrics['avg_confidence'],
            'signals_by_source': self.performance_metrics['signals_by_source'],
            'ai_initialized': self.ai_initialized
        }
    
    def _update_metrics(self, signal: Dict):
        """Update performance metrics"""
        self.performance_metrics['total_signals'] += 1
        confidence = signal.get('confidence', 0)
        
        # Update average confidence
        current_avg = self.performance_metrics['avg_confidence']
        total = self.performance_metrics['total_signals']
        self.performance_metrics['avg_confidence'] = (
            (current_avg * (total - 1) + confidence) / total
        )
        
        # Update signals by source
        source = signal.get('signal', 'unknown')
        self.performance_metrics['signals_by_source'][source] = (
            self.performance_metrics['signals_by_source'].get(source, 0) + 1
        )
    
    def save_signal_cache(self, filepath: str) -> bool:
        """
        Save signal cache to file for analysis
        
        Args:
            filepath: Path to save JSON file
            
        Returns:
            True if successful
        """
        try:
            # Convert datetime to string for JSON serialization
            data = {}
            for key, signal in self.signal_cache.items():
                signal_copy = signal.copy()
                if 'timestamp' in signal_copy:
                    signal_copy['timestamp'] = signal_copy['timestamp'].isoformat()
                data[key] = signal_copy
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Signal cache saved to {filepath}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving signal cache: {e}")
            return False
    
    def load_state(self, filepath: str) -> bool:
        """
        Load AI state from file
        
        Args:
            filepath: Path to state file
            
        Returns:
            True if successful
        """
        try:
            if self.ai_generator and hasattr(self.ai_generator, 'load_state'):
                self.ai_generator.load_state(filepath)
                logger.info(f"AI state loaded from {filepath}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading AI state: {e}")
            return False
    
    def save_state(self, filepath: str) -> bool:
        """
        Save AI state to file
        
        Args:
            filepath: Path to save state
            
        Returns:
            True if successful
        """
        try:
            if self.ai_generator and hasattr(self.ai_generator, 'save_state'):
                self.ai_generator.save_state(filepath)
                logger.info(f"AI state saved to {filepath}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving AI state: {e}")
            return False
