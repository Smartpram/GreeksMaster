"""
Multi-Model Trading System Architecture
Implements layered pipeline with ensemble models, risk management, and execution
Based on industry best practices for automated trading systems
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & DATA STRUCTURES
# ============================================================================

class MarketRegime(Enum):
    """Market regime classification for gating logic"""
    TRENDING = "trending"
    MEAN_REVERSION = "mean_reversion"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    UNKNOWN = "unknown"


class TradeSignal(Enum):
    """Trading signals from models"""
    BUY = 1
    SELL = -1
    HOLD = 0


@dataclass
class ModelPrediction:
    """Output from a single predictive model"""
    model_name: str
    signal: TradeSignal
    confidence: float  # 0-1
    predicted_return: float  # Expected return %
    timestamp: datetime
    metadata: Dict = None


@dataclass
class CombinedSignal:
    """Output from signal combination layer"""
    signal: TradeSignal
    combined_confidence: float
    constituent_signals: List[ModelPrediction]
    combination_method: str  # "ensemble_average", "voting", "weighted", etc.
    timestamp: datetime


@dataclass
class RiskAdjustedSignal:
    """Output from risk management layer"""
    signal: TradeSignal
    position_size: float  # Position size after risk adjustment
    stop_loss: float  # Stop loss price
    take_profit: float  # Take profit price
    risk_score: float  # 0-100, higher = more risk
    approved: bool  # Whether trade was approved by risk engine
    rejection_reason: Optional[str] = None
    timestamp: datetime = None


# ============================================================================
# LAYER 1: PREDICTIVE MODELS
# ============================================================================

class PredictiveModelBase:
    """Base class for all predictive models"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_trained = False
        self.performance_metrics = {}
    
    def predict(self, data: pd.DataFrame, stock_code: str) -> ModelPrediction:
        """Generate prediction for a stock"""
        raise NotImplementedError
    
    def train(self, data: pd.DataFrame, targets: pd.Series):
        """Train the model"""
        raise NotImplementedError
    
    def get_performance(self) -> Dict:
        """Get model performance metrics"""
        return self.performance_metrics


class TrendFollowingModel(PredictiveModelBase):
    """Classical trend-following model using moving averages"""
    
    def __init__(self):
        super().__init__("TrendFollowing")
        self.ma_short = 20
        self.ma_long = 50
    
    def predict(self, data: pd.DataFrame, stock_code: str) -> ModelPrediction:
        """Generate trend-following signal"""
        try:
            if len(data) < self.ma_long:
                return ModelPrediction(
                    model_name=self.name,
                    signal=TradeSignal.HOLD,
                    confidence=0.0,
                    predicted_return=0.0,
                    timestamp=datetime.now()
                )
            
            close = data['close'].values
            ma_short = np.mean(close[-self.ma_short:])
            ma_long = np.mean(close[-self.ma_long:])
            current_price = close[-1]
            
            # Trend signal
            if ma_short > ma_long:
                confidence = min(1.0, (ma_short - ma_long) / (ma_long * 0.05))
                return ModelPrediction(
                    model_name=self.name,
                    signal=TradeSignal.BUY,
                    confidence=confidence,
                    predicted_return=0.02,  # 2% expected return
                    timestamp=datetime.now()
                )
            elif ma_short < ma_long:
                confidence = min(1.0, (ma_long - ma_short) / (ma_long * 0.05))
                return ModelPrediction(
                    model_name=self.name,
                    signal=TradeSignal.SELL,
                    confidence=confidence,
                    predicted_return=-0.02,
                    timestamp=datetime.now()
                )
            else:
                return ModelPrediction(
                    model_name=self.name,
                    signal=TradeSignal.HOLD,
                    confidence=0.5,
                    predicted_return=0.0,
                    timestamp=datetime.now()
                )
        
        except Exception as e:
            logger.error(f"Error in TrendFollowing prediction: {e}")
            return ModelPrediction(
                model_name=self.name,
                signal=TradeSignal.HOLD,
                confidence=0.0,
                predicted_return=0.0,
                timestamp=datetime.now()
            )


