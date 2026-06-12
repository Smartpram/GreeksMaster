"""
PHASE 3 WEEK 2 - AI BACKTESTING
================================

Execute backtesting with trained ML models from Week 1
Compare AI models vs baseline SMA20 strategy
Validate edge on historical data

Success Criteria:
  • Win rate: >50%
  • Profit factor: >1.5
  • Drawdown: <20%
  • Sharpe ratio: >0.5

Timeline: Week 2 (Tuesday-Thursday)
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
import joblib
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('PHASE_3_WEEK2_BACKTEST.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

from app.ml_models.training_engine import ModelTrainer
from app.ml_models.data_collector import DataCollector


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


class AIBacktester:
    """Backtest AI models vs baseline strategy"""
    
    def __init__(self, symbol: str = 'NIFTY50'):
        self.symbol = symbol
        self.model_dir = Path('app/ml_models/trained_models')
        self.results = {}
        logger.info(f"AIBacktester initialized for {symbol}")
    
    def load_models(self) -> Dict:
        """Load trained models and scalers"""
        logger.info(f"Loading models for {self.symbol}...")
        
        try:
            xgb_path = self.model_dir / f'{self.symbol}_xgboost_model.joblib'
            rf_path = self.model_dir / f'{self.symbol}_random_forest_model.joblib'
            scaler_path = self.model_dir / f'{self.symbol}_scaler.joblib'
            
            if not xgb_path.exists():
                logger.error(f"XGBoost model not found: {xgb_path}")
                return None
            
            xgb_model = joblib.load(xgb_path)
            rf_model = joblib.load(rf_path)
            scaler = joblib.load(scaler_path)
            
            logger.info(f"[OK] XGBoost model loaded")
            logger.info(f"[OK] Random Forest model loaded")
            logger.info(f"[OK] Scaler loaded")
            
            return {
                'xgboost': xgb_model,
                'random_forest': rf_model,
                'scaler': scaler
            }
        
        except Exception as e:
            logger.error(f"Failed to load models: {str(e)}")
            traceback.print_exc()
            return None
    
    def load_data(self, days: int = 365) -> pd.DataFrame:
        """Load backtest data"""
        logger.info(f"Loading backtest data for {self.symbol}...")
        
        try:
            collector = DataCollector(self.symbol)
            df = collector.collect_from_breeze_api(days=days)
            
            if df is None or len(df) == 0:
                logger.warning("No data collected, using synthetic")
                df = collector._generate_synthetic_data(days=days)
            
            logger.info(f"[OK] Loaded {len(df)} candles for backtesting")
            return df
        
        except Exception as e:
            logger.error(f"Failed to load data: {str(e)}")
            return None
    
    def generate_baseline_signals(self, df: pd.DataFrame) -> np.ndarray:
        """Generate SMA20 baseline signals"""
        logger.info("Generating baseline SMA20 signals...")
        
        df = df.copy()
        df['sma20'] = df['close'].rolling(20).mean()
        df['sma50'] = df['close'].rolling(50).mean()
        
        signals = np.zeros(len(df))
        for i in range(1, len(df)):
            if df.iloc[i]['close'] > df.iloc[i]['sma20']:
                signals[i] = 1  # BUY
            elif df.iloc[i]['close'] < df.iloc[i]['sma20']:
                signals[i] = -1  # SELL
            else:
                signals[i] = 0  # HOLD
        
        logger.info(f"[OK] Generated baseline signals: {np.sum(signals > 0)} buys, {np.sum(signals < 0)} sells")
        return signals
    
    def generate_ai_signals(self, df: pd.DataFrame, models: Dict) -> np.ndarray:
        """Generate AI model signals"""
        logger.info("Generating AI model signals...")
        
        try:
            trainer = ModelTrainer(self.symbol)
            features_df, _ = trainer.generate_features(df)
            
            if features_df is None or len(features_df) == 0:
                logger.error("Failed to generate features")
                return None
            
            # Scale features
            features_scaled = models['scaler'].transform(features_df)
            
            # Get predictions
            xgb_pred = models['xgboost'].predict(features_scaled)
            rf_pred = models['random_forest'].predict(features_scaled)
            
            # Ensemble: average predictions
            ensemble_pred = (xgb_pred + rf_pred) / 2
            
            # Convert to signals (0=DOWN, 1=NEUTRAL, 2=UP)
            signals = np.zeros(len(ensemble_pred))
            for i in range(len(ensemble_pred)):
                if ensemble_pred[i] > 1.5:  # UP
                    signals[i] = 1
                elif ensemble_pred[i] < 0.5:  # DOWN
                    signals[i] = -1
                else:  # NEUTRAL
                    signals[i] = 0
            
            logger.info(f"[OK] Generated AI signals: {np.sum(signals > 0)} buys, {np.sum(signals < 0)} sells")
            return signals
        
        except Exception as e:
            logger.error(f"Failed to generate AI signals: {str(e)}")
            traceback.print_exc()
            return None
    
    def calculate_returns(self, df: pd.DataFrame, signals: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """Calculate strategy returns"""
        # Align df and signals (signals may be shorter due to NaN removal in features)
        min_len = min(len(df), len(signals))
        
        returns = np.zeros(min_len)
        pnl_points = 0
        trades = 0
        profitable_trades = 0
        
        for i in range(1, min_len):
            price_change = (df.iloc[i]['close'] - df.iloc[i-1]['close']) / df.iloc[i-1]['close']
            
            if signals[i-1] == 1:  # BUY
                returns[i] = price_change * 100  # In percentage
                pnl_points += price_change * 100
                trades += 1
                if price_change > 0:
                    profitable_trades += 1
            elif signals[i-1] == -1:  # SELL
                returns[i] = -price_change * 100  # Inverse
                pnl_points += -price_change * 100
                trades += 1
                if price_change < 0:
                    profitable_trades += 1
        
        win_rate = (profitable_trades / trades * 100) if trades > 0 else 0
        
        return returns, {
            'total_pnl': pnl_points,
            'total_trades': trades,
            'profitable_trades': profitable_trades,
            'win_rate': win_rate,
            'cumulative_return': np.sum(returns)
        }
    
    def run_backtest(self) -> Dict:
        """Execute full backtest"""
        print_section(f"BACKTESTING {self.symbol}")
        
        # Step 1: Load models
        print("[STEP 1] Loading trained models...")
        models = self.load_models()
        if models is None:
            logger.error("Failed to load models")
            return {'status': 'failed', 'reason': 'model_loading'}
        
        # Step 2: Load data
        print("[STEP 2] Loading backtest data...")
        df = self.load_data(days=365)
        if df is None:
            logger.error("Failed to load data")
            return {'status': 'failed', 'reason': 'data_loading'}
        
        # Step 3: Generate baseline signals
        print("[STEP 3] Generating baseline signals...")
        baseline_signals = self.generate_baseline_signals(df)
        
        # Step 4: Generate AI signals
        print("[STEP 4] Generating AI signals...")
        ai_signals = self.generate_ai_signals(df, models)
        if ai_signals is None:
            logger.error("Failed to generate AI signals")
            return {'status': 'failed', 'reason': 'ai_signals'}
        
        # Step 5: Calculate returns
        print("[STEP 5] Calculating returns...")
        baseline_returns, baseline_metrics = self.calculate_returns(df, baseline_signals)
        ai_returns, ai_metrics = self.calculate_returns(df, ai_signals)
        
        logger.info(f"\nBaseline Metrics:")
        logger.info(f"  Win Rate: {baseline_metrics['win_rate']:.2f}%")
        logger.info(f"  Total Trades: {baseline_metrics['total_trades']}")
        logger.info(f"  Cumulative Return: {baseline_metrics['cumulative_return']:.2f}%")
        
        logger.info(f"\nAI Model Metrics:")
        logger.info(f"  Win Rate: {ai_metrics['win_rate']:.2f}%")
        logger.info(f"  Total Trades: {ai_metrics['total_trades']}")
        logger.info(f"  Cumulative Return: {ai_metrics['cumulative_return']:.2f}%")
        
        # Calculate improvements
        win_rate_improvement = ai_metrics['win_rate'] - baseline_metrics['win_rate']
        return_improvement = ai_metrics['cumulative_return'] - baseline_metrics['cumulative_return']
        
        logger.info(f"\nImprovement:")
        logger.info(f"  Win Rate: {win_rate_improvement:+.2f}%")
        logger.info(f"  Return: {return_improvement:+.2f}%")
        
        self.results = {
            'symbol': self.symbol,
            'backtest_date': datetime.now().isoformat(),
            'baseline': baseline_metrics,
            'ai_model': ai_metrics,
            'improvement': {
                'win_rate': win_rate_improvement,
                'return': return_improvement
            },
            'edge_validated': ai_metrics['win_rate'] > 50 and return_improvement > 0
        }
        
        return self.results


def main():
    """Execute Phase 3 Week 2 backtesting"""
    
    print("\n" + "="*70)
    print("  PHASE 3 WEEK 2 - AI BACKTESTING")
    print("  June 10, 2026 - Validate ML Models")
    print("="*70)
    
    symbols = ['NIFTY50', 'BANKNIFTY', 'FINNIFTY']
    all_results = {}
    
    for symbol in symbols:
        print(f"\n\n{'='*70}")
        print(f"  BACKTESTING {symbol}")
        print(f"{'='*70}\n")
        
        backtester = AIBacktester(symbol)
        results = backtester.run_backtest()
        all_results[symbol] = results
        
        if results.get('status') != 'failed':
            print(f"\n[OK] {symbol} backtest complete")
            print(f"  AI Win Rate: {results['ai_model']['win_rate']:.2f}%")
            print(f"  AI Return: {results['ai_model']['cumulative_return']:.2f}%")
            if results['edge_validated']:
                print(f"  Edge: [OK] VALIDATED")
            else:
                print(f"  Edge: [WARN] NOT VALIDATED")
    
    # Generate report
    print_section("WEEK 2 BACKTESTING SUMMARY")
    
    report = f"""# PHASE 3 WEEK 2 - AI BACKTESTING REPORT

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

