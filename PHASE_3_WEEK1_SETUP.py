#!/usr/bin/env python3
"""
🚀 PHASE 3 WEEK 1 - ML MODEL TRAINING IMPLEMENTATION
Train XGBoost, Random Forest, and Ensemble models on historical data

Timeline: Week 1
Objective: Train prediction engine on 2+ years of historical data

Components:
  1. Data Collection (data_collector.py)
  2. Feature Engineering (using feature_engine.py)
  3. Model Training (training_engine.py)
  4. Model Validation
  5. Model Persistence
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'PHASE_3_WEEK1_LOG_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def phase3_week1_plan():
    """Display Phase 3 Week 1 implementation plan"""
    
    print_header("🚀 PHASE 3 WEEK 1 - ML MODEL TRAINING PLAN")
    
    plan = """
OBJECTIVE:
  Train XGBoost, Random Forest, and Ensemble models on 2+ years of data
  Generate feature matrix with 15+ technical indicators
  Validate models with cross-validation
  Save trained models for production use

TIMELINE:
  Monday-Wednesday: Data Collection & Feature Engineering
  Thursday-Friday: Model Training & Validation

ACTIVITIES:

1️⃣  DATA COLLECTION (Monday)
   Files: app/ml_models/data_collector.py
   Tasks:
     • Collect 2+ years of historical OHLCV data
     • Support multiple symbols (NIFTY50, BANKNIFTY, FINNIFTY)
     • Validate data quality
     • Save to CSV for training
   
   Command:
     python app/ml_models/data_collector.py

2️⃣  FEATURE ENGINEERING (Tuesday)
   Files: app/feature_engine.py (already built)
   Tasks:
     • Generate 15+ technical indicators
     • Create feature matrix from OHLCV data
     • Create labels (next 1-hour direction)
     • Remove NaN and invalid rows
   
   Features:
     ✓ Trend: SMA20, SMA50, SMA200, EMA12, EMA26
     ✓ Momentum: RSI, MACD, Stochastic
     ✓ Volatility: ATR, Bollinger Bands
     ✓ Volume: Volume ratio, SMA volume
     ✓ Price action: High-low ratio, close position

3️⃣  MODEL TRAINING (Wednesday-Thursday)
   Files: app/ml_models/training_engine.py
   Tasks:
     • Train XGBoost model (n_estimators=100)
     • Train Random Forest model (n_estimators=100)
     • Create Ensemble voting model
     • Split data: 80% train, 20% test
   
   Models:
     ✓ XGBoost: Fast, accurate, handles non-linearity
     ✓ Random Forest: Robust, interpretable
     ✓ Ensemble: Voting combination of both

4️⃣  MODEL VALIDATION (Thursday)
   Tasks:
     • Cross-validation (5-fold)
     • Confusion matrix on test set
     • Classification report (precision, recall, F1)
     • Feature importance analysis
   
   Target Metrics:
     ✓ Accuracy: >55% (better than random 33%)
     ✓ Precision: >50% for UP predictions
     ✓ Recall: >50% for UP predictions

5️⃣  MODEL PERSISTENCE (Friday)
   Tasks:
     • Save XGBoost model (.joblib)
     • Save Random Forest model (.joblib)
     • Save feature scaler (.joblib)
     • Save metadata (features, performance, date)
   
   Location: app/ml_models/trained_models/
   Files:
     • NIFTY50_xgboost_model.joblib
     • NIFTY50_random_forest_model.joblib
     • NIFTY50_scaler.joblib
     • NIFTY50_metadata.json

DELIVERABLES:
  ✓ Trained models (XGBoost + RF + Ensemble)
  ✓ Training report with metrics
  ✓ Feature importance analysis
  ✓ Cross-validation results
  ✓ Ready for backtesting

DEPENDENCIES:
  ✓ app/feature_engine.py (feature computation)
  ✓ app/ml_models/data_collector.py (data collection)
  ✓ app/ml_models/training_engine.py (model training)
  ✓ requirements: xgboost, scikit-learn, joblib

SUCCESS CRITERIA:
  ✓ Models train without errors
  ✓ Accuracy > 55% (better than baseline 33%)
  ✓ Cross-validation scores consistent
  ✓ Models saved successfully
  ✓ Ready to load in prediction_engine.py
