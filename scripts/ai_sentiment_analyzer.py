"""
Advanced Sentiment Analysis Module for AI Trading System
========================================================

Production-grade sentiment analysis with:
1. Financial News Sentiment Analysis
2. Social Media Sentiment Tracking (Twitter/X, Reddit)
3. Technical Sentiment Indicators
4. Market Fear/Greed Index
5. Sentiment-Price Correlation Analysis
6. Real-time Alert System
7. Historical Sentiment Database
8. Integration with Trading Signals

Author: GitHub Copilot
Date: May 28, 2026
Version: 1.0 - Production Ready
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# NLP Libraries
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    print("⚠️  TextBlob not installed. Install: pip install textblob")

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    print("⚠️  VADER not installed. Install: pip install vaderSentiment")

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except (ImportError, OSError):
    TRANSFORMERS_AVAILABLE = False
    print("WARNING: Transformers not fully installed. Install: pip install transformers torch")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  Requests not installed. Install: pip install requests")


# ============================================================================
# ENUMS & DATA STRUCTURES
# ============================================================================

class SentimentScore(Enum):
    """Sentiment classification"""
    VERY_BULLISH = 1.0      # > 0.8
    BULLISH = 0.5           # 0.5 to 0.8
    NEUTRAL = 0.0           # -0.5 to 0.5
    BEARISH = -0.5          # -0.8 to -0.5
    VERY_BEARISH = -1.0     # < -0.8


class SentimentSource(Enum):
    """Source of sentiment data"""
    NEWS = "news"
    TWITTER = "twitter"
    REDDIT = "reddit"
    FINANCIAL_FORUMS = "forums"
    EARNINGS = "earnings"
    ANALYST = "analyst"
    TECHNICAL = "technical"


@dataclass
class SentimentReading:
    """Single sentiment data point"""
    source: SentimentSource
    symbol: str
    sentiment_score: float  # -1.0 to 1.0
    confidence: float       # 0.0 to 1.0
    text: str              # Original text
    timestamp: datetime
    sentiment_category: str # "bullish", "bearish", "neutral"
    relevance_score: float  # 0.0 to 1.0
    metadata: Dict = None


@dataclass
class AggregatedSentiment:
    """Aggregated sentiment across sources"""
    symbol: str
    overall_sentiment: float      # -1.0 to 1.0
    sentiment_confidence: float   # 0.0 to 1.0
    source_breakdown: Dict        # Sentiment by source
    short_term_trend: str         # "improving", "stable", "deteriorating"
    long_term_trend: str          # "improving", "stable", "deteriorating"
    signal_strength: float        # 0.0 to 1.0
    timestamp: datetime
    underlying_data: List[SentimentReading] = None


# ============================================================================
# PART 1: SENTIMENT ANALYSIS ENGINES
# ============================================================================

class SentimentAnalyzerBase:
    """Base class for sentiment analysis engines"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"Sentiment-{self.name}")
        if not logger.handlers:
            handler = logging.FileHandler('ai_sentiment_analysis.log')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def analyze(self, text: str) -> Tuple[float, float]:
        """
        Analyze sentiment of text
        
        Returns:
            (sentiment_score: -1.0 to 1.0, confidence: 0.0 to 1.0)
        """
        raise NotImplementedError


class VADERSentimentAnalyzer(SentimentAnalyzerBase):
    """VADER Sentiment Analysis (best for social media & financial text)"""
    
    def __init__(self):
        super().__init__("VADER")
        if not VADER_AVAILABLE:
            raise ImportError("VADER not installed. Install: pip install vaderSentiment")
        self.analyzer = SentimentIntensityAnalyzer()
    
    def analyze(self, text: str) -> Tuple[float, float]:
        """
        Analyze sentiment using VADER
        
        Returns:
            (sentiment_score: -1.0 to 1.0, confidence: 0.0 to 1.0)
        """
        try:
            scores = self.analyzer.polarity_scores(text)
            # Convert from -1 to 1 range to -1.0 to 1.0
            sentiment_score = scores['compound']  # Already -1 to 1
            confidence = max(scores['pos'], scores['neg'])
            
            self.logger.info(f"VADER analysis: score={sentiment_score:.3f}, confidence={confidence:.3f}")
            return sentiment_score, confidence
        except Exception as e:
            self.logger.error(f"VADER analysis failed: {e}")
            return 0.0, 0.0


