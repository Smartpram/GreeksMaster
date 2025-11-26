"""
Integration test for enhanced strategy with MACD and Stochastic RSI
"""
import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from utils.indicators import TechnicalIndicators

def test_enhanced_indicators_integration():
    """Test integration of all enhanced indicators"""
    print("Testing Enhanced Technical Indicators Integration...")
    
    # Generate sample OHLCV data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    prices = []
    base_price = 100
    
    # Create realistic price data with trend and volatility
    for i in range(100):
        # Add trend component
        trend = i * 0.5
        
        # Add random volatility
        import random
        volatility = random.uniform(-2, 2)
        
        price = base_price + trend + volatility
        prices.append(max(price, 50))  # Ensure positive prices
    
    # Create OHLCV data
    data = []
    for i, price in enumerate(prices):
        high = price + random.uniform(0, 2)
        low = price - random.uniform(0, 2)
        open_price = prices[i-1] if i > 0 else price
        volume = random.randint(10000, 50000)
        
        data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': price,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    
    # Test all indicators
    indicators = TechnicalIndicators()
    
    try:
        # Test individual indicators
        print("✓ Testing Moving Average...")
        ma = indicators.moving_average(df['close'], 20)
        assert len(ma) == len(df), "MA length mismatch"
        
        print("✓ Testing RSI...")
        rsi = indicators.rsi(df['close'], 14)
        assert len(rsi) == len(df), "RSI length mismatch"
        
        print("✓ Testing MACD...")
        macd_data = indicators.macd(df['close'])
        assert 'macd' in macd_data, "MACD data missing"
        assert 'signal' in macd_data, "MACD signal missing"
        assert 'histogram' in macd_data, "MACD histogram missing"
        
        print("✓ Testing Stochastic RSI...")
        stoch_rsi_data = indicators.stochastic_rsi(df['close'])
        assert 'stoch_rsi' in stoch_rsi_data, "Stochastic RSI data missing"
        assert 'k_percent' in stoch_rsi_data, "Stochastic RSI K% missing"
        assert 'd_percent' in stoch_rsi_data, "Stochastic RSI D% missing"
        
        print("✓ Testing Calculate All Indicators...")
        all_indicators = indicators.calculate_all_indicators(df)
        
        # Check that all enhanced indicators are included
        expected_columns = [
            'sma_20', 'rsi', 'macd', 'signal', 'histogram',
            'stoch_rsi_stoch_rsi', 'stoch_rsi_k_percent', 'stoch_rsi_d_percent'
        ]
        
        for col in expected_columns:
            assert col in all_indicators.columns, f"Missing column: {col}"
        
        print("✓ All enhanced indicators working correctly!")
        
        # Print sample values for verification
        print("\nSample Enhanced Indicator Values (last 5 rows):")
        print(all_indicators[expected_columns].tail().round(4))
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_enhanced_indicators_integration()
    if success:
        print("\n🎉 All enhanced indicators integration tests passed!")
    else:
        print("\n❌ Integration tests failed!")