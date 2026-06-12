"""
Options Screener - Multi-Strategy Screening Engine
====================================================

Implements 6 options-specific screeners:
1. IMPLIED VOLATILITY SCREENER - Find high IV opportunities
2. EARNINGS PLAY SCREENER - Identify earnings events + volatility
3. THETA DECAY SCREENER - Best theta decay opportunities
4. GREEKS + TECHNICAL SCREENER - Combined signal screening
5. PORTFOLIO HEDGING SCREENER - Pair trading opportunities
6. DELTA NEUTRAL SCREENER - Neutral position construction

Usage:
    from app.options_screener import OptionsScreener
    
    screener = OptionsScreener(api_service=breeze_api)
    
    # IV Screener
    iv_results = screener.screen_high_iv(iv_percentile_min=75)
    
    # Earnings Screener
    earnings_results = screener.screen_earnings_plays(days_to_earnings=14)
    
    # Theta Decay Screener
    theta_results = screener.screen_theta_decay(dte_range=(3, 8))
    
    # Greeks + Technical
    combo_results = screener.screen_greeks_technical_combo()
    
    # Hedging Pairs
    hedge_pairs = screener.screen_hedging_pairs(correlation_min=0.7)
    
    # Delta Neutral
    dn_setups = screener.screen_delta_neutral_setups()
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


class ScreenerType(Enum):
    """Options screener types"""
    IV_HIGH = "high_iv"
    IV_LOW = "low_iv"
    EARNINGS = "earnings"
    THETA_DECAY = "theta_decay"
    GREEKS_TECHNICAL = "greeks_technical"
    HEDGING_PAIRS = "hedging_pairs"
    DELTA_NEUTRAL = "delta_neutral"


@dataclass
class IVScreenerResult:
    """Result from IV Screener"""
    symbol: str
    current_price: float
    iv_percentile: float      # 0-100
    iv_rank: float            # IV vs 52-week range
    current_iv: float         # Current volatility
    iv_52_week_high: float
    iv_52_week_low: float
    iv_mean: float
    expected_move: float      # Dollar move expected
    expected_move_pct: float  # Percentage move
    premium_skew: str         # CALLS_RICH, PUTS_RICH, NEUTRAL
    recommendation: str       # SELL_CALLS, SELL_PUTS, STRADDLE, STRANGLE
    score: float              # 0-100, higher = better opportunity
    matched_at: datetime


@dataclass
class EarningsScreenerResult:
    """Result from Earnings Screener"""
    symbol: str
    current_price: float
    earnings_date: datetime
    days_to_earnings: int
    historical_iv_increase: float  # Historical IV % increase at earnings
    current_iv: float
    expected_iv_at_earnings: float  # Projected IV at earnings
    expected_move: float
    expected_move_pct: float
    historical_move: float          # Average actual move
    iv_crush_probability: float     # Probability of IV drop post-earnings
    suggested_strategy: str         # STRADDLE, STRANGLE, IRON_CONDOR
    entry_premium: float
    breakeven_move: float
    score: float
    matched_at: datetime


@dataclass
class ThetaDecayScreenerResult:
    """Result from Theta Decay Screener"""
    symbol: str
    current_price: float
    expiry_date: datetime
    days_to_expiry: int
    option_type: str                # CALL, PUT
    strike: float
    premium: float
    theta: float                    # Daily theta decay
    theta_acceleration: float       # How much faster theta decays
    vega: float
    implied_move_vs_realized: str   # IMPLIED_HIGH, REALIZED_HIGH, NEUTRAL
    theta_to_premium_ratio: float   # Higher = better efficiency
    expected_theta_by_expiry: float # Total theta until expiry
    suggested_strategy: str         # SELL, STRANGLE, CONDOR
    efficiency_score: float         # 0-100
    matched_at: datetime


@dataclass
class GreeksTechnicalResult:
    """Result from Greeks + Technical Screener"""
    symbol: str
    current_price: float
    technical_signal: str           # BUY, SELL, HOLD
    technical_score: float          # 0-100
    support_level: float
    resistance_level: float
    optimal_strike: float
    option_type: str                # CALL or PUT
    greeks_favorable: Dict[str, float]
    suggested_strategy: str
    combined_score: float           # 0-100
    entry_premium: float
    risk_reward_ratio: float
    matched_at: datetime


@dataclass
class HedgingPairResult:
    """Result from Hedging Pairs Screener"""
    symbol_long: str
    symbol_short: str
    correlation: float
    current_prices: Dict[str, float]
    delta_long: float
    delta_short: float
    combined_delta: float
    gamma_exposure: float
    vega_exposure: float
    theta_benefit: float
    hedge_ratio: float              # How many short contracts per long
    cost_of_hedge: float
    break_even_move: float
    protection_level: float         # Downside protected to X%
    upside_preserved: float         # Upside available to X%
    matched_at: datetime


@dataclass
class DeltaNeutralResult:
    """Result from Delta Neutral Screener"""
    setup_id: str
    symbol: str
    current_price: float
    long_legs: List[Dict]           # [{'strike': X, 'type': 'CALL', 'qty': 1, 'delta': 0.5}]
    short_legs: List[Dict]
    total_delta: float              # Should be ~0
    total_gamma: float
    total_theta: float
    total_vega: float
    net_premium: float              # Net debit or credit
    max_profit: float
    max_loss: float
    breakeven_points: List[float]
    profit_zones: List[Tuple[float, float]]  # [(zone_low, zone_high)]
    suggested_strategy: str         # BUTTERFLY, IRON_CONDOR, etc.
    efficiency_score: float
    matched_at: datetime


class OptionsScreener:
    """Advanced options screener with 6 different scanning modes"""
    
    # Underlying list to scan
    UNDERLYINGS = [
        'NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY',
        'INFY', 'TCS', 'LT', 'RELIANCE', 'HDFC', 'ICICIBANK',
        'BAJAJFINSV', 'KOTAKBANK', 'HDFCBANK', 'AXISBANK',
        'MARUTI', 'HEROMOTOCO', 'ASIANPAINT', 'SBIN', 'ITC'
    ]
    
    def __init__(self, api_service=None, cache_expiry_minutes: int = 5):
        """
        Initialize Options Screener
        
        Args:
            api_service: Breeze API service instance (for live data)
            cache_expiry_minutes: Cache expiry for data
        """
        self.api = api_service
        self.cache_expiry = cache_expiry_minutes * 60  # Convert to seconds
        self.cache = {}
        self.last_cache_update = {}
        
        logger.info("Options Screener initialized with 6 scanning modes")
    
    def _get_cached_data(self, key: str, fetch_func, *args, **kwargs) -> Dict:
        """Cache data for performance"""
        now = datetime.now().timestamp()
        
        if key in self.cache:
            last_update = self.last_cache_update.get(key, 0)
            if now - last_update < self.cache_expiry:
                return self.cache[key]
        
        data = fetch_func(*args, **kwargs)
        self.cache[key] = data
        self.last_cache_update[key] = now
        return data
    
    # =========================================================================
    # SCREENER 1: IMPLIED VOLATILITY SCREENER
    # =========================================================================
    
    def screen_high_iv(self, iv_percentile_min: float = 75, 
                      iv_percentile_max: float = 100,
                      limit: int = 20) -> List[IVScreenerResult]:
        """
        Screen for high implied volatility opportunities
        
        Best for: SELLING premium strategies (bull spreads, iron condors)
        
        Args:
            iv_percentile_min: Minimum IV percentile (0-100)
            iv_percentile_max: Maximum IV percentile
            limit: Maximum results to return
            
        Returns:
            List of high-IV opportunities sorted by IV percentile
        """
        results = []
        
        for symbol in self.UNDERLYINGS:
            try:
                # Get historical IV data
                iv_data = self._get_iv_data(symbol)
                if not iv_data:
                    continue
                
                current_iv = iv_data.get('current_iv', 0)
                iv_52w_high = iv_data.get('iv_52w_high', 0)
                iv_52w_low = iv_data.get('iv_52w_low', 0)
                iv_mean = iv_data.get('iv_mean', 0)
                
                # Calculate IV percentile
                if iv_52w_high != iv_52w_low:
                    iv_percentile = ((current_iv - iv_52w_low) / (iv_52w_high - iv_52w_low)) * 100
                else:
                    iv_percentile = 50
                
                # IV Rank: How current IV ranks against 52-week range
                iv_rank = iv_percentile
                
                # Get current price
                current_price = self._get_current_price(symbol)
                
                # Calculate expected move
                expected_move = current_price * current_iv / 100
                expected_move_pct = current_iv
                
                # Determine premium skew
                call_iv = iv_data.get('call_iv', current_iv)
                put_iv = iv_data.get('put_iv', current_iv)
                if call_iv > put_iv + 2:
                    premium_skew = "CALLS_RICH"
                    recommendation = "SELL_CALLS"
                elif put_iv > call_iv + 2:
                    premium_skew = "PUTS_RICH"
                    recommendation = "SELL_PUTS"
                else:
                    premium_skew = "NEUTRAL"
                    recommendation = "IRON_CONDOR"
                
                # Check if meets criteria
                if iv_percentile_min <= iv_percentile <= iv_percentile_max:
                    # Calculate score (higher IV = better for selling)
                    score = min(100, iv_percentile)
                    
                    result = IVScreenerResult(
                        symbol=symbol,
                        current_price=current_price,
                        iv_percentile=iv_percentile,
                        iv_rank=iv_rank,
                        current_iv=current_iv,
                        iv_52_week_high=iv_52w_high,
                        iv_52_week_low=iv_52w_low,
                        iv_mean=iv_mean,
                        expected_move=expected_move,
                        expected_move_pct=expected_move_pct,
                        premium_skew=premium_skew,
                        recommendation=recommendation,
                        score=score,
                        matched_at=datetime.now()
                    )
                    results.append(result)
            
            except Exception as e:
                logger.debug(f"Error screening {symbol} for IV: {e}")
                continue
        
        # Sort by IV percentile (highest first) and limit
        results.sort(key=lambda x: x.iv_percentile, reverse=True)
        return results[:limit]
    
    def screen_low_iv(self, iv_percentile_max: float = 25, 
                     limit: int = 20) -> List[IVScreenerResult]:
        """
        Screen for low IV opportunities
        
        Best for: BUYING premium strategies (long straddles, long strangles)
        """
        return self.screen_high_iv(iv_percentile_min=0, 
                                   iv_percentile_max=iv_percentile_max, 
                                   limit=limit)
    
    # =========================================================================
    # SCREENER 2: EARNINGS PLAY SCREENER
    # =========================================================================
    
    def screen_earnings_plays(self, days_to_earnings: int = 14,
                             historical_move_min_pct: float = 2.0,
                             limit: int = 20) -> List[EarningsScreenerResult]:
        """
        Screen for stocks with upcoming earnings and favorable volatility
        
        Best for: Straddle/strangle entry before earnings
        
        Args:
            days_to_earnings: Only include earnings within X days
            historical_move_min_pct: Only if average historical move >= X%
            limit: Maximum results
            
        Returns:
            List of earnings plays sorted by opportunity score
        """
        results = []
        
        for symbol in self.UNDERLYINGS:
            try:
                # Get earnings date
                earnings_date = self._get_earnings_date(symbol)
                if not earnings_date:
                    continue
                
                # Check if within date range
                days_until = (earnings_date - datetime.now()).days
                if days_until < 0 or days_until > days_to_earnings:
                    continue
                
                # Get IV data
                current_price = self._get_current_price(symbol)
                iv_data = self._get_iv_data(symbol)
                current_iv = iv_data.get('current_iv', 0)
                
                # Get historical earnings move
                historical_move = self._get_historical_earnings_move(symbol)
                historical_move_pct = (historical_move / current_price) * 100
                
                if historical_move_pct < historical_move_min_pct:
                    continue
                
                # Historical IV increase at earnings
                historical_iv_increase = self._get_historical_iv_increase(symbol)
                
                # Project IV at earnings
                expected_iv_at_earnings = current_iv * (1 + historical_iv_increase / 100)
                
                # Expected move based on IV
                expected_move = current_price * expected_iv_at_earnings / 100
                expected_move_pct = expected_iv_at_earnings
                
                # IV Crush probability (drops after earnings)
                iv_crush_prob = 0.70  # Typically 70% chance of IV crush
                
                # Suggested strategy
                if expected_move_pct > historical_move_pct * 1.2:
                    strategy = "STRADDLE"  # High move expected
                    entry_premium = current_price * expected_iv_at_earnings * 0.015  # ~1.5% of price
                else:
                    strategy = "STRANGLE"  # Moderate move
                    entry_premium = current_price * expected_iv_at_earnings * 0.010  # ~1% of price
                
                # Breakeven move (move needed to profit)
                breakeven_move = entry_premium
                
                # Calculate score
                move_ratio = expected_move_pct / entry_premium if entry_premium > 0 else 0
                score = min(100, move_ratio * 20)  # Scale to 0-100
                
                result = EarningsScreenerResult(
                    symbol=symbol,
                    current_price=current_price,
                    earnings_date=earnings_date,
                    days_to_earnings=days_until,
                    historical_iv_increase=historical_iv_increase,
                    current_iv=current_iv,
                    expected_iv_at_earnings=expected_iv_at_earnings,
                    expected_move=expected_move,
                    expected_move_pct=expected_move_pct,
                    historical_move=historical_move,
                    iv_crush_probability=iv_crush_prob,
                    suggested_strategy=strategy,
                    entry_premium=entry_premium,
                    breakeven_move=breakeven_move,
                    score=score,
                    matched_at=datetime.now()
                )
                results.append(result)
            
            except Exception as e:
                logger.debug(f"Error screening {symbol} for earnings: {e}")
                continue
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    # =========================================================================
    # SCREENER 3: THETA DECAY SCREENER
    # =========================================================================
    
    def screen_theta_decay(self, dte_range: Tuple[int, int] = (3, 8),
                          theta_min: float = -0.5,
                          implied_vs_realized: str = None,
                          limit: int = 50) -> List[ThetaDecayScreenerResult]:
        """
        Screen for best theta decay opportunities
        
        Best for: Pure theta decay plays (Iron Condors, Credit Spreads)
        
        Args:
            dte_range: Days to expiry range (min, max)
            theta_min: Minimum daily theta decay (negative number, e.g., -0.5)
            implied_vs_realized: Filter for 'IMPLIED_HIGH', 'REALIZED_HIGH', or None
            limit: Maximum results
            
        Returns:
            List of theta decay opportunities sorted by efficiency
        """
        results = []
        
        for symbol in self.UNDERLYINGS:
            try:
                # Get option chains for nearest expiry
                option_chain = self._get_option_chain(symbol)
                if not option_chain:
                    continue
                
                current_price = self._get_current_price(symbol)
                
                # Process each option
                for option in option_chain:
                    # Check DTE range
                    dte = option.get('days_to_expiry', 0)
                    if not (dte_range[0] <= dte <= dte_range[1]):
                        continue
                    
                    theta = option.get('theta', 0)
                    
                    # Check theta minimum (more negative = better for sellers)
                    if theta > theta_min:  # theta_min is negative
                        continue
                    
                    strike = option.get('strike', 0)
                    premium = option.get('premium', 0)
                    option_type = option.get('option_type', 'CALL')
                    vega = option.get('vega', 0)
                    
                    # Calculate theta acceleration (theta increases as expiry approaches)
                    theta_acceleration = abs(theta) / (dte if dte > 0 else 1)
                    
                    # Expected total theta by expiry
                    expected_theta_by_expiry = abs(theta) * dte
                    
                    # Implied vs Realized volatility
                    implied_vol = option.get('iv', 0)
                    realized_vol = self._get_realized_volatility(symbol)
                    
                    if implied_vol > realized_vol * 1.1:
                        iv_vs_realized = "IMPLIED_HIGH"
                    elif realized_vol > implied_vol * 1.1:
                        iv_vs_realized = "REALIZED_HIGH"
                    else:
                        iv_vs_realized = "NEUTRAL"
                    
                    # Filter if specified
                    if implied_vs_realized and iv_vs_realized != implied_vs_realized:
                        continue
                    
                    # Calculate efficiency score
                    theta_to_premium_ratio = abs(theta) / premium if premium > 0 else 0
                    efficiency_score = min(100, theta_to_premium_ratio * 50)
                    
                    # Strategy suggestion
                    if abs(theta) > 1.0:
                        strategy = "SELL"  # Sell directly
                    else:
                        strategy = "STRANGLE" if option_type == "CALL" else "CONDOR"
                    
                    result = ThetaDecayScreenerResult(
                        symbol=symbol,
                        current_price=current_price,
                        expiry_date=option.get('expiry_date'),
                        days_to_expiry=dte,
                        option_type=option_type,
                        strike=strike,
                        premium=premium,
                        theta=theta,
                        theta_acceleration=theta_acceleration,
                        vega=vega,
                        implied_move_vs_realized=iv_vs_realized,
                        theta_to_premium_ratio=theta_to_premium_ratio,
                        expected_theta_by_expiry=expected_theta_by_expiry,
                        suggested_strategy=strategy,
                        efficiency_score=efficiency_score,
                        matched_at=datetime.now()
                    )
                    results.append(result)
            
            except Exception as e:
                logger.debug(f"Error screening {symbol} for theta: {e}")
                continue
        
        # Sort by efficiency (highest first)
        results.sort(key=lambda x: x.efficiency_score, reverse=True)
        return results[:limit]
    
    # =========================================================================
    # SCREENER 4: GREEKS + TECHNICAL SCREENER
    # =========================================================================
    
    def screen_greeks_technical_combo(self, 
                                     technical_score_min: float = 60,
                                     greeks_favorable_weight: float = 0.7,
                                     limit: int = 20) -> List[GreeksTechnicalResult]:
        """
        Screen for combined technical + Greeks favorable setups
        
        Best for: High-probability setups with favorable Greeks
        
        Combines:
        - Technical signal (from stock screener)
        - Greeks metrics
        - Risk/reward ratio
        
        Args:
            technical_score_min: Minimum technical score (0-100)
            greeks_favorable_weight: Weight for Greeks favorability
            limit: Maximum results
            
        Returns:
            List of combo setups sorted by combined score
        """
        results = []
        
        for symbol in self.UNDERLYINGS:
            try:
                # Get technical signal
                tech_data = self._get_technical_signal(symbol)
                if not tech_data:
                    continue
                
                tech_signal = tech_data.get('signal', 'HOLD')
                tech_score = tech_data.get('score', 50)
                
                if tech_score < technical_score_min:
                    continue
                
                # Get support/resistance
                support = tech_data.get('support', 0)
                resistance = tech_data.get('resistance', 0)
                current_price = self._get_current_price(symbol)
                
                # Select optimal strike based on signal
                if tech_signal == 'BUY':
                    option_type = 'CALL'
                    # Find ATM or slightly OTM call
                    optimal_strike = self._find_atm_strike(symbol, current_price)
                elif tech_signal == 'SELL':
                    option_type = 'PUT'
                    # Find ATM or slightly OTM put
                    optimal_strike = self._find_atm_strike(symbol, current_price)
                else:
                    continue
                
                # Get Greeks for optimal strike
                greeks = self._get_greeks(symbol, optimal_strike, option_type)
                if not greeks:
                    continue
                
                # Greeks favorability analysis
                delta = greeks.get('delta', 0)
                vega = greeks.get('vega', 0)
                theta = greeks.get('theta', 0)
                gamma = greeks.get('gamma', 0)
                
                greeks_favorable = {
                    'delta': delta,
                    'vega': vega,
                    'theta': theta,
                    'gamma': gamma
                }
                
                # For BUY signals, prefer positive delta and theta
                # For SELL signals, prefer negative delta and positive theta
                if tech_signal == 'BUY':
                    greeks_score = min(100, 
                                      (delta * 50 +  # Positive delta good
                                       theta * 20 +  # Some positive theta good
                                       max(0, 10 - vega) * 5))  # Low vega good
                else:
                    greeks_score = min(100,
                                      (-delta * 50 +  # Negative delta good
                                       theta * 20 +  # Positive theta good
                                       max(0, 10 - vega) * 5))
                
                # Get premium
                entry_premium = self._get_premium(symbol, optimal_strike, option_type)
                
                # Calculate risk/reward
                if tech_signal == 'BUY':
                    risk = entry_premium
                    reward = (resistance - optimal_strike)
                else:
                    risk = entry_premium
                    reward = (optimal_strike - support)
                
                risk_reward_ratio = reward / risk if risk > 0 else 0
                
                # Combined score
                combined_score = (tech_score * 0.5 + 
                                greeks_score * greeks_favorable_weight)
                
                result = GreeksTechnicalResult(
                    symbol=symbol,
                    current_price=current_price,
                    technical_signal=tech_signal,
                    technical_score=tech_score,
                    support_level=support,
                    resistance_level=resistance,
                    optimal_strike=optimal_strike,
                    option_type=option_type,
                    greeks_favorable=greeks_favorable,
                    suggested_strategy=f"BULL_{option_type}S" if tech_signal == 'BUY' else f"BEAR_{option_type}S",
                    combined_score=combined_score,
                    entry_premium=entry_premium,
                    risk_reward_ratio=risk_reward_ratio,
                    matched_at=datetime.now()
                )
                results.append(result)
            
            except Exception as e:
                logger.debug(f"Error screening {symbol} for combo: {e}")
                continue
        
        # Sort by combined score
        results.sort(key=lambda x: x.combined_score, reverse=True)
        return results[:limit]
    
    # =========================================================================
    # SCREENER 5: PORTFOLIO HEDGING PAIRS SCREENER
    # =========================================================================
    
    def screen_hedging_pairs(self, correlation_min: float = 0.70,
                            days_to_expiry: int = 7,
                            limit: int = 10) -> List[HedgingPairResult]:
        """
        Screen for hedging pairs (highly correlated stocks)
        
        Best for: Hedging concentrated positions
        
        Finds pairs of stocks that:
        - Are highly correlated
        - Can be paired for Greeks neutrality
        - Have cost-efficient hedge ratios
        
        Args:
            correlation_min: Minimum correlation between pair
            days_to_expiry: Days to expiry for options
            limit: Maximum pairs to return
            
        Returns:
            List of hedging pair opportunities
        """
        results = []
        
        # Get correlation matrix for underlyings
        correlation_matrix = self._get_correlation_matrix()
        
        # Find pairs above correlation threshold
        underlyings = list(self.UNDERLYINGS)
        for i, symbol_long in enumerate(underlyings):
            for symbol_short in underlyings[i+1:]:
                try:
                    # Get correlation
                    corr = correlation_matrix.get((symbol_long, symbol_short), 0)
                    
                    if corr < correlation_min:
                        continue
                    
                    # Get prices
                    price_long = self._get_current_price(symbol_long)
                    price_short = self._get_current_price(symbol_short)
                    
                    if price_long <= 0 or price_short <= 0:
                        continue
                    
                    # Get Greeks for pairing
                    # Long: Buy OTM call (positive delta)
                    atm_long = self._find_atm_strike(symbol_long, price_long)
                    greeks_long = self._get_greeks(symbol_long, atm_long, 'CALL')
                    
                    # Short: Sell OTM call (negative delta)
                    atm_short = self._find_atm_strike(symbol_short, price_short)
                    greeks_short = self._get_greeks(symbol_short, atm_short, 'CALL')
                    
                    if not greeks_long or not greeks_short:
                        continue
                    
                    delta_long = greeks_long.get('delta', 0)
                    delta_short = greeks_short.get('delta', 0)
                    
                    # Calculate hedge ratio
                    if delta_short != 0:
                        hedge_ratio = abs(delta_long / delta_short)
                    else:
                        hedge_ratio = 1.0
                    
                    combined_delta = delta_long - (delta_short * hedge_ratio)
                    
                    # Get other Greeks
                    gamma_long = greeks_long.get('gamma', 0)
                    gamma_short = greeks_short.get('gamma', 0)
                    gamma_exposure = gamma_long - (gamma_short * hedge_ratio)
                    
                    vega_long = greeks_long.get('vega', 0)
                    vega_short = greeks_short.get('vega', 0)
                    vega_exposure = vega_long - (vega_short * hedge_ratio)
                    
                    theta_long = greeks_long.get('theta', 0)
                    theta_short = greeks_short.get('theta', 0)
                    theta_benefit = theta_long - (theta_short * hedge_ratio)
                    
                    # Cost of hedge
                    premium_long = self._get_premium(symbol_long, atm_long, 'CALL')
                    premium_short = self._get_premium(symbol_short, atm_short, 'CALL')
                    cost_of_hedge = (premium_long - premium_short * hedge_ratio)
                    
                    # Downside protection
                    protection_level = (1 - 0.02) * 100  # ~2% protection
                    upside_preserved = (1 + 0.05) * 100  # ~5% upside
                    
                    # Break even
                    breakeven_move = abs(cost_of_hedge)
                    
                    result = HedgingPairResult(
                        symbol_long=symbol_long,
                        symbol_short=symbol_short,
                        correlation=corr,
                        current_prices={
                            symbol_long: price_long,
                            symbol_short: price_short
                        },
                        delta_long=delta_long,
                        delta_short=delta_short,
                        combined_delta=combined_delta,
                        gamma_exposure=gamma_exposure,
                        vega_exposure=vega_exposure,
                        theta_benefit=theta_benefit,
                        hedge_ratio=hedge_ratio,
                        cost_of_hedge=cost_of_hedge,
                        break_even_move=breakeven_move,
                        protection_level=protection_level,
                        upside_preserved=upside_preserved,
                        matched_at=datetime.now()
                    )
                    results.append(result)
                
                except Exception as e:
                    logger.debug(f"Error pairing {symbol_long}-{symbol_short}: {e}")
                    continue
        
        # Sort by cost of hedge (lowest first)
        results.sort(key=lambda x: x.cost_of_hedge)
        return results[:limit]
    
    # =========================================================================
    # SCREENER 6: DELTA NEUTRAL SETUPS SCREENER
    # =========================================================================
    
    def screen_delta_neutral_setups(self, 
                                   delta_tolerance: float = 0.05,
                                   min_profit_factor: float = 2.0,
                                   limit: int = 15) -> List[DeltaNeutralResult]:
        """
        Screen for delta neutral position setups
        
        Best for: Volatility plays with defined risk
        
        Finds setups like:
        - Butterflies (long/short call spreads)
        - Iron Condors (neutral)
        - Ratio spreads
        
        Args:
            delta_tolerance: Acceptable combined delta range
            min_profit_factor: Min profit zone width factor
            limit: Maximum setups to return
            
        Returns:
            List of delta neutral setup opportunities
        """
        results = []
        
        for symbol in self.UNDERLYINGS:
            try:
                current_price = self._get_current_price(symbol)
                
                # Get option chain
                option_chain = self._get_option_chain(symbol)
                if not option_chain:
                    continue
                
                # Filter for near-term expiry (7-14 DTE optimal for butterflies)
                near_term = [opt for opt in option_chain if 7 <= opt.get('days_to_expiry', 0) <= 14]
                if not near_term:
                    continue
                
                # Find ATM strikes
                atm_strike = self._find_atm_strike(symbol, current_price)
                
                # Get nearby strikes (for spreads)
                strikes = sorted([opt.get('strike', 0) for opt in near_term if opt.get('strike', 0) > 0])
                if not strikes:
                    continue
                
                # Find indices of nearby strikes
                atm_idx = None
                for i, s in enumerate(strikes):
                    if abs(s - atm_strike) < 100:
                        atm_idx = i
                        break
                
                if atm_idx is None or atm_idx < 1 or atm_idx >= len(strikes) - 1:
                    continue
                
                # Setup 1: Butterfly (Long ATM Call, Short 2x OTM Calls, Long 2x OTM2 Calls)
                call_otm1 = strikes[atm_idx + 1] if atm_idx + 1 < len(strikes) else None
                call_otm2 = strikes[atm_idx + 2] if atm_idx + 2 < len(strikes) else None
                
                if call_otm1 and call_otm2:
                    try:
                        # Get Greeks
                        greeks_atm = self._get_greeks(symbol, atm_strike, 'CALL')
                        greeks_otm1 = self._get_greeks(symbol, call_otm1, 'CALL')
                        greeks_otm2 = self._get_greeks(symbol, call_otm2, 'CALL')
                        
                        if all([greeks_atm, greeks_otm1, greeks_otm2]):
                            # Butterfly structure: Long 1 ATM, Short 2 ATM+100, Long 1 ATM+200
                            total_delta = (greeks_atm.get('delta', 0) - 
                                         2 * greeks_otm1.get('delta', 0) + 
                                         greeks_otm2.get('delta', 0))
                            
                            if abs(total_delta) <= delta_tolerance:
                                # Calculate Greeks
                                total_gamma = (greeks_atm.get('gamma', 0) - 
                                             2 * greeks_otm1.get('gamma', 0) + 
                                             greeks_otm2.get('gamma', 0))
                                
                                total_theta = (greeks_atm.get('theta', 0) - 
                                             2 * greeks_otm1.get('theta', 0) + 
                                             greeks_otm2.get('theta', 0))
                                
                                total_vega = (greeks_atm.get('vega', 0) - 
                                            2 * greeks_otm1.get('vega', 0) + 
                                            greeks_otm2.get('vega', 0))
                                
                                # Premium
                                prem_atm = self._get_premium(symbol, atm_strike, 'CALL')
                                prem_otm1 = self._get_premium(symbol, call_otm1, 'CALL')
                                prem_otm2 = self._get_premium(symbol, call_otm2, 'CALL')
                                
                                net_premium = prem_atm - 2 * prem_otm1 + prem_otm2
                                
                                # Profit zones
                                strike_width = call_otm1 - atm_strike
                                max_profit = strike_width - abs(net_premium)
                                max_loss = abs(net_premium)
                                
                                profit_zone = (atm_strike + max(0, net_premium), 
                                             call_otm1 - max(0, net_premium))
                                
                                # Calculate efficiency score
                                profit_factor = (max_profit - max_loss) / max_loss if max_loss > 0 else 0
                                efficiency = min(100, profit_factor * 10)
                                
                                if efficiency > 50:
                                    result = DeltaNeutralResult(
                                        setup_id=f"BUTTERFLY_{symbol}_{atm_strike}",
                                        symbol=symbol,
                                        current_price=current_price,
                                        long_legs=[
                                            {'strike': atm_strike, 'type': 'CALL', 'qty': 1, 'delta': greeks_atm.get('delta', 0)},
                                            {'strike': call_otm2, 'type': 'CALL', 'qty': 1, 'delta': greeks_otm2.get('delta', 0)}
                                        ],
                                        short_legs=[
                                            {'strike': call_otm1, 'type': 'CALL', 'qty': 2, 'delta': greeks_otm1.get('delta', 0)}
                                        ],
                                        total_delta=total_delta,
                                        total_gamma=total_gamma,
                                        total_theta=total_theta,
                                        total_vega=total_vega,
                                        net_premium=net_premium,
                                        max_profit=max_profit,
                                        max_loss=max_loss,
                                        breakeven_points=[atm_strike, call_otm1],
                                        profit_zones=[profit_zone],
                                        suggested_strategy="BUTTERFLY",
                                        efficiency_score=efficiency,
                                        matched_at=datetime.now()
                                    )
                                    results.append(result)
                    except:
                        pass
            
            except Exception as e:
                logger.debug(f"Error screening {symbol} for delta neutral: {e}")
                continue
        
        # Sort by efficiency
        results.sort(key=lambda x: x.efficiency_score, reverse=True)
        return results[:limit]
    
    # =========================================================================
    # HELPER METHODS (Mock implementations - replace with real API calls)
    # =========================================================================
    
    def _get_iv_data(self, symbol: str) -> Optional[Dict]:
        """Get implied volatility data for symbol"""
        if not self.api:
            return {'current_iv': 20, 'iv_52w_high': 40, 'iv_52w_low': 10, 'iv_mean': 25}
        try:
            return self.api.get_iv_data(symbol)
        except:
            return None
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        if not self.api:
            return 100.0
        try:
            return self.api.get_current_price(symbol)
        except:
            return 0.0
    
    def _get_earnings_date(self, symbol: str) -> Optional[datetime]:
        """Get next earnings date"""
        return None  # Would fetch from API
    
    def _get_historical_earnings_move(self, symbol: str) -> float:
        """Get average historical earnings move"""
        if not self.api:
            return 5.0  # Mock: 5% move
        try:
            return self.api.get_historical_earnings_move(symbol)
        except:
            return 0.0
    
    def _get_historical_iv_increase(self, symbol: str) -> float:
        """Get historical IV increase at earnings"""
        return 50.0  # Mock: 50% IV increase
    
    def _get_option_chain(self, symbol: str) -> Optional[List[Dict]]:
        """Get option chain for symbol"""
        if not self.api:
            return []
        try:
            return self.api.get_option_chain(symbol)
        except:
            return None
    
    def _get_realized_volatility(self, symbol: str) -> float:
        """Get realized volatility for symbol"""
        return 18.0  # Mock
    
    def _get_technical_signal(self, symbol: str) -> Optional[Dict]:
        """Get technical signal for symbol"""
        return {'signal': 'BUY', 'score': 75, 'support': 95, 'resistance': 105}
    
    def _find_atm_strike(self, symbol: str, price: float) -> float:
        """Find ATM strike"""
        interval = 100  # Default
        return round(price / interval) * interval
    
    def _get_greeks(self, symbol: str, strike: float, option_type: str) -> Optional[Dict]:
        """Get Greeks for option"""
        return {'delta': 0.5, 'gamma': 0.02, 'theta': -0.5, 'vega': 0.15}
    
    def _get_premium(self, symbol: str, strike: float, option_type: str) -> float:
        """Get option premium"""
        return 10.0
    
    def _get_correlation_matrix(self) -> Dict[Tuple[str, str], float]:
        """Get correlation between symbol pairs"""
        return {}
    
    # =========================================================================
    # REPORTING METHODS
    # =========================================================================
    
    def print_iv_screener_results(self, results: List[IVScreenerResult], top_n: int = 10):
        """Print IV screener results"""
        print("\n" + "="*100)
        print("IMPLIED VOLATILITY SCREENER RESULTS".center(100))
        print("="*100)
        
        for i, result in enumerate(results[:top_n], 1):
            print(f"\n{i}. {result.symbol} @ ₹{result.current_price:.2f}")
            print(f"   IV Percentile: {result.iv_percentile:.1f}% | Current IV: {result.current_iv:.2f}%")
            print(f"   Expected Move: ₹{result.expected_move:.2f} ({result.expected_move_pct:.2f}%)")
            print(f"   Skew: {result.premium_skew} | Recommendation: {result.recommendation}")
            print(f"   Score: {result.score:.1f}/100")
    
    def print_earnings_screener_results(self, results: List[EarningsScreenerResult], top_n: int = 10):
        """Print earnings screener results"""
        print("\n" + "="*100)
        print("EARNINGS PLAY SCREENER RESULTS".center(100))
        print("="*100)
        
        for i, result in enumerate(results[:top_n], 1):
            print(f"\n{i}. {result.symbol} @ ₹{result.current_price:.2f}")
            print(f"   Earnings in {result.days_to_earnings} days | Move: ₹{result.expected_move:.2f} ({result.expected_move_pct:.2f}%)")
            print(f"   Strategy: {result.suggested_strategy} | Premium: ₹{result.entry_premium:.2f}")
            print(f"   IV Crush Probability: {result.iv_crush_probability*100:.0f}%")
            print(f"   Score: {result.score:.1f}/100")
    
    def print_theta_screener_results(self, results: List[ThetaDecayScreenerResult], top_n: int = 10):
        """Print theta decay screener results"""
        print("\n" + "="*100)
        print("THETA DECAY SCREENER RESULTS".center(100))
        print("="*100)
        
        for i, result in enumerate(results[:top_n], 1):
            print(f"\n{i}. {result.symbol} {result.option_type} {result.strike}")
            print(f"   DTE: {result.days_to_expiry} | Premium: ₹{result.premium:.2f}")
            print(f"   Daily Theta: ₹{result.theta:.2f} | Acceleration: {result.theta_acceleration:.3f}")
            print(f"   Expected Theta by Expiry: ₹{result.expected_theta_by_expiry:.2f}")
            print(f"   Strategy: {result.suggested_strategy} | Efficiency: {result.efficiency_score:.1f}/100")
    
    def print_combo_screener_results(self, results: List[GreeksTechnicalResult], top_n: int = 10):
        """Print Greek + Technical combo screener results"""
        print("\n" + "="*100)
        print("GREEKS + TECHNICAL COMBO SCREENER RESULTS".center(100))
        print("="*100)
        
        for i, result in enumerate(results[:top_n], 1):
            print(f"\n{i}. {result.symbol} @ ₹{result.current_price:.2f}")
            print(f"   Signal: {result.technical_signal} (Score: {result.technical_score:.0f}/100)")
            print(f"   Strategy: {result.suggested_strategy} {result.option_type} @ {result.optimal_strike}")
            print(f"   Risk/Reward: {result.risk_reward_ratio:.2f}")
            print(f"   Combined Score: {result.combined_score:.1f}/100")
    
    def print_hedging_pairs_results(self, results: List[HedgingPairResult], top_n: int = 10):
        """Print hedging pairs results"""
        print("\n" + "="*100)
        print("PORTFOLIO HEDGING PAIRS RESULTS".center(100))
        print("="*100)
        
        for i, result in enumerate(results[:top_n], 1):
            print(f"\n{i}. {result.symbol_long} [LONG] <-> {result.symbol_short} [SHORT]")
            print(f"   Correlation: {result.correlation:.3f}")
            print(f"   Hedge Ratio: 1:{result.hedge_ratio:.2f} | Cost: ₹{result.cost_of_hedge:.2f}")
            print(f"   Protection: {result.protection_level:.0f}% | Upside: {result.upside_preserved:.0f}%")
    
    def print_delta_neutral_results(self, results: List[DeltaNeutralResult], top_n: int = 10):
        """Print delta neutral setup results"""
        print("\n" + "="*100)
        print("DELTA NEUTRAL SETUPS RESULTS".center(100))
        print("="*100)
        
        for i, result in enumerate(results[:top_n], 1):
            print(f"\n{i}. {result.symbol} - {result.suggested_strategy}")
            print(f"   Combined Delta: {result.total_delta:.3f}")
            print(f"   Profit Zones: {result.profit_zones}")
            print(f"   Max Profit: ₹{result.max_profit:.2f} | Max Loss: ₹{result.max_loss:.2f}")
            print(f"   Efficiency: {result.efficiency_score:.1f}/100")
