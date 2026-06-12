# Background Paper Trading - Master Checklist

Keep this handy for quick reference and daily operations.

---

## 🚀 SETUP (Do This First)

```
[ ] 1. Open PowerShell as Administrator
[ ] 2. Navigate to project: cd c:\Data\GreeksMaster
[ ] 3. Run setup: powershell -ExecutionPolicy Bypass -File setup_background_trading.ps1
[ ] 4. Wait for completion (should take 2-3 minutes)
[ ] 5. See "Task registered successfully" message
```

---

## ✅ TESTING (Do This After Setup)

```
[ ] 1. Run test suite: python test_background_execution.py
[ ] 2. All tests should PASS
[ ] 3. Manual trigger: schtasks /run /tn "GreeksMaster_PaperTrading"
[ ] 4. Monitor logs: Get-Content logs\paper_trading_*.log -Wait
[ ] 5. See execution messages and trades in logs
```

---

## 🔒 LOCKED MACHINE TEST (Critical - Do This)

```
[ ] 1. Open 2 PowerShell windows as Administrator
[ ] 2. Terminal 1: Get-Content logs\paper_trading_*.log -Wait
[ ] 3. Terminal 2: schtasks /run /tn "GreeksMaster_PaperTrading"
[ ] 4. Wait 5 seconds (see execution in Terminal 1)
[ ] 5. Lock machine: Windows Key + L
[ ] 6. Wait 10 seconds
[ ] 7. Unlock machine and check Terminal 1
[ ] 8. Should show execution happened despite locked machine
[ ] ✅ IF YES = Ready for production
```

---

## 📊 DAILY OPERATIONS

### Morning (Before Market Open)

```
[ ] Verify task exists: Get-ScheduledTask -TaskName "GreeksMaster_PaperTrading"
[ ] Should show State: Ready
[ ] Check logs from yesterday: Get-ChildItem logs\*.log -Tail 1
[ ] Review any errors from previous day
[ ] Confirm all trades were recorded
```

### During Market Hours

```
[ ] Hourly: Check logs for new executions
[ ] Look for: [CYCLE START] and [CYCLE END] messages
[ ] Count trades recorded each hour
[ ] Monitor for any ERROR messages
[ ] Verify P&L tracking (if trading)
```

### Evening (After Market Close)

```
[ ] Final log check: Get-Content logs\paper_trading_*.log -Tail 50
[ ] Verify no errors accumulated
[ ] Note total trades for the day
[ ] Review execution times (should be hourly)
[ ] Check resource usage and performance
```

---

## 🧪 WEEKLY MAINTENANCE

```
[ ] Monday: Archive previous week's logs
[ ] Wednesday: Review performance metrics
[ ] Friday: Summary report of all executions
[ ] Check for any patterns or issues
[ ] Verify task still enabled: Enable-ScheduledTask -TaskName "GreeksMaster_PaperTrading"
```

---

## 🚨 TROUBLESHOOTING QUICK FIXES

### Task Not Running?

```
[ ] Check if task exists: Get-ScheduledTask -TaskName "GreeksMaster_PaperTrading"
[ ] If not found: Re-run setup: powershell -ExecutionPolicy Bypass -File setup_background_trading.ps1
[ ] If found but disabled: Enable-ScheduledTask -TaskName "GreeksMaster_PaperTrading"
```

### No Logs Being Created?

```
[ ] Check logs directory exists: Test-Path c:\Data\GreeksMaster\logs
[ ] If not: mkdir c:\Data\GreeksMaster\logs
[ ] Test executor directly: python paper_trading_background.py
[ ] Check for Python errors in console output
```

### Python Executor Crashes?

```
[ ] Run test directly: python paper_trading_background.py
[ ] Check console output for errors
[ ] Verify models exist: Test-Path app\ml_models\*
[ ] Verify dependencies: pip list | grep xgboost
[ ] Reinstall if needed: pip install -r requirements.txt
```

