"""
News service for aggregating market news from various sources.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import aiohttp
import asyncio
import os
from textblob import TextBlob


class NewsService:
    """
    Service for fetching and aggregating financial news.
    Supports multiple news sources.
    """
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.news_api_key = os.getenv("NEWS_API_KEY")
    
    async def get_market_news(self, limit: int = 20) -> List[Dict]:
        """
        Get general market news.
        
        Args:
            limit: Number of news articles to return
        
        Returns:
            List of news articles
        """
        # TODO: Implement Alpha Vantage News API integration
        # For now, return mock data
        mock_news = [
            {
                "id": "1",
                "title": "Fed Holds Interest Rates Steady",
                "summary": "The Federal Reserve announced it will maintain current interest rate levels...",
                "source": "Reuters",
                "url": "https://example.com/news/1",
                "published_at": datetime.utcnow() - timedelta(hours=2),
                "sentiment": "neutral",
                "tickers": ["SPY", "QQQ"]
            },
            {
                "id": "2",
                "title": "Tech Stocks Rally on Earnings Beat",
                "summary": "Major technology companies exceeded earnings expectations...",
                "source": "Bloomberg",
                "url": "https://example.com/news/2",
                "published_at": datetime.utcnow() - timedelta(hours=5),
                "sentiment": "positive",
                "tickers": ["AAPL", "MSFT", "GOOGL"]
            }
        ]
        return mock_news[:limit]
    
    async def get_symbol_news(self, symbol: str, limit: int = 10) -> List[Dict]:
        """
        Get news for a specific stock symbol.
        
        Args:
            symbol: Stock symbol
            limit: Number of articles
        
        Returns:
            List of news articles related to the symbol
        """
        # TODO: Implement symbol-specific news fetching
        mock_news = [
            {
                "id": f"{symbol}_1",
                "title": f"{symbol} Announces New Product Launch",
                "summary": f"{symbol} unveiled its latest product at a press event...",
                "source": "TechCrunch",
                "url": f"https://example.com/news/{symbol}/1",
                "published_at": datetime.utcnow() - timedelta(hours=1),
                "sentiment": "positive",
                "tickers": [symbol]
            }
        ]
        return mock_news[:limit]
    
    async def analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of news text.
        
        Args:
            text: News article text
        
        Returns:
            Sentiment: 'positive', 'negative', or 'neutral'
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._analyze_sentiment_sync, text)

    def _analyze_sentiment_sync(self, text: str) -> str:
        """Synchronous helper for sentiment analysis."""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity

        if polarity > 0.1:
            return "positive"
        elif polarity < -0.1:
            return "negative"
        else:
            return "neutral"


# Singleton instance  
_news_service = None


def get_news_service() -> NewsService:
    """Get news service instance."""
    global _news_service
    if _news_service is None:
        _news_service = NewsService()
    return _news_service
