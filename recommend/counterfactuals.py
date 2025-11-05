"""
Counterfactual Explanations for SpendSenseAI.

Shows "what if" scenarios to increase trust:
- "If you reduced utilization to 30%, your interest would decrease by $X"
- "If you saved $200/month, you'd have 3-month emergency fund in Y months"
- "If you canceled these 3 subscriptions, you'd save $X/year"
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import ceil

from personas.persona_definition import PersonaType
from features.credit_utilization import analyze_credit_utilization_for_customer
from features.savings_pattern import analyze_savings_patterns_for_customer
from features.subscription_detection import detect_subscriptions_for_customer
from features.income_stability import analyze_income_stability_for_customer
from ingest.queries import get_accounts_by_customer, get_transactions_by_customer


@dataclass
class CounterfactualScenario:
    """A counterfactual scenario."""
    scenario_id: str
    title: str
    description: str
    current_state: Dict[str, Any]
    hypothetical_state: Dict[str, Any]
    projected_outcome: Dict[str, Any]
    time_to_achieve: Optional[str] = None  # e.g., "6 months", "12 months"
    confidence: float = 0.0  # Confidence in projection


@dataclass
class CounterfactualSet:
    """Set of counterfactual scenarios for a user."""
    user_id: str
    scenarios: List[CounterfactualScenario]
    generated_at: datetime


def calculate_interest_savings(
    current_utilization: float,
    target_utilization: float,
    current_balance: float,
    current_limit: float,
    apr: float = 0.20  # Default 20% APR
) -> Dict[str, Any]:
    """
    Calculate interest savings from reducing utilization.
    
    Args:
        current_utilization: Current utilization percentage
        target_utilization: Target utilization percentage
        current_balance: Current balance
        current_limit: Credit limit
        apr: Annual percentage rate
        
    Returns:
        Dictionary with savings calculations
    """
    current_monthly_interest = (current_balance * apr / 12) / 100
    target_balance = (target_utilization / 100) * current_limit
    target_monthly_interest = (target_balance * apr / 12) / 100
    
    monthly_savings = current_monthly_interest - target_monthly_interest
    annual_savings = monthly_savings * 12
    
    # Calculate time to pay down (assuming fixed payment)
    balance_reduction_needed = current_balance - target_balance
    # Assume 2% minimum payment or $25 minimum
    min_payment = max(current_balance * 0.02, 25)
    # Payment beyond interest
    principal_payment = min_payment - current_monthly_interest
    
    if principal_payment > 0:
        months_to_target = ceil(balance_reduction_needed / principal_payment)
    else:
        months_to_target = None
    
    return {
        "current_monthly_interest": current_monthly_interest,
        "target_monthly_interest": target_monthly_interest,
        "monthly_savings": monthly_savings,
        "annual_savings": annual_savings,
        "months_to_target": months_to_target,
        "balance_reduction_needed": balance_reduction_needed
    }


def calculate_emergency_fund_timeline(
    current_savings: float,
    monthly_savings_amount: float,
    target_months: float = 3.0,
    monthly_expenses: Optional[float] = None
) -> Dict[str, Any]:
    """
    Calculate timeline to build emergency fund.
    
    Args:
        current_savings: Current savings balance
        monthly_savings_amount: Amount saved per month
        target_months: Target months of expenses (default: 3)
        monthly_expenses: Average monthly expenses (if None, estimated from savings)
        
    Returns:
        Dictionary with timeline calculations
    """
    if monthly_expenses is None:
        # Estimate monthly expenses as 1/12 of savings (rough estimate)
        monthly_expenses = current_savings / 12 if current_savings > 0 else 1000
    
    target_emergency_fund = monthly_expenses * target_months
    remaining_needed = target_emergency_fund - current_savings
    
    if monthly_savings_amount > 0:
        months_to_target = ceil(remaining_needed / monthly_savings_amount)
    else:
        months_to_target = None
    
    return {
        "current_savings": current_savings,
        "target_emergency_fund": target_emergency_fund,
        "remaining_needed": remaining_needed,
        "monthly_savings_amount": monthly_savings_amount,
        "months_to_target": months_to_target,
        "target_months": target_months
    }


def calculate_subscription_savings(
    subscriptions: List[Any],
    subscriptions_to_cancel: List[str]
) -> Dict[str, Any]:
    """
    Calculate savings from canceling subscriptions.
    
    Args:
        subscriptions: List of subscription patterns
        subscriptions_to_cancel: List of subscription merchant names to cancel
        
    Returns:
        Dictionary with savings calculations
    """
    total_monthly_savings = 0.0
    canceled_subscriptions = []
    
    for subscription in subscriptions:
        if subscription.merchant_name in subscriptions_to_cancel:
            monthly_spend = subscription.monthly_recurring_spend
            total_monthly_savings += monthly_spend
            canceled_subscriptions.append({
                "merchant": subscription.merchant_name,
                "monthly_savings": monthly_spend
            })
    
    annual_savings = total_monthly_savings * 12
    
    return {
        "canceled_count": len(canceled_subscriptions),
        "monthly_savings": total_monthly_savings,
        "annual_savings": annual_savings,
        "canceled_subscriptions": canceled_subscriptions
    }


def generate_counterfactuals_for_user(
    user_id: str,
    db_path: str
) -> CounterfactualSet:
    """
    Generate counterfactual scenarios for a user.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        
    Returns:
        CounterfactualSet object
    """
    scenarios = []
    
    # Scenario 1: Credit utilization reduction
    try:
        card_metrics, agg_metrics = analyze_credit_utilization_for_customer(user_id, db_path, 30)
        
        if card_metrics and agg_metrics.aggregate_utilization > 30:
            current_utilization = agg_metrics.aggregate_utilization
            current_balance = sum(card.balance for card in card_metrics)
            current_limit = sum(card.limit for card in card_metrics)
            
            # Calculate savings if utilization reduced to 30%
            savings = calculate_interest_savings(
                current_utilization, 30.0, current_balance, current_limit
            )
            
            if savings["monthly_savings"] > 0:
                time_to_achieve = f"{savings['months_to_target']} months" if savings['months_to_target'] else "Unknown"
                
                scenario = CounterfactualScenario(
                    scenario_id=f"CF-{user_id}-UTIL-001",
                    title="Reduce Credit Utilization to 30%",
                    description=f"If you reduced your credit utilization from {current_utilization:.1f}% to 30%, you could save on interest charges.",
                    current_state={
                        "utilization": current_utilization,
                        "monthly_interest": savings["current_monthly_interest"],
                        "balance": current_balance
                    },
                    hypothetical_state={
                        "utilization": 30.0,
                        "monthly_interest": savings["target_monthly_interest"],
                        "balance": savings["balance_reduction_needed"]
                    },
                    projected_outcome={
                        "monthly_savings": savings["monthly_savings"],
                        "annual_savings": savings["annual_savings"],
                        "interest_reduction": savings["current_monthly_interest"] - savings["target_monthly_interest"]
                    },
                    time_to_achieve=time_to_achieve,
                    confidence=0.8
                )
                scenarios.append(scenario)
    except Exception:
        pass
    
    # Scenario 2: Emergency fund building
    try:
        savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(user_id, db_path, 180)
        
        if savings_accounts:
            current_savings = savings_metrics.total_savings_balance
            monthly_inflow = savings_metrics.average_monthly_inflow
            
            # Calculate timeline to 3-month emergency fund
            timeline = calculate_emergency_fund_timeline(
                current_savings, monthly_inflow, target_months=3.0
            )
            
            if timeline["months_to_target"]:
                scenario = CounterfactualScenario(
                    scenario_id=f"CF-{user_id}-EMERG-001",
                    title="Build 3-Month Emergency Fund",
                    description=f"If you continue saving ${monthly_inflow:.2f} per month, you could build a 3-month emergency fund.",
                    current_state={
                        "current_savings": current_savings,
                        "monthly_savings": monthly_inflow
                    },
                    hypothetical_state={
                        "target_emergency_fund": timeline["target_emergency_fund"],
                        "monthly_savings": monthly_inflow
                    },
                    projected_outcome={
                        "months_to_target": timeline["months_to_target"],
                        "target_amount": timeline["target_emergency_fund"]
                    },
                    time_to_achieve=f"{timeline['months_to_target']} months",
                    confidence=0.7
                )
                scenarios.append(scenario)
    except Exception:
        pass
    
    # Scenario 3: Subscription cancellation
    try:
        subscriptions, sub_metrics = detect_subscriptions_for_customer(user_id, db_path, window_days=90)
        
        if subscriptions and len(subscriptions) >= 3:
            # Suggest canceling top 3 subscriptions
            top_subscriptions = sorted(subscriptions, key=lambda s: s.monthly_recurring_spend, reverse=True)[:3]
            subscriptions_to_cancel = [s.merchant_name for s in top_subscriptions]
            
            savings = calculate_subscription_savings(subscriptions, subscriptions_to_cancel)
            
            if savings["annual_savings"] > 0:
                scenario = CounterfactualScenario(
                    scenario_id=f"CF-{user_id}-SUB-001",
                    title=f"Cancel Top {savings['canceled_count']} Subscriptions",
                    description=f"If you canceled your top {savings['canceled_count']} subscriptions, you could save annually.",
                    current_state={
                        "subscription_count": len(subscriptions),
                        "monthly_spend": sub_metrics.get("total_monthly_recurring_spend", 0)
                    },
                    hypothetical_state={
                        "canceled_count": savings["canceled_count"],
                        "monthly_savings": savings["monthly_savings"]
                    },
                    projected_outcome={
                        "monthly_savings": savings["monthly_savings"],
                        "annual_savings": savings["annual_savings"],
                        "canceled_subscriptions": savings["canceled_subscriptions"]
                    },
                    time_to_achieve="Immediate",
                    confidence=0.9
                )
                scenarios.append(scenario)
    except Exception:
        pass
    
    # Scenario 4: Increase savings rate
    try:
        savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(user_id, db_path, 180)
        
        if savings_accounts:
            current_monthly_inflow = savings_metrics.average_monthly_inflow
            target_increase = 200.0  # $200 more per month
            
            # Calculate impact of increasing savings by $200/month
            new_monthly_inflow = current_monthly_inflow + target_increase
            current_savings = savings_metrics.total_savings_balance
            
            # Project 6 months ahead
            projected_6mo = current_savings + (new_monthly_inflow * 6)
            projected_12mo = current_savings + (new_monthly_inflow * 12)
            
            scenario = CounterfactualScenario(
                scenario_id=f"CF-{user_id}-SAVE-001",
                title="Increase Savings by $200/Month",
                description=f"If you increased your monthly savings by $200, you could significantly grow your savings.",
                current_state={
                    "current_monthly_savings": current_monthly_inflow,
                    "current_balance": current_savings
                },
                hypothetical_state={
                    "new_monthly_savings": new_monthly_inflow,
                    "increase_amount": target_increase
                },
                projected_outcome={
                    "projected_6mo_balance": projected_6mo,
                    "projected_12mo_balance": projected_12mo,
                    "additional_6mo_savings": target_increase * 6,
                    "additional_12mo_savings": target_increase * 12
                },
                time_to_achieve="6-12 months",
                confidence=0.8
            )
            scenarios.append(scenario)
    except Exception:
        pass
    
    return CounterfactualSet(
        user_id=user_id,
        scenarios=scenarios,
        generated_at=datetime.now()
    )


def format_counterfactual_for_display(scenario: CounterfactualScenario) -> str:
    """
    Format counterfactual scenario for display.
    
    Args:
        scenario: CounterfactualScenario object
        
    Returns:
        Formatted string for display
    """
    text = f"**{scenario.title}**\n\n"
    text += f"{scenario.description}\n\n"
    
    text += "**Current State:**\n"
    for key, value in scenario.current_state.items():
        if isinstance(value, float):
            if key == "utilization" or "percentage" in key.lower():
                text += f"- {key.replace('_', ' ').title()}: {value:.1f}%\n"
            elif "interest" in key.lower() or "savings" in key.lower() or "balance" in key.lower():
                text += f"- {key.replace('_', ' ').title()}: ${value:,.2f}\n"
            else:
                text += f"- {key.replace('_', ' ').title()}: {value:.2f}\n"
        else:
            text += f"- {key.replace('_', ' ').title()}: {value}\n"
    
    text += "\n**Projected Outcome:**\n"
    for key, value in scenario.projected_outcome.items():
        if isinstance(value, float):
            if "interest" in key.lower() or "savings" in key.lower() or "balance" in key.lower():
                text += f"- {key.replace('_', ' ').title()}: ${value:,.2f}\n"
            else:
                text += f"- {key.replace('_', ' ').title()}: {value:.2f}\n"
        elif isinstance(value, list):
            text += f"- {key.replace('_', ' ').title()}:\n"
            for item in value:
                if isinstance(item, dict):
                    for k, v in item.items():
                        if isinstance(v, float):
                            text += f"  - {k.replace('_', ' ').title()}: ${v:,.2f}\n"
                        else:
                            text += f"  - {k.replace('_', ' ').title()}: {v}\n"
                else:
                    text += f"  - {item}\n"
        else:
            text += f"- {key.replace('_', ' ').title()}: {value}\n"
    
    if scenario.time_to_achieve:
        text += f"\n**Time to Achieve:** {scenario.time_to_achieve}\n"
    
    text += f"\n**Confidence:** {scenario.confidence:.0%}\n"
    
    return text

