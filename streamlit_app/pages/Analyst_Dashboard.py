
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
from streamlit_app.theme import apply_master_theme, get_chart_colors
from streamlit_app.ai_recommendations import get_ai_engine, render_ai_insight

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

    # Professional CSS for aesthetic design
    st.markdown("""
    <style>
    /* Global Aesthetics */
    .block-container {
        padding-top: 0.5rem;
        padding-bottom: 1rem;
        max-width: 1400px;
    }

    /* Professional Card Styling for Containers */
    [data-testid="column"] > div > div > div {
        background: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        margin-bottom: 12px;
        transition: all 0.3s ease;
    }

    /* Hover effect for card containers */
    [data-testid="column"] > div > div > div:hover {
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
        transform: translateY(-2px);
    }

    /* Professional Card Styling */
    .dashboard-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        margin-bottom: 20px;
        border-left: 4px solid transparent;
        transition: all 0.3s ease;
    }

    .dashboard-card:hover {
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
        transform: translateY(-2px);
    }

    .dashboard-card.critical {
        border-left-color: #E54848;
        background: linear-gradient(to right, #fff5f5 0%, white 10%);
    }

    .dashboard-card.success {
        border-left-color: #2E865F;
        background: linear-gradient(to right, #f0fdf4 0%, white 10%);
    }

    .dashboard-card.primary {
        border-left-color: #667eea;
        background: linear-gradient(to right, #f5f7ff 0%, white 10%);
    }

    .dashboard-card.warning {
        border-left-color: #F3B65B;
        background: linear-gradient(to right, #fffbf0 0%, white 10%);
    }

    /* Section Headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 2px solid #f0f0f0;
    }

    .section-header h2 {
        margin: 0 !important;
        font-size: 1.5rem !important;
        font-weight: 600;
        color: #1a202c;
    }

    .section-badge {
        display: inline-block;
        padding: 4px 12px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Subsection Headers */
    .subsection-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
    }

    .subsection-header h3 {
        margin: 0 !important;
        font-size: 1.1rem !important;
        font-weight: 600;
        color: #2d3748;
    }

    /* Compact Spacing */
    .stMarkdown {
        margin-bottom: 0.3rem;
    }

    h2 {
        margin-top: 0.8rem !important;
        margin-bottom: 0.4rem !important;
    }

    h3 {
        margin-top: 0.4rem !important;
        margin-bottom: 0.4rem !important;
    }

    /* Dataframe Styling */
    .stDataFrame {
        margin-bottom: 0.5rem;
        border-radius: 8px;
        overflow: hidden;
    }

    /* Chart Containers */
    .js-plotly-plot {
        margin-bottom: 0 !important;
        border-radius: 8px;
    }

    /* Metrics Enhancement */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    [data-testid="stMetricDelta"] {
        font-size: 0.9rem;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.85rem;
        font-weight: 600;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Column Gap Reduction */
    [data-testid="column"] {
        padding: 0 0.4rem;
    }

    /* Professional Button Styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
        border: 2px solid transparent;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        border-color: #667eea;
    }

    /* Caption Styling */
    .stCaptionContainer {
        margin-top: 8px;
    }

    /* Info Box Styling */
    .stAlert {
        border-radius: 8px;
        border-left-width: 4px;
    }

    /* Divider Styling */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(to right, transparent, #e2e8f0, transparent);
    }

    /* Status Indicator */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .status-indicator.live {
        background: #d1fae5;
        color: #065f46;
    }

    .status-indicator.alert {
        background: #fee2e2;
        color: #991b1b;
    }

    /* Quick Access Cards */
    .quick-access-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        transition: all 0.3s ease;
        border: 2px solid #f0f0f0;
        text-align: center;
    }

    .quick-access-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.2);
        transform: translateY(-4px);
    }

    /* Gradient Text */
    .gradient-text {
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)

    # Professional Header with Gradient
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px; margin-bottom: 24px; box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);'>
        <h1 style='color: white; margin: 0; font-size: 2rem; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            🛡️ Arriba Advisors Transaction Screening System
        </h1>
        <p style='color: rgba(255,255,255,0.95); margin: 8px 0 0 0; font-size: 1.1rem; font-weight: 500;'>
            Real-Time Fraud Detection & Prevention Analytics
        </p>
        <div style='display: inline-flex; align-items: center; gap: 6px; margin-top: 12px; padding: 6px 14px; background: rgba(255,255,255,0.2); border-radius: 20px; backdrop-filter: blur(10px);'>
            <div style='width: 8px; height: 8px; background: #10b981; border-radius: 50%; animation: pulse 2s infinite;'></div>
            <span style='color: white; font-size: 0.85rem; font-weight: 600;'>SYSTEM ACTIVE</span>
        </div>
    </div>

    <style>
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    </style>
    """, unsafe_allow_html=True)

    # Get standardized chart colors
    colors = get_chart_colors()

    # ==================== SECTION 1: Threat Detection ====================
    st.markdown("""
    <div class='section-header'>
        <h2>⚡ Threat Detection Command Center</h2>
        <span class='section-badge'>LIVE</span>
    </div>
    """, unsafe_allow_html=True)

    # Wrap table in card
    # Create alert card with proper container
    with st.container():
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
            height=220,
            column_config={
                'Risk Score': st.column_config.ProgressColumn(
                    'Risk Score',
                    min_value=0,
                    max_value=1,
                    format='%.2f'
                )
            }
        )

    # ==================== SECTION 2: Key Performance Metrics ====================
    st.markdown("""
    <div class='section-header' style='margin-top: 28px;'>
        <h2>📊 Key Performance Metrics</h2>
        <span class='section-badge'>REAL-TIME</span>
    </div>
    """, unsafe_allow_html=True)

    # Top-level KPI cards
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4, gap="medium")

    with kpi_col1:
        st.metric("Transactions Today", "12,547", "+3.2%")

    with kpi_col2:
        st.metric("Auto-Cleared", "95.0%", "+0.8%")

    with kpi_col3:
        st.metric("In Review Queue", "632", "-12")

    with kpi_col4:
        st.metric("Fraud Detected", "47", "+5")

    # System Status Overview Banner
    st.markdown("""
    <div style='background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
                padding: 16px;
                border-radius: 10px;
                margin: 16px 0;
                border-left: 5px solid #4caf50;
                box-shadow: 0 2px 8px rgba(76, 175, 80, 0.2);'>
        <div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; text-align: center;'>
            <div>
                <div style='color: #2e7d32; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;'>System Health</div>
                <div style='color: #1b5e20; font-size: 1.3rem; font-weight: 700; margin-top: 4px;'>✅ 99.8%</div>
            </div>
            <div>
                <div style='color: #2e7d32; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;'>Processing Time</div>
                <div style='color: #1b5e20; font-size: 1.3rem; font-weight: 700; margin-top: 4px;'>⚡ 45ms</div>
            </div>
            <div>
                <div style='color: #2e7d32; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;'>Active Rules</div>
                <div style='color: #1b5e20; font-size: 1.3rem; font-weight: 700; margin-top: 4px;'>🎯 20/20</div>
            </div>
            <div>
                <div style='color: #2e7d32; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;'>Detection Rate</div>
                <div style='color: #1b5e20; font-size: 1.3rem; font-weight: 700; margin-top: 4px;'>🛡️ 94.2%</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ==================== SECTION 3: Transaction Analytics ====================
    st.markdown("""
    <div class='section-header' style='margin-top: 28px;'>
        <h2>📈 Transaction Analytics</h2>
        <span class='section-badge'>24H VIEW</span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="medium")

    with col1:
        st.markdown("<div class='subsection-header'><h3>🤖 Transaction Lifecycle Monitor</h3></div>", unsafe_allow_html=True)

        funnel_data = pd.DataFrame({
            'Stage': ['Total Transactions', 'Auto-Cleared', 'Manual Review', 'Rejected', 'Fraud Confirmed'],
            'Count': [12547, 11915, 632, 85, 47],
            'Percentage': [100, 95, 5, 0.68, 0.37]
        })

        fig_funnel = go.Figure(go.Funnel(
            y=funnel_data['Stage'],
            x=funnel_data['Count'],
            textinfo="value+percent initial",
            marker=dict(color=colors['funnel'])
        ))

        fig_funnel.update_layout(
            height=280,
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_funnel, use_container_width=True, key="analyst_funnel_chart")

        st.markdown("""
        <div style='background: linear-gradient(135deg, #10b981, #059669); padding: 12px; border-radius: 8px; margin-top: 12px;'>
            <p style='margin: 0; color: white; font-size: 0.9rem; font-weight: 600; text-align: center;'>
                💰 <span style='color: white;'>Cost Savings:</span> $59,575/day
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='subsection-header'><h3>🧠 Decision Pattern Analytics</h3></div>", unsafe_allow_html=True)

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
            line=dict(color=colors['primary'], width=2)
        ))

        fig_decisions.update_layout(
            barmode='stack',
            height=280,
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(title='Count', title_font_size=11),
            yaxis2=dict(title='Confidence %', overlaying='y', side='right', range=[0, 100], title_font_size=11),
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=10)),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig_decisions, use_container_width=True, key="analyst_decisions_chart")

    # ==================== SECTION 4: Live Transaction Pulse ====================
    st.markdown("""
    <div class='section-header' style='margin-top: 28px;'>
        <h2>⚡ Live Transaction Pulse</h2>
        <span class='section-badge'>LIVE 24H</span>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='subsection-header'><h3>📊 Real-Time Transaction Flow</h3></div>", unsafe_allow_html=True)

        hours = pd.date_range(end=datetime.now(), periods=24, freq='H')
        transactions = np.random.poisson(lam=500, size=24) + np.random.randint(-50, 100, 24)
        fraud_detected = np.random.poisson(lam=2, size=24)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=hours,
            y=transactions,
            name='Total Transactions',
            line=dict(color=colors['primary'], width=2),
            fill='tozeroy',
            fillcolor='rgba(102, 126, 234, 0.1)'
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
            yaxis=dict(title='Transaction Volume', title_font_size=11),
            yaxis2=dict(title='Fraud Cases', overlaying='y', side='right', title_font_size=11),
            hovermode='x unified',
            height=280,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=10)),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig, use_container_width=True, key="analyst_pulse_chart")

    # ==================== SECTION 5: ML Intelligence ====================
    st.markdown("""
    <div class='section-header' style='margin-top: 28px;'>
        <h2>🤖 Machine Learning Intelligence</h2>
        <span class='section-badge'>AI-POWERED</span>
    </div>
    """, unsafe_allow_html=True)

    # ML Metrics in Cards
    ml_col1, ml_col2, ml_col3, ml_col4 = st.columns(4, gap="medium")

    with ml_col1:
        st.metric("Model Accuracy", "94.3%", "+1.2%")

    with ml_col2:
        st.metric("AUC-ROC Score", "0.963", "+0.008")

    with ml_col3:
        st.metric("Predictions/Min", "1,247", "+156")

    with ml_col4:
        st.metric("Avg Confidence", "87.2%", "+2.3%")

    # ML Visualizations
    ml_viz_col1, ml_viz_col2 = st.columns(2, gap="medium")

    with ml_viz_col1:
        st.markdown("<div class='subsection-header'><h3>🎯 Model Performance Trends</h3></div>", unsafe_allow_html=True)

        ml_days = pd.date_range(end=datetime.now(), periods=7, freq='D')
        ml_accuracy = [0.932 + i * 0.0015 + np.random.uniform(-0.005, 0.005) for i in range(7)]
        ml_precision = [0.918 + i * 0.002 + np.random.uniform(-0.005, 0.005) for i in range(7)]
        ml_recall = [0.895 + i * 0.0025 + np.random.uniform(-0.005, 0.005) for i in range(7)]

        fig_ml_perf = go.Figure()

        fig_ml_perf.add_trace(go.Scatter(
            x=ml_days,
            y=ml_accuracy,
            name='Accuracy',
            line=dict(color=colors['primary'], width=2),
            mode='lines+markers'
        ))

        fig_ml_perf.add_trace(go.Scatter(
            x=ml_days,
            y=ml_precision,
            name='Precision',
            line=dict(color=colors['success'], width=2),
            mode='lines+markers'
        ))

        fig_ml_perf.add_trace(go.Scatter(
            x=ml_days,
            y=ml_recall,
            name='Recall',
            line=dict(color=colors['info'], width=2),
            mode='lines+markers'
        ))

        fig_ml_perf.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(title='Score', range=[0.85, 0.98], title_font_size=11),
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=10)),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig_ml_perf, use_container_width=True, key="ml_performance_trends")

    with ml_viz_col2:
        st.markdown("<div class='subsection-header'><h3>📊 Prediction Confidence</h3></div>", unsafe_allow_html=True)

        np.random.seed(42)
        confidence_scores = np.concatenate([
            np.random.beta(8, 2, 400),
            np.random.beta(2, 2, 100)
        ]) * 100

        fig_conf = go.Figure()

        fig_conf.add_trace(go.Histogram(
            x=confidence_scores,
            nbinsx=20,
            marker=dict(
                color=confidence_scores,
                colorscale='RdYlGn',
                showscale=False
            ),
            opacity=0.75
        ))

        fig_conf.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(title='Confidence Score (%)', title_font_size=11),
            yaxis=dict(title='Predictions', title_font_size=11),
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig_conf, use_container_width=True, key="ml_confidence_dist")

    ml_viz_col3, ml_viz_col4 = st.columns(2, gap="medium")

    with ml_viz_col3:
        st.markdown("<div class='subsection-header'><h3>🔍 Top Feature Importance</h3></div>", unsafe_allow_html=True)

        feature_names = [
            'Transaction Amount',
            'Customer Risk Level',
            'Transaction Hour',
            'International Flag',
            'Account Balance',
            'Account Age',
            'Is PEP',
            'Weekend Flag'
        ]
        feature_importance = [0.28, 0.22, 0.14, 0.12, 0.10, 0.06, 0.05, 0.03]

        fig_features = go.Figure(go.Bar(
            y=feature_names,
            x=feature_importance,
            orientation='h',
            marker=dict(
                color=feature_importance,
                colorscale='Blues',
                showscale=False
            ),
            text=[f"{v:.1%}" for v in feature_importance],
            textposition='outside'
        ))

        fig_features.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(title='Importance', title_font_size=11),
            yaxis=dict(title='', tickfont=dict(size=10)),
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig_features, use_container_width=True, key="ml_feature_importance")

    with ml_viz_col4:
        st.markdown("<div class='subsection-header'><h3>⚡ Model Health</h3></div>", unsafe_allow_html=True)

        health_metrics = pd.DataFrame({
            'Metric': ['Data Quality', 'Model Drift', 'Latency', 'Throughput', 'Error Rate'],
            'Status': ['Excellent', 'Normal', 'Good', 'Excellent', 'Good'],
            'Score': [98, 92, 88, 97, 91]
        })

        fig_health = go.Figure()

        colors_health = ['#2E865F' if s >= 95 else '#F3B65B' if s >= 85 else '#E54848'
                        for s in health_metrics['Score']]

        fig_health.add_trace(go.Bar(
            y=health_metrics['Metric'],
            x=health_metrics['Score'],
            orientation='h',
            marker=dict(color=colors_health),
            text=[f"{s}%" for s in health_metrics['Score']],
            textposition='outside'
        ))

        fig_health.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(title='Health (%)', range=[0, 110], title_font_size=11),
            yaxis=dict(title='', tickfont=dict(size=10)),
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig_health, use_container_width=True, key="ml_health_metrics")

    # ML Insight - AI-Powered Analysis
    st.markdown("""
    <div class='section-header' style='margin-top: 28px;'>
        <h2>💡 AI Performance Analysis</h2>
        <span class='section-badge'>INTELLIGENT</span>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        ai_engine = get_ai_engine()
        ml_insight = ai_engine.get_ml_performance_insight(
            accuracy=0.943,
            precision=0.932,
            recall=0.906,
            auc_roc=0.963,
            trend='improving'
        )

        # Display AI insight with better formatting
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 16px;
                    border-radius: 10px;
                    border-left: 5px solid #ffd700;">
            <div style="color: white; font-weight: bold; margin-bottom: 10px; font-size: 1.05rem;">
                🤖 ML Performance Analysis
            </div>
            <div style="color: #f0f0f0; font-size: 0.95rem; line-height: 1.6;">
                {ml_insight}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ==================== SECTION 6: Quick Access ====================
    st.markdown("""
    <div class='section-header' style='margin-top: 28px;'>
        <h2>🚀 Quick Access</h2>
        <span class='section-badge'>SHORTCUTS</span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        st.markdown("""
            <div style='text-align: center; padding: 20px 0;'>
                <div style='font-size: 2.5rem; margin-bottom: 12px;'>🤖</div>
                <h4 style='margin: 0 0 8px 0; color: #1a202c; font-weight: 600;'>AI Transaction Intelligence</h4>
                <p style='margin: 0 0 16px 0; color: #718096; font-size: 0.9rem;'>Real-time AI monitoring & detection</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🔍 Open Monitor", use_container_width=True, key="btn_monitor"):
            st.success("✓ Use sidebar to navigate to AI & Machine Learning Intelligence")

    with col2:
        st.markdown("""
            <div style='text-align: center; padding: 20px 0;'>
                <div style='font-size: 2.5rem; margin-bottom: 12px;'>🧠</div>
                <h4 style='margin: 0 0 8px 0; color: #1a202c; font-weight: 600;'>Scenario Analysis</h4>
                <p style='margin: 0 0 16px 0; color: #718096; font-size: 0.9rem;'>13 fraud detection scenarios</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("📊 View Scenarios", use_container_width=True, key="btn_scenarios"):
            st.success("✓ Use sidebar to navigate to Scenario Analysis")

    with col3:
        st.markdown("""
            <div style='text-align: center; padding: 20px 0;'>
                <div style='font-size: 2.5rem; margin-bottom: 12px;'>📈</div>
                <h4 style='margin: 0 0 8px 0; color: #1a202c; font-weight: 600;'>Geographic Analytics</h4>
                <p style='margin: 0 0 16px 0; color: #718096; font-size: 0.9rem;'>Location-based fraud patterns</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🌍 View Geo Data", use_container_width=True, key="btn_geo"):
            st.success("✓ Use sidebar to navigate to Geo Analytics")

    # ==================== SECTION 7: AI Threshold Optimization ====================
    st.markdown("""
    <div class='section-header' style='margin-top: 28px;'>
        <h2>🎯 AI-Powered Dynamic Threshold Optimization</h2>
        <span class='section-badge'>ADAPTIVE</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='dashboard-card primary'>
        <p style='margin: 0; font-size: 0.95rem; color: #4a5568; line-height: 1.6;'>
            Our system continuously monitors fraud patterns and automatically adjusts detection thresholds
            based on real-time data analysis for optimal balance between fraud detection and operational efficiency.
        </p>
    </div>
    """, unsafe_allow_html=True)

    threshold_col1, threshold_col2 = st.columns([2, 1], gap="medium")

    with threshold_col1:
        st.markdown("<div class='subsection-header'><h3>📊 Current Threshold Performance</h3></div>", unsafe_allow_html=True)

        current_metrics = pd.DataFrame({
            'Threshold Type': ['Auto-Clear', 'Manual Review', 'High Priority', 'Critical'],
            'Current Value': [0.30, 0.60, 0.80, 0.90],
            'Utilization': [95.2, 4.5, 0.25, 0.05],
            'Efficiency': [98.5, 87.3, 92.1, 99.2]
        })

        st.dataframe(
            current_metrics,
            use_container_width=True,
            hide_index=True,
            height=200,
            column_config={
                'Current Value': st.column_config.ProgressColumn(
                    'Current Value',
                    min_value=0,
                    max_value=1,
                    format='%.2f'
                ),
                'Utilization': st.column_config.ProgressColumn(
                    'Utilization %',
                    min_value=0,
                    max_value=100,
                    format='%.1f%%'
                ),
                'Efficiency': st.column_config.ProgressColumn(
                    'Efficiency %',
                    min_value=0,
                    max_value=100,
                    format='%.1f%%'
                )
            }
        )

    with threshold_col2:
        st.markdown("<div class='subsection-header'><h3>🤖 AI Recommendations</h3></div>", unsafe_allow_html=True)

        threshold_rec = ai_engine.get_threshold_recommendation(
            current_threshold=0.60,
            recent_stats={
                'false_positive_rate': 0.062,
                'detection_rate': 0.942,
                'queue_size': 632,
                'avg_time': 45
            }
        )

        # Display threshold recommendation with styling
        st.markdown(f"""
        <div style='background: #e3f2fd; padding: 12px; border-radius: 8px; border-left: 4px solid #2196f3; margin-bottom: 12px;'>
            <div style='color: #1565c0; font-size: 0.9rem; line-height: 1.6;'>
                {threshold_rec}
            </div>
        </div>
        """, unsafe_allow_html=True)

        fraud_trend = [45, 47, 44, 52, 51, 48, 47]
        trend_analysis = ai_engine.get_trend_analysis(
            metric_name="Daily Fraud Detection",
            trend_data=fraud_trend
        )

        # Display trend analysis with styling
        st.markdown(f"""
        <div style='background: #e8f5e9; padding: 12px; border-radius: 8px; border-left: 4px solid #4caf50;'>
            <div style='color: #2e7d32; font-size: 0.9rem; line-height: 1.6;'>
                {trend_analysis}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ==================== FOOTER ====================
    st.markdown("<hr style='margin-top: 32px;'>", unsafe_allow_html=True)

    st.markdown("""
    <div style='background: linear-gradient(135deg, #f7fafc, #edf2f7); padding: 20px; border-radius: 12px; margin-top: 20px;'>
        <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; text-align: center;'>
            <div>
                <p style='margin: 0; color: #718096; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;'>System Info</p>
                <p style='margin: 4px 0 0 0; color: #2d3748; font-weight: 600;'>v2.5.3 • SQLite</p>
            </div>
            <div>
                <p style='margin: 0; color: #718096; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;'>Status</p>
                <p style='margin: 4px 0 0 0; color: #2d3748; font-weight: 600;'>✅ Healthy • Just now</p>
            </div>
            <div>
                <p style='margin: 0; color: #718096; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;'>Support</p>
                <p style='margin: 4px 0 0 0; color: #2d3748; font-weight: 600;'>support@arribaadvisors.com</p>
            </div>
        </div>
        <p style='margin: 16px 0 0 0; text-align: center; color: #a0aec0; font-size: 0.8rem;'>
            © 2024 Arriba Advisors. All rights reserved.
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    render()
