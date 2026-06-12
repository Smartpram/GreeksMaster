#!/usr/bin/env python3
"""
Final Root Cleanup - Move remaining JSON and data files
"""

from pathlib import Path
import shutil

ROOT = Path('c:\\Data\\MyBreezeApp')

# Remaining files to move
FILES_TO_MOVE = {
    # JSON backtest/analysis files → data/backtest_results/
    'breeze_diagnostic_20251107_092804.json': 'data/backtest_results/',
    'enhanced_backtest_RELIND_20260601_075305.json': 'data/backtest_results/',
    'enhanced_backtest_RELIND_20260601_075648.json': 'data/backtest_results/',
    'enhanced_backtest_TCS_20260601_075307.json': 'data/backtest_results/',
    'enhanced_backtest_TCS_20260601_075650.json': 'data/backtest_results/',
    'integrated_advanced_backtest_20260601_081039.json': 'data/backtest_results/',
    'integrated_advanced_backtest_20260601_081141.json': 'data/backtest_results/',
    'integrated_advanced_backtest_20260601_083430.json': 'data/backtest_results/',
    'integrated_advanced_backtest_20260601_084043.json': 'data/backtest_results/',
    'integrated_advanced_backtest_20260601_085254.json': 'data/backtest_results/',
    'integrated_advanced_backtest_20260601_085537.json': 'data/backtest_results/',
    'integrated_advanced_backtest_20260601_085622.json': 'data/backtest_results/',
    'integrated_advanced_backtest_20260601_085720.json': 'data/backtest_results/',
    'integrated_advanced_backtest_20260601_085813.json': 'data/backtest_results/',
    'integrated_advanced_backtest_20260601_085917.json': 'data/backtest_results/',
    'phase1_remediation_backtest_20260601_091057.json': 'data/backtest_results/',
    'production_readiness_report.json': 'data/reports/',
    'POSITION_TRACKING_REPORT.json': 'data/reports/',
    'POSITION_TRACKING_DETAILED.csv': 'data/reports/',
    'integrated_backtest_analysis.png': 'data/backtest_results/',
}

print("=" * 70)
print("🔄 FINAL ROOT CLEANUP - Move remaining data files")
print("=" * 70)

moves = 0
errors = 0

for filename, dest_dir in FILES_TO_MOVE.items():
    file_path = ROOT / filename
    
    if not file_path.exists():
        print(f"⚠️  SKIP:  {filename} (not found)")
        continue
    
    try:
        # Create destination directory
        dest_path = ROOT / dest_dir
        dest_path.mkdir(parents=True, exist_ok=True)
        
        # Move file
        new_path = dest_path / filename
        shutil.move(str(file_path), str(new_path))
        print(f"📁 MOVE:  {filename:50} → {dest_dir}")
        moves += 1
    except Exception as e:
        print(f"❌ ERROR: {filename} - {str(e)}")
        errors += 1

print("\n" + "=" * 70)
print(f"✅ Files moved: {moves}")
print(f"❌ Errors: {errors}")

# List final remaining files in root
remaining = sorted([f.name for f in ROOT.iterdir() if f.is_file()])
print(f"\n📋 Files remaining in root ({len(remaining)}):")
for f in remaining:
    print(f"  ✓ {f}")

print("=" * 70)
