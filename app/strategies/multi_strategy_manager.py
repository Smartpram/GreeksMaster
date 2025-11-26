#!/usr/bin/env python3
"""
Multi-Strategy Manager
Manages multiple trading strategies and provides unified interface
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Import all strategies
from .buy_hold_trend import BuyHoldTrendStrategy
from .optimized_buy_hold_trend import OptimizedBuyHoldTrendStrategy
from .trend_following import TrendFollowingStrategy
from .mean_reversion import MeanReversionStrategy
from .breakout import BreakoutStrategy
from .momentum import MomentumStrategy
from .vwap_intraday import VWAPStrategy

logger = logging.getLogger(__name__)

class StrategyType(Enum):
    """Available strategy types"""
    BUY_HOLD_TREND = "buy_hold_trend"
    OPTIMIZED_BUY_HOLD = "optimized_buy_hold"
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    MOMENTUM = "momentum"
    VWAP_INTRADAY = "vwap_intraday"

@dataclass
class StrategyAllocation:
    """Strategy allocation configuration"""
    strategy_type: StrategyType
    allocation_pct: float  # Percentage of capital allocated
    max_positions: int     # Maximum positions for this strategy
    active: bool = True    # Whether strategy is active

class MultiStrategyManager:
    """
    Multi-Strategy Trading Manager
    
    Features:
    1. Manages multiple strategies simultaneously
    2. Capital allocation across strategies
    3. Risk management at portfolio level
    4. Strategy performance tracking
    5. Dynamic strategy activation/deactivation
    """
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.strategies = {}
        self.strategy_allocations = {}
        self.portfolio_positions = {}
        self.performance_history = []
        self.strategy_factory = self._create_strategy_factory()
        
        logger.info(f"Initialized Multi-Strategy Manager with ₹{initial_capital:,.0f}")
    
    def _create_strategy_factory(self) -> Dict:
        """Create factory for strategy instantiation"""
        return {
            StrategyType.BUY_HOLD_TREND: lambda: BuyHoldTrendStrategy(),
            StrategyType.OPTIMIZED_BUY_HOLD: lambda: OptimizedBuyHoldTrendStrategy(),
            StrategyType.TREND_FOLLOWING: lambda: TrendFollowingStrategy(),
            StrategyType.MEAN_REVERSION: lambda: MeanReversionStrategy(),
            StrategyType.BREAKOUT: lambda: BreakoutStrategy(),
            StrategyType.MOMENTUM: lambda: MomentumStrategy(),
            StrategyType.VWAP_INTRADAY: lambda: VWAPStrategy()
        }
    
    def add_strategy(self, strategy_type: StrategyType, allocation_pct: float, 
                    max_positions: int = 5, custom_config: Any = None) -> bool:
        """Add a strategy to the manager"""
        
        try:
            # Validate allocation
            total_allocation = sum(alloc.allocation_pct for alloc in self.strategy_allocations.values())
            if total_allocation + allocation_pct > 1.0:
                logger.error(f"Total allocation would exceed 100%: {(total_allocation + allocation_pct) * 100:.1f}%")
                return False
            
            # Create strategy instance
            if strategy_type in self.strategy_factory:
                strategy = self.strategy_factory[strategy_type]()
                
                # Apply custom configuration if provided
                if custom_config and hasattr(strategy, 'config'):
                    for key, value in custom_config.items():
                        if hasattr(strategy.config, key):
                            setattr(strategy.config, key, value)
                
                self.strategies[strategy_type] = strategy
                
                # Set allocation
                self.strategy_allocations[strategy_type] = StrategyAllocation(
                    strategy_type=strategy_type,
                    allocation_pct=allocation_pct,
                    max_positions=max_positions,
                    active=True
                )
                
                logger.info(f"Added {strategy_type.value} strategy with {allocation_pct:.1%} allocation")
                return True
            else:
                logger.error(f"Unknown strategy type: {strategy_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to add strategy {strategy_type}: {e}")
            return False
    
    def remove_strategy(self, strategy_type: StrategyType) -> bool:
        """Remove a strategy from the manager"""
        
        try:
            if strategy_type in self.strategies:
                # Close all positions for this strategy first
                strategy_positions = [pos for pos in self.portfolio_positions.values() 
                                    if pos.get('strategy') == strategy_type]
                
                if strategy_positions:
                    logger.warning(f"Strategy {strategy_type.value} has {len(strategy_positions)} open positions")
                    # In real implementation, would close positions gracefully
                
                del self.strategies[strategy_type]
                del self.strategy_allocations[strategy_type]
                
                logger.info(f"Removed {strategy_type.value} strategy")
                return True
            else:
                logger.warning(f"Strategy {strategy_type.value} not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove strategy {strategy_type}: {e}")
            return False
    
    def get_strategy_capital(self, strategy_type: StrategyType) -> float:
        """Get allocated capital for a strategy"""
        
        if strategy_type not in self.strategy_allocations:
            return 0.0
        
        allocation = self.strategy_allocations[strategy_type]
        return self.current_capital * allocation.allocation_pct
    
    def process_market_data(self, symbol: str, market_data: pd.DataFrame) -> List[Dict]:
        """Process market data through all active strategies"""
        
        signals = []
        
        for strategy_type, strategy in self.strategies.items():
            if not self.strategy_allocations[strategy_type].active:
                continue
            
            try:
                # Calculate indicators for this strategy
                data_with_indicators = strategy.calculate_indicators(market_data.copy())
                
                if len(data_with_indicators) == 0:
                    continue
                
                current_row = data_with_indicators.iloc[-1]
                strategy_capital = self.get_strategy_capital(strategy_type)
                
                # Check for entry signals
                signal = self._check_strategy_signals(strategy_type, strategy, symbol, 
                                                    current_row, strategy_capital)
                
                if signal:
                    signals.append(signal)
                    
            except Exception as e:
                logger.error(f"Error processing {symbol} in {strategy_type.value}: {e}")
        
        return signals
    
    def _check_strategy_signals(self, strategy_type: StrategyType, strategy: Any, 
                               symbol: str, row: pd.Series, capital: float) -> Optional[Dict]:
        """Check for entry/exit signals from a specific strategy"""
        
        try:
            # Check for long entry
            if hasattr(strategy, 'should_enter_long'):
                should_enter, reason = strategy.should_enter_long(symbol, row, capital)
                if should_enter:
                    position_size = strategy.get_position_size(symbol, row['close'], capital, 
                                                             getattr(row, 'signal_strength', 0.8))
                    return {
                        'strategy': strategy_type,
                        'symbol': symbol,
                        'action': 'buy',
                        'price': row['close'],
                        'quantity': position_size,
                        'reason': reason,
                        'timestamp': datetime.now(),
                        'signal_data': self._extract_signal_data(strategy_type, row)
                    }
            
            # Check for short entry (if supported)
            if hasattr(strategy, 'should_enter_short'):
                should_enter, reason = strategy.should_enter_short(symbol, row, capital)
                if should_enter:
                    position_size = strategy.get_position_size(symbol, row['close'], capital,
                                                             getattr(row, 'signal_strength', 0.8))
                    return {
                        'strategy': strategy_type,
                        'symbol': symbol,
                        'action': 'sell',
                        'price': row['close'],
                        'quantity': position_size,
                        'reason': reason,
                        'timestamp': datetime.now(),
                        'signal_data': self._extract_signal_data(strategy_type, row)
                    }
            
            # Check for exits on existing positions
            existing_positions = [pos for pos in self.portfolio_positions.values() 
                                if pos.get('symbol') == symbol and pos.get('strategy') == strategy_type]
            
            for position in existing_positions:
                if hasattr(strategy, 'should_exit_position'):
                    should_exit, exit_reason = strategy.should_exit_position(symbol, row, position)
                    if should_exit:
                        return {
                            'strategy': strategy_type,
                            'symbol': symbol,
                            'action': 'exit',
                            'price': row['close'],
                            'quantity': position['quantity'],
                            'reason': exit_reason,
                            'timestamp': datetime.now(),
                            'position_id': position.get('id')
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking signals for {strategy_type.value}: {e}")
            return None
    
    def _extract_signal_data(self, strategy_type: StrategyType, row: pd.Series) -> Dict:
        """Extract relevant signal data based on strategy type"""
        
        base_data = {
            'price': row['close'],
            'volume': row.get('volume', 0)
        }
        
        # Strategy-specific data extraction
        if strategy_type == StrategyType.TREND_FOLLOWING:
            base_data.update({
                'ma_short': row.get('ma_short'),
                'ma_long': row.get('ma_long'),
                'adx': row.get('adx'),
                'trend_score': row.get('trend_score')
            })
        
        elif strategy_type == StrategyType.MEAN_REVERSION:
            base_data.update({
                'bb_position': row.get('bb_position'),
                'rsi': row.get('rsi'),
                'reversion_score': row.get('reversion_score')
            })
        
        elif strategy_type == StrategyType.BREAKOUT:
            base_data.update({
                'atr': row.get('atr'),
                'nearest_resistance': row.get('nearest_resistance'),
                'nearest_support': row.get('nearest_support'),
                'breakout_score': row.get('breakout_score')
            })
        
        elif strategy_type == StrategyType.MOMENTUM:
            base_data.update({
                'rsi': row.get('rsi'),
                'momentum_5d': row.get('momentum_5d'),
                'momentum_score': row.get('momentum_score')
            })
        
        elif strategy_type == StrategyType.VWAP_INTRADAY:
            base_data.update({
                'vwap': row.get('vwap'),
                'price_above_vwap': row.get('price_above_vwap'),
                'vwap_score': row.get('vwap_score')
            })
        
        return base_data
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary"""
        
        # Calculate total positions value
        total_position_value = 0
        positions_by_strategy = {}
        
        for pos in self.portfolio_positions.values():
            strategy = pos.get('strategy', 'unknown')
            if strategy not in positions_by_strategy:
                positions_by_strategy[strategy] = []
            positions_by_strategy[strategy].append(pos)
            total_position_value += pos.get('market_value', 0)
        
        # Calculate strategy allocations
        strategy_summary = {}
        for strategy_type, allocation in self.strategy_allocations.items():
            allocated_capital = self.current_capital * allocation.allocation_pct
            used_capital = sum(pos.get('cost', 0) for pos in positions_by_strategy.get(strategy_type, []))
            
            strategy_summary[strategy_type.value] = {
                'allocated_capital': allocated_capital,
                'used_capital': used_capital,
                'available_capital': allocated_capital - used_capital,
                'utilization': used_capital / allocated_capital if allocated_capital > 0 else 0,
                'positions': len(positions_by_strategy.get(strategy_type, [])),
                'max_positions': allocation.max_positions,
                'active': allocation.active
            }
        
        return {
            'total_capital': self.current_capital,
            'cash': self.current_capital - total_position_value,
            'invested': total_position_value,
            'total_positions': len(self.portfolio_positions),
            'strategies_active': sum(1 for a in self.strategy_allocations.values() if a.active),
            'strategy_breakdown': strategy_summary
        }
    
    def get_strategy_performance(self) -> Dict:
        """Get performance metrics for each strategy"""
        
        performance = {}
        
        for strategy_type in self.strategies.keys():
            # Calculate strategy-specific performance metrics
            strategy_positions = [pos for pos in self.portfolio_positions.values() 
                                if pos.get('strategy') == strategy_type]
            
            if strategy_positions:
                total_pnl = sum(pos.get('unrealized_pnl', 0) + pos.get('realized_pnl', 0) 
                              for pos in strategy_positions)
                total_invested = sum(pos.get('cost', 0) for pos in strategy_positions)
                
                performance[strategy_type.value] = {
                    'total_pnl': total_pnl,
                    'total_invested': total_invested,
                    'return_pct': total_pnl / total_invested if total_invested > 0 else 0,
                    'positions': len(strategy_positions),
                    'avg_position_size': total_invested / len(strategy_positions) if strategy_positions else 0
                }
            else:
                performance[strategy_type.value] = {
                    'total_pnl': 0,
                    'total_invested': 0,
                    'return_pct': 0,
                    'positions': 0,
                    'avg_position_size': 0
                }
        
        return performance
    
    def set_strategy_active(self, strategy_type: StrategyType, active: bool) -> bool:
        """Activate or deactivate a strategy"""
        
        if strategy_type in self.strategy_allocations:
            self.strategy_allocations[strategy_type].active = active
            logger.info(f"Strategy {strategy_type.value} {'activated' if active else 'deactivated'}")
            return True
        else:
            logger.warning(f"Strategy {strategy_type.value} not found")
            return False
    
    def get_strategy_info(self) -> Dict:
        """Get detailed information about all strategies"""
        
        strategy_info = {}
        
        for strategy_type, strategy in self.strategies.items():
            allocation = self.strategy_allocations[strategy_type]
            
            info = strategy.get_strategy_info()
            info.update({
                'allocation_pct': allocation.allocation_pct,
                'allocated_capital': self.get_strategy_capital(strategy_type),
                'max_positions': allocation.max_positions,
                'active': allocation.active
            })
            
            strategy_info[strategy_type.value] = info
        
        return strategy_info
    
    def rebalance_allocations(self, new_allocations: Dict[StrategyType, float]) -> bool:
        """Rebalance strategy allocations"""
        
        # Validate total allocation
        total_allocation = sum(new_allocations.values())
        if abs(total_allocation - 1.0) > 0.001:  # Allow small rounding errors
            logger.error(f"Total allocation must equal 100%, got {total_allocation:.1%}")
            return False
        
        # Update allocations
        for strategy_type, allocation_pct in new_allocations.items():
            if strategy_type in self.strategy_allocations:
                self.strategy_allocations[strategy_type].allocation_pct = allocation_pct
                logger.info(f"Updated {strategy_type.value} allocation to {allocation_pct:.1%}")
        
        return True