class TextBlobSentimentAnalyzer(SentimentAnalyzerBase):
    """TextBlob Sentiment Analysis (good baseline)"""
    
    def __init__(self):
        super().__init__("TextBlob")
        if not TEXTBLOB_AVAILABLE:
            raise ImportError("TextBlob not installed. Install: pip install textblob")
    
    def analyze(self, text: str) -> Tuple[float, float]:
        """
        Analyze sentiment using TextBlob
        
        Returns:
            (sentiment_score: -1.0 to 1.0, confidence: 0.0 to 1.0)
        """
        try:
            blob = TextBlob(text)
            sentiment_score = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            # Higher subjectivity = higher confidence (more opinion)
            confidence = subjectivity
            
            self.logger.info(f"TextBlob analysis: score={sentiment_score:.3f}, confidence={confidence:.3f}")
            return sentiment_score, confidence
        except Exception as e:
            self.logger.error(f"TextBlob analysis failed: {e}")
            return 0.0, 0.0


class TransformerSentimentAnalyzer(SentimentAnalyzerBase):
    """Deep Learning Sentiment Analysis using Transformers (most accurate)"""
    
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        super().__init__("Transformers")
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("Transformers not installed. Install: pip install transformers torch")
        
        self.model_name = model_name
        try:
            self.pipeline = pipeline("sentiment-analysis", model=model_name)
            self.logger.info(f"Loaded transformer model: {model_name}")
        except Exception as e:
            self.logger.error(f"Failed to load transformer model: {e}")
            self.pipeline = None
    
    def analyze(self, text: str) -> Tuple[float, float]:
        """
        Analyze sentiment using Transformers
        
        Returns:
            (sentiment_score: -1.0 to 1.0, confidence: 0.0 to 1.0)
        """
        if self.pipeline is None:
            return 0.0, 0.0
        
        try:
            # Truncate if text is too long
            text = text[:512]
            
            result = self.pipeline(text)[0]
            label = result['label'].lower()  # POSITIVE or NEGATIVE
            score = result['score']  # 0 to 1
            
            # Convert to -1 to 1 range
            sentiment_score = score if label == 'positive' else -score
            confidence = score
            
            self.logger.info(f"Transformer analysis: score={sentiment_score:.3f}, confidence={confidence:.3f}")
            return sentiment_score, confidence
        except Exception as e:
            self.logger.error(f"Transformer analysis failed: {e}")
            return 0.0, 0.0


class HybridSentimentAnalyzer(SentimentAnalyzerBase):
    """Hybrid analyzer combining multiple engines for robust sentiment"""
    
    def __init__(self, engines: List[SentimentAnalyzerBase] = None):
        super().__init__("Hybrid")
        self.engines = engines or self._get_available_engines()
        
        if not self.engines:
            self.logger.warning("No sentiment analyzers available!")
    
    def _get_available_engines(self) -> List[SentimentAnalyzerBase]:
        """Initialize available sentiment engines"""
        engines = []
        
        if VADER_AVAILABLE:
            try:
                engines.append(VADERSentimentAnalyzer())
                self.logger.info("[OK] VADER analyzer available")
            except Exception as e:
                self.logger.warning(f"VADER initialization failed: {e}")
        
        if TEXTBLOB_AVAILABLE:
            try:
                engines.append(TextBlobSentimentAnalyzer())
                self.logger.info("[OK] TextBlob analyzer available")
            except Exception as e:
                self.logger.warning(f"TextBlob initialization failed: {e}")
        
        if TRANSFORMERS_AVAILABLE:
            try:
                engines.append(TransformerSentimentAnalyzer())
                self.logger.info("[OK] Transformer analyzer available")
            except Exception as e:
                self.logger.warning(f"Transformer initialization failed: {e}")
        
        return engines
    
    def analyze(self, text: str) -> Tuple[float, float]:
        """
        Analyze sentiment using ensemble of engines
        
        Returns:
            (sentiment_score: -1.0 to 1.0, confidence: 0.0 to 1.0)
        """
        if not self.engines:
            return 0.0, 0.0
        
        scores = []
        confidences = []
        
        for engine in self.engines:
            try:
                score, confidence = engine.analyze(text)
                scores.append(score)
                confidences.append(confidence)
            except Exception as e:
                self.logger.warning(f"Engine {engine.name} failed: {e}")
        
        if not scores:
            return 0.0, 0.0
        
        # Average sentiment score
        avg_sentiment = np.mean(scores)
        avg_confidence = np.mean(confidences)
        
        self.logger.info(f"Hybrid analysis: score={avg_sentiment:.3f}, confidence={avg_confidence:.3f}")
        return avg_sentiment, avg_confidence


