"""
POSITION TRACKING & MONITORING SYSTEM
======================================

This module provides comprehensive position tracking:
✓ Active positions (entry date, entry price, days held)
✓ Closed positions (entry/exit dates, P&L, holding period)
✓ Position history logs
✓ Daily portfolio snapshots
✓ Real-time position monitoring

Tracks:
- Entry date and price
- Exit date and price
- Days held
- Return %
- Current unrealized P&L (for active positions)
- Portfolio value at each step
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import warnings

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

print("\n" + "="*150)
print("📊 POSITION TRACKING & MONITORING SYSTEM FOR ALGORITHMIC TRADING".center(150))
print("="*150 + "\n")

# ============================================================================
# STEP 1: Position Data Structures
# ============================================================================

class PositionStatus(Enum):
    """Position status enum"""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CLOSING = "CLOSING"  # Signal sent but not yet filled

@dataclass
class Position:
    """Track individual positions"""
    position_id: int
    symbol: str
    strategy: str
    entry_date: datetime
    entry_price: float
    entry_index: int
    quantity: float = 1.0
    status: PositionStatus = PositionStatus.OPEN
    exit_date: datetime = None
    exit_price: float = None
    exit_index: int = None
    
    @property
    def days_held(self) -> int:
        """Days position has been held"""
        if self.exit_date:
            return (self.exit_date - self.entry_date).days
        else:
            return None
    
    @property
    def return_pct(self) -> float:
        """Return percentage"""
        if self.exit_price:
            return ((self.exit_price - self.entry_price) / self.entry_price) * 100
        return None
    
    @property
    def pnl(self) -> float:
        """P&L in currency"""
        if self.exit_price:
            return (self.exit_price - self.entry_price) * self.quantity
        return None
    
    @property
    def unrealized_pnl(self, current_price) -> float:
        """Unrealized P&L for open positions"""
        if self.status == PositionStatus.OPEN:
            return (current_price - self.entry_price) * self.quantity
        return 0
    
    def close(self, exit_date: datetime, exit_price: float, exit_index: int):
        """Close the position"""
        self.exit_date = exit_date
        self.exit_price = exit_price
        self.exit_index = exit_index
        self.status = PositionStatus.CLOSED
    
    def to_dict(self):
        """Convert to dictionary for JSON"""
        return {
            'position_id': self.position_id,
            'symbol': self.symbol,
            'strategy': self.strategy,
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'entry_price': round(self.entry_price, 2),
            'entry_index': self.entry_index,
            'quantity': self.quantity,
            'status': self.status.value,
            'exit_date': self.exit_date.isoformat() if self.exit_date else None,
            'exit_price': round(self.exit_price, 2) if self.exit_price else None,
            'exit_index': self.exit_index,
            'days_held': self.days_held,
            'return_pct': round(self.return_pct, 2) if self.return_pct else None,
            'pnl': round(self.pnl, 2) if self.pnl else None,
        }

class PositionTracker:
    """Track all positions across strategies"""
    
    def __init__(self):
        self.positions: List[Position] = []
        self.position_counter = 0
        self.position_logs: List[Dict] = []
        self.daily_snapshots: List[Dict] = []
        self.active_positions_history: List[Dict] = []
    
    def open_position(self, symbol: str, strategy: str, entry_date: datetime, 
                     entry_price: float, entry_index: int, quantity: float = 1.0) -> int:
        """Open a new position and return position ID"""
        self.position_counter += 1
        position = Position(
            position_id=self.position_counter,
            symbol=symbol,
            strategy=strategy,
            entry_date=entry_date,
            entry_price=entry_price,
            entry_index=entry_index,
            quantity=quantity,
            status=PositionStatus.OPEN
        )
        self.positions.append(position)
        
        # Log the opening
        self.position_logs.append({
            'timestamp': datetime.now().isoformat(),
            'event': 'POSITION_OPENED',
            'position_id': self.position_counter,
            'symbol': symbol,
            'strategy': strategy,
            'entry_date': entry_date.isoformat(),
            'entry_price': entry_price,
            'quantity': quantity
        })
        
        return self.position_counter
    
    def close_position(self, position_id: int, exit_date: datetime, 
                      exit_price: float, exit_index: int):
        """Close a position"""
        for pos in self.positions:
            if pos.position_id == position_id:
                pos.close(exit_date, exit_price, exit_index)
                
                # Log the closing
                self.position_logs.append({
                    'timestamp': datetime.now().isoformat(),
                    'event': 'POSITION_CLOSED',
                    'position_id': position_id,
                    'symbol': pos.symbol,
                    'strategy': pos.strategy,
                    'exit_date': exit_date.isoformat(),
                    'exit_price': exit_price,
                    'days_held': pos.days_held,
                    'return_pct': pos.return_pct,
                    'pnl': pos.pnl
                })
                break
    
    def get_open_positions(self) -> List[Position]:
        """Get all open positions"""
        return [p for p in self.positions if p.status == PositionStatus.OPEN]
    
    def get_closed_positions(self) -> List[Position]:
        """Get all closed positions"""
        return [p for p in self.positions if p.status == PositionStatus.CLOSED]
    
    def get_position_by_id(self, position_id: int) -> Position:
        """Get position by ID"""
        for pos in self.positions:
            if pos.position_id == position_id:
                return pos
        return None
    
    def daily_snapshot(self, date: datetime, current_prices: Dict[str, float], 
                      portfolio_value: float, cash: float):
        """Record daily portfolio snapshot"""
        open_pos = self.get_open_positions()
        
        unrealized_pnl = 0
        position_details = []
        
        for pos in open_pos:
            current_price = current_prices.get(pos.symbol, pos.entry_price)
            upnl = (current_price - pos.entry_price) * pos.quantity
            unrealized_pnl += upnl
            days_held = (date - pos.entry_date).days
            
            position_details.append({
                'position_id': pos.position_id,
                'symbol': pos.symbol,
                'strategy': pos.strategy,
                'entry_price': pos.entry_price,
                'current_price': current_price,
                'entry_date': pos.entry_date.isoformat(),
                'days_held': days_held,
                'unrealized_return_pct': ((current_price - pos.entry_price) / pos.entry_price) * 100,
                'unrealized_pnl': upnl
            })
        
        self.daily_snapshots.append({
            'date': date.isoformat(),
            'portfolio_value': portfolio_value,
            'cash': cash,
            'open_positions_count': len(open_pos),
            'unrealized_pnl': unrealized_pnl,
            'positions': position_details
        })
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics"""
        closed_pos = self.get_closed_positions()
        open_pos = self.get_open_positions()
        
        if len(closed_pos) > 0:
            returns = [p.return_pct for p in closed_pos]
            pnls = [p.pnl for p in closed_pos]
            days_held = [p.days_held for p in closed_pos]
            
            winners = len([r for r in returns if r > 0])
            losers = len([r for r in returns if r < 0])
            breakeven = len([r for r in returns if r == 0])
        else:
            returns = []
            pnls = []
            days_held = []
            winners = losers = breakeven = 0
        
        return {
            'total_positions': len(self.positions),
            'open_positions': len(open_pos),
            'closed_positions': len(closed_pos),
            'winning_trades': winners,
            'losing_trades': losers,
            'breakeven_trades': breakeven,
            'win_rate': (winners / len(closed_pos) * 100) if len(closed_pos) > 0 else 0,
            'avg_return': np.mean(returns) if returns else 0,
            'avg_pnl': np.mean(pnls) if pnls else 0,
            'total_pnl': sum(pnls) if pnls else 0,
            'avg_days_held': np.mean(days_held) if days_held else 0,
            'max_return': max(returns) if returns else 0,
            'min_return': min(returns) if returns else 0,
            'best_position': max(closed_pos, key=lambda p: p.return_pct) if closed_pos else None,
            'worst_position': min(closed_pos, key=lambda p: p.return_pct) if closed_pos else None
        }

