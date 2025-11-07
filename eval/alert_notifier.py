"""
Alert Notification System for SpendSenseAI.

Sends alerts via multiple channels:
- Email (SMTP, SendGrid, AWS SES)
- Slack webhooks
- PagerDuty integration
- Console logging (for development)
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import os
import logging

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Notification channels for alerts."""
    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    CONSOLE = "console"


@dataclass
class AlertConfig:
    """Alert notification configuration."""
    channel: NotificationChannel
    enabled: bool = True
    webhook_url: Optional[str] = None
    email_recipients: List[str] = None
    slack_channel: Optional[str] = None
    pagerduty_service_key: Optional[str] = None
    severity_filter: List[str] = None  # Only send alerts for these severities
    
    def __post_init__(self):
        if self.email_recipients is None:
            self.email_recipients = []
        if self.severity_filter is None:
            self.severity_filter = ["critical", "warning", "info"]


@dataclass
class AlertNotification:
    """Alert notification record."""
    alert_id: str
    channel: NotificationChannel
    sent_at: datetime
    success: bool
    error_message: Optional[str] = None


def send_console_alert(alert: Dict[str, Any], config: AlertConfig) -> bool:
    """
    Send alert to console (for development/testing).
    
    Args:
        alert: Alert dictionary
        config: AlertConfig object
        
    Returns:
        True if successful, False otherwise
    """
    try:
        severity_icon = {
            "critical": "🔴",
            "warning": "🟡",
            "info": "🔵"
        }.get(alert.get("level", "info"), "⚪")
        
        print(f"\n{severity_icon} ALERT: {alert.get('title', 'Unknown Alert')}")
        print(f"   Level: {alert.get('level', 'unknown')}")
        print(f"   Component: {alert.get('component', 'unknown')}")
        print(f"   Message: {alert.get('message', 'No message')}")
        print(f"   Timestamp: {alert.get('timestamp', datetime.now())}")
        if alert.get("metadata"):
            print(f"   Metadata: {json.dumps(alert['metadata'], indent=2)}")
        print()
        
        return True
    except Exception as e:
        logger.error(f"Error sending console alert: {e}")
        return False


def send_slack_alert(alert: Dict[str, Any], config: AlertConfig) -> bool:
    """
    Send alert to Slack via webhook.
    
    Args:
        alert: Alert dictionary
        config: AlertConfig object
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import requests
        
        if not config.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False
        
        severity_color = {
            "critical": "#FF0000",  # Red
            "warning": "#FFA500",    # Orange
            "info": "#0066CC"        # Blue
        }.get(alert.get("level", "info"), "#808080")
        
        slack_payload = {
            "channel": config.slack_channel or "#alerts",
            "username": "SpendSenseAI Monitor",
            "icon_emoji": ":warning:",
            "attachments": [
                {
                    "color": severity_color,
                    "title": alert.get("title", "System Alert"),
                    "text": alert.get("message", "No message"),
                    "fields": [
                        {
                            "title": "Level",
                            "value": alert.get("level", "unknown"),
                            "short": True
                        },
                        {
                            "title": "Component",
                            "value": alert.get("component", "unknown"),
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": str(alert.get("timestamp", datetime.now())),
                            "short": False
                        }
                    ],
                    "footer": "SpendSenseAI Monitoring",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        if alert.get("metadata"):
            slack_payload["attachments"][0]["fields"].append({
                "title": "Details",
                "value": json.dumps(alert["metadata"], indent=2),
                "short": False
            })
        
        response = requests.post(
            config.webhook_url,
            json=slack_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Slack alert sent successfully: {alert.get('alert_id')}")
            return True
        else:
            logger.error(f"Slack webhook returned status {response.status_code}: {response.text}")
            return False
            
    except ImportError:
        logger.warning("requests library not installed. Install with: pip install requests")
        return False
    except Exception as e:
        logger.error(f"Error sending Slack alert: {e}")
        return False


def send_email_alert(alert: Dict[str, Any], config: AlertConfig) -> bool:
    """
    Send alert via email (SMTP).
    
    Args:
        alert: Alert dictionary
        config: AlertConfig object
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        if not config.email_recipients:
            logger.warning("No email recipients configured")
            return False
        
        # Get SMTP settings from environment
        smtp_host = os.getenv("SMTP_HOST", "localhost")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        smtp_from = os.getenv("SMTP_FROM", "alerts@spendsense.ai")
        
        # Create email
        msg = MIMEMultipart()
        msg["From"] = smtp_from
        msg["To"] = ", ".join(config.email_recipients)
        msg["Subject"] = f"[{alert.get('level', 'ALERT').upper()}] {alert.get('title', 'System Alert')}"
        
        body = f"""
SpendSenseAI Alert Notification

Alert ID: {alert.get('alert_id', 'unknown')}
Level: {alert.get('level', 'unknown')}
Component: {alert.get('component', 'unknown')}
Timestamp: {alert.get('timestamp', datetime.now())}

Message:
{alert.get('message', 'No message')}

"""
        
        if alert.get("metadata"):
            body += f"\nMetadata:\n{json.dumps(alert['metadata'], indent=2)}\n"
        
        msg.attach(MIMEText(body, "plain"))
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_user and smtp_password:
                server.starttls()
                server.login(smtp_user, smtp_password)
            
            server.send_message(msg)
        
        logger.info(f"Email alert sent successfully: {alert.get('alert_id')}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email alert: {e}")
        return False


