# Price Monitoring & Real-Time Position Tracking Guide

## Executive Summary

**YES - We WILL monitor prices throughout the day!** ✅

Our system includes:
- ✅ **Real-time data streaming** from Breeze API (live market prices)
- ✅ **Live position tracker** with continuous P&L updates
- ✅ **Price monitoring dashboard** with visual alerts
- ✅ **Automatic signal execution** based on price levels
- ✅ **Risk manager** checking triggers continuously
- ✅ **Notification system** for price alerts (Email/Telegram)

**Update Frequency**: Every 1 second during market hours

---

## Architecture Overview

### Data Flow for Price Monitoring

```
Market (NSE/BSE)
    ↓
Breeze API WebSocket
    ↓
DataStreamService (Real-time collection)
    ↓
LivePositionTracker (P&L calculation)
    ↓
RiskManager (Limit checking)
    ↓
SignalExecutor (Auto-execution)
    ↓
OrderManager (Order placement)
    ↓
NotificationService (Alerts to user)
    ↓
Web Dashboard (Visual updates)
```

---

## Core Monitoring Components

### 1. DataStreamService (Real-Time Data Collection)

**File**: `app/services/data_stream.py`

**What it does:**
- Connects to Breeze API for live market data
- Polls quotes every 1 second (during market hours)
- Processes data for all subscribed instruments
- Maintains latest price cache

**Key Methods:**

```python
# Start monitoring for specific stocks
data_stream.start_stream(instruments=['RELIANCE', 'TCS', 'INFY'])

# Get latest price for a stock
latest_price = data_stream.get_latest_data('RELIANCE')
# Returns: {
#    'symbol': 'RELIANCE',
#    'close': 2485.50,
#    'bid': 2485.40,
#    'ask': 2485.60,
#    'volume': 1234567,
#    'timestamp': datetime
# }

# Check stream status
status = data_stream.get_stream_status()
# Returns: {
#    'is_streaming': True,
#    'subscribed_instruments': 5,
#    'instruments': ['RELIANCE', 'TCS', ...],
#    'latest_update': datetime
# }

# Stop monitoring
data_stream.stop_stream()
```

**Data Points Captured**:
- **LTP** (Last Traded Price) - Most important
- **Bid/Ask** - Market depth
- **High/Low** - Daily range
- **Volume** - Trading activity
- **Change %** - Daily movement
- **Timestamp** - When data was received

---

### 2. LivePositionTracker (Real-Time P&L Updates)

**File**: `app/services/live_position_tracker.py`

**What it does:**
- Tracks all open positions
- Updates P&L every time price updates
- Calculates unrealized gains/losses
- Triggers buy/sell signals based on price levels
- Maintains position history

**Key Calculations:**

```python
# Real-time P&L calculation (updated every second)
unrealized_pnl = (current_price - entry_price) × quantity
unrealized_pnl_percent = unrealized_pnl / (entry_price × quantity)

# Example:
# Bought RELIANCE: 5 shares @ ₹2,500 = ₹12,500
# Current price: ₹2,550
# Unrealized P&L = (2550 - 2500) × 5 = ₹250 (+2%)
```

**Position Tracking**:

```python
# Update position when price changes
tracker.update_position_price(
    position_id='pos_123',
    current_price=2550.50,
    timestamp=datetime.now()
)

# Get all open positions
positions = tracker.get_all_open_positions()
# Returns list of LivePosition objects with:
# - entry_price, current_price
# - unrealized_pnl, unrealized_pnl_percent
# - entry_time, days_open
# - highest_price, lowest_price (for trailing stops)

# Get specific position details
position = tracker.get_position(position_id='pos_123')
print(f"Position P&L: {position.unrealized_pnl}")
print(f"Days Open: {position.days_open}")
print(f"Return %: {position.unrealized_pnl_percent * 100:.2f}%")
```

**Signal Triggers**:

```python
# Automatic triggers based on price levels
tracker.check_triggers(position, current_price)

# Triggers checked:
# 1. Stop Loss: Price hits -2% (default)
# 2. Take Profit: Price reaches +3% (default)
# 3. Trailing Stop: Locks in gains, stops further losses
# 4. Technical Signals: RSI, MA crossovers
```

---

### 3. RiskManager (Real-Time Limit Checking)

