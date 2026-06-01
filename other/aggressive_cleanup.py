#!/usr/bin/env python3
"""
Aggressive Repository Cleanup Script
Removes all unnecessary markdown files from root, keeping only essentials
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Files to KEEP in root
KEEP_FILES = {
    'README.md',
    '.env.example',
    'requirements.txt',
    'docker-compose.yml',
    'LICENSE',
    'CLEANUP_PLAN.md',
    'CLEANUP_QUICK_REFERENCE.md',
    'CLEANUP_INDEX.md',
    'CLEANUP_MASTER_CHECKLIST.md',
}

# Get all .md files in root
root_path = Path('.')
all_md_files = list(root_path.glob('*.md'))

# Create archive directory if needed
archive_path = root_path / 'docs' / 'archive'
archive_path.mkdir(parents=True, exist_ok=True)

# Move everything not in KEEP_FILES to archive
moved_count = 0
for md_file in all_md_files:
    if md_file.name not in KEEP_FILES:
        dest_path = archive_path / md_file.name
        try:
            shutil.move(str(md_file), str(dest_path))
            print(f"✅ Moved: {md_file.name} → docs/archive/")
            moved_count += 1
        except Exception as e:
            print(f"❌ Error moving {md_file.name}: {e}")

print(f"\n{'='*60}")
print(f"✅ AGGRESSIVE CLEANUP COMPLETE")
print(f"{'='*60}")
print(f"Files moved to archive: {moved_count}")
print(f"\nRemaining files in root:")
remaining = sorted([f.name for f in root_path.glob('*.md')])
for fname in remaining:
    print(f"  ✅ {fname}")

print(f"\nVerify with:")
print(f"  ls -la *.md")
print(f"  ls docs/archive/ | wc -l")
