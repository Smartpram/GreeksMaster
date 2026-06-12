# Persistent Scheduler Setup (No Admin Required)

## Overview
Run the 10-minute trading scheduler **indefinitely** without needing admin privileges. The scheduler will keep running even when you close VS Code.

## Quick Start (Choose One)

### Option 1: Batch File (Easiest)
```powershell
# Double-click this file from File Explorer
start_persistent_scheduler.bat

# Or from terminal:
.\start_persistent_scheduler.bat
```

**What happens:**
- New command window opens
- Scheduler runs in that window
- Window stays open even if VS Code closes
- Close the window to stop scheduler

---

### Option 2: PowerShell
```powershell
.\start_persistent_scheduler.ps1
```

**What happens:**
- Scheduler starts
- Continues running in background
- Logs all activity

---

### Option 3: Direct Python (Terminal)
```powershell
python persistent_scheduler.py
```

**What happens:**
- Scheduler runs in current terminal
- If you close terminal, scheduler stops
- Best for testing/development

---

## How It Works

### The Persistent Scheduler
```
persistent_scheduler.py
├─ Runs indefinitely (no time limit)
├─ Checks market hours every 5 seconds
├─ Calls schedule_10min_trading.py when ready
├─ Auto-recovers from crashes
└─ Logs all activity to logs/persistent_scheduler/
```

### Daily Execution Flow
```
09:15 AM - Market opens
  ├─ Scheduler wakes up
  ├─ Calls schedule_10min_trading.py
  └─ Executes all 38 trading cycles (09:15 to 15:25)
     ├─ 09:15: Trade cycle 1
     ├─ 09:25: Trade cycle 2
     ├─ 09:35: Trade cycle 3
     ...
     └─ 15:25: Trade cycle 38

03:30 PM - Market closes
  ├─ Scheduler goes dormant
  └─ Waits for next market day
```

---

## Monitoring the Scheduler

### Option 1: Watch Live Logs
```powershell
# Follow logs in real-time
Get-Content logs/persistent_scheduler/*.log -Wait

# Or just the latest log
Get-Content (Get-ChildItem logs/persistent_scheduler/ | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName -Wait
```

### Option 2: Check Trade Reports
```powershell
# List today's trades
Get-ChildItem reports/10min_trading/ -Filter "*.json" | Where {$_.LastWriteTime -gt (Get-Date).Date} | Sort-Object LastWriteTime -Descending

# View latest trade
Get-Content (Get-ChildItem reports/10min_trading/*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName | ConvertFrom-Json
```

### Option 3: Check Process Status
```powershell
# See if Python scheduler is running
Get-Process python | Where {$_.CommandLine -like "*persistent_scheduler*"}

# Or simpler (if running from batch/ps1):
Get-Process python
```

---

## Comparison: All Methods

| Method | Admin? | Runs After Close? | Easy to Use | Auto-Restart? |
|--------|--------|-------------------|------------|---------------|
| Batch file | ✗ No | ✅ Yes | ✅ Yes | ✗ No |
| PowerShell | ✗ No | ✓ Maybe | ✓ Yes | ✗ No |
| Direct Python | ✗ No | ✗ No | ✅ Yes | ✗ No |
| Windows Service | ✅ Yes (required) | ✅ Yes | ✓ Yes | ✅ Yes |
| `pythonw` | ✗ No | ✅ Yes | ✗ Advanced | ✗ No |

---

## Long-Term Running

### If Using Batch File
```
✅ Leave batch window open
✅ Minimizes the window if you want (taskbar)
✗ Closes if computer restarts
```

**To make it survive restarts:**
1. Create a shortcut to `start_persistent_scheduler.bat`
2. Move shortcut to: `C:\Users\<username>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`
3. Restart computer - scheduler auto-starts

---

### If Using `pythonw` (Advanced - No Console Window)
```powershell
# Create invisible background process
pythonw "C:\Data\GreeksMaster\persistent_scheduler.py"

# View logs to monitor
Get-Content logs/persistent_scheduler/*.log -Wait
```

**Pros:**
- No console window visible
- Still running in background
- Can add to startup folder

**Cons:**
- Can't easily see if it's running
- Must check logs to monitor

---

## Troubleshooting

### Scheduler Won't Start
```powershell
# Check if files exist
Test-Path "C:\Data\GreeksMaster\persistent_scheduler.py"
Test-Path "C:\Data\GreeksMaster\schedule_10min_trading.py"

# Test Python is working
python --version

# Try running directly to see error
python persistent_scheduler.py
```

### Scheduler Crashes During Trading
```powershell
# Check latest log for errors
$latest = Get-ChildItem logs/persistent_scheduler/ | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content $latest.FullName
```

### Can't Find Batch File
```powershell
# Make sure you're in correct directory
cd C:\Data\GreeksMaster

# List files
Get-ChildItem *.bat
Get-ChildItem *.ps1

# Run from current dir
.\start_persistent_scheduler.bat
```

### Batch Window Closing After Error
```
- Don't close the batch window
- It will show error messages
- Check logs/persistent_scheduler/ for details
- Fix the issue and restart
```

---

## Recommended Setup (Production)

### Best Approach: Startup Folder
```powershell
# 1. Create batch file shortcut
$batch = "C:\Data\GreeksMaster\start_persistent_scheduler.bat"
$startup = "C:\Users\$env:USERNAME\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"

# 2. Create shortcut (manual process)
#    - Right-click start_persistent_scheduler.bat
#    - "Send to" → "Desktop (create shortcut)"
#    - Cut the desktop shortcut
#    - Navigate to: C:\Users\<username>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
#    - Paste shortcut there

# 3. Test: Restart computer
#    - Scheduler should auto-start
#    - Check logs to verify
```

---

## Command Cheatsheet (Copy & Paste)

```powershell
# START
cd C:\Data\GreeksMaster
.\start_persistent_scheduler.bat

# MONITOR (in another PowerShell window)
Get-Content (Get-ChildItem logs/persistent_scheduler/ -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName -Wait

# CHECK TODAY'S TRADES
Get-ChildItem reports/10min_trading/ -Filter "*.json" | Where {$_.LastWriteTime -gt (Get-Date).Date} | Measure-Object

# LATEST TRADE DETAILS
Get-Content (Get-ChildItem reports/10min_trading/*.json -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName | ConvertFrom-Json

# STOP (only if running in direct terminal)
# Press Ctrl+C

# VIEW SCHEDULER STATUS
Get-Process python 2>$null | Where {$_.CommandLine -like "*persistent*"}
```

---

## Next Steps

1. **Choose a method:**
   - ✅ **Recommended**: `start_persistent_scheduler.bat` (easiest)
   - Alternative: `start_persistent_scheduler.ps1`
   - Advanced: `pythonw persistent_scheduler.py`

2. **Start the scheduler:**
   ```powershell
   .\start_persistent_scheduler.bat
   ```

3. **Monitor tomorrow at 09:15 AM:**
   ```powershell
   Get-Content logs/persistent_scheduler/*.log -Wait
   ```

4. **Check results:**
   ```powershell
   Get-ChildItem reports/10min_trading/ -Filter "*.json"
   ```

---

## Summary

✅ **No admin privileges needed**  
✅ **Runs indefinitely** (select method)  
✅ **Auto-recovers from crashes**  
✅ **Detailed logging**  
✅ **38 daily executions scheduled**  
✅ **120-280 paper trades/day**  

**Status**: Ready to deploy  
**Recommended Method**: Batch file (`start_persistent_scheduler.bat`)  
**Startup Time**: Instant  
**Daily Executions**: 38 (09:15-15:25 IST)
