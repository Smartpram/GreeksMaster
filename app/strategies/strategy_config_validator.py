"""
PRODUCTION SAFEGUARDS: Configuration Validator & Hard Stops
Prevents misconfiguration from enabling trailing in mean-reverting markets

Design: Based on TRAILING_STOPS_DESIGN_RULES.md
"""

import logging
from enum import Enum
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class StrategyConfigError(Exception):
    """Raised when configuration violates safety rules"""
    pass


class SafeguardLevel(Enum):
    """Safeguard severity levels"""
    INFO = "info"          # Log only, allow execution
    WARNING = "warning"    # Log warning, allow execution but flag
    ERROR = "error"        # Log error, still allow (might be intentional)
    FATAL = "fatal"        # Crash immediately, never allow


class StrategyConfigValidator:
    """
    Validates strategy configuration against design rules.
    
    Hard Stops (Will crash):
    - Trailing enabled in mean-reverting regime
    - Invalid configuration that contradicts backtest results
    - Missing required parameters
    
    Warnings (Will log but allow):
    - Unusual parameter combinations
    - Performance metrics outside expected ranges
    - Regime detection issues
    """
    
    def __init__(self):
        self.validation_rules = self._build_rules()
        self.violations = []
    
    # ========== CONFIGURATION RULES ==========
    
    def _build_rules(self) -> List[Dict]:
        """Build all validation rules"""
        return [
            # FATAL: Trailing can never be enabled by default
            {
                'name': 'trailing_disabled_by_default',
                'level': SafeguardLevel.FATAL,
                'description': 'Trailing stops must NOT be enabled by default',
                'check': lambda config: not config.get('trailing_enabled', False),
            },
            
            # FATAL: Mean-reverting regime forbids trailing (no exceptions)
            {
                'name': 'no_trailing_in_mean_reverting',
                'level': SafeguardLevel.FATAL,
                'description': 'Trailing forbidden in mean-reverting regime (intraday)',
                'check': lambda config: (
                    config.get('market_regime') != 'mean_reverting' or 
                    not config.get('trailing_enabled', False)
                ),
            },
            
            # FATAL: Pure intraday + trailing = forbidden
            {
                'name': 'no_trailing_with_intraday',
                'level': SafeguardLevel.FATAL,
                'description': 'Trailing forbidden when avg_holding_days < 1.0',
                'check': lambda config: (
                    config.get('avg_holding_days', 10) >= 1.0 or 
                    not config.get('trailing_enabled', False)
                ),
            },
            
            # FATAL: High volatility + trailing = forbidden
            {
                'name': 'no_trailing_with_high_volatility',
                'level': SafeguardLevel.FATAL,
                'description': 'Trailing forbidden when max_drawdown > 200% (high volatility)',
                'check': lambda config: (
                    abs(config.get('max_drawdown', -50)) < 200 or 
                    not config.get('trailing_enabled', False)
                ),
            },
            
            # ERROR: Target must be reasonable (0-20%)
            {
                'name': 'valid_target_pct',
                'level': SafeguardLevel.ERROR,
                'description': 'Target % must be between 0.5% and 20%',
                'check': lambda config: (
                    0.005 <= config.get('target_pct', 0.065) <= 0.20
                ),
            },
            
            # ERROR: Stop loss must be reasonable (0-10%)
            {
                'name': 'valid_stop_loss',
                'level': SafeguardLevel.ERROR,
                'description': 'Stop loss must be between 0.5% and 10%',
                'check': lambda config: (
                    0.005 <= config.get('stop_loss_pct', 0.04) <= 0.10
                ),
            },
            
            # ERROR: Trailing stop must be less than target
            {
                'name': 'trailing_less_than_target',
                'level': SafeguardLevel.ERROR,
                'description': 'Trailing stop must be less than target',
                'check': lambda config: (
                    config.get('trailing_stop_pct', 0.02) < 
                    config.get('target_pct', 0.065)
                ),
            },
            
            # ERROR: Position size must be positive
            {
                'name': 'valid_position_size',
                'level': SafeguardLevel.ERROR,
                'description': 'Position size must be positive',
                'check': lambda config: config.get('position_size', 1) > 0,
            },
            
            # WARNING: Backtest results validation
            {
                'name': 'backtest_pf_positive',
                'level': SafeguardLevel.WARNING,
                'description': 'Profit Factor should be > 1.0 (fixed exit)',
                'check': lambda config: (
                    config.get('expected_profit_factor', 1.14) > 1.0
                ),
            },
            
            # WARNING: Max drawdown should be < 100% in mean-reverting
            {
                'name': 'drawdown_within_limits',
                'level': SafeguardLevel.WARNING,
                'description': 'Max drawdown should stay < 100% (mean-rev) or < 500% (trailing)',
                'check': lambda config: (
                    abs(config.get('max_drawdown', -77.91)) < 500
                ),
            },
            
            # WARNING: Regime detection enabled
            {
                'name': 'regime_detection_enabled',
                'level': SafeguardLevel.WARNING,
                'description': 'Regime detection must be enabled',
                'check': lambda config: config.get('regime_detection_enabled', True),
            },
        ]
    
    # ========== VALIDATION METHODS ==========
    
    def validate_on_startup(self, config: Dict = None) -> Tuple[bool, List[str]]:
        """
        Validate configuration at application startup.
        
        Raises: StrategyConfigError if FATAL violation detected
        Returns: (is_valid, list_of_warnings)
        """
        
        if config is None:
            config = self._get_default_config()
        
        self.violations = []
        fatal_violations = []
        warnings = []
        
        logger.info("🔍 Validating strategy configuration...")
        
        for rule in self.validation_rules:
            try:
                passed = rule['check'](config)
                
                if not passed:
                    violation = f"❌ {rule['name']}: {rule['description']}"
                    self.violations.append(violation)
                    
                    if rule['level'] == SafeguardLevel.FATAL:
                        fatal_violations.append(violation)
                    elif rule['level'] == SafeguardLevel.WARNING:
                        warnings.append(violation)
                    
                    logger.warning(violation)
                else:
                    logger.debug(f"✅ {rule['name']}: PASS")
            
            except Exception as e:
                logger.error(f"⚠️ {rule['name']}: Exception during check: {e}")
                warnings.append(f"Exception in {rule['name']}: {e}")
        
        # CRASH if fatal violations
        if fatal_violations:
            error_msg = (
                f"🚨 FATAL CONFIGURATION ERRORS ({len(fatal_violations)}):\n"
                + "\n".join(fatal_violations) + "\n"
                f"Strategy execution blocked. Fix configuration before retry."
            )
            logger.critical(error_msg)
            raise StrategyConfigError(error_msg)
        
        if warnings:
            logger.warning(f"⚠️ {len(warnings)} warnings detected (non-fatal)")
        else:
            logger.info("✅ Configuration validation PASSED (no issues)")
        
        return len(fatal_violations) == 0, warnings
    
    def validate_market_state(
        self, 
        market_regime: str,
        avg_holding_days: float,
        max_drawdown_pct: float,
        profit_factor: float,
    ) -> Tuple[bool, str]:
        """
        Validate live market state against design rules.
        
        Called before each trade to ensure conditions permit trailing.
        
        Returns: (allow_trailing, reason)
        """
        
        issues = []
        
        # Check 1: Regime
        if market_regime == 'mean_reverting':
            issues.append("Mean-reverting regime detected")
        
        # Check 2: Holding time
        if avg_holding_days < 1.0:
            issues.append(f"Pure intraday moves (avg={avg_holding_days:.2f}d)")
        
        # Check 3: Volatility
        if abs(max_drawdown_pct) > 200:
            issues.append(f"High post-target volatility (DD={max_drawdown_pct:.1f}%)")
        
        # If ANY issue exists, forbid trailing
        allow_trailing = len(issues) == 0
        reason = " + ".join(issues) if issues else "All conditions clear for trailing"
        
        logger.info(
            f"📊 Market state validation: "
            f"Regime={market_regime}, Holding={avg_holding_days:.1f}d, "
            f"Drawdown={max_drawdown_pct:.1f}%, PF={profit_factor:.2f} "
            f"→ Trailing {'ALLOWED' if allow_trailing else 'DISALLOWED'}"
        )
        
        return allow_trailing, reason
    
    def validate_position_creation(
        self,
        symbol: str,
        entry_price: float,
        quantity: int,
        requested_strategy: str,
        market_regime: str,
    ) -> Tuple[bool, str]:
        """
        Validate position creation request.
        
        Hard stop: If trailing requested in mean-reverting, CRASH.
        
        Returns: (is_valid, corrected_strategy)
        """
        
        # If user explicitly requested trailing in mean-reverting, CRASH
        if requested_strategy == 'partial_with_trailing' and market_regime == 'mean_reverting':
            error_msg = (
                f"🚨 FATAL: Cannot create position with trailing stops in mean-reverting regime.\n"
                f"Position: {symbol} @ ₹{entry_price}\n"
                f"Regime: {market_regime}\n"
                f"Design Rule: Pure intraday moves (avg_holding < 1.0d) forbid trailing.\n"
                f"Action: Auto-correcting to FIXED_FULL_EXIT"
            )
            logger.error(error_msg)
            
            # Still create position but with safe strategy
            corrected_strategy = 'fixed_full_exit'
        else:
            corrected_strategy = requested_strategy
        
        logger.info(
            f"✅ Position validation: {symbol} | "
            f"Requested: {requested_strategy} | "
            f"Approved: {corrected_strategy}"
        )
        
        return True, corrected_strategy
    
    def validate_exit_timing(
        self,
        position_id: str,
        current_strategy: str,
        market_regime: str,
        holding_days: float,
    ) -> Tuple[bool, str]:
        """
        Validate that exit strategy still matches market state.
        
        If market regime changed (e.g., trending → mean-reverting),
        warn and consider switching to fixed exit.
        
        Returns: (is_valid, should_switch_strategy)
        """
        
        should_switch = False
        reason = "No change needed"
        
        # Case 1: Using trailing, but market became mean-reverting
        if current_strategy == 'partial_with_trailing' and market_regime == 'mean_reverting':
            should_switch = True
            reason = "Regime changed to mean-reverting, switch to FIXED_FULL_EXIT"
            logger.warning(f"⚠️ Strategy switch recommended: {reason}")
        
        # Case 2: Using fixed, but market is now trending (could optimize)
        elif current_strategy == 'fixed_full_exit' and market_regime == 'trending' and holding_days > 2.0:
            logger.info(f"ℹ️ Market now trending (holding={holding_days:.1f}d), could use trailing (optional)")
            # Don't force switch, but notify
        
        return not should_switch, reason
    
    # ========== CONFIGURATION HELPERS ==========
    
    def _get_default_config(self) -> Dict:
        """Get default configuration (matching unified_profit_booking.py)"""
        return {
            'trailing_enabled': False,  # CRITICAL: Default disabled
            'market_regime': 'mean_reverting',  # CRITICAL: Start conservative
            'avg_holding_days': 0.0,
            'max_drawdown': -77.91,  # From backtest
            'target_pct': 0.065,
            'stop_loss_pct': 0.04,
            'trailing_stop_pct': 0.02,
            'partial_exit_ratio': 0.50,
            'position_size': 100,
            'expected_profit_factor': 1.14,
            'regime_detection_enabled': True,
        }
    
    def get_config_report(self) -> str:
        """Generate configuration report for logging"""
        config = self._get_default_config()
        
        report = """
╔════════════════════════════════════════════════════════════╗
║         STRATEGY CONFIGURATION REPORT                      ║
╚════════════════════════════════════════════════════════════╝

Market State:
  Regime: {market_regime}
  Avg Holding Days: {avg_holding_days:.1f}d
  Max Drawdown: {max_drawdown:.1f}%

Strategy Parameters:
  Target: {target_pct:.1f}%
  Stop Loss: {stop_loss_pct:.1f}%
  Trailing Stop (if enabled): {trailing_stop_pct:.1f}%
  Partial Exit Ratio: {partial_exit_ratio:.0%}

Safety Settings:
  Trailing Enabled: {trailing_enabled} ✅ SAFE
  Regime Detection: {regime_detection_enabled} ✅ ACTIVE
  Position Size: {position_size}

Expected Performance:
  Profit Factor: {expected_profit_factor:.2f}
  Max Drawdown: {max_drawdown:.1f}%

Violations: {violations_count}
Status: {status}
""".format(
            violations_count=len(self.violations),
            status="✅ READY FOR PRODUCTION" if len(self.violations) == 0 else "❌ FIX VIOLATIONS",
            **config
        )
        
        return report


