# 🚀 GreeksMaster - Professional Options Trading Platform

> Intelligent options trading platform for Indian derivatives markets with advanced Greeks management, multi-leg spread strategies, dynamic exit optimization, and comprehensive risk monitoring through ICICIDirect Breeze API

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3%2B-green)](https://flask.palletsprojects.com)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)]()
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

---

## 📋 Quick Navigation

- **[🎯 Core Features](#-core-features)** - What the system does
- **[🏗️ Architecture](#-architecture)** - How it's organized
- **[⚡ Quick Start](#-quick-start)** - Get running in 10 minutes
- **[📚 Documentation](#-documentation-structure)** - Find what you need
- **[📊 Features](#-all-features)** - Complete feature list
- **[🚀 Deployment](#-deployment)** - Deploy to production
- **[💬 Support](#-support)** - Get help

---

## 📚 Documentation Structure

Our documentation is organized by feature for easy navigation:

### 🔌 **MCP Server** (AI Automation)
Run your trading system as an MCP server for Claude/AI integration
- **Start here:** `docs/features/MCP_SERVER/MCP_SERVER_QUICK_START.md`
- Architecture: `docs/features/MCP_SERVER/MCP_SERVER_IMPLEMENTATION_BLUEPRINT.md`
- Deployment: `docs/features/MCP_SERVER/MCP_DEPLOYMENT_GUIDE.md`
- Quick ref: `docs/features/MCP_SERVER/MCP_QUICK_REFERENCE.md`

### 📈 **Paper Trading** (Testing & Learning)
Test strategies and learn before live trading
- **Start here:** `docs/features/PAPER_TRADING/PAPER_TRADING_START_HERE.md`
- Quick start: `docs/features/PAPER_TRADING/START_PAPER_TRADING_NOW.md`
- Scripts: `scripts/paper_trading/`

### 💼 **Trade Management** (Live Trading)
Manage open positions, exits, and portfolio
- **Start here:** `docs/features/TRADE_MANAGEMENT/START_TRADE_MANAGEMENT_HERE.md`
- Complete guide: `docs/features/TRADE_MANAGEMENT/TRADE_MANAGEMENT_COMPLETE_DELIVERY.md`

### 📊 **Strategies** (Trading Logic)
Complete guide to all 4 trading strategies
- `docs/features/STRATEGIES/ALL_STRATEGIES_COMPREHENSIVE_GUIDE.md`

### 📖 **Reference & Updates**
General information and status
- `docs/reference/` - Reference documentation
- `docs/archived/` - Legacy documentation

---

## 🎯 Core Features

### 1️⃣ **Market Scanning & Signal Generation**
Automated detection of trading opportunities with machine learning-enhanced filtering.

**What You Get:**
- ✅ Continuous market scans across multiple symbols
- ✅ Trend-following entry signals (SMA20 crossover + RSI validation)
- ✅ Sentiment gate (NIFTY-based macro filtering)
- ✅ Multi-symbol support (TCS, WIPRO, RELIND, MARUTI, INFTEC, etc.)
- ✅ Real-time data integration via Breeze API
- ✅ AI signal validation (confidence scoring)

**Files:**
- `app/strategies/buy_hold_trend.py` - Screener logic
- `backtest/backtest_screener_trend_confirmation.py` - Screener validation

**Get Started:**
```bash
python app/strategies/buy_hold_trend.py  # Run screener
```

---

### 2️⃣ **Smart Signal Validation & Guardrails**
Before any trade executes, production validators ensure safety and market conditions are favorable.

**What You Get:**
- ✅ Configuration safety checks (position sizing, stops realistic)
- ✅ Market regime detection (trending vs ranging vs unknown)
- ✅ Entry gating (avoid bad market conditions)
- ✅ Production environment validation
- ✅ Risk pre-flight checks

**Files:**
- `app/strategies/production_validator.py` - Configuration validation
- `app/strategies/regime_monitor.py` - Market regime detection
- `app/market_sentiment_gate.py` - Sentiment-based entry filtering
- `app/ai_signal_validator.py` - AI confidence scoring

**How It Works:**
```
Signal Generated → Validator Checks → Regime Assessed → Entry Approved/Blocked
```

---

### 3️⃣ **Intelligent Position Sizing & Risk Management**
Automatic position sizing based on account equity and risk parameters.

**What You Get:**
- ✅ Dynamic position sizing (% of capital / entry price)
- ✅ Automatic stop-loss placement (entry - 4%, configurable)
- ✅ Profit target calculation (entry + 6.5%, configurable)
- ✅ Margin management
- ✅ Portfolio exposure limits
- ✅ Daily loss limit enforcement (2% default)

**Files:**
- `app/services/trading_service.py` - Position calculation
- `app/services/risk_service.py` - Risk enforcement

**Configuration:**
```python
MAX_POSITION_SIZE = 2.0           # % of account per trade
STOP_LOSS_PCT = 1.0               # 1% below entry
PROFIT_TARGET_PCT = 2.0           # 2% above entry
DAILY_LOSS_LIMIT = 1.0            # % of account per day
```

---

### 4️⃣ **Trade Execution via Breeze API**
Direct market orders with real-time order placement and confirmation.

**What You Get:**
- ✅ Market order execution (buy/sell)
- ✅ Limit orders with dynamic pricing
- ✅ Stop-loss order placement
- ✅ Order status tracking
- ✅ Real-time P&L monitoring
- ✅ Position tracking and aggregation
- ✅ Portfolio margin monitoring

**Files:**
- `app/api/breeze_client.py` - Breeze API wrapper
- `app/services/trading_service.py` - Order execution

**Example:**
```python
from app.api.breeze_client import BreezeClient

client = BreezeClient(api_key="your_key")
order = client.place_order(
    symbol="TCS",
    quantity=10,
    price=3100.0,
    order_type="MARKET"
)
```

---

### 5️⃣ **Dynamic Exit Strategy - Trade Management Layer**
Advanced exit optimization using SuperTrend indicators, context scoring, and historical pattern analysis.

**What You Get:**
- ✅ SuperTrend trend regime detection
- ✅ 4-axis context scoring (volume, time, range, custom)
- ✅ Historical pivot analysis (no look-ahead bias)
- ✅ Conditional density scoring
- ✅ Layered exit rules:
  - Full exit at high confidence (score ≥ 99)
  - Tighten stops at good zones (score ≥ 90, P&L > 20%)
  - Partial exits at favorable zones (score ≥ 80, P&L > 20%)
  - Profit targets (2% gain)
  - Stop losses (1% loss)

**Expected Results:**
- Win Rate: +1-2% improvement
- Avg P&L: +20-40% better per trade
- Drawdown: -2-3% reduction

**Files:**
- `app/trade_management_layer.py` - Complete system (600+ lines)
- `examples/trade_management_integration.py` - Integration example

**Quick Start:**
```python
from app.trade_management_layer import TradeManagementLayer

manager = TradeManagementLayer()
report = manager.analyze_trade(
    df=price_data,
    symbol="AXISBANK",
    pnl_pct=15.0,
    entry_price=1100.0
)

action = report['decision']['exit_action']  # HOLD, PARTIAL_EXIT, TIGHTEN_STOP, FULL_EXIT
```

**Documentation:**
- `TRADE_MANAGEMENT_QUICK_REFERENCE.md` - Quick start (5 min)
- `TRADE_MANAGEMENT_LAYER_GUIDE.md` - Full guide (30 min)
- `TRADE_MANAGEMENT_DEPLOYMENT_CHECKLIST.md` - Integration steps (45 min)

---

### 6️⃣ **Options Strategy Engine**
Multi-leg spread creation and optimization for options trading.

**What You Get:**
- ✅ Call/Put selection (delta-based)
- ✅ Multi-leg spreads (straddles, strangles, call spreads, put spreads)
- ✅ Greeks calculation (Delta, Gamma, Theta, Vega)
- ✅ Spread optimization (max profit/max loss)
- ✅ Implied volatility analysis
- ✅ Option chain filtering

**Files:**
- `app/strategies/options_engine.py` - Strategy construction
- `app/services/greeks_service.py` - Greeks calculation

---

### 7️⃣ **Real-time Portfolio Monitoring**
Live dashboard and position tracking.

**What You Get:**
- ✅ Real-time P&L tracking
- ✅ Active positions display
- ✅ Greeks aggregation (portfolio-level Greeks)
- ✅ Risk metrics (drawdown, daily loss, volatility)
- ✅ Trade history and analytics
- ✅ Performance reporting

**Access:**
```bash
python run.py  # Start web server at http://localhost:5000
```

---

### 8️⃣ **Backtesting & Validation**
Historical performance analysis before live trading.

**What You Get:**
- ✅ Full historical backtesting (2024-2025 data available)
- ✅ Performance metrics:
  - Win rate, profit factor, Sharpe ratio
  - Max drawdown, average holding time
  - P&L distribution, monthly returns
- ✅ Per-trade analytics
- ✅ Strategy comparison
- ✅ Parameter optimization
- ✅ Monte Carlo simulation (optional)

**Run Backtest:**
```bash
# Backtest screener with sentiment gate
python backtest/backtest_trading_engine_with_ai.py

# Backtest with range policy
python backtest_trading_engine_with_ai.py --range-policy

# Backtest Phase 5 paper trading
python backtest/phase5_paper_trading_enhanced.py
```

**Example Output:**
```
Win Rate: 50.1%
Profit Factor: 1.24
Sharpe Ratio: 0.89
Max Drawdown: -8.4%
Avg Holding: 2.3 days
Total Trades: 124
Winning: 62
Losing: 62
```

---

### 9️⃣ **Risk Monitoring & Alerts**
Continuous portfolio health monitoring with real-time alerts.

**What You Get:**
- ✅ Daily P&L tracking
- ✅ Max drawdown monitoring
- ✅ Stop-loss enforcement
- ✅ Daily loss limits
- ✅ Email alerts
- ✅ Telegram notifications (optional)
- ✅ Risk metrics dashboard

**Configuration:**
```python
DAILY_LOSS_LIMIT = 1.0       # % of account
MAX_DRAWDOWN = 5.0           # % from peak
ALERT_EMAIL = "admin@example.com"
ENABLE_TELEGRAM = True
```

---

### 🔟 **Comprehensive Backtesting Infrastructure**
Production-grade backtesting system for strategy validation.

**What You Get:**
- ✅ Multiple timeframe testing (5m, 15m, daily)
- ✅ Real historical data (NSE stocks)
- ✅ Commissions & slippage modeling
- ✅ Regime-aware testing (trending vs ranging)
- ✅ Parameter sensitivity analysis
- ✅ Walk-forward testing
- ✅ Out-of-sample validation

**Files:**
- `backtest/backtest_trading_engine_with_ai.py` - Main backtest engine
- `backtest/backtest_screener_trend_confirmation.py` - Screener backtest
- `backtest_trading_engine.py` - Simple backtest

---

## 🏗️ Architecture

### System Layers (Feature-Based Organization)

```
┌──────────────────────────────────────────────────────────┐
│         PRESENTATION LAYER (Dashboard & Alerts)          │
│  • Real-time web interface (Flask)                       │
│  • Email & Telegram notifications                         │
│  • Mobile-friendly views                                  │
└──────────────────────────────────────────────────────────┘
                            ↑↓
┌──────────────────────────────────────────────────────────┐
│      TRADING & RISK MANAGEMENT LAYER                     │
│  • Trade execution & position management                 │
│  • Real-time P&L tracking                                │
│  • Risk enforcement (stops, limits)                      │
│  • Exit decision engine (Trade Management)               │
│  • Portfolio aggregation                                 │
└──────────────────────────────────────────────────────────┘
                            ↑↓
┌──────────────────────────────────────────────────────────┐
│      STRATEGY & VALIDATION LAYER                         │
│  • Signal generation (screener)                          │
│  • Validation & guardrails                               │
│  • Market regime detection                               │
│  • Sentiment gating                                      │
│  • AI signal validation                                  │
│  • Options strategy engine                               │
└──────────────────────────────────────────────────────────┘
                            ↑↓
┌──────────────────────────────────────────────────────────┐
│      DATA & API LAYER                                    │
│  • Breeze API integration (orders, data, margin)        │
│  • Real-time price feeds                                 │
│  • Historical data loading                               │
│  • Greeks calculation (Black-Scholes)                    │
│  • Options chain data                                    │
└──────────────────────────────────────────────────────────┘
```

### Directory Structure

```
GreeksMaster/
├── 📚 Documentation/
│   ├── README.md (this file)
│   ├── TRADE_MANAGEMENT_QUICK_REFERENCE.md
│   ├── TRADE_MANAGEMENT_LAYER_GUIDE.md
│   └── docs/ (full documentation)
│
├── 🎯 Core Application/
│   ├── app/
│   │   ├── app.py                           # Flask application factory
│   │   ├── config.py                        # Configuration management
│   │   ├── __init__.py
│   │   │
│   │   ├── 🔍 Signal Generation
│   │   │   ├── strategies/
│   │   │   │   ├── buy_hold_trend.py        # Trend-following screener
│   │   │   │   ├── options_engine.py        # Options strategy builder
│   │   │   │   └── profit_booking_manager.py
│   │   │   │
│   │   ├── ✅ Validation & Guardrails
│   │   │   ├── strategies/
│   │   │   │   ├── production_validator.py  # Config validation
│   │   │   │   ├── regime_monitor.py        # Market regime detection
│   │   │   │   └── unified_profit_booking.py
│   │   │   ├── market_sentiment_gate.py     # Sentiment-based gating
│   │   │   └── ai_signal_validator.py       # AI confidence scoring
│   │   │
│   │   ├── 💳 Execution & Risk
│   │   │   ├── services/
│   │   │   │   ├── trading_service.py       # Order execution
│   │   │   │   ├── risk_service.py          # Risk enforcement
│   │   │   │   ├── portfolio_service.py     # Position aggregation
│   │   │   │   └── notification_service.py  # Alerts & emails
│   │   │   ├── api/
│   │   │   │   ├── breeze_client.py         # Breeze API wrapper
│   │   │   │   └── notification_client.py   # Email/Telegram
│   │   │   └── models/
│   │   │       ├── position.py              # Position data model
│   │   │       └── trade.py                 # Trade record
│   │   │
│   │   ├── 🎯 Exit Strategy
│   │   │   └── trade_management_layer.py    # Dynamic exit optimization
│   │   │
│   │   ├── 📊 Greeks & Analysis
│   │   │   ├── services/
│   │   │   │   └── greeks_service.py        # Greeks calculation
│   │   │   └── greeks.py                    # Black-Scholes models
│   │   │
│   │   ├── 🌐 Web Interface
│   │   │   ├── web/
│   │   │   │   ├── routes.py                # Flask routes
│   │   │   │   ├── templates/               # HTML templates
│   │   │   │   └── static/                  # CSS, JavaScript
│   │   │   └── api_routes.py                # REST API endpoints
│   │   │
│   │   └── 🛠️ Utilities
│   │       ├── utils/
│   │       │   ├── data_loader.py           # Data loading
│   │       │   ├── logger.py                # Logging setup
│   │       │   └── constants.py             # Constants
│   │       └── cache/                       # Caching layer
│   │
│   ├── 🧪 Testing
│   │   ├── tests/
│   │   │   ├── test_screener.py             # Screener tests
│   │   │   ├── test_validator.py            # Validator tests
│   │   │   ├── test_execution.py            # Execution tests
│   │   │   └── test_trade_management.py     # Exit strategy tests
│   │   └── fixtures/                        # Test data
│   │
│   ├── 📈 Backtesting
│   │   ├── backtest/
│   │   │   ├── backtest_trading_engine_with_ai.py  # Main backtest
│   │   │   ├── backtest_screener_trend_confirmation.py
│   │   │   ├── phase5_paper_trading_enhanced.py    # Paper trading
│   │   │   └── metrics.py                   # Performance metrics
│   │   └── historical_data/                 # Historical data cache
│   │
│   └── 🚀 Deployment
│       ├── run.py                           # Entry point
│       ├── requirements.txt                 # Dependencies
│       ├── .env.example                     # Environment template
│       ├── Dockerfile                       # Container definition
│       └── docker-compose.yml               # Orchestration
│
└── 📊 Data/
    ├── historical_data/                     # Cached OHLCV data
    ├── backtest_results/                    # Backtest outputs
    └── paper_trading_logs/                  # Paper trading records
```

---

## ⚡ Quick Start

### Installation (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/smartpram/greeksmaster.git
cd greeksmaster

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your Breeze API credentials
```

### Running the System

```bash
# Start web dashboard (http://localhost:5000)
python run.py

# Run screener manually
python app/strategies/buy_hold_trend.py

# Run backtest
python backtest/backtest_trading_engine_with_ai.py

# Run paper trading
python backtest/phase5_paper_trading_enhanced.py
```

### First Trade (Paper Trading)

```bash
# 1. Read quick reference
cat TRADE_MANAGEMENT_QUICK_REFERENCE.md  # 5 min

# 2. Backtest strategy
python backtest/backtest_trading_engine_with_ai.py  # 5 min

# 3. Run paper trading for 4 weeks
python backtest/phase5_paper_trading_enhanced.py  # 4 weeks

# 4. Monitor performance
# Visit http://localhost:5000 for dashboard
```

---

## 📚 Complete Guide

### Feature Documentation

| Feature | Guide | Time | Files |
|---------|-------|------|-------|
| **1. Signal Generation** | See `app/strategies/buy_hold_trend.py` | 15 min | screener logic |
| **2. Validation & Guardrails** | See `app/strategies/production_validator.py` | 15 min | validator, regime |
| **3. Position Sizing** | See `app/services/trading_service.py` | 10 min | trading service |
| **4. Trade Execution** | See `app/api/breeze_client.py` | 15 min | Breeze integration |
| **5. Exit Strategy** | `TRADE_MANAGEMENT_LAYER_GUIDE.md` | 30 min | Trade Management |
| **6. Options Engine** | See `app/strategies/options_engine.py` | 20 min | options strategy |
| **7. Portfolio Monitoring** | Dashboard at `http://localhost:5000` | 10 min | web interface |
| **8. Backtesting** | See `backtest/` directory | 30 min | backtesting |
| **9. Risk Monitoring** | See `app/services/risk_service.py` | 15 min | risk enforcement |
| **10. Infrastructure** | See deployment section below | 30 min | deployment |

---

## 🔄 Trading Pipeline

### Complete End-to-End Workflow

```
┌─────────────────────────────────────────────────────────┐
│ 1. SIGNAL GENERATION                                    │
│    • Screener scans TCS, WIPRO, RELIND, MARUTI         │
│    • Detects: SMA20 crossover + RSI healthy            │
│    • Output: "TCS setup detected @ 3100"               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. VALIDATION & MARKET REGIME                           │
│    • Production Validator: Config safe? ✅             │
│    • Regime Monitor: Market trending or ranging?       │
│    • Sentiment Gate: NIFTY sentiment OK?               │
│    • AI Validator: Confidence score high?              │
│    • Decision: APPROVE / REJECT                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. POSITION SIZING & EXECUTION                          │
│    • Calculate: qty = (capital × 2%) / 3100 = 100     │
│    • Place order: Buy 100 TCS @ market                 │
│    • Set stop-loss: 3100 - 31 = 3069                  │
│    • Set profit target: 3100 + 62 = 3162              │
│    • Position: OPEN                                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 4. POSITION MONITORING                                 │
│    • Track Trade Management recommendations            │
│    • Monitor: SuperTrend, context score, volume       │
│    • Decision logic: Exit when favorable zone found   │
│    • Options: Hold / Scale 50% / Tighten stop / Exit  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 5. EXIT EXECUTION                                       │
│    • Condition met: Context score ≥ 80, P&L +25%     │
│    • Action: Scale out 50%, trail stop 2%             │
│    • Or: Hit profit target 3162 → Close 100%          │
│    • Or: Hit stop-loss 3069 → Close 100%              │
│    • Position: CLOSED                                  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 6. RISK FEEDBACK & NEXT SIGNAL                         │
│    • Update: Daily P&L, max drawdown, regime          │
│    • Log: Trade result, holding time, strategy used   │
│    • Alert: Email/Telegram sent if needed             │
│    • Resume: Back to Signal Generation step           │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Backtesting

### How to Backtest

**Quick Test (2 minutes):**
```bash
python backtest/backtest_trading_engine_with_ai.py --quick
```

**Full Backtest (10 minutes):**
```bash
python backtest/backtest_trading_engine_with_ai.py
```

**With Range Policy (capital preservation):**
```bash
python backtest/backtest_trading_engine_with_ai.py --range-policy
```

**Paper Trading (4 weeks):**
```bash
python backtest/phase5_paper_trading_enhanced.py
```

### Interpreting Results

```
Win Rate: 50%                    # % of trades that profit
Profit Factor: 1.24              # Total Wins / Total Losses (>1.0 = profitable)
Sharpe Ratio: 0.89               # Risk-adjusted returns
Max Drawdown: -8.4%              # Worst peak-to-trough decline
Avg Holding: 2.3 days            # Average trade duration
Best Day: +₹5,000               # Best single day P&L
Worst Day: -₹2,000              # Worst single day P&L
```

**Success Criteria:**
- Win Rate ≥ 40%
- Profit Factor > 1.0
- Max Drawdown < 10%
- Sharpe Ratio > 0.5

---

## 🚀 Deployment

### Option 1: Local (Development)

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your API keys

# 3. Run
python run.py
```

### Option 2: Docker (Recommended for Production)

```bash
# 1. Build image
docker build -t greeksmaster .

# 2. Run container
docker run -p 5000:5000 --env-file .env greeksmaster

# 3. Access dashboard
# Navigate to http://localhost:5000
```

### Option 3: Docker Compose (Multi-Container)

```bash
# 1. Start services
docker-compose up -d

# 2. Check status
docker-compose ps

# 3. View logs
docker-compose logs -f app

# 4. Stop
docker-compose down
```

### Configuration

Create `.env` file:
```
# Breeze API
BREEZE_API_KEY=your_api_key_here
BREEZE_API_SECRET=your_secret_here

# Trading Parameters
MAX_POSITION_SIZE=2.0
STOP_LOSS_PCT=1.0
PROFIT_TARGET_PCT=2.0
DAILY_LOSS_LIMIT=1.0

# Database
DATABASE_URL=sqlite:///greeksmaster.db

# Notifications
ENABLE_EMAIL=True
ALERT_EMAIL=your_email@example.com
ENABLE_TELEGRAM=False
TELEGRAM_BOT_TOKEN=your_bot_token

# Logging
LOG_LEVEL=INFO
```

---

## 💬 Support

### Getting Help

**Question Type** | **Where to Look**
---|---
How do I use feature X? | See feature section above
How do I backtest? | Run: `python backtest/backtest_trading_engine_with_ai.py`
How do I deploy? | See [Deployment](#-deployment) section
Trade Management questions? | Read: `TRADE_MANAGEMENT_LAYER_GUIDE.md`
API integration? | See: `app/api/breeze_client.py`
Strategy customization? | See: `app/strategies/buy_hold_trend.py`

### Documentation Files

**Quick References:**
- `TRADE_MANAGEMENT_QUICK_REFERENCE.md` - 5-minute overview
- `START_TRADE_MANAGEMENT_HERE.md` - Getting started
- `GREEKSMASTER_QUICKSTART.md` - Platform quickstart

**Comprehensive Guides:**
- `TRADE_MANAGEMENT_LAYER_GUIDE.md` - Exit strategy deep dive
- `TRADE_MANAGEMENT_DEPLOYMENT_CHECKLIST.md` - Integration steps
- `README.md` (this file) - Complete overview

**Technical Details:**
- `TRADE_MANAGEMENT_LAYER_DOCUMENTATION_INDEX.md` - Full index
- `docs/` directory - Additional documentation

---

## 📝 License

MIT License - See LICENSE file for details

---

## 👥 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Add tests for new functionality
4. Submit pull request

---

## 🙏 Acknowledgments

- ICICIDirect Breeze API for market data
- Indian NSE for stock data
- Community feedback and improvements

---

**Last Updated:** June 9, 2026  
**Version:** 2.0 (Feature-Based)  
**Status:** Production Ready ✅

Start with: **[Quick Start](#-quick-start)** ➜ **[Trade Management Guide](TRADE_MANAGEMENT_LAYER_GUIDE.md)** ➜ **[Deployment](#-deployment)**
