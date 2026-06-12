#!/usr/bin/env python3
"""
Live Paper Trading Monitor - Real-time P&L tracking and signal monitoring
Run in separate terminal for live dashboard updates
"""

import logging
import json
from datetime import datetime
import pytz
import time
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')

class PaperTradingMonitor:
    """Monitor paper trading session in real-time"""
    
    def __init__(self):
        self.log_file = 'logs/paper_trading_session.log'
        self.last_position = 0
        self.trades_seen = set()
        
    def get_latest_report(self):
        """Get latest trade report"""
        try:
            reports = list(Path('logs').glob('paper_trading_report_*.json'))
            if not reports:
                return None
            
            latest = max(reports, key=os.path.getctime)
            with open(latest, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def parse_log_file(self):
        """Parse log file for latest trades"""
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
            
            recent_lines = lines[self.last_position:]
            self.last_position = len(lines)
            
            return recent_lines
        except FileNotFoundError:
            return []
    
    def display_dashboard(self):
        """Display real-time trading dashboard"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        now = datetime.now(IST)
        report = self.get_latest_report()
        
        print("\n" + "╔" + "=" * 118 + "╗")
        print("║" + " " * 35 + "PAPER TRADING LIVE MONITOR" + " " * 57 + "║")
        print("║" + " " * 118 + "║")
        print(f"║ Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')} | Market: NSE/BSE (India)" + " " * 70 + "║")
        print("╚" + "=" * 118 + "╝\n")
        
        if not report:
            print("⏳ Waiting for trading session to start...\n")
            print("📝 Run: python paper_trading_session_today.py")
            print("📊 Reports will appear here once trades execute\n")
            return
        
        # Parse report
        initial_capital = report['initial_capital']
        remaining_capital = report['remaining_capital']
        utilized_capital = initial_capital - remaining_capital
        utilization_percent = report['utilization_percent']
        trades = report['trades']
        open_positions = report['open_positions']
        
        # Display Capital
        print("┌─ CAPITAL STATUS " + "─" * 101 + "┐")
        print(f"│ Initial Capital:        ₹{initial_capital:>15,.0f}                                                                    │")
        print(f"│ Utilized Capital:       ₹{utilized_capital:>15,.0f} ({utilization_percent:>5.1f}%)                                                         │")
        print(f"│ Available Capital:      ₹{remaining_capital:>15,.0f}                                                                    │")
        print("└" + "─" * 117 + "┘\n")
        
        # Display Open Positions
        print("┌─ OPEN POSITIONS " + "─" * 101 + "┐")
        if open_positions:
            for symbol, pos in open_positions.items():
                notional = pos['quantity'] * pos['entry_price']
                print(f"│ {symbol:<12} | Q: {pos['quantity']:>6} | Entry: ₹{pos['entry_price']:>10,.2f} | Notional: ₹{notional:>15,.0f}                     │")
            print(f"│ Total Open Positions: {len(open_positions):<80} │")
        else:
            print("│ No open positions currently                                                                                         │")
        print("└" + "─" * 117 + "┘\n")
        
        # Display Recent Trades
        print("┌─ RECENT TRADES " + "─" * 102 + "┐")
        if trades:
            # Show last 10 trades
            recent_trades = trades[-10:]
            print(f"│ {'Time':<20} | {'Symbol':<10} | {'Action':<5} | {'Price':<10} | {'Quantity':<8} | {'P&L':<12} | {'Status':<8} │")
            print("├" + "─" * 116 + "┤")
            
            for trade in recent_trades:
                ts = trade['timestamp'][-8:] if isinstance(trade['timestamp'], str) else datetime.fromtimestamp(trade['timestamp'], IST).strftime('%H:%M:%S')
                symbol = trade['symbol']
                action = trade['action']
                price = trade['price']
                quantity = trade['quantity']
                pnl = trade.get('pnl', 0)
                pnl_str = f"₹{pnl:,.0f}" if pnl else "-"
                
                status = "✅ WIN" if pnl and pnl > 0 else ("❌ LOSS" if pnl and pnl < 0 else "")
                
                print(f"│ {ts:<20} | {symbol:<10} | {action:<5} | ₹{price:<9,.2f} | {quantity:>7} | {pnl_str:>11} | {status:<8} │")
            
            print(f"│ Total Trades Executed: {len(trades):<79} │")
            
            # Calculate stats
            completed_trades = [t for t in trades if t['action'] == 'SELL']
            if completed_trades:
                wins = sum(1 for t in completed_trades if t.get('pnl', 0) > 0)
                losses = sum(1 for t in completed_trades if t.get('pnl', 0) < 0)
                win_rate = (wins / len(completed_trades)) * 100 if completed_trades else 0
                total_pnl = sum(t.get('pnl', 0) for t in completed_trades)
                
                print("├" + "─" * 116 + "┤")
                print(f"│ Completed Trades: {len(completed_trades)} | Wins: {wins} | Losses: {losses} | Win Rate: {win_rate:.1f}% | Total P&L: ₹{total_pnl:,.0f}        │")
        else:
            print("│ No trades executed yet                                                                                              │")
        print("└" + "─" * 117 + "┘\n")
        
        # Display Statistics
        if trades:
            buy_trades = [t for t in trades if t['action'] == 'BUY']
            sell_trades = [t for t in trades if t['action'] == 'SELL']
            
            print("┌─ SESSION STATISTICS " + "─" * 96 + "┐")
            print(f"│ Total Trades:           {len(trades):<8} | Buys: {len(buy_trades):<6} | Sells: {len(sell_trades):<6}                                               │")
            
            if sell_trades:
                avg_confidence = sum(t.get('confidence', 0) for t in trades) / len(trades)
                print(f"│ Avg Confidence:         {avg_confidence:<8.2f}                                                                                │")
            
            print("└" + "─" * 117 + "┘\n")
        
        # Display Navigation
        print("┌─ COMMANDS " + "─" * 106 + "┐")
        print("│ r: Refresh | l: Show logs | s: Summary | q: Quit | Report: logs/paper_trading_report_*.json             │")
        print("└" + "─" * 117 + "┘\n")
    
    def show_logs(self):
        """Show latest log entries"""
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
            
            # Show last 30 lines
            recent = lines[-30:]
            
            os.system('clear' if os.name == 'posix' else 'cls')
            print("\n" + "═" * 120)
            print("LATEST LOG ENTRIES (Last 30 lines)")
            print("═" * 120 + "\n")
            
            for line in recent:
                print(line.rstrip())
            
            print("\n" + "═" * 120)
            print("Press Enter to return to dashboard...")
            input()
            
        except FileNotFoundError:
            print("❌ Log file not found. Start trading session first!")
            input("Press Enter to continue...")
    
    def show_summary(self):
        """Show trading summary"""
        report = self.get_latest_report()
        
        os.system('clear' if os.name == 'posix' else 'cls')
        print("\n" + "═" * 120)
        print("PAPER TRADING SUMMARY")
        print("═" * 120 + "\n")
        
        if not report:
            print("❌ No trading session data available yet!")
            input("Press Enter to continue...")
            return
        
        print(json.dumps(report, indent=2, default=str))
        print("\n" + "═" * 120)
        print("Press Enter to return to dashboard...")
        input()
    
    def run(self):
        """Main monitor loop"""
        try:
            while True:
                self.display_dashboard()
                
                # Get user input with timeout
                print("Press 'r' to refresh, 'l' for logs, 's' for summary, 'q' to quit: ", end='', flush=True)
                
                # Use input with default to refresh
                try:
                    choice = input().lower() or 'r'
                except:
                    choice = 'r'
                
                if choice == 'q':
                    print("\n✅ Monitor closed")
                    break
                elif choice == 'l':
                    self.show_logs()
                elif choice == 's':
                    self.show_summary()
                elif choice == 'r':
                    time.sleep(1)  # Brief delay before refresh
                    continue
                else:
                    time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n✅ Monitor interrupted")
            sys.exit(0)


def main():
    monitor = PaperTradingMonitor()
    monitor.run()


if __name__ == '__main__':
    main()
