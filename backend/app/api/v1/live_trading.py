"""
Live Trading API endpoints for real-time trading operations.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.strategy import Strategy
from app.schemas.order import OrderResponse
from app.schemas.live_trading import (
    LiveTradingStatusResponse,
    LiveTradingPortfolioResponse,
    LiveTradingActionRequest,
    LiveStrategyCreate,
    LiveStrategyUpdate,
    LiveStrategyResponse,
    LivePositionResponse,
    QuickDeployRequest,
    QuickDeployResponse,
)
from app.services.live_trading_service import LiveTradingService, get_live_trading_service

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(
    live_trading_service: LiveTradingService = Depends(get_live_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive live trading dashboard data.

    Returns summary statistics, active strategies, and recent signals.
    """
    # Get all strategies
    strategies = await live_trading_service.get_live_strategies(current_user.id)

    # Calculate summary stats
    active_strategies = [s for s in strategies if s.status == 'active']
    total_strategies = len(strategies)

    # TODO: Implement actual signal and trade tracking
    # For now return mock data
    summary = {
        "active_strategies": len(active_strategies),
        "total_strategies": total_strategies,
        "signals_today": 0,
        "trades_today": 0,
        "daily_pnl": 0.0,
        "total_pnl": sum(s.total_pnl for s in strategies)
    }

    return {
        "summary": summary,
        "active_strategies": strategies,  # Return all strategies for now
        "recent_signals": []  # TODO: Implement signal history tracking
    }


