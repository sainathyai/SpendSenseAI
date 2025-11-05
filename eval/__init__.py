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

from .adversarial_tests import (
    AdversarialTestResult,
    test_extreme_behaviors,
    test_sparse_data,
    test_conflicting_signals,
    test_missing_data,
    test_outliers,
    run_adversarial_tests,
    generate_adversarial_test_report
)

from .effectiveness_tracking import (
    EngagementMetrics,
    OutcomeMetrics,
    ContentPerformance,
    OfferPerformance,
    EffectivenessReport,
    track_engagement,
    track_outcome,
    calculate_content_performance,
    calculate_offer_roi,
    generate_effectiveness_report,
    generate_effectiveness_report_file
)

from .cohort_analysis import (
    CohortDefinition,
    CohortMetrics,
    create_income_cohorts,
    analyze_cohort_persona_distribution,
    calculate_cohort_average_metrics,
    analyze_cohort,
    analyze_all_cohorts,
    generate_cohort_report
)

from .bias_detection import (
    BiasMetric,
    BiasAnalysis,
    calculate_demographic_parity,
    calculate_disparate_impact,
    calculate_confidence_calibration,
    generate_bias_mitigation_recommendations,
    run_bias_analysis,
    generate_fairness_report
)

from .monitoring import (
    HealthCheck,
    PerformanceMetrics,
    DataQualityAlert,
    AnomalyAlert,
    SystemHealth,
    check_database_health,
    check_data_quality,
    detect_persona_distribution_anomaly,
    monitor_performance,
    check_system_health,
    generate_health_report
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
    'AdversarialTestResult',
    'test_extreme_behaviors',
    'test_sparse_data',
    'test_conflicting_signals',
    'test_missing_data',
    'test_outliers',
    'run_adversarial_tests',
    'generate_adversarial_test_report',
    
    # Effectiveness Tracking
    'EngagementMetrics',
    'OutcomeMetrics',
    'ContentPerformance',
    'OfferPerformance',
    'EffectivenessReport',
    'track_engagement',
    'track_outcome',
    'calculate_content_performance',
    'calculate_offer_roi',
    'generate_effectiveness_report',
    'generate_effectiveness_report_file',
    
    # Cohort Analysis
    'CohortDefinition',
    'CohortMetrics',
    'create_income_cohorts',
    'analyze_cohort_persona_distribution',
    'calculate_cohort_average_metrics',
    'analyze_cohort',
    'analyze_all_cohorts',
    'generate_cohort_report',
    
    # Bias Detection
    'BiasMetric',
    'BiasAnalysis',
    'calculate_demographic_parity',
    'calculate_disparate_impact',
    'calculate_confidence_calibration',
    'generate_bias_mitigation_recommendations',
    'run_bias_analysis',
    'generate_fairness_report',
    
    # Monitoring
    'HealthCheck',
    'PerformanceMetrics',
    'DataQualityAlert',
    'AnomalyAlert',
    'SystemHealth',
    'check_database_health',
    'check_data_quality',
    'detect_persona_distribution_anomaly',
    'monitor_performance',
    'check_system_health',
    'generate_health_report'
]
