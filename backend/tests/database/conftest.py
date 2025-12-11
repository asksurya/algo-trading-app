"""
Test configuration and fixtures for the database test suite.

This module provides comprehensive fixtures for testing the database layer
including models, enums, relationships, and session management.
"""
import os
import asyncio
from typing import AsyncGenerator, Generator
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment BEFORE importing app modules
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["SECRET_KEY"] = "test-secret-key-must-be-at-least-32-characters-long"
os.environ["ALPACA_API_KEY"] = "test-api-key"
os.environ["ALPACA_SECRET_KEY"] = "test-secret-key"

from app.models.base import Base
from app.models import (
    # User
    User,
    UserRole,
    # Strategy
    Strategy,
    StrategyTicker,
    # Trading
    Trade,
    Position,
    Order,
    PositionSnapshot,
    TradeType,
    TradeStatus,
    OrderSideEnum,
    OrderTypeEnum,
    OrderStatusEnum,
    # Risk
    RiskRule,
    RiskRuleType,
    RiskRuleAction,
    # Notification
    Notification,
    NotificationPreference,
    NotificationType,
    NotificationChannel,
    NotificationPriority,
    # API Keys
    ApiKey,
    ApiKeyAuditLog,
    BrokerType,
    ApiKeyStatus,
    # Market Data
    MarketDataCache,
    # Live Trading
    LiveStrategy,
    SignalHistory,
    LiveStrategyStatus,
    SignalType,
    # Backtesting
    Backtest,
    BacktestResult,
    BacktestTrade,
    BacktestStatus,
    # Strategy Execution
    StrategyExecution,
    StrategySignal,
    StrategyPerformance,
    ExecutionState,
    # Portfolio Analytics
    PortfolioSnapshot,
    PerformanceMetrics,
    TaxLot,
)
from app.database import reset_engine


# Test database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with transaction rollback."""
    async_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=True,
        autocommit=False,
    )
    
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


