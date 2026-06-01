# Visual User Guide - Live Trading System

A visual walkthrough of how to use the complete live trading system.

---

## System Architecture at a Glance

```
📊 STOCK UNIVERSE (201 Stocks)
        │
        ├─→ 🔍 MOMENTUM SCREENER → TCS (92%), INFY (85%)
        ├─→ 🔍 BREAKOUT SCREENER → HDFC (88%), RELIANCE (82%)
        ├─→ 🔍 VALUE SCREENER → MARUTI (75%), SBIN (78%)
        └─→ 🔍 [9 MORE SCREENERS...]
        
        All Results ──→ 📍 SIGNAL EXECUTOR
                             │
                             ├─→ Validate signal
                             ├─→ Check risk limits
                             ├─→ Place order
                             └─→ Start tracking
                                    │
                                    ▼
                        👁️ LIVE POSITION TRACKER
                             │
                             ├─→ Track P&L
                             ├─→ Monitor triggers
                             ├─→ Record signals
                             └─→ Auto-exit if triggered
                                    │
                                    ▼
                        📊 PORTFOLIO DASHBOARD
                             │
                             ├─→ All open positions
                             ├─→ Total P&L
                             ├─→ Win rate
                             └─→ Performance metrics
```

---

## Daily Trading Cycle - Visual

```
START OF DAY (09:15 AM)
│
├─ RUN SCREENERS
│  │
│  ├─ Scan 201 stocks
│  ├─ Apply 12 different criteria
│  ├─ Score each stock (0-100)
│  └─ Find: 15-20 qualified stocks
│
├─ EXECUTE ENTRY SIGNALS
│  │
│  ├─ Top 5 stocks identified
│  ├─ Risk check ✓
│  ├─ Position size: 10 shares each
│  ├─ Place BUY orders
│  └─ Start tracking 5 positions
│
├─ MONITOR POSITIONS (09:30-11:30)
│  │
│  ├─ Every minute:
│  │  ├─ Update prices
│  │  ├─ Calculate P&L
│  │  ├─ Check triggers
│  │  └─ Display portfolio
│  │
│  ├─ Example updates:
│  │  ├─ TCS: +2.5% (monitor)
│  │  ├─ INFY: +10% → EXIT (target hit)
│  │  ├─ WIPRO: -4% (monitor)
│  │  └─ HDFC: -5.2% → EXIT (stop loss)
│  │
│  └─ Result: 2 positions closed, 3 open
│
├─ EXECUTE EXIT SIGNALS (as needed)
│  │
│  ├─ Exit 1: INFY +10% (take profit)
│  ├─ Exit 2: WIPRO -5% (stop loss)
│  ├─ Exit 3: TCS +7% (signal)
│  └─ Continue monitoring remaining
│
└─ END OF DAY REPORT (16:00)
   │
   ├─ Total P&L: +₹2,450
   ├─ Closed Trades: 3
   ├─ Win Rate: 67% (2 winners, 1 loser)
   ├─ Best Trade: +₹500 (INFY)
   ├─ Worst Trade: -₹200 (WIPRO)
   └─ Export report for records
```

---

## Position Lifecycle - Visual

```
POSITION OPENS
├─ Symbol: TCS
├─ Entry Price: ₹3,500
├─ Quantity: 10
├─ Time: 09:30
└─ Status: OPEN

        ▼ [Price Updates Every Minute]

POSITION MONITORING
├─ 09:31 → Price: ₹3,510 → P&L: +₹100
├─ 09:32 → Price: ₹3,520 → P&L: +₹200
├─ 09:33 → Price: ₹3,530 → P&L: +₹300
├─ 09:34 → Price: ₹3,540 → P&L: +₹400
└─ 09:35 → Price: ₹3,550 → P&L: +₹500

        ▼ [Trigger: Price Hit Target]

POSITION CLOSES
├─ Exit Price: ₹3,650 (15% above entry)
├─ Quantity: 10
├─ Time: 09:45
├─ Reason: Target Hit
├─ Realized P&L: +₹1,500
└─ Status: CLOSED

        ▼ [Record Trade]

TRADE RECORDED
├─ Entry: ₹3,500 × 10 = ₹35,000
├─ Exit: ₹3,650 × 10 = ₹36,500
├─ Profit: ₹1,500
├─ Return: +4.3%
└─ Duration: 15 minutes
```