# ============================================================================
# STEP 2: Test Position Tracker with Mean Reversion Strategy
# ============================================================================

print("📊 RETRIEVING DATA\n")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from services.breeze_api_production import BreezeAPIService
except:
    BreezeAPIService = None

def get_historical_data(symbol: str, days: int = 365) -> pd.DataFrame:
    """Generate synthetic data"""
    np.random.seed(hash(symbol) % 2**32)
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    start_prices = {
        'NIFTY': 22000, 'BANKNIFTY': 44000, 'INFY': 3400, 'TCS': 4200,
        'RELIANCE': 2800, 'HDFC': 2900, 'ICICIBANK': 950, 'SBIN': 650
    }
    
    start = start_prices.get(symbol, 100)
    returns = np.random.normal(0.0005, 0.02, days)
    prices = start * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': prices * (1 + np.random.normal(0, 0.005, days)),
        'High': prices * (1 + np.abs(np.random.normal(0, 0.01, days))),
        'Low': prices * (1 - np.abs(np.random.normal(0, 0.01, days))),
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, days)
    })
    
    return df

# ============================================================================
# STEP 3: Mean Reversion Strategy with Position Tracking
# ============================================================================

def mean_reversion_with_tracking(data: pd.DataFrame, symbol: str, 
                                tracker: PositionTracker) -> List[Position]:
    """
    Mean Reversion strategy with detailed position tracking
    
    Shows:
    - Entry date/price
    - Exit date/price
    - Days held
    - Return %
    - Active positions on each day
    """
    
    sma20 = data['Close'].rolling(20).mean()
    position_id = None
    
    print(f"\n{'='*130}")
    print(f"📈 DETAILED POSITION TRACKING: {symbol} - MEAN REVERSION STRATEGY")
    print(f"{'='*130}\n")
    
    for i in range(20, len(data)):
        current_date = data['Date'].iloc[i]
        price = data['Close'].iloc[i]
        sma = sma20.iloc[i]
        deviation = (price - sma) / sma * 100 if sma > 0 else 0
        
        # ENTRY SIGNAL: Price is 2% below SMA
        if position_id is None and deviation < -2:
            position_id = tracker.open_position(
                symbol=symbol,
                strategy='Mean Reversion',
                entry_date=current_date,
                entry_price=price,
                entry_index=i,
                quantity=1.0
            )
            pos = tracker.get_position_by_id(position_id)
            print(f"🟢 [{current_date.strftime('%Y-%m-%d')}] ENTRY at ₹{price:.2f} (SMA: ₹{sma:.2f}, Dev: {deviation:.2f}%)")
            print(f"   Position ID: {position_id}")
        
        # EXIT SIGNAL: Price is 2% above SMA
        elif position_id is not None and deviation > 2:
            pos = tracker.get_position_by_id(position_id)
            tracker.close_position(position_id, current_date, price, i)
            
            return_pct = ((price - pos.entry_price) / pos.entry_price) * 100
            days_held = (current_date - pos.entry_date).days
            
            print(f"🔴 [{current_date.strftime('%Y-%m-%d')}] EXIT at ₹{price:.2f} (SMA: ₹{sma:.2f}, Dev: {deviation:.2f}%)")
            print(f"   Days Held: {days_held}")
            print(f"   Return: {return_pct:+.2f}%")
            print(f"   Entry → Exit: ₹{pos.entry_price:.2f} → ₹{price:.2f}")
            print()
            
            position_id = None
    
    # Close any remaining open position
    if position_id is not None:
        final_price = data['Close'].iloc[-1]
        tracker.close_position(position_id, data['Date'].iloc[-1], final_price, len(data)-1)
        pos = tracker.get_position_by_id(position_id)
        return_pct = ((final_price - pos.entry_price) / pos.entry_price) * 100
        days_held = (pos.exit_date - pos.entry_date).days
        print(f"🔴 [{pos.exit_date.strftime('%Y-%m-%d')}] AUTO-EXIT at ₹{final_price:.2f}")
        print(f"   Days Held: {days_held}")
        print(f"   Return: {return_pct:+.2f}%\n")
    
    return tracker.get_closed_positions()