**File**: `app/services/risk_manager.py`

**What it does:**
- Monitors portfolio drawdown
- Checks daily loss limits
- Validates position sizes continuously
- Calculates margin usage
- Triggers alerts when limits are approached

**Key Monitoring Functions**:

```python
# Calculate unrealized P&L for specific stock
pnl = risk_mgr.calculate_unrealized_pnl(
    stock_code='RELIANCE',
    current_price=2550
)

# Get portfolio-wide risk metrics
metrics = risk_mgr.get_portfolio_metrics()
# Returns: {
#    'total_capital': 300000,
#    'deployed_capital': 150000,
#    'available_capital': 150000,
#    'total_positions': 4,
#    'unrealized_pnl': 2500,
#    'daily_pnl': 1250,
#    'portfolio_return_percent': 0.83,
#    'margin_used': 0.15,
#    'margin_available': 85000
# }

# Check if any limits exceeded
warnings = risk_mgr.check_risk_limits()
# Returns: {
#    'daily_loss_limit': False,
#    'max_positions': False,
#    'max_position_size': False,
#    'margin_utilization': 0.15,
#    'warnings': []
# }
```

**Real-Time Thresholds**:

```
Daily Loss Limits (continuous checking):
- ₹1,500 loss (0.5%):  WARNING - reduce position size
- ₹3,000 loss (1%):    CAUTION - close positions and analyze
- ₹4,500 loss (1.5%):  STOP - halt all trading

Position Size Limits (per stock):
- Max ₹30,000 (10% of capital) per stock
- Alerts if approaching limit

Margin Limits:
- Max 25% intraday margin usage
- Alerts if approaching 20%
```

---

### 4. Web Dashboard (Visual Monitoring)

**Real-time updates in browser:**

#### Dashboard Displays:

**Portfolio Summary**:
- Total Capital: ₹3,00,000
- Deployed: ₹2,40,000
- Cash Available: ₹60,000
- Portfolio P&L: ₹2,500 (+0.83%)
- Daily P&L: ₹1,250 (+0.42%)

**Open Positions Table** (Updates every 1 second):
```
Symbol    Qty   Entry      Current    Value      P&L      Return%   Action
RELIANCE   5    ₹2,500    ₹2,550    ₹12,750    ₹250     +2.0%    Target Profit Alert
TCS        3    ₹3,200    ₹3,180    ₹9,540     -₹60     -0.6%    -
INFY       4    ₹1,800    ₹1,850    ₹7,400     ₹200     +2.7%    -
BANK       2    ₹1,500    ₹1,485    ₹2,970     -₹30     -1.0%    Stop Loss Near
```

**Real-time Charts**:
- Portfolio value over time
- Daily P&L progress
- Individual position performance
- Risk metrics gauge
- Unrealized P&L breakdown

**Live News Feed**:
- Recent trades executed
- Positions opened/closed
- Alerts triggered
- Risk warnings

---

## Monitoring Workflow During Trading Day

### 9:15 AM - Market Open

```
1. System starts data stream
2. Subscribes to your positions
3. Begins 1-second price updates
4. Dashboard shows live prices
5. Position tracker updates P&L
```

### Throughout Day (Every 1 Second)

```
1. Price received from Breeze API
2. All positions updated with new price
3. P&L recalculated
4. Triggers checked:
   - Stop loss price?
   - Take profit price?
   - Daily loss limit?
   - Position concentration?
5. Dashboard refreshed in browser
6. Notifications sent if alerts triggered
```

### Example Scenario (Real-time):

```
9:15:30 AM - Market opens
  RELIANCE opens at ₹2,500
  Your position: 5 shares @ ₹2,500
  P&L: ₹0 (+0%)

9:16:15 AM - Price moves to ₹2,505
  Dashboard shows: "RELIANCE +0.2%"
  Your position P&L: +₹25 (+0.2%)
  Still tracking...

9:30:45 AM - Price rises to ₹2,530
  Dashboard shows: "RELIANCE +1.2%"
  Your position P&L: +₹150 (+1.2%)
  Still tracking...

10:45:00 AM - Price reaches ₹2,550 (Your target)
  🎯 Alert: "RELIANCE reached target price ₹2,550"
  Dashboard highlights position
  Notification sent: Email + Telegram
  Option 1: Exit manually via dashboard
  Option 2: Auto-exit (if configured)

System continues monitoring...
```

