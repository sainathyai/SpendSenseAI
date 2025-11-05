"""
Monitoring & Alerting System for SpendSenseAI.

Detect system issues in production:
- Health check endpoints
- Performance monitoring (latency, throughput)
- Error rate tracking
- Data quality monitors (missing transactions, schema violations)
- Anomaly detection (sudden persona distribution changes)
- Alert configuration
- Dashboard for system health
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from collections import defaultdict
from statistics import mean, median

from personas.persona_prioritization import assign_personas_with_prioritization
from personas.persona_definition import PersonaType
from ingest.queries import get_accounts_by_customer, get_transactions_by_customer
from ingest.database import get_connection


@dataclass
class HealthCheck:
    """System health check result."""
    component: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    timestamp: datetime
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}


@dataclass
class PerformanceMetrics:
    """Performance monitoring metrics."""
    timestamp: datetime
    latency_p50: float  # 50th percentile latency
    latency_p95: float  # 95th percentile latency
    latency_p99: float  # 99th percentile latency
    throughput: float  # requests per second
    error_rate: float  # percentage of errors
    active_users: int


@dataclass
class DataQualityAlert:
    """Data quality alert."""
    alert_id: str
    alert_type: str  # "missing_transactions", "schema_violation", "orphaned_records"
    severity: str  # "low", "medium", "high", "critical"
    message: str
    timestamp: datetime
    affected_count: int
    resolution: Optional[str] = None


@dataclass
class AnomalyAlert:
    """Anomaly detection alert."""
    alert_id: str
    anomaly_type: str  # "persona_distribution_change", "latency_spike", "error_rate_spike"
    severity: str
    message: str
    timestamp: datetime
    baseline_value: float
    current_value: float
    deviation_percentage: float


@dataclass
class SystemHealth:
    """Complete system health status."""
    timestamp: datetime
    overall_status: str  # "healthy", "degraded", "unhealthy"
    health_checks: List[HealthCheck]
    performance_metrics: Optional[PerformanceMetrics] = None
    data_quality_alerts: List[DataQualityAlert] = []
    anomaly_alerts: List[AnomalyAlert] = []
    health_score: float = 0.0


def check_database_health(db_path: str) -> HealthCheck:
    """
    Check database health.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        HealthCheck object
    """
    try:
        from pathlib import Path
        
        if not Path(db_path).exists():
            return HealthCheck(
                component="database",
                status="unhealthy",
                message="Database file not found",
                timestamp=datetime.now()
            )
        
        # Check database connection
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM accounts")
            account_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM transactions")
            transaction_count = cursor.fetchone()[0]
            
            return HealthCheck(
                component="database",
                status="healthy",
                message="Database connection successful",
                timestamp=datetime.now(),
                metrics={
                    "account_count": account_count,
                    "transaction_count": transaction_count
                }
            )
    except Exception as e:
        return HealthCheck(
            component="database",
            status="unhealthy",
            message=f"Database error: {str(e)}",
            timestamp=datetime.now()
        )


def check_data_quality(db_path: str) -> List[DataQualityAlert]:
    """
    Check data quality and return alerts.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        List of DataQualityAlert objects
    """
    alerts = []
    
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Check for orphaned transactions
            cursor.execute("""
                SELECT COUNT(*) FROM transactions t
                LEFT JOIN accounts a ON t.account_id = a.account_id
                WHERE a.account_id IS NULL
            """)
            orphaned_count = cursor.fetchone()[0]
            
            if orphaned_count > 0:
                alerts.append(DataQualityAlert(
                    alert_id=f"DQ-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    alert_type="orphaned_records",
                    severity="high",
                    message=f"Found {orphaned_count} orphaned transactions",
                    timestamp=datetime.now(),
                    affected_count=orphaned_count
                ))
            
            # Check for missing account balances
            cursor.execute("""
                SELECT COUNT(*) FROM accounts
                WHERE balances_current IS NULL
            """)
            missing_balances = cursor.fetchone()[0]
            
            if missing_balances > 0:
                alerts.append(DataQualityAlert(
                    alert_id=f"DQ-{datetime.now().strftime('%Y%m%d%H%M%S')}-2",
                    alert_type="missing_data",
                    severity="medium",
                    message=f"Found {missing_balances} accounts with missing balances",
                    timestamp=datetime.now(),
                    affected_count=missing_balances
                ))
            
            # Check for accounts without transactions (could be new accounts)
            cursor.execute("""
                SELECT a.account_id FROM accounts a
                LEFT JOIN transactions t ON a.account_id = t.account_id
                WHERE t.transaction_id IS NULL
            """)
            accounts_without_transactions = len(cursor.fetchall())
            
            if accounts_without_transactions > 10:  # Threshold
                alerts.append(DataQualityAlert(
                    alert_id=f"DQ-{datetime.now().strftime('%Y%m%d%H%M%S')}-3",
                    alert_type="missing_transactions",
                    severity="low",
                    message=f"Found {accounts_without_transactions} accounts without transactions (may be new accounts)",
                    timestamp=datetime.now(),
                    affected_count=accounts_without_transactions
                ))
    
    except Exception as e:
        alerts.append(DataQualityAlert(
            alert_id=f"DQ-ERROR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            alert_type="data_quality_check_error",
            severity="critical",
            message=f"Error checking data quality: {str(e)}",
            timestamp=datetime.now(),
            affected_count=0
        ))
    
    return alerts


def detect_persona_distribution_anomaly(
    user_ids: List[str],
    db_path: str,
    baseline_distribution: Optional[Dict[str, float]] = None
) -> Optional[AnomalyAlert]:
    """
    Detect anomalies in persona distribution.
    
    Args:
        user_ids: List of user IDs
        db_path: Path to SQLite database
        baseline_distribution: Optional baseline persona distribution
        
    Returns:
        AnomalyAlert object or None
    """
    # Calculate current persona distribution
    persona_counts = defaultdict(int)
    total_users = 0
    
    for user_id in user_ids[:100]:  # Sample first 100 users
        try:
            persona_assignment = assign_personas_with_prioritization(user_id, db_path)
            if persona_assignment.primary_persona:
                persona_type = persona_assignment.primary_persona.persona_type.value
                persona_counts[persona_type] += 1
                total_users += 1
        except Exception:
            pass
    
    if total_users == 0:
        return None
    
    # Calculate percentages
    current_distribution = {
        persona: (count / total_users * 100)
        for persona, count in persona_counts.items()
    }
    
    # Compare with baseline (if provided)
    if baseline_distribution:
        for persona, current_pct in current_distribution.items():
            baseline_pct = baseline_distribution.get(persona, 0.0)
            
            if baseline_pct > 0:
                deviation = abs(current_pct - baseline_pct) / baseline_pct * 100
                
                # Alert if deviation > 20%
                if deviation > 20:
                    return AnomalyAlert(
                        alert_id=f"ANOM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        anomaly_type="persona_distribution_change",
                        severity="medium",
                        message=f"Persona distribution change detected for {persona}: {deviation:.1f}% deviation",
                        timestamp=datetime.now(),
                        baseline_value=baseline_pct,
                        current_value=current_pct,
                        deviation_percentage=deviation
                    )
    
    return None


def monitor_performance(
    user_ids: List[str],
    db_path: str
) -> PerformanceMetrics:
    """
    Monitor system performance.
    
    Args:
        user_ids: List of user IDs to test
        db_path: Path to SQLite database
        
    Returns:
        PerformanceMetrics object
    """
    import time
    
    latencies = []
    errors = 0
    total_requests = 0
    
    # Sample performance test
    for user_id in user_ids[:10]:  # Test with 10 users
        try:
            start_time = time.time()
            
            # Test persona assignment
            assign_personas_with_prioritization(user_id, db_path)
            
            latency = time.time() - start_time
            latencies.append(latency)
            total_requests += 1
        except Exception:
            errors += 1
            total_requests += 1
    
    if latencies:
        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)
        
        latency_p50 = sorted_latencies[n // 2]
        latency_p95 = sorted_latencies[int(n * 0.95)] if n > 1 else sorted_latencies[0]
        latency_p99 = sorted_latencies[int(n * 0.99)] if n > 1 else sorted_latencies[0]
    else:
        latency_p50 = latency_p95 = latency_p99 = 0.0
    
    total_time = sum(latencies) if latencies else 1.0
    throughput = total_requests / total_time if total_time > 0 else 0.0
    error_rate = (errors / total_requests * 100) if total_requests > 0 else 0.0
    
    return PerformanceMetrics(
        timestamp=datetime.now(),
        latency_p50=latency_p50,
        latency_p95=latency_p95,
        latency_p99=latency_p99,
        throughput=throughput,
        error_rate=error_rate,
        active_users=len(user_ids)
    )


def check_system_health(
    user_ids: List[str],
    db_path: str
) -> SystemHealth:
    """
    Check overall system health.
    
    Args:
        user_ids: List of user IDs
        db_path: Path to SQLite database
        
    Returns:
        SystemHealth object
    """
    health_checks = []
    
    # Database health
    db_health = check_database_health(db_path)
    health_checks.append(db_health)
    
    # Data quality
    data_quality_alerts = check_data_quality(db_path)
    
    # Performance monitoring
    performance_metrics = monitor_performance(user_ids, db_path)
    
    # Anomaly detection
    anomaly_alerts = []
    persona_anomaly = detect_persona_distribution_anomaly(user_ids, db_path)
    if persona_anomaly:
        anomaly_alerts.append(persona_anomaly)
    
    # Calculate overall health score
    health_score = 100.0
    
    # Deduct points for issues
    if db_health.status != "healthy":
        health_score -= 30
    
    health_score -= len(data_quality_alerts) * 5
    health_score -= len(anomaly_alerts) * 10
    
    if performance_metrics.error_rate > 5:
        health_score -= 20
    
    if performance_metrics.latency_p95 > 5.0:  # > 5 seconds
        health_score -= 15
    
    health_score = max(0, health_score)
    
    # Determine overall status
    if health_score >= 90:
        overall_status = "healthy"
    elif health_score >= 70:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    return SystemHealth(
        timestamp=datetime.now(),
        overall_status=overall_status,
        health_checks=health_checks,
        performance_metrics=performance_metrics,
        data_quality_alerts=data_quality_alerts,
        anomaly_alerts=anomaly_alerts,
        health_score=health_score
    )


def generate_health_report(
    system_health: SystemHealth,
    output_path: str
) -> None:
    """
    Generate system health report.
    
    Args:
        system_health: SystemHealth object
        output_path: Path to output report file
    """
    report = f"""
