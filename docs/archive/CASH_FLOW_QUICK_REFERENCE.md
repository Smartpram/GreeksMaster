---
title: CASH FLOW MANAGER - QUICK REFERENCE
created: 2026-05-30
category: Quick Reference
---

# CASH FLOW MANAGER - QUICK REFERENCE GUIDE

## TL;DR - The Problem & Solution

### The Problem
You buy stocks on Monday, cash is blocked. Wednesday (T+2), all purchases settle and your cash disappears. You haven't sold anything yet, so you need to ensure you don't overdraft.

### The Solution
`CashFlowManager` tracks:
- **available_cash**: What you can trade with RIGHT NOW
- **blocked_cash**: Money tied up in pending settlements  
- **pending_cash**: Money coming in from sales (not available yet)
- **reserved_cash**: For margin requirements

## 3-Line Implementation

```python
# 1. Create manager
cash_flow = CashFlowManager(initial_capital=100000)

# 2. Check before every buy
can_buy, reason, details = cash_flow.can_buy_delivery('RELIANCE', 10, 2500)
if not can_buy: return error(reason)

# 3. Record after execution
txn_id = cash_flow.record_buy_delivery(order_id, 'RELIANCE', 10, 2500)
```

## Quick Commands

### Check Cash Available
```python
pos = cash_flow.get_cash_position()
print(f"Available: ₹{pos['available_cash']}")  # What you can use
print(f"Blocked: ₹{pos['blocked_cash']}")      # Stuck in settlements
print(f"Pending: ₹{pos['pending_cash']}")      # Arriving later
```

### Before Buying
```python
can_buy, reason, details = cash_flow.can_buy_delivery(
    symbol='RELIANCE',
    quantity=10,
    price=2500
)
if can_buy:
    order_id = place_order(...)
    cash_flow.record_buy_delivery(order_id, 'RELIANCE', 10, 2500)
else:
    return f"Cannot buy: {reason}"
```

### After Selling (T+2 settlement)
```python
# This morning you sold shares
order_id = place_sell_order('RELIANCE', 10, 2550)
cash_flow.record_sell_delivery(order_id, 'RELIANCE', 10, 2550)

# Wednesday (T+2), settlement happens
# Cash becomes available
```

### Check If Margin Call
```python
triggered, info = order_manager.check_margin_call()
if triggered:
    print(f"Margin call! Utilization: {info['utilization']}%")
    print(f"Need to reduce below: {info['threshold']}%")
```

### See When Cash Arrives
```python
schedule = cash_flow.get_settlement_schedule()
for date, settlement in schedule.items():
    print(f"{date}: +₹{settlement['expected_inflow']} (from sales)")
```

## 4 Cash States

```
Available ─────→ Can buy with this RIGHT NOW
Blocked ───────→ Tied up in buy orders (T+0 to T+2)
Pending ───────→ From sales, will arrive T+2 after sale
Reserved ──────→ Reserved for margin (not available to use)
```

## Transaction Lifecycle

### Buy Delivery (Most Important)
```
T+0 (Buy Day):
├─ Cash BLOCKED immediately
│  available: 100K → 75K
│  blocked: 0K → 25K
└─ Status: BLOCKED

T+2 (Settlement Day - Wed):
├─ Settlement processed
├─ Shares in your demat
├─ blocked: 25K → 0K
└─ Status: SETTLED
```

### Sell Delivery (T+2 Standard)
```
T+0 (Sell Day):
├─ Execute sell (no cash impact yet)
└─ Status: PENDING

T+2 (Settlement Day - Wed):
├─ Cash received!
├─ pending: 50K → 0K
├─ available: increases
└─ Status: SETTLED
```

### Sell Delivery (T+0 with TPIN)
```
T+0 (Sell Day):
├─ Execute sell
├─ Cash available IMMEDIATELY
├─ pending: 50K → 0K
├─ available: increases
└─ Status: SETTLED
```

## Validations (In Order)