---

## Price Alert System

### Types of Alerts

**1. Price Level Alerts**
```
Triggered when:
- Stock reaches take profit price
- Stock reaches stop loss price
- Stock reaches custom alert price

Example:
RELIANCE at ₹2,550 (your target)
→ Alert: "RELIANCE reached target!"
→ Dashboard highlights in green
→ Email sent: "RELIANCE +3% - Consider exit"
→ Telegram notification sent
```

**2. Daily Limit Alerts**
```
Triggered when:
- Daily loss reaches 0.5%
- Daily loss reaches 1.0% (CRITICAL)
- Daily P&L turns positive after losses

Example:
Daily loss at -₹1,500 (0.5%)
→ Alert: "Daily loss limit warning"
→ Dashboard shows red warning
→ Email: "Daily loss at 0.5% - Review positions"
```

**3. Risk Alerts**
```
Triggered when:
- Position concentration approaching 10% limit
- Margin usage approaching 25% limit
- Multiple positions in drawdown

Example:
INFY position approaching ₹10,000 (10% limit)
→ Alert: "INFY position near concentration limit"
→ Cannot buy more INFY
```

**4. Technical Alerts**
```
Triggered when:
- RSI enters overbought (>70)
- RSI enters oversold (<30)
- Moving average crossover
- Trend reversal detected

Example:
RELIANCE RSI >70
→ Alert: "RELIANCE overbought - Consider profit"
```

---

## Monitoring Features by Trade Lifecycle

### Phase 1: Before Entry
```
✓ Monitor entry signal formation
✓ Watch price approaching entry level
✓ Check technical indicators
✓ Verify daily limit available
```

### Phase 2: Entry Execution
```
✓ Order placed at ₹2,500
✓ Live update: Order confirmed
✓ Position created with P&L = ₹0
```

### Phase 3: Position Holding
```
✓ Price updates every 1 second
✓ P&L updates in real-time
✓ Highest price tracked (for trailing stops)
✓ Lowest price tracked (for stop loss analysis)
✓ Days held displayed
✓ Return % shown
✓ Dashboard updates live
```

### Phase 4: Exit Triggers

**Manual Exit Options**:
```
1. Click "Close Position" on dashboard
2. Enter exit price or market order
3. Confirm
4. Position closed with P&L locked in
```

**Automatic Exit Options**:
```
1. Stop Loss Hit: Auto-sells at -2%
2. Take Profit Hit: Auto-sells at +3%
3. Trailing Stop: Locks gains, stops further losses
4. Daily Loss Limit: Force closes positions
```

### Phase 5: Post-Exit
```
✓ Realized P&L calculated
✓ Position moved to history
✓ Performance metrics updated
✓ Trade logged for analysis
✓ New capital available for next trade
```

---

## Dashboard Live Updates

### Real-time Display Refresh

**Update Frequency**: Every 1 second during market hours

**What Updates**:
```
1. Current prices (LTP)
2. Position P&L amounts
3. Position P&L percentages
4. Daily P&L total
5. Chart data points
6. Alert notifications
7. Risk metrics
8. Available capital
9. Margin usage
10. Position status indicators
```

**Visual Indicators**:
```
🟢 Green: Profit (P&L > 0)
🔴 Red: Loss (P&L < 0)
🟡 Yellow: Warning (Limit approaching)
⚪ Gray: Neutral (P&L = 0 or inactive)
🔵 Blue: Information/Neutral
```

**Chart Updates**:
- Portfolio value: New point every minute
- Daily P&L: New point every 10 minutes
- Individual positions: Real-time line updates
- Risk gauge: Continuous updates

---

## Notification System

### Channels Supported

**1. Email Notifications**
```
Sent for:
✓ Position opened
✓ Take profit reached
✓ Stop loss triggered
✓ Daily limits breached
✓ Critical alerts

Example:
Subject: RELIANCE - Target Price Reached ✅
Body: Your RELIANCE position reached ₹2,550
      Unrealized Profit: +₹250 (+2%)
      Suggested Action: Consider exit
```

**2. Telegram Bot**
```
Sent for:
✓ All critical alerts
✓ Position updates
✓ Daily summary
✓ Risk warnings

Example:
"📈 RELIANCE +₹250 (+2%)
 Entry: ₹2,500
 Current: ₹2,550
 ✅ Target reached!"
```

