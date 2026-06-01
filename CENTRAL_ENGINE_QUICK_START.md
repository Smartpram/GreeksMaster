"""
Central Engine Quick Start Guide
=================================

Getting the trading system up and running with the new orchestrator,
scheduler, and test suite.

Date: June 1, 2026
Version: 1.0.0
Status: Ready for Implementation
"""

# ==============================================================================
# QUICK REFERENCE
# ==============================================================================

## 1. FILE LOCATIONS

Core Components:
  app/engine/trading_engine.py          (750 lines) - Central orchestrator
  app/engine/scheduler.py               (400 lines) - Automated scheduler
  app/engine/__init__.py                (50 lines)  - Module exports
  
Tests:
  tests/test_trading_system_integration.py (700+ lines, 80+ tests)
  
Documentation:
  docs/CENTRAL_ENGINE_IMPLEMENTATION_GUIDE.md (Comprehensive design)


## 2. BASIC INITIALIZATION

Step 1: Ensure all pipeline components are available

    from app.services.stock_screener import StockScreener
    from app.strategies.strategy_regime_monitor import StrategyRegimeMonitor
    from app.strategies.profit_booking_manager import ProfitBookingManager
    from app.services.signal_executor import SignalExecutor, ExecutionMode
    from app.services.order_manager import OrderManager
    from app.services.risk_manager import RiskManager
    from app.services.live_position_tracker import LivePositionTracker
    from app.services.notifications import NotificationService
    from app.services.breeze_api_production import BreezeAPI

Step 2: Initialize all services

    # Get Breeze API
    breeze = BreezeAPI()
    
    # Stage 1: Screener
    screener = StockScreener(breeze_api=breeze)
    
    # Stage 2: Validators
    validator = ProductionValidator()  # or equivalent
    regime_monitor = StrategyRegimeMonitor()
    
    # Stage 3: Execution
    order_manager = OrderManager(breeze_api=breeze)
    executor = SignalExecutor(
        order_manager=order_manager,
        execution_mode=ExecutionMode.PAPER  # Start with paper
    )
    
    # Stage 4: Exit Management
    profit_manager = ProfitBookingManager()
    
    # Stage 5: Monitoring
    position_tracker = LivePositionTracker(breeze_api=breeze)
    notifications = NotificationService()
    
    # Risk Management
    risk_manager = RiskManager()

Step 3: Create the Trading Engine

    from app.engine import TradingEngine
    
    engine = TradingEngine(
        screener=screener,
        validator=validator,
        regime_monitor=regime_monitor,
        executor=executor,
        profit_manager=profit_manager,
        position_tracker=position_tracker,
        risk_manager=risk_manager,
        notifications=notifications
    )

Step 4: Create and start the Scheduler

    from app.engine import TradingScheduler
    
    scheduler = TradingScheduler(
        trading_engine=engine,
        cycle_interval_minutes=5,              # Run every 5 minutes
        start_time='09:15',                    # Market open
        end_time='15:30',                      # Market close
        timezone='Asia/Kolkata',               # IST
        enable_market_hours=True
    )
    
    scheduler.start()  # Runs in background thread

Step 5: Monitor execution

    # Get last cycle results
    last_cycle = engine.get_last_cycle_metrics()
    print(f"Signals: {last_cycle['signals_generated']}")
    print(f"Trades: {last_cycle['trades_executed']}")
    print(f"Status: {last_cycle['status']}")
    
    # Get statistics
    stats = engine.get_cycle_statistics()
    print(f"Total cycles: {stats['total_cycles']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")


## 3. MANUAL CYCLE EXECUTION (For Testing)

