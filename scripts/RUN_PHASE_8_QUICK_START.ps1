#!/usr/bin/env pwsh
# Phase 8 Quick Execution Guide (Windows PowerShell)
# Run these commands to get started with real data backtesting

Write-Host "═════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "PHASE 8: REAL DATA INTEGRATION - QUICK START" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "run_advanced_strategies_backtest.py")) {
    Write-Host "❌ Error: Not in MyBreezeApp directory" -ForegroundColor Red
    Write-Host "Please run: cd c:\Data\MyBreezeApp" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "📋 STEP 1: Understanding What's Available" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host ""
Write-Host "Running example script to show all 201 available stock codes..." -ForegroundColor White
Write-Host ""

python real_data_integration_example.py

Write-Host ""
Write-Host ""
Write-Host "📋 STEP 2: Extract Official Stock Codes" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host ""
Write-Host "Downloading and parsing official Breeze API Security Master..." -ForegroundColor White
Write-Host ""

python download_security_master.py

Write-Host ""
Write-Host ""
Write-Host "✨ STEP 3: Ready to Configure Your Backtest" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host ""
Write-Host "✅ Stock codes have been extracted!" -ForegroundColor Green
Write-Host ""
Write-Host "Next, you need to:" -ForegroundColor White
Write-Host ""
Write-Host "1. Edit: run_advanced_strategies_backtest.py" -ForegroundColor Cyan
Write-Host "2. Replace the symbols list with one from below:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   🔹 Conservative (2 symbols):" -ForegroundColor Magenta
Write-Host "      symbols = ['TCS', 'NIFTY']" -ForegroundColor White
Write-Host ""
Write-Host "   🔹 Index-Heavy (5 indices):" -ForegroundColor Magenta
Write-Host "      symbols = ['NIFTY', 'CNXBAN', 'CNXIT', 'CNXINF', 'CNXPSE']" -ForegroundColor White
Write-Host ""
Write-Host "   🔹 ETF Comparison (6 providers):" -ForegroundColor Magenta
Write-Host "      symbols = ['NIFTY', 'DSPN50', 'HDFRGE', 'ICINIF', 'KOTNIF', 'SBINIF']" -ForegroundColor White
Write-Host ""
Write-Host "   🔹 Sector Deep-Dive (10+ symbols):" -ForegroundColor Magenta
Write-Host "      symbols = ['NIFTY', 'CNXBAN', 'CNXIT', 'CNXINF',  # Indices" -ForegroundColor White
Write-Host "                 'DSPBAN', 'HDFBET', 'ICIPBE', 'SBIBAN',  # Bank ETFs" -ForegroundColor White
Write-Host "                 'DSPITF', 'HDFCIT', 'ICIPIT']            # IT ETFs" -ForegroundColor White
Write-Host ""
Write-Host "3. Save the file" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Run backtest with real data:" -ForegroundColor Cyan
Write-Host ""

$response = Read-Host "Press Enter to run backtest with REAL Breeze API data (or type 'skip' to skip)"

if ($response -ne "skip") {
    Write-Host ""
    Write-Host "🚀 Running backtest with REAL data from Breeze API..." -ForegroundColor Green
    Write-Host ""
    python run_advanced_strategies_backtest.py
}
else {
    Write-Host ""
    Write-Host "⏭️  Skipped backtest execution." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📚 Documentation Available" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "For more information, read these documents:" -ForegroundColor White
Write-Host ""
Write-Host "  📄 FINAL_STATUS_PHASE_8.md" -ForegroundColor Green
Write-Host "     Executive summary of Phase 8 achievements" -ForegroundColor Gray
Write-Host ""
Write-Host "  📄 PHASE_8_COMPLETION_SUMMARY.md" -ForegroundColor Green
Write-Host "     Detailed status and next steps" -ForegroundColor Gray
Write-Host ""
Write-Host "  📄 REAL_DATA_QUICK_REFERENCE.md" -ForegroundColor Green
Write-Host "     Implementation guide and troubleshooting" -ForegroundColor Gray
Write-Host ""
Write-Host "  📄 SECURITY_MASTER_REAL_DATA_ANALYSIS.md" -ForegroundColor Green
Write-Host "     Technical deep-dive into data extraction" -ForegroundColor Gray
Write-Host ""
Write-Host "  📄 FILE_INDEX_PHASE_8.md" -ForegroundColor Green
Write-Host "     Complete file inventory and dependencies" -ForegroundColor Gray
Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ PHASE 8: REAL DATA INTEGRATION - READY!" -ForegroundColor Green
Write-Host "═════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next: Run the 4 configuration templates above to start backtesting!" -ForegroundColor Yellow
