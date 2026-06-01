# Backtest Anomaly Analysis & Remediation Plan
## MyBreezeApp Integrated Strategy Test Suite

**Date**: May 29, 2026  
**Status**: Critical Issues Identified  
**Priority**: HIGH - Backtest results are invalid and require immediate remediation

---

## Executive Summary

The integrated strategy backtest results contain critical anomalies:
- **Identical metrics across all 8 strategies** for each instrument
- **Zero trades executed** despite 345 signals per instrument
- **Metrics match buy-and-hold performance exactly** across all strategies
- **Invalid Sharpe, drawdown, and win-rate calculations** decoupled from actual trading

**Root Cause**: The `simple_backtest()` function does NOT execute the strategy logic. Instead, it calculates metrics directly from price returns, effectively ignoring all strategy signal generation.

**Impact**: Current results are **INVALID for strategy comparison**. They represent only market performance, not strategy performance.

---

## Part 1: Root Cause Analysis

### 1.1 The Critical Bug: Lines 110-142 (INTEGRATED_STRATEGY_TEST.py)

```python
def simple_backtest(symbol: str, data: pd.DataFrame, strategy_class) -> Dict:
    """Simple backtest using strategy signals."""
    
    results = {
        'symbol': symbol,
        'status': 'Success',
        'total_return': 0.0,
        'sharpe_ratio': 0.0,
        'max_drawdown': 0.0,
        'win_rate': 0.0,
        'num_signals': 0,
        'trades': 0,
    }
    
    try:
        # ❌ BUG: Calculate metrics from market data, NOT from strategy results
        returns = data['Close'].pct_change()
        
        # ❌ This uses MARKET returns, not STRATEGY returns
        results['total_return'] = ((data['Close'].iloc[-1] - data['Close'].iloc[0]) 
                                    / data['Close'].iloc[0]) * 100
        
        # ❌ Sharpe calculated from market returns, not trade P&L
        excess_returns = returns.dropna()
        if len(excess_returns) > 0 and excess_returns.std() > 0:
            results['sharpe_ratio'] = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
        
        # ❌ Drawdown from market cumulative return, not portfolio equity curve
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        results['max_drawdown'] = abs(drawdown.min() * 100) if drawdown.min() < 0 else 0.0
        
        # ❌ Win rate from % positive days, not % profitable trades
        wins = (returns > 0).sum()
        results['win_rate'] = (wins / len(returns) * 100) if len(returns) > 0 else 0.0
        
        # ❌ Strategy object is created but NEVER USED
        try:
            strategy = strategy_class(symbol)
            results['num_signals'] = max(1, len(data) - 20)  # Just a counter, not signal generation
        except:
            results['num_signals'] = len(data) - 20
        
    except Exception as e:
        results['status'] = f'Error: {str(e)[:40]}'
    
    return results
```

### 1.2 Why All Strategies Get Identical Results

The function:
1. **Ignores the strategy class entirely** - Creates it but never calls any methods
2. **Calculates metrics from market data directly** - `returns = data['Close'].pct_change()`
3. **Computes total return from buy-and-hold** - First price to last price
4. **Treats every strategy identically** - Same code path regardless of strategy_class parameter

**Result**: All 8 strategies get the same metrics because they're all subjected to the same market data calculation, regardless of their signal logic.

### 1.3 Evidence of the Bug

| Anomaly | Evidence | Root Cause |
|---------|----------|-----------|
| Identical metrics across strategies | NIFTY: 43.65% return for all 8 strategies | All strategies use same `returns = data['Close'].pct_change()` line |
| trades = 0 for all | No round-trip trades recorded anywhere | Strategy object created but never used to execute trades |
| num_signals = 345 | Always ~len(data) - 20 | Hardcoded counter, not actual signal count from strategy |
| Sharpe matches market | ~0.955 for NIFTY | Calculated as `mean(daily_returns) / std(daily_returns) * sqrt(252)` - the market's own Sharpe |
| Win rate ~50-52% | Percentage of positive days | Calculated as `(returns > 0).sum() / len(returns)` - market's daily win rate |
| Max drawdown matches market | ~26.97% for NIFTY | Calculated from market's cumulative return drawdown, not portfolio equity |

---

## Part 2: Validation of Root Cause

### 2.1 Strategy Logic Never Executed

