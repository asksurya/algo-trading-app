"""
API endpoints for strategy optimizer.
Handles multi-ticker analysis and automated trading execution.
"""
from typing import Dict, Any
from uuid import uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.strategy_optimizer import StrategyOptimizer
from app.services.risk_manager import RiskManager
from app.services.notification_service import NotificationService
from app.integrations.order_execution import AlpacaOrderExecutor
from app.integrations.alpaca_client import get_alpaca_client
from app.schemas.optimizer import (
    OptimizeStrategyRequest,
    OptimizeStrategyResponse,
    ExecuteOptimalRequest,
    ExecuteOptimalResponse,
    OptimizationJobStatus,
    OptimizationHistory,
    StrategyPerformanceSchema,
    OptimizationResultSchema
)

router = APIRouter(prefix="/optimizer", tags=["optimizer"])

# In-memory job storage (in production, use Redis or database)
_optimization_jobs: Dict[str, Dict[str, Any]] = {}


async def get_optimizer_service(
    db: AsyncSession = Depends(get_db)
) -> StrategyOptimizer:
    """Get strategy optimizer service instance."""
    alpaca = get_alpaca_client()
    risk_manager = RiskManager(db, alpaca)
    notification_service = NotificationService(db)
    order_execution = AlpacaOrderExecutor()
    order_execution.set_db_session(db)
    
    return StrategyOptimizer(
        db=db,
        alpaca_client=alpaca,
        risk_manager=risk_manager,
        notification_service=notification_service,
        order_execution=order_execution
    )


async def run_optimization_job(
    job_id: str,
    user_id: int,
    request: OptimizeStrategyRequest,
    db: AsyncSession
):
    """Background task to run optimization."""
    try:
        # Update job status
        _optimization_jobs[job_id]["status"] = "running"
        _optimization_jobs[job_id]["current_step"] = "Initializing"
        
        # Get optimizer service
        alpaca = get_alpaca_client()
        risk_manager = RiskManager(db, alpaca)
        notification_service = NotificationService(db)
        order_execution = AlpacaOrderExecutor()
        order_execution.set_db_session(db)
        
        optimizer = StrategyOptimizer(
            db=db,
            alpaca_client=alpaca,
            risk_manager=risk_manager,
            notification_service=notification_service,
            order_execution=order_execution
        )
        
        # Run optimization
        _optimization_jobs[job_id]["current_step"] = "Running backtests"
        results = await optimizer.optimize_strategies(
            user_id=user_id,
            symbols=request.symbols,
            strategy_ids=request.strategy_ids,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital
        )
        
        # Convert results to schemas
        result_schemas = {}
        for symbol, opt_result in results.items():
            performances = [
                StrategyPerformanceSchema(
                    strategy_id=p.strategy_id,
                    strategy_name=p.strategy_name,
                    symbol=p.symbol,
                    backtest_id=p.backtest_id,
                    total_return=p.total_return,
                    sharpe_ratio=p.sharpe_ratio,
                    max_drawdown=p.max_drawdown,
                    win_rate=p.win_rate,
                    total_trades=p.total_trades,
                    net_profit=p.net_profit,
                    composite_score=p.composite_score,
                    rank=p.rank
                )
                for p in opt_result.all_performances
            ]
            
            result_schemas[symbol] = OptimizationResultSchema(
                symbol=opt_result.symbol,
                best_strategy=performances[0] if performances else None,
                all_performances=performances,
                analysis_date=opt_result.analysis_date
            )
        
        # Update job with results
        _optimization_jobs[job_id]["status"] = "completed"
        _optimization_jobs[job_id]["results"] = result_schemas
        _optimization_jobs[job_id]["completed_at"] = datetime.now(datetime.UTC)
        _optimization_jobs[job_id]["progress"] = 100.0
        _optimization_jobs[job_id]["results_available"] = True
        _optimization_jobs[job_id]["current_step"] = "Complete"
        
        # Send notification
        await notification_service.create_notification(
            user_id=user_id,
            title="Strategy Optimization Complete",
            message=f"Analyzed {len(request.symbols)} symbols across all strategies",
            notification_type="SYSTEM",
            priority="medium",
            metadata={"job_id": job_id}
        )
        
    except Exception as e:
        _optimization_jobs[job_id]["status"] = "failed"
        _optimization_jobs[job_id]["error_message"] = str(e)
        _optimization_jobs[job_id]["completed_at"] = datetime.now(datetime.UTC)
        
        # Send error notification
        notification_service = NotificationService(db)
        await notification_service.create_notification(
            user_id=user_id,
            title="Strategy Optimization Failed",
            message=f"Error: {str(e)}",
            notification_type="SYSTEM",
            priority="high",
            metadata={"job_id": job_id}
        )


