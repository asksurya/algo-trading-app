"""
Market data fetching service with caching.
Provides historical and real-time market data from Alpaca.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from abc import ABC, abstractmethod

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import (
    StockLatestQuoteRequest,
    StockLatestTradeRequest,
    StockBarsRequest,
    StockSnapshotRequest,
)
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.enums import DataFeed
from alpaca.common.exceptions import APIError

from app.core.config import settings
from app.integrations.cache import get_cache_manager

logger = logging.getLogger(__name__)


class MarketDataError(Exception):
    """Custom exception for market data errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, original_error: Optional[Exception] = None):
        self.message = message
        self.status_code = status_code
        self.original_error = original_error
        super().__init__(self.message)


class MarketDataProvider(ABC):
    """
    Abstract base class for market data providers.
    Defines interface for fetching historical and real-time market data.
    """
    
    @abstractmethod
    async def get_latest_quote(self, symbol: str) -> Dict[str, Any]:
        """Get the latest quote for a symbol."""
        pass
    
    @abstractmethod
    async def get_latest_trade(self, symbol: str) -> Dict[str, Any]:
        """Get the latest trade for a symbol."""
        pass
    
    @abstractmethod
    async def get_bars(
        self,
        symbol: str,
        timeframe: str = "1Day",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical bars (OHLCV data) for a symbol."""
        pass
    
    @abstractmethod
    async def get_snapshot(self, symbol: str) -> Dict[str, Any]:
        """Get market snapshot for a symbol."""
        pass


class AlpacaMarketData(MarketDataProvider):
    """
    Alpaca market data implementation with caching.
    """
    
    _instance: Optional['AlpacaMarketData'] = None
    _client: Optional[StockHistoricalDataClient] = None
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Alpaca market data client."""
        if self._client is None:
            try:
                self._client = StockHistoricalDataClient(
                    api_key=settings.ALPACA_API_KEY,
                    secret_key=settings.ALPACA_SECRET_KEY,
                )
                logger.info("Alpaca market data client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize market data client: {e}")
                raise MarketDataError(f"Client initialization failed: {str(e)}", original_error=e)
    
    def _handle_error(self, error: Exception, operation: str) -> None:
        """Centralized error handling."""
        if isinstance(error, APIError):
            status_code = getattr(error, 'status_code', None)
            message = str(error)
            logger.error(f"Alpaca API error in {operation}: {message} (status: {status_code})")
            raise MarketDataError(f"API error in {operation}: {message}", status_code=status_code, original_error=error)
        else:
            logger.error(f"Unexpected error in {operation}: {str(error)}")
            raise MarketDataError(f"Unexpected error in {operation}: {str(error)}", original_error=error)
    
    async def get_latest_quote(self, symbol: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get the latest quote for a symbol.
        
        Args:
            symbol: Stock symbol
            use_cache: Whether to use cached data (default: True, 1s TTL)
            
        Returns:
            Quote data with bid/ask prices and sizes
        """
        cache = get_cache_manager()
        cache_key = f"alpaca:quote:{symbol}"
        
        if use_cache:
            cached_data = await cache.get(cache_key)
            if cached_data:
                return cached_data
        
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quotes = self._client.get_stock_latest_quote(request)
            
            quote = quotes[symbol]
            quote_data = {
                "symbol": symbol,
                "bid_price": float(quote.bid_price),
                "bid_size": int(quote.bid_size),
                "ask_price": float(quote.ask_price),
                "ask_size": int(quote.ask_size),
                "timestamp": quote.timestamp.isoformat(),
                "conditions": quote.conditions,
                "tape": quote.tape,
            }
            
            await cache.set(cache_key, quote_data, ttl=1)
            logger.info(f"Fetched latest quote for {symbol}")
            return quote_data
            
        except Exception as e:
            self._handle_error(e, "get_latest_quote")
    
    async def get_latest_trade(self, symbol: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get the latest trade for a symbol.
        
        Args:
            symbol: Stock symbol
            use_cache: Whether to use cached data (default: True, 1s TTL)
            
        Returns:
            Trade data with price, size, and timestamp
        """
        cache = get_cache_manager()
        cache_key = f"alpaca:trade:{symbol}"
        
        if use_cache:
            cached_data = await cache.get(cache_key)
            if cached_data:
                return cached_data
        
        try:
            request = StockLatestTradeRequest(symbol_or_symbols=symbol)
            trades = self._client.get_stock_latest_trade(request)
            
            trade = trades[symbol]
            trade_data = {
                "symbol": symbol,
                "price": float(trade.price),
                "size": int(trade.size),
                "timestamp": trade.timestamp.isoformat(),
                "exchange": trade.exchange,
                "conditions": trade.conditions,
                "id": str(trade.id),
                "tape": trade.tape,
            }
            
            await cache.set(cache_key, trade_data, ttl=1)
            logger.info(f"Fetched latest trade for {symbol}")
            return trade_data
            
        except Exception as e:
            self._handle_error(e, "get_latest_trade")
    
    async def get_bars(
        self,
        symbol: str,
        timeframe: str = "1Day",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get historical bars (OHLCV data) for a symbol.
        
        Args:
            symbol: Stock symbol
            timeframe: Bar timeframe (1Min, 5Min, 15Min, 1Hour, 1Day)
            start: Start time for bars
            end: End time for bars
            limit: Maximum number of bars to return
            use_cache: Whether to use cached data (default: True, 5min TTL)
            
        Returns:
            List of bar data dictionaries
        """
        cache = get_cache_manager()
        cache_key = f"alpaca:bars:{symbol}:{timeframe}:{limit}"
        
        if use_cache and start is None and end is None:
            cached_data = await cache.get(cache_key)
            if cached_data:
                return cached_data
        
        try:
            # Parse timeframe
            tf = self._parse_timeframe(timeframe)
            
            # Set defaults for start/end if not provided
            if end is None:
                end = datetime.now(timezone.utc)
            if start is None:
                start = end - timedelta(days=30)  # Default to 30 days

            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=tf,
                start=start,
                end=end,
                limit=limit,
                feed=DataFeed.IEX,  # Use IEX feed for free tier compatibility
            )
            
            bars_dict = self._client.get_stock_bars(request)
            bars = bars_dict[symbol]
            
            bars_data = []
            for bar in bars:
                bars_data.append({
                    "symbol": symbol,
                    "timestamp": bar.timestamp.isoformat(),
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": int(bar.volume),
                    "trade_count": bar.trade_count,
                    "vwap": float(bar.vwap) if bar.vwap else None,
                })
            
            if use_cache and start is None and end is None:
                await cache.set(cache_key, bars_data, ttl=300)  # 5 minutes
            
            logger.info(f"Fetched {len(bars_data)} bars for {symbol}")
            return bars_data
            
        except Exception as e:
            self._handle_error(e, "get_bars")
    
    async def get_snapshot(self, symbol: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get market snapshot for a symbol.
        Includes latest trade, quote, minute/day bars.
        
        Args:
            symbol: Stock symbol
            use_cache: Whether to use cached data (default: True, 2s TTL)
            
        Returns:
            Market snapshot data
        """
        cache = get_cache_manager()
        cache_key = f"alpaca:snapshot:{symbol}"
        
        if use_cache:
            cached_data = await cache.get(cache_key)
            if cached_data:
                return cached_data
        
        try:
            request = StockSnapshotRequest(symbol_or_symbols=symbol)
            snapshots = self._client.get_stock_snapshot(request)
            
            snapshot = snapshots[symbol]
            
            snapshot_data = {
                "symbol": symbol,
                "latest_trade": {
                    "price": float(snapshot.latest_trade.price),
                    "size": int(snapshot.latest_trade.size),
                    "timestamp": snapshot.latest_trade.timestamp.isoformat(),
                } if snapshot.latest_trade else None,
                "latest_quote": {
                    "bid_price": float(snapshot.latest_quote.bid_price),
                    "bid_size": int(snapshot.latest_quote.bid_size),
                    "ask_price": float(snapshot.latest_quote.ask_price),
                    "ask_size": int(snapshot.latest_quote.ask_size),
                    "timestamp": snapshot.latest_quote.timestamp.isoformat(),
                } if snapshot.latest_quote else None,
                "minute_bar": {
                    "open": float(snapshot.minute_bar.open),
                    "high": float(snapshot.minute_bar.high),
                    "low": float(snapshot.minute_bar.low),
                    "close": float(snapshot.minute_bar.close),
                    "volume": int(snapshot.minute_bar.volume),
                    "timestamp": snapshot.minute_bar.timestamp.isoformat(),
                } if snapshot.minute_bar else None,
                "daily_bar": {
                    "open": float(snapshot.daily_bar.open),
                    "high": float(snapshot.daily_bar.high),
                    "low": float(snapshot.daily_bar.low),
                    "close": float(snapshot.daily_bar.close),
                    "volume": int(snapshot.daily_bar.volume),
                    "timestamp": snapshot.daily_bar.timestamp.isoformat(),
                } if snapshot.daily_bar else None,
                "prev_daily_bar": {
                    "open": float(snapshot.prev_daily_bar.open),
                    "high": float(snapshot.prev_daily_bar.high),
                    "low": float(snapshot.prev_daily_bar.low),
                    "close": float(snapshot.prev_daily_bar.close),
                    "volume": int(snapshot.prev_daily_bar.volume),
                    "timestamp": snapshot.prev_daily_bar.timestamp.isoformat(),
                } if snapshot.prev_daily_bar else None,
            }
            
            await cache.set(cache_key, snapshot_data, ttl=2)
            logger.info(f"Fetched snapshot for {symbol}")
            return snapshot_data
            
        except Exception as e:
            self._handle_error(e, "get_snapshot")
    
    def _parse_timeframe(self, timeframe: str) -> TimeFrame:
        """
        Parse timeframe string to TimeFrame object.
        
        Args:
            timeframe: Timeframe string (e.g., '1Min', '5Min', '1Hour', '1Day')
            
        Returns:
            TimeFrame object
        """
        timeframe_map = {
            "1Min": TimeFrame(1, TimeFrameUnit.Minute),
            "5Min": TimeFrame(5, TimeFrameUnit.Minute),
            "15Min": TimeFrame(15, TimeFrameUnit.Minute),
            "30Min": TimeFrame(30, TimeFrameUnit.Minute),
            "1Hour": TimeFrame(1, TimeFrameUnit.Hour),
            "4Hour": TimeFrame(4, TimeFrameUnit.Hour),
            "1Day": TimeFrame(1, TimeFrameUnit.Day),
            "1Week": TimeFrame(1, TimeFrameUnit.Week),
            "1Month": TimeFrame(1, TimeFrameUnit.Month),
        }
        
        if timeframe not in timeframe_map:
            raise MarketDataError(f"Invalid timeframe: {timeframe}. Must be one of: {', '.join(timeframe_map.keys())}")
        
        return timeframe_map[timeframe]
    
    async def get_multi_quotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Get latest quotes for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            List of quote data dictionaries
        """
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=symbols)
            quotes_dict = self._client.get_stock_latest_quote(request)
            
            quotes_data = []
            for symbol, quote in quotes_dict.items():
                quotes_data.append({
                    "symbol": symbol,
                    "bid_price": float(quote.bid_price),
                    "bid_size": int(quote.bid_size),
                    "ask_price": float(quote.ask_price),
                    "ask_size": int(quote.ask_size),
                    "timestamp": quote.timestamp.isoformat(),
                    "conditions": quote.conditions,
                    "tape": quote.tape,
                })
            
            logger.info(f"Fetched quotes for {len(quotes_data)} symbols")
            return quotes_data
            
        except Exception as e:
            self._handle_error(e, "get_multi_quotes")
    
    async def get_multi_trades(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Get latest trades for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            List of trade data dictionaries
        """
        try:
            request = StockLatestTradeRequest(symbol_or_symbols=symbols)
            trades_dict = self._client.get_stock_latest_trade(request)
            
            trades_data = []
            for symbol, trade in trades_dict.items():
                trades_data.append({
                    "symbol": symbol,
                    "price": float(trade.price),
                    "size": int(trade.size),
                    "timestamp": trade.timestamp.isoformat(),
                    "exchange": trade.exchange,
                    "conditions": trade.conditions,
                    "id": str(trade.id),
                    "tape": trade.tape,
                })
            
            logger.info(f"Fetched trades for {len(trades_data)} symbols")
            return trades_data
            
        except Exception as e:
            self._handle_error(e, "get_multi_trades")


# Global instance getter
_market_data_client: Optional[AlpacaMarketData] = None


def get_market_data_client() -> AlpacaMarketData:
    """
    Get or create singleton market data client instance.
    
    Returns:
        AlpacaMarketData instance
    """
    global _market_data_client
    if _market_data_client is None:
        _market_data_client = AlpacaMarketData()
    return _market_data_client


# Alias for backward compatibility
get_market_data_service = get_market_data_client
