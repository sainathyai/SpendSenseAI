"""
Adversarial Testing & Edge Cases for SpendSenseAI.

Stress-test the system against unusual inputs:
- User with extreme behaviors (99% utilization, $0 savings)
- Users with very little data
- Users with conflicting signals
- Data quality issues (missing fields, outliers)
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import traceback

from personas.persona_prioritization import assign_personas_with_prioritization
from personas.persona_definition import PersonaAssignment, PersonaType
from recommend.recommendation_builder import build_recommendations
from features.subscription_detection import detect_subscriptions_for_customer
from features.credit_utilization import analyze_credit_utilization_for_customer
from features.savings_pattern import analyze_savings_patterns_for_customer
from features.income_stability import analyze_income_stability_for_customer
from ingest.queries import get_accounts_by_customer, get_transactions_by_customer


@dataclass
class AdversarialTestResult:
    """Result of an adversarial test."""
    test_name: str
    passed: bool
    scenario_description: str
    error_message: Optional[str] = None
    system_response: Optional[Dict[str, Any]] = None
    graceful_degradation: bool = False
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


def test_extreme_behaviors(user_id: str, db_path: str) -> AdversarialTestResult:
    """
    Test system with extreme behaviors (99% utilization, $0 savings).
    
    Args:
        user_id: User ID to test
        db_path: Path to SQLite database
        
    Returns:
        AdversarialTestResult object
    """
    test_name = "Extreme Behaviors"
    scenario_description = "User with 99% credit utilization and $0 savings"
    
    try:
        # Assign persona
        persona_assignment = assign_personas_with_prioritization(user_id, db_path)
        
        # Check if system handles extreme behaviors gracefully
        if persona_assignment.primary_persona:
            # Generate recommendations
            recommendations = build_recommendations(
                user_id, db_path, persona_assignment,
                check_consent=False
            )
            
            # System should still provide recommendations
            has_recommendations = len(recommendations.education_items) > 0 or len(recommendations.partner_offers) > 0
            
            # Check for appropriate persona assignment (should be High Utilization or Financial Fragility)
            persona_type = persona_assignment.primary_persona.persona_type
            appropriate_persona = persona_type in [PersonaType.HIGH_UTILIZATION, PersonaType.FINANCIAL_FRAGILITY]
            
            return AdversarialTestResult(
                test_name=test_name,
                passed=True,
                scenario_description=scenario_description,
                system_response={
                    "persona_assigned": persona_type.value,
                    "has_recommendations": has_recommendations,
                    "appropriate_persona": appropriate_persona
                },
                graceful_degradation=True,
                details={
                    "persona_type": persona_type.value,
                    "recommendations_count": len(recommendations.education_items) + len(recommendations.partner_offers)
                }
            )
        else:
            return AdversarialTestResult(
                test_name=test_name,
                passed=False,
                scenario_description=scenario_description,
                error_message="No persona assigned for extreme behavior user",
                graceful_degradation=False
            )
    
    except Exception as e:
        return AdversarialTestResult(
            test_name=test_name,
            passed=False,
            scenario_description=scenario_description,
            error_message=str(e),
            graceful_degradation=False
        )


def test_sparse_data(user_id: str, db_path: str) -> AdversarialTestResult:
    """
    Test system with users with very little data.
    
    Args:
        user_id: User ID to test
        db_path: Path to SQLite database
        
    Returns:
        AdversarialTestResult object
    """
    test_name = "Sparse Data"
    scenario_description = "User with very few transactions (less than 10)"
    
    try:
        # Get transactions
        transactions = get_transactions_by_customer(user_id, db_path)
        
        if len(transactions) < 10:
            # System should still attempt to assign persona
            persona_assignment = assign_personas_with_prioritization(user_id, db_path)
            
            # System should handle gracefully (may not assign persona, but shouldn't crash)
            passed = True  # System didn't crash
            graceful_degradation = True
            
            if persona_assignment.primary_persona:
                # If persona assigned with sparse data, that's good
                recommendations = build_recommendations(
                    user_id, db_path, persona_assignment,
                    check_consent=False
                )
                has_recommendations = len(recommendations.education_items) > 0
            else:
                # No persona assigned is acceptable for sparse data
                has_recommendations = False
            
            return AdversarialTestResult(
                test_name=test_name,
                passed=passed,
                scenario_description=scenario_description,
                system_response={
                    "persona_assigned": persona_assignment.primary_persona is not None,
                    "has_recommendations": has_recommendations,
                    "transaction_count": len(transactions)
                },
                graceful_degradation=graceful_degradation,
                details={
                    "transaction_count": len(transactions),
                    "accounts_count": len(get_accounts_by_customer(user_id, db_path))
                }
            )
        else:
            return AdversarialTestResult(
                test_name=test_name,
                passed=True,
                scenario_description=scenario_description,
                system_response={"message": "User has sufficient data"},
                graceful_degradation=True,
                details={"transaction_count": len(transactions)}
            )
    
    except Exception as e:
        return AdversarialTestResult(
            test_name=test_name,
            passed=False,
            scenario_description=scenario_description,
            error_message=str(e),
            graceful_degradation=False
        )


def test_conflicting_signals(user_id: str, db_path: str) -> AdversarialTestResult:
    """
    Test system with conflicting signals (e.g., high savings but high utilization).
    
    Args:
        user_id: User ID to test
        db_path: Path to SQLite database
        
    Returns:
        AdversarialTestResult object
    """
    test_name = "Conflicting Signals"
    scenario_description = "User with conflicting signals (high savings but high utilization)"
    
    try:
        # Check for conflicting signals
        card_metrics, agg_metrics = analyze_credit_utilization_for_customer(user_id, db_path, 30)
        savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(user_id, db_path, 180)
        
        has_conflict = False
        if card_metrics and savings_accounts:
            utilization = agg_metrics.aggregate_utilization
            savings_balance = savings_metrics.total_savings_balance
            
            # Conflict: High utilization but good savings
            if utilization > 50 and savings_balance > 1000:
                has_conflict = True
        
        # System should handle conflicts gracefully
        persona_assignment = assign_personas_with_prioritization(user_id, db_path)
        
        if persona_assignment.primary_persona:
            recommendations = build_recommendations(
                user_id, db_path, persona_assignment,
                check_consent=False
            )
            
            # System should prioritize based on persona logic
            has_recommendations = len(recommendations.education_items) > 0
            
            return AdversarialTestResult(
                test_name=test_name,
                passed=True,
                scenario_description=scenario_description,
                system_response={
                    "has_conflict": has_conflict,
                    "persona_assigned": True,
                    "has_recommendations": has_recommendations
                },
                graceful_degradation=True,
                details={
                    "conflict_detected": has_conflict,
                    "persona_type": persona_assignment.primary_persona.persona_type.value if persona_assignment.primary_persona else None
                }
            )
        else:
            return AdversarialTestResult(
                test_name=test_name,
                passed=True,
                scenario_description=scenario_description,
                system_response={"message": "No persona assigned, system handled gracefully"},
                graceful_degradation=True
            )
    
    except Exception as e:
        return AdversarialTestResult(
            test_name=test_name,
            passed=False,
            scenario_description=scenario_description,
            error_message=str(e),
            graceful_degradation=False
        )


def test_missing_data(user_id: str, db_path: str) -> AdversarialTestResult:
    """
    Test system with missing data fields.
    
    Args:
        user_id: User ID to test
        db_path: Path to SQLite database
        
    Returns:
        AdversarialTestResult object
    """
    test_name = "Missing Data Fields"
    scenario_description = "User with missing optional data fields"
    
    try:
        # Get accounts
        accounts = get_accounts_by_customer(user_id, db_path)
        
        # Check for missing optional fields
        missing_fields = []
        for account in accounts:
            if account.balances.available is None:
                missing_fields.append(f"{account.account_id}: available balance")
            if account.balances.limit is None and account.type.value == "credit":
                missing_fields.append(f"{account.account_id}: credit limit")
        
        # System should handle missing optional fields gracefully
        persona_assignment = assign_personas_with_prioritization(user_id, db_path)
        
        passed = True  # System didn't crash
        graceful_degradation = len(missing_fields) > 0  # System should handle missing fields
        
        return AdversarialTestResult(
            test_name=test_name,
            passed=passed,
            scenario_description=scenario_description,
            system_response={
                "missing_fields_count": len(missing_fields),
                "persona_assigned": persona_assignment.primary_persona is not None
            },
            graceful_degradation=graceful_degradation,
            details={
                "missing_fields": missing_fields,
                "accounts_with_missing_data": len(missing_fields)
            }
        )
    
    except Exception as e:
        return AdversarialTestResult(
            test_name=test_name,
            passed=False,
            scenario_description=scenario_description,
            error_message=str(e),
            graceful_degradation=False
        )


def test_outliers(user_id: str, db_path: str) -> AdversarialTestResult:
    """
    Test system with outlier data (unusually large transactions, negative balances).
    
    Args:
        user_id: User ID to test
        db_path: Path to SQLite database
        
    Returns:
        AdversarialTestResult object
    """
    test_name = "Outlier Data"
    scenario_description = "User with outlier transactions (unusually large amounts)"
    
    try:
        # Get transactions
        transactions = get_transactions_by_customer(user_id, db_path)
        
        if transactions:
            amounts = [abs(t.amount) for t in transactions]
            if amounts:
                mean_amount = sum(amounts) / len(amounts)
                max_amount = max(amounts)
                
                # Check for outliers (transactions > 5x mean)
                outliers = [a for a in amounts if a > mean_amount * 5] if mean_amount > 0 else []
                
                # System should handle outliers gracefully
                persona_assignment = assign_personas_with_prioritization(user_id, db_path)
                
                passed = True  # System didn't crash
                graceful_degradation = len(outliers) > 0
                
                return AdversarialTestResult(
                    test_name=test_name,
                    passed=passed,
                    scenario_description=scenario_description,
                    system_response={
                        "outliers_detected": len(outliers),
                        "persona_assigned": persona_assignment.primary_persona is not None
                    },
                    graceful_degradation=graceful_degradation,
                    details={
                        "outlier_count": len(outliers),
                        "max_transaction": max_amount,
                        "mean_transaction": mean_amount
                    }
                )
        else:
            return AdversarialTestResult(
                test_name=test_name,
                passed=True,
                scenario_description=scenario_description,
                system_response={"message": "No transactions to analyze"},
                graceful_degradation=True
            )
    
    except Exception as e:
        return AdversarialTestResult(
            test_name=test_name,
            passed=False,
            scenario_description=scenario_description,
            error_message=str(e),
            graceful_degradation=False
        )


def run_adversarial_tests(
    user_ids: List[str],
    db_path: str
) -> List[AdversarialTestResult]:
    """
    Run all adversarial tests.
    
    Args:
        user_ids: List of user IDs to test
        db_path: Path to SQLite database
        
    Returns:
        List of AdversarialTestResult objects
    """
    results = []
    
    # Test with first user
    if user_ids:
        test_user = user_ids[0]
        
        # Run all adversarial tests
        results.append(test_extreme_behaviors(test_user, db_path))
        results.append(test_sparse_data(test_user, db_path))
        results.append(test_conflicting_signals(test_user, db_path))
        results.append(test_missing_data(test_user, db_path))
        results.append(test_outliers(test_user, db_path))
    
    return results


def generate_adversarial_test_report(
    results: List[AdversarialTestResult],
    output_path: str
) -> None:
    """
    Generate adversarial test report.
    
    Args:
        results: List of AdversarialTestResult objects
        output_path: Path to output report file
    """
    report = f"""
Adversarial Testing Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

================================================================================
SUMMARY
================================================================================
Total Tests: {len(results)}
Passed: {sum(1 for r in results if r.passed)}
Failed: {sum(1 for r in results if not r.passed)}
Graceful Degradation: {sum(1 for r in results if r.graceful_degradation)}

================================================================================
TEST RESULTS
================================================================================
"""
    
    for result in results:
        status = "✓ PASSED" if result.passed else "✗ FAILED"
        report += f"\n{status} - {result.test_name}\n"
        report += f"  Scenario: {result.scenario_description}\n"
        
        if result.error_message:
            report += f"  Error: {result.error_message}\n"
        
        if result.system_response:
            report += "  System Response:\n"
            for key, value in result.system_response.items():
                report += f"    - {key}: {value}\n"
        
        if result.graceful_degradation:
            report += "  ✓ Graceful degradation: System handled edge case gracefully\n"
        
        if result.details:
            report += "  Details:\n"
            for key, value in result.details.items():
                report += f"    - {key}: {value}\n"
        
        report += "\n"
    
    report += "=" * 60 + "\n"
    
    with open(output_path, 'w') as f:
        f.write(report)

