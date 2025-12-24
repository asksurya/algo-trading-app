"""
Pydantic schemas for paper trading.
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, List, Any
from datetime import datetime


class PaperOrderRequest(BaseModel):
    """Request schema for placing a paper trading order."""
    symbol: str = Field(..., description="Trading symbol (e.g., 'AAPL')")
    qty: float = Field(..., gt=0, description="Quantity of shares to trade")
    side: str = Field(..., pattern="^(buy|sell)$", description="Order side: 'buy' or 'sell'")
    order_type: str = Field(default="market", pattern="^(market|limit)$", description="Order type")
    limit_price: Optional[float] = Field(None, gt=0, description="Limit price for limit orders")
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
        if self.order_type == "limit" and self.limit_price is None:
            raise ValueError("limit_price is required for limit orders")

        # Stop-loss and take-profit only valid for buy orders
        if self.side == "sell":
            if self.stop_loss_price is not None:
                raise ValueError("stop_loss_price can only be set for buy orders")
            if self.take_profit_price is not None:
                raise ValueError("take_profit_price can only be set for buy orders")

        # Stop-loss should be below the limit price (or expected execution price)
        if self.stop_loss_price and self.take_profit_price:
            if self.stop_loss_price >= self.take_profit_price:
                raise ValueError("stop_loss_price must be less than take_profit_price")

        return self


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
    """Response schema for a paper trade execution."""
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
    positions: Dict[str, PaperPositionResponse]
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
    error: Optional[str] = None
    trade: Optional[PaperTradeResponse] = None
    account: Optional[PaperAccountResponse] = None


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
