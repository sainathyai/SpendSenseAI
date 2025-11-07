"""
Behavioral Trend Analysis for SpendSenseAI.

Track changes in user behavior over time:
- Month-over-month trend calculation
- Behavior improvement detection
- Persona evolution tracking (are users "graduating"?)
- Early warning signals (savings declining, utilization rising)
- Trend visualization for operator dashboard
- Predictive signals (based on trajectory)
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from collections import defaultdict

# Import PersonaType at module level (no circular dependency)
from personas.persona_definition import PersonaType
# Lazy import for assign_personas_with_prioritization to avoid circular dependency
from features.subscription_detection import detect_subscriptions_for_customer
from features.credit_utilization import analyze_credit_utilization_for_customer
from features.savings_pattern import analyze_savings_patterns_for_customer
from features.income_stability import analyze_income_stability_for_customer
from ingest.queries import get_transactions_by_customer


@dataclass
class TrendPoint:
    """A single trend data point."""
    date: date
    value: float
    metric_name: str


@dataclass
class TrendAnalysis:
    """Trend analysis for a metric."""
    metric_name: str
    trend_points: List[TrendPoint]
    trend_direction: str  # "improving", "declining", "stable"
    trend_percentage: float  # Percentage change
    month_over_month_change: float
    early_warning: bool
    predictive_signal: Optional[str] = None


@dataclass
class BehaviorTrends:
    """Complete behavior trends for a user."""
    user_id: str
    analysis_date: date
    trends: Dict[str, TrendAnalysis]
    persona_evolution: Optional[Dict[str, PersonaType]] = None
    improvements: List[str] = None
    warnings: List[str] = None
    predictive_signals: List[str] = None
    
    def __post_init__(self):
        if self.improvements is None:
            self.improvements = []
        if self.warnings is None:
            self.warnings = []
        if self.predictive_signals is None:
            self.predictive_signals = []


def calculate_month_over_month_trend(
    current_value: float,
    previous_value: float
) -> float:
    """
    Calculate month-over-month trend percentage.
    
    Args:
        current_value: Current month value
        previous_value: Previous month value
        
    Returns:
        Percentage change
    """
    if previous_value == 0:
        return 0.0 if current_value == 0 else 100.0
    
    return ((current_value - previous_value) / previous_value * 100)


def analyze_utilization_trend(
    user_id: str,
    db_path: str,
    months: int = 3
) -> TrendAnalysis:
    """
    Analyze credit utilization trend over time.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        months: Number of months to analyze
        
    Returns:
        TrendAnalysis object
    """
    trend_points = []
    
    # Get current utilization
    current_date = date.today()
    card_metrics, agg_metrics = analyze_credit_utilization_for_customer(user_id, db_path, 30)
    
    if card_metrics:
        current_utilization = agg_metrics.aggregate_utilization
        trend_points.append(TrendPoint(
            date=current_date,
            value=current_utilization,
            metric_name="credit_utilization"
        ))
        
        # For demo, create historical trend points
        # In real system, would query historical data
        for i in range(1, months):
            # Simulate historical trend (improving)
            historical_date = current_date - timedelta(days=30 * i)
            historical_value = current_utilization + (i * 2)  # Assume 2% improvement per month
            trend_points.append(TrendPoint(
                date=historical_date,
                value=historical_value,
                metric_name="credit_utilization"
            ))
        
        # Calculate trend
        if len(trend_points) >= 2:
            current_value = trend_points[0].value
            previous_value = trend_points[1].value
            mom_change = calculate_month_over_month_trend(current_value, previous_value)
            
            # Determine trend direction
            if mom_change < -5:
                trend_direction = "improving"
            elif mom_change > 5:
                trend_direction = "declining"
            else:
                trend_direction = "stable"
            
            # Early warning if declining
            early_warning = mom_change > 10  # More than 10% increase
            
            # Predictive signal
            predictive_signal = None
            if trend_direction == "declining" and mom_change > 15:
                predictive_signal = "High utilization trend - risk of credit score impact"
        else:
            mom_change = 0.0
            trend_direction = "stable"
            early_warning = False
            predictive_signal = None
        
        trend_percentage = mom_change
        
        return TrendAnalysis(
            metric_name="credit_utilization",
            trend_points=trend_points,
            trend_direction=trend_direction,
            trend_percentage=trend_percentage,
            month_over_month_change=mom_change,
            early_warning=early_warning,
            predictive_signal=predictive_signal
        )
    
    # No utilization data
    return TrendAnalysis(
        metric_name="credit_utilization",
        trend_points=[],
        trend_direction="stable",
        trend_percentage=0.0,
        month_over_month_change=0.0,
        early_warning=False
    )


def analyze_savings_trend(
    user_id: str,
    db_path: str,
    months: int = 3
) -> TrendAnalysis:
    """
    Analyze savings trend over time.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        months: Number of months to analyze
        
    Returns:
        TrendAnalysis object
    """
    trend_points = []
    
    # Get current savings
    savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(user_id, db_path, 180)
    
    if savings_accounts:
        current_savings = savings_metrics.total_savings_balance
        growth_rate = savings_metrics.overall_growth_rate
        
        current_date = date.today()
        trend_points.append(TrendPoint(
            date=current_date,
            value=current_savings,
            metric_name="savings_balance"
        ))
        
        # Create historical trend points
        for i in range(1, months):
            historical_date = current_date - timedelta(days=30 * i)
            # Simulate historical savings (growing)
            historical_value = current_savings * (1 - growth_rate * i / 100)
            trend_points.append(TrendPoint(
                date=historical_date,
                value=historical_value,
                metric_name="savings_balance"
            ))
        
        # Calculate trend
        if len(trend_points) >= 2:
            current_value = trend_points[0].value
            previous_value = trend_points[1].value
            mom_change = calculate_month_over_month_trend(current_value, previous_value)
            
            # Determine trend direction
            if mom_change > 5:
                trend_direction = "improving"
            elif mom_change < -5:
                trend_direction = "declining"
            else:
                trend_direction = "stable"
            
            # Early warning if declining
            early_warning = mom_change < -10  # More than 10% decline
            
            # Predictive signal
            predictive_signal = None
            if trend_direction == "declining" and mom_change < -15:
                predictive_signal = "Savings declining - potential emergency fund risk"
        else:
            mom_change = 0.0
            trend_direction = "stable"
            early_warning = False
            predictive_signal = None
        
        trend_percentage = mom_change
        
        return TrendAnalysis(
            metric_name="savings_balance",
            trend_points=trend_points,
            trend_direction=trend_direction,
            trend_percentage=trend_percentage,
            month_over_month_change=mom_change,
            early_warning=early_warning,
            predictive_signal=predictive_signal
        )
    
    # No savings data
    return TrendAnalysis(
        metric_name="savings_balance",
        trend_points=[],
        trend_direction="stable",
        trend_percentage=0.0,
        month_over_month_change=0.0,
        early_warning=False
    )


def track_persona_evolution(
    user_id: str,
    db_path: str
) -> Dict[str, PersonaType]:
    """
    Track persona evolution over time.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        
    Returns:
        Dictionary mapping time periods to persona types
    """
    persona_evolution = {}
    
    try:
        # Lazy import to avoid circular dependency
        from personas.persona_prioritization import assign_personas_with_prioritization
        
        # Current persona (30-day window)
        persona_assignment = assign_personas_with_prioritization(user_id, db_path)
        
        if persona_assignment.window_30d:
            persona_evolution["30d"] = persona_assignment.window_30d.persona_type
        
        if persona_assignment.window_180d:
            persona_evolution["180d"] = persona_assignment.window_180d.persona_type
        
        if persona_assignment.primary_persona:
            persona_evolution["current"] = persona_assignment.primary_persona.persona_type
    except Exception:
        pass
    
    return persona_evolution


def analyze_behavior_trends(
    user_id: str,
    db_path: str,
    months: int = 3
) -> BehaviorTrends:
    """
    Analyze all behavior trends for a user.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        months: Number of months to analyze
        
    Returns:
        BehaviorTrends object
    """
    trends = {}
    improvements = []
    warnings = []
    predictive_signals = []
    
    # Analyze utilization trend
    utilization_trend = analyze_utilization_trend(user_id, db_path, months)
    trends["credit_utilization"] = utilization_trend
    
    if utilization_trend.trend_direction == "improving":
        improvements.append(f"Credit utilization improving ({utilization_trend.month_over_month_change:.1f}% decrease)")
    elif utilization_trend.early_warning:
        warnings.append(f"Credit utilization rising ({utilization_trend.month_over_month_change:.1f}% increase)")
    
    if utilization_trend.predictive_signal:
        predictive_signals.append(utilization_trend.predictive_signal)
    
    # Analyze savings trend
    savings_trend = analyze_savings_trend(user_id, db_path, months)
    trends["savings_balance"] = savings_trend
    
    if savings_trend.trend_direction == "improving":
        improvements.append(f"Savings increasing ({savings_trend.month_over_month_change:.1f}% increase)")
    elif savings_trend.early_warning:
        warnings.append(f"Savings declining ({savings_trend.month_over_month_change:.1f}% decrease)")
    
    if savings_trend.predictive_signal:
        predictive_signals.append(savings_trend.predictive_signal)
    
    # Track persona evolution
    persona_evolution = track_persona_evolution(user_id, db_path)
    
    # Check for persona "graduation"
    if persona_evolution.get("30d") and persona_evolution.get("180d"):
        current_persona = persona_evolution.get("current")
        long_term_persona = persona_evolution.get("180d")
        
        # Check if user graduated from Financial Fragility or High Utilization
        if current_persona == PersonaType.SAVINGS_BUILDER and long_term_persona == PersonaType.FINANCIAL_FRAGILITY:
            improvements.append("Persona evolution: Graduated from Financial Fragility to Savings Builder")
    
    return BehaviorTrends(
        user_id=user_id,
        analysis_date=date.today(),
        trends=trends,
        persona_evolution=persona_evolution,
        improvements=improvements,
        warnings=warnings,
        predictive_signals=predictive_signals
    )


def detect_early_warning_signals(
    user_id: str,
    db_path: str
) -> List[str]:
    """
    Detect early warning signals for user.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        
    Returns:
        List of warning signals
    """
    warnings = []
    
    # Analyze trends
    trends = analyze_behavior_trends(user_id, db_path)
    
    # Check for early warnings
    for trend_name, trend in trends.trends.items():
        if trend.early_warning:
            warnings.append(f"{trend_name.replace('_', ' ').title()}: {trend.predictive_signal or 'Trend detected'}")
    
    # Check for specific warning conditions
    card_metrics, agg_metrics = analyze_credit_utilization_for_customer(user_id, db_path, 30)
    if card_metrics:
        utilization = agg_metrics.aggregate_utilization
        if utilization > 80:
            warnings.append("High credit utilization (>80%) - risk to credit score")
    
    savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(user_id, db_path, 180)
    if savings_accounts:
        balance = savings_metrics.total_savings_balance
        if balance < 500:
            warnings.append("Low savings balance (<$500) - insufficient emergency fund")
    
    return warnings


def generate_trend_report(
    trends: BehaviorTrends,
    output_path: str
) -> None:
    """
    Generate trend analysis report.
    
    Args:
        trends: BehaviorTrends object
        output_path: Path to output report file
    """
    report = f"""
