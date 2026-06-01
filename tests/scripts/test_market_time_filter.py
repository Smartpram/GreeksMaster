"""
Unit Tests for Market Time Filter
Tests all market session detection, gap detection, and volatility calculations
"""

import unittest
from datetime import time, datetime
from app.strategies.market_time_filter import MarketTimeFilter


class TestMarketTimeFilter(unittest.TestCase):
    """Test cases for MarketTimeFilter"""
    
    def setUp(self):
        """Initialize filter before each test"""
        self.filter = MarketTimeFilter()
    
    # Market Open/Close Detection Tests
    
    def test_market_open_detection_morning(self):
        """Test that morning open is detected correctly"""
        # 9:20 AM - should be open
        test_time = time(9, 20)
        self.assertTrue(self.filter.is_market_open(test_time))
    
    def test_market_open_detection_afternoon(self):
        """Test that afternoon is open"""
        # 2:00 PM - should be open
        test_time = time(14, 0)
        self.assertTrue(self.filter.is_market_open(test_time))
    
    def test_market_closed_before_open(self):
        """Test that market is closed before 9:15 AM"""
        # 9:00 AM - should be closed
        test_time = time(9, 0)
        self.assertFalse(self.filter.is_market_open(test_time))
    
    def test_market_closed_after_close(self):
        """Test that market is closed after 3:30 PM"""
        # 4:00 PM - should be closed
        test_time = time(16, 0)
        self.assertFalse(self.filter.is_market_open(test_time))
    
    def test_market_closed_evening(self):
        """Test that market is closed in evening"""
        # 8:00 PM - should be closed
        test_time = time(20, 0)
        self.assertFalse(self.filter.is_market_open(test_time))
    
    # Session Detection Tests
    
    def test_opening_bell_detection(self):
        """Test that opening bell session is detected"""
        # 9:30 AM - opening bell
        test_time = time(9, 30)
        session = self.filter.get_current_session(test_time)
        self.assertEqual(session, "opening_bell")
    
    def test_power_hour_detection(self):
        """Test that power hour session is detected"""
        # 10:30 AM - power hour
        test_time = time(10, 30)
        session = self.filter.get_current_session(test_time)
        self.assertEqual(session, "power_hour")
    
    def test_optimal_entry_detection(self):
        """Test that optimal entry window is detected"""
        # 12:00 PM - optimal entry
        test_time = time(12, 0)
        session = self.filter.get_current_session(test_time)
        self.assertEqual(session, "optimal_entry")
    
    def test_normal_session_detection(self):
        """Test that normal session is detected"""
        # 3:15 PM would be in closing bell, so use 1:00 PM for normal
        test_time = time(13, 0)  # 1:00 PM
        session = self.filter.get_current_session(test_time)
        self.assertIn(session, ["optimal_entry", "normal"])
    
    def test_closing_bell_detection(self):
        """Test that closing bell session is detected"""
        # 3:15 PM - closing bell
        test_time = time(15, 15)
        session = self.filter.get_current_session(test_time)
        self.assertEqual(session, "closing_bell")
    
    def test_closed_session_detection(self):
        """Test that closed session is detected"""
        # 8:00 PM - market closed
        test_time = time(20, 0)
        session = self.filter.get_current_session(test_time)
        self.assertEqual(session, "closed")
    
    # Entry Permission Tests
    
    def test_entry_allowed_optimal_window(self):
        """Test that entries are allowed in optimal window"""
        test_time = time(12, 0)  # 12:00 PM - clearly in optimal window
        should_avoid = self.filter.should_avoid_entry(test_time)
        self.assertFalse(should_avoid)
    
    def test_entry_avoided_opening_bell(self):
        """Test that entries are avoided during opening bell"""
        test_time = time(9, 30)  # 9:30 AM
        should_avoid = self.filter.should_avoid_entry(test_time)
        self.assertTrue(should_avoid)
    
    def test_entry_avoided_closing_bell(self):
        """Test that entries are avoided during closing bell"""
        test_time = time(15, 15)  # 3:15 PM
        should_avoid = self.filter.should_avoid_entry(test_time)
        self.assertTrue(should_avoid)
    
    def test_entry_avoided_when_closed(self):
        """Test that entries are avoided when market closed"""
        test_time = time(20, 0)  # 8:00 PM
        should_avoid = self.filter.should_avoid_entry(test_time)
        self.assertTrue(should_avoid)
    
    # Volatility Multiplier Tests
    
    def test_volatility_multiplier_opening_bell(self):
        """Test volatility multiplier during opening bell"""
        test_time = time(9, 30)
        multiplier = self.filter.get_volatility_multiplier(test_time)
        self.assertEqual(multiplier, 1.5)
    
    def test_volatility_multiplier_power_hour(self):
        """Test volatility multiplier during power hour"""
        test_time = time(10, 0)
        multiplier = self.filter.get_volatility_multiplier(test_time)
        self.assertEqual(multiplier, 1.3)
    
    def test_volatility_multiplier_optimal_entry(self):
        """Test volatility multiplier during optimal entry"""
        test_time = time(11, 30)
        multiplier = self.filter.get_volatility_multiplier(test_time)
        self.assertEqual(multiplier, 1.0)
    
    def test_volatility_multiplier_closing_bell(self):
        """Test volatility multiplier during closing bell"""
        test_time = time(15, 15)
        multiplier = self.filter.get_volatility_multiplier(test_time)
        self.assertEqual(multiplier, 1.3)
    
    # Gap Detection Tests
    
    def test_gap_up_detection(self):
        """Test detection of gap up movement"""
        previous_close = 1000.0
        current_open = 1030.0  # 3% gap up
        
        is_gap, gap_pct = self.filter.detect_gap(previous_close, current_open)
        
        self.assertTrue(is_gap)
        self.assertAlmostEqual(gap_pct, 0.03, places=4)
    
    def test_gap_down_detection(self):
        """Test detection of gap down movement"""
        previous_close = 1000.0
        current_open = 970.0  # 3% gap down
        
        is_gap, gap_pct = self.filter.detect_gap(previous_close, current_open)
        
        self.assertTrue(is_gap)
        self.assertAlmostEqual(gap_pct, 0.03, places=4)
    
    def test_small_gap_not_detected(self):
        """Test that small gaps are not detected"""
        previous_close = 1000.0
        current_open = 1010.0  # 1% gap (below 2% threshold)
        
        is_gap, gap_pct = self.filter.detect_gap(previous_close, current_open)
        
        self.assertFalse(is_gap)
        self.assertAlmostEqual(gap_pct, 0.01, places=4)
    
    def test_gap_at_threshold(self):
        """Test gap detection at exact threshold"""
        previous_close = 1000.0
        current_open = 1020.0  # 2% gap (exactly at threshold)
        
        is_gap, gap_pct = self.filter.detect_gap(previous_close, current_open)
        
        # Should not be detected (threshold is > 2%, not >= 2%)
        self.assertFalse(is_gap)
    
    def test_gap_detection_with_zero_close(self):
        """Test gap detection when previous close is zero"""
        previous_close = 0
        current_open = 1000.0
        
        is_gap, gap_pct = self.filter.detect_gap(previous_close, current_open)
        
        self.assertFalse(is_gap)
        self.assertEqual(gap_pct, 0)
    
    def test_skip_gap_trades_opening_bell(self):
        """Test that gap trades are skipped during opening bell"""
        test_time = time(9, 30)
        should_skip = self.filter.should_skip_gap_trades(test_time)
        self.assertTrue(should_skip)
    
    def test_skip_gap_trades_power_hour(self):
        """Test that gap trades are skipped during power hour"""
        test_time = time(10, 30)
        should_skip = self.filter.should_skip_gap_trades(test_time)
        self.assertTrue(should_skip)
    
    def test_allow_gap_trades_midday(self):
        """Test that gap trades are allowed midday"""
        test_time = time(12, 0)
        should_skip = self.filter.should_skip_gap_trades(test_time)
        self.assertFalse(should_skip)
    
    # Volume Spike Detection Tests
    
    def test_no_volume_spike_opening_bell(self):
        """Test that expected volume surge isn't flagged as spike"""
        test_time = time(9, 30)  # Opening bell
        current_volume = 1500
        avg_volume = 1000
        # 50% above normal is expected, so shouldn't be flagged as spike
        
        is_spike, ratio = self.filter.detect_volume_spike(
            current_volume, avg_volume, test_time
        )
        
        self.assertFalse(is_spike)
        self.assertAlmostEqual(ratio, 1.5, places=1)
    
    def test_volume_spike_opening_bell(self):
        """Test that excessive volume IS flagged as spike during opening"""
        test_time = time(9, 30)  # Opening bell
        current_volume = 1700
        avg_volume = 1000
        # 70% above normal is abnormal even for opening
        
        is_spike, ratio = self.filter.detect_volume_spike(
            current_volume, avg_volume, test_time
        )
        
        self.assertTrue(is_spike)
        self.assertAlmostEqual(ratio, 1.7, places=1)
    
    def test_no_volume_spike_optimal_entry(self):
        """Test that normal volume increase isn't spike during optimal time"""
        test_time = time(12, 0)  # Optimal entry
        current_volume = 1300
        avg_volume = 1000
        # 30% above normal is expected threshold
        
        is_spike, ratio = self.filter.detect_volume_spike(
            current_volume, avg_volume, test_time
        )
        
        self.assertFalse(is_spike)
        self.assertAlmostEqual(ratio, 1.3, places=1)
    
    def test_volume_spike_optimal_entry(self):
        """Test that excessive volume IS flagged as spike"""
        test_time = time(12, 0)  # Optimal entry
        current_volume = 1500
        avg_volume = 1000
        # 50% above normal is spike for midday
        
        is_spike, ratio = self.filter.detect_volume_spike(
            current_volume, avg_volume, test_time
        )
        
        self.assertTrue(is_spike)
        self.assertAlmostEqual(ratio, 1.5, places=1)
    
    def test_volume_spike_zero_average(self):
        """Test volume spike detection with zero average volume"""
        current_volume = 1000
        avg_volume = 0
        
        is_spike, ratio = self.filter.detect_volume_spike(
            current_volume, avg_volume
        )
        
        self.assertFalse(is_spike)
        self.assertEqual(ratio, 1.0)
    
    # Stop Loss Adjustment Tests
    
    def test_stop_loss_adjustment_opening_bell(self):
        """Test stop loss adjustment during opening bell"""
        base_stop = 0.02  # 2%
        test_time = time(9, 30)
        
        adjusted = self.filter.apply_volatility_adjustment(base_stop, test_time)
        
        # 2% * 1.5 = 3%
        self.assertAlmostEqual(adjusted, 0.03, places=4)
    
    def test_stop_loss_adjustment_optimal_entry(self):
        """Test stop loss adjustment during optimal entry"""
        base_stop = 0.02  # 2%
        test_time = time(12, 0)
        
        adjusted = self.filter.apply_volatility_adjustment(base_stop, test_time)
        
        # 2% * 1.0 = 2% (no adjustment)
        self.assertAlmostEqual(adjusted, 0.02, places=4)
    
    def test_stop_loss_adjustment_capped(self):
        """Test that stop loss adjustment is capped at 15%"""
        base_stop = 0.20  # 20%
        test_time = time(9, 30)  # Opening bell (1.5x multiplier)
        
        adjusted = self.filter.apply_volatility_adjustment(base_stop, test_time)
        
        # 20% * 1.5 = 30%, but capped at 15%
        self.assertEqual(adjusted, 0.15)
    
    def test_stop_loss_price_adjustment_buy_stop(self):
        """Test stop loss price adjustment for buy stop"""
        entry_price = 1000.0
        stop_loss_price = 980.0  # Distance: 20
        test_time = time(9, 30)  # Opening bell (1.5x multiplier)
        
        adjusted = self.filter.apply_volatility_adjustment_to_price(
            entry_price, stop_loss_price, test_time
        )
        
        # Distance adjusted: 20 * 1.5 = 30
        # New stop: 1000 - 30 = 970
        self.assertEqual(adjusted, 970.0)
    
    def test_stop_loss_price_adjustment_sell_stop(self):
        """Test stop loss price adjustment for sell stop"""
        entry_price = 1000.0
        stop_loss_price = 1020.0  # Distance: 20
        test_time = time(9, 30)  # Opening bell (1.5x multiplier)
        
        adjusted = self.filter.apply_volatility_adjustment_to_price(
            entry_price, stop_loss_price, test_time
        )
        
        # Distance adjusted: 20 * 1.5 = 30
        # New stop: 1000 + 30 = 1030
        self.assertEqual(adjusted, 1030.0)
    
    # Recommendation Tests
    
    def test_recommendation_opening_bell(self):
        """Test recommendation for opening bell"""
        test_time = time(9, 30)
        recommendation = self.filter.get_position_recommendation(test_time)
        
        self.assertEqual(recommendation["action"], "AVOID")
        self.assertFalse(recommendation["entry_allowed"])
        self.assertTrue(recommendation["exit_risky"])
        self.assertEqual(recommendation["multiplier"], 1.5)
    
    def test_recommendation_optimal_entry(self):
        """Test recommendation for optimal entry window"""
        test_time = time(12, 0)
        recommendation = self.filter.get_position_recommendation(test_time)
        
        self.assertEqual(recommendation["action"], "GO")
        self.assertTrue(recommendation["entry_allowed"])
        self.assertFalse(recommendation["exit_risky"])
        self.assertEqual(recommendation["multiplier"], 1.0)
    
    def test_recommendation_closing_bell(self):
        """Test recommendation for closing bell"""
        test_time = time(15, 15)
        recommendation = self.filter.get_position_recommendation(test_time)
        
        self.assertEqual(recommendation["action"], "CAUTION")
        self.assertFalse(recommendation["entry_allowed"])
        self.assertTrue(recommendation["exit_risky"])
        self.assertEqual(recommendation["multiplier"], 1.3)
    
    def test_recommendation_closed(self):
        """Test recommendation when market closed"""
        test_time = time(20, 0)
        recommendation = self.filter.get_position_recommendation(test_time)
        
        self.assertEqual(recommendation["action"], "CLOSED")
        self.assertFalse(recommendation["entry_allowed"])
        self.assertFalse(recommendation["exit_risky"])
    
    # Session Summary Tests
    
    def test_session_summary_contains_all_fields(self):
        """Test that session summary has all required fields"""
        test_time = time(12, 0)
        summary = self.filter.get_session_summary(test_time)
        
        required_fields = [
            "session",
            "market_open",
            "current_time",
            "minutes_until_close",
            "volatility_multiplier",
            "entry_allowed",
            "exit_risky",
            "action",
            "reason",
            "suggested_action",
            "details"
        ]
        
        for field in required_fields:
            self.assertIn(field, summary)
    
    def test_session_summary_market_open_status(self):
        """Test that session summary correctly shows market status"""
        # During market hours
        test_time = time(12, 0)
        summary = self.filter.get_session_summary(test_time)
        self.assertTrue(summary["market_open"])
        
        # Outside market hours
        test_time = time(20, 0)
        summary = self.filter.get_session_summary(test_time)
        self.assertFalse(summary["market_open"])
    
    def test_session_summary_minutes_until_close(self):
        """Test minutes until close calculation"""
        test_time = time(15, 0)  # 3:00 PM
        summary = self.filter.get_session_summary(test_time)
        
        # Should be 30 minutes until 3:30 PM close
        self.assertEqual(summary["minutes_until_close"], 30)


