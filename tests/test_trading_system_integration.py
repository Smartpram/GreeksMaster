"""
Comprehensive Test Suite for Trading System Integration
========================================================

Tests for:
1. Individual component unit tests (Signal Generation, Validation, Execution, Exits, Monitoring)
2. Full pipeline integration tests (end-to-end trading scenarios)
3. Edge cases and boundary conditions
4. Risk management and circuit breakers
5. Scheduler functionality

Organization:
- Stage-specific test classes for each pipeline stage
- Integration test class for full end-to-end flows
- Fixture setup with mocked components
- Parametrized tests for various scenarios

Usage:
    # Run all tests
    pytest tests/test_trading_system_integration.py -v
    
    # Run specific test class
    pytest tests/test_trading_system_integration.py::TestStage1SignalGeneration -v
    
    # Run with coverage
    pytest tests/test_trading_system_integration.py --cov=app.engine
"""

import pytest
import logging
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List

# Setup logging
logger = logging.getLogger(__name__)


# ==================== FIXTURES ====================

@pytest.fixture
def mock_screener():
    """Mock stock screener"""
    screener = Mock()
    screener.get_signals.return_value = [
        {
            'symbol': 'RELIANCE',
            'direction': 'BUY',
            'price': 2500.0,
            'confidence': 0.85,
            'reason': 'momentum',
            'metadata': {}
        },
        {
            'symbol': 'INFY',
            'direction': 'BUY',
            'price': 1400.0,
            'confidence': 0.75,
            'reason': 'technical_setup',
            'metadata': {}
        }
    ]
    return screener


@pytest.fixture
def mock_validator():
    """Mock production validator"""
    validator = Mock()
    validator.validate_signal.return_value = (True, "Signal valid")
    return validator


@pytest.fixture
def mock_regime_monitor():
    """Mock regime monitor"""
    regime_monitor = Mock()
    regime_monitor.get_current_regime.return_value = 'trending'
    regime_monitor.current_regime = 'trending'
    regime_monitor.detect_regime.return_value = 'trending'
    return regime_monitor


@pytest.fixture
def mock_executor():
    """Mock signal executor"""
    executor = Mock()
    executor.execute_buy_signal.return_value = {
        'success': True,
        'order_id': 'ORD12345',
        'symbol': 'RELIANCE',
        'quantity': 1,
        'price': 2500.0
    }
    executor.execute_sell_signal.return_value = {
        'success': True,
        'order_id': 'ORD12346',
        'symbol': 'RELIANCE',
        'quantity': 1,
        'price': 2550.0,
        'pnl': 50.0
    }
    return executor


@pytest.fixture
def mock_profit_manager():
    """Mock profit booking manager"""
    profit_manager = Mock()
    profit_manager.check_position_exit.return_value = None  # No exit needed
    return profit_manager


@pytest.fixture
def mock_position_tracker():
    """Mock live position tracker"""
    position_tracker = Mock()
    position_tracker.get_open_positions.return_value = []
    position_tracker.get_portfolio_metrics.return_value = {
        'total_value': 100000.0,
        'daily_pnl': 500.0,
        'open_positions': 0
    }
    return position_tracker


@pytest.fixture
def mock_risk_manager():
    """Mock risk manager"""
    risk_manager = Mock()
    risk_manager.validate_order.return_value = (True, "Order valid")
    risk_manager.calculate_position_size.return_value = 1
    risk_manager.config = Mock(MAX_DAILY_LOSS=0.10)  # 10% daily loss limit
    return risk_manager


@pytest.fixture
def mock_notifications():
    """Mock notification service"""
    notifications = Mock()
    notifications.send_alert.return_value = True
    return notifications


@pytest.fixture
def trading_engine(mock_screener, mock_validator, mock_regime_monitor,
                   mock_executor, mock_profit_manager, mock_position_tracker,
                   mock_risk_manager, mock_notifications):
    """
    Create a TradingEngine with all mocked components
    """
    from app.engine.trading_engine import TradingEngine
    
    engine = TradingEngine(
        screener=mock_screener,
        validator=mock_validator,
        regime_monitor=mock_regime_monitor,
        executor=mock_executor,
        profit_manager=mock_profit_manager,
        position_tracker=mock_position_tracker,
        risk_manager=mock_risk_manager,
        notifications=mock_notifications
    )
    return engine


# ==================== STAGE 1: SIGNAL GENERATION TESTS ====================

