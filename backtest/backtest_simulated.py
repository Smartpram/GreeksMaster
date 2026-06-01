#!/usr/bin/env python3
"""
MyBreezeApp Enhanced Strategy Backtesting with Simulated Data
Tests the Buy & Hold trend-following strategy with MACD, RSI, and Stochastic RSI using synthetic market data
"""
import sys
import os
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta, date
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from utils.indicators import TechnicalIndicators
from config import Config

class SimulatedMarketDataGenerator:
    """Generate realistic market data for backtesting"""
    
    def __init__(self, start_date, end_date, symbols):
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.symbols = symbols
        
    def generate_realistic_data(self, symbol, initial_price=1000):
        """Generate realistic OHLCV data with trends and volatility"""
        dates = pd.date_range(self.start_date, self.end_date, freq='D')
        dates = [d for d in dates if d.weekday() < 5]  # Remove weekends
        
        n_days = len(dates)
        
        # Create realistic price movement
        np.random.seed(hash(symbol) % 2**32)  # Consistent data for each symbol
        
        # Generate base returns with trend
        trend = np.random.uniform(-0.0002, 0.0008)  # Annual trend component
        daily_trend = trend / 252
        
        # Volatility components
        base_volatility = np.random.uniform(0.015, 0.035)  # Daily volatility
        volatility_clustering = np.random.beta(2, 5, n_days) * 0.02
        
        # Generate returns
        random_returns = np.random.normal(daily_trend, base_volatility, n_days)
        volatility_adjusted_returns = random_returns * (1 + volatility_clustering)
        
        # Add some momentum and mean reversion
        for i in range(1, len(volatility_adjusted_returns)):
            momentum = volatility_adjusted_returns[i-1] * 0.1  # Momentum factor
            mean_reversion = -volatility_adjusted_returns[i-1] * 0.05  # Mean reversion
            volatility_adjusted_returns[i] += momentum + mean_reversion
        
        # Calculate cumulative prices
        price_multipliers = np.cumprod(1 + volatility_adjusted_returns)
        close_prices = initial_price * price_multipliers
        
        # Generate OHLC from close prices
        data = []
        for i, (date, close) in enumerate(zip(dates, close_prices)):
            # Create realistic OHLC
            prev_close = close_prices[i-1] if i > 0 else close
            
            # High and low based on volatility
            daily_range = abs(volatility_adjusted_returns[i]) * close * np.random.uniform(2, 4)
            high = close + np.random.uniform(0, daily_range * 0.7)
            low = close - np.random.uniform(0, daily_range * 0.7)
            
            # Ensure logical OHLC relationships
            high = max(high, close, prev_close)
            low = min(low, close, prev_close)
            
            # Open price (gap from previous close)
            gap = np.random.normal(0, abs(volatility_adjusted_returns[i]) * 0.3)
            open_price = prev_close * (1 + gap)
            open_price = max(min(open_price, high), low)
            
            # Volume (inverse correlation with price typically)
            base_volume = np.random.uniform(100000, 500000)
            volume_multiplier = 1 + abs(volatility_adjusted_returns[i]) * 5  # Higher volume on big moves
            volume = int(base_volume * volume_multiplier)
            
            data.append({
                'date': date,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close, 2),
                'volume': volume
            })
        
        return pd.DataFrame(data)

