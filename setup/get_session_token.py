#!/usr/bin/env python3
"""
Helper script to get fresh Breeze API session token
Run this when your current session token expires
"""
import urllib.parse
from app.config import Config

def get_login_url():
    """Generate the web login URL for obtaining a fresh session token"""
    config = Config()
    api_key = config.BREEZE_API_KEY
    
    # URL encode the API key (important for special characters)
    encoded_api_key = urllib.parse.quote_plus(api_key)
    
    login_url = f"https://api.icicidirect.com/apiuser/login?api_key={encoded_api_key}"
    
    print("=" * 80)
    print("BREEZE API SESSION TOKEN REFRESH")
    print("=" * 80)
    print()
    print("Your current session token has likely expired.")
    print()
    print("To get a fresh session token:")
    print()
    print("1. Visit this URL in your browser:")
    print(f"   {login_url}")
    print()
    print("2. Log in with your ICICI Direct credentials")
    print()
    print("3. After successful login, you'll be provided with a session token")
    print()
    print("4. Copy the session token")
    print()
    print("5. Update the .env file:")
    print("   BREEZE_SESSION_TOKEN=<your_new_session_token>")
    print()
    print("6. Restart your application")
    print()
    print("=" * 80)
    print()
    print("Direct Login URL (plain text):")
    print(login_url)
    print()
    print("=" * 80)

if __name__ == "__main__":
    get_login_url()
