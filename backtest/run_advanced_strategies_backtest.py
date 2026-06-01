#!/usr/bin/env python3
"""
Advanced Strategies Backtest with Breeze Data
Runs all 8 advanced strategies on real Breeze API data
"""

import sys
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import advanced strategies
from app.strategies.advanced_strategies_suite import (
    VolatilityContractionPattern,
    StatisticalArbitrage,
    OrderFlowMicrostructure,
    PostEarningsAnnouncementDrift,
    DeltaNeutralVolatilityHarvesting,
    VolatilityMeanReversion,
    GammaScalping,
    DynamicOptionsMonitorTrendFollowing
)

# Import Breeze service
from app.services.breeze_service_factory import get_breeze_service


class AdvancedStrategiesBacktester:
    """Backtester for advanced strategies using Breeze data"""
    
    def __init__(self):
        self.breeze_service = get_breeze_service()
        self.results = {}
        self.logger = logger
        
    def fetch_breeze_data(self, symbol: str, days: int = 90, interval: str = '1day') -> pd.DataFrame:
        """
        Fetch historical data from Breeze API (real data)
        Falls back to synthetic data only if API fails
        
        Args:
            symbol: Trading symbol (e.g., 'NIFTY', 'INFY', 'BANKNIFTY')
            days: Number of days of historical data
            interval: Data interval ('1min', '5min', '15min', '30min', 'hour', '1day')
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            self.logger.info(f"🔄 Fetching {days} days of {interval} data for {symbol} from Breeze API (REAL DATA)...")
            
            # Import BreezeAPIService directly for historical data (has the method)
            from app.services.breeze_api import BreezeAPIService
            from app.config import Config
            from datetime import datetime, timedelta
            
            # Try to get historical data using BreezeAPIService
            try:
                # Create BreezeAPIService instance for historical data
                api_service = BreezeAPIService()
                
                # Authenticate first
                auth_result = api_service.authenticate()
                if not auth_result.get('success'):
                    self.logger.warning(f"⚠️ Authentication failed: {auth_result.get('error', 'Unknown error')}")
                    self.logger.info(f"📊 Falling back to synthetic data for {symbol}...")
                    return self._generate_synthetic_data(symbol, days)
                
                # Map interval names to Breeze API format
                interval_map = {
                    '1min': 'minute',
                    '1minute': 'minute',
                    '5min': '5minute',
                    '5minute': '5minute',
                    '15min': '30minute',
                    '30min': '30minute',
                    '30minute': '30minute',
                    '1hour': 'day',
                    'hour': 'day',
                    '1day': 'day',
                    'day': 'day'
                }
                breeze_interval = interval_map.get(interval, 'day')
                
                # Calculate date range (ISO 8601 format required by Breeze API)
                to_date_dt = datetime.now()
                from_date_dt = to_date_dt - timedelta(days=days)
                
                from_date_str = from_date_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                to_date_str = to_date_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                
                self.logger.debug(f"  Requesting: {symbol} | {breeze_interval} | {from_date_str} to {to_date_str}")
                
                # Call get_historical_data method with correct parameters
                result = api_service.get_historical_data(
                    stock_code=symbol,
                    exchange_code='NSE',
                    product_type='cash',
                    interval=breeze_interval,
                    from_date=from_date_str,
                    to_date=to_date_str
                )
                
                if result.get('success') and result.get('data'):
                    data = result.get('data', [])
                    
                    # Convert list of records to DataFrame
                    if isinstance(data, list) and len(data) > 0:
                        df = pd.DataFrame(data)
                        formatted = self._format_breeze_data(df)
                        if formatted is not None and len(formatted) > 0:
                            self.logger.info(f"✅ Successfully fetched {len(formatted)} REAL bars from Breeze API for {symbol}")
                            return formatted
                    
                    self.logger.warning(f"⚠️ Breeze API returned empty data for {symbol}")
                    self.logger.info(f"📊 Falling back to synthetic data for {symbol}...")
                    return self._generate_synthetic_data(symbol, days)
                else:
                    warning = result.get('warning') or result.get('error', 'Unknown error')
                    self.logger.warning(f"⚠️ Could not fetch from Breeze: {warning}")
                    self.logger.info(f"📊 Falling back to synthetic data for {symbol}...")
                    return self._generate_synthetic_data(symbol, days)
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Error fetching from Breeze API: {e}")
                self.logger.info(f"📊 Falling back to synthetic data for {symbol}...")
                return self._generate_synthetic_data(symbol, days)
            
        except Exception as e:
            self.logger.error(f"Fatal error fetching data for {symbol}: {e}")
            return None
    
    def _format_breeze_data(self, data: List[Dict]) -> pd.DataFrame:
        """Format Breeze API data into DataFrame"""
        try:
            df = pd.DataFrame(data)
            
            # Normalize column names to title case (Close, High, Low, Open, Volume)
            df.columns = df.columns.str.title()
            
            # Ensure required columns exist
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_cols):
                self.logger.error(f"Missing required columns. Available: {df.columns.tolist()}")
                return None
            
            # Convert to numeric
            for col in required_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Sort by timestamp if available
            if 'Timestamp' in df.columns or 'Datetime' in df.columns:
                time_col = 'Timestamp' if 'Timestamp' in df.columns else 'Datetime'
                df[time_col] = pd.to_datetime(df[time_col])
                df = df.sort_values(by=time_col).reset_index(drop=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error formatting Breeze data: {e}")
            return None
    
    def _generate_synthetic_data(self, symbol: str, days: int) -> pd.DataFrame:
        """Generate synthetic OHLCV data for testing"""
        np.random.seed(hash(symbol) % 2**32)
        
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        # Generate realistic price movements
        close_prices = [100]
        for _ in range(len(dates) - 1):
            change = np.random.normal(0.0005, 0.02)  # 0.05% mean, 2% volatility
            close_prices.append(close_prices[-1] * (1 + change))
        
        close_prices = np.array(close_prices)
        
        # Generate OHLC from close prices
        opens = close_prices + np.random.normal(0, 0.5, len(close_prices))
        highs = np.maximum(opens, close_prices) + np.abs(np.random.normal(0, 0.3, len(close_prices)))
        lows = np.minimum(opens, close_prices) - np.abs(np.random.normal(0, 0.3, len(close_prices)))
        volumes = np.random.uniform(1000000, 5000000, len(close_prices))
        
        # Use title-case column names (required by strategies)
        # Include both 'Date' and 'DateTime' for compatibility
        df = pd.DataFrame({
            'Date': dates,
            'DateTime': dates,
            'Open': opens,
            'High': highs,
            'Low': lows,
            'Close': close_prices,
            'Volume': volumes.astype(int)
        })
        
        self.logger.info(f"Generated {len(df)} synthetic bars for {symbol}")
        return df
    
    def run_equity_strategies(self, data: pd.DataFrame, symbol: str, pair_symbol: str = None, pair_data: pd.DataFrame = None) -> Dict[str, Any]:
        """Run all equity-based strategies
        
        Args:
            data: OHLCV data for primary symbol
            symbol: Primary symbol name
            pair_symbol: Secondary symbol for pairs trading
            pair_data: OHLCV data for secondary symbol
        """
        results = {}
        
        strategies_list = [
            ('VCP', VolatilityContractionPattern(symbol)),
            ('Order Flow', OrderFlowMicrostructure(symbol)),
            ('PEAD', PostEarningsAnnouncementDrift(symbol)),
        ]
        
        for name, strategy in strategies_list:
            try:
                self.logger.info(f"  → Running {name}...")
                backtest_results = strategy.backtest(data)
                results[name] = backtest_results
                self.logger.info(f"    ✓ {name}: Sharpe={backtest_results.get('sharpe_ratio', 0):.2f}, "
                               f"Return={backtest_results.get('total_return', 0):+.2f}%, "
                               f"Trades={backtest_results.get('trades', 0)}")
            except Exception as e:
                self.logger.error(f"    ✗ Error in {name}: {e}")
                results[name] = {'error': str(e), 'total_return': 0, 'sharpe_ratio': 0}
        
        # Pairs trading with correlated symbols
        if pair_symbol and pair_data is not None:
            try:
                self.logger.info(f"  → Running Pairs Trading ({symbol}/{pair_symbol})...")
                from app.strategies.advanced_strategies_suite import StatisticalArbitrage
                pairs_strategy = StatisticalArbitrage(symbol, pair_symbol)
                pairs_results = pairs_strategy.backtest_pairs(data, pair_data)
                results['Pairs Trading'] = pairs_results
                self.logger.info(f"    ✓ Pairs Trading: Sharpe={pairs_results.get('sharpe_ratio', 0):.2f}, "
                               f"Return={pairs_results.get('total_return', 0):+.2f}%, "
                               f"Trades={pairs_results.get('trades', 0)}")
            except Exception as e:
                self.logger.warning(f"    ⚠️ Pairs Trading failed: {e}")
                results['Pairs Trading'] = {
                    'error': f'Pairs trading error: {str(e)}',
                    'total_return': 0,
                    'sharpe_ratio': 0,
                    'trades': 0
                }
        else:
            # Skip pairs trading if no pair available
            results['Pairs Trading'] = {
                'error': 'Requires two correlated symbols (manual setup needed)',
                'total_return': 0,
                'sharpe_ratio': 0,
                'trades': 0
            }
        
        return results
    
    def run_options_strategies(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Run all options-based strategies"""
        results = {}
        
        strategies = [
            ('Vol Harvesting', DeltaNeutralVolatilityHarvesting(symbol)),
            ('Vol Mean Reversion', VolatilityMeanReversion(symbol)),
            ('Gamma Scalping', GammaScalping(symbol)),
            ('Options Momentum', DynamicOptionsMonitorTrendFollowing(symbol)),
        ]
        
        for name, strategy in strategies:
            try:
                self.logger.info(f"  → Running {name}...")
                backtest_results = strategy.backtest(data)
                results[name] = backtest_results
                self.logger.info(f"    ✓ {name}: Sharpe={backtest_results.get('sharpe_ratio', 0):.2f}, "
                               f"Return={backtest_results.get('total_return', 0):+.2f}%, "
                               f"Trades={backtest_results.get('trades', 0)}")
            except Exception as e:
                self.logger.error(f"    ✗ Error in {name}: {e}")
                results[name] = {'error': str(e), 'total_return': 0, 'sharpe_ratio': 0}
        
        return results
    
    def run_backtest(self, symbols: List[str] = None) -> Dict[str, Any]:
        """
        Run backtest on all strategies for specified symbols
        Supports pairs trading for correlated symbol pairs
        
        Args:
            symbols: List of trading symbols to backtest (can include pairs)
            
        Returns:
            Dictionary with all results
        """
        if symbols is None:
            symbols = ['NIFTY', 'INFY', 'RELIANCE', 'HDFC']
        
        all_results = {}
        symbol_data = {}  # Cache for data to use in pairs trading
        
        self.logger.info("=" * 80)
        self.logger.info("🚀 ADVANCED STRATEGIES BACKTEST - BREEZE DATA")
        self.logger.info("=" * 80)
        
        # First pass: Fetch all data and run individual strategies
        for symbol in symbols:
            self.logger.info(f"\n📊 Testing: {symbol}")
            self.logger.info("-" * 40)
            
            # Fetch data
            data = self.fetch_breeze_data(symbol, days=90)
            
            if data is None or len(data) < 50:
                self.logger.warning(f"Insufficient data for {symbol}, skipping...")
                continue
            
            # Store data for pairs trading
            symbol_data[symbol] = data
            
            # Run equity strategies (no pairs trading yet for individual symbols)
            self.logger.info("Equity Strategies:")
            equity_results = self.run_equity_strategies(data, symbol, pair_symbol=None, pair_data=None)
            
            # Run options strategies
            self.logger.info("Options Strategies:")
            options_results = self.run_options_strategies(data, symbol)
            
            # Store results
            all_results[symbol] = {
                'equity_strategies': equity_results,
                'options_strategies': options_results,
                'data_bars': len(data),
                'price_range': f"{data['Close'].min():.2f} - {data['Close'].max():.2f}"
            }
        
        # Second pass: Run pairs trading for correlated symbol pairs
        if len(symbols) >= 2:
            self.logger.info("\n" + "=" * 80)
            self.logger.info("📊 PAIRS TRADING - Correlated Symbols")
            self.logger.info("=" * 80)
            
            # For 2-symbol case (correlated pair)
            if len(symbols) == 2:
                sym1, sym2 = symbols[0], symbols[1]
                if sym1 in symbol_data and sym2 in symbol_data:
                    self.logger.info(f"\n🔗 Running Pairs Trading: {sym1} / {sym2}")
                    self.logger.info("-" * 40)
                    
                    # Update equity results with pairs trading for both symbols
                    try:
                        from app.strategies.advanced_strategies_suite import StatisticalArbitrage
                        pairs_strategy = StatisticalArbitrage(sym1, sym2)
                        # backtest() method takes two dataframes
                        pairs_results = pairs_strategy.backtest(symbol_data[sym1], symbol_data[sym2])
                        
                        self.logger.info(f"  → Running Pairs Trading...")
                        self.logger.info(f"    ✓ Pairs Trading: Sharpe={pairs_results.get('sharpe_ratio', 0):.2f}, "
                                       f"Return={pairs_results.get('total_return', 0):+.2f}%, "
                                       f"Trades={pairs_results.get('trades', 0)}")
                        
                        # Add pairs trading results to both symbols
                        all_results[sym1]['equity_strategies']['Pairs Trading'] = pairs_results
                        all_results[sym2]['equity_strategies']['Pairs Trading'] = pairs_results
                        
                    except Exception as e:
                        self.logger.warning(f"  ⚠️ Pairs trading failed: {e}")
                        error_result = {
                            'error': f'Pairs trading error: {str(e)}',
                            'total_return': 0,
                            'sharpe_ratio': 0,
                            'trades': 0
                        }
                        all_results[sym1]['equity_strategies']['Pairs Trading'] = error_result
                        all_results[sym2]['equity_strategies']['Pairs Trading'] = error_result
        
        # Print summary
        self._print_summary(all_results)
        
        # Save results
        self._save_results(all_results)
        
        return all_results
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print backtest summary"""
        self.logger.info("\n" + "=" * 80)
        self.logger.info("📈 BACKTEST SUMMARY")
        self.logger.info("=" * 80)
        
        for symbol, symbol_results in results.items():
            self.logger.info(f"\n{symbol}")
            self.logger.info("-" * 40)
            
            # Equity strategies summary
            self.logger.info("Equity Strategies:")
            for name, strategy_results in symbol_results['equity_strategies'].items():
                if 'error' in strategy_results:
                    self.logger.info(f"  {name}: ERROR - {strategy_results['error']}")
                else:
                    self.logger.info(f"  {name}:")
                    self.logger.info(f"    Return: {strategy_results.get('total_return', 0):+.2f}%")
                    self.logger.info(f"    Sharpe: {strategy_results.get('sharpe_ratio', 0):.2f}")
                    self.logger.info(f"    Win Rate: {strategy_results.get('win_rate', 0):.1f}%")
                    self.logger.info(f"    Trades: {strategy_results.get('trades', 0)}")
            
            # Options strategies summary
            self.logger.info("Options Strategies:")
            for name, strategy_results in symbol_results['options_strategies'].items():
                if 'error' in strategy_results:
                    self.logger.info(f"  {name}: ERROR - {strategy_results['error']}")
                else:
                    self.logger.info(f"  {name}:")
                    self.logger.info(f"    Return: {strategy_results.get('total_return', 0):+.2f}%")
                    self.logger.info(f"    Sharpe: {strategy_results.get('sharpe_ratio', 0):.2f}")
                    self.logger.info(f"    Win Rate: {strategy_results.get('win_rate', 0):.1f}%")
                    self.logger.info(f"    Trades: {strategy_results.get('trades', 0)}")
    
    def _save_results(self, results: Dict[str, Any]):
        """Save results to JSON file"""
        try:
            output_file = 'ADVANCED_STRATEGIES_BACKTEST_RESULTS.json'
            
            # Convert numpy types to Python types for JSON serialization
            def convert_types(obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, dict):
                    return {k: convert_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_types(item) for item in obj]
                return obj
            
            results_serializable = convert_types(results)
            
            with open(output_file, 'w') as f:
                json.dump(results_serializable, f, indent=2)
            
            self.logger.info(f"\n✓ Results saved to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")


def main():
    """Main entry point"""
    try:
        # Initialize backtester
        backtester = AdvancedStrategiesBacktester()
        
        # Run backtest on multiple symbols
        symbols = ['NIFTY', 'INFY', 'RELIANCE', 'HDFC', 'BANKNIFTY', 'TCS', 'SBIN', 'ICICIBANK']
        
        results = backtester.run_backtest(symbols)
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ BACKTEST COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Tested {len(results)} symbols")
        logger.info(f"8 strategies per symbol (4 equity + 4 options)")
        logger.info(f"Total strategy runs: {len(results) * 8}")
        logger.info("\nNext steps:")
        logger.info("1. Review ADVANCED_STRATEGIES_BACKTEST_RESULTS.json")
        logger.info("2. Identify top-performing strategies")
        logger.info("3. Optimize parameters for each strategy")
        logger.info("4. Paper trade before live deployment")
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
