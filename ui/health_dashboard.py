"""
Health Check Dashboard for SpendSenseAI.

Real-time system health monitoring dashboard with:
- Real-time metrics display
- System status indicators
- User activity tracking
- Data quality dashboard
- Cost tracking (LLM API costs)
- Export capabilities
"""

import streamlit as st
import requests
import json
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os
import time

# API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def get_health_data() -> Optional[Dict]:
    """Fetch system health data from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/health/full", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching health data: {e}")
        return None


def get_performance_metrics() -> Optional[Dict]:
    """Fetch performance metrics from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/health/performance", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching performance metrics: {e}")
        return None


def get_data_quality_alerts() -> Optional[Dict]:
    """Fetch data quality alerts from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/health/data-quality", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching data quality alerts: {e}")
        return None


def get_dashboard_metrics() -> Optional[Dict]:
    """Fetch comprehensive dashboard metrics from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/health/dashboard", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching dashboard metrics: {e}")
        return None


def format_currency(amount: float) -> str:
    """Format amount as currency."""
    return f"${amount:,.2f}"


def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value:.1f}%"


def get_status_color(status: str) -> str:
    """Get color for status indicator."""
    colors = {
        "healthy": "#28a745",
        "degraded": "#ffc107",
        "unhealthy": "#dc3545",
        "down": "#dc3545"
    }
    return colors.get(status.lower(), "#6c757d")


def show_health_dashboard():
    """Display the health check dashboard."""
    st.title("🏥 System Health Dashboard")
    st.markdown("---")
    
    # Auto-refresh control
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        auto_refresh = st.checkbox("Auto-refresh", value=False)
    with col2:
        refresh_interval = st.selectbox("Interval", [5, 10, 30, 60], index=1, format_func=lambda x: f"{x}s")
    
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()
    
    with col3:
        if st.button("🔄 Refresh Now"):
            st.rerun()
    
    st.markdown("---")
    
    # Fetch dashboard data
    dashboard_data = get_dashboard_metrics()
    
    if not dashboard_data:
        st.warning("Unable to fetch dashboard data. Please ensure the API is running.")
        return
    
    # Overall Status Section
    st.header("📊 Overall System Status")
    
    overall_status = dashboard_data.get("overall_status", "unknown")
    health_score = dashboard_data.get("health_score", 0.0)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_color = get_status_color(overall_status)
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background-color: {status_color}20; border-radius: 10px;">
            <h3 style="color: {status_color}; margin: 0;">{overall_status.upper()}</h3>
            <p style="margin: 5px 0 0 0; font-size: 14px;">System Status</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric("Health Score", f"{health_score:.1f}/100")
    
    with col3:
        uptime = dashboard_data.get("uptime_seconds", 0)
        uptime_hours = uptime / 3600
        st.metric("Uptime", f"{uptime_hours:.1f} hours")
    
    with col4:
        active_alerts = dashboard_data.get("active_alerts_count", 0)
        st.metric("Active Alerts", active_alerts)
    
    st.markdown("---")
    
    # Performance Metrics Section
    st.header("⚡ Performance Metrics")
    
    perf_metrics = dashboard_data.get("performance_metrics", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        latency_p50 = perf_metrics.get("latency_p50", 0.0)
        st.metric("P50 Latency", f"{latency_p50*1000:.0f}ms")
    
    with col2:
        latency_p95 = perf_metrics.get("latency_p95", 0.0)
        st.metric("P95 Latency", f"{latency_p95*1000:.0f}ms")
    
    with col3:
        throughput = perf_metrics.get("throughput", 0.0)
        st.metric("Throughput", f"{throughput:.1f} req/s")
    
    with col4:
        error_rate = perf_metrics.get("error_rate", 0.0)
        st.metric("Error Rate", format_percentage(error_rate))
    
    # Latency Chart
    if "latency_history" in perf_metrics:
        st.subheader("Latency Over Time")
        latency_df = pd.DataFrame(perf_metrics["latency_history"])
        if not latency_df.empty:
            st.line_chart(latency_df.set_index("timestamp")[["p50", "p95", "p99"]])
    
    st.markdown("---")
    
    # User Activity Section
    st.header("👥 User Activity")
    
    user_activity = dashboard_data.get("user_activity", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        active_today = user_activity.get("active_today", 0)
        st.metric("Active Today", active_today)
    
    with col2:
        active_week = user_activity.get("active_week", 0)
        st.metric("Active This Week", active_week)
    
    with col3:
        recommendations_served = user_activity.get("recommendations_served_today", 0)
        st.metric("Recommendations Today", recommendations_served)
    
    with col4:
        consent_granted = user_activity.get("consent_granted_today", 0)
        st.metric("Consent Granted Today", consent_granted)
    
    st.markdown("---")
    
    # Data Quality Section
    st.header("🔍 Data Quality")
    
    data_quality = dashboard_data.get("data_quality", {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_accounts = data_quality.get("total_accounts", 0)
        st.metric("Total Accounts", total_accounts)
    
    with col2:
        total_transactions = data_quality.get("total_transactions", 0)
        st.metric("Total Transactions", total_transactions)
    
    with col3:
        data_freshness = data_quality.get("data_freshness_hours", 0)
        st.metric("Data Freshness", f"{data_freshness:.1f} hours")
    
    # Data Quality Alerts
    alerts = data_quality.get("alerts", [])
    if alerts:
        st.subheader("Data Quality Alerts")
        for alert in alerts:
            severity = alert.get("severity", "info")
            severity_color = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
                "info": "🔵"
            }.get(severity.lower(), "⚪")
            
            st.warning(f"{severity_color} **{alert.get('alert_type', 'Unknown')}**: {alert.get('message', 'No message')} (Affected: {alert.get('affected_count', 0)})")
    
    st.markdown("---")
    
    # Cost Tracking Section
    st.header("💰 Cost Tracking")
    
    cost_data = dashboard_data.get("costs", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        llm_cost_today = cost_data.get("llm_cost_today", 0.0)
        st.metric("LLM Cost Today", format_currency(llm_cost_today))
    
    with col2:
        llm_cost_month = cost_data.get("llm_cost_month", 0.0)
        st.metric("LLM Cost This Month", format_currency(llm_cost_month))
    
    with col3:
        total_requests = cost_data.get("llm_requests_today", 0)
        st.metric("LLM Requests Today", total_requests)
    
    with col4:
        avg_cost_per_request = cost_data.get("avg_cost_per_request", 0.0)
        st.metric("Avg Cost/Request", format_currency(avg_cost_per_request))
    
    # Cost Chart
    if "cost_history" in cost_data:
        st.subheader("Cost Over Time")
        cost_df = pd.DataFrame(cost_data["cost_history"])
        if not cost_df.empty:
            st.line_chart(cost_df.set_index("date")[["daily_cost"]])
    
    st.markdown("---")
    
    # Export Section
    st.header("📥 Export Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Export to JSON"):
            json_str = json.dumps(dashboard_data, indent=2, default=str)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name=f"health_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📊 Export to CSV"):
            # Create CSV from key metrics
            metrics_data = {
                "timestamp": [datetime.now().isoformat()],
                "health_score": [health_score],
                "overall_status": [overall_status],
                "latency_p50": [latency_p50],
                "latency_p95": [latency_p95],
                "throughput": [throughput],
                "error_rate": [error_rate],
                "active_users_today": [active_today],
                "llm_cost_today": [llm_cost_today]
            }
            df = pd.DataFrame(metrics_data)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"health_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )


if __name__ == "__main__":
    show_health_dashboard()

