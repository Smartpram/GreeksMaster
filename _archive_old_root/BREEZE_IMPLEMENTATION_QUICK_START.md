# BREEZE API IMPLEMENTATION QUICK START
**Ready to implement live trading? Here's what you need to do.**

---

## TL;DR (30 seconds)

✅ **YES** - You can send orders through Breeze  
✅ **YES** - You can check order status  
✅ **YES** - You can manage positions  

**Start coding now. Most features already exist in:**
- `app/services/breeze_api.py` - API client
- `app/services/order_manager.py` - Order handling
- `app/services/live_position_tracker.py` - Position tracking
- `app/services/signal_executor.py` - Execution orchestration

---

## WHAT'S ALREADY BUILT (7/10)

### ✓ IMPLEMENTED (Just Use It)
1. **Order Placement** - Market, Limit, Stop-Loss orders
   ```python
   order_manager.place_market_order('INFTEC', 'BUY', 100, 'NSE')
   order_manager.place_limit_order('INFTEC', 'BUY', 100, price=250.50)
   ```

2. **Status Checking** - Get individual order status
   ```python
   status = breeze_service.get_order_details(order_id)
   ```

3. **Holdings** - Get positions
   ```python
   holdings = position_tracker.get_holdings()
   ```

4. **Authentication** - Session token handling
   ```python
   breeze_service.authenticate(session_token)
   ```

5. **Paper Trading** - Simulated execution for testing
   ```python
   # Set PAPER_TRADING=True in config
   ```

6. **Order Tracking** - Pending orders dict
   ```python
   pending_orders[order_id] = {...}
   ```

7. **Position Aggregation** - Sum across holdings
   ```python
   total_value = sum(h['value'] for h in holdings)
   ```

### ⚠️ NEEDS IMPLEMENTATION (3/10)

1. **Error Handling & Retries** ← START HERE
   ```python
   # Currently missing:
   try:
       response = breeze_service.place_order(params)
   except SessionExpiredException:
       breeze_service.authenticate()  # Auto-refresh
       response = breeze_service.place_order(params)
   ```

2. **Rate Limiting** ← THEN THIS
   ```python
   # Currently missing:
   # Track calls/minute, implement token bucket
   api_call_count = 0
   if api_call_count > 100:
       wait_until_next_minute()
   ```

3. **Partial Fill Handling** ← FINALLY THIS
   ```python
   # Currently missing:
   filled = status['filled_quantity']
   if filled < requested_qty:
       remaining = requested_qty - filled
       # Handle appropriately
   ```

---

## IMPLEMENTATION ROADMAP (1 Week)

### DAY 1: Error Handling (4 hours)
**File:** `app/services/breeze_api.py`

Add to BreezeAPIService:
```python
import time

def place_order_with_retry(self, order_params, max_retries=3):
    """Place order with automatic retry"""
    for attempt in range(max_retries):
        try:
            response = self.place_order(order_params)
            logger.info(f"Order placed: {response['Result']['order_id']}")
            return response
        
        except SessionExpiredException:
            logger.warning("Session expired, re-authenticating...")
            self.authenticate()
            
        except APIError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Order failed, retry in {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                logger.error(f"Order failed after {max_retries} attempts: {e}")
                raise
```

### DAY 2: Session Token Refresh (3 hours)
**File:** `app/services/breeze_api.py`

Add to BreezeAPIService.__init__:
```python
self.last_auth_time = time.time()
self.session_timeout = 1500  # 25 minutes (safety margin)

def ensure_session_valid(self):
    """Auto-refresh token if close to expiry"""
    elapsed = time.time() - self.last_auth_time
    if elapsed > self.session_timeout:
        logger.info("Session near expiry, refreshing...")
        self.authenticate()
        self.last_auth_time = time.time()

# Call before every API request:
def place_order(self, order_params):
    self.ensure_session_valid()
    # ... rest of method
```

### DAY 3: Order Status Polling (4 hours)
**File:** `app/services/order_manager.py`

Add polling loop:
```python
import threading
import time

class OrderManager:
    def __init__(self, breeze_service):
        self.breeze_service = breeze_service
        self.pending_orders = {}
        self.polling_thread = None
        self.stop_polling = False
    
    def start_polling(self, interval=2):
        """Start background order status polling"""
        self.polling_thread = threading.Thread(
            target=self._poll_orders,
            args=(interval,),
            daemon=True
        )
        self.polling_thread.start()
        logger.info(f"Order polling started (interval: {interval}s)")
    
    def _poll_orders(self, interval):
        """Poll pending orders for status changes"""
        while not self.stop_polling:
            try:
                order_ids = list(self.pending_orders.keys())
                if order_ids:
                    # Batch check all pending orders
                    orders_status = self.breeze_service.get_order_book()
                    
                    for order_id in order_ids:
                        order_status = next(
                            (o for o in orders_status if o['order_id'] == order_id),
                            None
                        )
                        
                        if order_status:
                            old_status = self.pending_orders[order_id]['status']
                            new_status = order_status['status']
                            
                            if new_status != old_status:
                                logger.info(f"Order {order_id}: {old_status} → {new_status}")
                                self.pending_orders[order_id].update(order_status)
                                
                                if new_status in ['EXECUTED', 'CANCELLED', 'REJECTED']:
                                    # Remove from pending
                                    del self.pending_orders[order_id]
                
                time.sleep(interval)
            
            except Exception as e:
                logger.error(f"Polling error: {e}")
                time.sleep(interval)
```

