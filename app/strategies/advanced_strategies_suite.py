"""
ADVANCED ALGORITHMIC STRATEGIES SUITE
=====================================

Complementary high-probability strategies filling gaps in the current portfolio:

📈 EQUITY STRATEGIES (4):
  1. Volatility Contraction Pattern (VCP) & Kinematics
  2. Statistical Arbitrage (Pairs Trading)
  3. Order Flow & Market Microstructure (Informed Volume)
  4. Post-Earnings Announcement Drift (PEAD)

📊 OPTIONS STRATEGIES (4):
  1. Systematic Delta-Neutral Volatility Harvesting
  2. Volatility Mean Reversion (Long Vega / Calendar Spreads)
  3. Gamma Scalping (Market Maker Model)
  4. Dynamic Options Momentum & Trend Following

Each strategy includes:
- Core logic implementation
- Risk management rules
- Performance metrics
- Position tracking
- Example backtests
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum
import logging
from math import sqrt, log, exp
from scipy.stats import norm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# SECTION 1: EQUITY STRATEGIES
# ============================================================================

class EquityStrategyBase:
    """Base class for equity strategies"""
    
    def __init__(self, symbol: str, lookback_period: int = 20, risk_per_trade: float = 0.02):
        """
        Args:
            symbol: Stock/Index symbol
            lookback_period: Historical lookback window for indicators
            risk_per_trade: Risk allocation per trade (default 2% of portfolio)
        """
        self.symbol = symbol
        self.lookback_period = lookback_period
        self.risk_per_trade = risk_per_trade
        self.trades = []
        self.positions = []
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate base indicators used by multiple strategies"""
        data = data.copy()
        
        # Moving averages
        data['SMA_10'] = data['Close'].rolling(10).mean()
        data['SMA_20'] = data['Close'].rolling(20).mean()
        data['SMA_50'] = data['Close'].rolling(50).mean()
        
        # Volatility indicators
        data['ATR_14'] = self._calculate_atr(data, 14)
        data['STD_20'] = data['Close'].rolling(20).std()
        
        # Volume indicators
        data['SMA_VOL_20'] = data['Volume'].rolling(20).mean()
        data['VOL_RATIO'] = data['Volume'] / data['SMA_VOL_20']
        
        # Additional indicators
        data['RSI_14'] = self._calculate_rsi(data['Close'], 14)
        data['MACD'], data['SIGNAL'] = self._calculate_macd(data['Close'])
        
        return data
    
    @staticmethod
    def _calculate_atr(data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range"""
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        return atr
    
    @staticmethod
    def _calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def _calculate_macd(close: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """Calculate MACD and Signal Line"""
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        return macd, signal


class VolatilityContractionPattern(EquityStrategyBase):
    """
    VCP Strategy: Detects progressive price dampening (successive rings of smaller pullbacks)
    accompanied by sharp volume drop, signaling institutional accumulation before breakout.
    
    Logic:
    - Measure successive price contractions (20% → 10% → 5%)
    - Volume threshold: below 20-day moving average by at least 50%
    - Entry: On first breakout after contraction pattern
    - Exit: When contraction pattern breaks or target reached
    """
    
    def __init__(self, symbol: str, vol_threshold: float = 0.50, contraction_levels: int = 3):
        """
        Args:
            symbol: Stock symbol
            vol_threshold: Volume must drop below SMA by this % (50% = 0.50)
            contraction_levels: Number of contraction rings to detect
        """
        super().__init__(symbol)
        self.vol_threshold = vol_threshold
        self.contraction_levels = contraction_levels
    
    def detect_vcp_pattern(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Detect Volatility Contraction Pattern
        
        Returns DataFrame with VCP signals
        """
        data = self.calculate_indicators(data)
        data['VCP_SIGNAL'] = 0
        data['VCP_PATTERN'] = False
        
        for i in range(self.lookback_period + 10, len(data)):
            # Calculate price ranges for successive periods
            ranges = []
            for j in range(1, self.contraction_levels + 1):
                start_idx = i - (j * 5)
                end_idx = i - ((j - 1) * 5)
                if start_idx >= 0:
                    high = data['High'].iloc[start_idx:end_idx].max()
                    low = data['Low'].iloc[start_idx:end_idx].min()
                    range_pct = ((high - low) / low) * 100 if low > 0 else 0
                    ranges.append(range_pct)
            
            # Check if ranges are contracting (each smaller than previous)
            if len(ranges) == self.contraction_levels:
                is_contracting = all(ranges[j] < ranges[j-1] for j in range(1, len(ranges)))
                
                # Check volume condition: below 20-day SMA by threshold
                vol_ratio = data['VOL_RATIO'].iloc[i]
                is_low_volume = vol_ratio < (1 - self.vol_threshold)
                
                if is_contracting and is_low_volume:
                    data.loc[i, 'VCP_PATTERN'] = True
                    
                    # Check for breakout (close above recent high)
                    recent_high = data['High'].iloc[i-5:i].max()
                    if data['Close'].iloc[i] > recent_high * 1.01:  # 1% breakout threshold
                        data.loc[i, 'VCP_SIGNAL'] = 1  # BUY signal
        
        return data
    
    def backtest(self, data: pd.DataFrame) -> Dict:
        """Run VCP backtest"""
        data = self.detect_vcp_pattern(data)
        
        trades_returns = []
        in_position = False
        entry_price = 0
        entry_index = 0
        
        for i in range(len(data)):
            if data['VCP_SIGNAL'].iloc[i] == 1 and not in_position:
                in_position = True
                entry_price = data['Close'].iloc[i]
                entry_index = i
                atr = data['ATR_14'].iloc[i]
                self.stop_loss = entry_price - (2 * atr)  # 2 ATR stop loss
                self.target = entry_price + (3 * atr)     # 3 ATR target
            
            elif in_position:
                current_price = data['Close'].iloc[i]
                
                # Exit conditions
                if current_price < self.stop_loss or current_price > self.target:
                    trade_return = (current_price - entry_price) / entry_price
                    trades_returns.append(trade_return)
                    
                    self.trades.append({
                        'entry_index': entry_index,
                        'exit_index': i,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'return': trade_return,
                        'type': 'VCP'
                    })
                    
                    in_position = False
        
        # Close any open position
        if in_position:
            trade_return = (data['Close'].iloc[-1] - entry_price) / entry_price
            trades_returns.append(trade_return)
        
        return self._compute_metrics(trades_returns, len(data))
    
    def _compute_metrics(self, trades_returns: List[float], data_length: int) -> Dict:
        """Compute performance metrics"""
        if len(trades_returns) == 0:
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'avg_trade_return': 0.0,
                'trades': 0
            }
        
        trades_array = np.array(trades_returns)
        
        # Metrics calculation
        total_return = (np.prod(1 + trades_array) - 1) * 100
        mean_return = np.mean(trades_array)
        std_return = np.std(trades_array)
        
        sharpe = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        
        win_rate = (np.sum(trades_array > 0) / len(trades_array)) * 100 if len(trades_array) > 0 else 0
        
        wins = np.sum(trades_array[trades_array > 0])
        losses = np.abs(np.sum(trades_array[trades_array < 0]))
        profit_factor = wins / losses if losses > 0 else 1.0
        
        return {
            'total_return': round(total_return, 2),
            'sharpe_ratio': round(sharpe, 2),
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'avg_trade_return': round(mean_return * 100, 2),
            'trades': len(trades_returns),
            'pattern': 'VCP'
        }


