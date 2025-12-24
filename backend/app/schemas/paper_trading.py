"""
Pydantic schemas for paper trading API.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class OrderSide(str, Enum):
    """Order side enum."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type enum."""
    MARKET = "market"
    LIMIT = "limit"


# Request Schemas
class PaperOrderRequest(BaseModel):
    """Request schema for placing a paper trade order."""
    symbol: str = Field(..., description="Stock ticker symbol", min_length=1, max_length=10)
    qty: float = Field(..., description="Quantity to trade", gt=0)
    side: OrderSide = Field(..., description="Order side: buy or sell")
    order_type: OrderType = Field(default=OrderType.MARKET, description="Order type: market or limit")
    limit_price: Optional[float] = Field(None, description="Limit price for limit orders", gt=0)

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "qty": 10,
                "side": "buy",
                "order_type": "market",
                "limit_price": None
            }
        }


class PaperAccountResetRequest(BaseModel):
    """Request schema for resetting paper trading account."""
    starting_balance: float = Field(
        default=100000.0,
        description="Starting balance for the reset account",
        gt=0
    )


# Response Schemas
class PaperPositionResponse(BaseModel):
    """Response schema for a paper trading position."""
    symbol: str
    qty: float
    avg_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float


class PaperTradeResponse(BaseModel):
    """Response schema for a paper trade."""
    symbol: str
    qty: float
    side: str
    price: float
    value: float
    timestamp: datetime


class PaperAccountResponse(BaseModel):
    """Response schema for paper trading account."""
    user_id: str
    cash_balance: float
    initial_balance: float
    total_equity: float
    positions: Dict[str, Any]
    orders: List[Any]
    trades: List[PaperTradeResponse]
    created_at: datetime
    total_pnl: float
    unrealized_pnl: float
    total_return_pct: float


class PaperOrderResponse(BaseModel):
    """Response schema for a paper order execution."""
    success: bool
    trade: Optional[PaperTradeResponse] = None
    account: Optional[PaperAccountResponse] = None
    error: Optional[str] = None
    required: Optional[float] = None
    available: Optional[float] = None
    requested: Optional[float] = None
