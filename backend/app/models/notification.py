"""
Notification models for alerts and user notifications.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Enum as SQLEnum, Text, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from app.models.base import Base
from app.models.enums import NotificationType, NotificationChannel, NotificationPriority



class Notification(Base):
    """User notifications and alerts."""
    
    __tablename__ = "notifications"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # Foreign key
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Notification details
    type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    priority: Mapped[NotificationPriority] = mapped_column(
        SQLEnum(NotificationPriority, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=NotificationPriority.MEDIUM
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Metadata
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Related entities
    strategy_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    trade_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Delivery status
    sent_via: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type={self.type}, title={self.title})>"


class NotificationPreference(Base):
    """User preferences for notification delivery."""
    
    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint('user_id', 'notification_type', 'channel', name='uq_user_notification_channel'),
    )
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # Foreign key
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Preference settings
    notification_type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        SQLEnum(NotificationChannel, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Filtering options
    min_priority: Mapped[NotificationPriority] = mapped_column(
        SQLEnum(NotificationPriority, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=NotificationPriority.LOW
    )
    
    # Quiet hours
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quiet_start_hour: Mapped[Optional[int]] = mapped_column(default=None)  # 0-23
    quiet_end_hour: Mapped[Optional[int]] = mapped_column(default=None)  # 0-23
    
    # Contact details
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    webhook_url: Mapped[Optional[str]] = mapped_column(String(512))
    
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
    user = relationship("User", back_populates="notification_preferences")
    
    def __repr__(self) -> str:
        return f"<NotificationPreference(id={self.id}, type={self.notification_type}, channel={self.channel})>"
