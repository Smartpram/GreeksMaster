"""
Full Pipeline Example: From Stock Signal to Strategy Recommendation
===================================================================

Demonstrates all three layers working together:
1. Stock screener (backtest_indian_stocks_real_data.py)
2. Signal normalizer (signal_normalizer.py)
3. Strategy selector (options_strategy_selector.py)

This is a dry-run that converts the AXIS backtest result into
a fully actionable strategy recommendation.
"""

import json
from datetime import datetime
import sys
from pathlib import Path

# Add parent dir
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.signal_normalizer import SignalNormalizer, NormalizedSignal
from app.options_strategy_selector import OptionsStrategySelector


def main():
    """Full pipeline: screener → normalizer → strategy selector"""
    
    print("\n" + "="*80)
    print("FULL PIPELINE: Stock Signal → Strategy Recommendation")
    print("="*80)
    
    # =========================================================================
    # STEP 1: Stock Screener Output (from backtest_indian_stocks_real_data.py)
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 1: STOCK SCREENER (backtest_indian_stocks_real_data.py)")
    print("="*80)
    
    # Simulating the output from backtest_indian_stocks_real_data.py
    # In production, this would come directly from the backtest module
    stock_signals = [
        {
            'symbol': 'AXIS',
            'signal_type': 'BREAKOUT',
            'direction': 'BULLISH',
            'confidence': 70,
            'spot_price': 1292.40,
            'sma_20': 1269.67,
            'sma_50': None,
            'atr': 24.54,
            'volatility': 0.200,
            'volume': 7533477,
            'avg_volume': 7533477,
            'price_change_20d': 2.9,
            'signal_date': '2026-06-09'
        },
        {
            'symbol': 'INFY',
            'signal_type': 'MOMENTUM',
            'direction': 'BULLISH',
            'confidence': 65,
            'spot_price': 1180.30,
            'sma_20': 1175.27,
            'sma_50': None,
            'atr': 31.69,
            'volatility': 0.332,
            'volume': 10983029,
            'avg_volume': 10983029,
            'price_change_20d': 5.1,
            'signal_date': '2026-06-09'
        },
    ]
    
    print(f"\nStock screener generated {len(stock_signals)} signals:")
    for sig in stock_signals:
        print(f"  • {sig['symbol']}: {sig['signal_type']} {sig['direction']} "
              f"(Conf: {sig['confidence']}%)")
    
    # =========================================================================
    # STEP 2: Signal Normalizer
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 2: SIGNAL NORMALIZER (signal_normalizer.py)")
    print("="*80)
    
    normalizer = SignalNormalizer()
    normalized_signals = []
    
    for stock_sig in stock_signals:
        # Normalize each stock signal
        normalized = normalizer.normalize_from_stock_analysis(
            symbol=stock_sig['symbol'],
            signal_type=stock_sig['signal_type'],
            direction=stock_sig['direction'],
            confidence=stock_sig['confidence'],
            spot_price=stock_sig['spot_price'],
            sma_20=stock_sig['sma_20'],
            sma_50=stock_sig['sma_50'],
            atr=stock_sig['atr'],
            volatility=stock_sig['volatility'],
            volume=stock_sig['volume'],
            avg_volume=stock_sig['avg_volume'],
            price_change_20d=stock_sig['price_change_20d'],
            signal_date=stock_sig['signal_date']
        )
        normalized_signals.append(normalized)
    
    print(f"\nNormalized {len(normalized_signals)} signals:")
    print("\nExample: AXIS Signal Normalized")
    print("-" * 80)
    axis_signal = normalized_signals[0]
    print(f"Signal ID:          {axis_signal.signal_id}")
    print(f"Symbol:             {axis_signal.symbol}")
    print(f"Type:               {axis_signal.signal_type}")
    print(f"Direction:          {axis_signal.direction}")
    print(f"Confidence:         {axis_signal.confidence}% ({axis_signal.confidence_band})")
    print(f"Spot Price:         ₹{axis_signal.spot_price:.2f}")
    print(f"Expected Move:      {axis_signal.expected_move_pct:.2f}%")
    print(f"Holding Period:     {axis_signal.holding_period_days} days")
    print(f"Volatility:         {axis_signal.volatility*100:.1f}%")
    print(f"ATR:                ₹{axis_signal.atr:.2f}")
    print(f"Urgency:            {axis_signal.urgency}")
    print(f"Features:")
    for key, val in axis_signal.features.items():
        print(f"  - {key}: {val}")
    
    # =========================================================================
    # STEP 3: Strategy Selector
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 3: STRATEGY SELECTOR (options_strategy_selector.py)")
    print("="*80)
    
    selector = OptionsStrategySelector(max_loss_per_trade_pct=2.0)
    
    # Convert normalized signals to strategy recommendations
    recommendations = []
    for normalized_sig in normalized_signals:
        # Convert to dict for selector
        sig_dict = {
            'signal_id': normalized_sig.signal_id,
            'symbol': normalized_sig.symbol,
            'signal_type': normalized_sig.signal_type,
            'direction': normalized_sig.direction,
            'confidence': normalized_sig.confidence,
            'spot_price': normalized_sig.spot_price,
            'holding_period_days': normalized_sig.holding_period_days,
            'volatility': normalized_sig.volatility,
            'atr': normalized_sig.atr,
            'expected_move_pct': normalized_sig.expected_move_pct,
        }
        
        # Get strategy recommendation
        rec = selector.select_strategy(sig_dict)
        if rec:
            recommendations.append(rec)
    
    print(f"\nStrategy selector generated {len(recommendations)} recommendations:")
    
    # =========================================================================
    # STEP 4: Display Recommendations
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 4: STRATEGY RECOMMENDATIONS (Ready for Execution)")
    print("="*80)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\nRecommendation {i}: {rec.strategy_type} for {rec.symbol}")
        print("-" * 80)
        print(f"Strategy ID:        {rec.strategy_id}")
        print(f"Signal ID:          {rec.signal_id}")
        print(f"Direction:          {rec.direction}")
        print(f"Confidence:         {rec.confidence}%")
        print(f"\nRationale:")
        print(f"  {rec.rationale}")
        print(f"\nRisk & Capital:")
        print(f"  Max Risk:         ₹{rec.max_risk_per_trade:.2f}")
        print(f"  Premium Budget:   ₹{rec.max_premium_outlay:.2f}")
        print(f"  Stop Loss:        {rec.stop_loss_pct}%")
        print(f"  Profit Target:    {rec.profit_target_pct}%")
        print(f"  Time Stop:        {rec.time_stop_days} days")
        print(f"  Holding Period:   {rec.holding_period_days} days")
        print(f"\nStrategy Legs:")
        for j, leg in enumerate(rec.legs, 1):
            print(f"  Leg {j}: {leg.position_type}")
            print(f"    Strike Selection: {leg.strike_selection}")
            print(f"    DTE: {leg.expiry_dte}")
            print(f"    Quantity: {leg.quantity}")
        print(f"\nPre-Trade Checklist (to be validated in Phase 3):")
        print(f"  ☐ Chain liquidity sufficient?")
        print(f"  ☐ Bid-ask spread acceptable?")
        print(f"  ☐ Premium within budget?")
        print(f"  ☐ Account margin available?")
        print(f"  ☐ Sector concentration OK?")
        print(f"  ☐ API/session quality good?")
    
    # =========================================================================
    # STEP 5: Export Pipeline Output
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 5: EXPORT PIPELINE OUTPUT")
    print("="*80)
    
    # Export normalized signals
    sig_filepath = normalizer.export_signals_json(
        "backtest_reports/pipeline_normalized_signals.json"
    )
    print(f"\n✓ Normalized signals: {sig_filepath}")
    
    # Export strategy recommendations
    rec_filepath = selector.export_recommendations_json(
        "backtest_reports/pipeline_strategy_recommendations.json"
    )
    print(f"✓ Recommendations: {rec_filepath}")
    
    # =========================================================================
    # STEP 6: Summary
    # =========================================================================
    print("\n" + "="*80)
    print("PIPELINE SUMMARY")
    print("="*80)
    
    print(f"\nInput:  {len(stock_signals)} stock signals")
    print(f"  → Normalized: {len(normalized_signals)} signals")
    print(f"  → Strategies: {len(recommendations)} recommendations")
    
    print(f"\nStrategy Breakdown:")
    from collections import Counter
    strategy_counts = Counter([r.strategy_type for r in recommendations])
    for strategy, count in strategy_counts.items():
        print(f"  • {strategy}: {count}")
    
    print(f"\nDirection Breakdown:")
    direction_counts = Counter([r.direction for r in recommendations])
    for direction, count in direction_counts.items():
        print(f"  • {direction}: {count}")
    
    print(f"\nConfidence Breakdown:")
    conf_90 = len([r for r in recommendations if r.confidence >= 90])
    conf_70 = len([r for r in recommendations if 70 <= r.confidence < 90])
    conf_50 = len([r for r in recommendations if 50 <= r.confidence < 70])
    print(f"  • Very High (≥90%): {conf_90}")
    print(f"  • High (70-89%): {conf_70}")
    print(f"  • Medium (50-69%): {conf_50}")
    
    total_capital_at_risk = sum([r.max_risk_per_trade for r in recommendations])
    print(f"\nTotal Capital at Risk: ₹{total_capital_at_risk:.2f}")
    
    # =========================================================================
    # FINAL NOTES
    # =========================================================================
    print("\n" + "="*80)
    print("NEXT PHASE: Execution Engine (Phase 3)")
    print("="*80)
    print("\nThe recommendations are now ready for the execution engine, which will:")
    print("  1. Authenticate with Breeze API")
    print("  2. Query live options chains (NFO)")
    print("  3. Filter contracts by liquidity")
    print("  4. Run pre-trade risk checks")
    print("  5. Place limit orders")
    print("  6. Monitor positions")
    print("  7. Execute exits (SL/PT/time)")
    print("\nBefore Phase 3: Complete historical options backtesting (Phase 2)")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
