"""
Pydantic schemas for paper trading API.
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, List, Any
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
    stop_loss_price: Optional[float] = Field(
        None,
        gt=0,
        description="Stop-loss price - auto-sells if price falls to this level (buy orders only)"
    )
    take_profit_price: Optional[float] = Field(
        None,
        gt=0,
        description="Take-profit price - auto-sells if price rises to this level (buy orders only)"
    )

    @model_validator(mode='after')
    def validate_order(self):
        """Validate order parameters."""
        # Limit price required for limit orders
        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("limit_price is required for limit orders")

        # Stop-loss and take-profit only valid for buy orders
        if self.side == OrderSide.SELL:
            if self.stop_loss_price is not None:
                raise ValueError("stop_loss_price can only be set for buy orders")
            if self.take_profit_price is not None:
                raise ValueError("take_profit_price can only be set for buy orders")

        # Stop-loss should be below take-profit
        if self.stop_loss_price and self.take_profit_price:
            if self.stop_loss_price >= self.take_profit_price:
                raise ValueError("stop_loss_price must be less than take_profit_price")

        return self

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "qty": 10,
                "side": "buy",
                "order_type": "market",
                "limit_price": None,
                "stop_loss_price": 140.0,
                "take_profit_price": 180.0
            }
        }


class PaperAccountResetRequest(BaseModel):
    """Request schema for resetting paper trading account."""
    starting_balance: float = Field(
        default=100000.0,
        description="Starting balance for the reset account",
        gt=0
    )


class UpdateStopLossRequest(BaseModel):
    """Request schema for updating stop-loss/take-profit on an existing position."""
    symbol: str = Field(..., description="Symbol of the position to update")
    stop_loss_price: Optional[float] = Field(None, description="New stop-loss price (None to remove)")
    take_profit_price: Optional[float] = Field(None, description="New take-profit price (None to remove)")

    @model_validator(mode='after')
    def validate_prices(self):
        """Validate that stop-loss is below take-profit if both are set."""
        if self.stop_loss_price and self.take_profit_price:
            if self.stop_loss_price >= self.take_profit_price:
                raise ValueError("stop_loss_price must be less than take_profit_price")
        return self


# Response Schemas
class PaperPositionResponse(BaseModel):
    """Response schema for a paper trading position."""
    symbol: str
    qty: float
    avg_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None

    class Config:
        from_attributes = True


class PaperTradeResponse(BaseModel):
    """Response schema for a paper trade."""
    symbol: str
    qty: float
    side: str
    price: float
    value: float
    timestamp: datetime

    class Config:
        from_attributes = True


class PaperAccountResponse(BaseModel):
    """Response schema for paper trading account."""
    user_id: str
    cash_balance: float
    initial_balance: float
    total_equity: float
    positions: Dict[str, Any]
    orders: List[Any] = []
    trades: List[PaperTradeResponse]
    created_at: datetime
    total_pnl: float
    unrealized_pnl: float
    total_return_pct: float

    class Config:
        from_attributes = True


class PaperOrderResponse(BaseModel):
    """Response schema for a paper order execution."""
    success: bool
    trade: Optional[PaperTradeResponse] = None
    account: Optional[PaperAccountResponse] = None
    error: Optional[str] = None
    required: Optional[float] = None
    available: Optional[float] = None
    requested: Optional[float] = None


class StopLossTriggerResponse(BaseModel):
    """Response schema for a triggered stop-loss or take-profit order."""
    success: bool
    trigger_type: str = Field(..., description="'stop_loss' or 'take_profit'")
    trigger_price: float
    execution_price: float
    position: Dict[str, Any]
    realized_pnl: float
    trade: PaperTradeResponse
    user_id: str


class MonitorCheckResponse(BaseModel):
    """Response schema for position monitor check."""
    triggered_orders: List[StopLossTriggerResponse]
    positions_checked: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
