"""
ICICI DIRECT PRIMARY IP REGISTRATION GUIDE
Your Public IP: 38.101.95.130
"""

print("""
🎯 YOUR PRIMARY IP FOR ICICI DIRECT REGISTRATION
============================================================

✅ PRIMARY IP ADDRESS TO REGISTER: 38.101.95.130

📋 NETWORK DETAILS:
   • Public IP: 38.101.95.130 (ISP assigned)
   • Local IP: 192.168.18.28 (private network)
   • Gateway: 192.168.18.1
   • Status: Current session key already works from this IP

🔍 ANALYSIS:
   ✅ Your current session key is working
   ✅ This means 38.101.95.130 is already registered with ICICI
   ✅ No immediate action needed for current session

📧 FOR NEW SESSION KEY CREATION:
   1. Log into ICICI Direct API portal
   2. Navigate to Session Key/IP Management
   3. Register Primary IP: 38.101.95.130
   4. Generate new session key
   5. Update your .env file

⚠️  IMPORTANT CONSIDERATIONS:

1. DYNAMIC vs STATIC IP:
   • Your IP (38.101.95.130) may change if your ISP uses dynamic IP
   • Check with your ISP if you need static IP for trading
   • Monitor IP changes that could break session keys

2. MULTIPLE LOCATIONS:
   • If trading from different locations, register all IPs
   • Home, office, mobile hotspot IPs may be different
   • ICICI allows multiple IP registration

3. SECURITY:
   • Only register trusted IPs
   • Monitor for unauthorized access attempts
   • Update IP whitelist when changing internet providers

🚀 IMMEDIATE ACTIONS FOR YOUR MYBREEZE APP:

1. ✅ CURRENT STATUS: Your session key works (no action needed)
2. 📊 CONTINUE DEVELOPMENT: Portfolio endpoints still need API documentation
3. 🔄 IF NEEDED: Re-register IP if session expires

🎊 CONCLUSION:
Your Primary IP (38.101.95.130) is already working with ICICI Direct!
This is why your authentication succeeds. The portfolio issues are 
unrelated to IP registration - they're API parameter format issues.

============================================================
""")

# Save IP information for future reference
ip_data = {
    "public_ip": "38.101.95.130",
    "local_ip": "192.168.18.28", 
    "gateway": "192.168.18.1",
    "registration_date": "2025-11-07",
    "status": "working",
    "notes": "Session key already works from this IP"
}

import json
with open('network_config.json', 'w') as f:
    json.dump(ip_data, f, indent=2)

print("✅ Network configuration saved to network_config.json")
print(f"✅ Your Primary IP for ICICI Direct: 38.101.95.130")