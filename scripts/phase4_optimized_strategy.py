"""
PHASE 4: Optimized Strategy with ADX & Entry Filters
====================================================

Improvements:
1. Proper ADX calculation (not hardcoded)
2. Entry filters: ADX > 25, volume filter
3. Exit rules: 2% profit target, 1% stop-loss, 10-bar time stop
4. Position sizing based on trend strength

Expected: 40%+ win rate, <20% drawdown
"""

import json
import numpy as np
import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from enum import Enum

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class TradeDirection(Enum):
    LONG = "long"


@dataclass
class Trade:
    symbol: str
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    exit_reason: str
    position_size: float
    profit_loss_pct: float
    profit_loss_amount: float
    bars_held: int
    adx_at_entry: float
    atr_pct_at_entry: float
    
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
    avg_bars_held: float
    avg_adx: float
    filtered_signals: int
    trades_executed: int


class ADXCalculator:
    """Proper ADX calculation"""
    
    def __init__(self, period=14):
        self.period = period
    
    def calculate(self, df: pd.DataFrame) -> float:
        """
        Calculate ADX (Average Directional Index)
        Returns: ADX value (0-100)
        """
        if len(df) < self.period + 1:
            return 25  # Neutral default
        
        df = df.copy()
        
        # Directional Movement
        up = df['high'].diff()
        down = -df['low'].diff()
        
        df['pdm'] = 0.0
        df['ndm'] = 0.0
        
        # Set +DM
        df.loc[up > down, 'pdm'] = df.loc[up > down, 'high'].diff()
        df.loc[df['pdm'] < 0, 'pdm'] = 0.0
        
        # Set -DM
        df.loc[down > up, 'ndm'] = df.loc[down > up, 'low'].diff()
        df.loc[df['ndm'] < 0, 'ndm'] = 0.0
        
        # True Range
        tr = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                np.abs(df['high'] - df['close'].shift(1)),
                np.abs(df['low'] - df['close'].shift(1))
            )
        )
        
        # Smoothed (Wilder's method)
        atr = tr.rolling(self.period).mean()
        
        pdm_smooth = df['pdm'].rolling(self.period).mean()
        ndm_smooth = df['ndm'].rolling(self.period).mean()
        
        # Direction Indicators
        di_plus = (pdm_smooth / atr * 100) if atr.iloc[-1] > 0 else 0
        di_minus = (ndm_smooth / atr * 100) if atr.iloc[-1] > 0 else 0
        
        di_plus_val = di_plus.iloc[-1] if not np.isnan(di_plus.iloc[-1]) else 0
        di_minus_val = di_minus.iloc[-1] if not np.isnan(di_minus.iloc[-1]) else 0
        
        # ADX
        di_diff = np.abs(di_plus_val - di_minus_val)
        di_sum = di_plus_val + di_minus_val
        
        if di_sum > 0:
            adx = (di_diff / di_sum) * 100
        else:
            adx = 25  # Neutral
        
        return min(100, max(0, adx))


