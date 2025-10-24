"""
Market data schemas for API responses.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class QuoteResponse(BaseModel):
    """Real-time quote data."""
    symbol: str
    bid_price: float
    bid_size: int
    ask_price: float
    ask_size: int
    timestamp: datetime
    conditions: Optional[List[str]] = None
    tape: Optional[str] = None


class TradeResponse(BaseModel):
    """Latest trade data."""
    symbol: str
    price: float
    size: int
    timestamp: datetime
    exchange: Optional[str] = None
    conditions: Optional[List[str]] = None
    id: Optional[str] = None
    tape: Optional[str] = None


class BarResponse(BaseModel):
    """OHLCV bar data."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    trade_count: Optional[int] = None
    vwap: Optional[float] = None


class SnapshotResponse(BaseModel):
    """Complete market snapshot."""
    symbol: str
    latest_trade: Optional[TradeResponse] = None
    latest_quote: Optional[QuoteResponse] = None
    minute_bar: Optional[BarResponse] = None
    daily_bar: Optional[BarResponse] = None
    prev_daily_bar: Optional[BarResponse] = None


class MultiQuoteResponse(BaseModel):
    """Multiple quotes response."""
    quotes: List[QuoteResponse]
    count: int = Field(description="Number of quotes returned")


class MultiTradeResponse(BaseModel):
    """Multiple trades response."""
    trades: List[TradeResponse]
    count: int = Field(description="Number of trades returned")


class BarsResponse(BaseModel):
    """Historical bars response."""
    symbol: str
    bars: List[BarResponse]
    count: int = Field(description="Number of bars returned")
    timeframe: str = Field(description="Timeframe of bars (e.g., '1Min', '1Hour', '1Day')")