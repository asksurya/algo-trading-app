"""
Watchlist schemas for API requests and responses.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class WatchlistCreate(BaseModel):
    """Create a new watchlist."""
    name: str = Field(..., min_length=1, max_length=100, description="Watchlist name")
    description: Optional[str] = Field(None, max_length=500, description="Watchlist description")


class WatchlistUpdate(BaseModel):
    """Update watchlist details."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class WatchlistItemCreate(BaseModel):
    """Add symbol to watchlist."""
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol")
    notes: Optional[str] = Field(None, max_length=500, description="Notes about this symbol")


class WatchlistItemResponse(BaseModel):
    """Watchlist item with current market data."""
    id: str
    symbol: str
    notes: Optional[str] = None
    created_at: datetime
    
    # Real-time market data (populated from broker)
    current_price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    
    class Config:
        from_attributes = True


class WatchlistResponse(BaseModel):
    """Watchlist with items."""
    id: str
    name: str
    description: Optional[str] = None
    user_id: str
    created_at: datetime
    updated_at: datetime
    items: List[WatchlistItemResponse] = []
    
    class Config:
        from_attributes = True


class PriceAlertCreate(BaseModel):
    """Create a price alert."""
    symbol: str = Field(..., min_length=1, max_length=10)
    condition: str = Field(..., description="'above' or 'below'")
    target_price: float = Field(..., gt=0, description="Alert trigger price")
    message: Optional[str] = Field(None, max_length=200, description="Custom alert message")


class PriceAlertUpdate(BaseModel):
    """Update price alert."""
    condition: Optional[str] = None
    target_price: Optional[float] = Field(None, gt=0)
    message: Optional[str] = None
    is_active: Optional[bool] = None


class PriceAlertResponse(BaseModel):
    """Price alert details."""
    id: str
    user_id: str
    symbol: str
    condition: str
    target_price: float
    message: Optional[str] = None
    is_active: bool
    triggered_at: Optional[datetime] = None
    created_at: datetime
    
    # Current market status
    current_price: Optional[float] = None
    distance_to_target: Optional[float] = None
    distance_percent: Optional[float] = None
    
    class Config:
        from_attributes = True


class WatchlistSummaryResponse(BaseModel):
    """Summary of all watchlists."""
    total_watchlists: int
    total_symbols: int
    watchlists: List[WatchlistResponse]
