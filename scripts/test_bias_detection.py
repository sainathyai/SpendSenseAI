"""
Test bias detection system.

Usage:
    python -m scripts.test_bias_detection
"""

from guardrails.bias_detection import (
    DemographicGroup, run_bias_detection,
    export_bias_report, generate_fairness_audit_report
)
from scripts.run_evaluation import get_all_user_ids
from pathlib import Path
from datetime import datetime

db_path = 'data/spendsense.db'
output_dir = Path('data/evaluation')

print("="*60)
print("Testing Bias Detection System")
print("="*60)
print()

# Get all user IDs
user_ids = get_all_user_ids(db_path)
print(f"Found {len(user_ids)} users")

# Create demographic groups (simplified - in production would use actual demographics)
# For demo, split users into two groups
midpoint = len(user_ids) // 2
group1 = DemographicGroup(
    group_name="Group A",
    user_ids=user_ids[:midpoint],
    metadata={"description": "First half of users"}
)
group2 = DemographicGroup(
    group_name="Group B",
    user_ids=user_ids[midpoint:],
    metadata={"description": "Second half of users"}
)

groups = [group1, group2]

print(f"Created {len(groups)} demographic groups")
print()

# Run bias detection
print("Running bias detection analysis...")
print("This may take a few minutes...")
print()

report = run_bias_detection(groups, db_path)

print(f"Bias Detection Report ID: {report.report_id}")
print(f"Total Groups: {report.summary.get('total_groups', 0)}")
print(f"Groups with Issues: {report.summary.get('groups_with_issues', 0)}")
print(f"Disparate Impact Cases: {report.summary.get('disparate_impact_count', 0)}")
print(f"Calibration Issues: {report.summary.get('calibration_issues_count', 0)}")
print()

# Export reports
output_dir.mkdir(parents=True, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

json_path = output_dir / f"bias_report_{timestamp}.json"
export_bias_report(report, str(json_path))
print(f"Exported JSON: {json_path}")

report_path = output_dir / f"bias_audit_report_{timestamp}.txt"
generate_fairness_audit_report(report, str(report_path))
print(f"Generated audit report: {report_path}")

print()
print("="*60)
print("Bias Detection Recommendations")
print("="*60)
for i, rec in enumerate(report.bias_mitigation_recommendations, 1):
    print(f"{i}. {rec}")

print("\n" + "="*60)
print("[SUCCESS] Bias detection test completed!")
print("="*60)