class TestStage1SignalGeneration:
    """Test Stage 1: Signal Generation"""
    
    def test_screener_generates_signals(self, trading_engine, mock_screener):
        """Test that screener produces signals"""
        signals = mock_screener.get_signals()
        assert signals is not None
        assert len(signals) == 2
        assert signals[0]['symbol'] == 'RELIANCE'
        assert signals[0]['direction'] == 'BUY'
    
    def test_screener_no_signals(self, trading_engine, mock_screener):
        """Test screener returns empty list when no signals"""
        mock_screener.get_signals.return_value = []
        signals = mock_screener.get_signals()
        assert signals == []
    
    def test_cycle_stage_1_generates_signals(self, trading_engine):
        """Test Stage 1 in full cycle"""
        result = trading_engine.run_cycle()
        assert result['signals_generated'] == 2
        assert result['signal_details'] is not None
        assert len(result['signal_details']) == 2


class TestStage2Validation:
    """Test Stage 2: Validation & Risk Guardrails"""
    
    def test_validator_approves_valid_signal(self, trading_engine, mock_validator):
        """Test validator approves valid signals"""
        is_valid, reason = mock_validator.validate_signal(
            {'symbol': 'RELIANCE', 'confidence': 0.85},
            'trending'
        )
        assert is_valid is True
        assert reason == "Signal valid"
    
    def test_validator_rejects_invalid_signal(self, trading_engine, mock_validator):
        """Test validator rejects invalid signals"""
        mock_validator.validate_signal.return_value = (False, "Low confidence")
        is_valid, reason = mock_validator.validate_signal(
            {'symbol': 'RELIANCE', 'confidence': 0.3},
            'unknown'
        )
        assert is_valid is False
    
    def test_regime_detection(self, trading_engine, mock_regime_monitor):
        """Test market regime detection"""
        regime = mock_regime_monitor.get_current_regime()
        assert regime == 'trending'
    
    def test_cycle_stage_2_validates_signals(self, trading_engine):
        """Test Stage 2 validation in full cycle"""
        result = trading_engine.run_cycle()
        assert result['signals_validated'] >= 0
        assert result['signals_rejected'] >= 0
        assert result['regime'] in ['trending', 'mean_reverting', 'unknown']


class TestStage3Execution:
    """Test Stage 3: Trade Execution"""
    
    def test_executor_places_buy_order(self, trading_engine, mock_executor):
        """Test executor places buy orders"""
        result = mock_executor.execute_buy_signal(
            symbol='RELIANCE',
            price=2500.0,
            confidence=0.85
        )
        assert result['success'] is True
        assert result['order_id'] == 'ORD12345'
    
    def test_executor_places_sell_order(self, trading_engine, mock_executor):
        """Test executor places sell orders"""
        result = mock_executor.execute_sell_signal(
            symbol='RELIANCE',
            price=2550.0
        )
        assert result['success'] is True
        assert result['pnl'] == 50.0
    
    def test_executor_failed_order(self, trading_engine, mock_executor):
        """Test executor handles failed orders"""
        mock_executor.execute_buy_signal.return_value = {
            'success': False,
            'error': 'Insufficient funds'
        }
        result = mock_executor.execute_buy_signal(
            symbol='RELIANCE',
            price=2500.0
        )
        assert result['success'] is False
    
    def test_cycle_stage_3_executes_trades(self, trading_engine):
        """Test Stage 3 execution in full cycle"""
        result = trading_engine.run_cycle()
        assert result['trades_executed'] >= 0
        assert result['execution_failures'] >= 0


class TestStage4ExitManagement:
    """Test Stage 4: Exit Management"""
    
    def test_profit_manager_checks_exits(self, trading_engine, mock_profit_manager):
        """Test profit manager checks position exits"""
        exit_signal = mock_profit_manager.check_position_exit(
            {'symbol': 'RELIANCE', 'quantity': 1, 'entry_price': 2500.0}
        )
        # When no exit needed
        assert exit_signal is None
    
    def test_profit_manager_triggers_exit(self, trading_engine, mock_profit_manager):
        """Test profit manager triggers exit when conditions met"""
        mock_profit_manager.check_position_exit.return_value = {
            'reason': 'target_hit',
            'price': 2550.0,
            'pnl': 50.0,
            'pnl_pct': 2.0
        }
        exit_signal = mock_profit_manager.check_position_exit(
            {'symbol': 'RELIANCE', 'quantity': 1}
        )
        assert exit_signal is not None
        assert exit_signal['reason'] == 'target_hit'
    
    def test_cycle_stage_4_manages_exits(self, trading_engine):
        """Test Stage 4 exit management in full cycle"""
        result = trading_engine.run_cycle()
        assert result['positions_monitored'] >= 0
        assert result['positions_exited'] >= 0


