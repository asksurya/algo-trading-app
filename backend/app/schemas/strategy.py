"""
Pydantic schemas for strategy-related requests and responses.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class StrategyBase(BaseModel):
    """Base strategy schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    strategy_type: str = Field(
        ...,
        description="Strategy type (e.g., 'bollinger_bands', 'momentum', 'ml_strategy')"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy-specific parameters"
    )


class StrategyCreate(StrategyBase):
    """Schema for strategy creation."""
    tickers: List[str] = Field(
        default_factory=list,
        description="List of tickers for this strategy"
    )


class StrategyUpdate(BaseModel):
    """Schema for strategy updates."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class StrategyResponse(StrategyBase):
    """Schema for strategy response."""
    id: str
    user_id: str
    is_active: bool
    is_backtested: bool
    backtest_results: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StrategyTickerBase(BaseModel):
    """Base strategy ticker schema."""
    ticker: str = Field(..., min_length=1, max_length=20)
    allocation_percent: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Percentage allocation"
    )


class StrategyTickerCreate(StrategyTickerBase):
    """Schema for adding ticker to strategy."""
    pass


class StrategyTickerResponse(StrategyTickerBase):
    """Schema for strategy ticker response."""
    id: str
    strategy_id: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class BacktestRequest(BaseModel):
    """Schema for backtest request."""
    start_date: str = Field(
        ...,
        description="Start date in YYYY-MM-DD format"
    )
    end_date: str = Field(
        ...,
        description="End date in YYYY-MM-DD format"
    )
    initial_capital: float = Field(
        default=100000.0,
        gt=0,
        description="Initial capital for backtesting"
    )
    tickers: List[str] = Field(
        ...,
        min_items=1,
        description="List of tickers to backtest"
    )


class BacktestResponse(BaseModel):
    """Schema for backtest response."""
    strategy_id: str
    total_return: float
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    total_trades: int
    results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed backtest results"
    )
