"""
A/B Testing Framework for SpendSenseAI.

Enables experimentation with recommendation strategies:
- Experiment configuration
- User cohort assignment (randomized)
- Statistical analysis
- Results tracking
- Winner declaration
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import math

from ingest.database import get_connection
from eval.effectiveness_tracking import EngagementMetrics, OutcomeMetrics


class ExperimentStatus(str, Enum):
    """Experiment status."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class VariantType(str, Enum):
    """Experiment variant type."""
    CONTROL = "control"
    TREATMENT = "treatment"


@dataclass
class ExperimentVariant:
    """Experiment variant configuration."""
    variant_id: str
    variant_type: VariantType
    name: str
    description: str
    configuration: Dict[str, Any]
    traffic_percentage: float = 50.0  # Percentage of users assigned to this variant


@dataclass
class Experiment:
    """A/B test experiment."""
    experiment_id: str
    name: str
    description: str
    status: ExperimentStatus
    variants: List[ExperimentVariant]
    start_date: datetime
    end_date: Optional[datetime] = None
    target_sample_size: Optional[int] = None
    min_sample_size: int = 100
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None


@dataclass
class ExperimentResult:
    """Experiment results."""
    experiment_id: str
    variant_id: str
    variant_type: VariantType
    sample_size: int
    engagement_rate: float
    completion_rate: float
    conversion_rate: float
    average_outcome_improvement: float
    statistical_significance: float  # p-value
    confidence_interval_lower: float
    confidence_interval_upper: float
    is_winner: bool = False


