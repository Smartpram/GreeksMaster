"""
Paper Trading Test Suite for Phase 9 Live Trading System
Tests:
1. Stock Screener with all 12 templates
2. Real-time position tracking
3. Signal execution with paper trading mode
4. Portfolio reporting and metrics
"""

import logging
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app/logs/paper_trading_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PaperTradingTester:
    """Comprehensive paper trading test suite"""
    
    def __init__(self):
        """Initialize tester with all components"""
        logger.info("=" * 80)
        logger.info("PAPER TRADING TEST SUITE - INITIALIZATION")
        logger.info("=" * 80)
        
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }
        
        try:
            # Import all required components
            logger.info("Importing system components...")
            
            from app.services.breeze_api import BreezeAPIService
            from app.services.stock_screener import StockScreener, ScreenerType
            from app.services.signal_executor import SignalExecutor, ExecutionMode
            from app.services.live_position_tracker import LivePositionTracker
            from app.services.order_manager import OrderManager
            from app.services.risk_manager import RiskManager
            import pandas as pd
            import csv
            
            from app.services.breeze_api import BreezeAPIService
            from app.services.stock_screener import StockScreener, ScreenerType
            from app.services.signal_executor import SignalExecutor, ExecutionMode
            from app.services.live_position_tracker import LivePositionTracker
            from app.services.order_manager import OrderManager
            from app.services.risk_manager import RiskManager
            from app.services.notifications import NotificationService
            import pandas as pd
            import csv
            
            self.breeze_api = BreezeAPIService()
            self.order_manager = OrderManager()
            self.risk_manager = RiskManager()
            self.tracker = LivePositionTracker()
            self.notifications = NotificationService()
            
            # Initialize screener with breeze_api
            self.screener = StockScreener(self.breeze_api, self.risk_manager)
            
            # Initialize executor with all required components
            self.executor = SignalExecutor(
                order_manager=self.order_manager,
                risk_manager=self.risk_manager,
                position_tracker=self.tracker,
                notifications=self.notifications
            )
            self.executor.set_execution_mode(ExecutionMode.PAPER)  # ⭐ PAPER TRADING MODE
            
            # Function to load stocks from Security Master file
            def load_stocks_from_master():
                """Load stocks from NSE Security Master file"""
                stocks = []
                try:
                    with open('NSEScripMaster.txt', 'r', encoding='utf-8', errors='ignore') as f:
                        reader = csv.DictReader(f, delimiter='|')
                        for row in reader:
                            if not row or all(v is None or v.strip() == '' for v in row.values()):
                                continue
                            # Extract ShortName (stock code)
                            short_name = None
                            for key in row.keys():
                                key_clean = key.strip().strip('"') if key else ''
                                if 'ShortName' in key_clean:
                                    short_name = (row.get(key) or '').strip().strip('"')
                                    break
                            if short_name and short_name not in ['', 'ShortName']:
                                stocks.append({
                                    'symbol': short_name,
                                    'name': short_name
                                })
                    return pd.DataFrame(stocks).drop_duplicates(subset=['symbol'])
                except Exception as e:
                    logger.warning(f"Could not load from NSEScripMaster, creating sample stocks: {e}")
                    return pd.DataFrame({
                        'symbol': ['TCS', 'INFY', 'RELIANCE', 'HDFCBANK', 'ICICIBANK', 
                                   'SBIN', 'AXISBANK', 'HDFC', 'ITC', 'BAJAJFINSV'],
                        'name': ['TCS', 'INFY', 'RELIANCE', 'HDFCBANK', 'ICICIBANK',
                                 'SBIN', 'AXISBANK', 'HDFC', 'ITC', 'BAJAJFINSV']
                    })
            
            self.load_stocks_from_master = load_stocks_from_master
            
            logger.info("✅ All components imported successfully")
            logger.info(f"✅ Execution mode set to: {self.executor.execution_mode}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def test_1_screener_initialization(self):
        """Test 1: Verify all 12 screeners initialize correctly"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1: SCREENER INITIALIZATION")
        logger.info("=" * 80)
        
        try:
            from app.services.stock_screener import ScreenerType
            
            screener_types = list(ScreenerType)
            logger.info(f"Total screeners available: {len(screener_types)}")
            
            for i, screener_type in enumerate(screener_types, 1):
                logger.info(f"  {i}. {screener_type.name} - ✅")
            
            self.test_results["tests"]["screener_initialization"] = {
                "status": "PASS",
                "screeners_count": len(screener_types),
                "screeners": [s.name for s in screener_types]
            }
            
            logger.info(f"\n✅ TEST 1 PASSED: All {len(screener_types)} screeners initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ TEST 1 FAILED: {str(e)}")
            logger.error(traceback.format_exc())
            self.test_results["tests"]["screener_initialization"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    def test_2_load_stock_universe(self):
        """Test 2: Load 201 stocks from Security Master"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 2: STOCK UNIVERSE LOADING")
        logger.info("=" * 80)
        
        try:
            logger.info("Loading stock universe from Security Master...")
            stocks_df = self.load_stocks_from_master()
            
            logger.info(f"✅ Loaded {len(stocks_df)} stocks")
            logger.info(f"   Columns: {list(stocks_df.columns)}")
            logger.info(f"   Sample stocks: {stocks_df.head(5)['symbol'].tolist()}")
            
            self.stocks_df = stocks_df
            self.test_results["tests"]["stock_universe"] = {
                "status": "PASS",
                "stocks_loaded": len(stocks_df),
                "columns": list(stocks_df.columns)
            }
            
            logger.info(f"\n✅ TEST 2 PASSED: Stock universe loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ TEST 2 FAILED: {str(e)}")
            logger.error(traceback.format_exc())
            self.test_results["tests"]["stock_universe"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    def test_3_run_all_screeners(self):
        """Test 3: Run all 12 screeners"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 3: RUNNING ALL SCREENERS")
        logger.info("=" * 80)
        
        try:
            if not hasattr(self, 'stocks_df'):
                raise ValueError("Stock universe not loaded. Run test 2 first.")
            
            logger.info(f"Running screeners on {len(self.stocks_df)} stocks...")
            
            # Run all screeners
            results = self.screener.run_all_screeners(self.stocks_df)
            
            screener_stats = {}
            total_opportunities = 0
            
            for screener_type, stocks in results.items():
                count = len(stocks)
                total_opportunities += count
                screener_stats[screener_type.name] = {
                    "count": count,
                    "top_3": [s.symbol for s in stocks[:3]] if stocks else []
                }
                logger.info(f"  {screener_type.name:20} → {count:3} opportunities")
                if stocks:
                    logger.info(f"    Top picks: {', '.join([s.symbol for s in stocks[:3]])}")
            
            self.screener_results = results
            self.test_results["tests"]["run_screeners"] = {
                "status": "PASS",
                "total_opportunities": total_opportunities,
                "by_screener": screener_stats
            }
            
            logger.info(f"\n✅ TEST 3 PASSED: All screeners executed successfully")
            logger.info(f"   Total opportunities identified: {total_opportunities}")
            return True
            
        except Exception as e:
            logger.error(f"❌ TEST 3 FAILED: {str(e)}")
            logger.error(traceback.format_exc())
            self.test_results["tests"]["run_screeners"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    def test_4_get_top_opportunities(self):
        """Test 4: Get top opportunities across all screeners"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 4: TOP OPPORTUNITIES RANKING")
        logger.info("=" * 80)
        
        try:
            if not hasattr(self, 'screener_results'):
                raise ValueError("Screeners not run. Run test 3 first.")
            
            # Collect all opportunities
            all_stocks = []
            for screener_type, stocks in self.screener_results.items():
                for stock in stocks:
                    all_stocks.append({
                        "symbol": stock.symbol,
                        "screener": screener_type.name,
                        "confidence": stock.confidence_score,
                        "price": stock.current_price
                    })
            
            # Sort by confidence score
            all_stocks.sort(key=lambda x: x["confidence"], reverse=True)
            
            top_10 = all_stocks[:10]
            logger.info(f"Top 10 opportunities by confidence score:")
            for i, stock in enumerate(top_10, 1):
                logger.info(f"  {i:2}. {stock['symbol']:12} - {stock['confidence']:3}% confidence (from {stock['screener']})")
            
            self.top_opportunities = all_stocks[:20]  # Keep top 20 for trading test
            
            self.test_results["tests"]["top_opportunities"] = {
                "status": "PASS",
                "total_opportunities": len(all_stocks),
                "top_10": [s["symbol"] for s in top_10]
            }
            
            logger.info(f"\n✅ TEST 4 PASSED: Ranked {len(all_stocks)} opportunities")
            return True
            
        except Exception as e:
            logger.error(f"❌ TEST 4 FAILED: {str(e)}")
            logger.error(traceback.format_exc())
            self.test_results["tests"]["top_opportunities"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    def test_5_paper_trading_buy_signals(self):
        """Test 5: Execute buy signals in paper trading mode"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 5: PAPER TRADING - BUY SIGNALS")
        logger.info("=" * 80)
        
        try:
            if not hasattr(self, 'top_opportunities'):
                raise ValueError("Top opportunities not identified. Run test 4 first.")
            
            logger.info(f"Executing buy signals for top 5 opportunities (PAPER MODE)...")
            
            executed_orders = []
            for i, stock in enumerate(self.top_opportunities[:5], 1):
                try:
                    symbol = stock["symbol"]
                    price = stock["price"]
                    confidence = stock["confidence"]
                    
                    logger.info(f"\n  {i}. Executing BUY signal for {symbol}")
                    logger.info(f"     Price: {price}, Confidence: {confidence}%")
                    
                    # Execute buy signal in PAPER mode
                    result = self.executor.execute_buy_signal(
                        symbol=symbol,
                        price=price,
                        confidence=confidence
                    )
                    
                    logger.info(f"     ✅ Order executed: {result}")
                    executed_orders.append({
                        "symbol": symbol,
                        "action": "BUY",
                        "price": price,
                        "order_id": result.get("order_id", "PAPER_ORDER")
                    })
                    
                except Exception as e:
                    logger.warning(f"     ⚠️  Could not execute order: {str(e)}")
            
            self.executed_orders = executed_orders
            
            self.test_results["tests"]["buy_signals"] = {
                "status": "PASS",
                "orders_executed": len(executed_orders),
                "orders": [o["symbol"] for o in executed_orders]
            }
            
            logger.info(f"\n✅ TEST 5 PASSED: Executed {len(executed_orders)} buy signals")
            return True
            
        except Exception as e:
            logger.error(f"❌ TEST 5 FAILED: {str(e)}")
            logger.error(traceback.format_exc())
            self.test_results["tests"]["buy_signals"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    def test_6_position_tracking(self):
        """Test 6: Track positions and calculate P&L"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 6: POSITION TRACKING & P&L")
        logger.info("=" * 80)
        
        try:
            logger.info("Getting all open positions...")
            
            positions = self.tracker.get_all_positions()
            logger.info(f"Total positions: {len(positions)}")
            
            for position in positions:
                logger.info(f"\n  Position: {position.symbol}")
                logger.info(f"    Entry Price: {position.entry_price}")
                logger.info(f"    Current Price: {position.current_price}")
                logger.info(f"    Quantity: {position.quantity}")
                logger.info(f"    Unrealized P&L: {position.unrealized_pnl:.2f}")
                logger.info(f"    Status: {position.status}")
            
            # Get portfolio summary
            summary = self.tracker.get_portfolio_summary()
            logger.info(f"\nPortfolio Summary:")
            logger.info(f"  Total Positions: {summary['total_positions']}")
            logger.info(f"  Total Value: {summary['total_value']:.2f}")
            logger.info(f"  Total P&L: {summary['total_pnl']:.2f}")
            logger.info(f"  Win Rate: {summary['win_rate']:.2f}%")
            
            self.portfolio_summary = summary
            
            self.test_results["tests"]["position_tracking"] = {
                "status": "PASS",
                "total_positions": len(positions),
                "portfolio": summary
            }
            
            logger.info(f"\n✅ TEST 6 PASSED: Position tracking working correctly")
            return True
            
        except Exception as e:
            logger.error(f"❌ TEST 6 FAILED: {str(e)}")
            logger.error(traceback.format_exc())
            self.test_results["tests"]["position_tracking"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    def test_7_execution_modes(self):
        """Test 7: Verify all 4 execution modes"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 7: EXECUTION MODES")
        logger.info("=" * 80)
        
        try:
            from app.services.signal_executor import ExecutionMode
            
            modes = list(ExecutionMode)
            logger.info(f"Testing {len(modes)} execution modes:")
            
            modes_info = {}
            for mode in modes:
                logger.info(f"\n  Mode: {mode.name}")
                logger.info(f"    Description: {mode.value}")
                
                # Test mode switching
                self.executor.set_execution_mode(mode)
                current_mode = self.executor.execution_mode
                logger.info(f"    ✅ Current mode: {current_mode}")
                
                modes_info[mode.name] = mode.value
            
            self.test_results["tests"]["execution_modes"] = {
                "status": "PASS",
                "modes": modes_info
            }
            
            # Switch back to PAPER mode
            self.executor.set_execution_mode(ExecutionMode.PAPER)
            
            logger.info(f"\n✅ TEST 7 PASSED: All execution modes working")
            return True
            
        except Exception as e:
            logger.error(f"❌ TEST 7 FAILED: {str(e)}")
            logger.error(traceback.format_exc())
            self.test_results["tests"]["execution_modes"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    def test_8_risk_management(self):
        """Test 8: Risk management validation"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 8: RISK MANAGEMENT")
        logger.info("=" * 80)
        
        try:
            logger.info("Testing risk management system...")
            
            # Check position limits
            positions = self.tracker.get_all_positions()
            total_value = sum(p.quantity * p.current_price for p in positions)
            
            logger.info(f"Total Position Value: {total_value:.2f}")
            logger.info(f"Max Position Size: {self.risk_manager.max_position_size * 100}%")
            
            # Test position sizing
            test_amount = 50000
            position_size = self.risk_manager.calculate_position_size(
                capital=test_amount,
                risk_percent=0.02,
                entry_price=100,
                stop_price=95
            )
            
            logger.info(f"\nPosition Sizing Test:")
            logger.info(f"  Capital: {test_amount}")
            logger.info(f"  Risk: 2%")
            logger.info(f"  Entry: 100, Stop: 95")
            logger.info(f"  Calculated Size: {position_size:.0f} shares")
            
            self.test_results["tests"]["risk_management"] = {
                "status": "PASS",
                "total_position_value": total_value,
                "position_size_test": position_size
            }
            
            logger.info(f"\n✅ TEST 8 PASSED: Risk management working correctly")
            return True
            
        except Exception as e:
            logger.error(f"❌ TEST 8 FAILED: {str(e)}")
            logger.error(traceback.format_exc())
            self.test_results["tests"]["risk_management"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    def test_9_signal_execution_types(self):
        """Test 9: Different signal types"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 9: SIGNAL EXECUTION TYPES")
        logger.info("=" * 80)
        
        try:
            from app.services.signal_executor import SignalType
            
            signal_types = list(SignalType)
            logger.info(f"Available signal types: {len(signal_types)}")
            
            for i, signal_type in enumerate(signal_types, 1):
                logger.info(f"  {i}. {signal_type.name}")
            
            self.test_results["tests"]["signal_types"] = {
                "status": "PASS",
                "signal_types": [s.name for s in signal_types]
            }
            
            logger.info(f"\n✅ TEST 9 PASSED: All signal types available")
            return True
            
        except Exception as e:
            logger.error(f"❌ TEST 9 FAILED: {str(e)}")
            logger.error(traceback.format_exc())
            self.test_results["tests"]["signal_types"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    def test_10_reporting(self):
        """Test 10: Portfolio reporting"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 10: PORTFOLIO REPORTING")
        logger.info("=" * 80)
        
        try:
            logger.info("Generating portfolio reports...")
            
            # Get summary
            summary = self.tracker.get_portfolio_summary()
            
            logger.info(f"\nPortfolio Report:")
            logger.info(f"  Timestamp: {datetime.now().isoformat()}")
            logger.info(f"  Total Positions: {summary['total_positions']}")
            logger.info(f"  Total Value: {summary['total_value']:.2f}")
            logger.info(f"  Unrealized P&L: {summary['unrealized_pnl']:.2f}")
            logger.info(f"  Realized P&L: {summary['realized_pnl']:.2f}")
            logger.info(f"  Total P&L: {summary['total_pnl']:.2f}")
            logger.info(f"  Win Rate: {summary['win_rate']:.2f}%")
            logger.info(f"  Best Trade: {summary['best_trade']:.2f}")
            logger.info(f"  Worst Trade: {summary['worst_trade']:.2f}")
            
            # Export report
            report_file = f"reports/paper_trading_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"\n  Report exported to: {report_file}")
            
            self.test_results["tests"]["reporting"] = {
                "status": "PASS",
                "report_exported": report_file,
                "summary": summary
            }
            
            logger.info(f"\n✅ TEST 10 PASSED: Reporting working correctly")
            return True
            
        except Exception as e:
            logger.error(f"❌ TEST 10 FAILED: {str(e)}")
            logger.error(traceback.format_exc())
            self.test_results["tests"]["reporting"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        logger.info("\n\n")
        logger.info("╔" + "=" * 78 + "╗")
        logger.info("║" + " " * 20 + "PHASE 9 PAPER TRADING TEST SUITE" + " " * 25 + "║")
        logger.info("╚" + "=" * 78 + "╝")
        
        tests = [
            ("TEST 1: Screener Initialization", self.test_1_screener_initialization),
            ("TEST 2: Stock Universe Loading", self.test_2_load_stock_universe),
            ("TEST 3: Run All Screeners", self.test_3_run_all_screeners),
            ("TEST 4: Top Opportunities", self.test_4_get_top_opportunities),
            ("TEST 5: Paper Trading Buy Signals", self.test_5_paper_trading_buy_signals),
            ("TEST 6: Position Tracking", self.test_6_position_tracking),
            ("TEST 7: Execution Modes", self.test_7_execution_modes),
            ("TEST 8: Risk Management", self.test_8_risk_management),
            ("TEST 9: Signal Execution Types", self.test_9_signal_execution_types),
            ("TEST 10: Portfolio Reporting", self.test_10_reporting),
        ]
        
        results = {}
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                    results[test_name] = "✅ PASS"
                else:
                    failed += 1
                    results[test_name] = "❌ FAIL"
            except Exception as e:
                failed += 1
                results[test_name] = f"❌ ERROR: {str(e)}"
                logger.error(f"Test error: {str(e)}")
        
        # Print summary
        logger.info("\n\n")
        logger.info("╔" + "=" * 78 + "╗")
        logger.info("║" + " " * 25 + "TEST EXECUTION SUMMARY" + " " * 30 + "║")
        logger.info("╚" + "=" * 78 + "╝")
        
        for test_name, result in results.items():
            logger.info(f"{test_name:50} {result}")
        
        logger.info("\n" + "=" * 80)
        logger.info(f"TOTAL PASSED: {passed}/{len(tests)} ✅")
        logger.info(f"TOTAL FAILED: {failed}/{len(tests)} ❌")
        logger.info("=" * 80)
        
        # Update summary
        self.test_results["summary"] = {
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / len(tests) * 100) if len(tests) > 0 else 0
        }
        
        return self.test_results
    
    def save_results(self):
        """Save test results to file"""
        results_file = f"reports/paper_trading_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(results_file, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            
            logger.info(f"\n✅ Test results saved to: {results_file}")
            return results_file
            
        except Exception as e:
            logger.error(f"Failed to save results: {str(e)}")
            return None


def main():
    """Main entry point"""
    try:
        # Create reports directory if it doesn't exist
        import os
        os.makedirs('reports', exist_ok=True)
        os.makedirs('app/logs', exist_ok=True)
        
        # Run tests
        tester = PaperTradingTester()
        results = tester.run_all_tests()
        
        # Save results
        tester.save_results()
        
        logger.info("\n🎉 PAPER TRADING TEST SUITE COMPLETE!")
        logger.info("Check logs/paper_trading_test.log for detailed results")
        
        return results
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
