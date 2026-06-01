Here is your **clean, copy‑paste ready Markdown documentation** for the Breeze API Python Client. I’ve structured it professionally with headings, code blocks, and sections so you can directly use it in GitHub README, Confluence, or internal docs.

***

````markdown
# Breeze API Python Client Documentation

## Project Description
The **Breeze API Python Client** is the official client library provided by ICICI Securities for interacting with Breeze APIs. It allows developers to build trading and investment platforms with real-time execution and market data capabilities.

📧 Contact: breezeapi@icicisecurities.com

---

## Table of Contents
- Breeze API Python Client
- Regulatory Changes
- API Documentation
- Setup Virtual Environment
- Installing Client
- API Usage
- WebSocket Usage
- Additional Notes
- Aggressive Limit Order
- List of APIs
- Version History

---

## Breeze API Python Client

**BreezeConnect** provides REST-like APIs for:

- ✅ Execute orders in real-time  
- ✅ Manage portfolio  
- ✅ Access up to 10 years of historical market data (1 sec OHLCV)  
- ✅ Live OHLC streaming via WebSockets  
- ✅ Option Chain API  

---

## Regulatory Changes

- Orders must be placed from a **registered static IP address**
- Static IP can be updated only **once per week**
- Multiple API keys allowed, but **Breeze routes orders via single API key**
- Max limit: **10 orders per second (combined)**
- ❌ Market orders NOT allowed → converted to *Aggressive Limit Orders*
- ❌ Margin & Option Plus orders cannot be modified via API

---

## API Documentation

- Breeze HTTP API Documentation  
- Python Client Documentation  

---

## Setup Virtual Environment

```bash
pip install virtualenv
virtualenv -p python3 breeze_venv
source breeze_venv/bin/activate
````

***

## Installing the Client

```bash
pip install --upgrade breeze-connect
```

Install specific version:

```bash
pip install breeze-connect==1.0.69
```

***

## API Usage

```python
from breeze_connect import BreezeConnect
import urllib
import datetime

# Initialize SDK
breeze = BreezeConnect(api_key="your_api_key")

# Generate login URL
print("https://api.icicidirect.com/apiuser/login?api_key=" + 
      urllib.parse.quote_plus("your_api_key"))

# Generate Session
breeze.generate_session(
    api_secret="your_secret_key",
    session_token="your_api_session"
)

# ISO Date Examples
iso_date = datetime.datetime.strptime("28/02/2021","%d/%m/%Y").isoformat()[:10] + 'T05:30:00.000Z'
iso_datetime = datetime.datetime.strptime("28/02/2021 23:59:59","%d/%m/%Y %H:%M:%S").isoformat()[:19] + '.000Z'
```

***

## WebSocket Usage

```python
from breeze_connect import BreezeConnect
import urllib

breeze = BreezeConnect(api_key="your_api_key")

print("https://api.icicidirect.com/apiuser/login?api_key=" +
      urllib.parse.quote_plus("your_api_key"))

breeze.generate_session(
    api_secret="your_secret_key",
    session_token="your_api_session"
)

# Connect
breeze.ws_connect()

# Callback
def on_ticks(ticks):
    print("Ticks:", ticks)

breeze.on_ticks = on_ticks

# Disconnect
breeze.ws_disconnect()
```

***

## Streaming Examples

### Subscribe by Stock Token

```python
breeze.subscribe_feeds(stock_token="4.1!2885", interval="1minute")
```

Unsubscribe:

```python
breeze.unsubscribe_feeds(stock_token="4.1!2885", interval="1minute")
```

***

### Subscribe NSE Stock

```python
breeze.subscribe_feeds(
    exchange_code="NSE",
    stock_code="NIFTY",
    product_type="cash",
    get_exchange_quotes=True
)
```

***

### Subscribe Options (NFO)

```python
breeze.subscribe_feeds(
    exchange_code="NFO",
    stock_code="NIFTY",
    expiry_date="13-Feb-2025",
    strike_price="23550",
    right="call",
    product_type="options",
    get_exchange_quotes=True,
    interval="1minute"
)
```

***

### Subscribe Multiple Tokens

```python
breeze.subscribe_feeds(stock_token=["4.1!3499", "4.1!2885"])
```

***

### Subscribe Order Notifications

```python
breeze.subscribe_feeds(get_order_notification=True)
```

***

## Additional Notes

### Stock Token Format

```
X.Y!Token
```

| Component | Description     |
| --------- | --------------- |
| X         | Exchange Code   |
| Y         | Data Type       |
| Token     | ISEC Stock Code |

**Exchange Code Values:**

* 1 → BSE
* 4 → NSE / NFO
* 8 → BFO

***

### Validation Rules

* `stock_code` → Required
* `product_type` → futures / options / cash
* `expiry_date` → Required for NFO
* `strike_price` → Required for options
* `right` → Call / Put
* `interval` → 1second / 1minute / 5minute / 30minute

***

## Aggressive Limit Order

Market orders are **converted into aggressive limit orders**.

### Pricing Logic

1. **Reference Price (LTP)**
2. **Range Calculation**
   * Equity → ±3%
   * Futures → ±1.5%
   * Options → ±10%
3. **Minimum Difference**
   * Options: 5 points
   * Equity/Futures: 0.05
4. **DPR Range Enforcement**
5. **Final Execution**
   * Buy → Higher price
   * Sell → Lower price

⚠️ *Orders may be partially executed or rejected depending on market conditions.*

***

## List of APIs

### Core APIs

* get\_customer\_details
* get\_demat\_holdings
* get\_funds / set\_funds
* place\_order / modify\_order / cancel\_order
* get\_order\_detail / get\_order\_list
* get\_portfolio\_holdings / get\_portfolio\_positions
* get\_quotes
* get\_option\_chain\_quotes
* square\_off
* get\_trade\_list / get\_trade\_detail
* get\_names
* preview\_order
* margin\_calculator
* limit\_calculator

***

## Sample API Calls

### Get Customer Details

```python
breeze.get_customer_details(api_session="your_api_session")
```

***

### Get Funds

```python
breeze.get_funds()
```

***

### Place Order (Equity)

```python
breeze.place_order(
    stock_code="ITC",
    exchange_code="NSE",
    product="cash",
    action="buy",
    order_type="limit",
    quantity="1",
    price="420",
    validity="day"
)
```

***

### Historical Data

```python
breeze.get_historical_data(
    interval="1minute",
    stock_code="RELIND",
    exchange_code="NSE",
    product_type="cash"
)
```

***

### Get Quotes

```python
breeze.get_quotes(
    stock_code="NIFTY",
    exchange_code="NFO",
    product_type="futures"
)
```

***

## GTT Orders

### GTT Three-Leg Order

```python
breeze.gtt_three_leg_place_order(
    exchange_code="NFO",
    stock_code="NIFTY",
    product="options",
    gtt_type="cover_oco"
)
```

***

### GTT Single-Leg Order

```python
breeze.gtt_single_leg_place_order(
    exchange_code="NFO",
    stock_code="NIFTY",
    product="options"
)
```

***

## Version History

* **1.0.57** → BFO integration
* **1.0.58** → GIFT NIFTY integration
* **1.0.60** → GTT integration
* **1.0.61** → Docs update
* **1.0.62** → API usage added
* **1.0.65** → Master file switch
* **1.0.68** → Aggressive Limit Order
