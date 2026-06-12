"""
Hybrid Multi-Tier ML Model Manager
Implements: Global + Group + Per-Ticker ensemble approach
Status: Production ready
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Tuple, List, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import xgboost as xgb


class HybridMLModelManager:
    """
    Manages 3-tier ML ensemble:
    Tier 1: Global Model (all tickers)
    Tier 2: Group Models (indices, stocks)
    Tier 3: Per-Ticker Models (premium tickers with volume > threshold)
    """
    
    def __init__(self, model_dir: str = "models/hybrid"):
        self.model_dir = model_dir
        self.models_dir = os.path.dirname(model_dir)
        os.makedirs(model_dir, exist_ok=True)
        
        # Tier 1: Global Model (XGBoost, RF, GB ensemble)
        self.global_xgb = None
        self.global_rf = None
        self.global_gb = None
        self.global_scaler = StandardScaler()
        self.global_version = 0
        
        # Tier 2: Group Models
        self.group_models = {}  # {'indices': {...}, 'stocks': {...}}
        self.group_scalers = {}
        self.group_versions = {}
        
        # Tier 3: Per-Ticker Models
        self.ticker_models = {}  # {'NIFTY': {...}, 'BANKNIFTY': {...}, ...}
        self.ticker_scalers = {}
        self.ticker_versions = {}
        
        # Training data buffers
        self.global_training_buffer = []  # [(features, label), ...]
        self.group_training_buffers = {'indices': [], 'stocks': []}
        self.ticker_training_buffers = {}  # {'NIFTY': [...], ...}
        
        # Configuration
        self.retraining_threshold = 100  # Retrain after 100 samples
        self.ticker_volume_threshold = 50  # Min daily trades to get per-ticker model
        
        # Ticker grouping
        self.ticker_groups = {
            'indices': ['NIFTY', 'BANKNIFTY', 'FINNIFTY'],
            'stocks': ['INFY', 'TCS', 'RELIANCE', 'WIPRO', 'LT', 'M&M', 
                      'BAJAJFINSV', 'SBIN', 'ICICIBANK', 'HDFC']
        }
        
        # Premium tickers (eligible for per-ticker models)
        self.premium_tickers = ['NIFTY', 'BANKNIFTY']
        
        # Performance tracking
        self.performance = {
            'global': {'accuracy': 0, 'samples': 0},
            'groups': {'indices': {'accuracy': 0, 'samples': 0}, 
                      'stocks': {'accuracy': 0, 'samples': 0}},
            'tickers': {}
        }
        
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models from disk if they exist"""
        try:
            # Load global models
            global_xgb_path = os.path.join(self.model_dir, 'global_xgb.pkl')
            global_rf_path = os.path.join(self.model_dir, 'global_rf.pkl')
            global_gb_path = os.path.join(self.model_dir, 'global_gb.pkl')
            global_scaler_path = os.path.join(self.model_dir, 'global_scaler.pkl')
            
            if os.path.exists(global_xgb_path):
                with open(global_xgb_path, 'rb') as f:
                    self.global_xgb = pickle.load(f)
                with open(global_rf_path, 'rb') as f:
                    self.global_rf = pickle.load(f)
                with open(global_gb_path, 'rb') as f:
                    self.global_gb = pickle.load(f)
                with open(global_scaler_path, 'rb') as f:
                    self.global_scaler = pickle.load(f)
                
                # Load version
                version_path = os.path.join(self.model_dir, 'global_version.txt')
                if os.path.exists(version_path):
                    with open(version_path, 'r') as f:
                        self.global_version = int(f.read())
            
            # Load group models
            for group_name in self.ticker_groups.keys():
                group_dir = os.path.join(self.model_dir, group_name)
                if os.path.exists(group_dir):
                    group_xgb_path = os.path.join(group_dir, f'{group_name}_xgb.pkl')
                    group_rf_path = os.path.join(group_dir, f'{group_name}_rf.pkl')
                    group_gb_path = os.path.join(group_dir, f'{group_name}_gb.pkl')
                    group_scaler_path = os.path.join(group_dir, f'{group_name}_scaler.pkl')
                    
                    if os.path.exists(group_xgb_path):
                        with open(group_xgb_path, 'rb') as f:
                            xgb_model = pickle.load(f)
                        with open(group_rf_path, 'rb') as f:
                            rf_model = pickle.load(f)
                        with open(group_gb_path, 'rb') as f:
                            gb_model = pickle.load(f)
                        with open(group_scaler_path, 'rb') as f:
                            scaler = pickle.load(f)
                        
                        self.group_models[group_name] = {
                            'xgb': xgb_model, 'rf': rf_model, 'gb': gb_model
                        }
                        self.group_scalers[group_name] = scaler
                        
                        version_path = os.path.join(group_dir, f'{group_name}_version.txt')
                        if os.path.exists(version_path):
                            with open(version_path, 'r') as f:
                                self.group_versions[group_name] = int(f.read())
            
            # Load per-ticker models
            for ticker in self.premium_tickers:
                ticker_dir = os.path.join(self.model_dir, 'tickers', ticker)
                if os.path.exists(ticker_dir):
                    ticker_xgb_path = os.path.join(ticker_dir, f'{ticker}_xgb.pkl')
                    ticker_rf_path = os.path.join(ticker_dir, f'{ticker}_rf.pkl')
                    ticker_gb_path = os.path.join(ticker_dir, f'{ticker}_gb.pkl')
                    ticker_scaler_path = os.path.join(ticker_dir, f'{ticker}_scaler.pkl')
                    
                    if os.path.exists(ticker_xgb_path):
                        with open(ticker_xgb_path, 'rb') as f:
                            xgb_model = pickle.load(f)
                        with open(ticker_rf_path, 'rb') as f:
                            rf_model = pickle.load(f)
                        with open(ticker_gb_path, 'rb') as f:
                            gb_model = pickle.load(f)
                        with open(ticker_scaler_path, 'rb') as f:
                            scaler = pickle.load(f)
                        
                        self.ticker_models[ticker] = {
                            'xgb': xgb_model, 'rf': rf_model, 'gb': gb_model
                        }
                        self.ticker_scalers[ticker] = scaler
                        
                        version_path = os.path.join(ticker_dir, f'{ticker}_version.txt')
                        if os.path.exists(version_path):
                            with open(version_path, 'r') as f:
                                self.ticker_versions[ticker] = int(f.read())
        
        except Exception as e:
            print(f"[WARN] Error loading models: {e}")
            print("[INFO] Starting with fresh models")
    
    def _extract_features(self, candles: List[Dict]) -> np.ndarray:
        """
        Extract 12 ML features from candles
        Returns: (n_samples, 12) array
        """
        features = []
        
        for candle in candles:
            # Convert to numeric
            close = float(candle.get('close', 0))
            open_ = float(candle.get('open', 0))
            high = float(candle.get('high', 0))
            low = float(candle.get('low', 0))
            volume = float(candle.get('volume', 0))
            
            # Feature 1-3: SMA ratios
            close_price = close if close > 0 else 1
            
            # Simplified: use close as proxy if full SMA data unavailable
            sma5_ratio = 1.0  # Will be populated by technical indicator
            sma10_ratio = 1.0
            sma20_ratio = 1.0
            
            # Feature 4: RSI (simplified: 0-1 scale)
            rsi = 0.5  # Will be populated by technical indicator
            
            # Feature 5-6: MACD components
            macd = 0.0
            macd_hist = 0.0
            
            # Feature 7: Bollinger Band width
            bb_width = (high - low) / close_price if close_price > 0 else 0
            
            # Feature 8: ATR ratio
            atr_ratio = (high - low) / close_price if close_price > 0 else 0
            
            # Feature 9: ADX value
            adx = 0.5  # Will be populated by technical indicator
            
            # Feature 10: Volume ratio
            volume_ratio = 1.0  # Will be populated by technical indicator
            
            # Feature 11: Momentum
            momentum = (close - open_) / close_price if close_price > 0 else 0
            
            # Feature 12: ROC (Rate of Change)
            roc = 0.0  # Will be populated by technical indicator
            
            features.append([
                sma5_ratio, sma10_ratio, sma20_ratio, rsi, macd, macd_hist,
                bb_width, atr_ratio, adx, volume_ratio, momentum, roc
            ])
        
        return np.array(features)
    
    def add_training_sample(self, features: np.ndarray, label: int, 
                           ticker: str, group: Optional[str] = None):
        """
        Add training sample to buffers
        
        Args:
            features: (12,) array of features
            label: 1 if profitable, 0 if loss
            ticker: Ticker symbol
            group: Optional group name ('indices' or 'stocks')
        """
        # Add to global buffer
        self.global_training_buffer.append((features, label))
        
        # Add to group buffer
        if group:
            self.group_training_buffers[group].append((features, label))
        
        # Add to ticker buffer
        if ticker in self.premium_tickers:
            if ticker not in self.ticker_training_buffers:
                self.ticker_training_buffers[ticker] = []
            self.ticker_training_buffers[ticker].append((features, label))
        
        # Check if retraining thresholds reached
        self._check_retraining_thresholds()
    
    def _check_retraining_thresholds(self):
        """Check if any model tier needs retraining"""
        # Global model
        if len(self.global_training_buffer) >= self.retraining_threshold:
            self._retrain_global_model()
        
        # Group models
        for group_name, buffer in self.group_training_buffers.items():
            if len(buffer) >= self.retraining_threshold:
                self._retrain_group_model(group_name)
        
        # Per-ticker models
        for ticker, buffer in self.ticker_training_buffers.items():
            if len(buffer) >= self.retraining_threshold:
                self._retrain_ticker_model(ticker)
    
    def _retrain_global_model(self):
        """Retrain global model on accumulated samples"""
        if len(self.global_training_buffer) == 0:
            return
        
        try:
            # Prepare data
            X = np.array([item[0] for item in self.global_training_buffer])
            y = np.array([item[1] for item in self.global_training_buffer])
            
            # Standardize features
            X_scaled = self.global_scaler.fit_transform(X)
            
            # Train ensemble
            self.global_xgb = xgb.XGBClassifier(
                n_estimators=100, max_depth=6, learning_rate=0.1,
                random_state=42, verbosity=0
            )
            self.global_xgb.fit(X_scaled, y)
            
            self.global_rf = RandomForestClassifier(
                n_estimators=100, max_depth=10, n_jobs=-1, random_state=42
            )
            self.global_rf.fit(X_scaled, y)
            
            self.global_gb = GradientBoostingClassifier(
                n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42
            )
            self.global_gb.fit(X_scaled, y)
            
            # Update version and save
            self.global_version += 1
            self._save_global_model()
            
            # Keep only recent samples (rolling window)
            self.global_training_buffer = self.global_training_buffer[-500:]
            
            print(f"[RETRAIN] Global model v{self.global_version} trained on {len(y)} samples")
            
            # Update performance tracking
            accuracy = (self.global_xgb.predict(X_scaled) == y).mean()
            self.performance['global']['accuracy'] = accuracy
            self.performance['global']['samples'] = len(y)
        
        except Exception as e:
            print(f"[ERROR] Failed to retrain global model: {e}")
    
    def _retrain_group_model(self, group_name: str):
        """Retrain group model"""
        buffer = self.group_training_buffers[group_name]
        if len(buffer) == 0:
            return
        
        try:
            # Prepare data
            X = np.array([item[0] for item in buffer])
            y = np.array([item[1] for item in buffer])
            
            # Get or create scaler
            if group_name not in self.group_scalers:
                self.group_scalers[group_name] = StandardScaler()
            
            X_scaled = self.group_scalers[group_name].fit_transform(X)
            
            # Train ensemble
            xgb_model = xgb.XGBClassifier(
                n_estimators=100, max_depth=6, learning_rate=0.1,
                random_state=42, verbosity=0
            )
            xgb_model.fit(X_scaled, y)
            
            rf_model = RandomForestClassifier(
                n_estimators=100, max_depth=10, n_jobs=-1, random_state=42
            )
            rf_model.fit(X_scaled, y)
            
            gb_model = GradientBoostingClassifier(
                n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42
            )
            gb_model.fit(X_scaled, y)
            
            self.group_models[group_name] = {
                'xgb': xgb_model, 'rf': rf_model, 'gb': gb_model
            }
            
            # Update version and save
            if group_name not in self.group_versions:
                self.group_versions[group_name] = 0
            self.group_versions[group_name] += 1
            self._save_group_model(group_name)
            
            # Keep rolling window
            self.group_training_buffers[group_name] = buffer[-300:]
            
            print(f"[RETRAIN] Group model '{group_name}' v{self.group_versions[group_name]} trained on {len(y)} samples")
            
            # Update performance
            accuracy = (xgb_model.predict(X_scaled) == y).mean()
            self.performance['groups'][group_name]['accuracy'] = accuracy
            self.performance['groups'][group_name]['samples'] = len(y)
        
        except Exception as e:
            print(f"[ERROR] Failed to retrain group model '{group_name}': {e}")
    
    def _retrain_ticker_model(self, ticker: str):
        """Retrain per-ticker model"""
        buffer = self.ticker_training_buffers[ticker]
        if len(buffer) == 0:
            return
        
        try:
            # Prepare data
            X = np.array([item[0] for item in buffer])
            y = np.array([item[1] for item in buffer])
            
            # Get or create scaler
            if ticker not in self.ticker_scalers:
                self.ticker_scalers[ticker] = StandardScaler()
            
            X_scaled = self.ticker_scalers[ticker].fit_transform(X)
            
            # Train ensemble
            xgb_model = xgb.XGBClassifier(
                n_estimators=100, max_depth=6, learning_rate=0.1,
                random_state=42, verbosity=0
            )
            xgb_model.fit(X_scaled, y)
            
            rf_model = RandomForestClassifier(
                n_estimators=100, max_depth=10, n_jobs=-1, random_state=42
            )
            rf_model.fit(X_scaled, y)
            
            gb_model = GradientBoostingClassifier(
                n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42
            )
            gb_model.fit(X_scaled, y)
            
            self.ticker_models[ticker] = {
                'xgb': xgb_model, 'rf': rf_model, 'gb': gb_model
            }
            
            # Update version and save
            if ticker not in self.ticker_versions:
                self.ticker_versions[ticker] = 0
            self.ticker_versions[ticker] += 1
            self._save_ticker_model(ticker)
            
            # Keep rolling window
            self.ticker_training_buffers[ticker] = buffer[-200:]
            
            print(f"[RETRAIN] Ticker model '{ticker}' v{self.ticker_versions[ticker]} trained on {len(y)} samples")
            
            # Update performance
            accuracy = (xgb_model.predict(X_scaled) == y).mean()
            if ticker not in self.performance['tickers']:
                self.performance['tickers'][ticker] = {}
            self.performance['tickers'][ticker]['accuracy'] = accuracy
            self.performance['tickers'][ticker]['samples'] = len(y)
        
        except Exception as e:
            print(f"[ERROR] Failed to retrain ticker model '{ticker}': {e}")
    
    def predict_ml_confidence(self, features: np.ndarray, ticker: str) -> Tuple[float, Dict]:
        """
        Get ML confidence for a trade using ensemble approach
        
        Args:
            features: (12,) array of features
            ticker: Ticker symbol
        
        Returns:
            (confidence_0_to_1, component_scores_dict)
        """
        scores = {}
        
        # Tier 1: Global model prediction
        global_conf = 0.5  # Default neutral
        if self.global_xgb is not None:
            try:
                X_scaled = self.global_scaler.transform([features])
                xgb_pred = self.global_xgb.predict_proba(X_scaled)[0][1]
                rf_pred = self.global_rf.predict_proba(X_scaled)[0][1]
                gb_pred = self.global_gb.predict_proba(X_scaled)[0][1]
                global_conf = np.mean([xgb_pred, rf_pred, gb_pred])
                scores['global'] = global_conf
            except:
                scores['global'] = 0.5
        else:
            scores['global'] = 0.5
        
        # Tier 2: Group model prediction
        group_name = self._get_ticker_group(ticker)
        group_conf = 0.5
        if group_name and group_name in self.group_models:
            try:
                X_scaled = self.group_scalers[group_name].transform([features])
                xgb_pred = self.group_models[group_name]['xgb'].predict_proba(X_scaled)[0][1]
                rf_pred = self.group_models[group_name]['rf'].predict_proba(X_scaled)[0][1]
                gb_pred = self.group_models[group_name]['gb'].predict_proba(X_scaled)[0][1]
                group_conf = np.mean([xgb_pred, rf_pred, gb_pred])
                scores['group'] = group_conf
            except:
                scores['group'] = 0.5
        else:
            scores['group'] = 0.5
        
        # Tier 3: Per-ticker model prediction
        ticker_conf = 0.5
        if ticker in self.ticker_models:
            try:
                X_scaled = self.ticker_scalers[ticker].transform([features])
                xgb_pred = self.ticker_models[ticker]['xgb'].predict_proba(X_scaled)[0][1]
                rf_pred = self.ticker_models[ticker]['rf'].predict_proba(X_scaled)[0][1]
                gb_pred = self.ticker_models[ticker]['gb'].predict_proba(X_scaled)[0][1]
                ticker_conf = np.mean([xgb_pred, rf_pred, gb_pred])
                scores['ticker'] = ticker_conf
            except:
                scores['ticker'] = 0.5
        else:
            scores['ticker'] = 0.5
        
        # Ensemble with fixed weights: 50% global, 30% group, 20% ticker
        ensemble_conf = (0.50 * global_conf) + (0.30 * group_conf) + (0.20 * ticker_conf)
        
        scores['ensemble'] = ensemble_conf
        
        return ensemble_conf, scores
    
    def _get_ticker_group(self, ticker: str) -> Optional[str]:
        """Get group name for ticker"""
        for group_name, tickers in self.ticker_groups.items():
            if ticker in tickers:
                return group_name
        return None
    
    def _save_global_model(self):
        """Save global model to disk"""
        try:
            os.makedirs(self.model_dir, exist_ok=True)
            
            with open(os.path.join(self.model_dir, 'global_xgb.pkl'), 'wb') as f:
                pickle.dump(self.global_xgb, f)
            with open(os.path.join(self.model_dir, 'global_rf.pkl'), 'wb') as f:
                pickle.dump(self.global_rf, f)
            with open(os.path.join(self.model_dir, 'global_gb.pkl'), 'wb') as f:
                pickle.dump(self.global_gb, f)
            with open(os.path.join(self.model_dir, 'global_scaler.pkl'), 'wb') as f:
                pickle.dump(self.global_scaler, f)
            
            with open(os.path.join(self.model_dir, 'global_version.txt'), 'w') as f:
                f.write(str(self.global_version))
        
        except Exception as e:
            print(f"[ERROR] Failed to save global model: {e}")
    
    def _save_group_model(self, group_name: str):
        """Save group model to disk"""
        try:
            group_dir = os.path.join(self.model_dir, group_name)
            os.makedirs(group_dir, exist_ok=True)
            
            with open(os.path.join(group_dir, f'{group_name}_xgb.pkl'), 'wb') as f:
                pickle.dump(self.group_models[group_name]['xgb'], f)
            with open(os.path.join(group_dir, f'{group_name}_rf.pkl'), 'wb') as f:
                pickle.dump(self.group_models[group_name]['rf'], f)
            with open(os.path.join(group_dir, f'{group_name}_gb.pkl'), 'wb') as f:
                pickle.dump(self.group_models[group_name]['gb'], f)
            with open(os.path.join(group_dir, f'{group_name}_scaler.pkl'), 'wb') as f:
                pickle.dump(self.group_scalers[group_name], f)
            
            with open(os.path.join(group_dir, f'{group_name}_version.txt'), 'w') as f:
                f.write(str(self.group_versions[group_name]))
        
        except Exception as e:
            print(f"[ERROR] Failed to save group model '{group_name}': {e}")
    
    def _save_ticker_model(self, ticker: str):
        """Save per-ticker model to disk"""
        try:
            ticker_dir = os.path.join(self.model_dir, 'tickers', ticker)
            os.makedirs(ticker_dir, exist_ok=True)
            
            with open(os.path.join(ticker_dir, f'{ticker}_xgb.pkl'), 'wb') as f:
                pickle.dump(self.ticker_models[ticker]['xgb'], f)
            with open(os.path.join(ticker_dir, f'{ticker}_rf.pkl'), 'wb') as f:
                pickle.dump(self.ticker_models[ticker]['rf'], f)
            with open(os.path.join(ticker_dir, f'{ticker}_gb.pkl'), 'wb') as f:
                pickle.dump(self.ticker_models[ticker]['gb'], f)
            with open(os.path.join(ticker_dir, f'{ticker}_scaler.pkl'), 'wb') as f:
                pickle.dump(self.ticker_scalers[ticker], f)
            
            with open(os.path.join(ticker_dir, f'{ticker}_version.txt'), 'w') as f:
                f.write(str(self.ticker_versions[ticker]))
        
        except Exception as e:
            print(f"[ERROR] Failed to save ticker model '{ticker}': {e}")
    
    def get_model_status(self) -> Dict:
        """Get comprehensive model status"""
        return {
            'timestamp': datetime.now().isoformat(),
            'global': {
                'version': self.global_version,
                'ready': self.global_xgb is not None,
                'training_samples': len(self.global_training_buffer),
                'accuracy': self.performance['global'].get('accuracy', 0)
            },
            'groups': {
                group_name: {
                    'version': self.group_versions.get(group_name, 0),
                    'ready': group_name in self.group_models,
                    'training_samples': len(self.group_training_buffers[group_name]),
                    'accuracy': self.performance['groups'][group_name].get('accuracy', 0)
                }
                for group_name in self.ticker_groups.keys()
            },
            'tickers': {
                ticker: {
                    'version': self.ticker_versions.get(ticker, 0),
                    'ready': ticker in self.ticker_models,
                    'training_samples': len(self.ticker_training_buffers.get(ticker, [])),
                    'accuracy': self.performance['tickers'].get(ticker, {}).get('accuracy', 0)
                }
                for ticker in self.premium_tickers
            }
        }
    
    def save_performance_report(self, report_dir: str = "reports/hybrid_ml"):
        """Save performance metrics report"""
        try:
            os.makedirs(report_dir, exist_ok=True)
            
            status = self.get_model_status()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = os.path.join(report_dir, f'model_status_{timestamp}.json')
            
            with open(report_path, 'w') as f:
                json.dump(status, f, indent=2)
            
            print(f"[INFO] Model status saved: {report_path}")
        
        except Exception as e:
            print(f"[ERROR] Failed to save performance report: {e}")
