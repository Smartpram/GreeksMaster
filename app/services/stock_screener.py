"""
Stock Screener Integration with ICICIDirect Expert Screeners
Incorporates popular stock screening criteria and integrates with trading system

This module provides:
1. Pre-built screener templates (from ICICIDirect popular screeners)
2. Custom screening criteria builder
3. Real-time stock filtering
4. Watchlist management
5. Integration with order execution
"""

import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ScreenerType(Enum):
    """Popular screener types from ICICIDirect"""
    MOMENTUM = "momentum"              # High momentum stocks
    GROWTH = "growth"                  # Growth stocks
    VALUE = "value"                    # Undervalued stocks
    DIVIDEND = "dividend"              # High dividend yield
    PENNY = "penny"                    # Penny stocks
    SMALL_CAP = "small_cap"           # Small cap movers
    MID_CAP = "mid_cap"               # Mid cap growth
    LARGE_CAP = "large_cap"           # Large cap stable
    BREAKOUT = "breakout"             # Breakout stocks
    TURNAROUND = "turnaround"         # Recovery plays
    SECTOR_LEADERS = "sector_leaders" # Top performers by sector
    TECHNICAL_SETUP = "technical"     # Technical analysis setups


@dataclass
class ScreenerCriteria:
    """Individual screening criterion"""
    name: str
    field: str
    operator: str  # '>', '<', '==', 'in', 'between'
    value: any
    weight: float = 1.0  # Importance weight for scoring


@dataclass
class ScreenedStock:
    """Result of stock screening"""
    symbol: str
    name: str
    screener_type: ScreenerType
    score: float  # 0-100
    criteria_matched: List[str]
    price: float
    recommendation: str  # BUY, HOLD, SELL
    matched_at: datetime
    
    def to_dict(self):
        return {
            'symbol': self.symbol,
            'name': self.name,
            'screener': self.screener_type.value,
            'score': round(self.score, 2),
            'criteria': self.criteria_matched,
            'price': round(self.price, 2),
            'recommendation': self.recommendation,
            'matched_at': self.matched_at.isoformat()
        }


