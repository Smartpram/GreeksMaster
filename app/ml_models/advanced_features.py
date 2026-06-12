"""
Advanced Features & Strategy Optimization Engine
Adaptive position sizing, ensemble improvements, market regime detection
"""

import numpy as np
import pandas as pd
from datetime import datetime
import logging
from pathlib import Path
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AdvancedFeatureGenerator:
    """Generate advanced features for ML models"""
    
    @staticmethod
    def generate_microstructure_features(df, lookback=20):
        """Market microstructure features"""
        features = pd.DataFrame(index=df.index)
        
        # Bid-ask spread proxy (high-low as proxy)
        features['Spread_Ratio'] = (df['high'] - df['low']) / df['close']
        
        # Volume pressure
        features['Up_Volume'] = np.where(df['close'] > df['open'], df['volume'], 0)
        features['Down_Volume'] = np.where(df['close'] < df['open'], df['volume'], 0)
        features['Volume_Pressure'] = (features['Up_Volume'] - features['Down_Volume']) / df['volume']
        
        # Order flow imbalance
        features['OFI'] = features['Volume_Pressure'].rolling(lookback).sum()
        
        # VWAP (Volume Weighted Average Price)
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        features['VWAP'] = (typical_price * df['volume']).rolling(lookback).sum() / df['volume'].rolling(lookback).sum()
        
        return features
    
    @staticmethod
    def generate_regime_features(df, lookback=20):
        """Market regime detection features"""
        features = pd.DataFrame(index=df.index)
        
        # Volatility regimes
        returns = df['close'].pct_change()
        features['High_Vol_Regime'] = (returns.rolling(lookback).std() > returns.rolling(100).std().median()).astype(int)
        
        # Trend regimes
        sma_short = df['close'].rolling(10).mean()
        sma_long = df['close'].rolling(50).mean()
        features['Uptrend_Regime'] = (sma_short > sma_long).astype(int)
        
        # Range regimes
        high_20 = df['high'].rolling(lookback).max()
        low_20 = df['low'].rolling(lookback).min()
        features['Range_Upper'] = high_20
        features['Range_Lower'] = low_20
        features['Range_Middle'] = (high_20 + low_20) / 2
        features['In_Range'] = ((df['close'] > low_20) & (df['close'] < high_20)).astype(int)
        
        # Squeeze detection (Bollinger Bands width)
        bb_width = 20 * df['close'].pct_change().rolling(20).std()
        features['BB_Squeeze'] = (bb_width < bb_width.rolling(100).quantile(0.25)).astype(int)
        
        return features
    
    @staticmethod
    def generate_correlation_features(symbols_data, lookback=20):
        """Cross-symbol correlation features"""
        features = {}
        
        close_prices = {}
        for symbol, df in symbols_data.items():
            close_prices[symbol] = df['close']
        
        close_df = pd.DataFrame(close_prices)
        
        for symbol in symbols_data.keys():
            corr_features = pd.DataFrame(index=close_df.index)
            
            # Correlation with other symbols
            for other_symbol in symbols_data.keys():
                if other_symbol != symbol:
                    corr = close_df[symbol].rolling(lookback).corr(close_df[other_symbol])
                    corr_features[f'Corr_{other_symbol}'] = corr
            
            features[symbol] = corr_features
        
        return features
    
    @staticmethod
    def generate_cyclical_features(df):
        """Time-based cyclical features"""
        features = pd.DataFrame(index=df.index)
        
        if 'datetime' not in df.columns:
            return features
        
        dt = pd.to_datetime(df['datetime'])
        
        # Hour of day (cyclical encoding)
        hour = dt.dt.hour
        features['Hour_Sin'] = np.sin(2 * np.pi * hour / 24)
        features['Hour_Cos'] = np.cos(2 * np.pi * hour / 24)
        
        # Day of week (cyclical encoding)
        dow = dt.dt.dayofweek
        features['DayOfWeek_Sin'] = np.sin(2 * np.pi * dow / 7)
        features['DayOfWeek_Cos'] = np.cos(2 * np.pi * dow / 7)
        
        # Month (cyclical encoding)
        month = dt.dt.month
        features['Month_Sin'] = np.sin(2 * np.pi * month / 12)
        features['Month_Cos'] = np.cos(2 * np.pi * month / 12)
        
        return features
    
    @staticmethod
    def generate_momentum_cascade(df, periods=[5, 10, 20, 50]):
        """Multi-period momentum features"""
        features = pd.DataFrame(index=df.index)
        
        for period in periods:
            features[f'Momentum_{period}'] = df['close'].pct_change(period)
            features[f'ROC_{period}'] = (df['close'] - df['close'].shift(period)) / df['close'].shift(period)
        
        return features


