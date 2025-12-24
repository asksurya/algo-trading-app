"""
Background scheduler for automated strategy execution.
Uses APScheduler to evaluate active strategies at regular intervals.
"""
import logging
from datetime import datetime, time, timezone
from typing import Dict, List
import asyncio
from concurrent.futures import ThreadPoolExecutor

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session_local
from app.models.strategy import Strategy
from app.models.strategy_execution import StrategyExecution, ExecutionState
from app.strategies.executor import StrategyExecutor

logger = logging.getLogger(__name__)


class StrategyScheduler:
    """
    Background scheduler for automated strategy execution.
    Runs active strategies at regular intervals during market hours.
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.executor_pool = ThreadPoolExecutor(max_workers=5)
        self.is_running = False
        self._market_hours = {
            "open": time(9, 30),  # 9:30 AM EST
            "close": time(16, 0)  # 4:00 PM EST
        }
        
    def start(self):
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Scheduler already running")
            return
            
        # Evaluate strategies every minute during market hours
        self.scheduler.add_job(
            func=self._evaluate_strategies,
            trigger=IntervalTrigger(minutes=1),
            id="strategy_evaluation",
            name="Evaluate Active Strategies",
            replace_existing=True,
        )
        
        # Reset daily counters at market open
        self.scheduler.add_job(
            func=self._reset_daily_counters,
            trigger=CronTrigger(hour=9, minute=30, day_of_week="mon-fri"),
            id="reset_daily_counters",
            name="Reset Daily Strategy Counters",
            replace_existing=True,
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("Strategy scheduler started")
        
    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            logger.warning("Scheduler not running")
            return
            
        self.scheduler.shutdown(wait=False)
        self.executor_pool.shutdown(wait=False)
        self.is_running = False
        logger.info("Strategy scheduler stopped")
        
    def pause(self):
        """Pause scheduler temporarily."""
        if self.scheduler.running:
            self.scheduler.pause()
            logger.info("Strategy scheduler paused")
            
    def resume(self):
        """Resume paused scheduler."""
        if self.scheduler.running and self.scheduler.state == 2:  # Paused state
            self.scheduler.resume()
            logger.info("Strategy scheduler resumed")
            
    def _is_market_open(self) -> bool:
        """
        Check if market is currently open.
        
        Returns:
            True if market is open, False otherwise
        """
        now = datetime.now().time()
        current_day = datetime.now().weekday()
        
        # Check if weekday (0 = Monday, 4 = Friday)
        if current_day > 4:
            return False
            
        # Check if within market hours
        return self._market_hours["open"] <= now <= self._market_hours["close"]
        
    def _evaluate_strategies(self):
        """
        Evaluate all active strategies.
        Called every minute by the scheduler.
        """
        # Check if market is open
        if not self._is_market_open():
            logger.debug("Market closed, skipping strategy evaluation")
            return
            
        logger.info("Evaluating active strategies")
        
        # Run async function in executor
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._evaluate_strategies_async())
        except Exception as e:
            logger.error(f"Error evaluating strategies: {e}")
        finally:
            loop.close()
            
    async def _evaluate_strategies_async(self):
        """Async implementation of strategy evaluation."""
        AsyncSessionLocal = get_async_session_local()
        async with AsyncSessionLocal() as session:
            try:
                # Get all active strategy executions
                result = await session.execute(
                    select(StrategyExecution)
                    .where(StrategyExecution.state == ExecutionState.ACTIVE)
                    .where(StrategyExecution.state == ExecutionState.ACTIVE)
                )
                active_executions = result.scalars().all()
                
                if not active_executions:
                    logger.debug("No active strategies to evaluate")
                    return
                    
                logger.info(f"Found {len(active_executions)} active strategies")
                
                # Evaluate each strategy
                for execution in active_executions:
                    try:
                        await self._evaluate_single_strategy(session, execution)
                    except Exception as e:
                        logger.error(
                            f"Error evaluating strategy {execution.strategy_id}: {e}"
                        )
                        # Update error state
                        execution.last_error = str(e)
                        execution.error_count += 1
                        
                        # Pause strategy if too many errors
                        if execution.error_count >= 5:
                            execution.state = ExecutionState.ERROR
                            logger.error(
                                f"Strategy {execution.strategy_id} paused due to "
                                f"repeated errors"
                            )
                            
                await session.commit()
                
            except Exception as e:
                logger.error(f"Error in strategy evaluation loop: {e}")
                await session.rollback()
                
    async def _evaluate_single_strategy(
        self,
        session: AsyncSession,
        execution: StrategyExecution
    ):
        """
        Evaluate a single strategy and execute if signal generated.
        
        Args:
            session: Database session
            execution: StrategyExecution instance
        """
        strategy_id = execution.strategy_id
        logger.debug(f"Evaluating strategy {strategy_id}")
        
        # Check circuit breakers
        if execution.trades_today >= execution.max_trades_per_day:
            logger.info(
                f"Strategy {strategy_id} reached max trades per day "
                f"({execution.max_trades_per_day})"
            )
            return
            
        if execution.daily_loss and execution.daily_loss <= -execution.max_daily_loss:
            logger.warning(
                f"Strategy {strategy_id} hit max daily loss "
                f"({execution.max_daily_loss})"
            )
            execution.state = ExecutionState.PAUSED
            return
            
        # Load strategy model
        result = await session.execute(
            select(Strategy).where(Strategy.id == strategy_id)
        )
        strategy = result.scalar_one_or_none()

        if not strategy:
            logger.error(f"Strategy {strategy_id} not found")
            return

        # Execute strategy
        executor = StrategyExecutor()

        try:
            result = await executor.execute_strategy(strategy, execution, session)
            
            # Update execution state
            execution.last_evaluated_at = datetime.now(timezone.utc)
            execution.evaluation_count += 1
            
            if result.get("signal"):
                execution.last_signal_at = datetime.now(timezone.utc)
                
            if result.get("order_id"):
                execution.trades_today += 1
                execution.total_trades += 1
                
            # Clear error count on successful execution
            execution.error_count = 0
            execution.last_error = None
            
            logger.info(
                f"Strategy {strategy_id} evaluated successfully. "
                f"Signal: {result.get('signal', 'HOLD')}"
            )
            
        except Exception as e:
            logger.error(f"Strategy {strategy_id} execution failed: {e}")
            raise
            
    def _reset_daily_counters(self):
        """
        Reset daily counters at market open.
        Called once per day via cron trigger.
        """
        logger.info("Resetting daily strategy counters")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._reset_daily_counters_async())
        except Exception as e:
            logger.error(f"Error resetting daily counters: {e}")
        finally:
            loop.close()
            
    async def _reset_daily_counters_async(self):
        """Async implementation of daily counter reset."""
        AsyncSessionLocal = get_async_session_local()
        async with AsyncSessionLocal() as session:
            try:
                # Get all active executions
                result = await session.execute(
                    select(StrategyExecution)
                    .where(StrategyExecution.state == ExecutionState.ACTIVE)
                )
                executions = result.scalars().all()
                
                # Reset counters
                for execution in executions:
                    execution.trades_today = 0
                    execution.daily_pnl = 0.0
                    execution.daily_loss = 0.0
                    
                    # Resume paused strategies at market open
                    if execution.state == ExecutionState.PAUSED:
                        execution.state = ExecutionState.ACTIVE
                        logger.info(f"Resumed strategy {execution.strategy_id}")
                        
                await session.commit()
                logger.info(f"Reset daily counters for {len(executions)} strategies")
                
            except Exception as e:
                logger.error(f"Error resetting daily counters: {e}")
                await session.rollback()
                
    def get_status(self) -> Dict:
        """
        Get scheduler status.
        
        Returns:
            Dictionary with scheduler status information
        """
        return {
            "running": self.is_running,
            "paused": self.scheduler.state == 2 if self.scheduler.running else False,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                }
                for job in self.scheduler.get_jobs()
            ],
            "market_open": self._is_market_open(),
        }


# Singleton instance
_scheduler: StrategyScheduler = None


def get_scheduler() -> StrategyScheduler:
    """
    Get or create singleton scheduler instance.
    
    Returns:
        StrategyScheduler instance
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = StrategyScheduler()
    return _scheduler


def start_scheduler():
    """Start the global scheduler."""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """Stop the global scheduler."""
    scheduler = get_scheduler()
    scheduler.stop()
