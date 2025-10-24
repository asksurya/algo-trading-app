"""
Order-related schemas for API requests and responses.
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class OrderSide(str, Enum):
    """Order side (buy/sell)."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class TimeInForce(str, Enum):
    """Time in force options."""
    DAY = "day"  # Day order
    GTC = "gtc"  # Good till canceled
    IOC = "ioc"  # Immediate or cancel
    FOK = "fok"  # Fill or kill
    OPG = "opg"  # Market on open
    CLS = "cls"  # Market on close


class OrderStatus(str, Enum):
    """Order status."""
    NEW = "new"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    DONE_FOR_DAY = "done_for_day"
    CANCELED = "canceled"
    EXPIRED = "expired"
    REPLACED = "replaced"
    PENDING_CANCEL = "pending_cancel"
    PENDING_REPLACE = "pending_replace"
    ACCEPTED = "accepted"
    PENDING_NEW = "pending_new"
    ACCEPTED_FOR_BIDDING = "accepted_for_bidding"
    STOPPED = "stopped"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    CALCULATED = "calculated"


class OrderRequest(BaseModel):
    """Request to place a new order."""
    symbol: str = Field(..., description="Stock symbol (e.g., AAPL)")
    qty: Optional[float] = Field(None, description="Quantity to buy/sell (use notional for dollars)")
    notional: Optional[float] = Field(None, description="Dollar amount (for fractional shares)")
    side: OrderSide = Field(..., description="Buy or sell")
    type: OrderType = Field(..., description="Order type")
    time_in_force: TimeInForce = Field(default=TimeInForce.DAY, description="Order duration")
    limit_price: Optional[float] = Field(None, description="Limit price (required for limit orders)")
    stop_price: Optional[float] = Field(None, description="Stop price (required for stop orders)")
    trail_price: Optional[float] = Field(None, description="Trail price (for trailing stop)")
    trail_percent: Optional[float] = Field(None, description="Trail percent (for trailing stop)")
    extended_hours: bool = Field(default=False, description="Allow extended hours trading")
    client_order_id: Optional[str] = Field(None, description="Client-specified order ID")
    strategy_id: Optional[int] = Field(None, description="Strategy ID for risk context")
    skip_risk_check: bool = Field(default=False, description="Skip risk rule evaluation (use with caution)")
    
    @field_validator('qty', 'notional')
    @classmethod
    def validate_quantity(cls, v, info):
        """Validate that either qty or notional is provided."""
        if v is not None and v <= 0:
            raise ValueError(f"{info.field_name} must be positive")
        return v
    
    @field_validator('limit_price', 'stop_price', 'trail_price')
    @classmethod
    def validate_price(cls, v):
        """Validate price is positive."""
        if v is not None and v <= 0:
            raise ValueError("Price must be positive")
        return v
    
    @field_validator('trail_percent')
    @classmethod
    def validate_trail_percent(cls, v):
        """Validate trail percent is between 0 and 100."""
        if v is not None and (v <= 0 or v >= 100):
            raise ValueError("Trail percent must be between 0 and 100")
        return v


class OrderUpdateRequest(BaseModel):
    """Request to modify an existing order."""
    qty: Optional[float] = Field(None, description="New quantity")
    limit_price: Optional[float] = Field(None, description="New limit price")
    stop_price: Optional[float] = Field(None, description="New stop price")
    trail: Optional[float] = Field(None, description="New trail amount")
    time_in_force: Optional[TimeInForce] = Field(None, description="New time in force")
    client_order_id: Optional[str] = Field(None, description="New client order ID")


class OrderResponse(BaseModel):
    """Order details response."""
    id: str = Field(..., description="Alpaca order ID")
    client_order_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    replaced_at: Optional[datetime] = None
    replaced_by: Optional[str] = None
    replaces: Optional[str] = None
    asset_id: str
    symbol: str
    asset_class: str
    notional: Optional[float] = None
    qty: Optional[float] = None
    filled_qty: float
    filled_avg_price: Optional[float] = None
    order_type: str
    side: str
    time_in_force: str
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    status: str
    extended_hours: bool
    legs: list = Field(default_factory=list)
    trail_percent: Optional[float] = None
    trail_price: Optional[float] = None
    hwm: Optional[float] = None  # High water mark for trailing stop


class BracketOrderRequest(BaseModel):
    """Request to place a bracket order (entry + take profit + stop loss)."""
    symbol: str = Field(..., description="Stock symbol")
    qty: float = Field(..., gt=0, description="Quantity to buy/sell")
    side: OrderSide = Field(..., description="Buy or sell")
    entry_type: OrderType = Field(default=OrderType.MARKET, description="Entry order type")
    entry_limit_price: Optional[float] = Field(None, description="Entry limit price")
    take_profit_limit_price: float = Field(..., description="Take profit limit price")
    stop_loss_stop_price: float = Field(..., description="Stop loss stop price")
    time_in_force: TimeInForce = Field(default=TimeInForce.GTC, description="Order duration")
    extended_hours: bool = Field(default=False)
    
    @field_validator('take_profit_limit_price', 'stop_loss_stop_price')
    @classmethod
    def validate_bracket_prices(cls, v, info):
        """Validate bracket order prices."""
        if v <= 0:
            raise ValueError(f"{info.field_name} must be positive")
        return v


class PositionCloseRequest(BaseModel):
    """Request to close a position."""
    qty: Optional[float] = Field(None, description="Quantity to close (omit to close all)")
    percentage: Optional[float] = Field(None, description="Percentage to close (0-100)")
    
    @field_validator('percentage')
    @classmethod
    def validate_percentage(cls, v):
        """Validate percentage is between 0 and 100."""
        if v is not None and (v <= 0 or v > 100):
            raise ValueError("Percentage must be between 0 and 100")
        return v


class OrderListResponse(BaseModel):
    """Multiple orders response."""
    orders: list[OrderResponse]
    count: int = Field(description="Number of orders returned")
