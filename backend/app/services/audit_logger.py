"""
Audit logging service for compliance and security.
"""
from datetime import datetime
from typing import Dict, Optional, Any
from enum import Enum
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession


class AuditEventType(str, Enum):
    """Types of audit events."""
    # Authentication events
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    
    # Trading events
    ORDER_PLACED = "order_placed"
    ORDER_CANCELED = "order_canceled"
    ORDER_FILLED = "order_filled"
    ORDER_REJECTED = "order_rejected"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    
    # Strategy events
    STRATEGY_CREATED = "strategy_created"
    STRATEGY_UPDATED = "strategy_updated"
    STRATEGY_DELETED = "strategy_deleted"
    STRATEGY_ACTIVATED = "strategy_activated"
    STRATEGY_DEACTIVATED = "strategy_deactivated"
    BACKTEST_RUN = "backtest_run"
    
    # Risk events
    RISK_RULE_TRIGGERED = "risk_rule_triggered"
    RISK_LIMIT_EXCEEDED = "risk_limit_exceeded"
    MARGIN_CALL = "margin_call"
    
    # Configuration events
    SETTINGS_CHANGED = "settings_changed"
    API_KEY_CREATED = "api_key_created"
    API_KEY_DELETED = "api_key_deleted"
    
    # Access events
    API_ACCESS = "api_access"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PERMISSION_DENIED = "permission_denied"


class AuditLogger:
    """
    Service for logging audit trails for compliance and security.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logging.getLogger("audit")
    
    async def log_event(
        self,
        user_id: str,
        event_type: AuditEventType,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: str = "info"
    ) -> Dict:
        """
        Log an audit event.
        
        Args:
            user_id: User ID who performed the action
            event_type: Type of audit event
            description: Human-readable description
            metadata: Additional structured data about the event
            ip_address: Client IP address
            user_agent: Client user agent
            severity: 'info', 'warning', 'error', 'critical'
        
        Returns:
            Audit log entry
        """
        timestamp = datetime.utcnow()
        
        # Create audit log entry
        audit_entry = {
            "timestamp": timestamp,
            "user_id": user_id,
            "event_type": event_type.value,
            "description": description,
            "metadata": metadata or {},
            "ip_address": ip_address,
            "user_agent": user_agent,
            "severity": severity
        }
        
        # TODO: Store in database once audit_log model is deployed
        # from app.models.audit_log import AuditLog
        # log_entry = AuditLog(**audit_entry)
        # self.session.add(log_entry)
        # await self.session.commit()
        
        # For now, log to application logs
        log_message = f"[AUDIT] {event_type.value} | User: {user_id} | {description}"
        if metadata:
            log_message += f" | Metadata: {json.dumps(metadata)}"
        
        if severity == "critical":
            self.logger.critical(log_message)
        elif severity == "error":
            self.logger.error(log_message)
        elif severity == "warning":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        return audit_entry
    
    async def log_trade(self, user_id: str, trade_data: Dict) -> Dict:
        """Log a trade execution for audit trail."""
        return await self.log_event(
            user_id=user_id,
            event_type=AuditEventType.ORDER_FILLED,
            description=f"Trade executed: {trade_data.get('side')} {trade_data.get('qty')} {trade_data.get('symbol')} @ ${trade_data.get('price')}",
            metadata=trade_data,
            severity="info"
        )
    
    async def log_order(self, user_id: str, order_data: Dict, event_type: AuditEventType) -> Dict:
        """Log an order event."""
        return await self.log_event(
            user_id=user_id,
            event_type=event_type,
            description=f"Order {event_type.value}: {order_data.get('symbol')} {order_data.get('qty')} shares",
            metadata=order_data,
            severity="info"
        )
    
    async def log_risk_event(self, user_id: str, risk_event: Dict) -> Dict:
        """Log a risk management event."""
        return await self.log_event(
            user_id=user_id,
            event_type=AuditEventType.RISK_RULE_TRIGGERED,
            description=risk_event.get('description', 'Risk rule triggered'),
            metadata=risk_event,
            severity="warning"
        )
    
    async def log_security_event(self, user_id: str, event_type: AuditEventType, details: Dict, ip_address: Optional[str] = None) -> Dict:
        """Log a security-related event."""
        return await self.log_event(
            user_id=user_id,
            event_type=event_type,
            description=details.get('description', 'Security event'),
            metadata=details,
            ip_address=ip_address,
            severity="warning" if event_type in [AuditEventType.LOGIN_FAILED, AuditEventType.UNAUTHORIZED_ACCESS] else "info"
        )
    
    async def get_audit_trail(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """
        Query audit trail with filters.
        
        Args:
            user_id: Filter by user ID
            event_type: Filter by event type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results
        
        Returns:
            List of audit log entries
        """
        # TODO: Implement database query once models are deployed
        # For now, return empty list
        return []
    
    async def generate_compliance_report(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Generate compliance report for a user within a date range.
        
        Includes:
        - All trades
        - Order history
        - Risk events
        - Configuration changes
        """
        # TODO: Implement once audit log queries are available
        return {
            "user_id": user_id,
            "report_period": {
                "start": start_date,
                "end": end_date
            },
            "total_trades": 0,
            "total_orders": 0,
            "risk_events": 0,
            "security_events": 0,
            "events": []
        }


async def get_audit_logger(session: AsyncSession) -> AuditLogger:
    """Get audit logger instance."""
    return AuditLogger(session)
