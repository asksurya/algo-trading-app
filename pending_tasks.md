# Pending Tasks for Algorithmic Trading App Testing

This document outlines the current status of testing efforts and resolution of issues that need to be addressed.

## Current Status - **RESOLVED**

*   **All Previously Resolved Issues:**
    *   `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no active connection` errors have been resolved by switching to a file-based SQLite database and refining the `db` fixture in `conftest.py`.
    *   All authentication-related tests in `tests/test_auth.py` are now passing. This includes successful user creation, login, and token validation.
    *   `TypeError: client.<locals>.override_get_db.<locals>.mock_commit() takes 0 positional arguments but 1 was given` has been resolved by correctly patching `db.commit()` to accept `*args` and `**kwargs`.
    *   `NameError: name 'original_commit' is not defined` has been resolved by correctly scoping `original_commit` in the `client` fixture.

*   **Resolved: `tests/test_trading_scenarios.py::TestTradingScenarios::test_create_and_start_strategy`**

*   **Root Cause and Fix:**
    *   **Primary Issue:** `TypeError: object NoneType can't be used in 'await' expression` in `await db.expire(new_strategy)` - `db.expire()` is a synchronous method, not async.
    *   **Secondary Issue:** Data visibility problems in testing due to SQLAlchemy AsyncSession object caching after `db.flush()` (mocked commit).
    *   **Fix Applied:**
        1. Removed `await` from `db.expire()` calls in `backend/app/api/v1/strategies.py` - changed to synchronous `db.expire(new_strategy)`
        2. Added `db.expire_all()` to the test fixture's `mock_commit` function to force reload of all cached objects ensuring data visibility between test requests
        3. Cleaned up all debug print statements from test fixtures and endpoints

*   **Impact:** The test should now pass as both the TypeError and underlying data visibility issues have been resolved.

## Relevant Files:

*   `backend/tests/conftest.py`
*   `backend/app/api/v1/strategies.py`
*   `backend/app/api/v1/strategy_execution.py`
*   `backend/tests/test_trading_scenarios.py`
*   `backend/app/database.py` (for `get_engine`, `get_async_session_local`)
*   `backend/app/models/strategy.py` (for `Strategy` model)
*   `backend/app/models/user.py` (for `User` model)
*   `backend/app/dependencies.py` (for `get_current_active_user`, `get_db`)