**3. In-App Notifications**
```
Browser notifications while dashboard open
Toast messages for quick alerts
Popup modals for critical alerts
```

### Alert Configuration

```python
# Enable/disable notifications
notifications.enable_email = True
notifications.enable_telegram = True
notifications.enable_in_app = True

# Alert types
config.ALERT_ON_TARGET_REACHED = True
config.ALERT_ON_STOP_LOSS = True
config.ALERT_ON_DAILY_LIMIT = True
config.ALERT_ON_TECHNICAL = True

# Quiet hours (no alerts outside market hours)
config.QUIET_HOURS_START = "16:00"
config.QUIET_HOURS_END = "09:15"
```

---

## Performance Metrics Monitoring

### Real-Time Metrics Displayed

**Position Level**:
```
Per position tracked:
- Entry price & time
- Current price
- Entry value
- Current value
- Unrealized P&L
- Unrealized P&L %
- Days held
- Highest price reached
- Lowest price reached
```

**Portfolio Level**:
```
Overall portfolio metrics:
- Total deployed capital
- Total current value
- Total unrealized P&L
- Total unrealized P&L %
- Daily P&L (today's trades)
- Daily P&L %
- Number of open positions
- Average position size
- Portfolio beta
- Win rate (if multiple trades)
```

**Risk Level**:
```
Real-time risk metrics:
- Daily loss so far
- Daily loss limit remaining
- Margin utilization %
- Leverage used
- Concentration risk
- Max drawdown on position
- Sharpe ratio (from closed trades)
```

---

## Advanced Monitoring Features

### 1. Price Action Alerts

```python
# Custom price level alerts
tracker.set_price_alert(
    symbol='RELIANCE',
    price_level=2550,  # Alert when price reaches
    alert_type='above'  # 'above', 'below', 'crosses'
)

# Multiple alerts per position
tracker.add_alert_level(symbol='INFY', price=1850)  # Sell signal
tracker.add_alert_level(symbol='INFY', price=1700)  # Stop loss

# Relative alerts
tracker.set_relative_alert(
    symbol='TCS',
    percent_change=5,  # Alert when +5% or -5%
    direction='both'
)
```

### 2. Trending Analysis

```python
# Track if in uptrend, downtrend, or sideways
trend = tracker.analyze_position_trend(position_id)
# Returns: 'uptrend', 'downtrend', 'sideways', 'volatile'

# Get momentum
momentum = tracker.calculate_momentum(position_id)
# High momentum = strong move continuing
# Low momentum = move weakening
```

### 3. Correlation Monitoring

```python
# Monitor correlation between positions
correlation = tracker.get_position_correlation('RELIANCE', 'NIFTY50')
# High correlation = similar movement (more risk)
# Low correlation = independent movement (less risk)
```

### 4. Volume Analysis

```python
# Confirm price moves with volume
volume_quality = tracker.analyze_volume_quality(symbol='RELIANCE')
# High volume on up moves = strength
# Low volume on up moves = weakness
```

---

## Emergency Stop Systems

### What Happens If Price Crashes

**Scenario: RELIANCE crashes 3% in 1 minute**

```
Timeline:
T+0s: Price drops 1%
     → Dashboard shows red highlight
     → No action yet

T+30s: Price drops to -2% (stop loss)
     → ⚠️ Stop loss triggered!
     → Automatic sell order placed
     → Email alert sent
     → Telegram alert sent
     → Dashboard shows "CLOSED" status

T+60s: Sell order executed
     → Position closed
     → Loss locked at -₹100 (2%)
     → New capital available
```

**Emergency Circuit Breakers**:
```
1. Daily Loss Limit: Halt if -₹4,500
2. Margin Call: Close positions if margin < 25%
3. Single Position Crash: Exit if -3% on any stock
4. Portfolio Correlation: Exit if all positions down
```

---

## Monitoring Checklist During Trading Day

### Morning (9:15-10:00 AM)
- [ ] Check market open status
- [ ] Verify data stream active
- [ ] Review opening prices
- [ ] Check for any overnight news
- [ ] Confirm positions loading correctly
- [ ] Monitor first hour volatility

