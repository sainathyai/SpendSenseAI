"""
Operator Dashboard UI for SpendSenseAI.

Provides internal oversight interface:
- User search and selection
- Signal visualization (charts for utilization, savings, income)
- Persona assignment display (30d and 180d)
- Recommendation list with rationales
- Decision trace viewer (expandable JSON/tree view)
- Approve/reject/override controls
- Flag-for-review functionality
- Override reason capture
- Audit log view
"""

import streamlit as st
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

# API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="SpendSenseAI Operator Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# Helper Functions
# ============================================================================

def api_request(method: str, endpoint: str, **kwargs) -> Optional[Dict]:
    """Make API request and return JSON response."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.request(method, url, **kwargs)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            st.error(f"Resource not found: {endpoint}")
            return None
        else:
            st.error(f"API Error ({response.status_code}): {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(f"Unable to connect to API at {API_BASE_URL}. Is the API server running?")
        return None
    except Exception as e:
        st.error(f"Error making API request: {str(e)}")
        return None


def format_persona(persona: Optional[Dict]) -> str:
    """Format persona for display."""
    if not persona:
        return "None"
    return f"{persona['persona_type'].replace('_', ' ').title()} ({persona['confidence_score']:.1%})"


def format_signal(signal: Dict) -> str:
    """Format signal for display."""
    signal_type = signal['signal_type'].replace('_', ' ').title()
    metrics = signal.get('metrics', {})
    
    if signal_type == "Credit Utilization":
        return f"{signal_type}: {metrics.get('aggregate_utilization', 0):.1f}%"
    elif signal_type == "Savings":
        return f"{signal_type}: ${metrics.get('total_savings_balance', 0):,.2f}"
    elif signal_type == "Subscription":
        return f"{signal_type}: {metrics.get('subscription_count', 0)} active"
    elif signal_type == "Income":
        return f"{signal_type}: {metrics.get('median_pay_gap_days', 0):.1f} day gap"
    else:
        return signal_type


# ============================================================================
# Main Dashboard
# ============================================================================

def main():
    """Main dashboard function."""
    st.title("📊 SpendSenseAI Operator Dashboard")
    st.markdown("---")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Pending Reviews", "User Search", "Decision Traces", "Audit Log"]
    )
    
    # API health check
    health = api_request("GET", "/health")
    if health:
        status_color = "🟢" if health.get("status") == "healthy" else "🔴"
        st.sidebar.markdown(f"{status_color} API Status: {health.get('status', 'unknown')}")
    else:
        st.sidebar.markdown("🔴 API Status: Disconnected")
    
    # Route to appropriate page
    if page == "Pending Reviews":
        show_pending_reviews()
    elif page == "User Search":
        show_user_search()
    elif page == "Decision Traces":
        show_decision_traces()
    elif page == "Audit Log":
        show_audit_log()


# ============================================================================
# Pending Reviews Page
# ============================================================================

def show_pending_reviews():
    """Show pending reviews queue."""
    st.header("Pending Reviews")
    st.markdown("Review and approve/reject recommendations")
    
    # Get pending reviews
    data = api_request("GET", "/operator/review")
    
    if not data:
        st.info("No pending reviews or API connection error.")
        return
    
    pending_count = data.get("pending_count", 0)
    reviews = data.get("reviews", [])
    
    if pending_count == 0:
        st.success("✅ No pending reviews!")
        return
    
    st.metric("Pending Reviews", pending_count)
    
    # Display each pending review
    for i, review in enumerate(reviews):
        with st.expander(f"Review #{i+1} - User: {review.get('user_id', 'Unknown')} - {review.get('timestamp', '')[:10]}"):
            display_review_details(review)


def display_review_details(review: Dict):
    """Display details of a review."""
    user_id = review.get("user_id", "Unknown")
    trace_id = review.get("trace_id", "Unknown")
    
    # Get full profile
    profile = api_request("GET", f"/profile/{user_id}")
    recommendations = api_request("GET", f"/recommendations/{user_id}?check_consent=false")
    
    # Display persona assignment
    st.subheader("Persona Assignment")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Primary Persona", format_persona(recommendations.get("persona", {}).get("primary") if recommendations else None))
    
    with col2:
        st.metric("30-Day Window", format_persona(recommendations.get("persona", {}).get("window_30d") if recommendations else None))
    
    with col3:
        st.metric("180-Day Window", format_persona(recommendations.get("persona", {}).get("window_180d") if recommendations else None))
    
    with col4:
        st.metric("Secondary Persona", format_persona(recommendations.get("persona", {}).get("secondary") if recommendations else None))
    
    # Display signals
    if profile:
        st.subheader("Behavioral Signals")
        signals = profile.get("signals", [])
        for signal in signals:
            st.write(f"• {format_signal(signal)}")
    
    # Display recommendations
    if recommendations:
        st.subheader("Recommendations")
        
        # Education items
        if recommendations.get("education_items"):
            st.write("**Education Content:**")
            for item in recommendations["education_items"]:
                with st.expander(f"{item.get('title', 'Unknown')} - Priority {item.get('priority', 0)}"):
                    st.write(f"**Description:** {item.get('description', 'N/A')}")
                    st.write(f"**Rationale:** {item.get('rationale', 'N/A')}")
        
        # Partner offers
        if recommendations.get("partner_offers"):
            st.write("**Partner Offers:**")
            for offer in recommendations["partner_offers"]:
                with st.expander(f"{offer.get('title', 'Unknown')} - Priority {offer.get('priority', 0)}"):
                    st.write(f"**Description:** {offer.get('description', 'N/A')}")
                    st.write(f"**Rationale:** {offer.get('rationale', 'N/A')}")
    
    # Review actions
    st.subheader("Review Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("✅ Approve", key=f"approve_{trace_id}"):
            review_status("approved", trace_id, user_id)
    
    with col2:
        if st.button("❌ Reject", key=f"reject_{trace_id}"):
            review_status("rejected", trace_id, user_id)
    
    with col3:
        if st.button("🚩 Flag", key=f"flag_{trace_id}"):
            review_status("flagged", trace_id, user_id)
    
    with col4:
        if st.button("🔄 Override", key=f"override_{trace_id}"):
            review_status("overridden", trace_id, user_id)


def review_status(status: str, trace_id: str, user_id: str):
    """Update review status."""
    operator_id = st.session_state.get("operator_id", "OPERATOR001")
    
    # Create form for review
    with st.form(key=f"review_form_{trace_id}"):
        review_notes = st.text_input(f"Review Notes ({status}):", key=f"notes_{trace_id}")
        override_reason = None
        
        if status == "overridden":
            override_reason = st.text_input("Override Reason:", key=f"override_{trace_id}")
        
        submitted = st.form_submit_button(f"Confirm {status.title()}")
        
        if submitted:
            data = {
                "review_status": status,
                "reviewed_by": operator_id,
                "review_notes": review_notes,
                "override_reason": override_reason
            }
            
            result = api_request("POST", f"/operator/override/{trace_id}", json=data)
            
            if result:
                st.success(f"✅ Review {status} successfully!")
                st.rerun()


# ============================================================================
# User Search Page
# ============================================================================

def show_user_search():
    """Show user search and profile view."""
    st.header("User Search")
    st.markdown("Search for users and view their profiles")
    
    # User search
    user_id = st.text_input("Enter User ID:", key="user_search")
    
    if user_id:
        # Get user profile
        profile = api_request("GET", f"/profile/{user_id}")
        recommendations = api_request("GET", f"/recommendations/{user_id}?check_consent=false")
        
        if profile:
            display_user_profile(user_id, profile, recommendations)
        else:
            st.error(f"User {user_id} not found or profile unavailable.")


def display_user_profile(user_id: str, profile: Dict, recommendations: Optional[Dict]):
    """Display user profile details."""
    st.subheader(f"Profile for User: {user_id}")
    
    # Persona assignment
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Persona Assignment (30-Day):**")
        persona_30d = profile.get("window_30d")
        if persona_30d:
            st.write(f"- Persona: {persona_30d.get('persona_type', 'N/A').replace('_', ' ').title()}")
            st.write(f"- Confidence: {persona_30d.get('confidence_score', 0):.1%}")
    
    with col2:
        st.write("**Persona Assignment (180-Day):**")
        persona_180d = profile.get("window_180d")
        if persona_180d:
            st.write(f"- Persona: {persona_180d.get('persona_type', 'N/A').replace('_', ' ').title()}")
            st.write(f"- Confidence: {persona_180d.get('confidence_score', 0):.1%}")
    
    # Behavioral signals
    st.subheader("Behavioral Signals")
    signals = profile.get("signals", [])
    
    if signals:
        for signal in signals:
            with st.expander(format_signal(signal)):
                st.json(signal.get("metrics", {}))
    else:
        st.info("No signals detected.")
    
    # Recommendations
    if recommendations:
        st.subheader("Current Recommendations")
        
        edu_items = recommendations.get("education_items", [])
        offers = recommendations.get("partner_offers", [])
        
        st.metric("Education Items", len(edu_items))
        st.metric("Partner Offers", len(offers))
        
        # Display recommendations
        if edu_items or offers:
            for item in edu_items + offers:
                with st.expander(f"{item.get('title', 'Unknown')}"):
                    st.write(f"**Type:** {item.get('type', 'N/A').title()}")
                    st.write(f"**Rationale:** {item.get('rationale', 'N/A')}")


# ============================================================================
# Decision Traces Page
# ============================================================================

def show_decision_traces():
    """Show decision traces viewer."""
    st.header("Decision Traces")
    st.markdown("View complete decision traces for recommendations")
    
    # Search for trace
    trace_id = st.text_input("Enter Trace ID:", key="trace_search")
    
    if trace_id:
        trace = api_request("GET", f"/operator/trace/{trace_id}")
        
        if trace:
            display_trace_details(trace)
        else:
            st.error(f"Trace {trace_id} not found.")
    
    # Or search by user
    user_id = st.text_input("Enter User ID to view all traces:", key="trace_user_search")
    
    if user_id:
        traces = api_request("GET", f"/operator/traces/{user_id}")
        
        if traces:
            st.write(f"Found {len(traces)} traces for user {user_id}")
            
            for trace in traces:
                with st.expander(f"Trace: {trace.get('trace_id', 'Unknown')} - {trace.get('timestamp', '')[:10]}"):
                    display_trace_details(trace)
        else:
            st.info(f"No traces found for user {user_id}.")


def display_trace_details(trace: Dict):
    """Display decision trace details."""
    st.subheader("Trace Details")
    
    # Basic info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write(f"**Trace ID:** {trace.get('trace_id', 'N/A')}")
    
    with col2:
        st.write(f"**User ID:** {trace.get('user_id', 'N/A')}")
    
    with col3:
        st.write(f"**Status:** {trace.get('review_status', 'N/A')}")
    
    # Full trace JSON
    st.subheader("Full Trace Data")
    with st.expander("View Full JSON"):
        st.json(trace)


# ============================================================================
# Audit Log Page
# ============================================================================

def show_audit_log():
    """Show audit log."""
    st.header("Audit Log")
    st.markdown("View consent audit trail")
    
    user_id = st.text_input("Enter User ID to view audit log:", key="audit_user_search")
    
    if user_id:
        consents = api_request("GET", f"/consent/{user_id}")
        
        if consents:
            st.write(f"Found {len(consents)} consent records for user {user_id}")
            
            for consent in consents:
                with st.expander(f"Consent: {consent.get('scope', 'N/A')} - {consent.get('status', 'N/A')} - {consent.get('granted_at', 'N/A')[:10]}"):
                    st.json(consent)
        else:
            st.info(f"No consent records found for user {user_id}.")


# ============================================================================
# Run Dashboard
# ============================================================================

if __name__ == "__main__":
    main()

