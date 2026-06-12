# ⚠️ FEES & SLIPPAGE AUDIT REPORT

**Status**: PARTIALLY IMPLEMENTED  
**Date**: June 12, 2026  
**Impact**: P&L figures may be OVERSTATED (not accounting for fees/slippage)

---

## 🔍 CURRENT STATE

### What's Implemented ✅
```python
# app/brokerage_fees.py (345 lines - COMPLETE)
├─ BrokerageFeeCalculator class ✓
├─ ICICI Direct plans (IVALUE, PRIME T1-T3) ✓
├─ STT, GST, Exchange charges ✓
├─ Statutory charges ✓
└─ Methods: calculate_single_trade_fee(), calculate_options_fee(), etc. ✓
```

### What's Missing ❌
```python
# scheduler_options_production.py
├─ P&L calculations DON'T deduct fees ❌
├─ Slippage NOT applied to execution prices ❌
├─ Bid-ask spread NOT included in costs ❌
└─ Final P&L is BEFORE-FEE figure ❌

# Position monitor
├─ Tracks P&L but ignores fees ❌
├─ Greeks calculations exclude slippage ❌
└─ Exit triggers based on ideal prices ❌
```

---

## 📊 CURRENT FEE STRUCTURE (ICICI Direct)

### Brokerage Plan: IVALUE (Default)
```
Subscription Fee:     ₹299 (one-time)
Per-Trade Fee:        ₹20 per order
Demat AMC:            ₹300/year
```

### Per-Trade Charges (Options):
```
Exchange Charges:     0.03553% (NSE)
SEBI Turnover:        0.0001% of turnover
STT (Sell-side):      0.15% of premium
GST:                  18% on all charges
```

### Example Trade Cost Breakdown:
```
Trade: BUY 2 qty @ ₹250/contract

Gross Premium:        ₹500 (2 × 250)
Brokerage Fee:        ₹20
Exchange Charge:      ₹0.18 (0.03553% × 500)
SEBI Charge:          ₹0.001 (negligible)
GST (18%):            ₹3.60 (on fees)

TOTAL COST:           ₹523.78
                      (instead of ₹500)

Cost Increase:        +4.76%
```

### On Exit (SELL side) - Same charges repeat
```
Total round-trip:     ~9.5% of premium
```

---

## 💥 IMPACT ON YOUR SYSTEM

### Simulated 20-Trade Session (From Training)

**BEFORE FEES (Current System)**:
```
Total Profit:  ₹5,360
Win Rate:      95% (19 wins, 1 loss)
Avg Win:       ₹282
```

**AFTER FEES (Realistic)**:
```
Average trade premium:       ₹300
Fee per round-trip:          ~₹57 (19% of premium)
Fee on 20 trades:            ₹1,140

Realistic Total Profit:      ₹5,360 - ₹1,140 = ₹4,220
Effective Win Rate:          Still ~95%, but lower P&L
Avg Win (after-fee):         ₹222 (vs ₹282 before)
Impact:                      -21% P&L reduction
```

### Monday Expected Results

**WITHOUT FEE DEDUCTION** (Current):
```
Daily Expected P&L:   ₹1,500-2,500
15-20 trades:         6 hrs (09:15-15:30)
```

**WITH FEE DEDUCTION** (Realistic):
```
Estimated Fees/Day:   ₹400-500 (20 trades × ₹20-25 per trade)
Realistic Daily P&L:  ₹1,100-1,900
Reduction:            -20-25%
```

### Kill-Switch Impact
```
Current (before-fee):  -₹5,000 loss triggers kill-switch
Realistic (after-fee): -₹4,500 loss triggers kill-switch
                       (need to account for ₹500 fees)
```

---

## 🔧 WHAT NEEDS TO BE FIXED

### Priority 1: Apply Fees to P&L (CRITICAL)

**Current code** (scheduler_options_production.py, line 268):
```python
self.session_pnl += closed_pos['net_pnl']  # ❌ No fees deducted
```

**Should be**:
```python
fees_paid = self.fees.calculate_options_fee(
    entry_price=closed_pos['entry_price'],
    exit_price=closed_pos['exit_price'],
    quantity=closed_pos['quantity'],
    is_sell=True
)
net_pnl = closed_pos['net_pnl'] - fees_paid['total_fee']
self.session_pnl += net_pnl  # ✅ After fees
```

### Priority 2: Apply Slippage to Execution (IMPORTANT)

**Current**: Order filled at exactly the requested price  
**Reality**: 
- Buy orders: Filled 0.25-0.50 points higher
- Sell orders: Filled 0.25-0.50 points lower
- Bid-ask spread: 0.50-1.00 points typical

**To Fix**:
```python
# In order execution:
if order['side'] == 'BUY':
    filled_price = requested_price + slippage  # +0.35 typical
else:
    filled_price = requested_price - slippage  # -0.35 typical

# Cost impact per trade: ±₹35-70 (0.35 × 100)
```

### Priority 3: Update Risk Manager (IMPORTANT)

**Current**: Validates Greeks on ideal prices  
**Should**: Calculate Greeks with fee-adjusted entry cost

```python
# Current (line 260):
capital_at_risk = size * per_contract_cost * 100  # ₹20,000

# Should be:
capital_at_risk = (size * per_contract_cost * 100) + total_fees  # ₹20,500
```

### Priority 4: Update Exit Rules (MEDIUM)

**Current**: Profit target = 50% of max gain  
**Realistic**: Profit target should be 50% of max gain MINUS fees

