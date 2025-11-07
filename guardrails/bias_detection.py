"""
Bias Detection & Mitigation for SpendSenseAI.

Ensures fairness across user groups:
- Demographic parity analysis
- Disparate impact testing
- Calibration checks
- Bias mitigation strategies
- Fairness report generation
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path

from personas.persona_definition import PersonaType
from personas.persona_prioritization import assign_personas_with_prioritization
# Lazy import to avoid circular dependency
# from recommend.recommendation_builder import build_recommendations
from ingest.queries import get_accounts_by_customer


@dataclass
class DemographicGroup:
    """Demographic group definition."""
    group_name: str
    user_ids: List[str]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class FairnessMetrics:
    """Fairness metrics for a demographic group."""
    group_name: str
    persona_distribution: Dict[str, float]  # Persona type -> percentage
    offer_distribution: Dict[str, float]  # Offer type -> percentage
    average_confidence_score: float
    recommendation_rate: float
    positive_outcome_rate: float = 0.0  # If we track outcomes


@dataclass
class BiasReport:
    """Bias detection report."""
    report_id: str
    timestamp: datetime
    demographic_groups: List[DemographicGroup]
    fairness_metrics: List[FairnessMetrics]
    disparate_impact_analysis: Dict[str, float]  # Metric -> impact ratio
    calibration_analysis: Dict[str, float]  # Group -> calibration error
    bias_mitigation_recommendations: List[str]
    summary: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.summary is None:
            self.summary = {}


def analyze_demographic_parity(
    groups: List[DemographicGroup],
    db_path: str
) -> Dict[str, FairnessMetrics]:
    """
    Analyze demographic parity across groups.
    
    Args:
        groups: List of demographic groups
        db_path: Path to SQLite database
        
    Returns:
        Dictionary mapping group name to FairnessMetrics
    """
    fairness_metrics = {}
    
    for group in groups:
        persona_distribution = {}
        offer_distribution = {}
        total_confidence = 0.0
        users_with_recommendations = 0
        total_users = len(group.user_ids)
        
        persona_counts = {}
        offer_counts = {}
        
        for user_id in group.user_ids:
            try:
                # Get persona assignment
                persona_assignment = assign_personas_with_prioritization(user_id, db_path)
                
                if persona_assignment.primary_persona:
                    persona_type = persona_assignment.primary_persona.persona_type.value
                    persona_counts[persona_type] = persona_counts.get(persona_type, 0) + 1
                    total_confidence += persona_assignment.primary_persona.confidence_score
                    
                    # Get recommendations (lazy import to avoid circular dependency)
                    from recommend.recommendation_builder import build_recommendations
                    recommendations = build_recommendations(
                        user_id, db_path, persona_assignment,
                        check_consent=False
                    )
                    
                    if recommendations.education_items or recommendations.partner_offers:
                        users_with_recommendations += 1
                        
                        # Count offers
                        for offer in recommendations.partner_offers:
                            offer_type = offer.offer_id.split('-')[1] if '-' in offer.offer_id else 'unknown'
                            offer_counts[offer_type] = offer_counts.get(offer_type, 0) + 1
            except Exception:
                pass
        
        # Calculate percentages
        total_personas = sum(persona_counts.values())
        for persona_type, count in persona_counts.items():
            persona_distribution[persona_type] = (count / total_personas * 100) if total_personas > 0 else 0.0
        
        total_offers = sum(offer_counts.values())
        for offer_type, count in offer_counts.items():
            offer_distribution[offer_type] = (count / total_offers * 100) if total_offers > 0 else 0.0
        
        average_confidence = (total_confidence / total_users) if total_users > 0 else 0.0
        recommendation_rate = (users_with_recommendations / total_users * 100) if total_users > 0 else 0.0
        
        fairness_metrics[group.group_name] = FairnessMetrics(
            group_name=group.group_name,
            persona_distribution=persona_distribution,
            offer_distribution=offer_distribution,
            average_confidence_score=average_confidence,
            recommendation_rate=recommendation_rate
        )
    
    return fairness_metrics


def detect_disparate_impact(
    fairness_metrics: Dict[str, FairnessMetrics],
    reference_group: str = None
) -> Dict[str, float]:
    """
    Detect disparate impact across groups.
    
    Uses the 80% rule: if a protected group's positive outcome rate is less than 80% of
    the reference group's rate, there may be disparate impact.
    
    Args:
        fairness_metrics: Dictionary of fairness metrics by group
        reference_group: Reference group name (defaults to first group)
        
    Returns:
        Dictionary mapping metric name to impact ratio
    """
    if not fairness_metrics:
        return {}
    
    if reference_group is None:
        reference_group = list(fairness_metrics.keys())[0]
    
    reference_metrics = fairness_metrics.get(reference_group)
    if not reference_metrics:
        return {}
    
    disparate_impact = {}
    
    # Compare recommendation rates
    reference_recommendation_rate = reference_metrics.recommendation_rate
    
    for group_name, metrics in fairness_metrics.items():
        if group_name == reference_group:
            continue
        
        impact_ratio = (metrics.recommendation_rate / reference_recommendation_rate) if reference_recommendation_rate > 0 else 0.0
        disparate_impact[f"{group_name}_recommendation_rate"] = impact_ratio
    
    # Compare persona distribution
    reference_personas = reference_metrics.persona_distribution
    
    for group_name, metrics in fairness_metrics.items():
        if group_name == reference_group:
            continue
        
        for persona_type, reference_pct in reference_personas.items():
            group_pct = metrics.persona_distribution.get(persona_type, 0.0)
            if reference_pct > 0:
                impact_ratio = group_pct / reference_pct
                key = f"{group_name}_{persona_type}_distribution"
                disparate_impact[key] = impact_ratio
    
    return disparate_impact


def check_calibration(
    fairness_metrics: Dict[str, FairnessMetrics]
) -> Dict[str, float]:
    """
    Check calibration (are confidence scores accurate across groups?).
    
    Args:
        fairness_metrics: Dictionary of fairness metrics by group
        
    Returns:
        Dictionary mapping group name to calibration error
    """
    calibration_errors = {}
    
    # Calculate average confidence score across all groups
    all_confidence_scores = [m.average_confidence_score for m in fairness_metrics.values()]
    overall_average = sum(all_confidence_scores) / len(all_confidence_scores) if all_confidence_scores else 0.0
    
    # Calculate calibration error for each group
    for group_name, metrics in fairness_metrics.items():
        error = abs(metrics.average_confidence_score - overall_average)
        calibration_errors[group_name] = error
    
    return calibration_errors


def generate_bias_mitigation_recommendations(
    fairness_metrics: Dict[str, FairnessMetrics],
    disparate_impact: Dict[str, float],
    calibration_errors: Dict[str, float]
) -> List[str]:
    """
    Generate bias mitigation recommendations.
    
    Args:
        fairness_metrics: Fairness metrics by group
        disparate_impact: Disparate impact analysis
        calibration_errors: Calibration errors by group
        
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Check for disparate impact (80% rule)
    for metric, impact_ratio in disparate_impact.items():
        if impact_ratio < 0.8:
            recommendations.append(
                f"⚠️ Disparate impact detected for {metric}: {impact_ratio:.2f} "
                f"(below 0.8 threshold). Consider re-weighting or threshold adjustments."
            )
    
    # Check for calibration issues
    for group_name, error in calibration_errors.items():
        if error > 0.1:  # 10% error threshold
            recommendations.append(
                f"⚠️ Calibration error detected for {group_name}: {error:.2%}. "
                f"Consider adjusting confidence score calibration for this group."
            )
    
    # Check for persona distribution imbalances
    for group_name, metrics in fairness_metrics.items():
        # Check if one persona dominates (>70%)
        max_persona_pct = max(metrics.persona_distribution.values()) if metrics.persona_distribution else 0.0
        if max_persona_pct > 0.7:
            max_persona = max(metrics.persona_distribution.items(), key=lambda x: x[1])[0]
            recommendations.append(
                f"⚠️ Persona distribution imbalance in {group_name}: {max_persona} represents "
                f"{max_persona_pct:.1f}% of assignments. Consider reviewing persona criteria."
            )
    
    if not recommendations:
        recommendations.append("✅ No significant bias detected. System appears fair across groups.")
    
    return recommendations