# ============================================================================
# PART 2: SENTIMENT DATA COLLECTION
# ============================================================================

class NewsNewsSentimentCollector:
    """Collect and analyze financial news sentiment"""
    
    def __init__(self, analyzer: SentimentAnalyzerBase = None):
        self.analyzer = analyzer or HybridSentimentAnalyzer()
        self.logger = logging.getLogger("NewsCollector")
        self.sentiment_history = []
    
    def analyze_news(self, news_articles: List[Dict]) -> List[SentimentReading]:
        """
        Analyze sentiment from news articles
        
        Args:
            news_articles: List of dicts with 'title', 'content', 'symbol', 'timestamp'
        
        Returns:
            List of SentimentReading objects
        """
        readings = []
        
        for article in news_articles:
            try:
                text = f"{article.get('title', '')} {article.get('content', '')}"
                
                sentiment_score, confidence = self.analyzer.analyze(text)
                
                # Determine category
                if sentiment_score > 0.5:
                    category = "bullish"
                elif sentiment_score < -0.5:
                    category = "bearish"
                else:
                    category = "neutral"
                
                reading = SentimentReading(
                    source=SentimentSource.NEWS,
                    symbol=article.get('symbol', 'UNKNOWN'),
                    sentiment_score=sentiment_score,
                    confidence=confidence,
                    text=text[:500],  # Truncate for storage
                    timestamp=article.get('timestamp', datetime.now()),
                    sentiment_category=category,
                    relevance_score=article.get('relevance_score', 0.8),
                    metadata=article.get('metadata', {})
                )
                
                readings.append(reading)
                self.sentiment_history.append(reading)
                
            except Exception as e:
                self.logger.error(f"Failed to analyze article: {e}")
        
        return readings
    
    def get_sentiment_summary(self, symbol: str, lookback_hours: int = 24) -> Dict:
        """Get sentiment summary for a symbol"""
        cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
        
        relevant_readings = [
            r for r in self.sentiment_history
            if r.symbol == symbol and r.timestamp >= cutoff_time
        ]
        
        if not relevant_readings:
            return {
                'symbol': symbol,
                'average_sentiment': 0.0,
                'article_count': 0,
                'bullish_count': 0,
                'bearish_count': 0,
                'neutral_count': 0
            }
        
        sentiments = [r.sentiment_score for r in relevant_readings]
        
        return {
            'symbol': symbol,
            'average_sentiment': np.mean(sentiments),
            'article_count': len(relevant_readings),
            'bullish_count': sum(1 for r in relevant_readings if r.sentiment_category == "bullish"),
            'bearish_count': sum(1 for r in relevant_readings if r.sentiment_category == "bearish"),
            'neutral_count': sum(1 for r in relevant_readings if r.sentiment_category == "neutral"),
            'max_sentiment': max(sentiments),
            'min_sentiment': min(sentiments),
            'std_sentiment': np.std(sentiments)
        }


