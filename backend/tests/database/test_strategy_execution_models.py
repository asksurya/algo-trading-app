"""
Tests for Strategy Execution models (StrategyExecution, StrategySignal, StrategyPerformance).

This module tests automated strategy execution tracking, signals, and performance metrics.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    StrategyExecution, StrategySignal, StrategyPerformance,
    ExecutionState, SignalType,
    User, Strategy,
)


class TestStrategyExecutionModel:
    """Test suite for StrategyExecution model."""
    
    @pytest.mark.asyncio
    async def test_create_strategy_execution(
        self, db_session: AsyncSession, test_strategy: Strategy
    ):
        """Test creating a strategy execution."""
        execution = StrategyExecution(
            strategy_id=test_strategy.id,
            state=ExecutionState.INACTIVE,
            max_trades_per_day=10,
            max_loss_per_day=1000.0,
            max_consecutive_losses=3,
            is_dry_run=True,
        )
        db_session.add(execution)
        await db_session.flush()
        
        assert execution.id is not None
        assert execution.state == ExecutionState.INACTIVE
        assert execution.trades_today == 0
        assert execution.is_dry_run is True
    
    @pytest.mark.asyncio
    async def test_strategy_execution_activation(
        self, db_session: AsyncSession, test_strategy: Strategy
    ):
        """Test activating a strategy execution."""
        execution = StrategyExecution(
            strategy_id=test_strategy.id,
            state=ExecutionState.INACTIVE,
        )
        db_session.add(execution)
        await db_session.flush()
        
        # Activate
        execution.state = ExecutionState.ACTIVE
        execution.last_evaluated_at = datetime.utcnow()
        
        await db_session.flush()
        await db_session.refresh(execution)
        
        assert execution.state == ExecutionState.ACTIVE
        assert execution.last_evaluated_at is not None
    
    @pytest.mark.asyncio
    async def test_strategy_execution_circuit_breaker(
        self, db_session: AsyncSession, test_strategy: Strategy
    ):
        """Test strategy execution circuit breaker."""
        execution = StrategyExecution(
            strategy_id=test_strategy.id,
            state=ExecutionState.ACTIVE,
            max_consecutive_losses=3,
        )
        db_session.add(execution)
        await db_session.flush()
        
        # Simulate consecutive losses triggering circuit breaker
        execution.consecutive_losses = 4
        execution.state = ExecutionState.CIRCUIT_BREAKER
        execution.circuit_breaker_reset_at = datetime.utcnow() + timedelta(hours=1)
        
        await db_session.flush()
        await db_session.refresh(execution)
        
        assert execution.state == ExecutionState.CIRCUIT_BREAKER
        assert execution.circuit_breaker_reset_at is not None
    
    @pytest.mark.asyncio
    async def test_strategy_execution_daily_tracking(
        self, db_session: AsyncSession, test_strategy: Strategy
    ):
        """Test daily trade and loss tracking."""
        execution = StrategyExecution(
            strategy_id=test_strategy.id,
            state=ExecutionState.ACTIVE,
            max_trades_per_day=10,
            max_loss_per_day=1000.0,
        )
        db_session.add(execution)
        await db_session.flush()
        
        # Record trades
        execution.trades_today = 5
        execution.loss_today = -350.0
        execution.last_trade_at = datetime.utcnow()
        
        await db_session.flush()
        await db_session.refresh(execution)
        
        assert execution.trades_today == 5
        assert execution.loss_today == -350.0
        
        # Check against limits
        assert execution.trades_today < execution.max_trades_per_day
        assert abs(execution.loss_today) < execution.max_loss_per_day
    
    @pytest.mark.asyncio
    async def test_strategy_execution_position_tracking(
        self, db_session: AsyncSession, test_strategy: Strategy
    ):
        """Test open position tracking."""
        execution = StrategyExecution(
            strategy_id=test_strategy.id,
            state=ExecutionState.ACTIVE,
        )
        db_session.add(execution)
        await db_session.flush()
        
        # Open a position
        execution.has_open_position = True
        execution.current_position_qty = 100.0
        execution.current_position_entry_price = 150.25
        
        await db_session.flush()
        await db_session.refresh(execution)
        
        assert execution.has_open_position is True
        assert execution.current_position_qty == 100.0
    
    @pytest.mark.asyncio
    async def test_strategy_execution_error_handling(
        self, db_session: AsyncSession, test_strategy: Strategy
    ):
        """Test error tracking in strategy execution."""
        execution = StrategyExecution(
            strategy_id=test_strategy.id,
            state=ExecutionState.ACTIVE,
        )
        db_session.add(execution)
        await db_session.flush()
        
        # Record an error
        execution.state = ExecutionState.ERROR
        execution.last_error = "Failed to fetch market data: Connection timeout"
        execution.error_count = 1
        
        await db_session.flush()
        await db_session.refresh(execution)
        
        assert execution.state == ExecutionState.ERROR
        assert "Connection timeout" in execution.last_error
        assert execution.error_count == 1
    
    @pytest.mark.asyncio
    async def test_strategy_execution_config_overrides(
        self, db_session: AsyncSession, test_strategy: Strategy
    ):
        """Test configuration overrides for strategy execution."""
        config = {
            "short_window": 15,  # Override default
            "long_window": 40,
            "stop_loss_pct": 0.02,
        }
        
        execution = StrategyExecution(
            strategy_id=test_strategy.id,
            state=ExecutionState.INACTIVE,
            config_overrides=config,
        )
        db_session.add(execution)
        await db_session.flush()
        await db_session.refresh(execution)
        
        assert execution.config_overrides["short_window"] == 15
        assert execution.config_overrides["stop_loss_pct"] == 0.02


class TestStrategySignalModel:
    """Test suite for StrategySignal model."""
    
    @pytest.mark.asyncio
    async def test_create_strategy_signal(
        self, db_session: AsyncSession, test_strategy: Strategy
    ):
        """Test creating a strategy signal."""
        # First create an execution
        execution = StrategyExecution(
            strategy_id=test_strategy.id,
            state=ExecutionState.ACTIVE,
        )
        db_session.add(execution)
        await db_session.flush()
        
        signal = StrategySignal(
            strategy_id=test_strategy.id,
            execution_id=execution.id,
            signal_type=SignalType.BUY,
            symbol="AAPL",
            price_at_signal=150.00,
            indicator_values={
                "sma_short": 148.50,
                "sma_long": 145.00,
                "volume": 50000000,
            },
            reasoning="SMA crossover detected: short MA crossed above long MA",
        )
        db_session.add(signal)
        await db_session.flush()
        
        assert signal.id is not None
        assert signal.signal_type == SignalType.BUY
        assert signal.was_executed is False
    
    @pytest.mark.asyncio
    async def test_strategy_signal_with_strength(
        self, db_session: AsyncSession, test_strategy: Strategy
    ):
        """Test signal with strength indicator."""
        execution = StrategyExecution(
            strategy_id=test_strategy.id,
            state=ExecutionState.ACTIVE,
        )
        db_session.add(execution)
        await db_session.flush()
        
        signal = StrategySignal(
            strategy_id=test_strategy.id,
            execution_id=execution.id,
            signal_type=SignalType.SELL,
            symbol="GOOGL",
            signal_strength=0.95,  # High confidence
            price_at_signal=140.00,
            indicator_values={"rsi": 75.0},
            reasoning="RSI overbought condition",
        )
        db_session.add(signal)
        await db_session.flush()
        
        assert signal.signal_strength == 0.95
    
    @pytest.mark.asyncio
    async def test_strategy_signal_execution(
        self, db_session: AsyncSession, test_strategy: Strategy
    ):
        """Test marking a signal as executed."""
        execution = StrategyExecution(
            strategy_id=test_strategy.id,
            state=ExecutionState.ACTIVE,
        )
        db_session.add(execution)
        await db_session.flush()
        
        signal = StrategySignal(
            strategy_id=test_strategy.id,
            execution_id=execution.id,
            signal_type=SignalType.BUY,
            symbol="MSFT",
            price_at_signal=350.00,
            indicator_values={},
            reasoning="Momentum signal",
        )
        db_session.add(signal)
        await db_session.flush()
        
        # Execute the signal
        signal.was_executed = True
        signal.order_id = "order_12345"
        signal.executed_at = datetime.utcnow()
        
        await db_session.flush()
        await db_session.refresh(signal)
        
        assert signal.was_executed is True
        assert signal.order_id == "order_12345"
        assert signal.executed_at is not None
    
    @pytest.mark.asyncio
    async def test_strategy_signal_execution_failure(
        self, db_session: AsyncSession, test_strategy: Strategy
    ):
        """Test recording a signal execution failure."""
        execution = StrategyExecution(
            strategy_id=test_strategy.id,
            state=ExecutionState.ACTIVE,
        )
        db_session.add(execution)
        await db_session.flush()
        
        signal = StrategySignal(
            strategy_id=test_strategy.id,
            execution_id=execution.id,
            signal_type=SignalType.BUY,
            symbol="NVDA",
            price_at_signal=450.00,
            indicator_values={},
            reasoning="Breakout signal",
            was_executed=False,
            execution_error="Order rejected: Market closed",
        )
        db_session.add(signal)
        await db_session.flush()
        
        assert signal.was_executed is False
        assert "Market closed" in signal.execution_error
    
    @pytest.mark.asyncio
    async def test_hold_signal(
        self, db_session: AsyncSession, test_strategy: Strategy
    ):
        """Test creating a HOLD signal."""
        execution = StrategyExecution(
            strategy_id=test_strategy.id,
            state=ExecutionState.ACTIVE,
        )
        db_session.add(execution)
        await db_session.flush()
        
        signal = StrategySignal(
            strategy_id=test_strategy.id,
            execution_id=execution.id,
            signal_type=SignalType.HOLD,
            symbol="AAPL",
            price_at_signal=150.00,
            indicator_values={"rsi": 55.0},
            reasoning="No clear directional signal",
        )
        db_session.add(signal)
        await db_session.flush()
        
        assert signal.signal_type == SignalType.HOLD


class TestStrategyPerformanceModel:
    """Test suite for StrategyPerformance model."""
    
    @pytest.mark.asyncio
    async def test_create_daily_performance(
        self, db_session: AsyncSession, test_strategy: Strategy
    ):
        """Test creating daily performance record."""
        perf = StrategyPerformance(
            strategy_id=test_strategy.id,
            date=datetime.utcnow(),
            period_type="daily",
            total_trades=5,
            winning_trades=3,
            losing_trades=2,
            total_pnl=250.0,
            gross_profit=500.0,
            gross_loss=-250.0,
            win_rate=60.0,
            profit_factor=2.0,
        )
        db_session.add(perf)
        await db_session.flush()
        
        assert perf.id is not None
        assert perf.period_type == "daily"
        assert perf.win_rate == 60.0
    
    @pytest.mark.asyncio
    async def test_strategy_performance_trade_metrics(
        self, db_session: AsyncSession, test_strategy: Strategy
    ):
        """Test performance record with detailed trade metrics."""
        perf = StrategyPerformance(
            strategy_id=test_strategy.id,
            date=datetime.utcnow(),
            period_type="daily",
            total_trades=10,
            winning_trades=7,
            losing_trades=3,
            total_pnl=1500.0,
            gross_profit=2500.0,
            gross_loss=-1000.0,
            avg_win=357.14,
            avg_loss=-333.33,
            largest_win=800.0,
            largest_loss=-500.0,
        )
        db_session.add(perf)
        await db_session.flush()
        
        assert perf.avg_win == 357.14
        assert perf.largest_win == 800.0
    
    @pytest.mark.asyncio
    async def test_strategy_performance_risk_metrics(
        self, db_session: AsyncSession, test_strategy: Strategy
    ):
        """Test performance record with risk metrics."""
        perf = StrategyPerformance(
            strategy_id=test_strategy.id,
            date=datetime.utcnow(),
            period_type="daily",
            total_trades=5,
            total_pnl=500.0,
            max_drawdown=-200.0,
            sharpe_ratio=1.5,
        )
        db_session.add(perf)
        await db_session.flush()
        
        assert perf.max_drawdown == -200.0
        assert perf.sharpe_ratio == 1.5
    
    @pytest.mark.asyncio
    async def test_strategy_performance_cumulative(
        self, db_session: AsyncSession, test_strategy: Strategy
    ):
        """Test cumulative performance tracking."""
        perf = StrategyPerformance(
            strategy_id=test_strategy.id,
            date=datetime.utcnow(),
            period_type="daily",
            total_trades=5,
            total_pnl=500.0,
            cumulative_pnl=5000.0,  # All-time cumulative
            cumulative_trades=100,  # All-time trades
        )
        db_session.add(perf)
        await db_session.flush()
        
        assert perf.cumulative_pnl == 5000.0
        assert perf.cumulative_trades == 100
    
    @pytest.mark.asyncio
    async def test_strategy_performance_history(
        self, db_session: AsyncSession, test_strategy: Strategy
    ):
        """Test building performance history over multiple days."""
        base_date = datetime(2024, 1, 1)
        
        for i in range(5):
            perf = StrategyPerformance(
                strategy_id=test_strategy.id,
                date=base_date + timedelta(days=i),
                period_type="daily",
                total_trades=i + 1,
                total_pnl=(i + 1) * 100.0,
                cumulative_pnl=sum((j + 1) * 100.0 for j in range(i + 1)),
            )
            db_session.add(perf)
        
        await db_session.flush()
        
        # Query history
        result = await db_session.execute(
            select(StrategyPerformance)
            .where(StrategyPerformance.strategy_id == test_strategy.id)
            .order_by(StrategyPerformance.date)
        )
        history = result.scalars().all()
        
        assert len(history) == 5
        assert history[0].total_pnl == 100.0
        assert history[4].cumulative_pnl == 1500.0  # Sum of 100+200+300+400+500


class TestExecutionStateEnum:
    """Test suite for ExecutionState enum."""
    
    def test_execution_state_values(self):
        """Test ExecutionState enum values."""
        assert ExecutionState.ACTIVE.value == "active"
        assert ExecutionState.INACTIVE.value == "inactive"
        assert ExecutionState.PAUSED.value == "paused"
        assert ExecutionState.ERROR.value == "error"
        assert ExecutionState.CIRCUIT_BREAKER.value == "circuit_breaker"
    
    def test_execution_state_count(self):
        """Test ExecutionState enum has expected count."""
        assert len(list(ExecutionState)) == 5
