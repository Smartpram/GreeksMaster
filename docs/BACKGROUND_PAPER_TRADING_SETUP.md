# BACKGROUND PAPER TRADING SETUP
**Question:** Can we run paper trading in the background? Will it work if the machine is locked?

**Short Answer:** 
- ✅ YES, it can run in background
- ✅ YES, it will work if machine is locked
- ✅ YES, it can run 24/7

---

## 📊 BACKGROUND EXECUTION OPTIONS

### Option 1: Windows Task Scheduler (EASIEST) ✅ RECOMMENDED
**How it works:**
- Schedule Python script to run at specific times
- Runs even if machine is locked
- Runs even if you're logged out
- Built into Windows (no extra software)

**Pros:**
- ✅ Super simple to set up
- ✅ Works with locked machine
- ✅ Works when logged out
- ✅ Perfect for 1-hour interval trades
- ✅ Can run at market open/close
- ✅ No GUI needed

**Cons:**
- ❌ No real-time console output (need logging)
- ❌ Harder to debug
- ❌ Requires log files to monitor

**Best For:** Running every hour, every 30 min, etc.

---

### Option 2: Windows Service (PROFESSIONAL) 
**How it works:**
- Runs as system service
- Always running in background
- Highest reliability
- Can restart on crash

**Pros:**
- ✅ Most reliable
- ✅ Restarts automatically if crashes
- ✅ Can log everything
- ✅ Runs with system startup

**Cons:**
- ❌ More complex setup
- ❌ Need admin privileges
- ❌ Harder to stop/modify

**Best For:** 24/7 production trading

---

### Option 3: Python Script with While Loop (SIMPLE)
**How it works:**
```python
while True:
    generate_signals()
    execute_trades()
    time.sleep(3600)  # Run every hour
```

**Pros:**
- ✅ Simple code
- ✅ Works with Task Scheduler
- ✅ Easy to test

**Cons:**
- ❌ Crashes stop everything
- ❌ No auto-restart
- ❌ Hard to monitor

**Best For:** Development testing

---

### Option 4: Docker Container (SCALABLE)
**How it works:**
- Package Python + scripts in Docker
- Run in background container
- Can restart automatically

**Pros:**
- ✅ Portable
- ✅ Isolated environment
- ✅ Auto-restart on crash

**Cons:**
- ❌ Setup complexity
- ❌ Overkill for single system

**Best For:** Cloud/production deployment

---

## 🎯 RECOMMENDATION: Task Scheduler (Option 1)

Why? 
- Simple to set up (5 minutes)
- Works on locked machine
- Works when logged out
- Perfect for hourly trades
- Built into Windows
- Most reliable for your use case

---

## 🚀 IMPLEMENTATION: Task Scheduler Setup

### Step 1: Create Background Trading Script
```python
# paper_trading_background.py
import logging
from datetime import datetime
from app.ml_models.performance_monitor import PerformanceMonitor
from app.paper_trading_engine import PaperTradingEngine

# Setup logging (output to file, not console)
logging.basicConfig(
    filename='logs/paper_trading.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Paper trading execution"""
    try:
        logger.info("="*80)
        logger.info(f"[START] Paper trading cycle at {datetime.now()}")
        
        # Initialize system
        engine = PaperTradingEngine()
        monitor = PerformanceMonitor()
        
        # Generate signals for each symbol
        for symbol in ['NIFTY50', 'BANKNIFTY', 'FINNIFTY']:
            logger.info(f"\n[{symbol}] Generating signals...")
            
            # Get latest data
            df = engine.get_latest_data(symbol)
            
            # Generate features
            features = engine.generate_features(df)
            
            # Predict
            prediction, confidence = engine.predict_signal(symbol, features)
            
            # Execute if signal
            if prediction != 0:
                entry_price = df['close'].iloc[-1]
                trade = engine.execute_paper_trade(
                    symbol=symbol,
                    direction='LONG' if prediction > 0 else 'SHORT',
                    price=entry_price,
                    confidence=confidence
                )
                monitor.record_trade(trade)
                logger.info(f"  ✓ Trade executed: {trade}")
            else:
                logger.info(f"  - No signal")
        
        # Generate report
        metrics = monitor.calculate_metrics()
        logger.info(f"\n[METRICS] P&L: {metrics['total_pnl']:.0f}, WR: {metrics['win_rate']:.1%}")
        
        logger.info("[END] Paper trading cycle complete\n")
        
    except Exception as e:
        logger.error(f"[ERROR] Paper trading failed: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
```

