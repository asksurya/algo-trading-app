"""
API key schemas for request/response validation.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, SecretStr

from app.models.api_key import BrokerType, ApiKeyStatus


class ApiKeyBase(BaseModel):
    """Base API key schema."""
    broker: BrokerType
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    account_id: Optional[str] = Field(None, max_length=255)
    base_url: Optional[str] = Field(None, max_length=512)
    is_paper_trading: bool = Field(default=True)
    is_default: bool = Field(default=False)


class ApiKeyCreate(ApiKeyBase):
    """Schema for creating an API key."""
    api_key: SecretStr = Field(..., description="API key (will be encrypted)")
    api_secret: SecretStr = Field(..., description="API secret (will be encrypted)")


class ApiKeyUpdate(BaseModel):
    """Schema for updating an API key."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    account_id: Optional[str] = Field(None, max_length=255)
    base_url: Optional[str] = Field(None, max_length=512)
    is_paper_trading: Optional[bool] = None
    is_default: Optional[bool] = None
    status: Optional[ApiKeyStatus] = None


class ApiKeyResponse(ApiKeyBase):
    """Schema for API key response (no sensitive data)."""
    id: str
    user_id: str
    status: ApiKeyStatus
    last_used_at: Optional[datetime]
    last_verified_at: Optional[datetime]
    usage_count: int
    error_count: int
    last_error: Optional[str]
    expires_at: Optional[datetime]
    last_rotated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    revoked_at: Optional[datetime]

    class Config:
        from_attributes = True


class ApiKeyWithSecret(ApiKeyResponse):
    """Schema for API key with plaintext credentials (only returned on creation/rotation)."""
    api_key: str = Field(..., description="Plaintext API key")
    api_secret: str = Field(..., description="Plaintext API secret")
    last_error: Optional[str] = None
    last_rotated_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None


class ApiKeyRotateRequest(BaseModel):
    """Schema for rotating API keys."""
    new_api_key: SecretStr = Field(..., description="New API key")
    new_api_secret: SecretStr = Field(..., description="New API secret")


class ApiKeyVerifyResponse(BaseModel):
    """Schema for API key verification response."""
    is_valid: bool
    verified_at: datetime
    message: str


class ApiKeyAuditLogResponse(BaseModel):
    """Schema for API key audit log response."""
    id: str
    api_key_id: str
    user_id: str
    action: str
    description: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    success: bool
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyStats(BaseModel):
    """Schema for API key usage statistics."""
    total_keys: int
    active_keys: int
    inactive_keys: int
    expired_keys: int
    revoked_keys: int
    by_broker: dict[str, int]
    total_usage: int
    total_errors: int
