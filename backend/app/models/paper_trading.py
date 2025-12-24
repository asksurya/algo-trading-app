"""
Paper trading models.
Stores paper trading accounts, positions, and trades.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from app.models.base import Base


class PaperAccount(Base):
    """
    Paper trading account for a user.
    """

    __tablename__ = "paper_accounts"

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
        unique=True,
        index=True
    )

    # Account details
    cash_balance: Mapped[float] = mapped_column(Float, default=100000.0, nullable=False)
    initial_balance: Mapped[float] = mapped_column(Float, default=100000.0, nullable=False)

    # Performance metrics
    total_pnl: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_return_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

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
    positions: Mapped[List["PaperPosition"]] = relationship(
        "PaperPosition",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    trades: Mapped[List["PaperTrade"]] = relationship(
        "PaperTrade",
        back_populates="account",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PaperAccount(id={self.id}, user_id={self.user_id}, balance={self.cash_balance})>"


class PaperPosition(Base):
    """
    Paper trading position.
    """

    __tablename__ = "paper_positions"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Foreign key
    account_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("paper_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Position details
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    qty: Mapped[float] = mapped_column(Float, nullable=False)
    avg_price: Mapped[float] = mapped_column(Float, nullable=False)

    # Stop-loss and take-profit levels (optional)
    stop_loss_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    take_profit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

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
    account = relationship("PaperAccount", back_populates="positions")

    def __repr__(self) -> str:
        return f"<PaperPosition(id={self.id}, symbol={self.symbol}, qty={self.qty})>"


class PaperTrade(Base):
    """
    Paper trading trade execution.
    """

    __tablename__ = "paper_trades"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Foreign key
    account_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("paper_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Trade details
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    qty: Mapped[float] = mapped_column(Float, nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # 'buy' or 'sell'
    price: Mapped[float] = mapped_column(Float, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)

    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    account = relationship("PaperAccount", back_populates="trades")

    def __repr__(self) -> str:
        return f"<PaperTrade(id={self.id}, symbol={self.symbol}, side={self.side}, qty={self.qty})>"
