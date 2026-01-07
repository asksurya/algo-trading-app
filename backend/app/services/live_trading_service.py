"""
Live Trading Service - Connects to paper trading or live broker.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.services.paper_trading import PaperTradingService, get_paper_trading_service
from app.integrations.alpaca_client import get_alpaca_client, AlpacaAPIError
from app.models.live_strategy import LiveStrategy
from app.models.strategy import Strategy
from app.models.enums import LiveStrategyStatus
from app.models.notification import NotificationType, NotificationPriority
from app.schemas.live_trading import LiveStrategyCreate, LiveStrategyUpdate, QuickDeployRequest
from app.services.notification_service import NotificationService
from datetime import timezone
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class LiveTradingService:
    """
    Service for live trading operations.
    Integrates with paper trading for simulation and Alpaca for real trading.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._paper_service: Optional[PaperTradingService] = None
        self._notification_service: Optional[NotificationService] = None

    @property
    def paper_service(self) -> PaperTradingService:
        """Lazy-load paper trading service."""
        if self._paper_service is None:
            self._paper_service = get_paper_trading_service(self.db)
        return self._paper_service

    @property
    def notification_service(self) -> NotificationService:
        """Lazy-load notification service."""
        if self._notification_service is None:
            self._notification_service = NotificationService(self.db)
        return self._notification_service

    # ========================================================================
    # Live Strategy CRUD Operations
    # ========================================================================

    async def create_live_strategy(
        self,
        user_id: str,
        strategy_data: LiveStrategyCreate
    ) -> LiveStrategy:
        """
        Create a new live trading strategy.

        Args:
            user_id: User ID who owns the strategy
            strategy_data: Strategy configuration

        Returns:
            Created LiveStrategy instance
        """
        try:
            # Create new live strategy with STOPPED status
            live_strategy = LiveStrategy(
                user_id=user_id,
                strategy_id=strategy_data.strategy_id,
                name=strategy_data.name,
                symbols=strategy_data.symbols,
                status=LiveStrategyStatus.STOPPED,
                check_interval=strategy_data.check_interval,
                auto_execute=strategy_data.auto_execute,
                max_positions=strategy_data.max_positions,
                daily_loss_limit=strategy_data.daily_loss_limit,
                position_size_pct=strategy_data.position_size_pct,
                max_position_size=strategy_data.max_position_size,
            )

            self.db.add(live_strategy)
            await self.db.commit()
            await self.db.refresh(live_strategy)

            logger.info(f"Created live strategy {live_strategy.id} for user {user_id}")
            return live_strategy

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating live strategy for user {user_id}: {e}")
            raise

    async def get_live_strategies(self, user_id: str) -> List[LiveStrategy]:
        """
        Get all live strategies for a user.

        Args:
            user_id: User ID

        Returns:
            List of LiveStrategy instances
        """
        try:
            result = await self.db.execute(
                select(LiveStrategy)
                .where(LiveStrategy.user_id == user_id)
                .order_by(LiveStrategy.created_at.desc())
            )
            strategies = result.scalars().all()
            return list(strategies)

        except Exception as e:
            logger.error(f"Error getting live strategies for user {user_id}: {e}")
            raise

    async def get_live_strategy(self, strategy_id: str, user_id: str) -> Optional[LiveStrategy]:
        """
        Get a specific live strategy by ID.

        Args:
            strategy_id: Strategy ID
            user_id: User ID (for authorization)

        Returns:
            LiveStrategy instance or None
        """
        try:
            result = await self.db.execute(
                select(LiveStrategy)
                .where(LiveStrategy.id == strategy_id)
                .where(LiveStrategy.user_id == user_id)
            )
            strategy = result.scalar_one_or_none()
            return strategy

        except Exception as e:
            logger.error(f"Error getting live strategy {strategy_id}: {e}")
            raise

    async def update_live_strategy(
        self,
        strategy_id: str,
        user_id: str,
        strategy_data: LiveStrategyUpdate
    ) -> Optional[LiveStrategy]:
        """
        Update an existing live strategy.

        Args:
            strategy_id: Strategy ID
            user_id: User ID (for authorization)
            strategy_data: Updated strategy data

        Returns:
            Updated LiveStrategy instance or None
        """
        try:
            # Get existing strategy
            strategy = await self.get_live_strategy(strategy_id, user_id)
            if not strategy:
                return None

            # Update fields that were provided
            update_data = strategy_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(strategy, field, value)

            await self.db.commit()
            await self.db.refresh(strategy)

            logger.info(f"Updated live strategy {strategy_id}")
            return strategy

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating live strategy {strategy_id}: {e}")
            raise

    async def delete_live_strategy(self, strategy_id: str, user_id: str) -> bool:
        """
        Delete a live strategy.

        Args:
            strategy_id: Strategy ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted, False if not found
        """
        try:
            strategy = await self.get_live_strategy(strategy_id, user_id)
            if not strategy:
                return False

            await self.db.delete(strategy)
            await self.db.commit()

            logger.info(f"Deleted live strategy {strategy_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting live strategy {strategy_id}: {e}")
            raise

    async def quick_deploy(
        self,
        user_id: str,
        request: QuickDeployRequest
    ) -> LiveStrategy:
        """
        Quick deploy a strategy to live trading with sensible defaults.
        Creates the LiveStrategy and immediately activates it.

        Args:
            user_id: User ID who owns the strategy
            request: Quick deploy request with strategy ID and symbols

        Returns:
            Created and activated LiveStrategy instance
        """
        try:
            # 1. Get the base strategy
            result = await self.db.execute(
                select(Strategy).where(Strategy.id == request.strategy_id)
            )
            strategy = result.scalar_one_or_none()
            if not strategy:
                raise HTTPException(status_code=404, detail="Strategy not found")

            # 2. Generate name if not provided
            name = request.name or f"Live - {strategy.name}"

            # 3. Create LiveStrategy record
            live_strategy = LiveStrategy(
                user_id=user_id,
                strategy_id=request.strategy_id,
                name=name,
                symbols=request.symbols,
                status=LiveStrategyStatus.ACTIVE,  # Start immediately
                check_interval=request.check_interval,
                auto_execute=request.auto_execute,
                max_positions=request.max_positions,
                position_size_pct=request.position_size_pct,
                max_position_size=request.max_position_size,
                daily_loss_limit=request.daily_loss_limit,
                state={},
            )

            self.db.add(live_strategy)
            await self.db.commit()
            await self.db.refresh(live_strategy)

            # 4. Send notification
            await self.notification_service.create_notification(
                user_id=user_id,
                notification_type=NotificationType.SYSTEM_ALERT,
                title=f"Live Trading Activated: {name}",
                message=f"Strategy deployed with auto-execute enabled. Monitoring {len(request.symbols)} symbols.",
                priority=NotificationPriority.HIGH
            )

            logger.info(f"Quick deployed live strategy {live_strategy.id} for user {user_id}")
            return live_strategy

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error quick deploying strategy for user {user_id}: {e}")
            raise

    # ========================================================================
    # Live Strategy Lifecycle Operations
    # ========================================================================

    async def start_strategy(self, strategy_id: str, user_id: str) -> Optional[LiveStrategy]:
        """
        Start a live trading strategy.

        Args:
            strategy_id: Strategy ID
            user_id: User ID (for authorization)

        Returns:
            Updated LiveStrategy instance or None
        """
        try:
            strategy = await self.get_live_strategy(strategy_id, user_id)
            if not strategy:
                return None

            strategy.status = LiveStrategyStatus.ACTIVE
            strategy.error_message = None

            await self.db.commit()
            await self.db.refresh(strategy)

            logger.info(f"Started live strategy {strategy_id}")
            return strategy

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error starting live strategy {strategy_id}: {e}")
            raise

    async def stop_strategy(self, strategy_id: str, user_id: str) -> Optional[LiveStrategy]:
        """
        Stop a live trading strategy.

        Args:
            strategy_id: Strategy ID
            user_id: User ID (for authorization)

        Returns:
            Updated LiveStrategy instance or None
        """
        try:
            strategy = await self.get_live_strategy(strategy_id, user_id)
            if not strategy:
                return None

            strategy.status = LiveStrategyStatus.STOPPED

            await self.db.commit()
            await self.db.refresh(strategy)

            logger.info(f"Stopped live strategy {strategy_id}")
            return strategy

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error stopping live strategy {strategy_id}: {e}")
            raise

    async def pause_strategy(self, strategy_id: str, user_id: str) -> Optional[LiveStrategy]:
        """
        Pause a live trading strategy.

        Args:
            strategy_id: Strategy ID
            user_id: User ID (for authorization)

        Returns:
            Updated LiveStrategy instance or None
        """
        try:
            strategy = await self.get_live_strategy(strategy_id, user_id)
            if not strategy:
                return None

            strategy.status = LiveStrategyStatus.PAUSED

            await self.db.commit()
            await self.db.refresh(strategy)

            logger.info(f"Paused live strategy {strategy_id}")
            return strategy

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error pausing live strategy {strategy_id}: {e}")
            raise

    # ========================================================================
    # System Status & Portfolio Operations
    # ========================================================================

    async def get_system_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get the overall status of the live trading system.

        Returns system health, active strategies count, and P&L summary.
        """
        try:
            # Get paper trading account for P&L data
            account = await self.paper_service.get_paper_account(user_id)

            # Get active live strategies count
            result = await self.db.execute(
                select(LiveStrategy)
                .where(LiveStrategy.user_id == user_id)
                .where(LiveStrategy.status == LiveStrategyStatus.ACTIVE)
            )
            active_strategies = result.scalars().all()

            # Get last trade timestamp
            last_trade_at = None
            if account and account.get("trades"):
                trades = account.get("trades", [])
                if trades:
                    last_trade_at = trades[-1].get("timestamp")

            return {
                "is_running": len(active_strategies) > 0,
                "active_strategies": len(active_strategies),
                "total_pnl": account.get("total_pnl", 0) if account else 0,
                "unrealized_pnl": account.get("unrealized_pnl", 0) if account else 0,
                "total_equity": account.get("total_equity", 0) if account else 0,
                "last_trade_at": last_trade_at,
                "paper_trading_mode": True,
            }

        except Exception as e:
            logger.error(f"Error getting system status for user {user_id}: {e}")
            return {
                "is_running": False,
                "active_strategies": 0,
                "total_pnl": 0,
                "unrealized_pnl": 0,
                "total_equity": 0,
                "last_trade_at": None,
                "paper_trading_mode": True,
                "error": str(e)
            }

    async def get_portfolio(self, user_id: str) -> Dict[str, Any]:
        """
        Get the current live trading portfolio.

        Returns positions, cash balance, and overall portfolio value.
        """
        try:
            account = await self.paper_service.get_paper_account(user_id)

            if not account:
                return {
                    "total_value": 0,
                    "cash": 0,
                    "positions": [],
                    "paper_trading_mode": True
                }

            # Convert positions dict to list format
            positions_list = []
            for symbol, pos_data in account.get("positions", {}).items():
                positions_list.append({
                    "symbol": symbol,
                    "qty": pos_data.get("qty", 0),
                    "avg_price": pos_data.get("avg_price", 0),
                    "current_price": pos_data.get("current_price", 0),
                    "market_value": pos_data.get("market_value", 0),
                    "unrealized_pnl": pos_data.get("unrealized_pnl", 0),
                })

            return {
                "total_value": account.get("total_equity", 0),
                "cash": account.get("cash_balance", 0),
                "buying_power": account.get("cash_balance", 0),
                "positions": positions_list,
                "positions_count": len(positions_list),
                "total_pnl": account.get("total_pnl", 0),
                "total_return_pct": account.get("total_return_pct", 0),
                "paper_trading_mode": True
            }

        except Exception as e:
            logger.error(f"Error getting portfolio for user {user_id}: {e}")
            return {
                "total_value": 0,
                "cash": 0,
                "positions": [],
                "paper_trading_mode": True,
                "error": str(e)
            }

    async def perform_action(self, user_id: str, action: str) -> Dict[str, Any]:
        """
        Perform a live trading action (e.g., pause, resume, reset).
        """
        try:
            if action == "reset":
                account = await self.paper_service.reset_paper_account(user_id)
                return {
                    "success": True,
                    "action": "reset",
                    "message": "Paper trading account has been reset",
                    "account": account
                }
            elif action == "pause":
                # Pause all active strategies for this user
                result = await self.db.execute(
                    select(LiveStrategy)
                    .where(LiveStrategy.user_id == user_id)
                    .where(LiveStrategy.status == LiveStrategyStatus.ACTIVE)
                )
                strategies = result.scalars().all()
                for strategy in strategies:
                    strategy.status = LiveStrategyStatus.PAUSED
                await self.db.commit()

                return {
                    "success": True,
                    "action": "pause",
                    "message": f"Paused {len(strategies)} active strategies"
                }
            elif action == "resume":
                # Resume paused strategies
                result = await self.db.execute(
                    select(LiveStrategy)
                    .where(LiveStrategy.user_id == user_id)
                    .where(LiveStrategy.status == LiveStrategyStatus.PAUSED)
                )
                strategies = result.scalars().all()
                for strategy in strategies:
                    strategy.status = LiveStrategyStatus.ACTIVE
                await self.db.commit()

                return {
                    "success": True,
                    "action": "resume",
                    "message": f"Resumed {len(strategies)} strategies"
                }
            else:
                return {
                    "success": False,
                    "action": action,
                    "message": f"Unknown action: {action}"
                }

        except Exception as e:
            logger.error(f"Error performing action {action} for user {user_id}: {e}")
            return {
                "success": False,
                "action": action,
                "error": str(e)
            }

    async def get_active_strategies(self, user_id: str) -> List[str]:
        """
        Get a list of currently active strategies in live trading.

        Returns list of strategy IDs.
        """
        try:
            result = await self.db.execute(
                select(LiveStrategy.strategy_id)
                .where(LiveStrategy.user_id == user_id)
                .where(LiveStrategy.status == LiveStrategyStatus.ACTIVE)
            )
            strategy_ids = result.scalars().all()
            return [str(sid) for sid in strategy_ids]

        except Exception as e:
            logger.error(f"Error getting active strategies for user {user_id}: {e}")
            return []

    async def get_orders(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get a list of recent live trading orders.

        For paper trading, returns trade history as orders.
        """
        try:
            trades = await self.paper_service.get_paper_trade_history(user_id, limit=limit)

            # Format trades as orders for compatibility
            orders = []
            for trade in trades:
                orders.append({
                    "id": f"paper_{trade.get('timestamp', '')}",
                    "symbol": trade.get("symbol"),
                    "side": trade.get("side"),
                    "qty": trade.get("qty"),
                    "filled_qty": trade.get("qty"),
                    "type": "market",
                    "status": "filled",
                    "filled_avg_price": trade.get("price"),
                    "submitted_at": trade.get("timestamp"),
                    "filled_at": trade.get("timestamp"),
                    "paper_trading": True
                })

            return orders

        except Exception as e:
            logger.error(f"Error getting orders for user {user_id}: {e}")
            return []

    async def execute_order(
        self,
        user_id: str,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = "market",
        limit_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute a trading order through paper trading.
        """
        try:
            result = await self.paper_service.execute_paper_order(
                user_id=user_id,
                symbol=symbol.upper(),
                qty=qty,
                side=side.lower(),
                order_type=order_type,
                limit_price=limit_price
            )
            return result

        except Exception as e:
            logger.error(f"Error executing order for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }


def get_live_trading_service(db: AsyncSession = Depends(get_db)) -> LiveTradingService:
    """Get live trading service instance."""
    return LiveTradingService(db)
