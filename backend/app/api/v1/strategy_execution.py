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
    # Convert UUID to string for VARCHAR column comparison
    strategy_id_str = str(strategy_id)
    result = await session.execute(
        select(Strategy)
        .where(and_(Strategy.id == strategy_id_str, Strategy.user_id == current_user.id))
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
        .where(StrategyExecution.strategy_id == strategy_id_str)
    )
    execution = result.scalar_one_or_none()

    if execution:
        # Reactivate existing execution
        if execution.state == ExecutionState.ACTIVE:
            return {
                "success": True,
                "message": "Strategy execution already active",
                "data": {
                    "strategy_id": str(strategy_id),
                    "state": execution.state.value,
                    "is_active": execution.state == ExecutionState.ACTIVE,
                }
            }

        execution.state = ExecutionState.ACTIVE
        execution.last_error = None
        execution.error_count = 0
    else:
        # Create new execution
        execution = StrategyExecution(
            strategy_id=strategy_id_str,
            state=ExecutionState.ACTIVE,
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
            "is_active": execution.state == ExecutionState.ACTIVE,
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
    # Convert UUID to string for VARCHAR column comparison
    strategy_id_str = str(strategy_id)

    # Verify strategy belongs to user
    result = await session.execute(
        select(Strategy)
        .where(and_(Strategy.id == strategy_id_str, Strategy.user_id == current_user.id))
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
        .where(StrategyExecution.strategy_id == strategy_id_str)
    )
    execution = result.scalar_one_or_none()
    
    if not execution or execution.state != ExecutionState.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Strategy execution not active"
        )

    execution.state = ExecutionState.PAUSED
    
    await session.commit()
    
    return {
        "success": True,
        "message": "Strategy execution stopped",
        "data": {
            "strategy_id": str(strategy_id),
            "state": execution.state.value,
            "is_active": execution.state == ExecutionState.ACTIVE,
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
    # Convert UUID to string for VARCHAR column comparison
    strategy_id_str = str(strategy_id)

    # Verify strategy belongs to user
    result = await session.execute(
        select(Strategy)
        .where(and_(Strategy.id == strategy_id_str, Strategy.user_id == current_user.id))
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
        .where(StrategyExecution.strategy_id == strategy_id_str)
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
            "is_active": execution.state == ExecutionState.ACTIVE,
            "state": execution.state.value,
            "has_open_position": execution.has_open_position,
            "current_position_qty": float(execution.current_position_qty) if execution.current_position_qty else None,
            "entry_price": float(execution.current_position_entry_price) if execution.current_position_entry_price else None,
            "trades_today": execution.trades_today,
            "loss_today": float(execution.loss_today) if execution.loss_today else 0.0,
            "last_evaluated_at": execution.last_evaluated_at.isoformat() if execution.last_evaluated_at else None,
            "last_signal_at": execution.last_signal_at.isoformat() if execution.last_signal_at else None,
            "last_trade_at": execution.last_trade_at.isoformat() if execution.last_trade_at else None,
            "error_count": execution.error_count,
            "last_error": execution.last_error,
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
    # Convert UUID to string for VARCHAR column comparison
    strategy_id_str = str(strategy_id)

    # Verify strategy belongs to user
    result = await session.execute(
        select(Strategy)
        .where(and_(Strategy.id == strategy_id_str, Strategy.user_id == current_user.id))
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
        .where(StrategyExecution.strategy_id == strategy_id_str)
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
    # Convert UUID to string for VARCHAR column comparison
    strategy_id_str = str(strategy_id)

    # Verify strategy belongs to user
    result = await session.execute(
        select(Strategy)
        .where(and_(Strategy.id == strategy_id_str, Strategy.user_id == current_user.id))
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
        .where(StrategyExecution.strategy_id == strategy_id_str)
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
    
    # Aggregate performance from daily records
    total_pnl = sum(perf.total_pnl for perf in daily_performance)
    total_trades = sum(perf.total_trades for perf in daily_performance)
    winning_trades = sum(perf.winning_trades for perf in daily_performance)
    losing_trades = sum(perf.losing_trades for perf in daily_performance)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

    return {
        "success": True,
        "data": {
            "strategy_id": str(strategy_id),
            "performance": {
                "total_pnl": total_pnl,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": win_rate,
                "trades_today": execution.trades_today,
                "loss_today": float(execution.loss_today) if execution.loss_today else 0.0,
            },
            "daily": [
                {
                    "date": perf.date.isoformat(),
                    "pnl": float(perf.total_pnl),
                    "return_pct": float(perf.win_rate) if perf.win_rate else 0.0,
                    "trades": perf.total_trades,
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
    # Convert UUID to string for VARCHAR column comparison
    strategy_id_str = str(strategy_id)

    # Verify strategy belongs to user
    result = await session.execute(
        select(Strategy)
        .where(and_(Strategy.id == strategy_id_str, Strategy.user_id == current_user.id))
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )

    # Get or create execution record for test mode
    result = await session.execute(
        select(StrategyExecution)
        .where(StrategyExecution.strategy_id == strategy_id_str)
    )
    execution = result.scalar_one_or_none()

    # Create a temporary execution for dry run if none exists
    if not execution:
        execution = StrategyExecution(
            strategy_id=strategy_id_str,
            is_active=False,
            state=ExecutionState.INACTIVE,
        )
        session.add(execution)
        await session.flush()

    # Mark as dry run for this test
    original_dry_run = getattr(execution, 'is_dry_run', False)
    execution.is_dry_run = True

    # Execute strategy in test mode
    executor = StrategyExecutor()

    try:
        exec_result = await executor.execute_strategy(strategy, execution, session)

        # Restore original dry_run state
        execution.is_dry_run = original_dry_run
        await session.commit()

        return {
            "success": True,
            "message": "Strategy test execution completed (no orders placed)",
            "data": exec_result
        }
    except Exception as e:
        # Restore original dry_run state on error
        execution.is_dry_run = original_dry_run
        await session.rollback()
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
    # Convert UUID to string for VARCHAR column comparison
    strategy_id_str = str(strategy_id)

    # Verify strategy belongs to user
    result = await session.execute(
        select(Strategy)
        .where(and_(Strategy.id == strategy_id_str, Strategy.user_id == current_user.id))
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
        .where(StrategyExecution.strategy_id == strategy_id_str)
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy execution not found"
        )

    # Reset execution state
    execution.state = ExecutionState.INACTIVE
    execution.has_open_position = False
    execution.current_position_qty = None
    execution.current_position_entry_price = None
    execution.trades_today = 0
    execution.loss_today = 0.0
    execution.consecutive_losses = 0
    execution.error_count = 0
    execution.last_error = None
    
    await session.commit()
    
    return {
        "success": True,
        "message": "Strategy execution reset successfully",
        "data": {
            "strategy_id": str(strategy_id),
            "state": execution.state.value,
            "is_active": execution.state == ExecutionState.ACTIVE,
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
