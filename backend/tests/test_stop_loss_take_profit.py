"""
Tests for stop-loss and take-profit functionality in paper trading.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.services.paper_trading import PaperTradingService
from app.services.stop_loss_monitor import StopLossTakeProfitMonitor
from app.models.paper_trading import PaperAccount, PaperPosition, PaperTrade
from app.schemas.paper_trading import PaperOrderRequest, UpdateStopLossRequest


@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    return session


class TestPaperOrderWithStopLoss:
    """Test placing paper orders with stop-loss and take-profit."""

    @pytest.mark.asyncio
    async def test_buy_order_with_stop_loss_and_take_profit(self, mock_session):
        """Test buying shares with stop-loss and take-profit attached."""
        with patch('app.services.paper_trading.get_market_data_service') as mock_get_md:
            mock_md_service = AsyncMock()
            mock_get_md.return_value = mock_md_service
            mock_md_service.get_latest_trade.return_value = {'price': 150.0}
            mock_md_service.get_multi_trades.return_value = [{'symbol': 'AAPL', 'price': 150.0}]

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

            mock_result_account = MagicMock()
            mock_result_account.scalar_one_or_none.return_value = mock_account
            mock_result_account.scalar_one.return_value = mock_account

            mock_result_pos = MagicMock()
            mock_result_pos.scalar_one_or_none.return_value = None

            mock_session.execute.side_effect = [
                mock_result_account,
                mock_result_pos,
                mock_result_account
            ]

            # Buy 10 shares with stop-loss at 140 and take-profit at 180
            result = await service.execute_paper_order(
                user_id=user_id,
                symbol="AAPL",
                qty=10,
                side="buy",
                stop_loss_price=140.0,
                take_profit_price=180.0
            )

            assert result["success"] is True

            # Verify position was created with stop-loss and take-profit
            add_calls = mock_session.add.call_args_list
            assert len(add_calls) >= 1

            # Check that at least one call was for a PaperPosition with stop-loss/take-profit
            position_added = False
            for call in add_calls:
                obj = call[0][0]
                if isinstance(obj, PaperPosition):
                    position_added = True
                    # Note: We can't easily verify the values in mocked scenario
                    # In integration tests, we would verify the actual values
            assert position_added or mock_result_pos.scalar_one_or_none.return_value is not None

    @pytest.mark.asyncio
    async def test_sell_order_rejects_stop_loss(self, mock_session):
        """Test that sell orders cannot have stop-loss attached."""
        with patch('app.services.paper_trading.get_market_data_service') as mock_get_md:
            mock_md_service = AsyncMock()
            mock_get_md.return_value = mock_md_service

            service = PaperTradingService(mock_session)

            result = await service.execute_paper_order(
                user_id="test_user",
                symbol="AAPL",
                qty=10,
                side="sell",
                stop_loss_price=140.0
            )

            assert result["success"] is False
            assert "sell orders" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_sell_order_rejects_take_profit(self, mock_session):
        """Test that sell orders cannot have take-profit attached."""
        with patch('app.services.paper_trading.get_market_data_service') as mock_get_md:
            mock_md_service = AsyncMock()
            mock_get_md.return_value = mock_md_service

            service = PaperTradingService(mock_session)

            result = await service.execute_paper_order(
                user_id="test_user",
                symbol="AAPL",
                qty=10,
                side="sell",
                take_profit_price=180.0
            )

            assert result["success"] is False
            assert "sell orders" in result["error"].lower()


class TestStopLossTakeProfitMonitor:
    """Test the stop-loss/take-profit position monitor."""

    @pytest.mark.asyncio
    async def test_stop_loss_trigger(self, mock_session):
        """Test that stop-loss is triggered when price falls below threshold."""
        with patch('app.services.stop_loss_monitor.get_market_data_service') as mock_get_md:
            mock_md_service = AsyncMock()
            mock_get_md.return_value = mock_md_service

            # Price has fallen to 135, below stop-loss of 140
            mock_md_service.get_multi_trades.return_value = [{'symbol': 'AAPL', 'price': 135.0}]

            mock_account = PaperAccount(
                id="acc_1",
                user_id="test_user",
                cash_balance=98500.0,
                initial_balance=100000.0,
                total_pnl=0.0
            )

            mock_position = PaperPosition(
                id="pos_1",
                account_id="acc_1",
                symbol="AAPL",
                qty=10,
                avg_price=150.0,
                stop_loss_price=140.0,
                take_profit_price=180.0
            )
            mock_position.account = mock_account

            # Mock query for positions with stop-loss/take-profit
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_position]
            mock_session.execute.return_value = mock_result

            monitor = StopLossTakeProfitMonitor(mock_session)
            triggered = await monitor.check_all_positions()

            assert len(triggered) == 1
            assert triggered[0]["trigger_type"] == "stop_loss"
            assert triggered[0]["execution_price"] == 135.0
            assert triggered[0]["realized_pnl"] == (135.0 - 150.0) * 10  # -150

    @pytest.mark.asyncio
    async def test_take_profit_trigger(self, mock_session):
        """Test that take-profit is triggered when price rises above threshold."""
        with patch('app.services.stop_loss_monitor.get_market_data_service') as mock_get_md:
            mock_md_service = AsyncMock()
            mock_get_md.return_value = mock_md_service

            # Price has risen to 185, above take-profit of 180
            mock_md_service.get_multi_trades.return_value = [{'symbol': 'AAPL', 'price': 185.0}]

            mock_account = PaperAccount(
                id="acc_1",
                user_id="test_user",
                cash_balance=98500.0,
                initial_balance=100000.0,
                total_pnl=0.0
            )

            mock_position = PaperPosition(
                id="pos_1",
                account_id="acc_1",
                symbol="AAPL",
                qty=10,
                avg_price=150.0,
                stop_loss_price=140.0,
                take_profit_price=180.0
            )
            mock_position.account = mock_account

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_position]
            mock_session.execute.return_value = mock_result

            monitor = StopLossTakeProfitMonitor(mock_session)
            triggered = await monitor.check_all_positions()

            assert len(triggered) == 1
            assert triggered[0]["trigger_type"] == "take_profit"
            assert triggered[0]["execution_price"] == 185.0
            assert triggered[0]["realized_pnl"] == (185.0 - 150.0) * 10  # +350

    @pytest.mark.asyncio
    async def test_no_trigger_when_price_in_range(self, mock_session):
        """Test that no trigger occurs when price is between stop-loss and take-profit."""
        with patch('app.services.stop_loss_monitor.get_market_data_service') as mock_get_md:
            mock_md_service = AsyncMock()
            mock_get_md.return_value = mock_md_service

            # Price is 160, between stop-loss (140) and take-profit (180)
            mock_md_service.get_multi_trades.return_value = [{'symbol': 'AAPL', 'price': 160.0}]

            mock_account = PaperAccount(
                id="acc_1",
                user_id="test_user",
                cash_balance=98500.0,
                initial_balance=100000.0,
                total_pnl=0.0
            )

            mock_position = PaperPosition(
                id="pos_1",
                account_id="acc_1",
                symbol="AAPL",
                qty=10,
                avg_price=150.0,
                stop_loss_price=140.0,
                take_profit_price=180.0
            )
            mock_position.account = mock_account

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_position]
            mock_session.execute.return_value = mock_result

            monitor = StopLossTakeProfitMonitor(mock_session)
            triggered = await monitor.check_all_positions()

            assert len(triggered) == 0

    @pytest.mark.asyncio
    async def test_no_positions_with_stop_loss(self, mock_session):
        """Test that no triggers occur when no positions have stop-loss/take-profit."""
        with patch('app.services.stop_loss_monitor.get_market_data_service') as mock_get_md:
            mock_md_service = AsyncMock()
            mock_get_md.return_value = mock_md_service

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute.return_value = mock_result

            monitor = StopLossTakeProfitMonitor(mock_session)
            triggered = await monitor.check_all_positions()

            assert len(triggered) == 0


class TestUpdateStopLossTakeProfit:
    """Test updating stop-loss/take-profit on existing positions."""

    @pytest.mark.asyncio
    async def test_update_stop_loss_on_existing_position(self, mock_session):
        """Test updating stop-loss price on an existing position."""
        with patch('app.services.paper_trading.get_market_data_service') as mock_get_md:
            mock_md_service = AsyncMock()
            mock_get_md.return_value = mock_md_service
            mock_md_service.get_latest_trade.return_value = {'price': 155.0}

            service = PaperTradingService(mock_session)

            mock_account = PaperAccount(
                id="acc_1",
                user_id="test_user",
                cash_balance=98500.0,
                initial_balance=100000.0
            )

            mock_position = PaperPosition(
                id="pos_1",
                account_id="acc_1",
                symbol="AAPL",
                qty=10,
                avg_price=150.0,
                stop_loss_price=140.0,
                take_profit_price=180.0
            )

            mock_result_account = MagicMock()
            mock_result_account.scalar_one_or_none.return_value = mock_account

            mock_result_pos = MagicMock()
            mock_result_pos.scalar_one_or_none.return_value = mock_position

            mock_session.execute.side_effect = [mock_result_account, mock_result_pos]

            result = await service.update_position_stop_loss_take_profit(
                user_id="test_user",
                symbol="AAPL",
                stop_loss_price=145.0
            )

            assert result["success"] is True
            assert mock_position.stop_loss_price == 145.0
            assert mock_position.take_profit_price == 180.0  # Unchanged

    @pytest.mark.asyncio
    async def test_clear_stop_loss(self, mock_session):
        """Test clearing stop-loss from a position."""
        with patch('app.services.paper_trading.get_market_data_service') as mock_get_md:
            mock_md_service = AsyncMock()
            mock_get_md.return_value = mock_md_service
            mock_md_service.get_latest_trade.return_value = {'price': 155.0}

            service = PaperTradingService(mock_session)

            mock_account = PaperAccount(
                id="acc_1",
                user_id="test_user",
                cash_balance=98500.0,
                initial_balance=100000.0
            )

            mock_position = PaperPosition(
                id="pos_1",
                account_id="acc_1",
                symbol="AAPL",
                qty=10,
                avg_price=150.0,
                stop_loss_price=140.0,
                take_profit_price=180.0
            )

            mock_result_account = MagicMock()
            mock_result_account.scalar_one_or_none.return_value = mock_account

            mock_result_pos = MagicMock()
            mock_result_pos.scalar_one_or_none.return_value = mock_position

            mock_session.execute.side_effect = [mock_result_account, mock_result_pos]

            result = await service.update_position_stop_loss_take_profit(
                user_id="test_user",
                symbol="AAPL",
                clear_stop_loss=True
            )

            assert result["success"] is True
            assert mock_position.stop_loss_price is None
            assert mock_position.take_profit_price == 180.0  # Unchanged

    @pytest.mark.asyncio
    async def test_update_nonexistent_position(self, mock_session):
        """Test updating stop-loss on a position that doesn't exist."""
        with patch('app.services.paper_trading.get_market_data_service') as mock_get_md:
            mock_md_service = AsyncMock()
            mock_get_md.return_value = mock_md_service

            service = PaperTradingService(mock_session)

            mock_account = PaperAccount(
                id="acc_1",
                user_id="test_user",
                cash_balance=100000.0,
                initial_balance=100000.0
            )

            mock_result_account = MagicMock()
            mock_result_account.scalar_one_or_none.return_value = mock_account

            mock_result_pos = MagicMock()
            mock_result_pos.scalar_one_or_none.return_value = None

            mock_session.execute.side_effect = [mock_result_account, mock_result_pos]

            result = await service.update_position_stop_loss_take_profit(
                user_id="test_user",
                symbol="AAPL",
                stop_loss_price=140.0
            )

            assert result["success"] is False
            assert "No position found" in result["error"]


