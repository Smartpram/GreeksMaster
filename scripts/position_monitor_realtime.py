"""
Real-Time Position Monitor
Monitors open positions every minute and exits based on profit/loss thresholds
Status: Production ready
"""

import os
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


class RealTimePositionMonitor:
    """
    Monitors open positions in real-time (every minute)
    - Tracks P&L every minute
    - Exits on stop-loss (avoid catastrophic loss)
    - Exits on profit targets (lock in gains)
    - Applies trailing stops to protect gains
    """
    
    def __init__(self, breeze_client, brokerage_fees):
        self.breeze = breeze_client
        self.fees = brokerage_fees
        
        # Open positions tracking
        # Structure: {ticker_side_timestamp: {position details}}
        self.open_positions = {}
        
        # Risk parameters (can be tuned)
        self.hard_stop_loss = -1.5  # -1.5% = immediate exit (catastrophic loss)
        self.profit_target = 0.8    # +0.8% = take profit
        self.trailing_stop = 0.4    # Trail stop at -0.4% (lock profits)
        
        # Monitoring
        self.monitor_interval = 60  # Check every 60 seconds (1 minute)
        self.log_dir = "logs/position_monitor"
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.log_file = os.path.join(
            self.log_dir,
            f"position_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
    
    def _log(self, message: str, level: str = "INFO"):
        """Log message"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_message = f"[{timestamp}] [{level}] {message}"
        
        print(log_message)
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_message + "\n")
        except Exception as e:
            print(f"[ERROR] Failed to write log: {e}")
    
    def open_position(self, ticker: str, direction: str, quantity: int, 
                     entry_price: float, entry_fee: float) -> str:
        """
        Register a new open position
        
        Args:
            ticker: Stock ticker
            direction: "BUY" or "SELL"
            quantity: Number of shares
            entry_price: Entry price per share
            entry_fee: Brokerage fee paid at entry
        
        Returns:
            Position ID (for tracking)
        """
        position_id = f"{ticker}_{direction}_{datetime.now().strftime('%H%M%S%f')[:-3]}"
        
        self.open_positions[position_id] = {
            'ticker': ticker,
            'direction': direction,
            'quantity': quantity,
            'entry_price': entry_price,
            'entry_fee': entry_fee,
            'entry_time': datetime.now(),
            'peak_price': entry_price,  # For trailing stop
            'low_price': entry_price,   # For stop loss tracking
            'minutes_held': 0,
            'status': 'OPEN',
            'exit_reason': None,
            'exit_price': None,
            'exit_fee': None,
            'exit_time': None,
            'gross_pnl': None,
            'net_pnl': None,
            'pnl_percent': None
        }
        
        self._log(f"OPEN: {ticker} {direction} x{quantity} @ ₹{entry_price:.2f} (ID: {position_id})")
        return position_id
    
    def check_and_update_positions(self) -> List[Dict]:
        """
        Check all open positions and update P&L
        Should be called every minute during market hours
        
        Returns:
            List of closed positions (if any)
        """
        closed_positions = []
        current_time = datetime.now()
        
        # Update each position
        for position_id, position in list(self.open_positions.items()):
            if position['status'] != 'OPEN':
                continue
            
            try:
                # Fetch current price
                current_price = self._fetch_current_price(position['ticker'])
                if current_price is None:
                    continue
                
                # Update tracking
                if position['direction'] == 'BUY':
                    position['peak_price'] = max(position['peak_price'], current_price)
                    position['low_price'] = min(position['low_price'], current_price)
                else:  # SELL
                    position['peak_price'] = min(position['peak_price'], current_price)
                    position['low_price'] = max(position['low_price'], current_price)
                
                # Calculate current P&L
                pnl_percent = self._calculate_pnl_percent(position, current_price)
                position['minutes_held'] += 1
                
                # Check exit conditions
                exit_signal = self._check_exit_conditions(position, current_price, pnl_percent)
                
                if exit_signal:
                    # Exit the position
                    closed = self._close_position(
                        position_id, current_price, pnl_percent, exit_signal
                    )
                    closed_positions.append(closed)
            
            except Exception as e:
                self._log(f"ERROR updating {position_id}: {e}", level="ERROR")
        
        return closed_positions
    
    def _fetch_current_price(self, ticker: str) -> Optional[float]:
        """Fetch current price for ticker"""
        try:
            # Get latest 1-minute candle
            candles = self.breeze.get_historical_data(
                stock_code=ticker,
                exchange_code="NSE",
                interval="1minute",
                from_date=datetime.now() - timedelta(minutes=2),
                to_date=datetime.now(),
                paginate=False
            )
            
            if candles and len(candles) > 0:
                return float(candles[-1]['close'])
            return None
        
        except Exception as e:
            self._log(f"Error fetching price for {ticker}: {e}", level="WARN")
            return None
    
    def _calculate_pnl_percent(self, position: Dict, current_price: float) -> float:
        """Calculate current P&L percentage"""
        if position['direction'] == 'BUY':
            pnl_percent = ((current_price - position['entry_price']) / position['entry_price']) * 100
        else:  # SELL
            pnl_percent = ((position['entry_price'] - current_price) / position['entry_price']) * 100
        
        return pnl_percent
    
    def _check_exit_conditions(self, position: Dict, current_price: float, 
                               pnl_percent: float) -> Optional[str]:
        """
        Check if position should be exited
        
        Returns:
            Exit reason if should exit, None otherwise
        """
        
        # 1. HARD STOP LOSS - Exit immediately on catastrophic loss
        if pnl_percent <= self.hard_stop_loss:
            return f"HARD_STOP_LOSS ({pnl_percent:.2f}%)"
        
        # 2. PROFIT TARGET - Lock in gains at target
        if pnl_percent >= self.profit_target:
            return f"PROFIT_TARGET ({pnl_percent:.2f}%)"
        
        # 3. TRAILING STOP - Protect gains if price turns negative after profit
        # Only activate if we had a gain at some point
        peak_pnl_percent = self._calculate_pnl_percent(position, position['peak_price'])
        
        if peak_pnl_percent > 0 and pnl_percent <= (peak_pnl_percent - self.trailing_stop):
            # We had profit, now we're down by trailing stop amount
            return f"TRAILING_STOP (peak: {peak_pnl_percent:.2f}%, current: {pnl_percent:.2f}%)"
        
        # 4. TIME-BASED EXIT - If held too long without profit (risk management)
        if position['minutes_held'] >= 30:  # 30 minutes
            if pnl_percent < 0:  # Still in loss after 30 mins
                return f"TIME_STOP_LOSS ({position['minutes_held']}m, {pnl_percent:.2f}%)"
        
        # 5. EXTREME TIME EXIT - Exit if held over 45 minutes (full cycle recovery)
        if position['minutes_held'] >= 45:
            return f"EXTREME_TIME_EXIT ({position['minutes_held']}m)"
        
        return None
    
    def _close_position(self, position_id: str, exit_price: float, 
                       pnl_percent: float, exit_reason: str) -> Dict:
        """Close a position and return trade record"""
        position = self.open_positions[position_id]
        
        # Calculate actual P&L
        gross_pnl = (exit_price - position['entry_price']) * position['quantity'] \
                   if position['direction'] == 'BUY' else \
                   (position['entry_price'] - exit_price) * position['quantity']
        
        exit_fee = self.fees.calculate_brokerage(
            exit_price * position['quantity'], "NSE"
        )
        
        net_pnl = gross_pnl - position['entry_fee'] - exit_fee
        
        # Update position record
        position['status'] = 'CLOSED'
        position['exit_reason'] = exit_reason
        position['exit_price'] = exit_price
        position['exit_fee'] = exit_fee
        position['exit_time'] = datetime.now()
        position['gross_pnl'] = gross_pnl
        position['net_pnl'] = net_pnl
        position['pnl_percent'] = pnl_percent
        
        # Log exit
        self._log(
            f"CLOSE: {position['ticker']} {position['direction']} after "
            f"{position['minutes_held']}m | Exit: {exit_reason} | "
            f"P&L: ₹{net_pnl:.2f} ({pnl_percent:.2f}%)"
        )
        
        return {
            'position_id': position_id,
            'ticker': position['ticker'],
            'direction': position['direction'],
            'quantity': position['quantity'],
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'entry_time': position['entry_time'],
            'exit_time': position['exit_time'],
            'duration_minutes': position['minutes_held'],
            'gross_pnl': gross_pnl,
            'fees': position['entry_fee'] + exit_fee,
            'net_pnl': net_pnl,
            'pnl_percent': pnl_percent,
            'exit_reason': exit_reason
        }
    
    def get_open_positions_summary(self) -> Dict:
        """Get summary of all open positions"""
        open_positions = {
            pos_id: pos for pos_id, pos in self.open_positions.items() 
            if pos['status'] == 'OPEN'
        }
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_open': len(open_positions),
            'positions': []
        }
        
        total_gross_pnl = 0
        for pos_id, pos in open_positions.items():
            current_price = self._fetch_current_price(pos['ticker'])
            if current_price:
                pnl_percent = self._calculate_pnl_percent(pos, current_price)
                gross_pnl = (current_price - pos['entry_price']) * pos['quantity'] \
                           if pos['direction'] == 'BUY' else \
                           (pos['entry_price'] - current_price) * pos['quantity']
                
                summary['positions'].append({
                    'ticker': pos['ticker'],
                    'direction': pos['direction'],
                    'quantity': pos['quantity'],
                    'entry_price': pos['entry_price'],
                    'current_price': current_price,
                    'pnl_percent': pnl_percent,
                    'gross_pnl': gross_pnl,
                    'minutes_held': pos['minutes_held']
                })
                
                total_gross_pnl += gross_pnl
        
        summary['total_open_pnl'] = total_gross_pnl
        return summary
    
    def get_closed_positions(self) -> List[Dict]:
        """Get all closed positions from this session"""
        closed = []
        for pos_id, pos in self.open_positions.items():
            if pos['status'] == 'CLOSED':
                closed.append({
                    'ticker': pos['ticker'],
                    'direction': pos['direction'],
                    'entry_price': pos['entry_price'],
                    'exit_price': pos['exit_price'],
                    'pnl': pos['net_pnl'],
                    'pnl_percent': pos['pnl_percent'],
                    'duration_minutes': pos['minutes_held'],
                    'exit_reason': pos['exit_reason']
                })
        
        return closed
    
    def save_position_report(self, report_dir: str = "reports/position_monitoring"):
        """Save position monitoring report"""
        try:
            os.makedirs(report_dir, exist_ok=True)
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'open_positions': self.get_open_positions_summary(),
                'closed_positions': self.get_closed_positions(),
                'total_positions': len(self.open_positions),
                'total_closed': len([p for p in self.open_positions.values() if p['status'] == 'CLOSED']),
                'risk_parameters': {
                    'hard_stop_loss': self.hard_stop_loss,
                    'profit_target': self.profit_target,
                    'trailing_stop': self.trailing_stop,
                    'monitor_interval_seconds': self.monitor_interval
                }
            }
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = os.path.join(report_dir, f'positions_{timestamp}.json')
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            self._log(f"Position report saved: {report_path}")
            return report_path
        
        except Exception as e:
            self._log(f"ERROR saving position report: {e}", level="ERROR")
            return None
