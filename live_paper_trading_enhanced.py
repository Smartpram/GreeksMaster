"""
Enhanced Live Paper Trading with Full Position Tracking & Price Simulation
Tracks:
- Entry prices & signals
- Current market prices
- Position sizes & PnL
- Exit prices & reasons
- Realistic profit/loss scenarios

This simulates actual trading as if ₹10,000 was allocated per trade
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# ML Libraries
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Breeze API
sys.path.insert(0, str(Path(__file__).parent))
from app.services.breeze_api import BreezeAPIService

# Load environment
load_dotenv()

# Setup logging & directories
LOG_DIR = Path(__file__).parent / "logs" / "live_trading"
LOG_DIR.mkdir(parents=True, exist_ok=True)

REPORT_DIR = Path(__file__).parent / "reports" / "live_trading"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

POSITION_DIR = Path(__file__).parent / "reports" / "positions"
POSITION_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
log_file = LOG_DIR / f"enhanced_paper_trading_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Position:
    """Represents an open or closed trading position"""
    
    def __init__(self, ticker, action, entry_price, quantity, entry_time, capital_allocated=10000):
        self.ticker = ticker
        self.action = action  # 'BUY' or 'SELL'
        self.entry_price = entry_price
        self.quantity = quantity
        self.entry_time = entry_time
        self.capital_allocated = capital_allocated
        
        # Exit info
        self.exit_price = None
        self.exit_time = None
        self.exit_reason = None  # 'target', 'stop_loss', 'timeout', 'manual'
        
        # P&L tracking
        self.pnl = None
        self.pnl_percent = None
        self.is_closed = False
        
        # Price points history
        self.high_price = entry_price
        self.low_price = entry_price
    
    def update_price(self, current_price):
        """Track highest and lowest prices during position"""
        self.high_price = max(self.high_price, current_price)
        self.low_price = min(self.low_price, current_price)
    
    def close_position(self, exit_price, exit_time, exit_reason='manual'):
        """Close the position and calculate P&L"""
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.exit_reason = exit_reason
        self.is_closed = True
        
        # Calculate P&L based on action
        if self.action == 'BUY':
            points_profit = exit_price - self.entry_price
        else:  # SELL
            points_profit = self.entry_price - exit_price
        
        # Convert points to INR (varies by ticker)
        point_values = {
            'NIFTY50': 75,
            'BANKNIFTY': 25,
            'FINNIFTY': 40,
            'NIFTYNXT50': 20,
            'MIDCAPNIFTY': 50
        }
        point_value = point_values.get(self.ticker, 47)  # Default average
        
        self.pnl = points_profit * point_value
        self.pnl_percent = (self.pnl / self.capital_allocated) * 100
    
    def get_current_pnl(self, current_price):
        """Calculate unrealized P&L at current price"""
        if self.is_closed:
            return self.pnl
        
        if self.action == 'BUY':
            points = current_price - self.entry_price
        else:
            points = self.entry_price - current_price
        
        point_values = {
            'NIFTY50': 75,
            'BANKNIFTY': 25,
            'FINNIFTY': 40,
            'NIFTYNXT50': 20,
            'MIDCAPNIFTY': 50
        }
        point_value = point_values.get(self.ticker, 47)
        
        return points * point_value
    
    def to_dict(self):
        """Convert to dictionary for reporting"""
        return {
            'ticker': self.ticker,
            'action': self.action,
            'entry_price': self.entry_price,
            'entry_time': str(self.entry_time),
            'exit_price': self.exit_price,
            'exit_time': str(self.exit_time) if self.exit_time else None,
            'exit_reason': self.exit_reason,
            'quantity': self.quantity,
            'capital_allocated': self.capital_allocated,
            'pnl': self.pnl,
            'pnl_percent': self.pnl_percent,
            'is_closed': self.is_closed,
            'high_price': self.high_price,
            'low_price': self.low_price,
            'duration_minutes': (self.exit_time - self.entry_time).total_seconds() / 60 if self.exit_time else None
        }


class AdvancedPaperTradingExecutor:
    """Enhanced executor that tracks positions and simulates realistic trading"""
    
    def __init__(self, capital_per_trade=10000):
        self.logger = logging.getLogger(__name__)
        self.capital_per_trade = capital_per_trade  # ₹10,000 per trade
        
        self.open_positions = {}  # {ticker: [positions]}
        self.closed_positions = []
        self.daily_pnl = 0
        self.total_trades = 0
    
    def execute_trade(self, ticker, signal, current_price, models=None):
        """
        Execute a paper trade with realistic position tracking
        
        Args:
            ticker: Stock/index name
            signal: {'action': 'BUY'/'SELL', 'confidence': 0.67}
            current_price: Current market price of the ticker
            models: ML models (to validate signal quality)
        """
        try:
            if signal is None or current_price is None:
                return None
            
            action = signal['action']
            confidence = signal['confidence']
            
            # Quantity based on capital and current price
            quantity = self.capital_per_trade / current_price
            
            # Create position
            position = Position(
                ticker=ticker,
                action=action,
                entry_price=current_price,
                quantity=quantity,
                entry_time=datetime.now(),
                capital_allocated=self.capital_per_trade
            )
            
            # Track position
            if ticker not in self.open_positions:
                self.open_positions[ticker] = []
            self.open_positions[ticker].append(position)
            
            self.total_trades += 1
            self.logger.info(f"[POSITION] {ticker} {action} @ ₹{current_price:.2f} | Qty: {quantity:.2f} | Confidence: {confidence:.1%}")
            
            return position
        
        except Exception as e:
            self.logger.error(f"[EXECUTION ERROR] {str(e)}")
            return None
    
    def simulate_position_exit(self, ticker, position, target_points=15, stop_loss_points=10, timeout_minutes=30):
        """
        Simulate position exit based on targets, stops, or timeout
        
        Args:
            ticker: Stock/index name
            position: Position object
            target_points: Points to close with profit (e.g., 15 points)
            stop_loss_points: Points for stop-loss (e.g., 10 points)
            timeout_minutes: Close if not exited in N minutes
        """
        if position.is_closed:
            return position
        
        try:
            # Simulate next candle price movement (±random within ATR)
            # For paper trading, use random walk within reasonable bounds
            price_move = np.random.normal(0, target_points * 0.3)  # Random walk
            
            if position.action == 'BUY':
                exit_price = position.entry_price + price_move
                
                # Check targets
                if exit_price >= position.entry_price + target_points:
                    position.close_position(position.entry_price + target_points, datetime.now(), 'target')
                    self.logger.info(f"[EXIT] {ticker} CLOSED (Target Hit): ₹{position.exit_price:.2f} | PnL: ₹{position.pnl:.0f}")
                
                # Check stop loss
                elif exit_price <= position.entry_price - stop_loss_points:
                    position.close_position(position.entry_price - stop_loss_points, datetime.now(), 'stop_loss')
                    self.logger.info(f"[EXIT] {ticker} CLOSED (Stop Loss): ₹{position.exit_price:.2f} | PnL: ₹{position.pnl:.0f}")
                
                # Check timeout
                elif (datetime.now() - position.entry_time).total_seconds() / 60 >= timeout_minutes:
                    position.close_position(exit_price, datetime.now(), 'timeout')
                    self.logger.info(f"[EXIT] {ticker} CLOSED (Timeout): ₹{position.exit_price:.2f} | PnL: ₹{position.pnl:.0f}")
            
            else:  # SELL
                exit_price = position.entry_price - price_move
                
                # Check targets
                if exit_price <= position.entry_price - target_points:
                    position.close_position(position.entry_price - target_points, datetime.now(), 'target')
                    self.logger.info(f"[EXIT] {ticker} CLOSED (Target Hit): ₹{position.exit_price:.2f} | PnL: ₹{position.pnl:.0f}")
                
                # Check stop loss
                elif exit_price >= position.entry_price + stop_loss_points:
                    position.close_position(position.entry_price + stop_loss_points, datetime.now(), 'stop_loss')
                    self.logger.info(f"[EXIT] {ticker} CLOSED (Stop Loss): ₹{position.exit_price:.2f} | PnL: ₹{position.pnl:.0f}")
                
                # Check timeout
                elif (datetime.now() - position.entry_time).total_seconds() / 60 >= timeout_minutes:
                    position.close_position(exit_price, datetime.now(), 'timeout')
                    self.logger.info(f"[EXIT] {ticker} CLOSED (Timeout): ₹{position.exit_price:.2f} | PnL: ₹{position.pnl:.0f}")
            
            # Move to closed if necessary
            if position.is_closed:
                self.open_positions[ticker].remove(position)
                self.closed_positions.append(position)
                self.daily_pnl += position.pnl
        
        except Exception as e:
            self.logger.error(f"[EXIT SIMULATION ERROR] {str(e)}")
        
        return position
    
    def get_portfolio_summary(self):
        """Generate portfolio summary"""
        open_count = sum(len(pos_list) for pos_list in self.open_positions.values())
        closed_count = len(self.closed_positions)
        
        closed_wins = sum(1 for p in self.closed_positions if p.pnl > 0)
        closed_losses = sum(1 for p in self.closed_positions if p.pnl < 0)
        win_rate = (closed_wins / closed_count * 100) if closed_count > 0 else 0
        
        total_pnl = sum(p.pnl for p in self.closed_positions)
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'open_positions': open_count,
            'closed_positions': closed_count,
            'total_trades': self.total_trades,
            'winning_trades': closed_wins,
            'losing_trades': closed_losses,
            'win_rate_percent': win_rate,
            'daily_pnl': total_pnl,
            'closed_positions_detail': [p.to_dict() for p in self.closed_positions],
            'open_positions_detail': [p.to_dict() for pos_list in self.open_positions.values() for p in pos_list]
        }
        
        return summary


class EnhancedReportGenerator:
    """Generate comprehensive trading reports with position details"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_position_report(self, executor, date_str=None):
        """Generate detailed position and P&L report"""
        try:
            if date_str is None:
                date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            summary = executor.get_portfolio_summary()
            
            report_file = POSITION_DIR / f"positions_{date_str}.json"
            with open(report_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            self.logger.info(f"[REPORT] Position report saved: {report_file.name}")
            
            # Also print summary
            self.logger.info("\n" + "="*70)
            self.logger.info("DAILY TRADING SUMMARY")
            self.logger.info("="*70)
            self.logger.info(f"Total Trades: {summary['total_trades']}")
            self.logger.info(f"Winning Trades: {summary['winning_trades']}")
            self.logger.info(f"Losing Trades: {summary['losing_trades']}")
            self.logger.info(f"Win Rate: {summary['win_rate_percent']:.1f}%")
            self.logger.info(f"Daily P&L: ₹{summary['daily_pnl']:.0f}")
            self.logger.info("="*70 + "\n")
            
            # Detailed breakdown
            self.logger.info("Closed Positions:")
            for pos in summary['closed_positions_detail']:
                self.logger.info(f"  {pos['ticker']} {pos['action']}: Entry ₹{pos['entry_price']:.2f} → Exit ₹{pos['exit_price']:.2f} | PnL: ₹{pos['pnl']:.0f} ({pos['pnl_percent']:.1f}%) [{pos['exit_reason']}]")
            
            return report_file
        
        except Exception as e:
            self.logger.error(f"[REPORT ERROR] {str(e)}")
            return None


# ============================================================================
# Example Usage & Testing
# ============================================================================

def test_position_tracking():
    """Test the enhanced position tracking system"""
    logger.info("\n" + "="*80)
    logger.info("ENHANCED PAPER TRADING - POSITION TRACKING TEST")
    logger.info("="*80 + "\n")
    
    # Initialize executor
    executor = AdvancedPaperTradingExecutor(capital_per_trade=10000)
    report_gen = EnhancedReportGenerator()
    
    # Simulate some trades
    test_trades = [
        {'ticker': 'NIFTY50', 'action': 'BUY', 'entry_price': 23850, 'confidence': 0.67},
        {'ticker': 'BANKNIFTY', 'action': 'SELL', 'entry_price': 48500, 'confidence': 1.0},
        {'ticker': 'FINNIFTY', 'action': 'BUY', 'entry_price': 21800, 'confidence': 0.67},
        {'ticker': 'NIFTY50', 'action': 'SELL', 'entry_price': 23860, 'confidence': 0.67},
        {'ticker': 'BANKNIFTY', 'action': 'BUY', 'entry_price': 48480, 'confidence': 0.67},
    ]
    
    # Execute trades
    positions = []
    for trade in test_trades:
        signal = {'action': trade['action'], 'confidence': trade['confidence']}
        pos = executor.execute_trade(trade['ticker'], signal, trade['entry_price'])
        if pos:
            positions.append(pos)
    
    logger.info(f"\n✓ Opened {len(positions)} positions\n")
    
    # Simulate exits
    for pos in positions:
        executor.simulate_position_exit(pos.ticker, pos, target_points=15, stop_loss_points=10)
    
    # Generate report
    report_gen.generate_position_report(executor)
    
    logger.info("\n✓ Position tracking test completed!")


if __name__ == '__main__':
    test_position_tracking()
