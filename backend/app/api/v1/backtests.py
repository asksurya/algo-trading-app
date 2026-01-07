"""
API endpoints for backtest management.
Allows users to create, run, and view backtests.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.backtest import Backtest, BacktestResult, BacktestTrade
from app.models.strategy import Strategy
from app.schemas.backtest import (
    BacktestCreate,
    BacktestResponse,
    BacktestListResponse,
    BacktestDetailResponse,
    BacktestStatusResponse,
    BacktestWithResults,
)
from app.backtesting.runner import BacktestRunner

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_backtest(
    backtest_data: BacktestCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create and queue a new backtest.
    
    The backtest will be created with status='pending' and can be executed
    by calling the run endpoint or automatically by a background worker.
    """
    # Check if strategy exists and belongs to user
    result = await session.execute(
        select(Strategy).where(
            Strategy.id == str(backtest_data.strategy_id),
            Strategy.user_id == current_user.id
        )
    )
    strategy = result.scalar_one_or_none()
    print(f"DEBUG: Found strategy: {strategy}")
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Create backtest
    backtest = Backtest(
        user_id=current_user.id,
        strategy_id=strategy.id,
        name=backtest_data.name,
        description=backtest_data.description,
        start_date=backtest_data.start_date,
        end_date=backtest_data.end_date,
        initial_capital=backtest_data.initial_capital,
        commission=backtest_data.commission,
        slippage=backtest_data.slippage,
        strategy_params=backtest_data.strategy_params,
    )
    
    session.add(backtest)
    await session.commit()
    await session.refresh(backtest)
    
    # Cache ID string before running (to avoid detached instance access later)
    backtest_id_str = str(backtest.id)
    
    # Run backtest asynchronously
    try:
        runner = BacktestRunner(session)
        result = await runner.run_backtest(backtest.id)
        
        return {
            "success": True,
            "message": "Backtest created and executed successfully",
            "data": {
                "id": backtest_id_str,
                "status": result.get("status", "completed"),
                "result": result
            }
        }
    except Exception as e:
        return {
            "success": True,
            "message": "Backtest created but execution failed",
            "data": {
                "id": backtest_id_str,
                "status": "failed",
                "error": str(e)
            }
        }


@router.get("", status_code=status.HTTP_200_OK)
async def list_backtests(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    strategy_id: Optional[UUID] = None,
    status_filter: Optional[str] = None,
):
    """
    List user's backtests with pagination and filtering.
    
    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50, max: 100)
    - strategy_id: Filter by strategy ID
    - status_filter: Filter by status (pending, running, completed, failed, cancelled)
    """
    # Build query
    query = select(Backtest).where(Backtest.user_id == current_user.id)
    
    if strategy_id:
        query = query.where(Backtest.strategy_id == str(strategy_id))
    
    if status_filter:
        query = query.where(Backtest.status == status_filter)
    
    # Count total
    count_query = select(func.count()).select_from(Backtest).where(Backtest.user_id == current_user.id)
    if strategy_id:
        count_query = count_query.where(Backtest.strategy_id == str(strategy_id))
    if status_filter:
        count_query = count_query.where(Backtest.status == status_filter)
    count_result = await session.execute(count_query)
    total = count_result.scalar() or 0
    
    # Get paginated results
    query = query.order_by(desc(Backtest.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await session.execute(query)
    backtests = result.scalars().all()
    
    return BacktestListResponse(
        data=[BacktestResponse.model_validate(bt) for bt in backtests],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{backtest_id}", status_code=status.HTTP_200_OK)
async def get_backtest(
    backtest_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_trades: bool = Query(False, description="Include trade history"),
):
    """
    Get detailed backtest results.
    
    Query Parameters:
    - include_trades: If true, includes full trade history (default: false)
    """
    # Get backtest
    result = await session.execute(
        select(Backtest).where(
            and_(
                Backtest.id == str(backtest_id),
                Backtest.user_id == current_user.id
            )
        )
    )
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found"
        )
    
    # Get results
    result = await session.execute(
        select(BacktestResult).where(BacktestResult.backtest_id == str(backtest_id))
    )
    backtest_result = result.scalar_one_or_none()
    
    # Get trades if requested
    trades = None
    if include_trades:
        result = await session.execute(
            select(BacktestTrade)
            .where(BacktestTrade.backtest_id == str(backtest_id))
            .order_by(BacktestTrade.entry_date)
        )
        trades = result.scalars().all()
    
    # Build response
    backtest_data = BacktestWithResults.model_validate(backtest)
    if backtest_result:
        backtest_data.results = backtest_result
    if trades:
        backtest_data.trades = trades
    
    return BacktestDetailResponse(data=backtest_data)


@router.get("/{backtest_id}/status", status_code=status.HTTP_200_OK)
async def get_backtest_status(
    backtest_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get backtest execution status.
    
    Useful for polling the status of a running backtest.
    """
    result = await session.execute(
        select(Backtest).where(
            and_(
                Backtest.id == str(backtest_id),
                Backtest.user_id == current_user.id
            )
        )
    )
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found"
        )
    
    status_data = {
        "id": str(backtest.id),
        "status": backtest.status.value,
        "progress": backtest.progress,
        "started_at": backtest.started_at.isoformat() if backtest.started_at else None,
        "completed_at": backtest.completed_at.isoformat() if backtest.completed_at else None,
        "duration_seconds": backtest.duration_seconds,
        "error_message": backtest.error_message,
    }
    
    if backtest.started_at and not backtest.completed_at:
        from datetime import datetime, timezone, timezone
        status_data["elapsed_seconds"] = (
            datetime.now(timezone.utc) - backtest.started_at
        ).total_seconds()
    
    return BacktestStatusResponse(data=status_data)


@router.delete("/{backtest_id}", status_code=status.HTTP_200_OK)
async def delete_backtest(
    backtest_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a backtest and all associated data.
    
    This will cascade delete results and trades.
    """
    result = await session.execute(
        select(Backtest).where(
            and_(
                Backtest.id == str(backtest_id),
                Backtest.user_id == current_user.id
            )
        )
    )
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found"
        )
    
    await session.delete(backtest)
    await session.commit()
    
    return {
        "success": True,
        "message": "Backtest deleted successfully"
    }
