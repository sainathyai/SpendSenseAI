"""
Notification System Design for SpendSenseAI.

How recommendations are delivered to users:
- Notification templates (email, push, in-app)
- Trigger logic (new persona, important insight, offer expiration)
- Frequency controls (avoid spam)
- Personalization engine (dynamic content insertion)
- Unsubscribe handling
- Template examples for each persona
- A/B testing framework design
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from enum import Enum
import json

from personas.persona_definition import PersonaType
from recommend.recommendation_builder import RecommendationSet


class NotificationChannel(str, Enum):
    """Notification channels."""
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"
    SMS = "sms"


class NotificationTrigger(str, Enum):
    """Notification trigger types."""
    NEW_PERSONA = "new_persona"
    IMPORTANT_INSIGHT = "important_insight"
    OFFER_EXPIRATION = "offer_expiration"
    RECOMMENDATION_UPDATE = "recommendation_update"
    MILESTONE_ACHIEVED = "milestone_achieved"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class NotificationTemplate:
    """Notification template."""
    template_id: str
    template_name: str
    channel: NotificationChannel
    trigger: NotificationTrigger
    target_personas: List[PersonaType]
    subject: str  # For email/SMS
    body_template: str  # Template with {placeholders}
    priority: NotificationPriority
    frequency_limit: Optional[int] = None  # Max per week/month
    placeholders: List[str] = None
    
    def __post_init__(self):
        if self.placeholders is None:
            self.placeholders = []


@dataclass
class Notification:
    """Notification instance."""
    notification_id: str
    user_id: str
    template_id: str
    channel: NotificationChannel
    subject: str
    body: str
    sent_at: datetime
    delivered: bool = False
    opened: bool = False
    clicked: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class NotificationPreferences:
    """User notification preferences."""
    user_id: str
    email_enabled: bool = True
    push_enabled: bool = True
    in_app_enabled: bool = True
    sms_enabled: bool = False
    frequency_limit: int = 7  # Max notifications per week
    quiet_hours_start: Optional[int] = None  # Hour of day (0-23)
    quiet_hours_end: Optional[int] = None
    unsubscribe_all: bool = False


# Default notification templates
DEFAULT_NOTIFICATION_TEMPLATES = {
    # High Utilization Persona
    "NOTIF-HU-001": NotificationTemplate(
        template_id="NOTIF-HU-001",
        template_name="High Utilization - Important Insight",
        channel=NotificationChannel.EMAIL,
        trigger=NotificationTrigger.IMPORTANT_INSIGHT,
        target_personas=[PersonaType.HIGH_UTILIZATION],
        subject="Important: Your credit utilization is {utilization}%",
        body_template="""
Dear {user_name},

We noticed your credit utilization is at {utilization}%. This high utilization can impact your credit score and increase interest costs.

Here's what you can do:
• {recommendation_1}
• {recommendation_2}

You're currently paying approximately ${monthly_interest:.2f} per month in interest. Reducing your utilization could help you save money.

View your personalized recommendations: {dashboard_link}

Best regards,
SpendSenseAI Team

This is educational content, not financial advice. Please consult with a qualified financial advisor.
        """,
        priority=NotificationPriority.HIGH,
        frequency_limit=2,  # Max 2 per week
        placeholders=["user_name", "utilization", "recommendation_1", "recommendation_2", "monthly_interest", "dashboard_link"]
    ),
    
    # Variable Income Budgeter
    "NOTIF-VI-001": NotificationTemplate(
        template_id="NOTIF-VI-001",
        template_name="Variable Income - Budget Help",
        channel=NotificationChannel.EMAIL,
        trigger=NotificationTrigger.NEW_PERSONA,
        target_personas=[PersonaType.VARIABLE_INCOME_BUDGETER],
        subject="New insights: Budgeting strategies for variable income",
        body_template="""
Dear {user_name},

We've analyzed your financial patterns and identified you as a Variable Income Budgeter. This means you have irregular income patterns that can make budgeting challenging.

Here are resources that can help:
• {recommendation_1}
• {recommendation_2}

Your median pay gap is {pay_gap_days:.1f} days, and your cash flow buffer is {buffer_months:.1f} months. Building a larger buffer can help you manage irregular income more effectively.

View your personalized recommendations: {dashboard_link}

Best regards,
SpendSenseAI Team

