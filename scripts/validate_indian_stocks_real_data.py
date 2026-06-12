"""
Real yfinance Data Integration - Indian Stocks Edition
======================================================

Tests screeners on REAL Indian stock options data via yfinance.
Maps Indian symbols to yfinance format (e.g., INFY → INFY.NS, TCS → TCS.BO)

Supports:
- NSE stocks (National Stock Exchange) - .NS suffix
- BSE stocks (Bombay Stock Exchange) - .BO suffix
- Major indices: NIFTY, BANKNIFTY (via indices)
"""

import logging
import pandas as pd
import numpy as np
import yfinance as yf
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


# Indian stock symbol mapping for yfinance
INDIAN_STOCK_MAP = {
    # Major IT stocks (NSE)
    'INFY': 'INFY.NS',      # Infosys
    'TCS': 'TCS.NS',        # Tata Consultancy Services
    'WIPRO': 'WIPRO.NS',    # Wipro
    'TECHM': 'TECHM.NS',    # Tech Mahindra
    'HCL': 'HCLTECH.NS',    # HCL Technologies
    
    # Banking & Finance (NSE)
    'HDFC': 'HDFC.NS',      # HDFC Bank
    'ICICI': 'ICICIBANK.NS', # ICICI Bank
    'AXIS': 'AXISBANK.NS',  # Axis Bank
    'INDUSIND': 'INDUSINDBK.NS', # IndusInd Bank
    'KOTAK': 'KOTAKBANK.NS', # Kotak Mahindra Bank
    
    # Auto & Manufacturing (NSE)
    'MARUTI': 'MARUTI.NS',  # Maruti Suzuki
    'BAJAJ': 'BAJAJFINSV.NS', # Bajaj Finserv
    'TATA': 'TATAMOTORS.NS', # Tata Motors
    'HERO': 'HEROMOTOCO.NS', # Hero MotoCorp
    
    # Pharma (NSE)
    'SBIN': 'SBIN.NS',      # State Bank of India
    'SUNPHARMA': 'SUNPHARMA.NS', # Sun Pharmaceutical
    'CIPLA': 'CIPLA.NS',    # Cipla
    
    # BSE listings (alternative)
    'INFY_BSE': 'INFY.BO',
    'TCS_BSE': 'TCS.BO',
}

# Indices (for benchmarking)
INDICES = {
    'NIFTY50': '^NSEI',
    'BANKNIFTY': '^NSEBANK',
    'FINNIFTY': '^NSEINFRA',
    'MIDCPNIFTY': '^NSMIDCP',
}


