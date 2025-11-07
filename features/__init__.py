"""
Feature engineering module for SpendSenseAI.

This module detects behavioral signals from transaction data:
- Subscription patterns
- Credit utilization
- Savings behaviors
- Income stability
- Trend analysis
"""

__version__ = "0.1.0"

from .subscription_detection import (
    SubscriptionPattern,
    detect_subscriptions,
    calculate_monthly_recurring_spend,
    calculate_subscription_share,
    detect_subscriptions_for_customer
)

# Alias for backward compatibility
analyze_subscriptions_for_customer = detect_subscriptions_for_customer

from .credit_utilization import (
    CreditUtilizationMetrics,
    AggregateCreditMetrics,
    calculate_utilization_percentage,
    detect_minimum_payment_only,
    detect_interest_charges,
    analyze_credit_utilization_for_customer
)

# Aliases for backward compatibility
calculate_utilization = calculate_utilization_percentage
identify_interest_charges = detect_interest_charges

from .savings_pattern import (
    SavingsAccountMetrics,
    AggregateSavingsMetrics,
    is_savings_account,
    calculate_net_inflow,
    calculate_growth_rate,
    calculate_emergency_fund_coverage,
    analyze_savings_patterns_for_customer
)

# Alias for backward compatibility
identify_savings_accounts = is_savings_account

from .income_stability import (
    IncomePattern,
    IncomeStabilityMetrics,
    is_payroll_deposit,
    detect_payment_frequency,
    calculate_income_variability,
    calculate_median_pay_gap,
    calculate_cash_flow_buffer,
    detect_income_patterns,
    analyze_income_stability_for_customer
)

# Note: trend_analysis is not imported here to avoid circular dependencies
# Import it directly when needed: from features.trend_analysis import ...

__all__ = [
    # Subscription Detection
    'SubscriptionPattern',
    'detect_subscriptions',
    'calculate_monthly_recurring_spend',
    'calculate_subscription_share',
    'detect_subscriptions_for_customer',
    'analyze_subscriptions_for_customer',  # Alias for detect_subscriptions_for_customer
    
    # Credit Utilization
    'CreditUtilizationMetrics',
    'AggregateCreditMetrics',
    'calculate_utilization_percentage',
    'calculate_utilization',  # Alias for calculate_utilization_percentage
    'detect_minimum_payment_only',
    'detect_interest_charges',
    'identify_interest_charges',  # Alias for detect_interest_charges
    'analyze_credit_utilization_for_customer',
    
    # Savings Pattern
    'SavingsAccountMetrics',
    'AggregateSavingsMetrics',
    'is_savings_account',
    'identify_savings_accounts',  # Alias for is_savings_account
    'calculate_net_inflow',
    'calculate_growth_rate',
    'calculate_emergency_fund_coverage',
    'analyze_savings_patterns_for_customer',
    
    # Income Stability
    'IncomePattern',
    'IncomeStabilityMetrics',
    'is_payroll_deposit',
    'detect_payment_frequency',
    'calculate_income_variability',
    'calculate_median_pay_gap',
    'calculate_cash_flow_buffer',
    'detect_income_patterns',
    'analyze_income_stability_for_customer'
    
    # Note: Trend Analysis functions are not exported here to avoid circular dependencies
    # Import directly: from features.trend_analysis import ...
]