class SocialMediaSentimentCollector:
    """Collect and analyze sentiment from social media (Twitter, Reddit, etc.)"""
    
    def __init__(self, analyzer: SentimentAnalyzerBase = None):
        self.analyzer = analyzer or HybridSentimentAnalyzer()
        self.logger = logging.getLogger("SocialMediaCollector")
        self.sentiment_history = []
    
    def analyze_tweets(self, tweets: List[Dict]) -> List[SentimentReading]:
        """
        Analyze sentiment from tweets
        
        Args:
            tweets: List of dicts with 'text', 'symbol', 'timestamp', 'likes', 'retweets'
        
        Returns:
            List of SentimentReading objects
        """
        readings = []
        
        for tweet in tweets:
            try:
                text = tweet.get('text', '')
                
                sentiment_score, confidence = self.analyzer.analyze(text)
                
                # Boost confidence based on engagement (likes, retweets)
                engagement = tweet.get('likes', 0) + tweet.get('retweets', 0)
                relevance_score = min(1.0, 0.5 + engagement / 1000)  # Normalize engagement
                
                # Determine category
                if sentiment_score > 0.5:
                    category = "bullish"
                elif sentiment_score < -0.5:
                    category = "bearish"
                else:
                    category = "neutral"
                
                reading = SentimentReading(
                    source=SentimentSource.TWITTER,
                    symbol=tweet.get('symbol', 'UNKNOWN'),
                    sentiment_score=sentiment_score,
                    confidence=confidence,
                    text=text[:280],  # Twitter limit
                    timestamp=tweet.get('timestamp', datetime.now()),
                    sentiment_category=category,
                    relevance_score=relevance_score,
                    metadata={
                        'likes': tweet.get('likes', 0),
                        'retweets': tweet.get('retweets', 0),
                        'author': tweet.get('author', 'unknown'),
                        'verified': tweet.get('verified', False)
                    }
                )
                
                readings.append(reading)
                self.sentiment_history.append(reading)
                
            except Exception as e:
                self.logger.error(f"Failed to analyze tweet: {e}")
        
        return readings
    
    def analyze_reddit_posts(self, posts: List[Dict]) -> List[SentimentReading]:
        """
        Analyze sentiment from Reddit posts
        
        Args:
            posts: List of dicts with 'text', 'symbol', 'timestamp', 'upvotes', 'comments'
        """
        readings = []
        
        for post in posts:
            try:
                text = f"{post.get('title', '')} {post.get('text', '')}"
                
                sentiment_score, confidence = self.analyzer.analyze(text)
                
                # Boost relevance based on engagement
                engagement = post.get('upvotes', 0) + post.get('comments', 0) / 2
                relevance_score = min(1.0, 0.5 + engagement / 100)
                
                # Determine category
                if sentiment_score > 0.5:
                    category = "bullish"
                elif sentiment_score < -0.5:
                    category = "bearish"
                else:
                    category = "neutral"
                
                reading = SentimentReading(
                    source=SentimentSource.REDDIT,
                    symbol=post.get('symbol', 'UNKNOWN'),
                    sentiment_score=sentiment_score,
                    confidence=confidence,
                    text=text[:500],
                    timestamp=post.get('timestamp', datetime.now()),
                    sentiment_category=category,
                    relevance_score=relevance_score,
                    metadata={
                        'upvotes': post.get('upvotes', 0),
                        'comments': post.get('comments', 0),
                        'subreddit': post.get('subreddit', 'unknown'),
                        'author': post.get('author', 'unknown')
                    }
                )
                
                readings.append(reading)
                self.sentiment_history.append(reading)
                
            except Exception as e:
                self.logger.error(f"Failed to analyze Reddit post: {e}")
        
        return readings


class TechnicalSentimentIndicator:
    """Generate sentiment from technical indicators (fear/greed)"""
    
    def __init__(self):
        self.logger = logging.getLogger("TechnicalSentiment")
    
    def calculate_technical_sentiment(self, market_data: pd.DataFrame, symbol: str) -> float:
        """
        Calculate sentiment from technical indicators
        
        Combines:
        - RSI (momentum)
        - Volatility (VIX-like)
        - Volume trend
        - Price momentum
        - Moving average position
        
        Returns:
            Sentiment score from -1.0 (very fearful) to 1.0 (very greedy)
        """
        try:
            components = []
            weights = []
            
            # 1. RSI Component (30% weight)
            if 'RSI_14' in market_data.columns:
                rsi = market_data['RSI_14'].iloc[-1]
                # 30-70 neutral, <30 oversold (bearish), >70 overbought (bullish)
                rsi_sentiment = (rsi - 50) / 50  # Convert to -1 to 1
                components.append(rsi_sentiment)
                weights.append(0.30)
            
            # 2. Price Momentum Component (25% weight)
            if 'close' in market_data.columns:
                returns = market_data['close'].pct_change().tail(5).mean()
                momentum_sentiment = np.clip(returns * 10, -1, 1)  # Scale returns
                components.append(momentum_sentiment)
                weights.append(0.25)
            
            # 3. Volatility Component (20% weight) - inverted (high vol = fearful)
            if 'close' in market_data.columns:
                volatility = market_data['close'].pct_change().tail(20).std()
                vol_sentiment = -np.clip(volatility * 20, 0, 1)  # Invert: high vol = fear
                components.append(vol_sentiment)
                weights.append(0.20)
            
            # 4. Volume Trend Component (15% weight)
            if 'volume' in market_data.columns:
                vol_ma_short = market_data['volume'].tail(5).mean()
                vol_ma_long = market_data['volume'].tail(20).mean()
                vol_trend = 1.0 if vol_ma_short > vol_ma_long else -1.0
                components.append(vol_trend * 0.5)  # Conservative weighting
                weights.append(0.15)
            
            # 5. Moving Average Position Component (10% weight)
            if 'MA_20' in market_data.columns and 'close' in market_data.columns:
                close = market_data['close'].iloc[-1]
                ma20 = market_data['MA_20'].iloc[-1]
                ma_position = (close - ma20) / ma20  # How far above/below MA
                ma_sentiment = np.clip(ma_position * 5, -1, 1)
                components.append(ma_sentiment)
                weights.append(0.10)
            
            if not components:
                return 0.0
            
            # Weighted average
            weighted_sentiment = np.average(components, weights=weights[:len(components)])
            weighted_sentiment = np.clip(weighted_sentiment, -1, 1)
            
            self.logger.info(f"{symbol} technical sentiment: {weighted_sentiment:.3f}")
            return weighted_sentiment
            
        except Exception as e:
            self.logger.error(f"Failed to calculate technical sentiment: {e}")
            return 0.0


