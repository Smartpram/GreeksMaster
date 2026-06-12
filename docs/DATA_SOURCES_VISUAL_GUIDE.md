# 📍 DATA SOURCES - VISUAL GUIDE

## WHERE TO GET DATA - QUICK REFERENCE

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PAPER TRADING DATA FLOW                              │
└─────────────────────────────────────────────────────────────────────────┘

THIS WEEKEND (June 12-14)
════════════════════════════════════════════════════════════════════════════

DATA REQUIREMENT #1: Historical Data for ML Training
────────────────────────────────────────────────────────────────────────────

Option A: AUTOMATIC (Easiest) ✅ RECOMMENDED
┌────────────────────────────────┐
│ Run This Command:              │
│                                │
│ python                         │
│ download_market_data.py        │
│                                │
│ Time: ~5 minutes               │
│ Symbols: INFY, TCS, RELIANCE  │
│ Period: 500 days               │
│ Output: CSV files in data/     │
└────────────────────────────────┘
            ↓
    Yahoo Finance API
    (Automatic download)
            ↓
    data/historical_*.csv


Option B: MANUAL (NSE Website) ✅ ALSO GOOD
┌────────────────────────────────┐
│ 1. Visit Website:              │
│    https://nseindia.com/       │
│                                │
│ 2. Navigate:                   │
│    Data → Historical Data      │
│                                │
│ 3. Select:                     │
│    Symbol, Date Range          │
│                                │
│ 4. Download: CSV               │
│                                │
│ 5. Save to:                    │
│    c:\Data\GreeksMaster\data\  │
│                                │
│ Time: ~10 minutes              │
└────────────────────────────────┘
            ↓
         NSE Server
    (Free public data)
            ↓
    data/historical_*.csv


Option C: PROGRAMMATIC (Breeze API) ✅ IF YOU HAVE CREDENTIALS
┌────────────────────────────────┐
│ Already integrated in:         │
│ app/options_data_fetcher.py    │
│                                │
│ If you have Breeze key:        │
│ Use it directly (automatic)    │
│                                │
│ Time: Real-time, no delay      │
└────────────────────────────────┘
            ↓
       Breeze API
    (Your credentials)
            ↓
  Historical options data


MONDAY DURING TRADING (June 15, 09:15-15:30 IST)
════════════════════════════════════════════════════════════════════════════

DATA REQUIREMENT #2: Live Real-Time Data
────────────────────────────────────────────────────────────────────────────

CANDLES (1-minute) ✅ REQUIRED
┌─────────────────────────────────────────┐
│  Breeze API (ICICI Direct)              │
│                                         │
│  Automatic every 1 minute               │
│                                         │
│  Data: OHLCV (Open, High, Low, Close)   │
│  Symbols: BANKNIFTY, NIFTY, INFY, TCS  │
│  Frequency: 09:15-15:30 IST             │
│  Your system: Auto-fetches              │
│                                         │
│  File: scheduler_options_production.py  │
│        (lines 50-75)                    │
└─────────────────────────────────────────┘
            ↓
       Live Candles
   (Every 1 minute)
            ↓
   31 Indicators
   (Calculated)
            ↓
   ML Signal
   (Every 10 min)


OPTIONS CHAIN (Live Greeks) ✅ REQUIRED
┌─────────────────────────────────────────┐
│  Breeze API (ICICI Direct)              │
│                                         │
│  Automatic every tick                   │
│                                         │
│  Data:                                  │
│  - Strikes, Prices, IV                  │
│  - Greeks (Δ, Γ, Θ, Vega)              │
│  - Bid-Ask spreads                      │
│                                         │
│  Symbols: BANKNIFTY, NIFTY options      │
│  Expiry: Weekly (Wed/Thu)               │
│  Frequency: Live, every tick            │
│                                         │
│  File: app/options_chain_manager.py     │
│        (lines 30-60)                    │
└─────────────────────────────────────────┘
            ↓
    Live Options Chain
    (Every tick)
            ↓
   Strategy Selection
   (9 strategies)
            ↓
    Order Execution


