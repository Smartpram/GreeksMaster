@echo off
REM Paper Trading Background Scheduler
REM This batch file is run by Windows Task Scheduler
REM It executes the paper trading Python script and logs output

echo. >> "%~dp0logs\scheduler.log"
echo ======================================================================== >> "%~dp0logs\scheduler.log"
echo Paper Trading Cycle Started at %date% %time% >> "%~dp0logs\scheduler.log"
echo ======================================================================== >> "%~dp0logs\scheduler.log"

REM Change to script directory
cd /d "%~dp0"

REM Run Python script (all output goes to log file)
python paper_trading_background.py >> "%~dp0logs\scheduler.log" 2>&1

REM Capture exit code
set EXIT_CODE=%ERRORLEVEL%

echo. >> "%~dp0logs\scheduler.log"
echo Paper Trading Cycle Ended at %date% %time% (Exit Code: %EXIT_CODE%) >> "%~dp0logs\scheduler.log"
echo ======================================================================== >> "%~dp0logs\scheduler.log"
echo. >> "%~dp0logs\scheduler.log"

exit /b %EXIT_CODE%
