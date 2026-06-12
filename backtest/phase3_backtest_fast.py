"""
PHASE 3: Fast Backtest with Range Policy (2024-2025)
=====================================================

Optimized version - processes full data but with efficient computation
"""

import json
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from enum import Enum
import numpy as np
import pandas as pd
import yfinance as yf
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TradeDirection(Enum):
    LONG = "long"


class ExitReason(Enum):
    SMA_BREAKDOWN = "sma_breakdown"
    RANGE_EXIT = "range_exit"


class RegimeType(Enum):
    TREND = "trend"
    RANGE = "range"


@dataclass
class Trade:
    symbol: str
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    direction: str
    exit_reason: str
    position_size: float
    profit_loss_pct: float
    profit_loss_amount: float
    regime_at_entry: str
    bars_held: int
    
    def is_win(self) -> bool:
        return self.profit_loss_pct > 0.0


@dataclass
class BacktestMetrics:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    total_pnl: float
    max_drawdown: float
    avg_win: float
    avg_loss: float
    sharpe_ratio: float
    range_blocks: int
    trades_executed: int
    avg_position_size: float


class RangeDetector:
    """Fast range detection"""
    
    def __init__(self, atr_period=14, bb_period=20):
        self.atr_period = atr_period
        self.bb_period = bb_period
        self.range_bars_count = 0
    
    def detect(self, df: pd.DataFrame) -> tuple:
        """Returns (is_range, confidence, atr_pct, persistence_bars)"""
        if len(df) < self.atr_period:
            return False, 0.0, 0.0, 0
        
        # ATR
        tr = np.maximum(
            df['high'].iloc[-1] - df['low'].iloc[-1],
            np.maximum(
                abs(df['high'].iloc[-1] - df['close'].iloc[-2] if len(df) > 1 else 0),
                abs(df['low'].iloc[-1] - df['close'].iloc[-2] if len(df) > 1 else 0)
            )
        )
        atr = tr / self.atr_period  # Simplified
        atr_pct = atr / df['close'].iloc[-1]
        is_low_vol = atr_pct < 0.015
        
        # ADX (simplified)
        adx = 50  # Neutral assumption
        weak_trend = adx < 25
        
        # BB (simplified)
        sma = df['close'].iloc[-self.bb_period:].mean()
        std = df['close'].iloc[-self.bb_period:].std()
        bb_width = 4 * std
        bb_squeeze = bb_width < atr_pct * 1.5 * df['close'].iloc[-1]
        
        score = (0.4 if is_low_vol else 0) + (0.3 if weak_trend else 0) + (0.3 if bb_squeeze else 0)
        is_range = score >= 0.6
        
        if is_range:
            self.range_bars_count += 1
        else:
            self.range_bars_count = 0
        
        return is_range, score, atr_pct, self.range_bars_count


