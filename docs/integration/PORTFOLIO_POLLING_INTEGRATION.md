# Portfolio Polling Integration Guide

**Step-by-step guide to integrate portfolio polling into the GreeksMaster trading system.**

---

## Overview

This guide shows how to integrate the portfolio polling service into:
1. **Main application** - Continuous background monitoring
2. **Flask routes** - Expose portfolio data via API
3. **Signal executor** - Track positions automatically
4. **Dashboard** - Display live portfolio updates

---

## Phase 1: Application Initialization

### Step 1: Import Portfolio Poller

In `app/__init__.py`:

```python
from app.services.portfolio_poller import PortfolioPoller, PortfolioUpdateEvent
```

### Step 2: Initialize on App Startup

```python
class GreeksMasterApp:
    def __init__(self):
        self.breeze_api = None
        self.order_poller = None
        self.portfolio_poller = None  # ← NEW
    
    def initialize_services(self):
        """Initialize all background services"""
        # Existing...
        self.breeze_api = BreezeAPIService()
        self.breeze_api.authenticate()
        
        # NEW: Initialize portfolio polling
        self.portfolio_poller = PortfolioPoller(
            self.breeze_api,
            poll_interval=5
        )
        self._register_portfolio_callbacks()
        self.portfolio_poller.start_polling()
        logger.info("Portfolio polling initialized")
    
    def _register_portfolio_callbacks(self):
        """Register event callbacks"""
        self.portfolio_poller.register_callback(
            PortfolioUpdateEvent.POSITION_OPENED,
            self._on_position_opened
        )
        self.portfolio_poller.register_callback(
            PortfolioUpdateEvent.POSITION_CLOSED,
            self._on_position_closed
        )
        self.portfolio_poller.register_callback(
            PortfolioUpdateEvent.PNL_UPDATED,
            self._on_pnl_updated
        )
        self.portfolio_poller.register_callback(
            PortfolioUpdateEvent.ERROR,
            self._on_polling_error
        )
    
    def _on_position_opened(self, data):
        """Handle new position"""
        symbol = data.get('symbol')
        logger.info(f"Position opened: {symbol}")
        # Notify dashboard, log to DB, etc.
    
    def _on_position_closed(self, data):
        """Handle position close"""
        symbol = data.get('symbol')
        logger.info(f"Position closed: {symbol}")
        # Calculate realized P&L, notify dashboard
    
    def _on_pnl_updated(self, data):
        """Handle P&L updates"""
        pnl = data.get('total_pnl', 0)
        logger.info(f"Portfolio P&L: Rs {pnl:.2f}")
        # Update dashboard metrics
    
    def _on_polling_error(self, data):
        """Handle polling errors"""
        error = data.get('error')
        logger.warning(f"Portfolio polling error: {error}")
    
    def shutdown(self):
        """Graceful shutdown"""
        if self.portfolio_poller:
            self.portfolio_poller.stop_polling_thread()
            logger.info("Portfolio polling stopped")
```

### Step 3: Flask App Integration

In `run.py`:

```python
# Existing code
app = Flask(__name__)
greeks_app = GreeksMasterApp()
greeks_app.initialize_services()

# Cleanup on shutdown
@app.teardown_appcontext
def cleanup(error):
    greeks_app.shutdown()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

## Phase 2: API Routes

### Add Portfolio Routes

Create `app/routes/portfolio_routes.py`:

```python
from flask import Blueprint, jsonify
from datetime import datetime

portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/api/portfolio')

@portfolio_bp.route('/holdings', methods=['GET'])
def get_holdings():
    """Get all holdings"""
    holdings = app.greeks_app.portfolio_poller.get_holdings()
    return jsonify({
        'success': True,
        'holdings': holdings,
        'timestamp': datetime.now().isoformat()
    })

