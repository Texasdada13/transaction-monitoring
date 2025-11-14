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
from streamlit_app.theme import apply_master_theme, render_logo
from streamlit_app.dashboard_icons import DashboardIcons, get_page_icon

# Page configuration
st.set_page_config(
    page_title="Arriba Advisors - Transaction Screening",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply master theme
apply_master_theme()


def login_page():
    """Display login page"""
    st.markdown('<div class="main-header">🛡️ Transaction Screening System</div>', unsafe_allow_html=True)
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

            - **Analyst**: Username: `analyst`, Password: `analyst123` (Limited Access - 5 pages)
            - **Manager**: Username: `manager`, Password: `manager123` (Full Access - 10 pages)
            """)


def main_dashboard():
    """Main dashboard after authentication"""

    # Sidebar
    with st.sidebar:
        # Logo
        render_logo(location="sidebar")

        st.markdown("### 🛡️ Arriba Advisors")
        st.markdown("**Transaction Screening System**")

        # User info
        user_info = get_user_info()
        user_role = user_info.get('role', 'Unknown').lower()
        st.markdown(f"**User:** {user_info.get('username', 'Unknown')}")
        st.markdown(f"**Role:** {user_info.get('role', 'Unknown').title()}")

        # Debug info - show access level
        if user_role == "analyst":
            st.info("🔒 Limited Access (5 pages)")
        elif user_role == "manager":
            st.success("🔓 Full Access (10 pages)")

        st.divider()

        # Navigation
        st.markdown("### 📍 Navigation")

        # Add custom CSS for professional icon navigation
        st.markdown("""
        <style>
        .nav-item {
            display: flex;
            align-items: center;
            padding: 10px 12px;
            margin: 4px 0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            background-color: transparent;
            border: 1px solid transparent;
        }

        .nav-item:hover {
            background-color: rgba(102, 126, 234, 0.1);
            border-left: 3px solid #667eea;
        }

        .nav-item.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-left: 3px solid #667eea;
        }

        .nav-item svg {
            width: 20px;
            height: 20px;
            margin-right: 12px;
            flex-shrink: 0;
        }

        .nav-item-text {
            font-size: 14px;
            font-weight: 500;
        }

        /* Style buttons to look like nav items */
        .stButton > button {
            width: 100%;
            text-align: left;
            background-color: transparent;
            border: none;
            padding: 0;
            margin: 0;
        }
        </style>
        """, unsafe_allow_html=True)

        # Define role-based page access (clean names without emojis)
        ANALYST_PAGES = [
            "Analyst Dashboard",
            "Fraud Transaction Monitoring",
            "Geo Analytics",
            "Transaction Review",
            "Compliance & KYC Analytics"
        ]

        MANAGER_PAGES = [
            "Analyst Dashboard",
            "Fraud Transaction Monitoring",
            "Rule Performance Analytics",
            "Transaction Review",
            "Scenario Analysis",
            "Operational Analytics",
            "Geo Analytics",
            "Compliance & KYC Analytics",
            "AI & Machine Learning Intelligence",
            "Executive Dashboard"
        ]

        # Filter pages based on role
        if user_role == "analyst":
            available_pages = ANALYST_PAGES
            st.caption(f"✓ Showing {len(ANALYST_PAGES)} analyst pages")
        elif user_role == "manager":
            available_pages = MANAGER_PAGES
            st.caption(f"✓ Showing {len(MANAGER_PAGES)} manager pages")
        else:
            # Default to analyst pages for unknown roles
            available_pages = ANALYST_PAGES
            st.warning(f"⚠️ Unknown role '{user_role}' - defaulting to analyst pages")

        # Initialize selected page in session state
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = available_pages[0]

        # Professional navigation with icons inline
        page = st.session_state.selected_page

        # Render navigation items with icons inline
        for page_name in available_pages:
            # Get icon for the page
            icon_color = "white" if page_name == st.session_state.selected_page else "#667eea"
            icon = get_page_icon(page_name, size=18, color=icon_color)
            is_selected = (page_name == st.session_state.selected_page)

            # Create container with icon and button
            nav_container = st.container()
            with nav_container:
                col_icon, col_button = st.columns([0.12, 0.88])

                with col_icon:
                    # Display icon
                    st.markdown(
                        f'<div style="padding-top: 8px;">{icon}</div>',
                        unsafe_allow_html=True
                    )

                with col_button:
                    # Create clickable button
                    if st.button(
                        page_name,
                        key=f"nav_{page_name}",
                        use_container_width=True,
                        type="primary" if is_selected else "secondary"
                    ):
                        st.session_state.selected_page = page_name
                        st.rerun()

        # Update page variable
        page = st.session_state.selected_page

        st.divider()

        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.session_state.clear()
            st.rerun()

    # Route to the selected page (clean names without emojis)
    if page == "Analyst Dashboard":
        from streamlit_app.pages import Analyst_Dashboard
        Analyst_Dashboard.render()
    elif page == "Fraud Transaction Monitoring":
        from streamlit_app.pages import Fraud_Transaction_Monitoring
        Fraud_Transaction_Monitoring.render()
    elif page == "Rule Performance Analytics":
        from streamlit_app.pages import Rule_Performance
        Rule_Performance.render()
    elif page == "Transaction Review":
        from streamlit_app.pages import Transaction_Review
        Transaction_Review.render()
    elif page == "Scenario Analysis":
        from streamlit_app.pages import scenario_analysis
        scenario_analysis.render()
    elif page == "Operational Analytics":
        from streamlit_app.pages import operational_analytics
        operational_analytics.render()
    elif page == "Geo Analytics":
        from streamlit_app.pages import Geo_Analytics
        Geo_Analytics.render()
    elif page == "Compliance & KYC Analytics":
        from streamlit_app.pages import Compliance_KYC_Analytics
        Compliance_KYC_Analytics.render()
    elif page == "AI & Machine Learning Intelligence":
        from streamlit_app.pages import AI_ML_Intelligence
        AI_ML_Intelligence.render()
    elif page == "Executive Dashboard":
        from streamlit_app.pages import Executive_Dashboard
        Executive_Dashboard.render()


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
