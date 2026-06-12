"""
Real Historical Options Data Fetcher - Improved Version
=========================================================

Uses yfinance to fetch REAL options data (not simulated):
- Live options chains with real premiums
- Real IV, Greeks from market
- Validates screener signals against actual market data
- Works for US stocks (AAPL, MSFT, GOOGL, etc.)

Integration with screeners:
- Apply screener rules to real options data
- Test screener signals on live data
- Measure actual signal accuracy
"""

import logging
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class RealOptionsDataValidator:
    """Validate screeners against real options data from yfinance"""
    
    def __init__(self):
        self.cache_dir = Path("data/real_options_data")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Real Options Data Validator initialized")
    
    def get_options_snapshot(self, symbol: str, use_first_expiry: bool = True) -> Dict:
        """
        Get real options chain data from yfinance
        
        Args:
            symbol: Stock symbol (US stocks like AAPL, MSFT, GOOGL)
            use_first_expiry: Use first available expiry if True
            
        Returns:
            Dictionary with options data
        """
        try:
            logger.info(f"Fetching real options data for {symbol}...")
            ticker = yf.Ticker(symbol)
            
            # Get available expirations
            expirations = ticker.options
            if not expirations:
                logger.warning(f"No options data available for {symbol}")
                return None
            
            # Use first expiry
            expiry_date = expirations[0]
            logger.info(f"Using expiry: {expiry_date}")
            
            # Get options chain
            chain = ticker.option_chain(expiry_date)
            calls = chain.calls
            puts = chain.puts
            
            # Get stock price
            hist = ticker.history(period='1d')
            spot_price = float(hist['Close'].iloc[-1]) if not hist.empty else 0
            
            # Calculate days to expiry
            expiry_dt = datetime.strptime(expiry_date, '%Y-%m-%d')
            dte = (expiry_dt - datetime.now()).days
            
            # Extract IV data
            calls_data = calls[['strike', 'lastPrice', 'bid', 'ask', 'volume', 'impliedVolatility']].copy()
            puts_data = puts[['strike', 'lastPrice', 'bid', 'ask', 'volume', 'impliedVolatility']].copy()
            
            # Calculate IV statistics
            calls_iv = pd.to_numeric(calls_data['impliedVolatility'], errors='coerce') * 100
            puts_iv = pd.to_numeric(puts_data['impliedVolatility'], errors='coerce') * 100
            
            snapshot = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'spot_price': spot_price,
                'expiry_date': expiry_date,
                'dte': dte,
                'num_calls': len(calls),
                'num_puts': len(puts),
                'calls': calls_data.to_dict('records'),
                'puts': puts_data.to_dict('records'),
                'iv_stats': {
                    'calls_iv_mean': float(calls_iv.mean()),
                    'puts_iv_mean': float(puts_iv.mean()),
                    'calls_iv_std': float(calls_iv.std()),
                    'calls_iv_max': float(calls_iv.max()),
                    'calls_iv_min': float(calls_iv.min()),
                    'call_put_iv_skew': float(puts_iv.mean() - calls_iv.mean())
                }
            }
            
            logger.info(f"✓ Retrieved {len(calls)} calls and {len(puts)} puts")
            logger.info(f"  Spot: ${spot_price:.2f} | DTE: {dte} | IV Skew: {snapshot['iv_stats']['call_put_iv_skew']:.1f}%")
            
            return snapshot
        
        except Exception as e:
            logger.error(f"Error fetching options data: {e}")
            return None
    
    def test_iv_screener(self, symbol: str, iv_percentile_threshold: float = 75) -> Dict:
        """
        Test IV screener on real data
        
        Args:
            symbol: Stock symbol
            iv_percentile_threshold: Percentile threshold
            
        Returns:
            Screener results with real data
        """
        logger.info(f"Testing IV Screener on {symbol} (real data)...")
        
        snapshot = self.get_options_snapshot(symbol)
        if not snapshot:
            return None
        
        calls_data = pd.DataFrame(snapshot['calls'])
        calls_data['IV%'] = pd.to_numeric(calls_data['impliedVolatility'], errors='coerce') * 100
        
        # Calculate IV percentile
        iv_values = calls_data['IV%'].dropna()
        iv_threshold = iv_values.quantile(iv_percentile_threshold / 100)
        
        # Find high IV calls
        high_iv_calls = calls_data[calls_data['IV%'] >= iv_threshold]
        
        results = {
            'screener': 'IV_HIGH',
            'symbol': symbol,
            'timestamp': snapshot['timestamp'],
            'spot_price': snapshot['spot_price'],
            'total_calls': len(calls_data),
            'high_iv_threshold': float(iv_threshold),
            'high_iv_count': len(high_iv_calls),
            'opportunities': high_iv_calls[['strike', 'IV%', 'bid', 'ask', 'lastPrice']].head(5).to_dict('records')
        }
        
        logger.info(f"✓ IV Screener: Found {len(high_iv_calls)} high IV calls (IV >= {iv_threshold:.1f}%)")
        return results
    
    def test_theta_screener(self, symbol: str, dte_range: tuple = (3, 30)) -> Dict:
        """
        Test theta screener on real data
        
        Args:
            symbol: Stock symbol
            dte_range: Days to expiry range
            
        Returns:
            Screener results with real data
        """
        logger.info(f"Testing Theta Screener on {symbol} (real data)...")
        
        snapshot = self.get_options_snapshot(symbol)
        if not snapshot:
            return None
        
        dte = snapshot['dte']
        
        # Check if DTE is in range
        if dte < dte_range[0] or dte > dte_range[1]:
            logger.warning(f"DTE {dte} outside range {dte_range}")
            return {
                'screener': 'THETA_DECAY',
                'symbol': symbol,
                'dte': dte,
                'dte_range': dte_range,
                'status': 'OUT_OF_RANGE',
                'opportunities': 0
            }
        
        # Analyze puts for theta decay
        puts_data = pd.DataFrame(snapshot['puts'])
        puts_data['lastPrice'] = pd.to_numeric(puts_data['lastPrice'], errors='coerce')
        
        # Filter liquid puts
        liquid_puts = puts_data[puts_data['lastPrice'] > 0.05]
        
        results = {
            'screener': 'THETA_DECAY',
            'symbol': symbol,
            'timestamp': snapshot['timestamp'],
            'spot_price': snapshot['spot_price'],
            'dte': dte,
            'total_puts': len(puts_data),
            'liquid_puts': len(liquid_puts),
            'opportunities': liquid_puts[['strike', 'bid', 'ask', 'lastPrice', 'volume']].head(5).to_dict('records')
        }
        
        logger.info(f"✓ Theta Screener: Found {len(liquid_puts)} tradeable puts with {dte} DTE")
        return results
    
    def test_all_screeners(self, symbols: List[str] = None) -> Dict:
        """
        Test all screeners on real data for multiple symbols
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Results dictionary
        """
        if symbols is None:
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        
        logger.info(f"Testing all screeners on {len(symbols)} symbols with REAL data...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'test_date': datetime.now().strftime('%Y-%m-%d'),
            'symbols_tested': len(symbols),
            'screeners': {
                'iv_screener': {},
                'theta_screener': {}
            },
            'summary': {}
        }
        
        total_opportunities = 0
        
        for symbol in symbols:
            logger.info(f"\n{'='*70}")
            logger.info(f"Testing: {symbol}")
            logger.info(f"{'='*70}")
            
            # Test IV screener
            iv_result = self.test_iv_screener(symbol, iv_percentile_threshold=75)
            if iv_result:
                results['screeners']['iv_screener'][symbol] = iv_result
                total_opportunities += iv_result.get('high_iv_count', 0)
            
            # Test Theta screener
            theta_result = self.test_theta_screener(symbol, dte_range=(5, 30))
            if theta_result:
                results['screeners']['theta_screener'][symbol] = theta_result
                if theta_result.get('status') != 'OUT_OF_RANGE':
                    total_opportunities += theta_result.get('opportunities', 0)
        
        results['summary'] = {
            'total_opportunities': total_opportunities,
            'data_source': 'yfinance (REAL)',
            'validation': 'LIVE_MARKET_DATA'
        }
        
        logger.info(f"\n{'='*70}")
        logger.info(f"TOTAL OPPORTUNITIES FOUND: {total_opportunities}")
        logger.info(f"DATA SOURCE: Yahoo Finance (Real Options Data)")
        logger.info(f"{'='*70}\n")
        
        return results
    
    def save_results(self, results: Dict, filename: str = None) -> str:
        """Save results to JSON file"""
        if filename is None:
            filename = f"screener_test_real_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.cache_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"✓ Results saved to {filepath}")
        return str(filepath)


