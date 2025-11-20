"""
Behavioral Analytics Page

Geographic fraud analysis and behavioral anomaly detection.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

from streamlit_app.theme import apply_master_theme, render_page_header, get_chart_colors
from streamlit_app.ai_recommendations import get_ai_engine, render_ai_insight
from streamlit_app.explainability import get_explainability_engine
from streamlit_app.components import init_tooltip_toggle, chart_with_explanation


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

    # Apply theme
    apply_master_theme()
    init_tooltip_toggle()

    # Professional CSS for card-based layout
    st.markdown("""
    <style>
    .block-container { padding-top: 0.5rem; padding-bottom: 1rem; max-width: 1400px; }
    [data-testid="column"] > div > div > div {
        background: white; border-radius: 12px; padding: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); margin-bottom: 12px; transition: all 0.3s ease;
    }
    [data-testid="column"] > div > div > div:hover {
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12); transform: translateY(-2px);
    }
    .section-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px;
        padding-bottom: 12px; border-bottom: 2px solid #f0f0f0; }
    .section-header h2, .section-header h3 { margin: 0 !important; font-size: 1.5rem !important;
        font-weight: 600; color: #1a202c; }
    .section-badge { display: inline-block; padding: 4px 12px;
        background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 20px;
        font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    h2, h3 { margin-top: 0.8rem !important; margin-bottom: 0.4rem !important; }
    [data-testid="stMetricValue"] {
        font-size: 1.6rem; font-weight: 700; background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    </style>
    """, unsafe_allow_html=True)

    # Professional gradient header
    st.markdown("""
    <div style='background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); padding: 28px; border-radius: 12px; margin-bottom: 24px; box-shadow: 0 4px 16px rgba(139, 92, 246, 0.3);'>
        <h1 style='color: white; margin: 0; font-size: 2rem; font-weight: 700;'>
            🗺️ Geographic & Behavioral Analytics
        </h1>
        <p style='color: rgba(255,255,255,0.95); margin: 10px 0 0 0; font-size: 1.05rem;'>
            Location-based fraud intelligence, VPN/Proxy detection, and behavioral anomaly analysis
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Key Geographic Metrics Callout
    st.markdown("""
    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                padding: 20px; border-radius: 12px; margin: 20px 0; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);">
        <div style="color: white; text-align: center;">
            <h3 style="margin: 0; color: white; font-size: 1.3rem;">🌐 Geographic Threat Intelligence</h3>
            <div style="display: flex; justify-content: space-around; margin-top: 15px;">
                <div>
                    <div style="font-size: 2rem; font-weight: bold;">145</div>
                    <div style="font-size: 0.9rem; opacity: 0.95;">VPN Cases (California)</div>
                </div>
                <div>
                    <div style="font-size: 2rem; font-weight: bold;">12</div>
                    <div style="font-size: 0.9rem; opacity: 0.95;">High-Risk States</div>
                </div>
                <div>
                    <div style="font-size: 2rem; font-weight: bold;">$2.4M</div>
                    <div style="font-size: 0.9rem; opacity: 0.95;">Geographic Risk Exposure</div>
                </div>
                <div>
                    <div style="font-size: 2rem; font-weight: bold;">89%</div>
                    <div style="font-size: 0.9rem; opacity: 0.95;">VPN Detection Rate</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Get standardized chart colors
    colors = get_chart_colors()

    # VPN/Proxy Fraud Locations (USA)
    st.markdown("""
    <div class='section-header'>
        <h2>🌐 Geolocation Threat Map</h2>
        <span class='section-badge'>USA</span>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Device locations remotely triggered across USA using VPN/Proxy")

    # Enhanced map hover with explainability
    map_hover_texts = []
    for _, row in usa_vpn_locations.iterrows():
        state = row['state']
        fraud_count = row['vpn_fraud_count']
        intensity = row['intensity']

        # Risk assessment
        if fraud_count > 100:
            risk_level = "🔴 CRITICAL"
            risk_color = "#dc2626"
            recommendation = "Deploy enhanced monitoring team immediately"
        elif fraud_count > 50:
            risk_level = "🟠 HIGH"
            risk_color = "#f59e0b"
            recommendation = "Increase screening for this region"
        elif fraud_count > 20:
            risk_level = "🟡 MODERATE"
            risk_color = "#eab308"
            recommendation = "Standard monitoring with alertness"
        else:
            risk_level = "🟢 LOW"
            risk_color = "#10b981"
            recommendation = "Normal processing procedures"

        # Estimate financial impact
        avg_fraud_loss = 3200  # Average VPN/proxy fraud loss
        total_risk = fraud_count * avg_fraud_loss

        hover_text = (
            f"<b style='font-size:16px'>{state}</b><br><br>"
            f"<b style='color:{risk_color}'>{risk_level} RISK</b><br><br>"
            f"<b>📊 Threat Metrics:</b><br>"
            f"• VPN/Proxy Fraud Cases: <b>{fraud_count}</b><br>"
            f"• Intensity Score: <b>{intensity:.2f}</b><br>"
            f"• National Rank: <b>#{usa_vpn_locations[usa_vpn_locations['vpn_fraud_count'] >= fraud_count].shape[0]}</b><br><br>"
            f"<b>💰 Financial Impact:</b><br>"
            f"• Est. Total Exposure: <b>${total_risk:,}</b><br>"
            f"• Avg per Case: <b>${avg_fraud_loss:,}</b><br><br>"
            f"<b>🎯 Recommendation:</b><br>"
            f"{recommendation}"
        )
        map_hover_texts.append(hover_text)

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
        hovertemplate='%{customdata}<extra></extra>',
        customdata=map_hover_texts
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
        height=400,
        margin=dict(l=0, r=0, t=30, b=0)
    )

    st.plotly_chart(fig_usa_map, use_container_width=True, key="geo_usa_map")

    # Top states table
    col1, col2, col3 = st.columns(3, gap="medium")
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

    # Behavioral Anomaly Timeline
    st.markdown("""
    <div class='section-header' style='margin-top: 24px;'>
        <h2>🧠 Anomaly Detection Timeline</h2>
        <span class='section-badge'>REAL-TIME</span>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Normal behavior baseline vs flagged transaction patterns")

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        st.markdown("**Transaction Frequency Analysis**")

        fig_behavior_freq = go.Figure()

        # Enhanced hover for normal frequency
        normal_freq_hover = [
            f"<b>Time:</b> {time.strftime('%Y-%m-%d %H:%M')}<br>"
            f"<b>Normal Frequency:</b> {freq} txn/hour<br><br>"
            f"<b>💡 Meaning:</b> Expected transaction rate<br>"
            f"<b>📊 Status:</b> Baseline behavior pattern<br>"
            f"<b>✅ Assessment:</b> Legitimate customer activity"
            for time, freq in zip(behavioral_timeline['time'], behavioral_timeline['normal_frequency'])
        ]

        fig_behavior_freq.add_trace(go.Scatter(
            x=behavioral_timeline['time'],
            y=behavioral_timeline['normal_frequency'],
            name='Normal Baseline',
            line=dict(color='#10b981', width=2),
            fill='tonexty',
            hovertemplate='%{customdata}<extra></extra>',
            customdata=normal_freq_hover
        ))

        # Enhanced hover for flagged frequency
        flagged_freq_hover = []
        for time, normal_freq, flagged_freq in zip(
            behavioral_timeline['time'],
            behavioral_timeline['normal_frequency'],
            behavioral_timeline['flagged_frequency']
        ):
            deviation = ((flagged_freq - normal_freq) / normal_freq * 100) if normal_freq > 0 else 0

            if deviation > 200:
                severity = "🔴 CRITICAL"
                alert = "Extreme anomaly - potential account takeover"
            elif deviation > 100:
                severity = "🟠 HIGH"
                alert = "Significant spike - investigate immediately"
            elif deviation > 50:
                severity = "🟡 MODERATE"
                alert = "Unusual activity - monitor closely"
            else:
                severity = "🟢 LOW"
                alert = "Minor deviation - within tolerance"

            hover_text = (
                f"<b>Time:</b> {time.strftime('%Y-%m-%d %H:%M')}<br>"
                f"<b>Flagged Frequency:</b> {flagged_freq} txn/hour<br>"
                f"<b>Normal Baseline:</b> {normal_freq} txn/hour<br><br>"
                f"<b>📊 Deviation:</b> <b>{deviation:+.1f}%</b><br>"
                f"<b>⚠️ Severity:</b> {severity}<br><br>"
                f"<b>🎯 Alert:</b> {alert}"
            )
            flagged_freq_hover.append(hover_text)

        fig_behavior_freq.add_trace(go.Scatter(
            x=behavioral_timeline['time'],
            y=behavioral_timeline['flagged_frequency'],
            name='Flagged Activity',
            line=dict(color='#ef4444', width=2),
            hovertemplate='%{customdata}<extra></extra>',
            customdata=flagged_freq_hover
        ))

        fig_behavior_freq.update_layout(
            xaxis_title="Time",
            yaxis_title="Transaction Frequency",
            height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(title_font_size=11),
            yaxis=dict(title_font_size=11),
            hovermode='x unified'
        )

        st.plotly_chart(fig_behavior_freq, use_container_width=True, key="geo_behavior_freq")

    with col2:
        st.markdown("**Transaction Amount Analysis**")

        fig_behavior_amount = go.Figure()

        # Enhanced hover for normal amounts
        normal_amt_hover = [
            f"<b>Time:</b> {time.strftime('%Y-%m-%d %H:%M')}<br>"
            f"<b>Normal Amount:</b> ${amt:,.2f}<br><br>"
            f"<b>💡 Meaning:</b> Typical transaction size<br>"
            f"<b>📊 Profile:</b> Customer's baseline spending<br>"
            f"<b>✅ Assessment:</b> Expected behavior"
            for time, amt in zip(behavioral_timeline['time'], behavioral_timeline['normal_amount'])
        ]

        fig_behavior_amount.add_trace(go.Scatter(
            x=behavioral_timeline['time'],
            y=behavioral_timeline['normal_amount'],
            name='Normal Baseline',
            line=dict(color='#10b981', width=2),
            hovertemplate='%{customdata}<extra></extra>',
            customdata=normal_amt_hover
        ))

        # Enhanced hover for flagged amounts
        flagged_amt_hover = []
        for time, normal_amt, flagged_amt in zip(
            behavioral_timeline['time'],
            behavioral_timeline['normal_amount'],
            behavioral_timeline['flagged_amount']
        ):
            amt_increase = ((flagged_amt - normal_amt) / normal_amt * 100) if normal_amt > 0 else 0

            if amt_increase > 500:
                risk = "🔴 CRITICAL"
                assessment = "Extreme amount spike - likely fraud"
            elif amt_increase > 200:
                risk = "🟠 HIGH"
                assessment = "Unusual high-value transaction"
            elif amt_increase > 100:
                risk = "🟡 MODERATE"
                assessment = "Above normal spending - verify"
            else:
                risk = "🟢 LOW"
                assessment = "Slightly elevated - acceptable variance"

            hover_text = (
                f"<b>Time:</b> {time.strftime('%Y-%m-%d %H:%M')}<br>"
                f"<b>Flagged Amount:</b> ${flagged_amt:,.2f}<br>"
                f"<b>Normal Amount:</b> ${normal_amt:,.2f}<br><br>"
                f"<b>📊 Increase:</b> <b>{amt_increase:+.1f}%</b><br>"
                f"<b>⚠️ Risk Level:</b> {risk}<br><br>"
                f"<b>💡 Assessment:</b> {assessment}<br>"
                f"<b>💰 Potential Loss:</b> ${flagged_amt:,.2f} at risk"
            )
            flagged_amt_hover.append(hover_text)

        fig_behavior_amount.add_trace(go.Scatter(
            x=behavioral_timeline['time'],
            y=behavioral_timeline['flagged_amount'],
            name='Flagged Activity',
            line=dict(color='#ef4444', width=2),
            mode='lines+markers',
            hovertemplate='%{customdata}<extra></extra>',
            customdata=flagged_amt_hover
        ))

        fig_behavior_amount.update_layout(
            xaxis_title="Time",
            yaxis_title="Transaction Amount ($)",
            yaxis_type="log",
            height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(title_font_size=11),
            yaxis=dict(title_font_size=11),
            hovermode='x unified'
        )

        st.plotly_chart(fig_behavior_amount, use_container_width=True, key="geo_behavior_amount")

    # Anomaly detection insights
    st.markdown("**🚨 Anomaly Detection Summary:**")

    col1, col2, col3, col4 = st.columns(4, gap="medium")
    with col1:
        st.metric("Frequency Spike", "8→18 txn/hr", delta="125% increase")
    with col2:
        st.metric("Amount Spike", "$150→$3,200", delta="2,033% increase")
    with col3:
        st.metric("Detection Time", "< 5 seconds", delta="Real-time")
    with col4:
        st.metric("Pattern Match", "Known fraud signature", delta="99% confidence")

    # Combined Multi-Metric Anomaly View
    st.markdown("""
    <div class='section-header' style='margin-top: 24px;'>
        <h2>🤖 Cross-Vector Threat Analysis</h2>
        <span class='section-badge'>AI-POWERED</span>
    </div>
    """, unsafe_allow_html=True)
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
        height=300,
        margin=dict(l=10, r=10, t=10, b=40),
        xaxis=dict(title_font_size=11, tickfont=dict(size=10)),
        yaxis=dict(range=[0, 110], title_font_size=11)
    )

    st.plotly_chart(fig_multi_anomaly, use_container_width=True, key="geo_multi_anomaly")

    # AI Geographic Pattern Analysis
    st.markdown("""
    <div class='section-header' style='margin-top: 24px;'>
        <h2>🤖 AI Geographic Risk Analysis</h2>
        <span class='section-badge'>INSIGHTS</span>
    </div>
    """, unsafe_allow_html=True)

    geo_col1, geo_col2 = st.columns(2, gap="medium")

    with geo_col1:
        st.markdown("### 🗺️ Regional Fraud Trends")

        # Get AI insights on geographic patterns
        ai_engine = get_ai_engine()

        top_states = usa_vpn_locations.nlargest(3, 'vpn_fraud_count')

        for idx, row in top_states.iterrows():
            geo_insight = ai_engine.get_pattern_insight(
                pattern_type="geographic",
                pattern_data={
                    "location": row['state'],
                    "vpn_count": int(row['vpn_fraud_count']),
                    "intensity": float(row['intensity']),
                    "trend": "increasing"
                }
            )

            render_ai_insight(
                title=f"{row['state']} - {row['vpn_fraud_count']} VPN Cases",
                recommendation=geo_insight,
                icon="🌍"
            )

    with geo_col2:
        st.markdown("### 🕵️ Behavioral Anomaly Insights")

        # Anomaly pattern insight
        anomaly_insight = ai_engine.get_pattern_insight(
            pattern_type="behavioral",
            pattern_data={
                "device_change": "100% different",
                "location_shift": "6,147 miles",
                "vpn_detected": True,
                "typing_speed_variance": "66%",
                "time_anomaly": "2 AM activity"
            }
        )

        render_ai_insight(
            title="Account Takeover Pattern Detected",
            recommendation=anomaly_insight,
            icon="🚨"
        )

        # Temporal pattern insight
        temporal_insight = ai_engine.get_pattern_insight(
            pattern_type="temporal",
            pattern_data={
                "peak_hours": "2-4 AM",
                "normal_hours": "9 AM - 6 PM",
                "fraud_spike": "250% above baseline",
                "day_pattern": "Weekdays higher risk"
            }
        )

        render_ai_insight(
            title="Temporal Fraud Patterns",
            recommendation=temporal_insight,
            icon="⏰"
        )

    # AI Intelligence Summary
    st.markdown("""
    <div class='section-header' style='margin-top: 24px;'>
        <h2>💡 Geographic Intelligence Summary</h2>
        <span class='section-badge'>AI INSIGHTS</span>
    </div>
    """, unsafe_allow_html=True)

    insight_cards_col1, insight_cards_col2, insight_cards_col3 = st.columns(3)

    with insight_cards_col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 15px; border-radius: 10px; color: white; height: 150px;">
            <h5 style="margin-top: 0; color: white;">🗺️ Regional Hotspots</h5>
            <p style="font-size: 14px;">California, New York, and Texas account for 60% of
            VPN/proxy fraud. Enhanced screening deployed in high-risk regions.</p>
        </div>
        """, unsafe_allow_html=True)

    with insight_cards_col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    padding: 15px; border-radius: 10px; color: white; height: 150px;">
            <h5 style="margin-top: 0; color: white;">🔍 VPN Detection</h5>
            <p style="font-size: 14px;">89% VPN detection rate with real-time IP analysis
            and device fingerprinting blocking proxy-based fraud attempts.</p>
        </div>
        """, unsafe_allow_html=True)

    with insight_cards_col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                    padding: 15px; border-radius: 10px; color: white; height: 150px;">
            <h5 style="margin-top: 0; color: white;">⚡ Behavioral Patterns</h5>
            <p style="font-size: 14px;">Account takeover attempts peak at 2-4 AM with 250%
            frequency spike and extreme transaction amount anomalies.</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    render()
    