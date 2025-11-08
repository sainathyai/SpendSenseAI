"""
Interactive Financial Calculators for SpendSenseAI.

Provides actionable tools within recommendations:
- Credit payoff calculator (time to 30% utilization)
- Emergency fund calculator (months to goal)
- Subscription cost analyzer (annual savings from cancellations)
- Budget planner for variable income
- Embeddable widgets for recommendations
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import date, timedelta
from math import ceil, log
import streamlit as st


@dataclass
class CalculatorResult:
    """Calculator result."""
    calculator_type: str
    input_values: Dict[str, Any]
    result: Dict[str, Any]
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


def calculate_credit_payoff(
    current_balance: float,
    current_limit: float,
    target_utilization: float,
    monthly_payment: float,
    apr: float = 0.20
) -> CalculatorResult:
    """
    Calculate time to reach target credit utilization.
    
    Args:
        current_balance: Current credit card balance
        current_limit: Credit limit
        target_utilization: Target utilization percentage (e.g., 30)
        monthly_payment: Monthly payment amount
        apr: Annual percentage rate (default: 20%)
        
    Returns:
        CalculatorResult object
    """
    target_balance = (target_utilization / 100) * current_limit
    balance_reduction_needed = current_balance - target_balance
    
    if balance_reduction_needed <= 0:
        return CalculatorResult(
            calculator_type="credit_payoff",
            input_values={
                "current_balance": current_balance,
                "current_limit": current_limit,
                "target_utilization": target_utilization,
                "monthly_payment": monthly_payment,
                "apr": apr
            },
            result={
                "status": "already_at_target",
                "message": f"Your utilization is already at or below {target_utilization}%",
                "current_utilization": (current_balance / current_limit * 100) if current_limit > 0 else 0
            },
            recommendations=["Maintain your current utilization rate"]
        )
    
    # Calculate monthly interest
    monthly_interest_rate = apr / 12 / 100
    
    # Calculate months to pay off (simplified - assumes fixed payment)
    # Using amortization formula approximation
    if monthly_payment > (current_balance * monthly_interest_rate):
        # Payment exceeds interest, balance will decrease
        principal_payment = monthly_payment - (current_balance * monthly_interest_rate)
        
        # Simple linear approximation (more accurate would use amortization formula)
        months_to_target = ceil(balance_reduction_needed / principal_payment) if principal_payment > 0 else None
        
        if months_to_target:
            total_interest = sum(
                (current_balance - i * principal_payment) * monthly_interest_rate
                for i in range(min(months_to_target, 100))
            )
            total_payments = months_to_target * monthly_payment
        else:
            total_interest = 0
            total_payments = 0
    else:
        months_to_target = None
        total_interest = 0
        total_payments = 0
    
    recommendations = []
    if months_to_target:
        if months_to_target > 24:
            recommendations.append(f"Consider increasing monthly payment to reduce payoff time")
        if months_to_target <= 12:
            recommendations.append("You're on track to reach your goal soon!")
    else:
        recommendations.append("Increase your monthly payment to reduce balance faster")
    
    return CalculatorResult(
        calculator_type="credit_payoff",
        input_values={
            "current_balance": current_balance,
            "current_limit": current_limit,
            "target_utilization": target_utilization,
            "monthly_payment": monthly_payment,
            "apr": apr
        },
        result={
            "current_utilization": (current_balance / current_limit * 100) if current_limit > 0 else 0,
            "target_utilization": target_utilization,
            "balance_reduction_needed": balance_reduction_needed,
            "months_to_target": months_to_target,
            "total_interest": total_interest,
            "total_payments": total_payments,
            "current_monthly_interest": current_balance * monthly_interest_rate
        },
        recommendations=recommendations
    )


def calculate_emergency_fund_timeline(
    current_savings: float,
    monthly_expenses: float,
    monthly_savings: float,
    target_months: float = 3.0
) -> CalculatorResult:
    """
    Calculate timeline to build emergency fund.
    
    Args:
        current_savings: Current savings balance
        monthly_expenses: Average monthly expenses
        monthly_savings: Amount saved per month
        target_months: Target months of expenses (default: 3.0)
        
    Returns:
        CalculatorResult object
    """
    target_emergency_fund = monthly_expenses * target_months
    remaining_needed = target_emergency_fund - current_savings
    
    if remaining_needed <= 0:
        return CalculatorResult(
            calculator_type="emergency_fund",
            input_values={
                "current_savings": current_savings,
                "monthly_expenses": monthly_expenses,
                "monthly_savings": monthly_savings,
                "target_months": target_months
            },
            result={
                "status": "goal_achieved",
                "message": f"You already have {target_months} months of expenses saved!",
                "current_coverage": current_savings / monthly_expenses if monthly_expenses > 0 else 0,
                "target_coverage": target_months
            },
            recommendations=["Maintain your emergency fund and consider increasing to 6 months"]
        )
    
    if monthly_savings <= 0:
        return CalculatorResult(
            calculator_type="emergency_fund",
            input_values={
                "current_savings": current_savings,
                "monthly_expenses": monthly_expenses,
                "monthly_savings": monthly_savings,
                "target_months": target_months
            },
            result={
                "status": "insufficient_savings",
                "message": "You need to start saving to build your emergency fund",
                "target_emergency_fund": target_emergency_fund,
                "remaining_needed": remaining_needed
            },
            recommendations=["Start by saving a small amount each month, even $50 helps"]
        )
    
    months_to_target = ceil(remaining_needed / monthly_savings)
    
    recommendations = []
    if months_to_target > 24:
        recommendations.append(f"Consider increasing monthly savings to ${monthly_savings * 1.5:.2f} to reach goal faster")
    elif months_to_target <= 6:
        recommendations.append("You're making great progress! Keep it up.")
    
    return CalculatorResult(
        calculator_type="emergency_fund",
        input_values={
            "current_savings": current_savings,
            "monthly_expenses": monthly_expenses,
            "monthly_savings": monthly_savings,
            "target_months": target_months
        },
        result={
            "target_emergency_fund": target_emergency_fund,
            "remaining_needed": remaining_needed,
            "months_to_target": months_to_target,
            "current_coverage": current_savings / monthly_expenses if monthly_expenses > 0 else 0,
            "target_coverage": target_months,
            "projected_savings_at_6mo": current_savings + (monthly_savings * 6),
            "projected_savings_at_12mo": current_savings + (monthly_savings * 12)
        },
        recommendations=recommendations
    )


def calculate_subscription_savings(
    subscriptions: list,
    subscriptions_to_cancel: list
) -> CalculatorResult:
    """
    Calculate annual savings from canceling subscriptions.
    
    Args:
        subscriptions: List of subscription dictionaries with 'merchant_name' and 'monthly_recurring_spend'
        subscriptions_to_cancel: List of merchant names to cancel
        
    Returns:
        CalculatorResult object
    """
    total_monthly_savings = 0.0
    canceled_subscriptions = []
    
    for subscription in subscriptions:
        if subscription.get('merchant_name') in subscriptions_to_cancel:
            monthly_spend = subscription.get('monthly_recurring_spend', 0.0)
            total_monthly_savings += monthly_spend
            canceled_subscriptions.append({
                "merchant": subscription.get('merchant_name'),
                "monthly_savings": monthly_spend
            })
    
    annual_savings = total_monthly_savings * 12
    five_year_savings = annual_savings * 5
    
    recommendations = []
    if annual_savings > 1000:
        recommendations.append(f"By canceling these subscriptions, you could save ${annual_savings:,.2f} per year!")
    if len(canceled_subscriptions) > 0:
        recommendations.append(f"Consider re-evaluating these subscriptions in 6 months")
    
    return CalculatorResult(
        calculator_type="subscription_savings",
        input_values={
            "total_subscriptions": len(subscriptions),
            "subscriptions_to_cancel": len(subscriptions_to_cancel)
        },
        result={
            "canceled_count": len(canceled_subscriptions),
            "monthly_savings": total_monthly_savings,
            "annual_savings": annual_savings,
            "five_year_savings": five_year_savings,
            "canceled_subscriptions": canceled_subscriptions
        },
        recommendations=recommendations
    )


def calculate_variable_income_budget(
    monthly_income_min: float,
    monthly_income_max: float,
    monthly_income_avg: float,
    essential_expenses: float,
    savings_goal_pct: float = 0.20
) -> CalculatorResult:
    """
    Calculate budget for variable income.
    
    Args:
        monthly_income_min: Minimum monthly income
        monthly_income_max: Maximum monthly income
        monthly_income_avg: Average monthly income
        essential_expenses: Essential monthly expenses
        savings_goal_pct: Target savings percentage (default: 20%)
        
    Returns:
        CalculatorResult object
    """
    # Base budget on minimum income
    base_income = monthly_income_min
    
    # Calculate essential expenses percentage
    essential_pct = (essential_expenses / base_income * 100) if base_income > 0 else 0
    
    # Calculate discretionary spending
    discretionary = base_income - essential_expenses
    savings_target = base_income * savings_goal_pct
    
    # Calculate how much can be saved in good months
    extra_income = monthly_income_avg - base_income
    additional_savings = extra_income * savings_goal_pct
    
    recommendations = []
    if essential_pct > 50:
        recommendations.append(f"Essential expenses are {essential_pct:.1f}% of minimum income. Consider reducing expenses.")
    if discretionary < savings_target:
        recommendations.append("Your discretionary spending is less than your savings goal. Consider increasing income or reducing expenses.")
    else:
        recommendations.append("Your budget is well-balanced. Save extra income in good months.")
    
    return CalculatorResult(
        calculator_type="variable_income_budget",
        input_values={
            "monthly_income_min": monthly_income_min,
            "monthly_income_max": monthly_income_max,
            "monthly_income_avg": monthly_income_avg,
            "essential_expenses": essential_expenses,
            "savings_goal_pct": savings_goal_pct
        },
        result={
            "base_income": base_income,
            "essential_expenses": essential_expenses,
            "essential_pct": essential_pct,
            "discretionary": discretionary,
            "savings_target": savings_target,
            "additional_savings_in_good_months": additional_savings,
            "recommended_savings_pct": savings_goal_pct * 100
        },
        recommendations=recommendations
    )


def render_calculator_widget(calculator_type: str, result: CalculatorResult) -> None:
    """
    Render calculator widget in Streamlit.
    
    Args:
        calculator_type: Type of calculator
        result: CalculatorResult object
    """
    st.subheader(f"📊 {calculator_type.replace('_', ' ').title()} Calculator")
    
    if calculator_type == "credit_payoff":
        if result.result.get("status") == "already_at_target":
            st.success(result.result["message"])
        else:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Current Utilization", f"{result.result.get('current_utilization', 0):.1f}%")
            
            with col2:
                st.metric("Target Utilization", f"{result.result.get('target_utilization', 0):.1f}%")
            
            with col3:
                months = result.result.get("months_to_target")
                if months:
                    st.metric("Months to Goal", f"{months}")
                else:
                    st.metric("Months to Goal", "N/A")
            
            if months:
                st.info(f"💡 You'll pay approximately ${result.result.get('total_interest', 0):,.2f} in interest during this time")
            
            for rec in result.recommendations:
                st.write(f"• {rec}")
    
    elif calculator_type == "emergency_fund":
        if result.result.get("status") == "goal_achieved":
            st.success(result.result["message"])
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Target Emergency Fund", f"${result.result.get('target_emergency_fund', 0):,.2f}")
                st.metric("Remaining Needed", f"${result.result.get('remaining_needed', 0):,.2f}")
            
            with col2:
                months = result.result.get("months_to_target")
                if months:
                    st.metric("Months to Goal", f"{months}")
                else:
                    st.metric("Months to Goal", "N/A")
                
                st.metric("Current Coverage", f"{result.result.get('current_coverage', 0):.1f} months")
            
            projected_6mo = result.result.get("projected_savings_at_6mo")
            projected_12mo = result.result.get("projected_savings_at_12mo")
            
            if projected_6mo:
                st.write(f"**Projected savings in 6 months:** ${projected_6mo:,.2f}")
            if projected_12mo:
                st.write(f"**Projected savings in 12 months:** ${projected_12mo:,.2f}")
            
            for rec in result.recommendations:
                st.write(f"• {rec}")
    
    elif calculator_type == "subscription_savings":
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Monthly Savings", f"${result.result.get('monthly_savings', 0):,.2f}")
        
        with col2:
            st.metric("Annual Savings", f"${result.result.get('annual_savings', 0):,.2f}")
        
        with col3:
            st.metric("5-Year Savings", f"${result.result.get('five_year_savings', 0):,.2f}")
        
        canceled = result.result.get("canceled_subscriptions", [])
        if canceled:
            st.write("**Canceled Subscriptions:**")
            for sub in canceled:
                st.write(f"- {sub['merchant']}: ${sub['monthly_savings']:.2f}/month")
        
        for rec in result.recommendations:
            st.write(f"• {rec}")
    
    elif calculator_type == "variable_income_budget":
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Essential Expenses", f"${result.result.get('essential_expenses', 0):,.2f}")
            st.metric("Essential %", f"{result.result.get('essential_pct', 0):.1f}%")
        
        with col2:
            st.metric("Discretionary", f"${result.result.get('discretionary', 0):,.2f}")
            st.metric("Savings Target", f"${result.result.get('savings_target', 0):,.2f}")
        
        with col3:
            st.metric("Additional Savings (Good Months)", f"${result.result.get('additional_savings_in_good_months', 0):,.2f}")
            st.metric("Recommended Savings %", f"{result.result.get('recommended_savings_pct', 0):.1f}%")
        
        for rec in result.recommendations:
            st.write(f"• {rec}")

