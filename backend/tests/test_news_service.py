import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import os
from app.services.news_service import NewsService

@pytest.fixture
def news_service():
    with patch.dict(os.environ, {'ALPHA_VANTAGE_API_KEY': 'test_key'}):
        service = NewsService()
        return service

@pytest.mark.asyncio
async def test_get_symbol_news_success(news_service):
    # Mock response data from Alpha Vantage
    mock_data = {
        "items": "2",
        "feed": [
            {
                "title": "Test News 1",
                "url": "https://example.com/1",
                "time_published": "20230101T120000",
                "authors": ["Author 1"],
                "summary": "Summary 1",
                "source": "Source 1",
                "overall_sentiment_label": "Bullish",
                "ticker_sentiment": [{"ticker": "AAPL", "relevance_score": "0.8", "ticker_sentiment_score": "0.5", "ticker_sentiment_label": "Bullish"}]
            },
            {
                "title": "Test News 2",
                "url": "https://example.com/2",
                "time_published": "20230102T120000",
                "authors": ["Author 2"],
                "summary": "Summary 2",
                "source": "Source 2",
                "overall_sentiment_label": "Bearish",
                "ticker_sentiment": []
            }
        ]
    }

    # Setup the mock for ClientSession
    # We patch the class so that ClientSession() returns our mock instance
    with patch('aiohttp.ClientSession') as MockSessionCls:
        # The session instance
        session_mock = MagicMock() # session object itself is synchronous (init is sync)
        # But it is used as async context manager: async with ClientSession()
        # So __aenter__ must be async

        session_enter_mock = AsyncMock(return_value=session_mock)
        session_mock.__aenter__ = session_enter_mock
        session_mock.__aexit__ = AsyncMock()

        MockSessionCls.return_value = session_mock

        # session.get() returns a response context manager
        # It is called synchronously: session.get(...)
        response_ctx_mgr = MagicMock()
        session_mock.get.return_value = response_ctx_mgr

        # The response context manager is used in 'async with'
        # So its __aenter__ must be async and return the response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = mock_data

        response_enter_mock = AsyncMock(return_value=mock_response)
        response_ctx_mgr.__aenter__ = response_enter_mock
        response_ctx_mgr.__aexit__ = AsyncMock()

        news = await news_service.get_symbol_news("AAPL", limit=2)

        assert len(news) == 2
        assert news[0]['title'] == "Test News 1"
        assert news[0]['sentiment'] == "positive"
        assert news[1]['sentiment'] == "negative"

@pytest.mark.asyncio
async def test_get_symbol_news_no_api_key():
    with patch.dict(os.environ, {}, clear=True):
        with patch('os.getenv', return_value=None):
            service = NewsService()
            news = await service.get_symbol_news("AAPL")
            assert news == []

@pytest.mark.asyncio
async def test_get_symbol_news_api_error(news_service):
    with patch('aiohttp.ClientSession') as MockSessionCls:
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock()
        MockSessionCls.return_value = session_mock

        response_ctx_mgr = MagicMock()
        session_mock.get.return_value = response_ctx_mgr

        mock_response = AsyncMock()
        mock_response.status = 500

        response_ctx_mgr.__aenter__ = AsyncMock(return_value=mock_response)
        response_ctx_mgr.__aexit__ = AsyncMock()

        news = await news_service.get_symbol_news("AAPL")
        assert news == []
