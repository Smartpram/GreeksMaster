"""
Live Paper Trading with Real-Time Model Retraining
Fetches live data from Breeze API, trains ML models, executes paper trad            # Ensure OHLCV columns are lowercase and numeric
            df.columns = df.columns.str.lower()
            
            # Convert OHLCV columns to numeric (they may be strings from API)
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Drop rows with NaN values
            df = df.dropna(subset=numeric_cols)
            
            # Sort by datetime
            df = df.sort_values('datetime')
            
            # Reset index
            df = df.reset_index(drop=True)
            
            self.logger.info(f"[LIVE DATA] Fetched {len(df)} candles for {ticker}")verything

Features:
- Live data fetching from Breeze API (1-min candles)
- Real-time model retraining (daily or hourly)
- Paper trading execution
- Comprehensive logging & reporting
- Support for multiple tickers
- Configurable execution frequency
"""

import os
import sys
import json
import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# ML Libraries
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Breeze API
sys.path.insert(0, str(Path(__file__).parent))
from app.services.breeze_api import BreezeAPIService

# Load environment
load_dotenv()

# Setup logging
LOG_DIR = Path(__file__).parent / "logs" / "live_trading"
LOG_DIR.mkdir(parents=True, exist_ok=True)

REPORT_DIR = Path(__file__).parent / "reports" / "live_trading"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_DIR = Path(__file__).parent / "app" / "ml_models" / "live"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = Path(__file__).parent / "data" / "live"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Logging configuration
log_file = LOG_DIR / f"paper_trading_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LiveDataCollector:
    """Fetches live data from Breeze API"""
    
    def __init__(self, api):
        self.api = api
        self.logger = logging.getLogger(__name__)
    
    def fetch_live_data(self, ticker, interval='minute', lookback_days=30):
        """
        Fetch live minute candle data from Breeze API
        
        Args:
            ticker: Stock symbol (e.g., 'NIFTY-I', 'BANKNIFTY-I')
            interval: 'minute', '5minute', '30minute', 'day'
            lookback_days: Number of days of historical data
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            self.logger.info(f"[LIVE DATA] Fetching {ticker} {interval} candles (last {lookback_days} days)")
            
            # Calculate date range in ISO 8601 format
            to_date = datetime.now()
            from_date = to_date - timedelta(days=lookback_days)
            
            from_date_str = from_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            to_date_str = to_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            # Fetch data using Breeze API
            # Stock code: remove -I suffix if present
            stock_code = ticker.replace('-I', '')
            
            result = self.api.get_historical_data(
                stock_code=stock_code,
                exchange_code="NSE",
                product_type="cash",
                interval=interval,
                from_date=from_date_str,
                to_date=to_date_str
            )
            
            if not result.get('success', False) or not result.get('data'):
                self.logger.warning(f"No data received for {ticker}")
                return None
            
            # Convert to DataFrame
            data = result['data']
            df = pd.DataFrame(data)
            
            # Ensure datetime column exists and is properly formatted
            # Breeze API returns 'date' field
            if 'date' in df.columns:
                df['datetime'] = pd.to_datetime(df['date'])
            elif 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'])
            else:
                # Try to find any date-like column
                date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
                if date_cols:
                    df['datetime'] = pd.to_datetime(df[date_cols[0]])
                else:
                    self.logger.error(f"No date column found in response for {ticker}. Columns: {list(df.columns)}")
                    return None
            
            # Ensure OHLCV columns are lowercase
            df.columns = df.columns.str.lower()
            
            # Debug: Log columns and first row
            self.logger.info(f"[DEBUG] DataFrame columns: {list(df.columns)}")
            if len(df) > 0:
                self.logger.info(f"[DEBUG] First row: open={df.iloc[0]['open']}, volume={df.iloc[0]['volume']}")
            
            # Convert OHLCV columns to numeric (they may be strings from API)
            # For indices like NIFTY-I, volume might be empty/NaN, so handle it specially
            for col in ['open', 'high', 'low', 'close']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Volume might be missing or empty for indices - fill with 0
            if 'volume' in df.columns:
                df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)
            else:
                df['volume'] = 0
            
            # Drop rows with NaN in OHLC (but NOT volume, since it can be 0)
            df = df.dropna(subset=['open', 'high', 'low', 'close'])
            
            # Sort by datetime
            df = df.sort_values('datetime')
            
            # Reset index
            df = df.reset_index(drop=True)
            
            self.logger.info(f"[LIVE DATA] Fetched {len(df)} candles for {ticker}")
            return df
        
        except Exception as e:
            self.logger.error(f"[LIVE DATA ERROR] Failed to fetch {ticker}: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None


class FeatureEngineer:
    """Generate features for ML models"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_features(self, df):
        """Generate trading features"""
        try:
            self.logger.info(f"[FEATURES] Input DF shape: {df.shape}, Columns: {list(df.columns)}")
            
            features_df = df.copy()
            
            # Price-based features
            features_df['log_return'] = np.log(features_df['close'] / features_df['close'].shift(1))
            features_df['high_low_ratio'] = features_df['high'] / features_df['low']
            features_df['close_open_ratio'] = features_df['close'] / features_df['open']
            
            # Volume features
            features_df['volume_ma5'] = features_df['volume'].rolling(5).mean()
            features_df['volume_ratio'] = features_df['volume'] / features_df['volume_ma5']
            
            # Moving averages
            for period in [5, 10, 20, 50]:
                features_df[f'sma_{period}'] = features_df['close'].rolling(period).mean()
                features_df[f'ema_{period}'] = features_df['close'].ewm(span=period).mean()
            
            # RSI (Relative Strength Index)
            features_df['rsi_14'] = self._calculate_rsi(features_df['close'], 14)
            
            # MACD
            features_df['macd'], features_df['macd_signal'], features_df['macd_diff'] = \
                self._calculate_macd(features_df['close'])
            
            # Bollinger Bands
            features_df['bb_upper'], features_df['bb_middle'], features_df['bb_lower'] = \
                self._calculate_bollinger_bands(features_df['close'], 20, 2)
            
            # Volatility
            features_df['volatility_20'] = features_df['log_return'].rolling(20).std()
            
            # Momentum
            features_df['momentum_10'] = features_df['close'] - features_df['close'].shift(10)
            
            # Fill NaN values from rolling calculations
            # Select only numeric columns for filling
            numeric_cols = features_df.select_dtypes(include=[np.number]).columns
            features_df[numeric_cols] = features_df[numeric_cols].bfill().ffill()
            
            # Check if we still have any NaN in numeric columns
            remaining_nan = features_df[numeric_cols].isna().sum().sum()
            if remaining_nan > 0:
                self.logger.warning(f"[FEATURES] {remaining_nan} NaN values remaining in {len(numeric_cols)} numeric columns")
                # Drop rows with NaN only in numeric columns
                features_df = features_df.dropna(subset=numeric_cols)
            
            self.logger.info(f"[FEATURES] Generated {len(features_df.columns)} features for {len(features_df)} candles")
            return features_df
        
        except Exception as e:
            self.logger.error(f"[FEATURES ERROR] Failed to generate features: {str(e)}")
            return None
    
    @staticmethod
    def _calculate_rsi(prices, period=14):
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def _calculate_macd(prices, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        macd_diff = macd - macd_signal
        return macd, macd_signal, macd_diff
    
    @staticmethod
    def _calculate_bollinger_bands(prices, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        sma = prices.rolling(period).mean()
        std = prices.rolling(period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower


class LiveModelTrainer:
    """Trains ML models with live data"""
    
    def __init__(self, output_dir=MODEL_DIR):
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        self.scaler = StandardScaler()
    
    def prepare_training_data(self, df, target_column='next_direction', lookahead=1):
        """
        Prepare training data with target variable
        
        Args:
            df: Features dataframe
            target_column: Name of target column to create
            lookahead: Bars ahead to predict
        
        Returns:
            X, y, feature_names
        """
        df_train = df.copy()
        
        # Create target: predict if price goes up (1) or down (0)
        df_train['next_close'] = df_train['close'].shift(-lookahead)
        df_train[target_column] = (df_train['next_close'] > df_train['close']).astype(int)
        
        # Check NaN counts before dropping
        nan_cols = df_train.columns[df_train.isna().any()].tolist()
        nan_counts = {col: df_train[col].isna().sum() for col in nan_cols if nan_cols}
        self.logger.info(f"[TRAINING DATA] NaN columns: {nan_counts}")
        
        # Remove rows with NaN (need to allow some NaN from recent candles)
        df_train = df_train.dropna()
        
        self.logger.info(f"[TRAINING DATA] After dropna: {len(df_train)} rows")
        
        # Select feature columns
        exclude_cols = ['open', 'high', 'low', 'close', 'volume', 'datetime', 
                       'next_close', target_column]
        feature_cols = [col for col in df_train.columns if col not in exclude_cols]
        
        X = df_train[feature_cols]
        y = df_train[target_column]
        
        self.logger.info(f"[TRAINING DATA] {len(X)} samples, {len(feature_cols)} features")
        return X, y, feature_cols
    
    def train_models(self, X, y, ticker, test_size=0.2):
        """Train multiple ML models"""
        try:
            self.logger.info(f"[TRAINING] Starting model training for {ticker}")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            results = {}
            models = {}
            
            # XGBoost
            self.logger.info("[TRAINING] Training XGBoost...")
            xgb_model = XGBClassifier(
                n_estimators=100,
                max_depth=7,
                learning_rate=0.1,
                random_state=42,
                eval_metric='logloss'
            )
            xgb_model.fit(X_train_scaled, y_train)
            xgb_pred = xgb_model.predict(X_test_scaled)
            results['xgboost'] = {
                'accuracy': accuracy_score(y_test, xgb_pred),
                'precision': precision_score(y_test, xgb_pred, zero_division=0),
                'recall': recall_score(y_test, xgb_pred, zero_division=0),
                'f1': f1_score(y_test, xgb_pred, zero_division=0)
            }
            models['xgboost'] = xgb_model
            self.logger.info(f"  XGBoost Accuracy: {results['xgboost']['accuracy']:.4f}")
            
            # Random Forest
            self.logger.info("[TRAINING] Training Random Forest...")
            rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            rf_model.fit(X_train_scaled, y_train)
            rf_pred = rf_model.predict(X_test_scaled)
            results['random_forest'] = {
                'accuracy': accuracy_score(y_test, rf_pred),
                'precision': precision_score(y_test, rf_pred, zero_division=0),
                'recall': recall_score(y_test, rf_pred, zero_division=0),
                'f1': f1_score(y_test, rf_pred, zero_division=0)
            }
            models['random_forest'] = rf_model
            self.logger.info(f"  Random Forest Accuracy: {results['random_forest']['accuracy']:.4f}")
            
            # Gradient Boosting
            self.logger.info("[TRAINING] Training Gradient Boosting...")
            gb_model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=7,
                learning_rate=0.1,
                random_state=42
            )
            gb_model.fit(X_train_scaled, y_train)
            gb_pred = gb_model.predict(X_test_scaled)
            results['gradient_boosting'] = {
                'accuracy': accuracy_score(y_test, gb_pred),
                'precision': precision_score(y_test, gb_pred, zero_division=0),
                'recall': recall_score(y_test, gb_pred, zero_division=0),
                'f1': f1_score(y_test, gb_pred, zero_division=0)
            }
            models['gradient_boosting'] = gb_model
            self.logger.info(f"  Gradient Boosting Accuracy: {results['gradient_boosting']['accuracy']:.4f}")
            
            # Save models
            for model_name, model in models.items():
                model_path = self.output_dir / f"{ticker}_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
                self.logger.info(f"[TRAINING] ✓ Saved {model_name} model: {model_path}")
            
            # Save scaler
            scaler_path = self.output_dir / f"{ticker}_scaler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            
            return models, results, X_test_scaled, y_test
        
        except Exception as e:
            self.logger.error(f"[TRAINING ERROR] Failed to train models: {str(e)}")
            return None, None, None, None


class PaperTradingExecutor:
    """Executes paper trades based on model signals"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.trades = []
        self.portfolio_value = 100000  # Initial capital
        self.cash = self.portfolio_value
        self.positions = {}
    
    def generate_signals(self, df, models):
        """Generate trading signals from models"""
        try:
            latest_row = df.iloc[-1]
            
            # Prepare features
            exclude_cols = ['open', 'high', 'low', 'close', 'volume', 'datetime']
            feature_cols = [col for col in df.columns if col not in exclude_cols]
            X_latest = df[feature_cols].iloc[-1:].values
            
            # Get predictions from all models
            signals = {}
            for model_name, model in models.items():
                pred = model.predict(X_latest)[0]
                prob = model.predict_proba(X_latest)[0]
                signals[model_name] = {
                    'prediction': pred,
                    'probability': max(prob),
                    'confidence': max(prob)
                }
            
            # Consensus signal (majority vote)
            votes = [s['prediction'] for s in signals.values()]
            consensus = 1 if sum(votes) > len(votes) / 2 else 0
            avg_confidence = np.mean([s['confidence'] for s in signals.values()])
            
            return {
                'timestamp': latest_row['datetime'],
                'price': latest_row['close'],
                'signals': signals,
                'consensus': consensus,
                'confidence': avg_confidence
            }
        
        except Exception as e:
            self.logger.error(f"[SIGNALS ERROR] Failed to generate signals: {str(e)}")
            return None
    
    def execute_trade(self, ticker, signal, position_size=0.1):
        """Execute paper trade"""
        try:
            if signal['confidence'] < 0.55:  # Low confidence threshold
                self.logger.debug(f"[TRADE] Low confidence {signal['confidence']:.2%}, skipping")
                return None
            
            trade_amount = self.portfolio_value * position_size
            
            if signal['consensus'] == 1:  # BUY signal
                action = 'BUY'
                quantity = int(trade_amount / signal['price'])
            else:  # SELL signal
                action = 'SELL'
                quantity = int(trade_amount / signal['price'])
            
            trade = {
                'timestamp': signal['timestamp'],
                'ticker': ticker,
                'action': action,
                'quantity': quantity,
                'price': signal['price'],
                'amount': quantity * signal['price'],
                'confidence': signal['confidence'],
                'consensus': signal['consensus']
            }
            
            self.trades.append(trade)
            self.logger.info(f"[TRADE] {action} {quantity} {ticker} @ {signal['price']} (confidence: {signal['confidence']:.2%})")
            
            return trade
        
        except Exception as e:
            self.logger.error(f"[TRADE ERROR] Failed to execute trade: {str(e)}")
            return None


class ReportGenerator:
    """Generates comprehensive reports"""
    
    def __init__(self, output_dir=REPORT_DIR):
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
    
    def generate_training_report(self, ticker, model_results, feature_names):
        """Generate model training report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'ticker': ticker,
                'model_results': model_results,
                'num_features': len(feature_names),
                'best_model': max(model_results.items(), key=lambda x: x[1]['accuracy'])[0],
                'best_accuracy': max([r['accuracy'] for r in model_results.values()])
            }
            
            # Save JSON
            report_file = self.output_dir / f"training_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"[REPORT] ✓ Training report saved: {report_file}")
            
            # Print summary
            self.logger.info(f"\n[TRAINING SUMMARY]")
            for model_name, metrics in model_results.items():
                self.logger.info(f"  {model_name}:")
                self.logger.info(f"    Accuracy: {metrics['accuracy']:.4f}")
                self.logger.info(f"    Precision: {metrics['precision']:.4f}")
                self.logger.info(f"    Recall: {metrics['recall']:.4f}")
                self.logger.info(f"    F1: {metrics['f1']:.4f}")
            
            return report_file
        
        except Exception as e:
            self.logger.error(f"[REPORT ERROR] Failed to generate training report: {str(e)}")
            return None
    
    def generate_trading_report(self, ticker, trades):
        """Generate paper trading report"""
        try:
            if not trades:
                self.logger.warning("[REPORT] No trades to report")
                return None
            
            trades_df = pd.DataFrame(trades)
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'ticker': ticker,
                'total_trades': len(trades),
                'buy_trades': len(trades_df[trades_df['action'] == 'BUY']),
                'sell_trades': len(trades_df[trades_df['action'] == 'SELL']),
                'total_volume': trades_df['quantity'].sum(),
                'avg_confidence': trades_df['confidence'].mean(),
                'high_confidence_trades': len(trades_df[trades_df['confidence'] > 0.7]),
                'first_trade': trades_df['timestamp'].min().isoformat(),
                'last_trade': trades_df['timestamp'].max().isoformat()
            }
            
            # Save JSON
            report_file = self.output_dir / f"trades_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Save CSV
            csv_file = self.output_dir / f"trades_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            trades_df.to_csv(csv_file, index=False)
            
            self.logger.info(f"[REPORT] ✓ Trading report saved: {report_file}")
            self.logger.info(f"[REPORT] ✓ Trades CSV saved: {csv_file}")
            
            # Print summary
            self.logger.info(f"\n[TRADING SUMMARY]")
            self.logger.info(f"  Total Trades: {report['total_trades']}")
            self.logger.info(f"  Buy Trades: {report['buy_trades']}")
            self.logger.info(f"  Sell Trades: {report['sell_trades']}")
            self.logger.info(f"  Total Volume: {report['total_volume']}")
            self.logger.info(f"  Average Confidence: {report['avg_confidence']:.2%}")
            
            return report_file
        
        except Exception as e:
            self.logger.error(f"[REPORT ERROR] Failed to generate trading report: {str(e)}")
            return None


