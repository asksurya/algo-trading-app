"""
Live Trading API endpoints for automated strategy execution.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.database import get_db
from app.models import (
    User, LiveStrategy, SignalHistory, Strategy,
    LiveStrategyStatus, SignalType, Order
)
from app.schemas.live_strategy import (
    LiveStrategyCreate, LiveStrategyUpdate, LiveStrategyResponse,
    SignalHistoryResponse, LiveStrategyStatusResponse,
    DashboardResponse, DashboardSummary, StartStrategyRequest, ControlResponse
)
from app.dependencies import get_current_user
from app.services.strategy_scheduler import StrategyScheduler
from app.integrations.alpaca_client import AlpacaClient
from app.integrations.order_execution import AlpacaOrderExecutor

router = APIRouter(prefix="/live-trading", tags=["Live Trading"])


def get_scheduler(db: Session = Depends(get_db)) -> StrategyScheduler:
    """Get strategy scheduler instance."""
    # In production, this should be a singleton
    alpaca_client = AlpacaClient()
    order_executor = AlpacaOrderExecutor(db)
    return StrategyScheduler(db, alpaca_client, order_executor)


@router.post("/strategies", response_model=LiveStrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_live_strategy(
    strategy_data: LiveStrategyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new live trading strategy configuration.
    
    This creates a strategy that can be started to continuously monitor
    markets and execute trades automatically.
    """
    # Verify strategy exists
    strategy = db.query(Strategy).filter(Strategy.id == strategy_data.strategy_id).first()
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy {strategy_data.strategy_id} not found"
        )
    
    # Create live strategy
    live_strategy = LiveStrategy(
        user_id=current_user.id,
        **strategy_data.dict()
    )
    
    db.add(live_strategy)
    db.commit()
    db.refresh(live_strategy)
    
    return live_strategy


@router.get("/strategies", response_model=List[LiveStrategyResponse])
async def list_live_strategies(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all live trading strategies for the current user.
    
    Can optionally filter by status (ACTIVE, PAUSED, STOPPED, ERROR).
    """
    query = db.query(LiveStrategy).filter(LiveStrategy.user_id == current_user.id)
    
    if status_filter:
        try:
            status_enum = LiveStrategyStatus[status_filter.upper()]
            query = query.filter(LiveStrategy.status == status_enum)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}"
            )
    
    strategies = query.order_by(LiveStrategy.created_at.desc()).all()
    return strategies


@router.get("/strategies/{strategy_id}", response_model=LiveStrategyResponse)
async def get_live_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific live trading strategy."""
    strategy = db.query(LiveStrategy).filter(
        and_(
            LiveStrategy.id == strategy_id,
            LiveStrategy.user_id == current_user.id
        )
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live strategy not found"
        )
    
    return strategy


@router.put("/strategies/{strategy_id}", response_model=LiveStrategyResponse)
async def update_live_strategy(
    strategy_id: str,
    strategy_data: LiveStrategyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a live trading strategy configuration.
    
    Note: Cannot update while strategy is ACTIVE. Stop it first.
    """
    strategy = db.query(LiveStrategy).filter(
        and_(
            LiveStrategy.id == strategy_id,
            LiveStrategy.user_id == current_user.id
        )
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live strategy not found"
        )
    
    if strategy.status == LiveStrategyStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update active strategy. Stop it first."
        )
    
    # Update fields
    update_data = strategy_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(strategy, field, value)
    
    strategy.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(strategy)
    
    return strategy


@router.delete("/strategies/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_live_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a live trading strategy.
    
    Note: Cannot delete while strategy is ACTIVE. Stop it first.
    """
    strategy = db.query(LiveStrategy).filter(
        and_(
            LiveStrategy.id == strategy_id,
            LiveStrategy.user_id == current_user.id
        )
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live strategy not found"
        )
    
    if strategy.status == LiveStrategyStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete active strategy. Stop it first."
        )
    
    db.delete(strategy)
    db.commit()


@router.post("/strategies/{strategy_id}/start", response_model=ControlResponse)
async def start_strategy(
    strategy_id: str,
    request: StartStrategyRequest = StartStrategyRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    scheduler: StrategyScheduler = Depends(get_scheduler)
):
    """
    Start a live trading strategy.
    
    This activates continuous monitoring and automated execution
    based on the strategy configuration.
    """
    strategy = db.query(LiveStrategy).filter(
        and_(
            LiveStrategy.id == strategy_id,
            LiveStrategy.user_id == current_user.id
        )
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live strategy not found"
        )
    
    if strategy.status == LiveStrategyStatus.ACTIVE:
        return ControlResponse(
            success=False,
            message="Strategy is already active",
            strategy_id=strategy_id
        )
    
    # Start the strategy
    success = await scheduler.start_strategy(strategy_id)
    
    if success:
        return ControlResponse(
            success=True,
            message=f"Live trading started for '{strategy.name}'",
            strategy_id=strategy_id
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start strategy"
        )


@router.post("/strategies/{strategy_id}/stop", response_model=ControlResponse)
async def stop_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    scheduler: StrategyScheduler = Depends(get_scheduler)
):
    """
    Stop a live trading strategy.
    
    This stops continuous monitoring and automated execution.
    Any open positions remain open.
    """
    strategy = db.query(LiveStrategy).filter(
        and_(
            LiveStrategy.id == strategy_id,
            LiveStrategy.user_id == current_user.id
        )
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live strategy not found"
        )
    
    if strategy.status == LiveStrategyStatus.STOPPED:
        return ControlResponse(
            success=False,
            message="Strategy is already stopped",
            strategy_id=strategy_id
        )
    
    # Stop the strategy
    success = await scheduler.stop_strategy(strategy_id)
    
    if success:
        return ControlResponse(
            success=True,
            message=f"Live trading stopped for '{strategy.name}'",
            strategy_id=strategy_id
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop strategy"
        )


