@echo off
REM ============================================================================
REM Start Persistent 10-Minute Trading Scheduler
REM ============================================================================
REM This batch file starts the trading scheduler in a separate window
REM that continues running even if VS Code is closed
REM ============================================================================

cd /d "C:\Data\GreeksMaster"

echo.
echo ============================================================================
echo PERSISTENT 10-MINUTE TRADING SCHEDULER
echo ============================================================================
echo.
echo This window will:
echo   - Keep running after VS Code closes
echo   - Automatically execute trades every 10 minutes (09:15-15:25 IST)
echo   - Auto-recover from crashes
echo   - Log all activity to logs/persistent_scheduler/
echo.
echo To close: Click the X button on this window (or Ctrl+C)
echo.
echo Starting scheduler in 3 seconds...
echo.

timeout /t 3

python persistent_scheduler.py

if errorlevel 1 (
    echo.
    echo ERROR: Scheduler failed to start
    echo Check logs/persistent_scheduler/ for details
    pause
)
