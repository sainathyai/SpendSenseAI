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
    analyze_subscriptions_for_customer,
    detect_subscriptions_for_customer
)

from .credit_utilization import (
    CreditUtilizationMetrics,
    AggregateCreditMetrics,
    calculate_utilization,
    detect_minimum_payment_only,
    identify_interest_charges,
    analyze_credit_utilization_for_customer
)

from .savings_pattern import (
    SavingsAccountMetrics,
    AggregateSavingsMetrics,
    identify_savings_accounts,
    calculate_net_inflow,
    calculate_growth_rate,
    calculate_emergency_fund_coverage,
    analyze_savings_patterns_for_customer
)

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

from .trend_analysis import (
    TrendPoint,
    TrendAnalysis,
    BehaviorTrends,
    calculate_month_over_month_trend,
    analyze_utilization_trend,
    analyze_savings_trend,
    track_persona_evolution,
    analyze_behavior_trends,
    detect_early_warning_signals,
    generate_trend_report
)

__all__ = [
    # Subscription Detection
    'SubscriptionPattern',
    'detect_subscriptions',
    'calculate_monthly_recurring_spend',
    'calculate_subscription_share',
    'analyze_subscriptions_for_customer',
    'detect_subscriptions_for_customer',
    
    # Credit Utilization
    'CreditUtilizationMetrics',
    'AggregateCreditMetrics',
    'calculate_utilization',
    'detect_minimum_payment_only',
    'identify_interest_charges',
    'analyze_credit_utilization_for_customer',
    
    # Savings Pattern
    'SavingsAccountMetrics',
    'AggregateSavingsMetrics',
    'identify_savings_accounts',
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
    'analyze_income_stability_for_customer',
    
    # Trend Analysis
    'TrendPoint',
    'TrendAnalysis',
    'BehaviorTrends',
    'calculate_month_over_month_trend',
    'analyze_utilization_trend',
    'analyze_savings_trend',
    'track_persona_evolution',
    'analyze_behavior_trends',
    'detect_early_warning_signals',
    'generate_trend_report'
]

