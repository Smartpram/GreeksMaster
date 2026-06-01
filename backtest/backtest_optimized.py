#!/usr/bin/env python3
"""
Optimized Strategy Backtest - Test Enhanced Parameters
"""

import sys
import os
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from strategies.optimized_buy_hold_trend import OptimizedBuyHoldTrendStrategy, OptimizedConfig

def generate_realistic_market_data(symbol: str, start_date: str, end_date: str, 
                                 initial_price: float = 1000) -> pd.DataFrame:
    """Generate realistic market data for backtesting"""
    
    np.random.seed(hash(symbol) % 2**32)  # Consistent data per symbol
    
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    dates = [d for d in dates if d.weekday() < 5]  # Only weekdays
    
    n_days = len(dates)
    
    # Market regime parameters (more realistic)
    trend_strength = np.random.choice([0.5, 1.0, 1.5], p=[0.3, 0.5, 0.2])  # Trend strength
    volatility = np.random.uniform(0.015, 0.035)  # Daily volatility 1.5-3.5%
    mean_reversion = np.random.uniform(0.95, 0.99)  # Mean reversion factor
    
    # Initialize arrays
    prices = np.zeros(n_days)
    volumes = np.zeros(n_days)
    prices[0] = initial_price
    
    # Generate price series with realistic patterns
    for i in range(1, n_days):
        # Trend component
        trend = np.random.uniform(-0.002, 0.003) * trend_strength
        
        # Mean reversion to moving average
        if i > 20:
            ma_20 = np.mean(prices[i-20:i])
            mean_revert = (ma_20 - prices[i-1]) / ma_20 * 0.1
        else:
            mean_revert = 0
        
        # Random shock
        shock = np.random.normal(0, volatility)
        
        # Market microstructure (bid-ask bounce)
        microstructure = np.random.uniform(-0.001, 0.001)
        
        # Calculate next price
        daily_return = trend + mean_revert + shock + microstructure
        prices[i] = prices[i-1] * (1 + daily_return)
        
        # Ensure prices don't go negative
        prices[i] = max(prices[i], prices[0] * 0.1)
    
    # Generate realistic volume (correlated with price changes)
    base_volume = np.random.uniform(100000, 500000)
    for i in range(n_days):
        if i == 0:
            volumes[i] = base_volume
        else:
            price_change = abs((prices[i] - prices[i-1]) / prices[i-1])
            volume_multiplier = 1 + price_change * 5  # Higher volume on big moves
            volumes[i] = base_volume * volume_multiplier * np.random.uniform(0.5, 2.0)
    
    # Create OHLC data
    highs = prices * np.random.uniform(1.001, 1.02, n_days)
    lows = prices * np.random.uniform(0.98, 0.999, n_days)
    opens = np.roll(prices, 1)
    opens[0] = prices[0]
    
    df = pd.DataFrame({
        'date': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': prices,
        'volume': volumes.astype(int)
    })
    
    return df

