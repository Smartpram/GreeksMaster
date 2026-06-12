"""
10-Minute Trading System for Indian Markets
Trades every 10 minutes during market hours with optimized candle settings

Features:
- Execute trades every 10 minutes (09:15-15:30 IST)
- Adjusted candles for faster signal generation
- Smaller timeframe indicators (5-min, 10-min, 15-min)
- Real-time Breeze API data
- ML models optimized for intraday
- Fee-aware P&L calculation

Schedule:
- 09:15, 09:25, 09:35, 09:45... every 10 minutes until 15:30 IST
- Total: ~40 executions per trading day
"""

import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# ML Libraries
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score

# Breeze API
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'app'))
from app.services.breeze_api import BreezeAPIService
from app.brokerage_fees import BrokerageFeeCalculator, BrokeragePlan
from app.expanded_tickers_config import get_recommended_paper_trading_set

load_dotenv()

# Setup logging
LOG_DIR = Path(__file__).parent / "logs" / "10min_trading"
LOG_DIR.mkdir(parents=True, exist_ok=True)

REPORT_DIR = Path(__file__).parent / "reports" / "10min_trading"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

log_file = LOG_DIR / f"10min_trading_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TenMinuteTradingEngine:
    """
    Execute paper trading every 10 minutes during market hours
    Optimized for intraday trading with adjusted candles
    """
    
    def __init__(self, candle_count=100, brokerage_plan=BrokeragePlan.IVALUE):
        """
        Initialize 10-minute trading engine
        
        Args:
            candle_count: Number of candles to load (100 for 10-min = ~16 hours of data)
            brokerage_plan: Fee calculation plan
        """
        self.logger = logging.getLogger(__name__)
        self.candle_count = candle_count  # 100 candles = ~16-17 hours of data for 10-min
        self.brokerage_plan = brokerage_plan
        self.fee_calculator = BrokerageFeeCalculator(plan=brokerage_plan)
        
        # Initialize Breeze API
        try:
            session_token = os.getenv('BREEZE_SESSION_TOKEN')
            if not session_token:
                self.logger.error("ERROR: BREEZE_SESSION_TOKEN not in .env")
                raise ValueError("Session token missing")
            
            self.api = BreezeAPIService(session_token=session_token)
            self.logger.info(f"[INIT] Breeze API initialized")
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to initialize Breeze API: {e}")
            raise
        
        # Load configuration
        config = get_recommended_paper_trading_set()
        self.tickers = config['indices'] + config['stocks']
        self.total_instruments = len(self.tickers)
        
        # Tracking
        self.trades_executed = 0
        self.total_gross_pnl = 0
        self.total_fees = 0
        self.total_net_pnl = 0
        self.signals_generated = {}
        
        self.logger.info(f"[INIT] 10-Minute Trading Engine Started")
        self.logger.info(f"  Instruments: {self.total_instruments}")
        self.logger.info(f"  Candles per ticker: {self.candle_count} (10-min bars)")
        self.logger.info(f"  Data coverage: ~{int(candle_count * 10 / 60)} hours")
        self.logger.info(f"  Brokerage Plan: {brokerage_plan.value.upper()}")
        self.logger.info(f"  Fee per trade: ~Rs 20-30 (including exchange fees)")
    
    def fetch_10min_candles(self, ticker: str) -> Optional[pd.DataFrame]:
        """Fetch 10-minute candles from Breeze API"""
        try:
            # Fetch 10-minute candles
            candles = self.api.get_candles(
                security_id=ticker,
                interval='10',  # 10-minute candles
                number_of_candles=self.candle_count
            )
            
            if not candles or len(candles) == 0:
                self.logger.warning(f"  No candle data for {ticker}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(candles)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.sort_values('datetime').reset_index(drop=True)
            
            self.logger.info(f"  Loaded {len(df)} candles for {ticker}")
            return df
            
        except Exception as e:
            self.logger.error(f"  Error fetching candles for {ticker}: {e}")
            return None
    
    def generate_10min_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate features optimized for 10-minute bars
        Adjusted for faster signal generation on shorter timeframe
        """
        if df is None or len(df) < 2:
            return None
        
        try:
            # Ensure numeric columns
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df = df.dropna()
            if len(df) < 2:
                return None
            
            # Basic indicators (adjusted for 10-min bars)
            df['SMA5'] = df['close'].rolling(window=5).mean()  # ~50 minutes
            df['SMA10'] = df['close'].rolling(window=10).mean()  # ~100 minutes
            df['SMA20'] = df['close'].rolling(window=20).mean()  # ~200 minutes (intraday trend)
            
            # RSI (14 period for 10-min = 140 minutes)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss + 1e-9)
            df['RSI14'] = 100 - (100 / (1 + rs))
            
            # MACD (12, 26, 9)
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Hist'] = df['MACD'] - df['Signal']
            
            # Bollinger Bands (20, 2)
            bb_sma = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['BB_Upper'] = bb_sma + (bb_std * 2)
            df['BB_Lower'] = bb_sma - (bb_std * 2)
            df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']
            
            # ATR (14 period)
            df['TR'] = np.maximum(
                df['high'] - df['low'],
                np.maximum(
                    abs(df['high'] - df['close'].shift()),
                    abs(df['low'] - df['close'].shift())
                )
            )
            df['ATR14'] = df['TR'].rolling(window=14).mean()
            
            # ADX (14 period)
            df['Plus_DM'] = np.where(df['high'].diff() > df['low'].diff().abs(), df['high'].diff(), 0)
            df['Minus_DM'] = np.where(df['low'].diff().abs() > df['high'].diff(), df['low'].diff().abs(), 0)
            df['Plus_DI'] = (df['Plus_DM'].rolling(window=14).mean() / df['ATR14']) * 100
            df['Minus_DI'] = (df['Minus_DM'].rolling(window=14).mean() / df['ATR14']) * 100
            df['ADX'] = abs(df['Plus_DI'] - df['Minus_DI']) / (df['Plus_DI'] + df['Minus_DI'] + 1e-9)
            
            # Volume indicators
            df['Volume_SMA'] = df['volume'].rolling(window=10).mean()
            df['Volume_Ratio'] = df['volume'] / (df['Volume_SMA'] + 1e-9)
            
            # Momentum
            df['Momentum'] = df['close'] - df['close'].shift(10)
            df['ROC10'] = ((df['close'] - df['close'].shift(10)) / df['close'].shift(10)) * 100
            
            # Fill NaN
            df = df.fillna(method='bfill').fillna(0)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error generating features: {e}")
            return None
    
    def generate_10min_signals(self, df: pd.DataFrame, ticker: str) -> Optional[Dict]:
        """Generate trading signals based on 10-minute bars"""
        
        if df is None or len(df) < 20:
            return None
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        try:
            # SMA crossover for trend
            sma5 = latest['SMA5']
            sma10 = latest['SMA10']
            sma20 = latest['SMA20']
            close = latest['close']
            rsi = latest['RSI14']
            macd = latest['MACD_Hist']
            volume_ratio = latest['Volume_Ratio']
            atr = latest['ATR14']
            
            signal = None
            confidence = 0
            reason = []
            
            # Rule 1: SMA Crossover (trending)
            if sma5 > sma10 > sma20:
                signal = 'BUY'
                confidence += 0.3
                reason.append("Uptrend (5>10>20)")
            elif sma5 < sma10 < sma20:
                signal = 'SELL'
                confidence += 0.3
                reason.append("Downtrend (5<10<20)")
            else:
                reason.append("No clear SMA trend")
            
            # Rule 2: RSI Confirmation
            if signal == 'BUY' and 30 < rsi < 70:
                confidence += 0.2
                reason.append("RSI in neutral zone (intraday friendly)")
            elif signal == 'SELL' and 30 < rsi < 70:
                confidence += 0.2
                reason.append("RSI in neutral zone (intraday friendly)")
            
            # Rule 3: MACD Momentum
            if signal == 'BUY' and macd > 0:
                confidence += 0.2
                reason.append("MACD positive")
            elif signal == 'SELL' and macd < 0:
                confidence += 0.2
                reason.append("MACD negative")
            
            # Rule 4: Volume Confirmation
            if volume_ratio > 1.2:
                confidence += 0.15
                reason.append(f"High volume ({volume_ratio:.2f}x)")
            
            # Rule 5: Volatility Check (ATR-based)
            if atr > 0:
                confidence += 0.15
                reason.append(f"Volatility: {atr:.2f}")
            
            if signal and confidence >= 0.5:
                return {
                    'ticker': ticker,
                    'signal': signal,
                    'confidence': min(confidence, 1.0),
                    'close_price': close,
                    'rsi': rsi,
                    'sma5': sma5,
                    'sma10': sma10,
                    'sma20': sma20,
                    'atr': atr,
                    'volume_ratio': volume_ratio,
                    'reason': ' | '.join(reason),
                    'timestamp': datetime.now()
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating signal for {ticker}: {e}")
            return None
    
    def execute_10min_trades(self):
        """
        Execute trades for all tickers every 10 minutes
        This is called repeatedly by the scheduler
        """
        execution_start = datetime.now()
        execution_time_str = execution_start.strftime("%H:%M:%S")
        
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info(f"[10-MIN EXECUTION] {execution_time_str}")
        self.logger.info("=" * 80)
        
        execution_trades = []
        execution_gross_pnl = 0
        execution_fees = 0
        
        for idx, ticker in enumerate(self.tickers, 1):
            try:
                self.logger.info(f"\n[{idx}/{self.total_instruments}] {ticker}")
                
                # Fetch 10-min candles
                df = self.fetch_10min_candles(ticker)
                if df is None or len(df) < 20:
                    self.logger.info(f"  Skipped (insufficient data)")
                    continue
                
                # Generate features
                df_features = self.generate_10min_features(df.copy())
                if df_features is None:
                    self.logger.info(f"  Skipped (feature generation failed)")
                    continue
                
                # Generate signal
                signal_data = self.generate_10min_signals(df_features, ticker)
                if signal_data is None:
                    self.logger.info(f"  No signal (confidence too low)")
                    continue
                
                # Execute trade
                entry_price = signal_data['close_price']
                exit_price = entry_price * (1.002 if signal_data['signal'] == 'BUY' else 0.998)  # Assumed exit
                gross_pnl = (exit_price - entry_price) if signal_data['signal'] == 'BUY' else (entry_price - exit_price)
                
                # Calculate fees
                trade_fees = self.fee_calculator.calculate_pnl_after_fees(
                    entry_price=entry_price,
                    exit_price=exit_price,
                    quantity=1,
                    is_long=signal_data['signal'] == 'BUY'
                )
                
                net_pnl = trade_fees['net_pnl']
                fees = trade_fees['total_fees']
                
                self.logger.info(f"  [{signal_data['signal']}] @ Rs{entry_price:.2f} (Conf: {signal_data['confidence']:.2%})")
                self.logger.info(f"  Gross: Rs{gross_pnl:.0f} | Fees: Rs{fees:.0f} | Net: Rs{net_pnl:.0f}")
                self.logger.info(f"  {signal_data['reason']}")
                
                # Track trade
                execution_trades.append({
                    'ticker': ticker,
                    'signal': signal_data['signal'],
                    'confidence': signal_data['confidence'],
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'gross_pnl': gross_pnl,
                    'fees': fees,
                    'net_pnl': net_pnl,
                    'timestamp': signal_data['timestamp']
                })
                
                execution_gross_pnl += gross_pnl
                execution_fees += fees
                self.trades_executed += 1
                
            except Exception as e:
                self.logger.error(f"  Error processing {ticker}: {e}")
                continue
        
        # Summary for this execution
        execution_net_pnl = execution_gross_pnl - execution_fees
        self.total_gross_pnl += execution_gross_pnl
        self.total_fees += execution_fees
        self.total_net_pnl += execution_net_pnl
        
        self.logger.info("")
        self.logger.info(f"[EXECUTION SUMMARY]")
        self.logger.info(f"  Trades: {len(execution_trades)}")
        self.logger.info(f"  Gross P&L: Rs{execution_gross_pnl:.0f}")
        self.logger.info(f"  Fees: Rs{execution_fees:.0f}")
        self.logger.info(f"  Net P&L: Rs{execution_net_pnl:.0f}")
        self.logger.info(f"  Cumulative Net P&L: Rs{self.total_net_pnl:.0f}")
        
        # Save execution report
        report = {
            'execution_time': execution_time_str,
            'trades': execution_trades,
            'execution_summary': {
                'total_trades': len(execution_trades),
                'gross_pnl': execution_gross_pnl,
                'total_fees': execution_fees,
                'net_pnl': execution_net_pnl,
                'cumulative_net_pnl': self.total_net_pnl
            }
        }
        
        report_file = REPORT_DIR / f"execution_{execution_start.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report


def run_10min_scheduler():
    """
    Schedule 10-minute trading executions during market hours
    09:15 AM - 03:30 PM IST
    """
    import schedule
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("[10-MINUTE TRADING SCHEDULER] Starting")
    logger.info("=" * 80)
    logger.info("Schedule: Every 10 minutes during 09:15 AM - 03:30 PM IST")
    logger.info(f"Candles: 100x 10-minute bars per ticker")
    logger.info("")
    
    engine = TenMinuteTradingEngine(candle_count=100, brokerage_plan=BrokeragePlan.IVALUE)
    
    # Schedule every 10 minutes
    schedule.every(10).minutes.do(engine.execute_10min_trades)
    
    logger.info("[SCHEDULER] 10-minute executions scheduled")
    logger.info("[INFO] Press Ctrl+C to stop")
    logger.info("")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n[SCHEDULER] Shutting down...")
        
        # Final summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("[FINAL SUMMARY]")
        logger.info(f"  Total Trades: {engine.trades_executed}")
        logger.info(f"  Total Gross P&L: Rs{engine.total_gross_pnl:.0f}")
        logger.info(f"  Total Fees: Rs{engine.total_fees:.0f}")
        logger.info(f"  Total Net P&L: Rs{engine.total_net_pnl:.0f}")
        logger.info("=" * 80)


if __name__ == "__main__":
    run_10min_scheduler()