@router.post("/strategies/{strategy_id}/pause", response_model=ControlResponse)
async def pause_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    scheduler: StrategyScheduler = Depends(get_scheduler)
):
    """
    Pause a live trading strategy.
    
    Similar to stop, but preserves the intention to resume.
    """
    strategy = db.query(LiveStrategy).filter(
        and_(
            LiveStrategy.id == strategy_id,
            LiveStrategy.user_id == current_user.id
        )
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live strategy not found"
        )
    
    success = await scheduler.pause_strategy(strategy_id)
    
    if success:
        return ControlResponse(
            success=True,
            message=f"Strategy '{strategy.name}' paused",
            strategy_id=strategy_id
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pause strategy"
        )


@router.get("/strategies/{strategy_id}/status", response_model=LiveStrategyStatusResponse)
async def get_strategy_status(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    scheduler: StrategyScheduler = Depends(get_scheduler)
):
    """
    Get detailed status of a live trading strategy.
    
    Includes recent signals and execution history.
    """
    strategy = db.query(LiveStrategy).filter(
        and_(
            LiveStrategy.id == strategy_id,
            LiveStrategy.user_id == current_user.id
        )
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live strategy not found"
        )
    
    status_data = scheduler.get_strategy_status(strategy_id)
    
    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get strategy status"
        )
    
    return status_data


