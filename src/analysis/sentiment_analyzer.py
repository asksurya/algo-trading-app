"""
Sentiment Analysis Module

Analyzes market sentiment from multiple sources:
- News headlines
- Social media (Twitter/Reddit)
- Financial news sentiment
- Market mood indicators
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class SentimentAnalyzer:
    """
    Analyze sentiment from multiple sources to enhance trading predictions.
    """
    
    def __init__(
        self,
        news_api_key: Optional[str] = None,
        alpha_vantage_key: Optional[str] = None
    ):
        """
        Initialize Sentiment Analyzer.
        
        Args:
            news_api_key: API key for NewsAPI (get free at newsapi.org)
            alpha_vantage_key: API key for Alpha Vantage sentiment
        """
        self.logger = logging.getLogger(__name__)
        self.news_api_key = news_api_key
        self.alpha_vantage_key = alpha_vantage_key
        
        if not TEXTBLOB_AVAILABLE:
            self.logger.warning("TextBlob not available. Install: pip install textblob")
        
        # Cache sentiment data
        self.sentiment_cache = {}
    
    def get_stock_sentiment(
        self,
        symbol: str,
        days_back: int = 7
    ) -> Dict[str, float]:
        """
        Get comprehensive sentiment score for a stock.
        
        Args:
            symbol: Stock symbol
            days_back: Days of news to analyze
            
        Returns:
            Dictionary with sentiment scores
        """
        sentiments = {
            'news_sentiment': 0.0,
            'headline_sentiment': 0.0,
            'social_sentiment': 0.0,
            'overall_sentiment': 0.0,
            'sentiment_change': 0.0,
            'news_volume': 0,
            'positive_ratio': 0.0
        }
        
        try:
            # Get news sentiment
            news_sent = self._get_news_sentiment(symbol, days_back)
            if news_sent:
                sentiments.update(news_sent)
            
            # Get social sentiment (simplified - would need Twitter/Reddit API)
            social_sent = self._get_social_sentiment(symbol)
            if social_sent:
                sentiments['social_sentiment'] = social_sent
            
            # Calculate overall sentiment
            sentiments['overall_sentiment'] = (
                sentiments['news_sentiment'] * 0.5 +
                sentiments['headline_sentiment'] * 0.3 +
                sentiments['social_sentiment'] * 0.2
            )
            
            # Cache results
            self.sentiment_cache[symbol] = {
                'sentiments': sentiments,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting sentiment for {symbol}: {e}")
        
        return sentiments
    
    def _get_news_sentiment(
        self,
        symbol: str,
        days_back: int = 7
    ) -> Optional[Dict[str, float]]:
        """
        Analyze news sentiment using NewsAPI or Alpha Vantage.
        
        Args:
            symbol: Stock symbol
            days_back: Days of news to analyze
            
        Returns:
            Dict with sentiment scores
        """
        # Try Alpha Vantage first (includes sentiment)
        if self.alpha_vantage_key:
            try:
                return self._get_alpha_vantage_sentiment(symbol)
            except Exception as e:
                self.logger.error(f"Alpha Vantage sentiment failed: {e}")
        
        # Fallback to NewsAPI with TextBlob analysis
        if self.news_api_key and TEXTBLOB_AVAILABLE and REQUESTS_AVAILABLE:
            try:
                return self._get_newsapi_sentiment(symbol, days_back)
            except Exception as e:
                self.logger.error(f"NewsAPI sentiment failed: {e}")
        
        # If no APIs available, use simulated sentiment
        return self._get_simulated_sentiment(symbol)
    
    def _get_alpha_vantage_sentiment(self, symbol: str) -> Dict[str, float]:
        """Get sentiment from Alpha Vantage News Sentiment API."""
        url = f"https://www.alphavantage.co/query"
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': symbol,
            'apikey': self.alpha_vantage_key,
            'limit': 50
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'feed' not in data:
            raise ValueError("No news data in response")
        
        sentiments = []
        headlines = []
        
        for article in data['feed']:
            # Get ticker-specific sentiment
            for ticker_sent in article.get('ticker_sentiment', []):
                if ticker_sent.get('ticker') == symbol:
                    sent_score = float(ticker_sent.get('ticker_sentiment_score', 0))
                    sentiments.append(sent_score)
            
            # Analyze headline
            headline = article.get('title', '')
            if headline:
                headlines.append(headline)
        
        # Calculate scores
        news_sentiment = np.mean(sentiments) if sentiments else 0.0
        headline_sentiment = self._analyze_headlines(headlines)
        
        positive_count = sum(1 for s in sentiments if s > 0.05)
        negative_count = sum(1 for s in sentiments if s < -0.05)
        total = len(sentiments)
        
        return {
            'news_sentiment': news_sentiment,
            'headline_sentiment': headline_sentiment,
            'news_volume': total,
            'positive_ratio': positive_count / total if total > 0 else 0.5,
            'sentiment_change': self._calculate_sentiment_trend(sentiments)
        }
    
    def _get_newsapi_sentiment(
        self,
        symbol: str,
        days_back: int
    ) -> Dict[str, float]:
        """Get news and analyze sentiment using TextBlob."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': f"{symbol} stock",
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'language': 'en',
            'sortBy': 'relevancy',
            'apiKey': self.news_api_key,
            'pageSize': 50
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get('status') != 'ok':
            raise ValueError(f"NewsAPI error: {data.get('message')}")
        
        articles = data.get('articles', [])
        headlines = [art.get('title', '') for art in articles]
        descriptions = [art.get('description', '') for art in articles]
        
        # Analyze sentiment
        headline_scores = []
        description_scores = []
        
        for headline in headlines:
            if headline:
                blob = TextBlob(headline)
                headline_scores.append(blob.sentiment.polarity)
        
        for desc in descriptions:
            if desc:
                blob = TextBlob(desc)
                description_scores.append(blob.sentiment.polarity)
        
        news_sentiment = np.mean(description_scores) if description_scores else 0.0
        headline_sentiment = np.mean(headline_scores) if headline_scores else 0.0
        
        positive_count = sum(1 for s in description_scores if s > 0.1)
        total = len(description_scores)
        
        return {
            'news_sentiment': news_sentiment,
            'headline_sentiment': headline_sentiment,
            'news_volume': total,
            'positive_ratio': positive_count / total if total > 0 else 0.5,
            'sentiment_change': self._calculate_sentiment_trend(description_scores)
        }
    
    def _analyze_headlines(self, headlines: List[str]) -> float:
        """Analyze sentiment of headlines using TextBlob."""
        if not TEXTBLOB_AVAILABLE or not headlines:
            return 0.0
        
        scores = []
        for headline in headlines:
            if headline:
                blob = TextBlob(headline)
                scores.append(blob.sentiment.polarity)
        
        return np.mean(scores) if scores else 0.0
    
    def _calculate_sentiment_trend(self, sentiments: List[float]) -> float:
        """Calculate if sentiment is improving or declining."""
        if len(sentiments) < 2:
            return 0.0
        
        # Split into recent and older
        mid = len(sentiments) // 2
        older = sentiments[:mid]
        recent = sentiments[mid:]
        
        older_avg = np.mean(older) if older else 0
        recent_avg = np.mean(recent) if recent else 0
        
        return recent_avg - older_avg
    
    def _get_social_sentiment(self, symbol: str) -> float:
        """
        Get social media sentiment (simplified).
        
        Note: Real implementation would use Twitter API, Reddit API, or
        social media aggregators like StockTwits.
        """
        # This is a placeholder. Real implementation would:
        # 1. Fetch tweets mentioning the stock
        # 2. Analyze tweet sentiment
        # 3. Consider user influence
        # 4. Aggregate scores
        
        # For now, return neutral
        return 0.0
    
    def _get_simulated_sentiment(self, symbol: str) -> Dict[str, float]:
        """
        Generate simulated sentiment when APIs not available.
        
        This uses simple market indicators as proxy:
        - Price momentum
        - Volume trends
        - Volatility
        """
        # In production, this should fetch real market data
        # For now, return neutral sentiment
        return {
            'news_sentiment': 0.0,
            'headline_sentiment': 0.0,
            'news_volume': 10,
            'positive_ratio': 0.5,
            'sentiment_change': 0.0
        }
    
    def get_batch_sentiment(
        self,
        symbols: List[str],
        days_back: int = 7
    ) -> Dict[str, Dict[str, float]]:
        """
        Get sentiment for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            days_back: Days of news to analyze
            
        Returns:
            Dict mapping symbols to sentiment scores
        """
        results = {}
        
        for symbol in symbols:
            self.logger.info(f"Analyzing sentiment for {symbol}")
            results[symbol] = self.get_stock_sentiment(symbol, days_back)
        
        return results
    
    def get_market_mood(self) -> str:
        """
        Get overall market sentiment/mood.
        
        Returns:
            String describing market mood: 'bullish', 'bearish', 'neutral'
        """
        # This could analyze major indices sentiment
        # For now, return neutral
        return 'neutral'


