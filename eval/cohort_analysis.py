"""
Cohort Analysis & Segmentation for SpendSenseAI.

Group users by characteristics for insights:
- Cohort definition (by age, income level, join date, geography)
- Persona distribution by cohort
- Average metrics by cohort
- Cohort performance over time
- Fairness analysis (outcome parity across demographics)
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date
from dataclasses import dataclass
from collections import defaultdict
from statistics import mean, median

from personas.persona_prioritization import assign_personas_with_prioritization
from personas.persona_definition import PersonaType
from features.subscription_detection import detect_subscriptions_for_customer
from features.credit_utilization import analyze_credit_utilization_for_customer
from features.savings_pattern import analyze_savings_patterns_for_customer
from features.income_stability import analyze_income_stability_for_customer
from ingest.queries import get_accounts_by_customer, get_transactions_by_customer


@dataclass
class CohortDefinition:
    """Cohort definition."""
    cohort_id: str
    name: str
    criteria: Dict[str, Any]  # e.g., {"age_range": (25, 35), "income_level": "medium"}


@dataclass
class CohortMetrics:
    """Metrics for a cohort."""
    cohort_id: str
    user_count: int
    persona_distribution: Dict[str, int]
    persona_percentages: Dict[str, float]
    average_metrics: Dict[str, float]
    median_metrics: Dict[str, float]


def create_income_cohorts(user_ids: List[str], db_path: str) -> Dict[str, List[str]]:
    """
    Create cohorts based on estimated income levels.
    
    Args:
        user_ids: List of user IDs
        db_path: Path to SQLite database
        
    Returns:
        Dictionary mapping cohort names to user ID lists
    """
    cohorts = {
        "low_income": [],      # < $30k
        "medium_income": [],   # $30k - $70k
        "high_income": []      # > $70k
    }
    
    # Estimate income from transactions (deposits/income)
    for user_id in user_ids:
        try:
            transactions = get_transactions_by_customer(user_id, db_path)
            
            # Find positive transactions (likely income)
            income_transactions = [t for t in transactions if t.amount > 0]
            
            if income_transactions:
                # Estimate monthly income
                monthly_income = sum(t.amount for t in income_transactions) / max(len(income_transactions), 1)
                annual_income = monthly_income * 12
                
                if annual_income < 30000:
                    cohorts["low_income"].append(user_id)
                elif annual_income < 70000:
                    cohorts["medium_income"].append(user_id)
                else:
                    cohorts["high_income"].append(user_id)
            else:
                # Default to medium income if no income transactions
                cohorts["medium_income"].append(user_id)
        except Exception:
            # Default to medium income on error
            cohorts["medium_income"].append(user_id)
    
    return cohorts


def analyze_cohort_persona_distribution(
    user_ids: List[str],
    db_path: str
) -> Dict[str, Dict[str, int]]:
    """
    Analyze persona distribution for a cohort.
    
    Args:
        user_ids: List of user IDs in cohort
        db_path: Path to SQLite database
        
    Returns:
        Dictionary mapping persona types to counts
    """
    persona_counts = defaultdict(int)
    
    for user_id in user_ids:
        try:
            persona_assignment = assign_personas_with_prioritization(user_id, db_path)
            
            if persona_assignment.primary_persona:
                persona_type = persona_assignment.primary_persona.persona_type.value
                persona_counts[persona_type] += 1
        except Exception:
            pass
    
    return dict(persona_counts)


def calculate_cohort_average_metrics(
    user_ids: List[str],
    db_path: str
) -> Dict[str, float]:
    """
    Calculate average metrics for a cohort.
    
    Args:
        user_ids: List of user IDs in cohort
        db_path: Path to SQLite database
        
    Returns:
        Dictionary with average metrics
    """
    metrics = {
        "utilization": [],
        "savings_balance": [],
        "subscription_count": [],
        "subscription_spend": [],
        "pay_gap_days": [],
        "cash_flow_buffer": []
    }
    
    for user_id in user_ids:
        try:
            # Credit utilization
            card_metrics, agg_metrics = analyze_credit_utilization_for_customer(user_id, db_path, 30)
            if card_metrics:
                metrics["utilization"].append(agg_metrics.aggregate_utilization)
            
            # Savings
            savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(user_id, db_path, 180)
            if savings_accounts:
                metrics["savings_balance"].append(savings_metrics.total_savings_balance)
            
            # Subscriptions
            subscriptions, sub_metrics = detect_subscriptions_for_customer(user_id, db_path, window_days=90)
            metrics["subscription_count"].append(sub_metrics.get("subscription_count", 0))
            metrics["subscription_spend"].append(sub_metrics.get("total_monthly_recurring_spend", 0))
            
            # Income
            income_metrics = analyze_income_stability_for_customer(user_id, db_path, 180)
            metrics["pay_gap_days"].append(income_metrics.median_pay_gap_days)
            metrics["cash_flow_buffer"].append(income_metrics.cash_flow_buffer_months)
        except Exception:
            pass
    
    # Calculate averages
    average_metrics = {}
    for key, values in metrics.items():
        if values:
            average_metrics[f"average_{key}"] = mean(values)
            average_metrics[f"median_{key}"] = median(values)
        else:
            average_metrics[f"average_{key}"] = 0.0
            average_metrics[f"median_{key}"] = 0.0
    
    return average_metrics


def analyze_cohort(
    cohort_id: str,
    user_ids: List[str],
    db_path: str
) -> CohortMetrics:
    """
    Analyze a cohort.
    
    Args:
        cohort_id: Cohort identifier
        user_ids: List of user IDs in cohort
        db_path: Path to SQLite database
        
    Returns:
        CohortMetrics object
    """
    # Persona distribution
    persona_distribution = analyze_cohort_persona_distribution(user_ids, db_path)
    
    # Calculate percentages
    total_users = len(user_ids)
    persona_percentages = {
        persona: (count / total_users * 100) if total_users > 0 else 0.0
        for persona, count in persona_distribution.items()
    }
    
    # Average metrics
    average_metrics = calculate_cohort_average_metrics(user_ids, db_path)
    
    # Separate average and median
    avg_metrics = {k: v for k, v in average_metrics.items() if k.startswith("average_")}
    med_metrics = {k: v for k, v in average_metrics.items() if k.startswith("median_")}
    
    return CohortMetrics(
        cohort_id=cohort_id,
        user_count=total_users,
        persona_distribution=persona_distribution,
        persona_percentages=persona_percentages,
        average_metrics=avg_metrics,
        median_metrics=med_metrics
    )


def analyze_all_cohorts(
    user_ids: List[str],
    db_path: str
) -> Dict[str, CohortMetrics]:
    """
    Analyze all cohorts.
    
    Args:
        user_ids: List of all user IDs
        db_path: Path to SQLite database
        
    Returns:
        Dictionary mapping cohort IDs to CohortMetrics objects
    """
    cohorts = {}
    
    # Create income-based cohorts
    income_cohorts = create_income_cohorts(user_ids, db_path)
    
    for cohort_name, cohort_user_ids in income_cohorts.items():
        if cohort_user_ids:
            cohorts[cohort_name] = analyze_cohort(cohort_name, cohort_user_ids, db_path)
    
    return cohorts


def generate_cohort_report(
    cohorts: Dict[str, CohortMetrics],
    output_path: str
) -> None:
    """
    Generate cohort analysis report.
    
    Args:
        cohorts: Dictionary of cohort analyses
        output_path: Path to output report file
    """
    report = f"""
