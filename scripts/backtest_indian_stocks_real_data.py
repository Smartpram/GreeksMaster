"""
Real Data Backtester - Indian Stocks Edition
=============================================

Backtests screeners on REAL Indian stock data from yfinance.
Uses NSE stock symbols (INFY, TCS, AXIS, etc.)

Key Features:
- Real prices from NSE via yfinance
- Real volatility and ATR
- Real trading volumes
- Technical indicators (SMA, ATR)
- Multi-symbol support
"""

import logging
import pandas as pd
import numpy as np
import yfinance as yf
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import sys
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Indian stock mapping
INDIAN_STOCKS = {
    'INFY': 'INFY.NS',
    'TCS': 'TCS.NS',
    'AXIS': 'AXISBANK.NS',
    'MARUTI': 'MARUTI.NS',
    'WIPRO': 'WIPRO.NS',
    'SUNPHARMA': 'SUNPHARMA.NS',
    'TECHM': 'TECHM.NS',
    'CIPLA': 'CIPLA.NS',
    'SBIN': 'SBIN.NS',
}


@dataclass
class IndianStockSignal:
    """Trading signal from Indian stock screener"""
    symbol: str
    date: str
    signal_type: str  # 'BREAKOUT', 'MOMENTUM', 'REVERSAL'
    price: float
    sma_20: float
    sma_50: float
    atr: float
    volatility: float
    volume: int
    confidence: float  # 0-1


