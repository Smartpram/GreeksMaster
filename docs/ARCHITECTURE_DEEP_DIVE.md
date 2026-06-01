# Architecture Deep Dive: The 5-Stage Decision Pipeline

**Purpose**: This document provides architectural details for developers who need to understand or extend the pipeline stages.

**Audience**: Developers, system architects, contributors

**Last Updated**: June 1, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Stage 1: Signal Generation](#stage-1-signal-generation)
3. [Stage 2: Validation & Guardrails](#stage-2-validation--guardrails)
4. [Stage 3: Trade Execution](#stage-3-trade-execution)
5. [Stage 4: Exit & Position Management](#stage-4-exit--position-management)
6. [Stage 5: Risk Monitoring & Feedback](#stage-5-risk-monitoring--feedback)
7. [Inter-Stage Communication](#inter-stage-communication)
8. [Error Handling & Resilience](#error-handling--resilience)
9. [Testing Strategy](#testing-strategy)

---

## Overview

MyBreezeApp's trading logic follows a **5-stage decision pipeline**:

```
[Stage 1] SIGNAL GENERATION
   Signal detected by screener
           ↓
[Stage 2] VALIDATION & GUARDRAILS
   Config & regime checks
           ↓
[Stage 3] TRADE EXECUTION
   Order placed via Breeze API
           ↓
[Stage 4] EXIT & POSITION MANAGEMENT
   Monitor price, decide exit timing
           ↓
[Stage 5] RISK MONITORING & FEEDBACK
   Track portfolio health, influence next decision
```

Each stage is **independently testable** and **loosely coupled** through well-defined interfaces.

---

## Stage 1: Signal Generation

### Module Location
- Primary: `app/strategies/buy_hold_trend.py`
- Data: `app/api/breeze_client.py` (provides price data)

### Responsibility
**Generate trade entry signals** based on technical indicators and market conditions.

### Signal Generation Algorithm

```python
class BuyHoldTrendStrategy:
    def scan_market(self, price_data) -> Optional[BuySignal]:
        """
        Scan OHLCV data for entry setup.
        
        Args:
            price_data: DataFrame with columns [open, high, low, close, volume, datetime]
        
        Returns:
            BuySignal object if setup detected, None otherwise
        """
        # 1. Calculate technical indicators
        ma_20 = price_data['close'].rolling(20).mean()
        rsi = self.calculate_rsi(price_data['close'], period=14)
        
        # 2. Check entry conditions
        is_uptrend = price_data['close'][-1] > ma_20[-1]
        is_rsi_valid = 40 <= rsi[-1] <= 80
        
        # 3. Generate signal if conditions met
        if is_uptrend and is_rsi_valid:
            return BuySignal(
                symbol=price_data['symbol'],
                entry_price=price_data['close'][-1],
                timestamp=price_data['datetime'][-1],
                indicators={'rsi': rsi[-1], 'ma_20': ma_20[-1]}
            )
        
        return None
```

### Configuration Impact
- **Entry Conditions**: `MA_PERIOD`, `RSI_PERIOD`, `RSI_MIN`, `RSI_MAX` (from `.env`)
- **Symbols to Scan**: `DEFAULT_SYMBOLS` (from `.env`)
- **Data Source**: Breeze API (real-time price feed)

### Output Contract
```python
@dataclass
class BuySignal:
    symbol: str              # e.g., 'TCS'
    entry_price: float       # e.g., 3100.50
    timestamp: datetime      # Time signal was generated
    indicators: dict         # e.g., {'rsi': 65, 'ma_20': 3050}
    confidence: float = 1.0  # Optional: signal strength (0-1)
```

### Key Design Decisions

1. **Non-blocking Scan**: Signal generation doesn't block if Breeze API is slow
2. **Per-Symbol Processing**: Each symbol scanned independently, failures isolated
3. **Indicator Caching**: Recent indicators cached to reduce API calls
4. **Signal De-duplication**: Multiple signals for same symbol within same bar ignored

### Testing Approach
- Unit tests: Mock price data, verify indicator calculations
- Integration tests: Real Breeze API data, verify signal trigger timing
- Edge cases: Gap openings, limit-up/down, circuit breakers

---

## Stage 2: Validation & Guardrails

### Module Locations
- Validator: `app/strategies/production_validator.py`
- Regime Monitor: `app/strategies/regime_monitor.py`
- Unified Manager: `app/strategies/unified_profit_booking.py`

### Responsibility
**Ensure signal is safe to trade** by checking:
1. Configuration validity
2. Market regime classification
3. Exit strategy appropriateness

### Validation Layers

#### Layer 1: Production Validator

```python
def validate_production_config(config: dict) -> List[str]:
    """
    Check that configuration is safe for trading.
    
    Args:
        config: Dictionary with keys like MAX_POSITION_SIZE, TARGET_PROFIT_PCT, etc.
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Check position sizing
    if not (0.01 <= config['MAX_POSITION_SIZE'] <= 0.20):
        errors.append("MAX_POSITION_SIZE must be 1-20% of capital")
    
    # Check risk ratios
    if config['TARGET_PROFIT_PCT'] <= config['STOP_LOSS_PCT']:
        errors.append("TARGET must be > STOP_LOSS")
    
    # Check daily limits
    if config['MAX_DAILY_LOSS_PCT'] < 0.01 or config['MAX_DAILY_LOSS_PCT'] > 0.05:
        errors.append("MAX_DAILY_LOSS_PCT should be 1-5%")
    
    # Check environment
    try:
        breeze_client = BreezeClient(config['BREEZE_API_KEY'])
        breeze_client.ping()  # Quick connectivity test
    except Exception as e:
        errors.append(f"Breeze API unreachable: {e}")
    
    return errors
```

**Blocking Conditions**:
- Configuration values outside acceptable ranges
- Breeze API unreachable
- Database offline
- Critical environment variables missing

**Decision**: If `errors` list is not empty, signal is **rejected** and logged.

#### Layer 2: Regime Detection & Classification

```python
class RegimeMonitor:
    def detect_market_regime(self, recent_trades: List[Trade]) -> MarketRegime:
        """
        Classify current market as mean-reverting, trending, or unknown.
        
        Args:
            recent_trades: Last 20 trades with holding duration data
        
        Returns:
            MarketRegime object with classification and confidence
        """
        # Calculate average holding duration
        holding_durations = [trade.holding_duration_days for trade in recent_trades]
        avg_holding_days = np.mean(holding_durations)
        
        # Classify based on holding duration
        if avg_holding_days < 1.0:
            regime = 'MEAN_REVERTING'
            reason = "Intraday closes indicate bounces, not sustained trends"
        elif avg_holding_days > 2.0:
            regime = 'TRENDING'
            reason = "Multi-day holds suggest sustained directional moves"
        else:
            regime = 'UNKNOWN'
            reason = "Mixed holding durations, unclear trend"
        
        return MarketRegime(
            classification=regime,
            avg_holding_days=avg_holding_days,
            confidence=self.calculate_confidence(recent_trades),
            reason=reason,
            recommended_exit_strategy=self.exit_strategy_for_regime(regime)
        )
```

**Key Metrics**:
- `avg_holding_days`: Mean holding period of last 20 trades
- `volatility`: Standard deviation of returns
- `win_rate`: Percentage of winning trades
- `drawdown`: Current portfolio drawdown

**Classification Rules**:

| avg_holding_days | Classification | Exit Strategy | Confidence Threshold |
|------------------|-----------------|---------------|--------------------|
| < 1.0 days | MEAN_REVERTING | FIXED_FULL_EXIT | > 0.8 |
| > 2.0 days | TRENDING | PARTIAL_WITH_TRAILING | > 0.8 |
| 1.0 - 2.0 days | UNKNOWN | FIXED_FULL_EXIT (conservative) | Any |

#### Layer 3: Exit Strategy Selection

```python
class UnifiedProfitBookingManager:
    def select_exit_strategy(self, regime: MarketRegime) -> ExitStrategy:
        """
        Choose exit mechanism based on regime.
        
        Args:
            regime: MarketRegime object from regime_monitor
        
        Returns:
            ExitStrategy.FIXED_FULL_EXIT or ExitStrategy.PARTIAL_WITH_TRAILING
        """
        if regime.classification == 'MEAN_REVERTING':
            # Backtests show trailing reduces profit factor 2x in intraday markets
            return ExitStrategy.FIXED_FULL_EXIT
        
        elif regime.classification == 'TRENDING':
            # Backtests show trailing extends profitable in multi-day moves
            return ExitStrategy.PARTIAL_WITH_TRAILING
        
        else:
            # Unknown regime defaults to safe mode
            return ExitStrategy.FIXED_FULL_EXIT
```

### Output Contract
```python
@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]                    # Validation errors (if any)
    regime: MarketRegime                 # Market classification
    exit_strategy: ExitStrategy          # Selected exit mechanism
    signal_id: str                       # Unique signal identifier
```

### Decision Tree
```
Signal Received
    ↓
[CHECK] Is config valid?
    No → REJECT signal, log error
    Yes ↓
[CHECK] Is Breeze API reachable?
    No → REJECT signal, log error
    Yes ↓
[DETECT] Market regime
    Get recent 20 trades
    Calculate avg_holding_days
    Classify as MEAN_REVERTING / TRENDING / UNKNOWN
    ↓
[SELECT] Exit strategy
    MEAN_REVERTING → FIXED_FULL_EXIT
    TRENDING → PARTIAL_WITH_TRAILING
    UNKNOWN → FIXED_FULL_EXIT (safe)
    ↓
[APPROVE] Signal + propagate to Stage 3
```

### Testing Approach
- Unit tests: Mock configs, verify validation logic
- Unit tests: Historical trade data, verify regime classification
- Integration tests: Real data, verify strategy selection
- Edge cases: Empty trade history, outlier trades, regime shifts

---

## Stage 3: Trade Execution

### Module Locations
- Trading Service: `app/services/trading_service.py`
- Risk Service: `app/services/risk_service.py`
- Breeze Client: `app/api/breeze_client.py`

### Responsibility
**Place order via Breeze API** while enforcing entry-level risk controls.

### Execution Flow

```python
class TradingService:
    def execute_buy_signal(self, signal: BuySignal, config: dict) -> Order:
        """
        Execute a buy signal with risk enforcement.
        
        Args:
            signal: BuySignal from Stage 1
            config: Configuration with capital, position sizing, etc.
        
        Returns:
            Order object with confirmation from Breeze API
        
        Raises:
            RiskLimitExceeded: If entry risk checks fail
        """
        # STEP 1: Calculate position size
        position_size_rupees = config['DEFAULT_CAPITAL'] * config['MAX_POSITION_SIZE']
        quantity = int(position_size_rupees / signal.entry_price)
        
        # STEP 2: Perform entry risk checks (via risk_service)
        daily_pnl = self.risk_service.get_daily_pnl()
        if daily_pnl < -config['DEFAULT_CAPITAL'] * config['MAX_DAILY_LOSS_PCT']:
            raise RiskLimitExceeded("Daily loss limit exceeded")
        
        portfolio_drawdown = self.risk_service.get_portfolio_drawdown()
        if portfolio_drawdown < -config['MAX_DRAWDOWN_LIMIT_PCT']:
            raise RiskLimitExceeded("Max drawdown limit exceeded")
        
        # STEP 3: Place order via Breeze API
        stop_loss_price = signal.entry_price * (1 - config['STOP_LOSS_PCT'])
        profit_target_price = signal.entry_price * (1 + config['TARGET_PROFIT_PCT'])
        
        try:
            order = self.breeze_client.place_order(
                symbol=signal.symbol,
                action='BUY',
                quantity=quantity,
                price=signal.entry_price,
                order_type='MARKET'
            )
            
            # STEP 4: Place stop-loss order immediately
            self.breeze_client.place_order(
                symbol=signal.symbol,
                action='SELL',
                quantity=quantity,
                price=stop_loss_price,
                order_type='STOP_LOSS'
            )
            
            # STEP 5: Queue profit target
            self.profit_booking_manager.queue_target(
                symbol=signal.symbol,
                quantity=quantity,
                target_price=profit_target_price
            )
            
            return order
        
        except BreezeAPIError as e:
            log.error(f"Order failed for {signal.symbol}: {e}")
            raise
```

### Risk Checks
1. **Daily P&L**: Cumulative loss for day within `MAX_DAILY_LOSS_PCT`
2. **Portfolio Drawdown**: Peak-to-current drawdown within `MAX_DRAWDOWN_LIMIT_PCT`
3. **Position Limits**: Total open positions within risk tolerance
4. **Quantity Rounding**: Ensure quantity is valid for exchange

### Order Types

| Order Type | Usage | Execution |
|-----------|-------|-----------|
| **MARKET** | Entry order | Fills immediately at best ask |
| **STOP_LOSS** | Protection | Triggers at stop price, becomes market order |
| **LIMIT** | Optional for targets | Waits for specific price |

### Error Handling
```python
# Retry logic for transient failures
@retry(max_attempts=3, backoff_seconds=1)
def place_order_with_retry(self, order_spec):
    return self.breeze_client.place_order(**order_spec)

# Partial fills
if order.filled_quantity < order.requested_quantity:
    log.warning(f"Partial fill: {order.filled_quantity} of {order.requested_quantity}")
    # Adjust risk calculations based on actual quantity

# Order rejection
if order.status == 'REJECTED':
    log.error(f"Order rejected: {order.rejection_reason}")
    # Alert trader, update signal log
```

### Testing Approach
- Unit tests: Mock Breeze API, verify position sizing math
- Unit tests: Risk checks with mock portfolio states
- Integration tests: Paper trading with real Breeze credentials
- Chaos tests: Simulate API timeouts, partial fills, rejections

---

## Stage 4: Exit & Position Management

### Module Locations
- Profit Booking Manager: `app/strategies/profit_booking_manager.py`
- Unified Profit Booking: `app/strategies/unified_profit_booking.py`

### Responsibility
**Monitor open positions and decide WHEN and HOW to exit** based on:
1. Exit strategy (fixed full vs. partial trailing)
2. Market regime
3. Current price vs. target/stop-loss

### Exit Strategy: Fixed Full Exit

```python
class FixedFullExitManager:
    def check_exit_conditions(self, position: Position) -> Optional[ExitDecision]:
        """
        Check if position should exit (100% at once).
        
        Args:
            position: Open position object
        
        Returns:
            ExitDecision if exit condition met, None otherwise
        """
        current_price = self.get_current_price(position.symbol)
        
        # Check profit target
        if current_price >= position.profit_target_price:
            return ExitDecision(
                should_exit=True,
                reason='PROFIT_TARGET_HIT',
                exit_price=position.profit_target_price,
                quantity=position.quantity,  # 100% exit
                pnl=(current_price - position.entry_price) * position.quantity
            )
        
        # Check stop loss
        if current_price <= position.stop_loss_price:
            return ExitDecision(
                should_exit=True,
                reason='STOP_LOSS_HIT',
                exit_price=position.stop_loss_price,
                quantity=position.quantity,  # 100% exit
                pnl=(current_price - position.entry_price) * position.quantity
            )
        
        return None  # Hold position
```

### Exit Strategy: Partial + Trailing

```python
class PartialTrailingExitManager:
    def check_exit_conditions(self, position: Position) -> Optional[ExitDecision]:
        """
        Check if position should exit (50% at target, 50% with trailing stop).
        
        Args:
            position: Open position object
        
        Returns:
            ExitDecision if exit condition met, None otherwise
        """
        current_price = self.get_current_price(position.symbol)
        
        # Update trailing stop price
        position.trailing_stop_price = max(
            position.trailing_stop_price,  # Never lower the trailing stop
            current_price * (1 - 0.02)     # 2% trailing stop
        )
        
        # Check partial exit at target (50%)
        if current_price >= position.profit_target_price and not position.partial_exited:
            position.partial_exited = True
            return ExitDecision(
                should_exit=True,
                reason='PARTIAL_TARGET_HIT',
                exit_price=position.profit_target_price,
                quantity=position.quantity // 2,  # 50% exit
                remaining_quantity=position.quantity - position.quantity // 2,
                pnl=(current_price - position.entry_price) * (position.quantity // 2)
            )
        
        # Check trailing stop (on remaining 50%)
        if current_price <= position.trailing_stop_price and position.partial_exited:
            return ExitDecision(
                should_exit=True,
                reason='TRAILING_STOP_HIT',
                exit_price=position.trailing_stop_price,
                quantity=position.remaining_quantity,  # Exit remaining
                pnl=(current_price - position.entry_price) * position.remaining_quantity
            )
        
        # Check stop loss (full exit at any time)
        if current_price <= position.stop_loss_price:
            return ExitDecision(
                should_exit=True,
                reason='HARD_STOP_LOSS',
                exit_price=position.stop_loss_price,
                quantity=position.quantity,  # Full exit (both portions)
                pnl=(current_price - position.entry_price) * position.quantity
            )
        
        return None  # Hold position
```

### Position Lifecycle

```
POSITION OPEN (Entry filled)
    ↓
[Loop] Check exit conditions every tick
    
    For FIXED_FULL_EXIT:
    ├─ Target hit? → Exit 100% at target
    ├─ Stop hit?   → Exit 100% at stop
    └─ Hold → Continue loop
    
    For PARTIAL_WITH_TRAILING:
    ├─ Target hit? → Exit 50% at target, enter trailing phase
    ├─ Trailing stop hit (on remaining 50%)? → Exit remaining 50%
    ├─ Stop loss hit? → Emergency exit 100%
    └─ Hold → Continue loop, update trailing price
    
    ↓
POSITION CLOSED (Full exit executed)
    ├─ Record exit price, P&L
    ├─ Calculate holding duration
    ├─ Log to trade history
    └─ Feedback to Stage 5 (regime monitoring)
```

### Key Data Structures

```python
@dataclass
class Position:
    symbol: str
    entry_price: float
    quantity: int
    timestamp: datetime
    stop_loss_price: float
    profit_target_price: float
    
    # For PARTIAL_WITH_TRAILING
    partial_exited: bool = False
    trailing_stop_price: Optional[float] = None
    remaining_quantity: int = 0
    
    @property
    def current_pnl(self) -> float:
        current_price = self.get_current_price()
        return (current_price - self.entry_price) * self.quantity
    
    @property
    def holding_duration(self) -> timedelta:
        return datetime.now() - self.timestamp
```

### Testing Approach
- Unit tests: Mock prices, verify exit logic for both strategies
- Unit tests: Trailing stop price updates, verify never goes down
- Integration tests: Simulate real price movements, verify exits trigger
- Edge cases: Gap moves, limit moves, instant profit/loss, overnight holds

---

## Stage 5: Risk Monitoring & Feedback

### Module Locations
- Regime Monitor: `app/strategies/regime_monitor.py` (continuous)
- Risk Service: `app/services/risk_service.py` (continuous)
- Notification Client: `app/api/notification_client.py`

### Responsibility
**Continuously monitor portfolio health** and **feed information back into signal validation**:
1. Track daily P&L and drawdown
2. Re-evaluate market regime (every 4 hours)
3. Send alerts and notifications
4. Influence next signal's acceptance

### Continuous Monitoring

```python
class RiskMonitor:
    def background_monitor(self):
        """
        Run continuously in background (every 1 minute).
        """
        while True:
            try:
                # MONITOR 1: Daily P&L
                daily_pnl = self.calculate_daily_pnl()
                max_daily_loss = self.config['MAX_DAILY_LOSS_PCT'] * self.config['DEFAULT_CAPITAL']
                
                if daily_pnl < max_daily_loss:
                    self.notify(f"⚠️ Daily loss limit approaching: {daily_pnl}")
                    # Could halt new signals here
                
                # MONITOR 2: Portfolio Drawdown
                portfolio_drawdown = self.calculate_portfolio_drawdown()
                max_drawdown = self.config['MAX_DRAWDOWN_LIMIT_PCT']
                
                if portfolio_drawdown < max_drawdown:
                    self.notify(f"⚠️ Portfolio drawdown: {portfolio_drawdown}")
                    # Could reduce position sizes here
                
                # MONITOR 3: Open Positions
                open_positions = self.get_open_positions()
                log.info(f"Open positions: {len(open_positions)}")
                
                # MONITOR 4: Regime Re-check (every 4 hours)
                if self.should_recheck_regime():
                    recent_trades = self.get_recent_trades(20)
                    new_regime = self.detect_market_regime(recent_trades)
                    
                    if new_regime != self.current_regime:
                        self.notify(f"📊 Market regime changed: {self.current_regime} → {new_regime}")
                        self.current_regime = new_regime
                
                time.sleep(60)  # Check every minute
            
            except Exception as e:
                log.error(f"Error in background monitor: {e}")
                time.sleep(60)  # Retry after error
```

### Feedback Loop to Signal Validation

```python
class SignalValidator:
    def accept_signal(self, signal: BuySignal) -> bool:
        """
        Decide whether to accept a signal based on current conditions.
        """
        # Normal acceptance
        daily_pnl = self.risk_monitor.get_daily_pnl()
        portfolio_drawdown = self.risk_monitor.get_portfolio_drawdown()
        open_positions = self.risk_monitor.get_open_positions()
        
        # Soft rejection: Already underwater, be more conservative
        if daily_pnl < -self.config['DEFAULT_CAPITAL'] * 0.015:  # 1.5% loss
            log.warning("System underwater. Requiring higher signal confidence.")
            return signal.confidence > 0.9  # Only high-confidence signals
        
        # Hard rejection: Stopped for the day
        if daily_pnl < -self.config['DEFAULT_CAPITAL'] * 0.02:  # 2% loss
            log.error("Daily loss limit reached. No new signals accepted.")
            self.notify("🛑 Daily loss limit hit. Trading halted for today.")
            return False
        
        # Hard rejection: Max positions reached
        if len(open_positions) >= self.config['MAX_OPEN_POSITIONS']:
            return False
        
        # Otherwise accept
        return True
```

### Metrics Tracked

| Metric | Calculation | Frequency | Action if Triggered |
|--------|-----------|-----------|-------------------|
| **Daily P&L** | Sum of closed trades P&L today | Every close | Alert at 1.5%, Halt at 2% |
| **Portfolio Drawdown** | (peak - current) / peak | Every minute | Alert threshold |
| **Avg Holding Duration** | Mean holding days of last 20 trades | Every 4 hours | Regime re-evaluation |
| **Win Rate** | % winning trades in last 20 | Every 4 hours | Confidence indicator |
| **Profit Factor** | Gross profit / gross loss | Every 4 hours | Strategy effectiveness |

### Alert System

```python
class NotificationClient:
    def send_alert(self, alert_type: str, message: str):
        """
        Route alerts to appropriate channels.
        """
        if alert_type == 'TRADE':
            # Trade execution alerts (all trades)
            if self.config['SEND_TELEGRAM_ALERTS']:
                self.send_telegram(message)
        
        elif alert_type == 'RISK':
            # Risk event alerts (daily loss, drawdown)
            self.send_email(f"⚠️ RISK ALERT: {message}")
            self.send_telegram(f"⚠️ {message}")
        
        elif alert_type == 'REGIME_CHANGE':
            # Regime change alerts
            self.send_email(f"📊 REGIME: {message}")
            self.send_telegram(f"📊 {message}")
        
        elif alert_type == 'ERROR':
            # Critical errors
            self.send_email(f"❌ ERROR: {message}")
            # Telegram for immediate visibility
```

### Testing Approach
- Unit tests: Mock portfolio states, verify P&L calculations
- Unit tests: Historical trade data, verify regime detection
- Integration tests: Simulate day trading, verify daily limits
- Chaos tests: Gaps, limit moves, sudden regime changes

---

## Inter-Stage Communication

### Data Flow

```
Signal (BuySignal) 
  Stage 1 → Stage 2
  ├─ symbol, entry_price, timestamp, indicators
  └─ Carries: Buy setup information

Validation Result (ValidationResult)
  Stage 2 → Stage 3
  ├─ is_valid, errors, regime, exit_strategy
  └─ Carries: Approval + regime classification

Order (Order)
  Stage 3 → Stage 4
  ├─ order_id, symbol, filled_price, quantity
  └─ Carries: Execution confirmation

Position (Position)
  Stage 4 → Stage 5 (ongoing)
  ├─ entry_price, current_price, holding_duration, pnl
  └─ Carries: Position state for monitoring

Trade (Trade)
  Stage 4 → Stage 5 (on close)
  ├─ symbol, entry_price, exit_price, holding_duration, pnl
  └─ Carries: Closed trade data for regime re-evaluation
```

### Error Propagation

```
Stage 1 (Signal Generation)
  Error: "No price data"
  Propagation: Logged, next cycle tries again
  Impact: Signal not generated (benign)

Stage 2 (Validation)
  Error: "Config invalid"
  Propagation: Signal rejected, stored
  Impact: Trade doesn't happen (safe)

Stage 3 (Execution)
  Error: "Breeze API timeout"
  Propagation: Retry with backoff
  Impact: Order delayed, may miss entry

Stage 4 (Exit)
  Error: "Position tracking lost"
  Propagation: Manual intervention required
  Impact: Position not exited automatically (critical)

Stage 5 (Monitoring)
  Error: "Risk calculation error"
  Propagation: Alert sent, conservative limits applied
  Impact: Next signal may be rejected
```

---

## Error Handling & Resilience

### Failure Modes

| Failure | Detection | Recovery | Impact |
|---------|-----------|----------|--------|
| **Signal gen fails** | No signals generated | Retry next cycle | Minor (no new trades) |
| **Breeze API down** | API returns 503 | Queue signals, retry | Medium (can't execute) |
| **Database offline** | DB connection timeout | Cache locally, sync later | Medium (order history lost) |
| **Position tracking lost** | Position not found | Alert trader, manual intervention | High (position abandoned) |
| **Configuration corrupt** | Validation fails | Load from backup | High (system stops) |

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
def place_order_with_retry(self, order_spec):
    """Retry order placement up to 3 times with exponential backoff."""
    return self.breeze_client.place_order(**order_spec)

# Results in delays: 1s, 2s, 4s (max 10s)
```

### Circuit Breaker Pattern

```python
from pybreaker import CircuitBreaker

breeze_circuit = CircuitBreaker(
    fail_max=5,        # Fail 5 times before opening
    reset_timeout=60   # Try again after 60 seconds
)

@breeze_circuit
def call_breeze_api(endpoint, **kwargs):
    return breeze_client.request(endpoint, **kwargs)

# If 5 failures occur within short time:
# - Circuit opens (blocks further calls)
# - After 60 seconds, tries one call (reset attempt)
# - If succeeds, circuit closes; if fails, reopens
```

### Graceful Degradation

```python
# If Breeze API is slow but not down
# Fall back to cached prices (slight staleness acceptable)

def get_current_price(symbol: str, max_staleness_seconds: int = 5):
    try:
        return breeze_client.get_price(symbol)  # Fresh price
    except TimeoutError:
        cached = price_cache.get(symbol)
        if cached and cached['age'] < max_staleness_seconds:
            log.warning(f"Using cached price for {symbol} (age: {cached['age']}s)")
            return cached['price']
        raise  # Staleness too high, can't proceed safely
```

---

## Testing Strategy

### Test Pyramid

```
                    /\
                   /E2E\  (End-to-end scenarios)
                  /------\
                 /Integration\  (Stage interactions)
                /-------------\
               /    Unit Tests    \  (Individual stages)
              /---------------------\

1. **Unit Tests** (70% of tests)
   - Each stage tested in isolation
   - Mocked dependencies
   - Fast execution (~100ms total)

2. **Integration Tests** (20% of tests)
   - Stage interactions tested
   - Real database, mocked Breeze API
   - Slower execution (~1s per test)

3. **E2E Tests** (10% of tests)
   - Full pipeline tested
   - Real Breeze API (paper trading)
   - Slow execution (~30s per test)
```

### Test Organization

```
tests/
├── test_stage1_signal_generation.py
│   ├── test_ma_crossover_detection
│   ├── test_rsi_validation
│   └── test_no_duplicate_signals
│
├── test_stage2_validation.py
│   ├── test_production_validator_config_checks
│   ├── test_regime_detection_mean_reverting
│   ├── test_regime_detection_trending
│   └── test_exit_strategy_selection
│
├── test_stage3_execution.py
│   ├── test_position_sizing_calculation
│   ├── test_daily_loss_limit_enforcement
│   ├── test_order_placement_via_breeze
│   └── test_stop_loss_placement
│
├── test_stage4_exit.py
│   ├── test_fixed_exit_full_exit_at_target
│   ├── test_fixed_exit_stop_loss_hit
│   ├── test_trailing_stop_update
│   ├── test_partial_exit_at_target
│   └── test_trailing_stop_hit_on_remainder
│
├── test_stage5_monitoring.py
│   ├── test_daily_pnl_calculation
│   ├── test_portfolio_drawdown_tracking
│   ├── test_regime_recheck_triggers
│   └── test_alerts_sent
│
└── test_e2e_full_pipeline.py
    ├── test_signal_to_close_mean_reverting
    ├── test_signal_to_close_trending
    └── test_daily_loss_halt
```

### Example Test

```python
def test_regime_detection_mean_reverting():
    """
    Verify that intraday trades are classified as mean-reverting.
    """
    # Setup: Create 20 trades with short holding duration
    trades = [
        Trade(
            symbol='TCS',
            entry_price=3100,
            exit_price=3103,
            holding_duration=timedelta(hours=2)  # Intraday
        )
        for _ in range(20)
    ]
    
    # Execute
    monitor = RegimeMonitor()
    regime = monitor.detect_market_regime(trades)
    
    # Assert
    assert regime.classification == 'MEAN_REVERTING'
    assert regime.avg_holding_days < 1.0
    assert regime.recommended_exit_strategy == ExitStrategy.FIXED_FULL_EXIT
    assert regime.confidence > 0.8
```

---

## Summary: How It All Works Together

1. **Stage 1** (Signal Generation): Screener finds a setup → BuySignal created
2. **Stage 2** (Validation): Checks if safe, detects regime, selects exit strategy
3. **Stage 3** (Execution): Places order via Breeze, enforces position sizing and daily limits
4. **Stage 4** (Exit): Monitors position, exits at target/stop based on strategy
5. **Stage 5** (Monitoring): Tracks P&L, detects regime shifts, sends alerts
6. **Feedback Loop**: Trade results feed back into Stage 2 for next signal

The entire flow is **automated**, **testable**, **resilient**, and **coherent**.

---

**Questions?** Refer to the main README.md for user-facing documentation, or the individual module files for implementation details.