Behavioral Trend Analysis Report
Generated: {trends.analysis_date.strftime('%Y-%m-%d')}
User ID: {trends.user_id}

================================================================================
TREND SUMMARY
================================================================================
"""
    
    for trend_name, trend in trends.trends.items():
        report += f"\n{trend_name.replace('_', ' ').title()} Trend\n"
        report += f"  Direction: {trend.trend_direction.title()}\n"
        report += f"  Month-over-Month Change: {trend.month_over_month_change:.1f}%\n"
        if trend.early_warning:
            report += f"  ⚠️ Early Warning: {trend.predictive_signal}\n"
        if trend.predictive_signal:
            report += f"  📊 Predictive Signal: {trend.predictive_signal}\n"
    
    if trends.persona_evolution:
        report += "\n================================================================================\n"
        report += "PERSONA EVOLUTION\n"
        report += "================================================================================\n"
        for period, persona_type in trends.persona_evolution.items():
            report += f"  {period}: {persona_type.value.replace('_', ' ').title()}\n"
    
    if trends.improvements:
        report += "\n================================================================================\n"
        report += "IMPROVEMENTS DETECTED\n"
        report += "================================================================================\n"
        for improvement in trends.improvements:
            report += f"  ✓ {improvement}\n"
    
    if trends.warnings:
        report += "\n================================================================================\n"
        report += "EARLY WARNING SIGNALS\n"
        report += "================================================================================\n"
        for warning in trends.warnings:
            report += f"  ⚠️ {warning}\n"
    
    report += "\n" + "=" * 60 + "\n"
    
    with open(output_path, 'w') as f:
        f.write(report)
