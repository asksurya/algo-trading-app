"""
Broker API endpoints for Alpaca integration.
Provides account info, positions, orders, and real-time market data streaming.
"""
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse

from app.dependencies import get_current_user
from app.models.user import User
from app.integrations.alpaca_client import get_alpaca_client, AlpacaAPIError
from app.integrations.market_data_ws import get_stream_client, StreamType

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# REST API Endpoints
# ============================================================================

@router.get("/account", response_model=Dict[str, Any])
async def get_account_info(
    use_cache: bool = Query(True, description="Use cached data"),
    current_user: User = Depends(get_current_user),
):
    """
    Get Alpaca account information.
    
    Returns account balance, buying power, equity, and other account details.
    Data is cached for 5 seconds by default.
    
    **Authentication required.**
    """
    try:
        client = get_alpaca_client()
        account_data = await client.get_account(use_cache=use_cache)
        
        return {
            "success": True,
            "data": account_data,
        }
        
    except AlpacaAPIError as e:
        logger.error(f"Alpaca API error for user {current_user.id}: {e.message}")
        
        status_code = e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": "alpaca_api_error",
                "message": e.message,
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error getting account for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to fetch account information",
            }
        )


@router.get("/positions", response_model=Dict[str, Any])
async def get_positions(
    use_cache: bool = Query(True, description="Use cached data"),
    current_user: User = Depends(get_current_user),
):
    """
    Get all open positions.
    
    Returns list of current positions with unrealized P&L.
    Data is cached for 3 seconds by default.
    
    **Authentication required.**
    """
    try:
        client = get_alpaca_client()
        positions_data = await client.get_positions(use_cache=use_cache)
        
        return {
            "success": True,
            "data": positions_data,
            "count": len(positions_data),
        }
        
    except AlpacaAPIError as e:
        logger.error(f"Alpaca API error for user {current_user.id}: {e.message}")
        
        status_code = e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": "alpaca_api_error",
                "message": e.message,
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error getting positions for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to fetch positions",
            }
        )


@router.get("/orders", response_model=Dict[str, Any])
async def get_orders(
    status_filter: Optional[str] = Query(None, description="Filter by status: all, open, closed"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of orders to return"),
    use_cache: bool = Query(False, description="Use cached data (not recommended for orders)"),
    current_user: User = Depends(get_current_user),
):
    """
    Get order history with optional filtering.
    
    Returns list of orders with their details and status.
    By default, returns all orders (not cached).
    
    **Query Parameters:**
    - status: Filter by order status (all, open, closed)
    - limit: Maximum number of orders to return (1-500)
    - use_cache: Whether to use cached data (default: false)
    
    **Authentication required.**
    """
    try:
        # Validate status filter
        if status_filter and status_filter.lower() not in ["all", "open", "closed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_parameter",
                    "message": "Status must be one of: all, open, closed",
                }
            )
        
        client = get_alpaca_client()
        orders_data = await client.get_orders(
            status=status_filter,
            limit=limit,
            use_cache=use_cache
        )
        
        return {
            "success": True,
            "data": orders_data,
            "count": len(orders_data),
            "filter": {
                "status": status_filter or "all",
                "limit": limit,
            }
        }
        
    except AlpacaAPIError as e:
        logger.error(f"Alpaca API error for user {current_user.id}: {e.message}")
        
        status_code = e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": "alpaca_api_error",
                "message": e.message,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting orders for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to fetch orders",
            }
        )


@router.post("/cache/invalidate", status_code=status.HTTP_204_NO_CONTENT)
async def invalidate_cache(
    pattern: Optional[str] = Query("alpaca:*", description="Cache key pattern to invalidate"),
    current_user: User = Depends(get_current_user),
):
    """
    Invalidate cached Alpaca data.
    
    Useful when you want fresh data immediately instead of waiting for cache expiration.
    
    **Query Parameters:**
    - pattern: Cache key pattern (default: alpaca:* for all Alpaca data)
    
    **Authentication required.**
    """
    try:
        client = get_alpaca_client()
        await client.invalidate_cache(pattern=pattern)
        logger.info(f"Cache invalidated by user {current_user.id} for pattern: {pattern}")
        return None
        
    except Exception as e:
        logger.error(f"Error invalidating cache for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to invalidate cache",
            }
        )


# ============================================================================
# WebSocket Endpoints for Real-Time Market Data
# ============================================================================

