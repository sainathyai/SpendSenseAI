"""
Interactive Financial Calculators for SpendSenseAI.

Provide actionable tools within recommendations:
- Credit payoff calculator (time to 30% utilization)
- Emergency fund calculator (months to goal)
- Subscription cost analyzer (annual savings from cancellations)
- Budget planner for variable income
"""

from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from math import ceil, log
from datetime import date, timedelta

from features.credit_utilization import analyze_credit_utilization_for_customer
from features.savings_pattern import analyze_savings_patterns_for_customer
from features.subscription_detection import detect_subscriptions_for_customer
from features.income_stability import analyze_income_stability_for_customer


@dataclass
class CreditPayoffResult:
    """Credit payoff calculator result."""
    current_balance: float
    current_utilization: float
    credit_limit: float
    target_utilization: float
    target_balance: float
    balance_reduction_needed: float
    monthly_payment: float
    months_to_goal: int
    total_interest_paid: float
    total_payments: float


@dataclass
class EmergencyFundResult:
    """Emergency fund calculator result."""
    current_savings: float
    target_emergency_fund: float
    monthly_expenses: float
    months_coverage: float
    remaining_needed: float
    monthly_savings: float
    months_to_goal: int
    achievable: bool


@dataclass
class SubscriptionAnalyzerResult:
    """Subscription analyzer result."""
    total_subscriptions: int
    monthly_recurring_spend: float
    annual_recurring_spend: float
    subscriptions_to_cancel: List[Dict[str, Any]]
    potential_monthly_savings: float
    potential_annual_savings: float


@dataclass
class BudgetPlannerResult:
    """Budget planner result."""
    monthly_income: float
    income_variability: float
    essential_expenses: float
    discretionary_expenses: float
    savings_target: float
    recommended_budget: Dict[str, float]
    percentage_budget: Dict[str, float]


def calculate_credit_payoff(
    current_balance: float,
    credit_limit: float,
    target_utilization: float = 0.30,
    monthly_payment: Optional[float] = None,
    apr: float = 22.0
) -> CreditPayoffResult:
    """
    Calculate credit payoff timeline to reach target utilization.
    
    Args:
        current_balance: Current credit card balance
        credit_limit: Credit limit
        target_utilization: Target utilization (default: 30%)
        monthly_payment: Optional fixed monthly payment (if None, uses minimum payment)
        apr: Annual percentage rate (default: 22%)
        
    Returns:
        CreditPayoffResult object
    """
    current_utilization = current_balance / credit_limit if credit_limit > 0 else 0.0
    target_balance = credit_limit * target_utilization
    balance_reduction_needed = current_balance - target_balance
    
    if balance_reduction_needed <= 0:
        return CreditPayoffResult(
            current_balance=current_balance,
            current_utilization=current_utilization,
            credit_limit=credit_limit,
            target_utilization=target_utilization,
            target_balance=target_balance,
            balance_reduction_needed=0.0,
            monthly_payment=0.0,
            months_to_goal=0,
            total_interest_paid=0.0,
            total_payments=0.0
        )
    
    # Calculate minimum payment (typically 2% of balance or $25, whichever is higher)
    if monthly_payment is None:
        minimum_payment = max(current_balance * 0.02, 25.0)
        monthly_payment = minimum_payment * 1.5  # Use 1.5x minimum for faster payoff
    
    # Calculate monthly interest rate
    monthly_apr = apr / 12 / 100
    
    # Calculate months to payoff using amortization formula
    if monthly_payment > current_balance * monthly_apr:
        # Payment is greater than interest, so we can calculate payoff time
        months_to_goal = ceil(
            -log(1 - (balance_reduction_needed * monthly_apr) / monthly_payment) / log(1 + monthly_apr)
        ) if monthly_apr > 0 else ceil(balance_reduction_needed / monthly_payment)
    else:
        # Payment is too low, will never pay off
        months_to_goal = 999
    
    # Calculate total interest and payments
    total_payments = months_to_goal * monthly_payment
    total_interest_paid = total_payments - balance_reduction_needed
    
    return CreditPayoffResult(
        current_balance=current_balance,
        current_utilization=current_utilization,
        credit_limit=credit_limit,
        target_utilization=target_utilization,
        target_balance=target_balance,
        balance_reduction_needed=balance_reduction_needed,
        monthly_payment=monthly_payment,
        months_to_goal=months_to_goal,
        total_interest_paid=total_interest_paid,
        total_payments=total_payments
    )


