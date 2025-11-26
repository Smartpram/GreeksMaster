"""
Technical Indicators for Trading Strategies
"""
import pandas as pd
import numpy as np
from typing import List, Union
import logging

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """Collection of technical indicators for trading analysis"""
    
    @staticmethod
    def moving_average(data: Union[List, pd.Series], period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        try:
            if isinstance(data, list):
                data = pd.Series(data)
            return data.rolling(window=period).mean()
        except Exception as e:
            logger.error(f"Error calculating moving average: {e}")
            return pd.Series([np.nan] * len(data))
    
    @staticmethod
    def exponential_moving_average(data: Union[List, pd.Series], period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        try:
            if isinstance(data, list):
                data = pd.Series(data)
            return data.ewm(span=period).mean()
        except Exception as e:
            logger.error(f"Error calculating EMA: {e}")
            return pd.Series([np.nan] * len(data))
    
    @staticmethod
    def rsi(data: Union[List, pd.Series], period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        try:
            if isinstance(data, list):
                data = pd.Series(data)
            
            delta = data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return pd.Series([np.nan] * len(data))
    
    @staticmethod
    def macd(data: Union[List, pd.Series], fast_period: int = 12, 
             slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        try:
            if isinstance(data, list):
                data = pd.Series(data)
            
            ema_fast = data.ewm(span=fast_period).mean()
            ema_slow = data.ewm(span=slow_period).mean()
            
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal_period).mean()
            histogram = macd_line - signal_line
            
            return pd.DataFrame({
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram
            })
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def bollinger_bands(data: Union[List, pd.Series], period: int = 20, 
                       std_dev: float = 2) -> pd.DataFrame:
        """Calculate Bollinger Bands"""
        try:
            if isinstance(data, list):
                data = pd.Series(data)
            
            sma = data.rolling(window=period).mean()
            std = data.rolling(window=period).std()
            
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            return pd.DataFrame({
                'upper': upper_band,
                'middle': sma,
                'lower': lower_band
            })
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def stochastic_oscillator(high: Union[List, pd.Series], low: Union[List, pd.Series], 
                            close: Union[List, pd.Series], k_period: int = 14, 
                            d_period: int = 3) -> pd.DataFrame:
        """Calculate Stochastic Oscillator"""
        try:
            if isinstance(high, list):
                high = pd.Series(high)
            if isinstance(low, list):
                low = pd.Series(low)
            if isinstance(close, list):
                close = pd.Series(close)
            
            lowest_low = low.rolling(window=k_period).min()
            highest_high = high.rolling(window=k_period).max()
            
            k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
            d_percent = k_percent.rolling(window=d_period).mean()
            
            return pd.DataFrame({
                'k_percent': k_percent,
                'd_percent': d_percent
            })
        except Exception as e:
            logger.error(f"Error calculating Stochastic Oscillator: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def stochastic_rsi(data: Union[List, pd.Series], rsi_period: int = 14, 
                      stoch_period: int = 14, k_period: int = 3, d_period: int = 3) -> pd.DataFrame:
        """Calculate Stochastic RSI"""
        try:
            if isinstance(data, list):
                data = pd.Series(data)
            
            # First calculate RSI
            rsi = TechnicalIndicators.rsi(data, rsi_period)
            
            # Then apply Stochastic formula to RSI
            rsi_low = rsi.rolling(window=stoch_period).min()
            rsi_high = rsi.rolling(window=stoch_period).max()
            
            stoch_rsi = 100 * ((rsi - rsi_low) / (rsi_high - rsi_low))
            
            # Smooth the Stochastic RSI
            k_percent = stoch_rsi.rolling(window=k_period).mean()
            d_percent = k_percent.rolling(window=d_period).mean()
            
            return pd.DataFrame({
                'stoch_rsi': stoch_rsi,
                'k_percent': k_percent,
                'd_percent': d_percent
            })
        except Exception as e:
            logger.error(f"Error calculating Stochastic RSI: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def average_true_range(high: Union[List, pd.Series], low: Union[List, pd.Series], 
                          close: Union[List, pd.Series], period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        try:
            if isinstance(high, list):
                high = pd.Series(high)
            if isinstance(low, list):
                low = pd.Series(low)
            if isinstance(close, list):
                close = pd.Series(close)
            
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = true_range.rolling(window=period).mean()
            
            return atr
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return pd.Series([np.nan] * len(high))
    
    @staticmethod
    def williams_r(high: Union[List, pd.Series], low: Union[List, pd.Series], 
                   close: Union[List, pd.Series], period: int = 14) -> pd.Series:
        """Calculate Williams %R"""
        try:
            if isinstance(high, list):
                high = pd.Series(high)
            if isinstance(low, list):
                low = pd.Series(low)
            if isinstance(close, list):
                close = pd.Series(close)
            
            highest_high = high.rolling(window=period).max()
            lowest_low = low.rolling(window=period).min()
            
            williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
            
            return williams_r
        except Exception as e:
            logger.error(f"Error calculating Williams %R: {e}")
            return pd.Series([np.nan] * len(high))
    
    @staticmethod
    def commodity_channel_index(high: Union[List, pd.Series], low: Union[List, pd.Series], 
                               close: Union[List, pd.Series], period: int = 20) -> pd.Series:
        """Calculate Commodity Channel Index"""
        try:
            if isinstance(high, list):
                high = pd.Series(high)
            if isinstance(low, list):
                low = pd.Series(low)
            if isinstance(close, list):
                close = pd.Series(close)
            
            typical_price = (high + low + close) / 3
            sma = typical_price.rolling(window=period).mean()
            mean_deviation = typical_price.rolling(window=period).apply(
                lambda x: np.mean(np.abs(x - np.mean(x)))
            )
            
            cci = (typical_price - sma) / (0.015 * mean_deviation)
            
            return cci
        except Exception as e:
            logger.error(f"Error calculating CCI: {e}")
            return pd.Series([np.nan] * len(high))
    
    @staticmethod
    def money_flow_index(high: Union[List, pd.Series], low: Union[List, pd.Series], 
                        close: Union[List, pd.Series], volume: Union[List, pd.Series], 
                        period: int = 14) -> pd.Series:
        """Calculate Money Flow Index"""
        try:
            if isinstance(high, list):
                high = pd.Series(high)
            if isinstance(low, list):
                low = pd.Series(low)
            if isinstance(close, list):
                close = pd.Series(close)
            if isinstance(volume, list):
                volume = pd.Series(volume)
            
            typical_price = (high + low + close) / 3
            money_flow = typical_price * volume
            
            positive_flow = money_flow.where(typical_price > typical_price.shift(), 0)
            negative_flow = money_flow.where(typical_price < typical_price.shift(), 0)
            
            positive_mf = positive_flow.rolling(window=period).sum()
            negative_mf = negative_flow.rolling(window=period).sum()
            
            money_ratio = positive_mf / negative_mf
            mfi = 100 - (100 / (1 + money_ratio))
            
            return mfi
        except Exception as e:
            logger.error(f"Error calculating MFI: {e}")
            return pd.Series([np.nan] * len(high))
    
    @staticmethod
    def on_balance_volume(close: Union[List, pd.Series], volume: Union[List, pd.Series]) -> pd.Series:
        """Calculate On-Balance Volume"""
        try:
            if isinstance(close, list):
                close = pd.Series(close)
            if isinstance(volume, list):
                volume = pd.Series(volume)
            
            price_change = close.diff()
            
            obv = volume.copy()
            obv.loc[price_change < 0] = -volume.loc[price_change < 0]
            obv.loc[price_change == 0] = 0
            
            return obv.cumsum()
        except Exception as e:
            logger.error(f"Error calculating OBV: {e}")
            return pd.Series([np.nan] * len(close))
    
    @staticmethod
    def fibonacci_retracement(high: float, low: float) -> dict:
        """Calculate Fibonacci Retracement Levels"""
        try:
            diff = high - low
            
            levels = {
                'level_0': high,
                'level_23.6': high - 0.236 * diff,
                'level_38.2': high - 0.382 * diff,
                'level_50': high - 0.5 * diff,
                'level_61.8': high - 0.618 * diff,
                'level_100': low
            }
            
            return levels
        except Exception as e:
            logger.error(f"Error calculating Fibonacci levels: {e}")
            return {}
    
    @staticmethod
    def pivot_points(high: float, low: float, close: float) -> dict:
        """Calculate Pivot Points"""
        try:
            pivot = (high + low + close) / 3
            
            levels = {
                'pivot': pivot,
                'r1': 2 * pivot - low,
                'r2': pivot + (high - low),
                'r3': high + 2 * (pivot - low),
                's1': 2 * pivot - high,
                's2': pivot - (high - low),
                's3': low - 2 * (high - pivot)
            }
            
            return levels
        except Exception as e:
            logger.error(f"Error calculating Pivot Points: {e}")
            return {}
    
    @staticmethod
    def support_resistance_levels(data: Union[List, pd.Series], window: int = 20) -> dict:
        """Identify Support and Resistance Levels"""
        try:
            if isinstance(data, list):
                data = pd.Series(data)
            
            # Find local maxima and minima
            highs = data.rolling(window=window, center=True).max()
            lows = data.rolling(window=window, center=True).min()
            
            resistance_levels = data[data == highs].dropna().unique()
            support_levels = data[data == lows].dropna().unique()
            
            # Sort and get top levels
            resistance_levels = sorted(resistance_levels, reverse=True)[:5]
            support_levels = sorted(support_levels)[-5:]
            
            return {
                'resistance': resistance_levels,
                'support': support_levels
            }
        except Exception as e:
            logger.error(f"Error calculating Support/Resistance levels: {e}")
            return {'resistance': [], 'support': []}
    
    @classmethod
    def calculate_all_indicators(cls, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all major indicators for a given OHLCV dataset"""
        try:
            result = data.copy()
            
            # Moving Averages
            result['sma_20'] = cls.moving_average(data['close'], 20)
            result['sma_50'] = cls.moving_average(data['close'], 50)
            result['ema_12'] = cls.exponential_moving_average(data['close'], 12)
            result['ema_26'] = cls.exponential_moving_average(data['close'], 26)
            
            # Oscillators
            result['rsi'] = cls.rsi(data['close'])
            
            # MACD
            macd_data = cls.macd(data['close'])
            result = pd.concat([result, macd_data], axis=1)
            
            # Bollinger Bands
            bb_data = cls.bollinger_bands(data['close'])
            result = pd.concat([result, bb_data.add_prefix('bb_')], axis=1)
            
            # Stochastic
            stoch_data = cls.stochastic_oscillator(data['high'], data['low'], data['close'])
            result = pd.concat([result, stoch_data], axis=1)
            
            # Stochastic RSI
            stoch_rsi_data = cls.stochastic_rsi(data['close'])
            result = pd.concat([result, stoch_rsi_data.add_prefix('stoch_rsi_')], axis=1)
            
            # Volume indicators
            if 'volume' in data.columns:
                result['obv'] = cls.on_balance_volume(data['close'], data['volume'])
                result['mfi'] = cls.money_flow_index(data['high'], data['low'], 
                                                   data['close'], data['volume'])
            
            # Volatility
            result['atr'] = cls.average_true_range(data['high'], data['low'], data['close'])
            
            return result
        
        except Exception as e:
            logger.error(f"Error calculating all indicators: {e}")
            return data