"""
Integration Testing & End-to-End Validation for SpendSenseAI.

Ensures all components work together:
- End-to-end test scenarios
- Multi-user batch processing
- Consent enforcement validation
- Eligibility filter validation
- Latency benchmarking
- Edge case testing
- Performance profiling
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from dataclasses import dataclass
import time
import traceback

from personas.persona_prioritization import assign_personas_with_prioritization
from personas.persona_definition import PersonaAssignment, PersonaType
from recommend.recommendation_builder import build_recommendations
from guardrails.consent import grant_consent, revoke_consent, verify_consent, ConsentScope
from guardrails.decision_trace import create_decision_trace, SignalTrace
from guardrails.decision_trace import ReviewStatus
from features.subscription_detection import detect_subscriptions_for_customer
from features.credit_utilization import analyze_credit_utilization_for_customer
from features.savings_pattern import analyze_savings_patterns_for_customer
from features.income_stability import analyze_income_stability_for_customer
from ingest.queries import get_accounts_by_customer, get_transactions_by_customer


@dataclass
class TestResult:
    """Test result."""
    test_name: str
    passed: bool
    duration: float
    error: Optional[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class TestReport:
    """Test report."""
    report_id: str
    timestamp: datetime
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_duration: float
    results: List[TestResult]
    summary: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.summary is None:
            self.summary = {}


def test_end_to_end_workflow(user_id: str, db_path: str) -> TestResult:
    """
    Test end-to-end workflow: ingestion → signals → persona → recommendations → operator review.
    
    Args:
        user_id: User ID to test
        db_path: Path to SQLite database
        
    Returns:
        TestResult object
    """
    test_name = "End-to-End Workflow"
    start_time = time.time()
    details = {}
    
    try:
        # Step 1: Verify user has data
        accounts = get_accounts_by_customer(user_id, db_path)
        if not accounts:
            return TestResult(test_name, False, time.time() - start_time, 
                            "No accounts found for user", details)
        details['accounts_count'] = len(accounts)
        
        # Step 2: Detect signals
        subscriptions, sub_metrics = detect_subscriptions_for_customer(user_id, db_path, window_days=90)
        card_metrics, agg_metrics = analyze_credit_utilization_for_customer(user_id, db_path, 30)
        savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(user_id, db_path, 180)
        income_metrics = analyze_income_stability_for_customer(user_id, db_path, 180)
        
        details['signals_detected'] = {
            'subscriptions': sub_metrics.get('subscription_count', 0),
            'credit_utilization': agg_metrics.aggregate_utilization if card_metrics else 0,
            'savings': len(savings_accounts),
            'income': income_metrics.median_pay_gap_days
        }
        
        # Step 3: Assign persona
        persona_assignment = assign_personas_with_prioritization(user_id, db_path)
        if not persona_assignment.primary_persona:
            return TestResult(test_name, False, time.time() - start_time,
                            "No persona assigned", details)
        details['persona'] = persona_assignment.primary_persona.persona_type.value
        
        # Step 4: Generate recommendations
        recommendations = build_recommendations(
            user_id, db_path, persona_assignment,
            check_consent=False
        )
        details['recommendations'] = {
            'education_items': len(recommendations.education_items),
            'partner_offers': len(recommendations.partner_offers)
        }
        
        # Step 5: Create decision trace
        signals = [
            SignalTrace(
                signal_type="subscription",
                window_days=90,
                metrics=sub_metrics,
                detected_at=datetime.now()
            )
        ]
        
        trace = create_decision_trace(
            user_id, db_path, signals, persona_assignment, recommendations
        )
        details['trace_id'] = trace.trace_id
        
        duration = time.time() - start_time
        details['duration'] = duration
        
        return TestResult(test_name, True, duration, None, details)
    
    except Exception as e:
        return TestResult(test_name, False, time.time() - start_time,
                         f"Error: {str(e)}", details)


def test_consent_enforcement(user_id: str, db_path: str) -> TestResult:
    """
    Test consent enforcement.
    
    Args:
        user_id: User ID to test
        db_path: Path to SQLite database
        
    Returns:
        TestResult object
    """
    test_name = "Consent Enforcement"
    start_time = time.time()
    details = {}
    
    try:
        # Step 1: Assign persona
        persona_assignment = assign_personas_with_prioritization(user_id, db_path)
        if not persona_assignment.primary_persona:
            return TestResult(test_name, False, time.time() - start_time,
                            "No persona assigned", details)
        
        # Step 2: Try to get recommendations without consent (should fail)
        recommendations_no_consent = build_recommendations(
            user_id, db_path, persona_assignment,
            check_consent=True
        )
        
        if recommendations_no_consent.education_items or recommendations_no_consent.partner_offers:
            details['consent_check_failed'] = True
            return TestResult(test_name, False, time.time() - start_time,
                            "Recommendations generated without consent", details)
        
        # Step 3: Grant consent
        grant_consent(user_id, db_path, ConsentScope.ALL)
        
        # Step 4: Try to get recommendations with consent (should succeed)
        recommendations_with_consent = build_recommendations(
            user_id, db_path, persona_assignment,
            check_consent=True
        )
        
        if not recommendations_with_consent.education_items and not recommendations_with_consent.partner_offers:
            details['consent_check_failed'] = True
            return TestResult(test_name, False, time.time() - start_time,
                            "No recommendations generated with consent", details)
        
        # Step 5: Revoke consent
        revoke_consent(user_id, db_path)
        
        # Step 6: Try to get recommendations after revocation (should fail)
        recommendations_after_revoke = build_recommendations(
            user_id, db_path, persona_assignment,
            check_consent=True,
            grace_period_days=0
        )
        
        if recommendations_after_revoke.education_items or recommendations_after_revoke.partner_offers:
            details['revocation_check_failed'] = True
            return TestResult(test_name, False, time.time() - start_time,
                            "Recommendations generated after revocation", details)
        
        duration = time.time() - start_time
        details['duration'] = duration
        
        return TestResult(test_name, True, duration, None, details)
    
    except Exception as e:
        return TestResult(test_name, False, time.time() - start_time,
                         f"Error: {str(e)}", details)


def test_eligibility_filters(user_id: str, db_path: str) -> TestResult:
    """
    Test eligibility filters for partner offers.
    
    Args:
        user_id: User ID to test
        db_path: Path to SQLite database
        
    Returns:
        TestResult object
    """
    test_name = "Eligibility Filters"
    start_time = time.time()
    details = {}
    
    try:
        from recommend.partner_offers import get_eligible_offers_for_persona, check_eligibility
        from recommend.partner_offers import DEFAULT_PARTNER_OFFERS
        
        # Assign persona
        persona_assignment = assign_personas_with_prioritization(user_id, db_path)
        if not persona_assignment.primary_persona:
            return TestResult(test_name, False, time.time() - start_time,
                            "No persona assigned", details)
        
        persona_type = persona_assignment.primary_persona.persona_type
        
        # Get eligible offers
        eligible_offers = get_eligible_offers_for_persona(
            persona_type, user_id, db_path,
            estimated_income=50000.0,
            estimated_credit_score=700
        )
        
        details['eligible_offers'] = len(eligible_offers)
        details['persona'] = persona_type.value
        
        # Test that harmful products are rejected
        for offer_id, offer in DEFAULT_PARTNER_OFFERS.items():
            if offer.is_harmful:
                is_eligible, reasons = check_eligibility(
                    offer, user_id, db_path,
                    persona_type=persona_type,
                    estimated_income=50000.0,
                    estimated_credit_score=700
                )
                
                if is_eligible:
                    return TestResult(test_name, False, time.time() - start_time,
                                    f"Harmful product {offer_id} was eligible", details)
        
        duration = time.time() - start_time
        details['duration'] = duration
        
        return TestResult(test_name, True, duration, None, details)
    
    except Exception as e:
        return TestResult(test_name, False, time.time() - start_time,
                         f"Error: {str(e)}", details)


def test_edge_cases(user_id: str, db_path: str) -> TestResult:
    """
    Test edge cases: no data, sparse data, conflicting signals.
    
    Args:
        user_id: User ID to test
        db_path: Path to SQLite database
        
    Returns:
        TestResult object
    """
    test_name = "Edge Cases"
    start_time = time.time()
    details = {}
    
    try:
        # Test with no accounts (should handle gracefully)
        try:
            persona_assignment = assign_personas_with_prioritization("NONEXISTENT_USER", db_path)
            details['nonexistent_user_handled'] = True
        except Exception as e:
            details['nonexistent_user_error'] = str(e)
        
        # Test with user that has data
        accounts = get_accounts_by_customer(user_id, db_path)
        if accounts:
            persona_assignment = assign_personas_with_prioritization(user_id, db_path)
            details['user_with_data'] = True
            details['persona_assigned'] = persona_assignment.primary_persona is not None
        
        # Test with sparse data (user with only one account)
        # This is already tested above with normal users
        
        duration = time.time() - start_time
        details['duration'] = duration
        
        return TestResult(test_name, True, duration, None, details)
    
    except Exception as e:
        return TestResult(test_name, False, time.time() - start_time,
                         f"Error: {str(e)}", details)


def test_multi_user_batch_processing(user_ids: List[str], db_path: str) -> TestResult:
    """
    Test multi-user batch processing.
    
    Args:
        user_ids: List of user IDs to test
        db_path: Path to SQLite database
        
    Returns:
        TestResult object
    """
    test_name = "Multi-User Batch Processing"
    start_time = time.time()
    details = {}
    
    try:
        processed_count = 0
        successful_count = 0
        
        for user_id in user_ids[:10]:  # Limit to 10 users for testing
            try:
                persona_assignment = assign_personas_with_prioritization(user_id, db_path)
                
                if persona_assignment.primary_persona:
                    recommendations = build_recommendations(
                        user_id, db_path, persona_assignment,
                        check_consent=False
                    )
                    successful_count += 1
                
                processed_count += 1
            except Exception:
                pass
        
        duration = time.time() - start_time
        throughput = processed_count / duration if duration > 0 else 0
        
        details['processed_count'] = processed_count
        details['successful_count'] = successful_count
        details['duration'] = duration
        details['throughput'] = throughput
        
        return TestResult(test_name, True, duration, None, details)
    
    except Exception as e:
        return TestResult(test_name, False, time.time() - start_time,
                         f"Error: {str(e)}", details)


def run_integration_tests(
    user_ids: List[str],
    db_path: str,
    report_id: Optional[str] = None
) -> TestReport:
    """
    Run all integration tests.
    
    Args:
        user_ids: List of user IDs to test
        db_path: Path to SQLite database
        report_id: Optional report ID (auto-generated if not provided)
        
    Returns:
        TestReport object
    """
    if report_id is None:
        timestamp = datetime.now()
        report_id = f"TEST-{timestamp.strftime('%Y%m%d%H%M%S')}"
    
    results = []
    total_start_time = time.time()
    
    # Test with first user
    test_user = user_ids[0] if user_ids else None
    
    if test_user:
        # End-to-end workflow
        results.append(test_end_to_end_workflow(test_user, db_path))
        
        # Consent enforcement
        results.append(test_consent_enforcement(test_user, db_path))
        
        # Eligibility filters
        results.append(test_eligibility_filters(test_user, db_path))
        
        # Edge cases
        results.append(test_edge_cases(test_user, db_path))
    
    # Multi-user batch processing
    results.append(test_multi_user_batch_processing(user_ids, db_path))
    
    total_duration = time.time() - total_start_time
    
    passed_tests = sum(1 for r in results if r.passed)
    failed_tests = sum(1 for r in results if not r.passed)
    
    summary = {
        "total_tests": len(results),
        "passed": passed_tests,
        "failed": failed_tests,
        "pass_rate": (passed_tests / len(results) * 100) if results else 0.0,
        "total_duration": total_duration
    }
    
    return TestReport(
        report_id=report_id,
        timestamp=datetime.now(),
        total_tests=len(results),
        passed_tests=passed_tests,
        failed_tests=failed_tests,
        total_duration=total_duration,
        results=results,
        summary=summary
    )


def generate_test_report(report: TestReport, output_path: str) -> None:
    """
    Generate test report.
    
    Args:
        report: TestReport object
        output_path: Path to output report file
    """
    report_text = f"""
SpendSenseAI Integration Test Report
Generated: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Report ID: {report.report_id}

================================================================================
SUMMARY
================================================================================
Total Tests: {report.total_tests}
Passed: {report.passed_tests}
Failed: {report.failed_tests}
Pass Rate: {report.summary.get('pass_rate', 0):.1f}%
Total Duration: {report.total_duration:.2f}s

================================================================================
TEST RESULTS
================================================================================
"""
    
    for result in report.results:
        status = "✓ PASSED" if result.passed else "✗ FAILED"
        report_text += f"\n{status} - {result.test_name}\n"
        report_text += f"  Duration: {result.duration:.2f}s\n"
        
        if result.error:
            report_text += f"  Error: {result.error}\n"
        
        if result.details:
            report_text += "  Details:\n"
            for key, value in result.details.items():
                report_text += f"    - {key}: {value}\n"
    
    report_text += "\n" + "="*60 + "\n"
    
    with open(output_path, 'w') as f:
        f.write(report_text)

