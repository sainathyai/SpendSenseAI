"""
Persona Definition & Assignment Logic for SpendSenseAI.

Implements the 4 required personas with matching criteria:
1. High Utilization
2. Variable Income Budgeter
3. Subscription-Heavy
4. Savings Builder

Plus 30-day and 180-day persona assignment.
"""

from typing import List, Optional, Dict
from datetime import date, timedelta
from dataclasses import dataclass
from enum import Enum

from features.subscription_detection import detect_subscriptions_for_customer
from features.credit_utilization import analyze_credit_utilization_for_customer
from features.savings_pattern import analyze_savings_patterns_for_customer
from features.income_stability import analyze_income_stability_for_customer


class PersonaType(str, Enum):
    """Persona types."""
    HIGH_UTILIZATION = "high_utilization"
    VARIABLE_INCOME_BUDGETER = "variable_income_budgeter"
    SUBSCRIPTION_HEAVY = "subscription_heavy"
    SAVINGS_BUILDER = "savings_builder"
    FINANCIAL_FRAGILITY = "financial_fragility"  # Will be added in PR #10
    NO_PERSONA = "no_persona"


@dataclass
class PersonaMatch:
    """Represents a persona match for a customer."""
    persona_type: PersonaType
    confidence_score: float  # 0.0 to 1.0
    criteria_met: List[str]  # List of criteria that were met
    window_days: int  # 30 or 180
    focus_areas: List[str]  # Focus areas for this persona
    supporting_data: Dict  # Supporting data for rationale


@dataclass
class PersonaAssignment:
    """Persona assignment for a customer."""
    customer_id: str
    primary_persona: Optional[PersonaMatch]
    secondary_persona: Optional[PersonaMatch]
    window_30d: Optional[PersonaMatch]
    window_180d: Optional[PersonaMatch]
    assigned_at: date


# ============================================================================
# Persona 1: High Utilization
# ============================================================================

def check_high_utilization_persona(
    customer_id: str,
    db_path: str,
    window_days: int
) -> Optional[PersonaMatch]:
    """
    Check if customer matches High Utilization persona.
    
    Criteria:
    - utilization ≥50% OR
    - interest charges > 0 OR
    - minimum-payment-only OR
    - overdue
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database
        window_days: Analysis window (30 or 180)
        
    Returns:
        PersonaMatch if criteria met, None otherwise
    """
    # Get credit utilization metrics
    card_metrics, agg_metrics = analyze_credit_utilization_for_customer(
        customer_id, db_path, window_days
    )
    
    if not card_metrics:
        return None  # No credit cards
    
    criteria_met = []
    confidence = 0.0
    
    # Check utilization ≥50%
    high_utilization_cards = [
        m for m in card_metrics
        if m.utilization_percentage >= 50.0
    ]
    
    if high_utilization_cards:
        criteria_met.append(f"High utilization ({len(high_utilization_cards)} cards at ≥50%)")
        confidence = max(confidence, 0.8)
        
        # Calculate average utilization
        avg_utilization = sum(m.utilization_percentage for m in high_utilization_cards) / len(high_utilization_cards)
        if avg_utilization >= 80:
            confidence = 1.0  # Critical utilization
        elif avg_utilization >= 65:
            confidence = 0.9
    
    # Check interest charges
    cards_with_interest = [m for m in card_metrics if m.has_interest_charges]
    if cards_with_interest:
        criteria_met.append(f"Interest charges detected ({len(cards_with_interest)} cards)")
        confidence = max(confidence, 0.85)
    
    # Check minimum payment only
    min_payment_only_cards = [m for m in card_metrics if m.is_minimum_payment_only]
    if min_payment_only_cards:
        criteria_met.append(f"Minimum payment only ({len(min_payment_only_cards)} cards)")
        confidence = max(confidence, 0.75)
    
    # Check overdue
    overdue_cards = [m for m in card_metrics if m.is_overdue]
    if overdue_cards:
        criteria_met.append(f"Overdue accounts ({len(overdue_cards)} cards)")
        confidence = max(confidence, 0.9)
    
    if not criteria_met:
        return None
    
    # Supporting data
    supporting_data = {
        'total_balance': agg_metrics.total_balance,
        'total_limit': agg_metrics.total_limit,
        'aggregate_utilization': agg_metrics.aggregate_utilization,
        'high_utilization_card_count': agg_metrics.high_utilization_card_count,
        'total_monthly_interest': agg_metrics.total_monthly_interest,
        'overdue_card_count': agg_metrics.overdue_card_count
    }
    
    return PersonaMatch(
        persona_type=PersonaType.HIGH_UTILIZATION,
        confidence_score=confidence,
        criteria_met=criteria_met,
        window_days=window_days,
        focus_areas=[
            "Payment planning",
            "Debt reduction strategies",
            "Balance transfer options",
            "Autopay setup"
        ],
        supporting_data=supporting_data
    )


