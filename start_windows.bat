@echo off
echo Starting MyBreezeApp...
cd /d "%~dp0"
set FLASK_APP=app.main:app
set FLASK_ENV=development
python -m flask run --host=0.0.0.0 --port=5000
pause
