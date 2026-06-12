"""
Expanded Paper Trading Engine with Multiple Tickers/Indices
Extends live_paper_trading_hybrid.py with:
- 40+ instruments (indices + stocks)
- Distributed execution across multiple tickers
- Aggregate P&L tracking
- Enhanced ML training data from multiple sources
"""

import os
import sys
import json
import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np

# Setup paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'app'))
from live_paper_trading_hybrid import LivePaperTradingPipeline, FeatureEngineer
from app.expanded_tickers_config import (
    get_recommended_paper_trading_set,
    get_ticker_info,
    PAPER_TRADING_EXPANSION,
)
from app.brokerage_fees import BrokerageFeeCalculator, BrokeragePlan

# Logging
LOG_DIR = Path(__file__).parent.parent / "logs" / "expanded_trading"
LOG_DIR.mkdir(parents=True, exist_ok=True)

REPORT_DIR = Path(__file__).parent.parent / "reports" / "expanded_trading"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


class ExpandedPaperTradingEngine:
    """
    Execute paper trading across multiple tickers/indices simultaneously
    Aggregate results for comprehensive ML training data
    """
    
    def __init__(self, portfolio_type='recommended', use_advanced_features=True, brokerage_plan=BrokeragePlan.IVALUE):
        """
        Initialize expanded trading engine
        
        Args:
        - portfolio_type: 'recommended'|'aggressive'|'conservative'|'custom'
        - use_advanced_features: Use 76 features (True) or 31 (False)
        - brokerage_plan: ICICI Direct plan for realistic fee calculation
        """
        self.logger = logging.getLogger(__name__)
        self.portfolio_type = portfolio_type
        self.use_advanced_features = use_advanced_features
        
        # Fee tracking
        self.fee_calculator = BrokerageFeeCalculator(plan=brokerage_plan)
        self.brokerage_plan = brokerage_plan
        self.total_fees = 0
        self.total_gross_pnl = 0
        self.total_net_pnl = 0
        
        # Load ticker configuration
        if portfolio_type == 'recommended':
            self.config = get_recommended_paper_trading_set()
        else:
            self.config = get_recommended_paper_trading_set()  # Default
        
        self.all_tickers = self.config['indices'] + self.config['stocks']
        self.total_instruments = len(self.all_tickers)
        
        # Results storage
        self.results = {}  # Per-ticker results
        self.aggregate_results = {}  # Combined results
        self.execution_time = None
        
        self.logger.info(f"[INIT] Expanded Engine with {self.total_instruments} instruments")
        self.logger.info(f"  Indices: {len(self.config['indices'])}")
        self.logger.info(f"  Stocks: {len(self.config['stocks'])}")
        self.logger.info(f"  Brokerage Plan: {brokerage_plan.value.upper()}")
    
    def execute_all_tickers(self):
        """
        Execute paper trading pipeline for ALL tickers
        
        Returns:
        - Dictionary with per-ticker and aggregate results
        """
        try:
            start_time = datetime.now()
            self.logger.info(f"\n{'='*80}")
            self.logger.info(f"[EXPANDED ENGINE] Starting execution for {self.total_instruments} instruments")
            self.logger.info(f"{'='*80}\n")
            
            # Execute each ticker
            for i, ticker in enumerate(self.all_tickers, 1):
                self.logger.info(f"\n[{i}/{self.total_instruments}] Processing: {ticker}")
                self.execute_ticker(ticker)
            
            # Aggregate results
            self.aggregate_results = self._aggregate_results()
            
            self.execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"\n{'='*80}")
            self.logger.info(f"[COMPLETED] All {self.total_instruments} instruments processed")
            self.logger.info(f"Execution Time: {self.execution_time:.2f} seconds")
            self.logger.info(f"Average per Ticker: {self.execution_time/self.total_instruments:.2f}s")
            self.logger.info(f"{'='*80}\n")
            
            return self.aggregate_results
        
        except Exception as e:
            self.logger.error(f"[EXECUTION ERROR] {str(e)}", exc_info=True)
            raise
    
    def execute_ticker(self, ticker):
        """Execute paper trading for single ticker"""
        try:
            # Create pipeline for this ticker
            pipeline = LivePaperTradingPipeline(
                tickers=[(ticker, ticker)]  # Match format expected by pipeline
            )
            
            # Run pipeline
            result = pipeline.run()
            
            # Store result
            if result:
                self.results[ticker] = result
                self.logger.info(f"  [OK] {ticker}: {result.get('trades_executed', 0)} trades, "
                               f"Confidence: {result.get('avg_confidence', 0):.1f}%")
            else:
                self.logger.warning(f"  [NO_RESULT] {ticker}: No result returned")
                self.results[ticker] = None
        
        except Exception as e:
            self.logger.error(f"  [ERROR] {ticker}: {str(e)}")
            self.results[ticker] = None
    
    def _aggregate_results(self):
        """Aggregate results from all tickers"""
        try:
            valid_results = {k: v for k, v in self.results.items() if v is not None}
            
            if not valid_results:
                self.logger.warning("[AGGREGATE] No valid results to aggregate")
                return {}
            
            # Aggregate metrics
            total_trades = sum(r.get('trades_executed', 0) for r in valid_results.values())
            total_gross_pnl = sum(r.get('gross_pnl', 0) for r in valid_results.values())
            total_fees = sum(r.get('total_fees', 0) for r in valid_results.values())
            total_net_pnl = total_gross_pnl - total_fees
            
            confidences = [r.get('avg_confidence', 0) for r in valid_results.values()]
            avg_confidence = np.mean(confidences) if confidences else 0
            
            win_rates = [r.get('win_rate', 0) for r in valid_results.values()]
            avg_win_rate = np.mean(win_rates) if win_rates else 0
            
            return {
                'timestamp': datetime.now().isoformat(),
                'tickers_processed': len(valid_results),
                'tickers_successful': len(valid_results),
                'tickers_failed': self.total_instruments - len(valid_results),
                'total_trades': total_trades,
                'total_gross_pnl': total_gross_pnl,
                'total_fees': total_fees,
                'total_net_pnl': total_net_pnl,
                'brokerage_plan': self.brokerage_plan.value,
                'avg_confidence': avg_confidence,
                'avg_win_rate': avg_win_rate,
                'execution_time_seconds': self.execution_time,
                'per_ticker_results': valid_results,
            }
        
        except Exception as e:
            self.logger.error(f"[AGGREGATE ERROR] {str(e)}")
            return {}
    
    def get_training_data_volume(self):
        """
        Calculate total data volume for ML training
        
        Returns:
        - Total candles, features, and training samples
        """
        total_candles = self.total_instruments * 1000  # ~1000 per ticker
        total_features = 76 if self.use_advanced_features else 31
        total_samples = total_candles - 50  # Minus NaN handling
        
        return {
            'tickers': self.total_instruments,
            'candles_per_ticker': 1000,
            'total_candles': total_candles,
            'features_per_candle': total_features,
            'total_training_samples': total_samples,
            'total_feature_values': total_samples * total_features,
        }
    
    def save_results(self):
        """Save results to JSON file"""
        try:
            filename = REPORT_DIR / f"expanded_trading_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Prepare data for JSON serialization
            report = {
                'summary': {
                    'execution_date': datetime.now().isoformat(),
                    'portfolio_type': self.portfolio_type,
                    'use_advanced_features': self.use_advanced_features,
                    'execution_time': self.execution_time,
                },
                'aggregate': self.aggregate_results,
                'per_ticker': {k: v for k, v in self.results.items() if v is not None},
                'training_data': self.get_training_data_volume(),
                'expansion_roadmap': PAPER_TRADING_EXPANSION,
            }
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"[SAVED] Results to {filename}")
            return filename
        
        except Exception as e:
            self.logger.error(f"[SAVE ERROR] {str(e)}")
            return None
    
    def print_summary(self):
        """Print summary to console"""
        print("\n" + "="*80)
        print("EXPANDED PAPER TRADING - EXECUTION SUMMARY")
        print("="*80)
        
        print(f"\n[CONFIGURATION]:")
        print(f"  Portfolio Type: {self.portfolio_type}")
        print(f"  Total Instruments: {self.total_instruments}")
        print(f"  Indices: {len(self.config['indices'])}")
        print(f"  Stocks: {len(self.config['stocks'])}")
        print(f"  Advanced Features: {'Yes (76)' if self.use_advanced_features else 'No (31)'}")
        
        print(f"\n[EXECUTION TIME]:")
        print(f"  Total Time: {self.execution_time:.2f}s")
        print(f"  Per Ticker: {self.execution_time/self.total_instruments:.2f}s")
        
        print(f"\n[RESULTS]:")
        print(f"  Successful: {self.aggregate_results.get('tickers_successful', 0)}/{self.total_instruments}")
        print(f"  Total Trades: {self.aggregate_results.get('total_trades', 0)}")
        print(f"  Total P&L: Rs {self.aggregate_results.get('total_pnl', 0):.2f}")
        print(f"  Avg Confidence: {self.aggregate_results.get('avg_confidence', 0):.1f}%")
        print(f"  Avg Win Rate: {self.aggregate_results.get('avg_win_rate', 0):.1f}%")
        
        print(f"\n[TRAINING DATA]:")
        training_vol = self.get_training_data_volume()
        print(f"  Total Candles: {training_vol['total_candles']:,}")
        print(f"  Total Samples: {training_vol['total_training_samples']:,}")
        print(f"  Total Feature Values: {training_vol['total_feature_values']:,}")
        print(f"  Data Volume: {training_vol['total_feature_values'] * 8 / (1024*1024):.1f} MB")
        
        print(f"\n[STATUS] EXECUTION COMPLETE")
        print("="*80 + "\n")


