# MyBreezeApp Repository Structure

**Repository Status**: ✅ Organized & Clean  
**Last Updated**: June 1, 2026  
**Files Organized**: 173 + 77 markdown files  
**Root Files**: 13 (down from 350+)

---

## 📁 Directory Overview

### Root Level (13 files)
```
├── README.md                          # Main project documentation
├── run.py                             # Primary application entry point
├── setup.py                           # Package setup configuration
├── requirements.txt                   # Python dependencies
├── Dockerfile                         # Docker container config
├── docker-compose.yml                 # Multi-container orchestration
├── .env                               # Environment variables (local)
├── .env.example                       # Environment template
├── .gitignore                         # Git ignore patterns
└── CLEANUP_*.md (4 files)             # Repository cleanup guides
```

### Core Directories

#### 🤖 `ai_ml/` - AI & Machine Learning
Machine learning models, sentiment analysis, signal generation
```
ai_sentiment_analyzer.py
ai_integration_guide.py
ENHANCED_SIGNAL_IMPLEMENTATION_GUIDE.py
setup_sentiment_analysis.py
... (12 files)
```

#### 📊 `backtest/` - Backtesting Engine
All backtest scripts and analysis tools
```
backtest.py                           # Core backtesting engine
backtest_profit_booking_breeze.py      # Profit booking strategy backtest
run_backtest.py                        # Execute backtest
enhanced_backtest_with_breeze.py       # Enhanced backtesting
integrated_advanced_backtest.py        # Advanced backtest suite
... (17 files)
```

#### 💹 `trading/` - Live Trading Systems
Paper trading, live trading, monitoring
```
run_live_trading_system.py             # Live trading entry point
run_paper_trader.py                    # Paper trading simulation
monitor.py                             # Real-time monitoring
multi_model_trading_system.py          # Multi-model trading system
... (8 files)
```

#### 🧪 `tests/scripts/` - Test Suite
40+ comprehensive test scripts
```
test_breeze_api.py                     # Breeze API tests
test_login.py                          # Authentication tests
test_market_time_filter.py             # Market time filter tests
INTEGRATED_STRATEGY_TEST.py            # Strategy integration tests
test_paper_trading.py                  # Paper trading tests
... (40 files)
```

#### 📈 `data/` - Data & Configuration
```
backtest_results/
├── backtest_profit_booking_breeze_20260601_094947.json  (latest)
├── enhanced_backtest_*.json
├── integrated_advanced_backtest_20260601_*.json
└── ... (30+ backtest result files)

config/
├── NSEScripMaster.txt                 # NSE script master
├── BSEScripMaster.txt                 # BSE script master
├── SecurityMaster.zip                 # Security master data
├── network_config.json                # Network configuration
├── mybreeze.db                        # Local database
└── safety_state.json

reports/
├── production_readiness_report.json
├── POSITION_TRACKING_REPORT.json
└── POSITION_TRACKING_DETAILED.csv
```

#### 📚 `docs/` - Documentation
```
README.md                              # Feature-based comprehensive guide

DESIGN_DECISIONS/
├── TRAILING_STOPS_DESIGN_RULES.md    # Trailing stop design rules

INTEGRATIONS/
├── INTEGRATION_GUIDE.md               # System integration guide

archive/
├── 131 historical markdown files      # All legacy documentation

guides/
├── START_HERE.txt                     # Quick start guide
├── STARTUP_GUIDE.txt                  # Setup guide
├── QUICK_START_README.txt             # Quick reference

indexes/
├── 00_DOCUMENTATION_INDEX.py          # Documentation index
├── DELIVERABLES_MANIFEST.py           # Deliverables manifest

summaries/
├── COMPLETION_SUMMARY.py              # Project completion summary
├── implementation_summary.py           # Implementation details

cleanup_reports/
└── CLEANUP_*.json                     # Cleanup execution reports
```

#### 📄 `test_results/` - Test Outputs
CSV and JSON test result files
```
COMPREHENSIVE_BACKTEST_RESULTS.json
INTEGRATED_TEST_RESULTS.csv
strategy_comparison_results.csv
... (12 files)
```

#### 🔍 `analysis/` - Analysis Tools
Data analysis and diagnostic scripts
```
create_optimization_report.py
create_production_solution.py
network_analysis.py
```

#### ⚙️ `setup/` - Configuration & Setup
Initialization and integration scripts
```
get_session_token.py
check_api_structure.py
download_security_master.py
INTEGRATION_CHECKLIST.py
POSITION_TRACKING_INTEGRATION.py
... (15 files)
```

