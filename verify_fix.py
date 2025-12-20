import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from decimal import Decimal
import sys
import os

# Add backend directory to path
sys.path.append(os.path.abspath("backend"))

from app.api.v1.trades import create_trade
from app.schemas.trade import TradeCreate
from app.models.trade import TradeStatus, TradeType
from app.models.user import User

async def verify_fix():
    # Mock data
    trade_data = TradeCreate(
        ticker="AAPL",
        trade_type=TradeType.BUY,
        quantity=Decimal("10"),
        price=Decimal("150.00"),
        strategy_id="strategy_123"
    )

    current_user = User(
        id="user_123",
        email="test@example.com"
    )

    # Mock DB session
    mock_db = AsyncMock()

    # Mock Order Execution
    with patch('app.api.v1.trades.get_order_executor') as mock_get_executor:
        mock_executor = AsyncMock()
        mock_get_executor.return_value = mock_executor

        # Setup successful order return
        mock_order = {
            "id": "alpaca_order_123",
            "status": "new",
            "filled_qty": 0,
            "filled_avg_price": None
        }
        mock_executor.place_order.return_value = mock_order

        print("Running create_trade with successful execution...")
        result = await create_trade(trade_data, current_user, mock_db)

        print(f"Trade created: {result}")
        print(f"Trade status: {result.status}")
        print(f"Trade order_id: {result.order_id}")

        # Verify executor was called correctly
        mock_executor.place_order.assert_called_once()
        call_args = mock_executor.place_order.call_args
        print(f"Executor called with: {call_args}")

        assert result.order_id == "alpaca_order_123"
        assert result.status == TradeStatus.PENDING # Default unless filled immediately

        print("SUCCESS: Trade creation triggered order execution.")

if __name__ == "__main__":
    asyncio.run(verify_fix())