@router.post("/analyze", response_model=OptimizeStrategyResponse)
async def analyze_strategies(
    request: OptimizeStrategyRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze multiple strategies across multiple symbols.
    Runs backtests in the background and returns a job ID for tracking.
    """
    # Validate symbols
    if not request.symbols:
        raise HTTPException(status_code=400, detail="At least one symbol required")
    
    # Basic validation
    date_range = request.end_date - request.start_date
    if date_range.days < 1:
        raise HTTPException(
            status_code=400,
            detail="End date must be after start date"
        )
    
    # Log large requests for monitoring
    if date_range.days > 365:
        logger.info(
            f"Large date range request: {date_range.days} days for "
            f"{len(request.symbols)} symbols (user {current_user.id})"
        )
    
    # Create job
    job_id = str(uuid4())
    total_backtests = len(request.symbols) * (
        len(request.strategy_ids) if request.strategy_ids else 10  # Estimate
    )
    
    _optimization_jobs[job_id] = {
        "job_id": job_id,
        "user_id": current_user.id,
        "status": "pending",
        "progress": 0.0,
        "current_step": "Pending",
        "started_at": datetime.now(datetime.UTC),
        "completed_at": None,
        "error_message": None,
        "results_available": False,
        "results": {},
        "total_symbols": len(request.symbols),
        "total_strategies": len(request.strategy_ids) if request.strategy_ids else 0,
        "total_backtests": total_backtests
    }
    
    # Start background task
    background_tasks.add_task(
        run_optimization_job,
        job_id,
        current_user.id,
        request,
        db
    )
    
    return OptimizeStrategyResponse(
        job_id=job_id,
        status="pending",
        results={},
        total_symbols=len(request.symbols),
        total_strategies=len(request.strategy_ids) if request.strategy_ids else 0,
        total_backtests=total_backtests,
        started_at=datetime.now(datetime.UTC)
    )


@router.get("/results/{job_id}", response_model=OptimizeStrategyResponse)
async def get_optimization_results(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get results of an optimization job.
    """
    if job_id not in _optimization_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = _optimization_jobs[job_id]
    
    # Check ownership
    if job["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return OptimizeStrategyResponse(
        job_id=job["job_id"],
        status=job["status"],
        results=job.get("results", {}),
        total_symbols=job["total_symbols"],
        total_strategies=job["total_strategies"],
        total_backtests=job["total_backtests"],
        started_at=job["started_at"],
        completed_at=job.get("completed_at"),
        error_message=job.get("error_message")
    )


@router.get("/status/{job_id}", response_model=OptimizationJobStatus)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get status of an optimization job.
    """
    if job_id not in _optimization_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = _optimization_jobs[job_id]
    
    # Check ownership
    if job["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return OptimizationJobStatus(
        job_id=job["job_id"],
        status=job["status"],
        progress=job.get("progress", 0.0),
        current_step=job.get("current_step"),
        started_at=job["started_at"],
        completed_at=job.get("completed_at"),
        error_message=job.get("error_message"),
        results_available=job.get("results_available", False)
    )


@router.post("/execute", response_model=ExecuteOptimalResponse)
async def execute_optimal_strategies(
    request: ExecuteOptimalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    optimizer: StrategyOptimizer = Depends(get_optimizer_service)
):
    """
    Execute trades for the best-performing strategies with risk checks.
    """
    # Get optimization results
    if request.optimization_job_id not in _optimization_jobs:
        raise HTTPException(status_code=404, detail="Optimization job not found")
    
    job = _optimization_jobs[request.optimization_job_id]
    
    # Check ownership
    if job["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check job status
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job status is {job['status']}, must be completed"
        )
    
    if not job.get("results"):
        raise HTTPException(status_code=400, detail="No results available")
    
    # Filter symbols if specified
    results_to_execute = job["results"]
    if request.symbols:
        results_to_execute = {
            sym: res for sym, res in results_to_execute.items()
            if sym in request.symbols
        }
    
    # Convert schema results back to dataclass format for optimizer
    from app.services.strategy_optimizer import OptimizationResult, StrategyPerformance
    
    optimization_results = {}
    for symbol, result_schema in results_to_execute.items():
        performances = []
        for perf_schema in result_schema.all_performances:
            perf = StrategyPerformance(
                strategy_id=perf_schema.strategy_id,
                strategy_name=perf_schema.strategy_name,
                symbol=perf_schema.symbol,
                backtest_id=perf_schema.backtest_id,
                total_return=perf_schema.total_return,
                sharpe_ratio=perf_schema.sharpe_ratio,
                max_drawdown=perf_schema.max_drawdown,
                win_rate=perf_schema.win_rate,
                total_trades=perf_schema.total_trades,
                net_profit=perf_schema.net_profit,
                composite_score=perf_schema.composite_score,
                rank=perf_schema.rank
            )
            performances.append(perf)
        
        optimization_results[symbol] = OptimizationResult(
            symbol=result_schema.symbol,
            best_strategy=performances[0] if performances else None,
            all_performances=performances,
            analysis_date=result_schema.analysis_date
        )
    
    # Execute trades
    execution_results = await optimizer.execute_optimal_strategies(
        user_id=current_user.id,
        optimization_results=optimization_results,
        risk_rule_ids=request.risk_rule_ids,
        auto_size=request.auto_size,
        max_position_pct=request.max_position_pct
    )
    
    return ExecuteOptimalResponse(
        job_id=str(uuid4()),
        executed_at=datetime.now(datetime.UTC),
        successful=execution_results["successful"],
        failed=execution_results["failed"],
        blocked=execution_results["blocked"],
        warnings=execution_results["warnings"],
        total_executed=len(execution_results["successful"]),
        total_blocked=len(execution_results["blocked"]),
        total_failed=len(execution_results["failed"])
    )


@router.get("/history", response_model=list[OptimizationHistory])
async def get_optimization_history(
    current_user: User = Depends(get_current_user),
    limit: int = 20
):
    """
    Get user's optimization history.
    """
    user_jobs = [
        job for job in _optimization_jobs.values()
        if job["user_id"] == current_user.id
    ]
    
    # Sort by start date (newest first)
    user_jobs.sort(key=lambda x: x["started_at"], reverse=True)
    
    # Limit results
    user_jobs = user_jobs[:limit]
    
    # Convert to response schema
    history = []
    for job in user_jobs:
        # Calculate best composite score
        best_score = None
        if job.get("results"):
            scores = [
                result.best_strategy.composite_score
                for result in job["results"].values()
                if result.best_strategy
            ]
            best_score = max(scores) if scores else None
        
        history.append(OptimizationHistory(
            job_id=job["job_id"],
            user_id=job["user_id"],
            symbols=[],  # Would need to store in job metadata
            strategy_count=job["total_strategies"],
            status=job["status"],
            started_at=job["started_at"],
            completed_at=job.get("completed_at"),
            total_backtests=job["total_backtests"],
            best_composite_score=best_score
        ))
    
    return history


@router.delete("/jobs/{job_id}")
async def delete_optimization_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete an optimization job.
    """
    if job_id not in _optimization_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = _optimization_jobs[job_id]
    
    # Check ownership
    if job["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    del _optimization_jobs[job_id]
    
    return {"message": "Job deleted successfully"}
