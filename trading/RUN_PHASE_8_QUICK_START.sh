#!/bin/bash
# Phase 8 Quick Execution Guide
# Run these commands to get started with real data backtesting

echo "═════════════════════════════════════════════════════════════"
echo "PHASE 8: REAL DATA INTEGRATION - QUICK START"
echo "═════════════════════════════════════════════════════════════"
echo ""

# Check if we're in the right directory
if [ ! -f "run_advanced_strategies_backtest.py" ]; then
    echo "❌ Error: Not in MyBreezeApp directory"
    echo "Please run: cd c:\\Data\\MyBreezeApp"
    exit 1
fi

echo ""
echo "📋 STEP 1: Understanding What's Available"
echo "─────────────────────────────────────────────────────────────"
echo ""
echo "Running example script to show all 201 available stock codes..."
echo ""
python real_data_integration_example.py
echo ""

echo ""
echo "📋 STEP 2: Extract Official Stock Codes"
echo "─────────────────────────────────────────────────────────────"
echo ""
echo "Downloading and parsing official Breeze API Security Master..."
echo ""
python download_security_master.py
echo ""

echo ""
echo "✨ STEP 3: Ready to Configure Your Backtest"
echo "─────────────────────────────────────────────────────────────"
echo ""
echo "✅ Stock codes have been extracted!"
echo ""
echo "Next, you need to:"
echo ""
echo "1. Edit: run_advanced_strategies_backtest.py"
echo "2. Replace the symbols list with one from below:"
echo ""
echo "   🔹 Conservative (2 symbols):"
echo "      symbols = ['TCS', 'NIFTY']"
echo ""
echo "   🔹 Index-Heavy (5 indices):"
echo "      symbols = ['NIFTY', 'CNXBAN', 'CNXIT', 'CNXINF', 'CNXPSE']"
echo ""
echo "   🔹 ETF Comparison (6 providers):"
echo "      symbols = ['NIFTY', 'DSPN50', 'HDFRGE', 'ICINIF', 'KOTNIF', 'SBINIF']"
echo ""
echo "   🔹 Sector Deep-Dive (10+ symbols):"
echo "      symbols = ['NIFTY', 'CNXBAN', 'CNXIT', 'CNXINF',  # Indices"
echo "                 'DSPBAN', 'HDFBET', 'ICIPBE', 'SBIBAN',  # Bank ETFs"
echo "                 'DSPITF', 'HDFCIT', 'ICIPIT']            # IT ETFs"
echo ""
echo "3. Save the file"
echo ""
echo "4. Run backtest with real data:"
echo ""

read -p "   Press Enter to run backtest (or Ctrl+C to cancel)..." -t 10 || true

if [ $? -eq 0 ]; then
    echo ""
    echo "🚀 Running backtest with REAL data from Breeze API..."
    echo ""
    python run_advanced_strategies_backtest.py
else
    echo ""
    echo "⏭️  Skipped backtest execution."
    echo ""
fi

echo ""
echo "═════════════════════════════════════════════════════════════"
echo "📚 Documentation Available"
echo "═════════════════════════════════════════════════════════════"
echo ""
echo "For more information, read these documents:"
echo ""
echo "  📄 FINAL_STATUS_PHASE_8.md"
echo "     Executive summary of Phase 8 achievements"
echo ""
echo "  📄 PHASE_8_COMPLETION_SUMMARY.md"
echo "     Detailed status and next steps"
echo ""
echo "  📄 REAL_DATA_QUICK_REFERENCE.md"
echo "     Implementation guide and troubleshooting"
echo ""
echo "  📄 SECURITY_MASTER_REAL_DATA_ANALYSIS.md"
echo "     Technical deep-dive into data extraction"
echo ""
echo "  📄 FILE_INDEX_PHASE_8.md"
echo "     Complete file inventory and dependencies"
echo ""
echo "═════════════════════════════════════════════════════════════"
echo "✅ PHASE 8: REAL DATA INTEGRATION - READY!"
echo "═════════════════════════════════════════════════════════════"