class EnsembleOptimizer:
    """Optimize ensemble model predictions"""
    
    def __init__(self, models, weights=None):
        self.models = models
        self.weights = weights or {name: 1/len(models) for name in models.keys()}
    
    def optimize_weights(self, X_test, y_test, optimization_method='accuracy'):
        """Optimize ensemble weights using test data"""
        from scipy.optimize import minimize
        
        logger.info("Optimizing ensemble weights...")
        
        def objective(weights):
            weighted_pred = np.zeros(len(y_test))
            for i, (name, model) in enumerate(self.models.items()):
                pred = model.predict(X_test)
                weighted_pred += weights[i] * pred
            
            if optimization_method == 'accuracy':
                accuracy = np.mean(np.sign(weighted_pred) == np.sign(y_test))
                return -accuracy  # Negative for minimization
            else:
                return np.mean((weighted_pred - y_test) ** 2)
        
        # Initial weights
        initial_weights = np.array(list(self.weights.values()))
        
        # Constraints: weights sum to 1
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        bounds = [(0, 1) for _ in self.models]
        
        # Optimize
        result = minimize(objective, initial_weights, method='SLSQP', 
                         bounds=bounds, constraints=constraints)
        
        optimized_weights = result.x
        self.weights = {name: w for name, w in zip(self.models.keys(), optimized_weights)}
        
        logger.info(f"[OK] Optimized weights: {self.weights}")
        return self.weights
    
    def predict_weighted(self, X):
        """Generate weighted ensemble predictions"""
        weighted_pred = np.zeros(len(X))
        
        for name, model in self.models.items():
            pred = model.predict(X)
            weighted_pred += self.weights[name] * pred
        
        return np.sign(weighted_pred)
    
    def predict_proba_weighted(self, X):
        """Generate weighted probability predictions"""
        weighted_proba = np.zeros((len(X), 3))
        
        for name, model in self.models.items():
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(X)
                if proba.shape[1] == 3:
                    weighted_proba += self.weights[name] * proba
                elif proba.shape[1] == 2:
                    # Convert binary to 3-class
                    proba_3class = np.zeros((len(X), 3))
                    proba_3class[:, 1] = proba[:, 1]  # UP
                    proba_3class[:, 2] = proba[:, 0]  # DOWN
                    weighted_proba += self.weights[name] * proba_3class
        
        return weighted_proba


class AdaptivePositionSizer:
    """Dynamically adjust position size based on market conditions"""
    
    def __init__(self, base_size=1.0, max_size=5.0, min_size=0.1):
        self.base_size = base_size
        self.max_size = max_size
        self.min_size = min_size
    
    def calculate_position_size(self, signal_confidence, volatility, drawdown, regime):
        """
        Calculate adaptive position size
        
        Args:
            signal_confidence: Model confidence (0-1)
            volatility: Current market volatility
            drawdown: Current drawdown (0-1)
            regime: Market regime ('trending', 'ranging', 'volatile')
        """
        size = self.base_size
        
        # Confidence adjustment
        if signal_confidence < 0.5:
            size *= 0.5
        elif signal_confidence > 0.7:
            size *= 1.2
        
        # Volatility adjustment
        if volatility > 0.03:  # High volatility
            size *= 0.7
        elif volatility < 0.01:  # Low volatility
            size *= 1.1
        
        # Drawdown adjustment (reduce during drawdown)
        if drawdown > 0.1:  # >10% drawdown
            size *= 0.5
        elif drawdown > 0.2:  # >20% drawdown
            size *= 0.25
        
        # Regime adjustment
        regime_multipliers = {
            'trending': 1.2,
            'ranging': 0.8,
            'volatile': 0.6
        }
        size *= regime_multipliers.get(regime, 1.0)
        
        # Apply bounds
        size = max(self.min_size, min(self.max_size, size))
        
        return size
    
    def generate_size_levels(self):
        """Generate size levels for risk management"""
        return {
            'small': self.base_size * 0.5,
            'normal': self.base_size,
            'large': self.base_size * 1.5,
            'max': self.max_size,
            'min': self.min_size
        }


