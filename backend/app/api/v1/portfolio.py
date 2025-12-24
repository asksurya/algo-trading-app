"""
Portfolio API endpoints for analytics and reporting.
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.portfolio import (
    PortfolioSummaryResponse,
    EquityCurveResponse,
    PerformanceMetricsResponse,
    ReturnsAnalysisResponse
)
from app.services.portfolio_analytics import get_portfolio_analytics_service, PortfolioAnalyticsService

router = APIRouter()


@router.get("/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    current_user: User = Depends(get_current_user),
    analytics_service: PortfolioAnalyticsService = Depends(get_portfolio_analytics_service)
):
    """
    Get current portfolio summary including equity, P&L, and position counts.

    Returns real-time data from the broker.
    """
    summary = await analytics_service.get_portfolio_summary(current_user.id)
    return summary


@router.get("/equity-curve", response_model=EquityCurveResponse)
async def get_equity_curve(
    start_date: Optional[datetime] = Query(None, description="Start date for equity curve"),
    end_date: Optional[datetime] = Query(None, description="End date for equity curve"),
    current_user: User = Depends(get_current_user),
    analytics_service: PortfolioAnalyticsService = Depends(get_portfolio_analytics_service)
):
    """
    Get equity curve data for charting.

    Returns time series of portfolio value over the specified date range.
    """
    equity_curve = await analytics_service.get_equity_curve(
        current_user.id,
        start_date,
        end_date
    )
    return equity_curve


@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    period: str = Query("all_time", description="Time period: daily, weekly, monthly, yearly, all_time"),
    current_user: User = Depends(get_current_user),
    analytics_service: PortfolioAnalyticsService = Depends(get_portfolio_analytics_service)
):
    """
    Get comprehensive performance metrics including:
    - Returns (total, annualized)
    - Risk metrics (volatility, Sharpe ratio, Sortino ratio, Calmar ratio)
    - Drawdown statistics
    - Win/loss statistics
    - Trading activity metrics

    **Period Options:**
    - `daily`: Last 24 hours
    - `weekly`: Last 7 days
    - `monthly`: Last 30 days
    - `yearly`: Last 365 days
    - `all_time`: Since account inception
    """
    metrics = await analytics_service.calculate_performance_metrics(
        current_user.id,
        period
    )
    return metrics


@router.get("/returns", response_model=ReturnsAnalysisResponse)
async def get_returns_analysis(
    current_user: User = Depends(get_current_user),
    analytics_service: PortfolioAnalyticsService = Depends(get_portfolio_analytics_service)
):
    """
    Get detailed returns breakdown including:
    - Daily, weekly, monthly returns
    - Best/worst day and month
    - Win/loss day counts
    - Average daily return
    """
    returns = await analytics_service.get_returns_analysis(current_user.id)
    return returns
