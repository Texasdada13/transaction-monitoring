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
</style>
""", unsafe_allow_html=True)


def login_page():
    """Display login page"""
    st.markdown('<div class="main-header">🛡️ Fraud Detection System</div>', unsafe_allow_html=True)
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
        st.markdown("### 🛡️ Fraud Detection")

        # User info
        user_info = get_user_info()
        st.markdown(f"**User:** {user_info.get('username', 'Unknown')}")
        st.markdown(f"**Role:** {user_info.get('role', 'Unknown').title()}")

        st.divider()

        # Navigation
        st.markdown("### Navigation")

        page = st.radio(
            "Select Page",
            ["🚨 Real-Time Monitoring", "📊 Risk Analytics", "🔍 Investigation Tools", "🏥 System Health"],
            label_visibility="collapsed"
        )

        st.divider()

        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.session_state.clear()
            st.rerun()

    # Main content
    if page == "🚨 Real-Time Monitoring":
        from streamlit_app.pages import real_time_monitoring
        real_time_monitoring.render()
    elif page == "📊 Risk Analytics":
        from streamlit_app.pages import risk_analytics
        risk_analytics.render()
    elif page == "🔍 Investigation Tools":
        st.info("🔍 Investigation Tools page - Coming soon!")
    elif page == "🏥 System Health":
        st.info("🏥 System Health page - Coming soon!")


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
