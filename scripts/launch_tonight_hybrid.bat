@echo off
cd /d C:\Data\GreeksMaster
if not exist logs\hybrid_scheduler_monitored mkdir logs\hybrid_scheduler_monitored
python schedule_hybrid_trading_monitored.py >> logs\hybrid_scheduler_monitored\scheduled_run.log 2>&1
