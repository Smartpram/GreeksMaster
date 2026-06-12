#!/usr/bin/env python3
"""
Breeze Backtest - Real Data or Fallback to Simulated
Runs backtest with real Breeze API data when available, otherwise uses high-quality simulated data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.config import Config
from app.services.breeze_api import BreezeAPIService
from app.services.data_stream import HistoricalDataService
from app.strategies.market_time_filter import MarketTimeFilter
from app.services.risk_manager import RiskManager

class RealDataBacktest:
    """Backtest engine - Real or Simulated Data"""
    
    def __init__(self, initial_capital=300000):
        self.initial_capital = initial_capital
        self.config = Config()
        self.market_filter = MarketTimeFilter()
        self.risk_manager = RiskManager()
        
        # Try to initialize Breeze (optional)
        self.breeze_service = None
        self.historical_service = None
        try:
            self.breeze_service = BreezeAPIService()
            self.historical_service = HistoricalDataService(self.breeze_service)
            logger.info("✓ Breeze API available for real data")
        except Exception as e:
            logger.warning(f"Breeze API not available: {e} - Using simulated data")
    
    def get_data(self, stock_code, days_back=252, use_real_data=True):
        """Get historical data - Real or Simulated
        
        Args:
            stock_code: Stock code (e.g., 'INFY')
            days_back: Days of history
            use_real_data: Try real data first if available
            
        Returns:
            DataFrame with OHLCV data
        """
        # Try real data
        if use_real_data and self.historical_service:
            logger.info(f"🔄 Fetching REAL data for {stock_code}...")
            try:
                data = self.historical_service.get_historical_data(
                    instrument=stock_code,
                    interval='1day',
                    days_back=days_back
                )
                
                if data and len(data) > 0:
                    df = pd.DataFrame(data)
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df = df.set_index('datetime').sort_index()
                    logger.info(f"✓ Fetched {len(df)} real candles for {stock_code}")
                    return df
            except Exception as e:
                logger.warning(f"Could not fetch real data: {e}")
        
        # Fallback to simulated data
        logger.info(f"📊 Generating SIMULATED data for {stock_code}...")
        return self._generate_simulated_data(stock_code, days_back)
    
    @staticmethod
    def _generate_simulated_data(stock_code, days_back):
        """Generate high-quality simulated data"""
        np.random.seed(hash(stock_code) % 2**32)  # Consistent per stock
        
        dates = pd.date_range(end=datetime.now(), periods=days_back, freq='B')
        
        # Starting price varies by stock
        price_map = {
            'INFY': 1400,
            'RELIANCE': 2000,
            'TCS': 3500,
            'HDFC': 1500,
            'BAJAJ': 900,
            'HDFCBANK': 1400,
        }
        
        price = price_map.get(stock_code, 1000)
        
        data = {'datetime': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}
        
        for i, date in enumerate(dates):
            # Trend component
            trend = 0.0002 * i
            
            # Daily volatility
            daily_return = np.random.normal(trend, 0.015)
            
            # OHLC generation
            open_price = price * (1 + np.random.normal(0, 0.005))
            close_price = open_price * (1 + daily_return)
            
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.01)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.01)))
            
            volume = np.random.normal(1000000, 300000)
            
            data['datetime'].append(date)
            data['open'].append(open_price)
            data['high'].append(high_price)
            data['low'].append(low_price)
            data['close'].append(close_price)
            data['volume'].append(max(500000, volume))
            
            price = close_price
        
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime')
        
        logger.info(f"✓ Generated {len(df)} simulated candles for {stock_code}")
        return df
    
    def backtest(self, stock_code, df):
        """Run backtest on data"""
        logger.info(f"\n{'='*80}")
        logger.info(f"BACKTEST: {stock_code} | {len(df)} days | Market Time Filter ACTIVE")
        logger.info(f"{'='*80}\n")
        
        capital = self.initial_capital
        position = None
        trades = []
        portfolio_vals = [capital]
        blocked = skipped = 0
        
        for idx, row in df.iterrows():
            price = row['close']
            
            if idx > 20:
                ma20 = df['close'].loc[:idx].tail(20).mean()
                rsi = self._rsi(df['close'].loc[:idx].values)
                
                # Entry with market filter
                if position is None and price > ma20 and rsi < 70:
                    session = self.market_filter.get_current_session()
                    should_avoid = self.market_filter.should_avoid_entry()
                    
                    if should_avoid:
                        blocked += 1
                    else:
                        # Entry
                        shares = int(capital * 0.95 / price)
                        cost = shares * price
                        capital -= cost
                        position = {
                            'entry': price,
                            'shares': shares,
                            'date': idx,
                            'session': session
                        }
                        logger.info(f"✓ ENTRY {idx.date()}: ₹{price:.0f} ({shares} shares) [{session}]")
                
                # Exit
                elif position:
                    pnl_pct = (price - position['entry']) / position['entry'] * 100
                    
                    sl_price = self.risk_manager.calculate_stop_loss(
                        position['entry'], 'BUY', 0.02
                    )
                    sl_pct = (position['entry'] - sl_price) / position['entry'] * 100
                    
                    if pnl_pct >= 5:  # Take profit
                        pnl = position['shares'] * (price - position['entry'])
                        capital += position['shares'] * price
                        trades.append({'pnl': pnl, 'pct': pnl_pct, 'type': 'TP'})
                        logger.info(f"✓ EXIT (TP) {idx.date()}: ₹{price:.0f} | PnL: ₹{pnl:,.0f} ({pnl_pct:.2f}%)")
                        position = None
                    
                    elif pnl_pct <= -sl_pct:  # Stop loss
                        pnl = position['shares'] * (price - position['entry'])
                        capital += position['shares'] * price
                        trades.append({'pnl': pnl, 'pct': pnl_pct, 'type': 'SL'})
                        logger.info(f"✓ EXIT (SL) {idx.date()}: ₹{price:.0f} | PnL: ₹{pnl:,.0f} ({pnl_pct:.2f}%)")
                        position = None
            
            # Portfolio value
            if position:
                portfolio_vals.append(capital + position['shares'] * price)
            else:
                portfolio_vals.append(capital)
        
        # Close position at end
        if position:
            price = df['close'].iloc[-1]
            pnl = position['shares'] * (price - position['entry'])
            capital += position['shares'] * price
            trades.append({'pnl': pnl})
        
        # Calculate metrics
        wins = [t for t in trades if t['pnl'] > 0]
        losses = [t for t in trades if t['pnl'] < 0]
        
        return {
            'stock': stock_code,
            'start': df.index[0].date(),
            'end': df.index[-1].date(),
            'final_capital': capital,
            'return': (capital - self.initial_capital) / self.initial_capital * 100,
            'trades': len(trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': len(wins) / len(trades) * 100 if trades else 0,
            'avg_win': np.mean([t['pnl'] for t in wins]) if wins else 0,
            'avg_loss': np.mean([t['pnl'] for t in losses]) if losses else 0,
            'drawdown': self._max_drawdown(portfolio_vals),
            'sharpe': self._sharpe(portfolio_vals),
            'blocked': blocked,
            'skipped': skipped,
            'portfolio': portfolio_vals
        }
    
    @staticmethod
    def _rsi(prices, period=14):
        if len(prices) < period: return 50
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain, avg_loss = np.mean(gains), np.mean(losses)
        if avg_loss == 0: return 100 if avg_gain > 0 else 50
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def _max_drawdown(vals):
        if len(vals) < 2: return 0
        arr = np.array(vals)
        returns = arr / arr[0]
        running_max = np.maximum.accumulate(returns)
        dd = (returns - running_max) / running_max * 100
        return np.min(dd)
    
    @staticmethod
    def _sharpe(vals, rf=0.05):
        if len(vals) < 2: return 0
        rets = np.diff(vals) / vals[:-1]
        excess = rets - (rf / 252)
        if np.std(excess) == 0: return 0
        return np.mean(excess) / np.std(excess) * np.sqrt(252)
    
    def print_results(self, r):
        """Print backtest results"""
        print(f"\n{'='*80}")
        print(f"RESULTS: {r['stock']}")
        print(f"{'='*80}\n")
        print(f"Period:       {r['start']} to {r['end']}")
        print(f"Final Cap:    ₹{r['final_capital']:,.0f}")
        print(f"Return:       {r['return']:.2f}% ✓")
        print(f"Trades:       {r['trades']} ({r['wins']}W/{r['losses']}L)")
        print(f"Win Rate:     {r['win_rate']:.1f}%")
        print(f"Avg Win/Loss: ₹{r['avg_win']:,.0f} / ₹{r['avg_loss']:,.0f}")
        print(f"Drawdown:     {r['drawdown']:.2f}%")
        print(f"Sharpe:       {r['sharpe']:.2f}")
        print(f"Blocked:      {r['blocked']} risky entries")
        print(f"{'='*80}\n")

def main():
    print("\n" + "#"*80)
    print("# BACKTEST: BUY-HOLD-TREND WITH MARKET TIME FILTER")
    print("# Real Breeze Data or High-Quality Simulated Data")
    print("#"*80 + "\n")
    
    # Get stocks from user
    print("Select stocks:")
    print("  1. INFY")
    print("  2. RELIANCE")
    print("  3. TCS")
    print("  4. HDFC")
    print("  5. All 4")
    
    choice = input("\nChoice (1-5) [5]: ").strip() or "5"
    
    stocks_map = {
        '1': ['INFY'],
        '2': ['RELIANCE'],
        '3': ['TCS'],
        '4': ['HDFC'],
        '5': ['INFY', 'RELIANCE', 'TCS', 'HDFC']
    }
    
    stocks = stocks_map.get(choice, ['INFY', 'RELIANCE', 'TCS', 'HDFC'])
    
    # Get period
    print("\nBacktest period:")
    print("  1. 20 days")
    print("  2. 60 days")
    print("  3. 120 days")
    print("  4. 252 days")
    
    period_choice = input("\nChoice (1-4) [4]: ").strip() or "4"
    
    period_map = {'1': 20, '2': 60, '3': 120, '4': 252}
    days = period_map.get(period_choice, 252)
    
    print(f"\n🚀 Starting backtest: {', '.join(stocks)} | {days} days\n")
    
    # Run backtest
    engine = RealDataBacktest(300000)
    results = {}
    
    for stock in stocks:
        try:
            df = engine.get_data(stock, days_back=days)
            result = engine.backtest(stock, df)
            engine.print_results(result)
            results[stock] = result
        except Exception as e:
            logger.error(f"Error with {stock}: {e}")
    
    # Summary
    if results:
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}\n")
        print(f"{'Stock':<12} {'Return':<12} {'Win Rate':<12} {'Max DD':<12} {'Sharpe':<12}")
        print("-" * 60)
        
        for stock, r in results.items():
            print(f"{stock:<12} {r['return']:>10.2f}% {r['win_rate']:>10.1f}% {r['drawdown']:>10.2f}% {r['sharpe']:>10.2f}")
    
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    main()
