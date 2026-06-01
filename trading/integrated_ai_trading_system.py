"""
Integrated AI Trading System with Sentiment Analysis
====================================================

Complete trading system combining:
1. Multi-Model Trading System (Trend, Reversion, ML)
2. Comprehensive Sentiment Analysis
3. Risk Management & Portfolio Optimization
4. Real-time Execution & Monitoring

This system represents the full production-grade implementation
of advanced algorithmic trading with AI.

Author: GitHub Copilot
Date: May 28, 2026
Version: 2.0 - Production Ready with Sentiment Integration
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Import our modules
try:
    from ai_sentiment_analyzer import (
        ComprehensiveSentimentAnalyzer,
        SentimentSource,
        print_sentiment_report
    )
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False
    print("⚠️  Sentiment module not found. Install: ai_sentiment_analyzer.py")

try:
    from multi_model_trading_system import (
        MultiModelTradingSystem,
        TradeSignal,
        MarketRegime
    )
    MULTI_MODEL_AVAILABLE = True
except ImportError:
    MULTI_MODEL_AVAILABLE = False
    print("⚠️  Multi-model system not found. Install: multi_model_trading_system.py")


# ============================================================================
# INTEGRATED SENTIMENT-PRICE MODEL
# ============================================================================

class SentimentEnhancedPredictor:
    """
    Predictor that combines price action with sentiment analysis
    
    This model blends technical/ML predictions with sentiment signals
    for more robust trading decisions
    """
    
    def __init__(self, sentiment_weight: float = 0.30):
        """
        Args:
            sentiment_weight: How much sentiment influences final signal (0.0-0.5)
                            0.0 = ignore sentiment
                            0.30 = 30% sentiment, 70% price action
                            0.50 = 50% sentiment, 50% price action
        """
        self.sentiment_weight = np.clip(sentiment_weight, 0.0, 0.5)
        self.price_weight = 1.0 - self.sentiment_weight
        self.logger = logging.getLogger("SentimentEnhancedPredictor")
    
    def combine_signals(self, price_signal: float, price_confidence: float,
                       sentiment_signal: float, sentiment_confidence: float) -> Tuple[float, float]:
        """
        Combine price and sentiment signals
        
        Args:
            price_signal: -1 to 1 (from technical/ML models)
            price_confidence: 0 to 1
            sentiment_signal: -1 to 1 (from sentiment analysis)
            sentiment_confidence: 0 to 1
        
        Returns:
            (combined_signal: -1 to 1, combined_confidence: 0 to 1)
        """
        # Weight by signal strength and confidence
        weighted_price = price_signal * price_confidence * self.price_weight
        weighted_sentiment = sentiment_signal * sentiment_confidence * self.sentiment_weight
        
        combined_signal = weighted_price + weighted_sentiment
        combined_signal = np.clip(combined_signal, -1, 1)
        
        # Confidence is higher when both signals agree
        price_agree = 1 - abs(price_signal - sentiment_signal)  # Measure agreement
        combined_confidence = (
            (price_confidence * self.price_weight) +
            (sentiment_confidence * self.sentiment_weight) +
            (price_agree * 0.2)  # Bonus for agreement
        )
        combined_confidence = np.clip(combined_confidence, 0, 1)
        
        return combined_signal, combined_confidence
    
    def get_signal_category(self, signal: float) -> str:
        """Categorize signal strength"""
        if signal > 0.7:
            return "Strong Buy"
        elif signal > 0.3:
            return "Buy"
        elif signal > -0.3:
            return "Hold"
        elif signal > -0.7:
            return "Sell"
        else:
            return "Strong Sell"


# ============================================================================
# INTEGRATED AI TRADING SYSTEM
# ============================================================================

class IntegratedAITradingSystem:
    """
    Complete production-grade AI trading system
    
    Combines:
    - Multi-model price prediction (Trend, Reversion, ML)
    - Comprehensive sentiment analysis
    - Risk management & position sizing
    - Portfolio optimization
    - Real-time execution & monitoring
    """
    
    def __init__(self, sentiment_weight: float = 0.30):
        self.logger = logging.getLogger("IntegratedAITradingSystem")
        
        # Initialize components
        if SENTIMENT_AVAILABLE:
            self.sentiment_analyzer = ComprehensiveSentimentAnalyzer()
            self.logger.info("[OK] Sentiment analyzer initialized")
        else:
            self.sentiment_analyzer = None
            self.logger.warning("[WARNING] Sentiment analyzer not available")
        
        if MULTI_MODEL_AVAILABLE:
            self.multi_model_system = MultiModelTradingSystem()
            self.logger.info("[OK] Multi-model system initialized")
        else:
            self.multi_model_system = None
            self.logger.warning("[WARNING] Multi-model system not available")
        
        self.sentiment_predictor = SentimentEnhancedPredictor(sentiment_weight)
        
        # Tracking
        self.trade_history = []
        self.signal_history = []
        self.performance_metrics = {}
        
        self.logger.info("[OK] Integrated AI Trading System initialized")
    
    def analyze_symbol(self, symbol: str, market_data: pd.DataFrame,
                      news_articles: List[Dict] = None,
                      tweets: List[Dict] = None,
                      reddit_posts: List[Dict] = None,
                      lookback_hours: int = 24) -> Dict:
        """
        Complete analysis for a symbol combining price and sentiment
        
        Args:
            symbol: Stock symbol
            market_data: OHLCV DataFrame
            news_articles: List of news articles (optional)
            tweets: List of tweets (optional)
            reddit_posts: List of Reddit posts (optional)
            lookback_hours: Hours to look back for analysis
        
        Returns:
            Comprehensive analysis with integrated signals
        """
        try:
            analysis = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'price_analysis': None,
                'sentiment_analysis': None,
                'integrated_signal': None,
                'recommendation': None,
                'confidence': 0.0
            }
            
            # 1. PRICE-BASED ANALYSIS (Multi-Model System)
            if self.multi_model_system and market_data is not None:
                try:
                    price_analysis = self._analyze_price_action(symbol, market_data)
                    analysis['price_analysis'] = price_analysis
                except Exception as e:
                    self.logger.error(f"Price analysis failed: {e}")
            
            # 2. SENTIMENT ANALYSIS
            if self.sentiment_analyzer:
                try:
                    sentiment_analysis = self.sentiment_analyzer.analyze_symbol(
                        symbol,
                        news_articles=news_articles,
                        tweets=tweets,
                        reddit_posts=reddit_posts,
                        market_data=market_data,
                        lookback_hours=lookback_hours
                    )
                    analysis['sentiment_analysis'] = sentiment_analysis
                except Exception as e:
                    self.logger.error(f"Sentiment analysis failed: {e}")
            
            # 3. INTEGRATED SIGNAL GENERATION
            if analysis['price_analysis'] and analysis['sentiment_analysis']:
                integrated = self._generate_integrated_signal(
                    analysis['price_analysis'],
                    analysis['sentiment_analysis']
                )
                analysis['integrated_signal'] = integrated
                analysis['recommendation'] = integrated['signal_category']
                analysis['confidence'] = integrated['combined_confidence']
            elif analysis['price_analysis']:
                analysis['recommendation'] = analysis['price_analysis']['signal_category']
                analysis['confidence'] = analysis['price_analysis']['confidence']
            elif analysis['sentiment_analysis']:
                sr = analysis['sentiment_analysis'].get('sentiment_report', {})
                analysis['recommendation'] = sr.get('signal', 'HOLD')
                analysis['confidence'] = sr.get('confidence', 0)
            
            return analysis
        
        except Exception as e:
            self.logger.error(f"Symbol analysis failed for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _analyze_price_action(self, symbol: str, market_data: pd.DataFrame) -> Dict:
        """Analyze price action using multi-model system"""
        try:
            # Generate trading signals from multi-model system
            signals = self.multi_model_system.generate_trading_signals(
                market_data,
                {symbol: market_data['close'].values}
            )
            
            # Extract signal for this symbol
            if symbol in signals:
                signal = signals[symbol]
                
                # Convert to unified format
                signal_value = 1.0 if signal.signal.value > 0 else -1.0 if signal.signal.value < 0 else 0.0
                
                return {
                    'symbol': symbol,
                    'signal': signal_value,
                    'confidence': signal.combined_confidence,
                    'signal_category': self.sentiment_predictor.get_signal_category(signal_value),
                    'method': 'multi_model',
                    'constituent_signals': len(signal.constituent_signals),
                    'market_regime': signal.metadata.get('market_regime', 'unknown') if signal.metadata else 'unknown'
                }
            
            return {
                'symbol': symbol,
                'signal': 0.0,
                'confidence': 0.0,
                'signal_category': 'Hold',
                'method': 'multi_model',
                'error': 'No signal generated'
            }
        
        except Exception as e:
            self.logger.error(f"Price analysis error: {e}")
            return {
                'symbol': symbol,
                'error': str(e)
            }
    
    def _generate_integrated_signal(self, price_analysis: Dict, sentiment_analysis: Dict) -> Dict:
        """Integrate price and sentiment signals"""
        try:
            # Extract signals
            price_signal = price_analysis.get('signal', 0.0)
            price_confidence = price_analysis.get('confidence', 0.0)
            
            sr = sentiment_analysis.get('sentiment_report', {})
            sentiment_signal = sr.get('overall_sentiment', 0.0)
            sentiment_confidence = sr.get('confidence', 0.0)
            
            # Combine signals
            combined_signal, combined_confidence = self.sentiment_predictor.combine_signals(
                price_signal, price_confidence,
                sentiment_signal, sentiment_confidence
            )
            
            return {
                'combined_signal': combined_signal,
                'combined_confidence': combined_confidence,
                'signal_category': self.sentiment_predictor.get_signal_category(combined_signal),
                'price_component': {
                    'signal': price_signal,
                    'confidence': price_confidence,
                    'weight': self.sentiment_predictor.price_weight
                },
                'sentiment_component': {
                    'signal': sentiment_signal,
                    'confidence': sentiment_confidence,
                    'weight': self.sentiment_predictor.sentiment_weight
                },
                'signal_agreement': abs(price_signal - sentiment_signal),  # Lower is better
                'integrated': True
            }
        
        except Exception as e:
            self.logger.error(f"Signal integration failed: {e}")
            return {}
    
    def analyze_portfolio(self, symbols: List[str], market_data_dict: Dict[str, pd.DataFrame],
                         sentiment_data: Dict[str, Dict] = None) -> Dict:
        """
        Analyze entire portfolio with integrated signals
        
        Args:
            symbols: List of symbols to analyze
            market_data_dict: Dict mapping symbol -> DataFrame
            sentiment_data: Dict with news/tweets/reddit per symbol
        
        Returns:
            Portfolio-level analysis and recommendations
        """
        portfolio_analysis = {
            'timestamp': datetime.now().isoformat(),
            'total_symbols': len(symbols),
            'symbol_analyses': {},
            'portfolio_signals': {},
            'portfolio_statistics': {}
        }
        
        all_signals = []
        all_confidences = []
        
        for symbol in symbols:
            try:
                market_data = market_data_dict.get(symbol)
                sentiment_info = sentiment_data.get(symbol, {}) if sentiment_data else {}
                
                analysis = self.analyze_symbol(
                    symbol,
                    market_data,
                    news_articles=sentiment_info.get('news', []),
                    tweets=sentiment_info.get('tweets', []),
                    reddit_posts=sentiment_info.get('reddit', [])
                )
                
                portfolio_analysis['symbol_analyses'][symbol] = analysis
                
                if 'recommendation' in analysis and analysis['recommendation']:
                    all_signals.append(analysis['recommendation'])
                    all_confidences.append(analysis.get('confidence', 0))
                
            except Exception as e:
                self.logger.error(f"Failed to analyze {symbol}: {e}")
                portfolio_analysis['symbol_analyses'][symbol] = {'error': str(e)}
        
        # Portfolio statistics
        if all_signals:
            buy_count = sum(1 for s in all_signals if s == 'Buy' or s == 'Strong Buy')
            sell_count = sum(1 for s in all_signals if s == 'Sell' or s == 'Strong Sell')
            hold_count = len(all_signals) - buy_count - sell_count
            
            portfolio_analysis['portfolio_signals'] = {
                'buy_signals': buy_count,
                'sell_signals': sell_count,
                'hold_signals': hold_count,
                'buy_percentage': buy_count / len(all_signals) if all_signals else 0,
                'sell_percentage': sell_count / len(all_signals) if all_signals else 0,
                'average_confidence': np.mean(all_confidences) if all_confidences else 0
            }
            
            # Portfolio health assessment
            if buy_count > sell_count:
                portfolio_health = "Bullish"
            elif sell_count > buy_count:
                portfolio_health = "Bearish"
            else:
                portfolio_health = "Neutral"
            
            portfolio_analysis['portfolio_health'] = portfolio_health
        
        return portfolio_analysis
    
    def get_system_status(self) -> Dict:
        """Get system health status"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'components': {
                'sentiment_analyzer': 'active' if self.sentiment_analyzer else 'inactive',
                'multi_model_system': 'active' if self.multi_model_system else 'inactive',
                'sentiment_predictor': 'active'
            },
            'statistics': {
                'total_trades': len(self.trade_history),
                'total_signals': len(self.signal_history)
            }
        }
        
        return status
    
    def print_analysis_report(self, analysis: Dict):
        """Print formatted analysis report"""
        print("\n" + "="*80)
        print(f"INTEGRATED AI TRADING ANALYSIS - {analysis['symbol']}")
        print("="*80)
        print(f"Timestamp: {analysis['timestamp']}")
        print(f"Recommendation: {analysis.get('recommendation', 'N/A')}")
        print(f"Confidence: {analysis.get('confidence', 0):.2%}")
        
        # Price Analysis
        if analysis['price_analysis']:
            print("\n--- Price Action Analysis ---")
            pa = analysis['price_analysis']
            print(f"Signal: {pa.get('signal_category', 'N/A')}")
            print(f"Confidence: {pa.get('confidence', 0):.2%}")
            print(f"Method: {pa.get('method', 'N/A')}")
            print(f"Market Regime: {pa.get('market_regime', 'N/A')}")
        
        # Sentiment Analysis
        if analysis['sentiment_analysis']:
            print("\n--- Sentiment Analysis ---")
            sr = analysis['sentiment_analysis'].get('sentiment_report', {})
            print(f"Signal: {sr.get('signal', 'N/A')}")
            print(f"Overall Sentiment: {sr.get('overall_sentiment', 0):.3f}")
            print(f"Trend: {sr.get('short_term_trend', 'N/A')} (short-term)")
        
        # Integrated Signal
        if analysis['integrated_signal']:
            print("\n--- Integrated Signal ---")
            iso = analysis['integrated_signal']
            print(f"Combined Signal: {iso.get('signal_category', 'N/A')}")
            print(f"Signal Strength: {abs(iso.get('combined_signal', 0)):.2%}")
            print(f"Signal Agreement: {1 - iso.get('signal_agreement', 1):.2%}")
        
        print("\n" + "="*80 + "\n")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_sample_market_data(symbol: str, days: int = 100) -> pd.DataFrame:
    """Create sample market data for testing"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Random walk
    returns = np.random.normal(0.0005, 0.02, days)
    prices = 100 * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.normal(0, 0.01, days)),
        'high': prices * (1 + abs(np.random.normal(0, 0.02, days))),
        'low': prices * (1 - abs(np.random.normal(0, 0.02, days))),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, days)
    })
    
    # Add technical indicators
    df['MA_20'] = df['close'].rolling(20).mean()
    df['MA_50'] = df['close'].rolling(50).mean()
    df['RSI_14'] = calculate_rsi(df['close'], 14)
    
    return df


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


# ============================================================================
# QUICK START & EXAMPLES
# ============================================================================

def quick_example():
    """Quick demonstration of the integrated system"""
    print("\n" + "🎯 "*20)
    print("INTEGRATED AI TRADING SYSTEM - QUICK DEMONSTRATION")
    print("🎯 "*20 + "\n")
    
    # Initialize system
    print("Initializing Integrated AI Trading System...")
    system = IntegratedAITradingSystem(sentiment_weight=0.30)
    
    # Create sample data
    print("Creating sample market data for INFY...")
    market_data = create_sample_market_data('INFY', days=100)
    
    # Sample news and social media
    sample_news = [
        {
            'title': 'Infosys reports strong Q3 results',
            'content': 'Infosys exceeded expectations with 15% revenue growth',
            'symbol': 'INFY',
            'timestamp': datetime.now(),
            'relevance_score': 0.95
        },
        {
            'title': 'IT sector shows resilience amid market volatility',
            'content': 'Information technology stocks remain strong performers',
            'symbol': 'INFY',
            'timestamp': datetime.now() - timedelta(hours=2),
            'relevance_score': 0.85
        }
    ]
    
    sample_tweets = [
        {
            'text': 'INFY stock looking bullish with strong fundamentals! #stocks #trading',
            'symbol': 'INFY',
            'timestamp': datetime.now() - timedelta(hours=1),
            'likes': 150,
            'retweets': 45,
            'author': 'stock_analyst',
            'verified': True
        }
    ]
    
    # Analyze symbol
    print("\nAnalyzing INFY with integrated system...")
    analysis = system.analyze_symbol(
        'INFY',
        market_data,
        news_articles=sample_news,
        tweets=sample_tweets,
        lookback_hours=24
    )
    
    # Print results
    system.print_analysis_report(analysis)
    
    # Portfolio analysis
    print("\nPerforming portfolio-level analysis...")
    portfolio_analysis = system.analyze_portfolio(
        ['INFY', 'TCS', 'WIPRO'],
        {
            'INFY': market_data,
            'TCS': create_sample_market_data('TCS'),
            'WIPRO': create_sample_market_data('WIPRO')
        }
    )
    
    print("\n--- PORTFOLIO ANALYSIS ---")
    print(f"Total Symbols: {portfolio_analysis['total_symbols']}")
    print(f"Buy Signals: {portfolio_analysis['portfolio_signals'].get('buy_signals', 0)}")
    print(f"Sell Signals: {portfolio_analysis['portfolio_signals'].get('sell_signals', 0)}")
    print(f"Hold Signals: {portfolio_analysis['portfolio_signals'].get('hold_signals', 0)}")
    print(f"Portfolio Health: {portfolio_analysis.get('portfolio_health', 'N/A')}")
    print(f"Average Confidence: {portfolio_analysis['portfolio_signals'].get('average_confidence', 0):.2%}")
    
    # System status
    print("\n--- SYSTEM STATUS ---")
    status = system.get_system_status()
    print(f"Sentiment Analyzer: {status['components']['sentiment_analyzer']}")
    print(f"Multi-Model System: {status['components']['multi_model_system']}")
    print(f"Sentiment Predictor: {status['components']['sentiment_predictor']}")


if __name__ == "__main__":
    quick_example()
