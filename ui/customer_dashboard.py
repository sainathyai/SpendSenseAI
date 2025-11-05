"""
Customer-Facing Dashboard for SpendSenseAI.

Simple web interface for customers to view:
- Their assigned persona (educational framing)
- Personalized recommendations
- Educational content
- Financial snapshot (balances, trends)
"""

import streamlit as st
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import os

# API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="SpendSenseAI - Your Financial Insights",
    page_icon="💰",
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


def format_persona_name(persona_type: str) -> str:
    """Format persona type for display."""
    return persona_type.replace('_', ' ').title()


def format_currency(amount: float) -> str:
    """Format currency for display."""
    return f"${amount:,.2f}"


# ============================================================================
# Main Dashboard
# ============================================================================

def main():
    """Main dashboard function."""
    st.title("💰 SpendSenseAI - Your Personalized Financial Insights")
    st.markdown("---")
    
    # Sidebar for user login/selection
    st.sidebar.title("Account")
    
    # User ID input (in production, this would be from authentication)
    user_id = st.sidebar.text_input("Enter Your User ID:", value="CUST000001", key="user_id_input")
    
    if not user_id:
        st.warning("Please enter a User ID to view your dashboard.")
        return
    
    # Check API health
    health = api_request("GET", "/health")
    if health:
        status_color = "🟢" if health.get("status") == "healthy" else "🔴"
        st.sidebar.markdown(f"{status_color} System Status: {health.get('status', 'unknown')}")
    else:
        st.sidebar.markdown("🔴 System Status: Disconnected")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🎯 Recommendations", "📚 Education", "💳 Financial Snapshot"])
    
    with tab1:
        show_overview(user_id)
    
    with tab2:
        show_recommendations(user_id)
    
    with tab3:
        show_education_content(user_id)
    
    with tab4:
        show_financial_snapshot(user_id)


# ============================================================================
# Overview Tab
# ============================================================================

def show_overview(user_id: str):
    """Show overview of user's financial profile."""
    st.header("Your Financial Profile")
    
    # Get user profile
    profile = api_request("GET", f"/profile/{user_id}")
    
    if not profile:
        st.error("Unable to load your profile. Please try again later.")
        return
    
    # Persona assignment
    st.subheader("Your Financial Persona")
    
    primary_persona = profile.get("primary_persona")
    if primary_persona:
        persona_type = primary_persona.get("persona_type", "Unknown")
        confidence = primary_persona.get("confidence_score", 0)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"### {format_persona_name(persona_type)}")
            st.markdown(f"**Confidence:** {confidence:.1%}")
            
            # Persona description
            persona_descriptions = {
                "High Utilization": "You're managing credit card balances that could benefit from strategic payment planning.",
                "Variable Income Budgeter": "Your income varies, so flexible budgeting strategies can help you manage cash flow better.",
                "Subscription Heavy": "You have multiple recurring subscriptions that might be worth reviewing.",
                "Savings Builder": "You're building your savings—great job! Let's optimize your strategy.",
                "Financial Fragility": "You're facing some immediate financial challenges. Let's build a buffer and avoid fees."
            }
            
            description = persona_descriptions.get(persona_type, "Your financial behavior shows unique patterns.")
            st.info(description)
        
        with col2:
            # Confidence visualization
            st.metric("Profile Match", f"{confidence:.0%}")
            
            # Secondary persona if available
            secondary_persona = profile.get("secondary_persona")
            if secondary_persona:
                st.caption(f"Secondary: {format_persona_name(secondary_persona.get('persona_type', ''))}")
    
    # Behavioral signals summary
    st.subheader("Your Financial Behaviors")
    
    signals = profile.get("signals", [])
    if signals:
        cols = st.columns(min(len(signals), 4))
        
        for i, signal in enumerate(signals):
            with cols[i % len(cols)]:
                signal_type = signal.get("signal_type", "").replace("_", " ").title()
                metrics = signal.get("metrics", {})
                
                if signal_type == "Credit Utilization":
                    value = metrics.get("aggregate_utilization", 0)
                    st.metric("Credit Utilization", f"{value:.1f}%")
                elif signal_type == "Savings":
                    value = metrics.get("total_savings_balance", 0)
                    st.metric("Savings Balance", format_currency(value))
                elif signal_type == "Subscription":
                    value = metrics.get("subscription_count", 0)
                    st.metric("Active Subscriptions", f"{value}")
                elif signal_type == "Income":
                    value = metrics.get("median_pay_gap_days", 0)
                    st.metric("Pay Frequency Gap", f"{value:.1f} days")
    else:
        st.info("No behavioral signals detected yet.")
    
    # Quick recommendations preview
    st.subheader("Quick Recommendations")
    
    recommendations = api_request("GET", f"/recommendations/{user_id}?check_consent=false")
    
    if recommendations:
        edu_items = recommendations.get("education_items", [])
        offers = recommendations.get("partner_offers", [])
        
        if edu_items or offers:
            # Show first 3 recommendations
            preview_items = (edu_items[:2] + offers[:1])[:3]
            
            for item in preview_items:
                with st.expander(f"💡 {item.get('title', 'Recommendation')}"):
                    st.write(item.get('description', ''))
                    st.caption(f"Priority: {item.get('priority', 0)}")
        else:
            st.info("No recommendations available at this time.")
    else:
        st.info("Recommendations are being prepared for you.")