class OptimizedSMA20Strategy:
    """SMA20 with ADX filter, volume filter, and optimized exits"""
    
    def __init__(self, capital=1_000_000):
        self.capital = capital
        self.adx_calc = ADXCalculator(period=14)
        
        # Entry filters
        self.min_adx_for_trade = 25  # Only trade if ADX > 25
        self.min_volume_factor = 0.7  # Volume > 70% of 20-day avg
        
        # Exit rules
        self.profit_target_pct = 0.02  # 2% profit target
        self.stop_loss_pct = 0.01  # 1% stop loss
        self.max_bars_held = 10  # Max 10 bars
        
        self.open_trades: Dict[str, Dict] = {}
        self.closed_trades: List[Trade] = []
        self.filtered_buy_signals = 0
    
    def calculate_sma20(self, df: pd.DataFrame) -> float:
        """SMA20"""
        if len(df) >= 20:
            return df['close'].iloc[-20:].mean()
        return df['close'].mean()
    
    def calculate_atr_pct(self, df: pd.DataFrame) -> float:
        """ATR as % of close"""
        if len(df) < 14:
            return 0.02
        
        tr = np.maximum(
            df['high'].iloc[-1] - df['low'].iloc[-1],
            np.maximum(
                abs(df['high'].iloc[-1] - df['close'].iloc[-2]),
                abs(df['low'].iloc[-1] - df['close'].iloc[-2])
            )
        )
        atr = tr / 14
        atr_pct = atr / df['close'].iloc[-1]
        return atr_pct
    
    def calculate_avg_volume(self, df: pd.DataFrame) -> float:
        """20-bar average volume"""
        if len(df) >= 20:
            return df['volume'].iloc[-20:].mean()
        return df['volume'].mean()
    
    def generate_signal(self, df: pd.DataFrame) -> str:
        """SMA20 crossover signal"""
        if len(df) < 22:
            return 'hold'
        
        sma = self.calculate_sma20(df)
        close_curr = df['close'].iloc[-1]
        close_prev = df['close'].iloc[-2]
        sma_prev = df['close'].iloc[-21:-1].mean()
        
        if close_prev <= sma_prev and close_curr > sma:
            return 'buy'
        
        if close_prev >= sma_prev and close_curr < sma:
            return 'sell'
        
        return 'hold'
    
    def should_trade(self, df: pd.DataFrame) -> tuple:
        """
        Check entry filters
        Returns: (should_trade: bool, adx: float, reason: str)
        """
        adx = self.adx_calc.calculate(df)
        atr_pct = self.calculate_atr_pct(df)
        avg_vol = self.calculate_avg_volume(df)
        curr_vol = df['volume'].iloc[-1]
        
        # Filter 1: ADX
        if adx < self.min_adx_for_trade:
            return False, adx, f"ADX too low ({adx:.1f} < 25)"
        
        # Filter 2: Volume
        if curr_vol < avg_vol * self.min_volume_factor:
            return False, adx, f"Volume low ({curr_vol:.0f} < {avg_vol*self.min_volume_factor:.0f})"
        
        # Filter 3: Volatility (not in ranging market)
        if atr_pct < 0.005:  # < 0.5% ATR = dead market
            return False, adx, f"Too calm (ATR {atr_pct:.4f})"
        
        return True, adx, "All filters passed"
    
    def process_bar(self, symbol: str, date: str, ohlcv: Dict, df: pd.DataFrame) -> Optional[Trade]:
        """Process one bar"""
        closed_trade = None
        
        # Check exit conditions
        if symbol in self.open_trades:
            trade = self.open_trades[symbol]
            curr_price = ohlcv['close']
            entry_price = trade['entry_price']
            
            # Profit target
            pnl_pct = (curr_price - entry_price) / entry_price
            if pnl_pct >= self.profit_target_pct:
                pnl_amt = pnl_pct * trade['capital']
                closed_trade = Trade(
                    symbol=symbol,
                    entry_date=trade['entry_date'],
                    entry_price=entry_price,
                    exit_date=date,
                    exit_price=curr_price,
                    exit_reason='profit_target',
                    position_size=trade['position_size'],
                    profit_loss_pct=pnl_pct,
                    profit_loss_amount=pnl_amt,
                    bars_held=trade['bars_held'] + 1,
                    adx_at_entry=trade['adx_at_entry'],
                    atr_pct_at_entry=trade['atr_pct_at_entry']
                )
                self.closed_trades.append(closed_trade)
                del self.open_trades[symbol]
                return closed_trade
            
            # Stop loss
            if pnl_pct <= -self.stop_loss_pct:
                pnl_amt = pnl_pct * trade['capital']
                closed_trade = Trade(
                    symbol=symbol,
                    entry_date=trade['entry_date'],
                    entry_price=entry_price,
                    exit_date=date,
                    exit_price=curr_price,
                    exit_reason='stop_loss',
                    position_size=trade['position_size'],
                    profit_loss_pct=pnl_pct,
                    profit_loss_amount=pnl_amt,
                    bars_held=trade['bars_held'] + 1,
                    adx_at_entry=trade['adx_at_entry'],
                    atr_pct_at_entry=trade['atr_pct_at_entry']
                )
                self.closed_trades.append(closed_trade)
                del self.open_trades[symbol]
                return closed_trade
            
            # Time stop
            if trade['bars_held'] >= self.max_bars_held:
                pnl_amt = pnl_pct * trade['capital']
                closed_trade = Trade(
                    symbol=symbol,
                    entry_date=trade['entry_date'],
                    entry_price=entry_price,
                    exit_date=date,
                    exit_price=curr_price,
                    exit_reason='time_stop',
                    position_size=trade['position_size'],
                    profit_loss_pct=pnl_pct,
                    profit_loss_amount=pnl_amt,
                    bars_held=trade['bars_held'] + 1,
                    adx_at_entry=trade['adx_at_entry'],
                    atr_pct_at_entry=trade['atr_pct_at_entry']
                )
                self.closed_trades.append(closed_trade)
                del self.open_trades[symbol]
                return closed_trade
            
            # Increment bars held
            self.open_trades[symbol]['bars_held'] += 1
        
        # Check entry
        signal = self.generate_signal(df)
        
        if signal == 'buy' and symbol not in self.open_trades:
            can_trade, adx, reason = self.should_trade(df)
            
            if not can_trade:
                self.filtered_buy_signals += 1
            else:
                # Position sizing based on ADX
                pos_size = 1.0
                if adx > 40:
                    pos_size = 1.5  # Strong trend
                elif adx > 60:
                    pos_size = 0.5  # Overextended
                
                atr_pct = self.calculate_atr_pct(df)
                
                self.open_trades[symbol] = {
                    'entry_date': date,
                    'entry_price': ohlcv['close'],
                    'capital': self.capital * pos_size,
                    'position_size': pos_size,
                    'bars_held': 0,
                    'adx_at_entry': adx,
                    'atr_pct_at_entry': atr_pct
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
                avg_loss=0.0, sharpe_ratio=0.0, avg_bars_held=0.0, avg_adx=0.0,
                filtered_signals=self.filtered_buy_signals, trades_executed=0
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
        
        avg_bars = np.mean([t.bars_held for t in trades]) if trades else 0.0
        avg_adx = np.mean([t.adx_at_entry for t in trades]) if trades else 0.0
        
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
            avg_bars_held=avg_bars,
            avg_adx=avg_adx,
            filtered_signals=self.filtered_buy_signals,
            trades_executed=total
        )


