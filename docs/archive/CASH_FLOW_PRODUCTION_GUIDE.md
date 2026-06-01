---
title: PRODUCTION CASH FLOW MANAGEMENT GUIDE
created: 2026-05-30
version: 1.0
category: Production Critical
---

# PRODUCTION CASH FLOW MANAGEMENT GUIDE

## THE PROBLEM: Why Cash Flow Management is Critical

You're right to bring this up. This is where most retail traders blow up accounts.

### Real Scenario Example

**Initial Capital**: ₹1,00,000

**Day 1 (Monday)**:
- 9:15 AM: Buy 20 shares of RELIANCE @ ₹2,500 = ₹50,000 (DELIVERY)
  - Cash blocked: ₹50,000
  - Settlement: T+2 (Wednesday)
  - Available cash remaining: ₹50,000
  
- 9:30 AM: Buy 15 shares of TCS @ ₹3,000 = ₹45,000 (DELIVERY)
  - Cash blocked: ₹45,000
  - Settlement: T+2 (Wednesday)
  - Available cash remaining: ₹5,000
  
- 9:45 AM: Buy 10 shares of INFY @ ₹1,800 = ₹18,000 (DELIVERY)
  - **PROBLEM**: Only ₹5,000 available, need ₹18,000 + charges
  - **WITHOUT CASH FLOW MANAGER**: System might allow this (OVERDRAFT)
  - **WITH CASH FLOW MANAGER**: System rejects with "Insufficient funds"

### The T+2 Trap

**Wednesday (Day 3)**:
- Market drops 5%
- Your three positions are now worth ₹102,000 but down ₹8,000
- But cash settlements haven't happened yet - so you still have zero available cash
- Broker issues margin call because utilization is 100%
- You're forced to sell one position at loss

**Thursday (Day 4) - T+2 Settlement**:
- Your Monday sells finally settle
- Cash becomes available
- But by now you've already been liquidated

## The Solution: CashFlowManager

Our new `CashFlowManager` tracks:

1. **Available Cash**: Can be used for new trades
2. **Blocked Cash**: Tied up in pending settlements (T+0 to T+2)
3. **Pending Cash**: Will be available at settlement date
4. **Reserved Cash**: For margin/regulatory requirements

### Key Features

```
TRANSACTION TYPES TRACKED:
├── BUY DELIVERY (T+2)
│   ├── Cash blocked immediately (available → blocked)
│   ├── Settlement: T+2 business days
│   └── Validation: Sufficient available cash
│
├── SELL DELIVERY (T+2 or T+0 with TPIN)
│   ├── Share validation: Do we have shares?
│   ├── Cash received T+2 (or T+0 if TPIN)
│   └── No cash impact at execution
│
├── INTRADAY (T+0)
│   ├── Margin blocked: ~25% of position value
│   ├── Released: End of day
│   └── Must be closed: Same day
│
└── SPECIAL CASES
    ├── Dividend credit (inflow)
    ├── Margin call (outflow)
    └── Brokerage/taxes (outflow)
```

## Integration with Trading System

### BEFORE: Without Cash Flow Management

```python
def place_order(symbol, qty, price):
    order = exchange.place_order(symbol, qty, price)
    return order

# PROBLEM: No validation!
# - Can overdraft
# - Can ignore T+2 settlements
# - Can exceed daily limits
# - Can trigger margin calls unexpectedly
```

### AFTER: With Cash Flow Management

```python
def place_delivery_buy_order(symbol, qty, price):
    # STEP 1: Validate funds
    can_buy, reason, details = cash_flow.can_buy_delivery(symbol, qty, price)
    if not can_buy:
        return False, reason  # Reject if insufficient funds
    
    # STEP 2: Place order
    order = exchange.place_order(symbol, qty, price)
    
    # STEP 3: Block cash immediately
    txn_id = cash_flow.record_buy_delivery(
        order_id=order.id,
        symbol=symbol,
        quantity=qty,
        price=price
    )
    
    return True, txn_id  # Success with transaction tracked
```

## Cash Flow State Machine

