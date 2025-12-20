
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.news_service import NewsService
from datetime import datetime

@pytest.fixture
def news_service():
    with patch("app.services.news_service.settings") as mock_settings:
        mock_settings.ALPHA_VANTAGE_API_KEY = "test_key"
        service = NewsService()
        yield service

@pytest.mark.asyncio
async def test_fetch_news_success(news_service):
    mock_response_data = {
        "feed": [
            {
                "title": "Test News",
                "summary": "Test Summary",
                "url": "http://test.com",
                "source": "Test Source",
                "time_published": "20230101T120000",
                "overall_sentiment_label": "Bullish",
                "ticker_sentiment": [{"ticker": "AAPL"}]
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=mock_response_data)

    # Mock context manager for session.get
    mock_get_context = MagicMock()
    mock_get_context.__aenter__.return_value = mock_response
    mock_get_context.__aexit__.return_value = None

    # Mock session
    mock_session = MagicMock()
    mock_session.get.return_value = mock_get_context

    # Mock ClientSession context manager
    mock_session_context = MagicMock()
    mock_session_context.__aenter__.return_value = mock_session
    mock_session_context.__aexit__.return_value = None

    # Patch ClientSession to return the mock context
    with patch("aiohttp.ClientSession", return_value=mock_session_context):
        news = await news_service.get_market_news(limit=1)

        assert len(news) == 1
        assert news[0]["title"] == "Test News"
        assert news[0]["sentiment"] == "positive"
        assert news[0]["tickers"] == ["AAPL"]
        assert isinstance(news[0]["published_at"], datetime)

@pytest.mark.asyncio
async def test_fetch_news_api_error(news_service):
    mock_response = MagicMock()
    mock_response.status = 500

    mock_get_context = MagicMock()
    mock_get_context.__aenter__.return_value = mock_response
    mock_get_context.__aexit__.return_value = None

    mock_session = MagicMock()
    mock_session.get.return_value = mock_get_context

    mock_session_context = MagicMock()
    mock_session_context.__aenter__.return_value = mock_session
    mock_session_context.__aexit__.return_value = None

    with patch("aiohttp.ClientSession", return_value=mock_session_context):
        news = await news_service.get_market_news()
        assert len(news) == 0

@pytest.mark.asyncio
async def test_get_symbol_news(news_service):
    mock_response_data = {
        "feed": [
            {
                "title": "Symbol News",
                "summary": "Summary",
                "url": "http://test.com",
                "source": "Source",
                "time_published": "20230101T120000",
                "overall_sentiment_label": "Bearish",
                "ticker_sentiment": [{"ticker": "TSLA"}]
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=mock_response_data)

    mock_get_context = MagicMock()
    mock_get_context.__aenter__.return_value = mock_response
    mock_get_context.__aexit__.return_value = None

    mock_session = MagicMock()
    mock_session.get.return_value = mock_get_context

    mock_session_context = MagicMock()
    mock_session_context.__aenter__.return_value = mock_session
    mock_session_context.__aexit__.return_value = None

    with patch("aiohttp.ClientSession", return_value=mock_session_context):
        news = await news_service.get_symbol_news("TSLA", limit=1)

        assert len(news) == 1
        assert news[0]["title"] == "Symbol News"
        assert news[0]["sentiment"] == "negative"
        assert news[0]["tickers"] == ["TSLA"]
