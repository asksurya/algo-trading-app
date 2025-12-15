"""
Paper trading models.
Stores paper trading accounts, positions, and trade history.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from app.models.base import Base


class PaperAccount(Base):
    """
    Paper trading account for a user.
    """
    __tablename__ = "paper_accounts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # Balance info
    cash_balance: Mapped[float] = mapped_column(Float, default=100000.0, nullable=False)
    initial_balance: Mapped[float] = mapped_column(Float, default=100000.0, nullable=False)

    # Performance metrics
    total_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    total_return_pct: Mapped[float] = mapped_column(Float, default=0.0)

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
    user = relationship("User", back_populates="paper_account")
    positions = relationship("PaperPosition", back_populates="account", cascade="all, delete-orphan")
    trades = relationship("PaperTrade", back_populates="account", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<PaperAccount(user_id={self.user_id}, cash={self.cash_balance})>"


class PaperPosition(Base):
    """
    Paper trading position.
    """
    __tablename__ = "paper_positions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    account_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("paper_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    qty: Mapped[float] = mapped_column(Float, nullable=False)
    avg_price: Mapped[float] = mapped_column(Float, nullable=False)

    # Market value tracking (updated periodically or on access)
    market_value: Mapped[float] = mapped_column(Float, default=0.0)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0)

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

    account = relationship("PaperAccount", back_populates="positions")

    def __repr__(self) -> str:
        return f"<PaperPosition(symbol={self.symbol}, qty={self.qty})>"


class PaperTrade(Base):
    """
    Paper trading trade history.
    """
    __tablename__ = "paper_trades"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    account_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("paper_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    qty: Mapped[float] = mapped_column(Float, nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # 'buy' or 'sell'
    price: Mapped[float] = mapped_column(Float, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    account = relationship("PaperAccount", back_populates="trades")

    def __repr__(self) -> str:
        return f"<PaperTrade(symbol={self.symbol}, side={self.side}, qty={self.qty})>"
