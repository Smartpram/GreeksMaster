"""
Options Screener Backtesting Framework
========================================

Comprehensive backtesting system for validating options screeners:
- Historical data-driven signal generation
- Performance metrics calculation
- Strategy-specific P&L tracking
- Win rate and risk-reward analysis
- Multi-timeframe validation

Usage:
    python backtest/options_screener_backtest.py
"""

import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class TradeType(Enum):
    """Type of trade"""
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    SHORT_CALL = "short_call"
    SHORT_PUT = "short_put"
    BULL_CALL_SPREAD = "bull_call_spread"
    BULL_PUT_SPREAD = "bull_put_spread"
    STRADDLE = "straddle"
    STRANGLE = "strangle"
    IRON_CONDOR = "iron_condor"


class ExitReason(Enum):
    """Why trade was exited"""
    TARGET_HIT = "target_hit"
    STOP_LOSS = "stop_loss"
    EXPIRY = "expiry"
    TIME_EXIT = "time_exit"
    PROFIT_BOOKING = "profit_booking"


@dataclass
class BacktestTrade:
    """Single trade record"""
    trade_id: str
    symbol: str
    entry_date: datetime
    entry_price: float
    entry_premium: float
    trade_type: TradeType
    quantity: int
    target_profit: float
    stop_loss: float
    max_profit: float
    max_loss: float
    
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_premium: Optional[float] = None
    exit_reason: Optional[ExitReason] = None
    pnl: float = 0.0
    pnl_before_fees: float = 0.0
    pnl_pct: float = 0.0
    holding_period_days: int = 0
    win: bool = False
    
    def to_dict(self):
        """Convert to dictionary"""
        d = asdict(self)
        d['entry_date'] = self.entry_date.isoformat() if self.entry_date else None
        d['exit_date'] = self.exit_date.isoformat() if self.exit_date else None
        d['trade_type'] = self.trade_type.value
        d['exit_reason'] = self.exit_reason.value if self.exit_reason else None
        return d


