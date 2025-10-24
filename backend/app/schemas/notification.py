"""
Notification schemas for request/response validation.
"""
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.notification import (
    NotificationType,
    NotificationChannel,
    NotificationPriority
)


class NotificationBase(BaseModel):
    """Base notification schema."""
    type: NotificationType
    priority: NotificationPriority = Field(default=NotificationPriority.MEDIUM)
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    data: Optional[dict[str, Any]] = None
    strategy_id: Optional[str] = None
    order_id: Optional[str] = None
    trade_id: Optional[str] = None


class NotificationCreate(NotificationBase):
    """Schema for creating a notification."""
    pass


class NotificationResponse(NotificationBase):
    """Schema for notification response."""
    id: str
    user_id: str
    is_read: bool
    read_at: Optional[datetime]
    sent_via: list[str]
    delivered_at: Optional[datetime]
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class NotificationUpdate(BaseModel):
    """Schema for updating a notification."""
    is_read: Optional[bool] = None


class NotificationPreferenceBase(BaseModel):
    """Base notification preference schema."""
    notification_type: NotificationType
    channel: NotificationChannel
    is_enabled: bool = Field(default=True)
    min_priority: NotificationPriority = Field(default=NotificationPriority.LOW)
    quiet_hours_enabled: bool = Field(default=False)
    quiet_start_hour: Optional[int] = Field(None, ge=0, le=23)
    quiet_end_hour: Optional[int] = Field(None, ge=0, le=23)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    webhook_url: Optional[str] = Field(None, max_length=512)


class NotificationPreferenceCreate(NotificationPreferenceBase):
    """Schema for creating notification preference."""
    pass


class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating notification preference."""
    is_enabled: Optional[bool] = None
    min_priority: Optional[NotificationPriority] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_start_hour: Optional[int] = Field(None, ge=0, le=23)
    quiet_end_hour: Optional[int] = Field(None, ge=0, le=23)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    webhook_url: Optional[str] = Field(None, max_length=512)


class NotificationPreferenceResponse(NotificationPreferenceBase):
    """Schema for notification preference response."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationStats(BaseModel):
    """Schema for notification statistics."""
    total_unread: int
    by_type: dict[str, int]
    by_priority: dict[str, int]
    recent_count: int
