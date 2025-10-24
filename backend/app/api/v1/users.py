"""
Users API routes.
Handles user profile management and password changes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, PasswordChange
from app.dependencies import get_current_active_user


router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current user profile.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user profile.
    
    - **full_name**: Update full name
    - **email**: Update email (must be unique)
    """
    # Check if email is being updated
    if user_update.email and user_update.email != current_user.email:
        # Check if new email already exists
        result = await db.execute(
            select(User).where(User.email == user_update.email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        
        current_user.email = user_update.email
    
    # Update full name if provided
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change current user password.
    
    - **current_password**: Current password for verification
    - **new_password**: New password (must meet strength requirements)
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Hash and update new password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    
    await db.commit()
    
    return None


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete current user account.
    
    This is a soft delete - sets is_active to False.
    """
    current_user.is_active = False
    await db.commit()
    
    return None
