# Background Paper Trading - Quick Start Guide

## Overview

Run paper trading automatically in the background, even when your machine is locked or you're logged out.

**What you get:**
- ✓ Automated execution every 1 hour during market hours (9:15 AM - 3:45 PM)
- ✓ Works when machine is locked
- ✓ Works when you're logged out
- ✓ Automatic logging and error tracking
- ✓ System privileges (highest execution level)

---

## 🚀 Quick Start (5 minutes)

### Option 1: PowerShell Setup (Recommended)

**Step 1:** Open PowerShell as Administrator
```powershell
Right-click PowerShell → Run as administrator
```

**Step 2:** Run setup script
```powershell
cd c:\Data\GreeksMaster
powershell -ExecutionPolicy Bypass -File setup_background_trading.ps1
```

**Step 3:** Wait for completion (shows task created)

---

### Option 2: Python Setup

**Step 1:** Open PowerShell as Administrator

**Step 2:** Run Python setup
```powershell
cd c:\Data\GreeksMaster
python setup_task_scheduler.py
```

**Step 3:** Create logs directory
```powershell
mkdir logs
```

---

## ✅ Testing

### Test 1: Verify Components Work

```powershell
# Run full test suite
python test_background_execution.py
```

**Expected output:**
- ✓ Environment validated
- ✓ Python executor runs
- ✓ Batch wrapper runs
- ✓ Logs created

### Test 2: Manual Trigger

```powershell
# Trigger the task immediately
schtasks /run /tn "GreeksMaster_PaperTrading"

# Check logs (live tail)
Get-Content "logs\paper_trading_*.log" -Wait

# Press Ctrl+C to stop monitoring
```

### Test 3: Test with Locked Machine

**Step 1:** In PowerShell, start monitoring logs
```powershell
Get-Content "logs\paper_trading_*.log" -Wait
```

**Step 2:** Open another PowerShell (as Admin) and trigger task
```powershell
schtasks /run /tn "GreeksMaster_PaperTrading"
```

**Step 3:** Press Windows Key + L to LOCK your machine

**Step 4:** Wait 10 seconds, then unlock

**Step 5:** Check logs - should show execution even though machine was locked

---

## 📊 Monitoring

### View Logs

```powershell
# Show most recent log
Get-Item logs\paper_trading_*.log | Sort-Object LastWriteTime | Select -Last 1 | ForEach-Object { Get-Content $_ | Tail -30 }

# Live tail logs (Ctrl+C to stop)
Get-Content "logs\paper_trading_*.log" -Wait
```

### View Task Status

```powershell
# Check if task exists
Get-ScheduledTask -TaskName "GreeksMaster_PaperTrading"

# Show next run time
Get-ScheduledTask -TaskName "GreeksMaster_PaperTrading" | Select TaskName, State, NextRunTime

# View full task details
Get-ScheduledTask -TaskName "GreeksMaster_PaperTrading" | Get-ScheduledTaskInfo
```

### View Task Scheduler UI

```powershell
taskschd.msc
```

Then navigate to: `Task Scheduler Library → GreeksMaster_PaperTrading`

---

## 🔧 Configuration

### Change Schedule Frequency

**Current:** Every 1 hour from 9:15 AM - 3:45 PM

**To modify:**

```powershell
# Open Task Scheduler
taskschd.msc

# Right-click GreeksMaster_PaperTrading → Properties
# Edit triggers to change frequency or times
```

Or via PowerShell:

```powershell
# Example: Change to every 30 minutes
$trigger = New-ScheduledTaskTrigger -Daily -At "09:15 AM"
$trigger.Repetition = New-ScheduledTaskRepetition `
    -RepetitionInterval (New-TimeSpan -Minutes 30) `
    -RepetitionDuration (New-TimeSpan -Hours 8 -Minutes 30)

Set-ScheduledTask -TaskName "GreeksMaster_PaperTrading" -Trigger $trigger
```

### Change Start Time

```powershell
# Example: Start at 10:00 AM instead of 9:15 AM
$trigger = New-ScheduledTaskTrigger -Daily -At "10:00 AM"
$trigger.Repetition = New-ScheduledTaskRepetition `
    -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration (New-TimeSpan -Hours 7 -Minutes 45)

