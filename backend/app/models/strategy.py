"""
Strategy configuration models.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from app.models.base import Base


class Strategy(Base):
    """Strategy configuration model."""
    
    __tablename__ = "strategies"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Strategy details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    strategy_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Type of strategy (e.g., 'bollinger_bands', 'momentum', 'ml_strategy')"
    )
    
    # Configuration stored as JSON
    parameters: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Strategy-specific parameters as JSON"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_backtested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Performance metrics (from backtesting)
    backtest_results: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="Backtest results and performance metrics"
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
    risk_rules = relationship("RiskRule", back_populates="strategy", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Strategy(id={self.id}, name={self.name}, type={self.strategy_type})>"


class StrategyTicker(Base):
    """Association table for strategies and tickers they trade."""
    
    __tablename__ = "strategy_tickers"
    __table_args__ = (
        UniqueConstraint('strategy_id', 'ticker', name='uq_strategy_ticker'),
    )
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    strategy_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("strategies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    ticker: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True
    )
    
    # Configuration per ticker
    allocation_percent: Mapped[Optional[float]] = mapped_column(
        comment="Percentage of capital to allocate to this ticker"
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<StrategyTicker(strategy_id={self.strategy_id}, ticker={self.ticker})>"