This is educational content, not financial advice. Please consult with a qualified financial advisor.
        """,
        priority=NotificationPriority.MEDIUM,
        frequency_limit=3,
        placeholders=["user_name", "recommendation_1", "recommendation_2", "pay_gap_days", "buffer_months", "dashboard_link"]
    ),
    
    # Subscription-Heavy
    "NOTIF-SH-001": NotificationTemplate(
        template_id="NOTIF-SH-001",
        template_name="Subscription-Heavy - Cost Analysis",
        channel=NotificationChannel.EMAIL,
        trigger=NotificationTrigger.IMPORTANT_INSIGHT,
        target_personas=[PersonaType.SUBSCRIPTION_HEAVY],
        subject="You're spending ${monthly_subscriptions:.2f}/month on subscriptions",
        body_template="""
Dear {user_name},

We noticed you have {subscription_count} active subscriptions totaling ${monthly_subscriptions:.2f} per month (${annual_cost:,.2f} per year).

Here's how you can optimize:
• {recommendation_1}
• {recommendation_2}

Your top subscription is {top_subscription} at ${top_subscription_amount:.2f}/month.

View your subscription audit: {dashboard_link}

Best regards,
SpendSenseAI Team

This is educational content, not financial advice. Please consult with a qualified financial advisor.
        """,
        priority=NotificationPriority.MEDIUM,
        frequency_limit=2,
        placeholders=["user_name", "monthly_subscriptions", "subscription_count", "annual_cost", "recommendation_1", "recommendation_2", "top_subscription", "top_subscription_amount", "dashboard_link"]
    ),
    
    # Savings Builder
    "NOTIF-SB-001": NotificationTemplate(
        template_id="NOTIF-SB-001",
        template_name="Savings Builder - Goal Achievement",
        channel=NotificationChannel.EMAIL,
        trigger=NotificationTrigger.MILESTONE_ACHIEVED,
        target_personas=[PersonaType.SAVINGS_BUILDER],
        subject="Congratulations! You're making great progress on your savings goals",
        body_template="""
Dear {user_name},

Great news! Your savings are growing at {growth_rate:.1f}% over the past 6 months.

You currently have ${savings_balance:,.2f} in savings. Here are ways to optimize further:
• {recommendation_1}
• {recommendation_2}

Keep up the excellent work! View your savings dashboard: {dashboard_link}

Best regards,
SpendSenseAI Team

This is educational content, not financial advice. Please consult with a qualified financial advisor.
        """,
        priority=NotificationPriority.LOW,
        frequency_limit=4,
        placeholders=["user_name", "growth_rate", "savings_balance", "recommendation_1", "recommendation_2", "dashboard_link"]
    ),
    
    # Financial Fragility
    "NOTIF-FF-001": NotificationTemplate(
        template_id="NOTIF-FF-001",
        template_name="Financial Fragility - Fee Avoidance",
        channel=NotificationChannel.EMAIL,
        trigger=NotificationTrigger.IMPORTANT_INSIGHT,
        target_personas=[PersonaType.FINANCIAL_FRAGILITY],
        subject="Tips to avoid fees and build your financial buffer",
        body_template="""
Dear {user_name},

We noticed your checking account balance is ${checking_balance:.2f}. Building a buffer can help you avoid fees and manage unexpected expenses.

Here's how to get started:
• {recommendation_1}
• {recommendation_2}

Avoiding just one overdraft fee can save you $35. Building a $500 buffer can help protect you from fees.

View your recommendations: {dashboard_link}

Best regards,
SpendSenseAI Team

