"""
Notification System Design for SpendSenseAI.

How recommendations are delivered to users:
- Notification templates (email, push, in-app)
- Trigger logic (new persona, important insight, offer expiration)
- Frequency controls (avoid spam)
- Personalization engine (dynamic content insertion)
- Unsubscribe handling
- Template examples for each persona
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from enum import Enum

from personas.persona_definition import PersonaType
from recommend.recommendation_builder import RecommendationSet


class NotificationChannel(str, Enum):
    """Notification channels."""
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"
    SMS = "sms"


class NotificationTrigger(str, Enum):
    """Notification triggers."""
    NEW_PERSONA = "new_persona"
    IMPORTANT_INSIGHT = "important_insight"
    OFFER_EXPIRATION = "offer_expiration"
    RECOMMENDATION_READY = "recommendation_ready"
    BEHAVIOR_CHANGE = "behavior_change"
    WEEKLY_DIGEST = "weekly_digest"


@dataclass
class NotificationTemplate:
    """Notification template."""
    template_id: str
    channel: NotificationChannel
    trigger: NotificationTrigger
    subject: str  # For email/SMS
    body: str  # Main content
    personalization_fields: List[str]  # Fields to personalize
    persona_types: List[PersonaType]  # Which personas this applies to
    priority: int = 0  # 0 = normal, 1 = high, 2 = urgent


@dataclass
class Notification:
    """A notification instance."""
    notification_id: str
    user_id: str
    channel: NotificationChannel
    template_id: str
    subject: str
    body: str
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None


@dataclass
class NotificationPreferences:
    """User notification preferences."""
    user_id: str
    channels_enabled: List[NotificationChannel]
    frequency_limit: int  # Max notifications per week
    unsubscribe_all: bool = False
    unsubscribe_channels: List[NotificationChannel] = None
    
    def __post_init__(self):
        if self.unsubscribe_channels is None:
            self.unsubscribe_channels = []


# Default notification templates
DEFAULT_NOTIFICATION_TEMPLATES = {
    "TEMPLATE-NEW-PERSONA": NotificationTemplate(
        template_id="TEMPLATE-NEW-PERSONA",
        channel=NotificationChannel.EMAIL,
        trigger=NotificationTrigger.NEW_PERSONA,
        subject="Your Financial Profile Has Been Updated",
        body="""Hi {user_name},

We've updated your financial profile. You've been assigned the {persona_type} persona based on your recent financial behavior.

This means: {persona_description}

We have personalized recommendations for you. View them here: {recommendations_url}

Best regards,
SpendSenseAI Team""",
        personalization_fields=["user_name", "persona_type", "persona_description", "recommendations_url"],
        persona_types=[p for p in PersonaType],
        priority=1
    ),
    
    "TEMPLATE-IMPORTANT-INSIGHT": NotificationTemplate(
        template_id="TEMPLATE-IMPORTANT-INSIGHT",
        channel=NotificationChannel.PUSH,
        trigger=NotificationTrigger.IMPORTANT_INSIGHT,
        subject="Important Financial Insight",
        body="""{user_name}, we noticed {insight_description}.

This could impact your financial health. Learn more: {insight_url}""",
        personalization_fields=["user_name", "insight_description", "insight_url"],
        persona_types=[p for p in PersonaType],
        priority=2
    ),
    
    "TEMPLATE-OFFER-EXPIRATION": NotificationTemplate(
        template_id="TEMPLATE-OFFER-EXPIRATION",
        channel=NotificationChannel.EMAIL,
        trigger=NotificationTrigger.OFFER_EXPIRATION,
        subject="Limited Time Offer Expiring Soon",
        body="""Hi {user_name},

The {offer_title} offer you were eligible for is expiring soon.

{offer_description}

Act now: {offer_url}

Expires: {expiration_date}""",
        personalization_fields=["user_name", "offer_title", "offer_description", "offer_url", "expiration_date"],
        persona_types=[p for p in PersonaType],
        priority=1
    ),
    
    "TEMPLATE-RECOMMENDATION-READY": NotificationTemplate(
        template_id="TEMPLATE-RECOMMENDATION-READY",
        channel=NotificationChannel.IN_APP,
        trigger=NotificationTrigger.RECOMMENDATION_READY,
        subject="New Recommendations for You",
        body="""Hi {user_name},

You have {recommendation_count} new personalized recommendations based on your financial behavior.

{recommendation_preview}

