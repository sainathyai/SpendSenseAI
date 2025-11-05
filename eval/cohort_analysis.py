"""
Cohort Analysis & Segmentation for SpendSenseAI.

Groups users by characteristics for insights:
- Cohort definition (by age, income level, join date, geography)
- Persona distribution by cohort
- Average metrics by cohort
- Cohort performance over time
- Fairness analysis (outcome parity across demographics)
- Report generation for operator view
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from enum import Enum
import json

from personas.persona_definition import PersonaType
from personas.persona_prioritization import assign_personas_with_prioritization
from features.credit_utilization import analyze_credit_utilization_for_customer
from features.savings_pattern import analyze_savings_patterns_for_customer
from features.subscription_detection import detect_subscriptions_for_customer
from features.income_stability import analyze_income_stability_for_customer
from ingest.queries import get_accounts_by_customer


class CohortDimension(str, Enum):
    """Cohort dimensions."""
    AGE = "age"
    INCOME_LEVEL = "income_level"
    JOIN_DATE = "join_date"
    GEOGRAPHY = "geography"
    PERSONA = "persona"


@dataclass
class CohortDefinition:
    """Cohort definition."""
    cohort_id: str
    cohort_name: str
    dimension: CohortDimension
    criteria: Dict[str, Any]  # Criteria for cohort membership
    user_ids: List[str]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CohortMetrics:
    """Metrics for a cohort."""
    cohort_id: str
    cohort_name: str
    user_count: int
    persona_distribution: Dict[str, int]
    persona_percentages: Dict[str, float]
    average_utilization: float
    average_savings_balance: float
    average_monthly_income: float
    average_subscription_spend: float
    recommendation_rate: float
    positive_outcome_rate: float = 0.0
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}


@dataclass
class CohortAnalysis:
    """Cohort analysis results."""
    analysis_id: str
    timestamp: datetime
    cohorts: List[CohortDefinition]
    cohort_metrics: List[CohortMetrics]
    fairness_analysis: Dict[str, float]  # Outcome parity across cohorts
    summary: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.summary is None:
            self.summary = {}


def create_age_cohorts(
    user_ids: List[str],
    age_ranges: List[tuple] = None
) -> List[CohortDefinition]:
    """
    Create cohorts by age (simplified - would need age data).
    
    Args:
        user_ids: List of user IDs
        age_ranges: List of (min_age, max_age, name) tuples
        
    Returns:
        List of CohortDefinition objects
    """
    if age_ranges is None:
        age_ranges = [
            (18, 25, "18-25"),
            (26, 35, "26-35"),
            (36, 45, "36-45"),
            (46, 55, "46-55"),
            (56, 100, "56+")
        ]
    
    cohorts = []
    for min_age, max_age, name in age_ranges:
        # Simplified - would need actual age data
        # For now, split users evenly
        cohort_size = len(user_ids) // len(age_ranges)
        start_idx = len(cohorts) * cohort_size
        end_idx = start_idx + cohort_size if len(cohorts) < len(age_ranges) - 1 else len(user_ids)
        
        cohorts.append(CohortDefinition(
            cohort_id=f"COHORT-AGE-{name}",
            cohort_name=f"Age {name}",
            dimension=CohortDimension.AGE,
            criteria={"min_age": min_age, "max_age": max_age},
            user_ids=user_ids[start_idx:end_idx],
            metadata={"age_range": f"{min_age}-{max_age}"}
        ))
    
    return cohorts


def create_income_cohorts(
    user_ids: List[str],
    income_levels: List[tuple] = None
) -> List[CohortDefinition]:
    """
    Create cohorts by income level (simplified - would need income data).
    
    Args:
        user_ids: List of user IDs
        income_levels: List of (min_income, max_income, name) tuples
        
    Returns:
        List of CohortDefinition objects
    """
    if income_levels is None:
        income_levels = [
            (0, 30000, "Low Income"),
            (30000, 60000, "Middle Income"),
            (60000, 100000, "Upper Middle Income"),
            (100000, 200000, "High Income"),
            (200000, float('inf'), "Very High Income")
        ]
    
    cohorts = []
    for min_income, max_income, name in income_levels:
        # Simplified - would need actual income data
        # For now, split users evenly
        cohort_size = len(user_ids) // len(income_levels)
        start_idx = len(cohorts) * cohort_size
        end_idx = start_idx + cohort_size if len(cohorts) < len(income_levels) - 1 else len(user_ids)
        
        cohorts.append(CohortDefinition(
            cohort_id=f"COHORT-INCOME-{name.replace(' ', '_')}",
            cohort_name=f"Income {name}",
            dimension=CohortDimension.INCOME_LEVEL,
            criteria={"min_income": min_income, "max_income": max_income},
            user_ids=user_ids[start_idx:end_idx],
            metadata={"income_range": f"${min_income:,.0f}-${max_income:,.0f}" if max_income != float('inf') else f"${min_income:,.0f}+"}
        ))
    
    return cohorts


def create_persona_cohorts(
    user_ids: List[str],
    db_path: str
) -> List[CohortDefinition]:
    """
    Create cohorts by persona.
    
    Args:
        user_ids: List of user IDs
        db_path: Path to SQLite database
        
    Returns:
        List of CohortDefinition objects
    """
    persona_groups = {persona: [] for persona in PersonaType}
    
    for user_id in user_ids:
        try:
            persona_assignment = assign_personas_with_prioritization(user_id, db_path)
            if persona_assignment.primary_persona:
                persona_type = persona_assignment.primary_persona.persona_type
                persona_groups[persona_type].append(user_id)
        except Exception:
            pass
    
    cohorts = []
    for persona_type, user_list in persona_groups.items():
        if user_list:
            cohorts.append(CohortDefinition(
                cohort_id=f"COHORT-PERSONA-{persona_type.value}",
                cohort_name=f"Persona: {persona_type.value.replace('_', ' ').title()}",
                dimension=CohortDimension.PERSONA,
                criteria={"persona_type": persona_type.value},
                user_ids=user_list,
                metadata={"persona_type": persona_type.value}
            ))
    
    return cohorts


def calculate_cohort_metrics(
    cohort: CohortDefinition,
    db_path: str
) -> CohortMetrics:
    """
    Calculate metrics for a cohort.
    
    Args:
        cohort: CohortDefinition object
        db_path: Path to SQLite database
        
    Returns:
        CohortMetrics object
    """
    persona_distribution = {}
    total_utilization = 0.0
    total_savings = 0.0
    total_income = 0.0
    total_subscription_spend = 0.0
    users_with_recommendations = 0
    users_analyzed = 0
    
    for user_id in cohort.user_ids:
        try:
            # Get persona
            persona_assignment = assign_personas_with_prioritization(user_id, db_path)
            
            if persona_assignment.primary_persona:
                persona_type = persona_assignment.primary_persona.persona_type.value
                persona_distribution[persona_type] = persona_distribution.get(persona_type, 0) + 1
            
            # Get utilization
            card_metrics, agg_metrics = analyze_credit_utilization_for_customer(user_id, db_path, 30)
            if card_metrics:
                total_utilization += agg_metrics.aggregate_utilization
                users_analyzed += 1
            
            # Get savings
            savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(user_id, db_path, 180)
            if savings_accounts:
                total_savings += savings_metrics.total_savings_balance
            
            # Get subscription spend
            subscriptions, sub_metrics = detect_subscriptions_for_customer(user_id, db_path, window_days=90)
            if sub_metrics.get('subscription_count', 0) > 0:
                total_subscription_spend += sub_metrics.get('total_monthly_recurring_spend', 0)
            
            # Estimate income (simplified - would need actual income data)
            # For now, estimate from transactions
            accounts = get_accounts_by_customer(user_id, db_path)
            if accounts:
                # Rough estimate based on account balances
                estimated_income = sum(acc.balances.current for acc in accounts) * 0.1  # Simplified
                total_income += estimated_income
            
            # Check recommendations (simplified)
            if persona_assignment.primary_persona:
                users_with_recommendations += 1
            
        except Exception:
            pass
    
    user_count = len(cohort.user_ids)
    
    # Calculate percentages
    total_personas = sum(persona_distribution.values())
    persona_percentages = {
        persona: (count / total_personas * 100) if total_personas > 0 else 0.0
        for persona, count in persona_distribution.items()
    }
    
    # Calculate averages
    average_utilization = (total_utilization / users_analyzed) if users_analyzed > 0 else 0.0
    average_savings_balance = (total_savings / user_count) if user_count > 0 else 0.0
    average_monthly_income = (total_income / user_count) if user_count > 0 else 0.0
    average_subscription_spend = (total_subscription_spend / user_count) if user_count > 0 else 0.0
    recommendation_rate = (users_with_recommendations / user_count * 100) if user_count > 0 else 0.0
    
    return CohortMetrics(
        cohort_id=cohort.cohort_id,
        cohort_name=cohort.cohort_name,
        user_count=user_count,
        persona_distribution=persona_distribution,
        persona_percentages=persona_percentages,
        average_utilization=average_utilization,
        average_savings_balance=average_savings_balance,
        average_monthly_income=average_monthly_income,
        average_subscription_spend=average_subscription_spend,
        recommendation_rate=recommendation_rate
    )


def analyze_fairness_across_cohorts(
    cohort_metrics: List[CohortMetrics],
    reference_cohort: Optional[CohortMetrics] = None
) -> Dict[str, float]:
    """
    Analyze fairness (outcome parity) across cohorts.
    
    Args:
        cohort_metrics: List of CohortMetrics objects
        reference_cohort: Reference cohort (defaults to first cohort)
        
    Returns:
        Dictionary mapping metric to fairness ratio
    """
    if not cohort_metrics:
        return {}
    
    if reference_cohort is None:
        reference_cohort = cohort_metrics[0]
    
    fairness_analysis = {}
    
    # Compare recommendation rates
    reference_rate = reference_cohort.recommendation_rate
    
    for cohort in cohort_metrics:
        if cohort.cohort_id == reference_cohort.cohort_id:
            continue
        
        ratio = (cohort.recommendation_rate / reference_rate) if reference_rate > 0 else 0.0
        fairness_analysis[f"{cohort.cohort_id}_recommendation_rate"] = ratio
    
    # Compare average metrics
    for cohort in cohort_metrics:
        if cohort.cohort_id == reference_cohort.cohort_id:
            continue
        
        # Utilization ratio
        if reference_cohort.average_utilization > 0:
            ratio = cohort.average_utilization / reference_cohort.average_utilization
            fairness_analysis[f"{cohort.cohort_id}_utilization"] = ratio
        
        # Savings ratio
        if reference_cohort.average_savings_balance > 0:
            ratio = cohort.average_savings_balance / reference_cohort.average_savings_balance
            fairness_analysis[f"{cohort.cohort_id}_savings"] = ratio
    
    return fairness_analysis


def run_cohort_analysis(
    cohorts: List[CohortDefinition],
    db_path: str,
    analysis_id: Optional[str] = None
) -> CohortAnalysis:
    """
    Run cohort analysis.
    
    Args:
        cohorts: List of CohortDefinition objects
        db_path: Path to SQLite database
        analysis_id: Optional analysis ID (auto-generated if not provided)
        
    Returns:
        CohortAnalysis object
    """
    if analysis_id is None:
        timestamp = datetime.now()
        analysis_id = f"COHORT-{timestamp.strftime('%Y%m%d%H%M%S')}"
    
    # Calculate metrics for each cohort
    cohort_metrics = []
    for cohort in cohorts:
        metrics = calculate_cohort_metrics(cohort, db_path)
        cohort_metrics.append(metrics)
    
    # Analyze fairness
    fairness_analysis = analyze_fairness_across_cohorts(cohort_metrics)
    
    # Create summary
    summary = {
        "total_cohorts": len(cohorts),
        "total_users": sum(len(c.user_ids) for c in cohorts),
        "average_cohort_size": sum(len(c.user_ids) for c in cohorts) / len(cohorts) if cohorts else 0,
        "cohorts_with_disparities": sum(1 for ratio in fairness_analysis.values() if ratio < 0.8)
    }
    
    return CohortAnalysis(
        analysis_id=analysis_id,
        timestamp=datetime.now(),
        cohorts=cohorts,
        cohort_metrics=cohort_metrics,
        fairness_analysis=fairness_analysis,
        summary=summary
    )


def export_cohort_report(analysis: CohortAnalysis, output_path: str) -> None:
    """
    Export cohort analysis report to JSON file.
    
    Args:
        analysis: CohortAnalysis object
        output_path: Path to output JSON file
    """
    data = {
        "analysis_id": analysis.analysis_id,
        "timestamp": analysis.timestamp.isoformat(),
        "cohorts": [
            {
                "cohort_id": c.cohort_id,
                "cohort_name": c.cohort_name,
                "dimension": c.dimension.value,
                "user_count": len(c.user_ids),
                "criteria": c.criteria,
                "metadata": c.metadata
            }
            for c in analysis.cohorts
        ],
        "cohort_metrics": [
            {
                "cohort_id": m.cohort_id,
                "cohort_name": m.cohort_name,
                "user_count": m.user_count,
                "persona_distribution": m.persona_distribution,
                "persona_percentages": m.persona_percentages,
                "average_utilization": m.average_utilization,
                "average_savings_balance": m.average_savings_balance,
                "average_monthly_income": m.average_monthly_income,
                "average_subscription_spend": m.average_subscription_spend,
                "recommendation_rate": m.recommendation_rate
            }
            for m in analysis.cohort_metrics
        ],
        "fairness_analysis": analysis.fairness_analysis,
        "summary": analysis.summary
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def generate_cohort_report(analysis: CohortAnalysis, output_path: str) -> None:
    """
    Generate human-readable cohort analysis report.
    
    Args:
        analysis: CohortAnalysis object
        output_path: Path to output report file
    """
    report_text = f"""
