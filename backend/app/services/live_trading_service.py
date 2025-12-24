"""
Live Trading Service for real-time trading operations.

This service provides the core functionality for live trading, including:
- System status monitoring
- Portfolio management via Alpaca
- Active strategy monitoring
- Order management
- Strategy lifecycle actions (pause/resume/stop)
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.integrations.alpaca_client import AlpacaAPIError, get_alpaca_client
from app.models import LiveStrategy, LiveStrategyStatus, SignalHistory

logger = logging.getLogger(__name__)


class LiveTradingService:
    """
    Service for managing live trading operations.

    Integrates with the Alpaca broker API for real-time portfolio data
    and coordinates with the database for strategy management.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._alpaca_client = None

    @property
    def alpaca_client(self):
        """Lazy-load Alpaca client to avoid initialization issues."""
        if self._alpaca_client is None:
            try:
                self._alpaca_client = get_alpaca_client()
            except Exception as e:
                logger.warning(f"Failed to initialize Alpaca client: {e}")
        return self._alpaca_client

    async def get_system_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get the current live trading system status.

        Aggregates data from:
        - Alpaca broker (account status, trading enabled)
        - Database (active strategies, total PnL)

        Args:
            user_id: The user's ID

        Returns:
            Dictionary containing system status information
        """
        # Get active strategies count and total PnL from database
        active_count = 0
        total_pnl = 0.0
        last_trade_at = None
        is_running = False
        broker_connected = False
        account_status = "unknown"

        try:
            # Query active strategies for this user
            result = await self.db.execute(
                select(LiveStrategy).where(
                    LiveStrategy.user_id == str(user_id),
                    LiveStrategy.status == LiveStrategyStatus.ACTIVE,
                )
            )
            active_strategies = result.scalars().all()
            active_count = len(active_strategies)
            is_running = active_count > 0

            # Sum up total PnL from all user's live strategies
            pnl_result = await self.db.execute(
                select(func.sum(LiveStrategy.total_pnl)).where(
                    LiveStrategy.user_id == str(user_id)
                )
            )
            pnl_sum = pnl_result.scalar()
            total_pnl = float(pnl_sum) if pnl_sum else 0.0

            # Get most recent signal/trade timestamp
            signal_result = await self.db.execute(
                select(SignalHistory.timestamp)
                .join(LiveStrategy, SignalHistory.live_strategy_id == LiveStrategy.id)
                .where(
                    LiveStrategy.user_id == str(user_id), SignalHistory.executed == True
                )
                .order_by(SignalHistory.timestamp.desc())
                .limit(1)
            )
            last_signal = signal_result.scalar()
            if last_signal:
                last_trade_at = (
                    last_signal.isoformat()
                    if hasattr(last_signal, "isoformat")
                    else str(last_signal)
                )

        except Exception as e:
            logger.error(f"Error querying database for system status: {e}")

        # Check Alpaca broker connection
        try:
            if self.alpaca_client:
                account = await self.alpaca_client.get_account(use_cache=True)
                broker_connected = True
                account_status = account.get("status", "unknown")
        except AlpacaAPIError as e:
            logger.warning(f"Alpaca API error: {e}")
            broker_connected = False
        except Exception as e:
            logger.warning(f"Error connecting to Alpaca: {e}")
            broker_connected = False

        return {
            "is_running": is_running,
            "active_strategies": active_count,
            "total_pnl": total_pnl,
            "last_trade_at": last_trade_at,
            "broker_connected": broker_connected,
            "account_status": account_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_portfolio(self, user_id: int) -> Dict[str, Any]:
        """
        Get the current portfolio from Alpaca broker.

        Fetches real-time account data including:
        - Total portfolio value
        - Cash balance
        - All open positions with current market values

        Args:
            user_id: The user's ID

        Returns:
            Dictionary containing portfolio information
        """
        portfolio = {
            "total_value": 0.0,
            "cash": 0.0,
            "buying_power": 0.0,
            "equity": 0.0,
            "positions": [],
            "unrealized_pnl": 0.0,
            "unrealized_pnl_pct": 0.0,
            "day_pnl": 0.0,
            "day_pnl_pct": 0.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if not self.alpaca_client:
            logger.warning("Alpaca client not available")
            return portfolio

        try:
            # Get account information
            account = await self.alpaca_client.get_account(use_cache=False)

            portfolio["total_value"] = account.get("portfolio_value", 0.0)
            portfolio["cash"] = account.get("cash", 0.0)
            portfolio["buying_power"] = account.get("buying_power", 0.0)
            portfolio["equity"] = account.get("equity", 0.0)

            # Calculate day PnL
            last_equity = account.get("last_equity", 0.0)
            current_equity = account.get("equity", 0.0)
            if last_equity > 0:
                portfolio["day_pnl"] = current_equity - last_equity
                portfolio["day_pnl_pct"] = ((current_equity / last_equity) - 1) * 100

        except AlpacaAPIError as e:
            logger.error(f"Error fetching Alpaca account: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching account: {e}")

        try:
            # Get all positions
            positions = await self.alpaca_client.get_positions(use_cache=False)

            total_unrealized_pnl = 0.0
            total_cost_basis = 0.0

            formatted_positions = []
            for pos in positions:
                unrealized_pl = pos.get("unrealized_pl", 0.0)
                total_unrealized_pnl += unrealized_pl
                total_cost_basis += pos.get("cost_basis", 0.0)

                formatted_positions.append(
                    {
                        "symbol": pos.get("symbol"),
                        "qty": pos.get("qty"),
                        "side": pos.get("side"),
                        "avg_entry_price": pos.get("avg_entry_price"),
                        "current_price": pos.get("current_price"),
                        "market_value": pos.get("market_value"),
                        "cost_basis": pos.get("cost_basis"),
                        "unrealized_pnl": unrealized_pl,
                        "unrealized_pnl_pct": pos.get("unrealized_plpc", 0.0) * 100,
                        "day_pnl": pos.get("unrealized_intraday_pl", 0.0),
                        "day_pnl_pct": pos.get("unrealized_intraday_plpc", 0.0) * 100,
                        "change_today": pos.get("change_today", 0.0) * 100,
                    }
                )

            portfolio["positions"] = formatted_positions
            portfolio["unrealized_pnl"] = total_unrealized_pnl
            if total_cost_basis > 0:
                portfolio["unrealized_pnl_pct"] = (
                    total_unrealized_pnl / total_cost_basis
                ) * 100

        except AlpacaAPIError as e:
            logger.error(f"Error fetching Alpaca positions: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching positions: {e}")

        return portfolio

    async def get_active_strategies(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all live strategies for a user with their current status.

        Queries the database for all LiveStrategy records belonging to the user,
        including related signal history for recent activity.

        Args:
            user_id: The user's ID

        Returns:
            List of strategy dictionaries with status and metrics
        """
        strategies = []

        try:
            # Query all live strategies for the user with eager loading of signals
            result = await self.db.execute(
                select(LiveStrategy)
                .where(LiveStrategy.user_id == str(user_id))
                .options(selectinload(LiveStrategy.signals))
                .order_by(LiveStrategy.created_at.desc())
            )
            live_strategies = result.scalars().all()

            for strategy in live_strategies:
                # Get recent signals count (last 24 hours)
                recent_signals = (
                    [
                        s
                        for s in strategy.signals
                        if s.timestamp
                        and (
                            datetime.now(timezone.utc)
                            - s.timestamp.replace(tzinfo=timezone.utc)
                        ).total_seconds()
                        < 86400
                    ]
                    if strategy.signals
                    else []
                )

                strategies.append(
                    {
                        "id": strategy.id,
                        "name": strategy.name,
                        "strategy_id": strategy.strategy_id,
                        "symbols": strategy.symbols,
                        "status": (
                            strategy.status.value if strategy.status else "unknown"
                        ),
                        "is_active": strategy.status == LiveStrategyStatus.ACTIVE,
                        "auto_execute": strategy.auto_execute,
                        "check_interval": strategy.check_interval,
                        "max_position_size": strategy.max_position_size,
                        "max_positions": strategy.max_positions,
                        "daily_loss_limit": strategy.daily_loss_limit,
                        "position_size_pct": strategy.position_size_pct,
                        "last_check": (
                            strategy.last_check.isoformat()
                            if strategy.last_check
                            else None
                        ),
                        "last_signal": (
                            strategy.last_signal.isoformat()
                            if strategy.last_signal
                            else None
                        ),
                        "error_message": strategy.error_message,
                        "total_signals": strategy.total_signals,
                        "executed_trades": strategy.executed_trades,
                        "current_positions": strategy.current_positions,
                        "win_rate": strategy.win_rate,
                        "total_pnl": strategy.total_pnl,
                        "recent_signals_24h": len(recent_signals),
                        "created_at": (
                            strategy.created_at.isoformat()
                            if strategy.created_at
                            else None
                        ),
                        "updated_at": (
                            strategy.updated_at.isoformat()
                            if strategy.updated_at
                            else None
                        ),
                    }
                )

        except Exception as e:
            logger.error(f"Error fetching active strategies: {e}")

        return strategies

    async def get_orders(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent orders from Alpaca broker.

        Fetches order history including open and recently filled orders.

        Args:
            user_id: The user's ID
            limit: Maximum number of orders to return (default: 100)

        Returns:
            List of order dictionaries
        """
        orders = []

        if not self.alpaca_client:
            logger.warning("Alpaca client not available")
            return orders

        try:
            # Get all recent orders (open and closed)
            raw_orders = await self.alpaca_client.get_orders(
                status="all", limit=min(limit, 500), use_cache=False
            )

            for order in raw_orders:
                orders.append(
                    {
                        "id": order.get("id"),
                        "client_order_id": order.get("client_order_id"),
                        "symbol": order.get("symbol"),
                        "side": order.get("side"),
                        "type": order.get("type"),
                        "qty": order.get("qty"),
                        "filled_qty": order.get("filled_qty"),
                        "limit_price": order.get("limit_price"),
                        "stop_price": order.get("stop_price"),
                        "filled_avg_price": order.get("filled_avg_price"),
                        "status": order.get("status"),
                        "time_in_force": order.get("time_in_force"),
                        "extended_hours": order.get("extended_hours"),
                        "created_at": order.get("created_at"),
                        "submitted_at": order.get("submitted_at"),
                        "filled_at": order.get("filled_at"),
                        "canceled_at": order.get("canceled_at"),
                        "expired_at": order.get("expired_at"),
                    }
                )

        except AlpacaAPIError as e:
            logger.error(f"Error fetching Alpaca orders: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching orders: {e}")

        return orders

    async def perform_action(
        self, user_id: int, action: str, strategy_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform a live trading action.

        Supported actions:
        - pause: Pause a specific strategy or all strategies
        - resume: Resume a specific strategy or all strategies
        - stop: Stop a specific strategy or all strategies
        - pause_all: Pause all active strategies
        - resume_all: Resume all paused strategies
        - stop_all: Stop all strategies

        Args:
            user_id: The user's ID
            action: The action to perform
            strategy_id: Optional specific strategy ID (for single strategy actions)

        Returns:
            Dictionary with success status and message
        """
        valid_actions = [
            "pause",
            "resume",
            "stop",
            "pause_all",
            "resume_all",
            "stop_all",
        ]

        if action not in valid_actions:
            return {
                "success": False,
                "error": f"Invalid action: {action}. Valid actions: {', '.join(valid_actions)}",
            }

        try:
            affected_count = 0

            if action in ["pause", "resume", "stop"] and strategy_id:
                # Single strategy action
                result = await self.db.execute(
                    select(LiveStrategy).where(
                        LiveStrategy.id == strategy_id,
                        LiveStrategy.user_id == str(user_id),
                    )
                )
                strategy = result.scalar_one_or_none()

                if not strategy:
                    return {
                        "success": False,
                        "error": f"Strategy not found: {strategy_id}",
                    }

                if action == "pause":
                    if strategy.status == LiveStrategyStatus.ACTIVE:
                        strategy.status = LiveStrategyStatus.PAUSED
                        affected_count = 1
                    else:
                        return {
                            "success": False,
                            "error": f"Strategy is not active (current status: {strategy.status.value})",
                        }

                elif action == "resume":
                    if strategy.status == LiveStrategyStatus.PAUSED:
                        strategy.status = LiveStrategyStatus.ACTIVE
                        strategy.error_message = None
                        affected_count = 1
                    else:
                        return {
                            "success": False,
                            "error": f"Strategy is not paused (current status: {strategy.status.value})",
                        }

                elif action == "stop":
                    if strategy.status != LiveStrategyStatus.STOPPED:
                        strategy.status = LiveStrategyStatus.STOPPED
                        affected_count = 1
                    else:
                        return {
                            "success": False,
                            "error": "Strategy is already stopped",
                        }

            elif action == "pause_all" or (action == "pause" and not strategy_id):
                # Pause all active strategies
                result = await self.db.execute(
                    select(LiveStrategy).where(
                        LiveStrategy.user_id == str(user_id),
                        LiveStrategy.status == LiveStrategyStatus.ACTIVE,
                    )
                )
                strategies = result.scalars().all()

                for strategy in strategies:
                    strategy.status = LiveStrategyStatus.PAUSED
                    affected_count += 1

            elif action == "resume_all" or (action == "resume" and not strategy_id):
                # Resume all paused strategies
                result = await self.db.execute(
                    select(LiveStrategy).where(
                        LiveStrategy.user_id == str(user_id),
                        LiveStrategy.status == LiveStrategyStatus.PAUSED,
                    )
                )
                strategies = result.scalars().all()

                for strategy in strategies:
                    strategy.status = LiveStrategyStatus.ACTIVE
                    strategy.error_message = None
                    affected_count += 1

            elif action == "stop_all" or (action == "stop" and not strategy_id):
                # Stop all non-stopped strategies
                result = await self.db.execute(
                    select(LiveStrategy).where(
                        LiveStrategy.user_id == str(user_id),
                        LiveStrategy.status != LiveStrategyStatus.STOPPED,
                    )
                )
                strategies = result.scalars().all()

                for strategy in strategies:
                    strategy.status = LiveStrategyStatus.STOPPED
                    affected_count += 1

            await self.db.commit()

            action_past_tense = {
                "pause": "paused",
                "resume": "resumed",
                "stop": "stopped",
                "pause_all": "paused",
                "resume_all": "resumed",
                "stop_all": "stopped",
            }

            return {
                "success": True,
                "message": f"Successfully {action_past_tense[action]} {affected_count} strategy/strategies",
                "affected_count": affected_count,
                "action": action,
            }

        except Exception as e:
            logger.error(f"Error performing action {action}: {e}")
            await self.db.rollback()
            return {"success": False, "error": f"Failed to perform action: {str(e)}"}

    async def get_strategy_by_id(
        self, user_id: int, strategy_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific live strategy by ID.

        Args:
            user_id: The user's ID
            strategy_id: The strategy ID

        Returns:
            Strategy dictionary or None if not found
        """
        try:
            result = await self.db.execute(
                select(LiveStrategy)
                .where(
                    LiveStrategy.id == strategy_id, LiveStrategy.user_id == str(user_id)
                )
                .options(selectinload(LiveStrategy.signals))
            )
            strategy = result.scalar_one_or_none()

            if strategy:
                return strategy.to_dict()
            return None

        except Exception as e:
            logger.error(f"Error fetching strategy {strategy_id}: {e}")
            return None


def get_live_trading_service(db: AsyncSession = Depends(get_db)) -> LiveTradingService:
    """
    FastAPI dependency to get LiveTradingService instance.

    Args:
        db: Database session from dependency injection

    Returns:
        LiveTradingService instance
    """
    return LiveTradingService(db)
