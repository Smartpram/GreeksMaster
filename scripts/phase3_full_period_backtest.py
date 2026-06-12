"""
PHASE 3: Full Period Backtest with Range Policy (2024-2025)
=============================================================

Comprehensive backtest comparing:
  1. WITH Range Policy (capital preservation)
  2. WITHOUT Range Policy (baseline SMA20 strategy)

Objective: Validate Range Policy effectiveness for sideways market protection

Key Metrics:
  - Total trades executed vs RANGE blocks
  - Win rate (with vs without)
  - Max drawdown (with vs without)
  - Profit factor, Sharpe ratio
  - % time in RANGE regime
  - Capital preservation during Jul-Sep 2024 (known sideways)

Data Source: yfinance (INFY, TCS, AXIS, MARUTI, WIPRO, SUNPHARMA)
Period: 2024-01-01 to 2026-06-09 (real historical data)
"""

import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional
from enum import Enum
import numpy as np
import pandas as pd
import yfinance as yf
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA STRUCTURES
# ============================================================================

class TradeDirection(Enum):
    """Trade direction"""
    LONG = "long"
    SHORT = "short"


class ExitReason(Enum):
    """Why trade exited"""
    STOP_LOSS = "stop_loss"
    PROFIT_TARGET = "profit_target"
    SMA_BREAKDOWN = "sma_breakdown"
    RANGE_EXIT = "range_exit"
    TIME_EXIT = "time_exit"


class RegimeType(Enum):
    """Market regime"""
    TREND = "trend"
    RANGE = "range"


@dataclass
class Trade:
    """Single trade record"""
    symbol: str
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    direction: TradeDirection
    exit_reason: ExitReason
    position_size: float  # Multiplier from Range Policy (0.0 to 1.0)
    profit_loss_pct: float
    profit_loss_amount: float
    regime_at_entry: RegimeType
    bars_held: int
    
    def is_win(self) -> bool:
        """Returns True if trade was profitable"""
        return self.profit_loss_pct > 0.0
    
    def __repr__(self):
        status = "WIN" if self.is_win() else "LOSS"
        return (
            f"Trade({self.symbol}, {self.entry_date}, "
            f"{self.direction.value}, {self.profit_loss_pct:+.2f}%, "
            f"{status}, {self.exit_reason.value})"
        )


@dataclass
class BacktestMetrics:
    """Performance metrics from backtest"""
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
    # Range Policy specific
    range_blocks: int
    trades_executed: int
    avg_position_size: float
    
    def __repr__(self):
        return (
            f"\n  Total Trades: {self.total_trades} (Executed: {self.trades_executed}, "
            f"Blocked: {self.range_blocks})\n"
            f"  Win Rate: {self.win_rate:.2%} ({self.winning_trades}W/{self.losing_trades}L)\n"
            f"  Profit Factor: {self.profit_factor:.2f}\n"
            f"  Total P&L: ${self.total_pnl:,.2f}\n"
            f"  Max Drawdown: {self.max_drawdown:.2%}\n"
            f"  Avg Win/Loss: ${self.avg_win:,.2f} / ${self.avg_loss:,.2f}\n"
            f"  Sharpe Ratio: {self.sharpe_ratio:.2f}\n"
            f"  Avg Position Size: {self.avg_position_size:.2%}"
        )


@dataclass
class RangeContext:
    """Market regime context"""
    is_range: bool
    confidence: float
    atr_pct: float
    persistence_bars: int
    
    def __repr__(self):
        status = "RANGE" if self.is_range else "TREND"
        return f"{status}(conf={self.confidence:.2f}, atr={self.atr_pct:.4f}, bars={self.persistence_bars})"


# ============================================================================
# RANGE POLICY DETECTOR
# ============================================================================

