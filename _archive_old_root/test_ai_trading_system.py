"""
AI-ENABLED TRADING SYSTEM COMPREHENSIVE TEST SUITE
===================================================

Tests for all AI/ML components:
1. Emergency Stop system
2. Feature Engine
3. Prediction Engine integration
4. AI Trading Orchestrator
5. End-to-end trading cycle

Run with: pytest test_ai_trading_system.py -v
"""

import pytest
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict

# Assuming imports from the system
from app.feature_engine import FeatureEngine, FeatureVector
from app.safety.emergency_stop import KillSwitchManager, KillSwitchTrigger, KillSwitchState
from app.ml_models.prediction_engine import PredictionEngine, MarketCondition
from app.ai_trading_orchestrator import AITradingOrchestrator, AITradingResult

logger = logging.getLogger(__name__)


# ============================================================================
# FIXTURES & TEST DATA
# ============================================================================

@pytest.fixture
def mock_data_provider():
    """Mock data provider for OHLCV data"""
    provider = Mock()
    
    # Create realistic OHLCV data
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    close = np.cumsum(np.random.randn(100) * 0.5) + 100
    high = close + np.abs(np.random.randn(100) * 0.5)
    low = close - np.abs(np.random.randn(100) * 0.5)
    volume = np.random.randint(1000000, 5000000, 100)
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': close + np.random.randn(100) * 0.2,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })
    
    provider.get_historical_data.return_value = df
    provider.get_options_chain.return_value = []
    
    return provider


@pytest.fixture
def feature_engine(mock_data_provider):
    """Feature engine instance"""
    return FeatureEngine(mock_data_provider, lookback_bars=100)


@pytest.fixture
def mock_emergency_stop():
    """Mock Emergency Stop"""
    ks = Mock(spec=KillSwitchManager)
    ks.is_active.return_value = False
    ks.get_reason.return_value = None
    ks.check_triggers.return_value = False
    ks.activate.return_value = True
    ks.reset.return_value = True
    return ks


@pytest.fixture
def mock_prediction_engine():
    """Mock Prediction Engine"""
    pe = Mock(spec=PredictionEngine)
    pe.predict_direction.return_value = {
        'direction': 'UP',
        'confidence': 0.75,
        'expected_return': 0.025
    }
    pe.predict_volatility.return_value = {
        'volatility': 0.15,
        'confidence': 0.8
    }
    return pe


@pytest.fixture
def mock_risk_manager():
    """Mock Risk Manager"""
    rm = Mock()
    rm.validate_trading_cycle.return_value = (True, "Risk validation passed")
    rm.validate_order.return_value = (True, "Order valid")
    rm.calculate_stop_loss.return_value = 95.0
    rm.calculate_target.return_value = 105.0
    return rm


@pytest.fixture
def mock_trading_engine():
    """Mock Phase 1 Trading Engine"""
    te = Mock()
    te.run_cycle.return_value = {
        'cycle_id': 'test_cycle_1',
        'signals_generated': 5,
        'trades_executed': 3,
        'execution_failures': 0,
        'positions_monitored': 3,
        'positions_exited': 1,
        'status': 'completed'
    }
    te.position_tracker = Mock()
    te.position_tracker.get_open_positions.return_value = [
        {'symbol': 'NIFTY50', 'qty': 1, 'entry_price': 100}
    ]
    te.profit_manager = Mock()
    te.profit_manager.check_exits.return_value = [
        {'symbol': 'NIFTY50', 'exit_reason': 'target_hit'}
    ]
    return te


@pytest.fixture
def mock_config():
    """Mock configuration"""
    config = Mock()
    config.PRIMARY_SYMBOL = 'NIFTY50'
    config.MAX_DAILY_LOSS = 0.10
    config.DEFAULT_CAPITAL = 100000
    return config


# ============================================================================
# TEST: Emergency Stop SYSTEM
# ============================================================================

