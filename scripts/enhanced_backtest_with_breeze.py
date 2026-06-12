#!/usr/bin/env python3
"""
Enhanced Backtest with Breeze API Data
Using Multi-Layer Signal Confirmation System
Improved entry/exit logic with regime detection
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import json
import logging
from typing import Dict, List, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import your components
from app.services.breeze_api import BreezeAPIService
from app.services.data_stream import HistoricalDataService
from app.strategies.enhanced_signal_confirmation import EnhancedSignalConfirmation
from app.services.risk_manager import RiskManager
from app.config import Config

class EnhancedBreezeBacktestEngine:
    """Enhanced backtest engine using multi-layer signal confirmation"""
    
    def __init__(self, initial_capital: float = 300000):
        """Initialize enhanced backtest with Breeze connection"""
        self.initial_capital = initial_capital
        self.config = Config()
        
        # Initialize Breeze API
        try:
            self.breeze_service = BreezeAPIService()
            logger.info("✓ Breeze API service initialized")
            
            # Authenticate with Breeze API
            logger.info("🔐 Authenticating with Breeze API...")
            auth_result = self.breeze_service.authenticate()
            
            if auth_result['success']:
                logger.info(f"✓ Authenticated successfully!")
                logger.info(f"  User: {auth_result.get('user_name', 'Unknown')}")
                logger.info(f"  Trading enabled: Yes")
            else:
                logger.error(f"✗ Authentication failed: {auth_result.get('error', 'Unknown error')}")
                raise Exception(f"Breeze API authentication failed: {auth_result.get('error')}")
                
        except Exception as e:
            logger.error(f"✗ Failed to initialize Breeze API: {e}")
            raise
        
        # Initialize risk manager
        self.risk_manager = RiskManager()
        
    def fetch_data(self, stock_code: str, days: int = 252) -> Tuple[bool, pd.DataFrame]:
        """Fetch historical data from Breeze API"""
        try:
            logger.info(f"\n{'='*80}")
            logger.info(f"Fetching real Breeze data for {stock_code}")
            logger.info(f"{'='*80}")
            
            logger.info(f"Requesting {days} days of historical data...")
            
            # Fetch historical data
            result = self.breeze_service.get_historical_data(
                stock_code=stock_code,
                interval="day",
                days_back=days
            )
            
            if result['success']:
                historical_data = result.get('data', [])
                
                if not historical_data:
                    raise ValueError(f"No data returned for {stock_code}")
                
                # Convert to DataFrame
                df = pd.DataFrame(historical_data)
                
                # Handle datetime column - API returns it already as datetime
                if 'datetime' in df.columns:
                    df['datetime'] = pd.to_datetime(df['datetime'])
                elif 'date' in df.columns:
                    df['datetime'] = pd.to_datetime(df['date'], format='%d-%b-%Y')
                else:
                    df['datetime'] = pd.to_datetime(df.index)
                
                df = df.set_index('datetime')
                df = df.sort_index()
                
                # Rename columns to lowercase and standard format
                df.columns = df.columns.str.lower()
                
                # Convert numeric columns to float
                numeric_cols = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                logger.info(f"✓ Fetched {len(df)} candles")
                logger.info(f"✓ Data range: {df.index.min().date()} to {df.index.max().date()}")
                
                # Handle case where 'low' or 'high' might not exist
                if 'low' in df.columns and 'high' in df.columns:
                    logger.info(f"✓ Price range: ₹{df['low'].min():.2f} - ₹{df['high'].max():.2f}")
                elif 'close' in df.columns:
                    logger.info(f"✓ Price range: ₹{df['close'].min():.2f} - ₹{df['close'].max():.2f}")
                
                if 'volume' in df.columns:
                    logger.info(f"✓ Avg Volume: {int(df['volume'].mean()):,}")
                
                return True, df
            else:
                logger.error(f"API Error: {result.get('error', 'Unknown error')}")
                return False, None
                
        except Exception as e:
            logger.error(f"✗ Error fetching data: {e}")
            return False, None
    
    def backtest_strategy(self, stock_code: str, df: pd.DataFrame) -> Dict:
        """Run enhanced backtest on real data with multi-layer signal confirmation
        
        Args:
            stock_code: Stock code for logging
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with backtest results
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"ENHANCED BACKTEST: {stock_code} WITH MULTI-LAYER SIGNAL CONFIRMATION")
        logger.info(f"{'='*80}")
        
        capital = self.initial_capital
        position = None
        trades = []
        portfolio_values = [capital]
        signal_scores = []
        regime_history = []
        
        # Initialize enhanced signal confirmation
        enhanced_signals = EnhancedSignalConfirmation(df)
        
        for bar_count, (idx, row) in enumerate(df.iterrows()):
            current_price = row['close']
            
            # Only process if we have enough data
            if bar_count < 20:
                continue
            
            # Detect market regime
            regime = enhanced_signals.detect_regime(bar_count)
            regime_history.append({
                'date': idx,
                'regime': regime.value
            })
            
            # Entry logic with enhanced signal confirmation
            if position is None:
                # Validate entry signal
                validation = enhanced_signals.validate_entry_signal(bar_count, 'BUY')
                
                if validation['valid'] and validation['overall_score'] >= 0.60:
                    # Entry allowed by enhanced signals
                    shares = int(capital * 0.95 / current_price)
                    cost = shares * current_price
                    capital -= cost
                    position = {
                        'entry_price': current_price,
                        'shares': shares,
                        'entry_date': idx,
                        'entry_score': validation['overall_score'],
                        'regime': regime.value
                    }
                    logger.info(f"✓ ENTRY at {idx.date()}: ₹{current_price:.2f} ({shares} shares) "
                              f"[Score: {validation['overall_score']:.2f}, Regime: {regime.value}]")
                    
                    signal_scores.append({
                        'date': idx,
                        'type': 'ENTRY',
                        'score': validation['overall_score'],
                        'regime': regime.value
                    })
                
            # Exit logic
            elif position is not None:
                pnl_pct = (current_price - position['entry_price']) / position['entry_price'] * 100
                
                # Get exit recommendations from enhanced signals
                recommendations = enhanced_signals.get_position_recommendations(bar_count, position)
                
                # Exit conditions
                should_exit = False
                exit_reason = ""
                
                if pnl_pct >= 5:  # Take profit
                    should_exit = True
                    exit_reason = "PROFIT_TARGET (5%)"
                elif pnl_pct <= -2:  # Stop loss
                    should_exit = True
                    exit_reason = "STOP_LOSS (-2%)"
                elif recommendations.get('exit_on_macd_divergence', False):
                    should_exit = True
                    exit_reason = "MACD_DIVERGENCE"
                elif recommendations.get('exit_on_ma_break', False):
                    should_exit = True
                    exit_reason = "MA_BREAK"
                elif recommendations.get('hold_position', False) is False:
                    should_exit = True
                    exit_reason = "SIGNAL_DEGRADATION"
                
                if should_exit:
                    proceeds = position['shares'] * current_price
                    trade_pnl = proceeds - (position['shares'] * position['entry_price'])
                    capital += proceeds
                    
                    trades.append({
                        'entry_date': position['entry_date'],
                        'entry_price': position['entry_price'],
                        'entry_score': position['entry_score'],
                        'exit_date': idx,
                        'exit_price': current_price,
                        'shares': position['shares'],
                        'pnl': trade_pnl,
                        'pnl_pct': pnl_pct,
                        'regime_at_entry': position['regime'],
                        'regime_at_exit': regime.value,
                        'exit_reason': exit_reason
                    })
                    
                    logger.info(f"✓ EXIT at {idx.date()}: ₹{current_price:.2f} | "
                              f"PnL: ₹{trade_pnl:.0f} ({pnl_pct:+.2f}%) | Reason: {exit_reason}")
                    
                    position = None
            
            # Update portfolio value
            if position is not None:
                portfolio_value = capital + (position['shares'] * current_price)
            else:
                portfolio_value = capital
            portfolio_values.append(portfolio_value)
        
        # Close any open position at end
        if position is not None:
            final_price = df.iloc[-1]['close']
            proceeds = position['shares'] * final_price
            trade_pnl = proceeds - (position['shares'] * position['entry_price'])
            capital += proceeds
            
            trades.append({
                'entry_date': position['entry_date'],
                'entry_price': position['entry_price'],
                'entry_score': position['entry_score'],
                'exit_date': df.index[-1],
                'exit_price': final_price,
                'shares': position['shares'],
                'pnl': trade_pnl,
                'pnl_pct': (final_price - position['entry_price']) / position['entry_price'] * 100,
                'regime_at_entry': position['regime'],
                'regime_at_exit': regime.value,
                'exit_reason': 'END_OF_PERIOD'
            })
        
        # Calculate metrics
        final_capital = capital
        total_return_pct = ((final_capital - self.initial_capital) / self.initial_capital) * 100
        
        if len(trades) > 0:
            winning_trades = len([t for t in trades if t['pnl'] > 0])
            losing_trades = len([t for t in trades if t['pnl'] < 0])
            win_rate = (winning_trades / len(trades)) * 100 if len(trades) > 0 else 0
            avg_win = sum([t['pnl'] for t in trades if t['pnl'] > 0]) / winning_trades if winning_trades > 0 else 0
            avg_loss = sum([t['pnl'] for t in trades if t['pnl'] < 0]) / losing_trades if losing_trades > 0 else 0
        else:
            winning_trades = 0
            losing_trades = 0
            win_rate = 0
            avg_win = 0
            avg_loss = 0
        
        # Calculate Sharpe Ratio
        if len(portfolio_values) > 1:
            returns = np.diff(portfolio_values) / portfolio_values[:-1]
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Calculate Max Drawdown
        cumulative = np.array(portfolio_values)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdown) * 100
        
        # Prepare results
        results = {
            'stock_code': stock_code,
            'period': {
                'start': str(df.index.min().date()),
                'end': str(df.index.max().date()),
                'bars': len(df)
            },
            'capital': {
                'initial': self.initial_capital,
                'final': final_capital,
                'pnl': final_capital - self.initial_capital,
                'return_pct': total_return_pct
            },
            'trades': {
                'total': len(trades),
                'winning': winning_trades,
                'losing': losing_trades,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': sum([t['pnl'] for t in trades if t['pnl'] > 0]) / abs(sum([t['pnl'] for t in trades if t['pnl'] < 0])) if losing_trades > 0 else 0
            },
            'risk': {
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio
            },
            'trades_detail': trades,
            'regime_history': regime_history[-20:]  # Last 20 regimes
        }
        
        # Print results
        self._print_results(results)
        
        return results
    
    def _print_results(self, results: Dict):
        """Print formatted backtest results"""
        logger.info("")
        logger.info("="*90)
        logger.info(f"ENHANCED BACKTEST RESULTS: {results['stock_code']}")
        logger.info("="*90)
        
        logger.info(f"\n📊 PERIOD: {results['period']['start']} to {results['period']['end']}")
        
        logger.info(f"\n💰 CAPITAL PERFORMANCE")
        logger.info(f"  Initial Capital:        ₹ {results['capital']['initial']:>12,.0f}")
        logger.info(f"  Final Capital:          ₹ {results['capital']['final']:>12,.0f}")
        logger.info(f"  Profit/Loss:            ₹ {results['capital']['pnl']:>12,.0f}")
        logger.info(f"  Total Return:           {results['capital']['return_pct']:>13.2f}%")
        
        logger.info(f"\n📈 TRADE STATISTICS")
        logger.info(f"  Total Trades:           {results['trades']['total']:>14}")
        logger.info(f"  Winning Trades:         {results['trades']['winning']:>14}")
        logger.info(f"  Losing Trades:          {results['trades']['losing']:>14}")
        logger.info(f"  Win Rate:               {results['trades']['win_rate']:>13.2f}%")
        logger.info(f"  Avg Win:                ₹ {results['trades']['avg_win']:>12,.0f}")
        logger.info(f"  Avg Loss:               ₹ {results['trades']['avg_loss']:>12,.0f}")
        logger.info(f"  Profit Factor:          {results['trades']['profit_factor']:>13.2f}")
        
        logger.info(f"\n⚠️  RISK METRICS")
        logger.info(f"  Max Drawdown:           {results['risk']['max_drawdown']:>13.2f}%")
        logger.info(f"  Sharpe Ratio:           {results['risk']['sharpe_ratio']:>13.2f}")
        
        logger.info("\n" + "="*90 + "\n")
    
    def run_backtest(self, stocks: List[str] = None):
        """Run backtest for multiple stocks"""
        if stocks is None:
            stocks = ['RELIND', 'TCS']
        
        all_results = []
        
        for stock_code in stocks:
            success, df = self.fetch_data(stock_code)
            
            if success:
                results = self.backtest_strategy(stock_code, df)
                all_results.append(results)
                
                # Save results
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"enhanced_backtest_{stock_code}_{timestamp}.json"
                with open(filename, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                logger.info(f"✓ Results saved to {filename}")
            else:
                logger.error(f"✗ Error backtesting {stock_code}")
        
        # Print comparison
        if len(all_results) > 1:
            self._print_comparison(all_results)
    
    def _print_comparison(self, results_list: List[Dict]):
        """Print comparison across stocks"""
        logger.info("\n" + "="*90)
        logger.info("COMPARISON ACROSS STOCKS")
        logger.info("="*90)
        logger.info("")
        logger.info(f"{'Stock':<10} {'Return':<12} {'Win Rate':<12} {'Avg Win':<15} {'Avg Loss':<15} {'Drawdown':<10}")
        logger.info("-"*90)
        
        for result in results_list:
            stock = result['stock_code']
            ret = result['capital']['return_pct']
            win_rate = result['trades']['win_rate']
            avg_win = result['trades']['avg_win']
            avg_loss = result['trades']['avg_loss']
            dd = result['risk']['max_drawdown']
            
            logger.info(f"{stock:<10} {ret:>10.2f}% {win_rate:>10.2f}% "
                       f"₹{avg_win:>12,.0f} ₹{avg_loss:>12,.0f} {dd:>8.2f}%")
        
        logger.info("="*90 + "\n")

def main():
    """Main execution"""
    try:
        logger.info("\n" + "#"*90)
        logger.info("# ENHANCED BREEZE REAL DATA BACKTEST - MULTI-LAYER SIGNAL CONFIRMATION")
        logger.info("# Stocks: RELIND, TCS | Period: 252 days")
        logger.info("# Strategy: Buy & Hold with Regime Detection + Multi-Layer Validation")
        logger.info("#"*90 + "\n")
        
        engine = EnhancedBreezeBacktestEngine(initial_capital=300000)
        engine.run_backtest(stocks=['RELIND', 'TCS'])
        
        logger.info("\n✓ Backtest completed successfully!")
        
    except Exception as e:
        logger.error(f"✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
