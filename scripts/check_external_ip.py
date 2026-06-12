#!/usr/bin/env python3
"""
External IP Check Tool for MyBreezeApp
=====================================

This tool checks your external/public IP address that ICICIDirect 
Breeze API will see when you make requests.
"""

import requests
import json
from datetime import datetime

def check_external_ip():
    """Check external IP address from multiple sources"""
    
    print("🌐 EXTERNAL IP ADDRESS CHECK")
    print("=" * 40)
    
    # Multiple IP checking services for reliability
    ip_services = [
        {"name": "ipify", "url": "https://api.ipify.org?format=json", "key": "ip"},
        {"name": "ipapi", "url": "https://ipapi.co/json/", "key": "ip"},
        {"name": "httpbin", "url": "https://httpbin.org/ip", "key": "origin"},
    ]
    
    external_ips = []
    
    print("🔍 Checking multiple IP services...")
    
    for service in ip_services:
        try:
            print(f"   📡 Querying {service['name']}...", end=" ")
            
            response = requests.get(service['url'], timeout=10)
            response.raise_for_status()
            
            data = response.json()
            ip = data.get(service['key'], 'Unknown')
            
            if ip and ip != 'Unknown':
                external_ips.append(ip)
                print(f"✅ {ip}")
            else:
                print(f"❌ No IP returned")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {str(e)[:50]}...")
        except Exception as e:
            print(f"❌ Parse error: {str(e)[:30]}...")
    
    # Determine consensus IP
    if external_ips:
        # Most common IP (in case of differences)
        consensus_ip = max(set(external_ips), key=external_ips.count)
        
        print(f"\n🎯 CONSENSUS EXTERNAL IP: {consensus_ip}")
        
        # Additional IP information
        try:
            print(f"\n📍 IP GEOLOCATION INFO:")
            geo_response = requests.get(f"https://ipapi.co/{consensus_ip}/json/", timeout=10)
            geo_data = geo_response.json()
            
            print(f"   🌍 Country: {geo_data.get('country_name', 'Unknown')}")
            print(f"   🏙️  City: {geo_data.get('city', 'Unknown')}")
            print(f"   🏢 ISP: {geo_data.get('org', 'Unknown')}")
            print(f"   📊 ASN: {geo_data.get('asn', 'Unknown')}")
            
        except Exception as e:
            print(f"   ⚠️  Could not get geolocation: {e}")
        
        # Check if all services agree
        if len(set(external_ips)) == 1:
            print(f"\n✅ All services report the same IP: {consensus_ip}")
        else:
            print(f"\n⚠️  Different IPs reported: {set(external_ips)}")
            print(f"   Using most common: {consensus_ip}")
        
        # Save results
        ip_info = {
            "timestamp": datetime.now().isoformat(),
            "consensus_ip": consensus_ip,
            "all_reported_ips": external_ips,
            "unique_ips": list(set(external_ips)),
            "services_checked": len(ip_services),
            "successful_checks": len(external_ips)
        }
        
        try:
            with requests.get(f"https://ipapi.co/{consensus_ip}/json/", timeout=10) as geo_response:
                if geo_response.status_code == 200:
                    ip_info["geolocation"] = geo_response.json()
        except:
            pass
        
        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'external_ip_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(ip_info, f, indent=2)
        
        print(f"\n💾 IP information saved to: {filename}")
        
        print(f"\n🎯 FOR ICICIDirect BREEZE API:")
        print(f"=" * 35)
        print(f"📋 Whitelist this IP: {consensus_ip}")
        print(f"🏠 Your internal IP: 192.168.18.28")
        print(f"🌐 Public IP (API sees): {consensus_ip}")
        
        print(f"\n⚠️  IMPORTANT NOTES:")
        print(f"   • This IP may change if you restart your router")
        print(f"   • Contact your ISP for static IP if needed")
        print(f"   • ICICIDirect may require IP whitelisting")
        print(f"   • Test API access after any IP changes")
        
        return consensus_ip
        
    else:
        print(f"\n❌ Could not determine external IP")
        print(f"   Check your internet connection")
        print(f"   Try manually visiting: https://whatismyipaddress.com/")
        return None

if __name__ == "__main__":
    try:
        external_ip = check_external_ip()
        
        if external_ip:
            print(f"\n✅ SUCCESS: Your external IP is {external_ip}")
        else:
            print(f"\n❌ FAILED: Could not determine external IP")
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  IP check cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")