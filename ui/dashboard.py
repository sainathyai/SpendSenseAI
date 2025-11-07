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
import logging
import traceback

# Import query tool and styles
from ui.query_tool import render_query_tool
from ui.styles import get_custom_css, get_status_badge, get_action_dot

# Configure logging to show in console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
    ]
)
logger = logging.getLogger(__name__)

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

def api_request(method: str, endpoint: str, params: Optional[Dict] = None, **kwargs) -> Optional[Dict]:
    """Make API request and return JSON response."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        # Log request for debugging
        logger.debug(f"Making {method} request to {url} with params: {params}")
        print(f"[DEBUG] Making {method} request to {url} with params: {params}")
        
        # Handle params properly
        if params:
            kwargs['params'] = params
        
        response = requests.request(method, url, **kwargs)
        
        # Log response for debugging
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response body: {response.text[:200]}")
        print(f"[DEBUG] Response status: {response.status_code}")
        print(f"[DEBUG] Response body: {response.text[:200]}")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            error_msg = f"Resource not found: {endpoint}"
            st.error(error_msg)
            logger.error(error_msg)
            print(f"[ERROR] {error_msg}")
            return None
        else:
            error_msg = f"API Error ({response.status_code}): {response.text}"
            st.error(error_msg)
            logger.error(error_msg)
            print(f"[ERROR] {error_msg}")
            return None
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Unable to connect to API at {API_BASE_URL}. Is the API server running?"
        st.error(error_msg)
        logger.error(f"{error_msg} - {str(e)}")
        print(f"[ERROR] {error_msg} - {str(e)}")
        traceback.print_exc()
        return None
    except Exception as e:
        error_msg = f"Error making API request: {str(e)}"
        st.error(error_msg)
        logger.error(error_msg)
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
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
    # Inject custom CSS
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    st.title("📊 SpendSenseAI Operator Dashboard")
    st.markdown("---")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["All Recommendations", "Pending Reviews", "User Search", "Query Tool", "Decision Traces", "Audit Log", "System Health"]
    )
    
    # API health check
    health = api_request("GET", "/health")
    if health:
        status_color = "🟢" if health.get("status") == "healthy" else "🔴"
        st.sidebar.markdown(f"{status_color} API Status: {health.get('status', 'unknown')}")
    else:
        st.sidebar.markdown("🔴 API Status: Disconnected")
    
    # Route to appropriate page
    if page == "All Recommendations":
        show_all_recommendations()
    elif page == "Model Review Portal":
        show_model_review_portal()
    elif page == "Pending Reviews":
        show_pending_reviews()
    elif page == "User Search":
        show_user_search()
    elif page == "Query Tool":
        show_query_tool()
    elif page == "Decision Traces":
        show_decision_traces()
    elif page == "Audit Log":
        show_audit_log()
    elif page == "System Health":
        from ui.health_dashboard import show_health_dashboard
        show_health_dashboard()


# ============================================================================
# All Recommendations Page
# ============================================================================

def show_all_recommendations():
    """Show all recommendations with detailed information including courses."""
    st.header("📚 All Recommendations Review")
    st.markdown("Comprehensive view of all recommendations, educational content, and partner offers")
    
    # Tabs for search and table view
    tab1, tab2 = st.tabs(["🔍 Search User", "📊 All Users Table"])
    
    with tab1:
        # Autocomplete search
        search_query = st.text_input(
            "Search User ID (type to see suggestions):", 
            key="all_rec_user_search", 
            placeholder="e.g., CUST000001"
        )
        
        # Get suggestions as user types
        suggestions = []
        if search_query and len(search_query) >= 1:
            suggestions_data = api_request("GET", f"/users/search/suggestions?query={search_query}&limit=10")
            if suggestions_data:
                suggestions = suggestions_data.get("suggestions", [])
        
        # Display suggestions
        if suggestions:
            st.markdown("**Suggestions:**")
            suggestion_cols = st.columns(min(len(suggestions), 5))
            for idx, suggestion in enumerate(suggestions[:5]):
                with suggestion_cols[idx % len(suggestion_cols)]:
                    if st.button(suggestion, key=f"suggestion_{suggestion}", use_container_width=True):
                        st.session_state['selected_user'] = suggestion
                        search_query = suggestion
        
        # Check if user was selected from suggestions
        selected_user = st.session_state.get('selected_user', search_query if search_query and search_query in suggestions else None)
        user_id = selected_user if selected_user else search_query
        
        if user_id:
            with st.spinner("Loading recommendations..."):
                recommendations = api_request("GET", f"/recommendations/{user_id}?check_consent=false")
                profile = api_request("GET", f"/profile/{user_id}")
                
                if recommendations:
                    display_full_recommendations(user_id, recommendations, profile)
                else:
                    st.error(f"❌ No recommendations found for user {user_id}. The user may not exist or may not have sufficient transaction data.")
        
        # Clear selected user after use
        if 'selected_user' in st.session_state:
            del st.session_state['selected_user']
    
    with tab2:
        # All Users Table View
        st.subheader("📊 All Users")
        
        # Get all users
        with st.spinner("Loading users..."):
            try:
                users_data = api_request("GET", "/users", params={"limit": 1000})
            except Exception as e:
                st.error(f"Error loading users: {str(e)}")
                users_data = None
        
        if users_data and users_data.get("users"):
            users = users_data.get("users", [])
            total = users_data.get("total", len(users))
            
            st.metric("Total Users", total)
            
            # Search/filter
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                table_search = st.text_input("Filter by User ID:", key="table_search", placeholder="Type to filter...")
            with filter_col2:
                sort_by = st.selectbox("Sort by:", ["Customer ID", "Account Count", "Transaction Count", "Total Balance"], key="table_sort")
            
            # Filter users
            filtered_users = users
            if table_search:
                filtered_users = [u for u in users if table_search.lower() in u.get('customer_id', '').lower()]
            
            # Sort users
            if sort_by == "Customer ID":
                filtered_users = sorted(filtered_users, key=lambda x: x.get('customer_id', ''))
            elif sort_by == "Account Count":
                filtered_users = sorted(filtered_users, key=lambda x: x.get('account_count', 0), reverse=True)
            elif sort_by == "Transaction Count":
                filtered_users = sorted(filtered_users, key=lambda x: x.get('transaction_count', 0), reverse=True)
            elif sort_by == "Total Balance":
                filtered_users = sorted(filtered_users, key=lambda x: x.get('total_balance', 0), reverse=True)
            
            if filtered_users:
                # Prepare data for table
                table_data = []
                for user in filtered_users:
                    account_types = user.get('account_types', {})
                    account_types_str = ", ".join([f"{k}: {v}" for k, v in account_types.items()])
                    
                    table_data.append({
                        "User ID": user.get('customer_id', 'N/A'),
                        "Accounts": user.get('account_count', 0),
                        "Transactions": user.get('transaction_count', 0),
                        "Total Balance": f"${user.get('total_balance', 0):,.2f}",
                        "Account Types": account_types_str
                    })
                
                # Display table
                st.dataframe(
                    table_data,
                    use_container_width=True,
                    hide_index=True,
                    height=400
                )
                
                # Click to view recommendations
                st.markdown("---")
                st.markdown("**Click a user ID above to view their recommendations:**")
                selected_user_id = st.selectbox(
                    "Select User ID to View Recommendations:",
                    [""] + [u.get('customer_id') for u in filtered_users],
                    key="table_user_select"
                )
                
                if selected_user_id:
                    with st.spinner("Loading recommendations..."):
                        recommendations = api_request("GET", f"/recommendations/{selected_user_id}?check_consent=false")
                        profile = api_request("GET", f"/profile/{selected_user_id}")
                        
                        if recommendations:
                            st.markdown("---")
                            display_full_recommendations(selected_user_id, recommendations, profile)
            else:
                st.info("No users found matching the filter.")
        else:
            st.info("No users found in the database.")
    
    # Show recent recommendations from pending reviews
    st.markdown("---")
    st.subheader("📋 Recent Recommendations (Pending Review)")
    
    pending_data = api_request("GET", "/operator/review")
    
    if pending_data and pending_data.get("pending_count", 0) > 0:
        reviews = pending_data.get("reviews", [])[:5]  # Show first 5
        
        for i, review in enumerate(reviews):
            user_id_recent = review.get("user_id", "Unknown")
            timestamp = review.get("timestamp", "")
            
            with st.expander(f"👤 User: {user_id_recent} | 📅 {timestamp[:10] if timestamp else 'Unknown'}"):
                user_recs = api_request("GET", f"/recommendations/{user_id_recent}?check_consent=false")
                user_profile = api_request("GET", f"/profile/{user_id_recent}")
                
                if user_recs:
                    display_full_recommendations(user_id_recent, user_recs, user_profile)
    else:
        st.info("💡 No pending reviews. Search for a user ID above to view their recommendations, or use 'User Search' to find users.")


def display_full_recommendations(user_id: str, recommendations: Dict, profile: Optional[Dict] = None):
    """Display comprehensive recommendations view with all details."""
    
    # User Info Header
    st.subheader(f"👤 User: {user_id}")
    
    # Persona Assignment
    persona_info = recommendations.get("persona", {})
    if persona_info:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            primary = persona_info.get("primary")
            if primary:
                st.metric("Primary Persona", primary.replace("_", " ").title(), help="Main persona assigned based on behavioral signals")
        
        with col2:
            window_30d = persona_info.get("window_30d")
            if window_30d:
                st.metric("30-Day Window", window_30d.replace("_", " ").title())
        
        with col3:
            window_180d = persona_info.get("window_180d")
            if window_180d:
                st.metric("180-Day Window", window_180d.replace("_", " ").title())
        
        with col4:
            secondary = persona_info.get("secondary")
            if secondary:
                st.metric("Secondary Persona", secondary.replace("_", " ").title())
    
    # Behavioral Signals (if profile available)
    if profile:
        st.markdown("### 📊 Behavioral Signals")
        signals = profile.get("signals", [])
        
        if signals:
            signal_cols = st.columns(min(len(signals), 4))
            
            for idx, signal in enumerate(signals):
                with signal_cols[idx % len(signal_cols)]:
                    signal_type = signal.get("signal_type", "unknown")
                    metrics = signal.get("metrics", {})
                    
                    st.markdown(f"**{signal_type.replace('_', ' ').title()}**")
                    if isinstance(metrics, dict):
                        for key, value in list(metrics.items())[:3]:  # Show first 3 metrics
                            if isinstance(value, (int, float)):
                                if "percent" in key.lower() or "utilization" in key.lower():
                                    st.write(f"  {key}: {value:.1f}%")
                                elif "amount" in key.lower() or "spend" in key.lower() or "balance" in key.lower():
                                    st.write(f"  {key}: ${value:,.2f}")
                                else:
                                    st.write(f"  {key}: {value}")
        else:
            st.info("No behavioral signals detected.")
    
    st.markdown("---")
    
    # Educational Content (Courses)
    education_items = recommendations.get("education_items", [])
    
    if education_items:
        st.markdown("### 📚 Educational Content / Courses Recommended")
        st.markdown(f"**Total Courses:** {len(education_items)}")
        
        for idx, item in enumerate(education_items, 1):
            with st.expander(
                f"📖 Course #{idx}: {item.get('title', 'Unknown')} | Priority: {item.get('priority', 0)}",
                expanded=(idx == 1)  # Expand first item by default
            ):
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    st.markdown(f"**Course Title:** {item.get('title', 'N/A')}")
                    st.markdown(f"**Description:** {item.get('description', 'N/A')}")
                    
                    # Rationale
                    rationale = item.get('rationale', 'N/A')
                    st.markdown("**Personalized Rationale:**")
                    st.info(rationale)
                
                with col_right:
                    st.markdown("**Recommendation Details**")
                    st.write(f"**ID:** {item.get('recommendation_id', 'N/A')}")
                    st.write(f"**Content ID:** {item.get('content_id', 'N/A')}")
                    st.write(f"**Priority:** {item.get('priority', 0)}")
                    st.write(f"**Type:** Education")
                    
                    # Badge for priority
                    priority = item.get('priority', 0)
                    if priority == 1:
                        st.success("🔝 High Priority")
                    elif priority <= 3:
                        st.info("📌 Medium Priority")
                    else:
                        st.warning("📋 Standard Priority")
    else:
        st.info("📚 No educational content recommended for this user.")
    
    st.markdown("---")
    
    # Partner Offers
    partner_offers = recommendations.get("partner_offers", [])
    
    if partner_offers:
        st.markdown("### 🎁 Partner Offers Recommended")
        st.markdown(f"**Total Offers:** {len(partner_offers)}")
        
        for idx, offer in enumerate(partner_offers, 1):
            with st.expander(
                f"🎁 Offer #{idx}: {offer.get('title', 'Unknown')} | Priority: {offer.get('priority', 0)}",
                expanded=(idx == 1)
            ):
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    st.markdown(f"**Offer Title:** {offer.get('title', 'N/A')}")
                    st.markdown(f"**Description:** {offer.get('description', 'N/A')}")
                    
                    # Rationale
                    rationale = offer.get('rationale', 'N/A')
                    st.markdown("**Personalized Rationale:**")
                    st.info(rationale)
                
                with col_right:
                    st.markdown("**Offer Details**")
                    st.write(f"**ID:** {offer.get('recommendation_id', 'N/A')}")
                    st.write(f"**Offer ID:** {offer.get('offer_id', 'N/A')}")
                    st.write(f"**Priority:** {offer.get('priority', 0)}")
                    st.write(f"**Type:** Partner Offer")
                    
                    # Badge for priority
                    priority = offer.get('priority', 0)
                    if priority == 1:
                        st.success("🔝 High Priority")
                    elif priority <= 3:
                        st.info("📌 Medium Priority")
                    else:
                        st.warning("📋 Standard Priority")
    else:
        st.info("🎁 No partner offers recommended for this user.")
    
    # Summary Statistics
    st.markdown("---")
    st.markdown("### 📈 Recommendation Summary")
    
    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    
    with summary_col1:
        st.metric("Total Recommendations", len(education_items) + len(partner_offers))
    
    with summary_col2:
        st.metric("Educational Courses", len(education_items))
    
    with summary_col3:
        st.metric("Partner Offers", len(partner_offers))
    
    with summary_col4:
        generated_at = recommendations.get("generated_at", "Unknown")
        if generated_at:
            st.metric("Generated", generated_at[:10] if len(generated_at) > 10 else generated_at)


# ============================================================================
# Model Review Portal Page
# ============================================================================

def show_model_review_portal():
    """Model Review Portal - Show transaction summaries by category for users."""
    st.header("🔍 Model Review Portal")
    st.markdown("**Review transaction summaries by category to understand AI recommendation basis**")
    
    # User search
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_id = st.text_input(
            "Enter User ID to review:",
            key="review_portal_user",
            placeholder="e.g., CUST000001"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_btn = st.button("🔍 Review", key="review_portal_search")
    
    if user_id or search_btn:
        if not user_id:
            st.warning("Please enter a User ID to review.")
        else:
            display_model_review(user_id)
    else:
        st.info("💡 Enter a User ID to see transaction summaries by category and understand how recommendations were generated.")


def display_model_review(user_id: str):
    """Display comprehensive model review with transaction summaries."""
    
    # Time period selector
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        days = st.selectbox("Time Period:", [30, 60, 90, 180, 365], index=2, key="review_period")
    with col2:
        show_raw_data = st.checkbox("Show Raw Data", key="show_raw_data", help="Display raw transaction data")
    
    # Get user profile and recommendations
    with st.spinner("Loading comprehensive user data..."):
        profile = api_request("GET", f"/profile/{user_id}")
        recommendations = api_request("GET", f"/recommendations/{user_id}?check_consent=false")
        signals = api_request("GET", f"/operator/signals/{user_id}")
        transaction_summary = api_request("GET", f"/operator/transactions/{user_id}/summary?days={days}")
        accounts_data = api_request("GET", f"/profile/{user_id}")  # Will include accounts
    
    if not profile:
        st.error(f"❌ User {user_id} not found or profile unavailable.")
        return
    
    # Header with user info
    st.markdown(f"## 👤 User: **{user_id}**")
    
    # Key Metrics Overview
    st.markdown("### 📊 Executive Summary")
    summary_col1, summary_col2, summary_col3, summary_col4, summary_col5 = st.columns(5)
    
    persona_info = recommendations.get("persona", {}) if recommendations else {}
    primary_persona = persona_info.get("primary", "Unknown")
    persona_confidence = 0.0
    if recommendations and recommendations.get("persona"):
        # Try to get confidence from persona data
        if isinstance(recommendations.get("persona"), dict):
            primary_persona_data = recommendations.get("persona", {}).get("primary_persona")
            if isinstance(primary_persona_data, dict):
                persona_confidence = primary_persona_data.get("confidence", 0.0)
    
    with summary_col1:
        st.metric("Assigned Persona", primary_persona.replace("_", " ").title(), 
                 delta=f"{persona_confidence:.0%} confidence" if persona_confidence > 0 else None)
    
    with summary_col2:
        signal_count = len(profile.get("signals", [])) if profile else 0
        st.metric("Behavioral Signals", signal_count)
    
    with summary_col3:
        rec_count = 0
        if recommendations:
            rec_count = len(recommendations.get("education_items", [])) + len(recommendations.get("partner_offers", []))
        st.metric("Total Recommendations", rec_count)
    
    with summary_col4:
        total_transactions = transaction_summary.get("total_transactions", 0) if transaction_summary else 0
        st.metric("Transactions", f"{total_transactions:,}", help=f"Last {days} days")
    
    with summary_col5:
        total_amount = transaction_summary.get("total_amount", 0.0) if transaction_summary else 0.0
        st.metric("Total Amount", f"${total_amount:,.2f}", help=f"Last {days} days")
    
    st.markdown("---")
    
    # Persona Assignment Details
    st.markdown("### 🎭 Persona Assignment Analysis")
    display_persona_details(recommendations, profile)
    
    st.markdown("---")
    
    # Behavioral Signals Deep Dive
    st.markdown("### 📈 Behavioral Signals Analysis")
    if profile and profile.get("signals"):
        display_comprehensive_signals(profile.get("signals", []))
    else:
        st.info("No behavioral signals detected for this user.")
    
    st.markdown("---")
    
    # Transaction Summary by Category
    st.markdown(f"### 💳 Transaction Summary by Category (Last {days} days)")
    if transaction_summary:
        display_transaction_category_summary(transaction_summary, show_raw_data)
    elif signals and signals.get("signals"):
        display_transaction_summary_by_category(user_id, signals.get("signals", []))
    else:
        st.info("Detailed transaction data not available.")
    
    st.markdown("---")
    
    # Account Information
    st.markdown("### 🏦 Account Overview")
    display_account_overview(user_id, profile)
    
    st.markdown("---")
    
    # Recommendations with Full Rationale
    if recommendations:
        st.markdown("### 🎯 Recommendations with Complete Data Citations")
        display_comprehensive_recommendations(user_id, recommendations, profile, transaction_summary)
    
    st.markdown("---")
    
    # Model Decision Path
    st.markdown("### 🔍 Complete Decision Path")
    display_complete_decision_path(user_id, profile, recommendations, signals, transaction_summary)
    
    st.markdown("---")
    
    # Actionable Insights
    st.markdown("### 💡 Operator Insights & Recommendations")
    display_operator_insights(user_id, profile, recommendations, transaction_summary)


def display_persona_details(recommendations: Dict, profile: Dict):
    """Display detailed persona assignment information."""
    
    if not recommendations or not recommendations.get("persona"):
        st.info("No persona assignment data available.")
        return
    
    persona_info = recommendations.get("persona", {})
    
    # Primary Persona
    primary = persona_info.get("primary")
    primary_data = persona_info.get("primary_persona", {})
    
    if primary:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**Primary Persona:** {primary.replace('_', ' ').title()}")
            if isinstance(primary_data, dict):
                confidence = primary_data.get("confidence", 0.0)
                st.progress(confidence, text=f"Confidence: {confidence:.0%}")
        
        with col2:
            window_30d = persona_info.get("window_30d")
            if window_30d:
                st.markdown(f"**30-Day Window:** {window_30d.replace('_', ' ').title()}")
            else:
                st.markdown("**30-Day Window:** Not Assigned")
        
        with col3:
            window_180d = persona_info.get("window_180d")
            if window_180d:
                st.markdown(f"**180-Day Window:** {window_180d.replace('_', ' ').title()}")
            else:
                st.markdown("**180-Day Window:** Not Assigned")
        
        # Criteria Met
        if isinstance(primary_data, dict) and primary_data.get("criteria_met"):
            st.markdown("**Criteria Met:**")
            criteria = primary_data.get("criteria_met", [])
            criteria_cols = st.columns(min(len(criteria), 4))
            for idx, criterion in enumerate(criteria):
                with criteria_cols[idx % len(criteria_cols)]:
                    st.success(f"✓ {criterion}")
        
        # Focus Areas
        if isinstance(primary_data, dict) and primary_data.get("focus_areas"):
            st.markdown("**Focus Areas:**")
            focus_areas = primary_data.get("focus_areas", [])
            for area in focus_areas:
                st.info(f"• {area}")
        
        # Secondary Persona
        secondary = persona_info.get("secondary")
        if secondary:
            st.markdown(f"**Secondary Persona:** {secondary.replace('_', ' ').title()}")
            secondary_data = persona_info.get("secondary_persona", {})
            if isinstance(secondary_data, dict) and secondary_data.get("criteria_met"):
                st.markdown("**Secondary Criteria Met:**")
                for criterion in secondary_data.get("criteria_met", [])[:3]:
                    st.write(f"• {criterion}")


def display_comprehensive_signals(signals: List[Dict]):
    """Display comprehensive behavioral signals with all details."""
    
    for signal in signals:
        signal_type = signal.get("signal_type", "unknown")
        metrics = signal.get("metrics", {})
        
        # Determine signal severity/importance
        severity = "info"
        if signal_type == "credit_utilization":
            util = metrics.get("aggregate", {}).get("utilization_percentage", 0)
            if util >= 90:
                severity = "error"
            elif util >= 75:
                severity = "warning"
        elif signal_type == "subscription":
            share = metrics.get("subscription_share_of_total", 0)
            if share >= 30:
                severity = "warning"
        
        with st.expander(f"📊 {signal_type.replace('_', ' ').title()}", expanded=True):
            # Display all metrics
            if isinstance(metrics, dict):
                # Create columns for metrics
                metric_items = list(metrics.items())
                num_cols = min(3, len(metric_items))
                
                if num_cols > 0:
                    cols = st.columns(num_cols)
                    
                    for idx, (key, value) in enumerate(metric_items[:9]):  # Show first 9 metrics
                        with cols[idx % num_cols]:
                            if isinstance(value, (int, float)):
                                if "percent" in key.lower() or "utilization" in key.lower() or "rate" in key.lower():
                                    st.metric(key.replace("_", " ").title(), f"{value:.1f}%")
                                elif "amount" in key.lower() or "spend" in key.lower() or "balance" in key.lower() or "interest" in key.lower():
                                    st.metric(key.replace("_", " ").title(), f"${value:,.2f}")
                                else:
                                    st.metric(key.replace("_", " ").title(), f"{value:,}")
                            elif isinstance(value, list):
                                st.metric(key.replace("_", " ").title(), len(value))
                            else:
                                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                
                # Show nested structures
                if "subscriptions" in metrics and isinstance(metrics["subscriptions"], list):
                    st.markdown("**Detected Subscriptions:**")
                    subscription_data = []
                    for sub in metrics["subscriptions"][:10]:  # Top 10
                        if isinstance(sub, dict):
                            subscription_data.append({
                                "Merchant": sub.get("merchant_name", "Unknown"),
                                "Monthly Spend": f"${sub.get('monthly_recurring_spend', 0):,.2f}",
                                "Cadence": sub.get("cadence", "unknown"),
                                "Transactions": sub.get("transaction_count", 0),
                                "Confidence": f"{sub.get('confidence_score', 0):.0%}"
                            })
                    if subscription_data:
                        st.dataframe(subscription_data, use_container_width=True, hide_index=True)
                
                if "cards" in metrics and isinstance(metrics["cards"], list):
                    st.markdown("**Credit Card Details:**")
                    card_data = []
                    for card in metrics["cards"]:
                        if isinstance(card, dict):
                            card_data.append({
                                "Account ID": card.get("account_id", "Unknown")[:20],
                                "Balance": f"${abs(card.get('balance', 0)):,.2f}",
                                "Limit": f"${card.get('limit', 0):,.2f}",
                                "Utilization": f"{card.get('utilization_percentage', 0):.1f}%",
                                "APR": f"{card.get('apr_percentage', 0):.1f}%"
                            })
                    if card_data:
                        st.dataframe(card_data, use_container_width=True, hide_index=True)


def display_account_overview(user_id: str, profile: Dict):
    """Display account overview information."""
    
    # Get account information from profile or signals
    accounts_info = []
    
    # Try to extract account info from signals
    if profile and profile.get("signals"):
        for signal in profile.get("signals", []):
            signal_type = signal.get("signal_type", "")
            metrics = signal.get("metrics", {})
            
            if signal_type == "credit_utilization" and "cards" in metrics:
                for card in metrics["cards"]:
                    if isinstance(card, dict):
                        accounts_info.append({
                            "Type": "Credit Card",
                            "Account ID": card.get("account_id", "Unknown")[:20],
                            "Balance": f"${abs(card.get('balance', 0)):,.2f}",
                            "Limit": f"${card.get('limit', 0):,.2f}",
                            "Utilization": f"{card.get('utilization_percentage', 0):.1f}%"
                        })
            
            elif signal_type == "savings" and "accounts" in metrics:
                for acc in metrics["accounts"]:
                    if isinstance(acc, dict):
                        accounts_info.append({
                            "Type": "Savings",
                            "Account ID": acc.get("account_id", "Unknown")[:20],
                            "Balance": f"${acc.get('current_balance', 0):,.2f}",
                            "Growth Rate": f"{acc.get('growth_rate', 0):.1f}%",
                            "Monthly Inflow": f"${acc.get('average_monthly_inflow', 0):,.2f}"
                        })
    
    if accounts_info:
        st.dataframe(accounts_info, use_container_width=True, hide_index=True)
    else:
        st.info("Account information not available in current view.")


def display_comprehensive_recommendations(user_id: str, recommendations: Dict, profile: Dict, transaction_summary: Dict):
    """Display recommendations with comprehensive data citations."""
    
    education_items = recommendations.get("education_items", [])
    partner_offers = recommendations.get("partner_offers", [])
    
    if education_items:
        st.markdown("#### 📚 Educational Content / Courses")
        
        for idx, item in enumerate(education_items, 1):
            with st.expander(
                f"📖 #{idx} - {item.get('title', 'Unknown')} | Priority: {item.get('priority', 0)}",
                expanded=(idx == 1)
            ):
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    st.markdown(f"**Course Title:** {item.get('title', 'N/A')}")
                    st.markdown(f"**Description:** {item.get('description', 'N/A')}")
                    
                    # Rationale
                    rationale = item.get('rationale', 'N/A')
                    st.markdown("**Personalized Rationale:**")
                    st.info(rationale)
                    
                    # Data Citations
                    data_citations = item.get('data_citations', {})
                    if data_citations:
                        st.markdown("**Supporting Data (Why this recommendation was made):**")
                        
                        citation_cols = st.columns(2)
                        citation_items = list(data_citations.items())
                        
                        for i, (key, value) in enumerate(citation_items[:6]):  # Show first 6
                            with citation_cols[i % 2]:
                                if isinstance(value, (int, float)):
                                    if "percent" in key.lower() or "utilization" in key.lower() or "rate" in key.lower():
                                        st.metric(key.replace("_", " ").title(), f"{value:.1f}%")
                                    elif "amount" in key.lower() or "spend" in key.lower() or "balance" in key.lower():
                                        st.metric(key.replace("_", " ").title(), f"${value:,.2f}")
                                    else:
                                        st.metric(key.replace("_", " ").title(), f"{value:,}")
                                else:
                                    st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                
                with col_right:
                    st.markdown("**Recommendation Details**")
                    st.write(f"**ID:** `{item.get('recommendation_id', 'N/A')}`")
                    st.write(f"**Content ID:** `{item.get('content_id', 'N/A')}`")
                    st.write(f"**Priority:** {item.get('priority', 0)}")
                    st.write(f"**Type:** Education")
                    
                    # Priority badge
                    priority = item.get('priority', 0)
                    if priority == 1:
                        st.success("🔝 High Priority - Most Important")
                    elif priority <= 3:
                        st.info("📌 Medium Priority")
                    else:
                        st.warning("📋 Standard Priority")
                    
                    # Connection to persona
                    persona_info = recommendations.get("persona", {})
                    primary_persona = persona_info.get("primary", "Unknown")
                    st.markdown(f"**Target Persona:** {primary_persona.replace('_', ' ').title()}")
    
    if partner_offers:
        st.markdown("#### 🎁 Partner Offers")
        
        for idx, offer in enumerate(partner_offers, 1):
            with st.expander(
                f"🎁 #{idx} - {offer.get('title', 'Unknown')} | Priority: {offer.get('priority', 0)}",
                expanded=(idx == 1)
            ):
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    st.markdown(f"**Offer Title:** {offer.get('title', 'N/A')}")
                    st.markdown(f"**Description:** {offer.get('description', 'N/A')}")
                    
                    # Rationale
                    rationale = offer.get('rationale', 'N/A')
                    st.markdown("**Personalized Rationale:**")
                    st.info(rationale)
                    
                    # Eligibility Data
                    data_citations = offer.get('data_citations', {})
                    if data_citations:
                        st.markdown("**Eligibility Criteria Met:**")
                        eligibility_cols = st.columns(2)
                        for i, (key, value) in enumerate(list(data_citations.items())[:4]):
                            with eligibility_cols[i % 2]:
                                if isinstance(value, (int, float)):
                                    if "percent" in key.lower() or "utilization" in key.lower():
                                        st.metric(key.replace("_", " ").title(), f"{value:.1f}%")
                                    elif "amount" in key.lower() or "spend" in key.lower():
                                        st.metric(key.replace("_", " ").title(), f"${value:,.2f}")
                
                with col_right:
                    st.markdown("**Offer Details**")
                    st.write(f"**ID:** `{offer.get('recommendation_id', 'N/A')}`")
                    st.write(f"**Offer ID:** `{offer.get('offer_id', 'N/A')}`")
                    st.write(f"**Priority:** {offer.get('priority', 0)}")
                    st.write(f"**Type:** Partner Offer")
                    
                    # Priority badge
                    priority = offer.get('priority', 0)
                    if priority == 1:
                        st.success("🔝 High Priority")
                    elif priority <= 3:
                        st.info("📌 Medium Priority")
                    else:
                        st.warning("📋 Standard Priority")


def display_complete_decision_path(user_id: str, profile: Dict, recommendations: Dict, signals: Dict, transaction_summary: Optional[Dict]):
    """Display the complete decision path from transactions to recommendations."""
    
    # Get days from session state or default
    days = st.session_state.get('review_period_days', 90)
    
    st.markdown("**AI Decision Journey:**")
    
    # Step 1: Data Ingestion
    step1_col1, step1_col2 = st.columns([1, 3])
    with step1_col1:
        st.markdown("#### Step 1: Data Ingestion")
    with step1_col2:
        total_txns = transaction_summary.get("total_transactions", 0) if transaction_summary else 0
        total_amount = transaction_summary.get("total_amount", 0.0) if transaction_summary else 0.0
        st.markdown(f"✅ Analyzed **{total_txns:,} transactions** totaling **${total_amount:,.2f}**")
        if transaction_summary:
            categories = len(transaction_summary.get("by_primary_category", {}))
            st.markdown(f"   - Categorized into **{categories} primary categories**")
            st.markdown(f"   - Time period: Last {days} days")
    
    # Step 2: Signal Detection
    step2_col1, step2_col2 = st.columns([1, 3])
    with step2_col1:
        st.markdown("#### Step 2: Behavioral Signal Detection")
    with step2_col2:
        if profile and profile.get("signals"):
            signal_types = [s.get("signal_type", "unknown") for s in profile.get("signals", [])]
            st.markdown(f"✅ Detected **{len(signal_types)} behavioral signals:**")
            for sig_type in signal_types:
                st.markdown(f"   - {sig_type.replace('_', ' ').title()}")
        else:
            st.markdown("⚠️ No behavioral signals detected")
    
    # Step 3: Persona Assignment
    step3_col1, step3_col2 = st.columns([1, 3])
    with step3_col1:
        st.markdown("#### Step 3: Persona Assignment")
    with step3_col2:
        if recommendations:
            persona_info = recommendations.get("persona", {})
            primary = persona_info.get("primary", "Unknown")
            primary_data = persona_info.get("primary_persona", {})
            confidence = 0.0
            if isinstance(primary_data, dict):
                confidence = primary_data.get("confidence", 0.0)
            
            st.markdown(f"✅ Assigned **{primary.replace('_', ' ').title()}** persona")
            st.markdown(f"   - Confidence: **{confidence:.0%}**")
            
            if isinstance(primary_data, dict) and primary_data.get("criteria_met"):
                criteria = primary_data.get("criteria_met", [])
                st.markdown(f"   - Criteria met: **{len(criteria)}**")
                for criterion in criteria[:3]:
                    st.markdown(f"     • {criterion}")
        else:
            st.markdown("⚠️ No persona assigned")
    
    # Step 4: Recommendation Generation
    step4_col1, step4_col2 = st.columns([1, 3])
    with step4_col1:
        st.markdown("#### Step 4: Recommendation Generation")
    with step4_col2:
        if recommendations:
            edu_count = len(recommendations.get("education_items", []))
            offer_count = len(recommendations.get("partner_offers", []))
            st.markdown(f"✅ Generated **{edu_count} educational content** items and **{offer_count} partner offers**")
            st.markdown(f"   - Based on persona-specific content catalog")
            st.markdown(f"   - Filtered by eligibility rules")
            st.markdown(f"   - Personalized with data citations")
        else:
            st.markdown("⚠️ No recommendations generated")
    
    # Step 5: Rationale Generation
    step5_col1, step5_col2 = st.columns([1, 3])
    with step5_col1:
        st.markdown("#### Step 5: Rationale Generation")
    with step5_col2:
        if recommendations:
            st.markdown("✅ Generated personalized rationales for each recommendation")
            st.markdown("   - Cited specific transaction data")
            st.markdown("   - Used tone-appropriate language")
            st.markdown("   - Validated for compliance")


def display_operator_insights(user_id: str, profile: Dict, recommendations: Dict, transaction_summary: Dict):
    """Display actionable insights for operators."""
    
    insights = []
    
    # Analyze persona assignment
    if recommendations:
        persona_info = recommendations.get("persona", {})
        primary = persona_info.get("primary", "")
        
        if primary == "high_utilization":
            insights.append({
                "type": "warning",
                "title": "High Credit Utilization Detected",
                "message": "User has high credit card utilization. Monitor for potential financial stress.",
                "action": "Review credit card recommendations and consider debt management resources."
            })
        
        elif primary == "subscription_heavy":
            insights.append({
                "type": "info",
                "title": "High Subscription Spending",
                "message": "User has significant recurring subscription costs.",
                "action": "Subscription cancellation recommendations may be impactful."
            })
        
        elif primary == "financial_fragility":
            insights.append({
                "type": "error",
                "title": "Financial Fragility Detected",
                "message": "User shows signs of financial stress (low balances, overdrafts).",
                "action": "Prioritize gentle, supportive recommendations. Avoid aggressive offers."
            })
    
    # Analyze transaction patterns
    if transaction_summary:
        by_primary = transaction_summary.get("by_primary_category", {})
        total_amount = transaction_summary.get("total_amount", 0.0)
        
        # Check for high spending categories
        for cat, data in by_primary.items():
            percentage = (data["total_amount"] / total_amount * 100) if total_amount > 0 else 0
            if percentage > 40:
                insights.append({
                    "type": "info",
                    "title": f"High Spending in {cat.replace('_', ' ').title()}",
                    "message": f"{percentage:.1f}% of spending is in {cat.replace('_', ' ').title()} category.",
                    "action": "Consider category-specific recommendations."
                })
    
    # Display insights
    if insights:
        for insight in insights:
            if insight["type"] == "error":
                st.error(f"**{insight['title']}:** {insight['message']}\n\n*Action: {insight['action']}*")
            elif insight["type"] == "warning":
                st.warning(f"**{insight['title']}:** {insight['message']}\n\n*Action: {insight['action']}*")
            else:
                st.info(f"**{insight['title']}:** {insight['message']}\n\n*Action: {insight['action']}*")
    else:
        st.success("✅ No critical insights. User profile appears stable.")


def display_transaction_category_summary(summary: Dict, show_raw_data: bool = False):
    """Display transaction summary grouped by category from API."""
    
    total_transactions = summary.get("total_transactions", 0)
    total_amount = summary.get("total_amount", 0.0)
    by_primary = summary.get("by_primary_category", {})
    by_category = summary.get("by_category", {})
    
    # Summary metrics with visual indicators
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Transactions", f"{total_transactions:,}")
    with col2:
        st.metric("Total Amount", f"${total_amount:,.2f}")
    with col3:
        st.metric("Categories", len(by_primary))
    with col4:
        avg_transaction = total_amount / total_transactions if total_transactions > 0 else 0
        st.metric("Avg Transaction", f"${avg_transaction:,.2f}")
    
    # Primary Category Summary with Chart
    st.markdown("#### 📊 Spending by Primary Category")
    if by_primary:
        # Chart data
        chart_data = []
        for cat, data in sorted(by_primary.items(), key=lambda x: x[1]["total_amount"], reverse=True):
            percentage = (data["total_amount"] / total_amount * 100) if total_amount > 0 else 0
            chart_data.append({
                "Category": cat.replace("_", " ").title(),
                "Amount": data["total_amount"],
                "Count": data["count"],
                "Percentage": percentage
            })
        
        # Display chart
        try:
            import pandas as pd
            df = pd.DataFrame(chart_data)
            st.bar_chart(df.set_index("Category")["Amount"], use_container_width=True)
        except:
            pass
        
        # Table
        primary_data = []
        for item in chart_data:
            primary_data.append({
                "Category": item["Category"],
                "Transaction Count": item["Count"],
                "Total Amount": f"${item['Amount']:,.2f}",
                "Percentage": f"{item['Percentage']:.1f}%"
            })
        
        st.dataframe(primary_data, use_container_width=True, hide_index=True)
    
    # Detailed Category Summary with expandable sections
    st.markdown("#### 📋 Detailed Category Breakdown")
    if by_category:
        # Sort by amount
        sorted_categories = sorted(by_category.items(), key=lambda x: x[1]["total_amount"], reverse=True)
        
        # Show top categories in tabs
        top_categories = sorted_categories[:10]  # Top 10
        other_categories = sorted_categories[10:]  # Rest
        
        if top_categories:
            st.markdown("**Top 10 Categories:**")
            for idx, (cat, data) in enumerate(top_categories, 1):
                percentage = (data["total_amount"] / total_amount * 100) if total_amount > 0 else 0
                with st.expander(f"📁 #{idx} - {cat.replace('_', ' ').title()} - ${data['total_amount']:,.2f} ({data['count']} transactions, {percentage:.1f}%)"):
                    col_left, col_right = st.columns([1, 1])
                    
                    with col_left:
                        st.markdown("**Summary Statistics**")
                        st.metric("Transaction Count", f"{data['count']:,}")
                        st.metric("Total Amount", f"${data['total_amount']:,.2f}")
                        st.metric("Average Amount", f"${data.get('average_amount', 0):,.2f}")
                        st.metric("Percentage of Total", f"{percentage:.1f}%")
                    
                    with col_right:
                        st.markdown("**Transaction Details**")
                        if data.get("transactions"):
                            st.markdown(f"**Recent Transactions (showing up to 10):**")
                            recent = data["transactions"][:10]
                            transaction_list = []
                            for txn in recent:
                                transaction_list.append({
                                    "Date": txn.get("date", "")[:10],
                                    "Amount": f"${txn.get('amount', 0):,.2f}",
                                    "Merchant": txn.get("merchant", "Unknown")
                                })
                            
                            if transaction_list:
                                st.dataframe(transaction_list, use_container_width=True, hide_index=True)
                            
                            if len(data["transactions"]) > 10:
                                st.caption(f"... and {len(data['transactions']) - 10} more transactions")
                        else:
                            st.info("No transaction details available")
                    
                    # Show raw data if requested
                    if show_raw_data and data.get("transactions"):
                        st.markdown("**Raw Transaction Data:**")
                        st.json(data["transactions"][:20])  # Show first 20
        
        if other_categories:
            with st.expander(f"📁 Other Categories ({len(other_categories)} more)"):
                other_data = []
                for cat, data in other_categories:
                    percentage = (data["total_amount"] / total_amount * 100) if total_amount > 0 else 0
                    other_data.append({
                        "Category": cat.replace("_", " ").title(),
                        "Count": data["count"],
                        "Amount": f"${data['total_amount']:,.2f}",
                        "Percentage": f"{percentage:.1f}%"
                    })
                st.dataframe(other_data, use_container_width=True, hide_index=True)
    else:
        st.info("No category data available.")


def display_transaction_summary_by_category(user_id: str, signals: List[Dict]):
    """Display transaction summary grouped by category."""
    
    # Extract transaction data from signals
    transaction_data = []
    
    for signal in signals:
        signal_type = signal.get("signal_type", "")
        metrics = signal.get("metrics", {})
        
        if signal_type == "subscription":
            # Subscription data
            subscriptions = metrics.get("subscriptions", [])
            for sub in subscriptions:
                transaction_data.append({
                    "category": "Subscription",
                    "subcategory": sub.get("merchant_name", "Unknown"),
                    "amount": sub.get("monthly_recurring_spend", 0),
                    "count": sub.get("transaction_count", 0),
                    "cadence": sub.get("cadence", "monthly")
                })
        
        elif signal_type == "credit_utilization":
            # Credit card transactions
            cards = metrics.get("cards", [])
            for card in cards:
                transaction_data.append({
                    "category": "Credit Card",
                    "subcategory": f"Card {card.get('account_id', 'Unknown')[:8]}",
                    "amount": abs(card.get("current_balance", 0)),
                    "count": 1,
                    "utilization": card.get("utilization_percentage", 0)
                })
        
        elif signal_type == "savings":
            # Savings data
            accounts = metrics.get("accounts", [])
            for acc in accounts:
                transaction_data.append({
                    "category": "Savings",
                    "subcategory": f"Account {acc.get('account_id', 'Unknown')[:8]}",
                    "amount": acc.get("current_balance", 0),
                    "count": acc.get("transaction_count", 0),
                    "growth_rate": acc.get("growth_rate", 0)
                })
        
        elif signal_type == "income_stability":
            # Income data
            income_patterns = metrics.get("income_patterns", [])
            for pattern in income_patterns:
                transaction_data.append({
                    "category": "Income",
                    "subcategory": pattern.get("source", "Payroll"),
                    "amount": pattern.get("average_amount", 0),
                    "count": pattern.get("occurrence_count", 0),
                    "frequency": pattern.get("frequency", "unknown")
                })
    
    if transaction_data:
        # Group by category
        category_summary = {}
        for item in transaction_data:
            category = item.get("category", "Other")
            if category not in category_summary:
                category_summary[category] = {
                    "total_amount": 0,
                    "total_count": 0,
                    "items": []
                }
            category_summary[category]["total_amount"] += item.get("amount", 0)
            category_summary[category]["total_count"] += item.get("count", 0)
            category_summary[category]["items"].append(item)
        
        # Display summary tables
        for category, summary in category_summary.items():
            with st.expander(f"📁 {category} - Total: ${summary['total_amount']:,.2f} ({summary['total_count']} transactions)"):
                # Create table data
                table_data = []
                for item in summary["items"]:
                    row = {
                        "Subcategory": item.get("subcategory", "N/A"),
                        "Amount": f"${item.get('amount', 0):,.2f}",
                        "Count": item.get("count", 0)
                    }
                    # Add category-specific fields
                    if "utilization" in item:
                        row["Utilization"] = f"{item.get('utilization', 0):.1f}%"
                    if "growth_rate" in item:
                        row["Growth Rate"] = f"{item.get('growth_rate', 0):.1f}%"
                    if "frequency" in item:
                        row["Frequency"] = item.get("frequency", "N/A")
                    if "cadence" in item:
                        row["Cadence"] = item.get("cadence", "N/A")
                    
                    table_data.append(row)
                
                st.dataframe(table_data, use_container_width=True, hide_index=True)
    else:
        st.info("No transaction data available for this user.")


def display_signals_summary(signals: List[Dict]):
    """Display behavioral signals summary."""
    for signal in signals:
        signal_type = signal.get("signal_type", "unknown")
        metrics = signal.get("metrics", {})
        
        with st.expander(f"📊 {signal_type.replace('_', ' ').title()}"):
            st.json(metrics)


def display_recommendations_with_data(user_id: str, recommendations: Dict, profile: Dict):
    """Display recommendations with their data citations."""
    
    # This function is now replaced by display_comprehensive_recommendations
    # Keeping for backward compatibility
    display_comprehensive_recommendations(user_id, recommendations, profile, None)


def display_decision_explanation(user_id: str, profile: Dict, recommendations: Dict, signals: Dict):
    """Display explanation of how the model made its decisions."""
    
    st.markdown("**How the AI made its recommendations:**")
    
    # Persona assignment explanation
    persona_info = recommendations.get("persona", {}) if recommendations else {}
    primary_persona = persona_info.get("primary")
    
    if primary_persona:
        st.markdown(f"1. **Persona Assignment:** User was assigned **{primary_persona.replace('_', ' ').title()}** persona based on:")
        
        # Show which signals led to persona
        if profile and profile.get("signals"):
            signal_reasons = []
            for signal in profile.get("signals", []):
                signal_type = signal.get("signal_type", "")
                metrics = signal.get("metrics", {})
                
                if signal_type == "credit_utilization" and metrics.get("aggregate", {}).get("utilization_percentage", 0) > 75:
                    signal_reasons.append(f"High credit utilization ({metrics.get('aggregate', {}).get('utilization_percentage', 0):.1f}%)")
                elif signal_type == "subscription" and metrics.get("subscription_share_of_total", 0) > 20:
                    signal_reasons.append(f"High subscription spend ({metrics.get('subscription_share_of_total', 0):.1f}% of total)")
                elif signal_type == "savings" and metrics.get("aggregate", {}).get("growth_rate", 0) > 0:
                    signal_reasons.append(f"Positive savings growth ({metrics.get('aggregate', {}).get('growth_rate', 0):.1f}%)")
                elif signal_type == "income_stability" and metrics.get("variability", 0) > 0.2:
                    signal_reasons.append(f"Income variability ({metrics.get('variability', 0):.1f})")
            
            for reason in signal_reasons:
                st.markdown(f"   - {reason}")
    
    # Recommendation generation explanation
    if recommendations:
        edu_count = len(recommendations.get("education_items", []))
        offer_count = len(recommendations.get("partner_offers", []))
        
        st.markdown(f"2. **Recommendation Generation:** Generated {edu_count} educational content items and {offer_count} partner offers based on:")
        st.markdown("   - Persona-specific content catalog")
        st.markdown("   - Eligibility rules for partner offers")
        st.markdown("   - User's behavioral signals and transaction patterns")
    
    # Data used
    st.markdown("3. **Data Sources Used:**")
    st.markdown("   - Transaction history (categorized by Personal Finance Category)")
    st.markdown("   - Account balances and credit limits")
    st.markdown("   - Subscription patterns (recurring transactions)")
    st.markdown("   - Income deposits (payroll detection)")
    st.markdown("   - Savings account growth patterns")


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
# Query Tool Page
# ============================================================================

def show_query_tool():
    """Show natural language query tool."""
    render_query_tool(API_BASE_URL)


# ============================================================================
# Run Dashboard
# ============================================================================

if __name__ == "__main__":
    main()

