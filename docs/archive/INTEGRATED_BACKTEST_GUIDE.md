# Integrated Backtesting & Paper Trading Suite

Complete guide for testing, optimizing, and running strategies without real money.

---

## 🎯 Overview

This suite provides three integrated components:

1. **Backtesting Engine** - Test strategies on historical data
2. **Parameter Optimizer** - Find optimal parameters for maximum returns
3. **Paper Trading Runner** - Simulate live trading without real money

---

## 📋 Quick Start

### 1. Run Comprehensive Backtest
```bash
python run_backtest.py
```
Tests 4 basic strategies (Buy & Hold, SMA Crossover, RSI, Momentum) on sample data.

**Output:**
- Comparison of all strategies
- Performance metrics (return, Sharpe, max drawdown)
- Visualization chart: `backtest_results.png`

---

### 2. Run Integrated Backtest with Optimization
```bash
python run_integrated_backtest.py
```
Advanced backtesting with real/realistic data and parameter optimization.

**Features:**
- ✅ Retrieves real data from Breeze API (or generates realistic data)
- ✅ Optimizes SMA parameters (short/long windows)
- ✅ Optimizes RSI parameters (period, oversold, overbought levels)
- ✅ Simulates paper trades with your optimized parameters
- ✅ Generates comparison analysis chart

**Output:**
- Optimal parameters for each strategy
- Paper trading results
- Visualization chart: `integrated_backtest_analysis.png`

---

### 3. Run Live Paper Trading
```bash
python run_paper_trader.py
```
Continuous paper trading simulation with configurable strategies.

**Features:**
- Runs in background with continuous monitoring
- Fetches live prices from Breeze API
- Executes paper trades based on strategy signals
- Tracks portfolio performance
- Saves state to JSON file

**Output:**
- Log file: `paper_trading.log`
- State file: `paper_trading_state.json`
- Real-time console updates

---

## 📊 Strategy Types

### SMA Crossover
- **Concept**: Buy when fast MA crosses above slow MA, sell on crossover below
- **Parameters**: Short window (10-30), Long window (40-100)
- **Best for**: Trending markets
- **Typical performance**: 0.5-2% returns on historical data

### RSI Mean Reversion
- **Concept**: Buy when oversold (RSI < 30), sell when overbought (RSI > 70)
- **Parameters**: Period (8-20), Oversold threshold (20-40), Overbought threshold (60-80)
- **Best for**: Range-bound markets
- **Typical performance**: 5-15% returns with higher volatility

### Momentum (ROC)
- **Concept**: Buy when momentum positive, sell when negative
- **Parameters**: ROC period (10-20), entry threshold (1-3%), exit threshold (-1-0%)
- **Best for**: Volatile markets
- **Typical performance**: 8-12% returns

### Buy & Hold
- **Concept**: Buy at start, hold for entire period
- **Parameters**: None (passive strategy)
- **Best for**: Bull markets
- **Typical performance**: Depends on market trend

---

## ⚙️ Parameter Optimization

### What Gets Optimized

**SMA Strategy:**
- Short window: 10-30 days (step 5)
- Long window: 40-100 days (step 5)
- Generates 45 parameter combinations tested

**RSI Strategy:**
- Period: 8-16 days (step 2)
- Oversold: 20-40 (step 5)
- Overbought: 60-80 (step 5)
- Generates 56 parameter combinations tested

### Optimization Metrics

Each combination is scored on:
- **Return %**: Total profit/loss percentage
- **Sharpe Ratio**: Risk-adjusted returns (higher = better)
- **Win Rate**: % of profitable trades
- **Max Drawdown**: Largest decline (lower = better)

### Output

```
Best SMA Parameters:
  Short Window: 30 | Long Window: 65
  Return: 0.69% | Sharpe: -0.19
  Win Rate: 100% | Max DD: -2.55%

Best RSI Parameters:
  Period: 10 | Oversold: 40 | Overbought: 65
  Return: 12.27% | Sharpe: 0.65
  Win Rate: 75% | Max DD: -22.73%
```

