"""
Bias Detection & Mitigation for SpendSenseAI.

Ensure fairness across user groups:
- Demographic parity analysis (if demographics in synthetic data)
- Disparate impact testing (do recommendations differ unfairly?)
- Calibration checks (are confidence scores accurate across groups?)
- Bias mitigation strategies (re-weighting, threshold adjustments)
- Fairness report generation
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict
from math import sqrt

from eval.cohort_analysis import analyze_all_cohorts, CohortMetrics
from personas.persona_prioritization import assign_personas_with_prioritization
from personas.persona_definition import PersonaType
from recommend.recommendation_builder import build_recommendations
from recommend.partner_offers import get_eligible_offers_for_persona


@dataclass
class BiasMetric:
    """Bias metric result."""
    metric_name: str
    value: float
    threshold: float
    meets_threshold: bool
    interpretation: str


@dataclass
class BiasAnalysis:
    """Bias analysis results."""
    analysis_id: str
    timestamp: datetime
    cohorts: Dict[str, CohortMetrics]
    persona_distribution_parity: Dict[str, BiasMetric]
    offer_distribution_parity: Dict[str, BiasMetric]
    confidence_calibration: Dict[str, BiasMetric]
    bias_mitigation_recommendations: List[str]
    fairness_score: float


def calculate_demographic_parity(
    cohorts: Dict[str, CohortMetrics],
    persona_type: PersonaType
) -> BiasMetric:
    """
    Calculate demographic parity for persona assignment.
    
    Args:
        cohorts: Dictionary of cohort analyses
        persona_type: Persona type to check
        
    Returns:
        BiasMetric object
    """
    persona_key = persona_type.value
    
    # Get persona percentages for each cohort
    cohort_percentages = []
    for cohort_name, cohort_metrics in cohorts.items():
        percentage = cohort_metrics.persona_percentages.get(persona_key, 0.0)
        cohort_percentages.append(percentage)
    
    if not cohort_percentages:
        return BiasMetric(
            metric_name="Demographic Parity",
            value=0.0,
            threshold=10.0,  # Max 10% difference between cohorts
            meets_threshold=False,
            interpretation="No cohort data available"
        )
    
    # Calculate variance (measure of disparity)
    mean_percentage = sum(cohort_percentages) / len(cohort_percentages)
    variance = sum((p - mean_percentage) ** 2 for p in cohort_percentages) / len(cohort_percentages)
    std_dev = sqrt(variance)
    
    # Check if max difference exceeds threshold
    max_diff = max(cohort_percentages) - min(cohort_percentages)
    threshold = 10.0  # Max 10% difference between cohorts
    
    meets_threshold = max_diff <= threshold
    
    interpretation = f"Max difference between cohorts: {max_diff:.1f}%. "
    if meets_threshold:
        interpretation += "Fair distribution across cohorts."
    else:
        interpretation += f"Exceeds threshold of {threshold}%. Potential bias detected."
    
    return BiasMetric(
        metric_name=f"Demographic Parity ({persona_key})",
        value=max_diff,
        threshold=threshold,
        meets_threshold=meets_threshold,
        interpretation=interpretation
    )


def calculate_disparate_impact(
    cohorts: Dict[str, CohortMetrics],
    outcome_type: str = "persona"
) -> BiasMetric:
    """
    Calculate disparate impact ratio (80% rule).
    
    Args:
        cohorts: Dictionary of cohort analyses
        outcome_type: Type of outcome to check ("persona" or "offer")
        
    Returns:
        BiasMetric object
    """
    if outcome_type == "persona":
        # Check for each persona type
        persona_types = set()
        for cohort_metrics in cohorts.values():
            persona_types.update(cohort_metrics.persona_distribution.keys())
        
        # Calculate disparate impact for each persona
        max_disparate_impact = 0.0
        worst_persona = None
        
        for persona_type in persona_types:
            cohort_rates = []
            for cohort_name, cohort_metrics in cohorts.items():
                total = cohort_metrics.user_count
                count = cohort_metrics.persona_distribution.get(persona_type, 0)
                rate = (count / total * 100) if total > 0 else 0.0
                cohort_rates.append(rate)
            
            if cohort_rates:
                # 80% rule: min rate / max rate should be >= 0.8
                min_rate = min(cohort_rates)
                max_rate = max(cohort_rates)
                
                if max_rate > 0:
                    disparate_impact_ratio = min_rate / max_rate
                    if disparate_impact_ratio < 0.8:
                        if (1 - disparate_impact_ratio) > max_disparate_impact:
                            max_disparate_impact = 1 - disparate_impact_ratio
                            worst_persona = persona_type
        
        threshold = 0.8
        meets_threshold = max_disparate_impact == 0 or (1 - max_disparate_impact) >= threshold
        
        interpretation = f"Disparate impact ratio: {1 - max_disparate_impact:.2f}. "
        if meets_threshold:
            interpretation += "Meets 80% rule (fair distribution)."
        else:
            interpretation += f"Below 80% threshold. Potential disparate impact detected for {worst_persona}."
        
        return BiasMetric(
            metric_name="Disparate Impact",
            value=1 - max_disparate_impact if max_disparate_impact > 0 else 1.0,
            threshold=threshold,
            meets_threshold=meets_threshold,
            interpretation=interpretation
        )
    
    return BiasMetric(
        metric_name="Disparate Impact",
        value=0.0,
        threshold=0.8,
        meets_threshold=False,
        interpretation="Not calculated"
    )


def calculate_confidence_calibration(
    user_ids: List[str],
    db_path: str,
    cohorts: Dict[str, List[str]]
) -> BiasMetric:
    """
    Check if confidence scores are calibrated across cohorts.
    
    Args:
        user_ids: List of all user IDs
        db_path: Path to SQLite database
        cohorts: Dictionary mapping cohort names to user ID lists
        
    Returns:
        BiasMetric object
    """
    cohort_confidences = defaultdict(list)
    
    for cohort_name, cohort_user_ids in cohorts.items():
        for user_id in cohort_user_ids:
            try:
                persona_assignment = assign_personas_with_prioritization(user_id, db_path)
                
                if persona_assignment.primary_persona:
                    confidence = persona_assignment.primary_persona.confidence_score
                    cohort_confidences[cohort_name].append(confidence)
            except Exception:
                pass
    
    # Calculate average confidence per cohort
    cohort_avg_confidences = {
        cohort: sum(confidences) / len(confidences) if confidences else 0.0
        for cohort, confidences in cohort_confidences.items()
    }
    
    if not cohort_avg_confidences:
        return BiasMetric(
            metric_name="Confidence Calibration",
            value=0.0,
            threshold=0.1,  # Max 10% difference in average confidence
            meets_threshold=False,
            interpretation="No confidence data available"
        )
    
    # Check if confidence differences exceed threshold
    confidences = list(cohort_avg_confidences.values())
    max_diff = max(confidences) - min(confidences)
    threshold = 0.1  # Max 10% difference
    
    meets_threshold = max_diff <= threshold
    
    interpretation = f"Max confidence difference between cohorts: {max_diff:.2%}. "
    if meets_threshold:
        interpretation += "Confidence scores are well-calibrated across cohorts."
    else:
        interpretation += f"Exceeds threshold of {threshold:.0%}. Potential calibration bias."
    
    return BiasMetric(
        metric_name="Confidence Calibration",
        value=max_diff,
        threshold=threshold,
        meets_threshold=meets_threshold,
        interpretation=interpretation
    )


def generate_bias_mitigation_recommendations(
    bias_analysis: BiasAnalysis
) -> List[str]:
    """
    Generate bias mitigation recommendations.
    
    Args:
        bias_analysis: BiasAnalysis object
        
    Returns:
        List of mitigation recommendations
    """
    recommendations = []
    
    # Check persona distribution parity
    for metric_name, metric in bias_analysis.persona_distribution_parity.items():
        if not metric.meets_threshold:
            recommendations.append(
                f"Persona distribution parity issue in {metric_name}: "
                f"Consider adjusting persona assignment thresholds to reduce disparity."
            )
    
    # Check disparate impact
    for metric_name, metric in bias_analysis.offer_distribution_parity.items():
        if not metric.meets_threshold:
            recommendations.append(
                f"Disparate impact detected in {metric_name}: "
                f"Review eligibility rules to ensure fair access across cohorts."
            )
    
    # Check confidence calibration
    for metric_name, metric in bias_analysis.confidence_calibration.items():
        if not metric.meets_threshold:
            recommendations.append(
                f"Confidence calibration issue in {metric_name}: "
                f"Review confidence scoring to ensure consistent calibration across cohorts."
            )
    
    if not recommendations:
        recommendations.append("No bias mitigation needed. System shows fair distribution across cohorts.")
    
    return recommendations


def run_bias_analysis(
    user_ids: List[str],
    db_path: str,
    analysis_id: Optional[str] = None
) -> BiasAnalysis:
    """
    Run complete bias analysis.
    
    Args:
        user_ids: List of all user IDs
        db_path: Path to SQLite database
        analysis_id: Optional analysis ID (auto-generated if not provided)
        
    Returns:
        BiasAnalysis object
    """
    if analysis_id is None:
        timestamp = datetime.now()
        analysis_id = f"BIAS-{timestamp.strftime('%Y%m%d%H%M%S')}"
    
    # Analyze cohorts
    cohorts = analyze_all_cohorts(user_ids, db_path)
    
    # Create cohort user ID mapping
    from eval.cohort_analysis import create_income_cohorts
    cohort_user_ids = create_income_cohorts(user_ids, db_path)
    
    # Persona distribution parity
    persona_distribution_parity = {}
    for persona_type in PersonaType:
        metric = calculate_demographic_parity(cohorts, persona_type)
        persona_distribution_parity[persona_type.value] = metric
    
    # Disparate impact
    disparate_impact = calculate_disparate_impact(cohorts, "persona")
    offer_distribution_parity = {
        "disparate_impact": disparate_impact
    }
    
    # Confidence calibration
    confidence_calibration_metric = calculate_confidence_calibration(user_ids, db_path, cohort_user_ids)
    confidence_calibration = {
        "confidence_calibration": confidence_calibration_metric
    }
    
    # Create bias analysis
    bias_analysis = BiasAnalysis(
        analysis_id=analysis_id,
        timestamp=datetime.now(),
        cohorts=cohorts,
        persona_distribution_parity=persona_distribution_parity,
        offer_distribution_parity=offer_distribution_parity,
        confidence_calibration=confidence_calibration,
        bias_mitigation_recommendations=[],
        fairness_score=0.0
    )
    
    # Generate mitigation recommendations
    bias_analysis.bias_mitigation_recommendations = generate_bias_mitigation_recommendations(bias_analysis)
    
    # Calculate overall fairness score
    total_metrics = len(persona_distribution_parity) + len(offer_distribution_parity) + len(confidence_calibration)
    passed_metrics = (
        sum(1 for m in persona_distribution_parity.values() if m.meets_threshold) +
        sum(1 for m in offer_distribution_parity.values() if m.meets_threshold) +
        sum(1 for m in confidence_calibration.values() if m.meets_threshold)
    )
    
    fairness_score = (passed_metrics / total_metrics * 100) if total_metrics > 0 else 0.0
    bias_analysis.fairness_score = fairness_score
    
    return bias_analysis


def generate_fairness_report(
    bias_analysis: BiasAnalysis,
    output_path: str
) -> None:
    """
    Generate fairness report.
    
    Args:
        bias_analysis: BiasAnalysis object
        output_path: Path to output report file
    """
    report = f"""
