"""
Advanced Feature Engineering Module
- Time-based patterns (opening/closing, day-of-week seasonality)
- News sentiment scoring (basic implementation)
- Gap analysis
- Intrabar volatility
- Session-based features
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
import logging

class TimeBasedFeatures:
    """Extract time-based patterns and seasonality"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def add_time_features(self, df):
        """
        Add time-based features to dataframe
        
        Returns:
        - hour: Trading hour (9-15 for NSE)
        - minute: Minute within hour
        - is_opening_hour: Boolean (9:15-9:45)
        - is_closing_hour: Boolean (15:30-15:59)
        - is_lunch_hour: Boolean (12:00-13:00)
        - day_of_week: 0=Monday, 6=Sunday
        - is_weekend: Boolean
        - trading_session: 'opening'|'morning'|'midday'|'afternoon'|'closing'
        - time_to_close: Minutes until market close (15:30)
        - hour_of_day_encoded: sin/cos encoding for cyclical hour
        """
        try:
            # Ensure datetime column
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'])
            else:
                self.logger.warning("No datetime column found")
                return df
            
            # Basic time features
            df['hour'] = df['datetime'].dt.hour
            df['minute'] = df['datetime'].dt.minute
            df['day_of_week'] = df['datetime'].dt.dayofweek  # 0=Monday, 4=Friday
            
            # Market sessions (NSE timing)
            df['is_opening_hour'] = ((df['hour'] == 9) & (df['minute'] <= 45)).astype(int)  # 9:15-9:45
            df['is_closing_hour'] = ((df['hour'] == 15) & (df['minute'] >= 30)).astype(int)  # 15:30-15:59
            df['is_lunch_hour'] = ((df['hour'] >= 12) & (df['hour'] < 13)).astype(int)       # 12:00-12:59
            
            # Trading session categorization
            def get_session(hour, minute):
                if hour < 9 or (hour == 9 and minute < 15):
                    return 'pre-market'
                elif hour == 9 and minute <= 45:
                    return 'opening'  # Highest volatility
                elif hour < 12:
                    return 'morning'   # High activity
                elif hour < 13:
                    return 'lunch'     # Lowest activity
                elif hour < 15:
                    return 'afternoon' # Moderate activity
                elif hour >= 15 and minute >= 30:
                    return 'closing'   # Profit-taking
                else:
                    return 'midday'
            
            df['trading_session'] = df.apply(lambda row: get_session(row['hour'], row['minute']), axis=1)
            
            # Time-based metrics
            df['time_to_close'] = (15*60 + 30) - (df['hour']*60 + df['minute'])  # Minutes to 15:30
            df['time_to_close'] = df['time_to_close'].clip(lower=0)
            df['time_to_close_ratio'] = df['time_to_close'] / (6*60 + 15)  # Fraction of day remaining
            
            # Cyclical encoding for hour (sine/cosine for circular nature)
            df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
            df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
            
            # Day-of-week seasonality
            df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
            df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
            
            # Week phase (early week vs late week bias)
            df['is_monday'] = (df['day_of_week'] == 0).astype(int)      # Gap risk
            df['is_friday'] = (df['day_of_week'] == 4).astype(int)      # Profit-taking
            df['is_midweek'] = ((df['day_of_week'] >= 1) & (df['day_of_week'] <= 3)).astype(int)  # Stable
            
            # Opening hour volatility is higher than closing
            df['is_high_vol_session'] = df['is_opening_hour'].astype(int)
            
            # Session-based expected volatility
            session_volatility = {
                'opening': 1.0,      # Baseline
                'morning': 0.8,      # Slightly lower
                'midday': 0.6,       # Lower
                'lunch': 0.4,        # Lowest
                'afternoon': 0.7,    # Picking up
                'closing': 0.9,      # High again
            }
            df['session_volatility_factor'] = df['trading_session'].map(session_volatility).fillna(0.5)
            
            self.logger.info(f"[TIME FEATURES] Added 17 time-based features")
            return df
        
        except Exception as e:
            self.logger.error(f"[TIME FEATURES ERROR] {str(e)}")
            return df


