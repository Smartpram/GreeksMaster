# Start Live Trading Scheduler - Simple Version

param(
    [string]$Mode = "daily"
)

$scriptPath = Join-Path $PSScriptRoot "schedule_live_trading_today.py"
$logDir = Join-Path $PSScriptRoot "logs\scheduler"

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

Write-Host "`n========== LIVE PAPER TRADING SCHEDULER =========`n"
Write-Host "Starting background scheduler process...`n"
Write-Host "Script: $scriptPath"
Write-Host "Mode: $Mode"
Write-Host "Logs: $logDir`n"

try {
    # Start process
    $process = Start-Process -FilePath "python" `
        -ArgumentList $scriptPath `
        -WorkingDirectory $PSScriptRoot `
        -NoNewWindow `
        -PassThru
    
    Write-Host "✅ Scheduler started successfully"
    Write-Host "Process ID: $($process.Id)`n"
    
    Write-Host "📊 The scheduler will:"
    Write-Host "   • Run daily at 15:30 IST"
    Write-Host "   • Process 5 tickers (NIFTY50, BANKNIFTY, FINNIFTY, etc.)"
    Write-Host "   • Generate ML models and trading signals"
    Write-Host "   • Save reports to reports/live_trading/`n"
    
    Write-Host "📁 Monitor at:"
    Write-Host "   Logs: logs\scheduler\"
    Write-Host "   Reports: reports\live_trading\"
    Write-Host ""
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
}
