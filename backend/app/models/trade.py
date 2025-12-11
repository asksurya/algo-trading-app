"""
Trade and position tracking models.
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, DateTime, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import uuid

from app.models.base import Base, SoftDeleteMixin
from app.models.enums import TradeType, TradeStatus



class Trade(Base, SoftDeleteMixin):
    """Trade execution model with soft delete support."""
    
    __tablename__ = "trades"
    
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
    strategy_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("strategies.id", ondelete="SET NULL"),
        index=True
    )
    
    # Trade details
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    trade_type: Mapped[TradeType] = mapped_column(
        SQLEnum(TradeType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    status: Mapped[TradeStatus] = mapped_column(
        SQLEnum(TradeStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TradeStatus.PENDING,
        index=True
    )
    
    # Quantities and prices
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=8),
        nullable=False
    )
    filled_quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=8),
        default=Decimal("0"),
        nullable=False
    )
    price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=8),
        comment="Limit price, if applicable"
    )
    filled_avg_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=8),
        comment="Average filled price"
    )
    
    # Order details
    order_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="Broker order ID"
    )
    
    # P&L tracking
    realized_pnl: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=8),
        comment="Realized profit/loss"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    executed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        comment="When the trade was executed"
    )
    
    def __repr__(self) -> str:
        return f"<Trade(id={self.id}, ticker={self.ticker}, type={self.trade_type}, status={self.status})>"


class Position(Base):
    """Current position tracking model."""
    
    __tablename__ = "positions"
    
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
    strategy_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("strategies.id", ondelete="SET NULL"),
        index=True
    )
    
    # Position details
    ticker: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=8),
        nullable=False
    )
    avg_entry_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=8),
        nullable=False
    )
    current_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=8)
    )
    
    # P&L tracking
    unrealized_pnl: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=8)
    )
    realized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=8),
        default=Decimal("0"),
        nullable=False
    )
    
    # Timestamps
    opened_at: Mapped[datetime] = mapped_column(
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
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    
    def __repr__(self) -> str:
        return f"<Position(id={self.id}, ticker={self.ticker}, quantity={self.quantity})>"
