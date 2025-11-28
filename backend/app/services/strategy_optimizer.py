"""
Strategy optimizer service for multi-ticker analysis and automated execution.
Enables parallel backtesting across multiple strategies and symbols,
performance ranking, and risk-aware automated trading.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4
import asyncio
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.strategy import Strategy
from app.models.backtest import Backtest, BacktestStatus
from app.models.order import Order, OrderSideEnum, OrderTypeEnum
from app.backtesting.runner import BacktestRunner
from app.services.risk_manager import RiskManager
from app.services.notification_service import NotificationService
from app.integrations.order_execution import AlpacaOrderExecutor
from app.integrations.alpaca_client import AlpacaClient

logger = logging.getLogger(__name__)


@dataclass
class StrategyPerformance:
    """Performance metrics for a strategy on a specific symbol."""
    strategy_id: int
    strategy_name: str
    symbol: str
    backtest_id: UUID
    total_return: float
    sharpe_ratio: Optional[float]
    max_drawdown: float
    win_rate: float
    total_trades: int
    net_profit: float
    composite_score: float
    rank: int = 0


@dataclass
class OptimizationResult:
    """Results of strategy optimization for a symbol."""
    symbol: str
    best_strategy: StrategyPerformance
    all_performances: List[StrategyPerformance]
    analysis_date: datetime


class StrategyOptimizer:
    """
    Orchestrates multi-strategy backtesting, performance ranking,
    and automated trade execution with risk management.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        alpaca_client: AlpacaClient,
        risk_manager: RiskManager,
        notification_service: NotificationService,
        order_execution: AlpacaOrderExecutor
    ):
        self.db = db
        self.alpaca = alpaca_client
        self.risk_manager = risk_manager
        self.notification_service = notification_service
        self.order_execution = order_execution
        self.backtest_runner = BacktestRunner(db)
    
    async def optimize_strategies(
        self,
        user_id: int,
        symbols: List[str],
        strategy_ids: Optional[List[int]] = None,
        start_date: datetime = None,
        end_date: datetime = None,
        initial_capital: float = 100000.0
    ) -> Dict[str, OptimizationResult]:
        """
        Run backtests for all strategies on all symbols and rank performance.
        
        Args:
            user_id: User ID
            symbols: List of ticker symbols to analyze
            strategy_ids: Optional list of strategy IDs (all if None)
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Initial capital for backtests
            
        Returns:
            Dictionary mapping symbol to OptimizationResult
        """
        logger.info(
            f"Starting strategy optimization for user {user_id}: "
            f"{len(symbols)} symbols, strategies: {strategy_ids}"
        )
        
        # Get strategies
        strategies = await self._get_strategies(user_id, strategy_ids)
        if not strategies:
            raise ValueError("No strategies found for user")
        
        logger.info(f"Analyzing {len(strategies)} strategies")
        
        # Create backtest configurations for all strategy-symbol combinations
        backtest_configs = []
        for symbol in symbols:
            for strategy in strategies:
                config = await self._create_backtest_config(
                    user_id=user_id,
                    strategy_id=strategy.id,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=initial_capital
                )
                backtest_configs.append((symbol, strategy, config))
        
        logger.info(f"Created {len(backtest_configs)} backtest configurations")
        
        # Execute backtests in parallel (in batches to avoid overload)
        batch_size = 5
        results = {}
        
        for i in range(0, len(backtest_configs), batch_size):
            batch = backtest_configs[i:i + batch_size]
            batch_results = await self._execute_backtest_batch(batch)
            
            # Group results by symbol
            for symbol, strategy, backtest_result in batch_results:
                if symbol not in results:
                    results[symbol] = []
                results[symbol].append((strategy, backtest_result))
        
        # Calculate composite scores and rank strategies per symbol
        optimization_results = {}
        for symbol, symbol_results in results.items():
            performances = []
            
            for strategy, backtest_result in symbol_results:
                performance = await self._create_performance_metrics(
                    strategy=strategy,
                    symbol=symbol,
                    backtest_result=backtest_result
                )
                performances.append(performance)
            
            # Sort by composite score (descending)
            performances.sort(key=lambda p: p.composite_score, reverse=True)
            
            # Assign ranks
            for rank, perf in enumerate(performances, start=1):
                perf.rank = rank
            
            # Create optimization result
            optimization_results[symbol] = OptimizationResult(
                symbol=symbol,
                best_strategy=performances[0] if performances else None,
                all_performances=performances,
                analysis_date=datetime.now(datetime.UTC)
            )
        
        logger.info(
            f"Optimization complete: {len(optimization_results)} symbols analyzed"
        )
        
        return optimization_results
    
    async def execute_optimal_strategies(
        self,
        user_id: int,
        optimization_results: Dict[str, OptimizationResult],
        risk_rule_ids: Optional[List[int]] = None,
        auto_size: bool = True,
        max_position_pct: float = 10.0
    ) -> Dict[str, Any]:
        """
        Execute trades for the best-performing strategies with risk checks.
        
        Args:
            user_id: User ID
            optimization_results: Results from optimize_strategies
            risk_rule_ids: Optional list of risk rule IDs to enforce
            auto_size: Whether to auto-calculate position sizes
            max_position_pct: Maximum position size as % of portfolio
            
        Returns:
            Dictionary with execution results
        """
        logger.info(
            f"Executing optimal strategies for user {user_id}: "
            f"{len(optimization_results)} symbols"
        )
        
        execution_results = {
            "successful": [],
            "failed": [],
            "blocked": [],
            "warnings": []
        }
        
        # Get account info for position sizing
        account = await self.alpaca.get_account()
        equity = float(account.equity)
        
        for symbol, opt_result in optimization_results.items():
            if not opt_result.best_strategy:
                execution_results["failed"].append({
                    "symbol": symbol,
                    "error": "No valid strategy found"
                })
                continue
            
            try:
                # Calculate position size
                max_position_value = equity * (max_position_pct / 100)
                
                # Get current quote for entry price
                quote = await self.alpaca.get_latest_quote(symbol)
                entry_price = float(quote.ask_price)
                
                # Calculate shares
                shares = int(max_position_value / entry_price)
                if shares < 1:
                    execution_results["warnings"].append({
                        "symbol": symbol,
                        "message": "Insufficient capital for minimum position"
                    })
                    continue
                
                order_value = shares * entry_price
                
                # Check risk rules
                breaches = await self.risk_manager.evaluate_rules(
                    user_id=str(user_id),
                    strategy_id=str(opt_result.best_strategy.strategy_id),
                    symbol=symbol,
                    order_qty=float(shares),
                    order_value=order_value
                )
                
                # Handle blocking breaches
                blocking_breaches = [
                    b for b in breaches
                    if b.action in ["BLOCK", "CLOSE_POSITION"]
                ]
                
                if blocking_breaches:
                    execution_results["blocked"].append({
                        "symbol": symbol,
                        "strategy": opt_result.best_strategy.strategy_name,
                        "breaches": [
                            {
                                "rule": b.rule_name,
                                "message": b.message,
                                "action": b.action
                            }
                            for b in blocking_breaches
                        ]
                    })
                    
                    # Send notification
                    await self.notification_service.create_notification(
                        user_id=user_id,
                        title=f"Trade Blocked: {symbol}",
                        message=f"Risk rule breach prevented trade execution",
                        notification_type="RISK_ALERT",
                        priority="high",
                        metadata={
                            "symbol": symbol,
                            "breaches": [b.rule_name for b in blocking_breaches]
                        }
                    )
                    continue
                
                # Create and submit order
                order = Order(
                    user_id=user_id,
                    strategy_id=opt_result.best_strategy.strategy_id,
                    symbol=symbol,
                    side=OrderSideEnum.BUY,
                    order_type=OrderTypeEnum.MARKET,
                    time_in_force="day",
                    quantity=shares,
                    status="pending_submission",
                    metadata={
                        "optimization_score": opt_result.best_strategy.composite_score,
                        "expected_return": opt_result.best_strategy.total_return,
                        "auto_executed": True
                    }
                )
                
                self.db.add(order)
                await self.db.commit()
                await self.db.refresh(order)
                
                # Submit to broker
                alpaca_order = await self.order_execution.submit_order(
                    order_id=order.id
                )
                
                execution_results["successful"].append({
                    "symbol": symbol,
                    "strategy": opt_result.best_strategy.strategy_name,
                    "order_id": str(order.id),
                    "alpaca_order_id": alpaca_order.id,
                    "shares": shares,
                    "estimated_value": order_value,
                    "composite_score": opt_result.best_strategy.composite_score
                })
                
                # Send success notification
                await self.notification_service.create_notification(
                    user_id=user_id,
                    title=f"Auto-Trade Executed: {symbol}",
                    message=(
                        f"Bought {shares} shares using {opt_result.best_strategy.strategy_name} "
                        f"(Score: {opt_result.best_strategy.composite_score:.2f})"
                    ),
                    notification_type="ORDER",
                    priority="medium",
                    metadata={
                        "symbol": symbol,
                        "order_id": str(order.id),
                        "strategy": opt_result.best_strategy.strategy_name
                    }
                )
                
            except Exception as e:
                logger.error(f"Failed to execute trade for {symbol}: {e}")
                execution_results["failed"].append({
                    "symbol": symbol,
                    "error": str(e)
                })
        
        logger.info(
            f"Execution complete: {len(execution_results['successful'])} successful, "
            f"{len(execution_results['failed'])} failed, "
            f"{len(execution_results['blocked'])} blocked"
        )
        
        return execution_results
    
    async def _get_strategies(
        self,
        user_id: int,
        strategy_ids: Optional[List[int]] = None
    ) -> List[Strategy]:
        """Get strategies for analysis."""
        query = select(Strategy).where(Strategy.user_id == user_id)
        
        if strategy_ids:
            query = query.where(Strategy.id.in_(strategy_ids))
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def _create_backtest_config(
        self,
        user_id: int,
        strategy_id: int,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float
    ) -> Backtest:
        """Create a backtest configuration."""
        backtest = Backtest(
            id=uuid4(),
            user_id=user_id,
            strategy_id=strategy_id,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            commission=0.0,  # Commission-free for Alpaca
            slippage=0.001,  # 0.1% slippage
            status=BacktestStatus.PENDING,
            metadata={
                "symbol": symbol,
                "optimization_run": True
            }
        )
        
        self.db.add(backtest)
        await self.db.commit()
        await self.db.refresh(backtest)
        
        return backtest
    
    async def _execute_backtest_batch(
        self,
        batch: List[tuple]
    ) -> List[tuple]:
        """Execute a batch of backtests in parallel."""
        tasks = []
        
        for symbol, strategy, backtest in batch:
            task = self._execute_single_backtest(symbol, strategy, backtest)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful results
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                symbol, strategy, backtest = batch[i]
                logger.error(
                    f"Backtest failed for {strategy.name} on {symbol}: {result}"
                )
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def _execute_single_backtest(
        self,
        symbol: str,
        strategy: Strategy,
        backtest: Backtest
    ) -> tuple:
        """Execute a single backtest."""
        try:
            result = await self.backtest_runner.run_backtest(backtest.id)
            return (symbol, strategy, result)
        except Exception as e:
            logger.error(f"Backtest execution failed: {e}")
            raise
    
    async def _create_performance_metrics(
        self,
        strategy: Strategy,
        symbol: str,
        backtest_result: Dict[str, Any]
    ) -> StrategyPerformance:
        """Create performance metrics and calculate composite score."""
        # Extract metrics from backtest result
        total_return = backtest_result.get("metrics", {}).get("total_return", 0)
        sharpe_ratio = backtest_result.get("metrics", {}).get("sharpe_ratio", 0)
        max_drawdown = abs(
            backtest_result.get("metrics", {}).get("max_drawdown", 0)
        )
        win_rate = backtest_result.get("metrics", {}).get("win_rate", 0)
        total_trades = backtest_result.get("metrics", {}).get("total_trades", 0)
        
        # Get net profit from backtest
        backtest_id = backtest_result.get("backtest_id")
        result = await self.db.execute(
            select(Backtest).where(Backtest.id == backtest_id)
        )
        backtest = result.scalar_one_or_none()
        net_profit = backtest.total_pnl if backtest else 0
        
        # Calculate composite score
        composite_score = await self._calculate_composite_score(
            total_return=total_return,
            sharpe_ratio=sharpe_ratio or 0,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=total_trades
        )
        
        return StrategyPerformance(
            strategy_id=strategy.id,
            strategy_name=strategy.name,
            symbol=symbol,
            backtest_id=backtest_id,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=total_trades,
            net_profit=net_profit,
            composite_score=composite_score
        )
    
    async def _calculate_composite_score(
        self,
        total_return: float,
        sharpe_ratio: float,
        max_drawdown: float,
        win_rate: float,
        total_trades: int
    ) -> float:
        """
        Calculate risk-adjusted composite score for strategy ranking.
        
        Scoring weights:
        - Return: 30%
        - Sharpe Ratio: 30%
        - Max Drawdown (inverse): 20%
        - Win Rate: 15%
        - Trade Count (activity): 5%
        """
        # Normalize return (cap at 100%)
        return_score = min(total_return / 100, 1.0) * 30
        
        # Normalize Sharpe (2.0 = excellent)
        sharpe_score = min(sharpe_ratio / 2.0, 1.0) * 30 if sharpe_ratio else 0
        
        # Drawdown penalty (lower is better, cap at 50%)
        drawdown_score = max(0, (1 - max_drawdown / 50)) * 20
        
        # Win rate score
        win_rate_score = (win_rate / 100) * 15
        
        # Activity score (min 10 trades = full points)
        activity_score = min(total_trades / 10, 1.0) * 5
        
        composite = (
            return_score +
            sharpe_score +
            drawdown_score +
            win_rate_score +
            activity_score
        )
        
        return round(composite, 2)
