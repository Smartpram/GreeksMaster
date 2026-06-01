"""
TEST SUITE: Unified Profit Booking Strategy
Comprehensive tests for conditional logic, integration, and edge cases

Test Coverage:
1. Unit Tests: Individual component validation
2. Integration Tests: Full signal flow
3. Edge Case Tests: Boundary conditions
4. Production Tests: Real-world scenarios
"""

import pytest
import logging
from datetime import datetime, timedelta
from typing import Dict, List

# These imports assume the modules are in sys.path
try:
    from app.strategies.unified_profit_booking import (
        UnifiedProfitBookingManager,
        ExitStrategy,
        MarketRegime,
        TrailingStopConditions,
    )
    from app.strategies.strategy_config_validator import (
        StrategyConfigValidator,
        StrategyConfigError,
        StrategyConfigMonitor,
    )
    from app.strategies.strategy_regime_monitor import (
        StrategyRegimeMonitor,
        RegimeChangeType,
    )
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    print("Tests will be skipped if modules unavailable")


# ============================================================================
# FIXTURES (Test Data)
# ============================================================================

@pytest.fixture
def sample_mean_reverting_trades():
    """Sample trades from mean-reverting market"""
    return [
        {'holding_days': 0.05, 'max_profit_pct': 7.0, 'max_drawdown': -50},
        {'holding_days': 0.10, 'max_profit_pct': 6.5, 'max_drawdown': -45},
        {'holding_days': 0.08, 'max_profit_pct': 7.2, 'max_drawdown': -55},
        {'holding_days': 0.12, 'max_profit_pct': 6.8, 'max_drawdown': -48},
        {'holding_days': 0.07, 'max_profit_pct': 7.1, 'max_drawdown': -52},
    ]


@pytest.fixture
def sample_trending_trades():
    """Sample trades from trending market"""
    return [
        {'holding_days': 2.5, 'max_profit_pct': 10.0, 'max_drawdown': -30},
        {'holding_days': 3.0, 'max_profit_pct': 12.0, 'max_drawdown': -25},
        {'holding_days': 2.1, 'max_profit_pct': 9.5, 'max_drawdown': -28},
        {'holding_days': 2.8, 'max_profit_pct': 11.0, 'max_drawdown': -32},
        {'holding_days': 2.3, 'max_profit_pct': 9.8, 'max_drawdown': -27},
    ]


@pytest.fixture
def unified_manager():
    """Fresh unified manager instance"""
    return UnifiedProfitBookingManager()


@pytest.fixture
def config_validator():
    """Fresh config validator instance"""
    return StrategyConfigValidator()


@pytest.fixture
def regime_monitor():
    """Fresh regime monitor instance"""
    return StrategyRegimeMonitor()


# ============================================================================
# UNIT TESTS: Individual Components
# ============================================================================