# ============================================================================
# Persona 2: Variable Income Budgeter
# ============================================================================

def check_variable_income_budgeter_persona(
    customer_id: str,
    db_path: str,
    window_days: int
) -> Optional[PersonaMatch]:
    """
    Check if customer matches Variable Income Budgeter persona.
    
    Criteria:
    - Median pay gap > 45 days AND
    - Cash-flow buffer < 1 month
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database
        window_days: Analysis window (30 or 180)
        
    Returns:
        PersonaMatch if criteria met, None otherwise
    """
    # Get income stability metrics
    income_metrics = analyze_income_stability_for_customer(
        customer_id, db_path, window_days
    )
    
    # Calculate monthly burn rate (approximate from checking account)
    # For simplicity, we'll use a default or estimate
    monthly_burn_rate = income_metrics.average_monthly_income * 0.8 if income_metrics.average_monthly_income > 0 else 0.0
    
    # Recalculate with burn rate
    income_metrics = analyze_income_stability_for_customer(
        customer_id, db_path, window_days, monthly_burn_rate
    )
    
    criteria_met = []
    confidence = 0.0
    
    # Check median pay gap > 45 days
    if income_metrics.median_pay_gap_days > 45:
        criteria_met.append(f"Median pay gap > 45 days ({income_metrics.median_pay_gap_days:.1f} days)")
        confidence = 0.8
        if income_metrics.median_pay_gap_days > 60:
            confidence = 0.9
    
    # Check cash-flow buffer < 1 month
    if income_metrics.cash_flow_buffer_months < 1.0:
        criteria_met.append(f"Cash-flow buffer < 1 month ({income_metrics.cash_flow_buffer_months:.1f} months)")
        confidence = max(confidence, 0.75)
        if income_metrics.cash_flow_buffer_months < 0.5:
            confidence = max(confidence, 0.9)
    
    # Both criteria must be met
    if len(criteria_met) < 2:
        return None
    
    # Supporting data
    supporting_data = {
        'median_pay_gap_days': income_metrics.median_pay_gap_days,
        'cash_flow_buffer_months': income_metrics.cash_flow_buffer_months,
        'income_variability': income_metrics.income_variability,
        'payment_frequency': income_metrics.payment_frequency,
        'is_gig_worker': income_metrics.is_gig_worker
    }
    
    return PersonaMatch(
        persona_type=PersonaType.VARIABLE_INCOME_BUDGETER,
        confidence_score=confidence,
        criteria_met=criteria_met,
        window_days=window_days,
        focus_areas=[
            "Percent-based budgets",
            "Emergency fund building",
            "Income smoothing strategies",
            "Variable expense management"
        ],
        supporting_data=supporting_data
    )


# ============================================================================
# Persona 3: Subscription-Heavy
# ============================================================================