class StockScreener:
    """
    Advanced stock screening engine with ICICIDirect popular screeners
    """
    
    def __init__(self, breeze_api, risk_manager=None):
        """
        Initialize screener
        
        Args:
            breeze_api: BreezeAPIService instance
            risk_manager: Risk manager for portfolio constraints
        """
        self.api = breeze_api
        self.risk_manager = risk_manager
        self.screened_results = {}
        self.watchlist = {}
        self.last_scan = {}
        
        # Load pre-built screener definitions
        self.screeners = self._initialize_screeners()
        
    def _initialize_screeners(self) -> Dict:
        """Initialize pre-built screener templates"""
        return {
            ScreenerType.MOMENTUM: self._screener_momentum,
            ScreenerType.GROWTH: self._screener_growth,
            ScreenerType.VALUE: self._screener_value,
            ScreenerType.DIVIDEND: self._screener_dividend,
            ScreenerType.BREAKOUT: self._screener_breakout,
            ScreenerType.TECHNICAL_SETUP: self._screener_technical,
        }
    
    # ==================== SCREENER TEMPLATES ====================
    
    def _screener_momentum(self, stocks_df: pd.DataFrame) -> Tuple[List[ScreenedStock], List[str]]:
        """
        Momentum Screener - High momentum, accelerating trends
        
        Criteria:
        - RSI > 60 (uptrend without overbought)
        - Price > 50-day MA (above trend)
        - Volume > 20-day avg (high interest)
        - Daily gain > 2% (strength)
        """
        criteria = [
            ScreenerCriteria("RSI High", "rsi", ">", 60, weight=2.0),
            ScreenerCriteria("Above MA50", "price_vs_ma50", ">", 1.0, weight=1.5),
            ScreenerCriteria("Volume Surge", "volume_vs_avg", ">", 1.2, weight=1.5),
            ScreenerCriteria("Daily Gain", "daily_return", ">", 0.02, weight=1.0),
        ]
        
        return self._apply_criteria(stocks_df, criteria, ScreenerType.MOMENTUM)
    
    def _screener_growth(self, stocks_df: pd.DataFrame) -> Tuple[List[ScreenedStock], List[str]]:
        """
        Growth Screener - Growing companies with upward potential
        
        Criteria:
        - Revenue growth > 15% YoY
        - Profit margin improving
        - Price forming higher lows (uptrend)
        - Low debt ratio
        """
        criteria = [
            ScreenerCriteria("Revenue Growth", "revenue_growth", ">", 0.15, weight=2.0),
            ScreenerCriteria("Margin Trend", "margin_trend", ">", 0, weight=1.5),
            ScreenerCriteria("Higher Lows", "higher_lows", "==", True, weight=1.5),
            ScreenerCriteria("Low Debt", "debt_ratio", "<", 0.5, weight=1.0),
        ]
        
        return self._apply_criteria(stocks_df, criteria, ScreenerType.GROWTH)
    
    def _screener_value(self, stocks_df: pd.DataFrame) -> Tuple[List[ScreenedStock], List[str]]:
        """
        Value Screener - Undervalued stocks trading below intrinsic value
        
        Criteria:
        - P/E ratio < sector average
        - P/B ratio < 1.5
        - Trading > 50% below 52-week high
        - Strong fundamentals
        """
        criteria = [
            ScreenerCriteria("Low P/E", "pe_vs_sector", "<", 0.8, weight=2.0),
            ScreenerCriteria("Low P/B", "pb_ratio", "<", 1.5, weight=1.5),
            ScreenerCriteria("Below 52W High", "price_vs_52w_high", "<", 0.5, weight=1.5),
            ScreenerCriteria("Strong Fundamentals", "fundamentals_score", ">", 7, weight=1.0),
        ]
        
        return self._apply_criteria(stocks_df, criteria, ScreenerType.VALUE)
    
    def _screener_dividend(self, stocks_df: pd.DataFrame) -> Tuple[List[ScreenedStock], List[str]]:
        """
        Dividend Screener - High dividend yielding stocks
        
        Criteria:
        - Dividend yield > 4%
        - Payout ratio sustainable (30-60%)
        - Dividend growth streak > 3 years
        - Stable prices (low volatility)
        """
        criteria = [
            ScreenerCriteria("High Yield", "dividend_yield", ">", 0.04, weight=2.0),
            ScreenerCriteria("Sustainable Payout", "payout_ratio", "between", (0.3, 0.6), weight=1.5),
            ScreenerCriteria("Dividend Growth", "dividend_growth_years", ">", 3, weight=1.5),
            ScreenerCriteria("Low Volatility", "volatility", "<", 0.25, weight=1.0),
        ]
        
        return self._apply_criteria(stocks_df, criteria, ScreenerType.DIVIDEND)
    
    def _screener_breakout(self, stocks_df: pd.DataFrame) -> Tuple[List[ScreenedStock], List[str]]:
        """
        Breakout Screener - Stocks breaking through key resistance
        
        Criteria:
        - Price > 52-week high (all-time high setup)
        - Volume > 200% of 20-day average (confirmation)
        - MACD positive (momentum)
        - RSI < 70 (room to run)
        """
        criteria = [
            ScreenerCriteria("New High", "price_vs_52w_high", ">", 0.95, weight=2.0),
            ScreenerCriteria("Volume Explosion", "volume_vs_avg", ">", 2.0, weight=2.0),
            ScreenerCriteria("MACD Positive", "macd_signal", ">", 0, weight=1.5),
            ScreenerCriteria("RSI Room", "rsi", "<", 70, weight=1.0),
        ]
        
        return self._apply_criteria(stocks_df, criteria, ScreenerType.BREAKOUT)
    
    def _screener_technical(self, stocks_df: pd.DataFrame) -> Tuple[List[ScreenedStock], List[str]]:
        """
        Technical Setup Screener - Perfect technical setups for entry
        
        Criteria:
        - Golden cross (MA20 > MA50 > MA200)
        - RSI 30-70 (optimal zone)
        - Bollinger band setup (touching lower band)
        - MACD crossover (bullish)
        """
        criteria = [
            ScreenerCriteria("Golden Cross", "golden_cross", "==", True, weight=2.0),
            ScreenerCriteria("RSI Optimal", "rsi", "between", (30, 70), weight=1.5),
            ScreenerCriteria("BB Setup", "bollinger_setup", "==", True, weight=1.5),
            ScreenerCriteria("MACD Crossover", "macd_crossover", "==", True, weight=1.5),
        ]
        
        return self._apply_criteria(stocks_df, criteria, ScreenerType.TECHNICAL_SETUP)
    
    # ==================== CORE SCREENING LOGIC ====================
    
    def _apply_criteria(self, stocks_df: pd.DataFrame, criteria: List[ScreenerCriteria], 
                       screener_type: ScreenerType) -> Tuple[List[ScreenedStock], List[str]]:
        """
        Apply screening criteria to stock dataframe
        
        Returns:
            Tuple of (screened stocks, unmatched reasons)
        """
        results = []
        unmatched = []
        
        for _, stock in stocks_df.iterrows():
            score = 0
            matched_criteria = []
            failed_criteria = []
            
            for criterion in criteria:
                try:
                    value = stock.get(criterion.field, None)
                    
                    # Check criterion
                    if criterion.operator == ">":
                        matches = value > criterion.value
                    elif criterion.operator == "<":
                        matches = value < criterion.value
                    elif criterion.operator == "==":
                        matches = value == criterion.value
                    elif criterion.operator == "in":
                        matches = value in criterion.value
                    elif criterion.operator == "between":
                        matches = criterion.value[0] <= value <= criterion.value[1]
                    else:
                        matches = False
                    
                    if matches:
                        score += criterion.weight
                        matched_criteria.append(criterion.name)
                    else:
                        failed_criteria.append(criterion.name)
                        
                except Exception as e:
                    logger.debug(f"Criterion check failed for {stock.get('symbol')}: {e}")
                    failed_criteria.append(criterion.name)
            
            # Normalize score (0-100)
            max_score = sum(c.weight for c in criteria)
            normalized_score = (score / max_score * 100) if max_score > 0 else 0
            
            # Include stock if it matches at least 50% of criteria
            if len(matched_criteria) >= len(criteria) * 0.5:
                screened_stock = ScreenedStock(
                    symbol=stock.get('symbol', 'UNKNOWN'),
                    name=stock.get('name', 'Unknown Company'),
                    screener_type=screener_type,
                    score=normalized_score,
                    criteria_matched=matched_criteria,
                    price=stock.get('price', 0),
                    recommendation=self._get_recommendation(normalized_score, screener_type),
                    matched_at=datetime.now()
                )
                results.append(screened_stock)
            else:
                unmatched.append(f"{stock.get('symbol')}: Missing {failed_criteria}")
        
        return results, unmatched
    
    def _get_recommendation(self, score: float, screener_type: ScreenerType) -> str:
        """Generate recommendation based on score and screener type"""
        if score >= 80:
            return "STRONG BUY"
        elif score >= 65:
            return "BUY"
        elif score >= 50:
            return "HOLD"
        else:
            return "SELL"
    
    # ==================== PUBLIC INTERFACE ====================
    
    def run_screener(self, screener_type: ScreenerType, stocks_df: pd.DataFrame) -> Dict:
        """
        Run a specific screener on stocks data
        
        Args:
            screener_type: Type of screener to run
            stocks_df: DataFrame with stock data
            
        Returns:
            Dictionary with results and metadata
        """
        try:
            if screener_type not in self.screeners:
                raise ValueError(f"Unknown screener: {screener_type}")
            
            screener_func = self.screeners[screener_type]
            results, unmatched = screener_func(stocks_df)
            
            # Sort by score
            results = sorted(results, key=lambda x: x.score, reverse=True)
            
            # Store results
            self.screened_results[screener_type] = results
            self.last_scan[screener_type] = datetime.now()
            
            logger.info(f"Screener {screener_type.value}: Found {len(results)} matching stocks")
            
            return {
                'success': True,
                'screener': screener_type.value,
                'matches': [s.to_dict() for s in results],
                'count': len(results),
                'top_picks': [s.to_dict() for s in results[:5]],  # Top 5 matches
                'scan_time': datetime.now().isoformat(),
                'unmatched_count': len(unmatched)
            }
            
        except Exception as e:
            logger.error(f"Screener execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'screener': screener_type.value if screener_type else 'unknown'
            }
    
    def run_all_screeners(self, stocks_df: pd.DataFrame) -> Dict:
        """
        Run all available screeners and aggregate results
        
        Returns:
            Dictionary with all screener results
        """
        all_results = {}
        
        for screener_type in ScreenerType:
            result = self.run_screener(screener_type, stocks_df)
            all_results[screener_type.value] = result
        
        return {
            'success': True,
            'total_screeners': len(ScreenerType),
            'results': all_results,
            'scan_time': datetime.now().isoformat()
        }
    
    def add_to_watchlist(self, symbol: str, screener_type: ScreenerType, 
                        price: float, target_price: float, stop_loss: float) -> bool:
        """
        Add screened stock to watchlist for monitoring
        
        Args:
            symbol: Stock symbol
            screener_type: Which screener identified it
            price: Current price
            target_price: Target for entry
            stop_loss: Stop loss level
            
        Returns:
            True if added, False otherwise
        """
        try:
            self.watchlist[symbol] = {
                'screener': screener_type.value,
                'entry_price': price,
                'target_price': target_price,
                'stop_loss': stop_loss,
                'added_at': datetime.now(),
                'status': 'watching',
                'alerts': []
            }
            
            logger.info(f"Added {symbol} to watchlist from {screener_type.value} screener")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add {symbol} to watchlist: {e}")
            return False
    
    def get_watchlist(self) -> List[Dict]:
        """Get current watchlist"""
        return list(self.watchlist.values())
    
    def remove_from_watchlist(self, symbol: str) -> bool:
        """Remove stock from watchlist"""
        if symbol in self.watchlist:
            del self.watchlist[symbol]
            logger.info(f"Removed {symbol} from watchlist")
            return True
        return False
    
    def check_watchlist_triggers(self, current_prices: Dict[str, float]) -> Dict:
        """
        Check if any watchlist stocks hit their target or stop loss
        
        Args:
            current_prices: Dict of {symbol: price}
            
        Returns:
            Dictionary of triggered alerts
        """
        triggers = {
            'target_hit': [],
            'stop_loss_hit': [],
            'entry_ready': []
        }
        
        for symbol, watch_data in self.watchlist.items():
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            
            # Check target hit
            if current_price >= watch_data['target_price']:
                triggers['target_hit'].append({
                    'symbol': symbol,
                    'current': current_price,
                    'target': watch_data['target_price']
                })
                watch_data['status'] = 'target_hit'
                watch_data['alerts'].append({'type': 'target_hit', 'at': datetime.now()})
            
            # Check stop loss hit
            elif current_price <= watch_data['stop_loss']:
                triggers['stop_loss_hit'].append({
                    'symbol': symbol,
                    'current': current_price,
                    'stop_loss': watch_data['stop_loss']
                })
                watch_data['status'] = 'stop_loss_hit'
                watch_data['alerts'].append({'type': 'stop_loss_hit', 'at': datetime.now()})
            
            # Check entry ready
            elif current_price >= watch_data['entry_price'] * 0.95:  # 5% tolerance
                triggers['entry_ready'].append({
                    'symbol': symbol,
                    'current': current_price,
                    'target_entry': watch_data['entry_price']
                })
        
        return triggers


