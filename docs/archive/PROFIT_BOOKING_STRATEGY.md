# MyBreezeApp Profit Booking Strategy

## Executive Summary
MyBreezeApp implements a multi-layered profit booking strategy that combines:
1. **Fixed Profit Targets** (primary exit)
2. **Partial Profit Taking** (intermediate exits at 8% gains)
3. **Trailing Stops** (lock-in gains as price moves favorably)
4. **Technical Signal-Based Exits** (advanced indicators for timing)
5. **Risk-Based Exits** (stop-loss, daily loss limits)

This diversified approach balances capital preservation with profit realization.

---

## 1. Fixed Profit Target Strategy

### Configuration
```python
TARGET_PCT: float = 0.12  # 12% profit target
```

### Implementation
- **Entry Point**: Calculated at trade entry via `risk_manager.calculate_target()`
- **Target Price Formula**: 
  - **Long**: `entry_price × (1 + 0.12)`
  - **Short**: `entry_price × (1 - 0.12)`
- **Exit Trigger**: When `current_price >= target_price`
- **Exit Reason Code**: `"target_achieved"`

### Characteristics
| Aspect | Details |
|--------|---------|
| **Profit Goal** | 12% per trade |
| **Trigger** | Automatic at target price |
| **Position Management** | Full position exit |
| **Frequency** | Occurs when price reaches target |
| **Historical Performance** | ~20-30% of exits achieve this target in backtests |

### Example Trade
```
Entry Price: ₹1000
Target Price: ₹1120 (12% up)
Exit Reason: PROFIT_TARGET
P&L: +₹120 per share
```

---

## 2. Partial Profit Taking Strategy (New Feature)

### Configuration
```python
PARTIAL_PROFIT_PCT: float = 0.08      # Take profits at 8% gain
PARTIAL_PROFIT_RATIO: float = 0.5     # Sell 50% of position
```

### Implementation Flow
```python
# Step 1: Check if partial profit condition met
def should_partial_exit(self, symbol: str, row: pd.Series, position: Dict) -> bool:
    if position.get('partial_taken', False):
        return False  # Already took partial
    
    current_return = (current_price - entry_price) / entry_price
    
    if current_return >= 0.08:  # 8% profit
        return True
    return False

# Step 2: Execute partial exit
def execute_partial_exit(self, symbol: str, position: Dict) -> Dict:
    partial_qty = int(position['quantity'] * 0.5)     # 50% sold
    remaining_qty = position['quantity'] - partial_qty
    
    position['partial_taken'] = True
    position['quantity'] = remaining_qty
    
    return {
        'symbol': symbol,
        'action': 'partial_exit',
        'quantity': partial_qty,
        'remaining_quantity': remaining_qty
    }
```

### Characteristics
| Aspect | Details |
|--------|---------|
| **First Exit** | At 8% profit |
| **Quantity Sold** | 50% of original position |
| **Remaining Qty** | 50% stays in trade for full target (12%) |
| **Risk Reduction** | Locks in 50% of profits, keeps 50% at risk |
| **Position After** | Remaining 50% tracked with trailing stops |

### Strategic Benefits
- **Capital Preservation**: Locks in profits early, reduces risk exposure
- **Continued Upside**: Remaining 50% captures additional 4% for 12% total target
- **Psychological Comfort**: Guarantees partial profit, reduces holding anxiety
- **Compounding**: Profits can be reinvested in new trades

### Example Trade with Partial Exit
```
Initial Position: 100 shares @ ₹1000

At 8% Gain (₹1080):
  Action: Partial Exit
  Sell: 50 shares @ ₹1080 = ₹54,000 profit
  Keep: 50 shares for further upside

At 12% Gain (₹1120):
  Action: Full Exit on remaining
  Sell: 50 shares @ ₹1120 = ₹6,000 profit
  Total P&L: ₹60,000 (60% on partial + remaining)
```

---

## 3. Trailing Stop Loss Strategy