---

## Screener Workflow - Visual

```
MOMENTUM SCREENER EXAMPLE

Input: 201 stocks

CRITERIA CHECK:
├─ RSI > 60? 
│  ├─ TCS: ✓ (RSI 68)
│  ├─ INFY: ✓ (RSI 65)
│  ├─ WIPRO: ✗ (RSI 45)
│  └─ ...
├─ Price > MA50?
│  ├─ TCS: ✓
│  ├─ INFY: ✓
│  ├─ WIPRO: ✗
│  └─ ...
├─ Volume surge?
├─ Daily gain > 2%?
└─ ...

SCORING:
├─ TCS: 92/100 ⭐⭐⭐⭐⭐
├─ INFY: 85/100 ⭐⭐⭐⭐
├─ HDFC: 78/100 ⭐⭐⭐
└─ ...

OUTPUT:
┌─────────────────────────┐
│ MOMENTUM QUALIFIED      │
├─────────────────────────┤
│ ✓ TCS     (92/100)      │
│ ✓ INFY    (85/100)      │
│ ✓ HDFC    (78/100)      │
│ ✓ RELIANCE(75/100)      │
│ ✓ SBIN    (72/100)      │
└─────────────────────────┘

NEXT: Execute buy signals
```

---

## Signal Execution Modes - Visual

```
MANUAL MODE
├─ User creates signal
│  └─ Signal queued for approval
├─ System shows approval dialog
│  └─ "Do you approve this trade?"
├─ User clicks YES or NO
│  ├─ YES → Order placed
│  └─ NO → Order rejected
└─ Best for: Learning, caution

    ┌─────────────────────┐
    │ Approve BUY TCS?    │
    ├─────────────────────┤
    │ Symbol: TCS         │
    │ Price: ₹3,500       │
    │ Qty: 10             │
    │ Confidence: 92%     │
    └─────────────────────┘
       [YES] [NO]


SEMI-AUTO MODE
├─ User creates signal
│  └─ Signal auto-executes
├─ System sends notification
│  └─ "BUY signal executed: TCS"
├─ User can cancel before execution
│  └─ Last chance to reject
└─ Best for: Balanced, monitored

    📱 NOTIFICATION
    ┌──────────────────────┐
    │ Trade Executed ✓     │
    ├──────────────────────┤
    │ BUY TCS × 10         │
    │ Price: ₹3,500        │
    │ P&L: Tracking...     │
    └──────────────────────┘


AUTO MODE
├─ User creates signal
│  └─ Signal auto-executes
├─ System logs the trade
│  └─ No user intervention
├─ Risk checks still happen
│  └─ Position size validated
└─ Best for: Production, high confidence

    ⚡ AUTO EXECUTED
    ├─ Entry: ₹3,500
    ├─ Qty: 10
    ├─ Order ID: ORD123456
    └─ Status: FILLED


PAPER MODE (DEFAULT)
├─ Everything is simulated
├─ No real money used
├─ No real orders placed
├─ Perfect for testing
└─ Best for: Development, testing

    🔬 SIMULATION
    ├─ Virtual balance: ₹100,000
    ├─ Test orders placed
    ├─ Test P&L calculated
    └─ No real impact
```

---

## Portfolio Dashboard - Visual

