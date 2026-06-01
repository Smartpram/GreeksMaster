"""
STRATEGY REGIME MONITOR
Detects market regime changes in real-time and daily/weekly checks

Regime Classification:
- MEAN_REVERTING: avg_holding_days < 1.0 (intraday bounces, quick reversals)
- TRENDING: avg_holding_days > 2.0 (multi-day runs, sustained moves)
- UNKNOWN: 1.0 ≤ avg_holding_days ≤ 2.0 (insufficient data or transition)

Purpose: Alert when market conditions change so trading strategy can adapt
"""

import logging
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


class RegimeChangeType(Enum):
    """Types of regime changes"""
    MEAN_TO_TRENDING = "mean_reverting_to_trending"
    TRENDING_TO_MEAN = "trending_to_mean_reverting"
    UNKNOWN_TO_MEAN = "unknown_to_mean_reverting"
    UNKNOWN_TO_TRENDING = "unknown_to_trending"
    MEAN_TO_UNKNOWN = "mean_reverting_to_unknown"
    TRENDING_TO_UNKNOWN = "trending_to_unknown"
    NONE = "no_change"


@dataclass
class RegimeSnapshot:
    """Snapshot of market regime at a point in time"""
    timestamp: datetime
    regime: str
    avg_holding_days: float
    recent_trades_count: int
    profit_factor: float
    max_drawdown: float
    avg_pnl_pct: float
    data: Dict = field(default_factory=dict)


