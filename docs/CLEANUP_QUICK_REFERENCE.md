# 🧹 Repository Cleanup - Quick Reference

**Date**: June 1, 2026  
**Status**: Ready to Execute  
**Files Affected**: 153 markdown files

---

## 🎯 Quick Commands

### Preview Changes (Dry Run)
```bash
python cleanup_repo.py --dry-run
```

### Execute Cleanup
```bash
python cleanup_repo.py --execute
```

### Cleanup Verification
```bash
# View new structure
tree -L 2 docs/
ls -la *.md
cat CLEANUP_REPORT_*.json
```

---

## 📊 What Will Happen

| Action | Count | Result |
|--------|-------|--------|
| Archive | 77 | Move to `docs/archive/` |
| Move | 5 | Organize into `docs/DESIGN_DECISIONS`, `INTEGRATIONS`, `PRODUCTION`, `DEVELOPMENT` |
| Delete | 76 | Remove duplicate/redundant files |
| Replace | 1 | README.md with comprehensive version |
| **Total** | **159** | **Files Processed** |

---

## 📁 New Repository Structure

```
MyBreezeApp/
├── README.md                          ← NEW (comprehensive, replaces 5 variants)
├── .env.example
├── requirements.txt
├── docker-compose.yml
├── LICENSE
├── .github/copilot-instructions.md
│
├── backtest_profit_booking_breeze.py  (latest backtest script)
├── backtest_profit_booking_breeze_20260601_094947.json (latest results)
│
├── docs/
│   ├── DESIGN_DECISIONS/
│   │   └── TRAILING_STOPS_DESIGN_RULES.md ← Why trailing is conditional
│   │
│   ├── INTEGRATIONS/
│   │   └── INTEGRATION_GUIDE.md
│   │
│   ├── PRODUCTION/
│   │   ├── PRODUCTION_VALIDATOR_GUIDE.md
│   │   └── REGIME_MONITOR_GUIDE.md
│   │
│   ├── DEVELOPMENT/
│   │   └── TEST_VALIDATION_GUIDE.md
│   │
│   └── archive/                       ← ALL historical documentation
│       ├── PHASE_1_*.md
│       ├── ADVANCED_*.md
│       ├── BACKTEST_*.md
│       ├── AI_*.md
│       └── ... (77 files)
│
├── app/
├── tests/
└── deployment/
```

---

## ⚠️ Safety Features

✅ **Dry Run First**: Preview all changes before executing  
✅ **Archived Not Deleted**: Old files preserved in `docs/archive/`  
✅ **README Backup**: Current README backed up as `README_OLD_BACKUP_*.md`  
✅ **JSON Report**: Cleanup report generated with all actions  
✅ **Git Safe**: All changes recoverable from git history  

---

## 🔄 Before & After

### BEFORE
```
134+ markdown files scattered in root directory
├── README.md (outdated)
├── README_OLD.md (duplicate)
├── README_EXPANDED_RESULTS.md (duplicate)
├── README_PHASE_9.md (historical)
├── README_PROFIT_BOOKING_COMPLETE.md (duplicate)
├── PHASE_1_*.md (14 files)
├── PHASE_2_*.md (14 files)
├── ADVANCED_*.md (12 files)
├── BACKTEST_*.md (13 files)
├── AI_*.md (9 files)
├── DELIVERY_*.md (11 files)
├── ... (100+ more)
```

### AFTER
```
Clean, organized structure
├── README.md (NEW - single comprehensive entry point)
├── docs/
│   ├── DESIGN_DECISIONS/
│   ├── INTEGRATIONS/
│   ├── PRODUCTION/
│   ├── DEVELOPMENT/
│   └── archive/ (all old files preserved)
├── app/
├── tests/
└── deployment/
```

---

## 📋 Manual Cleanup (If Script Fails)

If the Python script encounters issues, execute manually:

```bash
# Step 1: Create directories
mkdir -p docs/archive
mkdir -p docs/DESIGN_DECISIONS
mkdir -p docs/INTEGRATIONS
mkdir -p docs/PRODUCTION
mkdir -p docs/DEVELOPMENT

# Step 2: Archive PHASE_* files (77 total)
mv PHASE_*.md docs/archive/
mv ADVANCED_*.md docs/archive/
mv BACKTEST_*.md docs/archive/
mv DELIVERY_*.md docs/archive/
mv FINAL_*.md docs/archive/
mv AI_*.md docs/archive/
mv SENTIMENT_*.md docs/archive/
mv STATUS_*.md docs/archive/
mv CASH_FLOW_*.md docs/archive/

# Step 3: Move important files
mv TRAILING_STOPS_DESIGN_RULES.md docs/DESIGN_DECISIONS/
mv INTEGRATION_GUIDE.md docs/INTEGRATIONS/
mv PRODUCTION_VALIDATOR_GUIDE.md docs/PRODUCTION/
mv REGIME_MONITOR_GUIDE.md docs/PRODUCTION/
mv TEST_VALIDATION_GUIDE.md docs/DEVELOPMENT/

# Step 4: Delete redundant files (76 total)
rm README_OLD.md README_EXPANDED_RESULTS.md README_PHASE_9.md
rm README_PHASE1_REMEDIATION.md README_PROFIT_BOOKING_COMPLETE.md
rm DOCUMENTATION_INDEX.md INDEX.md QUICK_REFERENCE.md
rm QUICK_COMMAND_REFERENCE.md PROJECT_SUMMARY.md
# ... (see CLEANUP_PLAN.md for full list)

# Step 5: Replace README
rm README.md
mv README_NEW.md README.md

# Step 6: Verify
tree -L 2 docs/
ls -la *.md
```

---

## ✅ Post-Cleanup Verification

```bash
# Should have only 8 .md files in root
ls -la *.md
# Expected: README.md, .env.example, and key files only

# Should have docs/archive with 77 files
ls -la docs/archive/ | wc -l
# Expected: ~77-80 files (including . and ..)

# Should have organized docs structure
tree docs/
# Expected:
#   docs/DESIGN_DECISIONS/
#   docs/INTEGRATIONS/
#   docs/PRODUCTION/
#   docs/DEVELOPMENT/
#   docs/archive/

# Check git status
git status
# Expected: 150+ files deleted, 5+ files moved, 1-2 files added (README_NEW)
```

---

## 🔍 Files to Keep in Root

| File | Reason |
|------|--------|
| `README.md` | Main entry point |
| `.env.example` | Environment template |
| `requirements.txt` | Dependencies |
| `docker-compose.yml` | Container orchestration |
| `LICENSE` | License |
| `.github/copilot-instructions.md` | AI guidelines |
| `backtest_profit_booking_breeze.py` | Latest backtest script |
| `backtest_profit_booking_breeze_20260601_094947.json` | Latest results |

---

## 📊 Cleanup Impact

### Before
- **Complexity**: 134+ files to search through
- **Onboarding**: Confusing for new developers
- **Maintenance**: Hard to keep docs updated
- **Navigation**: No clear entry point

### After
- **Clarity**: Single README with clear navigation
- **Organization**: Docs grouped by purpose (design, integration, production, development)
- **History**: All old docs preserved in archive
- **Maintainability**: Easy to update canonical docs

---

## 🎯 Next Steps After Cleanup

1. ✅ **Commit cleanup**: `git commit -m "docs: consolidate 134 markdown files into organized structure"`

2. ✅ **Push to repository**: `git push origin main`

3. ✅ **Update team**: Notify team about new documentation structure

4. ✅ **Link old content**: Add "See also" references in README for commonly searched topics

5. ✅ **Set up CI/CD**: Optionally add automated documentation build/validation

---

## 🚀 Recommended Execution

```bash
# 1. Run dry-run first (see what will happen)
python cleanup_repo.py --dry-run
# Review CLEANUP_REPORT_*.json

# 2. Commit current state
git add .
git commit -m "docs: pre-cleanup checkpoint"

# 3. Execute cleanup
python cleanup_repo.py --execute

# 4. Verify results
tree docs/
git status

# 5. Commit changes
git add .
git commit -m "docs: consolidate 134 markdown files into organized structure"

# 6. Review README.md
cat README.md
```

---

## 📞 Questions?

- **Where are old files?** → `docs/archive/` (all 77 files preserved)
- **Can I recover deleted files?** → Yes, from git history: `git log --all --full-history -- <filename>`
- **What if cleanup fails?** → Manual cleanup steps provided above
- **Do I need to re-run backtest?** → No, latest results kept: `backtest_profit_booking_breeze_20260601_094947.json`

---

**Ready?** Execute: `python cleanup_repo.py --execute`
