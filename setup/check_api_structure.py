#!/usr/bin/env python3
"""Quick check of API response structure"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.breeze_api import BreezeAPIService

breeze = BreezeAPIService()
auth = breeze.authenticate()
if auth['success']:
    result = breeze.get_historical_data(stock_code='RELIND', interval="day", days_back=10)
    if result['success']:
        data = result['data']
        print(f"Number of records: {len(data)}")
        print(f"\nFirst record keys:")
        for key in data[0].keys():
            print(f"  - {key}: {data[0][key]}")
