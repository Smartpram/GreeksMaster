"""
ICICI Direct Brokerage Fee Calculator
Handles all fee calculations for realistic P&L tracking
"""

from enum import Enum
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class BrokeragePlan(Enum):
    """Available ICICI Direct brokerage plans"""
    IVALUE = "ivalue"          # ₹299 one-time, ₹20/trade
    PRIME_TIER1 = "prime_t1"   # ₹999/year, ₹49/trade
    PRIME_TIER2 = "prime_t2"   # ₹4999/year, ₹19/trade
    PRIME_TIER3 = "prime_t3"   # ₹9999/year, ₹9/trade


class BrokerageFeeCalculator:
    """Calculate all fees for trading: brokerage, STT, exchange charges, GST, etc."""
    
    # Plan details: (subscription_fee, per_trade_fee)
    PLAN_FEES = {
        BrokeragePlan.IVALUE: {
            "subscription_fee": 299,      # One-time
            "per_trade_fee": 20,
            "demat_amc": 300              # Annual AMC
        },
        BrokeragePlan.PRIME_TIER1: {
            "subscription_fee": 999,      # Annual
            "per_trade_fee": 49,
            "demat_amc": 550              # Estimated
        },
        BrokeragePlan.PRIME_TIER2: {
            "subscription_fee": 4999,     # Annual
            "per_trade_fee": 19,
            "demat_amc": 550              # Estimated
        },
        BrokeragePlan.PRIME_TIER3: {
            "subscription_fee": 9999,     # Annual
            "per_trade_fee": 9,
            "demat_amc": 550              # Estimated
        }
    }
    
    # Exchange transaction charges (on option premium)
    EXCHANGE_CHARGES = {
        "NSE": 0.03553 / 100,   # 0.03553%
        "BSE": 0.0325 / 100     # 0.0325%
    }
    
    # Other statutory charges
    SEBI_TURNOVER_CHARGE = 0.0001 / 100      # 0.0001% of turnover
    STT_RATE = 0.15 / 100                     # 0.15% (options sell side only)
    GST_RATE = 0.18                           # 18%
    
    def __init__(self, plan: BrokeragePlan = BrokeragePlan.IVALUE, exchange: str = "NSE"):
        """
        Initialize fee calculator
        
        Args:
            plan: Brokerage plan to use
            exchange: Exchange (NSE or BSE)
        """
        self.plan = plan
        self.exchange = exchange
        self.plan_details = self.PLAN_FEES[plan]
        self.logger = logging.getLogger(__name__)
    
    def calculate_single_trade_fee(self, entry_price: float, exit_price: float, 
                                   quantity: float, is_sell: bool = False) -> Dict:
        """
        Calculate all fees for a single trade
        
        Args:
            entry_price: Entry price per unit
            exit_price: Exit price per unit
            quantity: Quantity traded
            is_sell: Whether this is a sell transaction (for STT)
        
        Returns:
            Dict with breakdown of all fees
        """
        try:
            # Calculate trade values
            entry_value = entry_price * quantity
            exit_value = exit_price * quantity
            
            # 1. BROKERAGE FEE
            # Buy side: brokerage on entry
            # Sell side: brokerage on exit
            brokerage_fee = self.plan_details["per_trade_fee"]
            
            # 2. EXCHANGE TRANSACTION CHARGES
            # Applied to both buy and sell sides
            exchange_charge_buy = entry_value * self.EXCHANGE_CHARGES[self.exchange]
            exchange_charge_sell = exit_value * self.EXCHANGE_CHARGES[self.exchange]
            exchange_charge_total = exchange_charge_buy + exchange_charge_sell
            
            # 3. STT (Securities Transaction Tax)
            # Only on sell side for equities
            stt_charge = exit_value * self.STT_RATE if is_sell else 0
            
            # 4. SEBI TURNOVER CHARGES
            # On total turnover
            total_turnover = entry_value + exit_value
            sebi_charge = total_turnover * self.SEBI_TURNOVER_CHARGE
            
            # 5. STAMP DUTY (varies by state, assume 0.015% for Bombay)
            # Applied on buy side
            stamp_duty = entry_value * 0.00015  # ~0.015% average
            
            # 6. Subtotal before GST
            subtotal = brokerage_fee + exchange_charge_total + stt_charge + sebi_charge + stamp_duty
            
            # 7. GST (18% on brokerage + exchange charges + SEBI charges)
            gst_base = brokerage_fee + exchange_charge_total + sebi_charge
            gst_charge = gst_base * self.GST_RATE
            
            # Total fees
            total_fees = subtotal + gst_charge
            
            return {
                "brokerage": brokerage_fee,
                "exchange_charges": exchange_charge_total,
                "stt": stt_charge,
                "sebi_charge": sebi_charge,
                "stamp_duty": stamp_duty,
                "gst": gst_charge,
                "total": total_fees,
                "breakdown": {
                    "entry_value": entry_value,
                    "exit_value": exit_value,
                    "turnover": total_turnover
                }
            }
        
        except Exception as e:
            self.logger.error(f"[FEE ERROR] {str(e)}")
            return {"total": 0, "error": str(e)}
    
    def calculate_pnl_after_fees(self, entry_price: float, exit_price: float, 
                                 quantity: float) -> Dict:
        """
        Calculate profit/loss after all fees
        
        Args:
            entry_price: Entry price
            exit_price: Exit price
            quantity: Quantity
        
        Returns:
            Dict with gross P&L, fees, and net P&L
        """
        try:
            # Gross P&L (before fees)
            gross_pnl = (exit_price - entry_price) * quantity
            
            # Calculate all fees
            fees = self.calculate_single_trade_fee(entry_price, exit_price, quantity, is_sell=True)
            
            # Net P&L (after fees)
            net_pnl = gross_pnl - fees.get("total", 0)
            
            # Calculate percentage returns
            capital_invested = entry_price * quantity
            gross_pnl_pct = (gross_pnl / capital_invested * 100) if capital_invested > 0 else 0
            net_pnl_pct = (net_pnl / capital_invested * 100) if capital_invested > 0 else 0
            
            return {
                "entry_price": entry_price,
                "exit_price": exit_price,
                "quantity": quantity,
                "capital_invested": capital_invested,
                "gross_pnl": gross_pnl,
                "gross_pnl_pct": gross_pnl_pct,
                "total_fees": fees.get("total", 0),
                "net_pnl": net_pnl,
                "net_pnl_pct": net_pnl_pct,
                "fee_breakdown": fees,
                "breakeven_move_points": fees.get("total", 0) / quantity if quantity > 0 else 0
            }
        
        except Exception as e:
            self.logger.error(f"[P&L CALCULATION ERROR] {str(e)}")
            return {"error": str(e)}
    
    def get_plan_recommendation(self, expected_trades_per_year: int) -> Dict:
        """
        Recommend best brokerage plan based on expected trade frequency
        
        Args:
            expected_trades_per_year: Number of expected trades per year
        
        Returns:
            Dict with cost analysis for each plan
        """
        analysis = {}
        
        for plan in BrokeragePlan:
            details = self.PLAN_FEES[plan]
            
            # Calculate annual cost
            subscription_cost = details["subscription_fee"]
            # Multiply by 1 for one-time plans like iValue, or keep as is for annual
            if plan == BrokeragePlan.IVALUE:
                subscription_cost = details["subscription_fee"]  # One-time
            
            trading_cost = details["per_trade_fee"] * expected_trades_per_year
            demat_amc = details["demat_amc"]
            
            total_annual_cost = subscription_cost + trading_cost + demat_amc
            cost_per_trade = total_annual_cost / expected_trades_per_year if expected_trades_per_year > 0 else 0
            
            analysis[plan.value] = {
                "subscription_fee": subscription_cost,
                "per_trade_fee": details["per_trade_fee"],
                "demat_amc": demat_amc,
                "trades_per_year": expected_trades_per_year,
                "total_trading_cost": trading_cost,
                "total_annual_cost": total_annual_cost,
                "cost_per_trade": cost_per_trade
            }
        
        # Find best plan
        best_plan = min(analysis.items(), key=lambda x: x[1]["total_annual_cost"])
        
        return {
            "analysis": analysis,
            "recommended_plan": best_plan[0],
            "recommended_annual_cost": best_plan[1]["total_annual_cost"],
            "recommended_cost_per_trade": best_plan[1]["cost_per_trade"]
        }
    
    def get_breakeven_analysis(self, entry_price: float, quantity: float) -> Dict:
        """
        Calculate breakeven prices accounting for fees
        
        Args:
            entry_price: Entry price
            quantity: Quantity
        
        Returns:
            Dict with breakeven points for sell
        """
        try:
            capital_invested = entry_price * quantity
            
            # Approximate fees for one round trip (buy + sell)
            # Assuming fee of ~50-200 per side depending on plan
            fees = self.calculate_single_trade_fee(entry_price, entry_price, quantity, is_sell=True)
            total_fees = fees.get("total", 0)
            
            # Breakeven exit price (need to recover fees)
            breakeven_exit_price = entry_price + (total_fees / quantity)
            
            # Breakeven move in points
            breakeven_move = total_fees / quantity
            
            # Breakeven move in percentage
            breakeven_pct = (breakeven_move / entry_price) * 100
            
            return {
                "entry_price": entry_price,
                "quantity": quantity,
                "total_fees_estimated": total_fees,
                "breakeven_exit_price": breakeven_exit_price,
                "breakeven_move_points": breakeven_move,
                "breakeven_move_pct": breakeven_pct
            }
        
        except Exception as e:
            self.logger.error(f"[BREAKEVEN ANALYSIS ERROR] {str(e)}")
            return {"error": str(e)}


