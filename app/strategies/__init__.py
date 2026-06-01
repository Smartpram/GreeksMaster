"""
Strategies package initialization

Includes:
- Original strategies (8): Buy & Hold, Mean Reversion, Momentum, Trend Following, Breakout, VWAP, Optimized B&H, AI Enhanced
- Advanced equity strategies (4): VCP, Pairs Trading, Order Flow, PEAD
- Advanced options strategies (4): Delta-Neutral Vol, Vol Mean Reversion, Gamma Scalping, Options Momentum
"""

from .buy_hold_trend import BuyHoldTrendStrategy
from .mean_reversion import MeanReversionStrategy
from .momentum import MomentumStrategy
from .trend_following import TrendFollowingStrategy
from .breakout import BreakoutStrategy
from .vwap_intraday import VWAPStrategy
from .optimized_buy_hold_trend import OptimizedBuyHoldTrendStrategy
from .ai_enhanced_strategy import AIEnhancedStrategy

# Advanced strategies
try:
    from .advanced_strategies_suite import (
        VolatilityContractionPattern,
        StatisticalArbitrage,
        OrderFlowMicrostructure,
        PostEarningsAnnouncementDrift,
        DeltaNeutralVolatilityHarvesting,
        VolatilityMeanReversion,
        GammaScalping,
        DynamicOptionsMonitorTrendFollowing
    )
except ImportError as e:
    print(f"Warning: Could not import advanced strategies: {e}")

__all__ = [
    # Original strategies
    'BuyHoldTrendStrategy',
    'MeanReversionStrategy',
    'MomentumStrategy',
    'TrendFollowingStrategy',
    'BreakoutStrategy',
    'VWAPStrategy',
    'OptimizedBuyHoldTrendStrategy',
    'AIEnhancedStrategy',
    
    # Advanced equity strategies
    'VolatilityContractionPattern',
    'StatisticalArbitrage',
    'OrderFlowMicrostructure',
    'PostEarningsAnnouncementDrift',
    
    # Advanced options strategies
    'DeltaNeutralVolatilityHarvesting',
    'VolatilityMeanReversion',
    'GammaScalping',
    'DynamicOptionsMonitorTrendFollowing',
]