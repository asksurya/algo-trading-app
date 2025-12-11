"""
Tests for SoftDeleteMixin and TimestampMixin functionality.

This module tests:
- Soft delete behavior
- Timestamp auto-population
- Restore functionality
"""
import pytest
import pytest_asyncio
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Order, Trade, Backtest,
    User, Strategy, BacktestStatus,
    OrderSideEnum, OrderTypeEnum, OrderStatusEnum,
    TradeType, TradeStatus,
)


class TestSoftDeleteMixin:
    """Test suite for SoftDeleteMixin functionality."""
    
    @pytest.mark.asyncio
    async def test_order_soft_delete_defaults(self, db_session: AsyncSession, test_user: User):
        """Test that soft delete fields have correct defaults."""
        order = Order(
            user_id=test_user.id,
            alpaca_order_id="test_123",
            symbol="AAPL",
            side=OrderSideEnum.BUY,
            order_type=OrderTypeEnum.MARKET,
            time_in_force="day",
            qty=100.0,
            status=OrderStatusEnum.NEW,
        )
        db_session.add(order)
        await db_session.flush()
        
        assert order.is_deleted is False
        assert order.deleted_at is None
    
    @pytest.mark.asyncio
    async def test_order_soft_delete(self, db_session: AsyncSession, test_user: User):
        """Test soft deleting an order."""
        order = Order(
            user_id=test_user.id,
            alpaca_order_id="delete_test_123",
            symbol="GOOGL",
            side=OrderSideEnum.SELL,
            order_type=OrderTypeEnum.LIMIT,
            time_in_force="gtc",
            qty=50.0,
            limit_price=140.0,
            status=OrderStatusEnum.NEW,
        )
        db_session.add(order)
        await db_session.flush()
        
        # Soft delete the order
        order.soft_delete()
        await db_session.flush()
        await db_session.refresh(order)
        
        assert order.is_deleted is True
        assert order.deleted_at is not None
        assert isinstance(order.deleted_at, datetime)
    
    @pytest.mark.asyncio
    async def test_order_restore(self, db_session: AsyncSession, test_user: User):
        """Test restoring a soft-deleted order."""
        order = Order(
            user_id=test_user.id,
            alpaca_order_id="restore_test_123",
            symbol="MSFT",
            side=OrderSideEnum.BUY,
            order_type=OrderTypeEnum.MARKET,
            time_in_force="day",
            qty=25.0,
            status=OrderStatusEnum.NEW,
        )
        db_session.add(order)
        await db_session.flush()
        
        # Soft delete
        order.soft_delete()
        await db_session.flush()
        
        assert order.is_deleted is True
        
        # Restore
        order.restore()
        await db_session.flush()
        await db_session.refresh(order)
        
        assert order.is_deleted is False
        assert order.deleted_at is None
    
    @pytest.mark.asyncio
    async def test_filter_soft_deleted_orders(self, db_session: AsyncSession, test_user: User):
        """Test filtering out soft-deleted orders in queries."""
        # Create active order
        active_order = Order(
            user_id=test_user.id,
            alpaca_order_id="active_123",
            symbol="AAPL",
            side=OrderSideEnum.BUY,
            order_type=OrderTypeEnum.MARKET,
            time_in_force="day",
            qty=100.0,
            status=OrderStatusEnum.FILLED,
        )
        
        # Create soft-deleted order
        deleted_order = Order(
            user_id=test_user.id,
            alpaca_order_id="deleted_123",
            symbol="GOOGL",
            side=OrderSideEnum.BUY,
            order_type=OrderTypeEnum.MARKET,
            time_in_force="day",
            qty=50.0,
            status=OrderStatusEnum.CANCELED,
        )
        
        db_session.add_all([active_order, deleted_order])
        await db_session.flush()
        
        # Soft delete one order
        deleted_order.soft_delete()
        await db_session.flush()
        
        # Query active orders only
        result = await db_session.execute(
            select(Order)
            .where(Order.user_id == test_user.id)
            .where(Order.is_deleted == False)
        )
        active_orders = result.scalars().all()
        
        assert len(active_orders) == 1
        assert active_orders[0].symbol == "AAPL"
    
    @pytest.mark.asyncio
    async def test_trade_soft_delete(self, db_session: AsyncSession, test_user: User):
        """Test soft deleting a trade."""
        trade = Trade(
            user_id=test_user.id,
            ticker="NVDA",
            trade_type=TradeType.BUY,
            status=TradeStatus.FILLED,
            quantity=100,
            filled_quantity=100,
            price=450.0,
            filled_avg_price=450.25,
        )
        db_session.add(trade)
        await db_session.flush()
        
        # Verify defaults
        assert trade.is_deleted is False
        
        # Soft delete
        trade.soft_delete()
        await db_session.flush()
        
        assert trade.is_deleted is True
        assert trade.deleted_at is not None
    
    @pytest.mark.asyncio
    async def test_backtest_soft_delete(
        self, db_session: AsyncSession, test_user: User, test_strategy: Strategy
    ):
        """Test soft deleting a backtest."""
        backtest = Backtest(
            user_id=test_user.id,
            strategy_id=test_strategy.id,
            name="Soft Delete Test",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            initial_capital=100000.0,
            status=BacktestStatus.COMPLETED,
        )
        db_session.add(backtest)
        await db_session.flush()
        
        # Verify defaults
        assert backtest.is_deleted is False
        
        # Soft delete
        backtest.soft_delete()
        await db_session.flush()
        
        assert backtest.is_deleted is True
        assert backtest.deleted_at is not None


class TestTimestampMixin:
    """Test suite for TimestampMixin functionality."""
    
    @pytest.mark.asyncio
    async def test_order_timestamps(self, db_session: AsyncSession, test_user: User):
        """Test that timestamp fields are populated on Order."""
        order = Order(
            user_id=test_user.id,
            alpaca_order_id="timestamp_test_123",
            symbol="TSLA",
            side=OrderSideEnum.BUY,
            order_type=OrderTypeEnum.MARKET,
            time_in_force="day",
            qty=10.0,
            status=OrderStatusEnum.NEW,
        )
        db_session.add(order)
        await db_session.flush()
        await db_session.refresh(order)
        
        # Note: Order model may have its own timestamp fields
        # This test verifies created_at is populated
        assert order.created_at is not None
    
    @pytest.mark.asyncio
    async def test_strategy_timestamps(self, db_session: AsyncSession, test_user: User):
        """Test that timestamp fields are auto-populated on Strategy."""
        from app.models import Strategy
        
        strategy = Strategy(
            user_id=test_user.id,
            name="Timestamp Test Strategy",
            strategy_type="test",
            parameters={},
        )
        db_session.add(strategy)
        await db_session.flush()
        await db_session.refresh(strategy)
        
        assert strategy.created_at is not None
        assert strategy.updated_at is not None
        assert strategy.created_at <= strategy.updated_at