# ============================================================================
# Recommendations Tab
# ============================================================================

def show_recommendations(user_id: str):
    """Show personalized recommendations."""
    st.header("Your Personalized Recommendations")
    st.markdown("Based on your financial behavior, here are tailored recommendations for you:")
    
    # Get recommendations
    recommendations = api_request("GET", f"/recommendations/{user_id}?check_consent=false")
    
    if not recommendations:
        st.error("Unable to load recommendations. Please try again later.")
        return
    
    # Education content recommendations
    edu_items = recommendations.get("education_items", [])
    if edu_items:
        st.subheader("📚 Educational Content")
        st.markdown("Learn how to improve your financial situation:")
        
        for item in edu_items:
            with st.expander(f"**{item.get('title', 'Content')}** - Priority {item.get('priority', 0)}"):
                st.write(f"**What you'll learn:** {item.get('description', '')}")
                st.write(f"**Why this matters:** {item.get('rationale', '')}")
                st.caption(f"Content ID: {item.get('content_id', 'N/A')}")
    
    # Partner offers
    offers = recommendations.get("partner_offers", [])
    if offers:
        st.subheader("💼 Partner Offers")
        st.markdown("These offers may be suitable for your financial situation:")
        
        for offer in offers:
            with st.expander(f"**{offer.get('title', 'Offer')}** - Priority {offer.get('priority', 0)}"):
                st.write(f"**Description:** {offer.get('description', '')}")
                st.write(f"**Why this might help:** {offer.get('rationale', '')}")
                
                # Offer details
                col1, col2 = st.columns(2)
                with col1:
                    st.caption(f"Offer ID: {offer.get('offer_id', 'N/A')}")
                with col2:
                    if offer.get('offer_id'):
                        st.button("Learn More", key=f"offer_{offer.get('offer_id')}")
    
    # Disclaimer
    st.markdown("---")
    disclaimer = recommendations.get("disclaimer", "")
    if disclaimer:
        st.caption(f"ℹ️ {disclaimer}")


# ============================================================================
# Education Content Tab
# ============================================================================