Bias Detection & Fairness Analysis Report
Generated: {bias_analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Analysis ID: {bias_analysis.analysis_id}

================================================================================
EXECUTIVE SUMMARY
================================================================================
Overall Fairness Score: {bias_analysis.fairness_score:.1f}%

================================================================================
DEMOGRAPHIC PARITY ANALYSIS
================================================================================
"""
    
    for persona_type, metric in bias_analysis.persona_distribution_parity.items():
        status = "✓ FAIR" if metric.meets_threshold else "✗ BIAS DETECTED"
        report += f"\n{status} - {metric.metric_name}\n"
        report += f"  Value: {metric.value:.2f} (threshold: {metric.threshold:.2f})\n"
        report += f"  Interpretation: {metric.interpretation}\n"
    
    report += "\n================================================================================\n"
    report += "DISPARATE IMPACT ANALYSIS\n"
    report += "================================================================================\n"
    
    for metric_name, metric in bias_analysis.offer_distribution_parity.items():
        status = "✓ FAIR" if metric.meets_threshold else "✗ BIAS DETECTED"
        report += f"\n{status} - {metric.metric_name}\n"
        report += f"  Value: {metric.value:.2f} (threshold: {metric.threshold:.2f})\n"
        report += f"  Interpretation: {metric.interpretation}\n"
    
    report += "\n================================================================================\n"
    report += "CONFIDENCE CALIBRATION ANALYSIS\n"
    report += "================================================================================\n"
    
    for metric_name, metric in bias_analysis.confidence_calibration.items():
        status = "✓ CALIBRATED" if metric.meets_threshold else "✗ CALIBRATION ISSUE"
        report += f"\n{status} - {metric.metric_name}\n"
        report += f"  Value: {metric.value:.2%} (threshold: {metric.threshold:.2%})\n"
        report += f"  Interpretation: {metric.interpretation}\n"
    
    report += "\n================================================================================\n"
    report += "BIAS MITIGATION RECOMMENDATIONS\n"
    report += "================================================================================\n"
    
    for i, recommendation in enumerate(bias_analysis.bias_mitigation_recommendations, 1):
        report += f"{i}. {recommendation}\n"
    
    report += "\n" + "=" * 60 + "\n"
    
    with open(output_path, 'w') as f:
        f.write(report)

