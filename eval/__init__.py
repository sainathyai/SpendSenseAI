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

from .integration_tests import (
    TestResult,
    TestReport,
    run_integration_tests,
    generate_test_report
)

from .adversarial_testing import (
    AdversarialScenario,
    AdversarialTestReport,
    test_extreme_utilization,
    test_sparse_data,
    test_conflicting_signals,
    test_nonexistent_user,
    test_data_quality_issues,
    run_adversarial_tests,
    export_adversarial_report,
    generate_robustness_report
)

from .effectiveness_tracking import (
    EngagementType,
    OutcomeType,
    EngagementEvent,
    OutcomeMeasurement,
    ContentPerformance,
    OfferPerformance,
    EffectivenessReport,
    measure_utilization_outcome,
    measure_savings_outcome,
    calculate_content_performance,
    calculate_offer_performance,
    track_engagement,
    generate_effectiveness_report
)

__all__ = [
    # Metrics
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
    'generate_summary_report',
    
    # Integration Tests
    'TestResult',
    'TestReport',
    'run_integration_tests',
    'generate_test_report',
    
    # Adversarial Testing
    'AdversarialScenario',
    'AdversarialTestReport',
    'test_extreme_utilization',
    'test_sparse_data',
    'test_conflicting_signals',
    'test_nonexistent_user',
    'test_data_quality_issues',
    'run_adversarial_tests',
    'export_adversarial_report',
    'generate_robustness_report'
]