class MeanReversionModel(PredictiveModelBase):
    """Classical mean-reversion model using RSI"""
    
    def __init__(self):
        super().__init__("MeanReversion")
        self.rsi_period = 14
        self.oversold = 30
        self.overbought = 70
    
    def predict(self, data: pd.DataFrame, stock_code: str) -> ModelPrediction:
        """Generate mean-reversion signal"""
        try:
            if len(data) < self.rsi_period:
                return ModelPrediction(
                    model_name=self.name,
                    signal=TradeSignal.HOLD,
                    confidence=0.0,
                    predicted_return=0.0,
                    timestamp=datetime.now()
                )
            
            # Calculate RSI
            close = data['close'].values
            deltas = np.diff(close)
            seed = deltas[:self.rsi_period+1]
            up = seed[seed >= 0].sum() / self.rsi_period
            down = -seed[seed < 0].sum() / self.rsi_period
            rs = up / down if down != 0 else 0
            rsi = 100.0 - 100.0 / (1.0 + rs)
            
            # Mean-reversion signal
            if rsi < self.oversold:
                confidence = (self.oversold - rsi) / self.oversold
                return ModelPrediction(
                    model_name=self.name,
                    signal=TradeSignal.BUY,
                    confidence=confidence,
                    predicted_return=0.015,  # 1.5% expected return
                    timestamp=datetime.now()
                )
            elif rsi > self.overbought:
                confidence = (rsi - self.overbought) / (100 - self.overbought)
                return ModelPrediction(
                    model_name=self.name,
                    signal=TradeSignal.SELL,
                    confidence=confidence,
                    predicted_return=-0.015,
                    timestamp=datetime.now()
                )
            else:
                return ModelPrediction(
                    model_name=self.name,
                    signal=TradeSignal.HOLD,
                    confidence=0.3,
                    predicted_return=0.0,
                    timestamp=datetime.now()
                )
        
        except Exception as e:
            logger.error(f"Error in MeanReversion prediction: {e}")
            return ModelPrediction(
                model_name=self.name,
                signal=TradeSignal.HOLD,
                confidence=0.0,
                predicted_return=0.0,
                timestamp=datetime.now()
            )


class MachineLearningModel(PredictiveModelBase):
    """ML-based predictive model (placeholder for XGBoost, Neural Network, etc.)"""
    
    def __init__(self):
        super().__init__("MachineLearning")
        self.model = None
        self.is_trained = False
    
    def train(self, data: pd.DataFrame, targets: pd.Series):
        """Train ML model"""
        try:
            from sklearn.ensemble import RandomForestClassifier
            
            # Create features
            features = self._create_features(data)
            if len(features) == 0:
                return
            
            # Train model
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(features, targets[:len(features)])
            self.is_trained = True
            logger.info(f"ML Model trained on {len(features)} samples")
        
        except Exception as e:
            logger.error(f"Error training ML model: {e}")
    
    def predict(self, data: pd.DataFrame, stock_code: str) -> ModelPrediction:
        """Generate prediction from ML model"""
        try:
            if not self.is_trained or self.model is None:
                # Return baseline if not trained
                return ModelPrediction(
                    model_name=self.name,
                    signal=TradeSignal.HOLD,
                    confidence=0.5,
                    predicted_return=0.0,
                    timestamp=datetime.now()
                )
            
            features = self._create_features(data)
            if len(features) == 0:
                return ModelPrediction(
                    model_name=self.name,
                    signal=TradeSignal.HOLD,
                    confidence=0.0,
                    predicted_return=0.0,
                    timestamp=datetime.now()
                )
            
            # Predict
            last_features = features[-1:].reshape(1, -1)
            prediction = self.model.predict(last_features)[0]
            confidence = max(self.model.predict_proba(last_features)[0])
            
            signal = TradeSignal.BUY if prediction == 1 else TradeSignal.SELL
            predicted_return = 0.02 if prediction == 1 else -0.02
            
            return ModelPrediction(
                model_name=self.name,
                signal=signal,
                confidence=confidence,
                predicted_return=predicted_return,
                timestamp=datetime.now()
            )
        
        except Exception as e:
            logger.error(f"Error in ML prediction: {e}")
            return ModelPrediction(
                model_name=self.name,
                signal=TradeSignal.HOLD,
                confidence=0.0,
                predicted_return=0.0,
                timestamp=datetime.now()
            )
    
    def _create_features(self, data: pd.DataFrame) -> np.ndarray:
        """Create features for ML model"""
        try:
            close = data['close'].values
            if len(close) < 20:
                return np.array([])
            
            # Simple features: momentum, trend, volatility
            momentum = (close[-1] - close[-10]) / close[-10]
            trend = (close[-1] - close[-20]) / close[-20]
            volatility = np.std(close[-20:]) / np.mean(close[-20:])
            
            features = np.array([momentum, trend, volatility])
            return features.reshape(1, -1)
        
        except Exception as e:
            logger.warning(f"Error creating features: {e}")
            return np.array([])


