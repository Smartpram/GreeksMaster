# 🚀 MyBreezeApp - Enhanced Algorithmic Trading Application

> **Advanced algorithmic trading platform with MACD, RSI, and Stochastic RSI integration for superior trend confirmation and signal generation.**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3%2B-green)](https://flask.palletsprojects.com)
[![Tests](https://img.shields.io/badge/Tests-17%2F17%20Passing-brightgreen)](tests/)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

## 🎯 Overview

MyBreezeApp is a sophisticated algorithmic trading platform that implements a **Buy & Hold trend-following strategy** enhanced with multiple technical indicators for precise market analysis and trade execution through the ICICIDirect Breeze API.

### ✨ Key Features

- 🔥 **Enhanced Technical Analysis**: MACD, RSI, and Stochastic RSI integration
- 📈 **Multi-Indicator Signal Confirmation**: Advanced entry/exit logic with weighted scoring
- 🛡️ **Comprehensive Risk Management**: Position sizing, stop-loss, and daily loss limits
- 🌐 **Real-time Web Dashboard**: Interactive monitoring and control interface
- 📊 **Advanced Backtesting Engine**: Historical performance analysis with detailed metrics
- 🔔 **Smart Notifications**: Email and Telegram alerts for trades and risk events
- 💰 **Paper Trading Mode**: Risk-free strategy testing and validation
- 🐳 **Docker Ready**: Containerized deployment with Docker Compose
- ☁️ **Cloud Deployment**: AWS, Heroku, and Digital Ocean support

## 🚀 Quick Start

### Automated Setup (Recommended)
```bash
python setup.py
```
This creates all necessary files, directories, and configurations automatically.

### Manual Setup
```bash
# 1. Clone and install
git clone <repository-url>
cd MyBreezeApp
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Update .env with your API credentials

# 3. Run tests
python -m pytest tests/ -v

# 4. Start application
python -m flask run
```

### Docker Deployment
```bash
docker-compose up -d
```

## ⚙️ Configuration

### Essential Settings (.env file)
```env
# ICICIDirect Breeze API
BREEZE_API_KEY=your_api_key_here
BREEZE_SECRET_KEY=your_secret_key_here
BREEZE_USER_ID=your_user_id
BREEZE_PASSWORD=your_password

# Trading Configuration
PAPER_TRADING=True          # Start with paper trading
DEFAULT_CAPITAL=100000      # ₹1,00,000
MAX_POSITION_SIZE=0.1       # 10% per position

# Enhanced Strategy Parameters
TREND_PERIOD=20             # Moving average period
RSI_PERIOD=14               # RSI calculation period
RSI_OVERBOUGHT=70          # RSI overbought level
RSI_OVERSOLD=30            # RSI oversold level

# Risk Management
DEFAULT_STOP_LOSS=0.05     # 5% stop loss
DEFAULT_TARGET=0.15        # 15% target
MAX_DAILY_LOSS=0.02        # 2% daily loss limit
```

## 📊 Enhanced Strategy Features

### Multi-Indicator Analysis
- **MACD (12,26,9)**: Trend momentum confirmation
- **RSI (14)**: Momentum oscillator with healthy range validation  
- **Stochastic RSI**: Precise overbought/oversold timing
- **Moving Averages**: Primary trend identification
- **Volume Analysis**: Confirmation of price movements

### Advanced Entry Conditions
```python
# Primary Requirements (Must Have All)
✅ Price > Moving Average (trend confirmation)
✅ RSI in healthy range (30 < RSI < 70)

# Enhanced Requirements (Must Have ≥1)
✅ MACD bullish (MACD > Signal AND Histogram > 0)
✅ Stochastic RSI bullish (%K > 20, %D > 20, %K > %D)

# Supporting Conditions (Boost signal strength)
✅ Volume > 120% of average
✅ Price momentum (2% above 5-day ago)
✅ Not overbought (< 98% of 10-day high)
```

### Intelligent Exit Strategies
- **Multi-Indicator Bearish Signals**: 2+ indicators suggesting reversal
- **Profit Protection**: Technical exits with minimum profit thresholds
- **MACD Bearish Crossover**: Early trend change detection
- **Stochastic RSI Overbought**: Precise exit timing
- **Risk-Based Stops**: Dynamic stop-loss and target management

## 🏗️ Architecture

```
MyBreezeApp/
├── app/
│   ├── main.py                 # Flask application & routes
│   ├── config.py              # Configuration management
│   ├── models.py              # Database models
│   ├── services/
│   │   ├── breeze_api.py      # ICICIDirect API integration
│   │   ├── order_manager.py   # Order execution & tracking
│   │   ├── risk_manager.py    # Risk management & validation
│   │   ├── backtesting.py     # Historical analysis engine
│   │   └── notifications.py   # Email & Telegram alerts
│   ├── strategies/
│   │   └── buy_hold_trend.py  # Enhanced Buy & Hold strategy
│   └── utils/
│       └── indicators.py      # Technical indicators library
├── templates/                 # Web dashboard templates
├── static/                    # CSS, JS, images
├── tests/                     # Test suite (17 tests)
├── logs/                      # Application logs
├── data/                      # Market data storage
└── docs/                      # Documentation
```

## 🧪 Testing

### Comprehensive Test Suite (17 Tests - 100% Passing)
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_strategies.py -v
python -m pytest tests/test_integration.py -v

# Test with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

### Test Coverage
- ✅ **Strategy Tests**: Enhanced entry/exit conditions
- ✅ **Technical Indicators**: MACD, RSI, Stochastic RSI
- ✅ **Risk Management**: Position sizing, order validation
- ✅ **Integration Tests**: Full system functionality
- ✅ **Order Management**: Execution and tracking

## 📈 Performance Monitoring

### Built-in Monitoring Tools
```bash
# System health check
python monitor.py --health

# Create backups
python monitor.py --backup

# Full maintenance routine
python monitor.py --full

# Generate performance reports
python monitor.py --report
```

### Key Metrics Tracked
- **Strategy Performance**: Win rate, Sharpe ratio, max drawdown
- **Signal Quality**: Accuracy, signal-to-noise ratio
- **Risk Metrics**: Position sizing, stop-loss effectiveness
- **System Health**: Database integrity, log sizes, disk space

## 🌐 Web Dashboard

Access the interactive dashboard at `http://localhost:5000`

### Dashboard Features
- 📊 **Real-time Portfolio**: Live positions and P&L
- 📈 **Interactive Charts**: Price action with technical indicators
- 🎛️ **Strategy Controls**: Start/stop, parameter adjustment
- 📋 **Trade History**: Detailed execution logs
- ⚡ **Live Signals**: Real-time buy/sell recommendations
- 🚨 **Risk Alerts**: Position and loss limit notifications

## 🔒 Security & Risk Management

### Production Security Checklist
- [ ] Update default SECRET_KEY
- [ ] Set PAPER_TRADING=False only after thorough testing
- [ ] Use HTTPS in production
- [ ] Secure API credentials (never commit to code)
- [ ] Set up proper logging and monitoring
- [ ] Configure firewall and access controls
- [ ] Regular backups and disaster recovery

### Risk Controls
- **Position Sizing**: Maximum 10% of capital per position
- **Daily Loss Limits**: Automatic shutdown at 2% daily loss
- **Stop-Loss Orders**: Configurable risk-based stops
- **Order Validation**: Pre-execution risk checks
- **Paper Trading**: Comprehensive testing environment

## 📚 Documentation

- 📖 **[Strategy Enhancements](STRATEGY_ENHANCEMENTS.md)**: Technical indicator details
- 🚀 **[Deployment Guide](DEPLOYMENT.md)**: Production deployment instructions
- 🧪 **[Test Results](TEST_RESULTS.md)**: Comprehensive test analysis
- 🔧 **[API Documentation](API.md)**: REST API reference

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/enhancement`)
3. Run tests (`python -m pytest tests/ -v`)
4. Commit changes (`git commit -am 'Add enhancement'`)
5. Push to branch (`git push origin feature/enhancement`)
6. Create Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**Important**: This software is for educational and research purposes. Trading involves substantial risk of loss. Always:
- Start with paper trading
- Test thoroughly before live trading
- Never risk more than you can afford to lose
- Understand that past performance doesn't guarantee future results

## 🆘 Support

### Getting Help
1. Check the [troubleshooting guide](DEPLOYMENT.md#troubleshooting)
2. Review logs: `tail -f logs/mybreeze.log`
3. Run health check: `python monitor.py --health`
4. Open an issue with detailed information

### Performance Issues
- Monitor resource usage: `python monitor.py --health`
- Optimize database: Regular cleanup of old data
- Check API rate limits: Implement request throttling
- Review log levels: Use appropriate verbosity in production

---

<p align="center">
  <strong>🎯 Built for serious algorithmic traders who demand precision, reliability, and advanced technical analysis.</strong>
</p>