class StatisticalArbitrage(EquityStrategyBase):
    """
    Pairs Trading Strategy: Exploits divergence from historical correlation of two correlated assets.
    
    Logic:
    - Calculate cointegration of stock pairs
    - Long underperforming stock when spread > +2σ from mean
    - Short outperforming stock simultaneously (market neutral)
    - Close when spread reverts to mean
    """
    
    def __init__(self, symbol_1: str, symbol_2: str, zscore_threshold: float = 2.0):
        """
        Args:
            symbol_1: First stock symbol
            symbol_2: Second stock symbol (correlated pair)
            zscore_threshold: Z-score threshold for entry (typically ±2.0)
        """
        self.symbol_1 = symbol_1
        self.symbol_2 = symbol_2
        self.zscore_threshold = zscore_threshold
        self.trades = []
    
    def calculate_spread(self, data1: pd.DataFrame, data2: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate price spread and Z-score for pairs trading
        """
        # Normalize prices
        price1_norm = (data1['Close'] - data1['Close'].mean()) / data1['Close'].std()
        price2_norm = (data2['Close'] - data2['Close'].mean()) / data2['Close'].std()
        
        # Calculate spread
        spread = price1_norm - price2_norm
        
        # Calculate Z-score of spread
        spread_mean = spread.rolling(20).mean()
        spread_std = spread.rolling(20).std()
        zscore = (spread - spread_mean) / spread_std if spread_std.mean() > 0 else 0
        
        result = pd.DataFrame({
            'Date': data1['Date'],
            'Spread': spread,
            'ZScore': zscore,
            'Close1': data1['Close'],
            'Close2': data2['Close']
        })
        
        return result
    
    def backtest(self, data1: pd.DataFrame, data2: pd.DataFrame) -> Dict:
        """Run pairs trading backtest"""
        pairs_data = self.calculate_spread(data1, data2)
        
        trades_returns = []
        in_position = False
        entry_zscore = 0
        position_type = None  # 'long_1_short_2' or 'short_1_long_2'
        entry_prices = {'stock1': 0, 'stock2': 0}
        
        for i in range(20, len(pairs_data)):
            zscore = pairs_data['ZScore'].iloc[i]
            close1 = pairs_data['Close1'].iloc[i]
            close2 = pairs_data['Close2'].iloc[i]
            
            # Entry signals
            if not in_position:
                if zscore > self.zscore_threshold:
                    # Stock 1 overvalued, Stock 2 undervalued
                    # Long Stock 2, Short Stock 1
                    in_position = True
                    position_type = 'long_2_short_1'
                    entry_prices = {'stock1': close1, 'stock2': close2}
                    entry_zscore = zscore
                
                elif zscore < -self.zscore_threshold:
                    # Stock 1 undervalued, Stock 2 overvalued
                    # Long Stock 1, Short Stock 2
                    in_position = True
                    position_type = 'long_1_short_2'
                    entry_prices = {'stock1': close1, 'stock2': close2}
                    entry_zscore = zscore
            
            # Exit on mean reversion (Z-score crosses zero)
            elif in_position and abs(zscore) < 0.5:
                if position_type == 'long_1_short_2':
                    # Return = long return - short return
                    long_return = (close1 - entry_prices['stock1']) / entry_prices['stock1']
                    short_return = (entry_prices['stock2'] - close2) / entry_prices['stock2']
                    trade_return = (long_return + short_return) / 2  # Average return
                else:
                    long_return = (close2 - entry_prices['stock2']) / entry_prices['stock2']
                    short_return = (entry_prices['stock1'] - close1) / entry_prices['stock1']
                    trade_return = (long_return + short_return) / 2
                
                trades_returns.append(trade_return)
                self.trades.append({
                    'pair': f"{self.symbol_1}_{self.symbol_2}",
                    'type': position_type,
                    'return': trade_return,
                    'entry_zscore': entry_zscore,
                    'exit_zscore': zscore
                })
                in_position = False
        
        return self._compute_metrics(trades_returns)
    
    def _compute_metrics(self, trades_returns: List[float]) -> Dict:
        """Compute performance metrics"""
        if len(trades_returns) == 0:
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'strategy': 'Pairs Trading',
                'trades': 0
            }
        
        trades_array = np.array(trades_returns)
        total_return = (np.prod(1 + trades_array) - 1) * 100
        mean_return = np.mean(trades_array)
        std_return = np.std(trades_array)
        
        sharpe = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        win_rate = (np.sum(trades_array > 0) / len(trades_array)) * 100
        
        wins = np.sum(trades_array[trades_array > 0])
        losses = np.abs(np.sum(trades_array[trades_array < 0]))
        profit_factor = wins / losses if losses > 0 else 1.0
        
        return {
            'total_return': round(total_return, 2),
            'sharpe_ratio': round(sharpe, 2),
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'pair': f"{self.symbol_1}_{self.symbol_2}",
            'strategy': 'Pairs Trading',
            'trades': len(trades_returns)
        }


class OrderFlowMicrostructure(EquityStrategyBase):
    """
    Order Flow & Market Microstructure Strategy: Exploits institutional execution footprints.
    
    Logic:
    - Monitor Volume Imbalance: aggressive market buyers absorb sell limit orders
    - Track Cumulative Delta: sum of up-volume minus down-volume
    - Entry at key support with high volume imbalance
    - Exit on target or volume reversal
    """
    
    def __init__(self, symbol: str, volume_imbalance_threshold: float = 1.5):
        """
        Args:
            symbol: Stock symbol
            volume_imbalance_threshold: Ratio of buying to selling volume (1.5 = 50% more buys)
        """
        super().__init__(symbol)
        self.volume_imbalance_threshold = volume_imbalance_threshold
    
    def calculate_order_flow(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate order flow indicators:
        - Volume Imbalance: buying volume / selling volume
        - Cumulative Delta: sum of (up_volume - down_volume)
        """
        data = data.copy()
        
        # Determine up/down volume based on close vs open
        data['Up_Volume'] = data['Volume'].where(data['Close'] > data['Open'], 0)
        data['Down_Volume'] = data['Volume'].where(data['Close'] < data['Open'], 0)
        
        # Volume Imbalance Ratio
        data['Vol_Imbalance'] = data['Up_Volume'] / (data['Down_Volume'] + 1)  # +1 to avoid divide by zero
        
        # Cumulative Delta
        data['Delta'] = data['Up_Volume'] - data['Down_Volume']
        data['Cumulative_Delta'] = data['Delta'].cumsum()
        
        # Normalize cumulative delta
        data['Cum_Delta_Norm'] = (data['Cumulative_Delta'] - 
                                   data['Cumulative_Delta'].rolling(20).mean()) / (data['Cumulative_Delta'].rolling(20).std() + 0.001)
        
        return data
    
    def backtest(self, data: pd.DataFrame) -> Dict:
        """Run order flow backtest"""
        data = self.calculate_order_flow(data)
        
        trades_returns = []
        in_position = False
        entry_price = 0
        entry_index = 0
        
        for i in range(20, len(data)):
            vol_imbalance = data['Vol_Imbalance'].iloc[i]
            cum_delta_norm = data['Cum_Delta_Norm'].iloc[i]
            current_price = data['Close'].iloc[i]
            
            # Entry: High volume imbalance + positive cumulative delta at support
            if not in_position and vol_imbalance > self.volume_imbalance_threshold and cum_delta_norm > 1.0:
                # Check if we're near a support level (low of recent swing)
                recent_low = data['Low'].iloc[max(0, i-10):i].min()
                if current_price < recent_low * 1.02:  # Within 2% of low
                    in_position = True
                    entry_price = current_price
                    entry_index = i
                    self.target = entry_price * 1.05  # 5% target
                    self.stop_loss = entry_price * 0.97  # 3% stop
            
            # Exit conditions
            elif in_position:
                # Exit on target, stop loss, or volume reversal
                if (current_price > self.target or 
                    current_price < self.stop_loss or 
                    vol_imbalance < 1.0):  # Volume imbalance reversed
                    
                    trade_return = (current_price - entry_price) / entry_price
                    trades_returns.append(trade_return)
                    
                    self.trades.append({
                        'entry_index': entry_index,
                        'exit_index': i,
                        'return': trade_return,
                        'reason': 'target' if current_price > self.target else ('stop' if current_price < self.stop_loss else 'volume_reversal')
                    })
                    
                    in_position = False
        
        # Close any open position
        if in_position:
            trade_return = (data['Close'].iloc[-1] - entry_price) / entry_price
            trades_returns.append(trade_return)
        
        return self._compute_metrics(trades_returns)
    
    def _compute_metrics(self, trades_returns: List[float]) -> Dict:
        """Compute performance metrics"""
        if len(trades_returns) == 0:
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'strategy': 'Order Flow',
                'trades': 0
            }
        
        trades_array = np.array(trades_returns)
        total_return = (np.prod(1 + trades_array) - 1) * 100
        mean_return = np.mean(trades_array)
        std_return = np.std(trades_array)
        
        sharpe = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        win_rate = (np.sum(trades_array > 0) / len(trades_array)) * 100
        
        return {
            'total_return': round(total_return, 2),
            'sharpe_ratio': round(sharpe, 2),
            'win_rate': round(win_rate, 2),
            'strategy': 'Order Flow Microstructure',
            'trades': len(trades_returns)
        }


