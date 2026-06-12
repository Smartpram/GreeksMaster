#!/usr/bin/env python3
"""
Multi-Strategy Paper Trading Session - Indian Markets
Includes: Golden Cross, Mean Reversion, Momentum, Breakout strategies
Date: June 10, 2026
"""

import logging
import json
from datetime import datetime, timedelta
import pytz
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/paper_trading_multi_strategy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')

class MultiStrategyPaperTrading:
    """Multi-strategy paper trading session"""
    
    def __init__(self):
        """Initialize multi-strategy session"""
        self.paper_positions = {}
        self.paper_trades = []
        self.watchlist = []
        self.paper_capital = 500000
        self.current_capital = self.paper_capital
        self.strategy_signals = {}  # Track which strategy generated signal
        
        logger.info("=" * 80)
        logger.info("MULTI-STRATEGY PAPER TRADING SESSION INITIALIZED")
        logger.info(f"Capital: Rs {self.paper_capital:,.0f}")
        logger.info(f"Strategies: Golden Cross, Mean Reversion, Momentum, Breakout")
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
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators"""
        if data.empty or len(data) < 50:
            return data
        
        # Moving averages
        data['ma20'] = data['close'].rolling(20).mean()
        data['ma50'] = data['close'].rolling(50).mean()
        data['ma200'] = data['close'].rolling(200).mean()
        
        # RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-10)
        data['rsi'] = (100 - (100 / (1 + rs))).fillna(50)
        
        # Bollinger Bands
        data['bb_ma'] = data['close'].rolling(20).mean()
        data['bb_std'] = data['close'].rolling(20).std()
        data['bb_upper'] = data['bb_ma'] + (data['bb_std'] * 2)
        data['bb_lower'] = data['bb_ma'] - (data['bb_std'] * 2)
        data['bb_width'] = data['bb_upper'] - data['bb_lower']
        
        # MACD
        ema12 = data['close'].ewm(span=12).mean()
        ema26 = data['close'].ewm(span=26).mean()
        data['macd'] = ema12 - ema26
        data['macd_signal'] = data['macd'].ewm(span=9).mean()
        data['macd_histogram'] = data['macd'] - data['macd_signal']
        
        # ATR for breakout
        data['tr'] = np.maximum(
            data['high'] - data['low'],
            np.maximum(
                abs(data['high'] - data['close'].shift()),
                abs(data['low'] - data['close'].shift())
            )
        )
        data['atr'] = data['tr'].rolling(14).mean()
        
        # Volume
        data['volume_ma'] = data['volume'].rolling(20).mean()
        
        return data
    
    def golden_cross_signal(self, data: pd.DataFrame) -> Optional[Dict]:
        """Golden Cross Strategy: MA20 > MA50 + RSI < 70"""
        if len(data) < 50:
            return None
        
        current_price = data['close'].iloc[-1]
        ma20 = data['ma20'].iloc[-1]
        ma50 = data['ma50'].iloc[-1]
        rsi = data['rsi'].iloc[-1]
        
        ma20_prev = data['ma20'].iloc[-2]
        ma50_prev = data['ma50'].iloc[-2]
        
        # BUY: Golden Cross
        if ma20_prev < ma50_prev and ma20 > ma50 and rsi < 70:
            return {
                'action': 'BUY',
                'strategy': 'GOLDEN_CROSS',
                'confidence': 0.8,
                'price': float(current_price),
                'reasoning': f"MA20 ({ma20:.2f}) > MA50 ({ma50:.2f}), RSI {rsi:.2f}"
            }
        
        # SELL: Death Cross
        if ma20_prev > ma50_prev and ma20 < ma50 and rsi > 30:
            return {
                'action': 'SELL',
                'strategy': 'GOLDEN_CROSS',
                'confidence': 0.7,
                'price': float(current_price),
                'reasoning': f"MA20 ({ma20:.2f}) < MA50 ({ma50:.2f}), Death Cross"
            }
        
        return None
    
    def mean_reversion_signal(self, data: pd.DataFrame) -> Optional[Dict]:
        """Mean Reversion Strategy: Bollinger Band extremes + RSI"""
        if len(data) < 50:
            return None
        
        current_price = data['close'].iloc[-1]
        bb_upper = data['bb_upper'].iloc[-1]
        bb_lower = data['bb_lower'].iloc[-1]
        bb_ma = data['bb_ma'].iloc[-1]
        rsi = data['rsi'].iloc[-1]
        volume = data['volume'].iloc[-1]
        volume_ma = data['volume_ma'].iloc[-1]
        
        # BUY: Price at lower BB + RSI oversold
        if current_price < bb_lower and rsi < 30 and volume > volume_ma:
            return {
                'action': 'BUY',
                'strategy': 'MEAN_REVERSION',
                'confidence': 0.75,
                'price': float(current_price),
                'reasoning': f"Below BB-Lower ({bb_lower:.2f}), RSI {rsi:.2f} oversold, Vol spike"
            }
        
        # SELL: Price at upper BB + RSI overbought
        if current_price > bb_upper and rsi > 70 and volume > volume_ma:
            return {
                'action': 'SELL',
                'strategy': 'MEAN_REVERSION',
                'confidence': 0.75,
                'price': float(current_price),
                'reasoning': f"Above BB-Upper ({bb_upper:.2f}), RSI {rsi:.2f} overbought, Vol spike"
            }
        
        return None
    
    def momentum_signal(self, data: pd.DataFrame) -> Optional[Dict]:
        """Momentum Strategy: MACD + RSI confirmation"""
        if len(data) < 50:
            return None
        
        current_price = data['close'].iloc[-1]
        macd = data['macd'].iloc[-1]
        macd_signal = data['macd_signal'].iloc[-1]
        macd_hist = data['macd_histogram'].iloc[-1]
        rsi = data['rsi'].iloc[-1]
        macd_hist_prev = data['macd_histogram'].iloc[-2]
        
        # BUY: MACD crossover bullish + RSI > 50
        if macd_hist_prev < 0 and macd_hist > 0 and macd > macd_signal and rsi > 50:
            return {
                'action': 'BUY',
                'strategy': 'MOMENTUM',
                'confidence': 0.8,
                'price': float(current_price),
                'reasoning': f"MACD bullish crossover, RSI {rsi:.2f}, Histogram positive"
            }
        
        # SELL: MACD crossover bearish + RSI < 50
        if macd_hist_prev > 0 and macd_hist < 0 and macd < macd_signal and rsi < 50:
            return {
                'action': 'SELL',
                'strategy': 'MOMENTUM',
                'confidence': 0.8,
                'price': float(current_price),
                'reasoning': f"MACD bearish crossover, RSI {rsi:.2f}, Histogram negative"
            }
        
        return None
    
    def breakout_signal(self, data: pd.DataFrame) -> Optional[Dict]:
        """Breakout Strategy: ATR-based support/resistance breakout"""
        if len(data) < 50:
            return None
        
        current_price = data['close'].iloc[-1]
        atr = data['atr'].iloc[-1]
        high_20 = data['high'].iloc[-20:].max()
        low_20 = data['low'].iloc[-20:].min()
        volume = data['volume'].iloc[-1]
        volume_ma = data['volume_ma'].iloc[-1]
        
        resistance = high_20
        support = low_20
        
        # BUY: Breakout above resistance with volume
        if current_price > resistance and volume > volume_ma * 1.5:
            return {
                'action': 'BUY',
                'strategy': 'BREAKOUT',
                'confidence': 0.75,
                'price': float(current_price),
                'reasoning': f"Broke above resistance ({resistance:.2f}), Vol spike, ATR {atr:.2f}"
            }
        
        # SELL: Breakdown below support with volume
        if current_price < support and volume > volume_ma * 1.5:
            return {
                'action': 'SELL',
                'strategy': 'BREAKOUT',
                'confidence': 0.75,
                'price': float(current_price),
                'reasoning': f"Broke below support ({support:.2f}), Vol spike, ATR {atr:.2f}"
            }
        
        return None
    
    def analyze_symbol(self, symbol: str, data: pd.DataFrame) -> List[Dict]:
        """Analyze symbol with all strategies"""
        signals = []
        
        try:
            data = self.calculate_indicators(data)
            
            # Get signals from all strategies
            gc_signal = self.golden_cross_signal(data)
            if gc_signal:
                signals.append(gc_signal)
            
            mr_signal = self.mean_reversion_signal(data)
            if mr_signal:
                signals.append(mr_signal)
            
            mom_signal = self.momentum_signal(data)
            if mom_signal:
                signals.append(mom_signal)
            
            bo_signal = self.breakout_signal(data)
            if bo_signal:
                signals.append(bo_signal)
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
        
        return signals
    
    def execute_trade(self, symbol: str, signal: Dict) -> bool:
        """Execute paper trade"""
        try:
            action = signal['action']
            price = signal['price']
            strategy = signal['strategy']
            quantity = int(self.current_capital * 0.08 / price)  # 8% per trade
            timestamp = self.get_ist_now()
            
            if action == 'BUY':
                required_capital = quantity * price
                if required_capital > self.current_capital * 0.4:  # Max 40% utilization
                    return False
                
                if symbol in self.paper_positions:
                    return False
                
                self.paper_positions[symbol] = {
                    'quantity': quantity,
                    'entry_price': price,
                    'entry_time': timestamp,
                    'strategy': strategy
                }
                
                self.current_capital -= required_capital
                
                logger.info(f"✅ BUY ({strategy}): {symbol} | Q: {quantity} @ Rs{price:.2f} | Total: Rs{required_capital:,.0f}")
                logger.info(f"   {signal['reasoning']}")
                
                self.paper_trades.append({
                    'timestamp': timestamp.isoformat(),
                    'symbol': symbol,
                    'action': 'BUY',
                    'quantity': quantity,
                    'price': price,
                    'strategy': strategy,
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
                entry_strategy = position['strategy']
                
                logger.info(f"✅ SELL ({strategy}): {symbol} | Q: {quantity} @ Rs{exit_price:.2f} | Total: Rs{exit_price * quantity:,.0f}")
                logger.info(f"   Entry ({entry_strategy}): Rs{entry_price:.2f} | Exit: Rs{exit_price:.2f}")
                logger.info(f"   P&L: Rs{pnl:,.0f} ({pnl_percent:+.2f}%)")
                
                del self.paper_positions[symbol]
                
                self.paper_trades.append({
                    'timestamp': timestamp.isoformat(),
                    'symbol': symbol,
                    'action': 'SELL',
                    'quantity': quantity,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_percent': pnl_percent,
                    'entry_strategy': entry_strategy,
                    'exit_strategy': strategy,
                    'confidence': signal['confidence']
                })
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing trade for {symbol}: {e}")
            return False
    
    def run_screening(self) -> Dict:
        """Run screening with all strategies"""
        logger.info("\n" + "=" * 80)
        logger.info("MULTI-STRATEGY SCREENING CYCLE STARTED")
        logger.info(f"Time: {self.get_ist_now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info("Strategies: Golden Cross, Mean Reversion, Momentum, Breakout")
        logger.info("=" * 80)
        
        all_signals = {}
        self.watchlist = [
            'NIFTY50', 'BANKNIFTY', 'INFTEC',
            'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'ITC', 'INFY',
            'WIPRO', 'AXISBANK', 'MARUTI', 'BAJAJFINSV', 'LT',
            'ASIANPAINT', 'SUNPHARMA', 'ULTRACEMCO', 'POWERGRID', 'JSWSTEEL'
        ]
        
        strategy_counts = {
            'GOLDEN_CROSS': 0,
            'MEAN_REVERSION': 0,
            'MOMENTUM': 0,
            'BREAKOUT': 0
        }
        
        for symbol in self.watchlist:
            try:
                data = self.generate_mock_data(symbol)
                signals = self.analyze_symbol(symbol, data)
                
                if signals:
                    all_signals[symbol] = signals
                    for signal in signals:
                        strategy_counts[signal['strategy']] += 1
                        self.execute_trade(symbol, signal)
            
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
        
        logger.info(f"\nScreening complete")
        logger.info(f"Signals Summary:")
        logger.info(f"  • Golden Cross: {strategy_counts['GOLDEN_CROSS']}")
        logger.info(f"  • Mean Reversion: {strategy_counts['MEAN_REVERSION']}")
        logger.info(f"  • Momentum: {strategy_counts['MOMENTUM']}")
        logger.info(f"  • Breakout: {strategy_counts['BREAKOUT']}")
        logger.info(f"  • Total: {sum(strategy_counts.values())}")
        
        return strategy_counts
    
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
                logger.info(f"  • {symbol}: {pos['quantity']} @ Rs{pos['entry_price']:.2f} ({pos['strategy']})")
            logger.info(f"Total Notional: Rs{total_notional:,.0f}")
        
        logger.info(f"Available Capital: Rs{self.current_capital:,.0f}")
        logger.info(f"Total Capital: Rs{self.paper_capital:,.0f}")
        logger.info(f"Utilization: {((self.paper_capital - self.current_capital) / self.paper_capital * 100):.1f}%")
        
        if self.paper_trades:
            logger.info(f"\nTrades Executed: {len(self.paper_trades)}")
            buy_count = sum(1 for t in self.paper_trades if t['action'] == 'BUY')
            sell_count = sum(1 for t in self.paper_trades if t['action'] == 'SELL')
            logger.info(f"  • Buys: {buy_count}")
            logger.info(f"  • Sells: {sell_count}")
            
            realized_pnl = sum(t.get('pnl', 0) for t in self.paper_trades)
            logger.info(f"  • Realized P&L: Rs{realized_pnl:,.0f}")
            
            # Strategy breakdown
            strategies_used = {}
            for trade in self.paper_trades:
                if trade['action'] == 'BUY':
                    strat = trade.get('strategy', 'UNKNOWN')
                    strategies_used[strat] = strategies_used.get(strat, 0) + 1
            
            if strategies_used:
                logger.info(f"\nSignals by Strategy:")
                for strat, count in strategies_used.items():
                    logger.info(f"  • {strat}: {count}")
    
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
                    'entry_time': pos['entry_time'].isoformat(),
                    'strategy': pos['strategy']
                }
                for symbol, pos in self.paper_positions.items()
            }
        }
        
        report_file = f"logs/paper_trading_multi_strategy_{self.get_ist_now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\nSession report saved: {report_file}")
        return report_file
    
    def run(self):
        """Run multi-strategy paper trading session"""
        logger.info("\n" + "╔" + "=" * 78 + "╗")
        logger.info("║" + " " * 15 + "MULTI-STRATEGY PAPER TRADING SESSION START" + " " * 20 + "║")
        logger.info("║" + " " * 78 + "║")
        logger.info(f"║ Market: Indian NSE/BSE | Date: {self.get_ist_now().strftime('%Y-%m-%d')} | Strategies: 4" + " " * 33 + "║")
        logger.info("╚" + "=" * 78 + "╝\n")
        
        strategy_counts = self.run_screening()
        self.print_status()
        self.save_report()
        
        logger.info("\n" + "╔" + "=" * 78 + "╗")
        logger.info("║" + " " * 25 + "SESSION COMPLETE" + " " * 37 + "║")
        logger.info("╚" + "=" * 78 + "╝\n")


def main():
    """Main entry point"""
    try:
        Path('logs').mkdir(exist_ok=True)
        session = MultiStrategyPaperTrading()
        session.run()
    except KeyboardInterrupt:
        logger.info("\nSession interrupted by user")
    except Exception as e:
        logger.error(f"Session error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
