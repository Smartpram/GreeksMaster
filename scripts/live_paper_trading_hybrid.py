"""
Live Paper Trading with Hybrid Data Source (Local CSV + Breeze API)
Uses pre-downloaded training data combined with live Breeze data for robust ML training

Features:
- Load historical training data from local CSV (reliable baseline)
- Supplement with live Breeze API data (recent market conditions)
- Train ML models on combined dataset
- Execute paper trades with consensus signals
- Comprehensive logging & reporting
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
from app.advanced_feature_engineering import AdvancedFeatureEngineer
from app.brokerage_fees import BrokerageFeeCalculator, BrokeragePlan, calculate_net_pnl

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

# Configure logging
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


class HybridDataCollector:
    """Combines local CSV data with live Breeze API data"""
    
    def __init__(self, api):
        self.api = api
        self.logger = logging.getLogger(__name__)
        self.training_data_dir = Path(__file__).parent / "data" / "training"
    
    def fetch_local_training_data(self, ticker_name, days_back=30):
        """
        Load historical training data from local CSV files
        
        Args:
            ticker_name: 'NIFTY50', 'BANKNIFTY', 'FINNIFTY'
            days_back: How many days to load
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Find the latest training file for this ticker
            pattern = f"{ticker_name}_training_data_*.csv"
            csv_files = sorted(self.training_data_dir.glob(pattern), reverse=True)
            
            if not csv_files:
                self.logger.warning(f"No local training data found for {ticker_name}")
                return None
            
            latest_file = csv_files[0]
            self.logger.info(f"[LOCAL DATA] Loading {ticker_name} from {latest_file.name}")
            
            # Load CSV
            df = pd.read_csv(latest_file)
            
            # Parse timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['datetime'] = df['timestamp']
            
            # Ensure numeric columns
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Filter to last N days
            cutoff_date = datetime.now() - timedelta(days=days_back)
            df = df[df['datetime'] >= cutoff_date]
            
            # Sort by datetime
            df = df.sort_values('datetime').reset_index(drop=True)
            
            self.logger.info(f"[LOCAL DATA] Loaded {len(df)} candles from {latest_file.name}")
            return df
        
        except Exception as e:
            self.logger.error(f"[LOCAL DATA ERROR] Failed to load {ticker_name}: {str(e)}")
            return None
    
    def fetch_live_breeze_data(self, stock_code, exchange='NSE', interval='minute', lookback_days=1):
        """
        Fetch recent live data from Breeze API
        
        Args:
            stock_code: Stock code without -I (e.g., 'NIFTY', 'BANKNIFTY')
            exchange: 'NSE'
            interval: 'minute', '5minute', etc.
            lookback_days: Days to fetch (1 day of recent data)
        
        Returns:
            DataFrame with recent OHLCV data
        """
        try:
            self.logger.info(f"[LIVE DATA] Fetching recent {stock_code} from Breeze")
            
            to_date = datetime.now()
            from_date = to_date - timedelta(days=lookback_days)
            
            from_date_str = from_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            to_date_str = to_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            result = self.api.get_historical_data(
                stock_code=stock_code,
                exchange_code=exchange,
                product_type="cash",
                interval=interval,
                from_date=from_date_str,
                to_date=to_date_str
            )
            
            if not result.get('success', False) or not result.get('data'):
                self.logger.warning(f"No live data from Breeze for {stock_code}")
                return None
            
            # Convert to DataFrame
            data = result['data']
            df = pd.DataFrame(data)
            
            # Parse datetime
            if 'date' in df.columns:
                df['datetime'] = pd.to_datetime(df['date'])
            elif 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'])
            else:
                self.logger.error(f"No date column in Breeze response")
                return None
            
            # Ensure numeric columns
            df.columns = df.columns.str.lower()
            for col in ['open', 'high', 'low', 'close']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Volume might be empty for indices
            if 'volume' in df.columns:
                df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)
            else:
                df['volume'] = 0
            
            # Drop rows with NaN in OHLC
            df = df.dropna(subset=['open', 'high', 'low', 'close'])
            
            # Sort by datetime
            df = df.sort_values('datetime').reset_index(drop=True)
            
            self.logger.info(f"[LIVE DATA] Got {len(df)} recent candles from Breeze")
            return df
        
        except Exception as e:
            self.logger.error(f"[LIVE DATA ERROR] Breeze fetch failed: {str(e)}")
            return None
    
    def combine_data(self, local_df, live_df):
        """
        Combine local training data with live Breeze data
        
        Args:
            local_df: Historical training data
            live_df: Recent live data
        
        Returns:
            Combined DataFrame
        """
        try:
            if local_df is None and live_df is None:
                return None
            
            if local_df is None:
                self.logger.info("[HYBRID] Using only live Breeze data")
                return live_df
            
            if live_df is None:
                self.logger.info("[HYBRID] Using only local training data")
                return local_df
            
            # Find cutoff: last timestamp in local data
            last_local_time = local_df['datetime'].max()
            
            # Filter live data: keep only data AFTER local data
            live_df_after = live_df[live_df['datetime'] > last_local_time].copy()
            
            if len(live_df_after) == 0:
                self.logger.info("[HYBRID] No new data from Breeze after local data cutoff")
                return local_df
            
            # Select only OHLCV columns
            cols_to_keep = ['datetime', 'open', 'high', 'low', 'close', 'volume']
            local_df_clean = local_df[cols_to_keep].copy()
            live_df_clean = live_df_after[cols_to_keep].copy()
            
            # Combine
            combined_df = pd.concat([local_df_clean, live_df_clean], ignore_index=True)
            combined_df = combined_df.sort_values('datetime').reset_index(drop=True)
            
            self.logger.info(f"[HYBRID] Combined: {len(local_df_clean)} local + {len(live_df_clean)} live = {len(combined_df)} total")
            return combined_df
        
        except Exception as e:
            self.logger.error(f"[HYBRID ERROR] Failed to combine data: {str(e)}")
            return local_df if local_df is not None else live_df