class PostEarningsAnnouncementDrift(EquityStrategyBase):
    """
    PEAD Strategy: Exploits the underreaction of market to earnings surprises.
    
    Logic:
    - Monitor EPS/Revenue surprises (beat vs miss)
    - When fundamental beat + volume breakout on day 1: enter swing position
    - Use trailing stop based on ATR
    - Hold for multi-week drift capture
    """
    
    def __init__(self, symbol: str, surprise_threshold: float = 0.05):
        """
        Args:
            symbol: Stock symbol
            surprise_threshold: EPS surprise threshold (5% = 0.05)
        """
        super().__init__(symbol)
        self.surprise_threshold = surprise_threshold
    
    def simulate_earnings_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Simulate earnings announcements in data.
        In production, this would connect to earnings calendar API.
        """
        data = data.copy()
        data['Earnings'] = False
        data['Surprise'] = 0.0
        
        # Simulate earnings every quarter (roughly every 63 days)
        np.random.seed(hash(self.symbol) % 2**32)
        earnings_indices = np.arange(63, len(data), 63)
        
        for idx in earnings_indices[:len(data)//63]:
            if idx < len(data):
                # Random surprise between -10% and +10%
                data.loc[idx, 'Earnings'] = True
                data.loc[idx, 'Surprise'] = np.random.uniform(-0.10, 0.10)
        
        return data
    
    def backtest(self, data: pd.DataFrame) -> Dict:
        """Run PEAD backtest"""
        data = self.simulate_earnings_data(data)
        data = self.calculate_indicators(data)
        
        trades_returns = []
        in_position = False
        entry_price = 0
        entry_index = 0
        position_days = 0
        
        for i in range(self.lookback_period, len(data)):
            current_price = data['Close'].iloc[i]
            current_volume = data['Volume'].iloc[i]
            avg_volume = data['SMA_VOL_20'].iloc[i]
            
            # Entry: Earnings beat + volume breakout
            if not in_position and data['Earnings'].iloc[i]:
                surprise = data['Surprise'].iloc[i]
                
                # Positive surprise (beat) + high volume
                if surprise > self.surprise_threshold and current_volume > avg_volume * 1.5:
                    in_position = True
                    entry_price = current_price
                    entry_index = i
                    atr = data['ATR_14'].iloc[i]
                    self.trailing_stop = entry_price - (2 * atr)
                    self.max_price = entry_price
                    position_days = 0
            
            # Exit: trailing stop or hold for 20+ days
            elif in_position:
                position_days += 1
                
                # Update trailing stop
                self.max_price = max(self.max_price, current_price)
                atr = data['ATR_14'].iloc[i]
                trailing_stop = self.max_price - (2 * atr)
                self.trailing_stop = max(self.trailing_stop, trailing_stop)
                
                # Exit conditions
                if current_price < self.trailing_stop or position_days > 20:
                    trade_return = (current_price - entry_price) / entry_price
                    trades_returns.append(trade_return)
                    
                    self.trades.append({
                        'entry_index': entry_index,
                        'exit_index': i,
                        'days_held': position_days,
                        'return': trade_return,
                        'reason': 'trailing_stop' if current_price < self.trailing_stop else 'max_hold'
                    })
                    
                    in_position = False
        
        # Close any open position
        if in_position:
            trade_return = (data['Close'].iloc[-1] - entry_price) / entry_price
            trades_returns.append(trade_return)
        
        return self._compute_metrics(trades_returns)
    
    def _compute_metrics(self, trades_returns: List[float]) -> Dict:
        """Compute performance metrics"""
        if len(trades_returns) == 0:
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'avg_hold_days': 0,
                'strategy': 'PEAD',
                'trades': 0
            }
        
        trades_array = np.array(trades_returns)
        total_return = (np.prod(1 + trades_array) - 1) * 100
        mean_return = np.mean(trades_array)
        std_return = np.std(trades_array)
        
        sharpe = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        win_rate = (np.sum(trades_array > 0) / len(trades_array)) * 100
        
        avg_hold_days = np.mean([t['days_held'] for t in self.trades if 'days_held' in t])
        
        return {
            'total_return': round(total_return, 2),
            'sharpe_ratio': round(sharpe, 2),
            'win_rate': round(win_rate, 2),
            'avg_hold_days': round(avg_hold_days, 1),
            'strategy': 'Post-Earnings Announcement Drift',
            'trades': len(trades_returns)
        }


# ============================================================================
# SECTION 2: OPTIONS STRATEGIES
# ============================================================================

@dataclass
class OptionPosition:
    """Represents an options position"""
    symbol: str
    position_type: str  # 'long_call', 'short_call', 'long_put', 'short_put', 'long_straddle', 'iron_condor'
    entry_price: float
    entry_date: datetime
    strike: float
    expiration: datetime
    delta: float
    gamma: float
    theta: float  # Time decay
    vega: float
    
    @property
    def days_to_expiration(self) -> int:
        """Calculate days to expiration"""
        return (self.expiration - self.entry_date).days
    
    @property
    def time_decay_factor(self) -> float:
        """Proportion of time value decayed"""
        return 1.0 - (self.days_to_expiration / 30)


class OptionsStrategyBase:
    """Base class for options strategies"""
    
    def __init__(self, symbol: str, risk_per_trade: float = 0.01):
        self.symbol = symbol
        self.risk_per_trade = risk_per_trade
        self.positions = []
        self.trades = []
    
    def calculate_greeks(self, stock_price: float, strike: float, 
                        time_to_exp: float, rate: float = 0.05, 
                        volatility: float = 0.2, option_type: str = 'call') -> Dict:
        """
        Simplified Black-Scholes Greeks calculation
        
        Args:
            stock_price: Current stock price
            strike: Option strike price
            time_to_exp: Time to expiration in years
            rate: Risk-free rate
            volatility: Implied volatility
            option_type: 'call' or 'put'
        
        Returns:
            Dict with Greeks: delta, gamma, theta, vega
        """
        try:
            d1 = (log(stock_price / strike) + (rate + 0.5 * volatility ** 2) * time_to_exp) / (
                volatility * sqrt(time_to_exp)
            )
            d2 = d1 - volatility * sqrt(time_to_exp)
            
            if option_type == 'call':
                delta = norm.cdf(d1)
                theta = (
                    -(stock_price * norm.pdf(d1) * volatility) / (2 * sqrt(time_to_exp))
                    - rate * strike * exp(-rate * time_to_exp) * norm.cdf(d2)
                ) / 365
            else:  # put
                delta = norm.cdf(d1) - 1
                theta = (
                    -(stock_price * norm.pdf(d1) * volatility) / (2 * sqrt(time_to_exp))
                    + rate * strike * exp(-rate * time_to_exp) * norm.cdf(-d2)
                ) / 365
            
            gamma = norm.pdf(d1) / (stock_price * volatility * sqrt(time_to_exp))
            vega = stock_price * norm.pdf(d1) * sqrt(time_to_exp) / 100
            
            return {
                'delta': delta,
                'gamma': gamma,
                'theta': theta,
                'vega': vega
            }
        except:
            # Return default Greeks if calculation fails
            return {
                'delta': 0.5,
                'gamma': 0.01,
                'theta': -0.01,
                'vega': 0.1
            }
    
    def calculate_iv_metrics(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate IV Rank and IV Percentile
        
        In production, would pull from real options chains via broker API
        """
        data = data.copy()
        
        # Simplified: Use realized volatility as proxy for IV
        returns = data['Close'].pct_change()
        realized_vol = returns.rolling(20).std() * sqrt(252)
        
        # IV Rank: percentile rank of current IV within 52-week range
        iv_rank = (realized_vol - realized_vol.rolling(252).min()) / (
            realized_vol.rolling(252).max() - realized_vol.rolling(252).min() + 0.001
        ) * 100
        
        # IV Percentile: simpler calculation
        iv_percentile = iv_rank  # Simplified
        
        data['IV_Rank'] = iv_rank
        data['IV_Percentile'] = iv_percentile
        data['Realized_Vol'] = realized_vol
        
        return data
    
    @staticmethod
    def sqrt(x):
        """Safe square root"""
        return np.sqrt(max(x, 0.0001))


