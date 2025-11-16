"""
Database connection and session management.
Uses SQLAlchemy 2.0 with async support.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.core.config import settings


# Base class for models
Base = declarative_base()

_engine = None
_async_session_local = None

def get_engine():
    global _engine
    if _engine is None:
        # Convert postgresql:// to postgresql+asyncpg://
        async_database_url = settings.DATABASE_URL.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        _engine = create_async_engine(
            async_database_url,
            echo=settings.DATABASE_ECHO,
            poolclass=NullPool if settings.is_development else None,
            pool_pre_ping=True,
        )
    return _engine

def get_async_session_local():
    global _async_session_local
    if _async_session_local is None:
        _async_session_local = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_local

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    
    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    engine = get_engine()
    async with engine.begin() as conn:
        # Import all models here to ensure they are registered
        from app.models import user, strategy, trade  # noqa
        
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    engine = get_engine()
    await engine.dispose()
