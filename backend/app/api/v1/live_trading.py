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
)
from app.services.live_trading_service import LiveTradingService, get_live_trading_service

router = APIRouter()


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