def run_bias_detection(
    groups: List[DemographicGroup],
    db_path: str,
    report_id: Optional[str] = None
) -> BiasReport:
    """
    Run complete bias detection analysis.
    
    Args:
        groups: List of demographic groups
        db_path: Path to SQLite database
        report_id: Optional report ID (auto-generated if not provided)
        
    Returns:
        BiasReport object
    """
    if report_id is None:
        timestamp = datetime.now()
        report_id = f"BIAS-{timestamp.strftime('%Y%m%d%H%M%S')}"
    
    # Analyze demographic parity
    fairness_metrics_dict = analyze_demographic_parity(groups, db_path)
    fairness_metrics = list(fairness_metrics_dict.values())
    
    # Detect disparate impact
    disparate_impact = detect_disparate_impact(fairness_metrics_dict)
    
    # Check calibration
    calibration_errors = check_calibration(fairness_metrics_dict)
    
    # Generate recommendations
    recommendations = generate_bias_mitigation_recommendations(
        fairness_metrics_dict, disparate_impact, calibration_errors
    )
    
    # Create summary
    summary = {
        "total_groups": len(groups),
        "groups_with_issues": sum(1 for r in recommendations if "⚠️" in r),
        "disparate_impact_count": sum(1 for ratio in disparate_impact.values() if ratio < 0.8),
        "calibration_issues_count": sum(1 for error in calibration_errors.values() if error > 0.1)
    }
    
    return BiasReport(
        report_id=report_id,
        timestamp=datetime.now(),
        demographic_groups=groups,
        fairness_metrics=fairness_metrics,
        disparate_impact_analysis=disparate_impact,
        calibration_analysis=calibration_errors,
        bias_mitigation_recommendations=recommendations,
        summary=summary
    )