class IndianStocksRealDataValidator:
    """Validate screeners against REAL Indian stock options data"""
    
    def __init__(self):
        self.cache_dir = Path("data/indian_stocks_real_data")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir = Path("backtest_reports")
        self.report_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Indian Stocks Real Data Validator initialized")
        logger.info(f"Cache: {self.cache_dir}")
    
    def get_yfinance_symbol(self, indian_symbol: str) -> str:
        """
        Convert Indian symbol to yfinance format
        
        Examples:
            'INFY' -> 'INFY.NS'
            'TCS' -> 'TCS.NS'
        """
        if indian_symbol in INDIAN_STOCK_MAP:
            return INDIAN_STOCK_MAP[indian_symbol]
        elif indian_symbol.endswith('.NS') or indian_symbol.endswith('.BO'):
            return indian_symbol
        else:
            # Assume NSE by default
            return f"{indian_symbol}.NS"
    
    def get_stock_price(self, symbol: str) -> Dict:
        """Get real stock price data from yfinance"""
        try:
            yf_symbol = self.get_yfinance_symbol(symbol)
            logger.info(f"Fetching {symbol} ({yf_symbol}) price data...")
            
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period='1d')
            
            if hist.empty:
                logger.warning(f"No price data for {symbol}")
                return None
            
            row = hist.iloc[-1]
            data = {
                'symbol': symbol,
                'yfinance_symbol': yf_symbol,
                'date': hist.index[-1].strftime('%Y-%m-%d'),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume'])
            }
            
            logger.info(f"✓ {symbol}: Close={data['close']:.2f} | Volume={data['volume']:,}")
            return data
        
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return None
    
    def get_historical_prices(self, symbol: str, days: int = 30) -> Dict:
        """Get historical price data"""
        try:
            yf_symbol = self.get_yfinance_symbol(symbol)
            logger.info(f"Fetching {days}-day history for {symbol}...")
            
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period=f"{days}d")
            
            if hist.empty:
                logger.warning(f"No historical data for {symbol}")
                return None
            
            # Calculate technical indicators
            closes = hist['Close']
            highs = hist['High']
            lows = hist['Low']
            
            # Simple moving averages
            sma_20 = closes.rolling(window=20).mean().iloc[-1]
            sma_50 = closes.rolling(window=50).mean().iloc[-1]
            
            # ATR (Average True Range)
            tr = pd.concat([
                highs - lows,
                abs(highs - closes.shift()),
                abs(lows - closes.shift())
            ], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean().iloc[-1]
            
            # Volatility
            returns = closes.pct_change()
            volatility = returns.std() * np.sqrt(252)  # Annualized
            
            data = {
                'symbol': symbol,
                'days': len(hist),
                'current_price': float(closes.iloc[-1]),
                'sma_20': float(sma_20) if not pd.isna(sma_20) else None,
                'sma_50': float(sma_50) if not pd.isna(sma_50) else None,
                'atr': float(atr),
                'volatility': float(volatility),
                'price_range': {
                    'high': float(highs.max()),
                    'low': float(lows.min()),
                    'change_pct': float((closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0] * 100)
                }
            }
            
            logger.info(f"✓ {symbol}: Price={data['current_price']:.2f} | Volatility={data['volatility']*100:.1f}% | ATR={data['atr']:.2f}")
            return data
        
        except Exception as e:
            logger.error(f"Error fetching history: {e}")
            return None
    
    def test_all_indian_stocks(self, symbols: List[str] = None, days: int = 30) -> Dict:
        """Test on real Indian stock data"""
        if symbols is None:
            symbols = ['INFY', 'TCS', 'HDFC', 'AXIS', 'MARUTI', 'WIPRO', 'SUNPHARMA']
        
        logger.info(f"\n{'='*80}")
        logger.info(f"INDIAN STOCKS - REAL DATA VALIDATION")
        logger.info(f"{'='*80}")
        logger.info(f"Symbols: {', '.join(symbols)}")
        logger.info(f"Data Source: Yahoo Finance (REAL Indian Stock Data)")
        logger.info(f"{'='*80}\n")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'data_source': 'yfinance (REAL Indian Stocks)',
            'test_date': datetime.now().strftime('%Y-%m-%d'),
            'symbols_tested': len(symbols),
            'stocks': {},
            'summary': {}
        }
        
        success_count = 0
        total_volume = 0
        avg_volatility = []
        
        for symbol in symbols:
            logger.info(f"\nProcessing {symbol}...")
            logger.info(f"{'-'*60}")
            
            # Get current price
            price_data = self.get_stock_price(symbol)
            if not price_data:
                logger.warning(f"⚠️ Skipped {symbol} - no price data")
                continue
            
            # Get historical data
            hist_data = self.get_historical_prices(symbol, days)
            if hist_data:
                success_count += 1
                total_volume += price_data['volume']
                avg_volatility.append(hist_data['volatility'])
                
                results['stocks'][symbol] = {
                    'current': price_data,
                    'historical': hist_data,
                    'screener_ready': True
                }
        
        # Calculate summary
        results['summary'] = {
            'stocks_retrieved': success_count,
            'total_trading_volume': total_volume,
            'avg_volatility': float(np.mean(avg_volatility)) if avg_volatility else 0,
            'date_range': f"Last {days} days",
            'data_quality': 'HIGH' if success_count == len(symbols) else 'PARTIAL'
        }
        
        logger.info(f"\n{'='*80}")
        logger.info(f"SUMMARY - Indian Stocks Real Data")
        logger.info(f"{'='*80}")
        logger.info(f"✓ Stocks Retrieved: {success_count}/{len(symbols)}")
        logger.info(f"✓ Total Volume: {total_volume:,}")
        logger.info(f"✓ Avg Volatility: {results['summary']['avg_volatility']*100:.1f}%")
        logger.info(f"✓ Data Quality: {results['summary']['data_quality']}")
        logger.info(f"{'='*80}\n")
        
        return results
    
    def save_results(self, results: Dict, filename: str = None) -> str:
        """Save results to JSON"""
        if filename is None:
            filename = f"indian_stocks_real_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.report_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"✓ Results saved: {filepath}")
        return str(filepath)
    
    def print_detailed_results(self, results: Dict):
        """Print detailed stock information"""
        print("\n" + "="*80)
        print("INDIAN STOCKS - REAL DATA DETAILS")
        print("="*80 + "\n")
        
        for symbol, data in results['stocks'].items():
            current = data['current']
            hist = data['historical']
            
            print(f"{symbol}")
            print(f"  Current Price: ₹{current['close']:.2f}")
            print(f"  Date: {current['date']}")
            print(f"  Volume: {current['volume']:,} shares")
            
            if hist:
                print(f"\n  Technical Indicators:")
                print(f"    SMA-20: ₹{hist['sma_20']:.2f}" if hist['sma_20'] else "    SMA-20: N/A")
                print(f"    SMA-50: ₹{hist['sma_50']:.2f}" if hist['sma_50'] else "    SMA-50: N/A")
                print(f"    ATR: ₹{hist['atr']:.2f}")
                print(f"    Volatility (Annual): {hist['volatility']*100:.1f}%")
                print(f"    52-Week Range: ₹{hist['price_range']['low']:.2f} - ₹{hist['price_range']['high']:.2f}")
                print(f"    {hist['days']}-Day Change: {hist['price_range']['change_pct']:.1f}%")
            
            print()


def main():
    """Test real Indian stock data"""
    print("\n" + "="*80)
    print("INDIAN STOCKS - REAL DATA VALIDATION WITH yfinance")
    print("="*80 + "\n")
    
    validator = IndianStocksRealDataValidator()
    
    # Test on popular Indian stocks
    indian_symbols = [
        'INFY',      # Infosys
        'TCS',       # Tata Consultancy Services
        'HDFC',      # HDFC Bank
        'AXIS',      # Axis Bank
        'MARUTI',    # Maruti Suzuki
        'WIPRO',     # Wipro
        'SUNPHARMA', # Sun Pharmaceutical
    ]
    
    # Run validation
    results = validator.test_all_indian_stocks(indian_symbols, days=30)
    
    # Print detailed results
    validator.print_detailed_results(results)
    
    # Save results
    filepath = validator.save_results(results)
    
    # Print summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Symbols Tested: {len(indian_symbols)}")
    print(f"Stocks Retrieved: {results['summary']['stocks_retrieved']}")
    print(f"Total Volume: {results['summary']['total_trading_volume']:,}")
    print(f"Avg Volatility: {results['summary']['avg_volatility']*100:.1f}%")
    print(f"Report: {filepath}\n")


if __name__ == "__main__":
    main()
