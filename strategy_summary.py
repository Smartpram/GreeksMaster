#!/usr/bin/env python3
"""
Strategy Performance Summary - Quick Analysis
"""
import json
from pathlib import Path
from datetime import datetime

def load_latest_results():
    """Load the latest backtest results"""
    reports_dir = Path('reports')
    result_files = list(reports_dir.glob('backtest_results_*.json'))
    
    if not result_files:
        print("No backtest results found")
        return None
    
    latest_file = max(result_files, key=lambda x: x.stat().st_mtime)
    
    with open(latest_file, 'r') as f:
        results = json.load(f)
    
    return results, latest_file

def create_summary_report():
    """Create a comprehensive summary report"""
    
    results, results_file = load_latest_results()
    if not results:
        return
    
    summary = results['summary']
    
    print("\n" + "="*70)
    print("📊 MYBREEZE APP - ENHANCED STRATEGY BACKTEST SUMMARY")
    print("="*70)
    
    print(f"\n📋 BACKTEST DETAILS")
    print(f"Results File: {results_file.name}")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backtest Period: 22+ months (2023-01-01 to 2024-10-31)")
    print(f"Symbols Tested: RELIANCE, TCS, HDFCBANK, INFY, HINDUNILVR")
    
    print(f"\n💰 FINANCIAL PERFORMANCE")
    print(f"Initial Capital:     Rs. {summary['initial_capital']:,.0f}")
    print(f"Final Capital:       Rs. {summary['final_capital']:,.0f}")
    print(f"Total P&L:           Rs. {summary['total_pnl']:,.0f}")
    print(f"Portfolio Return:    {summary['total_return_pct']:.2%}")
    print(f"Annualized Return:   {(summary['total_return_pct'] * 365/700):.2%}")
    
    print(f"\n📈 TRADING STATISTICS")
    print(f"Total Trades:        {summary['total_trades']}")
    print(f"Winning Trades:      {summary['winning_trades']} ({summary['win_rate']:.1%})")
    print(f"Losing Trades:       {summary['losing_trades']}")
    print(f"Average Win:         Rs. {summary['avg_win']:,.0f}")
    print(f"Average Loss:        Rs. {summary['avg_loss']:,.0f}")
    print(f"Win/Loss Ratio:      {summary['avg_win']/abs(summary['avg_loss']):.2f}x")
    
    print(f"\n⚡ STRATEGY EFFECTIVENESS")
    print(f"Profit Factor:       {summary['profit_factor']:.2f}")
    print(f"Sharpe Ratio:        {summary['sharpe_ratio']:.2f}")
    print(f"Maximum Drawdown:    {summary['max_drawdown']:.2%}")
    print(f"Volatility:          {summary['volatility']:.2%}")
    
    # Enhanced Strategy Analysis
    print(f"\n🎯 ENHANCED INDICATORS PERFORMANCE")
    exit_reasons = results.get('exit_reasons', {})
    
    technical_exits = sum([
        exit_reasons.get('technical_exit_stoch_rsi_overbought+rsi_overbought', 0),
        exit_reasons.get('technical_exit_macd_bearish+rsi_overbought', 0),
        exit_reasons.get('trend_reversal', 0)
    ])
    
    stop_losses = exit_reasons.get('stop_loss', 0)
    targets = exit_reasons.get('target_achieved', 0)
    
    print(f"Technical Exits:     {technical_exits} trades ({technical_exits/summary['total_trades']:.1%})")
    print(f"Target Achievements: {targets} trades ({targets/summary['total_trades']:.1%})")
    print(f"Stop Losses:         {stop_losses} trades ({stop_losses/summary['total_trades']:.1%})")
    
    print(f"\n🏢 SYMBOL PERFORMANCE")
    symbol_perf = results.get('symbol_performance', {})
    
    for symbol, perf in sorted(symbol_perf.items(), key=lambda x: x[1]['pnl'], reverse=True):
        status = "✅" if perf['pnl'] > 0 else "❌"
        print(f"{status} {symbol:12} Rs. {perf['pnl']:>7,.0f} ({perf['trade_count']} trades)")
    
    # Strategy Assessment
    print(f"\n🔍 STRATEGY ASSESSMENT")
    
    # Overall Rating
    if summary['profit_factor'] > 1.5:
        rating = "EXCELLENT ⭐⭐⭐⭐⭐"
    elif summary['profit_factor'] > 1.2:
        rating = "GOOD ⭐⭐⭐⭐"
    elif summary['profit_factor'] > 1.0:
        rating = "FAIR ⭐⭐⭐"
    else:
        rating = "NEEDS IMPROVEMENT ⭐⭐"
    
    print(f"Overall Rating:      {rating}")
    
    # Risk Assessment
    if summary['max_drawdown'] > -0.05:
        risk_level = "LOW RISK 🟢"
    elif summary['max_drawdown'] > -0.15:
        risk_level = "MODERATE RISK 🟡"
    else:
        risk_level = "HIGH RISK 🔴"
    
    print(f"Risk Level:          {risk_level}")
    
    # Win Rate Assessment
    if summary['win_rate'] > 0.6:
        win_assessment = "EXCELLENT 🎯"
    elif summary['win_rate'] > 0.45:
        win_assessment = "GOOD 👍"
    elif summary['win_rate'] > 0.35:
        win_assessment = "FAIR 📊"
    else:
        win_assessment = "NEEDS IMPROVEMENT 📉"
    
    print(f"Win Rate Quality:    {win_assessment}")
    
    print(f"\n🚀 KEY INSIGHTS")
    
    print(f"✓ Enhanced Strategy Impact:")
    if technical_exits > targets:
        print(f"  • Technical indicators are actively protecting profits")
    else:
        print(f"  • Consider refining technical indicator sensitivity")
    
    print(f"✓ Risk Management:")
    if stop_losses > targets:
        print(f"  • Defensive approach - many trades hit stop-loss")
        print(f"  • Consider tighter entry conditions or wider stops")
    else:
        print(f"  • Good balance between stops and targets")
    
    print(f"✓ Symbol Diversification:")
    profitable_symbols = sum(1 for perf in symbol_perf.values() if perf['pnl'] > 0)
    print(f"  • {profitable_symbols}/{len(symbol_perf)} symbols were profitable")
    
    if profitable_symbols < len(symbol_perf) / 2:
        print(f"  • Consider sector/stock selection improvements")
    
    print(f"\n🎯 IMMEDIATE RECOMMENDATIONS")
    
    if summary['profit_factor'] < 1.0:
        print(f"🔴 CRITICAL: Strategy is losing money")
        print(f"   • Review entry conditions - current win rate {summary['win_rate']:.1%} too low")
        print(f"   • Consider increasing signal strength threshold from 0.7 to 0.8")
        print(f"   • Test different stop-loss levels (current: 5%)")
    
    if summary['win_rate'] < 0.4:
        print(f"🔴 LOW WIN RATE: Only {summary['win_rate']:.1%} of trades profitable")
        print(f"   • Add volume confirmation to entry conditions")
        print(f"   • Consider momentum filters (price above key MAs)")
        print(f"   • Test stricter RSI healthy range requirements")
    
    if summary['max_drawdown'] < -0.15:
        print(f"🔴 HIGH DRAWDOWN: {summary['max_drawdown']:.1%} maximum loss")
        print(f"   • Reduce position size from 10% to 6-8% per trade")
        print(f"   • Implement daily loss limits (2% of capital)")
        print(f"   • Consider maximum open positions limit")
    
    print(f"\n💡 OPTIMIZATION SUGGESTIONS")
    print(f"1. Entry Refinement:")
    print(f"   • Increase minimum signal strength to 0.8")
    print(f"   • Add trend strength filters (ADX > 25)")
    print(f"   • Require volume > 20-day average")
    
    print(f"2. Exit Strategy:")
    print(f"   • Test dynamic stops based on ATR")
    print(f"   • Consider partial profit taking at +10%")
    print(f"   • Refine technical exit thresholds")
    
    print(f"3. Risk Management:")
    print(f"   • Position sizing: 6-8% max per trade")
    print(f"   • Correlation limits: Max 2 trades in same sector")
    print(f"   • Daily loss limit: 2% of portfolio")
    
    print(f"4. Technical Indicators:")
    print(f"   • Test MACD parameters (current: 12,26,9)")
    print(f"   • Optimize RSI periods for market conditions")
    print(f"   • Add momentum confirmation (MACD histogram)")
    
    print(f"\n🎊 NEXT STEPS")
    print(f"1. 📝 Implement suggested optimizations")
    print(f"2. 🧪 Re-run backtest with new parameters")
    print(f"3. 📋 Start paper trading with optimized strategy")
    print(f"4. 💰 Begin live trading with small capital (Rs. 10,000-25,000)")
    print(f"5. 📊 Monitor performance vs backtest expectations")
    
    print(f"\n" + "="*70)
    print(f"Analysis Complete! Check reports/ folder for detailed files.")
    print(f"="*70)
    
    # Save simple text report
    report_file = Path('reports') / f'strategy_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    
    # Create a simple text version without special characters
    simple_report = f"""
MyBreezeApp Enhanced Strategy Backtest Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

FINANCIAL PERFORMANCE:
- Initial Capital: Rs. {summary['initial_capital']:,.0f}
- Final Capital: Rs. {summary['final_capital']:,.0f}  
- Total P&L: Rs. {summary['total_pnl']:,.0f}
- Portfolio Return: {summary['total_return_pct']:.2%}
- Annualized Return: {(summary['total_return_pct'] * 365/700):.2%}

TRADING STATISTICS:
- Total Trades: {summary['total_trades']}
- Win Rate: {summary['win_rate']:.1%}
- Profit Factor: {summary['profit_factor']:.2f}
- Sharpe Ratio: {summary['sharpe_ratio']:.2f}
- Max Drawdown: {summary['max_drawdown']:.2%}

SYMBOL PERFORMANCE:
"""
    
    for symbol, perf in sorted(symbol_perf.items(), key=lambda x: x[1]['pnl'], reverse=True):
        simple_report += f"- {symbol}: Rs. {perf['pnl']:,.0f} ({perf['trade_count']} trades)\n"
    
    simple_report += f"""
KEY RECOMMENDATIONS:
1. Strategy is currently unprofitable - needs optimization
2. Low win rate ({summary['win_rate']:.1%}) requires tighter entry conditions  
3. High stop-loss rate suggests market timing issues
4. Consider reducing position sizes and adding volume filters
5. Test different technical indicator parameters

NEXT STEPS:
1. Implement optimization suggestions
2. Re-run backtest with improved parameters
3. Start paper trading before live deployment
"""
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(simple_report)
    
    print(f"Summary report saved to: {report_file}")

if __name__ == "__main__":
    create_summary_report()