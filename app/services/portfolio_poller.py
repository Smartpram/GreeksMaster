"""
Portfolio Polling Service
Continuously monitors portfolio holdings, positions, and P&L in real-time
"""

import threading
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class PortfolioUpdateEvent(Enum):
    """Portfolio update event types"""
    HOLDINGS_UPDATED = "holdings_updated"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    POSITION_MODIFIED = "position_modified"
    PNL_UPDATED = "pnl_updated"
    MARGIN_CHANGED = "margin_changed"
    ERROR = "error"


class PortfolioPoller:
    """
    Background portfolio polling service
    
    Continuously monitors:
    - Holdings (quantity, price, value)
    - Active positions (entry price, current price, P&L)
    - Portfolio P&L (daily, overall, percentage)
    - Margin & cash (available, utilized, balance)
    """
    
    def __init__(self, breeze_service, position_tracker=None, poll_interval: int = 5):
        """
        Initialize portfolio poller
        
        Args:
            breeze_service: BreezeAPIService instance
            position_tracker: LivePositionTracker instance (optional)
            poll_interval: Seconds between polls (default: 5)
        """
        self.breeze_service = breeze_service
        self.position_tracker = position_tracker
        self.poll_interval = poll_interval
        
        # Polling control
        self.polling_thread: Optional[threading.Thread] = None
        self.stop_polling = False
        self.is_polling = False
        
        # Portfolio state
        self.current_holdings: Dict = {}
        self.current_positions: Dict = {}
        self.current_pnl: Dict = {
            'total_pnl': 0.0,
            'today_pnl': 0.0,
            'pnl_percentage': 0.0
        }
        self.current_margin: Dict = {
            'available_margin': 0.0,
            'utilized_margin': 0.0,
            'balance': 0.0
        }
        
        # Change tracking
        self.last_holdings: Dict = {}
        self.last_positions: Dict = {}
        self.last_pnl: Dict = {}
        
        # Event callbacks
        self.event_callbacks: Dict[PortfolioUpdateEvent, List] = {
            event: [] for event in PortfolioUpdateEvent
        }
        
        # Statistics
        self.poll_count = 0
        self.last_poll_time: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.error_count = 0
        
    def start_polling(self) -> bool:
        """Start background portfolio polling"""
        if self.is_polling:
            logger.warning("Portfolio polling already running")
            return False
        
        self.stop_polling = False
        self.polling_thread = threading.Thread(
            target=self._poll_loop,
            daemon=True,
            name="PortfolioPoller"
        )
        self.polling_thread.start()
        self.is_polling = True
        logger.info(f"Portfolio polling started (interval: {self.poll_interval}s)")
        return True
    
    def stop_polling_thread(self) -> bool:
        """Stop portfolio polling"""
        if not self.is_polling:
            logger.warning("Portfolio polling not running")
            return False
        
        self.stop_polling = True
        
        # Wait for thread to finish
        if self.polling_thread:
            self.polling_thread.join(timeout=5)
        
        self.is_polling = False
        logger.info("Portfolio polling stopped")
        return True
    
    def _poll_loop(self):
        """Main polling loop (runs in background thread)"""
        logger.info("Portfolio polling loop started")
        
        while not self.stop_polling:
            try:
                # Poll portfolio data
                self.poll_portfolio()
                
                # Wait before next poll
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Portfolio polling error: {e}", exc_info=True)
                self.last_error = str(e)
                self.error_count += 1
                time.sleep(self.poll_interval)
        
        logger.info("Portfolio polling loop ended")
    
    def poll_portfolio(self) -> bool:
        """
        Poll portfolio data from Breeze API
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Fetch current holdings
            holdings_data = self.breeze_service.get_portfolio_holdings()
            if holdings_data.get('success') or holdings_data.get('Success'):
                new_holdings = self._parse_holdings(holdings_data)
                self._detect_holdings_changes(new_holdings)
                self.current_holdings = new_holdings
            
            # Fetch current positions
            positions_data = self.breeze_service.get_positions()
            if positions_data.get('success') or positions_data.get('Success'):
                new_positions = self._parse_positions(positions_data)
                self._detect_position_changes(new_positions)
                self.current_positions = new_positions
            
            # Calculate P&L
            self._calculate_pnl()
            
            # Fetch margin info
            margin_data = self.breeze_service.get_funds()
            if margin_data.get('success') or margin_data.get('Success'):
                self._detect_margin_changes(margin_data)
            
            self.poll_count += 1
            self.last_poll_time = datetime.now()
            self.error_count = 0
            
            return True
            
        except Exception as e:
            logger.error(f"Error polling portfolio: {e}")
            self.last_error = str(e)
            self.error_count += 1
            self._emit_event(PortfolioUpdateEvent.ERROR, {'error': str(e)})
            return False
    
    def _parse_holdings(self, holdings_data: Dict) -> Dict:
        """Parse holdings response into standardized format"""
        holdings = {}
        
        try:
            # Extract holdings list (format varies by API response)
            holdings_list = holdings_data.get('Success', holdings_data.get('data', []))
            
            if isinstance(holdings_list, list):
                for holding in holdings_list:
                    symbol = holding.get('stock_code') or holding.get('symbol')
                    if symbol:
                        holdings[symbol] = {
                            'symbol': symbol,
                            'quantity': float(holding.get('quantity', 0)),
                            'price': float(holding.get('price', 0)),
                            'value': float(holding.get('value', 0)),
                            'pnl': float(holding.get('pnl', 0)),
                            'pnl_pct': float(holding.get('pnl_pct', 0)),
                            'timestamp': datetime.now()
                        }
            
            return holdings
            
        except Exception as e:
            logger.error(f"Error parsing holdings: {e}")
            return {}
    
    def _parse_positions(self, positions_data: Dict) -> Dict:
        """Parse positions response into standardized format"""
        positions = {}
        
        try:
            positions_list = positions_data.get('Success', positions_data.get('data', []))
            
            if isinstance(positions_list, list):
                for position in positions_list:
                    symbol = position.get('stock_code') or position.get('symbol')
                    if symbol:
                        positions[symbol] = {
                            'symbol': symbol,
                            'quantity': float(position.get('quantity', 0)),
                            'entry_price': float(position.get('entry_price', 0)),
                            'current_price': float(position.get('current_price', 0)),
                            'pnl': float(position.get('pnl', 0)),
                            'pnl_pct': float(position.get('pnl_pct', 0)),
                            'timestamp': datetime.now()
                        }
            
            return positions
            
        except Exception as e:
            logger.error(f"Error parsing positions: {e}")
            return {}
    
    def _detect_holdings_changes(self, new_holdings: Dict):
        """Detect changes in holdings"""
        try:
            # Check for new holdings
            for symbol, holding in new_holdings.items():
                if symbol not in self.last_holdings:
                    logger.info(f"New holding: {symbol} - {holding['quantity']} shares")
                    self._emit_event(PortfolioUpdateEvent.HOLDINGS_UPDATED, {
                        'symbol': symbol,
                        'action': 'added',
                        'holding': holding
                    })
            
            # Check for removed holdings
            for symbol in self.last_holdings:
                if symbol not in new_holdings:
                    logger.info(f"Holding removed: {symbol}")
                    self._emit_event(PortfolioUpdateEvent.HOLDINGS_UPDATED, {
                        'symbol': symbol,
                        'action': 'removed'
                    })
            
            # Check for quantity changes
            for symbol, holding in new_holdings.items():
                if symbol in self.last_holdings:
                    old_qty = self.last_holdings[symbol].get('quantity', 0)
                    new_qty = holding.get('quantity', 0)
                    
                    if old_qty != new_qty:
                        logger.info(f"Quantity change: {symbol} - {old_qty} → {new_qty}")
                        self._emit_event(PortfolioUpdateEvent.POSITION_MODIFIED, {
                            'symbol': symbol,
                            'old_quantity': old_qty,
                            'new_quantity': new_qty,
                            'holding': holding
                        })
            
            self.last_holdings = new_holdings.copy()
            
        except Exception as e:
            logger.error(f"Error detecting holdings changes: {e}")
    
    def _detect_position_changes(self, new_positions: Dict):
        """Detect changes in positions"""
        try:
            # Check for new positions
            for symbol, position in new_positions.items():
                if symbol not in self.last_positions:
                    logger.info(f"New position: {symbol}")
                    self._emit_event(PortfolioUpdateEvent.POSITION_OPENED, {
                        'symbol': symbol,
                        'position': position
                    })
            
            # Check for closed positions
            for symbol in self.last_positions:
                if symbol not in new_positions:
                    logger.info(f"Position closed: {symbol}")
                    self._emit_event(PortfolioUpdateEvent.POSITION_CLOSED, {
                        'symbol': symbol
                    })
            
            # Check for P&L changes
            for symbol, position in new_positions.items():
                if symbol in self.last_positions:
                    old_pnl = self.last_positions[symbol].get('pnl', 0)
                    new_pnl = position.get('pnl', 0)
                    
                    if abs(old_pnl - new_pnl) > 0.01:  # Threshold to avoid noise
                        logger.debug(f"P&L change: {symbol} - Rs {old_pnl:.2f} → Rs {new_pnl:.2f}")
                        self._emit_event(PortfolioUpdateEvent.PNL_UPDATED, {
                            'symbol': symbol,
                            'old_pnl': old_pnl,
                            'new_pnl': new_pnl,
                            'position': position
                        })
            
            self.last_positions = new_positions.copy()
            
        except Exception as e:
            logger.error(f"Error detecting position changes: {e}")
    
    def _detect_margin_changes(self, margin_data: Dict):
        """Detect changes in margin/funds"""
        try:
            # Extract margin information
            available_margin = float(margin_data.get('available_margin', margin_data.get('availableMargin', 0)))
            utilized_margin = float(margin_data.get('utilized_margin', margin_data.get('utilizedMargin', 0)))
            balance = float(margin_data.get('balance', 0))
            
            new_margin = {
                'available_margin': available_margin,
                'utilized_margin': utilized_margin,
                'balance': balance,
                'timestamp': datetime.now()
            }
            
            # Check for significant margin changes
            if self.last_pnl:
                old_available = self.last_pnl.get('available_margin', available_margin)
                
                if abs(old_available - available_margin) > 1000:  # >Rs 1000 threshold
                    logger.info(f"Margin change: Rs {old_available:.2f} → Rs {available_margin:.2f}")
                    self._emit_event(PortfolioUpdateEvent.MARGIN_CHANGED, new_margin)
            
            self.current_margin = new_margin
            
        except Exception as e:
            logger.error(f"Error detecting margin changes: {e}")
    
    def _calculate_pnl(self):
        """Calculate portfolio-level P&L"""
        try:
            total_pnl = sum(h.get('pnl', 0) for h in self.current_holdings.values())
            total_value = sum(h.get('value', 0) for h in self.current_holdings.values())
            
            pnl_pct = (total_pnl / total_value * 100) if total_value > 0 else 0
            
            new_pnl = {
                'total_pnl': total_pnl,
                'today_pnl': total_pnl,  # Note: today_pnl calculation may need adjustment
                'pnl_percentage': pnl_pct,
                'timestamp': datetime.now()
            }
            
            # Detect P&L changes
            if self.last_pnl:
                if abs(self.last_pnl.get('total_pnl', 0) - total_pnl) > 1:  # >Rs 1 threshold
                    self._emit_event(PortfolioUpdateEvent.PNL_UPDATED, new_pnl)
            
            self.current_pnl = new_pnl
            
        except Exception as e:
            logger.error(f"Error calculating P&L: {e}")
    
    def register_callback(self, event: PortfolioUpdateEvent, callback):
        """
        Register callback for portfolio events
        
        Args:
            event: PortfolioUpdateEvent
            callback: Function to call when event occurs
        """
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
            logger.debug(f"Registered callback for {event.value}")
    
    def unregister_callback(self, event: PortfolioUpdateEvent, callback):
        """Unregister callback for portfolio events"""
        if event in self.event_callbacks and callback in self.event_callbacks[event]:
            self.event_callbacks[event].remove(callback)
    
    def _emit_event(self, event: PortfolioUpdateEvent, data: Dict):
        """Emit portfolio event to all registered callbacks"""
        try:
            if event in self.event_callbacks:
                for callback in self.event_callbacks[event]:
                    try:
                        callback(data)
                    except Exception as e:
                        logger.error(f"Error in callback for {event.value}: {e}")
        except Exception as e:
            logger.error(f"Error emitting event {event.value}: {e}")
    
    # Public API
    
    def get_holdings(self) -> Dict:
        """Get current holdings"""
        return self.current_holdings.copy()
    
    def get_positions(self) -> Dict:
        """Get current positions"""
        return self.current_positions.copy()
    
    def get_pnl(self) -> Dict:
        """Get current portfolio P&L"""
        return self.current_pnl.copy()
    
    def get_margin(self) -> Dict:
        """Get current margin information"""
        return self.current_margin.copy()
    
    def get_holding(self, symbol: str) -> Optional[Dict]:
        """Get specific holding details"""
        return self.current_holdings.get(symbol)
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get specific position details"""
        return self.current_positions.get(symbol)
    
    def get_status(self) -> Dict:
        """Get polling status and statistics"""
        return {
            'is_polling': self.is_polling,
            'poll_interval': self.poll_interval,
            'poll_count': self.poll_count,
            'last_poll_time': self.last_poll_time.isoformat() if self.last_poll_time else None,
            'error_count': self.error_count,
            'last_error': self.last_error,
            'holdings_count': len(self.current_holdings),
            'positions_count': len(self.current_positions),
            'total_pnl': self.current_pnl.get('total_pnl', 0)
        }
    
    def wait_for_update(self, timeout: int = 30) -> bool:
        """
        Wait for next portfolio update
        
        Args:
            timeout: Seconds to wait
            
        Returns:
            bool: True if update occurred, False if timeout
        """
        start_time = datetime.now()
        initial_count = self.poll_count
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            if self.poll_count > initial_count:
                return True
            time.sleep(0.1)
        
        return False
