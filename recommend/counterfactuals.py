"""
Counterfactual Explanations for SpendSenseAI.

Shows "what if" scenarios to increase trust:
- "If you reduced utilization to 30%, your interest would decrease by $X"
- "If you saved $200/month, you'd have 3-month emergency fund in Y months"
- "If you canceled these 3 subscriptions, you'd save $X/year"
"""

from typing import List, Dict, Optional, Any
from datetime import date, timedelta
from dataclasses import dataclass
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
    impact: Dict[str, Any]
    time_to_achieve: Optional[str] = None
    confidence: float = 0.0


def calculate_interest_savings(
    current_balance: float,
    current_utilization: float,
    credit_limit: float,
    current_apr: float,
    target_utilization: float = 0.30
) -> Dict[str, Any]:
    """
    Calculate interest savings if utilization is reduced.
    
    Args:
        current_balance: Current credit card balance
        current_utilization: Current utilization percentage
        credit_limit: Credit limit
        current_apr: Current APR (annual percentage rate)
        target_utilization: Target utilization (default: 30%)
        
    Returns:
        Dictionary with savings calculations
    """
    target_balance = credit_limit * target_utilization
    balance_reduction = current_balance - target_balance
    
    if balance_reduction <= 0:
        return {
            "savings": 0.0,
            "monthly_interest_savings": 0.0,
            "annual_interest_savings": 0.0,
            "balance_reduction": 0.0
        }
    
    # Calculate monthly interest (APR / 12)
    monthly_apr = current_apr / 12 / 100
    
    # Current monthly interest
    current_monthly_interest = current_balance * monthly_apr
    
    # Target monthly interest
    target_monthly_interest = target_balance * monthly_apr
    
    # Monthly savings
    monthly_interest_savings = current_monthly_interest - target_monthly_interest
    
    # Annual savings
    annual_interest_savings = monthly_interest_savings * 12
    
    return {
        "savings": balance_reduction,
        "monthly_interest_savings": monthly_interest_savings,
        "annual_interest_savings": annual_interest_savings,
        "balance_reduction": balance_reduction,
        "current_monthly_interest": current_monthly_interest,
        "target_monthly_interest": target_monthly_interest
    }


def calculate_emergency_fund_timeline(
    current_savings: float,
    monthly_savings: float,
    target_months: float = 3.0,
    average_monthly_expenses: float = 0.0
) -> Dict[str, Any]:
    """
    Calculate timeline to reach emergency fund goal.
    
    Args:
        current_savings: Current savings balance
        monthly_savings: Amount saved per month
        target_months: Target emergency fund in months of expenses
        average_monthly_expenses: Average monthly expenses
        
    Returns:
        Dictionary with timeline calculations
    """
    if average_monthly_expenses <= 0:
        # Estimate from savings if expenses not provided
        average_monthly_expenses = current_savings / 3.0 if current_savings > 0 else 2000.0
    
    target_emergency_fund = average_monthly_expenses * target_months
    remaining_needed = max(0, target_emergency_fund - current_savings)
    
    if monthly_savings <= 0:
        return {
            "target_emergency_fund": target_emergency_fund,
            "current_savings": current_savings,
            "remaining_needed": remaining_needed,
            "months_to_goal": None,
            "achievable": False
        }
    
    months_to_goal = ceil(remaining_needed / monthly_savings)
    
    return {
        "target_emergency_fund": target_emergency_fund,
        "current_savings": current_savings,
        "remaining_needed": remaining_needed,
        "months_to_goal": months_to_goal,
        "achievable": True,
        "monthly_savings_needed": remaining_needed / months_to_goal if months_to_goal > 0 else 0
    }


