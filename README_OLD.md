# MyBreezeApp - Algorithmic Trading Platform

A comprehensive algorithmic trading application built with ICICIDirect Breeze API, implementing a Buy and Hold trend-following positional strategy.

## 🚀 Features

### Core Trading Features
- **Real-time Data Streaming**: Live market data via Breeze API
- **Order Execution**: Market, Limit, and Stop-loss orders
- **Risk Management**: Configurable stop-loss, target, and trailing stop-loss
- **Strategy Implementation**: Buy and Hold trend-following positional strategy
- **Paper Trading Mode**: Test strategies without real money

### Analysis & Backtesting
- **Historical Data Analysis**: Comprehensive backtesting engine
- **Performance Metrics**: Sharpe Ratio, Max Drawdown, Win Rate, and more
- **Technical Indicators**: RSI, Moving Averages, MACD, Bollinger Bands
- **Strategy Optimization**: Parameter optimization capabilities

### User Interface
- **Web Dashboard**: Real-time portfolio monitoring
- **Interactive Charts**: Portfolio performance visualization
- **Trade Management**: Order tracking and position monitoring
- **Performance Reports**: Detailed analytics and reports

### Notifications & Alerts
- **Email Notifications**: Trade alerts and daily summaries
- **Telegram Integration**: Real-time notifications via Telegram bot
- **Risk Alerts**: Automated risk management notifications

### Security & Authentication
- **OAuth Integration**: Secure authentication with Breeze API
- **Session Management**: Secure session handling
- **API Security**: JWT token-based API authentication

## 📋 Prerequisites

- Python 3.8 or higher
- ICICIDirect Breeze API credentials
- Git (for version control)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/MyBreezeApp.git
cd MyBreezeApp
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your credentials
```

### 5. Required Environment Variables
```env
# Breeze API Configuration
BREEZE_API_KEY=your_breeze_api_key
BREEZE_SECRET_KEY=your_breeze_secret_key
BREEZE_SESSION_TOKEN=your_session_token
BREEZE_USER_ID=your_user_id
BREEZE_PASSWORD=your_password

# Trading Configuration
PAPER_TRADING=True
DEFAULT_CAPITAL=100000
MAX_POSITION_SIZE=0.1
DEFAULT_STOP_LOSS=0.05
DEFAULT_TARGET=0.15

# Notification Configuration (Optional)
EMAIL_ENABLED=False
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

TELEGRAM_ENABLED=False
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 🚀 Running the Application

### Development Mode
```bash
python run.py
```

### Production Mode
```bash
# Using Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app

# Using Waitress (Windows)
waitress-serve --host=0.0.0.0 --port=5000 run:app
```

## 📊 Strategy Configuration

### Buy and Hold Trend Strategy Parameters
```python
# Technical Indicators
TREND_PERIOD=20          # Moving average period
RSI_PERIOD=14           # RSI calculation period
RSI_OVERBOUGHT=70       # RSI overbought level
RSI_OVERSOLD=30         # RSI oversold level

# Risk Management
DEFAULT_STOP_LOSS=0.05  # 5% stop loss
DEFAULT_TARGET=0.15     # 15% target
TRAILING_STOP_LOSS=0.03 # 3% trailing stop
MAX_DAILY_LOSS=0.02     # 2% max daily loss
```

### Strategy Logic
1. **Entry Conditions**:
   - Price above moving average (trend confirmation)
   - RSI not overbought (< 70)
   - Volume above average (confirmation)
   - Positive momentum (price higher than 5 days ago)

2. **Exit Conditions**:
   - Stop loss hit
   - Target achieved
   - Trend reversal (price below MA for 3+ days)
   - RSI overbought with profit

## 🧪 Testing

### Run Unit Tests
```bash
python -m pytest tests/
```

### Run Backtesting
```bash
python -c "
from app.services.backtesting import BacktestingEngine
from app.strategies.buy_hold_trend import BuyHoldTrendStrategy

# Run backtest example
engine = BacktestingEngine()
strategy = BuyHoldTrendStrategy()
results = engine.run_backtest(
    strategy=strategy,
    instrument='RELIANCE',
    start_date='2023-01-01',
    end_date='2023-12-31'
)
print(results)
"
```

## 📈 API Endpoints

### Authentication
- `GET /` - Main dashboard (requires authentication)
- `GET /login` - Login page
- `GET /auth/callback` - OAuth callback

### Trading APIs
- `GET /api/portfolio` - Get portfolio data
- `GET/POST /api/orders` - Order management
- `POST /api/strategy/toggle` - Start/stop strategy
- `GET /api/performance` - Performance metrics

### Data APIs
- `GET /api/stream/start` - Start data streaming
- `GET /api/stream/stop` - Stop data streaming
- `POST /api/backtest` - Run backtesting

## 🔧 Configuration Options

### Trading Settings
- `PAPER_TRADING`: Enable/disable paper trading mode
- `DEFAULT_CAPITAL`: Starting capital amount
- `MAX_POSITION_SIZE`: Maximum position size as % of capital

### Risk Management
- `DEFAULT_STOP_LOSS`: Default stop-loss percentage
- `DEFAULT_TARGET`: Default target percentage
- `TRAILING_STOP_LOSS`: Trailing stop-loss percentage
- `MAX_DAILY_LOSS`: Maximum daily loss limit

### Notifications
- `EMAIL_ENABLED`: Enable email notifications
- `TELEGRAM_ENABLED`: Enable Telegram notifications

## 🚢 Deployment

### Docker Deployment
```bash
# Build Docker image
docker build -t mybreeze-app .

# Run container
docker run -p 5000:5000 --env-file .env mybreeze-app
```

### AWS Deployment
```bash
# Deploy to AWS using provided script
python deployment/aws_deploy.py
```

## 📁 Project Structure
```
MyBreezeApp/
├── app/
│   ├── main.py              # Flask application
│   ├── config.py            # Configuration settings
│   ├── models/              # Data models
│   ├── services/            # Business logic services
│   │   ├── breeze_api.py    # Breeze API integration
│   │   ├── order_manager.py # Order management
│   │   ├── risk_manager.py  # Risk management
│   │   ├── backtesting.py   # Backtesting engine
│   │   └── notifications.py # Notification service
│   ├── strategies/          # Trading strategies
│   │   └── buy_hold_trend.py # Main strategy
│   ├── utils/               # Utility functions
│   ├── templates/           # HTML templates
│   └── static/              # CSS, JS, images
├── tests/                   # Unit tests
├── docker/                  # Docker configuration
├── deployment/              # Deployment scripts
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
└── run.py                  # Application runner
```

## 📊 Performance Metrics

The application calculates and displays:
- **Total Return**: Overall portfolio return
- **Sharpe Ratio**: Risk-adjusted return measure
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss
- **Average Trade**: Average profit/loss per trade

## 🔒 Security Features

- OAuth 2.0 authentication with Breeze API
- JWT token-based session management
- Input validation and sanitization
- Secure configuration management
- API rate limiting (recommended for production)

## 🚨 Risk Disclaimer

**Important**: This software is for educational and research purposes. Trading in financial markets involves substantial risk of loss. Past performance is not indicative of future results. Always:

- Test strategies thoroughly in paper trading mode
- Start with small position sizes
- Monitor risk limits carefully
- Understand the risks involved in algorithmic trading
- Consult with financial advisors before making investment decisions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the configuration settings

## 🙏 Acknowledgments

- ICICIDirect for providing the Breeze API
- Flask community for the excellent web framework  
- The open-source community for various libraries used

---

**Built with ❤️ for algorithmic trading enthusiasts**