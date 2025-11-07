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
from streamlit_app.ai_recommendations import get_ai_engine, render_ai_insight, render_adaptive_ai_banner


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

    # Executive Alert Notification System
    st.markdown("## 📨 Executive Alert Center")
    st.markdown("**Automated Daily Briefing & Critical Notifications**")

    # Alert tabs
    alert_tab1, alert_tab2, alert_tab3 = st.tabs(["🚨 Critical Alerts", "📊 Daily Summary", "📈 Trend Alerts"])

    with alert_tab1:
        st.markdown("### Critical Fraud Alerts (Last 24 Hours)")
        st.markdown("*Auto-sent to: CFO, Chief Risk Officer, VP Compliance*")

        critical_alerts = [
            {
                "time": "2 hours ago",
                "severity": "🔴 CRITICAL",
                "title": "Coordinated Account Takeover Pattern Detected",
                "description": "15 accounts showing simultaneous phone number changes followed by large transfers ($187K total). Geographic clustering in Lagos, Nigeria.",
                "action": "Fraud team investigating. 12 transactions blocked. Customer notifications in progress.",
                "recipients": "CFO, CRO, VP Fraud Prevention"
            },
            {
                "time": "4 hours ago",
                "severity": "🟠 HIGH",
                "title": "Merchant Category Fraud Spike - Cryptocurrency",
                "description": "Cryptocurrency transactions showing 340% increase in fraud rate (8.5% → 28.9%). $420K in suspicious activity detected.",
                "action": "Enhanced monitoring enabled. Thresholds adjusted. Analyst team expanded.",
                "recipients": "CRO, VP Compliance, Director AML"
            },
            {
                "time": "6 hours ago",
                "severity": "🟠 HIGH",
                "title": "False Positive Rate Increase - Manual Review Queue",
                "description": "Review queue increased to 892 cases (41% above normal). False positive rate: 8.7% (target: 6.2%).",
                "action": "AI threshold optimization in progress. Additional analysts assigned.",
                "recipients": "VP Operations, CRO"
            }
        ]

        for alert in critical_alerts:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fff5f5 0%, #ffe5e5 100%);
                        padding: 20px; border-radius: 10px; margin: 15px 0;
                        border-left: 5px solid {'#ef4444' if 'CRITICAL' in alert['severity'] else '#f97316'};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-weight: bold; font-size: 16px;">{alert['severity']}</span>
                    <span style="color: #666; font-size: 14px;">⏰ {alert['time']}</span>
                </div>
                <h4 style="margin: 10px 0; color: #1f2937;">{alert['title']}</h4>
                <p style="color: #4b5563; margin: 10px 0; line-height: 1.6;">{alert['description']}</p>
                <div style="background: white; padding: 12px; border-radius: 5px; margin: 10px 0;">
                    <strong style="color: #059669;">✓ Action Taken:</strong> {alert['action']}
                </div>
                <div style="color: #6b7280; font-size: 13px; margin-top: 10px;">
                    <strong>📧 Notification Sent To:</strong> {alert['recipients']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    with alert_tab2:
        st.markdown("### Daily Fraud Detection Summary")
        st.markdown(f"*Automatically sent every morning at 7:00 AM to executive team*")
        st.markdown(f"**Report Date:** {datetime.now().strftime('%B %d, %Y')}")

        summary_col1, summary_col2, summary_col3 = st.columns(3)

        with summary_col1:
            st.markdown("""
            <div style="background: #f0fdf4; padding: 20px; border-radius: 10px; border-left: 4px solid #10b981;">
                <h3 style="color: #059669; margin: 0;">✓ Prevention Success</h3>
                <h2 style="color: #047857; margin: 10px 0;">$2.3M</h2>
                <p style="color: #065f46; margin: 0;">Fraud Prevented (24 hrs)</p>
                <p style="font-size: 13px; color: #6b7280; margin-top: 8px;">47 fraudulent transactions blocked</p>
            </div>
            """, unsafe_allow_html=True)

        with summary_col2:
            st.markdown("""
            <div style="background: #fffbeb; padding: 20px; border-radius: 10px; border-left: 4px solid #f59e0b;">
                <h3 style="color: #d97706; margin: 0;">⚠️ Under Review</h3>
                <h2 style="color: #b45309; margin: 10px 0;">632</h2>
                <p style="color: #92400e; margin: 0;">Manual Reviews Pending</p>
                <p style="font-size: 13px; color: #6b7280; margin-top: 8px;">Avg. resolution time: 45 min</p>
            </div>
            """, unsafe_allow_html=True)

        with summary_col3:
            st.markdown("""
            <div style="background: #eff6ff; padding: 20px; border-radius: 10px; border-left: 4px solid #3b82f6;">
                <h3 style="color: #2563eb; margin: 0;">📊 System Health</h3>
                <h2 style="color: #1e40af; margin: 10px 0;">94.2%</h2>
                <p style="color: #1e3a8a; margin: 0;">Detection Accuracy</p>
                <p style="font-size: 13px; color: #6b7280; margin-top: 8px;">False positive: 6.2%</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("### 📋 Key Highlights from Past 24 Hours")

        highlights = pd.DataFrame({
            "Category": ["Geographic Patterns", "Transaction Velocity", "Merchant Risk", "Account Behavior", "Detection Rules"],
            "Status": ["🔴 Alert", "🟢 Normal", "🟠 Elevated", "🟢 Normal", "🟢 Optimal"],
            "Metric": [
                "California VPN fraud +45%",
                "Average velocity: 3.2 tx/hr",
                "Crypto fraud rate: 8.5% → 28.9%",
                "Account takeover: 15 cases",
                "Top rule precision: 98.1%"
            ],
            "Action Required": [
                "Enhanced CA monitoring active",
                "No action needed",
                "Threshold adjusted, monitoring",
                "Investigations ongoing",
                "No action needed"
            ]
        })

        st.dataframe(
            highlights,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Status": st.column_config.TextColumn("Status", width="small")
            }
        )

    with alert_tab3:
        st.markdown("### Fraud Pattern & Trend Alerts")
        st.markdown("*Triggered automatically when trends exceed thresholds*")

        trend_alerts = [
            {
                "icon": "📈",
                "type": "PATTERN ALERT",
                "color": "#3b82f6",
                "title": "New Fraud Pattern Detected: Payroll Rerouting via BEC",
                "details": "7 incidents in past 48 hours. Pattern: HR email compromise → payroll redirect. Average loss per incident: $18,500.",
                "trend": "Emerging threat - 0 cases last week → 7 cases this week",
                "recommendation": "Alert HR departments. Implement additional payroll verification step.",
                "sent_to": "CFO, CISO, VP HR"
            },
            {
                "icon": "🌍",
                "type": "GEOGRAPHIC ALERT",
                "color": "#8b5cf6",
                "title": "Geographic Fraud Spike: California Region",
                "details": "VPN/proxy fraud in California increased 45% (145 cases vs. 100 baseline). Concentrated in LA and San Francisco metro areas.",
                "trend": "7-day trend: +12, +8, +15, +22, +18, +31, +45",
                "recommendation": "Enhanced monitoring for CA transactions. Consider temporary threshold reduction.",
                "sent_to": "CRO, Regional Risk Managers"
            },
            {
                "icon": "💰",
                "type": "VOLUME ALERT",
                "color": "#ec4899",
                "title": "High-Value Transaction Surge Detected",
                "details": "Transactions >$50K increased 67% today (89 vs. 53 baseline). 12 flagged for enhanced review.",
                "trend": "Possibly legitimate - Q4 seasonal pattern observed",
                "recommendation": "Monitor for 48 hours. Analyst workload increased.",
                "sent_to": "VP Operations, CRO"
            }
        ]

        for alert in trend_alerts:
            st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 10px; margin: 15px 0;
                        border-left: 5px solid {alert['color']}; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; align-items: center; margin-bottom: 12px;">
                    <span style="font-size: 32px; margin-right: 15px;">{alert['icon']}</span>
                    <div>
                        <span style="background: {alert['color']}; color: white; padding: 4px 12px;
                                     border-radius: 4px; font-size: 12px; font-weight: bold;">
                            {alert['type']}
                        </span>
                    </div>
                </div>
                <h4 style="margin: 10px 0; color: #1f2937;">{alert['title']}</h4>
                <p style="color: #4b5563; margin: 10px 0; line-height: 1.6;"><strong>Details:</strong> {alert['details']}</p>
                <p style="color: #6b7280; margin: 10px 0;"><strong>Trend:</strong> {alert['trend']}</p>
                <div style="background: #f0fdf4; padding: 12px; border-radius: 5px; margin: 10px 0; border-left: 3px solid #10b981;">
                    <strong style="color: #059669;">💡 AI Recommendation:</strong> {alert['recommendation']}
                </div>
                <div style="color: #6b7280; font-size: 13px; margin-top: 10px;">
                    <strong>📧 Alert Sent To:</strong> {alert['sent_to']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

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

    # Adaptive AI Banner
    render_adaptive_ai_banner()

    st.markdown("---")

    # Executive AI Strategy Section
    st.markdown("## 🎯 AI-Powered Strategic Insights")

    insight_col1, insight_col2 = st.columns(2)

    with insight_col1:
        st.markdown("### 🔮 Predictive Analytics & Dynamic Thresholds")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    padding: 20px; border-radius: 10px; color: white;">
            <h4 style="margin-top: 0;">Next-Generation Fraud Prevention</h4>
            <p style="font-size: 14px; line-height: 1.6;">
                Our AI continuously analyzes transaction patterns, geographic trends, and
                emerging fraud vectors to automatically adjust detection thresholds. This
                ensures optimal protection while minimizing false positives.
            </p>
            <ul style="font-size: 13px; line-height: 1.8;">
                <li>Real-time pattern recognition</li>
                <li>Adaptive risk scoring</li>
                <li>Automated threshold optimization</li>
                <li>Predictive fraud forecasting</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # AI Strategic Recommendation
        ai_engine = get_ai_engine()
        strategic_rec = ai_engine.get_pattern_insight(
            pattern_type="strategic",
            pattern_data={
                "fraud_rate_trend": "stable",
                "false_positive_trend": "declining",
                "new_patterns_detected": 3,
                "system_efficiency": 94.2
            }
        )

        st.markdown("### 🤖 AI Strategic Recommendation")
        st.info(strategic_rec)

    with insight_col2:
        st.markdown("### 📊 Rule Performance Insights")

        # Get top 3 rules
        top_rules = rule_performance_df.nlargest(3, 'confirmed_fraud_count')

        for idx, row in top_rules.iterrows():
            rule_insight = ai_engine.get_rule_optimization(
                rule_name=row['rule_name'],
                performance={
                    'precision': row['precision'],
                    'frequency': row['trigger_frequency'],
                    'fp_rate': row['false_positive_rate'],
                    'catches': row['confirmed_fraud_count']
                }
            )

            render_ai_insight(
                title=f"Top Rule: {row['rule_name'][:30]}...",
                recommendation=rule_insight,
                icon="⭐"
            )

    st.markdown("---")

    st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | **Note:** Using enhanced synthetic data for demonstration")

if __name__ == "__main__" or True:
    render()
