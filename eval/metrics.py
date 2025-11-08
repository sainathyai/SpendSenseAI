"""
Metrics & Evaluation Harness for SpendSenseAI.

Measures system performance against success criteria:
- Coverage metrics (persona assignment rate, behaviors detected)
- Explainability metrics (recommendations with rationales, decision trace completeness)
- Performance metrics (latency, throughput)
- Fairness analysis (persona distribution, offer distribution)
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import csv
from pathlib import Path
import time

from personas.persona_prioritization import assign_personas_with_prioritization
from personas.persona_definition import PersonaAssignment, PersonaType
from recommend.recommendation_builder import build_recommendations
from guardrails.decision_trace import get_decision_traces_for_user, get_decision_trace
from features.subscription_detection import detect_subscriptions_for_customer
from features.credit_utilization import analyze_credit_utilization_for_customer
from features.savings_pattern import analyze_savings_patterns_for_customer
from features.income_stability import analyze_income_stability_for_customer
from ingest.queries import get_accounts_by_customer, get_transactions_by_customer


@dataclass
class CoverageMetrics:
    """Coverage metrics."""
    total_users: int = 0
    users_with_persona: int = 0
    persona_assignment_rate: float = 0.0  # Target: 100%
    users_with_signals: int = 0
    average_behaviors_per_user: float = 0.0  # Target: ≥3
    users_with_recommendations: int = 0
    recommendation_coverage_rate: float = 0.0


@dataclass
class ExplainabilityMetrics:
    """Explainability metrics."""
    total_recommendations: int = 0
    recommendations_with_rationales: int = 0
    rationale_coverage_rate: float = 0.0  # Target: 100%
    total_traces: int = 0
    traces_with_complete_data: int = 0
    trace_completeness_rate: float = 0.0  # Target: 100%
    recommendations_with_data_citations: int = 0
    data_citation_coverage_rate: float = 0.0


@dataclass
class PerformanceMetrics:
    """Performance metrics."""
    total_users_processed: int = 0
    total_processing_time: float = 0.0
    average_latency_per_user: float = 0.0  # Target: <5 seconds
    batch_processing_throughput: float = 0.0  # users per second
    persona_assignment_time: float = 0.0
    recommendation_generation_time: float = 0.0
    signal_detection_time: float = 0.0


@dataclass
class FairnessMetrics:
    """Fairness analysis metrics."""
    persona_distribution: Dict[str, int] = None
    persona_percentages: Dict[str, float] = None
    offer_distribution: Dict[str, int] = None
    offer_percentages: Dict[str, float] = None
    
    def __post_init__(self):
        if self.persona_distribution is None:
            self.persona_distribution = {}
        if self.persona_percentages is None:
            self.persona_percentages = {}
        if self.offer_distribution is None:
            self.offer_distribution = {}
        if self.offer_percentages is None:
            self.offer_percentages = {}


@dataclass
class EvaluationResults:
    """Complete evaluation results."""
    evaluation_id: str
    timestamp: datetime
    coverage_metrics: CoverageMetrics
    explainability_metrics: ExplainabilityMetrics
    performance_metrics: PerformanceMetrics
    fairness_metrics: FairnessMetrics
    summary: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.summary is None:
            self.summary = {}


def evaluate_coverage(
    user_ids: List[str],
    db_path: str
) -> CoverageMetrics:
    """
    Evaluate coverage metrics.
    
    Args:
        user_ids: List of user IDs to evaluate
        db_path: Path to SQLite database
        
    Returns:
        CoverageMetrics object
    """
    total_users = len(user_ids)
    users_with_persona = 0
    users_with_signals = 0
    total_behaviors = 0
    users_with_recommendations = 0
    
    for user_id in user_ids:
        # Check persona assignment
        try:
            persona_assignment = assign_personas_with_prioritization(user_id, db_path)
            if persona_assignment.primary_persona:
                users_with_persona += 1
        except Exception:
            pass
        
        # Check signals detected
        behavior_count = 0
        try:
            # Subscription signals
            subscriptions, sub_metrics = detect_subscriptions_for_customer(user_id, db_path, window_days=90)
            if sub_metrics.get('subscription_count', 0) > 0:
                behavior_count += 1
            
            # Credit utilization signals
            card_metrics, agg_metrics = analyze_credit_utilization_for_customer(user_id, db_path, 30)
            if card_metrics:
                behavior_count += 1
            
            # Savings signals
            savings_accounts, savings_metrics = analyze_savings_patterns_for_customer(user_id, db_path, 180)
            if savings_accounts:
                behavior_count += 1
            
            # Income signals (always present if we have transactions)
            accounts = get_accounts_by_customer(user_id, db_path)
            if accounts:
                behavior_count += 1
            
            if behavior_count > 0:
                users_with_signals += 1
                total_behaviors += behavior_count
        except Exception:
            pass
        
        # Check recommendations
        try:
            if persona_assignment.primary_persona:
                recommendations = build_recommendations(
                    user_id, db_path, persona_assignment,
                    check_consent=False
                )
                if recommendations.education_items or recommendations.partner_offers:
                    users_with_recommendations += 1
        except Exception:
            pass
    
    persona_assignment_rate = (users_with_persona / total_users * 100) if total_users > 0 else 0.0
    average_behaviors_per_user = (total_behaviors / total_users) if total_users > 0 else 0.0
    recommendation_coverage_rate = (users_with_recommendations / total_users * 100) if total_users > 0 else 0.0
    
    return CoverageMetrics(
        total_users=total_users,
        users_with_persona=users_with_persona,
        persona_assignment_rate=persona_assignment_rate,
        users_with_signals=users_with_signals,
        average_behaviors_per_user=average_behaviors_per_user,
        users_with_recommendations=users_with_recommendations,
        recommendation_coverage_rate=recommendation_coverage_rate
    )


def evaluate_explainability(
    user_ids: List[str],
    db_path: str
) -> ExplainabilityMetrics:
    """
    Evaluate explainability metrics.
    
    Args:
        user_ids: List of user IDs to evaluate
        db_path: Path to SQLite database
        
    Returns:
        ExplainabilityMetrics object
    """
    total_recommendations = 0
    recommendations_with_rationales = 0
    recommendations_with_data_citations = 0
    total_traces = 0
    traces_with_complete_data = 0
    
    for user_id in user_ids:
        try:
            persona_assignment = assign_personas_with_prioritization(user_id, db_path)
            
            if persona_assignment.primary_persona:
                recommendations = build_recommendations(
                    user_id, db_path, persona_assignment,
                    check_consent=False
                )
                
                # Check recommendations
                for item in recommendations.education_items + recommendations.partner_offers:
                    total_recommendations += 1
                    
                    if item.rationale and len(item.rationale) > 0:
                        recommendations_with_rationales += 1
                    
                    if item.data_citations and len(item.data_citations) > 0:
                        recommendations_with_data_citations += 1
                
                # Check traces
                traces = get_decision_traces_for_user(user_id, db_path)
                total_traces += len(traces)
                
                for trace in traces:
                    # Check if trace has complete data
                    if (trace.get('signals') and trace.get('persona_assignment') and 
                        trace.get('recommendations')):
                        traces_with_complete_data += 1
        except Exception:
            pass
    
    rationale_coverage_rate = (recommendations_with_rationales / total_recommendations * 100) if total_recommendations > 0 else 0.0
    trace_completeness_rate = (traces_with_complete_data / total_traces * 100) if total_traces > 0 else 0.0
    data_citation_coverage_rate = (recommendations_with_data_citations / total_recommendations * 100) if total_recommendations > 0 else 0.0
    
    return ExplainabilityMetrics(
        total_recommendations=total_recommendations,
        recommendations_with_rationales=recommendations_with_rationales,
        rationale_coverage_rate=rationale_coverage_rate,
        total_traces=total_traces,
        traces_with_complete_data=traces_with_complete_data,
        trace_completeness_rate=trace_completeness_rate,
        recommendations_with_data_citations=recommendations_with_data_citations,
        data_citation_coverage_rate=data_citation_coverage_rate
    )


def evaluate_performance(
    user_ids: List[str],
    db_path: str
) -> PerformanceMetrics:
    """
    Evaluate performance metrics.
    
    Args:
        user_ids: List of user IDs to evaluate
        db_path: Path to SQLite database
        
    Returns:
        PerformanceMetrics object
    """
    total_users = len(user_ids)
    total_processing_time = 0.0
    persona_assignment_time = 0.0
    recommendation_generation_time = 0.0
    signal_detection_time = 0.0
    
    for user_id in user_ids:
        try:
            # Time persona assignment
            start_time = time.time()
            persona_assignment = assign_personas_with_prioritization(user_id, db_path)
            persona_time = time.time() - start_time
            persona_assignment_time += persona_time
            
            # Time signal detection
            start_time = time.time()
            detect_subscriptions_for_customer(user_id, db_path, window_days=90)
            analyze_credit_utilization_for_customer(user_id, db_path, 30)
            analyze_savings_patterns_for_customer(user_id, db_path, 180)
            analyze_income_stability_for_customer(user_id, db_path, 180)
            signal_time = time.time() - start_time
            signal_detection_time += signal_time
            
            # Time recommendation generation
            if persona_assignment.primary_persona:
                start_time = time.time()
                build_recommendations(user_id, db_path, persona_assignment, check_consent=False)
                rec_time = time.time() - start_time
                recommendation_generation_time += rec_time
                
                total_processing_time += persona_time + signal_time + rec_time
            else:
                total_processing_time += persona_time + signal_time
        except Exception:
            pass
    
    average_latency_per_user = (total_processing_time / total_users) if total_users > 0 else 0.0
    batch_processing_throughput = (total_users / total_processing_time) if total_processing_time > 0 else 0.0
    
    return PerformanceMetrics(
        total_users_processed=total_users,
        total_processing_time=total_processing_time,
        average_latency_per_user=average_latency_per_user,
        batch_processing_throughput=batch_processing_throughput,
        persona_assignment_time=persona_assignment_time,
        recommendation_generation_time=recommendation_generation_time,
        signal_detection_time=signal_detection_time
    )


def evaluate_fairness(
    user_ids: List[str],
    db_path: str
) -> FairnessMetrics:
    """
    Evaluate fairness metrics.
    
    Args:
        user_ids: List of user IDs to evaluate
        db_path: Path to SQLite database
        
    Returns:
        FairnessMetrics object
    """
    persona_distribution = {}
    offer_distribution = {}
    total_personas = 0
    total_offers = 0
    
    for user_id in user_ids:
        try:
            persona_assignment = assign_personas_with_prioritization(user_id, db_path)
            
            if persona_assignment.primary_persona:
                persona_type = persona_assignment.primary_persona.persona_type.value
                persona_distribution[persona_type] = persona_distribution.get(persona_type, 0) + 1
                total_personas += 1
                
                recommendations = build_recommendations(
                    user_id, db_path, persona_assignment,
                    check_consent=False
                )
                
                for offer in recommendations.partner_offers:
                    offer_type = offer.offer_id.split('-')[1] if '-' in offer.offer_id else 'unknown'
                    offer_distribution[offer_type] = offer_distribution.get(offer_type, 0) + 1
                    total_offers += 1
        except Exception:
            pass
    
    # Calculate percentages
    persona_percentages = {
        persona: (count / total_personas * 100) if total_personas > 0 else 0.0
        for persona, count in persona_distribution.items()
    }
    
    offer_percentages = {
        offer_type: (count / total_offers * 100) if total_offers > 0 else 0.0
        for offer_type, count in offer_distribution.items()
    }
    
    return FairnessMetrics(
        persona_distribution=persona_distribution,
        persona_percentages=persona_percentages,
        offer_distribution=offer_distribution,
        offer_percentages=offer_percentages
    )


def run_evaluation(
    user_ids: List[str],
    db_path: str,
    evaluation_id: Optional[str] = None
) -> EvaluationResults:
    """
    Run complete evaluation.
    
    Args:
        user_ids: List of user IDs to evaluate
        db_path: Path to SQLite database
        evaluation_id: Optional evaluation ID (auto-generated if not provided)
        
    Returns:
        EvaluationResults object
    """
    if evaluation_id is None:
        timestamp = datetime.now()
        evaluation_id = f"EVAL-{timestamp.strftime('%Y%m%d%H%M%S')}"
    
    # Run all evaluations
    coverage = evaluate_coverage(user_ids, db_path)
    explainability = evaluate_explainability(user_ids, db_path)
    performance = evaluate_performance(user_ids, db_path)
    fairness = evaluate_fairness(user_ids, db_path)
    
    # Create summary
    summary = {
        "coverage": {
            "persona_assignment_rate": coverage.persona_assignment_rate,
            "meets_target": coverage.persona_assignment_rate >= 100.0,
            "average_behaviors_per_user": coverage.average_behaviors_per_user,
            "meets_target": coverage.average_behaviors_per_user >= 3.0
        },
        "explainability": {
            "rationale_coverage_rate": explainability.rationale_coverage_rate,
            "meets_target": explainability.rationale_coverage_rate >= 100.0,
            "trace_completeness_rate": explainability.trace_completeness_rate,
            "meets_target": explainability.trace_completeness_rate >= 100.0
        },
        "performance": {
            "average_latency_per_user": performance.average_latency_per_user,
            "meets_target": performance.average_latency_per_user < 5.0,
            "batch_processing_throughput": performance.batch_processing_throughput
        }
    }
    
    return EvaluationResults(
        evaluation_id=evaluation_id,
        timestamp=datetime.now(),
        coverage_metrics=coverage,
        explainability_metrics=explainability,
        performance_metrics=performance,
        fairness_metrics=fairness,
        summary=summary
    )


def export_metrics_json(results: EvaluationResults, output_path: str) -> None:
    """
    Export metrics to JSON file.
    
    Args:
        results: EvaluationResults object
        output_path: Path to output JSON file
    """
    data = asdict(results)
    
    # Convert datetime to string
    data['timestamp'] = results.timestamp.isoformat()
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def export_metrics_csv(results: EvaluationResults, output_path: str) -> None:
    """
    Export metrics to CSV file.
    
    Args:
        results: EvaluationResults object
        output_path: Path to output CSV file
    """
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(['Metric Category', 'Metric', 'Value', 'Target', 'Meets Target'])
        
        # Coverage metrics
        writer.writerow(['Coverage', 'Persona Assignment Rate', f"{results.coverage_metrics.persona_assignment_rate:.2f}%", '100%', results.coverage_metrics.persona_assignment_rate >= 100.0])
        writer.writerow(['Coverage', 'Average Behaviors Per User', f"{results.coverage_metrics.average_behaviors_per_user:.2f}", '≥3', results.coverage_metrics.average_behaviors_per_user >= 3.0])
        
        # Explainability metrics
        writer.writerow(['Explainability', 'Rationale Coverage Rate', f"{results.explainability_metrics.rationale_coverage_rate:.2f}%", '100%', results.explainability_metrics.rationale_coverage_rate >= 100.0])
        writer.writerow(['Explainability', 'Trace Completeness Rate', f"{results.explainability_metrics.trace_completeness_rate:.2f}%", '100%', results.explainability_metrics.trace_completeness_rate >= 100.0])
        
        # Performance metrics
        writer.writerow(['Performance', 'Average Latency Per User', f"{results.performance_metrics.average_latency_per_user:.2f}s", '<5s', results.performance_metrics.average_latency_per_user < 5.0])
        writer.writerow(['Performance', 'Batch Processing Throughput', f"{results.performance_metrics.batch_processing_throughput:.2f} users/s", 'N/A', 'N/A'])


def generate_summary_report(results: EvaluationResults, output_path: str) -> None:
    """
    Generate summary report (1-2 pages).
    
    Args:
        results: EvaluationResults object
        output_path: Path to output report file
    """
    report = f"""