# Convenience function
def calculate_net_pnl(entry_price: float, exit_price: float, quantity: float,
                      plan: BrokeragePlan = BrokeragePlan.IVALUE) -> Dict:
    """
    Convenience function to calculate net P&L with fees
    
    Args:
        entry_price: Entry price
        exit_price: Exit price
        quantity: Quantity
        plan: Brokerage plan
    
    Returns:
        Dict with P&L analysis
    """
    calculator = BrokerageFeeCalculator(plan=plan)
    return calculator.calculate_pnl_after_fees(entry_price, exit_price, quantity)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create calculator (default: iValue plan)
    calc = BrokerageFeeCalculator(plan=BrokeragePlan.IVALUE)
    
    # Example trade: Buy NIFTY50 at 23731.52, Sell at 23750
    print("\n" + "="*80)
    print("NIFTY50 TRADE EXAMPLE")
    print("="*80)
    
    pnl_result = calc.calculate_pnl_after_fees(
        entry_price=23731.52,
        exit_price=23750.00,
        quantity=1
    )
    
    print(f"\nEntry Price: Rs{pnl_result['entry_price']:.2f}")
    print(f"Exit Price: Rs{pnl_result['exit_price']:.2f}")
    print(f"Quantity: {pnl_result['quantity']}")
    print(f"Capital Invested: Rs{pnl_result['capital_invested']:.2f}")
    print(f"\nGross P&L: Rs{pnl_result['gross_pnl']:.2f} ({pnl_result['gross_pnl_pct']:.3f}%)")
    print(f"Total Fees: Rs{pnl_result['total_fees']:.2f}")
    print(f"NET P&L: Rs{pnl_result['net_pnl']:.2f} ({pnl_result['net_pnl_pct']:.3f}%)")
    print(f"\nBreakeven move required: Rs{pnl_result['breakeven_move_points']:.2f} per unit")
    
    # Plan recommendation
    print("\n" + "="*80)
    print("PLAN RECOMMENDATION (100 trades/year)")
    print("="*80)
    
    recommendation = calc.get_plan_recommendation(expected_trades_per_year=100)
    print(f"\nRecommended Plan: {recommendation['recommended_plan'].upper()}")
    print(f"Annual Cost: Rs{recommendation['recommended_annual_cost']:.2f}")
    print(f"Cost per trade: Rs{recommendation['recommended_cost_per_trade']:.2f}")
    
    # Breakeven analysis
    print("\n" + "="*80)
    print("BREAKEVEN ANALYSIS")
    print("="*80)
    
    breakeven = calc.get_breakeven_analysis(entry_price=23731.52, quantity=1)
    print(f"\nEntry Price: Rs{breakeven['entry_price']:.2f}")
    print(f"Total Fees: Rs{breakeven['total_fees_estimated']:.2f}")
    print(f"Breakeven Exit Price: Rs{breakeven['breakeven_exit_price']:.2f}")
    print(f"Breakeven Move: {breakeven['breakeven_move_points']:.2f} points ({breakeven['breakeven_move_pct']:.3f}%)")