class EnhancedStrategyBacktester:
    """Comprehensive backtesting for enhanced Buy & Hold strategy"""
    
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.config = Config()
        self.indicators = TechnicalIndicators()
        
        # Strategy parameters
        self.trend_period = 20
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        
        # Risk management
        self.max_position_size = 0.1  # 10% of capital
        self.stop_loss_pct = 0.05     # 5%
        self.target_pct = 0.15        # 15%
        self.max_daily_loss = 0.02    # 2%
        
        # Results tracking
        self.trades = []
        self.portfolio_values = []
        self.positions = {}
        self.current_capital = initial_capital
        
    def calculate_enhanced_indicators(self, df):
        """Calculate all enhanced technical indicators"""
        try:
            # Basic indicators
            df['ma'] = self.indicators.moving_average(df['close'], self.trend_period)
            df['rsi'] = self.indicators.rsi(df['close'], self.rsi_period)
            df['volume_ma'] = self.indicators.moving_average(df['volume'], 20)
            
            # MACD
            macd_data = self.indicators.macd(df['close'])
            df['macd'] = macd_data['macd']
            df['macd_signal'] = macd_data['signal']
            df['macd_histogram'] = macd_data['histogram']
            
            # Stochastic RSI
            stoch_rsi_data = self.indicators.stochastic_rsi(df['close'])
            df['stoch_rsi'] = stoch_rsi_data['stoch_rsi']
            df['stoch_rsi_k'] = stoch_rsi_data['k_percent']
            df['stoch_rsi_d'] = stoch_rsi_data['d_percent']
            
            return df
            
        except Exception as e:
            print(f"❌ Error calculating indicators: {e}")
            return df
    
    def check_enhanced_entry_conditions(self, row):
        """Check enhanced entry conditions with multi-indicator analysis"""
        try:
            conditions_met = []
            
            # Skip if insufficient data
            if pd.isna(row['ma']) or pd.isna(row['rsi']) or pd.isna(row['macd']):
                return None
            
            # Primary Condition 1: Price above moving average (trend confirmation)
            if row['close'] > row['ma']:
                conditions_met.append('trend_bullish')
            
            # Primary Condition 2: RSI in healthy range (not overbought but not oversold)
            if 30 < row['rsi'] < self.rsi_overbought:
                conditions_met.append('rsi_healthy')
            
            # Enhanced Condition 3: MACD trend confirmation
            if (not pd.isna(row['macd_histogram']) and 
                row['macd'] > row['macd_signal'] and row['macd_histogram'] > 0):
                conditions_met.append('macd_bullish')
            
            # Enhanced Condition 4: Stochastic RSI momentum confirmation
            if (not pd.isna(row['stoch_rsi_k']) and not pd.isna(row['stoch_rsi_d']) and
                row['stoch_rsi_k'] > 20 and row['stoch_rsi_d'] > 20 and 
                row['stoch_rsi_k'] > row['stoch_rsi_d']):
                conditions_met.append('stoch_rsi_bullish')
            
            # Supporting Condition 5: Volume confirmation
            if (not pd.isna(row['volume_ma']) and 
                row['volume'] > row['volume_ma'] * 1.2):
                conditions_met.append('volume_confirmation')
            
            # Calculate signal strength
            primary_conditions = ['trend_bullish', 'rsi_healthy']
            enhanced_conditions = ['macd_bullish', 'stoch_rsi_bullish']
            supporting_conditions = ['volume_confirmation']
            
            # Must have all primary conditions
            if not all(cond in conditions_met for cond in primary_conditions):
                return None
            
            # Must have at least 1 enhanced condition
            enhanced_met = sum(1 for cond in enhanced_conditions if cond in conditions_met)
            if enhanced_met == 0:
                return None
            
            # Calculate strength
            supporting_met = sum(1 for cond in supporting_conditions if cond in conditions_met)
            base_strength = 0.6 + (enhanced_met / len(enhanced_conditions)) * 0.2
            support_bonus = (supporting_met / len(supporting_conditions)) * 0.2
            strength = min(1.0, base_strength + support_bonus)
            
            return {
                'strength': strength,
                'conditions_met': conditions_met,
                'primary_met': len([c for c in primary_conditions if c in conditions_met]),
                'enhanced_met': enhanced_met,
                'supporting_met': supporting_met
            }
            
        except Exception as e:
            print(f"❌ Error checking entry conditions: {e}")
            return None
    
    def check_enhanced_exit_conditions(self, row, entry_price, days_held):
        """Check enhanced exit conditions"""
        try:
            current_price = row['close']
            current_pnl = (current_price - entry_price) / entry_price
            
            # Exit condition 1: Stop loss hit
            if current_price <= entry_price * (1 - self.stop_loss_pct):
                return {
                    'strength': 1.0,
                    'reason': 'stop_loss',
                    'pnl': current_pnl
                }
            
            # Exit condition 2: Target achieved
            if current_price >= entry_price * (1 + self.target_pct):
                return {
                    'strength': 1.0,
                    'reason': 'target_achieved',
                    'pnl': current_pnl
                }
            
            # Enhanced exit conditions
            technical_exit_signals = 0
            exit_reasons = []
            
            # MACD bearish divergence
            if (not pd.isna(row['macd']) and not pd.isna(row['macd_signal']) and
                not pd.isna(row['macd_histogram']) and
                row['macd'] < row['macd_signal'] and row['macd_histogram'] < 0):
                technical_exit_signals += 1
                exit_reasons.append('macd_bearish')
            
            # Stochastic RSI overbought and turning down
            if (not pd.isna(row['stoch_rsi_k']) and not pd.isna(row['stoch_rsi_d']) and
                row['stoch_rsi_k'] > 80 and row['stoch_rsi_d'] > 80 and 
                row['stoch_rsi_k'] < row['stoch_rsi_d']):
                technical_exit_signals += 1
                exit_reasons.append('stoch_rsi_overbought')
            
            # RSI overbought
            if row['rsi'] > self.rsi_overbought:
                technical_exit_signals += 1
                exit_reasons.append('rsi_overbought')
            
            # If multiple technical indicators suggest exit and we have profit
            if technical_exit_signals >= 2 and current_pnl > 0.05:  # 5% profit threshold
                return {
                    'strength': 0.7 + (technical_exit_signals * 0.1),
                    'reason': f"technical_exit_{'+'.join(exit_reasons)}",
                    'pnl': current_pnl
                }
            
            # Trend reversal (price below MA)
            if (not pd.isna(row['ma']) and current_price < row['ma'] and 
                current_pnl > 0.03):  # 3% profit protection
                return {
                    'strength': 0.6,
                    'reason': 'trend_reversal',
                    'pnl': current_pnl
                }
            
            # Time-based exit
            if days_held > 60:
                return {
                    'strength': 0.4,
                    'reason': 'time_based_exit',
                    'pnl': current_pnl
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Error checking exit conditions: {e}")
            return None
    
    def run_backtest(self, data, symbols):
        """Run comprehensive backtest"""
        print(f"🔄 Running enhanced strategy backtest...")
        print(f"Initial Capital: ₹{self.initial_capital:,.2f}")
        print(f"Symbols: {', '.join(symbols)}")
        print("-" * 60)
        
        # Get all unique dates
        all_dates = set()
        for symbol_data in data.values():
            all_dates.update(symbol_data['date'].dt.date)
        
        all_dates = sorted(list(all_dates))
        
        # Track daily portfolio value
        daily_portfolio = []
        
        for date in all_dates:
            daily_value = self.current_capital
            date_positions = {}
            
            # Process each symbol
            for symbol in symbols:
                if symbol not in data:
                    continue
                
                symbol_data = data[symbol]
                day_data = symbol_data[symbol_data['date'].dt.date == date]
                
                if day_data.empty:
                    continue
                
                row = day_data.iloc[-1]
                
                # Check existing positions for exits
                if symbol in self.positions:
                    position = self.positions[symbol]
                    days_held = (date - position['entry_date']).days
                    
                    exit_signal = self.check_enhanced_exit_conditions(
                        row, position['entry_price'], days_held
                    )
                    
                    if exit_signal:
                        # Execute exit
                        exit_price = row['close']
                        shares = position['shares']
                        exit_value = shares * exit_price
                        
                        pnl = exit_value - position['position_value']
                        pnl_pct = (exit_price - position['entry_price']) / position['entry_price']
                        
                        # Record trade
                        trade = {
                            'symbol': symbol,
                            'entry_date': position['entry_date'],
                            'exit_date': date,
                            'entry_price': position['entry_price'],
                            'exit_price': exit_price,
                            'shares': shares,
                            'position_value': position['position_value'],
                            'exit_value': exit_value,
                            'pnl': pnl,
                            'pnl_pct': pnl_pct,
                            'days_held': days_held,
                            'exit_reason': exit_signal['reason'],
                            'exit_strength': exit_signal['strength']
                        }
                        
                        self.trades.append(trade)
                        self.current_capital += exit_value
                        del self.positions[symbol]
                        
                        status = "💚" if pnl > 0 else "❤️"
                        print(f"{status} SELL {symbol}: ₹{exit_price:.2f} | P&L: ₹{pnl:,.2f} ({pnl_pct:.2%}) | {exit_signal['reason']}")
                    
                    else:
                        current_value = position['shares'] * row['close']
                        date_positions[symbol] = current_value
                
                # Check entry conditions (if no position and space available)
                elif len(self.positions) < 5:  # Max 5 positions
                    entry_signal = self.check_enhanced_entry_conditions(row)
                    
                    if entry_signal and entry_signal['strength'] >= 0.7:
                        # Calculate position size
                        max_position_value = self.current_capital * self.max_position_size
                        available_capital = self.current_capital * 0.95
                        
                        if available_capital >= max_position_value:
                            entry_price = row['close']
                            position_value = min(max_position_value, available_capital)
                            shares = int(position_value / entry_price)
                            actual_position_value = shares * entry_price
                            
                            if shares > 0:
                                self.positions[symbol] = {
                                    'entry_date': date,
                                    'entry_price': entry_price,
                                    'shares': shares,
                                    'position_value': actual_position_value
                                }
                                
                                self.current_capital -= actual_position_value
                                date_positions[symbol] = actual_position_value
                                
                                print(f"💙 BUY  {symbol}: ₹{entry_price:.2f} | Shares: {shares} | Value: ₹{actual_position_value:,.2f} | Strength: {entry_signal['strength']:.2f}")
                
                elif symbol in self.positions:
                    current_value = self.positions[symbol]['shares'] * row['close']
                    date_positions[symbol] = current_value
            
            # Calculate daily portfolio value
            total_positions_value = sum(date_positions.values())
            total_portfolio_value = self.current_capital + total_positions_value
            
            daily_portfolio.append({
                'date': date,
                'cash': self.current_capital,
                'positions_value': total_positions_value,
                'total_value': total_portfolio_value,
                'positions_count': len(self.positions)
            })
        
        self.portfolio_values = daily_portfolio
        
        # Close remaining positions
        final_date = all_dates[-1]
        for symbol in list(self.positions.keys()):
            if symbol in data:
                symbol_data = data[symbol]
                final_data = symbol_data[symbol_data['date'].dt.date == final_date]
                
                if not final_data.empty:
                    final_price = final_data.iloc[-1]['close']
                    position = self.positions[symbol]
                    
                    exit_value = position['shares'] * final_price
                    pnl = exit_value - position['position_value']
                    pnl_pct = (final_price - position['entry_price']) / position['entry_price']
                    days_held = (final_date - position['entry_date']).days
                    
                    trade = {
                        'symbol': symbol,
                        'entry_date': position['entry_date'],
                        'exit_date': final_date,
                        'entry_price': position['entry_price'],
                        'exit_price': final_price,
                        'shares': position['shares'],
                        'position_value': position['position_value'],
                        'exit_value': exit_value,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'days_held': days_held,
                        'exit_reason': 'end_of_backtest',
                        'exit_strength': 0.5
                    }
                    
                    self.trades.append(trade)
                    self.current_capital += exit_value
        
        return self.analyze_results()
    
    def analyze_results(self):
        """Analyze backtest results"""
        if not self.trades:
            return {"error": "No trades executed"}
        
        trades_df = pd.DataFrame(self.trades)
        portfolio_df = pd.DataFrame(self.portfolio_values)
        
        # Basic statistics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] <= 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # P&L statistics
        total_pnl = trades_df['pnl'].sum()
        total_pnl_pct = (self.current_capital / self.initial_capital) - 1
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] <= 0]['pnl'].mean() if losing_trades > 0 else 0
        
        # Risk metrics
        if len(portfolio_df) > 1:
            portfolio_df['daily_return'] = portfolio_df['total_value'].pct_change()
            daily_returns = portfolio_df['daily_return'].dropna()
            
            volatility = daily_returns.std() * np.sqrt(252)
            avg_daily_return = daily_returns.mean()
            sharpe_ratio = (avg_daily_return * 252) / volatility if volatility > 0 else 0
            
            # Maximum drawdown
            portfolio_df['peak'] = portfolio_df['total_value'].expanding().max()
            portfolio_df['drawdown'] = (portfolio_df['total_value'] - portfolio_df['peak']) / portfolio_df['peak']
            max_drawdown = portfolio_df['drawdown'].min()
        else:
            volatility = 0
            sharpe_ratio = 0
            max_drawdown = 0
        
        # Analysis by exit reason
        exit_reasons = trades_df['exit_reason'].value_counts().to_dict()
        
        # Performance by symbol
        symbol_performance = trades_df.groupby('symbol').agg({
            'pnl': 'sum',
            'pnl_pct': 'mean',
            'entry_date': 'count'
        }).rename(columns={'entry_date': 'trade_count'}).to_dict('index')
        
        results = {
            'summary': {
                'initial_capital': self.initial_capital,
                'final_capital': self.current_capital,
                'total_pnl': total_pnl,
                'total_return_pct': total_pnl_pct,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': abs(avg_win * winning_trades / (avg_loss * losing_trades)) if avg_loss != 0 else float('inf'),
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'volatility': volatility
            },
            'trades': trades_df.to_dict('records'),
            'daily_portfolio': portfolio_df.to_dict('records'),
            'exit_reasons': exit_reasons,
            'symbol_performance': symbol_performance
        }
        
        return results
    
    def print_results(self, results):
        """Print formatted backtest results"""
        summary = results['summary']
        
        print("\n" + "="*80)
        print("🎯 ENHANCED STRATEGY BACKTEST RESULTS")
        print("="*80)
        
        print(f"\n💰 FINANCIAL PERFORMANCE")
        print(f"Initial Capital:     ₹{summary['initial_capital']:,.2f}")
        print(f"Final Capital:       ₹{summary['final_capital']:,.2f}")
        print(f"Total P&L:           ₹{summary['total_pnl']:,.2f}")
        print(f"Total Return:        {summary['total_return_pct']:.2%}")
        
        print(f"\n📊 TRADE STATISTICS")
        print(f"Total Trades:        {summary['total_trades']}")
        print(f"Winning Trades:      {summary['winning_trades']} ({summary['win_rate']:.1%})")
        print(f"Losing Trades:       {summary['losing_trades']}")
        print(f"Average Win:         ₹{summary['avg_win']:,.2f}")
        print(f"Average Loss:        ₹{summary['avg_loss']:,.2f}")
        print(f"Profit Factor:       {summary['profit_factor']:.2f}")
        
        print(f"\n📈 RISK METRICS")
        print(f"Sharpe Ratio:        {summary['sharpe_ratio']:.2f}")
        print(f"Maximum Drawdown:    {summary['max_drawdown']:.2%}")
        print(f"Volatility:          {summary['volatility']:.2%}")
        
        # Exit reasons
        if 'exit_reasons' in results:
            print(f"\n📤 EXIT REASON ANALYSIS")
            for reason, count in results['exit_reasons'].items():
                print(f"  {reason:25} {count:3d} trades")
        
        # Symbol performance
        if 'symbol_performance' in results:
            print(f"\n🏢 SYMBOL PERFORMANCE")
            for symbol, perf in results['symbol_performance'].items():
                print(f"  {symbol:10} P&L: ₹{perf['pnl']:7,.0f} | Avg: {perf['pnl_pct']:6.1%} | Trades: {perf['trade_count']:2d}")
        
        print("\n" + "="*80)

