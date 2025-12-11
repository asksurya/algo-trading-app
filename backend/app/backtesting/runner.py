"""
Backtest runner service.
Executes backtests using the existing engine and stores results.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from uuid import UUID
import asyncio
import pandas as pd
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.backtest import Backtest, BacktestResult, BacktestTrade, BacktestStatus
from app.models.strategy import Strategy
from app.services.market_data_cache_service import MarketDataCacheService

# Import BacktestEngine and Strategies
try:
    from src.backtesting.backtest_engine import BacktestEngine
    from src.strategies.sma_crossover import SMACrossoverStrategy
    from src.strategies.rsi_strategy import RSIStrategy
    # Add other strategies as needed
except ImportError:
    logging.warning("Could not import src.backtesting. Ensure PYTHONPATH includes the project root.")
    BacktestEngine = None

logger = logging.getLogger(__name__)


class BacktestRunner:
    """Orchestrates backtest execution and result storage."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.cache_service = MarketDataCacheService(session)
        
    async def run_backtest(self, backtest_id: UUID) -> Dict[str, Any]:
        """
        Execute a backtest and store results.
        
        Args:
            backtest_id: Backtest configuration ID
            
        Returns:
            Dictionary with execution summary
        """
        # Load backtest configuration
        result = await self.session.execute(
            select(Backtest).where(Backtest.id == backtest_id)
        )
        backtest = result.scalar_one_or_none()
        
        if not backtest:
            raise ValueError(f"Backtest {backtest_id} not found")
            
        # Load strategy
        result = await self.session.execute(
            select(Strategy).where(Strategy.id == backtest.strategy_id)
        )
        strategy = result.scalar_one_or_none()
        
        if not strategy:
            raise ValueError(f"Strategy {backtest.strategy_id} not found")
            
        try:
            # Update status to running
            started_at = datetime.now(timezone.utc)
            backtest.status = BacktestStatus.RUNNING
            backtest.started_at = started_at
            await self.session.commit()
            
            # Refresh strategy to prevent MissingGreenlet on property access
            # We don't necessarily need to refresh backtest if we use local started_at
            await self.session.refresh(strategy)
            await self.session.refresh(backtest)
            
            # Run backtest
            results = await self._execute_backtest(
                backtest,
                strategy
            )
            
            # Store results
            await self._store_results(backtest, results)
            
            # Update status to completed
            completed_at = datetime.now(timezone.utc)
            backtest.status = BacktestStatus.COMPLETED
            backtest.completed_at = completed_at
            
            if started_at:
                backtest.duration_seconds = (
                    completed_at - started_at
                ).total_seconds()
            
            # Update summary fields
            metrics = results.get("metrics", {})
            backtest.total_trades = metrics.get("total_trades", 0)
            backtest.winning_trades = metrics.get("winning_trades", 0)
            backtest.losing_trades = metrics.get("losing_trades", 0)
            backtest.total_return = metrics.get("total_return_pct", 0)
            backtest.total_pnl = metrics.get("net_profit", 0)
            backtest.max_drawdown = metrics.get("max_drawdown_pct", 0)
            backtest.sharpe_ratio = metrics.get("sharpe_ratio")
            backtest.win_rate = metrics.get("win_rate_pct", 0)
            
            await self.session.commit()
            
            return {
                "success": True,
                "backtest_id": str(backtest_id),
                "status": "completed",
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"Backtest {backtest_id} failed: {e}", exc_info=True)
            backtest.status = BacktestStatus.FAILED
            backtest.error_message = str(e)
            backtest.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            raise
            
    async def _execute_backtest(
        self,
        backtest: Backtest,
        strategy_model: Strategy
    ) -> Dict[str, Any]:
        """
        Execute backtest logic using the real BacktestEngine.
        """
        if BacktestEngine is None:
            raise ImportError("BacktestEngine not available. Check PYTHONPATH.")

        # 1. Instantiate Strategy
        strategy_instance = self._create_strategy_instance(strategy_model)
        
        # 2. Prepare parameters
        # Use the first ticker from the strategy or a default
        # In a real app, we might backtest multiple tickers or a portfolio
        # For now, we'll assume single ticker backtest or take the first one
        # We need to fetch tickers associated with the strategy
        # But for now, let's assume the ticker is passed in backtest params or strategy params
        
        # Check backtest.strategy_params or strategy_model.parameters for symbol
        symbol = "SPY" # Default
        if backtest.strategy_params and "symbol" in backtest.strategy_params:
            symbol = backtest.strategy_params["symbol"]
        elif strategy_model.parameters and "symbol" in strategy_model.parameters:
            symbol = strategy_model.parameters["symbol"]
            
        start_date = backtest.start_date.strftime("%Y-%m-%d")
        end_date = backtest.end_date.strftime("%Y-%m-%d")
        
        # 3. Initialize Engine
        engine = BacktestEngine(
            strategy=strategy_instance,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=backtest.initial_capital,
            commission=backtest.commission,
            slippage=backtest.slippage
        )
        
        # 4. Run Engine (it's synchronous, so we might want to run it in a thread pool if it's slow)
        # For now, running directly is fine as it's CPU bound but pandas is fast
        # To be safe for async FastAPI, we can use run_in_executor
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, engine.run)
        
        return results

    def _create_strategy_instance(self, strategy_model: Strategy):
        """Factory method to create strategy instance from model."""
        strategy_type = strategy_model.strategy_type.lower()
        params = strategy_model.parameters or {}
        
        # Remove 'symbol' from params if it exists, as it's not a strategy init param usually
        # (It depends on the strategy __init__)
        init_params = params.copy()
        if "symbol" in init_params:
            del init_params["symbol"]
            
        if strategy_type == "sma_crossover":
            return SMACrossoverStrategy(
                short_window=int(init_params.get("short_window", 50)),
                long_window=int(init_params.get("long_window", 200))
            )
        elif strategy_type == "rsi":
            # Assuming RSIStrategy has period, overbought, oversold
            return RSIStrategy(
                period=int(init_params.get("period", 14)),
                overbought=int(init_params.get("overbought", 70)),
                oversold=int(init_params.get("oversold", 30))
            )
        else:
            # Fallback or error
            # For now, default to SMA if unknown, or raise error
            logger.warning(f"Unknown strategy type {strategy_type}, defaulting to SMA")
            return SMACrossoverStrategy()

    async def _store_results(
        self,
        backtest: Backtest,
        results: Dict[str, Any]
    ):
        """Store backtest results to database."""
        metrics = results.get("metrics", {})
        trades = results.get("trades", [])
        equity_curve = results.get("equity_curve")
        
        # Convert equity curve to dict/json if it's a Series
        equity_curve_dict = {}
        if isinstance(equity_curve, pd.Series):
            # Convert timestamp keys to strings
            equity_curve_dict = {
                k.strftime("%Y-%m-%d"): float(v) 
                for k, v in equity_curve.items()
            }
            
        # Create BacktestResult
        backtest_result = BacktestResult(
            backtest_id=backtest.id,
            final_capital=metrics.get("final_value", 0.0),
            total_return_pct=metrics.get("total_return_pct", 0.0),
            annualized_return=0.0, # Not calculated in engine yet
            total_trades=metrics.get("total_trades", 0),
            winning_trades=metrics.get("winning_trades", 0),
            losing_trades=metrics.get("losing_trades", 0),
            win_rate=metrics.get("win_rate_pct", 0.0), # Engine returns pct
            gross_profit=0.0, # Not explicitly in metrics dict sometimes
            gross_loss=0.0,
            net_profit=metrics.get("total_return", 0.0) * metrics.get("initial_capital", 0.0), # Approx
            avg_trade_pnl=metrics.get("avg_profit", 0.0),
            max_drawdown_pct=metrics.get("max_drawdown_pct", 0.0),
            max_drawdown_dollars=0.0,
            sharpe_ratio=metrics.get("sharpe_ratio", 0.0),
            equity_curve=equity_curve_dict,
        )
        
        self.session.add(backtest_result)
        
        # Create BacktestTrade records
        for trade_data in trades:
            # trade_data keys from engine: 
            # entry_date, exit_date, entry_price, exit_price, shares, profit, profit_pct, duration
            
            trade = BacktestTrade(
                backtest_id=backtest.id,
                symbol=results.get("symbol", "UNKNOWN"),
                side="long", # Engine currently only does long
                quantity=trade_data.get("shares", 0),
                entry_price=trade_data.get("entry_price", 0.0),
                exit_price=trade_data.get("exit_price", 0.0),
                entry_date=trade_data.get("entry_date"),
                exit_date=trade_data.get("exit_date"),
                pnl=trade_data.get("profit", 0.0),
                pnl_pct=trade_data.get("profit_pct", 0.0),
                commission=0.0, # Engine handles it in net profit but doesn't output per trade explicitly
                is_open=False,
            )
            self.session.add(trade)
            
        await self.session.commit()