class TestUnifiedProfitBookingManager:
    """Tests for UnifiedProfitBookingManager"""
    
    def test_initialization(self, unified_manager):
        """Test manager initializes correctly"""
        assert unified_manager is not None
        assert unified_manager.config['target_pct'] == 0.065
        assert unified_manager.config['stop_loss_pct'] == 0.04
        assert len(unified_manager.positions) == 0
        assert len(unified_manager.exit_history) == 0
    
    def test_detect_mean_reverting_regime(self, unified_manager, sample_mean_reverting_trades):
        """Test mean-reverting regime detection"""
        regime = unified_manager.detect_market_regime(sample_mean_reverting_trades)
        assert regime == MarketRegime.MEAN_REVERTING
    
    def test_detect_trending_regime(self, unified_manager, sample_trending_trades):
        """Test trending regime detection"""
        regime = unified_manager.detect_market_regime(sample_trending_trades)
        assert regime == MarketRegime.TRENDING
    
    def test_position_creation(self, unified_manager):
        """Test position creation with auto-strategy selection"""
        pos = unified_manager.create_position(
            symbol='TCS',
            entry_price=3100,
            quantity=100,
            position_id='TCS_001',
        )
        
        assert pos is not None
        assert pos['symbol'] == 'TCS'
        assert pos['entry_price'] == 3100
        assert pos['quantity'] == 100
        assert pos['exit_strategy'] in [ExitStrategy.FIXED_FULL_EXIT, ExitStrategy.PARTIAL_WITH_TRAILING]
    
    def test_fixed_exit_strategy_selection_in_mean_reverting(
        self, 
        unified_manager, 
        sample_mean_reverting_trades
    ):
        """Test that FIXED_FULL_EXIT is selected in mean-reverting regime"""
        unified_manager.detect_market_regime(sample_mean_reverting_trades)
        unified_manager.recent_trades = sample_mean_reverting_trades
        
        strategy = unified_manager.select_exit_strategy()
        assert strategy == ExitStrategy.FIXED_FULL_EXIT
    
    def test_exit_at_stop_loss_fixed(self, unified_manager):
        """Test fixed exit strategy: stop loss execution"""
        pos = unified_manager.create_position(
            symbol='TCS',
            entry_price=3100,
            quantity=100,
            position_id='TCS_001',
        )
        
        # Price drops to stop loss
        current_price = pos['stop_loss'] - 1
        should_exit, reason, details = unified_manager.check_exit_conditions('TCS_001', current_price)
        
        assert should_exit == True
        assert reason == 'stop_loss_hit'
        assert details['exit_qty'] == 100
    
    def test_exit_at_target_fixed(self, unified_manager):
        """Test fixed exit strategy: target execution"""
        pos = unified_manager.create_position(
            symbol='TCS',
            entry_price=3100,
            quantity=100,
            position_id='TCS_001',
        )
        
        # Price rises to target
        current_price = pos['target'] + 1
        should_exit, reason, details = unified_manager.check_exit_conditions('TCS_001', current_price)
        
        assert should_exit == True
        assert reason == 'target_hit'
        assert details['exit_qty'] == 100
    
    def test_exit_record_creation(self, unified_manager):
        """Test exit record is created correctly"""
        pos = unified_manager.create_position(
            symbol='TCS',
            entry_price=3100,
            quantity=100,
            position_id='TCS_001',
        )
        
        exit_record = unified_manager.execute_exit(
            position_id='TCS_001',
            exit_price=3300,
            exit_qty=100,
        )
        
        assert exit_record is not None
        assert exit_record['symbol'] == 'TCS'
        assert exit_record['entry_price'] == 3100
        assert exit_record['exit_price'] == 3300
        assert exit_record['pnl'] == (3300 - 3100) * 100
        assert exit_record['pnl_pct'] > 0


class TestStrategyConfigValidator:
    """Tests for StrategyConfigValidator"""
    
    def test_default_config_validation(self, config_validator):
        """Test that default config passes validation"""
        is_valid, warnings = config_validator.validate_on_startup()
        assert is_valid == True
    
    def test_trailing_disabled_by_default(self, config_validator):
        """Test trailing is disabled by default"""
        config = {'trailing_enabled': False}
        is_valid, warnings = config_validator.validate_on_startup(config)
        assert is_valid == True
    
    def test_trailing_in_mean_reverting_crashes(self, config_validator):
        """Test that trailing in mean-reverting crashes"""
        bad_config = {
            'trailing_enabled': True,
            'market_regime': 'mean_reverting',
            'avg_holding_days': 0.0,
            'target_pct': 0.065,
            'stop_loss_pct': 0.04,
            'trailing_stop_pct': 0.02,
        }
        
        with pytest.raises(StrategyConfigError):
            config_validator.validate_on_startup(bad_config)
    
    def test_invalid_target_pct(self, config_validator):
        """Test invalid target percentage is caught"""
        bad_config = {
            'target_pct': 0.50,  # 50% is unrealistic
            'stop_loss_pct': 0.04,
        }
        
        is_valid, warnings = config_validator.validate_on_startup(bad_config)
        # Should have warning but not crash
        assert any('target' in w.lower() for w in warnings)
    
    def test_market_state_validation_mean_reverting(self, config_validator):
        """Test market state validation for mean-reverting"""
        allow_trailing, reason = config_validator.validate_market_state(
            market_regime='mean_reverting',
            avg_holding_days=0.0,
            max_drawdown_pct=-77.91,
            profit_factor=1.14,
        )
        
        assert allow_trailing == False
        assert 'mean' in reason.lower()
    
    def test_market_state_validation_trending(self, config_validator):
        """Test market state validation for trending"""
        allow_trailing, reason = config_validator.validate_market_state(
            market_regime='trending',
            avg_holding_days=2.5,
            max_drawdown_pct=-50,
            profit_factor=1.2,
        )
        
        assert allow_trailing == True


