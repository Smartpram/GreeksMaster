"""
Buy and Hold Trend-Following Positional Strategy
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from app.strategies.base_strategy import BaseStrategy
from app.utils.indicators import TechnicalIndicators
from app.config import Config

logger = logging.getLogger(__name__)

class BuyHoldTrendStrategy(BaseStrategy):
    """
    Buy and Hold Trend-Following Positional Strategy
    
    Entry Criteria:
    - Price above moving average (trend confirmation)
    - RSI not overbought
    - Volume confirmation
    
    Exit Criteria:
    - Stop loss hit
    - Target achieved
    - Trend reversal (price below MA for sustained period)
    """
    
    def __init__(self, order_manager, risk_manager, notification_service):
        super().__init__(order_manager, risk_manager, notification_service)
        self.config = Config()
        self.indicators = TechnicalIndicators()
        self.watchlist = []
        self.entry_conditions = {}
        self.exit_conditions = {}
        self.trend_period = self.config.TREND_PERIOD
        self.rsi_period = self.config.RSI_PERIOD
        self.positions = {}
        
    def set_watchlist(self, instruments: List[str]):
        """Set the watchlist of instruments to trade"""
        self.watchlist = instruments
        logger.info(f"Watchlist updated: {instruments}")
    
    def generate_signals(self, data: Dict) -> Dict:
        """
        Generate trading signals based on trend-following criteria
        
        Args:
            data: Dictionary containing OHLCV data for instruments
            
        Returns:
            Dictionary containing signals for each instrument
        """
        signals = {}
        
        try:
            for instrument in self.watchlist:
                if instrument not in data:
                    continue
                
                instrument_data = data[instrument]
                if len(instrument_data) < max(self.trend_period, self.rsi_period, 26):  # Need at least 26 for MACD
                    continue
                
                # Convert to DataFrame for easier processing
                df = pd.DataFrame(instrument_data)
                if df.empty:
                    continue
                
                # Calculate technical indicators
                df['ma'] = self.indicators.moving_average(df['close'], self.trend_period)
                df['rsi'] = self.indicators.rsi(df['close'], self.rsi_period)
                df['volume_ma'] = self.indicators.moving_average(df['volume'], 20)
                
                # Calculate MACD
                macd_data = self.indicators.macd(df['close'])
                df['macd'] = macd_data['macd']
                df['macd_signal'] = macd_data['signal']
                df['macd_histogram'] = macd_data['histogram']
                
                # Calculate Stochastic RSI
                stoch_rsi_data = self.indicators.stochastic_rsi(df['close'])
                df['stoch_rsi'] = stoch_rsi_data['stoch_rsi']
                df['stoch_rsi_k'] = stoch_rsi_data['k_percent']
                df['stoch_rsi_d'] = stoch_rsi_data['d_percent']
                
                # Get current values
                current_price = df['close'].iloc[-1]
                current_ma = df['ma'].iloc[-1]
                current_rsi = df['rsi'].iloc[-1]
                current_volume = df['volume'].iloc[-1]
                avg_volume = df['volume_ma'].iloc[-1]
                
                # Get current MACD values
                current_macd = df['macd'].iloc[-1] if not pd.isna(df['macd'].iloc[-1]) else 0
                current_macd_signal = df['macd_signal'].iloc[-1] if not pd.isna(df['macd_signal'].iloc[-1]) else 0
                current_macd_histogram = df['macd_histogram'].iloc[-1] if not pd.isna(df['macd_histogram'].iloc[-1]) else 0
                
                # Get current Stochastic RSI values
                current_stoch_rsi = df['stoch_rsi'].iloc[-1] if not pd.isna(df['stoch_rsi'].iloc[-1]) else 50
                current_stoch_rsi_k = df['stoch_rsi_k'].iloc[-1] if not pd.isna(df['stoch_rsi_k'].iloc[-1]) else 50
                current_stoch_rsi_d = df['stoch_rsi_d'].iloc[-1] if not pd.isna(df['stoch_rsi_d'].iloc[-1]) else 50
                
                # Check for entry signal
                entry_signal = self._check_entry_conditions(
                    instrument, current_price, current_ma, current_rsi, 
                    current_volume, avg_volume, df,
                    current_macd, current_macd_signal, current_macd_histogram,
                    current_stoch_rsi, current_stoch_rsi_k, current_stoch_rsi_d
                )
                
                # Check for exit signal
                exit_signal = self._check_exit_conditions(
                    instrument, current_price, current_ma, current_rsi, df,
                    current_macd, current_macd_signal, current_macd_histogram,
                    current_stoch_rsi, current_stoch_rsi_k, current_stoch_rsi_d
                )
                
                # Log technical analysis summary
                self._log_technical_analysis(instrument, current_price, current_ma, current_rsi,
                                           current_macd, current_macd_signal, current_macd_histogram,
                                           current_stoch_rsi_k, current_stoch_rsi_d, current_volume, avg_volume)
                
                # Generate signal
                if entry_signal:
                    signals[instrument] = {
                        'action': 'BUY',
                        'signal_strength': entry_signal['strength'],
                        'entry_price': current_price,
                        'stop_loss': self.risk_manager.calculate_stop_loss(current_price, 'BUY'),
                        'target': self.risk_manager.calculate_target(current_price, 'BUY'),
                        'timestamp': datetime.now(),
                        'conditions_met': entry_signal.get('conditions_met', []),
                        'indicators': {
                            'price': current_price,
                            'ma': current_ma,
                            'rsi': current_rsi,
                            'macd': current_macd,
                            'macd_signal': current_macd_signal,
                            'macd_histogram': current_macd_histogram,
                            'stoch_rsi_k': current_stoch_rsi_k,
                            'stoch_rsi_d': current_stoch_rsi_d,
                            'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1
                        }
                    }
                
                elif exit_signal:
                    signals[instrument] = {
                        'action': 'SELL',
                        'signal_strength': exit_signal['strength'],
                        'exit_price': current_price,
                        'reason': exit_signal['reason'],
                        'timestamp': datetime.now(),
                        'indicators': {
                            'price': current_price,
                            'ma': current_ma,
                            'rsi': current_rsi,
                            'macd': current_macd,
                            'macd_signal': current_macd_signal,
                            'macd_histogram': current_macd_histogram,
                            'stoch_rsi_k': current_stoch_rsi_k,
                            'stoch_rsi_d': current_stoch_rsi_d
                        }
                    }
        
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
        
        return signals
    
    def _check_entry_conditions(self, instrument: str, price: float, ma: float, 
                               rsi: float, volume: float, avg_volume: float, 
                               df: pd.DataFrame, macd: float, macd_signal: float, 
                               macd_histogram: float, stoch_rsi: float, 
                               stoch_rsi_k: float, stoch_rsi_d: float) -> Optional[Dict]:
        """Check if entry conditions are met with enhanced technical analysis"""
        try:
            # Skip if we already have a position
            if instrument in self.positions and self.positions[instrument]['quantity'] > 0:
                return None
            
            conditions_met = []
            
            # Primary Condition 1: Price above moving average (trend confirmation)
            if price > ma:
                conditions_met.append('trend_bullish')
            
            # Primary Condition 2: RSI in healthy range (not overbought but not oversold)
            if 30 < rsi < self.config.RSI_OVERBOUGHT:
                conditions_met.append('rsi_healthy')
            
            # Enhanced Condition 3: MACD trend confirmation
            if macd > macd_signal and macd_histogram > 0:
                conditions_met.append('macd_bullish')
            
            # Enhanced Condition 4: Stochastic RSI momentum confirmation
            # Look for %K above %D and both above 20 (exiting oversold territory)
            if stoch_rsi_k > 20 and stoch_rsi_d > 20 and stoch_rsi_k > stoch_rsi_d:
                conditions_met.append('stoch_rsi_bullish')
            
            # Supporting Condition 5: Volume confirmation (above average)
            if volume > avg_volume * 1.2:  # 20% above average
                conditions_met.append('volume_confirmation')
            
            # Supporting Condition 6: Recent price momentum (price higher than 5 days ago)
            if len(df) >= 5:
                price_5d_ago = df['close'].iloc[-6]
                if price > price_5d_ago * 1.02:  # 2% higher than 5 days ago
                    conditions_met.append('momentum_positive')
            
            # Supporting Condition 7: Not in overbought territory based on recent highs
            recent_high = df['high'].tail(10).max()
            if price < recent_high * 0.98:  # Not within 2% of recent high
                conditions_met.append('not_overbought_price')
            
            # Calculate signal strength with enhanced requirements
            primary_conditions = ['trend_bullish', 'rsi_healthy']
            enhanced_conditions = ['macd_bullish', 'stoch_rsi_bullish']
            supporting_conditions = ['volume_confirmation', 'momentum_positive', 'not_overbought_price']
            
            # Must have all primary conditions
            if not all(cond in conditions_met for cond in primary_conditions):
                return None
            
            # Must have at least 1 of 2 enhanced conditions for strong signal
            enhanced_met = sum(1 for cond in enhanced_conditions if cond in conditions_met)
            if enhanced_met == 0:
                return None
            
            # Calculate strength based on all conditions met
            supporting_met = sum(1 for cond in supporting_conditions if cond in conditions_met)
            
            # Base strength from primary + enhanced conditions
            base_strength = 0.6 + (enhanced_met / len(enhanced_conditions)) * 0.2
            
            # Bonus from supporting conditions
            support_bonus = (supporting_met / len(supporting_conditions)) * 0.2
            
            strength = min(1.0, base_strength + support_bonus)  # Cap at 1.0
            
            return {
                'strength': strength,
                'conditions_met': conditions_met
            }
        
        except Exception as e:
            logger.error(f"Error checking entry conditions for {instrument}: {e}")
            return None
    
    def _check_exit_conditions(self, instrument: str, price: float, ma: float, 
                              rsi: float, df: pd.DataFrame, macd: float, 
                              macd_signal: float, macd_histogram: float, 
                              stoch_rsi: float, stoch_rsi_k: float, stoch_rsi_d: float) -> Optional[Dict]:
        """Check if exit conditions are met"""
        try:
            # Skip if we don't have a position
            if instrument not in self.positions or self.positions[instrument]['quantity'] <= 0:
                return None
            
            position = self.positions[instrument]
            entry_price = position['avg_price']
            
            # Calculate current P&L
            current_pnl = (price - entry_price) / entry_price
            
            # Exit condition 1: Stop loss hit
            stop_loss = position.get('stop_loss', entry_price * 0.95)
            if price <= stop_loss:
                return {
                    'strength': 1.0,
                    'reason': 'stop_loss'
                }
            
            # Exit condition 2: Target achieved
            target = position.get('target', entry_price * 1.15)
            if price >= target:
                return {
                    'strength': 1.0,
                    'reason': 'target_achieved'
                }
            
            # Exit condition 3: Trend reversal (price below MA for sustained period)
            if price < ma:
                # Check if price has been below MA for multiple days
                below_ma_days = 0
                for i in range(1, min(6, len(df))):
                    if df['close'].iloc[-i] < df['ma'].iloc[-i]:
                        below_ma_days += 1
                    else:
                        break
                
                if below_ma_days >= 3:  # Below MA for 3+ days
                    return {
                        'strength': 0.8,
                        'reason': 'trend_reversal'
                    }
            
            # Exit condition 4: Enhanced technical reversal signals
            technical_exit_signals = 0
            exit_reasons = []
            
            # MACD bearish divergence
            if macd < macd_signal and macd_histogram < 0:
                technical_exit_signals += 1
                exit_reasons.append('macd_bearish')
            
            # Stochastic RSI overbought and turning down
            if stoch_rsi_k > 80 and stoch_rsi_d > 80 and stoch_rsi_k < stoch_rsi_d:
                technical_exit_signals += 1
                exit_reasons.append('stoch_rsi_overbought')
            
            # RSI overbought
            if rsi > self.config.RSI_OVERBOUGHT:
                technical_exit_signals += 1
                exit_reasons.append('rsi_overbought')
            
            # If multiple technical indicators suggest exit and we have profit
            if technical_exit_signals >= 2 and current_pnl > 0.05:  # 5% profit threshold
                return {
                    'strength': 0.7 + (technical_exit_signals * 0.1),
                    'reason': f"technical_exit_{'+'.join(exit_reasons)}"
                }
            
            # Exit condition 5: Strong RSI overbought with good profit
            if rsi > self.config.RSI_OVERBOUGHT and current_pnl > 0.10:  # 10% profit
                return {
                    'strength': 0.6,
                    'reason': 'rsi_overbought_with_profit'
                }
            
            # Exit condition 6: MACD bearish crossover with profit protection
            if macd < macd_signal and macd_histogram < -0.1 and current_pnl > 0.08:  # 8% profit
                return {
                    'strength': 0.5,
                    'reason': 'macd_bearish_crossover'
                }
            
            # Exit condition 7: Time-based exit (holding for too long)
            if 'entry_time' in position:
                days_held = (datetime.now() - position['entry_time']).days
                if days_held > 60:  # Holding for more than 60 days
                    return {
                        'strength': 0.4,
                        'reason': 'time_based_exit'
                    }
            
            return None
        
        except Exception as e:
            logger.error(f"Error checking exit conditions for {instrument}: {e}")
            return None
    
    def execute_strategy(self, signals: Dict) -> bool:
        """Execute strategy based on generated signals"""
        try:
            for instrument, signal in signals.items():
                action = signal['action']
                
                if action == 'BUY':
                    self._execute_buy_signal(instrument, signal)
                elif action == 'SELL':
                    self._execute_sell_signal(instrument, signal)
            
            return True
        
        except Exception as e:
            logger.error(f"Error executing strategy: {e}")
            return False
    
    def _execute_buy_signal(self, instrument: str, signal: Dict):
        """Execute buy signal"""
        try:
            entry_price = signal['entry_price']
            stop_loss = signal['stop_loss']
            target = signal['target']
            
            # Calculate position size based on risk management
            quantity = self.order_manager.calculate_position_size(
                capital=self.risk_manager.total_capital,
                risk_per_trade=0.02,  # 2% risk per trade
                entry_price=entry_price,
                stop_loss_price=stop_loss
            )
            
            if quantity <= 0:
                logger.warning(f"Invalid quantity calculated for {instrument}")
                return
            
            # Validate order with risk manager
            order_params = {
                'stock_code': instrument,
                'action': 'BUY',
                'quantity': quantity,
                'price': entry_price
            }
            
            is_valid, message = self.risk_manager.validate_order(order_params)
            if not is_valid:
                logger.warning(f"Order validation failed for {instrument}: {message}")
                return
            
            # Place market order
            result = self.order_manager.place_market_order(
                stock_code=instrument,
                action='BUY',
                quantity=quantity
            )
            
            if result.get('Success'):
                # Update position tracking
                self.positions[instrument] = {
                    'quantity': quantity,
                    'avg_price': entry_price,
                    'entry_time': datetime.now(),
                    'stop_loss': stop_loss,
                    'target': target,
                    'signal_strength': signal['signal_strength'],
                    'order_id': result.get('Result', {}).get('order_id')
                }
                
                # Update risk manager
                self.risk_manager.update_position(instrument, 'BUY', quantity, entry_price)
                
                # Send notification
                message = (f"BUY signal executed for {instrument}\\n"
                          f"Quantity: {quantity}\\n"
                          f"Price: ₹{entry_price:.2f}\\n"
                          f"Stop Loss: ₹{stop_loss:.2f}\\n"
                          f"Target: ₹{target:.2f}")
                
                if self.notification_service:
                    self.notification_service.send_notification(message, "TRADE")
                
                logger.info(f"BUY order executed for {instrument}: {quantity} @ ₹{entry_price}")
            
            else:
                logger.error(f"Failed to execute BUY order for {instrument}: {result}")
        
        except Exception as e:
            logger.error(f"Error executing buy signal for {instrument}: {e}")
    
    def _execute_sell_signal(self, instrument: str, signal: Dict):
        """Execute sell signal"""
        try:
            if instrument not in self.positions:
                return
            
            position = self.positions[instrument]
            quantity = position['quantity']
            
            if quantity <= 0:
                return
            
            exit_price = signal['exit_price']
            reason = signal.get('reason', 'signal_based')
            
            # Place market order to sell
            result = self.order_manager.place_market_order(
                stock_code=instrument,
                action='SELL',
                quantity=quantity
            )
            
            if result.get('Success'):
                # Calculate P&L
                entry_price = position['avg_price']
                pnl = (exit_price - entry_price) * quantity
                pnl_percentage = ((exit_price - entry_price) / entry_price) * 100
                
                # Update performance metrics
                self.update_performance_metrics(pnl)
                
                # Update risk manager
                self.risk_manager.update_position(instrument, 'SELL', quantity, exit_price)
                
                # Clear position
                self.positions[instrument] = {
                    'quantity': 0,
                    'avg_price': 0,
                    'entry_time': None,
                    'stop_loss': 0,
                    'target': 0
                }
                
                # Send notification
                message = (f"SELL signal executed for {instrument}\\n"
                          f"Quantity: {quantity}\\n"
                          f"Exit Price: ₹{exit_price:.2f}\\n"
                          f"P&L: ₹{pnl:.2f} ({pnl_percentage:.2f}%)\\n"
                          f"Reason: {reason}")
                
                if self.notification_service:
                    self.notification_service.send_notification(message, "TRADE")
                
                logger.info(f"SELL order executed for {instrument}: {quantity} @ ₹{exit_price} | P&L: ₹{pnl:.2f}")
            
            else:
                logger.error(f"Failed to execute SELL order for {instrument}: {result}")
        
        except Exception as e:
            logger.error(f"Error executing sell signal for {instrument}: {e}")
    
    def update_trailing_stops(self, market_data: Dict):
        """Update trailing stop losses for open positions"""
        try:
            for instrument, position in self.positions.items():
                if position['quantity'] <= 0:
                    continue
                
                if instrument in market_data:
                    current_price = market_data[instrument]['close']
                    
                    # Calculate new trailing stop
                    new_stop_loss = self.risk_manager.calculate_trailing_stop_loss(
                        current_price=current_price,
                        entry_price=position['avg_price'],
                        action='BUY'
                    )
                    
                    # Update if new stop loss is higher than current
                    if new_stop_loss > position['stop_loss']:
                        position['stop_loss'] = new_stop_loss
                        logger.info(f"Trailing stop updated for {instrument}: ₹{new_stop_loss:.2f}")
        
        except Exception as e:
            logger.error(f"Error updating trailing stops: {e}")
    
    def get_active_positions(self) -> Dict:
        """Get currently active positions"""
        active_positions = {}
        for instrument, position in self.positions.items():
            if position['quantity'] > 0:
                active_positions[instrument] = position
        return active_positions
    
    def get_strategy_status(self) -> Dict:
        """Get current strategy status"""
        active_positions = self.get_active_positions()
        
        return {
            'is_running': self.is_running,
            'watchlist_size': len(self.watchlist),
            'active_positions': len(active_positions),
            'total_capital_deployed': sum(
                pos['quantity'] * pos['avg_price'] 
                for pos in active_positions.values()
            ),
            'performance_metrics': self.get_performance_metrics(),
            'risk_metrics': self.risk_manager.get_portfolio_metrics()
        }
    
    def _log_technical_analysis(self, instrument: str, price: float, ma: float, rsi: float,
                               macd: float, macd_signal: float, macd_histogram: float,
                               stoch_rsi_k: float, stoch_rsi_d: float, volume: float, avg_volume: float):
        """Log comprehensive technical analysis for debugging and monitoring"""
        try:
            # Calculate technical indicator status
            trend_status = "BULLISH" if price > ma else "BEARISH"
            rsi_status = "OVERBOUGHT" if rsi > 70 else "OVERSOLD" if rsi < 30 else "NEUTRAL"
            macd_status = "BULLISH" if macd > macd_signal else "BEARISH"
            stoch_rsi_status = "OVERBOUGHT" if stoch_rsi_k > 80 and stoch_rsi_d > 80 else \
                              "OVERSOLD" if stoch_rsi_k < 20 and stoch_rsi_d < 20 else "NEUTRAL"
            volume_status = "HIGH" if volume > avg_volume * 1.2 else "NORMAL"
            
            # Log detailed analysis
            logger.info(f"""
Technical Analysis for {instrument}:
  Price: ₹{price:.2f} | MA({self.trend_period}): ₹{ma:.2f} | Trend: {trend_status}
  RSI({self.rsi_period}): {rsi:.2f} | Status: {rsi_status}
  MACD: {macd:.4f} | Signal: {macd_signal:.4f} | Histogram: {macd_histogram:.4f} | Status: {macd_status}
  Stoch RSI: K%={stoch_rsi_k:.2f} | D%={stoch_rsi_d:.2f} | Status: {stoch_rsi_status}
  Volume: {volume:,.0f} | Avg: {avg_volume:,.0f} | Status: {volume_status}
            """)
            
        except Exception as e:
            logger.error(f"Error logging technical analysis for {instrument}: {e}")