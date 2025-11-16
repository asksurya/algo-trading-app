from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class LiveTradingStatusResponse(BaseModel):
    is_running: bool
    active_strategies: int
    total_pnl: Decimal
    last_trade_at: Optional[datetime]

class LiveTradingPortfolioResponse(BaseModel):
    total_value: Decimal
    cash: Decimal
    positions: List[dict]

class LiveTradingActionRequest(BaseModel):
    action: str # e.g., "pause", "resume"
