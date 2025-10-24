"""
Order execution API endpoints.
Provides order placement, modification, cancellation, and position management.
"""
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.integrations.order_execution import get_order_executor, OrderExecutionError
from app.schemas.order import (
    OrderRequest,
    OrderUpdateRequest,
    OrderResponse,
    BracketOrderRequest,
    PositionCloseRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def place_order(
    order_request: OrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Place a new order with automatic risk management checks.
    
    Supports all order types: market, limit, stop, stop_limit, trailing_stop.
    Orders are automatically evaluated against active risk rules before execution.
    
    **Request Body:**
    ```json
    {
      "symbol": "AAPL",
      "qty": 10,
      "side": "buy",
      "type": "limit",
      "time_in_force": "day",
      "limit_price": 150.00,
      "strategy_id": 1
    }
    ```
    
    **Authentication required.**
    **Risk rules will be evaluated unless skip_risk_check=true.**
    """
    try:
        executor = get_order_executor()
        executor.set_db_session(db)  # Enable risk checks
        
        order_data = await executor.place_order(
            symbol=order_request.symbol,
            qty=order_request.qty,
            notional=order_request.notional,
            side=order_request.side.value,
            order_type=order_request.type.value,
            time_in_force=order_request.time_in_force.value,
            limit_price=order_request.limit_price,
            stop_price=order_request.stop_price,
            trail_price=order_request.trail_price,
            trail_percent=order_request.trail_percent,
            extended_hours=order_request.extended_hours,
            client_order_id=order_request.client_order_id,
            user_id=current_user.id,  # Enable risk checks
            strategy_id=order_request.strategy_id,  # Optional strategy context
            skip_risk_check=order_request.skip_risk_check if hasattr(order_request, 'skip_risk_check') else False,
        )
        
        logger.info(f"Order placed by user {current_user.id}: {order_data['id']}")
        
        return {
            "success": True,
            "message": "Order placed successfully",
            "data": order_data,
        }
        
    except OrderExecutionError as e:
        logger.error(f"Order execution error for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "order_execution_error",
                "message": e.message,
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error placing order for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to place order",
            }
        )


@router.post("/bracket", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def place_bracket_order(
    bracket_request: BracketOrderRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Place a bracket order (entry + take profit + stop loss).
    
    Automatically creates OCO (One-Cancels-Other) orders for profit taking and stop loss.
    
    **Request Body:**
    ```json
    {
      "symbol": "AAPL",
      "qty": 10,
      "side": "buy",
      "take_profit_limit_price": 160.00,
      "stop_loss_stop_price": 145.00,
      "entry_limit_price": 150.00
    }
    ```
    
    **Authentication required.**
    """
    try:
        executor = get_order_executor()
        
        order_data = await executor.place_bracket_order(
            symbol=bracket_request.symbol,
            qty=bracket_request.qty,
            side=bracket_request.side.value,
            take_profit_limit_price=bracket_request.take_profit_limit_price,
            stop_loss_stop_price=bracket_request.stop_loss_stop_price,
            entry_limit_price=bracket_request.entry_limit_price,
            time_in_force=bracket_request.time_in_force.value,
            extended_hours=bracket_request.extended_hours,
        )
        
        logger.info(f"Bracket order placed by user {current_user.id}: {order_data['id']}")
        
        return {
            "success": True,
            "message": "Bracket order placed successfully",
            "data": order_data,
        }
        
    except OrderExecutionError as e:
        logger.error(f"Order execution error for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "order_execution_error",
                "message": e.message,
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error placing bracket order for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to place bracket order",
            }
        )


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Cancel an open order.
    
    **Path Parameters:**
    - order_id: Alpaca order ID
    
    **Authentication required.**
    """
    try:
        executor = get_order_executor()
        await executor.cancel_order(order_id)
        
        logger.info(f"Order {order_id} canceled by user {current_user.id}")
        return None
        
    except OrderExecutionError as e:
        logger.error(f"Order execution error for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_404_NOT_FOUND,
            detail={
                "error": "order_execution_error",
                "message": e.message,
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error canceling order for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to cancel order",
            }
        )


@router.patch("/{order_id}", response_model=Dict[str, Any])
async def modify_order(
    order_id: str,
    update_request: OrderUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Modify an existing order.
    
    Can update quantity, limit price, stop price, trail amount, or time in force.
    
    **Path Parameters:**
    - order_id: Alpaca order ID
    
    **Request Body:**
    ```json
    {
      "qty": 15,
      "limit_price": 152.00
    }
    ```
    
    **Authentication required.**
    """
    try:
        executor = get_order_executor()
        
        order_data = await executor.replace_order(
            order_id=order_id,
            qty=update_request.qty,
            limit_price=update_request.limit_price,
            stop_price=update_request.stop_price,
            trail=update_request.trail,
            time_in_force=update_request.time_in_force.value if update_request.time_in_force else None,
            client_order_id=update_request.client_order_id,
        )
        
        logger.info(f"Order {order_id} modified by user {current_user.id}")
        
        return {
            "success": True,
            "message": "Order modified successfully",
            "data": order_data,
        }
        
    except OrderExecutionError as e:
        logger.error(f"Order execution error for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_404_NOT_FOUND,
            detail={
                "error": "order_execution_error",
                "message": e.message,
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error modifying order for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to modify order",
            }
        )


@router.delete("/", status_code=status.HTTP_200_OK)
async def cancel_all_orders(
    current_user: User = Depends(get_current_user),
):
    """
    Cancel all open orders.
    
    **Authentication required.**
    """
    try:
        executor = get_order_executor()
        count = await executor.cancel_all_orders()
        
        logger.info(f"All orders ({count}) canceled by user {current_user.id}")
        
        return {
            "success": True,
            "message": f"Canceled {count} orders",
            "count": count,
        }
        
    except OrderExecutionError as e:
        logger.error(f"Order execution error for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "order_execution_error",
                "message": e.message,
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error canceling all orders for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to cancel orders",
            }
        )


