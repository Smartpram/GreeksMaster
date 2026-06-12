"""
Options Trading Engine
======================

Main trading engine for options strategies on NON-PINS NRO account

Strategies Implemented:
1. CALL_SPREAD - Buy ATM call, sell OTM call (bullish, limited risk)
2. PUT_SPREAD - Buy OTM put, sell ATM put (bearish, limited risk)
3. STRADDLE - Buy ATM call + put (high volatility play)
4. IRON_CONDOR - Sell call spread + put spread (neutral, income strategy)

Features:
- Signal generation based on technical analysis
- Options Greeks monitoring
- Risk management (delta, vega, theta limits)
- Position tracking
- Automated exit on Greeks thresholds
- Performance reporting
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np

from app.services.breeze_options_api import BreezOptionsAPIService
from app.options_strategy import OptionsTrader, OptionContract, GreeksData
from app.config import Config

logger = logging.getLogger(__name__)


@dataclass
class OptionsTradeSignal:
    """Signal for options trade"""
    timestamp: str
    symbol: str
    strategy: str                  # CALL_SPREAD, PUT_SPREAD, STRADDLE, IRON_CONDOR
    direction: str                 # BULLISH, BEARISH, NEUTRAL
    entry_strikes: Dict            # For spreads, legs
    premium: float
    confidence: float
    reason: str


class OptionsEngine:
    """Main options trading engine"""
    
    def __init__(self, capital: float = None, use_api: bool = False):
        """
        Initialize Options Engine
        
        Args:
            capital: Trading capital (defaults to Config.OPTIONS_CAPITAL)
            use_api: Use live Breeze API if True, else simulation mode
        """
        self.config = Config()
        self.capital = capital or self.config.OPTIONS_CAPITAL
        self.use_api = use_api
        
        # Initialize trader
        self.trader = OptionsTrader(
            capital=self.capital,
            max_position_size=self.config.MAX_OPTION_POSITION_SIZE
        )
        
        # Initialize API if needed
        self.api = None
        if use_api:
            self.api = BreezOptionsAPIService()
            auth_result = self.api.authenticate()
            if not auth_result.get('success'):
                logger.warning("⚠ API authentication failed, using simulation mode")
                self.api = None
        
        self.active_trades: List[Dict] = []
        self.closed_trades: List[Dict] = []
        self.pnl = 0.0
        
        logger.info(f"Options Engine initialized: Capital=₹{self.capital:,.0f}, API={'ON' if self.api else 'OFF'}")
    
    # ========================================================================
    # SIGNAL GENERATION
    # ========================================================================
    
    def generate_bull_call_spread_signal(self, symbol: str, spot_price: float,
                                        confidence: float, reason: str) -> Optional[OptionsTradeSignal]:
        """
        Generate bull call spread signal (bullish, limited risk)
        
        Buy ATM call, sell OTM call
        Max profit = difference in premiums
        Max loss = strike_width - premium_difference
        """
        if confidence < 0.60:
            return None
        
        # Select strikes based on confidence
        if confidence >= 0.80:
            strike_width = 100
        else:
            strike_width = 200  # Wider for lower confidence
        
        atm = self.trader.find_atm_strike(symbol, spot_price)
        long_strike = atm
        short_strike = atm + strike_width
        
        # Estimated premiums (would come from option chain in production)
        long_premium = spot_price * 0.015    # ATM premium ~1.5%
        short_premium = spot_price * 0.005   # OTM premium ~0.5%
        net_premium = long_premium - short_premium
        
        signal = OptionsTradeSignal(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            strategy='BULL_CALL_SPREAD',
            direction='BULLISH',
            entry_strikes={
                'long_call': long_strike,
                'short_call': short_strike
            },
            premium=net_premium,
            confidence=confidence,
            reason=reason
        )
        
        logger.info(f"✓ Generated BULL_CALL_SPREAD: {symbol} | Long ₹{long_strike} / Short ₹{short_strike}")
        return signal
    
    def generate_bear_put_spread_signal(self, symbol: str, spot_price: float,
                                       confidence: float, reason: str) -> Optional[OptionsTradeSignal]:
        """
        Generate bear put spread signal (bearish, limited risk)
        
        Sell ATM put, buy OTM put
        Max profit = difference in premiums
        Max loss = strike_width - premium_difference
        """
        if confidence < 0.60:
            return None
        
        if confidence >= 0.80:
            strike_width = 100
        else:
            strike_width = 200
        
        atm = self.trader.find_atm_strike(symbol, spot_price)
        short_strike = atm
        long_strike = atm - strike_width
        
        short_premium = spot_price * 0.015
        long_premium = spot_price * 0.005
        net_premium = short_premium - long_premium
        
        signal = OptionsTradeSignal(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            strategy='BEAR_PUT_SPREAD',
            direction='BEARISH',
            entry_strikes={
                'short_put': short_strike,
                'long_put': long_strike
            },
            premium=net_premium,
            confidence=confidence,
            reason=reason
        )
        
        logger.info(f"✓ Generated BEAR_PUT_SPREAD: {symbol} | Short ₹{short_strike} / Long ₹{long_strike}")
        return signal
    
    def generate_straddle_signal(self, symbol: str, spot_price: float,
                               market_volatility: float, reason: str) -> Optional[OptionsTradeSignal]:
        """
        Generate straddle signal (neutral, high volatility play)
        
        Buy ATM call + Buy ATM put
        Profit from large price movement in either direction
        """
        if market_volatility < 0.20:  # Only for high volatility
            return None
        
        strike = self.trader.find_atm_strike(symbol, spot_price)
        
        # Premiums scale with volatility
        call_premium = spot_price * 0.02 * min(market_volatility, 1.0)
        put_premium = spot_price * 0.02 * min(market_volatility, 1.0)
        total_premium = call_premium + put_premium
        
        signal = OptionsTradeSignal(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            strategy='STRADDLE',
            direction='NEUTRAL',
            entry_strikes={
                'strike': strike
            },
            premium=total_premium,
            confidence=market_volatility,
            reason=reason
        )
        
        logger.info(f"✓ Generated STRADDLE: {symbol} | Strike ₹{strike} | Vol {market_volatility:.0%}")
        return signal
    
    def generate_iron_condor_signal(self, symbol: str, spot_price: float,
                                   confidence: float, reason: str) -> Optional[OptionsTradeSignal]:
        """
        Generate iron condor signal (neutral, income strategy)
        
        Sell OTM call spread + Sell OTM put spread
        Max profit = premium collected
        Max loss = strike_width - premium
        """
        if confidence < 0.60:
            return None
        
        atm = self.trader.find_atm_strike(symbol, spot_price)
        
        # Upper spread (calls)
        call_short_strike = atm + 100
        call_long_strike = atm + 200
        
        # Lower spread (puts)
        put_short_strike = atm - 100
        put_long_strike = atm - 200
        
        # Estimated premiums
        call_short_premium = spot_price * 0.005
        call_long_premium = spot_price * 0.002
        put_short_premium = spot_price * 0.005
        put_long_premium = spot_price * 0.002
        
        total_credit = (call_short_premium - call_long_premium + 
                       put_short_premium - put_long_premium)
        
        signal = OptionsTradeSignal(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            strategy='IRON_CONDOR',
            direction='NEUTRAL',
            entry_strikes={
                'call_short': call_short_strike,
                'call_long': call_long_strike,
                'put_short': put_short_strike,
                'put_long': put_long_strike
            },
            premium=total_credit,
            confidence=confidence,
            reason=reason
        )
        
        logger.info(f"✓ Generated IRON_CONDOR: {symbol} | Call {call_short_strike}/{call_long_strike} | Put {put_short_strike}/{put_long_strike}")
        return signal
    
    # ========================================================================
    # EXECUTION
    # ========================================================================
    
    def execute_signal(self, signal: OptionsTradeSignal) -> Optional[Dict]:
        """Execute options trade signal"""
        try:
            trade_result = None
            
            if signal.strategy == 'BULL_CALL_SPREAD':
                # Buy call + Sell call
                long_call = self.trader.create_option_position(
                    symbol=signal.symbol,
                    strike=signal.entry_strikes['long_call'],
                    option_type='CALL',
                    expiry=self.trader.get_next_expiry(self.config.PREFERRED_EXPIRY),
                    premium=signal.premium * 0.60,  # Approximate split
                    quantity=1,
                    spot_price=signal.premium * 50
                )
                
                short_call = self.trader.create_option_position(
                    symbol=signal.symbol,
                    strike=signal.entry_strikes['short_call'],
                    option_type='CALL',
                    expiry=self.trader.get_next_expiry(self.config.PREFERRED_EXPIRY),
                    premium=signal.premium * 0.40,
                    quantity=1,
                    spot_price=signal.premium * 50
                )
                
                if long_call and short_call:
                    trade_result = {
                        'strategy': 'BULL_CALL_SPREAD',
                        'legs': [long_call.contract_name(), short_call.contract_name()],
                        'net_premium': signal.premium,
                        'status': 'EXECUTED'
                    }
            
            elif signal.strategy == 'BEAR_PUT_SPREAD':
                # Sell put + Buy put
                short_put = self.trader.create_option_position(
                    symbol=signal.symbol,
                    strike=signal.entry_strikes['short_put'],
                    option_type='PUT',
                    expiry=self.trader.get_next_expiry(self.config.PREFERRED_EXPIRY),
                    premium=signal.premium * 0.60,
                    quantity=1,
                    spot_price=signal.premium * 50
                )
                
                long_put = self.trader.create_option_position(
                    symbol=signal.symbol,
                    strike=signal.entry_strikes['long_put'],
                    option_type='PUT',
                    expiry=self.trader.get_next_expiry(self.config.PREFERRED_EXPIRY),
                    premium=signal.premium * 0.40,
                    quantity=1,
                    spot_price=signal.premium * 50
                )
                
                if short_put and long_put:
                    trade_result = {
                        'strategy': 'BEAR_PUT_SPREAD',
                        'legs': [short_put.contract_name(), long_put.contract_name()],
                        'net_premium': signal.premium,
                        'status': 'EXECUTED'
                    }
            
            elif signal.strategy == 'STRADDLE':
                # Buy call + Buy put
                call = self.trader.create_option_position(
                    symbol=signal.symbol,
                    strike=signal.entry_strikes['strike'],
                    option_type='CALL',
                    expiry=self.trader.get_next_expiry(self.config.PREFERRED_EXPIRY),
                    premium=signal.premium * 0.50,
                    quantity=1,
                    spot_price=signal.premium * 50
                )
                
                put = self.trader.create_option_position(
                    symbol=signal.symbol,
                    strike=signal.entry_strikes['strike'],
                    option_type='PUT',
                    expiry=self.trader.get_next_expiry(self.config.PREFERRED_EXPIRY),
                    premium=signal.premium * 0.50,
                    quantity=1,
                    spot_price=signal.premium * 50
                )
                
                if call and put:
                    trade_result = {
                        'strategy': 'STRADDLE',
                        'legs': [call.contract_name(), put.contract_name()],
                        'net_premium': signal.premium,
                        'status': 'EXECUTED'
                    }
            
            if trade_result:
                self.active_trades.append(trade_result)
                logger.info(f"✓ Executed {signal.strategy}: {signal.symbol}")
                return trade_result
            else:
                logger.warning(f"Failed to execute {signal.strategy}")
                return None
                
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            return None
    
    # ========================================================================
    # RISK MONITORING
    # ========================================================================
    
    def check_risk_limits(self) -> Dict:
        """Check if portfolio Greeks are within risk limits"""
        greeks = self.trader.calculate_greeks(self.trader.active_positions[0]) if self.trader.active_positions else GreeksData(0, 0, 0, 0, 0)
        
        # This is simplified - in production, aggregate Greeks from all positions
        portfolio_delta = sum(
            self.trader.calculate_greeks(pos).delta * pos.quantity
            for pos in self.trader.active_positions
        )
        
        portfolio_vega = sum(
            self.trader.calculate_greeks(pos).vega * pos.quantity
            for pos in self.trader.active_positions
        )
        
        portfolio_theta = sum(
            self.trader.calculate_greeks(pos).theta * pos.quantity * 100
            for pos in self.trader.active_positions
        )
        
        alerts = []
        
        if abs(portfolio_delta) > self.config.MAX_DELTA_EXPOSURE:
            alerts.append(f"⚠ Delta {portfolio_delta:.2f} exceeds limit {self.config.MAX_DELTA_EXPOSURE}")
        
        if abs(portfolio_vega) > self.config.MAX_VEGA_EXPOSURE:
            alerts.append(f"⚠ Vega {portfolio_vega:.2f} exceeds limit {self.config.MAX_VEGA_EXPOSURE}")
        
        if portfolio_theta < self.config.MAX_THETA_DECAY_PER_DAY:
            alerts.append(f"⚠ Theta {portfolio_theta:.0f} exceeds limit {self.config.MAX_THETA_DECAY_PER_DAY}")
        
        return {
            'portfolio_delta': portfolio_delta,
            'portfolio_vega': portfolio_vega,
            'portfolio_theta': portfolio_theta,
            'alerts': alerts,
            'status': 'OK' if not alerts else 'ALERT'
        }
    
    # ========================================================================
    # REPORTING
    # ========================================================================
    
    def print_portfolio_summary(self) -> None:
        """Print options portfolio summary"""
        summary = self.trader.get_portfolio_summary()
        risk_check = self.check_risk_limits()
        
        print("\n" + "="*70)
        print("OPTIONS PORTFOLIO SUMMARY")
        print("="*70)
        
        print(f"\nActive Positions: {summary['active_positions']}")
        print(f"Closed Trades: {summary['closed_trades']}")
        print(f"Realized P&L: ₹{summary['realized_pnl']:,.0f}")
        print(f"Premium at Risk: ₹{summary['total_premium_at_risk']:,.0f}")
        
        print(f"\nPortfolio Greeks:")
        print(f"  Delta: {risk_check['portfolio_delta']:.2f}")
        print(f"  Vega: {risk_check['portfolio_vega']:.2f}")
        print(f"  Theta: ₹{risk_check['portfolio_theta']:.0f}/day")
        
        if risk_check['alerts']:
            print(f"\n⚠ Risk Alerts:")
            for alert in risk_check['alerts']:
                print(f"  {alert}")
        
        print("\n" + "="*70)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Initialize engine
    engine = OptionsEngine(capital=500000, use_api=False)
    
    # Generate sample signal
    signal = engine.generate_bull_call_spread_signal(
        symbol='NIFTY',
        spot_price=22000,
        confidence=0.80,
        reason='Bullish RSI divergence + price above MA200'
    )
    
    if signal:
        engine.execute_signal(signal)
        engine.print_portfolio_summary()