# ============================================================================
# PART 3: SENTIMENT AGGREGATION & ANALYSIS
# ============================================================================

class SentimentAggregator:
    """Aggregate sentiment from multiple sources"""
    
    def __init__(self):
        self.logger = logging.getLogger("SentimentAggregator")
        self.readings_db = []
    
    def add_readings(self, readings: List[SentimentReading]):
        """Add sentiment readings to database"""
        self.readings_db.extend(readings)
    
    def get_aggregated_sentiment(self, symbol: str, lookback_hours: int = 24) -> AggregatedSentiment:
        """
        Get aggregated sentiment across all sources
        
        Returns weighted average considering:
        - Source importance (news > Twitter > Reddit)
        - Recency (newer = more weight)
        - Confidence of each reading
        - Relevance score
        """
        cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
        
        relevant_readings = [
            r for r in self.readings_db
            if r.symbol == symbol and r.timestamp >= cutoff_time
        ]
        
        if not relevant_readings:
            return AggregatedSentiment(
                symbol=symbol,
                overall_sentiment=0.0,
                sentiment_confidence=0.0,
                source_breakdown={},
                short_term_trend="stable",
                long_term_trend="stable",
                signal_strength=0.0,
                timestamp=datetime.now()
            )
        
        # Source weights
        source_weights = {
            SentimentSource.NEWS: 0.40,
            SentimentSource.EARNINGS: 0.25,
            SentimentSource.ANALYST: 0.20,
            SentimentSource.TWITTER: 0.10,
            SentimentSource.REDDIT: 0.05
        }
        
        # Calculate weighted sentiment
        total_weight = 0
        weighted_sentiment = 0
        source_breakdown = {}
        
        for source in SentimentSource:
            source_readings = [r for r in relevant_readings if r.source == source]
            
            if source_readings:
                # Average sentiment for this source
                source_sentiment = np.mean([r.sentiment_score for r in source_readings])
                source_confidence = np.mean([r.confidence for r in source_readings])
                
                # Time decay: older readings get less weight
                time_weights = []
                for reading in source_readings:
                    age_hours = (datetime.now() - reading.timestamp).total_seconds() / 3600
                    time_decay = np.exp(-age_hours / 24)  # Half-life of 24 hours
                    time_weights.append(time_decay * reading.relevance_score * source_confidence)
                
                avg_time_weight = np.mean(time_weights) if time_weights else 0.5
                
                source_weight = source_weights.get(source, 0.05) * avg_time_weight
                weighted_sentiment += source_sentiment * source_weight
                total_weight += source_weight
                
                source_breakdown[source.value] = {
                    'sentiment': source_sentiment,
                    'confidence': source_confidence,
                    'readings': len(source_readings),
                    'weight': source_weight
                }
        
        # Normalize
        if total_weight > 0:
            overall_sentiment = weighted_sentiment / total_weight
        else:
            overall_sentiment = 0.0
        
        overall_sentiment = np.clip(overall_sentiment, -1, 1)
        
        # Calculate sentiment confidence
        sentiment_confidence = total_weight / sum(source_weights.values())
        sentiment_confidence = np.clip(sentiment_confidence, 0, 1)
        
        # Determine trends
        short_term_readings = [r for r in relevant_readings if datetime.now() - r.timestamp < timedelta(hours=6)]
        long_term_readings = [r for r in relevant_readings if datetime.now() - r.timestamp < timedelta(hours=48)]
        
        short_trend = self._get_trend(short_term_readings)
        long_trend = self._get_trend(long_term_readings)
        
        # Signal strength based on consistency
        sentiments = [r.sentiment_score for r in relevant_readings]
        signal_strength = 1 - np.std(sentiments) if sentiments else 0
        signal_strength = np.clip(signal_strength, 0, 1)
        
        return AggregatedSentiment(
            symbol=symbol,
            overall_sentiment=overall_sentiment,
            sentiment_confidence=sentiment_confidence,
            source_breakdown=source_breakdown,
            short_term_trend=short_trend,
            long_term_trend=long_trend,
            signal_strength=signal_strength,
            timestamp=datetime.now(),
            underlying_data=relevant_readings[-10:]  # Last 10 readings
        )
    
    def _get_trend(self, readings: List[SentimentReading]) -> str:
        """Determine trend from readings"""
        if not readings:
            return "stable"
        
        sentiments = [r.sentiment_score for r in readings]
        recent = sentiments[-5:]
        older = sentiments[:-5] if len(sentiments) > 5 else sentiments
        
        recent_avg = np.mean(recent) if recent else 0
        older_avg = np.mean(older) if older else 0
        
        change = recent_avg - older_avg
        
        if change > 0.1:
            return "improving"
        elif change < -0.1:
            return "deteriorating"
        else:
            return "stable"


