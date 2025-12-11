"""
Portfolio analytics models.
Stores portfolio snapshots, performance metrics, and tax lot tracking.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from app.models.base import Base


class PortfolioSnapshot(Base):
    """
    Point-in-time snapshot of portfolio state.
    
    Used for tracking portfolio history and computing performance metrics.
    """
    
    __tablename__ = "portfolio_snapshots"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Foreign key
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Snapshot timestamp
    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    
    # Portfolio values
    total_equity: Mapped[float] = mapped_column(Float, nullable=False)
    cash_balance: Mapped[float] = mapped_column(Float, nullable=False)
    positions_value: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Daily metrics
    daily_pnl: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    daily_return_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Cumulative metrics
    total_pnl: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_return_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Position counts
    num_positions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    num_long_positions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    num_short_positions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    user = relationship("User", backref="portfolio_snapshots")
    
    def __repr__(self) -> str:
        return f"<PortfolioSnapshot(id={self.id}, date={self.snapshot_date}, equity={self.total_equity})>"


class PerformanceMetrics(Base):
    """
    Computed performance metrics for a time period.
    
    Stores pre-calculated risk/return metrics for efficient querying.
    """
    
    __tablename__ = "performance_metrics"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Foreign key
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Time period
    period: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Period type: daily, weekly, monthly, yearly, all_time"
    )
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    # Return metrics
    total_return: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_return_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    annualized_return: Mapped[Optional[float]] = mapped_column(Float)
    
    # Risk metrics
    volatility: Mapped[Optional[float]] = mapped_column(Float)
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(Float)
    sortino_ratio: Mapped[Optional[float]] = mapped_column(Float)
    calmar_ratio: Mapped[Optional[float]] = mapped_column(Float)
    
    # Drawdown metrics
    max_drawdown: Mapped[Optional[float]] = mapped_column(Float)
    max_drawdown_pct: Mapped[Optional[float]] = mapped_column(Float)
    current_drawdown: Mapped[Optional[float]] = mapped_column(Float)
    current_drawdown_pct: Mapped[Optional[float]] = mapped_column(Float)
    
    # Trade statistics
    total_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    winning_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    losing_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    win_rate: Mapped[Optional[float]] = mapped_column(Float)
    
    # Trade P&L
    avg_win: Mapped[Optional[float]] = mapped_column(Float)
    avg_loss: Mapped[Optional[float]] = mapped_column(Float)
    profit_factor: Mapped[Optional[float]] = mapped_column(Float)
    
    # Trade breakdown
    num_trades_long: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    num_trades_short: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_holding_period_days: Mapped[Optional[float]] = mapped_column(Float)
    
    # Benchmark comparison
    benchmark_return: Mapped[Optional[float]] = mapped_column(Float)
    benchmark_return_pct: Mapped[Optional[float]] = mapped_column(Float)
    alpha: Mapped[Optional[float]] = mapped_column(Float)
    beta: Mapped[Optional[float]] = mapped_column(Float)
    
    # Additional data
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="Additional strategy-specific metrics"
    )
    
    # Timestamps
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
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
    user = relationship("User", backref="performance_metrics")
    
    def __repr__(self) -> str:
        return f"<PerformanceMetrics(id={self.id}, period={self.period}, return={self.total_return_pct}%)>"


class TaxLot(Base):
    """
    Tax lot tracking for positions.
    
    Implements FIFO/LIFO/specific lot identification for tax reporting.
    """
    
    __tablename__ = "tax_lots"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Foreign key
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Asset details
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    
    # Acquisition details
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    acquisition_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    acquisition_price: Mapped[float] = mapped_column(Float, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Disposition details (if sold)
    disposition_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    disposition_price: Mapped[Optional[float]] = mapped_column(Float)
    total_proceeds: Mapped[Optional[float]] = mapped_column(Float)
    
    # Gain/Loss calculation
    realized_gain_loss: Mapped[Optional[float]] = mapped_column(Float)
    holding_period_days: Mapped[Optional[int]] = mapped_column(Integer)
    is_long_term: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        comment="True if held > 1 year at disposition"
    )
    
    # Lot status
    status: Mapped[str] = mapped_column(
        String(20),
        default="open",
        nullable=False,
        index=True,
        comment="open, closed, partial"
    )
    remaining_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Trade references
    acquisition_trade_id: Mapped[Optional[str]] = mapped_column(String(36))
    disposition_trade_id: Mapped[Optional[str]] = mapped_column(String(36))
    
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
    user = relationship("User", backref="tax_lots")
    
    def __repr__(self) -> str:
        return f"<TaxLot(id={self.id}, symbol={self.symbol}, qty={self.quantity}, status={self.status})>"
    
    @property
    def is_closed(self) -> bool:
        """Check if the tax lot is completely sold."""
        return self.status == "closed"
    
    @property
    def unrealized_gain_loss(self) -> Optional[float]:
        """Calculate unrealized gain/loss if lot is still open."""
        if self.is_closed:
            return None
        # Would need current price to calculate - return None for now
        return None
