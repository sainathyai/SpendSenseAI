"""
Test adversarial testing system.

Usage:
    python -m scripts.test_adversarial
"""

from eval.adversarial_testing import (
    run_adversarial_tests,
    export_adversarial_report,
    generate_robustness_report
)
from scripts.run_evaluation import get_all_user_ids
from pathlib import Path
from datetime import datetime

db_path = 'data/spendsense.db'
output_dir = Path('data/evaluation')

print("="*60)
print("Testing Adversarial Testing System")
print("="*60)
print()

# Get all user IDs
user_ids = get_all_user_ids(db_path)
print(f"Found {len(user_ids)} users")

print()
print("Running adversarial tests...")
print("Testing edge cases and robustness...")
print()

# Run adversarial tests
report = run_adversarial_tests(user_ids, db_path)

print(f"Adversarial Test Report ID: {report.report_id}")
print(f"Total Scenarios Tested: {report.total_scenarios}")
print(f"Passed: {report.passed_scenarios}")
print(f"Failed: {report.failed_scenarios}")
print(f"Robustness Score: {report.robustness_score:.1f}%")
print()

# Display test results
print("="*60)
print("Test Results")
print("="*60)
for scenario in report.scenarios:
    status = "✓ PASSED" if scenario.passed else "✗ FAILED"
    print(f"\n{status} - {scenario.scenario_name}")
    print(f"  {scenario.actual_behavior}")
    if scenario.error_message:
        print(f"  Error: {scenario.error_message}")

print()

# Export reports
output_dir.mkdir(parents=True, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

json_path = output_dir / f"adversarial_report_{timestamp}.json"
export_adversarial_report(report, str(json_path))
print(f"Exported JSON: {json_path}")

report_path = output_dir / f"robustness_report_{timestamp}.txt"
generate_robustness_report(report, str(report_path))
print(f"Generated robustness report: {report_path}")

print("\n" + "="*60)
print("[SUCCESS] Adversarial testing completed!")
print("="*60)