def send_pagerduty_alert(alert: Dict[str, Any], config: AlertConfig) -> bool:
    """
    Send alert to PagerDuty.
    
    Args:
        alert: Alert dictionary
        config: AlertConfig object
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import requests
        
        if not config.pagerduty_service_key:
            logger.warning("PagerDuty service key not configured")
            return False
        
        # Map alert level to PagerDuty severity
        severity_map = {
            "critical": "critical",
            "warning": "warning",
            "info": "info"
        }
        severity = severity_map.get(alert.get("level", "info"), "info")
        
        # Only send critical alerts to PagerDuty by default
        if severity != "critical":
            logger.debug(f"Skipping PagerDuty alert for non-critical severity: {severity}")
            return True
        
        pagerduty_payload = {
            "routing_key": config.pagerduty_service_key,
            "event_action": "trigger",
            "payload": {
                "summary": alert.get("title", "System Alert"),
                "source": alert.get("component", "spendsense-ai"),
                "severity": severity,
                "custom_details": {
                    "alert_id": alert.get("alert_id"),
                    "message": alert.get("message"),
                    "timestamp": str(alert.get("timestamp", datetime.now())),
                    "metadata": alert.get("metadata", {})
                }
            }
        }
        
        response = requests.post(
            "https://events.pagerduty.com/v2/enqueue",
            json=pagerduty_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code in [200, 202]:
            logger.info(f"PagerDuty alert sent successfully: {alert.get('alert_id')}")
            return True
        else:
            logger.error(f"PagerDuty API returned status {response.status_code}: {response.text}")
            return False
            
    except ImportError:
        logger.warning("requests library not installed. Install with: pip install requests")
        return False
    except Exception as e:
        logger.error(f"Error sending PagerDuty alert: {e}")
        return False


def send_alert_notification(
    alert: Dict[str, Any],
    configs: List[AlertConfig]
) -> List[AlertNotification]:
    """
    Send alert notification via configured channels.
    
    Args:
        alert: Alert dictionary
        configs: List of AlertConfig objects
        
    Returns:
        List of AlertNotification objects
    """
    notifications = []
    alert_level = alert.get("level", "info")
    
    for config in configs:
        if not config.enabled:
            continue
        
        if alert_level not in config.severity_filter:
            continue
        
        success = False
        error_message = None
        
        try:
            if config.channel == NotificationChannel.CONSOLE:
                success = send_console_alert(alert, config)
            elif config.channel == NotificationChannel.SLACK:
                success = send_slack_alert(alert, config)
            elif config.channel == NotificationChannel.EMAIL:
                success = send_email_alert(alert, config)
            elif config.channel == NotificationChannel.PAGERDUTY:
                success = send_pagerduty_alert(alert, config)
            else:
                logger.warning(f"Unknown notification channel: {config.channel}")
                continue
                
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error sending {config.channel} notification: {e}")
        
        notifications.append(AlertNotification(
            alert_id=alert.get("alert_id", "unknown"),
            channel=config.channel,
            sent_at=datetime.now(),
            success=success,
            error_message=error_message
        ))
    
    return notifications


def load_alert_configs() -> List[AlertConfig]:
    """
    Load alert notification configurations from environment variables.
    
    Returns:
        List of AlertConfig objects
    """
    configs = []
    
    # Console alerts (always enabled for development)
    console_config = AlertConfig(
        channel=NotificationChannel.CONSOLE,
        enabled=True,
        severity_filter=["critical", "warning", "info"]
    )
    configs.append(console_config)
    
    # Slack configuration
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    if slack_webhook:
        slack_config = AlertConfig(
            channel=NotificationChannel.SLACK,
            enabled=True,
            webhook_url=slack_webhook,
            slack_channel=os.getenv("SLACK_CHANNEL", "#alerts"),
            severity_filter=["critical", "warning"]
        )
        configs.append(slack_config)
    
    # Email configuration
    email_recipients = os.getenv("ALERT_EMAIL_RECIPIENTS", "")
    if email_recipients:
        recipients = [r.strip() for r in email_recipients.split(",") if r.strip()]
        if recipients:
            email_config = AlertConfig(
                channel=NotificationChannel.EMAIL,
                enabled=True,
                email_recipients=recipients,
                severity_filter=["critical", "warning"]
            )
            configs.append(email_config)
    
    # PagerDuty configuration
    pagerduty_key = os.getenv("PAGERDUTY_SERVICE_KEY")
    if pagerduty_key:
        pagerduty_config = AlertConfig(
            channel=NotificationChannel.PAGERDUTY,
            enabled=True,
            pagerduty_service_key=pagerduty_key,
            severity_filter=["critical"]  # Only critical alerts to PagerDuty
        )
        configs.append(pagerduty_config)
    
    return configs