### DAY 4: Rate Limiting (3 hours)
**File:** `app/services/breeze_api.py`

Add rate limiter:
```python
from collections import deque

class APIRateLimiter:
    def __init__(self, max_calls=100, window_seconds=60):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.call_times = deque()
    
    def wait_if_needed(self):
        """Wait if we've exceeded rate limit"""
        now = time.time()
        
        # Remove old calls outside the window
        while self.call_times and self.call_times[0] < now - self.window_seconds:
            self.call_times.popleft()
        
        if len(self.call_times) >= self.max_calls:
            # Wait until oldest call leaves the window
            sleep_time = self.call_times[0] + self.window_seconds - now
            logger.warning(f"Rate limit reached, waiting {sleep_time:.1f}s")
            time.sleep(sleep_time)
            self.call_times.popleft()
        
        self.call_times.append(now)

# In BreezeAPIService.__init__:
self.rate_limiter = APIRateLimiter()

# Before every API call:
def place_order(self, order_params):
    self.rate_limiter.wait_if_needed()
    # ... rest of method
```

### DAY 5: Partial Fill Handling (3 hours)
**File:** `app/services/order_manager.py`

Add fill verification:
```python
def place_market_order(self, stock_code, action, quantity, **kwargs):
    """Place market order with fill verification"""
    response = breeze_service.place_order({...})
    order_id = response['Result']['order_id']
    
    # Store for polling
    self.pending_orders[order_id] = {
        'original_qty': quantity,
        'status': 'PENDING',
        'placed_at': datetime.now(),
        'filled_qty': 0
    }
    
    # Start polling this order
    self._poll_order_until_filled(order_id, quantity)
    
    return response

def _poll_order_until_filled(self, order_id, expected_qty):
    """Poll until order is filled, handle partial fills"""
    while True:
        status = breeze_service.get_order_details(order_id)
        filled_qty = status.get('filled_quantity', 0)
        order_status = status.get('status', 'PENDING')
        
        if order_status == 'EXECUTED':
            if filled_qty < expected_qty:
                logger.warning(
                    f"Partial fill: {filled_qty}/{expected_qty} shares"
                )
                # Handle: place market order for remaining
                remaining = expected_qty - filled_qty
                self.place_market_order(
                    stock_code=status['stock_code'],
                    action=status['action'],
                    quantity=remaining
                )
            break
        
        elif order_status in ['CANCELLED', 'REJECTED']:
            logger.error(f"Order {order_id} {order_status}")
            break
        
        time.sleep(1)  # Poll every second
```

### DAY 6: Comprehensive Logging (3 hours)
**File:** `app/services/order_manager.py`

Add audit logging:
```python
import logging
from datetime import datetime

# Setup audit logger
audit_logger = logging.getLogger('order_audit')
file_handler = logging.FileHandler('logs/order_audit.log')
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
audit_logger.addHandler(file_handler)

class OrderManager:
    def place_market_order(self, stock_code, action, quantity, **kwargs):
        # Log placement
        audit_logger.info(
            f"ORDER_PLACED | Symbol: {stock_code} | "
            f"Action: {action} | Qty: {quantity}"
        )
        
        response = breeze_service.place_order({...})
        order_id = response['Result']['order_id']
        
        audit_logger.info(f"ORDER_ID: {order_id}")
        
        # Store with tracking
        self.pending_orders[order_id] = {
            'symbol': stock_code,
            'action': action,
            'qty': quantity,
            'placed_at': datetime.now(),
            'status': 'PENDING'
        }
        
        return response
    
    def _poll_orders(self, interval):
        """Poll with audit logging"""
        while not self.stop_polling:
            try:
                for order_id in list(self.pending_orders.keys()):
                    status = breeze_service.get_order_details(order_id)
                    
                    if status['status'] != self.pending_orders[order_id]['status']:
                        old = self.pending_orders[order_id]['status']
                        new = status['status']
                        
                        # Log status change
                        audit_logger.info(
                            f"ORDER_STATUS_CHANGE | ID: {order_id} | "
                            f"{old} → {new}"
                        )
                        
                        # Log execution details
                        if new == 'EXECUTED':
                            audit_logger.info(
                                f"ORDER_EXECUTED | ID: {order_id} | "
                                f"Qty: {status.get('filled_quantity')} | "
                                f"Price: {status.get('average_price')}"
                            )
                
                time.sleep(interval)
            
            except Exception as e:
                audit_logger.error(f"POLLING_ERROR | {e}", exc_info=True)
                time.sleep(interval)
```