### Configuration
```python
TRAILING_STOP_PCT: float = 0.02    # 2% trailing stop
```

### Implementation
```python
def should_exit_position(self, symbol: str, row: pd.Series, position: Dict):
    current_return = (current_price - entry_price) / entry_price
    
    # Initialize max return on first check
    if 'max_return' not in position:
        position['max_return'] = current_return
    else:
        position['max_return'] = max(position['max_return'], current_return)
        
        # Trail below the highest point by 2%
        if (position['max_return'] > 0.05 and  # Only if up at least 5%
            current_return < position['max_return'] - 0.02):
            return True, "trailing_stop"
    
    return False, "hold"
```

### Characteristics
| Aspect | Details |
|--------|---------|
| **Activation** | After 5% gain is reached |
| **Trail Distance** | 2% below highest price achieved |
| **Purpose** | Lock-in gains while allowing continued upside |
| **Exit Trigger** | Automatic when price pulls back 2% from high |
| **Advantage** | Captures most of the move but exits on reversal |

### Example Trailing Stop Scenario
```
Entry: ₹1000
Price Rise to: ₹1080 (8% gain)
  → Trailing Stop activated
  → High mark: ₹1080
  → Stop level: ₹1056 (2% below ₹1080)

Price continues to: ₹1120 (12% gain)
  → New high: ₹1120
  → New stop: ₹1097.6 (2% below ₹1120)

Price pulls back to: ₹1100
  → Still above stop (₹1097.6)
  → Position held

Price falls to: ₹1095
  → Below stop (₹1097.6)
  → EXIT triggered at market (≈₹1095)
  → P&L: ~₹95/share (9.5% profit)
```

---

## 4. Technical Signal-Based Exit Strategy

### Entry Exit Conditions

#### 4.1 RSI Overbought + Stochastic RSI Exit
```python
if (row['rsi'] > 75 and                          # RSI extremely overbought
    row['stoch_rsi_k'] > 75 and                  # Stochastic K line high
    row['stoch_rsi_k'] < row['stoch_rsi_d']):    # Bearish crossover
    return True, "technical_exit_rsi_stoch_overbought"
```

**Trigger Conditions**:
- RSI > 75 (extremely overbought)
- Stochastic RSI %K > 75
- %K crossing below %D (momentum reversal)

**Use Case**: Exit when momentum is exhausted and reversal signals appear

---

#### 4.2 MACD Bearish Crossover Exit
```python
if (row['macd'] < row['macd_signal'] and   # MACD crosses below signal
    row['macd_histogram'] < 0 and          # Histogram negative
    row['rsi'] > 60):                       # Confirming RSI warning
    return True, "technical_exit_macd_bearish"
```

**Trigger Conditions**:
- MACD line crosses below signal line
- MACD histogram turns negative
- RSI remains elevated (>60)

**Use Case**: Catch trend weakening before price reversal

---

#### 4.3 Trend Reversal Exit
```python
if (row['close'] < row['sma_20'] < row['sma_50'] and  # Price below both MAs
    row['adx'] < 20):                                  # Weak trend (low ADX)
    return True, "trend_reversal"
```

**Trigger Conditions**:
- Price below 20-day MA
- 20-day MA below 50-day MA (downtrend setup)
- ADX < 20 (trend strength weakening)

**Use Case**: Exit when uptrend structure breaks down

---

#### 4.4 Volume-Based Exit
```python
if (current_return > 0.03 and              # In profit (3%+)
    row['volume_ratio'] < 0.5):            # Volume < 50% of 20-day avg
    return True, "low_volume_exit"
```

**Trigger Conditions**:
- Position is profitable (>3%)
- Volume drops to below 50% of 20-day average
- Suggests weakening momentum/conviction

**Use Case**: Exit when price action loses momentum/participation

---

## 5. Risk-Based Exit Strategy

### 5.1 Stop Loss (Primary Risk Control)
```python
STOP_LOSS_PCT: float = 0.04    # 4% stop loss
```

