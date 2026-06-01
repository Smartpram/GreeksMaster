#!/usr/bin/env python3
"""
Debug script to test different login/authentication approaches
"""
import requests
import json
import hashlib
from datetime import datetime, timezone

BASE_URL = "https://api.icicidirect.com/breezeapi/api/v1"

# Credentials from .env
API_KEY = "7V893A3587i6I15m2!614N97777)$1y="
SECRET_KEY = "8y37tN4806822W8q^8Z0DQ62722E343G"
USER_ID = "PRAUZRKW"
PASSWORD = "Smartpram2@"

def test_simple_login():
    """Test simple login without checksum"""
    print("\n" + "=" * 70)
    print("TEST 1: Simple POST to /login (no checksum)")
    print("=" * 70)
    
    payload = {
        "userid": USER_ID,
        "password": PASSWORD,
        "appkey": API_KEY
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    url = f"{BASE_URL}/login"
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

def test_login_with_iso_checksum():
    """Test login with ISO format timestamp checksum"""
    print("\n" + "=" * 70)
    print("TEST 2: POST to /login with ISO timestamp checksum")
    print("=" * 70)
    
    payload = {
        "userid": USER_ID,
        "password": PASSWORD,
        "appkey": API_KEY
    }
    
    # Generate ISO timestamp
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    
    # JSONPostData as compact string
    json_post_data = json.dumps(payload, separators=(',', ':'))
    
    # Checksum: SHA256(timestamp + JSONPostData + secret_key)
    checksum_string = timestamp + json_post_data + SECRET_KEY
    checksum = hashlib.sha256(checksum_string.encode()).hexdigest()
    
    outer_payload = {
        "AppKey": API_KEY,
        "time_stamp": timestamp,
        "JSONPostData": json_post_data,
        "Checksum": checksum
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Checksum": f"token {checksum}",
        "X-Timestamp": timestamp,
        "X-AppKey": API_KEY
    }
    
    url = f"{BASE_URL}/login"
    print(f"URL: {url}")
    print(f"Timestamp: {timestamp}")
    print(f"Checksum: {checksum}")
    print(f"Payload: {json.dumps(outer_payload, indent=2)}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    
    try:
        response = requests.post(url, json=outer_payload, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

def test_login_with_dd_mon_checksum():
    """Test login with DD-Mon-YYYY HH:MM:SS timestamp checksum"""
    print("\n" + "=" * 70)
    print("TEST 3: POST to /login with DD-Mon-YYYY timestamp checksum")
    print("=" * 70)
    
    payload = {
        "userid": USER_ID,
        "password": PASSWORD,
        "appkey": API_KEY
    }
    
    # Generate DD-Mon-YYYY HH:MM:SS timestamp (IST, which is UTC+5:30)
    from datetime import timedelta, timezone
    now_utc = datetime.now(timezone.utc)
    # Convert to IST (UTC+5:30)
    ist_offset = timedelta(hours=5, minutes=30)
    ist_tz = timezone(ist_offset)
    now_ist = now_utc.astimezone(ist_tz)
    timestamp = now_ist.strftime('%d-%b-%Y %H:%M:%S')
    
    # JSONPostData as compact string
    json_post_data = json.dumps(payload, separators=(',', ':'))
    
    # Checksum: SHA256(timestamp + JSONPostData + secret_key)
    checksum_string = timestamp + json_post_data + SECRET_KEY
    checksum = hashlib.sha256(checksum_string.encode()).hexdigest()
    
    outer_payload = {
        "AppKey": API_KEY,
        "time_stamp": timestamp,
        "JSONPostData": json_post_data,
        "Checksum": checksum
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Checksum": f"token {checksum}",
        "X-Timestamp": timestamp,
        "X-AppKey": API_KEY
    }
    
    url = f"{BASE_URL}/login"
    print(f"URL: {url}")
    print(f"Timestamp: {timestamp}")
    print(f"Checksum: {checksum}")
    print(f"Payload: {json.dumps(outer_payload, indent=2)}")
    
    try:
        response = requests.post(url, json=outer_payload, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

def test_connectivity():
    """Test basic connectivity to API"""
    print("\n" + "=" * 70)
    print("TEST 0: Basic connectivity check")
    print("=" * 70)
    
    try:
        response = requests.get("https://api.icicidirect.com/breezeapi/documents/index.html", timeout=10)
        print(f"Status: {response.status_code}")
        print("✓ API server is reachable")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_connectivity()
    test_simple_login()
    test_login_with_iso_checksum()
    test_login_with_dd_mon_checksum()
