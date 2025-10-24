"""
API endpoints for strategy execution control.
Allows users to start, stop, and monitor automated strategy execution.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.strategy import Strategy
from app.models.strategy_execution import (
    StrategyExecution,
    StrategySignal,
    StrategyPerformance,
    ExecutionState,
    SignalType,
)
from app.strategies.executor import StrategyExecutor
from app.strategies.scheduler import get_scheduler

router = APIRouter()


@router.post("/{strategy_id}/start", status_code=status.HTTP_200_OK)
async def start_strategy_execution(
    strategy_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start automated execution for a strategy.
    
    Creates or activates StrategyExecution record for the strategy.
    """
    # Verify strategy exists and belongs to user
    result = await session.execute(
        select(Strategy)
        .where(and_(Strategy.id == strategy_id, Strategy.user_id == current_user.id))
    )
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Check if execution already exists
    result = await session.execute(
        select(StrategyExecution)
        .where(StrategyExecution.strategy_id == strategy_id)
    )
    execution = result.scalar_one_or_none()
    
    if execution:
        # Reactivate existing execution
        if execution.is_active:
            return {
                "success": True,
                "message": "Strategy execution already active",
                "data": {
                    "strategy_id": str(strategy_id),
                    "state": execution.state.value,
                    "is_active": execution.is_active,
                }
            }
        
        execution.is_active = True
        execution.state = ExecutionState.RUNNING
        execution.error_message = None
        execution.error_count = 0
    else:
        # Create new execution
        execution = StrategyExecution(
            strategy_id=strategy_id,
            is_active=True,
            state=ExecutionState.RUNNING,
        )
        session.add(execution)
    
    await session.commit()
    await session.refresh(execution)
    
    # Ensure scheduler is running
    scheduler = get_scheduler()
    if not scheduler.is_running:
        scheduler.start()
    
    return {
        "success": True,
        "message": "Strategy execution started",
        "data": {
            "strategy_id": str(strategy_id),
            "execution_id": str(execution.id),
            "state": execution.state.value,
            "is_active": execution.is_active,
        }
    }


