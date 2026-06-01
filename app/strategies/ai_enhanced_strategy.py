"""
AI-Enhanced Trading Strategy
Integrates Machine Learning models with existing trading framework
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from app.strategies.base_strategy import BaseStrategy
from app.utils.indicators import TechnicalIndicators
from app.config import Config

# Import AI modules
try:
    from ai_trading_engine import AISignalGenerator
    from ai_deployment_production import ProductionAITrader
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logging.warning("AI modules not available. Install ai_trading_engine and ai_deployment_production.")

logger = logging.getLogger(__name__)


class AIEnhancedStrategy(BaseStrategy):
    """
    AI-Enhanced Buy and Hold Trend-Following Strategy
    
    Combines traditional technical analysis with ML-powered signal prediction
    
    How it works:
    1. Collects OHLCV data for analysis
    2. Generates traditional technical signals
    3. Uses AI model to predict market direction with confidence score
    4. Validates signals using both technical and AI confidence
    5. Executes trades based on combined signal strength
    
    Entry Criteria:
    - Traditional: Price above moving average, RSI not overbought, volume confirmation
    - AI: Model predicts UP direction with confidence > threshold
    - Combined: Both traditional AND AI signals agree
    
    Exit Criteria:
    - Stop loss hit
    - Target achieved
    - AI confidence drops below threshold
    - Trend reversal confirmed
    """
    
    def __init__(self, order_manager, risk_manager, notification_service, 
                 enable_ai=True, ai_confidence_threshold=0.55):
        """
        Initialize AI-Enhanced Strategy
        
        Args:
            order_manager: Order execution service
            risk_manager: Risk management service
            notification_service: Notification service
            enable_ai: Whether to use AI predictions (default: True)
            ai_confidence_threshold: Minimum AI confidence to generate signal (default: 0.55)
        """
        super().__init__(order_manager, risk_manager, notification_service)
        
        self.enable_ai = enable_ai and AI_AVAILABLE
        self.ai_confidence_threshold = ai_confidence_threshold
        self.config = Config()
        self.indicators = TechnicalIndicators()
        self.watchlist = []
        
        # AI Components
        self.ai_generator = None
        self.ai_trader = None
        
        if self.enable_ai:
            self._initialize_ai_components()
        
        # Configuration
        self.trend_period = self.config.TREND_PERIOD or 20
        self.rsi_period = self.config.RSI_PERIOD or 14
        self.positions = {}
        self.signal_history = {}  # Track signals for analysis
        
        logger.info(f"AI-Enhanced Strategy initialized (AI enabled: {self.enable_ai})")
    
    def _initialize_ai_components(self):
        """Initialize AI model components"""
        try:
            if not AI_AVAILABLE:
                logger.warning("AI modules not available")
                self.enable_ai = False
                return
            
            logger.info("Initializing AI components...")
            
            # Will be initialized on first use with actual market data
            self.ai_initialized = False
            logger.info("AI components ready for initialization with market data")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI components: {e}")
            self.enable_ai = False
    
    def set_watchlist(self, instruments: List[str]):
        """Set the watchlist of instruments to trade"""
        self.watchlist = instruments
        logger.info(f"AI Enhanced Strategy watchlist updated: {instruments}")
    
    def _setup_ai_with_data(self, data_samples: pd.DataFrame):
        """
        Setup AI models with initial training data
        
        Args:
            data_samples: DataFrame with OHLCV data for training
        """
        if not self.enable_ai or self.ai_initialized:
            return
        
        try:
            logger.info("Setting up AI models with market data...")
            
            # Create AI generator
            self.ai_generator = AISignalGenerator(data_samples)
            self.ai_generator.setup()
            
            self.ai_initialized = True
            logger.info("AI models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup AI models: {e}")
            self.enable_ai = False
    
    def generate_signals(self, data: Dict) -> Dict:
        """
        Generate trading signals using combined technical + AI analysis
        
        Args:
            data: Dictionary containing OHLCV data for instruments
            
        Returns:
            Dictionary containing signals with confidence scores
        """
        signals = {}
        
        try:
            # Initialize AI if we have data
            if self.enable_ai and not self.ai_initialized and data:
                first_instrument = list(data.keys())[0]
                if isinstance(data[first_instrument], list) and len(data[first_instrument]) > 100:
                    df = pd.DataFrame(data[first_instrument])
                    if all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume']):
                        self._setup_ai_with_data(df)
            
            for instrument in self.watchlist:
                if instrument not in data:
                    continue
                
                instrument_data = data[instrument]
                
                # Ensure minimum data points
                min_periods = max(self.trend_period, self.rsi_period, 26, 100)
                if len(instrument_data) < min_periods:
                    logger.debug(f"Insufficient data for {instrument}: {len(instrument_data)} < {min_periods}")
                    continue
                
                # Convert to DataFrame
                df = pd.DataFrame(instrument_data)
                if df.empty:
                    continue
                
                # Normalize column names
                df.columns = [col.lower() for col in df.columns]
                required_cols = ['open', 'high', 'low', 'close', 'volume']
                if not all(col in df.columns for col in required_cols):
                    logger.warning(f"Missing OHLCV columns for {instrument}")
                    continue
                
                # Generate technical signal
                technical_signal = self._generate_technical_signal(df, instrument)
                
                # Generate AI signal
                ai_signal = None
                if self.enable_ai and self.ai_initialized:
                    ai_signal = self._generate_ai_signal(df, instrument)
                
                # Combine signals
                combined_signal = self._combine_signals(
                    instrument, technical_signal, ai_signal
                )
                
                if combined_signal:
                    signals[instrument] = combined_signal
                    
                    # Store in history
                    if instrument not in self.signal_history:
                        self.signal_history[instrument] = []
                    self.signal_history[instrument].append({
                        'timestamp': datetime.now(),
                        'signal': combined_signal,
                        'technical': technical_signal,
                        'ai': ai_signal
                    })
        
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
        
        return signals
    
    def _generate_technical_signal(self, df: pd.DataFrame, instrument: str) -> Optional[Dict]:
        """
        Generate traditional technical analysis signal
        
        Args:
            df: OHLCV DataFrame
            instrument: Stock/instrument code
            
        Returns:
            Signal dictionary or None
        """
        try:
            # Calculate technical indicators
            df['ma20'] = self.indicators.moving_average(df['close'], 20)
            df['ma50'] = self.indicators.moving_average(df['close'], 50)
            df['rsi'] = self.indicators.rsi(df['close'], self.rsi_period)
            df['volume_ma'] = self.indicators.moving_average(df['volume'], 20)
            
            # MACD
            macd_data = self.indicators.macd(df['close'])
            df['macd'] = macd_data['macd']
            df['macd_signal'] = macd_data['signal']
            df['macd_histogram'] = macd_data['histogram']
            
            # Get current values
            current_price = df['close'].iloc[-1]
            current_ma20 = df['ma20'].iloc[-1]
            current_ma50 = df['ma50'].iloc[-1]
            current_rsi = df['rsi'].iloc[-1]
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['volume_ma'].iloc[-1]
            current_macd = df['macd'].iloc[-1] if not pd.isna(df['macd'].iloc[-1]) else 0
            current_macd_signal = df['macd_signal'].iloc[-1] if not pd.isna(df['macd_signal'].iloc[-1]) else 0
            
            # Entry conditions
            uptrend = current_price > current_ma20 > current_ma50
            rsi_valid = 30 < current_rsi < 70  # Not extreme
            volume_valid = current_volume > avg_volume * 0.8
            macd_bullish = current_macd > current_macd_signal
            
            conditions_met = []
            if uptrend:
                conditions_met.append("uptrend")
            if rsi_valid:
                conditions_met.append("rsi_valid")
            if volume_valid:
                conditions_met.append("volume_confirmation")
            if macd_bullish:
                conditions_met.append("macd_bullish")
            
            # Generate signal
            signal_strength = len(conditions_met) / 4.0  # 0-1 scale
            
            if len(conditions_met) >= 2:  # Need at least 2 conditions
                return {
                    'action': 'BUY',
                    'signal_source': 'technical',
                    'signal_strength': signal_strength,
                    'confidence': signal_strength,  # Technical confidence = signal strength
                    'entry_price': current_price,
                    'stop_loss': current_price * 0.99,  # 1% stop loss
                    'target': current_price * 1.02,  # 2% target
                    'conditions_met': conditions_met,
                    'indicators': {
                        'price': current_price,
                        'ma20': current_ma20,
                        'ma50': current_ma50,
                        'rsi': current_rsi,
                        'macd': current_macd,
                        'macd_signal': current_macd_signal,
                        'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1
                    }
                }
        
        except Exception as e:
            logger.error(f"Error generating technical signal for {instrument}: {e}")
        
        return None
    
    def _generate_ai_signal(self, df: pd.DataFrame, instrument: str) -> Optional[Dict]:
        """
        Generate AI model signal prediction
        
        Args:
            df: OHLCV DataFrame
            instrument: Stock/instrument code
            
        Returns:
            Signal dictionary with AI confidence or None
        """
        if not self.enable_ai or not self.ai_initialized or self.ai_generator is None:
            return None
        
        try:
            current_price = df['close'].iloc[-1]
            
            # Generate AI signal
            ai_signal = self.ai_generator.generate_signal()
            
            if ai_signal and ai_signal.get('confidence', 0) >= self.ai_confidence_threshold:
                return {
                    'action': 'BUY' if ai_signal['signal'] == 'UP' else 'SELL',
                    'signal_source': 'ai_model',
                    'signal_strength': ai_signal.get('confidence', 0),
                    'confidence': ai_signal.get('confidence', 0),
                    'entry_price': current_price,
                    'ai_models': {
                        'ensemble_prediction': ai_signal.get('signal'),
                        'confidence_score': ai_signal.get('confidence'),
                        'signal_validity': ai_signal.get('valid'),
                        'feature_importance': self.ai_generator.signal_model.get_top_features(n=5) 
                                            if hasattr(self.ai_generator, 'signal_model') else None
                    }
                }
        
        except Exception as e:
            logger.error(f"Error generating AI signal for {instrument}: {e}")
        
        return None
    
    def _combine_signals(self, instrument: str, technical_signal: Optional[Dict], 
                        ai_signal: Optional[Dict]) -> Optional[Dict]:
        """
        Combine technical and AI signals
        
        Strategy:
        - If both signals agree (BUY/SELL): Use combined confidence
        - If only one signal available: Use that signal
        - If signals conflict: Reject (higher confidence from both needed)
        
        Args:
            instrument: Stock/instrument code
            technical_signal: Technical analysis signal
            ai_signal: AI model signal
            
        Returns:
            Combined signal dictionary or None
        """
        if not technical_signal and not ai_signal:
            return None
        
        # If only one signal available
        if not technical_signal:
            return ai_signal
        if not ai_signal:
            return technical_signal
        
        # Both signals available - combine them
        tech_action = technical_signal.get('action')
        ai_action = ai_signal.get('action')
        
        # Signals must agree on direction
        if tech_action != ai_action:
            logger.info(f"{instrument}: Signals conflict (Technical: {tech_action}, AI: {ai_action}). "
                       f"Skipping trade.")
            return None
        
        # Combine confidence scores
        tech_confidence = technical_signal.get('confidence', 0)
        ai_confidence = ai_signal.get('confidence', 0)
        combined_confidence = (tech_confidence + ai_confidence) / 2
        
        # Combine signals
        combined_signal = {
            'action': tech_action,
            'signal_source': 'combined_technical_ai',
            'signal_strength': combined_confidence,
            'confidence': combined_confidence,
            'entry_price': technical_signal.get('entry_price'),
            'stop_loss': technical_signal.get('stop_loss'),
            'target': technical_signal.get('target'),
            'technical_confidence': tech_confidence,
            'ai_confidence': ai_confidence,
            'technical_conditions': technical_signal.get('conditions_met', []),
            'ai_strength': ai_signal.get('signal_strength', 0),
            'indicators': technical_signal.get('indicators', {}),
            'ai_details': {
                'prediction': ai_signal.get('action'),
                'confidence': ai_confidence,
                'models': ai_signal.get('ai_models')
            }
        }
        
        logger.info(f"{instrument}: Combined signal: {tech_action} "
                   f"(Technical: {tech_confidence:.2%}, AI: {ai_confidence:.2%}, "
                   f"Combined: {combined_confidence:.2%})")
        
        return combined_signal
    
    def execute_strategy(self, signal: Dict) -> bool:
        """
        Execute strategy based on generated signals
        
        Args:
            signal: Signal dictionary from generate_signals()
            
        Returns:
            True if execution successful, False otherwise
        """
        try:
            if not signal or not self.order_manager:
                return False
            
            action = signal.get('action')
            entry_price = signal.get('entry_price')
            stop_loss = signal.get('stop_loss')
            target = signal.get('target')
            confidence = signal.get('confidence', 0)
            
            if action not in ['BUY', 'SELL']:
                return False
            
            # Log execution details
            logger.info(f"Executing {action} order at {entry_price:.2f} "
                       f"(Confidence: {confidence:.2%})")
            
            # Send notification
            if self.notification_service:
                msg = (f"{action} signal from {signal.get('signal_source', 'unknown')}\n"
                      f"Price: {entry_price:.2f}\n"
                      f"Confidence: {confidence:.2%}\n"
                      f"Stop Loss: {stop_loss:.2f}\n"
                      f"Target: {target:.2f}")
                self.notification_service.send_notification(msg, "SIGNAL")
            
            # Update performance metrics
            self.update_performance_metrics(0)  # Will update with actual PnL later
            
            return True
        
        except Exception as e:
            logger.error(f"Error executing strategy: {e}")
            return False
    
    def get_signal_history(self, instrument: Optional[str] = None) -> Dict:
        """
        Get signal history for analysis
        
        Args:
            instrument: Specific instrument or None for all
            
        Returns:
            Signal history dictionary
        """
        if instrument:
            return self.signal_history.get(instrument, [])
        return self.signal_history
    
    def get_ai_stats(self) -> Dict:
        """
        Get AI model statistics
        
        Returns:
            Dictionary with AI performance metrics
        """
        if not self.enable_ai or not self.ai_initialized:
            return {'ai_enabled': False}
        
        stats = {
            'ai_enabled': True,
            'ai_initialized': self.ai_initialized,
            'confidence_threshold': self.ai_confidence_threshold,
            'total_signals_generated': sum(len(v) for v in self.signal_history.values()),
            'signals_by_source': {
                'technical_only': 0,
                'ai_only': 0,
                'combined': 0
            }
        }
        
        # Count signal sources
        for signals_list in self.signal_history.values():
            for signal_record in signals_list:
                source = signal_record.get('signal', {}).get('signal_source', 'unknown')
                if source == 'combined_technical_ai':
                    stats['signals_by_source']['combined'] += 1
                elif source == 'technical':
                    stats['signals_by_source']['technical_only'] += 1
                elif source == 'ai_model':
                    stats['signals_by_source']['ai_only'] += 1
        
        return stats
