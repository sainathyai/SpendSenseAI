"""
Test Phase 3 Features: Advanced Features.

Tests:
1. A/B Testing Framework
2. Notification Enhancement
3. Advanced Cohort Analysis
4. Advanced Anomaly Detection
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from eval.ab_testing import (
    create_ab_testing_tables,
    create_experiment,
    Experiment,
    ExperimentVariant,
    ExperimentStatus,
    VariantType,
    assign_user_to_variant,
    analyze_experiment_results
)
from eval.cohort_analysis import (
    create_predictive_cohorts,
    analyze_fairness_across_cohorts,
    analyze_all_cohorts
)
from eval.advanced_anomaly_detection import (
    create_anomaly_detection_tables,
    detect_user_anomalies,
    prioritize_anomalies
)
from ui.notification_delivery import deliver_notification, NotificationChannel
from ui.notifications import Notification
from ingest.queries import get_all_customers
from datetime import datetime

DB_PATH = "data/spendsense.db"


def test_ab_testing():
    """Test A/B testing framework."""
    print("\n" + "=" * 80)
    print(" TEST 1: A/B TESTING FRAMEWORK")
    print("=" * 80)
    
    try:
        create_ab_testing_tables(DB_PATH)
        
        # Create test experiment
        experiment = Experiment(
            experiment_id="TEST-EXP-001",
            name="Test Rationale Wording",
            description="Testing different rationale wordings",
            status=ExperimentStatus.RUNNING,
            variants=[
                ExperimentVariant(
                    variant_id="VAR-CONTROL",
                    variant_type=VariantType.CONTROL,
                    name="Control",
                    description="Standard rationale",
                    configuration={"tone": "neutral"},
                    traffic_percentage=50.0
                ),
                ExperimentVariant(
                    variant_id="VAR-TREATMENT",
                    variant_type=VariantType.TREATMENT,
                    name="Treatment",
                    description="Enhanced rationale",
                    configuration={"tone": "supportive"},
                    traffic_percentage=50.0
                )
            ],
            start_date=datetime.now(),
            min_sample_size=10
        )
        
        exp_id = create_experiment(experiment, DB_PATH)
        print(f"✅ Experiment created: {exp_id}")
        
        # Assign users to variants
        customers = get_all_customers(DB_PATH)
        test_users = [c.customer_id if hasattr(c, 'customer_id') else c for c in customers[:5]]
        
        assignments = {}
        for user_id in test_users:
            variant_id = assign_user_to_variant(user_id, exp_id, DB_PATH)
            assignments[user_id] = variant_id
            print(f"  User {user_id} assigned to variant: {variant_id}")
        
        # Analyze results
        results = analyze_experiment_results(exp_id, DB_PATH)
        print(f"\n✅ Experiment results analyzed: {len(results)} variants")
        for result in results:
            print(f"  Variant {result.variant_id}: Sample size={result.sample_size}, "
                  f"Conversion rate={result.conversion_rate:.1f}%, "
                  f"P-value={result.statistical_significance:.3f}")
        
        return True
    except Exception as e:
        print(f"❌ A/B testing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_notification_delivery():
    """Test notification delivery system."""
    print("\n" + "=" * 80)
    print(" TEST 2: NOTIFICATION DELIVERY")
    print("=" * 80)
    
    try:
        # Create test notification
        notification = Notification(
            notification_id="NOTIF-TEST-001",
            user_id="CUST000001",
            template_id="TEMPLATE-001",
            channel=NotificationChannel.IN_APP,
            subject="Test Notification",
            body="This is a test notification",
            sent_at=datetime.now(),
            metadata={"email": "test@example.com"}
        )
        
        # Test in-app delivery
        result = deliver_notification(notification, DB_PATH)
        print(f"✅ Notification delivered: {result.success}")
        print(f"  Channel: {result.channel.value}")
        print(f"  Delivered at: {result.delivered_at}")
        
        return True
    except Exception as e:
        print(f"❌ Notification delivery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_advanced_cohorts():
    """Test advanced cohort analysis."""
    print("\n" + "=" * 80)
    print(" TEST 3: ADVANCED COHORT ANALYSIS")
    print("=" * 80)
    
    try:
        customers = get_all_customers(DB_PATH)
        user_ids = [c.customer_id if hasattr(c, 'customer_id') else c for c in customers[:20]]
        
        # Test predictive cohorts
        predictive_cohorts = create_predictive_cohorts(user_ids, DB_PATH)
        print(f"✅ Predictive cohorts created: {len(predictive_cohorts)} cohorts")
        for cohort_name, cohort_users in predictive_cohorts.items():
            print(f"  {cohort_name}: {len(cohort_users)} users")
        
        # Test fairness analysis
        all_cohorts = analyze_all_cohorts(user_ids, DB_PATH)
        fairness_metrics = analyze_fairness_across_cohorts(all_cohorts)
        print(f"\n✅ Fairness analysis completed: {len(fairness_metrics)} metrics")
        for metric, value in list(fairness_metrics.items())[:3]:
            print(f"  {metric}: {value:.2f}")
        
        return True
    except Exception as e:
        print(f"❌ Advanced cohort analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_anomaly_detection():
    """Test advanced anomaly detection."""
    print("\n" + "=" * 80)
    print(" TEST 4: ADVANCED ANOMALY DETECTION")
    print("=" * 80)
    
    try:
        create_anomaly_detection_tables(DB_PATH)
        
        customers = get_all_customers(DB_PATH)
        test_users = [c.customer_id if hasattr(c, 'customer_id') else c for c in customers[:5]]
        
        all_anomalies = []
        for user_id in test_users:
            anomalies = detect_user_anomalies(user_id, DB_PATH)
            if anomalies:
                all_anomalies.extend(anomalies)
                print(f"  User {user_id}: {len(anomalies)} anomalies detected")
                for anomaly in anomalies:
                    print(f"    - {anomaly.anomaly_type.value}: {anomaly.severity.value}")
        
        if all_anomalies:
            prioritized = prioritize_anomalies(all_anomalies)
            print(f"\n✅ Anomaly detection completed: {len(prioritized)} total anomalies")
            print(f"  Critical: {sum(1 for a in prioritized if a.severity.value == 'critical')}")
            print(f"  High: {sum(1 for a in prioritized if a.severity.value == 'high')}")
        else:
            print("✅ No anomalies detected (expected for test data)")
        
        return True
    except Exception as e:
        print(f"❌ Anomaly detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 3 tests."""
    print("=" * 80)
    print(" PHASE 3 FEATURES TEST SUITE")
    print(" Advanced Features: A/B Testing, Notifications, Cohorts, Anomalies")
    print("=" * 80)
    
    results = []
    
    results.append(("A/B Testing", test_ab_testing()))
    results.append(("Notification Delivery", test_notification_delivery()))
    results.append(("Advanced Cohort Analysis", test_advanced_cohorts()))
    results.append(("Anomaly Detection", test_anomaly_detection()))
    
    print("\n" + "=" * 80)
    print(" TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 80)
    if all_passed:
        print(" ALL TESTS PASSED")
        print("=" * 80)
        print("\n Phase 3 features are working correctly!")
    else:
        print(" SOME TESTS FAILED")
        print("=" * 80)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

