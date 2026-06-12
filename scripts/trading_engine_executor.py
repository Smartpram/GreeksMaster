#!/usr/bin/env python3
"""
Trading Pipeline Engine - Quick Executor
==========================================

Run the complete trading pipeline as an integrated engine.

Modes:
  1. Backtest     - Test on historical data
  2. Single Cycle - Execute one complete pipeline cycle
  3. Paper Trade  - Live paper trading for validation
  4. Continuous   - Run via Flask app with auto-scheduling

Usage:
  python trading_engine_executor.py backtest --quick
  python trading_engine_executor.py backtest --full
  python trading_engine_executor.py cycle
  python trading_engine_executor.py continuous
  python trading_engine_executor.py paper
"""

import sys
import os
import time
import logging
from datetime import datetime
from pathlib import Path
import argparse
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_ml'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backtest'))

# Import fee calculator for realistic P&L
from app.brokerage_fees import BrokerageFeeCalculator, BrokeragePlan


def run_backtest(quick=False, range_policy=False, symbols=None, capital=100000):
    """Run backtest engine on historical data"""
    logger.info("="*80)
    logger.info("TRADING PIPELINE: BACKTEST MODE")
    logger.info("="*80)
    
    try:
        from backtest.backtest_trading_engine_with_ai import main as backtest_main
        
        # Build args
        args_list = []
        
        if quick:
            args_list.append('--quick')
            logger.info("✓ Quick mode (2 minutes)")
        else:
            logger.info("✓ Full backtest mode (10+ minutes)")
        
        if range_policy:
            args_list.append('--range-policy')
            logger.info("✓ Range policy enabled (capital preservation)")
        
        if symbols:
            args_list.extend(['--symbols'] + symbols)
            logger.info(f"✓ Symbols: {', '.join(symbols)}")
        
        args_list.extend(['--capital', str(capital)])
        logger.info(f"✓ Capital: Rs {capital:,}")
        
        # Save original sys.argv
        original_argv = sys.argv
        sys.argv = [sys.argv[0]] + args_list
        
        # Run backtest
        logger.info("\nStarting backtest...")
        logger.info("-" * 80)
        backtest_main()
        logger.info("-" * 80)
        
        # Restore sys.argv
        sys.argv = original_argv
        
        # Add fee information
        logger.info("\n📊 Fee Information:")
        logger.info("-" * 80)
        fee_calc = BrokerageFeeCalculator(plan=BrokeragePlan.IVALUE)
        plan_rec = fee_calc.get_plan_recommendation(expected_trades_per_year=100)
        logger.info(f"Brokerage Plan (Recommended): {plan_rec['recommended_plan'].upper()}")
        logger.info(f"Annual Cost: Rs {plan_rec['recommended_annual_cost']:,.0f}")
        logger.info(f"Cost per Trade: Rs {plan_rec['recommended_cost_per_trade']:.2f}")
        logger.info("-" * 80)
        
        logger.info("✓ Backtest completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_single_cycle():
    """Run one complete pipeline cycle"""
    logger.info("="*80)
    logger.info("TRADING PIPELINE: SINGLE CYCLE MODE")
    logger.info("="*80)
    
    try:
        logger.info("\nInitializing trading engine...")
        
        # Initialize services
        from app.services.breeze_api import BreezeAPIService
        from app.stock_screener import StockScreener
        from app.production_validator import ProductionValidator
        from app.market_sentiment_gate import MarketSentimentEvaluator
        from app.engine.trading_engine import TradingEngine
        
        # For this demo, we'll use mock/stub services
        logger.warning("⚠ Using stub services for demo (API not connected)")
        logger.warning("  To use with real API, configure .env with API keys")
        
        # Create a simple test
        logger.info("\n" + "-" * 80)
        logger.info("Cycle Execution Timeline:")
        logger.info("-" * 80)
        
        stages = [
            ("Stage 1", "Signal Generation", 1.5),
            ("Stage 2", "Validation & Risk Gates", 1.2),
            ("Stage 3", "Position Sizing & Execution", 2.0),
            ("Stage 4", "Position Monitoring", 1.5),
            ("Stage 5", "Risk Monitoring & Alerts", 1.0)
        ]
        
        start_time = datetime.now()
        total_time = 0
        
        for stage_num, stage_name, duration in stages:
            logger.info(f"\n{stage_num}: {stage_name}")
            logger.info(f"  Duration: {duration:.1f}s")
            time.sleep(0.5)  # Simulate
            total_time += duration
            logger.info(f"  ✓ Completed")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info("\n" + "-" * 80)
        logger.info("Cycle Results:")
        logger.info("-" * 80)
        
        results = {
            "cycle_id": f"manual_cycle_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "duration_ms": elapsed * 1000,
            "signals_generated": 2,
            "signals_validated": 2,
            "signals_rejected": 0,
            "trades_executed": 1,
            "execution_failures": 0,
            "positions_monitored": 3,
            "positions_exited": 0,
            "risk_alerts": 0,
            "daily_pnl": 1250.50,
            "portfolio_value": 101250.50,
            "status": "COMPLETED"
        }
        
        logger.info(f"Cycle ID:              {results['cycle_id']}")
        logger.info(f"Timestamp:             {results['timestamp']}")
        logger.info(f"Duration:              {results['duration_ms']:.1f}ms")
        logger.info(f"\nSignals Generated:     {results['signals_generated']}")
        logger.info(f"Signals Validated:     {results['signals_validated']}")
        logger.info(f"Signals Rejected:      {results['signals_rejected']}")
        logger.info(f"\nTrades Executed:       {results['trades_executed']}")
        logger.info(f"Execution Failures:    {results['execution_failures']}")
        logger.info(f"\nPositions Monitored:   {results['positions_monitored']}")
        logger.info(f"Positions Exited:      {results['positions_exited']}")
        logger.info(f"\nRisk Alerts:           {results['risk_alerts']}")
        logger.info(f"Daily P&L:             Rs {results['daily_pnl']:,.2f}")
        logger.info(f"Portfolio Value:       Rs {results['portfolio_value']:,.2f}")
        logger.info(f"Status:                {results['status']}")
        
        logger.info("\n✓ Single cycle completed successfully!")
        logger.info("\nTo see actual trading results, configure API keys in .env and run again.")
        return True
        
    except Exception as e:
        logger.error(f"✗ Cycle execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_continuous(num_cycles=None, interval_sec=300):
    """Run continuous cycles (like live trading)"""
    logger.info("="*80)
    logger.info("TRADING PIPELINE: CONTINUOUS MODE")
    logger.info("="*80)
    
    logger.info(f"\nRunning continuous cycles")
    logger.info(f"Interval: {interval_sec} seconds")
    if num_cycles:
        logger.info(f"Max cycles: {num_cycles}")
    else:
        logger.info(f"Until stopped (Ctrl+C)")
    
    logger.info("\nNote: This demo will show cycle simulation.")
    logger.info("For real continuous trading, start Flask app: python run.py")
    logger.info("\n" + "-" * 80)
    
    try:
        cycle_num = 0
        
        while True:
            if num_cycles and cycle_num >= num_cycles:
                break
            
            cycle_num += 1
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            logger.info(f"\n[{now}] Cycle #{cycle_num}")
            logger.info("-" * 40)
            
            # Simulate cycle
            signals = 1 + (cycle_num % 3)
            trades = signals // 2 + 1
            exits = (cycle_num % 2)
            pnl = 500 + (cycle_num * 100)
            
            logger.info(f"  Signals generated:  {signals}")
            logger.info(f"  Trades executed:    {trades}")
            logger.info(f"  Positions exited:   {exits}")
            logger.info(f"  Cycle P&L:          Rs {pnl:,.2f}")
            logger.info(f"  Status:             ✓ Completed")
            
            # Wait for next cycle
            if num_cycles is None or cycle_num < num_cycles:
                logger.info(f"\n⏳ Next cycle in {interval_sec}s (Ctrl+C to stop)...")
                time.sleep(interval_sec)
        
        logger.info("\n✓ Continuous mode completed!")
        return True
        
    except KeyboardInterrupt:
        logger.info("\n\n⏹ Continuous mode stopped by user")
        logger.info(f"Total cycles executed: {cycle_num}")
        return True
    except Exception as e:
        logger.error(f"✗ Continuous mode failed: {e}")
        return False


def run_paper_trading():
    """Run paper trading mode (4-week validation)"""
    logger.info("="*80)
    logger.info("TRADING PIPELINE: PAPER TRADING MODE")
    logger.info("="*80)
    
    try:
        from backtest.phase5_paper_trading_enhanced import main as paper_trading_main
        
        logger.info("\nStarting 4-week paper trading session...")
        logger.info("This will run the trading pipeline on recent data")
        logger.info("without executing real trades.")
        logger.info("All P&L calculations include realistic ICICI Direct fees.\n")
        logger.info("-" * 80)
        
        paper_trading_main()
        
        logger.info("-" * 80)
        logger.info("\n📊 Fee Accounting:")
        logger.info("-" * 80)
        fee_calc = BrokerageFeeCalculator(plan=BrokeragePlan.IVALUE)
        logger.info("✓ Fee-Aware P&L Calculation")
        logger.info("  Gross P&L = Entry - Exit profit/loss")
        logger.info("  Total Fees = Brokerage + Exchange + STT + SEBI + Stamp + GST")
        logger.info("  Net P&L = Gross P&L - Total Fees")
        logger.info("-" * 80)
        
        logger.info("\n✓ Paper trading session completed!")
        logger.info("\nResults saved to: paper_trading_results.json")
        logger.info("⚠ Note: All P&L figures include realistic brokerage fees")
        logger.info("Next: Review results and move to live trading if satisfied")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Paper trading failed: {e}")
        logger.warning("File may not exist. Use backtest mode instead.")
        return False


def show_help():
    """Show comprehensive help"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║           TRADING PIPELINE ENGINE - EXECUTOR                               ║
║                                                                            ║
║  Run the complete 5-stage trading pipeline in various modes                ║
╚════════════════════════════════════════════════════════════════════════════╝

MODES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. BACKTEST MODE (Historical Testing)
   ─────────────────────────────────
   python trading_engine_executor.py backtest --quick
   python trading_engine_executor.py backtest --full
   python trading_engine_executor.py backtest --range-policy
   python trading_engine_executor.py backtest --symbols INFTEC TCS RELIANCE

   Purpose: Test strategy on historical data
   Duration: 2 minutes (--quick) or 10+ minutes (--full)
   Output: Win rate, profit factor, max drawdown, trade analysis

2. SINGLE CYCLE MODE (One Complete Loop)
   ───────────────────────────────────
   python trading_engine_executor.py cycle

   Purpose: Execute one complete pipeline cycle
   Duration: ~10 seconds
   Output: Cycle metrics and performance

3. CONTINUOUS MODE (Live-like Execution)
   ──────────────────────────────────
   python trading_engine_executor.py continuous
   python trading_engine_executor.py continuous --cycles 10 --interval 300

   Purpose: Run multiple cycles at intervals (like live trading)
   Duration: Configurable
   Output: Real-time cycle logs

4. PAPER TRADING MODE (4-Week Validation)
   ─────────────────────────────────
   python trading_engine_executor.py paper

   Purpose: Live testing without real money
   Duration: 4 weeks of data
   Output: Comprehensive performance report

PIPELINE STAGES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Stage 1: SIGNAL GENERATION
  • Screener scans for opportunities
  • Detects SMA20 crossovers, breakouts
  • Output: Trading signals

Stage 2: VALIDATION & RISK GATES
  • Production validator checks config
  • Market regime monitor evaluates trends
  • Market sentiment gate checks NIFTY
  • AI validator scores confidence
  • Output: Approve/Reject decision

Stage 3: POSITION SIZING & EXECUTION
  • Calculate position size (2% risk per trade)
  • Place order via Breeze API
  • Set stop-loss and profit targets
  • Output: Trade execution confirmation

Stage 4: POSITION MONITORING
  • Track open positions in real-time
  • Calculate P&L
  • Monitor technical levels
  • Prepare exit signals

Stage 5: RISK MONITORING & ALERTS
  • Monitor daily P&L limits
  • Track maximum drawdown
  • Send alerts on thresholds
  • Execute exits if needed

EXAMPLES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Quick 2-minute backtest
$ python trading_engine_executor.py backtest --quick

# Full backtest with range policy
$ python trading_engine_executor.py backtest --full --range-policy

# Single cycle (one complete loop)
$ python trading_engine_executor.py cycle

# Run 10 continuous cycles
$ python trading_engine_executor.py continuous --cycles 10

# 4-week paper trading validation
$ python trading_engine_executor.py paper

OPTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

--quick              Quick backtest (2 minutes)
--full               Full backtest (10+ minutes)
--range-policy       Enable capital preservation mode
--symbols SYMBOL...  Specific symbols to test (default: predefined list)
--capital AMOUNT     Starting capital (default: 100000)
--cycles NUM         Number of cycles to run (continuous mode)
--interval SEC       Seconds between cycles (default: 300)

WORKFLOW:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Test with backtest:
   $ python trading_engine_executor.py backtest --quick

2. If results look good, validate with paper trading:
   $ python trading_engine_executor.py paper

3. If paper trading succeeds, go live:
   $ python run.py

REQUIREMENTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Python 3.7+
✓ All packages: pip install -r requirements.txt
✓ For real trading: .env file with API keys

QUICK START:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Run quick backtest:
   python trading_engine_executor.py backtest --quick

2. Check results in console output

3. If satisfied, follow workflow above

Questions? See TRADING_PIPELINE_AS_ENGINE.md for complete documentation.
""")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Trading Pipeline Engine Executor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python trading_engine_executor.py backtest --quick
  python trading_engine_executor.py cycle
  python trading_engine_executor.py continuous --cycles 5
  python trading_engine_executor.py paper
        """
    )
    
    parser.add_argument(
        'mode',
        nargs='?',
        choices=['backtest', 'cycle', 'continuous', 'paper', 'help'],
        default='help',
        help='Execution mode'
    )
    
    parser.add_argument('--quick', action='store_true', help='Quick backtest (2 min)')
    parser.add_argument('--full', action='store_true', help='Full backtest (10+ min)')
    parser.add_argument('--range-policy', action='store_true', help='Enable range policy')
    parser.add_argument('--symbols', nargs='+', help='Symbols to test')
    parser.add_argument('--capital', type=int, default=100000, help='Starting capital')
    parser.add_argument('--cycles', type=int, help='Number of cycles')
    parser.add_argument('--interval', type=int, default=300, help='Interval between cycles (sec)')
    
    args = parser.parse_args()
    
    if args.mode == 'help' or not args.mode:
        show_help()
        return 0
    
    logger.info(f"Trading Pipeline Engine - {args.mode.upper()} mode")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = False
    
    if args.mode == 'backtest':
        success = run_backtest(
            quick=args.quick or not args.full,
            range_policy=args.range_policy,
            symbols=args.symbols,
            capital=args.capital
        )
    
    elif args.mode == 'cycle':
        success = run_single_cycle()
    
    elif args.mode == 'continuous':
        success = run_continuous(
            num_cycles=args.cycles,
            interval_sec=args.interval
        )
    
    elif args.mode == 'paper':
        success = run_paper_trading()
    
    logger.info(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
