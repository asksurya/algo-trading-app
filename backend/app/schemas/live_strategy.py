"""
Pydantic schemas for live trading strategies.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator


class LiveStrategyBase(BaseModel):
    """Base schema for live strategy."""
    name: str = Field(..., min_length=1, max_length=255)
    strategy_id: int
    symbols: List[str] = Field(..., min_items=1)
    check_interval: int = Field(default=300, ge=60, le=3600)  # 1 min to 1 hour
    auto_execute: bool = Field(default=False)
    max_position_size: Optional[float] = Field(default=None, ge=0)
    max_positions: int = Field(default=5, ge=1, le=20)
    daily_loss_limit: Optional[float] = Field(default=None, ge=0)
    position_size_pct: float = Field(default=0.02, ge=0.001, le=0.5)  # 0.1% to 50%
    
    @validator('symbols')
    def validate_symbols(cls, v):
        """Validate symbol list."""
        if not v:
            raise ValueError("At least one symbol is required")
        # Remove duplicates and uppercase
        return list(set([s.upper() for s in v]))
    
    @validator('check_interval')
    def validate_check_interval(cls, v):
        """Ensure check interval is reasonable."""
        valid_intervals = [60, 300, 900, 1800, 3600]  # 1m, 5m, 15m, 30m, 1h
        if v not in valid_intervals:
            # Round to nearest valid interval
            return min(valid_intervals, key=lambda x: abs(x - v))
        return v


class LiveStrategyCreate(LiveStrategyBase):
    """Schema for creating a live strategy."""
    pass


class LiveStrategyUpdate(BaseModel):
    """Schema for updating a live strategy."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    symbols: Optional[List[str]] = None
    check_interval: Optional[int] = Field(None, ge=60, le=3600)
    auto_execute: Optional[bool] = None
    max_position_size: Optional[float] = Field(None, ge=0)
    max_positions: Optional[int] = Field(None, ge=1, le=20)
    daily_loss_limit: Optional[float] = Field(None, ge=0)
    position_size_pct: Optional[float] = Field(None, ge=0.001, le=0.5)


class LiveStrategyResponse(LiveStrategyBase):
    """Schema for live strategy response."""
    id: str
    user_id: str
    status: str
    last_check: Optional[datetime] = None
    last_signal: Optional[datetime] = None
    state: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    total_signals: int = 0
    executed_trades: int = 0
    current_positions: int = 0
    daily_pnl: float = 0.0
    total_pnl: float = 0.0
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SignalHistoryResponse(BaseModel):
    """Schema for signal history response."""
    id: str
    live_strategy_id: str
    symbol: str
    signal_type: str
    signal_strength: Optional[float] = None
    price: float
    volume: Optional[float] = None
    indicators: Optional[Dict[str, Any]] = None
    executed: bool = False
    execution_price: Optional[float] = None
    order_id: Optional[str] = None
    execution_time: Optional[datetime] = None
    execution_error: Optional[str] = None
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class LiveStrategyStatusResponse(BaseModel):
    """Schema for live strategy status."""
    strategy: LiveStrategyResponse
    recent_signals: List[SignalHistoryResponse]
    is_running: bool


class DashboardSummary(BaseModel):
    """Schema for live trading dashboard summary."""
    active_strategies: int
    total_strategies: int
    signals_today: int
    trades_today: int
    total_pnl: float
    daily_pnl: float
    active_positions: int


class DashboardResponse(BaseModel):
    """Schema for live trading dashboard."""
    summary: DashboardSummary
    active_strategies: List[LiveStrategyResponse]
    recent_signals: List[SignalHistoryResponse]


class StartStrategyRequest(BaseModel):
    """Schema for starting a strategy."""
    force: bool = Field(default=False, description="Force start even if errors exist")


class ControlResponse(BaseModel):
    """Schema for control action responses."""
    success: bool
    message: str
    strategy_id: Optional[str] = None
