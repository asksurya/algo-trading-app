"""
WebSocket client for real-time market data streaming from Alpaca.
Handles connection lifecycle, subscriptions, and data distribution.
"""
import asyncio
import logging
from typing import Optional, Set, Callable, Dict, Any, List
from enum import Enum

from alpaca.data.live import StockDataStream
from alpaca.data.models import Bar, Quote, Trade

from app.core.config import settings

logger = logging.getLogger(__name__)


class StreamType(str, Enum):
    """Types of market data streams."""
    BARS = "bars"
    QUOTES = "quotes"
    TRADES = "trades"


class AlpacaStreamClient:
    """
    WebSocket client for real-time Alpaca market data.
    Manages connections, subscriptions, and data callbacks.
    """
    
    def __init__(self):
        """Initialize stream client."""
        self._stream: Optional[StockDataStream] = None
        self._connected: bool = False
        self._subscriptions: Dict[StreamType, Set[str]] = {
            StreamType.BARS: set(),
            StreamType.QUOTES: set(),
            StreamType.TRADES: set(),
        }
        self._callbacks: Dict[StreamType, List[Callable]] = {
            StreamType.BARS: [],
            StreamType.QUOTES: [],
            StreamType.TRADES: [],
        }
        self._reconnect_attempts: int = 0
        self._max_reconnect_attempts: int = 5
        self._reconnect_delay: int = 5
    
    async def connect(self):
        """
        Establish WebSocket connection to Alpaca.
        Automatically reconnects on failure.
        """
        if self._connected:
            logger.warning("Stream already connected")
            return
        
        try:
            # Initialize stream client
            self._stream = StockDataStream(
                api_key=settings.ALPACA_API_KEY,
                secret_key=settings.ALPACA_SECRET_KEY,
                url_override=None,  # Use default for data stream
            )
            
            # Register internal handlers
            self._stream._handlers["bars"] = self._handle_bar
            self._stream._handlers["quotes"] = self._handle_quote
            self._stream._handlers["trades"] = self._handle_trade
            
            # Start the stream in background
            asyncio.create_task(self._run_stream())
            
            self._connected = True
            self._reconnect_attempts = 0
            logger.info("Alpaca WebSocket stream connected")
            
        except Exception as e:
            logger.error(f"Failed to connect to Alpaca stream: {e}")
            await self._handle_reconnect()
    
    async def _run_stream(self):
        """Run the stream (internal method)."""
        try:
            await self._stream._run_forever()
        except Exception as e:
            logger.error(f"Stream error: {e}")
            self._connected = False
            await self._handle_reconnect()
    
    async def _handle_reconnect(self):
        """Handle automatic reconnection with exponential backoff."""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.error(f"Max reconnection attempts ({self._max_reconnect_attempts}) reached")
            return
        
        self._reconnect_attempts += 1
        delay = self._reconnect_delay * (2 ** (self._reconnect_attempts - 1))
        
        logger.info(f"Reconnecting in {delay} seconds (attempt {self._reconnect_attempts}/{self._max_reconnect_attempts})")
        await asyncio.sleep(delay)
        
        await self.connect()
    
    async def disconnect(self):
        """Close WebSocket connection."""
        if not self._connected or not self._stream:
            return
        
        try:
            await self._stream.stop_ws()
            self._connected = False
            logger.info("Alpaca WebSocket stream disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting stream: {e}")
    
    def register_callback(self, stream_type: StreamType, callback: Callable):
        """
        Register a callback for a specific stream type.
        
        Args:
            stream_type: Type of stream (bars, quotes, trades)
            callback: Async callback function to handle data
        """
        if callback not in self._callbacks[stream_type]:
            self._callbacks[stream_type].append(callback)
            logger.debug(f"Registered callback for {stream_type}")
    
    def unregister_callback(self, stream_type: StreamType, callback: Callable):
        """
        Unregister a callback.
        
        Args:
            stream_type: Type of stream
            callback: Callback function to remove
        """
        if callback in self._callbacks[stream_type]:
            self._callbacks[stream_type].remove(callback)
            logger.debug(f"Unregistered callback for {stream_type}")
    
    async def subscribe_bars(self, symbols: List[str]):
        """
        Subscribe to bar updates for symbols.
        
        Args:
            symbols: List of stock symbols
        """
        if not self._connected or not self._stream:
            logger.warning("Stream not connected, cannot subscribe to bars")
            return
        
        try:
            self._stream.subscribe_bars(self._handle_bar, *symbols)
            self._subscriptions[StreamType.BARS].update(symbols)
            logger.info(f"Subscribed to bars for: {', '.join(symbols)}")
        except Exception as e:
            logger.error(f"Failed to subscribe to bars: {e}")
    
    async def subscribe_quotes(self, symbols: List[str]):
        """
        Subscribe to quote updates for symbols.
        
        Args:
            symbols: List of stock symbols
        """
        if not self._connected or not self._stream:
            logger.warning("Stream not connected, cannot subscribe to quotes")
            return
        
        try:
            self._stream.subscribe_quotes(self._handle_quote, *symbols)
            self._subscriptions[StreamType.QUOTES].update(symbols)
            logger.info(f"Subscribed to quotes for: {', '.join(symbols)}")
        except Exception as e:
            logger.error(f"Failed to subscribe to quotes: {e}")
    
    async def subscribe_trades(self, symbols: List[str]):
        """
        Subscribe to trade updates for symbols.
        
        Args:
            symbols: List of stock symbols
        """
        if not self._connected or not self._stream:
            logger.warning("Stream not connected, cannot subscribe to trades")
            return
        
        try:
            self._stream.subscribe_trades(self._handle_trade, *symbols)
            self._subscriptions[StreamType.TRADES].update(symbols)
            logger.info(f"Subscribed to trades for: {', '.join(symbols)}")
        except Exception as e:
            logger.error(f"Failed to subscribe to trades: {e}")
    
    async def unsubscribe_bars(self, symbols: List[str]):
        """Unsubscribe from bar updates."""
        if not self._connected or not self._stream:
            return
        
        try:
            self._stream.unsubscribe_bars(*symbols)
            self._subscriptions[StreamType.BARS].difference_update(symbols)
            logger.info(f"Unsubscribed from bars for: {', '.join(symbols)}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe from bars: {e}")
    
    async def unsubscribe_quotes(self, symbols: List[str]):
        """Unsubscribe from quote updates."""
        if not self._connected or not self._stream:
            return
        
        try:
            self._stream.unsubscribe_quotes(*symbols)
            self._subscriptions[StreamType.QUOTES].difference_update(symbols)
            logger.info(f"Unsubscribed from quotes for: {', '.join(symbols)}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe from quotes: {e}")
    
    async def unsubscribe_trades(self, symbols: List[str]):
        """Unsubscribe from trade updates."""
        if not self._connected or not self._stream:
            return
        
        try:
            self._stream.unsubscribe_trades(*symbols)
            self._subscriptions[StreamType.TRADES].difference_update(symbols)
            logger.info(f"Unsubscribed from trades for: {', '.join(symbols)}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe from trades: {e}")
    
    async def _handle_bar(self, bar: Bar):
        """Internal handler for bar data."""
        try:
            bar_data = {
                "symbol": bar.symbol,
                "timestamp": bar.timestamp.isoformat(),
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": int(bar.volume),
                "trade_count": bar.trade_count,
                "vwap": float(bar.vwap) if bar.vwap else None,
            }
            
            # Call registered callbacks
            for callback in self._callbacks[StreamType.BARS]:
                await callback(bar_data)
                
        except Exception as e:
            logger.error(f"Error handling bar data: {e}")
    
    async def _handle_quote(self, quote: Quote):
        """Internal handler for quote data."""
        try:
            quote_data = {
                "symbol": quote.symbol,
                "timestamp": quote.timestamp.isoformat(),
                "bid_price": float(quote.bid_price),
                "bid_size": int(quote.bid_size),
                "ask_price": float(quote.ask_price),
                "ask_size": int(quote.ask_size),
                "conditions": quote.conditions,
            }
            
            # Call registered callbacks
            for callback in self._callbacks[StreamType.QUOTES]:
                await callback(quote_data)
                
        except Exception as e:
            logger.error(f"Error handling quote data: {e}")
    
    async def _handle_trade(self, trade: Trade):
        """Internal handler for trade data."""
        try:
            trade_data = {
                "symbol": trade.symbol,
                "timestamp": trade.timestamp.isoformat(),
                "price": float(trade.price),
                "size": int(trade.size),
                "conditions": trade.conditions,
                "id": str(trade.id),
                "exchange": trade.exchange,
            }
            
            # Call registered callbacks
            for callback in self._callbacks[StreamType.TRADES]:
                await callback(trade_data)
                
        except Exception as e:
            logger.error(f"Error handling trade data: {e}")
    
    @property
    def is_connected(self) -> bool:
        """Check if stream is connected."""
        return self._connected
    
    def get_subscriptions(self) -> Dict[str, List[str]]:
        """
        Get current subscriptions.
        
        Returns:
            Dictionary of stream types to subscribed symbols
        """
        return {
            stream_type.value: list(symbols)
            for stream_type, symbols in self._subscriptions.items()
        }


# Global stream client instance
_stream_client: Optional[AlpacaStreamClient] = None


def get_stream_client() -> AlpacaStreamClient:
    """
    Get or create singleton stream client instance.
    
    Returns:
        AlpacaStreamClient instance
    """
    global _stream_client
    if _stream_client is None:
        _stream_client = AlpacaStreamClient()
    return _stream_client