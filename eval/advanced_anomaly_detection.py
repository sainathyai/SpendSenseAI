"""
Advanced Anomaly Detection for SpendSenseAI.

User & system-level anomaly detection:
- User behavior anomalies (spending spikes, unusual patterns)
- System-level anomalies (performance degradation, data quality issues)
- Alert prioritization
- Automated responses
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

from ingest.database import get_connection
from ingest.queries import get_transactions_by_customer, get_accounts_by_customer
from eval.monitoring import AnomalyAlert


class AnomalyType(str, Enum):
    """Anomaly types."""
    SPENDING_SPIKE = "spending_spike"
    UNUSUAL_PATTERN = "unusual_pattern"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    DATA_QUALITY_ISSUE = "data_quality_issue"
    PERSONA_SHIFT = "persona_shift"
    UTILIZATION_SPIKE = "utilization_spike"


class AnomalySeverity(str, Enum):
    """Anomaly severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class UserAnomaly:
    """User-level anomaly."""
    anomaly_id: str
    user_id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    description: str
    detected_at: datetime
    baseline_value: Optional[float] = None
    current_value: Optional[float] = None
    deviation_percentage: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


def detect_spending_spike(
    user_id: str,
    db_path: str,
    threshold_multiplier: float = 2.0,
    window_days: int = 7
) -> Optional[UserAnomaly]:
    """
    Detect spending spike anomaly.
    
    Args:
        user_id: User ID
        db_path: Path to database
        threshold_multiplier: Multiplier for spike detection (default: 2x)
        window_days: Time window for comparison
        
    Returns:
        UserAnomaly object or None
    """
    try:
        transactions = get_transactions_by_customer(user_id, db_path)
        
        if len(transactions) < 30:  # Need enough history
            return None
        
        # Get recent transactions
        cutoff_date = datetime.now() - timedelta(days=window_days)
        recent_transactions = [t for t in transactions if t.date >= cutoff_date.date()]
        
        # Get historical average
        historical_transactions = [t for t in transactions if t.date < cutoff_date.date()]
        
        if not recent_transactions or not historical_transactions:
            return None
        
        recent_spending = sum(abs(t.amount) for t in recent_transactions if t.amount < 0)
        historical_avg = sum(abs(t.amount) for t in historical_transactions if t.amount < 0) / len(historical_transactions) * window_days
        
        if historical_avg == 0:
            return None
        
        if recent_spending > historical_avg * threshold_multiplier:
            deviation = ((recent_spending - historical_avg) / historical_avg) * 100
            
            severity = AnomalySeverity.CRITICAL if deviation > 200 else (
                AnomalySeverity.HIGH if deviation > 100 else AnomalySeverity.MEDIUM
            )
            
            return UserAnomaly(
                anomaly_id=f"ANOM-{user_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                user_id=user_id,
                anomaly_type=AnomalyType.SPENDING_SPIKE,
                severity=severity,
                description=f"Spending spike detected: ${recent_spending:,.2f} in last {window_days} days (avg: ${historical_avg:,.2f})",
                detected_at=datetime.now(),
                baseline_value=historical_avg,
                current_value=recent_spending,
                deviation_percentage=deviation,
                metadata={"window_days": window_days}
            )
    except Exception:
        pass
    
    return None


def detect_utilization_spike(
    user_id: str,
    db_path: str,
    threshold_percentage: float = 0.80
) -> Optional[UserAnomaly]:
    """
    Detect credit utilization spike.
    
    Args:
        user_id: User ID
        db_path: Path to database
        threshold_percentage: Utilization threshold (default: 80%)
        
    Returns:
        UserAnomaly object or None
    """
    try:
        from features.credit_utilization import analyze_credit_utilization_for_customer
        
        card_metrics, agg_metrics = analyze_credit_utilization_for_customer(user_id, db_path, 30)
        
        if not card_metrics:
            return None
        
        utilization = agg_metrics.aggregate_utilization
        
        if utilization > threshold_percentage:
            severity = AnomalySeverity.CRITICAL if utilization > 0.90 else AnomalySeverity.HIGH
            
            return UserAnomaly(
                anomaly_id=f"ANOM-{user_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                user_id=user_id,
                anomaly_type=AnomalyType.UTILIZATION_SPIKE,
                severity=severity,
                description=f"High credit utilization detected: {utilization:.1f}% (threshold: {threshold_percentage*100:.0f}%)",
                detected_at=datetime.now(),
                current_value=utilization,
                deviation_percentage=(utilization - threshold_percentage) * 100,
                metadata={"threshold": threshold_percentage}
            )
    except Exception:
        pass
    
    return None


def detect_user_anomalies(
    user_id: str,
    db_path: str
) -> List[UserAnomaly]:
    """
    Detect all user-level anomalies.
    
    Args:
        user_id: User ID
        db_path: Path to database
        
    Returns:
        List of UserAnomaly objects
    """
    anomalies = []
    
    # Detect spending spike
    spending_anomaly = detect_spending_spike(user_id, db_path)
    if spending_anomaly:
        anomalies.append(spending_anomaly)
    
    # Detect utilization spike
    utilization_anomaly = detect_utilization_spike(user_id, db_path)
    if utilization_anomaly:
        anomalies.append(utilization_anomaly)
    
    return anomalies


def prioritize_anomalies(
    anomalies: List[UserAnomaly]
) -> List[UserAnomaly]:
    """
    Prioritize anomalies by severity and impact.
    
    Args:
        anomalies: List of anomalies
        
    Returns:
        Prioritized list of anomalies
    """
    severity_order = {
        AnomalySeverity.CRITICAL: 0,
        AnomalySeverity.HIGH: 1,
        AnomalySeverity.MEDIUM: 2,
        AnomalySeverity.LOW: 3
    }
    
    return sorted(
        anomalies,
        key=lambda a: (severity_order.get(a.severity, 99), a.deviation_percentage or 0),
        reverse=True
    )


def create_anomaly_detection_tables(db_path: str) -> None:
    """Create anomaly detection tables."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_anomalies (
                anomaly_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                anomaly_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT NOT NULL,
                detected_at TIMESTAMP NOT NULL,
                baseline_value REAL,
                current_value REAL,
                deviation_percentage REAL,
                metadata TEXT,
                resolved INTEGER DEFAULT 0,
                resolved_at TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_anomalies_user 
            ON user_anomalies(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_anomalies_severity 
            ON user_anomalies(severity, detected_at DESC)
        """)
        
        conn.commit()


def save_user_anomaly(
    anomaly: UserAnomaly,
    db_path: str
) -> None:
    """Save user anomaly to database."""
    create_anomaly_detection_tables(db_path)
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_anomalies 
            (anomaly_id, user_id, anomaly_type, severity, description, detected_at, 
             baseline_value, current_value, deviation_percentage, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            anomaly.anomaly_id,
            anomaly.user_id,
            anomaly.anomaly_type.value,
            anomaly.severity.value,
            anomaly.description,
            anomaly.detected_at.isoformat(),
            anomaly.baseline_value,
            anomaly.current_value,
            anomaly.deviation_percentage,
            str(anomaly.metadata) if anomaly.metadata else None
        ))
        
        conn.commit()

