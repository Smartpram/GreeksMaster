#!/usr/bin/env python3
"""
Download and parse Breeze API Security Master file
Contains the correct stock codes for all instruments
Updated daily at 8:00 AM IST

Official URL: https://directlink.icicidirect.com/NewSecurityMaster/SecurityMaster.zip
Source: https://api.icicidirect.com/breezeapi/documents/index.html?python#instruments
"""
import os
import zipfile
import csv
import requests

def download_security_master():
    """Download Security Master file from Breeze API"""
    
    print("=" * 80)
    print("BREEZE API SECURITY MASTER DOWNLOADER")
    print("=" * 80)
    
    # Official URL from Breeze API documentation
    # Updated daily at 8:00 AM IST
    url = "https://directlink.icicidirect.com/NewSecurityMaster/SecurityMaster.zip"
    download_path = "SecurityMaster.zip"
    
    print(f"\n📥 Downloading Security Master from:")
    print(f"   {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        print(f"✅ Downloaded successfully: {len(response.content) / 1024 / 1024:.2f} MB")
        
        # Save the zip file
        with open(download_path, 'wb') as f:
            f.write(response.content)
        print(f"✅ Saved: {download_path}")
        
        # Extract the zip file
        print(f"\n📦 Extracting archive...")
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            zip_ref.extractall()
            files_extracted = zip_ref.namelist()
        print(f"✅ Extracted {len(files_extracted)} files")
        
        # Parse and display sample
        print(f"\n📊 Parsing Security Master files...")
        
        # Find stocks with HDFCBANK, ICICIBANK, TCS, NIFTY, etc.
        search_terms = ['HDFCBANK', 'ICICIBANK', 'TCS', 'NIFTY', 'INFY', 'RELIANCE', 'SBIN']
        found_stocks = {}
        total_rows = 0
        
        # Process NSE and NFO master files (most relevant for us)
        master_files = [
            ('NSEScripMaster.txt', 'NSE'),
            ('FONSEScripMaster.txt', 'NFO')
        ]
        
        for master_file, exchange_type in master_files:
            if not os.path.exists(master_file):
                print(f"   Skipping {master_file} (not found)")
                continue
            
            print(f"   Processing {master_file}...")
            
            try:
                with open(master_file, 'r', encoding='utf-8', errors='ignore') as f:
                    # Use csv.DictReader which handles quoted fields properly
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        total_rows += 1
                        # Fields in NSE and NFO files have quotes and spaces in column names
                        # ShortName is the actual stock code (e.g., TCS, INFY, RELIND)
                        # Symbol field is often empty
                        stock_code = ''
                        company_name = ''
                        
                        # Try to find the right fields
                        for key in row.keys():
                            key_clean = key.strip().strip('"')
                            if 'ShortName' in key_clean:
                                stock_code = (row.get(key) or '').strip().strip('"')
                            if 'CompanyName' in key_clean or 'Company' in key_clean:
                                company_name = (row.get(key) or '').strip().strip('"')
                        
                        # Look for our search terms
                        for term in search_terms:
                            search_upper = term.upper()
                            if (search_upper in stock_code.upper() or 
                                search_upper in company_name.upper()):
                                if stock_code and stock_code not in found_stocks:
                                    found_stocks[stock_code] = {
                                        'stock_code': stock_code,
                                        'company_name': company_name,
                                        'exchange': exchange_type
                                    }
                                    break
            except Exception as e:
                print(f"   Error reading {master_file}: {e}")
        
        # Display results
        print(f"\n✅ Processed {total_rows} rows from Security Master files")
        print(f"\n🔍 Found {len(found_stocks)} stocks matching our search terms:")
        print("-" * 80)
        
        for stock_code in sorted(found_stocks.keys()):
            info = found_stocks[stock_code]
            print(f"\n Stock Code: {stock_code}")
            print(f"  Name: {info['company_name']}")
            print(f"  Exchange: {info['exchange']}")
        
        # Generate Python dict for easy use
        print("\n" + "=" * 80)
        print("💾 STOCK CODES FOR BACKTEST (Python dict format):")
        print("=" * 80)
        print("\nstocks_dict = {")
        for stock_code in sorted(found_stocks.keys()):
            info = found_stocks[stock_code]
            print(f"    '{stock_code}': {{")
            print(f"        'name': '{info['company_name']}',")
            print(f"        'exchange': '{info['exchange']}'")
            print(f"    }},")
        print("}")
        
        # Print as simple list for quick reference
        print("\n" + "=" * 80)
        print("📋 STOCK CODES (Simple List for Backtesting):")
        print("=" * 80)
        print("\nstocks_list = [")
        for stock_code in sorted(found_stocks.keys()):
            print(f"    '{stock_code}',")
        print("]")
        
        return found_stocks
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to download Security Master: {e}")
        print(f"\n💡 Manual Download:")
        print(f"   Visit: https://api.icicidirect.com/breezeapi/documents/index.html?python#instruments")
        print(f"   Download: SecurityMaster.zip")
        print(f"   Extract and parse manually")
        return None
    except Exception as e:
        print(f"❌ Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    try:
        stocks = download_security_master()
        
        if stocks:
            print("\n" + "=" * 80)
            print("✅ SECURITY MASTER DOWNLOADED AND PARSED SUCCESSFULLY")
            print("=" * 80)
            print(f"\nReady to use {len(stocks)} stock codes for backtesting!")
            print("\nNext steps:")
            print("1. Use the stock codes above in your backtest")
            print("2. Test historical data availability with test_breeze_historical.py")
            print("3. Run backtest with real data: python run_advanced_strategies_backtest.py")
        else:
            print("\n" + "=" * 80)
            print("❌ FAILED TO DOWNLOAD SECURITY MASTER")
            print("=" * 80)
            print("\nPlease download manually from:")
            print("https://directlink.icicidirect.com/NewSecurityMaster/SecurityMaster.zip")
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
