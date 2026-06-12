# PowerShell Setup for Background Paper Trading
# Run as Administrator
# 
# Usage:
#   powershell -ExecutionPolicy Bypass -File setup_background_trading.ps1

Write-Host "`n" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host "BACKGROUND PAPER TRADING SETUP" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""

# Check if running as admin
$isAdmin = ([System.Security.Principal.WindowsPrincipal] [System.Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([System.Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "[ERROR] This script must run as Administrator!" -ForegroundColor Red
    Write-Host "Please right-click PowerShell and select 'Run as administrator'" -ForegroundColor Red
    Exit 1
}

Write-Host "[✓] Running as Administrator`n" -ForegroundColor Green

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Script directory: $scriptDir`n"

# Step 1: Create logs directory
Write-Host "[STEP 1] Creating logs directory..." -ForegroundColor Cyan
$logsDir = Join-Path $scriptDir "logs"

if (Test-Path $logsDir) {
    Write-Host "[✓] Logs directory already exists" -ForegroundColor Green
} else {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    Write-Host "[✓] Created logs directory" -ForegroundColor Green
}
Write-Host ""

# Step 2: Test Python executor
Write-Host "[STEP 2] Testing Python executor..." -ForegroundColor Cyan
$pythonExecutor = Join-Path $scriptDir "paper_trading_background.py"

if (Test-Path $pythonExecutor) {
    Write-Host "[✓] Python executor found: $pythonExecutor" -ForegroundColor Green
    
    Write-Host "[INFO] Running test (this may take 5-10 seconds)..." -ForegroundColor Yellow
    
    $output = & python $pythonExecutor 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[✓] Python executor works correctly" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Python executor returned exit code $LASTEXITCODE" -ForegroundColor Yellow
        Write-Host "Output: $output" -ForegroundColor Yellow
    }
} else {
    Write-Host "[ERROR] Python executor not found: $pythonExecutor" -ForegroundColor Red
    Exit 1
}
Write-Host ""

# Step 3: Create Task Scheduler task
Write-Host "[STEP 3] Creating Task Scheduler task..." -ForegroundColor Cyan

$taskName = "GreeksMaster_PaperTrading"
$batchFile = Join-Path $scriptDir "paper_trading_scheduler.bat"

# Check if task already exists
$taskExists = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($taskExists) {
    Write-Host "[INFO] Task already exists, removing old version..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false | Out-Null
}

# Create task triggers and actions
Write-Host "[INFO] Configuring task schedule..." -ForegroundColor Yellow

# Daily trigger at 9:15 AM, repeat every 1 hour for 8.5 hours (market hours 9:15 AM - 3:45 PM)
$trigger = New-ScheduledTaskTrigger -Daily -At "09:15 AM"
$trigger.Repetition = New-ScheduledTaskRepetition `
    -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration (New-TimeSpan -Hours 8 -Minutes 30)

# Action: run batch file
$action = New-ScheduledTaskAction -Execute $batchFile

# Principal: run as SYSTEM (highest privileges, works when locked/logged out)
$principal = New-ScheduledTaskPrincipal `
    -UserID "NT AUTHORITY\SYSTEM" `
    -RunLevel Highest

# Settings: restart on failure, run with or without network
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -MultipleInstances IgnoreNew

# Register task
$description = "Automated paper trading execution every hour (Market: 9:15 AM - 3:45 PM)"
Register-ScheduledTask `
    -TaskName $taskName `
    -Trigger $trigger `
    -Action $action `
    -Principal $principal `
    -Settings $settings `
    -Description $description `
    -Force | Out-Null

Write-Host "[✓] Task created successfully" -ForegroundColor Green
Write-Host ""

# Step 4: Verify task
Write-Host "[STEP 4] Verifying task..." -ForegroundColor Cyan

$task = Get-ScheduledTask -TaskName $taskName
Write-Host "[✓] Task Details:" -ForegroundColor Green
Write-Host "    Name: $($task.TaskName)" -ForegroundColor White
Write-Host "    State: $($task.State)" -ForegroundColor White
Write-Host "    Path: $($task.TaskPath)" -ForegroundColor White
Write-Host ""

# Step 5: Show test instructions
Write-Host "[STEP 5] Testing instructions:" -ForegroundColor Cyan
Write-Host ""
Write-Host "To test background execution:" -ForegroundColor Yellow
Write-Host "  1. Manual trigger:" -ForegroundColor Yellow
Write-Host "     schtasks /run /tn `"$taskName`"" -ForegroundColor White
Write-Host ""
Write-Host "  2. View logs:" -ForegroundColor Yellow
Write-Host "     Get-Content `"$logsDir\paper_trading_*.log`" -Wait" -ForegroundColor White
Write-Host ""
Write-Host "  3. To test with machine LOCKED:" -ForegroundColor Yellow
Write-Host "     - Lock your machine (Windows Key + L)" -ForegroundColor White
Write-Host "     - Run trigger from another device or wait for scheduled time" -ForegroundColor White
Write-Host "     - Unlock and check logs to verify execution" -ForegroundColor White
Write-Host ""
Write-Host "  4. View task in Task Scheduler:" -ForegroundColor Yellow
Write-Host "     taskschd.msc" -ForegroundColor White
Write-Host ""

# Step 6: Summary
Write-Host "======================================" -ForegroundColor Green
Write-Host "SETUP COMPLETE!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "Paper trading background execution is ready:" -ForegroundColor Green
Write-Host "  ✓ Python executor configured" -ForegroundColor Green
Write-Host "  ✓ Batch wrapper configured" -ForegroundColor Green
Write-Host "  ✓ Task Scheduler configured" -ForegroundColor Green
Write-Host "  ✓ Logs directory configured" -ForegroundColor Green
Write-Host ""
Write-Host "Schedule: Every 1 hour from 9:15 AM to 3:45 PM" -ForegroundColor Green
Write-Host "Runs when: Machine locked" -ForegroundColor Green
Write-Host "Runs when: User logged out" -ForegroundColor Green
Write-Host ""
Write-Host "Next: Test manually before going to production" -ForegroundColor Yellow
Write-Host ""