@router.get("/signals/recent", response_model=List[SignalHistoryResponse])
async def get_recent_signals(
    limit: int = Query(50, ge=1, le=200),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
    executed_only: bool = Query(False, description="Show only executed signals"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recent trading signals across all live strategies.
    
    Can be filtered by symbol, signal type, and execution status.
    """
    # Get user's live strategies
    strategy_ids = db.query(LiveStrategy.id).filter(
        LiveStrategy.user_id == current_user.id
    ).all()
    strategy_ids = [s[0] for s in strategy_ids]
    
    if not strategy_ids:
        return []
    
    query = db.query(SignalHistory).filter(
        SignalHistory.live_strategy_id.in_(strategy_ids)
    )
    
    if symbol:
        query = query.filter(SignalHistory.symbol == symbol.upper())
    
    if signal_type:
        try:
            signal_enum = SignalType[signal_type.upper()]
            query = query.filter(SignalHistory.signal_type == signal_enum)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid signal type: {signal_type}"
            )
    
    if executed_only:
        query = query.filter(SignalHistory.executed == True)
    
    signals = query.order_by(SignalHistory.timestamp.desc()).limit(limit).all()
    return signals


@router.get("/positions", response_model=List[dict])
async def get_live_positions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current open positions from live trading strategies.
    
    Returns positions created by live trading automation.
    """
    # Get user's live strategies
    strategy_ids = db.query(LiveStrategy.id).filter(
        LiveStrategy.user_id == current_user.id
    ).all()
    strategy_ids = [s[0] for s in strategy_ids]
    
    if not strategy_ids:
        return []
    
    # Get executed buy orders
    positions = db.query(SignalHistory).filter(
        and_(
            SignalHistory.live_strategy_id.in_(strategy_ids),
            SignalHistory.executed == True,
            SignalHistory.signal_type == SignalType.BUY
        )
    ).order_by(SignalHistory.execution_time.desc()).all()
    
    # Format positions
    position_list = []
    for signal in positions:
        live_strategy = db.query(LiveStrategy).filter(
            LiveStrategy.id == signal.live_strategy_id
        ).first()
        
        position_list.append({
            "id": signal.id,
            "symbol": signal.symbol,
            "strategy_name": live_strategy.name if live_strategy else "Unknown",
            "entry_price": signal.execution_price or signal.price,
            "entry_time": signal.execution_time,
            "quantity": 1,  # Placeholder - should track actual quantity
            "current_price": signal.price,  # Should fetch current price
            "pnl": 0.0,  # Should calculate actual P&L
            "pnl_percent": 0.0
        })
    
    return position_list


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get live trading dashboard summary.
    
    Returns overview of all live trading activity including strategies,
    signals, trades, and performance metrics.
    """
    # Get all user's live strategies
    all_strategies = db.query(LiveStrategy).filter(
        LiveStrategy.user_id == current_user.id
    ).all()
    
    active_strategies = [s for s in all_strategies if s.status == LiveStrategyStatus.ACTIVE]
    
    # Get today's date
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    # Get strategy IDs
    strategy_ids = [s.id for s in all_strategies]
    
    # Count today's signals
    signals_today = 0
    trades_today = 0
    
    if strategy_ids:
        signals_today = db.query(func.count(SignalHistory.id)).filter(
            and_(
                SignalHistory.live_strategy_id.in_(strategy_ids),
                SignalHistory.timestamp >= today_start
            )
        ).scalar() or 0
        
        trades_today = db.query(func.count(SignalHistory.id)).filter(
            and_(
                SignalHistory.live_strategy_id.in_(strategy_ids),
                SignalHistory.executed == True,
                SignalHistory.execution_time >= today_start
            )
        ).scalar() or 0
    
    # Calculate P&L
    total_pnl = sum(s.total_pnl for s in all_strategies)
    daily_pnl = sum(s.daily_pnl for s in all_strategies)
    
    # Count active positions
    active_positions = sum(s.current_positions for s in all_strategies)
    
    # Get recent signals
    recent_signals = []
    if strategy_ids:
        recent_signals = db.query(SignalHistory).filter(
            SignalHistory.live_strategy_id.in_(strategy_ids)
        ).order_by(SignalHistory.timestamp.desc()).limit(20).all()
    
    summary = DashboardSummary(
        active_strategies=len(active_strategies),
        total_strategies=len(all_strategies),
        signals_today=signals_today,
        trades_today=trades_today,
        total_pnl=total_pnl,
        daily_pnl=daily_pnl,
        active_positions=active_positions
    )
    
    return DashboardResponse(
        summary=summary,
        active_strategies=active_strategies,
        recent_signals=recent_signals
    )