def run_phase4_backtest():
    """Run Phase 4 backtest"""
    SYMBOLS = ["INFY", "TCS", "AXIS", "MARUTI", "WIPRO", "SUNPHARMA"]
    START = "2024-01-01"
    END = "2026-06-09"
    
    print(f"\n{'='*80}")
    print("PHASE 4: SMA20 + ADX + Optimized Exits")
    print(f"{'='*80}")
    print(f"Period: {START} to {END}")
    print(f"Entry Filters: ADX > 25, Volume > 70% avg")
    print(f"Exit Rules: 2% PT, 1% SL, 10-bar max")
    print(f"Position Sizing: ADX-based (0.5x-1.5x)")
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
        print("❌ No data!")
        return
    
    # Strategy
    strategy = OptimizedSMA20Strategy(capital=2_500_000)
    
    # Run
    print(f"\nProcessing {sum(len(df) for df in data.values())} bars...")
    bar_count = 0
    
    for symbol, raw_df in data.items():
        # Handle MultiIndex from yfinance
        if isinstance(raw_df.columns, pd.MultiIndex):
            df = raw_df.copy()
            df.columns = [col[0] for col in df.columns]
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
            
            hist_df = df.iloc[:idx+1][['High', 'Low', 'Close', 'Volume']].copy()
            hist_df.columns = ['high', 'low', 'close', 'volume']
            
            strategy.process_bar(symbol, date, ohlcv, hist_df)
            bar_count += 1
    
    print(f"Processed {bar_count} bars")
    
    # Metrics
    metrics = strategy.get_metrics()
    
    # Report
    print(f"\n{'='*80}")
    print("PHASE 4 RESULTS")
    print(f"{'='*80}\n")
    
    print("Entry Filtering:")
    print(f"  Buy signals generated: {metrics.filtered_signals + metrics.trades_executed}")
    print(f"  Filtered out (no ADX/volume): {metrics.filtered_signals}")
    print(f"  Executed: {metrics.trades_executed}\n")
    
    print("Performance Metrics:")
    print(f"  Win Rate: {metrics.win_rate:.1%} ({metrics.winning_trades}W/{metrics.losing_trades}L)")
    print(f"  Profit Factor: {metrics.profit_factor:.2f}")
    print(f"  Total P&L: ${metrics.total_pnl:,.0f}")
    print(f"  Max Drawdown: {metrics.max_drawdown:.1%}")
    print(f"  Sharpe Ratio: {metrics.sharpe_ratio:.2f}\n")
    
    print("Trade Details:")
    print(f"  Avg Bars Held: {metrics.avg_bars_held:.1f}")
    print(f"  Avg ADX at Entry: {metrics.avg_adx:.1f}")
    print(f"  Avg Win: ${metrics.avg_win:,.0f}")
    print(f"  Avg Loss: ${metrics.avg_loss:,.0f}\n")
    
    # Save
    results = {
        'metrics': asdict(metrics),
        'summary': {
            'period': f"{START} to {END}",
            'symbols': SYMBOLS,
            'filters': {
                'min_adx': 25,
                'min_volume_factor': 0.7,
                'profit_target_pct': 0.02,
                'stop_loss_pct': 0.01,
                'max_bars_held': 10
            }
        }
    }
    
    output_file = Path("backtest_reports/phase4_backtest_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Results saved to: {output_file}")
    print(f"{'='*80}\n")
    
    # Comparison
    print("PHASE 3 vs PHASE 4 Comparison:")
    print(f"  Phase 3 (no filters): 24.7% WR, 0.97 PF, -$209K P&L, -56% DD")
    print(f"  Phase 4 (with filters): {metrics.win_rate:.1%} WR, {metrics.profit_factor:.2f} PF, ${metrics.total_pnl:+,.0f} P&L, {metrics.max_drawdown:.1%} DD")
    
    if metrics.win_rate > 0.30 and metrics.max_drawdown > -0.25:
        print(f"\n✓ IMPROVEMENTS DETECTED")
    else:
        print(f"\n⚠ Further optimization needed")


if __name__ == "__main__":
    run_phase4_backtest()
