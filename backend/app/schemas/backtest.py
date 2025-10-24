"""
Pydantic schemas for backtesting.
Request and response models for backtest API endpoints.
"""
from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


# Request schemas

class BacktestCreate(BaseModel):
    """Schema for creating a new backtest."""
    
    strategy_id: UUID = Field(..., description="ID of the strategy to backtest")
    name: str = Field(..., min_length=1, max_length=200, description="Backtest name")
    description: Optional[str] = Field(None, description="Backtest description")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: float = Field(100000.0, gt=0, description="Starting capital")
    commission: float = Field(0.001, ge=0, le=1, description="Commission rate")
    slippage: float = Field(0.0005, ge=0, le=1, description="Slippage rate")
    strategy_params: Optional[Dict[str, Any]] = Field(None, description="Strategy parameter overrides")
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: datetime, info) -> datetime:
        """Ensure end_date is after start_date."""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "strategy_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "RSI Strategy Backtest Q1 2024",
                "description": "Testing RSI strategy on tech stocks",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-03-31T23:59:59Z",
                "initial_capital": 100000.0,
                "commission": 0.001,
                "slippage": 0.0005,
                "strategy_params": {
                    "rsi_period": 14,
                    "overbought": 70,
                    "oversold": 30
                }
            }]
        }
    }


# Response schemas

class BacktestTradeResponse(BaseModel):
    """Schema for backtest trade response."""
    
    id: UUID
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: Optional[float]
    entry_date: datetime
    exit_date: Optional[datetime]
    pnl: Optional[float]
    pnl_pct: Optional[float]
    commission: float
    slippage: float
    duration_hours: Optional[float]
    entry_signal: Optional[str]
    exit_signal: Optional[str]
    is_open: bool
    
    model_config = {"from_attributes": True}


class BacktestResultResponse(BaseModel):
    """Schema for detailed backtest results."""
    
    id: UUID
    backtest_id: UUID
    
    # Performance metrics
    final_capital: float
    total_return_pct: float
    annualized_return: float
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # P&L metrics
    gross_profit: float
    gross_loss: float
    net_profit: float
    profit_factor: Optional[float]
    
    # Average trade metrics
    avg_trade_pnl: float
    avg_winning_trade: Optional[float]
    avg_losing_trade: Optional[float]
    largest_win: Optional[float]
    largest_loss: Optional[float]
    
    # Risk metrics
    max_drawdown_pct: float
    max_drawdown_dollars: float
    sharpe_ratio: Optional[float]
    sortino_ratio: Optional[float]
    calmar_ratio: Optional[float]
    
    # Other metrics
    volatility: Optional[float]
    avg_trade_duration_hours: Optional[float]
    market_exposure_pct: Optional[float]
    
    # Data series
    equity_curve: Dict[str, Any]
    drawdown_periods: Optional[Dict[str, Any]]
    monthly_returns: Optional[Dict[str, Any]]
    additional_metrics: Optional[Dict[str, Any]]
    
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class BacktestResponse(BaseModel):
    """Schema for backtest response."""
    
    id: UUID
    user_id: UUID
    strategy_id: UUID
    name: str
    description: Optional[str]
    
    # Time period
    start_date: datetime
    end_date: datetime
    
    # Parameters
    initial_capital: float
    commission: float
    slippage: float
    strategy_params: Optional[Dict[str, Any]]
    
    # Status
    status: str
    progress: int
    
    # Timing
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    
    # Error
    error_message: Optional[str]
    
    # Results summary
    total_trades: Optional[int]
    winning_trades: Optional[int]
    losing_trades: Optional[int]
    total_return: Optional[float]
    total_pnl: Optional[float]
    max_drawdown: Optional[float]
    sharpe_ratio: Optional[float]
    win_rate: Optional[float]
    
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class BacktestWithResults(BacktestResponse):
    """Schema for backtest with full results."""
    
    results: Optional[BacktestResultResponse] = None
    trades: Optional[List[BacktestTradeResponse]] = None


class BacktestListResponse(BaseModel):
    """Schema for list of backtests."""
    
    success: bool = True
    data: List[BacktestResponse]
    total: int
    page: int = 1
    page_size: int = 50


class BacktestDetailResponse(BaseModel):
    """Schema for detailed backtest response."""
    
    success: bool = True
    data: BacktestWithResults


class BacktestStatusResponse(BaseModel):
    """Schema for backtest status check."""
    
    success: bool = True
    data: Dict[str, Any] = Field(..., description="Backtest status information")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "success": True,
                "data": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "status": "running",
                    "progress": 65,
                    "started_at": "2024-10-20T15:30:00Z",
                    "elapsed_seconds": 120.5
                }
            }]
        }
    }