def export_bias_report(report: BiasReport, output_path: str) -> None:
    """
    Export bias report to JSON file.
    
    Args:
        report: BiasReport object
        output_path: Path to output JSON file
    """
    data = {
        "report_id": report.report_id,
        "timestamp": report.timestamp.isoformat(),
        "demographic_groups": [
            {
                "group_name": g.group_name,
                "user_count": len(g.user_ids),
                "metadata": g.metadata
            }
            for g in report.demographic_groups
        ],
        "fairness_metrics": [
            {
                "group_name": m.group_name,
                "persona_distribution": m.persona_distribution,
                "offer_distribution": m.offer_distribution,
                "average_confidence_score": m.average_confidence_score,
                "recommendation_rate": m.recommendation_rate
            }
            for m in report.fairness_metrics
        ],
        "disparate_impact_analysis": report.disparate_impact_analysis,
        "calibration_analysis": report.calibration_analysis,
        "bias_mitigation_recommendations": report.bias_mitigation_recommendations,
        "summary": report.summary
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def generate_fairness_audit_report(report: BiasReport, output_path: str) -> None:
    """
    Generate human-readable fairness audit report.
    
    Args:
        report: BiasReport object
        output_path: Path to output report file
    """
    report_text = f"""
SpendSenseAI Fairness Audit Report
Generated: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Report ID: {report.report_id}

================================================================================
EXECUTIVE SUMMARY
================================================================================
Total Groups Analyzed: {report.summary.get('total_groups', 0)}
Groups with Issues: {report.summary.get('groups_with_issues', 0)}
Disparate Impact Cases: {report.summary.get('disparate_impact_count', 0)}
Calibration Issues: {report.summary.get('calibration_issues_count', 0)}

================================================================================
FAIRNESS METRICS BY GROUP
================================================================================
"""
    
    for metrics in report.fairness_metrics:
        report_text += f"\n{metrics.group_name}:\n"
        report_text += f"  Recommendation Rate: {metrics.recommendation_rate:.2f}%\n"
        report_text += f"  Average Confidence Score: {metrics.average_confidence_score:.2%}\n"
        report_text += f"  Persona Distribution:\n"
        for persona, pct in metrics.persona_distribution.items():
            report_text += f"    - {persona.replace('_', ' ').title()}: {pct:.1f}%\n"
        report_text += f"  Offer Distribution:\n"
        for offer_type, pct in metrics.offer_distribution.items():
            report_text += f"    - {offer_type.replace('_', ' ').title()}: {pct:.1f}%\n"
    
    report_text += "\n" + "="*60 + "\n"
    report_text += "DISPARATE IMPACT ANALYSIS\n"
    report_text += "="*60 + "\n"
    report_text += "(80% rule: values below 0.8 may indicate disparate impact)\n\n"
    
    for metric, impact_ratio in report.disparate_impact_analysis.items():
        status = "⚠️ FAIL" if impact_ratio < 0.8 else "✓ PASS"
        report_text += f"{status} {metric}: {impact_ratio:.3f}\n"
    
    report_text += "\n" + "="*60 + "\n"
    report_text += "CALIBRATION ANALYSIS\n"
    report_text += "="*60 + "\n"
    
    for group_name, error in report.calibration_analysis.items():
        status = "⚠️ ISSUE" if error > 0.1 else "✓ OK"
        report_text += f"{status} {group_name}: {error:.2%} error\n"
    
    report_text += "\n" + "="*60 + "\n"
    report_text += "BIAS MITIGATION RECOMMENDATIONS\n"
    report_text += "="*60 + "\n"
    
    for i, recommendation in enumerate(report.bias_mitigation_recommendations, 1):
        report_text += f"{i}. {recommendation}\n"
    
    with open(output_path, 'w') as f:
        f.write(report_text)

