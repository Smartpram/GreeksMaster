#!/usr/bin/env python3
"""
LIVE DATA TEST RUNNER
=====================

Quick script to run live data tests with common configurations.

Usage:
    python run_live_tests.py [preset]

Presets:
    quick     - 5 cycles, NIFTY50 (default)
    standard  - 10 cycles, NIFTY50, BANKNIFTY
    extended  - 20 cycles, multiple symbols
    stress    - 100 cycles, stress test
    ci        - For CI/CD pipeline
"""

import sys
import os
import subprocess
import json
from datetime import datetime


def run_test(symbol: str, cycles: int, verbose: bool = False) -> int:
    """Run test with given parameters"""
    cmd = [sys.executable, 'test_live_data.py', 
           '--symbol', symbol, 
           '--cycles', str(cycles)]
    
    if verbose:
        cmd.append('--verbose')
    
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    return subprocess.run(cmd).returncode


def run_preset(preset: str = 'quick'):
    """Run predefined test presets"""
    
    print(f"\n{'#'*60}")
    print(f"# LIVE DATA TEST RUNNER - {preset.upper()} PRESET")
    print(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")
    
    failed_tests = []
    
    if preset == 'quick':
        print("\n[Preset: QUICK] 5 cycles, NIFTY50")
        if run_test('NIFTY50', 5) != 0:
            failed_tests.append('NIFTY50 (quick)')
    
    elif preset == 'standard':
        print("\n[Preset: STANDARD] Multiple symbols, 10 cycles each")
        for symbol in ['NIFTY50', 'BANKNIFTY']:
            if run_test(symbol, 10) != 0:
                failed_tests.append(symbol)
    
    elif preset == 'extended':
        print("\n[Preset: EXTENDED] Multiple symbols, 20 cycles each")
        for symbol in ['NIFTY50', 'BANKNIFTY', 'FINNIFTY']:
            if run_test(symbol, 20) != 0:
                failed_tests.append(symbol)
    
    elif preset == 'stress':
        print("\n[Preset: STRESS] 100 cycles for stability testing")
        if run_test('NIFTY50', 100) != 0:
            failed_tests.append('NIFTY50 (stress)')
    
    elif preset == 'ci':
        print("\n[Preset: CI/CD] 10 cycles, minimal output")
        if run_test('NIFTY50', 10, verbose=False) != 0:
            failed_tests.append('CI test')
    
    else:
        print(f"Unknown preset: {preset}")
        print("Available: quick, standard, extended, stress, ci")
        return 1
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    if not failed_tests:
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {len(failed_tests)} test(s) failed:")
        for test in failed_tests:
            print(f"  - {test}")
        return 1


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        preset = sys.argv[1]
    else:
        preset = 'quick'
    
    return run_preset(preset)


if __name__ == '__main__':
    sys.exit(main())