### DAY 7: Testing & Integration (Full day)

**Unit Tests:**
```python
# tests/test_error_handling.py
def test_session_expiry_retry():
    """Verify auto-retry on session expiry"""
    manager = OrderManager(mock_breeze_service)
    manager.place_order_with_retry({'stock_code': 'INFTEC'})
    # Verify authenticate() was called

def test_partial_fill_handling():
    """Verify partial fill is handled correctly"""
    # Order 100, fill 60, then fill 40
    # Should result in single position of 100

def test_rate_limiting():
    """Verify rate limit enforcement"""
    for i in range(101):
        limiter.wait_if_needed()  # 101st should wait
```

**Integration Test:**
```python
# tests/test_live_trading_workflow.py
def test_complete_buy_hold_sell():
    """End-to-end: BUY → HOLD → SELL"""
    order_manager.place_market_order('INFTEC', 'BUY', 100)
    time.sleep(2)  # Wait for execution
    
    holdings = position_tracker.get_holdings()
    assert 'INFTEC' in holdings
    assert holdings['INFTEC']['qty'] == 100
    
    order_manager.place_market_order('INFTEC', 'SELL', 100)
    time.sleep(2)
    
    holdings = position_tracker.get_holdings()
    assert 'INFTEC' not in holdings  # Closed
```

---

## EXACT CODE LOCATIONS TO MODIFY

| File | Lines | What | Priority |
|------|-------|------|----------|
| `app/services/breeze_api.py` | 150-200 | Add error handling | 1 |
| `app/services/breeze_api.py` | 50-100 | Add session refresh | 1 |
| `app/services/order_manager.py` | 200-250 | Add polling loop | 1 |
| `app/services/breeze_api.py` | 1-50 | Add rate limiter | 2 |
| `app/services/order_manager.py` | 80-120 | Add fill verification | 2 |
| `app/services/order_manager.py` | 300-350 | Add audit logging | 2 |

---

## CONFIGURATION NEEDED

Add to `config.py`:

```python
# Breeze API
BREEZE_API_KEY = os.getenv('BREEZE_API_KEY')
BREEZE_SECRET_KEY = os.getenv('BREEZE_SECRET_KEY')
BREEZE_SESSION_TOKEN = os.getenv('BREEZE_SESSION_TOKEN')
BREEZE_USER_ID = os.getenv('BREEZE_USER_ID')
BREEZE_PASSWORD = os.getenv('BREEZE_PASSWORD')

# Trading
PAPER_TRADING = False  # Set to True for testing
LIVE_TRADING = True    # Enable real money trading

# Rate Limiting
API_RATE_LIMIT = 100  # calls per minute
API_RATE_WINDOW = 60  # seconds

# Order Polling
ORDER_POLL_INTERVAL = 2  # seconds
ORDER_POLL_TIMEOUT = 300  # 5 minutes max wait

# Retry Policy
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # Exponential: 2^attempt

# Logging
AUDIT_LOG_FILE = 'logs/order_audit.log'
```

Add to `.env`:
```
BREEZE_API_KEY=your_key_here
BREEZE_SECRET_KEY=your_secret_here
BREEZE_SESSION_TOKEN=your_token_here
BREEZE_USER_ID=your_user_id
BREEZE_PASSWORD=your_password
```

---

## GETTING BREEZE CREDENTIALS

1. **Get Session Token:**
   - Go to: https://breezealgo.icicidirect.com/api/v1/
   - Login with your ICICIDirect account
   - Extract session token from response

2. **API Key & Secret:**
   - From ICICIDirect account settings
   - API → API Credentials
   - Copy KEY and SECRET

3. **User ID & Password:**
   - Your ICICIDirect login credentials
   - Stored securely in .env

---

## DEPLOYMENT CHECKLIST

Before going live:

- [ ] Error handling implemented & tested
- [ ] Session refresh working
- [ ] Order polling functional
- [ ] Rate limiting active
- [ ] Partial fill handling verified
- [ ] Audit logging working
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Paper trading validated
- [ ] Small live test (1 share) successful
- [ ] Full monitoring dashboard ready
- [ ] Rollback plan documented

---

## GETTING HELP

**Test Comprehensive Report:** `BREEZE_API_CAPABILITY_REPORT.md`  
**Test Results JSON:** `logs/breeze_integration_test_results.json`  
**Test Code:** `tests/test_breeze_integration_comprehensive.py`

---

**Ready? Start with DAY 1: Error Handling. Should take 4 hours. You've got this! 🚀**
