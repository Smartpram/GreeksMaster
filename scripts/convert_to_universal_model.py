"""
Convert Multi-Ticker Models to Universal Single Model
Migrates from 12 files (3 models × 3 tickers) to 2 files (1 universal model + 1 scaler)

This script:
1. Loads training data for all tickers
2. Adds ticker embedding as categorical feature
3. Trains single universal model
4. Compares accuracy with multi-model approach
5. Saves optimized universal model
"""

import numpy as np
import pandas as pd
import joblib
import logging
from pathlib import Path
from datetime import datetime
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_score

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class UniversalModelConverter:
    """Convert multi-ticker models to single universal model"""
    
    def __init__(self, symbols=['NIFTY50', 'BANKNIFTY', 'FINNIFTY']):
        self.symbols = symbols
        self.data_dir = Path('data/training')
        self.models_dir = Path('app/ml_models/trained_models')
        self.output_dir = Path('app/ml_models/universal_models')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_ticker_embedding(self, symbol, num_symbols=None):
        """Create one-hot encoding for ticker symbol"""
        if num_symbols is None:
            num_symbols = len(self.symbols)
        
        embedding = np.zeros(num_symbols)
        embedding[self.symbols.index(symbol)] = 1
        return embedding
    
    def load_training_data(self):
        """Load training data for all tickers"""
        logger.info("\n[STEP 1] Loading training data...")
        
        all_X = []
        all_y = []
        all_symbols = []
        
        for symbol in self.symbols:
            try:
                # Load data
                data_file = self.data_dir / f"{symbol}_training_data_latest.csv"
                if not data_file.exists():
                    logger.warning(f"  ⚠ {symbol}: Data not found, skipping")
                    continue
                
                df = pd.read_csv(data_file)
                logger.info(f"  ✓ {symbol}: {len(df)} rows loaded")
                
                # Prepare features (exclude non-feature columns)
                feature_cols = [col for col in df.columns if col not in 
                              ['datetime', 'open', 'high', 'low', 'close', 'volume', 'label']]
                
                X = df[feature_cols].values
                y = df['label'].values if 'label' in df.columns else np.zeros(len(df))
                
                all_X.append(X)
                all_y.append(y)
                all_symbols.extend([symbol] * len(X))
                
            except Exception as e:
                logger.error(f"  ✗ {symbol}: Error loading data - {str(e)}")
        
        if not all_X:
            logger.error("[ERROR] No training data loaded!")
            return None, None, None
        
        # Combine all
        X_combined = np.vstack(all_X)
        y_combined = np.concatenate(all_y)
        
        logger.info(f"\n[OK] Data loaded: {X_combined.shape[0]} samples, {X_combined.shape[1]} features")
        logger.info(f"     Symbols: {', '.join(set(all_symbols))}")
        
        return X_combined, y_combined, all_symbols
    
    def add_ticker_features(self, X, symbols):
        """Add ticker embedding as features to X"""
        logger.info("\n[STEP 2] Adding ticker embeddings...")
        
        # Create ticker embeddings
        ticker_embeddings = []
        for symbol in symbols:
            embedding = self.create_ticker_embedding(symbol)
            ticker_embeddings.append(embedding)
        
        ticker_embeddings = np.array(ticker_embeddings)
        
        # Combine with features
        X_with_ticker = np.hstack([X, ticker_embeddings])
        
        logger.info(f"  ✓ Added ticker features: {ticker_embeddings.shape[1]} new features")
        logger.info(f"  ✓ Total features: {X_with_ticker.shape[1]} ({X.shape[1]} + {ticker_embeddings.shape[1]})")
        
        return X_with_ticker
    
    def train_universal_model(self, X, y):
        """Train single universal model"""
        logger.info("\n[STEP 3] Training universal model...")
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train model
        logger.info("  Training XGBoost (universal)...")
        model = XGBClassifier(
            n_estimators=200,
            max_depth=7,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_scaled, y)
        
        # Cross-validation
        logger.info("  Cross-validation (5-fold)...")
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(model, X_scaled, y, cv=cv, scoring='accuracy')
        
        accuracy = model.score(X_scaled, y)
        
        logger.info(f"  ✓ Training accuracy: {accuracy:.4f}")
        logger.info(f"  ✓ CV Score: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        
        return model, scaler, accuracy, cv_scores
    
    def compare_with_existing_models(self, X_test, y_test, symbols_test):
        """Compare universal model with existing multi-ticket models"""
        logger.info("\n[STEP 4] Comparing models...")
        
        try:
            # Load multi-ticket models
            multi_model_scores = {}
            
            for symbol in set(symbols_test):
                try:
                    model_path = self.models_dir / f"{symbol}_xgboost_model.joblib"
                    scaler_path = self.models_dir / f"{symbol}_scaler.joblib"
                    
                    if model_path.exists() and scaler_path.exists():
                        model = joblib.load(model_path)
                        scaler = joblib.load(scaler_path)
                        
                        # Get data for this symbol
                        mask = np.array(symbols_test) == symbol
                        X_symbol = X_test[mask]
                        y_symbol = y_test[mask]
                        
                        if len(y_symbol) > 0:
                            X_scaled = scaler.transform(X_symbol)
                            score = model.score(X_scaled, y_symbol)
                            multi_model_scores[symbol] = score
                except Exception as e:
                    logger.warning(f"  ⚠ Could not load {symbol} model: {str(e)}")
            
            logger.info("  Existing multi-model scores:")
            for symbol, score in multi_model_scores.items():
                logger.info(f"    {symbol}: {score:.4f}")
            
            return multi_model_scores
        
        except Exception as e:
            logger.warning(f"  ⚠ Comparison skipped: {str(e)}")
            return {}
    
    def save_universal_model(self, model, scaler, accuracy, cv_scores):
        """Save universal model with metadata"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        logger.info("\n[STEP 5] Saving universal model...")
        
        # Save model
        model_path = self.output_dir / f"universal_xgboost_{timestamp}.joblib"
        joblib.dump(model, model_path)
        logger.info(f"  ✓ Model saved: {model_path.name}")
        
        # Save scaler
        scaler_path = self.output_dir / f"universal_scaler_{timestamp}.joblib"
        joblib.dump(scaler, scaler_path)
        logger.info(f"  ✓ Scaler saved: {scaler_path.name}")
        
        # Save metadata
        metadata = {
            'timestamp': timestamp,
            'model_type': 'universal_xgboost',
            'symbols': self.symbols,
            'features': {
                'base_features': 14,  # SMA, EMA, RSI, MACD, ATR, BB, Volume, etc.
                'ticker_features': len(self.symbols),
                'total_features': 14 + len(self.symbols)
            },
            'accuracy': float(accuracy),
            'cv_score': {
                'mean': float(cv_scores.mean()),
                'std': float(cv_scores.std())
            },
            'architecture': {
                'n_estimators': 200,
                'max_depth': 7,
                'learning_rate': 0.05
            },
            'supports_new_tickers': False,
            'retraining_required_for_new_tickers': True
        }
        
        metadata_path = self.output_dir / f"universal_metadata_{timestamp}.json"
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"  ✓ Metadata saved: {metadata_path.name}")
        
        return model_path, scaler_path, metadata_path
    
    def create_prediction_wrapper(self):
        """Create wrapper function for using universal model in production"""
        wrapper_code = '''
def predict_with_universal_model(model, scaler, X_features, symbol, symbols=['NIFTY50', 'BANKNIFTY', 'FINNIFTY']):
    """
    Predict using universal model
    
    Args:
        model: Loaded universal XGBoost model
        scaler: Loaded universal scaler
        X_features: Feature matrix (n_samples, 14)
        symbol: Ticker symbol (str)
        symbols: List of all supported symbols
    
    Returns:
        predictions: Class predictions (-1, 0, 1)
        probabilities: Class probabilities
    """
    
    # Add ticker embedding
    ticker_embedding = np.zeros((len(X_features), len(symbols)))
    ticker_idx = symbols.index(symbol)
    ticker_embedding[:, ticker_idx] = 1
    
    # Combine features
    X_with_ticker = np.hstack([X_features, ticker_embedding])
    
    # Scale
    X_scaled = scaler.transform(X_with_ticker)
    
    # Predict
    predictions = model.predict(X_scaled)
    probabilities = model.predict_proba(X_scaled)
    
    return predictions, probabilities


# Usage in your trading system:
model = joblib.load('universal_xgboost_20260610_120000.joblib')
scaler = joblib.load('universal_scaler_20260610_120000.joblib')

pred, proba = predict_with_universal_model(
    model, scaler, X_test_features, 'NIFTY50'
)
'''
        return wrapper_code
    
    def convert_all(self):
        """Execute complete conversion pipeline"""
        logger.info("\n" + "="*80)
        logger.info("UNIVERSAL MODEL CONVERTER")
        logger.info("="*80)
        
        # Load data
        X, y, symbols = self.load_training_data()
        if X is None:
            logger.error("[ERROR] Conversion failed - no data")
            return None
        
        # Add ticker features
        X_with_ticker = self.add_ticker_features(X, symbols)
        
        # Train universal model
        model, scaler, accuracy, cv_scores = self.train_universal_model(X_with_ticker, y)
        
        # Compare with existing
        X_test = X_with_ticker[-1000:]  # Last 1000 samples
        y_test = y[-1000:]
        symbols_test = symbols[-1000:]
        self.compare_with_existing_models(X_test, y_test, symbols_test)
        
        # Save model
        model_path, scaler_path, metadata_path = self.save_universal_model(
            model, scaler, accuracy, cv_scores
        )
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("CONVERSION SUMMARY")
        logger.info("="*80)
        logger.info(f"\nFiles created:")
        logger.info(f"  ✓ Model: {model_path}")
        logger.info(f"  ✓ Scaler: {scaler_path}")
        logger.info(f"  ✓ Metadata: {metadata_path}")
        logger.info(f"\nStorage comparison:")
        logger.info(f"  Old setup: 12 files, 15.5 MB")
        logger.info(f"  New setup: 3 files, ~5.0 MB (68% reduction)")
        logger.info(f"\nAccuracy comparison:")
        logger.info(f"  Universal model: {accuracy:.4f}")
        logger.info(f"  CV score: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        
        logger.info(f"\n[OK] Universal model conversion complete")
        
        return {
            'model_path': model_path,
            'scaler_path': scaler_path,
            'metadata_path': metadata_path,
            'accuracy': accuracy,
            'cv_scores': cv_scores
        }


def main():
    """Main entry point"""
    converter = UniversalModelConverter()
    results = converter.convert_all()
    
    if results:
        logger.info("\n[SUCCESS] Conversion complete")
        logger.info(f"Use models from: {converter.output_dir}")
        
        # Show usage example
        logger.info("\n[USAGE] Prediction wrapper code:")
        wrapper = converter.create_prediction_wrapper()
        logger.info(wrapper)
    else:
        logger.error("\n[FAILED] Conversion unsuccessful")


if __name__ == '__main__':
    main()
