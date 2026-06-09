"""
Options Integration for Trading Engine
======================================

Integrates options strategies with the main trading pipeline
Supports simultaneous equity and options trading

Features:
- Options signal generation based on equity signals
- Combined equity + options portfolio management
- Risk aggregation across both assets
- Greeks-based risk monitoring
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from app.options_strategy import OptionsTrader, OptionContract

logger = logging.getLogger(__name__)


@dataclass
class OptionsSignal:
    """Options trading signal"""
    timestamp: str
    symbol: str                    # e.g., NIFTY
    signal_type: str               # 'CALL_BUY', 'CALL_SELL', 'PUT_BUY', 'PUT_SELL'
    strategy: str                  # 'ATM_CALL', 'OTM_SPREAD', 'STRADDLE', etc.
    strike: float
    expiry: str
    premium: float
    quantity: int
    confidence: float              # 0-1 confidence score
    reason: str                    # Why this signal


class OptionsIntegration:
    """Integrates options into main trading system"""
    
    def __init__(self, equity_trader=None, capital: float = 500000, 
                 max_options_capital_allocation: float = 0.3):
        """
        Initialize options integration
        
        Args:
            equity_trader: Reference to equity trading engine
            capital: Total trading capital
            max_options_capital_allocation: Max % of capital for options (default 30%)
        """
        self.equity_trader = equity_trader
        self.total_capital = capital
        self.max_options_capital_allocation = max_options_capital_allocation
        
        # Split capital
        equity_capital = capital * (1 - max_options_capital_allocation)
        options_capital = capital * max_options_capital_allocation
        
        self.options_trader = OptionsTrader(
            capital=options_capital,
            max_position_size=0.1
        )
        
        self.options_signals: List[OptionsSignal] = []
        self.options_trades: List[Dict] = []
        
        logger.info(f"Options Integration initialized:")
        logger.info(f"  Total Capital: ₹{capital:,.0f}")
        logger.info(f"  Equity Allocation: ₹{equity_capital:,.0f}")
        logger.info(f"  Options Allocation: ₹{options_capital:,.0f}")
    
    # ========================================================================
    # SIGNAL GENERATION
    # ========================================================================
    
    def generate_call_signal(self, symbol: str, spot_price: float,
                            equity_signal: str, confidence: float) -> Optional[OptionsSignal]:
        """
        Generate options call signal based on equity bullish signal
        
        Args:
            symbol: Underlying (NIFTY, BANKNIFTY, etc.)
            spot_price: Current spot price
            equity_signal: Equity trading signal (BUY, HOLD, SELL)
            confidence: Signal confidence (0-1)
            
        Returns:
            OptionsSignal or None
        """
        if equity_signal != 'BUY':
            return None
        
        if confidence < 0.60:
            logger.info(f"Call signal confidence {confidence:.2%} below threshold")
            return None
        
        # Strategy selection based on confidence
        if confidence >= 0.85:
            strategy = 'ATM_CALL'  # High confidence: buy ATM calls
            strike = self.options_trader.find_atm_strike(symbol, spot_price)
            premium = spot_price * 0.02  # Assume 2% premium
        elif confidence >= 0.70:
            strategy = 'CALL_SPREAD'  # Medium confidence: call spread
            strike = self.options_trader.find_atm_strike(symbol, spot_price) + 100
            premium = spot_price * 0.01  # Assume 1% net premium
        else:
            strategy = 'BUY_FAR_OTM'  # Lower confidence: buy far OTM calls
            strikes = self.options_trader.find_otm_strikes(symbol, spot_price, 'CALL', 2)
            strike = strikes[1] if len(strikes) > 1 else strikes[0]
            premium = spot_price * 0.005  # Assume 0.5% premium
        
        expiry = self.options_trader.get_next_expiry('weekly')
        
        signal = OptionsSignal(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            signal_type='CALL_BUY',
            strategy=strategy,
            strike=strike,
            expiry=expiry,
            premium=premium,
            quantity=1,
            confidence=confidence,
            reason=f"Bullish equity signal with {confidence:.0%} confidence"
        )
        
        logger.info(f"✓ Generated CALL signal: {symbol} {strategy} @₹{strike}")
        return signal
    
    def generate_put_signal(self, symbol: str, spot_price: float,
                           equity_signal: str, confidence: float) -> Optional[OptionsSignal]:
        """
        Generate options put signal based on equity bearish signal
        
        Args:
            symbol: Underlying
            spot_price: Current spot price
            equity_signal: Equity trading signal
            confidence: Signal confidence (0-1)
            
        Returns:
            OptionsSignal or None
        """
        if equity_signal != 'SELL':
            return None
        
        if confidence < 0.60:
            return None
        
        # Strategy selection based on confidence
        if confidence >= 0.85:
            strategy = 'ATM_PUT'
            strike = self.options_trader.find_atm_strike(symbol, spot_price)
            premium = spot_price * 0.02
        elif confidence >= 0.70:
            strategy = 'PUT_SPREAD'
            strike = self.options_trader.find_atm_strike(symbol, spot_price) - 100
            premium = spot_price * 0.01
        else:
            strategy = 'BUY_FAR_OTM'
            strikes = self.options_trader.find_otm_strikes(symbol, spot_price, 'PUT', 2)
            strike = strikes[1] if len(strikes) > 1 else strikes[0]
            premium = spot_price * 0.005
        
        expiry = self.options_trader.get_next_expiry('weekly')
        
        signal = OptionsSignal(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            signal_type='PUT_BUY',
            strategy=strategy,
            strike=strike,
            expiry=expiry,
            premium=premium,
            quantity=1,
            confidence=confidence,
            reason=f"Bearish equity signal with {confidence:.0%} confidence"
        )
        
        logger.info(f"✓ Generated PUT signal: {symbol} {strategy} @₹{strike}")
        return signal
    
    def generate_straddle_signal(self, symbol: str, spot_price: float,
                               market_volatility: float) -> Optional[OptionsSignal]:
        """
        Generate straddle signal when volatility is high
        
        Args:
            symbol: Underlying
            spot_price: Current spot price
            market_volatility: Expected market volatility (0-1)
            
        Returns:
            OptionsSignal or None
        """
        if market_volatility < 0.20:  # Only for high volatility
            return None
        
        strike = self.options_trader.find_atm_strike(symbol, spot_price)
        expiry = self.options_trader.get_next_expiry('weekly')
        
        # Premium increases with volatility
        call_premium = spot_price * 0.02 * market_volatility
        put_premium = spot_price * 0.02 * market_volatility
        
        signal = OptionsSignal(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            signal_type='STRADDLE',
            strategy='STRADDLE',
            strike=strike,
            expiry=expiry,
            premium=call_premium + put_premium,
            quantity=1,
            confidence=market_volatility,
            reason=f"High volatility ({market_volatility:.0%}) - straddle opportunity"
        )
        
        logger.info(f"✓ Generated STRADDLE signal: {symbol} @₹{strike}")
        return signal
    
    # ========================================================================
    # EXECUTION
    # ========================================================================
    
    def execute_options_signal(self, signal: OptionsSignal) -> Optional[Dict]:
        """
        Execute options signal
        
        Args:
            signal: OptionsSignal to execute
            
        Returns:
            Trade execution result or None
        """
        try:
            if signal.signal_type == 'CALL_BUY':
                contract = self.options_trader.create_option_position(
                    symbol=signal.symbol,
                    strike=signal.strike,
                    option_type='CALL',
                    expiry=signal.expiry,
                    premium=signal.premium,
                    quantity=signal.quantity,
                    spot_price=signal.premium * 50  # Approximation
                )
            elif signal.signal_type == 'PUT_BUY':
                contract = self.options_trader.create_option_position(
                    symbol=signal.symbol,
                    strike=signal.strike,
                    option_type='PUT',
                    expiry=signal.expiry,
                    premium=signal.premium,
                    quantity=signal.quantity,
                    spot_price=signal.premium * 50
                )
            else:
                logger.warning(f"Unknown signal type: {signal.signal_type}")
                return None
            
            if contract:
                trade = {
                    'timestamp': datetime.now().isoformat(),
                    'signal_id': signal.timestamp,
                    'contract': contract.contract_name(),
                    'premium': signal.premium,
                    'status': 'EXECUTED'
                }
                self.options_trades.append(trade)
                self.options_signals.append(signal)
                logger.info(f"✓ Executed options trade: {contract.contract_name()}")
                return trade
            else:
                logger.warning(f"Failed to execute signal: {signal.symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error executing options signal: {e}")
            return None
    
    # ========================================================================
    # RISK MANAGEMENT
    # ========================================================================
    
    def calculate_portfolio_greeks(self) -> Dict:
        """
        Calculate aggregate Greeks for all options positions
        
        Returns:
            Aggregated Greeks across all positions
        """
        total_delta = 0
        total_gamma = 0
        total_theta = 0
        total_vega = 0
        total_rho = 0
        
        for contract in self.options_trader.active_positions:
            greeks = self.options_trader.calculate_greeks(contract)
            total_delta += greeks.delta * contract.quantity
            total_gamma += greeks.gamma * contract.quantity
            total_theta += greeks.theta * contract.quantity * 100  # Theta per contract
            total_vega += greeks.vega * contract.quantity
            total_rho += greeks.rho * contract.quantity
        
        return {
            'delta': round(total_delta, 2),
            'gamma': round(total_gamma, 4),
            'theta': round(total_theta, 2),
            'vega': round(total_vega, 2),
            'rho': round(total_rho, 2),
            'num_positions': len(self.options_trader.active_positions)
        }
    
    def check_Greeks_limits(self, delta_limit: float = 0.5, vega_limit: float = 2.0) -> Dict:
        """
        Check if Greeks are within acceptable limits
        
        Args:
            delta_limit: Max delta exposure
            vega_limit: Max vega exposure
            
        Returns:
            Warnings if limits exceeded
        """
        greeks = self.calculate_portfolio_greeks()
        warnings = []
        
        if abs(greeks['delta']) > delta_limit:
            warnings.append(f"Delta exposure {greeks['delta']:.2f} exceeds limit {delta_limit}")
        
        if abs(greeks['vega']) > vega_limit:
            warnings.append(f"Vega exposure {greeks['vega']:.2f} exceeds limit {vega_limit}")
        
        if greeks['theta'] < -500:  # Daily theta decay
            warnings.append(f"Theta decay {greeks['theta']:.0f} is significant")
        
        for warning in warnings:
            logger.warning(f"⚠ {warning}")
        
        return {
            'Greeks': greeks,
            'warnings': warnings,
            'status': 'OK' if not warnings else 'ALERT'
        }
    
    def check_expiry_proximity(self) -> List[str]:
        """Check positions approaching expiry"""
        alerts = []
        for contract in self.options_trader.active_positions:
            dte = self.options_trader.days_to_expiry(contract.expiry)
            if dte <= 3:
                alert = f"⚠ {contract.contract_name()} expires in {dte} days"
                alerts.append(alert)
                logger.warning(alert)
        return alerts
    
    # ========================================================================
    # REPORTING
    # ========================================================================
    
    def get_options_portfolio_report(self) -> Dict:
        """Generate comprehensive options portfolio report"""
        summary = self.options_trader.get_portfolio_summary()
        greeks = self.calculate_portfolio_greeks()
        limits_check = self.check_Greeks_limits()
        expiry_alerts = self.check_expiry_proximity()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'portfolio': {
                'active_positions': summary['active_positions'],
                'closed_trades': summary['closed_trades'],
                'realized_pnl': summary['realized_pnl'],
                'premium_at_risk': summary['total_premium_at_risk']
            },
            'aggregated_greeks': greeks,
            'risk_check': limits_check,
            'expiry_alerts': expiry_alerts,
            'positions': summary['positions']
        }
        
        return report
    
    def print_options_summary(self) -> None:
        """Print human-readable options portfolio summary"""
        report = self.get_options_portfolio_report()
        
        print("\n" + "="*70)
        print("OPTIONS PORTFOLIO SUMMARY")
        print("="*70)
        
        portfolio = report['portfolio']
        print(f"\nActive Positions: {portfolio['active_positions']}")
        print(f"Closed Trades: {portfolio['closed_trades']}")
        print(f"Realized P&L: ₹{portfolio['realized_pnl']:,.0f}")
        print(f"Premium at Risk: ₹{portfolio['premium_at_risk']:,.0f}")
        
        print("\nAggregated Greeks:")
        greeks = report['aggregated_greeks']
        print(f"  Delta: {greeks['delta']:.2f} (directional exposure)")
        print(f"  Gamma: {greeks['gamma']:.4f} (delta acceleration)")
        print(f"  Theta: ₹{greeks['theta']:.0f}/day (time decay)")
        print(f"  Vega: {greeks['vega']:.2f} (volatility exposure)")
        
        if report['risk_check']['status'] == 'ALERT':
            print("\n⚠ Risk Alerts:")
            for warning in report['risk_check']['warnings']:
                print(f"  - {warning}")
        
        if report['expiry_alerts']:
            print("\n⏰ Expiry Alerts:")
            for alert in report['expiry_alerts']:
                print(f"  {alert}")
        
        print("\n" + "="*70)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize integration
    integration = OptionsIntegration(capital=500000)
    
    # Generate sample signals
    call_signal = integration.generate_call_signal(
        symbol='NIFTY',
        spot_price=22000,
        equity_signal='BUY',
        confidence=0.80
    )
    
    if call_signal:
        integration.execute_options_signal(call_signal)
    
    # Print summary
    integration.print_options_summary()
