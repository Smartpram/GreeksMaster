"""
Helper utilities
"""
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class DataValidator:
    """Validate trading data and parameters"""
    
    @staticmethod
    def validate_ohlcv_data(data: List[Dict]) -> bool:
        """Validate OHLCV data format"""
        try:
            required_fields = ['open', 'high', 'low', 'close', 'volume']
            
            for item in data:
                if not all(field in item for field in required_fields):
                    return False
                
                # Check data types and logical constraints
                o, h, l, c, v = item['open'], item['high'], item['low'], item['close'], item['volume']
                
                if not all(isinstance(x, (int, float)) for x in [o, h, l, c, v]):
                    return False
                
                if h < max(o, c) or l > min(o, c):
                    return False
                
                if v < 0:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating OHLCV data: {e}")
            return False
    
    @staticmethod
    def validate_trade_parameters(params: Dict) -> bool:
        """Validate trade parameters"""
        try:
            required_fields = ['stock_code', 'action', 'quantity']
            
            if not all(field in params for field in required_fields):
                return False
            
            if params['action'].upper() not in ['BUY', 'SELL']:
                return False
            
            if not isinstance(params['quantity'], int) or params['quantity'] <= 0:
                return False
            
            if 'price' in params and not isinstance(params['price'], (int, float)):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating trade parameters: {e}")
            return False


class DataCleaner:
    """Clean and preprocess trading data"""
    
    @staticmethod
    def clean_ohlcv_data(data: List[Dict]) -> List[Dict]:
        """Clean OHLCV data"""
        try:
            cleaned_data = []
            
            for item in data:
                # Skip invalid entries
                if not DataValidator.validate_ohlcv_data([item]):
                    continue
                
                # Clean and normalize
                cleaned_item = {
                    'datetime': item.get('datetime'),
                    'open': float(item['open']),
                    'high': float(item['high']),
                    'low': float(item['low']),
                    'close': float(item['close']),
                    'volume': int(item['volume'])
                }
                
                cleaned_data.append(cleaned_item)
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error cleaning OHLCV data: {e}")
            return data
    
    @staticmethod
    def remove_outliers(data: pd.Series, method: str = 'iqr', threshold: float = 1.5) -> pd.Series:
        """Remove outliers from data series"""
        try:
            if method == 'iqr':
                Q1 = data.quantile(0.25)
                Q3 = data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                return data[(data >= lower_bound) & (data <= upper_bound)]
            
            elif method == 'zscore':
                z_scores = np.abs((data - data.mean()) / data.std())
                return data[z_scores < threshold]
            
            return data
            
        except Exception as e:
            logger.error(f"Error removing outliers: {e}")
            return data


class DateTimeHelper:
    """Helper functions for date and time operations"""
    
    @staticmethod
    def is_market_open(dt: datetime = None) -> bool:
        """Check if market is open at given datetime"""
        try:
            if dt is None:
                dt = datetime.now()
            
            # NSE trading hours: 9:15 AM to 3:30 PM, Monday to Friday
            weekday = dt.weekday()  # 0 = Monday, 6 = Sunday
            
            if weekday >= 5:  # Weekend
                return False
            
            market_open = dt.replace(hour=9, minute=15, second=0, microsecond=0)
            market_close = dt.replace(hour=15, minute=30, second=0, microsecond=0)
            
            return market_open <= dt <= market_close
            
        except Exception as e:
            logger.error(f"Error checking market hours: {e}")
            return False
    
    @staticmethod
    def get_next_market_open(dt: datetime = None) -> datetime:
        """Get next market opening datetime"""
        try:
            if dt is None:
                dt = datetime.now()
            
            # If market is currently open, return current time
            if DateTimeHelper.is_market_open(dt):
                return dt
            
            # Find next market open
            next_open = dt.replace(hour=9, minute=15, second=0, microsecond=0)
            
            # If past today's market hours, move to next day
            if dt.hour >= 15 and dt.minute >= 30:
                next_open += timedelta(days=1)
            
            # Skip weekends
            while next_open.weekday() >= 5:
                next_open += timedelta(days=1)
            
            return next_open
            
        except Exception as e:
            logger.error(f"Error getting next market open: {e}")
            return dt
    
    @staticmethod
    def get_trading_days_between(start_date: datetime, end_date: datetime) -> int:
        """Get number of trading days between two dates"""
        try:
            trading_days = 0
            current_date = start_date
            
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Monday to Friday
                    trading_days += 1
                current_date += timedelta(days=1)
            
            return trading_days
            
        except Exception as e:
            logger.error(f"Error calculating trading days: {e}")
            return 0


