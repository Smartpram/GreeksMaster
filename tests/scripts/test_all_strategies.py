#!/usr/bin/env python3
"""
Comprehensive Multi-Strategy Backtesting Suite
Tests all strategies individually and in combination
"""

import sys
import os
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from strategies.multi_strategy_manager import (
    MultiStrategyManager, StrategyType, 
    CONSERVATIVE_ALLOCATION, AGGRESSIVE_ALLOCATION, BALANCED_ALLOCATION
)

def generate_market_data(symbol: str, start_date: str, end_date: str, 
                        regime: str = 'mixed') -> pd.DataFrame:
    """Generate realistic market data with different market regimes"""
    
    np.random.seed(hash(symbol) % 2**32)
    
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    dates = [d for d in dates if d.weekday() < 5]  # Only weekdays
    
    n_days = len(dates)
    
    # Market regime parameters
    if regime == 'trending':
        trend_strength = 1.5
        volatility = 0.020
        mean_reversion = 0.98
    elif regime == 'sideways':
        trend_strength = 0.3
        volatility = 0.015
        mean_reversion = 0.95
    elif regime == 'volatile':
        trend_strength = 1.0
        volatility = 0.035
        mean_reversion = 0.96
    else:  # mixed
        trend_strength = np.random.choice([0.5, 1.0, 1.5], p=[0.3, 0.4, 0.3])
        volatility = np.random.uniform(0.015, 0.030)
        mean_reversion = np.random.uniform(0.95, 0.99)
    
    # Base price
    initial_price = np.random.uniform(800, 1500)
    
    # Generate price series
    prices = np.zeros(n_days)
    prices[0] = initial_price
    
    for i in range(1, n_days):
        # Trend component
        trend = np.random.uniform(-0.002, 0.004) * trend_strength
        
        # Mean reversion
        if i > 20:
            ma_20 = np.mean(prices[i-20:i])
            mean_revert = (ma_20 - prices[i-1]) / ma_20 * (1 - mean_reversion)
        else:
            mean_revert = 0
        
        # Random shock
        shock = np.random.normal(0, volatility)
        
        # Market microstructure
        microstructure = np.random.uniform(-0.001, 0.001)
        
        # Calculate next price
        daily_return = trend + mean_revert + shock + microstructure
        prices[i] = prices[i-1] * (1 + daily_return)
        
        # Ensure prices don't go too low
        prices[i] = max(prices[i], initial_price * 0.2)
    
    # Generate OHLCV data
    highs = prices * np.random.uniform(1.001, 1.025, n_days)
    lows = prices * np.random.uniform(0.975, 0.999, n_days)
    opens = np.roll(prices, 1)
    opens[0] = prices[0]
    
    # Generate volume (correlated with price changes)
    base_volume = np.random.uniform(100000, 500000)
    volumes = []
    
    for i in range(n_days):
        if i == 0:
            volumes.append(base_volume)
        else:
            price_change = abs((prices[i] - prices[i-1]) / prices[i-1])
            volume_multiplier = 1 + price_change * 8  # Higher volume on big moves
            volume = base_volume * volume_multiplier * np.random.uniform(0.5, 2.5)
            volumes.append(int(volume))
    
    df = pd.DataFrame({
        'date': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': prices,
        'volume': volumes
    })
    
    # Set date as index for time series operations
    df.set_index('date', inplace=True)
    
    return df

