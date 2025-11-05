"""
Test decision trace logging system end-to-end.

Tests the complete trace flow:
Persona → Signals → Recommendations → Trace → Review
"""

from guardrails.decision_trace import (
    create_decision_trace_tables, create_decision_trace,
    get_decision_trace, get_decision_traces_for_user,
    get_pending_reviews, update_review_status,
    ReviewStatus, SignalTrace
)
from personas.persona_prioritization import assign_personas_with_prioritization
from recommend.recommendation_builder import build_recommendations
from features.subscription_detection import detect_subscriptions_for_customer
from features.credit_utilization import analyze_credit_utilization_for_customer
from features.savings_pattern import analyze_savings_patterns_for_customer
from features.income_stability import analyze_income_stability_for_customer
from datetime import datetime

db_path = 'data/spendsense.db'
sample_customer = 'CUST000001'

print("="*60)
print("Testing Decision Trace Logging System")
print("="*60)
print()

# Step 1: Create decision trace tables
print("[STEP 1] Creating decision trace tables...")
create_decision_trace_tables(db_path)
print("   [SUCCESS] Decision trace tables created")

print()

# Step 2: Assign persona
print("[STEP 2] Assigning persona...")
persona_assignment = assign_personas_with_prioritization(sample_customer, db_path)

if persona_assignment.primary_persona:
    print(f"   Primary Persona: {persona_assignment.primary_persona.persona_type.value}")
    print(f"   Confidence: {persona_assignment.primary_persona.confidence_score:.2%}")
else:
    print("   No persona assigned")
    exit(1)

print()

# Step 3: Collect signals
print("[STEP 3] Collecting behavioral signals...")
signals = []

# Subscription signals
subscriptions, sub_metrics = detect_subscriptions_for_customer(sample_customer, db_path, window_days=90)
if sub_metrics['subscription_count'] > 0:
    signals.append(SignalTrace(
        signal_type="subscription",
        window_days=90,
        metrics=sub_metrics,
        detected_at=datetime.now()
    ))
    print(f"   Subscriptions: {sub_metrics['subscription_count']} active")

# Credit utilization signals
card_metrics, agg_metrics = analyze_credit_utilization_for_customer(sample_customer, db_path, 30)
if card_metrics:
    signals.append(SignalTrace(
        signal_type="credit_utilization",
        window_days=30,
        metrics={
            'aggregate_utilization': agg_metrics.aggregate_utilization,
            'total_monthly_interest': agg_metrics.total_monthly_interest,
            'overdue_card_count': agg_metrics.overdue_card_count
        },
        detected_at=datetime.now()
    ))
    print(f"   Credit Utilization: {agg_metrics.aggregate_utilization:.1f}%")

# Savings signals
savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(sample_customer, db_path, 180)
if savings_accounts:
    signals.append(SignalTrace(
        signal_type="savings",
        window_days=180,
        metrics={
            'total_savings_balance': savings_metrics.total_savings_balance,
            'overall_growth_rate': savings_metrics.overall_growth_rate,
            'average_monthly_inflow': savings_metrics.average_monthly_inflow
        },
        detected_at=datetime.now()
    ))
    print(f"   Savings Balance: ${savings_metrics.total_savings_balance:,.2f}")

# Income signals
income_metrics = analyze_income_stability_for_customer(sample_customer, db_path, 180)
signals.append(SignalTrace(
    signal_type="income",
    window_days=180,
    metrics={
        'median_pay_gap_days': income_metrics.median_pay_gap_days,
        'cash_flow_buffer_months': income_metrics.cash_flow_buffer_months,
        'income_variability': income_metrics.income_variability
    },
    detected_at=datetime.now()
))
print(f"   Income Stability: {income_metrics.median_pay_gap_days:.1f} day median pay gap")

print(f"   Total Signals: {len(signals)}")

print()

# Step 4: Build recommendations
print("[STEP 4] Building recommendations...")
recommendations = build_recommendations(
    sample_customer,
    db_path,
    persona_assignment,
    estimated_income=50000.0,
    estimated_credit_score=700,
    check_consent=False  # Skip consent check for testing
)

print(f"   Education Items: {len(recommendations.education_items)}")
print(f"   Partner Offers: {len(recommendations.partner_offers)}")

print()

# Step 5: Create decision trace
print("[STEP 5] Creating decision trace...")
trace = create_decision_trace(
    sample_customer,
    db_path,
    signals,
    persona_assignment,
    recommendations
)

print(f"   Trace ID: {trace.trace_id}")
print(f"   User ID: {trace.user_id}")
print(f"   Timestamp: {trace.timestamp}")
print(f"   Review Status: {trace.review_status.value}")
print(f"   Signals: {len(trace.signals)}")
print(f"   Analysis Windows: 30d={trace.analysis_window_30d}, 180d={trace.analysis_window_180d}")

print()

# Step 6: Retrieve trace
print("[STEP 6] Retrieving decision trace...")
retrieved = get_decision_trace(trace.trace_id, db_path)
if retrieved:
    print(f"   Trace ID: {retrieved['trace_id']}")
    print(f"   User ID: {retrieved['user_id']}")
    print(f"   Review Status: {retrieved['review_status']}")

print()

# Step 7: Get all traces for user
print("[STEP 7] Retrieving all traces for user...")
all_traces = get_decision_traces_for_user(sample_customer, db_path)
print(f"   Total Traces: {len(all_traces)}")

print()

# Step 8: Get pending reviews
print("[STEP 8] Retrieving pending reviews...")
pending = get_pending_reviews(db_path)
print(f"   Pending Reviews: {len(pending)}")

print()

# Step 9: Update review status
print("[STEP 9] Updating review status...")
success = update_review_status(
    trace.trace_id,
    db_path,
    ReviewStatus.APPROVED,
    reviewed_by="OPERATOR001",
    review_notes="Recommendations look good"
)
print(f"   Update Success: {success}")

# Verify update
updated = get_decision_trace(trace.trace_id, db_path)
if updated:
    print(f"   New Review Status: {updated['review_status']}")
    print(f"   Reviewed By: {updated['reviewed_by']}")

print()

# Step 10: Check pending reviews again
print("[STEP 10] Checking pending reviews after approval...")
pending_after = get_pending_reviews(db_path)
print(f"   Pending Reviews: {len(pending_after)}")

print("\n" + "="*60)
print("[SUCCESS] Decision trace logging system tested successfully!")
print("="*60)