class IndianStocksBacktester:
    """Backtest screeners on REAL Indian stock data"""
    
    def __init__(self):
        self.cache_dir = Path("data/indian_stocks_backtest")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir = Path("backtest_reports")
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.signals = []
        logger.info("Indian Stocks Backtester initialized")
    
    def get_yfinance_symbol(self, symbol: str) -> str:
        """Convert Indian symbol to yfinance format"""
        if symbol in INDIAN_STOCKS:
            return INDIAN_STOCKS[symbol]
        elif symbol.endswith('.NS') or symbol.endswith('.BO'):
            return symbol
        else:
            return f"{symbol}.NS"
    
    def analyze_stock(self, symbol: str, days: int = 60) -> Dict:
        """Analyze real Indian stock data"""
        try:
            yf_symbol = self.get_yfinance_symbol(symbol)
            logger.info(f"Analyzing {symbol} ({yf_symbol})...")
            
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period=f"{days}d")
            
            if hist.empty:
                logger.warning(f"No data for {symbol}")
                return None
            
            # Get latest data
            latest = hist.iloc[-1]
            current_price = float(latest['Close'])
            current_volume = int(latest['Volume'])
            
            # Technical indicators
            closes = hist['Close']
            highs = hist['High']
            lows = hist['Low']
            
            # Moving averages
            sma_20 = closes.rolling(window=20).mean().iloc[-1]
            sma_50 = closes.rolling(window=50).mean().iloc[-1]
            
            # ATR
            tr = pd.concat([
                highs - lows,
                abs(highs - closes.shift()),
                abs(lows - closes.shift())
            ], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean().iloc[-1]
            
            # Volatility
            returns = closes.pct_change()
            volatility = returns.std() * np.sqrt(252)
            
            # Volume analysis
            avg_volume = hist['Volume'].mean()
            volume_ratio = current_volume / avg_volume
            
            # Price momentum
            price_change_pct = (current_price - closes.iloc[-20]) / closes.iloc[-20] * 100
            
            return {
                'symbol': symbol,
                'yf_symbol': yf_symbol,
                'date': hist.index[-1].strftime('%Y-%m-%d'),
                'price': current_price,
                'sma_20': float(sma_20) if not pd.isna(sma_20) else None,
                'sma_50': float(sma_50) if not pd.isna(sma_50) else None,
                'atr': float(atr),
                'volatility': float(volatility),
                'volume': current_volume,
                'avg_volume': float(avg_volume),
                'volume_ratio': float(volume_ratio),
                'price_change_20d': float(price_change_pct),
                'data_points': len(hist)
            }
        
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def generate_signals(self, analysis: Dict) -> List[IndianStockSignal]:
        """Generate trading signals from analysis"""
        if not analysis:
            return []
        
        signals = []
        symbol = analysis['symbol']
        price = analysis['price']
        sma_20 = analysis['sma_20']
        sma_50 = analysis['sma_50']
        atr = analysis['atr']
        volatility = analysis['volatility']
        volume = analysis['volume']
        volume_ratio = analysis['volume_ratio']
        momentum = analysis['price_change_20d']
        
        # Signal 1: Breakout above SMA-20 with volume
        if sma_20 and price > sma_20 * 1.01 and volume_ratio > 1.0:
            confidence = min(0.9, 0.6 + volume_ratio * 0.1)
            signals.append(IndianStockSignal(
                symbol=symbol,
                date=analysis['date'],
                signal_type='BREAKOUT',
                price=price,
                sma_20=sma_20,
                sma_50=sma_50,
                atr=atr,
                volatility=volatility,
                volume=volume,
                confidence=confidence
            ))
        
        # Signal 2: Positive momentum + low volatility
        if momentum > 0 and volatility < 0.35 and volume_ratio > 0.9:
            confidence = min(0.85, 0.5 + (momentum / 10) * 0.1)
            signals.append(IndianStockSignal(
                symbol=symbol,
                date=analysis['date'],
                signal_type='MOMENTUM',
                price=price,
                sma_20=sma_20,
                sma_50=sma_50,
                atr=atr,
                volatility=volatility,
                volume=volume,
                confidence=confidence
            ))
        
        # Signal 3: Reversal from low volatility
        if volatility < 0.25 and abs(momentum) < 5 and volume_ratio > 1.1:
            confidence = 0.7
            signals.append(IndianStockSignal(
                symbol=symbol,
                date=analysis['date'],
                signal_type='REVERSAL',
                price=price,
                sma_20=sma_20,
                sma_50=sma_50,
                atr=atr,
                volatility=volatility,
                volume=volume,
                confidence=confidence
            ))
        
        return signals
    
    def backtest_symbol(self, symbol: str, days: int = 60) -> Dict:
        """Backtest single Indian stock"""
        logger.info(f"\n{'='*70}")
        logger.info(f"Backtesting: {symbol}")
        logger.info(f"{'='*70}")
        
        analysis = self.analyze_stock(symbol, days)
        if not analysis:
            logger.warning(f"Cannot backtest {symbol} - no data")
            return None
        
        # Generate signals
        signals = self.generate_signals(analysis)
        
        # Store signals
        for signal in signals:
            self.signals.append(signal)
        
        # Log results
        logger.info(f"  Current Price: ₹{analysis['price']:.2f}")
        logger.info(f"  SMA-20: ₹{analysis['sma_20']:.2f}" if analysis['sma_20'] else "  SMA-20: N/A")
        logger.info(f"  Volatility: {analysis['volatility']*100:.1f}%")
        logger.info(f"  Volume: {analysis['volume']:,} ({analysis['volume_ratio']:.1f}x avg)")
        logger.info(f"  20-Day Change: {analysis['price_change_20d']:.1f}%")
        logger.info(f"  Signals Generated: {len(signals)}")
        
        for i, signal in enumerate(signals, 1):
            logger.info(f"    {i}. {signal.signal_type} - Confidence: {signal.confidence:.1%}")
        
        return {
            'symbol': symbol,
            'analysis': analysis,
            'signals': [asdict(s) for s in signals],
            'signal_count': len(signals)
        }
    
    def backtest_all_symbols(self, symbols: List[str] = None, days: int = 60) -> Dict:
        """Backtest all Indian stocks"""
        if symbols is None:
            symbols = ['INFY', 'TCS', 'AXIS', 'MARUTI', 'WIPRO', 'SUNPHARMA']
        
        logger.info(f"\n{'='*80}")
        logger.info(f"INDIAN STOCKS BACKTESTER - REAL DATA")
        logger.info(f"{'='*80}")
        logger.info(f"Symbols: {', '.join(symbols)}")
        logger.info(f"Period: {days} days")
        logger.info(f"Data Source: Yahoo Finance (NSE)")
        logger.info(f"{'='*80}")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'data_source': 'yfinance (Real NSE Data)',
            'test_date': datetime.now().strftime('%Y-%m-%d'),
            'symbols_tested': len(symbols),
            'period_days': days,
            'backtest_results': {},
            'summary': {}
        }
        
        total_signals = 0
        successful_symbols = 0
        signal_types_count = {}
        
        for symbol in symbols:
            result = self.backtest_symbol(symbol, days)
            
            if result:
                results['backtest_results'][symbol] = result
                total_signals += result['signal_count']
                successful_symbols += 1
                
                for signal in result['signals']:
                    signal_type = signal['signal_type']
                    signal_types_count[signal_type] = signal_types_count.get(signal_type, 0) + 1
        
        # Calculate summary
        results['summary'] = {
            'symbols_analyzed': successful_symbols,
            'total_signals': total_signals,
            'signal_breakdown': signal_types_count,
            'avg_signals_per_stock': total_signals / successful_symbols if successful_symbols > 0 else 0,
            'data_quality': 'HIGH' if successful_symbols >= len(symbols) * 0.8 else 'PARTIAL'
        }
        
        return results
    
    def print_summary(self, results: Dict):
        """Print backtest summary"""
        print("\n" + "="*80)
        print("INDIAN STOCKS BACKTEST SUMMARY")
        print("="*80)
        print(f"Data Source: {results['data_source']}")
        print(f"Test Date: {results['test_date']}")
        print(f"Period: {results['period_days']} days\n")
        
        print("Results:")
        for symbol, result in results['backtest_results'].items():
            analysis = result['analysis']
            print(f"\n{symbol}:")
            print(f"  Price: ₹{analysis['price']:.2f}")
            print(f"  Volatility: {analysis['volatility']*100:.1f}%")
            print(f"  Signals: {result['signal_count']}")
            
            if result['signals']:
                for sig in result['signals']:
                    print(f"    • {sig['signal_type']} (Conf: {sig['confidence']:.0%})")
        
        summary = results['summary']
        print(f"\n{'='*80}")
        print("Overall Summary:")
        print(f"  Symbols Analyzed: {summary['symbols_analyzed']}")
        print(f"  Total Signals: {summary['total_signals']}")
        print(f"  Signal Types: {summary['signal_breakdown']}")
        print(f"  Avg Signals/Stock: {summary['avg_signals_per_stock']:.1f}")
        print(f"  Data Quality: {summary['data_quality']}")
        print(f"{'='*80}\n")
    
    def save_results(self, results: Dict, filename: str = None) -> str:
        """Save results to JSON"""
        if filename is None:
            filename = f"indian_stocks_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.report_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\n✓ Report saved: {filepath}")
        return str(filepath)


def main():
    """Run Indian stocks backtest"""
    backtester = IndianStocksBacktester()
    
    # Backtest popular Indian stocks
    indian_symbols = ['INFY', 'TCS', 'AXIS', 'MARUTI', 'WIPRO', 'SUNPHARMA']
    
    # Run backtest
    results = backtester.backtest_all_symbols(indian_symbols, days=60)
    
    # Print summary
    backtester.print_summary(results)
    
    # Save results
    filepath = backtester.save_results(results)
    
    print("="*80)
    print(f"✅ BACKTEST COMPLETE")
    print(f"Report: {filepath}")
    print("="*80)


if __name__ == "__main__":
    main()
