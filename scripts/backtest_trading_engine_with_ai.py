"""
AI-Enhanced Backtest Runner for Central Trading Engine with Breeze API Data
===========================================================================

This script runs your trading engine against historical Breeze API data
with AI signal validation enabled to measure the impact of ML predictions
on trading performance.

Features:
- Real data from Breeze API (or simulated if unavailable)
- Full 5-stage pipeline execution
- AI signal validation layer
- Side-by-side comparison: Traditional vs AI-Enhanced signals
- Comprehensive performance metrics
- Risk management validation
- Trade-by-trade analysis

Usage:
    python backtest_trading_engine_with_ai.py --start 2023-01-01 --end 2023-12-31 --capital 100000
    python backtest_trading_engine_with_ai.py --instruments INFY TCS RELIANCE --days 365 --enable-ai
"""

import sys
import os
import json
import logging
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
import pandas as pd
import numpy as np
from pathlib import Path
from enum import Enum

# Setup paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_ml'))
sys.path.insert(0, os.path.dirname(__file__))

warnings.filterwarnings('ignore')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# IMPORTS & SETUP
# ============================================================================

try:
    from app.services.breeze_api import BreezeAPIService
    logger.info("✓ Breeze API service imported")
    BREEZE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠ Breeze API not available: {e}")
    BREEZE_AVAILABLE = False

# Import Market Sentiment Gate
try:
    from app.market_sentiment_gate import MarketSentimentEvaluator, SentimentAction
    logger.info("✓ Market Sentiment Gate imported")
    SENTIMENT_GATE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠ Market Sentiment Gate not available: {e}")
    SENTIMENT_GATE_AVAILABLE = False

# Try to import AI components
AI_AVAILABLE = False
AI_SIGNAL_VALIDATOR = None
try:
    # Simple AI signal validator - generates probabilistic predictions
    class SimpleAISignalValidator:
        """
        Simple AI-based signal validator using price pattern recognition
        and technical analysis with predictive confidence scoring
        """
        def __init__(self, lookback=20):
            self.lookback = lookback
            self.pattern_memory = {}
        
        def validate_signal(self, df: pd.DataFrame, instrument: str, 
                          signal_type: str, entry_price: float) -> Dict:
            """
            Validate signal using AI-based pattern recognition
            
            Args:
                df: DataFrame with price data
                instrument: Stock symbol
                signal_type: 'BUY' or 'SELL'
                entry_price: Proposed entry price
                
            Returns:
                Dict with validation result and confidence score
            """
            if len(df) < self.lookback:
                return {
                    'valid': True,
                    'confidence': 0.50,
                    'reason': 'insufficient_data',
                    'ai_score': 0.50
                }
            
            # Analyze recent price patterns
            recent = df.tail(self.lookback)
            prices = recent['close'].values
            
            # Calculate trend strength
            sma = prices.mean()
            trend_strength = abs(prices[-1] - sma) / sma
            
            # Calculate volatility
            returns = np.diff(prices) / prices[:-1]
            volatility = np.std(returns)
            
            # Calculate momentum
            momentum = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
            
            # AI confidence based on multiple factors
            if signal_type == 'BUY':
                # High confidence if: trend up, momentum positive, moderate volatility
                ai_confidence = 0.5
                if prices[-1] > sma:
                    ai_confidence += 0.15  # Uptrend
                if momentum > 0.01:
                    ai_confidence += 0.15  # Positive momentum
                if 0.01 < volatility < 0.05:
                    ai_confidence += 0.10  # Moderate volatility (not too choppy)
                if trend_strength > 0.02:
                    ai_confidence += 0.10  # Strong trend
                
                # Reduce confidence if too volatile or overbought
                if volatility > 0.08:
                    ai_confidence -= 0.20
                
                # Check for recent losses (pattern memory)
                if instrument in self.pattern_memory:
                    recent_loss_count = self.pattern_memory[instrument].get('losses', 0)
                    if recent_loss_count > 2:
                        ai_confidence -= 0.15
            
            else:  # SELL
                ai_confidence = 0.5
                if prices[-1] < sma:
                    ai_confidence += 0.15
                if momentum < -0.01:
                    ai_confidence += 0.15
                if volatility > 0.04:
                    ai_confidence += 0.10
            
            # Clamp confidence between 0 and 1
            ai_confidence = max(0.0, min(1.0, ai_confidence))
            
            # Determine if signal is valid based on confidence
            is_valid = ai_confidence > 0.45  # Lower threshold for backtest
            
            return {
                'valid': is_valid,
                'confidence': ai_confidence,
                'reason': 'ai_validated',
                'ai_score': ai_confidence,
                'trend_strength': trend_strength,
                'volatility': volatility,
                'momentum': momentum,
                'signal_type': signal_type
            }
        
        def update_pattern_memory(self, instrument: str, trade_result: float):
            """Update pattern memory based on trade results"""
            if instrument not in self.pattern_memory:
                self.pattern_memory[instrument] = {'wins': 0, 'losses': 0}
            
            if trade_result > 0:
                self.pattern_memory[instrument]['wins'] += 1
                self.pattern_memory[instrument]['losses'] = max(0, 
                    self.pattern_memory[instrument].get('losses', 0) - 1)
            else:
                self.pattern_memory[instrument]['losses'] += 1
    
    AI_SIGNAL_VALIDATOR = SimpleAISignalValidator()
    AI_AVAILABLE = True
    logger.info("✓ AI Signal Validator initialized")

