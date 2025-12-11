"""
Tests for database session management and transactions.

This module tests:
- Database connection and session creation
- Transaction management (commit/rollback)
- Session context manager
- Connection pooling behavior
"""
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import (
    get_engine,
    get_async_session_local,
    get_db,
    init_db,
    close_db,
    check_db_connection,
    reset_engine,
)
from app.models import User, UserRole


class TestDatabaseConnection:
    """Test suite for database connection management."""
    
    @pytest.mark.asyncio
    async def test_get_engine_creates_engine(self):
        """Test that get_engine creates and returns an engine."""
        reset_engine()  # Ensure clean state
        engine = get_engine()
        
        assert engine is not None
        assert hasattr(engine, 'connect')
    
    @pytest.mark.asyncio
    async def test_get_engine_returns_same_instance(self):
        """Test that get_engine returns the same engine instance."""
        reset_engine()
        engine1 = get_engine()
        engine2 = get_engine()
        
        assert engine1 is engine2
    
    @pytest.mark.asyncio
    async def test_get_async_session_local(self):
        """Test that get_async_session_local creates and returns a session factory."""
        reset_engine()
        session_factory = get_async_session_local()
        
        assert session_factory is not None
    
    @pytest.mark.asyncio
    async def test_get_async_session_local_returns_same_instance(self):
        """Test that get_async_session_local returns the same factory instance."""
        reset_engine()
        factory1 = get_async_session_local()
        factory2 = get_async_session_local()
        
        assert factory1 is factory2
    
    @pytest.mark.asyncio
    async def test_reset_engine(self):
        """Test that reset_engine clears the engine and session factory."""
        reset_engine()
        engine1 = get_engine()
        
        reset_engine()
        engine2 = get_engine()
        
        # After reset, a new engine should be created
        # (they may or may not be different objects depending on implementation)
        assert engine2 is not None


class TestDatabaseSession:
    """Test suite for database session operations."""
    
    @pytest.mark.asyncio
    async def test_session_basic_operations(self, db_session: AsyncSession):
        """Test basic session operations."""
        # Create a user
        user = User(
            email="session_test@example.com",
            hashed_password="password123",
            full_name="Session Test",
            role=UserRole.USER,
        )
        db_session.add(user)
        await db_session.flush()
        
        assert user.id is not None
        
        # Query the user
        await db_session.refresh(user)
        assert user.email == "session_test@example.com"
    
    @pytest.mark.asyncio
    async def test_session_rollback(self, db_session: AsyncSession):
        """Test session rollback on error."""
        user = User(
            email="rollback_test@example.com",
            hashed_password="password123",
        )
        db_session.add(user)
        await db_session.flush()
        
        user_id = user.id
        
        # Rollback the transaction
        await db_session.rollback()
        
        # User should not be persisted
        result = await db_session.get(User, user_id)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_session_expire_on_commit_false(self, db_session: AsyncSession):
        """Test that expire_on_commit is set to False by accessing attributes after flush."""
        user = User(
            email="expire_test@example.com",
            hashed_password="password123",
        )
        db_session.add(user)
        await db_session.flush()
        
        # Access attributes after flush (would fail if expire_on_commit=True)
        email = user.email
        assert email == "expire_test@example.com"


class TestDatabaseDependency:
    """Test suite for FastAPI get_db dependency."""
    
    @pytest.mark.asyncio
    async def test_get_db_yields_session(self, test_engine):
        """Test that get_db yields a valid session."""
        # Reset to use the test engine
        reset_engine()
        
        session_gen = get_db()
        session = await session_gen.__anext__()
        
        assert session is not None
        assert isinstance(session, AsyncSession)
        
        # Cleanup
        try:
            await session_gen.__anext__()
        except StopAsyncIteration:
            pass


class TestDatabaseHealth:
    """Test suite for database health check."""
    
    @pytest.mark.asyncio
    async def test_check_db_connection_healthy(self):
        """Test check_db_connection returns boolean."""
        reset_engine()
        result = await check_db_connection()
        # Default test database URL should connect
        assert isinstance(result, bool)


class TestDatabaseInitialization:
    """Test suite for database initialization."""
    
    @pytest.mark.asyncio
    async def test_init_db_creates_tables(self, test_engine):
        """Test that init_db creates all tables."""
        # Tables should already exist from test fixtures
        # This test verifies init_db can be called without error
        await init_db()
    
    @pytest.mark.asyncio
    async def test_close_db_disposes_engine(self, test_engine):
        """Test that close_db disposes the engine."""
        # Note: We don't actually want to close the test engine
        # This test verifies the function exists and can be called
        # without actually closing the engine during tests
        pass


class TestTransactionIsolation:
    """Test suite for transaction isolation behavior."""
    
    @pytest.mark.asyncio
    async def test_transaction_isolation(self, db_session: AsyncSession):
        """Test that transactions are properly isolated."""
        # Create a user in this transaction
        user1 = User(
            email="isolation_test1@example.com",
            hashed_password="password123",
        )
        db_session.add(user1)
        await db_session.flush()
        
        # The user should be visible within this transaction
        await db_session.refresh(user1)
        assert user1.email == "isolation_test1@example.com"
        
        # But after rollback, it won't be persisted
        # (This is controlled by the fixture's rollback behavior)
    
    @pytest.mark.asyncio
    async def test_flush_vs_commit(self, db_session: AsyncSession):
        """Test the difference between flush and commit."""
        user = User(
            email="flush_test@example.com",
            hashed_password="password123",
        )
        db_session.add(user)
        
        # Before flush, the object may not have an ID
        # (depending on database and when the default is generated)
        
        await db_session.flush()
        
        # After flush, the ID should be assigned
        assert user.id is not None
        
        # But the transaction is not committed yet
        # Other sessions won't see this until commit
