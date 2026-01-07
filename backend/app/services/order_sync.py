"""
Order synchronization service.
Syncs orders from Alpaca to local database for tracking and analytics.
"""
import logging
from datetime import datetime, timezone, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models.order import Order, OrderSideEnum, OrderTypeEnum, OrderStatusEnum
from app.integrations.alpaca_client import get_alpaca_client

logger = logging.getLogger(__name__)


class OrderSyncService:
    """
    Service for synchronizing orders from Alpaca to database.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize order sync service."""
        self.session = session
        self.alpaca_client = get_alpaca_client()
    
    async def sync_order(self, user_id: str, alpaca_order_data: Dict[str, Any]) -> Order:
        """
        Sync a single order from Alpaca to database.
        
        Args:
            user_id: User ID
            alpaca_order_data: Order data from Alpaca API
            
        Returns:
            Order model instance
        """
        try:
            # Parse order data
            order_data = {
                "user_id": user_id,
                "alpaca_order_id": alpaca_order_data["id"],
                "client_order_id": alpaca_order_data.get("client_order_id"),
                "symbol": alpaca_order_data["symbol"],
                "side": OrderSideEnum(alpaca_order_data["side"]),
                "order_type": self._map_order_type(alpaca_order_data["order_type"]),
                "time_in_force": alpaca_order_data["time_in_force"],
                "qty": alpaca_order_data.get("qty"),
                "notional": alpaca_order_data.get("notional"),
                "filled_qty": alpaca_order_data.get("filled_qty", 0.0),
                "limit_price": alpaca_order_data.get("limit_price"),
                "stop_price": alpaca_order_data.get("stop_price"),
                "filled_avg_price": alpaca_order_data.get("filled_avg_price"),
                "trail_price": alpaca_order_data.get("trail_price"),
                "trail_percent": alpaca_order_data.get("trail_percent"),
                "hwm": alpaca_order_data.get("hwm"),
                "status": OrderStatusEnum(alpaca_order_data["status"]),
                "submitted_at": self._parse_datetime(alpaca_order_data.get("submitted_at")),
                "filled_at": self._parse_datetime(alpaca_order_data.get("filled_at")),
                "canceled_at": self._parse_datetime(alpaca_order_data.get("canceled_at")),
                "expired_at": self._parse_datetime(alpaca_order_data.get("expired_at")),
                "failed_at": self._parse_datetime(alpaca_order_data.get("failed_at")),
                "replaced_at": self._parse_datetime(alpaca_order_data.get("replaced_at")),
                "replaced_by": alpaca_order_data.get("replaced_by"),
                "replaces": alpaca_order_data.get("replaces"),
                "extended_hours": alpaca_order_data.get("extended_hours", False),
                "asset_class": alpaca_order_data.get("asset_class", "us_equity"),
                "asset_id": alpaca_order_data.get("asset_id"),
            }
            
            # Upsert order (insert or update if exists)
            stmt = insert(Order).values(**order_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=['alpaca_order_id'],
                set_={
                    "filled_qty": stmt.excluded.filled_qty,
                    "filled_avg_price": stmt.excluded.filled_avg_price,
                    "status": stmt.excluded.status,
                    "filled_at": stmt.excluded.filled_at,
                    "canceled_at": stmt.excluded.canceled_at,
                    "expired_at": stmt.excluded.expired_at,
                    "failed_at": stmt.excluded.failed_at,
                    "replaced_at": stmt.excluded.replaced_at,
                    "replaced_by": stmt.excluded.replaced_by,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            
            await self.session.execute(stmt)
            await self.session.commit()
            
            # Fetch and return the order
            result = await self.session.execute(
                select(Order).where(Order.alpaca_order_id == alpaca_order_data["id"])
            )
            order = result.scalar_one()
            
            logger.info(f"Synced order {order.alpaca_order_id} for user {user_id}")
            return order
            
        except Exception as e:
            logger.error(f"Error syncing order: {e}")
            await self.session.rollback()
            raise
    
    async def sync_user_orders(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Order]:
        """
        Sync all orders for a user from Alpaca to database.
        
        Args:
            user_id: User ID
            status: Optional status filter ("all", "open", "closed")
            limit: Maximum number of orders to sync
            
        Returns:
            List of synced Order instances
        """
        try:
            # Fetch orders from Alpaca
            alpaca_orders = await self.alpaca_client.get_orders(
                status=status,
                limit=limit,
                use_cache=False  # Always fetch fresh data for sync
            )
            
            # Sync each order
            synced_orders = []
            for alpaca_order in alpaca_orders:
                order = await self.sync_order(user_id, alpaca_order)
                synced_orders.append(order)
            
            logger.info(f"Synced {len(synced_orders)} orders for user {user_id}")
            return synced_orders
            
        except Exception as e:
            logger.error(f"Error syncing user orders: {e}")
            raise
    
    async def get_user_orders(
        self,
        user_id: str,
        status: Optional[OrderStatusEnum] = None,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Order]:
        """
        Get orders from database with optional filtering.
        
        Args:
            user_id: User ID
            status: Optional status filter
            symbol: Optional symbol filter
            limit: Maximum number of orders to return
            
        Returns:
            List of Order instances
        """
        try:
            query = select(Order).where(Order.user_id == user_id)
            
            if status:
                query = query.where(Order.status == status)
            
            if symbol:
                query = query.where(Order.symbol == symbol.upper())
            
            query = query.order_by(Order.created_at.desc()).limit(limit)
            
            result = await self.session.execute(query)
            orders = result.scalars().all()
            
            return list(orders)
            
        except Exception as e:
            logger.error(f"Error fetching user orders: {e}")
            raise
    
    def _map_order_type(self, order_type: str) -> OrderTypeEnum:
        """Map Alpaca order type to enum."""
        type_map = {
            "market": OrderTypeEnum.MARKET,
            "limit": OrderTypeEnum.LIMIT,
            "stop": OrderTypeEnum.STOP,
            "stop_limit": OrderTypeEnum.STOP_LIMIT,
            "trailing_stop": OrderTypeEnum.TRAILING_STOP,
        }
        return type_map.get(order_type.lower(), OrderTypeEnum.MARKET)
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object."""
        if not dt_str:
            return None
        
        try:
            # Handle ISO format with timezone
            if isinstance(dt_str, str):
                # Remove timezone info for simplicity
                dt_str = dt_str.replace('Z', '+00:00')
                return datetime.fromisoformat(dt_str).replace(tzinfo=None)
            return dt_str
        except Exception as e:
            logger.warning(f"Error parsing datetime {dt_str}: {e}")
            return None


async def get_order_sync_service(session: AsyncSession) -> OrderSyncService:
    """
    Factory function to create OrderSyncService instance.
    
    Args:
        session: Database session
        
    Returns:
        OrderSyncService instance
    """
    return OrderSyncService(session)