def create_ab_testing_tables(db_path: str) -> None:
    """Create A/B testing tables in database."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Experiments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ab_experiments (
                experiment_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP,
                target_sample_size INTEGER,
                min_sample_size INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT
            )
        """)
        
        # Experiment variants table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ab_experiment_variants (
                variant_id TEXT PRIMARY KEY,
                experiment_id TEXT NOT NULL,
                variant_type TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                configuration TEXT NOT NULL,
                traffic_percentage REAL DEFAULT 50.0,
                FOREIGN KEY (experiment_id) REFERENCES ab_experiments(experiment_id)
            )
        """)
        
        # User assignments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ab_user_assignments (
                user_id TEXT NOT NULL,
                experiment_id TEXT NOT NULL,
                variant_id TEXT NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, experiment_id),
                FOREIGN KEY (experiment_id) REFERENCES ab_experiments(experiment_id),
                FOREIGN KEY (variant_id) REFERENCES ab_experiment_variants(variant_id)
            )
        """)
        
        # Experiment results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ab_experiment_results (
                experiment_id TEXT NOT NULL,
                variant_id TEXT NOT NULL,
                sample_size INTEGER,
                engagement_rate REAL,
                completion_rate REAL,
                conversion_rate REAL,
                average_outcome_improvement REAL,
                statistical_significance REAL,
                confidence_interval_lower REAL,
                confidence_interval_upper REAL,
                is_winner INTEGER DEFAULT 0,
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (experiment_id, variant_id),
                FOREIGN KEY (experiment_id) REFERENCES ab_experiments(experiment_id),
                FOREIGN KEY (variant_id) REFERENCES ab_experiment_variants(variant_id)
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ab_experiments_status 
            ON ab_experiments(status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ab_user_assignments_user 
            ON ab_user_assignments(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ab_user_assignments_experiment 
            ON ab_user_assignments(experiment_id)
        """)
        
        conn.commit()


def assign_user_to_variant(
    user_id: str,
    experiment_id: str,
    db_path: str,
    force_variant: Optional[str] = None
) -> Optional[str]:
    """
    Assign user to experiment variant (deterministic assignment).
    
    Args:
        user_id: User ID
        experiment_id: Experiment ID
        db_path: Path to database
        force_variant: Optional variant ID to force assignment
        
    Returns:
        Variant ID assigned to user
    """
    create_ab_testing_tables(db_path)
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Check if user is already assigned
        cursor.execute("""
            SELECT variant_id 
            FROM ab_user_assignments 
            WHERE user_id = ? AND experiment_id = ?
        """, (user_id, experiment_id))
        
        row = cursor.fetchone()
        if row:
            return row[0]
        
        # Check if experiment exists and is running
        cursor.execute("""
            SELECT status 
            FROM ab_experiments 
            WHERE experiment_id = ?
        """, (experiment_id,))
        
        exp_row = cursor.fetchone()
        if not exp_row or exp_row[0] != ExperimentStatus.RUNNING.value:
            return None
        
        # Get variants
        cursor.execute("""
            SELECT variant_id, variant_type, traffic_percentage 
            FROM ab_experiment_variants 
            WHERE experiment_id = ?
            ORDER BY variant_type
        """, (experiment_id,))
        
        variants = cursor.fetchall()
        if not variants:
            return None
        
        # Force assignment if specified
        if force_variant:
            variant_id = force_variant
        else:
            # Deterministic assignment based on user_id hash
            hash_value = int(hashlib.md5(f"{user_id}:{experiment_id}".encode()).hexdigest(), 16)
            hash_percentage = (hash_value % 10000) / 100.0
            
            # Assign based on traffic percentages
            cumulative = 0.0
            variant_id = None
            for v_id, v_type, v_percentage in variants:
                cumulative += v_percentage
                if hash_percentage < cumulative:
                    variant_id = v_id
                    break
            
            # Fallback to first variant
            if not variant_id:
                variant_id = variants[0][0]
        
        # Record assignment
        cursor.execute("""
            INSERT INTO ab_user_assignments (user_id, experiment_id, variant_id)
            VALUES (?, ?, ?)
        """, (user_id, experiment_id, variant_id))
        
        conn.commit()
        
        return variant_id


def get_user_variant(
    user_id: str,
    experiment_id: str,
    db_path: str
) -> Optional[str]:
    """
    Get variant assigned to user for an experiment.
    
    Args:
        user_id: User ID
        experiment_id: Experiment ID
        db_path: Path to database
        
    Returns:
        Variant ID or None
    """
    create_ab_testing_tables(db_path)
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT variant_id 
            FROM ab_user_assignments 
            WHERE user_id = ? AND experiment_id = ?
        """, (user_id, experiment_id))
        
        row = cursor.fetchone()
        return row[0] if row else None


def calculate_statistical_significance(
    control_metric: float,
    treatment_metric: float,
    control_sample_size: int,
    treatment_sample_size: int
) -> Tuple[float, float, float]:
    """
    Calculate statistical significance using two-proportion z-test.
    
    Args:
        control_metric: Control group metric (e.g., conversion rate)
        treatment_metric: Treatment group metric
        control_sample_size: Control group sample size
        treatment_sample_size: Treatment group sample size
        
    Returns:
        Tuple of (p-value, confidence_interval_lower, confidence_interval_upper)
    """
    if control_sample_size == 0 or treatment_sample_size == 0:
        return 1.0, 0.0, 0.0
    
    # Pooled proportion
    p_pool = (control_metric * control_sample_size + treatment_metric * treatment_sample_size) / (control_sample_size + treatment_sample_size)
    
    if p_pool == 0 or p_pool == 1:
        return 1.0, 0.0, 0.0
    
    # Standard error
    se = math.sqrt(p_pool * (1 - p_pool) * (1/control_sample_size + 1/treatment_sample_size))
    
    if se == 0:
        return 1.0, 0.0, 0.0
    
    # Z-score
    z = (treatment_metric - control_metric) / se
    
    # P-value (two-tailed test)
    # Simplified: using normal approximation
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    
    # 95% confidence interval
    margin = 1.96 * se
    ci_lower = (treatment_metric - control_metric) - margin
    ci_upper = (treatment_metric - control_metric) + margin
    
    return p_value, ci_lower, ci_upper


def analyze_experiment_results(
    experiment_id: str,
    db_path: str
) -> List[ExperimentResult]:
    """
    Analyze experiment results and calculate statistical significance.
    
    Args:
        experiment_id: Experiment ID
        db_path: Path to database
        
    Returns:
        List of ExperimentResult objects
    """
    create_ab_testing_tables(db_path)
    
    results = []
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Get variants
        cursor.execute("""
            SELECT variant_id, variant_type 
            FROM ab_experiment_variants 
            WHERE experiment_id = ?
        """, (experiment_id,))
        
        variants = cursor.fetchall()
        
        # Get engagement metrics for each variant
        variant_metrics = {}
        
        for variant_id, variant_type in variants:
            # Get users in this variant
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) 
                FROM ab_user_assignments 
                WHERE experiment_id = ? AND variant_id = ?
            """, (experiment_id, variant_id))
            
            sample_size = cursor.fetchone()[0] or 0
            
            # Get engagement metrics
            try:
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT e.recommendation_id) as total_recs,
                        SUM(CASE WHEN e.action='view' THEN 1 ELSE 0 END) as views,
                        SUM(CASE WHEN e.action='click' THEN 1 ELSE 0 END) as clicks,
                        SUM(CASE WHEN e.action='complete' THEN 1 ELSE 0 END) as completions
                    FROM recommendation_engagement e
                    INNER JOIN ab_user_assignments a ON e.user_id = a.user_id
                    WHERE a.experiment_id = ? AND a.variant_id = ?
                """, (experiment_id, variant_id))
                
                row = cursor.fetchone()
                total_recs = row[0] or 0
                views = row[1] or 0
                clicks = row[2] or 0
                completions = row[3] or 0
                
                engagement_rate = (clicks / views * 100) if views > 0 else 0.0
                completion_rate = (completions / views * 100) if views > 0 else 0.0
                conversion_rate = (completions / total_recs * 100) if total_recs > 0 else 0.0
                
                # Get outcome metrics
                cursor.execute("""
                    SELECT AVG(improvement_percentage) 
                    FROM recommendation_outcome o
                    INNER JOIN ab_user_assignments a ON o.user_id = a.user_id
                    WHERE a.experiment_id = ? AND a.variant_id = ?
                """, (experiment_id, variant_id))
                
                outcome_row = cursor.fetchone()
                avg_outcome = outcome_row[0] or 0.0
                
            except Exception:
                engagement_rate = 0.0
                completion_rate = 0.0
                conversion_rate = 0.0
                avg_outcome = 0.0
            
            variant_metrics[variant_id] = {
                "variant_type": VariantType(variant_type),
                "sample_size": sample_size,
                "engagement_rate": engagement_rate,
                "completion_rate": completion_rate,
                "conversion_rate": conversion_rate,
                "average_outcome_improvement": avg_outcome
            }
        
        # Calculate statistical significance
        control_variant = None
        treatment_variants = []
        
        for variant_id, metrics in variant_metrics.items():
            if metrics["variant_type"] == VariantType.CONTROL:
                control_variant = (variant_id, metrics)
            else:
                treatment_variants.append((variant_id, metrics))
        
        if not control_variant:
            return results
        
        control_id, control_metrics = control_variant
        
        # Compare each treatment to control
        for treatment_id, treatment_metrics in treatment_variants:
            p_value, ci_lower, ci_upper = calculate_statistical_significance(
                control_metric=control_metrics["conversion_rate"] / 100.0,
                treatment_metric=treatment_metrics["conversion_rate"] / 100.0,
                control_sample_size=control_metrics["sample_size"],
                treatment_sample_size=treatment_metrics["sample_size"]
            )
            
            is_winner = p_value < 0.05 and treatment_metrics["conversion_rate"] > control_metrics["conversion_rate"]
            
            result = ExperimentResult(
                experiment_id=experiment_id,
                variant_id=treatment_id,
                variant_type=treatment_metrics["variant_type"],
                sample_size=treatment_metrics["sample_size"],
                engagement_rate=treatment_metrics["engagement_rate"],
                completion_rate=treatment_metrics["completion_rate"],
                conversion_rate=treatment_metrics["conversion_rate"],
                average_outcome_improvement=treatment_metrics["average_outcome_improvement"],
                statistical_significance=p_value,
                confidence_interval_lower=ci_lower * 100,
                confidence_interval_upper=ci_upper * 100,
                is_winner=is_winner
            )
            
            results.append(result)
        
        # Add control result
        control_result = ExperimentResult(
            experiment_id=experiment_id,
            variant_id=control_id,
            variant_type=control_metrics["variant_type"],
            sample_size=control_metrics["sample_size"],
            engagement_rate=control_metrics["engagement_rate"],
            completion_rate=control_metrics["completion_rate"],
            conversion_rate=control_metrics["conversion_rate"],
            average_outcome_improvement=control_metrics["average_outcome_improvement"],
            statistical_significance=1.0,
            confidence_interval_lower=0.0,
            confidence_interval_upper=0.0,
            is_winner=False
        )
        
        results.insert(0, control_result)
    
    return results


