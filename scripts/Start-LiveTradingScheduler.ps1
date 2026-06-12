# Live Paper Trading Scheduler - Start Background Process for Today
# This script starts the scheduler in the background

param(
    [string]$Mode = "daily",
    [int]$IntervalMinutes = 60
)

$scriptPath = Join-Path $PSScriptRoot "schedule_live_trading_today.py"
$pythonExe = "python"
$logDir = Join-Path $PSScriptRoot "logs\scheduler"

# Ensure log directory exists
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Log file for this session
$logFile = Join-Path $logDir "background_start_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

Write-Host "`n╔════════════════════════════════════════════════════════════════════════╗"
Write-Host "║                                                                        ║"
Write-Host "║  LIVE PAPER TRADING SCHEDULER - BACKGROUND STARTUP                    ║"
Write-Host "║                                                                        ║"
Write-Host "╚════════════════════════════════════════════════════════════════════════╝`n"

Write-Host "📋 Configuration:"
Write-Host "   Execution Mode: $Mode"
Write-Host "   Interval (if applicable): $IntervalMinutes minutes"
Write-Host "   Script: $scriptPath"
Write-Host "   Logs: $logDir"
Write-Host ""

# Check if script exists
if (-not (Test-Path $scriptPath)) {
    Write-Host "❌ Error: Script not found at $scriptPath" -ForegroundColor Red
    exit 1
}

# Create environment file if needed
$envFile = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "⚠️  Warning: .env file not found. Make sure session token is configured." -ForegroundColor Yellow
}

Write-Host "✅ Starting background scheduler process..."
Write-Host ""

# Start the process in background
try {
    # For daily mode, schedule for 3:30 PM
    if ($Mode -eq "daily") {
        Write-Host "⏰ Scheduled to run daily at 15:30 IST"
        Write-Host "📍 Next execution will be calculated based on current time"
    }
    
    # Start as background job with PS with no window
    $process = Start-Process -FilePath $pythonExe `
        -ArgumentList @($scriptPath) `
        -WorkingDirectory (Split-Path $scriptPath) `
        -NoNewWindow `
        -PassThru `
        -RedirectStandardOutput (Join-Path $logDir "output_$(Get-Date -Format 'yyyyMMdd_HHmmss').log") `
        -RedirectStandardError (Join-Path $logDir "errors_$(Get-Date -Format 'yyyyMMdd_HHmmss').log")
    
    Write-Host "✅ Process started successfully"
    Write-Host "   Process ID: $($process.Id)"
    Write-Host "   Name: $($process.Name)"
    Write-Host ""
    
    Write-Host "📊 Monitoring:"
    Write-Host "   • Check logs at: $logDir"
    Write-Host "   • Check reports at: $(Join-Path $PSScriptRoot 'reports\live_trading')"
    Write-Host "   • View daily execution summary: $logFile"
    Write-Host ""
    
    # Display next execution estimate
    $now = Get-Date
    $scheduledTime = $now.Date.AddHours(15).AddMinutes(30)
    if ($scheduledTime -le $now) {
        $scheduledTime = $scheduledTime.AddDays(1)
    }
    $timeUntilExecution = $scheduledTime - $now
    
    Write-Host "⏳ Next Execution:"
    Write-Host "   Scheduled for: $($scheduledTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Host "   Time until execution: $($timeUntilExecution.Hours)h $($timeUntilExecution.Minutes)m $($timeUntilExecution.Seconds)s"
    Write-Host ""
    
    Write-Host "🎯 Quick Commands:"
    Write-Host "   • View latest log:"
    Write-Host "     Get-Content $(Join-Path $logDir 'scheduler_*.log') -Tail 50 -Wait"
    Write-Host "   • Stop scheduler:"
    Write-Host "     Stop-Process -Id $($process.Id)"
    Write-Host "   • Check if running:"
    Write-Host "     Get-Process | Where-Object {`$_.Id -eq $($process.Id)}"
    Write-Host ""
    
    Write-Host "💾 Data Location:"
    Write-Host "   Logs: $logDir"
    Write-Host "   Reports: $(Join-Path $PSScriptRoot 'reports\live_trading')"
    Write-Host ""
    
    Write-Host "✨ System is now scheduled for live trading!" -ForegroundColor Green
    Write-Host "   The scheduler will automatically execute paper trading at configured times."
    Write-Host ""
    
} catch {
    Write-Host "❌ Error starting process: $_" -ForegroundColor Red
    exit 1
}
