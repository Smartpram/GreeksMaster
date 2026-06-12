"""
PHASE 5: ENHANCED LIVE PAPER TRADING SYSTEM
===========================================

Objective: Generate daily trading signals and track their performance
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
from typing import Dict, List, Optional, Tuple
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


@dataclass
class PaperSignal:
    """Paper trading signal with real-time tracking"""
    signal_id: str
    entry_date: str          # When signal was generated
    symbol: str
    signal_type: str         # BUY, SELL
    entry_price: float
    confidence: float        # ADX value (0-100)
    atr_pct: float          # Current volatility
    sma20: float            # SMA20 value
    
    # Tracking
    status: str = "pending"      # pending, closed
    current_price: float = 0.0
    current_pnl_pct: float = 0.0
    max_pnl_pct: float = 0.0
    min_pnl_pct: float = 0.0
    
    # Resolution
    days_held: int = 0
    final_pnl_pct: float = 0.0
    final_status: str = "pending"  # win, loss
    close_reason: str = ""         # profit_target, stop_loss, time_stop
    close_date: Optional[str] = None
    
    def __repr__(self):
        status_icon = "✓" if self.final_status == "win" else "✗" if self.final_status == "loss" else "⏳"
        return (
            f"{status_icon} {self.symbol} {self.signal_type.upper()} "
            f"@{self.entry_price:.2f} (ADX={self.confidence:.0f}) "
            f"PNL={self.current_pnl_pct:+.2%}"
        )


class PaperTradingEngine:
    """
    Enhanced paper trading engine
    
    Features:
    - Proper signal generation using Phase 4 logic
    - Real-time P&L tracking
    - Automatic signal closure
    - Daily/weekly reporting
    """
    
    def __init__(self, symbols: List[str], capital: float = 2_500_000):
        self.symbols = symbols
        self.capital = capital
        self.signals: Dict[str, PaperSignal] = {}  # signal_id -> signal
        self.daily_signals: Dict[str, List[str]] = {}  # date -> [signal_ids]
        self.cache: Dict[str, pd.DataFrame] = {}  # symbol -> dataframe
        
        logger.info(f"Initialized Paper Trading Engine")
        logger.info(f"Symbols: {symbols}")
        logger.info(f"Capital: ${capital:,.0f}")
    
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
    
    def _load_data(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """Load price data with caching"""
        cache_key = f"{symbol}_{start}_{end}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            yf_symbol = self._get_yf_symbol(symbol)
            df = yf.download(yf_symbol, start=start, end=end, progress=False)
            
            # Handle MultiIndex
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]
            
            # Ensure sorted index
            df = df.sort_index()
            
            self.cache[cache_key] = df
            return df
        
        except Exception as e:
            logger.warning(f"Failed to load data for {symbol}: {e}")
            return pd.DataFrame()
    
    def _calc_adx(self, df: pd.DataFrame) -> float:
        """Calculate ADX using Wilder's method"""
        if len(df) < 14:
            return 25.0
        
        try:
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
        except:
            return 25.0
    
    def _calc_atr_pct(self, df: pd.DataFrame) -> float:
        """Calculate ATR as percentage"""
        try:
            if len(df) < 14:
                return 0.02
            
            high_low = df['High'] - df['Low']
            high_close = abs(df['High'] - df['Close'].shift(1))
            low_close = abs(df['Low'] - df['Close'].shift(1))
            
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean()
            atr_pct = atr.iloc[-1] / df['Close'].iloc[-1]
            
            return float(min(0.05, max(0.005, atr_pct)))
        except:
            return 0.02
    
    def _calc_sma20(self, df: pd.DataFrame) -> float:
        """Calculate SMA20"""
        try:
            if len(df) >= 20:
                return float(df['Close'].iloc[-20:].mean())
            return float(df['Close'].mean())
        except:
            return df['Close'].iloc[-1] if len(df) > 0 else 0.0
    
    def _calc_volume_avg(self, df: pd.DataFrame) -> float:
        """Calculate 20-day average volume"""
        try:
            if len(df) >= 20:
                return float(df['Volume'].iloc[-20:].mean())
            return float(df['Volume'].mean())
        except:
            return df['Volume'].iloc[-1] if len(df) > 0 else 0.0
    
    def _check_sma20_signal(self, df: pd.DataFrame, sma20: float) -> str:
        """Check for SMA20 crossover signal"""
        try:
            if len(df) < 2:
                return 'hold'
            
            close_curr = df['Close'].iloc[-1]
            close_prev = df['Close'].iloc[-2]
            sma_prev = df['Close'].iloc[-21:-1].mean() if len(df) >= 22 else sma20
            
            if close_prev <= sma_prev and close_curr > sma20:
                return 'buy'
            elif close_prev >= sma_prev and close_curr < sma20:
                return 'sell'
            else:
                return 'hold'
        except:
            return 'hold'
    
    def generate_signals(self, date: str) -> List[PaperSignal]:
        """
        Generate trading signals for a specific date
        Uses Phase 4 filters:
        - ADX > 25 (trend confirmed)
        - Volume > 70% of 20-day avg (not thin)
        - ATR > 0.5% (market alive)
        """
        signals = []
        
        for symbol in self.symbols:
            try:
                # Load data up to this date
                df = self._load_data(symbol, "2024-01-01", date)
                
                if len(df) < 22:
                    continue
                
                # Calculate indicators
                sma20 = self._calc_sma20(df)
                adx = self._calc_adx(df)
                atr_pct = self._calc_atr_pct(df)
                volume_avg = self._calc_volume_avg(df)
                current_price = df['Close'].iloc[-1]
                current_volume = df['Volume'].iloc[-1]
                
                # Apply Phase 4 filters
                if adx < 25:
                    continue
                
                if current_volume < volume_avg * 0.7:
                    continue
                
                if atr_pct < 0.005:
                    continue
                
                # Check for SMA20 signal
                signal_type = self._check_sma20_signal(df, sma20)
                
                if signal_type == 'hold':
                    continue
                
                # Create signal
                signal = PaperSignal(
                    signal_id=f"{symbol}_{date}_{signal_type}",
                    entry_date=date,
                    symbol=symbol,
                    signal_type=signal_type,
                    entry_price=current_price,
                    confidence=adx,
                    atr_pct=atr_pct,
                    sma20=sma20
                )
                
                signals.append(signal)
                self.signals[signal.signal_id] = signal
                
                if date not in self.daily_signals:
                    self.daily_signals[date] = []
                self.daily_signals[date].append(signal.signal_id)
                
                logger.info(f"Generated signal: {signal}")
            
            except Exception as e:
                logger.debug(f"Error generating signal for {symbol}: {e}")
        
        return signals
    
    def update_outcomes(self, end_date: str):
        """
        Update P&L for all pending signals based on price data
        Automatically closes signals when they hit targets/stops
        """
        for signal_id, signal in self.signals.items():
            if signal.status == "closed":
                continue
            
            try:
                # Load data from signal date to end date
                df = self._load_data(signal.symbol, signal.entry_date, end_date)
                
                if len(df) < 2:
                    continue
                
                # Get current price
                current_price = df['Close'].iloc[-1]
                signal.current_price = current_price
                
                # Calculate P&L
                if signal.signal_type == "buy":
                    signal.current_pnl_pct = ((current_price - signal.entry_price) / 
                                             signal.entry_price)
                else:  # sell
                    signal.current_pnl_pct = ((signal.entry_price - current_price) / 
                                             signal.entry_price)
                
                # Days held
                signal.days_held = len(df) - 1
                
                # Track extremes
                if signal.signal_type == "buy":
                    prices = df['Close'].iloc[1:]
                    pnl_series = (prices - signal.entry_price) / signal.entry_price
                else:  # sell
                    prices = df['Close'].iloc[1:]
                    pnl_series = (signal.entry_price - prices) / signal.entry_price
                
                signal.max_pnl_pct = float(pnl_series.max())
                signal.min_pnl_pct = float(pnl_series.min())
                
                # Check closure conditions
                self._check_signal_closure(signal)
            
            except Exception as e:
                logger.debug(f"Error updating signal {signal_id}: {e}")
    
    def _check_signal_closure(self, signal: PaperSignal):
        """Check if signal should be closed"""
        # Priority: Stop Loss > Profit Target > Time Stop
        
        if signal.current_pnl_pct <= -0.01:
            # Hit stop loss
            signal.status = "closed"
            signal.final_status = "loss"
            signal.final_pnl_pct = -0.01
            signal.close_reason = "stop_loss"
        
        elif signal.current_pnl_pct >= 0.02:
            # Hit profit target
            signal.status = "closed"
            signal.final_status = "win"
            signal.final_pnl_pct = 0.02
            signal.close_reason = "profit_target"
        
        elif signal.days_held >= 10:
            # Time stop
            signal.status = "closed"
            signal.final_status = "win" if signal.current_pnl_pct > 0 else "loss"
            signal.final_pnl_pct = signal.current_pnl_pct
            signal.close_reason = "time_stop"
    
    def get_metrics(self) -> Dict:
        """Calculate overall metrics"""
        closed = [s for s in self.signals.values() if s.status == "closed"]
        pending = [s for s in self.signals.values() if s.status == "pending"]
        
        if not closed:
            return {
                'total_signals': len(self.signals),
                'closed_signals': 0,
                'pending_signals': len(pending),
                'win_rate': 0.0,
                'wins': 0,
                'losses': 0,
                'avg_pnl': 0.0,
                'total_pnl': 0.0,
                'avg_days_held': 0.0,
                'max_drawdown': 0.0,
                'avg_adx': np.mean([s.confidence for s in self.signals.values()]) if self.signals else 0.0
            }
        
        wins = [s for s in closed if s.final_status == "win"]
        losses = [s for s in closed if s.final_status == "loss"]
        
        return {
            'total_signals': len(self.signals),
            'closed_signals': len(closed),
            'pending_signals': len(pending),
            'win_rate': len(wins) / len(closed) if closed else 0.0,
            'wins': len(wins),
            'losses': len(losses),
            'avg_pnl': np.mean([s.final_pnl_pct for s in closed]) if closed else 0.0,
            'total_pnl': sum(s.final_pnl_pct for s in closed) if closed else 0.0,
            'avg_days_held': np.mean([s.days_held for s in closed]) if closed else 0.0,
            'max_drawdown': min([s.min_pnl_pct for s in closed], default=0.0),
            'avg_adx': np.mean([s.confidence for s in self.signals.values()]) if self.signals else 0.0
        }
    
    def save_report(self, filename: str = "phase5_paper_trading_report.json"):
        """Save detailed report to JSON"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'metrics': self.get_metrics(),
            'signals': [
                {
                    'signal_id': s.signal_id,
                    'entry_date': s.entry_date,
                    'symbol': s.symbol,
                    'signal_type': s.signal_type,
                    'entry_price': s.entry_price,
                    'confidence_adx': s.confidence,
                    'status': s.status,
                    'current_price': s.current_price,
                    'current_pnl': f"{s.current_pnl_pct:.2%}",
                    'final_pnl': f"{s.final_pnl_pct:.2%}",
                    'final_status': s.final_status,
                    'days_held': s.days_held,
                    'close_reason': s.close_reason
                }
                for s in self.signals.values()
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {filename}")


def main():
    """Main entry point"""
    
    symbols = ["INFY", "TCS", "AXIS", "MARUTI", "WIPRO", "SUNPHARMA"]
    engine = PaperTradingEngine(symbols)
    
    print(f"\n{'='*80}")
    print("PHASE 5: LIVE PAPER TRADING SYSTEM - ENHANCED")
    print(f"{'='*80}\n")
    
    # Simulate trading days (last 30 days)
    today = datetime.now()
    
    for i in range(30, 0, -1):
        test_date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        
        # Skip weekends
        if pd.Timestamp(test_date).dayofweek >= 5:
            continue
        
        print(f"Processing {test_date}...", end=" ")
        
        # Generate signals for this date
        signals = engine.generate_signals(test_date)
        
        # Update all signal outcomes
        engine.update_outcomes(test_date)
        
        if signals:
            print(f"Generated {len(signals)} signal(s)")
            for sig in signals:
                print(f"  → {sig}")
        else:
            print("No signals")
    
    # Final update
    final_date = today.strftime('%Y-%m-%d')
    engine.update_outcomes(final_date)
    
    # Print summary
    print(f"\n{'='*80}")
    print("PAPER TRADING SUMMARY")
    print(f"{'='*80}\n")
    
    metrics = engine.get_metrics()
    
    print(f"Total Signals Generated:  {metrics['total_signals']}")
    print(f"Closed Signals:           {metrics['closed_signals']}")
    print(f"Pending Signals:          {metrics['pending_signals']}")
    print(f"Winning Trades:           {metrics['wins']}")
    print(f"Losing Trades:            {metrics['losses']}")
    print(f"Win Rate:                 {metrics['win_rate']:.1%}")
    print(f"Average P&L per Trade:    {metrics['avg_pnl']:+.2%}")
    print(f"Total P&L (all trades):   {metrics['total_pnl']:+.2%}")
    print(f"Average Days Held:        {metrics['avg_days_held']:.1f} days")
    print(f"Max Drawdown:             {metrics['max_drawdown']:.2%}")
    print(f"Average ADX:              {metrics['avg_adx']:.1f}")
    
    print(f"\n{'='*80}\n")
    
    # Show all signals
    print("SIGNAL DETAILS:")
    print("-" * 80)
    
    for signal_id in sorted(engine.signals.keys()):
        sig = engine.signals[signal_id]
        print(f"  {sig}")
    
    print(f"\n{'='*80}\n")
    
    # Save report
    engine.save_report()
    
    # Print status
    closed = [s for s in engine.signals.values() if s.status == "closed"]
    if closed:
        print(f"✅ System OPERATIONAL - Generated {metrics['total_signals']} signals, "
              f"closed {metrics['closed_signals']}, win rate {metrics['win_rate']:.0%}")
    else:
        print(f"⏳ System RUNNING - Generated {metrics['total_signals']} signals, "
              f"tracking outcomes (need more trading days for closures)")
    
    print()


if __name__ == "__main__":
    main()