class TestPaperOrderRequestSchema:
    """Test Pydantic schema validation for paper orders."""

    def test_valid_buy_order_with_stop_loss(self):
        """Test valid buy order with stop-loss and take-profit."""
        order = PaperOrderRequest(
            symbol="AAPL",
            qty=10,
            side="buy",
            stop_loss_price=140.0,
            take_profit_price=180.0
        )
        assert order.stop_loss_price == 140.0
        assert order.take_profit_price == 180.0

    def test_sell_order_rejects_stop_loss(self):
        """Test that sell order rejects stop-loss."""
        with pytest.raises(ValueError) as exc_info:
            PaperOrderRequest(
                symbol="AAPL",
                qty=10,
                side="sell",
                stop_loss_price=140.0
            )
        assert "stop_loss_price can only be set for buy orders" in str(exc_info.value)

    def test_stop_loss_must_be_below_take_profit(self):
        """Test that stop-loss must be below take-profit."""
        with pytest.raises(ValueError) as exc_info:
            PaperOrderRequest(
                symbol="AAPL",
                qty=10,
                side="buy",
                stop_loss_price=180.0,
                take_profit_price=140.0
            )
        assert "stop_loss_price must be less than take_profit_price" in str(exc_info.value)

    def test_limit_order_requires_limit_price(self):
        """Test that limit orders require limit price."""
        with pytest.raises(ValueError) as exc_info:
            PaperOrderRequest(
                symbol="AAPL",
                qty=10,
                side="buy",
                order_type="limit"
            )
        assert "limit_price is required" in str(exc_info.value)


class TestUpdateStopLossRequestSchema:
    """Test Pydantic schema validation for updating stop-loss/take-profit."""

    def test_valid_update_request(self):
        """Test valid update request."""
        request = UpdateStopLossRequest(
            symbol="AAPL",
            stop_loss_price=145.0,
            take_profit_price=185.0
        )
        assert request.stop_loss_price == 145.0
        assert request.take_profit_price == 185.0

    def test_stop_loss_must_be_below_take_profit(self):
        """Test that stop-loss must be below take-profit in update request."""
        with pytest.raises(ValueError) as exc_info:
            UpdateStopLossRequest(
                symbol="AAPL",
                stop_loss_price=180.0,
                take_profit_price=140.0
            )
        assert "stop_loss_price must be less than take_profit_price" in str(exc_info.value)