View all recommendations: {recommendations_url}""",
        personalization_fields=["user_name", "recommendation_count", "recommendation_preview", "recommendations_url"],
        persona_types=[p for p in PersonaType],
        priority=0
    ),
    
    "TEMPLATE-WEEKLY-DIGEST": NotificationTemplate(
        template_id="TEMPLATE-WEEKLY-DIGEST",
        channel=NotificationChannel.EMAIL,
        trigger=NotificationTrigger.WEEKLY_DIGEST,
        subject="Your Weekly Financial Summary",
        body="""Hi {user_name},

Here's your weekly financial summary:

{summary_content}

View your dashboard: {dashboard_url}""",
        personalization_fields=["user_name", "summary_content", "dashboard_url"],
        persona_types=[p for p in PersonaType],
        priority=0
    ),
}


def personalize_template(
    template: NotificationTemplate,
    personalization_data: Dict[str, Any]
) -> Notification:
    """
    Personalize a notification template.
    
    Args:
        template: NotificationTemplate object
        personalization_data: Dictionary with personalization values
        
    Returns:
        Notification object
    """
    # Replace placeholders in subject and body
    subject = template.subject
    body = template.body
    
    for field, value in personalization_data.items():
        placeholder = f"{{{field}}}"
        subject = subject.replace(placeholder, str(value))
        body = body.replace(placeholder, str(value))
    
    # Generate notification ID
    notification_id = f"NOTIF-{datetime.now().strftime('%Y%m%d%H%M%S')}-{template.template_id}"
    
    return Notification(
        notification_id=notification_id,
        user_id=personalization_data.get("user_id", "UNKNOWN"),
        channel=template.channel,
        template_id=template.template_id,
        subject=subject,
        body=body
    )


def should_send_notification(
    user_id: str,
    trigger: NotificationTrigger,
    notification_preferences: Optional[NotificationPreferences] = None,
    frequency_tracking: Optional[Dict[str, int]] = None
) -> bool:
    """
    Check if notification should be sent based on preferences and frequency controls.
    
    Args:
        user_id: User ID
        trigger: Notification trigger
        notification_preferences: Optional user preferences
        frequency_tracking: Optional tracking of notification frequency
        
    Returns:
        True if notification should be sent
    """
    # Check if user unsubscribed
    if notification_preferences and notification_preferences.unsubscribe_all:
        return False
    
    # Check frequency limits
    if frequency_tracking:
        weekly_count = frequency_tracking.get(user_id, 0)
        max_per_week = notification_preferences.frequency_limit if notification_preferences else 5
        
        if weekly_count >= max_per_week:
            return False
    
    # Check channel preferences
    if notification_preferences:
        # For now, assume all channels are enabled unless explicitly disabled
        # In real system, would check specific channel preferences
        pass
    
    return True


def generate_notification_for_persona(
    user_id: str,
    persona_type: PersonaType,
    recommendations: RecommendationSet,
    trigger: NotificationTrigger = NotificationTrigger.RECOMMENDATION_READY
) -> Optional[Notification]:
    """
    Generate notification for a persona.
    
    Args:
        user_id: User ID
        persona_type: PersonaType enum value
        recommendations: RecommendationSet object
        trigger: Notification trigger
        
    Returns:
        Notification object or None
    """
    # Get appropriate template
    template_id = "TEMPLATE-RECOMMENDATION-READY"
    if trigger == NotificationTrigger.NEW_PERSONA:
        template_id = "TEMPLATE-NEW-PERSONA"
    elif trigger == NotificationTrigger.IMPORTANT_INSIGHT:
        template_id = "TEMPLATE-IMPORTANT-INSIGHT"
    
    template = DEFAULT_NOTIFICATION_TEMPLATES.get(template_id)
    
    if not template:
        return None
    
    # Prepare personalization data
    persona_descriptions = {
        PersonaType.HIGH_UTILIZATION: "your credit card utilization is high",
        PersonaType.VARIABLE_INCOME_BUDGETER: "your income varies and you need flexible budgeting",
        PersonaType.SUBSCRIPTION_HEAVY: "you have multiple recurring subscriptions",
        PersonaType.SAVINGS_BUILDER: "you're building your savings",
        PersonaType.FINANCIAL_FRAGILITY: "you're facing immediate financial challenges"
    }
    
    personalization_data = {
        "user_id": user_id,
        "user_name": f"User {user_id}",  # In real system, would get from user profile
        "persona_type": persona_type.value.replace('_', ' ').title(),
        "persona_description": persona_descriptions.get(persona_type, "your financial behavior"),
        "recommendation_count": len(recommendations.education_items) + len(recommendations.partner_offers),
        "recommendation_preview": recommendations.education_items[0].title if recommendations.education_items else "New recommendations available",
        "recommendations_url": f"https://app.spendsenseai.com/recommendations/{user_id}",
        "dashboard_url": f"https://app.spendsenseai.com/dashboard/{user_id}"
    }
    
    # Personalize template
    notification = personalize_template(template, personalization_data)
    
    return notification


def create_notification_preferences(
    user_id: str,
    channels_enabled: Optional[List[NotificationChannel]] = None,
    frequency_limit: int = 5
) -> NotificationPreferences:
    """
    Create notification preferences for a user.
    
    Args:
        user_id: User ID
        channels_enabled: Optional list of enabled channels
        frequency_limit: Max notifications per week
        
    Returns:
        NotificationPreferences object
    """
    if channels_enabled is None:
        channels_enabled = [NotificationChannel.EMAIL, NotificationChannel.IN_APP]
    
    return NotificationPreferences(
        user_id=user_id,
        channels_enabled=channels_enabled,
        frequency_limit=frequency_limit,
        unsubscribe_all=False,
        unsubscribe_channels=[]
    )


def generate_notification_templates_for_personas() -> Dict[str, NotificationTemplate]:
    """
    Generate notification templates for each persona.
    
    Returns:
        Dictionary of persona-specific templates
    """
    templates = {}
    
    persona_specific_templates = {
        PersonaType.HIGH_UTILIZATION: {
            "subject": "Reduce Your Credit Card Interest",
            "body": """Hi {user_name},