class DeltaNeutralVolatilityHarvesting(OptionsStrategyBase):
    """
    Systematic Delta-Neutral Volatility Harvesting: Sells premium when IV is high.
    
    Logic:
    - Scan for high IV Percentile (IVP > 70%)
    - Sell Delta-Neutral Iron Condor or Strangle (15-30 Delta)
    - Auto-manage at 50% max profit or close at loss limit
    - Position sizing based on margin available
    """
    
    def __init__(self, symbol: str, iv_threshold: float = 70.0, target_profit_pct: float = 0.50):
        """
        Args:
            symbol: Stock symbol
            iv_threshold: IV Percentile threshold for selling premium (70%)
            target_profit_pct: Close at this % of max profit (50%)
        """
        super().__init__(symbol)
        self.iv_threshold = iv_threshold
        self.target_profit_pct = target_profit_pct
    
    def backtest(self, data: pd.DataFrame) -> Dict:
        """Run delta-neutral volatility harvesting backtest"""
        data = self.calculate_iv_metrics(data)
        
        trades_returns = []
        in_position = False
        entry_credit = 0
        entry_index = 0
        max_risk = 0
        
        for i in range(20, len(data)):
            iv_percentile = data['IV_Percentile'].iloc[i]
            current_price = data['Close'].iloc[i]
            
            # Entry: High IV - sell premium at delta neutral
            if not in_position and iv_percentile > self.iv_threshold:
                in_position = True
                entry_index = i
                
                # Approximate credit received (simplified)
                # Higher IV = higher premium
                entry_credit = current_price * 0.02 * (iv_percentile / 100)
                max_risk = entry_credit * 2  # Max loss = 2x credit
                
                # Store position details
                self.short_strike = current_price  # Delta-neutral strike
                self.entry_date = data['Date'].iloc[i]
                self.expiration = self.entry_date + timedelta(days=30)
            
            # Exit: At 50% max profit or max loss
            elif in_position:
                current_price = data['Close'].iloc[i]
                
                # Simplified P&L: varies with distance from strike
                distance_from_strike = abs(current_price - self.short_strike) / self.short_strike
                
                # As underlying moves away, we lose
                # As time passes or IV contracts, we gain
                time_decay_factor = max(0, 1 - (i - entry_index) / 30)
                iv_change = (data['IV_Percentile'].iloc[i] - data['IV_Percentile'].iloc[entry_index]) / 100
                
                # P&L approximation
                pnl = (entry_credit * time_decay_factor * 0.8 - distance_from_strike * 0.1) - iv_change * 0.05
                pnl_pct = pnl / entry_credit if entry_credit > 0 else 0
                
                # Exit conditions
                profit_target = entry_credit * self.target_profit_pct
                
                if pnl > profit_target or pnl < -max_risk or (i - entry_index) > 30:
                    trade_return = pnl_pct
                    trades_returns.append(trade_return)
                    
                    self.trades.append({
                        'entry_index': entry_index,
                        'exit_index': i,
                        'credit_received': entry_credit,
                        'return': trade_return,
                        'reason': 'profit_target' if pnl > profit_target else ('max_loss' if pnl < -max_risk else 'expiration')
                    })
                    
                    in_position = False
        
        return self._compute_metrics(trades_returns)
    
    def _compute_metrics(self, trades_returns: List[float]) -> Dict:
        """Compute performance metrics"""
        if len(trades_returns) == 0:
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'strategy': 'Delta-Neutral Volatility Harvesting',
                'trades': 0
            }
        
        trades_array = np.array(trades_returns)
        total_return = (np.prod(1 + trades_array) - 1) * 100
        mean_return = np.mean(trades_array)
        std_return = np.std(trades_array)
        
        sharpe = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        win_rate = (np.sum(trades_array > 0) / len(trades_array)) * 100
        
        return {
            'total_return': round(total_return, 2),
            'sharpe_ratio': round(sharpe, 2),
            'win_rate': round(win_rate, 2),
            'avg_trade_return': round(mean_return * 100, 2),
            'strategy': 'Delta-Neutral Volatility Harvesting',
            'trades': len(trades_returns),
            'premium_seller': True
        }