def backtest_optimized_strategy():
    """Comprehensive backtest of optimized strategy"""
    
    print("🚀 OPTIMIZED STRATEGY BACKTEST")
    print("=" * 50)
    
    # Initialize strategy
    config = OptimizedConfig()
    strategy = OptimizedBuyHoldTrendStrategy(config)
    
    # Test parameters
    symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR']
    sectors = {'RELIANCE': 'Energy', 'TCS': 'IT', 'HDFCBANK': 'Finance', 
              'INFY': 'IT', 'HINDUNILVR': 'FMCG'}
    
    start_date = '2023-01-01'
    end_date = '2024-10-31'
    initial_capital = 100000
    
    print(f"📊 Testing optimized parameters:")
    print(f"   Signal Strength: {config.MIN_SIGNAL_STRENGTH}")
    print(f"   Position Size: {config.MAX_POSITION_SIZE:.1%}")
    print(f"   Stop Loss: {config.STOP_LOSS_PCT:.1%}")
    print(f"   Volume Filter: {config.MIN_VOLUME_RATIO}x")
    print(f"   Max Positions: {config.MAX_OPEN_POSITIONS}")
    
    # Portfolio tracking
    portfolio = {'cash': initial_capital, 'positions': {}}
    trades = []
    daily_values = []
    
    # Generate market data for all symbols
    print(f"\n📈 Generating market data...")
    market_data = {}
    for symbol in symbols:
        base_price = np.random.uniform(800, 1500)
        market_data[symbol] = generate_realistic_market_data(symbol, start_date, end_date, base_price)
        print(f"   {symbol}: {len(market_data[symbol])} days")
    
    # Get all unique dates
    all_dates = sorted(set().union(*[df['date'].tolist() for df in market_data.values()]))
    
    print(f"\n💰 Starting backtest with ₹{initial_capital:,.0f}")
    print(f"📅 Period: {start_date} to {end_date} ({len(all_dates)} trading days)")
    
    # Main backtesting loop
    for date_idx, current_date in enumerate(all_dates):
        
        # Reset daily tracking
        if date_idx == 0 or current_date.day == 1:
            strategy.reset_daily_tracking()
        
        # Get current portfolio value
        portfolio_value = portfolio['cash']
        for symbol, pos in portfolio['positions'].items():
            if symbol in market_data and current_date in market_data[symbol]['date'].values:
                current_price = market_data[symbol][market_data[symbol]['date'] == current_date]['close'].iloc[0]
                portfolio_value += pos['quantity'] * current_price
        
        # Process each symbol
        for symbol in symbols:
            df = market_data[symbol]
            
            # Skip if no data for this date
            if current_date not in df['date'].values:
                continue
            
            # Get current row with technical indicators
            current_idx = df[df['date'] == current_date].index[0]
            
            # Need sufficient history for indicators
            if current_idx < 50:
                continue
            
            # Calculate indicators for the window
            window_df = df.iloc[:current_idx+1].copy()
            window_df = strategy.calculate_technical_indicators(window_df)
            
            current_row = window_df.iloc[-1]
            
            # Check for exits first
            if symbol in portfolio['positions']:
                position = portfolio['positions'][symbol]
                
                # Check for partial exit
                if strategy.should_partial_exit(symbol, current_row, position):
                    partial_info = strategy.execute_partial_exit(symbol, position)
                    
                    # Record partial exit
                    partial_proceeds = partial_info['quantity'] * current_row['close']
                    portfolio['cash'] += partial_proceeds
                    
                    trades.append({
                        'symbol': symbol,
                        'action': 'partial_sell',
                        'quantity': partial_info['quantity'],
                        'price': current_row['close'],
                        'date': current_date,
                        'proceeds': partial_proceeds
                    })
                
                # Check for full exit
                should_exit, exit_reason = strategy.should_exit_position(symbol, current_row, position)
                
                if should_exit:
                    # Execute full exit
                    exit_proceeds = position['quantity'] * current_row['close']
                    pnl = exit_proceeds - (position['quantity'] * position['entry_price'])
                    
                    portfolio['cash'] += exit_proceeds
                    
                    # Record trade
                    trades.append({
                        'symbol': symbol,
                        'action': 'sell',
                        'quantity': position['quantity'],
                        'price': current_row['close'],
                        'entry_price': position['entry_price'],
                        'entry_date': position['entry_date'],
                        'exit_date': current_date,
                        'pnl': pnl,
                        'pnl_pct': pnl / (position['quantity'] * position['entry_price']),
                        'exit_reason': exit_reason,
                        'days_held': (current_date - position['entry_date']).days
                    })
                    
                    # Update sector tracking
                    strategy.update_sector_positions(symbol, sectors[symbol], 'sell')
                    
                    # Remove position
                    del portfolio['positions'][symbol]
                    del strategy.positions[symbol]
                    
                    # Update daily P&L
                    strategy.daily_pnl += pnl
            
            # Check for entries
            else:
                should_enter, entry_reason = strategy.should_enter_position(
                    symbol, current_row, portfolio_value, sectors[symbol]
                )
                
                if should_enter:
                    # Calculate position size
                    signal_strength = strategy.calculate_signal_strength(current_row)
                    quantity = strategy.get_position_size(symbol, current_row['close'], 
                                                        portfolio_value, signal_strength)
                    
                    cost = quantity * current_row['close']
                    
                    # Check if we have enough cash
                    if cost <= portfolio['cash']:
                        # Execute entry
                        portfolio['cash'] -= cost
                        
                        position = {
                            'quantity': quantity,
                            'entry_price': current_row['close'],
                            'entry_date': current_date,
                            'signal_strength': signal_strength,
                            'partial_taken': False
                        }
                        
                        portfolio['positions'][symbol] = position
                        strategy.positions[symbol] = position
                        
                        # Update sector tracking
                        strategy.update_sector_positions(symbol, sectors[symbol], 'buy')
                        
                        # Record trade
                        trades.append({
                            'symbol': symbol,
                            'action': 'buy',
                            'quantity': quantity,
                            'price': current_row['close'],
                            'date': current_date,
                            'cost': cost,
                            'signal_strength': signal_strength,
                            'entry_reason': entry_reason
                        })
        
        # Record daily portfolio value
        if date_idx % 5 == 0:  # Record every 5 days to save space
            daily_values.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'cash': portfolio['cash'],
                'total_value': portfolio_value,
                'positions': len(portfolio['positions'])
            })
    
    # Final portfolio valuation
    final_portfolio_value = portfolio['cash']
    for symbol, pos in portfolio['positions'].items():
        if symbol in market_data:
            final_price = market_data[symbol]['close'].iloc[-1]
            final_portfolio_value += pos['quantity'] * final_price
    
    print(f"\n✅ Backtest completed!")
    print(f"📊 Total trades executed: {len([t for t in trades if t['action'] in ['buy', 'sell']])}")
    
    # Calculate performance metrics
    total_return = (final_portfolio_value - initial_capital) / initial_capital
    completed_trades = [t for t in trades if t['action'] == 'sell']
    
    if completed_trades:
        winning_trades = [t for t in completed_trades if t['pnl'] > 0]
        losing_trades = [t for t in completed_trades if t['pnl'] <= 0]
        
        win_rate = len(winning_trades) / len(completed_trades)
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        total_wins = sum([t['pnl'] for t in winning_trades])
        total_losses = abs(sum([t['pnl'] for t in losing_trades]))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Calculate drawdown
        portfolio_values = [initial_capital] + [dv['total_value'] for dv in daily_values]
        running_max = np.maximum.accumulate(portfolio_values)
        drawdowns = (np.array(portfolio_values) - running_max) / running_max
        max_drawdown = np.min(drawdowns)
        
        # Calculate Sharpe ratio
        returns = np.diff(portfolio_values) / portfolio_values[:-1]
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # Performance summary
        print(f"\n📈 OPTIMIZED STRATEGY PERFORMANCE")
        print(f"=" * 40)
        print(f"Initial Capital:     ₹{initial_capital:,.0f}")
        print(f"Final Capital:       ₹{final_portfolio_value:,.0f}")
        print(f"Total Return:        {total_return:.2%}")
        print(f"Total P&L:           ₹{final_portfolio_value - initial_capital:,.0f}")
        
        print(f"\nTrading Stats:")
        print(f"Total Trades:        {len(completed_trades)}")
        print(f"Win Rate:            {win_rate:.1%}")
        print(f"Profit Factor:       {profit_factor:.2f}")
        print(f"Average Win:         ₹{avg_win:,.0f}")
        print(f"Average Loss:        ₹{avg_loss:,.0f}")
        
        print(f"\nRisk Metrics:")
        print(f"Max Drawdown:        {max_drawdown:.2%}")
        print(f"Sharpe Ratio:        {sharpe_ratio:.2f}")
        print(f"Volatility:          {np.std(returns) * np.sqrt(252):.2%}")
        
        # Compare with original results
        print(f"\n📊 IMPROVEMENT vs ORIGINAL STRATEGY")
        print(f"=" * 40)
        
        original_return = -0.0731
        original_win_rate = 0.324
        original_profit_factor = 0.79
        original_drawdown = -0.0997
        
        return_improvement = total_return - original_return
        win_rate_improvement = win_rate - original_win_rate
        pf_improvement = profit_factor - original_profit_factor
        dd_improvement = max_drawdown - original_drawdown
        
        print(f"Return Improvement:  {return_improvement:+.2%}")
        print(f"Win Rate Improvement: {win_rate_improvement:+.1%}")
        print(f"Profit Factor Improv: {pf_improvement:+.2f}")
        print(f"Drawdown Improvement: {dd_improvement:+.2%}")
        
        # Success assessment
        improvements = 0
        if return_improvement > 0:
            improvements += 1
            print(f"✅ Better returns")
        if win_rate_improvement > 0:
            improvements += 1
            print(f"✅ Higher win rate")
        if pf_improvement > 0:
            improvements += 1
            print(f"✅ Better profit factor")
        if dd_improvement > 0:
            improvements += 1
            print(f"✅ Lower drawdown")
        
        print(f"\n🎯 OPTIMIZATION SUCCESS: {improvements}/4 metrics improved")
        
        if total_return > 0 and profit_factor > 1.0:
            print(f"🎉 STRATEGY IS NOW PROFITABLE!")
        elif return_improvement > 0.05:
            print(f"🚀 SIGNIFICANT IMPROVEMENT ACHIEVED!")
        elif improvements >= 2:
            print(f"👍 GOOD IMPROVEMENT, FURTHER TUNING RECOMMENDED")
        else:
            print(f"⚠️  MIXED RESULTS, CONSIDER ALTERNATIVE APPROACHES")
    
    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'strategy': 'Optimized Enhanced Buy & Hold',
        'config': {
            'min_signal_strength': config.MIN_SIGNAL_STRENGTH,
            'max_position_size': config.MAX_POSITION_SIZE,
            'stop_loss': config.STOP_LOSS_PCT,
            'target': config.TARGET_PCT,
            'volume_filter': config.MIN_VOLUME_RATIO,
            'max_positions': config.MAX_OPEN_POSITIONS
        },
        'performance': {
            'initial_capital': initial_capital,
            'final_capital': final_portfolio_value,
            'total_return': total_return,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': len(completed_trades)
        },
        'improvements': {
            'return_improvement': return_improvement,
            'win_rate_improvement': win_rate_improvement,
            'profit_factor_improvement': pf_improvement,
            'drawdown_improvement': dd_improvement
        },
        'trades': completed_trades[-10:],  # Last 10 trades as sample
        'daily_portfolio': daily_values[-20:]  # Last 20 data points
    }
    
    # Save results
    os.makedirs('reports', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f'reports/optimized_backtest_{timestamp}.json'
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    try:
        results = backtest_optimized_strategy()
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()