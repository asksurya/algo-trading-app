"""
Backtesting models.
Stores backtest configurations, results, and trade history.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, JSON, Float, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from app.models.base import Base, SoftDeleteMixin
from app.models.enums import BacktestStatus



class Backtest(Base, SoftDeleteMixin):
    """
    Backtest configuration and metadata.
    Stores parameters for running historical strategy backtests.
    Supports soft delete for data retention.
    """
    
    __tablename__ = "backtests"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # Foreign keys
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    strategy_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("strategies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Backtest metadata
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="User-provided name for the backtest"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Description of the backtest purpose/goals"
    )
    
    # Time period
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Backtest start date"
    )
    
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Backtest end date"
    )
    
    # Execution parameters
    initial_capital: Mapped[float] = mapped_column(
        Float,
        default=100000.0,
        nullable=False,
        comment="Starting capital for backtest"
    )
    
    commission: Mapped[float] = mapped_column(
        Float,
        default=0.001,
        nullable=False,
        comment="Commission rate (e.g., 0.001 = 0.1%)"
    )
    
    slippage: Mapped[float] = mapped_column(
        Float,
        default=0.0005,
        nullable=False,
        comment="Slippage rate"
    )
    
    # Strategy parameters (can override default)
    strategy_params: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="Strategy parameters for this backtest"
    )
    
    # Status tracking
    status: Mapped[BacktestStatus] = mapped_column(
        SQLEnum(BacktestStatus, values_callable=lambda x: [e.value for e in x]),
        default=BacktestStatus.PENDING,
        nullable=False,
        index=True
    )
    
    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Completion percentage (0-100)"
    )
    
    # Execution timing
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        comment="When backtest execution started"
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        comment="When backtest execution completed"
    )
    
    duration_seconds: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Total execution time in seconds"
    )
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Error message if backtest failed"
    )
    
    # Results summary (denormalized for quick access)
    total_trades: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Total number of trades executed"
    )
    
    winning_trades: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Number of winning trades"
    )
    
    losing_trades: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Number of losing trades"
    )
    
    total_return: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Total return percentage"
    )
    
    total_pnl: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Total profit/loss in dollars"
    )
    
    max_drawdown: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Maximum drawdown percentage"
    )
    
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Sharpe ratio"
    )
    
    win_rate: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Win rate percentage"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    strategy = relationship("Strategy", backref="backtests")
    user = relationship("User", backref="backtests")
    result = relationship(
        "BacktestResult",
        back_populates="backtest",
        uselist=False,
        cascade="all, delete-orphan"
    )
    trades = relationship(
        "BacktestTrade",
        back_populates="backtest",
        cascade="all, delete-orphan",
        order_by="BacktestTrade.entry_date"
    )
    
    def __repr__(self) -> str:
        return f"<Backtest(id={self.id}, name={self.name}, status={self.status})>"


class BacktestResult(Base):
    """
    Detailed backtest results and metrics.
    Stores comprehensive performance analysis.
    """
    
    __tablename__ = "backtest_results"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # Foreign key
    backtest_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("backtests.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Performance metrics
    final_capital: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Final portfolio value"
    )
    
    total_return_pct: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Total return percentage"
    )
    
    annualized_return: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Annualized return percentage"
    )
    
    # Trade statistics
    total_trades: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    winning_trades: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    losing_trades: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    win_rate: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Percentage of winning trades"
    )
    
    # P&L metrics
    gross_profit: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )
    
    gross_loss: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )
    
    net_profit: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    
    profit_factor: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Gross profit / Gross loss"
    )
    
    # Average trade metrics
    avg_trade_pnl: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    
    avg_winning_trade: Mapped[Optional[float]] = mapped_column(
        Float
    )
    
    avg_losing_trade: Mapped[Optional[float]] = mapped_column(
        Float
    )
    
    largest_win: Mapped[Optional[float]] = mapped_column(
        Float
    )
    
    largest_loss: Mapped[Optional[float]] = mapped_column(
        Float
    )
    
    # Risk metrics
    max_drawdown_pct: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Maximum drawdown percentage"
    )
    
    max_drawdown_dollars: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Risk-adjusted return metric"
    )
    
    sortino_ratio: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Downside risk-adjusted return"
    )
    
    calmar_ratio: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Return to max drawdown ratio"
    )
    
    # Volatility metrics
    volatility: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Portfolio volatility (standard deviation of returns)"
    )
    
    # Trade duration
    avg_trade_duration_hours: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Average trade holding period in hours"
    )
    
    # Exposure metrics
    market_exposure_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Percentage of time capital was invested"
    )
    
    # Equity curve data (stored as JSON array)
    equity_curve: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Daily equity curve data points"
    )
    
    # Drawdown data
    drawdown_periods: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="Significant drawdown periods with dates and amounts"
    )
    
    # Monthly returns
    monthly_returns: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="Monthly return breakdown"
    )
    
    # Additional metrics
    additional_metrics: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="Additional strategy-specific metrics"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    backtest = relationship("Backtest", back_populates="result")
    
    def __repr__(self) -> str:
        return f"<BacktestResult(id={self.id}, backtest_id={self.backtest_id})>"


class BacktestTrade(Base):
    """
    Individual trades executed during backtest.
    Complete trade history for analysis.
    """
    
    __tablename__ = "backtest_trades"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # Foreign key
    backtest_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("backtests.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Trade details
    symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True
    )
    
    side: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="buy or sell"
    )
    
    quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    
    entry_price: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    
    exit_price: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Exit price if position closed"
    )
    
    entry_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    
    exit_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        index=True
    )
    
    # Trade P&L
    pnl: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Profit/loss for this trade"
    )
    
    pnl_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="P&L as percentage of entry value"
    )
    
    # Costs
    commission: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )
    
    slippage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )
    
    # Trade duration
    duration_hours: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Trade holding period in hours"
    )
    
    # Signal information
    entry_signal: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="Signal that triggered entry"
    )
    
    exit_signal: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="Signal that triggered exit"
    )
    
    # Indicator values at entry
    indicators_at_entry: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="Technical indicator values at trade entry"
    )
    
    # Trade status
    is_open: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether trade is still open"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    backtest = relationship("Backtest", back_populates="trades")
    
    def __repr__(self) -> str:
        return f"<BacktestTrade(id={self.id}, symbol={self.symbol}, side={self.side})>"
