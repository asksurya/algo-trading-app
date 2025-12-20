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

async def test_create_trade_flow():
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

    # Run the function
    print("Running create_trade...")
    try:
        result = await create_trade(trade_data, current_user, mock_db)

        print(f"Trade created: {result}")
        print(f"Trade status: {result.status}")
        print(f"Trade order_id: {result.order_id}")

        # Verify DB interactions
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        # In the current implementation, order_id should be None (or not set from broker)
        if result.order_id is None:
             print("SUCCESS: order_id is None as expected (no broker execution yet)")
        else:
             print(f"FAIL: order_id is {result.order_id} (unexpected)")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_create_trade_flow())
