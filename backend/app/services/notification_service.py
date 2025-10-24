"""
Notification service for sending alerts and notifications
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime, time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.notification import Notification, NotificationPreference, NotificationType, NotificationChannel
from app.models.user import User


class NotificationService:
    """Service for creating and sending notifications"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from = os.getenv("SMTP_FROM", "noreply@algotrading.com")
    
    async def create_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: str = "MEDIUM",
        data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Create a new notification
        
        Args:
            user_id: User to notify
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            priority: Priority level (LOW, MEDIUM, HIGH, URGENT)
            data: Additional JSON data
            
        Returns:
            Created notification
        """
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            priority=priority,
            data=data
        )
        
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        
        # Send notification through appropriate channels
        await self._send_notification(notification)
        
        return notification
    
    async def _send_notification(self, notification: Notification):
        """Send notification through configured channels"""
        
        # Get user preferences
        result = await self.db.execute(
            select(NotificationPreference).where(
                and_(
                    NotificationPreference.user_id == notification.user_id,
                    NotificationPreference.type == notification.type,
                    NotificationPreference.is_enabled == True
                )
            )
        )
        preferences = result.scalars().all()
        
        # If no preferences found, use defaults (in-app only)
        if not preferences:
            # In-app notifications are always created in the database
            return
        
        # Check quiet hours
        if not await self._is_within_quiet_hours(notification.user_id):
            for pref in preferences:
                if NotificationChannel.EMAIL in pref.channels:
                    await self._send_email(notification)
                
                if NotificationChannel.WEBSOCKET in pref.channels:
                    await self._send_websocket(notification)
                
                # SMS and Push would be implemented here
    
    async def _is_within_quiet_hours(self, user_id: int) -> bool:
        """Check if current time is within user's quiet hours"""
        
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id
            ).limit(1)
        )
        pref = result.scalar_one_or_none()
        
        if not pref or not pref.quiet_hours_start or not pref.quiet_hours_end:
            return False
        
        current_time = datetime.now().time()
        start = pref.quiet_hours_start
        end = pref.quiet_hours_end
        
        # Handle cases where quiet hours span midnight
        if start < end:
            return start <= current_time <= end
        else:
            return current_time >= start or current_time <= end
    
    async def _send_email(self, notification: Notification):
        """Send notification via email"""
        
        if not all([self.smtp_user, self.smtp_password]):
            print("Email not configured, skipping email notification")
            return
        
        try:
            # Get user email
            result = await self.db.execute(
                select(User).where(User.id == notification.user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.email:
                return
            
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{notification.priority}] {notification.title}"
            msg['From'] = self.smtp_from
            msg['To'] = user.email
            
            # Create HTML body
            html = f"""
            <html>
              <head></head>
              <body>
                <h2>{notification.title}</h2>
                <p>{notification.message}</p>
                <p><small>Priority: {notification.priority} | Type: {notification.type}</small></p>
              </body>
            </html>
            """
            
            # Attach parts
            text_part = MIMEText(notification.message, 'plain')
            html_part = MIMEText(html, 'html')
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"Email sent to {user.email} for notification {notification.id}")
            
        except Exception as e:
            print(f"Failed to send email notification: {str(e)}")
    
    async def _send_websocket(self, notification: Notification):
        """
        Send notification via WebSocket
        This is a placeholder - actual implementation would use a WebSocket manager
        """
        # TODO: Implement WebSocket notification
        # This would typically broadcast to connected clients
        print(f"WebSocket notification for user {notification.user_id}: {notification.title}")
    
    async def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        
        result = await self.db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            )
        )
        notification = result.scalar_one_or_none()
        
        if not notification:
            return False
        
        notification.is_read = True
        await self.db.commit()
        
        return True
    
    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        
        result = await self.db.execute(
            select(Notification).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
        )
        notifications = result.scalars().all()
        
        count = 0
        for notification in notifications:
            notification.is_read = True
            count += 1
        
        await self.db.commit()
        
        return count
    
    async def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete a notification"""
        
        result = await self.db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            )
        )
        notification = result.scalar_one_or_none()
        
        if not notification:
            return False
        
        await self.db.delete(notification)
        await self.db.commit()
        
        return True
    
    async def get_notification_stats(self, user_id: int) -> Dict[str, Any]:
        """Get notification statistics for a user"""
        
        result = await self.db.execute(
            select(Notification).where(Notification.user_id == user_id)
        )
        all_notifications = result.scalars().all()
        
        # Count by type
        by_type = {}
        for notification in all_notifications:
            notification_type = str(notification.type.value if hasattr(notification.type, 'value') else notification.type)
            by_type[notification_type] = by_type.get(notification_type, 0) + 1
        
        # Count by priority
        by_priority = {}
        for notification in all_notifications:
            priority = str(notification.priority.value if hasattr(notification.priority, 'value') else notification.priority)
            by_priority[priority] = by_priority.get(priority, 0) + 1
        
        # Count unread and recent (last 24 hours)
        unread_count = sum(1 for n in all_notifications if not n.is_read)
        recent_count = sum(1 for n in all_notifications if (datetime.now() - n.created_at).days == 0)
        
        return {
            "total_unread": unread_count,
            "by_type": by_type,
            "by_priority": by_priority,
            "recent_count": recent_count
        }
    
    # Convenience methods for common notification types
    
    async def notify_order_filled(self, user_id: int, order_data: Dict[str, Any]):
        """Send notification when an order is filled"""
        await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.ORDER_FILLED,
            title="Order Filled",
            message=f"Your {order_data.get('side')} order for {order_data.get('qty')} shares of {order_data.get('symbol')} has been filled at ${order_data.get('filled_avg_price')}",
            priority="MEDIUM",
            data=order_data
        )
    
    async def notify_risk_breach(self, user_id: int, breach_data: Dict[str, Any]):
        """Send notification when a risk rule is breached"""
        await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.RISK_BREACH,
            title="Risk Rule Breached",
            message=f"Risk rule '{breach_data.get('rule_name')}' has been breached. {breach_data.get('message')}",
            priority="HIGH",
            data=breach_data
        )
    
    async def notify_strategy_error(self, user_id: int, error_data: Dict[str, Any]):
        """Send notification when a strategy encounters an error"""
        await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.STRATEGY_ERROR,
            title="Strategy Error",
            message=f"Strategy '{error_data.get('strategy_name')}' encountered an error: {error_data.get('error')}",
            priority="HIGH",
            data=error_data
        )
    
    async def notify_position_update(self, user_id: int, position_data: Dict[str, Any]):
        """Send notification for position updates"""
        await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.POSITION_UPDATE,
            title="Position Update",
            message=f"Position in {position_data.get('symbol')} updated. Current P/L: ${position_data.get('unrealized_pl')}",
            priority="LOW",
            data=position_data
        )
    
    async def notify_system_alert(self, user_id: int, alert_data: Dict[str, Any]):
        """Send system alert notification"""
        await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.SYSTEM_ALERT,
            title="System Alert",
            message=alert_data.get('message', 'System alert'),
            priority=alert_data.get('priority', 'MEDIUM'),
            data=alert_data
        )