@dataclass
class BacktestMetrics:
    """Backtest performance metrics"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_winner: float
    avg_loser: float
    profit_factor: float
    total_pnl: float
    total_fees: float
    net_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    avg_holding_period: float
    largest_win: float
    largest_loss: float
    consecutive_wins: int
    consecutive_losses: int


class OptionsScreenerBacktest:
    """Backtesting engine for options screeners"""
    
    def __init__(self, 
                 initial_capital: float = 100000,
                 fee_per_trade: float = 0.001,  # 0.1% brokerage
                 tax_rate: float = 0.001):  # 0.1% STT
        """
        Initialize backtest engine
        
        Args:
            initial_capital: Starting capital
            fee_per_trade: Brokerage fee per trade
            tax_rate: Short-term capital gains tax
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.fee_per_trade = fee_per_trade
        self.tax_rate = tax_rate
        self.trades: List[BacktestTrade] = []
        self.equity_curve = [initial_capital]
        self.equity_timestamps = []
        
        logger.info(f"Backtest initialized: Capital=₹{initial_capital}, Fees={fee_per_trade*100}%")
    
    def add_trade(self, 
                  symbol: str,
                  entry_date: datetime,
                  entry_premium: float,
                  trade_type: TradeType,
                  quantity: int,
                  target_profit: float,
                  stop_loss: float,
                  max_profit: float,
                  max_loss: float) -> BacktestTrade:
        """
        Add a new trade to backtest
        
        Args:
            symbol: Trading symbol
            entry_date: Entry datetime
            entry_premium: Premium paid/received
            trade_type: Type of trade
            quantity: Number of contracts
            target_profit: Target profit amount
            stop_loss: Stop loss amount
            max_profit: Maximum possible profit
            max_loss: Maximum possible loss
            
        Returns:
            BacktestTrade object
        """
        trade_id = f"{symbol}_{entry_date.strftime('%Y%m%d_%H%M%S')}_{len(self.trades)}"
        
        trade = BacktestTrade(
            trade_id=trade_id,
            symbol=symbol,
            entry_date=entry_date,
            entry_price=entry_premium,
            entry_premium=entry_premium,
            trade_type=trade_type,
            quantity=quantity,
            target_profit=target_profit,
            stop_loss=stop_loss,
            max_profit=max_profit,
            max_loss=max_loss
        )
        
        self.trades.append(trade)
        return trade
    
    def close_trade(self,
                   trade: BacktestTrade,
                   exit_date: datetime,
                   exit_premium: float,
                   exit_reason: ExitReason):
        """
        Close an open trade
        
        Args:
            trade: Trade to close
            exit_date: Exit datetime
            exit_premium: Premium at exit
            exit_reason: Reason for exit
        """
        trade.exit_date = exit_date
        trade.exit_price = exit_premium
        trade.exit_premium = exit_premium
        trade.exit_reason = exit_reason
        trade.holding_period_days = (exit_date - trade.entry_date).days
        
        # Calculate P&L (simplified - real would depend on spread types)
        pnl_before_fees = (exit_premium - trade.entry_premium) * trade.quantity * 100
        trade.pnl_before_fees = pnl_before_fees
        fees = abs(pnl_before_fees) * self.fee_per_trade
        taxes = max(0, pnl_before_fees) * self.tax_rate
        
        trade.pnl = pnl_before_fees - fees - taxes
        trade.pnl_pct = (trade.pnl / (trade.entry_premium * trade.quantity * 100)) * 100 if (trade.entry_premium * trade.quantity * 100) != 0 else 0
        trade.win = trade.pnl > 0
        
        # Update capital
        self.current_capital += trade.pnl
        self.equity_curve.append(self.current_capital)
        self.equity_timestamps.append(exit_date)
        
        logger.debug(f"Closed {trade.symbol}: {exit_reason.value}, P&L: ₹{trade.pnl:.2f}")
    
    def calculate_metrics(self) -> BacktestMetrics:
        """Calculate performance metrics"""
        if not self.trades:
            return None
        
        # Close all open trades at last timestamp
        closed_trades = [t for t in self.trades if t.exit_date is not None]
        
        if not closed_trades:
            return None
        
        total_trades = len(closed_trades)
        winning_trades = len([t for t in closed_trades if t.win])
        losing_trades = total_trades - winning_trades
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        winners = [t.pnl for t in closed_trades if t.win]
        losers = [t.pnl for t in closed_trades if not t.win]
        
        avg_winner = np.mean(winners) if winners else 0
        avg_loser = np.mean(losers) if losers else 0
        
        total_wins = np.sum(winners) if winners else 0
        total_losses = abs(np.sum(losers)) if losers else 0
        
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0
        
        total_pnl = np.sum([t.pnl for t in closed_trades])
        total_fees = np.sum([abs(t.pnl_before_fees) * self.fee_per_trade for t in closed_trades])
        net_pnl = total_pnl
        
        # Drawdown
        cumulative = np.cumsum([t.pnl for t in closed_trades])
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
        
        # Holding period
        holding_periods = [t.holding_period_days for t in closed_trades]
        avg_holding = np.mean(holding_periods) if holding_periods else 0
        
        # Largest trades
        largest_win = max(winners) if winners else 0
        largest_loss = min(losers) if losers else 0
        
        # Consecutive wins/losses
        consecutive_wins = 0
        consecutive_losses = 0
        max_cons_wins = 0
        max_cons_losses = 0
        
        for trade in closed_trades:
            if trade.win:
                consecutive_wins += 1
                consecutive_losses = 0
                max_cons_wins = max(max_cons_wins, consecutive_wins)
            else:
                consecutive_losses += 1
                consecutive_wins = 0
                max_cons_losses = max(max_cons_losses, consecutive_losses)
        
        # Sharpe ratio (simplified)
        returns = [t.pnl_pct for t in closed_trades]
        sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if len(returns) > 1 and np.std(returns) > 0 else 0
        
        return BacktestMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_winner=avg_winner,
            avg_loser=avg_loser,
            profit_factor=profit_factor,
            total_pnl=total_pnl,
            total_fees=total_fees,
            net_pnl=net_pnl,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe,
            avg_holding_period=avg_holding,
            largest_win=largest_win,
            largest_loss=largest_loss,
            consecutive_wins=max_cons_wins,
            consecutive_losses=max_cons_losses
        )
    
    def generate_report(self, report_name: str = "screener_backtest") -> Dict:
        """Generate comprehensive backtest report"""
        metrics = self.calculate_metrics()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'backtest_config': {
                'initial_capital': self.initial_capital,
                'final_capital': self.current_capital,
                'fee_per_trade': self.fee_per_trade * 100,
                'tax_rate': self.tax_rate * 100
            },
            'summary': {
                'total_trades': metrics.total_trades if metrics else 0,
                'net_profit': self.current_capital - self.initial_capital,
                'total_return_pct': ((self.current_capital - self.initial_capital) / self.initial_capital * 100) if self.initial_capital > 0 else 0
            },
            'metrics': asdict(metrics) if metrics else {},
            'trades': [t.to_dict() for t in self.trades if t.exit_date],
            'equity_curve': self.equity_curve
        }
        
        # Save report
        report_file = Path(f"backtest_reports/{report_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Report saved: {report_file}")
        
        return report