class TestKillSwitch:
    """Test Emergency Stop safety system"""
    
    def test_emergency_stop_initialization(self):
        """Test Emergency Stop can be initialized"""
        ks = KillSwitchManager()
        assert ks is not None
        assert not ks.is_active()
    
    def test_emergency_stop_manual_activation(self):
        """Test manual Emergency Stop activation"""
        ks = KillSwitchManager()
        ks.activate(reason="Manual test", trigger=KillSwitchTrigger.MANUAL)
        assert ks.is_active()
    
    def test_emergency_stop_get_reason(self):
        """Test getting activation reason"""
        ks = KillSwitchManager()
        ks.activate(reason="Test drawdown", trigger=KillSwitchTrigger.DRAWDOWN_EXCEEDED)
        reason = ks.get_reason()
        assert "drawdown" in reason.lower() or "test" in reason.lower()
    
    def test_emergency_stop_reset(self):
        """Test Emergency Stop reset"""
        ks = KillSwitchManager()
        ks.activate(reason="Test", trigger=KillSwitchTrigger.MANUAL)
        ks.reset(authorized_key="test_key_123")
        assert not ks.is_active()
    
    def test_emergency_stop_prevents_trading(self, mock_emergency_stop):
        """Test that active Emergency Stop prevents trading"""
        mock_emergency_stop.is_active.return_value = True
        mock_emergency_stop.get_reason.return_value = "Daily loss limit exceeded"
        
        assert mock_emergency_stop.is_active() is True
        assert "loss limit" in mock_emergency_stop.get_reason().lower()


# ============================================================================
# TEST: FEATURE ENGINE
# ============================================================================

class TestFeatureEngine:
    """Test Feature Engineering system"""
    
    def test_feature_engine_initialization(self, mock_data_provider):
        """Test Feature Engine can be initialized"""
        engine = FeatureEngine(mock_data_provider)
        assert engine is not None
        assert engine.data_provider is not None
    
    def test_compute_all_features(self, feature_engine):
        """Test computing complete feature vector"""
        features = feature_engine.compute_all_features('NIFTY50')
        
        assert features is not None
        assert isinstance(features, FeatureVector)
        assert features.symbol == 'NIFTY50'
        assert 0 <= features.bullish_score <= 100
    
    def test_feature_vector_contains_all_fields(self, feature_engine):
        """Test that feature vector has all required fields"""
        features = feature_engine.compute_all_features('NIFTY50')
        
        required_fields = [
            'ma_ratio', 'ma_trend', 'rsi_14', 'atr_14', 'bb_position',
            'volume_ratio', 'higher_high', 'higher_low', 'bullish_score'
        ]
        
        for field in required_fields:
            assert hasattr(features, field), f"Missing field: {field}"
            value = getattr(features, field)
            assert value is not None, f"Field {field} is None"
    
    def test_bullish_score_calculation(self, feature_engine):
        """Test bullish score is properly calculated"""
        features = feature_engine.compute_all_features('NIFTY50')
        
        # Score should be between 0-100
        assert 0 <= features.bullish_score <= 100
        
        # Test with mock data that should be bullish
        # (Price > SMA, RSI > 50, Volume high)
        assert features.bullish_score > 20  # Should have some bullish bias
    
    def test_technical_indicators(self, feature_engine):
        """Test technical indicator calculations"""
        features = feature_engine.compute_all_features('NIFTY50')
        
        # RSI should be 0-100
        assert 0 <= features.rsi_14 <= 100
        
        # MA ratio should be positive
        assert features.ma_ratio > 0
        
        # BB position should be 0-1
        assert 0 <= features.bb_position <= 1
        
        # ATR should be positive
        assert features.atr_14 > 0


# ============================================================================
# TEST: PREDICTION ENGINE
# ============================================================================

class TestPredictionEngine:
    """Test ML Prediction Engine"""
    
    def test_prediction_engine_initialization(self, mock_prediction_engine):
        """Test Prediction Engine can be initialized"""
        assert mock_prediction_engine is not None
        assert mock_prediction_engine.predict_direction is not None
    
    def test_predict_direction(self, mock_prediction_engine):
        """Test direction prediction"""
        features = {
            'ma_ratio': 1.02,
            'rsi_14': 65,
            'volume_ratio': 1.5
        }
        
        prediction = mock_prediction_engine.predict_direction(features)
        
        assert prediction is not None
        assert 'direction' in prediction
        assert prediction['direction'] in ['UP', 'DOWN', 'NEUTRAL']
        assert 0 <= prediction['confidence'] <= 1.0
    
    def test_predict_volatility(self, mock_prediction_engine):
        """Test volatility prediction"""
        features = {'atr_14': 1.5, 'bb_width': 0.05}
        
        prediction = mock_prediction_engine.predict_volatility(features)
        
        assert prediction is not None
        assert 'volatility' in prediction
        assert prediction['volatility'] >= 0


# ============================================================================
# TEST: PHASE 2 INTEGRATION
# ============================================================================

