@echo off
REM ============================================================================
REM Start ML-Enhanced Trading System with Online Learning
REM ============================================================================
REM This batch file starts the trading scheduler with ML models that learn
REM continuously from paper trading results
REM ============================================================================

cd /d "C:\Data\GreeksMaster"

echo.
echo ============================================================================
echo ML-ENHANCED TRADING SYSTEM WITH ONLINE LEARNING
echo ============================================================================
echo.
echo What's Running:
echo   * 38 daily trading executions (every 10 minutes)
echo   * Technical indicators (SMA, RSI, MACD, Bollinger, ATR, ADX)
echo   * ML predictions (XGBoost, Random Forest, Gradient Boosting)
echo   * Hybrid confidence scoring (Technical + ML combined)
echo   * Automatic model retraining (every 100 trades)
echo   * Real-time P&L with accurate fees
echo.
echo Expected Results:
echo   * 120-280 paper trades per day
echo   * 43-52%% win rate (improving over time)
echo   * Models improving: v0 ^-> v1 ^-> v2 ^-> v3...
echo   * First retrain: ~3-8 hours after start
echo.
echo Key Metrics:
echo   * Model Version: Automatically incremented
echo   * Training Samples: Accumulated daily
echo   * Accuracy: Improving with each retrain
echo   * P&L: Tracked in real-time
echo.
echo Monitoring:
echo   * Logs: logs/ml_scheduler/ml_scheduler_*.log
echo   * Models: models/online_learning/performance.json
echo   * Reports: reports/ml_trading/execution_*.json
echo.
echo Starting in 3 seconds...
echo.

timeout /t 3

python schedule_ml_trading.py

if errorlevel 1 (
    echo.
    echo ERROR: ML Trading System failed to start
    echo Check logs/ml_trading/ for details
    pause
)
