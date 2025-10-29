"""
Transaction Monitoring Dashboard - Main Application

Streamlit-based fraud detection dashboard with role-based access control.
"""
import streamlit as st
import sys
import os
from styles.theme import apply_theme, COLORS

# Page config MUST be the first Streamlit command
# st.set_page_config(
#     page_title="Transaction Monitoring Dashboard",
#     page_icon="",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# Apply the custom theme
apply_theme()

# Rest of your existing app.py code continues below...


# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from streamlit_app.api_client import get_api_client, is_authenticated, get_user_info, logout

# Page configuration
st.set_page_config(
    page_title="Fraud Detection Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with Dark Blue as master theme
st.markdown("""
<style>
            
    section[data-testid="stSidebarNav"] .css-1v3fvcr, 
        section[data-testid="stSidebarNav"] .css-17ziqus {
            display: none;
        }
            
    /* ===== MASTER THEME: DARK BLUE ===== */
    
    /* Main Header - Dark Blue */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #002B5B;
        margin-bottom: 1rem;
    }
    
    /* Metric/KPI Card - Light Blue background with Dark Blue accent */
    .metric-card {
        background-color: #E5F1FA;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #002B5B;  /* Dark Blue border */
    }
    
    /* Alert Cards */
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
    
    /* ===== TABS STYLING - DARK BLUE ===== */
    
    /* Tab container */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #F5F7FA;
        padding: 0.5rem;
        border-radius: 0.5rem;
    }
    
    /* Individual tabs - Dark Blue */
    .stTabs [data-baseweb="tab"] {
        background-color: #E5F1FA;
        color: #002B5B;
        border-radius: 0.3rem;
        padding: 0.5rem 1rem;
        font-weight: 500;
        border: 2px solid transparent;
    }
    
    /* Active/Selected tab - Dark Blue background */
    .stTabs [aria-selected="true"] {
        background-color: #002B5B !important;
        color: #FFFFFF !important;
        border: 2px solid #002B5B;
        font-weight: bold;
    }
    
    /* Tab hover state */
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #0A5CAD;
        color: #FFFFFF;
    }
    
    /* Tab panel content */
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #FFFFFF;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 0.5rem;
    }
    
    /* ===== SIDEBAR - DARK BLUE ===== */
    
    [data-testid="stSidebar"] {
        background-color: #002B5B !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #FFFFFF !important;
    }
    
    /* Sidebar widgets */
    [data-testid="stSidebar"] [data-testid="stSelectbox"] label,
    [data-testid="stSidebar"] [data-testid="stDateInput"] label,
    [data-testid="stSidebar"] [data-testid="stNumberInput"] label {
        color: #FFFFFF !important;
    }
    
    /* ===== HEADERS - DARK BLUE ===== */
    
    h1, h2, h3, h4, h5, h6 {
        color: #002B5B !important;
    }
    
    /* ===== BUTTONS - DARK BLUE ===== */
    
    .stButton>button {
        background-color: #002B5B !important;
        color: #FFFFFF !important;
        border: none;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #001A3D !important;
        box-shadow: 0 4px 8px rgba(0, 43, 91, 0.3);
    }
    
    /* ===== METRICS - DARK BLUE ACCENTS ===== */
    
    [data-testid="stMetricLabel"] {
        color: #002B5B !important;
        font-weight: 600;
    }
    
    [data-testid="stMetricValue"] {
        color: #002B5B !important;
    }
    
    /* ===== PAGE BACKGROUND ===== */
    
    .main .block-container {
        background-color: #F5F7FA;
        padding: 2rem;
    }
    
    /* ===== DATAFRAMES/TABLES ===== */
    
    [data-testid="stDataFrame"] {
        background-color: #FFFFFF;
        border: 1px solid #E5F1FA;
        border-radius: 0.5rem;
    }
    
    /* Table headers - Dark Blue */
    [data-testid="stDataFrame"] thead tr th {
        background-color: #002B5B !important;
        color: #FFFFFF !important;
        font-weight: bold;
    }
    
    /* ===== EXPANDABLE SECTIONS ===== */
    
    [data-testid="stExpander"] {
        background-color: #F5F7FA;
        border: 2px solid #002B5B;
        border-radius: 0.5rem;
    }
    
    [data-testid="stExpander"] summary {
        color: #002B5B !important;
        font-weight: 600;
    }
    
    /* ===== SELECT BOXES & INPUTS - DARK BLUE ===== */
    
    .stSelectbox [data-baseweb="select"] {
        border-color: #002B5B;
    }
    
    .stTextInput input {
        border-color: #002B5B;
    }
    
    .stTextInput input:focus {
        border-color: #002B5B;
        box-shadow: 0 0 0 2px rgba(0, 43, 91, 0.2);
    }
    
    /* ===== DIVIDERS - DARK BLUE ===== */
    
    hr {
        border-color: #002B5B;
        opacity: 0.3;
    }
    
    /* ===== LINKS - DARK BLUE ===== */
    
    a {
        color: #002B5B !important;
        font-weight: 600;
    }
    
    a:hover {
        color: #0A5CAD !important;
    }
</style>
""", unsafe_allow_html=True)



def login_page():
    """Display login page"""
    st.markdown('<div class="main-header">Arriba Advisors Fraud Detection System</div>', unsafe_allow_html=True)
    st.markdown("### User Authentication")

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

                        st.success(f"Welcome, {username}!")
                        st.session_state.logged_in = True
                        st.session_state.user_info = user_info
                        st.rerun()

                    except Exception as e:
                        st.error(f"Login failed: {str(e)}")
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
            ["Real_Time_Monitoring", "Risk Intelligence", "Investigation Tools", "QuantShield AI Modules", "System Health"],
            label_visibility="collapsed"
        )

        st.divider()

        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.session_state.clear()
            st.rerun()

    # Main content
    if page == "Real_Time_Monitoring":
        from streamlit_app.pages import Real_Time_Monitoring as real_time_monitoring
        real_time_monitoring.render()
    if page == "Risk Intelligence":
        from streamlit_app.pages import Risk_Intelligence as risk_analytics
        risk_analytics.render()
    elif page == "Investigation Tools":
        from streamlit_app.pages import Case_Investigation_Center as investigation_tools
        investigation_tools.render()
    elif page == "QuantShield AI Modules":
        from streamlit_app.pages import QuantShield_AI_Modules as model_ai
        model_ai.render()
    elif page == "System Health":
        st.info("System Health page - Coming soon!")


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
