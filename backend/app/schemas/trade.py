"""
Pydantic schemas for trade and position-related requests and responses.
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field
from app.models.trade import TradeType, TradeStatus


class TradeBase(BaseModel):
    """Base trade schema."""
    ticker: str = Field(..., min_length=1, max_length=20)
    trade_type: TradeType
    quantity: Decimal = Field(..., gt=0)
    price: Optional[Decimal] = Field(None, gt=0)


class TradeCreate(TradeBase):
    """Schema for trade creation."""
    strategy_id: Optional[str] = None


class TradeUpdate(BaseModel):
    """Schema for trade updates."""
    status: Optional[TradeStatus] = None
    filled_quantity: Optional[Decimal] = Field(None, ge=0)
    filled_avg_price: Optional[Decimal] = Field(None, gt=0)


class TradeResponse(TradeBase):
    """Schema for trade response."""
    id: str
    user_id: str
    strategy_id: Optional[str] = None
    status: TradeStatus
    filled_quantity: Decimal
    filled_avg_price: Optional[Decimal] = None
    order_id: Optional[str] = None
    realized_pnl: Optional[Decimal] = None
    created_at: datetime
    executed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PositionBase(BaseModel):
    """Base position schema."""
    ticker: str = Field(..., min_length=1, max_length=20)
    quantity: Decimal = Field(..., gt=0)
    avg_entry_price: Decimal = Field(..., gt=0)


class PositionResponse(PositionBase):
    """Schema for position response."""
    id: str
    user_id: str
    strategy_id: Optional[str] = None
    current_price: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    realized_pnl: Decimal
    opened_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TradingStatistics(BaseModel):
    """Schema for trading statistics."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: Decimal
    avg_win: Optional[Decimal] = None
    avg_loss: Optional[Decimal] = None
    largest_win: Optional[Decimal] = None
    largest_loss: Optional[Decimal] = None
    sharpe_ratio: Optional[float] = None


class PortfolioSummary(BaseModel):
    """Schema for portfolio summary."""
    total_value: Decimal
    cash_balance: Decimal
    positions_value: Decimal
    total_pnl: Decimal
    day_pnl: Decimal
    positions_count: int
    active_strategies: int