@router.post("/{strategy_id}/stop", status_code=status.HTTP_200_OK)
async def stop_strategy_execution(
    strategy_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Stop automated execution for a strategy.
    
    Deactivates the StrategyExecution record.
    """
    # Verify strategy belongs to user
    result = await session.execute(
        select(Strategy)
        .where(and_(Strategy.id == strategy_id, Strategy.user_id == current_user.id))
    )
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Get execution
    result = await session.execute(
        select(StrategyExecution)
        .where(StrategyExecution.strategy_id == strategy_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution or not execution.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Strategy execution not active"
        )
    
    execution.is_active = False
    execution.state = ExecutionState.STOPPED
    
    await session.commit()
    
    return {
        "success": True,
        "message": "Strategy execution stopped",
        "data": {
            "strategy_id": str(strategy_id),
            "state": execution.state.value,
            "is_active": execution.is_active,
        }
    }


@router.get("/{strategy_id}/status", status_code=status.HTTP_200_OK)
async def get_strategy_execution_status(
    strategy_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get execution status for a strategy.
    
    Returns current state, metrics, and last execution details.
    """
    # Verify strategy belongs to user
    result = await session.execute(
        select(Strategy)
        .where(and_(Strategy.id == strategy_id, Strategy.user_id == current_user.id))
    )
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Get execution
    result = await session.execute(
        select(StrategyExecution)
        .where(StrategyExecution.strategy_id == strategy_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        return {
            "success": True,
            "data": {
                "strategy_id": str(strategy_id),
                "is_active": False,
                "state": "not_started",
                "message": "Execution not started yet"
            }
        }
    
    return {
        "success": True,
        "data": {
            "strategy_id": str(strategy_id),
            "execution_id": str(execution.id),
            "is_active": execution.is_active,
            "state": execution.state.value,
            "current_position": execution.current_position,
            "entry_price": float(execution.entry_price) if execution.entry_price else None,
            "current_pnl": float(execution.current_pnl) if execution.current_pnl else 0.0,
            "total_pnl": float(execution.total_pnl) if execution.total_pnl else 0.0,
            "trades_today": execution.trades_today,
            "total_trades": execution.total_trades,
            "win_rate": float(execution.win_rate) if execution.win_rate else 0.0,
            "last_evaluated_at": execution.last_evaluated_at.isoformat() if execution.last_evaluated_at else None,
            "last_signal_at": execution.last_signal_at.isoformat() if execution.last_signal_at else None,
            "evaluation_count": execution.evaluation_count,
            "error_count": execution.error_count,
            "error_message": execution.error_message,
        }
    }


@router.get("/{strategy_id}/signals", status_code=status.HTTP_200_OK)
async def get_strategy_signals(
    strategy_id: UUID,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get recent signals generated by a strategy.
    
    Returns list of signals with timestamps and reasoning.
    """
    # Verify strategy belongs to user
    result = await session.execute(
        select(Strategy)
        .where(and_(Strategy.id == strategy_id, Strategy.user_id == current_user.id))
    )
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Get execution
    result = await session.execute(
        select(StrategyExecution)
        .where(StrategyExecution.strategy_id == strategy_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        return {
            "success": True,
            "data": {
                "strategy_id": str(strategy_id),
                "signals": [],
                "total": 0
            }
        }
    
    # Get signals
    result = await session.execute(
        select(StrategySignal)
        .where(StrategySignal.execution_id == execution.id)
        .order_by(StrategySignal.timestamp.desc())
        .limit(limit)
    )
    signals = result.scalars().all()
    
    return {
        "success": True,
        "data": {
            "strategy_id": str(strategy_id),
            "signals": [
                {
                    "id": str(signal.id),
                    "signal_type": signal.signal_type.value,
                    "symbol": signal.symbol,
                    "price": float(signal.price),
                    "quantity": float(signal.quantity) if signal.quantity else None,
                    "reasoning": signal.reasoning,
                    "executed": signal.executed,
                    "timestamp": signal.timestamp.isoformat(),
                }
                for signal in signals
            ],
            "total": len(signals)
        }
    }


@router.get("/{strategy_id}/performance", status_code=status.HTTP_200_OK)
async def get_strategy_performance(
    strategy_id: UUID,
    days: int = 30,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get performance metrics for a strategy.
    
    Returns daily and cumulative performance statistics.
    """
    # Verify strategy belongs to user
    result = await session.execute(
        select(Strategy)
        .where(and_(Strategy.id == strategy_id, Strategy.user_id == current_user.id))
    )
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Get execution
    result = await session.execute(
        select(StrategyExecution)
        .where(StrategyExecution.strategy_id == strategy_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        return {
            "success": True,
            "data": {
                "strategy_id": str(strategy_id),
                "performance": {
                    "total_pnl": 0.0,
                    "total_trades": 0,
                    "win_rate": 0.0,
                },
                "daily": []
            }
        }
    
    # Get daily performance records
    result = await session.execute(
        select(StrategyPerformance)
        .where(StrategyPerformance.execution_id == execution.id)
        .order_by(StrategyPerformance.date.desc())
        .limit(days)
    )
    daily_performance = result.scalars().all()
    
    return {
        "success": True,
        "data": {
            "strategy_id": str(strategy_id),
            "performance": {
                "total_pnl": float(execution.total_pnl) if execution.total_pnl else 0.0,
                "total_trades": execution.total_trades,
                "winning_trades": execution.winning_trades,
                "losing_trades": execution.losing_trades,
                "win_rate": float(execution.win_rate) if execution.win_rate else 0.0,
                "current_pnl": float(execution.current_pnl) if execution.current_pnl else 0.0,
            },
            "daily": [
                {
                    "date": perf.date.isoformat(),
                    "pnl": float(perf.pnl),
                    "return_pct": float(perf.return_pct) if perf.return_pct else 0.0,
                    "trades": perf.trades,
                    "winning_trades": perf.winning_trades,
                    "losing_trades": perf.losing_trades,
                }
                for perf in daily_performance
            ]
        }
    }


@router.post("/{strategy_id}/test", status_code=status.HTTP_200_OK)
async def test_strategy_execution(
    strategy_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Test strategy execution without placing real orders (dry run).
    
    Evaluates strategy and returns what signal would be generated.
    """
    # Verify strategy belongs to user
    result = await session.execute(
        select(Strategy)
        .where(and_(Strategy.id == strategy_id, Strategy.user_id == current_user.id))
    )
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Execute strategy in test mode (dry_run=True)
    executor = StrategyExecutor(session)
    
    try:
        result = await executor.execute_strategy(strategy_id, dry_run=True)
        
        return {
            "success": True,
            "message": "Strategy test execution completed (no orders placed)",
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Strategy test failed: {str(e)}"
        )


@router.post("/{strategy_id}/reset", status_code=status.HTTP_200_OK)
async def reset_strategy_execution(
    strategy_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reset strategy execution state.
    
    Clears counters, positions, and performance metrics.
    Useful for restarting after errors or testing.
    """
    # Verify strategy belongs to user
    result = await session.execute(
        select(Strategy)
        .where(and_(Strategy.id == strategy_id, Strategy.user_id == current_user.id))
    )
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Get execution
    result = await session.execute(
        select(StrategyExecution)
        .where(StrategyExecution.strategy_id == strategy_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy execution not found"
        )
    
    # Reset execution state
    execution.state = ExecutionState.IDLE
    execution.is_active = False
    execution.current_position = None
    execution.entry_price = None
    execution.current_pnl = 0.0
    execution.total_pnl = 0.0
    execution.trades_today = 0
    execution.total_trades = 0
    execution.winning_trades = 0
    execution.losing_trades = 0
    execution.win_rate = 0.0
    execution.daily_pnl = 0.0
    execution.daily_loss = 0.0
    execution.error_count = 0
    execution.error_message = None
    execution.evaluation_count = 0
    
    await session.commit()
    
    return {
        "success": True,
        "message": "Strategy execution reset successfully",
        "data": {
            "strategy_id": str(strategy_id),
            "state": execution.state.value,
            "is_active": execution.is_active,
        }
    }


@router.get("/scheduler/status", status_code=status.HTTP_200_OK)
async def get_scheduler_status(
    current_user: User = Depends(get_current_user),
):
    """
    Get status of the background strategy scheduler.
    
    Returns scheduler state and job information.
    """
    scheduler = get_scheduler()
    status_data = scheduler.get_status()
    
    return {
        "success": True,
        "data": status_data
    }