# ============================================================================
# LAYER 2: SIGNAL COMBINATION
# ============================================================================

class SignalCombiner:
    """Combines multiple model predictions into a single trading signal"""
    
    def __init__(self, combination_method: str = "weighted_ensemble"):
        """
        Initialize signal combiner
        
        Args:
            combination_method: "ensemble_average", "voting", "weighted", "hierarchical"
        """
        self.combination_method = combination_method
        self.model_weights = {}
    
    def set_model_weights(self, weights: Dict[str, float]):
        """Set weights for weighted ensemble"""
        self.model_weights = weights
    
    def combine(self, predictions: List[ModelPrediction]) -> CombinedSignal:
        """Combine multiple model predictions"""
        
        if not predictions:
            return CombinedSignal(
                signal=TradeSignal.HOLD,
                combined_confidence=0.0,
                constituent_signals=[],
                combination_method=self.combination_method,
                timestamp=datetime.now()
            )
        
        if self.combination_method == "ensemble_average":
            return self._ensemble_average(predictions)
        elif self.combination_method == "voting":
            return self._voting(predictions)
        elif self.combination_method == "weighted":
            return self._weighted(predictions)
        else:
            return self._ensemble_average(predictions)
    
    def _ensemble_average(self, predictions: List[ModelPrediction]) -> CombinedSignal:
        """Average confidence across all models"""
        
        # Calculate average confidence for each signal type
        signals = {}
        for pred in predictions:
            if pred.signal not in signals:
                signals[pred.signal] = []
            signals[pred.signal].append(pred.confidence)
        
        # Determine dominant signal
        signal_scores = {s: np.mean(conf) for s, conf in signals.items()}
        dominant_signal = max(signal_scores, key=signal_scores.get)
        combined_confidence = signal_scores[dominant_signal]
        
        return CombinedSignal(
            signal=dominant_signal,
            combined_confidence=combined_confidence,
            constituent_signals=predictions,
            combination_method="ensemble_average",
            timestamp=datetime.now()
        )
    
    def _voting(self, predictions: List[ModelPrediction]) -> CombinedSignal:
        """Majority voting among models"""
        
        buy_votes = sum(1 for p in predictions if p.signal == TradeSignal.BUY)
        sell_votes = sum(1 for p in predictions if p.signal == TradeSignal.SELL)
        hold_votes = sum(1 for p in predictions if p.signal == TradeSignal.HOLD)
        
        total_votes = len(predictions)
        
        if buy_votes > sell_votes and buy_votes > hold_votes:
            signal = TradeSignal.BUY
            confidence = buy_votes / total_votes
        elif sell_votes > buy_votes and sell_votes > hold_votes:
            signal = TradeSignal.SELL
            confidence = sell_votes / total_votes
        else:
            signal = TradeSignal.HOLD
            confidence = hold_votes / total_votes
        
        return CombinedSignal(
            signal=signal,
            combined_confidence=confidence,
            constituent_signals=predictions,
            combination_method="voting",
            timestamp=datetime.now()
        )
    
    def _weighted(self, predictions: List[ModelPrediction]) -> CombinedSignal:
        """Weighted combination based on model weights"""
        
        total_weight = sum(self.model_weights.get(p.model_name, 1.0) for p in predictions)
        
        weighted_signal = 0.0
        weighted_confidence = 0.0
        
        for pred in predictions:
            weight = self.model_weights.get(pred.model_name, 1.0) / total_weight
            signal_value = pred.signal.value  # BUY=1, HOLD=0, SELL=-1
            weighted_signal += signal_value * weight * pred.confidence
            weighted_confidence += pred.confidence * weight
        
        if weighted_signal > 0.3:
            signal = TradeSignal.BUY
        elif weighted_signal < -0.3:
            signal = TradeSignal.SELL
        else:
            signal = TradeSignal.HOLD
        
        return CombinedSignal(
            signal=signal,
            combined_confidence=min(1.0, abs(weighted_signal)),
            constituent_signals=predictions,
            combination_method="weighted",
            timestamp=datetime.now()
        )


