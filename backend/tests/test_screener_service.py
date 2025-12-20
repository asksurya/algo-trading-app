import pytest
from unittest.mock import MagicMock, patch
import asyncio
from app.services.screener import ScreenerService, get_screener_service

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.mark.asyncio
async def test_get_most_active_success(mock_session):
    service = ScreenerService(mock_session)

    mock_quotes = [
        {
            "symbol": "AAPL",
            "shortName": "Apple Inc.",
            "regularMarketPrice": 150.0,
            "marketCap": 2000000000,
            "trailingPE": 25.0,
            "dividendYield": 0.5,
            "regularMarketVolume": 1000000,
            "exchange": "NMS"
        },
        {
            "symbol": "MSFT",
            "longName": "Microsoft Corp",
            "regularMarketPrice": 300.0,
            "marketCap": 2500000000,
            "trailingPE": 30.0,
            "dividendYield": 0.8,
            "regularMarketVolume": 800000,
            "exchange": "NMS"
        }
    ]

    mock_screen_result = {"quotes": mock_quotes}

    with patch("yfinance.screen", return_value=mock_screen_result) as mock_screen:
        # Mock Ticker for sector enrichment
        with patch("yfinance.Ticker") as mock_ticker_cls:
            mock_ticker = MagicMock()
            mock_ticker_cls.return_value = mock_ticker
            # Mock info property
            # Since we use asyncio.to_thread(lambda: ticker.info), we need info to be a property returning dict
            type(mock_ticker).info = {"sector": "Technology"}

            results = await service.get_most_active(limit=2)

            assert len(results) == 2
            assert results[0]["symbol"] == "AAPL"
            assert results[0]["name"] == "Apple Inc."
            assert results[0]["sector"] == "Technology"
            assert results[1]["symbol"] == "MSFT"
            assert results[1]["name"] == "Microsoft Corp"
            assert results[1]["sector"] == "Technology"

            mock_screen.assert_called_once_with("most_actives")

@pytest.mark.asyncio
async def test_get_most_active_limit(mock_session):
    service = ScreenerService(mock_session)

    mock_quotes = [{"symbol": f"S{i}", "regularMarketVolume": 100} for i in range(10)]
    mock_screen_result = {"quotes": mock_quotes}

    with patch("yfinance.screen", return_value=mock_screen_result):
        # We don't need to mock Ticker if limit is large enough or result is filtered?
        # Actually limit logic happens after fetch.
        # But sector enrichment only happens if limit <= 20.

        # Test with limit < number of quotes
        results = await service.get_most_active(limit=5)
        assert len(results) == 5

        # Test with sector enrichment (limit <= 20)
        with patch("yfinance.Ticker") as mock_ticker_cls:
            mock_ticker = MagicMock()
            mock_ticker_cls.return_value = mock_ticker
            type(mock_ticker).info = {"sector": "TestSector"}

            results = await service.get_most_active(limit=5)
            assert results[0]["sector"] == "TestSector"

@pytest.mark.asyncio
async def test_get_most_active_no_sector_enrichment_large_limit(mock_session):
    service = ScreenerService(mock_session)

    mock_quotes = [{"symbol": f"S{i}"} for i in range(25)]
    mock_screen_result = {"quotes": mock_quotes}

    with patch("yfinance.screen", return_value=mock_screen_result):
        with patch("yfinance.Ticker") as mock_ticker_cls:
            results = await service.get_most_active(limit=25)
            assert len(results) == 25
            assert results[0]["sector"] is None
            # Ticker should not be called
            mock_ticker_cls.assert_not_called()

@pytest.mark.asyncio
async def test_get_most_active_error_handling(mock_session):
    service = ScreenerService(mock_session)

    with patch("yfinance.screen", side_effect=Exception("API Error")):
        results = await service.get_most_active()
        assert results == []
