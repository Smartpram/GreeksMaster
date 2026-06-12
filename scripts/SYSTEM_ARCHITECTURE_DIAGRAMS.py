#!/usr/bin/env python3
"""
ENHANCED SIGNAL CONFIRMATION - ARCHITECTURE & DATA FLOW
Visual representations of system components and their interactions
"""

ARCHITECTURE_DIAGRAMS = """

╔════════════════════════════════════════════════════════════════════════════╗
║              ENHANCED SIGNAL SYSTEM - ARCHITECTURE DIAGRAMS               ║
║                                                                          ║
║              Visual guide to system components and data flow              ║
╚════════════════════════════════════════════════════════════════════════════╝


█████ DIAGRAM 1: SYSTEM COMPONENT HIERARCHY █████

                           BACKTEST ENGINE
                                 │
                 ┌─────────────────┼─────────────────┐
                 │                 │                 │
         MARKET DATA FLOW    SIGNAL SYSTEM      RISK MANAGEMENT
         (OHLCV Bars)       (NEW SYSTEM)       (Position Sizing)
                 │                 │                 │
                 │                 ▼                 │
                 │        ┌─────────────────┐        │
                 └───────▶│  ENHANCED SIGNAL│◀───────┘
                          │  CONFIRMATION   │
                          └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
             ENTRY LOGIC    EXIT LOGIC    REGIME MODE
          (Allow/Reject)  (Timing/Price)  (Adapt Params)


█████ DIAGRAM 2: VALIDATION SCORING SYSTEM █████

INPUT: Current bar data (OHLCV)
            │
            ▼
    ┌───────────────────────────────────────┐
    │  COMPONENT 1: REGIME (20%)            │
    │  Check: Price vs 50/200 MA alignment  │
    │  Output: 0.0-1.0 score               │
    └───────────────────────────────────────┘
            │
            ▼
    ┌───────────────────────────────────────┐
    │  COMPONENT 2: ADX (20%)               │
    │  Check: Trend strength magnitude      │
    │  Output: 0.0-1.0 score               │
    └───────────────────────────────────────┘
            │
            ▼
    ┌───────────────────────────────────────┐
    │  COMPONENT 3: RSI (15%)               │
    │  Check: Momentum zone                 │
    │  Output: 0.0-1.0 score               │
    └───────────────────────────────────────┘
            │
            ▼
    ┌───────────────────────────────────────┐
    │  COMPONENT 4: MACD (15%)              │
    │  Check: Momentum divergence           │
    │  Output: 0.0-1.0 score               │
    └───────────────────────────────────────┘
            │
            ▼
    ┌───────────────────────────────────────┐
    │  COMPONENT 5: VOLUME (15%)            │
    │  Check: Relative volume strength      │
    │  Output: 0.0-1.0 score               │
    └───────────────────────────────────────┘
            │
            ▼
    ┌───────────────────────────────────────┐
    │  COMPONENT 6: VOLATILITY (15%)        │
    │  Check: ATR volatility regime         │
    │  Output: 0.0-1.0 score               │
    └───────────────────────────────────────┘
            │
            ▼
    ┌───────────────────────────────────────┐
    │  COMPOSITE SCORER                     │
    │  = 0.20×c1 + 0.20×c2 + 0.15×c3 +     │
    │    0.15×c4 + 0.15×c5 + 0.15×c6       │
    │  Output: 0.0-1.0 final score         │
    └───────────────────────────────────────┘
            │
            ▼
    ┌───────────────────────────────────────┐
    │  THRESHOLD CHECK                      │
    │  if score >= 0.60 → VALID             │
    │  else             → INVALID           │
    └───────────────────────────────────────┘
            │
            ▼
        OUTPUT: {
            'valid': bool,
            'overall_score': 0.0-1.0,
            'regime': MarketRegime,
            'scores': {6 components},
            'reasons': [list of explanations]
        }


█████ DIAGRAM 3: MARKET REGIME CLASSIFICATION █████

                      CURRENT BAR DATA
                            │
                            ▼
            ┌───────────────────────────────┐
            │  Calculate Key Indicators:    │
            │  • ADX (trend strength)       │
            │  • Price vs MA50/MA200        │
            │  • DI+ vs DI- (directional)   │
            └───────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
      ADX > 25?        Price > MA?      +DI > -DI?
            │               │               │
    ┌───────┴───────┐       │               │
    │               │       │               │
   YES              NO      │               │
    │               │       │               │
    │           (ADX ≤ 25)  │               │
    │               │       │               │
    │               ▼       │               │
    │        [SIDEWAYS]     │               │
    │        (if price≈MA)  │               │
    │               │       │               │
    ▼               ▼       ▼               ▼
[STRONG        [MILD      [MILD/DOWN    [BULLISH/
 UPTREND]      UPTREND]   TREND]         BEARISH]
 (if +DI>-DI)  (weak      (weak            (check
               trend)     momentum)        +DI/-DI)


REGIME OUTCOMES (8 States):
─────────────────────────────
┌──────────────────────────┬──────────┬─────────┬──────────┐
│ Regime                   │ ADX      │ Price   │ DI+/-    │
├──────────────────────────┼──────────┼─────────┼──────────┤
│ STRONG_UPTREND          │ > 25     │ > MA    │ DI+>DI-  │
│ UPTREND                 │ > 20     │ > MA    │ any      │
│ MILD_UPTREND            │ < 20     │ > MA    │ any      │
│ SIDEWAYS                │ < 20     │ ≈ MA    │ any      │
│ MILD_DOWNTREND          │ < 20     │ < MA    │ any      │
│ DOWNTREND               │ > 20     │ < MA    │ any      │
│ STRONG_DOWNTREND        │ > 25     │ < MA    │ DI->DI+  │
│ [UNDEFINED]             │ unusual  │ unusual │ unusual  │
└──────────────────────────┴──────────┴─────────┴──────────┘


█████ DIAGRAM 4: STRATEGY MODES BY REGIME █████

REGIME                  → STRATEGY MODE
────────────────────────────────────────

STRONG_UPTREND         → TREND_LONG
├─ Position sizing:       1.0x (full)
├─ Take-profit target:    7% (maximize upside)
├─ Stop-loss:             2% (wide stop)
└─ Avg trade duration:    7+ days

UPTREND                → TREND_LONG
├─ Position sizing:       1.0x
├─ Take-profit target:    5%
├─ Stop-loss:             2%
└─ Avg trade duration:    5-7 days

MILD_UPTREND           → MILD_LONG
├─ Position sizing:       0.7x (reduced)
├─ Take-profit target:    3%
├─ Stop-loss:             1.5%
└─ Avg trade duration:    4-5 days

SIDEWAYS               → RANGE_MODE
├─ Position sizing:       0.5x (cautious)
├─ Take-profit target:    2%
├─ Stop-loss:             1%
└─ Avg trade duration:    2-3 days

MILD_DOWNTREND         → MILD_SHORT
├─ Position sizing:       0.3x (very small)
├─ Take-profit target:    2%
├─ Stop-loss:             1%
└─ Avg trade duration:    2-3 days

DOWNTREND              → NO_ENTRY / SHORT
├─ Position sizing:       0.0x (no longs)
├─ Alternative:           SHORT mode
├─ Stop-loss:             2%
└─ Avg trade duration:    varies

STRONG_DOWNTREND       → NO_ENTRY / SHORT
├─ Position sizing:       0.0x (no longs)
├─ Alternative:           TREND_SHORT
├─ Take-profit target:    7%
├─ Stop-loss:             2%
└─ Avg trade duration:    7+ days


█████ DIAGRAM 5: DATA FLOW THROUGH BACKTEST █████

                    ┌──────────────┐
                    │ BACKTEST     │
                    │ INITIALIZATION
                    └──────┬───────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │ Load historical OHLCV data   │
            │ (from Breeze API or file)    │
            └──────────┬───────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │ Initialize Enhanced Signal System│
        │ esc = EnhancedSignalConfirmation │
        └──────────┬──────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────┐
    │ BACKTEST LOOP: for bar_idx in dataframe │
    └──────────────────┬──────────────────────┘
                       │
                       ▼
            ┌─────────────────────────────┐
            │ 1. Calculate base indicators│
            │ (MA20, RSI, etc)            │
            └──────────┬──────────────────┘
                       │
                       ├─────── IF POSITION IS CLOSED ─────────┐
                       │                                       │
                       ▼                                       │
        ┌──────────────────────────────┐                      │
        │ Check base entry conditions  │                      │
        │ (e.g., price > MA20)         │                      │
        └──────────┬───────────────────┘                      │
                   │                                          │
                   ▼                                          │
        ┌──────────────────────────────┐                      │
        │ Call enhanced validation:    │                      │
        │ validation =                 │                      │
        │ esc.validate_entry_signal()  │                      │
        └──────────┬───────────────────┘                      │
                   │                                          │
        ┌──────────┴──────────┐                               │
        │                     │                               │
       YES                     NO                              │
   validation              (skip entry)                       │
    .valid?                     │                             │
        │                       │                             │
        ▼                       │                             │
    ┌────────────────────┐      │                             │
    │ Get strategy mode: │      │                             │
    │ mode =             │      │                             │
    │ esc.get_strategy   │      │                             │
    │ _mode()            │      │                             │
    └────────┬───────────┘      │                             │
             │                  │                             │
             ▼                  │                             │
    ┌────────────────────┐      │                             │
    │ Create position:   │      │                             │
    │ • Size by mode     │      │                             │
    │ • Target by mode   │      │                             │
    │ • Stop by mode     │      │                             │
    └────────┬───────────┘      │                             │
             │                  │                             │
             ▼                  │                             │
    ┌────────────────────┐      │                             │
    │ Record trade entry │      │                             │
    └────────┬───────────┘      │                             │
             │                  │                             │
             └─────────┬────────┘                             │
                       │                                      │
                       ├─────── IF POSITION IS OPEN ─────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │ Calculate position P&L       │
        │ current_pnl_pct = (current - │
        │ entry_price) / entry_price   │
        └──────────┬───────────────────┘
                   │
                   ▼
        ┌──────────────────────────────┐
        │ Get exit recommendations:    │
        │ recs = esc.get_position      │
        │ _recommendations()           │
        └──────────┬───────────────────┘
                   │
        ┌──────────┴──────────────────┐
        │                             │
    P&L at     P&L at              Exit signal
    target?    stop?               triggered?
        │         │                   │
       YES       YES                 YES
        │         │                   │
        └────┬────┴───────────┬───────┘
             │                │
             ▼                │
    ┌──────────────────────┐ │
    │ Record trade exit    │ │
    │ • Close position     │ │
    │ • Calculate P&L      │ │
    │ • Update metrics     │ │
    └──────────┬───────────┘ │
               │              │
               └──────┬───────┘
                      │
                      ▼
        ┌──────────────────────────────┐
        │ Move to next bar             │
        │ (end of loop)                │
        └──────────┬───────────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │ After loop: Generate report  │
    │ • Total P&L                  │
    │ • Win rate                   │
    │ • Sharpe ratio               │
    │ • Drawdown                   │
    └──────────────────────────────┘


█████ DIAGRAM 6: INDICATOR CALCULATION CHAIN █████

Each technical indicator depends on prior calculations:

RAW MARKET DATA
      │
      ├─────────────────────────┬──────────────────┬──────────────┐
      │                         │                  │              │
      ▼                         ▼                  ▼              ▼
   CLOSE PRICES            HIGH/LOW PRICES    VOLUME DATA      OPEN PRICES
      │                         │                  │              │
      │                         │                  │              │
      ├──────────┐              │                  │              │
      │          │              │                  │              │
      ▼          ▼              │                  │              │
    MA50      MA200             │                  │              │
      │          │              │                  │              │
      │          │              │                  │              │
      ├──────────┴──────────┐   │                  │              │
      │                     │   │                  │              │
      ▼                     ▼   │                  │              │
   RSI (14)              TRUE RANGE               │              │
      │                     │   │                  │              │
      │                     ▼   │                  │              │
      │                    ATR (14)                │              │
      │                     │                     │              │
      ├──────────────┬──────┴──────┬──────────────┼─────┐        │
      │              │             │              │     │        │
      ▼              ▼             ▼              ▼     ▼        │
    EMA12         EMA26          DI+/DI-      VOLUME/   │        │
      │              │             │           MA20    │        │
      │              │             ▼             │     │        │
      │              │            ADX            ├─────┴─┐      │
      │              │             │             │       │      │
      ├──────────┬───┴──────────┐   │             ▼       ▼      │
      │          │              │   │          RVOL      VWAP    │
      ▼          ▼              ▼   │          (Vol Ratio)│     │
    MACD      MACD SIGNAL    MACD HIST         │         │      │
      │          │              │              │         │      │
      └────┬─────┴──────────┬───┘              │         │      │
           │                │                  │         │      │
           ▼                ▼                  ▼         ▼      ▼
    ┌──────────────────────────────────────────────────────────┐
    │         BOLLINGER BANDS (BB_UPPER, BB_MID, BB_LOWER)    │
    │         Uses: MA20 + 2 * StdDev(close, 20)              │
    └──────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
     COMPONENT:         COMPONENT:         COMPONENT:
     ADX+DI             RSI (14)             MACD
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
                 ┌─────────────────────────┐
                 │  VALIDATION SCORING     │
                 │  (6 components)         │
                 └─────────────────────────┘


█████ DIAGRAM 7: TEST EXECUTION PIPELINE █████

Entry Point:
──────────
    run_comprehensive_validation(df, symbols_data)
            │
            ├─────────────────────────┬─────────────────┬─────────┬───────────┐
            │                         │                 │         │           │
            ▼                         ▼                 ▼         ▼           ▼
        TEST 1:             TEST 2:         TEST 3:     TEST 4: TEST 5:    TEST 6:
        Regime              ADX             Entry       Regime  Component  Multi-
        Distribution        Sensitivity     Signal      Specific Ablation  Symbol
        Analysis            Analysis        Quality     Perf.   (Weights)  Validation
            │                   │               │         │        │          │
            ├─ Count bars   ├─ Test 15    ├─ Sample    ├─ Group ├─ For each├─ For each
            │  by regime    │  Test 20    │  50 bars   │  trades  component: symbol:
            │  │            │  Test 25    │  by regime │  by     │  - Calc  │  - Calc
            │  │            │  Test 30    │  measure   │  regime │   score  │   score
            │  │            │  count bars │  stats     │  measure│   w/o    │   measure
            │  │            │  in trend   │  (pass%)   │  win%   │   comp   │   pass%
            │  │            │  for each   │            │         │   - Note │   compare
            │  │            │  threshold  │            │         │   diff   │   across
            │  │            │             │            │         │          │
            ▼  ▼            ▼             ▼            ▼         ▼          ▼
        ┌──────────┐   ┌──────────┐  ┌──────────┐ ┌──────┐  ┌──────┐   ┌──────┐
        │Results 1 │   │Results 2 │  │Results 3 │ │Result│  │Result│   │Result│
        │Regime    │   │ADX       │  │Entry Sig │ │4     │  │5     │   │6     │
        │Dist      │   │Threshold │  │Quality   │ │Regime│  │Ablat │   │Multi │
        │Analysis  │   │Sensitivity   │Stats    │ │Spec  │  │Test  │   │Sym   │
        └────┬─────┘   └────┬─────┘  └────┬────┘ └──┬───┘  └──┬───┘   └──┬───┘
             │              │             │         │        │         │
             └──────────────┼─────────────┴─────────┴────────┴─────────┘
                            │
                            ▼
                   ┌─────────────────────┐
                   │ AGGREGATE RESULTS   │
                   │ (All 6 tests)       │
                   └─────────┬───────────┘
                             │
                             ▼
                   ┌─────────────────────┐
                   │ CREATE JSON OUTPUT  │
                   │ validation_results  │
                   │ _YYYYMMDD_HHMMSS    │
                   │ .json               │
                   └─────────┬───────────┘
                             │
                             ▼
                   ┌─────────────────────┐
                   │ GENERATE REPORT     │
                   │ (Human-readable)    │
                   └─────────────────────┘


█████ DIAGRAM 8: INTEGRATION POINT IN BACKTEST █████

EXISTING BACKTEST CODE:
──────────────────────

    def run(self):
        df = self.fetch_historical_data()
        
        for idx, row in df.iterrows():
            price = row['close']
            ma20 = calculate_ma20(df, idx)
            rsi = calculate_rsi(df, idx)
            
            if position is None and price > ma20 and rsi < 70:
                # Entry
                position = {'entry_price': price}
            
            elif position and price > position['entry_price'] * 1.02:
                # Exit
                position = None


WITH ENHANCED SYSTEM:
────────────────────

    def run(self):
        df = self.fetch_historical_data()
        
        # NEW: Initialize enhanced system
        from app.strategies.enhanced_signal_confirmation import EnhancedSignalConfirmation
        esc = EnhancedSignalConfirmation(df)
        
        for bar_count, (idx, row) in enumerate(df.iterrows()):
            price = row['close']
            ma20 = calculate_ma20(df, idx)
            rsi = calculate_rsi(df, idx)
            
            if position is None and price > ma20 and rsi < 70:
                # NEW: Validate with enhanced system
                validation = esc.validate_entry_signal(bar_count, 'LONG')
                
                if validation['valid']:
                    # MODIFIED: Use regime-specific parameters
                    mode = esc.get_strategy_mode(bar_count)
                    position = {
                        'entry_price': price,
                        'target': price * (1 + mode['take_profit_pct']),
                        'stop': price * (1 - mode['stop_loss_pct']),
                    }
            
            elif position:
                # NEW: Use enhanced exit recommendations
                recs = esc.get_position_recommendations(bar_count, position)
                
                if (price > position['target'] or 
                    price < position['stop'] or 
                    recs.get('should_exit')):
                    position = None


█████ DIAGRAM 9: PERFORMANCE COMPARISON VIEW █████

BASELINE vs ENHANCED (Expected Results)

WIN RATE IMPROVEMENT:
┌────────────────────────────────────────────────────────┐
│                                                        │
│ Baseline:     ▒▒▒▒▒▒▒▒ 43.75%                        │
│ Enhanced:     ▒▒▒▒▒▒▒▒▒▒▒▒ 50-55%                   │
│                                                        │
│ Gain: +5-15% (fewer low-quality trades)              │
└────────────────────────────────────────────────────────┘

SHARPE RATIO IMPROVEMENT:
┌────────────────────────────────────────────────────────┐
│                                                        │
│ Baseline:    -0.77 ███                               │
│ Enhanced:    -0.20 ██                                │
│              +0.30 █  (best case)                   │
│                                                        │
│ Gain: +0.5-1.0 (better risk-adjusted returns)        │
└────────────────────────────────────────────────────────┘

MAX DRAWDOWN IMPROVEMENT:
┌────────────────────────────────────────────────────────┐
│                                                        │
│ Baseline:     -15% ▒▒▒▒▒                            │
│ Enhanced:     -11% ▒▒▒                              │
│               -9%  ▒▒  (best case)                 │
│                                                        │
│ Reduction: -2 to -4% (better downside control)      │
└────────────────────────────────────────────────────────┘


█████ DIAGRAM 10: ROLLBACK & RECOVERY PATHS █████

SCENARIO 1: ENHANCED SYSTEM PERFORMS POORLY
───────────────────────────────────────────

Enhanced backtest shows:
├─ Win rate DECREASED
├─ Sharpe ratio NEGATIVE
└─ Drawdown INCREASED

Recovery Path:
├─ Step 1: Disable exit logic (keep entry only)
│          → Re-run backtest to isolate problem
│
├─ Step 2: If improved → Entry logic is issue
│          └─ Debug: Review validation test results
│          └ Check: Do rejected trades match bad trades?
│          └ Fix: Adjust weights, thresholds
│
├─ Step 3: If unchanged → Exit logic is issue
│          └─ Debug: Review exit recommendations
│          └ Check: Are exits too aggressive/passive?
│          └ Fix: Adjust position recommendation logic
│
└─ Step 4: Last resort
           └─ Rollback to baseline: cp .backup backtest_with_breeze_real_data.py
           └ Run with simple regime detection only (safest approach)


SCENARIO 2: SYSTEM CRASHES OR ERRORS
─────────────────────────────────────

Error message shows:
├─ AttributeError, KeyError, or similar
├─ NaN values in calculations
└─ Data shape mismatch

Recovery Path:
├─ Step 1: Check data quality
│          └ python -c "df.info(); print(df.head())"
│
├─ Step 2: Verify minimum data length
│          └ Require at least 50 bars (should have 168)
│
├─ Step 3: Test indicator calculations separately
│          └ Try single indicator at a time
│
├─ Step 4: Add error handling
│          └ Wrap validation calls in try/except
│
└─ Step 5: If persistent
           └ Simplify: Disable advanced indicators
           └ Use: Regime detection only
           └ Fallback: Baseline strategy


SCENARIO 3: OVERFITTING DETECTED
────────────────────────────────

Walk-forward test shows:
├─ In-sample Sharpe +0.80
├─ Out-of-sample Sharpe +0.10
└─ Inconsistency > ±5% across periods

Recovery Path:
├─ Step 1: Reduce model complexity
│          └ Use fewer components (disable volume, volatility)
│          └ Simplify: Use only regime + ADX
│
├─ Step 2: Relax thresholds
│          └ Lower validation threshold (0.60 → 0.55)
│          └ Widen ADX ranges
│
├─ Step 3: Use larger dataset
│          └ Include more historical data if available
│          └ Test on fresh data (pre-Sep 2025)
│
└─ Step 4: Document findings
           └ Record what caused overfitting
           └ Update approach for next optimization


═══════════════════════════════════════════════════════════════════════════════

KEY TAKEAWAYS:

1. System adds 6 validation layers on top of existing entry logic
2. Each layer contributes 15-20% to final decision
3. Regime detection enables strategy adaptation
4. Multiple validation components reduce false signals
5. Testing framework validates all assumptions
6. Clear paths for debugging and optimization


═══════════════════════════════════════════════════════════════════════════════
"""

if __name__ == '__main__':
    print(ARCHITECTURE_DIAGRAMS)