---

## 📝 Paper Trading Configuration

Edit `run_paper_trader.py` to customize:

```python
config = {
    'initial_capital': 100000,           # Starting capital in ₹
    'update_interval': 3600,             # Update every 3600 seconds (1 hour)
    'watchlist': [                       # Stocks to monitor
        'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR'
    ],
    'strategies': [                      # Strategies to run
        {
            'name': 'SMA Crossover - RELIANCE',
            'symbol': 'RELIANCE',
            'type': 'sma_crossover',
            'params': {'short_window': 30, 'long_window': 65}
        },
        {
            'name': 'RSI Mean Reversion - RELIANCE',
            'symbol': 'RELIANCE',
            'type': 'rsi_reversal',
            'params': {'period': 10, 'oversold': 40, 'overbought': 65}
        }
    ]
}
```

---

## 📈 Interpreting Results

### Key Metrics

| Metric | Good Value | Interpretation |
|--------|-----------|-----------------|
| Return | > 5% | Annual return target |
| Sharpe Ratio | > 1.0 | Risk-adjusted returns |
| Win Rate | > 60% | % of profitable trades |
| Max Drawdown | < -5% | Largest portfolio decline |
| Profit Factor | > 1.5 | Ratio of gains to losses |

### Example Results

```
✅ Good Strategy:
- Return: 12%
- Sharpe: 0.65
- Win Rate: 75%
- Max DD: -22%
→ Deploy to paper trading for 2 weeks

⚠️ Marginal Strategy:
- Return: 0.5%
- Sharpe: -0.2
- Win Rate: 50%
- Max DD: -2%
→ Needs parameter tuning or rejection

❌ Poor Strategy:
- Return: -5%
- Sharpe: -1.5
- Win Rate: 30%
- Max DD: -45%
→ Reject and try different parameters
```

---

## 🚀 Deployment Workflow

### Phase 1: Backtesting (1 day)
```bash
python run_backtest.py
python run_integrated_backtest.py
```
✅ Verify strategies work on historical data
✅ Find optimal parameters
✅ Identify best performers

### Phase 2: Paper Trading (1-2 weeks)
```bash
python run_paper_trader.py
```
✅ Monitor signal generation
✅ Track realized vs unrealized P&L
✅ Verify parameters match backtest
✅ Document all trades

### Phase 3: Live Trading (after paper trading success)
```bash
# Use app/services/live_trading.py
# Start with reduced position size (50% of planned)
# Gradually scale up over weeks
```
✅ Execute real trades with small size
✅ Monitor daily performance
✅ Adjust parameters based on live data

---

## ⚠️ Risk Management

### Position Sizing
```python
# Never risk more than 1-2% per trade
position_size = (portfolio_value * 0.01) / stop_loss_distance

# Typical allocation
- First trade: ₹5,000 (5%)
- Scale to: ₹10,000 (10%) after 2 weeks
- Scale to: ₹20,000 (20%) after 1 month
```

### Stop Loss Rules
- Always set stop losses on entry
- Typical: 2-4% below entry price
- Trailing stops for winners (protect profits)

### Position Limits
```python
# Maximum concurrent positions: 4
# Maximum sector concentration: 2 positions
# Daily loss limit: 1-1.5% of portfolio
# Maximum leverage: 1.0x (no margin trading)
```

---

## 🔍 Monitoring & Alerts

### Key Monitoring Points
- Daily P&L vs backtest expectations
- Signal quality (too many false signals?)
- Performance by sector
- Drawdown periods
- Capital utilization

### Alert Thresholds
- Daily loss > 1.5% → STOP TRADING, REVIEW
- Win rate drops < 50% → PAUSE, ANALYZE
- Sharpe < 0.5 for 5 days → ADJUST PARAMETERS
- Drawdown > -10% → REDUCE POSITION SIZE

---

