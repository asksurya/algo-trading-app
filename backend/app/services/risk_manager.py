"""
Risk management service for evaluating trading rules and calculating position sizes.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import numpy as np

from app.models.risk_rule import RiskRule, RiskRuleType, RiskRuleAction
from app.models.order import Order, OrderStatusEnum
from app.models.trade import Trade, Position
from app.schemas.risk_rule import (
    RiskRuleBreachResponse,
    PositionSizeRequest,
    PositionSizeResponse
)
from app.integrations.alpaca_client import AlpacaClient


class RiskManager:
    """Service for managing trading risk and position sizing."""
    
    def __init__(self, db: Session, alpaca_client: AlpacaClient):
        self.db = db
        self.alpaca = alpaca_client
    
    async def evaluate_rules(
        self,
        user_id: str,
        strategy_id: Optional[str] = None,
        symbol: Optional[str] = None,
        order_qty: Optional[float] = None,
        order_value: Optional[float] = None
    ) -> List[RiskRuleBreachResponse]:
        """
        Evaluate all active risk rules for a user/strategy.
        
        Args:
            user_id: User ID
            strategy_id: Optional strategy ID to filter rules
            symbol: Symbol being traded
            order_qty: Proposed order quantity
            order_value: Proposed order value
            
        Returns:
            List of rule breaches
        """
        breaches = []
        
        # Get active rules
        query = self.db.query(RiskRule).filter(
            and_(
                RiskRule.user_id == user_id,
                RiskRule.is_active == True
            )
        )
        
        if strategy_id:
            query = query.filter(
                or_(
                    RiskRule.strategy_id == strategy_id,
                    RiskRule.strategy_id.is_(None)  # Global rules
                )
            )
        
        rules = query.all()
        
        # Get account info
        account = await self.alpaca.get_account()
        equity = float(account.equity)
        
        # Get current positions
        positions = await self.alpaca.get_positions()
        
        # Evaluate each rule
        for rule in rules:
            breach = await self._evaluate_single_rule(
                rule, equity, positions, symbol, order_qty, order_value
            )
            if breach:
                breaches.append(breach)
                
                # Update breach count
                rule.breach_count += 1
                rule.last_breach_at = datetime.now(datetime.UTC)
                self.db.commit()
        
        return breaches
    
    async def _evaluate_single_rule(
        self,
        rule: RiskRule,
        equity: float,
        positions: List[Any],
        symbol: Optional[str],
        order_qty: Optional[float],
        order_value: Optional[float]
    ) -> Optional[RiskRuleBreachResponse]:
        """Evaluate a single risk rule."""
        
        if rule.rule_type == RiskRuleType.MAX_POSITION_SIZE:
            return await self._check_max_position_size(
                rule, equity, symbol, order_value
            )
        
        elif rule.rule_type == RiskRuleType.MAX_DAILY_LOSS:
            return await self._check_max_daily_loss(rule, equity)
        
        elif rule.rule_type == RiskRuleType.MAX_DRAWDOWN:
            return await self._check_max_drawdown(rule, equity)
        
        elif rule.rule_type == RiskRuleType.POSITION_LIMIT:
            return await self._check_position_limit(rule, positions)
        
        elif rule.rule_type == RiskRuleType.MAX_LEVERAGE:
            return await self._check_max_leverage(rule, equity, positions)
        
        # Add other rule type checks as needed
        
        return None
    
    async def _check_max_position_size(
        self,
        rule: RiskRule,
        equity: float,
        symbol: Optional[str],
        order_value: Optional[float]
    ) -> Optional[RiskRuleBreachResponse]:
        """Check if position size exceeds maximum."""
        if not order_value:
            return None
        
        if rule.threshold_unit == "percent":
            max_value = equity * (rule.threshold_value / 100)
        else:  # dollars
            max_value = rule.threshold_value
        
        if order_value > max_value:
            return RiskRuleBreachResponse(
                rule_id=rule.id,
                rule_name=rule.name,
                rule_type=rule.rule_type,
                threshold_value=rule.threshold_value,
                threshold_unit=rule.threshold_unit,
                current_value=order_value,
                action=rule.action,
                message=f"Position size ${order_value:,.2f} exceeds maximum ${max_value:,.2f}",
                timestamp=datetime.now(datetime.UTC)
            )
        
        return None
    
    async def _check_max_daily_loss(
        self,
        rule: RiskRule,
        equity: float
    ) -> Optional[RiskRuleBreachResponse]:
        """Check if daily loss exceeds maximum."""
        # Get today's trades
        today_start = datetime.now(datetime.UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        
        trades = self.db.query(Trade).filter(
            and_(
                Trade.user_id == rule.user_id,
                Trade.created_at >= today_start
            )
        ).all()
        
        daily_pnl = sum(t.profit_loss or 0 for t in trades)
        
        if rule.threshold_unit == "percent":
            max_loss = equity * (rule.threshold_value / 100)
        else:  # dollars
            max_loss = rule.threshold_value
        
        if abs(daily_pnl) > max_loss and daily_pnl < 0:
            return RiskRuleBreachResponse(
                rule_id=rule.id,
                rule_name=rule.name,
                rule_type=rule.rule_type,
                threshold_value=rule.threshold_value,
                threshold_unit=rule.threshold_unit,
                current_value=abs(daily_pnl),
                action=rule.action,
                message=f"Daily loss ${abs(daily_pnl):,.2f} exceeds maximum ${max_loss:,.2f}",
                timestamp=datetime.now(datetime.UTC)
            )
        
        return None
    
    async def _check_max_drawdown(
        self,
        rule: RiskRule,
        equity: float
    ) -> Optional[RiskRuleBreachResponse]:
        """Check if drawdown exceeds maximum."""
        # Get historical equity peak (simplified - would need equity tracking)
        # For now, use a simple approximation
        account = await self.alpaca.get_account()
        equity_peak = float(account.equity)  # Simplified
        
        current_drawdown = ((equity_peak - equity) / equity_peak) * 100
        
        if current_drawdown > rule.threshold_value:
            return RiskRuleBreachResponse(
                rule_id=rule.id,
                rule_name=rule.name,
                rule_type=rule.rule_type,
                threshold_value=rule.threshold_value,
                threshold_unit=rule.threshold_unit,
                current_value=current_drawdown,
                action=rule.action,
                message=f"Drawdown {current_drawdown:.2f}% exceeds maximum {rule.threshold_value:.2f}%",
                timestamp=datetime.now(datetime.UTC)
            )
        
        return None
    
    async def _check_position_limit(
        self,
        rule: RiskRule,
        positions: List[Any]
    ) -> Optional[RiskRuleBreachResponse]:
        """Check if number of positions exceeds limit."""
        position_count = len(positions)
        
        if position_count >= rule.threshold_value:
            return RiskRuleBreachResponse(
                rule_id=rule.id,
                rule_name=rule.name,
                rule_type=rule.rule_type,
                threshold_value=rule.threshold_value,
                threshold_unit="count",
                current_value=position_count,
                action=rule.action,
                message=f"Position count {position_count} exceeds maximum {int(rule.threshold_value)}",
                timestamp=datetime.now(datetime.UTC)
            )
        
        return None
    
    async def _check_max_leverage(
        self,
        rule: RiskRule,
        equity: float,
        positions: List[Any]
    ) -> Optional[RiskRuleBreachResponse]:
        """Check if leverage exceeds maximum."""
        total_position_value = sum(
            abs(float(p.market_value)) for p in positions
        )
        
        current_leverage = total_position_value / equity if equity > 0 else 0
        
        if current_leverage > rule.threshold_value:
            return RiskRuleBreachResponse(
                rule_id=rule.id,
                rule_name=rule.name,
                rule_type=rule.rule_type,
                threshold_value=rule.threshold_value,
                threshold_unit="ratio",
                current_value=current_leverage,
                action=rule.action,
                message=f"Leverage {current_leverage:.2f}x exceeds maximum {rule.threshold_value:.2f}x",
                timestamp=datetime.now(datetime.UTC)
            )
        
        return None
    
    async def calculate_position_size(
        self,
        request: PositionSizeRequest,
        user_id: str
    ) -> PositionSizeResponse:
        """
        Calculate recommended position size based on risk parameters.
        
        Uses the formula:
        Position Size = (Account Risk $) / (Entry Price - Stop Loss Price)
        """
        warnings = []
        
        # Get account info
        account = await self.alpaca.get_account()
        equity = float(account.equity)
        
        # Calculate risk amount
        risk_amount = equity * (request.account_risk_percent / 100)
        
        # Calculate position size
        if request.stop_loss_price and request.entry_price > request.stop_loss_price:
            risk_per_share = request.entry_price - request.stop_loss_price
            recommended_shares = int(risk_amount / risk_per_share)
        else:
            # If no stop loss, use a conservative 2% of equity per position
            recommended_shares = int((equity * 0.02) / request.entry_price)
            warnings.append("No stop loss provided - using conservative position sizing")
        
        # Ensure minimum 1 share
        recommended_shares = max(1, recommended_shares)
        
        position_value = recommended_shares * request.entry_price
        
        # Check against risk rules
        breaches = await self.evaluate_rules(
            user_id=user_id,
            symbol=request.symbol,
            order_value=position_value
        )
        
        if breaches:
            for breach in breaches:
                warnings.append(f"Risk rule '{breach.rule_name}' would be breached")
        
        return PositionSizeResponse(
            symbol=request.symbol,
            recommended_shares=recommended_shares,
            position_value=position_value,
            risk_amount=risk_amount,
            risk_percent=request.account_risk_percent,
            stop_loss_price=request.stop_loss_price,
            entry_price=request.entry_price,
            account_equity=equity,
            warnings=warnings
        )
    
    async def get_portfolio_risk_metrics(self, user_id: str) -> Dict[str, Any]:
        """
        Get current portfolio risk metrics.
        
        Returns:
            Dictionary of risk metrics
        """
        # Get account and positions
        account = await self.alpaca.get_account()
        positions = await self.alpaca.get_positions()
        
        equity = float(account.equity)
        
        # Calculate metrics
        total_position_value = sum(abs(float(p.market_value)) for p in positions)
        leverage = total_position_value / equity if equity > 0 else 0
        
        # Get today's P&L
        today_start = datetime.now(datetime.UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        trades = self.db.query(Trade).filter(
            and_(
                Trade.user_id == user_id,
                Trade.created_at >= today_start
            )
        ).all()
        
        daily_pnl = sum(t.profit_loss or 0 for t in trades)
        daily_pnl_percent = (daily_pnl / equity * 100) if equity > 0 else 0
        
        # Position concentration
        largest_position = max(
            (abs(float(p.market_value)) for p in positions),
            default=0
        )
        concentration = (largest_position / equity * 100) if equity > 0 else 0
        
        return {
            "equity": equity,
            "position_count": len(positions),
            "total_position_value": total_position_value,
            "leverage": leverage,
            "daily_pnl": daily_pnl,
            "daily_pnl_percent": daily_pnl_percent,
            "largest_position_value": largest_position,
            "concentration_percent": concentration,
            "buying_power": float(account.buying_power),
            "cash": float(account.cash)
        }