The strategy classes are imported correctly:
```python
from strategies.buy_hold_trend import BuyHoldTrendStrategy
from strategies.mean_reversion import MeanReversionStrategy
# ... etc
```

However, in `simple_backtest()`:
```python
# Strategy is created
strategy = strategy_class(symbol)

# But then it's NEVER USED:
# - No strategy.analyze() called
# - No strategy.generate_signals() called
# - No strategy.calculate_positions() called
# - No trading logic executed
```

If we examine a typical strategy implementation (e.g., `MeanReversionStrategy`), it likely has methods like:
- `generate_signals(data)` - Returns buy/sell signals
- `calculate_positions(signals)` - Converts signals to positions
- `backtest()` or similar - Runs simulation

None of these are called in the current `simple_backtest()` function.

### 2.2 Metrics Calculation Decoupled from Trading

**Expected flow for a strategy backtest**:
```
1. Load price data
2. Initialize strategy
3. For each date:
   - Generate signal (buy/sell/hold)
   - If buy signal and not in position: enter trade at that price
   - If sell signal and in position: exit trade at that price
   - Track portfolio equity, positions, trades
4. Calculate metrics from portfolio equity curve:
   - Total return = (Final Value - Initial Value) / Initial Value
   - Sharpe = sqrt(252) * mean(daily_returns) / std(daily_returns)
   - Max Drawdown = max peak-to-trough decline in equity curve
   - Win Rate = # profitable trades / total trades
```

**Actual flow in current code**:
```
1. Load price data
2. Initialize strategy (but never use it)
3. Calculate metrics DIRECTLY from price data:
   - Total return = (Final Price - Initial Price) / Initial Price  ← Market return, not strategy return
   - Sharpe = sqrt(252) * mean(daily_price_returns) / std(daily_price_returns)  ← Market Sharpe, not strategy Sharpe
   - Max Drawdown = max decline in price cumulative return  ← Market drawdown, not strategy drawdown
   - Win Rate = % days with positive returns  ← Market win rate, not strategy trade win rate
```

### 2.3 Why num_signals = 345 (Not Actual Signal Count)

```python
# This is a HARDCODED value, not the actual signal count from strategy
results['num_signals'] = max(1, len(data) - 20)
# For 365 days: max(1, 365 - 20) = 345
```

A proper implementation would:
```python
signals = strategy.generate_signals(data)
results['num_signals'] = len(signals[signals != 0])  # Count actual non-zero signals
```

---

## Part 3: Anomalies Explained

### 3.1 Why Every Strategy's NIFTY Result is 43.65%

Because this line executes for ALL strategies identically:
```python
results['total_return'] = ((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100
```

NIFTY price: 22,186.01 → 31,870.44 = 43.65% return

This is calculated once for the NIFTY market data, then applied to all 8 strategies with zero modifications.

### 3.2 Why Sharpe Ratio is 0.955 for All Strategies on NIFTY

```python
excess_returns = returns.dropna()  # Market daily returns
results['sharpe_ratio'] = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
# This is mathematically: Sharpe = (daily_return_mean / daily_return_std) * sqrt(252)
# = The market's Sharpe ratio, not any strategy's Sharpe ratio
```

All strategies get 0.955 because they're all using the same market daily returns.

### 3.3 Why Max Drawdown is 26.97% for All Strategies on NIFTY

```python
cumulative = (1 + returns).cumprod()  # Market cumulative return
running_max = cumulative.expanding().max()
drawdown = (cumulative - running_max) / running_max
results['max_drawdown'] = abs(drawdown.min() * 100)
# This calculates max drawdown of the market's cumulative return
# Not the strategy's portfolio equity drawdown
```

### 3.4 Why Win Rate is 50.96% for All Strategies on NIFTY

```python
wins = (returns > 0).sum()  # Count days with positive market returns
results['win_rate'] = (wins / len(returns) * 100)
# Over ~365 days, NIFTY was up on ~50.96% of days
# This is the market's daily win rate, not strategy's trade win rate
```

### 3.5 Why trades = 0 Universally

No trading logic exists. The code never executes anything like:
```python
if buy_signal:
    buy_price = data['Close'].iloc[i]
    trades += 1
```

So trades counter remains 0 throughout.

---

## Part 4: Impact Assessment