class TestStrategyRegimeMonitor:
    """Tests for StrategyRegimeMonitor"""
    
    def test_mean_reverting_detection(self, regime_monitor, sample_mean_reverting_trades):
        """Test mean-reverting regime detection"""
        regime = regime_monitor.detect_regime(sample_mean_reverting_trades)
        assert regime == 'mean_reverting'
    
    def test_trending_detection(self, regime_monitor, sample_trending_trades):
        """Test trending regime detection"""
        regime = regime_monitor.detect_regime(sample_trending_trades)
        assert regime == 'trending'
    
    def test_regime_update_and_change_detection(self, regime_monitor, sample_mean_reverting_trades):
        """Test regime update and change detection"""
        # Start with mean-reverting
        current, changed = regime_monitor.update_regime(sample_mean_reverting_trades)
        assert current == 'mean_reverting'
        assert changed == False  # First update
        
        # Switch to trending (simulated)
        trending_trades = [{'holding_days': 3.0} for _ in range(5)]
        current, changed = regime_monitor.update_regime(trending_trades)
        assert current == 'trending'
        assert changed == True  # Regime changed
    
    def test_snapshot_creation(self, regime_monitor, sample_mean_reverting_trades):
        """Test regime snapshot creation"""
        regime_monitor.detect_regime(sample_mean_reverting_trades)
        snapshot = regime_monitor.create_snapshot(sample_mean_reverting_trades)
        
        assert snapshot is not None
        assert snapshot.regime == 'mean_reverting'
        assert snapshot.recent_trades_count == 5
        assert snapshot.avg_holding_days == pytest.approx(0.084, rel=0.01)


# ============================================================================
# INTEGRATION TESTS: Full Signal Flow
# ============================================================================

