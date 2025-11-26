"""
Notification Service for Email and Telegram alerts
"""
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import requests
from app.config import Config

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications via Email and Telegram"""
    
    def __init__(self):
        self.config = Config()
        
    def send_notification(self, message: str, notification_type: str = "INFO"):
        """
        Send notification via enabled channels
        
        Args:
            message: Message to send
            notification_type: Type of notification (INFO, WARNING, ERROR, TRADE)
        """
        try:
            # Format message with type and timestamp
            formatted_message = self._format_message(message, notification_type)
            
            # Send via enabled channels
            if self.config.EMAIL_ENABLED:
                self.send_email(formatted_message, notification_type)
            
            if self.config.TELEGRAM_ENABLED:
                self.send_telegram(formatted_message)
                
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def send_email(self, message: str, notification_type: str = "INFO"):
        """Send email notification"""
        try:
            if not self.config.EMAIL_ENABLED:
                return
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.EMAIL_FROM
            msg['To'] = self.config.EMAIL_TO
            msg['Subject'] = f"MyBreezeApp Alert - {notification_type}"
            
            # Add body
            msg.attach(MIMEText(message, 'plain'))
            
            # Create SMTP session
            with smtplib.SMTP(self.config.EMAIL_SMTP_SERVER, self.config.EMAIL_SMTP_PORT) as server:
                server.starttls()  # Enable TLS
                server.login(self.config.EMAIL_USERNAME, self.config.EMAIL_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email notification sent: {notification_type}")
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
    
    def send_telegram(self, message: str):
        """Send Telegram notification"""
        try:
            if not self.config.TELEGRAM_ENABLED:
                return
            
            url = f"https://api.telegram.org/bot{self.config.TELEGRAM_BOT_TOKEN}/sendMessage"
            
            payload = {
                'chat_id': self.config.TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("Telegram notification sent successfully")
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
    
    def _format_message(self, message: str, notification_type: str) -> str:
        """Format message with timestamp and type"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add emoji based on type
        emoji_map = {
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'TRADE': '💰',
            'SUCCESS': '✅'
        }
        
        emoji = emoji_map.get(notification_type, 'ℹ️')
        
        formatted = f"{emoji} <b>{notification_type}</b>\n"
        formatted += f"🕐 {timestamp}\n"
        formatted += f"🤖 MyBreezeApp\n\n"
        formatted += message
        
        return formatted
    
    def send_trade_notification(self, trade_data: dict):
        """Send specialized trade notification"""
        try:
            action = trade_data.get('action', 'UNKNOWN')
            instrument = trade_data.get('instrument', 'UNKNOWN')
            quantity = trade_data.get('quantity', 0)
            price = trade_data.get('price', 0)
            
            if action.upper() == 'BUY':
                message = f"🟢 <b>BUY ORDER EXECUTED</b>\n\n"
                message += f"📈 Symbol: {instrument}\n"
                message += f"📊 Quantity: {quantity:,}\n"
                message += f"💰 Price: ₹{price:.2f}\n"
                message += f"💵 Total Value: ₹{quantity * price:,.2f}\n"
                
                if 'stop_loss' in trade_data:
                    message += f"🛑 Stop Loss: ₹{trade_data['stop_loss']:.2f}\n"
                if 'target' in trade_data:
                    message += f"🎯 Target: ₹{trade_data['target']:.2f}\n"
                    
            elif action.upper() == 'SELL':
                message = f"🔴 <b>SELL ORDER EXECUTED</b>\n\n"
                message += f"📉 Symbol: {instrument}\n"
                message += f"📊 Quantity: {quantity:,}\n"
                message += f"💰 Price: ₹{price:.2f}\n"
                message += f"💵 Total Value: ₹{quantity * price:,.2f}\n"
                
                if 'pnl' in trade_data:
                    pnl = trade_data['pnl']
                    pnl_emoji = "💚" if pnl > 0 else "❤️"
                    message += f"{pnl_emoji} P&L: ₹{pnl:,.2f}\n"
                
                if 'reason' in trade_data:
                    message += f"📝 Reason: {trade_data['reason']}\n"
            
            self.send_notification(message, "TRADE")
            
        except Exception as e:
            logger.error(f"Error sending trade notification: {e}")
    
    def send_daily_summary(self, summary_data: dict):
        """Send daily trading summary"""
        try:
            message = f"📊 <b>DAILY TRADING SUMMARY</b>\n\n"
            
            # Portfolio metrics
            if 'total_pnl' in summary_data:
                pnl = summary_data['total_pnl']
                pnl_emoji = "💚" if pnl > 0 else "❤️"
                message += f"{pnl_emoji} Total P&L: ₹{pnl:,.2f}\n"
            
            if 'total_trades' in summary_data:
                message += f"🔢 Total Trades: {summary_data['total_trades']}\n"
            
            if 'winning_trades' in summary_data and 'losing_trades' in summary_data:
                winning = summary_data['winning_trades']
                losing = summary_data['losing_trades']
                win_rate = (winning / (winning + losing)) * 100 if (winning + losing) > 0 else 0
                message += f"📈 Winning Trades: {winning}\n"
                message += f"📉 Losing Trades: {losing}\n"
                message += f"🎯 Win Rate: {win_rate:.1f}%\n"
            
            if 'portfolio_value' in summary_data:
                message += f"💼 Portfolio Value: ₹{summary_data['portfolio_value']:,.2f}\n"
            
            # Active positions
            if 'active_positions' in summary_data:
                positions = summary_data['active_positions']
                message += f"📊 Active Positions: {len(positions)}\n"
                
                if positions:
                    message += "\n<b>Current Positions:</b>\n"
                    for pos in positions[:5]:  # Show max 5 positions
                        symbol = pos.get('symbol', 'N/A')
                        qty = pos.get('quantity', 0)
                        price = pos.get('current_price', 0)
                        pnl = pos.get('unrealized_pnl', 0)
                        pnl_emoji = "💚" if pnl > 0 else "❤️"
                        message += f"• {symbol}: {qty:,} @ ₹{price:.2f} {pnl_emoji}₹{pnl:,.2f}\n"
            
            self.send_notification(message, "INFO")
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
    
    def send_risk_alert(self, risk_data: dict):
        """Send risk management alert"""
        try:
            message = f"⚠️ <b>RISK ALERT</b>\n\n"
            
            if 'type' in risk_data:
                message += f"🚨 Alert Type: {risk_data['type']}\n"
            
            if 'description' in risk_data:
                message += f"📝 Description: {risk_data['description']}\n"
            
            if 'current_loss' in risk_data:
                message += f"📉 Current Loss: ₹{risk_data['current_loss']:,.2f}\n"
            
            if 'loss_limit' in risk_data:
                message += f"🛑 Loss Limit: ₹{risk_data['loss_limit']:,.2f}\n"
            
            if 'action_required' in risk_data:
                message += f"⚡ Action Required: {risk_data['action_required']}\n"
            
            self.send_notification(message, "WARNING")
            
        except Exception as e:
            logger.error(f"Error sending risk alert: {e}")
    
    def send_system_status(self, status_data: dict):
        """Send system status notification"""
        try:
            status = status_data.get('status', 'UNKNOWN')
            
            if status == 'STARTED':
                message = f"🟢 <b>SYSTEM STARTED</b>\n\n"
                message += f"🤖 MyBreezeApp is now running\n"
            elif status == 'STOPPED':
                message = f"🔴 <b>SYSTEM STOPPED</b>\n\n"
                message += f"🤖 MyBreezeApp has been stopped\n"
            elif status == 'ERROR':
                message = f"❌ <b>SYSTEM ERROR</b>\n\n"
                message += f"🚨 Error: {status_data.get('error', 'Unknown error')}\n"
            else:
                message = f"ℹ️ <b>SYSTEM STATUS</b>\n\n"
                message += f"📊 Status: {status}\n"
            
            if 'details' in status_data:
                message += f"📝 Details: {status_data['details']}\n"
            
            notification_type = "ERROR" if status == 'ERROR' else "INFO"
            self.send_notification(message, notification_type)
            
        except Exception as e:
            logger.error(f"Error sending system status: {e}")
    
    def test_notifications(self):
        """Test all notification channels"""
        try:
            test_message = "🧪 This is a test notification from MyBreezeApp"
            
            results = {
                'email': False,
                'telegram': False
            }
            
            if self.config.EMAIL_ENABLED:
                try:
                    self.send_email(test_message, "TEST")
                    results['email'] = True
                except Exception as e:
                    logger.error(f"Email test failed: {e}")
            
            if self.config.TELEGRAM_ENABLED:
                try:
                    self.send_telegram(test_message)
                    results['telegram'] = True
                except Exception as e:
                    logger.error(f"Telegram test failed: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error testing notifications: {e}")
            return {'email': False, 'telegram': False}