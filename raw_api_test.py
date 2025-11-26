#!/usr/bin/env python3
"""
Raw API Response Test for Breeze API
===================================

This test bypasses the BreezeConnect library and makes direct API calls
to see exactly what the ICICI servers are returning.
"""

import requests
import json
from datetime import datetime
import sys
import os

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_raw_api_calls():
    """Test raw API calls to ICICI Breeze endpoints"""
    
    print("🔍 RAW API RESPONSE TEST")
    print("=" * 40)
    
    try:
        from app.config import Config
        
        # Test parameters from your config
        api_key = Config.BREEZE_API_KEY
        secret_key = Config.BREEZE_SECRET_KEY
        session_token = Config.BREEZE_SESSION_TOKEN
        user_id = Config.BREEZE_USER_ID
        
        print(f"📋 Using credentials:")
        print(f"   API Key: {api_key[:10]}...")
        print(f"   Secret: {secret_key[:10]}...")
        print(f"   Session Token: {session_token}")
        print(f"   User ID: {user_id}")
        
        # Test 1: Direct session generation call
        print(f"\n🔐 TEST 1: Direct Session Generation")
        print("-" * 35)
        
        session_url = "https://api.icicidirect.com/breezeapi/api/v1/customerdetails"
        
        session_payload = {
            "SessionToken": session_token,
            "AppKey": api_key
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        print(f"   📤 Making POST request to: {session_url}")
        print(f"   📦 Payload: {session_payload}")
        
        try:
            response = requests.get(
                session_url,
                json=session_payload,
                headers=headers,
                timeout=30
            )
            
            print(f"   📥 Response Status: {response.status_code}")
            print(f"   📄 Response Headers:")
            for key, value in response.headers.items():
                if key.lower() in ['content-type', 'content-length', 'date']:
                    print(f"     {key}: {value}")
            
            print(f"   📋 Raw Response Text:")
            response_text = response.text
            print(f"     Length: {len(response_text)} characters")
            print(f"     First 500 chars: {response_text[:500]}")
            
            # Try to parse as JSON
            try:
                response_json = response.json()
                print(f"   ✅ JSON Parse Successful:")
                print(f"     Type: {type(response_json)}")
                
                if isinstance(response_json, dict):
                    print(f"     Keys: {list(response_json.keys())}")
                    for key, value in response_json.items():
                        if isinstance(value, str) and len(value) > 50:
                            print(f"     {key}: {str(value)[:50]}...")
                        else:
                            print(f"     {key}: {value}")
                else:
                    print(f"     Content: {response_json}")
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON Parse Failed: {e}")
                print(f"   📄 Raw text response:")
                print(f"     {response_text}")
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
        
        # Test 2: Try alternative session endpoint
        print(f"\n🔐 TEST 2: Alternative Session Endpoint")
        print("-" * 35)
        
        alt_url = "https://api.icicidirect.com/breezeapi/api/v1/sessionvalidation"
        
        alt_payload = {
            "SessionToken": session_token,
            "AppKey": api_key,
            "SecretKey": secret_key  # Include secret key
        }
        
        print(f"   📤 Trying alternative endpoint: {alt_url}")
        print(f"   📦 Payload with secret key included")
        
        try:
            response = requests.post(
                alt_url,
                json=alt_payload,
                headers=headers,
                timeout=30
            )
            
            print(f"   📥 Response Status: {response.status_code}")
            print(f"   📋 Response Text: {response.text[:200]}...")
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Alternative request failed: {e}")
        
        # Test 3: Check what BreezeConnect is actually doing
        print(f"\n🔍 TEST 3: BreezeConnect Internal Analysis")
        print("-" * 40)
        
        try:
            from breeze_connect import BreezeConnect
            
            # Create breeze instance
            breeze = BreezeConnect(api_key=api_key)
            
            # Check internal attributes
            print(f"   📋 BreezeConnect object attributes:")
            internal_attrs = [attr for attr in dir(breeze) if not attr.startswith('__')]
            print(f"     Available methods: {len(internal_attrs)}")
            
            # Key attributes to check
            key_attrs = ['api_key', 'base_url', 'session_token', 'user_id']
            for attr in key_attrs:
                if hasattr(breeze, attr):
                    value = getattr(breeze, attr)
                    if isinstance(value, str) and len(value) > 20:
                        print(f"     {attr}: {value[:20]}...")
                    else:
                        print(f"     {attr}: {value}")
                else:
                    print(f"     {attr}: Not found")
            
            # Try to intercept the actual API call
            print(f"\n   🔍 Attempting to trace generate_session call...")
            
            # Monkey patch requests to see what's being called
            original_request = requests.request
            
            def traced_request(method, url, **kwargs):
                print(f"     📤 {method} {url}")
                if 'json' in kwargs:
                    print(f"     📦 JSON Payload: {kwargs['json']}")
                result = original_request(method, url, **kwargs)
                print(f"     📥 Status: {result.status_code}")
                print(f"     📄 Response: {result.text[:100]}...")
                return result
            
            requests.request = traced_request
            
            try:
                # Now call generate_session
                result = breeze.generate_session(
                    api_secret=secret_key,
                    session_token=session_token
                )
                print(f"   🎯 generate_session result: {result}")
                print(f"   🎯 Result type: {type(result)}")
            finally:
                # Restore original request
                requests.request = original_request
            
        except Exception as e:
            print(f"   ❌ BreezeConnect analysis failed: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Raw API test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        print("🧪 Starting raw API response analysis...")
        print(f"⏰ Time: {datetime.now()}")
        
        test_raw_api_calls()
        
        print(f"\n" + "="*50)
        print("📊 RAW API TEST COMPLETE")
        print("🔍 Check the output above for API response details")
        print("="*50)
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Raw API test cancelled by user")
    except Exception as e:
        print(f"\n❌ Raw API test script error: {e}")
        import traceback
        traceback.print_exc()