#!/usr/bin/env python3
"""
Backtest with Real Breeze API Data
Buy-Hold-Trend Strategy with Market Time Filter
Validates strategy against actual NSE market data
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
from app.strategies.market_time_filter import MarketTimeFilter
from app.services.risk_manager import RiskManager
from app.strategies.enhanced_signal_confirmation import EnhancedSignalConfirmation
from app.config import Config

class BreezeBacktestEngine:
    """Backtest engine using real Breeze API data"""
    
    def __init__(self, initial_capital: float = 300000):
        """Initialize backtest with Breeze connection"""
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
        
        # Initialize other components
        self.historical_service = HistoricalDataService(self.breeze_service)
        self.market_filter = MarketTimeFilter()
        self.risk_manager = RiskManager()
    
    def fetch_historical_data(self, stock_code: str, days_back: int = 252) -> pd.DataFrame:
        """Fetch real historical data from Breeze API
        
        Args:
            stock_code: NSE stock code (e.g., 'INFY', 'RELIND')
            days_back: Number of days of historical data
            
        Returns:
            DataFrame with OHLCV data
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"Fetching real Breeze data for {stock_code}")
        logger.info(f"{'='*80}")
        logger.info(f"Requesting {days_back} days of historical data...")
        
        try:
            # Fetch from Breeze using correct API format
            # Note: interval should be "day" (not "1day"), and stock_code format matters
            response = self.breeze_service.get_historical_data(
                stock_code=stock_code,
                exchange_code="NSE",
                product_type="cash",
                interval="day",
                days_back=days_back
            )
            
            if not response.get('success'):
                error_msg = response.get('error', 'Unknown error')
                logger.error(f"API Error: {error_msg}")
                raise ValueError(f"Failed to fetch data: {error_msg}")
            
            historical_data = response.get('data', [])
            
            if not historical_data:
                raise ValueError(f"No data returned for {stock_code}")
            
            logger.info(f"✓ Fetched {len(historical_data)} candles")
            
            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            
            # The API returns data with 'date' as string, convert it to datetime
            if 'date' in df.columns:
                df['datetime'] = pd.to_datetime(df['date'], format='%d-%b-%Y')
            elif 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'])
            else:
                df['datetime'] = pd.to_datetime(df.index)
            
            df = df.set_index('datetime')
            df = df.sort_index()
            
            # Rename columns to lowercase and standard format
            df.columns = df.columns.str.lower()
            
            # Ensure we have the required OHLCV columns
            if 'close' not in df.columns:
                df['close'] = df.get('c', df.get('close_price', None))
            if 'open' not in df.columns:
                df['open'] = df.get('o', df.get('open_price', None))
            if 'high' not in df.columns:
                df['high'] = df.get('h', df.get('high_price', None))
            if 'low' not in df.columns:
                df['low'] = df.get('l', df.get('low_price', None))
            if 'volume' not in df.columns:
                df['volume'] = df.get('v', df.get('volume', 0))
            
            # Convert price columns to float
            for col in ['open', 'high', 'low', 'close']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
            
            logger.info(f"✓ Data range: {df.index[0].date()} to {df.index[-1].date()}")
            logger.info(f"✓ Price range: ₹{df['low'].min():.2f} - ₹{df['high'].max():.2f}")
            logger.info(f"✓ Avg Volume: {df['volume'].mean():,.0f}")
            
            return df
            
        except Exception as e:
            logger.error(f"✗ Error fetching data: {e}")
            raise
    
    def backtest_strategy(self, stock_code: str, df: pd.DataFrame) -> Dict:
        """Run backtest on real data
        
        Args:
            stock_code: Stock code for logging
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with backtest results
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"BACKTEST: {stock_code} WITH MARKET TIME FILTER")
        logger.info(f"{'='*80}")
        
        capital = self.initial_capital
        position = None
        trades = []
        portfolio_values = [capital]
        entry_blocks = []
        gap_skips = []
        
        for bar_count, (idx, row) in enumerate(df.iterrows()):
            current_price = row['close']
            
            # Calculate technical indicators
            if bar_count >= 20:  # Need 20 periods for MA
                ma20 = df['close'].loc[:idx].tail(20).mean()
                rsi = self._calculate_rsi(df['close'].loc[:idx].values)
                
                # Entry logic with market time filter
                if position is None and current_price > ma20 and rsi < 70:
                    
                    # Check market time filter
                    session = self.market_filter.get_current_session()
                    should_avoid = self.market_filter.should_avoid_entry()
                    
                    if should_avoid:
                        entry_blocks.append({
                            'date': idx,
                            'price': current_price,
                            'session': session,
                            'reason': f'Avoided entry during {session}'
                        })
                        logger.warning(f"BLOCKED entry at {idx.date()}: {session} session")
                    else:
                        # Check for gap
                        if bar_count > 0:
                            prev_close = df['close'].iloc[bar_count - 1] if bar_count > 0 else current_price
                            is_gap, gap_pct = self.market_filter.detect_gap(prev_close, current_price)
                            
                            if is_gap and self.market_filter.should_skip_gap_trades():
                                gap_skips.append({
                                    'date': idx,
                                    'price': current_price,
                                    'gap_pct': gap_pct,
                                    'reason': 'Gap detected'
                                })
                                logger.warning(f"SKIPPED gap trade at {idx.date()}: {gap_pct:.2f}% gap")
                                continue
                        
                        # Entry allowed
                        shares = int(capital * 0.95 / current_price)
                        cost = shares * current_price
                        capital -= cost
                        position = {
                            'entry_price': current_price,
                            'shares': shares,
                            'entry_date': idx,
                            'session': session,
                            'ma20': ma20,
                            'rsi': rsi
                        }
                        logger.info(f"✓ ENTRY at {idx.date()}: ₹{current_price:.2f} ({shares} shares) [{session}]")
                
                # Exit logic
                elif position is not None:
                    pnl_pct = (current_price - position['entry_price']) / position['entry_price'] * 100
                    
                    # Calculate dynamic stop loss
                    sl_price = self.risk_manager.calculate_stop_loss(
                        entry_price=position['entry_price'],
                        action='BUY',
                        custom_sl_percent=0.02
                    )
                    sl_pct = (position['entry_price'] - sl_price) / position['entry_price'] * 100
                    
                    # Exit conditions
                    if pnl_pct >= 5:  # Take profit
                        proceeds = position['shares'] * current_price
                        trade_pnl = proceeds - (position['shares'] * position['entry_price'])
                        capital += proceeds
                        
                        trades.append({
                            'entry_date': position['entry_date'],
                            'entry_price': position['entry_price'],
                            'entry_session': position['session'],
                            'exit_date': idx,
                            'exit_price': current_price,
                            'exit_session': self.market_filter.get_current_session(),
                            'shares': position['shares'],
                            'pnl': trade_pnl,
                            'pnl_pct': pnl_pct,
                            'exit_reason': 'TP',
                            'ma20_at_entry': position['ma20'],
                            'rsi_at_entry': position['rsi']
                        })
                        logger.info(f"✓ EXIT (TP) at {idx.date()}: ₹{current_price:.2f} | PnL: ₹{trade_pnl:,.0f} ({pnl_pct:.2f}%)")
                        position = None
                    
                    elif pnl_pct <= -sl_pct:  # Stop loss
                        proceeds = position['shares'] * current_price
                        trade_pnl = proceeds - (position['shares'] * position['entry_price'])
                        capital += proceeds
                        
                        trades.append({
                            'entry_date': position['entry_date'],
                            'entry_price': position['entry_price'],
                            'entry_session': position['session'],
                            'exit_date': idx,
                            'exit_price': current_price,
                            'exit_session': self.market_filter.get_current_session(),
                            'shares': position['shares'],
                            'pnl': trade_pnl,
                            'pnl_pct': pnl_pct,
                            'exit_reason': 'SL',
                            'ma20_at_entry': position['ma20'],
                            'rsi_at_entry': position['rsi']
                        })
                        logger.info(f"✓ EXIT (SL) at {idx.date()}: ₹{current_price:.2f} | PnL: ₹{trade_pnl:,.0f} ({pnl_pct:.2f}%)")
                        position = None
            
            # Update portfolio value
            if position is not None:
                position_value = position['shares'] * current_price
                portfolio_values.append(capital + position_value)
            else:
                portfolio_values.append(capital)
        
        # Close any open position at end
        if position is not None:
            last_price = df['close'].iloc[-1]
            proceeds = position['shares'] * last_price
            trade_pnl = proceeds - (position['shares'] * position['entry_price'])
            capital += proceeds
            final_pnl_pct = (last_price - position['entry_price']) / position['entry_price'] * 100
            trades.append({
                'entry_date': position['entry_date'],
                'entry_price': position['entry_price'],
                'exit_date': df.index[-1],
                'exit_price': last_price,
                'shares': position['shares'],
                'pnl': trade_pnl,
                'pnl_pct': final_pnl_pct,
                'exit_reason': 'EOB'
            })
        
        # Calculate metrics
        results = {
            'stock_code': stock_code,
            'start_date': df.index[0].date(),
            'end_date': df.index[-1].date(),
            'initial_capital': self.initial_capital,
            'final_capital': capital,
            'total_return': (capital - self.initial_capital) / self.initial_capital * 100,
            'total_trades': len(trades),
            'winning_trades': len([t for t in trades if t['pnl'] > 0]),
            'losing_trades': len([t for t in trades if t['pnl'] < 0]),
            'win_rate': len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100 if trades else 0,
            'avg_win': np.mean([t['pnl'] for t in trades if t['pnl'] > 0]) if any(t['pnl'] > 0 for t in trades) else 0,
            'avg_loss': np.mean([t['pnl'] for t in trades if t['pnl'] < 0]) if any(t['pnl'] < 0 for t in trades) else 0,
            'max_drawdown': self._calculate_max_drawdown(portfolio_values),
            'sharpe_ratio': self._calculate_sharpe_ratio(portfolio_values),
            'entry_blocks': len(entry_blocks),
            'gap_skips': len(gap_skips),
            'trades': trades,
            'portfolio_values': portfolio_values,
            'entry_blocks_detail': entry_blocks,
            'gap_skips_detail': gap_skips
        }
        
        return results
    
    @staticmethod
    def _calculate_rsi(prices, period=14):
        """Calculate RSI indicator"""
        if len(prices) < period:
            return 50
        
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100 if avg_gain > 0 else 50
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def _calculate_max_drawdown(portfolio_values):
        """Calculate maximum drawdown"""
        if not portfolio_values or len(portfolio_values) < 2:
            return 0
        
        portfolio_array = np.array(portfolio_values)
        cumulative_returns = portfolio_array / portfolio_array[0]
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max * 100
        return np.min(drawdown)
    
    @staticmethod
    def _calculate_sharpe_ratio(portfolio_values, risk_free_rate=0.05):
        """Calculate Sharpe ratio"""
        if len(portfolio_values) < 2:
            return 0
        
        returns = np.diff(portfolio_values) / portfolio_values[:-1]
        excess_returns = returns - (risk_free_rate / 252)
        
        if np.std(excess_returns) == 0:
            return 0
        
        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        return sharpe
    
    def print_results(self, results: Dict):
        """Print formatted backtest results"""
        print(f"\n{'='*90}")
        print(f"BACKTEST RESULTS: {results['stock_code']}")
        print(f"{'='*90}")
        
        print(f"\n📊 PERIOD: {results['start_date']} to {results['end_date']}")
        
        print(f"\n💰 CAPITAL PERFORMANCE")
        print(f"  Initial Capital:        ₹{results['initial_capital']:>12,.0f}")
        print(f"  Final Capital:          ₹{results['final_capital']:>12,.0f}")
        print(f"  Profit/Loss:            ₹{results['final_capital'] - results['initial_capital']:>12,.0f}")
        print(f"  Total Return:           {results['total_return']:>12.2f}%")
        
        print(f"\n📈 TRADE STATISTICS")
        print(f"  Total Trades:           {results['total_trades']:>12}")
        print(f"  Winning Trades:         {results['winning_trades']:>12}")
        print(f"  Losing Trades:          {results['losing_trades']:>12}")
        print(f"  Win Rate:               {results['win_rate']:>12.2f}%")
        print(f"  Avg Win:                ₹{results['avg_win']:>12,.0f}")
        print(f"  Avg Loss:               ₹{results['avg_loss']:>12,.0f}")
        
        if results['avg_loss'] != 0:
            profit_factor = abs(results['avg_win'] / results['avg_loss'])
            print(f"  Profit Factor:          {profit_factor:>12.2f}")
        
        print(f"\n⚠️  RISK METRICS")
        print(f"  Max Drawdown:           {results['max_drawdown']:>12.2f}%")
        print(f"  Sharpe Ratio:           {results['sharpe_ratio']:>12.2f}")
        
        print(f"\n🛡️  MARKET TIME FILTER IMPACT")
        print(f"  Entry Blocks:           {results['entry_blocks']:>12} (risky sessions avoided)")
        print(f"  Gap Skips:              {results['gap_skips']:>12} (gap trades avoided)")
        
        print(f"\n{'='*90}\n")
    
    def save_results(self, results: Dict, stock_code: str):
        """Save results to JSON file"""
        filename = f"backtest_breeze_{stock_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"✓ Results saved to {filename}")
        return filename

def run_backtest_for_stocks(stock_codes: List[str], days_back: int = 252):
    """Run backtest for multiple stocks
    
    Args:
        stock_codes: List of NSE stock codes (e.g., ['INFY', 'RELIANCE', 'TCS'])
        days_back: Number of days of historical data
    """
    logger.info(f"\n{'#'*90}")
    logger.info(f"# BREEZE REAL DATA BACKTEST - MARKET TIME FILTER STRATEGY")
    logger.info(f"# Stocks: {', '.join(stock_codes)} | Period: {days_back} days")
    logger.info(f"{'#'*90}\n")
    
    try:
        backtest = BreezeBacktestEngine(initial_capital=300000)
        
        all_results = {}
        
        for stock_code in stock_codes:
            try:
                # Fetch real data
                df = backtest.fetch_historical_data(stock_code, days_back)
                
                # Run backtest
                results = backtest.backtest_strategy(stock_code, df)
                
                # Print results
                backtest.print_results(results)
                
                # Save results
                backtest.save_results(results, stock_code)
                
                all_results[stock_code] = results
                
            except Exception as e:
                logger.error(f"✗ Error backtesting {stock_code}: {e}")
                continue
        
        # Print comparison
        print_comparison(all_results)
        
    except Exception as e:
        logger.error(f"✗ Fatal error: {e}")
        raise

def print_comparison(results_dict: Dict):
    """Print comparison across multiple stocks"""
    if not results_dict:
        return
    
    print(f"\n{'='*90}")
    print(f"COMPARISON ACROSS {len(results_dict)} STOCKS")
    print(f"{'='*90}\n")
    
    print(f"{'Stock':<10} {'Return':<12} {'Win Rate':<12} {'Avg Win':<15} {'Avg Loss':<15} {'Drawdown':<12}")
    print("-" * 90)
    
    for stock_code, results in results_dict.items():
        print(f"{stock_code:<10} "
              f"{results['total_return']:>10.2f}% "
              f"{results['win_rate']:>10.2f}% "
              f"₹{results['avg_win']:>12,.0f} "
              f"₹{results['avg_loss']:>12,.0f} "
              f"{results['max_drawdown']:>10.2f}%")
    
    print(f"\n{'='*90}\n")

if __name__ == '__main__':
    # Test with popular NSE stocks (using Breeze API stock codes)
    stocks_to_test = [
        'INFY',      # Infosys
        'RELIND',    # Reliance Industries (NOTE: Breeze uses 'RELIND', not 'RELIANCE')
        'TCS',       # Tata Consultancy Services
        'HDFC',      # HDFC Bank
    ]
    
    try:
        # Run backtest for 252 trading days (approximately 1 year)
        run_backtest_for_stocks(stocks_to_test, days_back=252)
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        sys.exit(1)
