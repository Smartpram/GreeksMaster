"""
Mock Dependencies for Testing
==============================
Provides minimal implementations of RiskManager and NotificationService
for backtesting without requiring full production infrastructure.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ============================================================================
# MOCK RISK MANAGER
# ============================================================================

class MockRiskManager:
    """Minimal risk manager stub for backtesting"""
    
    def __init__(self):
        self.position_size = 1.0
        self.max_loss_per_trade = 0.05
        self.max_daily_loss = 0.10
        self.daily_loss = 0.0
        self.current_positions = {}
        
    def calculate_position_size(self, capital: float, risk_per_trade: float = 0.02) -> float:
        """Calculate position size based on risk"""
        return capital * risk_per_trade
    
    def check_risk_limits(self, symbol: str, position_size: float) -> bool:
        """Verify risk limits are not exceeded"""
        return True
    
    def record_trade(self, symbol: str, entry_price: float, quantity: int) -> None:
        """Record a trade for risk tracking"""
        self.current_positions[symbol] = {
            'entry_price': entry_price,
            'quantity': quantity,
            'entry_time': None
        }
    
    def close_trade(self, symbol: str, exit_price: float) -> Dict[str, Any]:
        """Close a trade and calculate P&L"""
        if symbol in self.current_positions:
            pos = self.current_positions[symbol]
            pnl = (exit_price - pos['entry_price']) * pos['quantity']
            del self.current_positions[symbol]
            return {'pnl': pnl, 'status': 'closed'}
        return {'pnl': 0, 'status': 'not_found'}
    
    def get_current_exposure(self) -> float:
        """Get total current market exposure"""
        return float(len(self.current_positions))


# ============================================================================
# MOCK NOTIFICATION SERVICE
# ============================================================================

class MockNotificationService:
    """Minimal notification service stub for backtesting"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.event_log = []
    
    def send_trade_alert(self, message: str, **kwargs) -> None:
        """Send trade alert (email/telegram in production)"""
        if self.verbose:
            logger.info(f"[TRADE ALERT] {message}")
        self.event_log.append({'type': 'trade_alert', 'message': message, **kwargs})
    
    def send_risk_alert(self, message: str, **kwargs) -> None:
        """Send risk alert (email/telegram in production)"""
        if self.verbose:
            logger.warning(f"[RISK ALERT] {message}")
        self.event_log.append({'type': 'risk_alert', 'message': message, **kwargs})
    
    def send_error_alert(self, message: str, **kwargs) -> None:
        """Send error alert"""
        if self.verbose:
            logger.error(f"[ERROR ALERT] {message}")
        self.event_log.append({'type': 'error_alert', 'message': message, **kwargs})
    
    def log_event(self, event_type: str, message: str, **kwargs) -> None:
        """Log an event"""
        if self.verbose:
            logger.debug(f"[{event_type}] {message}")
        self.event_log.append({'type': event_type, 'message': message, **kwargs})
    
    def get_event_log(self) -> list:
        """Retrieve event log"""
        return self.event_log


# ============================================================================
# STRATEGY CONFIGURATION DATACLASSES
# ============================================================================

@dataclass
class BuyHoldTrendConfig:
    """Configuration for Buy & Hold Trend Strategy"""
    MA_PERIOD: int = 20
    RSI_PERIOD: int = 14
    RSI_THRESHOLD: float = 50.0
    VOLUME_CONFIRMATION: bool = True
    MIN_SIGNAL_STRENGTH: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'MA_PERIOD': self.MA_PERIOD,
            'RSI_PERIOD': self.RSI_PERIOD,
            'RSI_THRESHOLD': self.RSI_THRESHOLD,
            'VOLUME_CONFIRMATION': self.VOLUME_CONFIRMATION,
            'MIN_SIGNAL_STRENGTH': self.MIN_SIGNAL_STRENGTH,
        }


@dataclass
class MeanReversionConfig:
    """Configuration for Mean Reversion Strategy"""
    BB_PERIOD: int = 20
    BB_STD_DEV: float = 2.0
    ENTRY_THRESHOLD: float = -2.0
    EXIT_THRESHOLD: float = 2.0
    MIN_SIGNAL_STRENGTH: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'BB_PERIOD': self.BB_PERIOD,
            'BB_STD_DEV': self.BB_STD_DEV,
            'ENTRY_THRESHOLD': self.ENTRY_THRESHOLD,
            'EXIT_THRESHOLD': self.EXIT_THRESHOLD,
            'MIN_SIGNAL_STRENGTH': self.MIN_SIGNAL_STRENGTH,
        }


