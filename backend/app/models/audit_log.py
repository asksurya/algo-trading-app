"""
Audit Log model.
"""
from typing import Dict, Any, Optional
from sqlalchemy import String, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import AuditEventType


class AuditLog(Base, TimestampMixin):
    """
    Audit log model for tracking system events.
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    event_type: Mapped[AuditEventType] = mapped_column(Enum(AuditEventType), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    metadata_data: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    severity: Mapped[str] = mapped_column(String, default="info", nullable=False)

    def __repr__(self) -> str:
        return f"<AuditLog(user_id={self.user_id}, event={self.event_type}, timestamp={self.created_at})>"
