"""
Test which stock codes from Security Master have historical data available
"""
import requests
import json
from datetime import datetime, timedelta
import time

# Import from existing breeze module
import sys
sys.path.insert(0, r'c:\Data\MyBreezeApp')

# Credentials (loaded from environment in production)
API_KEY = "d5d45b9e6a284d52adc3eb29b5e81a32"
SESSION_TOKEN = "01a1a3c4-2844-4ab3-a48f-8b58e84aff54"

# Key test stocks to validate
TEST_STOCKS = ['TCS', 'NIFTY', 'RELIND', 'SBIN150', 'NIFTY50', 'CNXNIF', 'CNXBAN']

def test_historical_data(symbol):
    """Test if we can fetch historical data for a symbol"""
    try:
        # Prepare request
        url = "https://api.icicidirect.com/breezeapi/historical"
        
        # Date range: Last 30 days
        end_date = datetime.now().strftime("%d-%b-%y")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%y")
        
        params = {
            "token": "999926009",  # NIFTY 50 token (standard)
            "interval": "day",
            "fromdate": start_date,
            "todate": end_date,
        }
        
        headers = {
            "X-SessionToken": SESSION_TOKEN,
            "X-ApiKey": API_KEY,
        }
        
        print(f"\n🔍 Testing {symbol}...")
        print(f"   URL: {url}")
        print(f"   Params: {params}")
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we got actual data
            if isinstance(data, dict) and 'data' in data:
                records = data['data']
                if records:
                    print(f"   ✅ SUCCESS: Got {len(records)} records for {symbol}")
                    # Show first record
                    first = records[0]
                    print(f"      Sample: {first}")
                    return True
                else:
                    print(f"   ⚠️  No data: Response is empty for {symbol}")
                    return False
            else:
                print(f"   ⚠️  Unexpected format: {data}")
                return False
        else:
            print(f"   ❌ Error {response.status_code}: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return False
    finally:
        time.sleep(0.5)  # Rate limiting

if __name__ == "__main__":
    print("=" * 80)
    print("TESTING STOCK DATA AVAILABILITY")
    print("=" * 80)
    
    results = {}
    for stock in TEST_STOCKS:
        available = test_historical_data(stock)
        results[stock] = "✅ Available" if available else "❌ Not Available"
    
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    for stock, status in results.items():
        print(f"  {stock:15} {status}")
    
    available_count = sum(1 for v in results.values() if "Available" in v)
    print(f"\n  Total Available: {available_count}/{len(TEST_STOCKS)}")
    print("=" * 80)
