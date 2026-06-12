#!/usr/bin/env python3
"""
GreeksMaster MCP Server - Model Context Protocol Implementation
Exposes trading strategies, risk management, and order execution as MCP tools
"""

import json
import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

# MCP imports (install via: pip install mcp)
from mcp.server import Server
from mcp.types import (
    Tool, TextContent, Resource, ResourceTemplate,
    Prompt, PromptArgument, PromptMessage
)

# Local imports
import sys
sys.path.insert(0, '/app')

from services.breeze_api import BreezeAPI
from services.risk_manager import RiskManager
from services.signal_executor import SignalExecutor
from market_sentiment_gate import MarketSentimentGate
from strategies.buy_hold_trend import GoldenCrossStrategy
from range_policy import RangePolicy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS & CONSTANTS
# ============================================================================

TOP_SYMBOLS = [
    "INFTEC", "NIFTY", "TCS", "RELIANCE", "WIPRO",
    "MARUTI", "BAJAJFINSV", "HINDUNILVR", "ITC", "LT",
    "HDFCBANK", "ICICIBANK", "INFY", "TATA", "ADANIPOWER"
]

TIMEFRAMES = ["5min", "15min", "hourly", "daily"]
STRATEGIES = ["golden_cross", "mean_reversion", "momentum", "breakout", "all"]
ORDER_TYPES = ["BUY", "SELL"]

# ============================================================================
# MCP SERVER INITIALIZATION
# ============================================================================

server = Server("greeksmaster-mcp")

# Global service instances
breeze_api: Optional[BreezeAPI] = None
risk_manager: Optional[RiskManager] = None
signal_executor: Optional[SignalExecutor] = None
sentiment_gate: Optional[MarketSentimentGate] = None
range_policy: Optional[RangePolicy] = None

# ============================================================================
# TOOL 1: SCREEN_MARKET
# ============================================================================

SCREEN_MARKET_TOOL = Tool(
    name="screen_market",
    description="Scan market for trading signals across multiple symbols using technical strategies",
    inputSchema={
        "type": "object",
        "properties": {
            "symbols": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of symbols to scan (e.g., ['INFTEC', 'NIFTY', 'TCS'])"
            },
            "strategy": {
                "type": "string",
                "enum": STRATEGIES,
                "description": "Which strategy/strategies to use"
            },
            "timeframe": {
                "type": "string",
                "enum": TIMEFRAMES,
                "description": "Candle timeframe for analysis"
            },
            "min_confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Minimum confidence score to report (default: 0.6)"
            }
        },
        "required": ["symbols"]
    }
)