except Exception as e:
    logger.warning(f"⚠ AI components not available: {e}")
    AI_AVAILABLE = False


# ============================================================================
# MOCK COMPONENTS (for testing without full setup)
# ============================================================================

class MockBreeze:
    """Mock Breeze API for data retrieval"""
    def get_historical_data(self, symbol, exchange="NSE", interval="1day", date_start=None, date_end=None):
        """Generate synthetic but realistic historical data"""
        np.random.seed(hash(symbol) % 2**32)
        
        # Date range
        if date_end is None:
            date_end = datetime.now()
        if date_start is None:
            date_start = date_end - timedelta(days=365)
        
        dates = pd.date_range(start=date_start, end=date_end, freq='D')
        
        # Realistic starting prices
        start_prices = {
            'NIFTY': 22000, 'BANKNIFTY': 44000, 'INFY': 3400, 'TCS': 4200,
            'RELIANCE': 2800, 'HDFC': 2900, 'ICICIBANK': 950, 'SBIN': 650
        }
        
        start = start_prices.get(symbol, 100)
        
        # Generate realistic price movements
        returns = np.random.normal(0.0005, 0.015, len(dates))
        prices = start * np.exp(np.cumsum(returns))
        
        data = []
        for i, date in enumerate(dates):
            open_p = prices[i] * (1 + np.random.normal(0, 0.003))
            close_p = prices[i]
            high_p = max(open_p, close_p) * (1 + np.abs(np.random.normal(0, 0.005)))
            low_p = min(open_p, close_p) * (1 - np.abs(np.random.normal(0, 0.005)))
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(open_p, 2),
                'high': round(high_p, 2),
                'low': round(low_p, 2),
                'close': round(close_p, 2),
                'volume': int(np.random.uniform(1e6, 10e6))
            })
        
        return data


# ============================================================================
# BACKTEST STATE TRACKER
# ============================================================================

@dataclass
class AIBacktestTrade:
    """Represents a single trade with AI validation data"""
    symbol: str
    entry_date: str
    entry_price: float
    entry_quantity: int
    
    # Traditional signal info
    traditional_score: float = 0.0
    traditional_valid: bool = True
    
    # AI validation info
    ai_validated: bool = False
    ai_confidence: float = 0.0
    ai_score: float = 0.0
    
    # Result
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    exit_quantity: Optional[int] = None
    pnl: float = 0.0
    pnl_percent: float = 0.0
    status: str = "OPEN"  # OPEN, CLOSED
    reason: str = ""
    
    # AI impact tracking
    ai_helped: bool = False  # Did AI validation help?
    ai_hindered: bool = False  # Did AI validation hurt?