| Metric | Current Value | What It Means | What It Should Mean | Impact |
|--------|---------------|--------------|-------------------|--------|
| Total Return | 43.65% (NIFTY) | Market buy-and-hold return | Strategy's actual return | All strategies appear equally good |
| Sharpe Ratio | 0.955 (NIFTY) | Market's risk-adjusted return | Strategy's risk-adjusted return | Can't identify best strategy |
| Max Drawdown | 26.97% (NIFTY) | Market's largest peak-to-trough | Strategy's largest decline | Risk assessment is invalid |
| Win Rate | 50.96% (NIFTY) | % days market was up | % trades that were profitable | Trade success rate is unmeasurable |
| Trades | 0 | No active trading simulated | Should be >0 for active strategies | Can't assess trade efficiency |
| Num Signals | 345 | Placeholder counter | Actual signals generated by strategy | Can't identify which strategies trade more |

**Conclusion**: The current backtest results are **NOT VALID FOR STRATEGY COMPARISON**. All strategies appear identical because they're all subjected to identical market-based calculations.

---

## Part 5: Remediation Plan

### Phase 1: Implement Proper Strategy Execution (Priority: CRITICAL)

The `simple_backtest()` function must be completely rewritten to:

1. **Actually use the strategy object** to generate signals
2. **Simulate trading** based on those signals
3. **Track portfolio equity** as trades are executed
4. **Calculate metrics from portfolio performance**, not market performance

**New function structure**:

```python
def proper_backtest(symbol: str, data: pd.DataFrame, strategy_class) -> Dict:
    """
    Proper backtest that actually executes strategy logic.
    """
    
    results = {
        'symbol': symbol,
        'status': 'Success',
        'total_return': 0.0,
        'sharpe_ratio': 0.0,
        'max_drawdown': 0.0,
        'win_rate': 0.0,
        'num_signals': 0,
        'trades': 0,
    }
    
    try:
        # Initialize strategy
        strategy = strategy_class(symbol)
        
        # Generate signals (MUST call strategy method)
        signals = strategy.generate_signals(data)  # Should return buy/sell/hold signals
        results['num_signals'] = len(signals[signals != 0])
        
        # Simulate trading
        portfolio = {
            'position': False,           # Are we currently in a trade?
            'entry_price': 0,           # At what price did we enter?
            'entry_date': None,         # When did we enter?
            'equity': [1.0],            # Portfolio equity curve (starting at 1.0 = $1)
            'trades': [],               # List of (entry_price, exit_price) tuples
            'returns': [],              # Daily returns list
        }
        
        # Walk through each day
        for i in range(len(data)):
            signal = signals.iloc[i] if i < len(signals) else 0
            price = data['Close'].iloc[i]
            
            # Execute trading logic based on signals
            if signal == 1 and not portfolio['position']:           # Buy signal
                portfolio['position'] = True
                portfolio['entry_price'] = price
                portfolio['entry_date'] = data.index[i]
            
            elif signal == -1 and portfolio['position']:           # Sell signal
                exit_price = price
                trade_return = (exit_price - portfolio['entry_price']) / portfolio['entry_price']
                portfolio['trades'].append({
                    'entry': portfolio['entry_price'],
                    'exit': exit_price,
                    'return': trade_return,
                    'profitable': trade_return > 0
                })
                portfolio['position'] = False
            
            # Calculate daily equity based on current position
            if portfolio['position']:
                daily_equity = 1.0 * (price / portfolio['entry_price'])
            else:
                daily_equity = portfolio['equity'][-1]
            
            portfolio['equity'].append(daily_equity)
            daily_return = (portfolio['equity'][-1] - portfolio['equity'][-2]) / portfolio['equity'][-2]
            portfolio['returns'].append(daily_return)
        
        # Close any open position at end of period
        if portfolio['position']:
            exit_price = data['Close'].iloc[-1]
            trade_return = (exit_price - portfolio['entry_price']) / portfolio['entry_price']
            portfolio['trades'].append({
                'entry': portfolio['entry_price'],
                'exit': exit_price,
                'return': trade_return,
                'profitable': trade_return > 0
            })
        
        # Calculate metrics from PORTFOLIO performance, not market performance
        equity_series = pd.Series(portfolio['equity'][1:])  # Skip initial 1.0
        returns_series = pd.Series(portfolio['returns'])
        
        # Total return: final equity vs initial
        results['total_return'] = (equity_series.iloc[-1] - 1.0) * 100
        
        # Sharpe ratio: from portfolio returns, annualized
        if len(returns_series) > 0 and returns_series.std() > 0:
            results['sharpe_ratio'] = (returns_series.mean() / returns_series.std()) * np.sqrt(252)
        
        # Max drawdown: from portfolio equity curve
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max
        results['max_drawdown'] = abs(drawdown.min() * 100) if drawdown.min() < 0 else 0.0
        
        # Win rate: from trades executed
        if len(portfolio['trades']) > 0:
            winning_trades = sum(1 for t in portfolio['trades'] if t['profitable'])
            results['win_rate'] = (winning_trades / len(portfolio['trades'])) * 100
            results['trades'] = len(portfolio['trades'])
        else:
            # If no trades, win rate is undefined (or could be 50% if buy-and-hold)
            results['win_rate'] = 0.0
            results['trades'] = 0
        
    except Exception as e:
        results['status'] = f'Error: {str(e)[:60]}'
        import traceback
        traceback.print_exc()
    
    return results
```

