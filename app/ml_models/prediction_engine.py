"""
ML PREDICTION ENGINE
====================

Integrated machine learning inference module for market predictions.

Predictions:
1. Price Direction: UP / DOWN (probability 0-1)
2. Expected Move: Magnitude of predicted move (e.g., +2.5%)
3. Volatility Forecast: ATR/volatility estimate
4. Confidence Score: Overall confidence in prediction

Architecture:
    PredictionEngine
    ├── ModelLoader (load pre-trained models)
    ├── FeaturePreprocessor (prepare input features)
    ├── EnsemblePredictor (combine multiple models)
    └── PredictionAggregator (output standardized prediction)

Models Supported:
- XGBoost (primary)
- Logistic Regression (baseline)
- Random Forest (secondary)
- Neural Networks (Phase 3 future)

Usage:
    engine = PredictionEngine(
        model_paths={
            'price_direction': 'models/price_direction_xgb.pkl',
            'expected_move': 'models/expected_move_xgb.pkl'
        }
    )
    
    prediction = engine.predict(features_df)
    # Returns: {
    #     'direction': 'UP',
    #     'direction_confidence': 0.72,
    #     'expected_move_pct': 2.5,
    #     'volatility_forecast': 2.1,
    #     'overall_confidence': 0.70,
    #     'timestamp': datetime
    # }
"""

import logging
import os
import pickle
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
except ImportError:
    logging.warning("scikit-learn not available - some features disabled")

try:
    import xgboost as xgb
except ImportError:
    xgb = None

logger = logging.getLogger(__name__)


class PredictionDirection(Enum):
    """Direction of predicted price movement"""
    UP = "UP"
    DOWN = "DOWN"
    NEUTRAL = "NEUTRAL"