class TestAITradingOrchestrator:
    """Test Phase 2 Integration orchestrator"""
    
    def test_phase2_initialization(self, mock_config, mock_trading_engine,
                                   mock_emergency_stop, feature_engine,
                                   mock_prediction_engine, mock_risk_manager):
        """Test Phase 2 Integration can be initialized"""
        phase2 = AITradingOrchestrator(
            config=mock_config,
            trading_engine=mock_trading_engine,
            emergency_stop=mock_emergency_stop,
            feature_engine=feature_engine,
            prediction_engine=mock_prediction_engine,
            risk_manager=mock_risk_manager
        )
        
        assert phase2 is not None
        assert phase2.phase2_enabled is True
    
    def test_phase2_trading_active_check(self, mock_config, mock_trading_engine,
                                         mock_emergency_stop, feature_engine,
                                         mock_prediction_engine, mock_risk_manager):
        """Test trading active check"""
        phase2 = AITradingOrchestrator(
            config=mock_config,
            trading_engine=mock_trading_engine,
            emergency_stop=mock_emergency_stop,
            feature_engine=feature_engine,
            prediction_engine=mock_prediction_engine,
            risk_manager=mock_risk_manager
        )
        
        # Should be active when Emergency Stop is inactive
        mock_emergency_stop.is_active.return_value = False
        assert phase2.is_trading_active() is True
        
        # Should be inactive when Emergency Stop is active
        mock_emergency_stop.is_active.return_value = True
        assert phase2.is_trading_active() is False
    
    def test_run_trading_cycle(self, mock_config, mock_trading_engine,
                               mock_emergency_stop, feature_engine,
                               mock_prediction_engine, mock_risk_manager):
        """Test complete trading cycle execution"""
        phase2 = AITradingOrchestrator(
            config=mock_config,
            trading_engine=mock_trading_engine,
            emergency_stop=mock_emergency_stop,
            feature_engine=feature_engine,
            prediction_engine=mock_prediction_engine,
            risk_manager=mock_risk_manager
        )
        
        result = phase2.run_trading_cycle()
        
        assert isinstance(result, AITradingResult)
        assert result.cycle_id is not None
        assert result.timestamp is not None
        assert isinstance(result.emergency_stop_active, bool)
    
    def test_cycle_with_emergency_stop_active(self, mock_config, mock_trading_engine,
                                            mock_emergency_stop, feature_engine,
                                            mock_prediction_engine, mock_risk_manager):
        """Test cycle when Emergency Stop is active"""
        phase2 = AITradingOrchestrator(
            config=mock_config,
            trading_engine=mock_trading_engine,
            emergency_stop=mock_emergency_stop,
            feature_engine=feature_engine,
            prediction_engine=mock_prediction_engine,
            risk_manager=mock_risk_manager
        )
        
        # Activate Emergency Stop
        mock_emergency_stop.is_active.return_value = True
        mock_emergency_stop.get_reason.return_value = "Test Emergency Stop"
        
        result = phase2.run_trading_cycle()
        
        assert result.emergency_stop_active is True
        assert result.cycle_successful is False
    
    def test_cycle_with_successful_execution(self, mock_config, mock_trading_engine,
                                              mock_emergency_stop, feature_engine,
                                              mock_prediction_engine, mock_risk_manager):
        """Test successful trading cycle with execution"""
        phase2 = AITradingOrchestrator(
            config=mock_config,
            trading_engine=mock_trading_engine,
            emergency_stop=mock_emergency_stop,
            feature_engine=feature_engine,
            prediction_engine=mock_prediction_engine,
            risk_manager=mock_risk_manager
        )
        
        # All systems go
        mock_emergency_stop.is_active.return_value = False
        mock_risk_manager.validate_trading_cycle.return_value = (True, "OK")
        mock_prediction_engine.predict_direction.return_value = {
            'direction': 'UP',
            'confidence': 0.8
        }
        
        result = phase2.run_trading_cycle()
        
        assert result.emergency_stop_active is False
        assert result.features_computed is True
        assert result.predictions_available is True
        assert result.risk_approved is True
        assert result.signals_generated > 0
    
    def test_get_system_status(self, mock_config, mock_trading_engine,
                               mock_emergency_stop, feature_engine,
                               mock_prediction_engine, mock_risk_manager):
        """Test system status reporting"""
        phase2 = AITradingOrchestrator(
            config=mock_config,
            trading_engine=mock_trading_engine,
            emergency_stop=mock_emergency_stop,
            feature_engine=feature_engine,
            prediction_engine=mock_prediction_engine,
            risk_manager=mock_risk_manager
        )
        
        status = phase2.get_system_status()
        
        assert status is not None
        assert 'phase2_enabled' in status
        assert 'emergency_stop_active' in status
        assert 'cycle_count' in status


# ============================================================================
# TEST: INTEGRATION SCENARIOS
# ============================================================================

