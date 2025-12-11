"""
Tests for Backtest models (Backtest, BacktestResult, BacktestTrade).

This module tests:
- Backtest model CRUD operations
- Backtest status transitions
- BacktestResult metrics
- BacktestTrade entries
- Backtest relationships
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Backtest, BacktestResult, BacktestTrade, BacktestStatus,
    User, Strategy,
)


class TestBacktestModel:
    """Test suite for Backtest model."""
    
    @pytest.mark.asyncio
    async def test_create_backtest(self, db_session: AsyncSession, test_user: User, test_strategy: Strategy):
        """Test creating a new backtest."""
        backtest = Backtest(
            user_id=test_user.id,
            strategy_id=test_strategy.id,
            name="Q4 2023 Backtest",
            description="Testing strategy performance in Q4 2023",
            start_date=datetime(2023, 10, 1),
            end_date=datetime(2023, 12, 31),
            initial_capital=100000.0,
            commission=0.001,
            slippage=0.0005,
        )
        db_session.add(backtest)
        await db_session.flush()
        
        assert backtest.id is not None
        assert backtest.status == BacktestStatus.PENDING
        assert backtest.progress == 0
        assert backtest.initial_capital == 100000.0
    
    @pytest.mark.asyncio
    async def test_backtest_status_transitions(self, db_session: AsyncSession, test_backtest: Backtest):
        """Test backtest status transitions."""
        # Start backtest
        test_backtest.status = BacktestStatus.RUNNING
        test_backtest.started_at = datetime.utcnow()
        test_backtest.progress = 10
        
        await db_session.flush()
        await db_session.refresh(test_backtest)
        
        assert test_backtest.status == BacktestStatus.RUNNING
        assert test_backtest.started_at is not None
        
        # Complete backtest
        test_backtest.status = BacktestStatus.COMPLETED
        test_backtest.completed_at = datetime.utcnow()
        test_backtest.progress = 100
        test_backtest.duration_seconds = 45.5
        
        await db_session.flush()
        await db_session.refresh(test_backtest)
        
        assert test_backtest.status == BacktestStatus.COMPLETED
        assert test_backtest.progress == 100
    
    @pytest.mark.asyncio
    async def test_backtest_failure(self, db_session: AsyncSession, test_backtest: Backtest):
        """Test backtest failure handling."""
        test_backtest.status = BacktestStatus.RUNNING
        test_backtest.started_at = datetime.utcnow()
        
        # Simulate failure
        test_backtest.status = BacktestStatus.FAILED
        test_backtest.error_message = "Insufficient data for date range"
        
        await db_session.flush()
        await db_session.refresh(test_backtest)
        
        assert test_backtest.status == BacktestStatus.FAILED
        assert "Insufficient data" in test_backtest.error_message
    
    @pytest.mark.asyncio
    async def test_backtest_with_summary_results(
        self, db_session: AsyncSession, test_backtest: Backtest
    ):
        """Test backtest with summary results populated."""
        test_backtest.status = BacktestStatus.COMPLETED
        test_backtest.total_trades = 42
        test_backtest.winning_trades = 28
        test_backtest.losing_trades = 14
        test_backtest.total_return = 15.5
        test_backtest.total_pnl = 15500.0
        test_backtest.max_drawdown = -8.3
        test_backtest.sharpe_ratio = 1.25
        test_backtest.win_rate = 66.67
        
        await db_session.flush()
        await db_session.refresh(test_backtest)
        
        assert test_backtest.total_trades == 42
        assert test_backtest.winning_trades == 28
        assert test_backtest.win_rate == 66.67
    
    @pytest.mark.asyncio
    async def test_backtest_strategy_params_override(
        self, db_session: AsyncSession, test_user: User, test_strategy: Strategy
    ):
        """Test backtest with strategy parameter overrides."""
        backtest = Backtest(
            user_id=test_user.id,
            strategy_id=test_strategy.id,
            name="Parameter Optimization Test",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 6, 30),
            initial_capital=50000.0,
            strategy_params={
                "short_window": 10,  # Override default
                "long_window": 30,   # Override default
                "stop_loss": 0.02,
            },
        )
        db_session.add(backtest)
        await db_session.flush()
        await db_session.refresh(backtest)
        
        assert backtest.strategy_params["short_window"] == 10
        assert backtest.strategy_params["stop_loss"] == 0.02
    
    @pytest.mark.asyncio
    async def test_backtest_repr(self, test_backtest: Backtest):
        """Test backtest string representation."""
        repr_str = repr(test_backtest)
        assert "Backtest" in repr_str
        assert test_backtest.name in repr_str


class TestBacktestStatusEnum:
    """Test suite for BacktestStatus enum."""
    
    def test_backtest_status_values(self):
        """Test BacktestStatus enum values."""
        assert BacktestStatus.PENDING.value == "pending"
        assert BacktestStatus.RUNNING.value == "running"
        assert BacktestStatus.COMPLETED.value == "completed"
        assert BacktestStatus.FAILED.value == "failed"
        assert BacktestStatus.CANCELLED.value == "cancelled"
    
    def test_backtest_status_iteration(self):
        """Test iterating over all backtest statuses."""
        all_statuses = list(BacktestStatus)
        assert len(all_statuses) == 5


class TestBacktestResultModel:
    """Test suite for BacktestResult model."""
    
    @pytest.mark.asyncio
    async def test_create_backtest_result(self, db_session: AsyncSession, test_backtest: Backtest):
        """Test creating a backtest result."""
        result = BacktestResult(
            backtest_id=test_backtest.id,
            final_capital=115500.0,
            total_return_pct=15.5,
            annualized_return=31.0,
            total_trades=42,
            winning_trades=28,
            losing_trades=14,
            win_rate=66.67,
            gross_profit=22000.0,
            gross_loss=6500.0,
            net_profit=15500.0,
            profit_factor=3.38,
            avg_trade_pnl=369.05,
            avg_winning_trade=785.71,
            avg_losing_trade=-464.29,
            largest_win=2500.0,
            largest_loss=-1200.0,
            max_drawdown_pct=8.3,
            max_drawdown_dollars=8300.0,
            sharpe_ratio=1.25,
            sortino_ratio=1.85,
            calmar_ratio=1.87,
            equity_curve={"dates": [], "values": []},
        )
        db_session.add(result)
        await db_session.flush()
        
        assert result.id is not None
        assert result.backtest_id == test_backtest.id
        assert result.final_capital == 115500.0
        assert result.profit_factor == 3.38
    
    @pytest.mark.asyncio
    async def test_backtest_result_equity_curve(self, db_session: AsyncSession, test_backtest: Backtest):
        """Test backtest result with equity curve data."""
        equity_data = {
            "dates": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "values": [100000, 100500, 101200],
        }
        
        result = BacktestResult(
            backtest_id=test_backtest.id,
            final_capital=101200.0,
            total_return_pct=1.2,
            annualized_return=300.0,  # Extrapolated
            total_trades=5,
            winning_trades=4,
            losing_trades=1,
            win_rate=80.0,
            net_profit=1200.0,
            avg_trade_pnl=240.0,
            max_drawdown_pct=0.5,
            max_drawdown_dollars=500.0,
            equity_curve=equity_data,
        )
        db_session.add(result)
        await db_session.flush()
        await db_session.refresh(result)
        
        assert len(result.equity_curve["dates"]) == 3
        assert result.equity_curve["values"][-1] == 101200
    
    @pytest.mark.asyncio
    async def test_backtest_result_monthly_returns(self, db_session: AsyncSession, test_backtest: Backtest):
        """Test backtest result with monthly returns data."""
        monthly_data = {
            "2023-01": 2.5,
            "2023-02": -1.2,
            "2023-03": 3.8,
            "2023-04": 1.5,
        }
        
        result = BacktestResult(
            backtest_id=test_backtest.id,
            final_capital=106000.0,
            total_return_pct=6.0,
            annualized_return=18.0,
            total_trades=20,
            winning_trades=14,
            losing_trades=6,
            win_rate=70.0,
            net_profit=6000.0,
            avg_trade_pnl=300.0,
            max_drawdown_pct=3.0,
            max_drawdown_dollars=3000.0,
            equity_curve={},
            monthly_returns=monthly_data,
        )
        db_session.add(result)
        await db_session.flush()
        await db_session.refresh(result)
        
        assert result.monthly_returns["2023-01"] == 2.5
        assert result.monthly_returns["2023-02"] == -1.2
    
    @pytest.mark.asyncio
    async def test_backtest_result_repr(self, db_session: AsyncSession, test_backtest: Backtest):
        """Test backtest result string representation."""
        result = BacktestResult(
            backtest_id=test_backtest.id,
            final_capital=100000.0,
            total_return_pct=0.0,
            annualized_return=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            net_profit=0.0,
            avg_trade_pnl=0.0,
            max_drawdown_pct=0.0,
            max_drawdown_dollars=0.0,
            equity_curve={},
        )
        db_session.add(result)
        await db_session.flush()
        
        repr_str = repr(result)
        assert "BacktestResult" in repr_str


class TestBacktestTradeModel:
    """Test suite for BacktestTrade model."""
    
    @pytest.mark.asyncio
    async def test_create_backtest_trade(self, db_session: AsyncSession, test_backtest: Backtest):
        """Test creating a backtest trade."""
        trade = BacktestTrade(
            backtest_id=test_backtest.id,
            symbol="AAPL",
            side="buy",
            quantity=100.0,
            entry_price=150.00,
            entry_date=datetime(2023, 1, 15),
            entry_signal="sma_crossover_bullish",
        )
        db_session.add(trade)
        await db_session.flush()
        
        assert trade.id is not None
        assert trade.symbol == "AAPL"
        assert trade.side == "buy"
        assert trade.is_open is False  # Default
    
    @pytest.mark.asyncio
    async def test_backtest_trade_with_exit(self, db_session: AsyncSession, test_backtest: Backtest):
        """Test backtest trade with exit data."""
        trade = BacktestTrade(
            backtest_id=test_backtest.id,
            symbol="GOOGL",
            side="buy",
            quantity=50.0,
            entry_price=140.00,
            exit_price=155.00,
            entry_date=datetime(2023, 2, 1),
            exit_date=datetime(2023, 2, 15),
            pnl=750.0,  # 50 * (155 - 140)
            pnl_pct=10.71,
            commission=2.80,  # Simulated
            slippage=0.50,
            duration_hours=336.0,  # 14 days
            entry_signal="momentum_entry",
            exit_signal="take_profit",
            is_open=False,
        )
        db_session.add(trade)
        await db_session.flush()
        await db_session.refresh(trade)
        
        assert trade.exit_price == 155.00
        assert trade.pnl == 750.0
        assert trade.pnl_pct == 10.71
        assert trade.exit_signal == "take_profit"
    
    @pytest.mark.asyncio
    async def test_backtest_trade_indicators(self, db_session: AsyncSession, test_backtest: Backtest):
        """Test backtest trade with indicator values at entry."""
        indicators = {
            "sma_20": 148.50,
            "sma_50": 145.00,
            "rsi": 65.3,
            "volume": 15000000,
        }
        
        trade = BacktestTrade(
            backtest_id=test_backtest.id,
            symbol="MSFT",
            side="buy",
            quantity=30.0,
            entry_price=350.00,
            entry_date=datetime(2023, 3, 1),
            indicators_at_entry=indicators,
            is_open=True,
        )
        db_session.add(trade)
        await db_session.flush()
        await db_session.refresh(trade)
        
        assert trade.indicators_at_entry["sma_20"] == 148.50
        assert trade.indicators_at_entry["rsi"] == 65.3
        assert trade.is_open is True
    
    @pytest.mark.asyncio
    async def test_multiple_trades_per_backtest(self, db_session: AsyncSession, test_backtest: Backtest):
        """Test creating multiple trades for a backtest."""
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "META"]
        
        for i, symbol in enumerate(symbols):
            trade = BacktestTrade(
                backtest_id=test_backtest.id,
                symbol=symbol,
                side="buy" if i % 2 == 0 else "sell",
                quantity=float(10 + i * 5),
                entry_price=float(100 + i * 10),
                entry_date=datetime(2023, 1, 1) + timedelta(days=i),
            )
            db_session.add(trade)
        
        await db_session.flush()
        
        # Fetch all trades for the backtest
        result = await db_session.execute(
            select(BacktestTrade).where(BacktestTrade.backtest_id == test_backtest.id)
        )
        trades = result.scalars().all()
        
        assert len(trades) == 5
    
    @pytest.mark.asyncio
    async def test_backtest_trade_repr(self, db_session: AsyncSession, test_backtest: Backtest):
        """Test backtest trade string representation."""
        trade = BacktestTrade(
            backtest_id=test_backtest.id,
            symbol="NVDA",
            side="buy",
            quantity=20.0,
            entry_price=450.00,
            entry_date=datetime(2023, 4, 1),
        )
        db_session.add(trade)
        await db_session.flush()
        
        repr_str = repr(trade)
        assert "BacktestTrade" in repr_str
        assert "NVDA" in repr_str


class TestBacktestRelationships:
    """Test suite for Backtest model relationships."""
    
    @pytest.mark.asyncio
    async def test_backtest_creates_with_result(self, db_session: AsyncSession, test_user: User, test_strategy: Strategy):
        """Test backtest and result creation together."""
        # Create backtest
        backtest = Backtest(
            user_id=test_user.id,
            strategy_id=test_strategy.id,
            name="Relationship Test",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            initial_capital=100000.0,
        )
        db_session.add(backtest)
        await db_session.flush()
        
        # Create result linking to backtest
        result = BacktestResult(
            backtest_id=backtest.id,
            final_capital=110000.0,
            total_return_pct=10.0,
            annualized_return=20.0,
            total_trades=30,
            winning_trades=20,
            losing_trades=10,
            win_rate=66.67,
            net_profit=10000.0,
            avg_trade_pnl=333.33,
            max_drawdown_pct=5.0,
            max_drawdown_dollars=5000.0,
            equity_curve={},
        )
        db_session.add(result)
        await db_session.flush()
        
        # Verify the result is linked
        assert result.backtest_id == backtest.id
        assert result.final_capital == 110000.0
    
    @pytest.mark.asyncio
    async def test_backtest_creates_with_trades(self, db_session: AsyncSession, test_user: User, test_strategy: Strategy):
        """Test backtest with trades creation."""
        # Create backtest
        backtest = Backtest(
            user_id=test_user.id,
            strategy_id=test_strategy.id,
            name="Trades Test",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            initial_capital=100000.0,
        )
        db_session.add(backtest)
        await db_session.flush()
        
        # Create trades
        for i in range(3):
            trade = BacktestTrade(
                backtest_id=backtest.id,
                symbol=f"SYM{i}",
                side="buy",
                quantity=10.0,
                entry_price=100.0,
                entry_date=datetime(2023, 1, 1) + timedelta(days=i),
            )
            db_session.add(trade)
        
        await db_session.flush()
        
        # Query trades directly
        result = await db_session.execute(
            select(BacktestTrade).where(BacktestTrade.backtest_id == backtest.id)
        )
        trades = result.scalars().all()
        assert len(trades) == 3
    
    @pytest.mark.asyncio
    async def test_cascade_delete_on_backtest(self, db_session: AsyncSession, test_user: User, test_strategy: Strategy):
        """Test that deleting a backtest cascades to results and trades."""
        # Create a backtest with result and trades
        backtest = Backtest(
            user_id=test_user.id,
            strategy_id=test_strategy.id,
            name="Cascade Test Backtest",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            initial_capital=100000.0,
        )
        db_session.add(backtest)
        await db_session.flush()
        
        result = BacktestResult(
            backtest_id=backtest.id,
            final_capital=100000.0,
            total_return_pct=0.0,
            annualized_return=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            net_profit=0.0,
            avg_trade_pnl=0.0,
            max_drawdown_pct=0.0,
            max_drawdown_dollars=0.0,
            equity_curve={},
        )
        db_session.add(result)
        
        trade = BacktestTrade(
            backtest_id=backtest.id,
            symbol="TEST",
            side="buy",
            quantity=10.0,
            entry_price=100.0,
            entry_date=datetime(2023, 1, 1),
        )
        db_session.add(trade)
        await db_session.flush()
        
        backtest_id = backtest.id
        result_id = result.id
        trade_id = trade.id
        
        # Delete the backtest
        await db_session.delete(backtest)
        await db_session.flush()
        
        # Verify cascade delete
        result_check = await db_session.execute(
            select(BacktestResult).where(BacktestResult.id == result_id)
        )
        assert result_check.scalar_one_or_none() is None
        
        trade_check = await db_session.execute(
            select(BacktestTrade).where(BacktestTrade.id == trade_id)
        )
        assert trade_check.scalar_one_or_none() is None
