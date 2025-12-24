"""
Email delivery service using SMTP.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Email message structure."""
    to: List[str]
    subject: str
    body: str
    html_body: Optional[str] = None


class EmailService:
    """SMTP email delivery service."""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAIL_FROM
        self.enabled = bool(self.smtp_host and self.smtp_user)

    async def send_email(self, message: EmailMessage) -> bool:
        """Send an email message."""
        if not self.enabled:
            logger.warning("Email service not configured, skipping send")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject
            msg["From"] = self.from_email
            msg["To"] = ", ".join(message.to)

            # Add plain text
            msg.attach(MIMEText(message.body, "plain"))

            # Add HTML if provided
            if message.html_body:
                msg.attach(MIMEText(message.html_body, "html"))

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, message.to, msg.as_string())

            logger.info(f"Email sent to {message.to}: {message.subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    async def send_trade_notification(
        self,
        to_email: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        strategy_name: str
    ) -> bool:
        """Send trade execution notification."""
        subject = f"Trade Executed: {side.upper()} {quantity} {symbol}"
        body = f"""
Trade Notification

Strategy: {strategy_name}
Action: {side.upper()}
Symbol: {symbol}
Quantity: {quantity}
Price: ${price:,.2f}
Total Value: ${quantity * price:,.2f}

This is an automated notification from your Algo Trading Platform.
        """

        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
<h2>Trade Executed</h2>
<table style="border-collapse: collapse;">
<tr><td><strong>Strategy:</strong></td><td>{strategy_name}</td></tr>
<tr><td><strong>Action:</strong></td><td style="color: {'green' if side.lower() == 'buy' else 'red'}">{side.upper()}</td></tr>
<tr><td><strong>Symbol:</strong></td><td>{symbol}</td></tr>
<tr><td><strong>Quantity:</strong></td><td>{quantity}</td></tr>
<tr><td><strong>Price:</strong></td><td>${price:,.2f}</td></tr>
<tr><td><strong>Total:</strong></td><td>${quantity * price:,.2f}</td></tr>
</table>
</body>
</html>
        """

        return await self.send_email(EmailMessage(
            to=[to_email],
            subject=subject,
            body=body,
            html_body=html_body
        ))


_email_service: Optional[EmailService] = None

def get_email_service() -> EmailService:
    """Get singleton email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