def show_education_content(user_id: str):
    """Show educational content library."""
    st.header("Financial Education Library")
    st.markdown("Browse educational content tailored to your financial situation:")
    
    # Get user profile to show persona-specific content
    profile = api_request("GET", f"/profile/{user_id}")
    
    if profile:
        primary_persona = profile.get("primary_persona")
        if primary_persona:
            persona_type = primary_persona.get("persona_type", "")
            st.info(f"Showing content recommended for: **{format_persona_name(persona_type)}**")
    
    # Get recommendations to show education items
    recommendations = api_request("GET", f"/recommendations/{user_id}?check_consent=false")
    
    if recommendations:
        edu_items = recommendations.get("education_items", [])
        
        if edu_items:
            for item in edu_items:
                st.markdown(f"### {item.get('title', 'Content')}")
                st.write(item.get('description', ''))
                st.write(f"**Why this matters for you:** {item.get('rationale', '')}")
                st.markdown("---")
        else:
            st.info("No educational content available at this time.")
    else:
        st.info("Educational content is being prepared for you.")


# ============================================================================
# Financial Snapshot Tab
# ============================================================================

def show_financial_snapshot(user_id: str):
    """Show financial snapshot with balances and trends."""
    st.header("Your Financial Snapshot")
    
    # Get user profile
    profile = api_request("GET", f"/profile/{user_id}")
    
    if not profile:
        st.error("Unable to load your financial snapshot. Please try again later.")
        return
    
    # Display signals as financial snapshot
    signals = profile.get("signals", [])
    
    if signals:
        st.subheader("Current Financial Status")
        
        # Credit utilization
        credit_signal = next((s for s in signals if s.get("signal_type") == "credit_utilization"), None)
        if credit_signal:
            metrics = credit_signal.get("metrics", {})
            utilization = metrics.get("aggregate_utilization", 0)
            balance = metrics.get("total_balance", 0)
            limit = metrics.get("total_limit", 0)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Credit Utilization", f"{utilization:.1f}%")
            with col2:
                st.metric("Total Balance", format_currency(balance))
            with col3:
                st.metric("Total Credit Limit", format_currency(limit))
            
            # Utilization status
            if utilization >= 80:
                st.warning("⚠️ High credit utilization detected. Consider paying down balances.")
            elif utilization >= 50:
                st.info("ℹ️ Credit utilization is moderate. Aim for below 30% for optimal credit health.")
            else:
                st.success("✅ Credit utilization is healthy.")
        
        # Savings
        savings_signal = next((s for s in signals if s.get("signal_type") == "savings"), None)
        if savings_signal:
            metrics = savings_signal.get("metrics", {})
            balance = metrics.get("total_savings_balance", 0)
            growth_rate = metrics.get("overall_growth_rate", 0)
            
            st.markdown("### Savings")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Savings Balance", format_currency(balance))
            with col2:
                st.metric("Growth Rate (6 months)", f"{growth_rate:.1f}%")
        
        # Subscriptions
        subscription_signal = next((s for s in signals if s.get("signal_type") == "subscription"), None)
        if subscription_signal:
            metrics = subscription_signal.get("metrics", {})
            count = metrics.get("subscription_count", 0)
            monthly_spend = metrics.get("total_monthly_recurring_spend", 0)
            
            st.markdown("### Subscriptions")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Active Subscriptions", f"{count}")
            with col2:
                st.metric("Monthly Recurring Spend", format_currency(monthly_spend))
            
            annual_spend = monthly_spend * 12
            st.caption(f"Annual subscription cost: {format_currency(annual_spend)}")
        
        # Income
        income_signal = next((s for s in signals if s.get("signal_type") == "income"), None)
        if income_signal:
            metrics = income_signal.get("metrics", {})
            pay_gap = metrics.get("median_pay_gap_days", 0)
            buffer = metrics.get("cash_flow_buffer_months", 0)
            
            st.markdown("### Income")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Median Pay Gap", f"{pay_gap:.1f} days")
            with col2:
                st.metric("Cash Flow Buffer", f"{buffer:.1f} months")
    else:
        st.info("Financial snapshot data is being prepared for you.")


# ============================================================================
# Run Dashboard
# ============================================================================

if __name__ == "__main__":
    main()