"""
    
    print(plan)


def check_dependencies():
    """Check if required packages are installed"""
    
    print_header("📦 CHECKING DEPENDENCIES")
    
    required_packages = {
        'xgboost': 'Machine learning model',
        'scikit-learn': 'ML algorithms and validation',
        'joblib': 'Model serialization',
        'pandas': 'Data manipulation',
        'numpy': 'Numerical computing'
    }
    
    missing = []
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"✓ {package:20} OK - {description}")
        except ImportError:
            print(f"✗ {package:20} MISSING - {description}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    print("\n✓ All dependencies available")
    return True


def create_directory_structure():
    """Create required directories"""
    
    print_header("📁 CREATING DIRECTORY STRUCTURE")
    
    dirs = [
        'app/ml_models/trained_models',
        'data/training',
        'reports/training'
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {dir_path}")


def display_next_steps():
    """Display next steps for Phase 3 Week 1"""
    
    print_header("📋 NEXT STEPS - PHASE 3 WEEK 1 EXECUTION")
    
    steps = """
IMMEDIATE ACTIONS:

1. DATA COLLECTION
   Command: python app/ml_models/data_collector.py
   Expected: Collects 2+ years of OHLCV data for each symbol
   Output: data/training/NIFTY50_training_data_*.csv

2. MODEL TRAINING
   Command: python -c "
from app.ml_models.training_engine import ModelTrainer
from app.ml_models.data_collector import DataCollector

# Collect data
collector = DataCollector('NIFTY50')
df = collector.collect_from_breeze_api(days=730)

# Generate features
trainer = ModelTrainer('NIFTY50')
features, labels = trainer.generate_features(df)

# Train models
results = trainer.train_models(features, labels)

# Validate
validation = trainer.validate_models()

# Save
trainer.save_models()

# Report
report = trainer.generate_report(validation)
print(report)
"
   Expected: All models trained and saved
   Output: app/ml_models/trained_models/NIFTY50_*.joblib

3. VERIFY MODELS
   Command: ls -la app/ml_models/trained_models/
   Expected: See model files (.joblib), scaler, metadata.json
   
4. LOAD MODELS IN PREDICTION ENGINE
   Update: app/ml_models/prediction_engine.py
   Add: Load trained models from disk
   Test: Verify predictions work with trained models

MONITORING:
  • Watch training log for accuracy > 55%
  • Check cross-validation scores are consistent
  • Verify no memory errors during training
  • Confirm all models saved successfully

TROUBLESHOOTING:
  If data collection fails:
    → Check Breeze API credentials
    → Use synthetic data (already implemented)
    → Or load from existing CSV files
  
  If training is slow:
    → Reduce n_estimators (try 50 instead of 100)
    → Use fewer symbols initially
    → Run on GPU if available
  
  If memory errors:
    → Process data in batches
    → Reduce max_depth in models
    → Use sampling for initial training

COMPLETION CRITERIA:
  ✓ Data collected: 2+ years for NIFTY50, BANKNIFTY
  ✓ Models trained: XGBoost + RF + Ensemble
  ✓ Accuracy: >55% on test set
  ✓ Cross-validation: Consistent scores (diff < 5%)
  ✓ Models saved: Ready to load in production
  ✓ Metadata saved: Features, performance, date

Timeline: 1 week (Monday - Friday)
Status: READY TO IMPLEMENT
"""
    
    print(steps)


def main():
    """Main Phase 3 Week 1 setup"""
    
    print("\n" + "="*70)
    print("  🚀 PHASE 3 - PRODUCTION DEPLOYMENT")
    print("  Week 1: ML Model Training")
    print("="*70)
    
    # Display plan
    phase3_week1_plan()
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Missing required dependencies. Install and try again.")
        return 1
    
    # Create directories
    create_directory_structure()
    
    # Display next steps
    display_next_steps()
    
    # Summary
    print_header("✅ PHASE 3 WEEK 1 - SETUP COMPLETE")
    
    summary = """
READY TO START TRAINING:

1. Ensure you have 2+ years of historical data
2. Run data collection script to prepare data
3. Execute model training
4. Validate models meet success criteria
5. Save trained models for production

Key Files:
  ✓ app/ml_models/data_collector.py
  ✓ app/ml_models/training_engine.py
  ✓ app/ml_models/trained_models/ (output directory)

Next Phase: Week 2 - Backtesting with AI
Estimated Timeline: 1 week

Questions or Issues?
  See: PHASE_3_DEPLOYMENT_ROADMAP.md
  Or: LIVE_DATA_TESTING_GUIDE.md
"""
    
    print(summary)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
