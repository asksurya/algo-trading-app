"""
Alpaca API client wrapper with caching and rate limiting.
Provides thread-safe singleton access to Alpaca paper trading API.
"""
import logging
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from threading import Lock

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide, QueryOrderStatus
from alpaca.common.exceptions import APIError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.config import settings
from app.integrations.cache import get_cache_manager

logger = logging.getLogger(__name__)


class AlpacaAPIError(Exception):
    """Custom exception for Alpaca API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, original_error: Optional[Exception] = None):
        self.message = message
        self.status_code = status_code
        self.original_error = original_error
        super().__init__(self.message)


class RateLimiter:
    """
    Simple in-memory rate limiter for Alpaca API.
    Paper trading limit: 200 requests per minute.
    """
    
    def __init__(self, max_requests: int = 200, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: List[float] = []
        self._lock = Lock()
    
    def acquire(self) -> bool:
        """
        Check if request can be made within rate limit.
        
        Returns:
            True if request allowed, False if rate limited
        """
        with self._lock:
            now = time.time()
            # Remove requests outside the window
            self.requests = [req_time for req_time in self.requests if now - req_time < self.window_seconds]
            
            if len(self.requests) >= self.max_requests:
                return False
            
            self.requests.append(now)
            return True
    
    def wait_time(self) -> float:
        """
        Get wait time in seconds before next request is allowed.
        
        Returns:
            Seconds to wait, or 0 if request can be made immediately
        """
        with self._lock:
            if len(self.requests) < self.max_requests:
                return 0.0
            
            oldest_request = min(self.requests)
            wait_until = oldest_request + self.window_seconds
            return max(0.0, wait_until - time.time())


class AlpacaClient:
    """
    Singleton Alpaca API client with caching and rate limiting.
    Provides methods for account management, positions, and orders.
    """
    
    _instance: Optional['AlpacaClient'] = None
    _lock: Lock = Lock()
    _client: Optional[TradingClient] = None
    _rate_limiter: Optional[RateLimiter] = None
    
    def __new__(cls):
        """Thread-safe singleton implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Alpaca client (only once due to singleton)."""
        if self._client is None:
            self._initialize_client()
            self._rate_limiter = RateLimiter(max_requests=200, window_seconds=60)
    
    def _initialize_client(self):
        """Initialize Alpaca Trading Client with paper trading validation."""
        try:
            # Validate paper trading mode
            if "paper-api.alpaca.markets" not in settings.ALPACA_BASE_URL:
                raise AlpacaAPIError(
                    "SECURITY: Only paper trading API is allowed. "
                    f"Current URL: {settings.ALPACA_BASE_URL}"
                )
            
            self._client = TradingClient(
                api_key=settings.ALPACA_API_KEY,
                secret_key=settings.ALPACA_SECRET_KEY,
                paper=True,  # Enforce paper trading
                url_override=settings.ALPACA_BASE_URL,
            )
            
            logger.info("Alpaca client initialized in PAPER TRADING mode")
            
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca client: {e}")
            raise AlpacaAPIError(f"Client initialization failed: {str(e)}", original_error=e)
    
    def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        if not self._rate_limiter.acquire():
            wait_time = self._rate_limiter.wait_time()
            raise AlpacaAPIError(
                f"Rate limit exceeded. Retry after {wait_time:.1f} seconds",
                status_code=429
            )
    
    def _handle_api_error(self, error: Exception, operation: str) -> None:
        """
        Centralized error handling for Alpaca API calls.
        
        Args:
            error: The exception that occurred
            operation: Name of the operation that failed
        """
        if isinstance(error, APIError):
            status_code = getattr(error, 'status_code', None)
            message = str(error)
            
            logger.error(f"Alpaca API error in {operation}: {message} (status: {status_code})")
            
            if status_code == 401:
                raise AlpacaAPIError("Authentication failed. Check API credentials.", status_code=401, original_error=error)
            elif status_code == 403:
                raise AlpacaAPIError("Access forbidden. Check API permissions.", status_code=403, original_error=error)
            elif status_code == 429:
                raise AlpacaAPIError("Rate limit exceeded.", status_code=429, original_error=error)
            elif status_code and status_code >= 500:
                raise AlpacaAPIError(f"Alpaca server error: {message}", status_code=status_code, original_error=error)
            else:
                raise AlpacaAPIError(f"API error in {operation}: {message}", status_code=status_code, original_error=error)
        else:
            logger.error(f"Unexpected error in {operation}: {str(error)}")
            raise AlpacaAPIError(f"Unexpected error in {operation}: {str(error)}", original_error=error)
    
    def _parse_order(self, order: Any) -> Dict[str, Any]:
        """
        Parse Alpaca Order object to dictionary, including multi-leg orders.

        Args:
            order: Alpaca Order object

        Returns:
            Dictionary representation of order
        """
        order_data = {
            "id": str(order.id),
            "client_order_id": order.client_order_id,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
            "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None,
            "filled_at": order.filled_at.isoformat() if order.filled_at else None,
            "expired_at": order.expired_at.isoformat() if order.expired_at else None,
            "canceled_at": order.canceled_at.isoformat() if order.canceled_at else None,
            "failed_at": order.failed_at.isoformat() if order.failed_at else None,
            "asset_id": str(order.asset_id),
            "symbol": order.symbol,
            "asset_class": order.asset_class.value,
            "qty": float(order.qty) if order.qty else None,
            "filled_qty": float(order.filled_qty),
            "type": order.type.value,
            "side": order.side.value,
            "time_in_force": order.time_in_force.value,
            "limit_price": float(order.limit_price) if order.limit_price else None,
            "stop_price": float(order.stop_price) if order.stop_price else None,
            "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
            "status": order.status.value,
            "extended_hours": order.extended_hours,
            "legs": [],
        }

        # Handle multi-leg orders recursively
        if hasattr(order, 'legs') and order.legs:
            order_data['legs'] = [self._parse_order(leg) for leg in order.legs]

        return order_data

    @retry(
        retry=retry_if_exception_type((APIError,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def get_account(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get account information with caching.
        
        Args:
            use_cache: Whether to use cached data (default: True)
            
        Returns:
            Account information including balance, buying power, equity
            
        Raises:
            AlpacaAPIError: If API call fails
        """
        cache = get_cache_manager()
        cache_key = "alpaca:account"
        
        # Try cache first
        if use_cache:
            cached_data = await cache.get(cache_key)
            if cached_data:
                return cached_data
        
        # Check rate limit
        self._check_rate_limit()
        
        try:
            account = self._client.get_account()
            
            # Convert to dict for caching
            account_data = {
                "id": str(account.id),
                "account_number": account.account_number,
                "status": account.status.value,
                "currency": account.currency,
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "buying_power": float(account.buying_power),
                "equity": float(account.equity),
                "last_equity": float(account.last_equity),
                "long_market_value": float(account.long_market_value),
                "short_market_value": float(account.short_market_value),
                "initial_margin": float(account.initial_margin),
                "maintenance_margin": float(account.maintenance_margin),
                "daytrade_count": account.daytrade_count,
                "daytrading_buying_power": float(account.daytrading_buying_power),
                "regt_buying_power": float(account.regt_buying_power),
                "pattern_day_trader": account.pattern_day_trader,
                "trading_blocked": account.trading_blocked,
                "transfers_blocked": account.transfers_blocked,
                "account_blocked": account.account_blocked,
                "created_at": account.created_at.isoformat() if account.created_at else None,
            }
            
            # Cache for 5 seconds
            await cache.set(cache_key, account_data, ttl=5)
            
            logger.info("Successfully fetched account information")
            return account_data
            
        except Exception as e:
            self._handle_api_error(e, "get_account")
    
    @retry(
        retry=retry_if_exception_type((APIError,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def get_positions(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get all open positions with caching.
        
        Args:
            use_cache: Whether to use cached data (default: True)
            
        Returns:
            List of position dictionaries
            
        Raises:
            AlpacaAPIError: If API call fails
        """
        cache = get_cache_manager()
        cache_key = "alpaca:positions"
        
        # Try cache first
        if use_cache:
            cached_data = await cache.get(cache_key)
            if cached_data:
                return cached_data
        
        # Check rate limit
        self._check_rate_limit()
        
        try:
            positions = self._client.get_all_positions()
            
            # Convert to list of dicts for caching
            positions_data = []
            for pos in positions:
                positions_data.append({
                    "asset_id": str(pos.asset_id),
                    "symbol": pos.symbol,
                    "exchange": pos.exchange.value if pos.exchange else None,
                    "asset_class": pos.asset_class.value,
                    "qty": float(pos.qty),
                    "avg_entry_price": float(pos.avg_entry_price),
                    "side": pos.side.value,
                    "market_value": float(pos.market_value),
                    "cost_basis": float(pos.cost_basis),
                    "unrealized_pl": float(pos.unrealized_pl),
                    "unrealized_plpc": float(pos.unrealized_plpc),
                    "unrealized_intraday_pl": float(pos.unrealized_intraday_pl),
                    "unrealized_intraday_plpc": float(pos.unrealized_intraday_plpc),
                    "current_price": float(pos.current_price),
                    "lastday_price": float(pos.lastday_price),
                    "change_today": float(pos.change_today),
                })
            
            # Cache for 3 seconds
            await cache.set(cache_key, positions_data, ttl=3)
            
            logger.info(f"Successfully fetched {len(positions_data)} positions")
            return positions_data
            
        except Exception as e:
            self._handle_api_error(e, "get_positions")
    
    @retry(
        retry=retry_if_exception_type((APIError,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def get_orders(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        use_cache: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get order history with optional filtering.
        
        Args:
            status: Filter by order status (all, open, closed). Default: all
            limit: Maximum number of orders to return (max: 500)
            use_cache: Whether to use cached data (default: False for orders)
            
        Returns:
            List of order dictionaries
            
        Raises:
            AlpacaAPIError: If API call fails
        """
        cache = get_cache_manager()
        cache_key = f"alpaca:orders:{status or 'all'}:{limit}"
        
        # Try cache first (usually disabled for orders to ensure freshness)
        if use_cache:
            cached_data = await cache.get(cache_key)
            if cached_data:
                return cached_data
        
        # Check rate limit
        self._check_rate_limit()
        
        try:
            # Build request
            request_params = GetOrdersRequest(
                limit=min(limit, 500),  # Alpaca max is 500
            )
            
            # Add status filter if provided
            if status:
                if status.lower() == "open":
                    request_params.status = QueryOrderStatus.OPEN
                elif status.lower() == "closed":
                    request_params.status = QueryOrderStatus.CLOSED
                # "all" doesn't need a filter
            
            orders = self._client.get_orders(filter=request_params)
            
            # Convert to list of dicts
            orders_data = [self._parse_order(order) for order in orders]
            
            # Cache for 10 seconds if requested
            if use_cache:
                await cache.set(cache_key, orders_data, ttl=10)
            
            logger.info(f"Successfully fetched {len(orders_data)} orders")
            return orders_data
            
        except Exception as e:
            self._handle_api_error(e, "get_orders")
    
    async def invalidate_cache(self, pattern: str = "alpaca:*"):
        """
        Invalidate cached data.
        
        Args:
            pattern: Cache key pattern to invalidate (default: all alpaca data)
        """
        cache = get_cache_manager()
        await cache.clear_pattern(pattern)
        logger.info(f"Cache invalidated for pattern: {pattern}")


# Singleton instance getter
_alpaca_client: Optional[AlpacaClient] = None


def get_alpaca_client() -> AlpacaClient:
    """
    Get or create singleton Alpaca client instance.
    
    Returns:
        AlpacaClient instance
    """
    global _alpaca_client
    if _alpaca_client is None:
        _alpaca_client = AlpacaClient()
    return _alpaca_client