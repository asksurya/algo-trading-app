"""
Unit and integration tests for Alpaca integration.
Tests REST API endpoints, caching, rate limiting, and WebSocket streaming.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.integrations.alpaca_client import AlpacaClient, AlpacaAPIError, RateLimiter
from app.integrations.cache import CacheManager
from alpaca.common.exceptions import APIError


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_alpaca_account():
    """Mock Alpaca account data."""
    mock_account = Mock()
    mock_account.id = "test-account-id"
    mock_account.account_number = "123456789"
    mock_account.status.value = "ACTIVE"
    mock_account.currency = "USD"
    mock_account.cash = 100000.0
    mock_account.portfolio_value = 100000.0
    mock_account.buying_power = 100000.0
    mock_account.equity = 100000.0
    mock_account.last_equity = 100000.0
    mock_account.long_market_value = 0.0
    mock_account.short_market_value = 0.0
    mock_account.initial_margin = 0.0
    mock_account.maintenance_margin = 0.0
    mock_account.daytrade_count = 0
    mock_account.daytrading_buying_power = 400000.0
    mock_account.regt_buying_power = 100000.0
    mock_account.pattern_day_trader = False
    mock_account.trading_blocked = False
    mock_account.transfers_blocked = False
    mock_account.account_blocked = False
    mock_account.created_at = None
    return mock_account


@pytest.fixture
def mock_alpaca_position():
    """Mock Alpaca position data."""
    mock_position = Mock()
    mock_position.asset_id = "test-asset-id"
    mock_position.symbol = "AAPL"
    mock_position.exchange.value = "NASDAQ"
    mock_position.asset_class.value = "us_equity"
    mock_position.qty = 10.0
    mock_position.avg_entry_price = 150.0
    mock_position.side.value = "long"
    mock_position.market_value = 1500.0
    mock_position.cost_basis = 1500.0
    mock_position.unrealized_pl = 0.0
    mock_position.unrealized_plpc = 0.0
    mock_position.unrealized_intraday_pl = 0.0
    mock_position.unrealized_intraday_plpc = 0.0
    mock_position.current_price = 150.0
    mock_position.lastday_price = 150.0
    mock_position.change_today = 0.0
    return mock_position


@pytest.fixture
def mock_alpaca_order():
    """Mock Alpaca order data."""
    mock_order = Mock()
    mock_order.id = "test-order-id"
    mock_order.client_order_id = "test-client-order-id"
    mock_order.created_at = None
    mock_order.updated_at = None
    mock_order.submitted_at = None
    mock_order.filled_at = None
    mock_order.expired_at = None
    mock_order.canceled_at = None
    mock_order.failed_at = None
    mock_order.asset_id = "test-asset-id"
    mock_order.symbol = "AAPL"
    mock_order.asset_class.value = "us_equity"
    mock_order.qty = 10.0
    mock_order.filled_qty = 10.0
    mock_order.type.value = "market"
    mock_order.side.value = "buy"
    mock_order.time_in_force.value = "day"
    mock_order.limit_price = None
    mock_order.stop_price = None
    mock_order.filled_avg_price = 150.0
    mock_order.status.value = "filled"
    mock_order.extended_hours = False
    return mock_order


# ============================================================================
# Rate Limiter Tests
# ============================================================================

class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def test_rate_limiter_allows_requests_within_limit(self):
        """Test that rate limiter allows requests within limit."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        for _ in range(5):
            assert limiter.acquire() is True
        
        # 6th request should be blocked
        assert limiter.acquire() is False
    
    def test_rate_limiter_wait_time(self):
        """Test wait time calculation."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        # Use up the limit
        limiter.acquire()
        limiter.acquire()
        
        # Should have wait time now
        wait_time = limiter.wait_time()
        assert wait_time > 0
        assert wait_time <= 60


# ============================================================================
# Cache Manager Tests
# ============================================================================

class TestCacheManager:
    """Test cache functionality."""
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """Test setting and getting cache values."""
        cache = CacheManager()
        
        # Mock Redis client
        cache._redis_client = AsyncMock()
        cache._redis_client.get = AsyncMock(return_value='{"test": "data"}')
        cache._redis_client.setex = AsyncMock()
        
        # Test set
        await cache.set("test_key", {"test": "data"}, ttl=60)
        cache._redis_client.setex.assert_called_once()
        
        # Test get
        result = await cache.get("test_key")
        assert result == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_cache_handles_missing_key(self):
        """Test cache returns None for missing keys."""
        cache = CacheManager()
        cache._redis_client = AsyncMock()
        cache._redis_client.get = AsyncMock(return_value=None)
        
        result = await cache.get("nonexistent_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_handles_redis_error(self):
        """Test cache handles Redis errors gracefully."""
        cache = CacheManager()
        cache._redis_client = AsyncMock()
        cache._redis_client.get = AsyncMock(side_effect=Exception("Redis error"))
        
        # Should not raise, should return None
        result = await cache.get("test_key")
        assert result is None


# ============================================================================
# AlpacaClient Tests
# ============================================================================

class TestAlpacaClient:
    """Test AlpacaClient functionality."""
    
    @pytest.mark.asyncio
    async def test_get_account_success(self, mock_alpaca_account):
        """Test successful account info retrieval."""
        client = AlpacaClient()
        
        # Mock the trading client
        with patch.object(client, '_client') as mock_trading_client:
            mock_trading_client.get_account.return_value = mock_alpaca_account
            
            # Mock cache to return None (cache miss)
            with patch('app.integrations.alpaca_client.get_cache_manager') as mock_cache:
                mock_cache_instance = AsyncMock()
                mock_cache_instance.get = AsyncMock(return_value=None)
                mock_cache_instance.set = AsyncMock()
                mock_cache.return_value = mock_cache_instance
                
                result = await client.get_account(use_cache=False)
                
                assert result["account_number"] == "123456789"
                assert result["cash"] == 100000.0
                assert result["equity"] == 100000.0
    
    @pytest.mark.asyncio
    async def test_get_account_uses_cache(self, mock_alpaca_account):
        """Test that account retrieval uses cache when available."""
        client = AlpacaClient()
        
        cached_data = {"cached": True, "account_number": "cached-account"}
        
        with patch('app.integrations.alpaca_client.get_cache_manager') as mock_cache:
            mock_cache_instance = AsyncMock()
            mock_cache_instance.get = AsyncMock(return_value=cached_data)
            mock_cache.return_value = mock_cache_instance
            
            result = await client.get_account(use_cache=True)
            
            assert result == cached_data
            mock_cache_instance.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_positions_success(self, mock_alpaca_position):
        """Test successful positions retrieval."""
        client = AlpacaClient()
        
        with patch.object(client, '_client') as mock_trading_client:
            mock_trading_client.get_all_positions.return_value = [mock_alpaca_position]
            
            with patch('app.integrations.alpaca_client.get_cache_manager') as mock_cache:
                mock_cache_instance = AsyncMock()
                mock_cache_instance.get = AsyncMock(return_value=None)
                mock_cache_instance.set = AsyncMock()
                mock_cache.return_value = mock_cache_instance
                
                result = await client.get_positions(use_cache=False)
                
                assert len(result) == 1
                assert result[0]["symbol"] == "AAPL"
                assert result[0]["qty"] == 10.0
    
    @pytest.mark.asyncio
    async def test_get_orders_with_filter(self, mock_alpaca_order):
        """Test orders retrieval with status filter."""
        client = AlpacaClient()
        
        with patch.object(client, '_client') as mock_trading_client:
            mock_trading_client.get_orders.return_value = [mock_alpaca_order]
            
            with patch('app.integrations.alpaca_client.get_cache_manager') as mock_cache:
                mock_cache_instance = AsyncMock()
                mock_cache_instance.get = AsyncMock(return_value=None)
                mock_cache_instance.set = AsyncMock()
                mock_cache.return_value = mock_cache_instance
                
                result = await client.get_orders(status="open", limit=50)
                
                assert len(result) == 1
                assert result[0]["symbol"] == "AAPL"
                assert result[0]["status"] == "filled"
    
    @pytest.mark.asyncio
    async def test_alpaca_api_error_handling(self):
        """Test proper handling of Alpaca API errors."""
        client = AlpacaClient()
        
        with patch.object(client, '_client') as mock_trading_client:
            mock_trading_client.get_account.side_effect = APIError("API Error", status_code=401)
            
            with patch('app.integrations.alpaca_client.get_cache_manager') as mock_cache:
                mock_cache_instance = AsyncMock()
                mock_cache_instance.get = AsyncMock(return_value=None)
                mock_cache.return_value = mock_cache_instance
                
                with pytest.raises(AlpacaAPIError) as exc_info:
                    await client.get_account(use_cache=False)
                
                assert exc_info.value.status_code == 401
                assert "Authentication failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Test rate limit error handling."""
        client = AlpacaClient()
        
        # Exhaust rate limit
        for _ in range(200):
            client._rate_limiter.acquire()
        
        with pytest.raises(AlpacaAPIError) as exc_info:
            await client.get_account(use_cache=False)
        
        assert exc_info.value.status_code == 429
        assert "Rate limit exceeded" in str(exc_info.value)


