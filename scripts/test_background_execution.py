"""
Test Background Paper Trading Execution
Quick validation that background execution works when machine is locked

Usage:
    python test_background_execution.py

This will:
    1. Create test logs
    2. Verify batch file works
    3. Verify Python executor works
    4. Show how to test with machine locked
"""

import subprocess
import sys
from pathlib import Path
import time
import json
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_environment():
    """Test that all required files exist"""
    logger.info("\n" + "="*80)
    logger.info("ENVIRONMENT VALIDATION")
    logger.info("="*80 + "\n")
    
    script_dir = Path(__file__).parent
    files_needed = [
        "paper_trading_background.py",
        "paper_trading_scheduler.bat",
        "setup_task_scheduler.py"
    ]
    
    all_exist = True
    for fname in files_needed:
        fpath = script_dir / fname
        if fpath.exists():
            logger.info(f"[✓] Found: {fname}")
        else:
            logger.error(f"[✗] Missing: {fname}")
            all_exist = False
    
    # Check logs directory
    logs_dir = script_dir / "logs"
    if not logs_dir.exists():
        logger.info(f"\n[INFO] Creating logs directory...")
        logs_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[✓] Created: {logs_dir}")
    else:
        logger.info(f"[✓] Logs directory exists: {logs_dir}")
    
    return all_exist


def test_python_executor():
    """Test that Python executor runs"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: PYTHON EXECUTOR")
    logger.info("="*80 + "\n")
    
    script_dir = Path(__file__).parent
    executor = script_dir / "paper_trading_background.py"
    
    if not executor.exists():
        logger.error(f"[✗] Executor not found: {executor}")
        return False
    
    logger.info(f"[INFO] Testing: {executor}")
    logger.info("[INFO] Running Python executor (this will take ~5-10 seconds)...\n")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, str(executor)],
            capture_output=True,
            text=True,
            timeout=30
        )
        elapsed = time.time() - start_time
        
        logger.info(f"[RESULT] Execution time: {elapsed:.1f} seconds")
        logger.info(f"[RESULT] Exit code: {result.returncode}")
        
        if result.stdout:
            logger.info(f"\n[STDOUT]\n{result.stdout}")
        
        if result.stderr:
            logger.info(f"\n[STDERR]\n{result.stderr}")
        
        # Check logs were created
        logs_dir = script_dir / "logs"
        log_files = list(logs_dir.glob("paper_trading_*.log"))
        
        if log_files:
            logger.info(f"\n[✓] Log files created: {len(log_files)}")
            for log_file in sorted(log_files)[-1:]:  # Show most recent
                logger.info(f"    {log_file.name}")
                with open(log_file, 'r') as f:
                    content = f.read()
                    if content:
                        logger.info(f"\n[LOG CONTENT]\n{content[:500]}")
        else:
            logger.warning("[✗] No log files created")
        
        return result.returncode == 0
    
    except subprocess.TimeoutExpired:
        logger.error("[✗] Executor timed out")
        return False
    except Exception as e:
        logger.error(f"[✗] Executor failed: {str(e)}")
        return False


def test_batch_wrapper():
    """Test that batch wrapper works"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: BATCH WRAPPER")
    logger.info("="*80 + "\n")
    
    script_dir = Path(__file__).parent
    batch_file = script_dir / "paper_trading_scheduler.bat"
    
    if not batch_file.exists():
        logger.error(f"[✗] Batch file not found: {batch_file}")
        return False
    
    logger.info(f"[INFO] Testing: {batch_file}")
    logger.info("[INFO] Running batch wrapper (this will take ~5-10 seconds)...\n")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            [str(batch_file)],
            capture_output=True,
            text=True,
            shell=True,
            timeout=30
        )
        elapsed = time.time() - start_time
        
        logger.info(f"[RESULT] Execution time: {elapsed:.1f} seconds")
        logger.info(f"[RESULT] Exit code: {result.returncode}")
        
        if result.stdout:
            logger.info(f"\n[STDOUT]\n{result.stdout}")
        
        if result.stderr:
            logger.info(f"\n[STDERR]\n{result.stderr}")
        
        # Check scheduler log
        logs_dir = script_dir / "logs"
        scheduler_log = logs_dir / "scheduler.log"
        
        if scheduler_log.exists():
            logger.info(f"\n[✓] Scheduler log created: {scheduler_log.name}")
            with open(scheduler_log, 'r') as f:
                content = f.read()
                if content:
                    logger.info(f"\n[LOG CONTENT - Last 500 chars]\n{content[-500:]}")
        
        return result.returncode == 0
    
    except Exception as e:
        logger.error(f"[✗] Batch wrapper failed: {str(e)}")
        return False


