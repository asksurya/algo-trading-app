"""
News service for aggregating market news from various sources.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import aiohttp
import asyncio
import os
import logging
from textblob import TextBlob
from app.core.config import settings

logger = logging.getLogger(__name__)

class NewsService:
    """
    Service for fetching and aggregating financial news.
    Supports multiple news sources.
    """
    
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self):
        self.alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY or os.getenv("ALPHA_VANTAGE_API_KEY")
        self.news_api_key = os.getenv("NEWS_API_KEY")

        if not self.alpha_vantage_key:
            logger.warning("ALPHA_VANTAGE_API_KEY not set. News service may not function correctly.")
    
    async def _fetch_news(self, params: Dict[str, str]) -> List[Dict]:
        """
        Fetch news from Alpha Vantage API.

        Args:
            params: Query parameters for the API call

        Returns:
            List of parsed news articles
        """
        if not self.alpha_vantage_key:
            logger.error("Alpha Vantage API key missing")
            return []

        default_params = {
            "function": "NEWS_SENTIMENT",
            "apikey": self.alpha_vantage_key,
            "sort": "LATEST"
        }
        query_params = {**default_params, **params}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=query_params) as response:
                    if response.status != 200:
                        logger.error(f"Error fetching news: {response.status}")
                        return []

                    data = await response.json()

                    if "feed" not in data:
                        if "Note" in data: # API limit reached
                            logger.warning(f"Alpha Vantage API limit reached: {data['Note']}")
                        elif "Error Message" in data:
                            logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                        return []

                    return self._parse_av_news(data["feed"])
        except Exception as e:
            logger.error(f"Exception fetching news: {str(e)}")
            return []

    def _parse_av_news(self, feed: List[Dict[str, Any]]) -> List[Dict]:
        """
        Parse Alpha Vantage news feed into application format.

        Args:
            feed: List of news items from Alpha Vantage

        Returns:
            List of parsed news articles
        """
        parsed_news = []

        for item in feed:
            try:
                # Parse date: "20230101T123000" -> datetime
                time_published_str = item.get("time_published", "")
                published_at = datetime.utcnow()
                if time_published_str:
                    try:
                        published_at = datetime.strptime(time_published_str, "%Y%m%dT%H%M%S")
                    except ValueError:
                        pass

                # Extract tickers
                tickers = []
                if "ticker_sentiment" in item:
                    tickers = [t["ticker"] for t in item["ticker_sentiment"]]

                # Map sentiment
                sentiment_label = item.get("overall_sentiment_label", "Neutral")
                sentiment = "neutral"
                if "Bullish" in sentiment_label:
                    sentiment = "positive"
                elif "Bearish" in sentiment_label:
                    sentiment = "negative"

                parsed_news.append({
                    "id": item.get("url", ""), # Use URL as ID
                    "title": item.get("title", ""),
                    "summary": item.get("summary", ""),
                    "source": item.get("source", ""),
                    "url": item.get("url", ""),
                    "published_at": published_at,
                    "sentiment": sentiment,
                    "tickers": tickers,
                    "image_url": item.get("banner_image", "")
                })
            except Exception as e:
                logger.warning(f"Error parsing news item: {e}")
                continue

        return parsed_news

    async def get_market_news(self, limit: int = 20) -> List[Dict]:
        """
        Get general market news.
        
        Args:
            limit: Number of news articles to return
        
        Returns:
            List of news articles
        """
        # Fetch news with general financial topics
        # topics=financial_markets is a good default for general news
        news = await self._fetch_news({"topics": "financial_markets", "limit": str(limit)})
        return news[:limit]
    
    async def get_symbol_news(self, symbol: str, limit: int = 10) -> List[Dict]:
        """
        Get news for a specific stock symbol.
        
        Args:
            symbol: Stock symbol
            limit: Number of articles
        
        Returns:
            List of news articles related to the symbol
        """
        news = await self._fetch_news({"tickers": symbol, "limit": str(limit)})
        return news[:limit]
    
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