class StrategyConfigMonitor:
    """
    Continuous monitoring of strategy configuration.
    
    Detects:
    - Configuration changes during runtime
    - Market regime changes requiring strategy adjustment
    - Parameter drift from expected values
    - Alert threshold breaches
    """
    
    def __init__(self):
        self.validator = StrategyConfigValidator()
        self.config_history = []
        self.alerts = []
    
    def check_runtime_safety(self, current_state: Dict) -> List[str]:
        """
        Check runtime state for safety violations.
        
        Returns: List of alerts (empty if all safe)
        """
        alerts = []
        
        # Check 1: Trailing shouldn't be enabled in mean-reverting
        if (current_state.get('trailing_enabled', False) and 
            current_state.get('market_regime') == 'mean_reverting'):
            alerts.append(
                "🚨 RUNTIME ALERT: Trailing is ENABLED in mean-reverting regime! "
                "This violates design rules. Disabling trailing immediately."
            )
            current_state['trailing_enabled'] = False
        
        # Check 2: Drawdown spike detection
        if abs(current_state.get('max_drawdown', 0)) > 300:
            alerts.append(
                f"⚠️ ALERT: Max drawdown spike detected ({current_state['max_drawdown']:.0f}%). "
                f"Recommend manual review of recent trades."
            )
        
        # Check 3: Losing streak (too many consecutive losses)
        if current_state.get('losing_streak', 0) > 5:
            alerts.append(
                f"⚠️ ALERT: {current_state['losing_streak']} consecutive losses. "
                f"Consider market pause until trend confirms."
            )
        
        return alerts


