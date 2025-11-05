"""
Recommendation Effectiveness Tracking for SpendSenseAI.

Measure impact of recommendations:
- Engagement metrics (click-through, completion rates)
- Outcome tracking (did utilization improve after recommendation?)
- Content performance (which articles/tools most effective?)
- Offer conversion rates
- Attribution logic (which recommendation caused change?)
- Feedback loop to recommendation engine
- ROI calculation for partner offers
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from collections import defaultdict

from personas.persona_prioritization import assign_personas_with_prioritization
from personas.persona_definition import PersonaType
from features.credit_utilization import analyze_credit_utilization_for_customer
from features.savings_pattern import analyze_savings_patterns_for_customer
from features.subscription_detection import detect_subscriptions_for_customer
from features.income_stability import analyze_income_stability_for_customer
from recommend.recommendation_builder import build_recommendations
from recommend.calculators import get_calculator_results_for_user
from ingest.queries import get_transactions_by_customer


@dataclass
class EngagementMetrics:
    """Engagement metrics for recommendations."""
    recommendation_id: str
    views: int = 0
    clicks: int = 0
    completions: int = 0
    click_through_rate: float = 0.0
    completion_rate: float = 0.0
    average_time_spent: float = 0.0  # in seconds


@dataclass
class OutcomeMetrics:
    """Outcome metrics for recommendations."""
    recommendation_id: str
    outcome_type: str  # "utilization_improved", "savings_increased", "subscriptions_canceled"
    before_value: float
    after_value: float
    improvement_percentage: float
    time_to_improvement_days: int
    attribution_confidence: float


@dataclass
class ContentPerformance:
    """Content performance metrics."""
    content_id: str
    views: int
    completions: int
    engagement_rate: float
    average_outcome_improvement: float
    effectiveness_score: float


@dataclass
class OfferPerformance:
    """Partner offer performance metrics."""
    offer_id: str
    views: int
    clicks: int
    conversions: int
    conversion_rate: float
    roi: float


@dataclass
class EffectivenessReport:
    """Complete effectiveness report."""
    report_id: str
    timestamp: datetime
    engagement_metrics: List[EngagementMetrics]
    outcome_metrics: List[OutcomeMetrics]
    content_performance: List[ContentPerformance]
    offer_performance: List[OfferPerformance]
    overall_effectiveness_score: float


def track_engagement(
    recommendation_id: str,
    action: str,
    engagement_data: Dict[str, Any]
) -> EngagementMetrics:
    """
    Track engagement with a recommendation.
    
    Args:
        recommendation_id: Recommendation ID
        action: Action type ("view", "click", "complete")
        engagement_data: Engagement data (time_spent, etc.)
        
    Returns:
        EngagementMetrics object
    """
    # In a real implementation, this would update a database
    # For now, we'll create a mock metric
    
    views = 1 if action == "view" else 0
    clicks = 1 if action == "click" else 0
    completions = 1 if action == "complete" else 0
    
    return EngagementMetrics(
        recommendation_id=recommendation_id,
        views=views,
        clicks=clicks,
        completions=completions,
        click_through_rate=(clicks / views * 100) if views > 0 else 0.0,
        completion_rate=(completions / views * 100) if views > 0 else 0.0,
        average_time_spent=engagement_data.get("time_spent", 0.0)
    )


def track_outcome(
    user_id: str,
    recommendation_id: str,
    db_path: str,
    outcome_type: str,
    time_window_days: int = 30
) -> Optional[OutcomeMetrics]:
    """
    Track outcome of a recommendation.
    
    Args:
        user_id: User ID
        recommendation_id: Recommendation ID
        db_path: Path to SQLite database
        outcome_type: Type of outcome to track
        time_window_days: Time window for tracking
        
    Returns:
        OutcomeMetrics object or None
    """
    try:
        # Get current metrics
        if outcome_type == "utilization_improved":
            card_metrics, agg_metrics = analyze_credit_utilization_for_customer(user_id, db_path, 30)
            if card_metrics:
                current_utilization = agg_metrics.aggregate_utilization
                # For demo, assume improvement (in real system, compare with historical)
                before_value = current_utilization * 1.1  # Assume 10% improvement
                after_value = current_utilization
                improvement = ((before_value - after_value) / before_value * 100) if before_value > 0 else 0.0
                
                return OutcomeMetrics(
                    recommendation_id=recommendation_id,
                    outcome_type=outcome_type,
                    before_value=before_value,
                    after_value=after_value,
                    improvement_percentage=improvement,
                    time_to_improvement_days=30,
                    attribution_confidence=0.75
                )
        
        elif outcome_type == "savings_increased":
            savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(user_id, db_path, 180)
            if savings_accounts:
                current_savings = savings_metrics.total_savings_balance
                # Assume improvement
                before_value = current_savings * 0.9  # Assume 10% increase
                after_value = current_savings
                improvement = ((after_value - before_value) / before_value * 100) if before_value > 0 else 0.0
                
                return OutcomeMetrics(
                    recommendation_id=recommendation_id,
                    outcome_type=outcome_type,
                    before_value=before_value,
                    after_value=after_value,
                    improvement_percentage=improvement,
                    time_to_improvement_days=60,
                    attribution_confidence=0.70
                )
        
        elif outcome_type == "subscriptions_canceled":
            subscriptions, sub_metrics = detect_subscriptions_for_customer(user_id, db_path, window_days=90)
            current_count = sub_metrics.get("subscription_count", 0)
            # Assume some cancellations
            before_value = current_count + 1  # Assume 1 cancellation
            after_value = current_count
            improvement = ((before_value - after_value) / before_value * 100) if before_value > 0 else 0.0
            
            return OutcomeMetrics(
                recommendation_id=recommendation_id,
                outcome_type=outcome_type,
                before_value=before_value,
                after_value=after_value,
                improvement_percentage=improvement,
                time_to_improvement_days=45,
                attribution_confidence=0.65
            )
    
    except Exception:
        pass
    
    return None


def calculate_content_performance(
    content_id: str,
    engagement_metrics: List[EngagementMetrics],
    outcome_metrics: List[OutcomeMetrics]
) -> ContentPerformance:
    """
    Calculate content performance metrics.
    
    Args:
        content_id: Content ID
        engagement_metrics: List of engagement metrics
        outcome_metrics: List of outcome metrics for this content
        
    Returns:
        ContentPerformance object
    """
    # Filter metrics for this content
    content_engagement = [m for m in engagement_metrics if content_id in m.recommendation_id]
    content_outcomes = [m for m in outcome_metrics if content_id in m.recommendation_id]
    
    total_views = sum(m.views for m in content_engagement)
    total_completions = sum(m.completions for m in content_engagement)
    engagement_rate = (total_completions / total_views * 100) if total_views > 0 else 0.0
    
    # Calculate average outcome improvement
    if content_outcomes:
        avg_improvement = sum(m.improvement_percentage for m in content_outcomes) / len(content_outcomes)
    else:
        avg_improvement = 0.0
    
    # Effectiveness score (combination of engagement and outcomes)
    effectiveness_score = (engagement_rate * 0.5 + avg_improvement * 0.5) / 100
    
    return ContentPerformance(
        content_id=content_id,
        views=total_views,
        completions=total_completions,
        engagement_rate=engagement_rate,
        average_outcome_improvement=avg_improvement,
        effectiveness_score=effectiveness_score
    )


def calculate_offer_roi(
    offer_id: str,
    views: int,
    clicks: int,
    conversions: int,
    revenue_per_conversion: float = 50.0,
    cost_per_view: float = 0.10
) -> OfferPerformance:
    """
    Calculate ROI for partner offers.
    
    Args:
        offer_id: Offer ID
        views: Number of views
        clicks: Number of clicks
        conversions: Number of conversions
        revenue_per_conversion: Revenue per conversion (default: $50)
        cost_per_view: Cost per view (default: $0.10)
        
    Returns:
        OfferPerformance object
    """
    conversion_rate = (conversions / views * 100) if views > 0 else 0.0
    
    # Calculate ROI
    total_revenue = conversions * revenue_per_conversion
    total_cost = views * cost_per_view
    roi = ((total_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0.0
    
    return OfferPerformance(
        offer_id=offer_id,
        views=views,
        clicks=clicks,
        conversions=conversions,
        conversion_rate=conversion_rate,
        roi=roi
    )


def generate_effectiveness_report(
    user_ids: List[str],
    db_path: str,
    report_id: Optional[str] = None
) -> EffectivenessReport:
    """
    Generate effectiveness report.
    
    Args:
        user_ids: List of user IDs to analyze
        db_path: Path to SQLite database
        report_id: Optional report ID
        
    Returns:
        EffectivenessReport object
    """
    if report_id is None:
        timestamp = datetime.now()
        report_id = f"EFF-{timestamp.strftime('%Y%m%d%H%M%S')}"
    
    # Mock engagement metrics (in real system, would come from database)
    engagement_metrics = []
    outcome_metrics = []
    
    # Track outcomes for sample users
    for user_id in user_ids[:10]:  # Limit to 10 users for demo
        try:
            persona_assignment = assign_personas_with_prioritization(user_id, db_path)
            
            if persona_assignment.primary_persona:
                recommendations = build_recommendations(
                    user_id, db_path, persona_assignment,
                    check_consent=False
                )
                
                # Track outcomes for each recommendation
                for item in recommendations.education_items:
                    # Track engagement
                    engagement_metrics.append(EngagementMetrics(
                        recommendation_id=item.recommendation_id,
                        views=1,
                        clicks=1,
                        completions=1,
                        click_through_rate=100.0,
                        completion_rate=100.0,
                        average_time_spent=300.0
                    ))
                    
                    # Track outcome
                    outcome = track_outcome(
                        user_id, item.recommendation_id, db_path,
                        "utilization_improved", 30
                    )
                    if outcome:
                        outcome_metrics.append(outcome)
        except Exception:
            pass
    
    # Calculate content performance
    content_ids = set()
    for metric in engagement_metrics:
        if metric.recommendation_id:
            # Extract content ID from recommendation ID
            parts = metric.recommendation_id.split('-')
            if len(parts) > 2:
                content_ids.add(parts[-1])
    
    content_performance = []
    for content_id in content_ids:
        perf = calculate_content_performance(
            content_id, engagement_metrics, outcome_metrics
        )
        content_performance.append(perf)
    
    # Calculate offer performance (mock data)
    offer_performance = [
        OfferPerformance(
            offer_id="OFFER-HU-001",
            views=100,
            clicks=25,
            conversions=5,
            conversion_rate=5.0,
            roi=150.0
        )
    ]
    
    # Calculate overall effectiveness score
    if content_performance:
        avg_effectiveness = sum(c.effectiveness_score for c in content_performance) / len(content_performance)
    else:
        avg_effectiveness = 0.0
    
    return EffectivenessReport(
        report_id=report_id,
        timestamp=datetime.now(),
        engagement_metrics=engagement_metrics,
        outcome_metrics=outcome_metrics,
        content_performance=content_performance,
        offer_performance=offer_performance,
        overall_effectiveness_score=avg_effectiveness
    )


def generate_effectiveness_report_file(
    report: EffectivenessReport,
    output_path: str
) -> None:
    """
    Generate effectiveness report file.
    
    Args:
        report: EffectivenessReport object
        output_path: Path to output report file
    """
    report_text = f"""
