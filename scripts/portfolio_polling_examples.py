#!/usr/bin/env python3
"""
Portfolio Polling Integration Examples
Shows how to use the portfolio polling service
"""

import time
import logging
from app.services.breeze_api import BreezeAPIService
from app.services.live_position_tracker import LivePositionTracker
from app.services.portfolio_poller import PortfolioPoller, PortfolioUpdateEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Example 1: Basic Portfolio Polling
def example_basic_polling():
    """Start polling and get portfolio updates"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Portfolio Polling")
    print("="*60)
    
    # Initialize services
    breeze_api = BreezeAPIService()
    breeze_api.authenticate()
    
    poller = PortfolioPoller(breeze_api, poll_interval=5)
    
    # Start polling
    poller.start_polling()
    
    # Let it run for 30 seconds
    print("Polling for 30 seconds...")
    for i in range(6):
        time.sleep(5)
        
        holdings = poller.get_holdings()
        positions = poller.get_positions()
        pnl = poller.get_pnl()
        
        print(f"\n--- Update {i+1} ---")
        print(f"Holdings: {len(holdings)} holdings")
        print(f"Positions: {len(positions)} positions")
        print(f"Portfolio P&L: Rs {pnl.get('total_pnl', 0):.2f} ({pnl.get('pnl_percentage', 0):.2f}%)")
    
    # Stop polling
    poller.stop_polling_thread()
    print("\nPolling stopped")


# Example 2: Event-Driven Updates
def example_event_callbacks():
    """Use callbacks to respond to portfolio changes"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Event-Driven Portfolio Monitoring")
    print("="*60)
    
    breeze_api = BreezeAPIService()
    breeze_api.authenticate()
    
    poller = PortfolioPoller(breeze_api, poll_interval=5)
    
    # Register event callbacks
    def on_position_opened(data):
        symbol = data.get('symbol')
        print(f"🟢 NEW POSITION OPENED: {symbol}")
    
    def on_position_closed(data):
        symbol = data.get('symbol')
        print(f"🔴 POSITION CLOSED: {symbol}")
    
    def on_pnl_change(data):
        symbol = data.get('symbol')
        pnl = data.get('new_pnl', 0)
        print(f"💹 P&L Update: {symbol} - Rs {pnl:.2f}")
    
    def on_holdings_change(data):
        symbol = data.get('symbol')
        action = data.get('action')
        print(f"📊 Holding {action}: {symbol}")
    
    def on_error(data):
        error = data.get('error')
        print(f"❌ Error: {error}")
    
    # Register callbacks
    poller.register_callback(PortfolioUpdateEvent.POSITION_OPENED, on_position_opened)
    poller.register_callback(PortfolioUpdateEvent.POSITION_CLOSED, on_position_closed)
    poller.register_callback(PortfolioUpdateEvent.PNL_UPDATED, on_pnl_change)
    poller.register_callback(PortfolioUpdateEvent.HOLDINGS_UPDATED, on_holdings_change)
    poller.register_callback(PortfolioUpdateEvent.ERROR, on_error)
    
    # Start polling
    poller.start_polling()
    print("Polling with event callbacks started...")
    
    # Run for 2 minutes
    print("Running for 2 minutes...")
    time.sleep(120)
    
    # Stop polling
    poller.stop_polling_thread()
    print("Polling stopped")


