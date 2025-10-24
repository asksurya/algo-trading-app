"""
Risk rule schemas for request/response validation.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.risk_rule import RiskRuleType, RiskRuleAction


class RiskRuleBase(BaseModel):
    """Base risk rule schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    rule_type: RiskRuleType
    threshold_value: float = Field(..., gt=0)
    threshold_unit: str = Field(default="percent", max_length=20)
    action: RiskRuleAction = Field(default=RiskRuleAction.ALERT)
    is_active: bool = Field(default=True)
    strategy_id: Optional[str] = None


class RiskRuleCreate(RiskRuleBase):
    """Schema for creating a risk rule."""
    pass


class RiskRuleUpdate(BaseModel):
    """Schema for updating a risk rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    rule_type: Optional[RiskRuleType] = None
    threshold_value: Optional[float] = Field(None, gt=0)
    threshold_unit: Optional[str] = Field(None, max_length=20)
    action: Optional[RiskRuleAction] = None
    is_active: Optional[bool] = None
    strategy_id: Optional[str] = None


class RiskRuleResponse(RiskRuleBase):
    """Schema for risk rule response."""
    id: str
    user_id: str
    breach_count: int
    last_breach_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RiskRuleBreachResponse(BaseModel):
    """Schema for risk rule breach information."""
    rule_id: str
    rule_name: str
    rule_type: RiskRuleType
    threshold_value: float
    threshold_unit: str
    current_value: float
    action: RiskRuleAction
    message: str
    timestamp: datetime


class RiskRuleTestRequest(BaseModel):
    """Request schema for testing a risk rule."""
    strategy_id: Optional[int] = None
    symbol: str = Field(..., min_length=1, max_length=20)
    order_qty: Optional[float] = Field(None, gt=0)
    order_value: Optional[float] = Field(None, gt=0)


class PositionSizeRequest(BaseModel):
    """Request schema for calculating position size."""
    strategy_id: Optional[int] = None
    symbol: str = Field(..., min_length=1, max_length=20)
    entry_price: float = Field(..., gt=0)
    stop_loss: Optional[float] = Field(None, gt=0)


class PositionSizeResponse(BaseModel):
    """Response schema for position size calculation."""
    symbol: str
    recommended_shares: int
    recommended_value: float
    max_loss: float
    risk_per_share: float
    account_value: float
    risk_percentage: float


class PortfolioRiskMetrics(BaseModel):
    """Response schema for portfolio risk metrics."""
    account_value: float
    buying_power: float
    total_position_value: float
    cash: float
    number_of_positions: int
    daily_pl: float
    daily_pl_percent: float
    total_unrealized_pl: float
    total_unrealized_pl_percent: float
    leverage: float
    max_drawdown_percent: float
