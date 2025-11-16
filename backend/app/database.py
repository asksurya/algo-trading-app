"""
Database connection and session management.
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.models.base import Base

_engine = None
_async_session_local = None

def get_engine():
    """Get the database engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            pool_pre_ping=True
        )
    return _engine

def get_async_session_local():
    """Get the async session local."""
    global _async_session_local
    if _async_session_local is None:
        _async_session_local = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_local

async def get_db() -> AsyncSession:
    """
    Dependency to get a database session.
    """
    async_session = get_async_session_local()
    async with async_session() as session:
        yield session

async def init_db():
    """Initialize the database."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """Close the database connection."""
    engine = get_engine()
    await engine.dispose()
