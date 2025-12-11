"""
Tests for Strategy and StrategyTicker models.

This module tests:
- Strategy model CRUD operations
- StrategyTicker association table
- Strategy parameters JSON handling
- Strategy relationships
"""
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Strategy, StrategyTicker, User


class TestStrategyModel:
    """Test suite for Strategy model."""
    
    @pytest.mark.asyncio
    async def test_create_strategy(self, db_session: AsyncSession, test_user: User):
        """Test creating a new strategy."""
        strategy = Strategy(
            user_id=test_user.id,
            name="Bollinger Bands Strategy",
            description="Mean reversion strategy using Bollinger Bands",
            strategy_type="bollinger_bands",
            parameters={
                "period": 20,
                "std_dev": 2.0,
                "symbols": ["AAPL", "GOOGL"],
            },
        )
        db_session.add(strategy)
        await db_session.flush()
        
        assert strategy.id is not None
        assert strategy.user_id == test_user.id
        assert strategy.name == "Bollinger Bands Strategy"
        assert strategy.strategy_type == "bollinger_bands"
        assert strategy.is_active is False
        assert strategy.is_backtested is False
    
    @pytest.mark.asyncio
    async def test_strategy_parameters_json(self, db_session: AsyncSession, test_user: User):
        """Test strategy parameters JSON field."""
        params = {
            "short_window": 10,
            "long_window": 50,
            "symbols": ["AAPL", "GOOGL", "MSFT"],
            "options": {
                "use_volume": True,
                "max_positions": 5,
            },
        }
        
        strategy = Strategy(
            user_id=test_user.id,
            name="Complex Strategy",
            strategy_type="custom",
            parameters=params,
        )
        db_session.add(strategy)
        await db_session.flush()
        await db_session.refresh(strategy)
        
        # Verify JSON is stored and retrieved correctly
        assert strategy.parameters["short_window"] == 10
        assert strategy.parameters["symbols"] == ["AAPL", "GOOGL", "MSFT"]
        assert strategy.parameters["options"]["use_volume"] is True
    
    @pytest.mark.asyncio
    async def test_strategy_backtest_results_json(self, db_session: AsyncSession, test_user: User):
        """Test strategy backtest results JSON field."""
        strategy = Strategy(
            user_id=test_user.id,
            name="Backtested Strategy",
            strategy_type="sma_crossover",
            parameters={"short": 20, "long": 50},
            is_backtested=True,
            backtest_results={
                "total_return": 15.5,
                "sharpe_ratio": 1.25,
                "max_drawdown": -8.3,
                "total_trades": 42,
            },
        )
        db_session.add(strategy)
        await db_session.flush()
        await db_session.refresh(strategy)
        
        assert strategy.is_backtested is True
        assert strategy.backtest_results["total_return"] == 15.5
        assert strategy.backtest_results["sharpe_ratio"] == 1.25
    
    @pytest.mark.asyncio
    async def test_update_strategy(self, db_session: AsyncSession, test_strategy: Strategy):
        """Test updating a strategy."""
        test_strategy.name = "Updated Strategy Name"
        test_strategy.is_active = True
        
        await db_session.flush()
        await db_session.refresh(test_strategy)
        
        assert test_strategy.name == "Updated Strategy Name"
        assert test_strategy.is_active is True
    
    @pytest.mark.asyncio
    async def test_update_strategy_parameters(self, db_session: AsyncSession, test_user: User):
        """Test updating strategy parameters with full replacement."""
        strategy = Strategy(
            user_id=test_user.id,
            name="Param Update Test",
            strategy_type="test",
            parameters={"original": 1},
        )
        db_session.add(strategy)
        await db_session.flush()
        
        # Update with full replacement (JSON columns require this)
        strategy.parameters = {**strategy.parameters, "new_param": 100}
        await db_session.flush()
        await db_session.refresh(strategy)
        
        assert strategy.parameters["new_param"] == 100
    
    @pytest.mark.asyncio
    async def test_strategy_repr(self, test_strategy: Strategy):
        """Test strategy string representation."""
        repr_str = repr(test_strategy)
        assert "Strategy" in repr_str
        assert test_strategy.name in repr_str
        assert test_strategy.strategy_type in repr_str
    
    @pytest.mark.asyncio
    async def test_fetch_strategy_by_type(self, db_session: AsyncSession, test_user: User):
        """Test fetching strategies by type."""
        # Create multiple strategies
        for strategy_type in ["sma_crossover", "momentum", "sma_crossover"]:
            strategy = Strategy(
                user_id=test_user.id,
                name=f"{strategy_type} Strategy",
                strategy_type=strategy_type,
                parameters={},
            )
            db_session.add(strategy)
        await db_session.flush()
        
        # Fetch SMA crossover strategies
        result = await db_session.execute(
            select(Strategy).where(Strategy.strategy_type == "sma_crossover")
        )
        sma_strategies = result.scalars().all()
        
        assert len(sma_strategies) == 2


class TestStrategyTickerModel:
    """Test suite for StrategyTicker model."""
    
    @pytest.mark.asyncio
    async def test_create_strategy_ticker(self, db_session: AsyncSession, test_strategy: Strategy):
        """Test creating a strategy ticker association."""
        ticker = StrategyTicker(
            strategy_id=test_strategy.id,
            ticker="GOOGL",
            allocation_percent=0.3,
            is_active=True,
        )
        db_session.add(ticker)
        await db_session.flush()
        
        assert ticker.id is not None
        assert ticker.strategy_id == test_strategy.id
        assert ticker.ticker == "GOOGL"
        assert ticker.allocation_percent == 0.3
        assert ticker.is_active is True
    
    @pytest.mark.asyncio
    async def test_multiple_tickers_per_strategy(self, db_session: AsyncSession, test_strategy: Strategy):
        """Test adding multiple tickers to a strategy."""
        tickers = ["AAPL", "GOOGL", "MSFT", "AMZN", "META"]
        
        for i, symbol in enumerate(tickers):
            ticker = StrategyTicker(
                strategy_id=test_strategy.id,
                ticker=symbol,
                allocation_percent=0.2,
                is_active=True,
            )
            db_session.add(ticker)
        
        await db_session.flush()
        
        # Fetch all tickers for the strategy
        result = await db_session.execute(
            select(StrategyTicker).where(StrategyTicker.strategy_id == test_strategy.id)
        )
        strategy_tickers = result.scalars().all()
        
        assert len(strategy_tickers) == 5
    
    @pytest.mark.asyncio
    async def test_strategy_ticker_repr(self, test_strategy_ticker: StrategyTicker):
        """Test strategy ticker string representation."""
        repr_str = repr(test_strategy_ticker)
        assert "StrategyTicker" in repr_str
        assert test_strategy_ticker.ticker in repr_str
    
    @pytest.mark.asyncio
    async def test_deactivate_ticker(self, db_session: AsyncSession, test_strategy_ticker: StrategyTicker):
        """Test deactivating a strategy ticker."""
        test_strategy_ticker.is_active = False
        await db_session.flush()
        await db_session.refresh(test_strategy_ticker)
        
        assert test_strategy_ticker.is_active is False


class TestStrategyRelationships:
    """Test suite for Strategy relationships."""
    
    @pytest.mark.asyncio
    async def test_strategy_risk_rules_relationship(
        self, db_session: AsyncSession, test_strategy: Strategy, test_risk_rule
    ):
        """Test strategy to risk rules relationship."""
        await db_session.refresh(test_strategy)
        
        assert test_risk_rule.strategy_id == test_strategy.id
