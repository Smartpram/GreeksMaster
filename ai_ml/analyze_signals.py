#!/usr/bin/env python3
"""
Diagnostic script to analyze signal scores and validation
Debug why no trades are being executed
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from app.services.breeze_api import BreezeAPIService
from app.strategies.enhanced_signal_confirmation import EnhancedSignalConfirmation

def analyze_signals(stock_code: str = 'RELIND'):
    """Analyze signal validation for debugging"""
    logger.info(f"\n{'='*80}")
    logger.info(f"SIGNAL ANALYSIS: {stock_code}")
    logger.info(f"{'='*80}\n")
    
    # Authenticate
    breeze = BreezeAPIService()
    auth = breeze.authenticate()
    if not auth['success']:
        logger.error("Authentication failed")
        return
    
    # Fetch data
    result = breeze.get_historical_data(stock_code=stock_code, interval="day", days_back=252)
    if not result['success']:
        logger.error("Data fetch failed")
        return
    
    # Prepare DataFrame
    df = pd.DataFrame(result['data'])
    
    # Handle datetime column - it's already a datetime
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
    elif 'date' in df.columns:
        df['datetime'] = pd.to_datetime(df['date'], format='%d-%b-%Y')
    
    df = df.set_index('datetime').sort_index()
    df.columns = df.columns.str.lower()
    
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    logger.info(f"Data loaded: {len(df)} bars | {df.index.min().date()} to {df.index.max().date()}\n")
    
    # Initialize enhanced signals
    enhanced_signals = EnhancedSignalConfirmation(df)
    
    # Analyze signals at different points
    test_points = [20, 40, 60, 80, 100, 120]
    
    logger.info("SIGNAL VALIDATION ANALYSIS")
    logger.info("-" * 100)
    logger.info(f"{'Bar':<6} {'Date':<12} {'Price':<10} {'Regime':<15} {'Score':<8} {'Valid':<8} {'Components'}")
    logger.info("-" * 100)
    
    all_scores = []
    all_valid = []
    
    for bar_idx in range(20, len(df)):
        validation = enhanced_signals.validate_entry_signal(bar_idx, 'BUY')
        regime = enhanced_signals.detect_regime(bar_idx)
        
        date = df.index[bar_idx].strftime('%Y-%m-%d')
        price = df['close'].iloc[bar_idx]
        score = validation.get('overall_score', 0.0)
        is_valid = validation['valid']
        
        all_scores.append(score)
        all_valid.append(is_valid)
        
        # Print selected bars
        if bar_idx in test_points or score > 0.70 or score < 0.30 or bar_idx > len(df) - 10:
            components = ", ".join([f"{k}:{v:.2f}" for k, v in validation.get('scores', {}).items()])[:50]
            valid_text = "✓ YES" if is_valid else "✗ NO"
            logger.info(f"{bar_idx:<6} {date:<12} ₹{price:<8.0f} {regime.value:<15} {score:<8.2f} {valid_text:<8} {components}")
    
    # Summary statistics
    logger.info("\n" + "="*100)
    logger.info("SUMMARY STATISTICS")
    logger.info("="*100)
    logger.info(f"Average Score:          {np.mean(all_scores):.3f}")
    logger.info(f"Min Score:              {np.min(all_scores):.3f}")
    logger.info(f"Max Score:              {np.max(all_scores):.3f}")
    logger.info(f"Median Score:           {np.median(all_scores):.3f}")
    logger.info(f"Std Dev:                {np.std(all_scores):.3f}")
    logger.info(f"\nScore Distribution:")
    logger.info(f"  > 0.70 (high):        {sum(1 for s in all_scores if s > 0.70)} bars")
    logger.info(f"  0.60-0.70:            {sum(1 for s in all_scores if 0.60 <= s <= 0.70)} bars")
    logger.info(f"  0.50-0.60:            {sum(1 for s in all_scores if 0.50 <= s < 0.60)} bars")
    logger.info(f"  < 0.50 (low):         {sum(1 for s in all_scores if s < 0.50)} bars")
    
    logger.info(f"\nValid Signals (score >= 0.60):  {sum(all_valid)} out of {len(all_valid)} bars")
    
    # Recommendations
    logger.info("\n" + "="*100)
    logger.info("RECOMMENDATIONS")
    logger.info("="*100)
    
    high_score_pct = sum(1 for s in all_scores if s > 0.70) / len(all_scores) * 100
    
    if high_score_pct < 5:
        logger.info("⚠️  Low high-score signals detected (<5%)")
        logger.info("   → Consider lowering threshold from 0.60 to 0.50")
        logger.info("   → Or review component weights in EnhancedSignalConfirmation")
    elif high_score_pct > 20:
        logger.info("✓ Good number of strong signals (>20%)")
        logger.info("   → Current threshold (0.60) appears reasonable")
    else:
        logger.info("→ Moderate signal strength")
        logger.info("   → Threshold might need fine-tuning based on desired trade frequency")
    
    logger.info("\n")

if __name__ == "__main__":
    analyze_signals('RELIND')