class VolatilityMeanReversion(OptionsStrategyBase):
    """
    Long Vega / Calendar Spreads: Buy volatility when it's at historical lows.
    
    Logic:
    - When IV Rank drops to near-zero (extreme complacency)
    - Deploy calendar spreads or diagonal spreads on liquid underlyings
    - Sell short-term theta while staying long back-month volatility (vega)
    - Profit from IV expansion or vol spike
    """
    
    def __init__(self, symbol: str, iv_rank_threshold: float = 20.0):
        """
        Args:
            symbol: Stock symbol
            iv_rank_threshold: IV Rank threshold for deployment (20% = low volatility)
        """
        super().__init__(symbol)
        self.iv_rank_threshold = iv_rank_threshold
    
    def backtest(self, data: pd.DataFrame) -> Dict:
        """Run volatility mean reversion backtest"""
        data = self.calculate_iv_metrics(data)
        
        trades_returns = []
        in_position = False
        entry_index = 0
        position_vega = 0
        position_theta = 0
        
        for i in range(20, len(data)):
            iv_rank = data['IV_Rank'].iloc[i]
            current_price = data['Close'].iloc[i]
            
            # Entry: IV at historical lows - buy volatility via calendar spreads
            if not in_position and iv_rank < self.iv_rank_threshold:
                in_position = True
                entry_index = i
                
                # Calendar spread: short 30 DTE call, long 60 DTE call (same strike)
                # This gives positive vega (long vol) and some positive theta
                position_vega = 0.15  # Long vega exposure
                position_theta = 0.005  # Small positive theta from short-term decay
                
                self.entry_iv_rank = iv_rank
            
            # Exit: IV expansion or 20 days
            elif in_position:
                iv_rank = data['IV_Rank'].iloc[i]
                days_held = i - entry_index
                
                # P&L from vega exposure and theta decay
                iv_change = (iv_rank - self.entry_iv_rank) / 100
                vega_pnl = iv_change * position_vega  # Positive if IV expands
                theta_pnl = position_theta * days_held / 365  # Small daily decay benefit
                
                total_pnl = vega_pnl + theta_pnl
                
                # Exit conditions: IV spike (10%+ increase) or 20 days
                iv_spike = (iv_rank - self.entry_iv_rank) > 10
                time_limit = days_held > 20
                
                if iv_spike or time_limit:
                    trade_return = total_pnl
                    trades_returns.append(trade_return)
                    
                    self.trades.append({
                        'entry_index': entry_index,
                        'exit_index': i,
                        'days_held': days_held,
                        'entry_iv_rank': self.entry_iv_rank,
                        'exit_iv_rank': iv_rank,
                        'vega_pnl': vega_pnl,
                        'theta_pnl': theta_pnl,
                        'return': total_pnl
                    })
                    
                    in_position = False
        
        return self._compute_metrics(trades_returns)
    
    def _compute_metrics(self, trades_returns: List[float]) -> Dict:
        """Compute performance metrics"""
        if len(trades_returns) == 0:
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'strategy': 'Volatility Mean Reversion',
                'trades': 0
            }
        
        trades_array = np.array(trades_returns)
        total_return = sum(trades_array) * 100  # Linear return for vol strategies
        mean_return = np.mean(trades_array)
        std_return = np.std(trades_array)
        
        sharpe = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        win_rate = (np.sum(trades_array > 0) / len(trades_array)) * 100
        
        return {
            'total_return': round(total_return, 2),
            'sharpe_ratio': round(sharpe, 2),
            'win_rate': round(win_rate, 2),
            'strategy': 'Volatility Mean Reversion',
            'trades': len(trades_returns),
            'long_vega': True
        }


