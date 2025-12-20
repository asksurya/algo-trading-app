
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.paper_trading import PaperTradingService
from app.models.paper_trading import PaperAccount, PaperPosition, PaperTrade

@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    return session

@pytest.mark.asyncio
async def test_initialize_paper_account(mock_session):
    with patch('app.services.paper_trading.get_market_data_service') as mock_get_md:
        mock_md_service = AsyncMock()
        mock_get_md.return_value = mock_md_service
        # Setup mock market data return for format call
        mock_md_service.get_multi_trades.return_value = []

        service = PaperTradingService(mock_session)
        user_id = "test_user"

        # Mock execute result for checking existence (return None initially)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Handle sequential calls:
        # 1. Check existence -> None
        # 2. get_paper_account check existence -> account (after commit)

        created_account = PaperAccount(
            user_id=user_id,
            cash_balance=100000.0,
            initial_balance=100000.0,
            positions=[],
            trades=[]
        )

        mock_result_none = MagicMock()
        mock_result_none.scalar_one_or_none.return_value = None

        mock_result_account = MagicMock()
        mock_result_account.scalar_one_or_none.return_value = created_account

        mock_session.execute.side_effect = [mock_result_none, mock_result_account]

        account = await service.initialize_paper_account(user_id)

        assert account["user_id"] == user_id
        assert account["cash_balance"] == 100000.0

        assert mock_session.add.called
        assert mock_session.commit.called

@pytest.mark.asyncio
async def test_get_paper_account_existing(mock_session):
    with patch('app.services.paper_trading.get_market_data_service') as mock_get_md:
        mock_md_service = AsyncMock()
        mock_get_md.return_value = mock_md_service

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
    with patch('app.services.paper_trading.get_market_data_service') as mock_get_md:
        mock_md_service = AsyncMock()
        mock_get_md.return_value = mock_md_service

        # Setup mock price
        mock_md_service.get_latest_trade.return_value = {'price': 150.0}

        # Setup for format call at end: get_multi_trades
        mock_md_service.get_multi_trades.return_value = [{'symbol': 'AAPL', 'price': 150.0}]

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

        # Mock objects
        mock_result_account = MagicMock()
        mock_result_account.scalar_one_or_none.return_value = mock_account
        mock_result_account.scalar_one.return_value = mock_account # For refresh calls if any

        mock_result_pos = MagicMock()
        mock_result_pos.scalar_one_or_none.return_value = None

        # Sequence:
        # 1. Fetch account (execute_paper_order start)
        # 2. Fetch position (check if exists)
        # 3. Fetch account final (for return)
        mock_session.execute.side_effect = [
            mock_result_account,
            mock_result_pos,
            mock_result_account
        ]

        # Execute buy order: 10 shares
        # Note: limit_price=None, so it fetches market price
        result = await service.execute_paper_order(user_id, "AAPL", 10, "buy")

        assert result["success"] is True

        # Verify price fetch
        mock_md_service.get_latest_trade.assert_called_with("AAPL")

        # Cash balance check - we need to verify logic, but since mock_account is mutated in place by service logic (if ORM worked),
        # or we check calls.
        # Logic: cash -= 10 * 150 = 1500. New cash = 98500.
        assert mock_account.cash_balance == 98500.0

        # Verify add was called
        # We can't easily check args type equality because PaperPosition constructor issues from SQLAlchemy
        assert mock_session.add.call_count >= 1

@pytest.mark.asyncio
async def test_execute_paper_order_buy_existing_position(mock_session):
    with patch('app.services.paper_trading.get_market_data_service') as mock_get_md:
        mock_md_service = AsyncMock()
        mock_get_md.return_value = mock_md_service

        mock_md_service.get_latest_trade.return_value = {'price': 200.0}
        mock_md_service.get_multi_trades.return_value = [{'symbol': 'AAPL', 'price': 200.0}]

        service = PaperTradingService(mock_session)
        user_id = "test_user"

        # Mock existing account with a position
        existing_pos = PaperPosition(symbol="AAPL", qty=10, avg_price=150.0)
        mock_account = PaperAccount(
            id="acc_1",
            user_id=user_id,
            cash_balance=98500.0,
            initial_balance=100000.0,
            positions=[existing_pos],
            trades=[]
        )

        mock_result_account = MagicMock()
        mock_result_account.scalar_one_or_none.return_value = mock_account
        mock_result_account.scalar_one.return_value = mock_account

        # Mock position query
        mock_result_pos = MagicMock()
        mock_result_pos.scalar_one_or_none.return_value = existing_pos

        mock_session.execute.side_effect = [
            mock_result_account,
            mock_result_pos,
            mock_result_account
        ]

        # Buy more: 10 shares at market price (mocked 200)
        result = await service.execute_paper_order(user_id, "AAPL", 10, "buy")

        assert result["success"] is True

        # Cash balance should decrease by 2000
        assert mock_account.cash_balance == 98500.0 - 2000.0 # 96500.0

        # Position should be updated
        # Avg price = (1500 + 2000) / 20 = 175
        assert existing_pos.qty == 20
        assert existing_pos.avg_price == 175.0

@pytest.mark.asyncio
async def test_execute_paper_order_insufficient_funds(mock_session):
    with patch('app.services.paper_trading.get_market_data_service') as mock_get_md:
        mock_md_service = AsyncMock()
        mock_get_md.return_value = mock_md_service
        mock_md_service.get_latest_trade.return_value = {'price': 150.0}

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

        result = await service.execute_paper_order(user_id, "AAPL", 10, "buy")

        assert result["success"] is False
        assert result["error"] == "Insufficient buying power"

@pytest.mark.asyncio
async def test_execute_paper_order_price_fetch_failure(mock_session):
    with patch('app.services.paper_trading.get_market_data_service') as mock_get_md:
        mock_md_service = AsyncMock()
        mock_get_md.return_value = mock_md_service

        # Simulate price fetch error
        mock_md_service.get_latest_trade.side_effect = Exception("API Error")

        service = PaperTradingService(mock_session)
        user_id = "test_user"

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

        result = await service.execute_paper_order(user_id, "AAPL", 10, "buy")

        assert result["success"] is False
        assert "Failed to fetch market price" in result["error"]