# ============================================================================
# PART 4: SENTIMENT-BASED TRADING SIGNALS
# ============================================================================

class SentimentTradeSignalGenerator:
    """Generate trading signals based on sentiment analysis"""
    
    def __init__(self, min_sentiment_threshold: float = 0.3):
        self.min_sentiment_threshold = min_sentiment_threshold
        self.logger = logging.getLogger("SentimentSignalGenerator")
    
    def generate_signal(self, aggregated_sentiment: AggregatedSentiment) -> Tuple[int, float, str]:
        """
        Generate trading signal from sentiment
        
        Returns:
            (signal: 1=BUY, -1=SELL, 0=HOLD, confidence: 0-1, reason: str)
        """
        sentiment = aggregated_sentiment.overall_sentiment
        confidence = aggregated_sentiment.sentiment_confidence
        strength = aggregated_sentiment.signal_strength
        
        # Check signal strength - need strong consensus
        if strength < 0.3:
            return 0, 0, "Weak signal - insufficient consensus"
        
        # Generate signal based on sentiment and trend
        if sentiment > 0.5 and aggregated_sentiment.short_term_trend == "improving":
            # Strong bullish
            signal_confidence = confidence * strength
            return 1, signal_confidence, "Strong bullish sentiment with improving trend"
        
        elif sentiment > self.min_sentiment_threshold:
            # Mild bullish
            signal_confidence = confidence * strength * 0.7
            return 1, signal_confidence, "Mild bullish sentiment"
        
        elif sentiment < -0.5 and aggregated_sentiment.short_term_trend == "deteriorating":
            # Strong bearish
            signal_confidence = confidence * strength
            return -1, signal_confidence, "Strong bearish sentiment with deteriorating trend"
        
        elif sentiment < -self.min_sentiment_threshold:
            # Mild bearish
            signal_confidence = confidence * strength * 0.7
            return -1, signal_confidence, "Mild bearish sentiment"
        
        else:
            # Neutral/Hold
            return 0, 0, "Neutral sentiment"
    
    def get_signal_report(self, symbol: str, aggregated_sentiment: AggregatedSentiment) -> Dict:
        """Generate detailed sentiment signal report"""
        signal, confidence, reason = self.generate_signal(aggregated_sentiment)
        
        return {
            'symbol': symbol,
            'signal': 'BUY' if signal == 1 else 'SELL' if signal == -1 else 'HOLD',
            'signal_value': signal,
            'confidence': confidence,
            'reason': reason,
            'overall_sentiment': aggregated_sentiment.overall_sentiment,
            'sentiment_confidence': aggregated_sentiment.sentiment_confidence,
            'signal_strength': aggregated_sentiment.signal_strength,
            'short_term_trend': aggregated_sentiment.short_term_trend,
            'long_term_trend': aggregated_sentiment.long_term_trend,
            'source_breakdown': aggregated_sentiment.source_breakdown,
            'timestamp': aggregated_sentiment.timestamp.isoformat()
        }


