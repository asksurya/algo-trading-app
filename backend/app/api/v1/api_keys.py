"""
API Key Management endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.api_key import ApiKey, ApiKeyAuditLog, ApiKeyStatus, BrokerType
from app.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyUpdate,
    ApiKeyResponse,
    ApiKeyWithSecret,
    ApiKeyRotateRequest,
    ApiKeyVerifyResponse,
    ApiKeyAuditLogResponse
)
from app.services.encryption_service import get_encryption_service
from app.dependencies import get_current_active_user

router = APIRouter()


def _create_audit_log(
    api_key_id: str,
    user_id: str,
    action: str,
    description: str,
    success: bool,
    request: Request,
    error_message: Optional[str] = None
) -> ApiKeyAuditLog:
    """Create an audit log entry"""
    return ApiKeyAuditLog(
        api_key_id=api_key_id,
        user_id=user_id,
        action=action,
        description=description,
        success=success,
        error_message=error_message,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )


@router.post("", response_model=ApiKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: ApiKeyCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new encrypted API key.
    Returns the plaintext secret only once during creation.
    """
    encryption_service = get_encryption_service()
    
    try:
        # Encrypt the credentials
        encrypted_key = encryption_service.encrypt_api_key(key_data.api_key.get_secret_value())
        encrypted_secret = encryption_service.encrypt_api_key(key_data.api_secret.get_secret_value())
        
        # Create API key record
        api_key = ApiKey(
            user_id=current_user.id,
            broker=key_data.broker,
            name=key_data.name,
            description=key_data.description,
            encrypted_api_key=encrypted_key,
            encrypted_api_secret=encrypted_secret,
            account_id=key_data.account_id,
            base_url=key_data.base_url,
            is_paper_trading=key_data.is_paper_trading,
            is_default=key_data.is_default
        )
        # Only set expires_at if provided
        if hasattr(key_data, 'expires_at') and key_data.expires_at:
            api_key.expires_at = key_data.expires_at
        
        # If this is set as default, unset other defaults
        if key_data.is_default:
            result = await db.execute(
                select(ApiKey).where(
                    and_(
                        ApiKey.user_id == current_user.id,
                        ApiKey.broker == key_data.broker,
                        ApiKey.is_default == True
                    )
                )
            )
            existing_defaults = result.scalars().all()
            for existing in existing_defaults:
                existing.is_default = False
        
        db.add(api_key)
        await db.flush()  # Flush to generate ID
        
        # Create audit log
        audit_log = _create_audit_log(
            api_key_id=api_key.id,
            user_id=current_user.id,
            action="CREATE",
            description=f"Created API key '{key_data.name}' for broker {key_data.broker}",
            success=True,
            request=request
        )
        db.add(audit_log)
        
        await db.commit()
        await db.refresh(api_key)
        
        # Return response with plaintext credentials (only time they're exposed)
        return ApiKeyWithSecret(
            id=api_key.id,
            user_id=api_key.user_id,
            broker=api_key.broker,
            name=api_key.name,
            description=api_key.description,
            account_id=api_key.account_id,
            base_url=api_key.base_url,
            is_paper_trading=api_key.is_paper_trading,
            status=api_key.status,
            is_default=api_key.is_default,
            last_used_at=api_key.last_used_at,
            last_verified_at=api_key.last_verified_at,
            usage_count=api_key.usage_count,
            error_count=api_key.error_count,
            expires_at=api_key.expires_at,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at,
            api_key=key_data.api_key.get_secret_value(),  # Plaintext
            api_secret=key_data.api_secret.get_secret_value()  # Plaintext
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get("", response_model=List[ApiKeyResponse])
async def list_api_keys(
    broker: Optional[BrokerType] = None,
    status_filter: Optional[ApiKeyStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all API keys for the current user (without secrets)"""
    
    query = select(ApiKey).where(ApiKey.user_id == current_user.id)
    
    if broker:
        query = query.where(ApiKey.broker == broker)
    
    if status_filter:
        query = query.where(ApiKey.status == status_filter)
    
    query = query.order_by(ApiKey.created_at.desc())
    
    result = await db.execute(query)
    api_keys = result.scalars().all()
    
    return api_keys


@router.get("/{key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    key_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific API key (without secrets)"""
    
    result = await db.execute(
        select(ApiKey).where(
            and_(
                ApiKey.id == key_id,
                ApiKey.user_id == current_user.id
            )
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return api_key


@router.put("/{key_id}", response_model=ApiKeyResponse)
async def update_api_key(
    key_id: str,
    key_update: ApiKeyUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update API key metadata (not credentials)"""
    
    result = await db.execute(
        select(ApiKey).where(
            and_(
                ApiKey.id == key_id,
                ApiKey.user_id == current_user.id
            )
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Update fields
    update_data = key_update.model_dump(exclude_unset=True)
    
    # Handle default flag
    if update_data.get("is_default") and not api_key.is_default:
        # Unset other defaults for this broker
        result = await db.execute(
            select(ApiKey).where(
                and_(
                    ApiKey.user_id == current_user.id,
                    ApiKey.broker == api_key.broker,
                    ApiKey.is_default == True
                )
            )
        )
        existing_defaults = result.scalars().all()
        for existing in existing_defaults:
            existing.is_default = False
    
    for field, value in update_data.items():
        setattr(api_key, field, value)
    
    # Create audit log
    audit_log = _create_audit_log(
        api_key_id=api_key.id,
        user_id=current_user.id,
        action="UPDATE",
        description=f"Updated API key '{api_key.name}'",
        success=True,
        request=request
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(api_key)
    
    return api_key


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke (soft delete) an API key"""
    
    result = await db.execute(
        select(ApiKey).where(
            and_(
                ApiKey.id == key_id,
                ApiKey.user_id == current_user.id
            )
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Soft delete by marking as revoked
    api_key.status = ApiKeyStatus.REVOKED
    api_key.revoked_at = datetime.now(datetime.UTC)
    
    # Create audit log
    audit_log = _create_audit_log(
        api_key_id=api_key.id,
        user_id=current_user.id,
        action="REVOKE",
        description=f"Revoked API key '{api_key.name}'",
        success=True,
        request=request
    )
    db.add(audit_log)
    
    await db.commit()


@router.post("/{key_id}/rotate", response_model=ApiKeyWithSecret)
async def rotate_api_key(
    key_id: str,
    rotation_data: ApiKeyRotateRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Rotate API key credentials"""
    
    result = await db.execute(
        select(ApiKey).where(
            and_(
                ApiKey.id == key_id,
                ApiKey.user_id == current_user.id
            )
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    encryption_service = get_encryption_service()
    
    try:
        # Encrypt new credentials
        encrypted_key = encryption_service.encrypt_api_key(rotation_data.new_api_key.get_secret_value())
        encrypted_secret = encryption_service.encrypt_api_key(rotation_data.new_api_secret.get_secret_value())
        
        # Update credentials
        api_key.encrypted_api_key = encrypted_key
        api_key.encrypted_api_secret = encrypted_secret
        api_key.last_rotated_at = datetime.now(datetime.UTC)
        api_key.encryption_version += 1
        
        # Create audit log
        audit_log = _create_audit_log(
            api_key_id=api_key.id,
            user_id=current_user.id,
            action="ROTATE",
            description=f"Rotated credentials for API key '{api_key.name}'",
            success=True,
            request=request
        )
        db.add(audit_log)
        
        await db.commit()
        await db.refresh(api_key)
        
        # Return with new plaintext credentials
        return ApiKeyWithSecret(
            id=api_key.id,
            user_id=api_key.user_id,
            broker=api_key.broker,
            name=api_key.name,
            description=api_key.description,
            account_id=api_key.account_id,
            base_url=api_key.base_url,
            is_paper_trading=api_key.is_paper_trading,
            status=api_key.status,
            is_default=api_key.is_default,
            last_used_at=api_key.last_used_at,
            last_verified_at=api_key.last_verified_at,
            usage_count=api_key.usage_count,
            error_count=api_key.error_count,
            expires_at=api_key.expires_at,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at,
            api_key=rotation_data.new_api_key.get_secret_value(),
            api_secret=rotation_data.new_api_secret.get_secret_value()
        )
        
    except Exception as e:
        # Create failure audit log
        audit_log = _create_audit_log(
            api_key_id=api_key.id,
            user_id=current_user.id,
            action="ROTATE",
            description=f"Failed to rotate credentials for API key '{api_key.name}'",
            success=False,
            request=request,
            error_message=str(e)
        )
        db.add(audit_log)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rotate API key: {str(e)}"
        )


@router.post("/{key_id}/verify", response_model=ApiKeyVerifyResponse)
async def verify_api_key(
    key_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify API key is valid with the broker"""
    
    result = await db.execute(
        select(ApiKey).where(
            and_(
                ApiKey.id == key_id,
                ApiKey.user_id == current_user.id
            )
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    encryption_service = get_encryption_service()
    
    try:
        # Decrypt credentials
        plaintext_key = encryption_service.decrypt_api_key(api_key.encrypted_api_key)
        plaintext_secret = encryption_service.decrypt_api_key(api_key.encrypted_api_secret)
        
        # TODO: Actually verify with broker API
        # For now, just check if decryption worked
        is_valid = bool(plaintext_key and plaintext_secret)
        
        # Update last verified
        api_key.last_verified_at = datetime.now(datetime.UTC)
        
        if is_valid:
            api_key.status = ApiKeyStatus.ACTIVE
            api_key.error_count = 0
            api_key.last_error = None
        else:
            api_key.error_count += 1
            api_key.last_error = "Verification failed"
        
        # Create audit log
        audit_log = _create_audit_log(
            api_key_id=api_key.id,
            user_id=current_user.id,
            action="VERIFY",
            description=f"Verified API key '{api_key.name}'",
            success=is_valid,
            request=request,
            error_message=None if is_valid else "Verification failed"
        )
        db.add(audit_log)
        
        await db.commit()
        
        return ApiKeyVerifyResponse(
            is_valid=is_valid,
            verified_at=api_key.last_verified_at,
            message="API key is valid" if is_valid else "API key verification failed"
        )
        
    except Exception as e:
        # Create failure audit log
        audit_log = _create_audit_log(
            api_key_id=api_key.id,
            user_id=current_user.id,
            action="VERIFY",
            description=f"Failed to verify API key '{api_key.name}'",
            success=False,
            request=request,
            error_message=str(e)
        )
        db.add(audit_log)
        await db.commit()
        
        return ApiKeyVerifyResponse(
            is_valid=False,
            verified_at=datetime.now(datetime.UTC),
            message=f"Verification error: {str(e)}"
        )


@router.get("/{key_id}/audit-logs", response_model=List[ApiKeyAuditLogResponse])
async def get_audit_logs(
    key_id: str,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs for an API key"""
    
    # Verify ownership
    result = await db.execute(
        select(ApiKey).where(
            and_(
                ApiKey.id == key_id,
                ApiKey.user_id == current_user.id
            )
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Get audit logs
    result = await db.execute(
        select(ApiKeyAuditLog)
        .where(ApiKeyAuditLog.api_key_id == key_id)
        .order_by(ApiKeyAuditLog.created_at.desc())
        .limit(limit)
    )
    audit_logs = result.scalars().all()
    
    return audit_logs