def calculate_emergency_fund(
    current_savings: float,
    monthly_expenses: float,
    target_months: float = 3.0,
    monthly_savings: Optional[float] = None
) -> EmergencyFundResult:
    """
    Calculate emergency fund timeline.
    
    Args:
        current_savings: Current savings balance
        monthly_expenses: Average monthly expenses
        target_months: Target emergency fund in months (default: 3)
        monthly_savings: Optional fixed monthly savings amount
        
    Returns:
        EmergencyFundResult object
    """
    target_emergency_fund = monthly_expenses * target_months
    remaining_needed = max(0, target_emergency_fund - current_savings)
    months_coverage = current_savings / monthly_expenses if monthly_expenses > 0 else 0.0
    
    if monthly_savings is None:
        # Estimate 10% of monthly expenses as savings
        monthly_savings = monthly_expenses * 0.10
    
    if monthly_savings <= 0:
        return EmergencyFundResult(
            current_savings=current_savings,
            target_emergency_fund=target_emergency_fund,
            monthly_expenses=monthly_expenses,
            months_coverage=months_coverage,
            remaining_needed=remaining_needed,
            monthly_savings=0.0,
            months_to_goal=999,
            achievable=False
        )
    
    months_to_goal = ceil(remaining_needed / monthly_savings) if monthly_savings > 0 else 999
    achievable = months_to_goal < 999
    
    return EmergencyFundResult(
        current_savings=current_savings,
        target_emergency_fund=target_emergency_fund,
        monthly_expenses=monthly_expenses,
        months_coverage=months_coverage,
        remaining_needed=remaining_needed,
        monthly_savings=monthly_savings,
        months_to_goal=months_to_goal,
        achievable=achievable
    )


def analyze_subscription_costs(
    subscriptions: list,
    subscriptions_to_cancel: Optional[list] = None
) -> SubscriptionAnalyzerResult:
    """
    Analyze subscription costs and potential savings.
    
    Args:
        subscriptions: List of subscription objects
        subscriptions_to_cancel: Optional list of subscriptions to cancel
        
    Returns:
        SubscriptionAnalyzerResult object
    """
    total_subscriptions = len(subscriptions)
    
    # Calculate total recurring spend
    monthly_recurring_spend = sum(
        getattr(sub, 'monthly_recurring_spend', 0) for sub in subscriptions
    )
    annual_recurring_spend = monthly_recurring_spend * 12
    
    # Determine which subscriptions to cancel
    if subscriptions_to_cancel is None:
        # Cancel top 3 most expensive
        sorted_subscriptions = sorted(
            subscriptions,
            key=lambda s: getattr(s, 'monthly_recurring_spend', 0),
            reverse=True
        )
        subscriptions_to_cancel = sorted_subscriptions[:3]
    
    # Calculate potential savings
    potential_monthly_savings = sum(
        getattr(sub, 'monthly_recurring_spend', 0) for sub in subscriptions_to_cancel
    )
    potential_annual_savings = potential_monthly_savings * 12
    
    # Format subscriptions to cancel
    cancel_list = [
        {
            "name": getattr(sub, 'merchant_name', 'Unknown'),
            "monthly_cost": getattr(sub, 'monthly_recurring_spend', 0),
            "annual_cost": getattr(sub, 'monthly_recurring_spend', 0) * 12
        }
        for sub in subscriptions_to_cancel
    ]
    
    return SubscriptionAnalyzerResult(
        total_subscriptions=total_subscriptions,
        monthly_recurring_spend=monthly_recurring_spend,
        annual_recurring_spend=annual_recurring_spend,
        subscriptions_to_cancel=cancel_list,
        potential_monthly_savings=potential_monthly_savings,
        potential_annual_savings=potential_annual_savings
    )


def plan_variable_income_budget(
    monthly_income: float,
    income_variability: float,
    essential_expenses: float,
    savings_target_percentage: float = 0.20
) -> BudgetPlannerResult:
    """
    Plan budget for variable income.
    
    Args:
        monthly_income: Average monthly income
        income_variability: Income variability (0-1, where 1 is highly variable)
        essential_expenses: Essential monthly expenses
        savings_target_percentage: Target savings percentage (default: 20%)
        
    Returns:
        BudgetPlannerResult object
    """
    # Calculate savings target
    savings_target = monthly_income * savings_target_percentage
    
    # Calculate discretionary budget
    discretionary_budget = monthly_income - essential_expenses - savings_target
    
    # Ensure discretionary is non-negative
    if discretionary_budget < 0:
        # Adjust savings target to ensure essential expenses are covered
        savings_target = max(0, monthly_income - essential_expenses)
        discretionary_budget = 0
    
    # Recommended budget
    recommended_budget = {
        "essential_expenses": essential_expenses,
        "discretionary_expenses": discretionary_budget,
        "savings": savings_target,
        "total": monthly_income
    }
    
    # Percentage-based budget
    percentage_budget = {
        "essential_percentage": (essential_expenses / monthly_income * 100) if monthly_income > 0 else 0.0,
        "discretionary_percentage": (discretionary_budget / monthly_income * 100) if monthly_income > 0 else 0.0,
        "savings_percentage": (savings_target / monthly_income * 100) if monthly_income > 0 else 0.0
    }
    
    return BudgetPlannerResult(
        monthly_income=monthly_income,
        income_variability=income_variability,
        essential_expenses=essential_expenses,
        discretionary_expenses=discretionary_budget,
        savings_target=savings_target,
        recommended_budget=recommended_budget,
        percentage_budget=percentage_budget
    )


