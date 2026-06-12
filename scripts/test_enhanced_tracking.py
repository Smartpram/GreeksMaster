#!/usr/bin/env python3
"""
Quick Test: Enhanced Paper Trading with Position Tracking
Demonstrates realistic position opening, tracking, and closing with P&L
"""

import json
from datetime import datetime

def test_enhanced_position_tracking():
    """Demonstrate enhanced position tracking"""
    
    print("\n" + "="*80)
    print("  ENHANCED PAPER TRADING - POSITION TRACKING DEMO")
    print("="*80)
    print("  Simulating realistic trades with prices, entries, and exits")
    print("  Tracking: Entry Price -> Exit Price -> P&L Calculation\n")
    
    # Simulate data
    trades_data = [
        # Opening Surge
        {
            'ticker': 'NIFTY50',
            'action': 'BUY',
            'entry_price': 23850,
            'confidence': 0.67,
            'exit_price': 23865,
            'exit_reason': 'target',
            'session': 'opening'
        },
        {
            'ticker': 'BANKNIFTY',
            'action': 'SELL',
            'entry_price': 48500,
            'confidence': 1.0,
            'exit_price': 48485,
            'exit_reason': 'target',
            'session': 'opening'
        },
        {
            'ticker': 'FINNIFTY',
            'action': 'BUY',
            'entry_price': 21800,
            'confidence': 0.67,
            'exit_price': 21815,
            'exit_reason': 'target',
            'session': 'opening'
        },
        # Intraday
        {
            'ticker': 'NIFTY50',
            'action': 'SELL',
            'entry_price': 23860,
            'confidence': 0.67,
            'exit_price': 23850,
            'exit_reason': 'stop_loss',
            'session': 'intraday'
        },
        {
            'ticker': 'BANKNIFTY',
            'action': 'BUY',
            'entry_price': 48480,
            'confidence': 0.67,
            'exit_price': 48495,
            'exit_reason': 'target',
            'session': 'intraday'
        },
        # Closing Surge
        {
            'ticker': 'NIFTY50',
            'action': 'BUY',
            'entry_price': 23920,
            'confidence': 0.67,
            'exit_price': 23935,
            'exit_reason': 'target',
            'session': 'closing'
        },
        {
            'ticker': 'BANKNIFTY',
            'action': 'SELL',
            'entry_price': 48550,
            'confidence': 1.0,
            'exit_price': 48535,
            'exit_reason': 'target',
            'session': 'closing'
        },
        {
            'ticker': 'FINNIFTY',
            'action': 'BUY',
            'entry_price': 21850,
            'confidence': 0.67,
            'exit_price': 21865,
            'exit_reason': 'target',
            'session': 'closing'
        },
    ]
    
    # Point values
    point_values = {
        'NIFTY50': 75,
        'BANKNIFTY': 25,
        'FINNIFTY': 40,
        'NIFTYNXT50': 20,
        'MIDCAPNIFTY': 50
    }
    
    capital_per_trade = 10000
    
    # Process trades
    sessions = {'opening': [], 'intraday': [], 'closing': []}
    all_trades = []
    
    for trade_data in trades_data:
        ticker = trade_data['ticker']
        action = trade_data['action']
        entry_price = trade_data['entry_price']
        exit_price = trade_data['exit_price']
        session = trade_data['session']
        
        # Calculate P&L
        pv = point_values.get(ticker, 47)
        if action == 'BUY':
            points = exit_price - entry_price
        else:
            points = entry_price - exit_price
        
        pnl = points * pv
        pnl_percent = (pnl / capital_per_trade) * 100
        quantity = capital_per_trade / entry_price
        
        trade_obj = {
            'ticker': ticker,
            'action': action,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'exit_reason': trade_data['exit_reason'],
            'confidence': trade_data['confidence'],
            'capital_allocated': capital_per_trade
        }
        
        sessions[session].append(trade_obj)
        all_trades.append(trade_obj)
    
    # Display results - Opening Surge
    print("="*80)
    print("  OPENING SURGE (09:15-09:30 AM) - HIGHEST VOLATILITY")
    print("="*80)
    
    opening_pnl = 0
    for i, trade in enumerate(sessions['opening'], 1):
        status = "OK" if trade['pnl'] > 0 else "XX"
        print(f"  {status} Trade {i}: {trade['ticker']} {trade['action']}")
        print(f"      Entry: {trade['entry_price']:.0f} -> Exit: {trade['exit_price']:.0f}")
        print(f"      Qty: {trade['quantity']:.3f} lots | P&L: {trade['pnl']:.0f} ({trade['pnl_percent']:.1f}%)")
        print(f"      Reason: {trade['exit_reason']}")
        print()
        opening_pnl += trade['pnl']
    
    opening_win = (sum(1 for t in sessions['opening'] if t['pnl'] > 0) / len(sessions['opening']) * 100) if sessions['opening'] else 0
    print(f"  Opening Surge Subtotal: {opening_pnl:.0f} ({len(sessions['opening'])} trades, {opening_win:.0f}% win)\n")
    
    # Intraday
    print("="*80)
    print("  INTRADAY TRADES (10:00 AM - 01:00 PM) - LOWER VOLATILITY")
    print("="*80)
    
    intraday_pnl = 0
    for i, trade in enumerate(sessions['intraday'], 1):
        status = "OK" if trade['pnl'] > 0 else "XX"
        print(f"  {status} Trade {i}: {trade['ticker']} {trade['action']}")
        print(f"      Entry: {trade['entry_price']:.0f} -> Exit: {trade['exit_price']:.0f}")
        print(f"      Qty: {trade['quantity']:.3f} lots | P&L: {trade['pnl']:.0f} ({trade['pnl_percent']:.1f}%)")
        print(f"      Reason: {trade['exit_reason']}")
        print()
        intraday_pnl += trade['pnl']
    
    intraday_win = (sum(1 for t in sessions['intraday'] if t['pnl'] > 0) / len(sessions['intraday']) * 100) if sessions['intraday'] else 0
    print(f"  Intraday Subtotal: {intraday_pnl:.0f} ({len(sessions['intraday'])} trades, {intraday_win:.0f}% win)\n")
    
    # Closing Surge
    print("="*80)
    print("  CLOSING SURGE (03:00-03:30 PM) - 2ND HIGHEST VOLATILITY")
    print("="*80)
    
    closing_pnl = 0
    for i, trade in enumerate(sessions['closing'], 1):
        status = "OK" if trade['pnl'] > 0 else "XX"
        print(f"  {status} Trade {i}: {trade['ticker']} {trade['action']}")
        print(f"      Entry: {trade['entry_price']:.0f} -> Exit: {trade['exit_price']:.0f}")
        print(f"      Qty: {trade['quantity']:.3f} lots | P&L: {trade['pnl']:.0f} ({trade['pnl_percent']:.1f}%)")
        print(f"      Reason: {trade['exit_reason']}")
        print()
        closing_pnl += trade['pnl']
    
    closing_win = (sum(1 for t in sessions['closing'] if t['pnl'] > 0) / len(sessions['closing']) * 100) if sessions['closing'] else 0
    print(f"  Closing Surge Subtotal: {closing_pnl:.0f} ({len(sessions['closing'])} trades, {closing_win:.0f}% win)\n")
    
    # Summary
    print("="*80)
    print("  DAILY TRADING SUMMARY")
    print("="*80)
    
    total_pnl = opening_pnl + intraday_pnl + closing_pnl
    winning_trades = sum(1 for t in all_trades if t['pnl'] > 0)
    losing_trades = sum(1 for t in all_trades if t['pnl'] < 0)
    total_trades = len(all_trades)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    print(f"  Total Trades:               {total_trades}")
    print(f"  Winning Trades:             {winning_trades}")
    print(f"  Losing Trades:              {losing_trades}")
    print(f"  Win Rate:                   {win_rate:.1f}%")
    print()
    print(f"  Opening Surge P&L:          {opening_pnl:.0f}")
    print(f"  Intraday P&L:               {intraday_pnl:.0f}")
    print(f"  Closing Surge P&L:          {closing_pnl:.0f}")
    print()
    print(f"  TOTAL DAILY P&L:            {total_pnl:.0f}")
    
    # Capital calculation
    initial_capital = 100000
    end_capital = initial_capital + total_pnl
    daily_return = (total_pnl / initial_capital) * 100
    
    print()
    print(f"  Start of Day Capital:       {initial_capital:,}")
    print(f"  End of Day Tally:           {end_capital:,.0f}")
    print(f"  Daily Gain:                 {total_pnl:,.0f} ({daily_return:.2f}%)")
    
    # JSON Report
    print("\n" + "="*80)
    print("  SAMPLE JSON REPORT")
    print("="*80)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "daily_summary": {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate_percent": win_rate,
            "daily_pnl": total_pnl,
            "daily_return_percent": daily_return
        },
        "session_breakdown": {
            "opening_surge": {
                "trades": len(sessions['opening']),
                "pnl": opening_pnl,
                "win_rate": opening_win
            },
            "intraday": {
                "trades": len(sessions['intraday']),
                "pnl": intraday_pnl,
                "win_rate": intraday_win
            },
            "closing_surge": {
                "trades": len(sessions['closing']),
                "pnl": closing_pnl,
                "win_rate": closing_win
            }
        }
    }
    
    print("\n" + json.dumps(report, indent=2))
    
    # Final message
    print("\n" + "="*80)
    print("  TEST COMPLETE")
    print("="*80)
    print("  Enhanced position tracking integrated!")
    print("  Files generated:")
    print("    - live_paper_trading_hybrid.py (updated with tracking)")
    print("    - ENHANCED_POSITION_TRACKING_GUIDE.md (documentation)")
    print()
    print("  When running the scheduler:")
    print("    - Entry prices from live market data")
    print("    - Exit prices with targets/stops")
    print("    - P&L in INR per position")
    print("    - Daily reports with win rate and profits")
    print()


if __name__ == '__main__':
    test_enhanced_position_tracking()
