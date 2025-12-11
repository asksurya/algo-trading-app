"""
Database connection and session management.
Provides async SQLAlchemy 2.0 engine and session management with proper transaction handling.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.models.base import Base

# Global engine and session instances
_engine: Optional[AsyncEngine] = None
_async_session_local: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    """
    Get or create the database engine.
    
    Uses connection pooling configuration appropriate for the environment.
    """
    global _engine
    if _engine is None:
        # Determine pool settings based on environment
        pool_kwargs = {}
        
        if "sqlite" in settings.DATABASE_URL:
            # SQLite doesn't support connection pooling well with async
            pool_kwargs["poolclass"] = NullPool
        else:
            # PostgreSQL connection pool configuration
            pool_kwargs.update({
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 1800,  # Recycle connections after 30 minutes
                "pool_pre_ping": True,  # Verify connections before use
            })
        
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            **pool_kwargs
        )
    return _engine


def get_async_session_local() -> async_sessionmaker[AsyncSession]:
    """
    Get or create the async session factory.
    
    Sessions created with expire_on_commit=False to allow accessing
    objects after commit without re-fetching.
    """
    global _async_session_local
    if _async_session_local is None:
        _async_session_local = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False,
        )
    return _async_session_local


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a database session with proper transaction management.
    
    This is the main database dependency for FastAPI routes.
    Implements a try/finally pattern to ensure proper cleanup on errors.
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async_session = get_async_session_local()
    session = async_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions (for use outside of FastAPI routes).
    
    Usage:
        async with get_db_context() as db:
            user = await db.get(User, user_id)
    """
    async_session = get_async_session_local()
    session = async_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db() -> None:
    """
    Initialize the database by creating all tables.
    
    Should be called during application startup.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close the database connection pool.
    
    Should be called during application shutdown.
    """
    global _engine, _async_session_local
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_local = None


async def check_db_connection() -> bool:
    """
    Check if the database connection is healthy.
    
    Returns:
        True if connection is healthy, False otherwise.
    """
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception:
        return False


def reset_engine() -> None:
    """
    Reset the engine and session factory.
    
    Useful for testing to ensure clean state between tests.
    """
    global _engine, _async_session_local
    _engine = None
    _async_session_local = None