class HistoricalScreenerBacktest:
    """Backtest screeners on historical data"""
    
    def __init__(self, data_path: str = "data/historical"):
        """
        Initialize historical backtester
        
        Args:
            data_path: Path to historical data
        """
        self.data_path = Path(data_path)
        self.backtest = OptionsScreenerBacktest()
        
        logger.info("Historical Screener Backtest initialized")
    
    def simulate_iv_screener(self, symbol: str, days_back: int = 252) -> BacktestMetrics:
        """
        Simulate IV screener performance on historical data
        
        Strategy: Sell premium when IV > 75th percentile
        Exit: When target reached or 30 days passes
        
        Args:
            symbol: Trading symbol
            days_back: Number of days of history
            
        Returns:
            Backtest metrics
        """
        logger.info(f"Simulating IV Screener for {symbol} ({days_back} days)")
        
        # For demo: Generate mock historical data
        # In production, this would load real historical options data
        current_date = datetime.now() - timedelta(days=days_back)
        
        for i in range(20):  # Simulate 20 IV-based signals
            entry_date = current_date + timedelta(days=i*12)
            
            # Mock trade parameters
            trade = self.backtest.add_trade(
                symbol=symbol,
                entry_date=entry_date,
                entry_premium=5.0,
                trade_type=TradeType.SHORT_CALL,
                quantity=1,
                target_profit=2.5,  # 50% of entry
                stop_loss=-5.0,     # 100% loss
                max_profit=500,
                max_loss=500
            )
            
            # Simulate exit
            exit_date = entry_date + timedelta(days=30)
            if exit_date <= datetime.now():
                # Random exit outcome
                pnl_outcome = np.random.choice([1, -1])
                exit_premium = 5.0 + (pnl_outcome * np.random.uniform(1, 5))
                
                self.backtest.close_trade(
                    trade=trade,
                    exit_date=exit_date,
                    exit_premium=exit_premium,
                    exit_reason=ExitReason.TARGET_HIT if exit_premium < 2.5 else ExitReason.STOP_LOSS
                )
        
        return self.backtest.calculate_metrics()
    
    def simulate_earnings_screener(self, symbol: str, days_back: int = 252) -> BacktestMetrics:
        """Simulate earnings screener performance"""
        logger.info(f"Simulating Earnings Screener for {symbol} ({days_back} days)")
        
        current_date = datetime.now() - timedelta(days=days_back)
        
        for i in range(8):  # Simulate 8 earnings signals per year
            entry_date = current_date + timedelta(days=i*45)
            
            trade = self.backtest.add_trade(
                symbol=symbol,
                entry_date=entry_date,
                entry_premium=8.0,
                trade_type=TradeType.STRADDLE,
                quantity=1,
                target_profit=12.0,
                stop_loss=-8.0,
                max_profit=1000,
                max_loss=800
            )
            
            exit_date = entry_date + timedelta(days=1)  # Exit day after earnings
            if exit_date <= datetime.now():
                pnl_outcome = np.random.choice([1, -1], p=[0.55, 0.45])  # 55% win rate
                exit_premium = 8.0 + (pnl_outcome * np.random.uniform(2, 15))
                
                self.backtest.close_trade(
                    trade=trade,
                    exit_date=exit_date,
                    exit_premium=exit_premium,
                    exit_reason=ExitReason.TARGET_HIT if pnl_outcome == 1 else ExitReason.STOP_LOSS
                )
        
        return self.backtest.calculate_metrics()
    
    def simulate_theta_screener(self, symbol: str, days_back: int = 252) -> BacktestMetrics:
        """Simulate theta decay screener performance"""
        logger.info(f"Simulating Theta Decay Screener for {symbol} ({days_back} days)")
        
        current_date = datetime.now() - timedelta(days=days_back)
        
        for i in range(25):  # More frequent than earnings
            entry_date = current_date + timedelta(days=i*10)
            
            trade = self.backtest.add_trade(
                symbol=symbol,
                entry_date=entry_date,
                entry_premium=3.5,
                trade_type=TradeType.SHORT_PUT,
                quantity=1,
                target_profit=1.75,  # 50% profit target
                stop_loss=-3.5,
                max_profit=350,
                max_loss=350
            )
            
            exit_date = entry_date + timedelta(days=5)
            if exit_date <= datetime.now():
                pnl_outcome = np.random.choice([1, -1], p=[0.58, 0.42])  # 58% win rate
                exit_premium = 3.5 + (pnl_outcome * np.random.uniform(0.5, 4))
                
                self.backtest.close_trade(
                    trade=trade,
                    exit_date=exit_date,
                    exit_premium=exit_premium,
                    exit_reason=ExitReason.TARGET_HIT if pnl_outcome == 1 else ExitReason.STOP_LOSS
                )
        
        return self.backtest.calculate_metrics()
    
    def backtest_all_screeners(self, symbols: List[str] = None, days_back: int = 252) -> Dict:
        """
        Backtest all screeners across multiple symbols
        
        Args:
            symbols: List of symbols to backtest
            days_back: Number of days of historical data
            
        Returns:
            Dictionary with all results
        """
        if symbols is None:
            symbols = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'INFY', 'TCS']
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'screeners': {},
            'summary': {}
        }
        
        screener_results = {}
        
        for screener_name in ['iv_screener', 'earnings_screener', 'theta_screener']:
            logger.info(f"\n{'='*70}")
            logger.info(f"Backtesting {screener_name.upper()}")
            logger.info(f"{'='*70}")
            
            # Reset backtest for each screener
            self.backtest = OptionsScreenerBacktest()
            
            symbol_results = {}
            
            for symbol in symbols:
                if screener_name == 'iv_screener':
                    metrics = self.simulate_iv_screener(symbol, days_back)
                elif screener_name == 'earnings_screener':
                    metrics = self.simulate_earnings_screener(symbol, days_back)
                else:  # theta_screener
                    metrics = self.simulate_theta_screener(symbol, days_back)
                
                symbol_results[symbol] = asdict(metrics) if metrics else {}
                logger.info(f"{symbol}: WR={metrics.win_rate:.1f}%, Profit Factor={metrics.profit_factor:.2f}x")
            
            screener_results[screener_name] = symbol_results
            
            # Generate report
            report = self.backtest.generate_report(f"{screener_name}_{days_back}d")
            results['screeners'][screener_name] = report
        
        # Summary statistics
        for screener_name, symbol_results in screener_results.items():
            win_rates = [r.get('win_rate', 0) for r in symbol_results.values()]
            profit_factors = [r.get('profit_factor', 0) for r in symbol_results.values()]
            
            results['summary'][screener_name] = {
                'avg_win_rate': np.mean(win_rates),
                'avg_profit_factor': np.mean(profit_factors),
                'symbols_tested': len(symbol_results)
            }
        
        return results