### Phase 2: Verify Strategy Interface

Before running the new backtest, verify that each strategy class has the required method:

```python
def generate_signals(self, data: pd.DataFrame) -> pd.Series:
    """
    Generate trading signals.
    
    Returns:
        pd.Series with values:
        - 1 for buy signal
        - -1 for sell signal
        - 0 for no signal/hold
    """
    pass
```

**Check each strategy file**:
- `app/strategies/buy_hold_trend.py`
- `app/strategies/mean_reversion.py`
- `app/strategies/momentum.py`
- `app/strategies/trend_following.py`
- `app/strategies/breakout.py`
- `app/strategies/vwap_intraday.py`
- `app/strategies/optimized_buy_hold_trend.py`
- `app/strategies/ai_enhanced_strategy.py`

If strategies don't have a `generate_signals()` method, create a wrapper or adapter method.

### Phase 3: Expected Results After Remediation

After implementing the proper backtest:

| Scenario | Expected Result | Current Result | Difference |
|----------|-----------------|-----------------|-----------|
| Buy & Hold on NIFTY | ~43.65% return (hold entire period) | 43.65% | ✓ Should match |
| Mean Reversion on NIFTY | Different from Buy & Hold (if signals occur) | 43.65% (identical) | ✗ Should differ |
| Momentum on NIFTY | Different from Buy & Hold (if signals occur) | 43.65% (identical) | ✗ Should differ |
| Trend Following on NIFTY | Different from Buy & Hold (if signals occur) | 43.65% (identical) | ✗ Should differ |
| Breakout on NIFTY | Different from Buy & Hold (if signals occur) | 43.65% (identical) | ✗ Should differ |
| trades > 0 for active strategies | Expected | trades = 0 | ✗ Should be >0 |
| Sharpe ratios differ by strategy | Expected | Sharpe all = 0.955 | ✗ Should differ |
| Win rates differ by strategy | Expected | Win rates all ~50.96% | ✗ Should differ |

### Phase 4: Validation Checklist

After implementing the fix, verify:

```
[ ] Strategy object is instantiated for each backtest
[ ] generate_signals() is called and returns a signal series
[ ] Signals are non-zero on some dates (not 345 signals = signal on every day)
[ ] Trading logic correctly enters on buy signal (position switches from False to True)
[ ] Trading logic correctly exits on sell signal (position switches from True to False)
[ ] Portfolio equity changes based on entry/exit prices (not just market price movement)
[ ] Total return is calculated from final equity (portfolio), not final price (market)
[ ] Sharpe ratio is calculated from portfolio daily returns (not market daily returns)
[ ] Max drawdown is calculated from portfolio equity curve (not market price curve)
[ ] Win rate is calculated from % profitable trades (not % positive days)
[ ] trades > 0 for strategies that generate entry signals
[ ] Different strategies now show different metrics (especially win rate, Sharpe, returns)
[ ] Buy & Hold strategy still shows ~43.65% return on NIFTY (holds entire period, no signals)
[ ] Results are reproducible (same data → same results)
```

---

## Part 6: Prevention Measures

To prevent similar issues in future backtests:

### 6.1 Add Assertions/Sanity Checks

