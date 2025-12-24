"""
Trade audit logging service.
Records all trading decisions, signals, and executions.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, DateTime, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base

logger = logging.getLogger(__name__)


class TradeAuditLog(Base):
    """Audit log for all trading activities."""
    __tablename__ = "trade_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    user_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)  # signal, order, fill, error
    strategy_id = Column(String, nullable=True, index=True)
    symbol = Column(String, nullable=True, index=True)
    side = Column(String, nullable=True)  # buy, sell
    quantity = Column(Float, nullable=True)
    price = Column(Float, nullable=True)
    order_id = Column(String, nullable=True)
    details = Column(JSON, default={})


class TradeAuditService:
    """Service for recording trade audit logs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_signal(
        self,
        user_id: str,
        strategy_id: str,
        symbol: str,
        signal_type: str,
        price: float,
        strength: float,
        indicators: Dict[str, Any]
    ):
        """Log a trading signal."""
        log = TradeAuditLog(
            user_id=user_id,
            event_type="signal",
            strategy_id=strategy_id,
            symbol=symbol,
            side=signal_type.lower() if signal_type in ["BUY", "SELL"] else None,
            price=price,
            details={
                "signal_type": signal_type,
                "strength": strength,
                "indicators": indicators
            }
        )
        self.db.add(log)
        await self.db.commit()
        logger.info(f"Audit: Signal {signal_type} for {symbol} @ {price}")

    async def log_order(
        self,
        user_id: str,
        strategy_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        order_id: str,
        order_type: str = "market"
    ):
        """Log an order placement."""
        log = TradeAuditLog(
            user_id=user_id,
            event_type="order",
            strategy_id=strategy_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            order_id=order_id,
            details={"order_type": order_type}
        )
        self.db.add(log)
        await self.db.commit()
        logger.info(f"Audit: Order {order_id} - {side} {quantity} {symbol}")

    async def log_error(
        self,
        user_id: str,
        error_type: str,
        error_message: str,
        strategy_id: Optional[str] = None,
        symbol: Optional[str] = None
    ):
        """Log an error event."""
        log = TradeAuditLog(
            user_id=user_id,
            event_type="error",
            strategy_id=strategy_id,
            symbol=symbol,
            details={
                "error_type": error_type,
                "error_message": error_message
            }
        )
        self.db.add(log)
        await self.db.commit()
        logger.error(f"Audit: Error - {error_type}: {error_message}")


def get_trade_audit_service(db: AsyncSession) -> TradeAuditService:
    """Get trade audit service instance."""
    return TradeAuditService(db)
