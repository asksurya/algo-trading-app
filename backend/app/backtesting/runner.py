"""
Backtest runner service.
Executes backtests using the existing engine and stores results.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import UUID
import asyncio
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.backtest import Backtest, BacktestResult, BacktestTrade, BacktestStatus
from app.models.strategy import Strategy
from app.integrations.market_data import get_market_data_service

logger = logging.getLogger(__name__)


class BacktestRunner:
    """Orchestrates backtest execution and result storage."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.market_data = get_market_data_service()
        
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
            backtest.status = BacktestStatus.RUNNING
            backtest.started_at = datetime.utcnow()
            await self.session.commit()
            
            # Fetch historical data
            logger.info(f"Fetching data for backtest {backtest_id}")
            hist_data = await self._fetch_historical_data(
                strategy.tickers[0].ticker if strategy.tickers else "SPY",
                backtest.start_date,
                backtest.end_date
            )
            
            # Run backtest (simplified - would integrate with src/backtesting/backtest_engine.py)
            results = await self._execute_backtest(
                backtest,
                strategy,
                hist_data
            )
            
            # Store results
            await self._store_results(backtest, results)
            
            # Update status to completed
            backtest.status = BacktestStatus.COMPLETED
            backtest.completed_at = datetime.utcnow()
            backtest.duration_seconds = (
                backtest.completed_at - backtest.started_at
            ).total_seconds()
            
            # Update summary fields
            backtest.total_trades = results.get("total_trades", 0)
            backtest.winning_trades = results.get("winning_trades", 0)
            backtest.losing_trades = results.get("losing_trades", 0)
            backtest.total_return = results.get("total_return_pct", 0)
            backtest.total_pnl = results.get("net_profit", 0)
            backtest.max_drawdown = results.get("max_drawdown_pct", 0)
            backtest.sharpe_ratio = results.get("sharpe_ratio")
            backtest.win_rate = results.get("win_rate", 0)
            
            await self.session.commit()
            
            return {
                "success": True,
                "backtest_id": str(backtest_id),
                "status": "completed",
                "metrics": {
                    "total_trades": backtest.total_trades,
                    "win_rate": backtest.win_rate,
                    "total_return": backtest.total_return,
                    "sharpe_ratio": backtest.sharpe_ratio,
                }
            }
            
        except Exception as e:
            logger.error(f"Backtest {backtest_id} failed: {e}")
            backtest.status = BacktestStatus.FAILED
            backtest.error_message = str(e)
            backtest.completed_at = datetime.utcnow()
            await self.session.commit()
            raise
            
    async def _fetch_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Fetch historical market data."""
        try:
            bars = await self.market_data.get_bars(
                symbol=symbol,
                start=start_date,
                end=end_date,
                timeframe="1Day"
            )
            
            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    "timestamp": bar.timestamp,
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": int(bar.volume),
                }
                for bar in bars
            ])
            
            df.set_index("timestamp", inplace=True)
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            raise
            
    async def _execute_backtest(
        self,
        backtest: Backtest,
        strategy: Strategy,
        data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Execute backtest logic.
        In production, this would integrate with src/backtesting/backtest_engine.py
        """
        # Simplified backtest execution
        # TODO: Integrate with actual backtest engine from src/
        
        initial_capital = backtest.initial_capital
        capital = initial_capital
        position = None
        trades = []
        
        # Simple buy-and-hold for demonstration
        entry_price = data.iloc[0]["close"]
        exit_price = data.iloc[-1]["close"]
        
        trade = {
            "symbol": strategy.tickers[0].ticker if strategy.tickers else "SPY",
            "side": "buy",
            "quantity": initial_capital / entry_price,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "entry_date": data.index[0],
            "exit_date": data.index[-1],
            "pnl": (exit_price - entry_price) * (initial_capital / entry_price),
            "pnl_pct": ((exit_price - entry_price) / entry_price) * 100,
            "commission": backtest.commission * 2 * initial_capital,
        }
        
        trades.append(trade)
        
        final_capital = initial_capital + trade["pnl"] - trade["commission"]
        total_return = ((final_capital - initial_capital) / initial_capital) * 100
        
        return {
            "trades": trades,
            "final_capital": final_capital,
            "total_return_pct": total_return,
            "annualized_return": total_return,  # Simplified
            "total_trades": len(trades),
            "winning_trades": 1 if trade["pnl"] > 0 else 0,
            "losing_trades": 1 if trade["pnl"] < 0 else 0,
            "win_rate": 100.0 if trade["pnl"] > 0 else 0.0,
            "gross_profit": trade["pnl"] if trade["pnl"] > 0 else 0,
            "gross_loss": trade["pnl"] if trade["pnl"] < 0 else 0,
            "net_profit": trade["pnl"] - trade["commission"],
            "max_drawdown_pct": 0.0,
            "sharpe_ratio": 0.0,
        }
        
    async def _store_results(
        self,
        backtest: Backtest,
        results: Dict[str, Any]
    ):
        """Store backtest results to database."""
        # Create BacktestResult
        backtest_result = BacktestResult(
            backtest_id=backtest.id,
            final_capital=results["final_capital"],
            total_return_pct=results["total_return_pct"],
            annualized_return=results["annualized_return"],
            total_trades=results["total_trades"],
            winning_trades=results["winning_trades"],
            losing_trades=results["losing_trades"],
            win_rate=results["win_rate"],
            gross_profit=results["gross_profit"],
            gross_loss=results["gross_loss"],
            net_profit=results["net_profit"],
            avg_trade_pnl=results["net_profit"] / max(results["total_trades"], 1),
            max_drawdown_pct=results["max_drawdown_pct"],
            max_drawdown_dollars=0.0,
            sharpe_ratio=results.get("sharpe_ratio"),
            equity_curve={},
        )
        
        self.session.add(backtest_result)
        
        # Create BacktestTrade records
        for trade_data in results["trades"]:
            trade = BacktestTrade(
                backtest_id=backtest.id,
                symbol=trade_data["symbol"],
                side=trade_data["side"],
                quantity=trade_data["quantity"],
                entry_price=trade_data["entry_price"],
                exit_price=trade_data.get("exit_price"),
                entry_date=trade_data["entry_date"],
                exit_date=trade_data.get("exit_date"),
                pnl=trade_data.get("pnl"),
                pnl_pct=trade_data.get("pnl_pct"),
                commission=trade_data.get("commission", 0),
                is_open=False,
            )
            self.session.add(trade)
            
        await self.session.commit()
