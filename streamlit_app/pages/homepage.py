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

# Generate synthetic dataset for visualization
np.random.seed(42)

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

    # Header
    st.markdown("# Arriba Advisors Transaction Screening System")
    st.markdown("### Executive Dashboard - Transaction Fraud Monitoring & Prevention")
    st.caption(f"Last Updated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}")

    st.markdown("---")

    # Key Performance Indicators
    st.markdown("## 📊 Key Performance Indicators")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Transactions Today", "12,547", delta="↑ 8.2%")
    with col2:
        st.metric("Auto-Approved", "11,915 (95%)", delta="↑ 2.1%")
    with col3:
        st.metric("Flagged for Review", "632 (5%)", delta="↓ 1.3%")
    with col4:
        st.metric("Fraud Detected", "47", delta="↓ 12%")
    with col5:
        st.metric("Detection Accuracy", "94.2%", delta="↑ 1.5%")

    st.markdown("---")

    # Transaction Flow Funnel and Analyst Decision Trends
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📉 Transaction Processing Funnel")

        funnel_data = pd.DataFrame({
            'Stage': ['Total Transactions', 'Auto-Cleared', 'Manual Review', 'Rejected', 'Fraud Confirmed'],
            'Count': [12547, 11915, 632, 85, 47],
            'Percentage': [100, 95, 5, 0.68, 0.37]
        })

        fig_funnel = go.Figure(go.Funnel(
            y=funnel_data['Stage'],
            x=funnel_data['Count'],
            textinfo="value+percent initial",
            marker=dict(color=['#0A5CAD', '#2E865F', '#F3B65B', '#F08736', '#E54848'])
        ))

        fig_funnel.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_funnel, use_container_width=True)

        # Cost savings
        st.info(f"💰 **Cost Savings**: Manual reviews prevented: 11,915 × $5 = **$59,575/day**")

    with col2:
        st.subheader("📊 Analyst Decision Trends (30 Days)")

        fig_decisions = go.Figure()

        fig_decisions.add_trace(go.Bar(
            x=analyst_decisions_df['date'],
            y=analyst_decisions_df['cleared'],
            name='Cleared',
            marker_color='#2E865F'
        ))

        fig_decisions.add_trace(go.Bar(
            x=analyst_decisions_df['date'],
            y=analyst_decisions_df['rejected'],
            name='Rejected',
            marker_color='#E54848'
        ))

        fig_decisions.add_trace(go.Bar(
            x=analyst_decisions_df['date'],
            y=analyst_decisions_df['escalated'],
            name='Escalated',
            marker_color='#F08736'
        ))

        fig_decisions.add_trace(go.Scatter(
            x=analyst_decisions_df['date'],
            y=analyst_decisions_df['confidence'],
            name='Confidence %',
            yaxis='y2',
            line=dict(color='#0A5CAD', width=3)
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

    # Recent Alerts Summary (moved below funnel)
    st.markdown("## 🚨 Recent High-Risk Alerts")

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

    # System Activity Timeline
    st.markdown("## 📈 Transaction Activity (Last 24 Hours)")

    # Generate sample time series data
    hours = pd.date_range(end=datetime.now(), periods=24, freq='H')
    transactions = np.random.poisson(lam=500, size=24) + np.random.randint(-50, 100, 24)
    fraud_detected = np.random.poisson(lam=2, size=24)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hours,
        y=transactions,
        name='Total Transactions',
        line=dict(color='#0A5CAD', width=2),
        fill='tozeroy'
    ))

    fig.add_trace(go.Scatter(
        x=hours,
        y=fraud_detected,
        name='Fraud Detected',
        line=dict(color='#E54848', width=2),
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
        st.markdown("### 📊 Transaction Monitoring")
        st.markdown("Real-time transaction monitoring with live alerts and automated decision-making.")
        if st.button("Open Transaction Monitor", use_container_width=True):
            st.info("Navigate using sidebar to Transaction Monitoring System")

    with col2:
        st.markdown("### 🔍 Scenario Analysis")
        st.markdown("Deep-dive analysis of 13 fraud scenarios with detailed rule breakdowns.")
        if st.button("View Fraud Scenarios", use_container_width=True):
            st.info("Navigate using sidebar to Fraud Scenario Analysis")

    with col3:
        st.markdown("### 📈 Rule Performance")
        st.markdown("Analyze fraud detection rule effectiveness with advanced metrics.")
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

    st.caption("© 2024 Arriba Advisors. All rights reserved. | Transaction Screening Platform")