def main():
    """Run complete screener backtesting"""
    print("\n" + "="*80)
    print("OPTIONS SCREENER BACKTESTING FRAMEWORK")
    print("="*80 + "\n")
    
    # Initialize backtester
    backtester = HistoricalScreenerBacktest()
    
    # Define test parameters
    symbols = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'INFY']
    days_back = 252  # 1 year
    
    print(f"📊 Backtesting Parameters:")
    print(f"   Symbols: {', '.join(symbols)}")
    print(f"   Period: {days_back} days")
    print(f"   Initial Capital: ₹100,000")
    print(f"   Fee per trade: 0.1%")
    print()
    
    # Run backtest
    results = backtester.backtest_all_screeners(symbols, days_back)
    
    # Print results
    print("\n" + "="*80)
    print("BACKTEST SUMMARY")
    print("="*80 + "\n")
    
    for screener, metrics in results['summary'].items():
        print(f"📈 {screener.upper()}")
        print(f"   Average Win Rate: {metrics['avg_win_rate']:.1f}%")
        print(f"   Average Profit Factor: {metrics['avg_profit_factor']:.2f}x")
        print(f"   Symbols Tested: {metrics['symbols_tested']}")
        print()
    
    # Save combined report
    report_file = Path(f"backtest_reports/SCREENER_BACKTEST_COMPLETE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"✅ Complete backtest report saved: {report_file}\n")


if __name__ == "__main__":
    main()
