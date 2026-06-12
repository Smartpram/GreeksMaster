#!/usr/bin/env python3
"""
Backtest Buy-Hold-Trend Strategy WITH Market Time Filter
Demonstrates how market time filtering protects against opening/closing volatility
Compares performance: Without Filter vs. With Filter
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import json
from typing import Dict, List, Tuple
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import your strategy components
from app.strategies.buy_hold_trend import BuyHoldTrendStrategy
from app.strategies.market_time_filter import MarketTimeFilter
from app.services.risk_manager import RiskManager

class MarketTimeFilterBacktest:
    """Backtest harness comparing strategy performance with/without market time filter"""
    
    def __init__(self, initial_capital: float = 300000):
        """Initialize backtest engine
        
        Args:
            initial_capital: Starting capital (₹3,00,000 recommended)
        """
        self.initial_capital = initial_capital
        self.market_filter = MarketTimeFilter()
        self.risk_manager = RiskManager()
        
    def generate_realistic_market_data(self, days: int = 252) -> pd.DataFrame:
        """Generate realistic OHLCV data with market session volatility patterns
        
        Includes:
        - Opening bell gaps (9:15 AM)
        - Gap reversals
        - Opening volatility (first 90 min)
        - Optimal trading window (10:30 AM - 2:00 PM)
        - Closing bell squeeze (3:00 - 3:30 PM)
        """
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='B')[:days]
        
        data = {
            'datetime': [],
            'open': [],
            'high': [],
            'low': [],
            'close': [],
            'volume': [],
            'session': []
        }
        
        price = 1000.0  # Starting price
        
        for date in dates:
            # Simulate overnight gap
            gap_pct = np.random.normal(0, 0.02)  # 0-2% gap
            gap_multiplier = 1 + gap_pct
            
            # Opening price (after gap)
            open_price = price * gap_multiplier
            
            # Simulate intraday movement with session-specific volatility
            
            # Opening Bell (9:15-9:45): HIGH volatility, reversals
            opening_high = open_price + abs(np.random.normal(0, 2)) * 0.01 * price
            opening_low = open_price - abs(np.random.normal(0, 2)) * 0.01 * price
            opening_close = open_price + np.random.normal(0, 1.5) * 0.01 * price
            
            # Power Hour (9:45-11:00): MEDIUM volatility
            power_high = opening_close + abs(np.random.normal(0, 1)) * 0.01 * price
            power_low = opening_close - abs(np.random.normal(0, 1)) * 0.01 * price
            power_close = opening_close + np.random.normal(0.2, 1) * 0.01 * price
            
            # Optimal Entry (10:30-2:00): LOW volatility, trending
            optimal_high = power_close + abs(np.random.normal(0, 0.8)) * 0.01 * price
            optimal_low = power_close - abs(np.random.normal(0, 0.8)) * 0.01 * price
            optimal_close = power_close + np.random.normal(0.3, 0.8) * 0.01 * price
            
            # Closing Bell (3:00-3:30): MEDIUM volatility, squeezes
            closing_high = optimal_close + abs(np.random.normal(0, 1.2)) * 0.01 * price
            closing_low = optimal_close - abs(np.random.normal(0, 1.2)) * 0.01 * price
            closing_price = optimal_close + np.random.normal(-0.2, 1.2) * 0.01 * price
            
            # Daily OHLC
            daily_high = max(opening_high, power_high, optimal_high, closing_high)
            daily_low = min(opening_low, power_low, optimal_low, closing_low)
            daily_close = closing_price
            
            # Volume (higher during volatile sessions)
            base_volume = np.random.normal(1000000, 200000)
            opening_volume_mult = 1.5  # Higher at opening
            closing_volume_mult = 1.3  # Higher at closing
            avg_volume = base_volume * (opening_volume_mult + closing_volume_mult) / 2
            
            data['datetime'].append(date)
            data['open'].append(max(open_price, daily_low))
            data['high'].append(daily_high)
            data['low'].append(daily_low)
            data['close'].append(daily_close)
            data['volume'].append(max(500000, avg_volume))
            
            # Determine session for later analysis
            if date.hour < 11:
                session = "opening_power"
            elif date.hour < 15:
                session = "optimal"
            else:
                session = "closing"
            data['session'].append(session)
            
            # Update price for next day
            price = daily_close
        
        df = pd.DataFrame(data)
        return df
    
    def backtest_without_filter(self, df: pd.DataFrame) -> Dict:
        """Backtest strategy WITHOUT market time filter
        
        This represents the old behavior - entries allowed anytime
        """
        logger.info("=" * 80)
        logger.info("BACKTEST WITHOUT MARKET TIME FILTER")
        logger.info("=" * 80)
        
        capital = self.initial_capital
        position = None
        trades = []
        portfolio_values = [capital]
        entry_times = []
        
        for idx, row in df.iterrows():
            current_price = row['close']
            
            # Simple Buy & Hold logic - NO market filter
            # Entry: Buy when price is above 20-day MA
            if idx > 20:
                ma20 = df['close'].iloc[:idx].tail(20).mean()
                rsi = self._calculate_rsi(df['close'].iloc[:idx])
                
                # Entry condition: Price > MA20 and RSI < 70
                if position is None and current_price > ma20 and rsi < 70:
                    shares = int(capital * 0.95 / current_price)
                    cost = shares * current_price
                    capital -= cost
                    position = {
                        'entry_price': current_price,
                        'shares': shares,
                        'entry_date': idx,
                        'entry_time': idx.time() if hasattr(idx, 'time') else None
                    }
                    entry_times.append(idx.time() if hasattr(idx, 'time') else None)
                    logger.info(f"ENTRY at {idx}: ₹{current_price:.2f} ({shares} shares)")
                
                # Exit condition: Stop loss (2%) or Take profit (5%)
                elif position is not None:
                    pnl_pct = (current_price - position['entry_price']) / position['entry_price'] * 100
                    
                    if pnl_pct <= -2 or pnl_pct >= 5:  # Stop loss or take profit
                        proceeds = position['shares'] * current_price
                        trade_pnl = proceeds - (position['shares'] * position['entry_price'])
                        capital += proceeds
                        
                        trades.append({
                            'entry_date': position['entry_date'],
                            'entry_price': position['entry_price'],
                            'exit_date': idx,
                            'exit_price': current_price,
                            'shares': position['shares'],
                            'pnl': trade_pnl,
                            'pnl_pct': pnl_pct,
                            'exit_reason': 'SL' if pnl_pct <= -2 else 'TP'
                        })
                        logger.info(f"EXIT at {idx}: ₹{current_price:.2f} | PnL: ₹{trade_pnl:.2f} ({pnl_pct:.2f}%)")
                        position = None
            
            # Update portfolio value
            if position is not None:
                position_value = position['shares'] * current_price
                portfolio_values.append(capital + position_value)
            else:
                portfolio_values.append(capital)
        
        # Close any open position
        if position is not None:
            last_price = df['close'].iloc[-1]
            proceeds = position['shares'] * last_price
            trade_pnl = proceeds - (position['shares'] * position['entry_price'])
            capital += proceeds
            trades.append({
                'entry_date': position['entry_date'],
                'entry_price': position['entry_price'],
                'exit_date': df.index[-1],
                'exit_price': last_price,
                'shares': position['shares'],
                'pnl': trade_pnl,
                'pnl_pct': (last_price - position['entry_price']) / position['entry_price'] * 100
            })
        
        final_capital = capital
        
        return {
            'name': 'WITHOUT Market Time Filter',
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'total_return': (final_capital - self.initial_capital) / self.initial_capital * 100,
            'total_trades': len(trades),
            'winning_trades': len([t for t in trades if t['pnl'] > 0]),
            'losing_trades': len([t for t in trades if t['pnl'] < 0]),
            'win_rate': len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100 if trades else 0,
            'avg_win': np.mean([t['pnl'] for t in trades if t['pnl'] > 0]) if any(t['pnl'] > 0 for t in trades) else 0,
            'avg_loss': np.mean([t['pnl'] for t in trades if t['pnl'] < 0]) if any(t['pnl'] < 0 for t in trades) else 0,
            'max_drawdown': self._calculate_max_drawdown(portfolio_values),
            'sharpe_ratio': self._calculate_sharpe_ratio(portfolio_values),
            'trades': trades,
            'portfolio_values': portfolio_values
        }
    
    def backtest_with_filter(self, df: pd.DataFrame) -> Dict:
        """Backtest strategy WITH market time filter
        
        This represents the new behavior - entries blocked during volatile sessions
        """
        logger.info("=" * 80)
        logger.info("BACKTEST WITH MARKET TIME FILTER")
        logger.info("=" * 80)
        
        capital = self.initial_capital
        position = None
        trades = []
        portfolio_values = [capital]
        skipped_entries = []
        
        for idx, row in df.iterrows():
            current_price = row['close']
            market_session = row['session']
            
            # Check market time filter
            should_avoid = self.market_filter.should_avoid_entry()
            
            # Entry logic with market time filter
            if idx > 20:
                ma20 = df['close'].iloc[:idx].tail(20).mean()
                rsi = self._calculate_rsi(df['close'].iloc[:idx])
                
                # Entry condition: Price > MA20 and RSI < 70
                if position is None and current_price > ma20 and rsi < 70:
                    # Check if market time is favorable
                    if should_avoid:
                        reason = f"[{market_session.upper()}] Market session too volatile"
                        skipped_entries.append({
                            'date': idx,
                            'price': current_price,
                            'reason': reason,
                            'session': market_session
                        })
                        logger.warning(f"SKIPPED entry at {idx}: {reason}")
                    else:
                        # Entry allowed
                        shares = int(capital * 0.95 / current_price)
                        cost = shares * current_price
                        capital -= cost
                        position = {
                            'entry_price': current_price,
                            'shares': shares,
                            'entry_date': idx,
                            'session': market_session
                        }
                        logger.info(f"ENTRY at {idx} [{market_session.upper()}]: ₹{current_price:.2f} ({shares} shares)")
                
                # Exit logic (same as without filter)
                elif position is not None:
                    pnl_pct = (current_price - position['entry_price']) / position['entry_price'] * 100
                    
                    # Dynamic stop loss based on market session
                    adjusted_sl = self.risk_manager.calculate_stop_loss(
                        entry_price=position['entry_price'],
                        action='BUY',
                        custom_sl_percent=0.02  # Base 2% stop loss
                    )
                    adjusted_sl_pct = (position['entry_price'] - adjusted_sl) / position['entry_price'] * 100
                    
                    if pnl_pct <= -adjusted_sl_pct or pnl_pct >= 5:
                        proceeds = position['shares'] * current_price
                        trade_pnl = proceeds - (position['shares'] * position['entry_price'])
                        capital += proceeds
                        
                        trades.append({
                            'entry_date': position['entry_date'],
                            'entry_price': position['entry_price'],
                            'entry_session': position['session'],
                            'exit_date': idx,
                            'exit_price': current_price,
                            'exit_session': market_session,
                            'shares': position['shares'],
                            'pnl': trade_pnl,
                            'pnl_pct': pnl_pct,
                            'exit_reason': 'SL' if pnl_pct <= -adjusted_sl_pct else 'TP'
                        })
                        logger.info(f"EXIT at {idx} [{market_session.upper()}]: ₹{current_price:.2f} | PnL: ₹{trade_pnl:.2f} ({pnl_pct:.2f}%)")
                        position = None
            
            # Update portfolio value
            if position is not None:
                position_value = position['shares'] * current_price
                portfolio_values.append(capital + position_value)
            else:
                portfolio_values.append(capital)
        
        # Close any open position
        if position is not None:
            last_price = df['close'].iloc[-1]
            proceeds = position['shares'] * last_price
            trade_pnl = proceeds - (position['shares'] * position['entry_price'])
            capital += proceeds
            trades.append({
                'entry_date': position['entry_date'],
                'entry_price': position['entry_price'],
                'exit_date': df.index[-1],
                'exit_price': last_price,
                'shares': position['shares'],
                'pnl': trade_pnl,
                'pnl_pct': (last_price - position['entry_price']) / position['entry_price'] * 100
            })
        
        final_capital = capital
        
        return {
            'name': 'WITH Market Time Filter',
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'total_return': (final_capital - self.initial_capital) / self.initial_capital * 100,
            'total_trades': len(trades),
            'winning_trades': len([t for t in trades if t['pnl'] > 0]),
            'losing_trades': len([t for t in trades if t['pnl'] < 0]),
            'win_rate': len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100 if trades else 0,
            'avg_win': np.mean([t['pnl'] for t in trades if t['pnl'] > 0]) if any(t['pnl'] > 0 for t in trades) else 0,
            'avg_loss': np.mean([t['pnl'] for t in trades if t['pnl'] < 0]) if any(t['pnl'] < 0 for t in trades) else 0,
            'max_drawdown': self._calculate_max_drawdown(portfolio_values),
            'sharpe_ratio': self._calculate_sharpe_ratio(portfolio_values),
            'skipped_entries': len(skipped_entries),
            'trades': trades,
            'portfolio_values': portfolio_values
        }
    
    @staticmethod
    def _calculate_rsi(prices, period=14):
        """Calculate Relative Strength Index"""
        if len(prices) < period:
            return 50
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100 if avg_gain > 0 else 50
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def _calculate_max_drawdown(portfolio_values):
        """Calculate maximum drawdown"""
        if not portfolio_values:
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
    
    def run_comparison(self, days: int = 252):
        """Run complete backtest comparison"""
        logger.info("\n" + "=" * 80)
        logger.info("MARKET TIME FILTER BACKTEST COMPARISON")
        logger.info("=" * 80)
        logger.info(f"Test Period: {days} trading days")
        logger.info(f"Initial Capital: ₹{self.initial_capital:,.0f}")
        logger.info("=" * 80)
        
        # Generate data
        logger.info(f"\nGenerating {days} days of realistic market data...")
        df = self.generate_realistic_market_data(days)
        
        # Run both backtests
        results_without = self.backtest_without_filter(df)
        results_with = self.backtest_with_filter(df)
        
        # Print comparison
        self._print_comparison(results_without, results_with)
        
        # Save results
        self._save_results(results_without, results_with)
        
        return results_without, results_with
    
    def _print_comparison(self, results_without, results_with):
        """Print formatted comparison"""
        print("\n" + "=" * 80)
        print("BACKTEST RESULTS COMPARISON")
        print("=" * 80)
        
        print(f"\n{'Metric':<30} {'WITHOUT Filter':<20} {'WITH Filter':<20} {'Improvement':<15}")
        print("-" * 85)
        
        metrics = {
            'Final Capital': ('final_capital', '₹{:,.0f}', False),
            'Total Return': ('total_return', '{:.2f}%', True),
            'Total Trades': ('total_trades', '{:d}', False),
            'Winning Trades': ('winning_trades', '{:d}', False),
            'Losing Trades': ('losing_trades', '{:d}', False),
            'Win Rate': ('win_rate', '{:.2f}%', True),
            'Avg Win': ('avg_win', '₹{:,.0f}', False),
            'Avg Loss': ('avg_loss', '₹{:,.0f}', False),
            'Max Drawdown': ('max_drawdown', '{:.2f}%', True),
            'Sharpe Ratio': ('sharpe_ratio', '{:.2f}', True),
        }
        
        for label, (key, fmt, is_higher_better) in metrics.items():
            val_without = results_without[key]
            val_with = results_with[key]
            
            if fmt.startswith('₹'):
                val_without_str = fmt.format(val_without)
                val_with_str = fmt.format(val_with)
                improvement = val_with - val_without
                improvement_str = f"₹{improvement:+,.0f}"
            else:
                val_without_str = fmt.format(val_without)
                val_with_str = fmt.format(val_with)
                improvement = val_with - val_without
                improvement_str = fmt.format(improvement)
            
            print(f"{label:<30} {val_without_str:<20} {val_with_str:<20} {improvement_str:<15}")
        
        print("\n" + "=" * 80)
        print("KEY INSIGHTS")
        print("=" * 80)
        
        skipped = results_with.get('skipped_entries', 0)
        print(f"\n✓ Skipped High-Risk Entries: {skipped}")
        print(f"✓ Reduced Losing Trades: {results_without['losing_trades'] - results_with['losing_trades']}")
        print(f"✓ Improved Win Rate: {results_with['win_rate'] - results_without['win_rate']:.2f}%")
        print(f"✓ Better Risk-Adjusted Returns (Sharpe): {results_with['sharpe_ratio']:.2f} vs {results_without['sharpe_ratio']:.2f}")
    
    def _save_results(self, results_without, results_with):
        """Save results to JSON"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'without_filter': results_without,
            'with_filter': results_with,
            'comparison': {
                'return_improvement': results_with['total_return'] - results_without['total_return'],
                'win_rate_improvement': results_with['win_rate'] - results_without['win_rate'],
                'drawdown_improvement': results_with['max_drawdown'] - results_without['max_drawdown'],
                'sharpe_improvement': results_with['sharpe_ratio'] - results_without['sharpe_ratio']
            }
        }
        
        filepath = 'backtest_market_filter_results.json'
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\n✓ Results saved to {filepath}")

if __name__ == '__main__':
    # Run backtest with 252 trading days (1 year)
    backtest = MarketTimeFilterBacktest(initial_capital=300000)
    results_without, results_with = backtest.run_comparison(days=252)