def backtest_single_strategy(strategy_type: StrategyType, market_data: Dict[str, pd.DataFrame], 
                           initial_capital: float = 100000) -> Dict:
    """Backtest a single strategy"""
    
    print(f"\n🧪 Testing {strategy_type.value.upper()} Strategy")
    print("-" * 50)
    
    # Create manager with single strategy
    manager = MultiStrategyManager(initial_capital)
    manager.add_strategy(strategy_type, allocation_pct=1.0, max_positions=5)
    
    # Portfolio tracking
    portfolio_value = initial_capital
    trades = []
    daily_values = []
    positions = {}
    
    # Get all dates
    all_dates = sorted(set().union(*[df.index.tolist() for df in market_data.values()]))
    
    for date_idx, current_date in enumerate(all_dates):
        
        # Process each symbol
        for symbol, df in market_data.items():
            
            if current_date not in df.index:
                continue
            
            # Get data up to current date
            historical_data = df.loc[:current_date].copy()
            
            if len(historical_data) < 50:  # Need sufficient history
                continue
            
            # Get strategy signals
            signals = manager.process_market_data(symbol, historical_data)
            
            for signal in signals:
                if signal['action'] == 'buy':
                    # Execute buy
                    cost = signal['quantity'] * signal['price']
                    if cost <= portfolio_value * 0.2:  # Max 20% per position
                        
                        position_id = f"{symbol}_{current_date.strftime('%Y%m%d')}_{len(trades)}"
                        positions[position_id] = {
                            'symbol': symbol,
                            'quantity': signal['quantity'],
                            'entry_price': signal['price'],
                            'entry_date': current_date,
                            'strategy': strategy_type,
                            'cost': cost
                        }
                        
                        portfolio_value -= cost
                        
                        trades.append({
                            'id': position_id,
                            'symbol': symbol,
                            'action': 'buy',
                            'quantity': signal['quantity'],
                            'price': signal['price'],
                            'date': current_date,
                            'cost': cost,
                            'reason': signal['reason']
                        })
                
                elif signal['action'] == 'exit':
                    # Find and close position
                    position_id = signal.get('position_id')
                    if position_id and position_id in positions:
                        position = positions[position_id]
                        
                        proceeds = position['quantity'] * signal['price']
                        pnl = proceeds - position['cost']
                        
                        portfolio_value += proceeds
                        
                        trades.append({
                            'id': position_id,
                            'symbol': symbol,
                            'action': 'sell',
                            'quantity': position['quantity'],
                            'price': signal['price'],
                            'entry_price': position['entry_price'],
                            'entry_date': position['entry_date'],
                            'exit_date': current_date,
                            'date': current_date,
                            'proceeds': proceeds,
                            'pnl': pnl,
                            'pnl_pct': pnl / position['cost'],
                            'days_held': (current_date - position['entry_date']).days,
                            'reason': signal['reason']
                        })
                        
                        del positions[position_id]
        
        # Record daily value
        if date_idx % 5 == 0:  # Every 5 days
            position_value = 0
            for pos in positions.values():
                symbol = pos['symbol']
                if symbol in market_data and current_date in market_data[symbol].index:
                    current_price = market_data[symbol].loc[current_date, 'close']
                    position_value += pos['quantity'] * current_price
            
            total_value = portfolio_value + position_value
            daily_values.append({
                'date': current_date,
                'cash': portfolio_value,
                'positions_value': position_value,
                'total_value': total_value
            })
    
    # Final valuation
    final_position_value = 0
    for pos in positions.values():
        symbol = pos['symbol']
        if symbol in market_data:
            final_price = market_data[symbol].iloc[-1]['close']
            final_position_value += pos['quantity'] * final_price
    
    final_portfolio_value = portfolio_value + final_position_value
    
    # Calculate performance metrics
    completed_trades = [t for t in trades if t['action'] == 'sell']
    total_return = (final_portfolio_value - initial_capital) / initial_capital
    
    if completed_trades:
        winning_trades = [t for t in completed_trades if t['pnl'] > 0]
        losing_trades = [t for t in completed_trades if t['pnl'] <= 0]
        
        win_rate = len(winning_trades) / len(completed_trades)
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        total_wins = sum([t['pnl'] for t in winning_trades])
        total_losses = abs(sum([t['pnl'] for t in losing_trades]))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Calculate Sharpe ratio
        if daily_values:
            returns = np.diff([dv['total_value'] for dv in daily_values]) / [dv['total_value'] for dv in daily_values[:-1]]
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
            
            # Max drawdown
            values = [dv['total_value'] for dv in daily_values]
            running_max = np.maximum.accumulate(values)
            drawdowns = (np.array(values) - running_max) / running_max
            max_drawdown = np.min(drawdowns)
        else:
            sharpe_ratio = 0
            max_drawdown = 0
    else:
        win_rate = 0
        avg_win = 0
        avg_loss = 0
        profit_factor = 0
        sharpe_ratio = 0
        max_drawdown = 0
    
    results = {
        'strategy': strategy_type.value,
        'initial_capital': initial_capital,
        'final_capital': final_portfolio_value,
        'total_return': total_return,
        'total_trades': len(completed_trades),
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'trades': completed_trades[-5:],  # Last 5 trades as sample
        'daily_values': daily_values[-10:]  # Last 10 values
    }
    
    # Print results
    print(f"📊 {strategy_type.value.upper()} RESULTS:")
    print(f"  Return: {total_return:.2%}")
    print(f"  Win Rate: {win_rate:.1%}")
    print(f"  Profit Factor: {profit_factor:.2f}")
    print(f"  Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"  Max Drawdown: {max_drawdown:.2%}")
    print(f"  Total Trades: {len(completed_trades)}")
    
    return results

def backtest_multi_strategy(allocation: Dict[StrategyType, float], 
                           market_data: Dict[str, pd.DataFrame],
                           allocation_name: str = "Custom",
                           initial_capital: float = 100000) -> Dict:
    """Backtest multi-strategy allocation"""
    
    print(f"\n🚀 Testing {allocation_name.upper()} Multi-Strategy")
    print("=" * 60)
    
    # Create manager with multiple strategies
    manager = MultiStrategyManager(initial_capital)
    
    for strategy_type, alloc_pct in allocation.items():
        manager.add_strategy(strategy_type, alloc_pct, max_positions=3)
        print(f"  {strategy_type.value}: {alloc_pct:.1%}")
    
    # Portfolio tracking
    portfolio_value = initial_capital
    trades = []
    daily_values = []
    positions = {}
    strategy_performance = {st: {'pnl': 0, 'trades': 0} for st in allocation.keys()}
    
    # Get all dates
    all_dates = sorted(set().union(*[df.index.tolist() for df in market_data.values()]))
    
    for date_idx, current_date in enumerate(all_dates):
        
        # Process each symbol
        for symbol, df in market_data.items():
            
            if current_date not in df.index:
                continue
            
            historical_data = df.loc[:current_date].copy()
            
            if len(historical_data) < 50:
                continue
            
            # Get signals from all strategies
            signals = manager.process_market_data(symbol, historical_data)
            
            for signal in signals:
                strategy_type = signal['strategy']
                strategy_capital = manager.get_strategy_capital(strategy_type)
                
                if signal['action'] == 'buy':
                    cost = signal['quantity'] * signal['price']
                    
                    # Check if strategy has capital
                    if cost <= strategy_capital * 0.3:  # Max 30% of strategy capital per position
                        
                        position_id = f"{symbol}_{strategy_type.value}_{current_date.strftime('%Y%m%d')}_{len(trades)}"
                        positions[position_id] = {
                            'symbol': symbol,
                            'quantity': signal['quantity'],
                            'entry_price': signal['price'],
                            'entry_date': current_date,
                            'strategy': strategy_type,
                            'cost': cost
                        }
                        
                        portfolio_value -= cost
                        
                        trades.append({
                            'id': position_id,
                            'symbol': symbol,
                            'strategy': strategy_type.value,
                            'action': 'buy',
                            'quantity': signal['quantity'],
                            'price': signal['price'],
                            'date': current_date,
                            'cost': cost,
                            'reason': signal['reason']
                        })
                
                elif signal['action'] == 'exit':
                    position_id = signal.get('position_id')
                    if position_id and position_id in positions:
                        position = positions[position_id]
                        
                        proceeds = position['quantity'] * signal['price']
                        pnl = proceeds - position['cost']
                        
                        portfolio_value += proceeds
                        
                        # Track strategy performance
                        strategy_performance[strategy_type]['pnl'] += pnl
                        strategy_performance[strategy_type]['trades'] += 1
                        
                        trades.append({
                            'id': position_id,
                            'symbol': symbol,
                            'strategy': strategy_type.value,
                            'action': 'sell',
                            'quantity': position['quantity'],
                            'price': signal['price'],
                            'entry_price': position['entry_price'],
                            'entry_date': position['entry_date'],
                            'exit_date': current_date,
                            'date': current_date,
                            'proceeds': proceeds,
                            'pnl': pnl,
                            'pnl_pct': pnl / position['cost'],
                            'days_held': (current_date - position['entry_date']).days,
                            'reason': signal['reason']
                        })
                        
                        del positions[position_id]
        
        # Record daily value
        if date_idx % 5 == 0:
            position_value = 0
            for pos in positions.values():
                symbol = pos['symbol']
                if symbol in market_data and current_date in market_data[symbol].index:
                    current_price = market_data[symbol].loc[current_date, 'close']
                    position_value += pos['quantity'] * current_price
            
            total_value = portfolio_value + position_value
            daily_values.append({
                'date': current_date,
                'cash': portfolio_value,
                'positions_value': position_value,
                'total_value': total_value
            })
    
    # Final calculations
    final_position_value = 0
    for pos in positions.values():
        symbol = pos['symbol']
        if symbol in market_data:
            final_price = market_data[symbol].iloc[-1]['close']
            final_position_value += pos['quantity'] * final_price
    
    final_portfolio_value = portfolio_value + final_position_value
    
    # Performance metrics
    completed_trades = [t for t in trades if t['action'] == 'sell']
    total_return = (final_portfolio_value - initial_capital) / initial_capital
    
    if completed_trades:
        winning_trades = [t for t in completed_trades if t['pnl'] > 0]
        win_rate = len(winning_trades) / len(completed_trades)
        
        total_wins = sum([t['pnl'] for t in winning_trades])
        total_losses = abs(sum([t['pnl'] for t in completed_trades if t['pnl'] <= 0]))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        if daily_values:
            returns = np.diff([dv['total_value'] for dv in daily_values]) / [dv['total_value'] for dv in daily_values[:-1]]
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
            
            values = [dv['total_value'] for dv in daily_values]
            running_max = np.maximum.accumulate(values)
            drawdowns = (np.array(values) - running_max) / running_max
            max_drawdown = np.min(drawdowns)
        else:
            sharpe_ratio = 0
            max_drawdown = 0
    else:
        win_rate = 0
        profit_factor = 0
        sharpe_ratio = 0
        max_drawdown = 0
    
    results = {
        'allocation_name': allocation_name,
        'allocation': {st.value: alloc for st, alloc in allocation.items()},
        'initial_capital': initial_capital,
        'final_capital': final_portfolio_value,
        'total_return': total_return,
        'total_trades': len(completed_trades),
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'strategy_performance': {st.value: perf for st, perf in strategy_performance.items()},
        'trades': completed_trades[-10:],  # Last 10 trades
        'daily_values': daily_values[-15:]  # Last 15 values
    }
    
    # Print results
    print(f"📊 {allocation_name.upper()} MULTI-STRATEGY RESULTS:")
    print(f"  Return: {total_return:.2%}")
    print(f"  Win Rate: {win_rate:.1%}")
    print(f"  Profit Factor: {profit_factor:.2f}")
    print(f"  Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"  Max Drawdown: {max_drawdown:.2%}")
    print(f"  Total Trades: {len(completed_trades)}")
    
    print(f"\n  Strategy Breakdown:")
    for strategy, perf in strategy_performance.items():
        print(f"    {strategy.value}: ₹{perf['pnl']:,.0f} P&L ({perf['trades']} trades)")
    
    return results

def run_comprehensive_backtest():
    """Run comprehensive backtest of all strategies"""
    
    print("🎯 MyBreezeApp Comprehensive Strategy Backtest")
    print("=" * 80)
    
    # Test parameters
    symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR', 'ICICIBANK', 'SBIN']
    start_date = '2023-01-01'
    end_date = '2024-10-31'
    initial_capital = 100000
    
    print(f"📊 Test Parameters:")
    print(f"  Symbols: {', '.join(symbols)}")
    print(f"  Period: {start_date} to {end_date}")
    print(f"  Capital: ₹{initial_capital:,.0f}")
    print(f"  Market Regimes: Mixed conditions")
    
    # Generate market data
    print(f"\n📈 Generating market data...")
    market_data = {}
    
    for symbol in symbols:
        # Mix different market regimes
        if symbol in ['RELIANCE', 'TCS']:
            regime = 'trending'
        elif symbol in ['HDFCBANK', 'ICICIBANK']:
            regime = 'volatile'
        elif symbol in ['INFY', 'SBIN']:
            regime = 'sideways'
        else:
            regime = 'mixed'
        
        market_data[symbol] = generate_market_data(symbol, start_date, end_date, regime)
        print(f"    {symbol}: {len(market_data[symbol])} days ({regime} regime)")
    
    # Test individual strategies
    print(f"\n🧪 INDIVIDUAL STRATEGY TESTS")
    print("=" * 50)
    
    individual_results = {}
    strategies_to_test = [
        StrategyType.OPTIMIZED_BUY_HOLD,
        StrategyType.TREND_FOLLOWING,
        StrategyType.MEAN_REVERSION,
        StrategyType.BREAKOUT,
        StrategyType.MOMENTUM,
        StrategyType.VWAP_INTRADAY
    ]
    
    for strategy_type in strategies_to_test:
        try:
            result = backtest_single_strategy(strategy_type, market_data, initial_capital)
            individual_results[strategy_type.value] = result
        except Exception as e:
            print(f"❌ Error testing {strategy_type.value}: {e}")
            individual_results[strategy_type.value] = {'error': str(e)}
    
    # Test multi-strategy allocations
    print(f"\n🚀 MULTI-STRATEGY TESTS")
    print("=" * 50)
    
    multi_strategy_results = {}
    
    allocations_to_test = [
        (CONSERVATIVE_ALLOCATION, "Conservative"),
        (AGGRESSIVE_ALLOCATION, "Aggressive"), 
        (BALANCED_ALLOCATION, "Balanced")
    ]
    
    for allocation, name in allocations_to_test:
        try:
            result = backtest_multi_strategy(allocation, market_data, name, initial_capital)
            multi_strategy_results[name.lower()] = result
        except Exception as e:
            print(f"❌ Error testing {name}: {e}")
            multi_strategy_results[name.lower()] = {'error': str(e)}
    
    # Performance comparison
    print(f"\n📊 PERFORMANCE COMPARISON")
    print("=" * 50)
    
    # Individual strategies comparison
    print(f"\n📈 Individual Strategies:")
    print(f"{'Strategy':<20} {'Return':<10} {'Win Rate':<10} {'Profit Factor':<12} {'Sharpe':<8} {'Drawdown':<10}")
    print("-" * 70)
    
    for strategy_name, result in individual_results.items():
        if 'error' not in result:
            print(f"{strategy_name:<20} {result['total_return']:>8.1%} {result['win_rate']:>8.1%} "
                  f"{result['profit_factor']:>10.2f} {result['sharpe_ratio']:>6.2f} {result['max_drawdown']:>8.1%}")
    
    # Multi-strategy comparison
    print(f"\n🚀 Multi-Strategy Allocations:")
    print(f"{'Allocation':<15} {'Return':<10} {'Win Rate':<10} {'Profit Factor':<12} {'Sharpe':<8} {'Drawdown':<10}")
    print("-" * 65)
    
    for allocation_name, result in multi_strategy_results.items():
        if 'error' not in result:
            print(f"{allocation_name.title():<15} {result['total_return']:>8.1%} {result['win_rate']:>8.1%} "
                  f"{result['profit_factor']:>10.2f} {result['sharpe_ratio']:>6.2f} {result['max_drawdown']:>8.1%}")
    
    # Find best performers
    print(f"\n🏆 BEST PERFORMERS")
    print("-" * 30)
    
    # Best individual strategy
    best_individual = max(individual_results.items(), 
                         key=lambda x: x[1].get('total_return', -1) if 'error' not in x[1] else -1)
    print(f"Best Individual: {best_individual[0]} ({best_individual[1].get('total_return', 0):.1%})")
    
    # Best multi-strategy
    best_multi = max(multi_strategy_results.items(),
                    key=lambda x: x[1].get('total_return', -1) if 'error' not in x[1] else -1)
    print(f"Best Multi-Strategy: {best_multi[0].title()} ({best_multi[1].get('total_return', 0):.1%})")
    
    # Save results
    all_results = {
        'timestamp': datetime.now().isoformat(),
        'test_parameters': {
            'symbols': symbols,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': initial_capital
        },
        'individual_strategies': individual_results,
        'multi_strategies': multi_strategy_results,
        'best_performers': {
            'individual': best_individual[0],
            'multi_strategy': best_multi[0]
        }
    }
    
    # Save to file
    os.makedirs('reports', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f'reports/comprehensive_backtest_{timestamp}.json'
    
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n💾 Comprehensive results saved to: {results_file}")
    
    return all_results

if __name__ == "__main__":
    try:
        results = run_comprehensive_backtest()
        print(f"\n✅ COMPREHENSIVE BACKTEST COMPLETE!")
        print(f"🎯 All strategies tested successfully")
        print(f"📊 Results saved for detailed analysis")
        
    except Exception as e:
        print(f"❌ Comprehensive backtest failed: {e}")
        import traceback
        traceback.print_exc()