class LivePaperTradingPipeline:
    """Main orchestrator"""
    
    def __init__(self, tickers=None, execution_frequency='hourly'):
        """
        Args:
            tickers: List of tickers to trade (default: ['NIFTY-I', 'BANKNIFTY-I'])
            execution_frequency: 'hourly', 'daily', or integer (minutes)
        """
        self.tickers = tickers or ['NIFTY-I', 'BANKNIFTY-I']
        self.execution_frequency = execution_frequency
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        try:
            # Initialize Breeze API
            self.api = BreezeAPIService()
            
            # Authenticate using session token
            auth_result = self.api.authenticate()
            if auth_result.get('success'):
                self.logger.info("[INIT] ✓ Breeze API authenticated successfully")
            else:
                self.logger.error(f"[INIT ERROR] Authentication failed: {auth_result.get('error', 'Unknown error')}")
                self.api = None
        
        except Exception as e:
            self.logger.error(f"[INIT ERROR] Failed to initialize Breeze API: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.api = None
        
        self.data_collector = LiveDataCollector(self.api)
        self.feature_engineer = FeatureEngineer()
        self.model_trainer = LiveModelTrainer()
        self.paper_trader = PaperTradingExecutor()
        self.report_generator = ReportGenerator()
    
    def run(self):
        """Run the complete pipeline"""
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"LIVE PAPER TRADING WITH MODEL RETRAINING")
        self.logger.info(f"Start Time: {datetime.now()}")
        self.logger.info(f"Tickers: {self.tickers}")
        self.logger.info(f"Execution Frequency: {self.execution_frequency}")
        self.logger.info(f"{'='*80}\n")
        
        for ticker in self.tickers:
            self.logger.info(f"\n[PIPELINE] Processing {ticker}...")
            
            try:
                # 1. Fetch live data
                df = self.data_collector.fetch_live_data(ticker, interval='minute', lookback_days=30)
                if df is None:
                    continue
                
                # 2. Generate features
                features_df = self.feature_engineer.generate_features(df)
                if features_df is None:
                    continue
                
                # 3. Train models
                X, y, feature_cols = self.model_trainer.prepare_training_data(features_df)
                models, model_results, X_test, y_test = self.model_trainer.train_models(X, y, ticker)
                if models is None:
                    continue
                
                # 4. Generate training report
                self.report_generator.generate_training_report(ticker, model_results, feature_cols)
                
                # 5. Generate trading signals and execute
                signal = self.paper_trader.generate_signals(features_df, models)
                if signal:
                    trade = self.paper_trader.execute_trade(ticker, signal, position_size=0.1)
                
                # 6. Generate trading report
                if self.paper_trader.trades:
                    self.report_generator.generate_trading_report(ticker, self.paper_trader.trades)
            
            except Exception as e:
                self.logger.error(f"[PIPELINE ERROR] Failed to process {ticker}: {str(e)}", exc_info=True)
        
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"PIPELINE COMPLETE")
        self.logger.info(f"End Time: {datetime.now()}")
        self.logger.info(f"{'='*80}\n")


def main():
    """Main entry point"""
    
    # Configuration
    TICKERS = [
        'NIFTY-I',      # Nifty 50 Index
        'BANKNIFTY-I',  # Bank Nifty Index
        'FINNIFTY-I',   # Financial Nifty Index
    ]
    
    EXECUTION_FREQUENCY = 'hourly'  # Can be 'hourly', 'daily', or integer (minutes)
    
    # Create and run pipeline
    pipeline = LivePaperTradingPipeline(
        tickers=TICKERS,
        execution_frequency=EXECUTION_FREQUENCY
    )
    
    pipeline.run()
    
    logger.info("\n[SUCCESS] Live paper trading pipeline completed")
    logger.info(f"[LOGS] Check: {LOG_DIR}")
    logger.info(f"[REPORTS] Check: {REPORT_DIR}")


if __name__ == '__main__':
    main()