class ConnectionManager:
    """Manages WebSocket connections for market data streaming."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and track WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client {client_id} connected")
    
    def disconnect(self, client_id: str):
        """Remove WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket client {client_id} disconnected")
    
    async def send_data(self, client_id: str, data: Dict[str, Any]):
        """Send data to specific client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(data)
            except Exception as e:
                logger.error(f"Error sending data to client {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, data: Dict[str, Any]):
        """Broadcast data to all connected clients."""
        disconnected = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {e}")
                disconnected.append(client_id)
        
        for client_id in disconnected:
            self.disconnect(client_id)


manager = ConnectionManager()


@router.websocket("/stream")
async def market_data_stream(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
    symbols: str = Query(..., description="Comma-separated list of symbols (e.g., AAPL,MSFT,GOOGL)"),
    streams: str = Query("trades,quotes", description="Comma-separated list of stream types: bars, quotes, trades"),
):
    """
    WebSocket endpoint for real-time market data streaming with authentication.
    
    **Query Parameters:**
    - token: JWT authentication token (required)
    - symbols: Comma-separated list of stock symbols to subscribe to
    - streams: Types of data to stream (bars, quotes, trades)
    
    **Example:**
    ```
    ws://localhost:8000/api/v1/broker/stream?token=YOUR_JWT&symbols=AAPL,MSFT&streams=trades,quotes
    ```
    
    **Message Format:**
    ```json
    {
      "type": "trade",
      "data": {
        "symbol": "AAPL",
        "price": 150.25,
        "size": 100,
        "timestamp": "2025-01-20T14:30:00Z"
      }
    }
    ```
    
    **Authentication:** JWT token is required in query parameter.
    """
    from app.core.security import verify_websocket_token
    
    # Verify authentication before accepting connection
    user = await verify_websocket_token(token)
    if not user:
        await websocket.close(code=1008, reason="Authentication failed")
        logger.warning(f"WebSocket authentication failed for token: {token[:10]}...")
        return
    
    client_id = f"ws_{user.id}_{id(websocket)}"
    logger.info(f"WebSocket authenticated for user {user.id}")
    
    try:
        # Accept connection
        await manager.connect(websocket, client_id)
        
        # Parse symbols and stream types
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        stream_types = [s.strip().lower() for s in streams.split(",") if s.strip()]
        
        if not symbol_list:
            await websocket.send_json({
                "type": "error",
                "message": "No symbols provided"
            })
            return
        
        # Validate stream types
        valid_streams = {"bars", "quotes", "trades"}
        invalid_streams = set(stream_types) - valid_streams
        if invalid_streams:
            await websocket.send_json({
                "type": "error",
                "message": f"Invalid stream types: {', '.join(invalid_streams)}"
            })
            return
        
        # Get stream client
        stream_client = get_stream_client()
        
        # Connect to Alpaca stream if not already connected
        if not stream_client.is_connected:
            await stream_client.connect()
        
        # Define callback for this WebSocket client
        async def send_to_client(data: Dict[str, Any]):
            await manager.send_data(client_id, data)
        
        # Subscribe to requested streams
        if "bars" in stream_types:
            stream_client.register_callback(StreamType.BARS, send_to_client)
            await stream_client.subscribe_bars(symbol_list)
        
        if "quotes" in stream_types:
            stream_client.register_callback(StreamType.QUOTES, send_to_client)
            await stream_client.subscribe_quotes(symbol_list)
        
        if "trades" in stream_types:
            stream_client.register_callback(StreamType.TRADES, send_to_client)
            await stream_client.subscribe_trades(symbol_list)
        
        # Send confirmation
        await websocket.send_json({
            "type": "subscribed",
            "symbols": symbol_list,
            "streams": stream_types,
            "message": "Successfully subscribed to market data"
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive messages from client (e.g., subscribe/unsubscribe requests)
                message = await websocket.receive_json()
                
                # Handle client commands
                if message.get("action") == "subscribe":
                    new_symbols = message.get("symbols", [])
                    if "bars" in stream_types:
                        await stream_client.subscribe_bars(new_symbols)
                    if "quotes" in stream_types:
                        await stream_client.subscribe_quotes(new_symbols)
                    if "trades" in stream_types:
                        await stream_client.subscribe_trades(new_symbols)
                    
                    await websocket.send_json({
                        "type": "subscribed",
                        "symbols": new_symbols
                    })
                
                elif message.get("action") == "unsubscribe":
                    remove_symbols = message.get("symbols", [])
                    if "bars" in stream_types:
                        await stream_client.unsubscribe_bars(remove_symbols)
                    if "quotes" in stream_types:
                        await stream_client.unsubscribe_quotes(remove_symbols)
                    if "trades" in stream_types:
                        await stream_client.unsubscribe_trades(remove_symbols)
                    
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "symbols": remove_symbols
                    })
                
                elif message.get("action") == "ping":
                    await websocket.send_json({"type": "pong"})
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        # Cleanup: unregister callbacks and unsubscribe
        stream_client = get_stream_client()
        
        # Unregister callbacks
        if "bars" in stream_types:
            stream_client.unregister_callback(StreamType.BARS, send_to_client)
            await stream_client.unsubscribe_bars(symbol_list)
        if "quotes" in stream_types:
            stream_client.unregister_callback(StreamType.QUOTES, send_to_client)
            await stream_client.unsubscribe_quotes(symbol_list)
        if "trades" in stream_types:
            stream_client.unregister_callback(StreamType.TRADES, send_to_client)
            await stream_client.unsubscribe_trades(symbol_list)
        
        manager.disconnect(client_id)


@router.get("/stream/status", response_model=Dict[str, Any])
async def get_stream_status(
    current_user: User = Depends(get_current_user),
):
    """
    Get WebSocket stream connection status and subscriptions.
    
    **Authentication required.**
    """
    try:
        stream_client = get_stream_client()
        
        return {
            "success": True,
            "data": {
                "connected": stream_client.is_connected,
                "subscriptions": stream_client.get_subscriptions(),
                "active_websocket_clients": len(manager.active_connections),
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting stream status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to get stream status",
            }
        )


# ============================================================================
# Market Data Endpoints
# ============================================================================

from app.integrations.market_data import get_market_data_client, MarketDataError
from app.schemas.market_data import (
    QuoteResponse,
    TradeResponse,
    BarsResponse,
    SnapshotResponse,
    MultiQuoteResponse,
)


@router.get("/market/quote/{symbol}", response_model=Dict[str, Any])
async def get_latest_quote(
    symbol: str,
    use_cache: bool = Query(True, description="Use cached data"),
    current_user: User = Depends(get_current_user),
):
    """
    Get latest quote for a symbol.
    
    Returns bid/ask prices with sizes.
    Cached for 1 second by default.
    
    **Authentication required.**
    """
    try:
        client = get_market_data_client()
        quote_data = await client.get_latest_quote(symbol.upper(), use_cache=use_cache)
        
        return {
            "success": True,
            "data": quote_data,
        }
        
    except MarketDataError as e:
        logger.error(f"Market data error for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "market_data_error",
                "message": e.message,
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error getting quote for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to fetch quote",
            }
        )


@router.get("/market/quotes", response_model=Dict[str, Any])
async def get_multiple_quotes(
    symbols: str = Query(..., description="Comma-separated symbols (e.g., AAPL,MSFT,GOOGL)"),
    current_user: User = Depends(get_current_user),
):
    """
    Get latest quotes for multiple symbols.
    
    **Query Parameters:**
    - symbols: Comma-separated list of symbols
    
    **Authentication required.**
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        
        if not symbol_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_parameter",
                    "message": "No symbols provided",
                }
            )
        
        client = get_market_data_client()
        quotes_data = await client.get_multi_quotes(symbol_list)
        
        return {
            "success": True,
            "data": quotes_data,
            "count": len(quotes_data),
        }
        
    except MarketDataError as e:
        logger.error(f"Market data error for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "market_data_error",
                "message": e.message,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting quotes for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to fetch quotes",
            }
        )


