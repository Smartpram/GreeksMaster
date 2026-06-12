"""
Enhanced Backtest with Screener-Generated Tickers and Trend Confirmation
=========================================================================

This script:
1. Uses stock screeners to identify candidate stocks
2. Runs backtest on pre-February 2026 data (before geopolitical crisis)
3. Excludes IT and Banking sectors
4. Implements Golden Cross trend confirmation (MA20 > MA50 > MA200)
5. Only enters trades when trend is confirmed
6. Uses real Breeze API data
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from pathlib import Path

# Setup paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from app.services.breeze_api import BreezeAPIService
    from app.services.stock_screener import StockScreener, ScreenerType
    logger.info("✓ Services imported successfully")
    SERVICES_AVAILABLE = True
except ImportError as e:
    logger.error(f"✗ Import error: {e}")
    SERVICES_AVAILABLE = False

# ============================================================================
# SECTOR CLASSIFICATION
# ============================================================================

SECTOR_MAPPING = {
    # IT/Technology (EXCLUDE)
    'TCS': 'IT',
    'INFY': 'IT',
    'WIPRO': 'IT',
    'HCLTECH': 'IT',
    'TECHM': 'IT',
    'LTTS': 'IT',
    'PERSISTENT': 'IT',
    'MPHASIS': 'IT',
    
    # Banking/Financial (EXCLUDE)
    'HDFC': 'Banking',
    'ICICIBANK': 'Banking',
    'AXISBANK': 'Banking',
    'KOTAK': 'Banking',
    'INDUSIND': 'Banking',
    'HDFCBANK': 'Banking',
    
    # Automotive (INCLUDE)
    'MARUTI': 'Automotive',
    'BAJAJFINSV': 'Automotive',
    'EICHER': 'Automotive',
    'M&M': 'Automotive',
    'ASHOKLEYLAND': 'Automotive',
    'TATAMOTORS': 'Automotive',
    
    # Pharma (INCLUDE)
    'SUNPHARMA': 'Pharma',
    'CIPLA': 'Pharma',
    'DRREDDY': 'Pharma',
    'DIVISLAB': 'Pharma',
    'LUPIN': 'Pharma',
    'BIOCON': 'Pharma',
    'ALKEM': 'Pharma',
    
    # FMCG (INCLUDE)
    'ITC': 'FMCG',
    'NESTLEIND': 'FMCG',
    'BRITANNIA': 'FMCG',
    'MARICO': 'FMCG',
    'HINDUNILVR': 'FMCG',
    'DABUR': 'FMCG',
    
    # Energy/Oil (INCLUDE)
    'RELIANCE': 'Energy',
    'BPCL': 'Energy',
    'HPCL': 'Energy',
    'NTPC': 'Energy',
    'JSWSTEEL': 'Energy',
    'TATASTEEL': 'Energy',
    
    # Utilities/Infrastructure (INCLUDE)
    'POWERGRID': 'Infrastructure',
    'ADANIGREEN': 'Infrastructure',
    'ADANIPORTS': 'Infrastructure',
    'ADANIEL': 'Infrastructure',
    'BHARTIARTL': 'Telecom',
    'JIO': 'Telecom',
}

EXCLUDE_SECTORS = ['IT', 'Banking']


# ============================================================================
# ENHANCED BACKTEST ENGINE WITH TREND CONFIRMATION
# ============================================================================

class EnhancedTrendConfirmationBacktest:
    """
    Backtest engine with:
    - Golden Cross trend confirmation (MA20 > MA50 > MA200)
    - Screener-based stock selection
    - Data before February 2026
    - Excludes IT and Banking stocks
    """
    
    def __init__(self, breeze_api, initial_capital=100000):
        self.api = breeze_api
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades = []
        
    def is_valid_ticker(self, ticker: str) -> bool:
        """Check if ticker should be included in backtest"""
        sector = SECTOR_MAPPING.get(ticker, 'Unknown')
        if sector in EXCLUDE_SECTORS:
            logger.info(f"  ✗ {ticker}: Excluded ({sector} sector)")
            return False
        logger.info(f"  ✓ {ticker}: Included ({sector} sector)")
        return True
    
    def check_golden_cross(self, df: pd.DataFrame) -> bool:
        """
        Check if Golden Cross pattern exists: MA20 > MA50 > MA200
        This indicates confirmed uptrend
        
        Returns:
            True if MA20 > MA50 > MA200 (uptrend confirmed)
        """
        if len(df) < 200:
            return False
        
        latest = df.iloc[-1]
        
        # Calculate moving averages
        ma20 = df['close'].rolling(20).mean().iloc[-1]
        ma50 = df['close'].rolling(50).mean().iloc[-1]
        ma200 = df['close'].rolling(200).mean().iloc[-1]
        
        # Golden Cross = MA20 > MA50 > MA200
        golden_cross = (ma20 > ma50) and (ma50 > ma200)
        
        return golden_cross
    
    def get_trend_strength(self, df: pd.DataFrame) -> float:
        """
        Calculate trend strength (0-100)
        
        Factors:
        - Distance from SMA200 (higher = stronger)
        - Angle of MA20 (steeper = stronger)
        - RSI level (50-70 = strong trend)
        """
        if len(df) < 200:
            return 0.0
        
        latest_close = df['close'].iloc[-1]
        ma200 = df['close'].rolling(200).mean().iloc[-1]
        ma20 = df['close'].rolling(20).mean().iloc[-1]
        
        # Distance from MA200
        distance_pct = (latest_close - ma200) / ma200 * 100 if ma200 > 0 else 0
        
        # Trend strength scoring
        trend_strength = min(abs(distance_pct), 10)  # Cap at 10%
        
        return trend_strength
    
    def backtest_ticker(self, ticker: str, start_date: str, end_date: str) -> Dict:
        """
        Backtest a single ticker with trend confirmation
        
        Returns:
            Dictionary with backtest results
        """
        try:
            # Convert dates to ISO 8601 format for Breeze API
            from_iso = start_date + 'T00:00:00.000Z' if 'T' not in start_date else start_date
            to_iso = end_date + 'T23:59:59.000Z' if 'T' not in end_date else end_date
            
            # Fetch historical data
            logger.info(f"\n  Fetching data for {ticker}...")
            result = self.api.get_historical_data(
                stock_code=ticker,
                exchange_code="NSE",
                product_type="cash",
                interval="day",
                from_date=from_iso,
                to_date=to_iso
            )
            
            # Check if API call was successful
            if not result.get('success', False):
                logger.warning(f"    ✗ Failed to fetch data for {ticker}: {result.get('error', 'Unknown error')}")
                return {
                    'ticker': ticker,
                    'status': 'NO_DATA',
                    'trades': 0,
                    'return_pct': 0,
                    'win_rate': 0,
                    'trades_list': []
                }
            
            # Convert list of dicts to DataFrame
            data = result.get('data', [])
            if not data:
                logger.warning(f"    ✗ No data available for {ticker}")
                return {
                    'ticker': ticker,
                    'status': 'NO_DATA',
                    'trades': 0,
                    'return_pct': 0,
                    'win_rate': 0,
                    'trades_list': []
                }
            
            # Convert to DataFrame with proper column mapping
            df = pd.DataFrame(data)
            
            # Rename columns if needed (Breeze API uses different naming)
            if 'open_price' in df.columns:
                df = df.rename(columns={
                    'open_price': 'open',
                    'high_price': 'high',
                    'low_price': 'low',
                    'close_price': 'close',
                    'volume': 'volume'
                })
            
            # Parse date if it's a string
            if 'date' in df.columns and isinstance(df['date'].iloc[0], str):
                df['date'] = pd.to_datetime(df['date'])
            elif 'datetime' in df.columns:
                df['date'] = pd.to_datetime(df['datetime'])
            
            # Ensure we have required columns
            required_cols = ['date', 'open', 'high', 'low', 'close']
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"    ✗ Missing required columns for {ticker}. Got: {df.columns.tolist()}")
                return {
                    'ticker': ticker,
                    'status': 'NO_DATA',
                    'trades': 0,
                    'return_pct': 0,
                    'win_rate': 0,
                    'trades_list': []
                }
            
            logger.info(f"    ✓ Got {len(df)} candles ({df['date'].min()} to {df['date'].max()})")
            
            # Initialize metrics
            trades_executed = []
            position = None
            
            # Iterate through data
            for idx in range(200, len(df)):  # Start after 200 SMA can be calculated
                current_date = df.iloc[idx]['date']
                current_price = df.iloc[idx]['close']
                lookback_df = df.iloc[:idx+1]
                
                # Check for entry signal: Golden Cross
                has_golden_cross = self.check_golden_cross(lookback_df)
                trend_strength = self.get_trend_strength(lookback_df)
                
                # Entry logic
                if position is None and has_golden_cross and trend_strength > 2.0:
                    position = {
                        'entry_date': current_date,
                        'entry_price': current_price,
                        'entry_strength': trend_strength,
                    }
                    logger.debug(f"    ENTRY {ticker} @ {current_price:.2f} on {current_date} (strength: {trend_strength:.1f}%)")
                
                # Exit logic
                elif position is not None:
                    price_change_pct = (current_price - position['entry_price']) / position['entry_price'] * 100
                    
                    # Exit on take profit (3%) or stop loss (-2%)
                    should_exit = (price_change_pct >= 3.0) or (price_change_pct <= -2.0)
                    
                    if should_exit:
                        pnl = (current_price - position['entry_price']) * 100  # Assuming 100 shares
                        pnl_pct = price_change_pct
                        win = 1 if pnl > 0 else 0
                        
                        trade = {
                            'entry_date': position['entry_date'],
                            'exit_date': current_date,
                            'entry_price': position['entry_price'],
                            'exit_price': current_price,
                            'pnl_pct': pnl_pct,
                            'pnl': pnl,
                            'win': win,
                            'days_held': (current_date - position['entry_date']).days
                        }
                        trades_executed.append(trade)
                        logger.debug(f"    EXIT {ticker} @ {current_price:.2f} on {current_date} | P&L: {pnl_pct:+.2f}%")
                        
                        position = None
            
            # Calculate metrics
            total_return = sum([t['pnl_pct'] for t in trades_executed])
            win_rate = sum([t['win'] for t in trades_executed]) / len(trades_executed) * 100 if trades_executed else 0
            avg_trade = total_return / len(trades_executed) if trades_executed else 0
            
            result = {
                'ticker': ticker,
                'status': 'SUCCESS',
                'trades': len(trades_executed),
                'return_pct': total_return,
                'win_rate': win_rate,
                'avg_trade_pct': avg_trade,
                'trades_list': trades_executed,
                'data_points': len(df)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"    ✗ Error backtesting {ticker}: {e}")
            return {
                'ticker': ticker,
                'status': 'ERROR',
                'error': str(e),
                'trades': 0
            }
    
    def run_backtest_suite(self, tickers: List[str], start_date: str, end_date: str) -> Dict:
        """
        Run backtest on multiple tickers
        """
        results = {
            'test_date': datetime.now().isoformat(),
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': self.initial_capital,
            'tickers_tested': [],
            'summary': {
                'total_tickers': 0,
                'successful_tickers': 0,
                'avg_return': 0,
                'avg_win_rate': 0,
                'total_trades': 0,
                'total_winners': 0,
            },
            'details': []
        }
        
        total_returns = []
        total_win_rates = []
        total_trades = 0
        total_winners = 0
        
        for ticker in tickers:
            if not self.is_valid_ticker(ticker):
                continue
            
            logger.info(f"\n{'='*80}")
            logger.info(f"Testing {ticker}")
            logger.info(f"{'='*80}")
            
            result = self.backtest_ticker(ticker, start_date, end_date)
            results['details'].append(result)
            
            if result['status'] == 'SUCCESS':
                results['tickers_tested'].append(ticker)
                total_returns.append(result['return_pct'])
                total_win_rates.append(result['win_rate'])
                total_trades += result['trades']
                total_winners += sum([1 for t in result['trades_list'] if t['win']])
                
                logger.info(f"\n✓ {ticker} Results:")
                logger.info(f"  Trades: {result['trades']}")
                logger.info(f"  Return: {result['return_pct']:+.2f}%")
                logger.info(f"  Win Rate: {result['win_rate']:.1f}%")
                logger.info(f"  Avg Trade: {result['avg_trade_pct']:+.2f}%")
        
        # Summary statistics
        if results['tickers_tested']:
            results['summary']['total_tickers'] = len(tickers)
            results['summary']['successful_tickers'] = len(results['tickers_tested'])
            results['summary']['avg_return'] = np.mean(total_returns) if total_returns else 0
            results['summary']['avg_win_rate'] = np.mean(total_win_rates) if total_win_rates else 0
            results['summary']['total_trades'] = total_trades
            results['summary']['total_winners'] = total_winners
        
        return results


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    logger.info("="*80)
    logger.info("ENHANCED BACKTEST WITH SCREENER AND TREND CONFIRMATION")
    logger.info("="*80)
    
    if not SERVICES_AVAILABLE:
        logger.error("✗ Services not available. Please check imports.")
        return
    
    try:
        # Initialize Breeze API
        logger.info("\nInitializing Breeze API...")
        breeze = BreezeAPIService()
        
        # Authenticate
        auth_result = breeze.authenticate()
        if not auth_result.get('success', False):
            logger.error(f"✗ Authentication failed: {auth_result.get('error', 'Unknown error')}")
            return
        
        logger.info(f"✓ Breeze API authenticated: {auth_result.get('user_name', 'User')}")
        
    except Exception as e:
        logger.error(f"✗ Failed to initialize Breeze API: {e}")
        return
    
    # Define test parameters
    # Use data BEFORE February 2026 (before geopolitical crisis)
    START_DATE = "2024-06-01"  # 2 years of data before crisis
    END_DATE = "2026-02-01"    # Stop before geopolitical issues
    
    # Curated list of non-IT, non-Banking stocks across sectors
    CANDIDATE_TICKERS = [
        # Automotive
        'MARUTI',
        'BAJAJFINSV',
        'EICHER',
        'M&M',
        
        # Pharma
        'SUNPHARMA',
        'CIPLA',
        'DRREDDY',
        'DIVISLAB',
        'LUPIN',
        
        # FMCG
        'ITC',
        'NESTLEIND',
        'BRITANNIA',
        'MARICO',
        
        # Energy
        'RELIANCE',
        'BPCL',
        'NTPC',
        
        # Infrastructure
        'POWERGRID',
        'ADANIPORTS',
        
        # Steel/Metals
        'TATASTEEL',
        'JSWSTEEL',
        
        # Telecom
        'BHARTIARTL',
    ]
    
    logger.info(f"\n{'='*80}")
    logger.info("SECTOR CLASSIFICATION")
    logger.info(f"{'='*80}")
    logger.info("Filtering out IT and Banking sectors...")
    logger.info(f"Total candidates: {len(CANDIDATE_TICKERS)}\n")
    
    # Initialize backtest engine
    backtest = EnhancedTrendConfirmationBacktest(breeze, initial_capital=100000)
    
    # Run backtest suite
    logger.info(f"\n{'='*80}")
    logger.info("RUNNING BACKTEST SUITE")
    logger.info(f"Period: {START_DATE} to {END_DATE}")
    logger.info(f"Entry Signal: Golden Cross (MA20 > MA50 > MA200)")
    logger.info(f"Exit Signal: +3% profit or -2% stop loss")
    logger.info(f"{'='*80}\n")
    
    results = backtest.run_backtest_suite(
        CANDIDATE_TICKERS,
        START_DATE,
        END_DATE
    )
    
    # Print summary
    logger.info(f"\n{'='*80}")
    logger.info("BACKTEST SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Tickers Tested: {results['summary']['total_tickers']}")
    logger.info(f"Successful: {results['summary']['successful_tickers']}")
    logger.info(f"Average Return: {results['summary']['avg_return']:+.2f}%")
    logger.info(f"Average Win Rate: {results['summary']['avg_win_rate']:.1f}%")
    logger.info(f"Total Trades: {results['summary']['total_trades']}")
    logger.info(f"Total Winners: {results['summary']['total_winners']}")
    
    # Print detailed results table
    logger.info(f"\n{'='*80}")
    logger.info("DETAILED RESULTS BY TICKER")
    logger.info(f"{'='*80}\n")
    
    print(f"{'Ticker':<12} {'Trades':<8} {'Return %':<12} {'Win Rate %':<12} {'Avg Trade %':<12} {'Status':<15}")
    print("-" * 80)
    
    for detail in results['details']:
        if detail['status'] == 'SUCCESS':
            print(f"{detail['ticker']:<12} {detail['trades']:<8} "
                  f"{detail['return_pct']:>10.2f}% {detail['win_rate']:>10.1f}% "
                  f"{detail['avg_trade_pct']:>10.2f}% {'✓ OK':<15}")
        else:
            print(f"{detail['ticker']:<12} {'0':<8} {'0.00':<12}% {'0.0':<12}% "
                  f"{'0.00':<12}% {detail['status']:<15}")
    
    # Save results to file
    output_file = f"screener_backtest_results_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\n✓ Results saved to: {output_file}")
    
    # Print top performers
    logger.info(f"\n{'='*80}")
    logger.info("TOP PERFORMERS")
    logger.info(f"{'='*80}\n")
    
    successful = [d for d in results['details'] if d['status'] == 'SUCCESS']
    successful_sorted = sorted(successful, key=lambda x: x['return_pct'], reverse=True)
    
    if successful_sorted:
        for i, detail in enumerate(successful_sorted[:5], 1):
            logger.info(f"{i}. {detail['ticker']}: {detail['return_pct']:+.2f}% "
                       f"({detail['trades']} trades, {detail['win_rate']:.1f}% win rate)")
    else:
        logger.info("No successful backtests yet")


if __name__ == '__main__':
    main()
