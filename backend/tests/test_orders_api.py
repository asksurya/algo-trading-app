"""
Comprehensive test suite for Orders API routes.

Tests cover order placement, modification, cancellation, and position management
with proper mocking of order execution and async patterns.
"""
import pytest
from fastapi import status
from unittest.mock import AsyncMock, patch, MagicMock


class TestPlaceOrder:
    """Tests for POST /api/v1/orders endpoint."""

    async def test_place_market_order(self, client, auth_headers):
        """Test placing a market order successfully."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.set_db_session = MagicMock()
            mock_executor.place_order = AsyncMock(return_value={
                "id": "order-123",
                "symbol": "AAPL",
                "qty": 10.0,
                "side": "buy",
                "type": "market",
                "status": "accepted",
                "filled_qty": 0.0,
                "created_at": "2025-12-25T10:00:00Z"
            })

            response = await client.post(
                "/api/v1/orders/",
                json={
                    "symbol": "AAPL",
                    "qty": 10,
                    "side": "buy",
                    "type": "market",
                    "time_in_force": "day"
                },
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Order placed successfully"
            assert data["data"]["symbol"] == "AAPL"
            assert data["data"]["side"] == "buy"
            assert data["data"]["type"] == "market"
            assert data["data"]["status"] == "accepted"

    async def test_place_limit_order(self, client, auth_headers):
        """Test placing a limit order with limit price."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.set_db_session = MagicMock()
            mock_executor.place_order = AsyncMock(return_value={
                "id": "order-456",
                "symbol": "GOOGL",
                "qty": 5.0,
                "side": "sell",
                "type": "limit",
                "limit_price": 150.50,
                "status": "pending_new",
                "filled_qty": 0.0,
                "created_at": "2025-12-25T10:05:00Z"
            })

            response = await client.post(
                "/api/v1/orders/",
                json={
                    "symbol": "GOOGL",
                    "qty": 5,
                    "side": "sell",
                    "type": "limit",
                    "time_in_force": "day",
                    "limit_price": 150.50
                },
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["data"]["symbol"] == "GOOGL"
            assert data["data"]["type"] == "limit"
            assert data["data"]["limit_price"] == 150.50
            assert data["data"]["status"] == "pending_new"

    async def test_place_stop_order(self, client, auth_headers):
        """Test placing a stop order with stop price."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.set_db_session = MagicMock()
            mock_executor.place_order = AsyncMock(return_value={
                "id": "order-789",
                "symbol": "TSLA",
                "qty": 20.0,
                "side": "buy",
                "type": "stop",
                "stop_price": 250.00,
                "status": "accepted",
                "filled_qty": 0.0,
                "created_at": "2025-12-25T10:10:00Z"
            })

            response = await client.post(
                "/api/v1/orders/",
                json={
                    "symbol": "TSLA",
                    "qty": 20,
                    "side": "buy",
                    "type": "stop",
                    "time_in_force": "gtc",
                    "stop_price": 250.00
                },
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["data"]["type"] == "stop"
            assert data["data"]["stop_price"] == 250.00

    async def test_place_order_unauthorized(self, client):
        """Test placing an order without authentication returns 401."""
        response = await client.post(
            "/api/v1/orders/",
            json={
                "symbol": "AAPL",
                "qty": 10,
                "side": "buy",
                "type": "market",
                "time_in_force": "day"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "detail" in data

    async def test_place_order_execution_error(self, client, auth_headers):
        """Test handling order execution errors."""
        from app.integrations.order_execution import OrderExecutionError

        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.set_db_session = MagicMock()
            mock_executor.place_order = AsyncMock(
                side_effect=OrderExecutionError(
                    "Insufficient buying power",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            )

            response = await client.post(
                "/api/v1/orders/",
                json={
                    "symbol": "AAPL",
                    "qty": 10,
                    "side": "buy",
                    "type": "market",
                    "time_in_force": "day"
                },
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert "detail" in data

    async def test_place_trailing_stop_order(self, client, auth_headers):
        """Test placing a trailing stop order."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.set_db_session = MagicMock()
            mock_executor.place_order = AsyncMock(return_value={
                "id": "order-ts-123",
                "symbol": "MSFT",
                "qty": 15.0,
                "side": "buy",
                "type": "trailing_stop",
                "trail_percent": 5.0,
                "status": "accepted",
                "filled_qty": 0.0,
                "created_at": "2025-12-25T10:15:00Z"
            })

            response = await client.post(
                "/api/v1/orders/",
                json={
                    "symbol": "MSFT",
                    "qty": 15,
                    "side": "buy",
                    "type": "trailing_stop",
                    "time_in_force": "gtc",
                    "trail_percent": 5.0
                },
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["data"]["type"] == "trailing_stop"


class TestBracketOrder:
    """Tests for POST /api/v1/orders/bracket endpoint."""

    async def test_place_bracket_order(self, client, auth_headers):
        """Test placing a bracket order (entry + take profit + stop loss)."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.place_bracket_order = AsyncMock(return_value={
                "id": "bracket-123",
                "symbol": "AAPL",
                "qty": 10.0,
                "side": "buy",
                "take_profit_limit_price": 160.00,
                "stop_loss_stop_price": 145.00,
                "status": "accepted",
                "orders": [
                    {"id": "order-entry-1", "type": "limit", "status": "pending_new"},
                    {"id": "order-tp-1", "type": "limit", "status": "pending_new"},
                    {"id": "order-sl-1", "type": "stop", "status": "pending_new"}
                ]
            })

            response = await client.post(
                "/api/v1/orders/bracket",
                json={
                    "symbol": "AAPL",
                    "qty": 10,
                    "side": "buy",
                    "type": "market",
                    "time_in_force": "day",
                    "take_profit_price": 160.00,
                    "stop_loss_price": 145.00
                },
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Bracket order placed successfully"
            assert data["data"]["symbol"] == "AAPL"
            assert len(data["data"]["orders"]) == 3

    async def test_place_bracket_order_unauthorized(self, client):
        """Test placing bracket order without authentication returns 401."""
        response = await client.post(
            "/api/v1/orders/bracket",
            json={
                "symbol": "AAPL",
                "qty": 10,
                "side": "buy",
                "type": "market",
                "time_in_force": "day",
                "take_profit_price": 160.00,
                "stop_loss_price": 145.00
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_place_bracket_order_execution_error(self, client, auth_headers):
        """Test handling bracket order execution errors."""
        from app.integrations.order_execution import OrderExecutionError

        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.place_bracket_order = AsyncMock(
                side_effect=OrderExecutionError("Invalid order parameters")
            )

            response = await client.post(
                "/api/v1/orders/bracket",
                json={
                    "symbol": "AAPL",
                    "qty": 10,
                    "side": "buy",
                    "type": "market",
                    "time_in_force": "day",
                    "take_profit_price": 160.00,
                    "stop_loss_price": 145.00
                },
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestModifyOrder:
    """Tests for PATCH /api/v1/orders/{order_id} endpoint."""

    async def test_modify_order_quantity(self, client, auth_headers):
        """Test modifying order quantity."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.replace_order = AsyncMock(return_value={
                "id": "order-123",
                "symbol": "AAPL",
                "qty": 15.0,
                "side": "buy",
                "type": "limit",
                "limit_price": 150.00,
                "status": "pending_new",
                "filled_qty": 0.0,
                "created_at": "2025-12-25T10:00:00Z"
            })

            response = await client.patch(
                "/api/v1/orders/order-123",
                json={"qty": 15},
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Order modified successfully"
            assert data["data"]["qty"] == 15

    async def test_modify_order_limit_price(self, client, auth_headers):
        """Test modifying order limit price."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.replace_order = AsyncMock(return_value={
                "id": "order-456",
                "symbol": "GOOGL",
                "qty": 5.0,
                "side": "sell",
                "type": "limit",
                "limit_price": 155.00,
                "status": "pending_new",
                "filled_qty": 0.0,
                "created_at": "2025-12-25T10:05:00Z"
            })

            response = await client.patch(
                "/api/v1/orders/order-456",
                json={"limit_price": 155.00},
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["data"]["limit_price"] == 155.00

    async def test_modify_order_not_found(self, client, auth_headers):
        """Test modifying a non-existent order returns 404."""
        from app.integrations.order_execution import OrderExecutionError

        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.replace_order = AsyncMock(
                side_effect=OrderExecutionError(
                    "Order not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            )

            response = await client.patch(
                "/api/v1/orders/nonexistent-order",
                json={"qty": 10},
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "detail" in data

    async def test_modify_order_unauthorized(self, client):
        """Test modifying an order without authentication returns 401."""
        response = await client.patch(
            "/api/v1/orders/order-123",
            json={"qty": 15}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCancelOrder:
    """Tests for DELETE /api/v1/orders/{order_id} endpoint."""

    async def test_cancel_order_success(self, client, auth_headers):
        """Test canceling an order successfully."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.cancel_order = AsyncMock(return_value=True)

            response = await client.delete(
                "/api/v1/orders/order-123",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_204_NO_CONTENT
            mock_executor.cancel_order.assert_called_once_with("order-123")

    async def test_cancel_order_not_found(self, client, auth_headers):
        """Test canceling a non-existent order returns 404."""
        from app.integrations.order_execution import OrderExecutionError

        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.cancel_order = AsyncMock(
                side_effect=OrderExecutionError(
                    "Order not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            )

            response = await client.delete(
                "/api/v1/orders/nonexistent-order",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_cancel_order_unauthorized(self, client):
        """Test canceling an order without authentication returns 401."""
        response = await client.delete("/api/v1/orders/order-123")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_cancel_order_already_filled(self, client, auth_headers):
        """Test canceling an already filled order returns error."""
        from app.integrations.order_execution import OrderExecutionError

        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.cancel_order = AsyncMock(
                side_effect=OrderExecutionError(
                    "Cannot cancel a filled order",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            )

            response = await client.delete(
                "/api/v1/orders/filled-order",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestCancelAllOrders:
    """Tests for DELETE /api/v1/orders endpoint."""

    async def test_cancel_all_orders_success(self, client, auth_headers):
        """Test canceling all open orders."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.cancel_all_orders = AsyncMock(return_value=5)

            response = await client.delete(
                "/api/v1/orders/",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["count"] == 5
            assert "Canceled 5 orders" in data["message"]

    async def test_cancel_all_orders_no_orders(self, client, auth_headers):
        """Test canceling all orders when no orders exist."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.cancel_all_orders = AsyncMock(return_value=0)

            response = await client.delete(
                "/api/v1/orders/",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["count"] == 0

    async def test_cancel_all_orders_unauthorized(self, client):
        """Test canceling all orders without authentication returns 401."""
        response = await client.delete("/api/v1/orders/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_cancel_all_orders_execution_error(self, client, auth_headers):
        """Test handling execution error when canceling all orders."""
        from app.integrations.order_execution import OrderExecutionError

        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.cancel_all_orders = AsyncMock(
                side_effect=OrderExecutionError("Failed to cancel orders")
            )

            response = await client.delete(
                "/api/v1/orders/",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestClosePosition:
    """Tests for POST /api/v1/orders/positions/{symbol}/close endpoint."""

    async def test_close_position_full(self, client, auth_headers):
        """Test closing a full position."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.close_position = AsyncMock(return_value={
                "id": "close-order-123",
                "symbol": "AAPL",
                "qty": 100.0,
                "side": "sell",
                "type": "market",
                "status": "filled",
                "filled_qty": 100.0,
                "filled_avg_price": 150.25,
                "created_at": "2025-12-25T10:00:00Z"
            })

            response = await client.post(
                "/api/v1/orders/positions/AAPL/close",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "Position AAPL closed" in data["message"]
            assert data["data"]["symbol"] == "AAPL"
            assert data["data"]["status"] == "filled"

    async def test_close_position_not_found(self, client, auth_headers):
        """Test closing a non-existent position returns 404."""
        from app.integrations.order_execution import OrderExecutionError

        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.close_position = AsyncMock(
                side_effect=OrderExecutionError(
                    "Position not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            )

            response = await client.post(
                "/api/v1/orders/positions/NONEXIST/close",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_close_position_unauthorized(self, client):
        """Test closing a position without authentication returns 401."""
        response = await client.post("/api/v1/orders/positions/AAPL/close")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_close_position_symbol_uppercase(self, client, auth_headers):
        """Test that symbol is converted to uppercase."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.close_position = AsyncMock(return_value={
                "id": "close-order-123",
                "symbol": "MSFT",
                "qty": 50.0,
                "side": "sell",
                "type": "market",
                "status": "filled",
                "filled_qty": 50.0,
                "filled_avg_price": 420.00,
                "created_at": "2025-12-25T10:15:00Z"
            })

            response = await client.post(
                "/api/v1/orders/positions/msft/close",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            # Verify that the executor was called with uppercase symbol
            mock_executor.close_position.assert_called_once()
            call_args = mock_executor.close_position.call_args
            assert call_args.kwargs["symbol"] == "MSFT"


class TestCloseAllPositions:
    """Tests for DELETE /api/v1/orders/positions endpoint."""

    async def test_close_all_positions_with_cancel_orders(self, client, auth_headers):
        """Test closing all positions and canceling orders."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.close_all_positions = AsyncMock(return_value=3)

            response = await client.delete(
                "/api/v1/orders/positions?cancel_orders=true",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["count"] == 3
            assert "Closed 3 positions" in data["message"]
            mock_executor.close_all_positions.assert_called_once_with(cancel_orders=True)

    async def test_close_all_positions_without_cancel_orders(self, client, auth_headers):
        """Test closing all positions without canceling orders."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.close_all_positions = AsyncMock(return_value=2)

            response = await client.delete(
                "/api/v1/orders/positions?cancel_orders=false",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["count"] == 2
            mock_executor.close_all_positions.assert_called_once_with(cancel_orders=False)

    async def test_close_all_positions_default_cancel_orders(self, client, auth_headers):
        """Test that cancel_orders defaults to true."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.close_all_positions = AsyncMock(return_value=1)

            response = await client.delete(
                "/api/v1/orders/positions",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            mock_executor.close_all_positions.assert_called_once_with(cancel_orders=True)

    async def test_close_all_positions_no_positions(self, client, auth_headers):
        """Test closing all positions when none exist."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.close_all_positions = AsyncMock(return_value=0)

            response = await client.delete(
                "/api/v1/orders/positions",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["count"] == 0

    async def test_close_all_positions_unauthorized(self, client):
        """Test closing all positions without authentication returns 401."""
        response = await client.delete("/api/v1/orders/positions")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_close_all_positions_execution_error(self, client, auth_headers):
        """Test handling execution error when closing all positions."""
        from app.integrations.order_execution import OrderExecutionError

        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.close_all_positions = AsyncMock(
                side_effect=OrderExecutionError("Failed to close positions")
            )

            response = await client.delete(
                "/api/v1/orders/positions",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestOrderEdgeCases:
    """Tests for edge cases and error handling."""

    async def test_place_order_missing_required_symbol(self, client, auth_headers):
        """Test placing order with missing required symbol field."""
        response = await client.post(
            "/api/v1/orders/",
            json={
                "qty": 10,
                "side": "buy",
                "type": "market",
                "time_in_force": "day"
            },
            headers=auth_headers
        )

        # Should fail due to missing symbol field
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_place_order_missing_required_qty(self, client, auth_headers):
        """Test placing order with missing required qty field."""
        response = await client.post(
            "/api/v1/orders/",
            json={
                "symbol": "AAPL",
                "side": "buy",
                "type": "market",
                "time_in_force": "day"
            },
            headers=auth_headers
        )

        # Should fail due to missing qty field
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_modify_order_with_all_fields(self, client, auth_headers):
        """Test modifying an order with multiple fields at once."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.replace_order = AsyncMock(return_value={
                "id": "order-789",
                "symbol": "TSLA",
                "qty": 25.0,
                "side": "buy",
                "type": "limit",
                "limit_price": 255.00,
                "status": "pending_new",
                "filled_qty": 0.0,
                "created_at": "2025-12-25T10:10:00Z"
            })

            response = await client.patch(
                "/api/v1/orders/order-789",
                json={
                    "qty": 25,
                    "limit_price": 255.00
                },
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["data"]["qty"] == 25
            assert data["data"]["limit_price"] == 255.00

    async def test_cancel_all_orders_then_place_new_order(self, client, auth_headers):
        """Test canceling all orders and then placing a new one."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            # First cancel all orders
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.cancel_all_orders = AsyncMock(return_value=3)

            response = await client.delete(
                "/api/v1/orders/",
                headers=auth_headers
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["count"] == 3

            # Then place a new order
            mock_executor.set_db_session = MagicMock()
            mock_executor.place_order = AsyncMock(return_value={
                "id": "order-new-123",
                "symbol": "AAPL",
                "qty": 5.0,
                "side": "buy",
                "type": "market",
                "status": "accepted",
                "filled_qty": 0.0,
                "created_at": "2025-12-25T10:30:00Z"
            })

            response = await client.post(
                "/api/v1/orders/",
                json={
                    "symbol": "AAPL",
                    "qty": 5,
                    "side": "buy",
                    "type": "market",
                    "time_in_force": "day"
                },
                headers=auth_headers
            )
            assert response.status_code == status.HTTP_201_CREATED
            assert response.json()["data"]["qty"] == 5.0

    async def test_place_order_generic_error_handling(self, client, auth_headers):
        """Test generic error handling when order executor fails."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.set_db_session = MagicMock()
            # Simulate an unexpected error
            mock_executor.place_order = AsyncMock(
                side_effect=RuntimeError("Unexpected error in order executor")
            )

            response = await client.post(
                "/api/v1/orders/",
                json={
                    "symbol": "AAPL",
                    "qty": 10,
                    "side": "buy",
                    "type": "market",
                    "time_in_force": "day"
                },
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert "detail" in data

    async def test_close_position_with_lowercase_symbol(self, client, auth_headers):
        """Test that lowercase symbols are properly handled."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.close_position = AsyncMock(return_value={
                "id": "close-order-456",
                "symbol": "IBM",
                "qty": 30.0,
                "side": "sell",
                "type": "market",
                "status": "filled",
                "filled_qty": 30.0,
                "filled_avg_price": 180.50,
                "created_at": "2025-12-25T11:00:00Z"
            })

            response = await client.post(
                "/api/v1/orders/positions/ibm/close",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["data"]["symbol"] == "IBM"

    async def test_place_multiple_orders_sequentially(self, client, auth_headers):
        """Test placing multiple orders in sequence."""
        with patch('app.api.v1.orders.get_order_executor') as mock_get_executor:
            mock_executor = AsyncMock()
            mock_get_executor.return_value = mock_executor
            mock_executor.set_db_session = MagicMock()

            order_responses = [
                {
                    "id": f"order-{i}",
                    "symbol": symbol,
                    "qty": 10.0,
                    "side": "buy",
                    "type": "market",
                    "status": "accepted",
                    "filled_qty": 0.0
                }
                for i, symbol in enumerate(["AAPL", "GOOGL", "MSFT"])
            ]

            mock_executor.place_order = AsyncMock(side_effect=order_responses)

            for i, symbol in enumerate(["AAPL", "GOOGL", "MSFT"]):
                response = await client.post(
                    "/api/v1/orders/",
                    json={
                        "symbol": symbol,
                        "qty": 10,
                        "side": "buy",
                        "type": "market",
                        "time_in_force": "day"
                    },
                    headers=auth_headers
                )
                assert response.status_code == status.HTTP_201_CREATED
                assert response.json()["data"]["symbol"] == symbol