class SMA20Strategy:
    """SMA20 with optional Range Policy"""
    
    def __init__(self, capital=1_000_000, enable_range_policy=False):
        self.capital = capital
        self.enable_range_policy = enable_range_policy
        self.range_detector = RangeDetector()
        self.open_trades: Dict[str, Dict] = {}
        self.closed_trades: List[Trade] = []
        self.range_blocks = 0
    
    def get_sma20(self, df: pd.DataFrame) -> float:
        """Calculate SMA20"""
        if len(df) >= 20:
            return df['close'].iloc[-20:].mean()
        return df['close'].mean()
    
    def generate_signal(self, df: pd.DataFrame) -> str:
        """Generate buy/sell signal from SMA20 crossover"""
        if len(df) < 22:
            return 'hold'
        
        sma = self.get_sma20(df)
        close_curr = df['close'].iloc[-1]
        close_prev = df['close'].iloc[-2]
        sma_curr = sma
        sma_prev = df['close'].iloc[-21:-1].mean()
        
        # BUY: Price crosses above SMA20
        if close_prev <= sma_prev and close_curr > sma_curr:
            return 'buy'
        
        # SELL: Price crosses below SMA20
        if close_prev >= sma_prev and close_curr < sma_curr:
            return 'sell'
        
        return 'hold'
    
    def process_bar(self, symbol: str, date: str, ohlcv: Dict, df: pd.DataFrame) -> Optional[Trade]:
        """Process one bar"""
        closed_trade = None
        
        # Range check
        is_range, conf, atr_pct, persistence = self.range_detector.detect(df)
        pos_size = 1.0
        can_trade = True
        
        if self.enable_range_policy and is_range:
            if persistence >= 5:
                can_trade = False
                pos_size = 0.0
                self.range_blocks += 1
            elif persistence < 5:
                pos_size = 0.5
        
        # Signals
        signal = self.generate_signal(df)
        
        # Close trades
        if symbol in self.open_trades and signal == 'sell':
            trade = self.open_trades[symbol]
            pnl_pct = (ohlcv['close'] - trade['entry_price']) / trade['entry_price']
            pnl_amt = pnl_pct * trade['capital']
            
            closed_trade = Trade(
                symbol=symbol,
                entry_date=trade['entry_date'],
                entry_price=trade['entry_price'],
                exit_date=date,
                exit_price=ohlcv['close'],
                direction='long',
                exit_reason='sma_breakdown',
                position_size=trade['position_size'],
                profit_loss_pct=pnl_pct,
                profit_loss_amount=pnl_amt,
                regime_at_entry=trade['regime_at_entry'],
                bars_held=trade['bars_held'] + 1
            )
            self.closed_trades.append(closed_trade)
            del self.open_trades[symbol]
        
        # Open trades
        if can_trade and signal == 'buy' and symbol not in self.open_trades:
            self.open_trades[symbol] = {
                'entry_date': date,
                'entry_price': ohlcv['close'],
                'capital': self.capital * pos_size,
                'position_size': pos_size,
                'regime_at_entry': 'range' if is_range else 'trend',
                'bars_held': 0
            }
        
        return closed_trade
    
    def get_metrics(self) -> BacktestMetrics:
        """Calculate metrics"""
        trades = self.closed_trades
        total = len(trades)
        
        if total == 0:
            return BacktestMetrics(
                total_trades=0, winning_trades=0, losing_trades=0, win_rate=0.0,
                profit_factor=0.0, total_pnl=0.0, max_drawdown=0.0, avg_win=0.0,
                avg_loss=0.0, sharpe_ratio=0.0, range_blocks=self.range_blocks,
                trades_executed=0, avg_position_size=1.0
            )
        
        wins = [t for t in trades if t.is_win()]
        losses = [t for t in trades if not t.is_win()]
        
        win_rate = len(wins) / total if total > 0 else 0.0
        total_wins = sum(t.profit_loss_amount for t in wins) if wins else 0.0
        total_losses = abs(sum(t.profit_loss_amount for t in losses)) if losses else 0.0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0.0
        
        total_pnl = sum(t.profit_loss_amount for t in trades)
        avg_win = sum(t.profit_loss_amount for t in wins) / len(wins) if wins else 0.0
        avg_loss = sum(t.profit_loss_amount for t in losses) / len(losses) if losses else 0.0
        
        # Drawdown
        equity = self.capital
        eq_vals = [equity]
        for t in trades:
            equity += t.profit_loss_amount
            eq_vals.append(equity)
        
        eq_vals = np.array(eq_vals)
        running_max = np.maximum.accumulate(eq_vals)
        dd = (eq_vals - running_max) / running_max
        max_dd = np.min(dd) if len(dd) > 0 else 0.0
        
        # Sharpe
        pnls = np.array([t.profit_loss_pct for t in trades])
        sharpe = (pnls.mean() / pnls.std() * np.sqrt(252)) if pnls.std() > 0 else 0.0
        
        avg_pos_size = np.mean([t.position_size for t in trades]) if trades else 1.0
        
        return BacktestMetrics(
            total_trades=total,
            winning_trades=len(wins),
            losing_trades=len(losses),
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_pnl=total_pnl,
            max_drawdown=max_dd,
            avg_win=avg_win,
            avg_loss=avg_loss,
            sharpe_ratio=sharpe,
            range_blocks=self.range_blocks,
            trades_executed=total,
            avg_position_size=avg_pos_size
        )