Cohort Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

================================================================================
SUMMARY
================================================================================
Total Cohorts: {len(cohorts)}
Total Users Analyzed: {sum(c.user_count for c in cohorts.values())}

================================================================================
COHORT ANALYSIS
================================================================================
"""
    
    for cohort_id, cohort_metrics in cohorts.items():
        cohort_name = cohort_id.replace('_', ' ').title()
        report += f"\n{cohort_name} Cohort\n"
        report += f"  User Count: {cohort_metrics.user_count}\n"
        
        report += "\n  Persona Distribution:\n"
        for persona, count in cohort_metrics.persona_distribution.items():
            percentage = cohort_metrics.persona_percentages.get(persona, 0.0)
            report += f"    - {persona.replace('_', ' ').title()}: {count} users ({percentage:.1f}%)\n"
        
        report += "\n  Average Metrics:\n"
        for metric, value in cohort_metrics.average_metrics.items():
            if isinstance(value, float):
                if "balance" in metric or "spend" in metric:
                    report += f"    - {metric.replace('_', ' ').title()}: ${value:,.2f}\n"
                else:
                    report += f"    - {metric.replace('_', ' ').title()}: {value:.2f}\n"
        
        report += "\n"
    
    report += "=" * 60 + "\n"
    
    with open(output_path, 'w') as f:
        f.write(report)