class FeatureEngineer:
    """Generate trading features from OHLCV data - Extended with Advanced Features"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.advanced_engineer = AdvancedFeatureEngineer()
    
    def generate_features(self, df, ticker=None, use_advanced=True):
        """
        Generate 30+ trading features + advanced features if enabled
        
        Args:
        - df: OHLCV DataFrame
        - ticker: Ticker symbol (for advanced features)
        - use_advanced: Include time-based, news sentiment, price action (default: True)
        
        Returns:
        - DataFrame with 30+ basic + 45+ advanced features (if enabled)
        """
        try:
            if df is None or len(df) == 0:
                return None
            
            self.logger.info(f"[FEATURES] Input: {len(df)} candles")
            
            features_df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']].copy()
            
            # === BASIC FEATURES (31 indicators) ===
            
            # Price-based features
            features_df['log_return'] = np.log(features_df['close'] / features_df['close'].shift(1))
            features_df['high_low_ratio'] = features_df['high'] / features_df['low']
            features_df['close_open_ratio'] = features_df['close'] / features_df['open']
            
            # Volume features
            features_df['volume_ma5'] = features_df['volume'].rolling(5).mean()
            features_df['volume_ratio'] = features_df['volume'] / (features_df['volume_ma5'] + 1)
            
            # Moving averages
            for period in [5, 10, 20, 50]:
                features_df[f'sma_{period}'] = features_df['close'].rolling(period).mean()
                features_df[f'ema_{period}'] = features_df['close'].ewm(span=period).mean()
            
            # RSI
            features_df['rsi_14'] = self._calculate_rsi(features_df['close'], 14)
            
            # MACD
            ema_12 = features_df['close'].ewm(span=12).mean()
            ema_26 = features_df['close'].ewm(span=26).mean()
            features_df['macd'] = ema_12 - ema_26
            features_df['macd_signal'] = features_df['macd'].ewm(span=9).mean()
            features_df['macd_diff'] = features_df['macd'] - features_df['macd_signal']
            
            # Bollinger Bands
            sma_20 = features_df['close'].rolling(20).mean()
            std_20 = features_df['close'].rolling(20).std()
            features_df['bb_upper'] = sma_20 + (std_20 * 2)
            features_df['bb_lower'] = sma_20 - (std_20 * 2)
            features_df['bb_width'] = features_df['bb_upper'] - features_df['bb_lower']
            
            # ATR (Average True Range)
            features_df['atr'] = self._calculate_atr(features_df, 14)
            
            # ADX
            features_df['adx'] = self._calculate_adx(features_df, 14)
            
            # Momentum
            features_df['momentum'] = features_df['close'] - features_df['close'].shift(10)
            
            # Rate of Change
            features_df['roc'] = features_df['close'].pct_change(10)
            
            # Stochastic
            features_df['stoch_k'], features_df['stoch_d'] = self._calculate_stochastic(features_df, 14)
            
            basic_feature_count = len(features_df.columns) - 6  # Excluding OHLCV
            
            # === ADVANCED FEATURES (45+) ===
            if use_advanced:
                self.logger.info(f"[FEATURES] Adding advanced features...")
                features_df = self.advanced_engineer.generate_all_advanced_features(
                    features_df, ticker=ticker, news_data=None
                )
            
            # Fill NaN from rolling calculations using forward fill then backward fill
            # Pandas 2.0+ uses bfill() and ffill() without method parameter
            features_df = features_df.bfill().ffill().fillna(0)
            
            # Drop rows that still have NaN
            features_df = features_df.dropna()
            
            total_features = len(features_df.columns) - 6  # Excluding OHLCV
            advanced_features = total_features - basic_feature_count if use_advanced else 0
            
            self.logger.info(f"[FEATURES] Generated {len(features_df)} rows with {total_features} total features")
            if use_advanced:
                self.logger.info(f"  - Basic: {basic_feature_count} indicators")
                self.logger.info(f"  - Advanced: {advanced_features} features")
            
            return features_df
        
        except Exception as e:
            self.logger.error(f"[FEATURES ERROR] Failed: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def _calculate_rsi(self, prices, period):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_atr(self, df, period):
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        return atr
    
    def _calculate_adx(self, df, period):
        high_diff = df['high'].diff()
        low_diff = -df['low'].diff()
        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
        tr = (df['high'] - df['low']).rolling(period).mean()
        plus_di = 100 * plus_dm.rolling(period).mean() / (tr + 1e-10)
        minus_di = 100 * minus_dm.rolling(period).mean() / (tr + 1e-10)
        di_diff = abs(plus_di - minus_di)
        adx = di_diff.rolling(period).mean()
        return adx
    
    def _calculate_stochastic(self, df, period):
        low_min = df['low'].rolling(period).min()
        high_max = df['high'].rolling(period).max()
        k = 100 * (df['close'] - low_min) / (high_max - low_min + 1e-10)
        d = k.rolling(3).mean()
        return k, d


class LiveModelTrainer:
    """Train ML models on features"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scaler = StandardScaler()
    
    def prepare_training_data(self, df, target_column='next_direction', lookahead=1):
        """Prepare data with target variable"""
        try:
            df_train = df.copy()
            
            # Create target
            df_train['next_close'] = df_train['close'].shift(-lookahead)
            df_train[target_column] = (df_train['next_close'] > df_train['close']).astype(int)
            
            # Drop last rows (no target)
            df_train = df_train.dropna()
            
            # Select feature columns
            exclude_cols = ['open', 'high', 'low', 'close', 'volume', 'datetime', 'next_close', target_column]
            feature_cols = [col for col in df_train.columns if col not in exclude_cols]
            
            X = df_train[feature_cols]
            y = df_train[target_column]
            
            self.logger.info(f"[TRAINING DATA] {len(X)} samples, {len(feature_cols)} features")
            return X, y, feature_cols
        
        except Exception as e:
            self.logger.error(f"[TRAINING DATA ERROR] {str(e)}")
            return None, None, None
    
    def train_models(self, X, y, ticker):
        """Train 3 ML models"""
        try:
            if X is None or len(X) == 0:
                self.logger.error(f"[TRAINING] No training data for {ticker}")
                return None, None, None, None
            
            self.logger.info(f"[TRAINING] Starting model training for {ticker}")
            
            # Filter to numeric columns only (drop string columns from time features)
            numeric_cols = X.select_dtypes(include=[np.number]).columns
            X = X[numeric_cols]
            self.logger.info(f"[TRAINING] Using {len(numeric_cols)} numeric features (dropped string columns)")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train models
            models = {
                'xgboost': XGBClassifier(n_estimators=100, learning_rate=0.1, random_state=42, verbosity=0),
                'rf': RandomForestClassifier(n_estimators=100, random_state=42),
                'gb': GradientBoostingClassifier(n_estimators=100, random_state=42)
            }
            
            results = {}
            for name, model in models.items():
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
                
                acc = accuracy_score(y_test, y_pred)
                prec = precision_score(y_test, y_pred, zero_division=0)
                rec = recall_score(y_test, y_pred, zero_division=0)
                f1 = f1_score(y_test, y_pred, zero_division=0)
                
                results[name] = {'accuracy': acc, 'precision': prec, 'recall': rec, 'f1': f1}
                self.logger.info(f"[TRAINED] {name}: Acc={acc:.3f}, Prec={prec:.3f}, Rec={rec:.3f}, F1={f1:.3f}")
            
            return models, results, X_test_scaled, y_test
        
        except Exception as e:
            self.logger.error(f"[TRAINING ERROR] {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None, None, None, None


class PaperTradingExecutor:
    """Execute paper trades with enhanced position tracking and fee accounting"""
    
    def __init__(self, capital_per_trade=10000, brokerage_plan=BrokeragePlan.IVALUE):
        self.logger = logging.getLogger(__name__)
        self.trades = []
        self.positions = []  # Track all positions
        self.open_positions = {}  # {ticker: [positions]}
        self.closed_positions = []
        self.capital_per_trade = capital_per_trade
        
        # Fee tracking
        self.fee_calculator = BrokerageFeeCalculator(plan=brokerage_plan)
        self.brokerage_plan = brokerage_plan
        self.total_fees = 0
        self.total_gross_pnl = 0
        self.total_net_pnl = 0
        self.daily_pnl = 0
    
    def generate_signals(self, features_df, models):
        """Generate consensus signals from models"""
        if models is None or features_df is None or len(features_df) == 0:
            return None
        
        try:
            # Get latest candle for reference
            latest = features_df.iloc[-1]
            current_price = latest['close']
            
            # Get feature columns (exclude OHLCV and datetime)
            exclude_cols = ['open', 'high', 'low', 'close', 'volume', 'datetime']
            feature_cols = [col for col in features_df.columns if col not in exclude_cols]
            
            # Filter to numeric columns only (matches training)
            X_temp = features_df[feature_cols]
            numeric_cols = X_temp.select_dtypes(include=[np.number]).columns.tolist()
            
            X_latest = features_df[numeric_cols].iloc[-1:].values
            
            # Get predictions from all models
            predictions = []
            for name, model in models.items():
                pred = model.predict(X_latest)[0]
                predictions.append(pred)
            
            # Consensus
            consensus = 1 if sum(predictions) > len(predictions) / 2 else 0
            confidence = max(sum(predictions), len(predictions) - sum(predictions)) / len(predictions)
            
            if confidence >= 0.6:  # High confidence
                signal = {
                    'action': 'BUY' if consensus == 1 else 'SELL',
                    'confidence': confidence,
                    'current_price': current_price,
                    'timestamp': latest['datetime']
                }
                self.logger.info(f"[SIGNAL] {signal['action']} @ Rs{current_price:.2f} (confidence: {confidence:.2f})")
                return signal
            
            return None
        
        except Exception as e:
            self.logger.error(f"[SIGNAL ERROR] {str(e)}")
            return None
    
    def execute_trade(self, ticker, signal, position_size=0.1):
        """Execute paper trade with position tracking"""
        try:
            entry_price = signal.get('current_price', 0)
            quantity = self.capital_per_trade / entry_price if entry_price > 0 else 0
            
            trade = {
                'timestamp': datetime.now(),
                'ticker': ticker,
                'action': signal['action'],
                'confidence': signal['confidence'],
                'position_size': position_size,
                'entry_price': entry_price,
                'quantity': quantity,
                'capital_allocated': self.capital_per_trade,
                'status': 'OPEN',
                'pnl': 0,
                'pnl_percent': 0
            }
            self.trades.append(trade)
            self.positions.append(trade)
            
            # Track by ticker
            if ticker not in self.open_positions:
                self.open_positions[ticker] = []
            self.open_positions[ticker].append(trade)
            
            self.logger.info(f"[POSITION] {ticker} {signal['action']} @ Rs{entry_price:.2f} | Qty: {quantity:.2f} | Conf: {signal['confidence']:.1%}")
            return trade
        
        except Exception as e:
            self.logger.error(f"[TRADE ERROR] {str(e)}")
            return None
    
    def close_position(self, ticker, trade_index, exit_price, exit_reason='timeout'):
        """Close a position and calculate P&L"""
        try:
            trade = self.trades[trade_index]
            entry_price = trade['entry_price']
            
            # Point values by ticker
            point_values = {
                'NIFTY50': 75,
                'BANKNIFTY': 25,
                'FINNIFTY': 40,
                'NIFTYNXT50': 20,
                'MIDCAPNIFTY': 50
            }
            point_value = point_values.get(ticker, 47)
            
            # Calculate P&L
            if trade['action'] == 'BUY':
                points_profit = exit_price - entry_price
            else:  # SELL
                points_profit = entry_price - exit_price
            
            # Gross P&L (before fees)
            gross_pnl = points_profit * point_value
            
            # Calculate fees (estimated for a round trip)
            quantity = 1  # For index contracts
            pnl_result = self.fee_calculator.calculate_pnl_after_fees(
                entry_price=entry_price,
                exit_price=exit_price,
                quantity=quantity
            )
            
            fees = pnl_result.get('total_fees', 0)
            net_pnl = gross_pnl - fees
            pnl_percent = (net_pnl / self.capital_per_trade) * 100
            
            # Update aggregates
            self.total_gross_pnl += gross_pnl
            self.total_fees += fees
            self.total_net_pnl += net_pnl
            
            # Update trade
            trade['status'] = 'CLOSED'
            trade['exit_price'] = exit_price
            trade['exit_reason'] = exit_reason
            trade['gross_pnl'] = gross_pnl
            trade['fees'] = fees
            trade['pnl'] = net_pnl
            trade['pnl_percent'] = pnl_percent
            trade['exit_time'] = datetime.now()
            
            # Move to closed
            if ticker in self.open_positions and trade in self.open_positions[ticker]:
                self.open_positions[ticker].remove(trade)
            self.closed_positions.append(trade)
            self.daily_pnl += net_pnl
            
            self.logger.info(f"[CLOSE] {ticker} @ Rs{exit_price:.2f} | Gross: Rs{gross_pnl:.0f} | Fees: Rs{fees:.0f} | Net PnL: Rs{net_pnl:.0f} ({pnl_percent:.1f}%) [{exit_reason}]")
            
            return trade
        
        except Exception as e:
            self.logger.error(f"[CLOSE ERROR] {str(e)}")
            return None
    
    def get_daily_summary(self):
        """Get daily trading summary"""
        closed_count = len(self.closed_positions)
        winning_trades = sum(1 for t in self.closed_positions if t['pnl'] > 0)
        losing_trades = sum(1 for t in self.closed_positions if t['pnl'] < 0)
        win_rate = (winning_trades / closed_count * 100) if closed_count > 0 else 0
        
        summary = {
            'total_trades': len(self.trades),
            'closed_trades': closed_count,
            'open_trades': len(self.positions) - closed_count,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate_percent': win_rate,
            'daily_pnl': self.daily_pnl,
            'trades': self.trades
        }
        
        return summary


class ReportGenerator:
    """Generate training and trading reports with position tracking"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_training_report(self, ticker, model_results, feature_cols):
        """Generate JSON training report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'ticker': ticker,
                'models': model_results,
                'feature_count': len(feature_cols),
                'features': feature_cols[:10]  # First 10
            }
            
            report_file = REPORT_DIR / f"training_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"[REPORT] Training report saved: {report_file.name}")
        
        except Exception as e:
            self.logger.error(f"[REPORT ERROR] {str(e)}")
    
    def generate_trading_report(self, ticker, executor):
        """Generate comprehensive JSON trading report with positions"""
        try:
            # Get closed trades for this ticker
            ticker_trades = [t for t in executor.closed_positions if t['ticker'] == ticker]
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'ticker': ticker,
                'total_trades': len(executor.trades),
                'closed_trades': len(ticker_trades),
                'open_trades': len([t for t in executor.trades if t['status'] == 'OPEN']),
                'winning_trades': len([t for t in ticker_trades if t['pnl'] > 0]),
                'losing_trades': len([t for t in ticker_trades if t['pnl'] < 0]),
                'daily_pnl': sum(t['pnl'] for t in ticker_trades),
                'trades': [
                    {
                        'timestamp': str(t['timestamp']),
                        'action': t['action'],
                        'confidence': t['confidence'],
                        'entry_price': t.get('entry_price', 0),
                        'exit_price': t.get('exit_price', None),
                        'quantity': t.get('quantity', 0),
                        'pnl': t.get('pnl', 0),
                        'pnl_percent': t.get('pnl_percent', 0),
                        'status': t.get('status', 'OPEN'),
                        'exit_reason': t.get('exit_reason', None)
                    } for t in executor.trades if t['ticker'] == ticker
                ]
            }
            
            report_file = REPORT_DIR / f"positions_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                # Convert numpy types to python types for JSON serialization
                json_str = json.dumps(report, default=str, indent=2)
                f.write(json_str)
            
            self.logger.info(f"[REPORT] Position report saved: {report_file.name}")
            
            # Log summary
            if report['closed_trades'] > 0:
                total_fees = sum(t.get('fees', 0) for t in executor.closed_positions if t['ticker'] == ticker)
                gross_pnl = sum(t.get('gross_pnl', 0) for t in executor.closed_positions if t['ticker'] == ticker)
                net_pnl = report['daily_pnl']
                self.logger.info(f"[{ticker}] Trades: {report['closed_trades']} | Wins: {report['winning_trades']} | Loss: {report['losing_trades']} | Gross: Rs{gross_pnl:.0f} | Fees: Rs{total_fees:.0f} | Net: Rs{net_pnl:.0f}")
        
        except Exception as e:
            self.logger.error(f"[REPORT ERROR] {str(e)}")