@portfolio_bp.route('/positions', methods=['GET'])
def get_positions():
    """Get all open positions"""
    positions = app.greeks_app.portfolio_poller.get_positions()
    return jsonify({
        'success': True,
        'positions': positions,
        'timestamp': datetime.now().isoformat()
    })

@portfolio_bp.route('/pnl', methods=['GET'])
def get_pnl():
    """Get portfolio P&L"""
    pnl = app.greeks_app.portfolio_poller.get_pnl()
    return jsonify({
        'success': True,
        'pnl': pnl,
        'timestamp': datetime.now().isoformat()
    })

@portfolio_bp.route('/margin', methods=['GET'])
def get_margin():
    """Get margin information"""
    margin = app.greeks_app.portfolio_poller.get_margin()
    return jsonify({
        'success': True,
        'margin': margin,
        'timestamp': datetime.now().isoformat()
    })

@portfolio_bp.route('/status', methods=['GET'])
def get_status():
    """Get polling status"""
    status = app.greeks_app.portfolio_poller.get_status()
    return jsonify({
        'success': True,
        'status': status
    })

@portfolio_bp.route('/summary', methods=['GET'])
def get_summary():
    """Get complete portfolio summary"""
    poller = app.greeks_app.portfolio_poller
    return jsonify({
        'success': True,
        'holdings': poller.get_holdings(),
        'positions': poller.get_positions(),
        'pnl': poller.get_pnl(),
        'margin': poller.get_margin(),
        'status': poller.get_status(),
        'timestamp': datetime.now().isoformat()
    })
```

Register in `app/__init__.py`:

```python
from app.routes.portfolio_routes import portfolio_bp

app.register_blueprint(portfolio_bp)
```

---

## Phase 3: WebSocket for Real-time Updates

### Setup WebSocket Events

In `app/__init__.py`:

```python
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

def emit_portfolio_update(data):
    """Emit portfolio update to connected clients"""
    socketio.emit('portfolio_update', {
        'timestamp': datetime.now().isoformat(),
        'data': data
    })

def _on_pnl_updated(self, data):
    emit_portfolio_update({
        'event': 'pnl_updated',
        'pnl': data
    })
```

### JavaScript Client

In `app/static/js/portfolio.js`:

```javascript
const socket = io();

socket.on('portfolio_update', (data) => {
    console.log('Portfolio update:', data);
    
    if (data.data.event === 'pnl_updated') {
        updateDashboard(data.data.pnl);
    }
});

function updateDashboard(pnl) {
    document.getElementById('totalPnL').textContent = 
        `Rs ${pnl.total_pnl.toFixed(2)}`;
    document.getElementById('pnlPercent').textContent = 
        `${pnl.pnl_percentage.toFixed(2)}%`;
}

// Fetch holdings on page load
fetch('/api/portfolio/holdings')
    .then(r => r.json())
    .then(data => {
        console.log('Holdings:', data.holdings);
        renderHoldings(data.holdings);
    });
```

---

## Phase 4: Dashboard Integration

### Update Dashboard HTML

In `app/templates/dashboard.html`:

```html
<!-- Existing sections -->

<!-- New: Portfolio Section -->
<div class="portfolio-section">
    <h2>Portfolio</h2>
    
    <!-- P&L Summary -->
    <div class="pnl-summary">
        <div class="metric">
            <label>Total P&L</label>
            <span id="totalPnL" class="value">--</span>
        </div>
        <div class="metric">
            <label>P&L %</label>
            <span id="pnlPercent" class="value">--</span>
        </div>
        <div class="metric">
            <label>Today's P&L</label>
            <span id="todayPnL" class="value">--</span>
        </div>
    </div>
    
    <!-- Holdings Table -->
    <div class="holdings-section">
        <h3>Holdings</h3>
        <table id="holdingsTable">
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Qty</th>
                    <th>Price</th>
                    <th>Value</th>
                    <th>P&L</th>
                </tr>
            </thead>
            <tbody id="holdingsBody">
            </tbody>
        </table>
    </div>
    
    <!-- Positions Table -->
    <div class="positions-section">
        <h3>Open Positions</h3>
        <table id="positionsTable">
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Qty</th>
                    <th>Entry</th>
                    <th>Current</th>
                    <th>P&L</th>
                </tr>
            </thead>
            <tbody id="positionsBody">
            </tbody>
        </table>
    </div>
    
    <!-- Margin Section -->
    <div class="margin-section">
        <h3>Margin</h3>
        <div class="margin-bar">
            <div id="marginUsed" class="bar-segment used"></div>
            <div id="marginFree" class="bar-segment free"></div>
        </div>
        <div class="margin-text">
            <span>Available: <strong id="availableMargin">--</strong></span>
            <span>Used: <strong id="usedMargin">--</strong></span>
        </div>
    </div>
