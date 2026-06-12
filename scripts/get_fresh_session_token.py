#!/usr/bin/env python3
"""
Helper script to get a fresh Breeze API session token
Run this when you get "Resource not available" errors
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.breeze_api import BreezeAPIService
from app.config import Config
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_fresh_token():
    """Get fresh session token instructions"""
    logger.info("\n" + "="*80)
    logger.info("BREEZE API SESSION TOKEN REFRESH")
    logger.info("="*80 + "\n")
    
    breeze = BreezeAPIService()
    result = breeze.login()
    
    if result['success']:
        logger.info("📋 STEP 1: Open this URL in your browser:")
        logger.info(f"   {result['login_url']}\n")
        
        logger.info("📋 STEP 2: After login, you'll see your session token")
        logger.info("   Copy the session token from the browser\n")
        
        logger.info("📋 STEP 3: Update the .env file:")
        logger.info("   BREEZE_SESSION_TOKEN=<paste_your_token_here>\n")
        
        logger.info("📋 STEP 4: Then run the backtest again:")
        logger.info("   python backtest_with_breeze_real_data.py\n")
        
        logger.info("="*80)
        logger.info("Note: Session tokens expire after inactivity. If you get")
        logger.info("'Resource not available' error, repeat these steps.")
        logger.info("="*80 + "\n")
    else:
        logger.error(f"Error: {result.get('error')}")

if __name__ == "__main__":
    get_fresh_token()
