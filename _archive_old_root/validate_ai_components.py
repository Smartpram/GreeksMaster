"""
PHASE 2 IMPLEMENTATION COMPLETE - VALIDATION SCRIPT
===================================================

This script validates all Phase 2 components are properly integrated and ready.

Features:
1. Checks all Phase 2 files exist
2. Validates module imports
3. Tests component initialization
4. Runs quick smoke tests
5. Generates implementation report

Usage:
    python validate_ai_system|AISystem.py
"""

import os
import sys
import importlib
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ai_system|AISystemValidator:
    """Validate Phase 2 implementation"""
    
    def __init__(self, base_path='c:/Data/GreeksMaster'):
        self.base_path = base_path
        self.results = {
            'files_exist': {},
            'imports_success': {},
            'initialization_success': {},
            'tests_passed': {},
            'errors': []
        }
    
    def run_all_validations(self):
        """Run complete validation suite"""
        logger.info("=" * 70)
        logger.info("PHASE 2 IMPLEMENTATION VALIDATION")
        logger.info("=" * 70)
        logger.info(f"Start Time: {datetime.now()}")
        logger.info("")
        
        # Phase 1: Check files exist
        logger.info("STEP 1: Checking Phase 2 files...")
        self.validate_files_exist()
        self.print_results("Files", self.results['files_exist'])
        
        # Phase 2: Check imports
        logger.info("\nSTEP 2: Validating imports...")
        self.validate_imports()
        self.print_results("Imports", self.results['imports_success'])
        
        # Phase 3: Check initialization
        logger.info("\nSTEP 3: Testing component initialization...")
        self.validate_initialization()
        self.print_results("Initialization", self.results['initialization_success'])
        
        # Phase 4: Run smoke tests
        logger.info("\nSTEP 4: Running smoke tests...")
        self.run_smoke_tests()
        self.print_results("Smoke Tests", self.results['tests_passed'])
        
        # Phase 5: Generate report
        logger.info("\nSTEP 5: Generating validation report...")
        self.generate_report()
    
    def validate_files_exist(self):
        """Check all Phase 2 files exist"""
        files_to_check = [
            'app/safety/emergency_stop.py',
            'app/ml_models/prediction_engine.py',
            'app/feature_engine.py',
            'app/ai_system|AISystem_integration.py',
            'test_ai_system|AISystem_complete.py'
        ]
        
        for filepath in files_to_check:
            full_path = os.path.join(self.base_path, filepath)
            exists = os.path.exists(full_path)
            self.results['files_exist'][filepath] = exists
            
            if exists:
                size = os.path.getsize(full_path)
                logger.info(f"  ✓ {filepath} ({size:,} bytes)")
            else:
                logger.error(f"  ✗ {filepath} NOT FOUND")
                self.results['errors'].append(f"File not found: {filepath}")
    
    def validate_imports(self):
        """Validate all imports work"""
        # Add app to path
        sys.path.insert(0, self.base_path)
        
        modules_to_import = [
            ('app.safety.emergency_stop', 'KillSwitchManager'),
            ('app.ml_models.prediction_engine', 'PredictionEngine'),
            ('app.feature_engine', 'FeatureEngine'),
            ('app.ai_system|AISystem_integration', 'ai_system|AISystemIntegration'),
        ]
        
        for module_name, class_name in modules_to_import:
            try:
                module = importlib.import_module(module_name)
                cls = getattr(module, class_name, None)
                
                if cls:
                    self.results['imports_success'][module_name] = True
                    logger.info(f"  ✓ {module_name}.{class_name}")
                else:
                    self.results['imports_success'][module_name] = False
                    logger.error(f"  ✗ {class_name} not found in {module_name}")
                    self.results['errors'].append(f"Class {class_name} not found in {module_name}")
            except Exception as e:
                self.results['imports_success'][module_name] = False
                logger.error(f"  ✗ Failed to import {module_name}: {e}")
                self.results['errors'].append(f"Import error in {module_name}: {str(e)}")
    
    def validate_initialization(self):
        """Test component initialization"""
        try:
            # Test Emergency Stop
            from app.safety.emergency_stop import KillSwitchManager
            ks = KillSwitchManager()
            assert ks is not None
            self.results['initialization_success']['KillSwitchManager'] = True
            logger.info("  ✓ KillSwitchManager initialized")
        except Exception as e:
            self.results['initialization_success']['KillSwitchManager'] = False
            logger.error(f"  ✗ KillSwitchManager init failed: {e}")
            self.results['errors'].append(f"KillSwitchManager init: {str(e)}")
        
        try:
            # Test Feature Engine
            from app.feature_engine import FeatureEngine
            from unittest.mock import Mock
            
            mock_provider = Mock()
            mock_provider.get_historical_data.return_value = None
            
            fe = FeatureEngine(mock_provider)
            assert fe is not None
            self.results['initialization_success']['FeatureEngine'] = True
            logger.info("  ✓ FeatureEngine initialized")
        except Exception as e:
            self.results['initialization_success']['FeatureEngine'] = False
            logger.error(f"  ✗ FeatureEngine init failed: {e}")
            self.results['errors'].append(f"FeatureEngine init: {str(e)}")
        
        try:
            # Test Prediction Engine
            from app.ml_models.prediction_engine import PredictionEngine
            
            pe = PredictionEngine()
            assert pe is not None
            self.results['initialization_success']['PredictionEngine'] = True
            logger.info("  ✓ PredictionEngine initialized")
        except Exception as e:
            self.results['initialization_success']['PredictionEngine'] = False
            logger.error(f"  ✗ PredictionEngine init failed: {e}")
            self.results['errors'].append(f"PredictionEngine init: {str(e)}")
    
    def run_smoke_tests(self):
        """Run quick smoke tests"""
        try:
            from app.safety.emergency_stop import KillSwitchManager
            
            ks = KillSwitchManager()
            
            # Test basic operations
            assert not ks.is_active(), "Emergency Stop should start inactive"
            assert ks.get_reason() is None, "No reason should exist initially"
            
            self.results['tests_passed']['KillSwitch_basic_ops'] = True
            logger.info("  ✓ Emergency Stop basic operations")
        except Exception as e:
            self.results['tests_passed']['KillSwitch_basic_ops'] = False
            logger.error(f"  ✗ Emergency Stop test failed: {e}")
            self.results['errors'].append(f"Emergency Stop test: {str(e)}")
        
        try:
            from app.feature_engine import FeatureEngine
            from unittest.mock import Mock
            import pandas as pd
            import numpy as np
            
            # Create mock data
            mock_provider = Mock()
            df = pd.DataFrame({
                'open': np.random.rand(100) * 100,
                'high': np.random.rand(100) * 100,
                'low': np.random.rand(100) * 100,
                'close': np.random.rand(100) * 100,
                'volume': np.random.randint(1000, 10000, 100)
            })
            mock_provider.get_historical_data.return_value = df
            mock_provider.get_options_chain.return_value = []
            
            fe = FeatureEngine(mock_provider)
            features = fe.compute_all_features('TEST')
            
            if features:
                assert hasattr(features, 'bullish_score'), "Missing bullish_score"
                assert 0 <= features.bullish_score <= 100, "Invalid bullish_score range"
                self.results['tests_passed']['FeatureEngine_compute'] = True
                logger.info(f"  ✓ Feature engine computation (score: {features.bullish_score:.1f})")
            else:
                self.results['tests_passed']['FeatureEngine_compute'] = False
                logger.error("  ✗ Feature engine returned None")
        except Exception as e:
            self.results['tests_passed']['FeatureEngine_compute'] = False
            logger.error(f"  ✗ Feature engine test failed: {e}")
            self.results['errors'].append(f"Feature engine test: {str(e)}")
    
    def generate_report(self):
        """Generate validation report"""
        logger.info("\n" + "=" * 70)
        logger.info("VALIDATION REPORT")
        logger.info("=" * 70)
        
        # Summary
        total_checks = (
            len(self.results['files_exist']) +
            len(self.results['imports_success']) +
            len(self.results['initialization_success']) +
            len(self.results['tests_passed'])
        )
        
        passed_checks = (
            sum(1 for v in self.results['files_exist'].values() if v) +
            sum(1 for v in self.results['imports_success'].values() if v) +
            sum(1 for v in self.results['initialization_success'].values() if v) +
            sum(1 for v in self.results['tests_passed'].values() if v)
        )
        
        logger.info(f"\nTotal Checks: {total_checks}")
        logger.info(f"Passed: {passed_checks}")
        logger.info(f"Failed: {total_checks - passed_checks}")
        logger.info(f"Success Rate: {(passed_checks/total_checks)*100:.1f}%")
        
        # Errors
        if self.results['errors']:
            logger.error(f"\nErrors ({len(self.results['errors'])}):")
            for error in self.results['errors']:
                logger.error(f"  - {error}")
        else:
            logger.info("\n✓ No errors found!")
        
        # Overall status
        logger.info("\n" + "=" * 70)
        if passed_checks == total_checks:
            logger.info("✓ PHASE 2 VALIDATION PASSED - ALL CHECKS OK")
            logger.info("Ready for testing and deployment")
        else:
            logger.warning("⚠ PHASE 2 VALIDATION INCOMPLETE - REVIEW ERRORS")
        logger.info("=" * 70)
        
        return passed_checks == total_checks
    
    def print_results(self, category, results):
        """Print results for a category"""
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        logger.info(f"  → {passed}/{total} passed")


def main():
    """Run validation"""
    validator = ai_system|AISystemValidator()
    success = False
    
    try:
        validator.run_all_validations()
        success = True
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