def check_subscription_heavy_persona(
    customer_id: str,
    db_path: str,
    window_days: int
) -> Optional[PersonaMatch]:
    """
    Check if customer matches Subscription-Heavy persona.
    
    Criteria:
    - Recurring merchants ≥3 AND
    - (monthly spend ≥$50 OR subscription share ≥10%)
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database
        window_days: Analysis window (30 or 180)
        
    Returns:
        PersonaMatch if criteria met, None otherwise
    """
    # Get subscription metrics
    subscriptions, sub_metrics = detect_subscriptions_for_customer(
        customer_id, db_path, window_days
    )
    
    criteria_met = []
    confidence = 0.0
    
    # Check recurring merchants ≥3
    if sub_metrics['subscription_count'] >= 3:
        criteria_met.append(f"Recurring merchants ≥3 ({sub_metrics['subscription_count']} subscriptions)")
        confidence = 0.7
        
        # Check monthly spend ≥$50
        if sub_metrics['total_monthly_recurring_spend'] >= 50.0:
            criteria_met.append(f"Monthly recurring spend ≥$50 (${sub_metrics['total_monthly_recurring_spend']:.2f})")
            confidence = max(confidence, 0.85)
        
        # Check subscription share ≥10%
        if sub_metrics['subscription_share_of_total'] >= 10.0:
            criteria_met.append(f"Subscription share ≥10% ({sub_metrics['subscription_share_of_total']:.1f}%)")
            confidence = max(confidence, 0.8)
        
        # Both spend criteria must be met (OR condition)
        if sub_metrics['total_monthly_recurring_spend'] >= 50.0 or sub_metrics['subscription_share_of_total'] >= 10.0:
            # Confidence increases with more subscriptions
            if sub_metrics['subscription_count'] >= 5:
                confidence = min(confidence + 0.1, 1.0)
        else:
            return None  # Need at least one of the spend criteria
    else:
        return None  # Need at least 3 subscriptions
    
    # Supporting data
    supporting_data = {
        'subscription_count': sub_metrics['subscription_count'],
        'active_subscription_count': sub_metrics['active_subscription_count'],
        'total_monthly_recurring_spend': sub_metrics['total_monthly_recurring_spend'],
        'subscription_share_of_total': sub_metrics['subscription_share_of_total'],
        'top_subscriptions': [
            {
                'merchant': s.merchant_name,
                'monthly_spend': s.monthly_recurring_spend,
                'cadence': s.cadence
            }
            for s in subscriptions[:5]  # Top 5
        ]
    }
    
    return PersonaMatch(
        persona_type=PersonaType.SUBSCRIPTION_HEAVY,
        confidence_score=confidence,
        criteria_met=criteria_met,
        window_days=window_days,
        focus_areas=[
            "Subscription audit",
            "Cancellation tips",
            "Bill alerts",
            "Spending optimization"
        ],
        supporting_data=supporting_data
    )


# ============================================================================
# Persona 4: Savings Builder
# ============================================================================

