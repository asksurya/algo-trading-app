"""
Comprehensive test suite for Broker API routes.

Tests for Alpaca account, positions, orders, and market data endpoints.
Covers both success and error scenarios with proper authentication.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import status


# ============================================================================
# Test Fixtures - Mock Data
# ============================================================================

@pytest.fixture
def mock_alpaca_account():
    """Mock Alpaca account data."""
    return {
        "id": "account-123",
        "account_number": "123456789",
        "status": "ACTIVE",
        "currency": "USD",
        "cash": 100000.0,
        "portfolio_value": 150000.0,
        "buying_power": 200000.0,
        "equity": 150000.0,
        "long_market_value": 50000.0,
        "short_market_value": 0.0,
        "initial_margin": 25000.0,
        "maintenance_margin": 15000.0,
        "daytrade_count": 0,
        "daytrading_buying_power": 400000.0,
        "pattern_day_trader": False,
        "trading_blocked": False,
        "transfers_blocked": False,
    }


@pytest.fixture
def mock_alpaca_position():
    """Mock Alpaca position data."""
    return {
        "symbol": "AAPL",
        "qty": 10.0,
        "avg_entry_price": 150.0,
        "side": "long",
        "market_value": 1550.0,
        "cost_basis": 1500.0,
        "unrealized_pl": 50.0,
        "unrealized_plpc": 0.0333,
        "current_price": 155.0,
        "lastday_price": 150.0,
        "change_today": 0.0333,
    }


@pytest.fixture
def mock_alpaca_order():
    """Mock Alpaca order data."""
    return {
        "id": "order-123",
        "client_order_id": "client-order-123",
        "symbol": "AAPL",
        "qty": 10.0,
        "filled_qty": 10.0,
        "order_type": "market",
        "side": "buy",
        "status": "filled",
        "time_in_force": "day",
        "created_at": "2025-01-20T10:00:00Z",
        "filled_at": "2025-01-20T10:00:01Z",
    }


@pytest.fixture
def mock_market_quote():
    """Mock market quote data."""
    return {
        "symbol": "AAPL",
        "bid": 155.0,
        "ask": 155.05,
        "bid_size": 1000,
        "ask_size": 500,
        "last": 155.025,
        "last_size": 100,
        "timestamp": "2025-01-20T15:30:00Z",
    }


@pytest.fixture
def mock_market_bar():
    """Mock market bar (OHLCV) data."""
    return {
        "symbol": "AAPL",
        "timestamp": "2025-01-20T15:30:00Z",
        "open": 154.0,
        "high": 156.0,
        "low": 153.5,
        "close": 155.0,
        "volume": 50000,
        "vwap": 154.8,
        "trade_count": 1234,
    }


# ============================================================================
# Test: GET /broker/account
# ============================================================================

@pytest.mark.asyncio
async def test_get_account(client, auth_headers, mock_alpaca_account):
    """Test getting account information successfully."""
    with patch("app.api.v1.broker.get_alpaca_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_account = AsyncMock(return_value=mock_alpaca_account)
        mock_get_client.return_value = mock_client

        response = await client.get("/api/v1/broker/account", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == "account-123"
        assert data["data"]["cash"] == 100000.0
        assert data["data"]["portfolio_value"] == 150000.0
        mock_client.get_account.assert_called_once_with(use_cache=True)


@pytest.mark.asyncio
async def test_get_account_with_cache_disabled(client, auth_headers, mock_alpaca_account):
    """Test getting account information with cache disabled."""
    with patch("app.api.v1.broker.get_alpaca_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_account = AsyncMock(return_value=mock_alpaca_account)
        mock_get_client.return_value = mock_client

        response = await client.get(
            "/api/v1/broker/account?use_cache=false",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        mock_client.get_account.assert_called_once_with(use_cache=False)


@pytest.mark.asyncio
async def test_get_account_unauthorized(client):
    """Test getting account information without authentication."""
    response = await client.get("/api/v1/broker/account")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_account_alpaca_error(client, auth_headers):
    """Test handling of Alpaca API errors."""
    from app.integrations.alpaca_client import AlpacaAPIError

    with patch("app.api.v1.broker.get_alpaca_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_account = AsyncMock(
            side_effect=AlpacaAPIError(
                "API rate limit exceeded",
                status_code=429
            )
        )
        mock_get_client.return_value = mock_client

        response = await client.get("/api/v1/broker/account", headers=auth_headers)

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        data = response.json()
        assert data["detail"]["error"] == "alpaca_api_error"
        assert "rate limit" in data["detail"]["message"].lower()


# ============================================================================
# Test: GET /broker/positions
# ============================================================================

@pytest.mark.asyncio
async def test_get_positions(client, auth_headers, mock_alpaca_position):
    """Test getting open positions successfully."""
    mock_positions = [mock_alpaca_position, {**mock_alpaca_position, "symbol": "MSFT"}]

    with patch("app.api.v1.broker.get_alpaca_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_positions = AsyncMock(return_value=mock_positions)
        mock_get_client.return_value = mock_client

        response = await client.get("/api/v1/broker/positions", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert len(data["data"]) == 2
        assert data["data"][0]["symbol"] == "AAPL"
        assert data["data"][1]["symbol"] == "MSFT"
        mock_client.get_positions.assert_called_once_with(use_cache=True)


@pytest.mark.asyncio
async def test_get_positions_empty(client, auth_headers):
    """Test getting positions when none exist."""
    with patch("app.api.v1.broker.get_alpaca_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_positions = AsyncMock(return_value=[])
        mock_get_client.return_value = mock_client

        response = await client.get("/api/v1/broker/positions", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 0
        assert data["data"] == []


@pytest.mark.asyncio
async def test_get_positions_unauthorized(client):
    """Test getting positions without authentication."""
    response = await client.get("/api/v1/broker/positions")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_positions_with_cache_disabled(client, auth_headers, mock_alpaca_position):
    """Test getting positions with caching disabled."""
    with patch("app.api.v1.broker.get_alpaca_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_positions = AsyncMock(return_value=[mock_alpaca_position])
        mock_get_client.return_value = mock_client

        response = await client.get(
            "/api/v1/broker/positions?use_cache=false",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        mock_client.get_positions.assert_called_once_with(use_cache=False)


# ============================================================================
# Test: GET /broker/orders
# ============================================================================

@pytest.mark.asyncio
async def test_get_orders(client, auth_headers, mock_alpaca_order):
    """Test getting orders successfully."""
    mock_orders = [mock_alpaca_order, {**mock_alpaca_order, "id": "order-124"}]

    with patch("app.api.v1.broker.get_alpaca_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_orders = AsyncMock(return_value=mock_orders)
        mock_get_client.return_value = mock_client

        response = await client.get("/api/v1/broker/orders", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert len(data["data"]) == 2
        assert data["filter"]["status"] == "all"
        assert data["filter"]["limit"] == 100
        mock_client.get_orders.assert_called_once_with(
            status=None,
            limit=100,
            use_cache=False
        )


@pytest.mark.asyncio
async def test_get_orders_with_status_filter(client, auth_headers, mock_alpaca_order):
    """Test getting orders with status filter."""
    open_orders = [{**mock_alpaca_order, "status": "open"}]

    with patch("app.api.v1.broker.get_alpaca_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_orders = AsyncMock(return_value=open_orders)
        mock_get_client.return_value = mock_client

        response = await client.get(
            "/api/v1/broker/orders?status_filter=open",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["filter"]["status"] == "open"
        mock_client.get_orders.assert_called_once_with(
            status="open",
            limit=100,
            use_cache=False
        )


@pytest.mark.asyncio
async def test_get_orders_with_limit(client, auth_headers, mock_alpaca_order):
    """Test getting orders with custom limit."""
    with patch("app.api.v1.broker.get_alpaca_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_orders = AsyncMock(return_value=[mock_alpaca_order])
        mock_get_client.return_value = mock_client

        response = await client.get(
            "/api/v1/broker/orders?limit=50",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["filter"]["limit"] == 50
        mock_client.get_orders.assert_called_once_with(
            status=None,
            limit=50,
            use_cache=False
        )


@pytest.mark.asyncio
async def test_get_orders_invalid_status(client, auth_headers):
    """Test getting orders with invalid status filter."""
    response = await client.get(
        "/api/v1/broker/orders?status_filter=invalid",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"]["error"] == "invalid_parameter"
    assert "Status must be one of" in data["detail"]["message"]


@pytest.mark.asyncio
async def test_get_orders_invalid_limit(client, auth_headers):
    """Test getting orders with invalid limit."""
    response = await client.get(
        "/api/v1/broker/orders?limit=1000",  # > 500 max
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_orders_unauthorized(client):
    """Test getting orders without authentication."""
    response = await client.get("/api/v1/broker/orders")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# Test: POST /broker/cache/invalidate
# ============================================================================

@pytest.mark.asyncio
async def test_invalidate_cache(client, auth_headers):
    """Test invalidating cache successfully."""
    with patch("app.api.v1.broker.get_alpaca_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.invalidate_cache = AsyncMock(return_value=None)
        mock_get_client.return_value = mock_client

        response = await client.post(
            "/api/v1/broker/cache/invalidate",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_client.invalidate_cache.assert_called_once_with(pattern="alpaca:*")


@pytest.mark.asyncio
async def test_invalidate_cache_custom_pattern(client, auth_headers):
    """Test invalidating cache with custom pattern."""
    with patch("app.api.v1.broker.get_alpaca_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.invalidate_cache = AsyncMock(return_value=None)
        mock_get_client.return_value = mock_client

        response = await client.post(
            "/api/v1/broker/cache/invalidate?pattern=alpaca:account:*",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_client.invalidate_cache.assert_called_once_with(pattern="alpaca:account:*")


@pytest.mark.asyncio
async def test_invalidate_cache_unauthorized(client):
    """Test invalidating cache without authentication."""
    response = await client.post("/api/v1/broker/cache/invalidate")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_invalidate_cache_error(client, auth_headers):
    """Test handling cache invalidation error."""
    with patch("app.api.v1.broker.get_alpaca_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.invalidate_cache = AsyncMock(
            side_effect=Exception("Redis connection failed")
        )
        mock_get_client.return_value = mock_client

        response = await client.post(
            "/api/v1/broker/cache/invalidate",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert data["detail"]["error"] == "internal_error"


# ============================================================================
# Test: GET /broker/market/quote/{symbol}
# ============================================================================

@pytest.mark.asyncio
async def test_get_quote(client, auth_headers, mock_market_quote):
    """Test getting latest quote for a symbol."""
    with patch("app.api.v1.broker.get_market_data_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_latest_quote = AsyncMock(return_value=mock_market_quote)
        mock_get_client.return_value = mock_client

        response = await client.get(
            "/api/v1/broker/market/quote/AAPL",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["symbol"] == "AAPL"
        assert data["data"]["bid"] == 155.0
        assert data["data"]["ask"] == 155.05
        mock_client.get_latest_quote.assert_called_once_with("AAPL", use_cache=True)


@pytest.mark.asyncio
async def test_get_quote_lowercase_symbol(client, auth_headers, mock_market_quote):
    """Test getting quote with lowercase symbol (should be converted to uppercase)."""
    with patch("app.api.v1.broker.get_market_data_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_latest_quote = AsyncMock(return_value=mock_market_quote)
        mock_get_client.return_value = mock_client

        response = await client.get(
            "/api/v1/broker/market/quote/aapl",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        mock_client.get_latest_quote.assert_called_once_with("AAPL", use_cache=True)


@pytest.mark.asyncio
async def test_get_quote_with_cache_disabled(client, auth_headers, mock_market_quote):
    """Test getting quote with cache disabled."""
    with patch("app.api.v1.broker.get_market_data_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_latest_quote = AsyncMock(return_value=mock_market_quote)
        mock_get_client.return_value = mock_client

        response = await client.get(
            "/api/v1/broker/market/quote/AAPL?use_cache=false",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        mock_client.get_latest_quote.assert_called_once_with("AAPL", use_cache=False)


@pytest.mark.asyncio
async def test_get_quote_unauthorized(client):
    """Test getting quote without authentication."""
    response = await client.get("/api/v1/broker/market/quote/AAPL")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_quote_market_data_error(client, auth_headers):
    """Test handling of market data errors."""
    from app.integrations.market_data import MarketDataError

    with patch("app.api.v1.broker.get_market_data_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_latest_quote = AsyncMock(
            side_effect=MarketDataError("Symbol not found", status_code=404)
        )
        mock_get_client.return_value = mock_client

        response = await client.get(
            "/api/v1/broker/market/quote/INVALID",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"]["error"] == "market_data_error"


# ============================================================================
# Test: GET /broker/market/bars/{symbol}
# ============================================================================

@pytest.mark.asyncio
async def test_get_bars(client, auth_headers, mock_market_bar):
    """Test getting historical bars (OHLCV) data."""
    mock_bars = [mock_market_bar]

    with patch("app.api.v1.broker.get_market_data_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_bars = AsyncMock(return_value=mock_bars)
        mock_get_client.return_value = mock_client

        response = await client.get(
            "/api/v1/broker/market/bars/AAPL",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["symbol"] == "AAPL"
        assert data["data"]["count"] == 1
        assert data["data"]["timeframe"] == "1Day"
        assert data["data"]["bars"][0]["close"] == 155.0
        mock_client.get_bars.assert_called_once_with(
            "AAPL",
            timeframe="1Day",
            limit=100,
            use_cache=True
        )


@pytest.mark.asyncio
async def test_get_bars_custom_timeframe(client, auth_headers, mock_market_bar):
    """Test getting bars with custom timeframe."""
    with patch("app.api.v1.broker.get_market_data_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_bars = AsyncMock(return_value=[mock_market_bar])
        mock_get_client.return_value = mock_client

        response = await client.get(
            "/api/v1/broker/market/bars/AAPL?timeframe=15Min",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["timeframe"] == "15Min"
        mock_client.get_bars.assert_called_once_with(
            "AAPL",
            timeframe="15Min",
            limit=100,
            use_cache=True
        )


@pytest.mark.asyncio
async def test_get_bars_custom_limit(client, auth_headers, mock_market_bar):
    """Test getting bars with custom limit."""
    with patch("app.api.v1.broker.get_market_data_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_bars = AsyncMock(return_value=[mock_market_bar])
        mock_get_client.return_value = mock_client

        response = await client.get(
            "/api/v1/broker/market/bars/AAPL?limit=250",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        mock_client.get_bars.assert_called_once_with(
            "AAPL",
            timeframe="1Day",
            limit=250,
            use_cache=True
        )


@pytest.mark.asyncio
async def test_get_bars_invalid_limit_too_high(client, auth_headers):
    """Test getting bars with limit exceeding maximum."""
    response = await client.get(
        "/api/v1/broker/market/bars/AAPL?limit=20000",  # > 10000 max
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_bars_invalid_limit_too_low(client, auth_headers):
    """Test getting bars with limit below minimum."""
    response = await client.get(
        "/api/v1/broker/market/bars/AAPL?limit=0",  # < 1 min
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_bars_lowercase_symbol(client, auth_headers, mock_market_bar):
    """Test getting bars with lowercase symbol."""
    with patch("app.api.v1.broker.get_market_data_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_bars = AsyncMock(return_value=[mock_market_bar])
        mock_get_client.return_value = mock_client

        response = await client.get(
            "/api/v1/broker/market/bars/aapl",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        mock_client.get_bars.assert_called_once_with(
            "AAPL",
            timeframe="1Day",
            limit=100,
            use_cache=True
        )


@pytest.mark.asyncio
async def test_get_bars_unauthorized(client):
    """Test getting bars without authentication."""
    response = await client.get("/api/v1/broker/market/bars/AAPL")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_bars_market_data_error(client, auth_headers):
    """Test handling market data errors for bars."""
    from app.integrations.market_data import MarketDataError

    with patch("app.api.v1.broker.get_market_data_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_bars = AsyncMock(
            side_effect=MarketDataError("API limit exceeded", status_code=429)
        )
        mock_get_client.return_value = mock_client

        response = await client.get(
            "/api/v1/broker/market/bars/AAPL",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        data = response.json()
        assert data["detail"]["error"] == "market_data_error"


# ============================================================================
# Test: GET /broker/stream/status
# ============================================================================

@pytest.mark.asyncio
async def test_get_stream_status(client, auth_headers):
    """Test getting WebSocket stream status."""
    with patch("app.api.v1.broker.get_stream_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.is_connected = True
        mock_client.get_subscriptions = MagicMock(
            return_value={"symbols": ["AAPL", "MSFT"], "streams": ["trades", "quotes"]}
        )
        mock_get_client.return_value = mock_client

        with patch("app.api.v1.broker.manager") as mock_manager:
            mock_manager.active_connections = {"ws_1": None, "ws_2": None}

            response = await client.get(
                "/api/v1/broker/stream/status",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["connected"] is True
            assert data["data"]["active_websocket_clients"] == 2


@pytest.mark.asyncio
async def test_get_stream_status_disconnected(client, auth_headers):
    """Test getting stream status when not connected."""
    with patch("app.api.v1.broker.get_stream_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.is_connected = False
        mock_client.get_subscriptions = MagicMock(return_value={})
        mock_get_client.return_value = mock_client

        with patch("app.api.v1.broker.manager") as mock_manager:
            mock_manager.active_connections = {}

            response = await client.get(
                "/api/v1/broker/stream/status",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["data"]["connected"] is False
            assert data["data"]["active_websocket_clients"] == 0


@pytest.mark.asyncio
async def test_get_stream_status_unauthorized(client):
    """Test getting stream status without authentication."""
    response = await client.get("/api/v1/broker/stream/status")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# Test: GET /broker/market/quotes
# ============================================================================

@pytest.mark.asyncio
async def test_get_multiple_quotes(client, auth_headers, mock_market_quote):
    """Test getting multiple quotes successfully."""
    mock_quotes = [
        mock_market_quote,
        {**mock_market_quote, "symbol": "MSFT", "bid": 425.0}
    ]

    with patch("app.api.v1.broker.get_market_data_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_multi_quotes = AsyncMock(return_value=mock_quotes)
        mock_get_client.return_value = mock_client

        response = await client.get(
            "/api/v1/broker/market/quotes?symbols=AAPL,MSFT",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert len(data["data"]) == 2
        assert data["data"][0]["symbol"] == "AAPL"
        assert data["data"][1]["symbol"] == "MSFT"
        mock_client.get_multi_quotes.assert_called_once_with(["AAPL", "MSFT"])


@pytest.mark.asyncio
async def test_get_multiple_quotes_no_symbols(client, auth_headers):
    """Test getting quotes with no symbols provided."""
    response = await client.get(
        "/api/v1/broker/market/quotes?symbols=",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"]["error"] == "invalid_parameter"
    assert "No symbols provided" in data["detail"]["message"]


@pytest.mark.asyncio
async def test_get_multiple_quotes_lowercase_symbols(client, auth_headers, mock_market_quote):
    """Test getting quotes with lowercase symbols."""
    mock_quotes = [mock_market_quote]

    with patch("app.api.v1.broker.get_market_data_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_multi_quotes = AsyncMock(return_value=mock_quotes)
        mock_get_client.return_value = mock_client

        response = await client.get(
            "/api/v1/broker/market/quotes?symbols=aapl,msft",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        mock_client.get_multi_quotes.assert_called_once_with(["AAPL", "MSFT"])


@pytest.mark.asyncio
async def test_get_multiple_quotes_unauthorized(client):
    """Test getting multiple quotes without authentication."""
    response = await client.get("/api/v1/broker/market/quotes?symbols=AAPL,MSFT")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# Test: GET /broker/market/trade/{symbol}
# ============================================================================

@pytest.mark.asyncio
async def test_get_latest_trade(client, auth_headers):
    """Test getting latest trade for a symbol."""
    mock_trade = {
        "symbol": "AAPL",
        "price": 155.025,
        "size": 100,
        "timestamp": "2025-01-20T15:30:00Z",
        "exchange": "NASDAQ",
    }

    with patch("app.api.v1.broker.get_market_data_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_latest_trade = AsyncMock(return_value=mock_trade)
        mock_get_client.return_value = mock_client

        response = await client.get(
            "/api/v1/broker/market/trade/AAPL",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["symbol"] == "AAPL"
        assert data["data"]["price"] == 155.025
        mock_client.get_latest_trade.assert_called_once_with("AAPL", use_cache=True)


@pytest.mark.asyncio
async def test_get_latest_trade_unauthorized(client):
    """Test getting latest trade without authentication."""
    response = await client.get("/api/v1/broker/market/trade/AAPL")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# Test: GET /broker/market/snapshot/{symbol}
# ============================================================================

@pytest.mark.asyncio
async def test_get_market_snapshot(client, auth_headers):
    """Test getting complete market snapshot."""
    mock_snapshot = {
        "symbol": "AAPL",
        "quote": {
            "bid": 155.0,
            "ask": 155.05,
            "bid_size": 1000,
            "ask_size": 500,
        },
        "trade": {
            "price": 155.025,
            "size": 100,
        },
        "minute_bar": {
            "open": 154.5,
            "high": 155.5,
            "low": 154.25,
            "close": 155.0,
            "volume": 50000,
        },
        "daily_bar": {
            "open": 152.0,
            "high": 156.0,
            "low": 151.5,
            "close": 155.0,
            "volume": 500000,
        }
    }

    with patch("app.api.v1.broker.get_market_data_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_snapshot = AsyncMock(return_value=mock_snapshot)
        mock_get_client.return_value = mock_client

        response = await client.get(
            "/api/v1/broker/market/snapshot/AAPL",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["symbol"] == "AAPL"
        assert "quote" in data["data"]
        assert "trade" in data["data"]
        assert "minute_bar" in data["data"]
        assert "daily_bar" in data["data"]
        mock_client.get_snapshot.assert_called_once_with("AAPL", use_cache=True)


@pytest.mark.asyncio
async def test_get_market_snapshot_unauthorized(client):
    """Test getting market snapshot without authentication."""
    response = await client.get("/api/v1/broker/market/snapshot/AAPL")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
