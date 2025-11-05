"""
Behavioral Analytics Page

Geographic fraud analysis and behavioral anomaly detection.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta


# Generate synthetic dataset for visualization
np.random.seed(42)

# VPN/Proxy fraud locations (USA)
usa_vpn_locations = pd.DataFrame({
    'state': ['California', 'Texas', 'Florida', 'New York', 'Illinois', 'Pennsylvania',
              'Ohio', 'Georgia', 'North Carolina', 'Michigan', 'New Jersey', 'Virginia'],
    'lat': [36.7783, 31.9686, 27.6648, 42.1657, 40.6331, 41.2033,
            40.4173, 32.1656, 35.7596, 44.3148, 40.0583, 37.4316],
    'lon': [-119.4179, -99.9018, -81.5158, -74.9481, -89.3985, -77.1945,
            -82.9071, -82.9001, -79.0193, -85.6024, -74.4057, -78.6569],
    'vpn_fraud_count': [145, 98, 87, 132, 76, 54, 48, 65, 52, 43, 89, 58],
    'intensity': [0.9, 0.6, 0.55, 0.8, 0.48, 0.35, 0.3, 0.42, 0.33, 0.27, 0.57, 0.37]
})

# Behavioral anomaly timeline data
behavioral_timeline = pd.DataFrame({
    'time': pd.date_range(start='2024-11-01', periods=48, freq='H'),
    'normal_frequency': np.random.poisson(lam=3, size=48),
    'normal_amount': np.random.normal(loc=150, scale=30, size=48),
    'flagged_frequency': [3] * 40 + [8, 9, 12, 15, 18, 11, 7, 5],
    'flagged_amount': [150] * 40 + [180, 250, 450, 2500, 3200, 1800, 500, 300]
})


def render():
    """Render the Behavioral Analytics page"""

    st.header("🗺️ Geographic & Behavioral Analysis")
    st.caption("Location-based fraud patterns and behavioral anomaly detection")

    # VPN/Proxy Fraud Locations (USA)
    st.subheader("🌐 VPN/Proxy Fraud Heatmap - USA")
    st.caption("Device locations remotely triggered across USA using VPN/Proxy")

    fig_usa_map = go.Figure(go.Scattergeo(
        lon=usa_vpn_locations['lon'],
        lat=usa_vpn_locations['lat'],
        text=usa_vpn_locations['state'],
        mode='markers',
        marker=dict(
            size=usa_vpn_locations['vpn_fraud_count'] / 3,
            color=usa_vpn_locations['intensity'],
            colorscale='Reds',
            showscale=True,
            colorbar=dict(title="Intensity"),
            line=dict(width=1, color='white'),
            sizemode='diameter'
        ),
        hovertemplate='<b>%{text}</b><br>VPN Fraud Count: %{marker.size:.0f}<br>Intensity: %{marker.color:.2f}<extra></extra>'
    ))

    fig_usa_map.update_layout(
        geo=dict(
            scope='usa',
            projection_type='albers usa',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            coastlinecolor='rgb(204, 204, 204)',
            showlakes=True,
            lakecolor='rgb(255, 255, 255)',
            showsubunits=True,
            showcountries=True,
            resolution=50,
            projection=dict(
                type='albers usa'
            )
        ),
        height=600,
        title="VPN/Proxy Fraud Activity Across USA"
    )

    st.plotly_chart(fig_usa_map, use_container_width=True)

    # Top states table
    col1, col2, col3 = st.columns(3)
    top_states = usa_vpn_locations.nlargest(3, 'vpn_fraud_count')

    with col1:
        st.metric("Highest VPN Fraud", top_states.iloc[0]['state'],
                 f"{top_states.iloc[0]['vpn_fraud_count']} cases")
    with col2:
        st.metric("Second Highest", top_states.iloc[1]['state'],
                 f"{top_states.iloc[1]['vpn_fraud_count']} cases")
    with col3:
        st.metric("Third Highest", top_states.iloc[2]['state'],
                 f"{top_states.iloc[2]['vpn_fraud_count']} cases")

    st.markdown("---")

    # Behavioral Anomaly Timeline
    st.subheader("📈 Behavioral Anomaly Timeline")
    st.caption("Normal behavior baseline vs flagged transaction patterns")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Transaction Frequency Analysis**")

        fig_behavior_freq = go.Figure()

        fig_behavior_freq.add_trace(go.Scatter(
            x=behavioral_timeline['time'],
            y=behavioral_timeline['normal_frequency'],
            name='Normal Baseline',
            line=dict(color='#10b981', width=2),
            fill='tonexty'
        ))

        fig_behavior_freq.add_trace(go.Scatter(
            x=behavioral_timeline['time'],
            y=behavioral_timeline['flagged_frequency'],
            name='Flagged Activity',
            line=dict(color='#ef4444', width=2)
        ))

        fig_behavior_freq.update_layout(
            xaxis_title="Time",
            yaxis_title="Transaction Frequency",
            height=400,
            hovermode='x unified'
        )

        st.plotly_chart(fig_behavior_freq, use_container_width=True)

    with col2:
        st.markdown("**Transaction Amount Analysis**")

        fig_behavior_amount = go.Figure()

        fig_behavior_amount.add_trace(go.Scatter(
            x=behavioral_timeline['time'],
            y=behavioral_timeline['normal_amount'],
            name='Normal Baseline',
            line=dict(color='#10b981', width=2)
        ))

        fig_behavior_amount.add_trace(go.Scatter(
            x=behavioral_timeline['time'],
            y=behavioral_timeline['flagged_amount'],
            name='Flagged Activity',
            line=dict(color='#ef4444', width=2),
            mode='lines+markers'
        ))

        fig_behavior_amount.update_layout(
            xaxis_title="Time",
            yaxis_title="Transaction Amount ($)",
            yaxis_type="log",
            height=400,
            hovermode='x unified'
        )

        st.plotly_chart(fig_behavior_amount, use_container_width=True)

    # Anomaly detection insights
    st.markdown("**🚨 Anomaly Detection Summary:**")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Frequency Spike", "8→18 txn/hr", delta="125% increase")
    with col2:
        st.metric("Amount Spike", "$150→$3,200", delta="2,033% increase")
    with col3:
        st.metric("Detection Time", "< 5 seconds", delta="Real-time")
    with col4:
        st.metric("Pattern Match", "Known fraud signature", delta="99% confidence")

    st.markdown("---")

    # Combined Multi-Metric Anomaly View
    st.subheader("🔍 Multi-Dimensional Anomaly Detection")
    st.caption("Comprehensive view of device, location, and behavioral inconsistencies")

    # Create sample anomaly data for a suspicious transaction
    anomaly_metrics = pd.DataFrame({
        'Metric': ['Device Fingerprint', 'Geo-Location', 'VPN Usage', 'Typing Speed',
                   'Transaction Time', 'Amount', 'Frequency'],
        'Normal_Range': [100, 100, 0, 68, 12, 150, 3],
        'Current_Value': [0, 15, 100, 23, 3, 15000, 15],
        'Anomaly_Score': [100, 85, 100, 66, 75, 99, 83]
    })

    fig_multi_anomaly = go.Figure()

    fig_multi_anomaly.add_trace(go.Bar(
        x=anomaly_metrics['Metric'],
        y=anomaly_metrics['Anomaly_Score'],
        marker=dict(
            color=anomaly_metrics['Anomaly_Score'],
            colorscale='YlOrRd',
            showscale=True,
            colorbar=dict(title="Anomaly<br>Score")
        ),
        text=anomaly_metrics['Anomaly_Score'],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Anomaly Score: %{y}<extra></extra>'
    ))

    fig_multi_anomaly.update_layout(
        xaxis_title="Detection Parameter",
        yaxis_title="Anomaly Score (0-100)",
        height=400,
        yaxis=dict(range=[0, 110])
    )

    st.plotly_chart(fig_multi_anomaly, use_container_width=True)

    st.markdown("---")
    st.caption(f"💡 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | **Note:** Geographic and behavioral analytics with synthetic data")

if __name__ == "__main__" or True:
    render()
    