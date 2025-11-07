"""
Transaction Monitoring Business Intelligence Dashboard

A comprehensive multi-page Streamlit application for visualizing
fraud detection patterns, risk distributions, and transaction analytics.
"""
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Transaction Monitoring BI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stMetric {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<div class="main-header">📊 Transaction Monitoring BI Dashboard</div>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar navigation
st.sidebar.title("Navigation")
st.sidebar.markdown("Select a page to view different analytics and insights.")

page = st.sidebar.radio(
    "Go to:",
    [
        "🏠 Executive Summary",
        "🔍 Fraud Scenario Analysis",
        "📋 Rule Performance",
        "⚠️ Risk Distribution",
        "👥 Manual Review Queue",
        "🏦 Account Activity",
        "⚡ Transaction Velocity",
        "💰 Cost-Benefit Analysis"
    ]
)

# Import page modules
from pages import (
    executive_summary,
    fraud_scenarios,
    rule_performance,
    risk_distribution,
    review_queue,
    account_activity,
    transaction_velocity,
    cost_benefit
)

# Route to selected page
if page == "🏠 Executive Summary":
    executive_summary.show()
elif page == "🔍 Fraud Scenario Analysis":
    fraud_scenarios.show()
elif page == "📋 Rule Performance":
    rule_performance.show()
elif page == "⚠️ Risk Distribution":
    risk_distribution.show()
elif page == "👥 Manual Review Queue":
    review_queue.show()
elif page == "🏦 Account Activity":
    account_activity.show()
elif page == "⚡ Transaction Velocity":
    transaction_velocity.show()
elif page == "💰 Cost-Benefit Analysis":
    cost_benefit.show()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Transaction Monitoring System v1.0**")
st.sidebar.info("Real-time fraud detection and risk assessment platform")