### Locked Machine Test Failed?

```
[ ] Verify principal is SYSTEM
[ ] Re-run setup as Administrator
[ ] Check Windows Event Log for task errors
[ ] Ensure logs directory has write permissions
```

---

## 📈 MONITORING COMMANDS (Keep These Handy)

### View Status
```powershell
Get-ScheduledTask -TaskName "GreeksMaster_PaperTrading" | Get-ScheduledTaskInfo
```

### View Latest Logs
```powershell
Get-Content logs\paper_trading_*.log -Tail 30
```

### Monitor Live
```powershell
Get-Content logs\paper_trading_*.log -Wait
```

### Count Today's Executions
```powershell
(Get-Content logs\paper_trading_*.log | Select-String "CYCLE START").Count
```

### Find Errors
```powershell
Select-String -Path logs\paper_trading_*.log -Pattern "ERROR"
```

### Check Next Run Time
```powershell
Get-ScheduledTask -TaskName "GreeksMaster_PaperTrading" | Select NextRunTime
```

### Manual Trigger
```powershell
schtasks /run /tn "GreeksMaster_PaperTrading"
```

### Disable Task
```powershell
Disable-ScheduledTask -TaskName "GreeksMaster_PaperTrading"
```

### Enable Task
```powershell
Enable-ScheduledTask -TaskName "GreeksMaster_PaperTrading"
```

### Open Task Scheduler UI
```powershell
taskschd.msc
```

---

## ⚙️ CONFIGURATION CHANGES

### Change Frequency (Currently: Every 1 Hour)

To change to every 30 minutes:
```powershell
$trigger = New-ScheduledTaskTrigger -Daily -At "09:15 AM"
$trigger.Repetition = New-ScheduledTaskRepetition `
    -RepetitionInterval (New-TimeSpan -Minutes 30) `
    -RepetitionDuration (New-TimeSpan -Hours 8 -Minutes 30)
Set-ScheduledTask -TaskName "GreeksMaster_PaperTrading" -Trigger $trigger
```

### Change Start Time (Currently: 9:15 AM)

To change to 10:00 AM:
```powershell
$trigger = New-ScheduledTaskTrigger -Daily -At "10:00 AM"
$trigger.Repetition = New-ScheduledTaskRepetition `
    -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration (New-TimeSpan -Hours 7 -Minutes 45)
