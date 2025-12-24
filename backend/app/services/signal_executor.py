"""
Signal Executor Service - Converts trading signals into actual orders.
Handles order placement, position sizing, and execution logging.
"""
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.paper_trading import get_paper_trading_service
from app.services.live_trading_service import LiveTradingService
from app.models.strategy_execution import StrategySignal, SignalType

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of signal execution."""
    success: bool
    order_id: Optional[str] = None
    error: Optional[str] = None
    dry_run: bool = False
    execution_price: Optional[float] = None
    quantity: Optional[float] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class SignalExecutor:
    """
    Executes trading signals by placing orders.
    Supports both paper trading and live trading modes.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._paper_service = None
        self._live_service = None

    @property
    def paper_service(self):
        if self._paper_service is None:
            self._paper_service = get_paper_trading_service(self.db)
        return self._paper_service

    @property
    def live_service(self):
        if self._live_service is None:
            self._live_service = LiveTradingService(self.db)
        return self._live_service

    async def execute_signal(
        self,
        signal: Dict[str, Any],
        user_id: str,
        dry_run: bool = False,
        use_paper_trading: bool = True
    ) -> ExecutionResult:
        """
        Execute a trading signal.

        Args:
            signal: Signal dict with signal_type, symbol, price, quantity
            user_id: User ID for the account
            dry_run: If True, don't actually place orders
            use_paper_trading: If True, use paper trading account

        Returns:
            ExecutionResult with order details or error
        """
        try:
            signal_type = signal.get("signal_type", "").upper()
            symbol = signal.get("symbol")
            price = signal.get("price")
            quantity = signal.get("quantity", self._calculate_position_size(signal))

            if not symbol:
                return ExecutionResult(success=False, error="No symbol in signal")

            if signal_type not in ["BUY", "SELL"]:
                logger.info(f"Signal type {signal_type} - no action needed")
                return ExecutionResult(success=True, dry_run=True)

            if dry_run:
                logger.info(f"DRY RUN: Would {signal_type} {quantity} {symbol} @ {price}")
                return ExecutionResult(
                    success=True,
                    dry_run=True,
                    quantity=quantity,
                    execution_price=price
                )

            # Execute the order
            result = await self._place_order(
                user_id=user_id,
                symbol=symbol,
                quantity=quantity,
                side=signal_type.lower(),
                use_paper=use_paper_trading
            )

            return ExecutionResult(
                success=result.get("success", False),
                order_id=result.get("order_id") or result.get("trade", {}).get("id"),
                execution_price=result.get("price") or result.get("trade", {}).get("price"),
                quantity=quantity,
                error=result.get("error")
            )

        except Exception as e:
            logger.error(f"Signal execution failed: {e}")
            return ExecutionResult(success=False, error=str(e))

    async def _place_order(
        self,
        user_id: str,
        symbol: str,
        quantity: float,
        side: str,
        use_paper: bool = True
    ) -> Dict[str, Any]:
        """Place an order through paper or live trading."""
        if use_paper:
            return await self.paper_service.execute_paper_order(
                user_id=user_id,
                symbol=symbol,
                qty=quantity,
                side=side,
                order_type="market"
            )
        else:
            return await self.live_service.execute_order(
                user_id=user_id,
                symbol=symbol,
                qty=quantity,
                side=side,
                order_type="market"
            )

    def _calculate_position_size(self, signal: Dict[str, Any]) -> float:
        """Calculate position size based on signal strength and risk parameters."""
        # Default to 10 shares if not specified
        base_qty = signal.get("quantity", 10)
        strength = signal.get("strength", 1.0)

        # Scale by signal strength (0.5 to 1.0 multiplier)
        adjusted_qty = int(base_qty * max(0.5, min(1.0, strength)))
        return max(1, adjusted_qty)


def get_signal_executor(db: AsyncSession) -> SignalExecutor:
    """Get signal executor instance."""
    return SignalExecutor(db)