1. **Available Cash** ← Check first
   ```python
   if total_cost > available_cash:
       return "Insufficient funds"
   ```

2. **Daily Limit** ← Check second
   ```python
   if daily_outflow + cost > max_daily_outflow:
       return "Exceeds daily limit"
   ```

3. **Position Size** ← Check third
   ```python
   if cost > capital * 0.10:
       return "Position too large"
   ```

4. **Margin Utilization** ← Check always
   ```python
   if utilization > 0.75:
       trigger_margin_call()
   ```

## Fees (NSE/BSE Standard)

```
Brokerage:  0.001  (0.1%)  = ₹10 per ₹10,000
STT Tax:    0.0001 (0.01%) = ₹1 per ₹10,000
Charges:    Variable       = ₹0-5 per transaction

Total for ₹50,000 buy:
├─ Brokerage: ₹50
├─ Tax: ₹5
├─ Charges: ₹1
└─ Total: ₹56
```

## Configuration (Edit Before Going Live)

```python
CashFlowManager(
    initial_capital=100000,
    config={
        'brokerage_rate': 0.001,           # Your broker's rate
        'tax_rate': 0.0001,                # STT
        'transaction_charges': 0.00001,    # Exchange charges
        'settlement_days': 2,              # T+2 standard
        'enable_tpin': False,              # Set True if you have TPIN
        'margin_call_threshold': 0.75,     # Call margin at 75%
    }
)

# Also set daily limit
cf.max_daily_outflow = initial_capital * 0.30  # Max 30% per day
```

## Real Example

```python
# Monday Morning
cf = CashFlowManager(100000)  # ₹1 lakh capital

# 9:15 AM: Buy RELIANCE
can, reason, _ = cf.can_buy_delivery('RELIANCE', 10, 2500)
# returns: (True, "Approved", {...})
cf.record_buy_delivery('ORD001', 'RELIANCE', 10, 2500)
# cash: available=74,973, blocked=25,027

# 10:00 AM: Try to buy TCS  
can, reason, _ = cf.can_buy_delivery('TCS', 5, 3000)
# returns: (False, "Position too large", {...})
# REJECTED! (Position concentration limit)

# 11:00 AM: Check schedule
schedule = cf.get_settlement_schedule()
# {
#   "2026-06-02": {
#     "expected_outflow": 25027.50,
#     "note": "RELIANCE buy settles Wednesday"
#   }
# }

# Wednesday 9:15 AM
cf.process_settlement('TXN...')
# cash: available=49,973, blocked=0
# RELIANCE shares now yours!

# Wednesday 10:00 AM: Sell RELIANCE
cf.record_sell_delivery('ORD002', 'RELIANCE', 10, 2550)
# cash: available=49,973, pending=25,000
# (pending arrives Friday T+2)

# Friday 9:15 AM
cf.process_settlement('TXN...')
# cash: available=74,973
# Sale proceeds arrived!
```

## Danger Signs 🚨

```
⚠️ available_cash < 10% of capital
   → Stop buying, too little buffer

⚠️ utilization > 75%
   → Margin call imminent

⚠️ daily_outflow > 90% of limit
   → Can't make many more trades

⚠️ pending_settlements > 50
   → Too many open positions

⚠️ blocked_cash won't release
   → Check settlement dates
```

## Common Mistakes & Fixes

### Mistake 1: Forgetting T+2
```python
# WRONG
Monday: Buy ₹50K (cash blocked)
Wednesday: OOPS! Cash not available yet

# RIGHT
Monday: Buy ₹50K, remember it's blocked until Wednesday
Plan other trades with remaining cash
```

### Mistake 2: Ignoring Daily Limits
```python
# WRONG
Buy ₹20K, buy ₹25K, buy ₹20K (₹65K > ₹30K limit) ✗

# RIGHT
Check daily_remaining before each buy
Daily limit: ₹30K, already used ₹20K, can only buy ₹10K more ✓
```

