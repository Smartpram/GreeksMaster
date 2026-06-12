"""
PHASE 5: LIVE PAPER TRADING SYSTEM
===================================

Objective: Generate daily trading signals on live data and track performance
without executing trades. Validates Phase 4 backtest results in real-world.

Duration: 2-4 weeks
Success Criteria:
  - Paper signal win rate ≥ 40%
  - Real drawdown < 5%
  - Signals match backtest ±5%
  - System stable & reliable

Architecture:
  1. Daily Signal Generation (5 PM IST after market close)
  2. Signal Tracking (date, symbol, price, ADX, etc.)
  3. Outcome Tracking (actual price action vs signal)
  4. Performance Analysis (daily/weekly reports)
  5. Comparison to Backtest (validation)
"""

import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional
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


class SignalType(Enum):
    """Type of signal generated"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class OutcomeStatus(Enum):
    """Status of paper trade outcome"""
    PENDING = "pending"        # Not enough data yet
    WINNING = "winning"        # Price moved in right direction
    LOSING = "losing"          # Price moved in wrong direction
    NEUTRAL = "neutral"        # No clear movement
    CLOSED = "closed"          # Trade closure tracked


@dataclass
class PaperSignal:
    """Paper trading signal"""
    signal_id: str
    timestamp: str          # When signal was generated (5 PM IST)
    symbol: str
    signal_type: str        # BUY, SELL, HOLD
    entry_price: float
    confidence: float       # ADX value (0-100)
    atr_pct: float         # Current volatility
    sma20: float           # SMA20 value
    expected_move_pct: float  # Expected profit target
    
    # Tracking
    tracking_days: int = 0
    current_price: float = 0.0
    current_pnl_pct: float = 0.0
    max_pnl_pct: float = 0.0
    min_pnl_pct: float = 0.0
    status: str = "pending"
    
    # Resolution
    days_to_resolution: int = 0
    final_pnl_pct: float = 0.0
    final_status: str = "pending"
    close_reason: str = ""
    
    def __repr__(self):
        return (
            f"Signal({self.symbol}, {self.signal_type}, "
            f"ADX={self.confidence:.1f}, PNL={self.current_pnl_pct:+.2f}%)"
        )


@dataclass
class DailyReport:
    """Daily paper trading report"""
    date: str
    signals_generated: int
    pending_signals: int
    closed_signals: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_pnl_pct: float
    total_pnl_pct: float
    max_drawdown: float
    
    def __repr__(self):
        return (
            f"Report({self.date}: {self.signals_generated} signals, "
            f"{self.win_rate:.1%} WR, {self.total_pnl_pct:+.2f}% PNL)"
        )


class PaperTradingSystem:
    """
    Live paper trading system
    
    Generates signals daily at 5 PM IST (after market close)
    Tracks actual price movements
    Measures signal quality vs backtest
    """
    
    def __init__(self, symbols: List[str], capital: float = 2_500_000):
        self.symbols = symbols
        self.capital = capital
        self.signals: List[PaperSignal] = []
        self.daily_reports: List[DailyReport] = []
        self.last_signal_date: Dict[str, str] = {}
        
        logger.info(f"Initialized Paper Trading System")
        logger.info(f"Symbols: {symbols}")
        logger.info(f"Capital: ${capital:,.0f}")
    
    def generate_daily_signals(self, date: str) -> List[PaperSignal]:
        """
        Generate signals for given date (5 PM IST market close)
        
        Uses Phase 4 logic:
        1. Check SMA20 crossover
        2. Filter by ADX > 25
        3. Filter by volume > 70% avg
        4. Generate signal
        """
        signals = []
        timestamp = f"{date} 17:00:00"  # 5 PM IST
        
        for symbol in self.symbols:
            # Get data up to this date
            yf_symbol = self._get_yf_symbol(symbol)
            try:
                df = yf.download(yf_symbol, start="2024-01-01", end=date, progress=False)
                
                if len(df) < 22:
                    continue  # Not enough data
                
                # Handle MultiIndex from yfinance
                if isinstance(df.columns, pd.MultiIndex):
                    df_clean = df.copy()
                    df_clean.columns = [col[0] for col in df_clean.columns]
                else:
                    df_clean = df.copy()
                
                # Calculate indicators
                sma20 = self._calc_sma20(df_clean)
                adx = self._calc_adx(df_clean)
                atr_pct = self._calc_atr_pct(df_clean)
                volume_avg = self._calc_volume_avg(df_clean)
                
                # Check filters
                if adx < 25:
                    continue  # ADX too low
                
                if df_clean['Volume'].iloc[-1] < volume_avg * 0.7:
                    continue  # Volume too low
                
                if atr_pct < 0.005:
                    continue  # Market too calm
                
                # Check for SMA20 crossover
                signal_type = self._check_sma20_crossover(df_clean, sma20)
                
                if signal_type == 'hold':
                    continue  # No signal
                
                # Generate signal
                current_price = df_clean['Close'].iloc[-1]
                expected_move = atr_pct * 2  # 2x ATR as expected move
                
                signal = PaperSignal(
                    signal_id=f"{symbol}_{date}_{signal_type}",
                    timestamp=timestamp,
                    symbol=symbol,
                    signal_type=signal_type,
                    entry_price=current_price,
                    confidence=adx,
                    atr_pct=atr_pct,
                    sma20=sma20,
                    expected_move_pct=expected_move
                )
                
                signals.append(signal)
                self.last_signal_date[symbol] = date
                
                logger.info(f"Signal: {signal}")
            
            except Exception as e:
                logger.warning(f"Error generating signal for {symbol}: {e}")
        
        # Store signals
        self.signals.extend(signals)
        
        return signals
    
    def update_signal_outcomes(self, date: str, lookback_days: int = 10):
        """
        Update outcomes for pending signals
        Check if signals have hit profit target, stop loss, or time limit
        """
        yf_data = {}
        
        # Load data for all symbols
        for symbol in self.symbols:
            yf_symbol = self._get_yf_symbol(symbol)
            try:
                df = yf.download(yf_symbol, start="2024-01-01", end=date, progress=False)
                
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [col[0] for col in df.columns]
                
                yf_data[symbol] = df.sort_index()
            except:
                pass
        
        # Update each pending signal
        for signal in self.signals:
            if signal.status == "closed":
                continue
            
            if signal.symbol not in yf_data:
                continue
            
            df = yf_data[signal.symbol]
            
            # Find signal date in data
            try:
                signal_date = pd.Timestamp(signal.timestamp[:10])
                
                # Get price data from signal date onwards
                df_after = df[df.index >= signal_date].copy()
                
                if len(df_after) == 0:
                    continue
                
                # Calculate tracking period
                signal.tracking_days = len(df_after) - 1
                
                if signal.tracking_days <= 0:
                    continue
                
                current_price = df_after['Close'].iloc[-1]
                signal.current_price = current_price
                
                # Calculate P&L based on signal direction
                if signal.signal_type == "buy":
                    signal.current_pnl_pct = ((current_price - signal.entry_price) / 
                                             signal.entry_price)
                else:  # sell
                    signal.current_pnl_pct = ((signal.entry_price - current_price) / 
                                             signal.entry_price)
                
                # Track max/min P&L
                signal.max_pnl_pct = max(signal.max_pnl_pct, signal.current_pnl_pct)
                signal.min_pnl_pct = min(signal.min_pnl_pct, signal.current_pnl_pct)
                
                # Check exit conditions (in order of priority)
                
                # 1. Stop Loss (-1%)
                if signal.current_pnl_pct <= -0.01:
                    signal.status = "closed"
                    signal.final_status = "loss"
                    signal.days_to_resolution = signal.tracking_days
                    signal.final_pnl_pct = -0.01
                    signal.close_reason = "stop_loss"
                
                # 2. Profit Target (+2%)
                elif signal.current_pnl_pct >= 0.02:
                    signal.status = "closed"
                    signal.final_status = "win"
                    signal.days_to_resolution = signal.tracking_days
                    signal.final_pnl_pct = 0.02
                    signal.close_reason = "profit_target"
                
                # 3. Time Stop (10 days)
                elif signal.tracking_days >= 10:
                    signal.status = "closed"
                    signal.final_status = "win" if signal.current_pnl_pct > 0 else "loss"
                    signal.days_to_resolution = signal.tracking_days
                    signal.final_pnl_pct = signal.current_pnl_pct
                    signal.close_reason = "time_stop"
                
                else:
                    signal.status = "pending"
            
            except Exception as e:
                logger.debug(f"Error updating signal for {signal.symbol}: {e}")
                continue
    
    def generate_daily_report(self, date: str) -> Optional[DailyReport]:
        """Generate daily paper trading report"""
        day_signals = [s for s in self.signals if date in s.timestamp]
        
        if not day_signals:
            return None
        
        closed = [s for s in day_signals if s.status == "closed"]
        pending = [s for s in day_signals if s.status == "pending"]
        
        if not closed:
            return DailyReport(
                date=date,
                signals_generated=len(day_signals),
                pending_signals=len(pending),
                closed_signals=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                avg_pnl_pct=0.0,
                total_pnl_pct=0.0,
                max_drawdown=0.0
            )
        
        wins = [s for s in closed if s.final_status == "win"]
        losses = [s for s in closed if s.final_status == "loss"]
        
        win_rate = len(wins) / len(closed) if closed else 0.0
        avg_pnl = np.mean([s.final_pnl_pct for s in closed]) if closed else 0.0
        total_pnl = sum(s.final_pnl_pct for s in closed) if closed else 0.0
        
        report = DailyReport(
            date=date,
            signals_generated=len(day_signals),
            pending_signals=len(pending),
            closed_signals=len(closed),
            winning_trades=len(wins),
            losing_trades=len(losses),
            win_rate=win_rate,
            avg_pnl_pct=avg_pnl,
            total_pnl_pct=total_pnl,
            max_drawdown=min([s.min_pnl_pct for s in closed], default=0.0)
        )
        
        self.daily_reports.append(report)
        return report
    
    def get_metrics_summary(self) -> Dict:
        """Calculate overall paper trading metrics"""
        closed_signals = [s for s in self.signals if s.status == "closed"]
        
        if not closed_signals:
            return {
                'total_signals': len(self.signals),
                'closed_signals': 0,
                'pending_signals': len(self.signals),
                'win_rate': 0.0,
                'avg_pnl_pct': 0.0,
                'total_pnl_pct': 0.0,
                'avg_days_held': 0.0,
                'avg_adx': 0.0
            }
        
        wins = [s for s in closed_signals if s.final_status == "win"]
        
        return {
            'total_signals': len(self.signals),
            'closed_signals': len(closed_signals),
            'pending_signals': len([s for s in self.signals if s.status == "pending"]),
            'win_rate': len(wins) / len(closed_signals) if closed_signals else 0.0,
            'avg_pnl_pct': np.mean([s.final_pnl_pct for s in closed_signals]),
            'total_pnl_pct': sum(s.final_pnl_pct for s in closed_signals),
            'avg_days_held': np.mean([s.days_to_resolution for s in closed_signals]),
            'avg_adx': np.mean([s.confidence for s in self.signals])
        }
    
    # Helper methods
    
    def _get_yf_symbol(self, symbol: str) -> str:
        """Get yfinance symbol mapping"""
        mapping = {
            "INFY": "INFY.NS",
            "TCS": "TCS.NS",
            "AXIS": "AXISBANK.NS",
            "MARUTI": "MARUTI.NS",
            "WIPRO": "WIPRO.NS",
            "SUNPHARMA": "SUNPHARMA.NS"
        }
        return mapping.get(symbol, f"{symbol}.NS")
    
    def _calc_sma20(self, df: pd.DataFrame) -> float:
        """Calculate SMA20"""
        if len(df) >= 20:
            return df['Close'].iloc[-20:].mean()
        return df['Close'].mean()
    
    def _calc_adx(self, df: pd.DataFrame) -> float:
        """Calculate ADX using Wilder's method"""
        if len(df) < 14:
            return 25.0
        
        # Calculate True Range
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift(1))
        low_close = abs(df['Low'] - df['Close'].shift(1))
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()
        
        # Calculate Directional Movements
        up = df['High'].diff()
        down = -df['Low'].diff()
        
        pos_dm = up.where((up > down) & (up > 0), 0)
        neg_dm = down.where((down > up) & (down > 0), 0)
        
        pos_di = (pos_dm.rolling(window=14).mean() / atr * 100).fillna(25)
        neg_di = (neg_dm.rolling(window=14).mean() / atr * 100).fillna(25)
        
        # Calculate DX and ADX
        dx = (abs(pos_di - neg_di) / (pos_di + neg_di) * 100).fillna(25)
        adx = dx.rolling(window=14).mean().fillna(25)
        
        return float(min(100, max(0, adx.iloc[-1])))
    
    def _calc_atr_pct(self, df: pd.DataFrame) -> float:
        """Calculate ATR as percentage"""
        if len(df) < 14:
            return 0.02
        
        tr = np.maximum(
            df['High'].iloc[-1] - df['Low'].iloc[-1],
            np.maximum(
                abs(df['High'].iloc[-1] - df['Close'].iloc[-2]),
                abs(df['Low'].iloc[-1] - df['Close'].iloc[-2])
            )
        )
        atr = tr / 14
        atr_pct = atr / df['Close'].iloc[-1]
        return atr_pct
    
    def _calc_volume_avg(self, df: pd.DataFrame) -> float:
        """Calculate 20-day average volume"""
        if len(df) >= 20:
            return df['Volume'].iloc[-20:].mean()
        return df['Volume'].mean()
    
    def _check_sma20_crossover(self, df: pd.DataFrame, sma20: float) -> str:
        """Check for SMA20 crossover signal"""
        if len(df) < 2:
            return 'hold'
        
        close_curr = df['Close'].iloc[-1]
        close_prev = df['Close'].iloc[-2]
        sma_prev = df['Close'].iloc[-21:-1].mean() if len(df) >= 22 else sma20
        
        if close_prev <= sma_prev and close_curr > sma20:
            return 'buy'
        
        if close_prev >= sma_prev and close_curr < sma20:
            return 'sell'
        
        return 'hold'


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_usage():
    """Example of how to use the paper trading system"""
    
    symbols = ["INFY", "TCS", "AXIS", "MARUTI", "WIPRO", "SUNPHARMA"]
    system = PaperTradingSystem(symbols)
    
    print(f"\n{'='*80}")
    print("PHASE 5: LIVE PAPER TRADING SYSTEM")
    print(f"{'='*80}\n")
    
    # Simulate daily signal generation for last 10 trading days
    today = datetime.now()
    
    for i in range(10):
        test_date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        
        print(f"\nGenerating signals for {test_date}...")
        signals = system.generate_daily_signals(test_date)
        
        if signals:
            print(f"  Generated {len(signals)} signals:")
            for sig in signals:
                print(f"    - {sig}")
        else:
            print(f"  No signals generated")
        
        # Update outcomes
        system.update_signal_outcomes(test_date)
        
        # Generate report
        report = system.generate_daily_report(test_date)
        if report:
            print(f"  Report: {report}")
    
    # Summary
    print(f"\n{'='*80}")
    print("PAPER TRADING SUMMARY")
    print(f"{'='*80}\n")
    
    metrics = system.get_metrics_summary()
    print(f"Total Signals: {metrics['total_signals']}")
    print(f"Closed Signals: {metrics['closed_signals']}")
    print(f"Pending Signals: {metrics['pending_signals']}")
    print(f"Win Rate: {metrics['win_rate']:.1%}")
    print(f"Avg P&L: {metrics['avg_pnl_pct']:+.2%}")
    print(f"Total P&L: {metrics['total_pnl_pct']:+.2%}")
    print(f"Avg Days Held: {metrics['avg_days_held']:.1f}")
    print(f"Avg ADX: {metrics['avg_adx']:.1f}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    try:
        example_usage()
        exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        exit(1)
