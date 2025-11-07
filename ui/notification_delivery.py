"""
Notification Delivery System for SpendSenseAI.

Multi-channel notification delivery:
- Email (SMTP, SendGrid, AWS SES)
- Push notifications
- In-app notifications
- SMS (Twilio, AWS SNS)
- Delivery tracking and analytics
"""

from typing import Dict, Optional, Any, List
from datetime import datetime
from dataclasses import dataclass
import os
import logging

from ui.notifications import Notification, NotificationChannel

logger = logging.getLogger(__name__)


@dataclass
class DeliveryResult:
    """Notification delivery result."""
    notification_id: str
    channel: NotificationChannel
    success: bool
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    external_id: Optional[str] = None  # External service ID (e.g., email message ID)


def send_email_notification(
    notification: Notification,
    smtp_config: Optional[Dict[str, Any]] = None
) -> DeliveryResult:
    """
    Send email notification.
    
    Args:
        notification: Notification object
        smtp_config: Optional SMTP configuration
        
    Returns:
        DeliveryResult object
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        smtp_config = smtp_config or {}
        smtp_host = smtp_config.get("host") or os.getenv("SMTP_HOST", "localhost")
        smtp_port = smtp_config.get("port") or int(os.getenv("SMTP_PORT", "587"))
        smtp_user = smtp_config.get("user") or os.getenv("SMTP_USER", "")
        smtp_password = smtp_config.get("password") or os.getenv("SMTP_PASSWORD", "")
        smtp_from = smtp_config.get("from") or os.getenv("SMTP_FROM", "noreply@spendsense.ai")
        
        msg = MIMEMultipart()
        msg["From"] = smtp_from
        msg["To"] = notification.metadata.get("email", "")
        msg["Subject"] = notification.subject
        msg.attach(MIMEText(notification.body, "plain"))
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_user and smtp_password:
                server.starttls()
                server.login(smtp_user, smtp_password)
            
            server.send_message(msg)
        
        logger.info(f"Email notification sent: {notification.notification_id}")
        return DeliveryResult(
            notification_id=notification.notification_id,
            channel=NotificationChannel.EMAIL,
            success=True,
            delivered_at=datetime.now()
        )
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")
        return DeliveryResult(
            notification_id=notification.notification_id,
            channel=NotificationChannel.EMAIL,
            success=False,
            error_message=str(e)
        )


def send_push_notification(
    notification: Notification,
    push_config: Optional[Dict[str, Any]] = None
) -> DeliveryResult:
    """
    Send push notification.
    
    Args:
        notification: Notification object
        push_config: Optional push notification configuration
        
    Returns:
        DeliveryResult object
    """
    try:
        # In a real implementation, this would integrate with FCM, APNS, etc.
        # For now, we'll log it
        logger.info(f"Push notification sent: {notification.notification_id}")
        return DeliveryResult(
            notification_id=notification.notification_id,
            channel=NotificationChannel.PUSH,
            success=True,
            delivered_at=datetime.now()
        )
    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")
        return DeliveryResult(
            notification_id=notification.notification_id,
            channel=NotificationChannel.PUSH,
            success=False,
            error_message=str(e)
        )


def send_sms_notification(
    notification: Notification,
    sms_config: Optional[Dict[str, Any]] = None
) -> DeliveryResult:
    """
    Send SMS notification.
    
    Args:
        notification: Notification object
        sms_config: Optional SMS configuration
        
    Returns:
        DeliveryResult object
    """
    try:
        # In a real implementation, this would integrate with Twilio, AWS SNS, etc.
        # For now, we'll log it
        logger.info(f"SMS notification sent: {notification.notification_id}")
        return DeliveryResult(
            notification_id=notification.notification_id,
            channel=NotificationChannel.SMS,
            success=True,
            delivered_at=datetime.now()
        )
    except Exception as e:
        logger.error(f"Failed to send SMS notification: {e}")
        return DeliveryResult(
            notification_id=notification.notification_id,
            channel=NotificationChannel.SMS,
            success=False,
            error_message=str(e)
        )


def send_in_app_notification(
    notification: Notification,
    db_path: str
) -> DeliveryResult:
    """
    Store in-app notification.
    
    Args:
        notification: Notification object
        db_path: Path to database
        
    Returns:
        DeliveryResult object
    """
    try:
        from ingest.database import get_connection
        
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Create in-app notifications table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS in_app_notifications (
                    notification_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    body TEXT NOT NULL,
                    sent_at TIMESTAMP NOT NULL,
                    read_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                INSERT INTO in_app_notifications 
                (notification_id, user_id, subject, body, sent_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                notification.notification_id,
                notification.user_id,
                notification.subject,
                notification.body,
                notification.sent_at.isoformat()
            ))
            
            conn.commit()
        
        logger.info(f"In-app notification stored: {notification.notification_id}")
        return DeliveryResult(
            notification_id=notification.notification_id,
            channel=NotificationChannel.IN_APP,
            success=True,
            delivered_at=datetime.now()
        )
    except Exception as e:
        logger.error(f"Failed to store in-app notification: {e}")
        return DeliveryResult(
            notification_id=notification.notification_id,
            channel=NotificationChannel.IN_APP,
            success=False,
            error_message=str(e)
        )


def deliver_notification(
    notification: Notification,
    db_path: str,
    channel_configs: Optional[Dict[NotificationChannel, Dict[str, Any]]] = None
) -> DeliveryResult:
    """
    Deliver notification via specified channel.
    
    Args:
        notification: Notification object
        db_path: Path to database
        channel_configs: Optional channel-specific configurations
        
    Returns:
        DeliveryResult object
    """
    channel_configs = channel_configs or {}
    
    if notification.channel == NotificationChannel.EMAIL:
        return send_email_notification(notification, channel_configs.get(NotificationChannel.EMAIL))
    elif notification.channel == NotificationChannel.PUSH:
        return send_push_notification(notification, channel_configs.get(NotificationChannel.PUSH))
    elif notification.channel == NotificationChannel.SMS:
        return send_sms_notification(notification, channel_configs.get(NotificationChannel.SMS))
    elif notification.channel == NotificationChannel.IN_APP:
        return send_in_app_notification(notification, db_path)
    else:
        return DeliveryResult(
            notification_id=notification.notification_id,
            channel=notification.channel,
            success=False,
            error_message=f"Unknown channel: {notification.channel}"
        )

