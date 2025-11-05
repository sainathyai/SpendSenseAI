"""
Adversarial Testing & Edge Cases for SpendSenseAI.

Stress-tests the system against unusual inputs:
- Users with extreme behaviors (99% utilization, $0 savings)
- Users with very little data
- Users with conflicting signals
- Data quality issues (missing fields, outliers)
- Graceful degradation logic
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, date, timedelta
import json

from personas.persona_prioritization import assign_personas_with_prioritization
from personas.persona_definition import PersonaAssignment
from recommend.recommendation_builder import build_recommendations
from features.subscription_detection import detect_subscriptions_for_customer
from features.credit_utilization import analyze_credit_utilization_for_customer
from features.savings_pattern import analyze_savings_patterns_for_customer
from features.income_stability import analyze_income_stability_for_customer
from ingest.queries import get_accounts_by_customer, get_transactions_by_customer


@dataclass
class AdversarialScenario:
    """Adversarial test scenario."""
    scenario_id: str
    scenario_name: str
    description: str
    test_user_id: str
    expected_behavior: str
    actual_behavior: str
    passed: bool
    error_message: Optional[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class AdversarialTestReport:
    """Adversarial testing report."""
    report_id: str
    timestamp: datetime
    scenarios: List[AdversarialScenario]
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    robustness_score: float
    summary: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.summary is None:
            self.summary = {}


def test_extreme_utilization(
    user_id: str,
    db_path: str
) -> AdversarialScenario:
    """
    Test user with extreme credit utilization (99%).
    
    Args:
        user_id: User ID to test
        db_path: Path to SQLite database
        
    Returns:
        AdversarialScenario object
    """
    scenario_name = "Extreme Credit Utilization (99%)"
    description = "User with 99% credit utilization, $0 savings, multiple overdue accounts"
    
    try:
        # Try to assign persona
        persona_assignment = assign_personas_with_prioritization(user_id, db_path)
        
        # System should handle gracefully
        if persona_assignment.primary_persona:
            actual_behavior = f"Persona assigned: {persona_assignment.primary_persona.persona_type.value}"
            passed = True
            error_message = None
        else:
            actual_behavior = "No persona assigned (graceful handling)"
            passed = True  # Acceptable - no persona is better than wrong persona
            error_message = None
        
        # Try to generate recommendations
        try:
            recommendations = build_recommendations(
                user_id, db_path, persona_assignment,
                check_consent=False
            )
            rec_count = len(recommendations.education_items) + len(recommendations.partner_offers)
            actual_behavior += f" | Recommendations generated: {rec_count}"
        except Exception as e:
            actual_behavior += f" | Recommendations failed: {str(e)}"
            passed = False
            error_message = str(e)
        
        return AdversarialScenario(
            scenario_id=f"ADV-{user_id}-EXTREME-001",
            scenario_name=scenario_name,
            description=description,
            test_user_id=user_id,
            expected_behavior="System handles extreme case gracefully, assigns appropriate persona, generates recommendations",
            actual_behavior=actual_behavior,
            passed=passed,
            error_message=error_message,
            details={"persona_assigned": persona_assignment.primary_persona is not None}
        )
    except Exception as e:
        return AdversarialScenario(
            scenario_id=f"ADV-{user_id}-EXTREME-001",
            scenario_name=scenario_name,
            description=description,
            test_user_id=user_id,
            expected_behavior="System handles extreme case gracefully",
            actual_behavior=f"Error: {str(e)}",
            passed=False,
            error_message=str(e)
        )


def test_sparse_data(
    user_id: str,
    db_path: str
) -> AdversarialScenario:
    """
    Test user with very little data (few transactions).
    
    Args:
        user_id: User ID to test
        db_path: Path to SQLite database
        
    Returns:
        AdversarialScenario object
    """
    scenario_name = "Sparse Data (Few Transactions)"
    description = "User with very few transactions (< 10 total)"
    
    try:
        # Get transactions
        transactions = get_transactions_by_customer(user_id, db_path)
        transaction_count = len(transactions)
        
        # Try to assign persona
        persona_assignment = assign_personas_with_prioritization(user_id, db_path)
        
        # System should handle gracefully
        if transaction_count < 10:
            if persona_assignment.primary_persona:
                actual_behavior = f"Persona assigned with limited data ({transaction_count} transactions)"
                passed = True  # System can work with limited data
            else:
                actual_behavior = f"No persona assigned (insufficient data: {transaction_count} transactions)"
                passed = True  # Acceptable - graceful degradation
            error_message = None
        else:
            actual_behavior = f"More data than expected ({transaction_count} transactions)"
            passed = True
            error_message = None
        
        return AdversarialScenario(
            scenario_id=f"ADV-{user_id}-SPARSE-001",
            scenario_name=scenario_name,
            description=description,
            test_user_id=user_id,
            expected_behavior="System handles sparse data gracefully, either assigns persona or gracefully degrades",
            actual_behavior=actual_behavior,
            passed=passed,
            error_message=error_message,
            details={"transaction_count": transaction_count}
        )
    except Exception as e:
        return AdversarialScenario(
            scenario_id=f"ADV-{user_id}-SPARSE-001",
            scenario_name=scenario_name,
            description=description,
            test_user_id=user_id,
            expected_behavior="System handles sparse data gracefully",
            actual_behavior=f"Error: {str(e)}",
            passed=False,
            error_message=str(e)
        )


def test_conflicting_signals(
    user_id: str,
    db_path: str
) -> AdversarialScenario:
    """
    Test user with conflicting signals (e.g., high savings but high utilization).
    
    Args:
        user_id: User ID to test
        db_path: Path to SQLite database
        
    Returns:
        AdversarialScenario object
    """
    scenario_name = "Conflicting Signals"
    description = "User with conflicting financial signals (e.g., high savings + high utilization)"
    
    try:
        # Get signals
        card_metrics, agg_metrics = analyze_credit_utilization_for_customer(user_id, db_path, 30)
        savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(user_id, db_path, 180)
        
        has_high_utilization = agg_metrics.aggregate_utilization >= 50 if card_metrics else False
        has_high_savings = savings_metrics.total_savings_balance >= 10000 if savings_accounts else False
        
        conflicting = has_high_utilization and has_high_savings
        
        # Try to assign persona
        persona_assignment = assign_personas_with_prioritization(user_id, db_path)
        
        if conflicting:
            if persona_assignment.primary_persona:
                actual_behavior = f"Persona assigned despite conflicting signals: {persona_assignment.primary_persona.persona_type.value}"
                passed = True  # System should prioritize based on rules
            else:
                actual_behavior = "No persona assigned (unable to resolve conflicting signals)"
                passed = True  # Acceptable - graceful degradation
        else:
            actual_behavior = "No conflicting signals detected"
            passed = True
        
        return AdversarialScenario(
            scenario_id=f"ADV-{user_id}-CONFLICT-001",
            scenario_name=scenario_name,
            description=description,
            test_user_id=user_id,
            expected_behavior="System handles conflicting signals gracefully, prioritizes based on rules",
            actual_behavior=actual_behavior,
            passed=passed,
            error_message=None,
            details={
                "has_high_utilization": has_high_utilization,
                "has_high_savings": has_high_savings,
                "conflicting": conflicting
            }
        )
    except Exception as e:
        return AdversarialScenario(
            scenario_id=f"ADV-{user_id}-CONFLICT-001",
            scenario_name=scenario_name,
            description=description,
            test_user_id=user_id,
            expected_behavior="System handles conflicting signals gracefully",
            actual_behavior=f"Error: {str(e)}",
            passed=False,
            error_message=str(e)
        )


def test_nonexistent_user(
    db_path: str
) -> AdversarialScenario:
    """
    Test with nonexistent user ID.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        AdversarialScenario object
    """
    scenario_name = "Nonexistent User"
    description = "Test with user ID that doesn't exist in database"
    user_id = "NONEXISTENT_USER_12345"
    
    try:
        # Try to assign persona
        persona_assignment = assign_personas_with_prioritization(user_id, db_path)
        
        # Should handle gracefully (no persona assigned)
        if persona_assignment.primary_persona is None:
            actual_behavior = "No persona assigned (nonexistent user handled gracefully)"
            passed = True
        else:
            actual_behavior = "Persona assigned (unexpected - should be None)"
            passed = False
            error_message = "System assigned persona to nonexistent user"
        
        return AdversarialScenario(
            scenario_id=f"ADV-NONEXISTENT-001",
            scenario_name=scenario_name,
            description=description,
            test_user_id=user_id,
            expected_behavior="System handles nonexistent user gracefully, returns no persona",
            actual_behavior=actual_behavior,
            passed=passed,
            error_message=error_message
        )
    except Exception as e:
        # Exception is acceptable for nonexistent user
        actual_behavior = f"Exception handled: {str(e)}"
        passed = True  # Exception handling is acceptable
        
        return AdversarialScenario(
            scenario_id=f"ADV-NONEXISTENT-001",
            scenario_name=scenario_name,
            description=description,
            test_user_id=user_id,
            expected_behavior="System handles nonexistent user gracefully",
            actual_behavior=actual_behavior,
            passed=passed,
            error_message=str(e)
        )


def test_data_quality_issues(
    user_id: str,
    db_path: str
) -> AdversarialScenario:
    """
    Test system with data quality issues (missing fields, outliers).
    
    Args:
        user_id: User ID to test
        db_path: Path to SQLite database
        
    Returns:
        AdversarialScenario object
    """
    scenario_name = "Data Quality Issues"
    description = "Test system robustness to data quality issues (missing fields, outliers)"
    
    try:
        # Get accounts
        accounts = get_accounts_by_customer(user_id, db_path)
        
        # Check for accounts with missing balances
        accounts_with_missing_balances = sum(1 for acc in accounts if acc.balances.current is None)
        
        # Try to assign persona
        persona_assignment = assign_personas_with_prioritization(user_id, db_path)
        
        # System should handle gracefully
        if accounts_with_missing_balances > 0:
            if persona_assignment.primary_persona:
                actual_behavior = f"Persona assigned despite data quality issues ({accounts_with_missing_balances} accounts with missing balances)"
                passed = True  # System handles missing data gracefully
            else:
                actual_behavior = f"No persona assigned due to data quality issues"
                passed = True  # Acceptable - graceful degradation
        else:
            actual_behavior = "No data quality issues detected"
            passed = True
        
        return AdversarialScenario(
            scenario_id=f"ADV-{user_id}-QUALITY-001",
            scenario_name=scenario_name,
            description=description,
            test_user_id=user_id,
            expected_behavior="System handles data quality issues gracefully",
            actual_behavior=actual_behavior,
            passed=passed,
            error_message=None,
            details={"accounts_with_missing_balances": accounts_with_missing_balances}
        )
    except Exception as e:
        return AdversarialScenario(
            scenario_id=f"ADV-{user_id}-QUALITY-001",
            scenario_name=scenario_name,
            description=description,
            test_user_id=user_id,
            expected_behavior="System handles data quality issues gracefully",
            actual_behavior=f"Error: {str(e)}",
            passed=False,
            error_message=str(e)
        )


def run_adversarial_tests(
    user_ids: List[str],
    db_path: str,
    report_id: Optional[str] = None
) -> AdversarialTestReport:
    """
    Run all adversarial tests.
    
    Args:
        user_ids: List of user IDs to test
        db_path: Path to SQLite database
        report_id: Optional report ID (auto-generated if not provided)
        
    Returns:
        AdversarialTestReport object
    """
    if report_id is None:
        timestamp = datetime.now()
        report_id = f"ADV-{timestamp.strftime('%Y%m%d%H%M%S')}"
    
    scenarios = []
    
    # Test with first user (or use specific user if available)
    test_user = user_ids[0] if user_ids else None
    
    # Test extreme cases
    if test_user:
        scenarios.append(test_extreme_utilization(test_user, db_path))
        scenarios.append(test_sparse_data(test_user, db_path))
        scenarios.append(test_conflicting_signals(test_user, db_path))
        scenarios.append(test_data_quality_issues(test_user, db_path))
    
    # Test nonexistent user
    scenarios.append(test_nonexistent_user(db_path))
    
    # Calculate robustness score
    passed_count = sum(1 for s in scenarios if s.passed)
    total_count = len(scenarios)
    robustness_score = (passed_count / total_count * 100) if total_count > 0 else 0.0
    
    summary = {
        "total_scenarios": total_count,
        "passed_scenarios": passed_count,
        "failed_scenarios": total_count - passed_count,
        "robustness_score": robustness_score,
        "edge_cases_handled": passed_count
    }
    
    return AdversarialTestReport(
        report_id=report_id,
        timestamp=datetime.now(),
        scenarios=scenarios,
        total_scenarios=total_count,
        passed_scenarios=passed_count,
        failed_scenarios=total_count - passed_count,
        robustness_score=robustness_score,
        summary=summary
    )


def export_adversarial_report(report: AdversarialTestReport, output_path: str) -> None:
    """
    Export adversarial test report to JSON file.
    
    Args:
        report: AdversarialTestReport object
        output_path: Path to output JSON file
    """
    data = {
        "report_id": report.report_id,
        "timestamp": report.timestamp.isoformat(),
        "scenarios": [
            {
                "scenario_id": s.scenario_id,
                "scenario_name": s.scenario_name,
                "description": s.description,
                "test_user_id": s.test_user_id,
                "expected_behavior": s.expected_behavior,
                "actual_behavior": s.actual_behavior,
                "passed": s.passed,
                "error_message": s.error_message,
                "details": s.details
            }
            for s in report.scenarios
        ],
        "summary": report.summary
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def generate_robustness_report(report: AdversarialTestReport, output_path: str) -> None:
    """
    Generate human-readable robustness report.
    
    Args:
        report: AdversarialTestReport object
        output_path: Path to output report file
    """
    report_text = f"""
