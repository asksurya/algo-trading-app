"""
Tests for Trading models (Trade, Position, Order).

This module tests:
- Trade model CRUD operations
- Position model operations
- Order model and status transitions
- Trading enums
"""
import pytest
import pytest_asyncio
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Trade, Position, Order, PositionSnapshot,
    TradeType, TradeStatus,
    OrderSideEnum, OrderTypeEnum, OrderStatusEnum,
    User, Strategy,
)


class TestTradeModel:
    """Test suite for Trade model."""
    
    @pytest.mark.asyncio
    async def test_create_trade(self, db_session: AsyncSession, test_user: User):
        """Test creating a new trade."""
        trade = Trade(
            user_id=test_user.id,
            ticker="TSLA",
            trade_type=TradeType.BUY,
            status=TradeStatus.PENDING,
            quantity=Decimal("50"),
            filled_quantity=Decimal("0"),
            price=Decimal("200.00"),
        )
        db_session.add(trade)
        await db_session.flush()
        
        assert trade.id is not None
        assert trade.ticker == "TSLA"
        assert trade.trade_type == TradeType.BUY
        assert trade.status == TradeStatus.PENDING
        assert trade.quantity == Decimal("50")
    
    @pytest.mark.asyncio
    async def test_trade_fill(self, db_session: AsyncSession, test_user: User):
        """Test filling a trade."""
        trade = Trade(
            user_id=test_user.id,
            ticker="NVDA",
            trade_type=TradeType.SELL,
            status=TradeStatus.PENDING,
            quantity=Decimal("25"),
            filled_quantity=Decimal("0"),
        )
        db_session.add(trade)
        await db_session.flush()
        
        # Simulate trade fill
        trade.status = TradeStatus.FILLED
        trade.filled_quantity = Decimal("25")
        trade.filled_avg_price = Decimal("450.75")
        trade.executed_at = datetime.utcnow()
        
        await db_session.flush()
        await db_session.refresh(trade)
        
        assert trade.status == TradeStatus.FILLED
        assert trade.filled_quantity == Decimal("25")
        assert trade.filled_avg_price == Decimal("450.75")
        assert trade.executed_at is not None
    
    @pytest.mark.asyncio
    async def test_trade_partial_fill(self, db_session: AsyncSession, test_user: User):
        """Test partially filling a trade."""
        trade = Trade(
            user_id=test_user.id,
            ticker="AMD",
            trade_type=TradeType.BUY,
            status=TradeStatus.PENDING,
            quantity=Decimal("100"),
            filled_quantity=Decimal("0"),
        )
        db_session.add(trade)
        await db_session.flush()
        
        # Partial fill
        trade.status = TradeStatus.PARTIALLY_FILLED
        trade.filled_quantity = Decimal("60")
        trade.filled_avg_price = Decimal("125.50")
        
        await db_session.flush()
        
        assert trade.status == TradeStatus.PARTIALLY_FILLED
        assert trade.filled_quantity == Decimal("60")
        assert trade.quantity - trade.filled_quantity == Decimal("40")
    
    @pytest.mark.asyncio
    async def test_trade_with_pnl(self, db_session: AsyncSession, test_user: User):
        """Test trade with realized PnL."""
        trade = Trade(
            user_id=test_user.id,
            ticker="AAPL",
            trade_type=TradeType.SELL,
            status=TradeStatus.FILLED,
            quantity=Decimal("100"),
            filled_quantity=Decimal("100"),
            price=Decimal("155.00"),
            filled_avg_price=Decimal("155.50"),
            realized_pnl=Decimal("550.00"),  # Sold at profit
            executed_at=datetime.utcnow(),
        )
        db_session.add(trade)
        await db_session.flush()
        
        assert trade.realized_pnl == Decimal("550.00")
    
    @pytest.mark.asyncio
    async def test_trade_repr(self, test_trade: Trade):
        """Test trade string representation."""
        repr_str = repr(test_trade)
        assert "Trade" in repr_str
        assert test_trade.ticker in repr_str


class TestTradeEnums:
    """Test suite for Trade enums."""
    
    def test_trade_type_values(self):
        """Test TradeType enum values."""
        assert TradeType.BUY.value == "buy"
        assert TradeType.SELL.value == "sell"
    
    def test_trade_status_values(self):
        """Test TradeStatus enum values."""
        assert TradeStatus.PENDING.value == "pending"
        assert TradeStatus.FILLED.value == "filled"
        assert TradeStatus.PARTIALLY_FILLED.value == "partially_filled"
        assert TradeStatus.CANCELLED.value == "cancelled"
        assert TradeStatus.REJECTED.value == "rejected"