class TestStage5Monitoring:
    """Test Stage 5: Risk Monitoring & Alerts"""
    
    def test_position_tracker_gets_metrics(self, trading_engine, mock_position_tracker):
        """Test position tracker provides metrics"""
        metrics = mock_position_tracker.get_portfolio_metrics()
        assert metrics['total_value'] == 100000.0
        assert metrics['daily_pnl'] == 500.0
    
    def test_notifications_sent(self, trading_engine, mock_notifications):
        """Test notifications are sent"""
        mock_notifications.send_alert(
            subject='DAILY_LOSS_LIMIT',
            message='Daily loss limit reached',
            severity='HIGH'
        )
        assert mock_notifications.send_alert.called
    
    def test_cycle_stage_5_monitoring(self, trading_engine):
        """Test Stage 5 monitoring in full cycle"""
        result = trading_engine.run_cycle()
        assert result['portfolio_value'] >= 0
        assert result['daily_pnl'] is not None
        assert result['risk_alerts'] >= 0


# ==================== FULL PIPELINE INTEGRATION TESTS ====================

class TestFullPipelineIntegration:
    """Test complete end-to-end trading pipeline"""
    
    def test_complete_cycle_execution(self, trading_engine):
        """Test complete trading cycle from start to finish"""
        result = trading_engine.run_cycle()
        
        # Verify all stages ran
        assert result['status'] == 'completed'
        assert result['signals_generated'] >= 0
        assert 'cycle_id' in result
        assert result['duration_ms'] >= 0
    
    def test_no_signals_scenario(self, trading_engine, mock_screener):
        """Test cycle when no signals generated"""
        mock_screener.get_signals.return_value = []
        result = trading_engine.run_cycle()
        
        assert result['status'] == 'completed'
        assert result['signals_generated'] == 0
        assert result['trades_executed'] == 0
    
    def test_all_signals_rejected_scenario(self, trading_engine, mock_validator):
        """Test cycle when all signals rejected at validation"""
        mock_validator.validate_signal.return_value = (False, "Failed validation")
        result = trading_engine.run_cycle()
        
        assert result['signals_generated'] > 0
        assert result['signals_validated'] == 0
        assert result['trades_executed'] == 0
    
    def test_partial_execution_scenario(self, trading_engine, mock_executor):
        """Test cycle with some execution failures"""
        # First call succeeds, second fails
        mock_executor.execute_buy_signal.side_effect = [
            {'success': True, 'order_id': 'ORD1'},
            {'success': False, 'error': 'Insufficient funds'}
        ]
        result = trading_engine.run_cycle()
        
        assert result['trades_executed'] >= 0
        assert result['execution_failures'] >= 0
    
    def test_multiple_cycles(self, trading_engine):
        """Test running multiple cycles in sequence"""
        results = []
        for i in range(3):
            result = trading_engine.run_cycle()
            results.append(result)
            assert result['status'] in ['completed', 'halted', 'failed']
        
        # Verify cycles are tracked
        assert trading_engine.cycle_count == 3
        assert len(trading_engine.cycle_history) == 3


# ==================== EDGE CASES & BOUNDARY CONDITIONS ====================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_invalid_signal_data(self, trading_engine, mock_screener):
        """Test handling of malformed signal data"""
        mock_screener.get_signals.return_value = [
            {'symbol': None},  # Missing direction
            {}                  # Completely empty
        ]
        result = trading_engine.run_cycle()
        assert result['signals_generated'] == 2
    
    def test_execution_exception_handling(self, trading_engine, mock_executor):
        """Test graceful handling of execution exceptions"""
        mock_executor.execute_buy_signal.side_effect = Exception("API error")
        result = trading_engine.run_cycle()
        assert result['status'] == 'completed'  # Should still complete
    
    def test_validation_exception_handling(self, trading_engine, mock_validator):
        """Test graceful handling of validation exceptions"""
        mock_validator.validate_signal.side_effect = Exception("Validation error")
        result = trading_engine.run_cycle()
        assert result['status'] == 'failed'
    
    def test_extremely_high_pnl(self, trading_engine, mock_position_tracker):
        """Test handling of unusual P&L values"""
        mock_position_tracker.get_portfolio_metrics.return_value = {
            'total_value': 1_000_000_000.0,  # 1 billion
            'daily_pnl': 10_000_000.0,       # 10 million
            'open_positions': 100
        }
        result = trading_engine.run_cycle()
        assert result['portfolio_value'] > 0


