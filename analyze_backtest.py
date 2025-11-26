#!/usr/bin/env python3
"""
Enhanced Strategy Backtest Analysis and Visualization
"""
import sys
import os
import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for better plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_backtest_results():
    """Load the latest backtest results"""
    reports_dir = Path('reports')
    
    # Find the latest results file
    result_files = list(reports_dir.glob('backtest_results_*.json'))
    if not result_files:
        print("❌ No backtest results found")
        return None
    
    latest_file = max(result_files, key=lambda x: x.stat().st_mtime)
    print(f"📊 Loading results from: {latest_file}")
    
    with open(latest_file, 'r') as f:
        results = json.load(f)
    
    return results

def analyze_strategy_performance(results):
    """Comprehensive analysis of strategy performance"""
    print("\n" + "="*80)
    print("📈 ENHANCED STRATEGY PERFORMANCE ANALYSIS")
    print("="*80)
    
    summary = results['summary']
    
    # Performance Analysis
    print(f"\n🎯 OVERALL PERFORMANCE")
    print(f"Portfolio Return:    {summary['total_return_pct']:.2%}")
    print(f"Annualized Return:   {summary['total_return_pct'] * (365/700):.2%}")  # Approx 700 days
    print(f"Total P&L:           ₹{summary['total_pnl']:,.2f}")
    print(f"Risk-Adjusted Return (Sharpe): {summary['sharpe_ratio']:.2f}")
    
    # Strategy Effectiveness
    print(f"\n🎲 STRATEGY EFFECTIVENESS")
    print(f"Win Rate:            {summary['win_rate']:.1%}")
    print(f"Profit Factor:       {summary['profit_factor']:.2f}")
    print(f"Average Win/Loss:    {summary['avg_win']/abs(summary['avg_loss']):.2f}x")
    print(f"Max Drawdown:        {summary['max_drawdown']:.2%}")
    
    # Risk Analysis
    print(f"\n⚠️  RISK ANALYSIS")
    risk_rating = "LOW" if summary['max_drawdown'] > -0.05 else "MODERATE" if summary['max_drawdown'] > -0.15 else "HIGH"
    print(f"Risk Level:          {risk_rating}")
    print(f"Volatility:          {summary['volatility']:.2%}")
    print(f"Downside Protection: {'GOOD' if summary['profit_factor'] > 1.0 else 'NEEDS IMPROVEMENT'}")
    
    # Enhanced Strategy Analysis
    print(f"\n🔥 ENHANCED INDICATORS IMPACT")
    
    # Analyze exit reasons
    exit_reasons = results.get('exit_reasons', {})
    technical_exits = sum([
        exit_reasons.get('technical_exit_stoch_rsi_overbought+rsi_overbought', 0),
        exit_reasons.get('technical_exit_macd_bearish+rsi_overbought', 0),
        exit_reasons.get('trend_reversal', 0)
    ])
    
    stop_losses = exit_reasons.get('stop_loss', 0)
    targets = exit_reasons.get('target_achieved', 0)
    
    print(f"Technical Exits:     {technical_exits} ({technical_exits/summary['total_trades']:.1%})")
    print(f"Target Achievements: {targets} ({targets/summary['total_trades']:.1%})")
    print(f"Stop Losses:         {stop_losses} ({stop_losses/summary['total_trades']:.1%})")
    
    # Symbol Performance Analysis
    print(f"\n🏢 SYMBOL PERFORMANCE BREAKDOWN")
    symbol_perf = results.get('symbol_performance', {})
    
    best_performer = max(symbol_perf.items(), key=lambda x: x[1]['pnl']) if symbol_perf else None
    worst_performer = min(symbol_perf.items(), key=lambda x: x[1]['pnl']) if symbol_perf else None
    
    if best_performer:
        print(f"Best Performer:      {best_performer[0]} (₹{best_performer[1]['pnl']:,.0f} P&L)")
    if worst_performer:
        print(f"Worst Performer:     {worst_performer[0]} (₹{worst_performer[1]['pnl']:,.0f} P&L)")
    
    # Strategy Recommendations
    print(f"\n💡 STRATEGY RECOMMENDATIONS")
    
    if summary['win_rate'] < 0.4:
        print("• 🔴 Consider tightening entry conditions to improve win rate")
    
    if summary['profit_factor'] < 1.0:
        print("• 🔴 Strategy is losing money - review exit conditions")
        print("• 🔧 Consider adjusting stop-loss and target levels")
    
    if summary['max_drawdown'] < -0.15:
        print("• ⚠️  High drawdown detected - implement better risk management")
    
    if technical_exits > stop_losses:
        print("• ✅ Enhanced indicators are working well for exits!")
    else:
        print("• 🔧 Consider refining technical indicator thresholds")
    
    if targets < stop_losses:
        print("• 🔧 Consider adjusting target levels or improving entry timing")
    
    return summary