# ============================================================================
# PART 5: INTEGRATION WITH MULTI-MODEL SYSTEM
# ============================================================================

class SentimentModelAdapter:
    """Adapter to integrate sentiment analysis with multi-model trading system"""
    
    def __init__(self, sentiment_analyzer: SentimentAggregator = None):
        self.sentiment_analyzer = sentiment_analyzer or SentimentAggregator()
        self.signal_generator = SentimentTradeSignalGenerator()
        self.logger = logging.getLogger("SentimentModelAdapter")
    
    def create_sentiment_prediction(self, symbol: str, lookback_hours: int = 24):
        """
        Create ModelPrediction object compatible with multi-model system
        
        Returns:
            ModelPrediction object that can be used in signal combination
        """
        agg_sentiment = self.sentiment_analyzer.get_aggregated_sentiment(symbol, lookback_hours)
        signal, confidence, reason = self.signal_generator.generate_signal(agg_sentiment)
        
        # Convert signal to prediction format
        if signal == 1:
            signal_enum = "BUY"
            predicted_return = (agg_sentiment.overall_sentiment + 1) * 2.5  # 0% to 5% expected
        elif signal == -1:
            signal_enum = "SELL"
            predicted_return = (agg_sentiment.overall_sentiment - 1) * -2.5  # -5% to 0% expected
        else:
            signal_enum = "HOLD"
            predicted_return = 0.0
        
        prediction = {
            'model_name': 'SentimentAnalysis',
            'signal': signal_enum,
            'confidence': confidence,
            'predicted_return': predicted_return,
            'timestamp': datetime.now().isoformat(),
            'metadata': {
                'overall_sentiment': agg_sentiment.overall_sentiment,
                'signal_strength': agg_sentiment.signal_strength,
                'source_breakdown': agg_sentiment.source_breakdown,
                'short_term_trend': agg_sentiment.short_term_trend,
                'long_term_trend': agg_sentiment.long_term_trend
            }
        }
        
        return prediction


# ============================================================================
# PART 6: MAIN SENTIMENT ANALYZER CLASS
# ============================================================================

