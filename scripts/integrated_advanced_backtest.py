#!/usr/bin/env python3
"""
Integrated Advanced Indicators Backtest
Combines Stochastic RSI, Fibonacci, and Renko Bars with Enhanced Signal System
Tests with real Breeze API data - PRODUCTION IMPLEMENTATION
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime
import json
import logging
from typing import Dict, List, Tuple, Optional

from app.services.breeze_api import BreezeAPIService
from app.strategies.enhanced_signal_confirmation import EnhancedSignalConfirmation
from app.strategies.advanced_signal_validators import AdvancedSignalValidator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()


class IntegratedAdvancedBacktest:
    """Complete integrated backtest with all three advanced indicators"""
    
    def __init__(self):
        """Initialize with Breeze connection"""
        self.breeze_service = BreezeAPIService()
        auth_result = self.breeze_service.authenticate()
        if not auth_result['success']:
            raise Exception(f"Auth failed: {auth_result.get('error')}")
        logger.info("✓ Breeze connection established")
    
    def fetch_data(self, stock_code: str, days: int = 168) -> Optional[pd.DataFrame]:
        """Fetch historical data from Breeze API"""
        try:
            logger.info(f"Fetching {days} days of {stock_code} data...")
            
            result = self.breeze_service.get_historical_data(
                stock_code=stock_code,
                interval="day",
                days_back=days
            )
            
            if not result.get('success'):
                logger.error(f"No data for {stock_code}")
                return None
            
            historical_data = result.get('data', [])
            
            if not historical_data:
                logger.error(f"Empty data response for {stock_code}")
                return None
            
            df = pd.DataFrame(historical_data)
            
            # Handle datetime column
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'])
            elif 'date' in df.columns:
                df['datetime'] = pd.to_datetime(df['date'], format='%d-%b-%Y')
            else:
                raise ValueError("No datetime column found")
            
            df = df.set_index('datetime').sort_index()
            df.columns = df.columns.str.lower()
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            logger.info(f"✓ {len(df)} bars | ₹{df['close'].min():.2f} - ₹{df['close'].max():.2f}")
            return df
        
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            return None
    
    def backtest_integrated_system(self, stock_code: str, df: pd.DataFrame,
                                  use_stoch_rsi: bool = True,
                                  use_fibonacci: bool = True,
                                  use_renko: bool = True,
                                  initial_capital: float = 100000) -> Dict:
        """Run integrated backtest with all enabled indicators"""
        
        logger.info(f"\n{'='*70}")
        logger.info(f"INTEGRATED BACKTEST: {stock_code}")
        logger.info(f"{'='*70}")
        logger.info(f"Stochastic RSI: {use_stoch_rsi} | Fibonacci: {use_fibonacci} | Renko: {use_renko}")
        
        results = {
            'stock_code': stock_code,
            'config': {
                'stoch_rsi': use_stoch_rsi,
                'fibonacci': use_fibonacci,
                'renko': use_renko
            },
            'trades': [],
            'metrics': {}
        }
        
        cash = initial_capital
        position = None
        position_pl_list = []
        
        enhanced_signal = EnhancedSignalConfirmation(df)
        advanced_validator = AdvancedSignalValidator(df)
        
        indicators_triggered = {'stoch_rsi': 0, 'fibonacci': 0, 'renko': 0}
        indicators_rejected = {'stoch_rsi': 0, 'fibonacci': 0, 'renko': 0}
        
        for bar_idx in range(20, len(df)):
            current_date = df.index[bar_idx]
            current_price = df['close'].iloc[bar_idx]
            
            # ENTRY LOGIC
            if position is None:
                entry_result = enhanced_signal.validate_entry_signal(bar_idx)
                entry_score = entry_result.get('overall_score', 0.0)
                
                if entry_score >= 0.50:
                    # Base signal passed, now check advanced indicators
                    entry_valid = True
                    rejection_reasons = []
                    
                    # Check Stochastic RSI
                    if use_stoch_rsi:
                        stoch_result = advanced_validator.validate_entry_with_stoch_rsi(
                            bar_idx, signal_type='BUY'
                        )
                        stoch_score = stoch_result.get('score', 0.0)
                        if stoch_score >= 0.50:
                            indicators_triggered['stoch_rsi'] += 1
                        else:
                            indicators_rejected['stoch_rsi'] += 1
                            if stoch_score < 0.30:
                                entry_valid = False
                                rejection_reasons.append(f"Stoch RSI ({stoch_score:.2f})")
                    
                    # Check Fibonacci
                    if use_fibonacci and entry_valid:
                        fib_result = advanced_validator.validate_entry_with_fibonacci(
                            bar_idx, signal_type='BUY', proximity_threshold=1.5
                        )
                        fib_score = fib_result.get('score', 0.0)
                        if fib_score >= 0.60:
                            indicators_triggered['fibonacci'] += 1
                        else:
                            indicators_rejected['fibonacci'] += 1
                            if fib_score < 0.40:
                                entry_valid = False
                                rejection_reasons.append(f"Fibonacci ({fib_score:.2f})")
                    
                    # Check Renko
                    if use_renko and entry_valid:
                        renko_result = advanced_validator.validate_entry_with_renko(bar_idx)
                        renko_score = renko_result.get('score', 0.0)
                        if renko_score >= 0.50:
                            indicators_triggered['renko'] += 1
                        else:
                            indicators_rejected['renko'] += 1
                            if renko_score < 0.30:
                                entry_valid = False
                                rejection_reasons.append(f"Renko ({renko_score:.2f})")
                    
                    # Execute entry if all checks pass
                    if entry_valid:
                        units = int(cash * 0.95 / current_price)
                        if units > 0:
                            position = {
                                'entry_price': current_price,
                                'entry_idx': bar_idx,
                                'entry_date': current_date,
                                'units': units,
                                'entry_score': entry_score
                            }
                            logger.info(f"ENTRY #{len(results['trades'])+1}: {current_date.date()} @ ₹{current_price:.2f} | Score: {entry_score:.3f}")
            
            # EXIT LOGIC
            elif position is not None:
                pnl = (current_price - position['entry_price']) * position['units']
                pnl_pct = (current_price - position['entry_price']) / position['entry_price'] * 100
                
                should_exit = False
                exit_reason = None
                
                # Exit conditions
                if pnl_pct >= 5.0:
                    should_exit = True
                    exit_reason = "PROFIT_TARGET"
                elif pnl_pct <= -2.0:
                    should_exit = True
                    exit_reason = "STOP_LOSS"
                elif enhanced_signal.validate_entry_signal(bar_idx).get('overall_score', 0.0) < 0.30:
                    should_exit = True
                    exit_reason = "SIGNAL_DEGRADATION"
                
                if should_exit and exit_reason:
                    cash = position['units'] * current_price
                    position_pl = pnl
                    position_pl_list.append(position_pl)
                    
                    results['trades'].append({
                        'entry_date': position['entry_date'].strftime('%Y-%m-%d'),
                        'entry_price': position['entry_price'],
                        'exit_date': current_date.strftime('%Y-%m-%d'),
                        'exit_price': current_price,
                        'units': position['units'],
                        'pnl': position_pl,
                        'pnl_pct': pnl_pct,
                        'exit_reason': exit_reason
                    })
                    
                    logger.info(f"  EXIT: {current_date.date()} @ ₹{current_price:.2f} | PnL: ₹{position_pl:.0f} ({pnl_pct:+.2f}%) | {exit_reason}")
                    
                    position = None
        
        # Calculate metrics
        if position_pl_list:
            total_pnl = sum(position_pl_list)
            wins = sum(1 for p in position_pl_list if p > 0)
            losses = sum(1 for p in position_pl_list if p < 0)
            breakeven = sum(1 for p in position_pl_list if p == 0)
            
            results['metrics'] = {
                'total_trades': len(position_pl_list),
                'winning_trades': wins,
                'losing_trades': losses,
                'breakeven_trades': breakeven,
                'win_rate': wins / len(position_pl_list) * 100 if position_pl_list else 0,
                'total_pnl': total_pnl,
                'return_pct': (total_pnl / initial_capital) * 100,
                'avg_win': np.mean([p for p in position_pl_list if p > 0]) if wins > 0 else 0,
                'avg_loss': np.mean([p for p in position_pl_list if p < 0]) if losses > 0 else 0,
                'profit_factor': sum(p for p in position_pl_list if p > 0) / abs(sum(p for p in position_pl_list if p < 0)) if losses > 0 else 0,
                'max_drawdown': self._calculate_max_drawdown(position_pl_list),
                'sharpe_ratio': self._calculate_sharpe(position_pl_list),
                'indicators': indicators_triggered
            }
            
            logger.info(f"\n{'─'*70}")
            logger.info(f"RESULTS: {stock_code}")
            logger.info(f"  Trades: {results['metrics']['total_trades']} | Win Rate: {results['metrics']['win_rate']:.2f}%")
            logger.info(f"  Total PnL: ₹{results['metrics']['total_pnl']:.0f} ({results['metrics']['return_pct']:+.2f}%)")
            logger.info(f"  Sharpe: {results['metrics']['sharpe_ratio']:.2f} | Max DD: {results['metrics']['max_drawdown']:.2f}%")
            logger.info(f"  Stoch RSI Signals: {indicators_triggered['stoch_rsi']} | Rejects: {indicators_rejected['stoch_rsi']}")
            logger.info(f"  Fibonacci Signals: {indicators_triggered['fibonacci']} | Rejects: {indicators_rejected['fibonacci']}")
            logger.info(f"  Renko Signals: {indicators_triggered['renko']} | Rejects: {indicators_rejected['renko']}")
            logger.info(f"{'─'*70}\n")
        
        return results
    
    @staticmethod
    def _calculate_max_drawdown(returns: List[float]) -> float:
        """Calculate maximum drawdown from returns"""
        if not returns:
            return 0.0
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max * 100
        return np.min(drawdown) if len(drawdown) > 0 else 0.0
    
    @staticmethod
    def _calculate_sharpe(returns: List[float], risk_free_rate: float = 0.06) -> float:
        """Calculate Sharpe ratio"""
        if not returns or len(returns) < 2:
            return 0.0
        returns_array = np.array(returns)
        excess_returns = returns_array - risk_free_rate
        if np.std(excess_returns) == 0:
            return 0.0
        sharpe = (np.mean(excess_returns) / np.std(excess_returns)) * np.sqrt(252)
        return sharpe
    
    def run_full_test(self, stocks: List[str]) -> Dict:
        """Run complete test suite"""
        
        all_results = {
            'test_run': datetime.now().isoformat(),
            'configurations': [
                {'name': 'BASE_ONLY', 'stoch_rsi': False, 'fibonacci': False, 'renko': False},
                {'name': 'WITH_ALL', 'stoch_rsi': True, 'fibonacci': True, 'renko': True},
            ],
            'results': {}
        }
        
        for stock_code in stocks:
            logger.info(f"\n{'#'*70}")
            logger.info(f"# TESTING {stock_code}")
            logger.info(f"{'#'*70}")
            
            df = self.fetch_data(stock_code)
            if df is None or len(df) < 50:
                logger.error(f"Insufficient data for {stock_code}")
                continue
            
            all_results['results'][stock_code] = {}
            
            # Test BASE ONLY
            base_results = self.backtest_integrated_system(
                stock_code, df,
                use_stoch_rsi=False,
                use_fibonacci=False,
                use_renko=False
            )
            all_results['results'][stock_code]['BASE_ONLY'] = base_results
            
            # Test WITH ALL INDICATORS
            integrated_results = self.backtest_integrated_system(
                stock_code, df,
                use_stoch_rsi=True,
                use_fibonacci=True,
                use_renko=True
            )
            all_results['results'][stock_code]['WITH_ALL'] = integrated_results
            
            # Compare
            self._compare_configs(base_results, integrated_results)
        
        # Save results
        results_file = f"integrated_advanced_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        logger.info(f"\n✓ Results saved to {results_file}")
        return all_results
    
    def _compare_configs(self, base: Dict, integrated: Dict):
        """Compare BASE vs INTEGRATED configurations"""
        
        base_metrics = base.get('metrics', {})
        integrated_metrics = integrated.get('metrics', {})
        
        if not base_metrics or not integrated_metrics:
            return
        
        logger.info(f"\n{'='*70}")
        logger.info(f"COMPARISON: BASE vs INTEGRATED - {base['stock_code']}")
        logger.info(f"{'='*70}")
        logger.info(f"Trades:     {base_metrics.get('total_trades', 0):>3} → {integrated_metrics.get('total_trades', 0):>3}")
        logger.info(f"Win Rate:   {base_metrics.get('win_rate', 0):>6.2f}% → {integrated_metrics.get('win_rate', 0):>6.2f}%")
        logger.info(f"Return:     {base_metrics.get('return_pct', 0):>6.2f}% → {integrated_metrics.get('return_pct', 0):>6.2f}%")
        logger.info(f"Sharpe:     {base_metrics.get('sharpe_ratio', 0):>6.2f} → {integrated_metrics.get('sharpe_ratio', 0):>6.2f}")
        logger.info(f"Max DD:     {base_metrics.get('max_drawdown', 0):>6.2f}% → {integrated_metrics.get('max_drawdown', 0):>6.2f}%")
        
        # Recommendation
        return_improved = integrated_metrics.get('return_pct', 0) > base_metrics.get('return_pct', 0)
        sharpe_maintained = integrated_metrics.get('sharpe_ratio', 0) >= base_metrics.get('sharpe_ratio', 0) - 0.1
        win_rate_good = integrated_metrics.get('win_rate', 0) >= 65
        
        if return_improved and sharpe_maintained and win_rate_good:
            logger.info(f"✅ INTEGRATED SYSTEM SHOWS IMPROVEMENT")
        elif integrated_metrics.get('return_pct', 0) > base_metrics.get('return_pct', 0) - 0.5:
            logger.info(f"✅ INTEGRATED SYSTEM MAINTAINS PERFORMANCE")
        else:
            logger.info(f"⚠️  BASE SYSTEM PREFERRED (INTEGRATED UNDERPERFORMS)")
        
        logger.info(f"{'='*70}\n")


def main():
    """Execute integrated backtest"""
    
    try:
        backtest = IntegratedAdvancedBacktest()
        
        # Extended test with more stocks and indices
        test_securities = [
            'RELIND',      # Financial services (trending) ✓ Data available
            'TCS',         # IT services (volatile) ✓ Data available
            'INFTEC',      # IT (highly liquid) ✓ Data available - NSE official symbol for Infosys
            'WIPRO',       # IT (moderate volatility) ✓ Data available
            'BAFINS',      # Financial (trending) ✓ Data available - NSE official symbol for Bajaj Finserv
            'MARUTI',      # Auto (broad market) ✓ Data available
        ]
        
        results = backtest.run_full_test(test_securities)
        
        logger.info("\n" + "="*70)
        logger.info("✓ INTEGRATED BACKTEST COMPLETE")
        logger.info("="*70)
        
        return results
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