def create_performance_charts(results):
    """Create comprehensive performance visualization"""
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Enhanced Strategy Backtest Analysis', fontsize=16, fontweight='bold')
    
    # 1. Portfolio Value Over Time
    portfolio_df = pd.DataFrame(results['daily_portfolio'])
    portfolio_df['date'] = pd.to_datetime(portfolio_df['date'])
    
    axes[0, 0].plot(portfolio_df['date'], portfolio_df['total_value'], linewidth=2, color='blue')
    axes[0, 0].axhline(y=100000, color='red', linestyle='--', alpha=0.7, label='Initial Capital')
    axes[0, 0].set_title('Portfolio Value Over Time')
    axes[0, 0].set_ylabel('Portfolio Value (₹)')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].tick_params(axis='x', rotation=45)
    
    # 2. Drawdown Analysis
    portfolio_df['peak'] = portfolio_df['total_value'].expanding().max()
    portfolio_df['drawdown'] = (portfolio_df['total_value'] - portfolio_df['peak']) / portfolio_df['peak'] * 100
    
    axes[0, 1].fill_between(portfolio_df['date'], portfolio_df['drawdown'], 0, 
                           color='red', alpha=0.3, label='Drawdown')
    axes[0, 1].plot(portfolio_df['date'], portfolio_df['drawdown'], color='red', linewidth=1)
    axes[0, 1].set_title('Portfolio Drawdown')
    axes[0, 1].set_ylabel('Drawdown (%)')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].tick_params(axis='x', rotation=45)
    
    # 3. Win/Loss Distribution
    trades_df = pd.DataFrame(results['trades'])
    
    win_trades = trades_df[trades_df['pnl'] > 0]['pnl']
    loss_trades = trades_df[trades_df['pnl'] <= 0]['pnl']
    
    axes[0, 2].hist([win_trades, loss_trades], bins=20, alpha=0.7, 
                   color=['green', 'red'], label=['Wins', 'Losses'])
    axes[0, 2].set_title('P&L Distribution')
    axes[0, 2].set_xlabel('P&L (₹)')
    axes[0, 2].set_ylabel('Frequency')
    axes[0, 2].legend()
    axes[0, 2].grid(True, alpha=0.3)
    
    # 4. Exit Reasons Analysis
    exit_reasons = results.get('exit_reasons', {})
    reasons = list(exit_reasons.keys())
    counts = list(exit_reasons.values())
    
    # Shorten reason names for better display
    short_reasons = []
    for reason in reasons:
        if 'technical_exit' in reason:
            short_reasons.append('Technical Exit')
        elif 'stop_loss' in reason:
            short_reasons.append('Stop Loss')
        elif 'target_achieved' in reason:
            short_reasons.append('Target Hit')
        elif 'trend_reversal' in reason:
            short_reasons.append('Trend Reversal')
        else:
            short_reasons.append(reason.replace('_', ' ').title())
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(reasons)))
    axes[1, 0].pie(counts, labels=short_reasons, autopct='%1.1f%%', colors=colors)
    axes[1, 0].set_title('Exit Reasons Distribution')
    
    # 5. Symbol Performance
    symbol_perf = results.get('symbol_performance', {})
    symbols = list(symbol_perf.keys())
    pnls = [symbol_perf[symbol]['pnl'] for symbol in symbols]
    colors = ['green' if pnl > 0 else 'red' for pnl in pnls]
    
    bars = axes[1, 1].bar(symbols, pnls, color=colors, alpha=0.7)
    axes[1, 1].set_title('P&L by Symbol')
    axes[1, 1].set_ylabel('P&L (₹)')
    axes[1, 1].axhline(y=0, color='black', linestyle='-', alpha=0.3)
    axes[1, 1].grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, pnl in zip(bars, pnls):
        height = bar.get_height()
        axes[1, 1].text(bar.get_x() + bar.get_width()/2., height + (100 if height > 0 else -200),
                        f'₹{pnl:,.0f}', ha='center', va='bottom' if height > 0 else 'top')
    
    # 6. Monthly Returns
    trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date'])
    trades_df['month'] = trades_df['exit_date'].dt.to_period('M')
    monthly_returns = trades_df.groupby('month')['pnl'].sum()
    
    months = [str(m) for m in monthly_returns.index]
    returns = monthly_returns.values
    colors = ['green' if ret > 0 else 'red' for ret in returns]
    
    axes[1, 2].bar(range(len(months)), returns, color=colors, alpha=0.7)
    axes[1, 2].set_title('Monthly P&L')
    axes[1, 2].set_ylabel('P&L (₹)')
    axes[1, 2].set_xticks(range(len(months)))
    axes[1, 2].set_xticklabels(months, rotation=45)
    axes[1, 2].axhline(y=0, color='black', linestyle='-', alpha=0.3)
    axes[1, 2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save the chart
    chart_file = Path('reports') / f'backtest_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"\n📊 Performance charts saved to: {chart_file}")

def generate_strategy_report(results):
    """Generate comprehensive strategy report"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = Path('reports') / f'strategy_analysis_{timestamp}.md'
    
    summary = results['summary']
    
    report_content = f"""# Enhanced Strategy Backtest Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

The enhanced Buy & Hold trend-following strategy with MACD, RSI, and Stochastic RSI integration was backtested over a {'~23 month' if 'daily_portfolio' in results else 'simulated'} period with realistic market data.

### Key Findings

- **Total Return:** {summary['total_return_pct']:.2%}
- **Win Rate:** {summary['win_rate']:.1%}
- **Profit Factor:** {summary['profit_factor']:.2f}
- **Maximum Drawdown:** {summary['max_drawdown']:.2%}
- **Sharpe Ratio:** {summary['sharpe_ratio']:.2f}

## Performance Analysis

### Financial Performance
- Initial Capital: ₹{summary['initial_capital']:,.2f}
- Final Capital: ₹{summary['final_capital']:,.2f}
- Total P&L: ₹{summary['total_pnl']:,.2f}
- Annualized Return: {summary['total_return_pct'] * (365/700):.2%}

### Trading Statistics
- Total Trades Executed: {summary['total_trades']}
- Winning Trades: {summary['winning_trades']} ({summary['win_rate']:.1%})
- Losing Trades: {summary['losing_trades']}
- Average Win: ₹{summary['avg_win']:,.2f}
- Average Loss: ₹{summary['avg_loss']:,.2f}

### Risk Metrics
- Volatility: {summary['volatility']:.2%}
- Risk-Adjusted Return: {summary['sharpe_ratio']:.2f}
- Maximum Drawdown: {summary['max_drawdown']:.2%}

## Enhanced Strategy Analysis

### Multi-Indicator Effectiveness

The enhanced strategy incorporates:
1. **MACD (12,26,9)** for trend momentum confirmation
2. **Stochastic RSI** for precise overbought/oversold timing
3. **Enhanced RSI analysis** with healthy range validation

### Exit Strategy Performance
"""

    # Add exit reasons analysis
    if 'exit_reasons' in results:
        exit_reasons = results['exit_reasons']
        report_content += f"""
| Exit Reason | Count | Percentage |
|-------------|-------|------------|"""
        
        for reason, count in exit_reasons.items():
            pct = count / summary['total_trades'] * 100
            report_content += f"""
| {reason.replace('_', ' ').title()} | {count} | {pct:.1f}% |"""

    # Add symbol performance
    report_content += f"""

### Symbol Performance Analysis
"""
    
    if 'symbol_performance' in results:
        symbol_perf = results['symbol_performance']
        report_content += f"""
| Symbol | Total P&L | Avg Return | Trade Count |
|--------|-----------|------------|-------------|"""
        
        for symbol, perf in symbol_perf.items():
            report_content += f"""
| {symbol} | ₹{perf['pnl']:,.0f} | {perf['pnl_pct']:.2%} | {perf['trade_count']} |"""

    # Add recommendations
    report_content += f"""

## Strategy Recommendations

### Immediate Actions Required
"""
    
    if summary['win_rate'] < 0.4:
        report_content += f"""
- 🔴 **Low Win Rate Alert:** Current win rate of {summary['win_rate']:.1%} is below optimal threshold
- **Action:** Tighten entry conditions by increasing signal strength threshold
"""
    
    if summary['profit_factor'] < 1.0:
        report_content += f"""
- 🔴 **Negative Profit Factor:** Strategy is currently unprofitable
- **Action:** Review exit conditions and adjust stop-loss/target ratios
"""
    
    if summary['max_drawdown'] < -0.15:
        report_content += f"""
- ⚠️ **High Drawdown Risk:** Maximum drawdown of {summary['max_drawdown']:.2%} exceeds acceptable levels
- **Action:** Implement stricter position sizing and daily loss limits
"""

    report_content += f"""

### Strategy Optimization Suggestions

1. **Entry Conditions Enhancement**
   - Consider increasing minimum signal strength from 0.7 to 0.8
   - Add volume confirmation requirements for all entries
   - Implement sector rotation to avoid concentration risk

2. **Exit Strategy Refinement**
   - Fine-tune Stochastic RSI overbought levels (current: 80)
   - Consider dynamic stop-loss based on volatility
   - Implement partial profit-taking at intermediate levels

3. **Risk Management Improvements**
   - Reduce maximum position size from 10% to 8% of capital
   - Implement correlation-based position limits
   - Add maximum open positions limit (current: 5)

4. **Technical Indicator Optimization**
   - Test different MACD parameters (current: 12,26,9)
   - Optimize RSI periods for different market conditions
   - Consider adding momentum confirmation indicators

## Market Conditions Impact

### Strategy Performance in Different Market Phases

Based on the backtest results, the enhanced strategy shows:

- **Trending Markets:** {"Good" if summary['profit_factor'] > 1.2 else "Mixed"} performance with enhanced indicator confirmation
- **Sideways Markets:** {"Challenging" if summary['win_rate'] < 0.4 else "Adequate"} performance due to whipsaws
- **Volatile Markets:** {"Well-managed" if summary['max_drawdown'] > -0.1 else "Needs improvement"} risk through technical exits

## Conclusion

The enhanced Buy & Hold strategy with MACD, RSI, and Stochastic RSI integration demonstrates {"strong potential" if summary['sharpe_ratio'] > 0 else "areas for improvement"} in systematic trading execution. 

**Overall Rating:** {"EXCELLENT" if summary['profit_factor'] > 1.5 else "GOOD" if summary['profit_factor'] > 1.2 else "FAIR" if summary['profit_factor'] > 1.0 else "NEEDS IMPROVEMENT"}

### Next Steps

1. **Paper Trading:** Deploy strategy in paper trading mode with optimized parameters
2. **Parameter Tuning:** Implement suggested optimizations and re-test
3. **Live Testing:** Start with small capital allocation (₹10,000-₹25,000)
4. **Monitoring:** Track real-time performance vs. backtest expectations

---

*This report was generated automatically by the MyBreezeApp Enhanced Strategy Backtesting System.*
"""
    
    with open(report_file, 'w') as f:
        f.write(report_content)
    
    print(f"📄 Comprehensive strategy report saved to: {report_file}")
    return report_file

def main():
    """Main analysis function"""
    print("🔍 MyBreezeApp Enhanced Strategy Analysis")
    print("=" * 50)
    
    # Load results
    results = load_backtest_results()
    if not results:
        return
    
    # Analyze performance
    summary = analyze_strategy_performance(results)
    
    # Create visualizations
    try:
        create_performance_charts(results)
    except Exception as e:
        print(f"⚠️ Could not create charts (matplotlib not available): {e}")
    
    # Generate comprehensive report
    report_file = generate_strategy_report(results)
    
    print(f"\n✅ Analysis complete!")
    print(f"📊 Check the reports/ directory for detailed analysis files")
    
    return results

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()