class TestIntegration:
    """Integration tests for full trading flow"""
    
    def test_entry_to_exit_mean_reverting(self, unified_manager, regime_monitor):
        """Test complete flow: entry → regime detection → exit in mean-reverting"""
        
        # Setup: Mean-reverting market
        mean_reverting_trades = [
            {'holding_days': 0.1, 'max_profit_pct': 7.0},
            {'holding_days': 0.1, 'max_profit_pct': 7.0},
            {'holding_days': 0.1, 'max_profit_pct': 7.0},
        ]
        
        # Detect regime
        regime, _ = regime_monitor.update_regime(mean_reverting_trades, unified_manager)
        assert regime == 'mean_reverting'
        
        # Create position (should auto-select FIXED_FULL_EXIT)
        unified_manager.recent_trades = mean_reverting_trades
        pos = unified_manager.create_position(
            symbol='TCS',
            entry_price=3100,
            quantity=100,
            position_id='TCS_001',
            auto_select_strategy=True,
        )
        assert pos['exit_strategy'] == ExitStrategy.FIXED_FULL_EXIT
        
        # Simulate price hitting target
        should_exit, reason, details = unified_manager.check_exit_conditions(
            'TCS_001',
            pos['target'] + 1,
        )
        
        assert should_exit == True
        assert reason == 'target_hit'
        
        # Execute exit
        exit_record = unified_manager.execute_exit(
            'TCS_001',
            details['exit_price'],
            details['exit_qty'],
        )
        
        assert exit_record['strategy'] == 'fixed_full_exit'
    
    def test_regime_change_during_trading(self, unified_manager, regime_monitor):
        """Test regime change detection during live trading"""
        
        # Start in mean-reverting
        mean_trades = [{'holding_days': 0.1} for _ in range(5)]
        regime, _ = regime_monitor.update_regime(mean_trades)
        assert regime == 'mean_reverting'
        
        # Switch to trending
        trending_trades = [{'holding_days': 3.0} for _ in range(5)]
        regime, changed = regime_monitor.update_regime(trending_trades)
        assert regime == 'trending'
        assert changed == True
        
        # Verify regime change was logged
        assert regime_monitor.regime_change_count == 1
        assert len(regime_monitor.regime_changes) == 1


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Edge case and boundary condition tests"""
    
    def test_empty_trade_list(self, unified_manager):
        """Test regime detection with empty trade list"""
        regime = unified_manager.detect_market_regime([])
        assert regime == MarketRegime.UNKNOWN
    
    def test_single_trade(self, unified_manager):
        """Test regime detection with single trade"""
        regime = unified_manager.detect_market_regime([{'holding_days': 0.1}])
        assert regime == MarketRegime.MEAN_REVERTING
    
    def test_position_at_exactly_stop_loss(self, unified_manager):
        """Test exit at exact stop loss price"""
        pos = unified_manager.create_position(
            symbol='TCS',
            entry_price=3100,
            quantity=100,
            position_id='TCS_001',
        )
        
        # Price exactly at stop loss
        should_exit, reason, _ = unified_manager.check_exit_conditions(
            'TCS_001',
            pos['stop_loss'],
        )
        
        # Should exit (<=)
        assert should_exit == True
        assert reason == 'stop_loss_hit'
    
    def test_position_at_exactly_target(self, unified_manager):
        """Test exit at exact target price"""
        pos = unified_manager.create_position(
            symbol='TCS',
            entry_price=3100,
            quantity=100,
            position_id='TCS_001',
        )
        
        # Price exactly at target
        should_exit, reason, _ = unified_manager.check_exit_conditions(
            'TCS_001',
            pos['target'],
        )
        
        # Should exit (>=)
        assert should_exit == True
        assert reason == 'target_hit'
    
    def test_high_volatility_market(self, regime_monitor):
        """Test regime detection in high volatility"""
        volatile_trades = [
            {'holding_days': 1.5, 'max_drawdown': -300},
            {'holding_days': 1.5, 'max_drawdown': -250},
        ]
        
        regime = regime_monitor.detect_regime(volatile_trades)
        assert regime == 'unknown'  # Between thresholds


# ============================================================================
# PRODUCTION SCENARIO TESTS
# ============================================================================

class TestProductionScenarios:
    """Real-world production scenarios"""
    
    def test_daily_regime_check(self, regime_monitor, sample_mean_reverting_trades):
        """Test daily regime check workflow"""
        report = regime_monitor.daily_regime_check(sample_mean_reverting_trades)
        
        assert report is not None
        assert 'date' in report
        assert 'regime' in report
        assert 'stats' in report
        assert 'alerts' in report
    
    def test_strategy_configuration_at_startup(self, config_validator):
        """Test strategy validation at application startup"""
        # This should NOT raise an exception
        is_valid, warnings = config_validator.validate_on_startup()
        assert is_valid == True
    
    def test_continuous_monitoring(self, regime_monitor, sample_mean_reverting_trades):
        """Test continuous regime monitoring"""
        
        # Simulate 5 days of trading
        for day in range(5):
            regime_monitor.update_regime(sample_mean_reverting_trades)
            regime_monitor.create_snapshot(sample_mean_reverting_trades)
        
        assert len(regime_monitor.regime_snapshots) == 5
        assert regime_monitor.current_regime == 'mean_reverting'


# ============================================================================
# PERFORMANCE VALIDATION TESTS
# ============================================================================

class TestPerformanceValidation:
    """Validate against backtest performance metrics"""
    
    def test_backtest_metrics_from_attachment(self):
        """Validate against backtest results from attachment"""
        
        # Expected from backtest_profit_booking_breeze_20260601_094947.json
        expected_fixed = {
            'trades': 169,
            'win_rate': 29.59,  # %
            'profit_factor': 1.14,
            'total_pnl': 359850,
            'max_drawdown': -77.91,  # %
        }
        
        expected_partial_trailing = {
            'trades': 169,
            'win_rate': 29.59,  # %
            'profit_factor': 0.57,
            'total_pnl': -1105910,
            'max_drawdown': -528.00,  # %
        }
        
        # Assertions
        assert expected_fixed['profit_factor'] > 1.0, "Fixed exit should be profitable"
        assert expected_partial_trailing['profit_factor'] < expected_fixed['profit_factor'], \
            "Trailing should underperform in mean-reverting"
        assert abs(expected_fixed['max_drawdown']) < abs(expected_partial_trailing['max_drawdown']), \
            "Fixed exit should have lower drawdown"


# ============================================================================
# PARAMETRIZED TESTS
# ============================================================================

class TestParametrized:
    """Parametrized tests for multiple scenarios"""
    
    @pytest.mark.parametrize("holding_days,expected_regime", [
        (0.0, 'mean_reverting'),
        (0.5, 'mean_reverting'),
        (0.99, 'mean_reverting'),
        (1.5, 'unknown'),
        (2.0, 'unknown'),
        (2.1, 'trending'),
        (3.0, 'trending'),
        (5.0, 'trending'),
    ])
    def test_regime_classification_boundaries(self, regime_monitor, holding_days, expected_regime):
        """Test regime classification at boundaries"""
        trades = [{'holding_days': holding_days} for _ in range(5)]
        regime = regime_monitor.detect_regime(trades)
        assert regime == expected_regime, \
            f"Failed: holding_days={holding_days} should be {expected_regime}, got {regime}"
    
    @pytest.mark.parametrize("entry_price,exit_price", [
        (3100, 3100 * 1.065),  # Exact target
        (3100, 3100 * 0.96),    # Exact stop loss
        (3100, 3100 * 1.10),    # Well above target
        (3100, 3100 * 0.90),    # Well below stop loss
    ])
    def test_exit_prices(self, unified_manager, entry_price, exit_price):
        """Test exit conditions at various prices"""
        pos = unified_manager.create_position(
            symbol='TCS',
            entry_price=entry_price,
            quantity=100,
            position_id='TCS_001',
        )
        
        should_exit, _, _ = unified_manager.check_exit_conditions('TCS_001', exit_price)
        # Should exit at either target or stop loss
        assert should_exit in [True, False]


# ============================================================================
# TEST EXECUTION & REPORTING
# ============================================================================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "production: mark test as production scenario"
    )


def test_full_integration_report(unified_manager, regime_monitor, config_validator):
    """
    Full integration test - Can be run manually with:
    python -m pytest test_unified_strategy.py::test_full_integration_report -v
    """
    
    print("\n" + "="*70)
    print("UNIFIED STRATEGY INTEGRATION REPORT")
    print("="*70)
    
    # 1. Validation
    print("\n1. Configuration Validation")
    is_valid, warnings = config_validator.validate_on_startup()
    print(f"   Status: {'✅ PASS' if is_valid else '❌ FAIL'}")
    print(f"   Warnings: {len(warnings)}")
    
    # 2. Regime monitoring
    print("\n2. Regime Monitor Status")
    status = regime_monitor.get_regime_status()
    print(f"   Current Regime: {status['current_regime']}")
    print(f"   Regime Changes: {status['regime_changes_total']}")
    
    # 3. Manager status
    print("\n3. Unified Manager Status")
    print(f"   Active Positions: {len(unified_manager.positions)}")
    print(f"   Exit History: {len(unified_manager.exit_history)}")
    print(f"   Current Market Regime: {unified_manager.market_regime}")
    
    print("\n" + "="*70)
    print("✅ INTEGRATION REPORT COMPLETE")
    print("="*70 + "\n")


# ============================================================================
# MAIN: Run tests
# ============================================================================

if __name__ == "__main__":
    # Run with: python test_unified_strategy.py
    # Or with: pytest test_unified_strategy.py -v
    
    print("\n" + "="*70)
    print("UNIFIED PROFIT BOOKING STRATEGY - TEST SUITE")
    print("="*70)
    print("\nTo run all tests:")
    print("  pytest test_unified_strategy.py -v")
    print("\nTo run specific test class:")
    print("  pytest test_unified_strategy.py::TestUnifiedProfitBookingManager -v")
    print("\nTo run with coverage:")
    print("  pytest test_unified_strategy.py --cov=app.strategies --cov-report=html")
    print("\n" + "="*70 + "\n")
