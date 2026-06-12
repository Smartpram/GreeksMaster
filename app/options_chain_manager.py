"""
Phase 1: Options Chain Manager
Fetches and maintains live options chain data from Breeze API
Real-time updates with strike, IV, Greeks, premiums
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class OptionChain:
    """Represents a single option contract"""
    symbol: str
    strike: float
    option_type: str  # 'CE' (Call) or 'PE' (Put)
    expiry: str  # Format: "DD-MMM-YYYY"
    bid: float
    ask: float
    iv: float  # Implied Volatility (0.0-1.0)
    delta: float
    gamma: float
    theta: float
    vega: float
    open_interest: int
    last_traded_price: float
    timestamp: datetime


@dataclass
class OptionChainSnapshot:
    """Snapshot of all options for an underlying"""
    underlying: str
    timestamp: datetime
    expiries: List[str]  # Available expiries
    calls: List[OptionChain]
    puts: List[OptionChain]
    iv_percentile: float  # IV rank (0-100) for this underlying


class OptionsChainManager:
    """
    Manages live options chain data from Breeze API
    - Fetches and caches options chains
    - Updates every minute
    - Provides Greeks and volatility metrics
    """

    def __init__(self, breeze_client):
        """
        Initialize Options Chain Manager
        
        Args:
            breeze_client: BreezeConnect API client
        """
        self.breeze = breeze_client
        self.chains_cache: Dict[str, OptionChainSnapshot] = {}
        self.last_update: Dict[str, datetime] = {}
        self.iv_history: Dict[str, List[Tuple[datetime, float]]] = {}
        
    def fetch_option_chain(self, underlying: str, refresh: bool = False) -> Optional[OptionChainSnapshot]:
        """
        Fetch live options chain for underlying
        
        Args:
            underlying: NSE symbol (e.g., 'RELIANCE', 'BANKNIFTY')
            refresh: Force refresh from API
            
        Returns:
            OptionChainSnapshot with all available options
        """
        try:
            # Check cache (update every minute)
            if underlying in self.chains_cache and not refresh:
                if datetime.now() - self.last_update.get(underlying, datetime.min) < timedelta(minutes=1):
                    return self.chains_cache[underlying]
            
            # Fetch from Breeze API
            logger.info(f"[OPTIONS CHAIN] Fetching options chain for {underlying}")
            
            # Get available expiries for this underlying
            expiries = self._get_available_expiries(underlying)
            if not expiries:
                logger.warning(f"[OPTIONS CHAIN] No expiries found for {underlying}")
                return None
            
            calls = []
            puts = []
            
            # Fetch options for each expiry
            for expiry in expiries:
                expiry_calls, expiry_puts = self._fetch_options_for_expiry(underlying, expiry)
                calls.extend(expiry_calls)
                puts.extend(expiry_puts)
            
            # Calculate IV percentile (volatility rank)
            all_ivs = [opt.iv for opt in calls + puts]
            iv_percentile = self._calculate_iv_percentile(underlying, all_ivs)
            
            # Create snapshot
            snapshot = OptionChainSnapshot(
                underlying=underlying,
                timestamp=datetime.now(),
                expiries=expiries,
                calls=calls,
                puts=puts,
                iv_percentile=iv_percentile
            )
            
            # Cache and track
            self.chains_cache[underlying] = snapshot
            self.last_update[underlying] = datetime.now()
            self._update_iv_history(underlying, iv_percentile)
            
            logger.info(
                f"[OPTIONS CHAIN] {underlying}: {len(calls)} calls, {len(puts)} puts, "
                f"IV percentile: {iv_percentile:.1f}, Expiries: {expiries}"
            )
            return snapshot
            
        except Exception as e:
            logger.error(f"[OPTIONS CHAIN ERROR] Failed to fetch {underlying}: {str(e)}")
            return None
    
    def _get_available_expiries(self, underlying: str) -> List[str]:
        """
        Get available option expiries for underlying
        
        Returns: List of expiry dates (e.g., ['13-JUN-2026', '20-JUN-2026'])
        """
        try:
            # Get next 3 weekly expiries + next monthly
            today = datetime.now()
            
            expiries = []
            
            # Weekly expiries (Thursdays for NSE)
            for days_ahead in range(1, 22):
                next_date = today + timedelta(days=days_ahead)
                if next_date.weekday() == 3:  # Thursday
                    expiries.append(next_date.strftime("%d-%b-%Y").upper())
                    if len(expiries) >= 3:
                        break
            
            # Monthly expiry (last Thursday)
            month_ahead = today.month % 12 + 1
            year_ahead = today.year if today.month < 12 else today.year + 1
            
            # Find last Thursday of next month
            last_day = pd.Timestamp(year_ahead, month_ahead, 1) + pd.DateOffset(months=1) - pd.DateOffset(days=1)
            while last_day.weekday() != 3:  # Not Thursday
                last_day -= timedelta(days=1)
            
            if last_day > today:
                expiries.append(last_day.strftime("%d-%b-%Y").upper())
            
            return expiries[:4]  # Return top 4 expiries
            
        except Exception as e:
            logger.error(f"[OPTIONS CHAIN] Error getting expiries for {underlying}: {e}")
            return []
    
    def _fetch_options_for_expiry(self, underlying: str, expiry: str) -> Tuple[List[OptionChain], List[OptionChain]]:
        """
        Fetch all options (calls and puts) for specific expiry
        
        Args:
            underlying: Symbol
            expiry: Expiry date string
            
        Returns:
            Tuple of (calls_list, puts_list)
        """
        calls = []
        puts = []
        
        try:
            # Fetch option chain from Breeze
            # Note: Actual API call depends on Breeze API specifics
            # This is a template - adjust based on actual API
            
            option_chain_data = self.breeze.get_option_chain(
                exchange="NFO",  # NSE Futures & Options
                symbol=underlying,
                expiry_date=expiry
            )
            
            if not option_chain_data:
                return calls, puts
            
            # Parse option chain data
            for row in option_chain_data:
                try:
                    if row.get('type') == 'CE':  # Call option
                        call = OptionChain(
                            symbol=underlying,
                            strike=float(row.get('strike', 0)),
                            option_type='CE',
                            expiry=expiry,
                            bid=float(row.get('bid', 0)),
                            ask=float(row.get('ask', 0)),
                            iv=float(row.get('iv', 0)) / 100,  # Convert to decimal
                            delta=float(row.get('delta', 0)),
                            gamma=float(row.get('gamma', 0)),
                            theta=float(row.get('theta', 0)),
                            vega=float(row.get('vega', 0)),
                            open_interest=int(row.get('open_interest', 0)),
                            last_traded_price=float(row.get('ltp', 0)),
                            timestamp=datetime.now()
                        )
                        calls.append(call)
                        
                    elif row.get('type') == 'PE':  # Put option
                        put = OptionChain(
                            symbol=underlying,
                            strike=float(row.get('strike', 0)),
                            option_type='PE',
                            expiry=expiry,
                            bid=float(row.get('bid', 0)),
                            ask=float(row.get('ask', 0)),
                            iv=float(row.get('iv', 0)) / 100,
                            delta=float(row.get('delta', 0)),
                            gamma=float(row.get('gamma', 0)),
                            theta=float(row.get('theta', 0)),
                            vega=float(row.get('vega', 0)),
                            open_interest=int(row.get('open_interest', 0)),
                            last_traded_price=float(row.get('ltp', 0)),
                            timestamp=datetime.now()
                        )
                        puts.append(put)
                        
                except Exception as e:
                    logger.debug(f"Error parsing option row: {e}")
                    continue
            
            logger.info(f"[OPTIONS CHAIN] {underlying} {expiry}: {len(calls)} calls, {len(puts)} puts")
            return calls, puts
            
        except Exception as e:
            logger.error(f"[OPTIONS CHAIN] Error fetching {underlying} {expiry}: {e}")
            return calls, puts
    
    def _calculate_iv_percentile(self, underlying: str, ivs: List[float]) -> float:
        """
        Calculate IV percentile (IV rank) for volatility regime
        
        Returns: Value 0-100 (low IV vs high IV historically)
        """
        try:
            if not ivs:
                return 50.0
            
            avg_iv = np.mean(ivs)
            
            # Track historical IVs
            if underlying not in self.iv_history:
                self.iv_history[underlying] = []
            
            self.iv_history[underlying].append((datetime.now(), avg_iv))
            
            # Keep last 20 days of data
            cutoff_time = datetime.now() - timedelta(days=20)
            self.iv_history[underlying] = [
                (ts, iv) for ts, iv in self.iv_history[underlying]
                if ts > cutoff_time
            ]
            
            # Calculate percentile
            historical_ivs = [iv for _, iv in self.iv_history[underlying]]
            if len(historical_ivs) < 2:
                return 50.0
            
            percentile = (sum(1 for iv in historical_ivs if iv <= avg_iv) / len(historical_ivs)) * 100
            return percentile
            
        except Exception as e:
            logger.error(f"Error calculating IV percentile: {e}")
            return 50.0
    
    def _update_iv_history(self, underlying: str, iv_percentile: float):
        """Track IV percentile history for regime detection"""
        if underlying not in self.iv_history:
            self.iv_history[underlying] = []
        self.iv_history[underlying].append((datetime.now(), iv_percentile))
    
    def get_atm_strike(self, underlying: str, current_price: float, expiry: str) -> Optional[float]:
        """
        Get At-The-Money strike for given underlying and expiry
        
        Args:
            underlying: NSE symbol
            current_price: Current underlying price
            expiry: Option expiry
            
        Returns:
            ATM strike price (nearest to current price)
        """
        snapshot = self.fetch_option_chain(underlying)
        if not snapshot:
            return None
        
        calls = [opt for opt in snapshot.calls if opt.expiry == expiry]
        if not calls:
            return None
        
        # Find strike closest to current price
        atm_strike = min(calls, key=lambda x: abs(x.strike - current_price)).strike
        return atm_strike
    
    def get_option_greeks_by_strike(
        self, 
        underlying: str, 
        strike: float, 
        expiry: str, 
        option_type: str
    ) -> Optional[Dict]:
        """
        Get Greeks for specific option
        
        Args:
            underlying: NSE symbol
            strike: Strike price
            expiry: Option expiry
            option_type: 'CE' (call) or 'PE' (put)
            
        Returns:
            Dict with delta, gamma, theta, vega
        """
        snapshot = self.fetch_option_chain(underlying)
        if not snapshot:
            return None
        
        options = snapshot.calls if option_type == 'CE' else snapshot.puts
        
        option = next(
            (opt for opt in options if opt.strike == strike and opt.expiry == expiry),
            None
        )
        
        if not option:
            return None
        
        return {
            'delta': option.delta,
            'gamma': option.gamma,
            'theta': option.theta,
            'vega': option.vega,
            'iv': option.iv,
            'bid': option.bid,
            'ask': option.ask,
            'ltp': option.last_traded_price
        }
    
    def get_iv_regime(self, underlying: str) -> str:
        """
        Determine volatility regime for underlying
        
        Returns: 'HIGH' (>75th), 'LOW' (<25th), or 'NORMAL'
        """
        snapshot = self.fetch_option_chain(underlying)
        if not snapshot:
            return 'NORMAL'
        
        if snapshot.iv_percentile > 75:
            return 'HIGH'
        elif snapshot.iv_percentile < 25:
            return 'LOW'
        else:
            return 'NORMAL'
    
    def get_strikes_around(
        self, 
        underlying: str, 
        center_strike: float, 
        num_strikes: int = 5
    ) -> List[float]:
        """
        Get strikes around a center strike
        
        Args:
            underlying: NSE symbol
            center_strike: Center strike price
            num_strikes: Number of strikes on each side
            
        Returns:
            Sorted list of strike prices
        """
        snapshot = self.fetch_option_chain(underlying)
        if not snapshot:
            return []
        
        strikes = sorted(set(opt.strike for opt in snapshot.calls))
        
        # Find center index
        try:
            center_idx = min(
                range(len(strikes)),
                key=lambda i: abs(strikes[i] - center_strike)
            )
        except (ValueError, IndexError):
            return strikes[:num_strikes * 2 + 1]
        
        # Return strikes around center
        start_idx = max(0, center_idx - num_strikes)
        end_idx = min(len(strikes), center_idx + num_strikes + 1)
        
        return strikes[start_idx:end_idx]
