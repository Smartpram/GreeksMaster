"""
IP Address Detection for ICICI Direct Session Key Registration
Determine the correct Primary IP to register with ICICI Direct
"""
import socket
import requests
import subprocess
import platform

def get_all_ip_addresses():
    """Get comprehensive IP address information for ICICI registration"""
    print("🌐 IP ADDRESS DETECTION FOR ICICI DIRECT REGISTRATION")
    print("=" * 60)
    
    ip_info = {}
    
    # 1. Local Machine IP (Private Network)
    print("1️⃣ LOCAL MACHINE IP ADDRESS:")
    try:
        # Connect to external server to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        ip_info['local_ip'] = local_ip
        print(f"   📍 Local IP: {local_ip}")
        print(f"   📋 Type: Private network IP (internal)")
        
    except Exception as e:
        print(f"   ❌ Could not determine local IP: {str(e)}")
    
    # 2. Public IP Address (What ICICI sees)
    print("\n2️⃣ PUBLIC IP ADDRESS (What ICICI Direct sees):")
    try:
        # Multiple services to get public IP
        services = [
            "https://api.ipify.org",
            "https://ipecho.net/plain",
            "https://icanhazip.com",
            "https://ident.me"
        ]
        
        public_ips = []
        for service in services:
            try:
                response = requests.get(service, timeout=10)
                if response.status_code == 200:
                    public_ip = response.text.strip()
                    public_ips.append(public_ip)
                    print(f"   📍 Public IP ({service.split('//')[1].split('/')[0]}): {public_ip}")
                    break
            except:
                continue
        
        if public_ips:
            ip_info['public_ip'] = public_ips[0]
            print(f"   ✅ Your Primary IP for ICICI: {public_ips[0]}")
            print(f"   📋 Type: Public IP (ISP assigned)")
        else:
            print("   ❌ Could not determine public IP")
            
    except Exception as e:
        print(f"   ❌ Public IP detection failed: {str(e)}")
    
    # 3. Network Interface Details
    print("\n3️⃣ NETWORK INTERFACE DETAILS:")
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True, shell=True)
            print("   📋 Windows Network Configuration:")
            # Extract relevant lines
            lines = result.stdout.split('\n')
            for line in lines:
                if 'IPv4 Address' in line or 'Default Gateway' in line or 'DNS Servers' in line:
                    print(f"   {line.strip()}")
        else:
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            print("   📋 Network interfaces detected")
            
    except Exception as e:
        print(f"   ⚠️  Network interface details not available: {str(e)}")
    
    # 4. Router/Gateway Information
    print("\n4️⃣ NETWORK GATEWAY:")
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['route', 'print', '0.0.0.0'], capture_output=True, text=True, shell=True)
            lines = result.stdout.split('\n')
            for line in lines:
                if '0.0.0.0' in line and 'Gateway' not in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        gateway = parts[2]
                        print(f"   📍 Default Gateway: {gateway}")
                        ip_info['gateway'] = gateway
                        break
    except Exception as e:
        print(f"   ⚠️  Gateway detection failed: {str(e)}")
    
    return ip_info

def provide_icici_registration_guidance(ip_info):
    """Provide specific guidance for ICICI Direct registration"""
    print("\n" + "=" * 60)
    print("🎯 ICICI DIRECT SESSION KEY REGISTRATION GUIDANCE")
    print("=" * 60)
    
    if 'public_ip' in ip_info:
        public_ip = ip_info['public_ip']
        print(f"✅ PRIMARY IP TO REGISTER WITH ICICI DIRECT:")
        print(f"   📍 IP Address: {public_ip}")
        print(f"   📋 Type: Public IP (ISP assigned)")
        print(f"   🌐 This is what ICICI's servers will see")
        
        print(f"\n📋 REGISTRATION STEPS:")
        print(f"   1. Log into ICICI Direct API portal")
        print(f"   2. Navigate to Session Key/IP Registration section")
        print(f"   3. Add Primary IP: {public_ip}")
        print(f"   4. Save and wait for activation (usually immediate)")
        print(f"   5. Generate new session key with this IP")
        
        print(f"\n⚠️  IMPORTANT NOTES:")
        print(f"   • Your public IP may change if you have dynamic IP from ISP")
        print(f"   • If trading from different locations, register multiple IPs")
        print(f"   • Contact your ISP if you need static IP for trading")
        
    else:
        print("❌ Could not determine public IP address")
        print("   Try manually visiting: https://whatismyipaddress.com/")
    
    if 'local_ip' in ip_info:
        local_ip = ip_info['local_ip']
        print(f"\n📍 YOUR LOCAL NETWORK IP: {local_ip}")
        print(f"   📋 Use for: Local development/testing only")
        print(f"   ❌ Do NOT register this with ICICI Direct")
    
    print(f"\n🔒 SECURITY CONSIDERATIONS:")
    print(f"   • Only register IPs you trust")
    print(f"   • Monitor for unauthorized access")
    print(f"   • Update IP list if you change internet connection")
    
    print(f"\n🚀 NEXT STEPS AFTER IP REGISTRATION:")
    print(f"   1. Generate new session key with registered IP")
    print(f"   2. Update your .env file with new session key")
    print(f"   3. Test authentication with updated credentials")
    print(f"   4. Verify portfolio endpoints work with new session")

def test_current_session_key():
    """Test if current session key works from this IP"""
    print(f"\n🔍 TESTING CURRENT SESSION KEY FROM THIS IP:")
    print("=" * 50)
    
    try:
        # Import and test current API
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from app.services.breeze_api import BreezeAPIService
        
        api = BreezeAPIService()
        result = api.authenticate()
        
        if result['success']:
            print("✅ CURRENT SESSION KEY WORKS!")
            print(f"   User: {result['data'].get('user_name', 'Unknown')}")
            print(f"   ID: {result['data'].get('user_id', 'Unknown')}")
            print("   📋 Your current IP is already registered with ICICI")
        else:
            print("❌ CURRENT SESSION KEY FAILED!")
            print(f"   Error: {result['message']}")
            print("   📋 You may need to register current IP and generate new session key")
            
    except Exception as e:
        print(f"❌ Could not test current session key: {str(e)}")
        print("   📋 Manual IP registration recommended")

if __name__ == "__main__":
    # Get IP information
    ip_info = get_all_ip_addresses()
    
    # Provide ICICI registration guidance
    provide_icici_registration_guidance(ip_info)
    
    # Test current session key
    test_current_session_key()
    
    print(f"\n🎊 SUMMARY:")
    print("=" * 40)
    if 'public_ip' in ip_info:
        print(f"✅ Register this IP with ICICI: {ip_info['public_ip']}")
    print("✅ Current session key testing completed")
    print("✅ Follow registration steps above")
    print("✅ Update session key after IP registration")