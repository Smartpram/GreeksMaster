#!/usr/bin/env python3
"""
Test script to debug Breeze API historical data endpoint
"""
import os
import sys
import logging
from datetime import datetime, timedelta
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.breeze_api import BreezeAPIService
from app.config import Config

def test_historical_data():
    """Test various historical data calls"""
    
    logger.info("=" * 80)
    logger.info("BREEZE API HISTORICAL DATA TEST")
    logger.info("=" * 80)
    
    # Initialize API service
    api = BreezeAPIService()
    
    # Test 1: Authenticate
    logger.info("\n1️⃣ Testing Authentication...")
    auth_result = api.authenticate()
    if auth_result.get('success'):
        logger.info(f"✅ Authentication successful: {auth_result.get('user_name')}")
    else:
        logger.error(f"❌ Authentication failed: {auth_result}")
        return
    
    # Test 2: Try different stock codes with 'day' interval
    test_cases = [
        # (stock_code, exchange, product_type, interval, days_back)
        ("HDFCBANK", "NSE", "cash", "day", 30),
        ("ICICIBANK", "NSE", "cash", "day", 30),
        ("INFY", "NSE", "cash", "day", 30),
        ("TCS", "NSE", "cash", "day", 30),
        ("RELIANCE", "NSE", "cash", "day", 30),
        ("NIFTY", "NSE", "cash", "day", 30),
    ]
    
    for i, (stock_code, exchange, product, interval, days) in enumerate(test_cases, 1):
        logger.info(f"\n{i+1}️⃣ Testing: {stock_code}")
        logger.info(f"   Exchange: {exchange}, Product: {product}, Interval: {interval}, Days: {days}")
        
        result = api.get_historical_data(
            stock_code=stock_code,
            exchange_code=exchange,
            product_type=product,
            interval=interval,
            days_back=days
        )
        
        if result.get('success'):
            data_count = len(result.get('data', []))
            logger.info(f"   ✅ SUCCESS: Got {data_count} bars")
            if data_count > 0:
                logger.info(f"      First bar: {result['data'][0]}")
        else:
            error = result.get('error') or result.get('warning')
            logger.warning(f"   ⚠️  FAILED: {error}")
    
    # Test 3: Try with explicit dates
    logger.info(f"\n{len(test_cases)+2}️⃣ Testing: HDFCBANK with explicit dates")
    to_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')
    from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    
    logger.info(f"   From: {from_date}")
    logger.info(f"   To: {to_date}")
    
    result = api.get_historical_data(
        stock_code="HDFCBANK",
        exchange_code="NSE",
        product_type="cash",
        interval="day",
        from_date=from_date,
        to_date=to_date
    )
    
    if result.get('success'):
        data_count = len(result.get('data', []))
        logger.info(f"   ✅ SUCCESS: Got {data_count} bars")
    else:
        error = result.get('error') or result.get('warning')
        logger.warning(f"   ⚠️  FAILED: {error}")
    
    logger.info("\n" + "=" * 80)
    logger.info("TEST COMPLETED")
    logger.info("=" * 80)

if __name__ == '__main__':
    try:
        test_historical_data()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
