"""
Options Screeners Demo & Integration
=====================================

Demonstrates all 6 options screeners with example usage
"""

import logging
from datetime import datetime
from app.options_screener import (
    OptionsScreener,
    ScreenerType,
    IVScreenerResult,
    EarningsScreenerResult,
    ThetaDecayScreenerResult,
    GreeksTechnicalResult,
    HedgingPairResult,
    DeltaNeutralResult
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptionsScreenersDemo:
    """Demo and integration class for all screeners"""
    
    def __init__(self, api_service=None):
        """Initialize screeners"""
        self.screener = OptionsScreener(api_service=api_service)
        self.results_cache = {}
    
    # =========================================================================
    # SCREENER DEMONSTRATIONS
    # =========================================================================
    
    def demo_iv_screener(self):
        """Demonstrate IV Screener"""
        print("\n" + "="*120)
        print("DEMO 1: IMPLIED VOLATILITY SCREENER".center(120))
        print("="*120)
        print("\nFinding stocks with high implied volatility (IV percentile > 75%)")
        print("→ Best for: SELLING premium strategies (bull spreads, iron condors)\n")
        
        # Screen for high IV
        results = self.screener.screen_high_iv(iv_percentile_min=75, limit=15)
        
        if results:
            print(f"Found {len(results)} high-IV opportunities:\n")
            for i, result in enumerate(results[:5], 1):
                print(f"{i}. {result.symbol}")
                print(f"   Current Price: ₹{result.current_price:.2f}")
                print(f"   IV Percentile: {result.iv_percentile:.1f}% (Current IV: {result.current_iv:.2f}%)")
                print(f"   IV Range (52W): {result.iv_52_week_low:.2f}% - {result.iv_52_week_high:.2f}%")
                print(f"   Expected Move: ₹{result.expected_move:.2f} ({result.expected_move_pct:.2f}%)")
                print(f"   Premium Skew: {result.premium_skew} → {result.recommendation}")
                print(f"   Opportunity Score: {result.score:.1f}/100\n")
        
        self.results_cache['iv_screener'] = results
        return results
    
    def demo_earnings_screener(self):
        """Demonstrate Earnings Screener"""
        print("\n" + "="*120)
        print("DEMO 2: EARNINGS PLAY SCREENER".center(120))
        print("="*120)
        print("\nFinding stocks with upcoming earnings and volatility opportunities")
        print("→ Best for: Straddle/strangle entry before earnings\n")
        
        # Screen for earnings plays
        results = self.screener.screen_earnings_plays(days_to_earnings=14, limit=15)
        
        if results:
            print(f"Found {len(results)} earnings play opportunities:\n")
            for i, result in enumerate(results[:5], 1):
                print(f"{i}. {result.symbol}")
                print(f"   Current Price: ₹{result.current_price:.2f}")
                print(f"   Earnings in: {result.days_to_earnings} days")
                print(f"   Historical Earnings Move: ₹{result.historical_move:.2f} ({result.historical_move_pct:.2f}%)")
                print(f"   Current IV: {result.current_iv:.2f}% → Expected at Earnings: {result.expected_iv_at_earnings:.2f}%")
                print(f"   Expected Move: ₹{result.expected_move:.2f} ({result.expected_move_pct:.2f}%)")
                print(f"   Strategy: {result.suggested_strategy} | Entry Premium: ₹{result.entry_premium:.2f}")
                print(f"   IV Crush Probability: {result.iv_crush_probability*100:.0f}%")
                print(f"   Opportunity Score: {result.score:.1f}/100\n")
        
        self.results_cache['earnings_screener'] = results
        return results
    
    def demo_theta_screener(self):
        """Demonstrate Theta Decay Screener"""
        print("\n" + "="*120)
        print("DEMO 3: THETA DECAY SCREENER".center(120))
        print("="*120)
        print("\nFinding best theta decay opportunities (3-8 days to expiry)")
        print("→ Best for: Pure theta decay plays (Iron Condors, Credit Spreads)\n")
        
        # Screen for theta decay
        results = self.screener.screen_theta_decay(
            dte_range=(3, 8),
            theta_min=-0.5,
            limit=20
        )
        
        if results:
            print(f"Found {len(results)} theta decay opportunities:\n")
            for i, result in enumerate(results[:10], 1):
                print(f"{i}. {result.symbol} - {result.option_type} {result.strike}")
                print(f"   Current Price: ₹{result.current_price:.2f}")
                print(f"   Days to Expiry: {result.days_to_expiry} | Premium: ₹{result.premium:.2f}")
                print(f"   Daily Theta: ₹{result.theta:.3f} | Theta Acceleration: {result.theta_acceleration:.4f}")
                print(f"   Expected Total Theta by Expiry: ₹{result.expected_theta_by_expiry:.2f}")
                print(f"   IV vs Realized: {result.implied_move_vs_realized} (Vega: {result.vega:.3f})")
                print(f"   Theta/Premium Ratio: {result.theta_to_premium_ratio:.3f} (Efficiency: {result.efficiency_score:.1f}/100)")
                print(f"   Strategy: {result.suggested_strategy}\n")
        
        self.results_cache['theta_screener'] = results
        return results
    
    def demo_combo_screener(self):
        """Demonstrate Greeks + Technical Screener"""
        print("\n" + "="*120)
        print("DEMO 4: GREEKS + TECHNICAL COMBINATION SCREENER".center(120))
        print("="*120)
        print("\nFinding high-probability setups combining technical analysis with favorable Greeks")
        print("→ Best for: Multi-timeframe confirmation with Greeks edge\n")
        
        # Screen for combo
        results = self.screener.screen_greeks_technical_combo(
            technical_score_min=60,
            limit=15
        )
        
        if results:
            print(f"Found {len(results)} high-quality combo setups:\n")
            for i, result in enumerate(results[:5], 1):
                print(f"{i}. {result.symbol}")
                print(f"   Current Price: ₹{result.current_price:.2f}")
                print(f"   Technical Signal: {result.technical_signal} (Score: {result.technical_score:.0f}/100)")
                print(f"   Support: ₹{result.support_level:.2f} | Resistance: ₹{result.resistance_level:.2f}")
                print(f"   Optimal Strike: {result.optimal_strike} ({result.option_type})")
                print(f"   Entry Premium: ₹{result.entry_premium:.2f}")
                print(f"   Greeks Favorable: Delta={result.greeks_favorable['delta']:.2f}, Theta={result.greeks_favorable['theta']:.2f}")
                print(f"   Risk/Reward: {result.risk_reward_ratio:.2f}")
                print(f"   Strategy: {result.suggested_strategy}")
                print(f"   Combined Score: {result.combined_score:.1f}/100\n")
        
        self.results_cache['combo_screener'] = results
        return results
    
    def demo_hedging_screener(self):
        """Demonstrate Hedging Pairs Screener"""
        print("\n" + "="*120)
        print("DEMO 5: PORTFOLIO HEDGING PAIRS SCREENER".center(120))
        print("="*120)
        print("\nFinding highly correlated stock pairs for efficient hedging")
        print("→ Best for: Hedging concentrated long positions\n")
        
        # Screen for hedging pairs
        results = self.screener.screen_hedging_pairs(
            correlation_min=0.70,
            limit=10
        )
        
        if results:
            print(f"Found {len(results)} hedging pair opportunities:\n")
            for i, result in enumerate(results[:5], 1):
                print(f"{i}. {result.symbol_long} [LONG] <-> {result.symbol_short} [SHORT]")
                print(f"   Correlation: {result.correlation:.3f}")
                print(f"   Prices: {result.symbol_long}=₹{result.current_prices[result.symbol_long]:.2f}, "
                      f"{result.symbol_short}=₹{result.current_prices[result.symbol_short]:.2f}")
                print(f"   Delta (Long): {result.delta_long:.2f} | Delta (Short): {result.delta_short:.2f}")
                print(f"   Hedge Ratio: 1:{result.hedge_ratio:.2f}")
                print(f"   Cost of Hedge: ₹{result.cost_of_hedge:.2f}")
                print(f"   Protection Level: {result.protection_level:.0f}% | Upside Preserved: {result.upside_preserved:.0f}%")
                print(f"   Combined Greeks - Gamma: {result.gamma_exposure:.4f}, Vega: {result.vega_exposure:.3f}, Theta: {result.theta_benefit:.3f}\n")
        
        self.results_cache['hedging_screener'] = results
        return results
    
    def demo_delta_neutral_screener(self):
        """Demonstrate Delta Neutral Setups Screener"""
        print("\n" + "="*120)
        print("DEMO 6: DELTA NEUTRAL SETUPS SCREENER".center(120))
        print("="*120)
        print("\nFinding delta-neutral position setups with defined risk")
        print("→ Best for: Volatility plays with no directional bias\n")
        
        # Screen for delta neutral
        results = self.screener.screen_delta_neutral_setups(
            delta_tolerance=0.05,
            limit=15
        )
        
        if results:
            print(f"Found {len(results)} delta-neutral setup opportunities:\n")
            for i, result in enumerate(results[:5], 1):
                print(f"{i}. {result.symbol} - {result.suggested_strategy}")
                print(f"   Current Price: ₹{result.current_price:.2f}")
                print(f"   Setup: {result.setup_id}")
                print(f"   Long Legs: {result.long_legs}")
                print(f"   Short Legs: {result.short_legs}")
                print(f"   Combined Greeks:")
                print(f"     - Delta: {result.total_delta:.4f} (Target: ~0)")
                print(f"     - Gamma: {result.total_gamma:.4f}")
                print(f"     - Theta: {result.total_theta:.4f}")
                print(f"     - Vega: {result.total_vega:.4f}")
                print(f"   Net Premium: ₹{result.net_premium:.2f} (Debit/Credit)")
                print(f"   Max Profit: ₹{result.max_profit:.2f} | Max Loss: ₹{result.max_loss:.2f}")
                print(f"   Breakeven Points: {[f'₹{x:.0f}' for x in result.breakeven_points]}")
                print(f"   Efficiency Score: {result.efficiency_score:.1f}/100\n")
        
        self.results_cache['delta_neutral_screener'] = results
        return results
    
    # =========================================================================
    # COMPREHENSIVE REPORT
    # =========================================================================
    
    def generate_comprehensive_report(self):
        """Generate comprehensive report from all screeners"""
        print("\n" + "="*120)
        print("COMPREHENSIVE OPTIONS SCREENING REPORT".center(120))
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(120))
        print("="*120)
        
        # Run all screeners
        print("\n[1/6] Running IV Screener...")
        iv_results = self.demo_iv_screener()
        
        print("\n[2/6] Running Earnings Screener...")
        earnings_results = self.demo_earnings_screener()
        
        print("\n[3/6] Running Theta Decay Screener...")
        theta_results = self.demo_theta_screener()
        
        print("\n[4/6] Running Combo (Greeks+Technical) Screener...")
        combo_results = self.demo_combo_screener()
        
        print("\n[5/6] Running Hedging Pairs Screener...")
        hedge_results = self.demo_hedging_screener()
        
        print("\n[6/6] Running Delta Neutral Screener...")
        dn_results = self.demo_delta_neutral_screener()
        
        # Summary
        print("\n" + "="*120)
        print("SCREENING SUMMARY".center(120))
        print("="*120)
        print(f"\nIV Screener:              {len(iv_results) if iv_results else 0} opportunities")
        print(f"Earnings Screener:       {len(earnings_results) if earnings_results else 0} opportunities")
        print(f"Theta Decay Screener:    {len(theta_results) if theta_results else 0} opportunities")
        print(f"Combo Screener:          {len(combo_results) if combo_results else 0} opportunities")
        print(f"Hedging Pairs Screener:  {len(hedge_results) if hedge_results else 0} opportunities")
        print(f"Delta Neutral Screener:  {len(dn_results) if dn_results else 0} opportunities")
        print("\n" + "="*120)
        
        return {
            'iv_screener': iv_results,
            'earnings_screener': earnings_results,
            'theta_screener': theta_results,
            'combo_screener': combo_results,
            'hedging_screener': hedge_results,
            'delta_neutral_screener': dn_results
        }
    
    def get_top_signal_by_screener(self, screener_type: str) -> dict:
        """Get top opportunity from each screener"""
        cache = self.results_cache
        
        results = {
            'iv_screener': cache.get('iv_screener', []),
            'earnings_screener': cache.get('earnings_screener', []),
            'theta_screener': cache.get('theta_screener', []),
            'combo_screener': cache.get('combo_screener', []),
            'hedging_screener': cache.get('hedging_screener', []),
            'delta_neutral_screener': cache.get('delta_neutral_screener', [])
        }
        
        top_signals = {}
        for screen_name, opportunities in results.items():
            if opportunities:
                top_signals[screen_name] = opportunities[0]
        
        return top_signals