class GammaScalping(OptionsStrategyBase):
    """
    Gamma Scalping: Maintain delta-neutral portfolio by trading underlying shares.
    
    Logic:
    - Buy ATM long straddle (high gamma position)
    - Monitor portfolio delta as stock price moves
    - Auto buy/short shares to maintain delta-neutral
    - Lock in micro-profits from delta hedging
    """
    
    def __init__(self, symbol: str, rehedge_threshold: float = 0.1):
        """
        Args:
            symbol: Stock symbol
            rehedge_threshold: Rebalance when portfolio delta > this threshold (10%)
        """
        super().__init__(symbol)
        self.rehedge_threshold = rehedge_threshold
    
    def backtest(self, data: pd.DataFrame) -> Dict:
        """Run gamma scalping backtest"""
        
        trades_returns = []
        in_position = False
        entry_price = 0
        entry_index = 0
        position_delta = 0
        straddle_premium_paid = 0
        
        for i in range(20, len(data)):
            current_price = data['Close'].iloc[i]
            
            # Entry: Buy long straddle at ATM
            if not in_position:
                in_position = True
                entry_price = current_price
                entry_index = i
                
                # Straddle cost (simplified: 3% of stock price for ATM straddle)
                straddle_premium_paid = entry_price * 0.03
                position_delta = 0  # Initially delta-neutral
                
                # Initial Greeks at entry
                greeks = self.calculate_greeks(current_price, current_price, 30/365, volatility=0.2)
                position_delta = greeks['delta'] + (-greeks['delta'])  # Long call delta - short put delta (hedged)
            
            elif in_position:
                # Calculate current option delta at current price
                greeks = self.calculate_greeks(current_price, entry_price, 30/365, volatility=0.2)
                long_call_delta = greeks['delta']
                long_put_delta = greeks['delta'] - 1  # Put delta
                
                # Straddle delta (long call + long put)
                straddle_delta = long_call_delta + long_put_delta
                
                # P&L from gamma (option gains value as it moves)
                gamma = greeks['gamma']
                price_change = current_price - entry_price
                gamma_pnl = 0.5 * gamma * (price_change ** 2)
                
                # Time decay loss
                time_decay = straddle_premium_paid * 0.001 * (i - entry_index)
                
                # Need to rehedge to stay delta-neutral
                hedge_pnl = 0
                if abs(straddle_delta) > self.rehedge_threshold:
                    # Buy or sell shares to neutralize delta
                    shares_to_trade = abs(straddle_delta)
                    hedge_pnl = shares_to_trade * price_change / current_price  # Simplified
                    straddle_delta = 0
                
                net_pnl = gamma_pnl - time_decay + hedge_pnl
                net_pnl_pct = net_pnl / straddle_premium_paid if straddle_premium_paid > 0 else 0
                
                # Exit after 20 days or if straddle becomes unprofitable
                if (i - entry_index) > 20 or net_pnl < -straddle_premium_paid * 0.5:
                    trade_return = net_pnl_pct
                    trades_returns.append(trade_return)
                    
                    self.trades.append({
                        'entry_index': entry_index,
                        'exit_index': i,
                        'days_held': i - entry_index,
                        'premium_paid': straddle_premium_paid,
                        'gamma_pnl': gamma_pnl,
                        'time_decay': time_decay,
                        'hedge_pnl': hedge_pnl,
                        'return': net_pnl_pct
                    })
                    
                    in_position = False
        
        return self._compute_metrics(trades_returns)
    
    def _compute_metrics(self, trades_returns: List[float]) -> Dict:
        """Compute performance metrics"""
        if len(trades_returns) == 0:
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'strategy': 'Gamma Scalping',
                'trades': 0
            }
        
        trades_array = np.array(trades_returns)
        total_return = (np.prod(1 + trades_array) - 1) * 100 if len(trades_array) > 0 else 0
        mean_return = np.mean(trades_array)
        std_return = np.std(trades_array)
        
        sharpe = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        win_rate = (np.sum(trades_array > 0) / len(trades_array)) * 100 if len(trades_array) > 0 else 0
        
        return {
            'total_return': round(total_return, 2),
            'sharpe_ratio': round(sharpe, 2),
            'win_rate': round(win_rate, 2),
            'strategy': 'Gamma Scalping',
            'trades': len(trades_returns),
            'delta_neutral': True
        }


