"""
Test all detection engines together.

Tests subscription detection, credit utilization, savings patterns,
and income stability for a sample customer.
"""

from datetime import date, timedelta
from features.subscription_detection import detect_subscriptions_for_customer
from features.credit_utilization import analyze_credit_utilization_for_customer
from features.savings_pattern import analyze_savings_patterns_for_customer
from features.income_stability import analyze_income_stability_for_customer

db_path = 'data/spendsense.db'
sample_customer = 'CUST000001'

print("="*60)
print("Testing All Detection Engines")
print("="*60)
print()

# Test Subscription Detection
print("[TEST] Subscription Detection Engine")
print("-" * 60)
subscriptions, sub_metrics = detect_subscriptions_for_customer(
    sample_customer, db_path, window_days=180
)
print(f"   Subscriptions Found: {sub_metrics['subscription_count']}")
print(f"   Active Subscriptions: {sub_metrics['active_subscription_count']}")
print(f"   Monthly Recurring Spend: ${sub_metrics['total_monthly_recurring_spend']:.2f}")
print(f"   Subscription Share: {sub_metrics['subscription_share_of_total']:.1f}%")
if subscriptions:
    print(f"   Top Subscription: {subscriptions[0].merchant_name} (${subscriptions[0].monthly_recurring_spend:.2f}/month)")
print()

# Test Credit Utilization
print("[TEST] Credit Utilization Analysis")
print("-" * 60)
card_metrics, agg_metrics = analyze_credit_utilization_for_customer(
    sample_customer, db_path, window_days=30
)
print(f"   Credit Cards: {agg_metrics.card_count}")
print(f"   Aggregate Utilization: {agg_metrics.aggregate_utilization:.1f}%")
print(f"   High Utilization Cards: {agg_metrics.high_utilization_card_count}")
print(f"   Critical Utilization Cards: {agg_metrics.critical_utilization_card_count}")
print(f"   Overdue Cards: {agg_metrics.overdue_card_count}")
print(f"   Total Monthly Interest: ${agg_metrics.total_monthly_interest:.2f}")
if card_metrics:
    print(f"   Top Card: {card_metrics[0].account_id} - {card_metrics[0].utilization_percentage:.1f}% utilization")
print()

# Test Savings Patterns
print("[TEST] Savings Pattern Detection")
print("-" * 60)
savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(
    sample_customer, db_path, window_days=180
)
print(f"   Savings Accounts: {savings_metrics.savings_account_count}")
print(f"   Total Savings Balance: ${savings_metrics.total_savings_balance:.2f}")
print(f"   Net Inflow (180d): ${savings_metrics.total_net_inflow:.2f}")
print(f"   Growth Rate: {savings_metrics.overall_growth_rate:.1f}%")
print(f"   Average Monthly Inflow: ${savings_metrics.average_monthly_inflow:.2f}")
if savings_accounts:
    print(f"   Top Account: {savings_accounts[0].account_id} - ${savings_accounts[0].current_balance:.2f}")
print()

# Test Income Stability
print("[TEST] Income Stability Analysis")
print("-" * 60)
income_metrics = analyze_income_stability_for_customer(
    sample_customer, db_path, window_days=180
)
print(f"   Income Sources: {income_metrics.income_source_count}")
print(f"   Total Income (180d): ${income_metrics.total_income:.2f}")
print(f"   Average Monthly Income: ${income_metrics.average_monthly_income:.2f}")
print(f"   Payment Frequency: {income_metrics.payment_frequency}")
print(f"   Income Variability: {income_metrics.income_variability:.2f}")
print(f"   Median Pay Gap: {income_metrics.median_pay_gap_days:.1f} days")
print(f"   Is Gig Worker: {'Yes' if income_metrics.is_gig_worker else 'No'}")
if income_metrics.primary_income_pattern:
    print(f"   Primary Income: {income_metrics.primary_income_pattern.source_name}")
print()

print("="*60)
print("[SUCCESS] All detection engines tested successfully!")
print("="*60)

