"""
ntfy Notification Service for Trading Alerts
Sends real-time trading alerts to ntfy.sh
Integration with trading system for notifications on phone/desktop
"""

import requests
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import pytz

logger = logging.getLogger(__name__)

class NtfyNotificationService:
    """Send trading alerts via ntfy.sh"""
    
    def __init__(self, topic: str = "trading-alerts"):
        """
        Initialize ntfy notification service
        
        Args:
            topic: ntfy topic name (default: trading-alerts)
                   Use: mport (your custom topic)
        """
        self.base_url = "https://ntfy.sh"
        self.topic = topic
        self.ist_tz = pytz.timezone('Asia/Kolkata')
        self.enabled = True
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in IST"""
        return datetime.now(self.ist_tz).strftime('%Y-%m-%d %H:%M:%S IST')
    
    def send_alert(self, 
                   title: str, 
                   message: str, 
                   priority: str = "default",
                   tags: Optional[str] = None) -> bool:
        """
        Send alert via ntfy
        
        Args:
            title: Alert title (max 100 chars, ASCII only)
            message: Alert message
            priority: "min", "low", "default", "high", "max"
            tags: Tags for categorization (ASCII only)
        
        Returns:
            bool: True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            url = f"{self.base_url}/{self.topic}"
            
            # Format message with timestamp (ASCII safe)
            full_message = f"{message}\n[{self._get_timestamp()}]"
            
            headers = {
                "Title": title,
                "Priority": priority,
            }
            
            if tags:
                headers["Tags"] = tags
            
            # Ensure all headers are ASCII-safe
            safe_headers = {}
            for key, value in headers.items():
                if isinstance(value, str):
                    safe_headers[key] = value.encode('utf-8', errors='ignore').decode('utf-8')
                else:
                    safe_headers[key] = value
            
            response = requests.post(
                url,
                data=full_message.encode('utf-8', errors='ignore'),
                headers=safe_headers,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"+ ntfy alert sent: {title}")
                return True
            else:
                logger.warning(f"- ntfy error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"- ntfy notification error: {str(e)[:100]}")
            return False
    
    # ============================================
    # TRADING ALERTS
    # ============================================
    
    def entry_signal(self, symbol: str, direction: str, confidence: float, 
                     strategy: str = "ML"):
        """Send entry signal alert"""
        title = f"[{direction}] ENTRY: {symbol}"
        message = f"{direction} {strategy} Signal\nConfidence: {confidence:.1%}"
        
        self.send_alert(
            title=title,
            message=message,
            priority="high",
            tags="entry,signal"
        )
    
    def exit_signal(self, symbol: str, exit_type: str, pnl: float, 
                    reason: str = "Exit Rule"):
        """Send exit signal alert"""
        status = "PROFIT" if pnl >= 0 else "LOSS"
        title = f"[{status}] EXIT: {symbol}"
        message = f"{exit_type} - {reason}\nP&L: Rs {pnl:,.0f}"
        
        self.send_alert(
            title=title,
            message=message,
            priority="high",
            tags="exit,signal"
        )
    
    def stop_loss_hit(self, symbol: str, entry: float, exit: float, 
                      loss: float, qty: int = 1):
        """Send stop loss alert"""
        title = f"[SL] STOP LOSS HIT: {symbol}"
        message = f"SL HIT\nEntry: Rs {entry:,.0f}\nExit: Rs {exit:,.0f}\nLoss: Rs {loss:,.0f}"
        
        self.send_alert(
            title=title,
            message=message,
            priority="max",
            tags="stop-loss,alert"
        )
    
    def profit_target_hit(self, symbol: str, entry: float, exit: float, 
                         profit: float, qty: int = 1):
        """Send profit target alert"""
        title = f"[PT] PROFIT TARGET HIT: {symbol}"
        message = f"TARGET HIT\nEntry: Rs {entry:,.0f}\nExit: Rs {exit:,.0f}\nProfit: Rs {profit:,.0f}"
        
        self.send_alert(
            title=title,
            message=message,
            priority="high",
            tags="profit-target,alert"
        )
    
    def kill_switch_triggered(self, cumulative_loss: float, threshold: float):
        """Send kill switch alert"""
        title = "*** KILL SWITCH TRIGGERED ***"
        message = f"Daily loss limit reached\nLoss: Rs {cumulative_loss:,.0f}\nThreshold: Rs {threshold:,.0f}"
        
        self.send_alert(
            title=title,
            message=message,
            priority="max",
            tags="kill-switch,critical"
        )
    
    def position_opened(self, symbol: str, strategy: str, entry: float, 
                       qty: int, risk: float):
        """Send position opened alert"""
        title = f"[OPEN] POSITION OPENED: {symbol}"
        message = f"Strategy: {strategy}\nEntry: Rs {entry:,.0f}\nQty: {qty}\nRisk: Rs {risk:,.0f}"
        
        self.send_alert(
            title=title,
            message=message,
            priority="high",
            tags="position,open"
        )
    
    def position_closed(self, symbol: str, pnl: float, trades: int = 1):
        """Send position closed alert"""
        status = "PROFIT" if pnl >= 0 else "LOSS"
        title = f"[{status}] POSITION CLOSED: {symbol}"
        message = f"P&L: Rs {pnl:,.0f}\nTrades: {trades}"
        
        self.send_alert(
            title=title,
            message=message,
            priority="default",
            tags="position,closed"
        )
    
    def session_started(self, capital: float, max_loss: float):
        """Send session started alert"""
        title = "[START] TRADING SESSION STARTED"
        message = f"Capital: Rs {capital:,.0f}\nMax Loss: Rs {max_loss:,.0f}\nTime: {self._get_timestamp()}"
        
        self.send_alert(
            title=title,
            message=message,
            priority="high",
            tags="session,start"
        )
    
    def session_ended(self, trades: int, win_rate: float, pnl: float, fees: float):
        """Send session ended alert"""
        status = "PROFIT" if pnl >= 0 else "LOSS"
        title = f"[END] SESSION ENDED - {status}"
        net_pnl = pnl - fees
        message = (
            f"Trades: {trades}\n"
            f"Win Rate: {win_rate:.1%}\n"
            f"Gross P&L: Rs {pnl:,.0f}\n"
            f"Fees: Rs {fees:,.0f}\n"
            f"Net P&L: Rs {net_pnl:,.0f}"
        )
        
        self.send_alert(
            title=title,
            message=message,
            priority="high",
            tags="session,end"
        )
    
    def error_alert(self, error_type: str, error_message: str):
        """Send error alert"""
        title = f"[ERROR] {error_type}"
        message = error_message[:100]  # Limit message length
        
        self.send_alert(
            title=title,
            message=message,
            priority="max",
            tags="error,alert"
        )
    
    def api_connection_error(self, service: str):
        """Send API connection error"""
        title = f"[API] ERROR: {service}"
        message = f"Cannot connect to {service}. Check connection."
        
        self.send_alert(
            title=title,
            message=message,
            priority="max",
            tags="api,error"
        )
    
    def no_signal(self, reason: str):
        """Send no signal alert"""
        title = "[INFO] NO SIGNAL"
        message = f"Reason: {reason}"
        
        self.send_alert(
            title=title,
            message=message,
            priority="low",
            tags="no-signal,info"
        )
    
    def market_alert(self, alert_type: str, details: str):
        """Send generic market alert"""
        title = f"[MARKET] {alert_type.upper()}"
        message = details
        
        self.send_alert(
            title=title,
            message=message,
            priority="default",
            tags="market,alert"
        )
    
    def range_detected(self, symbol: str, range_type: str):
        """Send range detection alert"""
        title = f"[RANGE] DETECTED: {symbol}"
        message = f"Market in {range_type} regime. Reduced position size."
        
        self.send_alert(
            title=title,
            message=message,
            priority="low",
            tags="range,market"
        )
    
    def sentiment_update(self, sentiment: str, score: float):
        """Send market sentiment alert"""
        title = f"[SENTIMENT] {sentiment}"
        message = f"Score: {score:.2f}"
        
        self.send_alert(
            title=title,
            message=message,
            priority="default",
            tags="sentiment,market"
        )
    
    def daily_summary(self, trades: int, win_rate: float, pnl: float, 
                     best_trade: float, worst_trade: float):
        """Send daily summary alert"""
        title = "[SUMMARY] DAILY RESULTS"
        message = (
            f"Trades: {trades}\n"
            f"Win Rate: {win_rate:.1%}\n"
            f"P&L: Rs {pnl:,.0f}\n"
            f"Best: Rs {best_trade:,.0f}\n"
            f"Worst: Rs {worst_trade:,.0f}"
        )
        
        self.send_alert(
            title=title,
            message=message,
            priority="default",
            tags="summary,daily"
        )


# Global instance
_notification_service = None

def get_notification_service(topic: str = "trading-alerts") -> NtfyNotificationService:
    """Get or create global notification service"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NtfyNotificationService(topic=topic)
    return _notification_service


# Quick functions for easy access
def send_alert(title: str, message: str, priority: str = "default"):
    """Quick alert send"""
    service = get_notification_service()
    service.send_alert(title, message, priority)


def entry_signal(symbol: str, direction: str, confidence: float):
    """Entry signal notification"""
    service = get_notification_service()
    service.entry_signal(symbol, direction, confidence)


def exit_signal(symbol: str, exit_type: str, pnl: float, reason: str = "Exit Rule"):
    """Exit signal notification"""
    service = get_notification_service()
    service.exit_signal(symbol, exit_type, pnl, reason)


def stop_loss_hit(symbol: str, entry: float, exit: float, loss: float):
    """Stop loss alert"""
    service = get_notification_service()
    service.stop_loss_hit(symbol, entry, exit, loss)


def kill_switch(loss: float, threshold: float):
    """Kill switch alert"""
    service = get_notification_service()
    service.kill_switch_triggered(loss, threshold)
