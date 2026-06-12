# Setup Windows Service for 10-Minute Trading Scheduler
# This script creates a persistent Windows Service using NSSM

$serviceName = "GreeksMaster-10Min-Trading"
$pythonPath = "C:\Users\476776\AppData\Local\Programs\Python\Python312\python.exe"
$scriptPath = "C:\Data\GreeksMaster\schedule_10min_trading.py"
$workingDir = "C:\Data\GreeksMaster"
$nssmPath = "C:\nssm\win64\nssm.exe"

Write-Host "================================================" -ForegroundColor Green
Write-Host "WINDOWS SERVICE SETUP - 10-MIN TRADING SCHEDULER" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Running as Administrator: OK" -ForegroundColor Green
Write-Host ""

# Check if NSSM exists
if (-not (Test-Path $nssmPath)) {
    Write-Host "WARNING: NSSM not found at $nssmPath" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "DOWNLOAD & INSTALL NSSM:" -ForegroundColor Cyan
    Write-Host "1. Download from: https://nssm.cc/download" -ForegroundColor White
    Write-Host "2. Extract to: C:\nssm\" -ForegroundColor White
    Write-Host "3. Run this script again" -ForegroundColor White
    Write-Host ""
    
    # Try alternative path
    $altPath = "C:\Program Files\nssm\win64\nssm.exe"
    if (Test-Path $altPath) {
        $nssmPath = $altPath
        Write-Host "Found NSSM at alternative location: $nssmPath" -ForegroundColor Green
    } else {
        exit 1
    }
}

Write-Host "NSSM found: $nssmPath" -ForegroundColor Green
Write-Host ""

# Check if Python exists
if (-not (Test-Path $pythonPath)) {
    Write-Host "ERROR: Python not found at $pythonPath" -ForegroundColor Red
    exit 1
}

Write-Host "Python found: $pythonPath" -ForegroundColor Green
Write-Host ""

# Check if script exists
if (-not (Test-Path $scriptPath)) {
    Write-Host "ERROR: Script not found at $scriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "Script found: $scriptPath" -ForegroundColor Green
Write-Host ""

# Check if service already exists
$existingService = Get-Service $serviceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "Service already exists: $serviceName" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "OPTIONS:" -ForegroundColor Cyan
    Write-Host "  1. Stop and remove old service (then reinstall)" -ForegroundColor White
    Write-Host "  2. Keep existing service" -ForegroundColor White
    Write-Host ""
    $choice = Read-Host "Enter choice (1 or 2)"
    
    if ($choice -eq "1") {
        Write-Host ""
        Write-Host "Stopping service..." -ForegroundColor Yellow
        Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        
        Write-Host "Removing service..." -ForegroundColor Yellow
        & $nssmPath remove $serviceName confirm
        Start-Sleep -Seconds 2
        
        Write-Host "Old service removed" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "Keeping existing service" -ForegroundColor Green
        exit 0
    }
}

# Create new service
Write-Host "Creating new Windows Service..." -ForegroundColor Cyan
Write-Host ""

Write-Host "Service Details:" -ForegroundColor Yellow
Write-Host "  Name: $serviceName" -ForegroundColor White
Write-Host "  Python: $pythonPath" -ForegroundColor White
Write-Host "  Script: $scriptPath" -ForegroundColor White
Write-Host "  Working Dir: $workingDir" -ForegroundColor White
Write-Host ""

# Install service
Write-Host "Installing service..." -ForegroundColor Yellow
& $nssmPath install $serviceName $pythonPath $scriptPath

# Set service to run in working directory
Write-Host "Configuring service..." -ForegroundColor Yellow
& $nssmPath set $serviceName AppDirectory $workingDir

# Set service startup type to Automatic
Write-Host "Setting startup type to Automatic..." -ForegroundColor Yellow
sc.exe config $serviceName start= auto

# Set service to restart on failure
Write-Host "Configuring auto-restart on failure..." -ForegroundColor Yellow
& $nssmPath set $serviceName AppExit Default Restart
& $nssmPath set $serviceName AppRestartDelay 5000

# Set log file
$logDir = "$workingDir\logs\service"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}
$logFile = "$logDir\10min_trading_service.log"
Write-Host "Setting log file: $logFile" -ForegroundColor Yellow
& $nssmPath set $serviceName AppStdout $logFile
& $nssmPath set $serviceName AppStderr $logFile

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "SERVICE INSTALLATION COMPLETE" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Start service: Start-Service -Name '$serviceName'" -ForegroundColor White
Write-Host "  2. Check status: Get-Service -Name '$serviceName'" -ForegroundColor White
Write-Host "  3. View logs: Get-Content '$logFile' -Wait" -ForegroundColor White
Write-Host "  4. Stop service: Stop-Service -Name '$serviceName'" -ForegroundColor White
Write-Host ""

Write-Host "Service will:" -ForegroundColor Green
Write-Host "  - Start automatically on Windows startup" -ForegroundColor White
Write-Host "  - Run 38 daily trading executions (09:15-15:25 IST)" -ForegroundColor White
Write-Host "  - Restart automatically if it crashes" -ForegroundColor White
Write-Host "  - Log all activity to: $logFile" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to continue"
