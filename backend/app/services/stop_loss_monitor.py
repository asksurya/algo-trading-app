"""
Stop-loss and take-profit position monitor.
Monitors paper trading positions and auto-executes sell orders when price thresholds are hit.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.paper_trading import PaperAccount, PaperPosition, PaperTrade
from app.integrations.market_data import get_market_data_service

logger = logging.getLogger(__name__)


class StopLossTakeProfitMonitor:
    """
    Monitors positions with stop-loss or take-profit levels.
    Automatically triggers sell orders when price thresholds are breached.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.market_data = get_market_data_service()

    async def check_all_positions(self) -> List[Dict[str, Any]]:
        """
        Check all positions with stop-loss or take-profit levels.
        Returns a list of triggered orders.
        """
        triggered_orders = []

        # Query all positions that have stop-loss or take-profit set
        result = await self.session.execute(
            select(PaperPosition)
            .where(
                (PaperPosition.stop_loss_price.isnot(None)) |
                (PaperPosition.take_profit_price.isnot(None))
            )
            .options(selectinload(PaperPosition.account))
        )
        positions = result.scalars().all()

        if not positions:
            logger.debug("No positions with stop-loss or take-profit levels found")
            return triggered_orders

        # Get unique symbols to fetch prices
        symbols = list(set(pos.symbol for pos in positions))

        # Fetch current prices for all symbols
        current_prices = await self._fetch_current_prices(symbols)

        # Check each position
        for position in positions:
            current_price = current_prices.get(position.symbol)
            if current_price is None:
                logger.warning(f"Could not fetch price for {position.symbol}, skipping")
                continue

            trigger_result = await self._check_position_triggers(position, current_price)
            if trigger_result:
                triggered_orders.append(trigger_result)

        return triggered_orders

    async def check_user_positions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Check positions for a specific user.
        Returns a list of triggered orders.
        """
        triggered_orders = []

        # Get user's account
        result = await self.session.execute(
            select(PaperAccount)
            .where(PaperAccount.user_id == user_id)
            .options(selectinload(PaperAccount.positions))
        )
        account = result.scalar_one_or_none()

        if not account:
            logger.debug(f"No paper account found for user {user_id}")
            return triggered_orders

        # Filter positions with stop-loss or take-profit
        positions_to_check = [
            pos for pos in account.positions
            if pos.stop_loss_price is not None or pos.take_profit_price is not None
        ]

        if not positions_to_check:
            return triggered_orders

        # Get unique symbols
        symbols = list(set(pos.symbol for pos in positions_to_check))

        # Fetch current prices
        current_prices = await self._fetch_current_prices(symbols)

        # Check each position
        for position in positions_to_check:
            current_price = current_prices.get(position.symbol)
            if current_price is None:
                continue

            trigger_result = await self._check_position_triggers(position, current_price)
            if trigger_result:
                triggered_orders.append(trigger_result)

        return triggered_orders

    async def _fetch_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Fetch current prices for a list of symbols."""
        prices = {}
        try:
            trades_data = await self.market_data.get_multi_trades(symbols)
            for trade in trades_data:
                prices[trade["symbol"]] = trade["price"]
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
        return prices

    async def _check_position_triggers(
        self,
        position: PaperPosition,
        current_price: float
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a position's stop-loss or take-profit has been triggered.
        If triggered, execute the sell order and return the result.
        """
        trigger_type = None
        trigger_price = None

        # Check stop-loss (price fell below threshold)
        if position.stop_loss_price is not None and current_price <= position.stop_loss_price:
            trigger_type = "stop_loss"
            trigger_price = position.stop_loss_price
            logger.info(
                f"STOP-LOSS triggered for {position.symbol}: "
                f"current={current_price:.2f}, stop_loss={position.stop_loss_price:.2f}"
            )

        # Check take-profit (price rose above threshold)
        elif position.take_profit_price is not None and current_price >= position.take_profit_price:
            trigger_type = "take_profit"
            trigger_price = position.take_profit_price
            logger.info(
                f"TAKE-PROFIT triggered for {position.symbol}: "
                f"current={current_price:.2f}, take_profit={position.take_profit_price:.2f}"
            )

        if trigger_type is None:
            return None

        # Execute the sell order
        return await self._execute_triggered_sell(position, current_price, trigger_type, trigger_price)

    async def _execute_triggered_sell(
        self,
        position: PaperPosition,
        execution_price: float,
        trigger_type: str,
        trigger_price: float
    ) -> Dict[str, Any]:
        """
        Execute a sell order triggered by stop-loss or take-profit.
        """
        account = position.account
        qty = position.qty
        order_value = qty * execution_price

        # Calculate realized P&L
        realized_pnl = (execution_price - position.avg_price) * qty

        # Update account cash balance and P&L
        account.cash_balance += order_value
        account.total_pnl += realized_pnl

        # Create trade record
        timestamp = datetime.utcnow()
        trade = PaperTrade(
            account_id=account.id,
            symbol=position.symbol,
            qty=qty,
            side="sell",
            price=execution_price,
            value=order_value,
            timestamp=timestamp
        )
        self.session.add(trade)

        # Store position info before deletion for the result
        position_info = {
            "symbol": position.symbol,
            "qty": qty,
            "avg_price": position.avg_price,
            "stop_loss_price": position.stop_loss_price,
            "take_profit_price": position.take_profit_price,
        }

        # Delete the position (fully closed)
        await self.session.delete(position)

        # Commit the transaction
        await self.session.commit()

        result = {
            "success": True,
            "trigger_type": trigger_type,
            "trigger_price": trigger_price,
            "execution_price": execution_price,
            "position": position_info,
            "realized_pnl": realized_pnl,
            "trade": {
                "symbol": position_info["symbol"],
                "qty": qty,
                "side": "sell",
                "price": execution_price,
                "value": order_value,
                "timestamp": timestamp.isoformat(),
            },
            "user_id": account.user_id,
        }

        logger.info(
            f"{trigger_type.upper()} order executed for {position_info['symbol']}: "
            f"sold {qty} shares at {execution_price:.2f}, P&L: {realized_pnl:.2f}"
        )

        return result


async def get_stop_loss_monitor(session: AsyncSession) -> StopLossTakeProfitMonitor:
    """Get stop-loss/take-profit monitor instance."""
    return StopLossTakeProfitMonitor(session)
