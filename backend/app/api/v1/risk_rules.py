"""
Risk Rules API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from app.models.user import User
from app.models.risk_rule import RiskRule
from app.models.strategy import Strategy
from app.schemas.risk_rule import (
    RiskRuleCreate,
    RiskRuleUpdate,
    RiskRuleResponse,
    RiskRuleTestRequest,
    PositionSizeRequest,
    PositionSizeResponse,
    PortfolioRiskMetrics
)
from app.services.risk_manager import RiskManager
from app.integrations.alpaca_client import get_alpaca_client
from app.dependencies import get_current_active_user

router = APIRouter()


@router.post("", response_model=RiskRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_risk_rule(
    rule_data: RiskRuleCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new risk rule"""
    
    # Verify strategy ownership if strategy_id is provided
    if rule_data.strategy_id:
        result = await db.execute(
            select(Strategy).where(
                and_(
                    Strategy.id == rule_data.strategy_id,
                    Strategy.user_id == current_user.id
                )
            )
        )
        strategy = result.scalar_one_or_none()
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )
    
    # Create risk rule
    risk_rule = RiskRule(
        user_id=current_user.id,
        **rule_data.model_dump()
    )
    
    db.add(risk_rule)
    await db.commit()
    await db.refresh(risk_rule)
    
    return risk_rule


@router.get("", response_model=List[RiskRuleResponse])
async def list_risk_rules(
    strategy_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all risk rules for the current user"""
    
    query = select(RiskRule).where(RiskRule.user_id == current_user.id)
    
    if strategy_id is not None:
        query = query.where(RiskRule.strategy_id == strategy_id)
    
    if is_active is not None:
        query = query.where(RiskRule.is_active == is_active)
    
    query = query.order_by(RiskRule.created_at.desc())
    
    result = await db.execute(query)
    risk_rules = result.scalars().all()
    
    return risk_rules


@router.get("/portfolio-risk", response_model=PortfolioRiskMetrics)
async def get_portfolio_risk(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current portfolio risk metrics"""
    
    try:
        alpaca_client = get_alpaca_client(current_user)
        risk_manager = RiskManager(db, alpaca_client)
        
        metrics = await risk_manager.get_portfolio_risk_metrics(current_user.id)
        
        return PortfolioRiskMetrics(**metrics)
    except Exception as e:
        # Return default metrics if Alpaca API fails
        return PortfolioRiskMetrics(
            account_value=0.0,
            buying_power=0.0,
            total_position_value=0.0,
            cash=0.0,
            number_of_positions=0,
            daily_pl=0.0,
            daily_pl_percent=0.0,
            total_unrealized_pl=0.0,
            total_unrealized_pl_percent=0.0,
            leverage=0.0,
            max_drawdown_percent=0.0
        )


@router.get("/{rule_id}", response_model=RiskRuleResponse)
async def get_risk_rule(
    rule_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific risk rule"""
    
    result = await db.execute(
        select(RiskRule).where(
            and_(
                RiskRule.id == rule_id,
                RiskRule.user_id == current_user.id
            )
        )
    )
    risk_rule = result.scalar_one_or_none()
    
    if not risk_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk rule not found"
        )
    
    return risk_rule


@router.put("/{rule_id}", response_model=RiskRuleResponse)
async def update_risk_rule(
    rule_id: str,
    rule_update: RiskRuleUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a risk rule"""
    
    result = await db.execute(
        select(RiskRule).where(
            and_(
                RiskRule.id == rule_id,
                RiskRule.user_id == current_user.id
            )
        )
    )
    risk_rule = result.scalar_one_or_none()
    
    if not risk_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk rule not found"
        )
    
    # Update fields
    update_data = rule_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(risk_rule, field, value)
    
    await db.commit()
    await db.refresh(risk_rule)
    
    return risk_rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_risk_rule(
    rule_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a risk rule"""
    
    result = await db.execute(
        select(RiskRule).where(
            and_(
                RiskRule.id == rule_id,
                RiskRule.user_id == current_user.id
            )
        )
    )
    risk_rule = result.scalar_one_or_none()
    
    if not risk_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk rule not found"
        )
    
    await db.delete(risk_rule)
    await db.commit()


@router.post("/test")
async def test_risk_rule(
    test_request: RiskRuleTestRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Test a risk rule against current portfolio state"""
    
    alpaca_client = get_alpaca_client(current_user)
    risk_manager = RiskManager(db, alpaca_client)
    
    breaches = await risk_manager.evaluate_rules(
        user_id=current_user.id,
        strategy_id=test_request.strategy_id,
        symbol=test_request.symbol,
        order_qty=test_request.order_qty,
        order_value=test_request.order_value
    )
    
    return {
        "would_block": any(b.action == "BLOCK" for b in breaches),
        "would_warn": any(b.action == "WARN" for b in breaches),
        "breaches": [
            {
                "rule_id": b.rule_id,
                "rule_name": b.rule_name,
                "rule_type": b.rule_type,
                "threshold": float(b.threshold),
                "current_value": float(b.current_value),
                "action": b.action,
                "message": b.message
            }
            for b in breaches
        ]
    }


@router.post("/calculate-position-size", response_model=PositionSizeResponse)
async def calculate_position_size(
    request: PositionSizeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Calculate recommended position size based on risk rules"""
    
    try:
        alpaca_client = get_alpaca_client(current_user)
        risk_manager = RiskManager(db, alpaca_client)
        
        position_size = await risk_manager.calculate_position_size(
            user_id=current_user.id,
            strategy_id=request.strategy_id,
            symbol=request.symbol,
            entry_price=request.entry_price,
            stop_loss=request.stop_loss
        )
        
        return PositionSizeResponse(
            symbol=request.symbol,
            recommended_shares=position_size["recommended_shares"],
            recommended_value=position_size["recommended_value"],
            max_loss=position_size["max_loss"],
            risk_per_share=position_size["risk_per_share"],
            account_value=position_size["account_value"],
            risk_percentage=position_size["risk_percentage"]
        )
    except Exception as e:
        # Return safe defaults if calculation fails
        risk_per_share = abs(request.entry_price - (request.stop_loss or request.entry_price * 0.95))
        return PositionSizeResponse(
            symbol=request.symbol,
            recommended_shares=0,
            recommended_value=0.0,
            max_loss=0.0,
            risk_per_share=risk_per_share,
            account_value=0.0,
            risk_percentage=0.0
        )
