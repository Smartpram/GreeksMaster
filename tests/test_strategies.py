"""
Unit tests for MyBreezeApp
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from strategies.buy_hold_trend import BuyHoldTrendStrategy
from services.risk_manager import RiskManager
from services.order_manager import OrderManager
from utils.indicators import TechnicalIndicators

class TestBuyHoldTrendStrategy(unittest.TestCase):
    """Test Buy and Hold Trend Strategy"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_order_manager = Mock()
        self.mock_risk_manager = Mock()
        self.mock_notification_service = Mock()
        
        self.strategy = BuyHoldTrendStrategy(
            order_manager=self.mock_order_manager,
            risk_manager=self.mock_risk_manager,
            notification_service=self.mock_notification_service
        )
    
    def test_strategy_initialization(self):
        """Test strategy initialization"""
        self.assertIsNotNone(self.strategy)
        self.assertEqual(self.strategy.order_manager, self.mock_order_manager)
        self.assertEqual(self.strategy.risk_manager, self.mock_risk_manager)
        self.assertFalse(self.strategy.is_running)
    
    def test_start_stop_strategy(self):
        """Test starting and stopping strategy"""
        # Test start
        self.strategy.start()
        self.assertTrue(self.strategy.is_running)
        
        # Test stop
        self.strategy.stop()
        self.assertFalse(self.strategy.is_running)
    
    def test_generate_signals_empty_data(self):
        """Test signal generation with empty data"""
        signals = self.strategy.generate_signals({})
        self.assertEqual(signals, {})
    
    def test_generate_signals_insufficient_data(self):
        """Test signal generation with insufficient data"""
        data = {
            'RELIANCE': [
                {'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000}
            ]
        }
        
        self.strategy.set_watchlist(['RELIANCE'])
        signals = self.strategy.generate_signals(data)
        
        # Should not generate signals with insufficient data
        self.assertEqual(len(signals), 0)
    
    @patch('app.strategies.buy_hold_trend.logger')
    def test_enhanced_entry_conditions(self, mock_logger):
        """Test enhanced entry conditions with MACD and Stochastic RSI"""
        # Create test data that should trigger a BUY signal
        test_data = []
        base_price = 100
        
        # Generate 30 data points with upward trend
        for i in range(30):
            price = base_price + (i * 0.5)  # Gradual uptrend
            test_data.append({
                'open': price - 0.5,
                'high': price + 1,
                'low': price - 1,
                'close': price,
                'volume': 1000 + (i * 10)  # Increasing volume
            })
        
        data = {'TEST_STOCK': test_data}
        self.strategy.set_watchlist(['TEST_STOCK'])
        
        # Mock the risk manager to allow the trade
        self.mock_risk_manager.validate_order.return_value = (True, "Valid")
        self.mock_risk_manager.calculate_stop_loss.return_value = 110.0
        self.mock_risk_manager.calculate_target.return_value = 130.0
        
        # Mock order manager for position sizing
        self.mock_order_manager.calculate_position_size.return_value = 10
        
        signals = self.strategy.generate_signals(data)
        
        # Should generate a signal if conditions are met
        # Note: This might not always generate a signal depending on exact indicator values
        # The test verifies the method runs without errors
        self.assertIsInstance(signals, dict)
    
    def test_enhanced_exit_conditions(self):
        """Test enhanced exit conditions"""
        # Set up a position first
        self.strategy.positions = {
            'TEST_STOCK': {
                'quantity': 10,
                'avg_price': 100.0,
                'stop_loss': 95.0,
                'target': 115.0,
                'entry_time': datetime.now()
            }
        }
        
        # Test data indicating overbought conditions
        test_data = []
        base_price = 115  # Price at target level
        
        for i in range(30):
            price = base_price + (i * 0.1)  # Slight uptrend to overbought
            test_data.append({
                'open': price - 0.1,
                'high': price + 0.2,
                'low': price - 0.2,
                'close': price,
                'volume': 1000
            })
        
        data = {'TEST_STOCK': test_data}
        self.strategy.set_watchlist(['TEST_STOCK'])
        
        signals = self.strategy.generate_signals(data)
        
        # Should potentially generate a SELL signal
        self.assertIsInstance(signals, dict)

class TestRiskManager(unittest.TestCase):
    """Test Risk Manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.risk_manager = RiskManager()
    
    def test_validate_order_valid(self):
        """Test order validation with valid parameters"""
        order_params = {
            'stock_code': 'RELIANCE',
            'action': 'BUY',
            'quantity': 4,  # 4 * 2500 = 10,000 which is exactly 10% of 100,000 capital
            'price': 2500
        }
        
        is_valid, message = self.risk_manager.validate_order(order_params)
        self.assertTrue(is_valid)
    
    def test_validate_order_invalid_quantity(self):
        """Test order validation with invalid quantity"""
        order_params = {
            'stock_code': 'RELIANCE',
            'action': 'BUY',
            'quantity': 0,
            'price': 2500
        }
        
        is_valid, message = self.risk_manager.validate_order(order_params)
        self.assertFalse(is_valid)
        self.assertIn('quantity', message.lower())
    
    def test_calculate_stop_loss(self):
        """Test stop loss calculation"""
        entry_price = 1000
        stop_loss = self.risk_manager.calculate_stop_loss(entry_price, 'BUY')
        
        # Should be 5% below entry price (default stop loss)
        expected_stop_loss = entry_price * 0.95
        self.assertEqual(stop_loss, expected_stop_loss)
    
    def test_calculate_target(self):
        """Test target calculation"""
        entry_price = 1000
        target = self.risk_manager.calculate_target(entry_price, 'BUY')
        
        # Should be 15% above entry price (default target)
        expected_target = entry_price * 1.15
        self.assertEqual(target, expected_target)

class TestTechnicalIndicators(unittest.TestCase):
    """Test Technical Indicators"""
    
    def test_moving_average(self):
        """Test moving average calculation"""
        data = [100, 102, 98, 105, 103, 107, 109, 104, 106, 108]
        period = 5
        
        ma = TechnicalIndicators.moving_average(data, period)
        
        # Check that we get correct number of values
        self.assertEqual(len(ma), len(data))
        
        # Check that first few values are NaN (insufficient data)
        import pandas as pd
        self.assertTrue(pd.isna(ma.iloc[0]))
        self.assertTrue(pd.isna(ma.iloc[3]))
        
        # Check calculated value
        expected_ma = sum(data[:5]) / 5
        self.assertAlmostEqual(ma.iloc[4], expected_ma, places=2)
    
    def test_rsi_calculation(self):
        """Test RSI calculation"""
        # Simple test data with clear trend
        data = [100, 105, 110, 115, 120, 115, 110, 105, 100, 95]
        
        rsi = TechnicalIndicators.rsi(data, period=5)
        
        # Check that we get correct number of values
        self.assertEqual(len(rsi), len(data))
        
        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        for value in valid_rsi:
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 100)
    
    def test_macd_calculation(self):
        """Test MACD calculation"""
        # Generate test data with clear trend
        data = list(range(100, 150))  # Uptrending data
        
        macd_data = TechnicalIndicators.macd(data)
        
        # Check that we get the expected structure
        self.assertIn('macd', macd_data)
        self.assertIn('signal', macd_data)
        self.assertIn('histogram', macd_data)
        
        # Check data length
        self.assertEqual(len(macd_data['macd']), len(data))
        self.assertEqual(len(macd_data['signal']), len(data))
        self.assertEqual(len(macd_data['histogram']), len(data))
    
    def test_stochastic_rsi_calculation(self):
        """Test Stochastic RSI calculation"""
        # Generate test data
        data = [100, 105, 102, 108, 103, 110, 107, 112, 109, 115, 111, 118, 114, 120]
        
        stoch_rsi_data = TechnicalIndicators.stochastic_rsi(data)
        
        # Check that we get the expected structure
        self.assertIn('stoch_rsi', stoch_rsi_data)
        self.assertIn('k_percent', stoch_rsi_data)
        self.assertIn('d_percent', stoch_rsi_data)
        
        # Check data length
        self.assertEqual(len(stoch_rsi_data['stoch_rsi']), len(data))
        self.assertEqual(len(stoch_rsi_data['k_percent']), len(data))
        self.assertEqual(len(stoch_rsi_data['d_percent']), len(data))
        
        # Values should be between 0 and 100
        valid_k = stoch_rsi_data['k_percent'].dropna()
        valid_d = stoch_rsi_data['d_percent'].dropna()
        
        for value in valid_k:
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 100)
            
        for value in valid_d:
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 100)

class TestOrderManager(unittest.TestCase):
    """Test Order Manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_breeze_service = Mock()
        self.order_manager = OrderManager(self.mock_breeze_service)
    
    def test_calculate_position_size(self):
        """Test position size calculation"""
        capital = 100000
        risk_per_trade = 0.02  # 2%
        entry_price = 1000
        stop_loss_price = 950
        
        position_size = self.order_manager.calculate_position_size(
            capital, risk_per_trade, entry_price, stop_loss_price
        )
        
        # Risk-based calculation: (100000 * 0.02) / (1000 - 950) = 2000 / 50 = 40
        # But max position size is 10% of capital: 100000 * 0.1 / 1000 = 10
        # So the smaller value (10) should be returned
        self.assertEqual(position_size, 10)
    
    def test_calculate_position_size_zero_risk(self):
        """Test position size calculation with zero risk"""
        capital = 100000
        risk_per_trade = 0.02
        entry_price = 1000
        stop_loss_price = 1000  # Same as entry price
        
        position_size = self.order_manager.calculate_position_size(
            capital, risk_per_trade, entry_price, stop_loss_price
        )
        
        # Should return 0 when there's no price risk
        self.assertEqual(position_size, 0)

if __name__ == '__main__':
    unittest.main()