
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

    # Add custom CSS for compact layout
    st.markdown("""
    <style>
    /* Reduce default spacing */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }

    /* Tighten section spacing */
    .stMarkdown {
        margin-bottom: 0.5rem;
    }

    /* Reduce header margins */
    h2 {
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
    }

    h3 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* Compact dataframe */
    .stDataFrame {
        margin-bottom: 0.5rem;
    }

    /* Reduce plotly chart margins */
    .js-plotly-plot {
        margin-bottom: 0rem !important;
    }

    /* Compact metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }

    /* Reduce column gap */
    [data-testid="column"] {
        padding: 0 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    render_page_header(
        title="Arriba Advisors Transaction Screening System",
        subtitle="Real-Time Fraud Detection & Prevention Analytics",
        show_logo=False  # Logo is in sidebar
    )

    # Get standardized chart colors
    colors = get_chart_colors()

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
        height=180,  # Compact height
        column_config={
            'Risk Score': st.column_config.ProgressColumn(
                'Risk Score',
                min_value=0,
                max_value=1,
                format='%.2f'
            )
        }
    )

    # Transaction Flow & Decision Analytics (side by side, compact)
    col1, col2 = st.columns([1, 1], gap="small")

    with col1:
        st.markdown("### 🤖 Transaction Lifecycle Monitor")

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
            height=280,  # Reduced from 400
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_funnel, use_container_width=True, key="analyst_funnel_chart")

        st.caption("💰 **Cost Savings**: Manual reviews prevented: 11,915 × $5 = **$59,575/day**")

    with col2:
        st.markdown("### 🧠 Decision Pattern Analytics")

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
            height=280,  # Reduced from 400
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(title='Count', title_font_size=11),
            yaxis2=dict(title='Confidence %', overlaying='y', side='right', range=[0, 100], title_font_size=11),
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=10))
        )

        st.plotly_chart(fig_decisions, use_container_width=True, key="analyst_decisions_chart")

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
        yaxis=dict(title='Transaction Volume', title_font_size=11),
        yaxis2=dict(title='Fraud Cases', overlaying='y', side='right', title_font_size=11),
        hovermode='x unified',
        height=280,  # Reduced from 400
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=10))
    )

    st.plotly_chart(fig, use_container_width=True, key="analyst_pulse_chart")

    # Quick Access Panels (more compact)
    st.markdown("## 🚀 Quick Access")

    col1, col2, col3 = st.columns(3, gap="small")

    with col1:
        st.markdown("**🤖 AI Transaction Intelligence**")
        st.caption("Real-time AI-powered transaction monitoring")
        if st.button("Open Monitor", use_container_width=True, key="btn_monitor"):
            st.info("Navigate via sidebar")

    with col2:
        st.markdown("**🧠 AI Scenario Intelligence**")
        st.caption("ML-driven analysis of 13 fraud scenarios")
        if st.button("View Scenarios", use_container_width=True, key="btn_scenarios"):
            st.info("Navigate via sidebar")

    with col3:
        st.markdown("**📊 AI Rule Performance**")
        st.caption("ML-powered rule analysis")
        if st.button("Analyze Rules", use_container_width=True, key="btn_rules"):
            st.info("Navigate via sidebar")

    # AI-Powered Dynamic Threshold Optimization (more compact)
    st.markdown("## 🎯 AI-Powered Dynamic Threshold Optimization")

    st.markdown("""
    <div style="background: #f8f9fa; padding: 12px; border-radius: 8px; border-left: 4px solid #667eea; margin: 8px 0;">
        <p style="margin: 0; font-size: 0.9rem; color: #666;">
            Our system continuously monitors fraud patterns and automatically adjusts detection thresholds
            based on real-time data analysis for optimal balance between fraud detection and operational efficiency.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # AI Recommendations for Current Thresholds (more compact)
    threshold_col1, threshold_col2 = st.columns([2, 1], gap="small")

    with threshold_col1:
        st.markdown("### 📊 Current Threshold Performance")

        # Mock current threshold metrics
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
            height=180,  # Compact height
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
        st.markdown("### 🤖 AI Recommendations")

        # Get AI recommendation for thresholds
        ai_engine = get_ai_engine()
        threshold_rec = ai_engine.get_threshold_recommendation(
            current_threshold=0.60,
            recent_stats={
                'false_positive_rate': 0.062,
                'detection_rate': 0.942,
                'queue_size': 632,
                'avg_time': 45
            }
        )

        st.info(threshold_rec)

        # Trend insight
        fraud_trend = [45, 47, 44, 52, 51, 48, 47]
        trend_analysis = ai_engine.get_trend_analysis(
            metric_name="Daily Fraud Detection",
            trend_data=fraud_trend
        )

        st.success(trend_analysis)

    # ML Intelligence Section (more compact)
    st.markdown("## 🤖 Machine Learning Intelligence")

    ml_col1, ml_col2, ml_col3, ml_col4 = st.columns(4, gap="small")

    with ml_col1:
        st.metric("Model Accuracy", "94.3%", "+1.2%")
    with ml_col2:
        st.metric("AUC-ROC Score", "0.963", "+0.008")
    with ml_col3:
        st.metric("Predictions/Min", "1,247", "+156")
    with ml_col4:
        st.metric("Avg Confidence", "87.2%", "+2.3%")

    ml_viz_col1, ml_viz_col2 = st.columns(2, gap="small")

    with ml_viz_col1:
        st.markdown("### 🎯 Model Performance Trends")

        # Model performance over last 7 days
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
            height=250,  # Reduced from 350
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(title='Score', range=[0.85, 0.98], title_font_size=11),
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=10))
        )

        st.plotly_chart(fig_ml_perf, use_container_width=True, key="ml_performance_trends")

    with ml_viz_col2:
        st.markdown("### 📊 Prediction Confidence Distribution")

        # Generate prediction confidence distribution
        np.random.seed(42)
        confidence_scores = np.concatenate([
            np.random.beta(8, 2, 400),  # High confidence predictions
            np.random.beta(2, 2, 100)   # Low confidence predictions
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
            height=250,  # Reduced from 350
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(title='Confidence Score (%)', title_font_size=11),
            yaxis=dict(title='Number of Predictions', title_font_size=11),
            showlegend=False
        )

        st.plotly_chart(fig_conf, use_container_width=True, key="ml_confidence_dist")

    ml_viz_col3, ml_viz_col4 = st.columns(2, gap="small")

    with ml_viz_col3:
        st.markdown("### 🔍 Top Feature Importance")

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
            height=250,  # Reduced from 350
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(title='Importance Score', title_font_size=11),
            yaxis=dict(title='', tickfont=dict(size=10)),
            showlegend=False
        )

        st.plotly_chart(fig_features, use_container_width=True, key="ml_feature_importance")

    with ml_viz_col4:
        st.markdown("### ⚡ Real-time Model Health")

        # Model health metrics
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
            height=250,  # Reduced from 350
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(title='Health Score (%)', range=[0, 110], title_font_size=11),
            yaxis=dict(title='', tickfont=dict(size=10)),
            showlegend=False
        )

        st.plotly_chart(fig_health, use_container_width=True, key="ml_health_metrics")

    # AI Insight for ML Performance (more compact)
    st.markdown("### 💡 ML Performance Insights")

    ai_engine = get_ai_engine()
    ml_insight = ai_engine.get_ml_performance_insight(
        accuracy=0.943,
        precision=0.932,
        recall=0.906,
        auc_roc=0.963,
        trend='improving'
    )

    render_ai_insight("ML Performance Analysis", ml_insight, icon="🤖")

    # Footer (more compact)
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption("**System Version:** 2.5.3 | **Database:** SQLite")
    with col2:
        st.caption("**API Status:** ✅ Healthy | **Last Sync:** Just now")
    with col3:
        st.caption("**Support:** support@arribaadvisors.com")

    st.caption("© 2024 Arriba Advisors. All rights reserved.")

if __name__ == "__main__":
    render()