def check_savings_builder_persona(
    customer_id: str,
    db_path: str,
    window_days: int
) -> Optional[PersonaMatch]:
    """
    Check if customer matches Savings Builder persona.
    
    Criteria:
    - (Growth rate ≥2% OR net inflow ≥$200/month) AND
    - utilizations < 30%
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database
        window_days: Analysis window (30 or 180)
        
    Returns:
        PersonaMatch if criteria met, None otherwise
    """
    # Get savings metrics
    savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(
        customer_id, db_path, window_days
    )
    
    # Get credit utilization (must be < 30%)
    card_metrics, agg_metrics = analyze_credit_utilization_for_customer(
        customer_id, db_path, window_days
    )
    
    criteria_met = []
    confidence = 0.0
    
    # Check utilizations < 30% (must have credit cards)
    if card_metrics:
        high_utilization = any(m.utilization_percentage >= 30.0 for m in card_metrics)
        if high_utilization:
            return None  # Disqualifies if utilization ≥30%
        criteria_met.append(f"All credit cards < 30% utilization")
    # If no credit cards, still eligible
    
    # Check savings growth rate ≥2% OR net inflow ≥$200/month
    if savings_metrics.savings_account_count > 0:
        if savings_metrics.overall_growth_rate >= 2.0:
            criteria_met.append(f"Savings growth rate ≥2% ({savings_metrics.overall_growth_rate:.1f}%)")
            confidence = 0.8
            if savings_metrics.overall_growth_rate >= 5.0:
                confidence = 0.9
        
        if savings_metrics.average_monthly_inflow >= 200.0:
            criteria_met.append(f"Net inflow ≥$200/month (${savings_metrics.average_monthly_inflow:.2f}/month)")
            confidence = max(confidence, 0.85)
        
        # Need at least one savings criterion
        if savings_metrics.overall_growth_rate < 2.0 and savings_metrics.average_monthly_inflow < 200.0:
            return None  # No savings growth or inflow
        
        # If both criteria met, increase confidence
        if savings_metrics.overall_growth_rate >= 2.0 and savings_metrics.average_monthly_inflow >= 200.0:
            confidence = min(confidence + 0.1, 1.0)
    else:
        return None  # Need savings accounts
    
    # Supporting data
    supporting_data = {
        'savings_account_count': savings_metrics.savings_account_count,
        'total_savings_balance': savings_metrics.total_savings_balance,
        'overall_growth_rate': savings_metrics.overall_growth_rate,
        'average_monthly_inflow': savings_metrics.average_monthly_inflow,
        'total_net_inflow': savings_metrics.total_net_inflow,
        'aggregate_credit_utilization': agg_metrics.aggregate_utilization if card_metrics else 0.0
    }
    
    return PersonaMatch(
        persona_type=PersonaType.SAVINGS_BUILDER,
        confidence_score=confidence,
        criteria_met=criteria_met,
        window_days=window_days,
        focus_areas=[
            "Goal setting",
            "APY optimization",
            "Savings strategies",
            "Investment basics"
        ],
        supporting_data=supporting_data
    )


# ============================================================================
# Persona Assignment Logic
# ============================================================================

def assign_persona_for_window(
    customer_id: str,
    db_path: str,
    window_days: int
) -> Optional[PersonaMatch]:
    """
    Assign persona for a specific time window.
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database
        window_days: Analysis window (30 or 180)
        
    Returns:
        PersonaMatch for the window, or None if no match
    """
    from personas.persona_prioritization import prioritize_personas
    
    # Check all personas
    personas = []
    
    # Persona 1: High Utilization
    high_util = check_high_utilization_persona(customer_id, db_path, window_days)
    if high_util:
        personas.append(high_util)
    
    # Persona 2: Financial Fragility (Custom 5th Persona)
    from personas.financial_fragility import check_financial_fragility_persona
    financial_fragility = check_financial_fragility_persona(customer_id, db_path, window_days)
    if financial_fragility:
        personas.append(financial_fragility)
    
    # Persona 3: Variable Income Budgeter
    variable_income = check_variable_income_budgeter_persona(customer_id, db_path, window_days)
    if variable_income:
        personas.append(variable_income)
    
    # Persona 4: Subscription-Heavy
    subscription_heavy = check_subscription_heavy_persona(customer_id, db_path, window_days)
    if subscription_heavy:
        personas.append(subscription_heavy)
    
    # Persona 5: Savings Builder
    savings_builder = check_savings_builder_persona(customer_id, db_path, window_days)
    if savings_builder:
        personas.append(savings_builder)
    
    if not personas:
        return None
    
    # Prioritize and return highest priority persona
    prioritized = prioritize_personas(personas)
    return prioritized[0] if prioritized else None


def assign_personas_for_customer(
    customer_id: str,
    db_path: str
) -> PersonaAssignment:
    """
    Assign personas for a customer (30-day and 180-day windows).
    
    Uses prioritization logic from persona_prioritization module.
    
    Args:
        customer_id: Customer ID
        db_path: Path to SQLite database
        
    Returns:
        PersonaAssignment object
    """
    from personas.persona_prioritization import assign_personas_with_prioritization
    
    # Use prioritization logic
    return assign_personas_with_prioritization(customer_id, db_path)