# =============================================================================
# User Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        hashed_password="hashed_password_123",
        full_name="Test User",
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user."""
    user = User(
        id=str(uuid.uuid4()),
        email="admin@example.com",
        hashed_password="hashed_admin_password",
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


# =============================================================================
# Strategy Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_strategy(db_session: AsyncSession, test_user: User) -> Strategy:
    """Create a test strategy."""
    strategy = Strategy(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        name="Test SMA Strategy",
        description="A simple moving average crossover strategy",
        strategy_type="sma_crossover",
        parameters={
            "short_window": 20,
            "long_window": 50,
            "symbol": "AAPL",
        },
        is_active=False,
        is_backtested=False,
    )
    db_session.add(strategy)
    await db_session.flush()
    await db_session.refresh(strategy)
    return strategy


@pytest_asyncio.fixture
async def test_strategy_ticker(db_session: AsyncSession, test_strategy: Strategy) -> StrategyTicker:
    """Create a strategy ticker association."""
    ticker = StrategyTicker(
        id=str(uuid.uuid4()),
        strategy_id=test_strategy.id,
        ticker="AAPL",
        allocation_percent=0.5,
        is_active=True,
    )
    db_session.add(ticker)
    await db_session.flush()
    await db_session.refresh(ticker)
    return ticker


# =============================================================================
# Trading Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_trade(db_session: AsyncSession, test_user: User, test_strategy: Strategy) -> Trade:
    """Create a test trade."""
    trade = Trade(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        strategy_id=test_strategy.id,
        ticker="AAPL",
        trade_type=TradeType.BUY,
        status=TradeStatus.FILLED,
        quantity=Decimal("100"),
        filled_quantity=Decimal("100"),
        price=Decimal("150.00"),
        filled_avg_price=Decimal("150.25"),
        order_id="order_123",
        realized_pnl=Decimal("0"),
        executed_at=datetime.utcnow(),
    )
    db_session.add(trade)
    await db_session.flush()
    await db_session.refresh(trade)
    return trade


@pytest_asyncio.fixture
async def test_position(db_session: AsyncSession, test_user: User, test_strategy: Strategy) -> Position:
    """Create a test position."""
    position = Position(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        strategy_id=test_strategy.id,
        ticker="AAPL",
        quantity=Decimal("100"),
        avg_entry_price=Decimal("150.25"),
        current_price=Decimal("155.00"),
        unrealized_pnl=Decimal("475.00"),
        realized_pnl=Decimal("0"),
    )
    db_session.add(position)
    await db_session.flush()
    await db_session.refresh(position)
    return position


@pytest_asyncio.fixture
async def test_order(db_session: AsyncSession, test_user: User) -> Order:
    """Create a test order."""
    order = Order(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        alpaca_order_id=f"alpaca_{uuid.uuid4()}",
        client_order_id=str(uuid.uuid4()),
        symbol="AAPL",
        side=OrderSideEnum.BUY,
        order_type=OrderTypeEnum.LIMIT,
        time_in_force="day",
        qty=100.0,
        limit_price=150.00,
        status=OrderStatusEnum.NEW,
        submitted_at=datetime.utcnow(),
    )
    db_session.add(order)
    await db_session.flush()
    await db_session.refresh(order)
    return order


# =============================================================================
# Risk Rule Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_risk_rule(db_session: AsyncSession, test_user: User, test_strategy: Strategy) -> RiskRule:
    """Create a test risk rule."""
    rule = RiskRule(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        strategy_id=test_strategy.id,
        name="Max Position Size",
        description="Limit position size to 5% of portfolio",
        rule_type=RiskRuleType.MAX_POSITION_SIZE,
        threshold_value=5.0,
        threshold_unit="percent",
        action=RiskRuleAction.BLOCK,
        is_active=True,
    )
    db_session.add(rule)
    await db_session.flush()
    await db_session.refresh(rule)
    return rule


# =============================================================================
# Notification Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_notification(db_session: AsyncSession, test_user: User) -> Notification:
    """Create a test notification."""
    notification = Notification(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        type=NotificationType.ORDER_FILLED,
        priority=NotificationPriority.MEDIUM,
        title="Order Filled",
        message="Your order for 100 shares of AAPL has been filled.",
        data={"order_id": "123", "symbol": "AAPL", "qty": 100},
        is_read=False,
        sent_via=["in_app"],
    )
    db_session.add(notification)
    await db_session.flush()
    await db_session.refresh(notification)
    return notification


@pytest_asyncio.fixture
async def test_notification_preference(db_session: AsyncSession, test_user: User) -> NotificationPreference:
    """Create a test notification preference."""
    pref = NotificationPreference(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        notification_type=NotificationType.ORDER_FILLED,
        channel=NotificationChannel.EMAIL,
        is_enabled=True,
        min_priority=NotificationPriority.LOW,
        email="test@example.com",
    )
    db_session.add(pref)
    await db_session.flush()
    await db_session.refresh(pref)
    return pref


# =============================================================================
# API Key Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_api_key(db_session: AsyncSession, test_user: User) -> ApiKey:
    """Create a test API key."""
    api_key = ApiKey(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        broker=BrokerType.ALPACA,
        name="My Alpaca Paper Account",
        description="Paper trading account for testing",
        encrypted_api_key="encrypted_key_data",
        encrypted_api_secret="encrypted_secret_data",
        encryption_version=1,
        is_paper_trading=True,
        status=ApiKeyStatus.ACTIVE,
        is_default=True,
    )
    db_session.add(api_key)
    await db_session.flush()
    await db_session.refresh(api_key)
    return api_key


# =============================================================================
# Backtest Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_backtest(db_session: AsyncSession, test_user: User, test_strategy: Strategy) -> Backtest:
    """Create a test backtest."""
    backtest = Backtest(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        strategy_id=test_strategy.id,
        name="SMA Backtest 2023",
        description="Testing SMA strategy performance in 2023",
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        initial_capital=100000.0,
        commission=0.001,
        slippage=0.0005,
        strategy_params={"short_window": 20, "long_window": 50},
        status=BacktestStatus.PENDING,
    )
    db_session.add(backtest)
    await db_session.flush()
    await db_session.refresh(backtest)
    return backtest


# =============================================================================
# Live Strategy Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_live_strategy(db_session: AsyncSession, test_user: User, test_strategy: Strategy) -> LiveStrategy:
    """Create a test live strategy."""
    live_strategy = LiveStrategy(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        strategy_id=test_strategy.id,
        name="Live SMA Strategy",
        symbols=["AAPL", "GOOGL", "MSFT"],
        status=LiveStrategyStatus.STOPPED,
        check_interval=300,
        auto_execute=False,
        max_position_size=10000.0,
        max_positions=5,
        daily_loss_limit=500.0,
        position_size_pct=0.02,
    )
    db_session.add(live_strategy)
    await db_session.flush()
    await db_session.refresh(live_strategy)
    return live_strategy


# =============================================================================
# Portfolio Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_portfolio_snapshot(db_session: AsyncSession, test_user: User) -> PortfolioSnapshot:
    """Create a test portfolio snapshot."""
    snapshot = PortfolioSnapshot(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        snapshot_date=datetime.utcnow(),
        total_equity=105000.0,
        cash_balance=50000.0,
        positions_value=55000.0,
        daily_pnl=500.0,
        daily_return_pct=0.48,
        total_pnl=5000.0,
        total_return_pct=5.0,
        num_positions=3,
        num_long_positions=2,
        num_short_positions=1,
    )
    db_session.add(snapshot)
    await db_session.flush()
    await db_session.refresh(snapshot)
    return snapshot


@pytest_asyncio.fixture
async def test_tax_lot(db_session: AsyncSession, test_user: User) -> TaxLot:
    """Create a test tax lot."""
    tax_lot = TaxLot(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        symbol="AAPL",
        quantity=100.0,
        acquisition_date=datetime.utcnow() - timedelta(days=30),
        acquisition_price=150.0,
        total_cost=15000.0,
        status="open",
        remaining_quantity=100.0,
    )
    db_session.add(tax_lot)
    await db_session.flush()
    await db_session.refresh(tax_lot)
    return tax_lot
