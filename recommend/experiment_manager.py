"""
Experiment Manager for SpendSenseAI.

Manages A/B test experiments and integrates with recommendation builder.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import os

from eval.ab_testing import (
    assign_user_to_variant,
    get_user_variant,
    get_experiment,
    ExperimentStatus
)


def get_active_experiments(db_path: str) -> list:
    """Get all active experiments."""
    from ingest.database import get_connection
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT experiment_id 
            FROM ab_experiments 
            WHERE status = ?
        """, (ExperimentStatus.RUNNING.value,))
        
        return [row[0] for row in cursor.fetchall()]


def apply_experiment_config(
    user_id: str,
    recommendation_config: Dict[str, Any],
    db_path: str
) -> Dict[str, Any]:
    """
    Apply experiment configuration to recommendation config.
    
    Args:
        user_id: User ID
        recommendation_config: Base recommendation configuration
        db_path: Path to database
        
    Returns:
        Modified recommendation configuration
    """
    active_experiments = get_active_experiments(db_path)
    
    if not active_experiments:
        return recommendation_config
    
    # Get user's variant for first active experiment
    experiment_id = active_experiments[0]
    variant_id = get_user_variant(user_id, experiment_id, db_path)
    
    if not variant_id:
        # Assign user to variant
        variant_id = assign_user_to_variant(user_id, experiment_id, db_path)
    
    if not variant_id:
        return recommendation_config
    
    # Get experiment and variant configuration
    experiment = get_experiment(experiment_id, db_path)
    if not experiment:
        return recommendation_config
    
    variant = next((v for v in experiment.variants if v.variant_id == variant_id), None)
    if not variant:
        return recommendation_config
    
    # Apply variant configuration
    modified_config = recommendation_config.copy()
    modified_config.update(variant.configuration)
    modified_config["experiment_id"] = experiment_id
    modified_config["variant_id"] = variant_id
    
    return modified_config

