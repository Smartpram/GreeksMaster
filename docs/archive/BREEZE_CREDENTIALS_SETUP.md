# Breeze API Credentials Setup Guide

## Overview
To run the backtest with **REAL market data**, you need valid Breeze API credentials from ICICIDirect.

## Step 1: Get API Key & Secret Key

### Option A: Web Dashboard (Recommended)
1. Go to https://www.icicidirect.com/
2. Login with your account credentials
3. Navigate to: **Settings** → **API Settings** or **Developer Console**
4. Copy your:
   - **API Key** (looks like: `XXXXXXXXXXXXXXXX`)
   - **Secret Key** (looks like: `YYYYYYYYYYYYYYYY`)
   - **User ID** (your ICICI account ID)

### Option B: Contact Support
- Email: support@icicidirect.com
- Ask for: API credentials for algorithmic trading

## Step 2: Generate Session Token

The session token is a temporary credential valid for 24 hours.

### Quick Method (PowerShell):
```powershell
cd c:\Data\MyBreezeApp

# Run this to generate a session token
python -c "
from app.services.breeze_api import BreezeAPIService
import json

api_key = input('Enter your API Key: ')
secret_key = input('Enter your Secret Key: ')
user_id = input('Enter your User ID: ')
password = input('Enter your ICICI password: ')

service = BreezeAPIService(api_key, secret_key, user_id, password)
login_url = service.login()
print(f'\n✅ Go to this URL and authenticate:\n{login_url}\n')
print('After authenticating, your session token will be displayed.')
"
```

### Manual Method:
1. Open PowerShell in the project directory
2. Run:
   ```powershell
   python -c "from app.services.breeze_api import BreezeAPIService; service = BreezeAPIService('YOUR_API_KEY', 'YOUR_SECRET_KEY'); print(service.login())"
   ```
3. Visit the URL in your browser
4. Authenticate with your ICICI credentials
5. Copy the session token shown on the next page

## Step 3: Configure Environment Variables

### Option A: Set Windows Environment Variables

**Using PowerShell (Recommended):**
```powershell
# Set for current PowerShell session only
$env:BREEZE_API_KEY = "your_api_key_here"
$env:BREEZE_SECRET_KEY = "your_secret_key_here"
$env:BREEZE_SESSION_TOKEN = "your_session_token_here"
$env:BREEZE_USER_ID = "your_user_id_here"

# Verify they are set
dir env: | grep BREEZE
```

**Using Command Prompt (Permanent):**
```cmd
setx BREEZE_API_KEY "your_api_key_here"
setx BREEZE_SECRET_KEY "your_secret_key_here"
setx BREEZE_SESSION_TOKEN "your_session_token_here"
setx BREEZE_USER_ID "your_user_id_here"

# Restart Command Prompt and verify
echo %BREEZE_API_KEY%
```

### Option B: Use .env File

1. Create a `.env` file in `c:\Data\MyBreezeApp\`:
```
BREEZE_API_KEY=your_api_key_here
BREEZE_SECRET_KEY=your_secret_key_here
BREEZE_SESSION_TOKEN=your_session_token_here
BREEZE_USER_ID=your_user_id_here
PAPER_TRADING=True
DEFAULT_CAPITAL=100000
```

2. The app will automatically load these values when it starts

## Step 4: Verify Credentials are Loaded

Run the verification script:
```powershell
cd c:\Data\MyBreezeApp
python setup_breeze_backtest.py
```

Expected output:
```
✓ API_KEY: XXXX...XXXX
✓ SECRET_KEY: XXXX...XXXX
✓ SESSION_TOKEN: XXXX...XXXX
✓ USER_ID: XXXX...XXXX
```

If any show `✗ NOT SET`, they weren't loaded properly. Check:
- Environment variables are set (for current session)
- `.env` file exists and has correct values
- No typos in variable names

## Step 5: Run Backtest with Real Data

```powershell
cd c:\Data\MyBreezeApp
python setup_breeze_backtest.py
```

The script will:
1. ✅ Verify credentials are loaded
2. ✅ Confirm you want to run with real data
3. ✅ Fetch historical data for 8 symbols from Breeze API
4. ✅ Run 64 backtests (8 symbols × 8 strategies)
5. ✅ Save results to `ADVANCED_STRATEGIES_BACKTEST_RESULTS.json`

## Troubleshooting

### Issue: "Session Token Expired"
**Solution:** Generate a new session token every 24 hours
```powershell
python -c "from app.services.breeze_api import BreezeAPIService; service = BreezeAPIService(); print(service.login())"
```

### Issue: "API Key Invalid"
**Solution:** Check credentials match exactly from ICICIDirect dashboard
- No extra spaces
- Correct case (usually uppercase)
- No special characters

### Issue: "No data returned from Breeze"
**Solution:** 
1. Verify you're using correct symbol codes (NIFTY, INFY, RELIANCE, etc.)
2. Check if market data is available for those symbols
3. Try fetching data for a different symbol

### Issue: "Rate limit exceeded"
**Solution:** Wait a few minutes and try again
- Breeze API has rate limits
- Usually 100-500 requests per hour depending on your plan
- Check your subscription level

### Issue: Environment variables not loading
**Solution:** 
1. Make sure you use `.env` file (backup method)
2. Restart PowerShell after setting environment variables
3. Verify with: `$env:BREEZE_API_KEY`

## Security Notes

⚠️ **IMPORTANT:**
- ❌ Never commit credentials to Git
- ❌ Never share your API Key or Secret
- ❌ Never hardcode credentials in code
- ✅ Always use environment variables or .env files
- ✅ Add `.env` to `.gitignore`
- ✅ Rotate credentials periodically

## What's Next?

After running the backtest with real data:

1. ✅ Review `ADVANCED_STRATEGIES_BACKTEST_RESULTS.md` for performance analysis
2. ✅ Identify top-performing strategies (usually Gamma Scalping, Order Flow)
3. ✅ Set up paper trading to validate with real market conditions
4. ✅ Deploy live trading with validated strategies (10% capital initially)

See `ADVANCED_STRATEGIES_QUICK_REFERENCE.md` for more details.

---

**Questions?** Check:
- `app/services/breeze_api.py` - Breeze API implementation
- `run_advanced_strategies_backtest.py` - Backtest engine
- `ADVANCED_STRATEGIES_QUICK_REFERENCE.md` - Strategy documentation