class MarketRegimeClassifier:
    """Classifies market regime for gating logic"""
    
    def __init__(self):
        self.volatility_threshold_high = 0.02  # 2% volatility
        self.volatility_threshold_low = 0.01   # 1% volatility
        self.trend_threshold = 0.01  # 1% trend strength
    
    def classify(self, data: pd.DataFrame) -> MarketRegime:
        """Classify current market regime"""
        
        try:
            if len(data) < 50:
                return MarketRegime.UNKNOWN
            
            close = data['close'].values
            
            # Calculate metrics
            volatility = np.std(close[-20:]) / np.mean(close[-20:])
            trend = (close[-1] - close[-20]) / close[-20]
            
            # Classify regime
            if volatility > self.volatility_threshold_high:
                return MarketRegime.HIGH_VOLATILITY
            elif volatility < self.volatility_threshold_low:
                return MarketRegime.LOW_VOLATILITY
            elif abs(trend) > self.trend_threshold:
                return MarketRegime.TRENDING
            else:
                return MarketRegime.MEAN_REVERSION
        
        except Exception as e:
            logger.error(f"Error classifying regime: {e}")
            return MarketRegime.UNKNOWN


# ============================================================================
# LAYER 3: RISK MANAGEMENT
# ============================================================================

class RiskManagementEngine:
    """Risk management layer - validates and adjusts signals"""
    
    def __init__(self, portfolio_value: float = 1000000):
        """
        Initialize risk engine
        
        Args:
            portfolio_value: Total portfolio value in currency units
        """
        self.portfolio_value = portfolio_value
        self.risk_limit_per_trade = 0.02  # 2% max risk per trade
        self.max_position_size = 0.05  # 5% max position size
        self.max_leverage = 2.0  # 2x max leverage
        
        # Risk controls
        self.kill_switch_enabled = False
        self.daily_loss_limit = 0.05  # 5% daily loss limit
        self.max_drawdown_limit = 0.15  # 15% max drawdown
        
        # Tracking
        self.daily_pnl = 0.0
        self.max_drawdown = 0.0
        self.positions = {}
    
    def assess_risk(self, signal: CombinedSignal, current_price: float,
                   stock_code: str) -> RiskAdjustedSignal:
        """Assess risk and adjust signal"""
        
        timestamp = datetime.now() if signal.timestamp is None else signal.timestamp
        
        # Check kill switch
        if self.kill_switch_enabled:
            return RiskAdjustedSignal(
                signal=TradeSignal.HOLD,
                position_size=0.0,
                stop_loss=0.0,
                take_profit=0.0,
                risk_score=100,
                approved=False,
                rejection_reason="Kill switch enabled",
                timestamp=timestamp
            )
        
        # Check daily loss limit
        if self.daily_pnl < -self.portfolio_value * self.daily_loss_limit:
            return RiskAdjustedSignal(
                signal=TradeSignal.HOLD,
                position_size=0.0,
                stop_loss=0.0,
                take_profit=0.0,
                risk_score=100,
                approved=False,
                rejection_reason="Daily loss limit exceeded",
                timestamp=timestamp
            )
        
        # Calculate position size based on confidence and risk
        base_position_size = signal.combined_confidence * self.max_position_size
        risk_score = self._calculate_risk_score(signal, current_price)
        
        # Adjust position size based on risk
        if risk_score > 75:
            position_size = base_position_size * 0.5  # Reduce by 50%
        elif risk_score > 50:
            position_size = base_position_size * 0.75  # Reduce by 25%
        else:
            position_size = base_position_size
        
        # Ensure position size doesn't exceed limits
        position_size = min(position_size, self.max_position_size)
        
        # Calculate stop loss and take profit
        stop_loss_pct = 0.02  # 2% stop loss
        take_profit_pct = 0.04  # 4% take profit
        
        if signal.signal == TradeSignal.BUY:
            stop_loss = current_price * (1 - stop_loss_pct)
            take_profit = current_price * (1 + take_profit_pct)
        elif signal.signal == TradeSignal.SELL:
            stop_loss = current_price * (1 + stop_loss_pct)
            take_profit = current_price * (1 - take_profit_pct)
        else:
            stop_loss = 0.0
            take_profit = 0.0
            position_size = 0.0
        
        # Determine approval
        approved = (signal.combined_confidence >= 0.55 and 
                   risk_score < 80 and 
                   position_size > 0)
        
        return RiskAdjustedSignal(
            signal=signal.signal,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_score=risk_score,
            approved=approved,
            rejection_reason=None if approved else "Risk criteria not met",
            timestamp=timestamp
        )
    
    def _calculate_risk_score(self, signal: CombinedSignal, current_price: float) -> float:
        """Calculate risk score (0-100)"""
        
        base_score = 50  # Start with neutral score
        
        # Reduce score for high confidence (less risky)
        if signal.combined_confidence > 0.7:
            base_score -= 20
        elif signal.combined_confidence > 0.6:
            base_score -= 10
        
        # Increase score for low confidence (more risky)
        if signal.combined_confidence < 0.5:
            base_score += 20
        
        # Cap risk score
        risk_score = max(0, min(100, base_score))
        
        return risk_score
    
    def enable_kill_switch(self):
        """Enable kill switch - stop all trading"""
        self.kill_switch_enabled = True
        logger.warning("KILL SWITCH ENABLED - All trading halted")
    
    def disable_kill_switch(self):
        """Disable kill switch"""
        self.kill_switch_enabled = False
        logger.info("Kill switch disabled")
    
    def update_pnl(self, pnl: float):
        """Update daily P&L"""
        self.daily_pnl += pnl
        self.max_drawdown = min(self.max_drawdown, self.daily_pnl)