Set-ScheduledTask -TaskName "GreeksMaster_PaperTrading" -Trigger $trigger
```

---

## 📋 QUICK REFERENCE TABLE

| Task | Command | Time |
|------|---------|------|
| Initial Setup | `powershell -ExecutionPolicy Bypass -File setup_background_trading.ps1` | 3 min |
| Test Everything | `python test_background_execution.py` | 2 min |
| View Status | `Get-ScheduledTask -TaskName "GreeksMaster_PaperTrading"` | 10 sec |
| Check Logs | `Get-Content logs\paper_trading_*.log -Wait` | Continuous |
| Trigger Manually | `schtasks /run /tn "GreeksMaster_PaperTrading"` | 5 sec |
| Count Trades | `(Get-Content logs\paper_trading_*.log \| Select-String "TRADE").Count` | 5 sec |
| Find Errors | `Select-String -Path logs\*.log -Pattern "ERROR"` | 5 sec |
| Disable Task | `Disable-ScheduledTask -TaskName "GreeksMaster_PaperTrading"` | 3 sec |
| Enable Task | `Enable-ScheduledTask -TaskName "GreeksMaster_PaperTrading"` | 3 sec |
| Open UI | `taskschd.msc` | Instant |

---

## 🎯 SUCCESS INDICATORS

### All Working Well When:
- ✅ Task shows "Ready" state
- ✅ Logs created hourly (8-9 per day)
- ✅ Each log contains [CYCLE START] and [CYCLE END]
- ✅ Trades recorded each cycle
- ✅ No ERROR messages
- ✅ Execution time < 30 seconds
- ✅ Machine lock doesn't stop execution

### Needs Attention When:
- ⚠️ Task shows "Disabled" state
- ⚠️ Logs not created on schedule
- ⚠️ Error messages in logs
- ⚠️ Trades not recorded
- ⚠️ Execution time > 60 seconds
- ⚠️ Machine lock stops execution

---

## 📚 DOCUMENTATION QUICK LINKS

| Need | File |
|------|------|
| Quick answers | `BACKGROUND_TRADING_QUICKSTART.md` |
| Setup help | `COMPLETE_BACKGROUND_IMPLEMENTATION.md` |
| Technical details | `BACKGROUND_PAPER_TRADING_SETUP.md` |
| Validation steps | `BACKGROUND_TRADING_DEPLOYMENT_CHECKLIST.md` |
| Package overview | `BACKGROUND_TRADING_IMPLEMENTATION_PACKAGE.md` |
| Summary & status | `BACKGROUND_EXECUTION_COMPLETE_SUMMARY.md` |
| Deployment score | `DEPLOYMENT_READINESS_MATRIX.md` |

---

## 🚨 EMERGENCY PROCEDURES

### Task Stuck / Not Running

1. Disable: `Disable-ScheduledTask -TaskName "GreeksMaster_PaperTrading"`
2. Wait 10 seconds
3. Enable: `Enable-ScheduledTask -TaskName "GreeksMaster_PaperTrading"`
4. Verify: `Get-ScheduledTask -TaskName "GreeksMaster_PaperTrading"`

### Complete Reset

1. Remove task: `Unregister-ScheduledTask -TaskName "GreeksMaster_PaperTrading" -Confirm:$false`
2. Create logs: `mkdir c:\Data\GreeksMaster\logs -Force`
3. Re-setup: `powershell -ExecutionPolicy Bypass -File setup_background_trading.ps1`
4. Re-test: `python test_background_execution.py`

### Python Dependency Issues

1. Check: `pip list | grep -E "xgboost|scikit-learn|pandas"`
2. Update: `pip install --upgrade pip`
3. Reinstall: `pip install -r requirements.txt`
4. Test: `python paper_trading_background.py`

---

## 📞 SUPPORT ESCALATION

### Level 1: Self-Service
- Check this checklist first
- Read `BACKGROUND_TRADING_QUICKSTART.md`
- Run test suite: `python test_background_execution.py`

### Level 2: Documentation
- Read `BACKGROUND_PAPER_TRADING_SETUP.md`
- Check `COMPLETE_BACKGROUND_IMPLEMENTATION.md`
- Review `BACKGROUND_TRADING_DEPLOYMENT_CHECKLIST.md`

### Level 3: Manual Intervention
- Disable task, wait, re-enable
- Clear logs and re-run setup
- Check Windows Event Log for OS errors

---

## ✅ PRODUCTION CHECKLIST

### Daily Before Market Open
- [ ] Verify task is enabled
- [ ] Review yesterday's logs
- [ ] Check for any errors
- [ ] Confirm all trades recorded

### During Market Hours
- [ ] Monitor logs hourly
- [ ] Check for new executions
- [ ] Verify no errors
- [ ] Track trades volume

### Daily After Market Close
- [ ] Final log review
- [ ] Error summary
- [ ] Daily metrics
- [ ] Prepare next day

### Weekly
- [ ] Full performance review
- [ ] Archive old logs
- [ ] Check system resources
- [ ] Plan any changes

---

## 🎉 YOU'RE READY!

Print this checklist and keep handy for:
- Daily operations
- Quick troubleshooting
- Performance monitoring
- Emergency procedures

**All systems ready for 24/7 automated trading!** ✅

---

**Last Updated:** June 10, 2026  
**Status:** ✅ PRODUCTION ACTIVE  
**Version:** 1.0
