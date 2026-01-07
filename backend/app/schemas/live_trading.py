from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal


# ============================================================================
# Live Strategy Schemas
# ============================================================================

class LiveStrategyCreate(BaseModel):
    """Schema for creating a new live trading strategy."""
    name: str = Field(..., min_length=1, max_length=255, description="Strategy name")
    strategy_id: str = Field(..., description="Base strategy ID (UUID)")
    symbols: List[str] = Field(..., min_items=1, description="List of symbols to trade")
    check_interval: int = Field(default=300, ge=60, description="Check interval in seconds")
    auto_execute: bool = Field(default=False, description="Automatically execute trades")
    max_positions: int = Field(default=5, ge=1, le=20, description="Maximum concurrent positions")
    daily_loss_limit: Optional[float] = Field(default=None, description="Maximum daily loss in dollars")
    position_size_pct: float = Field(default=0.02, ge=0.001, le=1.0, description="Position size as % of portfolio")
    max_position_size: Optional[float] = Field(default=None, description="Maximum position size in dollars")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "AMD NVDA Live Trading",
                "strategy_id": "55eb1840-9df6-4bf2-a9a3-9bab4a4073cf",
                "symbols": ["AMD", "NVDA"],
                "check_interval": 300,
                "auto_execute": False,
                "max_positions": 5,
                "daily_loss_limit": 1000.0,
                "position_size_pct": 0.02,
                "max_position_size": 5000.0
            }
        }


class LiveStrategyUpdate(BaseModel):
    """Schema for updating an existing live strategy."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    symbols: Optional[List[str]] = Field(None, min_items=1)
    check_interval: Optional[int] = Field(None, ge=60)
    auto_execute: Optional[bool] = None
    max_positions: Optional[int] = Field(None, ge=1, le=20)
    daily_loss_limit: Optional[float] = None
    position_size_pct: Optional[float] = Field(None, ge=0.001, le=1.0)
    max_position_size: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "auto_execute": True,
                "max_positions": 10
            }
        }


class LiveStrategyResponse(BaseModel):
    """Schema for live strategy response."""
    id: str
    user_id: str
    strategy_id: str
    name: str
    symbols: List[str]
    status: str
    check_interval: int
    auto_execute: bool
    max_position_size: Optional[float]
    max_positions: int
    daily_loss_limit: Optional[float]
    position_size_pct: float
    last_check: Optional[datetime]
    last_signal: Optional[datetime]
    error_message: Optional[str]
    total_signals: int
    executed_trades: int
    current_positions: int
    win_rate: Optional[float]
    total_pnl: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user-uuid",
                "strategy_id": "55eb1840-9df6-4bf2-a9a3-9bab4a4073cf",
                "name": "AMD NVDA Live Trading",
                "symbols": ["AMD", "NVDA"],
                "status": "active",
                "check_interval": 300,
                "auto_execute": False,
                "max_position_size": 5000.0,
                "max_positions": 5,
                "daily_loss_limit": 1000.0,
                "position_size_pct": 0.02,
                "last_check": None,
                "last_signal": None,
                "error_message": None,
                "total_signals": 0,
                "executed_trades": 0,
                "current_positions": 0,
                "win_rate": None,
                "total_pnl": 0.0,
                "created_at": "2025-12-25T20:00:00Z",
                "updated_at": "2025-12-25T20:00:00Z"
            }
        }


class LivePositionResponse(BaseModel):
    """Schema for live position response."""
    id: str
    live_strategy_id: str
    symbol: str
    quantity: float
    avg_entry_price: float
    current_price: float
    unrealized_pnl: float
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# System Status & Portfolio Schemas
# ============================================================================

class LiveTradingStatusResponse(BaseModel):
    is_running: bool
    active_strategies: int
    total_pnl: Decimal
    last_trade_at: Optional[datetime]

class LiveTradingPortfolioResponse(BaseModel):
    total_value: Decimal
    cash: Decimal
    positions: List[dict]

class LiveTradingActionRequest(BaseModel):
    action: str # e.g., "pause", "resume"


# ============================================================================
# Quick Deploy Schemas
# ============================================================================

class QuickDeployRequest(BaseModel):
    """Request for quick deployment of a strategy to live trading."""
    strategy_id: str = Field(..., description="Base strategy ID (UUID)")
    symbols: List[str] = Field(..., min_items=1, description="List of symbols to trade")
    # Optional overrides (all have sensible defaults)
    name: Optional[str] = Field(None, description="Strategy name (defaults to 'Live - {strategy.name}')")
    check_interval: int = Field(default=300, ge=60, description="Check interval in seconds (default: 5 minutes)")
    auto_execute: bool = Field(default=True, description="Automatically execute trades (default: true)")
    max_positions: int = Field(default=5, ge=1, le=20, description="Maximum concurrent positions")
    position_size_pct: float = Field(default=0.02, ge=0.001, le=1.0, description="Position size as % of portfolio")
    max_position_size: Optional[float] = Field(default=None, description="Maximum position size in dollars")
    daily_loss_limit: Optional[float] = Field(default=None, description="Maximum daily loss in dollars")

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "55eb1840-9df6-4bf2-a9a3-9bab4a4073cf",
                "symbols": ["AAPL", "MSFT"],
                "name": "Live - RSI Strategy",
                "check_interval": 300,
                "auto_execute": True,
                "max_positions": 5,
                "position_size_pct": 0.02
            }
        }


class QuickDeployResponse(BaseModel):
    """Response for quick deploy."""
    success: bool
    live_strategy_id: str
    name: str
    status: str
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "live_strategy_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Live - RSI Strategy",
                "status": "ACTIVE",
                "message": "Strategy deployed successfully. Now monitoring 2 symbols."
            }
        }
