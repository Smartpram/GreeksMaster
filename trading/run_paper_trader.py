#!/usr/bin/env python3
"""
Live Paper Trading Runner
Continuously monitors strategies and executes paper trades
Can be deployed as a background service
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
import time
from typing import Dict, List
import threading
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('paper_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    from app.services.breeze_api import BreezeAPIService
    BREEZE_AVAILABLE = True
except Exception as e:
    logger.warning(f"Breeze API not available: {e}")
    BREEZE_AVAILABLE = False


class PaperTradingRunner:
    """Live paper trading runner with continuous monitoring"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.paper_trading_data = {
            'initial_capital': config.get('initial_capital', 100000),
            'capital': config.get('initial_capital', 100000),
            'positions': {},
            'trades': [],
            'daily_pnl': {},
            'start_date': datetime.now().isoformat(),
            'strategies': config.get('strategies', [])
        }
        self.running = False
        self.breeze_service = None
        self.last_prices = {}
        self.last_update = {}
        
    def start(self):
        """Start paper trading"""
        logger.info("=" * 100)
        logger.info("PAPER TRADING RUNNER STARTED")
        logger.info("=" * 100)
        logger.info(f"Initial Capital: ₹{self.paper_trading_data['initial_capital']:,.0f}")
        logger.info(f"Strategies: {', '.join([s['name'] for s in self.paper_trading_data['strategies']])}")
        
        self.running = True
        self.save_state()
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        
        return monitor_thread
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Update prices
                self._update_prices()
                
                # Generate signals for each strategy
                for strategy_config in self.paper_trading_data['strategies']:
                    self._process_strategy(strategy_config)
                
                # Update daily P&L
                self._update_daily_pnl()
                
                # Save state
                self.save_state()
                
                # Log status
                logger.info(self._get_status_string())
                
                # Wait before next update
                time.sleep(self.config.get('update_interval', 3600))  # Default 1 hour
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)
    
    def _update_prices(self):
        """Fetch latest prices from Breeze API"""
        if not BREEZE_AVAILABLE:
            logger.debug("Using simulated prices")
            return
        
        try:
            if not self.breeze_service:
                self.breeze_service = BreezeAPIService()
                auth = self.breeze_service.authenticate()
                if not auth.get('success'):
                    logger.warning(f"Authentication failed: {auth.get('error')}")
                    return
            
            # Get quotes for all positions
            for instrument in list(self.paper_trading_data['positions'].keys()) + self.config.get('watchlist', []):
                try:
                    quote = self.breeze_service.get_quotes(instrument, exchange_code="NSE")
                    if quote.get('success'):
                        data = quote.get('data', {})
                        if isinstance(data, dict) and 'ltp' in data:
                            self.last_prices[instrument] = float(data['ltp'])
                            self.last_update[instrument] = datetime.now()
                            logger.debug(f"Updated {instrument}: ₹{self.last_prices[instrument]:.2f}")
                except Exception as e:
                    logger.debug(f"Error fetching quote for {instrument}: {e}")
        
        except Exception as e:
            logger.error(f"Error updating prices: {e}")
    
    def _process_strategy(self, strategy_config: Dict):
        """Process strategy signals"""
        strategy_name = strategy_config['name']
        symbol = strategy_config['symbol']
        strategy_type = strategy_config['type']
        
        try:
            # Generate signal (simplified)
            signal = self._generate_signal(strategy_type, symbol)
            
            if signal:
                logger.info(f"Signal from {strategy_name}: {signal}")
                
                if signal['action'] == 'BUY':
                    self._execute_buy(symbol, signal.get('quantity', 10), signal.get('reason'))
                elif signal['action'] == 'SELL':
                    if symbol in self.paper_trading_data['positions']:
                        quantity = signal.get('quantity', self.paper_trading_data['positions'][symbol]['quantity'])
                        self._execute_sell(symbol, quantity, signal.get('reason'))
        
        except Exception as e:
            logger.error(f"Error processing strategy {strategy_name}: {e}")
    
    def _generate_signal(self, strategy_type: str, symbol: str) -> Dict:
        """Generate trading signal (simplified for demo)"""
        # In production, this would implement actual strategy logic
        # For now, return None (no signal)
        return None
    
    def _execute_buy(self, symbol: str, quantity: int, reason: str = ""):
        """Execute buy trade"""
        if symbol not in self.last_prices:
            logger.warning(f"No price available for {symbol}")
            return
        
        price = self.last_prices[symbol]
        cost = quantity * price
        
        if cost <= self.paper_trading_data['capital']:
            self.paper_trading_data['capital'] -= cost
            
            if symbol not in self.paper_trading_data['positions']:
                self.paper_trading_data['positions'][symbol] = {
                    'quantity': 0,
                    'avg_price': 0,
                    'entry_date': datetime.now().isoformat()
                }
            
            old_qty = self.paper_trading_data['positions'][symbol]['quantity']
            self.paper_trading_data['positions'][symbol]['quantity'] += quantity
            self.paper_trading_data['positions'][symbol]['avg_price'] = (
                (old_qty * self.paper_trading_data['positions'][symbol]['avg_price'] + quantity * price) /
                self.paper_trading_data['positions'][symbol]['quantity']
            )
            
            trade = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'action': 'BUY',
                'quantity': quantity,
                'price': price,
                'cost': cost,
                'reason': reason
            }
            self.paper_trading_data['trades'].append(trade)
            
            logger.info(f"✅ BUY: {quantity} x {symbol} @ ₹{price:.2f} ({reason})")
        else:
            logger.warning(f"Insufficient capital for {quantity} x {symbol}. Need: ₹{cost:.2f}, Have: ₹{self.paper_trading_data['capital']:.2f}")
    
    def _execute_sell(self, symbol: str, quantity: int, reason: str = ""):
        """Execute sell trade"""
        if symbol not in self.last_prices:
            logger.warning(f"No price available for {symbol}")
            return
        
        if symbol not in self.paper_trading_data['positions']:
            logger.warning(f"No position in {symbol}")
            return
        
        if self.paper_trading_data['positions'][symbol]['quantity'] < quantity:
            logger.warning(f"Insufficient quantity. Have: {self.paper_trading_data['positions'][symbol]['quantity']}, Need: {quantity}")
            return
        
        price = self.last_prices[symbol]
        proceeds = quantity * price
        entry_price = self.paper_trading_data['positions'][symbol]['avg_price']
        pnl = (price - entry_price) * quantity
        pnl_pct = (pnl / (entry_price * quantity)) * 100
        
        self.paper_trading_data['capital'] += proceeds
        self.paper_trading_data['positions'][symbol]['quantity'] -= quantity
        
        if self.paper_trading_data['positions'][symbol]['quantity'] == 0:
            del self.paper_trading_data['positions'][symbol]
        
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': 'SELL',
            'quantity': quantity,
            'price': price,
            'proceeds': proceeds,
            'entry_price': entry_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'reason': reason
        }
        self.paper_trading_data['trades'].append(trade)
        
        logger.info(f"✅ SELL: {quantity} x {symbol} @ ₹{price:.2f} | P&L: ₹{pnl:.2f} ({pnl_pct:.2f}%) ({reason})")
    
    def _update_daily_pnl(self):
        """Calculate daily P&L"""
        today = datetime.now().date().isoformat()
        
        # Realized P&L from today's sells
        today_realized = sum([
            t['pnl'] for t in self.paper_trading_data['trades']
            if t['action'] == 'SELL' and t['timestamp'].startswith(today)
        ])
        
        # Unrealized P&L from open positions
        today_unrealized = 0
        for symbol, position in self.paper_trading_data['positions'].items():
            if symbol in self.last_prices:
                today_unrealized += (self.last_prices[symbol] - position['avg_price']) * position['quantity']
        
        self.paper_trading_data['daily_pnl'][today] = {
            'realized': today_realized,
            'unrealized': today_unrealized,
            'total': today_realized + today_unrealized
        }
    
    def _get_status_string(self) -> str:
        """Generate status string"""
        portfolio_value = self.paper_trading_data['capital']
        for symbol, position in self.paper_trading_data['positions'].items():
            if symbol in self.last_prices:
                portfolio_value += position['quantity'] * self.last_prices[symbol]
        
        total_return = (
            (portfolio_value - self.paper_trading_data['initial_capital']) /
            self.paper_trading_data['initial_capital'] * 100
        )
        
        today = datetime.now().date().isoformat()
        daily_pnl = self.paper_trading_data['daily_pnl'].get(today, {}).get('total', 0)
        
        status = (
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"Portfolio: ₹{portfolio_value:>12,.0f} | "
            f"Return: {total_return:>7.2f}% | "
            f"Daily P&L: ₹{daily_pnl:>10,.0f} | "
            f"Positions: {len(self.paper_trading_data['positions'])}"
        )
        return status
    
    def save_state(self):
        """Save paper trading state to file"""
        state_file = Path("paper_trading_state.json")
        try:
            with open(state_file, 'w') as f:
                json.dump(self.paper_trading_data, f, indent=2, default=str)
            logger.debug("State saved")
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def load_state(self):
        """Load paper trading state from file"""
        state_file = Path("paper_trading_state.json")
        try:
            if state_file.exists():
                with open(state_file, 'r') as f:
                    self.paper_trading_data = json.load(f)
                logger.info("State loaded from file")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
    
    def get_summary(self) -> Dict:
        """Get trading summary"""
        portfolio_value = self.paper_trading_data['capital']
        for symbol, position in self.paper_trading_data['positions'].items():
            if symbol in self.last_prices:
                portfolio_value += position['quantity'] * self.last_prices[symbol]
        
        total_return = (
            (portfolio_value - self.paper_trading_data['initial_capital']) /
            self.paper_trading_data['initial_capital'] * 100
        )
        
        # Calculate realized P&L
        realized_pnl = sum([
            t['pnl'] for t in self.paper_trading_data['trades']
            if t['action'] == 'SELL'
        ])
        
        # Calculate unrealized P&L
        unrealized_pnl = 0
        for symbol, position in self.paper_trading_data['positions'].items():
            if symbol in self.last_prices:
                unrealized_pnl += (self.last_prices[symbol] - position['avg_price']) * position['quantity']
        
        return {
            'initial_capital': self.paper_trading_data['initial_capital'],
            'portfolio_value': portfolio_value,
            'cash': self.paper_trading_data['capital'],
            'total_return': total_return,
            'realized_pnl': realized_pnl,
            'unrealized_pnl': unrealized_pnl,
            'total_pnl': realized_pnl + unrealized_pnl,
            'open_positions': len(self.paper_trading_data['positions']),
            'total_trades': len([t for t in self.paper_trading_data['trades'] if t['action'] == 'BUY']),
            'win_rate': self._calculate_win_rate(),
            'daily_pnl': self.paper_trading_data['daily_pnl']
        }
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate"""
        profitable = len([t for t in self.paper_trading_data['trades'] if t.get('pnl', 0) > 0])
        total = len([t for t in self.paper_trading_data['trades'] if t['action'] == 'SELL'])
        return (profitable / total * 100) if total > 0 else 0
    
    def stop(self):
        """Stop paper trading"""
        self.running = False
        logger.info("Paper trading stopped")
        self.save_state()


def main():
    """Main entry point"""
    
    # Configuration
    config = {
        'initial_capital': 100000,
        'update_interval': 3600,  # Update every hour
        'watchlist': ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR'],
        'strategies': [
            {
                'name': 'SMA Crossover - RELIANCE',
                'symbol': 'RELIANCE',
                'type': 'sma_crossover',
                'params': {'short_window': 30, 'long_window': 65}
            },
            {
                'name': 'RSI Mean Reversion - RELIANCE',
                'symbol': 'RELIANCE',
                'type': 'rsi_reversal',
                'params': {'period': 10, 'oversold': 40, 'overbought': 65}
            }
        ]
    }
    
    # Start runner
    runner = PaperTradingRunner(config)
    runner.load_state()
    monitor_thread = runner.start()
    
    print("\n" + "=" * 100)
    print("  LIVE PAPER TRADING RUNNER")
    print("=" * 100)
    print("\n  ✅ Paper trading runner started in background")
    print(f"  📊 Monitoring {len(config['strategies'])} strategies")
    print(f"  💰 Initial Capital: ₹{config['initial_capital']:,.0f}")
    print(f"  ⏱️  Update Interval: {config['update_interval']} seconds")
    print("\n  View log: paper_trading.log")
    print("  State file: paper_trading_state.json")
    print("\n" + "=" * 100 + "\n")
    
    # Keep runner alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        runner.stop()
        
        # Print final summary
        summary = runner.get_summary()
        print("\n" + "=" * 100)
        print("  FINAL SUMMARY")
        print("=" * 100)
        print(f"  Initial Capital:    ₹{summary['initial_capital']:>12,.0f}")
        print(f"  Portfolio Value:    ₹{summary['portfolio_value']:>12,.0f}")
        print(f"  Total Return:       {summary['total_return']:>12.2f}%")
        print(f"  Total P&L:          ₹{summary['total_pnl']:>12,.0f}")
        print(f"     Realized:       ₹{summary['realized_pnl']:>12,.0f}")
        print(f"     Unrealized:     ₹{summary['unrealized_pnl']:>12,.0f}")
        print(f"  Open Positions:     {summary['open_positions']:>12}")
        print(f"  Total Trades:       {summary['total_trades']:>12}")
        print(f"  Win Rate:           {summary['win_rate']:>12.2f}%")
        print(f"  Cash Available:     ₹{summary['cash']:>12,.0f}")
        print("\n" + "=" * 100 + "\n")


if __name__ == "__main__":
    main()