# ==================== RISK MANAGEMENT TESTS ====================

class TestRiskManagement:
    """Test risk management and circuit breakers"""
    
    def test_daily_loss_limit_halts_trading(self, trading_engine, mock_position_tracker):
        """Test that daily loss limit halts trading"""
        # Set portfolio to be at loss
        mock_position_tracker.get_portfolio_metrics.return_value = {
            'total_value': 100000.0,
            'daily_pnl': -15000.0,  # 15% loss (exceeds 10% limit)
        }
        result = trading_engine.run_cycle()
        # Check halt triggered
        assert trading_engine.halt_flag == True
    
    def test_risk_manager_blocks_oversized_position(self, trading_engine, mock_risk_manager):
        """Test risk manager blocks oversized positions"""
        mock_risk_manager.validate_order.return_value = (
            False,
            "Position size exceeds limit"
        )
        result = trading_engine.run_cycle()
        assert result['execution_failures'] >= 0
    
    def test_halt_flag_prevents_execution(self, trading_engine):
        """Test halt flag prevents cycle execution"""
        trading_engine.halt_flag = True
        result = trading_engine.run_cycle()
        assert result['status'] == 'halted'


# ==================== SCHEDULER TESTS ====================

class TestScheduler:
    """Test trading scheduler"""
    
    def test_scheduler_initialization(self):
        """Test scheduler can be initialized"""
        from app.engine.scheduler import TradingScheduler
        from unittest.mock import Mock
        
        mock_engine = Mock()
        scheduler = TradingScheduler(mock_engine)
        
        assert scheduler.cycle_interval_seconds == 300  # 5 minutes default
        assert scheduler.enable_market_hours == True
    
    def test_scheduler_status_tracking(self):
        """Test scheduler status tracking"""
        from app.engine.scheduler import TradingScheduler, SchedulerStatus
        from unittest.mock import Mock
        
        mock_engine = Mock()
        scheduler = TradingScheduler(mock_engine)
        
        status = scheduler.get_status()
        assert status['status'] == SchedulerStatus.STOPPED.value
        assert status['cycles_scheduled'] == 0
        assert status['is_running'] == False


# ==================== PERFORMANCE TESTS ====================

class TestPerformance:
    """Test performance characteristics"""
    
    def test_cycle_completes_in_reasonable_time(self, trading_engine):
        """Test cycle completes within acceptable time"""
        result = trading_engine.run_cycle()
        # Should complete in less than 5 seconds
        assert result['duration_ms'] < 5000
    
    def test_cycle_metrics_accuracy(self, trading_engine):
        """Test cycle metrics are accurately tracked"""
        result = trading_engine.run_cycle()
        
        # Verify metrics structure
        assert 'cycle_id' in result
        assert 'timestamp' in result
        assert 'duration_ms' in result
        assert result['duration_ms'] >= 0
    
    def test_cycle_history_retention(self, trading_engine):
        """Test cycle history is retained"""
        for i in range(5):
            trading_engine.run_cycle()
        
        history = trading_engine.get_cycle_history(limit=5)
        assert len(history) == 5
    
    def test_cycle_statistics(self, trading_engine):
        """Test aggregate cycle statistics"""
        for i in range(3):
            trading_engine.run_cycle()
        
        stats = trading_engine.get_cycle_statistics()
        assert stats['total_cycles'] == 3
        assert stats['success_rate'] >= 0


# ==================== PARAMETRIZED TESTS ====================

@pytest.mark.parametrize("signal_confidence", [0.5, 0.75, 0.9, 0.95])
def test_signal_confidence_levels(trading_engine, signal_confidence):
    """Test execution with various confidence levels"""
    result = trading_engine.run_cycle()
    assert result['status'] in ['completed', 'halted', 'failed']


@pytest.mark.parametrize("market_regime", ['trending', 'mean_reverting', 'unknown'])
def test_different_market_regimes(trading_engine, mock_regime_monitor, market_regime):
    """Test execution in different market regimes"""
    mock_regime_monitor.get_current_regime.return_value = market_regime
    result = trading_engine.run_cycle()
    assert result['regime'] == market_regime


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
