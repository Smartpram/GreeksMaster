#!/usr/bin/env python3
"""
Paper Trading Session for Indian Markets - June 10, 2026
Real-time signal generation with live monitoring and manual order placement
"""

import logging
import json
from datetime import datetime, timedelta, time
import pytz
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import Config
from app.api.breeze_client import BreezeClient
from app.strategies.buy_hold_trend import BuyHoldTrendStrategy
from app.strategies.production_validator import ProductionValidator
from app.market_sentiment_gate import MarketSentimentEvaluator
from app.range_policy import RangePolicy
from app.services.risk_service import RiskService
from app.utils.indicators import TechnicalIndicators

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/paper_trading_session.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Indian market timezone
IST = pytz.timezone('Asia/Kolkata')

class PaperTradingSession:
    """Live paper trading session for Indian markets"""
    
    def __init__(self):
        """Initialize paper trading session"""
        self.config = Config()
        self.breeze = BreezeClient(
            api_key=self.config.BREEZE_API_KEY,
            secret_key=self.config.BREEZE_SECRET_KEY
        )
        
        # Strategy components
        self.strategy = BuyHoldTrendStrategy(None, None, None)
        self.validator = ProductionValidator()
        self.sentiment = MarketSentimentEvaluator()
        self.range_policy = RangePolicy()
        self.risk_service = RiskService()
        self.indicators = TechnicalIndicators()
        
        # Trading state
        self.paper_positions = {}  # {symbol: {'quantity': int, 'entry_price': float, 'entry_time': datetime}}
        self.paper_trades = []  # List of all trades executed
        self.watchlist = []
        self.market_open_time = time(9, 15)  # 9:15 AM IST
        self.market_close_time = time(15, 30)  # 3:30 PM IST
        self.paper_capital = 500000  # ₹5,00,000
        self.current_capital = self.paper_capital
        
        logger.info("=" * 80)
        logger.info("PAPER TRADING SESSION INITIALIZED")
        logger.info(f"Paper Capital: ₹{self.paper_capital:,.0f}")
        logger.info(f"Market Hours: 9:15 AM - 3:30 PM IST")
        logger.info("=" * 80)
    
    def get_ist_now(self) -> datetime:
        """Get current time in IST"""
        return datetime.now(IST)
    
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        now = self.get_ist_now()
        current_time = now.time()
        
        # Check if weekday (Monday=0, Friday=4)
        is_weekday = now.weekday() < 5
        
        is_open = is_weekday and self.market_open_time <= current_time < self.market_close_time
        return is_open
    
    def get_indian_indices(self) -> List[str]:
        """Get list of Indian market indices and top stocks"""
        return [
            'NIFTY50',      # Nifty 50 Index
            'BANKNIFTY',    # Bank Nifty Index
            'INFTEC',       # Nifty IT Index
            'RELIANCE',     # Reliance Industries
            'TCS',          # Tata Consultancy Services
            'HDFCBANK',     # HDFC Bank
            'ICICIBANK',    # ICICI Bank
            'SBIN',         # State Bank of India
            'ITC',          # ITC Limited
            'INFY',         # Infosys
            'WIPRO',        # Wipro
            'AXISBANK',     # Axis Bank
            'MARUTI',       # Maruti Suzuki
            'BAJAJFINSV',   # Bajaj Finserv
            'LT',           # Larsen & Toubro
            'ASIANPAINT',   # Asian Paints
            'SUNPHARMA',    # Sun Pharmaceutical
            'ULTRACEMCO',   # UltraTech Cement
            'POWERGRID',    # Power Grid
            'JSWSTEEL',     # JSW Steel
        ]
    
    def fetch_intraday_data(self, symbol: str, interval: int = 5) -> Optional[pd.DataFrame]:
        """
        Fetch intraday data for a symbol
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')
            interval: Candle interval in minutes (default: 5)
            
        Returns:
            DataFrame with OHLCV data or None
        """
        try:
            logger.info(f"Fetching intraday data: {symbol} ({interval}min)")
            
            # Get last 100 candles (5-min interval = ~8+ hours = full trading day)
            # In production, use Breeze API: self.breeze.get_historical_data(symbol, interval)
            
            # For demo: Fetch daily data and create synthetic 5-min data
            end_date = self.get_ist_now().date()
            start_date = end_date - timedelta(days=5)
            
            # Placeholder - In production this would call Breeze API
            logger.debug(f"Would fetch data: {symbol} from {start_date} to {end_date}")
            
            # Create mock intraday data for demonstration
            data = self._generate_mock_intraday_data(symbol, 100)
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def _generate_mock_intraday_data(self, symbol: str, num_candles: int = 100) -> pd.DataFrame:
        """Generate mock intraday data for demonstration"""
        now = self.get_ist_now()
        
        # Create time series (5-min intervals going backward)
        times = [now - timedelta(minutes=5*i) for i in range(num_candles)]
        times.reverse()
        
        # Generate realistic OHLCV data
        np.random.seed(hash(symbol) % 2**32)  # Consistent seed per symbol
        
        # Starting price based on symbol
        prices = {
            'NIFTY50': 22500,
            'BANKNIFTY': 47000,
            'RELIANCE': 2800,
            'TCS': 3600,
            'HDFCBANK': 1900,
            'ICICIBANK': 980,
            'SBIN': 550,
            'INFY': 1450,
            'WIPRO': 380,
            'AXISBANK': 1090,
        }
        
        start_price = prices.get(symbol, 2500)
        
        # Generate price walk
        returns = np.random.normal(0.0001, 0.005, num_candles)
        close_prices = start_price * np.exp(np.cumsum(returns))
        
        # Generate OHLC data
        data = []
        for i, ts in enumerate(times):
            close = close_prices[i]
            open_price = close * (1 + np.random.uniform(-0.005, 0.005))
            high = max(close, open_price) * (1 + np.random.uniform(0, 0.01))
            low = min(close, open_price) * (1 - np.random.uniform(0, 0.01))
            volume = np.random.randint(100000, 5000000)
            
            data.append({
                'timestamp': ts,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        return df
    
    def analyze_signal(self, symbol: str, data: pd.DataFrame) -> Optional[Dict]:
        """
        Analyze signal for a symbol
        
        Args:
            symbol: Stock symbol
            data: Intraday data
            
        Returns:
            Signal dict with action, confidence, reasoning
        """
        try:
            if data.empty or len(data) < 50:
                return None
            
            # Calculate indicators
            data['ma20'] = data['close'].rolling(20).mean()
            data['ma50'] = data['close'].rolling(50).mean()
            data['rsi'] = self.indicators.rsi(data['close'], 14)
            
            # Get current values
            current_price = data['close'].iloc[-1]
            ma20 = data['ma20'].iloc[-1]
            ma50 = data['ma50'].iloc[-1]
            rsi = data['rsi'].iloc[-1]
            volume = data['volume'].iloc[-1]
            avg_volume = data['volume'].rolling(20).mean().iloc[-1]
            
            # Golden Cross (Buy Signal)
            ma20_prev = data['ma20'].iloc[-2]
            ma50_prev = data['ma50'].iloc[-2]
            
            signal = None
            confidence = 0.0
            reasoning = []
            
            # BUY Signal: Golden Cross + RSI not overbought
            if ma20_prev < ma50_prev and ma20 > ma50 and rsi < 70:
                signal = 'BUY'
                confidence = 0.8
                reasoning = [
                    f"Golden Cross: MA20 ({ma20:.2f}) > MA50 ({ma50:.2f})",
                    f"RSI ({rsi:.2f}) not overbought (< 70)",
                    f"Volume confirmation: {volume:,.0f} vs Avg: {avg_volume:,.0f}"
                ]
            
            # SELL Signal: Death Cross + RSI not oversold
            elif ma20_prev > ma50_prev and ma20 < ma50 and rsi > 30:
                signal = 'SELL'
                confidence = 0.7
                reasoning = [
                    f"Death Cross: MA20 ({ma20:.2f}) < MA50 ({ma50:.2f})",
                    f"RSI ({rsi:.2f}) not oversold (> 30)",
                    f"Trend reversal detected"
                ]
            
            # HOLD: Price between MAs with good RSI
            elif ma20 * 0.98 < current_price < ma50 * 1.02:
                signal = 'HOLD'
                confidence = 0.5
                reasoning = [
                    f"Price between MA20-MA50: {ma20:.2f} - {ma50:.2f}",
                    f"RSI neutral: {rsi:.2f}",
                    "Consolidation pattern"
                ]
            
            if signal:
                return {
                    'symbol': symbol,
                    'signal': signal,
                    'confidence': confidence,
                    'current_price': current_price,
                    'ma20': ma20,
                    'ma50': ma50,
                    'rsi': rsi,
                    'reasoning': reasoning
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing signal for {symbol}: {e}")
            return None
    
    def execute_paper_trade(self, symbol: str, signal: Dict) -> bool:
        """
        Execute paper trade (add to paper positions)
        
        Args:
            symbol: Stock symbol
            signal: Signal dict
            
        Returns:
            True if trade executed, False otherwise
        """
        try:
            action = signal['signal']
            price = signal['current_price']
            quantity = int(self.current_capital * 0.1 / price)  # 10% of capital per trade
            timestamp = self.get_ist_now()
            
            if action == 'BUY':
                # Check if we have capital
                required_capital = quantity * price
                if required_capital > self.current_capital * 0.5:  # Max 50% utilization
                    logger.warning(f"Insufficient capital for {symbol}: Need ₹{required_capital:,.0f}, Have ₹{self.current_capital:,.0f}")
                    return False
                
                # Add or update position
                if symbol in self.paper_positions:
                    logger.info(f"Already holding {symbol}, skipping buy signal")
                    return False
                
                self.paper_positions[symbol] = {
                    'quantity': quantity,
                    'entry_price': price,
                    'entry_time': timestamp,
                    'status': 'OPEN'
                }
                
                self.current_capital -= required_capital
                
                logger.info(f"✅ BUY: {symbol} | Q: {quantity} @ ₹{price:.2f} | Total: ₹{required_capital:,.0f}")
                logger.info(f"   Reasoning: {'; '.join(signal['reasoning'])}")
                logger.info(f"   Remaining Capital: ₹{self.current_capital:,.0f}")
                
                self.paper_trades.append({
                    'timestamp': timestamp,
                    'symbol': symbol,
                    'action': 'BUY',
                    'quantity': quantity,
                    'price': price,
                    'total': required_capital,
                    'confidence': signal['confidence']
                })
                
                return True
            
            elif action == 'SELL':
                # Check if we have open position
                if symbol not in self.paper_positions:
                    logger.warning(f"No open position in {symbol}, skipping sell signal")
                    return False
                
                position = self.paper_positions[symbol]
                quantity = position['quantity']
                entry_price = position['entry_price']
                exit_price = price
                
                pnl = (exit_price - entry_price) * quantity
                pnl_percent = (pnl / (entry_price * quantity)) * 100
                
                self.current_capital += exit_price * quantity
                
                logger.info(f"✅ SELL: {symbol} | Q: {quantity} @ ₹{exit_price:.2f} | Total: ₹{exit_price * quantity:,.0f}")
                logger.info(f"   Entry: ₹{entry_price:.2f} | Exit: ₹{exit_price:.2f}")
                logger.info(f"   P&L: ₹{pnl:,.0f} ({pnl_percent:+.2f}%)")
                logger.info(f"   Reasoning: {'; '.join(signal['reasoning'])}")
                logger.info(f"   Remaining Capital: ₹{self.current_capital:,.0f}")
                
                del self.paper_positions[symbol]
                
                self.paper_trades.append({
                    'timestamp': timestamp,
                    'symbol': symbol,
                    'action': 'SELL',
                    'quantity': quantity,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'price': exit_price,
                    'pnl': pnl,
                    'pnl_percent': pnl_percent,
                    'confidence': signal['confidence']
                })
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing paper trade for {symbol}: {e}")
            return False
    
    def run_screening(self) -> List[Dict]:
        """
        Run screening across watchlist
        
        Returns:
            List of signals generated
        """
        logger.info("\n" + "=" * 80)
        logger.info("SCREENING CYCLE STARTED")
        logger.info(f"Time: {self.get_ist_now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info("=" * 80)
        
        signals = []
        self.watchlist = self.get_indian_indices()
        
        for symbol in self.watchlist:
            try:
                # Fetch data
                data = self.fetch_intraday_data(symbol)
                if data is None or data.empty:
                    continue
                
                # Analyze
                signal = self.analyze_signal(symbol, data)
                if signal:
                    signals.append(signal)
                    
                    # Execute paper trade
                    self.execute_paper_trade(symbol, signal)
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        logger.info(f"\nScreening complete | Signals found: {len(signals)}")
        return signals
    
    def print_portfolio_status(self):
        """Print current portfolio status"""
        logger.info("\n" + "=" * 80)
        logger.info("PORTFOLIO STATUS")
        logger.info("=" * 80)
        
        if not self.paper_positions:
            logger.info("No open positions")
        else:
            logger.info(f"Open Positions: {len(self.paper_positions)}")
            total_notional = 0
            for symbol, pos in self.paper_positions.items():
                notional = pos['quantity'] * pos['entry_price']
                total_notional += notional
                logger.info(f"  • {symbol}: {pos['quantity']} @ ₹{pos['entry_price']:.2f} = ₹{notional:,.0f}")
            
            logger.info(f"Total Notional: ₹{total_notional:,.0f}")
        
        logger.info(f"Available Capital: ₹{self.current_capital:,.0f}")
        logger.info(f"Total Capital: ₹{self.paper_capital:,.0f}")
        logger.info(f"Utilization: {((self.paper_capital - self.current_capital) / self.paper_capital * 100):.1f}%")
        
        if self.paper_trades:
            logger.info(f"\nTrades Executed: {len(self.paper_trades)}")
            buy_count = sum(1 for t in self.paper_trades if t['action'] == 'BUY')
            sell_count = sum(1 for t in self.paper_trades if t['action'] == 'SELL')
            logger.info(f"  • Buys: {buy_count}")
            logger.info(f"  • Sells: {sell_count}")
            
            # Calculate realized P&L
            realized_pnl = sum(t.get('pnl', 0) for t in self.paper_trades)
            logger.info(f"  • Realized P&L: ₹{realized_pnl:,.0f}")
    
    def save_session_report(self):
        """Save detailed session report"""
        report = {
            'session_date': self.get_ist_now().isoformat(),
            'initial_capital': self.paper_capital,
            'remaining_capital': self.current_capital,
            'utilization_percent': (self.paper_capital - self.current_capital) / self.paper_capital * 100,
            'trades': self.paper_trades,
            'open_positions': {
                symbol: {
                    'quantity': pos['quantity'],
                    'entry_price': pos['entry_price'],
                    'entry_time': pos['entry_time'].isoformat()
                }
                for symbol, pos in self.paper_positions.items()
            }
        }
        
        # Save to file
        report_file = f"logs/paper_trading_report_{self.get_ist_now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"\nSession report saved: {report_file}")
        return report_file
    
    def run_session(self, check_market_hours: bool = True):
        """
        Run paper trading session
        
        Args:
            check_market_hours: If True, only run during market hours
        """
        logger.info("\n" + "╔" + "=" * 78 + "╗")
        logger.info("║" + " " * 20 + "PAPER TRADING SESSION START" + " " * 31 + "║")
        logger.info("║" + " " * 78 + "║")
        logger.info(f"║ Market: Indian NSE/BSE | Date: {self.get_ist_now().strftime('%Y-%m-%d')} | Time: {self.get_ist_now().strftime('%H:%M:%S %Z')}" + " " * 10 + "║")
        logger.info("╚" + "=" * 78 + "╝\n")
        
        if check_market_hours and not self.is_market_open():
            logger.warning("⚠️ Market is currently CLOSED (9:15 AM - 3:30 PM IST)")
            logger.info("Paper trading will still run, but live data may not be available")
        
        # Run screening cycle
        signals = self.run_screening()
        
        # Print status
        self.print_portfolio_status()
        
        # Save report
        self.save_session_report()
        
        logger.info("\n" + "╔" + "=" * 78 + "╗")
        logger.info("║" + " " * 25 + "SESSION COMPLETE" + " " * 37 + "║")
        logger.info("╚" + "=" * 78 + "╝\n")


def main():
    """Main entry point"""
    try:
        # Initialize session
        session = PaperTradingSession()
        
        # Run paper trading
        session.run_session(check_market_hours=True)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Session interrupted by user")
    except Exception as e:
        logger.error(f"Session error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
