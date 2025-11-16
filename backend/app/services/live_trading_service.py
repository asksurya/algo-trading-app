from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

class LiveTradingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_system_status(self, user_id: int):
        # Dummy implementation
        return {"is_running": True, "active_strategies": 0, "total_pnl": 0, "last_trade_at": None}

    async def get_portfolio(self, user_id: int):
        # Dummy implementation
        return {"total_value": 0, "cash": 0, "positions": []}

    async def perform_action(self, user_id: int, action: str):
        # Dummy implementation
        return {"success": True}

    async def get_active_strategies(self, user_id: int):
        # Dummy implementation
        return []

    async def get_orders(self, user_id: int, limit: int):
        # Dummy implementation
        return []

def get_live_trading_service(db: AsyncSession = Depends(get_db)):
    return LiveTradingService(db)
