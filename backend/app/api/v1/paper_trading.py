"""
Paper Trading API endpoints for simulated trading operations.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.paper_trading import (
    PaperAccountResponse,
    PaperOrderRequest,
    PaperOrderResponse,
    PaperPositionResponse,
    PaperTradeResponse,
    PaperAccountResetRequest,
)
from app.services.paper_trading import PaperTradingService

router = APIRouter()


async def get_paper_trading_service(
    db: AsyncSession = Depends(get_db),
) -> PaperTradingService:
    """Dependency to get paper trading service instance."""
    return PaperTradingService(db)


@router.get("/account", response_model=PaperAccountResponse)
async def get_paper_account(
    service: PaperTradingService = Depends(get_paper_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get paper trading account information.

    Returns the current paper trading account including:
    - Cash balance and total equity
    - All positions with current market values
    - Trade history
    - Overall P&L metrics
    """
    account = await service.get_paper_account(str(current_user.id))
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper trading account not found"
        )
    return account


@router.post("/orders", response_model=PaperOrderResponse)
async def place_paper_order(
    order: PaperOrderRequest,
    service: PaperTradingService = Depends(get_paper_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Place a paper trading order.

    Executes a simulated buy or sell order against the paper trading account.
    For market orders, uses current market price.
    For limit orders, uses the specified limit price.

    Returns the executed trade details and updated account state.
    """
    result = await service.execute_paper_order(
        user_id=str(current_user.id),
        symbol=order.symbol.upper(),
        qty=order.qty,
        side=order.side.value,
        order_type=order.order_type.value,
        limit_price=order.limit_price,
    )
    return result


@router.get("/orders", response_model=List[PaperTradeResponse])
async def get_paper_orders(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of orders to return"),
    service: PaperTradingService = Depends(get_paper_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get paper trading order/trade history.

    Returns a list of all executed paper trades, ordered by timestamp.
    """
    trades = await service.get_paper_trade_history(
        user_id=str(current_user.id),
        limit=limit,
    )
    return trades


@router.get("/positions", response_model=List[PaperPositionResponse])
async def get_paper_positions(
    service: PaperTradingService = Depends(get_paper_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get all paper trading positions.

    Returns a list of all current positions with:
    - Symbol and quantity
    - Average cost and current price
    - Market value and unrealized P&L
    """
    positions = await service.get_paper_positions(str(current_user.id))
    return positions


@router.get("/trades", response_model=List[PaperTradeResponse])
async def get_paper_trades(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of trades to return"),
    service: PaperTradingService = Depends(get_paper_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get paper trading trade history.

    Returns a list of all executed paper trades, ordered by timestamp.
    """
    trades = await service.get_paper_trade_history(
        user_id=str(current_user.id),
        limit=limit,
    )
    return trades


@router.post("/reset", response_model=PaperAccountResponse)
async def reset_paper_account(
    reset_request: PaperAccountResetRequest = PaperAccountResetRequest(),
    service: PaperTradingService = Depends(get_paper_trading_service),
    current_user: User = Depends(get_current_user),
):
    """
    Reset paper trading account to initial state.

    Clears all positions and trades, resets cash balance to specified amount.
    This action cannot be undone.
    """
    account = await service.reset_paper_account(
        user_id=str(current_user.id),
        starting_balance=reset_request.starting_balance,
    )
    return account