### Mistake 3: Over-concentrating
```python
# WRONG
Buy ₹20K of one stock (20% of capital) ✗

# RIGHT
Max ₹10K per stock (10% of capital) ✓
Diversify across multiple stocks ✓
```

### Mistake 4: Forgetting Settlement Schedule
```python
# WRONG
Monday: Buy 5 stocks for ₹30K each = ₹150K
Wednesday: All settle, cash needed = ₹150K
Problem: You only have ₹100K!

# RIGHT
Monday: Buy 1-2 stocks max
Check settlement schedule
Only buy more when previous ones settle Wednesday
```

## Testing Before Live

```python
# Run test suite
python test_cash_flow_manager.py

# Expected output:
# TEST 1: initialization - PASS
# TEST 2: buy success - PASS
# ... (10 more tests)
# SUMMARY: 9 PASSED / 0 FAILED = 100%
```

## Daily Checklist

- [ ] Check `available_cash` at market open
- [ ] Review settlement schedule for incoming funds
- [ ] Verify no orders exceed daily limit
- [ ] Monitor utilization ratio (target < 60%)
- [ ] Check pending settlements count
- [ ] End of day: confirm all margins released
- [ ] Weekly: review transaction history

## Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `cash_flow_manager.py` | Core logic | 600+ |
| `cash_flow_integration.py` | OrderManager integration | 400+ |
| `test_cash_flow_manager.py` | Tests (run to validate) | 350+ |
| `CASH_FLOW_PRODUCTION_GUIDE.md` | Full documentation | 500+ |
| `CASH_FLOW_PHASE_10_SUMMARY.md` | Detailed summary | 600+ |
| This file | Quick reference | - |

## API Reference (Top 10 Functions)

```python
# Initialization
cf = CashFlowManager(initial_capital, config=None)

# Before Buying
cf.can_buy_delivery(symbol, qty, price) → (bool, reason, details)
cf.can_sell_delivery(symbol, qty, price) → (bool, reason, details)

# After Trading
cf.record_buy_delivery(order_id, symbol, qty, price) → txn_id
cf.record_sell_delivery(order_id, symbol, qty, price) → txn_id

# Monitoring
cf.get_cash_position() → {all cash states}
cf.get_settlement_schedule() → {date: {inflow, outflow, txns}}
cf.validate_daily_limits() → {all_pass: bool, checks: {...}}

# Settlements
cf.process_settlement(txn_id) → (success, message)

# Export
cf.export_transactions(filepath) → saves JSON
```

## When to Use Each Function

```
BEFORE EVERY ORDER:
├─ can_buy_delivery() or can_sell_delivery()
└─ Check response before proceeding

AFTER ORDER EXECUTION:
├─ record_buy_delivery() or record_sell_delivery()
└─ Pass order details immediately

DAILY MONITORING:
├─ get_cash_position() - Check cash at market open
├─ get_settlement_schedule() - Plan upcoming settlements
└─ validate_daily_limits() - Verify all checks pass

WHEN T+2 DATE ARRIVES:
├─ process_settlement(txn_id)
└─ Move cash from blocked/pending to available

WEEKLY/AUDIT:
├─ export_transactions(filepath)
└─ Review transaction history
```

## Integration Checklist

- [ ] Copy `cash_flow_manager.py` to `app/services/`
- [ ] Copy `cash_flow_integration.py` to `app/services/`
- [ ] Import in OrderManager
- [ ] Add validation in `place_buy_order()`
- [ ] Add validation in `place_sell_order()`
- [ ] Configure for your broker (fees, limits)
- [ ] Run `test_cash_flow_manager.py`
- [ ] Test with paper trading 2 weeks
- [ ] Go live!

---

**Quick Links**:
- Full Guide: See `CASH_FLOW_PRODUCTION_GUIDE.md`
- Implementation: See `CASH_FLOW_PHASE_10_SUMMARY.md`
- Tests: Run `python test_cash_flow_manager.py`
- Code: `app/services/cash_flow_manager.py`

**Created**: 2026-05-30  
**Status**: Production Ready  
**Last Updated**: 2026-05-30
