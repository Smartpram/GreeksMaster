#!/usr/bin/env python3
"""
Network Connectivity Test for Breeze API
========================================

Test network connectivity and SSL issues that might affect Breeze API calls.
"""

import requests
import socket
import ssl
from datetime import datetime

def test_network_connectivity():
    """Test basic network connectivity"""
    
    print("🌐 NETWORK CONNECTIVITY TEST")
    print("=" * 40)
    
    # Test basic internet connectivity
    test_sites = [
        "https://www.google.com",
        "https://api.ipify.org",
        "https://httpbin.org/ip"
    ]
    
    print("🔍 Testing basic internet connectivity...")
    
    for site in test_sites:
        try:
            response = requests.get(site, timeout=10)
            if response.status_code == 200:
                print(f"   ✅ {site} - OK")
            else:
                print(f"   ⚠️  {site} - Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {site} - Error: {str(e)[:50]}...")
    
    # Test ICICI specific domains (if known)
    icici_domains = [
        "https://api.icicidirect.com",
        "https://breeze.icicidirect.com"
    ]
    
    print(f"\n🏦 Testing ICICI/Breeze domain connectivity...")
    
    for domain in icici_domains:
        try:
            response = requests.get(domain, timeout=10)
            print(f"   ✅ {domain} - Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {domain} - Error: {str(e)[:50]}...")

def test_breeze_with_debug():
    """Test Breeze API with detailed debugging"""
    
    print(f"\n🔍 BREEZE API DEBUG TEST")
    print("=" * 35)
    
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
        
        from breeze_connect import BreezeConnect
        from app.config import Config
        
        print("📋 Creating BreezeConnect instance...")
        breeze = BreezeConnect(api_key=Config.BREEZE_API_KEY)
        
        print("🔧 Checking BreezeConnect internals...")
        
        # Check if breeze object has the expected attributes
        attrs = ['api_key', 'session_token', 'user_id']
        for attr in attrs:
            if hasattr(breeze, attr):
                value = getattr(breeze, attr)
                display_value = str(value)[:10] + "..." if value and len(str(value)) > 10 else str(value)
                print(f"   {attr}: {display_value}")
            else:
                print(f"   {attr}: Not found")
        
        print(f"\n🔐 Testing session generation with verbose output...")
        
        # Enable requests logging if possible
        try:
            import logging
            import http.client as http_client
            
            # Enable debugging at http.client level (requests->urllib3->http.client)
            http_client.HTTPConnection.debuglevel = 1
            
            # Initialize logging
            logging.basicConfig()
            logging.getLogger().setLevel(logging.DEBUG)
            requests_log = logging.getLogger("requests.packages.urllib3")
            requests_log.setLevel(logging.DEBUG)
            requests_log.propagate = True
            
            print("   📊 HTTP debugging enabled")
            
        except Exception as e:
            print(f"   ⚠️  Could not enable HTTP debugging: {e}")
        
        # Make the API call
        print(f"   📤 Making generate_session API call...")
        
        try:
            response = breeze.generate_session(
                api_secret=Config.BREEZE_SECRET_KEY,
                session_token=Config.BREEZE_SESSION_TOKEN
            )
            
            print(f"   📥 Response received: {type(response)}")
            
            if response is not None:
                print(f"   📄 Response content: {response}")
                return True
            else:
                print(f"   ❌ Response is None")
                return False
                
        except Exception as e:
            print(f"   ❌ API call exception: {e}")
            print(f"   Exception type: {type(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Debug test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_ssl_certificates():
    """Check SSL certificate issues"""
    
    print(f"\n🔒 SSL CERTIFICATE TEST")
    print("=" * 30)
    
    test_hosts = [
        ("www.google.com", 443),
        ("api.icicidirect.com", 443),
        ("breeze.icicidirect.com", 443)
    ]
    
    for host, port in test_hosts:
        try:
            context = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    print(f"   ✅ {host} - SSL OK")
        except socket.gaierror:
            print(f"   ❌ {host} - DNS resolution failed")
        except Exception as e:
            print(f"   ❌ {host} - SSL error: {str(e)[:50]}...")

if __name__ == "__main__":
    try:
        print("🧪 Starting network and connectivity diagnostics...")
        print(f"⏰ Time: {datetime.now()}")
        
        # Test basic connectivity
        test_network_connectivity()
        
        # Test SSL certificates
        check_ssl_certificates()
        
        # Test Breeze API with debugging
        breeze_success = test_breeze_with_debug()
        
        print(f"\n" + "="*50)
        if breeze_success:
            print("🎉 NETWORK TESTS PASSED!")
        else:
            print("❌ NETWORK ISSUES DETECTED!")
            print("\n🔧 Troubleshooting suggestions:")
            print("   1. Check firewall settings")
            print("   2. Try from different network")
            print("   3. Contact ICICI Direct for API endpoint status")
            print("   4. Verify credentials are correct and active")
            print("   5. Check if your IP needs whitelisting")
        print("="*50)
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Network test cancelled by user")
    except Exception as e:
        print(f"\n❌ Network test script error: {e}")
        import traceback
        traceback.print_exc()