class ScreenerIntegration:
    """
    Integration layer between screener and trading system
    """
    
    def __init__(self, screener: StockScreener, order_manager=None, 
                 notifications=None):
        """
        Initialize screener integration
        
        Args:
            screener: StockScreener instance
            order_manager: OrderManager for executing trades
            notifications: Notification service for alerts
        """
        self.screener = screener
        self.order_manager = order_manager
        self.notifications = notifications
    
    def screen_and_alert(self, screener_type: ScreenerType, stocks_df: pd.DataFrame) -> Dict:
        """
        Run screener and send alerts for high-score matches
        """
        result = self.screener.run_screener(screener_type, stocks_df)
        
        if not result['success']:
            return result
        
        # Send alerts for top picks
        if result['top_picks']:
            for stock in result['top_picks']:
                if self.notifications:
                    self.notifications.send_alert(
                        f"Screener Alert: {stock['symbol']}",
                        f"Score: {stock['score']:.0f}% | Recommendation: {stock['recommendation']}",
                        severity='info'
                    )
        
        return result
    
    def screen_and_execute(self, screener_type: ScreenerType, stocks_df: pd.DataFrame,
                          auto_execute: bool = False) -> Dict:
        """
        Run screener and optionally execute trades for high-confidence signals
        
        Args:
            screener_type: Screener to run
            stocks_df: Stock data
            auto_execute: If True, automatically execute orders for high-score stocks
            
        Returns:
            Execution results
        """
        result = self.screener.run_screener(screener_type, stocks_df)
        
        if not result['success']:
            return result
        
        execution_results = []
        
        # Process high-score matches
        for stock in result['matches']:
            if stock['score'] >= 75 and auto_execute and self.order_manager:
                try:
                    # Calculate position sizing based on score
                    quantity = max(1, int(stock['score'] / 100 * 10))  # 0-10 shares
                    
                    # Execute buy order
                    order = self.order_manager.place_order(
                        symbol=stock['symbol'],
                        order_type='BUY',
                        order_subtype='MARKET',
                        quantity=quantity,
                        price=stock['price']
                    )
                    
                    execution_results.append({
                        'symbol': stock['symbol'],
                        'status': 'executed',
                        'order_id': order.get('id'),
                        'quantity': quantity
                    })
                    
                    logger.info(f"Auto-executed BUY for {stock['symbol']}: {quantity} @ {stock['price']}")
                    
                except Exception as e:
                    logger.error(f"Auto-execution failed for {stock['symbol']}: {e}")
                    execution_results.append({
                        'symbol': stock['symbol'],
                        'status': 'failed',
                        'error': str(e)
                    })
        
        return {
            'screener': result,
            'executions': execution_results,
            'auto_execute': auto_execute
        }
