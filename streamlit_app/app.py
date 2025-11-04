"""
Transaction Monitoring Dashboard - Main Application

Streamlit-based fraud detection dashboard with role-based access control.
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from streamlit_app.api_client import get_api_client, is_authenticated, get_user_info, logout

# Page configuration
st.set_page_config(
    page_title="Fraud Detection Dashboard",
    page_icon="🛡️",
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
        border-left: 4px solid #1f77b4;
    }
    .alert-high {
        background-color: #ffcccc;
        padding: 0.5rem;
        border-radius: 0.3rem;
        border-left: 4px solid #ff0000;
    }
    .alert-medium {
        background-color: #fff3cd;
        padding: 0.5rem;
        border-radius: 0.3rem;
        border-left: 4px solid #ffa500;
    }
    .alert-low {
        background-color: #d1ecf1;
        padding: 0.5rem;
        border-radius: 0.3rem;
        border-left: 4px solid #17a2b8;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f1f5f9;
        border-radius: 5px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


def login_page():
    """Display login page"""
    st.markdown('<div class="main-header">🛡️ Arriba Advisors Real-Time Detection System</div>', unsafe_allow_html=True)
    st.markdown("### Login to Dashboard")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("login_form"):
            st.markdown("#### Enter your credentials")

            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if username and password:
                    try:
                        client = get_api_client()
                        user_info = client.login(username, password)

                        st.success(f"✅ Welcome, {username}!")
                        st.session_state.logged_in = True
                        st.session_state.user_info = user_info
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Login failed: {str(e)}")
                        st.error("Please check your username and password.")
                else:
                    st.warning("Please enter both username and password")

        # Test credentials info
        with st.expander("ℹ️ Test Credentials"):
            st.markdown("""
            **Available test accounts:**

            - **Analyst**: Username: `analyst`, Password: `analyst123`
            - **Manager**: Username: `manager`, Password: `manager123`
            - **Investigator**: Username: `investigator`, Password: `investigator123`
            - **Admin**: Username: `admin`, Password: `admin123`
            """)


def main_dashboard():
    """Main dashboard after authentication"""

    # Sidebar
    with st.sidebar:
        st.markdown("### 🛡️ Arriba Advisors")
        st.markdown("**Real-Time Detection System**")

        # User info
        user_info = get_user_info()
        st.markdown(f"**User:** {user_info.get('username', 'Unknown')}")
        st.markdown(f"**Role:** {user_info.get('role', 'Unknown').title()}")

        st.divider()

        # Navigation
        st.markdown("### 📍 Navigation")

        # Professional navigation structure
        page = st.selectbox(
            "Select Page",
            [
                "🏠 Homepage",
                "📊 Transaction Monitoring System",
                "📈 Rule Performance Analytics",
                "🔍 Fraud Scenario Analysis",
                "⚙️ Operational Analytics",
                "💼 Transaction Analytics",
                "🌍 Geographic Fraud Analysis"
            ],
            index=0,  # Default to Homepage
            label_visibility="visible"
        )

        st.divider()

        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.session_state.clear()
            st.rerun()

    # Route to the selected page
    if page == "🏠 Homepage":
        from streamlit_app.pages import Analyst_Dashboard
        Analyst_Dashboard.render()
    elif page == "📊 Transaction Monitoring System":
        from streamlit_app.pages import Fraud_Transaction_Monitoring
        Fraud_Transaction_Monitoring.render()
    elif page == "📈 Rule Performance Analytics":
        from streamlit_app.pages import Rule_Performance
        Rule_Performance.render()
    elif page == "🔍 Fraud Scenario Analysis":
        from streamlit_app.pages import Scenario_Analysis
        Scenario_Analysis.render()
    elif page == "⚙️ Operational Analytics":
        from streamlit_app.pages import operational_analytics
        operational_analytics.render()
    elif page == "💼 Transaction Analytics":
        from streamlit_app.pages import transaction_analytics
        transaction_analytics.render()
    elif page == "🌍 Geographic Fraud Analysis":
        from streamlit_app.pages import geographic_fraud
        geographic_fraud.render()


def main():
    """Main application entry point"""

    # Check API health (without auth)
    try:
        client = get_api_client()
        health = client.health_check()

        if health.get("status") != "healthy":
            st.error("⚠️ API is not healthy. Please check the backend server.")
            st.stop()

    except Exception as e:
        st.error(f"❌ Cannot connect to API server: {str(e)}")
        st.info("Please ensure the FastAPI server is running at http://localhost:8000")
        st.code("python -m uvicorn api.main:app --reload", language="bash")
        st.stop()

    # Authentication check
    if not is_authenticated():
        login_page()
    else:
        main_dashboard()


if __name__ == "__main__":
    main()