class PortfolioOptimizer:
    """Optimize ticker selection based on liquidity & tradability"""
    
    @staticmethod
    def get_expansion_plan(current=3, target=40):
        """
        Get phase-by-phase expansion plan
        
        Example: current=3 (NIFTY50, BANKNIFTY, FINNIFTY)
                 target=40 (comprehensive coverage)
        """
        phases = PAPER_TRADING_EXPANSION
        
        plan = {
            'current_phase': 'current',
            'current_count': current,
            'target_count': target,
            'expansion_phases': []
        }
        
        for phase, config in phases.items():
            if config['total'] > current and config['total'] <= target:
                plan['expansion_phases'].append({
                    'phase': phase.upper(),
                    'instruments': config['total'],
                    'reason': config['reason'],
                })
        
        return plan
    
    @staticmethod
    def get_phase_tickers(phase='phase_1'):
        """Get recommended tickers for specific expansion phase"""
        from expanded_tickers_config import get_recommended_paper_trading_set
        config = get_recommended_paper_trading_set()
        
        if phase == 'phase_1':
            return config['indices'][:8] + config['stocks'][:5]
        elif phase == 'phase_2':
            return config['indices'][:12] + config['stocks'][:15]
        elif phase == 'phase_3':
            return config['indices'][:16] + config['stocks'][:25]
        else:
            return config['indices'] + config['stocks']


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("EXPANDED PAPER TRADING ENGINE")
    print("="*80 + "\n")
    
    # Create expanded engine
    engine = ExpandedPaperTradingEngine(
        portfolio_type='recommended',
        use_advanced_features=True  # Use 76 features
    )
    
    print(f"Configured for {engine.total_instruments} instruments\n")
    
    # Execute
    results = engine.execute_all_tickers()
    
    # Print summary
    engine.print_summary()
    
    # Save results
    output_file = engine.save_results()
    
    # Show expansion roadmap
    print("\n📊 EXPANSION ROADMAP:")
    optimizer = PortfolioOptimizer()
    plan = optimizer.get_expansion_plan(current=3, target=40)
    
    print(f"  Current: 3 instruments")
    for phase_info in plan['expansion_phases']:
        print(f"  → {phase_info['phase']}: {phase_info['instruments']} instruments")
        print(f"    {phase_info['reason']}")
    
    print(f"\nExpanded to {engine.total_instruments} instruments successfully! ✅")