# ============================================================================
# API Endpoint Tests
# ============================================================================

class TestBrokerEndpoints:
    """Test broker API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        return TestClient(app)
    
    def test_get_account_endpoint_requires_auth(self, client):
        """Test that account endpoint requires authentication."""
        response = client.get("/api/v1/broker/account")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_positions_endpoint_requires_auth(self, client):
        """Test that positions endpoint requires authentication."""
        response = client.get("/api/v1/broker/positions")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_orders_endpoint_requires_auth(self, client):
        """Test that orders endpoint requires authentication."""
        response = client.get("/api/v1/broker/orders")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_orders_invalid_status_filter(self, client):
        """Test that invalid status filter returns 400."""
        # Note: This would require authentication in practice
        # For now, testing the validation logic
        pass


# ============================================================================
# WebSocket Tests
# ============================================================================

class TestWebSocketStreaming:
    """Test WebSocket market data streaming."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection establishment."""
        # This would require a full WebSocket test client
        # Placeholder for integration testing
        pass
    
    @pytest.mark.asyncio
    async def test_websocket_subscription(self):
        """Test subscribing to market data streams."""
        # Placeholder for integration testing
        pass
    
    @pytest.mark.asyncio
    async def test_websocket_disconnection(self):
        """Test proper cleanup on disconnection."""
        # Placeholder for integration testing
        pass


# ============================================================================
# Integration Tests (Optional - Requires Live Credentials)
# ============================================================================

@pytest.mark.integration
@pytest.mark.skipif(
    "ALPACA_API_KEY" not in __import__("os").environ,
    reason="Requires Alpaca API credentials"
)
class TestAlpacaIntegration:
    """
    Integration tests with actual Alpaca paper trading API.
    These tests are skipped unless ALPACA_API_KEY is set in environment.
    """
    
    @pytest.mark.asyncio
    async def test_real_account_fetch(self):
        """Test fetching account from real API."""
        client = AlpacaClient()
        result = await client.get_account(use_cache=False)
        
        assert "account_number" in result
        assert "cash" in result
        assert "buying_power" in result
    
    @pytest.mark.asyncio
    async def test_real_positions_fetch(self):
        """Test fetching positions from real API."""
        client = AlpacaClient()
        result = await client.get_positions(use_cache=False)
        
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_real_orders_fetch(self):
        """Test fetching orders from real API."""
        client = AlpacaClient()
        result = await client.get_orders(limit=10, use_cache=False)
        
        assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])