This is educational content, not financial advice. Please consult with a qualified financial advisor.
        """,
        priority=NotificationPriority.HIGH,
        frequency_limit=2,
        placeholders=["user_name", "checking_balance", "recommendation_1", "recommendation_2", "dashboard_link"]
    ),
}


def personalize_notification(
    template: NotificationTemplate,
    user_id: str,
    user_name: str,
    recommendations: RecommendationSet,
    data_citations: Dict[str, Any]
) -> str:
    """
    Personalize notification template with user data.
    
    Args:
        template: NotificationTemplate object
        user_id: User ID
        user_name: User name
        recommendations: RecommendationSet object
        data_citations: Dictionary with data citations
        
    Returns:
        Personalized notification body
    """
    body = template.body_template
    
    # Replace placeholders
    replacements = {
        "user_name": user_name or "Valued Customer",
        "dashboard_link": f"https://app.spendsenseai.com/user/{user_id}",
    }
    
    # Add recommendation placeholders
    if recommendations.education_items:
        replacements["recommendation_1"] = recommendations.education_items[0].title
    if len(recommendations.education_items) > 1:
        replacements["recommendation_2"] = recommendations.education_items[1].title
    
    # Add data citation placeholders
    if "utilization_percentage" in data_citations:
        replacements["utilization"] = f"{data_citations['utilization_percentage']:.1f}"
    if "monthly_interest" in data_citations:
        replacements["monthly_interest"] = data_citations["monthly_interest"]
    if "subscription_count" in data_citations:
        replacements["subscription_count"] = data_citations["subscription_count"]
    if "monthly_recurring_spend" in data_citations:
        replacements["monthly_subscriptions"] = data_citations["monthly_recurring_spend"]
        replacements["annual_cost"] = data_citations["monthly_recurring_spend"] * 12
    if "top_subscription" in data_citations:
        replacements["top_subscription"] = data_citations["top_subscription"]
    if "top_subscription_amount" in data_citations:
        replacements["top_subscription_amount"] = data_citations["top_subscription_amount"]
    if "growth_rate" in data_citations:
        replacements["growth_rate"] = data_citations["growth_rate"]
    if "savings_balance" in data_citations:
        replacements["savings_balance"] = data_citations["savings_balance"]
    if "checking_balance" in data_citations:
        replacements["checking_balance"] = data_citations["checking_balance"]
    if "median_pay_gap_days" in data_citations:
        replacements["pay_gap_days"] = data_citations["median_pay_gap_days"]
    if "cash_flow_buffer_months" in data_citations:
        replacements["buffer_months"] = data_citations["cash_flow_buffer_months"]
    
    # Replace all placeholders
    for placeholder, value in replacements.items():
        body = body.replace(f"{{{placeholder}}}", str(value))
    
    return body


def should_send_notification(
    user_id: str,
    template: NotificationTemplate,
    preferences: NotificationPreferences,
    last_notification_date: Optional[datetime] = None
) -> bool:
    """
    Check if notification should be sent based on frequency controls.
    
    Args:
        user_id: User ID
        template: NotificationTemplate object
        preferences: NotificationPreferences object
        last_notification_date: Last notification sent date
        
    Returns:
        True if notification should be sent, False otherwise
    """
    # Check if user unsubscribed
    if preferences.unsubscribe_all:
        return False
    
    # Check channel preference
    if template.channel == NotificationChannel.EMAIL and not preferences.email_enabled:
        return False
    if template.channel == NotificationChannel.PUSH and not preferences.push_enabled:
        return False
    if template.channel == NotificationChannel.IN_APP and not preferences.in_app_enabled:
        return False
    if template.channel == NotificationChannel.SMS and not preferences.sms_enabled:
        return False
    
    # Check frequency limit
    if last_notification_date and template.frequency_limit:
        days_since_last = (datetime.now() - last_notification_date).days
        min_days_between = 7 / template.frequency_limit  # Convert per week to days
        
        if days_since_last < min_days_between:
            return False
    
    # Check quiet hours (for push/SMS)
    if template.channel in [NotificationChannel.PUSH, NotificationChannel.SMS]:
        if preferences.quiet_hours_start and preferences.quiet_hours_end:
            current_hour = datetime.now().hour
            if preferences.quiet_hours_start <= current_hour <= preferences.quiet_hours_end:
                return False
    
    return True


def create_notification(
    user_id: str,
    template: NotificationTemplate,
    personalized_body: str,
    personalized_subject: str
) -> Notification:
    """
    Create notification instance.
    
    Args:
        user_id: User ID
        template: NotificationTemplate object
        personalized_body: Personalized notification body
        personalized_subject: Personalized notification subject
        
    Returns:
        Notification object
    """
    notification_id = f"NOTIF-{user_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return Notification(
        notification_id=notification_id,
        user_id=user_id,
        template_id=template.template_id,
        channel=template.channel,
        subject=personalized_subject,
        body=personalized_body,
        sent_at=datetime.now(),
        delivered=False,
        opened=False,
        clicked=False
    )


def get_template_for_persona(
    persona_type: PersonaType,
    trigger: NotificationTrigger,
    channel: NotificationChannel = NotificationChannel.EMAIL
) -> Optional[NotificationTemplate]:
    """
    Get notification template for persona and trigger.
    
    Args:
        persona_type: PersonaType enum value
        trigger: NotificationTrigger enum value
        channel: NotificationChannel enum value
        
    Returns:
        NotificationTemplate object or None
    """
    for template in DEFAULT_NOTIFICATION_TEMPLATES.values():
        if (persona_type in template.target_personas and
            template.trigger == trigger and
            template.channel == channel):
            return template
    
    return None

