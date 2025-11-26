# MyBreezeApp - Algorithmic Trading Application

This is a comprehensive algorithmic trading application built with ICICIDirect Breeze API, implementing a Buy and Hold trend-following positional strategy.

## Project Status
- [x] Project Structure Created
- [x] Core Components Implemented
- [x] Flask Web Application
- [x] Trading Strategy Implementation
- [x] Risk Management System
- [x] Backtesting Engine
- [x] Web Dashboard & Templates
- [x] Docker Configuration
- [x] AWS Deployment Scripts
- [x] Unit Tests Framework
- [ ] Dependencies Installation
- [ ] Configuration Setup
- [ ] Production Testing

## Features Implemented
- **Trading Core**: Real-time data streaming, order execution (Market/Limit/Stop-loss), paper trading mode
- **Strategy**: Buy & Hold trend-following with technical indicators (RSI, MA, volume analysis)
- **Risk Management**: Stop-loss, targets, trailing stops, position sizing, daily loss limits
- **Backtesting**: Historical data analysis, performance metrics, strategy optimization
- **Web Interface**: Real-time dashboard, portfolio monitoring, trade management
- **Notifications**: Email and Telegram alerts for trades and risk events
- **Security**: OAuth authentication, JWT sessions, secure API endpoints
- **Deployment**: Docker containers, AWS Elastic Beanstalk deployment scripts
- **Performance**: Sharpe ratio, max drawdown, win rate, profit factor calculations

## Architecture
- Flask web framework with modular service architecture
- Real-time data streaming and WebSocket support
- Comprehensive risk management and order execution system
- Advanced backtesting engine with performance analytics
- Responsive web dashboard with interactive charts