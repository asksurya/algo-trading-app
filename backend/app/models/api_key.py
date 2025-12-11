"""
API key management model for broker integrations.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Enum as SQLEnum, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from app.models.base import Base
from app.models.enums import BrokerType, ApiKeyStatus



class ApiKey(Base):
    """Encrypted API keys for broker integrations."""
    
    __tablename__ = "api_keys"
    
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
    
    # Broker information
    broker: Mapped[BrokerType] = mapped_column(
        SQLEnum(BrokerType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Encrypted credentials
    encrypted_api_key: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_api_secret: Mapped[str] = mapped_column(Text, nullable=False)
    encryption_version: Mapped[int] = mapped_column(default=1, nullable=False)
    
    # Additional fields for specific brokers
    account_id: Mapped[Optional[str]] = mapped_column(String(255))
    base_url: Mapped[Optional[str]] = mapped_column(String(512))
    is_paper_trading: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Status
    status: Mapped[ApiKeyStatus] = mapped_column(
        SQLEnum(ApiKeyStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ApiKeyStatus.ACTIVE
    )
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Usage tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    usage_count: Mapped[int] = mapped_column(default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(default=0, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    
    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Rotation tracking
    rotation_history: Mapped[Optional[str]] = mapped_column(Text)
    last_rotated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
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
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self) -> str:
        return f"<ApiKey(id={self.id}, broker={self.broker}, name={self.name})>"


class ApiKeyAuditLog(Base):
    """Audit log for API key usage and changes."""
    
    __tablename__ = "api_key_audit_logs"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # Foreign keys
    api_key_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("api_keys.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Audit details
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    
    # Result
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Relationships
    api_key = relationship("ApiKey")
    user = relationship("User")
    
    def __repr__(self) -> str:
        return f"<ApiKeyAuditLog(id={self.id}, action={self.action}, success={self.success})>"