@dataclass
class Prediction:
    """Standardized prediction output"""
    timestamp: datetime
    symbol: str
    
    # Primary prediction
    direction: PredictionDirection
    direction_confidence: float  # 0-1, probability of direction
    
    # Expected move
    expected_move_pct: float  # Magnitude of move, e.g., 2.5 for +2.5%
    expected_move_direction: str  # "+", "-"
    
    # Volatility
    volatility_forecast: float  # Expected ATR or volatility
    
    # Meta
    overall_confidence: float  # 0-1, how confident in this prediction
    model_version: str
    models_used: List[str]
    
    # Additional context
    supporting_factors: List[str] = None
    risk_score: float = 0.5  # 0-1, 0 = low risk, 1 = high risk
    
    def to_dict(self):
        """Convert to dictionary"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        d['direction'] = self.direction.value
        d['supporting_factors'] = self.supporting_factors or []
        return d
    
    def is_strong_signal(self, confidence_threshold: float = 0.65) -> bool:
        """Check if prediction is a strong trading signal"""
        return self.overall_confidence >= confidence_threshold


class PredictionEngine:
    """
    Central ML prediction engine.
    Handles model loading, feature preprocessing, and inference.
    """
    
    def __init__(self, model_paths: Dict[str, str] = None, model_dir: str = None):
        """
        Initialize prediction engine.
        
        Args:
            model_paths: Dict of model names to file paths
            model_dir: Directory containing models (auto-discover)
        """
        self.models = {}
        self.scalers = {}
        self.model_version = "1.0"
        self.last_prediction = None
        
        # Load models
        if model_paths:
            for name, path in model_paths.items():
                self._load_model(name, path)
        elif model_dir:
            self._load_models_from_directory(model_dir)
        else:
            logger.warning("No model paths provided - engine in demo mode")
        
        logger.info(f"PredictionEngine initialized with {len(self.models)} models")
    
    # ==================== MODEL LOADING ====================
    
    def _load_model(self, name: str, filepath: str):
        """Load a single model from file"""
        try:
            if not os.path.exists(filepath):
                logger.warning(f"Model file not found: {filepath}")
                return
            
            # Try different formats
            if filepath.endswith('.pkl'):
                with open(filepath, 'rb') as f:
                    model = pickle.load(f)
            elif filepath.endswith('.joblib'):
                model = joblib.load(filepath)
            else:
                logger.error(f"Unsupported model format: {filepath}")
                return
            
            self.models[name] = model
            logger.info(f"Loaded model: {name}")
            
        except Exception as e:
            logger.error(f"Error loading model {name}: {e}", exc_info=True)
    
    def _load_models_from_directory(self, model_dir: str):
        """Auto-discover and load models from directory"""
        if not os.path.isdir(model_dir):
            logger.error(f"Model directory not found: {model_dir}")
            return
        
        for filename in os.listdir(model_dir):
            if filename.endswith(('.pkl', '.joblib')):
                name = filename.replace('.pkl', '').replace('.joblib', '')
                filepath = os.path.join(model_dir, filename)
                self._load_model(name, filepath)
    
    def add_model(self, name: str, model):
        """Register a model programmatically"""
        self.models[name] = model
        logger.info(f"Registered model: {name}")
    
    # ==================== PREDICTION ====================
    
    def predict(self, features: pd.DataFrame, symbol: str = "INDEX") -> Prediction:
        """
        Make prediction given feature vector.
        
        Args:
            features: DataFrame with feature columns
            symbol: Stock/index symbol for tracking
        
        Returns:
            Prediction object
        """
        try:
            timestamp = datetime.now()
            
            # Validate features
            if features is None or features.empty:
                logger.warning("Empty features provided")
                return self._create_neutral_prediction(symbol, timestamp)
            
            # Preprocess features
            X = self._preprocess_features(features)
            
            # Get predictions from available models
            predictions = {}
            
            if 'price_direction' in self.models:
                pred = self._predict_direction(X)
                predictions['direction'] = pred
            
            if 'expected_move' in self.models:
                pred = self._predict_move(X)
                predictions['move'] = pred
            
            if 'volatility' in self.models:
                pred = self._predict_volatility(X)
                predictions['volatility'] = pred
            
            # Aggregate predictions
            result = self._aggregate_predictions(
                predictions=predictions,
                symbol=symbol,
                timestamp=timestamp,
                models_used=list(self.models.keys())
            )
            
            self.last_prediction = result
            return result
            
        except Exception as e:
            logger.error(f"Error in prediction: {e}", exc_info=True)
            return self._create_neutral_prediction(symbol, datetime.now())
    
    def _preprocess_features(self, features: pd.DataFrame) -> np.ndarray:
        """Prepare features for model inference"""
        try:
            # Handle missing values
            features = features.fillna(features.mean())
            
            # Convert to numpy
            X = features.values if isinstance(features, pd.DataFrame) else features
            
            # Ensure 2D
            if X.ndim == 1:
                X = X.reshape(1, -1)
            
            return X
        except Exception as e:
            logger.error(f"Error preprocessing features: {e}")
            return np.array([[0]])
    
    def _predict_direction(self, X: np.ndarray) -> Dict:
        """Predict price direction (UP/DOWN)"""
        try:
            model = self.models.get('price_direction')
            if not model:
                return {'direction': 'NEUTRAL', 'confidence': 0.5}
            
            # Get prediction and probability
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(X)[0]
                confidence = max(proba)
                direction = 'UP' if proba[1] > 0.5 else 'DOWN'
            else:
                pred = model.predict(X)[0]
                direction = 'UP' if pred > 0 else 'DOWN'
                confidence = 0.6 if abs(pred) > 0.5 else 0.5
            
            return {
                'direction': direction,
                'confidence': float(confidence),
                'raw_prediction': float(proba[1]) if hasattr(model, 'predict_proba') else float(pred)
            }
        except Exception as e:
            logger.error(f"Error in direction prediction: {e}")
            return {'direction': 'NEUTRAL', 'confidence': 0.5}
    
    def _predict_move(self, X: np.ndarray) -> Dict:
        """Predict expected move percentage"""
        try:
            model = self.models.get('expected_move')
            if not model:
                return {'move_pct': 1.5, 'confidence': 0.5}
            
            # Get prediction
            move_pred = model.predict(X)[0]
            
            # Ensure reasonable bounds
            move_pct = float(np.clip(move_pred, 0.1, 10.0))
            
            return {
                'move_pct': move_pct,
                'confidence': 0.6,
                'raw_prediction': float(move_pred)
            }
        except Exception as e:
            logger.error(f"Error in move prediction: {e}")
            return {'move_pct': 1.5, 'confidence': 0.5}
    
    def _predict_volatility(self, X: np.ndarray) -> Dict:
        """Predict volatility/ATR"""
        try:
            model = self.models.get('volatility')
            if not model:
                return {'volatility': 2.0, 'confidence': 0.5}
            
            vol_pred = model.predict(X)[0]
            volatility = float(np.clip(vol_pred, 0.5, 5.0))
            
            return {
                'volatility': volatility,
                'confidence': 0.6,
                'raw_prediction': float(vol_pred)
            }
        except Exception as e:
            logger.error(f"Error in volatility prediction: {e}")
            return {'volatility': 2.0, 'confidence': 0.5}
    
    def _aggregate_predictions(self, predictions: Dict, symbol: str, 
                               timestamp: datetime, models_used: List[str]) -> Prediction:
        """Combine individual model predictions"""
        
        # Direction
        direction_pred = predictions.get('direction', {})
        direction_str = direction_pred.get('direction', 'NEUTRAL')
        direction = PredictionDirection[direction_str]
        direction_conf = direction_pred.get('confidence', 0.5)
        
        # Move
        move_pred = predictions.get('move', {})
        expected_move = move_pred.get('move_pct', 1.5)
        
        # Volatility
        vol_pred = predictions.get('volatility', {})
        volatility = vol_pred.get('volatility', 2.0)
        
        # Overall confidence (weighted average)
        confidences = [
            direction_conf * 0.6,  # Direction weighted 60%
            move_pred.get('confidence', 0.5) * 0.25,  # Move weighted 25%
            vol_pred.get('confidence', 0.5) * 0.15  # Volatility weighted 15%
        ]
        overall_conf = np.mean(confidences)
        
        # Determine move direction
        move_direction = "+" if direction == PredictionDirection.UP else "-"
        
        # Supporting factors
        factors = []
        if direction_conf > 0.70:
            factors.append(f"Strong {direction_str} signal (confidence: {direction_conf:.1%})")
        if expected_move > 3.0:
            factors.append(f"Large expected move: {expected_move:.1f}%")
        if volatility > 3.0:
            factors.append(f"High volatility: {volatility:.1f}%")
        
        # Risk score (inverse of confidence)
        risk_score = 1.0 - overall_conf
        
        return Prediction(
            timestamp=timestamp,
            symbol=symbol,
            direction=direction,
            direction_confidence=direction_conf,
            expected_move_pct=expected_move,
            expected_move_direction=move_direction,
            volatility_forecast=volatility,
            overall_confidence=overall_conf,
            model_version=self.model_version,
            models_used=models_used,
            supporting_factors=factors,
            risk_score=risk_score
        )
    
    def _create_neutral_prediction(self, symbol: str, timestamp: datetime) -> Prediction:
        """Create neutral/default prediction"""
        return Prediction(
            timestamp=timestamp,
            symbol=symbol,
            direction=PredictionDirection.NEUTRAL,
            direction_confidence=0.5,
            expected_move_pct=1.5,
            expected_move_direction="+",
            volatility_forecast=2.0,
            overall_confidence=0.5,
            model_version=self.model_version,
            models_used=[],
            supporting_factors=["No models loaded - neutral prediction"],
            risk_score=1.0
        )
    
    # ==================== BATCH PREDICTIONS ====================
    
    def predict_batch(self, features_list: List[pd.DataFrame], 
                     symbols: List[str] = None) -> List[Prediction]:
        """Predict for multiple feature sets"""
        if symbols is None:
            symbols = [f"SYM_{i}" for i in range(len(features_list))]
        
        predictions = []
        for features, symbol in zip(features_list, symbols):
            pred = self.predict(features, symbol)
            predictions.append(pred)
        
        return predictions
    
    # ==================== MODEL INFO ====================
    
    def get_model_info(self) -> Dict:
        """Get information about loaded models"""
        info = {}
        for name, model in self.models.items():
            info[name] = {
                'type': type(model).__name__,
                'loaded': True,
                'has_predict': hasattr(model, 'predict'),
                'has_predict_proba': hasattr(model, 'predict_proba')
            }
        return info
    
    def get_last_prediction(self) -> Optional[Prediction]:
        """Get the last prediction made"""
        return self.last_prediction
    
    # ==================== PERFORMANCE MONITORING ====================
    
    def track_prediction_accuracy(self, prediction: Prediction, actual_direction: str, 
                                 actual_move: float) -> Dict:
        """
        Track prediction accuracy for monitoring.
        
        Args:
            prediction: Prediction object
            actual_direction: Actual direction ('UP' / 'DOWN')
            actual_move: Actual move percentage
        
        Returns: Accuracy metrics
        """
        direction_correct = (prediction.direction.value == actual_direction)
        
        # Check if move was in expected direction
        expected_correct = (prediction.expected_move_direction == ("+" if actual_direction == "UP" else "-"))
        
        # Move magnitude accuracy (within 30%)
        move_tolerance = prediction.expected_move_pct * 0.3
        move_accurate = abs(actual_move - prediction.expected_move_pct) <= move_tolerance
        
        return {
            'timestamp': prediction.timestamp,
            'symbol': prediction.symbol,
            'direction_correct': direction_correct,
            'direction_confidence_at_pred': prediction.direction_confidence,
            'expected_correct': expected_correct,
            'move_accurate': move_accurate,
            'predicted_move': prediction.expected_move_pct,
            'actual_move': actual_move,
            'overall_correct': direction_correct and move_accurate
        }


# ==================== EXAMPLE USAGE & TESTING ====================

if __name__ == "__main__":
    """
    Example usage and testing
    """
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create dummy feature data
    features_data = {
        'ma_ratio': [1.02],  # MA20/MA50
        'rsi': [65.5],       # RSI (0-100)
        'atr': [1.5],        # ATR
        'volume_ratio': [1.1], # Volume vs MA
        'bb_position': [0.75], # Within Bollinger Bands (0-1)
        'momentum': [2.5]    # Momentum %
    }
    features_df = pd.DataFrame(features_data)
    
    # Create engine (no real models, demo mode)
    engine = PredictionEngine()
    
    # Make prediction
    print("\n--- Prediction Test ---")
    pred = engine.predict(features_df, symbol="NIFTY")
    
    print(f"Symbol: {pred.symbol}")
    print(f"Direction: {pred.direction.value}")
    print(f"Direction Confidence: {pred.direction_confidence:.2%}")
    print(f"Expected Move: {pred.expected_move_pct:.1f}%")
    print(f"Volatility Forecast: {pred.volatility_forecast:.1f}%")
    print(f"Overall Confidence: {pred.overall_confidence:.2%}")
    print(f"Risk Score: {pred.risk_score:.2f}")
    print(f"Strong Signal: {pred.is_strong_signal()}")
    print(f"Supporting Factors: {pred.supporting_factors}")
    
    # Model info
    print(f"\n--- Model Info ---")
    print(f"Loaded models: {engine.get_model_info()}")
