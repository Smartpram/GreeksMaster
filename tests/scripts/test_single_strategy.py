#!/usr/bin/env python3
"""
Quick test of the optimized strategy
"""

from app.services.backtesting import BacktestingEngine
from app.strategies.optimized_buy_hold_trend import create_optimized_strategy

def test_optimized_strategy():
    print("Testing Optimized Strategy...")
    
    engine = BacktestingEngine()
    strategy = create_optimized_strategy()
    
    results = engine.run_backtest(
        strategy, 
        'RELIANCE', 
        start_date='2023-01-01', 
        end_date='2024-01-01'
    )
    
    print(f"Return: {results['total_return']:.2%}")
    print(f"Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate']:.1%}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    
    return results

if __name__ == "__main__":
    test_optimized_strategy()