#### 🚀 `scripts/` - Deployment Scripts
Shell and batch scripts for deployment
```
start_unix.sh
start_windows.bat
deploy.sh
RUN_PHASE_8_QUICK_START.ps1
```

#### 📋 `logs/` - Application Logs
```
backtest_output.txt
project_structure.txt
SESSION_COMPLETION_SUMMARY.txt
SYSTEM_READY_SUMMARY.txt
strategy_refinement.log
```

#### 📦 `other/` - Miscellaneous
Utility scripts and reference materials
```
aggressive_cleanup.py
cleanup_repo.py
final_cleanup.py
CODE_SNIPPETS_REFERENCE.py
SYSTEM_ARCHITECTURE_DIAGRAMS.py
```

#### 📱 `app/` - Main Application
```
strategies/
├── profit_booking_manager.py          # Profit booking engine (FIXED)
├── unified_profit_booking.py          # Unified strategy selection
├── regime_monitor.py                  # Market regime monitoring
└── ... (14 files)

services/
├── cash_flow_manager.py
├── live_position_tracker.py
├── signal_executor.py
└── ... (8 files)

backtesting/
├── strategy_wrapper.py

mocks/
├── mock_dependencies.py
```

---

## 🔑 Key Files by Purpose

### Data Analysis & Backtesting
- **Primary Backtest**: `data/backtest_results/backtest_profit_booking_breeze_20260601_094947.json`
- **Latest Results**: Fixed calculations (max_drawdown, avg_pnl_pct, sharpe_ratio)
- **Backtest Engine**: `backtest/backtest_profit_booking_breeze.py`

### Strategy Implementation
- **Profit Booking**: `app/strategies/profit_booking_manager.py` (Bug fixes applied ✅)
- **Unified Strategy**: `app/strategies/unified_profit_booking.py` (Conditional regime detection)
- **Market Monitor**: `app/strategies/regime_monitor.py` (Continuous market analysis)

### Production Deployment
- **Live Trading**: `trading/run_live_trading_system.py`
- **Paper Trading**: `trading/run_paper_trader.py`
- **Docker**: `Dockerfile` + `docker-compose.yml`

### Documentation
- **Main README**: `README.md` (Feature-based comprehensive guide)
- **Design Rules**: `docs/DESIGN_DECISIONS/TRAILING_STOPS_DESIGN_RULES.md`
- **Integration**: `docs/INTEGRATIONS/INTEGRATION_GUIDE.md`
- **Quick Start**: `docs/guides/START_HERE.txt`

---

## 📊 Statistics

| Category | Count |
|----------|-------|
| Python Scripts | 250+ |
| Test Scripts | 40+ |
| Test Result Files | 20+ |
| JSON Backtest Results | 30+ |
| Markdown Files (archived) | 131 |
| Root Configuration Files | 13 |
| Directories | 25 |
| **Total Organized** | **350+** |

---

## ✅ Cleanup Summary

### Before Cleanup
- **Root Files**: 350+ (chaotic, mixed)
- **Markdown Files**: 134+ scattered in root
- **Backtest Results**: Mixed with scripts
- **Organization**: None

### After Cleanup
- **Root Files**: 13 (essential only)
- **Markdown Files**: 131 archived + 5 active
- **Backtest Results**: Organized in `data/backtest_results/`
- **Organization**: Feature-based directory structure

### Moved Files
- 173 Python/config files organized into 13 functional directories
- 77 markdown files archived in `docs/archive/`
- 20 JSON/data files organized into data/ subdirectories

---

## 🎯 Usage

### Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python run.py

# Run backtest
python backtest/run_backtest.py

# Run paper trading
python trading/run_paper_trader.py
```

### Development
```bash
# Run tests
pytest tests/scripts/

# Run specific test
pytest tests/scripts/test_breeze_api.py

# Run backtest with real data
python backtest/run_backtest_real_data.py
```

### Docker
```bash
# Build and run with Docker
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## 🔄 Git History

Latest commit:
```
refactor: comprehensive repository cleanup - organize 173+ files into logical directories
- Moved 77 markdown files to docs/archive/
- Organized 173+ root files into 13 functional directories
- Clean root directory with only 13 essential files
```

---

## 📝 Notes

- All historical markdown files preserved in `docs/archive/`
- Calculation fixes applied to profit booking (3 bugs corrected)
- Unified strategy with conditional logic implemented
- Design rules documented and evidence-based
- Production safeguards and monitoring system in place
- Repository is ready for production deployment

---

**Last Organized**: June 1, 2026, 10:32 AM  
**By**: GitHub Copilot Cleanup System
