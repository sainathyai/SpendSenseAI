"""
Customer-Facing Dashboard for SpendSenseAI.

Provides end-user interface for viewing:
- Assigned persona (educational framing)
- Personalized recommendations
- Educational content
- Financial snapshot (balances, trends)
"""

import streamlit as st
import requests
from typing import Dict, Optional, List
from datetime import datetime
import os

# API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="SpendSenseAI - Your Financial Insights",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
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
    """Main customer dashboard function."""
    # Header
    st.title("💰 SpendSenseAI")
    st.markdown("**Your Personalized Financial Education Platform**")
    st.markdown("---")
    
    # Sidebar for user authentication (in production, this would be real auth)
    st.sidebar.title("Account")
    user_id = st.sidebar.text_input("User ID", value="CUST000001", key="customer_user_id")
    
    if not user_id:
        st.warning("Please enter your User ID to view your dashboard.")
        return
    
    # Get user profile
    profile = api_request("GET", f"/profile/{user_id}")
    recommendations = api_request("GET", f"/recommendations/{user_id}?check_consent=false")
    
    if not profile or not recommendations:
        st.error("Unable to load your profile. Please check your User ID or contact support.")
        return
    
    # Display persona assignment
    st.header("Your Financial Persona")
    
    persona_data = recommendations.get("persona", {})
    primary_persona = persona_data.get("primary")
    
    if primary_persona:
        persona_type = primary_persona.get("persona_type", "Unknown")
        confidence = primary_persona.get("confidence_score", 0.0)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(f"🎯 {format_persona_name(persona_type)}")
            st.markdown(f"**Confidence:** {confidence:.1%}")
            st.info(f"""
            Your financial behavior patterns indicate you're a **{format_persona_name(persona_type)}**.
            This persona helps us provide personalized recommendations that match your financial situation and goals.
            """)
        
        with col2:
            # Display persona icon or visual
            st.metric("Persona Match", f"{confidence:.0%}")
    else:
        st.info("No persona assigned yet. We're analyzing your financial patterns...")
    
    st.markdown("---")
    
    # Financial snapshot
    st.header("📊 Financial Snapshot")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Get account balances (simplified - in production would come from accounts API)
    with col1:
        st.metric("Total Accounts", "Loading...")
    
    with col2:
        st.metric("Total Balance", "Loading...")
    
    with col3:
        st.metric("Credit Utilization", "Loading...")
    
    with col4:
        st.metric("Savings Rate", "Loading...")
    
    # Behavioral signals
    st.subheader("📈 Your Financial Patterns")
    
    signals = profile.get("signals", [])
    
    if signals:
        for signal in signals:
            signal_type = signal.get("signal_type", "Unknown")
            metrics = signal.get("metrics", {})
            
            with st.expander(f"🔍 {signal_type.replace('_', ' ').title()}"):
                if signal_type == "credit_utilization":
                    utilization = metrics.get("aggregate_utilization", 0)
                    st.metric("Overall Utilization", f"{utilization:.1f}%")
                    if utilization >= 80:
                        st.warning("⚠️ High utilization detected. Consider paying down balances.")
                    elif utilization >= 50:
                        st.info("💡 Utilization is moderate. Keeping it below 30% can improve your credit score.")
                    else:
                        st.success("✅ Good utilization rate!")
                
                elif signal_type == "savings":
                    balance = metrics.get("total_savings_balance", 0)
                    growth_rate = metrics.get("overall_growth_rate", 0)
                    st.metric("Total Savings", format_currency(balance))
                    st.metric("Growth Rate (6 months)", f"{growth_rate:.1f}%")
                    if growth_rate > 0:
                        st.success(f"📈 Your savings are growing at {growth_rate:.1f}%!")
                
                elif signal_type == "subscription":
                    count = metrics.get("subscription_count", 0)
                    monthly_spend = metrics.get("total_monthly_recurring_spend", 0)
                    st.metric("Active Subscriptions", count)
                    st.metric("Monthly Recurring Spend", format_currency(monthly_spend))
                    st.metric("Annual Cost", format_currency(monthly_spend * 12))
                
                elif signal_type == "income":
                    pay_gap = metrics.get("median_pay_gap_days", 0)
                    buffer = metrics.get("cash_flow_buffer_months", 0)
                    st.metric("Median Pay Gap", f"{pay_gap:.1f} days")
                    st.metric("Cash Flow Buffer", f"{buffer:.1f} months")
                    if buffer < 1:
                        st.warning("⚠️ Consider building a larger cash flow buffer.")
    
    st.markdown("---")
    
    # Recommendations
    st.header("💡 Personalized Recommendations")
    st.markdown("Based on your financial patterns, here are personalized recommendations:")
    
    # Education items
    edu_items = recommendations.get("education_items", [])
    if edu_items:
        st.subheader("📚 Educational Content")
        
        for i, item in enumerate(edu_items, 1):
            with st.expander(f"{i}. {item.get('title', 'Unknown')}"):
                st.markdown(f"**Description:** {item.get('description', 'N/A')}")
                st.markdown(f"**Why this helps you:** {item.get('rationale', 'N/A')}")
                
                if st.button(f"Learn More", key=f"learn_{i}"):
                    st.info("In a production system, this would link to the full educational content.")
    
    # Partner offers
    offers = recommendations.get("partner_offers", [])
    if offers:
        st.subheader("🎁 Partner Offers")
        
        for i, offer in enumerate(offers, 1):
            with st.expander(f"{i}. {offer.get('title', 'Unknown')}"):
                st.markdown(f"**Description:** {offer.get('description', 'N/A')}")
                st.markdown(f"**Why this might help:** {offer.get('rationale', 'N/A')}")
                
                if st.button(f"Explore Offer", key=f"offer_{i}"):
                    st.info("In a production system, this would link to the partner offer details.")
    
    if not edu_items and not offers:
        st.info("No recommendations available at this time. Check back soon!")
    
    st.markdown("---")
    
    # Footer with disclaimer
    st.markdown("""
    ---
    **Disclaimer:** This information is for educational purposes only and does not constitute financial advice. 
    Please consult with a qualified financial advisor before making financial decisions.
    """)
    
    # Feedback section
    with st.expander("💬 Feedback"):
        feedback_type = st.selectbox(
            "How helpful was this dashboard?",
            ["Very Helpful", "Somewhat Helpful", "Not Helpful", "Other"]
        )
        
        comment = st.text_area("Additional Comments (Optional)")
        
        if st.button("Submit Feedback"):
            feedback_data = {
                "user_id": user_id,
                "feedback_type": feedback_type.lower().replace(" ", "_"),
                "comment": comment
            }
            result = api_request("POST", "/feedback", json=feedback_data)
            if result:
                st.success("✅ Thank you for your feedback!")
            else:
                st.error("Failed to submit feedback. Please try again.")


if __name__ == "__main__":
    main()