SpendSenseAI Cohort Analysis Report
Generated: {analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Analysis ID: {analysis.analysis_id}

================================================================================
SUMMARY
================================================================================
Total Cohorts: {analysis.summary.get('total_cohorts', 0)}
Total Users: {analysis.summary.get('total_users', 0)}
Average Cohort Size: {analysis.summary.get('average_cohort_size', 0):.1f}
Cohorts with Disparities: {analysis.summary.get('cohorts_with_disparities', 0)}

================================================================================
COHORT METRICS
================================================================================
"""
    
    for metrics in analysis.cohort_metrics:
        report_text += f"\n{metrics.cohort_name}:\n"
        report_text += f"  User Count: {metrics.user_count}\n"
        report_text += f"  Average Utilization: {metrics.average_utilization:.1f}%\n"
        report_text += f"  Average Savings Balance: ${metrics.average_savings_balance:,.2f}\n"
        report_text += f"  Average Monthly Income: ${metrics.average_monthly_income:,.2f}\n"
        report_text += f"  Average Subscription Spend: ${metrics.average_subscription_spend:,.2f}/month\n"
        report_text += f"  Recommendation Rate: {metrics.recommendation_rate:.1f}%\n"
        report_text += f"  Persona Distribution:\n"
        for persona, pct in metrics.persona_percentages.items():
            report_text += f"    - {persona.replace('_', ' ').title()}: {pct:.1f}%\n"
    
    report_text += "\n" + "="*60 + "\n"
    report_text += "FAIRNESS ANALYSIS\n"
    report_text += "="*60 + "\n"
    report_text += "(80% rule: values below 0.8 may indicate disparities)\n\n"
    
    for metric, ratio in analysis.fairness_analysis.items():
        status = "⚠️ DISPARITY" if ratio < 0.8 else "✓ PARITY"
        report_text += f"{status} {metric}: {ratio:.3f}\n"
    
    with open(output_path, 'w') as f:
        f.write(report_text)

