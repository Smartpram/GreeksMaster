"""
Live Trading System Integration
Complete end-to-end trading workflow:
1. Initialize all components
2. Run screeners
3. Execute signals
4. Monitor positions
5. Generate reports

This is the main entry point for live trading operations.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app/logs/live_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class LiveTradingSystem:
    """
    Integrated live trading system combining:
    - Stock screeners (12 templates)
    - Position tracking (real-time P&L)
    - Signal execution (automated trading)
    """
    
    def __init__(self):
        """Initialize the trading system"""
        logger.info("Initializing Live Trading System...")
        
        from app.services.breeze_api import BreezeAPIService
        from app.services.order_manager import OrderManager
        from app.services.risk_manager import RiskManager
        from app.services.stock_screener import StockScreener
        from app.services.live_position_tracker import LivePositionTracker
        from app.services.signal_executor import SignalExecutor, ExecutionMode
        from app.services.notifications import NotificationService
        
        # Initialize core services
        self.breeze = BreezeAPIService()
        
        capital = float(os.getenv('DEFAULT_CAPITAL', '100000'))
        self.risk_manager = RiskManager(capital=capital)
        self.order_manager = OrderManager(self.breeze, self.risk_manager)
        self.notifications = NotificationService()
        
        # Initialize trading components
        self.screener = StockScreener(self.breeze, self.risk_manager)
        self.position_tracker = LivePositionTracker(
            self.risk_manager, 
            self.notifications
        )
        
        # Get execution mode
        mode_str = os.getenv('EXECUTION_MODE', 'paper').lower()
        mode_map = {
            'manual': ExecutionMode.MANUAL,
            'semi_auto': ExecutionMode.SEMI_AUTO,
            'auto': ExecutionMode.AUTO,
            'paper': ExecutionMode.PAPER
        }
        exec_mode = mode_map.get(mode_str, ExecutionMode.PAPER)
        
        self.executor = SignalExecutor(
            self.order_manager,
            self.risk_manager,
            self.position_tracker,
            self.notifications,
            execution_mode=exec_mode
        )
        
        logger.info(f"✓ System initialized in {exec_mode.value} mode")
    
    # ==================== SCREENER OPERATIONS ====================
    
    def run_all_screeners(self, stocks_df) -> Dict:
        """
        Run all 12 screeners and return results
        
        Returns:
            Dictionary with results for each screener
        """
        logger.info("🔍 Running all screeners...")
        
        from app.services.stock_screener import ScreenerType
        
        results = {}
        
        for screener_type in ScreenerType:
            try:
                screened = self.screener.run_screener(screener_type, stocks_df)
                results[screener_type.value] = screened
                logger.info(f"  {screener_type.value}: {len(screened)} stocks found")
            except Exception as e:
                logger.error(f"  {screener_type.value}: Error - {e}")
                results[screener_type.value] = []
        
        return results
    
    def get_top_opportunities(self, screener_results: Dict, 
                             top_n: int = 5) -> List[Dict]:
        """Get top opportunities across all screeners"""
        all_stocks = []
        
        for screener_name, stocks in screener_results.items():
            for stock in stocks:
                stock['screener_type'] = screener_name
                all_stocks.append(stock)
        
        # Sort by score (highest first)
        all_stocks.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return all_stocks[:top_n]
    
    # ==================== SIGNAL EXECUTION ====================
    
    def execute_top_screener_signals(self, screener_results: Dict,
                                     auto_execute: bool = True,
                                     min_confidence: float = 0.7) -> Dict:
        """
        Execute buy signals from screener results
        
        Args:
            screener_results: Results from run_all_screeners
            auto_execute: Whether to auto-execute or require approval
            min_confidence: Minimum signal confidence threshold
        """
        logger.info("📍 Executing screener signals...")
        
        # Get top stocks across screeners
        top_stocks = []
        for screener_type, results in screener_results.items():
            for stock in results[:2]:  # Top 2 from each screener
                stock['screener_type'] = screener_type
                top_stocks.append(stock)
        
        # Filter by confidence
        filtered = [s for s in top_stocks 
                   if s.get('score', 0) / 100 >= min_confidence]
        
        logger.info(f"  Executing {len(filtered)} high-confidence signals")
        
        # Execute signals
        execution_result = self.executor.execute_screener_signal(
            filtered, 
            auto_execute=auto_execute
        )
        
        logger.info(f"  Executed: {execution_result['executed']}, "
                   f"Failed: {execution_result['failed']}, "
                   f"Pending: {execution_result['pending_approval']}")
        
        return execution_result
    
    # ==================== POSITION MONITORING ====================
    
    def update_all_positions(self, current_prices: Dict[str, float]) -> int:
        """
        Update all positions with latest prices
        
        Returns:
            Number of positions updated
        """
        updated = 0
        
        for position in self.position_tracker.get_all_positions():
            symbol = position['symbol']
            if symbol in current_prices:
                new_price = current_prices[symbol]
                self.position_tracker.update_position_price(
                    position['position_id'],
                    new_price
                )
                updated += 1
        
        return updated
    
    def check_exit_triggers(self) -> List[Dict]:
        """
        Check if any positions hit exit triggers
        
        Returns:
            List of positions with triggered exits
        """
        triggered_exits = []
        
        target_percent = float(os.getenv('TARGET_PERCENT', '0.15'))
        stop_loss_percent = float(os.getenv('STOP_LOSS_PERCENT', '-0.05'))
        
        for position in self.position_tracker.get_all_positions():
            pnl_pct = position['unrealized_pnl_percent'] / 100
            
            # Check target hit
            if pnl_pct >= target_percent:
                triggered_exits.append({
                    'position': position,
                    'reason': 'target_hit',
                    'pnl_pct': pnl_pct
                })
            
            # Check stop loss hit
            elif pnl_pct <= stop_loss_percent:
                triggered_exits.append({
                    'position': position,
                    'reason': 'stop_loss',
                    'pnl_pct': pnl_pct
                })
        
        return triggered_exits
    
    def auto_exit_triggered_positions(self) -> Dict:
        """Automatically exit positions that hit triggers"""
        logger.info("🔍 Checking exit triggers...")
        
        triggered = self.check_exit_triggers()
        logger.info(f"  Found {len(triggered)} triggered positions")
        
        executed_exits = 0
        total_pnl = 0
        
        for trigger in triggered:
            position = trigger['position']
            reason = trigger['reason']
            
            result = self.executor.execute_exit_signal(
                symbol=position['symbol'],
                price=position['current_price'],
                confidence=0.95,
                reason=reason,
                exit_type='full'
            )
            
            if result['success']:
                executed_exits += 1
                total_pnl += position['unrealized_pnl']
                logger.info(f"  ✓ {position['symbol']}: {reason} "
                           f"(PnL: {position['unrealized_pnl']:.0f})")
        
        return {
            'executed': executed_exits,
            'total_pnl': total_pnl,
            'positions': triggered
        }
    
    # ==================== REPORTING ====================
    
    def get_portfolio_report(self) -> Dict:
        """Get comprehensive portfolio report"""
        summary = self.position_tracker.get_portfolio_summary()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'portfolio': summary,
            'positions': self.position_tracker.get_all_positions(),
            'execution_stats': self.executor.get_execution_stats(),
            'pending_approvals': len(self.executor.get_pending_approvals())
        }
        
        return report
    
    def print_report(self):
        """Print formatted portfolio report"""
        report = self.get_portfolio_report()
        portfolio = report['portfolio']
        
        print("\n" + "="*60)
        print("📊 PORTFOLIO REPORT")
        print("="*60)
        print(f"Timestamp: {report['timestamp']}")
        
        print(f"\n💰 Positions:")
        print(f"  Open Positions: {portfolio['open_positions']}")
        print(f"  Closed Positions: {portfolio['closed_positions']}")
        
        print(f"\n📈 Values:")
        print(f"  Entry Value: ${portfolio['total_entry_value']:,.0f}")
        print(f"  Current Value: ${portfolio['total_current_value']:,.0f}")
        print(f"  Unrealized P&L: ${portfolio['unrealized_pnl']:+,.0f}")
        print(f"  Realized P&L: ${portfolio['realized_pnl']:+,.0f}")
        print(f"  Total P&L: ${portfolio['total_pnl']:+,.0f} ({portfolio['total_pnl_percent']:+.1f}%)")
        
        print(f"\n📊 Performance:")
        print(f"  Win Rate: {portfolio['win_rate']:.1f}%")
        print(f"  Best Trade: ${portfolio['best_trade']:+,.0f}")
        print(f"  Worst Trade: ${portfolio['worst_trade']:+,.0f}")
        print(f"  Avg Win: ${portfolio['avg_winning_trade']:+,.0f}")
        print(f"  Avg Loss: ${portfolio['avg_losing_trade']:+,.0f}")
        
        print(f"\n⚙️ Execution:")
        stats = report['execution_stats']
        print(f"  Total Signals: {stats['total_signals']}")
        print(f"  Successful: {stats['successful']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Success Rate: {stats['success_rate']:.1f}%")
        print(f"  Pending Approvals: {report['pending_approvals']}")
        
        print("\n" + "="*60 + "\n")
    
    def export_report(self, filename: str = None) -> str:
        """Export portfolio report as JSON"""
        if filename is None:
            filename = f"app/logs/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = self.get_portfolio_report()
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Report exported to {filename}")
        return filename
    
    # ==================== EXECUTION MODE ====================
    
    def set_execution_mode(self, mode: str):
        """Change execution mode (manual, semi_auto, auto, paper)"""
        from app.services.signal_executor import ExecutionMode
        
        mode_map = {
            'manual': ExecutionMode.MANUAL,
            'semi_auto': ExecutionMode.SEMI_AUTO,
            'auto': ExecutionMode.AUTO,
            'paper': ExecutionMode.PAPER
        }
        
        if mode.lower() in mode_map:
            self.executor.set_execution_mode(mode_map[mode.lower()])
            logger.info(f"Execution mode changed to: {mode}")
        else:
            logger.warning(f"Invalid mode: {mode}")
    
    def get_status(self) -> Dict:
        """Get system status"""
        return {
            'timestamp': datetime.now().isoformat(),
            'execution_mode': self.executor.execution_mode.value,
            'open_positions': len(self.position_tracker.get_all_positions()),
            'portfolio_pnl': self.position_tracker.get_portfolio_summary()['total_pnl'],
            'pending_approvals': len(self.executor.get_pending_approvals()),
            'execution_success_rate': self.executor.get_execution_stats()['success_rate']
        }


# ==================== STANDALONE ENTRY POINT ====================

def main():
    """Main entry point for live trading system"""
    
    print("\n" + "="*60)
    print("🚀 MyBreezeApp Live Trading System")
    print("="*60)
    
    # Initialize system
    system = LiveTradingSystem()
    
    # Load stock universe
    logger.info("Loading stock universe...")
    from download_security_master import get_stock_universe
    stocks_df = get_stock_universe()
    logger.info(f"✓ Loaded {len(stocks_df)} stocks")
    
    # Run screeners
    logger.info("Running screeners...")
    screener_results = system.run_all_screeners(stocks_df)
    
    # Get top opportunities
    top_opportunities = system.get_top_opportunities(screener_results, top_n=10)
    logger.info(f"Found {len(top_opportunities)} top opportunities:")
    for stock in top_opportunities[:5]:
        logger.info(f"  - {stock['symbol']}: {stock['score']}/100 "
                   f"({stock.get('screener_type', 'unknown')})")
    
    # Execute signals
    logger.info("Executing signals...")
    execution = system.execute_top_screener_signals(
        screener_results,
        auto_execute=True,
        min_confidence=0.75
    )
    
    # Print report
    system.print_report()
    
    # Export report
    system.export_report()
    
    logger.info("✓ Live trading system ready")
    logger.info(f"Status: {system.get_status()}")


if __name__ == '__main__':
    main()
