"""
Tests for Portfolio Analytics models (PortfolioSnapshot, PerformanceMetrics, TaxLot).

This module tests:
- PortfolioSnapshot model operations
- PerformanceMetrics calculations
- TaxLot tracking
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    PortfolioSnapshot, PerformanceMetrics, TaxLot,
    User,
)


class TestPortfolioSnapshotModel:
    """Test suite for PortfolioSnapshot model."""
    
    @pytest.mark.asyncio
    async def test_create_portfolio_snapshot(self, db_session: AsyncSession, test_user: User):
        """Test creating a portfolio snapshot."""
        snapshot = PortfolioSnapshot(
            user_id=test_user.id,
            snapshot_date=datetime.utcnow(),
            total_equity=100000.0,
            cash_balance=25000.0,
            positions_value=75000.0,
            daily_pnl=500.0,
            daily_return_pct=0.5,
            total_pnl=5000.0,
            total_return_pct=5.0,
            num_positions=5,
            num_long_positions=4,
            num_short_positions=1,
        )
        db_session.add(snapshot)
        await db_session.flush()
        
        assert snapshot.id is not None
        assert snapshot.total_equity == 100000.0
        assert snapshot.num_positions == 5
    
    @pytest.mark.asyncio
    async def test_portfolio_snapshot_daily_tracking(self, db_session: AsyncSession, test_user: User):
        """Test creating daily portfolio snapshots."""
        base_date = datetime(2024, 1, 1)
        
        for i in range(7):
            snapshot = PortfolioSnapshot(
                user_id=test_user.id,
                snapshot_date=base_date + timedelta(days=i),
                total_equity=100000.0 + i * 500,
                cash_balance=25000.0,
                positions_value=75000.0 + i * 500,
                daily_pnl=500.0 if i > 0 else 0.0,
                daily_return_pct=0.5 if i > 0 else 0.0,
            )
            db_session.add(snapshot)
        
        await db_session.flush()
        
        # Query snapshots
        result = await db_session.execute(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.user_id == test_user.id)
            .order_by(PortfolioSnapshot.snapshot_date)
        )
        snapshots = result.scalars().all()
        
        assert len(snapshots) == 7
        assert snapshots[0].total_equity == 100000.0
        assert snapshots[6].total_equity == 103000.0  # 100000 + 6 * 500
    
    @pytest.mark.asyncio
    async def test_portfolio_snapshot_repr(self, test_portfolio_snapshot: PortfolioSnapshot):
        """Test portfolio snapshot string representation."""
        repr_str = repr(test_portfolio_snapshot)
        assert "PortfolioSnapshot" in repr_str


class TestPerformanceMetricsModel:
    """Test suite for PerformanceMetrics model."""
    
    @pytest.mark.asyncio
    async def test_create_performance_metrics(self, db_session: AsyncSession, test_user: User):
        """Test creating performance metrics."""
        metrics = PerformanceMetrics(
            user_id=test_user.id,
            period="monthly",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            total_return=5000.0,
            total_return_pct=5.0,
            annualized_return=60.0,
            volatility=15.0,
            sharpe_ratio=1.25,
            sortino_ratio=1.85,
            calmar_ratio=2.0,
            max_drawdown=-3000.0,
            max_drawdown_pct=-3.0,
            total_trades=20,
            winning_trades=14,
            losing_trades=6,
            win_rate=70.0,
            avg_win=500.0,
            avg_loss=-300.0,
            profit_factor=2.0,
        )
        db_session.add(metrics)
        await db_session.flush()
        
        assert metrics.id is not None
        assert metrics.sharpe_ratio == 1.25
        assert metrics.win_rate == 70.0
    
    @pytest.mark.asyncio
    async def test_performance_metrics_with_benchmark(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test performance metrics with benchmark comparison."""
        metrics = PerformanceMetrics(
            user_id=test_user.id,
            period="yearly",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            total_return=20000.0,
            total_return_pct=20.0,
            benchmark_return=10000.0,
            benchmark_return_pct=10.0,
            alpha=0.08,  # 8% alpha
            beta=0.85,
        )
        db_session.add(metrics)
        await db_session.flush()
        await db_session.refresh(metrics)
        
        assert metrics.benchmark_return_pct == 10.0
        assert metrics.alpha == 0.08
        assert metrics.beta == 0.85
    
    @pytest.mark.asyncio
    async def test_performance_metrics_multiple_periods(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test performance metrics for multiple periods."""
        periods = ["daily", "weekly", "monthly", "yearly", "all_time"]
        
        for period in periods:
            metrics = PerformanceMetrics(
                user_id=test_user.id,
                period=period,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
                total_return=1000.0,
                total_return_pct=1.0,
            )
            db_session.add(metrics)
        
        await db_session.flush()
        
        result = await db_session.execute(
            select(PerformanceMetrics).where(PerformanceMetrics.user_id == test_user.id)
        )
        all_metrics = result.scalars().all()
        
        assert len(all_metrics) == 5
    
    @pytest.mark.asyncio
    async def test_performance_metrics_with_metadata(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test performance metrics with additional metadata."""
        custom_metrics = {
            "strategy_specific_metric": 42.5,
            "sector_breakdown": {
                "technology": 0.45,
                "healthcare": 0.30,
                "finance": 0.25,
            },
        }
        
        metrics = PerformanceMetrics(
            user_id=test_user.id,
            period="monthly",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            total_return=0.0,
            total_return_pct=0.0,
            metadata_json=custom_metrics,
        )
        db_session.add(metrics)
        await db_session.flush()
        await db_session.refresh(metrics)
        
        assert metrics.metadata_json["strategy_specific_metric"] == 42.5
        assert metrics.metadata_json["sector_breakdown"]["technology"] == 0.45
    
    @pytest.mark.asyncio
    async def test_performance_metrics_repr(self, db_session: AsyncSession, test_user: User):
        """Test performance metrics string representation."""
        metrics = PerformanceMetrics(
            user_id=test_user.id,
            period="monthly",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            total_return=1000.0,
            total_return_pct=1.0,
        )
        db_session.add(metrics)
        await db_session.flush()
        
        repr_str = repr(metrics)
        assert "PerformanceMetrics" in repr_str


class TestTaxLotModel:
    """Test suite for TaxLot model."""
    
    @pytest.mark.asyncio
    async def test_create_tax_lot(self, db_session: AsyncSession, test_user: User):
        """Test creating a tax lot."""
        tax_lot = TaxLot(
            user_id=test_user.id,
            symbol="AAPL",
            quantity=100.0,
            acquisition_date=datetime(2024, 1, 15),
            acquisition_price=150.0,
            total_cost=15000.0,
            status="open",
            remaining_quantity=100.0,
        )
        db_session.add(tax_lot)
        await db_session.flush()
        
        assert tax_lot.id is not None
        assert tax_lot.symbol == "AAPL"
        assert tax_lot.quantity == 100.0
        assert tax_lot.status == "open"
    
    @pytest.mark.asyncio
    async def test_tax_lot_complete_sale(self, db_session: AsyncSession, test_user: User):
        """Test tax lot with complete sale."""
        acquisition_date = datetime(2024, 1, 1)
        disposition_date = datetime(2024, 7, 1)
        
        tax_lot = TaxLot(
            user_id=test_user.id,
            symbol="GOOGL",
            quantity=50.0,
            acquisition_date=acquisition_date,
            acquisition_price=140.0,
            total_cost=7000.0,
            disposition_date=disposition_date,
            disposition_price=160.0,
            total_proceeds=8000.0,
            realized_gain_loss=1000.0,
            holding_period_days=182,
            is_long_term=True,  # Held > 1 year = long term
            status="closed",
            remaining_quantity=0.0,
        )
        db_session.add(tax_lot)
        await db_session.flush()
        await db_session.refresh(tax_lot)
        
        assert tax_lot.disposition_date is not None
        assert tax_lot.realized_gain_loss == 1000.0
        assert tax_lot.is_long_term is True
        assert tax_lot.is_closed is True
    
    @pytest.mark.asyncio
    async def test_tax_lot_partial_sale(self, db_session: AsyncSession, test_user: User):
        """Test tax lot with partial sale."""
        tax_lot = TaxLot(
            user_id=test_user.id,
            symbol="MSFT",
            quantity=100.0,
            acquisition_date=datetime(2024, 1, 1),
            acquisition_price=350.0,
            total_cost=35000.0,
            status="partial",
            remaining_quantity=60.0,  # Sold 40 shares
        )
        db_session.add(tax_lot)
        await db_session.flush()
        await db_session.refresh(tax_lot)
        
        assert tax_lot.status == "partial"
        assert tax_lot.remaining_quantity == 60.0
        assert tax_lot.quantity - tax_lot.remaining_quantity == 40.0
    
    @pytest.mark.asyncio
    async def test_tax_lot_short_term_vs_long_term(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test distinguishing short-term vs long-term tax lots."""
        # Short-term lot (held < 1 year)
        short_term = TaxLot(
            user_id=test_user.id,
            symbol="AAPL",
            quantity=50.0,
            acquisition_date=datetime(2024, 1, 1),
            acquisition_price=150.0,
            total_cost=7500.0,
            disposition_date=datetime(2024, 6, 1),
            disposition_price=160.0,
            total_proceeds=8000.0,
            realized_gain_loss=500.0,
            holding_period_days=152,
            is_long_term=False,
            status="closed",
            remaining_quantity=0.0,
        )
        
        # Long-term lot (held >= 1 year)
        long_term = TaxLot(
            user_id=test_user.id,
            symbol="GOOGL",
            quantity=50.0,
            acquisition_date=datetime(2022, 1, 1),
            acquisition_price=120.0,
            total_cost=6000.0,
            disposition_date=datetime(2024, 1, 15),
            disposition_price=160.0,
            total_proceeds=8000.0,
            realized_gain_loss=2000.0,
            holding_period_days=745,
            is_long_term=True,
            status="closed",
            remaining_quantity=0.0,
        )
        
        db_session.add(short_term)
        db_session.add(long_term)
        await db_session.flush()
        
        assert short_term.is_long_term is False
        assert long_term.is_long_term is True
    
    @pytest.mark.asyncio
    async def test_tax_lot_fifo_tracking(self, db_session: AsyncSession, test_user: User):
        """Test FIFO tax lot tracking with multiple lots."""
        # First purchase
        lot1 = TaxLot(
            user_id=test_user.id,
            symbol="NVDA",
            quantity=50.0,
            acquisition_date=datetime(2024, 1, 1),
            acquisition_price=400.0,
            total_cost=20000.0,
            status="open",
            remaining_quantity=50.0,
        )
        
        # Second purchase (same stock)
        lot2 = TaxLot(
            user_id=test_user.id,
            symbol="NVDA",
            quantity=30.0,
            acquisition_date=datetime(2024, 2, 1),
            acquisition_price=450.0,
            total_cost=13500.0,
            status="open",
            remaining_quantity=30.0,
        )
        
        # Third purchase
        lot3 = TaxLot(
            user_id=test_user.id,
            symbol="NVDA",
            quantity=20.0,
            acquisition_date=datetime(2024, 3, 1),
            acquisition_price=500.0,
            total_cost=10000.0,
            status="open",
            remaining_quantity=20.0,
        )
        
        db_session.add_all([lot1, lot2, lot3])
        await db_session.flush()
        
        # Query lots in FIFO order
        result = await db_session.execute(
            select(TaxLot)
            .where(TaxLot.user_id == test_user.id)
            .where(TaxLot.symbol == "NVDA")
            .order_by(TaxLot.acquisition_date)
        )
        lots = result.scalars().all()
        
        assert len(lots) == 3
        assert lots[0].acquisition_price == 400.0  # First in
        assert lots[2].acquisition_price == 500.0  # Last in
    
    @pytest.mark.asyncio
    async def test_tax_lot_is_closed_property(self, db_session: AsyncSession, test_tax_lot: TaxLot):
        """Test is_closed property."""
        # Open lot
        assert test_tax_lot.is_closed is False
        
        # Close it
        test_tax_lot.status = "closed"
        test_tax_lot.remaining_quantity = 0.0
        await db_session.flush()
        await db_session.refresh(test_tax_lot)
        
        assert test_tax_lot.is_closed is True
    
    @pytest.mark.asyncio
    async def test_tax_lot_repr(self, test_tax_lot: TaxLot):
        """Test tax lot string representation."""
        repr_str = repr(test_tax_lot)
        assert "TaxLot" in repr_str
        assert test_tax_lot.symbol in repr_str
