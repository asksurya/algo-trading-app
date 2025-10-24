"""
Order validation service.
Validates order parameters before submission to prevent errors and provide better feedback.
"""
import logging
from datetime import datetime, time
from typing import Optional, Dict, Any
from decimal import Decimal

from app.integrations.alpaca_client import get_alpaca_client

logger = logging.getLogger(__name__)


class OrderValidationError(Exception):
    """Custom exception for order validation errors."""
    pass


class OrderValidator:
    """
    Service for validating order parameters before submission.
    """
    
    def __init__(self):
        """Initialize order validator."""
        self.alpaca_client = get_alpaca_client()
    
    async def validate_order(
        self,
        symbol: str,
        qty: Optional[float] = None,
        notional: Optional[float] = None,
        side: str = "buy",
        order_type: str = "market",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        trail_price: Optional[float] = None,
        trail_percent: Optional[float] = None,
        extended_hours: bool = False,
    ) -> Dict[str, Any]:
        """
        Validate all order parameters comprehensively.
        
        Args:
            symbol: Stock symbol
            qty: Quantity
            notional: Dollar amount
            side: Buy or sell
            order_type: Order type
            limit_price: Limit price
            stop_price: Stop price
            trail_price: Trail price
            trail_percent: Trail percent
            extended_hours: Extended hours flag
            
        Returns:
            Validation result dictionary with warnings and recommendations
            
        Raises:
            OrderValidationError: If order is invalid
        """
        warnings = []
        recommendations = []
        
        try:
            # 1. Validate quantity/notional
            self._validate_quantity(qty, notional)
            
            # 2. Validate symbol
            await self._validate_symbol(symbol)
            
            # 3. Validate side
            self._validate_side(side)
            
            # 4. Validate order type and prices
            self._validate_order_type_and_prices(
                order_type, limit_price, stop_price, trail_price, trail_percent
            )
            
            # 5. Validate market hours
            market_hours_warning = self._validate_market_hours(extended_hours)
            if market_hours_warning:
                warnings.append(market_hours_warning)
            
            # 6. Validate buying power (for buy orders)
            if side.lower() == "buy":
                buying_power_warning = await self._validate_buying_power(
                    symbol, qty, notional, order_type, limit_price
                )
                if buying_power_warning:
                    warnings.append(buying_power_warning)
            
            # 7. Validate price reasonability
            price_warning = await self._validate_price_reasonability(
                symbol, order_type, limit_price, stop_price
            )
            if price_warning:
                warnings.append(price_warning)
            
            # 8. Check for pattern day trader status
            pdt_warning = await self._check_pattern_day_trader()
            if pdt_warning:
                warnings.append(pdt_warning)
            
            # 9. Generate recommendations
            recommendations = self._generate_recommendations(
                symbol, qty, order_type, limit_price, stop_price, trail_percent
            )
            
            return {
                "valid": True,
                "warnings": warnings,
                "recommendations": recommendations,
            }
            
        except OrderValidationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during validation: {e}")
            raise OrderValidationError(f"Validation error: {str(e)}")
    
    def _validate_quantity(self, qty: Optional[float], notional: Optional[float]) -> None:
        """Validate quantity or notional."""
        if qty is None and notional is None:
            raise OrderValidationError("Either qty or notional must be provided")
        
        if qty is not None and qty <= 0:
            raise OrderValidationError("Quantity must be positive")
        
        if notional is not None and notional <= 0:
            raise OrderValidationError("Notional amount must be positive")
        
        if qty is not None and notional is not None:
            raise OrderValidationError("Cannot specify both qty and notional")
    
    async def _validate_symbol(self, symbol: str) -> None:
        """Validate symbol exists and is tradable."""
        if not symbol or len(symbol) > 10:
            raise OrderValidationError("Invalid symbol format")
        
        # In production, we would check if symbol exists and is tradable
        # For now, just validate format
        if not symbol.isalpha():
            raise OrderValidationError("Symbol must contain only letters")
    
    def _validate_side(self, side: str) -> None:
        """Validate order side."""
        if side.lower() not in ["buy", "sell"]:
            raise OrderValidationError("Side must be 'buy' or 'sell'")
    
    def _validate_order_type_and_prices(
        self,
        order_type: str,
        limit_price: Optional[float],
        stop_price: Optional[float],
        trail_price: Optional[float],
        trail_percent: Optional[float],
    ) -> None:
        """Validate order type and associated prices."""
        order_type_lower = order_type.lower()
        
        if order_type_lower == "limit":
            if limit_price is None:
                raise OrderValidationError("Limit price required for limit orders")
            if limit_price <= 0:
                raise OrderValidationError("Limit price must be positive")
        
        elif order_type_lower == "stop":
            if stop_price is None:
                raise OrderValidationError("Stop price required for stop orders")
            if stop_price <= 0:
                raise OrderValidationError("Stop price must be positive")
        
        elif order_type_lower == "stop_limit":
            if limit_price is None or stop_price is None:
                raise OrderValidationError("Both limit and stop prices required for stop-limit orders")
            if limit_price <= 0 or stop_price <= 0:
                raise OrderValidationError("Prices must be positive")
        
        elif order_type_lower == "trailing_stop":
            if trail_price is None and trail_percent is None:
                raise OrderValidationError("Either trail_price or trail_percent required for trailing stop")
            if trail_percent is not None and (trail_percent <= 0 or trail_percent >= 100):
                raise OrderValidationError("Trail percent must be between 0 and 100")
        
        elif order_type_lower != "market":
            raise OrderValidationError(f"Invalid order type: {order_type}")
    
    def _validate_market_hours(self, extended_hours: bool) -> Optional[str]:
        """Check if market is open."""
        now = datetime.now().time()
        
        # Market hours: 9:30 AM - 4:00 PM ET
        market_open = time(9, 30)
        market_close = time(16, 0)
        
        # Extended hours: 4:00 AM - 9:30 AM, 4:00 PM - 8:00 PM ET
        pre_market_open = time(4, 0)
        after_hours_close = time(20, 0)
        
        is_market_hours = market_open <= now <= market_close
        is_extended_hours = (pre_market_open <= now < market_open) or (market_close < now <= after_hours_close)
        
        if not extended_hours and not is_market_hours:
            if is_extended_hours:
                return "Market is closed. Consider enabling extended hours trading."
            else:
                return "Market is closed. Order will be queued until market opens."
        
        return None
    
    async def _validate_buying_power(
        self,
        symbol: str,
        qty: Optional[float],
        notional: Optional[float],
        order_type: str,
        limit_price: Optional[float],
    ) -> Optional[str]:
        """Validate sufficient buying power."""
        try:
            # Get account info
            account = await self.alpaca_client.get_account(use_cache=True)
            buying_power = float(account.get("buying_power", 0))
            
            # Estimate order cost
            if notional:
                estimated_cost = notional
            elif qty and order_type.lower() == "limit" and limit_price:
                estimated_cost = qty * limit_price
            elif qty:
                # For market orders, get current price estimate
                try:
                    from app.integrations.market_data import get_market_data_client
                    market_data = get_market_data_client()
                    quote = await market_data.get_latest_quote(symbol, use_cache=True)
                    estimated_cost = qty * float(quote["ask_price"])
                except Exception:
                    # If we can't get price, skip this check
                    return None
            else:
                return None
            
            # Check buying power
            if estimated_cost > buying_power:
                return f"Insufficient buying power. Order cost: ${estimated_cost:.2f}, Available: ${buying_power:.2f}"
            
            # Warning if using more than 80% of buying power
            if estimated_cost > buying_power * 0.8:
                return f"Warning: Using {(estimated_cost/buying_power)*100:.1f}% of available buying power"
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not validate buying power: {e}")
            return None
    
    async def _validate_price_reasonability(
        self,
        symbol: str,
        order_type: str,
        limit_price: Optional[float],
        stop_price: Optional[float],
    ) -> Optional[str]:
        """Check if prices are reasonable relative to current market price."""
        if order_type.lower() == "market":
            return None
        
        try:
            from app.integrations.market_data import get_market_data_client
            market_data = get_market_data_client()
            quote = await market_data.get_latest_quote(symbol, use_cache=True)
            
            current_price = (float(quote["bid_price"]) + float(quote["ask_price"])) / 2
            
            # Check limit price if provided
            if limit_price:
                diff_percent = abs(limit_price - current_price) / current_price * 100
                if diff_percent > 10:
                    return f"Limit price is {diff_percent:.1f}% away from current price ${current_price:.2f}"
            
            # Check stop price if provided
            if stop_price:
                diff_percent = abs(stop_price - current_price) / current_price * 100
                if diff_percent > 10:
                    return f"Stop price is {diff_percent:.1f}% away from current price ${current_price:.2f}"
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not validate price reasonability: {e}")
            return None
    
    async def _check_pattern_day_trader(self) -> Optional[str]:
        """Check pattern day trader status."""
        try:
            account = await self.alpaca_client.get_account(use_cache=True)
            
            if account.get("pattern_day_trader"):
                return "Account is flagged as Pattern Day Trader. Be aware of day trading restrictions."
            
            daytrade_count = account.get("daytrade_count", 0)
            if daytrade_count >= 3:
                return f"Warning: {daytrade_count} day trades in rolling 5-day period. Close to PDT threshold."
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not check PDT status: {e}")
            return None
    
    def _generate_recommendations(
        self,
        symbol: str,
        qty: Optional[float],
        order_type: str,
        limit_price: Optional[float],
        stop_price: Optional[float],
        trail_percent: Optional[float],
    ) -> list:
        """Generate recommendations for the order."""
        recommendations = []
        
        # Recommend limit orders over market for large quantities
        if qty and qty > 100 and order_type.lower() == "market":
            recommendations.append("Consider using a limit order for large quantities to control execution price")
        
        # Recommend stop loss for large positions
        if qty and qty > 50 and order_type.lower() == "market":
            recommendations.append("Consider adding a stop-loss order to protect your position")
        
        # Recommend bracket order
        if order_type.lower() == "market" and qty:
            recommendations.append("Consider using a bracket order to automatically set profit target and stop loss")
        
        # Recommend trailing stop percent
        if order_type.lower() == "trailing_stop" and not trail_percent:
            recommendations.append("Trail percent is often more flexible than trail price for volatile stocks")
        
        return recommendations


# Global instance getter
_validator: Optional[OrderValidator] = None


def get_order_validator() -> OrderValidator:
    """
    Get or create singleton order validator instance.
    
    Returns:
        OrderValidator instance
    """
    global _validator
    if _validator is None:
        _validator = OrderValidator()
    return _validator