</div>

<script src="{{ url_for('static', filename='js/portfolio.js') }}"></script>
```

### Dashboard Styling

In `app/static/css/dashboard.css`:

```css
.portfolio-section {
    padding: 20px;
    background: #f5f5f5;
    border-radius: 8px;
    margin-top: 20px;
}

.pnl-summary {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    margin-bottom: 30px;
}

.metric {
    background: white;
    padding: 15px;
    border-radius: 6px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.metric label {
    display: block;
    color: #666;
    font-size: 12px;
    margin-bottom: 5px;
}

.metric .value {
    display: block;
    font-size: 24px;
    font-weight: bold;
    color: #333;
}

.metric .value.positive {
    color: #28a745;
}

.metric .value.negative {
    color: #dc3545;
}

.holdings-section, .positions-section, .margin-section {
    background: white;
    padding: 20px;
    margin-bottom: 20px;
    border-radius: 6px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th {
    background: #f8f9fa;
    padding: 10px;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #dee2e6;
}

td {
    padding: 12px 10px;
    border-bottom: 1px solid #dee2e6;
}

tr:hover {
    background: #f8f9fa;
}

.margin-bar {
    display: flex;
    height: 20px;
    background: #e9ecef;
    border-radius: 4px;
    margin-bottom: 10px;
    overflow: hidden;
}

.bar-segment {
    height: 100%;
}

.bar-segment.used {
    background: #dc3545;
}

.bar-segment.free {
    background: #28a745;
}
```

---

## Phase 5: Integration with Signal Executor

### Update Signal Executor

In `app/services/signal_executor.py`:

```python
class SignalExecutor:
    def __init__(self, order_manager, risk_manager, position_tracker, portfolio_poller=None):
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.position_tracker = position_tracker
        self.portfolio_poller = portfolio_poller  # ← NEW
    
    def execute_signal(self, signal):
        """Execute trading signal"""
        # Existing validation
        if not self._validate_signal(signal):
            return False
        
        # Get current portfolio state
        if self.portfolio_poller:
            current_holdings = self.portfolio_poller.get_holdings()
            current_positions = self.portfolio_poller.get_positions()
            current_margin = self.portfolio_poller.get_margin()
        
        # Check risk limits
        if not self.risk_manager.check_risk(
            signal,
            current_holdings,
            current_margin
        ):
            logger.warning(f"Signal rejected by risk manager: {signal}")
            return False
        
        # Execute order
        order = self.order_manager.place_order(signal)
        
        # Track in position tracker
        if order and self.position_tracker:
            self.position_tracker.add_position(order)
        
        return True
```

---

## Phase 6: Logging & Monitoring

### Setup Portfolio Logging

Create `app/logging/portfolio_logger.py`:

```python
import json
import logging
from datetime import datetime
from pathlib import Path

class PortfolioLogger:
    def __init__(self, log_dir='logs/portfolio'):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Daily log file
        today = datetime.now().strftime('%Y-%m-%d')
        self.log_file = self.log_dir / f'portfolio_{today}.jsonl'
        
        self.logger = logging.getLogger('portfolio')
    
    def log_portfolio_snapshot(self, poller):
        """Log current portfolio state"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'holdings': poller.get_holdings(),
            'positions': poller.get_positions(),
            'pnl': poller.get_pnl(),
            'margin': poller.get_margin()
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def log_event(self, event_type, data):
        """Log portfolio event"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event': event_type,
            'data': data
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
```

Use in app:

```python
portfolio_logger = PortfolioLogger()

def _on_position_opened(self, data):
    portfolio_logger.log_event('position_opened', data)

def _on_pnl_updated(self, data):
    portfolio_logger.log_event('pnl_updated', data)
```

---

## Phase 7: Testing Integration

### Integration Test

Create `tests/test_portfolio_integration.py`:

```python
import pytest
from app import create_app
from app.services.portfolio_poller import PortfolioUpdateEvent

@pytest.fixture
def app():
    app = create_app(testing=True)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_portfolio_api_holdings(client):
    """Test GET /api/portfolio/holdings"""
    response = client.get('/api/portfolio/holdings')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']
    assert 'holdings' in data

def test_portfolio_api_positions(client):
    """Test GET /api/portfolio/positions"""
    response = client.get('/api/portfolio/positions')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']
    assert 'positions' in data

def test_portfolio_api_pnl(client):
    """Test GET /api/portfolio/pnl"""
    response = client.get('/api/portfolio/pnl')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']
    assert 'pnl' in data

def test_portfolio_api_summary(client):
    """Test GET /api/portfolio/summary"""
    response = client.get('/api/portfolio/summary')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']
    assert all(k in data for k in ['holdings', 'positions', 'pnl', 'margin'])

def test_portfolio_polling_started(app):
    """Test that portfolio polling starts"""
    assert app.greeks_app.portfolio_poller is not None
    assert app.greeks_app.portfolio_poller.is_polling

def test_callbacks_registered(app):
    """Test that callbacks are registered"""
    poller = app.greeks_app.portfolio_poller
    assert len(poller.callbacks) > 0
```

Run tests:

```bash
pytest tests/test_portfolio_integration.py -v
```

---

## Checklist

- [ ] **Phase 1:** Portfolio poller initialized in app
- [ ] **Phase 2:** API routes created and registered
- [ ] **Phase 3:** WebSocket events setup
- [ ] **Phase 4:** Dashboard UI integrated
- [ ] **Phase 5:** Signal executor updated
- [ ] **Phase 6:** Logging implemented
- [ ] **Phase 7:** Tests passing
- [ ] **Testing:** Manual dashboard testing
- [ ] **Deployment:** Updated deployment scripts
- [ ] **Documentation:** Updated user guide

---

## Verification

### Check Portfolio Polling Status

```bash
# In Python shell
from app import create_app
app = create_app()
poller = app.greeks_app.portfolio_poller
print(poller.get_status())
```

Expected output:
```python
{
    'is_polling': True,
    'poll_interval': 5,
    'poll_count': 120,
    'holdings_count': 5,
    'positions_count': 3,
    'total_pnl': 5500.00,
    ...
}
```

### Check API Endpoints

```bash
curl http://localhost:5000/api/portfolio/summary
```

Should return all portfolio data.

### Check Dashboard

Open browser: http://localhost:5000/dashboard

Should show:
- Live P&L metrics
- Holdings table with real-time updates
- Open positions
- Margin usage bar

---

## Next Steps

1. ✅ Review integration steps
2. ✅ Implement Phase 1-2 (core integration)
3. ✅ Test API endpoints
4. ✅ Implement Phase 3-4 (real-time dashboard)
5. ✅ Implement Phase 5-6 (executor + logging)
6. ✅ Run full test suite
7. ✅ Deploy to production

**Estimated time:** 2-3 hours for full integration

---

**Ready to integrate! Follow phases in order.** 🚀
