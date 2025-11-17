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
    page_title="Transaction Screening System",
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
        # Remove top padding and hide collapse button
        st.markdown("""
        <style>
        /* Remove top padding from sidebar */
        [data-testid="stSidebar"] {
            padding-top: 0 !important;
        }

        [data-testid="stSidebar"] > div:first-child {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }

        /* Hide sidebar collapse button */
        [data-testid="collapsedControl"] {
            display: none !important;
        }

        button[kind="header"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Professional header
        st.markdown("""
        <div style='text-align: center; padding: 20px 0 15px 0; border-bottom: 1px solid rgba(255,255,255,0.1);'>
            <h2 style='color: #667eea; margin: 0; font-size: 24px;'>🛡️ Fraud Shield</h2>
            <p style='color: #718096; font-size: 18px; margin-top: 5px; margin-bottom: 0;'>AI-Powered Detection</p>
        </div>
        """, unsafe_allow_html=True)

        # User info section
        user_info = get_user_info()
        user_role = user_info.get('role', 'Unknown').lower()

        st.markdown(f"""
        <div style='padding: 15px 10px; background: rgba(102, 126, 234, 0.1); border-radius: 8px; margin: 15px 0;'>
            <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 8px;'>
                <div style='width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #667eea, #764ba2); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 16px;'>{user_info.get('username', 'U')[0].upper()}</div>
                <div>
                    <p style='margin: 0; color: #1a202c; font-size: 14px; font-weight: 600;'>{user_info.get('username', 'Unknown').upper()} ACCESS</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Professional CSS for navigation
        st.markdown("""
        <style>
        /* Remove Streamlit button styling */
        [data-testid="stSidebar"] .stButton > button {
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
            box-shadow: none !important;
            width: 100%;
            text-align: left;
        }

        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        [data-testid="stSidebar"] .stButton > button:active,
        [data-testid="stSidebar"] .stButton > button:focus {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        /* Navigation item styling */
        .nav-item {
            display: flex;
            align-items: center;
            padding: 12px 15px;
            margin: 2px 0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            background-color: transparent;
            color: #2d3748;
        }

        .nav-item:hover {
            background-color: rgba(102, 126, 234, 0.15);
            transform: translateX(3px);
        }

        .nav-item.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
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

        /* Section headers */
        .nav-section-header {
            color: #718096;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 15px 15px 8px 15px;
            font-weight: 600;
            margin-top: 10px;
        }

        .nav-divider {
            height: 1px;
            background-color: rgba(113, 128, 150, 0.2);
            margin: 15px 0;
        }

        /* 3D Home Button Styling - Active State */
        .home-button-active {
            background: linear-gradient(145deg, #7c8ef7 0%, #8b5cf6 50%, #764ba2 100%) !important;
            color: white !important;
            padding: 12px 20px !important;
            border-radius: 10px !important;
            font-size: 14px !important;
            font-weight: 700 !important;
            text-align: center !important;
            cursor: pointer !important;
            border: none !important;
            box-shadow:
                0 8px 16px rgba(102, 126, 234, 0.4),
                0 4px 8px rgba(118, 75, 162, 0.3),
                inset 0 -3px 6px rgba(0, 0, 0, 0.2),
                inset 0 2px 4px rgba(255, 255, 255, 0.3) !important;
            transition: all 0.2s ease !important;
            transform: translateY(0px) !important;
            position: relative !important;
        }

        .home-button-active:hover {
            transform: translateY(-2px) !important;
            box-shadow:
                0 10px 20px rgba(102, 126, 234, 0.5),
                0 6px 12px rgba(118, 75, 162, 0.4),
                inset 0 -3px 6px rgba(0, 0, 0, 0.2),
                inset 0 2px 4px rgba(255, 255, 255, 0.3) !important;
        }

        .home-button-active:active {
            transform: translateY(2px) !important;
            box-shadow:
                0 4px 8px rgba(102, 126, 234, 0.3),
                0 2px 4px rgba(118, 75, 162, 0.2),
                inset 0 3px 6px rgba(0, 0, 0, 0.3) !important;
        }

        /* 3D Home Button Styling - Inactive State */
        .home-button-inactive {
            background: linear-gradient(145deg, #f0f4ff 0%, #e8edff 100%) !important;
            color: #667eea !important;
            padding: 12px 20px !important;
            border-radius: 10px !important;
            font-size: 14px !important;
            font-weight: 700 !important;
            text-align: center !important;
            cursor: pointer !important;
            border: 2px solid rgba(102, 126, 234, 0.2) !important;
            box-shadow:
                0 6px 12px rgba(102, 126, 234, 0.15),
                0 3px 6px rgba(0, 0, 0, 0.1),
                inset 0 -2px 4px rgba(0, 0, 0, 0.05),
                inset 0 2px 4px rgba(255, 255, 255, 0.8) !important;
            transition: all 0.2s ease !important;
            transform: translateY(0px) !important;
        }

        .home-button-inactive:hover {
            background: linear-gradient(145deg, #e8edff 0%, #dde5ff 100%) !important;
            border-color: rgba(102, 126, 234, 0.4) !important;
            transform: translateY(-2px) !important;
            box-shadow:
                0 8px 16px rgba(102, 126, 234, 0.25),
                0 4px 8px rgba(0, 0, 0, 0.15),
                inset 0 -2px 4px rgba(0, 0, 0, 0.05),
                inset 0 2px 4px rgba(255, 255, 255, 0.8) !important;
        }

        .home-button-inactive:active {
            transform: translateY(2px) !important;
            box-shadow:
                0 3px 6px rgba(102, 126, 234, 0.2),
                0 2px 4px rgba(0, 0, 0, 0.1),
                inset 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        }

        /* Logout button styling - Purple */
        [data-testid="stSidebar"] .stButton:last-of-type > button {
            background: linear-gradient(145deg, #7c8ef7 0%, #8b5cf6 50%, #764ba2 100%) !important;
            color: white !important;
            padding: 12px 20px !important;
            border-radius: 10px !important;
            font-size: 14px !important;
            font-weight: 700 !important;
            text-align: center !important;
            cursor: pointer !important;
            border: none !important;
            box-shadow:
                0 8px 16px rgba(102, 126, 234, 0.4),
                0 4px 8px rgba(118, 75, 162, 0.3),
                inset 0 -3px 6px rgba(0, 0, 0, 0.2),
                inset 0 2px 4px rgba(255, 255, 255, 0.3) !important;
            transition: all 0.2s ease !important;
            transform: translateY(0px) !important;
        }

        [data-testid="stSidebar"] .stButton:last-of-type > button:hover {
            transform: translateY(-2px) !important;
            box-shadow:
                0 10px 20px rgba(102, 126, 234, 0.5),
                0 6px 12px rgba(118, 75, 162, 0.4),
                inset 0 -3px 6px rgba(0, 0, 0, 0.2),
                inset 0 2px 4px rgba(255, 255, 255, 0.3) !important;
        }

        [data-testid="stSidebar"] .stButton:last-of-type > button:active {
            transform: translateY(2px) !important;
            box-shadow:
                0 4px 8px rgba(102, 126, 234, 0.3),
                0 2px 4px rgba(118, 75, 162, 0.2),
                inset 0 3px 6px rgba(0, 0, 0, 0.3) !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Define role-based page structure - Top-level pages and dropdown groups
        ANALYST_TOP_PAGES = ["Analyst Dashboard"]
        ANALYST_DROPDOWN_PAGES = [
            "Fraud Transaction Monitoring",
            "Transaction Review",
            "Rule Performance Analytics",
            "Scenario Analysis",
            "AI & Machine Learning Intelligence"
        ]

        MANAGER_TOP_PAGES = ["Executive Dashboard"]
        MANAGER_DROPDOWN_PAGES = [
            "Transaction Review",
            "Geo Analytics",
            "Compliance & KYC Analytics",
            "Rule Performance Analytics",
            "Scenario Analysis",
            "AI & Machine Learning Intelligence",
            "Operational Analytics"        
        ]

        # Select page structure based on role
        if user_role == "analyst":
            top_pages = ANALYST_TOP_PAGES
            dropdown_pages = ANALYST_DROPDOWN_PAGES
            total_pages = len(top_pages) + len(dropdown_pages)
            #st.caption(f"Access {total_pages} AI powered pages")
        elif user_role == "manager":
            top_pages = MANAGER_TOP_PAGES
            dropdown_pages = MANAGER_DROPDOWN_PAGES
            total_pages = len(top_pages) + len(dropdown_pages)
            #st.caption(f"Access {total_pages} AI powered pages")
        else:
            top_pages = ANALYST_TOP_PAGES
            dropdown_pages = ANALYST_DROPDOWN_PAGES
            total_pages = len(top_pages) + len(dropdown_pages)
            #st.warning(f"⚠️ Unknown role - {total_pages} pages")

        # Initialize selected page in session state
        all_pages = top_pages + dropdown_pages
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = all_pages[0]

        # Render top-level navigation pages
        # Set header and home page based on user role
        if user_role == "analyst":
            st.markdown('<div class="nav-section-header">ANALYST DASHBOARD</div>', unsafe_allow_html=True)
            home_page = "Analyst Dashboard"
        else:  # manager
            st.markdown('<div class="nav-section-header">MANAGER DASHBOARD</div>', unsafe_allow_html=True)
            home_page = "Executive Dashboard"

        # Create small horizontal "Home" button with 3D design - Always Purple
        button_style = """
        <style>
        /* 3D Home Button - Always Purple */
        div[data-testid="stSidebar"] button[key="home_button"],
        [data-testid="stSidebar"] div[data-testid="column"] > div > div > div > button:first-of-type {
            background: linear-gradient(145deg, #7c8ef7 0%, #8b5cf6 50%, #764ba2 100%) !important;
            color: white !important;
            padding: 12px 20px !important;
            border-radius: 10px !important;
            font-size: 14px !important;
            font-weight: 700 !important;
            text-align: center !important;
            cursor: pointer !important;
            border: none !important;
            box-shadow:
                0 8px 16px rgba(102, 126, 234, 0.4),
                0 4px 8px rgba(118, 75, 162, 0.3),
                inset 0 -3px 6px rgba(0, 0, 0, 0.2),
                inset 0 2px 4px rgba(255, 255, 255, 0.3) !important;
            transition: all 0.2s ease !important;
            transform: translateY(0px) !important;
            position: relative !important;
        }

        div[data-testid="stSidebar"] button[key="home_button"]:hover,
        [data-testid="stSidebar"] div[data-testid="column"] > div > div > div > button:first-of-type:hover {
            transform: translateY(-2px) !important;
            box-shadow:
                0 10px 20px rgba(102, 126, 234, 0.5),
                0 6px 12px rgba(118, 75, 162, 0.4),
                inset 0 -3px 6px rgba(0, 0, 0, 0.2),
                inset 0 2px 4px rgba(255, 255, 255, 0.3) !important;
        }

        div[data-testid="stSidebar"] button[key="home_button"]:active,
        [data-testid="stSidebar"] div[data-testid="column"] > div > div > div > button:first-of-type:active {
            transform: translateY(2px) !important;
            box-shadow:
                0 4px 8px rgba(102, 126, 234, 0.3),
                0 2px 4px rgba(118, 75, 162, 0.2),
                inset 0 3px 6px rgba(0, 0, 0, 0.3) !important;
        }
        </style>
        """

        st.markdown(button_style, unsafe_allow_html=True)

        if st.button("Home", key="home_button", use_container_width=True):
            st.session_state.selected_page = home_page
            st.rerun()

         # Render dropdown section for other pages
        st.markdown('<div class="nav-section-header">Access AI powered pages</div>', unsafe_allow_html=True)

        # Create selectbox for dropdown pages
        # Get current selection index - only if current page is in dropdown
        if st.session_state.selected_page in dropdown_pages:
            current_index = dropdown_pages.index(st.session_state.selected_page)
        else:
            # If current page is not in dropdown (e.g., on a dashboard), default to first option
            current_index = 0

        # Display selectbox with clean page names
        st.selectbox(
            label="Select Page",
            options=dropdown_pages,
            index=current_index,
            key="page_selectbox",
            label_visibility="collapsed",
            on_change=lambda: setattr(st.session_state, 'selected_page', st.session_state.page_selectbox)
        )

        # Get selected page
        page = st.session_state.selected_page

        # Divider before logout
        st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)

        # Logout button
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
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
        from streamlit_app.pages import Scenario_Analysis
        Scenario_Analysis.render()
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
