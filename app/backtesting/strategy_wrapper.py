"""
Strategy Wrapper - Dependency Injection Layer
===============================================
Handles instantiation of strategies with mock dependencies for testing.
"""

import logging
from typing import Type, Optional, Any, Dict
from app.mocks.mock_dependencies import (
    MockRiskManager,
    MockNotificationService,
    get_default_config,
    CONFIG_MAP
)

logger = logging.getLogger(__name__)


class StrategyWrapper:
    """
    Wraps strategy classes to handle dependency injection.
    Provides mock implementations for testing/backtesting.
    """
    
    def __init__(
        self,
        strategy_class: Type,
        symbol: str,
        config: Optional[Any] = None,
        risk_manager: Optional[MockRiskManager] = None,
        notification_service: Optional[MockNotificationService] = None,
        verbose: bool = False
    ):
        """
        Initialize strategy wrapper with optional dependencies.
        
        Args:
            strategy_class: The strategy class to instantiate
            symbol: Trading symbol (e.g., 'NIFTY')
            config: Strategy configuration object (uses defaults if None)
            risk_manager: Risk management instance (creates mock if None)
            notification_service: Notification service (creates mock if None)
            verbose: Enable verbose logging
        """
        self.strategy_class = strategy_class
        self.symbol = symbol
        self.verbose = verbose
        
        # Get or create dependencies
        self.risk_manager = risk_manager or MockRiskManager()
        self.notification_service = notification_service or MockNotificationService(verbose=verbose)
        
        # Get or create configuration
        if config is None:
            config = self._get_default_config()
        self.config = config
        
        self.strategy_instance = None
        
    def _get_default_config(self) -> Any:
        """Get default configuration for the strategy"""
        strategy_name = self.strategy_class.__name__
        config = get_default_config(strategy_name)
        
        if config is None:
            logger.warning(f"No configuration found for {strategy_name}, using empty object")
            config = object()  # Fallback to empty object
        
        return config
    
    def instantiate(self) -> Optional[Any]:
        """
        Create and return strategy instance with dependencies.
        
        Returns:
            Instantiated strategy object, or None if instantiation fails
        """
        try:
            strategy_name = self.strategy_class.__name__
            
            # Attempt standard constructor: (symbol, risk_manager, notification_service)
            try:
                self.strategy_instance = self.strategy_class(
                    self.symbol,
                    self.risk_manager,
                    self.notification_service
                )
                if self.verbose:
                    logger.info(f"✓ Instantiated {strategy_name} with (symbol, risk_manager, notification_service)")
                return self.strategy_instance
            except TypeError as e:
                # If that fails, try with config
                if 'config' in str(e).lower():
                    self.strategy_instance = self.strategy_class(
                        self.symbol,
                        self.risk_manager,
                        self.notification_service,
                        self.config
                    )
                    if self.verbose:
                        logger.info(f"✓ Instantiated {strategy_name} with config parameter")
                    return self.strategy_instance
                raise
                
        except Exception as e:
            logger.error(f"✗ Failed to instantiate {self.strategy_class.__name__}: {str(e)}")
            return None
    
    def get_strategy(self) -> Optional[Any]:
        """
        Get or instantiate the strategy.
        
        Returns:
            Strategy instance or None
        """
        if self.strategy_instance is None:
            self.instantiate()
        return self.strategy_instance
    
    @staticmethod
    def create_batch(
        strategy_classes: Dict[str, Type],
        symbols: list,
        config_overrides: Optional[Dict] = None,
        verbose: bool = False
    ) -> Dict[str, Dict[str, Optional[Any]]]:
        """
        Create multiple strategy instances for batch testing.
        
        Args:
            strategy_classes: Dict mapping strategy name to class
            symbols: List of symbols to test
            config_overrides: Optional config overrides by strategy name
            verbose: Enable verbose logging
            
        Returns:
            Nested dict: {strategy_name: {symbol: strategy_instance}}
        """
        results = {}
        risk_manager = MockRiskManager()
        notification_service = MockNotificationService(verbose=verbose)
        
        for strategy_name, strategy_class in strategy_classes.items():
            results[strategy_name] = {}
            config = None
            
            # Apply config override if provided
            if config_overrides and strategy_name in config_overrides:
                config = config_overrides[strategy_name]
            
            for symbol in symbols:
                wrapper = StrategyWrapper(
                    strategy_class=strategy_class,
                    symbol=symbol,
                    config=config,
                    risk_manager=risk_manager,
                    notification_service=notification_service,
                    verbose=verbose
                )
                strategy = wrapper.instantiate()
                results[strategy_name][symbol] = strategy
        
        return results


class StrategyFactory:
    """Factory for creating strategy wrappers with consistent configuration"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.risk_manager = MockRiskManager()
        self.notification_service = MockNotificationService(verbose=verbose)
        self.config_cache = {}
    
    def create_wrapper(
        self,
        strategy_class: Type,
        symbol: str,
        config: Optional[Any] = None
    ) -> StrategyWrapper:
        """Create a strategy wrapper"""
        return StrategyWrapper(
            strategy_class=strategy_class,
            symbol=symbol,
            config=config,
            risk_manager=self.risk_manager,
            notification_service=self.notification_service,
            verbose=self.verbose
        )
    
    def create_strategy(
        self,
        strategy_class: Type,
        symbol: str,
        config: Optional[Any] = None
    ) -> Optional[Any]:
        """Create a strategy instance directly"""
        wrapper = self.create_wrapper(strategy_class, symbol, config)
        return wrapper.instantiate()
    
    def get_config_for_strategy(self, strategy_name: str) -> Optional[Any]:
        """Get or cache configuration for a strategy"""
        if strategy_name not in self.config_cache:
            self.config_cache[strategy_name] = get_default_config(strategy_name)
        return self.config_cache[strategy_name]