System Health Report
Generated: {system_health.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

================================================================================
OVERALL STATUS
================================================================================
Status: {system_health.overall_status.upper()}
Health Score: {system_health.health_score:.1f}/100

================================================================================
HEALTH CHECKS
================================================================================
"""
    
    for check in system_health.health_checks:
        status_icon = "✓" if check.status == "healthy" else "✗"
        report += f"\n{status_icon} {check.component.upper()}: {check.status}\n"
        report += f"  Message: {check.message}\n"
        if check.metrics:
            report += "  Metrics:\n"
            for key, value in check.metrics.items():
                report += f"    - {key}: {value}\n"
    
    if system_health.performance_metrics:
        report += "\n================================================================================\n"
        report += "PERFORMANCE METRICS\n"
        report += "================================================================================\n"
        pm = system_health.performance_metrics
        report += f"  P50 Latency: {pm.latency_p50:.2f}s\n"
        report += f"  P95 Latency: {pm.latency_p95:.2f}s\n"
        report += f"  P99 Latency: {pm.latency_p99:.2f}s\n"
        report += f"  Throughput: {pm.throughput:.2f} requests/second\n"
        report += f"  Error Rate: {pm.error_rate:.1f}%\n"
        report += f"  Active Users: {pm.active_users}\n"
    
    if system_health.data_quality_alerts:
        report += "\n================================================================================\n"
        report += "DATA QUALITY ALERTS\n"
        report += "================================================================================\n"
        for alert in system_health.data_quality_alerts:
            report += f"\n{alert.severity.upper()} - {alert.alert_type}\n"
            report += f"  Message: {alert.message}\n"
            report += f"  Affected Count: {alert.affected_count}\n"
    
    if system_health.anomaly_alerts:
        report += "\n================================================================================\n"
        report += "ANOMALY ALERTS\n"
        report += "================================================================================\n"
        for alert in system_health.anomaly_alerts:
            report += f"\n{alert.severity.upper()} - {alert.anomaly_type}\n"
            report += f"  Message: {alert.message}\n"
            report += f"  Deviation: {alert.deviation_percentage:.1f}%\n"
    
    report += "\n" + "=" * 60 + "\n"
    
    with open(output_path, 'w') as f:
        f.write(report)