class SimpleRangeDetector:
    """
    Simplified Range Detection
    
    Detects sideways/range market using:
    1. ATR < 1.5% of close price
    2. ADX < 25
    3. Bollinger Bands width low
    """
    
    def __init__(self, atr_period=14, bb_period=20, adx_period=14):
        self.atr_period = atr_period
        self.bb_period = bb_period
        self.adx_period = adx_period
        self.range_bars_count = 0
    
    def detect(self, df: pd.DataFrame) -> RangeContext:
        """
        Detect if current bar is in RANGE regime
        
        Args:
            df: DataFrame with OHLCV, must have at least atr_period rows
            
        Returns:
            RangeContext with detection info
        """
        if len(df) < self.atr_period:
            return RangeContext(
                is_range=False, confidence=0.0, atr_pct=0.0, persistence_bars=0
            )
        
        current_price = df['close'].iloc[-1]
        
        # 1. Calculate ATR
        atr = self._calc_atr(df)
        atr_pct = atr / current_price
        is_low_vol = atr_pct < 0.015  # < 1.5%
        
        # 2. Calculate ADX
        adx = self._calc_adx(df)
        weak_trend = adx < 25
        
        # 3. Calculate Bollinger Bands width
        bb_width = self._calc_bb_width(df)
        bb_squeeze = bb_width < atr_pct * 1.5
        
        # Composite score
        score = 0.0
        if is_low_vol:
            score += 0.4
        if weak_trend:
            score += 0.3
        if bb_squeeze:
            score += 0.3
        
        is_range = score >= 0.6
        
        # Track persistence
        if is_range:
            self.range_bars_count += 1
        else:
            self.range_bars_count = 0
        
        return RangeContext(
            is_range=is_range,
            confidence=score,
            atr_pct=atr_pct,
            persistence_bars=self.range_bars_count
        )
    
    def _calc_atr(self, df: pd.DataFrame) -> float:
        """Calculate ATR"""
        df = df.copy()
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        atr = df['tr'].rolling(self.atr_period).mean().iloc[-1]
        return atr if not np.isnan(atr) else df['high'].iloc[-1] - df['low'].iloc[-1]
    
    def _calc_adx(self, df: pd.DataFrame) -> float:
        """Simplified ADX calculation"""
        df = df.copy()
        df['up'] = df['high'].diff()
        df['dn'] = -df['low'].diff()
        
        df['pdm'] = df['up'].apply(lambda x: x if x > 0 else 0)
        df['ndm'] = df['dn'].apply(lambda x: x if x > 0 else 0)
        
        atr = self._calc_atr(df)
        pdm = df['pdm'].rolling(self.adx_period).mean().iloc[-1]
        ndm = df['ndm'].rolling(self.adx_period).mean().iloc[-1]
        
        di_plus = (pdm / atr * 100) if atr > 0 else 0
        di_minus = (ndm / atr * 100) if atr > 0 else 0
        di_diff = abs(di_plus - di_minus)
        di_sum = di_plus + di_minus
        
        adx = (di_diff / di_sum * 100) if di_sum > 0 else 50
        return adx
    
    def _calc_bb_width(self, df: pd.DataFrame) -> float:
        """Calculate Bollinger Bands width"""
        sma = df['close'].rolling(self.bb_period).mean()
        std = df['close'].rolling(self.bb_period).std()
        
        upper = sma + (std * 2.0)
        lower = sma - (std * 2.0)
        
        width = (upper - lower).iloc[-1]
        return width if not np.isnan(width) else 0.0


# ============================================================================
# SMA20 STRATEGY
# ============================================================================

