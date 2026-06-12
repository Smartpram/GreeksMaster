#!/usr/bin/env python3
"""
ENHANCED SIGNAL CONFIRMATION - CODE SNIPPETS
Ready-to-use code blocks for common integration scenarios
"""

CODE_SNIPPETS = """

╔════════════════════════════════════════════════════════════════════════════╗
║              ENHANCED SIGNAL - READY-TO-USE CODE SNIPPETS                 ║
║                                                                          ║
║             Copy-paste code blocks for common integration tasks           ║
╚════════════════════════════════════════════════════════════════════════════╝


█████ SNIPPET 1: BASIC INITIALIZATION █████

Purpose: Initialize enhanced signal system in your backtest
Location: In BacktestEngine.__init__ or run() method

COPY THIS:
──────────

from app.strategies.enhanced_signal_confirmation import EnhancedSignalConfirmation

# After fetching historical data:
df = self.fetch_historical_data(symbol, start_date, end_date)

# Initialize enhanced signals
self.enhanced_signals = EnhancedSignalConfirmation(df)

logger.info("✓ Enhanced signal system initialized")


█████ SNIPPET 2: ENTRY WITH VALIDATION █████

Purpose: Check entry signal validity before entering trade
Replace in: Your entry logic (usually around line 165-215)

COPY THIS:
──────────

# Check if enhanced system recommends this entry
validation = self.enhanced_signals.validate_entry_signal(bar_count, signal_type='LONG')

if validation['valid']:
    logger.info(f"✓ Entry Valid | Score: {validation['overall_score']:.2f} | "
                f"Regime: {validation['regime'].value}")
    
    # Get regime-specific parameters
    strategy_mode = self.enhanced_signals.get_strategy_mode(bar_count)
    
    # Calculate position size based on regime
    position_size = strategy_mode['position_sizing']  # 0.5 to 1.0x
    shares = int(capital * 0.95 * position_size / current_price)
    
    # Create position
    position = {
        'entry_price': current_price,
        'shares': shares,
        'entry_date': idx,
        'validation_score': validation['overall_score'],
        'regime': validation['regime'].value,
        'target': current_price * (1 + strategy_mode['take_profit_pct']),
        'stop_loss': current_price * (1 - strategy_mode['stop_loss_pct']),
    }
    
    # Record entry
    trades.append({
        'symbol': symbol,
        'entry_date': idx,
        'entry_price': current_price,
        'shares': shares,
        'entry_reason': 'Enhanced signal validation',
        'validation_components': validation['scores'],
    })

else:
    logger.debug(f"✗ Entry Rejected | Score: {validation['overall_score']:.2f}")
    logger.debug(f"  Reasons: {validation['reasons']}")


█████ SNIPPET 3: EXIT WITH RECOMMENDATIONS █████

Purpose: Use enhanced system for exit decisions
Replace in: Your exit logic (usually around line 220-280)

COPY THIS:
──────────

elif position is not None:
    pnl = current_price - position['entry_price']
    pnl_pct = (pnl / position['entry_price']) * 100
    
    # Get exit recommendations from enhanced system
    recommendations = self.enhanced_signals.get_position_recommendations(
        bar_count, 
        position
    )
    
    # Use regime-adapted targets and stops
    target = position.get('target', position['entry_price'] * 1.02)
    stop = position.get('stop_loss', position['entry_price'] * 0.99)
    
    # Check exit conditions
    should_exit = (
        current_price >= target or                    # Hit profit target
        current_price <= stop or                      # Hit stop loss
        recommendations.get('should_exit', False)    # Signal-based exit
    )
    
    if should_exit:
        exit_reason = (
            'profit_target' if current_price >= target else
            'stop_loss' if current_price <= stop else
            recommendations.get('exit_triggers', ['signal_based'])[0]
        )
        
        # Record trade exit
        trade_result = {
            'symbol': symbol,
            'exit_date': idx,
            'exit_price': current_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'holding_days': (idx - position['entry_date']).days,
            'exit_reason': exit_reason,
        }
        
        # Calculate metrics
        total_pnl += pnl
        trades_closed += 1
        if pnl > 0:
            winning_trades += 1
        
        logger.info(f"EXIT {symbol}: {exit_reason} | P&L: {pnl_pct:+.2f}%")
        
        position = None


█████ SNIPPET 4: REGIME DETECTION ONLY █████

Purpose: Use only regime detection (simplest use case)
Location: Anywhere you want to know current market regime

COPY THIS:
──────────

from app.strategies.enhanced_signal_confirmation import EnhancedSignalConfirmation, MarketRegime

esc = EnhancedSignalConfirmation(df)

# Get current regime
regime = esc.detect_regime(bar_index)

print(f"Current regime: {regime.value}")

# Adapt strategy based on regime
if regime == MarketRegime.STRONG_UPTREND:
    position_size = 1.0
    take_profit = 0.05  # 5% target
    stop_loss = 0.02    # 2% stop
    
elif regime in [MarketRegime.UPTREND, MarketRegime.MILD_UPTREND]:
    position_size = 0.7
    take_profit = 0.03
    stop_loss = 0.015
    
elif regime == MarketRegime.SIDEWAYS:
    position_size = 0.5
    take_profit = 0.02  # Smaller targets in range
    stop_loss = 0.01
    
elif regime == MarketRegime.STRONG_DOWNTREND:
    position_size = 0.0  # No longs
    # Consider short instead
    
else:  # Downtrend regimes
    position_size = 0.3
    take_profit = 0.02
    stop_loss = 0.01


█████ SNIPPET 5: MULTI-INDICATOR CHECK █████

Purpose: Check individual indicators without full validation
Location: For debugging or custom logic

COPY THIS:
──────────

from app.strategies.enhanced_signal_confirmation import TechnicalIndicators

# Calculate indicators at specific bar
bar_idx = 50
adx = TechnicalIndicators.calculate_adx(df, bar_idx)
rsi = TechnicalIndicators.calculate_rsi(df, bar_idx)
macd_line, macd_signal, macd_hist = TechnicalIndicators.calculate_macd(df, bar_idx)
bb_upper, bb_mid, bb_lower = TechnicalIndicators.calculate_bollinger_bands(df, bar_idx)
atr = TechnicalIndicators.calculate_atr(df, bar_idx)

print(f"ADX: {adx:.2f}")
print(f"RSI: {rsi:.2f}")
print(f"MACD: {macd_line:.4f} (signal: {macd_signal:.4f})")
print(f"Bollinger Bands: {bb_lower:.2f} | {bb_mid:.2f} | {bb_upper:.2f}")
print(f"ATR: {atr:.2f}")

# Combine for custom logic
if adx > 25 and rsi > 50 and macd_line > macd_signal:
    logger.info("Strong uptrend conditions detected")


█████ SNIPPET 6: PARAMETER OPTIMIZATION █████

Purpose: Test different validation thresholds
Location: Run in separate script for sensitivity analysis

COPY THIS:
──────────

from app.strategies.enhanced_signal_confirmation import EnhancedSignalConfirmation
import json

# Test different thresholds
thresholds_to_test = [0.50, 0.55, 0.60, 0.65, 0.70]
results = {}

for threshold in thresholds_to_test:
    valid_count = 0
    score_sum = 0
    
    esc = EnhancedSignalConfirmation(df)
    
    for bar_idx in range(20, len(df)):
        validation = esc.validate_entry_signal(bar_idx, 'LONG')
        score_sum += validation['overall_score']
        
        if validation['overall_score'] >= threshold:
            valid_count += 1
    
    pass_rate = (valid_count / (len(df) - 20)) * 100
    avg_score = score_sum / (len(df) - 20)
    
    results[f'threshold_{threshold}'] = {
        'pass_rate_pct': pass_rate,
        'avg_score': avg_score,
        'valid_bars': valid_count,
    }
    
    print(f"Threshold {threshold}: {pass_rate:.1f}% pass rate, avg score {avg_score:.2f}")

# Save results
with open('threshold_sensitivity_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)


█████ SNIPPET 7: VALIDATION TEST RUNNER █████

Purpose: Run comprehensive validation on your data
Location: Standalone script

COPY THIS:
──────────

from app.strategies.signal_validation_tester import run_comprehensive_validation
from app.strategies.breeze_api_service import BreezeAPIService
import json
from datetime import datetime

# Fetch data
breeze = BreezeAPIService()
breeze.authenticate()

symbols = ['RELIND', 'TCS', 'INFY']
all_results = {}

for symbol in symbols:
    print(f"\\nValidating {symbol}...")
    
    df = breeze.fetch_historical_data(
        stock_code=symbol,
        exchange_code='NSE',
        interval='day',
        product_type='cash'
    )
    
    if df is None or df.empty:
        print(f"  ✗ No data for {symbol}")
        continue
    
    # Run tests
    results = run_comprehensive_validation(df)
    all_results[symbol] = results
    
    print(f"  ✓ Tests complete")

# Save results
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f'validation_results_{timestamp}.json'

with open(output_file, 'w') as f:
    json.dump(all_results, f, indent=2)

print(f"\\n✓ All validation complete. Results saved to {output_file}")


█████ SNIPPET 8: BACKTEST COMPARISON HELPER █████

Purpose: Compare baseline vs enhanced backtest results
Location: After running both backtests

COPY THIS:
──────────

import json
import pandas as pd

baseline_file = 'baseline_results.txt'
enhanced_file = 'enhanced_results.txt'

def extract_metrics(filename):
    metrics = {}
    with open(filename, 'r') as f:
        content = f.read()
        
    # Parse metrics from output (adjust parsing based on your format)
    for line in content.split('\\n'):
        if 'Total Return' in line:
            metrics['return'] = float(line.split(':')[1].strip().rstrip('%'))
        elif 'Win Rate' in line:
            metrics['win_rate'] = float(line.split(':')[1].strip().rstrip('%'))
        elif 'Sharpe' in line:
            metrics['sharpe'] = float(line.split(':')[1].strip())
        elif 'Max Drawdown' in line:
            metrics['max_dd'] = float(line.split(':')[1].strip().rstrip('%'))
    
    return metrics

# Extract metrics
baseline = extract_metrics(baseline_file)
enhanced = extract_metrics(enhanced_file)

# Compare
print("\\n" + "="*60)
print("BASELINE vs ENHANCED COMPARISON")
print("="*60)
print(f"\\n{'Metric':<20} {'Baseline':>15} {'Enhanced':>15} {'Change':>15}")
print("-"*60)

for key in baseline.keys():
    b_val = baseline.get(key, 0)
    e_val = enhanced.get(key, 0)
    change = e_val - b_val
    
    metric_name = key.replace('_', ' ').title()
    print(f"{metric_name:<20} {b_val:>15.2f} {e_val:>15.2f} {change:>+15.2f}")

print("="*60)


█████ SNIPPET 9: LOGGING SETUP █████

Purpose: Add detailed logging for debugging
Location: At top of your backtest file

COPY THIS:
──────────

import logging
from logging.handlers import RotatingFileHandler
import sys

# Create logger
logger = logging.getLogger('EnhancedBacktest')
logger.setLevel(logging.DEBUG)

# File handler (detailed)
fh = RotatingFileHandler(
    'backtest_detailed.log',
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5
)
fh.setLevel(logging.DEBUG)

# Console handler (summary)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# Add handlers
logger.addHandler(fh)
logger.addHandler(ch)

# Test
logger.info("✓ Logging initialized")
logger.debug("This goes to file only")


█████ SNIPPET 10: ERROR HANDLING █████

Purpose: Gracefully handle edge cases
Location: Wrap around validation calls

COPY THIS:
──────────

try:
    validation = self.enhanced_signals.validate_entry_signal(bar_count, 'LONG')
    
    if validation is None:
        logger.warning(f"Validation returned None at bar {bar_count}")
        skip_entry = True
    elif validation['valid']:
        # Process entry
        pass
    else:
        logger.debug(f"Entry rejected at bar {bar_count}")
        
except Exception as e:
    logger.error(f"Error in validation at bar {bar_count}: {str(e)}")
    logger.exception("Full traceback:")
    skip_entry = True


█████ SNIPPET 11: SIMPLE DASHBOARD █████

Purpose: Print summary stats during backtest
Location: In backtest loop at regular intervals (every N bars)

COPY THIS:
──────────

# Print status every 50 bars
if bar_count % 50 == 0 and bar_count > 0:
    print(f"\\n{'='*60}")
    print(f"Progress: Bar {bar_count}/{len(df)} ({(bar_count/len(df)*100):.1f}%)")
    print(f"{'='*60}")
    print(f"Regime:        {self.enhanced_signals.detect_regime(bar_count).value}")
    print(f"Current Price: {current_price:.2f}")
    print(f"Position:      {'OPEN' if position else 'CLOSED'}")
    print(f"Trades:        {len(trades)} total, {sum(1 for t in trades if t.get('pnl', 0) > 0)} wins")
    print(f"Total P&L:     {total_pnl:+.2f}")
    print(f"{'='*60}\\n")


█████ SNIPPET 12: BATCH TESTING MULTIPLE SYMBOLS █████

Purpose: Run backtest on multiple symbols sequentially
Location: Wrapper script

COPY THIS:
──────────

import subprocess
import json
from datetime import datetime

symbols = ['RELIND', 'TCS', 'INFY', 'HDFC']
results_summary = {}

print("Starting batch backtest run...")
print(f"Symbols to test: {symbols}")
print()

for symbol in symbols:
    print(f"Processing {symbol}...", end=' ', flush=True)
    
    # Run backtest (you'll need to modify this based on your actual script)
    result = subprocess.run(
        ['python', 'backtest_with_breeze_real_data.py', f'--symbol={symbol}'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ Complete")
        # Parse results from result.stdout
        results_summary[symbol] = {
            'status': 'success',
            'output': result.stdout[-500:]  # Last 500 chars
        }
    else:
        print("✗ Failed")
        results_summary[symbol] = {
            'status': 'failed',
            'error': result.stderr[-500:]
        }

# Save summary
with open(f'batch_results_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.json', 'w') as f:
    json.dump(results_summary, f, indent=2)

print()
print("Batch run complete!")


═══════════════════════════════════════════════════════════════════════════════

USAGE GUIDE:

1. Pick the snippet that matches your need
2. Copy the code from the COPY THIS section
3. Paste into your Python file
4. Modify variable names to match your context
5. Run and test


COMMON CUSTOMIZATIONS:

Change validation threshold:
  threshold = 0.60  # Default
  threshold = 0.50  # More lenient (more trades)
  threshold = 0.70  # More strict (fewer trades)

Change position sizing:
  position_size = 1.0              # Full size
  position_size = 0.5              # Half size
  position_size = int(account * x) # Fixed amount

Change take-profit target:
  take_profit = 0.02  # 2%
  take_profit = 0.05  # 5%
  target = entry_price * (1 + take_profit)

Change stop-loss:
  stop_loss = 0.01    # 1%
  stop_loss = 0.03    # 3%
  stop = entry_price * (1 - stop_loss)


═══════════════════════════════════════════════════════════════════════════════
"""

if __name__ == '__main__':
    print(CODE_SNIPPETS)
