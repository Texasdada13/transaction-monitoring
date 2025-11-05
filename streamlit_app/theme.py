"""
Arriba Advisors - Master Theme and Branding
Centralized theme configuration for consistent styling across all dashboard pages.
"""

import streamlit as st
import os

# Arriba Advisors Color Palette
COLORS = {
    # Primary Palette
    'dark_blue': '#002B5B',
    'medium_blue': '#0A5CAD',
    'light_blue': '#E5F1FA',
    'soft_grey': '#F5F7FA',
    'white': '#FFFFFF',

    # Secondary Palette
    'deep_grey': '#4A586E',
    'mid_grey': '#A3B1C6',
    'pale_blue': '#BBD9F4',
    'hover_white': '#F0F4F8',

    # Status Indicators
    'positive_green': '#2E865F',
    'neutral_blue_grey': '#6A7CA0',
    'critical_red': '#E54848',
    'high_orange': '#F08736',
    'medium_amber': '#F3B65B',
    'low_green_blue': '#51A5BA',
}

# Logo configuration
LOGO_PATH = "streamlit_app/assets/arriba_logo.png"  # Path to logo file
LOGO_URL = "https://via.placeholder.com/200x60/002B5B/FFFFFF?text=ARRIBA+ADVISORS"  # Placeholder

def get_logo_url():
    """Get the logo URL - checks for local file first, then falls back to URL"""
    if os.path.exists(LOGO_PATH):
        return LOGO_PATH
    return LOGO_URL


def apply_master_theme():
    """
    Apply the Arriba Advisors master theme to the current page.
    Should be called at the start of each page's render() function.
    """
    st.markdown(f"""
    <style>
        /* ===== ARRIBA ADVISORS MASTER THEME ===== */

        /* Color Variables */
        :root {{
            --dark-blue: {COLORS['dark_blue']};
            --medium-blue: {COLORS['medium_blue']};
            --light-blue: {COLORS['light_blue']};
            --soft-grey: {COLORS['soft_grey']};
            --white: {COLORS['white']};
            --deep-grey: {COLORS['deep_grey']};
            --mid-grey: {COLORS['mid_grey']};
            --pale-blue: {COLORS['pale_blue']};
            --hover-white: {COLORS['hover_white']};
            --positive-green: {COLORS['positive_green']};
            --neutral-blue-grey: {COLORS['neutral_blue_grey']};
            --critical-red: {COLORS['critical_red']};
            --high-orange: {COLORS['high_orange']};
            --medium-amber: {COLORS['medium_amber']};
            --low-green-blue: {COLORS['low_green_blue']};
        }}

        /* Page Background */
        .main .block-container {{
            background-color: var(--soft-grey);
            padding: 2rem 3rem;
        }}

        /* Headers */
        .main-header {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--dark-blue);
            margin-bottom: 1rem;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}

        h1 {{
            color: var(--dark-blue) !important;
            font-weight: 700 !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        }}

        h2 {{
            color: var(--deep-grey) !important;
            font-weight: 600 !important;
        }}

        h3 {{
            color: var(--medium-blue) !important;
            font-weight: 600 !important;
        }}

        /* Metric Cards */
        .metric-card {{
            background-color: var(--white);
            padding: 1.5rem;
            border-radius: 8px;
            border-left: 4px solid var(--medium-blue);
            box-shadow: 0 2px 4px rgba(0, 43, 91, 0.1);
        }}

        /* Alert Boxes */
        .alert-critical {{
            background-color: #FEE2E2;
            padding: 1rem;
            border-radius: 6px;
            border-left: 4px solid var(--critical-red);
            margin: 1rem 0;
        }}

        .alert-high {{
            background-color: #FED7AA;
            padding: 1rem;
            border-radius: 6px;
            border-left: 4px solid var(--high-orange);
            margin: 1rem 0;
        }}

        .alert-medium {{
            background-color: #FEF3C7;
            padding: 1rem;
            border-radius: 6px;
            border-left: 4px solid var(--medium-amber);
            margin: 1rem 0;
        }}

        .alert-low {{
            background-color: #D1FAE5;
            padding: 1rem;
            border-radius: 6px;
            border-left: 4px solid var(--low-green-blue);
            margin: 1rem 0;
        }}

        /* Sidebar Styling */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, var(--dark-blue) 0%, #001a3d 100%);
            padding-top: 2rem;
        }}

        [data-testid="stSidebar"] .stMarkdown {{
            color: var(--white);
        }}

        [data-testid="stSidebar"] .stSelectbox label {{
            color: var(--white) !important;
        }}

        [data-testid="stSidebar"] hr {{
            border-color: var(--medium-blue);
        }}

        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 12px;
            background-color: transparent;
        }}

        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            padding: 0 24px;
            background-color: var(--white);
            border-radius: 8px;
            color: var(--deep-grey);
            font-weight: 500;
            border: 2px solid var(--pale-blue);
            transition: all 0.3s ease;
        }}

        .stTabs [data-baseweb="tab"]:hover {{
            background-color: var(--light-blue);
            border-color: var(--medium-blue);
        }}

        .stTabs [aria-selected="true"] {{
            background-color: var(--medium-blue);
            color: var(--white);
            border-color: var(--dark-blue);
        }}

        /* Buttons */
        .stButton button {{
            background-color: var(--medium-blue);
            color: var(--white);
            border-radius: 6px;
            font-weight: 500;
            border: none;
            padding: 0.5rem 2rem;
            transition: all 0.3s ease;
        }}

        .stButton button:hover {{
            background-color: var(--dark-blue);
            box-shadow: 0 4px 8px rgba(0, 43, 91, 0.2);
        }}

        /* DataFrames */
        .stDataFrame {{
            border: 1px solid var(--pale-blue);
            border-radius: 8px;
        }}

        /* Streamlit Metrics */
        [data-testid="stMetricValue"] {{
            color: var(--dark-blue);
            font-weight: 700;
        }}

        /* Info/Success/Warning/Error boxes */
        .stAlert {{
            border-radius: 8px;
            border-left-width: 4px;
        }}

        /* Logo Container */
        .logo-container {{
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem;
            margin-bottom: 1.5rem;
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
        }}

        .logo-container img {{
            max-width: 100%;
            height: auto;
        }}

        /* Professional Card Container */
        .professional-card {{
            background-color: var(--white);
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0, 43, 91, 0.08);
            margin-bottom: 1.5rem;
            border: 1px solid var(--pale-blue);
        }}

        /* Status Badges */
        .status-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.875rem;
            font-weight: 500;
        }}

        .status-success {{
            background-color: rgba(46, 134, 95, 0.1);
            color: var(--positive-green);
        }}

        .status-warning {{
            background-color: rgba(240, 135, 54, 0.1);
            color: var(--high-orange);
        }}

        .status-error {{
            background-color: rgba(229, 72, 72, 0.1);
            color: var(--critical-red);
        }}
    </style>
    """, unsafe_allow_html=True)


