"""
Run integration tests for SpendSenseAI.

Usage:
    python -m scripts.run_integration_tests
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

from eval.integration_tests import run_integration_tests, generate_test_report
from scripts.run_evaluation import get_all_user_ids


def main():
    """Main integration test function."""
    parser = argparse.ArgumentParser(description="Run SpendSenseAI integration tests")
    parser.add_argument("--db-path", default="data/spendsense.db", help="Path to SQLite database")
    parser.add_argument("--output-dir", default="data/evaluation", help="Output directory for results")
    parser.add_argument("--user-ids", nargs="*", help="Specific user IDs to test (if not provided, uses all users)")
    
    args = parser.parse_args()
    
    # Get user IDs
    if args.user_ids:
        user_ids = args.user_ids
    else:
        print("Getting all user IDs from database...")
        user_ids = get_all_user_ids(args.db_path)
        print(f"Found {len(user_ids)} users")
    
    if not user_ids:
        print("No users found to test!")
        return
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run integration tests
    print("Running integration tests...")
    print("This may take a few minutes...")
    
    report = run_integration_tests(user_ids, args.db_path)
    
    print(f"\nTest Report ID: {report.report_id}")
    print(f"Total Tests: {report.total_tests}")
    print(f"Passed: {report.passed_tests}")
    print(f"Failed: {report.failed_tests}")
    print(f"Pass Rate: {report.summary.get('pass_rate', 0):.1f}%")
    print(f"Total Duration: {report.total_duration:.2f}s")
    
    # Generate report file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"integration_test_report_{timestamp}.txt"
    generate_test_report(report, str(report_path))
    print(f"\nGenerated report: {report_path}")
    
    # Print test results
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    for result in report.results:
        status = "✓ PASSED" if result.passed else "✗ FAILED"
        print(f"{status} - {result.test_name} ({result.duration:.2f}s)")
        if result.error:
            print(f"  Error: {result.error}")
    print("="*60)


if __name__ == "__main__":
    main()