@router.get("/status", response_model=LiveTradingStatusResponse)
async def get_live_trading_status(
    live_trading_service: LiveTradingService = Depends(get_live_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get the overall status of the live trading system.
    """
    status_data = await live_trading_service.get_system_status(current_user.id)
    return status_data


@router.get("/portfolio", response_model=LiveTradingPortfolioResponse)
async def get_live_trading_portfolio(
    live_trading_service: LiveTradingService = Depends(get_live_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get the current live trading portfolio.
    """
    portfolio_data = await live_trading_service.get_portfolio(current_user.id)
    return portfolio_data


@router.post("/action", status_code=status.HTTP_200_OK)
async def perform_live_trading_action(
    action_request: LiveTradingActionRequest,
    live_trading_service: LiveTradingService = Depends(get_live_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Perform a live trading action (e.g., pause, resume).
    """
    result = await live_trading_service.perform_action(current_user.id, action_request.action)
    return result


@router.get("/strategies/active", response_model=List[UUID])
async def get_active_strategies(
    live_trading_service: LiveTradingService = Depends(get_live_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get a list of currently active strategies in live trading.
    """
    active_strategies = await live_trading_service.get_active_strategies(current_user.id)
    return active_strategies


@router.get("/orders", response_model=List[OrderResponse])
async def get_live_orders(
    live_trading_service: LiveTradingService = Depends(get_live_trading_service),
    current_user: User = Depends(get_current_user),
    limit: int = 100,
):
    """
    Get a list of recent live trading orders.
    """
    orders = await live_trading_service.get_orders(current_user.id, limit=limit)
    return orders


# ============================================================================
# Live Strategy CRUD Endpoints
# ============================================================================

@router.post("/strategies", response_model=LiveStrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_live_strategy(
    strategy_data: LiveStrategyCreate,
    live_trading_service: LiveTradingService = Depends(get_live_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new live trading strategy.

    Creates a strategy in STOPPED status. Use the start endpoint to begin execution.
    """
    strategy = await live_trading_service.create_live_strategy(
        user_id=current_user.id,
        strategy_data=strategy_data
    )
    return strategy


@router.post("/quick-deploy", response_model=QuickDeployResponse, status_code=status.HTTP_201_CREATED)
async def quick_deploy_strategy(
    request: QuickDeployRequest,
    live_trading_service: LiveTradingService = Depends(get_live_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Quick deploy a strategy to live trading.

    Creates a live strategy with sensible defaults and immediately activates it.
    The strategy will begin monitoring markets and executing trades.
    """
    live_strategy = await live_trading_service.quick_deploy(
        user_id=current_user.id,
        request=request
    )

    return QuickDeployResponse(
        success=True,
        live_strategy_id=live_strategy.id,
        name=live_strategy.name,
        status=live_strategy.status.value,
        message=f"Strategy deployed successfully. Now monitoring {len(request.symbols)} symbols."
    )


@router.get("/strategies", response_model=List[LiveStrategyResponse])
async def get_live_strategies(
    live_trading_service: LiveTradingService = Depends(get_live_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get all live trading strategies for the current user.
    """
    strategies = await live_trading_service.get_live_strategies(current_user.id)
    return strategies


@router.get("/strategies/{strategy_id}", response_model=LiveStrategyResponse)
async def get_live_strategy(
    strategy_id: str,
    live_trading_service: LiveTradingService = Depends(get_live_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific live trading strategy by ID.
    """
    strategy = await live_trading_service.get_live_strategy(strategy_id, current_user.id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Live strategy {strategy_id} not found"
        )
    return strategy


@router.put("/strategies/{strategy_id}", response_model=LiveStrategyResponse)
async def update_live_strategy(
    strategy_id: str,
    strategy_data: LiveStrategyUpdate,
    live_trading_service: LiveTradingService = Depends(get_live_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing live trading strategy.

    Note: Cannot update a strategy while it's ACTIVE. Stop or pause it first.
    """
    strategy = await live_trading_service.update_live_strategy(
        strategy_id=strategy_id,
        user_id=current_user.id,
        strategy_data=strategy_data
    )
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Live strategy {strategy_id} not found"
        )
    return strategy


@router.delete("/strategies/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_live_strategy(
    strategy_id: str,
    live_trading_service: LiveTradingService = Depends(get_live_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a live trading strategy.

    Note: Cannot delete an ACTIVE strategy. Stop it first.
    """
    deleted = await live_trading_service.delete_live_strategy(strategy_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Live strategy {strategy_id} not found"
        )
    return None


# ============================================================================
# Live Strategy Lifecycle Endpoints
# ============================================================================

@router.post("/strategies/{strategy_id}/start", response_model=LiveStrategyResponse)
async def start_live_strategy(
    strategy_id: str,
    live_trading_service: LiveTradingService = Depends(get_live_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Start a live trading strategy.

    Transitions the strategy from STOPPED or PAUSED to ACTIVE status.
    The strategy will begin monitoring markets and executing trades.
    """
    strategy = await live_trading_service.start_strategy(strategy_id, current_user.id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Live strategy {strategy_id} not found"
        )
    return strategy


@router.post("/strategies/{strategy_id}/stop", response_model=LiveStrategyResponse)
async def stop_live_strategy(
    strategy_id: str,
    live_trading_service: LiveTradingService = Depends(get_live_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Stop a live trading strategy.

    Transitions the strategy to STOPPED status.
    All monitoring and execution will halt.
    """
    strategy = await live_trading_service.stop_strategy(strategy_id, current_user.id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Live strategy {strategy_id} not found"
        )
    return strategy


@router.post("/strategies/{strategy_id}/pause", response_model=LiveStrategyResponse)
async def pause_live_strategy(
    strategy_id: str,
    live_trading_service: LiveTradingService = Depends(get_live_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Pause a live trading strategy.

    Transitions the strategy to PAUSED status.
    Monitoring continues but no new trades will be executed.
    """
    strategy = await live_trading_service.pause_strategy(strategy_id, current_user.id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Live strategy {strategy_id} not found"
        )
    return strategy


@router.get("/strategies/{strategy_id}/positions", response_model=List[LivePositionResponse])
async def get_strategy_positions(
    strategy_id: str,
    live_trading_service: LiveTradingService = Depends(get_live_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get current positions for a live trading strategy.

    Returns all open positions associated with this strategy.
    """
    # First verify the strategy exists and belongs to the user
    strategy = await live_trading_service.get_live_strategy(strategy_id, current_user.id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Live strategy {strategy_id} not found"
        )

    # For now, return empty list - positions tracking will be implemented later
    # TODO: Implement position tracking for live strategies
    return []
