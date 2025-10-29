# styles/theme.py
import streamlit as st

# Centralized color tokens
COLORS = {
    "DARK_BLUE": "#002B5B",
    "MID_BLUE":  "#0A5CAD",
    "LIGHT_BLUE":"#E5F1FA",
    "BG_GRAY":   "#F5F7FA",
    "WHITE":     "#FFFFFF",
    "ALERT_RED_BG":    "#ffcccc",
    "ALERT_RED_BORDER":"#ff0000",
    "ALERT_ORANGE_BG": "#fff3cd",
    "ALERT_ORANGE_BORDER":"#ffa500",
    "ALERT_LOW_BG":    "#d1ecf1",
    "ALERT_LOW_BORDER":"#17a2b8",
}

def apply_theme():
    # Page config MUST be the first Streamlit call in your main file.
    # (Do it there, not here, to avoid duplicate calls.)
    st.markdown(f"""
    <style>
        /* ===== MASTER THEME: DARK BLUE ===== */
        .main-header {{
            font-size: 2.5rem;
            font-weight: bold;
            color: {COLORS["DARK_BLUE"]};
            margin-bottom: 1rem;
        }}

        .metric-card {{
            background-color: {COLORS["LIGHT_BLUE"]};
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid {COLORS["DARK_BLUE"]};
        }}

        .alert-high {{
            background-color: {COLORS["ALERT_RED_BG"]};
            padding: 0.5rem;
            border-radius: 0.3rem;
            border-left: 4px solid {COLORS["ALERT_RED_BORDER"]};
        }}
        .alert-medium {{
            background-color: {COLORS["ALERT_ORANGE_BG"]};
            padding: 0.5rem;
            border-radius: 0.3rem;
            border-left: 4px solid {COLORS["ALERT_ORANGE_BORDER"]};
        }}
        .alert-low {{
            background-color: {COLORS["ALERT_LOW_BG"]};
            padding: 0.5rem;
            border-radius: 0.3rem;
            border-left: 4px solid {COLORS["ALERT_LOW_BORDER"]};
        }}

        /* ===== TABS ===== */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 2px;
            background-color: {COLORS["BG_GRAY"]};
            padding: 0.5rem;
            border-radius: 0.5rem;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: {COLORS["LIGHT_BLUE"]};
            color: {COLORS["DARK_BLUE"]};
            border-radius: 0.3rem;
            padding: 0.5rem 1rem;
            font-weight: 500;
            border: 2px solid transparent;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {COLORS["DARK_BLUE"]} !important;
            color: {COLORS["WHITE"]} !important;
            border: 2px solid {COLORS["DARK_BLUE"]};
            font-weight: bold;
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            background-color: {COLORS["MID_BLUE"]};
            color: {COLORS["WHITE"]};
        }}
        .stTabs [data-baseweb="tab-panel"] {{
            background-color: {COLORS["WHITE"]};
            padding: 1rem;
            border-radius: 0.5rem;
            margin-top: 0.5rem;
        }}

        /* ===== SIDEBAR ===== */
        [data-testid="stSidebar"] {{
            background-color: {COLORS["DARK_BLUE"]} !important;
        }}
        [data-testid="stSidebar"] *, 
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] label,
        [data-testid="stSidebar"] [data-testid="stDateInput"] label,
        [data-testid="stSidebar"] [data-testid="stNumberInput"] label {{
            color: {COLORS["WHITE"]} !important;
        }}

        /* ===== HEADERS ===== */
        h1, h2, h3, h4, h5, h6 {{
            color: {COLORS["DARK_BLUE"]} !important;
        }}

        /* ===== BUTTONS ===== */
        .stButton>button {{
            background-color: {COLORS["DARK_BLUE"]} !important;
            color: {COLORS["WHITE"]} !important;
            border: none;
            font-weight: 600;
            transition: all 0.3s ease;
        }}
        .stButton>button:hover {{
            background-color: #001A3D !important;
            box-shadow: 0 4px 8px rgba(0, 43, 91, 0.3);
        }}

        /* ===== METRICS ===== */
        [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {{
            color: {COLORS["DARK_BLUE"]} !important;
            font-weight: 600;
        }}

        /* ===== PAGE BACKGROUND ===== */
        .main .block-container {{
            background-color: {COLORS["BG_GRAY"]};
            padding: 2rem;
        }}

        /* ===== DATAFRAMES/TABLES ===== */
        [data-testid="stDataFrame"] {{
            background-color: {COLORS["WHITE"]};
            border: 1px solid {COLORS["LIGHT_BLUE"]};
            border-radius: 0.5rem;
        }}
        [data-testid="stDataFrame"] thead tr th {{
            background-color: {COLORS["DARK_BLUE"]} !important;
            color: {COLORS["WHITE"]} !important;
            font-weight: bold;
        }}

        /* ===== EXPANDERS ===== */
        [data-testid="stExpander"] {{
            background-color: {COLORS["BG_GRAY"]};
            border: 2px solid {COLORS["DARK_BLUE"]};
            border-radius: 0.5rem;
        }}
        [data-testid="stExpander"] summary {{
            color: {COLORS["DARK_BLUE"]} !important;
            font-weight: 600;
        }}

        /* ===== INPUTS ===== */
        .stSelectbox [data-baseweb="select"],
        .stTextInput input {{
            border-color: {COLORS["DARK_BLUE"]};
        }}
        .stTextInput input:focus {{
            border-color: {COLORS["DARK_BLUE"]};
            box-shadow: 0 0 0 2px rgba(0, 43, 91, 0.2);
        }}

        /* ===== DIVIDERS & LINKS ===== */
        hr {{ border-color: {COLORS["DARK_BLUE"]}; opacity: 0.3; }}
        a {{ color: {COLORS["DARK_BLUE"]} !important; font-weight: 600; }}
        a:hover {{ color: {COLORS["MID_BLUE"]} !important; }}
    </style>
    """, unsafe_allow_html=True)