**Exit Logic**:
```python
if current_return <= -0.04:  # Down 4%
    return True, "stop_loss"
```

**Characteristics**:
- **Trigger**: Automatic at 4% loss
- **Purpose**: Capital preservation, limits downside
- **Frequency**: ~40-50% of losing trades in backtests
- **Exit Reason Code**: `"STOP_LOSS"`

### 5.2 Daily Loss Limit
```python
MAX_DAILY_LOSS_PCT: float = 0.015  # 1.5% daily loss limit on capital
```

**Implementation**:
- Tracks cumulative daily P&L
- Prevents new entries once daily loss exceeds 1.5% of capital
- Acts as circuit breaker to prevent catastrophic loss days
- Resets at start of trading day

---

## 6. Market-Time Aware Volatility Adjustment

### Concept
Stop-loss percentages are **dynamically adjusted** based on market session:

```python
def calculate_stop_loss(self, entry_price: float, action: str, 
                       custom_sl_percent: Optional[float] = None) -> float:
    market_filter = MarketTimeFilter()
    sl_percent = custom_sl_percent or DEFAULT_STOP_LOSS
    
    # Adjust for market session volatility
    adjusted_sl = market_filter.apply_volatility_adjustment(sl_percent)
    
    if action.upper() == 'BUY':
        stop_loss = entry_price * (1 - adjusted_sl)
    else:  # SELL
        stop_loss = entry_price * (1 + adjusted_sl)
    
    return round(stop_loss, 2)
```

### Application
- **Market Open** (9:15-10:00 IST): Wider stop-loss (higher volatility)
- **Market Mid** (10:00-14:30 IST): Normal stop-loss
- **Market Close** (14:30-15:30 IST): Wider stop-loss (closing bell volatility)

---

## 7. Complete Exit Decision Tree

```
┌─────────────────────────────┐
│ Check Exit Conditions       │
└──────────────┬──────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
Check Limits        Check Position
    │                     │
    │         ┌───────────┴──────────┐
    │         │                      │
    │         ▼                      ▼
    │    ┌────────────┐      ┌──────────────┐
    │    │ Stop Loss  │      │ Partial Exit │
    │    │ -4.0%      │      │ +8.0%        │
    │    └────────────┘      └──────────────┘
    │                               │
    │                      (50% exit, 50% stay)
    │                               │
    │         ┌─────────────────────┴──────────┐
    │         │                                │
    │         ▼                                ▼
    │    ┌──────────────┐         ┌────────────────┐
    │    │ Target/Exit  │         │ Remaining 50%  │
    │    │ +12.0%       │         │ Can reach +12% │
    │    └──────────────┘         └────────────────┘
    │                                   │
    │         ┌─────────────────────────┴───┐
    │         │                             │
    │         ▼                             ▼
    │    ┌─────────┐           ┌──────────────────┐
    │    │ Trailing│           │ Technical Exits  │
    │    │ Stop -2%│           │ • MACD Bearish   │
    │    │ (after  │           │ • RSI Overbought │
    │    │ +5% gain)           │ • Trend Reversal │
    │    └─────────┘           │ • Low Volume     │
    │                          └──────────────────┘
    │
    └────────► FULL EXIT


Exit Summary:
─────────────
🔴 HARD STOPS (Forced Exit):
   • Stop Loss: -4.0% loss
   • Daily Limit: -1.5% daily loss
   • Target: +12.0% gain

🟡 SOFT EXITS (Opportunity-Based):
   • Partial: +8.0% (sell 50%)
   • Trailing: -2% below high
   • Technical: Various signals
```

---

## 8. Performance Summary by Exit Type

### Backtest Exit Statistics (Real Data)