class StrategyRegimeMonitor:
    """
    Monitors market regime changes in real-time and logs trends.
    
    Responsibilities:
    1. Track current market regime (mean-reverting, trending, unknown)
    2. Detect regime changes and alert
    3. Daily/weekly regime summary for decision-making
    4. Historical tracking for re-enablement analysis
    5. Integration with unified strategy (auto-switch if needed)
    """
    
    def __init__(self, history_size: int = 200):
        """
        Initialize regime monitor
        
        Args:
            history_size: Number of trades to keep in history
        """
        self.history_size = history_size
        self.current_regime = 'unknown'
        self.previous_regime = 'unknown'
        self.regime_change_count = 0
        
        # History tracking
        self.regime_snapshots: List[RegimeSnapshot] = []
        self.regime_changes: List[Tuple[datetime, str, str]] = []  # timestamp, from, to
        self.daily_reports: Dict[str, Dict] = {}  # date -> report
        self.weekly_reports: Dict[str, Dict] = {}  # week -> report
        
        # Thresholds for regime classification
        self.thresholds = {
            'trending_threshold': 2.0,      # avg_holding > 2.0d = trending
            'mean_revert_threshold': 1.0,   # avg_holding < 1.0d = mean-reverting
            'extension_threshold': 0.2,     # < 20% of trades show extension
            'volatility_threshold': 200,    # abs(drawdown) > 200% = high vol
        }
        
        logger.info("✅ Regime Monitor initialized")
    
    # ========== CORE REGIME DETECTION ==========
    
    def detect_regime(self, recent_trades: List[Dict]) -> str:
        """
        Detect market regime from recent trade history.
        
        Algorithm:
        1. Calculate avg_holding_days from recent trades
        2. If avg < 1.0: MEAN_REVERTING
        3. If avg > 2.0: TRENDING
        4. Otherwise: UNKNOWN
        
        Args:
            recent_trades: List of recent trade dicts with 'holding_days' key
            
        Returns:
            Regime name: 'mean_reverting', 'trending', or 'unknown'
        """
        
        if not recent_trades:
            regime = 'unknown'
        else:
            holding_days_list = [t.get('holding_days', 0) for t in recent_trades]
            avg_holding = sum(holding_days_list) / len(holding_days_list)
            
            if avg_holding < self.thresholds['mean_revert_threshold']:
                regime = 'mean_reverting'
            elif avg_holding > self.thresholds['trending_threshold']:
                regime = 'trending'
            else:
                regime = 'unknown'
        
        return regime
    
    def update_regime(
        self,
        recent_trades: List[Dict],
        unified_manager=None,  # Optional link to UnifiedProfitBookingManager
    ) -> Tuple[str, bool]:
        """
        Update current regime and detect changes.
        
        Args:
            recent_trades: List of recent trade dicts
            unified_manager: Optional reference to UnifiedProfitBookingManager
            
        Returns:
            (current_regime, regime_changed)
        """
        
        self.previous_regime = self.current_regime
        self.current_regime = self.detect_regime(recent_trades)
        
        # Detect regime change
        regime_changed = self.current_regime != self.previous_regime and self.previous_regime != 'unknown'
        
        if regime_changed:
            self.regime_change_count += 1
            self._log_regime_change()
        
        # Optional: Update unified manager's regime
        if unified_manager:
            unified_manager.detect_market_regime(recent_trades)
        
        return self.current_regime, regime_changed
    
    def _log_regime_change(self):
        """Log regime change with details"""
        timestamp = datetime.now()
        change_type = self._get_change_type(self.previous_regime, self.current_regime)
        
        self.regime_changes.append((timestamp, self.previous_regime, self.current_regime))
        
        logger.warning(
            f"🔄 REGIME CHANGE #{self.regime_change_count}: "
            f"{self.previous_regime.upper()} → {self.current_regime.upper()} "
            f"({change_type.value})"
        )
        
        # Alert for specific transitions
        if change_type == RegimeChangeType.MEAN_TO_TRENDING:
            logger.info(
                "📈 Market transitioned to TRENDING - "
                "Trailing stops MAY be re-enabled after re-backtest"
            )
        elif change_type == RegimeChangeType.TRENDING_TO_MEAN:
            logger.critical(
                "📉 Market transitioned to MEAN-REVERTING - "
                "Trailing stops are DISALLOWED. Using FIXED_FULL_EXIT."
            )
    
    @staticmethod
    def _get_change_type(prev: str, curr: str) -> RegimeChangeType:
        """Map regime transition to change type"""
        mapping = {
            ('mean_reverting', 'trending'): RegimeChangeType.MEAN_TO_TRENDING,
            ('trending', 'mean_reverting'): RegimeChangeType.TRENDING_TO_MEAN,
            ('unknown', 'mean_reverting'): RegimeChangeType.UNKNOWN_TO_MEAN,
            ('unknown', 'trending'): RegimeChangeType.UNKNOWN_TO_TRENDING,
            ('mean_reverting', 'unknown'): RegimeChangeType.MEAN_TO_UNKNOWN,
            ('trending', 'unknown'): RegimeChangeType.TRENDING_TO_UNKNOWN,
        }
        return mapping.get((prev, curr), RegimeChangeType.NONE)
    
    # ========== SNAPSHOT & HISTORY ==========
    
    def create_snapshot(
        self,
        recent_trades: List[Dict],
        unified_manager=None,
    ) -> RegimeSnapshot:
        """
        Create a snapshot of current market state.
        
        Args:
            recent_trades: List of recent trades
            unified_manager: Optional UnifiedProfitBookingManager for stats
            
        Returns:
            RegimeSnapshot with current state
        """
        
        holding_days_list = [t.get('holding_days', 0) for t in recent_trades]
        avg_holding = sum(holding_days_list) / len(holding_days_list) if holding_days_list else 0
        
        # Get stats if manager provided
        if unified_manager:
            stats = unified_manager.get_strategy_stats()
            profit_factor = stats.get('profit_factor', 0)
            max_drawdown = stats.get('max_drawdown', 0)
            avg_pnl_pct = stats.get('avg_pnl_pct', 0)
        else:
            profit_factor = 0
            max_drawdown = 0
            avg_pnl_pct = 0
        
        snapshot = RegimeSnapshot(
            timestamp=datetime.now(),
            regime=self.current_regime,
            avg_holding_days=avg_holding,
            recent_trades_count=len(recent_trades),
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            avg_pnl_pct=avg_pnl_pct,
            data={
                'regime': self.current_regime,
                'avg_holding_days': round(avg_holding, 2),
                'trades': len(recent_trades),
                'pf': round(profit_factor, 2),
                'dd': round(max_drawdown, 2),
            },
        )
        
        self.regime_snapshots.append(snapshot)
        
        # Keep only recent snapshots
        if len(self.regime_snapshots) > self.history_size:
            self.regime_snapshots.pop(0)
        
        return snapshot
    
    # ========== DAILY MONITORING ==========
    
    def daily_regime_check(
        self,
        recent_trades: List[Dict],
        unified_manager=None,
    ) -> Dict:
        """
        Perform daily regime check. Called once at market close.
        
        Returns:
            Daily report with regime, stats, and alerts
        """
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Update regime
        current, changed = self.update_regime(recent_trades, unified_manager)
        
        # Create snapshot
        snapshot = self.create_snapshot(recent_trades, unified_manager)
        
        # Build report
        report = {
            'date': today,
            'timestamp': datetime.now().isoformat(),
            'regime': current,
            'regime_changed': changed,
            'previous_regime': self.previous_regime,
            'stats': {
                'avg_holding_days': snapshot.avg_holding_days,
                'trades_today': snapshot.recent_trades_count,
                'profit_factor': snapshot.profit_factor,
                'max_drawdown': snapshot.max_drawdown,
                'avg_pnl_pct': snapshot.avg_pnl_pct,
            },
            'alerts': [],
            'recommendations': [],
        }
        
        # Generate alerts
        report['alerts'] = self._generate_daily_alerts(snapshot)
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(snapshot, changed)
        
        # Log report
        self._log_daily_report(report)
        
        # Store report
        self.daily_reports[today] = report
        
        return report
    
    def _generate_daily_alerts(self, snapshot: RegimeSnapshot) -> List[str]:
        """Generate alerts based on daily snapshot"""
        alerts = []
        
        # Alert 1: Regime change
        if self.current_regime != self.previous_regime and self.previous_regime != 'unknown':
            alerts.append(
                f"🔄 Regime changed: {self.previous_regime} → {self.current_regime}"
            )
        
        # Alert 2: High drawdown
        if abs(snapshot.max_drawdown) > 100:
            alerts.append(
                f"⚠️ High drawdown detected: {snapshot.max_drawdown:.1f}%"
            )
        
        # Alert 3: Low profit factor
        if snapshot.profit_factor < 1.0 and snapshot.profit_factor > 0:
            alerts.append(
                f"⚠️ Profit factor below 1.0: {snapshot.profit_factor:.2f}"
            )
        
        # Alert 4: Low trade count (indication of low volatility/activity)
        if snapshot.recent_trades_count < 3:
            alerts.append(
                f"ℹ️ Low activity: {snapshot.recent_trades_count} trades today"
            )
        
        # Alert 5: Trailing stop warnings in mean-reverting
        if self.current_regime == 'mean_reverting' and snapshot.max_drawdown < -200:
            alerts.append(
                f"🚨 High post-target volatility in mean-reverting regime: {abs(snapshot.max_drawdown):.0f}%"
            )
        
        return alerts
    
    def _generate_recommendations(self, snapshot: RegimeSnapshot, regime_changed: bool) -> List[str]:
        """Generate recommendations based on conditions"""
        recommendations = []
        
        if regime_changed:
            if self.current_regime == 'trending':
                recommendations.append(
                    "✅ Trending detected - Consider re-backtesting for trailing stop re-enablement"
                )
            elif self.current_regime == 'mean_reverting':
                recommendations.append(
                    "❌ Mean-reverting detected - Stick to FIXED_FULL_EXIT, trailing disallowed"
                )
        
        if snapshot.profit_factor > 1.2:
            recommendations.append(
                "📈 Strategy performing well (PF > 1.2) - Continue current approach"
            )
        
        if snapshot.max_drawdown < -100:
            recommendations.append(
                "⚠️ Drawdown elevated - Monitor for regime changes or increased volatility"
            )
        
        if snapshot.avg_holding_days > 1.5:
            recommendations.append(
                "📊 Holding period increasing - Possible transition to trending regime"
            )
        
        return recommendations
    
    def _log_daily_report(self, report: Dict):
        """Log daily report in structured format"""
        logger.info(
            f"📊 DAILY REGIME REPORT ({report['date']}):\n"
            f"   Regime: {report['regime'].upper()} "
            f"{'(CHANGED)' if report['regime_changed'] else ''}\n"
            f"   Avg Holding: {report['stats']['avg_holding_days']:.2f}d\n"
            f"   Trades: {report['stats']['trades_today']}\n"
            f"   Profit Factor: {report['stats']['profit_factor']:.2f}\n"
            f"   Max Drawdown: {report['stats']['max_drawdown']:.1f}%\n"
            f"   Alerts: {len(report['alerts'])}\n"
            f"   Recommendations: {len(report['recommendations'])}"
        )
        
        for alert in report['alerts']:
            logger.warning(alert)
        
        for rec in report['recommendations']:
            logger.info(rec)
    
    # ========== WEEKLY MONITORING ==========
    
    def weekly_regime_summary(self) -> Dict:
        """
        Generate weekly regime summary (called once per week).
        
        Returns:
            Weekly report with trend analysis and regime stability
        """
        
        # Calculate week key
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_key = week_start.strftime('%Y-W%V')  # ISO week
        
        # Collect this week's snapshots
        week_snapshots = [s for s in self.regime_snapshots 
                         if s.timestamp >= week_start]
        
        if not week_snapshots:
            logger.warning("No snapshots for weekly report")
            return {}
        
        # Analyze regime stability
        regimes_this_week = [s.regime for s in week_snapshots]
        regime_counts = {r: regimes_this_week.count(r) for r in set(regimes_this_week)}
        
        avg_holding = sum([s.avg_holding_days for s in week_snapshots]) / len(week_snapshots)
        avg_pf = sum([s.profit_factor for s in week_snapshots]) / len(week_snapshots)
        avg_dd = sum([s.max_drawdown for s in week_snapshots]) / len(week_snapshots)
        
        # Detect regime trend
        regime_trend = self._analyze_regime_trend(week_snapshots)
        
        report = {
            'week': week_key,
            'date_range': f"{week_start.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}",
            'regime_distribution': regime_counts,
            'dominant_regime': max(regime_counts, key=regime_counts.get),
            'regime_changes_count': len([1 for c in self.regime_changes if c[0] >= week_start]),
            'regime_trend': regime_trend,
            'stats': {
                'avg_holding_days': round(avg_holding, 2),
                'avg_profit_factor': round(avg_pf, 2),
                'avg_max_drawdown': round(avg_dd, 2),
                'total_snapshots': len(week_snapshots),
            },
            'assessment': self._generate_weekly_assessment(regime_counts, regime_trend, avg_pf),
        }
        
        self.weekly_reports[week_key] = report
        
        self._log_weekly_report(report)
        
        return report
    
    @staticmethod
    def _analyze_regime_trend(snapshots: List[RegimeSnapshot]) -> str:
        """Analyze trend in regime changes"""
        if len(snapshots) < 2:
            return "insufficient_data"
        
        # Look at holding days trend
        first_half = snapshots[:len(snapshots)//2]
        second_half = snapshots[len(snapshots)//2:]
        
        avg_first = sum([s.avg_holding_days for s in first_half]) / len(first_half)
        avg_second = sum([s.avg_holding_days for s in second_half]) / len(second_half)
        
        if avg_second > avg_first * 1.2:  # > 20% increase
            return "trending_increasing"  # Toward trending
        elif avg_second < avg_first * 0.8:  # > 20% decrease
            return "mean_reverting_increasing"  # Toward mean-reverting
        else:
            return "stable"
    
    @staticmethod
    def _generate_weekly_assessment(regime_counts: Dict, trend: str, avg_pf: float) -> str:
        """Generate weekly assessment"""
        assessments = []
        
        if len(regime_counts) > 2:
            assessments.append("⚠️ Multiple regime changes detected (market unstable)")
        elif len(regime_counts) == 1:
            assessments.append("✅ Regime stable (no changes)")
        
        if trend == "trending_increasing":
            assessments.append("📈 Market transitioning toward trending")
        elif trend == "mean_reverting_increasing":
            assessments.append("📉 Market transitioning toward mean-reverting")
        
        if avg_pf > 1.2:
            assessments.append("✅ Strong week (PF > 1.2)")
        elif avg_pf < 0.8:
            assessments.append("⚠️ Weak week (PF < 0.8)")
        
        return " | ".join(assessments) if assessments else "📊 Average week"
    
    def _log_weekly_report(self, report: Dict):
        """Log weekly report"""
        logger.info(
            f"📅 WEEKLY REGIME SUMMARY ({report['week']}):\n"
            f"   Period: {report['date_range']}\n"
            f"   Dominant Regime: {report['dominant_regime'].upper()}\n"
            f"   Regime Distribution: {report['regime_distribution']}\n"
            f"   Regime Changes: {report['regime_changes_count']}\n"
            f"   Trend: {report['regime_trend']}\n"
            f"   Avg Holding: {report['stats']['avg_holding_days']:.2f}d\n"
            f"   Avg PF: {report['stats']['avg_profit_factor']:.2f}\n"
            f"   Assessment: {report['assessment']}"
        )
    
    # ========== DECISION SUPPORT ==========
    
    def should_enable_trailing(self) -> Tuple[bool, str]:
        """
        Decision support: Should trailing stops be enabled?
        
        Returns:
            (should_enable, reason)
        """
        
        # Check 1: Must be trending regime
        if self.current_regime != 'trending':
            return False, f"Current regime is {self.current_regime}, not trending"
        
        # Check 2: Regime must be stable (no recent changes)
        recent_changes = [c for c in self.regime_changes 
                         if c[0] > datetime.now() - timedelta(days=2)]
        if recent_changes:
            return False, "Regime unstable (changes in last 2 days)"
        
        # Check 3: Profit factor must be decent
        if self.regime_snapshots:
            avg_pf = sum([s.profit_factor for s in self.regime_snapshots[-10:]]) / 10
            if avg_pf < 1.05:
                return False, f"Profit factor too low ({avg_pf:.2f} < 1.05)"
        
        # All checks passed
        return True, "Conditions permit trailing (trending regime, stable, good PF)"
    
    def get_regime_status(self) -> Dict:
        """Get comprehensive regime status for logging/UI"""
        return {
            'current_regime': self.current_regime,
            'previous_regime': self.previous_regime,
            'regime_changes_total': self.regime_change_count,
            'daily_reports_count': len(self.daily_reports),
            'weekly_reports_count': len(self.weekly_reports),
            'recent_snapshots': [s.data for s in self.regime_snapshots[-5:]],  # Last 5
            'can_enable_trailing': self.should_enable_trailing()[0],
        }


# ============================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*70)
    print("REGIME MONITOR TEST")
    print("="*70)
    
    monitor = StrategyRegimeMonitor()
    
    # Test 1: Mean-reverting detection
    print("\nTest 1: Mean-reverting detection")
    mean_revert_trades = [
        {'holding_days': 0.1},
        {'holding_days': 0.2},
        {'holding_days': 0.15},
    ]
    regime = monitor.detect_regime(mean_revert_trades)
    print(f"Detected regime: {regime} (expected: mean_reverting)")
    assert regime == 'mean_reverting', "Failed mean-reverting detection"
    
    # Test 2: Trending detection
    print("\nTest 2: Trending detection")
    trending_trades = [
        {'holding_days': 2.5},
        {'holding_days': 3.0},
        {'holding_days': 2.1},
    ]
    regime = monitor.detect_regime(trending_trades)
    print(f"Detected regime: {regime} (expected: trending)")
    assert regime == 'trending', "Failed trending detection"
    
    # Test 3: Regime update
    print("\nTest 3: Regime change detection")
    current, changed = monitor.update_regime(mean_revert_trades)
    print(f"After update - Current: {current}, Changed: {changed}")
    
    current, changed = monitor.update_regime(trending_trades)
    print(f"After update - Current: {current}, Changed: {changed} (should be True)")
    assert changed == True, "Failed to detect regime change"
    
    # Test 4: Daily check
    print("\nTest 4: Daily regime check")
    report = monitor.daily_regime_check(mean_revert_trades)
    print(f"Daily report generated: {report['date']}")
    
    # Test 5: Status report
    print("\nTest 5: Status report")
    status = monitor.get_regime_status()
    print(f"Current regime: {status['current_regime']}")
    print(f"Total regime changes: {status['regime_changes_total']}")
    
    print("\n✅ All regime monitor tests passed!")