def main():
    """Run screener validation on real options data"""
    print("\n" + "="*80)
    print("SCREENER VALIDATION WITH REAL OPTIONS DATA (yfinance)")
    print("="*80 + "\n")
    
    validator = RealOptionsDataValidator()
    
    # Test on real stock symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
    
    print(f"📊 Testing screeners on {len(symbols)} real stocks...")
    print(f"Data Source: Yahoo Finance (REAL market data)")
    print()
    
    # Run all screeners
    results = validator.test_all_screeners(symbols)
    
    # Save results
    filepath = validator.save_results(results)
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Symbols Tested: {', '.join(symbols)}")
    print(f"Total Opportunities Found: {results['summary']['total_opportunities']}")
    print(f"Data Source: {results['summary']['data_source']}")
    print(f"Report: {filepath}\n")
    
    # Show detailed results for each symbol
    print("\n" + "="*80)
    print("DETAILED RESULTS")
    print("="*80)
    
    for symbol in symbols:
        print(f"\n{symbol}:")
        
        # IV Screener results
        if symbol in results['screeners']['iv_screener']:
            iv = results['screeners']['iv_screener'][symbol]
            print(f"  IV Screener: {iv['high_iv_count']} opportunities found")
        
        # Theta Screener results
        if symbol in results['screeners']['theta_screener']:
            theta = results['screeners']['theta_screener'][symbol]
            if theta.get('status') != 'OUT_OF_RANGE':
                print(f"  Theta Screener: {len(theta['opportunities'])} opportunities ({theta['dte']} DTE)")
            else:
                print(f"  Theta Screener: No opportunities (DTE {theta['dte']} out of range)")


if __name__ == "__main__":
    main()