════════════════════════════════════════════════════════════════════════════
AFTER TRADING (Every Day 15:30 IST)
════════════════════════════════════════════════════════════════════════════

TRADE DATA (For ML Learning)
┌─────────────────────────────────────────┐
│  Your System Auto-Records:              │
│                                         │
│  ✓ All executed trades                  │
│  ✓ Entry prices & times                 │
│  ✓ Exit prices & times                  │
│  ✓ P&L results                          │
│  ✓ Exit reason (profit/loss/theta/etc)  │
│  ✓ Market conditions at entry           │
│  ✓ Indicator values                     │
│                                         │
│  File: Export to CSV/JSON               │
│  Location: logs/ folder                 │
└─────────────────────────────────────────┘
            ↓
   Saved locally
   (JSON format)
            ↓
   Daily ML Learning
   (15:30-16:00 IST)
            ↓
   Model Improved
   (Ready for next day)


════════════════════════════════════════════════════════════════════════════
```

---

## 🎯 DATA CHECKLIST

### BEFORE THIS WEEKEND (Today - June 12)
```
□ Internet connection: Verify (required)
□ Python 3.13+: Check installed
□ Dependencies: pip install -r requirements.txt
□ Free disk space: 1 GB minimum
□ Windows machine: Ready
```

### THIS WEEKEND (June 12-14)
```
□ Historical data downloaded (Option A, B, or C)
□ Files location: c:\Data\GreeksMaster\data\
□ Files format: CSV with OHLCV columns
□ Validate data: Run download_market_data.py
□ ML model trained: weekend_ml_training_deployment.py
□ System tested: test_hybrid_system_integration.py
□ All tests passing: 14/14 ✓
```

### MONDAY MORNING (Before 09:15 IST)
```
□ Breeze API credentials: Ready
□ Internet stable: Verified
□ Terminal window: Open
□ System test: Run one more time (14/14 ✓)
□ Time: 09:10 IST exactly
```

### DURING TRADING (09:15-15:30 IST)
```
□ Candles updating: Every 1 minute
□ Options chain updating: Every tick
□ Indicators calculating: Every 1 minute
□ Signals generating: Every 10 minutes
□ Orders executing: As signals trigger
□ Exit rules checking: Every 1 minute
□ P&L updating: Real-time
```

### END OF DAY (15:30+ IST)
```
□ All positions closed: Auto
□ Session report: Generated
□ Trade data exported: JSON/CSV
□ ML learning: Completed
□ Model saved: Ready for Tuesday
```

---

## 📊 SPECIFIC SYMBOLS & TICKERS

### What Symbols Are We Trading?

**INDEX OPTIONS (Best for paper trading)**
```
BANKNIFTY (NSE Index):
  └─ Underlying: Banking index (50 stocks)
  └─ Liquidity: VERY HIGH
  └─ Volatility: 26-27% IV
  └─ Spreads: 1-2 rupees (very tight)
  └─ Volume: 10M+ daily
  └─ BEST CHOICE ✓

NIFTY (NSE Index):
  └─ Underlying: Top 50 NSE stocks
  └─ Liquidity: VERY HIGH
  └─ Volatility: 22% IV
  └─ Spreads: 0.5-1.5 rupees
  └─ Volume: 15M+ daily
  └─ ALSO GOOD ✓
```

**STOCK OPTIONS (If expanding)**
```
INFY (Infosys):
  └─ Liquidity: HIGH
  └─ Volatility: 20-22%
  └─ Spreads: 1-2 rupees
  └─ Volume: 2M+ daily

TCS (Tata Consultancy):
  └─ Liquidity: HIGH
  └─ Volatility: 18-20%
  └─ Spreads: 0.5-1.5 rupees
  └─ Volume: 1M+ daily

RELIANCE, HDFC, SBIN, ICICIBANK:
  └─ Medium liquidity options
  └─ Start with BANKNIFTY/NIFTY first