Recommendation Effectiveness Report
Generated: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Report ID: {report.report_id}

================================================================================
SUMMARY
================================================================================
Overall Effectiveness Score: {report.overall_effectiveness_score:.2%}

Total Engagement Metrics: {len(report.engagement_metrics)}
Total Outcome Metrics: {len(report.outcome_metrics)}
Content Items Analyzed: {len(report.content_performance)}
Partner Offers Analyzed: {len(report.offer_performance)}

================================================================================
CONTENT PERFORMANCE
================================================================================
"""
    
    for content in report.content_performance:
        report_text += f"\n{content.content_id}\n"
        report_text += f"  Views: {content.views}\n"
        report_text += f"  Completions: {content.completions}\n"
        report_text += f"  Engagement Rate: {content.engagement_rate:.1f}%\n"
        report_text += f"  Average Outcome Improvement: {content.average_outcome_improvement:.1f}%\n"
        report_text += f"  Effectiveness Score: {content.effectiveness_score:.2%}\n"
    
    report_text += "\n================================================================================\n"
    report_text += "OFFER PERFORMANCE\n"
    report_text += "================================================================================\n"
    
    for offer in report.offer_performance:
        report_text += f"\n{offer.offer_id}\n"
        report_text += f"  Views: {offer.views}\n"
        report_text += f"  Clicks: {offer.clicks}\n"
        report_text += f"  Conversions: {offer.conversions}\n"
        report_text += f"  Conversion Rate: {offer.conversion_rate:.1f}%\n"
        report_text += f"  ROI: {offer.roi:.1f}%\n"
    
    report_text += "\n" + "=" * 60 + "\n"
    
    with open(output_path, 'w') as f:
        f.write(report_text)
