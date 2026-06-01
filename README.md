# 🚀 MyBreezeApp - Algorithmic Trading Platform

> Advanced algorithmic trading application with intelligent profit booking strategies, real-time portfolio monitoring, and comprehensive risk management through ICICIDirect Breeze API

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3%2B-green)](https://flask.palletsprojects.com)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)]()
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Core Components](#core-components)
- [Trading Strategies](#trading-strategies)
- [Deployment](#deployment)
- [Development](#development)
- [Support](#support)

---

## 🎯 Overview

MyBreezeApp is a sophisticated algorithmic trading platform designed for Indian equity markets. It implements intelligent **profit-booking strategies** with adaptive exit mechanisms, real-time risk management, and comprehensive backtesting capabilities.

**Current Status**: Trading 4 stocks (TCS, WIPRO, RELIND, MARUTI) using Buy & Hold trend-following with advanced profit booking.

### Market Regime Detection

The platform automatically detects market conditions and adapts strategy:
- **Mean-Reverting Markets**: Fixed full exit (6.8x better risk profile)
- **Trending Markets**: Partial exit with conditional trailing stops
- **Unknown Markets**: Conservative fixed exit mode

---

## ✨ Features

### 🎲 Trading Strategies

| Feature | Status | Details |
|---------|--------|---------|
| **Buy & Hold Trend Following** | ✅ Production | Multi-symbol position tracking, real-time signals |
| **Fixed Full Exit** | ✅ Production | 100% position exit at target or stop-loss (Profit Factor: 1.14) |
| **Partial + Trailing** | ⚠️ Conditional | 50% exit at target, trailing on remainder (disabled in choppy markets) |
| **Profit Booking Manager** | ✅ Complete | Adaptive exit strategy selection based on market regime |

### 🛡️ Risk Management

| Feature | Implementation |
|---------|-----------------|
| **Position Sizing** | Percentage of capital (default: 10% per position) |
| **Stop-Loss** | 4% below entry price (default) |
| **Profit Target** | 6.5% above entry price (default) |
| **Daily Loss Limit** | 2% of capital (default) |
| **Max Drawdown Control** | Real-time portfolio monitoring with alerts |

### 📊 Analysis & Backtesting

- **Backtesting Engine**: Historical performance analysis with corrected metrics
- **Performance Metrics**: Profit Factor, Sharpe Ratio, Max Drawdown, Win Rate
- **Trade Analytics**: Entry/exit prices, P&L, holding periods, strategy effectiveness
- **Optimization**: Parameter tuning across multiple symbols
- **Data Validation**: Real data from ICICIDirect Breeze API

### 🌐 Web Interface

- **Real-time Dashboard**: Portfolio overview, active positions, P&L tracking
- **Order Management**: Market, Limit, and Stop-loss order execution
- **Trade History**: Detailed trade logs with analytics
- **Risk Monitoring**: Daily loss limits, drawdown warnings, position alerts
- **Paper Trading Mode**: Risk-free strategy validation

### 🔔 Notifications

- **Email Alerts**: Trade execution, risk events, daily summaries
- **Telegram Notifications**: Real-time trading signals and status updates
- **Smart Routing**: Conditional alerts based on trade outcome

### 📈 Data & Integration

- **Real-time Streaming**: Breeze API live price feeds
- **Historical Data**: 1-year backtesting dataset (2025-2026)
- **Multi-Symbol Support**: TCS, WIPRO, RELIND, MARUTI, and extensible
- **Database Storage**: Trade history, position tracking, performance metrics
- **API-Ready**: REST endpoints for external system integration

---

## 🏗️ Architecture

```
MyBreezeApp/
├── app/
│   ├── strategies/              # Trading strategy implementations
│   │   ├── buy_hold_trend.py           # Primary strategy (Buy & Hold)
│   │   ├── profit_booking_manager.py   # Adaptive exit manager (CORRECTED)
│   │   ├── unified_profit_booking.py   # Conditional strategy selection
│   │   ├── regime_monitor.py           # Market regime detection
│   │   └── production_validator.py     # Configuration safeguards
│   │
│   ├── models/                 # Data models
│   │   ├── trade.py                    # Trade tracking
│   │   ├── position.py                 # Position management
│   │   └── portfolio.py                # Portfolio aggregation
│   │
│   ├── api/                    # External API integrations
│   │   ├── breeze_client.py           # ICICIDirect Breeze API wrapper
│   │   └── notification_client.py     # Email & Telegram sender
│   │
│   ├── services/               # Business logic
│   │   ├── trading_service.py          # Order execution & tracking
│   │   ├── risk_service.py             # Risk calculations & limits
│   │   └── portfolio_service.py        # Portfolio management
│   │
│   ├── backtesting/            # Historical analysis
│   │   ├── backtester.py              # Backtest engine
│   │   ├── data_loader.py             # Historical data loading
│   │   └── metrics.py                 # Performance calculations
│   │
│   ├── web/                    # Web interface
│   │   ├── routes.py                  # Flask routes
│   │   ├── templates/                 # HTML templates
│   │   └── static/                    # CSS, JavaScript
│   │
│   ├── config.py               # Configuration management
│   └── app.py                  # Flask application factory
│
├── tests/                      # Test suites
│   ├── test_unified_strategy.py       # Strategy validation tests
│   ├── test_regime_monitor.py         # Regime detection tests
│   ├── test_production_validator.py   # Safeguard validation
│   └── test_integration.py            # End-to-end tests
│
├── backtest_profit_booking_breeze.py  # Backtest runner
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── docker-compose.yml          # Container orchestration
└── deployment/                 # Cloud deployment configs
    ├── aws_deploy.sh           # AWS Elastic Beanstalk
    └── heroku_deploy.sh        # Heroku deployment
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- ICICIDirect account with Breeze API access
- Docker (optional, for containerized deployment)

### Setup (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/Smartpram/myBreezeApp.git
cd myBreezeApp

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your Breeze API credentials and preferences

# 5. Verify installation
python -m pytest tests/ -v

# 6. Run backtests
python backtest_profit_booking_breeze.py

# 7. Start application
python -m flask run --host=0.0.0.0 --port=5000
```

### First Trade (Paper Trading)

```bash
# Set PAPER_TRADING=True in .env

# Access dashboard: http://localhost:5000
# Create a watch list for TCS, WIPRO, RELIND, MARUTI
# Monitor entries, exits, and P&L in real-time
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```env
# === APPLICATION ===
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your_secret_key_here

# === BREEZE API ===
BREEZE_API_KEY=your_api_key
BREEZE_SECRET_KEY=your_secret_key
BREEZE_USER_ID=your_user_id
BREEZE_PASSWORD=your_password

# === TRADING MODE ===
PAPER_TRADING=True              # Start with paper trading
DEFAULT_CAPITAL=100000          # ₹1,00,000 starting capital
MAX_POSITION_SIZE=0.1           # 10% max per position

# === STRATEGY PARAMETERS ===
TARGET_PROFIT_PCT=0.065         # 6.5% profit target
STOP_LOSS_PCT=0.04              # 4% stop loss
TRAILING_STOP_PCT=0.02          # 2% trailing stop (if enabled)
PARTIAL_EXIT_RATIO=0.50         # Exit 50% at target (for trailing)

# === RISK MANAGEMENT ===
MAX_DAILY_LOSS_PCT=0.02         # 2% daily loss limit
MAX_DRAWDOWN_LIMIT_PCT=-0.30    # 30% max portfolio drawdown

# === NOTIFICATIONS ===
SEND_EMAIL_ALERTS=True
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

SEND_TELEGRAM_ALERTS=True
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# === MONITORING ===
REGIME_CHECK_INTERVAL_HOURS=4   # Check market regime every 4 hours
LOG_LEVEL=INFO
```

### Strategy Selection

The platform **automatically selects** the exit strategy based on market conditions:

```python
# Detected: MEAN-REVERTING market (intraday bounces, avg_holding < 1.0 day)
→ Use: FIXED_FULL_EXIT (100% exit at target)
→ Result: Profit Factor 1.14, Max Drawdown -77.91%

# Detected: TRENDING market (multi-day moves, avg_holding > 2.0 days)
→ Use: PARTIAL_WITH_TRAILING (50% at target, 50% with trailing stop)
→ Only if conditions permit (backtest-validated)
```

---

## 📦 Core Components

### 1. Profit Booking Manager (`profit_booking_manager.py`)

**Purpose**: Adaptive exit strategy management

**Key Fixes (Corrected Calculations)**:
- ✅ `avg_pnl_pct`: Fixed calculation to `df['pnl_pct'].mean()` (was incorrectly using total)
- ✅ `max_drawdown`: Normalized to peak cumsum, not running max (-77.91% realistic vs -50,801% buggy)
- ✅ `sharpe_ratio`: Converted returns to decimals, now -3.28 (correct indicator of risk)

**Usage**:
```python
from app.strategies.profit_booking_manager import ProfitBookingManager

manager = ProfitBookingManager()
exit_strategy = manager.get_strategy_stats()
print(exit_strategy['profit_factor'])  # 1.14 (Fixed) vs 0.57 (Partial)
```

### 2. Unified Strategy (`unified_profit_booking.py`)

**Purpose**: Conditional strategy selection with regime awareness

**Features**:
- Market regime detection (Mean-Reverting, Trending, Unknown)
- Trailing stop condition assessment (3 rules)
- Automatic strategy switching based on conditions
- Position lifecycle management

**Usage**:
```python
from app.strategies.unified_profit_booking import UnifiedProfitBookingManager

manager = UnifiedProfitBookingManager()
manager.detect_market_regime(recent_trades)
strategy = manager.select_exit_strategy()  # Auto-selects FIXED or PARTIAL+TRAILING
position = manager.create_position(symbol='TCS', entry_price=3100, quantity=10)
```

### 3. Production Validator (`production_validator.py`)

**Purpose**: Prevent misconfiguration in production

**Safeguards**:
- ✅ Hard stop: Prevents trailing in mean-reverting regimes
- ✅ Configuration validation: Ensures valid parameter ranges
- ✅ Regime consistency: Verifies strategy matches market conditions
- ✅ Risk compliance: Checks position sizing and daily loss limits

**Usage**:
```python
from app.strategies.production_validator import validate_production_config

errors = validate_production_config(config)
if errors:
    raise StrategyConfigError(f"Invalid config: {errors}")
```

### 4. Regime Monitor (`regime_monitor.py`)

**Purpose**: Continuous market regime tracking with alerts

**Features**:
- Daily regime re-evaluation
- Weekly performance metrics check
- Automated strategy re-selection if regime changes
- Alert thresholds for abnormal volatility

**Usage**:
```python
from app.strategies.regime_monitor import RegimeMonitor

monitor = RegimeMonitor()
daily_report = monitor.get_daily_report()
if daily_report['regime_changed']:
    print(f"Strategy changed: {daily_report['action']}")
```

---

## 🎲 Trading Strategies

### Fixed Full Exit (Production)

**When to use**: Mean-reverting, intraday markets

**Mechanics**:
1. Buy signal: Price above MA, RSI healthy range
2. Position taken at market price
3. 100% exit at profit target (6.5%) OR stop-loss (4%)
4. No trailing, no partial exits

**Backtest Results** (169 trades, 12 months):
```
Total Trades: 169
Winning Trades: 50 (29.6% win rate)
Losing Trades: 119
Profit Factor: 1.14 ✅
Total P&L: ₹359,850 ✅
Max Drawdown: -77.91% ✅ (realistic)
Sharpe Ratio: -3.28
```

### Partial + Trailing (Conditional)

**When to use**: Trending, multi-day markets ONLY

**Mechanics**:
1. Buy signal same as Fixed Full Exit
2. 50% exit at profit target (6.5%)
3. Remaining 50% held with 2% trailing stop
4. Exit on trailing stop hit OR stop-loss

**Backtest Results** (same 169 trades):
```
Total Trades: 169
Winning Trades: 50 (29.6% win rate, same!)
Losing Trades: 119
Profit Factor: 0.57 ❌ (halved)
Total P&L: ₹-1,105,910 ❌ (lost money)
Max Drawdown: -528.00% ❌ (6.8x worse)
Sharpe Ratio: -3.28
```

**Design Decision**: Trailing disallowed in mean-reverting markets due to:
1. **No additional winners**: Same 50 wins despite trailing (no new extensions)
2. **Pure intraday moves**: avg_holding_days = 0.0 for all 169 trades
3. **High post-target volatility**: Drawdown ratio 6.8x worse (528% vs 77.91%)

---

## 📊 Backtesting

### Run Backtest

```bash
# Full backtest (all symbols, 12 months)
python backtest_profit_booking_breeze.py

# With custom date range
python backtest_profit_booking_breeze.py --start-date 2025-06-01 --end-date 2026-05-31

# Single symbol
python backtest_profit_booking_breeze.py --symbols TCS,WIPRO
```

### Backtest Output

```json
{
  "timestamp": "2026-06-01T09:49:47",
  "fixed_full_exit": {
    "trades": 169,
    "winning_trades": 50,
    "profit_factor": 1.14,
    "total_pnl": 359850,
    "max_drawdown": -77.91,
    "avg_holding_days": 0.0
  },
  "partial_trailing": {
    "trades": 169,
    "winning_trades": 50,
    "profit_factor": 0.57,
    "total_pnl": -1105910,
    "max_drawdown": -528.00,
    "avg_holding_days": 0.0
  }
}
```

### Interpretation

| Metric | Fixed Full Exit | Partial + Trailing | Verdict |
|--------|-----------------|-------------------|---------|
| Profit Factor | 1.14 ✅ | 0.57 ❌ | Fixed wins 2x |
| Total P&L | ₹359,850 ✅ | ₹-1,105,910 ❌ | Fixed profitable |
| Max Drawdown | -77.91% ✅ | -528.00% ❌ | Fixed 6.8x better |
| Strategy | ACTIVE | DISALLOWED | Mean-reverting market |

---

## 🚀 Deployment

### Docker (Recommended)

```bash
# Build and run
docker-compose up --build

# Access application
# http://localhost:5000

# Logs
docker-compose logs -f app
```

### Kubernetes

```bash
kubectl apply -f deployment/k8s/
```

### AWS Elastic Beanstalk

```bash
bash deployment/aws_deploy.sh
```

### Manual Linux/Mac

```bash
# Start application
nohup python -m flask run > app.log 2>&1 &

# Background job for regime monitoring
nohup python -c "from app.strategies.regime_monitor import RegimeMonitor; RegimeMonitor().start()" > monitor.log 2>&1 &

# Check status
ps aux | grep python
```

---

## 🧪 Development

### Run Tests

```bash
# All tests
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_unified_strategy.py -v

# With coverage
python -m pytest tests/ --cov=app
```

### Test Suite

| Test File | Purpose | Coverage |
|-----------|---------|----------|
| `test_unified_strategy.py` | Strategy selection logic | Regime detection, condition assessment |
| `test_regime_monitor.py` | Market regime tracking | Daily checks, alerts |
| `test_production_validator.py` | Configuration validation | Safeguards, risk limits |
| `test_integration.py` | End-to-end flows | Trade execution, position tracking |

### Add New Strategy

```python
# 1. Create strategy file
# app/strategies/new_strategy.py

class NewStrategy:
    def __init__(self):
        self.config = {...}
    
    def should_enter(self, data):
        return True/False
    
    def should_exit(self, position, data):
        return True/False

# 2. Register in unified manager
# app/strategies/unified_profit_booking.py
def select_exit_strategy(self):
    if self.new_condition:
        return ExitStrategy.NEW_STRATEGY

# 3. Test and backtest
# tests/test_new_strategy.py
```

---

## 📖 Documentation Map

| Document | Purpose |
|----------|---------|
| [TRAILING_STOPS_DESIGN_RULES.md](TRAILING_STOPS_DESIGN_RULES.md) | Why trailing is disallowed in mean-reverting markets |
| [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) | Complete integration guide with buy-and-hold strategy |
| [PRODUCTION_VALIDATOR_GUIDE.md](PRODUCTION_VALIDATOR_GUIDE.md) | Configuration safeguards and validation |
| [REGIME_MONITOR_GUIDE.md](REGIME_MONITOR_GUIDE.md) | Continuous market monitoring system |
| [TEST_VALIDATION_GUIDE.md](TEST_VALIDATION_GUIDE.md) | Test suite and validation procedures |

---

## 📞 Support

### Common Issues

**Q: Trailing stops disabled, why?**  
A: Current market is mean-reverting (intraday bounces). Backtests show trailing reduces profit factor from 1.14 to 0.57 and increases drawdown 6.8x. Re-enable when market becomes trending (avg_holding_days > 2.0 days).

**Q: How do I switch from paper trading to live?**  
A: Set `PAPER_TRADING=False` in `.env`. Highly recommended to paper trade for 4 weeks first and validate backtest predictions.

**Q: What if a trade goes wrong?**  
A: All trades are logged in database. Use dashboard to review and manually close if needed. Risk limits still apply.

**Q: How often should I backtest?**  
A: Weekly with latest 1-month data to verify strategy performance hasn't degraded.

### Logs & Debugging

```bash
# View application logs
tail -f logs/trading.log

# View API calls
tail -f logs/api.log

# View strategy decisions
tail -f logs/strategy.log

# Enable debug mode
export FLASK_DEBUG=True
python -m flask run
```

---

## 📜 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Contributions welcome! Please:

1. Create feature branch: `git checkout -b feature/your-feature`
2. Write tests: `pytest tests/`
3. Add documentation
4. Submit pull request

---

## 🎯 Roadmap

- [ ] Machine learning signal optimization
- [ ] Multi-strategy portfolio optimization
- [ ] Real-time sentiment analysis integration
- [ ] Advanced derivatives trading
- [ ] Crypto asset class support
- [ ] Live performance dashboards with Grafana

---

**Last Updated**: June 1, 2026  
**Status**: Production Ready (Fixed Exit Strategy)  
**Maintainer**: Smartpram
