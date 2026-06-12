"""
Options Trading Strategy Module for NON-PINS NRO Account
=========================================================

Supports:
- Call/Put options trading
- Strike selection logic
- Expiry management
- Options Greeks calculation (Delta, Gamma, Theta, Vega)
- Risk management for options

Usage:
    from app.options_strategy import OptionsTrader
    
    trader = OptionsTrader(capital=100000, max_position_size=0.1)
    
    # Find ATM call option
    call_signal = trader.find_atm_call('NIFTY', entry_price=22000)
    
    # Calculate Greeks
    greeks = trader.calculate_greeks(call_signal)
    
    # Manage position
    trader.manage_option_position(call_signal)
"""

import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy.stats import norm

logger = logging.getLogger(__name__)


@dataclass
class OptionContract:
    """Represents an options contract"""
    symbol: str          # e.g., 'NIFTY', 'BANKNIFTY'
    strike: float        # Strike price
    expiry: str          # Expiry date (YYYY-MM-DD)
    option_type: str     # 'CALL' or 'PUT'
    exchange: str        # 'NFO' (National Futures and Options Exchange)
    spot_price: float    # Current spot price
    premium: float       # Option premium (price)
    quantity: int        # Quantity to trade
    entry_price: float   # Entry price for trade tracking
    entry_time: str      # Entry time
    
    def contract_name(self) -> str:
        """Generate standard contract name format"""
        expiry_str = self.expiry.replace('-', '')
        return f"{self.symbol}{expiry_str}{self.strike}{self.option_type[0]}"


@dataclass
class GreeksData:
    """Options Greeks for risk management"""
    delta: float         # Price sensitivity
    gamma: float         # Delta change rate
    theta: float         # Time decay per day
    vega: float          # Volatility sensitivity
    rho: float           # Interest rate sensitivity


