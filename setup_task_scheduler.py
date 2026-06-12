"""
Setup Windows Task Scheduler for Background Paper Trading
Run this script as Administrator to schedule automated paper trading

Usage:
    python setup_task_scheduler.py

This will:
    1. Create a new scheduled task
    2. Run paper trading every 1 hour
    3. Start at 9:15 AM market open
    4. Run even if machine is locked
    5. Run even if user is logged out
"""

import subprocess
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def check_admin():
    """Check if running as administrator"""
    try:
        import ctypes
        return ctypes.windll.shell.IsUserAnAdmin()
    except Exception:
        return False


def setup_task_scheduler():
    """Create Windows Task Scheduler task for paper trading"""
    
    logger.info("\n" + "="*80)
    logger.info("WINDOWS TASK SCHEDULER SETUP")
    logger.info("="*80)
    
    # Check admin
    if not check_admin():
        logger.error("[ERROR] This script must run as Administrator!")
        logger.error("Right-click PowerShell and select 'Run as administrator'")
        return False
    
    logger.info("\n[✓] Running as Administrator\n")
    
    # Paths
    script_dir = Path(__file__).parent.absolute()
    batch_file = script_dir / "paper_trading_scheduler.bat"
    
    logger.info(f"Script directory: {script_dir}")
    logger.info(f"Batch file: {batch_file}")
    
    if not batch_file.exists():
        logger.error(f"[ERROR] Batch file not found: {batch_file}")
        return False
    
    logger.info(f"[✓] Batch file found\n")
    
    # Task parameters
    task_name = "GreeksMaster_PaperTrading"
    task_description = "Automated paper trading execution every hour (Market: 9:15 AM - 3:45 PM)"
    
    logger.info(f"Task Name: {task_name}")
    logger.info(f"Description: {task_description}\n")
    
    # PowerShell commands to create task
    ps_commands = [
        # Delete existing task if any
        f'$taskExists = Get-ScheduledTask -TaskName "{task_name}" -ErrorAction SilentlyContinue; if ($taskExists) {{ Unregister-ScheduledTask -TaskName "{task_name}" -Confirm:$false; Write-Host "[INFO] Removed existing task" }}',
        
        # Create new trigger (Daily at 9:15 AM, repeat every 1 hour for 8.5 hours - market hours)
        f'''
$trigger = New-ScheduledTaskTrigger -Daily -At "09:15 AM"
$trigger.Repetition = New-ScheduledTaskRepetition -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Hours 8 -Minutes 30)
Write-Host "[INFO] Trigger created: Daily 9:15 AM, repeat every 1 hour"
''',
        
        # Create action (run batch file)
        f'$action = New-ScheduledTaskAction -Execute "{batch_file}"',
        
        # Create principal (run with SYSTEM privileges, even when logged out)
        f'$principal = New-ScheduledTaskPrincipal -UserID "NT AUTHORITY\\SYSTEM" -RunLevel Highest',
        
        # Create settings (allow task to run with or without network, restart on failure)
        '''
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew
Write-Host "[INFO] Settings configured"
''',
        
        # Register the task
        f'''
Register-ScheduledTask -TaskName "{task_name}" -Trigger $trigger -Action $action -Principal $principal -Settings $settings -Description "{task_description}" -Force
Write-Host "[✓] Task registered successfully"
Write-Host ""
Write-Host "Task Details:"
Write-Host "  Name: {task_name}"
Write-Host "  Schedule: Every 1 hour from 9:15 AM - 3:45 PM"
Write-Host "  Runs when: User logged in or out"
Write-Host "  Runs when: Machine locked"
Write-Host "  Runs as: SYSTEM (highest privileges)"
Write-Host "  Batch file: {batch_file}"
Write-Host ""
''',
    ]
    
    # Combine PowerShell commands
    ps_script = "; ".join(ps_commands)
    
    try:
        logger.info("[STEP 1] Creating Task Scheduler task...\n")
        
        # Run PowerShell
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True
        )
        
        # Print output
        if result.stdout:
            logger.info(result.stdout)
        
        if result.stderr:
            logger.error(f"[WARNING] Stderr output:\n{result.stderr}")
        
        if result.returncode != 0:
            logger.error(f"[ERROR] Task creation failed (exit code: {result.returncode})")
            return False
        
        logger.info("[✓] Task created successfully!\n")
        
        # Verify task
        logger.info("[STEP 2] Verifying task...\n")
        
        verify_cmd = f'Get-ScheduledTask -TaskName "{task_name}" | Select TaskName, State, @{{N="NextRun";E={{$_.NextRunTime}}}} | Format-Table -AutoSize'
        
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", verify_cmd],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            logger.info(result.stdout)
        
        logger.info("[✓] Task verified!\n")
        
        # Show test instructions
        logger.info("="*80)
        logger.info("SETUP COMPLETE!")
        logger.info("="*80)
        logger.info("\nNext steps:")
        logger.info("1. Create logs directory:")
        logger.info(f"   mkdir {script_dir}\\logs\n")
        logger.info("2. Test the task manually:")
        logger.info(f'   schtasks /run /tn "{task_name}"\n')
        logger.info("3. Monitor logs:")
        logger.info(f"   Get-Content {script_dir}\\logs\\paper_trading_*.log -Wait\n")
        logger.info("4. Lock your machine and wait for next scheduled run")
        logger.info("5. Unlock and check logs to verify it ran\n")
        
        return True
    
    except Exception as e:
        logger.error(f"[ERROR] Setup failed: {str(e)}")
        return False


def setup_logs_directory():
    """Create logs directory if it doesn't exist"""
    logs_dir = Path(__file__).parent / "logs"
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[✓] Created logs directory: {logs_dir}\n")
    else:
        logger.info(f"[✓] Logs directory exists: {logs_dir}\n")


def main():
    """Main setup function"""
    try:
        logger.info("\n")
        setup_logs_directory()
        success = setup_task_scheduler()
        
        if success:
            logger.info("\n[SUCCESS] Task Scheduler setup complete!")
            logger.info("Paper trading will now run automatically every hour during market hours.")
            logger.info("Machine can be locked and you can stay logged out.")
            return 0
        else:
            logger.error("\n[FAILED] Task Scheduler setup failed")
            return 1
    
    except Exception as e:
        logger.error(f"\n[FATAL] Setup error: {str(e)}")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