class NewsAndGapFeatures:
    """Extract news sentiment and gap analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.news_keywords = {
            'positive': ['bullish', 'surge', 'rally', 'breakthrough', 'strong', 'gains', 'outperform', 'upgrade', 'profit', 'growth'],
            'negative': ['bearish', 'crash', 'plunge', 'collapse', 'weak', 'loss', 'underperform', 'downgrade', 'decline', 'recession'],
            'volatile': ['earnings', 'ipo', 'merger', 'split', 'announcement', 'conference', 'event', 'surprise', 'shock']
        }
    
    def add_gap_features(self, df):
        """
        Detect gaps and add gap-based features
        
        Gap = Open price significantly different from previous close
        Indicates overnight news or market events
        """
        try:
            # Calculate previous close
            df['prev_close'] = df['close'].shift(1)
            
            # Gap calculation
            df['gap'] = (df['open'] - df['prev_close']) / df['prev_close']  # % gap
            df['gap_abs'] = abs(df['gap'])
            df['has_gap'] = (df['gap_abs'] > 0.005).astype(int)  # >0.5% gap
            df['gap_size'] = df['gap_abs'].rolling(5).mean()  # Average gap
            
            # Gap direction
            df['gap_direction'] = np.where(df['gap'] > 0, 1, -1)  # Up gap vs Down gap
            
            # Gap fill probability (price tends to fill gaps)
            df['gap_filled'] = ((df['low'] <= df['prev_close']) | (df['high'] >= df['prev_close'])).astype(int)
            
            self.logger.info(f"[GAP FEATURES] Added 5 gap-based features")
            return df
        
        except Exception as e:
            self.logger.error(f"[GAP FEATURES ERROR] {str(e)}")
            return df
    
    def add_news_sentiment(self, df, ticker, news_data=None):
        """
        Add news sentiment features
        
        For now: Mock implementation with calendar-based sentiment
        In production: Connect to real news API (NewsAPI, Finnhub, etc.)
        
        Returns:
        - news_sentiment: -1 (bearish), 0 (neutral), +1 (bullish)
        - news_confidence: 0-1 (how confident we are)
        - is_earnings_day: Boolean
        - is_macro_event: Boolean (RBI, Fed announcements, etc.)
        """
        try:
            # Mock news data structure
            if news_data is None:
                news_data = []
            
            # Initialize sentiment column
            df['news_sentiment'] = 0  # Neutral by default
            df['news_confidence'] = 0
            df['is_earnings_day'] = 0
            df['is_macro_event'] = 0
            df['sentiment_strength'] = 0  # 0-1 scale
            
            # If real news data provided
            if news_data and len(news_data) > 0:
                for idx, row in df.iterrows():
                    row_date = row['datetime'].date()
                    
                    # Check for news on this date
                    day_news = [n for n in news_data if n.get('date') == row_date]
                    
                    if day_news:
                        sentiments = [self._score_news(n) for n in day_news]
                        avg_sentiment = np.mean([s['score'] for s in sentiments])
                        confidence = np.mean([s['confidence'] for s in sentiments])
                        
                        df.at[idx, 'news_sentiment'] = np.sign(avg_sentiment)
                        df.at[idx, 'news_confidence'] = confidence
                        df.at[idx, 'sentiment_strength'] = abs(avg_sentiment)
                        
                        # Check for special events
                        for news in day_news:
                            if news.get('type') == 'earnings':
                                df.at[idx, 'is_earnings_day'] = 1
                            if news.get('type') == 'macro':
                                df.at[idx, 'is_macro_event'] = 1
            
            # Mock calendar-based sentiment (example)
            # In production, replace with real API data
            df['has_news'] = (df['news_sentiment'] != 0).astype(int)
            
            self.logger.info(f"[NEWS SENTIMENT] Added 6 sentiment features")
            return df
        
        except Exception as e:
            self.logger.error(f"[NEWS SENTIMENT ERROR] {str(e)}")
            return df
    
    def _score_news(self, news_item):
        """Score individual news item for sentiment"""
        text = (news_item.get('title', '') + ' ' + news_item.get('description', '')).lower()
        
        positive_score = sum(text.count(kw) for kw in self.news_keywords['positive'])
        negative_score = sum(text.count(kw) for kw in self.news_keywords['negative'])
        
        net_score = positive_score - negative_score
        max_score = max(positive_score, negative_score, 1)
        
        return {
            'score': net_score / max_score,
            'confidence': min(0.9, (positive_score + negative_score) / 10)
        }


class VolatilityEnhancedFeatures:
    """Extract intrabar volatility and volatility clustering"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def add_intrabar_volatility(self, df):
        """
        Calculate intrabar volatility measures
        
        Returns:
        - intrabar_volatility: (High - Low) / Close
        - volatility_clustering: Rolling volatility (should cluster)
        - volatility_regimes: 'low'|'medium'|'high'
        """
        try:
            # Intrabar range
            df['intrabar_range'] = (df['high'] - df['low']) / df['close']
            df['intrabar_range_ma'] = df['intrabar_range'].rolling(5).mean()
            
            # Body vs Wick ratio
            df['body'] = abs(df['close'] - df['open'])
            df['upper_wick'] = df['high'] - np.maximum(df['open'], df['close'])
            df['lower_wick'] = np.minimum(df['open'], df['close']) - df['low']
            df['wick_to_body'] = (df['upper_wick'] + df['lower_wick']) / (df['body'] + 1e-10)
            
            # Volatility clustering (volatility tends to cluster)
            df['returns'] = df['close'].pct_change()
            df['volatility'] = df['returns'].rolling(10).std()
            df['volatility_ma'] = df['volatility'].rolling(5).mean()
            
            # Volatility regimes
            vol_threshold_low = df['volatility'].quantile(0.33)
            vol_threshold_high = df['volatility'].quantile(0.67)
            
            def get_vol_regime(vol):
                if vol < vol_threshold_low:
                    return 'low'
                elif vol < vol_threshold_high:
                    return 'medium'
                else:
                    return 'high'
            
            df['volatility_regime'] = df['volatility'].apply(get_vol_regime)
            
            # Volatility persistence
            df['vol_persistence'] = df['volatility'].rolling(5).corr(df['volatility'].shift(1))
            
            self.logger.info(f"[VOLATILITY FEATURES] Added 8 intrabar volatility features")
            return df
        
        except Exception as e:
            self.logger.error(f"[VOLATILITY ERROR] {str(e)}")
            return df


