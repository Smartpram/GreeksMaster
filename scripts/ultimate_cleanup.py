#!/usr/bin/env python3
"""
Ultimate Repository Cleanup Script
Organizes all files in root into proper project structure
"""

from pathlib import Path
import shutil
import json
from datetime import datetime

ROOT = Path('c:\\Data\\MyBreezeApp')
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

# Files to keep in root
KEEP_IN_ROOT = {
    'README.md',
    '.env',
    '.env.example',
    '.gitignore',
    'LICENSE',
    'requirements.txt',
    'docker-compose.yml',
    'Dockerfile',
    'setup.py',
    'run.py',
}

# Categorize files
CATEGORIES = {
    'backtest_results': {
        'patterns': ['backtest*.json', 'backtest_results.png', 'BACKTEST*.txt'],
        'dest': 'data/backtest_results'
    },
    'config_data': {
        'patterns': ['*.db', '*ScripMaster.txt', 'network_config*.json', 'safety_state.json', 'SecurityMaster.zip'],
        'dest': 'data/config'
    },
    'test_scripts': {
        'patterns': ['test_*.py', '*_test.py', 'TEST_*.py'],
        'dest': 'tests/scripts'
    },
    'backtest_scripts': {
        'patterns': ['backtest*.py', '*backtest*.py', 'run_backtest*.py', 'run_*backtest*.py'],
        'dest': 'backtest'
    },
    'trading_scripts': {
        'patterns': ['run_*.py', 'run_*.sh', 'run_*.bat', '*_trader*.py', '*trading*.py', 'monitor.py'],
        'dest': 'trading'
    },
    'ai_scripts': {
        'patterns': ['ai_*.py', 'ai_*.log', 'ai_*.txt', '*sentiment*.py', '*signal*.py'],
        'dest': 'ai_ml'
    },
    'analysis_scripts': {
        'patterns': ['analyze_*.py', '*analysis*.py', 'create_*.py', 'diagnose_*.py'],
        'dest': 'analysis'
    },
    'setup_scripts': {
        'patterns': ['setup_*.py', 'check_*.py', 'download_*.py', '*integration*.py', 'get_*.py', 'fix_*.py'],
        'dest': 'setup'
    },
    'documentation_indexes': {
        'patterns': ['*_INDEX*.py', '*_INDEX*.txt', '*MANIFEST*.py', '00_*.py'],
        'dest': 'docs/indexes'
    },
    'cleanup_reports': {
        'patterns': ['CLEANUP_REPORT_*.json'],
        'dest': 'docs/cleanup_reports'
    },
    'test_results': {
        'patterns': ['*_RESULTS.csv', '*_RESULTS.json', '*TEST_RESULTS.csv', '*TEST_RESULTS.json', 'CORRECTED_TEST_RESULTS*'],
        'dest': 'test_results'
    },
    'guides': {
        'patterns': ['*GUIDE*.txt', '*GUIDE*.py', '*QUICK*.txt', '*QUICK*.py', 'START_HERE.txt', 'STARTUP_GUIDE.txt'],
        'dest': 'docs/guides'
    },
    'shell_scripts': {
        'patterns': ['*.sh', '*.bat', '*.ps1'],
        'dest': 'scripts'
    },
    'logs_and_outputs': {
        'patterns': ['*.log', 'backtest_output.txt', 'phase1_backtest_output.txt', 'project_structure.txt', '*_SUMMARY.txt'],
        'dest': 'logs'
    },
    'summary_reports': {
        'patterns': ['*SUMMARY*.py', '*SUMMARY*.json', '*SUMMARY.txt', '*COMPLETION*.txt', '*COMPLETION*.py', 'final_*.py'],
        'dest': 'docs/summaries'
    },
}

def get_destination(filename):
    """Determine destination directory for a file"""
    name = Path(filename)
    
    # Keep specific files in root
    if name.name in KEEP_IN_ROOT:
        return None
    
    # Skip cleanup guide files and markdown
    if name.name.startswith('CLEANUP_') and name.suffix == '.md':
        return None
    if name.name == 'README.md':
        return None
    
    # Check categories
    for category, config in CATEGORIES.items():
        for pattern in config['patterns']:
            if name.match(pattern):
                return config['dest']
    
    # Default for unknown files
    if name.suffix in ['.py', '.txt']:
        return 'other'
    
    return None

def main():
    print("=" * 70)
    print("🔍 ULTIMATE REPOSITORY CLEANUP")
    print("=" * 70)
    
    moves = []
    errors = []
    
    # Get all files in root
    root_files = sorted([f for f in ROOT.iterdir() if f.is_file()])
    
    for file_path in root_files:
        dest_dir = get_destination(file_path.name)
        
        if dest_dir is None:
            print(f"✅ KEEP:  {file_path.name}")
            continue
        
        try:
            # Create destination directory
            dest_path = ROOT / dest_dir
            dest_path.mkdir(parents=True, exist_ok=True)
            
            # Move file
            new_path = dest_path / file_path.name
            shutil.move(str(file_path), str(new_path))
            print(f"📁 MOVE:  {file_path.name:50} → {dest_dir}/")
            moves.append({
                'file': file_path.name,
                'destination': dest_dir
            })
        except Exception as e:
            error_msg = f"❌ ERROR: {file_path.name} - {str(e)}"
            print(error_msg)
            errors.append(error_msg)
    
    # Generate summary
    print("\n" + "=" * 70)
    print(f"✅ Files moved: {len(moves)}")
    print(f"❌ Errors: {len(errors)}")
    
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(f"  {error}")
    
    # List remaining files in root
    remaining = sorted([f.name for f in ROOT.iterdir() if f.is_file()])
    print(f"\n📋 Files remaining in root ({len(remaining)}):")
    for f in remaining:
        print(f"  ✓ {f}")
    
    # Save report
    report = {
        'timestamp': TIMESTAMP,
        'files_moved': len(moves),
        'errors': len(errors),
        'moves': moves,
        'remaining_files': remaining
    }
    
    report_path = ROOT / f'ULTIMATE_CLEANUP_REPORT_{TIMESTAMP}.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved: ULTIMATE_CLEANUP_REPORT_{TIMESTAMP}.json")
    print("=" * 70)

if __name__ == '__main__':
    main()
