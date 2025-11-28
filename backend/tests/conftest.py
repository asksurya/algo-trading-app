import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import get_async_session_local, get_engine, Base
from app.core.config import settings
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.dependencies import get_db
from httpx import AsyncClient, ASGITransport
import pytest
import pytest_asyncio

# Use file-based SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Override database settings for testing
settings.DATABASE_URL = TEST_DATABASE_URL
settings.ENVIRONMENT = "test"

# Initialize the test engine and session local after settings are overridden
test_engine = get_engine()
TestingSessionLocal = get_async_session_local()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Create and drop tables once for the entire test session."""
    # Ensure the test database file is clean before starting
    if os.path.exists("./test.db"):
        os.remove("./test.db")

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # Clean up the test database file after the session
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest_asyncio.fixture(scope="function")
async def db(setup_database):
    """Create a test database session with a transactional rollback."""
    connection = await test_engine.connect()
    transaction = await connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        await transaction.rollback() # Rollback the transaction
        await session.close()
        await connection.close()

@pytest_asyncio.fixture(scope="function")
async def client(db):
    """Create an async test client with database override."""
    original_commit = db.commit

    # This function will be used to override the get_db dependency
    async def override_get_db():
        # Patch the commit method to prevent actual commits in tests
        # Instead, it will just flush the session
        async def mock_commit(*args, **kwargs):
            await db.flush()
            db.expire_all()  # Force reload of all cached objects to ensure visibility

        db.commit = mock_commit.__get__(db, AsyncSession)

        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    # Use httpx.AsyncClient with ASGITransport
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
    db.commit = original_commit

@pytest_asyncio.fixture(scope="function")
async def committed_test_user(db: AsyncSession):
    """Create a test user for authentication tests."""
    user = User(
        email="committed_test@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Committed Test User",
        role=UserRole.USER,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    yield user

@pytest_asyncio.fixture
async def auth_headers(client, committed_test_user):
    """Get authentication headers with valid JWT token."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": committed_test_user.email, "password": "testpass123"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    yield {"Authorization": f"Bearer {token}"}