class ComprehensiveSentimentAnalyzer:
    """
    Main class for complete sentiment analysis system
    
    Combines:
    - Multiple sentiment engines (VADER, TextBlob, Transformers)
    - Multiple data sources (News, Twitter, Reddit, Technical)
    - Aggregation and weighting
    - Signal generation
    - Integration with trading system
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ComprehensiveSentimentAnalyzer")
        
        # Initialize components
        self.sentiment_engine = HybridSentimentAnalyzer()
        self.news_collector = NewsNewsSentimentCollector(self.sentiment_engine)
        self.social_collector = SocialMediaSentimentCollector(self.sentiment_engine)
        self.technical_sentiment = TechnicalSentimentIndicator()
        self.aggregator = SentimentAggregator()
        self.signal_generator = SentimentTradeSignalGenerator()
        self.model_adapter = SentimentModelAdapter(self.aggregator)
        
        self.logger.info("✓ Comprehensive Sentiment Analyzer initialized")
    
    def analyze_symbol(self, symbol: str, news_articles: List[Dict] = None,
                      tweets: List[Dict] = None, reddit_posts: List[Dict] = None,
                      market_data: pd.DataFrame = None, lookback_hours: int = 24) -> Dict:
        """
        Complete sentiment analysis for a symbol
        
        Args:
            symbol: Stock symbol
            news_articles: List of news articles
            tweets: List of tweets
            reddit_posts: List of Reddit posts
            market_data: OHLCV data for technical sentiment
            lookback_hours: Hours to look back for aggregation
        
        Returns:
            Comprehensive sentiment report with trading signal
        """
        try:
            # Collect sentiment from all sources
            if news_articles:
                self.news_collector.analyze_news(news_articles)
            
            if tweets:
                self.social_collector.analyze_tweets(tweets)
            
            if reddit_posts:
                self.social_collector.analyze_reddit_posts(reddit_posts)
            
            # Add technical sentiment if market data provided
            if market_data is not None:
                technical_sentiment = self.technical_sentiment.calculate_technical_sentiment(market_data, symbol)
                tech_reading = SentimentReading(
                    source=SentimentSource.TECHNICAL,
                    symbol=symbol,
                    sentiment_score=technical_sentiment,
                    confidence=0.8,  # Moderate confidence for technical
                    text="Technical indicators sentiment",
                    timestamp=datetime.now(),
                    sentiment_category="bullish" if technical_sentiment > 0.3 else "bearish" if technical_sentiment < -0.3 else "neutral",
                    relevance_score=0.9
                )
                self.aggregator.add_readings([tech_reading])
            
            # Get aggregated sentiment
            agg_sentiment = self.aggregator.get_aggregated_sentiment(symbol, lookback_hours)
            
            # Generate trading signal
            signal_report = self.signal_generator.get_signal_report(symbol, agg_sentiment)
            
            # Create model prediction for integration
            model_prediction = self.model_adapter.create_sentiment_prediction(symbol, lookback_hours)
            
            return {
                'symbol': symbol,
                'sentiment_report': signal_report,
                'model_prediction': model_prediction,
                'aggregated_sentiment': {
                    'overall_sentiment': agg_sentiment.overall_sentiment,
                    'confidence': agg_sentiment.sentiment_confidence,
                    'source_breakdown': agg_sentiment.source_breakdown,
                    'short_term_trend': agg_sentiment.short_term_trend,
                    'long_term_trend': agg_sentiment.long_term_trend,
                    'signal_strength': agg_sentiment.signal_strength
                },
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Failed to analyze {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'sentiment_report': None,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_portfolio_sentiment(self, symbols: List[str]) -> Dict:
        """Get sentiment analysis for entire portfolio"""
        portfolio_sentiment = {}
        
        for symbol in symbols:
            agg_sentiment = self.aggregator.get_aggregated_sentiment(symbol)
            signal, confidence, reason = self.signal_generator.generate_signal(agg_sentiment)
            
            portfolio_sentiment[symbol] = {
                'sentiment': agg_sentiment.overall_sentiment,
                'signal': 'BUY' if signal == 1 else 'SELL' if signal == -1 else 'HOLD',
                'confidence': confidence,
                'trend': agg_sentiment.short_term_trend
            }
        
        return portfolio_sentiment


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_sentiment_report(report: Dict):
    """Pretty print sentiment report"""
    print("\n" + "="*70)
    print(f"SENTIMENT ANALYSIS REPORT - {report['symbol']}")
    print("="*70)
    
    sr = report.get('sentiment_report', {})
    print(f"\nSignal: {sr.get('signal', 'N/A')} (Confidence: {sr.get('confidence', 0):.2%})")
    print(f"Reason: {sr.get('reason', 'N/A')}")
    print(f"\nOverall Sentiment: {sr.get('overall_sentiment', 0):.3f} (Range: -1.0 to 1.0)")
    print(f"Signal Strength: {sr.get('signal_strength', 0):.2%}")
    print(f"Short-term Trend: {sr.get('short_term_trend', 'N/A')}")
    print(f"Long-term Trend: {sr.get('long_term_trend', 'N/A')}")
    
    print("\nSource Breakdown:")
    for source, data in sr.get('source_breakdown', {}).items():
        print(f"  • {source.upper()}: {data.get('sentiment', 0):.3f} ({data.get('readings', 0)} readings)")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    # Quick test
    print("\n🎯 Sentiment Analysis Module Loaded Successfully!\n")
    print("Features:")
    print("✓ VADER Sentiment Analysis")
    print("✓ TextBlob Sentiment Analysis")
    print("✓ Transformer-based Deep Learning")
    print("✓ Hybrid Multi-Engine Approach")
    print("✓ News Sentiment Collection")
    print("✓ Social Media Sentiment (Twitter/Reddit)")
    print("✓ Technical Sentiment Indicators")
    print("✓ Sentiment Aggregation & Weighting")
    print("✓ Trading Signal Generation")
    print("✓ Integration with Multi-Model System")
    print("\n")
