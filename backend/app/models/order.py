"""
Order history database model.
Stores order information for tracking and analytics.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Boolean, DateTime, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base, SoftDeleteMixin
from app.models.enums import OrderSideEnum, OrderTypeEnum, OrderStatusEnum


class Order(Base, SoftDeleteMixin):
    """
    Order history model.
    
    Stores all order information for tracking, analytics, and audit purposes.
    Orders are synced from Alpaca and stored locally.
    Supports soft delete for data retention.
    """
    __tablename__ = "orders"
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_orders_user_created', 'user_id', 'created_at'),
        Index('idx_orders_symbol_created', 'symbol', 'created_at'),
        Index('idx_orders_status_created', 'status', 'created_at'),
        Index('idx_orders_user_symbol', 'user_id', 'symbol'),
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
    
    # Alpaca order details
    alpaca_order_id: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        nullable=False, 
        index=True
    )
    client_order_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Order details
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    side: Mapped[OrderSideEnum] = mapped_column(
        SQLEnum(OrderSideEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    order_type: Mapped[OrderTypeEnum] = mapped_column(
        SQLEnum(OrderTypeEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    time_in_force: Mapped[str] = mapped_column(
        String(10), 
        nullable=False,
        comment="day, gtc, ioc, fok, etc."
    )
    
    # Quantities and prices
    qty: Mapped[Optional[float]] = mapped_column(Float, comment="Null for notional orders")
    notional: Mapped[Optional[float]] = mapped_column(Float, comment="For fractional shares")
    filled_qty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    limit_price: Mapped[Optional[float]] = mapped_column(Float)
    stop_price: Mapped[Optional[float]] = mapped_column(Float)
    filled_avg_price: Mapped[Optional[float]] = mapped_column(Float)
    
    # Trailing stop fields
    trail_price: Mapped[Optional[float]] = mapped_column(Float)
    trail_percent: Mapped[Optional[float]] = mapped_column(Float)
    hwm: Mapped[Optional[float]] = mapped_column(Float, comment="High water mark")
    
    # Status and timestamps
    status: Mapped[OrderStatusEnum] = mapped_column(
        SQLEnum(OrderStatusEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    filled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    replaced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Order relationships (for replacements)
    replaced_by: Mapped[Optional[str]] = mapped_column(String(100))
    replaces: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Additional fields
    extended_hours: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    asset_class: Mapped[str] = mapped_column(String(20), default="us_equity", nullable=False)
    asset_id: Mapped[Optional[str]] = mapped_column(String(100))
    
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
    user = relationship("User", back_populates="orders")
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, symbol={self.symbol}, side={self.side}, status={self.status})>"
    
    def to_dict(self) -> dict:
        """Convert order to dictionary."""
        return {
            "id": str(self.id),
            "alpaca_order_id": self.alpaca_order_id,
            "client_order_id": self.client_order_id,
            "user_id": str(self.user_id),
            "symbol": self.symbol,
            "side": self.side.value if self.side else None,
            "order_type": self.order_type.value if self.order_type else None,
            "time_in_force": self.time_in_force,
            "qty": self.qty,
            "notional": self.notional,
            "filled_qty": self.filled_qty,
            "limit_price": self.limit_price,
            "stop_price": self.stop_price,
            "filled_avg_price": self.filled_avg_price,
            "trail_price": self.trail_price,
            "trail_percent": self.trail_percent,
            "hwm": self.hwm,
            "status": self.status.value if self.status else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "canceled_at": self.canceled_at.isoformat() if self.canceled_at else None,
            "expired_at": self.expired_at.isoformat() if self.expired_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "replaced_at": self.replaced_at.isoformat() if self.replaced_at else None,
            "replaced_by": self.replaced_by,
            "replaces": self.replaces,
            "extended_hours": self.extended_hours,
            "asset_class": self.asset_class,
            "asset_id": self.asset_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_deleted": self.is_deleted,
        }


class PositionSnapshot(Base):
    """
    Position snapshot model.
    
    Stores periodic snapshots of positions for analytics and performance tracking.
    """
    __tablename__ = "position_snapshots"
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_position_snapshots_user_time', 'user_id', 'snapshot_at'),
        Index('idx_position_snapshots_symbol_time', 'symbol', 'snapshot_at'),
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
    
    # Position details
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    qty: Mapped[float] = mapped_column(Float, nullable=False)
    side: Mapped[OrderSideEnum] = mapped_column(
        SQLEnum(OrderSideEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="long or short"
    )
    
    # Price information
    avg_entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float] = mapped_column(Float, nullable=False)
    market_value: Mapped[float] = mapped_column(Float, nullable=False)
    cost_basis: Mapped[float] = mapped_column(Float, nullable=False)
    
    # P&L information
    unrealized_pl: Mapped[float] = mapped_column(Float, nullable=False)
    unrealized_plpc: Mapped[float] = mapped_column(Float, nullable=False, comment="Percentage")
    
    # Snapshot metadata
    snapshot_at: Mapped[datetime] = mapped_column(
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
    user = relationship("User", back_populates="position_snapshots")
    
    def __repr__(self) -> str:
        return f"<PositionSnapshot(symbol={self.symbol}, qty={self.qty}, unrealized_pl={self.unrealized_pl})>"
    
    def to_dict(self) -> dict:
        """Convert position snapshot to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "symbol": self.symbol,
            "qty": self.qty,
            "side": self.side.value if self.side else None,
            "avg_entry_price": self.avg_entry_price,
            "current_price": self.current_price,
            "market_value": self.market_value,
            "cost_basis": self.cost_basis,
            "unrealized_pl": self.unrealized_pl,
            "unrealized_plpc": self.unrealized_plpc,
            "snapshot_at": self.snapshot_at.isoformat() if self.snapshot_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
