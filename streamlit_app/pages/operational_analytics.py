"""
Operational Analytics Page

Operational efficiency metrics including time analysis and merchant risk profiles.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from streamlit_app.theme import apply_master_theme, render_page_header, get_chart_colors
from streamlit_app.ai_recommendations import get_ai_engine, render_ai_insight


# Generate synthetic dataset for visualization
np.random.seed(42)

# Transaction time data (hourly heatmap)
hours = list(range(24))
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
transaction_heatmap_data = np.random.poisson(lam=15, size=(7, 24))
transaction_heatmap_data[0:5, 0:6] = np.random.poisson(lam=5, size=(5, 6))  # Lower at night
transaction_heatmap_data[0:5, 9:17] = np.random.poisson(lam=25, size=(5, 8))  # Higher during business hours

# Time-to-resolution data
resolution_data = pd.DataFrame({
    'risk_level': ['Low'] * 100 + ['Medium'] * 150 + ['High'] * 100 + ['Critical'] * 50,
    'resolution_time_minutes': list(np.random.gamma(2, 5, 100)) +
                               list(np.random.gamma(3, 8, 150)) +
                               list(np.random.gamma(4, 12, 100)) +
                               list(np.random.gamma(5, 15, 50))
})

# Merchant category risk data
merchant_categories = ['Retail', 'E-commerce', 'Gaming', 'Financial Services',
                       'Travel', 'Cryptocurrency', 'Food & Beverage', 'Healthcare']
merchant_risk_df = pd.DataFrame({
    'category': merchant_categories,
    'risk_score': [45, 62, 78, 55, 58, 85, 38, 42],
    'transaction_volume': [2500, 3200, 1800, 1500, 1200, 900, 3500, 2000],
    'fraud_rate': [2.1, 4.5, 6.8, 3.2, 3.8, 8.5, 1.5, 1.8]
})


def render():
    """Render the Operational Analytics page"""

    # Apply theme
    apply_master_theme()

    # Header
    render_page_header(
        title="Operational Efficiency Metrics",
        subtitle="Time-based patterns and operational performance analysis",
        show_logo=False
    )

    # Get standardized chart colors
    colors = get_chart_colors()

    # Real-Time Transaction Heatmap
    st.subheader("🤖 Transaction Flow Heatmap")
    st.caption("Shows when suspicious transactions cluster throughout the week")

    fig_heatmap_time = go.Figure(data=go.Heatmap(
        z=transaction_heatmap_data,
        x=hours,
        y=days,
        colorscale='YlOrRd',
        hovertemplate='Day: %{y}<br>Hour: %{x}:00<br>Flagged Transactions: %{z}<extra></extra>',
        colorbar=dict(title="Flagged<br>Count")
    ))

    fig_heatmap_time.update_layout(
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        height=400,
        xaxis=dict(tickmode='linear', dtick=2)
    )

    st.plotly_chart(fig_heatmap_time, use_container_width=True)

    # Insights
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Peak Fraud Time", "2-4 AM", delta="High Risk")
    with col2:
        st.metric("Peak Day", "Friday", delta="25% more flags")
    with col3:
        st.metric("Lowest Risk", "Weekends 9AM-5PM", delta="Safe Period")

    st.markdown("---")

    # Time-to-Resolution Metrics
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("⚡ Investigation Velocity Metrics")
        st.caption("How quickly flagged transactions are reviewed by risk level")

        fig_resolution = go.Figure()

        for risk_level in ['Low', 'Medium', 'High', 'Critical']:
            data = resolution_data[resolution_data['risk_level'] == risk_level]['resolution_time_minutes']

            fig_resolution.add_trace(go.Box(
                y=data,
                name=risk_level,
                marker_color={'Low': '#10b981', 'Medium': '#eab308',
                             'High': '#f97316', 'Critical': '#ef4444'}[risk_level]
            ))

        fig_resolution.update_layout(
            yaxis_title="Resolution Time (minutes)",
            height=400,
            showlegend=True
        )

        st.plotly_chart(fig_resolution, use_container_width=True)

        # Resolution time metrics
        st.markdown("**Average Resolution Times:**")
        for risk_level in ['Low', 'Medium', 'High', 'Critical']:
            avg_time = resolution_data[resolution_data['risk_level'] == risk_level]['resolution_time_minutes'].mean()
            st.markdown(f"- **{risk_level}:** {avg_time:.1f} minutes")

    with col2:
        st.subheader("📊 Case Resolution Analytics")

        fig_dist = go.Figure()

        fig_dist.add_trace(go.Histogram(
            x=resolution_data['resolution_time_minutes'],
            nbinsx=30,
            marker_color='#3b82f6',
            hovertemplate='Time: %{x:.1f} min<br>Count: %{y}<extra></extra>'
        ))

        fig_dist.update_layout(
            xaxis_title="Resolution Time (minutes)",
            yaxis_title="Number of Cases",
            height=400
        )

        st.plotly_chart(fig_dist, use_container_width=True)

        # Calculate percentiles
        st.markdown("**Resolution Time Percentiles:**")
        percentiles = [50, 75, 90, 95, 99]
        for p in percentiles:
            val = np.percentile(resolution_data['resolution_time_minutes'], p)
            st.markdown(f"- **{p}th percentile:** {val:.1f} minutes")

    st.markdown("---")

    # Merchant Category Risk Profile
    st.subheader("🎯 Merchant Risk Segmentation")
    st.caption("Risk scores and fraud rates across different merchant categories")

    col1, col2 = st.columns([1, 1])

    with col1:
        # Radar chart
        fig_radar = go.Figure()

        fig_radar.add_trace(go.Scatterpolar(
            r=merchant_risk_df['risk_score'],
            theta=merchant_risk_df['category'],
            fill='toself',
            name='Risk Score',
            line_color='#ef4444'
        ))

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100])
            ),
            showlegend=True,
            height=500
        )

        st.plotly_chart(fig_radar, use_container_width=True)

    with col2:
        # Bar chart showing fraud rate
        fig_merchant_bar = go.Figure()

        # Sort by risk score
        merchant_sorted = merchant_risk_df.sort_values('risk_score', ascending=True)

        fig_merchant_bar.add_trace(go.Bar(
            y=merchant_sorted['category'],
            x=merchant_sorted['fraud_rate'],
            orientation='h',
            marker=dict(
                color=merchant_sorted['risk_score'],
                colorscale='YlOrRd',
                showscale=True,
                colorbar=dict(title="Risk Score")
            ),
            text=merchant_sorted['fraud_rate'].apply(lambda x: f"{x}%"),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Fraud Rate: %{x}%<br><extra></extra>'
        ))

        fig_merchant_bar.update_layout(
            xaxis_title="Fraud Rate (%)",
            height=500,
            showlegend=False
        )

        st.plotly_chart(fig_merchant_bar, use_container_width=True)

    # Merchant details table
    st.markdown("**Detailed Merchant Analysis:**")
    merchant_display = merchant_risk_df.copy()
    merchant_display['fraud_rate'] = merchant_display['fraud_rate'].apply(lambda x: f"{x}%")
    merchant_display = merchant_display.rename(columns={
        'category': 'Category',
        'risk_score': 'Risk Score',
        'transaction_volume': 'Transaction Volume',
        'fraud_rate': 'Fraud Rate'
    })
    st.dataframe(merchant_display, use_container_width=True, hide_index=True)

    st.markdown("---")

    # AI Operational Insights
    st.markdown("## 🤖 AI Operational Intelligence")

    ops_col1, ops_col2 = st.columns(2)

    with ops_col1:
        st.markdown("### ⚡ Resolution Efficiency Analysis")

        # Get AI insight on resolution time
        ai_engine = get_ai_engine()

        avg_resolution_times = {
            'Low': resolution_data[resolution_data['risk_level'] == 'Low']['resolution_time_minutes'].mean(),
            'Medium': resolution_data[resolution_data['risk_level'] == 'Medium']['resolution_time_minutes'].mean(),
            'High': resolution_data[resolution_data['risk_level'] == 'High']['resolution_time_minutes'].mean(),
            'Critical': resolution_data[resolution_data['risk_level'] == 'Critical']['resolution_time_minutes'].mean()
        }

        efficiency_insight = ai_engine.get_pattern_insight(
            pattern_type="operational_efficiency",
            pattern_data={
                "avg_times": avg_resolution_times,
                "workload": "632 pending reviews",
                "analysts": 8,
                "peak_hour": "2-4 AM"
            }
        )

        render_ai_insight(
            title="Case Resolution Performance",
            recommendation=efficiency_insight,
            icon="📊"
        )

    with ops_col2:
        st.markdown("### 🎯 Merchant Risk Insights")

        # Get top risk merchant categories
        high_risk_merchants = merchant_risk_df.nlargest(2, 'fraud_rate')

        for idx, row in high_risk_merchants.iterrows():
            merchant_insight = ai_engine.get_pattern_insight(
                pattern_type="merchant_risk",
                pattern_data={
                    "category": row['category'],
                    "risk_score": int(row['risk_score']),
                    "fraud_rate": row['fraud_rate'],
                    "volume": int(row['transaction_volume'])
                }
            )

            render_ai_insight(
                title=f"{row['category']} ({row['fraud_rate']}% fraud rate)",
                recommendation=merchant_insight,
                icon="🏪"
            )

    st.markdown("---")
    st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | **Note:** Operational metrics with synthetic data")

if __name__ == "__main__" or True:
    render()