def calculate_subscription_savings(
    subscriptions: List[Any],
    subscriptions_to_cancel: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Calculate savings from canceling subscriptions.
    
    Args:
        subscriptions: List of subscription objects
        subscriptions_to_cancel: Optional list of subscription IDs to cancel
        
    Returns:
        Dictionary with savings calculations
    """
    if not subscriptions:
        return {
            "total_subscriptions": 0,
            "monthly_savings": 0.0,
            "annual_savings": 0.0,
            "subscriptions_to_cancel": []
        }
    
    if subscriptions_to_cancel is None:
        # Cancel top 3 most expensive subscriptions
        sorted_subscriptions = sorted(
            subscriptions,
            key=lambda s: getattr(s, 'monthly_recurring_spend', 0),
            reverse=True
        )
        subscriptions_to_cancel = sorted_subscriptions[:3]
    
    monthly_savings = sum(
        getattr(sub, 'monthly_recurring_spend', 0) for sub in subscriptions_to_cancel
    )
    annual_savings = monthly_savings * 12
    
    return {
        "total_subscriptions": len(subscriptions),
        "subscriptions_to_cancel": len(subscriptions_to_cancel),
        "monthly_savings": monthly_savings,
        "annual_savings": annual_savings,
        "subscription_names": [getattr(sub, 'merchant_name', 'Unknown') for sub in subscriptions_to_cancel]
    }


def generate_counterfactual_scenarios(
    user_id: str,
    db_path: str
) -> List[CounterfactualScenario]:
    """
    Generate counterfactual scenarios for a user.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        
    Returns:
        List of CounterfactualScenario objects
    """
    scenarios = []
    
    # Scenario 1: Credit utilization reduction
    try:
        card_metrics, agg_metrics = analyze_credit_utilization_for_customer(user_id, db_path, 30)
        
        if card_metrics and len(card_metrics) > 0:
            card = card_metrics[0]
            current_utilization = card.utilization_percentage / 100
            
            if current_utilization > 0.30:
                # Assume average APR of 22%
                interest_savings = calculate_interest_savings(
                    card.balance,
                    current_utilization,
                    card.limit,
                    current_apr=22.0,
                    target_utilization=0.30
                )
                
                if interest_savings["annual_interest_savings"] > 0:
                    scenarios.append(CounterfactualScenario(
                        scenario_id="CF-UTIL-001",
                        title="Reduce Credit Utilization to 30%",
                        description=f"If you reduce your credit utilization from {current_utilization:.1%} to 30%, you could save on interest.",
                        current_state={
                            "utilization": f"{current_utilization:.1%}",
                            "balance": card.balance,
                            "monthly_interest": interest_savings["current_monthly_interest"]
                        },
                        hypothetical_state={
                            "utilization": "30%",
                            "balance": card.balance - interest_savings["balance_reduction"],
                            "monthly_interest": interest_savings["target_monthly_interest"]
                        },
                        impact={
                            "monthly_interest_savings": interest_savings["monthly_interest_savings"],
                            "annual_interest_savings": interest_savings["annual_interest_savings"],
                            "balance_reduction_needed": interest_savings["balance_reduction"]
                        },
                        confidence=0.85
                    ))
    except Exception:
        pass
    
    # Scenario 2: Emergency fund building
    try:
        savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(user_id, db_path, 180)
        
        if savings_accounts:
            current_savings = savings_metrics.total_savings_balance
            monthly_inflow = savings_metrics.average_monthly_inflow
            
            # Estimate monthly expenses from savings balance
            if current_savings > 0:
                estimated_expenses = current_savings / 3.0
            else:
                estimated_expenses = 2000.0
            
            timeline = calculate_emergency_fund_timeline(
                current_savings=current_savings,
                monthly_savings=max(monthly_inflow, 200.0),  # Minimum $200/month
                target_months=3.0,
                average_monthly_expenses=estimated_expenses
            )
            
            if timeline["achievable"] and timeline["months_to_goal"]:
                scenarios.append(CounterfactualScenario(
                    scenario_id="CF-EMERG-001",
                    title="Build 3-Month Emergency Fund",
                    description=f"If you save ${max(monthly_inflow, 200.0):.0f} per month, you can build a 3-month emergency fund.",
                    current_state={
                        "current_savings": current_savings,
                        "monthly_savings": monthly_inflow,
                        "emergency_fund_coverage": f"{(current_savings / estimated_expenses):.1f} months"
                    },
                    hypothetical_state={
                        "target_emergency_fund": timeline["target_emergency_fund"],
                        "monthly_savings": max(monthly_inflow, 200.0)
                    },
                    impact={
                        "months_to_goal": timeline["months_to_goal"],
                        "target_emergency_fund": timeline["target_emergency_fund"]
                    },
                    time_to_achieve=f"{timeline['months_to_goal']} months",
                    confidence=0.80
                ))
    except Exception:
        pass
    
    # Scenario 3: Subscription cancellation savings
    try:
        subscriptions, sub_metrics = detect_subscriptions_for_customer(user_id, db_path, window_days=90)
        
        if subscriptions and len(subscriptions) >= 3:
            savings = calculate_subscription_savings(subscriptions)
            
            if savings["annual_savings"] > 0:
                scenarios.append(CounterfactualScenario(
                    scenario_id="CF-SUB-001",
                    title="Cancel Top 3 Subscriptions",
                    description=f"If you cancel your top 3 subscriptions, you could save significant money annually.",
                    current_state={
                        "total_subscriptions": savings["total_subscriptions"],
                        "monthly_spend": sub_metrics.get("total_monthly_recurring_spend", 0)
                    },
                    hypothetical_state={
                        "subscriptions_to_cancel": savings["subscriptions_to_cancel"],
                        "monthly_savings": savings["monthly_savings"]
                    },
                    impact={
                        "monthly_savings": savings["monthly_savings"],
                        "annual_savings": savings["annual_savings"],
                        "subscription_names": savings["subscription_names"]
                    },
                    confidence=0.90
                ))
    except Exception:
        pass
    
    return scenarios


def format_counterfactual_for_display(scenario: CounterfactualScenario) -> str:
    """
    Format counterfactual scenario for display.
    
    Args:
        scenario: CounterfactualScenario object
        
    Returns:
        Formatted string for display
    """
    output = f"**{scenario.title}**\n\n"
    output += f"{scenario.description}\n\n"
    
    if scenario.impact:
        output += "**Impact:**\n"
        for key, value in scenario.impact.items():
            if isinstance(value, float):
                if key.endswith("_savings") or key.endswith("_savings_needed"):
                    output += f"- {key.replace('_', ' ').title()}: ${value:,.2f}\n"
                else:
                    output += f"- {key.replace('_', ' ').title()}: {value:.2f}\n"
            elif isinstance(value, list):
                output += f"- {key.replace('_', ' ').title()}: {', '.join(str(v) for v in value)}\n"
            else:
                output += f"- {key.replace('_', ' ').title()}: {value}\n"
    
    if scenario.time_to_achieve:
        output += f"\n**Time to achieve:** {scenario.time_to_achieve}\n"
    
    return output
