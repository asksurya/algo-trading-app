"""
Trades API routes.
Handles trade execution, positions, and trading statistics.
"""
from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.user import User
from app.models.trade import Trade, Position, TradeStatus
from app.schemas.trade import (
    TradeCreate,
    TradeResponse,
    PositionResponse,
    TradingStatistics,
    PortfolioSummary,
)
from app.dependencies import get_current_active_user
from app.integrations.market_data import get_market_data_client
import asyncio
from datetime import datetime, timezone


router = APIRouter()


@router.get("", response_model=List[TradeResponse])
async def list_trades(
    skip: int = 0,
    limit: int = 100,
    ticker: str = None,
    status_filter: TradeStatus = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all trades for current user.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **ticker**: Filter by ticker symbol (optional)
    - **status_filter**: Filter by trade status (optional)
    """
    query = select(Trade).where(Trade.user_id == current_user.id)
    
    if ticker:
        query = query.where(Trade.ticker == ticker.upper())
    
    if status_filter:
        query = query.where(Trade.status == status_filter)
    
    query = query.offset(skip).limit(limit).order_by(Trade.created_at.desc())
    
    result = await db.execute(query)
    trades = result.scalars().all()
    
    return trades


@router.post("", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
async def create_trade(
    trade_data: TradeCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new trade.
    
    - **ticker**: Stock ticker symbol
    - **trade_type**: BUY or SELL
    - **quantity**: Number of shares
    - **price**: Limit price (optional, market order if not provided)
    - **strategy_id**: Associated strategy ID (optional)
    """
    # Create trade
    new_trade = Trade(
        user_id=current_user.id,
        strategy_id=trade_data.strategy_id,
        ticker=trade_data.ticker.upper(),
        trade_type=trade_data.trade_type,
        quantity=trade_data.quantity,
        price=trade_data.price,
        status=TradeStatus.PENDING,
    )
    
    db.add(new_trade)
    await db.commit()
    await db.refresh(new_trade)
    
    # TODO: In production, this would:
    # 1. Send order to Alpaca API
    # 2. Update order_id with broker's order ID
    # 3. Use background task/webhook to update status
    
    return new_trade


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific trade by ID.
    """
    result = await db.execute(
        select(Trade).where(
            Trade.id == trade_id,
            Trade.user_id == current_user.id
        )
    )
    trade = result.scalar_one_or_none()
    
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    
    return trade


@router.get("/positions/current", response_model=List[PositionResponse])
async def list_current_positions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all current open positions.
    """
    result = await db.execute(
        select(Position).where(
            Position.user_id == current_user.id,
            Position.closed_at.is_(None)
        )
    )
    positions = result.scalars().all()
    
    return positions


@router.get("/positions/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific position by ID.
    """
    result = await db.execute(
        select(Position).where(
            Position.id == position_id,
            Position.user_id == current_user.id
        )
    )
    position = result.scalar_one_or_none()
    
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found"
        )
    
    return position


@router.get("/statistics/summary", response_model=TradingStatistics)
async def get_trading_statistics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get trading statistics for current user.
    
    Returns win rate, total P&L, average win/loss, etc.
    """
    # Get all filled trades
    result = await db.execute(
        select(Trade).where(
            Trade.user_id == current_user.id,
            Trade.status == TradeStatus.FILLED,
            Trade.realized_pnl.isnot(None)
        )
    )
    trades = result.scalars().all()
    
    if not trades:
        return TradingStatistics(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            total_pnl=Decimal("0"),
        )
    
    # Calculate statistics
    winning_trades = [t for t in trades if t.realized_pnl > 0]
    losing_trades = [t for t in trades if t.realized_pnl < 0]
    
    total_pnl = sum(t.realized_pnl for t in trades if t.realized_pnl)
    
    avg_win = (
        sum(t.realized_pnl for t in winning_trades) / len(winning_trades)
        if winning_trades else None
    )
    
    avg_loss = (
        sum(t.realized_pnl for t in losing_trades) / len(losing_trades)
        if losing_trades else None
    )
    
    largest_win = max((t.realized_pnl for t in winning_trades), default=None)
    largest_loss = min((t.realized_pnl for t in losing_trades), default=None)
    
    win_rate = (
        len(winning_trades) / len(trades) * 100
        if trades else 0.0
    )
    
    return TradingStatistics(
        total_trades=len(trades),
        winning_trades=len(winning_trades),
        losing_trades=len(losing_trades),
        win_rate=win_rate,
        total_pnl=total_pnl,
        avg_win=avg_win,
        avg_loss=avg_loss,
        largest_win=largest_win,
        largest_loss=largest_loss,
    )


@router.get("/portfolio/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get portfolio summary for current user.
    
    Returns total value, cash balance, positions value, P&L, etc.
    """
    # Get all open positions
    result = await db.execute(
        select(Position).where(
            Position.user_id == current_user.id,
            Position.closed_at.is_(None)
        )
    )
    positions = result.scalars().all()
    
    # Calculate position values
    positions_value = Decimal("0")
    total_unrealized_pnl = Decimal("0")
    
    for position in positions:
        if position.current_price and position.quantity:
            position_value = position.current_price * position.quantity
            positions_value += position_value
            
            if position.unrealized_pnl:
                total_unrealized_pnl += position.unrealized_pnl
    
    # Get realized P&L from all trades
    result = await db.execute(
        select(func.sum(Trade.realized_pnl)).where(
            Trade.user_id == current_user.id,
            Trade.realized_pnl.isnot(None)
        )
    )
    total_realized_pnl = result.scalar() or Decimal("0")
    
    # TODO: Get actual cash balance from broker API
    # For now, use a placeholder
    cash_balance = Decimal("100000.00")
    
    total_value = cash_balance + positions_value
    total_pnl = total_realized_pnl + total_unrealized_pnl
    
    # Calculate day P&L
    day_pnl = Decimal("0")
    
    try:
        # 1. Get Realized P&L from trades executed today
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        result = await db.execute(
            select(func.sum(Trade.realized_pnl)).where(
                Trade.user_id == current_user.id,
                Trade.realized_pnl.isnot(None),
                Trade.executed_at >= today_start
            )
        )
        day_realized_pnl = result.scalar() or Decimal("0")

        # 2. Get Unrealized P&L change for OPEN positions
        day_unrealized_pnl_change = Decimal("0")

        if positions:
            market_data = get_market_data_client()

            # Fetch snapshots for all open positions concurrently
            tasks = [market_data.get_snapshot(p.ticker) for p in positions]
            snapshots = await asyncio.gather(*tasks, return_exceptions=True)

            for position, snapshot in zip(positions, snapshots):
                if isinstance(snapshot, Exception) or not snapshot:
                    continue

                prev_close = Decimal(str(snapshot['prev_daily_bar']['close']))
                current_price = Decimal(str(snapshot['daily_bar']['close']))

                # If opened today, reference is entry price. Otherwise previous close.
                # Note: This is a simplification. Ideally check tax lots.
                if position.opened_at >= today_start:
                    reference_price = position.avg_entry_price
                else:
                    reference_price = prev_close

                pnl_change = (current_price - reference_price) * position.quantity
                day_unrealized_pnl_change += pnl_change

        day_pnl = day_realized_pnl + day_unrealized_pnl_change

    except Exception as e:
        # Log error but don't fail the request
        print(f"Error calculating Day P&L: {e}")
        day_pnl = Decimal("0")

    # Count active strategies
    from app.models.strategy import Strategy
    result = await db.execute(
        select(func.count(Strategy.id)).where(
            Strategy.user_id == current_user.id,
            Strategy.is_active == True
        )
    )
    active_strategies = result.scalar() or 0
    
    return PortfolioSummary(
        total_value=total_value,
        cash_balance=cash_balance,
        positions_value=positions_value,
        total_pnl=total_pnl,
        day_pnl=day_pnl,
        positions_count=len(positions),
        active_strategies=active_strategies,
    )
