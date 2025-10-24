"""
Notifications API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import time as datetime_time

from app.database import get_db
from app.models.user import User
from app.models.notification import (
    Notification,
    NotificationPreference,
    NotificationType,
    NotificationChannel,
    NotificationPriority
)
from app.schemas.notification import (
    NotificationResponse,
    NotificationPreferenceCreate,
    NotificationPreferenceUpdate,
    NotificationPreferenceResponse,
    NotificationStats
)
from app.services.notification_service import NotificationService
from app.dependencies import get_current_active_user

router = APIRouter()


@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    is_read: Optional[bool] = None,
    priority: Optional[NotificationPriority] = None,
    type_filter: Optional[NotificationType] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List notifications for the current user with optional filters"""
    
    query = select(Notification).where(Notification.user_id == current_user.id)
    
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)
    
    if priority:
        query = query.where(Notification.priority == priority)
    
    if type_filter:
        query = query.where(Notification.type == type_filter)
    
    query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return notifications


@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get notification statistics"""
    
    notification_service = NotificationService(db)
    stats = await notification_service.get_notification_stats(current_user.id)
    
    return NotificationStats(**stats)


@router.get("/preferences", response_model=List[NotificationPreferenceResponse])
async def list_notification_preferences(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all notification preferences for the current user"""
    
    result = await db.execute(
        select(NotificationPreference)
        .where(NotificationPreference.user_id == current_user.id)
        .order_by(NotificationPreference.notification_type)
    )
    preferences = result.scalars().all()
    
    return preferences


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific notification"""
    
    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == current_user.id
            )
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return notification


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a notification as read"""
    
    notification_service = NotificationService(db)
    success = await notification_service.mark_as_read(notification_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Return updated notification
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one()
    
    return notification


@router.put("/mark-all-read")
async def mark_all_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark all notifications as read"""
    
    notification_service = NotificationService(db)
    count = await notification_service.mark_all_as_read(current_user.id)
    
    return {"message": f"Marked {count} notifications as read"}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a notification"""
    
    notification_service = NotificationService(db)
    success = await notification_service.delete_notification(notification_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )


@router.delete("/clear-all")
async def clear_all_notifications(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete all read notifications"""
    
    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.user_id == current_user.id,
                Notification.is_read == True
            )
        )
    )
    notifications = result.scalars().all()
    
    count = 0
    for notification in notifications:
        await db.delete(notification)
        count += 1
    
    await db.commit()
    
    return {"message": f"Deleted {count} read notifications"}


# Notification Preferences


@router.post("/preferences", response_model=NotificationPreferenceResponse, status_code=status.HTTP_201_CREATED)
async def create_notification_preference(
    pref_data: NotificationPreferenceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new notification preference"""
    
    # Check if preference already exists for this type
    result = await db.execute(
        select(NotificationPreference).where(
            and_(
                NotificationPreference.user_id == current_user.id,
                NotificationPreference.notification_type == pref_data.notification_type
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Preference for {pref_data.type} already exists. Use PUT to update."
        )
    
    preference = NotificationPreference(
        user_id=current_user.id,
        **pref_data.model_dump()
    )
    
    db.add(preference)
    await db.commit()
    await db.refresh(preference)
    
    return preference


@router.get("/preferences/{pref_id}", response_model=NotificationPreferenceResponse)
async def get_notification_preference(
    pref_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific notification preference"""
    
    result = await db.execute(
        select(NotificationPreference).where(
            and_(
                NotificationPreference.id == pref_id,
                NotificationPreference.user_id == current_user.id
            )
        )
    )
    preference = result.scalar_one_or_none()
    
    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification preference not found"
        )
    
    return preference


@router.put("/preferences/{pref_id}", response_model=NotificationPreferenceResponse)
async def update_notification_preference(
    pref_id: str,
    pref_update: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a notification preference"""
    
    result = await db.execute(
        select(NotificationPreference).where(
            and_(
                NotificationPreference.id == pref_id,
                NotificationPreference.user_id == current_user.id
            )
        )
    )
    preference = result.scalar_one_or_none()
    
    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification preference not found"
        )
    
    # Update fields
    update_data = pref_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preference, field, value)
    
    await db.commit()
    await db.refresh(preference)
    
    return preference


@router.delete("/preferences/{pref_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_preference(
    pref_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a notification preference"""
    
    result = await db.execute(
        select(NotificationPreference).where(
            and_(
                NotificationPreference.id == pref_id,
                NotificationPreference.user_id == current_user.id
            )
        )
    )
    preference = result.scalar_one_or_none()
    
    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification preference not found"
        )
    
    await db.delete(preference)
    await db.commit()


@router.post("/preferences/set-defaults")
async def set_default_preferences(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Set default notification preferences for all notification types"""
    
    # Define default preferences for each notification type
    default_prefs = [
        {
            "type": NotificationType.ORDER_FILLED,
            "channels": [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            "is_enabled": True
        },
        {
            "type": NotificationType.ORDER_FAILED,
            "channels": [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            "is_enabled": True
        },
        {
            "type": NotificationType.RISK_BREACH,
            "channels": [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            "is_enabled": True
        },
        {
            "type": NotificationType.STRATEGY_ERROR,
            "channels": [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            "is_enabled": True
        },
        {
            "type": NotificationType.POSITION_UPDATE,
            "channels": [NotificationChannel.IN_APP],
            "is_enabled": False  # Disabled by default to avoid spam
        },
        {
            "type": NotificationType.SYSTEM_ALERT,
            "channels": [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
            "is_enabled": True
        }
    ]
    
    created_count = 0
    for pref_data in default_prefs:
        # Check if preference already exists
        result = await db.execute(
            select(NotificationPreference).where(
                and_(
                    NotificationPreference.user_id == current_user.id,
                    NotificationPreference.notification_type == pref_data["notification_type"]
                )
            )
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            preference = NotificationPreference(
                user_id=current_user.id,
                **pref_data
            )
            db.add(preference)
            created_count += 1
    
    await db.commit()
    
    return {"message": f"Created {created_count} default notification preferences"}
