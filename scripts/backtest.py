#!/usr/bin/env python3
"""
MyBreezeApp Enhanced Strategy Backtesting Script
Tests the Buy & Hold trend-following strategy with MACD, RSI, and Stochastic RSI
"""
import sys
import os
import pandas as pd
import numpy as np
import yfinance as yf
import json
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from utils.indicators import TechnicalIndicators
from config import Config

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
        
    def fetch_data(self, symbols, start_date, end_date):
        """Fetch historical data for backtesting"""
        print(f"📊 Fetching historical data from {start_date} to {end_date}")
        
        data = {}
        failed_symbols = []
        
        for symbol in symbols:
            try:
                print(f"  Downloading {symbol}...")
                
                # Convert Indian symbols for yfinance
                yf_symbol = f"{symbol}.NS" if not symbol.endswith('.NS') else symbol
                
                ticker = yf.Ticker(yf_symbol)
                df = ticker.history(start=start_date, end=end_date)
                
                if df.empty:
                    print(f"  ⚠️  No data available for {symbol}")
                    failed_symbols.append(symbol)
                    continue
                
                # Rename columns to match our format
                df.columns = df.columns.str.lower()
                df = df.rename(columns={'adj close': 'close'})
                
                # Reset index to get date as column
                df = df.reset_index()
                df['date'] = df['Date']
                
                data[symbol] = df
                print(f"  ✅ {symbol}: {len(df)} data points")
                
            except Exception as e:
                print(f"  ❌ Failed to fetch {symbol}: {e}")
                failed_symbols.append(symbol)
        
        if failed_symbols:
            print(f"⚠️  Failed to fetch data for: {', '.join(failed_symbols)}")
        
        return data
    
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
            
            # Time-based exit (holding too long)
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
        
        # Combine all data for portfolio tracking
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
                
                row = day_data.iloc[-1]  # Take last entry for the day
                
                # Check if we have a position
                if symbol in self.positions:
                    position = self.positions[symbol]
                    days_held = (date - position['entry_date']).days
                    
                    # Check exit conditions
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
                        
                        # Remove position
                        del self.positions[symbol]
                        
                        print(f"📤 SELL {symbol}: ₹{exit_price:.2f} | P&L: ₹{pnl:,.2f} ({pnl_pct:.2%}) | Reason: {exit_signal['reason']}")
                    
                    else:
                        # Update position value
                        current_value = position['shares'] * row['close']
                        date_positions[symbol] = current_value
                
                # Check entry conditions (if no position)
                elif len(self.positions) < 5:  # Max 5 positions
                    entry_signal = self.check_enhanced_entry_conditions(row)
                    
                    if entry_signal and entry_signal['strength'] >= 0.7:  # High confidence threshold
                        # Calculate position size
                        max_position_value = self.current_capital * self.max_position_size
                        available_capital = self.current_capital * 0.95  # Keep 5% cash
                        
                        if available_capital >= max_position_value:
                            entry_price = row['close']
                            position_value = min(max_position_value, available_capital)
                            shares = int(position_value / entry_price)
                            actual_position_value = shares * entry_price
                            
                            if shares > 0:
                                # Create position
                                self.positions[symbol] = {
                                    'entry_date': date,
                                    'entry_price': entry_price,
                                    'shares': shares,
                                    'position_value': actual_position_value
                                }
                                
                                self.current_capital -= actual_position_value
                                date_positions[symbol] = actual_position_value
                                
                                print(f"📥 BUY {symbol}: ₹{entry_price:.2f} | Shares: {shares} | Value: ₹{actual_position_value:,.2f} | Strength: {entry_signal['strength']:.2f}")
                
                # Add existing positions to daily value
                elif symbol in self.positions:
                    current_value = self.positions[symbol]['shares'] * row['close']
                    date_positions[symbol] = current_value
            
            # Calculate total portfolio value
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
        
        # Close any remaining positions at the end
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
            
            volatility = daily_returns.std() * np.sqrt(252)  # Annualized
            sharpe_ratio = (total_pnl_pct * 252) / volatility if volatility > 0 else 0
            
            # Maximum drawdown
            portfolio_df['peak'] = portfolio_df['total_value'].expanding().max()
            portfolio_df['drawdown'] = (portfolio_df['total_value'] - portfolio_df['peak']) / portfolio_df['peak']
            max_drawdown = portfolio_df['drawdown'].min()
        else:
            volatility = 0
            sharpe_ratio = 0
            max_drawdown = 0
        
        # Trade analysis by exit reason
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
            'symbol_performance': symbol_performance,
            'enhanced_metrics': self.calculate_enhanced_metrics(trades_df)
        }
        
        return results
    
    def calculate_enhanced_metrics(self, trades_df):
        """Calculate enhanced strategy-specific metrics"""
        try:
            metrics = {}
            
            # Signal strength analysis
            if 'exit_strength' in trades_df.columns:
                metrics['avg_exit_strength'] = trades_df['exit_strength'].mean()
                
            # Holding period analysis
            metrics['avg_holding_days'] = trades_df['days_held'].mean()
            metrics['median_holding_days'] = trades_df['days_held'].median()
            
            # Exit reason effectiveness
            reason_performance = trades_df.groupby('exit_reason')['pnl_pct'].agg(['mean', 'count']).to_dict('index')
            metrics['exit_reason_performance'] = reason_performance
            
            # Monthly performance
            trades_df['exit_month'] = pd.to_datetime(trades_df['exit_date']).dt.to_period('M')
            monthly_pnl = trades_df.groupby('exit_month')['pnl'].sum().to_dict()
            metrics['monthly_pnl'] = {str(k): v for k, v in monthly_pnl.items()}
            
            return metrics
            
        except Exception as e:
            print(f"Warning: Could not calculate enhanced metrics: {e}")
            return {}
    
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
        
        # Enhanced metrics
        if 'enhanced_metrics' in results:
            enhanced = results['enhanced_metrics']
            print(f"\n🔥 ENHANCED STRATEGY METRICS")
            
            if 'avg_holding_days' in enhanced:
                print(f"Avg Holding Period:  {enhanced['avg_holding_days']:.1f} days")
            
            if 'exit_reason_performance' in enhanced:
                print(f"\n📤 EXIT REASON ANALYSIS")
                for reason, stats in enhanced['exit_reason_performance'].items():
                    print(f"  {reason:20} Avg Return: {stats['mean']:.2%} | Count: {stats['count']}")
        
        # Symbol performance
        if 'symbol_performance' in results:
            print(f"\n🏢 SYMBOL PERFORMANCE")
            for symbol, perf in results['symbol_performance'].items():
                print(f"  {symbol:10} P&L: ₹{perf['pnl']:,.2f} | Avg Return: {perf['pnl_pct']:.2%} | Trades: {perf['trade_count']}")
        
        print("\n" + "="*80)

