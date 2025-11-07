"""
Homepage - Arriba Advisors Transaction Screening System

Executive dashboard with key performance indicators and system overview.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

from streamlit_app.api_client import get_api_client
from streamlit_app.theme import apply_master_theme, render_page_header, get_chart_colors

 
    # Generate synthetic dataset for visualization
np.random.seed(42)

# Rule performance data (20 rules)
rule_names = [
    "Transaction Amount Anomalies", "Transaction Frequency", "Recipient Verification Status",
    "Recipient Blacklist Status", "Device Fingerprinting", "VPN or Proxy Usage",
    "Geo-Location Flags", "Behavioral Biometrics", "Time Since Last Transaction",
    "Social Trust Score", "Account Age", "High-Risk Transaction Times",
    "Past Fraudulent Behavior", "Location-Inconsistent Transactions", "Normalized Transaction Amount",
    "Transaction Context Anomalies", "Fraud Complaints Count", "Merchant Category Mismatch",
    "User Daily Limit Exceeded", "Recent High-Value Transaction"
]

rule_performance_df = pd.DataFrame({
    'rule_name': rule_names,
    'trigger_frequency': np.random.randint(50, 500, 20),
    'precision': np.random.uniform(0.65, 0.98, 20),
    'false_positive_rate': np.random.uniform(0.02, 0.35, 20),
    'avg_contribution': np.random.uniform(5, 35, 20),
    'confirmed_fraud_count': np.random.randint(10, 200, 20),
    'rule_weight': [32, 35, 26, 22, 30, 22, 32, 15, 24, 18, 8, 28, 35, 20, 18, 24, 12, 4, 10, 6]
})

# Analyst decision data (30 days)
dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
analyst_decisions_df = pd.DataFrame({
    'date': dates,
    'cleared': np.random.randint(150, 250, 30),
    'rejected': np.random.randint(20, 80, 30),
    'escalated': np.random.randint(10, 40, 30)
})
analyst_decisions_df['total'] = analyst_decisions_df[['cleared', 'rejected', 'escalated']].sum(axis=1)
analyst_decisions_df['confidence'] = np.minimum(50 + np.arange(30) * 1.2 + np.random.uniform(-5, 5, 30), 95)

def render():
    """Render the Homepage"""

    # Apply theme
    apply_master_theme()

    # Header
    render_page_header(
        title="Arriba Advisors Transaction Screening System",
        subtitle="Real-Time Fraud Detection & Prevention Analytics",
        show_logo=False  # Logo is in sidebar
    )

    # Get standardized chart colors
    colors = get_chart_colors()

    # # Key Performance Indicators
    # st.markdown("## 📊 Key Performance Indicators")

    # col1, col2, col3, col4, col5 = st.columns(5)

    # with col1:
    #     st.metric("Total Transactions Today", "12,547", delta="↑ 8.2%")
    # with col2:
    #     st.metric("Auto-Approved", "11,915 (95%)", delta="↑ 2.1%")
    # with col3:
    #     st.metric("Flagged for Review", "632 (5%)", delta="↓ 1.3%")
    # with col4:
    #     st.metric("Fraud Detected", "47", delta="↓ 12%")
    # with col5:
    #     st.metric("Detection Accuracy", "94.2%", delta="↑ 1.5%")

    # st.markdown("---")

 # Recent Alerts Summary
    st.markdown("## ⚡ Threat Detection Command Center")

    recent_alerts = pd.DataFrame({
        'Time': ['10 min ago', '25 min ago', '1 hr ago', '2 hr ago', '3 hr ago'],
        'Transaction ID': ['TXN-78945', 'TXN-78932', 'TXN-78901', 'TXN-78876', 'TXN-78834'],
        'Amount': ['$15,000', '$12,500', '$45,000', '$3,200', '$8,900'],
        'Risk Score': [0.89, 0.96, 0.91, 0.88, 0.84],
        'Status': ['Under Review', 'Blocked', 'Escalated', 'Under Review', 'Cleared'],
        'Scenario': ['Large Transfer', 'Account Takeover', 'Vendor Impersonation', 'Duplicate Check', 'Odd Hours']
    })
      
    st.dataframe(
        recent_alerts,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Risk Score': st.column_config.ProgressColumn(
                'Risk Score',
                min_value=0,
                max_value=1,
                format='%.2f'
            )
        }
    )

    st.markdown("---")

       # Transaction Flow Funnel
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🤖 Transaction Lifecycle Monitor")

        funnel_data = pd.DataFrame({
            'Stage': ['Total Transactions', 'Auto-Cleared', 'Manual Review', 'Rejected', 'Fraud Confirmed'],
            'Count': [12547, 11915, 632, 85, 47],
            'Percentage': [100, 95, 5, 0.68, 0.37]
        })

        fig_funnel = go.Figure(go.Funnel(
            y=funnel_data['Stage'],
            x=funnel_data['Count'],
            textinfo="value+percent initial",
            marker=dict(color=colors['funnel'])  # Standardized Arriba palette
        ))

        fig_funnel.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_funnel, use_container_width=True)

        # Cost savings
        st.info(f"💰 **Cost Savings**: Manual reviews prevented: 11,915 × $5 = **$59,575/day**")

    with col2:
        st.subheader("🧠 Decision Pattern Analytics")

        fig_decisions = go.Figure()

        fig_decisions.add_trace(go.Bar(
            x=analyst_decisions_df['date'],
            y=analyst_decisions_df['cleared'],
            name='Cleared',
            marker_color=colors['success']
        ))

        fig_decisions.add_trace(go.Bar(
            x=analyst_decisions_df['date'],
            y=analyst_decisions_df['rejected'],
            name='Rejected',
            marker_color=colors['danger']
        ))

        fig_decisions.add_trace(go.Bar(
            x=analyst_decisions_df['date'],
            y=analyst_decisions_df['escalated'],
            name='Escalated',
            marker_color=colors['warning']
        ))

        fig_decisions.add_trace(go.Scatter(
            x=analyst_decisions_df['date'],
            y=analyst_decisions_df['confidence'],
            name='Confidence %',
            yaxis='y2',
            line=dict(color=colors['primary'], width=3)
        ))

        fig_decisions.update_layout(
            barmode='stack',
            height=400,
            yaxis=dict(title='Transaction Count'),
            yaxis2=dict(title='Confidence %', overlaying='y', side='right', range=[0, 100]),
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )

        st.plotly_chart(fig_decisions, use_container_width=True)

    st.markdown("---")

    # # Executive Summary
    # st.markdown("## 💼 Executive Summary")

    # col1, col2 = st.columns([2, 1])

    # with col1:
    #     st.markdown("""
    #     **System Performance Overview**

    #     The fraud detection system is operating at optimal efficiency with a **94.2% accuracy rate**.
    #     Today's transaction volume shows healthy growth (+8.2%) while maintaining strong fraud prevention metrics.

    #     **Key Highlights:**
    #     - ✅ **95% auto-approval rate** - Minimal false positives
    #     - ✅ **47 fraud cases detected** - $2.3M in potential losses prevented
    #     - ✅ **Sub-second detection** - Real-time risk assessment
    #     - ✅ **6.2% false positive rate** - Down from 7.0% last week

    #     **Risk Areas Monitored:**
    #     - Account Takeover Attempts
    #     - Payment Fraud & BEC Attacks
    #     - Money Laundering Patterns
    #     - Geographic Anomalies
    #     - Beneficiary Fraud
    #     """)

    # with col2:
    #     st.markdown("**System Status**")
    #     st.success("🟢 **All Systems Operational**")

    #     st.markdown("**Active Detection Modules**")
    #     st.info("26 fraud detection rules")

    #     st.markdown("**Coverage**")
    #     st.info("7 fraud scenarios")

    #     st.markdown("**Response Time**")
    #     st.info("< 500ms average")

    # st.markdown("---")

    # # Financial Impact
    # st.markdown("## 💰 Financial Impact Analysis")

    # col1, col2, col3, col4 = st.columns(4)

    # with col1:
    #     st.metric("Fraud Prevented (Today)", "$2.3M", delta="-12% vs. yesterday")
    # with col2:
    #     st.metric("Fraud Prevented (MTD)", "$47.8M", delta="↑ 15%")
    # with col3:
    #     st.metric("Manual Review Costs Saved", "$59,575", delta="Per day")
    # with col4:
    #     st.metric("Average Fraud Amount", "$48,936", delta="↓ 8%")

    # st.markdown("---")

    # System Activity Timeline
    st.markdown("## 📊 Live Transaction Pulse")

    # Generate sample time series data
    hours = pd.date_range(end=datetime.now(), periods=24, freq='H')
    transactions = np.random.poisson(lam=500, size=24) + np.random.randint(-50, 100, 24)
    fraud_detected = np.random.poisson(lam=2, size=24)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hours,
        y=transactions,
        name='Total Transactions',
        line=dict(color=colors['primary'], width=2),
        fill='tozeroy'
    ))

    fig.add_trace(go.Scatter(
        x=hours,
        y=fraud_detected,
        name='Fraud Detected',
        line=dict(color=colors['danger'], width=2),
        mode='lines+markers',
        yaxis='y2'
    ))

    fig.update_layout(
        yaxis=dict(title='Transaction Volume'),
        yaxis2=dict(title='Fraud Cases', overlaying='y', side='right'),
        hovermode='x unified',
        height=400,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Quick Access Panels
    st.markdown("## 🚀 Quick Access")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🤖 AI Transaction Intelligence")
        st.markdown("Real-time AI-powered transaction monitoring with automated decision intelligence.")
        if st.button("Open Transaction Monitor", use_container_width=True):
            st.info("Navigate using sidebar to Transaction Monitoring System")

    with col2:
        st.markdown("### 🧠 AI Scenario Intelligence")
        st.markdown("ML-driven analysis of 13 fraud scenarios with AI-powered rule intelligence.")
        if st.button("View Fraud Scenarios", use_container_width=True):
            st.info("Navigate using sidebar to Fraud Scenario Analysis")

    with col3:
        st.markdown("### 📊 AI Rule Performance Intelligence")
        st.markdown("ML-powered fraud detection rule analysis with predictive performance metrics.")
        if st.button("Analyze Rules", use_container_width=True):
            st.info("Navigate using sidebar to Rule Performance Analytics")

    st.markdown("---")

 

    # Footer
    st.markdown("## ℹ️ System Information")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**System Version:** 2.5.3")
        st.markdown("**Database:** SQLite (Production-Ready)")
    with col2:
        st.markdown("**API Status:** ✅ Healthy")
        st.markdown("**Last Sync:** Just now")
    with col3:
        st.markdown("**Support:** support@arribaadvisors.com")
        st.markdown("**Documentation:** Available in sidebar")

    st.caption("© 2024 Arriba Advisors. All rights reserved. | Real-Time Fraud Detection Platform")

if __name__ == "__main__" or True:
    render()