# Windows Service Setup - 10-Minute Trading Scheduler

## Overview
Deploy the 10-minute trading scheduler as a **Windows Service** so it runs 24/7, even when you close VS Code or log off.

## Prerequisites

### 1. Download NSSM (Non-Sucking Service Manager)
- **URL**: https://nssm.cc/download
- **Download**: `nssm-2.24-101-g897c7ad.zip` (or latest)
- **Extract to**: `C:\nssm\`

Your folder should look like:
```
C:\nssm\
├── win32\
│   └── nssm.exe
├── win64\
│   └── nssm.exe
├── src\
└── README.txt
```

### 2. Run as Administrator
**IMPORTANT**: PowerShell script MUST run as Administrator

## Installation Steps

### Step 1: Open PowerShell as Administrator
```powershell
# Right-click PowerShell → Run as Administrator
```

### Step 2: Navigate to Project
```powershell
cd C:\Data\GreeksMaster
```

### Step 3: Run Setup Script
```powershell
.\setup_trading_service.ps1
```

This will:
- ✅ Create Windows Service named `GreeksMaster-10Min-Trading`
- ✅ Configure to run `schedule_10min_trading.py`
- ✅ Set auto-startup on Windows boot
- ✅ Configure auto-restart on crash
- ✅ Setup logging to `logs/service/10min_trading_service.log`

### Step 4: Start Service
```powershell
Start-Service -Name "GreeksMaster-10Min-Trading"
```

### Step 5: Verify Running
```powershell
Get-Service -Name "GreeksMaster-10Min-Trading"
```

Expected output:
```
Status   Name                DisplayName
------   ----                -----------
Running  GreeksMaster-10M... GreeksMaster-10Min-Trading
```

## Service Management Commands

### Check Status
```powershell
Get-Service -Name "GreeksMaster-10Min-Trading"
```

### View Live Logs
```powershell
Get-Content "C:\Data\GreeksMaster\logs\service\10min_trading_service.log" -Wait
```

### Stop Service
```powershell
Stop-Service -Name "GreeksMaster-10Min-Trading"
```

### Restart Service
```powershell
Restart-Service -Name "GreeksMaster-10Min-Trading"
```

### Remove Service (if needed)
```powershell
# First stop it
Stop-Service -Name "GreeksMaster-10Min-Trading" -Force

# Then remove
nssm remove "GreeksMaster-10Min-Trading" confirm
```

## What Happens

### When Service is Running ✅
- **Automatically starts** when Windows boots
- **Runs in background** even if you log off
- **Runs continuously** even if VS Code is closed
- **Executes 38 trades** every 10 minutes (09:15-15:25 IST)
- **Logs all activity** to `logs/service/10min_trading_service.log`
- **Auto-restarts** if it crashes (5-second delay)

### Daily Schedule
```
09:15 AM - First execution (38 trades expected)
09:25 AM - 2nd execution
09:35 AM - 3rd execution
...
15:15 PM - 37th execution
15:25 PM - Final execution (38th)
```

**Total: 38 executions/day = 120-280 paper trades**

## Troubleshooting

### Service Won't Start
```powershell
# Check error in Event Viewer
Get-WinEvent -LogName "System" -MaxEvents 10 | Where {$_.ProviderName -like "*nssm*"}

# Or check service log
Get-Content "C:\Data\GreeksMaster\logs\service\10min_trading_service.log" -Tail 50
```

### Python Import Errors
```powershell
# Verify Python
C:\Users\476776\AppData\Local\Programs\Python\Python312\python.exe --version

# Check packages
C:\Users\476776\AppData\Local\Programs\Python\Python312\python.exe -m pip list
```

### Service Crashes During Trading
```powershell
# Check scheduler logs (more detailed than service log)
Get-ChildItem "C:\Data\GreeksMaster\logs\10min_scheduler\" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

## Comparison: Service vs Manual Run

| Feature | Manual (`schedule_10min_trading.py`) | Windows Service |
|---------|--------------------------------------|-----------------|
| Runs when VS Code closed | ✗ No | ✅ Yes |
| Runs when logged off | ✗ No | ✅ Yes |
| Starts on boot | ✗ No | ✅ Yes |
| Restarts on crash | ✗ No | ✅ Yes |
| Suitable for production | ✗ No | ✅ Yes |
| Easy to manage | ✗ Manual | ✅ Services panel |

## Next Steps

1. **Download NSSM** from https://nssm.cc/download
2. **Extract to C:\nssm\**
3. **Run setup script**: `.\setup_trading_service.ps1` (as Administrator)
4. **Start service**: `Start-Service -Name "GreeksMaster-10Min-Trading"`
5. **Monitor tomorrow** starting at 09:15 AM IST
6. **Check logs** throughout the day

## Key Monitoring Commands (Bookmark These)

```powershell
# Status check
Get-Service -Name "GreeksMaster-10Min-Trading"

# Live logs (real-time)
Get-Content "C:\Data\GreeksMaster\logs\service\10min_trading_service.log" -Wait

# Latest 50 lines
Get-Content "C:\Data\GreeksMaster\logs\service\10min_trading_service.log" -Tail 50

# Today's trades
Get-ChildItem "C:\Data\GreeksMaster\reports\10min_trading\" -Filter "*.json" | Where {$_.LastWriteTime -gt (Get-Date).Date}

# Service restart history
Get-WinEvent -LogName "System" | Where {$_.ProviderName -like "*nssm*"} | Select-Object -First 10
```

## Summary

✅ **After setup:**
- Service runs 24/7
- Auto-restarts on failure
- Starts on Windows boot
- Produces 38 daily executions
- Generates 120-280 paper trades/day
- Fully automated, no user intervention needed

---

**Status**: Ready to deploy  
**Setup Time**: 5 minutes  
**Daily Executions**: 38 (09:15-15:25 IST)  
**Expected Trades/Day**: 120-280