class DynamicOptionsMonitorTrendFollowing(OptionsStrategyBase):
    """
    Dynamic Options Momentum: Use options leverage for trend following.
    
    Logic:
    - When trend-following indicators flash buy signal
    - Enter bull call spread or long call (50-60 Delta)
    - Use 45-60 DTE for time decay protection
    - Asymmetric risk-reward profile captures explosive moves
    """
    
    def __init__(self, symbol: str, target_delta: float = 0.55):
        """
        Args:
            symbol: Stock symbol
            target_delta: Target delta for long call (55% = good leverage + time decay balance)
        """
        super().__init__(symbol)
        self.target_delta = target_delta
    
    def backtest(self, data: pd.DataFrame) -> Dict:
        """Run dynamic options momentum backtest"""
        
        trades_returns = []
        in_position = False
        entry_price = 0
        entry_index = 0
        call_premium_paid = 0
        strike_price = 0
        
        # Trend-following indicator (SMA crossover)
        sma_10 = data['Close'].rolling(10).mean()
        sma_30 = data['Close'].rolling(30).mean()
        
        for i in range(30, len(data)):
            current_price = data['Close'].iloc[i]
            
            # Entry: Trend-following signal (10-day SMA > 30-day SMA)
            if not in_position and sma_10.iloc[i] > sma_30.iloc[i] and sma_10.iloc[i-1] <= sma_30.iloc[i-1]:
                # Buy long call 50-60 days DTE
                in_position = True
                entry_price = current_price
                entry_index = i
                strike_price = current_price  # At-the-money
                
                # Estimate call premium (simplified)
                call_premium_paid = current_price * 0.05  # 5% of stock price
            
            elif in_position:
                # Trend-following exit (10-day SMA < 30-day SMA)
                if sma_10.iloc[i] < sma_30.iloc[i]:
                    # Calculate intrinsic value of call
                    intrinsic = max(current_price - strike_price, 0)
                    
                    # Approximate time value remaining
                    days_held = i - entry_index
                    time_value = call_premium_paid * max(0, 1 - days_held / 60)
                    
                    # Call value
                    call_value = intrinsic + time_value
                    
                    # Return on call
                    trade_return = (call_value - call_premium_paid) / call_premium_paid
                    trades_returns.append(trade_return)
                    
                    self.trades.append({
                        'entry_index': entry_index,
                        'exit_index': i,
                        'days_held': days_held,
                        'premium_paid': call_premium_paid,
                        'intrinsic_at_exit': intrinsic,
                        'return': trade_return
                    })
                    
                    in_position = False
                
                # Also exit if 60 days pass or large loss
                elif (i - entry_index) > 60 or current_price < strike_price * 0.90:
                    intrinsic = max(current_price - strike_price, 0)
                    days_held = i - entry_index
                    time_value = call_premium_paid * max(0, 1 - days_held / 60)
                    call_value = intrinsic + time_value
                    
                    trade_return = (call_value - call_premium_paid) / call_premium_paid
                    trades_returns.append(trade_return)
                    
                    in_position = False
        
        return self._compute_metrics(trades_returns)
    
    def _compute_metrics(self, trades_returns: List[float]) -> Dict:
        """Compute performance metrics"""
        if len(trades_returns) == 0:
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'strategy': 'Dynamic Options Momentum',
                'trades': 0
            }
        
        trades_array = np.array(trades_returns)
        total_return = (np.prod(1 + trades_array) - 1) * 100 if len(trades_array) > 0 else 0
        mean_return = np.mean(trades_array)
        std_return = np.std(trades_array)
        
        sharpe = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        win_rate = (np.sum(trades_array > 0) / len(trades_array)) * 100 if len(trades_array) > 0 else 0
        
        return {
            'total_return': round(total_return, 2),
            'sharpe_ratio': round(sharpe, 2),
            'win_rate': round(win_rate, 2),
            'strategy': 'Dynamic Options Momentum',
            'trades': len(trades_returns),
            'leveraged': True
        }