@router.get("/market/trade/{symbol}", response_model=Dict[str, Any])
async def get_latest_trade(
    symbol: str,
    use_cache: bool = Query(True, description="Use cached data"),
    current_user: User = Depends(get_current_user),
):
    """
    Get latest trade for a symbol.
    
    Returns most recent trade with price, size, and timestamp.
    Cached for 1 second by default.
    
    **Authentication required.**
    """
    try:
        client = get_market_data_client()
        trade_data = await client.get_latest_trade(symbol.upper(), use_cache=use_cache)
        
        return {
            "success": True,
            "data": trade_data,
        }
        
    except MarketDataError as e:
        logger.error(f"Market data error for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "market_data_error",
                "message": e.message,
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error getting trade for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to fetch trade",
            }
        )


@router.get("/market/bars/{symbol}", response_model=Dict[str, Any])
async def get_historical_bars(
    symbol: str,
    timeframe: str = Query("1Day", description="Timeframe (1Min, 5Min, 15Min, 1Hour, 1Day)"),
    limit: int = Query(100, ge=1, le=10000, description="Maximum number of bars"),
    use_cache: bool = Query(True, description="Use cached data"),
    current_user: User = Depends(get_current_user),
):
    """
    Get historical bars (OHLCV data) for a symbol.
    
    **Query Parameters:**
    - timeframe: Bar timeframe (1Min, 5Min, 15Min, 1Hour, 1Day)
    - limit: Maximum bars to return (1-10000)
    - use_cache: Use cached data (5 minute TTL)
    
    **Authentication required.**
    """
    try:
        client = get_market_data_client()
        bars_data = await client.get_bars(
            symbol.upper(),
            timeframe=timeframe,
            limit=limit,
            use_cache=use_cache
        )
        
        return {
            "success": True,
            "data": {
                "symbol": symbol.upper(),
                "bars": bars_data,
                "count": len(bars_data),
                "timeframe": timeframe,
            }
        }
        
    except MarketDataError as e:
        logger.error(f"Market data error for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "market_data_error",
                "message": e.message,
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error getting bars for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to fetch bars",
            }
        )


@router.get("/market/snapshot/{symbol}", response_model=Dict[str, Any])
async def get_market_snapshot(
    symbol: str,
    use_cache: bool = Query(True, description="Use cached data"),
    current_user: User = Depends(get_current_user),
):
    """
    Get complete market snapshot for a symbol.
    
    Includes latest trade, quote, minute bar, and daily bar.
    Cached for 2 seconds by default.
    
    **Authentication required.**
    """
    try:
        client = get_market_data_client()
        snapshot_data = await client.get_snapshot(symbol.upper(), use_cache=use_cache)
        
        return {
            "success": True,
            "data": snapshot_data,
        }
        
    except MarketDataError as e:
        logger.error(f"Market data error for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "market_data_error",
                "message": e.message,
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error getting snapshot for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to fetch snapshot",
            }
        )