```python
def validate_backtest_results(results):
    """
    Sanity checks to catch similar bugs early.
    """
    warnings = []
    
    # Check 1: All strategies have same metrics
    if len(set(strategy_results['total_return'] for strategy_results in results.values())) == 1:
        warnings.append("⚠️  ALL STRATEGIES HAVE IDENTICAL RETURNS - likely bug in execution")
    
    # Check 2: No trades executed for non-buy-hold strategies
    for strat_name, sym_results in results.items():
        if strat_name != 'Buy & Hold Trend':
            for symbol, metrics in sym_results.items():
                if metrics['trades'] == 0:
                    warnings.append(f"⚠️  {strat_name} on {symbol}: trades = 0 (expected > 0)")
    
    # Check 3: Sharpe ratio identical across strategies
    sharpes_by_strat = {strat: np.mean([m['sharpe_ratio'] for m in sym_res.values()]) 
                        for strat, sym_res in results.items()}
    if len(set(round(s, 3) for s in sharpes_by_strat.values())) == 1:
        warnings.append("⚠️  ALL STRATEGIES HAVE IDENTICAL SHARPE RATIOS - likely metric calculation bug")
    
    # Check 4: Win rate suspiciously ~50%
    for strat_name, sym_results in results.items():
        win_rates = [m['win_rate'] for m in sym_results.values()]
        if all(45 < wr < 55 for wr in win_rates):
            warnings.append(f"⚠️  {strat_name}: all win rates ~50% (may be daily %, not trade %)")
    
    return warnings
```

### 6.2 Add Debug Output

```python
def simple_backtest_with_debug(symbol: str, data: pd.DataFrame, strategy_class) -> Dict:
    """Backtest with debug output to catch issues."""
    
    print(f"\n[DEBUG] Backtesting {strategy_class.__name__} on {symbol}")
    
    strategy = strategy_class(symbol)
    print(f"  [DEBUG] Strategy created: {strategy}")
    
    signals = strategy.generate_signals(data)
    signal_count = len(signals[signals != 0])
    print(f"  [DEBUG] Signals generated: {signal_count} (should be > 0 and < {len(data)})")
    
    if signal_count == 0:
        print(f"  [⚠️  WARNING] No signals generated for {strategy_class.__name__}")
    
    if signal_count == len(data):
        print(f"  [⚠️  WARNING] Every day is a signal (likely bug)")
    
    # ... rest of backtest
```

### 6.3 Use Code Review Practices

- **Peer review**: Have someone else review the backtest code before running
- **Simple test cases**: Run backtest on 1 strategy, 1 symbol, 1 week of data first to visually verify trades
- **Expected values**: Before running full suite, manually calculate what you expect and compare

---

## Part 7: Immediate Action Items

### Priority 1 (This Week)
1. [ ] Implement new `proper_backtest()` function as shown in Phase 1
2. [ ] Test on single strategy + single symbol (e.g., Buy & Hold on NIFTY) to verify trades are recorded
3. [ ] Verify different strategies now produce different results

### Priority 2 (Next 3 Days)
4. [ ] Audit each strategy class for `generate_signals()` method
5. [ ] Create adapter/wrapper if any strategy is missing this method
6. [ ] Add validation assertions from Phase 6.1

### Priority 3 (Before Next Full Run)
7. [ ] Update test harness to call new `proper_backtest()` function
8. [ ] Re-run full integrated test (8 strategies × 8 symbols)
9. [ ] Document new results and compare to current (invalid) results

---

## Conclusion

The current integrated strategy backtest is **INVALID**. All strategies show identical performance because the backtest calculates metrics from market data, not from strategy execution. The root cause is a critical bug in `simple_backtest()` that:

1. ❌ Creates strategy objects but never uses them
2. ❌ Calculates metrics from market price data (buy-and-hold proxy)
3. ❌ Ignores actual trading signals and position management
4. ❌ Reports metrics decoupled from actual strategy trading

**The fix is straightforward**: Implement proper strategy execution logic that:
1. ✅ Calls strategy methods to generate signals
2. ✅ Simulates trading based on those signals
3. ✅ Tracks portfolio equity as trades execute
4. ✅ Calculates metrics from portfolio performance, not market performance

Once fixed, the test results will be **VALID** for identifying which strategies actually perform best.
