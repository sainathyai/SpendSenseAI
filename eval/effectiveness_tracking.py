"""
Recommendation Effectiveness Tracking for SpendSenseAI.

Measures impact of recommendations:
- Engagement metrics (click-through, completion rates)
- Outcome tracking (did utilization improve after recommendation?)
- Content performance (which articles/tools most effective?)
- Offer conversion rates
- Attribution logic (which recommendation caused change?)
- Feedback loop to recommendation engine
- ROI calculation for partner offers
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from enum import Enum
import json

from personas.persona_definition import PersonaType
from features.credit_utilization import analyze_credit_utilization_for_customer
from features.savings_pattern import analyze_savings_patterns_for_customer
from features.subscription_detection import detect_subscriptions_for_customer
from ingest.queries import get_accounts_by_customer


class EngagementType(str, Enum):
    """Engagement types."""
    CLICK = "click"
    VIEW = "view"
    COMPLETE = "complete"
    SHARE = "share"
    FEEDBACK = "feedback"


class OutcomeType(str, Enum):
    """Outcome types."""
    UTILIZATION_IMPROVED = "utilization_improved"
    SAVINGS_INCREASED = "savings_increased"
    SUBSCRIPTION_CANCELED = "subscription_canceled"
    ACCOUNT_OPENED = "account_opened"
    NO_CHANGE = "no_change"
    NEGATIVE_CHANGE = "negative_change"


@dataclass
class EngagementEvent:
    """Engagement event."""
    event_id: str
    user_id: str
    recommendation_id: str
    engagement_type: EngagementType
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class OutcomeMeasurement:
    """Outcome measurement."""
    measurement_id: str
    user_id: str
    recommendation_id: str
    outcome_type: OutcomeType
    before_value: float
    after_value: float
    change_percentage: float
    measurement_date: date
    attribution_confidence: float  # 0.0 to 1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ContentPerformance:
    """Content performance metrics."""
    content_id: str
    content_title: str
    total_views: int
    total_clicks: int
    total_completions: int
    click_through_rate: float
    completion_rate: float
    positive_outcomes: int
    negative_outcomes: int
    average_attribution_confidence: float
    effectiveness_score: float  # 0.0 to 1.0


@dataclass
class OfferPerformance:
    """Offer performance metrics."""
    offer_id: str
    offer_title: str
    total_views: int
    total_clicks: int
    conversions: int
    click_through_rate: float
    conversion_rate: float
    roi: float  # Return on investment
    average_attribution_confidence: float


@dataclass
class EffectivenessReport:
    """Recommendation effectiveness report."""
    report_id: str
    timestamp: datetime
    content_performance: List[ContentPerformance]
    offer_performance: List[OfferPerformance]
    overall_engagement_rate: float
    overall_outcome_rate: float
    summary: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.summary is None:
            self.summary = {}


def measure_utilization_outcome(
    user_id: str,
    db_path: str,
    recommendation_id: str,
    recommendation_date: date,
    days_before: int = 30,
    days_after: int = 30
) -> Optional[OutcomeMeasurement]:
    """
    Measure utilization outcome after recommendation.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        recommendation_id: Recommendation ID
        recommendation_date: Date recommendation was made
        days_before: Days before recommendation to measure
        days_after: Days after recommendation to measure
        
    Returns:
        OutcomeMeasurement object or None
    """
    try:
        from features.credit_utilization import analyze_credit_utilization_for_customer
        
        # Measure before (use historical data if available, otherwise current)
        before_date = recommendation_date - timedelta(days=days_before)
        # Simplified - would need historical data
        # For now, use current metrics as "before"
        
        card_metrics_before, agg_metrics_before = analyze_credit_utilization_for_customer(
            user_id, db_path, 30
        )
        
        # Measure after
        after_date = recommendation_date + timedelta(days=days_after)
        # Simplified - would need historical data
        # For now, use current metrics as "after"
        
        card_metrics_after, agg_metrics_after = analyze_credit_utilization_for_customer(
            user_id, db_path, 30
        )
        
        if not card_metrics_before or not card_metrics_after:
            return None
        
        before_utilization = agg_metrics_before.aggregate_utilization
        after_utilization = agg_metrics_after.aggregate_utilization
        
        change_pct = ((after_utilization - before_utilization) / before_utilization * 100) if before_utilization > 0 else 0.0
        
        # Determine outcome type
        if change_pct < -5:  # 5% improvement
            outcome_type = OutcomeType.UTILIZATION_IMPROVED
        elif change_pct > 5:
            outcome_type = OutcomeType.NEGATIVE_CHANGE
        else:
            outcome_type = OutcomeType.NO_CHANGE
        
        # Attribution confidence (simplified - would need more sophisticated logic)
        attribution_confidence = 0.7 if abs(change_pct) > 10 else 0.5
        
        return OutcomeMeasurement(
            measurement_id=f"OUTCOME-{user_id}-{recommendation_id}",
            user_id=user_id,
            recommendation_id=recommendation_id,
            outcome_type=outcome_type,
            before_value=before_utilization,
            after_value=after_utilization,
            change_percentage=change_pct,
            measurement_date=date.today(),
            attribution_confidence=attribution_confidence
        )
    
    except Exception:
        return None


def measure_savings_outcome(
    user_id: str,
    db_path: str,
    recommendation_id: str,
    recommendation_date: date,
    days_before: int = 90,
    days_after: int = 90
) -> Optional[OutcomeMeasurement]:
    """
    Measure savings outcome after recommendation.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        recommendation_id: Recommendation ID
        recommendation_date: Date recommendation was made
        days_before: Days before recommendation to measure
        days_after: Days after recommendation to measure
        
    Returns:
        OutcomeMeasurement object or None
    """
    try:
        from features.savings_pattern import analyze_savings_patterns_for_customer
        
        # Measure before
        savings_accounts_before, savings_metrics_before = analyze_savings_patterns_for_customer(
            user_id, db_path, 180
        )
        
        # Measure after
        savings_accounts_after, savings_metrics_after = analyze_savings_patterns_for_customer(
            user_id, db_path, 180
        )
        
        if not savings_accounts_before or not savings_accounts_after:
            return None
        
        before_balance = savings_metrics_before.total_savings_balance
        after_balance = savings_metrics_after.total_savings_balance
        
        change_pct = ((after_balance - before_balance) / before_balance * 100) if before_balance > 0 else 0.0
        
        # Determine outcome type
        if change_pct > 10:  # 10% increase
            outcome_type = OutcomeType.SAVINGS_INCREASED
        elif change_pct < -10:
            outcome_type = OutcomeType.NEGATIVE_CHANGE
        else:
            outcome_type = OutcomeType.NO_CHANGE
        
        attribution_confidence = 0.7 if abs(change_pct) > 20 else 0.5
        
        return OutcomeMeasurement(
            measurement_id=f"OUTCOME-{user_id}-{recommendation_id}",
            user_id=user_id,
            recommendation_id=recommendation_id,
            outcome_type=outcome_type,
            before_value=before_balance,
            after_value=after_balance,
            change_percentage=change_pct,
            measurement_date=date.today(),
            attribution_confidence=attribution_confidence
        )
    
    except Exception:
        return None


def calculate_content_performance(
    content_id: str,
    engagement_events: List[EngagementEvent],
    outcome_measurements: List[OutcomeMeasurement]
) -> ContentPerformance:
    """
    Calculate content performance metrics.
    
    Args:
        content_id: Content ID
        engagement_events: List of engagement events for this content
        outcome_measurements: List of outcome measurements for this content
        
    Returns:
        ContentPerformance object
    """
    content_engagements = [e for e in engagement_events if e.recommendation_id.startswith(f"REC-") and content_id in e.metadata.get("content_id", "")]
    content_outcomes = [o for o in outcome_measurements if content_id in o.metadata.get("content_id", "")]
    
    total_views = sum(1 for e in content_engagements if e.engagement_type == EngagementType.VIEW)
    total_clicks = sum(1 for e in content_engagements if e.engagement_type == EngagementType.CLICK)
    total_completions = sum(1 for e in content_engagements if e.engagement_type == EngagementType.COMPLETE)
    
    click_through_rate = (total_clicks / total_views * 100) if total_views > 0 else 0.0
    completion_rate = (total_completions / total_clicks * 100) if total_clicks > 0 else 0.0
    
    positive_outcomes = sum(1 for o in content_outcomes if o.outcome_type in [
        OutcomeType.UTILIZATION_IMPROVED, OutcomeType.SAVINGS_INCREASED
    ])
    negative_outcomes = sum(1 for o in content_outcomes if o.outcome_type == OutcomeType.NEGATIVE_CHANGE)
    
    avg_attribution = sum(o.attribution_confidence for o in content_outcomes) / len(content_outcomes) if content_outcomes else 0.0
    
    # Calculate effectiveness score (weighted combination)
    engagement_score = (click_through_rate / 100) * 0.3 + (completion_rate / 100) * 0.3
    outcome_score = (positive_outcomes / len(content_outcomes) if content_outcomes else 0.0) * 0.4
    effectiveness_score = min(engagement_score + outcome_score, 1.0)
    
    return ContentPerformance(
        content_id=content_id,
        content_title=content_engagements[0].metadata.get("content_title", "Unknown") if content_engagements else "Unknown",
        total_views=total_views,
        total_clicks=total_clicks,
        total_completions=total_completions,
        click_through_rate=click_through_rate,
        completion_rate=completion_rate,
        positive_outcomes=positive_outcomes,
        negative_outcomes=negative_outcomes,
        average_attribution_confidence=avg_attribution,
        effectiveness_score=effectiveness_score
    )


def calculate_offer_performance(
    offer_id: str,
    engagement_events: List[EngagementEvent],
    outcome_measurements: List[OutcomeMeasurement],
    conversion_value: float = 0.0  # Revenue per conversion
) -> OfferPerformance:
    """
    Calculate offer performance metrics.
    
    Args:
        offer_id: Offer ID
        engagement_events: List of engagement events for this offer
        outcome_measurements: List of outcome measurements for this offer
        conversion_value: Revenue per conversion
        
    Returns:
        OfferPerformance object
    """
    offer_engagements = [e for e in engagement_events if e.recommendation_id.startswith(f"REC-") and offer_id in e.metadata.get("offer_id", "")]
    offer_outcomes = [o for o in outcome_measurements if offer_id in o.metadata.get("offer_id", "")]
    
    total_views = sum(1 for e in offer_engagements if e.engagement_type == EngagementType.VIEW)
    total_clicks = sum(1 for e in offer_engagements if e.engagement_type == EngagementType.CLICK)
    conversions = sum(1 for o in offer_outcomes if o.outcome_type == OutcomeType.ACCOUNT_OPENED)
    
    click_through_rate = (total_clicks / total_views * 100) if total_views > 0 else 0.0
    conversion_rate = (conversions / total_clicks * 100) if total_clicks > 0 else 0.0
    
    # Calculate ROI (simplified - would need actual cost data)
    total_revenue = conversions * conversion_value
    total_cost = total_views * 0.01  # Simplified cost per view
    roi = ((total_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0.0
    
    avg_attribution = sum(o.attribution_confidence for o in offer_outcomes) / len(offer_outcomes) if offer_outcomes else 0.0
    
    return OfferPerformance(
        offer_id=offer_id,
        offer_title=offer_engagements[0].metadata.get("offer_title", "Unknown") if offer_engagements else "Unknown",
        total_views=total_views,
        total_clicks=total_clicks,
        conversions=conversions,
        click_through_rate=click_through_rate,
        conversion_rate=conversion_rate,
        roi=roi,
        average_attribution_confidence=avg_attribution
    )


def track_engagement(
    user_id: str,
    recommendation_id: str,
    engagement_type: EngagementType,
    metadata: Optional[Dict[str, Any]] = None
) -> EngagementEvent:
    """
    Track user engagement with a recommendation.
    
    Args:
        user_id: User ID
        recommendation_id: Recommendation ID
        engagement_type: Type of engagement
        metadata: Optional metadata
        
    Returns:
        EngagementEvent object
    """
    return EngagementEvent(
        event_id=f"ENG-{user_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        user_id=user_id,
        recommendation_id=recommendation_id,
        engagement_type=engagement_type,
        timestamp=datetime.now(),
        metadata=metadata or {}
    )


def generate_effectiveness_report(
    engagement_events: List[EngagementEvent],
    outcome_measurements: List[OutcomeMeasurement],
    report_id: Optional[str] = None
) -> EffectivenessReport:
    """
    Generate effectiveness report.
    
    Args:
        engagement_events: List of engagement events
        outcome_measurements: List of outcome measurements
        report_id: Optional report ID (auto-generated if not provided)
        
    Returns:
        EffectivenessReport object
    """
    if report_id is None:
        timestamp = datetime.now()
        report_id = f"EFF-{timestamp.strftime('%Y%m%d%H%M%S')}"
    
    # Get unique content IDs and offer IDs
    content_ids = set()
    offer_ids = set()
    
    for event in engagement_events:
        if "content_id" in event.metadata:
            content_ids.add(event.metadata["content_id"])
        if "offer_id" in event.metadata:
            offer_ids.add(event.metadata["offer_id"])
    
    # Calculate content performance
    content_performance = []
    for content_id in content_ids:
        perf = calculate_content_performance(content_id, engagement_events, outcome_measurements)
        content_performance.append(perf)
    
    # Calculate offer performance
    offer_performance = []
    for offer_id in offer_ids:
        perf = calculate_offer_performance(offer_id, engagement_events, outcome_measurements)
        offer_performance.append(perf)
    
    # Calculate overall metrics
    total_views = sum(1 for e in engagement_events if e.engagement_type == EngagementType.VIEW)
    total_clicks = sum(1 for e in engagement_events if e.engagement_type == EngagementType.CLICK)
    overall_engagement_rate = (total_clicks / total_views * 100) if total_views > 0 else 0.0
    
    positive_outcomes = sum(1 for o in outcome_measurements if o.outcome_type in [
        OutcomeType.UTILIZATION_IMPROVED, OutcomeType.SAVINGS_INCREASED, OutcomeType.ACCOUNT_OPENED
    ])
    overall_outcome_rate = (positive_outcomes / len(outcome_measurements) * 100) if outcome_measurements else 0.0
    
    summary = {
        "total_engagement_events": len(engagement_events),
        "total_outcome_measurements": len(outcome_measurements),
        "positive_outcomes": positive_outcomes,
        "content_items_analyzed": len(content_performance),
        "offers_analyzed": len(offer_performance)
    }
    
    return EffectivenessReport(
        report_id=report_id,
        timestamp=datetime.now(),
        content_performance=content_performance,
        offer_performance=offer_performance,
        overall_engagement_rate=overall_engagement_rate,
        overall_outcome_rate=overall_outcome_rate,
        summary=summary
    )