class SMA20Strategy:
    """
    Classic SMA20 trend-following strategy
    
    Entry: Price crosses above SMA20
    Exit:  Price crosses below SMA20 (or stop-loss / profit target)
    """
    
    def __init__(self, sma_period=20, capital=1_000_000, enable_range_policy=False):
        self.sma_period = sma_period
        self.capital = capital
        self.enable_range_policy = enable_range_policy
        self.range_detector = SimpleRangeDetector()
        
        # Trade tracking
        self.open_trades: Dict[str, Dict] = {}
        self.closed_trades: List[Trade] = []
        
        # Stats
        self.equity_curve: List[float] = []
        self.range_blocks = 0
    
    def calculate_sma(self, df: pd.DataFrame) -> pd.Series:
        """Calculate SMA20"""
        return df['close'].rolling(self.sma_period).mean()
    
    def generate_signals(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Generate buy/sell signals from SMA20 crossover
        
        Returns:
            {
                'action': 'buy'|'sell'|'hold',
                'signal_strength': 0.0-1.0,
                'reason': str,
                'sma20': float
            }
        """
        if len(df) < self.sma_period + 1:
            return {'action': 'hold', 'signal_strength': 0.0, 'reason': 'Insufficient data', 'sma20': 0.0}
        
        sma = self.calculate_sma(df)
        close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-2]
        sma_current = sma.iloc[-1]
        sma_prev = sma.iloc[-2]
        
        if np.isnan(sma_current):
            return {'action': 'hold', 'signal_strength': 0.0, 'reason': 'SMA nan', 'sma20': 0.0}
        
        # BUY: Price crosses above SMA20
        if prev_close <= sma_prev and close > sma_current:
            signal_strength = min(1.0, abs(close - sma_current) / close)
            return {
                'action': 'buy',
                'signal_strength': signal_strength,
                'reason': 'SMA20 bullish crossover',
                'sma20': sma_current
            }
        
        # SELL: Price crosses below SMA20
        if prev_close >= sma_prev and close < sma_current:
            signal_strength = min(1.0, abs(sma_current - close) / close)
            return {
                'action': 'sell',
                'signal_strength': signal_strength,
                'reason': 'SMA20 bearish crossover',
                'sma20': sma_current
            }
        
        return {'action': 'hold', 'signal_strength': 0.0, 'reason': 'No crossover', 'sma20': sma_current}
    
    def process_bar(self, symbol: str, date: str, ohlcv: Dict, df: pd.DataFrame) -> Optional[Trade]:
        """
        Process one bar of data
        
        Returns:
            Closed trade if any, else None
        """
        closed_trade = None
        
        # Check Range Policy
        range_context = self.range_detector.detect(df)
        position_size_factor = 1.0
        should_trade = True
        
        if self.enable_range_policy and range_context.is_range:
            if range_context.persistence_bars >= 5:
                # Confirmed RANGE: BLOCK
                should_trade = False
                position_size_factor = 0.0
                self.range_blocks += 1
            elif range_context.persistence_bars < 5:
                # Early RANGE: 50% size
                position_size_factor = 0.5
        
        # Generate signals
        signal = self.generate_signals(df, symbol)
        
        # Close open trades
        if symbol in self.open_trades and signal['action'] == 'sell':
            trade_data = self.open_trades[symbol]
            profit_loss_pct = (ohlcv['close'] - trade_data['entry_price']) / trade_data['entry_price']
            profit_loss_amt = profit_loss_pct * trade_data['capital']
            
            closed_trade = Trade(
                symbol=symbol,
                entry_date=trade_data['entry_date'],
                entry_price=trade_data['entry_price'],
                exit_date=date,
                exit_price=ohlcv['close'],
                direction=TradeDirection.LONG,
                exit_reason=ExitReason.SMA_BREAKDOWN,
                position_size=trade_data['position_size'],
                profit_loss_pct=profit_loss_pct,
                profit_loss_amount=profit_loss_amt,
                regime_at_entry=trade_data['regime_at_entry'],
                bars_held=trade_data['bars_held'] + 1
            )
            self.closed_trades.append(closed_trade)
            del self.open_trades[symbol]
        
        # Open new trades
        if should_trade and signal['action'] == 'buy' and symbol not in self.open_trades:
            self.open_trades[symbol] = {
                'entry_date': date,
                'entry_price': ohlcv['close'],
                'capital': self.capital * position_size_factor,
                'position_size': position_size_factor,
                'regime_at_entry': RegimeType.RANGE if range_context.is_range else RegimeType.TREND,
                'bars_held': 0
            }
        
        return closed_trade
    
    def get_metrics(self) -> BacktestMetrics:
        """Calculate performance metrics"""
        trades = self.closed_trades
        total_trades = len(trades)
        
        if total_trades == 0:
            return BacktestMetrics(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                profit_factor=0.0,
                total_pnl=0.0,
                max_drawdown=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                sharpe_ratio=0.0,
                range_blocks=self.range_blocks,
                trades_executed=total_trades,
                avg_position_size=1.0
            )
        
        wins = [t for t in trades if t.is_win()]
        losses = [t for t in trades if not t.is_win()]
        
        winning_trades = len(wins)
        losing_trades = len(losses)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        # Profit factor
        total_wins = sum(t.profit_loss_amount for t in wins) if wins else 0.0
        total_losses = abs(sum(t.profit_loss_amount for t in losses)) if losses else 0.0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0.0
        
        # Total P&L
        total_pnl = sum(t.profit_loss_amount for t in trades)
        
        # Avg win/loss
        avg_win = sum(t.profit_loss_amount for t in wins) / len(wins) if wins else 0.0
        avg_loss = sum(t.profit_loss_amount for t in losses) / len(losses) if losses else 0.0
        
        # Max drawdown (simplified)
        equity = self.capital
        equity_vals = [equity]
        for trade in trades:
            equity += trade.profit_loss_amount
            equity_vals.append(equity)
        
        equity_vals = np.array(equity_vals)
        running_max = np.maximum.accumulate(equity_vals)
        drawdown = (equity_vals - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        # Sharpe ratio (simplified)
        pnls = np.array([t.profit_loss_pct for t in trades])
        if len(pnls) > 1 and pnls.std() > 0:
            sharpe = (pnls.mean() / pnls.std()) * np.sqrt(252)
        else:
            sharpe = 0.0
        
        avg_position_size = np.mean([t.position_size for t in trades]) if trades else 1.0
        
        return BacktestMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_pnl=total_pnl,
            max_drawdown=max_drawdown,
            avg_win=avg_win,
            avg_loss=avg_loss,
            sharpe_ratio=sharpe,
            range_blocks=self.range_blocks,
            trades_executed=total_trades,
            avg_position_size=avg_position_size
        )


# ============================================================================
# MAIN BACKTEST ENGINE
# ============================================================================

class Phase3Backtest:
    """
    Full period backtest with Range Policy comparison
    """
    
    def __init__(self, symbols: List[str], start_date: str, end_date: str, capital: float = 1_000_000):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.capital = capital
        
        self.strategy_with_range = SMA20Strategy(capital=capital, enable_range_policy=True)
        self.strategy_without_range = SMA20Strategy(capital=capital, enable_range_policy=False)
    
    def load_data(self) -> Dict[str, pd.DataFrame]:
        """Load yfinance data for all symbols"""
        data = {}
        
        # Symbol mappings for NSE
        symbol_map = {
            "INFY": "INFY.NS",
            "TCS": "TCS.NS",
            "AXIS": "AXISBANK.NS",  # Correct symbol for Axis Bank
            "MARUTI": "MARUTI.NS",
            "WIPRO": "WIPRO.NS",
            "SUNPHARMA": "SUNPHARMA.NS"
        }
        
        for symbol in self.symbols:
            yf_symbol = symbol_map.get(symbol, f"{symbol}.NS")
            
            try:
                logger.info(f"Loading {symbol}...")
                df = yf.download(yf_symbol, start=self.start_date, end=self.end_date, progress=False)
                
                if len(df) > 0:
                    data[symbol] = df.copy()
                    logger.info(f"✓ {symbol}: {len(df)} bars loaded")
                else:
                    logger.warning(f"✗ {symbol}: No data returned")
            except Exception as e:
                logger.error(f"✗ {symbol}: {e}")
        
        return data
    
    def run(self) -> Dict:
        """Run full backtest comparison"""
        logger.info(f"Loading data for {self.symbols}...")
        data = self.load_data()
        
        if not data:
            logger.error("No data loaded!")
            return {}
        
        logger.info(f"\nRunning backtest...")
        total_bars = 0
        
        for symbol in self.symbols:
            if symbol not in data:
                continue
            
            raw_df = data[symbol]
            total_bars += len(raw_df)
            
            logger.info(f"\n{symbol}: Processing {len(raw_df)} bars...")
            
            for idx in range(len(raw_df)):
                date_val = raw_df.index[idx]
                if hasattr(date_val, 'strftime'):
                    date = date_val.strftime('%Y-%m-%d')
                else:
                    date = str(date_val).split()[0]
                
                ohlcv = {
                    'open': float(raw_df['Open'].iloc[idx]),
                    'high': float(raw_df['High'].iloc[idx]),
                    'low': float(raw_df['Low'].iloc[idx]),
                    'close': float(raw_df['Close'].iloc[idx]),
                    'volume': int(raw_df['Volume'].iloc[idx]) if 'Volume' in raw_df.columns else 0
                }
                
                # Get historical data up to this point
                hist_df = raw_df.iloc[:idx+1][['High', 'Low', 'Close', 'Volume']].copy()
                hist_df.columns = ['high', 'low', 'close', 'volume']
                
                # Process with Range Policy
                self.strategy_with_range.process_bar(symbol, date, ohlcv, hist_df)
                
                # Process without Range Policy
                self.strategy_without_range.process_bar(symbol, date, ohlcv, hist_df)
        
        logger.info(f"\nProcessed {total_bars} bars across {len(data)} symbols")
        
        # Get metrics
        metrics_with = self.strategy_with_range.get_metrics()
        metrics_without = self.strategy_without_range.get_metrics()
        
        return {
            'with_range_policy': asdict(metrics_with),
            'without_range_policy': asdict(metrics_without),
            'summary': {
                'period': f"{self.start_date} to {self.end_date}",
                'symbols': self.symbols,
                'total_bars_processed': total_bars,
                'initial_capital': self.capital
            }
        }


# ============================================================================
# REPORTING
# ============================================================================

def print_comparison(results: Dict):
    """Print backtest comparison"""
    if not results:
        print("No results to display")
        return
    
    print("\n" + "="*80)
    print("PHASE 3 BACKTEST RESULTS: Range Policy Effectiveness")
    print("="*80)
    
    print(f"\nPeriod: {results['summary']['period']}")
    print(f"Symbols: {', '.join(results['summary']['symbols'])}")
    print(f"Initial Capital: ${results['summary']['initial_capital']:,.0f}")
    print(f"Total Bars: {results['summary']['total_bars_processed']}")
    
    with_rp = results['with_range_policy']
    without_rp = results['without_range_policy']
    
    print("\n" + "-"*80)
    print("WITH RANGE POLICY (Capital Preservation)")
    print("-"*80)
    print(f"  Total Trades: {with_rp['total_trades']}")
    print(f"  RANGE Blocks: {with_rp['range_blocks']}")
    print(f"  Win Rate: {with_rp['win_rate']:.2%}")
    print(f"  Profit Factor: {with_rp['profit_factor']:.2f}")
    print(f"  Total P&L: ${with_rp['total_pnl']:,.2f}")
    print(f"  Max Drawdown: {with_rp['max_drawdown']:.2%}")
    print(f"  Sharpe Ratio: {with_rp['sharpe_ratio']:.2f}")
    print(f"  Avg Position Size: {with_rp['avg_position_size']:.2%}")
    
    print("\n" + "-"*80)
    print("WITHOUT RANGE POLICY (Baseline SMA20)")
    print("-"*80)
    print(f"  Total Trades: {without_rp['total_trades']}")
    print(f"  Win Rate: {without_rp['win_rate']:.2%}")
    print(f"  Profit Factor: {without_rp['profit_factor']:.2f}")
    print(f"  Total P&L: ${without_rp['total_pnl']:,.2f}")
    print(f"  Max Drawdown: {without_rp['max_drawdown']:.2%}")
    print(f"  Sharpe Ratio: {without_rp['sharpe_ratio']:.2f}")
    
    print("\n" + "-"*80)
    print("COMPARISON (Range Policy vs Baseline)")
    print("-"*80)
    
    trade_diff = with_rp['total_trades'] - without_rp['total_trades']
    wr_diff = (with_rp['win_rate'] - without_rp['win_rate']) * 100
    pnl_diff = with_rp['total_pnl'] - without_rp['total_pnl']
    dd_diff = (with_rp['max_drawdown'] - without_rp['max_drawdown']) * 100
    
    print(f"  Trades Reduction: {trade_diff:+d} ({trade_diff/without_rp['total_trades']*100:+.1f}%)")
    print(f"  Win Rate Change: {wr_diff:+.1f}%")
    print(f"  P&L Difference: ${pnl_diff:+,.2f}")
    print(f"  Max Drawdown Improvement: {dd_diff:.1f}%  {'✓' if dd_diff < 0 else '✗'}")
    
    print("\n" + "="*80)
    print("INTERPRETATION")
    print("="*80)
    
    if dd_diff < -0.5:
        print("✓ Range Policy IMPROVED drawdown control (less downside)")
    elif dd_diff > 0.5:
        print("✗ Range Policy WORSENED drawdown (needs adjustment)")
    else:
        print("~ Range Policy drawdown similar to baseline")
    
    if pnl_diff > 0:
        print("✓ Range Policy increased profits (avoided bad trades)")
    elif pnl_diff < -1000:
        print("✗ Range Policy reduced profits significantly")
    else:
        print("~ Range Policy profits similar to baseline")
    
    print("\n✅ FINDINGS SAVED TO: phase3_backtest_results.json")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Test symbols
    SYMBOLS = ["INFY", "TCS", "AXIS", "MARUTI", "WIPRO", "SUNPHARMA"]
    
    # Period: 2024-2025 (recent 2 years)
    START_DATE = "2024-01-01"
    END_DATE = "2026-06-09"
    
    print(f"\n{'='*80}")
    print("PHASE 3 BACKTEST WITH RANGE POLICY")
    print(f"{'='*80}")
    print(f"Symbols: {SYMBOLS}")
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Strategy: SMA20 Trend Following")
    print(f"Comparison: WITH vs WITHOUT Range Policy")
    print(f"{'='*80}\n")
    
    # Run backtest
    backtest = Phase3Backtest(
        symbols=SYMBOLS,
        start_date=START_DATE,
        end_date=END_DATE,
        capital=2_500_000  # ₹25 lakhs (typical account size)
    )
    
    results = backtest.run()
    
    # Print results
    print_comparison(results)
    
    # Save results
    output_file = Path("backtest_reports/phase3_backtest_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to: {output_file}")
