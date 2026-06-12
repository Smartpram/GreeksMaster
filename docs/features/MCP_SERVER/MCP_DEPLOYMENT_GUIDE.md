# MCP Server Deployment & Configuration Guide

## 📦 Installation

### Step 1: Add MCP to requirements
```bash
# app/requirements_mcp.txt
mcp>=0.1.0
python-json-logger>=2.0.0
asyncio>=3.4.3
```

Or update existing `requirements.txt`:
```bash
pip install mcp
```

### Step 2: Verify Imports
Create test file to verify all dependencies:

```bash
# verify_mcp_deps.sh
#!/bin/bash

echo "Checking MCP dependencies..."

python -c "from mcp.server import Server; print('✅ mcp.server')" || echo "❌ mcp.server"
python -c "from mcp.types import Tool; print('✅ mcp.types')" || echo "❌ mcp.types"
python -c "from app.services.breeze_api import BreezeAPI; print('✅ breeze_api')" || echo "❌ breeze_api"
python -c "from app.services.risk_manager import RiskManager; print('✅ risk_manager')" || echo "❌ risk_manager"
python -c "from app.services.signal_executor import SignalExecutor; print('✅ signal_executor')" || echo "❌ signal_executor"
python -c "from app.market_sentiment_gate import MarketSentimentGate; print('✅ sentiment_gate')" || echo "❌ sentiment_gate"
python -c "from app.range_policy import RangePolicy; print('✅ range_policy')" || echo "❌ range_policy"

echo "All checks complete!"
```

---

## 🚀 Running the Server

### Option A: Direct Execution (Development)
```bash
cd /path/to/GreeksMaster
python app/mcp_server.py
```

Expected output:
```
INFO - Initializing MCP services...
INFO - ✅ All services initialized successfully
INFO - 🚀 Starting GreeksMaster MCP Server...
INFO - 📝 Available tools: 8
INFO - Listening for MCP protocol messages on stdio...
```

### Option B: As Background Service (Production)
```bash
# Create systemd service file
sudo nano /etc/systemd/system/greeksmaster-mcp.service

[Unit]
Description=GreeksMaster MCP Trading Server
After=network.target

[Service]
Type=simple
User=trader
WorkingDirectory=/path/to/GreeksMaster
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python app/mcp_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable greeksmaster-mcp
sudo systemctl start greeksmaster-mcp
sudo systemctl status greeksmaster-mcp
```

### Option C: Docker Container
```dockerfile
# Dockerfile.mcp
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
COPY config/ ./config/

ENV PYTHONUNBUFFERED=1
EXPOSE 8001

CMD ["python", "app/mcp_server.py"]
```

Build and run:
```bash
docker build -f Dockerfile.mcp -t greeksmaster-mcp .
docker run -d \
  --name greeksmaster-mcp \
  -e BREEZE_API_KEY=your_key \
  -e BREEZE_API_SECRET=your_secret \
  greeksmaster-mcp
```

### Option D: Supervisor (Process Manager)
```ini
# /etc/supervisor/conf.d/greeksmaster-mcp.conf
[program:greeksmaster-mcp]
command=/path/to/venv/bin/python /path/to/GreeksMaster/app/mcp_server.py
directory=/path/to/GreeksMaster
autostart=true
autorestart=true
stdout_logfile=/var/log/greeksmaster-mcp-stdout.log
stderr_logfile=/var/log/greeksmaster-mcp-stderr.log
user=trader

# Reload and start
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start greeksmaster-mcp
```

---

## 🔌 Client Configuration

### Claude Desktop Integration

#### On macOS/Linux:
```bash
# Edit Claude desktop config
nano ~/.claude_desktop_config.json
```

```json
{
  "mcpServers": {
    "greeksmaster": {
      "command": "python",
      "args": ["/path/to/GreeksMaster/app/mcp_server.py"],
      "disabled": false,
      "env": {
        "BREEZE_API_KEY": "YOUR_KEY",
        "PYTHONPATH": "/path/to/GreeksMaster"
      }
    }
  }
}
```

#### On Windows (PowerShell):
```powershell
# Edit config file
$configPath = "$env:APPDATA\Claude\claude_desktop_config.json"
notepad $configPath
```

```json
{
  "mcpServers": {
    "greeksmaster": {
      "command": "python",
      "args": ["C:\\Data\\GreeksMaster\\app\\mcp_server.py"],
      "disabled": false,
      "env": {
        "BREEZE_API_KEY": "YOUR_KEY",
        "PYTHONPATH": "C:\\Data\\GreeksMaster"
      }
    }
  }
}
```

### Restart Claude Desktop
- Close Claude desktop completely
- Reopen - MCP server should connect automatically
- Check console for connection messages

---

## 🔐 Security Configuration

### Environment Variables
```bash
# .env file (git-ignored)
BREEZE_API_KEY=your_api_key_here
BREEZE_API_SECRET=your_api_secret_here
MCP_ALLOW_DRY_RUN=true
MCP_REQUIRE_VALIDATION=true
MCP_LOG_LEVEL=INFO
```

