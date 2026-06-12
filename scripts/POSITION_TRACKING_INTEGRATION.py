"""
INTEGRATION GUIDE: Using Position Tracker with Backtests
=========================================================

This shows how to integrate the PositionTracker into your
existing backtesting strategies to track all positions
across multiple days.
"""

# ============================================================================
# EXAMPLE 1: Simple Integration with Strategy Backtest
# ============================================================================

from POSITION_TRACKING_SYSTEM import PositionTracker, Position, PositionStatus
import pandas as pd
import numpy as np
from datetime import datetime

# Initialize tracker
tracker = PositionTracker()

# Sample data
data = pd.DataFrame({
    'Date': pd.date_range('2026-01-01', periods=100, freq='D'),
    'Close': np.random.randn(100).cumsum() + 100,
    'Volume': np.random.randint(1000000, 10000000, 100)
})

# ============================================================================
# Strategy with Position Tracking
# ============================================================================

def mean_reversion_with_tracking(data, symbol, tracker):
    """Mean Reversion with full position tracking"""
    
    sma20 = data['Close'].rolling(20).mean()
    position_id = None
    
    for i in range(20, len(data)):
        price = data['Close'].iloc[i]
        date = data['Date'].iloc[i]
        sma = sma20.iloc[i]
        
        # Entry condition
        if position_id is None and price < sma * 0.98:
            # OPEN POSITION
            position_id = tracker.open_position(
                symbol=symbol,
                strategy='Mean Reversion',
                entry_date=date,
                entry_price=price,
                entry_index=i,
                quantity=1.0
            )
            print(f"🟢 Entry: {date.date()} @ ${price:.2f}")
        
        # Exit condition
        elif position_id is not None and price > sma * 1.02:
            # CLOSE POSITION
            tracker.close_position(
                position_id=position_id,
                exit_date=date,
                exit_price=price,
                exit_index=i
            )
            print(f"🔴 Exit: {date.date()} @ ${price:.2f}")
            position_id = None
    
    return tracker

# Run the strategy
tracker = mean_reversion_with_tracking(data, 'TEST', tracker)

# ============================================================================
# Query Results
# ============================================================================

# Get all closed trades
closed_trades = tracker.get_closed_positions()

print("\n" + "="*80)
print("CLOSED POSITIONS:")
print("="*80)
for pos in closed_trades:
    print(f"\nPosition {pos.position_id}:")
    print(f"  Entry: {pos.entry_date.date()} @ ${pos.entry_price:.2f}")
    print(f"  Exit:  {pos.exit_date.date()} @ ${pos.exit_price:.2f}")
    print(f"  Days:  {pos.days_held}")
    print(f"  Return: {pos.return_pct:+.2f}%")

# Get open positions (if any still active)
open_trades = tracker.get_open_positions()
print(f"\n\nOPEN POSITIONS: {len(open_trades)}")

# Get summary stats
summary = tracker.get_summary_stats()
print(f"\nSUMMARY:")
print(f"  Total Trades: {summary['total_positions']}")
print(f"  Winners: {summary['winning_trades']}")
print(f"  Losers: {summary['losing_trades']}")
print(f"  Win Rate: {summary['win_rate']:.1f}%")
print(f"  Avg Return: {summary['avg_return']:+.2f}%")

# ============================================================================
# EXAMPLE 2: Multi-Strategy Tracking
# ============================================================================

def run_multi_strategy_backtest(data, tracker):
    """Track positions across multiple strategies"""
    
    # Strategy 1: Mean Reversion
    sma20 = data['Close'].rolling(20).mean()
    mr_position = None
    
    # Strategy 2: Momentum
    momentum = data['Close'].diff(5)
    mom_position = None
    
    for i in range(20, len(data)):
        price = data['Close'].iloc[i]
        date = data['Date'].iloc[i]
        
        # MEAN REVERSION LOGIC
        if mr_position is None and price < sma20.iloc[i] * 0.98:
            mr_position = tracker.open_position(
                symbol='MEAN_REV',
                strategy='Mean Reversion',
                entry_date=date,
                entry_price=price,
                entry_index=i
            )
        elif mr_position is not None and price > sma20.iloc[i] * 1.02:
            tracker.close_position(mr_position, date, price, i)
            mr_position = None
        
        # MOMENTUM LOGIC
        if mom_position is None and momentum.iloc[i] > 0.5:
            mom_position = tracker.open_position(
                symbol='MOMENTUM',
                strategy='Momentum',
                entry_date=date,
                entry_price=price,
                entry_index=i
            )
        elif mom_position is not None and momentum.iloc[i] < -0.5:
            tracker.close_position(mom_position, date, price, i)
            mom_position = None
    
    return tracker