class LivePaperTradingPipeline:
    """Main orchestrator using hybrid data"""
    
    def __init__(self, tickers=None):
        self.tickers = tickers or [('NIFTY50', 'NIFTY'), ('BANKNIFTY', 'BANKNIFTY'), ('FINNIFTY', 'FINNIFTY')]
        self.logger = logging.getLogger(__name__)
        
        # Initialize API
        try:
            self.api = BreezeAPIService()
            auth_result = self.api.authenticate()
            if auth_result.get('success'):
                self.logger.info("[INIT] Breeze API authenticated")
            else:
                self.logger.error(f"[INIT] Auth failed: {auth_result.get('error')}")
                self.api = None
        except Exception as e:
            self.logger.error(f"[INIT] API init failed: {str(e)}")
            self.api = None
        
        self.data_collector = HybridDataCollector(self.api)
        self.feature_engineer = FeatureEngineer()
        self.model_trainer = LiveModelTrainer()
        self.paper_trader = PaperTradingExecutor()
        self.report_generator = ReportGenerator()
    
    def run(self):
        """Run pipeline"""
        self.logger.info(f"\n{'='*80}\nLIVE PAPER TRADING - HYBRID DATA\nStart: {datetime.now()}\n{'='*80}\n")
        
        trades_executed = []
        
        for ticker_name, stock_code in self.tickers:
            self.logger.info(f"\n[PIPELINE] Processing {ticker_name}...")
            
            try:
                # 1. Fetch local + live data
                local_df = self.data_collector.fetch_local_training_data(ticker_name, days_back=30)
                live_df = self.data_collector.fetch_live_breeze_data(stock_code, lookback_days=1)
                
                # 2. Combine data
                df = self.data_collector.combine_data(local_df, live_df)
                if df is None:
                    continue
                
                # 3. Generate features
                features_df = self.feature_engineer.generate_features(df)
                if features_df is None:
                    continue
                
                # 4. Train models
                X, y, feature_cols = self.model_trainer.prepare_training_data(features_df)
                models, model_results, X_test, y_test = self.model_trainer.train_models(X, y, ticker_name)
                if models is None:
                    continue
                
                # 5. Generate training report
                self.report_generator.generate_training_report(ticker_name, model_results, feature_cols)
                
                # 6. Generate signals and execute
                signal = self.paper_trader.generate_signals(features_df, models)
                if signal:
                    trade = self.paper_trader.execute_trade(ticker_name, signal, position_size=0.1)
                    
                    # 7. Simulate position exit (for demo: close after some variation)
                    # In real scenario, this would be in a separate position management loop
                    if trade and trade['entry_price'] > 0:
                        # Simulate exit with +15 or -10 points
                        point_values = {'NIFTY50': 75, 'BANKNIFTY': 25, 'FINNIFTY': 40, 'NIFTYNXT50': 20, 'MIDCAPNIFTY': 50}
                        pv = point_values.get(ticker_name, 47)
                        
                        # Randomly hit target (15 pts) or loss (10 pts)
                        if np.random.rand() > 0.5:
                            exit_price = trade['entry_price'] + (15 * pv / 100000)  # Convert to price points
                            reason = 'target'
                        else:
                            exit_price = trade['entry_price'] - (10 * pv / 100000)
                            reason = 'stop_loss'
                        
                        self.paper_trader.close_position(ticker_name, len(self.paper_trader.trades)-1, exit_price, reason)
                        
                        # Collect trade info
                        if self.paper_trader.trades:
                            last_trade = self.paper_trader.trades[-1]
                            trades_executed.append({
                                'ticker': ticker_name,
                                'action': last_trade.get('action', 'UNKNOWN'),
                                'entry_price': last_trade.get('entry_price', 0),
                                'pnl': last_trade.get('pnl', 0),
                                'status': last_trade.get('status', 'UNKNOWN')
                            })
                
                # 8. Generate comprehensive position report
                self.report_generator.generate_trading_report(ticker_name, self.paper_trader)
            
            except Exception as e:
                self.logger.error(f"[PIPELINE ERROR] {ticker_name}: {str(e)}", exc_info=True)
        
        self.logger.info(f"\n{'='*80}\nPIPELINE COMPLETE\nEnd: {datetime.now()}\n{'='*80}\n")
        self.logger.info(f"[SUCCESS] Paper trading completed")
        self.logger.info(f"[LOGS] Check: {LOG_DIR}")
        self.logger.info(f"[REPORTS] Check: {REPORT_DIR}")
        
        # Return summary
        return {
            'total_trades': len(trades_executed),
            'trades': trades_executed,
            'total_pnl': sum(t['pnl'] for t in trades_executed)
        }


def main():
    """Main entry point"""
    
    # Expanded ticker list - Multiple indices and stocks
    TICKERS = [
        # Major Indices
        ('NIFTY50', 'NIFTY'),
        ('BANKNIFTY', 'BANKNIFTY'),
        ('FINNIFTY', 'FINNIFTY'),
        ('NIFTYNXT50', 'NIFTYNXT50'),
        ('MIDCAPNIFTY', 'MIDCAPNIFTY'),
    ]
    
    pipeline = LivePaperTradingPipeline(tickers=TICKERS)
    pipeline.run()


if __name__ == '__main__':
    main()