class FormatHelper:
    """Helper functions for formatting data"""
    
    @staticmethod
    def format_currency(amount: float, currency: str = "₹") -> str:
        """Format amount as currency"""
        try:
            if amount >= 10000000:  # 1 Crore
                return f"{currency}{amount/10000000:.2f}Cr"
            elif amount >= 100000:  # 1 Lakh
                return f"{currency}{amount/100000:.2f}L"
            elif amount >= 1000:  # 1 Thousand
                return f"{currency}{amount/1000:.2f}K"
            else:
                return f"{currency}{amount:.2f}"
                
        except Exception as e:
            logger.error(f"Error formatting currency: {e}")
            return f"{currency}{amount}"
    
    @staticmethod
    def format_percentage(value: float, decimals: int = 2) -> str:
        """Format value as percentage"""
        try:
            return f"{value:.{decimals}f}%"
        except Exception as e:
            logger.error(f"Error formatting percentage: {e}")
            return f"{value}%"
    
    @staticmethod
    def format_large_number(value: int) -> str:
        """Format large numbers with commas"""
        try:
            return f"{value:,}"
        except Exception as e:
            logger.error(f"Error formatting number: {e}")
            return str(value)


class ConfigHelper:
    """Helper functions for configuration management"""
    
    @staticmethod
    def validate_config(config_dict: Dict) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        try:
            # Required fields
            required_fields = [
                'BREEZE_API_KEY',
                'BREEZE_SECRET_KEY',
                'BREEZE_USER_ID'
            ]
            
            for field in required_fields:
                if not config_dict.get(field):
                    errors.append(f"Missing required field: {field}")
            
            # Validate numeric fields
            numeric_fields = {
                'DEFAULT_CAPITAL': (1000, 10000000),
                'MAX_POSITION_SIZE': (0.01, 1.0),
                'DEFAULT_STOP_LOSS': (0.01, 0.2),
                'DEFAULT_TARGET': (0.05, 1.0)
            }
            
            for field, (min_val, max_val) in numeric_fields.items():
                if field in config_dict:
                    try:
                        value = float(config_dict[field])
                        if not min_val <= value <= max_val:
                            errors.append(f"{field} should be between {min_val} and {max_val}")
                    except ValueError:
                        errors.append(f"{field} should be a valid number")
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validating config: {e}")
            return [f"Configuration validation error: {e}"]
    
    @staticmethod
    def load_instruments_list(file_path: str) -> List[str]:
        """Load instruments list from file"""
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.json'):
                    data = json.load(f)
                    return data if isinstance(data, list) else []
                else:
                    return [line.strip() for line in f.readlines() if line.strip()]
                    
        except Exception as e:
            logger.error(f"Error loading instruments list: {e}")
            return []


class LogHelper:
    """Helper functions for logging"""
    
    @staticmethod
    def setup_logging(log_level: str = "INFO", log_file: str = None):
        """Setup logging configuration"""
        try:
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # Setup root logger
            logger = logging.getLogger()
            logger.setLevel(getattr(logging, log_level.upper()))
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # File handler if specified
            if log_file:
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                
        except Exception as e:
            print(f"Error setting up logging: {e}")
    
    @staticmethod
    def log_trade(trade_data: Dict, logger_instance: logging.Logger):
        """Log trade information"""
        try:
            action = trade_data.get('action', 'UNKNOWN')
            symbol = trade_data.get('symbol', 'UNKNOWN')
            quantity = trade_data.get('quantity', 0)
            price = trade_data.get('price', 0)
            
            message = f"{action} {quantity} {symbol} @ ₹{price:.2f}"
            
            if 'pnl' in trade_data:
                pnl = trade_data['pnl']
                message += f" | P&L: ₹{pnl:.2f}"
            
            logger_instance.info(message)
            
        except Exception as e:
            logger_instance.error(f"Error logging trade: {e}")


class MathHelper:
    """Mathematical helper functions"""
    
    @staticmethod
    def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
        """Safe division that handles zero denominator"""
        try:
            return numerator / denominator if denominator != 0 else default
        except Exception:
            return default
    
    @staticmethod
    def calculate_compound_return(returns: List[float]) -> float:
        """Calculate compound return from list of returns"""
        try:
            if not returns:
                return 0.0
            
            compound = 1.0
            for ret in returns:
                compound *= (1 + ret/100)
            
            return (compound - 1) * 100
            
        except Exception as e:
            logger.error(f"Error calculating compound return: {e}")
            return 0.0
    
    @staticmethod
    def normalize_data(data: List[float], method: str = 'minmax') -> List[float]:
        """Normalize data using specified method"""
        try:
            data_array = np.array(data)
            
            if method == 'minmax':
                min_val, max_val = data_array.min(), data_array.max()
                if max_val == min_val:
                    return [0.0] * len(data)
                return ((data_array - min_val) / (max_val - min_val)).tolist()
            
            elif method == 'zscore':
                mean_val, std_val = data_array.mean(), data_array.std()
                if std_val == 0:
                    return [0.0] * len(data)
                return ((data_array - mean_val) / std_val).tolist()
            
            return data
            
        except Exception as e:
            logger.error(f"Error normalizing data: {e}")
            return data