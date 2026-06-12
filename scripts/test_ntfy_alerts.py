#!/usr/bin/env python3
"""
ntfy Trading Alerts Demo & Test
Test all notification types
Run: python scripts/test_ntfy_alerts.py
"""

import sys
import os
from pathlib import Path

# Add scripts directory to path
scripts_dir = os.path.dirname(os.path.abspath(__file__))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from ntfy_notification_service import get_notification_service
import time

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_basic_alerts():
    """Test basic alert types"""
    print_section("1. BASIC ALERTS")
    
    service = get_notification_service(topic="mport")
    
    print("Sending: Session Started Alert...")
    service.session_started(capital=100000, max_loss=5000)
    time.sleep(1)
    
    print("✓ Sent")

def test_entry_exit_alerts():
    """Test entry and exit alerts"""
    print_section("2. ENTRY/EXIT ALERTS")
    
    service = get_notification_service(topic="mport")
    
    print("Sending: Entry Signal Alert...")
    service.entry_signal(
        symbol="BANKNIFTY",
        direction="BUY",
        confidence=0.85,
        strategy="ML Hybrid"
    )
    time.sleep(1)
    
    print("Sending: Profit Target Hit Alert...")
    service.profit_target_hit(
        symbol="BANKNIFTY",
        entry=48000,
        exit=48500,
        profit=1500
    )
    time.sleep(1)
    
    print("✓ Sent")

def test_stop_loss_alerts():
    """Test stop loss alerts"""
    print_section("3. STOP LOSS ALERTS")
    
    service = get_notification_service(topic="mport")
    
    print("Sending: Stop Loss Hit Alert...")
    service.stop_loss_hit(
        symbol="TCS",
        entry=3400,
        exit=3350,
        loss=500
    )
    time.sleep(1)
    
    print("✓ Sent")

def test_position_alerts():
    """Test position alerts"""
    print_section("4. POSITION ALERTS")
    
    service = get_notification_service(topic="mport")
    
    print("Sending: Position Opened Alert...")
    service.position_opened(
        symbol="NIFTY50",
        strategy="Options Bull Call Spread",
        entry=22000,
        qty=2,
        risk=20000
    )
    time.sleep(1)
    
    print("Sending: Position Closed Alert...")
    service.position_closed(
        symbol="NIFTY50",
        pnl=2500,
        trades=1
    )
    time.sleep(1)
    
    print("✓ Sent")

def test_kill_switch_alert():
    """Test kill switch alert"""
    print_section("5. KILL SWITCH ALERT")
    
    service = get_notification_service(topic="mport")
    
    print("Sending: Kill Switch Triggered Alert...")
    service.kill_switch_triggered(
        cumulative_loss=5500,
        threshold=5000
    )
    time.sleep(1)
    
    print("✓ Sent")

def test_session_summary_alert():
    """Test session summary alert"""
    print_section("6. SESSION SUMMARY ALERT")
    
    service = get_notification_service(topic="mport")
    
    print("Sending: Session Ended Alert...")
    service.session_ended(
        trades=18,
        win_rate=0.94,
        pnl=3500,
        fees=450
    )
    time.sleep(1)
    
    print("Sending: Daily Summary Alert...")
    service.daily_summary(
        trades=18,
        win_rate=0.94,
        pnl=3050,
        best_trade=850,
        worst_trade=-200
    )
    time.sleep(1)
    
    print("✓ Sent")

def test_error_alerts():
    """Test error alerts"""
    print_section("7. ERROR ALERTS")
    
    service = get_notification_service(topic="mport")
    
    print("Sending: API Connection Error Alert...")
    service.api_connection_error("Breeze API")
    time.sleep(1)
    
    print("Sending: Generic Error Alert...")
    service.error_alert(
        error_type="Module Import Failed",
        error_message="Cannot import trading_engine module"
    )
    time.sleep(1)
    
    print("✓ Sent")

def test_market_alerts():
    """Test market alerts"""
    print_section("8. MARKET ALERTS")
    
    service = get_notification_service(topic="mport")
    
    print("Sending: Range Detection Alert...")
    service.range_detected(
        symbol="BANKNIFTY",
        range_type="sideways"
    )
    time.sleep(1)
    
    print("Sending: Sentiment Update Alert...")
    service.sentiment_update(
        sentiment="BULLISH",
        score=0.72
    )
    time.sleep(1)
    
    print("✓ Sent")

def test_quick_functions():
    """Test quick convenience functions"""
    print_section("9. QUICK FUNCTIONS")
    
    print("Sending: Quick Entry Signal...")
    from ntfy_notification_service import entry_signal, stop_loss_hit, exit_signal
    
    entry_signal(
        symbol="FINTECH",
        direction="BUY",
        confidence=0.78
    )
    time.sleep(1)
    
    print("Sending: Quick Stop Loss Alert...")
    stop_loss_hit(
        symbol="FINTECH",
        entry=2500,
        exit=2450,
        loss=500
    )
    time.sleep(1)
    
    print("✓ Sent")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  ntfy TRADING ALERTS - TEST SUITE")
    print("="*60)
    print("\n🔔 Testing all alert types...")
    print("📱 Download ntfy app and subscribe to: mport")
    print("🌐 Or open: https://ntfy.sh/mport")
    print("\nYou should receive notifications on all your devices!")
    
    try:
        test_basic_alerts()
        test_entry_exit_alerts()
        test_stop_loss_alerts()
        test_position_alerts()
        test_kill_switch_alert()
        test_session_summary_alert()
        test_error_alerts()
        test_market_alerts()
        test_quick_functions()
        
        print_section("✅ ALL TESTS COMPLETED")
        print("🎉 ntfy integration working!")
        print("\nExpected behavior:")
        print("  ✓ Receive notifications on your phone/desktop")
        print("  ✓ Notifications appear in ntfy app")
        print("  ✓ Sound/vibration alerts (depending on priority)")
        print("  ✓ All categories tagged for filtering")
        print("\nNext: Integrate into trading scheduler!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