Load in server:
```python
import os
from dotenv import load_dotenv

load_dotenv()

BREEZE_API_KEY = os.getenv("BREEZE_API_KEY")
BREEZE_API_SECRET = os.getenv("BREEZE_API_SECRET")
```

### Rate Limiting
```python
# app/mcp_middleware.py
from functools import wraps
from collections import defaultdict
import time

call_history = defaultdict(list)

def rate_limit(max_calls=100, window=60):
    """Rate limit decorator for MCP tools"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            now = time.time()
            call_history[func.__name__] = [
                t for t in call_history[func.__name__]
                if now - t < window
            ]
            
            if len(call_history[func.__name__]) >= max_calls:
                raise RuntimeError(f"Rate limit exceeded for {func.__name__}")
            
            call_history[func.__name__].append(now)
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@rate_limit(max_calls=10, window=60)  # 10 calls per minute
async def screen_market(**kwargs):
    ...
```

### Audit Logging
```python
# app/mcp_audit.py
import json
import logging
from datetime import datetime

audit_logger = logging.getLogger("mcp_audit")

async def log_tool_call(tool_name, arguments, result):
    """Log all tool calls for audit trail"""
    audit_logger.info(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "arguments": arguments,
        "result_success": result.get("success", False),
        "result_error": result.get("error"),
    }))
```

---

## 📊 Monitoring & Observability

### Health Check Endpoint
```python
# app/mcp_health.py
async def health_check():
    """Check server and service health"""
    checks = {
        "server": "OK",
        "breeze_api": "CHECKING",
        "risk_manager": "CHECKING",
        "signal_executor": "CHECKING",
    }
    
    try:
        # Test Breeze API connection
        await breeze_api.get_market_data("NIFTY", "5min")
        checks["breeze_api"] = "OK"
    except Exception as e:
        checks["breeze_api"] = f"ERROR: {str(e)}"
    
    return checks
```

### Metrics Collection
```python
# app/mcp_metrics.py
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class ToolMetrics:
    calls: int = 0
    errors: int = 0
    avg_response_time: float = 0.0
    last_call: str = ""

metrics = defaultdict(ToolMetrics)

async def record_tool_call(tool_name, duration_ms, success):
    """Record metrics for tools"""
    m = metrics[tool_name]
    m.calls += 1
    if not success:
        m.errors += 1
    m.avg_response_time = (m.avg_response_time * (m.calls - 1) + duration_ms) / m.calls
    m.last_call = datetime.now().isoformat()
```

### Logging Configuration
```python
# app/mcp_logging.py
import logging
import logging.handlers

def setup_logging():
    """Configure comprehensive logging"""
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        "logs/mcp_server.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Apply to all loggers
    for handler in [console_handler, file_handler]:
        handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

setup_logging()
```

---

## 🧪 Testing

### Unit Tests
```python
# tests/test_mcp_tools.py
import pytest
import asyncio
from app.mcp_server import (
    screen_market, validate_signal, calculate_position_size,
    place_order, analyze_risk, get_portfolio
)

@pytest.mark.asyncio
async def test_screen_market():
    """Test market screening"""
    result = await screen_market(
        symbols=["INFTEC", "TCS"],
        strategy="golden_cross"
    )
    assert result["success"] == True
    assert "signals" in result
    assert "summary" in result

@pytest.mark.asyncio
async def test_validate_signal():
    """Test signal validation"""
    result = await validate_signal(
        symbol="INFTEC",
        signal_type="BUY",
        entry_price=250.0
    )
    assert result["success"] == True
    assert "approved" in result

@pytest.mark.asyncio
async def test_calculate_position_size():
    """Test position sizing"""
    result = await calculate_position_size(
        symbol="INFTEC",
        entry_price=250.0,
        stop_loss_price=245.0,
        risk_amount=5000
    )
    assert result["success"] == True
    assert result["quantity"] > 0

# Run tests
# pytest tests/test_mcp_tools.py -v
```

### Integration Tests
```python
# tests/test_mcp_integration.py
@pytest.mark.asyncio
async def test_full_workflow():
    """Test complete trading workflow"""
    
    # 1. Screen market
    signals = await screen_market(symbols=["INFTEC"])
    assert len(signals["signals"]) > 0
    
    # 2. Validate signal
    signal = signals["signals"][0]
    validation = await validate_signal(
        symbol=signal["symbol"],
        signal_type=signal["signal_type"],
        entry_price=signal["entry_price"]
    )
    assert validation["approved"] == True
    
    # 3. Calculate position size
    sizing = await calculate_position_size(
        symbol=signal["symbol"],
        entry_price=signal["entry_price"],
        stop_loss_price=signal["entry_price"] - 5,
        risk_amount=5000
    )
    assert sizing["quantity"] > 0
    
    # 4. Get portfolio
    portfolio = await get_portfolio()
    assert portfolio["success"] == True
```

