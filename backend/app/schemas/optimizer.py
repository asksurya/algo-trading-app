"""
Schemas for strategy optimizer API.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class OptimizeStrategyRequest(BaseModel):
    """Request to optimize strategies across multiple symbols."""
    symbols: List[str] = Field(
        ...,
        description="List of ticker symbols to analyze",
        min_items=1,
        max_items=20
    )
    strategy_ids: Optional[List[int]] = Field(
        None,
        description="Optional list of strategy IDs (all if None)"
    )
    start_date: datetime = Field(
        ...,
        description="Backtest start date"
    )
    end_date: datetime = Field(
        ...,
        description="Backtest end date"
    )
    initial_capital: float = Field(
        default=100000.0,
        description="Initial capital for backtests",
        gt=0
    )


class StrategyPerformanceSchema(BaseModel):
    """Performance metrics for a strategy on a specific symbol."""
    strategy_id: int
    strategy_name: str
    symbol: str
    backtest_id: UUID
    total_return: float
    sharpe_ratio: Optional[float]
    max_drawdown: float
    win_rate: float
    total_trades: int
    net_profit: float
    composite_score: float
    rank: int
    
    class Config:
        from_attributes = True


class OptimizationResultSchema(BaseModel):
    """Results of strategy optimization for a symbol."""
    symbol: str
    best_strategy: StrategyPerformanceSchema
    all_performances: List[StrategyPerformanceSchema]
    analysis_date: datetime
    
    class Config:
        from_attributes = True


class OptimizeStrategyResponse(BaseModel):
    """Response from strategy optimization."""
    job_id: str = Field(
        ...,
        description="Unique job identifier for tracking"
    )
    status: str = Field(
        ...,
        description="Job status (pending, running, completed, failed)"
    )
    results: Dict[str, OptimizationResultSchema] = Field(
        default_factory=dict,
        description="Optimization results per symbol"
    )
    total_symbols: int
    total_strategies: int
    total_backtests: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ExecuteOptimalRequest(BaseModel):
    """Request to execute optimal strategies."""
    optimization_job_id: str = Field(
        ...,
        description="Job ID from previous optimization"
    )
    symbols: Optional[List[str]] = Field(
        None,
        description="Specific symbols to execute (all if None)"
    )
    risk_rule_ids: Optional[List[int]] = Field(
        None,
        description="Risk rule IDs to enforce"
    )
    auto_size: bool = Field(
        default=True,
        description="Auto-calculate position sizes"
    )
    max_position_pct: float = Field(
        default=10.0,
        description="Max position size as % of portfolio",
        gt=0,
        le=100
    )


class ExecutionResultSchema(BaseModel):
    """Result of a single execution."""
    symbol: str
    strategy: str
    order_id: Optional[str] = None
    alpaca_order_id: Optional[str] = None
    shares: Optional[int] = None
    estimated_value: Optional[float] = None
    composite_score: Optional[float] = None
    error: Optional[str] = None
    breaches: Optional[List[Dict[str, Any]]] = None


class ExecuteOptimalResponse(BaseModel):
    """Response from optimal strategy execution."""
    job_id: str
    executed_at: datetime
    successful: List[ExecutionResultSchema]
    failed: List[ExecutionResultSchema]
    blocked: List[ExecutionResultSchema]
    warnings: List[Dict[str, str]]
    total_executed: int
    total_blocked: int
    total_failed: int


class OptimizationJobStatus(BaseModel):
    """Status of an optimization job."""
    job_id: str
    status: str
    progress: float = Field(
        default=0.0,
        description="Progress percentage (0-100)",
        ge=0,
        le=100
    )
    current_step: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    results_available: bool = False


class OptimizationHistory(BaseModel):
    """Historical optimization job."""
    job_id: str
    user_id: int
    symbols: List[str]
    strategy_count: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_backtests: int
    best_composite_score: Optional[float] = None