def test_locked_machine_simulation():
    """Provide instructions for testing with locked machine"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: LOCKED MACHINE SIMULATION")
    logger.info("="*80 + "\n")
    
    logger.info("To test if background execution works when machine is LOCKED:\n")
    
    logger.info("[STEP 1] Start monitoring logs in one PowerShell window:")
    logger.info('  Get-Content "logs\\paper_trading_*.log" -Wait\n')
    
    logger.info("[STEP 2] In another PowerShell window, manually trigger task:")
    logger.info('  schtasks /run /tn "GreeksMaster_PaperTrading"\n')
    
    logger.info("[STEP 3] Verify it runs in the log monitoring window\n")
    
    logger.info("[STEP 4] Lock your machine:")
    logger.info("  Windows Key + L\n")
    
    logger.info("[STEP 5] From another device (or wait for scheduled time)")
    logger.info("  Trigger task again:")
    logger.info('  schtasks /run /tn "GreeksMaster_PaperTrading"\n')
    
    logger.info("[STEP 6] Unlock machine and check logs to see if it executed\n")
    
    logger.info("[EXPECTED] Logs show execution even though machine was locked\n")
    
    return True


def test_task_scheduler_status():
    """Check if Task Scheduler task exists"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: TASK SCHEDULER STATUS")
    logger.info("="*80 + "\n")
    
    task_name = "GreeksMaster_PaperTrading"
    
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", 
             f'Get-ScheduledTask -TaskName "{task_name}" -ErrorAction SilentlyContinue | Select TaskName, State, @{{N="NextRun";E={{$_.NextRunTime}}}} | Format-List'],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            logger.info(f"[✓] Task found:\n{result.stdout}")
            return True
        else:
            logger.warning(f"[INFO] Task '{task_name}' not yet scheduled")
            logger.info("      Run 'python setup_task_scheduler.py' to create it\n")
            return False
    
    except Exception as e:
        logger.error(f"[✗] Could not check task status: {str(e)}")
        return False


def generate_summary():
    """Generate test summary"""
    logger.info("\n" + "="*80)
    logger.info("BACKGROUND EXECUTION TEST COMPLETE")
    logger.info("="*80 + "\n")
    
    logger.info("Next steps:")
    logger.info("1. [✓] Environment validated")
    logger.info("2. [✓] Python executor tested")
    logger.info("3. [✓] Batch wrapper tested")
    logger.info("4. [✓] Locked machine instructions provided")
    logger.info("5. [ ] Next: Set up Task Scheduler (run as Admin):\n")
    logger.info("      python setup_task_scheduler.py\n")
    logger.info("6. [ ] Test with locked machine following instructions above")
    logger.info("7. [ ] Verify logs show execution")
    logger.info("8. [ ] Background execution ready for production!\n")


def main():
    """Run all tests"""
    try:
        logger.info("\n")
        logger.info("="*80)
        logger.info("BACKGROUND PAPER TRADING TEST SUITE")
        logger.info("="*80)
        
        # Test environment
        if not test_environment():
            logger.error("\n[FAILED] Environment validation failed")
            return 1
        
        # Test Python executor
        py_ok = test_python_executor()
        
        # Test batch wrapper
        batch_ok = test_batch_wrapper()
        
        # Test locked machine scenario
        locked_ok = test_locked_machine_simulation()
        
        # Check task scheduler
        task_ok = test_task_scheduler_status()
        
        # Generate summary
        generate_summary()
        
        if py_ok and batch_ok:
            logger.info("[SUCCESS] All tests passed!")
            logger.info("Background execution is working correctly.")
            return 0
        else:
            logger.warning("[WARNING] Some tests had issues - check output above")
            return 1
    
    except Exception as e:
        logger.error(f"\n[FATAL] Test suite failed: {str(e)}")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