# ============================================================================
# INTEGRATION & TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*140)
    print("🚀 ADVANCED STRATEGIES SUITE - DEMONSTRATION".center(140))
    print("="*140 + "\n")
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=365, freq='D')
    start_price = 100
    returns = np.random.normal(0.0005, 0.02, 365)
    prices = start_price * np.exp(np.cumsum(returns))
    
    data = pd.DataFrame({
        'Date': dates,
        'Open': prices * (1 + np.random.normal(0, 0.005, 365)),
        'High': prices * (1 + np.abs(np.random.normal(0, 0.01, 365))),
        'Low': prices * (1 - np.abs(np.random.normal(0, 0.01, 365))),
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, 365)
    })
    
    print("📊 TESTING EQUITY STRATEGIES\n")
    
    # Test VCP
    print("1️⃣  VOLATILITY CONTRACTION PATTERN (VCP)")
    vcp = VolatilityContractionPattern('TEST', vol_threshold=0.50, contraction_levels=3)
    vcp_results = vcp.backtest(data)
    print(f"   Return: {vcp_results['total_return']:+.2f}%")
    print(f"   Sharpe: {vcp_results['sharpe_ratio']:.2f}")
    print(f"   Win Rate: {vcp_results['win_rate']:.1f}%")
    print(f"   Trades: {vcp_results['trades']}\n")
    
    # Test Pairs Trading
    print("2️⃣  STATISTICAL ARBITRAGE (PAIRS TRADING)")
    data2 = data.copy()
    data2['Close'] = data2['Close'] * (1 + np.random.normal(0, 0.01, len(data2)))
    pairs = StatisticalArbitrage('TEST1', 'TEST2', zscore_threshold=2.0)
    pairs_results = pairs.backtest(data, data2)
    print(f"   Pair: {pairs_results['pair']}")
    print(f"   Return: {pairs_results['total_return']:+.2f}%")
    print(f"   Sharpe: {pairs_results['sharpe_ratio']:.2f}")
    print(f"   Win Rate: {pairs_results['win_rate']:.1f}%")
    print(f"   Trades: {pairs_results['trades']}\n")
    
    # Test Order Flow
    print("3️⃣  ORDER FLOW & MARKET MICROSTRUCTURE")
    order_flow = OrderFlowMicrostructure('TEST', volume_imbalance_threshold=1.5)
    order_flow_results = order_flow.backtest(data)
    print(f"   Return: {order_flow_results['total_return']:+.2f}%")
    print(f"   Sharpe: {order_flow_results['sharpe_ratio']:.2f}")
    print(f"   Win Rate: {order_flow_results['win_rate']:.1f}%")
    print(f"   Trades: {order_flow_results['trades']}\n")
    
    # Test PEAD
    print("4️⃣  POST-EARNINGS ANNOUNCEMENT DRIFT (PEAD)")
    pead = PostEarningsAnnouncementDrift('TEST', surprise_threshold=0.05)
    pead_results = pead.backtest(data)
    print(f"   Return: {pead_results['total_return']:+.2f}%")
    print(f"   Sharpe: {pead_results['sharpe_ratio']:.2f}")
    print(f"   Win Rate: {pead_results['win_rate']:.1f}%")
    print(f"   Avg Hold Days: {pead_results['avg_hold_days']:.1f}")
    print(f"   Trades: {pead_results['trades']}\n")
    
    print("📊 TESTING OPTIONS STRATEGIES\n")
    
    # Test Delta-Neutral Volatility Harvesting
    print("5️⃣  DELTA-NEUTRAL VOLATILITY HARVESTING")
    vol_harvest = DeltaNeutralVolatilityHarvesting('TEST', iv_threshold=70.0)
    vol_harvest_results = vol_harvest.backtest(data)
    print(f"   Return: {vol_harvest_results['total_return']:+.2f}%")
    print(f"   Sharpe: {vol_harvest_results['sharpe_ratio']:.2f}")
    print(f"   Win Rate: {vol_harvest_results['win_rate']:.1f}%")
    print(f"   Trades: {vol_harvest_results['trades']}\n")
    
    # Test Volatility Mean Reversion
    print("6️⃣  VOLATILITY MEAN REVERSION (LONG VEGA)")
    vol_mr = VolatilityMeanReversion('TEST', iv_rank_threshold=20.0)
    vol_mr_results = vol_mr.backtest(data)
    print(f"   Return: {vol_mr_results['total_return']:+.2f}%")
    print(f"   Sharpe: {vol_mr_results['sharpe_ratio']:.2f}")
    print(f"   Win Rate: {vol_mr_results['win_rate']:.1f}%")
    print(f"   Trades: {vol_mr_results['trades']}\n")
    
    # Test Gamma Scalping
    print("7️⃣  GAMMA SCALPING (MARKET MAKER MODEL)")
    gamma = GammaScalping('TEST', rehedge_threshold=0.1)
    gamma_results = gamma.backtest(data)
    print(f"   Return: {gamma_results['total_return']:+.2f}%")
    print(f"   Sharpe: {gamma_results['sharpe_ratio']:.2f}")
    print(f"   Win Rate: {gamma_results['win_rate']:.1f}%")
    print(f"   Trades: {gamma_results['trades']}\n")
    
    # Test Dynamic Options Momentum
    print("8️⃣  DYNAMIC OPTIONS MOMENTUM & TREND FOLLOWING")
    options_mom = DynamicOptionsMonitorTrendFollowing('TEST', target_delta=0.55)
    options_mom_results = options_mom.backtest(data)
    print(f"   Return: {options_mom_results['total_return']:+.2f}%")
    print(f"   Sharpe: {options_mom_results['sharpe_ratio']:.2f}")
    print(f"   Win Rate: {options_mom_results['win_rate']:.1f}%")
    print(f"   Trades: {options_mom_results['trades']}\n")
    
    print("="*140)
    print("✅ ADVANCED STRATEGIES SUITE DEMO COMPLETE")
    print("="*140 + "\n")