class StrategyOptimizer:
    """Optimize strategy parameters"""
    
    def __init__(self):
        self.optimization_history = []
    
    def optimize_sma_periods(self, df, test_periods=None):
        """Optimize SMA crossover periods"""
        if test_periods is None:
            test_periods = [(5, 20), (10, 30), (20, 50), (20, 200)]
        
        logger.info("Optimizing SMA periods...")
        results = []
        
        for short, long in test_periods:
            sma_short = df['close'].rolling(short).mean()
            sma_long = df['close'].rolling(long).mean()
            
            signals = np.where(sma_short > sma_long, 1, -1)
            signal_changes = np.diff(signals)
            
            win_count = np.sum(signal_changes != 0)
            win_rate = self._calculate_win_rate(df, signals)
            
            results.append({
                'short_period': short,
                'long_period': long,
                'win_rate': win_rate,
                'signal_count': win_count
            })
        
        best = max(results, key=lambda x: x['win_rate'])
        logger.info(f"[OK] Best SMA: {best['short_period']}/{best['long_period']} (WR: {best['win_rate']:.2%})")
        
        return results
    
    def optimize_rsi_thresholds(self, df, test_thresholds=None):
        """Optimize RSI thresholds"""
        if test_thresholds is None:
            test_thresholds = [(20, 80), (25, 75), (30, 70), (35, 65)]
        
        logger.info("Optimizing RSI thresholds...")
        results = []
        
        rsi = self._calculate_rsi(df['close'], 14)
        
        for oversold, overbought in test_thresholds:
            signals = np.where(rsi < oversold, 1, np.where(rsi > overbought, -1, 0))
            win_rate = self._calculate_win_rate(df, signals)
            
            results.append({
                'oversold': oversold,
                'overbought': overbought,
                'win_rate': win_rate
            })
        
        best = max(results, key=lambda x: x['win_rate'])
        logger.info(f"[OK] Best RSI: {best['oversold']}/{best['overbought']} (WR: {best['win_rate']:.2%})")
        
        return results
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_win_rate(self, df, signals):
        """Calculate win rate from signals"""
        if len(signals) < 2:
            return 0.5
        
        returns = df['close'].pct_change()
        signal_returns = returns * signals
        wins = np.sum(signal_returns > 0)
        total = np.sum(signal_returns != 0)
        
        return wins / total if total > 0 else 0.5


def main():
    """Test advanced features"""
    logger.info("\n[ADVANCED FEATURES ENGINE] Starting...")
    
    # Example data
    dates = pd.date_range('2024-01-01', periods=1000, freq='1H')
    df = pd.DataFrame({
        'datetime': dates,
        'open': 100 + np.cumsum(np.random.randn(1000) * 0.5),
        'high': 102 + np.cumsum(np.random.randn(1000) * 0.5),
        'low': 98 + np.cumsum(np.random.randn(1000) * 0.5),
        'close': 100 + np.cumsum(np.random.randn(1000) * 0.5),
        'volume': np.random.randint(1000, 100000, 1000)
    })
    
    # Generate features
    logger.info("\n[STEP 1] Generating advanced features...")
    
    fg = AdvancedFeatureGenerator()
    micro_features = fg.generate_microstructure_features(df)
    regime_features = fg.generate_regime_features(df)
    cyclical_features = fg.generate_cyclical_features(df)
    momentum_features = fg.generate_momentum_cascade(df)
    
    logger.info(f"  ✓ Microstructure: {micro_features.shape[1]} features")
    logger.info(f"  ✓ Regime: {regime_features.shape[1]} features")
    logger.info(f"  ✓ Cyclical: {cyclical_features.shape[1]} features")
    logger.info(f"  ✓ Momentum: {momentum_features.shape[1]} features")
    
    # Adaptive position sizing
    logger.info("\n[STEP 2] Testing adaptive position sizing...")
    sizer = AdaptivePositionSizer(base_size=1.0)
    
    test_cases = [
        (0.8, 0.01, 0.05, 'trending'),
        (0.6, 0.02, 0.10, 'ranging'),
        (0.5, 0.04, 0.15, 'volatile'),
    ]
    
    for confidence, vol, dd, regime in test_cases:
        size = sizer.calculate_position_size(confidence, vol, dd, regime)
        logger.info(f"  {regime:8} | Conf: {confidence:.1%} | Vol: {vol:.2%} | DD: {dd:.1%} → Size: {size:.2f}")
    
    # Strategy optimization
    logger.info("\n[STEP 3] Optimizing strategy parameters...")
    optimizer = StrategyOptimizer()
    sma_results = optimizer.optimize_sma_periods(df)
    rsi_results = optimizer.optimize_rsi_thresholds(df)
    
    logger.info(f"  ✓ SMA optimization complete ({len(sma_results)} tested)")
    logger.info(f"  ✓ RSI optimization complete ({len(rsi_results)} tested)")
    
    logger.info("\n[OK] Advanced features engine operational")


if __name__ == '__main__':
    main()