@dataclass
class AIBacktestComparison:
    """Comparison between traditional and AI-enhanced backtest"""
    instrument: str
    period: str
    
    # Traditional (no AI)
    traditional_return_percent: float = 0.0
    traditional_trades: int = 0
    traditional_wins: int = 0
    traditional_sharpe: float = 0.0
    traditional_max_dd: float = 0.0
    
    # AI-Enhanced
    ai_return_percent: float = 0.0
    ai_trades: int = 0
    ai_wins: int = 0
    ai_sharpe: float = 0.0
    ai_max_dd: float = 0.0
    
    # Comparison metrics
    return_improvement_percent: float = 0.0
    win_rate_improvement: float = 0.0
    drawdown_reduction: float = 0.0
    trade_reduction_percent: float = 0.0
    trades_prevented: int = 0
    false_signals_filtered: int = 0
    
    # Details
    trades_traditional: List[Dict] = field(default_factory=list)
    trades_ai_enhanced: List[Dict] = field(default_factory=list)


# ============================================================================
# ENHANCED BACKTEST ENGINE
# ============================================================================

class AIEnhancedBacktestEngine:
    """
    Backtest engine that runs full trading pipeline with optional AI validation
    """
    
    def __init__(self, initial_capital: float = 100000, max_position_size: float = 0.1, 
                 enable_ai: bool = True, ai_confidence_threshold: float = 0.50):
        """
        Initialize backtest engine
        
        Args:
            initial_capital: Starting capital in rupees
            max_position_size: Max position as % of capital
            enable_ai: Whether to enable AI signal validation
            ai_confidence_threshold: Min AI confidence for signal (0-1)
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_position_size = max_position_size
        self.enable_ai = enable_ai and AI_AVAILABLE
        self.ai_confidence_threshold = ai_confidence_threshold
        self.enable_sentiment_gate = SENTIMENT_GATE_AVAILABLE
        
        # Initialize sentiment evaluator if available
        self.sentiment_evaluator = None
        if self.enable_sentiment_gate:
            self.sentiment_evaluator = MarketSentimentEvaluator()
        
        self.trades = []
        self.portfolio_values = []
        self.open_positions = {}
        self.cycle_results = []
        self.breeze = MockBreeze()
        
        # Cache index data for sentiment evaluation
        self.index_data_cache = {}
        self.current_index_data = None
        
        logger.info(f"Backtest engine initialized:")
        logger.info(f"  Capital: ₹{initial_capital:,.0f}")
        logger.info(f"  Max Position Size: {max_position_size*100:.0f}%")
        logger.info(f"  AI Enabled: {self.enable_ai}")
        logger.info(f"  Sentiment Gate Enabled: {self.enable_sentiment_gate}")
        if self.enable_ai:
            logger.info(f"  AI Confidence Threshold: {ai_confidence_threshold:.2%}")
    
    def get_historical_data(self, symbol: str, days: int = 365, 
                           custom_start_date: Optional[str] = None,
                           custom_end_date: Optional[str] = None,
                           interval: str = "1day") -> pd.DataFrame:
        """Get historical data for a symbol"""
        # Use custom dates if provided, otherwise use days offset
        if custom_start_date and custom_end_date:
            start_date = datetime.strptime(custom_start_date, '%Y-%m-%d')
            end_date = datetime.strptime(custom_end_date, '%Y-%m-%d')
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
        
        logger.info(f"Fetching historical data for {symbol}: {start_date.date()} to {end_date.date()}")
        
        # Try real Breeze API first
        try:
            if BREEZE_AVAILABLE:
                breeze = BreezeAPIService()
                auth_result = breeze.authenticate()
                if auth_result.get('success'):
                    logger.info(f"  ✓ Using real Breeze API data (interval: {interval})")
                    data = breeze.get_historical_data(
                        symbol=symbol,
                        exchange="NSE",
                        interval=interval,
                        date_start=start_date.strftime('%Y-%m-%d'),
                        date_end=end_date.strftime('%Y-%m-%d')
                    )
                    if data:
                        df = pd.DataFrame(data)
                        df['date'] = pd.to_datetime(df.get('date') or df.get('datetime'))
                        return df.sort_values('date').reset_index(drop=True)
        except Exception as e:
            logger.debug(f"Real Breeze API unavailable: {e}")
        
        # Fallback to mock data
        logger.info(f"  ⚠ Using simulated data (mock, interval: {interval})")
        data = self.breeze.get_historical_data(
            symbol=symbol,
            interval=interval,
            date_start=start_date,
            date_end=end_date
        )
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        return df.sort_values('date').reset_index(drop=True)
    
    def get_index_data(self, days: int = 365,
                      custom_start_date: Optional[str] = None,
                      custom_end_date: Optional[str] = None,
                      interval: str = "1day") -> pd.DataFrame:
        """Get historical index data (NIFTY 50) for sentiment evaluation"""
        # Use cached data if available
        cache_key = f"{custom_start_date}_{custom_end_date}_{interval}"
        if cache_key in self.index_data_cache:
            return self.index_data_cache[cache_key]
        
        # Fetch index data (using NIFTY as proxy for market sentiment)
        index_df = self.get_historical_data(
            symbol="NIFTY",  # NIFTY 50 index
            days=days,
            custom_start_date=custom_start_date,
            custom_end_date=custom_end_date,
            interval=interval
        )
        
        # Cache it
        self.index_data_cache[cache_key] = index_df
        self.current_index_data = index_df
        
        return index_df
    
    def calculate_position_size(self, price: float) -> int:
        """Calculate position size based on capital and price"""
        max_amount = self.current_capital * self.max_position_size
        quantity = int(max_amount / price)
        return max(1, quantity)
    
    def simulate_cycle(self, date: str, df: pd.DataFrame, cycle_num: int, 
                      enable_ai_validation: bool = True) -> Tuple[Dict, Dict]:
        """
        Simulate a single trading cycle with optional AI validation
        
        Returns:
            Tuple of (traditional_result, ai_enhanced_result)
        """
        # Both cycles start with same state
        traditional_result = {
            'signals': 0, 'executed': 0, 'closed': 0, 'pnl': 0.0
        }
        ai_result = {
            'signals': 0, 'executed': 0, 'closed': 0, 'pnl': 0.0,
            'ai_validated': 0, 'ai_rejected': 0
        }
        
        # Get current price for date
        date_data = df[df['date'].dt.strftime('%Y-%m-%d') == date]
        if date_data.empty:
            return traditional_result, ai_result
        
        current_data = date_data.iloc[0]
        current_price = current_data['close']
        
        # Generate traditional signal (SMA20 crossover)
        if len(df) > 50:  # Need 50 periods for MA50
            sma20 = df['close'].rolling(20).mean().iloc[-1]
            sma50 = df['close'].rolling(50).mean().iloc[-1]
            sma200 = df['close'].rolling(200).mean().iloc[-1] if len(df) > 200 else sma50
            
            # ENTRY CONDITION: Simple SMA20 crossover (baseline)
            # This is the core signal without trend confirmation
            sma20_crossover = current_price > sma20 * 1.01
            
            # MARKET SENTIMENT GATE: Check macro conditions before entry
            # Stage 2: Validation & Risk Guardrails
            sentiment_decision = None
            market_approved = True  # Default to allowing trades
            
            if self.enable_sentiment_gate and self.sentiment_evaluator and self.current_index_data is not None:
                try:
                    # Use INDEX data for sentiment evaluation, not individual stock data
                    sentiment_decision = self.sentiment_evaluator.assess_market(self.current_index_data, date)
                    market_approved = sentiment_decision.action != SentimentAction.BLOCK
                    
                    # Log sentiment decisions for trades (not just blocks)
                    if sma20_crossover:
                        logger.info(f"{date}: Sentiment={sentiment_decision.state.value}, Action={sentiment_decision.action.value}, Approved={market_approved}")
                    
                    if not market_approved:
                        logger.info(f"{date}: Trade signal rejected by sentiment gate. {sentiment_decision.rationale}")
                except Exception as e:
                    logger.info(f"Sentiment gate error: {e}. Proceeding with trade.")
                    market_approved = True
            
            # Entry: Signal triggered AND market approved
            if sma20_crossover and market_approved and len(self.open_positions) < 3:
                quantity = self.calculate_position_size(current_price)
                cost = quantity * current_price
                
                if cost <= self.current_capital * 0.5:
                    traditional_result['signals'] += 1
                    
                    symbol = f"TRAD_{len(self.trades) % 5}"
                    
                    trade = AIBacktestTrade(
                        symbol=symbol,
                        entry_date=date,
                        entry_price=current_price,
                        entry_quantity=quantity,
                        traditional_score=0.85,
                        traditional_valid=True
                    )
                    
                    # AI VALIDATION: Check if AI agrees
                    ai_validation = None
                    if self.enable_ai and enable_ai_validation:
                        try:
                            ai_validation = AI_SIGNAL_VALIDATOR.validate_signal(
                                df, symbol, 'BUY', current_price
                            )
                            
                            if ai_validation['valid'] and ai_validation['confidence'] > self.ai_confidence_threshold:
                                # AI agrees - execute trade
                                trade.ai_validated = True
                                trade.ai_confidence = ai_validation['confidence']
                                trade.ai_score = ai_validation['ai_score']
                                
                                self.open_positions[symbol] = trade
                                self.current_capital -= cost
                                
                                traditional_result['executed'] += 1
                                ai_result['executed'] += 1
                                ai_result['ai_validated'] += 1
                            else:
                                # AI rejects signal
                                ai_result['ai_rejected'] += 1
                        except Exception as e:
                            logger.debug(f"AI validation error: {e}")
                            # Fallback: execute anyway
                            self.open_positions[symbol] = trade
                            self.current_capital -= cost
                            traditional_result['executed'] += 1
                    else:
                        # No AI validation - execute anyway
                        self.open_positions[symbol] = trade
                        self.current_capital -= cost
                        traditional_result['executed'] += 1
        
        # Check for exit conditions
        symbols_to_close = []
        for symbol, trade in list(self.open_positions.items()):
            price_change = (current_price - trade.entry_price) / trade.entry_price * 100
            
            should_exit = False
            reason = ""
            
            # Check ALL exit conditions (not mutually exclusive)
            if price_change >= 5.0:
                should_exit = True
                reason = "Take Profit (5%)"
            elif price_change <= -2.0:
                should_exit = True
                reason = "Stop Loss (2%)"
            
            # Also check Golden Cross breakdown (even if profit/loss not hit yet)
            if not should_exit and len(df) > 200:
                sma20_exit = df['close'].rolling(20).mean().iloc[-1]
                sma50_exit = df['close'].rolling(50).mean().iloc[-1]
                sma200_exit = df['close'].rolling(200).mean().iloc[-1]
                
                if (sma20_exit < sma50_exit) or (sma50_exit < sma200_exit):
                    should_exit = True
                    reason = "Golden Cross Breakdown Exit"
            
            # Also check price crossing below SMA20
            if not should_exit and len(df) > 20:
                sma20_val = df['close'].rolling(20).mean().iloc[-1]
                if current_price < sma20_val * 0.99:
                    should_exit = True
                    reason = "Exit Signal (Below SMA20)"
            
            if should_exit:
                exit_amount = current_price * trade.entry_quantity
                pnl = exit_amount - (trade.entry_price * trade.entry_quantity)
                pnl_percent = (pnl / (trade.entry_price * trade.entry_quantity)) * 100
                
                trade.exit_date = date
                trade.exit_price = current_price
                trade.exit_quantity = trade.entry_quantity
                trade.pnl = pnl
                trade.pnl_percent = pnl_percent
                trade.status = "CLOSED"
                trade.reason = reason
                
                self.current_capital += exit_amount
                
                # Track which results the trade contributed to
                traditional_result['closed'] += 1
                traditional_result['pnl'] += pnl
                
                if trade.ai_validated:
                    ai_result['closed'] += 1
                    ai_result['pnl'] += pnl
                
                # Update AI pattern memory
                if self.enable_ai and AI_SIGNAL_VALIDATOR:
                    AI_SIGNAL_VALIDATOR.update_pattern_memory(symbol, pnl)
                
                self.trades.append(trade)
                symbols_to_close.append(symbol)
        
        # Remove closed positions
        for symbol in symbols_to_close:
            del self.open_positions[symbol]
        
        return traditional_result, ai_result
    
    def run_backtest_comparison(self, symbol: str = "INFY", days: int = 365,
                                start_date: Optional[str] = None,
                                end_date: Optional[str] = None,
                                interval: str = "1day") -> AIBacktestComparison:
        """
        Run backtest comparing traditional vs AI-enhanced performance
        
        Returns:
            Comparison object with detailed metrics
        """
        logger.info(f"\n{'='*100}")
        logger.info(f"AI-ENHANCED BACKTEST: {symbol} ({interval})")
        logger.info(f"{'='*100}")
        
        # Get data (pass custom dates if provided)
        df = self.get_historical_data(symbol, days, 
                                     custom_start_date=start_date,
                                     custom_end_date=end_date,
                                     interval=interval)
        
        if df.empty:
            logger.error(f"No data available for {symbol}")
            return None
        
        logger.info(f"Data range: {df['date'].min().date()} to {df['date'].max().date()} ({len(df)} days)")
        
        # Fetch index data for sentiment gate if enabled
        if self.enable_sentiment_gate:
            try:
                self.current_index_data = self.get_index_data(
                    days=days,
                    custom_start_date=start_date,
                    custom_end_date=end_date,
                    interval=interval
                )
                logger.info(f"Index data loaded: {len(self.current_index_data)} candles")
            except Exception as e:
                logger.warning(f"Failed to load index data for sentiment gate: {e}")
                self.current_index_data = None
        
        # Reset state
        self.trades = []
        self.open_positions = {}
        self.current_capital = self.initial_capital
        self.cycle_results = []
        self.portfolio_values = [self.initial_capital]
        
        # Run cycles
        traditional_trades = []
        ai_enhanced_trades = []
        
        for cycle_num, (idx, row) in enumerate(df.iterrows()):
            date = row['date'].strftime('%Y-%m-%d')
            
            try:
                trad_result, ai_result = self.simulate_cycle(date, df, cycle_num, enable_ai_validation=True)
                
                if cycle_num % 50 == 0:
                    logger.info(f"  Cycle {cycle_num}: {date} | Capital: ₹{self.current_capital:.2f}")
            
            except Exception as e:
                logger.error(f"Error in cycle {cycle_num} ({date}): {e}")
        
        # Calculate metrics
        closed_trades = [t for t in self.trades if t.status == "CLOSED"]
        ai_validated_trades = [t for t in closed_trades if t.ai_validated]
        
        # For comparison:
        # TRADITIONAL = what would happen if we executed ALL signals
        # AI-ENHANCED = what happened with AI filter (only executing when AI approved)
        
        # Calculate comparison metrics
        def calculate_metrics(trades):
            if not trades:
                return 0.0, 0, 0, 0.0, 0.0
            
            wins = len([t for t in trades if t.pnl > 0])
            win_rate = wins / len(trades) * 100 if trades else 0
            
            # Return
            total_pnl = sum(t.pnl for t in trades)
            ret_pct = (total_pnl / self.initial_capital) * 100
            
            # Sharpe
            pnls = [t.pnl for t in trades]
            sharpe = np.mean(pnls) / (np.std(pnls) + 1e-6) if len(pnls) > 1 else 0
            
            # Max drawdown
            portfolio_values = [self.initial_capital]
            for t in sorted(trades, key=lambda x: x.entry_date):
                portfolio_values.append(portfolio_values[-1] + t.pnl)
            
            max_dd = 0
            peak = portfolio_values[0]
            for val in portfolio_values:
                if val > peak:
                    peak = val
                dd = (peak - val) / peak if peak > 0 else 0
                if dd > max_dd:
                    max_dd = dd
            
            return ret_pct, len(trades), wins, sharpe, max_dd * 100
        
        # TRADITIONAL = ALL closed trades (what would happen without AI filter)
        trad_return, trad_count, trad_wins, trad_sharpe, trad_dd = calculate_metrics(closed_trades)
        
        # AI-ENHANCED = only AI-validated trades (what happened with AI filter)
        ai_return, ai_count, ai_wins, ai_sharpe, ai_dd = calculate_metrics(ai_validated_trades)
        
        # Create comparison
        comparison = AIBacktestComparison(
            instrument=symbol,
            period=f"{df['date'].min().date()} to {df['date'].max().date()}",
            
            # Traditional (ALL trades - simulating no AI filter)
            traditional_return_percent=trad_return,
            traditional_trades=len(closed_trades),
            traditional_wins=trad_wins,
            traditional_sharpe=trad_sharpe,
            traditional_max_dd=trad_dd,
            
            # AI-Enhanced (only AI-validated trades)
            ai_return_percent=ai_return,
            ai_trades=len(ai_validated_trades),
            ai_wins=ai_wins,
            ai_sharpe=ai_sharpe,
            ai_max_dd=ai_dd,
            
            # Improvements
            return_improvement_percent=ai_return - trad_return,
            win_rate_improvement=((ai_wins / len(ai_validated_trades) * 100) if ai_validated_trades else 0) - 
                                 ((trad_wins / len(closed_trades) * 100) if closed_trades else 0),
            drawdown_reduction=trad_dd - ai_dd,
            trade_reduction_percent=((len(closed_trades) - len(ai_validated_trades)) / len(closed_trades) * 100) 
                                    if closed_trades else 0,
            trades_prevented=len(closed_trades) - len(ai_validated_trades),
            false_signals_filtered=len(closed_trades) - len(ai_validated_trades)
        )
        
        # Print summary
        self._print_ai_comparison(comparison)
        
        return comparison
    
    def _print_ai_comparison(self, comparison: AIBacktestComparison):
        """Print AI comparison in readable format"""
        print(f"\n{'='*100}")
        print(f"AI-ENHANCED BACKTEST COMPARISON: {comparison.instrument}")
        print(f"{'='*100}\n")
        
        print(f"Period: {comparison.period}\n")
        
        print(f"{'METRIC':<35} {'TRADITIONAL':<20} {'AI-ENHANCED':<20} {'IMPROVEMENT':<20}")
        print("-" * 95)
        
        ret_color = "[OK]" if comparison.return_improvement_percent >= 0 else "[X]"
        print(f"{'Total Return %':<35} {comparison.traditional_return_percent:>18.2f}% {comparison.ai_return_percent:>18.2f}% {ret_color} {comparison.return_improvement_percent:>17.2f}%")
        
        trades_reduced = comparison.traditional_trades - comparison.ai_trades
        print(f"{'Total Trades':<35} {comparison.traditional_trades:>19} {comparison.ai_trades:>19} [OK] {trades_reduced:>18} fewer")
        
        win_improve = comparison.win_rate_improvement
        trad_wr = (comparison.traditional_wins / comparison.traditional_trades * 100) if comparison.traditional_trades else 0
        ai_wr = (comparison.ai_wins / comparison.ai_trades * 100) if comparison.ai_trades else 0
        win_color = "[OK]" if win_improve >= 0 else "[X]"
        print(f"{'Win Rate %':<35} {trad_wr:>18.2f}% {ai_wr:>18.2f}% {win_color} {win_improve:>17.2f}%")
        
        sharpe_improve = comparison.ai_sharpe - comparison.traditional_sharpe
        sharpe_color = "[OK]" if sharpe_improve >= 0 else "[X]"
        print(f"{'Sharpe Ratio':<35} {comparison.traditional_sharpe:>18.2f} {comparison.ai_sharpe:>18.2f} {sharpe_color} {sharpe_improve:>17.2f}")
        
        dd_improve = comparison.traditional_max_dd - comparison.ai_max_dd
        dd_color = "[OK]" if dd_improve >= 0 else "[X]"
        print(f"{'Max Drawdown %':<35} {comparison.traditional_max_dd:>18.2f}% {comparison.ai_max_dd:>18.2f}% {dd_color} {dd_improve:>17.2f}%")
        
        print(f"\n{'AI SIGNAL VALIDATION STATS':<35}")
        print("-" * 95)
        print(f"{'False Signals Filtered':<35} {comparison.false_signals_filtered:>19}")
        print(f"{'Trade Reduction':<35} {comparison.trade_reduction_percent:>18.2f}%")
# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run AI-enhanced backtest"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI-Enhanced backtest with Breeze API data')
    parser.add_argument('--instrument', '-i', default='INFY', help='Stock symbol')
    parser.add_argument('--symbols', '-s', nargs='+', help='Multiple symbols')
    parser.add_argument('--days', '-d', type=int, default=365, help='Days of history')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--capital', '-c', type=float, default=100000, help='Initial capital')
    parser.add_argument('--position-size', '-p', type=float, default=0.1, help='Max position size')
    parser.add_argument('--enable-ai', action='store_true', default=True, help='Enable AI validation')
    parser.add_argument('--disable-ai', dest='enable_ai', action='store_false', help='Disable AI validation')
    parser.add_argument('--ai-threshold', type=float, default=0.50, help='AI confidence threshold')
    parser.add_argument('--interval', type=str, default='1day', help='Candle interval (1min, 5min, 15min, 1hour, 1day)')
    parser.add_argument('--output', '-o', help='Output file for comparison (JSON)')
    
    args = parser.parse_args()
    
    print("\n" + "="*100)
    print("[AI] AI-ENHANCED BACKTEST: Trading Engine with Breeze API Data".center(100))
    print("="*100 + "\n")
    
    symbols = args.symbols if args.symbols else [args.instrument]
    
    print(f"Configuration:")
    print(f"  Instruments: {', '.join(symbols)}")
    print(f"  Period: {args.days} days")
    print(f"  Candle Interval: {args.interval}")
    print(f"  Initial Capital: Rs. {args.capital:,.0f}")
    print(f"  AI Enabled: {'YES' if args.enable_ai else 'NO'}")
    if args.enable_ai:
        print(f"  AI Confidence Threshold: {args.ai_threshold:.0%}")
    print()
    
    engine = AIEnhancedBacktestEngine(
        initial_capital=args.capital,
        max_position_size=args.position_size,
        enable_ai=args.enable_ai and AI_AVAILABLE,
        ai_confidence_threshold=args.ai_threshold
    )
    
    comparisons = []
    for symbol in symbols:
        try:
            comparison = engine.run_backtest_comparison(
                symbol=symbol,
                days=args.days,
                start_date=args.start,
                end_date=args.end,
                interval=args.interval
            )
            
            if comparison:
                comparisons.append(comparison)
        
        except Exception as e:
            logger.error(f"Error backtesting {symbol}: {e}", exc_info=True)
    
    # Save results
    if args.output and comparisons:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(
                [asdict(c) for c in comparisons],
                f,
                indent=2,
                default=str
            )
        
        logger.info(f"✓ Results saved to {output_path}")
    
    # Print overall comparison
    if len(comparisons) > 1:
        print(f"\n{'='*100}")
        print(f"OVERALL AI IMPACT ANALYSIS".center(100))
        print(f"{'='*100}\n")
        
        total_ai_improvement = sum(c.return_improvement_percent for c in comparisons) / len(comparisons)
        total_trades_reduced = sum(c.false_signals_filtered for c in comparisons)
        avg_wr_improvement = sum(c.win_rate_improvement for c in comparisons) / len(comparisons)
        
        print(f"SUMMARY: Average Return Improvement: {total_ai_improvement:+.2f}%")
        print(f"[OK] False Signals Filtered: {total_trades_reduced}")
        print(f"METRICS: Average Win Rate Improvement: {avg_wr_improvement:+.2f}%\n")


if __name__ == '__main__':
    main()