# ============================================================================
# EXAMPLE 3: Risk Monitoring (Unrealized P&L)
# ============================================================================

def monitor_active_positions(tracker, current_prices):
    """Monitor open positions for risk management"""
    
    open_pos = tracker.get_open_positions()
    
    print("\nACTIVE POSITIONS MONITOR:")
    print("="*80)
    
    total_unrealized = 0
    
    for pos in open_pos:
        current_price = current_prices.get(pos.symbol, pos.entry_price)
        unrealized_return = ((current_price - pos.entry_price) / pos.entry_price) * 100
        unrealized_pnl = (current_price - pos.entry_price) * pos.quantity
        
        total_unrealized += unrealized_pnl
        
        status = "📈" if unrealized_return > 0 else "📉"
        print(f"\n{status} Position {pos.position_id} ({pos.symbol}):")
        print(f"    Entry: ${pos.entry_price:.2f}")
        print(f"    Current: ${current_price:.2f}")
        print(f"    Days Held: {(datetime.now() - pos.entry_date).days}")
        print(f"    Unrealized: {unrealized_return:+.2f}% (${unrealized_pnl:+.2f})")
    
    print(f"\n{'='*80}")
    print(f"Total Unrealized P&L: ${total_unrealized:+.2f}")
    
    # Risk checks
    for pos in open_pos:
        current_price = current_prices.get(pos.symbol, pos.entry_price)
        unrealized_return = ((current_price - pos.entry_price) / pos.entry_price) * 100
        
        if unrealized_return < -5:
            print(f"⚠️  ALERT: Position {pos.position_id} down {unrealized_return:.2f}%")
        if (datetime.now() - pos.entry_date).days > 60:
            print(f"⏰ ALERT: Position {pos.position_id} held for >60 days")

# ============================================================================
# EXAMPLE 4: Generate Daily Report
# ============================================================================

def generate_daily_report(tracker, date, current_prices, portfolio_value, cash):
    """Generate daily portfolio snapshot"""
    
    # Record daily snapshot
    tracker.daily_snapshot(date, current_prices, portfolio_value, cash)
    
    # Print report
    open_pos = tracker.get_open_positions()
    closed_today = [p for p in tracker.get_closed_positions() 
                   if p.exit_date.date() == date.date()]
    
    print(f"\n📊 DAILY REPORT - {date.date()}")
    print("="*80)
    print(f"Portfolio Value: ${portfolio_value:,.2f}")
    print(f"Cash: ${cash:,.2f}")
    print(f"Open Positions: {len(open_pos)}")
    print(f"Positions Closed Today: {len(closed_today)}")
    
    # Closed today summary
    if closed_today:
        print("\nClosed Today:")
        for pos in closed_today:
            print(f"  {pos.symbol}: {pos.return_pct:+.2f}%")

# ============================================================================
# EXAMPLE 5: Export and Analysis
# ============================================================================

import json

def export_position_data(tracker, filename='positions_export.json'):
    """Export positions for external analysis"""
    
    export_data = {
        'summary': tracker.get_summary_stats(),
        'positions': [p.to_dict() for p in tracker.positions],
        'logs': tracker.position_logs,
        'snapshots': tracker.daily_snapshots
    }
    
    # Convert to JSON-serializable format
    export_json = json.dumps(export_data, indent=2, default=str)
    
    with open(filename, 'w') as f:
        f.write(export_json)
    
    print(f"✓ Exported to {filename}")
    return export_data

# ============================================================================
# MAIN: Full Integration Example
# ============================================================================

if __name__ == "__main__":
    
    print("🎯 POSITION TRACKER INTEGRATION EXAMPLES\n")
    
    # Create fresh tracker
    tracker = PositionTracker()
    
    # Run strategy
    print("Running Mean Reversion Strategy...")
    tracker = mean_reversion_with_tracking(data, 'TEST', tracker)
    
    # Get results
    print("\n" + "="*80)
    summary = tracker.get_summary_stats()
    print(f"Strategy Results:")
    print(f"  Total Positions: {summary['total_positions']}")
    print(f"  Win Rate: {summary['win_rate']:.1f}%")
    print(f"  Avg Return: {summary['avg_return']:+.2f}%")
    print(f"  Max Return: {summary['max_return']:+.2f}%")
    print(f"  Min Return: {summary['min_return']:+.2f}%")
    print(f"  Avg Days Held: {summary['avg_days_held']:.1f}")
    
    # Export
    export_position_data(tracker, 'integration_example_positions.json')
    
    print("\n✅ Integration Complete!")