## 📊 Analyzing Results

### Check Consistency
```python
# Compare backtest vs paper trading
backtest_return = 12.27%
paper_trading_return = ?  # Should be within ±2%

# If divergence > 3%:
# - Check market conditions (trending vs range-bound)
# - Verify parameter implementation
# - Adjust strategy or parameters
```

### Performance Comparison
```
RELIANCE (Last 180 days)
Buy & Hold:         +20% ✅
SMA Optimal:        +0.7% ⚠️
RSI Optimal:        +12.3% ✅

Recommendation: Deploy RSI strategy
```

---

## 🛠️ Troubleshooting

### Issue: "No trades generated"
- RSI never hits oversold/overbought threshold
- Solution: Adjust thresholds (40-65 instead of 30-70)

### Issue: "High drawdowns but positive returns"
- Strategy generates few large losing trades
- Solution: Tighten stop losses or increase Sharpe threshold

### Issue: "Paper trading returns differ from backtest"
- Market conditions changed (trend → range-bound)
- Slippage not modeled in backtest
- Solution: Include transaction costs in backtest

### Issue: "Breeze API connection failed"
- Session token expired
- Solution: Get fresh token from https://api.icicidirect.com/apiuser/login?api_key=YOUR_KEY

---

## 📚 Files Reference

| File | Purpose |
|------|---------|
| `run_backtest.py` | Basic strategy comparison |
| `run_integrated_backtest.py` | Advanced backtest + optimization |
| `run_paper_trader.py` | Live paper trading runner |
| `paper_trading.log` | Detailed trading log |
| `paper_trading_state.json` | Current portfolio state |
| `integrated_backtest_analysis.png` | Performance charts |

---

## 🎓 Learning Resources

### Understanding Indicators
- **SMA**: Simple Moving Average - Trend identification
- **RSI**: Relative Strength Index - Momentum measurement
- **MACD**: Moving Average Convergence Divergence - Trend confirmation
- **Volume**: Position confirmation signal

### Backtesting Best Practices
1. Use sufficient historical data (6-24 months minimum)
2. Test on multiple symbols
3. Verify with walk-forward analysis
4. Include transaction costs
5. Test different market regimes

### Paper Trading Best Practices
1. Run for at least 2 weeks
2. Use realistic position sizes
3. Document every trade
4. Compare vs benchmarks
5. Only deploy live after 80%+ win rate

---

## 💡 Tips & Tricks

### Optimize Faster
```bash
# Reduce optimization range for quick tests
sma_results = optimizer.optimize_sma_strategy(
    short_window_range=(20, 30),  # Reduced from 10-30
    long_window_range=(50, 70),   # Reduced from 40-100
    step=5
)
```

### Focus on Quality
- Prefer strategies with:
  - Sharpe > 1.0
  - Win rate > 60%
  - Drawdown < 10%
  - Few trades (quality > quantity)

### Multi-Strategy Approach
```python
# Run multiple strategies on different stocks
strategies = [
    {'symbol': 'RELIANCE', 'type': 'sma'},      # Trending stock
    {'symbol': 'INFY', 'type': 'rsi'},          # Range-bound stock
    {'symbol': 'TCS', 'type': 'momentum'}       # Volatile stock
]
# Allocate 25-35% to each for diversification
```

---

## 🚀 Next Steps

1. ✅ Run `run_integrated_backtest.py` to find optimal parameters
2. ✅ Run `run_paper_trader.py` for 2 weeks of simulation
3. ✅ Compare paper trading results vs backtest
4. ✅ If consistent, deploy to live trading with 50% position size
5. ✅ Scale positions up gradually as confidence builds

---

## 📞 Support

For issues or questions:
1. Check `paper_trading.log` for error messages
2. Review backtest results for parameter validation
3. Verify Breeze API connection with `test_auth_smoke.py`
4. Compare strategy performance on multiple symbols

---

**Good luck! May your strategies be profitable! 📈💰**