If you want to run a single cycle manually (without scheduler):

    # Run one cycle
    result = engine.run_cycle()
    
    # Check result
    print(f"Cycle {result['cycle_id']}: {result['status']}")
    print(f"Duration: {result['duration_ms']:.2f}ms")
    print(f"Trades executed: {result['trades_executed']}")
    
    # Get detailed metrics
    metrics = engine.get_last_cycle_metrics()
    print(metrics['to_json()])  # Pretty-printed JSON


## 4. RUNNING TESTS

Run all tests:
    pytest tests/test_trading_system_integration.py -v

Run specific test class:
    pytest tests/test_trading_system_integration.py::TestStage1SignalGeneration -v

Run with coverage:
    pytest tests/test_trading_system_integration.py --cov=app.engine --cov-report=html

Run specific test:
    pytest tests/test_trading_system_integration.py::TestFullPipelineIntegration::test_complete_cycle_execution -v

Run performance tests only:
    pytest tests/test_trading_system_integration.py::TestPerformance -v


## 5. OPERATIONAL COMMANDS

Pause trading (keep scheduler running):
    scheduler.pause()
    # No new cycles will execute

Resume trading:
    scheduler.resume()
    # Cycles resume

Check scheduler status:
    status = scheduler.get_status()
    print(f"Status: {status['status']}")
    print(f"Is running: {status['is_running']}")
    print(f"Cycles executed: {status['cycles_executed']}")
    print(f"Last cycle: {status['last_cycle_time']}")

Get scheduler metrics:
    metrics = scheduler.get_metrics()
    print(f"Execution rate: {metrics['execution_rate']:.1f}%")
    print(f"Avg cycle time: {metrics['avg_cycle_time_ms']:.2f}ms")

Stop scheduler gracefully:
    scheduler.stop()
    # Waits for current cycle to finish, then stops


## 6. ERROR HANDLING & CIRCUIT BREAKERS

Daily Loss Limit Breached:
    # Automatic: halt_flag set to True
    # Automatic: No new cycles scheduled
    # Action: scheduler.reset_halt() then scheduler.resume()

Cycle Execution Failed:
    result = engine.run_cycle()
    if result['status'] == 'failed':
        print(f"Errors: {result['errors']}")
        # Debug the specific error and retry

Trading Engine Halted:
    if engine.halt_flag:
        print("Trading halted due to risk breach")
        engine.reset_halt()  # Clear halt
        engine.resume_trading()  # Or call scheduler.resume()


## 7. MONITORING & DIAGNOSTICS

Get cycle history (last N cycles):
    history = engine.get_cycle_history(limit=20)
    for cycle in history:
        print(f"{cycle['cycle_id']}: {cycle['status']} ({cycle['duration_ms']:.0f}ms)")
        print(f"  Signals: {cycle['signals_generated']}")
        print(f"  Trades: {cycle['trades_executed']}")
        print(f"  Portfolio: {cycle['portfolio_value']:.2f}")

Get aggregate statistics:
    stats = engine.get_cycle_statistics()
    print(f"Total cycles: {stats['total_cycles']}")
    print(f"Total signals: {stats['total_signals']}")
    print(f"Total trades: {stats['total_trades']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
    print(f"Avg cycle time: {stats['avg_cycle_time_ms']:.2f}ms")
    print(f"Halt status: {stats['halt_status']}")

Monitor memory usage (example script):
    import psutil
    import time
    
    process = psutil.Process()
    
    for i in range(100):
        result = engine.run_cycle()
        mem_mb = process.memory_info().rss / (1024 * 1024)
        print(f"Cycle {i}: {result['status']} - Memory: {mem_mb:.1f}MB")
        time.sleep(1)


## 8. CONFIGURATION

Key Configuration Options:

    # Cycle interval
    TRADING_CYCLE_INTERVAL_MINUTES=5        # Default
    
    # Market hours (IST)
    TRADING_START_TIME=09:15
    TRADING_END_TIME=15:30
    TRADING_TIMEZONE=Asia/Kolkata
    
    # Risk limits
    MAX_DAILY_LOSS=0.10                     # 10% of capital
    MAX_POSITION_SIZE=0.05                  # 5% of capital
    DEFAULT_STOP_LOSS=0.04                  # 4%
    DEFAULT_TARGET=0.06                     # 6%
    
    # Execution mode
    EXECUTION_MODE=PAPER                    # PAPER, SEMI_AUTO, AUTO
    
    # Notification settings
    ENABLE_EMAIL_ALERTS=true
    ENABLE_TELEGRAM_ALERTS=true
    ALERT_RECIPIENTS=user@example.com


## 9. INTEGRATION WITH FLASK APP

Example integration in Flask app:

    from flask import Flask
    from app.engine import TradingEngine, TradingScheduler
    
    app = Flask(__name__)
    
    # Initialize engine and scheduler at app startup
    engine = None
    scheduler = None
    
    @app.before_first_request
    def init_trading():
        global engine, scheduler
        
        # [Initialize all components...]
        
        engine = TradingEngine(...)
        scheduler = TradingScheduler(engine)
        scheduler.start()
    
    @app.route('/api/trading/status', methods=['GET'])
    def get_trading_status():
        return {
            'scheduler': scheduler.get_status(),
            'engine': {
                'last_cycle': engine.get_last_cycle_metrics(),
                'statistics': engine.get_cycle_statistics()
            }
        }
    
    @app.route('/api/trading/pause', methods=['POST'])
    def pause_trading():
        scheduler.pause()
        return {'status': 'paused'}
    
    @app.route('/api/trading/resume', methods=['POST'])
    def resume_trading():
        scheduler.resume()
        return {'status': 'resumed'}
    
    @app.teardown_appcontext
    def shutdown_trading(exception):
        if scheduler:
            scheduler.stop()


## 10. NEXT STEPS

Immediate (Next 1-2 Hours):
  1. Review this quick start guide
  2. Review CENTRAL_ENGINE_IMPLEMENTATION_GUIDE.md
  3. Examine trading_engine.py code
  4. Examine scheduler.py code
  5. Read test file for usage examples

Short Term (Next 3-5 Days):
  1. Run tests locally (pytest)
  2. Test engine with mocked components
  3. Test scheduler with mocked engine
  4. Verify performance targets met
  5. Deploy to staging environment

Medium Term (Next 1-2 Weeks):
  1. Integrate with real Breeze API
  2. Run paper trading with real data
  3. Monitor for 1 week
  4. Gather metrics and performance data
  5. Deploy to production

Long Term (Ongoing):
  1. Monitor system daily
  2. Tune performance based on metrics
  3. Add new indicators/screeners as needed
  4. Improve risk management rules
  5. Expand to more trading strategies


## 11. TROUBLESHOOTING

Q: Engine won't initialize
A: Ensure all components (screener, executor, etc.) are properly imported
   and available. Check logs for missing dependencies.

Q: Scheduler not running cycles
A: 1. Check if market hours (if enabled)
   2. Check if halt flag is set
   3. Check logs for exceptions
   4. Verify engine.run_cycle() works manually

Q: Cycles taking too long
A: 1. Profile each stage to identify bottleneck
   2. Check Breeze API latency
   3. Consider enabling parallel processing
   4. Check for missing cache optimization

Q: Tests failing
A: 1. Check all mock components are properly configured
   2. Run individual test for details
   3. Check Python/library versions
   4. Verify imports work

Q: Memory growing continuously
A: 1. Check cycle history retention size
   2. Look for resource leaks in components
   3. Profile with memory_profiler
   4. Restart system if needed


## 12. PERFORMANCE TARGETS

Expected Performance (per cycle):

    Stage 1 (Signal Generation):   100-500ms
    Stage 2 (Validation):          100-300ms
    Stage 3 (Execution):           500ms-2s (API dependent)
    Stage 4 (Exit Management):     100-300ms
    Stage 5 (Monitoring):          50-100ms
    ─────────────────────────────
    Total Cycle:                   1-3 seconds typical
                                   < 5 seconds maximum

Memory:
    Baseline:                      50-100MB
    Per 1000 cycles:               0MB (no leaks)
    Cycle history (100 cycles):    ~5MB

Success Rate:
    Cycle completion:              >99%
    No overlapping executions:     100%
    Risk gates working:            100%


## 13. QUICK DIAGNOSTICS SCRIPT

    # Save as: diagnose_system.py
    
    from app.engine import TradingEngine, TradingScheduler
    
    def diagnose():
        print("Trading System Diagnostic Report")
        print("=" * 50)
        
        # Test 1: Engine initialization
        try:
            engine = TradingEngine(...)
            print("✓ Engine initialized successfully")
        except Exception as e:
            print(f"✗ Engine initialization failed: {e}")
            return
        
        # Test 2: Single cycle execution
        try:
            result = engine.run_cycle()
            print(f"✓ Cycle executed: {result['status']}")
            print(f"  Signals: {result['signals_generated']}")
            print(f"  Trades: {result['trades_executed']}")
            print(f"  Duration: {result['duration_ms']:.0f}ms")
        except Exception as e:
            print(f"✗ Cycle execution failed: {e}")
            return
        
        # Test 3: Scheduler initialization
        try:
            scheduler = TradingScheduler(engine)
            print("✓ Scheduler initialized successfully")
        except Exception as e:
            print(f"✗ Scheduler initialization failed: {e}")
            return
        
        # Test 4: Check statistics
        stats = engine.get_cycle_statistics()
        print(f"✓ Statistics available:")
        print(f"  Total cycles: {stats['total_cycles']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        
        print("\nSystem is ready for trading!")
    
    if __name__ == '__main__':
        diagnose()


---

For complete details, see: docs/CENTRAL_ENGINE_IMPLEMENTATION_GUIDE.md
For code examples, see: tests/test_trading_system_integration.py
For API reference, see: app/engine/trading_engine.py
"""
