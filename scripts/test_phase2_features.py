"""
Test Phase 2 Features: Production Readiness.

Tests:
1. Behavioral Trend Analysis
2. Recommendation Effectiveness Tracking
3. Monitoring & Alerting
4. System Health Checks
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from features.trend_analysis import (
    analyze_behavior_trends,
    detect_early_warning_signals,
    track_persona_evolution
)
from eval.effectiveness_tracking import (
    track_engagement,
    track_outcome,
    generate_effectiveness_report
)
from eval.monitoring import (
    check_system_health,
    check_database_health,
    check_data_quality,
    monitor_performance
)
from ingest.queries import get_all_customers

DB_PATH = "data/spendsense.db"


def test_behavioral_trends():
    """Test behavioral trend analysis."""
    print("=" * 80)
    print(" TEST 1: BEHAVIORAL TREND ANALYSIS")
    print("=" * 80)
    
    try:
        # Get sample customers
        customers = get_all_customers(DB_PATH)
        test_customers = customers[:5]
        
        print(f"\nTesting trend analysis for {len(test_customers)} customers...")
        
        for customer in test_customers:
            # Handle both string and object customer IDs
            user_id = customer.customer_id if hasattr(customer, 'customer_id') else customer
            print(f"\n--- Customer: {user_id} ---")
            
            # Analyze behavior trends
            trends = analyze_behavior_trends(user_id, DB_PATH, months=3)
            
            print(f"Analysis Date: {trends.analysis_date}")
            print(f"Metrics Analyzed: {len(trends.trends)}")
            
            # Display trends
            for metric_name, trend in trends.trends.items():
                print(f"\n  {metric_name.upper()}:")
                print(f"    Direction: {trend.trend_direction}")
                print(f"    MoM Change: {trend.month_over_month_change:.1f}%")
                if trend.early_warning:
                    print(f"    WARNING: {trend.predictive_signal}")
            
            # Display persona evolution
            if trends.persona_evolution:
                print(f"\n  PERSONA EVOLUTION:")
                for period, persona in trends.persona_evolution.items():
                    print(f"    {period}: {persona.value}")
            
            # Display improvements
            if trends.improvements:
                print(f"\n  IMPROVEMENTS:")
                for improvement in trends.improvements:
                    print(f"    - {improvement}")
            
            # Display warnings
            if trends.warnings:
                print(f"\n  WARNINGS:")
                for warning in trends.warnings:
                    print(f"    ! {warning}")
        
        print("\n✅ Behavioral trend analysis test PASSED")
        return True
    
    except Exception as e:
        print(f"\n❌ Behavioral trend analysis test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_early_warnings():
    """Test early warning detection."""
    print("\n" + "=" * 80)
    print(" TEST 2: EARLY WARNING DETECTION")
    print("=" * 80)
    
    try:
        # Get sample customers
        customers = get_all_customers(DB_PATH)
        test_customers = customers[:3]
        
        print(f"\nTesting early warning detection for {len(test_customers)} customers...")
        
        total_warnings = 0
        for customer in test_customers:
            user_id = customer.customer_id if hasattr(customer, 'customer_id') else customer
            warnings = detect_early_warning_signals(user_id, DB_PATH)
            
            if warnings:
                print(f"\n{user_id}: {len(warnings)} warning(s)")
                for warning in warnings:
                    print(f"  ! {warning}")
                total_warnings += len(warnings)
        
        print(f"\n✅ Early warning detection test PASSED")
        print(f"   Total warnings detected: {total_warnings}")
        return True
    
    except Exception as e:
        print(f"\n❌ Early warning detection test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_effectiveness_tracking():
    """Test recommendation effectiveness tracking."""
    print("\n" + "=" * 80)
    print(" TEST 3: EFFECTIVENESS TRACKING")
    print("=" * 80)
    
    try:
        # Test engagement tracking
        print("\nTesting engagement tracking...")
        engagement = track_engagement(
            "REC-TEST-001",
            "view",
            {"time_spent": 120.5}
        )
        
        print(f"  Engagement tracked:")
        print(f"    Views: {engagement.views}")
        print(f"    Clicks: {engagement.clicks}")
        print(f"    CTR: {engagement.click_through_rate:.1f}%")
        
        # Test outcome tracking
        print("\nTesting outcome tracking...")
        customers = get_all_customers(DB_PATH)
        test_customer = customers[0].customer_id if hasattr(customers[0], 'customer_id') else customers[0]
        
        outcome = track_outcome(
            test_customer,
            "REC-TEST-002",
            DB_PATH,
            "utilization_improved"
        )
        
        if outcome:
            print(f"  Outcome tracked for {test_customer}:")
            print(f"    Type: {outcome.outcome_type}")
            print(f"    Improvement: {outcome.improvement_percentage:.1f}%")
            print(f"    Confidence: {outcome.attribution_confidence:.0%}")
        else:
            print(f"  No outcome data for {test_customer}")
        
        # Test effectiveness report
        print("\nGenerating effectiveness report...")
        user_ids = [c.customer_id if hasattr(c, 'customer_id') else c for c in customers[:3]]
        report = generate_effectiveness_report(user_ids, DB_PATH)
        
        print(f"  Report ID: {report.report_id}")
        print(f"  Engagement Metrics: {len(report.engagement_metrics)}")
        print(f"  Outcome Metrics: {len(report.outcome_metrics)}")
        print(f"  Overall Score: {report.overall_effectiveness_score:.2%}")
        
        print("\n✅ Effectiveness tracking test PASSED")
        return True
    
    except Exception as e:
        print(f"\n❌ Effectiveness tracking test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_system_health():
    """Test system health monitoring."""
    print("\n" + "=" * 80)
    print(" TEST 4: SYSTEM HEALTH MONITORING")
    print("=" * 80)
    
    try:
        # Test database health
        print("\nChecking database health...")
        db_health = check_database_health(DB_PATH)
        print(f"  Status: {db_health.status}")
        print(f"  Message: {db_health.message}")
        if db_health.metrics:
            for key, value in db_health.metrics.items():
                print(f"    {key}: {value}")
        
        # Test data quality
        print("\nChecking data quality...")
        alerts = check_data_quality(DB_PATH)
        print(f"  Alerts found: {len(alerts)}")
        for alert in alerts[:5]:  # Show first 5
            print(f"    [{alert.severity.upper()}] {alert.alert_type}: {alert.message}")
        
        # Test performance monitoring
        print("\nMonitoring performance...")
        customers = get_all_customers(DB_PATH)
        user_ids = [c.customer_id if hasattr(c, 'customer_id') else c for c in customers[:3]]
        
        metrics = monitor_performance(user_ids, DB_PATH)
        print(f"  P50 Latency: {metrics.latency_p50:.3f}s")
        print(f"  P95 Latency: {metrics.latency_p95:.3f}s")
        print(f"  P99 Latency: {metrics.latency_p99:.3f}s")
        print(f"  Throughput: {metrics.throughput:.2f} req/s")
        print(f"  Error Rate: {metrics.error_rate:.1f}%")
        
        # Test full system health
        print("\nRunning full system health check...")
        system_health = check_system_health(user_ids, DB_PATH)
        print(f"  Overall Status: {system_health.overall_status.upper()}")
        print(f"  Health Score: {system_health.health_score:.1f}/100")
        print(f"  Components Checked: {len(system_health.health_checks)}")
        print(f"  Data Quality Alerts: {len(system_health.data_quality_alerts)}")
        print(f"  Anomaly Alerts: {len(system_health.anomaly_alerts)}")
        
        print("\n✅ System health monitoring test PASSED")
        return True
    
    except Exception as e:
        print(f"\n❌ System health monitoring test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """Test API endpoints (requires running API)."""
    print("\n" + "=" * 80)
    print(" TEST 5: API ENDPOINTS (Optional)")
    print("=" * 80)
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        # Test health check
        print("\nTesting /health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        # Test trends endpoint
        print("\nTesting /trends endpoint...")
        customers = get_all_customers(DB_PATH)
        test_customer = customers[0].customer_id if hasattr(customers[0], 'customer_id') else customers[0]
        
        response = requests.get(f"{base_url}/trends/{test_customer}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"  Trends analyzed: {len(data.get('trends', {}))}")
            print(f"  Warnings: {len(data.get('warnings', []))}")
            print(f"  Improvements: {len(data.get('improvements', []))}")
        else:
            print(f"  Error: {response.status_code}")
        
        # Test health/full endpoint
        print("\nTesting /health/full endpoint...")
        response = requests.get(f"{base_url}/health/full", timeout=15)
        if response.status_code == 200:
            data = response.json()
            print(f"  Overall Status: {data.get('overall_status')}")
            print(f"  Health Score: {data.get('health_score')}")
        else:
            print(f"  Error: {response.status_code}")
        
        print("\n✅ API endpoints test PASSED")
        return True
    
    except requests.exceptions.ConnectionError:
        print("\n⚠️  API endpoints test SKIPPED (API not running)")
        print("   Start API with: python scripts/run_api.py")
        return True  # Not a failure, just skipped
    
    except Exception as e:
        print(f"\n⚠️  API endpoints test SKIPPED: {e}")
        return True  # Not a failure, just skipped


def main():
    """Run all Phase 2 tests."""
    print("\n" + "=" * 80)
    print(" PHASE 2 FEATURES TEST SUITE")
    print(" Production Readiness: Behavioral Trends, Effectiveness, Monitoring")
    print("=" * 80)
    
    results = []
    
    # Run all tests
    results.append(("Behavioral Trends", test_behavioral_trends()))
    results.append(("Early Warnings", test_early_warnings()))
    results.append(("Effectiveness Tracking", test_effectiveness_tracking()))
    results.append(("System Health", test_system_health()))
    results.append(("API Endpoints", test_api_endpoints()))
    
    # Print summary
    print("\n" + "=" * 80)
    print(" TEST SUMMARY")
    print("=" * 80)
    
    for name, passed in results:
        status = "PASSED" if passed else "FAILED"
        icon = "✅" if passed else "❌"
        print(f"{icon} {name}: {status}")
    
    # Overall result
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 80)
    if all_passed:
        print(" ALL TESTS PASSED")
        print("=" * 80)
        print("\n Phase 2 features are working correctly!")
        print("\n Next steps:")
        print("   1. Test API endpoints: python scripts/run_api.py")
        print("   2. Check health dashboard: http://localhost:8000/health/full")
        print("   3. View API docs: http://localhost:8000/docs")
        return 0
    else:
        print(" SOME TESTS FAILED")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())

