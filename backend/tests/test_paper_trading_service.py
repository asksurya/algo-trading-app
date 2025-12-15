
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.paper_trading import PaperTradingService
from app.models.paper_trading import PaperAccount, PaperPosition, PaperTrade

@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    return session

@pytest.mark.asyncio
async def test_initialize_paper_account(mock_session):
    service = PaperTradingService(mock_session)
    user_id = "test_user"

    # Mock execute result for checking existence (return None initially)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    account = await service.initialize_paper_account(user_id)

    assert account["user_id"] == user_id
    assert account["cash_balance"] == 100000.0

    # Verify add was called
    assert mock_session.add.called
    assert mock_session.commit.called
    assert mock_session.refresh.called

@pytest.mark.asyncio
async def test_get_paper_account_existing(mock_session):
    service = PaperTradingService(mock_session)
    user_id = "test_user"

    # Mock existing account
    mock_account = PaperAccount(
        id="acc_1",
        user_id=user_id,
        cash_balance=50000.0,
        initial_balance=100000.0,
        positions=[],
        trades=[]
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_account
    mock_session.execute.return_value = mock_result

    account = await service.get_paper_account(user_id)

    assert account["user_id"] == user_id
    assert account["cash_balance"] == 50000.0

@pytest.mark.asyncio
async def test_execute_paper_order_buy_new_position(mock_session):
    service = PaperTradingService(mock_session)
    user_id = "test_user"

    # Mock existing account
    mock_account = PaperAccount(
        id="acc_1",
        user_id=user_id,
        cash_balance=100000.0,
        initial_balance=100000.0,
        positions=[],
        trades=[]
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_account
    mock_session.execute.return_value = mock_result
    # For execute_paper_order where it re-fetches if not found (not needed here but good to know)
    mock_result.scalar_one.return_value = mock_account

    # Execute buy order: 10 shares at $150
    result = await service.execute_paper_order(user_id, "AAPL", 10, "buy", limit_price=150.0)

    assert result["success"] is True

    # Cash balance should decrease
    assert mock_account.cash_balance == 100000.0 - (10 * 150.0)

    # Positions should have the new position
    assert len(mock_account.positions) == 1
    assert mock_account.positions[0].symbol == "AAPL"
    assert mock_account.positions[0].qty == 10

    # Check return values
    # Total equity should remain unchanged (Cash + Stock Value = 98500 + 1500 = 100000)
    # Note: total_return_pct is (total_equity / initial_balance - 1) * 100
    assert result["account"]["total_equity"] == 100000.0
    assert result["account"]["total_return_pct"] == 0.0

@pytest.mark.asyncio
async def test_execute_paper_order_buy_existing_position(mock_session):
    service = PaperTradingService(mock_session)
    user_id = "test_user"

    # Mock existing account with a position
    existing_pos = PaperPosition(symbol="AAPL", qty=10, avg_price=150.0, market_value=1500.0)
    mock_account = PaperAccount(
        id="acc_1",
        user_id=user_id,
        cash_balance=98500.0,
        initial_balance=100000.0,
        positions=[existing_pos],
        trades=[]
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_account
    mock_session.execute.return_value = mock_result

    # Buy more: 10 shares at $200
    result = await service.execute_paper_order(user_id, "AAPL", 10, "buy", limit_price=200.0)

    assert result["success"] is True

    # Cash balance should decrease by 2000
    assert mock_account.cash_balance == 98500.0 - 2000.0 # 96500.0

    # Position should be updated
    pos = mock_account.positions[0]
    assert pos.qty == 20
    # Avg price = (1500 + 2000) / 20 = 175
    assert pos.avg_price == 175.0

    # Equity check: Cash(96500) + Stock(20 * 200 = 4000) = 100500
    assert result["account"]["total_equity"] == 100500.0
    # Return pct: (100500 / 100000 - 1) * 100 = 0.5%
    assert result["account"]["total_return_pct"] == pytest.approx(0.5)

@pytest.mark.asyncio
async def test_execute_paper_order_insufficient_funds(mock_session):
    service = PaperTradingService(mock_session)
    user_id = "test_user"

    mock_account = PaperAccount(
        id="acc_1",
        user_id=user_id,
        cash_balance=100.0,
        initial_balance=100000.0,
        positions=[],
        trades=[]
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_account
    mock_session.execute.return_value = mock_result

    result = await service.execute_paper_order(user_id, "AAPL", 10, "buy", limit_price=150.0)

    assert result["success"] is False
    assert result["error"] == "Insufficient buying power"