def get_calculator_results_for_user(
    user_id: str,
    db_path: str
) -> Dict[str, Any]:
    """
    Get all calculator results for a user.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database
        
    Returns:
        Dictionary with calculator results
    """
    results = {}
    
    # Credit payoff calculator
    try:
        card_metrics, agg_metrics = analyze_credit_utilization_for_customer(user_id, db_path, 30)
        if card_metrics and len(card_metrics) > 0:
            card = card_metrics[0]
            payoff_result = calculate_credit_payoff(
                current_balance=card.balance,
                credit_limit=card.limit,
                target_utilization=0.30,
                apr=22.0
            )
            results["credit_payoff"] = {
                "current_balance": payoff_result.current_balance,
                "current_utilization": payoff_result.current_utilization,
                "target_utilization": payoff_result.target_utilization,
                "balance_reduction_needed": payoff_result.balance_reduction_needed,
                "monthly_payment": payoff_result.monthly_payment,
                "months_to_goal": payoff_result.months_to_goal,
                "total_interest_paid": payoff_result.total_interest_paid
            }
    except Exception:
        pass
    
    # Emergency fund calculator
    try:
        savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(user_id, db_path, 180)
        if savings_accounts:
            # Estimate monthly expenses from savings balance
            current_savings = savings_metrics.total_savings_balance
            estimated_expenses = current_savings / 3.0 if current_savings > 0 else 2000.0
            monthly_inflow = savings_metrics.average_monthly_inflow
            
            emergency_result = calculate_emergency_fund(
                current_savings=current_savings,
                monthly_expenses=estimated_expenses,
                target_months=3.0,
                monthly_savings=max(monthly_inflow, 200.0)
            )
            results["emergency_fund"] = {
                "current_savings": emergency_result.current_savings,
                "target_emergency_fund": emergency_result.target_emergency_fund,
                "months_coverage": emergency_result.months_coverage,
                "remaining_needed": emergency_result.remaining_needed,
                "monthly_savings": emergency_result.monthly_savings,
                "months_to_goal": emergency_result.months_to_goal,
                "achievable": emergency_result.achievable
            }
    except Exception:
        pass
    
    # Subscription analyzer
    try:
        subscriptions, sub_metrics = detect_subscriptions_for_customer(user_id, db_path, window_days=90)
        if subscriptions:
            subscription_result = analyze_subscription_costs(subscriptions)
            results["subscription_analyzer"] = {
                "total_subscriptions": subscription_result.total_subscriptions,
                "monthly_recurring_spend": subscription_result.monthly_recurring_spend,
                "annual_recurring_spend": subscription_result.annual_recurring_spend,
                "subscriptions_to_cancel": subscription_result.subscriptions_to_cancel,
                "potential_monthly_savings": subscription_result.potential_monthly_savings,
                "potential_annual_savings": subscription_result.potential_annual_savings
            }
    except Exception:
        pass
    
    # Budget planner
    try:
        income_metrics = analyze_income_stability_for_customer(user_id, db_path, 180)
        # Estimate monthly income from income metrics
        estimated_monthly_income = 3000.0  # Default estimate
        income_variability = income_metrics.income_variability
        
        # Estimate essential expenses (50% of income)
        essential_expenses = estimated_monthly_income * 0.50
        
        budget_result = plan_variable_income_budget(
            monthly_income=estimated_monthly_income,
            income_variability=income_variability,
            essential_expenses=essential_expenses,
            savings_target_percentage=0.20
        )
        results["budget_planner"] = {
            "monthly_income": budget_result.monthly_income,
            "income_variability": budget_result.income_variability,
            "recommended_budget": budget_result.recommended_budget,
            "percentage_budget": budget_result.percentage_budget
        }
    except Exception:
        pass
    
    return results

