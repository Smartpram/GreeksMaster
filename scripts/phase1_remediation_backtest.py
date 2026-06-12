#!/usr/bin/env python3
"""
Phase 1 Remediation Backtest: Hierarchical Filter Implementation
Tests new FilterHierarchy (2-of-3 logic) vs original RIGID AND logic
Compares: BASE vs RIGID_AND vs HIERARCHICAL
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
from app.strategies.filter_hierarchy import FilterHierarchy, MarketRegime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()


class Phase1RemediationBacktest:
    """Phase 1 backtest: Tests FilterHierarchy vs original AND logic"""
    
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
    
    def backtest_configuration(self, stock_code: str, df: pd.DataFrame,
                              config_type: str = 'hierarchical',
                              initial_capital: float = 100000) -> Dict:
        """
        Run backtest with specified configuration
        
        Args:
            stock_code: Stock code to test
            df: OHLCV DataFrame
            config_type: 'base' (no filters), 'rigid_and' (original), or 'hierarchical' (new)
            initial_capital: Starting capital
            
        Returns:
            Dict with trade results and metrics
        """
        
        logger.info(f"\n{'─'*70}")
        logger.info(f"BACKTEST: {stock_code} - {config_type.upper()}")
        logger.info(f"{'─'*70}")
        
        results = {
            'stock_code': stock_code,
            'config': config_type,
            'trades': [],
            'metrics': {},
            'filter_stats': {}
        }
        
        cash = initial_capital
        position = None
        position_pl_list = []
        
        enhanced_signal = EnhancedSignalConfirmation(df)
        advanced_validator = AdvancedSignalValidator(df)
        filter_hierarchy = FilterHierarchy(df, advanced_validator)
        
        filter_stats = {
            'base_signals': 0,
            'base_entries': 0,
            'hierarchical_entries': 0,
            'regime_changes': [],
            'patterns_used': {}
        }
        
        current_regime = None
        
        for bar_idx in range(20, len(df)):
            current_date = df.index[bar_idx]
            current_price = df['close'].iloc[bar_idx]
            
            # Track regime changes
            regime = filter_hierarchy.regime_detector.get_regime(bar_idx)
            if regime != current_regime:
                filter_stats['regime_changes'].append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'regime': regime.value
                })
                current_regime = regime
            
            # ENTRY LOGIC
            if position is None:
                entry_result = enhanced_signal.validate_entry_signal(bar_idx)
                entry_score = entry_result.get('overall_score', 0.0)
                
                if entry_score >= 0.50:
                    filter_stats['base_signals'] += 1
                    
                    # Determine if entry should be taken based on config
                    should_enter = False
                    entry_details = {}
                    
                    if config_type == 'base':
                        # Just use base signal
                        should_enter = True
                        entry_details = {'reason': 'base_signal'}
                    
                    elif config_type == 'rigid_and':
                        # Original strict AND logic
                        stoch_ok = advanced_validator.validate_entry_with_stoch_rsi(bar_idx, 'BUY').get('valid', False)
                        fib_ok = advanced_validator.validate_entry_with_fibonacci(bar_idx, 'BUY').get('valid', False)
                        renko_ok = advanced_validator.validate_entry_with_renko(bar_idx).get('valid', False)
                        
                        should_enter = stoch_ok and fib_ok and renko_ok
                        entry_details = {
                            'stoch_ok': stoch_ok,
                            'fib_ok': fib_ok,
                            'renko_ok': renko_ok,
                            'reason': 'rigid_and'
                        }
                    
                    elif config_type == 'hierarchical':
                        # New hierarchical 2-of-3 logic
                        should_enter, signal_quality, hier_details = filter_hierarchy.should_trade_hierarchical(bar_idx, 'BUY')
                        entry_details = {
                            'signal_quality': signal_quality,
                            'pattern': hier_details.get('pattern', 'none'),
                            'regime': hier_details.get('regime', 'unknown'),
                            'reason': 'hierarchical'
                        }
                    
                    # Execute entry
                    if should_enter:
                        if config_type == 'hierarchical':
                            filter_stats['hierarchical_entries'] += 1
                            pattern = entry_details.get('pattern', 'unknown')
                            filter_stats['patterns_used'][pattern] = filter_stats['patterns_used'].get(pattern, 0) + 1
                        else:
                            filter_stats['base_entries'] += 1
                        
                        units = int(cash * 0.95 / current_price)
                        if units > 0:
                            position = {
                                'entry_price': current_price,
                                'entry_idx': bar_idx,
                                'entry_date': current_date,
                                'units': units,
                                'entry_score': entry_score,
                                'entry_details': entry_details
                            }
                            
                            entry_msg = f"ENTRY: {current_date.date()} @ ₹{current_price:.2f}"
                            if config_type == 'hierarchical':
                                entry_msg += f" | Quality: {entry_details.get('signal_quality', 0):.2f} | Pattern: {entry_details.get('pattern', '?')}"
                            logger.info(entry_msg)
            
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
                        'exit_reason': exit_reason,
                        'entry_details': position.get('entry_details', {})
                    })
                    
                    logger.info(f"  EXIT: {current_date.date()} @ ₹{current_price:.2f} | PnL: ₹{position_pl:.0f} ({pnl_pct:+.2f}%) | {exit_reason}")
                    
                    position = None
        
        # Calculate metrics
        if position_pl_list:
            total_pnl = sum(position_pl_list)
            wins = sum(1 for p in position_pl_list if p > 0)
            losses = sum(1 for p in position_pl_list if p < 0)
            
            results['metrics'] = {
                'total_trades': len(position_pl_list),
                'winning_trades': wins,
                'losing_trades': losses,
                'win_rate': wins / len(position_pl_list) * 100 if position_pl_list else 0,
                'total_pnl': total_pnl,
                'return_pct': (total_pnl / initial_capital) * 100,
                'avg_win': np.mean([p for p in position_pl_list if p > 0]) if wins > 0 else 0,
                'avg_loss': np.mean([p for p in position_pl_list if p < 0]) if losses > 0 else 0,
                'profit_factor': sum(p for p in position_pl_list if p > 0) / abs(sum(p for p in position_pl_list if p < 0)) if losses > 0 else 0,
                'max_drawdown': self._calculate_max_drawdown(position_pl_list),
                'sharpe_ratio': self._calculate_sharpe(position_pl_list),
            }
            
            results['filter_stats'] = filter_stats
            
            logger.info(f"METRICS: {results['metrics']}")
            logger.info(f"FILTER_STATS: {filter_stats}")
        
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
        """Run complete test suite comparing all configurations"""
        
        all_results = {
            'test_run': datetime.now().isoformat(),
            'test_name': 'Phase 1 Remediation: FilterHierarchy vs Rigid AND',
            'configurations': ['BASE', 'RIGID_AND', 'HIERARCHICAL'],
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
            
            # Test BASE (no filters)
            base_results = self.backtest_configuration(stock_code, df, 'base')
            all_results['results'][stock_code]['BASE'] = base_results
            
            # Test RIGID AND (original)
            rigid_results = self.backtest_configuration(stock_code, df, 'rigid_and')
            all_results['results'][stock_code]['RIGID_AND'] = rigid_results
            
            # Test HIERARCHICAL (new Phase 1)
            hierarchical_results = self.backtest_configuration(stock_code, df, 'hierarchical')
            all_results['results'][stock_code]['HIERARCHICAL'] = hierarchical_results
            
            # Compare all three
            self._compare_all_configs(base_results, rigid_results, hierarchical_results)
        
        # Save results
        results_file = f"phase1_remediation_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        logger.info(f"\n✓ Results saved to {results_file}")
        return all_results
    
    def _compare_all_configs(self, base: Dict, rigid: Dict, hierarchical: Dict):
        """Compare all three configurations"""
        
        base_m = base.get('metrics', {})
        rigid_m = rigid.get('metrics', {})
        hier_m = hierarchical.get('metrics', {})
        
        if not base_m:
            return
        
        logger.info(f"\n{'='*70}")
        logger.info(f"CONFIGURATION COMPARISON - {base['stock_code']}")
        logger.info(f"{'='*70}")
        logger.info(f"{'Metric':<20} {'BASE':>12} {'RIGID_AND':>12} {'HIERARCHICAL':>12}")
        logger.info(f"{'-'*56}")
        logger.info(f"{'Trades':<20} {base_m.get('total_trades', 0):>12} {rigid_m.get('total_trades', 0):>12} {hier_m.get('total_trades', 0):>12}")
        logger.info(f"{'Win Rate (%)':<20} {base_m.get('win_rate', 0):>12.2f} {rigid_m.get('win_rate', 0):>12.2f} {hier_m.get('win_rate', 0):>12.2f}")
        logger.info(f"{'Return (%)':<20} {base_m.get('return_pct', 0):>12.2f} {rigid_m.get('return_pct', 0):>12.2f} {hier_m.get('return_pct', 0):>12.2f}")
        logger.info(f"{'Profit Factor':<20} {base_m.get('profit_factor', 0):>12.2f} {rigid_m.get('profit_factor', 0):>12.2f} {hier_m.get('profit_factor', 0):>12.2f}")
        logger.info(f"{'Sharpe Ratio':<20} {base_m.get('sharpe_ratio', 0):>12.2f} {rigid_m.get('sharpe_ratio', 0):>12.2f} {hier_m.get('sharpe_ratio', 0):>12.2f}")
        logger.info(f"{'Max Drawdown (%)':<20} {base_m.get('max_drawdown', 0):>12.2f} {rigid_m.get('max_drawdown', 0):>12.2f} {hier_m.get('max_drawdown', 0):>12.2f}")
        logger.info(f"{'='*70}\n")
        
        # Verdict
        hier_improvement = hier_m.get('profit_factor', 0) > rigid_m.get('profit_factor', 0)
        hier_maintains_dr = hier_m.get('max_drawdown', 0) >= rigid_m.get('max_drawdown', 0)  # Less negative is better
        
        logger.info("VERDICT:")
        if hier_m.get('total_trades', 0) > rigid_m.get('total_trades', 0):
            logger.info(f"✓ Hierarchical captures MORE trades ({hier_m.get('total_trades', 0)} vs {rigid_m.get('total_trades', 0)})")
        else:
            logger.info(f"⚠ Hierarchical takes fewer trades ({hier_m.get('total_trades', 0)} vs {rigid_m.get('total_trades', 0)})")
        
        if hier_m.get('profit_factor', 0) > rigid_m.get('profit_factor', 0):
            logger.info(f"✓ Hierarchical shows better profit factor ({hier_m.get('profit_factor', 0):.2f} vs {rigid_m.get('profit_factor', 0):.2f})")
        else:
            logger.info(f"⚠ Rigid AND shows better profit factor")
        
        if hier_m.get('win_rate', 0) >= rigid_m.get('win_rate', 0):
            logger.info(f"✓ Hierarchical maintains/improves win rate ({hier_m.get('win_rate', 0):.2f}% vs {rigid_m.get('win_rate', 0):.2f}%)")


def main():
    """Execute Phase 1 remediation backtest"""
    
    try:
        backtest = Phase1RemediationBacktest()
        
        test_securities = [
            'RELIND',
            'TCS',
            'INFTEC',
            'WIPRO',
            'BAFINS',
            'MARUTI',
        ]
        
        results = backtest.run_full_test(test_securities)
        
        logger.info("\n" + "="*70)
        logger.info("✓ PHASE 1 REMEDIATION BACKTEST COMPLETE")
        logger.info("="*70)
        
        return results
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
