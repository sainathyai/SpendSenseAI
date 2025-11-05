"""
Run evaluation metrics for SpendSenseAI.

Usage:
    python -m scripts.run_evaluation [user_ids...]
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

from eval.metrics import (
    run_evaluation, export_metrics_json, export_metrics_csv,
    generate_summary_report
)
from ingest.queries import get_accounts_by_customer


def get_all_user_ids(db_path: str) -> list:
    """Get all user IDs from database."""
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT customer_id FROM accounts")
    user_ids = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    return user_ids


def main():
    """Main evaluation function."""
    parser = argparse.ArgumentParser(description="Run SpendSenseAI evaluation metrics")
    parser.add_argument("--db-path", default="data/spendsense.db", help="Path to SQLite database")
    parser.add_argument("--output-dir", default="data/evaluation", help="Output directory for results")
    parser.add_argument("--user-ids", nargs="*", help="Specific user IDs to evaluate (if not provided, evaluates all users)")
    parser.add_argument("--format", choices=["all", "json", "csv", "report"], default="all", help="Output format")
    
    args = parser.parse_args()
    
    # Get user IDs
    if args.user_ids:
        user_ids = args.user_ids
    else:
        print("Getting all user IDs from database...")
        user_ids = get_all_user_ids(args.db_path)
        print(f"Found {len(user_ids)} users")
    
    if not user_ids:
        print("No users found to evaluate!")
        return
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run evaluation
    print(f"Running evaluation for {len(user_ids)} users...")
    print("This may take a few minutes...")
    
    results = run_evaluation(user_ids, args.db_path)
    
    print(f"Evaluation complete! ID: {results.evaluation_id}")
    
    # Export results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if args.format in ["all", "json"]:
        json_path = output_dir / f"evaluation_{timestamp}.json"
        export_metrics_json(results, str(json_path))
        print(f"Exported JSON: {json_path}")
    
    if args.format in ["all", "csv"]:
        csv_path = output_dir / f"evaluation_{timestamp}.csv"
        export_metrics_csv(results, str(csv_path))
        print(f"Exported CSV: {csv_path}")
    
    if args.format in ["all", "report"]:
        report_path = output_dir / f"evaluation_report_{timestamp}.txt"
        generate_summary_report(results, str(report_path))
        print(f"Generated report: {report_path}")
        
        # Also print summary to console
        print("\n" + "="*60)
        print("EVALUATION SUMMARY")
        print("="*60)
        print(f"Coverage - Persona Assignment Rate: {results.coverage_metrics.persona_assignment_rate:.2f}%")
        print(f"Coverage - Average Behaviors Per User: {results.coverage_metrics.average_behaviors_per_user:.2f}")
        print(f"Explainability - Rationale Coverage: {results.explainability_metrics.rationale_coverage_rate:.2f}%")
        print(f"Explainability - Trace Completeness: {results.explainability_metrics.trace_completeness_rate:.2f}%")
        print(f"Performance - Average Latency: {results.performance_metrics.average_latency_per_user:.2f}s")
        print("="*60)


if __name__ == "__main__":
    main()