# ============================================================================
# LAYER 4: PORTFOLIO OPTIMIZATION
# ============================================================================

class PortfolioOptimizer:
    """Portfolio optimization layer - determines position sizes"""
    
    def __init__(self, portfolio_value: float = 1000000):
        self.portfolio_value = portfolio_value
        self.optimization_method = "risk_parity"  # or "volatility_scaling", "equal_weight"
    
    def optimize_positions(self, signals: Dict[str, RiskAdjustedSignal],
                          volatilities: Dict[str, float]) -> Dict[str, float]:
        """
        Optimize position sizes across multiple signals
        
        Args:
            signals: Risk-adjusted signals for each stock
            volatilities: Volatility for each stock
            
        Returns:
            Optimized position sizes
        """
        
        positions = {}
        
        if self.optimization_method == "risk_parity":
            positions = self._risk_parity(signals, volatilities)
        elif self.optimization_method == "volatility_scaling":
            positions = self._volatility_scaling(signals, volatilities)
        else:
            positions = self._equal_weight(signals)
        
        return positions
    
    def _risk_parity(self, signals: Dict[str, RiskAdjustedSignal],
                     volatilities: Dict[str, float]) -> Dict[str, float]:
        """Risk parity: allocate inversely to volatility"""
        
        positions = {}
        total_inverse_vol = 0.0
        
        # Calculate total inverse volatility
        for stock, signal in signals.items():
            if signal.approved and signal.signal != TradeSignal.HOLD:
                vol = volatilities.get(stock, 0.02)
                inverse_vol = 1.0 / vol if vol > 0 else 1.0
                total_inverse_vol += inverse_vol
        
        # Allocate positions
        for stock, signal in signals.items():
            if signal.approved and signal.signal != TradeSignal.HOLD:
                vol = volatilities.get(stock, 0.02)
                inverse_vol = 1.0 / vol if vol > 0 else 1.0
                positions[stock] = (inverse_vol / total_inverse_vol) * signal.position_size
            else:
                positions[stock] = 0.0
        
        return positions
    
    def _volatility_scaling(self, signals: Dict[str, RiskAdjustedSignal],
                           volatilities: Dict[str, float]) -> Dict[str, float]:
        """Volatility scaling: larger positions in less volatile stocks"""
        
        positions = {}
        target_volatility = 0.015  # 1.5% target
        
        for stock, signal in signals.items():
            if signal.approved and signal.signal != TradeSignal.HOLD:
                vol = volatilities.get(stock, 0.02)
                scaling_factor = target_volatility / vol if vol > 0 else 1.0
                positions[stock] = signal.position_size * scaling_factor
            else:
                positions[stock] = 0.0
        
        return positions
    
    def _equal_weight(self, signals: Dict[str, RiskAdjustedSignal]) -> Dict[str, float]:
        """Equal weight allocation"""
        
        positions = {}
        approved_count = sum(1 for s in signals.values() 
                            if s.approved and s.signal != TradeSignal.HOLD)
        
        for stock, signal in signals.items():
            if signal.approved and signal.signal != TradeSignal.HOLD:
                positions[stock] = signal.position_size / max(1, approved_count)
            else:
                positions[stock] = 0.0
        
        return positions