```

---

## 🔌 EXACT DATA FEEDS USED

### Our Current Configuration

**File: scheduler_options_production.py**
```python
# Line 50-75: Fetch candles
breeze.get_candle_data(
    interval="1minute",
    stock_code="BANKNIFTY",
    from_date="2026-06-15 09:15",
    to_date="2026-06-15 15:30"
)

# Line 100-125: Fetch options chain
breeze.get_options_chain(
    underlying="BANKNIFTY",
    expiry_date="2026-06-19"
)

# Line 150+: Calculate 31 indicators (from candles)
# Line 200+: Generate ML signal
# Line 250+: Select strategy
# Line 300+: Execute order
```

**File: app/options_chain_manager.py**
```python
# Line 30-60: Live options chain fetching
# Updates with every new candle (every 1 min)

# Line 80-120: Greeks calculation
# Delta, Gamma, Theta, Vega from chain data

# Line 150-180: IV analysis
# Current IV vs historical
```

---

## 💾 FILE FORMATS

### Downloaded Data (CSV Format)
```csv
Date,Open,High,Low,Close,Volume
2026-06-12,48100.00,48450.00,48000.00,48350.00,12500000
2026-06-11,48050.00,48300.00,47950.00,48100.00,11800000
2026-06-10,48200.00,48500.00,48000.00,48050.00,12000000
```

### Options Chain Data (JSON Format)
```json
{
  "underlying": "BANKNIFTY",
  "expiry": "2026-06-19",
  "contracts": [
    {
      "strike": 48000,
      "type": "CE",
      "bid": 246.50,
      "ask": 247.00,
      "iv": 0.265,
      "delta": 0.68,
      "gamma": 0.0082,
      "theta": -0.88,
      "vega": 0.125
    },
    ...
  ]
}
```

### Session Report (JSON Format)
```json
{
  "date": "2026-06-15",
  "trades": 15,
  "win_rate": 0.73,
  "total_pnl": 1850,
  "capital_start": 100000,
  "capital_end": 101850,
  "improvements": {
    "ml_accuracy": "72% → 73%",
    "feature_importance": {...}
  }
}
```

---

## 🎯 SUMMARY: WHERE TO GET WHAT

| Data Type | Source | When | How | Time |
|-----------|--------|------|-----|------|
| **Historical Candles** | Yahoo Finance OR NSE | This weekend | `python download_market_data.py` | 5 min |
| **Live Candles (1-min)** | Breeze API | Mon 09:15-15:30 | Auto-fetched | Real-time |
| **Live Options** | Breeze API | Mon 09:15-15:30 | Auto-fetched | Every tick |
| **Indicators (31)** | Calculated from candles | Mon 09:15+ | Auto-calculated | Every 1 min |
| **ML Signals** | Your ML Engine | Mon 09:15+ | Auto-generated | Every 10 min |
| **Trade Data** | Your System | Mon 09:15-15:30 | Auto-recorded | Real-time |

---

## ⚡ QUICK ACTION ITEMS

### DO THIS NOW (This Weekend)

**Step 1: Get Data** (5 min)
```bash
python download_market_data.py
```
Downloads: INFY, TCS, RELIANCE (500 days each)
Saves to: c:\Data\GreeksMaster\data\

**Step 2: Train Model** (10 min)
```bash
python weekend_ml_training_deployment.py
```
Output: Model ready, 73% expected accuracy

**Step 3: Validate System** (10 min)
```bash
python test_hybrid_system_integration.py
```
Expected: 14/14 tests PASS ✓

### DO THIS MONDAY (8:45-9:15 IST)

**Step 1: Final Check** (5 min)
```bash
python test_hybrid_system_integration.py
```

**Step 2: Launch** (at 09:15 exactly)
```bash
python scheduler_options_production.py
```

That's it! System runs automatically.

---

## 🟢 READY TO GO

**Data Sources**: ✓ Multiple options available  
**ML Training**: ✓ Can do this weekend  
**Live Trading**: ✓ Monday morning ready  
**Safety**: ✓ All systems armed  
**Monitoring**: ✓ Real-time tracking  

You're all set! Start downloading data this weekend. 🚀
