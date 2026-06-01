"""
Trading Engine Module
=====================

Central orchestration and automation components for the trading system.

Components:
  - trading_engine.py: Central orchestrator for 5-stage pipeline
  - scheduler.py: Automated scheduler for autonomous trading
  - test_trading_system_integration.py: Comprehensive test suite

Usage:
    from app.engine.trading_engine import TradingEngine
    from app.engine.scheduler import TradingScheduler
    
    # Initialize engine
    engine = TradingEngine(
        screener=screener,
        validator=validator,
        regime_monitor=regime_monitor,
        executor=executor,
        profit_manager=profit_manager,
        position_tracker=position_tracker,
        risk_manager=risk_manager,
        notifications=notifications
    )
    
    # Start scheduler
    scheduler = TradingScheduler(engine, cycle_interval_minutes=5)
    scheduler.start()
    
    # Run cycles automatically every 5 minutes during market hours
"""

from app.engine.trading_engine import TradingEngine, CycleStatus, CycleMetrics
from app.engine.scheduler import TradingScheduler, SchedulerStatus

__all__ = [
    'TradingEngine',
    'CycleStatus',
    'CycleMetrics',
    'TradingScheduler',
    'SchedulerStatus'
]

__version__ = '1.0.0'