# ============================================================================
# LAYER 5: EXECUTION ENGINE
# ============================================================================

class ExecutionEngine:
    """Execution engine - places and manages orders"""
    
    def __init__(self, order_manager=None):
        self.order_manager = order_manager
        self.orders = {}
        self.order_counter = 0
        self.execution_log = []
    
    def execute_signal(self, signal: RiskAdjustedSignal, stock_code: str,
                      current_price: float) -> Optional[Dict]:
        """Execute a trading signal"""
        
        if not signal.approved or signal.position_size == 0:
            return None
        
        try:
            self.order_counter += 1
            order_id = f"ORD_{self.order_counter}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            order = {
                'order_id': order_id,
                'stock_code': stock_code,
                'side': 'BUY' if signal.signal == TradeSignal.BUY else 'SELL',
                'quantity': int(signal.position_size * 1000),  # Assume position size * 1000 shares
                'price': current_price,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'timestamp': datetime.now(),
                'status': 'PENDING'
            }
            
            # Place order (if order manager available)
            if self.order_manager:
                # Call actual order manager
                pass
            
            # Track order
            self.orders[order_id] = order
            self.execution_log.append({
                'timestamp': datetime.now(),
                'event': 'order_placed',
                'order_id': order_id,
                'stock': stock_code,
                'side': order['side'],
                'price': current_price
            })
            
            logger.info(f"Order placed: {order_id} - {stock_code} {order['side']} "
                       f"at {current_price:.2f}")
            
            return order
        
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            return None
    
    def get_execution_summary(self) -> Dict:
        """Get execution summary"""
        return {
            'total_orders': len(self.orders),
            'pending_orders': sum(1 for o in self.orders.values() if o['status'] == 'PENDING'),
            'filled_orders': sum(1 for o in self.orders.values() if o['status'] == 'FILLED'),
            'cancelled_orders': sum(1 for o in self.orders.values() if o['status'] == 'CANCELLED'),
            'execution_log_entries': len(self.execution_log)
        }


# ============================================================================
# LAYER 6: MULTI-MODEL ORCHESTRATOR (Main Pipeline)
# ============================================================================