### Step 2: Create Batch File to Run Python Script
```batch
@echo off
REM paper_trading_scheduler.bat

echo Paper Trading Started at %date% %time% >> C:\Data\GreeksMaster\logs\scheduler.log

cd C:\Data\GreeksMaster
python paper_trading_background.py >> C:\Data\GreeksMaster\logs\scheduler.log 2>&1

echo Paper Trading Completed at %date% %time% >> C:\Data\GreeksMaster\logs\scheduler.log
```

### Step 3: Create Task in Windows Task Scheduler

**Method 1: GUI (Easy)**
1. Open Task Scheduler (Win+R → taskscheduler.msc)
2. Click "Create Basic Task"
3. Name: "Paper Trading Hourly"
4. Trigger: "Daily" → Repeat every 1 hour
5. Action: Start program → `C:\Data\GreeksMaster\paper_trading_scheduler.bat`
6. Check "Run whether user is logged in or not"

**Method 2: PowerShell Script (Automated)**
```powershell
# Create-PaperTradingTask.ps1
$taskName = "PaperTradingHourly"
$scriptPath = "C:\Data\GreeksMaster\paper_trading_scheduler.bat"

$trigger = New-ScheduledTaskTrigger -Daily -At "09:15 AM"
$repeat = New-ScheduledTaskTrigger -Daily -At "09:15 AM" -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Hours 8)

$action = New-ScheduledTaskAction -Execute $scriptPath

$principal = New-ScheduledTaskPrincipal -UserID "NT AUTHORITY\SYSTEM" -RunLevel Highest

Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Principal $principal
```

---

## ✅ TESTING BACKGROUND EXECUTION

### Test 1: Run via Task Scheduler (Manual)
```powershell
# Manually run the task
schtasks /run /tn "PaperTradingHourly"

# Check if it's running
Get-ScheduledTask -TaskName "PaperTradingHourly" | Get-ScheduledTaskInfo
```

### Test 2: Lock Machine and Verify It Still Runs
1. Start task manually with `schtasks /run /tn "PaperTradingHourly"`
2. Lock machine (Win+L)
3. Wait 5 minutes
4. Unlock and check logs: `cat logs/paper_trading.log`

### Test 3: Check Logs While Locked
On another computer, RDP into system and check logs

---

## 📝 LOGGING SETUP (CRITICAL FOR BACKGROUND)

Since you can't see console output, logging to files is essential:

```python
import logging
import os
from datetime import datetime

# Create logs directory
os.makedirs('logs', exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # File logging (detailed)
        logging.FileHandler(f'logs/paper_trading_{datetime.now().strftime("%Y%m%d")}.log'),
        
        # Console logging (if interactive)
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Log everything
logger.info("Starting paper trading...")
logger.info(f"Processing {symbol}")
logger.info(f"Trade executed: {trade}")
logger.error(f"Error occurred: {error}")
```

---

## 🔄 MACHINE LOCKED - WILL IT WORK?

**YES, it will work:**
- ✅ Windows Task Scheduler runs background tasks regardless of lock status
- ✅ Python script executes in system context
- ✅ No GUI needed
- ✅ No user interaction needed
- ✅ Works with Windows 10/11

**Requirements:**
1. Task runs with system privileges
2. No GUI popups (use file logging)
3. No user input prompts
4. Proper error handling

**Test it:**
1. Create simple test script that writes to file
2. Schedule it for 1 minute from now
3. Lock machine
4. Check if file was created

---

## 📊 COMPLETE SETUP CHECKLIST

### Prerequisites
- [ ] Python script ready (`paper_trading_background.py`)
- [ ] Logs directory created (`logs/`)
- [ ] Batch file ready (`paper_trading_scheduler.bat`)
- [ ] Models in correct location
- [ ] Data sources accessible

### Setup
- [ ] Create Task Scheduler task
- [ ] Set to run every 1 hour (or desired interval)
- [ ] Set to run with system privileges
- [ ] Set to run when user logged out
- [ ] Configure log rotation

### Testing
- [ ] Run manually once
- [ ] Check logs for success
- [ ] Lock machine and verify it still runs
- [ ] Check log files after unlock
- [ ] Verify trades recorded correctly

