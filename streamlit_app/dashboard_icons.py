"""
Professional SVG Icons for Fraud Detection Dashboard
Based on HTML icon template - clean, scalable, and professional
"""

import streamlit as st
from typing import Optional


class DashboardIcons:
    """SVG Icon library for fraud detection dashboard"""

    @staticmethod
    def get_icon(icon_name: str, size: int = 20, color: str = "#667eea") -> str:
        """
        Get SVG icon as string

        Args:
            icon_name: Name of the icon
            size: Size in pixels (default 20)
            color: Icon color (default #667eea)

        Returns:
            SVG string
        """

        icons = {
            'dashboard': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="3" width="7" height="7" rx="1.5" stroke="{color}" stroke-width="2" fill="none"/>
                    <rect x="14" y="3" width="7" height="7" rx="1.5" stroke="{color}" stroke-width="2" fill="none"/>
                    <rect x="3" y="14" width="7" height="7" rx="1.5" stroke="{color}" stroke-width="2" fill="none"/>
                    <rect x="14" y="14" width="7" height="7" rx="1.5" stroke="{color}" stroke-width="2" fill="none"/>
                </svg>
            ''',

            'ai_ml': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="3" stroke="{color}" stroke-width="2" fill="none"/>
                    <path d="M12 2v4M12 18v4M22 12h-4M6 12H2" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <path d="M20 20l-3-3M7 7L4 4M20 4l-3 3M7 17l-3 3" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="12" cy="12" r="8" stroke="{color}" stroke-width="1" opacity="0.3" fill="none"/>
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
                    <path d="M12 2L3 7V12C3 16.5 6 20.26 12 21C18 20.26 21 16.5 21 12V7L12 2Z" stroke="{color}" stroke-width="2" stroke-linejoin="round" fill="none"/>
                    <path d="M9 12L11 14L15 10" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            ''',

            'executive': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="7" width="18" height="14" rx="2" stroke="{color}" stroke-width="2" fill="none"/>
                    <path d="M8 7V5C8 3.89543 8.89543 3 10 3H14C15.1046 3 16 3.89543 16 5V7" stroke="{color}" stroke-width="2"/>
                    <line x1="12" y1="11" x2="12" y2="17" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <line x1="9" y1="14" x2="15" y2="14" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                </svg>
            ''',

            'fraud': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#ff6b6b" stroke-width="2" stroke-linejoin="round" fill="none"/>
                    <path d="M2 17L12 22L22 17" stroke="#ff6b6b" stroke-width="2" stroke-linejoin="round"/>
                    <path d="M2 12L12 17L22 12" stroke="#ff6b6b" stroke-width="2" stroke-linejoin="round"/>
                    <circle cx="19" cy="19" r="3" fill="#ff6b6b"/>
                    <path d="M19 18V19.5M19 20.5V19.5M19 19.5H17.5M19 19.5H20.5" stroke="white" stroke-width="1" stroke-linecap="round"/>
                </svg>
            ''',

            'geo': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="{color}" stroke-width="2" fill="none"/>
                    <ellipse cx="12" cy="12" rx="10" ry="4" stroke="{color}" stroke-width="2" fill="none"/>
                    <line x1="12" y1="2" x2="12" y2="22" stroke="{color}" stroke-width="2"/>
                    <path d="M2 12H22" stroke="{color}" stroke-width="2"/>
                    <circle cx="16" cy="8" r="2" fill="{color}"/>
                    <circle cx="8" cy="16" r="2" fill="#ff6b6b"/>
                </svg>
            ''',

            'operational': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="3" stroke="{color}" stroke-width="2" fill="none"/>
                    <path d="M12 1V5M12 19V23" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <path d="M4.22 4.22L7.07 7.07M16.93 16.93L19.78 19.78" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <path d="M1 12H5M19 12H23" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <path d="M4.22 19.78L7.07 16.93M16.93 7.07L19.78 4.22" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                </svg>
            ''',

            'rules': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="3" width="18" height="18" rx="2" stroke="{color}" stroke-width="2" fill="none"/>
                    <path d="M8 10H16" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <path d="M8 14H12" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="6" cy="10" r="1" fill="{color}"/>
                    <circle cx="6" cy="14" r="1" fill="{color}"/>
                    <path d="M16 14L17 15L19 13" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            ''',

            'scenario': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L12 8" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <path d="M12 8L7 13L7 22" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <path d="M12 8L17 13L17 22" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="12" cy="8" r="2" fill="{color}"/>
                    <circle cx="7" cy="22" r="2" fill="#ff6b6b"/>
                    <circle cx="17" cy="22" r="2" fill="#10b981"/>
                </svg>
            ''',

            'transaction': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="6" width="18" height="12" rx="2" stroke="{color}" stroke-width="2" fill="none"/>
                    <path d="M3 10H21" stroke="{color}" stroke-width="2"/>
                    <circle cx="7" cy="14" r="1.5" fill="{color}"/>
                    <line x1="11" y1="14" x2="17" y2="14" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <path d="M20 21L17 18" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="15" cy="16" r="3" stroke="{color}" stroke-width="2" fill="none"/>
                </svg>
            ''',

            'settings': f'''
                <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 15C13.6569 15 15 13.6569 15 12C15 10.3431 13.6569 9 12 9C10.3431 9 9 10.3431 9 12C9 13.6569 10.3431 15 12 15Z" stroke="{color}" stroke-width="2" fill="none"/>
                    <path d="M19.6224 10.3954L18.5247 7.7448L20.5207 6.00436L18.3611 3.84481L16.6208 5.84085L13.9702 4.74308L12.9655 2H10.9655L9.96046 4.74308L7.30989 5.84085L5.56945 3.84481L3.40991 6.00436L5.40595 7.7448L4.30818 10.3954L1.565 11.4V13.4L4.30818 14.4046L5.40595 17.0552L3.40991 18.7956L5.56945 20.9552L7.30989 18.9591L9.96046 20.0569L10.9655 22.8H12.9655L13.9702 20.0569L16.6208 18.9591L18.3611 20.9552L20.5207 18.7956L18.5247 17.0552L19.6224 14.4046L22.365 13.4V11.4L19.6224 10.3954Z" stroke="{color}" stroke-width="2" fill="none"/>
                </svg>
            '''
        }

        return icons.get(icon_name, icons['dashboard'])


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


def get_page_icon(page_name: str, size: int = 20, color: str = "#667eea") -> str:
    """
    Get icon for a specific page name

    Args:
        page_name: Name of the page
        size: Icon size in pixels
        color: Icon color

    Returns:
        SVG icon string
    """
    icon_name = PAGE_ICONS.get(page_name, 'dashboard')
    return DashboardIcons.get_icon(icon_name, size, color)
