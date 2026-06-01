#!/usr/bin/env python3
"""
Profit Booking Strategy Comprehensive Backtest
Tests Fixed Full Exit vs Partial Exit + Trailing Stop strategies
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

from strategies.profit_booking_manager import (
    ProfitBookingManager, ExitStrategy, ExitReason
)
from utils.indicators import TechnicalIndicators
from config import Config


class ProfitBookingBacktester:
    """Comprehensive backtester for profit booking strategies"""
    
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.config = Config()
        self.indicators = TechnicalIndicators()
        self.results = {}
        
        # Strategy managers
        self.managers = {
            ExitStrategy.FIXED_FULL_EXIT: ProfitBookingManager(),
            ExitStrategy.PARTIAL_WITH_TRAILING: ProfitBookingManager(),
        }
        
        # Configure managers
        self.managers[ExitStrategy.FIXED_FULL_EXIT].config['target_pct'] = 0.065
        self.managers[ExitStrategy.FIXED_FULL_EXIT].config['stop_loss_pct'] = 0.04
        self.managers[ExitStrategy.FIXED_FULL_EXIT].default_exit_strategy = ExitStrategy.FIXED_FULL_EXIT
        
        self.managers[ExitStrategy.PARTIAL_WITH_TRAILING].config['target_pct'] = 0.065
        self.managers[ExitStrategy.PARTIAL_WITH_TRAILING].config['stop_loss_pct'] = 0.04
        self.managers[ExitStrategy.PARTIAL_WITH_TRAILING].config['trailing_stop_pct'] = 0.02
        self.managers[ExitStrategy.PARTIAL_WITH_TRAILING].config['partial_exit_ratio'] = 0.50
        self.managers[ExitStrategy.PARTIAL_WITH_TRAILING].default_exit_strategy = ExitStrategy.PARTIAL_WITH_TRAILING
    
    def fetch_data(self, symbols, start_date, end_date):
        """Fetch historical data for backtesting"""
        print(f"\n📊 Fetching historical data from {start_date} to {end_date}")
        print("=" * 80)
        
        data = {}
        for symbol in symbols:
            try:
                yf_symbol = f"{symbol}.NS" if not symbol.endswith('.NS') else symbol
                ticker = yf.Ticker(yf_symbol)
                df = ticker.history(start=start_date, end=end_date)
                
                if df.empty:
                    print(f"⚠️  No data for {symbol}")
                    continue
                
                df.columns = df.columns.str.lower()
                df = df.rename(columns={'adj close': 'close'})
                df = df.reset_index()
                df['date'] = df['Date']
                df['symbol'] = symbol
                
                data[symbol] = df
                print(f"✅ {symbol:8s} | {len(df):4d} candles | "
                      f"{df['date'].min().date()} to {df['date'].max().date()}")
            
            except Exception as e:
                print(f"❌ Error fetching {symbol}: {str(e)[:60]}")
        
        return data
    
    def identify_entry_signals(self, data):
        """Identify potential entry points using technical indicators"""
        print(f"\n🔍 Identifying entry signals...")
        print("=" * 80)
        
        entry_signals = []
        
        for symbol, df in data.items():
            if len(df) < 30:
                continue
            
            # Calculate indicators
            df['ma20'] = df['close'].rolling(20).mean()
            df['rsi'] = self.indicators.rsi(df['close'], 14)
            df['volume_ma'] = df['volume'].rolling(20).mean()
            
            # Entry criteria: Price > MA20, RSI < 70, Volume confirmation
            for i in range(20, len(df) - 1):
                price = df['close'].iloc[i]
                ma = df['ma20'].iloc[i]
                rsi = df['rsi'].iloc[i]
                volume = df['volume'].iloc[i]
                avg_volume = df['volume_ma'].iloc[i]
                date = df['date'].iloc[i]
                
                # Entry condition
                if (price > ma and 40 < rsi < 70 and volume > avg_volume * 0.8):
                    entry_signals.append({
                        'symbol': symbol,
                        'entry_date': date,
                        'entry_price': price,
                        'entry_idx': i,
                        'df_start_idx': i,
                    })
        
        print(f"Found {len(entry_signals)} entry signals across {len(data)} symbols")
        return entry_signals, data
    
    def run_backtest(self, entry_signals, data, strategy_type):
        """Run backtest for a specific strategy"""
        manager = self.managers[strategy_type]
        trades_executed = []
        
        for signal in entry_signals:
            symbol = signal['symbol']
            entry_price = signal['entry_price']
            entry_idx = signal['df_start_idx']
            df = data[symbol]
            
            if entry_idx >= len(df) - 10:  # Need at least 10 candles after entry
                continue
            
            # Create position
            position_id = f"{symbol}_{len(manager.positions)}"
            pos = manager.create_position(
                symbol=symbol,
                entry_price=entry_price,
                quantity=100,  # Fixed quantity for simplicity
                position_id=position_id,
                exit_strategy=strategy_type
            )
            
            # Simulate price movement
            exit_executed = False
            for j in range(entry_idx + 1, len(df)):
                current_price = df['close'].iloc[j]
                current_date = df['date'].iloc[j]
                
                should_exit, exit_reason, exit_details = manager.check_exit_conditions(
                    position_id, current_price
                )
                
                if should_exit and exit_details:
                    exit_qty = exit_details.get('exit_qty', pos.quantity)
                    exit_record = manager.execute_exit(position_id, current_price, exit_qty)
                    trades_executed.append(exit_record)
                    exit_executed = True
                    
                    # For partial exit, track continuation
                    if exit_reason == ExitReason.TARGET_HIT and 'remaining_qty' in exit_details:
                        # Continue simulating for trailing exit
                        pass
                    else:
                        break
            
            # Force exit if no exit triggered (max holding = 50 days)
            if not exit_executed and entry_idx + 50 < len(df):
                final_price = df['close'].iloc[entry_idx + 50]
                exit_record = manager.execute_exit(position_id, final_price)
                trades_executed.append(exit_record)
        
        return manager, trades_executed
    
    def print_detailed_results(self, strategy_type, manager, trades):
        """Print detailed trade results"""
        strategy_name = "FIXED FULL EXIT" if strategy_type == ExitStrategy.FIXED_FULL_EXIT \
                       else "PARTIAL + TRAILING"
        
        print(f"\n{'='*100}")
        print(f"STRATEGY: {strategy_name}")
        print(f"{'='*100}\n")
        
        # Trade details
        print(f"📋 INDIVIDUAL TRADES (Top 15)")
        print("-" * 100)
        print(f"{'Symbol':<8} {'Entry':<10} {'Exit':<10} {'Qty':<6} {'P&L $':<10} {'P&L %':<8} "
              f"{'Max Profit %':<12} {'Reason':<20}")
        print("-" * 100)
        
        for i, trade in enumerate(manager.exit_history[:15]):
            symbol = trade['symbol']
            entry = trade['entry_price']
            exit_p = trade['exit_price']
            qty = trade['exit_qty']
            pnl = trade['pnl']
            pnl_pct = trade['pnl_pct']
            max_profit = trade['max_profit_pct']
            reason = trade['exit_reason'].value if trade['exit_reason'] else 'N/A'
            
            print(f"{symbol:<8} ₹{entry:<9.2f} ₹{exit_p:<9.2f} {qty:<6} "
                  f"₹{pnl:<9.0f} {pnl_pct:>6.2f}% {max_profit:>10.2f}% {reason:<20}")
        
        print()
        
        # Summary statistics
        stats = manager.get_strategy_stats()
        
        print(f"📊 PERFORMANCE STATISTICS")
        print("-" * 100)
        print(f"Total Trades:              {stats['total_trades']}")
        print(f"Winning Trades:            {stats['winning_trades']}")
        print(f"Losing Trades:             {stats['losing_trades']}")
        print(f"Win Rate:                  {stats['win_rate']:.1f}%")
        print(f"Profit Factor:             {stats['profit_factor']:.2f}")
        print(f"Total P&L:                 ₹{stats['total_pnl']:,.0f}")
        print(f"Average P&L per Trade:     {stats['avg_pnl_pct']:.2f}%")
        print(f"Sharpe Ratio:              {stats['sharpe_ratio']:.2f}")
        print(f"Max Drawdown:              {stats['max_drawdown']:.2f}%")
        print(f"Average Holding Period:    {stats['avg_holding_days']:.1f} days")
        print()
        
        return stats
    
    def compare_strategies(self, stats_fixed, stats_partial):
        """Compare both strategies"""
        print(f"\n{'='*100}")
        print("STRATEGY COMPARISON")
        print(f"{'='*100}\n")
        
        print(f"{'Metric':<30} {'FIXED EXIT':<20} {'PARTIAL+TRAILING':<20} {'Winner':<10}")
        print("-" * 100)
        
        comparison_data = [
            ('Profit Factor', stats_fixed['profit_factor'], stats_partial['profit_factor']),
            ('Win Rate %', stats_fixed['win_rate'], stats_partial['win_rate']),
            ('Total P&L ₹', stats_fixed['total_pnl'], stats_partial['total_pnl']),
            ('Avg P&L %', stats_fixed['avg_pnl_pct'], stats_partial['avg_pnl_pct']),
            ('Sharpe Ratio', stats_fixed['sharpe_ratio'], stats_partial['sharpe_ratio']),
            ('Max Drawdown %', abs(stats_fixed['max_drawdown']), abs(stats_partial['max_drawdown'])),
        ]
        
        for metric, fixed_val, partial_val in comparison_data:
            # Determine winner (for drawdown, lower is better)
            if metric == 'Max Drawdown %':
                winner = '✅ PARTIAL' if fixed_val > partial_val else '✅ FIXED' if partial_val > fixed_val else 'TIE'
            else:
                winner = '✅ FIXED' if fixed_val < partial_val else '✅ PARTIAL' if partial_val < fixed_val else 'TIE'
            
            # Invert winner for drawdown (lower is better)
            if metric == 'Max Drawdown %':
                winner = '✅ PARTIAL' if fixed_val > partial_val else '✅ FIXED' if partial_val > fixed_val else 'TIE'
            
            print(f"{metric:<30} {fixed_val:>18.2f}   {partial_val:>18.2f}   {winner:<10}")
        
        print()


def main():
    """Main backtest execution"""
    print("\n" + "=" * 100)
    print("🚀 PROFIT BOOKING STRATEGY BACKTEST - COMPREHENSIVE ANALYSIS")
    print("=" * 100)
    
    # Configuration
    symbols = ['TCS', 'WIPRO', 'RELIND', 'MARUTI']
    start_date = '2025-06-01'
    end_date = '2026-05-31'
    
    # Create backtester
    backtester = ProfitBookingBacktester(initial_capital=100000)
    
    # Fetch data
    data = backtester.fetch_data(symbols, start_date, end_date)
    
    if not data:
        print("❌ No data fetched. Exiting.")
        return
    
    # Identify entry signals
    entry_signals, data = backtester.identify_entry_signals(data)
    
    if not entry_signals:
        print("❌ No entry signals found. Exiting.")
        return
    
    # Run backtests for both strategies
    print(f"\n⏳ Running FIXED FULL EXIT backtest...")
    manager_fixed, trades_fixed = backtester.run_backtest(
        entry_signals, data, ExitStrategy.FIXED_FULL_EXIT
    )
    
    print(f"⏳ Running PARTIAL + TRAILING backtest...")
    manager_partial, trades_partial = backtester.run_backtest(
        entry_signals, data, ExitStrategy.PARTIAL_WITH_TRAILING
    )
    
    # Print results
    stats_fixed = backtester.print_detailed_results(
        ExitStrategy.FIXED_FULL_EXIT, manager_fixed, trades_fixed
    )
    
    stats_partial = backtester.print_detailed_results(
        ExitStrategy.PARTIAL_WITH_TRAILING, manager_partial, trades_partial
    )
    
    # Compare strategies
    backtester.compare_strategies(stats_fixed, stats_partial)
    
    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'backtest_period': {'start': start_date, 'end': end_date},
        'symbols': symbols,
        'fixed_full_exit': {
            'trades': len(manager_fixed.exit_history),
            'stats': stats_fixed,
            'exit_history': manager_fixed.exit_history
        },
        'partial_trailing': {
            'trades': len(manager_partial.exit_history),
            'stats': stats_partial,
            'exit_history': manager_partial.exit_history
        }
    }
    
    # Save JSON results
    results_file = Path(__file__).parent / f"backtest_profit_booking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        # Convert datetime objects for JSON serialization
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, ExitReason):
                return obj.value
            raise TypeError(f"Type {type(obj)} not serializable")
        
        json.dump(results, f, default=json_serializer, indent=2)
    
    print(f"\n✅ Results saved to: {results_file}")
    print("\n" + "=" * 100)
    print("📈 BACKTEST COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()
