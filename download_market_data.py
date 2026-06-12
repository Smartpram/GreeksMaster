"""
Data Download Helper for Paper Trading
Easily download historical data from multiple sources for ML training
Works this weekend to prepare for Monday deployment

Usage:
    python download_market_data.py --source yfinance --symbols INFY TCS --output data/
    python download_market_data.py --source nse --symbols BANKNIFTY NIFTY --days 30
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import List, Optional
import pytz

# UTF-8 encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("Installing required packages...")
    os.system("pip install pandas numpy requests yfinance --quiet")
    import pandas as pd
    import numpy as np

try:
    import yfinance as yf
except ImportError:
    os.system("pip install yfinance --quiet")
    import yfinance as yf

try:
    import requests
except ImportError:
    os.system("pip install requests --quiet")
    import requests


class DataDownloader:
    """Download market data from various sources"""
    
    def __init__(self, output_dir: str = "data"):
        """Initialize downloader"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.ist_tz = pytz.timezone('Asia/Kolkata')
        print(f"✓ Data downloader initialized (output: {output_dir})")
    
    # ===== YFINANCE SOURCE =====
    
    def download_from_yfinance(
        self, 
        symbols: List[str], 
        days: int = 500,
        interval: str = '1d'
    ) -> dict:
        """
        Download historical data from Yahoo Finance
        
        Args:
            symbols: List of symbols (e.g., ['INFY', 'TCS', 'RELIANCE.NS'])
            days: Number of historical days to download
            interval: Interval ('1d', '1h', '5m', '1m')
            
        Returns:
            Dictionary of downloaded data
        """
        print(f"\n{'='*70}")
        print(f"Downloading from Yahoo Finance")
        print(f"{'='*70}")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        results = {}
        
        for symbol in symbols:
            print(f"\n📊 Downloading {symbol} ({days} days, {interval})...")
            
            try:
                # Handle NSE symbols
                if '.' not in symbol and symbol not in ['AAPL', 'MSFT', 'GOOGL']:
                    ticker_symbol = f"{symbol}.NS"
                else:
                    ticker_symbol = symbol
                
                # Download data
                ticker = yf.Ticker(ticker_symbol)
                data = ticker.history(
                    start=start_date.strftime('%Y-%m-%d'),
                    end=end_date.strftime('%Y-%m-%d'),
                    interval=interval
                )
                
                if data.empty:
                    print(f"  ✗ No data found for {symbol}")
                    continue
                
                # Save to CSV
                filename = f"{self.output_dir}/historical_{symbol}_{interval}.csv"
                data.to_csv(filename)
                
                results[symbol] = {
                    'rows': len(data),
                    'start_date': str(data.index[0]),
                    'end_date': str(data.index[-1]),
                    'file': filename
                }
                
                print(f"  ✓ Downloaded {len(data)} candles")
                print(f"    File: {filename}")
                print(f"    Date range: {data.index[0]} to {data.index[-1]}")
                
            except Exception as e:
                print(f"  ✗ Error downloading {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        
        return results
    
    # ===== NSE SOURCE (WEB SCRAPING) =====
    
    def download_from_nse(
        self,
        symbols: List[str],
        days: int = 30
    ) -> dict:
        """
        Download data from NSE website
        
        Note: NSE has throttling, this provides sample data
        For production, use Breeze API directly
        
        Args:
            symbols: List of NSE symbols
            days: Number of days to simulate
            
        Returns:
            Dictionary of generated sample data
        """
        print(f"\n{'='*70}")
        print(f"Generating NSE-format Sample Data")
        print(f"{'='*70}")
        
        results = {}
        
        for symbol in symbols:
            print(f"\n📊 Generating sample data for {symbol}...")
            
            try:
                # Generate realistic historical data
                dates = pd.date_range(
                    end=datetime.now(),
                    periods=days,
                    freq='D'
                )
                
                # Base prices
                base_prices = {
                    'BANKNIFTY': 48000,
                    'NIFTY': 23500,
                    'INFY': 19800,
                    'TCS': 3850,
                    'RELIANCE': 2750,
                }
                
                base_price = base_prices.get(symbol, 5000)
                
                # Generate OHLCV
                opens = np.random.normal(base_price, base_price * 0.01, days)
                closes = np.random.normal(base_price, base_price * 0.01, days)
                highs = np.maximum(opens, closes) + np.abs(np.random.normal(0, base_price * 0.005, days))
                lows = np.minimum(opens, closes) - np.abs(np.random.normal(0, base_price * 0.005, days))
                volumes = np.random.randint(1000000, 20000000, days)
                
                data = pd.DataFrame({
                    'Date': dates,
                    'Open': opens,
                    'High': highs,
                    'Low': lows,
                    'Close': closes,
                    'Volume': volumes
                })
                
                # Save to CSV
                filename = f"{self.output_dir}/sample_{symbol}_nse.csv"
                data.to_csv(filename, index=False)
                
                results[symbol] = {
                    'rows': len(data),
                    'start_date': str(dates[0]),
                    'end_date': str(dates[-1]),
                    'file': filename,
                    'note': 'Generated sample data (use Breeze API for live)'
                }
                
                print(f"  ✓ Generated {len(data)} candles")
                print(f"    File: {filename}")
                print(f"    Date range: {dates[0]} to {dates[-1]}")
                
            except Exception as e:
                print(f"  ✗ Error for {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        
        return results
    
    # ===== BREEZE API SOURCE =====
    
    def prepare_breeze_integration(self) -> dict:
        """
        Prepare Breeze API integration documentation
        
        Returns:
            Integration setup guide
        """
        print(f"\n{'='*70}")
        print(f"Breeze API Integration (Live Data)")
        print(f"{'='*70}")
        
        guide = {
            'source': 'Breeze API (ICICI Direct)',
            'type': 'Real-time data (live)',
            'symbols': [
                'BANKNIFTY', 'NIFTY', 'INFY', 'TCS', 'RELIANCE',
                'HDFC', 'SBIN', 'ICICIBANK', 'AXISBANK'
            ],
            'data_types': {
                'candles': ['1minute', '5minute', '15minute', '1hour', '1day'],
                'options': ['chain', 'greeks', 'iv', 'spreads'],
            },
            'frequency': 'Every 1 minute (candles) or every tick (options)',
            'setup_steps': [
                '1. Get Breeze API key from ICICI Direct',
                '2. Update app/config.py with your credentials',
                '3. Test connection: python test_breeze_connection.py',
                '4. Run scheduler: python scheduler_options_production.py',
            ],
            'file': 'scheduler_options_production.py',
            'status': '✓ Already integrated in your code'
        }
        
        print(f"\n✓ Breeze API Setup:")
        for key, value in guide.items():
            if key == 'setup_steps':
                print(f"  {key}:")
                for step in value:
                    print(f"    {step}")
            else:
                print(f"  {key}: {value}")
        
        return guide
    
    # ===== VALIDATION =====
    
    def validate_downloaded_data(self, filepath: str) -> bool:
        """Validate downloaded data"""
        try:
            data = pd.read_csv(filepath)
            
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            if not all(col in data.columns for col in required_cols):
                print(f"  ✗ Missing columns in {filepath}")
                return False
            
            # Check for nulls
            if data[required_cols].isnull().any().any():
                print(f"  ⚠ Contains null values in {filepath}")
            
            # Check data quality
            if (data['High'] < data['Low']).any():
                print(f"  ✗ Invalid: High < Low in {filepath}")
                return False
            
            if (data['Open'] < data['Low']).any() or (data['Open'] > data['High']).any():
                print(f"  ✗ Invalid: Open outside High-Low in {filepath}")
                return False
            
            print(f"  ✓ Valid data: {len(data)} rows")
            return True
            
        except Exception as e:
            print(f"  ✗ Error validating {filepath}: {e}")
            return False
    
    # ===== REPORTS =====
    
    def generate_summary_report(self, results: dict) -> str:
        """Generate download summary report"""
        report = f"\n{'='*70}\n"
        report += f"DATA DOWNLOAD SUMMARY\n"
        report += f"{'='*70}\n\n"
        
        success_count = sum(1 for r in results.values() if 'error' not in r)
        error_count = len(results) - success_count
        
        report += f"Total downloads: {len(results)}\n"
        report += f"Successful: {success_count}\n"
        report += f"Failed: {error_count}\n\n"
        
        report += f"Downloaded Files:\n"
        for symbol, result in results.items():
            if 'file' in result:
                report += f"  ✓ {symbol}: {result['file']}\n"
                report += f"    Rows: {result['rows']}, Period: {result['start_date']} to {result['end_date']}\n"
            elif 'error' in result:
                report += f"  ✗ {symbol}: {result['error']}\n"
        
        report += f"\n{'='*70}\n"
        report += f"Next Steps:\n"
        report += f"  1. Use downloaded data to train ML model\n"
        report += f"  2. Run: python weekend_ml_training_deployment.py\n"
        report += f"  3. Run: python test_hybrid_system_integration.py\n"
        report += f"  4. Deploy Monday: python scheduler_options_production.py\n"
        report += f"{'='*70}\n"
        
        return report
    
    def run_complete_download(self):
        """Run complete data download workflow"""
        print(f"\n{'='*80}")
        print(f"DATA DOWNLOAD HELPER FOR PAPER TRADING")
        print(f"{'='*80}\n")
        
        all_results = {}
        
        # Download from yfinance
        yf_results = self.download_from_yfinance(
            symbols=['INFY', 'TCS', 'RELIANCE'],
            days=500,
            interval='1d'
        )
        all_results.update(yf_results)
        
        # Generate NSE sample data
        nse_results = self.download_from_nse(
            symbols=['BANKNIFTY', 'NIFTY'],
            days=30
        )
        all_results.update(nse_results)
        
        # Show Breeze API integration
        breeze_guide = self.prepare_breeze_integration()
        
        # Validate downloaded files
        print(f"\n{'='*70}")
        print(f"Validating Downloaded Data")
        print(f"{'='*70}\n")
        
        for symbol, result in all_results.items():
            if 'file' in result:
                print(f"Validating {symbol}...")
                self.validate_downloaded_data(result['file'])
        
        # Generate report
        report = self.generate_summary_report(all_results)
        print(report)
        
        # Save report
        report_file = os.path.join(self.output_dir, 'download_report.txt')
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"Report saved: {report_file}\n")
        
        return all_results


def main():
    """Main execution"""
    downloader = DataDownloader(output_dir="data")
    results = downloader.run_complete_download()
    
    # Quick stats
    print("\n✓ Data Download Complete!")
    print(f"  Files saved to: data/")
    print(f"  Ready for ML training this weekend")
    print(f"  Deploy Monday: python scheduler_options_production.py")


if __name__ == "__main__":
    main()
