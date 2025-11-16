from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from .trade import TradeType

class OrderBase(BaseModel):
    symbol: str
    qty: Decimal
    side: str
    type: str
    time_in_force: str
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None

class OrderRequest(OrderBase):
    pass

class OrderUpdateRequest(BaseModel):
    qty: Optional[Decimal] = None
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None

class BracketOrderRequest(OrderBase):
    take_profit_price: Decimal
    stop_loss_price: Decimal

class PositionCloseRequest(BaseModel):
    qty_percent: Optional[float] = None

class OrderResponse(OrderBase):
    id: int
    user_id: int
    strategy_id: Optional[int] = None
    trade_id: int
    alpaca_order_id: str
    filled_qty: Decimal
    filled_avg_price: Optional[Decimal] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrderCancelResponse(BaseModel):
    success: bool
    message: str
    order_id: int
