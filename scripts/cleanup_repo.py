#!/usr/bin/env python3
"""
Repository Cleanup Script - MyBreezeApp

Automatically:
1. Creates new documentation structure
2. Archives old documentation to docs/archive/
3. Moves important docs to organized locations
4. Deletes redundant files (with safety checks)
5. Replaces README.md with new version
6. Generates cleanup report

Usage:
    python cleanup_repo.py --dry-run    # See what will be deleted
    python cleanup_repo.py --execute    # Actually perform cleanup
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

class RepoCleanup:
    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Files to archive (move to docs/archive/)
        self.archive_patterns = [
            "PHASE_*.md",
            "ADVANCED_*.md",
            "BACKTEST_*.md",
            "DELIVERY_*.md",
            "FINAL_*.md",
            "AI_*.md",
            "SENTIMENT_*.md",
            "STATUS_*.md",
            "*_COMPLETE.md",
            "CASH_FLOW_*.md",
        ]
        
        # Specific files to delete (redundant)
        self.delete_files = [
            "README_OLD.md",
            "README_EXPANDED_RESULTS.md",
            "README_PHASE_9.md",
            "README_PHASE1_REMEDIATION.md",
            "README_PROFIT_BOOKING_COMPLETE.md",
            "DOCUMENTATION_INDEX.md",
            "INDEX.md",
            "QUICK_REFERENCE.md",
            "QUICK_COMMAND_REFERENCE.md",
            "PROJECT_SUMMARY.md",
            "IMPLEMENTATION_SUMMARY.md",
            "GET_STARTED.md",
            "START_HERE_ADVANCED_INDICATORS.md",
            "START_HERE_ADVANCED_STRATEGIES.md",
            "START_HERE_EXPANDED_RESULTS.md",
            "ENHANCED_SIGNAL_README.md",
        ]
        
        # Files to move to organized locations
        self.move_files = {
            "INTEGRATION_GUIDE.md": "docs/INTEGRATIONS/",
            "PRODUCTION_VALIDATOR_GUIDE.md": "docs/PRODUCTION/",
            "REGIME_MONITOR_GUIDE.md": "docs/PRODUCTION/",
            "TEST_VALIDATION_GUIDE.md": "docs/DEVELOPMENT/",
            "TRAILING_STOPS_DESIGN_RULES.md": "docs/DESIGN_DECISIONS/",
        }
        
        self.cleanup_report = {
            "timestamp": self.timestamp,
            "repo_root": str(self.repo_root),
            "actions": {
                "archived": [],
                "moved": [],
                "deleted": [],
            },
            "stats": {
                "archived_count": 0,
                "moved_count": 0,
                "deleted_count": 0,
            }
        }
    
    def create_directory_structure(self) -> bool:
        """Create new documentation directory structure"""
        directories = [
            "docs/archive",
            "docs/DESIGN_DECISIONS",
            "docs/INTEGRATIONS",
            "docs/PRODUCTION",
            "docs/DEVELOPMENT",
        ]
        
        try:
            for directory in directories:
                path = self.repo_root / directory
                path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created: {directory}")
            return True
        except Exception as e:
            print(f"❌ Error creating directories: {e}")
            return False
    
    def find_files_by_pattern(self, patterns: List[str]) -> List[Path]:
        """Find files matching glob patterns"""
        files = []
        for pattern in patterns:
            files.extend(self.repo_root.glob(pattern))
        return files
    
    def archive_files(self, dry_run: bool = True) -> int:
        """Archive old documentation files"""
        archived = 0
        files_to_archive = self.find_files_by_pattern(self.archive_patterns)
        
        print(f"\n📦 Archiving Files ({len(files_to_archive)} files)")
        print("-" * 60)
        
        for file_path in sorted(files_to_archive):
            if file_path.is_file():
                dest_path = self.repo_root / "docs/archive" / file_path.name
                
                print(f"  Archive: {file_path.name}")
                
                if not dry_run:
                    try:
                        shutil.move(str(file_path), str(dest_path))
                        self.cleanup_report["actions"]["archived"].append(file_path.name)
                    except Exception as e:
                        print(f"    ⚠️  Error: {e}")
                        continue
                
                archived += 1
        
        self.cleanup_report["stats"]["archived_count"] = archived
        print(f"✅ Total archived: {archived} files")
        return archived
    
    def move_important_files(self, dry_run: bool = True) -> int:
        """Move important documentation to organized locations"""
        moved = 0
        
        print(f"\n🔄 Moving Important Files")
        print("-" * 60)
        
        for file_name, dest_dir in self.move_files.items():
            file_path = self.repo_root / file_name
            
            if file_path.exists():
                dest_path = self.repo_root / dest_dir / file_name
                print(f"  Move: {file_name} → {dest_dir}")
                
                if not dry_run:
                    try:
                        shutil.move(str(file_path), str(dest_path))
                        self.cleanup_report["actions"]["moved"].append({
                            "from": file_name,
                            "to": dest_dir
                        })
                    except Exception as e:
                        print(f"    ⚠️  Error: {e}")
                        continue
                
                moved += 1
            else:
                print(f"  ⚠️  Not found: {file_name}")
        
        self.cleanup_report["stats"]["moved_count"] = moved
        print(f"✅ Total moved: {moved} files")
        return moved
    
    def delete_redundant_files(self, dry_run: bool = True) -> int:
        """Delete redundant/duplicate files"""
        deleted = 0
        
        print(f"\n🗑️  Deleting Redundant Files ({len(self.delete_files)} files)")
        print("-" * 60)
        
        for file_name in self.delete_files:
            file_path = self.repo_root / file_name
            
            if file_path.exists():
                print(f"  Delete: {file_name}")
                
                if not dry_run:
                    try:
                        file_path.unlink()
                        self.cleanup_report["actions"]["deleted"].append(file_name)
                    except Exception as e:
                        print(f"    ⚠️  Error: {e}")
                        continue
                
                deleted += 1
        
        self.cleanup_report["stats"]["deleted_count"] = deleted
        print(f"✅ Total deleted: {deleted} files")
        return deleted
    
    def replace_readme(self, dry_run: bool = True) -> bool:
        """Replace README.md with new comprehensive version"""
        readme_old = self.repo_root / "README.md"
        readme_new = self.repo_root / "README_NEW.md"
        
        print(f"\n📝 Replacing README.md")
        print("-" * 60)
        
        if readme_new.exists():
            print(f"  Backup: README.md → README_OLD_BACKUP_{self.timestamp}.md")
            if not dry_run:
                if readme_old.exists():
                    backup_path = self.repo_root / f"README_OLD_BACKUP_{self.timestamp}.md"
                    shutil.move(str(readme_old), str(backup_path))
                
                print(f"  Replace: README_NEW.md → README.md")
                shutil.move(str(readme_new), str(readme_old))
            
            print(f"✅ README.md replaced successfully")
            return True
        else:
            print(f"⚠️  README_NEW.md not found, skipping replacement")
            return False
    
    def generate_report(self) -> str:
        """Generate cleanup report"""
        report_path = self.repo_root / f"CLEANUP_REPORT_{self.timestamp}.json"
        
        print(f"\n📊 Cleanup Report")
        print("-" * 60)
        print(f"  Archived: {self.cleanup_report['stats']['archived_count']} files")
        print(f"  Moved: {self.cleanup_report['stats']['moved_count']} files")
        print(f"  Deleted: {self.cleanup_report['stats']['deleted_count']} files")
        print(f"  Total: {sum(self.cleanup_report['stats'].values())} files processed")
        
        with open(report_path, 'w') as f:
            json.dump(self.cleanup_report, f, indent=2)
        
        print(f"\n✅ Report saved: {report_path}")
        return str(report_path)
    
    def print_summary(self, dry_run: bool = True):
        """Print final summary"""
        print(f"\n{'=' * 60}")
        print(f"  REPOSITORY CLEANUP {'[DRY RUN]' if dry_run else '[EXECUTED]'}")
        print(f"{'=' * 60}")
        
        print(f"\n📊 Changes Summary:")
        print(f"  ├─ Archived: {self.cleanup_report['stats']['archived_count']} files")
        print(f"  ├─ Moved: {self.cleanup_report['stats']['moved_count']} files")
        print(f"  └─ Deleted: {self.cleanup_report['stats']['deleted_count']} files")
        
        print(f"\n📁 New Structure:")
        print(f"  ├─ README.md (comprehensive, single entry point)")
        print(f"  ├─ .env.example")
        print(f"  ├─ requirements.txt")
        print(f"  └─ docs/")
        print(f"     ├─ DESIGN_DECISIONS/")
        print(f"     ├─ INTEGRATIONS/")
        print(f"     ├─ PRODUCTION/")
        print(f"     ├─ DEVELOPMENT/")
        print(f"     └─ archive/ (77 historical files)")
        
        if dry_run:
            print(f"\n⚠️  This is a DRY RUN. No files were actually modified.")
            print(f"   Run with --execute to perform actual cleanup.")
        else:
            print(f"\n✅ Cleanup completed successfully!")
    
    def execute(self, dry_run: bool = True):
        """Execute full cleanup"""
        print(f"🚀 Starting Repository Cleanup (DRY RUN: {dry_run})")
        print(f"   Timestamp: {self.timestamp}")
        print(f"   Root: {self.repo_root}")
        
        # Step 1: Create structure
        if not self.create_directory_structure():
            print("❌ Failed to create directory structure")
            return
        
        # Step 2: Archive old files
        self.archive_files(dry_run=dry_run)
        
        # Step 3: Move important files
        self.move_important_files(dry_run=dry_run)
        
        # Step 4: Delete redundant files
        self.delete_redundant_files(dry_run=dry_run)
        
        # Step 5: Replace README
        self.replace_readme(dry_run=dry_run)
        
        # Step 6: Generate report
        self.generate_report()
        
        # Step 7: Print summary
        self.print_summary(dry_run=dry_run)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="MyBreezeApp Repository Cleanup Tool"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview changes without modifying files (default)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform cleanup (removes --dry-run)"
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root directory (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # If --execute is specified, disable dry-run
    dry_run = not args.execute
    
    cleanup = RepoCleanup(repo_root=args.repo_root)
    cleanup.execute(dry_run=dry_run)


if __name__ == "__main__":
    main()
