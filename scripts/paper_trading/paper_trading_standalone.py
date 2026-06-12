#!/usr/bin/env python3
"""
Standalone Paper Trading Session - Indian Markets
Self-contained with no external app dependencies
"""

import logging
import json
from datetime import datetime, timedelta
import pytz
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import sys
from pathlib import Path

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

class SimpleRSI:
    """Simple RSI calculation"""
    @staticmethod
    def rsi(prices, period=14):
        """Calculate RSI"""
        prices = np.asarray(prices)
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        
        # Calculate first period values
        up_sum = np.sum(np.where(seed >= 0, seed, 0))
        down_sum = np.sum(np.where(seed < 0, -seed, 0))
        
        up = up_sum / period if period > 0 else 0
        down = down_sum / period if period > 0 else 1
        
        rsi = np.zeros_like(prices, dtype=float)
        
        for i in range(period, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
            
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            
            if down > 0:
                rs = up / down
                rsi[i] = 100. - (100. / (1. + rs))
            else:
                rsi[i] = 100.0 if up > 0 else 50.0
        
        # Fill initial period with first calculated value
        if len(rsi) > period:
            rsi[:period] = rsi[period]
        
        return rsi

class StandalonePaperTrading:
    """Standalone paper trading session for Indian markets"""
    
    def __init__(self):
        """Initialize paper trading session"""
        self.paper_positions = {}
        self.paper_trades = []
        self.watchlist = []
        self.market_open_time = datetime.strptime("09:15", "%H:%M").time()
        self.market_close_time = datetime.strptime("15:30", "%H:%M").time()
        self.paper_capital = 500000  # ₹5,00,000
        self.current_capital = self.paper_capital
        
        logger.info("=" * 80)
        logger.info("STANDALONE PAPER TRADING SESSION INITIALIZED")
        logger.info(f"Paper Capital: ₹{self.paper_capital:,.0f}")
        logger.info(f"Market Hours: 9:15 AM - 3:30 PM IST")
        logger.info("=" * 80)
    
    def get_ist_now(self) -> datetime:
        """Get current time in IST"""
        return datetime.now(IST)
    
    def generate_mock_data(self, symbol: str, num_candles: int = 100) -> pd.DataFrame:
        """Generate realistic mock intraday data"""
        now = self.get_ist_now()
        times = [now - timedelta(minutes=5*i) for i in range(num_candles)]
        times.reverse()
        
        np.random.seed(hash(symbol) % 2**32)
        
        prices = {
            'NIFTY50': 22500, 'BANKNIFTY': 47000, 'RELIANCE': 2800,
            'TCS': 3600, 'HDFCBANK': 1900, 'ICICIBANK': 980,
            'SBIN': 550, 'INFY': 1450, 'WIPRO': 380,
            'AXISBANK': 1090, 'MARUTI': 12500, 'ITC': 350,
            'ASIANPAINT': 3200, 'SUNPHARMA': 750, 'ULTRACEMCO': 11500,
            'POWERGRID': 310, 'JSWSTEEL': 920, 'LT': 3450,
            'BAJAJFINSV': 1650, 'INFTEC': 24000
        }
        
        start_price = prices.get(symbol, 2500)
        returns = np.random.normal(0.0001, 0.005, num_candles)
        close_prices = start_price * np.exp(np.cumsum(returns))
        
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
        
        return pd.DataFrame(data)
    
    def analyze_signal(self, symbol: str, data: pd.DataFrame) -> Optional[Dict]:
        """Analyze signal for a symbol"""
        try:
            if data.empty or len(data) < 50:
                return None
            
            data['ma20'] = data['close'].rolling(20).mean()
            data['ma50'] = data['close'].rolling(50).mean()
            
            # Simple RSI without using the class method (to avoid issues)
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss + 1e-10)  # Avoid division by zero
            rsi_values = 100 - (100 / (1 + rs))
            data['rsi'] = rsi_values.fillna(50)  # Fill NaN with neutral 50
            
            current_price = data['close'].iloc[-1]
            ma20 = data['ma20'].iloc[-1]
            ma50 = data['ma50'].iloc[-1]
            rsi = float(data['rsi'].iloc[-1])
            volume = data['volume'].iloc[-1]
            avg_volume = data['volume'].rolling(20).mean().iloc[-1]
            
            ma20_prev = data['ma20'].iloc[-2]
            ma50_prev = data['ma50'].iloc[-2]
            
            signal = None
            confidence = 0.0
            reasoning = []
            
            # Skip if MA values are NaN
            if pd.isna(ma20) or pd.isna(ma50) or pd.isna(rsi):
                return None
            
            # BUY: Golden Cross
            if ma20_prev < ma50_prev and ma20 > ma50 and rsi < 70:
                signal = 'BUY'
                confidence = 0.8
                reasoning = [
                    f"Golden Cross: MA20 ({ma20:.2f}) > MA50 ({ma50:.2f})",
                    f"RSI ({rsi:.2f}) not overbought",
                    f"Volume: {volume:,.0f} vs Avg: {avg_volume:,.0f}"
                ]
            
            # SELL: Death Cross
            elif ma20_prev > ma50_prev and ma20 < ma50 and rsi > 30:
                signal = 'SELL'
                confidence = 0.7
                reasoning = [
                    f"Death Cross: MA20 ({ma20:.2f}) < MA50 ({ma50:.2f})",
                    f"RSI ({rsi:.2f}) not oversold",
                    f"Trend reversal detected"
                ]
            
            if signal:
                return {
                    'symbol': symbol,
                    'signal': signal,
                    'confidence': confidence,
                    'current_price': float(current_price),
                    'ma20': float(ma20),
                    'ma50': float(ma50),
                    'rsi': float(rsi),
                    'reasoning': reasoning
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def execute_trade(self, symbol: str, signal: Dict) -> bool:
        """Execute paper trade"""
        try:
            action = signal['signal']
            price = signal['current_price']
            quantity = int(self.current_capital * 0.1 / price)
            timestamp = self.get_ist_now()
            
            if action == 'BUY':
                required_capital = quantity * price
                if required_capital > self.current_capital * 0.5:
                    logger.warning(f"Insufficient capital for {symbol}")
                    return False
                
                if symbol in self.paper_positions:
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
                    'timestamp': timestamp.isoformat(),
                    'symbol': symbol,
                    'action': 'BUY',
                    'quantity': quantity,
                    'price': price,
                    'total': required_capital,
                    'confidence': signal['confidence']
                })
                
                return True
            
            elif action == 'SELL':
                if symbol not in self.paper_positions:
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
                
                del self.paper_positions[symbol]
                
                self.paper_trades.append({
                    'timestamp': timestamp.isoformat(),
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
            logger.error(f"Error executing trade for {symbol}: {e}")
            return False
    
    def run_screening(self) -> List[Dict]:
        """Run screening across watchlist"""
        logger.info("\n" + "=" * 80)
        logger.info("SCREENING CYCLE STARTED")
        logger.info(f"Time: {self.get_ist_now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info("=" * 80)
        
        signals = []
        self.watchlist = [
            'NIFTY50', 'BANKNIFTY', 'INFTEC',
            'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'ITC', 'INFY',
            'WIPRO', 'AXISBANK', 'MARUTI', 'BAJAJFINSV', 'LT',
            'ASIANPAINT', 'SUNPHARMA', 'ULTRACEMCO', 'POWERGRID', 'JSWSTEEL'
        ]
        
        for symbol in self.watchlist:
            try:
                data = self.generate_mock_data(symbol)
                signal = self.analyze_signal(symbol, data)
                if signal:
                    signals.append(signal)
                    self.execute_trade(symbol, signal)
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
        
        logger.info(f"\nScreening complete | Signals found: {len(signals)}")
        return signals
    
    def print_status(self):
        """Print portfolio status"""
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
            
            realized_pnl = sum(t.get('pnl', 0) for t in self.paper_trades)
            logger.info(f"  • Realized P&L: ₹{realized_pnl:,.0f}")
    
    def save_report(self):
        """Save session report"""
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
        
        report_file = f"logs/paper_trading_report_{self.get_ist_now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\nSession report saved: {report_file}")
        return report_file
    
    def run(self):
        """Run paper trading session"""
        logger.info("\n" + "╔" + "=" * 78 + "╗")
        logger.info("║" + " " * 20 + "PAPER TRADING SESSION START" + " " * 31 + "║")
        logger.info("║" + " " * 78 + "║")
        logger.info(f"║ Market: Indian NSE/BSE | Date: {self.get_ist_now().strftime('%Y-%m-%d')} | Time: {self.get_ist_now().strftime('%H:%M:%S %Z')}" + " " * 10 + "║")
        logger.info("╚" + "=" * 78 + "╝\n")
        
        signals = self.run_screening()
        self.print_status()
        self.save_report()
        
        logger.info("\n" + "╔" + "=" * 78 + "╗")
        logger.info("║" + " " * 25 + "SESSION COMPLETE" + " " * 37 + "║")
        logger.info("╚" + "=" * 78 + "╝\n")


def main():
    """Main entry point"""
    try:
        Path('logs').mkdir(exist_ok=True)
        session = StandalonePaperTrading()
        session.run()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Session interrupted by user")
    except Exception as e:
        logger.error(f"Session error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