```
📊 LIVE PORTFOLIO DASHBOARD
═══════════════════════════════════════════════

💰 ACCOUNT
├─ Total Capital: ₹100,000
├─ Available: ₹62,000
└─ Deployed: ₹38,000

📈 PERFORMANCE
├─ Unrealized P&L: +₹2,800 (↑7.4%)
├─ Realized P&L: +₹1,200 (↑1.2%)
├─ Total P&L: +₹4,000 (↑4.0%)
└─ Today's Return: +3.8%

📍 OPEN POSITIONS (4)
┌──────────────────────────────────────┐
│ TCS                                  │
├──────────────────────────────────────┤
│ Entry: ₹3,500 × 10 | Current: ₹3,520│
│ Unrealized P&L: +₹200 (+0.6%)        │
│ Entry Time: 09:30 | Days Open: 1     │
│ Signals: 0                           │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ INFY                                 │
├──────────────────────────────────────┤
│ Entry: ₹1,850 × 15 | Current: ₹1,920│
│ Unrealized P&L: +₹1,050 (+3.8%)      │
│ Entry Time: 09:35 | Days Open: 1     │
│ Signals: 1 (Target near)             │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ HDFC BANK                            │
├──────────────────────────────────────┤
│ Entry: ₹2,000 × 12 | Current: ₹2,080│
│ Unrealized P&L: +₹960 (+4.0%)        │
│ Entry Time: 10:00 | Days Open: 0.5   │
│ Signals: 0                           │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ RELIANCE                             │
├──────────────────────────────────────┤
│ Entry: ₹2,400 × 8 | Current: ₹2,380 │
│ Unrealized P&L: -₹160 (-0.8%)        │
│ Entry Time: 10:30 | Days Open: 0.2   │
│ Signals: 1 (Stop loss near)          │
└──────────────────────────────────────┘

📊 STATS
├─ Closed Trades: 2
├─ Win Rate: 100% (2/2)
├─ Best Trade: +₹1,500 (WIPRO)
├─ Worst Trade: +₹400 (SBIN)
└─ Avg Trade: +₹950

⚙️ SYSTEM
├─ Mode: SEMI_AUTO
├─ Pending Approvals: 1
├─ Execution Success: 95.2%
└─ Last Update: 10:45:32
```

---

## Signal Types - Visual

```
ENTRY SIGNALS
├─ BUY SIGNAL
│  ├─ Source: Screener/Technical/AI
│  ├─ Action: Place buy order
│  ├─ Risk Check: Position sizing ✓
│  └─ Result: Position opened
│
└─ ADD POSITION
   ├─ Condition: Position up 10%+
   ├─ Action: Buy more (pyramid)
   └─ Risk Check: Total size limit

EXIT SIGNALS
├─ TAKE PROFIT
│  ├─ Condition: Up 15%+
│  ├─ Action: Sell all or partial
│  └─ Result: Profit locked
│
├─ STOP LOSS
│  ├─ Condition: Down 5%+
│  ├─ Action: Sell immediately
│  └─ Result: Loss limited
│
├─ TRAILING STOP
│  ├─ Condition: Price falls 3% from high
│  ├─ Action: Follow price up, exit on pullback
│  └─ Result: Capture gains while protecting
│
└─ SIGNAL-BASED EXIT
   ├─ Condition: Technical/screener signal reverses
   ├─ Action: Exit position
   └─ Result: Exit on confirmation
```

---

## Real-World Example - Momentum Trade

