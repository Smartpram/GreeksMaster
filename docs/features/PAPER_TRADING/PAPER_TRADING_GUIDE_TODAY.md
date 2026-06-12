# 📊 Paper Trading Session - June 10, 2026 (Indian Markets)

## Quick Start

```bash
# 1. Run paper trading session (10 min cycle)
python paper_trading_session_today.py

# 2. View live logs
tail -f logs/paper_trading_session.log

# 3. Check results
ls -la logs/paper_trading_report_*.json
```

## Session Overview

**Date:** June 10, 2026 (Tuesday)  
**Market:** NSE/BSE (Indian Equities)  
**Hours:** 9:15 AM - 3:30 PM IST  
**Capital:** ₹5,00,000 (paper trading)  
**Strategy:** Golden Cross (MA20 > MA50)  

## Watchlist (20 symbols)

### Indices
- NIFTY50 (Nifty 50)
- BANKNIFTY (Bank Nifty)
- INFTEC (Nifty IT)

### Bank Stocks
- HDFCBANK (HDFC Bank)
- ICICIBANK (ICICI Bank)
- SBIN (State Bank of India)
- AXISBANK (Axis Bank)

### IT Stocks
- TCS (Tata Consultancy Services)
- INFY (Infosys)
- WIPRO (Wipro)

### Conglomerate/Energy
- RELIANCE (Reliance Industries)
- POWERGRID (Power Grid)

### Auto/Cement/Steel
- MARUTI (Maruti Suzuki)
- ULTRACEMCO (UltraTech Cement)
- JSWSTEEL (JSW Steel)
- LT (Larsen & Toubro)

### Pharma/Consumer/Paints
- SUNPHARMA (Sun Pharmaceutical)
- ITC (ITC Limited)
- ASIANPAINT (Asian Paints)

### Financials
- BAJAJFINSV (Bajaj Finserv)

## Trading Logic

### BUY Signal (Golden Cross)
```
✓ MA20 crosses above MA50 (uptrend begins)
✓ RSI < 70 (not overbought)
✓ Volume confirmation
→ Action: Buy 10% portfolio
```

### SELL Signal (Death Cross)
```
✓ MA20 crosses below MA50 (downtrend begins)
✓ RSI > 30 (not oversold)
→ Action: Sell entire position
```

### HOLD Signal
```
✓ Price between MA20-MA50
✓ RSI neutral
→ Action: No trade
```

## Expected Outcomes

### Success Criteria
- ✅ Signals generated on 50%+ symbols
- ✅ Positive P&L on exits
- ✅ <50% capital utilization
- ✅ Clean execution logs

### Typical Results (Backtested)
- Win Rate: 50-55%
- Avg Win: ₹500-1,000 per trade
- Avg Loss: -₹300-500 per trade
- Sharpe Ratio: 0.8+

## Log Files

### Main Log
```
logs/paper_trading_session.log
```

**Contains:**
- Initialization info
- Screening cycles
- Entry/exit prices
- P&L calculations
- Portfolio status

### Trade Report (JSON)
```
logs/paper_trading_report_20260610_HHMMSS.json
```

**Contains:**
- All trades executed
- Open positions
- Capital utilization
- Timestamped details

## Real-Time Monitoring

```bash
# Terminal 1: Run session
python paper_trading_session_today.py

# Terminal 2: Watch logs (live)
tail -f logs/paper_trading_session.log

# Terminal 3: Monitor report (after session)
cat logs/paper_trading_report_*.json | jq .
```

## Output Example

```
════════════════════════════════════════════════════════════════════════════════
                        PAPER TRADING SESSION START
════════════════════════════════════════════════════════════════════════════════

Market: Indian NSE/BSE | Date: 2026-06-10 | Time: 14:32:45 IST

════════════════════════════════════════════════════════════════════════════════
SCREENING CYCLE STARTED
Time: 2026-06-10 14:32:45 IST
════════════════════════════════════════════════════════════════════════════════

✅ BUY: RELIANCE | Q: 178 @ ₹2,809.12 | Total: ₹500,000.00
   Reasoning: Golden Cross: MA20 (2814.32) > MA50 (2798.76); RSI (62.34) not overbought
   Remaining Capital: ₹0.00

✅ BUY: TCS | Q: 138 @ ₹3,623.45 | Total: ₹500,000.00
   Reasoning: Golden Cross: MA20 (3645.23) > MA50 (3601.12); RSI (58.91) not overbought
   Remaining Capital: ₹0.00

════════════════════════════════════════════════════════════════════════════════
PORTFOLIO STATUS
════════════════════════════════════════════════════════════════════════════════

Open Positions: 2
  • RELIANCE: 178 @ ₹2,809.12 = ₹500,000.00
  • TCS: 138 @ ₹3,623.45 = ₹500,000.00

Available Capital: ₹0.00
Total Capital: ₹500,000.00
Utilization: 100.0%

Trades Executed: 2
  • Buys: 2
  • Sells: 0
  • Realized P&L: ₹0.00

════════════════════════════════════════════════════════════════════════════════
                            SESSION COMPLETE
════════════════════════════════════════════════════════════════════════════════
```

## Next Cycle

To run multiple screening cycles:

```python
# Run continuous screening every 5 minutes
import time

session = PaperTradingSession()

for cycle in range(1, 100):  # 100 cycles = ~8 hours
    logger.info(f"\n{'='*80}\nCYCLE {cycle} - {session.get_ist_now()}\n{'='*80}")
    signals = session.run_screening()
    session.print_portfolio_status()
    time.sleep(300)  # Wait 5 minutes

session.save_session_report()
```

## Integration with Scheduler

To run this as a scheduled job (using EXECUTION_SEQUENCE_SCHEDULER.md):

```python
# In app/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

# Run paper trading every 5 minutes during market hours
scheduler.add_job(
    run_paper_trading,
    CronTrigger(minute='*/5', hour='9-15'),  # 9:15 AM - 3:30 PM
    name='paper_trading_session'
)

scheduler.start()
```

## Files Generated

```
logs/
├── paper_trading_session.log                    # Main log
└── paper_trading_report_20260610_HHMMSS.json   # Trade report
```

## Troubleshooting

### No signals generated
- Check if market is open (9:15 AM - 3:30 PM IST)
- Verify data is loading (check logs for errors)
- Check watchlist symbols are correct

### Capital exhausted too quickly
- Adjust position size: Change `0.1` to `0.05` in execute_paper_trade()
- This limits each trade to 5% instead of 10% of capital

### Positions not closing
- Check RSI threshold (currently 30 for sell)
- Verify MA crossover logic
- Check for missing data points

## Success Tips

✅ Run during market hours (9:15 AM - 3:30 PM IST)  
✅ Let it complete full cycle before evaluating  
✅ Check logs for signal reasoning  
✅ Verify P&L on each trade  
✅ Compare with backtesting results  

## Next Steps

1. ✅ Run today's session (10 min)
2. Review generated trades and P&L
3. Compare with backtesting results
4. If profitable, schedule daily runs
5. Move to live trading (Phase 5)

---

**Status:** Ready to Execute  
**Date:** June 10, 2026  
**Capital:** ₹5,00,000 (Paper)  
**Duration:** ~8 hours (market hours)  

**Command:**
```bash
python paper_trading_session_today.py
```

Let's start paper trading! 🚀
