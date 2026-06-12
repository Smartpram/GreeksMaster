#!/usr/bin/env python3
"""
MyBreezeApp Monitoring and Maintenance Script
"""
import os
import sys
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

class MyBreezeMonitor:
    """Monitor and maintain MyBreezeApp"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.logs_dir = self.base_dir / "logs"
        self.backups_dir = self.base_dir / "backups"
        self.reports_dir = self.base_dir / "reports"
        
        # Ensure directories exist
        for directory in [self.logs_dir, self.backups_dir, self.reports_dir]:
            directory.mkdir(exist_ok=True)
    
    def check_system_health(self):
        """Check overall system health"""
        print("🏥 System Health Check")
        print("-" * 40)
        
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # Check disk space
        disk_usage = self._check_disk_space()
        health_status["checks"]["disk_space"] = disk_usage
        print(f"💾 Disk Space: {disk_usage['status']}")
        
        # Check log file size
        log_size = self._check_log_sizes()
        health_status["checks"]["log_sizes"] = log_size
        print(f"📄 Log Sizes: {log_size['status']}")
        
        # Check database integrity
        db_health = self._check_database_health()
        health_status["checks"]["database"] = db_health
        print(f"🗄️  Database: {db_health['status']}")
        
        # Check configuration
        config_health = self._check_configuration()
        health_status["checks"]["configuration"] = config_health
        print(f"⚙️  Configuration: {config_health['status']}")
        
        # Save health report
        health_file = self.reports_dir / f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(health_file, 'w') as f:
            json.dump(health_status, f, indent=2)
        
        return health_status
    
    def _check_disk_space(self):
        """Check available disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.base_dir)
            
            free_gb = free // (1024**3)
            total_gb = total // (1024**3)
            usage_percent = (used / total) * 100
            
            status = "GOOD"
            if usage_percent > 90:
                status = "CRITICAL"
            elif usage_percent > 80:
                status = "WARNING"
            
            return {
                "status": status,
                "free_gb": free_gb,
                "total_gb": total_gb,
                "usage_percent": round(usage_percent, 2)
            }
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    def _check_log_sizes(self):
        """Check log file sizes"""
        try:
            log_files = list(self.logs_dir.glob("*.log"))
            total_size_mb = 0
            large_files = []
            
            for log_file in log_files:
                size_mb = log_file.stat().st_size / (1024**2)
                total_size_mb += size_mb
                
                if size_mb > 100:  # Files larger than 100MB
                    large_files.append({
                        "file": log_file.name,
                        "size_mb": round(size_mb, 2)
                    })
            
            status = "GOOD"
            if total_size_mb > 1000:  # Total logs > 1GB
                status = "WARNING"
            if any(f["size_mb"] > 500 for f in large_files):
                status = "CRITICAL"
            
            return {
                "status": status,
                "total_size_mb": round(total_size_mb, 2),
                "large_files": large_files
            }
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    def _check_database_health(self):
        """Check database integrity"""
        try:
            db_file = self.base_dir / "mybreeze.db"
            if not db_file.exists():
                return {"status": "WARNING", "message": "Database file not found"}
            
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            
            # Check database integrity
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            # Get database size
            db_size_mb = db_file.stat().st_size / (1024**2)
            
            # Count tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            conn.close()
            
            status = "GOOD" if integrity_result == "ok" else "ERROR"
            
            return {
                "status": status,
                "integrity": integrity_result,
                "size_mb": round(db_size_mb, 2),
                "table_count": len(tables)
            }
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    def _check_configuration(self):
        """Check configuration validity"""
        try:
            env_file = self.base_dir / ".env"
            if not env_file.exists():
                return {"status": "ERROR", "message": ".env file not found"}
            
            # Check for required environment variables
            required_vars = [
                "BREEZE_API_KEY",
                "BREEZE_SECRET_KEY",
                "BREEZE_USER_ID",
                "SECRET_KEY"
            ]
            
            missing_vars = []
            with open(env_file) as f:
                env_content = f.read()
                for var in required_vars:
                    if f"{var}=" not in env_content or f"{var}=your_" in env_content:
                        missing_vars.append(var)
            
            status = "GOOD" if not missing_vars else "WARNING"
            
            return {
                "status": status,
                "missing_or_default": missing_vars
            }
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    def backup_data(self):
        """Create backup of important data"""
        print("💾 Creating Backups")
        print("-" * 40)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_results = {}
        
        # Backup database
        db_file = self.base_dir / "mybreeze.db"
        if db_file.exists():
            backup_db = self.backups_dir / f"mybreeze_{timestamp}.db"
            try:
                import shutil
                shutil.copy2(db_file, backup_db)
                backup_results["database"] = {"status": "SUCCESS", "file": str(backup_db)}
                print(f"✅ Database backed up to {backup_db}")
            except Exception as e:
                backup_results["database"] = {"status": "ERROR", "error": str(e)}
                print(f"❌ Database backup failed: {e}")
        
        # Backup configuration
        env_file = self.base_dir / ".env"
        if env_file.exists():
            backup_env = self.backups_dir / f"env_{timestamp}.backup"
            try:
                import shutil
                shutil.copy2(env_file, backup_env)
                backup_results["configuration"] = {"status": "SUCCESS", "file": str(backup_env)}
                print(f"✅ Configuration backed up to {backup_env}")
            except Exception as e:
                backup_results["configuration"] = {"status": "ERROR", "error": str(e)}
                print(f"❌ Configuration backup failed: {e}")
        
        # Backup logs (compress)
        try:
            import tarfile
            backup_logs = self.backups_dir / f"logs_{timestamp}.tar.gz"
            with tarfile.open(backup_logs, "w:gz") as tar:
                tar.add(self.logs_dir, arcname="logs")
            backup_results["logs"] = {"status": "SUCCESS", "file": str(backup_logs)}
            print(f"✅ Logs backed up to {backup_logs}")
        except Exception as e:
            backup_results["logs"] = {"status": "ERROR", "error": str(e)}
            print(f"❌ Logs backup failed: {e}")
        
        return backup_results
    
    def cleanup_old_files(self, days_to_keep=30):
        """Clean up old log and backup files"""
        print(f"🧹 Cleaning up files older than {days_to_keep} days")
        print("-" * 40)
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleanup_results = {"logs": 0, "backups": 0, "reports": 0}
        
        # Clean logs
        for log_file in self.logs_dir.glob("*.log.*"):  # Rotated logs
            if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_date:
                log_file.unlink()
                cleanup_results["logs"] += 1
        
        # Clean old backups
        for backup_file in self.backups_dir.glob("*"):
            if datetime.fromtimestamp(backup_file.stat().st_mtime) < cutoff_date:
                backup_file.unlink()
                cleanup_results["backups"] += 1
        
        # Clean old reports
        for report_file in self.reports_dir.glob("*.json"):
            if datetime.fromtimestamp(report_file.stat().st_mtime) < cutoff_date:
                report_file.unlink()
                cleanup_results["reports"] += 1
        
        print(f"✅ Cleaned up {cleanup_results['logs']} log files")
        print(f"✅ Cleaned up {cleanup_results['backups']} backup files")
        print(f"✅ Cleaned up {cleanup_results['reports']} report files")
        
        return cleanup_results
    
    def rotate_logs(self):
        """Rotate large log files"""
        print("🔄 Rotating Log Files")
        print("-" * 40)
        
        rotated_files = []
        
        for log_file in self.logs_dir.glob("*.log"):
            try:
                size_mb = log_file.stat().st_size / (1024**2)
                if size_mb > 50:  # Rotate files larger than 50MB
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    rotated_name = f"{log_file.stem}_{timestamp}.log"
                    rotated_path = log_file.parent / rotated_name
                    
                    log_file.rename(rotated_path)
                    log_file.touch()  # Create new empty log file
                    
                    rotated_files.append(str(rotated_path))
                    print(f"✅ Rotated {log_file.name} to {rotated_name}")
            except Exception as e:
                print(f"❌ Failed to rotate {log_file.name}: {e}")
        
        return rotated_files
    
    def generate_performance_report(self):
        """Generate performance summary report"""
        print("📊 Generating Performance Report")
        print("-" * 40)
        
        try:
            # This would integrate with the actual application to get metrics
            # For now, we'll create a template structure
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "period": "last_30_days",
                "summary": {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "win_rate": 0.0,
                    "total_pnl": 0.0,
                    "max_drawdown": 0.0,
                    "sharpe_ratio": 0.0
                },
                "strategy_performance": {
                    "signals_generated": 0,
                    "signals_acted_on": 0,
                    "signal_accuracy": 0.0
                },
                "risk_metrics": {
                    "max_position_size": 0.0,
                    "average_position_size": 0.0,
                    "stop_loss_hits": 0,
                    "target_hits": 0
                }
            }
            
            # Save report
            report_file = self.reports_dir / f"performance_{datetime.now().strftime('%Y%m%d')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"✅ Performance report saved to {report_file}")
            return report
            
        except Exception as e:
            print(f"❌ Failed to generate performance report: {e}")
            return None
    
    def run_full_maintenance(self):
        """Run complete maintenance routine"""
        print("🔧 MyBreezeApp Full Maintenance")
        print("=" * 50)
        print(f"Started at: {datetime.now()}")
        print()
        
        # Health check
        health = self.check_system_health()
        print()
        
        # Backup
        backup_results = self.backup_data()
        print()
        
        # Log rotation
        rotated_logs = self.rotate_logs()
        print()
        
        # Cleanup
        cleanup_results = self.cleanup_old_files()
        print()
        
        # Performance report
        perf_report = self.generate_performance_report()
        print()
        
        print("✅ Maintenance Complete!")
        print(f"Finished at: {datetime.now()}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MyBreezeApp Monitor and Maintenance")
    parser.add_argument("--health", action="store_true", help="Run health check only")
    parser.add_argument("--backup", action="store_true", help="Run backup only")
    parser.add_argument("--cleanup", action="store_true", help="Run cleanup only")
    parser.add_argument("--rotate", action="store_true", help="Rotate logs only")
    parser.add_argument("--report", action="store_true", help="Generate performance report")
    parser.add_argument("--full", action="store_true", help="Run full maintenance")
    parser.add_argument("--days", type=int, default=30, help="Days to keep files (default: 30)")
    
    args = parser.parse_args()
    
    monitor = MyBreezeMonitor()
    
    if args.health:
        monitor.check_system_health()
    elif args.backup:
        monitor.backup_data()
    elif args.cleanup:
        monitor.cleanup_old_files(args.days)
    elif args.rotate:
        monitor.rotate_logs()
    elif args.report:
        monitor.generate_performance_report()
    elif args.full:
        monitor.run_full_maintenance()
    else:
        # Default: run health check
        monitor.check_system_health()

if __name__ == "__main__":
    main()