class OptionsTrader:
    """Handles options trading logic and risk management"""
    
    # Standard strike intervals by underlying
    STRIKE_INTERVALS = {
        'NIFTY': 100,      # ₹100 intervals
        'BANKNIFTY': 100,  # ₹100 intervals
        'FINNIFTY': 50,    # ₹50 intervals
        'MIDCPNIFTY': 25,  # ₹25 intervals
    }
    
    # Standard expiries (weekly & monthly)
    EXPIRY_SCHEDULE = {
        'weekly': [1, 2, 3, 4],      # 4 weeklies
        'monthly': [1],              # 1 monthly
    }
    
    def __init__(self, capital: float = 100000, max_position_size: float = 0.1):
        """
        Initialize options trader
        
        Args:
            capital: Trading capital
            max_position_size: Maximum position size as % of capital
        """
        self.capital = capital
        self.max_position_size = max_position_size
        self.active_positions: List[OptionContract] = []
        self.closed_trades: List[Dict] = []
        self.pnl = 0.0
        
        logger.info(f"Options Trader initialized: Capital=₹{capital:,.0f}, Max Position={max_position_size*100:.1f}%")
    
    # ========================================================================
    # STRIKE SELECTION
    # ========================================================================
    
    def find_atm_strike(self, symbol: str, spot_price: float) -> float:
        """
        Find At-The-Money (ATM) strike for given spot price
        
        Args:
            symbol: Underlying symbol (NIFTY, BANKNIFTY, etc.)
            spot_price: Current spot price
            
        Returns:
            ATM strike price
        """
        interval = self.STRIKE_INTERVALS.get(symbol, 100)
        atm_strike = round(spot_price / interval) * interval
        return atm_strike
    
    def find_itm_strikes(self, symbol: str, spot_price: float, 
                        option_type: str = 'CALL', num_strikes: int = 2) -> List[float]:
        """
        Find In-The-Money (ITM) strikes
        
        Args:
            symbol: Underlying symbol
            spot_price: Current spot price
            option_type: 'CALL' or 'PUT'
            num_strikes: Number of ITM strikes to return
            
        Returns:
            List of ITM strike prices
        """
        interval = self.STRIKE_INTERVALS.get(symbol, 100)
        atm = self.find_atm_strike(symbol, spot_price)
        
        itm_strikes = []
        for i in range(1, num_strikes + 1):
            if option_type == 'CALL':
                # For calls, ITM = below spot
                strike = atm - (i * interval)
            else:
                # For puts, ITM = above spot
                strike = atm + (i * interval)
            itm_strikes.append(strike)
        
        return itm_strikes
    
    def find_otm_strikes(self, symbol: str, spot_price: float, 
                        option_type: str = 'CALL', num_strikes: int = 2) -> List[float]:
        """
        Find Out-Of-The-Money (OTM) strikes
        
        Args:
            symbol: Underlying symbol
            spot_price: Current spot price
            option_type: 'CALL' or 'PUT'
            num_strikes: Number of OTM strikes to return
            
        Returns:
            List of OTM strike prices
        """
        interval = self.STRIKE_INTERVALS.get(symbol, 100)
        atm = self.find_atm_strike(symbol, spot_price)
        
        otm_strikes = []
        for i in range(1, num_strikes + 1):
            if option_type == 'CALL':
                # For calls, OTM = above spot
                strike = atm + (i * interval)
            else:
                # For puts, OTM = below spot
                strike = atm - (i * interval)
            otm_strikes.append(strike)
        
        return otm_strikes
    
    # ========================================================================
    # EXPIRY MANAGEMENT
    # ========================================================================
    
    def get_next_expiry(self, expiry_type: str = 'weekly') -> str:
        """
        Get next available expiry date
        
        Args:
            expiry_type: 'weekly' or 'monthly'
            
        Returns:
            Expiry date as YYYY-MM-DD
            
        Note:
            NSE options expiry is every Wednesday (weekly) and last Thursday (monthly)
        """
        today = datetime.now()
        
        if expiry_type == 'weekly':
            # Next Wednesday
            days_ahead = 2 - today.weekday()  # 2 = Wednesday
            if days_ahead <= 0:
                days_ahead += 7
            expiry_date = today + timedelta(days=days_ahead)
        else:  # monthly
            # Last Thursday of current month
            if today.month == 12:
                last_day = datetime(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = datetime(today.year, today.month + 1, 1) - timedelta(days=1)
            
            # Find last Thursday
            while last_day.weekday() != 3:  # 3 = Thursday
                last_day -= timedelta(days=1)
            
            expiry_date = last_day
        
        return expiry_date.strftime('%Y-%m-%d')
    
    def days_to_expiry(self, expiry_date: str) -> int:
        """Calculate days remaining to expiry"""
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
        today = datetime.now()
        return max(0, (expiry - today).days)
    
    # ========================================================================
    # GREEKS CALCULATION (Black-Scholes)
    # ========================================================================
    
    def calculate_greeks(self, option_contract: OptionContract, 
                        volatility: float = 0.20, risk_free_rate: float = 0.06) -> GreeksData:
        """
        Calculate options Greeks using Black-Scholes model
        
        Args:
            option_contract: OptionContract object
            volatility: Historical volatility (annualized)
            risk_free_rate: Risk-free interest rate
            
        Returns:
            GreeksData with Delta, Gamma, Theta, Vega, Rho
        """
        S = option_contract.spot_price      # Spot price
        K = option_contract.strike          # Strike price
        T = self.days_to_expiry(option_contract.expiry) / 365  # Time to expiry
        r = risk_free_rate                  # Risk-free rate
        sigma = volatility                  # Volatility
        
        # Avoid division by zero for expired options
        if T <= 0:
            logger.warning(f"Option {option_contract.contract_name()} has expired")
            return GreeksData(0, 0, 0, 0, 0)
        
        # Calculate d1 and d2
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Calculate Greeks based on option type
        if option_contract.option_type == 'CALL':
            # Call Greeks
            delta = norm.cdf(d1)
            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
            theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) - 
                    r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
            vega = S * norm.pdf(d1) * np.sqrt(T) / 100  # Per 1% change in volatility
            rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100  # Per 1% change in rate
        else:
            # Put Greeks
            delta = norm.cdf(d1) - 1
            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
            theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) + 
                    r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365
            vega = S * norm.pdf(d1) * np.sqrt(T) / 100
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
        
        return GreeksData(
            delta=round(delta, 4),
            gamma=round(gamma, 6),
            theta=round(theta, 4),
            vega=round(vega, 4),
            rho=round(rho, 4)
        )
    
    # ========================================================================
    # POSITION MANAGEMENT
    # ========================================================================
    
    def create_option_position(self, symbol: str, strike: float, 
                              option_type: str, expiry: str, 
                              premium: float, quantity: int,
                              spot_price: float) -> Optional[OptionContract]:
        """
        Create a new options position
        
        Args:
            symbol: Underlying symbol
            strike: Strike price
            option_type: 'CALL' or 'PUT'
            expiry: Expiry date (YYYY-MM-DD)
            premium: Premium paid/received
            quantity: Number of contracts (1 contract = 100 shares)
            spot_price: Current spot price
            
        Returns:
            OptionContract if successful, None if risk limit exceeded
        """
        # Risk management: Check position size
        required_capital = premium * quantity * 100  # Premium per share
        if required_capital > self.capital * self.max_position_size:
            logger.warning(f"Position size {required_capital:,.0f} exceeds limit")
            return None
        
        contract = OptionContract(
            symbol=symbol,
            strike=strike,
            expiry=expiry,
            option_type=option_type,
            exchange='NFO',
            spot_price=spot_price,
            premium=premium,
            quantity=quantity,
            entry_price=premium,
            entry_time=datetime.now().isoformat()
        )
        
        self.active_positions.append(contract)
        logger.info(f"✓ Created {option_type} position: {contract.contract_name()} @₹{premium}")
        
        return contract
    
    def close_position(self, contract: OptionContract, exit_price: float) -> Dict:
        """
        Close an options position
        
        Args:
            contract: OptionContract to close
            exit_price: Exit premium
            
        Returns:
            Trade result dictionary with P&L
        """
        if contract not in self.active_positions:
            logger.error(f"Position {contract.contract_name()} not found")
            return {}
        
        # Calculate P&L (per contract)
        if contract.option_type == 'CALL':
            pnl_per_contract = (exit_price - contract.entry_price) * 100
        else:
            pnl_per_contract = (contract.entry_price - exit_price) * 100
        
        total_pnl = pnl_per_contract * contract.quantity
        
        trade_result = {
            'contract': contract.contract_name(),
            'entry_price': contract.entry_price,
            'exit_price': exit_price,
            'quantity': contract.quantity,
            'pnl_per_contract': pnl_per_contract,
            'total_pnl': total_pnl,
            'exit_time': datetime.now().isoformat()
        }
        
        self.active_positions.remove(contract)
        self.closed_trades.append(trade_result)
        self.pnl += total_pnl
        
        logger.info(f"✓ Closed position: {contract.contract_name()} | P&L: ₹{total_pnl:,.0f}")
        
        return trade_result
    
    def manage_theta_decay(self) -> None:
        """Monitor and manage positions affected by time decay (theta)"""
        for contract in self.active_positions:
            dte = self.days_to_expiry(contract.expiry)
            
            # Alert if approaching expiry
            if dte <= 3:
                logger.warning(f"⚠ {contract.contract_name()} expires in {dte} days - consider closing")
            
            # Calculate theta impact
            greeks = self.calculate_greeks(contract)
            if dte > 0:
                daily_theta_loss = greeks.theta * contract.quantity * 100
                logger.info(f"  {contract.contract_name()}: Daily theta decay ≈ ₹{daily_theta_loss:.0f}")
    
    # ========================================================================
    # STRATEGY BUILDERS
    # ========================================================================
    
    def build_call_spread(self, symbol: str, spot_price: float, 
                         premium_received: float, premium_paid: float,
                         strike_width: float = 100) -> Dict[str, OptionContract]:
        """
        Build a call spread (long call + short call)
        Max profit = strike_width - (premium_paid - premium_received)
        Max loss = premium_paid - premium_received
        
        Args:
            symbol: Underlying symbol
            spot_price: Current spot price
            premium_received: Premium received from short call
            premium_paid: Premium paid for long call
            strike_width: Difference between strikes
            
        Returns:
            Dictionary with 'long_call' and 'short_call' contracts
        """
        expiry = self.get_next_expiry('weekly')
        atm = self.find_atm_strike(symbol, spot_price)
        
        short_strike = atm + 100  # Sell near OTM
        long_strike = short_strike + strike_width  # Buy further OTM
        
        short_call = self.create_option_position(
            symbol=symbol,
            strike=short_strike,
            option_type='CALL',
            expiry=expiry,
            premium=premium_received,
            quantity=1,
            spot_price=spot_price
        )
        
        long_call = self.create_option_position(
            symbol=symbol,
            strike=long_strike,
            option_type='CALL',
            expiry=expiry,
            premium=premium_paid,
            quantity=1,
            spot_price=spot_price
        )
        
        logger.info(f"✓ Call spread created: Short ₹{short_strike} / Long ₹{long_strike}")
        
        return {
            'short_call': short_call,
            'long_call': long_call
        }
    
    def build_put_spread(self, symbol: str, spot_price: float,
                        premium_received: float, premium_paid: float,
                        strike_width: float = 100) -> Dict[str, OptionContract]:
        """
        Build a put spread (long put + short put)
        Max profit = premium_received - premium_paid
        Max loss = strike_width - (premium_received - premium_paid)
        """
        expiry = self.get_next_expiry('weekly')
        atm = self.find_atm_strike(symbol, spot_price)
        
        short_strike = atm - 100  # Sell near OTM
        long_strike = short_strike - strike_width  # Buy further OTM
        
        short_put = self.create_option_position(
            symbol=symbol,
            strike=short_strike,
            option_type='PUT',
            expiry=expiry,
            premium=premium_received,
            quantity=1,
            spot_price=spot_price
        )
        
        long_put = self.create_option_position(
            symbol=symbol,
            strike=long_strike,
            option_type='PUT',
            expiry=expiry,
            premium=premium_paid,
            quantity=1,
            spot_price=spot_price
        )
        
        logger.info(f"✓ Put spread created: Short ₹{short_strike} / Long ₹{long_strike}")
        
        return {
            'short_put': short_put,
            'long_put': long_put
        }
    
    def build_straddle(self, symbol: str, spot_price: float,
                      call_premium: float, put_premium: float) -> Dict[str, OptionContract]:
        """
        Build a straddle (long call + long put at same strike)
        Profit from high volatility in either direction
        Max loss = call_premium + put_premium
        """
        expiry = self.get_next_expiry('weekly')
        strike = self.find_atm_strike(symbol, spot_price)
        
        call = self.create_option_position(
            symbol=symbol,
            strike=strike,
            option_type='CALL',
            expiry=expiry,
            premium=call_premium,
            quantity=1,
            spot_price=spot_price
        )
        
        put = self.create_option_position(
            symbol=symbol,
            strike=strike,
            option_type='PUT',
            expiry=expiry,
            premium=put_premium,
            quantity=1,
            spot_price=spot_price
        )
        
        logger.info(f"✓ Straddle created at strike ₹{strike}")
        
        return {
            'call': call,
            'put': put
        }
    
    # ========================================================================
    # REPORTING
    # ========================================================================
    
    def get_portfolio_summary(self) -> Dict:
        """Get summary of options portfolio"""
        total_premium = sum(c.premium * c.quantity * 100 for c in self.active_positions)
        
        summary = {
            'active_positions': len(self.active_positions),
            'closed_trades': len(self.closed_trades),
            'total_premium_at_risk': total_premium,
            'realized_pnl': self.pnl,
            'positions': [
                {
                    'contract': c.contract_name(),
                    'type': c.option_type,
                    'strike': c.strike,
                    'expiry': c.expiry,
                    'premium': c.premium,
                    'quantity': c.quantity,
                    'greeks': self.calculate_greeks(c).__dict__
                }
                for c in self.active_positions
            ]
        }
        
        return summary


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Initialize trader
    trader = OptionsTrader(capital=500000, max_position_size=0.1)
    
    # Example: Create a call spread on NIFTY
    spot = 22000
    spreads = trader.build_call_spread(
        symbol='NIFTY',
        spot_price=spot,
        premium_received=150,
        premium_paid=100,
        strike_width=100
    )
    
    # Calculate Greeks
    for name, contract in spreads.items():
        if contract:
            greeks = trader.calculate_greeks(contract)
            print(f"\n{contract.contract_name()} Greeks:")
            print(f"  Delta: {greeks.delta}")
            print(f"  Gamma: {greeks.gamma}")
            print(f"  Theta: {greeks.theta}")
            print(f"  Vega: {greeks.vega}")
    
    # Get portfolio summary
    print("\nPortfolio Summary:")
    summary = trader.get_portfolio_summary()
    print(f"Active Positions: {summary['active_positions']}")
    print(f"Premium at Risk: ₹{summary['total_premium_at_risk']:,.0f}")
    
    # Manage theta decay
    trader.manage_theta_decay()
