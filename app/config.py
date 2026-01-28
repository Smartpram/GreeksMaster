"""
Configuration settings for MyBreezeApp
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Breeze API settings
    BREEZE_API_KEY = os.getenv('BREEZE_API_KEY')
    BREEZE_SECRET_KEY = os.getenv('BREEZE_SECRET_KEY')
    BREEZE_SESSION_TOKEN = os.getenv('BREEZE_SESSION_TOKEN')
    BREEZE_USER_ID = os.getenv('BREEZE_USER_ID')
    BREEZE_PASSWORD = os.getenv('BREEZE_PASSWORD')
    
    # Trading settings
    PAPER_TRADING = os.getenv('PAPER_TRADING', 'True').lower() == 'true'
    DEFAULT_CAPITAL = float(os.getenv('DEFAULT_CAPITAL', '100000'))
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '0.1'))  # 10% of capital
    
    # Risk management settings
    DEFAULT_STOP_LOSS = float(os.getenv('DEFAULT_STOP_LOSS', '0.05'))  # 5%
    DEFAULT_TARGET = float(os.getenv('DEFAULT_TARGET', '0.15'))  # 15%
    TRAILING_STOP_LOSS = float(os.getenv('TRAILING_STOP_LOSS', '0.03'))  # 3%
    MAX_DAILY_LOSS = float(os.getenv('MAX_DAILY_LOSS', '0.02'))  # 2%
    
    # Strategy settings
    TREND_PERIOD = int(os.getenv('TREND_PERIOD', '20'))
    RSI_PERIOD = int(os.getenv('RSI_PERIOD', '14'))
    RSI_OVERBOUGHT = float(os.getenv('RSI_OVERBOUGHT', '70'))
    RSI_OVERSOLD = float(os.getenv('RSI_OVERSOLD', '30'))
    
    # Database settings (SQLite for simplicity)
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///mybreeze.db')
    # Ingest API key for protecting ingestion endpoints (defaults to SECRET_KEY)
    INGEST_API_KEY = os.getenv('INGEST_API_KEY', SECRET_KEY)
    
    # Notification settings
    EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'False').lower() == 'true'
    EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
    EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
    EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    EMAIL_FROM = os.getenv('EMAIL_FROM')
    EMAIL_TO = os.getenv('EMAIL_TO')
    
    TELEGRAM_ENABLED = os.getenv('TELEGRAM_ENABLED', 'False').lower() == 'true'
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # AWS settings for deployment
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # Data storage settings
    DATA_PATH = os.getenv('DATA_PATH', './data')
    BACKTEST_DATA_PATH = os.getenv('BACKTEST_DATA_PATH', './data/backtest')
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'mybreeze.log')
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        required_fields = [
            'BREEZE_API_KEY',
            'BREEZE_SECRET_KEY',
            'BREEZE_USER_ID'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(cls, field):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
        
        return True