# Example 3: Integration with Signal Executor
def example_with_signal_executor():
    """Use portfolio polling with trading signals"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Portfolio Polling with Signal Executor")
    print("="*60)
    
    breeze_api = BreezeAPIService()
    breeze_api.authenticate()
    
    position_tracker = LivePositionTracker(breeze_api)
    poller = PortfolioPoller(breeze_api, position_tracker, poll_interval=5)
    
    def on_position_opened(data):
        """Handle new position - update signal tracking"""
        symbol = data.get('symbol')
        position = data.get('position', {})
        
        print(f"\n✨ New position: {symbol}")
        print(f"   Quantity: {position.get('quantity', 0)}")
        print(f"   Entry Price: Rs {position.get('entry_price', 0):.2f}")
        
        # Update signal tracking
        if position_tracker:
            position_tracker.track_position(symbol, position)
    
    def on_position_closed(data):
        """Handle closed position - calculate realized P&L"""
        symbol = data.get('symbol')
        
        print(f"\n🏁 Position closed: {symbol}")
        
        # Calculate realized P&L
        if position_tracker:
            pnl_data = position_tracker.get_position_pnl(symbol)
            if pnl_data:
                print(f"   Realized P&L: Rs {pnl_data.get('realized_pnl', 0):.2f}")
    
    # Register callbacks
    poller.register_callback(PortfolioUpdateEvent.POSITION_OPENED, on_position_opened)
    poller.register_callback(PortfolioUpdateEvent.POSITION_CLOSED, on_position_closed)
    
    # Start polling
    poller.start_polling()
    print("Portfolio polling with signal executor started...")
    
    # Display portfolio status every 10 seconds
    for i in range(12):
        time.sleep(10)
        
        status = poller.get_status()
        pnl = poller.get_pnl()
        
        print(f"\n[{i+1}0s] Portfolio Status:")
        print(f"  • Polls: {status['poll_count']}")
        print(f"  • Holdings: {status['holdings_count']}")
        print(f"  • Positions: {status['positions_count']}")
        print(f"  • Total P&L: Rs {pnl.get('total_pnl', 0):.2f}")
    
    # Stop polling
    poller.stop_polling_thread()
    print("\nPolling stopped")


# Example 4: Continuous Monitoring Dashboard
def example_monitoring_dashboard():
    """Create a simple monitoring dashboard"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Portfolio Monitoring Dashboard")
    print("="*60)
    
    breeze_api = BreezeAPIService()
    breeze_api.authenticate()
    
    poller = PortfolioPoller(breeze_api, poll_interval=3)
    
    # Start polling
    poller.start_polling()
    
    # Display dashboard for 1 minute
    print("Portfolio Dashboard (updating every 3 seconds):\n")
    
    for i in range(20):
        time.sleep(3)
        
        holdings = poller.get_holdings()
        positions = poller.get_positions()
        pnl = poller.get_pnl()
        margin = poller.get_margin()
        status = poller.get_status()
        
        # Clear screen (simple version)
        print("\n" + "="*60)
        print(f"Portfolio Dashboard - Update #{status['poll_count']}")
        print("="*60)
        
        # P&L Summary
        print("\n📊 P&L Summary:")
        print(f"   Total P&L:     Rs {pnl.get('total_pnl', 0):>10.2f}")
        print(f"   P&L %:         {pnl.get('pnl_percentage', 0):>10.2f}%")
        
        # Holdings
        if holdings:
            print(f"\n📈 Holdings ({len(holdings)} total):")
            for symbol, holding in list(holdings.items())[:5]:
                qty = holding.get('quantity', 0)
                val = holding.get('value', 0)
                h_pnl = holding.get('pnl', 0)
                print(f"   {symbol:10} | Qty: {qty:>6.0f} | Val: Rs {val:>10.2f} | P&L: {h_pnl:>8.2f}")
        
        # Positions
        if positions:
            print(f"\n💰 Open Positions ({len(positions)} total):")
            for symbol, position in list(positions.items())[:5]:
                qty = position.get('quantity', 0)
                entry = position.get('entry_price', 0)
                current = position.get('current_price', 0)
                pos_pnl = position.get('pnl', 0)
                print(f"   {symbol:10} | Entry: Rs {entry:>8.2f} | Current: Rs {current:>8.2f} | P&L: {pos_pnl:>8.2f}")
        
        # Margin
        print(f"\n💳 Margin:")
        print(f"   Available:    Rs {margin.get('available_margin', 0):>10.2f}")
        print(f"   Utilized:     Rs {margin.get('utilized_margin', 0):>10.2f}")
        print(f"   Balance:      Rs {margin.get('balance', 0):>10.2f}")
        
        # Status
        print(f"\n⚙️ Status:")
        print(f"   Last Poll:    {status.get('last_poll_time', 'Never')}")
        print(f"   Errors:       {status['error_count']}")
    
    poller.stop_polling_thread()
    print("\n\nDashboard closed")


# Example 5: Alert on P&L Thresholds
def example_pnl_alerts():
    """Generate alerts when P&L crosses thresholds"""
    print("\n" + "="*60)
    print("EXAMPLE 5: P&L Threshold Alerts")
    print("="*60)
    
    breeze_api = BreezeAPIService()
    breeze_api.authenticate()
    
    poller = PortfolioPoller(breeze_api, poll_interval=5)
    
    # Configuration
    daily_loss_limit = -5000  # Alert if daily loss > Rs 5000
    daily_profit_target = 10000  # Alert if daily profit > Rs 10000
    
    alerts_sent = {'loss': False, 'profit': False}
    
    def on_pnl_update(data):
        """Check P&L and send alerts if needed"""
        pnl = data.get('total_pnl', 0)
        
        # Check loss alert
        if pnl < daily_loss_limit and not alerts_sent['loss']:
            print(f"\n🚨 ALERT: Daily loss limit exceeded!")
            print(f"   Current P&L: Rs {pnl:.2f}")
            print(f"   Limit: Rs {daily_loss_limit:.2f}")
            alerts_sent['loss'] = True
        
        # Check profit alert
        if pnl > daily_profit_target and not alerts_sent['profit']:
            print(f"\n✨ ALERT: Daily profit target achieved!")
            print(f"   Current P&L: Rs {pnl:.2f}")
            print(f"   Target: Rs {daily_profit_target:.2f}")
            alerts_sent['profit'] = True
        
        # Reset at end of day (simple version)
        if pnl > daily_profit_target:
            alerts_sent['loss'] = False  # Can incur loss after profit
    
    # Register callback
    poller.register_callback(PortfolioUpdateEvent.PNL_UPDATED, on_pnl_update)
    
    # Start polling
    poller.start_polling()
    print("P&L monitoring started (looking for limits)...")
    print(f"Loss limit: Rs {daily_loss_limit:.2f}")
    print(f"Profit target: Rs {daily_profit_target:.2f}")
    
    # Run for 2 minutes
    time.sleep(120)
    
    poller.stop_polling_thread()
    print("P&L monitoring stopped")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        
        if example_num == "1":
            example_basic_polling()
        elif example_num == "2":
            example_event_callbacks()
        elif example_num == "3":
            example_with_signal_executor()
        elif example_num == "4":
            example_monitoring_dashboard()
        elif example_num == "5":
            example_pnl_alerts()
        else:
            print("Usage: python portfolio_polling_examples.py <example_number>")
            print("  1: Basic portfolio polling")
            print("  2: Event-driven updates")
            print("  3: Integration with signal executor")
            print("  4: Monitoring dashboard")
            print("  5: P&L threshold alerts")
    else:
        print("Portfolio Polling Examples")
        print("Usage: python portfolio_polling_examples.py <example_number>")
        print("\nAvailable examples:")
        print("  1: Basic portfolio polling")
        print("  2: Event-driven updates")
        print("  3: Integration with signal executor")
        print("  4: Monitoring dashboard")
        print("  5: P&L threshold alerts")
