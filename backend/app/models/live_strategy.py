"""
Live Strategy models for automated trading.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from app.models.base import Base
from app.models.enums import SignalType, LiveStrategyStatus


class LiveStrategy(Base):
    """
    Live trading strategy configuration for automated trading.
    
    This model represents a strategy that runs continuously in the background,
    monitoring market conditions and automatically executing trades.
    """
    __tablename__ = "live_strategies"
    
    __table_args__ = (
        Index('idx_live_strategies_user_status', 'user_id', 'status'),
    )
    
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
    
    # Configuration
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    symbols: Mapped[list] = mapped_column(JSON, nullable=False, comment="List of symbols to monitor")
    status: Mapped[LiveStrategyStatus] = mapped_column(
        SQLEnum(LiveStrategyStatus, name="livestrategystatusenum", values_callable=lambda x: [e.value for e in x]),
        default=LiveStrategyStatus.STOPPED,
        nullable=False,
        index=True
    )
    check_interval: Mapped[int] = mapped_column(Integer, default=300, nullable=False, comment="seconds")
    auto_execute: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Risk Parameters
    max_position_size: Mapped[Optional[float]] = mapped_column(Float, comment="Maximum $ per position")
    max_positions: Mapped[int] = mapped_column(Integer, default=5, comment="Max concurrent positions")
    daily_loss_limit: Mapped[Optional[float]] = mapped_column(Float, comment="Max daily loss $")
    position_size_pct: Mapped[float] = mapped_column(Float, default=0.02, comment="% of portfolio per position")
    
    # State Tracking
    last_check: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_signal: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    state: Mapped[dict] = mapped_column(JSON, default=dict, comment="Strategy state data")
    error_message: Mapped[Optional[str]] = mapped_column(String(1000))
    
    # Metrics
    total_signals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    executed_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_positions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    win_rate: Mapped[Optional[float]] = mapped_column(Float)
    total_pnl: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
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
    user = relationship("User")
    strategy = relationship("Strategy")
    signals = relationship("SignalHistory", back_populates="live_strategy", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<LiveStrategy(id={self.id}, name={self.name}, status={self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "strategy_id": self.strategy_id,
            "name": self.name,
            "symbols": self.symbols,
            "status": self.status.value if self.status else None,
            "check_interval": self.check_interval,
            "auto_execute": self.auto_execute,
            "max_position_size": self.max_position_size,
            "max_positions": self.max_positions,
            "daily_loss_limit": self.daily_loss_limit,
            "position_size_pct": self.position_size_pct,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_signal": self.last_signal.isoformat() if self.last_signal else None,
            "error_message": self.error_message,
            "total_signals": self.total_signals,
            "executed_trades": self.executed_trades,
            "current_positions": self.current_positions,
            "win_rate": self.win_rate,
            "total_pnl": self.total_pnl,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SignalHistory(Base):
    """
    Historical record of detected trading signals.
    
    Tracks all signals detected by live strategies, whether they were
    executed or not, along with market conditions at the time.
    """
    __tablename__ = "signal_history"
    
    __table_args__ = (
        Index('idx_signal_history_strategy_time', 'live_strategy_id', 'timestamp'),
        Index('idx_signal_history_symbol_time', 'symbol', 'timestamp'),
    )
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # Foreign key
    live_strategy_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("live_strategies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Signal Details
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    signal_type: Mapped[SignalType] = mapped_column(
        SQLEnum(SignalType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    signal_strength: Mapped[Optional[float]] = mapped_column(Float, comment="Confidence score 0-1")
    
    # Market Conditions
    price: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[Optional[float]] = mapped_column(Float)
    indicators: Mapped[Optional[dict]] = mapped_column(JSON, comment="Technical indicators at signal time")
    
    # Execution
    executed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    execution_price: Mapped[Optional[float]] = mapped_column(Float)
    order_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("orders.id", ondelete="SET NULL")
    )
    execution_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    execution_error: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    live_strategy = relationship("LiveStrategy", back_populates="signals")
    order = relationship("Order")
    
    def __repr__(self) -> str:
        return f"<SignalHistory(symbol={self.symbol}, signal_type={self.signal_type}, executed={self.executed})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "live_strategy_id": self.live_strategy_id,
            "symbol": self.symbol,
            "signal_type": self.signal_type.value if self.signal_type else None,
            "signal_strength": self.signal_strength,
            "price": self.price,
            "volume": self.volume,
            "indicators": self.indicators,
            "executed": self.executed,
            "execution_price": self.execution_price,
            "order_id": self.order_id,
            "execution_time": self.execution_time.isoformat() if self.execution_time else None,
            "execution_error": self.execution_error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
