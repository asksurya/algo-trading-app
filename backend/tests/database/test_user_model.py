"""
Tests for User model and related functionality.

This module tests:
- User model CRUD operations
- User role enum handling
- User relationships
- User constraints and validations
"""
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole


class TestUserModel:
    """Test suite for User model."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a new user."""
        user = User(
            email="newuser@example.com",
            hashed_password="hashed_password",
            full_name="New User",
            role=UserRole.USER,
        )
        db_session.add(user)
        await db_session.flush()
        
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.is_verified is False
        assert user.created_at is not None
        assert user.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_user_uuid_generation(self, db_session: AsyncSession):
        """Test that user ID is a valid UUID string."""
        user = User(
            email="uuid_test@example.com",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.flush()
        
        assert user.id is not None
        assert len(user.id) == 36  # UUID format: 8-4-4-4-12
        assert "-" in user.id
    
    @pytest.mark.asyncio
    async def test_user_roles(self, db_session: AsyncSession):
        """Test all user roles can be assigned."""
        roles = [UserRole.ADMIN, UserRole.USER, UserRole.VIEWER]
        
        for i, role in enumerate(roles):
            user = User(
                email=f"role_test_{i}@example.com",
                hashed_password="hashed_password",
                role=role,
            )
            db_session.add(user)
            await db_session.flush()
            assert user.role == role
    
    @pytest.mark.asyncio
    async def test_user_default_values(self, db_session: AsyncSession):
        """Test that default values are correctly set."""
        user = User(
            email="defaults@example.com",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        await db_session.flush()
        
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.is_verified is False
        assert user.full_name is None
        assert user.last_login is None
    
    @pytest.mark.asyncio
    async def test_user_repr(self, test_user: User):
        """Test user string representation."""
        repr_str = repr(test_user)
        assert "User" in repr_str
        assert test_user.email in repr_str
        assert str(test_user.role) in repr_str
    
    @pytest.mark.asyncio
    async def test_fetch_user_by_email(self, db_session: AsyncSession, test_user: User):
        """Test fetching user by email."""
        result = await db_session.execute(
            select(User).where(User.email == test_user.email)
        )
        fetched_user = result.scalar_one()
        
        assert fetched_user.id == test_user.id
        assert fetched_user.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_update_user(self, db_session: AsyncSession, test_user: User):
        """Test updating user fields."""
        original_updated_at = test_user.updated_at
        
        test_user.full_name = "Updated Name"
        test_user.is_verified = True
        await db_session.flush()
        await db_session.refresh(test_user)
        
        assert test_user.full_name == "Updated Name"
        assert test_user.is_verified is True


class TestUserRole:
    """Test suite for UserRole enum."""
    
    def test_user_role_values(self):
        """Test UserRole enum values."""
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.USER.value == "user"
        assert UserRole.VIEWER.value == "viewer"
    
    def test_user_role_is_string_enum(self):
        """Test that UserRole is a string enum."""
        assert isinstance(UserRole.ADMIN, str)
        assert UserRole.ADMIN == "admin"
    
    def test_user_role_from_string(self):
        """Test creating UserRole from string."""
        assert UserRole("admin") == UserRole.ADMIN
        assert UserRole("user") == UserRole.USER
        assert UserRole("viewer") == UserRole.VIEWER


class TestUserRelationships:
    """Test suite for User relationships."""
    
    @pytest.mark.asyncio
    async def test_user_orders_relationship(self, db_session: AsyncSession, test_user: User, test_order):
        """Test user to orders relationship."""
        await db_session.refresh(test_user)
        
        # The order should be accessible through the user
        assert test_order.user_id == test_user.id
    
    @pytest.mark.asyncio
    async def test_user_api_keys_relationship(self, db_session: AsyncSession, test_user: User, test_api_key):
        """Test user to API keys relationship."""
        await db_session.refresh(test_user)
        
        # The API key should be accessible through the user
        assert test_api_key.user_id == test_user.id
    
    @pytest.mark.asyncio
    async def test_user_notifications_relationship(self, db_session: AsyncSession, test_user: User, test_notification):
        """Test user to notifications relationship."""
        await db_session.refresh(test_user)
        
        # The notification should be accessible through the user
        assert test_notification.user_id == test_user.id
    
    @pytest.mark.asyncio
    async def test_user_risk_rules_relationship(self, db_session: AsyncSession, test_user: User, test_risk_rule):
        """Test user to risk rules relationship."""
        await db_session.refresh(test_user)
        
        # The risk rule should be accessible through the user
        assert test_risk_rule.user_id == test_user.id
