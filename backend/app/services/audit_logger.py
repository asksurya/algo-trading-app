"""
Audit logging service for compliance and security.
"""
from datetime import datetime
from typing import Dict, Optional, Any, List
import json
import logging

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AuditEventType
from app.models.audit_log import AuditLog


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
        # Create audit log entry
        log_entry = AuditLog(
            user_id=user_id,
            event_type=event_type,
            description=description,
            metadata_data=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity
        )
        
        self.session.add(log_entry)
        await self.session.commit()
        await self.session.refresh(log_entry)
        
        # For now, log to application logs as well
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

        return {
            "id": log_entry.id,
            "timestamp": log_entry.created_at,
            "user_id": log_entry.user_id,
            "event_type": log_entry.event_type.value,
            "description": log_entry.description,
            "metadata": log_entry.metadata_data,
            "ip_address": log_entry.ip_address,
            "user_agent": log_entry.user_agent,
            "severity": log_entry.severity
        }
    
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
    ) -> List[AuditLog]:
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
        query = select(AuditLog)

        filters = []
        if user_id:
            filters.append(AuditLog.user_id == user_id)
        if event_type:
            filters.append(AuditLog.event_type == event_type)
        if start_date:
            filters.append(AuditLog.created_at >= start_date)
        if end_date:
            filters.append(AuditLog.created_at <= end_date)

        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(AuditLog.created_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()
    
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
        # Query all events for the user in the date range
        query = select(AuditLog).where(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.created_at >= start_date,
                AuditLog.created_at <= end_date
            )
        ).order_by(AuditLog.created_at.asc())

        result = await self.session.execute(query)
        logs = result.scalars().all()

        # Categorize events
        trades = []
        orders = []
        risk_events = []
        security_events = []
        config_changes = []
        other_events = []

        for log in logs:
            event_data = {
                "timestamp": log.created_at,
                "event_type": log.event_type.value,
                "description": log.description,
                "metadata": log.metadata_data,
                "ip_address": log.ip_address,
                "severity": log.severity
            }

            # Map event types to categories
            if log.event_type in [
                AuditEventType.ORDER_FILLED,
                AuditEventType.POSITION_OPENED,
                AuditEventType.POSITION_CLOSED
            ]:
                trades.append(event_data)
            elif log.event_type in [
                AuditEventType.ORDER_PLACED,
                AuditEventType.ORDER_CANCELED,
                AuditEventType.ORDER_REJECTED
            ]:
                orders.append(event_data)
            elif log.event_type in [
                AuditEventType.RISK_RULE_TRIGGERED,
                AuditEventType.RISK_LIMIT_EXCEEDED,
                AuditEventType.MARGIN_CALL
            ]:
                risk_events.append(event_data)
            elif log.event_type in [
                AuditEventType.LOGIN,
                AuditEventType.LOGOUT,
                AuditEventType.LOGIN_FAILED,
                AuditEventType.PASSWORD_CHANGE,
                AuditEventType.API_ACCESS,
                AuditEventType.UNAUTHORIZED_ACCESS,
                AuditEventType.PERMISSION_DENIED
            ]:
                security_events.append(event_data)
            elif log.event_type in [
                AuditEventType.SETTINGS_CHANGED,
                AuditEventType.API_KEY_CREATED,
                AuditEventType.API_KEY_DELETED
            ]:
                config_changes.append(event_data)
            else:
                other_events.append(event_data)

        return {
            "user_id": user_id,
            "report_period": {
                "start": start_date,
                "end": end_date
            },
            "summary": {
                "total_trades": len(trades),
                "total_orders": len(orders),
                "risk_events": len(risk_events),
                "security_events": len(security_events),
                "config_changes": len(config_changes),
                "total_events": len(logs)
            },
            "details": {
                "trades": trades,
                "orders": orders,
                "risk_events": risk_events,
                "security_events": security_events,
                "configuration_changes": config_changes,
                "other_events": other_events
            }
        }


async def get_audit_logger(session: AsyncSession) -> AuditLogger:
    """Get audit logger instance."""
    return AuditLogger(session)
