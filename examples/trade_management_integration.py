"""
TRADE MANAGEMENT LAYER - PHASE 5 INTEGRATION EXAMPLE
=====================================================

Shows how to integrate Trade Management Layer with Phase 5 paper trading system.

Integration Pattern:
  Phase 5 generates signal
  ↓
  Trade Management Layer monitors
  ↓
  Recommends dynamic exits
  ↓
  Phase 5 executes recommendations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json

# Import from existing Phase 5
# from backtest.phase5_paper_trading_enhanced import PaperTradingEngine, PaperSignal

# Add parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import new Trade Management Layer
from app.trade_management_layer import (
    TradeManagementLayer,
    TrendDirection,
    ExitSignal
)


# ============================================================================
# ENHANCED PAPER SIGNAL WITH TRADE MANAGEMENT SUPPORT
# ============================================================================

class EnhancedPaperSignal:
    """Paper trading signal with Trade Management Layer support"""
    
    def __init__(self, symbol: str, entry_price: float, entry_time: datetime,
                 timeframe: str = "15m"):
        self.symbol = symbol
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.timeframe = timeframe
        
        # Trade state
        self.status = "OPEN"  # OPEN, PARTIAL_EXITED, CLOSED
        self.closed_time = None
        self.close_reason = None
        self.close_price = None
        
        # Scaling tracking
        self.scaled_out_pcts = []  # Track all scale-outs
        self.total_scaled_out = 0.0  # Cumulative %
        
        # Trade Management recommendations
        self.last_mgmt_report = None
        self.exit_recommendations = []
    
    def get_pnl_pct(self, current_price: float) -> float:
        """Calculate P&L %"""
        return ((current_price - self.entry_price) / self.entry_price) * 100
    
    def record_management_recommendation(self, report: Dict):
        """Log trade management recommendation"""
        self.last_mgmt_report = report
        
        decision = report['decision']
        recommendation = {
            'timestamp': report['timestamp'],
            'action': decision['exit_action'],
            'reason': decision['exit_reason'],
            'context_score': report['context']['overall_score'],
            'scale_pct': decision['scale_out_pct']
        }
        self.exit_recommendations.append(recommendation)
    
    def scale_out(self, pct: float, price: float, reason: str = ""):
        """Scale out portion of position"""
        self.scaled_out_pcts.append({
            'pct': pct,
            'price': price,
            'time': datetime.now(),
            'reason': reason
        })
        self.total_scaled_out += pct
        self.status = "PARTIAL_EXITED"
    
    def close(self, price: float, reason: str = "", full: bool = True):
        """Close position"""
        self.close_price = price
        self.close_time = datetime.now()
        self.close_reason = reason
        self.status = "CLOSED"
        if full:
            self.total_scaled_out = 100.0
    
    def get_summary(self) -> Dict:
        """Get signal summary with all details"""
        return {
            'symbol': self.symbol,
            'entry_price': self.entry_price,
            'entry_time': self.entry_time.isoformat(),
            'close_price': self.close_price,
            'close_time': self.close_time.isoformat() if self.close_time else None,
            'status': self.status,
            'pnl_pct': self.get_pnl_pct(self.close_price) if self.close_price else None,
            'exit_reason': self.close_reason,
            'scaled_out': self.total_scaled_out,
            'scale_outs': self.scaled_out_pcts,
            'mgmt_recommendations': self.exit_recommendations,
            'last_mgmt_report': self.last_mgmt_report
        }


# ============================================================================
# ENHANCED PAPER TRADING ENGINE WITH TRADE MANAGEMENT
# ============================================================================

class EnhancedPaperTradingEngine:
    """Phase 5 Paper Trading with Trade Management Layer"""
    
    def __init__(self, screener_class=None, options_engine_class=None):
        self.trade_manager = TradeManagementLayer()
        
        # Active and closed signals
        self.active_signals: List[EnhancedPaperSignal] = []
        self.closed_signals: List[EnhancedPaperSignal] = []
        
        # Statistics
        self.metrics = {
            'total_signals': 0,
            'closed_signals': 0,
            'winning_signals': 0,
            'losing_signals': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'avg_pnl': 0.0
        }
    
    def generate_entry_signal(self, symbol: str, entry_price: float,
                            df: pd.DataFrame) -> Optional[EnhancedPaperSignal]:
        """Generate new entry signal with Trade Management validation"""
        
        # Stage 1: Check if entry is favorable (Trade Management)
        context = self.trade_manager.context_engine.calculate(df)
        
        # Get historical exit pool for this symbol
        bullish_pool, bearish_pool = self.trade_manager.exit_pool_builder.find_pivots(
            df,
            self.trade_manager.context_engine
        )
        
        # Score context
        score = self.trade_manager.density_scorer.score(context, bullish_pool)
        
        # Evaluate entry
        st = self.trade_manager.supertrend.calculate(df)
        entry_favorable, reason = self.trade_manager.exit_manager.evaluate_entry(
            score.overall_score,
            st.flip_detected
        )
        
        if not entry_favorable:
            print(f"  ❌ Entry blocked: {reason}")
            return None
        
        # Create signal
        signal = EnhancedPaperSignal(
            symbol=symbol,
            entry_price=entry_price,
            entry_time=datetime.now(),
            timeframe="15m"
        )
        
        # Record initial context
        signal.last_mgmt_report = self.trade_manager.analyze_trade(
            df, symbol, "15m", 0.0, entry_price
        )
        
        self.active_signals.append(signal)
        self.metrics['total_signals'] += 1
        
        print(f"  ✅ Entry signal: {symbol} @ {entry_price:.2f}")
        print(f"     Context score: {score.overall_score:.1f} ({score.tp_quality})")
        
        return signal
    
    def update_active_signals(self, df: pd.DataFrame, current_price: float):
        """Update active signals with Trade Management recommendations"""
        
        closed_this_bar = []
        
        for signal in self.active_signals:
            # Calculate current P&L
            pnl_pct = signal.get_pnl_pct(current_price)
            
            # Get Trade Management recommendation
            mgmt_report = self.trade_manager.analyze_trade(
                df,
                symbol=signal.symbol,
                timeframe=signal.timeframe,
                pnl_pct=pnl_pct,
                entry_price=signal.entry_price
            )
            
            # Record recommendation
            signal.record_management_recommendation(mgmt_report)
            
            # Execute recommendation
            decision = mgmt_report['decision']
            action = decision['exit_action']
            
            if action == "FULL_EXIT":
                # Close entire position
                signal.close(
                    current_price,
                    reason=decision['exit_reason'],
                    full=True
                )
                closed_this_bar.append(signal)
                
                final_pnl = signal.get_pnl_pct(current_price)
                self.metrics['total_pnl'] += final_pnl
                self.metrics['closed_signals'] += 1
                
                if final_pnl > 0:
                    self.metrics['winning_signals'] += 1
                    print(f"  ✅ CLOSED {signal.symbol} @ {current_price:.2f}: +{final_pnl:.2f}% ({decision['exit_reason']})")
                else:
                    self.metrics['losing_signals'] += 1
                    print(f"  ❌ CLOSED {signal.symbol} @ {current_price:.2f}: {final_pnl:.2f}% ({decision['exit_reason']})")
            
            elif action == "PARTIAL_EXIT":
                # Scale out portion
                scale_pct = decision['scale_out_pct'] / 100
                signal.scale_out(
                    scale_pct * 100,
                    current_price,
                    reason=decision['exit_reason']
                )
                print(f"  📊 SCALED {signal.symbol} @ {current_price:.2f}: -{scale_pct*100:.0f}% ({decision['exit_reason']})")
            
            elif action == "TIGHTEN_STOP":
                # Update stop loss
                if decision['new_stop']:
                    print(f"  🛡️  TIGHTEN STOP {signal.symbol}: {decision['exit_reason']}")
        
        # Move closed signals
        for signal in closed_this_bar:
            self.active_signals.remove(signal)
            self.closed_signals.append(signal)
    
    def get_metrics(self) -> Dict:
        """Get trading metrics"""
        if self.metrics['closed_signals'] > 0:
            self.metrics['win_rate'] = (
                self.metrics['winning_signals'] / self.metrics['closed_signals'] * 100
            )
            self.metrics['avg_pnl'] = (
                self.metrics['total_pnl'] / self.metrics['closed_signals']
            )
        
        return self.metrics
    
    def print_summary(self):
        """Print trading summary"""
        metrics = self.get_metrics()
        
        print("\n" + "="*80)
        print("TRADING SUMMARY")
        print("="*80)
        print(f"Total Signals: {metrics['total_signals']}")
        print(f"Closed Signals: {metrics['closed_signals']}")
        print(f"Win Rate: {metrics['win_rate']:.1f}%")
        print(f"Total P&L: {metrics['total_pnl']:.2f}%")
        print(f"Avg P&L per trade: {metrics['avg_pnl']:.2f}%")
        print(f"Active Signals: {len(self.active_signals)}")
        print("="*80)
        
        if self.closed_signals:
            print("\nClosed Trades:")
            for signal in self.closed_signals:
                pnl = signal.get_pnl_pct(signal.close_price)
                print(f"  {signal.symbol}: {pnl:+.2f}% ({signal.close_reason})")


# ============================================================================
# EXAMPLE USAGE - SIMULATED EXECUTION
# ============================================================================

def example_integration():
    """Example showing Trade Management integration with Phase 5"""
    
    print("="*80)
    print("TRADE MANAGEMENT LAYER - PHASE 5 INTEGRATION EXAMPLE")
    print("="*80)
    print()
    
    # Initialize enhanced engine
    engine = EnhancedPaperTradingEngine()
    
    # Simulate price data (would come from yfinance in real usage)
    dates = pd.date_range('2024-01-01', periods=100, freq='15min')
    base_price = 1250.0
    
    prices = []
    for i in range(len(dates)):
        # Create realistic price movement
        if i < 20:
            price = base_price + (i * 0.5)  # Uptrend
        elif i < 50:
            price = base_price + 10 + np.sin(i/10) * 5  # Ranging
        else:
            price = base_price + 12 - ((i-50) * 0.3)  # Downtrend
        
        prices.append(price)
    
    df_base = pd.DataFrame({
        'Open': np.array(prices) + np.random.rand(len(prices)) * 2,
        'High': np.array(prices) + 5,
        'Low': np.array(prices) - 5,
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, len(prices))
    }, index=dates)
    
    # Simulate trading
    print("\nSimulating 100 bars of trading:\n")
    
    # Generate entry at bar 20
    print(f"Bar 20: Price={df_base['Close'].iloc[20]:.2f}")
    signal = engine.generate_entry_signal(
        "TESTSTOCK",
        df_base['Close'].iloc[20],
        df_base.iloc[:21]
    )
    
    if signal:
        # Update signal through remaining bars
        for i in range(21, len(df_base)):
            current_price = df_base['Close'].iloc[i]
            
            # Only update every 3 bars for demo
            if i % 3 == 0:
                print(f"\nBar {i}: Price={current_price:.2f}")
                engine.update_active_signals(df_base.iloc[:i+1], current_price)
            
            # Stop if signal closed
            if not engine.active_signals:
                break
    
    # Print summary
    engine.print_summary()
    
    # Print detailed signal info
    if engine.closed_signals:
        print("\nDetailed Trade Info:")
        for signal in engine.closed_signals:
            print(f"\n{signal.symbol}:")
            print(f"  Entry: {signal.entry_price:.2f}")
            print(f"  Exit: {signal.close_price:.2f}")
            print(f"  P&L: {signal.get_pnl_pct(signal.close_price):+.2f}%")
            print(f"  Reason: {signal.close_reason}")
            
            if signal.exit_recommendations:
                print(f"  Management Actions ({len(signal.exit_recommendations)}):")
                for rec in signal.exit_recommendations[-3:]:  # Last 3
                    print(f"    - {rec['action']}: {rec['reason']}")


# ============================================================================
# REAL INTEGRATION TEMPLATE (Use with actual Phase 5)
# ============================================================================

def integrate_with_phase5():
    """
    Template for integrating Trade Management with actual Phase 5 system.
    
    Add this to phase5_paper_trading_enhanced.py:
    """
    
    template = '''
# At top of phase5_paper_trading_enhanced.py:
from app.trade_management_layer import TradeManagementLayer

class PaperTradingEngine:
    def __init__(self, ...):
        # ... existing code ...
        self.trade_manager = TradeManagementLayer()  # ADD THIS LINE
    
    def generate_signal(self, symbol, entry_price, df):
        # ... existing signal generation ...
        
        # ADD: Trade Management validation
        context = self.trade_manager.context_engine.calculate(df)
        bullish_pool, _ = self.trade_manager.exit_pool_builder.find_pivots(df)
        score = self.trade_manager.density_scorer.score(context, bullish_pool)
        st = self.trade_manager.supertrend.calculate(df)
        
        entry_favorable, reason = self.trade_manager.exit_manager.evaluate_entry(
            score.overall_score, st.flip_detected
        )
        
        if not entry_favorable:
            print(f"Entry blocked: {reason}")
            return None  # Skip entry
        
        # ... proceed with signal generation ...
    
    def update_signals(self, df, current_price):
        # ... existing signal management ...
        
        for signal in self.active_signals:
            # ADD: Trade Management monitoring
            pnl_pct = ((current_price - signal.entry_price) / signal.entry_price) * 100
            
            mgmt_report = self.trade_manager.analyze_trade(
                df, signal.symbol, signal.timeframe, pnl_pct, signal.entry_price
            )
            
            action = mgmt_report['decision']['exit_action']
            
            if action == "FULL_EXIT":
                signal.close(current_price, mgmt_report['decision']['exit_reason'])
            elif action == "PARTIAL_EXIT":
                scale = mgmt_report['decision']['scale_out_pct'] / 100
                signal.scale_out(scale, current_price)
            # ... etc ...
    '''
    
    print(template)


if __name__ == "__main__":
    # Run example
    example_integration()
    
    # Show integration template
    print("\n" + "="*80)
    print("PHASE 5 INTEGRATION TEMPLATE")
    print("="*80)
    # integrate_with_phase5()
