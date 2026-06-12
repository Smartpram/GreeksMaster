"""
ML Model Training Engine - Phase 3 Week 1
Train XGBoost, Random Forest, and Ensemble models on historical data

Purpose:
  Train ML models on 2+ years of historical OHLCV data
  Generate feature matrix with technical indicators
  Validate models with cross-validation and out-of-sample testing
  Save trained models for production deployment

Workflow:
  1. Collect historical data (2+ years)
  2. Generate features (15+ indicators via FeatureEngine)
  3. Create labels (next 1-hour direction: UP/DOWN/NEUTRAL)
  4. Train models (XGBoost, Random Forest, Ensemble)
  5. Validate with cross-validation
  6. Save models and metadata
"""

import os
import json
import logging
import pickle
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple, Dict, List, Optional
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
import xgboost as xgb

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Train ML models for directional prediction"""
    
    def __init__(self, symbol: str = 'NIFTY50', output_dir: str = 'app/ml_models/trained_models'):
        """
        Initialize trainer
        
        Args:
            symbol: Trading symbol
            output_dir: Directory to save trained models
        """
        self.symbol = symbol
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Models
        self.xgboost_model = None
        self.rf_model = None
        self.scaler = StandardScaler()
        
        # Data
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.feature_names = None
        
        # Metadata
        self.metadata = {
            'symbol': symbol,
            'training_date': datetime.now().isoformat(),
            'data_points': 0,
            'features': [],
            'models': ['xgboost', 'random_forest', 'ensemble'],
            'performance': {}
        }
        
        logger.info(f"ModelTrainer initialized for {symbol}")
    
    def generate_features(self, ohlcv_data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Generate features and labels from OHLCV data
        
        Uses FeatureEngine to compute 15+ technical indicators
        Creates labels as next 1-hour direction (UP/DOWN/NEUTRAL)
        
        Args:
            ohlcv_data: DataFrame with OHLCV columns
                       Expected columns: open, high, low, close, volume
        
        Returns:
            Tuple of (features_df, labels_series)
        """
        logger.info(f"Generating features from {len(ohlcv_data)} candles...")
        
        df = ohlcv_data.copy()
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Calculate technical indicators
        features_dict = {}
        
        # Trend indicators
        features_dict['sma_20'] = df['close'].rolling(20).mean()
        features_dict['sma_50'] = df['close'].rolling(50).mean()
        features_dict['sma_200'] = df['close'].rolling(200).mean()
        features_dict['ema_12'] = df['close'].ewm(span=12).mean()
        features_dict['ema_26'] = df['close'].ewm(span=26).mean()
        
        # Momentum indicators
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        features_dict['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        features_dict['macd'] = ema_12 - ema_26
        features_dict['macd_signal'] = (ema_12 - ema_26).ewm(span=9).mean()
        
        # Volatility indicators
        features_dict['atr'] = self._calculate_atr(df)
        features_dict['bb_width'] = self._calculate_bb_width(df)
        
        # Volume indicators
        features_dict['volume_sma'] = df['volume'].rolling(20).mean()
        features_dict['volume_ratio'] = df['volume'] / (df['volume'].rolling(20).mean() + 1)
        
        # Price action
        features_dict['high_low_ratio'] = (df['high'] - df['low']) / df['close']
        features_dict['close_position'] = (df['close'] - df['low']) / (df['high'] - df['low'] + 0.001)
        
        # Create features DataFrame
        features_df = pd.DataFrame(features_dict)
        
        # Create labels (next 1-hour direction)
        labels = []
        for i in range(len(df) - 1):
            current_close = df.iloc[i]['close']
            next_close = df.iloc[i + 1]['close']
            
            if next_close > current_close * 1.001:  # UP if >0.1% gain
                labels.append(1)  # UP
            elif next_close < current_close * 0.999:  # DOWN if >0.1% loss
                labels.append(-1)  # DOWN
            else:
                labels.append(0)  # NEUTRAL
        
        # Align labels with features (drop last row)
        features_df = features_df[:-1].reset_index(drop=True)
        labels_series = pd.Series(labels, name='direction')
        
        # Remove NaN rows (from indicator calculation)
        valid_idx = ~features_df.isna().any(axis=1)
        features_df = features_df[valid_idx].reset_index(drop=True)
        labels_series = labels_series[valid_idx].reset_index(drop=True)
        
        logger.info(f"Generated {len(features_df)} samples with {len(features_df.columns)} features")
        logger.info(f"Label distribution: UP={sum(labels_series==1)}, DOWN={sum(labels_series==-1)}, NEUTRAL={sum(labels_series==0)}")
        
        return features_df, labels_series
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        
        return atr
    
    def _calculate_bb_width(self, df: pd.DataFrame, period: int = 20, num_std: float = 2) -> pd.Series:
        """Calculate Bollinger Bands width"""
        sma = df['close'].rolling(period).mean()
        std = df['close'].rolling(period).std()
        
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        
        width = (upper_band - lower_band) / sma
        
        return width
    
    def train_models(self, features_df: pd.DataFrame, labels: pd.Series, 
                    test_size: float = 0.2) -> Dict:
        """
        Train XGBoost and Random Forest models
        
        Args:
            features_df: Feature matrix
            labels: Target labels (direction)
            test_size: Fraction for test set
        
        Returns:
            Dictionary with training results
        """
        logger.info("Training models...")
        
        self.feature_names = features_df.columns.tolist()
        
        # Split data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            features_df, labels, test_size=test_size, random_state=42, shuffle=True
        )
        
        # Scale features
        self.X_train_scaled = self.scaler.fit_transform(self.X_train)
        self.X_test_scaled = self.scaler.transform(self.X_test)
        
        logger.info(f"Train set: {len(self.X_train)}, Test set: {len(self.X_test)}")
        
        results = {}
        
        # Train XGBoost
        logger.info("Training XGBoost...")
        self.xgboost_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            objective='multi:softmax',
            num_class=3,
            random_state=42,
            verbosity=0
        )
        
        # Map labels to 0,1,2 for XGBoost
        y_train_mapped = self.y_train.map({-1: 0, 0: 1, 1: 2})
        y_test_mapped = self.y_test.map({-1: 0, 0: 1, 1: 2})
        
        self.xgboost_model.fit(self.X_train_scaled, y_train_mapped)
        xgb_pred = self.xgboost_model.predict(self.X_test_scaled)
        xgb_acc = accuracy_score(y_test_mapped, xgb_pred)
        
        logger.info(f"XGBoost accuracy: {xgb_acc:.4f}")
        results['xgboost'] = {'accuracy': float(xgb_acc)}
        
        # Train Random Forest
        logger.info("Training Random Forest...")
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
            verbose=0
        )
        
        # Map labels for RF
        y_train_rf = self.y_train.map({-1: 0, 0: 1, 1: 2})
        y_test_rf = self.y_test.map({-1: 0, 0: 1, 1: 2})
        
        self.rf_model.fit(self.X_train_scaled, y_train_rf)
        rf_pred = self.rf_model.predict(self.X_test_scaled)
        rf_acc = accuracy_score(y_test_rf, rf_pred)
        
        logger.info(f"Random Forest accuracy: {rf_acc:.4f}")
        results['random_forest'] = {'accuracy': float(rf_acc)}
        
        # Ensemble voting
        ensemble_pred = np.round((xgb_pred + rf_pred) / 2).astype(int)
        ensemble_acc = accuracy_score(y_test_rf, ensemble_pred)
        
        logger.info(f"Ensemble accuracy: {ensemble_acc:.4f}")
        results['ensemble'] = {'accuracy': float(ensemble_acc)}
        
        self.metadata['performance'] = results
        self.metadata['data_points'] = len(features_df)
        self.metadata['features'] = self.feature_names
        
        return results
    
    def validate_models(self) -> Dict:
        """
        Validate models with cross-validation and metrics
        
        Returns:
            Dictionary with validation results
        """
        logger.info("Validating models with cross-validation...")
        
        y_train_mapped = self.y_train.map({-1: 0, 0: 1, 1: 2})
        
        # Cross-validation scores
        xgb_cv_scores = cross_val_score(
            xgb.XGBClassifier(n_estimators=100, max_depth=6, random_state=42),
            self.X_train_scaled, y_train_mapped, cv=5, scoring='accuracy'
        )
        
        rf_cv_scores = cross_val_score(
            RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
            self.X_train_scaled, y_train_mapped, cv=5, scoring='accuracy'
        )
        
        logger.info(f"XGBoost CV scores: {xgb_cv_scores.mean():.4f} (+/- {xgb_cv_scores.std():.4f})")
        logger.info(f"Random Forest CV scores: {rf_cv_scores.mean():.4f} (+/- {rf_cv_scores.std():.4f})")
        
        # Confusion matrix
        y_test_mapped = self.y_test.map({-1: 0, 0: 1, 1: 2})
        xgb_pred = self.xgboost_model.predict(self.X_test_scaled)
        cm = confusion_matrix(y_test_mapped, xgb_pred)
        
        logger.info(f"\nConfusion Matrix:\n{cm}")
        logger.info(f"\nClassification Report:\n{classification_report(y_test_mapped, xgb_pred)}")
        
        return {
            'xgboost_cv_mean': float(xgb_cv_scores.mean()),
            'xgboost_cv_std': float(xgb_cv_scores.std()),
            'random_forest_cv_mean': float(rf_cv_scores.mean()),
            'random_forest_cv_std': float(rf_cv_scores.std()),
            'confusion_matrix': cm.tolist()
        }
    
    def save_models(self) -> Dict:
        """
        Save trained models to disk
        
        Returns:
            Dictionary with saved file paths
        """
        logger.info("Saving trained models...")
        
        saved_files = {}
        
        # Save XGBoost
        xgb_path = self.output_dir / f'{self.symbol}_xgboost_model.joblib'
        joblib.dump(self.xgboost_model, xgb_path)
        saved_files['xgboost'] = str(xgb_path)
        logger.info(f"Saved XGBoost to {xgb_path}")
        
        # Save Random Forest
        rf_path = self.output_dir / f'{self.symbol}_random_forest_model.joblib'
        joblib.dump(self.rf_model, rf_path)
        saved_files['random_forest'] = str(rf_path)
        logger.info(f"Saved Random Forest to {rf_path}")
        
        # Save scaler
        scaler_path = self.output_dir / f'{self.symbol}_scaler.joblib'
        joblib.dump(self.scaler, scaler_path)
        saved_files['scaler'] = str(scaler_path)
        logger.info(f"Saved scaler to {scaler_path}")
        
        # Save metadata
        self.metadata['saved_files'] = saved_files
        metadata_path = self.output_dir / f'{self.symbol}_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        saved_files['metadata'] = str(metadata_path)
        logger.info(f"Saved metadata to {metadata_path}")
        
        return saved_files
    
    def generate_report(self, validation_results: Dict) -> str:
        """
        Generate training report
        
        Args:
            validation_results: Results from validate_models()
        
        Returns:
            Report as string
        """
        report = f"""
# ML MODEL TRAINING REPORT

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Symbol:** {self.symbol}
**Data Points:** {self.metadata['data_points']}
**Training Date:** {self.metadata['training_date']}

## Models Trained
- XGBoost
- Random Forest
- Ensemble (voting)

## Features ({len(self.feature_names)})
{', '.join(self.feature_names)}

## Training Results

### Model Performance
"""
        
        for model, perf in self.metadata['performance'].items():
            report += f"\n**{model.upper()}**\n"
            report += f"  - Accuracy: {perf['accuracy']:.4f}\n"
        
        report += f"""
### Cross-Validation Results
- XGBoost CV: {validation_results['xgboost_cv_mean']:.4f} (+/- {validation_results['xgboost_cv_std']:.4f})
- Random Forest CV: {validation_results['random_forest_cv_mean']:.4f} (+/- {validation_results['random_forest_cv_std']:.4f})

### Confusion Matrix (XGBoost on test set)
```
{np.array(validation_results['confusion_matrix'])}
```

## Data Split
- Training set: {len(self.X_train)} samples
- Test set: {len(self.X_test)} samples
- Test ratio: {len(self.X_test) / (len(self.X_train) + len(self.X_test)):.2%}

## Next Steps
1. Load trained models in prediction_engine.py
2. Run backtesting with trained models
3. Validate on paper trading
4. Deploy to live trading

---
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return report


def main():
    """Example: Train models on sample data"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # This is a template - real training will use actual historical data
    logger.info("ML Model Training Engine initialized")
    logger.info("To train models, call:")
    logger.info("  1. trainer = ModelTrainer('NIFTY50')")
    logger.info("  2. features, labels = trainer.generate_features(historical_data)")
    logger.info("  3. trainer.train_models(features, labels)")
    logger.info("  4. results = trainer.validate_models()")
    logger.info("  5. trainer.save_models()")


if __name__ == "__main__":
    main()