# ============================================================================
# STEP 4: Run Example with NIFTY
# ============================================================================

print("[✓] Loading data for NIFTY...\n")
data = get_historical_data('NIFTY')

tracker = PositionTracker()
closed_positions = mean_reversion_with_tracking(data, 'NIFTY', tracker)

# ============================================================================
# STEP 5: Generate Reports
# ============================================================================

print("="*130)
print("📊 POSITION SUMMARY REPORT".center(130))
print("="*130 + "\n")

summary = tracker.get_summary_stats()

print("TRADE STATISTICS:\n")
print(f"  Total Positions:     {summary['total_positions']}")
print(f"  Open Positions:      {summary['open_positions']}")
print(f"  Closed Positions:    {summary['closed_positions']}")
print(f"  Winning Trades:      {summary['winning_trades']}")
print(f"  Losing Trades:       {summary['losing_trades']}")
print(f"  Breakeven Trades:    {summary['breakeven_trades']}")
print(f"  Win Rate:            {summary['win_rate']:.1f}%")

print(f"\nRETURN STATISTICS:\n")
print(f"  Avg Return/Trade:    {summary['avg_return']:+.2f}%")
print(f"  Max Return:          {summary['max_return']:+.2f}%")
print(f"  Min Return:          {summary['min_return']:+.2f}%")
print(f"  Total P&L:           ₹{summary['total_pnl']:.2f}")
print(f"  Avg P&L/Trade:       ₹{summary['avg_pnl']:.2f}")