async def screen_market(
    symbols: List[str],
    strategy: str = "all",
    timeframe: str = "5min",
    min_confidence: float = 0.6,
    **kwargs
) -> Dict[str, Any]:
    """
    Scan market for trading signals
    
    Returns:
        Dict with signals array and summary statistics
    """
    try:
        logger.info(f"Screening {len(symbols)} symbols with {strategy} strategy")
        
        signals = []
        summary = {
            "total_scanned": len(symbols),
            "total_signals": 0,
            "buy_signals": 0,
            "sell_signals": 0,
            "high_confidence": 0,
        }
        
        for symbol in symbols:
            try:
                # Fetch market data
                data = await breeze_api.get_market_data(symbol, timeframe)
                
                # Run strategy analysis
                if strategy in ["golden_cross", "all"]:
                    gc_signals = await _analyze_golden_cross(symbol, data)
                    signals.extend(gc_signals)
                
                if strategy in ["mean_reversion", "all"]:
                    mr_signals = await _analyze_mean_reversion(symbol, data)
                    signals.extend(mr_signals)
                
                if strategy in ["momentum", "all"]:
                    mom_signals = await _analyze_momentum(symbol, data)
                    signals.extend(mom_signals)
                
                if strategy in ["breakout", "all"]:
                    bo_signals = await _analyze_breakout(symbol, data)
                    signals.extend(bo_signals)
                
            except Exception as e:
                logger.warning(f"Error screening {symbol}: {str(e)}")
                continue
        
        # Filter by confidence and update summary
        filtered_signals = [s for s in signals if s.get("confidence", 0) >= min_confidence]
        
        summary["total_signals"] = len(filtered_signals)
        summary["buy_signals"] = sum(1 for s in filtered_signals if s["signal_type"] == "BUY")
        summary["sell_signals"] = sum(1 for s in filtered_signals if s["signal_type"] == "SELL")
        summary["high_confidence"] = sum(1 for s in filtered_signals if s.get("confidence", 0) >= 0.8)
        
        return {
            "success": True,
            "signals": filtered_signals,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in screen_market: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def _analyze_golden_cross(symbol: str, data: Any) -> List[Dict]:
    """Analyze Golden Cross strategy"""
    try:
        strategy = GoldenCrossStrategy()
        signals = strategy.analyze(symbol, data)
        return signals or []
    except Exception as e:
        logger.warning(f"Golden Cross analysis failed for {symbol}: {str(e)}")
        return []


async def _analyze_mean_reversion(symbol: str, data: Any) -> List[Dict]:
    """Analyze Mean Reversion strategy (BB + RSI)"""
    # TODO: Integrate with mean_reversion.py
    return []


async def _analyze_momentum(symbol: str, data: Any) -> List[Dict]:
    """Analyze Momentum strategy (MACD + RSI)"""
    # TODO: Integrate with momentum.py
    return []


async def _analyze_breakout(symbol: str, data: Any) -> List[Dict]:
    """Analyze Breakout strategy (Support/Resistance + Volume)"""
    # TODO: Integrate with breakout.py
    return []

# ============================================================================
# TOOL 2: VALIDATE_SIGNAL
# ============================================================================

VALIDATE_SIGNAL_TOOL = Tool(
    name="validate_signal",
    description="Validate a trading signal against market conditions, sentiment, and risk rules",
    inputSchema={
        "type": "object",
        "properties": {
            "symbol": {"type": "string"},
            "signal_type": {
                "type": "string",
                "enum": ORDER_TYPES,
                "description": "BUY or SELL"
            },
            "entry_price": {
                "type": "number",
                "description": "Entry price for the signal"
            },
            "strategy": {
                "type": "string",
                "enum": STRATEGIES,
                "description": "Which strategy generated this signal"
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Signal confidence (0-1)"
            },
            "check_sentiment": {
                "type": "boolean",
                "description": "Run market sentiment check (default: true)"
            },
            "check_regime": {
                "type": "boolean",
                "description": "Check market regime trending/ranging (default: true)"
            }
        },
        "required": ["symbol", "signal_type", "entry_price"]
    }
)


async def validate_signal(
    symbol: str,
    signal_type: str,
    entry_price: float,
    strategy: str = "manual",
    confidence: float = 0.5,
    check_sentiment: bool = True,
    check_regime: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Validate trading signal through all gatekeepers
    
    Returns:
        Dict with approval status, reason, and recommendations
    """
    try:
        logger.info(f"Validating {signal_type} signal for {symbol} at {entry_price}")
        
        approved = True
        checks = {}
        reasons = []
        
        # Check 1: Range Policy (market regime)
        if check_regime:
            regime_check = await _check_range_policy(symbol)
            checks["range_policy"] = regime_check["passed"]
            if not regime_check["passed"]:
                approved = False
                reasons.append(f"Range detected: {regime_check['reason']}")
        
        # Check 2: Market Sentiment
        if check_sentiment:
            sentiment_check = await _check_sentiment(symbol, signal_type)
            checks["sentiment"] = sentiment_check["passed"]
            if not sentiment_check["passed"]:
                approved = False
                reasons.append(f"Sentiment blocked: {sentiment_check['reason']}")
        
        # Check 3: Risk Limits
        risk_check = await _check_risk_limits(symbol, signal_type, entry_price)
        checks["risk_limits"] = risk_check["passed"]
        if not risk_check["passed"]:
            approved = False
            reasons.append(f"Risk limit exceeded: {risk_check['reason']}")
        
        # Check 4: Daily Loss Limit
        daily_check = await _check_daily_loss_limit()
        checks["daily_loss_limit"] = daily_check["passed"]
        if not daily_check["passed"]:
            approved = False
            reasons.append(f"Daily loss limit: {daily_check['reason']}")
        
        return {
            "success": True,
            "approved": approved,
            "symbol": symbol,
            "signal_type": signal_type,
            "entry_price": entry_price,
            "strategy": strategy,
            "confidence": confidence,
            "gatekeeper_checks": checks,
            "reasons": reasons if not approved else ["All checks passed"],
            "recommended_size_multiplier": 1.0 if approved else 0.0,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error validating signal: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "approved": False,
            "timestamp": datetime.now().isoformat()
        }


async def _check_range_policy(symbol: str) -> Dict[str, Any]:
    """Check if market is in range (no trading)"""
    try:
        is_range = range_policy.is_range(symbol)
        return {
            "passed": not is_range,
            "reason": f"Market in {'RANGE' if is_range else 'TREND'} regime"
        }
    except Exception as e:
        return {"passed": True, "reason": f"Range check error (pass): {str(e)}"}


async def _check_sentiment(symbol: str, signal_type: str) -> Dict[str, Any]:
    """Check market sentiment (NIFTY-based)"""
    try:
        sentiment = sentiment_gate.evaluate_sentiment(symbol)
        
        if signal_type == "BUY" and sentiment["bullish"]:
            return {"passed": True, "reason": "Bullish sentiment confirmed"}
        elif signal_type == "SELL" and sentiment["bearish"]:
            return {"passed": True, "reason": "Bearish sentiment confirmed"}
        else:
            return {"passed": False, "reason": f"Sentiment: {sentiment.get('description', 'neutral')}"}
    
    except Exception as e:
        return {"passed": True, "reason": f"Sentiment check error (pass): {str(e)}"}


async def _check_risk_limits(symbol: str, signal_type: str, entry_price: float) -> Dict[str, Any]:
    """Check portfolio risk limits"""
    try:
        limits = risk_manager.check_position_limits(symbol, signal_type)
        return {
            "passed": limits["allowed"],
            "reason": limits.get("reason", "OK")
        }
    except Exception as e:
        return {"passed": True, "reason": f"Risk limit check error (pass): {str(e)}"}


async def _check_daily_loss_limit() -> Dict[str, Any]:
    """Check daily loss limit"""
    try:
        daily_pnl = risk_manager.get_daily_pnl()
        daily_limit = risk_manager.get_daily_loss_limit()
        
        passed = daily_pnl > (-daily_limit)
        return {
            "passed": passed,
            "reason": f"Daily P&L: ₹{daily_pnl:.2f} / Limit: ₹{-daily_limit:.2f}"
        }
    except Exception as e:
        return {"passed": True, "reason": f"Daily limit check error (pass): {str(e)}"}

# ============================================================================
# TOOL 3: CALCULATE_POSITION_SIZE
# ============================================================================

CALCULATE_POSITION_SIZE_TOOL = Tool(
    name="calculate_position_size",
    description="Calculate safe position size given entry price, stop loss, and risk parameters",
    inputSchema={
        "type": "object",
        "properties": {
            "symbol": {"type": "string"},
            "entry_price": {
                "type": "number",
                "description": "Entry price"
            },
            "stop_loss_price": {
                "type": "number",
                "description": "Stop loss price"
            },
            "risk_amount": {
                "type": "number",
                "description": "Maximum rupees to risk on this trade"
            },
            "max_position_pct": {
                "type": "number",
                "description": "Max % of portfolio to use (default: 2%)"
            }
        },
        "required": ["symbol", "entry_price", "stop_loss_price", "risk_amount"]
    }
)


async def calculate_position_size(
    symbol: str,
    entry_price: float,
    stop_loss_price: float,
    risk_amount: float,
    max_position_pct: float = 2.0,
    **kwargs
) -> Dict[str, Any]:
    """
    Calculate position size for safe risk management
    
    Returns:
        Dict with quantity, position value, and risk metrics
    """
    try:
        logger.info(f"Calculating position size for {symbol}")
        
        # Get current portfolio
        portfolio = await _get_portfolio()
        account_value = portfolio["total_equity"]
        
        # Calculate quantity based on risk
        risk_per_share = abs(entry_price - stop_loss_price)
        if risk_per_share == 0:
            return {
                "success": False,
                "error": "Stop loss price equals entry price (zero risk)"
            }
        
        quantity_by_risk = int(risk_amount / risk_per_share)
        
        # Calculate max quantity based on position size limit
        max_risk_amount = (account_value * max_position_pct) / 100
        quantity_by_limit = int(max_risk_amount / risk_per_share)
        
        # Use lower of the two
        quantity = min(quantity_by_risk, quantity_by_limit)
        
        if quantity <= 0:
            return {
                "success": False,
                "error": f"Calculated quantity {quantity} <= 0. Risk per share too high."
            }
        
        position_value = quantity * entry_price
        actual_risk = quantity * risk_per_share
        reward_per_share = 2 * risk_per_share  # Assume 2:1 RR
        reward_amount = quantity * reward_per_share
        risk_reward_ratio = reward_amount / actual_risk if actual_risk > 0 else 0
        
        # Check margin requirement (approximate)
        margin_required = position_value * 0.2  # 20% margin for equities
        margin_available = portfolio.get("margin_available", 0)
        
        return {
            "success": True,
            "symbol": symbol,
            "quantity": quantity,
            "position_value": position_value,
            "entry_price": entry_price,
            "stop_loss_price": stop_loss_price,
            "risk_per_trade": actual_risk,
            "potential_reward": reward_amount,
            "risk_reward_ratio": round(risk_reward_ratio, 2),
            "portfolio_impact": {
                "pct_of_equity": round((position_value / account_value) * 100, 2),
                "margin_required": margin_required,
                "margin_available": margin_available,
                "margin_sufficient": margin_required <= margin_available
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error calculating position size: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# ============================================================================
# TOOL 4: PLACE_ORDER
# ============================================================================

PLACE_ORDER_TOOL = Tool(
    name="place_order",
    description="Place a BUY or SELL order with automatic risk management (stop loss & profit target)",
    inputSchema={
        "type": "object",
        "properties": {
            "symbol": {"type": "string"},
            "order_type": {
                "type": "string",
                "enum": ORDER_TYPES,
                "description": "BUY or SELL"
            },
            "quantity": {
                "type": "integer",
                "minimum": 1,
                "description": "Number of shares"
            },
            "stop_loss_price": {
                "type": "number",
                "description": "Stop loss price"
            },
            "profit_target_price": {
                "type": "number",
                "description": "Profit target price"
            },
            "strategy": {
                "type": "string",
                "description": "Which strategy generated this signal",
                "enum": STRATEGIES + ["manual"]
            },
            "dry_run": {
                "type": "boolean",
                "description": "Validate without placing order (default: false)"
            }
        },
        "required": ["symbol", "order_type", "quantity", "stop_loss_price", "profit_target_price"]
    }
)


async def place_order(
    symbol: str,
    order_type: str,
    quantity: int,
    stop_loss_price: float,
    profit_target_price: float,
    strategy: str = "manual",
    dry_run: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Place a trading order with full validation and risk management
    
    Returns:
        Dict with order confirmation or error details
    """
    try:
        logger.info(f"{'[DRY RUN] ' if dry_run else ''}Placing {order_type} order for {quantity} {symbol}")
        
        # Get current price
        market_data = await breeze_api.get_market_data(symbol, "5min")
        current_price = market_data[-1]["close"] if market_data else None
        
        if not current_price:
            return {
                "success": False,
                "error": f"Could not fetch current price for {symbol}"
            }
        
        # Validate order parameters
        validation = _validate_order_params(
            order_type, current_price, stop_loss_price, profit_target_price
        )
        if not validation["valid"]:
            return {
                "success": False,
                "error": validation["error"]
            }
        
        # Calculate risk/reward
        risk_per_share = abs(current_price - stop_loss_price)
        reward_per_share = abs(profit_target_price - current_price)
        rr_ratio = reward_per_share / risk_per_share if risk_per_share > 0 else 0
        
        order_details = {
            "symbol": symbol,
            "order_type": order_type,
            "quantity": quantity,
            "entry_price": current_price,
            "stop_loss_price": stop_loss_price,
            "profit_target_price": profit_target_price,
            "risk_per_trade": quantity * risk_per_share,
            "potential_reward": quantity * reward_per_share,
            "risk_reward_ratio": rr_ratio,
            "strategy": strategy,
            "timestamp": datetime.now().isoformat()
        }
        
        if dry_run:
            order_details["dry_run"] = True
            order_details["order_id"] = f"DRY_{symbol}_{datetime.now().timestamp()}"
            return {
                "success": True,
                "message": "Validation passed (dry run mode)",
                "order_details": order_details
            }
        
        # Execute order via signal executor
        result = await signal_executor.execute_trade(
            symbol=symbol,
            order_type=order_type,
            quantity=quantity,
            stop_loss_price=stop_loss_price,
            profit_target_price=profit_target_price,
            strategy=strategy
        )
        
        if result.get("success"):
            order_details["order_id"] = result.get("order_id")
            order_details["status"] = "PENDING"
            return {
                "success": True,
                "order_details": order_details,
                "breeze_response": result
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Order execution failed"),
                "order_details": order_details
            }
    
    except Exception as e:
        logger.error(f"Error placing order: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def _validate_order_params(order_type: str, current: float, sl: float, pt: float) -> Dict:
    """Validate order parameters"""
    if order_type == "BUY":
        if sl >= current:
            return {"valid": False, "error": "BUY: Stop loss must be below entry"}
        if pt <= current:
            return {"valid": False, "error": "BUY: Profit target must be above entry"}
    elif order_type == "SELL":
        if sl <= current:
            return {"valid": False, "error": "SELL: Stop loss must be above entry"}
        if pt >= current:
            return {"valid": False, "error": "SELL: Profit target must be below entry"}
    
    return {"valid": True}

# ============================================================================
# TOOL 5: CLOSE_POSITION
# ============================================================================

CLOSE_POSITION_TOOL = Tool(
    name="close_position",
    description="Close an open position (stop loss, profit target, or manual)",
    inputSchema={
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "Order ID to close"
            },
            "exit_reason": {
                "type": "string",
                "enum": ["stop_loss", "profit_target", "sma20_breakdown", "manual", "risk_limit"],
                "description": "Reason for closing (default: manual)"
            }
        },
        "required": ["order_id"]
    }
)


async def close_position(
    order_id: str,
    exit_reason: str = "manual",
    **kwargs
) -> Dict[str, Any]:
    """
    Close an open position with exit tracking
    
    Returns:
        Dict with position closure details and P&L
    """
    try:
        logger.info(f"Closing position {order_id} - Reason: {exit_reason}")
        
        # Get position details
        position = await signal_executor.get_position(order_id)
        if not position:
            return {
                "success": False,
                "error": f"Position {order_id} not found"
            }
        
        # Get current price
        market_data = await breeze_api.get_market_data(position["symbol"], "5min")
        current_price = market_data[-1]["close"] if market_data else None
        
        if not current_price:
            return {
                "success": False,
                "error": f"Could not fetch current price"
            }
        
        # Calculate P&L
        pnl = (current_price - position["entry_price"]) * position["quantity"]
        pnl_pct = ((current_price - position["entry_price"]) / position["entry_price"]) * 100
        
        # Execute exit
        result = await signal_executor.exit_trade(
            order_id=order_id,
            exit_price=current_price,
            exit_reason=exit_reason
        )
        
        return {
            "success": result.get("success", True),
            "position_closed": {
                "order_id": order_id,
                "symbol": position["symbol"],
                "quantity": position["quantity"],
                "entry_price": position["entry_price"],
                "entry_time": position.get("entry_time"),
                "exit_price": current_price,
                "exit_reason": exit_reason,
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "duration": position.get("duration", "N/A")
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error closing position: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# ============================================================================
# TOOL 6: GET_PORTFOLIO
# ============================================================================

GET_PORTFOLIO_TOOL = Tool(
    name="get_portfolio",
    description="Get current portfolio state: holdings, open positions, and P&L",
    inputSchema={
        "type": "object",
        "properties": {
            "include_history": {
                "type": "boolean",
                "description": "Include closed positions from today (default: false)"
            }
        }
    }
)


async def get_portfolio(include_history: bool = False, **kwargs) -> Dict[str, Any]:
    """Get current portfolio snapshot"""
    try:
        return await _get_portfolio(include_history=include_history)
    except Exception as e:
        logger.error(f"Error getting portfolio: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def _get_portfolio(include_history: bool = False) -> Dict[str, Any]:
    """Internal portfolio fetcher"""
    portfolio = risk_manager.get_portfolio()
    
    result = {
        "success": True,
        "account_summary": {
            "total_equity": portfolio.get("total_equity", 0),
            "cash": portfolio.get("cash", 0),
            "margin_used": portfolio.get("margin_used", 0),
            "margin_available": portfolio.get("margin_available", 0),
            "daily_pnl": portfolio.get("daily_pnl", 0),
            "daily_pnl_pct": portfolio.get("daily_pnl_pct", 0),
            "drawdown": portfolio.get("drawdown", 0),
            "drawdown_pct": portfolio.get("drawdown_pct", 0)
        },
        "open_positions": portfolio.get("open_positions", []),
        "position_count": len(portfolio.get("open_positions", []))
    }
    
    if include_history:
        result["closed_today"] = portfolio.get("closed_today", [])
        result["trades_today"] = len(portfolio.get("closed_today", []))
    
    result["timestamp"] = datetime.now().isoformat()
    return result

# ============================================================================
# TOOL 7: GET_MARKET_DATA
# ============================================================================

GET_MARKET_DATA_TOOL = Tool(
    name="get_market_data",
    description="Fetch OHLCV data and technical indicators for a symbol",
    inputSchema={
        "type": "object",
        "properties": {
            "symbol": {"type": "string"},
            "timeframe": {
                "type": "string",
                "enum": TIMEFRAMES,
                "description": "Candle timeframe (default: 5min)"
            },
            "periods": {
                "type": "integer",
                "description": "Number of candles (default: 100, max: 500)",
                "minimum": 10,
                "maximum": 500
            },
            "include_indicators": {
                "type": "array",
                "description": "Which indicators to include",
                "items": {
                    "type": "string",
                    "enum": ["MA", "RSI", "MACD", "BB", "ATR", "ADX"]
                }
            }
        },
        "required": ["symbol"]
    }
)


async def get_market_data(
    symbol: str,
    timeframe: str = "5min",
    periods: int = 100,
    include_indicators: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Fetch market data with technical indicators"""
    try:
        logger.info(f"Fetching market data: {symbol} {timeframe} ({periods} candles)")
        
        # Fetch OHLCV
        data = await breeze_api.get_market_data(symbol, timeframe, periods)
        
        if not data:
            return {
                "success": False,
                "error": f"No data available for {symbol}"
            }
        
        # Calculate indicators if requested
        if include_indicators:
            data = _calculate_indicators(data, include_indicators)
        
        # Format response
        formatted_data = [
            {
                "timestamp": candle.get("timestamp"),
                "open": candle.get("open"),
                "high": candle.get("high"),
                "low": candle.get("low"),
                "close": candle.get("close"),
                "volume": candle.get("volume"),
                "indicators": candle.get("indicators", {}) if include_indicators else {}
            }
            for candle in data
        ]
        
        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "periods": len(formatted_data),
            "data": formatted_data,
            "latest": formatted_data[-1] if formatted_data else None,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def _calculate_indicators(data: List[Dict], indicators: List[str]) -> List[Dict]:
    """Calculate technical indicators for candle data"""
    # TODO: Integrate with talib or pandas_ta
    return data

# ============================================================================
# TOOL 8: ANALYZE_RISK
# ============================================================================

ANALYZE_RISK_TOOL = Tool(
    name="analyze_risk",
    description="Comprehensive risk analysis: portfolio exposure, drawdown, daily limits",
    inputSchema={
        "type": "object",
        "properties": {
            "include_pending": {
                "type": "boolean",
                "description": "Include pending orders in analysis (default: false)"
            },
            "horizon": {
                "type": "string",
                "enum": ["current", "daily", "weekly"],
                "description": "Risk analysis timeframe (default: current)"
            }
        }
    }
)


async def analyze_risk(
    include_pending: bool = False,
    horizon: str = "current",
    **kwargs
) -> Dict[str, Any]:
    """Comprehensive risk analysis"""
    try:
        logger.info(f"Analyzing risk - Horizon: {horizon}")
        
        portfolio = risk_manager.get_portfolio()
        
        risk_analysis = {
            "success": True,
            "portfolio_value": portfolio.get("total_equity", 0),
            "total_exposure": sum(
                pos["position_value"] for pos in portfolio.get("open_positions", [])
            ),
            "exposure_pct": 0,
            "cash_available": portfolio.get("cash", 0),
            "margin": {
                "used": portfolio.get("margin_used", 0),
                "available": portfolio.get("margin_available", 0),
                "utilization_pct": 0
            },
            "pnl": {
                "daily": portfolio.get("daily_pnl", 0),
                "daily_pct": portfolio.get("daily_pnl_pct", 0),
                "unrealized": sum(
                    pos.get("unrealized_pnl", 0) for pos in portfolio.get("open_positions", [])
                )
            },
            "drawdown": {
                "amount": portfolio.get("drawdown", 0),
                "pct": portfolio.get("drawdown_pct", 0),
                "max_allowed_pct": 2.0
            },
            "open_positions": len(portfolio.get("open_positions", [])),
            "max_positions": 5,
            "position_concentration": [],
            "risk_warnings": []
        }
        
        # Calculate percentages
        total_eq = risk_analysis["portfolio_value"]
        if total_eq > 0:
            risk_analysis["exposure_pct"] = round(
                (risk_analysis["total_exposure"] / total_eq) * 100, 2
            )
            risk_analysis["margin"]["utilization_pct"] = round(
                (risk_analysis["margin"]["used"] / total_eq) * 100, 2
            )
        
        # Position concentration
        for pos in portfolio.get("open_positions", []):
            pct = (pos.get("position_value", 0) / total_eq) * 100 if total_eq > 0 else 0
            risk_analysis["position_concentration"].append({
                "symbol": pos.get("symbol"),
                "pct": round(pct, 2)
            })
        
        # Generate warnings
        warnings = []
        if risk_analysis["exposure_pct"] > 50:
            warnings.append(f"⚠️ High exposure: {risk_analysis['exposure_pct']}% (>50%)")
        if risk_analysis["margin"]["utilization_pct"] > 70:
            warnings.append(f"⚠️ High margin usage: {risk_analysis['margin']['utilization_pct']}%")
        if risk_analysis["drawdown"]["pct"] > risk_analysis["drawdown"]["max_allowed_pct"]:
            warnings.append(f"⚠️ Drawdown limit exceeded: {risk_analysis['drawdown']['pct']}%")
        if risk_analysis["open_positions"] >= risk_analysis["max_positions"]:
            warnings.append(f"⚠️ Max positions reached: {risk_analysis['open_positions']}")
        
        risk_analysis["risk_warnings"] = warnings
        risk_analysis["risk_level"] = (
            "CRITICAL" if len(warnings) >= 3
            else "HIGH" if len(warnings) >= 2
            else "MEDIUM" if len(warnings) >= 1
            else "LOW"
        )
        
        risk_analysis["timestamp"] = datetime.now().isoformat()
        return risk_analysis
    
    except Exception as e:
        logger.error(f"Error analyzing risk: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# ============================================================================
# MCP SERVER ENDPOINTS
# ============================================================================

@server.list_tools()
async def list_tools():
    """List all available tools"""
    return [
        SCREEN_MARKET_TOOL,
        VALIDATE_SIGNAL_TOOL,
        CALCULATE_POSITION_SIZE_TOOL,
        PLACE_ORDER_TOOL,
        CLOSE_POSITION_TOOL,
        GET_PORTFOLIO_TOOL,
        GET_MARKET_DATA_TOOL,
        ANALYZE_RISK_TOOL,
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute tool by name"""
    tools_map = {
        "screen_market": screen_market,
        "validate_signal": validate_signal,
        "calculate_position_size": calculate_position_size,
        "place_order": place_order,
        "close_position": close_position,
        "get_portfolio": get_portfolio,
        "get_market_data": get_market_data,
        "analyze_risk": analyze_risk,
    }
    
    tool_fn = tools_map.get(name)
    if not tool_fn:
        raise ValueError(f"Tool '{name}' not found")
    
    logger.info(f"Calling tool: {name}")
    result = await tool_fn(**arguments)
    
    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2, default=str)
    )]


@server.list_resources()
async def list_resources():
    """List available resources"""
    resources = []
    
    # Market data resources
    for symbol in TOP_SYMBOLS:
        resources.append(
            ResourceTemplate(
                uriTemplate=f"market_data://symbol/{symbol}",
                name=f"{symbol} Market Data",
                description=f"Current market data and indicators for {symbol}",
                mimeType="application/json"
            )
        )
    
    # Portfolio resources
    resources.extend([
        Resource(
            uri="portfolio://current",
            name="Current Portfolio",
            description="Current holdings and P&L",
            mimeType="application/json"
        ),
        Resource(
            uri="portfolio://risk",
            name="Portfolio Risk Analysis",
            description="Detailed risk metrics and warnings",
            mimeType="application/json"
        ),
    ])
    
    # Strategy resources
    for strategy in STRATEGIES[:-1]:  # Exclude 'all'
        resources.append(
            Resource(
                uri=f"strategy://{strategy}",
                name=f"{strategy.title()} Strategy",
                description=f"Configuration and performance metrics",
                mimeType="application/json"
            )
        )
    
    return resources


@server.read_resource()
async def read_resource(uri: str):
    """Read resource by URI"""
    try:
        if uri.startswith("market_data://symbol/"):
            symbol = uri.replace("market_data://symbol/", "")
            result = await get_market_data(
                symbol=symbol,
                timeframe="5min",
                periods=20,
                include_indicators=["MA", "RSI", "BB"]
            )
            return TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )
        
        elif uri == "portfolio://current":
            result = await get_portfolio(include_history=False)
            return TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )
        
        elif uri == "portfolio://risk":
            result = await analyze_risk(horizon="current")
            return TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )
        
        else:
            return TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown resource: {uri}"}, indent=2)
            )
    
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {str(e)}")
        return TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )


@server.list_prompts()
async def list_prompts():
    """List available prompt templates"""
    return [
        Prompt(
            name="daily_trading_brief",
            description="Get comprehensive trading analysis for the day",
            arguments=[
                PromptArgument(
                    name="include_recommendations",
                    description="Include buy/sell recommendations",
                    required=False
                ),
                PromptArgument(
                    name="risk_level",
                    description="Risk tolerance: conservative, balanced, aggressive",
                    required=False
                ),
            ]
        ),
        Prompt(
            name="analyze_opportunity",
            description="Deep dive into a trading opportunity",
            arguments=[
                PromptArgument(
                    name="symbol",
                    description="Stock symbol to analyze",
                    required=True
                ),
                PromptArgument(
                    name="signal_type",
                    description="BUY or SELL signal",
                    required=True
                ),
            ]
        ),
        Prompt(
            name="risk_review",
            description="Comprehensive risk assessment and adjustments",
            arguments=[]
        ),
    ]


@server.get_prompt()
async def get_prompt(name: str, arguments: dict):
    """Get prompt template with arguments"""
    if name == "daily_trading_brief":
        return {
            "messages": [
                {
                    "role": "user",
                    "content": """Analyze the market for trading opportunities today:

1. Screen the market using screen_market tool
2. Review portfolio risk using analyze_risk
3. Check market sentiment and regime
4. Suggest top opportunities with:
   - Entry price and signal confidence
   - Calculated position size
   - Risk/reward ratio
5. Provide trading recommendations"""
                }
            ]
        }
    
    elif name == "analyze_opportunity":
        symbol = arguments.get("symbol", "INFTEC")
        signal_type = arguments.get("signal_type", "BUY")
        return {
            "messages": [
                {
                    "role": "user",
                    "content": f"""Analyze {signal_type} opportunity for {symbol}:

1. Get market data using get_market_data
2. Validate the signal using validate_signal
3. Calculate position size
4. Assess risk/reward
5. Recommend entry/exit prices"""
                }
            ]
        }
    
    elif name == "risk_review":
        return {
            "messages": [
                {
                    "role": "user",
                    "content": """Review portfolio risk:

1. Get portfolio status using get_portfolio
2. Analyze risk using analyze_risk
3. Identify any positions to close
4. Check if any daily limits are breached
5. Provide risk management recommendations"""
                }
            ]
        }
    
    return {"messages": []}

# ============================================================================
# SERVER INITIALIZATION
# ============================================================================

async def init_services():
    """Initialize service instances"""
    global breeze_api, risk_manager, signal_executor, sentiment_gate, range_policy
    
    logger.info("Initializing MCP services...")
    
    try:
        breeze_api = BreezeAPI()
        risk_manager = RiskManager()
        signal_executor = SignalExecutor()
        sentiment_gate = MarketSentimentGate()
        range_policy = RangePolicy()
        
        logger.info("✅ All services initialized successfully")
    except Exception as e:
        logger.error(f"❌ Error initializing services: {str(e)}")
        raise


async def main():
    """Run MCP server"""
    await init_services()
    
    logger.info("🚀 Starting GreeksMaster MCP Server...")
    logger.info(f"📝 Available tools: {len(await list_tools())}")
    logger.info("Listening for MCP protocol messages on stdio...")
    
    from mcp.server.stdio import stdio_server
    from mcp.types import InitializationOptions
    
    async with stdio_server(server) as (read_stream, write_stream):
        await server.run(read_stream, write_stream, InitializationOptions())


if __name__ == "__main__":
    asyncio.run(main())