def render_logo(location="sidebar"):
    """
    Render the Arriba Advisors logo

    Args:
        location: 'sidebar' or 'header' - determines styling
    """
    logo_url = get_logo_url()

    if location == "sidebar":
        st.markdown(f"""
        <div class="logo-container">
            <img src="{logo_url}" alt="Arriba Advisors Logo" style="max-width: 180px;">
        </div>
        """, unsafe_allow_html=True)
    elif location == "header":
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 2rem;">
            <img src="{logo_url}" alt="Arriba Advisors Logo" style="max-width: 250px;">
        </div>
        """, unsafe_allow_html=True)


def render_page_header(title, subtitle=None, show_logo=False):
    """
    Render a professional page header with optional logo

    Args:
        title: Main page title
        subtitle: Optional subtitle
        show_logo: Whether to show logo in header
    """
    if show_logo:
        render_logo(location="header")

    st.markdown(f'<h1 class="main-header">{title}</h1>', unsafe_allow_html=True)

    if subtitle:
        st.markdown(f"### {subtitle}")

    from datetime import datetime
    st.caption(f"Last Updated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}")
    st.markdown("---")


def get_chart_colors():
    """
    Return standardized chart colors for consistency across all visualizations
    """
    return {
        'primary': COLORS['medium_blue'],
        'secondary': COLORS['dark_blue'],
        'success': COLORS['positive_green'],
        'danger': COLORS['critical_red'],
        'warning': COLORS['high_orange'],
        'info': COLORS['low_green_blue'],
        'neutral': COLORS['neutral_blue_grey'],

        # Multi-color palettes for charts
        'gradient': [
            COLORS['dark_blue'],
            COLORS['medium_blue'],
            COLORS['low_green_blue'],
            COLORS['pale_blue'],
            COLORS['light_blue']
        ],

        'status': [
            COLORS['positive_green'],    # Cleared/Approved
            COLORS['critical_red'],       # Rejected/Fraud
            COLORS['high_orange'],        # Escalated/High Risk
            COLORS['medium_amber'],       # Medium Risk
            COLORS['low_green_blue']      # Low Risk
        ],

        'funnel': [
            COLORS['medium_blue'],        # Total
            COLORS['positive_green'],     # Auto-Cleared
            COLORS['medium_amber'],       # Manual Review
            COLORS['high_orange'],        # Rejected
            COLORS['critical_red']        # Fraud Confirmed
        ]
    }
