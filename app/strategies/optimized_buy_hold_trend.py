#!/usr/bin/env python3
"""
Optimized Enhanced Buy & Hold Strategy
Based on backtest analysis and performance recommendations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OptimizedConfig:
    """Optimized strategy configuration based on backtest analysis"""
    
    # Entry Conditions (Tightened based on low win rate)
    MIN_SIGNAL_STRENGTH: float = 0.8  # Increased from 0.7
    MIN_VOLUME_RATIO: float = 1.5     # Require 50% above 20-day average
    MIN_TREND_STRENGTH: float = 25    # ADX > 25 for strong trends
    
    # Technical Indicators (Optimized parameters)
    RSI_PERIOD: int = 14
    RSI_HEALTHY_MIN: int = 35         # Tightened from 30
    RSI_HEALTHY_MAX: int = 65         # Tightened from 70
    RSI_OVERSOLD: int = 25            # More extreme levels
    RSI_OVERBOUGHT: int = 75
    
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9
    
    STOCH_RSI_PERIOD: int = 14
    STOCH_RSI_K_PERIOD: int = 3
    STOCH_RSI_D_PERIOD: int = 3
    STOCH_RSI_OVERSOLD: int = 20
    STOCH_RSI_OVERBOUGHT: int = 75    # Tightened from 80
    
    # Moving Averages (Added for trend confirmation)
    MA_SHORT: int = 20
    MA_LONG: int = 50
    
    # Risk Management (Enhanced based on drawdown analysis)
    MAX_POSITION_SIZE: float = 0.08   # Reduced from 10% to 8%
    STOP_LOSS_PCT: float = 0.04       # Tightened from 5% to 4%
    TARGET_PCT: float = 0.12          # Reduced from 15% to 12%
    TRAILING_STOP_PCT: float = 0.02   # 2% trailing stop
    
    MAX_DAILY_LOSS_PCT: float = 0.015 # 1.5% daily loss limit
    MAX_OPEN_POSITIONS: int = 4       # Reduced from 5
    MAX_SECTOR_POSITIONS: int = 2     # Sector diversification
    
    # Partial Profit Taking (New feature)
    PARTIAL_PROFIT_PCT: float = 0.08  # Take 50% profit at 8%
    PARTIAL_PROFIT_RATIO: float = 0.5 # Sell 50% of position

class OptimizedBuyHoldTrendStrategy:
    """
    Optimized Enhanced Buy & Hold Trend Following Strategy
    
    Improvements based on backtest analysis:
    1. Tighter entry conditions to improve win rate
    2. Enhanced risk management to reduce drawdown
    3. Sector diversification rules
    4. Volume and momentum filters
    5. Partial profit taking
    6. Dynamic position sizing
    """
    
    def __init__(self, config: OptimizedConfig = None):
        self.config = config or OptimizedConfig()
        self.positions = {}
        self.daily_pnl = 0
        self.sector_positions = {}  # Track positions by sector
        
        logger.info("Initialized Optimized Enhanced Buy & Hold Strategy")
        logger.info(f"Key parameters: Signal strength {self.config.MIN_SIGNAL_STRENGTH}, "
                   f"Max position {self.config.MAX_POSITION_SIZE:.1%}, "
                   f"Stop loss {self.config.STOP_LOSS_PCT:.1%}")
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators with optimized parameters"""
        
        # Price-based indicators
        df['sma_20'] = df['close'].rolling(window=self.config.MA_SHORT).mean()
        df['sma_50'] = df['close'].rolling(window=self.config.MA_LONG).mean()
        
        # Volume analysis
        df['volume_20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_20']
        
        # RSI with optimized parameters
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.config.RSI_PERIOD).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.config.RSI_PERIOD).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=self.config.MACD_FAST).mean()
        exp2 = df['close'].ewm(span=self.config.MACD_SLOW).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=self.config.MACD_SIGNAL).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Stochastic RSI
        rsi_low = df['rsi'].rolling(window=self.config.STOCH_RSI_PERIOD).min()
        rsi_high = df['rsi'].rolling(window=self.config.STOCH_RSI_PERIOD).max()
        stoch_rsi = (df['rsi'] - rsi_low) / (rsi_high - rsi_low) * 100
        
        df['stoch_rsi_k'] = stoch_rsi.rolling(window=self.config.STOCH_RSI_K_PERIOD).mean()
        df['stoch_rsi_d'] = df['stoch_rsi_k'].rolling(window=self.config.STOCH_RSI_D_PERIOD).mean()
        
        # ADX for trend strength
        high_low = df['high'] - df['low']
        high_close_prev = np.abs(df['high'] - df['close'].shift(1))
        low_close_prev = np.abs(df['low'] - df['close'].shift(1))
        
        true_range = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
        atr = true_range.rolling(window=14).mean()
        
        plus_dm = np.where((df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']),
                          np.maximum(df['high'] - df['high'].shift(1), 0), 0)
        minus_dm = np.where((df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)),
                           np.maximum(df['low'].shift(1) - df['low'], 0), 0)
        
        plus_di = 100 * (pd.Series(plus_dm).rolling(window=14).mean() / atr)
        minus_di = 100 * (pd.Series(minus_dm).rolling(window=14).mean() / atr)
        
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        df['adx'] = dx.rolling(window=14).mean()
        
        return df
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Alias for calculate_technical_indicators to maintain compatibility"""
        return self.calculate_technical_indicators(df)
    
    def calculate_signal_strength(self, row: pd.Series) -> float:
        """Calculate enhanced signal strength with optimized criteria"""
        
        signal_strength = 0.0
        max_strength = 0.0
        
        # Primary Trend Analysis (40% weight)
        trend_weight = 0.4
        trend_score = 0.0
        
        # Price above moving averages
        if row['close'] > row['sma_20'] > row['sma_50']:
            trend_score += 0.4
        elif row['close'] > row['sma_20']:
            trend_score += 0.2
        
        # Strong trend confirmation (ADX)
        if row['adx'] > self.config.MIN_TREND_STRENGTH:
            trend_score += 0.3
        elif row['adx'] > 20:
            trend_score += 0.15
        
        # MACD trend confirmation
        if row['macd'] > row['macd_signal'] and row['macd_histogram'] > 0:
            trend_score += 0.3
        elif row['macd'] > row['macd_signal']:
            trend_score += 0.15
        
        signal_strength += trend_score * trend_weight
        max_strength += trend_weight
        
        # RSI Health Check (25% weight)
        rsi_weight = 0.25
        rsi_score = 0.0
        
        if self.config.RSI_HEALTHY_MIN <= row['rsi'] <= self.config.RSI_HEALTHY_MAX:
            rsi_score = 1.0
        elif row['rsi'] < self.config.RSI_OVERSOLD:
            rsi_score = 0.8  # Oversold can be good for entry
        elif row['rsi'] > self.config.RSI_OVERBOUGHT:
            rsi_score = 0.0  # Avoid overbought
        else:
            rsi_score = 0.5
        
        signal_strength += rsi_score * rsi_weight
        max_strength += rsi_weight
        
        # Enhanced Momentum (20% weight)
        momentum_weight = 0.2
        momentum_score = 0.0
        
        # Stochastic RSI momentum
        if (row['stoch_rsi_k'] < self.config.STOCH_RSI_OVERSOLD and 
            row['stoch_rsi_k'] > row['stoch_rsi_d']):
            momentum_score += 0.6  # Bullish crossover from oversold
        elif row['stoch_rsi_k'] > row['stoch_rsi_d']:
            momentum_score += 0.3
        
        # Price momentum
        if row['close'] > row['close'] * 1.02:  # Simple momentum check
            momentum_score += 0.4
        
        signal_strength += momentum_score * momentum_weight
        max_strength += momentum_weight
        
        # Volume Confirmation (15% weight)
        volume_weight = 0.15
        volume_score = 0.0
        
        if row['volume_ratio'] >= self.config.MIN_VOLUME_RATIO:
            volume_score = 1.0
        elif row['volume_ratio'] >= 1.2:
            volume_score = 0.6
        elif row['volume_ratio'] >= 1.0:
            volume_score = 0.3
        
        signal_strength += volume_score * volume_weight
        max_strength += volume_weight
        
        # Normalize to 0-1 range
        return signal_strength / max_strength if max_strength > 0 else 0.0
    
    def should_enter_position(self, symbol: str, row: pd.Series, portfolio_value: float, 
                            sector: str = None) -> Tuple[bool, str]:
        """Enhanced entry logic with optimized conditions"""
        
        # Check if already have position
        if symbol in self.positions:
            return False, "Already have position"
        
        # Check maximum open positions
        if len(self.positions) >= self.config.MAX_OPEN_POSITIONS:
            return False, "Max open positions reached"
        
        # Check sector diversification
        if sector and self.sector_positions.get(sector, 0) >= self.config.MAX_SECTOR_POSITIONS:
            return False, f"Max positions in {sector} sector"
        
        # Check daily loss limit
        if self.daily_pnl < -portfolio_value * self.config.MAX_DAILY_LOSS_PCT:
            return False, "Daily loss limit reached"
        
        # Calculate signal strength
        signal_strength = self.calculate_signal_strength(row)
        
        # Check minimum signal strength (enhanced threshold)
        if signal_strength < self.config.MIN_SIGNAL_STRENGTH:
            return False, f"Signal strength {signal_strength:.2f} below threshold {self.config.MIN_SIGNAL_STRENGTH}"
        
        # Additional volume filter
        if row['volume_ratio'] < self.config.MIN_VOLUME_RATIO:
            return False, f"Volume too low: {row['volume_ratio']:.2f}x average"
        
        # Trend strength filter
        if row['adx'] < self.config.MIN_TREND_STRENGTH:
            return False, f"Trend too weak: ADX {row['adx']:.1f}"
        
        # Enhanced RSI filter
        if (row['rsi'] > self.config.RSI_OVERBOUGHT or 
            row['rsi'] < self.config.RSI_OVERSOLD):
            return False, f"RSI extreme level: {row['rsi']:.1f}"
        
        return True, f"Strong entry signal: {signal_strength:.2f}"
    
    def should_exit_position(self, symbol: str, row: pd.Series, position: Dict) -> Tuple[bool, str]:
        """Enhanced exit logic with optimized conditions"""
        
        current_price = row['close']
        entry_price = position['entry_price']
        current_return = (current_price - entry_price) / entry_price
        
        # Stop loss (tighter)
        if current_return <= -self.config.STOP_LOSS_PCT:
            return True, "stop_loss"
        
        # Target achievement (adjusted)
        if current_return >= self.config.TARGET_PCT:
            return True, "target_achieved"
        
        # Trailing stop
        if 'max_return' not in position:
            position['max_return'] = current_return
        else:
            position['max_return'] = max(position['max_return'], current_return)
            
            # If we've made good profit and now declining
            if (position['max_return'] > 0.05 and 
                current_return < position['max_return'] - self.config.TRAILING_STOP_PCT):
                return True, "trailing_stop"
        
        # Enhanced technical exits
        
        # RSI overbought with Stochastic RSI confirmation
        if (row['rsi'] > self.config.RSI_OVERBOUGHT and 
            row['stoch_rsi_k'] > self.config.STOCH_RSI_OVERBOUGHT and
            row['stoch_rsi_k'] < row['stoch_rsi_d']):  # Bearish crossover
            return True, "technical_exit_rsi_stoch_overbought"
        
        # MACD bearish crossover with RSI warning
        if (row['macd'] < row['macd_signal'] and 
            row['macd_histogram'] < 0 and
            row['rsi'] > 60):
            return True, "technical_exit_macd_bearish"
        
        # Trend reversal (price below both MAs with weak ADX)
        if (row['close'] < row['sma_20'] < row['sma_50'] and 
            row['adx'] < 20):
            return True, "trend_reversal"
        
        # Volume-based exit (very low volume in uptrend)
        if (current_return > 0.03 and row['volume_ratio'] < 0.5):
            return True, "low_volume_exit"
        
        return False, "hold"
    
    def should_partial_exit(self, symbol: str, row: pd.Series, position: Dict) -> bool:
        """Check if should take partial profits"""
        
        if position.get('partial_taken', False):
            return False
        
        current_price = row['close']
        entry_price = position['entry_price']
        current_return = (current_price - entry_price) / entry_price
        
        # Take partial profits at configured level
        if current_return >= self.config.PARTIAL_PROFIT_PCT:
            return True
        
        return False
    
    def execute_partial_exit(self, symbol: str, position: Dict) -> Dict:
        """Execute partial profit taking"""
        
        partial_quantity = int(position['quantity'] * self.config.PARTIAL_PROFIT_RATIO)
        remaining_quantity = position['quantity'] - partial_quantity
        
        # Mark partial as taken
        position['partial_taken'] = True
        position['quantity'] = remaining_quantity
        position['partial_quantity'] = partial_quantity
        
        logger.info(f"Partial exit for {symbol}: Sold {partial_quantity} shares, "
                   f"keeping {remaining_quantity}")
        
        return {
            'symbol': symbol,
            'action': 'partial_exit',
            'quantity': partial_quantity,
            'remaining_quantity': remaining_quantity
        }
    
    def get_position_size(self, symbol: str, price: float, portfolio_value: float, 
                         signal_strength: float) -> int:
        """Dynamic position sizing based on signal strength and volatility"""
        
        # Base position size
        base_size = portfolio_value * self.config.MAX_POSITION_SIZE
        
        # Adjust based on signal strength
        signal_multiplier = 0.5 + (signal_strength * 0.5)  # 0.5x to 1.0x
        adjusted_size = base_size * signal_multiplier
        
        # Calculate shares
        shares = int(adjusted_size / price)
        
        return max(1, shares)  # At least 1 share
    
    def reset_daily_tracking(self):
        """Reset daily P&L and sector tracking"""
        self.daily_pnl = 0
        # Don't reset sector positions as they should persist
    
    def update_sector_positions(self, symbol: str, sector: str, action: str):
        """Update sector position tracking"""
        if action == 'buy':
            self.sector_positions[sector] = self.sector_positions.get(sector, 0) + 1
        elif action == 'sell':
            self.sector_positions[sector] = max(0, self.sector_positions.get(sector, 0) - 1)
    
    def get_strategy_info(self) -> Dict:
        """Get current strategy configuration and status"""
        return {
            'name': 'Optimized Enhanced Buy & Hold Trend Strategy',
            'version': '2.0',
            'config': {
                'min_signal_strength': self.config.MIN_SIGNAL_STRENGTH,
                'max_position_size': self.config.MAX_POSITION_SIZE,
                'stop_loss': self.config.STOP_LOSS_PCT,
                'target': self.config.TARGET_PCT,
                'max_positions': self.config.MAX_OPEN_POSITIONS,
                'sector_limit': self.config.MAX_SECTOR_POSITIONS
            },
            'current_positions': len(self.positions),
            'sector_positions': dict(self.sector_positions),
            'daily_pnl': self.daily_pnl
        }

def create_optimized_strategy():
    """Factory function to create optimized strategy"""
    config = OptimizedConfig()
    strategy = OptimizedBuyHoldTrendStrategy(config)
    
    logger.info("Created optimized strategy with enhanced parameters")
    logger.info(f"Key improvements: "
               f"Signal threshold {config.MIN_SIGNAL_STRENGTH}, "
               f"Position size {config.MAX_POSITION_SIZE:.1%}, "
               f"Stop loss {config.STOP_LOSS_PCT:.1%}")
    
    return strategy

if __name__ == "__main__":
    # Test the optimized strategy
    strategy = create_optimized_strategy()
    print("Optimized Enhanced Buy & Hold Strategy Created!")
    print(f"Configuration: {strategy.get_strategy_info()}")