```
DELIVERY BUY ORDER LIFECYCLE:
─────────────────────────────

T+0 (Execution Day - e.g., Monday)
├─ Check: available_cash >= (qty * price + fees)
├─ [YES] → Block cash
│         • available_cash ↓
│         • blocked_cash ↑
│         • Status: BLOCKED
└─ [NO] → Reject order
          Return to trader immediately

T+1 (Next Business Day - e.g., Tuesday)
├─ Cash still blocked
├─ Status: BLOCKED
└─ Shares not yet in demat account

T+2 (Settlement Day - e.g., Wednesday)
├─ Settlement processed
├─ Shares credited to demat
├─ Cash moved from blocked → spent
├─ Status: SETTLED
└─ Now you own the shares

Subsequent Days
├─ Shares available for sale
├─ Can place DELIVERY SELL order
└─ Cash from sale arrives T+2 after sale


DELIVERY SELL ORDER LIFECYCLE (Opposite):
──────────────────────────────────────────

T+0 (Execution Day)
├─ Check: position_tracker has shares
├─ [YES] → Execute sell
│         • No cash impact yet
│         • Status: PENDING
└─ [NO] → Reject (no shares)

T+2 (Settlement Day)
├─ Cash from sale received
├─ available_cash ↑
├─ Status: SETTLED
└─ Can use cash for new trades

WITH TPIN (T+0 Settlement) - Optional
├─ Requires TPIN (Tax Pin) from Income Tax
├─ Cash available T+0 (same day)
├─ Status: SETTLED immediately
└─ Check config.enable_tpin flag
```

## Daily Limits & Controls

### Setting Daily Limits

```python
# In CashFlowManager.__init__
self.max_daily_outflow = initial_capital * 0.3  # Max 30% daily

# Example:
# Initial capital: ₹1,00,000
# Max daily outflow: ₹30,000
# This prevents over-trading on volatile days
```

### Daily Limit Validation

```python
# What happens with daily outflow limit

Day 1:
├─ 10:00 AM: Buy ₹20,000 worth (outflow: ₹20,000)
├─ 10:15 AM: Buy ₹15,000 worth (outflow: ₹35,000)
│            ❌ EXCEEDS LIMIT (₹30,000)
│            Order rejected with: "Exceeds daily limit"
├─ 10:30 AM: Market recovers, try again
│            ✅ Amount check against REMAINING limit only
└─ Status: Can only buy ₹10,000 more today

Day 2:
├─ 9:15 AM: Counter resets
└─ Max outflow: ₹30,000 again (fresh day)
```

### Understanding Settlement Schedule

The most important report for production trading:

```python
settlement_schedule = cash_flow.get_settlement_schedule()

Output Example:
{
  "2026-06-03": {              # Wednesday (T+2 from Monday)
    "expected_inflow": 50000,  # RELIANCE sell proceeds
    "expected_outflow": 0,
    "transactions": [
      {
        "symbol": "RELIANCE",
        "type": "SELL_DELIVERY",
        "amount": 50000
      }
    ]
  },
  "2026-06-04": {              # Thursday (T+2 from Tuesday)
    "expected_inflow": 45000,  # TCS buy settlement
    "expected_outflow": 45000,
    ...
  }
}

This shows:
├─ When cash will become available
├─ When cash is needed
├─ Potential liquidity crunches
└─ Perfect for planning multi-leg spreads
```

## Critical Validations

### Validation 1: Sufficient Available Cash

```
Before BUY order:
├─ Required: qty * price + brokerage + taxes + charges
├─ Have: available_cash
├─ Rule: required <= available
└─ If fail: "Insufficient funds. Need ₹X, Have ₹Y"
```

### Validation 2: Daily Spending Limit

```
Before BUY order:
├─ Amount: qty * price + charges
├─ Today's total: daily_outflow + amount
├─ Limit: max_daily_outflow (30% of capital)
├─ Rule: today's_total <= limit
└─ If fail: "Exceeds daily limit. Used ₹X/₹Y, Need ₹Z more"
```

### Validation 3: Position Concentration

```
Before BUY order:
├─ Max per stock: 10% of initial capital
├─ Amount: qty * price
├─ Rule: amount <= max_position_value
└─ If fail: "Position too large. Max ₹X, Requested ₹Y"
```