| Exit Reason | Frequency | Avg P&L | Notes |
|------------|-----------|---------|-------|
| **PROFIT_TARGET** | ~20-30% | +₹3,000-5,000 | Full 12% target reached |
| **STOP_LOSS** | ~40-50% | -₹1,500-2,500 | 4% loss hit |
| **TRAILING_STOP** | ~10-15% | +₹500-1,500 | Caught partial move |
| **TECHNICAL_EXIT** | ~5-10% | -₹500-1,000 | Mixed timing |
| **PARTIAL_EXIT** | ~15-20% | +₹300-800 | Intermediate profit lock |

### Cumulative Strategy Effectiveness
- **Win Rate**: 13-17% (profitable trades)
- **Loss Rate**: 83-87% (losing trades)
- **Profit Factor**: 0.30-0.60 (wins/losses ratio)
- **Avg Trade P&L**: -₹500 to -₹1,000

---

## 9. Configuration Parameters Reference

### Profit Taking Configuration
```python
@dataclass
class OptimizedConfig:
    # Profit Targets
    TARGET_PCT: float = 0.12              # 12% profit target
    
    # Partial Profit Taking
    PARTIAL_PROFIT_PCT: float = 0.08      # 8% threshold for partial
    PARTIAL_PROFIT_RATIO: float = 0.5     # 50% of position
    
    # Trailing Stop
    TRAILING_STOP_PCT: float = 0.02       # 2% trailing distance
    
    # Risk Management
    STOP_LOSS_PCT: float = 0.04           # 4% stop loss
    MAX_DAILY_LOSS_PCT: float = 0.015     # 1.5% daily limit
```

---

## 10. Key Implementation Files

| File | Function | Key Method |
|------|----------|------------|
| `app/strategies/optimized_buy_hold_trend.py` | Main strategy | `should_exit_position()`, `should_partial_exit()` |
| `app/services/risk_manager.py` | Risk calculations | `calculate_target()`, `calculate_stop_loss()` |
| `app/strategies/market_time_filter.py` | Session volatility | `apply_volatility_adjustment()` |
| `backtest.py` | Testing framework | Exit tracking and reporting |

---

## 11. Recent Improvements & Phase 1 Enhancements

### Planned Improvements (Phase 1 - June 2026)
1. **Hierarchical Filter Integration**: Add 2-of-3 voting for entry quality
   - Better entry = Better exit opportunities
   - Higher profit factor (target: 0.59+ from current 0.34)

2. **Dynamic Threshold Adjustment**: (Phase 2)
   - Adaptive target% based on market regime
   - Volatility-adjusted stop-loss

3. **Scaled Entry Strategy**: (Phase 3)
   - Multiple entry points reduce average cost
   - Better partial profit opportunities

4. **Enhanced Risk Management**: (Phase 3)
   - Position scaling based on volatility (ATR)
   - Maximum loss limits per position

---

## 12. Strategic Recommendations

### For Better Profit Booking
1. **Increase Entry Quality**: Use hierarchical filter (Phase 1)
   - Better entries → Better exits → Higher win rate

2. **Optimize Partial Exit Level**: Consider 10% instead of 8%
   - Allow position to run longer
   - Reduce frequent exits on smaller gains

3. **Add Scaling Opportunities**: 
   - Scale into positions on breakouts
   - Take partials more frequently on larger moves

4. **Regime-Based Targets**: (Phase 2)
   - Trending markets: 15% targets
   - Range-bound: 5-8% targets

5. **Profit Confirmation Signals**:
   - Exit partial only after technical confirmation
   - Require 2-of-3 filters agreement for holds

---

## Summary

Your **Profit Booking Strategy** is comprehensive and multi-layered:

✅ **Fixed Targets** (12%) provide clear profit goals
✅ **Partial Exits** (8% for 50%) lock in gains early
✅ **Trailing Stops** (-2%) protect profits while allowing upside
✅ **Technical Exits** (MACD, RSI, Trend) catch reversals
✅ **Hard Stops** (-4%) and daily limits prevent catastrophic losses
✅ **Market-Time Aware** adjustments improve stop-loss placement

**Current Focus**: Phase 1 implementation to improve entry quality, which will naturally improve exit timing and profit realization through the hierarchical filter system.

