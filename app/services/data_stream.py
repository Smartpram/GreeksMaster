"""
Data Streaming Service for Real-time Data
"""
import logging
import threading
import time
from typing import Dict, List, Callable, Optional
from datetime import datetime, timedelta
import json
import websocket
from app.services.breeze_api import BreezeAPIService
from app.config import Config

logger = logging.getLogger(__name__)

class DataStreamService:
    """Service for real-time data streaming"""
    
    def __init__(self, breeze_service: BreezeAPIService):
        self.breeze_service = breeze_service
        self.config = Config()
        self.is_streaming = False
        self.subscribed_instruments = []
        self.data_callbacks = []
        self.ws = None
        self.stream_thread = None
        self.latest_data = {}
        
    def add_data_callback(self, callback: Callable):
        """Add callback function to receive streaming data"""
        self.data_callbacks.append(callback)
    
    def remove_data_callback(self, callback: Callable):
        """Remove callback function"""
        if callback in self.data_callbacks:
            self.data_callbacks.remove(callback)
    
    def start_stream(self, instruments: List[str]):
        """Start streaming data for specified instruments"""
        try:
            if self.is_streaming:
                logger.warning("Stream is already running")
                return False
            
            self.subscribed_instruments = instruments
            self.is_streaming = True
            
            # Start streaming in a separate thread
            self.stream_thread = threading.Thread(target=self._stream_worker)
            self.stream_thread.daemon = True
            self.stream_thread.start()
            
            logger.info(f"Started streaming for instruments: {instruments}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting stream: {e}")
            self.is_streaming = False
            return False
    
    def stop_stream(self):
        """Stop data streaming"""
        try:
            self.is_streaming = False
            
            if self.ws:
                self.ws.close()
            
            if self.stream_thread and self.stream_thread.is_alive():
                self.stream_thread.join(timeout=5)
            
            logger.info("Data streaming stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
            return False
    
    def _stream_worker(self):
        """Worker thread for data streaming"""
        try:
            # For now, simulate streaming with polling
            # In production, this would use Breeze WebSocket API
            while self.is_streaming:
                self._fetch_and_broadcast_data()
                time.sleep(1)  # Update every second
                
        except Exception as e:
            logger.error(f"Error in stream worker: {e}")
            self.is_streaming = False
    
    def _fetch_and_broadcast_data(self):
        """Fetch current data and broadcast to callbacks"""
        try:
            for instrument in self.subscribed_instruments:
                # Get current quote
                quote_data = self.breeze_service.get_quotes(
                    stock_code=instrument,
                    exchange_code="NSE"
                )
                
                if quote_data.get('Success'):
                    result = quote_data.get('Result', {})
                    if result:
                        # Process and structure the data
                        processed_data = self._process_quote_data(instrument, result)
                        self.latest_data[instrument] = processed_data
                        
                        # Broadcast to all callbacks
                        for callback in self.data_callbacks:
                            try:
                                callback(instrument, processed_data)
                            except Exception as callback_error:
                                logger.error(f"Error in data callback: {callback_error}")
                
        except Exception as e:
            logger.error(f"Error fetching and broadcasting data: {e}")
    
    def _process_quote_data(self, instrument: str, raw_data: Dict) -> Dict:
        """Process raw quote data into standardized format"""
        try:
            # Extract relevant fields from Breeze quote response
            processed = {
                'symbol': instrument,
                'timestamp': datetime.now(),
                'open': float(raw_data.get('open', 0)),
                'high': float(raw_data.get('high', 0)),
                'low': float(raw_data.get('low', 0)),
                'close': float(raw_data.get('ltp', 0)),  # Last Traded Price
                'volume': int(raw_data.get('volume', 0)),
                'bid': float(raw_data.get('best_bid_price', 0)),
                'ask': float(raw_data.get('best_ask_price', 0)),
                'bid_qty': int(raw_data.get('best_bid_quantity', 0)),
                'ask_qty': int(raw_data.get('best_ask_quantity', 0)),
                'change': float(raw_data.get('change', 0)),
                'change_percent': float(raw_data.get('change_percentage', 0)),
                'previous_close': float(raw_data.get('previous_close', 0))
            }
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing quote data for {instrument}: {e}")
            return {}
    
    def get_latest_data(self, instrument: str = None) -> Dict:
        """Get latest data for instrument(s)"""
        if instrument:
            return self.latest_data.get(instrument, {})
        else:
            return self.latest_data.copy()
    
    def subscribe_instrument(self, instrument: str):
        """Subscribe to a new instrument"""
        if instrument not in self.subscribed_instruments:
            self.subscribed_instruments.append(instrument)
            logger.info(f"Subscribed to {instrument}")
    
    def unsubscribe_instrument(self, instrument: str):
        """Unsubscribe from an instrument"""
        if instrument in self.subscribed_instruments:
            self.subscribed_instruments.remove(instrument)
            if instrument in self.latest_data:
                del self.latest_data[instrument]
            logger.info(f"Unsubscribed from {instrument}")
    
    def get_subscribed_instruments(self) -> List[str]:
        """Get list of currently subscribed instruments"""
        return self.subscribed_instruments.copy()
    
    def is_instrument_subscribed(self, instrument: str) -> bool:
        """Check if instrument is subscribed"""
        return instrument in self.subscribed_instruments
    
    def get_stream_status(self) -> Dict:
        """Get current streaming status"""
        return {
            'is_streaming': self.is_streaming,
            'subscribed_instruments': len(self.subscribed_instruments),
            'instruments': self.subscribed_instruments,
            'latest_update': max(
                [data.get('timestamp', datetime.min) for data in self.latest_data.values()],
                default=None
            ),
            'data_callbacks': len(self.data_callbacks)
        }


class HistoricalDataService:
    """Service for fetching historical data for backtesting"""
    
    def __init__(self, breeze_service: BreezeAPIService):
        self.breeze_service = breeze_service
        self.data_cache = {}
    
    def get_historical_data(self, instrument: str, interval: str = "1day", 
                          days_back: int = 365) -> List[Dict]:
        """
        Get historical data for an instrument
        
        Args:
            instrument: Stock code
            interval: Data interval (1minute, 5minute, 1day, etc.)
            days_back: Number of days of historical data
            
        Returns:
            List of OHLCV data dictionaries
        """
        try:
            # Create cache key
            cache_key = f"{instrument}_{interval}_{days_back}"
            
            # Check cache first
            if cache_key in self.data_cache:
                cache_time, data = self.data_cache[cache_key]
                # Use cached data if less than 1 hour old
                if (datetime.now() - cache_time).seconds < 3600:
                    return data
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Fetch data from Breeze API
            response = self.breeze_service.get_historical_data(
                stock_code=instrument,
                interval=interval,
                from_date=start_date.strftime("%Y-%m-%dT00:00:00.000Z"),
                to_date=end_date.strftime("%Y-%m-%dT23:59:59.000Z")
            )
            
            if response.get('Success'):
                raw_data = response.get('Result', [])
                processed_data = self._process_historical_data(raw_data)
                
                # Cache the data
                self.data_cache[cache_key] = (datetime.now(), processed_data)
                
                return processed_data
            else:
                logger.error(f"Failed to fetch historical data: {response}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {instrument}: {e}")
            return []
    
    def _process_historical_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Process raw historical data into standardized format"""
        processed_data = []
        
        try:
            for item in raw_data:
                processed = {
                    'datetime': item.get('datetime'),
                    'open': float(item.get('open', 0)),
                    'high': float(item.get('high', 0)),
                    'low': float(item.get('low', 0)),
                    'close': float(item.get('close', 0)),
                    'volume': int(item.get('volume', 0))
                }
                processed_data.append(processed)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing historical data: {e}")
            return []
    
    def clear_cache(self):
        """Clear historical data cache"""
        self.data_cache.clear()
        logger.info("Historical data cache cleared")
    
    def get_cache_info(self) -> Dict:
        """Get cache information"""
        return {
            'cached_items': len(self.data_cache),
            'cache_keys': list(self.data_cache.keys())
        }