### Validation 4: Margin Utilization

```
Continuously checked:
├─ Used: (blocked_cash + reserved_cash)
├─ Total: initial_capital
├─ Utilization: used / total
├─ Threshold: 75% (can configure)
├─ Rule: utilization < threshold
└─ If fail: Margin call triggered → liquidation required
```

### Validation 5: Shares for Sell

```
Before SELL order:
├─ Required shares: qty
├─ Have: position_tracker.get_shares(symbol)
├─ Rule: have >= required
└─ If fail: "Insufficient shares. Have X, Want Y"
```

## Brokerage Fee Structure

The system handles typical NSE/BSE charges:

```python
config = {
    'brokerage_rate': 0.001,           # 0.1% = ₹10 per ₹10,000
    'tax_rate': 0.0001,                # 0.01% STT (Delivery)
    'transaction_charges': 0.00001,    # Exchange charges
    'settlement_days': 2,              # T+2 standard
    'enable_tpin': False,              # Can enable T+0 sells
}

Example Delivery Buy:
├─ Gross: ₹50,000 (50 shares @ ₹1,000)
├─ Brokerage (0.1%): ₹50
├─ STT (0.01%): ₹5
├─ Charges: ₹0-2
├─ Total: ₹50,055-57
└─ Cash blocked: ₹50,055-57
```

## Production Checklist

### Before Going Live

- [ ] Configure initial_capital correctly
- [ ] Set daily limits based on risk tolerance
- [ ] Configure brokerage rates (get from broker)
- [ ] Set settlement_days = 2 (NSE/BSE standard)
- [ ] Test with paper trading first
- [ ] Verify all fund checks working
- [ ] Set up monitoring alerts
- [ ] Test margin call scenarios
- [ ] Verify settlement schedule calculation
- [ ] Configure logging to file
- [ ] Set up error notifications

### Daily Operations

- [ ] Check cash position at market open
- [ ] Review settlement schedule for incoming funds
- [ ] Monitor daily outflow limit
- [ ] Check utilization ratio (target < 60%)
- [ ] Review pending settlements
- [ ] End of day: Process EOD margin release
- [ ] T+2: Process settlement dates as they occur

### Weekly Review

- [ ] Review cash flow history
- [ ] Analyze fee/charge breakdown
- [ ] Check for optimization opportunities
- [ ] Verify no margin calls were triggered
- [ ] Review concentration limits
- [ ] Assess leverage utilization

## Common Issues & Solutions

### Issue 1: Unexpected Margin Call

**Root Cause**: Not accounting for T+2 settlements
- You have ₹10,000 available on Monday
- You buy ₹10,000 worth of 3 stocks with that
- Total blocked: ₹30,000 (with charges)
- Utilization: 30%
- But T+2 (Wednesday), all 3 settlements happen
- You're short ₹20,000

**Solution**: 
- Check settlement schedule daily
- Only buy if you have spare cash for T+2 settlements
- Use daily limits to prevent over-trading

### Issue 2: Running Out of Cash Mid-Week

**Root Cause**: Multiple T+2 settlements happening same day
- Monday: Buy ₹20,000 (settlement Wed)
- Tuesday: Buy ₹20,000 (settlement Thu)
- Wednesday: Both settle same day = ₹40,000 outflow

**Solution**:
- Plan trades to spread settlements
- Use settlement_schedule to see upcoming needs
- Keep 20% cash buffer for unexpected costs

### Issue 3: Can't Close Position Due to Cash Block

**Root Cause**: Selling to raise cash but cash won't settle
- You sell a position Monday for ₹50,000
- Settlement is T+2 (Wednesday)
- You need cash Tuesday to buy something else

**Solution**:
- Use TPIN for T+0 settlement on sells (if available)
- Plan sell orders with settlement dates in mind
- Consider intraday trading for quick cash needs

## Monitoring & Alerts

### Key Metrics to Monitor

```python
# Check daily
cash_pos = cash_flow.get_cash_position()

print(f"Available: ₹{cash_pos['available_cash']}")
print(f"Blocked: ₹{cash_pos['blocked_cash']}")
print(f"Utilization: {cash_pos['utilization_percent']}%")
print(f"Daily remaining: ₹{cash_pos['daily_remaining']}")

# Alert if:
# - available_cash < 10% of capital
# - utilization_percent > 80%
# - daily_remaining < 0
# - pending_settlements > 50
```

