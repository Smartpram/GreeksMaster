"""
Base Strategy Class
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    """Abstract base class for all trading strategies"""
    
    def __init__(self, order_manager, risk_manager, notification_service):
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.notification_service = notification_service
        self.is_running = False
        self.positions = {}
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'win_rate': 0.0
        }
        
    @abstractmethod
    def generate_signals(self, data: Dict) -> Dict:
        """Generate trading signals based on market data"""
        pass
    
    @abstractmethod
    def execute_strategy(self, signal: Dict) -> bool:
        """Execute strategy based on generated signals"""
        pass
    
    def start(self):
        """Start the strategy"""
        self.is_running = True
        logger.info(f"{self.__class__.__name__} strategy started")
        if self.notification_service:
            self.notification_service.send_notification(
                f"Strategy {self.__class__.__name__} started",
                "INFO"
            )
    
    def stop(self):
        """Stop the strategy"""
        self.is_running = False
        logger.info(f"{self.__class__.__name__} strategy stopped")
        if self.notification_service:
            self.notification_service.send_notification(
                f"Strategy {self.__class__.__name__} stopped",
                "INFO"
            )
    
    def update_performance_metrics(self, trade_pnl: float):
        """Update performance metrics after a trade"""
        self.performance_metrics['total_trades'] += 1
        self.performance_metrics['total_pnl'] += trade_pnl
        
        if trade_pnl > 0:
            self.performance_metrics['winning_trades'] += 1
        else:
            self.performance_metrics['losing_trades'] += 1
        
        # Calculate win rate
        total_trades = self.performance_metrics['total_trades']
        if total_trades > 0:
            self.performance_metrics['win_rate'] = (
                self.performance_metrics['winning_trades'] / total_trades
            ) * 100
    
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        return self.performance_metrics.copy()
    
    def reset_performance_metrics(self):
        """Reset performance metrics"""
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'win_rate': 0.0
        }