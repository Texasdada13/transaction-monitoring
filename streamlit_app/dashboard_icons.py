"""
Professional SVG Icons for Fraud Detection Dashboard
Designed for Streamlit integration with role-based navigation
"""

import streamlit as st
from typing import Optional


class DashboardIcons:
    """SVG Icon library for fraud detection dashboard"""

    # Icon color schemes
    COLORS = {
        'primary': '#667eea',
        'danger': '#ff6b6b',
        'success': '#10b981',
        'neutral': '#718096',
        'white': '#ffffff',
        'dark': '#1a202c'
    }

    @staticmethod
    def get_icon(icon_name: str, size: int = 20, color: Optional[str] = None) -> str:
        """
        Get SVG icon as string

        Args:
            icon_name: Name of the icon
            size: Size in pixels (default 20)
            color: Color hex code (default uses theme color)

        Returns:
            SVG string
        """
        if color is None:
            color = DashboardIcons.COLORS['primary']

        icons = {
            'dashboard': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="3" width="7" height="7" rx="1.5" stroke="{color}" stroke-width="2"/>
                    <rect x="14" y="3" width="7" height="7" rx="1.5" stroke="{color}" stroke-width="2"/>
                    <rect x="3" y="14" width="7" height="7" rx="1.5" stroke="{color}" stroke-width="2"/>
                    <rect x="14" y="14" width="7" height="7" rx="1.5" stroke="{color}" stroke-width="2"/>
                </svg>
            ''',

            'ai_ml': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="3" stroke="{color}" stroke-width="2"/>
                    <path d="M12 2v4M12 18v4M22 12h-4M6 12H2" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <path d="M20 20l-3-3M7 7L4 4M20 4l-3 3M7 17l-3 3" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="12" cy="12" r="8" stroke="{color}" stroke-width="1" opacity="0.3"/>
                </svg>
            ''',

            'analyst': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="12" width="4" height="9" rx="1" fill="{color}" opacity="0.3"/>
                    <rect x="10" y="8" width="4" height="13" rx="1" fill="{color}" opacity="0.5"/>
                    <rect x="17" y="4" width="4" height="17" rx="1" fill="{color}"/>
                    <path d="M3 3L8 8L13 5L21 11" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            ''',

            'compliance': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L3 7V12C3 16.5 6 20.26 12 21C18 20.26 21 16.5 21 12V7L12 2Z" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>
                    <path d="M9 12L11 14L15 10" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            ''',

            'executive': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="7" width="18" height="14" rx="2" stroke="{color}" stroke-width="2"/>
                    <path d="M8 7V5C8 3.89543 8.89543 3 10 3H14C15.1046 3 16 3.89543 16 5V7" stroke="{color}" stroke-width="2"/>
                    <line x1="12" y1="11" x2="12" y2="17" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <line x1="9" y1="14" x2="15" y2="14" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                </svg>
            ''',

            'fraud': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="{DashboardIcons.COLORS['danger']}" stroke-width="2" stroke-linejoin="round"/>
                    <path d="M2 17L12 22L22 17" stroke="{DashboardIcons.COLORS['danger']}" stroke-width="2" stroke-linejoin="round"/>
                    <path d="M2 12L12 17L22 12" stroke="{DashboardIcons.COLORS['danger']}" stroke-width="2" stroke-linejoin="round"/>
                    <circle cx="19" cy="19" r="3" fill="{DashboardIcons.COLORS['danger']}"/>
                    <path d="M19 18V19.5M19 20.5V19.5M19 19.5H17.5M19 19.5H20.5" stroke="white" stroke-width="1" stroke-linecap="round"/>
                </svg>
            ''',

            'geo': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="{color}" stroke-width="2"/>
                    <ellipse cx="12" cy="12" rx="10" ry="4" stroke="{color}" stroke-width="2"/>
                    <line x1="12" y1="2" x2="12" y2="22" stroke="{color}" stroke-width="2"/>
                    <path d="M2 12H22" stroke="{color}" stroke-width="2"/>
                    <circle cx="16" cy="8" r="2" fill="{color}"/>
                    <circle cx="8" cy="16" r="2" fill="{DashboardIcons.COLORS['danger']}"/>
                </svg>
            ''',

            'operational': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="3" stroke="{color}" stroke-width="2"/>
                    <path d="M12 1V5M12 19V23" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <path d="M4.22 4.22L7.07 7.07M16.93 16.93L19.78 19.78" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <path d="M1 12H5M19 12H23" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <path d="M4.22 19.78L7.07 16.93M16.93 7.07L19.78 4.22" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                </svg>
            ''',

            'rules': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="3" width="18" height="18" rx="2" stroke="{color}" stroke-width="2"/>
                    <path d="M8 10H16" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <path d="M8 14H12" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="6" cy="10" r="1" fill="{color}"/>
                    <circle cx="6" cy="14" r="1" fill="{color}"/>
                    <path d="M16 14L17 15L19 13" stroke="{DashboardIcons.COLORS['success']}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            ''',

            'scenario': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L12 8" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <path d="M12 8L7 13L7 22" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <path d="M12 8L17 13L17 22" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="12" cy="8" r="2" fill="{color}"/>
                    <circle cx="7" cy="22" r="2" fill="{DashboardIcons.COLORS['danger']}"/>
                    <circle cx="17" cy="22" r="2" fill="{DashboardIcons.COLORS['success']}"/>
                </svg>
            ''',

            'transaction': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="6" width="18" height="12" rx="2" stroke="{color}" stroke-width="2"/>
                    <path d="M3 10H21" stroke="{color}" stroke-width="2"/>
                    <circle cx="7" cy="14" r="1.5" fill="{color}"/>
                    <line x1="11" y1="14" x2="17" y2="14" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <path d="M20 21L17 18" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="15" cy="16" r="3" stroke="{color}" stroke-width="2"/>
                </svg>
            ''',

            'settings': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="3" stroke="{color}" stroke-width="2"/>
                    <path d="M12 1V5M12 19V23M23 12H19M5 12H1" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <path d="M20.5 7.5L17.5 10.5M6.5 16.5L3.5 19.5M20.5 16.5L17.5 13.5M6.5 7.5L3.5 4.5" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                </svg>
            '''
        }

        return icons.get(icon_name, icons['dashboard'])

    @staticmethod
    def render_icon_with_text(icon_name: str, text: str, size: int = 20, color: Optional[str] = None) -> str:
        """
        Render icon with text inline

        Args:
            icon_name: Name of the icon
            text: Text to display
            size: Icon size
            color: Icon color

        Returns:
            HTML string with icon and text
        """
        icon = DashboardIcons.get_icon(icon_name, size, color)
        html = f"""
        <div style="display: inline-flex; align-items: center; gap: 10px;">
            <span style="display: inline-flex; align-items: center;">{icon}</span>
            <span style="font-size: 14px; font-weight: 500;">{text}</span>
        </div>
        """
        return html


# Page to icon mapping
PAGE_ICONS = {
    "Analyst Dashboard": "analyst",
    "Fraud Transaction Monitoring": "fraud",
    "Rule Performance Analytics": "rules",
    "Transaction Review": "transaction",
    "Scenario Analysis": "scenario",
    "Operational Analytics": "operational",
    "Geo Analytics": "geo",
    "Compliance & KYC Analytics": "compliance",
    "AI & Machine Learning Intelligence": "ai_ml",
    "Executive Dashboard": "executive"
}


def get_page_icon(page_name: str, size: int = 20, color: Optional[str] = None) -> str:
    """
    Get icon for a specific page name

    Args:
        page_name: Name of the page (without emoji prefix)
        size: Icon size
        color: Icon color

    Returns:
        SVG icon string
    """
    # Remove emoji prefix if present
    clean_name = page_name.split(" ", 1)[-1] if any(char in page_name for char in "🏠📊📈🔍⚙️🌍📋🤖💼") else page_name

    icon_name = PAGE_ICONS.get(clean_name, 'dashboard')
    return DashboardIcons.get_icon(icon_name, size, color)


def format_page_with_icon(page_name: str, size: int = 18) -> str:
    """
    Format page name with its corresponding icon

    Args:
        page_name: Page name (can include emoji prefix)
        size: Icon size

    Returns:
        Formatted HTML string
    """
    # Remove emoji prefix if present
    clean_name = page_name.split(" ", 1)[-1] if any(char in page_name for char in "🏠📊📈🔍⚙️🌍📋🤖💼") else page_name

    icon = get_page_icon(page_name, size)
    return f"""
    <div style="display: flex; align-items: center; gap: 10px; padding: 2px 0;">
        {icon}
        <span>{clean_name}</span>
    </div>
    """