def main():
    """Main backtesting function"""
    print("🚀 MyBreezeApp Enhanced Strategy Backtesting (Simulated Data)")
    print("=" * 70)
    
    # Configuration
    symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR']
    start_date = '2023-01-01'
    end_date = '2024-10-31'
    initial_capital = 100000
    
    print(f"📅 Period: {start_date} to {end_date}")
    print(f"💰 Initial Capital: ₹{initial_capital:,}")
    print(f"📈 Symbols: {', '.join(symbols)}")
    print(f"🔧 Using simulated market data with realistic price patterns")
    print()
    
    # Generate market data
    data_generator = SimulatedMarketDataGenerator(start_date, end_date, symbols)
    data = {}
    
    print("📊 Generating realistic market data...")
    initial_prices = {'RELIANCE': 2500, 'TCS': 3200, 'HDFCBANK': 1600, 'INFY': 1400, 'HINDUNILVR': 2400}
    
    for symbol in symbols:
        print(f"  Generating {symbol}...")
        initial_price = initial_prices.get(symbol, 1000)
        data[symbol] = data_generator.generate_realistic_data(symbol, initial_price)
    
    # Initialize backtester
    backtester = EnhancedStrategyBacktester(initial_capital)
    
    # Calculate indicators
    print(f"\n🔧 Calculating enhanced technical indicators...")
    for symbol in data:
        print(f"  Processing {symbol}...")
        data[symbol] = backtester.calculate_enhanced_indicators(data[symbol])
    
    # Run backtest
    print(f"\n🎯 Running enhanced strategy backtest...")
    results = backtester.run_backtest(data, symbols)
    
    # Print results
    backtester.print_results(results)
    
    # Save results
    results_dir = Path('reports')
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = results_dir / f'backtest_results_{timestamp}.json'
    
    # Convert dates for JSON serialization
    json_results = results.copy()
    if 'trades' in json_results:
        for trade in json_results['trades']:
            if 'entry_date' in trade:
                trade['entry_date'] = str(trade['entry_date'])
            if 'exit_date' in trade:
                trade['exit_date'] = str(trade['exit_date'])
    
    if 'daily_portfolio' in json_results:
        for day in json_results['daily_portfolio']:
            if 'date' in day:
                day['date'] = str(day['date'])
    
    with open(results_file, 'w') as f:
        json.dump(json_results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    # Create trades CSV
    if results['trades']:
        trades_df = pd.DataFrame(results['trades'])
        trades_csv = results_dir / f'trades_{timestamp}.csv'
        trades_df.to_csv(trades_csv, index=False)
        print(f"📊 Trades CSV saved to: {trades_csv}")
    
    return results

if __name__ == "__main__":
    try:
        results = main()
    except KeyboardInterrupt:
        print("\n❌ Backtesting interrupted by user")
    except Exception as e:
        print(f"\n❌ Backtesting failed: {e}")
        import traceback
        traceback.print_exc()