def run_backtest():
    """Main backtest"""
    SYMBOLS = ["INFY", "TCS", "AXIS", "MARUTI", "WIPRO", "SUNPHARMA"]
    START = "2024-01-01"
    END = "2026-06-09"
    
    print(f"\n{'='*80}")
    print("PHASE 3 BACKTEST: Range Policy Effectiveness")
    print(f"{'='*80}")
    print(f"Period: {START} to {END}")
    print(f"Symbols: {', '.join(SYMBOLS)}")
    print(f"{'='*80}\n")
    
    # Load data
    data = {}
    symbol_map = {
        "INFY": "INFY.NS", "TCS": "TCS.NS", "AXIS": "AXISBANK.NS",
        "MARUTI": "MARUTI.NS", "WIPRO": "WIPRO.NS", "SUNPHARMA": "SUNPHARMA.NS"
    }
    
    print("Loading data...")
    for symbol in SYMBOLS:
        try:
            df = yf.download(symbol_map[symbol], start=START, end=END, progress=False)
            if len(df) > 0:
                data[symbol] = df
                print(f"  ✓ {symbol}: {len(df)} bars")
        except Exception as e:
            print(f"  ✗ {symbol}: {e}")
    
    if not data:
        print("❌ No data loaded!")
        return
    
    # Strategies
    strat_with_rp = SMA20Strategy(capital=2_500_000, enable_range_policy=True)
    strat_no_rp = SMA20Strategy(capital=2_500_000, enable_range_policy=False)
    
    # Run
    print(f"\nProcessing {sum(len(df) for df in data.values())} bars...")
    
    for symbol, raw_df in data.items():
        # Handle MultiIndex columns from yfinance
        if isinstance(raw_df.columns, pd.MultiIndex):
            ticker = raw_df.columns.get_level_values(1)[0]
            df = raw_df.copy()
            df.columns = [col[0] for col in df.columns]  # Extract first level only
        else:
            df = raw_df.copy()
        
        for idx in range(1, len(df)):
            date = df.index[idx].strftime('%Y-%m-%d')
            
            ohlcv = {
                'open': float(df['Open'].iloc[idx]),
                'high': float(df['High'].iloc[idx]),
                'low': float(df['Low'].iloc[idx]),
                'close': float(df['Close'].iloc[idx]),
                'volume': int(df['Volume'].iloc[idx]) if 'Volume' in df.columns else 0
            }
            
            hist_df = df.iloc[:idx+1][['High', 'Low', 'Close']].copy()
            hist_df.columns = ['high', 'low', 'close']
            
            strat_with_rp.process_bar(symbol, date, ohlcv, hist_df)
            strat_no_rp.process_bar(symbol, date, ohlcv, hist_df)
    
    # Metrics
    m1 = strat_with_rp.get_metrics()
    m2 = strat_no_rp.get_metrics()
    
    # Report
    print(f"\n{'='*80}")
    print("RESULTS: WITH Range Policy vs WITHOUT")
    print(f"{'='*80}\n")
    
    print("WITH RANGE POLICY (Capital Preservation):")
    print(f"  Trades: {m1.total_trades} executed, {m1.range_blocks} blocked")
    print(f"  Win Rate: {m1.win_rate:.1%}")
    print(f"  Profit Factor: {m1.profit_factor:.2f}")
    print(f"  P&L: ${m1.total_pnl:,.0f}")
    print(f"  Max Drawdown: {m1.max_drawdown:.1%}")
    print(f"  Sharpe: {m1.sharpe_ratio:.2f}\n")
    
    print("WITHOUT RANGE POLICY (Baseline SMA20):")
    print(f"  Trades: {m2.total_trades} executed")
    print(f"  Win Rate: {m2.win_rate:.1%}")
    print(f"  Profit Factor: {m2.profit_factor:.2f}")
    print(f"  P&L: ${m2.total_pnl:,.0f}")
    print(f"  Max Drawdown: {m2.max_drawdown:.1%}")
    print(f"  Sharpe: {m2.sharpe_ratio:.2f}\n")
    
    print("COMPARISON:")
    trade_diff = m1.trades_executed - m2.trades_executed
    wr_diff = (m1.win_rate - m2.win_rate) * 100
    pnl_diff = m1.total_pnl - m2.total_pnl
    dd_diff = (m1.max_drawdown - m2.max_drawdown) * 100
    
    print(f"  Trades: {trade_diff:+d} ({trade_diff/m2.trades_executed*100:+.1f}%)" if m2.trades_executed > 0 else "  Trades: N/A")
    print(f"  Win Rate: {wr_diff:+.1f}%")
    print(f"  P&L: ${pnl_diff:+,.0f}")
    print(f"  Drawdown: {dd_diff:.1f}%  {'✓ Better' if dd_diff < 0 else '✗ Worse'}")
    
    # Save results
    results = {
        'with_range_policy': asdict(m1),
        'without_range_policy': asdict(m2),
        'summary': {
            'period': f"{START} to {END}",
            'symbols': SYMBOLS,
            'total_trades_baseline': m2.total_trades,
            'range_blocks': m1.range_blocks,
            'trades_executed_with_rp': m1.trades_executed,
            'pnl_improvement': pnl_diff,
            'drawdown_improvement': dd_diff
        }
    }
    
    output_file = Path("backtest_reports/phase3_backtest_results_fast.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_file}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    run_backtest()