SpendSenseAI Evaluation Report
Generated: {results.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Evaluation ID: {results.evaluation_id}

================================================================================
COVERAGE METRICS
================================================================================
Total Users Evaluated: {results.coverage_metrics.total_users}
Users with Persona Assignment: {results.coverage_metrics.users_with_persona}
Persona Assignment Rate: {results.coverage_metrics.persona_assignment_rate:.2f}%
  Target: 100% | Status: {'✓ MEETS TARGET' if results.coverage_metrics.persona_assignment_rate >= 100.0 else '✗ BELOW TARGET'}

Users with Behavioral Signals: {results.coverage_metrics.users_with_signals}
Average Behaviors Detected Per User: {results.coverage_metrics.average_behaviors_per_user:.2f}
  Target: ≥3 | Status: {'✓ MEETS TARGET' if results.coverage_metrics.average_behaviors_per_user >= 3.0 else '✗ BELOW TARGET'}

Users with Recommendations: {results.coverage_metrics.users_with_recommendations}
Recommendation Coverage Rate: {results.coverage_metrics.recommendation_coverage_rate:.2f}%

================================================================================
EXPLAINABILITY METRICS
================================================================================
Total Recommendations: {results.explainability_metrics.total_recommendations}
Recommendations with Rationales: {results.explainability_metrics.recommendations_with_rationales}
Rationale Coverage Rate: {results.explainability_metrics.rationale_coverage_rate:.2f}%
  Target: 100% | Status: {'✓ MEETS TARGET' if results.explainability_metrics.rationale_coverage_rate >= 100.0 else '✗ BELOW TARGET'}

Total Decision Traces: {results.explainability_metrics.total_traces}
Traces with Complete Data: {results.explainability_metrics.traces_with_complete_data}
Trace Completeness Rate: {results.explainability_metrics.trace_completeness_rate:.2f}%
  Target: 100% | Status: {'✓ MEETS TARGET' if results.explainability_metrics.trace_completeness_rate >= 100.0 else '✗ BELOW TARGET'}

Recommendations with Data Citations: {results.explainability_metrics.recommendations_with_data_citations}
Data Citation Coverage Rate: {results.explainability_metrics.data_citation_coverage_rate:.2f}%

================================================================================
PERFORMANCE METRICS
================================================================================
Total Users Processed: {results.performance_metrics.total_users_processed}
Total Processing Time: {results.performance_metrics.total_processing_time:.2f}s
Average Latency Per User: {results.performance_metrics.average_latency_per_user:.2f}s
  Target: <5s | Status: {'✓ MEETS TARGET' if results.performance_metrics.average_latency_per_user < 5.0 else '✗ BELOW TARGET'}

Batch Processing Throughput: {results.performance_metrics.batch_processing_throughput:.2f} users/second

Component Timing:
  - Persona Assignment: {results.performance_metrics.persona_assignment_time:.2f}s
  - Signal Detection: {results.performance_metrics.signal_detection_time:.2f}s
  - Recommendation Generation: {results.performance_metrics.recommendation_generation_time:.2f}s

================================================================================
FAIRNESS ANALYSIS
================================================================================
Persona Distribution:
"""
    
    for persona, count in results.fairness_metrics.persona_distribution.items():
        percentage = results.fairness_metrics.persona_percentages.get(persona, 0.0)
        report += f"  - {persona.replace('_', ' ').title()}: {count} users ({percentage:.1f}%)\n"
    
    report += "\nOffer Distribution:\n"
    for offer_type, count in results.fairness_metrics.offer_distribution.items():
        percentage = results.fairness_metrics.offer_percentages.get(offer_type, 0.0)
        report += f"  - {offer_type.replace('_', ' ').title()}: {count} offers ({percentage:.1f}%)\n"
    
    report += f"""
================================================================================
SUMMARY
================================================================================
Overall System Status: {'✓ MEETS TARGETS' if all([
    results.coverage_metrics.persona_assignment_rate >= 100.0,
    results.coverage_metrics.average_behaviors_per_user >= 3.0,
    results.explainability_metrics.rationale_coverage_rate >= 100.0,
    results.explainability_metrics.trace_completeness_rate >= 100.0,
    results.performance_metrics.average_latency_per_user < 5.0
]) else '✗ SOME TARGETS NOT MET'}

Key Achievements:
  - Persona assignment coverage: {results.coverage_metrics.persona_assignment_rate:.1f}%
  - Explainability: {results.explainability_metrics.rationale_coverage_rate:.1f}% of recommendations have rationales
  - Performance: Average latency of {results.performance_metrics.average_latency_per_user:.2f}s per user

Areas for Improvement:
"""
    
    if results.coverage_metrics.persona_assignment_rate < 100.0:
        report += f"  - Persona assignment rate below target ({results.coverage_metrics.persona_assignment_rate:.1f}% < 100%)\n"
    if results.coverage_metrics.average_behaviors_per_user < 3.0:
        report += f"  - Average behaviors per user below target ({results.coverage_metrics.average_behaviors_per_user:.2f} < 3.0)\n"
    if results.explainability_metrics.rationale_coverage_rate < 100.0:
        report += f"  - Rationale coverage below target ({results.explainability_metrics.rationale_coverage_rate:.1f}% < 100%)\n"
    if results.performance_metrics.average_latency_per_user >= 5.0:
        report += f"  - Average latency above target ({results.performance_metrics.average_latency_per_user:.2f}s >= 5.0s)\n"
    
    if not any([
        results.coverage_metrics.persona_assignment_rate < 100.0,
        results.coverage_metrics.average_behaviors_per_user < 3.0,
        results.explainability_metrics.rationale_coverage_rate < 100.0,
        results.performance_metrics.average_latency_per_user >= 5.0
    ]):
        report += "  - All targets met! System is performing well.\n"
    
    with open(output_path, 'w') as f:
        f.write(report)

