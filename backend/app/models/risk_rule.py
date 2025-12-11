"""
Risk management rules model.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Boolean, DateTime, Enum as SQLEnum, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from app.models.base import Base
from app.models.enums import RiskRuleType, RiskRuleAction



class RiskRule(Base):
    """Risk management rules for strategies."""
    
    __tablename__ = "risk_rules"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # Foreign keys
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    strategy_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("strategies.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Rule configuration
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    rule_type: Mapped[RiskRuleType] = mapped_column(
        SQLEnum(RiskRuleType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    
    # Threshold values
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="percent"
    )  # percent, dollars, count, ratio
    
    # Action configuration
    action: Mapped[RiskRuleAction] = mapped_column(
        SQLEnum(RiskRuleAction, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=RiskRuleAction.ALERT
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    breach_count: Mapped[int] = mapped_column(default=0, nullable=False)
    last_breach_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    user = relationship("User", back_populates="risk_rules")
    strategy = relationship("Strategy", back_populates="risk_rules")
    
    def __repr__(self) -> str:
        return f"<RiskRule(id={self.id}, name={self.name}, type={self.rule_type})>"