### Automated Alerts

```python
def check_health():
    limits = cash_flow.validate_daily_limits()
    
    if not limits['all_checks_pass']:
        for check_name, check in limits['checks'].items():
            if not check['passed']:
                send_alert(f"⚠️ {check_name}: {check['message']}")
```

## Code Examples

### Example 1: Check If You Can Buy

```python
# Before placing order
can_buy, reason, details = cash_flow.can_buy_delivery(
    symbol='RELIANCE',
    quantity=10,
    price=2500.0
)

if can_buy:
    print(f"✅ Can buy for ₹{details['total_cost']}")
    # Place order
else:
    print(f"❌ Cannot buy: {reason}")
    # Show details of what's available
    print(f"   Have: ₹{details['available_cash']}")
    print(f"   Need: ₹{details['total_cost']}")
```

### Example 2: View Settlement Schedule

```python
# What cash is coming when?
schedule = cash_flow.get_settlement_schedule()

for date, settlement in schedule.items():
    print(f"\n{date}:")
    print(f"  Inflow: ₹{settlement['expected_inflow']}")
    print(f"  Outflow: ₹{settlement['expected_outflow']}")
    print(f"  Net: ₹{settlement['expected_inflow'] - settlement['expected_outflow']}")
```

### Example 3: Daily Health Check

```python
# Quick health check
status = order_manager.get_trading_status()

print(f"✅ Can trade: {status['can_trade']}")
print(f"Available: ₹{status['cash_position']['available_cash']}")
print(f"Utilization: {status['cash_position']['utilization_percent']:.1f}%")

if not status['can_trade']:
    print("\n❌ Trading blocked due to:")
    for check, result in status['daily_limits']['checks'].items():
        if not result['passed']:
            print(f"  - {result['message']}")
```

## Integration Timeline

### Phase 1: Basic Integration (Week 1)
- [ ] Add CashFlowManager to order_manager
- [ ] Add fund validation before orders
- [ ] Track buy/sell transactions
- [ ] Test with paper trading

### Phase 2: Advanced Monitoring (Week 2)
- [ ] Add settlement schedule tracking
- [ ] Implement daily limit checks
- [ ] Add margin call detection
- [ ] Daily monitoring reports

### Phase 3: Automation (Week 3+)
- [ ] Auto-liquidation on margin call
- [ ] Settlement reminder alerts
- [ ] Daily health reports
- [ ] Optimization analysis

## Key Takeaways

1. **Never assume you have cash available**
   - Always check available_cash before ordering
   - Remember T+2 settlements block capital

2. **Plan trades with settlement dates in mind**
   - Use settlement_schedule to see cash flow
   - Spread trades across days to avoid liquidity crunches

3. **Monitor daily limits**
   - Don't spend > 30% of capital per day
   - Keep buffer for unexpected costs

4. **Prepare for margin calls**
   - Keep utilization < 75%
   - Have liquidation plan ready
   - Monitor daily

5. **Test thoroughly**
   - Run paper trading for 2 weeks
   - Stress-test with margin call scenarios
   - Verify all alerts working

## Files Created

```
app/services/
├── cash_flow_manager.py           # Core cash flow logic (600+ lines)
└── cash_flow_integration.py        # Integration with OrderManager

Documentation/
├── CASH_FLOW_PRODUCTION_GUIDE.md   # This file
├── SETTLEMENT_SCHEDULE_GUIDE.md    # How to interpret schedules
└── MARGIN_CALL_SCENARIOS.md        # What-if analysis
```

## Next Steps

1. Read through the code in `cash_flow_manager.py`
2. Integrate with existing OrderManager
3. Test with paper trading
4. Set up monitoring and alerts
5. Go live after 2 weeks of successful paper testing

---

**Created**: 2026-05-30  
**Status**: Production Ready  
**Risk Level**: 🔴 CRITICAL - Must implement before live trading  
**Approval Required**: Yes - Test thoroughly before using real capital
