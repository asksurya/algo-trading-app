"""
Comprehensive test suite for the Order Validation Service.

Tests cover all validation methods including:
- Order quantity and notional validation
- Symbol validation
- Order side validation
- Order type and price validation
- Market hours validation
- Buying power validation
- Price reasonability checks
- Pattern Day Trader status checks
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, time

from app.services.order_validation import OrderValidator, OrderValidationError


@pytest.fixture
def mock_alpaca_client():
    """Mock Alpaca API client."""
    client = AsyncMock()
    client.get_account = AsyncMock(
        return_value={
            "buying_power": 100000.0,
            "pattern_day_trader": False,
            "daytrade_count": 0,
        }
    )
    return client


@pytest.fixture
def mock_market_data_client():
    """Mock market data client for quote and trade data."""
    client = AsyncMock()
    client.get_latest_quote = AsyncMock(
        return_value={
            "bid_price": 149.5,
            "ask_price": 150.5,
        }
    )
    client.get_latest_trade = AsyncMock(
        return_value={
            "price": 150.0,
        }
    )
    return client


@pytest.fixture
def order_validator():
    """Create an OrderValidator instance."""
    return OrderValidator()


# ========================
# Quantity Validation Tests
# ========================


class TestQuantityValidation:
    """Tests for quantity and notional validation."""

    @pytest.mark.asyncio
    async def test_validate_order_success(
        self, order_validator, mock_alpaca_client, mock_market_data_client
    ):
        """Test that a valid order passes all validation checks."""
        with patch(
            "app.services.order_validation.get_alpaca_client",
            return_value=mock_alpaca_client,
        ):
            with patch(
                "app.integrations.market_data.get_market_data_client",
                return_value=mock_market_data_client,
            ):
                order_validator.alpaca_client = mock_alpaca_client

                result = await order_validator.validate_order(
                    symbol="AAPL",
                    qty=10,
                    side="buy",
                    order_type="market",
                )

                assert result["valid"] is True
                assert isinstance(result["warnings"], list)
                assert isinstance(result["recommendations"], list)

    @pytest.mark.asyncio
    async def test_validate_quantity_zero(self, order_validator):
        """Test that zero quantity fails validation."""
        with pytest.raises(OrderValidationError) as exc_info:
            order_validator._validate_quantity(qty=0, notional=None)

        assert "Quantity must be positive" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_quantity_negative(self, order_validator):
        """Test that negative quantity fails validation."""
        with pytest.raises(OrderValidationError) as exc_info:
            order_validator._validate_quantity(qty=-10, notional=None)

        assert "Quantity must be positive" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_quantity_none_and_notional_none(self, order_validator):
        """Test that both qty and notional cannot be None."""
        with pytest.raises(OrderValidationError) as exc_info:
            order_validator._validate_quantity(qty=None, notional=None)

        assert "Either qty or notional must be provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_notional_zero(self, order_validator):
        """Test that zero notional fails validation."""
        with pytest.raises(OrderValidationError) as exc_info:
            order_validator._validate_quantity(qty=None, notional=0)

        assert "Notional amount must be positive" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_notional_negative(self, order_validator):
        """Test that negative notional fails validation."""
        with pytest.raises(OrderValidationError) as exc_info:
            order_validator._validate_quantity(qty=None, notional=-1000)

        assert "Notional amount must be positive" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_both_qty_and_notional(self, order_validator):
        """Test that both qty and notional cannot be specified together."""
        with pytest.raises(OrderValidationError) as exc_info:
            order_validator._validate_quantity(qty=10, notional=1500)

        assert "Cannot specify both qty and notional" in str(exc_info.value)


# ========================
# Symbol Validation Tests
# ========================


class TestSymbolValidation:
    """Tests for symbol validation."""

    @pytest.mark.asyncio
    async def test_validate_symbol_valid(self, order_validator):
        """Test that valid symbol passes validation."""
        # Should not raise exception
        await order_validator._validate_symbol("AAPL")

    @pytest.mark.asyncio
    async def test_validate_symbol_empty(self, order_validator):
        """Test that empty symbol fails validation."""
        with pytest.raises(OrderValidationError) as exc_info:
            await order_validator._validate_symbol("")

        assert "Invalid symbol format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_symbol_too_long(self, order_validator):
        """Test that symbol longer than 10 characters fails validation."""
        with pytest.raises(OrderValidationError) as exc_info:
            await order_validator._validate_symbol("VERYLONGSYMBOL")

        assert "Invalid symbol format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_symbol_with_numbers(self, order_validator):
        """Test that symbol with numbers fails validation."""
        with pytest.raises(OrderValidationError) as exc_info:
            await order_validator._validate_symbol("AAPL1")

        assert "Symbol must contain only letters" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_symbol_with_special_chars(self, order_validator):
        """Test that symbol with special characters fails validation."""
        with pytest.raises(OrderValidationError) as exc_info:
            await order_validator._validate_symbol("AA-PL")

        assert "Symbol must contain only letters" in str(exc_info.value)


# ========================
# Side Validation Tests
# ========================


class TestSideValidation:
    """Tests for order side validation."""

    @pytest.mark.asyncio
    async def test_validate_side_buy(self, order_validator):
        """Test that 'buy' side is valid."""
        # Should not raise exception
        order_validator._validate_side("buy")

    @pytest.mark.asyncio
    async def test_validate_side_sell(self, order_validator):
        """Test that 'sell' side is valid."""
        # Should not raise exception
        order_validator._validate_side("sell")

    @pytest.mark.asyncio
    async def test_validate_side_case_insensitive(self, order_validator):
        """Test that side validation is case insensitive."""
        # Should not raise exceptions
        order_validator._validate_side("BUY")
        order_validator._validate_side("SELL")
        order_validator._validate_side("Buy")

    @pytest.mark.asyncio
    async def test_validate_side_invalid(self, order_validator):
        """Test that invalid side fails validation."""
        with pytest.raises(OrderValidationError) as exc_info:
            order_validator._validate_side("hold")

        assert "Side must be 'buy' or 'sell'" in str(exc_info.value)


# ========================
# Order Type and Price Tests
# ========================


class TestOrderTypeAndPriceValidation:
    """Tests for order type and price validation."""

    @pytest.mark.asyncio
    async def test_validate_market_order(self, order_validator):
        """Test that market order is valid without prices."""
        # Should not raise exception
        order_validator._validate_order_type_and_prices(
            order_type="market",
            limit_price=None,
            stop_price=None,
            trail_price=None,
            trail_percent=None,
        )

    @pytest.mark.asyncio
    async def test_validate_limit_order_with_price(self, order_validator):
        """Test that limit order with price is valid."""
        # Should not raise exception
        order_validator._validate_order_type_and_prices(
            order_type="limit",
            limit_price=150.0,
            stop_price=None,
            trail_price=None,
            trail_percent=None,
        )

    @pytest.mark.asyncio
    async def test_validate_limit_order_without_price(self, order_validator):
        """Test that limit order without price fails validation."""
        with pytest.raises(OrderValidationError) as exc_info:
            order_validator._validate_order_type_and_prices(
                order_type="limit",
                limit_price=None,
                stop_price=None,
                trail_price=None,
                trail_percent=None,
            )

        assert "Limit price required for limit orders" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_limit_order_with_zero_price(self, order_validator):
        """Test that limit order with zero price fails validation."""
        with pytest.raises(OrderValidationError) as exc_info:
            order_validator._validate_order_type_and_prices(
                order_type="limit",
                limit_price=0,
                stop_price=None,
                trail_price=None,
                trail_percent=None,
            )

        assert "Limit price must be positive" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_stop_order_with_price(self, order_validator):
        """Test that stop order with price is valid."""
        # Should not raise exception
        order_validator._validate_order_type_and_prices(
            order_type="stop",
            limit_price=None,
            stop_price=145.0,
            trail_price=None,
            trail_percent=None,
        )

    @pytest.mark.asyncio
    async def test_validate_stop_order_without_price(self, order_validator):
        """Test that stop order without price fails validation."""
        with pytest.raises(OrderValidationError) as exc_info:
            order_validator._validate_order_type_and_prices(
                order_type="stop",
                limit_price=None,
                stop_price=None,
                trail_price=None,
                trail_percent=None,
            )

        assert "Stop price required for stop orders" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_stop_limit_order_with_both_prices(self, order_validator):
        """Test that stop-limit order with both prices is valid."""
        # Should not raise exception
        order_validator._validate_order_type_and_prices(
            order_type="stop_limit",
            limit_price=150.0,
            stop_price=145.0,
            trail_price=None,
            trail_percent=None,
        )

    @pytest.mark.asyncio
    async def test_validate_stop_limit_order_missing_limit_price(self, order_validator):
        """Test that stop-limit order without limit price fails validation."""
        with pytest.raises(OrderValidationError) as exc_info:
            order_validator._validate_order_type_and_prices(
                order_type="stop_limit",
                limit_price=None,
                stop_price=145.0,
                trail_price=None,
                trail_percent=None,
            )

        assert "Both limit and stop prices required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_trailing_stop_with_trail_percent(self, order_validator):
        """Test that trailing stop with trail percent is valid."""
        # Should not raise exception
        order_validator._validate_order_type_and_prices(
            order_type="trailing_stop",
            limit_price=None,
            stop_price=None,
            trail_price=None,
            trail_percent=2.5,
        )

    @pytest.mark.asyncio
    async def test_validate_trailing_stop_with_trail_price(self, order_validator):
        """Test that trailing stop with trail price is valid."""
        # Should not raise exception
        order_validator._validate_order_type_and_prices(
            order_type="trailing_stop",
            limit_price=None,
            stop_price=None,
            trail_price=5.0,
            trail_percent=None,
        )

    @pytest.mark.asyncio
    async def test_validate_trailing_stop_without_trail(self, order_validator):
        """Test that trailing stop without trail price or percent fails."""
        with pytest.raises(OrderValidationError) as exc_info:
            order_validator._validate_order_type_and_prices(
                order_type="trailing_stop",
                limit_price=None,
                stop_price=None,
                trail_price=None,
                trail_percent=None,
            )

        assert "Either trail_price or trail_percent required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_trailing_stop_with_invalid_percent(self, order_validator):
        """Test that trailing stop with invalid percent fails."""
        with pytest.raises(OrderValidationError) as exc_info:
            order_validator._validate_order_type_and_prices(
                order_type="trailing_stop",
                limit_price=None,
                stop_price=None,
                trail_price=None,
                trail_percent=101.0,
            )

        assert "Trail percent must be between 0 and 100" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_invalid_order_type(self, order_validator):
        """Test that invalid order type fails validation."""
        with pytest.raises(OrderValidationError) as exc_info:
            order_validator._validate_order_type_and_prices(
                order_type="invalid_type",
                limit_price=None,
                stop_price=None,
                trail_price=None,
                trail_percent=None,
            )

        assert "Invalid order type" in str(exc_info.value)


# ========================
# Market Hours Validation Tests
# ========================


class TestMarketHoursValidation:
    """Tests for market hours validation."""

    @pytest.mark.asyncio
    async def test_validate_market_hours_during_hours(self, order_validator):
        """Test that order during market hours returns no warning."""
        # Mock market hours: 9:30 AM - 4:00 PM
        with patch("app.services.order_validation.datetime") as mock_datetime:
            mock_datetime.now.return_value.time.return_value = time(10, 30)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(
                *args, **kwargs
            )

            warning = order_validator._validate_market_hours(extended_hours=False)

            assert warning is None

    @pytest.mark.asyncio
    async def test_validate_market_hours_after_hours_without_extended(
        self, order_validator
    ):
        """Test that after-hours order without extended flag returns warning."""
        # Mock after-hours time: 5:00 PM
        with patch("app.services.order_validation.datetime") as mock_datetime:
            mock_datetime.now.return_value.time.return_value = time(17, 0)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(
                *args, **kwargs
            )

            warning = order_validator._validate_market_hours(extended_hours=False)

            assert warning is not None
            assert "extended hours" in warning.lower()

    @pytest.mark.asyncio
    async def test_validate_market_hours_extended_hours_enabled(self, order_validator):
        """Test that extended hours order returns no warning."""
        # Mock pre-market time: 7:00 AM
        with patch("app.services.order_validation.datetime") as mock_datetime:
            mock_datetime.now.return_value.time.return_value = time(7, 0)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(
                *args, **kwargs
            )

            warning = order_validator._validate_market_hours(extended_hours=True)

            # Should not return warning if extended hours are enabled
            assert warning is None

    @pytest.mark.asyncio
    async def test_validate_market_hours_closed_without_extended(self, order_validator):
        """Test that market closed warning without extended hours."""
        # Mock closed time: 3:00 AM
        with patch("app.services.order_validation.datetime") as mock_datetime:
            mock_datetime.now.return_value.time.return_value = time(3, 0)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(
                *args, **kwargs
            )

            warning = order_validator._validate_market_hours(extended_hours=False)

            assert warning is not None
            assert "closed" in warning.lower()


# ========================
# Buying Power Validation Tests
# ========================


class TestBuyingPowerValidation:
    """Tests for buying power validation."""

    @pytest.mark.asyncio
    async def test_validate_buying_power_sufficient(
        self, order_validator, mock_alpaca_client, mock_market_data_client
    ):
        """Test that sufficient buying power returns no warning."""
        order_validator.alpaca_client = mock_alpaca_client
        mock_alpaca_client.get_account = AsyncMock(
            return_value={"buying_power": 100000.0}
        )

        with patch(
            "app.integrations.market_data.get_market_data_client",
            return_value=mock_market_data_client,
        ):
            # Order cost: 10 * 150 = 1500
            warning = await order_validator._validate_buying_power(
                symbol="AAPL",
                qty=10,
                notional=None,
                order_type="market",
                limit_price=None,
            )

            assert warning is None

    @pytest.mark.asyncio
    async def test_validate_buying_power_insufficient(
        self, order_validator, mock_alpaca_client, mock_market_data_client
    ):
        """Test that insufficient buying power returns warning."""
        order_validator.alpaca_client = mock_alpaca_client
        mock_alpaca_client.get_account = AsyncMock(
            return_value={"buying_power": 1000.0}
        )

        with patch(
            "app.integrations.market_data.get_market_data_client",
            return_value=mock_market_data_client,
        ):
            # Order cost: 10 * 150 = 1500 > 1000
            warning = await order_validator._validate_buying_power(
                symbol="AAPL",
                qty=10,
                notional=None,
                order_type="market",
                limit_price=None,
            )

            assert warning is not None
            assert "Insufficient buying power" in warning

    @pytest.mark.asyncio
    async def test_validate_buying_power_with_notional(
        self, order_validator, mock_alpaca_client
    ):
        """Test buying power validation with notional amount."""
        order_validator.alpaca_client = mock_alpaca_client
        mock_alpaca_client.get_account = AsyncMock(
            return_value={"buying_power": 100000.0}
        )

        # Notional: 2500
        warning = await order_validator._validate_buying_power(
            symbol="AAPL",
            qty=None,
            notional=2500.0,
            order_type="market",
            limit_price=None,
        )

        assert warning is None

    @pytest.mark.asyncio
    async def test_validate_buying_power_with_limit_price(
        self, order_validator, mock_alpaca_client
    ):
        """Test buying power validation with limit price."""
        order_validator.alpaca_client = mock_alpaca_client
        mock_alpaca_client.get_account = AsyncMock(
            return_value={"buying_power": 100000.0}
        )

        # Order cost: 10 * 155 (limit price) = 1550
        warning = await order_validator._validate_buying_power(
            symbol="AAPL",
            qty=10,
            notional=None,
            order_type="limit",
            limit_price=155.0,
        )

        assert warning is None

    @pytest.mark.asyncio
    async def test_validate_buying_power_high_utilization_warning(
        self, order_validator, mock_alpaca_client, mock_market_data_client
    ):
        """Test warning when using more than 80% of buying power."""
        order_validator.alpaca_client = mock_alpaca_client
        mock_alpaca_client.get_account = AsyncMock(
            return_value={"buying_power": 10000.0}
        )

        with patch(
            "app.integrations.market_data.get_market_data_client",
            return_value=mock_market_data_client,
        ):
            # Order cost: 50 * 150 = 7500, which is 75% of buying power
            # Actually 7500 / 10000 = 75%, but we need > 80%
            # Let's use 100 * 85 = 8500, which is 85% of 10000
            mock_market_data_client.get_latest_quote = AsyncMock(
                return_value={"bid_price": 84.5, "ask_price": 85.5}
            )

            warning = await order_validator._validate_buying_power(
                symbol="AAPL",
                qty=100,
                notional=None,
                order_type="market",
                limit_price=None,
            )

            assert warning is not None
            assert "Warning" in warning or "%" in warning


# ========================
# Price Reasonability Tests
# ========================


class TestPriceReasonabilityValidation:
    """Tests for price reasonability validation."""

    @pytest.mark.asyncio
    async def test_validate_price_market_order_no_check(
        self, order_validator, mock_market_data_client
    ):
        """Test that market orders skip price reasonability checks."""
        with patch(
            "app.integrations.market_data.get_market_data_client",
            return_value=mock_market_data_client,
        ):
            warning = await order_validator._validate_price_reasonability(
                symbol="AAPL",
                order_type="market",
                limit_price=None,
                stop_price=None,
            )

            assert warning is None
            # Market data client should not be called
            mock_market_data_client.get_latest_quote.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_price_reasonability_limit_reasonable(
        self, order_validator, mock_market_data_client
    ):
        """Test that reasonable limit price returns no warning."""
        with patch(
            "app.integrations.market_data.get_market_data_client",
            return_value=mock_market_data_client,
        ):
            # Current price: ~150, limit price: 150
            warning = await order_validator._validate_price_reasonability(
                symbol="AAPL",
                order_type="limit",
                limit_price=150.0,
                stop_price=None,
            )

            assert warning is None

    @pytest.mark.asyncio
    async def test_validate_price_reasonability_limit_unreasonable(
        self, order_validator, mock_market_data_client
    ):
        """Test that unreasonable limit price returns warning."""
        with patch(
            "app.integrations.market_data.get_market_data_client",
            return_value=mock_market_data_client,
        ):
            # Current price: ~150, limit price: 50 (66% below)
            warning = await order_validator._validate_price_reasonability(
                symbol="AAPL",
                order_type="limit",
                limit_price=50.0,
                stop_price=None,
            )

            assert warning is not None
            assert "Limit price" in warning

    @pytest.mark.asyncio
    async def test_validate_price_reasonability_stop_reasonable(
        self, order_validator, mock_market_data_client
    ):
        """Test that reasonable stop price returns no warning."""
        with patch(
            "app.integrations.market_data.get_market_data_client",
            return_value=mock_market_data_client,
        ):
            # Current price: ~150, stop price: 145 (3.3% below)
            warning = await order_validator._validate_price_reasonability(
                symbol="AAPL",
                order_type="stop",
                limit_price=None,
                stop_price=145.0,
            )

            assert warning is None

    @pytest.mark.asyncio
    async def test_validate_price_reasonability_stop_unreasonable(
        self, order_validator, mock_market_data_client
    ):
        """Test that unreasonable stop price returns warning."""
        with patch(
            "app.integrations.market_data.get_market_data_client",
            return_value=mock_market_data_client,
        ):
            # Current price: ~150, stop price: 300 (100% above)
            warning = await order_validator._validate_price_reasonability(
                symbol="AAPL",
                order_type="stop",
                limit_price=None,
                stop_price=300.0,
            )

            assert warning is not None
            assert "Stop price" in warning


# ========================
# Pattern Day Trader Tests
# ========================


class TestPatternDayTraderValidation:
    """Tests for pattern day trader status checks."""

    @pytest.mark.asyncio
    async def test_check_pattern_day_trader_not_flagged(
        self, order_validator, mock_alpaca_client
    ):
        """Test that non-PDT account returns no warning."""
        order_validator.alpaca_client = mock_alpaca_client
        mock_alpaca_client.get_account = AsyncMock(
            return_value={
                "pattern_day_trader": False,
                "daytrade_count": 0,
            }
        )

        warning = await order_validator._check_pattern_day_trader()

        assert warning is None

    @pytest.mark.asyncio
    async def test_check_pattern_day_trader_flagged(
        self, order_validator, mock_alpaca_client
    ):
        """Test that PDT flagged account returns warning."""
        order_validator.alpaca_client = mock_alpaca_client
        mock_alpaca_client.get_account = AsyncMock(
            return_value={
                "pattern_day_trader": True,
                "daytrade_count": 3,
            }
        )

        warning = await order_validator._check_pattern_day_trader()

        assert warning is not None
        assert "Pattern Day Trader" in warning

    @pytest.mark.asyncio
    async def test_check_pattern_day_trader_approaching_threshold(
        self, order_validator, mock_alpaca_client
    ):
        """Test that close to PDT threshold returns warning."""
        order_validator.alpaca_client = mock_alpaca_client
        mock_alpaca_client.get_account = AsyncMock(
            return_value={
                "pattern_day_trader": False,
                "daytrade_count": 3,
            }
        )

        warning = await order_validator._check_pattern_day_trader()

        assert warning is not None
        assert "day trades" in warning.lower()

    @pytest.mark.asyncio
    async def test_check_pattern_day_trader_api_error(
        self, order_validator, mock_alpaca_client
    ):
        """Test that API error is handled gracefully."""
        order_validator.alpaca_client = mock_alpaca_client
        mock_alpaca_client.get_account = AsyncMock(side_effect=Exception("API Error"))

        warning = await order_validator._check_pattern_day_trader()

        # Should return None when API fails
        assert warning is None


# ========================
# Recommendations Tests
# ========================


class TestRecommendationsGeneration:
    """Tests for order recommendations generation."""

    @pytest.mark.asyncio
    async def test_recommendations_large_market_order(self, order_validator):
        """Test recommendations for large market orders."""
        recommendations = order_validator._generate_recommendations(
            symbol="AAPL",
            qty=150,
            order_type="market",
            limit_price=None,
            stop_price=None,
            trail_percent=None,
        )

        assert len(recommendations) > 0
        # Should recommend limit order for large quantity
        assert any("limit order" in rec.lower() for rec in recommendations)

    @pytest.mark.asyncio
    async def test_recommendations_large_position_without_stop(self, order_validator):
        """Test recommendations for large position without stop loss."""
        recommendations = order_validator._generate_recommendations(
            symbol="AAPL",
            qty=75,
            order_type="market",
            limit_price=None,
            stop_price=None,
            trail_percent=None,
        )

        assert len(recommendations) > 0
        # Should recommend stop-loss
        assert any("stop" in rec.lower() for rec in recommendations)

    @pytest.mark.asyncio
    async def test_recommendations_small_order(self, order_validator):
        """Test no recommendations for small orders."""
        recommendations = order_validator._generate_recommendations(
            symbol="AAPL",
            qty=5,
            order_type="market",
            limit_price=None,
            stop_price=None,
            trail_percent=None,
        )

        # Small orders may still get some recommendations (bracket order)
        # but not the large quantity recommendations
        for rec in recommendations:
            assert "100" not in rec  # No mention of large quantities

    @pytest.mark.asyncio
    async def test_recommendations_trailing_stop_without_percent(self, order_validator):
        """Test recommendations for trailing stop without percent."""
        recommendations = order_validator._generate_recommendations(
            symbol="AAPL",
            qty=10,
            order_type="trailing_stop",
            limit_price=None,
            stop_price=None,
            trail_percent=None,
        )

        # Should recommend using trail percent
        assert any("trail" in rec.lower() and "percent" in rec.lower() for rec in recommendations)


# ========================
# Integration Tests
# ========================


class TestOrderValidationIntegration:
    """Integration tests for complete order validation flow."""

    @pytest.mark.asyncio
    async def test_full_validation_buy_order(
        self, mock_alpaca_client, mock_market_data_client
    ):
        """Test complete validation flow for a buy order."""
        with patch(
            "app.services.order_validation.get_alpaca_client",
            return_value=mock_alpaca_client,
        ):
            with patch(
                "app.integrations.market_data.get_market_data_client",
                return_value=mock_market_data_client,
            ):
                validator = OrderValidator()
                validator.alpaca_client = mock_alpaca_client

                result = await validator.validate_order(
                    symbol="AAPL",
                    qty=50,
                    side="buy",
                    order_type="limit",
                    limit_price=150.0,
                    extended_hours=False,
                )

                assert result["valid"] is True
                assert isinstance(result["warnings"], list)
                assert isinstance(result["recommendations"], list)

    @pytest.mark.asyncio
    async def test_full_validation_sell_order(
        self, mock_alpaca_client, mock_market_data_client
    ):
        """Test complete validation flow for a sell order."""
        with patch(
            "app.services.order_validation.get_alpaca_client",
            return_value=mock_alpaca_client,
        ):
            with patch(
                "app.integrations.market_data.get_market_data_client",
                return_value=mock_market_data_client,
            ):
                validator = OrderValidator()
                validator.alpaca_client = mock_alpaca_client

                result = await validator.validate_order(
                    symbol="TSLA",
                    qty=20,
                    side="sell",
                    order_type="market",
                    extended_hours=False,
                )

                assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_full_validation_with_notional(
        self, mock_alpaca_client, mock_market_data_client
    ):
        """Test complete validation flow using notional amount."""
        with patch(
            "app.services.order_validation.get_alpaca_client",
            return_value=mock_alpaca_client,
        ):
            with patch(
                "app.integrations.market_data.get_market_data_client",
                return_value=mock_market_data_client,
            ):
                validator = OrderValidator()
                validator.alpaca_client = mock_alpaca_client

                result = await validator.validate_order(
                    symbol="MSFT",
                    notional=5000.0,
                    side="buy",
                    order_type="market",
                    extended_hours=False,
                )

                assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_full_validation_invalid_symbol(
        self, mock_alpaca_client, mock_market_data_client
    ):
        """Test that invalid symbol fails validation."""
        with patch(
            "app.services.order_validation.get_alpaca_client",
            return_value=mock_alpaca_client,
        ):
            with patch(
                "app.integrations.market_data.get_market_data_client",
                return_value=mock_market_data_client,
            ):
                validator = OrderValidator()
                validator.alpaca_client = mock_alpaca_client

                with pytest.raises(OrderValidationError) as exc_info:
                    await validator.validate_order(
                        symbol="INVALID123",
                        qty=10,
                        side="buy",
                        order_type="market",
                    )

                assert "Invalid symbol" in str(exc_info.value) or "Symbol" in str(
                    exc_info.value
                )

    @pytest.mark.asyncio
    async def test_full_validation_invalid_order_type(
        self, mock_alpaca_client, mock_market_data_client
    ):
        """Test that invalid order type fails validation."""
        with patch(
            "app.services.order_validation.get_alpaca_client",
            return_value=mock_alpaca_client,
        ):
            with patch(
                "app.integrations.market_data.get_market_data_client",
                return_value=mock_market_data_client,
            ):
                validator = OrderValidator()
                validator.alpaca_client = mock_alpaca_client

                with pytest.raises(OrderValidationError):
                    await validator.validate_order(
                        symbol="AAPL",
                        qty=10,
                        side="buy",
                        order_type="invalid_order_type",
                    )

    @pytest.mark.asyncio
    async def test_error_handling_unexpected_exception(
        self, mock_alpaca_client, mock_market_data_client
    ):
        """Test that unexpected errors are caught and wrapped."""
        with patch(
            "app.services.order_validation.get_alpaca_client",
            return_value=mock_alpaca_client,
        ):
            with patch(
                "app.integrations.market_data.get_market_data_client",
                return_value=mock_market_data_client,
            ):
                validator = OrderValidator()
                validator.alpaca_client = mock_alpaca_client

                # Mock _validate_symbol to raise unexpected exception
                with patch.object(
                    validator,
                    "_validate_symbol",
                    side_effect=RuntimeError("Unexpected error"),
                ):
                    with pytest.raises(OrderValidationError) as exc_info:
                        await validator.validate_order(
                            symbol="AAPL",
                            qty=10,
                            side="buy",
                            order_type="market",
                        )

                    assert "Validation error" in str(exc_info.value)