# Utility functions
def sentiment_to_signal(sentiment_score: float, threshold: float = 0.1) -> int:
    """
    Convert sentiment score to trading signal.
    
    Args:
        sentiment_score: Sentiment score (-1 to 1)
        threshold: Minimum absolute value to generate signal
        
    Returns:
        Signal: 1 (buy), -1 (sell), 0 (hold)
    """
    if sentiment_score > threshold:
        return 1
    elif sentiment_score < -threshold:
        return -1
    else:
        return 0


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Initialize analyzer
    analyzer = SentimentAnalyzer(
        news_api_key="your_newsapi_key",  # Get free at newsapi.org
        alpha_vantage_key="your_alphavantage_key"  # Get free at alphavantage.co
    )
    
    # Get sentiment for a stock
    sentiment = analyzer.get_stock_sentiment('AAPL', days_back=7)
    
    print(f"\nSentiment Analysis for AAPL:")
    print(f"  Overall Sentiment: {sentiment['overall_sentiment']:.3f}")
    print(f"  News Sentiment: {sentiment['news_sentiment']:.3f}")
    print(f"  Headline Sentiment: {sentiment['headline_sentiment']:.3f}")
    print(f"  News Volume: {sentiment['news_volume']}")
    print(f"  Positive Ratio: {sentiment['positive_ratio']:.1%}")
    print(f"  Sentiment Trend: {sentiment['sentiment_change']:.3f}")
    
    # Convert to trading signal
    signal = sentiment_to_signal(sentiment['overall_sentiment'])
    signal_str = "BUY" if signal == 1 else "SELL" if signal == -1 else "HOLD"
    print(f"\n  Trading Signal: {signal_str}")
