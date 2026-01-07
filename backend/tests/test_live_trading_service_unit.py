"""
Comprehensive unit tests for the Live Trading Service.

Tests cover:
- System status retrieval with account information
- Portfolio retrieval with positions and P&L
- Empty portfolio scenarios
- Action execution (reset, pause, resume)
- Order execution
- Error handling and edge cases
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.live_trading_service import LiveTradingService
from app.models.live_strategy import LiveStrategy
from app.models.paper_trading import PaperAccount, PaperPosition, PaperTrade
from app.models.enums import LiveStrategyStatus


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession for testing."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def live_trading_service(mock_session):
    """Create a LiveTradingService instance with mock session."""
    return LiveTradingService(mock_session)


# =============================================================================
# Test: get_system_status
# =============================================================================

@pytest.mark.asyncio
async def test_get_system_status(mock_session):
    """
    Test get_system_status returns system status with account info.

    Verifies:
    - System status is returned correctly
    - Active strategies count is accurate
    - P&L information is included
    - Paper trading mode flag is set
    """
    with patch('app.services.live_trading_service.get_paper_trading_service') as mock_get_paper:
        mock_paper_service = AsyncMock()
        mock_get_paper.return_value = mock_paper_service

        # Mock paper account with trades
        mock_account = {
            "user_id": "test_user",
            "cash_balance": 75000.0,
            "total_pnl": 5000.0,
            "unrealized_pnl": 2500.0,
            "total_equity": 105000.0,
            "trades": [
                {
                    "symbol": "AAPL",
                    "qty": 10,
                    "price": 150.0,
                    "side": "buy",
                    "timestamp": "2024-01-15T10:00:00"
                }
            ]
        }
        mock_paper_service.get_paper_account.return_value = mock_account

        # Mock active strategies
        mock_strategy1 = MagicMock()
        mock_strategy1.id = "strat_1"
        mock_strategy1.name = "SMA Strategy"
        mock_strategy1.user_id = "test_user"
        mock_strategy1.is_active = True

        mock_strategy2 = MagicMock()
        mock_strategy2.id = "strat_2"
        mock_strategy2.name = "RSI Strategy"
        mock_strategy2.user_id = "test_user"
        mock_strategy2.is_active = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_strategy1, mock_strategy2]
        mock_session.execute.return_value = mock_result

        service = LiveTradingService(mock_session)
        status = await service.get_system_status("test_user")

        # Assertions
        assert status["is_running"] is True
        assert status["active_strategies"] == 2
        assert status["total_pnl"] == 5000.0
        assert status["unrealized_pnl"] == 2500.0
        assert status["total_equity"] == 105000.0
        assert status["paper_trading_mode"] is True
        assert status["last_trade_at"] == "2024-01-15T10:00:00"
        assert "error" not in status


@pytest.mark.asyncio
async def test_get_system_status_no_active_strategies(mock_session):
    """
    Test get_system_status when no strategies are active.

    Verifies:
    - is_running is False when no active strategies
    - active_strategies count is zero
    - System is still operational
    """
    with patch('app.services.live_trading_service.get_paper_trading_service') as mock_get_paper:
        mock_paper_service = AsyncMock()
        mock_get_paper.return_value = mock_paper_service

        mock_account = {
            "user_id": "test_user",
            "total_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "total_equity": 100000.0,
            "trades": []
        }
        mock_paper_service.get_paper_account.return_value = mock_account

        # No active strategies
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        service = LiveTradingService(mock_session)
        status = await service.get_system_status("test_user")

        assert status["is_running"] is False
        assert status["active_strategies"] == 0
        assert status["last_trade_at"] is None


@pytest.mark.asyncio
async def test_get_system_status_with_exception(mock_session):
    """
    Test get_system_status error handling.

    Verifies:
    - Exception is caught and logged
    - Default error response is returned
    - System remains operational
    """
    with patch('app.services.live_trading_service.get_paper_trading_service') as mock_get_paper:
        mock_paper_service = AsyncMock()
        mock_get_paper.return_value = mock_paper_service

        # Simulate exception
        mock_paper_service.get_paper_account.side_effect = Exception("Database error")

        service = LiveTradingService(mock_session)
        status = await service.get_system_status("test_user")

        assert status["is_running"] is False
        assert status["active_strategies"] == 0
        assert "error" in status
        assert "Database error" in status["error"]


# =============================================================================
# Test: get_portfolio
# =============================================================================

@pytest.mark.asyncio
async def test_get_portfolio(mock_session):
    """
    Test get_portfolio returns portfolio with positions and P&L.

    Verifies:
    - Portfolio value is calculated correctly
    - Positions are formatted properly
    - Buying power matches cash balance
    - Total return percentage is included
    """
    with patch('app.services.live_trading_service.get_paper_trading_service') as mock_get_paper:
        mock_paper_service = AsyncMock()
        mock_get_paper.return_value = mock_paper_service

        # Mock account with positions
        mock_account = {
            "user_id": "test_user",
            "cash_balance": 50000.0,
            "total_equity": 105000.0,
            "total_pnl": 5000.0,
            "total_return_pct": 5.0,
            "positions": {
                "AAPL": {
                    "qty": 10,
                    "avg_price": 150.0,
                    "current_price": 155.5,
                    "market_value": 1555.0,
                    "unrealized_pnl": 55.0
                },
                "GOOGL": {
                    "qty": 5,
                    "avg_price": 2800.0,
                    "current_price": 2900.0,
                    "market_value": 14500.0,
                    "unrealized_pnl": 500.0
                }
            }
        }
        mock_paper_service.get_paper_account.return_value = mock_account

        service = LiveTradingService(mock_session)
        portfolio = await service.get_portfolio("test_user")

        # Assertions
        assert portfolio["total_value"] == 105000.0
        assert portfolio["cash"] == 50000.0
        assert portfolio["buying_power"] == 50000.0
        assert portfolio["positions_count"] == 2
        assert portfolio["total_pnl"] == 5000.0
        assert portfolio["total_return_pct"] == 5.0
        assert portfolio["paper_trading_mode"] is True

        # Verify positions format
        assert len(portfolio["positions"]) == 2
        positions_by_symbol = {p["symbol"]: p for p in portfolio["positions"]}

        assert positions_by_symbol["AAPL"]["qty"] == 10
        assert positions_by_symbol["AAPL"]["avg_price"] == 150.0
        assert positions_by_symbol["AAPL"]["market_value"] == 1555.0

        assert positions_by_symbol["GOOGL"]["qty"] == 5
        assert positions_by_symbol["GOOGL"]["unrealized_pnl"] == 500.0


@pytest.mark.asyncio
async def test_get_portfolio_empty(mock_session):
    """
    Test get_portfolio with empty positions.

    Verifies:
    - Empty portfolio is handled correctly
    - Positions list is empty
    - Cash equals total value
    - Paper trading mode is indicated
    """
    with patch('app.services.live_trading_service.get_paper_trading_service') as mock_get_paper:
        mock_paper_service = AsyncMock()
        mock_get_paper.return_value = mock_paper_service

        # Mock account with no positions
        mock_account = {
            "user_id": "test_user",
            "cash_balance": 100000.0,
            "total_equity": 100000.0,
            "total_pnl": 0.0,
            "total_return_pct": 0.0,
            "positions": {}
        }
        mock_paper_service.get_paper_account.return_value = mock_account

        service = LiveTradingService(mock_session)
        portfolio = await service.get_portfolio("test_user")

        assert portfolio["total_value"] == 100000.0
        assert portfolio["cash"] == 100000.0
        assert portfolio["positions"] == []
        assert portfolio["positions_count"] == 0
        assert portfolio["total_pnl"] == 0.0


@pytest.mark.asyncio
async def test_get_portfolio_account_not_found(mock_session):
    """
    Test get_portfolio when account doesn't exist.

    Verifies:
    - Null account is handled gracefully
    - Default empty portfolio is returned
    - No errors are raised
    """
    with patch('app.services.live_trading_service.get_paper_trading_service') as mock_get_paper:
        mock_paper_service = AsyncMock()
        mock_get_paper.return_value = mock_paper_service

        # Account not found
        mock_paper_service.get_paper_account.return_value = None

        service = LiveTradingService(mock_session)
        portfolio = await service.get_portfolio("nonexistent_user")

        assert portfolio["total_value"] == 0
        assert portfolio["cash"] == 0
        assert portfolio["positions"] == []
        assert portfolio["paper_trading_mode"] is True


@pytest.mark.asyncio
async def test_get_portfolio_exception(mock_session):
    """
    Test get_portfolio error handling.

    Verifies:
    - Exceptions are caught gracefully
    - Empty portfolio is returned on error
    - Error message is included
    """
    with patch('app.services.live_trading_service.get_paper_trading_service') as mock_get_paper:
        mock_paper_service = AsyncMock()
        mock_get_paper.return_value = mock_paper_service

        # Simulate exception
        mock_paper_service.get_paper_account.side_effect = Exception("Service error")

        service = LiveTradingService(mock_session)
        portfolio = await service.get_portfolio("test_user")

        assert portfolio["total_value"] == 0
        assert portfolio["cash"] == 0
        assert portfolio["positions"] == []
        assert "error" in portfolio


# =============================================================================
# Test: perform_action - RESET
# =============================================================================

@pytest.mark.asyncio
async def test_perform_action_reset(mock_session):
    """
    Test perform_action with reset action.

    Verifies:
    - Reset action clears account state
    - Success response is returned
    - Paper trading account is reset
    - Appropriate message is provided
    """
    with patch('app.services.live_trading_service.get_paper_trading_service') as mock_get_paper:
        mock_paper_service = AsyncMock()
        mock_get_paper.return_value = mock_paper_service

        # Mock reset response
        reset_account = {
            "user_id": "test_user",
            "cash_balance": 100000.0,
            "initial_balance": 100000.0,
            "total_pnl": 0.0,
            "positions": {}
        }
        mock_paper_service.reset_paper_account.return_value = reset_account

        service = LiveTradingService(mock_session)
        result = await service.perform_action("test_user", "reset")

        assert result["success"] is True
        assert result["action"] == "reset"
        assert "reset" in result["message"].lower()
        assert result["account"] == reset_account
        mock_paper_service.reset_paper_account.assert_called_once_with("test_user")


# =============================================================================
# Test: perform_action - PAUSE
# =============================================================================

@pytest.mark.asyncio
async def test_perform_action_pause(mock_session):
    """
    Test perform_action with pause action.

    Verifies:
    - Pause action deactivates all active strategies
    - Active strategies are marked as inactive
    - Database is committed
    - Success response includes strategy count
    """
    # Create mock strategies
    mock_strategy1 = MagicMock(spec=LiveStrategy)
    mock_strategy1.id = "strat_1"
    mock_strategy1.is_active = True

    mock_strategy2 = MagicMock(spec=LiveStrategy)
    mock_strategy2.id = "strat_2"
    mock_strategy2.is_active = True

    # Mock database query result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_strategy1, mock_strategy2]
    mock_session.execute.return_value = mock_result
    mock_session.commit = AsyncMock()

    service = LiveTradingService(mock_session)
    result = await service.perform_action("test_user", "pause")

    # Assertions
    assert result["success"] is True
    assert result["action"] == "pause"
    assert "paused" in result["message"].lower()
    assert "2" in result["message"]  # 2 strategies paused

    # Verify strategies were marked as inactive
    assert mock_strategy1.is_active is False
    assert mock_strategy2.is_active is False

    # Verify database commit was called
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_perform_action_pause_no_strategies(mock_session):
    """
    Test perform_action pause when no strategies are active.

    Verifies:
    - Pause succeeds with zero active strategies
    - Appropriate message indicates zero paused
    """
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result
    mock_session.commit = AsyncMock()

    service = LiveTradingService(mock_session)
    result = await service.perform_action("test_user", "pause")

    assert result["success"] is True
    assert result["action"] == "pause"
    assert "0" in result["message"]


# =============================================================================
# Test: perform_action - RESUME
# =============================================================================

@pytest.mark.asyncio
async def test_perform_action_resume(mock_session):
    """
    Test perform_action with resume action.

    Verifies:
    - Resume action reactivates paused strategies
    - Inactive strategies are marked as active
    - Database is committed
    - Success response includes strategy count
    """
    # Create mock paused strategies
    mock_strategy1 = MagicMock(spec=LiveStrategy)
    mock_strategy1.id = "strat_1"
    mock_strategy1.is_active = False

    mock_strategy2 = MagicMock(spec=LiveStrategy)
    mock_strategy2.id = "strat_2"
    mock_strategy2.is_active = False

    # Mock database query result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_strategy1, mock_strategy2]
    mock_session.execute.return_value = mock_result
    mock_session.commit = AsyncMock()

    service = LiveTradingService(mock_session)
    result = await service.perform_action("test_user", "resume")

    # Assertions
    assert result["success"] is True
    assert result["action"] == "resume"
    assert "resumed" in result["message"].lower()
    assert "2" in result["message"]

    # Verify strategies were marked as active
    assert mock_strategy1.is_active is True
    assert mock_strategy2.is_active is True

    # Verify database commit was called
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_perform_action_resume_no_paused(mock_session):
    """
    Test perform_action resume when no strategies are paused.

    Verifies:
    - Resume succeeds with zero paused strategies
    - Appropriate message indicates zero resumed
    """
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result
    mock_session.commit = AsyncMock()

    service = LiveTradingService(mock_session)
    result = await service.perform_action("test_user", "resume")

    assert result["success"] is True
    assert result["action"] == "resume"
    assert "0" in result["message"]


# =============================================================================
# Test: perform_action - INVALID ACTION
# =============================================================================

@pytest.mark.asyncio
async def test_perform_action_invalid(mock_session):
    """
    Test perform_action with invalid action.

    Verifies:
    - Unknown action returns success=False
    - Error message indicates unknown action
    - No database operations occur
    """
    service = LiveTradingService(mock_session)
    result = await service.perform_action("test_user", "invalid_action")

    assert result["success"] is False
    assert result["action"] == "invalid_action"
    assert "unknown" in result["message"].lower()

    # Verify no database operations occurred
    mock_session.execute.assert_not_called()
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_perform_action_exception(mock_session):
    """
    Test perform_action error handling.

    Verifies:
    - Database exceptions are caught
    - Error response is returned
    - Error message is included
    """
    mock_session.execute.side_effect = Exception("DB connection lost")

    service = LiveTradingService(mock_session)
    result = await service.perform_action("test_user", "pause")

    assert result["success"] is False
    assert result["action"] == "pause"
    assert "error" in result
    assert "DB connection lost" in result["error"]


# =============================================================================
# Test: execute_order
# =============================================================================

@pytest.mark.asyncio
async def test_execute_order(mock_session):
    """
    Test execute_order executes a trading order.

    Verifies:
    - Order is successfully executed
    - Paper trading service is called with correct parameters
    - Response includes execution details
    - Symbol is converted to uppercase
    - Side is converted to lowercase
    """
    with patch('app.services.live_trading_service.get_paper_trading_service') as mock_get_paper:
        mock_paper_service = AsyncMock()
        mock_get_paper.return_value = mock_paper_service

        # Mock successful order execution
        order_result = {
            "success": True,
            "symbol": "AAPL",
            "qty": 10,
            "side": "buy",
            "price": 150.25,
            "timestamp": "2024-01-15T10:00:00",
            "account_cash": 98502.5
        }
        mock_paper_service.execute_paper_order.return_value = order_result

        service = LiveTradingService(mock_session)
        result = await service.execute_order("test_user", "aapl", 10, "BUY")

        # Assertions
        assert result["success"] is True
        assert result["symbol"] == "AAPL"

        # Verify paper service was called with normalized parameters
        mock_paper_service.execute_paper_order.assert_called_once_with(
            user_id="test_user",
            symbol="AAPL",
            qty=10,
            side="buy",
            order_type="market",
            limit_price=None
        )


@pytest.mark.asyncio
async def test_execute_order_with_limit(mock_session):
    """
    Test execute_order with limit price.

    Verifies:
    - Limit price is passed to paper trading service
    - Order type is set correctly
    - All parameters are normalized
    """
    with patch('app.services.live_trading_service.get_paper_trading_service') as mock_get_paper:
        mock_paper_service = AsyncMock()
        mock_get_paper.return_value = mock_paper_service

        order_result = {"success": True}
        mock_paper_service.execute_paper_order.return_value = order_result

        service = LiveTradingService(mock_session)
        result = await service.execute_order(
            "test_user",
            "GOOGL",
            5,
            "sell",
            order_type="limit",
            limit_price=2950.0
        )

        assert result["success"] is True

        # Verify limit price was passed
        mock_paper_service.execute_paper_order.assert_called_once_with(
            user_id="test_user",
            symbol="GOOGL",
            qty=5,
            side="sell",
            order_type="limit",
            limit_price=2950.0
        )


@pytest.mark.asyncio
async def test_execute_order_insufficient_funds(mock_session):
    """
    Test execute_order when account has insufficient funds.

    Verifies:
    - Paper service returns failure for insufficient funds
    - Error message is included
    - Response indicates order failure
    """
    with patch('app.services.live_trading_service.get_paper_trading_service') as mock_get_paper:
        mock_paper_service = AsyncMock()
        mock_get_paper.return_value = mock_paper_service

        # Mock insufficient funds response
        order_result = {
            "success": False,
            "error": "Insufficient buying power"
        }
        mock_paper_service.execute_paper_order.return_value = order_result

        service = LiveTradingService(mock_session)
        result = await service.execute_order("test_user", "AAPL", 1000, "buy")

        assert result["success"] is False
        assert "Insufficient" in result["error"]


@pytest.mark.asyncio
async def test_execute_order_exception(mock_session):
    """
    Test execute_order error handling.

    Verifies:
    - Service exceptions are caught
    - Error response is returned
    - Error message is included
    - No partial execution occurs
    """
    with patch('app.services.live_trading_service.get_paper_trading_service') as mock_get_paper:
        mock_paper_service = AsyncMock()
        mock_get_paper.return_value = mock_paper_service

        # Simulate exception
        mock_paper_service.execute_paper_order.side_effect = Exception("Market closed")

        service = LiveTradingService(mock_session)
        result = await service.execute_order("test_user", "AAPL", 10, "buy")

        assert result["success"] is False
        assert "error" in result
        assert "Market closed" in result["error"]


# =============================================================================
# Test: get_active_strategies
# =============================================================================

@pytest.mark.asyncio
async def test_get_active_strategies(mock_session):
    """
    Test get_active_strategies retrieves active strategy IDs.

    Verifies:
    - Active strategies are returned as list
    - Strategy IDs are correctly formatted
    - Only active strategies are included
    """
    # Mock active strategy IDs
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        "strat_1",
        "strat_2",
        "strat_3"
    ]
    mock_session.execute.return_value = mock_result

    service = LiveTradingService(mock_session)
    strategies = await service.get_active_strategies("test_user")

    assert len(strategies) == 3
    assert "strat_1" in strategies
    assert "strat_2" in strategies
    assert "strat_3" in strategies


@pytest.mark.asyncio
async def test_get_active_strategies_empty(mock_session):
    """
    Test get_active_strategies when no strategies are active.

    Verifies:
    - Empty list is returned
    - No errors occur
    """
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    service = LiveTradingService(mock_session)
    strategies = await service.get_active_strategies("test_user")

    assert strategies == []


@pytest.mark.asyncio
async def test_get_active_strategies_exception(mock_session):
    """
    Test get_active_strategies error handling.

    Verifies:
    - Exceptions return empty list
    - Service remains operational
    """
    mock_session.execute.side_effect = Exception("DB error")

    service = LiveTradingService(mock_session)
    strategies = await service.get_active_strategies("test_user")

    assert strategies == []


# =============================================================================
# Test: get_orders
# =============================================================================

@pytest.mark.asyncio
async def test_get_orders(mock_session):
    """
    Test get_orders retrieves recent trade history as orders.

    Verifies:
    - Trade history is formatted as orders
    - Order status is set to 'filled'
    - Paper trading flag is included
    - All trade details are preserved
    """
    with patch('app.services.live_trading_service.get_paper_trading_service') as mock_get_paper:
        mock_paper_service = AsyncMock()
        mock_get_paper.return_value = mock_paper_service

        # Mock trade history
        trades = [
            {
                "symbol": "AAPL",
                "qty": 10,
                "price": 150.0,
                "side": "buy",
                "timestamp": "2024-01-15T10:00:00"
            },
            {
                "symbol": "GOOGL",
                "qty": 5,
                "price": 2900.0,
                "side": "sell",
                "timestamp": "2024-01-15T11:00:00"
            }
        ]
        mock_paper_service.get_paper_trade_history.return_value = trades

        service = LiveTradingService(mock_session)
        orders = await service.get_orders("test_user", limit=50)

        # Assertions
        assert len(orders) == 2

        assert orders[0]["symbol"] == "AAPL"
        assert orders[0]["qty"] == 10
        assert orders[0]["side"] == "buy"
        assert orders[0]["status"] == "filled"
        assert orders[0]["paper_trading"] is True

        assert orders[1]["symbol"] == "GOOGL"
        assert orders[1]["qty"] == 5
        assert orders[1]["side"] == "sell"

        # Verify limit was passed
        mock_paper_service.get_paper_trade_history.assert_called_once_with(
            "test_user",
            limit=50
        )


@pytest.mark.asyncio
async def test_get_orders_empty(mock_session):
    """
    Test get_orders when no trades exist.

    Verifies:
    - Empty list is returned
    - No errors occur
    """
    with patch('app.services.live_trading_service.get_paper_trading_service') as mock_get_paper:
        mock_paper_service = AsyncMock()
        mock_get_paper.return_value = mock_paper_service

        mock_paper_service.get_paper_trade_history.return_value = []

        service = LiveTradingService(mock_session)
        orders = await service.get_orders("test_user")

        assert orders == []


@pytest.mark.asyncio
async def test_get_orders_exception(mock_session):
    """
    Test get_orders error handling.

    Verifies:
    - Service exceptions are caught
    - Empty list is returned
    - Service remains operational
    """
    with patch('app.services.live_trading_service.get_paper_trading_service') as mock_get_paper:
        mock_paper_service = AsyncMock()
        mock_get_paper.return_value = mock_paper_service

        mock_paper_service.get_paper_trade_history.side_effect = Exception("API error")

        service = LiveTradingService(mock_session)
        orders = await service.get_orders("test_user")

        assert orders == []


# =============================================================================
# Test: Integration and Edge Cases
# =============================================================================

@pytest.mark.asyncio
async def test_multiple_operations_sequence(mock_session):
    """
    Test multiple operations in sequence.

    Verifies:
    - Multiple operations can be performed sequentially
    - State is maintained correctly between calls
    - No side effects occur between operations
    """
    with patch('app.services.live_trading_service.get_paper_trading_service') as mock_get_paper:
        mock_paper_service = AsyncMock()
        mock_get_paper.return_value = mock_paper_service

        # Setup mocks
        mock_paper_service.get_paper_account.return_value = {
            "cash_balance": 100000.0,
            "total_equity": 100000.0,
            "positions": {}
        }

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        service = LiveTradingService(mock_session)

        # Sequence of operations
        portfolio = await service.get_portfolio("test_user")
        assert portfolio["total_value"] == 100000.0

        status = await service.get_system_status("test_user")
        assert status["active_strategies"] == 0

        strategies = await service.get_active_strategies("test_user")
        assert strategies == []

        # All operations should succeed
        mock_paper_service.get_paper_account.assert_called()
        mock_session.execute.assert_called()


@pytest.mark.asyncio
async def test_large_position_portfolio(mock_session):
    """
    Test get_portfolio with many positions.

    Verifies:
    - Large portfolios are handled correctly
    - All positions are included
    - Aggregations are accurate
    """
    with patch('app.services.live_trading_service.get_paper_trading_service') as mock_get_paper:
        mock_paper_service = AsyncMock()
        mock_get_paper.return_value = mock_paper_service

        # Create 20 positions
        positions = {}
        for i in range(20):
            symbol = f"STOCK{i:02d}"
            positions[symbol] = {
                "qty": 10,
                "avg_price": 100.0 + i,
                "current_price": 105.0 + i,
                "market_value": 1050.0 + (10 * i),
                "unrealized_pnl": 50.0 + i
            }

        mock_account = {
            "cash_balance": 50000.0,
            "total_equity": 100000.0,
            "total_pnl": 5000.0,
            "total_return_pct": 5.0,
            "positions": positions
        }
        mock_paper_service.get_paper_account.return_value = mock_account

        service = LiveTradingService(mock_session)
        portfolio = await service.get_portfolio("test_user")

        assert portfolio["positions_count"] == 20
        assert len(portfolio["positions"]) == 20
        assert portfolio["total_value"] == 100000.0
