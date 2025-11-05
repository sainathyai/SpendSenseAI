"""
Evaluation Module for SpendSenseAI.

Provides:
- Metrics & Evaluation Harness
- Integration Testing & End-to-End Validation
"""

from .metrics import (
    CoverageMetrics,
    ExplainabilityMetrics,
    PerformanceMetrics,
    FairnessMetrics,
    EvaluationResults,
    run_evaluation,
    evaluate_coverage,
    evaluate_explainability,
    evaluate_performance,
    evaluate_fairness,
    export_metrics_json,
    export_metrics_csv,
    generate_summary_report
)

__all__ = [
    'CoverageMetrics',
    'ExplainabilityMetrics',
    'PerformanceMetrics',
    'FairnessMetrics',
    'EvaluationResults',
    'run_evaluation',
    'evaluate_coverage',
    'evaluate_explainability',
    'evaluate_performance',
    'evaluate_fairness',
    'export_metrics_json',
    'export_metrics_csv',
    'generate_summary_report'
]
