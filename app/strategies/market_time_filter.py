"""
Market Time Aware Filter
Detects market session and applies volatility-appropriate rules
Handles opening bell chaos, closing bell volatility, gaps, and volume patterns
"""

import logging
from datetime import datetime, time
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class MarketTimeFilter:
    """
    Filters trading signals based on market session
    
    Sessions:
    - Opening Bell (9:15-9:45): High volatility, gap clearing
    - Power Hour (9:45-11:00): Still volatile, settling down
    - Optimal Entry (10:30-14:00): Best time for entries
    - Normal (11:00-15:00): Regular trading
    - Closing Bell (15:00-15:30): Position squaring, rebalancing
    - Closed: Market not open
    """
    
    # IST Market Hours
    MARKET_OPEN = time(9, 15)
    MARKET_CLOSE = time(15, 30)
    
    # Dangerous Times
    OPENING_BELL = (time(9, 15), time(9, 45))      # 30 min - gap clearing
    POWER_HOUR = (time(9, 45), time(11, 0))        # 1h 15m - still volatile
    CLOSING_BELL = (time(15, 0), time(15, 30))     # 30 min - squaring
    
    # Safe Times
    OPTIMAL_ENTRY = (time(10, 30), time(14, 0))    # 3h 30m - settled + before close
    
    # Gap Detection
    GAP_THRESHOLD = 0.02  # 2% gap considered significant
    
    # Volume Thresholds (multiplier of average volume)
    OPENING_VOLUME_THRESHOLD = 1.5    # 50% above normal expected
    POWER_HOUR_VOLUME_THRESHOLD = 1.4 # 40% above normal expected
    CLOSING_VOLUME_THRESHOLD = 1.4    # 40% above normal expected
    NORMAL_VOLUME_THRESHOLD = 1.3     # 30% above normal expected
    
    def __init__(self):
        """Initialize market time filter"""
        self.session_cache = {}
        logger.info("Market Time Filter initialized")
    
    def get_current_session(self, current_time: time = None) -> str:
        """
        Determine current market session
        
        Returns:
            str: Session name ('opening_bell', 'power_hour', 'optimal_entry', 
                 'normal', 'closing_bell', or 'closed')
        """
        now = current_time or datetime.now().time()
        
        if not self.is_market_open(now):
            return "closed"
        elif self._is_in_timerange(now, self.OPENING_BELL):
            return "opening_bell"
        elif self._is_in_timerange(now, self.POWER_HOUR):
            return "power_hour"
        elif self._is_in_timerange(now, self.OPTIMAL_ENTRY):
            return "optimal_entry"
        elif self._is_in_timerange(now, self.CLOSING_BELL):
            return "closing_bell"
        else:
            return "normal"
    
    def is_market_open(self, current_time: time = None) -> bool:
        """
        Check if market is currently open
        
        Args:
            current_time: Optional time object (defaults to now)
            
        Returns:
            bool: True if market is open, False otherwise
        """
        now = current_time or datetime.now().time()
        return self.MARKET_OPEN <= now <= self.MARKET_CLOSE
    
    def is_optimal_entry_time(self, current_time: time = None) -> bool:
        """
        Check if current time is optimal for entries
        
        Args:
            current_time: Optional time object
            
        Returns:
            bool: True if in optimal entry window
        """
        session = self.get_current_session(current_time)
        return session == "optimal_entry"
    
    def should_avoid_entry(self, current_time: time = None) -> bool:
        """
        Check if we should AVOID making entries right now
        
        Returns True for: opening bell, power hour, closing bell, closed
        
        Args:
            current_time: Optional time object
            
        Returns:
            bool: True if should avoid entries
        """
        session = self.get_current_session(current_time)
        return session in ["opening_bell", "power_hour", "closing_bell", "closed"]
    
    def get_volatility_multiplier(self, current_time: time = None) -> float:
        """
        Get stop loss/take profit multiplier based on current market session
        
        Multiplier applied to standard stop loss:
        - 1.0 = normal stops (e.g., -2% stays -2%)
        - 1.5 = wide stops (e.g., -2% becomes -3%)
        
        Args:
            current_time: Optional time object
            
        Returns:
            float: Volatility multiplier
        """
        session = self.get_current_session(current_time)
        
        multipliers = {
            "opening_bell": 1.5,      # 50% wider stops
            "power_hour": 1.3,        # 30% wider stops
            "optimal_entry": 1.0,     # Normal stops
            "normal": 1.1,            # 10% wider stops
            "closing_bell": 1.3,      # 30% wider stops
            "closed": 1.0             # N/A
        }
        
        return multipliers.get(session, 1.0)
    
    def get_position_recommendation(self, current_time: time = None) -> Dict:
        """
        Get comprehensive recommendation for current market session
        
        Args:
            current_time: Optional time object
            
        Returns:
            Dict: Recommendation with action, reason, and parameters
        """
        session = self.get_current_session(current_time)
        
        recommendations = {
            "opening_bell": {
                "action": "AVOID",
                "reason": "Overnight orders clearing - extremely high volatility",
                "entry_allowed": False,
                "exit_risky": True,
                "wider_stops": True,
                "multiplier": 1.5,
                "suggested_action": "Wait for market to settle (9:45 AM minimum)",
                "details": "Gap movements, overnight order execution, low liquidity"
            },
            "power_hour": {
                "action": "CAUTION",
                "reason": "Market still volatile - gradually settling down",
                "entry_allowed": False,
                "exit_risky": False,
                "wider_stops": True,
                "multiplier": 1.3,
                "suggested_action": "Wait for optimal entry window (10:30 AM)",
                "details": "Volatility decreasing, but still elevated from open"
            },
            "optimal_entry": {
                "action": "GO",
                "reason": "Market settled - optimal time for new entries",
                "entry_allowed": True,
                "exit_risky": False,
                "wider_stops": False,
                "multiplier": 1.0,
                "suggested_action": "Good time for new positions",
                "details": "Normal market conditions, good risk/reward"
            },
            "normal": {
                "action": "OK",
                "reason": "Normal market hours - regular trading conditions",
                "entry_allowed": True,
                "exit_risky": False,
                "wider_stops": False,
                "multiplier": 1.1,
                "suggested_action": "Monitor for closing bell in remaining time",
                "details": "Standard trading conditions"
            },
            "closing_bell": {
                "action": "CAUTION",
                "reason": "Position squaring + rebalancing + panic selling",
                "entry_allowed": False,
                "exit_risky": True,
                "wider_stops": True,
                "multiplier": 1.3,
                "suggested_action": "Exit existing positions or hold overnight",
                "details": "Volatile last 30 minutes - artificial price swings"
            },
            "closed": {
                "action": "CLOSED",
                "reason": "Market is closed - no trading allowed",
                "entry_allowed": False,
                "exit_risky": False,
                "wider_stops": False,
                "multiplier": 1.0,
                "suggested_action": "Market opens at 9:15 AM (IST)",
                "details": "Current time outside market hours"
            }
        }
        
        return recommendations.get(session, {})
    
    def detect_gap(self, previous_close: float, current_open: float) -> Tuple[bool, float]:
        """
        Detect if market gapped up or down at open
        
        Args:
            previous_close: Previous day closing price
            current_open: Current day opening price
            
        Returns:
            Tuple[bool, float]: (is_gap, gap_percentage)
        """
        if previous_close == 0:
            return False, 0
        
        gap_percent = abs(current_open - previous_close) / previous_close
        is_gap = gap_percent > self.GAP_THRESHOLD
        
        if is_gap:
            direction = "UP" if current_open > previous_close else "DOWN"
            logger.warning(
                f"Gap detected: {direction} {gap_percent*100:.2f}% "
                f"(Previous close: {previous_close:.2f}, Current open: {current_open:.2f})"
            )
        
        return is_gap, gap_percent
    
    def should_skip_gap_trades(self, current_time: time = None) -> bool:
        """
        Check if we should skip trading gap-opened stocks
        
        Gap trades are very risky in first 1-1.5 hours as they often reverse
        
        Args:
            current_time: Optional time object
            
        Returns:
            bool: True if should skip gap trades
        """
        session = self.get_current_session(current_time)
        return session in ["opening_bell", "power_hour"]
    
    def detect_volume_spike(self, current_volume: float, 
                           avg_volume: float, 
                           current_time: time = None) -> Tuple[bool, float]:
        """
        Detect if volume is abnormally high for the session
        
        Different sessions have different expected volume patterns
        
        Args:
            current_volume: Current bar/tick volume
            avg_volume: Average volume (typically 20-day average)
            current_time: Optional time object
            
        Returns:
            Tuple[bool, float]: (is_abnormal_spike, volume_ratio)
        """
        if avg_volume == 0:
            return False, 1.0
        
        volume_ratio = current_volume / avg_volume
        session = self.get_current_session(current_time)
        
        # Different thresholds for different sessions
        thresholds = {
            "opening_bell": self.OPENING_VOLUME_THRESHOLD,      # 50% above normal
            "power_hour": self.POWER_HOUR_VOLUME_THRESHOLD,     # 40% above normal
            "optimal_entry": self.NORMAL_VOLUME_THRESHOLD,      # 30% above normal
            "normal": self.NORMAL_VOLUME_THRESHOLD,             # 30% above normal
            "closing_bell": self.CLOSING_VOLUME_THRESHOLD,      # 40% above normal
            "closed": 1.0                                       # N/A
        }
        
        threshold = thresholds.get(session, 1.3)
        is_spike = volume_ratio > threshold
        
        if is_spike:
            logger.info(
                f"Volume spike detected in {session}: "
                f"{volume_ratio:.2f}x average (threshold: {threshold:.2f}x)"
            )
        
        return is_spike, volume_ratio
    
    def apply_volatility_adjustment(self, stop_loss_percent: float, 
                                   current_time: time = None) -> float:
        """
        Adjust stop loss percentage based on market session volatility
        
        Example:
            - Normal stop loss: 2%
            - Opening bell multiplier: 1.5
            - Adjusted stop loss: 3%
        
        Args:
            stop_loss_percent: Base stop loss percentage (e.g., 0.02 for 2%)
            current_time: Optional time object
            
        Returns:
            float: Adjusted stop loss percentage (capped at 15%)
        """
        multiplier = self.get_volatility_multiplier(current_time)
        adjusted = stop_loss_percent * multiplier
        
        # Cap at reasonable maximum (15%)
        capped = min(adjusted, 0.15)
        
        if capped != adjusted:
            logger.warning(
                f"Stop loss adjustment capped: {adjusted*100:.2f}% → {capped*100:.2f}%"
            )
        
        return capped
    
    def apply_volatility_adjustment_to_price(self, entry_price: float, 
                                            stop_loss_price: float,
                                            current_time: time = None) -> float:
        """
        Calculate adjusted stop loss price based on volatility
        
        Widens the stop loss distance if in volatile session
        
        Example:
            - Entry: ₹1,000
            - Stop loss: ₹980 (distance: ₹20)
            - Opening bell multiplier: 1.5
            - Adjusted stop: ₹970 (distance: ₹30)
        
        Args:
            entry_price: Entry price
            stop_loss_price: Original stop loss price
            current_time: Optional time object
            
        Returns:
            float: Adjusted stop loss price
        """
        multiplier = self.get_volatility_multiplier(current_time)
        
        # Calculate original distance from entry
        stop_loss_distance = abs(entry_price - stop_loss_price)
        
        # Widen the distance
        adjusted_distance = stop_loss_distance * multiplier
        
        # Calculate new stop loss
        if stop_loss_price < entry_price:  # Below entry (buy stop)
            new_stop_loss = entry_price - adjusted_distance
        else:  # Above entry (sell stop)
            new_stop_loss = entry_price + adjusted_distance
        
        return round(new_stop_loss, 2)
    
    def get_session_summary(self, current_time: time = None) -> Dict:
        """
        Get comprehensive summary of current market conditions
        
        Args:
            current_time: Optional time object
            
        Returns:
            Dict: Complete market session summary
        """
        session = self.get_current_session(current_time)
        recommendation = self.get_position_recommendation(current_time)
        multiplier = self.get_volatility_multiplier(current_time)
        
        now = current_time or datetime.now().time()
        
        # Calculate minutes until close
        close_time = self.MARKET_CLOSE
        minutes_until_close = (close_time.hour * 60 + close_time.minute) - \
                            (now.hour * 60 + now.minute)
        
        summary = {
            "session": session,
            "market_open": self.is_market_open(now),
            "current_time": now.strftime("%H:%M:%S"),
            "minutes_until_close": max(0, minutes_until_close),
            "volatility_multiplier": multiplier,
            "entry_allowed": recommendation.get("entry_allowed", False),
            "exit_risky": recommendation.get("exit_risky", False),
            "action": recommendation.get("action", "UNKNOWN"),
            "reason": recommendation.get("reason", ""),
            "suggested_action": recommendation.get("suggested_action", ""),
            "details": recommendation.get("details", "")
        }
        
        return summary
    
    def _is_in_timerange(self, current_time: time, timerange: Tuple[time, time]) -> bool:
        """
        Check if time is within a specific range
        
        Args:
            current_time: Time to check
            timerange: Tuple of (start_time, end_time)
            
        Returns:
            bool: True if time is in range (inclusive)
        """
        start, end = timerange
        return start <= current_time <= end


# Convenience functions for use in other modules

def get_market_filter() -> MarketTimeFilter:
    """Get singleton instance of market time filter"""
    return MarketTimeFilter()


def is_optimal_entry_time() -> bool:
    """Quick check if current time is good for entries"""
    return get_market_filter().is_optimal_entry_time()


def should_avoid_entry() -> bool:
    """Quick check if should avoid entries"""
    return get_market_filter().should_avoid_entry()


def get_volatility_multiplier() -> float:
    """Get current volatility multiplier"""
    return get_market_filter().get_volatility_multiplier()


def get_session_info() -> Dict:
    """Get current session info"""
    filter = get_market_filter()
    return filter.get_session_summary()