@dataclass
class MomentumConfig:
    """Configuration for Momentum Strategy"""
    RSI_MOMENTUM_THRESHOLD: float = 0.0
    MOMENTUM_PERIOD: int = 5
    RSI_THRESHOLD: float = 30.0
    RSI_OVERBOUGHT: float = 70.0
    MIN_SIGNAL_STRENGTH: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'RSI_MOMENTUM_THRESHOLD': self.RSI_MOMENTUM_THRESHOLD,
            'MOMENTUM_PERIOD': self.MOMENTUM_PERIOD,
            'RSI_THRESHOLD': self.RSI_THRESHOLD,
            'RSI_OVERBOUGHT': self.RSI_OVERBOUGHT,
            'MIN_SIGNAL_STRENGTH': self.MIN_SIGNAL_STRENGTH,
        }


@dataclass
class TrendFollowingConfig:
    """Configuration for Trend Following Strategy"""
    MA_SHORT: int = 10
    MA_LONG: int = 30
    TREND_THRESHOLD: float = 0.005
    MIN_SIGNAL_STRENGTH: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'MA_SHORT': self.MA_SHORT,
            'MA_LONG': self.MA_LONG,
            'TREND_THRESHOLD': self.TREND_THRESHOLD,
            'MIN_SIGNAL_STRENGTH': self.MIN_SIGNAL_STRENGTH,
        }


@dataclass
class BreakoutConfig:
    """Configuration for Breakout Strategy"""
    LOOKBACK_PERIOD: int = 20
    BREAKOUT_THRESHOLD: float = 0.01
    VOLUME_CONFIRMATION: float = 1.5
    MIN_SIGNAL_STRENGTH: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'LOOKBACK_PERIOD': self.LOOKBACK_PERIOD,
            'BREAKOUT_THRESHOLD': self.BREAKOUT_THRESHOLD,
            'VOLUME_CONFIRMATION': self.VOLUME_CONFIRMATION,
            'MIN_SIGNAL_STRENGTH': self.MIN_SIGNAL_STRENGTH,
        }


@dataclass
class VWAPConfig:
    """Configuration for VWAP Strategy"""
    VWAP_PERIOD: int = 14
    VWAP_DEVIATION: float = 0.02
    VOLUME_FILTER: bool = True
    MIN_SIGNAL_STRENGTH: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'VWAP_PERIOD': self.VWAP_PERIOD,
            'VWAP_DEVIATION': self.VWAP_DEVIATION,
            'VOLUME_FILTER': self.VOLUME_FILTER,
            'MIN_SIGNAL_STRENGTH': self.MIN_SIGNAL_STRENGTH,
        }


@dataclass
class OptimizedBuyHoldConfig:
    """Configuration for Optimized Buy & Hold Strategy"""
    MIN_SIGNAL_STRENGTH: float = 0.5
    TREND_CONFIRMATION: int = 3
    VOLATILITY_ADJUSTMENT: bool = True
    MA_PERIOD: int = 20
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'MIN_SIGNAL_STRENGTH': self.MIN_SIGNAL_STRENGTH,
            'TREND_CONFIRMATION': self.TREND_CONFIRMATION,
            'VOLATILITY_ADJUSTMENT': self.VOLATILITY_ADJUSTMENT,
            'MA_PERIOD': self.MA_PERIOD,
        }


@dataclass
class AIEnhancedConfig:
    """Configuration for AI Enhanced Strategy"""
    MIN_SIGNAL_STRENGTH: float = 0.5
    MODEL_CONFIDENCE_THRESHOLD: float = 0.65
    ENSEMBLE_SIZE: int = 3
    USE_SENTIMENT: bool = True
    UPDATE_FREQUENCY: int = 60
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'MIN_SIGNAL_STRENGTH': self.MIN_SIGNAL_STRENGTH,
            'MODEL_CONFIDENCE_THRESHOLD': self.MODEL_CONFIDENCE_THRESHOLD,
            'ENSEMBLE_SIZE': self.ENSEMBLE_SIZE,
            'USE_SENTIMENT': self.USE_SENTIMENT,
            'UPDATE_FREQUENCY': self.UPDATE_FREQUENCY,
        }


# ============================================================================
# CONFIGURATION REGISTRY
# ============================================================================

CONFIG_MAP = {
    'BuyHoldTrendStrategy': BuyHoldTrendConfig,
    'MeanReversionStrategy': MeanReversionConfig,
    'MomentumStrategy': MomentumConfig,
    'TrendFollowingStrategy': TrendFollowingConfig,
    'BreakoutStrategy': BreakoutConfig,
    'VWAPStrategy': VWAPConfig,
    'OptimizedBuyHoldTrendStrategy': OptimizedBuyHoldConfig,
    'AIEnhancedStrategy': AIEnhancedConfig,
}


def get_default_config(strategy_name: str) -> Optional[Any]:
    """Get default configuration for a strategy by class name"""
    config_class = CONFIG_MAP.get(strategy_name)
    if config_class:
        return config_class()
    logger.warning(f"No config found for strategy: {strategy_name}")
    return None
