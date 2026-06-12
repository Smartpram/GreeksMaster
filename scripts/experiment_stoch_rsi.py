#!/usr/bin/env python3
"""
Experiment 1: Stochastic RSI Integration Testing
Compare base system vs. Stochastic RSI momentum confirmation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime
from breeze_connect import BreezeConnect
import json
import logging
from typing import Dict, List, Tuple
from collections import defaultdict

from app.strategies.enhanced_signal_confirmation import EnhancedSignalConfirmation
from app.strategies.advanced_signal_validators import AdvancedSignalValidator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
from dotenv import load_dotenv
load_dotenv()


class StochRSIExperiment:
    """Experiment framework for Stochastic RSI testing"""
    
    def __init__(self, session_token: str):
        """Initialize experiment with Breeze connection"""
        self.breeze = BreezeConnect(api_key=os.getenv('BREEZE_API_KEY'))
        self.breeze.generate_session(session_token=session_token)
        self.session_token = session_token
        
        logger.info("✓ StochRSI Experiment initialized")
    
    def fetch_data(self, stock_code: str, days: int = 168) -> pd.DataFrame:
        """Fetch historical data from Breeze"""
        try:
            logger.info(f"Fetching {days} days of {stock_code} data...")
            
            historical_data = self.breeze.get_historical_data(
                interval="1day",
                from_date="01-Jan-2024",
                to_date="30-May-2026",
                stock_code=stock_code
            )
            
            if not historical_data:
                logger.error(f"No data retrieved for {stock_code}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime').sort_index()
            
            # Convert numeric columns
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Get last N days
            df = df.tail(days).copy()
            
            logger.info(f"✓ Fetched {len(df)} bars for {stock_code}")
            logger.info(f"  Price range: ₹{df['close'].min():.2f} - ₹{df['close'].max():.2f}")
            
            return df
        
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return None
    
    def backtest_base_system(self, stock_code: str, df: pd.DataFrame,
                           initial_capital: float = 100000) -> Dict:
        """Run backtest with BASE SYSTEM ONLY (no advanced indicators)"""
        
        logger.info(f"\n{'='*60}")
        logger.info(f"BACKTEST: BASE SYSTEM ONLY - {stock_code}")
        logger.info(f"{'='*60}")
        
        results = {
            'stock_code': stock_code,
            'system': 'BASE_ONLY',
            'entries': [],
            'exits': [],
            'trades': [],
            'metrics': {}
        }
        
        cash = initial_capital
        position = None  # {entry_price, entry_idx, entry_date, units}
        position_pl_list = []
        
        enhanced_signal = EnhancedSignalConfirmation(df)
        
        for bar_idx in range(20, len(df)):
            current_date = df.index[bar_idx]
            current_price = df['close'].iloc[bar_idx]
            
            # Entry logic: Base system only
            if position is None:
                entry_score = enhanced_signal.validate_entry_signal(bar_idx)
                
                if entry_score >= 0.50:
                    units = int(cash * 0.95 / current_price)
                    if units > 0:
                        position = {
                            'entry_price': current_price,
                            'entry_idx': bar_idx,
                            'entry_date': current_date,
                            'units': units,
                            'entry_score': entry_score
                        }
                        
                        results['entries'].append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'price': current_price,
                            'units': units,
                            'score': entry_score
                        })
                        
                        logger.info(f"ENTRY #{len(results['entries'])}: {current_date.date()} @ ₹{current_price:.2f} | Score: {entry_score:.3f}")
            
            # Exit logic
            elif position is not None:
                pnl = (current_price - position['entry_price']) * position['units']
                pnl_pct = (current_price - position['entry_price']) / position['entry_price'] * 100
                
                # Exit conditions
                should_exit = False
                exit_reason = None
                
                # Profit target: +5%
                if pnl_pct >= 5.0:
                    should_exit = True
                    exit_reason = "PROFIT_TARGET"
                
                # Stop loss: -2%
                elif pnl_pct <= -2.0:
                    should_exit = True
                    exit_reason = "STOP_LOSS"
                
                # Exit on signal degradation
                elif enhanced_signal.validate_entry_signal(bar_idx) < 0.30:
                    should_exit = True
                    exit_reason = "SIGNAL_DEGRADATION"
                
                if should_exit and exit_reason:
                    # Execute exit
                    cash = position['units'] * current_price
                    position_pl = pnl
                    position_pl_list.append(position_pl)
                    
                    results['exits'].append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'price': current_price,
                        'pnl': position_pl,
                        'pnl_pct': pnl_pct,
                        'reason': exit_reason
                    })
                    
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
                'avg_win': np.mean([p for p in position_pl_list if p > 0]) if wins > 0 else 0,
                'avg_loss': np.mean([p for p in position_pl_list if p < 0]) if losses > 0 else 0,
                'profit_factor': sum(p for p in position_pl_list if p > 0) / abs(sum(p for p in position_pl_list if p < 0)) if losses > 0 else 0,
                'max_drawdown': self._calculate_max_drawdown(position_pl_list),
                'sharpe_ratio': self._calculate_sharpe(position_pl_list)
            }
            
            logger.info(f"\n{'─'*60}")
            logger.info(f"BASE SYSTEM RESULTS:")
            logger.info(f"  Trades: {results['metrics']['total_trades']}")
            logger.info(f"  Win Rate: {results['metrics']['win_rate']:.2f}%")
            logger.info(f"  Total PnL: ₹{results['metrics']['total_pnl']:.0f}")
            logger.info(f"  Sharpe: {results['metrics']['sharpe_ratio']:.2f}")
            logger.info(f"  Max DD: {results['metrics']['max_drawdown']:.2f}%")
            logger.info(f"{'─'*60}\n")
        
        return results
    
    def backtest_with_stoch_rsi(self, stock_code: str, df: pd.DataFrame,
                               stoch_threshold: float = 0.50,
                               initial_capital: float = 100000) -> Dict:
        """Run backtest with STOCHASTIC RSI CONFIRMATION"""
        
        logger.info(f"\n{'='*60}")
        logger.info(f"BACKTEST: WITH STOCHASTIC RSI - {stock_code}")
        logger.info(f"Stochastic RSI threshold: {stoch_threshold}")
        logger.info(f"{'='*60}")
        
        results = {
            'stock_code': stock_code,
            'system': 'WITH_STOCH_RSI',
            'stoch_threshold': stoch_threshold,
            'entries': [],
            'exits': [],
            'trades': [],
            'metrics': {}
        }
        
        cash = initial_capital
        position = None
        position_pl_list = []
        
        enhanced_signal = EnhancedSignalConfirmation(df)
        advanced_validator = AdvancedSignalValidator(df)
        
        stoch_confirms = 0
        stoch_rejects = 0
        
        for bar_idx in range(20, len(df)):
            current_date = df.index[bar_idx]
            current_price = df['close'].iloc[bar_idx]
            
            # Entry logic: Base system + Stochastic RSI
            if position is None:
                entry_score = enhanced_signal.validate_entry_signal(bar_idx)
                
                if entry_score >= 0.50:
                    # NEW: Add Stochastic RSI confirmation
                    stoch_result = advanced_validator.validate_entry_with_stoch_rsi(
                        bar_idx, 
                        signal_type='BUY'
                    )
                    
                    # Entry valid only if BOTH conditions met
                    if stoch_result['score'] >= stoch_threshold:
                        units = int(cash * 0.95 / current_price)
                        if units > 0:
                            position = {
                                'entry_price': current_price,
                                'entry_idx': bar_idx,
                                'entry_date': current_date,
                                'units': units,
                                'entry_score': entry_score,
                                'stoch_score': stoch_result['score']
                            }
                            
                            results['entries'].append({
                                'date': current_date.strftime('%Y-%m-%d'),
                                'price': current_price,
                                'units': units,
                                'entry_score': entry_score,
                                'stoch_score': stoch_result['score']
                            })
                            
                            stoch_confirms += 1
                            logger.info(f"ENTRY #{len(results['entries'])}: {current_date.date()} @ ₹{current_price:.2f} | Base: {entry_score:.3f} | Stoch: {stoch_result['score']:.3f}")
                    else:
                        stoch_rejects += 1
                        # Signal rejected by Stochastic RSI
                        pass
            
            # Exit logic (same as base system)
            elif position is not None:
                pnl = (current_price - position['entry_price']) * position['units']
                pnl_pct = (current_price - position['entry_price']) / position['entry_price'] * 100
                
                should_exit = False
                exit_reason = None
                
                if pnl_pct >= 5.0:
                    should_exit = True
                    exit_reason = "PROFIT_TARGET"
                elif pnl_pct <= -2.0:
                    should_exit = True
                    exit_reason = "STOP_LOSS"
                elif enhanced_signal.validate_entry_signal(bar_idx) < 0.30:
                    should_exit = True
                    exit_reason = "SIGNAL_DEGRADATION"
                
                if should_exit and exit_reason:
                    cash = position['units'] * current_price
                    position_pl = pnl
                    position_pl_list.append(position_pl)
                    
                    results['exits'].append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'price': current_price,
                        'pnl': position_pl,
                        'pnl_pct': pnl_pct,
                        'reason': exit_reason
                    })
                    
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
            
            results['metrics'] = {
                'total_trades': len(position_pl_list),
                'winning_trades': wins,
                'losing_trades': losses,
                'breakeven_trades': sum(1 for p in position_pl_list if p == 0),
                'win_rate': wins / len(position_pl_list) * 100 if position_pl_list else 0,
                'total_pnl': total_pnl,
                'avg_win': np.mean([p for p in position_pl_list if p > 0]) if wins > 0 else 0,
                'avg_loss': np.mean([p for p in position_pl_list if p < 0]) if losses > 0 else 0,
                'profit_factor': sum(p for p in position_pl_list if p > 0) / abs(sum(p for p in position_pl_list if p < 0)) if losses > 0 else 0,
                'max_drawdown': self._calculate_max_drawdown(position_pl_list),
                'sharpe_ratio': self._calculate_sharpe(position_pl_list),
                'stoch_confirms': stoch_confirms,
                'stoch_rejects': stoch_rejects
            }
            
            logger.info(f"\n{'─'*60}")
            logger.info(f"STOCHASTIC RSI SYSTEM RESULTS:")
            logger.info(f"  Trades: {results['metrics']['total_trades']}")
            logger.info(f"  Stoch Confirms: {stoch_confirms} | Rejects: {stoch_rejects}")
            logger.info(f"  Win Rate: {results['metrics']['win_rate']:.2f}%")
            logger.info(f"  Total PnL: ₹{results['metrics']['total_pnl']:.0f}")
            logger.info(f"  Sharpe: {results['metrics']['sharpe_ratio']:.2f}")
            logger.info(f"  Max DD: {results['metrics']['max_drawdown']:.2f}%")
            logger.info(f"{'─'*60}\n")
        
        return results
    
    def compare_results(self, base_results: Dict, stoch_results: Dict) -> Dict:
        """Compare base system vs Stochastic RSI system"""
        
        comparison = {
            'timestamp': datetime.now().isoformat(),
            'stock': base_results['stock_code'],
            'base_metrics': base_results.get('metrics', {}),
            'stoch_metrics': stoch_results.get('metrics', {}),
            'improvements': {}
        }
        
        base_metrics = base_results.get('metrics', {})
        stoch_metrics = stoch_results.get('metrics', {})
        
        if base_metrics and stoch_metrics:
            comparison['improvements'] = {
                'trades_change': stoch_metrics.get('total_trades', 0) - base_metrics.get('total_trades', 0),
                'win_rate_change': stoch_metrics.get('win_rate', 0) - base_metrics.get('win_rate', 0),
                'pnl_change': stoch_metrics.get('total_pnl', 0) - base_metrics.get('total_pnl', 0),
                'pnl_pct_change': (stoch_metrics.get('total_pnl', 0) / base_metrics.get('total_pnl', 1)) * 100 - 100 if base_metrics.get('total_pnl', 0) != 0 else 0,
                'sharpe_change': stoch_metrics.get('sharpe_ratio', 0) - base_metrics.get('sharpe_ratio', 0),
                'drawdown_change': stoch_metrics.get('max_drawdown', 0) - base_metrics.get('max_drawdown', 0)
            }
            
            logger.info(f"\n{'='*60}")
            logger.info(f"COMPARISON: BASE vs STOCHASTIC RSI - {base_results['stock_code']}")
            logger.info(f"{'='*60}")
            logger.info(f"Trades:        {base_metrics.get('total_trades', 0):>3} → {stoch_metrics.get('total_trades', 0):>3} ({comparison['improvements']['trades_change']:+d})")
            logger.info(f"Win Rate:      {base_metrics.get('win_rate', 0):>6.2f}% → {stoch_metrics.get('win_rate', 0):>6.2f}% ({comparison['improvements']['win_rate_change']:+.2f}%)")
            logger.info(f"Total PnL:     ₹{base_metrics.get('total_pnl', 0):>8.0f} → ₹{stoch_metrics.get('total_pnl', 0):>8.0f} ({comparison['improvements']['pnl_change']:+.0f})")
            logger.info(f"Sharpe:        {base_metrics.get('sharpe_ratio', 0):>6.2f} → {stoch_metrics.get('sharpe_ratio', 0):>6.2f} ({comparison['improvements']['sharpe_change']:+.2f})")
            logger.info(f"Max Drawdown:  {base_metrics.get('max_drawdown', 0):>6.2f}% → {stoch_metrics.get('max_drawdown', 0):>6.2f}% ({comparison['improvements']['drawdown_change']:+.2f}%)")
            logger.info(f"{'='*60}\n")
            
            # Decision logic
            pnl_improved = comparison['improvements']['pnl_change'] > 0
            sharpe_maintained = comparison['improvements']['sharpe_change'] >= -0.1
            win_rate_good = stoch_metrics.get('win_rate', 0) >= 65
            
            if pnl_improved and sharpe_maintained and win_rate_good:
                comparison['recommendation'] = "✅ KEEP - Stochastic RSI improves profitability"
            elif comparison['improvements']['pnl_pct_change'] > 1 and sharpe_maintained:
                comparison['recommendation'] = "✅ KEEP - At least 1% improvement with maintained risk"
            else:
                comparison['recommendation'] = "❌ DISCARD - No clear benefit, complexity not justified"
            
            logger.info(f"RECOMMENDATION: {comparison['recommendation']}")
        
        return comparison
    
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
        """Calculate Sharpe ratio from returns"""
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - risk_free_rate
        
        if np.std(excess_returns) == 0:
            return 0.0
        
        # Annualized (assuming 252 trading days)
        sharpe = (np.mean(excess_returns) / np.std(excess_returns)) * np.sqrt(252)
        
        return sharpe
    
    def run_experiment(self, stocks: List[str], session_token: str) -> Dict:
        """Run complete experiment: Base vs Stoch RSI"""
        
        all_results = {
            'experiment': 'STOCHASTIC_RSI_INTEGRATION',
            'timestamp': datetime.now().isoformat(),
            'stocks': {}
        }
        
        for stock_code in stocks:
            logger.info(f"\n{'#'*60}")
            logger.info(f"# EXPERIMENTING WITH {stock_code}")
            logger.info(f"{'#'*60}\n")
            
            # Fetch data
            df = self.fetch_data(stock_code)
            if df is None or len(df) < 50:
                logger.error(f"Insufficient data for {stock_code}")
                continue
            
            # Run backtests
            base_results = self.backtest_base_system(stock_code, df)
            stoch_results = self.backtest_with_stoch_rsi(stock_code, df, stoch_threshold=0.50)
            
            # Compare
            comparison = self.compare_results(base_results, stoch_results)
            
            all_results['stocks'][stock_code] = {
                'base': base_results,
                'stoch_rsi': stoch_results,
                'comparison': comparison
            }
        
        # Save results
        results_file = f"stoch_rsi_experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            # Convert to serializable format
            def serialize(obj):
                if isinstance(obj, pd.Timestamp):
                    return obj.isoformat()
                return str(obj)
            
            json.dump(all_results, f, indent=2, default=serialize)
        
        logger.info(f"\n✓ Results saved to {results_file}")
        
        return all_results


def main():
    """Run Stochastic RSI experiment"""
    
    # Get session token from env
    session_token = os.getenv('BREEZE_SESSION_TOKEN')
    if not session_token:
        logger.error("BREEZE_SESSION_TOKEN not found in .env")
        return
    
    # Initialize experiment
    experiment = StochRSIExperiment(session_token)
    
    # Run experiment on RELIND and TCS
    results = experiment.run_experiment(['RELIND', 'TCS'], session_token)
    
    logger.info("\n" + "="*60)
    logger.info("EXPERIMENT COMPLETE")
    logger.info("="*60)


if __name__ == "__main__":
    main()