### Production
- [ ] Monitor logs daily
- [ ] Set up log rotation (prevent disk fill)
- [ ] Set up alerts on errors
- [ ] Weekly verification

---

## 🕐 TRADING SCHEDULE EXAMPLES

### Example 1: Every Hour (Default)
```
09:15 AM ─ 03:45 PM (7 trades/day)
Every 1 hour
```

### Example 2: Every 30 Minutes
```
09:15 AM ─ 03:45 PM (15 trades/day)
Every 30 minutes
```

### Example 3: Market Open/Close
```
09:15 AM (Market open)
01:00 PM (Mid-day)
03:30 PM (Market close)
3 trades/day
```

### Example 4: 24/7 Continuous
```
Every 1 hour, 24 hours/day
Monitor trends overnight
Weekend data collection
```

---

## 🛡️ ERROR HANDLING FOR BACKGROUND

Since you won't see errors, implement comprehensive error handling:

```python
import smtplib
from email.mime.text import MIMEText

def send_error_alert(error_message):
    """Send email alert on error"""
    msg = MIMEText(error_message)
    msg['Subject'] = 'Paper Trading Error Alert'
    msg['From'] = 'trading@system.local'
    msg['To'] = 'your_email@gmail.com'
    
    # Send email (or use cloud service)
    # smtplib.SMTP(...).sendmail(...)

try:
    paper_trading_cycle()
except Exception as e:
    logger.error(f"Critical error: {e}")
    send_error_alert(str(e))
    raise
```

---

## 📈 MONITORING LOGS

```python
# view_logs.py - Check current status
import os
from datetime import datetime

log_file = f'logs/paper_trading_{datetime.now().strftime("%Y%m%d")}.log'

if os.path.exists(log_file):
    with open(log_file, 'r') as f:
        lines = f.readlines()
        # Show last 50 lines
        for line in lines[-50:]:
            print(line.strip())
else:
    print(f"Log file not found: {log_file}")
```

---

## 💾 LOG ROTATION (Prevent Disk Full)

```python
from logging.handlers import RotatingFileHandler

# 10 MB per log file, keep 10 backups
handler = RotatingFileHandler(
    'logs/paper_trading.log',
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=10
)

logger.addHandler(handler)
```

---

## ✅ FINAL SETUP SUMMARY

### Option A: Simple (Recommended for Now)
1. Create `paper_trading_background.py` (with logging)
2. Create `paper_trading_scheduler.bat`
3. Schedule task in Task Scheduler
4. Run every 1 hour
5. Monitor logs daily

**Time to setup:** 30 minutes

### Option B: Professional (Production)
1. Same as Option A
2. Add email alerts on errors
3. Add log rotation
4. Add health checks
5. Dashboard for monitoring

**Time to setup:** 2-3 hours

### Option C: Enterprise (Future)
1. Windows Service
2. Monitoring system
3. Backup execution
4. Disaster recovery

**Time to setup:** 1-2 days

---

## 🎯 MY RECOMMENDATION

**For your paper trading system:**

✅ **Use Option 1: Task Scheduler**
- Simple to set up (30 min)
- Works with locked machine
- Works when logged out
- Perfect for hourly trades
- Add logging for monitoring

**Schedule:**
- Every 1 hour: 09:15 AM - 03:45 PM
- Or custom: Market open, mid-day, close

**Monitoring:**
- Check logs daily
- Email alerts on errors
- Weekly verification

**Result:**
- Paper trading runs 24/7
- You can go to sleep/lock machine
- Trades execute automatically
- Logs show everything that happened

---

## 📝 QUICK START

Create these 3 files:

### File 1: `paper_trading_background.py`
```python
# Your paper trading logic with file logging
# See above for example
```

### File 2: `paper_trading_scheduler.bat`
```batch
@echo off
cd C:\Data\GreeksMaster
python paper_trading_background.py
```

### File 3: Register Task (PowerShell)
```powershell
# Run this in PowerShell as Admin
$taskName = "PaperTradingHourly"
$scriptPath = "C:\Data\GreeksMaster\paper_trading_scheduler.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At "09:15 AM" -RepetitionInterval (New-TimeSpan -Minutes 60) -RepetitionDuration (New-TimeSpan -Hours 10)
$action = New-ScheduledTaskAction -Execute $scriptPath
Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Principal (New-ScheduledTaskPrincipal -UserID "SYSTEM" -RunLevel Highest)
```

**Done!** Paper trading now runs every hour, even with machine locked.