class MultiModelTradingSystem:
    """
    Main orchestrator for the multi-model trading system
    Coordinates all layers from data ingestion to execution
    """
    
    def __init__(self, portfolio_value: float = 1000000, order_manager=None):
        """Initialize the complete trading system"""
        
        self.portfolio_value = portfolio_value
        self.order_manager = order_manager
        
        # Layer 1: Predictive models
        self.trend_model = TrendFollowingModel()
        self.reversion_model = MeanReversionModel()
        self.ml_model = MachineLearningModel()
        self.models = [self.trend_model, self.reversion_model, self.ml_model]
        
        # Layer 2: Signal combination
        self.signal_combiner = SignalCombiner(combination_method="weighted_ensemble")
        self.signal_combiner.set_model_weights({
            "TrendFollowing": 0.4,
            "MeanReversion": 0.3,
            "MachineLearning": 0.3
        })
        self.regime_classifier = MarketRegimeClassifier()
        
        # Layer 3: Risk management
        self.risk_engine = RiskManagementEngine(portfolio_value)
        
        # Layer 4: Portfolio optimization
        self.portfolio_optimizer = PortfolioOptimizer(portfolio_value)
        
        # Layer 5: Execution
        self.execution_engine = ExecutionEngine(order_manager)
        
        # Tracking
        self.trading_history = []
        self.signal_history = []
    
    def generate_trading_signals(self, market_data: Dict[str, pd.DataFrame],
                               current_prices: Dict[str, float]) -> Dict[str, RiskAdjustedSignal]:
        """
        Generate trading signals through complete pipeline
        
        Args:
            market_data: OHLCV data for each stock
            current_prices: Current prices for each stock
            
        Returns:
            Risk-adjusted trading signals for each stock
        """
        
        final_signals = {}
        
        for stock_code, data in market_data.items():
            try:
                current_price = current_prices.get(stock_code)
                if current_price is None:
                    continue
                
                # Step 1: Get market regime
                regime = self.regime_classifier.classify(data)
                
                # Step 2: Generate predictions from all models
                predictions = []
                for model in self.models:
                    pred = model.predict(data, stock_code)
                    if pred.signal != TradeSignal.HOLD:  # Only include non-hold signals
                        predictions.append(pred)
                
                if not predictions:
                    continue
                
                # Step 3: Combine signals
                combined_signal = self.signal_combiner.combine(predictions)
                
                # Step 4: Risk management
                risk_adjusted_signal = self.risk_engine.assess_risk(
                    combined_signal, current_price, stock_code
                )
                
                # Step 5: Track signal
                final_signals[stock_code] = risk_adjusted_signal
                self.signal_history.append({
                    'timestamp': datetime.now(),
                    'stock': stock_code,
                    'regime': regime.value,
                    'predictions': [asdict(p) for p in predictions],
                    'combined_signal': asdict(combined_signal),
                    'risk_adjusted_signal': asdict(risk_adjusted_signal)
                })
                
                logger.info(f"{stock_code}: {combined_signal.signal.name} "
                           f"(Confidence: {combined_signal.combined_confidence:.2%}, "
                           f"Risk Score: {risk_adjusted_signal.risk_score:.0f}, "
                           f"Approved: {risk_adjusted_signal.approved})")
            
            except Exception as e:
                logger.error(f"Error generating signal for {stock_code}: {e}")
                continue
        
        return final_signals
    
    def optimize_and_execute(self, signals: Dict[str, RiskAdjustedSignal],
                           current_prices: Dict[str, float],
                           volatilities: Dict[str, float]) -> Dict[str, Dict]:
        """
        Optimize positions and execute trades
        
        Args:
            signals: Risk-adjusted signals
            current_prices: Current prices
            volatilities: Stock volatilities
            
        Returns:
            Executed orders
        """
        
        executed_orders = {}
        
        # Step 4: Portfolio optimization (if multiple signals)
        if len(signals) > 1:
            optimized_positions = self.portfolio_optimizer.optimize_positions(
                signals, volatilities
            )
        else:
            optimized_positions = {
                stock: signal.position_size
                for stock, signal in signals.items()
            }
        
        # Step 5: Execute trades
        for stock_code, signal in signals.items():
            if signal.approved and signal.signal != TradeSignal.HOLD:
                # Adjust signal with optimized position size
                optimized_signal = RiskAdjustedSignal(
                    signal=signal.signal,
                    position_size=optimized_positions.get(stock_code, signal.position_size),
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                    risk_score=signal.risk_score,
                    approved=signal.approved,
                    timestamp=datetime.now()
                )
                
                # Execute
                order = self.execution_engine.execute_signal(
                    optimized_signal, stock_code, current_prices[stock_code]
                )
                
                if order:
                    executed_orders[stock_code] = order
                    self.trading_history.append({
                        'timestamp': datetime.now(),
                        'order': order
                    })
        
        return executed_orders
    
    def get_system_status(self) -> Dict:
        """Get complete system status"""
        return {
            'timestamp': datetime.now().isoformat(),
            'portfolio_value': self.portfolio_value,
            'risk_engine': {
                'kill_switch': self.risk_engine.kill_switch_enabled,
                'daily_pnl': self.risk_engine.daily_pnl,
                'max_drawdown': self.risk_engine.max_drawdown
            },
            'execution': self.execution_engine.get_execution_summary(),
            'total_signals_generated': len(self.signal_history),
            'total_trades_executed': len(self.trading_history)
        }
    
    def get_performance_report(self) -> Dict:
        """Get detailed performance report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'system_status': self.get_system_status(),
            'models': {
                'trend_following': self.trend_model.get_performance(),
                'mean_reversion': self.reversion_model.get_performance(),
                'machine_learning': self.ml_model.get_performance()
            },
            'signal_history_count': len(self.signal_history),
            'trading_history_count': len(self.trading_history)
        }