def create_experiment(
    experiment: Experiment,
    db_path: str
) -> str:
    """
    Create a new A/B test experiment.
    
    Args:
        experiment: Experiment object
        db_path: Path to database
        
    Returns:
        Experiment ID
    """
    create_ab_testing_tables(db_path)
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Insert experiment
        cursor.execute("""
            INSERT INTO ab_experiments 
            (experiment_id, name, description, status, start_date, end_date, target_sample_size, min_sample_size, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            experiment.experiment_id,
            experiment.name,
            experiment.description,
            experiment.status.value,
            experiment.start_date.isoformat(),
            experiment.end_date.isoformat() if experiment.end_date else None,
            experiment.target_sample_size,
            experiment.min_sample_size,
            experiment.created_at.isoformat(),
            experiment.created_by
        ))
        
        # Insert variants
        for variant in experiment.variants:
            cursor.execute("""
                INSERT INTO ab_experiment_variants 
                (variant_id, experiment_id, variant_type, name, description, configuration, traffic_percentage)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                variant.variant_id,
                experiment.experiment_id,
                variant.variant_type.value,
                variant.name,
                variant.description,
                json.dumps(variant.configuration),
                variant.traffic_percentage
            ))
        
        conn.commit()
    
    return experiment.experiment_id


def get_experiment(
    experiment_id: str,
    db_path: str
) -> Optional[Experiment]:
    """
    Get experiment by ID.
    
    Args:
        experiment_id: Experiment ID
        db_path: Path to database
        
    Returns:
        Experiment object or None
    """
    create_ab_testing_tables(db_path)
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, description, status, start_date, end_date, target_sample_size, min_sample_size, created_at, created_by
            FROM ab_experiments 
            WHERE experiment_id = ?
        """, (experiment_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        # Get variants
        cursor.execute("""
            SELECT variant_id, variant_type, name, description, configuration, traffic_percentage
            FROM ab_experiment_variants 
            WHERE experiment_id = ?
        """, (experiment_id,))
        
        variants = []
        for v_row in cursor.fetchall():
            variants.append(ExperimentVariant(
                variant_id=v_row[0],
                variant_type=VariantType(v_row[1]),
                name=v_row[2],
                description=v_row[3],
                configuration=json.loads(v_row[4]),
                traffic_percentage=v_row[5]
            ))
        
        return Experiment(
            experiment_id=experiment_id,
            name=row[0],
            description=row[1],
            status=ExperimentStatus(row[2]),
            variants=variants,
            start_date=datetime.fromisoformat(row[3]),
            end_date=datetime.fromisoformat(row[4]) if row[4] else None,
            target_sample_size=row[5],
            min_sample_size=row[6],
            created_at=datetime.fromisoformat(row[7]),
            created_by=row[8]
        )


