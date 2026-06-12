@echo off
REM Live Paper Trading Scheduler - Start for Today
REM Runs paper trading at scheduled intervals

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ================================================================================
echo   LIVE PAPER TRADING SCHEDULER - TODAY
echo ================================================================================
echo.
echo Starting live paper trading with expanded tickers...
echo Tickers: NIFTY50, BANKNIFTY, FINNIFTY, NIFTYNXT50, MIDCAPNIFTY
echo.
echo Execution Mode: DAILY at 15:30 IST
echo Logs: logs\scheduler\scheduler_*.log
echo Reports: reports\live_trading\*.json
echo.

REM Run in background using VBScript
set SCRIPT=%~dp0schedule_live_trading_today.py
python "%SCRIPT%" %*

pause