Set-ScheduledTask -TaskName "GreeksMaster_PaperTrading" -Trigger $trigger
```

---

## 🚨 Troubleshooting

### Task Not Running?

**Check 1:** Verify task exists
```powershell
Get-ScheduledTask -TaskName "GreeksMaster_PaperTrading"
```

**Check 2:** Verify task is enabled
```powershell
# Enable task
Enable-ScheduledTask -TaskName "GreeksMaster_PaperTrading"
```

**Check 3:** Check last run result
```powershell
Get-ScheduledTask -TaskName "GreeksMaster_PaperTrading" | Get-ScheduledTaskInfo | Select TaskName, LastRunTime, LastTaskResult
```

### Logs Not Created?

**Check:** Logs directory exists
```powershell
Test-Path c:\Data\GreeksMaster\logs
```

**Create if missing:**
```powershell
mkdir c:\Data\GreeksMaster\logs
```

### Python Executor Fails?

**Test directly:**
```powershell
cd c:\Data\GreeksMaster
python paper_trading_background.py
```

**Check for errors:**
- Look at console output
- Check logs/paper_trading_*.log files
- Verify all required models and data files exist

### Batch File Fails?

**Test directly:**
```powershell
cd c:\Data\GreeksMaster
.\paper_trading_scheduler.bat
```

**Check:**
- Verify Python is installed and in PATH
- Verify batch file has correct path to Python script
- Check logs directory permissions

---

## 📋 Files Overview

| File | Purpose | Status |
|------|---------|--------|
| `paper_trading_background.py` | Main executor (file-based logging) | ✓ Ready |
| `paper_trading_scheduler.bat` | Batch wrapper (Task Scheduler integration) | ✓ Ready |
| `setup_task_scheduler.py` | Python setup script | ✓ Ready |
| `setup_background_trading.ps1` | PowerShell setup script | ✓ Ready |
| `test_background_execution.py` | Test suite | ✓ Ready |
| `logs/` | Log files (created automatically) | ✓ Ready |

---

## 📈 Advanced

### View Recent Execution History

```powershell
# Show last 10 executions
Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" `
  -FilterXPath "*[System[(EventID=201 or EventID=202 or EventID=203 or EventID=206) and (Task/Provider[@Name='Microsoft-Windows-TaskScheduler'] or Task/Provider[@Name='TaskScheduler'])]]" `
  | Where-Object { $_.Properties[0].Value -like "*GreeksMaster*" } `
  | Select-Object -First 10 `
  | Format-Table TimeCreated, Id, Message
```

### Export Task Configuration

```powershell
Export-ScheduledTask -TaskName "GreeksMaster_PaperTrading" `
  | Out-File "GreeksMaster_PaperTrading_backup.xml"
```

### Import from Backup

```powershell
Register-ScheduledTask -Xml (Get-Content "GreeksMaster_PaperTrading_backup.xml" | Out-String) `
  -TaskName "GreeksMaster_PaperTrading" -Force
```

---

## 🔒 Security Notes

- **Runs as:** SYSTEM (highest Windows privileges)
- **When:** Every hour during market hours, even if machine locked
- **Access:** Only files in `c:\Data\GreeksMaster\` directory
- **Logging:** All activity logged to `logs/` directory
- **Network:** Runs with or without network connectivity

---

## ⚠️ Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Access denied when running setup | Run PowerShell as Administrator |
| Task created but not running | Check task status: `Get-ScheduledTaskInfo` |
| Logs not appearing | Create `logs` directory, check permissions |
| Python not found | Install Python or add to PATH |
| Batch file fails | Verify Python path in batch file matches your installation |
| Machine lock test fails | Ensure "NT AUTHORITY\SYSTEM" principal is configured |

---

## 📞 Support

If issues arise:

1. **Check logs:** `Get-Content logs\paper_trading_*.log`
2. **Test manually:** `python paper_trading_background.py`
3. **Verify files:** `Test-Path c:\Data\GreeksMaster\{all required files}`
4. **Check Task Scheduler:** `taskschd.msc`

---

## ✨ Next Steps

1. ✓ Setup task (PowerShell or Python script)
2. ✓ Test manually (test_background_execution.py)
3. ✓ Test with machine locked
4. ✓ Monitor logs daily
5. ✓ Ready for production deployment!

**Enjoy 24/7 automated paper trading!** 🚀
