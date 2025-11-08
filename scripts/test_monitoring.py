"""
Test monitoring system.

Usage:
    python -m scripts.test_monitoring
"""

from ui.monitoring import (
    check_database_health, check_data_quality,
    check_performance_metrics, generate_alerts,
    create_monitoring_tables, save_health_metrics,
    save_alert, get_active_alerts, get_recent_health_metrics
)
from pathlib import Path
from datetime import datetime

db_path = 'data/spendsense.db'

print("="*60)
print("Testing Monitoring System")
print("="*60)
print()

# Create monitoring tables
print("[STEP 1] Creating monitoring tables...")
create_monitoring_tables(db_path)
print("   [SUCCESS] Monitoring tables created")

print()

# Check database health
print("[STEP 2] Checking database health...")
db_health = check_database_health(db_path)
print(f"   Status: {db_health['status']}")
print(f"   Connected: {db_health['connected']}")
print(f"   Table Count: {db_health.get('table_count', 0)}")

print()

# Check data quality
print("[STEP 3] Checking data quality...")
data_quality_issues = check_data_quality(db_path)
print(f"   Issues Found: {len(data_quality_issues)}")
for issue in data_quality_issues:
    print(f"   - {issue.issue_type}: {issue.description}")

print()

# Check performance metrics
print("[STEP 4] Checking performance metrics...")
health_metrics = check_performance_metrics(db_path)
print(f"   System Status: {health_metrics.status.value}")
print(f"   Latency P95: {health_metrics.latency_p95:.2f}s")
print(f"   Error Rate: {health_metrics.error_rate:.2%}")
print(f"   Throughput: {health_metrics.throughput:.2f} requests/s")

# Save metrics
save_health_metrics(health_metrics, db_path)

print()

# Generate alerts
print("[STEP 5] Generating alerts...")
alerts = generate_alerts(db_path, health_metrics, data_quality_issues)
print(f"   Alerts Generated: {len(alerts)}")

for alert in alerts:
    print(f"   - [{alert.level.value.upper()}] {alert.title}: {alert.message}")
    save_alert(alert, db_path)

print()

# Get active alerts
print("[STEP 6] Retrieving active alerts...")
active_alerts = get_active_alerts(db_path)
print(f"   Active Alerts: {len(active_alerts)}")

print()

# Get recent health metrics
print("[STEP 7] Retrieving recent health metrics...")
recent_metrics = get_recent_health_metrics(db_path, hours=24)
print(f"   Recent Metrics (24h): {len(recent_metrics)}")

print("\n" + "="*60)
print("[SUCCESS] Monitoring system tested successfully!")
print("="*60)