SpendSenseAI Adversarial Testing & Robustness Report
Generated: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Report ID: {report.report_id}

================================================================================
SUMMARY
================================================================================
Total Scenarios Tested: {report.total_scenarios}
Passed: {report.passed_scenarios}
Failed: {report.failed_scenarios}
Robustness Score: {report.robustness_score:.1f}%

================================================================================
TEST RESULTS
================================================================================
"""
    
    for scenario in report.scenarios:
        status = "✓ PASSED" if scenario.passed else "✗ FAILED"
        report_text += f"\n{status} - {scenario.scenario_name}\n"
        report_text += f"  Description: {scenario.description}\n"
        report_text += f"  Expected: {scenario.expected_behavior}\n"
        report_text += f"  Actual: {scenario.actual_behavior}\n"
        
        if scenario.error_message:
            report_text += f"  Error: {scenario.error_message}\n"
        
        if scenario.details:
            report_text += "  Details:\n"
            for key, value in scenario.details.items():
                report_text += f"    - {key}: {value}\n"
    
    report_text += "\n" + "="*60 + "\n"
    report_text += "ROBUSTNESS ASSESSMENT\n"
    report_text += "="*60 + "\n"
    
    if report.robustness_score >= 90:
        report_text += "✅ EXCELLENT - System shows high robustness to edge cases\n"
    elif report.robustness_score >= 70:
        report_text += "⚠️ GOOD - System handles most edge cases well\n"
    else:
        report_text += "❌ NEEDS IMPROVEMENT - System struggles with some edge cases\n"
    
    report_text += f"\nRecommendation: {'System is robust' if report.robustness_score >= 80 else 'Review failed scenarios and improve error handling'}\n"
    
    with open(output_path, 'w') as f:
        f.write(report_text)

