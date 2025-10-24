"""
Order execution service with validation and error handling.
Provides order placement, modification, and cancellation via Alpaca.
"""
import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    StopOrderRequest,
    StopLimitOrderRequest,
    TrailingStopOrderRequest,
    OrderRequest as AlpacaOrderRequest,
    ReplaceOrderRequest,
    ClosePositionRequest,
)
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce, OrderClass
from alpaca.common.exceptions import APIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations.alpaca_client import get_alpaca_client
from app.services.risk_manager import RiskManager
from app.services.notification_service import NotificationService
from app.models.notification import NotificationType

logger = logging.getLogger(__name__)


class OrderExecutionError(Exception):
    """Custom exception for order execution errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, original_error: Optional[Exception] = None):
        self.message = message
        self.status_code = status_code
        self.original_error = original_error
        super().__init__(self.message)


class OrderExecutor(ABC):
    """
    Abstract base class for order execution.
    Defines interface for placing, modifying, and canceling orders.
    """
    
    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        order_type: OrderType,
        time_in_force: TimeInForce = TimeInForce.DAY,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        extended_hours: bool = False,
    ) -> Dict[str, Any]:
        """
        Place a new order.
        
        Args:
            symbol: Stock symbol
            qty: Quantity to buy/sell
            side: Buy or sell
            order_type: Market, limit, stop, or stop_limit
            time_in_force: Order duration
            limit_price: Limit price (required for limit/stop_limit orders)
            stop_price: Stop price (required for stop/stop_limit orders)
            extended_hours: Allow extended hours trading
            
        Returns:
            Order confirmation with order ID and status
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if canceled successfully
        """
        pass
    
    @abstractmethod
    async def replace_order(
        self,
        order_id: str,
        qty: Optional[float] = None,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: Optional[TimeInForce] = None,
    ) -> Dict[str, Any]:
        """
        Replace/modify an existing order.
        
        Args:
            order_id: Order ID to replace
            qty: New quantity
            limit_price: New limit price
            stop_price: New stop price
            time_in_force: New time in force
            
        Returns:
            Updated order details
        """
        pass
    
    @abstractmethod
    async def cancel_all_orders(self) -> int:
        """
        Cancel all open orders.
        
        Returns:
            Number of orders canceled
        """
        pass
    
    @abstractmethod
    async def close_position(self, symbol: str) -> Dict[str, Any]:
        """
        Close an open position (market order for full quantity).
        
        Args:
            symbol: Symbol to close position for
            
        Returns:
            Order details for closing order
        """
        pass
    
    @abstractmethod
    async def close_all_positions(self) -> int:
        """
        Close all open positions.
        
        Returns:
            Number of positions closed
        """
        pass


class AlpacaOrderExecutor(OrderExecutor):
    """
    Alpaca order execution implementation with validation and error handling.
    Includes risk management integration.
    """
    
    _instance: Optional['AlpacaOrderExecutor'] = None
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Alpaca order executor."""
        self._alpaca_client = get_alpaca_client()
        self._db_session: Optional[AsyncSession] = None
        logger.info("AlpacaOrderExecutor initialized")
    
    def set_db_session(self, db: AsyncSession):
        """Set database session for risk checks."""
        self._db_session = db
    
    def _handle_error(self, error: Exception, operation: str) -> None:
        """Centralized error handling for order operations."""
        if isinstance(error, APIError):
            status_code = getattr(error, 'status_code', None)
            message = str(error)
            logger.error(f"Alpaca API error in {operation}: {message} (status: {status_code})")
            raise OrderExecutionError(f"API error in {operation}: {message}", status_code=status_code, original_error=error)
        else:
            logger.error(f"Unexpected error in {operation}: {str(error)}")
            raise OrderExecutionError(f"Unexpected error in {operation}: {str(error)}", original_error=error)
    
    async def place_order(
        self,
        symbol: str,
        qty: Optional[float] = None,
        notional: Optional[float] = None,
        side: str = "buy",
        order_type: str = "market",
        time_in_force: str = "day",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        trail_price: Optional[float] = None,
        trail_percent: Optional[float] = None,
        extended_hours: bool = False,
        client_order_id: Optional[str] = None,
        user_id: Optional[int] = None,
        strategy_id: Optional[int] = None,
        skip_risk_check: bool = False,
    ) -> Dict[str, Any]:
        """
        Place a new order with comprehensive validation and risk checks.
        
        Args:
            symbol: Stock symbol
            qty: Quantity (for share-based orders)
            notional: Dollar amount (for notional orders)
            side: "buy" or "sell"
            order_type: "market", "limit", "stop", "stop_limit", "trailing_stop"
            time_in_force: "day", "gtc", "ioc", "fok", "opg", "cls"
            limit_price: Limit price (required for limit orders)
            stop_price: Stop price (required for stop orders)
            trail_price: Trail amount for trailing stop
            trail_percent: Trail percentage for trailing stop
            extended_hours: Allow extended hours trading
            client_order_id: Client-specified order ID
            user_id: User ID for risk checks
            strategy_id: Strategy ID for risk checks
            skip_risk_check: Skip risk evaluation (use with caution)
            
        Returns:
            Order details dictionary
        """
        try:
            # Risk check integration
            if not skip_risk_check and user_id and self._db_session:
                await self._evaluate_risk_rules(
                    user_id=user_id,
                    strategy_id=strategy_id,
                    symbol=symbol,
                    qty=qty,
                    notional=notional,
                    side=side,
                    limit_price=limit_price
                )
            # Validate inputs
            if qty is None and notional is None:
                raise OrderExecutionError("Either qty or notional must be provided")
            
            # Convert string enums
            alpaca_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
            alpaca_tif = TimeInForce[time_in_force.upper()]
            
            # Build order request based on type
            order_data = {
                "symbol": symbol,
                "side": alpaca_side,
                "time_in_force": alpaca_tif,
                "extended_hours": extended_hours,
            }
            
            if qty is not None:
                order_data["qty"] = qty
            if notional is not None:
                order_data["notional"] = notional
            if client_order_id:
                order_data["client_order_id"] = client_order_id
            
            # Create appropriate order request
            if order_type.lower() == "market":
                order_request = MarketOrderRequest(**order_data)
            elif order_type.lower() == "limit":
                if limit_price is None:
                    raise OrderExecutionError("limit_price required for limit orders")
                order_request = LimitOrderRequest(**order_data, limit_price=limit_price)
            elif order_type.lower() == "stop":
                if stop_price is None:
                    raise OrderExecutionError("stop_price required for stop orders")
                order_request = StopOrderRequest(**order_data, stop_price=stop_price)
            elif order_type.lower() == "stop_limit":
                if limit_price is None or stop_price is None:
                    raise OrderExecutionError("limit_price and stop_price required for stop_limit orders")
                order_request = StopLimitOrderRequest(**order_data, limit_price=limit_price, stop_price=stop_price)
            elif order_type.lower() == "trailing_stop":
                trail_data = order_data.copy()
                if trail_price:
                    trail_data["trail_price"] = trail_price
                if trail_percent:
                    trail_data["trail_percent"] = trail_percent
                order_request = TrailingStopOrderRequest(**trail_data)
            else:
                raise OrderExecutionError(f"Invalid order type: {order_type}")
            
            # Submit order via Alpaca client
            order = self._alpaca_client._client.submit_order(order_request)
            
            # Convert to dict
            order_dict = self._order_to_dict(order)
            
            logger.info(f"Order placed successfully: {order.id} for {symbol}")
            
            # Send notification if user_id provided
            if user_id and self._db_session:
                await self._send_order_notification(user_id, order_dict, "placed")
            
            return order_dict
            
        except OrderExecutionError:
            raise
        except Exception as e:
            self._handle_error(e, "place_order")
    
    async def _evaluate_risk_rules(
        self,
        user_id: int,
        strategy_id: Optional[int],
        symbol: str,
        qty: Optional[float],
        notional: Optional[float],
        side: str,
        limit_price: Optional[float]
    ):
        """
        Evaluate risk rules before placing order.
        Raises OrderExecutionError if any blocking rules are breached.
        """
        try:
            risk_manager = RiskManager(self._db_session, self._alpaca_client)
            
            # Calculate order value
            order_value = notional
            if order_value is None and qty:
                # Get current price if not provided
                if limit_price:
                    order_value = qty * limit_price
                else:
                    # Get latest trade price
                    try:
                        latest_trade = self._alpaca_client.get_latest_trade(symbol)
                        order_value = qty * float(latest_trade.price)
                    except Exception:
                        logger.warning(f"Could not get price for {symbol}, skipping value-based risk checks")
                        order_value = None
            
            # Evaluate rules
            breaches = await risk_manager.evaluate_rules(
                user_id=user_id,
                strategy_id=strategy_id,
                symbol=symbol,
                order_qty=qty,
                order_value=order_value
            )
            
            # Check for blocking breaches
            blocking_breaches = [b for b in breaches if b.action == "BLOCK"]
            if blocking_breaches:
                breach_messages = [b.message for b in blocking_breaches]
                error_msg = f"Order blocked by risk rules: {'; '.join(breach_messages)}"
                logger.warning(error_msg)
                
                # Send risk breach notification
                notification_service = NotificationService(self._db_session)
                await notification_service.notify_risk_breach(
                    user_id=user_id,
                    breach_data={
                        "symbol": symbol,
                        "rule_breaches": [
                            {
                                "rule_name": b.rule_name,
                                "message": b.message,
                                "threshold": float(b.threshold),
                                "current_value": float(b.current_value)
                            }
                            for b in blocking_breaches
                        ]
                    }
                )
                
                raise OrderExecutionError(error_msg, status_code=403)
            
            # Log warnings for non-blocking breaches
            warning_breaches = [b for b in breaches if b.action == "WARN"]
            if warning_breaches:
                for breach in warning_breaches:
                    logger.warning(f"Risk warning: {breach.message}")
                
                # Send warning notification
                notification_service = NotificationService(self._db_session)
                await notification_service.notify_risk_breach(
                    user_id=user_id,
                    breach_data={
                        "symbol": symbol,
                        "rule_breaches": [
                            {
                                "rule_name": b.rule_name,
                                "message": b.message,
                                "threshold": float(b.threshold),
                                "current_value": float(b.current_value)
                            }
                            for b in warning_breaches
                        ],
                        "action": "WARNING"
                    }
                )
        
        except OrderExecutionError:
            raise
        except Exception as e:
            logger.error(f"Error evaluating risk rules: {str(e)}")
            # Don't block order on risk check errors, just log
    
    async def _send_order_notification(self, user_id: int, order_dict: Dict[str, Any], action: str):
        """Send notification about order action."""
        try:
            notification_service = NotificationService(self._db_session)
            
            if action == "placed":
                await notification_service.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.ORDER_FILLED,
                    title=f"Order Placed: {order_dict['symbol']}",
                    message=f"{order_dict['side'].upper()} {order_dict['qty']} shares of {order_dict['symbol']} at {order_dict['order_type']}",
                    priority="MEDIUM",
                    data=order_dict
                )
        except Exception as e:
            logger.error(f"Error sending order notification: {str(e)}")
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        try:
            self._alpaca_client._client.cancel_order_by_id(order_id)
            logger.info(f"Order canceled: {order_id}")
            return True
        except Exception as e:
            self._handle_error(e, "cancel_order")
    
    async def replace_order(
        self,
        order_id: str,
        qty: Optional[float] = None,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        trail: Optional[float] = None,
        time_in_force: Optional[str] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Replace/modify an existing order."""
        try:
            replace_data = {}
            if qty is not None:
                replace_data["qty"] = qty
            if limit_price is not None:
                replace_data["limit_price"] = limit_price
            if stop_price is not None:
                replace_data["stop_price"] = stop_price
            if trail is not None:
                replace_data["trail"] = trail
            if time_in_force is not None:
                replace_data["time_in_force"] = TimeInForce[time_in_force.upper()]
            if client_order_id is not None:
                replace_data["client_order_id"] = client_order_id
            
            request = ReplaceOrderRequest(**replace_data)
            order = self._alpaca_client._client.replace_order_by_id(order_id, request)
            
            logger.info(f"Order replaced: {order_id}")
            return self._order_to_dict(order)
            
        except Exception as e:
            self._handle_error(e, "replace_order")
    
    async def cancel_all_orders(self) -> int:
        """Cancel all open orders."""
        try:
            result = self._alpaca_client._client.cancel_orders()
            count = len(result) if result else 0
            logger.info(f"Canceled {count} orders")
            return count
        except Exception as e:
            self._handle_error(e, "cancel_all_orders")
    
    async def close_position(
        self,
        symbol: str,
        qty: Optional[float] = None,
        percentage: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Close an open position."""
        try:
            close_data = {}
            if qty is not None:
                close_data["qty"] = str(qty)
            if percentage is not None:
                close_data["percentage"] = str(percentage)
            
            request = ClosePositionRequest(**close_data) if close_data else None
            order = self._alpaca_client._client.close_position(symbol, close_options=request)
            
            logger.info(f"Position closed for {symbol}")
            return self._order_to_dict(order)
            
        except Exception as e:
            self._handle_error(e, "close_position")
    
    async def close_all_positions(self, cancel_orders: bool = True) -> int:
        """Close all open positions."""
        try:
            result = self._alpaca_client._client.close_all_positions(cancel_orders=cancel_orders)
            count = len(result) if result else 0
            logger.info(f"Closed {count} positions")
            return count
        except Exception as e:
            self._handle_error(e, "close_all_positions")
    
    async def place_bracket_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        take_profit_limit_price: float,
        stop_loss_stop_price: float,
        entry_limit_price: Optional[float] = None,
        time_in_force: str = "gtc",
        extended_hours: bool = False,
    ) -> Dict[str, Any]:
        """
        Place a bracket order (entry + take profit + stop loss).
        
        Args:
            symbol: Stock symbol
            qty: Quantity
            side: "buy" or "sell"
            take_profit_limit_price: Take profit limit price
            stop_loss_stop_price: Stop loss stop price
            entry_limit_price: Entry limit price (None for market entry)
            time_in_force: Order duration
            extended_hours: Allow extended hours
            
        Returns:
            Parent order details
        """
        try:
            alpaca_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
            alpaca_tif = TimeInForce[time_in_force.upper()]
            
            order_data = {
                "symbol": symbol,
                "qty": qty,
                "side": alpaca_side,
                "time_in_force": alpaca_tif,
                "order_class": OrderClass.BRACKET,
                "take_profit": {"limit_price": take_profit_limit_price},
                "stop_loss": {"stop_price": stop_loss_stop_price},
                "extended_hours": extended_hours,
            }
            
            if entry_limit_price:
                order_request = LimitOrderRequest(**order_data, limit_price=entry_limit_price)
            else:
                order_request = MarketOrderRequest(**order_data)
            
            order = self._alpaca_client._client.submit_order(order_request)
            
            logger.info(f"Bracket order placed for {symbol}")
            return self._order_to_dict(order)
            
        except Exception as e:
            self._handle_error(e, "place_bracket_order")
    
    def _order_to_dict(self, order) -> Dict[str, Any]:
        """Convert Alpaca order object to dictionary."""
        return {
            "id": str(order.id),
            "client_order_id": order.client_order_id,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
            "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None,
            "filled_at": order.filled_at.isoformat() if order.filled_at else None,
            "expired_at": order.expired_at.isoformat() if order.expired_at else None,
            "canceled_at": order.canceled_at.isoformat() if order.canceled_at else None,
            "failed_at": order.failed_at.isoformat() if order.failed_at else None,
            "replaced_at": order.replaced_at.isoformat() if order.replaced_at else None,
            "replaced_by": str(order.replaced_by) if order.replaced_by else None,
            "replaces": str(order.replaces) if order.replaces else None,
            "asset_id": str(order.asset_id),
            "symbol": order.symbol,
            "asset_class": order.asset_class.value,
            "notional": float(order.notional) if order.notional else None,
            "qty": float(order.qty) if order.qty else None,
            "filled_qty": float(order.filled_qty),
            "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
            "order_type": order.type.value,
            "side": order.side.value,
            "time_in_force": order.time_in_force.value,
            "limit_price": float(order.limit_price) if order.limit_price else None,
            "stop_price": float(order.stop_price) if order.stop_price else None,
            "status": order.status.value,
            "extended_hours": order.extended_hours,
            "legs": [],  # TODO: Handle multi-leg orders
            "trail_percent": float(order.trail_percent) if hasattr(order, 'trail_percent') and order.trail_percent else None,
            "trail_price": float(order.trail_price) if hasattr(order, 'trail_price') and order.trail_price else None,
            "hwm": float(order.hwm) if hasattr(order, 'hwm') and order.hwm else None,
        }


# Global instance getter
_order_executor: Optional[AlpacaOrderExecutor] = None


def get_order_executor() -> AlpacaOrderExecutor:
    """
    Get or create singleton order executor instance.
    
    Returns:
        AlpacaOrderExecutor instance
    """
    global _order_executor
    if _order_executor is None:
        _order_executor = AlpacaOrderExecutor()
    return _order_executor
