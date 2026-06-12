# Start Persistent 10-Minute Trading Scheduler (No Admin Required)
# This script starts the scheduler in a new terminal window
# The scheduler continues running even if VS Code closes

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "PERSISTENT 10-MINUTE TRADING SCHEDULER" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""

# Get project root
$projectRoot = "C:\Data\GreeksMaster"
$schedulerScript = "$projectRoot\persistent_scheduler.py"

# Verify script exists
if (-not (Test-Path $schedulerScript)) {
    Write-Host "ERROR: $schedulerScript not found" -ForegroundColor Red
    exit 1
}

Write-Host "Starting persistent scheduler..." -ForegroundColor Cyan
Write-Host ""
Write-Host "This scheduler will:" -ForegroundColor Yellow
Write-Host "  - Run continuously in the background" -ForegroundColor White
Write-Host "  - Keep running even when VS Code closes" -ForegroundColor White
Write-Host "  - Execute 38 trades daily (09:15-15:25 IST)" -ForegroundColor White
Write-Host "  - Auto-recover from crashes" -ForegroundColor White
Write-Host "  - Log activity to: logs/persistent_scheduler/" -ForegroundColor White
Write-Host ""

Write-Host "Monitor Commands:" -ForegroundColor Cyan
Write-Host "  Get-Content logs/persistent_scheduler/*.log -Wait" -ForegroundColor White
Write-Host "  Get-Content reports/10min_trading/*.json | ConvertFrom-Json" -ForegroundColor White
Write-Host ""

Write-Host "To stop: Press Ctrl+C in the new window" -ForegroundColor Yellow
Write-Host ""

Write-Host "Starting in 3 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start in new terminal (PowerShell 7+) or separate process
try {
    # Try PowerShell Core first (Windows Terminal)
    $pwshPath = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
    if ($pwshPath) {
        Write-Host "Starting with PowerShell Core..." -ForegroundColor Green
        & pwsh -NoExit -Command "cd '$projectRoot'; python persistent_scheduler.py"
    } else {
        # Fall back to python directly (will open in same window)
        Write-Host "Starting with Python..." -ForegroundColor Green
        cd $projectRoot
        python persistent_scheduler.py
    }
} catch {
    Write-Host "Error starting scheduler: $_" -ForegroundColor Red
    exit 1
}