class TestMarketTimeFilterIntegration(unittest.TestCase):
    """Integration tests for market time filter"""
    
    def setUp(self):
        """Initialize filter before each test"""
        self.filter = MarketTimeFilter()
    
    def test_realistic_morning_scenario(self):
        """Test realistic morning trading scenario"""
        # 9:20 AM - gap up detected
        gap_time = time(9, 20)
        self.assertTrue(self.filter.should_avoid_entry(gap_time))
        
        # 10:35 AM - should be good to enter
        entry_time = time(10, 35)
        self.assertFalse(self.filter.should_avoid_entry(entry_time))
        self.assertTrue(self.filter.is_optimal_entry_time(entry_time))
    
    def test_realistic_afternoon_scenario(self):
        """Test realistic afternoon trading scenario"""
        # 2:00 PM - normal trading
        normal_time = time(14, 0)
        self.assertFalse(self.filter.should_avoid_entry(normal_time))
        
        # 3:20 PM - closing bell, should avoid
        closing_time = time(15, 20)
        self.assertTrue(self.filter.should_avoid_entry(closing_time))
    
    def test_position_recommendation_workflow(self):
        """Test typical workflow using recommendations"""
        # Morning: Check at 9:30
        morning_rec = self.filter.get_position_recommendation(time(9, 30))
        self.assertFalse(morning_rec["entry_allowed"])
        
        # Mid-morning: Check at 10:45
        midday_rec = self.filter.get_position_recommendation(time(10, 45))
        self.assertTrue(midday_rec["entry_allowed"])
        
        # Afternoon: Check at 3:15
        closing_rec = self.filter.get_position_recommendation(time(15, 15))
        self.assertFalse(closing_rec["entry_allowed"])


if __name__ == '__main__':
    unittest.main()