class TestPositionModel:
    """Test suite for Position model."""
    
    @pytest.mark.asyncio
    async def test_create_position(self, db_session: AsyncSession, test_user: User):
        """Test creating a new position."""
        position = Position(
            user_id=test_user.id,
            ticker="GOOGL",
            quantity=Decimal("50"),
            avg_entry_price=Decimal("140.00"),
            current_price=Decimal("145.00"),
        )
        db_session.add(position)
        await db_session.flush()
        
        assert position.id is not None
        assert position.ticker == "GOOGL"
        assert position.quantity == Decimal("50")
        assert position.avg_entry_price == Decimal("140.00")
    
    @pytest.mark.asyncio
    async def test_position_unrealized_pnl(self, db_session: AsyncSession, test_user: User):
        """Test position with unrealized PnL."""
        position = Position(
            user_id=test_user.id,
            ticker="MSFT",
            quantity=Decimal("100"),
            avg_entry_price=Decimal("350.00"),
            current_price=Decimal("360.00"),
            unrealized_pnl=Decimal("1000.00"),  # 100 * (360 - 350)
            realized_pnl=Decimal("0"),
        )
        db_session.add(position)
        await db_session.flush()
        
        assert position.unrealized_pnl == Decimal("1000.00")
    
    @pytest.mark.asyncio
    async def test_close_position(self, db_session: AsyncSession, test_position: Position):
        """Test closing a position."""
        test_position.quantity = Decimal("0")
        test_position.realized_pnl = Decimal("500.00")
        test_position.closed_at = datetime.utcnow()
        
        await db_session.flush()
        await db_session.refresh(test_position)
        
        assert test_position.quantity == Decimal("0")
        assert test_position.closed_at is not None
    
    @pytest.mark.asyncio
    async def test_position_repr(self, test_position: Position):
        """Test position string representation."""
        repr_str = repr(test_position)
        assert "Position" in repr_str
        assert test_position.ticker in repr_str


class TestOrderModel:
    """Test suite for Order model."""
    
    @pytest.mark.asyncio
    async def test_create_market_order(self, db_session: AsyncSession, test_user: User):
        """Test creating a market order."""
        order = Order(
            user_id=test_user.id,
            alpaca_order_id="alp_market_123",
            symbol="AAPL",
            side=OrderSideEnum.BUY,
            order_type=OrderTypeEnum.MARKET,
            time_in_force="day",
            qty=100.0,
            status=OrderStatusEnum.NEW,
        )
        db_session.add(order)
        await db_session.flush()
        
        assert order.id is not None
        assert order.order_type == OrderTypeEnum.MARKET
        assert order.limit_price is None
        assert order.stop_price is None
    
    @pytest.mark.asyncio
    async def test_create_limit_order(self, db_session: AsyncSession, test_user: User):
        """Test creating a limit order."""
        order = Order(
            user_id=test_user.id,
            alpaca_order_id="alp_limit_123",
            symbol="GOOGL",
            side=OrderSideEnum.BUY,
            order_type=OrderTypeEnum.LIMIT,
            time_in_force="gtc",
            qty=50.0,
            limit_price=140.00,
            status=OrderStatusEnum.NEW,
        )
        db_session.add(order)
        await db_session.flush()
        
        assert order.order_type == OrderTypeEnum.LIMIT
        assert order.limit_price == 140.00
    
    @pytest.mark.asyncio
    async def test_create_stop_limit_order(self, db_session: AsyncSession, test_user: User):
        """Test creating a stop-limit order."""
        order = Order(
            user_id=test_user.id,
            alpaca_order_id="alp_stop_limit_123",
            symbol="TSLA",
            side=OrderSideEnum.SELL,
            order_type=OrderTypeEnum.STOP_LIMIT,
            time_in_force="day",
            qty=25.0,
            limit_price=190.00,
            stop_price=195.00,
            status=OrderStatusEnum.NEW,
        )
        db_session.add(order)
        await db_session.flush()
        
        assert order.order_type == OrderTypeEnum.STOP_LIMIT
        assert order.limit_price == 190.00
        assert order.stop_price == 195.00
    
    @pytest.mark.asyncio
    async def test_order_fill(self, db_session: AsyncSession, test_order: Order):
        """Test filling an order."""
        test_order.status = OrderStatusEnum.FILLED
        test_order.filled_qty = test_order.qty
        test_order.filled_avg_price = 151.25
        test_order.filled_at = datetime.utcnow()
        
        await db_session.flush()
        await db_session.refresh(test_order)
        
        assert test_order.status == OrderStatusEnum.FILLED
        assert test_order.filled_qty == test_order.qty
        assert test_order.filled_at is not None
    
    @pytest.mark.asyncio
    async def test_order_cancellation(self, db_session: AsyncSession, test_order: Order):
        """Test cancelling an order."""
        test_order.status = OrderStatusEnum.CANCELED
        test_order.canceled_at = datetime.utcnow()
        
        await db_session.flush()
        await db_session.refresh(test_order)
        
        assert test_order.status == OrderStatusEnum.CANCELED
        assert test_order.canceled_at is not None
    
    @pytest.mark.asyncio
    async def test_order_to_dict(self, test_order: Order):
        """Test order to_dict method."""
        order_dict = test_order.to_dict()
        
        assert order_dict["id"] == str(test_order.id)
        assert order_dict["symbol"] == test_order.symbol
        assert order_dict["side"] == test_order.side.value
        assert order_dict["order_type"] == test_order.order_type.value
        assert order_dict["status"] == test_order.status.value
    
    @pytest.mark.asyncio
    async def test_order_repr(self, test_order: Order):
        """Test order string representation."""
        repr_str = repr(test_order)
        assert "Order" in repr_str
        assert test_order.symbol in repr_str


