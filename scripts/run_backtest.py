#!/usr/bin/env python3
"""
Comprehensive Backtesting Suite for MyBreezeApp Strategies
Tests all implemented trading strategies with detailed performance analysis
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import seaborn as sns

# Set style
sns.set_style("darkgrid")
plt.rcParams['figure.figsize'] = (14, 8)

def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 90)
    print(f"  {title}")
    print("=" * 90)

def print_subsection(title):
    """Print formatted subsection header"""
    print(f"\n  {title}")
    print("  " + "-" * 86)

def generate_sample_backtest_data():
    """Generate sample OHLCV data for backtesting"""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    
    # Generate realistic price data with trend
    price = 100
    prices = []
    volumes = []
    opens = []
    highs = []
    lows = []
    
    for i in range(len(dates)):
        # Add trend and noise
        price = price + np.random.normal(0.5, 2)  # Slight uptrend with volatility
        open_price = price + np.random.normal(0, 1)
        high_price = max(price, open_price) + abs(np.random.normal(0, 1))
        low_price = min(price, open_price) - abs(np.random.normal(0, 1))
        volume = np.random.normal(1000000, 200000)
        
        opens.append(open_price)
        highs.append(high_price)
        lows.append(low_price)
        prices.append(price)
        volumes.append(max(100000, volume))
    
    df = pd.DataFrame({
        'datetime': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': prices,
        'volume': volumes
    })
    
    return df

def backtest_buy_hold_strategy(df: pd.DataFrame) -> Dict:
    """Simple Buy & Hold strategy backtest"""
    initial_capital = 100000
    shares = 0
    capital = initial_capital
    entry_price = 0
    trades = []
    portfolio_values = [initial_capital]
    
    # Entry condition: Buy at first data point
    entry_signal = True
    
    for idx, row in df.iterrows():
        current_price = row['close']
        
        # Entry
        if entry_signal and shares == 0:
            shares = capital / current_price
            entry_price = current_price
            trades.append({
                'date': idx,
                'type': 'BUY',
                'price': current_price,
                'shares': shares,
                'capital': capital
            })
            entry_signal = False
        
        # Update portfolio value
        if shares > 0:
            portfolio_value = shares * current_price
        else:
            portfolio_value = capital
        
        portfolio_values.append(portfolio_value)
    
    # Exit at end
    if shares > 0:
        exit_price = df['close'].iloc[-1]
        capital = shares * exit_price
        trades.append({
            'date': df.index[-1],
            'type': 'SELL',
            'price': exit_price,
            'shares': shares,
            'capital': capital,
            'pnl': capital - initial_capital,
            'pnl_pct': ((capital - initial_capital) / initial_capital) * 100
        })
    
    return {
        'strategy': 'Buy & Hold',
        'total_return': ((capital - initial_capital) / initial_capital) * 100,
        'final_capital': capital,
        'trades': len(trades),
        'max_dd': calculate_max_drawdown(portfolio_values),
        'sharpe': calculate_sharpe_ratio(portfolio_values),
        'trades_list': trades,
        'portfolio_values': portfolio_values
    }

def backtest_sma_crossover(df: pd.DataFrame) -> Dict:
    """Simple Moving Average Crossover strategy"""
    initial_capital = 100000
    shares = 0
    capital = initial_capital
    trades = []
    portfolio_values = [initial_capital]
    
    # Calculate SMAs
    df['SMA20'] = df['close'].rolling(window=20).mean()
    df['SMA50'] = df['close'].rolling(window=50).mean()
    
    in_trade = False
    
    for idx, row in df.iterrows():
        if pd.isna(row['SMA20']) or pd.isna(row['SMA50']):
            portfolio_values.append(capital if shares == 0 else shares * row['close'])
            continue
        
        current_price = row['close']
        
        # Buy signal: SMA20 crosses above SMA50
        if not in_trade and row['SMA20'] > row['SMA50']:
            if capital > 0:
                shares = capital / current_price
                trades.append({'date': idx, 'type': 'BUY', 'price': current_price})
                capital = 0
                in_trade = True
        
        # Sell signal: SMA20 crosses below SMA50
        elif in_trade and row['SMA20'] < row['SMA50']:
            if shares > 0:
                exit_price = current_price
                pnl = (exit_price - trades[-1]['price']) * shares
                trades.append({'date': idx, 'type': 'SELL', 'price': exit_price, 'pnl': pnl})
                capital = shares * exit_price
                shares = 0
                in_trade = False
        
        # Update portfolio value
        if shares > 0:
            portfolio_value = shares * current_price
        else:
            portfolio_value = capital
        portfolio_values.append(portfolio_value)
    
    # Close any open position
    if shares > 0:
        exit_price = df['close'].iloc[-1]
        capital = shares * exit_price
    
    return {
        'strategy': 'SMA Crossover (20/50)',
        'total_return': ((capital - initial_capital) / initial_capital) * 100,
        'final_capital': capital,
        'trades': len([t for t in trades if t['type'] == 'BUY']),
        'max_dd': calculate_max_drawdown(portfolio_values),
        'sharpe': calculate_sharpe_ratio(portfolio_values),
        'trades_list': trades,
        'portfolio_values': portfolio_values
    }

def backtest_rsi_strategy(df: pd.DataFrame) -> Dict:
    """RSI-based Mean Reversion strategy"""
    initial_capital = 100000
    shares = 0
    capital = initial_capital
    trades = []
    portfolio_values = [initial_capital]
    
    # Calculate RSI
    df['RSI'] = calculate_rsi(df['close'], period=14)
    
    for idx, row in df.iterrows():
        if pd.isna(row['RSI']):
            portfolio_values.append(capital if shares == 0 else shares * row['close'])
            continue
        
        current_price = row['close']
        
        # Buy signal: RSI < 30 (oversold)
        if shares == 0 and row['RSI'] < 30:
            if capital > 0:
                shares = capital / current_price
                trades.append({'date': idx, 'type': 'BUY', 'price': current_price})
                capital = 0
        
        # Sell signal: RSI > 70 (overbought)
        elif shares > 0 and row['RSI'] > 70:
            exit_price = current_price
            pnl = (exit_price - trades[-1]['price']) * shares
            trades.append({'date': idx, 'type': 'SELL', 'price': exit_price, 'pnl': pnl})
            capital = shares * exit_price
            shares = 0
        
        # Update portfolio value
        if shares > 0:
            portfolio_value = shares * current_price
        else:
            portfolio_value = capital
        portfolio_values.append(portfolio_value)
    
    # Close any open position
    if shares > 0:
        exit_price = df['close'].iloc[-1]
        capital = shares * exit_price
    
    return {
        'strategy': 'RSI Mean Reversion (14)',
        'total_return': ((capital - initial_capital) / initial_capital) * 100,
        'final_capital': capital,
        'trades': len([t for t in trades if t['type'] == 'BUY']),
        'max_dd': calculate_max_drawdown(portfolio_values),
        'sharpe': calculate_sharpe_ratio(portfolio_values),
        'trades_list': trades,
        'portfolio_values': portfolio_values
    }

def backtest_momentum_strategy(df: pd.DataFrame) -> Dict:
    """Momentum strategy with ROC indicator"""
    initial_capital = 100000
    shares = 0
    capital = initial_capital
    trades = []
    portfolio_values = [initial_capital]
    
    # Calculate ROC (Rate of Change)
    df['ROC'] = ((df['close'] - df['close'].shift(10)) / df['close'].shift(10)) * 100
    
    for idx, row in df.iterrows():
        if pd.isna(row['ROC']):
            portfolio_values.append(capital if shares == 0 else shares * row['close'])
            continue
        
        current_price = row['close']
        
        # Buy signal: Positive momentum
        if shares == 0 and row['ROC'] > 2:
            if capital > 0:
                shares = capital / current_price
                trades.append({'date': idx, 'type': 'BUY', 'price': current_price})
                capital = 0
        
        # Sell signal: Negative momentum
        elif shares > 0 and row['ROC'] < -1:
            exit_price = current_price
            pnl = (exit_price - trades[-1]['price']) * shares
            trades.append({'date': idx, 'type': 'SELL', 'price': exit_price, 'pnl': pnl})
            capital = shares * exit_price
            shares = 0
        
        # Update portfolio value
        if shares > 0:
            portfolio_value = shares * current_price
        else:
            portfolio_value = capital
        portfolio_values.append(portfolio_value)
    
    # Close any open position
    if shares > 0:
        exit_price = df['close'].iloc[-1]
        capital = shares * exit_price
    
    return {
        'strategy': 'Momentum (ROC-10)',
        'total_return': ((capital - initial_capital) / initial_capital) * 100,
        'final_capital': capital,
        'trades': len([t for t in trades if t['type'] == 'BUY']),
        'max_dd': calculate_max_drawdown(portfolio_values),
        'sharpe': calculate_sharpe_ratio(portfolio_values),
        'trades_list': trades,
        'portfolio_values': portfolio_values
    }

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    deltas = np.diff(prices)
    seed = deltas[:period + 1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 1
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)
    
    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta
        
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down if down != 0 else 1
        rsi[i] = 100. - 100. / (1. + rs)
    
    return rsi

def calculate_max_drawdown(portfolio_values):
    """Calculate maximum drawdown"""
    cummax = np.maximum.accumulate(portfolio_values)
    drawdown = (np.array(portfolio_values) - cummax) / cummax
    max_dd = np.min(drawdown) * 100
    return max_dd

def calculate_sharpe_ratio(portfolio_values, rf_rate=0.02):
    """Calculate Sharpe Ratio"""
    returns = np.diff(portfolio_values) / portfolio_values[:-1]
    excess_returns = returns - (rf_rate / 252)  # Daily risk-free rate
    sharpe = np.sqrt(252) * np.mean(excess_returns) / (np.std(excess_returns) + 1e-8)
    return sharpe

def plot_backtest_results(results_list: List[Dict]):
    """Plot backtest results"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle('Strategy Backtest Performance Comparison', fontsize=16, fontweight='bold')
    
    # Plot 1: Portfolio values over time
    ax = axes[0, 0]
    for result in results_list:
        ax.plot(result['portfolio_values'], label=result['strategy'], linewidth=2)
    ax.set_title('Portfolio Value Over Time', fontweight='bold')
    ax.set_xlabel('Trading Days')
    ax.set_ylabel('Portfolio Value (₹)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 2: Total Returns Comparison
    ax = axes[0, 1]
    strategies = [r['strategy'] for r in results_list]
    returns = [r['total_return'] for r in results_list]
    colors = ['green' if x > 0 else 'red' for x in returns]
    ax.bar(strategies, returns, color=colors, alpha=0.7)
    ax.set_title('Total Returns (%)', fontweight='bold')
    ax.set_ylabel('Return (%)')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.tick_params(axis='x', rotation=45)
    
    # Plot 3: Max Drawdown Comparison
    ax = axes[1, 0]
    max_dds = [r['max_dd'] for r in results_list]
    ax.bar(strategies, max_dds, color='orange', alpha=0.7)
    ax.set_title('Maximum Drawdown (%)', fontweight='bold')
    ax.set_ylabel('Drawdown (%)')
    ax.tick_params(axis='x', rotation=45)
    
    # Plot 4: Sharpe Ratio Comparison
    ax = axes[1, 1]
    sharpes = [r['sharpe'] for r in results_list]
    colors = ['green' if x > 0 else 'red' for x in sharpes]
    ax.bar(strategies, sharpes, color=colors, alpha=0.7)
    ax.set_title('Sharpe Ratio', fontweight='bold')
    ax.set_ylabel('Sharpe Ratio')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.axhline(y=1.0, color='green', linestyle='--', linewidth=1, alpha=0.5, label='Target (1.0)')
    ax.legend()
    ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('backtest_results.png', dpi=100, bbox_inches='tight')
    print("\n  📊 Chart saved: backtest_results.png")

def main():
    print_section("MYBREEZE APP - COMPREHENSIVE STRATEGY BACKTESTING")
    
    print("\n  📈 Generating sample market data (1 year)...")
    df = generate_sample_backtest_data()
    print(f"  ✅ Generated {len(df)} trading days of data")
    print(f"  Price range: ₹{df['close'].min():.2f} - ₹{df['close'].max():.2f}")
    print(f"  Avg Volume: {df['volume'].mean():,.0f}")
    
    # Run all strategies
    print_section("RUNNING STRATEGY BACKTESTS")
    
    results = []
    
    print_subsection("1. Buy & Hold Strategy")
    result = backtest_buy_hold_strategy(df.copy())
    results.append(result)
    print_result(result)
    
    print_subsection("2. SMA Crossover Strategy (20/50)")
    result = backtest_sma_crossover(df.copy())
    results.append(result)
    print_result(result)
    
    print_subsection("3. RSI Mean Reversion Strategy (14)")
    result = backtest_rsi_strategy(df.copy())
    results.append(result)
    print_result(result)
    
    print_subsection("4. Momentum Strategy (ROC-10)")
    result = backtest_momentum_strategy(df.copy())
    results.append(result)
    print_result(result)
    
    # Performance comparison
    print_section("PERFORMANCE COMPARISON")
    print_comparison_table(results)
    
    # Plot results
    print_section("GENERATING VISUALIZATIONS")
    plot_backtest_results(results)
    
    # Summary
    print_section("BACKTEST SUMMARY & RECOMMENDATIONS")
    best_return = max(results, key=lambda x: x['total_return'])
    best_risk = max(results, key=lambda x: -x['max_dd'])
    best_sharpe = max(results, key=lambda x: x['sharpe'])
    
    print(f"\n  🏆 Best Return: {best_return['strategy']} ({best_return['total_return']:.2f}%)")
    print(f"  🛡️  Best Risk Control: {best_risk['strategy']} (Max DD: {best_risk['max_dd']:.2f}%)")
    print(f"  ⭐ Best Risk-Adjusted: {best_sharpe['strategy']} (Sharpe: {best_sharpe['sharpe']:.2f})")
    
    print("\n  💡 Recommendations:")
    print("     • Deploy best-performing strategies to paper trading first")
    print("     • Monitor live performance vs backtest results")
    print("     • Rebalance portfolio allocation based on Sharpe ratios")
    print("     • Test strategies on additional symbols for robustness")
    print("     • Implement stricter risk management in live trading")
    
    print("\n" + "=" * 90 + "\n")

def print_result(result: Dict):
    """Print formatted backtest result"""
    print(f"  Total Return: {result['total_return']:>8.2f}% | Final Capital: ₹{result['final_capital']:>12,.2f}")
    print(f"  Trades:       {result['trades']:>8} | Max Drawdown: {result['max_dd']:>8.2f}%")
    print(f"  Sharpe Ratio: {result['sharpe']:>8.2f} | Status: {'✅ POSITIVE' if result['total_return'] > 0 else '❌ NEGATIVE'}")

def print_comparison_table(results: List[Dict]):
    """Print comparison table"""
    print(f"\n  {'Strategy':<30} {'Return %':>10} {'Final Capital':>15} {'Sharpe':>8} {'Max DD %':>10}")
    print("  " + "-" * 86)
    for result in results:
        status = "✅" if result['total_return'] > 0 else "❌"
        print(f"  {result['strategy']:<28} {status} {result['total_return']:>8.2f}% ₹{result['final_capital']:>13,.0f} {result['sharpe']:>8.2f} {result['max_dd']:>9.2f}%")

if __name__ == "__main__":
    main()
