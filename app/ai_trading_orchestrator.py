"""
AI-Enabled Trading System Orchestrator
======================================

Integrates all AI/ML components for intelligent trading:
1. Emergency Stop System (kill-switch) with trading engine
2. ML Prediction Engine for signal validation
3. Feature Engineering for ML inputs
4. Enhanced Risk Management with AI insights

This module coordinates the trading pipeline with advanced AI/ML capabilities
while maintaining safety and risk controls.

Architecture:
    TradingEngine (orchestrator)
    ├── EmergencyStopSystem (safety override)
    ├── FeatureEngine (compute indicators)
    ├── PredictionEngine (ML models)
    ├── RiskManager (enhanced validation)
    └── [existing Stage 1-5 components]

Usage:
    # Initialize AI system
    ai_system = AITradingOrchestrator(config)
    
    # Run with full AI integration
    result = ai_system.run_trading_cycle()
    
    # Check emergency stop status
    if ai_system.is_trading_active():
        print("Trading active")
    else:
        print("Emergency stop triggered")
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


@dataclass
class AITradingResult:
    """Complete AI trading cycle result"""
    cycle_id: str
    timestamp: datetime
    
    # Emergency stop status
    emergency_stop_active: bool
    
    # Features computed
    features_computed: bool
    
    # ML predictions
    predictions_available: bool
    
    # Risk assessment
    risk_approved: bool = False
    
    # Optional fields with defaults
    emergency_stop_reason: Optional[str] = None
    feature_vector: Optional[Dict] = None
    bullish_score: float = 0.0
    predicted_direction: Optional[str] = None  # UP, DOWN, NEUTRAL
    prediction_confidence: float = 0.0
    risk_message: str = ""
    signals_generated: int = 0
    signals_executed: int = 0
    execution_errors: int = 0
    
    # Position management
    positions_managed: int = 0
    exits_executed: int = 0
    
    # Overall result
    cycle_successful: bool = False
    errors: List[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d


class AITradingOrchestrator:
    """
    Main orchestrator for AI-Enabled Trading System.
    
    Responsibilities:
    1. Initialize all AI/ML components
    2. Manage component lifecycle
    3. Coordinate execution with AI enhancements
    4. Handle errors and fallback logic
    5. Provide monitoring and diagnostics
    """
    
    def __init__(self, config: Any, trading_engine: Any, emergency_stop: Any,
                 feature_engine: Any, prediction_engine: Any,
                 risk_manager: Any, notifications: Any = None):
        """
        Initialize AI Trading Orchestrator
        
        Args:
            config: Configuration object
            trading_engine: Primary TradingEngine instance
            emergency_stop: Emergency stop system
            feature_engine: FeatureEngine for indicator computation
            prediction_engine: PredictionEngine for ML predictions
            risk_manager: Enhanced risk manager
            notifications: Optional notification service
        """
        self.config = config
        self.trading_engine = trading_engine
        self.emergency_stop = emergency_stop
        self.feature_engine = feature_engine
        self.prediction_engine = prediction_engine
        self.risk_manager = risk_manager
        self.notifications = notifications
        
        # State tracking
        self.cycle_count = 0
        self.ai_enabled = True
        self.fallback_to_legacy = False  # If AI fails, use legacy trading only
        
        logger.info("AI Trading Orchestrator initialized")
    
    def run_trading_cycle(self) -> AITradingResult:
        """
        Execute one complete AI-enabled trading cycle.
        
        Process:
        1. Check Emergency Stop status
        2. Compute features (if not in emergency stop)
        3. Generate ML predictions
        4. Validate signals with ML confidence
        5. Execute approved trades
        6. Manage exits with AI insights
        
        Returns:
            AITradingResult with full cycle diagnostics
        """
        self.cycle_count += 1
        cycle_id = f"ai_cycle_{self.cycle_count}_{int(datetime.now().timestamp())}"
        
        result = AITradingResult(
            cycle_id=cycle_id,
            timestamp=datetime.now(),
            emergency_stop_active=False,
            features_computed=False,
            predictions_available=False,
            risk_approved=False,
            errors=[]
        )
        
        try:
            logger.info(f"[{cycle_id}] Starting AI-Enabled Trading Cycle")
            
            # ===== STEP 1: CHECK EMERGENCY STOP =====
            if not self._check_emergency_stop(result):
                logger.error(f"[{cycle_id}] Emergency stop is active, halting trading")
                return result
            
            # ===== STEP 2: COMPUTE FEATURES =====
            if not self._compute_features(result):
                logger.warning(f"[{cycle_id}] Feature computation failed, continuing without AI")
                self.fallback_to_legacy = True
            
            # ===== STEP 3: GENERATE ML PREDICTIONS =====
            if result.features_computed:
                if not self._generate_predictions(result):
                    logger.warning(f"[{cycle_id}] ML prediction failed, using legacy only")
                    self.fallback_to_legacy = True
            
            # ===== STEP 4: VALIDATE SIGNALS WITH RISK =====
            if not self._validate_signals(result):
                logger.warning(f"[{cycle_id}] Signal validation failed")
                result.errors.append("Signal validation failed")
                return result
            
            # ===== STEP 5: EXECUTE TRADES =====
            if not self._execute_trades(result):
                logger.warning(f"[{cycle_id}] Trade execution had errors")
            
            # ===== STEP 6: MANAGE EXITS =====
            if not self._manage_exits(result):
                logger.warning(f"[{cycle_id}] Exit management had errors")
            
            result.cycle_successful = True
            logger.info(f"[{cycle_id}] AI cycle completed successfully")
            
        except Exception as e:
            logger.error(f"[{cycle_id}] Unexpected error in AI cycle: {e}")
            result.errors.append(f"AI cycle error: {str(e)}")
            result.cycle_successful = False
        
        return result
    
    def _check_emergency_stop(self, result: AITradingResult) -> bool:
        """
        Check if emergency stop is active.
        
        Returns:
            True if trading should proceed (emergency stop inactive)
            False if trading halted (emergency stop active)
        """
        try:
            if self.emergency_stop.is_active():
                result.emergency_stop_active = True
                result.emergency_stop_reason = self.emergency_stop.get_reason()
                logger.warning(f"Emergency stop active: {result.emergency_stop_reason}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking emergency stop: {e}")
            result.errors.append(f"Emergency stop check failed: {str(e)}")
            return False
    
    def _compute_features(self, result: AITradingResult) -> bool:
        """
        Compute feature vector for ML models.
        
        Returns:
            True if features computed successfully
        """
        try:
            if not self.feature_engine:
                logger.debug("Feature engine not available, skipping feature computation")
                return False
            
            # Get primary symbol (typically NIFTY50)
            symbol = getattr(self.config, 'PRIMARY_SYMBOL', 'NIFTY50')
            
            # Compute features
            feature_vector = self.feature_engine.compute_all_features(symbol)
            
            if feature_vector is None:
                logger.warning(f"Failed to compute features for {symbol}")
                return False
            
            # Store results
            result.features_computed = True
            result.feature_vector = asdict(feature_vector)
            result.bullish_score = feature_vector.bullish_score
            
            logger.info(f"Features computed: bullish_score={feature_vector.bullish_score:.1f}")
            return True
            
        except Exception as e:
            logger.error(f"Error computing features: {e}")
            result.errors.append(f"Feature computation error: {str(e)}")
            return False
    
    def _generate_predictions(self, result: AITradingResult) -> bool:
        """
        Generate ML predictions using computed features.
        
        Returns:
            True if predictions generated successfully
        """
        try:
            if not self.prediction_engine or not result.feature_vector:
                return False
            
            # Prepare features for prediction
            features = self._prepare_features_for_model(result.feature_vector)
            
            # Get prediction
            prediction = self.prediction_engine.predict_direction(features)
            
            if prediction is None:
                logger.warning("ML prediction returned None")
                return False
            
            # Store results
            result.predictions_available = True
            result.predicted_direction = prediction.get('direction', 'NEUTRAL')
            result.prediction_confidence = prediction.get('confidence', 0.0)
            
            logger.info(
                f"ML Prediction: {result.predicted_direction} "
                f"(confidence: {result.prediction_confidence:.2%})"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            result.errors.append(f"Prediction error: {str(e)}")
            return False
    
    def _validate_signals(self, result: AITradingResult) -> bool:
        """
        Validate trading signals with risk checks.
        
        Considers:
        - Kill-switch status
        - ML predictions and confidence
        - Feature bullish score
        - Risk limits
        
        Returns:
            True if signals validated successfully
        """
        try:
            # Check risk manager approval
            risk_ok, risk_msg = self.risk_manager.validate_trading_cycle()
            
            result.risk_approved = risk_ok
            result.risk_message = risk_msg
            
            if not risk_ok:
                logger.warning(f"Risk validation failed: {risk_msg}")
                return False
            
            # Additional checks if ML is available
            if result.predictions_available:
                # Reject signals if ML predicts BEARISH with high confidence
                if (result.predicted_direction == 'DOWN' and 
                    result.prediction_confidence > 0.7):
                    logger.info("Rejecting signals: ML predicts strong downtrend")
                    result.risk_approved = False
                    result.risk_message = "ML predicts bearish market"
                    return False
                
                # Boost confidence if ML bullish and features bullish
                if (result.predicted_direction == 'UP' and 
                    result.bullish_score > 60):
                    logger.info("High confidence: ML and features both bullish")
            
            logger.info("Signals validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error validating signals: {e}")
            result.errors.append(f"Validation error: {str(e)}")
            return False
    
    def _execute_trades(self, result: AITradingResult) -> bool:
        """
        Execute approved trades using Phase 1 executor.
        
        Returns:
            True if execution completed without critical errors
        """
        try:
            if not result.risk_approved:
                logger.info("Trades not approved for execution")
                result.signals_executed = 0
                return True
            
            # Run Phase 1 trading engine cycle
            phase1_result = self.trading_engine.run_cycle()
            
            if phase1_result is None:
                return False
            
            # Extract metrics from Phase 1
            if isinstance(phase1_result, dict):
                result.signals_generated = phase1_result.get('signals_generated', 0)
                result.signals_executed = phase1_result.get('trades_executed', 0)
                result.execution_errors = phase1_result.get('execution_failures', 0)
            else:
                # Handle CycleMetrics object
                result.signals_generated = getattr(phase1_result, 'signals_generated', 0)
                result.signals_executed = getattr(phase1_result, 'trades_executed', 0)
                result.execution_errors = getattr(phase1_result, 'execution_failures', 0)
            
            logger.info(
                f"Trades executed: {result.signals_executed} "
                f"(errors: {result.execution_errors})"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error executing trades: {e}")
            result.errors.append(f"Trade execution error: {str(e)}")
            return False
    
    def _manage_exits(self, result: AITradingResult) -> bool:
        """
        Manage exits for open positions.
        
        Returns:
            True if exit management completed
        """
        try:
            # Get position tracker from trading engine
            position_tracker = getattr(self.trading_engine, 'position_tracker', None)
            
            if not position_tracker:
                logger.debug("Position tracker not available")
                return True
            
            # Get open positions
            open_positions = position_tracker.get_open_positions()
            result.positions_managed = len(open_positions) if open_positions else 0
            
            # Check exits using profit manager
            profit_manager = getattr(self.trading_engine, 'profit_manager', None)
            
            if profit_manager and open_positions:
                exits = profit_manager.check_exits(open_positions)
                result.exits_executed = len(exits) if exits else 0
            
            logger.info(f"Positions managed: {result.positions_managed}, exits: {result.exits_executed}")
            return True
            
        except Exception as e:
            logger.error(f"Error managing exits: {e}")
            result.errors.append(f"Exit management error: {str(e)}")
            return False
    
    def _prepare_features_for_model(self, feature_dict: Dict) -> Dict:
        """
        Prepare feature dictionary for ML model input.
        
        Converts FeatureVector dataclass dict to model input format.
        """
        # Extract numeric features for ML model
        model_features = {
            'ma_ratio': feature_dict.get('ma_ratio', 1.0),
            'rsi_14': feature_dict.get('rsi_14', 50),
            'atr_14': feature_dict.get('atr_14', 0),
            'bb_position': feature_dict.get('bb_position', 0.5),
            'volume_ratio': feature_dict.get('volume_ratio', 1.0),
            'stoch_rsi': feature_dict.get('stoch_rsi', 50),
            'ma_trend': feature_dict.get('ma_trend', 0),
            'macd_signal': feature_dict.get('macd_signal', 0),
        }
        return model_features
    
    def is_trading_active(self) -> bool:
        """Check if system is ready for trading"""
        return not self.emergency_stop.is_active()
    
    def get_system_status(self) -> Dict:
        """Get complete system status"""
        return {
            'ai_enabled': self.ai_enabled,
            'emergency_stop_active': self.emergency_stop.is_active(),
            'emergency_stop_reason': self.emergency_stop.get_reason(),
            'feature_engine_available': self.feature_engine is not None,
            'prediction_engine_available': self.prediction_engine is not None,
            'fallback_to_legacy': self.fallback_to_legacy,
            'cycle_count': self.cycle_count,
            'timestamp': datetime.now().isoformat()
        }
