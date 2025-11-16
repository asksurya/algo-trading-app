# Pending Tasks for Algorithmic Trading App Testing

This document outlines the current status of testing efforts and details the remaining issues that need to be addressed.

## Current Status

*   **Resolved Issues:**
    *   `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no active connection` errors have been resolved by switching to a file-based SQLite database and refining the `db` fixture in `conftest.py`.
    *   All authentication-related tests in `tests/test_auth.py` are now passing. This includes successful user creation, login, and token validation.
    *   `TypeError: client.<locals>.override_get_db.<locals>.mock_commit() takes 0 positional arguments but 1 was given` has been resolved by correctly patching `db.commit()` to accept `*args` and `**kwargs`.
    *   `NameError: name 'original_commit' is not defined` has been resolved by correctly scoping `original_commit` in the `client` fixture.

*   **Remaining Failing Test:**
    *   `tests/test_trading_scenarios.py::TestTradingScenarios::test_create_and_start_strategy`

*   **Specific Error in Failing Test:**
    *   `TypeError: object NoneType can't be used in 'await' expression` occurring in `backend/app/api/v1/strategies.py` at `await db.expire(new_strategy)`.

*   **Root Cause Analysis for `TypeError`:**
    *   The `db` object (an `AsyncSession` instance) is unexpectedly `None` when `await db.expire(new_strategy)` is called within the `create_strategy` endpoint.
    *   This is critical because `db` is injected via `Depends(get_db)`, and the `client` fixture's `override_get_db` is designed to always yield a valid `AsyncSession`.
    *   The print statements added in the last debugging session (which are still in `backend/app/api/v1/strategies.py`) show that `db` is a valid `AsyncSession` object *before* `await db.expire(new_strategy)`. This suggests that `db` is becoming `None` *during* or immediately before the `await db.expire(new_strategy)` call, which is highly unusual for a function parameter.

*   **Underlying Issue (masked by TypeError):**
    *   The original problem was `AssertionError: assert 404 == 200` in `test_trading_scenarios.py`, indicating that the strategy created by the `/api/v1/strategies` endpoint was not found by the subsequent `/api/v1/strategies/execution/{strategy_id}/start` endpoint.
    *   The debug output from `start_strategy_execution` consistently showed `Strategy found in DB: False`.
    *   This points to a transaction isolation or data visibility issue, where changes flushed by `db.commit()` (mocked to `db.flush()`) are not immediately visible to subsequent queries within the same session, or the session state is being improperly managed. The `TypeError` is currently preventing us from fully debugging this.

## Next Steps for Future Agents

1.  **Investigate `TypeError: object NoneType can't be used in 'await' expression`:**
    *   **Analyze Debug Output:** Carefully examine the full debug output from the last test run (with print statements in `conftest.py`, `strategies.py`, and `strategy_execution.py`). Pay close attention to the `db` object's value and type at each print statement, especially around the `await db.expire(new_strategy)` call.
    *   **Verify `new_strategy` object:** Ensure `new_strategy` itself is a valid object and not `None` when `db.expire()` is called.
    *   **Check `AsyncSession` lifecycle:** Investigate if there are any scenarios where an `AsyncSession` instance could legitimately become `None` or invalid mid-function execution, especially after `db.commit()` (which is `db.flush()` in tests) and `db.refresh()`.
    *   **Temporarily remove `db.expire()`:** If the `TypeError` persists, temporarily remove `await db.expire(new_strategy)` from `create_strategy` again to confirm the `TypeError` is directly caused by that line. If the `TypeError` goes away, then the issue is specifically with `db.expire()`'s interaction with the session state.

2.  **Address `404 Not Found` (after TypeError is resolved):**
    *   If removing `db.expire()` resolves the `TypeError` but brings back the `404 Not Found`, then `db.expire()` (or a similar mechanism) is indeed necessary for data visibility.
    *   **Alternative to `db.expire()`:** If `db.expire()` continues to be problematic, explore alternative ways to ensure data visibility within the same session after `db.flush()`:
        *   Explicitly re-query the strategy by ID in `start_strategy_execution` to ensure it's fetched from the database.
        *   Consider `session.refresh(new_strategy, attribute_names=['id'])` or similar targeted refreshes if `db.refresh(new_strategy)` is not sufficient.
        *   Investigate if `db.flush()` itself is behaving as expected in the test environment.

3.  **Clean up Debugging Code:** Once the issues are resolved, remove all added print statements and debugging code from `conftest.py`, `backend/app/api/v1/strategies.py`, and `backend/app/api/v1/strategy_execution.py`.

## Relevant Files:

*   `backend/tests/conftest.py`
*   `backend/app/api/v1/strategies.py`
*   `backend/app/api/v1/strategy_execution.py`
*   `backend/tests/test_trading_scenarios.py`
*   `backend/app/database.py` (for `get_engine`, `get_async_session_local`)
*   `backend/app/models/strategy.py` (for `Strategy` model)
*   `backend/app/models/user.py` (for `User` model)
*   `backend/app/dependencies.py` (for `get_current_active_user`, `get_db`)
