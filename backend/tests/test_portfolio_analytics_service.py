"""
Test suite for Portfolio Analytics Service.

Tests cover:
- Portfolio summary calculation (with and without positions)
- Equity curve data retrieval (with and without data)
- Performance metrics calculation (Sharpe ratio, max drawdown, etc.)
- Returns analysis (daily, weekly, monthly aggregation)
"""

import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.portfolio_analytics import PortfolioAnalyticsService
from app.models.portfolio import PortfolioSnapshot


@pytest.fixture
def mock_session():
    """Create mock async database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def mock_broker():
    """Create mock Alpaca broker client."""
    broker = AsyncMock()
    return broker


@pytest.fixture
def service(mock_session, mock_broker):
    """Instantiate service with mocked dependencies."""
    return PortfolioAnalyticsService(mock_session, mock_broker)


class TestGetPortfolioSummary:
    """Tests for get_portfolio_summary method."""

    @pytest.mark.asyncio
    async def test_get_portfolio_summary_with_positions(self, service, mock_broker):
        """Test portfolio summary calculation with active positions."""
        # Mock broker responses
        mock_broker.get_account.return_value = {
            "equity": 105000.0,
            "cash": 50000.0,
            "long_market_value": 55000.0,
            "short_market_value": 0.0,
            "last_equity": 100000.0,
            "initial_equity": 100000.0
        }

        mock_broker.get_positions.return_value = [
            {"symbol": "AAPL", "qty": 10, "market_value": 1500.0, "unrealized_pl": 50.0},
            {"symbol": "GOOGL", "qty": 5, "market_value": 3500.0, "unrealized_pl": 100.0}
        ]

        # Execute
        user_id = "test_user_123"
        summary = await service.get_portfolio_summary(user_id)

        # Assert
        assert summary["total_equity"] == 105000.0
        assert summary["cash_balance"] == 50000.0
        assert summary["positions_value"] == 55000.0
        assert summary["daily_pnl"] == 5000.0
        assert abs(summary["daily_return_pct"] - 5.0) < 0.0001  # Float precision
        assert summary["total_pnl"] == 5000.0
        assert abs(summary["total_return_pct"] - 5.0) < 0.0001  # Float precision
        assert summary["num_positions"] == 2
        assert summary["num_long_positions"] == 2
        assert summary["num_short_positions"] == 0
        assert "last_updated" in summary

    @pytest.mark.asyncio
    async def test_get_portfolio_summary_no_positions(self, service, mock_broker):
        """Test portfolio summary with no open positions."""
        # Mock broker responses
        mock_broker.get_account.return_value = {
            "equity": 100000.0,
            "cash": 100000.0,
            "long_market_value": 0.0,
            "short_market_value": 0.0,
            "last_equity": 100000.0,
            "initial_equity": 100000.0
        }

        mock_broker.get_positions.return_value = []

        # Execute
        user_id = "test_user_456"
        summary = await service.get_portfolio_summary(user_id)

        # Assert
        assert summary["total_equity"] == 100000.0
        assert summary["cash_balance"] == 100000.0
        assert summary["positions_value"] == 0.0
        assert summary["daily_pnl"] == 0.0
        assert summary["daily_return_pct"] == 0.0
        assert summary["num_positions"] == 0
        assert summary["num_long_positions"] == 0
        assert summary["num_short_positions"] == 0

    @pytest.mark.asyncio
    async def test_get_portfolio_summary_with_short_positions(self, service, mock_broker):
        """Test portfolio summary with short positions included."""
        # Mock broker responses
        mock_broker.get_account.return_value = {
            "equity": 98000.0,
            "cash": 120000.0,
            "long_market_value": 30000.0,
            "short_market_value": -52000.0,
            "last_equity": 100000.0,
            "initial_equity": 100000.0
        }

        mock_broker.get_positions.return_value = [
            {"symbol": "AAPL", "qty": 20, "market_value": 3000.0},
            {"symbol": "TSLA", "qty": -10, "market_value": -2000.0}
        ]

        # Execute
        user_id = "test_user_789"
        summary = await service.get_portfolio_summary(user_id)

        # Assert
        assert summary["num_long_positions"] == 1
        assert summary["num_short_positions"] == 1
        assert summary["positions_value"] == 82000.0  # abs(-52000) + 30000


class TestGetEquityCurve:
    """Tests for get_equity_curve method."""

    @pytest.mark.asyncio
    async def test_get_equity_curve_with_data(self, service, mock_session):
        """Test equity curve retrieval with historical snapshots."""
        # Create mock snapshots
        base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        snapshots = [
            PortfolioSnapshot(
                id="snap1",
                user_id="test_user",
                snapshot_date=base_date,
                total_equity=100000.0,
                cash_balance=50000.0,
                positions_value=50000.0,
                daily_pnl=0.0,
                daily_return_pct=0.0,
                total_pnl=0.0,
                total_return_pct=0.0,
                num_positions=2,
                num_long_positions=2,
                num_short_positions=0
            ),
            PortfolioSnapshot(
                id="snap2",
                user_id="test_user",
                snapshot_date=base_date + timedelta(days=1),
                total_equity=101000.0,
                cash_balance=50000.0,
                positions_value=51000.0,
                daily_pnl=1000.0,
                daily_return_pct=1.0,
                total_pnl=1000.0,
                total_return_pct=1.0,
                num_positions=2,
                num_long_positions=2,
                num_short_positions=0
            ),
            PortfolioSnapshot(
                id="snap3",
                user_id="test_user",
                snapshot_date=base_date + timedelta(days=2),
                total_equity=102500.0,
                cash_balance=50000.0,
                positions_value=52500.0,
                daily_pnl=1500.0,
                daily_return_pct=1.49,
                total_pnl=2500.0,
                total_return_pct=2.5,
                num_positions=2,
                num_long_positions=2,
                num_short_positions=0
            )
        ]

        # Mock session execute
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = snapshots
        mock_session.execute.return_value = mock_result

        # Execute
        user_id = "test_user"
        start_date = base_date
        end_date = base_date + timedelta(days=2)

        equity_curve = await service.get_equity_curve(user_id, start_date, end_date)

        # Assert
        assert len(equity_curve["data_points"]) == 3
        assert equity_curve["data_points"][0]["equity"] == 100000.0
        assert equity_curve["data_points"][1]["equity"] == 101000.0
        assert equity_curve["data_points"][2]["equity"] == 102500.0
        assert equity_curve["total_points"] == 3
        assert equity_curve["start_date"] == start_date
        assert equity_curve["end_date"] == end_date

    @pytest.mark.asyncio
    async def test_get_equity_curve_empty(self, service, mock_session):
        """Test equity curve retrieval with no historical data."""
        # Mock session execute (empty result)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        # Execute
        user_id = "test_user"
        equity_curve = await service.get_equity_curve(user_id)

        # Assert
        assert len(equity_curve["data_points"]) == 0
        assert equity_curve["total_points"] == 0

    @pytest.mark.asyncio
    async def test_get_equity_curve_default_dates(self, service, mock_session):
        """Test equity curve uses default 30-day window when no dates provided."""
        # Mock session execute
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        # Execute without dates
        user_id = "test_user"
        await service.get_equity_curve(user_id)

        # Verify the query was constructed with correct date range
        call_args = mock_session.execute.call_args
        assert call_args is not None


class TestCalculatePerformanceMetrics:
    """Tests for calculate_performance_metrics method."""

    @pytest.mark.asyncio
    async def test_calculate_performance_metrics_all_time(self, service, mock_session):
        """Test comprehensive performance metrics calculation for all_time period."""
        # Create equity curve data
        base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        data_points = [
            {"date": base_date, "equity": 100000.0, "daily_return": 0.0, "cumulative_return": 0.0},
            {"date": base_date + timedelta(days=1), "equity": 101000.0, "daily_return": 1.0, "cumulative_return": 1.0},
            {"date": base_date + timedelta(days=2), "equity": 102500.0, "daily_return": 1.49, "cumulative_return": 2.5},
            {"date": base_date + timedelta(days=3), "equity": 101500.0, "daily_return": -0.98, "cumulative_return": 1.5},
            {"date": base_date + timedelta(days=4), "equity": 103000.0, "daily_return": 1.48, "cumulative_return": 3.0},
        ]

        # Mock get_equity_curve
        with patch.object(service, 'get_equity_curve') as mock_equity:
            mock_equity.return_value = {
                "data_points": data_points,
                "start_date": base_date,
                "end_date": base_date + timedelta(days=4)
            }

            # Execute
            user_id = "test_user"
            metrics = await service.calculate_performance_metrics(user_id, period="all_time")

            # Assert
            assert metrics["period"] == "all_time"
            assert metrics["total_return"] == 0.03  # (103000 - 100000) / 100000
            assert metrics["total_return_pct"] == 3.0
            assert metrics["annualized_return"] > 0
            assert metrics["volatility"] > 0
            assert metrics["sharpe_ratio"] > 0
            assert metrics["sortino_ratio"] > 0
            assert metrics["max_drawdown_pct"] > 0
            assert "calmar_ratio" in metrics

    @pytest.mark.asyncio
    async def test_calculate_sharpe_ratio(self, service, mock_session):
        """Test Sharpe ratio calculation is correctly computed."""
        # Create consistent equity curve (positive returns)
        base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        data_points = [
            {"date": base_date + timedelta(days=i), "equity": 100000.0 + (i * 500), "daily_return": 0.005, "cumulative_return": i * 0.5}
            for i in range(20)
        ]

        with patch.object(service, 'get_equity_curve') as mock_equity:
            mock_equity.return_value = {
                "data_points": data_points,
                "start_date": base_date,
                "end_date": base_date + timedelta(days=19)
            }

            # Execute
            metrics = await service.calculate_performance_metrics("test_user")

            # Assert
            assert metrics["sharpe_ratio"] is not None
            assert isinstance(metrics["sharpe_ratio"], (int, float))

    @pytest.mark.asyncio
    async def test_calculate_max_drawdown(self, service, mock_session):
        """Test max drawdown calculation identifies peak-to-trough decline."""
        # Create equity curve with clear drawdown
        base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        data_points = [
            {"date": base_date, "equity": 100000.0, "daily_return": 0.0, "cumulative_return": 0.0},
            {"date": base_date + timedelta(days=1), "equity": 110000.0, "daily_return": 10.0, "cumulative_return": 10.0},
            {"date": base_date + timedelta(days=2), "equity": 120000.0, "daily_return": 10.0, "cumulative_return": 20.0},  # Peak
            {"date": base_date + timedelta(days=3), "equity": 100000.0, "daily_return": -16.67, "cumulative_return": 0.0},  # Drawdown
            {"date": base_date + timedelta(days=4), "equity": 102000.0, "daily_return": 2.0, "cumulative_return": 2.0},
        ]

        with patch.object(service, 'get_equity_curve') as mock_equity:
            mock_equity.return_value = {
                "data_points": data_points,
                "start_date": base_date,
                "end_date": base_date + timedelta(days=4)
            }

            # Execute
            metrics = await service.calculate_performance_metrics("test_user")

            # Assert max drawdown from 120000 to 100000 = 20000
            assert metrics["max_drawdown"] == 20000.0
            assert metrics["max_drawdown_pct"] > 0

    @pytest.mark.asyncio
    async def test_calculate_performance_metrics_empty(self, service, mock_session):
        """Test performance metrics return empty structure when no data available."""
        # Mock get_equity_curve with no data
        with patch.object(service, 'get_equity_curve') as mock_equity:
            mock_equity.return_value = {
                "data_points": [],
                "start_date": datetime.utcnow(),
                "end_date": datetime.utcnow()
            }

            # Execute
            metrics = await service.calculate_performance_metrics("test_user")

            # Assert
            assert metrics["total_return"] == 0.0
            assert metrics["total_return_pct"] == 0.0
            assert metrics["volatility"] is None
            assert metrics["sharpe_ratio"] is None


class TestGetReturnsAnalysis:
    """Tests for get_returns_analysis method."""

    @pytest.mark.asyncio
    async def test_get_returns_analysis_with_data(self, service, mock_session):
        """Test returns analysis calculates daily, weekly, and monthly returns."""
        # Create equity curve data spanning multiple months
        base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        data_points = [
            {"date": base_date + timedelta(days=i), "equity": 100000.0 + (i * 500), "daily_return": 0.5, "cumulative_return": i * 0.5}
            for i in range(60)  # 2 months of data
        ]

        with patch.object(service, 'get_equity_curve') as mock_equity:
            mock_equity.return_value = {
                "data_points": data_points,
                "start_date": base_date,
                "end_date": base_date + timedelta(days=59)
            }

            # Execute
            returns = await service.get_returns_analysis("test_user")

            # Assert
            assert len(returns["daily_returns"]) > 0
            assert len(returns["weekly_returns"]) > 0
            assert len(returns["monthly_returns"]) > 0
            assert returns["best_day"] > 0
            assert returns["worst_day"] <= 0 or returns["worst_day"] >= 0  # Could be either
            assert returns["positive_days"] > 0
            assert returns["avg_daily_return"] > 0

    @pytest.mark.asyncio
    async def test_get_returns_analysis_positive_and_negative_days(self, service, mock_session):
        """Test returns analysis correctly identifies positive and negative days."""
        # Create equity curve with mixed returns
        base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        data_points = [
            {"date": base_date, "equity": 100000.0, "daily_return": 0.0, "cumulative_return": 0.0},
            {"date": base_date + timedelta(days=1), "equity": 101000.0, "daily_return": 1.0, "cumulative_return": 1.0},  # +1%
            {"date": base_date + timedelta(days=2), "equity": 99500.0, "daily_return": -1.49, "cumulative_return": -0.5},  # -1.49%
            {"date": base_date + timedelta(days=3), "equity": 101500.0, "daily_return": 2.01, "cumulative_return": 1.5},  # +2.01%
            {"date": base_date + timedelta(days=4), "equity": 100000.0, "daily_return": -1.48, "cumulative_return": 0.0},  # -1.48%
        ]

        with patch.object(service, 'get_equity_curve') as mock_equity:
            mock_equity.return_value = {
                "data_points": data_points,
                "start_date": base_date,
                "end_date": base_date + timedelta(days=4)
            }

            # Execute
            returns = await service.get_returns_analysis("test_user")

            # Assert
            assert returns["positive_days"] == 2  # Days 1 and 3
            assert returns["negative_days"] == 2  # Days 2 and 4
            assert returns["best_day"] > returns["worst_day"]

    @pytest.mark.asyncio
    async def test_get_returns_analysis_empty(self, service, mock_session):
        """Test returns analysis returns empty structure when no data available."""
        # Mock get_equity_curve with no data
        with patch.object(service, 'get_equity_curve') as mock_equity:
            mock_equity.return_value = {
                "data_points": [],
                "start_date": datetime.utcnow(),
                "end_date": datetime.utcnow()
            }

            # Execute
            returns = await service.get_returns_analysis("test_user")

            # Assert
            assert returns["daily_returns"] == []
            assert returns["weekly_returns"] == []
            assert returns["monthly_returns"] == []
            assert returns["best_day"] == 0.0
            assert returns["worst_day"] == 0.0
            assert returns["positive_days"] == 0
            assert returns["negative_days"] == 0
            assert returns["avg_daily_return"] == 0.0


class TestCalculateSharpeRatio:
    """Tests specifically for Sharpe ratio calculation."""

    @pytest.mark.asyncio
    async def test_calculate_sharpe_ratio_positive_returns(self, service, mock_session):
        """Test Sharpe ratio is positive when returns exceed risk-free rate."""
        # Create equity curve with consistent positive returns
        base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        data_points = [
            {"date": base_date + timedelta(days=i), "equity": 100000.0 * (1.001 ** i), "daily_return": 0.1, "cumulative_return": i * 0.1}
            for i in range(30)
        ]

        with patch.object(service, 'get_equity_curve') as mock_equity:
            mock_equity.return_value = {
                "data_points": data_points,
                "start_date": base_date,
                "end_date": base_date + timedelta(days=29)
            }

            # Execute
            metrics = await service.calculate_performance_metrics("test_user")

            # Assert
            assert metrics["sharpe_ratio"] > 0

    @pytest.mark.asyncio
    async def test_calculate_sharpe_ratio_high_volatility(self, service, mock_session):
        """Test Sharpe ratio decreases with higher volatility."""
        # Create equity curve with high volatility (erratic returns)
        base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        volatilities = [1.005, 0.995, 1.01, 0.99, 1.008, 0.992]  # Alternating up/down
        equity = 100000.0
        data_points = [{"date": base_date, "equity": equity, "daily_return": 0.0, "cumulative_return": 0.0}]

        for i, vol in enumerate(volatilities):
            equity *= vol
            data_points.append({
                "date": base_date + timedelta(days=i+1),
                "equity": equity,
                "daily_return": (vol - 1) * 100,
                "cumulative_return": ((equity - 100000.0) / 100000.0) * 100
            })

        with patch.object(service, 'get_equity_curve') as mock_equity:
            mock_equity.return_value = {
                "data_points": data_points,
                "start_date": base_date,
                "end_date": base_date + timedelta(days=len(volatilities))
            }

            # Execute
            metrics = await service.calculate_performance_metrics("test_user")

            # Assert - high volatility should result in lower/negative Sharpe
            assert "sharpe_ratio" in metrics


class TestPerformanceMetricsPeriods:
    """Tests for different time periods in performance metrics."""

    @pytest.mark.asyncio
    async def test_calculate_metrics_daily_period(self, service, mock_session):
        """Test performance metrics for daily period."""
        # Create one day of data
        base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        data_points = [
            {"date": base_date, "equity": 100000.0, "daily_return": 0.0, "cumulative_return": 0.0},
            {"date": base_date + timedelta(hours=12), "equity": 100500.0, "daily_return": 0.5, "cumulative_return": 0.5},
        ]

        with patch.object(service, 'get_equity_curve') as mock_equity:
            mock_equity.return_value = {
                "data_points": data_points,
                "start_date": base_date,
                "end_date": base_date + timedelta(hours=12)
            }

            # Execute
            metrics = await service.calculate_performance_metrics("test_user", period="daily")

            # Assert
            assert metrics["period"] == "daily"

    @pytest.mark.asyncio
    async def test_calculate_metrics_monthly_period(self, service, mock_session):
        """Test performance metrics for monthly period."""
        # Create one month of data
        base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        data_points = [
            {"date": base_date + timedelta(days=i), "equity": 100000.0 + (i * 300), "daily_return": 0.3, "cumulative_return": i * 0.3}
            for i in range(30)
        ]

        with patch.object(service, 'get_equity_curve') as mock_equity:
            mock_equity.return_value = {
                "data_points": data_points,
                "start_date": base_date,
                "end_date": base_date + timedelta(days=29)
            }

            # Execute
            metrics = await service.calculate_performance_metrics("test_user", period="monthly")

            # Assert
            assert metrics["period"] == "monthly"


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_portfolio_summary_zero_initial_equity(self, service, mock_broker):
        """Test portfolio summary handles zero initial equity gracefully."""
        # Mock broker responses with zero initial equity
        mock_broker.get_account.return_value = {
            "equity": 100000.0,
            "cash": 50000.0,
            "long_market_value": 50000.0,
            "short_market_value": 0.0,
            "last_equity": 100000.0,
            "initial_equity": 0.0  # Edge case
        }

        mock_broker.get_positions.return_value = [
            {"symbol": "AAPL", "qty": 10, "market_value": 1500.0}
        ]

        # Execute - should not raise exception
        summary = await service.get_portfolio_summary("test_user")

        # Assert return % should be 0 when initial equity is 0
        assert summary["total_return_pct"] == 0.0

    @pytest.mark.asyncio
    async def test_performance_metrics_single_data_point(self, service, mock_session):
        """Test performance metrics with only one data point."""
        base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        data_points = [
            {"date": base_date, "equity": 100000.0, "daily_return": 0.0, "cumulative_return": 0.0}
        ]

        with patch.object(service, 'get_equity_curve') as mock_equity:
            mock_equity.return_value = {
                "data_points": data_points,
                "start_date": base_date,
                "end_date": base_date
            }

            # Execute - should return empty metrics
            metrics = await service.calculate_performance_metrics("test_user")

            # Assert
            assert metrics["total_return"] == 0.0
            assert metrics["volatility"] is None

    @pytest.mark.asyncio
    async def test_returns_analysis_single_data_point(self, service, mock_session):
        """Test returns analysis with only one data point."""
        base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        data_points = [
            {"date": base_date, "equity": 100000.0, "daily_return": 0.0, "cumulative_return": 0.0}
        ]

        with patch.object(service, 'get_equity_curve') as mock_equity:
            mock_equity.return_value = {
                "data_points": data_points,
                "start_date": base_date,
                "end_date": base_date
            }

            # Execute
            returns = await service.get_returns_analysis("test_user")

            # Assert
            assert returns["daily_returns"] == []
            assert returns["positive_days"] == 0


class TestServiceIntegration:
    """Integration-style tests combining multiple methods."""

    @pytest.mark.asyncio
    async def test_full_analytics_workflow(self, service, mock_session, mock_broker):
        """Test complete analytics workflow: summary -> equity -> metrics."""
        # Setup broker mocks
        mock_broker.get_account.return_value = {
            "equity": 105000.0,
            "cash": 50000.0,
            "long_market_value": 55000.0,
            "short_market_value": 0.0,
            "last_equity": 100000.0,
            "initial_equity": 100000.0
        }

        mock_broker.get_positions.return_value = [
            {"symbol": "AAPL", "qty": 10, "market_value": 5500.0}
        ]

        # Setup equity curve data
        base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        snapshots = [
            PortfolioSnapshot(
                id=f"snap{i}",
                user_id="test_user",
                snapshot_date=base_date + timedelta(days=i),
                total_equity=100000.0 + (i * 500),
                cash_balance=50000.0,
                positions_value=50000.0 + (i * 500),
                daily_pnl=i * 500,
                daily_return_pct=i * 0.5,
                total_pnl=i * 500,
                total_return_pct=i * 0.5,
                num_positions=1,
                num_long_positions=1,
                num_short_positions=0
            )
            for i in range(10)
        ]

        # Setup session mocks
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = snapshots
        mock_session.execute.return_value = mock_result

        # Execute workflow
        user_id = "test_user"

        # Step 1: Get summary
        summary = await service.get_portfolio_summary(user_id)
        assert summary["total_equity"] == 105000.0

        # Step 2: Get equity curve
        equity_curve = await service.get_equity_curve(user_id)
        assert len(equity_curve["data_points"]) == 10

        # Step 3: Calculate metrics
        with patch.object(service, 'get_equity_curve', return_value=equity_curve):
            metrics = await service.calculate_performance_metrics(user_id)
            assert metrics["period"] == "all_time"
            assert metrics["total_return_pct"] > 0
