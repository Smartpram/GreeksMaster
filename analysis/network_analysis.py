#!/usr/bin/env python3
"""
MyBreezeApp IP Address & Network Configuration Analysis
=====================================================

This script analyzes the IP address configuration for requests 
made by your MyBreezeApp to ICICIDirect Breeze API.
"""

import socket
import json
from datetime import datetime

def analyze_ip_configuration():
    """Analyze current IP configuration for MyBreezeApp"""
    
    print("🌐 MyBreezeApp IP ADDRESS & NETWORK ANALYSIS")
    print("=" * 60)
    
    # Local network information
    print("\n📍 LOCAL NETWORK CONFIGURATION:")
    print("-" * 35)
    
    try:
        # Get local hostname and IP
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        print(f"🖥️  Hostname: {hostname}")
        print(f"📡 Local IP: {local_ip}")
        
        # From ipconfig output, we know:
        wifi_ip = "192.168.18.28"
        subnet = "255.255.255.0"
        gateway = "192.168.18.1"
        
        print(f"🌐 WiFi IP: {wifi_ip}")
        print(f"🌐 Subnet: {subnet}")  
        print(f"🚪 Gateway: {gateway}")
        
    except Exception as e:
        print(f"❌ Error getting local IP: {e}")
    
    print("\n🚀 MyBreezeApp SERVER CONFIGURATION:")
    print("-" * 40)
    
    # Flask app configuration (from run.py)
    print("📋 Flask Application Settings:")
    print(f"   🏠 Host: 0.0.0.0 (binds to all interfaces)")
    print(f"   🔌 Port: 5000 (default)")
    print(f"   🔧 Debug: Environment dependent")
    print(f"   🧵 Threading: Enabled")
    
    print("\n📤 OUTBOUND REQUEST SOURCES:")
    print("-" * 35)
    
    print("🎯 ICICIDirect Breeze API Requests originate from:")
    print(f"   📍 Internal Network: {wifi_ip}")
    print(f"   🌍 External IP: [Need to check with ISP/Router]")
    print(f"   🔒 NAT Translation: Via router {gateway}")
    
    print("\n🔍 ANALYSIS OF REQUEST Flow:")
    print("-" * 35)
    
    print("1. 💻 MyBreezeApp (Local): 192.168.18.28:5000")
    print("2. 🏠 Router NAT: 192.168.18.1")
    print("3. 🌐 ISP Gateway: [ISP Assigned IP]")
    print("4. 🎯 ICICIDirect Servers: [Breeze API Endpoints]")
    
    print("\n⚠️  IMPORTANT CONSIDERATIONS:")
    print("-" * 35)
    
    print("🔐 IP Whitelisting:")
    print("   • ICICIDirect may require IP whitelisting")
    print("   • Your external IP may change (dynamic)")
    print("   • Consider static IP for production")
    
    print("\n🌍 Dynamic vs Static IP:")
    print("   • Current setup uses dynamic IP from ISP")
    print("   • External IP changes when router restarts")
    print("   • May cause authentication issues")
    
    print("\n🏢 Production Deployment IPs:")
    print("   • AWS: Will have different IP ranges")
    print("   • Docker: Container networking considerations")
    print("   • VPS: Dedicated static IP recommended")
    
    print("\n🛠️  RECOMMENDED ACTIONS:")
    print("-" * 30)
    
    print("1. 📞 Contact ICICIDirect:")
    print("   • Ask about IP whitelisting requirements")
    print("   • Get list of required IP ranges to whitelist")
    print("   • Understand their security policies")
    
    print("\n2. 🌐 Check External IP:")
    print("   • Use online tools to find your public IP")
    print("   • Monitor if it changes frequently")
    print("   • Consider static IP from ISP")
    
    print("\n3. 🚀 Production Planning:")
    print("   • Choose hosting with static IP")
    print("   • Document all IP addresses for whitelisting")
    print("   • Set up proper firewall rules")
    
    print("\n4. 🔒 Security Measures:")
    print("   • Use HTTPS for all API calls")
    print("   • Implement proper authentication")
    print("   • Monitor for unauthorized access")
    
    print("\n📊 CURRENT STATUS SUMMARY:")
    print("-" * 30)
    
    config_summary = {
        "local_development": {
            "internal_ip": wifi_ip,
            "flask_host": "0.0.0.0",
            "flask_port": 5000,
            "network_type": "Home WiFi"
        },
        "api_integration": {
            "service": "ICICIDirect Breeze API",
            "authentication": "API Key + Session Token",
            "requests_from": "Dynamic ISP IP (via NAT)"
        },
        "considerations": {
            "ip_whitelisting": "May be required",
            "static_ip_needed": "For production stability",
            "nat_translation": "Through home router"
        }
    }
    
    print(f"✅ Configuration saved for reference")
    
    # Save configuration
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'network_config_{timestamp}.json', 'w') as f:
        json.dump(config_summary, f, indent=2)
    
    print(f"\n💾 Network configuration saved to: network_config_{timestamp}.json")
    
    print("\n" + "=" * 60)
    print("🎯 CONCLUSION: Your requests originate from 192.168.18.28")
    print("🌍 External IP needs to be checked for API whitelisting")
    print("=" * 60)

if __name__ == "__main__":
    analyze_ip_configuration()