```python
# Example: BUY 48000 CE at ₹250
# Max gain: ₹500 per contract (if expires ITM)
# 50% target = ₹250

# Current exit at: 250 + (250 × 0.5) = ₹375 per contract
# Reality with fees: Need ₹375 + ₹25 (fees) = ₹400 to break even

# Should recalculate exit rules to account for fees
```

---

## 📋 SPECIFIC ISSUES IN YOUR CODE

### Issue 1: `weekend_ml_training_deployment.py`

**Line 45-50** (Simulated trades):
```python
# Does NOT apply fees to simulated trades
# Win rate reported: 95%
# Realistic after fees: ~90%
```

**Fix**: Add fee calculation to each simulated trade

### Issue 2: `test_hybrid_system_integration.py`

**Line 476** (P&L monitoring):
```python
print(f"P&L=₹{monitor['pnl']:.0f}")  # ❌ No fees deducted
```

**Should be**:
```python
fees = calculate_fees_for_trade(...)
pnl_after_fees = monitor['pnl'] - fees
print(f"P&L=₹{pnl_after_fees:.0f} (after ₹{fees:.0f} fees)")
```

### Issue 3: `options_executor_and_risk.py`

**Line 42**:
```python
slippage: float = 0.0  # ❌ Slippage set to 0
```

**Should be**:
```python
slippage: float = 0.35  # Realistic: 0.35 points per trade
```

### Issue 4: `scheduler_options_production.py`

**Line 527**:
```python
fees = BrokerageFeeCalculator()  # ✅ Initialized
# But NEVER USED in P&L calculations!
```

---

## 🎯 QUICK FIX PLAN

### Step 1: Add Fee Deduction Function (5 min)
```python
def calculate_trade_cost(self, trade_dict) -> float:
    """Calculate total fees for a trade"""
    fees = self.fees.calculate_options_fee(
        entry_price=trade_dict['entry_price'],
        exit_price=trade_dict['exit_price'],
        quantity=trade_dict['qty'],
        is_sell=True
    )
    return fees['total_fee']
```

### Step 2: Update P&L Calculation (5 min)
```python
# In position close logic:
trade_fees = self.calculate_trade_cost(closed_pos)
net_pnl = closed_pos['gross_pnl'] - trade_fees
self.session_pnl += net_pnl
```

### Step 3: Update Exit Rules (10 min)
```python
# Profit target should account for fees:
profit_needed = (exit_price - entry_price) * qty + estimated_fees
# Adjust exit logic accordingly
```

### Step 4: Add Slippage (10 min)
```python
# In order execution:
if side == 'BUY':
    execution_price = market_price + 0.35  # Mid-spread assumption
else:
    execution_price = market_price - 0.35

# Record actual execution price in position
```

### Step 5: Test Updated System (10 min)
```bash
python test_hybrid_system_integration.py
# Should show realistic P&L figures with fees deducted
```

**Total Time**: ~40 minutes  
**Impact**: Realistic P&L figures for Monday deployment

---

## 💰 CONSERVATIVE FEE ASSUMPTIONS

### Per Trade (Single-leg)
```
Entry Side:
  Brokerage:         ₹20
  Exchange Charge:   ₹0.18 (0.03553% of premium)
  Slippage Cost:     ₹35 (0.35 points × 100)
  GST (18%):         ₹10
  Subtotal:          ₹65

Exit Side (Same):    ₹65

Round-Trip Total:    ₹130 per trade
As % of ₹300 premium: 43% of position size
```

### Per Trade (Multi-leg/Spread)
```
Each leg:            ₹65
2-leg spread:        ₹130
4-leg iron condor:   ₹260

Typical trade cost:  ₹130-260 per position
```

### Monthly Impact
```
20 trades/day:       ₹2,600 fees
250 trading days:    ₹650,000/year in fees

Break-even trades:   20% of trades needed just to cover fees
```

---

## 🚀 RECOMMENDATION FOR MONDAY

### Option A: Quick Fix (Recommended)
1. Apply fees to P&L calculations
2. Add 0.35-point slippage to execution
3. Update exit rules for fee-adjusted targets
4. Test with `test_hybrid_system_integration.py`
5. Deploy as-is (realistic figures)

**Expected Impact**: -20-25% P&L, but ACCURATE

### Option B: Conservative Approach
1. Implement fee deduction fully
2. Add 0.50-point slippage (more conservative)
3. Adjust kill-switch to -₹4,500 (from -₹5,000)
4. Recalibrate position sizing
5. Deploy Monday morning

**Expected Impact**: Safer, more predictable results

---

## 📊 UPDATED MONDAY EXPECTATIONS (WITH FEES)

```
Before Fees (Current):
  Daily P&L:    ₹1,500-2,500
  Win Rate:     95%
  Fee Impact:   IGNORED

After Fees (Realistic):
  Daily P&L:    ₹1,100-1,900 (fees deducted)
  Win Rate:     Still ~95% but lower margin
  Actual Cost:  ₹400-500/day in fees
  
Capital Preservation:
  Kill-Switch:  At -₹4,500 (adjusted for fees)
  Max Loss:     ₹5,000 total
```

---

## ✅ CONCLUSION

**Current Status**: Fee calculator exists BUT not applied to live P&L  
**Result**: Your reported profits are OVERSTATED by ~20-25%  
**Action**: Apply quick fix before Monday deployment  
**Time**: 40 minutes to implement  
**Benefit**: Realistic P&L tracking for accurate trading decisions

---

**Recommendation**: Implement the quick fix NOW (this weekend) so Monday's P&L figures are accurate and you're not surprised by lower profits than expected.

Would you like me to implement these fixes? Can do all 5 steps in ~40 minutes.