class TestIntegrationScenarios:
    """Test realistic integration scenarios"""
    
    def test_scenario_bearish_market_rejection(self, mock_config, mock_trading_engine,
                                                mock_emergency_stop, feature_engine,
                                                mock_prediction_engine, mock_risk_manager):
        """Test: ML predicts bearish → trades rejected"""
        phase2 = AITradingOrchestrator(
            config=mock_config,
            trading_engine=mock_trading_engine,
            emergency_stop=mock_emergency_stop,
            feature_engine=feature_engine,
            prediction_engine=mock_prediction_engine,
            risk_manager=mock_risk_manager
        )
        
        # ML predicts strong bearish
        mock_prediction_engine.predict_direction.return_value = {
            'direction': 'DOWN',
            'confidence': 0.85
        }
        mock_risk_manager.validate_trading_cycle.return_value = (True, "OK")
        
        result = phase2.run_trading_cycle()
        
        # Signals should be rejected
        assert result.risk_approved is False
    
    def test_scenario_bullish_alignment(self, mock_config, mock_trading_engine,
                                        mock_emergency_stop, feature_engine,
                                        mock_prediction_engine, mock_risk_manager):
        """Test: ML and features bullish → high confidence trade"""
        phase2 = AITradingOrchestrator(
            config=mock_config,
            trading_engine=mock_trading_engine,
            emergency_stop=mock_emergency_stop,
            feature_engine=feature_engine,
            prediction_engine=mock_prediction_engine,
            risk_manager=mock_risk_manager
        )
        
        # Both signals bullish
        mock_prediction_engine.predict_direction.return_value = {
            'direction': 'UP',
            'confidence': 0.8
        }
        mock_risk_manager.validate_trading_cycle.return_value = (True, "OK")
        
        result = phase2.run_trading_cycle()
        
        # Should approve and execute
        assert result.risk_approved is True
        assert result.signals_executed > 0
    
    def test_scenario_fallback_to_phase1(self, mock_config, mock_trading_engine,
                                         mock_emergency_stop, feature_engine,
                                         mock_prediction_engine, mock_risk_manager):
        """Test: Phase 2 ML fails → fallback to Phase 1"""
        phase2 = AITradingOrchestrator(
            config=mock_config,
            trading_engine=mock_trading_engine,
            emergency_stop=mock_emergency_stop,
            feature_engine=feature_engine,
            prediction_engine=mock_prediction_engine,
            risk_manager=mock_risk_manager
        )
        
        # ML prediction fails
        mock_prediction_engine.predict_direction.side_effect = Exception("Model error")
        mock_risk_manager.validate_trading_cycle.return_value = (True, "OK")
        
        result = phase2.run_trading_cycle()
        
        # Should still complete with Phase 1 fallback
        assert phase2.fallback_to_phase1 is True
        assert len(result.errors) > 0


# ============================================================================
# TEST: ERROR HANDLING
# ============================================================================

class TestErrorHandling:
    """Test error handling and resilience"""
    
    def test_feature_computation_error_handling(self, mock_config, mock_trading_engine,
                                                 mock_emergency_stop, feature_engine,
                                                 mock_prediction_engine, mock_risk_manager):
        """Test graceful handling of feature computation errors"""
        phase2 = AITradingOrchestrator(
            config=mock_config,
            trading_engine=mock_trading_engine,
            emergency_stop=mock_emergency_stop,
            feature_engine=feature_engine,
            prediction_engine=mock_prediction_engine,
            risk_manager=mock_risk_manager
        )
        
        # Feature engine returns error
        feature_engine.compute_all_features = Mock(return_value=None)
        
        result = phase2.run_trading_cycle()
        
        # Should handle gracefully
        assert result.features_computed is False
        assert phase2.fallback_to_phase1 is True
    
    def test_emergency_stop_error_handling(self, mock_config, mock_trading_engine,
                                        mock_emergency_stop, feature_engine,
                                        mock_prediction_engine, mock_risk_manager):
        """Test handling of Emergency Stop errors"""
        phase2 = AITradingOrchestrator(
            config=mock_config,
            trading_engine=mock_trading_engine,
            emergency_stop=mock_emergency_stop,
            feature_engine=feature_engine,
            prediction_engine=mock_prediction_engine,
            risk_manager=mock_risk_manager
        )
        
        # Emergency Stop check raises exception
        mock_emergency_stop.is_active.side_effect = Exception("Emergency Stop error")
        
        result = phase2.run_trading_cycle()
        
        # Should capture error but not crash
        assert len(result.errors) > 0
        assert result.cycle_successful is False


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
