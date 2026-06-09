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
    
    # Breeze Account (NON-PINS NRO only - OPTIONS TRADING)
    BREEZE_USER_ID = os.getenv('BREEZE_USER_ID')
    BREEZE_SESSION_TOKEN = os.getenv('BREEZE_SESSION_TOKEN')
    BREEZE_PASSWORD = os.getenv('BREEZE_PASSWORD')
    
    # Options Trading Settings
    PAPER_TRADING = os.getenv('PAPER_TRADING', 'True').lower() == 'true'
    OPTIONS_CAPITAL = float(os.getenv('OPTIONS_CAPITAL', '500000'))
    MAX_OPTION_POSITION_SIZE = float(os.getenv('MAX_OPTION_POSITION_SIZE', '0.1'))
    
    # Risk Management Settings
    MAX_DELTA_EXPOSURE = float(os.getenv('MAX_DELTA_EXPOSURE', '0.5'))
    MAX_VEGA_EXPOSURE = float(os.getenv('MAX_VEGA_EXPOSURE', '2.0'))
    MAX_THETA_DECAY_PER_DAY = float(os.getenv('MAX_THETA_DECAY_PER_DAY', '-500'))
    MAX_DAILY_LOSS = float(os.getenv('MAX_DAILY_LOSS', '0.02'))
    
    # Options Strategy Settings
    DEFAULT_OPTION_STRATEGY = os.getenv('DEFAULT_OPTION_STRATEGY', 'CALL_SPREAD')
    PREFERRED_EXPIRY = os.getenv('PREFERRED_EXPIRY', 'WEEKLY')
    USE_ATM_STRIKES = os.getenv('USE_ATM_STRIKES', 'True').lower() == 'true'
    SPREAD_WIDTH = float(os.getenv('SPREAD_WIDTH', '100'))
    
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
            'BREEZE_SECRET_KEY'
        ]
        
        # Check at least one account is configured
        pins_configured = cls.BREEZE_USER_ID_PINS and cls.BREEZE_SESSION_TOKEN_PINS
        non_pins_configured = cls.BREEZE_USER_ID_NON_PINS and cls.BREEZE_SESSION_TOKEN_NON_PINS
        
        if not (pins_configured or non_pins_configured):
            raise ValueError("At least one account (PINS or NON_PINS) must be configured")
        
        missing_fields = []
        for field in required_fields:
            if not getattr(cls, field):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
        
        return True