### Mid-Day (10:00 AM-2:30 PM)
- [ ] Monitor position P&L
- [ ] Check for entry signals
- [ ] Watch for exit triggers
- [ ] Review technical indicators
- [ ] Monitor market breadth
- [ ] Check concentration limits

### Closing Hour (2:30-3:30 PM)
- [ ] Check closing price movements
- [ ] Review daily P&L
- [ ] Monitor volume patterns
- [ ] Check RSI overbought/oversold
- [ ] Plan next day trades
- [ ] Review any pending orders

### After Market Close (3:30 PM+)
- [ ] Stop data stream
- [ ] Review daily performance
- [ ] Check position P&L locked
- [ ] Review trade executions
- [ ] Plan for next day
- [ ] Check for any errors/alerts

---

## Troubleshooting Price Monitoring

### Issue: Price Not Updating

```
Check:
1. Is data stream running? (Dashboard shows "Streaming: ON")
2. Is stock subscribed? (Position list shows it)
3. Check internet connection
4. Verify Breeze API connection status
5. Check browser console for errors

Fix:
- Refresh browser page
- Stop and restart stream
- Re-authenticate with Breeze API
- Check Breeze API status page
```

### Issue: Alert Not Received

```
Check:
1. Notification enabled in settings?
2. Email configured correctly?
3. Telegram bot token valid?
4. Price actually reached alert level?

Fix:
- Go to Settings → Notifications
- Verify email/telegram details
- Test notification with manual test button
- Check spam/junk folder for emails
```

### Issue: P&L Not Matching

```
Check:
1. Using same price source (LTP vs bid/ask)?
2. Accounting for brokerage/taxes?
3. Check entry price is correct
4. Verify quantity is accurate

Fix:
- Use LTP (Last Traded Price) only
- Include brokerage in P&L calc: P&L = ((LTP - Entry) × Qty) - Brokerage
- Verify entry price in position details
```

---

## Summary: Price Monitoring Capabilities

| Feature | Status | Update Freq |
|---------|--------|-----------|
| Real-time price feed | ✅ Active | Every 1 sec |
| Live P&L updates | ✅ Active | Every 1 sec |
| Position tracking | ✅ Active | Every 1 sec |
| Price alerts | ✅ Active | Real-time |
| Stop loss monitoring | ✅ Active | Every 1 sec |
| Take profit monitoring | ✅ Active | Every 1 sec |
| Daily limit checking | ✅ Active | Every 1 sec |
| Risk alerts | ✅ Active | Real-time |
| Dashboard updates | ✅ Active | Every 1 sec |
| Email notifications | ✅ Active | Real-time |
| Telegram alerts | ✅ Active | Real-time |
| Emergency stops | ✅ Active | Immediate |

---

## Quick Start: Enable Price Monitoring

### Step 1: Start Dashboard
```
1. Open http://localhost:5000 in browser
2. Login with your Breeze credentials
3. Click "Strategy" → "Start"
```

### Step 2: Verify Data Stream
```
Dashboard shows:
- "Streaming: ON" (green indicator)
- Live prices updating
- P&L changing in real-time
```

### Step 3: Open First Position
```
1. Click "Buy RELIANCE"
2. Enter quantity (4 shares for ₹10,000)
3. Place order
4. Watch position P&L update every second
```

### Step 4: Configure Alerts
```
1. Go to Settings → Notifications
2. Enter email address
3. Enter Telegram chat ID
4. Enable all alert types
5. Test notification
```

### Step 5: Monitor Throughout Day
```
1. Keep dashboard open
2. Watch for alerts
3. Review P&L every hour
4. Exit when targets hit
5. Stop stream at market close
```

---

## Conclusion

**Price monitoring is fully automated and continuous!** 

Your MyBreezeApp system will:
- ✅ Monitor prices every 1 second
- ✅ Update P&L in real-time
- ✅ Track all triggers automatically
- ✅ Alert you when targets/stops hit
- ✅ Never miss an opportunity
- ✅ Protect against large losses
- ✅ Give you complete visibility into positions

**You have complete control:**
- Manual exit anytime
- Modify stop loss/target anytime
- Change alert thresholds anytime
- Pause/resume monitoring anytime
- Emergency stop available anytime

**Ready to start live monitoring?** Yes! The system is production-ready. 🚀
