"""
Local Portfolio Tracker
Interim solution while portfolio API endpoint is being fixed
"""
import json
import os
from datetime import datetime
from typing import Dict, List

class LocalPortfolioTracker:
    """Track portfolio locally using trade confirmations"""
    
    def __init__(self):
        self.portfolio_file = "data/local_portfolio.json"
        self.trades_file = "data/local_trades.json"
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs("data", exist_ok=True)
        
        # Initialize files if they don't exist
        if not os.path.exists(self.portfolio_file):
            with open(self.portfolio_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.trades_file):
            with open(self.trades_file, 'w') as f:
                json.dump([], f)
    
    def add_trade(self, trade_data: Dict):
        """Add a trade to local tracking"""
        with open(self.trades_file, 'r') as f:
            trades = json.load(f)
        
        trade_data['timestamp'] = datetime.now().isoformat()
        trades.append(trade_data)
        
        with open(self.trades_file, 'w') as f:
            json.dump(trades, f, indent=2)
        
        # Update portfolio
        self.update_portfolio_from_trades()
    
    def update_portfolio_from_trades(self):
        """Update portfolio based on trades"""
        with open(self.trades_file, 'r') as f:
            trades = json.load(f)
        
        portfolio = {}
        
        for trade in trades:
            symbol = trade.get('stock_code', 'UNKNOWN')
            quantity = int(trade.get('quantity', 0))
            price = float(trade.get('price', 0))
            action = trade.get('action', 'buy').lower()
            
            if symbol not in portfolio:
                portfolio[symbol] = {
                    'quantity': 0,
                    'average_price': 0,
                    'total_invested': 0
                }
            
            if action == 'buy':
                old_quantity = portfolio[symbol]['quantity']
                old_invested = portfolio[symbol]['total_invested']
                
                new_quantity = old_quantity + quantity
                new_invested = old_invested + (quantity * price)
                
                portfolio[symbol]['quantity'] = new_quantity
                portfolio[symbol]['total_invested'] = new_invested
                portfolio[symbol]['average_price'] = new_invested / new_quantity if new_quantity > 0 else 0
                
            elif action == 'sell':
                portfolio[symbol]['quantity'] -= quantity
                if portfolio[symbol]['quantity'] <= 0:
                    del portfolio[symbol]
        
        with open(self.portfolio_file, 'w') as f:
            json.dump(portfolio, f, indent=2)
    
    def get_portfolio(self) -> Dict:
        """Get current portfolio"""
        try:
            with open(self.portfolio_file, 'r') as f:
                portfolio = json.load(f)
            
            return {
                'success': True,
                'data': portfolio,
                'message': 'Local portfolio data',
                'source': 'local_tracking'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Local portfolio error: {str(e)}',
                'data': {}
            }
    
    def get_trades(self) -> Dict:
        """Get trade history"""
        try:
            with open(self.trades_file, 'r') as f:
                trades = json.load(f)
            
            return {
                'success': True,
                'data': trades,
                'message': 'Local trade history'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Local trades error: {str(e)}',
                'data': []
            }