class TestOrderEnums:
    """Test suite for Order enums."""
    
    def test_order_side_values(self):
        """Test OrderSideEnum values."""
        assert OrderSideEnum.BUY.value == "buy"
        assert OrderSideEnum.SELL.value == "sell"
    
    def test_order_type_values(self):
        """Test OrderTypeEnum values."""
        assert OrderTypeEnum.MARKET.value == "market"
        assert OrderTypeEnum.LIMIT.value == "limit"
        assert OrderTypeEnum.STOP.value == "stop"
        assert OrderTypeEnum.STOP_LIMIT.value == "stop_limit"
        assert OrderTypeEnum.TRAILING_STOP.value == "trailing_stop"
    
    def test_order_status_values(self):
        """Test OrderStatusEnum values."""
        assert OrderStatusEnum.NEW.value == "new"
        assert OrderStatusEnum.FILLED.value == "filled"
        assert OrderStatusEnum.CANCELED.value == "canceled"
        assert OrderStatusEnum.REJECTED.value == "rejected"


class TestPositionSnapshotModel:
    """Test suite for PositionSnapshot model."""
    
    @pytest.mark.asyncio
    async def test_create_position_snapshot(self, db_session: AsyncSession, test_user: User):
        """Test creating a position snapshot."""
        snapshot = PositionSnapshot(
            user_id=test_user.id,
            symbol="AAPL",
            qty=100.0,
            side=OrderSideEnum.BUY,
            avg_entry_price=150.00,
            current_price=155.00,
            market_value=15500.00,
            cost_basis=15000.00,
            unrealized_pl=500.00,
            unrealized_plpc=3.33,
        )
        db_session.add(snapshot)
        await db_session.flush()
        
        assert snapshot.id is not None
        assert snapshot.unrealized_pl == 500.00
        assert snapshot.unrealized_plpc == 3.33
    
    @pytest.mark.asyncio
    async def test_position_snapshot_to_dict(self, db_session: AsyncSession, test_user: User):
        """Test position snapshot to_dict method."""
        snapshot = PositionSnapshot(
            user_id=test_user.id,
            symbol="GOOGL",
            qty=50.0,
            side=OrderSideEnum.BUY,
            avg_entry_price=140.00,
            current_price=145.00,
            market_value=7250.00,
            cost_basis=7000.00,
            unrealized_pl=250.00,
            unrealized_plpc=3.57,
        )
        db_session.add(snapshot)
        await db_session.flush()
        
        snapshot_dict = snapshot.to_dict()
        
        assert snapshot_dict["symbol"] == "GOOGL"
        assert snapshot_dict["qty"] == 50.0
        assert snapshot_dict["unrealized_pl"] == 250.00