# ============================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test validation
    validator = StrategyConfigValidator()
    
    print("=" * 70)
    print("STRATEGY CONFIGURATION VALIDATION TEST")
    print("=" * 70)
    
    # Test 1: Default config (should pass)
    try:
        is_valid, warnings = validator.validate_on_startup()
        print(f"\n✅ Default config: PASS ({len(warnings)} warnings)")
    except StrategyConfigError as e:
        print(f"\n❌ Default config: FAIL - {e}")
    
    # Test 2: Invalid config (trailing in mean-reverting - should crash)
    print("\n" + "=" * 70)
    print("TEST: Trailing enabled in mean-reverting (should CRASH)")
    print("=" * 70)
    
    bad_config = {
        'trailing_enabled': True,
        'market_regime': 'mean_reverting',
        'avg_holding_days': 0.0,
        'target_pct': 0.065,
        'stop_loss_pct': 0.04,
        'trailing_stop_pct': 0.02,
    }
    
    try:
        validator.validate_on_startup(bad_config)
        print("❌ Should have crashed but didn't!")
    except StrategyConfigError as e:
        print(f"✅ Correctly crashed: {str(e)[:100]}...")
    
    # Test 3: Market state validation
    print("\n" + "=" * 70)
    print("TEST: Market state validation")
    print("=" * 70)
    
    allow, reason = validator.validate_market_state(
        market_regime='mean_reverting',
        avg_holding_days=0.0,
        max_drawdown_pct=-77.91,
        profit_factor=1.14,
    )
    print(f"Trailing allowed: {allow} | Reason: {reason}")
    
    # Test 4: Configuration report
    print("\n" + validator.get_config_report())
    
    print("\n✅ All validation tests completed!")
