"""
Portfolio analytics schemas for API requests and responses.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PortfolioSummaryResponse(BaseModel):
    """Summary of current portfolio state."""
    total_equity: float = Field(..., description="Total portfolio value")
    cash_balance: float = Field(..., description="Available cash")
    positions_value: float = Field(..., description="Market value of all positions")
    daily_pnl: float = Field(..., description="Today's P&L")
    daily_return_pct: float = Field(..., description="Today's return percentage")
    total_pnl: float = Field(..., description="All-time P&L")
    total_return_pct: float = Field(..., description="All-time return percentage")
    num_positions: int = Field(..., description="Number of open positions")
    num_long_positions: int = Field(0, description="Number of long positions")
    num_short_positions: int = Field(0, description="Number of short positions")
    last_updated: datetime = Field(..., description="Last update timestamp")


class EquityCurvePoint(BaseModel):
    """Single point on the equity curve."""
    date: datetime
    equity: float
    daily_return: Optional[float] = None
    cumulative_return: Optional[float] = None


class EquityCurveResponse(BaseModel):
    """Equity curve over time."""
    data_points: List[EquityCurvePoint]
    start_date: datetime
    end_date: datetime
    total_points: int


class PerformanceMetricsResponse(BaseModel):
    """Comprehensive performance metrics."""
    # Time period
    period: str = Field(..., description="Time period: daily, weekly, monthly, yearly, all_time")
    start_date: datetime
    end_date: datetime
    
    # Returns
    total_return: float
    total_return_pct: float
    annualized_return: Optional[float] = None
    
    # Risk metrics
    volatility: Optional[float] = Field(None, description="Standard deviation of returns")
    sharpe_ratio: Optional[float] = Field(None, description="Risk-adjusted return")
    sortino_ratio: Optional[float] = Field(None, description="Downside risk-adjusted return")
    calmar_ratio: Optional[float] = Field(None, description="Return / max drawdown")
    
    # Drawdown
    max_drawdown: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    current_drawdown: Optional[float] = None
    current_drawdown_pct: Optional[float] = None
    
    # Win/Loss
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: Optional[float] = Field(None, description="Win rate percentage")
    avg_win: Optional[float] = None
    avg_loss: Optional[float] = None
    profit_factor: Optional[float] = Field(None, description="Gross profit / gross loss")
    
    # Trading activity
    num_trades_long: int = 0
    num_trades_short: int = 0
    avg_holding_period_days: Optional[float] = None
    
    # Benchmark comparison
    benchmark_return: Optional[float] = None
    benchmark_return_pct: Optional[float] = None
    alpha: Optional[float] = Field(None, description="Excess return vs benchmark")
    beta: Optional[float] = Field(None, description="Correlation with benchmark")
    
    class Config:
        from_attributes = True


class ReturnsAnalysisResponse(BaseModel):
    """Detailed returns breakdown."""
    daily_returns: List[float]
    weekly_returns: List[float]
    monthly_returns: List[float]
    best_day: float
    worst_day: float
    best_month: float
    worst_month: float
    positive_days: int
    negative_days: int
    avg_daily_return: float


class TaxLotResponse(BaseModel):
    """Tax lot information for capital gains reporting."""
    id: str
    symbol: str
    quantity: float
    acquisition_date: datetime
    acquisition_price: float
    total_cost: float
    disposition_date: Optional[datetime] = None
    disposition_price: Optional[float] = None
    total_proceeds: Optional[float] = None
    realized_gain_loss: Optional[float] = None
    holding_period_days: Optional[int] = None
    is_long_term: Optional[bool] = None
    status: str
    remaining_quantity: float
    
    class Config:
        from_attributes = True


class TaxReportResponse(BaseModel):
    """Tax report summary."""
    year: int
    total_realized_gains: float
    total_realized_losses: float
    net_gain_loss: float
    short_term_gains: float
    long_term_gains: float
    tax_lots: List[TaxLotResponse]


class BenchmarkComparisonRequest(BaseModel):
    """Request to compare portfolio with benchmark."""
    benchmark_symbol: str = Field("SPY", description="Benchmark symbol (default: SPY)")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class BenchmarkComparisonResponse(BaseModel):
    """Portfolio vs benchmark comparison."""
    portfolio_return: float
    benchmark_return: float
    outperformance: float
    correlation: float
    beta: float
    alpha: float
    tracking_error: float