```
09:30 - MORNING
────────────────
🔍 SCREENER RUNS
│
├─ Momentum Screener Results:
│  ├─ TCS: Score 92/100
│  │  - RSI: 68 (overbought)
│  │  - MA50: ₹3,480 (price above)
│  │  - Volume: Up 250%
│  │  - Daily gain: +2.8%
│  │
│  └─ Confidence: 92%

📍 SIGNAL GENERATED
│
├─ execute_buy_signal(
│    symbol='TCS',
│    price=3500,
│    confidence=0.92,
│    reason='momentum_screener'
│  )

✅ ORDER PLACED
│
├─ Order ID: ORD123456
├─ Buy 10 shares @ ₹3,500
├─ Status: FILLED
└─ Cost: ₹35,000


09:45 - MONITORING
──────────────────
👁️ POSITION TRACKED

Time    | Price | P&L    | P&L%  | Status
--------|-------|--------|-------|--------
09:30   | 3,500 | 0      | 0%    | OPEN
09:35   | 3,510 | +100   | +0.3% | ↑
09:40   | 3,525 | +250   | +0.7% | ↑↑
09:45   | 3,540 | +400   | +1.1% | ↑↑↑
09:50   | 3,560 | +600   | +1.7% | ↑↑↑
09:55   | 3,580 | +800   | +2.3% | ↑↑↑
10:00   | 3,600 | +1,000 | +2.9% | ↑↑↑
10:05   | 3,625 | +1,250 | +3.6% | ↑↑↑↑
10:10   | 3,650 | +1,500 | +4.3% | TARGET HIT! 🎯


10:12 - EXIT SIGNAL
────────────────────
🎯 TARGET HIT
│
├─ Price: ₹3,650 (15% above entry)
├─ execute_exit_signal(
│    symbol='TCS',
│    price=3650,
│    reason='target_hit'
│  )

✅ ORDER PLACED
│
├─ Order ID: ORD789012
├─ Sell 10 shares @ ₹3,650
├─ Status: FILLED
└─ Return: ₹36,500


10:15 - TRADE CLOSED
─────────────────────
📊 TRADE SUMMARY
│
├─ Entry: ₹3,500 × 10 = ₹35,000
├─ Exit: ₹3,650 × 10 = ₹36,500
├─ Profit: ₹1,500
├─ Return: +4.3%
├─ Duration: 45 minutes
├─ Quality: ⭐⭐⭐⭐⭐ (Excellent)
└─ Status: CLOSED ✓

📈 LOGGED
│
└─ Trade added to portfolio history
   - Best Trade This Session: +₹1,500
   - Win Rate: 100% (1/1)
```

---

## Integration Points - Visual

```
COMPONENT INTERACTIONS

Stock Screener
     │
     ├─ Uses: Breeze API (historical data)
     ├─ Uses: Risk Manager (position limits)
     └─ Output: Qualified stocks + scores

Signal Executor
     │
     ├─ Uses: Stock Screener (signal source)
     ├─ Uses: Risk Manager (validation)
     ├─ Uses: Order Manager (execution)
     └─ Output: Executed orders

Live Position Tracker
     │
     ├─ Uses: Order Manager (order status)
     ├─ Uses: Risk Manager (position sizing)
     └─ Output: Real-time P&L

Live Trading System (Integration Layer)
     │
     ├─ Orchestrates: Stock Screener
     ├─ Orchestrates: Signal Executor
     ├─ Orchestrates: Position Tracker
     └─ Provides: Portfolio Dashboard

All Components
     │
     └─ Log: Execution history, alerts, reports
```

---

## Command Reference - Quick

```bash
# Initialize and run
python run_live_trading_system.py

# Check system status
system.get_status()

# Run screeners
results = system.run_all_screeners(stocks_df)

# Execute signals
system.execute_top_screener_signals(results)

# Monitor positions
system.update_all_positions(current_prices)
system.auto_exit_triggered_positions()

# View report
system.print_report()
system.export_report()

# Change mode
system.set_execution_mode('semi_auto')
```

---

## Success Path

```
WEEK 1: PAPER TRADING (Safe)
├─ Run system in PAPER mode
├─ No real money at risk
├─ Test all 12 screeners
├─ Validate P&L calculations
├─ Review all signals
└─ Target: 50+ test trades

WEEK 2: SEMI-AUTO (Monitored)
├─ Switch to real trading
├─ Use SEMI_AUTO mode
├─ Review each trade
├─ Approve/reject signals
├─ Monitor performance
└─ Target: 80%+ approval rate

WEEK 3+: AUTO MODE (Automated)
├─ Full automation enabled
├─ System trades independently
├─ Review daily reports
├─ Adjust parameters as needed
└─ Target: 60%+ win rate

ONGOING: PRODUCTION
├─ Daily P&L reviews
├─ Weekly performance analysis
├─ Monthly strategy optimization
└─ Continuous improvements
```

---

**That's it! You now have a complete, production-ready live trading system. Start with paper trading, monitor carefully, and scale up as you gain confidence.** 🚀