# Factory function for easy creation
def create_multi_strategy_manager(initial_capital: float = 100000) -> MultiStrategyManager:
    """Create a multi-strategy manager with default configurations"""
    
    manager = MultiStrategyManager(initial_capital)
    
    logger.info(f"Created Multi-Strategy Manager with ₹{initial_capital:,.0f}")
    logger.info("Available strategies:")
    for strategy_type in StrategyType:
        logger.info(f"  - {strategy_type.value}")
    
    return manager

# Example configurations
CONSERVATIVE_ALLOCATION = {
    StrategyType.OPTIMIZED_BUY_HOLD: 0.4,    # 40% - Stable base
    StrategyType.MEAN_REVERSION: 0.3,        # 30% - Range-bound markets
    StrategyType.TREND_FOLLOWING: 0.2,       # 20% - Trending markets
    StrategyType.VWAP_INTRADAY: 0.1          # 10% - Intraday opportunities
}

AGGRESSIVE_ALLOCATION = {
    StrategyType.MOMENTUM: 0.3,              # 30% - High momentum
    StrategyType.BREAKOUT: 0.25,             # 25% - Volatility plays
    StrategyType.TREND_FOLLOWING: 0.25,      # 25% - Trend capture
    StrategyType.OPTIMIZED_BUY_HOLD: 0.2     # 20% - Stable base
}

BALANCED_ALLOCATION = {
    StrategyType.OPTIMIZED_BUY_HOLD: 0.25,   # 25% - Core holding
    StrategyType.TREND_FOLLOWING: 0.25,      # 25% - Trend capture
    StrategyType.MEAN_REVERSION: 0.2,        # 20% - Range trading
    StrategyType.MOMENTUM: 0.15,             # 15% - Momentum plays
    StrategyType.BREAKOUT: 0.15              # 15% - Breakout trades
}