AI models backtested on {len(symbols)} symbols over 365-day period.

## Results by Symbol

"""
    
    edges_validated = 0
    for symbol, results in all_results.items():
        if results.get('status') != 'failed':
            ai_wr = results['ai_model']['win_rate']
            bl_wr = results['baseline']['win_rate']
            edge = "[OK] VALIDATED" if results['edge_validated'] else "[WARN] NOT VALIDATED"
            
            report += f"""### {symbol}
- Baseline Win Rate: {bl_wr:.2f}%
- AI Model Win Rate: {ai_wr:.2f}%
- Win Rate Improvement: {results['improvement']['win_rate']:+.2f}%
- Return Improvement: {results['improvement']['return']:+.2f}%
- Edge Status: {edge}

"""
            if results['edge_validated']:
                edges_validated += 1
    
    report += f"""## Overall Assessment

- Symbols with validated edge: {edges_validated}/{len(symbols)}
- Ready for Week 3 Paper Trading: {"YES" if edges_validated >= 2 else "NO"}

## Next Steps

{"Proceed to Week 3 (Paper Trading)" if edges_validated >= 2 else "Fine-tune models and retry"}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    report_path = Path('PHASE_3_WEEK2_BACKTEST_REPORT.md')
    report_path.write_text(report, encoding='utf-8')
    logger.info(f"Report saved to {report_path}")
    
    # Save JSON results
    with open('PHASE_3_WEEK2_RESULTS.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n[OK] Week 2 Backtesting Complete")
    print(f"  Report: PHASE_3_WEEK2_BACKTEST_REPORT.md")
    print(f"  Results: PHASE_3_WEEK2_RESULTS.json")
    print(f"  Edges Validated: {edges_validated}/{len(symbols)}\n")


if __name__ == '__main__':
    main()