@router.post("/positions/{symbol}/close", response_model=Dict[str, Any])
async def close_position(
    symbol: str,
    close_request: Optional[PositionCloseRequest] = None,
    current_user: User = Depends(get_current_user),
):
    """
    Close an open position.
    
    Can close full position or partial based on quantity or percentage.
    
    **Path Parameters:**
    - symbol: Stock symbol
    
    **Request Body (optional):**
    ```json
    {
      "qty": 5,
      "percentage": 50
    }
    ```
    
    **Authentication required.**
    """
    try:
        executor = get_order_executor()
        
        qty = close_request.qty if close_request else None
        percentage = close_request.percentage if close_request else None
        
        order_data = await executor.close_position(
            symbol=symbol.upper(),
            qty=qty,
            percentage=percentage,
        )
        
        logger.info(f"Position {symbol} closed by user {current_user.id}")
        
        return {
            "success": True,
            "message": f"Position {symbol} closed",
            "data": order_data,
        }
        
    except OrderExecutionError as e:
        logger.error(f"Order execution error for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_404_NOT_FOUND,
            detail={
                "error": "order_execution_error",
                "message": e.message,
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error closing position for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to close position",
            }
        )


@router.delete("/positions", status_code=status.HTTP_200_OK)
async def close_all_positions(
    cancel_orders: bool = True,
    current_user: User = Depends(get_current_user),
):
    """
    Close all open positions.
    
    **Query Parameters:**
    - cancel_orders: Also cancel all open orders (default: true)
    
    **Authentication required.**
    """
    try:
        executor = get_order_executor()
        count = await executor.close_all_positions(cancel_orders=cancel_orders)
        
        logger.info(f"All positions ({count}) closed by user {current_user.id}")
        
        return {
            "success": True,
            "message": f"Closed {count} positions",
            "count": count,
        }
        
    except OrderExecutionError as e:
        logger.error(f"Order execution error for user {current_user.id}: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "order_execution_error",
                "message": e.message,
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error closing all positions for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to close positions",
            }
        )