# =========================================================================
# MAIN EXECUTION
# =========================================================================

if __name__ == "__main__":
    """Run complete options screener demo"""
    
    logger.info("="*120)
    logger.info("OPTIONS SCREENERS - COMPREHENSIVE DEMO".center(120))
    logger.info("="*120)
    
    # Initialize demo (without live API for now)
    demo = OptionsScreenersDemo(api_service=None)
    
    # Generate comprehensive report
    all_results = demo.generate_comprehensive_report()
    
    # Print top opportunities from each screener
    print("\n" + "="*120)
    print("TOP OPPORTUNITY FROM EACH SCREENER".center(120))
    print("="*120)
    
    top_signals = demo.get_top_signal_by_screener('all')
    
    print("\n1. IV Screener - Best SELLING opportunity (high premium)")
    if top_signals.get('iv_screener'):
        top = top_signals['iv_screener']
        print(f"   {top.symbol} @ ₹{top.current_price:.2f} | IV: {top.current_iv:.2f}% ({top.iv_percentile:.0f} percentile)")
        print(f"   Strategy: {top.recommendation}")
    
    print("\n2. Earnings Screener - Best earnings play (volatility expansion)")
    if top_signals.get('earnings_screener'):
        top = top_signals['earnings_screener']
        print(f"   {top.symbol} @ ₹{top.current_price:.2f} | Earnings in {top.days_to_earnings} days")
        print(f"   Strategy: {top.suggested_strategy} | Score: {top.score:.0f}/100")
    
    print("\n3. Theta Screener - Best THETA opportunity (time decay)")
    if top_signals.get('theta_screener'):
        top = top_signals['theta_screener']
        print(f"   {top.symbol} {top.option_type} {top.strike} | Theta: ₹{top.theta:.2f}/day")
        print(f"   DTE: {top.days_to_expiry} | Premium: ₹{top.premium:.2f}")
    
    print("\n4. Combo Screener - Best multi-factor setup")
    if top_signals.get('combo_screener'):
        top = top_signals['combo_screener']
        print(f"   {top.symbol} @ ₹{top.current_price:.2f} | Signal: {top.technical_signal}")
        print(f"   Strategy: {top.suggested_strategy} | Risk/Reward: {top.risk_reward_ratio:.2f}")
    
    print("\n5. Hedging Screener - Best hedge pair (correlation-based)")
    if top_signals.get('hedging_screener'):
        top = top_signals['hedging_screener']
        print(f"   Long: {top.symbol_long} | Short: {top.symbol_short}")
        print(f"   Correlation: {top.correlation:.3f} | Hedge Cost: ₹{top.cost_of_hedge:.2f}")
    
    print("\n6. Delta Neutral Screener - Best volatility play (no directional bias)")
    if top_signals.get('delta_neutral_screener'):
        top = top_signals['delta_neutral_screener']
        print(f"   {top.symbol} - {top.suggested_strategy}")
        print(f"   Max Profit: ₹{top.max_profit:.2f} | Max Loss: ₹{top.max_loss:.2f}")
    
    print("\n" + "="*120)
    logger.info("Options Screeners Demo Complete ✅")
    print("="*120)