---

## 🔄 Continuous Deployment

### GitHub Actions Workflow
```yaml
# .github/workflows/mcp_deploy.yml
name: MCP Server Deploy

on:
  push:
    branches: [main]
    paths:
      - 'app/mcp_server.py'
      - 'app/services/**'
      - 'requirements*.txt'

jobs:
  test-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio
    
    - name: Run tests
      run: pytest tests/test_mcp_tools.py -v
    
    - name: Deploy to production
      if: success()
      run: |
        ssh user@prod-server "cd /app/GreeksMaster && \
          git pull && \
          pip install -r requirements.txt && \
          systemctl restart greeksmaster-mcp"
```

---

## 📈 Performance Tuning

### Connection Pooling
```python
# app/mcp_connection_pool.py
from aiohttp import TCPConnector, ClientSession

async def create_session():
    """Create connection pool for HTTP requests"""
    connector = TCPConnector(
        limit=100,
        limit_per_host=30,
        ttl_dns_cache=300
    )
    return ClientSession(connector=connector)
```

### Caching
```python
# app/mcp_cache.py
from functools import lru_cache
from datetime import datetime, timedelta

cache_times = {}

def cached(ttl_seconds=300):
    """Cache decorator with TTL"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}_{args}_{kwargs}"
            now = datetime.now()
            
            if cache_key in cache_times:
                if (now - cache_times[cache_key]).seconds < ttl_seconds:
                    return cache[cache_key]
            
            result = await func(*args, **kwargs)
            cache_times[cache_key] = now
            return result
        return wrapper
    return decorator

# Usage
@cached(ttl_seconds=60)  # Cache for 1 minute
async def get_market_data(symbol):
    ...
```

---

## 🚨 Error Handling & Recovery

### Circuit Breaker
```python
# app/mcp_circuit_breaker.py
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
    
    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if (time.time() - self.last_failure_time) > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise RuntimeError("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self.failure_count = 0
            self.state = CircuitState.CLOSED
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
            
            raise
```

### Retry Logic
```python
# app/mcp_retry.py
import asyncio

async def retry(func, max_attempts=3, backoff_ms=100):
    """Retry with exponential backoff"""
    for attempt in range(max_attempts):
        try:
            return await func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            
            wait_time = (backoff_ms * (2 ** attempt)) / 1000
            await asyncio.sleep(wait_time)
```

---

## 📝 Documentation

### API Documentation
```python
# app/mcp_docs.py
TOOL_DOCUMENTATION = {
    "screen_market": {
        "description": "Scan market for trading signals across symbols",
        "use_cases": [
            "Find new trading opportunities",
            "Scan for mean reversion setups",
            "Identify breakout signals"
        ],
        "example": {
            "input": {
                "symbols": ["INFTEC", "TCS"],
                "strategy": "golden_cross"
            },
            "output": {
                "signals": [{"symbol": "INFTEC", "signal_type": "BUY"}]
            }
        }
    },
    # ... other tools
}
```

### Generate Swagger/OpenAPI
```python
# Generate OpenAPI spec from MCP schema
def generate_openapi_spec(mcp_server):
    """Convert MCP tools to OpenAPI spec"""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "GreeksMaster MCP API", "version": "1.0.0"},
        "paths": {}
    }
    
    for tool in mcp_server.tools:
        spec["paths"][f"/{tool.name}"] = {
            "post": {
                "summary": tool.description,
                "requestBody": {"content": {"application/json": {"schema": tool.inputSchema}}},
            }
        }
    
    return spec
```

---

## 🎯 Success Checklist

- [ ] MCP server starts without errors
- [ ] All 8 tools are accessible
- [ ] Claude Desktop connects successfully
- [ ] First tool call returns correct format
- [ ] Error handling works as expected
- [ ] Rate limiting is enforced
- [ ] Audit logs are being written
- [ ] Metrics are being collected
- [ ] Health checks pass
- [ ] Performance is acceptable (<1s tool calls)
- [ ] Security is configured (API keys, env vars)
- [ ] Monitoring is in place
- [ ] Documentation is updated

---

## 🆘 Support & Debugging

### Check Server Logs
```bash
# Live logs
tail -f logs/mcp_server.log

# Search for errors
grep ERROR logs/mcp_server.log

# Check specific tool
grep screen_market logs/mcp_server.log
```

### Debug Mode
```bash
# Run with debug logging
MCP_LOG_LEVEL=DEBUG python app/mcp_server.py
```

### Verify Connection
```bash
# Check if MCP server is listening
netstat -tlnp | grep 8001

# Test with nc
nc -zv localhost 8001
```

---

## Summary

✅ **MCP Server Ready to Deploy**
- Production-ready code in `app/mcp_server.py`
- Multiple deployment options (systemd, docker, supervisor)
- Security configured (env vars, rate limiting, audit logs)
- Monitoring and observability built-in
- Testing framework ready
- Documentation complete

**Next Step:** Choose a deployment option and start the server!
