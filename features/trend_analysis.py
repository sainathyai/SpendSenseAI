"""
Behavioral Trend Analysis for SpendSenseAI.

Tracks changes in user behavior over time:
- Month-over-month trend calculation
- Behavior improvement detection
- Persona evolution tracking (are users \"graduating\"?)
- Early warning signals (savings declining, utilization rising)
- Trend visualization for operator dashboard
- Predictive signals (based on trajectory)
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from enum import Enum

from personas.persona_definition import PersonaType
from features.subscription_detection import detect_subscriptions_for_customer
from features.credit_utilization import analyze_credit_utilization_for_customer
from features.savings_pattern import analyze_savings_patterns_for_customer
from features.income_stability import analyze_income_stability_for_customer
from ingest.queries import get_transactions_by_customer


class TrendDirection(str, Enum):
    """Trend direction."""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"


@dataclass
class TrendDataPoint:
    """Single data point in a trend."""
    date: date
    value: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BehaviorTrend:
    """Behavior trend analysis."""
    behavior_type: str  # 'credit_utilization', 'savings', 'subscription', 'income'
    current_value: float
    previous_value: float
    change_percentage: float
    trend_direction: TrendDirection
    trend_strength: float  # 0.0 to 1.0
    data_points: List[TrendDataPoint]
    months_analyzed: int
    projected_value: Optional[float] = None
    early_warning: bool = False
    warning_message: Optional[str] = None


@dataclass
class PersonaEvolution:
    """Persona evolution tracking."""
    user_id: str
    current_persona: Optional[PersonaType]
    previous_persona: Optional[PersonaType]
    persona_changed: bool
    evolution_direction: str  # 'improving', 'declining', 'stable'
    months_in_current_persona: int
    potential_graduation: bool = False
    graduation_message: Optional[str] = None


@dataclass
class TrendAnalysis:
    """Complete trend analysis for a user."""
    user_id: str
    timestamp: datetime
    behavior_trends: List[BehaviorTrend]
    persona_evolution: PersonaEvolution
    early_warnings: List[str]
    summary: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.summary is None:
            self.summary = {}


def calculate_trend_direction(
    values: List[float],
    threshold: float = 0.05  # 5% change threshold
) -> Tuple[TrendDirection, float]:
    """
    Calculate trend direction from a list of values.
    
    Args:
        values: List of values over time
        threshold: Minimum change percentage to consider significant
        
    Returns:
        Tuple of (trend_direction, trend_strength)
    """
    if len(values) < 2:
        return TrendDirection.STABLE, 0.0
    
    first_half = values[:len(values)//2] if len(values) >= 4 else values[:1]
    second_half = values[len(values)//2:] if len(values) >= 4 else values[-1:]
    
    avg_first = sum(first_half) / len(first_half) if first_half else 0.0
    avg_second = sum(second_half) / len(second_half) if second_half else 0.0
    
    if avg_first == 0:
        return TrendDirection.STABLE, 0.0
    
    change_pct = abs((avg_second - avg_first) / avg_first)
    
    if change_pct < threshold:
        direction = TrendDirection.STABLE
    elif avg_second > avg_first:
        direction = TrendDirection.IMPROVING
    else:
        direction = TrendDirection.DECLINING
    
    # Calculate volatility
    if len(values) >= 3:
        variance = sum((v - sum(values) / len(values))**2 for v in values) / len(values)
        std_dev = variance ** 0.5
        mean_value = sum(values) / len(values)
        coefficient_of_variation = std_dev / mean_value if mean_value > 0 else 0.0
        
        if coefficient_of_variation > 0.3:
            direction = TrendDirection.VOLATILE
    
    trend_strength = min(change_pct, 1.0)
    
    return direction, trend_strength


def analyze_credit_utilization_trend(
    user_id: str,
    db_path: str,
    months: int = 6
) -> BehaviorTrend:
    """
    Analyze credit utilization trend over time.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        months: Number of months to analyze
        
    Returns:
        BehaviorTrend object
    """
    data_points = []
    
    # Calculate utilization for each month
    end_date = date.today()
    start_date = end_date - timedelta(days=months * 30)
    
    for month_offset in range(months):
        month_start = start_date + timedelta(days=month_offset * 30)
        month_end = month_start + timedelta(days=30)
        
        try:
            card_metrics, agg_metrics = analyze_credit_utilization_for_customer(
                user_id, db_path, 30
            )
            
            if card_metrics:
                utilization = agg_metrics.aggregate_utilization
                data_points.append(TrendDataPoint(
                    date=month_end,
                    value=utilization,
                    metadata={"balance": agg_metrics.total_balance, "limit": agg_metrics.total_limit}
                ))
        except Exception:
            pass
    
    if len(data_points) < 2:
        return BehaviorTrend(
            behavior_type="credit_utilization",
            current_value=0.0,
            previous_value=0.0,
            change_percentage=0.0,
            trend_direction=TrendDirection.STABLE,
            trend_strength=0.0,
            data_points=data_points,
            months_analyzed=len(data_points)
        )
    
    values = [dp.value for dp in data_points]
    current_value = values[-1] if values else 0.0
    previous_value = values[-2] if len(values) >= 2 else current_value
    
    change_pct = ((current_value - previous_value) / previous_value * 100) if previous_value > 0 else 0.0
    
    direction, strength = calculate_trend_direction(values)
    
    # Early warning if utilization is rising
    early_warning = direction == TrendDirection.DECLINING and current_value > 50
    warning_message = None
    if early_warning:
        warning_message = f"Credit utilization is rising and currently at {current_value:.1f}%"
    
    # Simple projection (linear extrapolation)
    if len(values) >= 2:
        projected_value = current_value + (current_value - previous_value)
    else:
        projected_value = None
    
    return BehaviorTrend(
        behavior_type="credit_utilization",
        current_value=current_value,
        previous_value=previous_value,
        change_percentage=change_pct,
        trend_direction=direction,
        trend_strength=strength,
        data_points=data_points,
        months_analyzed=len(data_points),
        projected_value=projected_value,
        early_warning=early_warning,
        warning_message=warning_message
    )


def analyze_savings_trend(
    user_id: str,
    db_path: str,
    months: int = 6
) -> BehaviorTrend:
    """
    Analyze savings trend over time.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        months: Number of months to analyze
        
    Returns:
        BehaviorTrend object
    """
    data_points = []
    
    # Calculate savings balance for each month
    end_date = date.today()
    start_date = end_date - timedelta(days=months * 30)
    
    for month_offset in range(months):
        month_start = start_date + timedelta(days=month_offset * 30)
        month_end = month_start + timedelta(days=30)
        
        try:
            savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(
                user_id, db_path, 180
            )
            
            if savings_accounts:
                balance = savings_metrics.total_savings_balance
                data_points.append(TrendDataPoint(
                    date=month_end,
                    value=balance,
                    metadata={"growth_rate": savings_metrics.overall_growth_rate}
                ))
        except Exception:
            pass
    
    if len(data_points) < 2:
        return BehaviorTrend(
            behavior_type="savings",
            current_value=0.0,
            previous_value=0.0,
            change_percentage=0.0,
            trend_direction=TrendDirection.STABLE,
            trend_strength=0.0,
            data_points=data_points,
            months_analyzed=len(data_points)
        )
    
    values = [dp.value for dp in data_points]
    current_value = values[-1] if values else 0.0
    previous_value = values[-2] if len(values) >= 2 else current_value
    
    change_pct = ((current_value - previous_value) / previous_value * 100) if previous_value > 0 else 0.0
    
    direction, strength = calculate_trend_direction(values)
    
    # Early warning if savings is declining
    early_warning = direction == TrendDirection.DECLINING and current_value > 0
    warning_message = None
    if early_warning:
        warning_message = f"Savings balance is declining from ${previous_value:,.2f} to ${current_value:,.2f}"
    
    # Simple projection
    if len(values) >= 2:
        projected_value = current_value + (current_value - previous_value)
        if projected_value < 0:
            projected_value = 0.0
    else:
        projected_value = None
    
    return BehaviorTrend(
        behavior_type="savings",
        current_value=current_value,
        previous_value=previous_value,
        change_percentage=change_pct,
        trend_direction=direction,
        trend_strength=strength,
        data_points=data_points,
        months_analyzed=len(data_points),
        projected_value=projected_value,
        early_warning=early_warning,
        warning_message=warning_message
    )


def analyze_subscription_trend(
    user_id: str,
    db_path: str,
    months: int = 6
) -> BehaviorTrend:
    """
    Analyze subscription trend over time.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        months: Number of months to analyze
        
    Returns:
        BehaviorTrend object
    """
    data_points = []
    
    # Calculate subscription count and spend for each month
    end_date = date.today()
    start_date = end_date - timedelta(days=months * 30)
    
    for month_offset in range(months):
        month_start = start_date + timedelta(days=month_offset * 30)
        month_end = month_start + timedelta(days=30)
        
        try:
            subscriptions, sub_metrics = detect_subscriptions_for_customer(
                user_id, db_path, window_days=90
            )
            
            monthly_spend = sub_metrics.get("total_monthly_recurring_spend", 0.0)
            subscription_count = sub_metrics.get("subscription_count", 0)
            
            # Use monthly spend as the value
            data_points.append(TrendDataPoint(
                date=month_end,
                value=monthly_spend,
                metadata={"subscription_count": subscription_count}
            ))
        except Exception:
            pass
    
    if len(data_points) < 2:
        return BehaviorTrend(
            behavior_type="subscription",
            current_value=0.0,
            previous_value=0.0,
            change_percentage=0.0,
            trend_direction=TrendDirection.STABLE,
            trend_strength=0.0,
            data_points=data_points,
            months_analyzed=len(data_points)
        )
    
    values = [dp.value for dp in data_points]
    current_value = values[-1] if values else 0.0
    previous_value = values[-2] if len(values) >= 2 else current_value
    
    change_pct = ((current_value - previous_value) / previous_value * 100) if previous_value > 0 else 0.0
    
    direction, strength = calculate_trend_direction(values)
    
    # Early warning if subscription spend is increasing significantly
    early_warning = direction == TrendDirection.DECLINING and change_pct > 20
    warning_message = None
    if early_warning:
        warning_message = f"Subscription spending increased by {change_pct:.1f}% from ${previous_value:.2f} to ${current_value:.2f}/month"
    
    return BehaviorTrend(
        behavior_type="subscription",
        current_value=current_value,
        previous_value=previous_value,
        change_percentage=change_pct,
        trend_direction=direction,
        trend_strength=strength,
        data_points=data_points,
        months_analyzed=len(data_points),
        early_warning=early_warning,
        warning_message=warning_message
    )


def track_persona_evolution(
    user_id: str,
    db_path: str,
    current_persona: PersonaType,
    previous_persona: Optional[PersonaType] = None
) -> PersonaEvolution:
    """
    Track persona evolution for a user.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        current_persona: Current persona type
        previous_persona: Previous persona type (if available)
        
    Returns:
        PersonaEvolution object
    """
    persona_changed = previous_persona is not None and previous_persona != current_persona
    
    # Determine evolution direction
    if persona_changed:
        # Define persona hierarchy (improving direction)
        persona_hierarchy = {
            PersonaType.FINANCIAL_FRAGILITY: 1,
            PersonaType.HIGH_UTILIZATION: 2,
            PersonaType.VARIABLE_INCOME_BUDGETER: 3,
            PersonaType.SUBSCRIPTION_HEAVY: 4,
            PersonaType.SAVINGS_BUILDER: 5
        }
        
        current_level = persona_hierarchy.get(current_persona, 0)
        previous_level = persona_hierarchy.get(previous_persona, 0)
        
        if current_level > previous_level:
            evolution_direction = "improving"
            potential_graduation = current_persona == PersonaType.SAVINGS_BUILDER
            graduation_message = "User has graduated to Savings Builder persona!" if potential_graduation else None
        elif current_level < previous_level:
            evolution_direction = "declining"
            potential_graduation = False
            graduation_message = None
        else:
            evolution_direction = "stable"
            potential_graduation = False
            graduation_message = None
    else:
        evolution_direction = "stable"
        potential_graduation = False
        graduation_message = None
    
    # Estimate months in current persona (simplified - would need historical data)
    months_in_current_persona = 3  # Default estimate
    
    return PersonaEvolution(
        user_id=user_id,
        current_persona=current_persona,
        previous_persona=previous_persona,
        persona_changed=persona_changed,
        evolution_direction=evolution_direction,
        months_in_current_persona=months_in_current_persona,
        potential_graduation=potential_graduation,
        graduation_message=graduation_message
    )


def analyze_trends_for_user(
    user_id: str,
    db_path: str,
    current_persona: PersonaType,
    previous_persona: Optional[PersonaType] = None,
    months: int = 6
) -> TrendAnalysis:
    """
    Analyze all trends for a user.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        current_persona: Current persona type
        previous_persona: Previous persona type (if available)
        months: Number of months to analyze
        
    Returns:
        TrendAnalysis object
    """
    # Analyze behavior trends
    behavior_trends = []
    
    try:
        utilization_trend = analyze_credit_utilization_trend(user_id, db_path, months)
        behavior_trends.append(utilization_trend)
    except Exception:
        pass
    
    try:
        savings_trend = analyze_savings_trend(user_id, db_path, months)
        behavior_trends.append(savings_trend)
    except Exception:
        pass
    
    try:
        subscription_trend = analyze_subscription_trend(user_id, db_path, months)
        behavior_trends.append(subscription_trend)
    except Exception:
        pass
    
    # Track persona evolution
    persona_evolution = track_persona_evolution(user_id, db_path, current_persona, previous_persona)
    
    # Collect early warnings
    early_warnings = []
    for trend in behavior_trends:
        if trend.early_warning and trend.warning_message:
            early_warnings.append(trend.warning_message)
    
    if persona_evolution.potential_graduation and persona_evolution.graduation_message:
        early_warnings.append(persona_evolution.graduation_message)
    
    # Create summary
    summary = {
        "total_trends": len(behavior_trends),
        "improving_trends": sum(1 for t in behavior_trends if t.trend_direction == TrendDirection.IMPROVING),
        "declining_trends": sum(1 for t in behavior_trends if t.trend_direction == TrendDirection.DECLINING),
        "early_warnings": len(early_warnings),
        "persona_changed": persona_evolution.persona_changed
    }
    
    return TrendAnalysis(
        user_id=user_id,
        timestamp=datetime.now(),
        behavior_trends=behavior_trends,
        persona_evolution=persona_evolution,
        early_warnings=early_warnings,
        summary=summary
    )

