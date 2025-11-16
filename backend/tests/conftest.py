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
from fastapi.testclient import TestClient
import pytest

# Use file-based SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Override database settings for testing
settings.DATABASE_URL = TEST_DATABASE_URL
settings.ENVIRONMENT = "test"

# Initialize the test engine and session local after settings are overridden
test_engine = get_engine()
TestingSessionLocal = get_async_session_local()

@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    print(f"\n--- Debug: setup_database fixture START ---")
    """Create and drop tables once for the entire test session."""
    # Ensure the test database file is clean before starting
    if os.path.exists("./test.db"):
        os.remove("./test.db")
    print(f"Database file ./test.db cleaned before setup.")

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"Tables created for test session.")
    yield
    print(f"--- Debug: setup_database fixture TEARDOWN ---")
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print(f"Tables dropped after test session.")
    # Clean up the test database file after the session
    if os.path.exists("./test.db"):
        os.remove("./test.db")
    print(f"Database file ./test.db cleaned after teardown.")
    print(f"--- Debug: setup_database fixture END ---")

@pytest.fixture(scope="function")
async def db(setup_database):
    print(f"\n--- Debug: db fixture START ---")
    """Create a test database session with a transactional rollback."""
    connection = await test_engine.connect()
    transaction = await connection.begin()
    session = TestingSessionLocal(bind=connection)
    print(f"db fixture: Session created: {session}")
    print(f"db fixture: Transaction begun: {transaction}")
    try:
        yield session
    finally:
        print(f"--- Debug: db fixture TEARDOWN ---")
        print(f"db fixture: Rolling back transaction: {transaction}")
        await transaction.rollback() # Rollback the transaction
        print(f"db fixture: Closing session: {session}")
        await session.close()
        print(f"db fixture: Closing connection: {connection}")
        await connection.close()
        print(f"--- Debug: db fixture TEARDOWN END ---")

@pytest.fixture(scope="function")
async def client(db):
    print(f"\n--- Debug: client fixture START ---")
    original_commit = db.commit # Define original_commit in the client fixture's scope
    print(f"client fixture: Original db.commit stored: {original_commit}")

    # This function will be used to override the get_db dependency
    async def override_get_db():
        print(f"--- Debug: override_get_db START ---")
        print(f"override_get_db: db object received: {db}")
        print(f"override_get_db: type of db received: {type(db)}")
        # Patch the commit method to prevent actual commits in tests
        # Instead, it will just flush the session
        async def mock_commit(*args, **kwargs): # Accept all arguments
            print(f"--- Debug: mock_commit START ---")
            print(f"mock_commit: Flushing session: {db}")
            await db.flush()
            print(f"mock_commit: Session flushed.")
            print(f"--- Debug: mock_commit END ---")

        print(f"override_get_db: Patching db.commit with mock_commit.")
        db.commit = mock_commit.__get__(db, AsyncSession) # Bind mock_commit to the session instance

        try:
            print(f"override_get_db: Yielding db session: {db}")
            yield db # Yield the same session provided by the db fixture
        finally:
            print(f"--- Debug: override_get_db TEARDOWN ---")
            # DO NOT rollback or close here. The db fixture will handle it.
            pass 
            print(f"--- Debug: override_get_db TEARDOWN END ---")

    print(f"client fixture: Overriding app.dependency_overrides[get_db].")
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        print(f"client fixture: TestClient created.")
        yield test_client
    print(f"client fixture: Clearing app.dependency_overrides.")
    app.dependency_overrides.clear()
    # Restore original commit method here, after the test client is done
    print(f"client fixture: Restoring original db.commit: {original_commit}")
    db.commit = original_commit # original_commit is now accessible here
    print(f"--- Debug: client fixture END ---")

@pytest.fixture(scope="function")
async def committed_test_user(db: AsyncSession):
    print(f"\n--- Debug: committed_test_user fixture START ---")
    print(f"committed_test_user: db object received: {db}")
    user = User(
        email="committed_test@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Committed Test User",
        role=UserRole.USER,
    )
    print(f"committed_test_user: Adding user to session: {user.email}")
    db.add(user)
    print(f"committed_test_user: Calling db.commit() (mocked to flush).")
    await db.commit() # Commit to the transaction provided by the db fixture
    print(f"committed_test_user: Calling db.refresh(user).")
    await db.refresh(user) # Refresh should now work
    print(f"committed_test_user: User refreshed: {user.id}")
    yield user
    print(f"--- Debug: committed_test_user fixture END ---")

@pytest.fixture
async def auth_headers(client, committed_test_user):
    print(f"\n--- Debug: auth_headers fixture START ---")
    print(f"auth_headers: Attempting login for user: {committed_test_user.email}")
    response = client.post(
        "/api/v1/auth/login",
        json={"email": committed_test_user.email, "password": "testpass123"}
    )
    print(f"auth_headers: Login response status code: {response.status_code}")
    print(f"auth_headers: Login response JSON: {response.json()}")
    response.raise_for_status() # Raise an exception for bad status codes
    token = response.json()["access_token"]
    print(f"auth_headers: Access token obtained: {token[:10]}...") # Print first 10 chars of token
    yield {"Authorization": f"Bearer {token}"}
    print(f"--- Debug: auth_headers fixture END ---")