def main():
    """Main backtesting function"""
    print("🚀 MyBreezeApp Enhanced Strategy Backtesting")
    print("=" * 60)
    
    # Configuration
    symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR', 'ITC', 'SBIN', 'BAJFINANCE', 'BHARTIARTL', 'ASIANPAINT']
    start_date = '2023-01-01'
    end_date = '2024-10-31'
    initial_capital = 100000
    
    print(f"📅 Period: {start_date} to {end_date}")
    print(f"💰 Initial Capital: ₹{initial_capital:,}")
    print(f"📈 Symbols: {', '.join(symbols)}")
    print()
    
    # Initialize backtester
    backtester = EnhancedStrategyBacktester(initial_capital)
    
    # Fetch data
    data = backtester.fetch_data(symbols, start_date, end_date)
    
    if not data:
        print("❌ No data available for backtesting")
        return
    
    # Calculate indicators for all symbols
    print(f"\n🔧 Calculating enhanced technical indicators...")
    for symbol in data:
        print(f"  Processing {symbol}...")
        data[symbol] = backtester.calculate_enhanced_indicators(data[symbol])
    
    # Run backtest
    print(f"\n🎯 Running backtest...")
    results = backtester.run_backtest(data, list(data.keys()))
    
    # Print results
    backtester.print_results(results)
    
    # Save results
    results_dir = Path('reports')
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = results_dir / f'backtest_results_{timestamp}.json'
    
    # Convert dates to strings for JSON serialization
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
    
    # Create summary CSV
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