class PriceActionFeatures:
    """Extract price action patterns and strength"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def add_price_action(self, df):
        """
        Advanced price action features
        
        Returns:
        - bullish_engulf: Bullish engulfing pattern
        - bearish_engulf: Bearish engulfing pattern
        - hammer: Hammer pattern (reversal)
        - shooting_star: Shooting star pattern
        - candle_strength: How strong was the candle
        - consecutive_direction: How many candles in same direction
        """
        try:
            df['up_candle'] = (df['close'] >= df['open']).astype(int)
            df['down_candle'] = (df['close'] < df['open']).astype(int)
            
            # Consecutive candles in same direction
            df['consecutive_direction'] = (df['up_candle'] != df['up_candle'].shift()).cumsum()
            df['consecutive_count'] = df.groupby('consecutive_direction').cumcount() + 1
            
            # Candle strength (% of daily range that was captured)
            df['candle_strength'] = abs(df['close'] - df['open']) / (df['high'] - df['low'] + 1e-10)
            
            # Engulfing patterns (current candle contains previous candle)
            df['bullish_engulfing'] = (
                (df['up_candle'] == 1) & 
                (df['down_candle'].shift(1) == 1) &
                (df['close'] > df['open'].shift(1)) &
                (df['open'] < df['close'].shift(1))
            ).astype(int)
            
            df['bearish_engulfing'] = (
                (df['down_candle'] == 1) & 
                (df['up_candle'].shift(1) == 1) &
                (df['close'] < df['open'].shift(1)) &
                (df['open'] > df['close'].shift(1))
            ).astype(int)
            
            # Hammer pattern (small body, long lower wick)
            df['body_size'] = abs(df['close'] - df['open']) / df['close']
            df['lower_wick'] = (np.minimum(df['open'], df['close']) - df['low']) / df['close']
            df['upper_wick'] = (df['high'] - np.maximum(df['open'], df['close'])) / df['close']
            
            df['hammer'] = (
                (df['lower_wick'] > df['body_size'] * 2) &
                (df['upper_wick'] < df['body_size'] * 0.5) &
                (df['up_candle'] == 1)
            ).astype(int)
            
            # Shooting star pattern (opposite of hammer)
            df['shooting_star'] = (
                (df['upper_wick'] > df['body_size'] * 2) &
                (df['lower_wick'] < df['body_size'] * 0.5) &
                (df['down_candle'] == 1)
            ).astype(int)
            
            self.logger.info(f"[PRICE ACTION] Added 9 price action features")
            return df
        
        except Exception as e:
            self.logger.error(f"[PRICE ACTION ERROR] {str(e)}")
            return df


class AdvancedFeatureEngineer:
    """Complete advanced feature engineering pipeline"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.time_features = TimeBasedFeatures()
        self.news_features = NewsAndGapFeatures()
        self.volatility_features = VolatilityEnhancedFeatures()
        self.price_action_features = PriceActionFeatures()
    
    def generate_all_advanced_features(self, df, ticker=None, news_data=None):
        """
        Generate all advanced features
        
        Args:
        - df: DataFrame with OHLCV
        - ticker: Ticker symbol for news lookup
        - news_data: Pre-fetched news data (optional)
        
        Returns:
        - Enhanced DataFrame with 35+ new features
        """
        try:
            self.logger.info("[ADVANCED] Starting advanced feature engineering...")
            
            # Time-based features (17)
            df = self.time_features.add_time_features(df)
            
            # Gap features (5)
            df = self.news_features.add_gap_features(df)
            
            # News sentiment (6)
            df = self.news_features.add_news_sentiment(df, ticker, news_data)
            
            # Volatility features (8)
            df = self.volatility_features.add_intrabar_volatility(df)
            
            # Price action features (9)
            df = self.price_action_features.add_price_action(df)
            
            # Fill NaN values
            df = df.bfill().ffill().fillna(0)
            
            self.logger.info(f"[ADVANCED] Total advanced features added: 45+")
            self.logger.info(f"[ADVANCED] Final shape: {df.shape}")
            
            return df
        
        except Exception as e:
            self.logger.error(f"[ADVANCED ERROR] {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return df


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create sample data
    dates = pd.date_range(start='2026-06-01 09:15', end='2026-06-10 15:30', freq='1min')
    df = pd.DataFrame({
        'datetime': dates,
        'open': np.random.randn(len(dates)).cumsum() + 100,
        'high': np.random.randn(len(dates)).cumsum() + 101,
        'low': np.random.randn(len(dates)).cumsum() + 99,
        'close': np.random.randn(len(dates)).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, len(dates))
    })
    
    # Ensure high/low/close are valid
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)
    
    # Generate advanced features
    engineer = AdvancedFeatureEngineer()
    df_features = engineer.generate_all_advanced_features(df, ticker='NIFTY50')
    
    print("\n=== ADVANCED FEATURES ADDED ===")
    print(f"Original columns: 6")
    print(f"Final columns: {len(df_features.columns)}")
    print(f"New features: {len(df_features.columns) - 6}")
    print(f"\nFeature list:")
    for col in sorted(df_features.columns[6:]):
        print(f"  - {col}")
