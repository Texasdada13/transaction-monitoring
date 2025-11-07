"""
Summary Dashboard Page

Executive overview with key metrics, funnels, heatmaps, and treemaps.
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
    """Render the Summary Dashboard page"""

    # Apply theme
    apply_master_theme()

    # Header
    render_page_header(
        title="Executive Summary Dashboard",
        subtitle="High-level overview of fraud detection performance and trends",
        show_logo=False
    )

    # Get standardized chart colors
    colors = get_chart_colors()

    # Key metrics row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Transactions Today", "12,547", delta="↑ 8.2%")
    with col2:
        st.metric("Auto-Cleared", "11,915 (95%)", delta="↑ 2.1%")
    with col3:
        st.metric("Flagged for Review", "632 (5%)", delta="↓ 1.3%")
    with col4:
        st.metric("Fraud Detected", "47", delta="↓ 12%")
    with col5:
        st.metric("False Positive Rate", "6.2%", delta="↓ 0.8%")

    st.markdown("---")

    # Rule Contribution Treemap
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🤖 Detection Attribution Analysis")
        st.caption("Shows which rules catch the most confirmed fraud")

        fig_treemap = go.Figure(go.Treemap(
            labels=rule_performance_df['rule_name'],
            parents=[''] * len(rule_performance_df),
            values=rule_performance_df['confirmed_fraud_count'],
            textinfo='label+value+percent parent',
            marker=dict(
                colorscale='Reds',
                cmid=rule_performance_df['confirmed_fraud_count'].mean()
            ),
            hovertemplate='<b>%{label}</b><br>Fraud Caught: %{value}<br>Percentage: %{percentParent}<extra></extra>'
        ))

        fig_treemap.update_layout(height=500)
        st.plotly_chart(fig_treemap, use_container_width=True)

    with col2:
        st.subheader("🧠 Rule Performance Matrix")
        st.caption("X: Trigger Frequency | Y: Precision | Size: Rule Weight")

        fig_bubble = go.Figure()

        fig_bubble.add_trace(go.Scatter(
            x=rule_performance_df['trigger_frequency'],
            y=rule_performance_df['precision'] * 100,
            mode='markers',
            marker=dict(
                size=rule_performance_df['rule_weight'],
                sizemode='diameter',
                sizeref=2,
                color=rule_performance_df['precision'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Precision"),
                line=dict(width=1, color='white')
            ),
            text=rule_performance_df['rule_name'],
            hovertemplate='<b>%{text}</b><br>Frequency: %{x}<br>Precision: %{y:.1f}%<br><extra></extra>'
        ))

        fig_bubble.update_layout(
            xaxis_title="Trigger Frequency",
            yaxis_title="Precision (%)",
            height=500,
            hovermode='closest'
        )

        st.plotly_chart(fig_bubble, use_container_width=True)

    st.markdown("---") 

    # Rule Effectiveness Matrix (Heatmap)
    st.subheader("📊 Strategic Detection Dashboard")
    st.caption("Quick visual identification of high-performing and underperforming rules")

    # Prepare heatmap data
    heatmap_data = rule_performance_df[['rule_name', 'trigger_frequency', 'precision',
                                         'false_positive_rate', 'avg_contribution']].copy()

    # Normalize for better visualization
    heatmap_data['trigger_frequency_norm'] = (heatmap_data['trigger_frequency'] - heatmap_data['trigger_frequency'].min()) / (heatmap_data['trigger_frequency'].max() - heatmap_data['trigger_frequency'].min())
    heatmap_data['precision_norm'] = heatmap_data['precision']
    heatmap_data['fpr_norm'] = 1 - heatmap_data['false_positive_rate']  # Inverted so green is good
    heatmap_data['contribution_norm'] = (heatmap_data['avg_contribution'] - heatmap_data['avg_contribution'].min()) / (heatmap_data['avg_contribution'].max() - heatmap_data['avg_contribution'].min())

    heatmap_matrix = heatmap_data[['rule_name', 'trigger_frequency_norm', 'precision_norm',
                                     'fpr_norm', 'contribution_norm']].set_index('rule_name')

    fig_heatmap = go.Figure(data=go.Heatmap(
        z=heatmap_matrix.values,
        x=['Trigger Frequency', 'Precision', 'False Positive Rate (Inv)', 'Avg Contribution'],
        y=heatmap_matrix.index,
        colorscale='RdYlGn',
        text=np.round(heatmap_matrix.values, 2),
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title="Performance Score")
    ))

    fig_heatmap.update_layout(
        height=600,
        xaxis_title="Performance Metrics",
        yaxis_title="Rules",
        yaxis=dict(autorange='reversed')
    )

    st.plotly_chart(fig_heatmap, use_container_width=True)

    st.markdown("---")


    st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | **Note:** Using enhanced synthetic data for demonstration")

if __name__ == "__main__" or True:
    render()