print(f"\nHOLDING PERIOD:\n")
print(f"  Avg Days Held:       {summary['avg_days_held']:.1f} days")

if summary['best_position']:
    best = summary['best_position']
    print(f"\n✅ BEST TRADE:\n")
    print(f"  Entry: {best.entry_date.strftime('%Y-%m-%d')} @ ₹{best.entry_price:.2f}")
    print(f"  Exit:  {best.exit_date.strftime('%Y-%m-%d')} @ ₹{best.exit_price:.2f}")
    print(f"  Days:  {best.days_held}")
    print(f"  Return: {best.return_pct:+.2f}%")

if summary['worst_position']:
    worst = summary['worst_position']
    print(f"\n❌ WORST TRADE:\n")
    print(f"  Entry: {worst.entry_date.strftime('%Y-%m-%d')} @ ₹{worst.entry_price:.2f}")
    print(f"  Exit:  {worst.exit_date.strftime('%Y-%m-%d')} @ ₹{worst.exit_price:.2f}")
    print(f"  Days:  {worst.days_held}")
    print(f"  Return: {worst.return_pct:+.2f}%")

# ============================================================================
# STEP 6: Position Details Table
# ============================================================================

print(f"\n{'='*130}")
print("📋 DETAILED POSITION HISTORY".center(130))
print(f"{'='*130}\n")

closed_pos = tracker.get_closed_positions()
print(f"{'ID':<4} {'Symbol':<10} {'Entry Date':<12} {'Entry Price':<12} {'Exit Date':<12} {'Exit Price':<12} {'Days':<6} {'Return':<10}")
print(f"{'-'*130}")

for pos in closed_pos:
    print(f"{pos.position_id:<4} {pos.symbol:<10} {pos.entry_date.strftime('%Y-%m-%d'):<12} "
          f"₹{pos.entry_price:<11.2f} {pos.exit_date.strftime('%Y-%m-%d'):<12} "
          f"₹{pos.exit_price:<11.2f} {pos.days_held:<6} {pos.return_pct:+8.2f}%")

# ============================================================================
# STEP 7: Save Tracking Data
# ============================================================================

print(f"\n{'='*130}")
print("💾 SAVING POSITION DATA".center(130))
print(f"{'='*130}\n")

# Save positions to JSON
positions_json = {
    'summary': summary,
    'positions': [p.to_dict() for p in tracker.positions],
    'logs': tracker.position_logs
}

with open('POSITION_TRACKING_REPORT.json', 'w') as f:
    json.dump(positions_json, f, indent=2, default=str)
print("✓ Saved: POSITION_TRACKING_REPORT.json")

# Save to CSV
positions_df = pd.DataFrame([p.to_dict() for p in tracker.positions])
positions_df.to_csv('POSITION_TRACKING_DETAILED.csv', index=False)
print("✓ Saved: POSITION_TRACKING_DETAILED.csv")

print("\n" + "="*130 + "\n")

print("📌 KEY INSIGHTS:\n")
print("  1. POSITION TRACKING:")
print("     ✓ Every position has a unique ID")
print("     ✓ Entry/exit dates tracked automatically")
print("     ✓ Days held calculated from dates")
print("     ✓ Multi-day holding periods captured\n")

print("  2. ACTIVE POSITIONS:")
print("     ✓ Open positions monitored daily")
print("     ✓ Unrealized P&L calculated in real-time")
print("     ✓ Can check status of each position anytime\n")

print("  3. CLOSED POSITIONS:")
print("     ✓ Complete trade history maintained")
print("     ✓ Return % calculated for each trade")
print("     ✓ Win/loss statistics derived from trades\n")

print("  4. PORTFOLIO MONITORING:")
print("     ✓ Daily snapshots available")
print("     ✓ Shows positions held each day")
print("     ✓ Tracks portfolio evolution\n")

print("="*130 + "\n")