Your credit utilization is at {utilization}%. Reducing it to 30% could save you ${annual_interest_savings:.0f} per year in interest.

Learn how: {recommendations_url}"""
        },
        PersonaType.VARIABLE_INCOME_BUDGETER: {
            "subject": "Budget Strategies for Variable Income",
            "body": """Hi {user_name},

Your income varies with a {pay_gap} day median gap. We have budgeting strategies tailored for variable income earners.

View recommendations: {recommendations_url}"""
        },
        PersonaType.SUBSCRIPTION_HEAVY: {
            "subject": "Review Your Subscriptions",
            "body": """Hi {user_name},

You have {subscription_count} active subscriptions totaling ${monthly_spend:.0f}/month. Reviewing them could save you ${annual_savings:.0f} per year.

Review subscriptions: {recommendations_url}"""
        },
        PersonaType.SAVINGS_BUILDER: {
            "subject": "Optimize Your Savings Strategy",
            "body": """Hi {user_name},

Your savings are growing at {growth_rate:.1f}%. We have strategies to help you optimize your savings further.

View recommendations: {recommendations_url}"""
        },
        PersonaType.FINANCIAL_FRAGILITY: {
            "subject": "Build Your Financial Buffer",
            "body": """Hi {user_name},

Building a $500 buffer can help you avoid fees and manage unexpected expenses. We have strategies to help you build this buffer.

Learn more: {recommendations_url}"""
        }
    }
    
    for persona_type, template_data in persona_specific_templates.items():
        template_id = f"TEMPLATE-PERSONA-{persona_type.value.upper()}"
        templates[template_id] = NotificationTemplate(
            template_id=template_id,
            channel=NotificationChannel.EMAIL,
            trigger=NotificationTrigger.RECOMMENDATION_READY,
            subject=template_data["subject"],
            body=template_data["body"],
            personalization_fields=["user_name", "recommendations_url"],
            persona_types=[persona_type],
            priority=1
        )
    
    return templates


def format_notification_for_display(notification: Notification) -> str:
    """
    Format notification for display.
    
    Args:
        notification: Notification object
        
    Returns:
        Formatted string
    """
    output = f"Notification ID: {notification.notification_id}\n"
    output += f"Channel: {notification.channel.value}\n"
    output += f"Subject: {notification.subject}\n"
    output += f"Body:\n{notification.body}\n"
    
    if notification.sent_at:
        output += f"Sent: {notification.sent_at}\n"
    if notification.delivered_at:
        output += f"Delivered: {notification.delivered_at}\n"
    if notification.opened_at:
        output += f"Opened: {notification.opened_at}\n"
    if notification.clicked_at:
        output += f"Clicked: {notification.clicked_at}\n"
    
    return output

