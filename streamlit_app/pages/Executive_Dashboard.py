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

    # Executive Decision Framework
    st.markdown("## 🎯 Executive Decision Framework")
    st.markdown("**Strategic Guidance: From Data to Action**")

    decision_tab1, decision_tab2, decision_tab3 = st.tabs([
        "🎯 Decision Matrix",
        "🔍 Fraud Profiling",
        "💼 Resource Allocation"
    ])

    with decision_tab1:
        st.markdown("### Strategic Decision Matrix")
        st.markdown("**What You See → Why It Matters → What To Do**")

        decision_matrix = pd.DataFrame({
            "Observation": [
                "Fraud prevented: $2.3M today",
                "False positive rate: 6.2%",
                "Review queue: 632 cases",
                "California VPN fraud +45%",
                "Crypto merchant fraud: 28.9%",
                "Detection accuracy: 94.2%"
            ],
            "Implication": [
                "System ROI: $2.3M saved vs. $59K operating cost = 39:1 ratio",
                "Acceptable range (target: 5-8%). Analyst productivity optimal",
                "Backlog forming. Current resolution: 45 min/case = 474 analyst hours",
                "Regional fraud ring likely. Organized criminal activity",
                "High-risk merchant category. Industry-wide vulnerability",
                "Strong performance but 5.8% fraud still escapes (potential $140K/day exposure)"
            ],
            "Decision Required": [
                "✓ Maintain current investment. Report ROI to board",
                "✓ No action. Monitor weekly. Alert if exceeds 8%",
                "⚠️ Deploy 2 additional analysts OR adjust thresholds to reduce queue",
                "🔴 Enable enhanced CA screening. Consider temp transaction limits",
                "🔴 Restrict crypto merchants OR increase monitoring/hold times",
                "✓ Investigate false negatives. Consider additional rule deployment"
            ],
            "Priority": ["Low", "Low", "Medium", "High", "High", "Medium"]
        })

        st.dataframe(
            decision_matrix,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Priority": st.column_config.TextColumn("Priority", width="small")
            }
        )

        st.markdown("---")
        st.markdown("### 🎯 Immediate Action Items (Next 24-48 Hours)")

        action_col1, action_col2 = st.columns(2)

        with action_col1:
            st.markdown("""
            <div style="background: #fee2e2; padding: 20px; border-radius: 10px; border-left: 4px solid #ef4444;">
                <h4 style="color: #991b1b; margin-top: 0;">🔴 Critical Actions</h4>
                <ol style="color: #7f1d1d; line-height: 2;">
                    <li><strong>California Fraud Ring:</strong> Deploy regional fraud specialist.
                        Review all CA transactions >$5K manually for 48 hours.</li>
                    <li><strong>Cryptocurrency Merchants:</strong> Emergency policy meeting with risk team.
                        Consider temporary hold period (24-48 hrs) for crypto transactions >$1K.</li>
                    <li><strong>Account Takeover Wave:</strong> Send customer security alerts.
                        Enable mandatory 2FA for phone number changes.</li>
                </ol>
                <p style="margin-top: 15px; font-weight: bold; color: #7f1d1d;">
                    ⏰ Timeline: Implement within 24 hours
                </p>
            </div>
            """, unsafe_allow_html=True)

        with action_col2:
            st.markdown("""
            <div style="background: #fef3c7; padding: 20px; border-radius: 10px; border-left: 4px solid #f59e0b;">
                <h4 style="color: #92400e; margin-top: 0;">🟠 High Priority Actions</h4>
                <ol style="color: #78350f; line-height: 2;">
                    <li><strong>Review Queue Backlog:</strong> Allocate 2 FTE from adjacent team
                        OR adjust auto-clear threshold from 0.30 to 0.35 (reduce queue by ~150 cases).</li>
                    <li><strong>Payroll BEC Pattern:</strong> Partner with HR to issue company-wide
                        alert. Implement secondary verification for payroll changes.</li>
                    <li><strong>False Negative Review:</strong> Schedule rules committee meeting.
                        Analyze 5.8% escape rate for pattern gaps.</li>
                </ol>
                <p style="margin-top: 15px; font-weight: bold; color: #78350f;">
                    ⏰ Timeline: Implement within 48-72 hours
                </p>
            </div>
            """, unsafe_allow_html=True)

    with decision_tab2:
        st.markdown("### Fraud Profile Analysis")
        st.markdown("**Recurring Fraud Types & Mitigation Strategies**")

        fraud_profiles = [
            {
                "type": "Account Takeover (ATO)",
                "icon": "🔐",
                "frequency": "15 cases/day",
                "avg_loss": "$12,400/incident",
                "total_exposure": "$186K/day",
                "trend": "📈 +23% this week",
                "characteristics": [
                    "Phone number/SIM changes immediately before large transfers",
                    "Geographic anomalies (Lagos, Eastern Europe)",
                    "Device fingerprint changes",
                    "Off-hours activity (2-4 AM)"
                ],
                "root_causes": [
                    "Phishing campaigns targeting mobile banking users",
                    "SIM swap social engineering at carriers",
                    "Credential stuffing from breached databases"
                ],
                "mitigation_steps": [
                    "✓ Implement mandatory 2FA for phone number changes",
                    "✓ Add 24-hour cooling period for high-risk account changes",
                    "✓ Partner with carriers to flag SIM swap requests",
                    "✓ Deploy behavioral biometrics (typing patterns, mouse movements)",
                    "⚠️ Estimated cost: $85K implementation, $15K/month ongoing",
                    "💰 Expected reduction: 60-70% of ATO cases"
                ]
            },
            {
                "type": "Business Email Compromise (BEC)",
                "icon": "📧",
                "frequency": "7 cases/week",
                "avg_loss": "$18,500/incident",
                "total_exposure": "$130K/week",
                "trend": "📈 +340% vs. last month",
                "characteristics": [
                    "Payroll rerouting requests via email",
                    "Vendor payment account changes",
                    "Executive impersonation (CFO, CEO)",
                    "Urgent language and tight deadlines"
                ],
                "root_causes": [
                    "Email account compromises (phishing)",
                    "Lack of out-of-band verification",
                    "No secondary approval workflow"
                ],
                "mitigation_steps": [
                    "✓ Mandate voice/phone verification for payment changes >$5K",
                    "✓ Implement dual approval for beneficiary additions",
                    "✓ Deploy email authentication (DMARC, SPF, DKIM)",
                    "✓ Security awareness training for finance team (quarterly)",
                    "⚠️ Estimated cost: $12K training, $0 for policy changes",
                    "💰 Expected reduction: 80-90% of BEC cases"
                ]
            },
            {
                "type": "Geographic/VPN Fraud",
                "icon": "🌍",
                "frequency": "145 cases/day (CA spike)",
                "avg_loss": "$3,200/incident",
                "total_exposure": "$464K/day",
                "trend": "📈 +45% California region",
                "characteristics": [
                    "VPN/proxy usage to mask location",
                    "High-risk countries (Nigeria, Eastern Europe)",
                    "Multiple accounts from same IP",
                    "Rapid-fire transaction attempts"
                ],
                "root_causes": [
                    "Organized fraud rings",
                    "Stolen credential marketplaces",
                    "Geographic restrictions easily bypassed"
                ],
                "mitigation_steps": [
                    "✓ Enhanced screening for VPN-detected transactions",
                    "✓ Velocity limits per IP address (5 transactions/hour)",
                    "✓ Mandatory delays for first transaction after location change",
                    "✓ Partner with fraud intelligence networks for IP reputation",
                    "⚠️ Estimated cost: $45K for IP intelligence feeds",
                    "💰 Expected reduction: 40-50% of geo fraud"
                ]
            },
            {
                "type": "Merchant Category Fraud",
                "icon": "💳",
                "frequency": "Crypto: 89 cases/day",
                "avg_loss": "$4,700/incident",
                "total_exposure": "$418K/day",
                "trend": "🔴 Critical: 8.5% → 28.9% fraud rate",
                "characteristics": [
                    "Cryptocurrency merchants highest risk",
                    "Gaming and digital goods second tier",
                    "Chargebacks after 30-60 days",
                    "Stolen card testing"
                ],
                "root_causes": [
                    "Irreversible nature of crypto transactions",
                    "Limited merchant verification",
                    "High-value, low-friction purchases"
                ],
                "mitigation_steps": [
                    "✓ Implement 24-48 hour hold for crypto transactions >$1K",
                    "✓ Require additional verification (ID, selfie) for new crypto customers",
                    "✓ Partner with crypto exchanges for wallet reputation scoring",
                    "✓ Consider restricting or exiting high-risk merchant relationships",
                    "⚠️ Estimated cost: $0 (policy change), potential revenue impact: $200K/month",
                    "💰 Expected reduction: 70-80% of crypto fraud"
                ]
            }
        ]

        for profile in fraud_profiles:
            with st.expander(f"{profile['icon']} **{profile['type']}** - {profile['frequency']} | {profile['trend']}", expanded=False):
                st.markdown(f"**Average Loss:** {profile['avg_loss']} | **Total Daily Exposure:** {profile['total_exposure']}")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### 📋 Fraud Characteristics")
                    for char in profile['characteristics']:
                        st.markdown(f"• {char}")

                    st.markdown("#### 🔍 Root Causes")
                    for cause in profile['root_causes']:
                        st.markdown(f"• {cause}")

                with col2:
                    st.markdown("#### 🛡️ Mitigation Strategy")
                    for step in profile['mitigation_steps']:
                        if step.startswith("⚠️"):
                            st.warning(step)
                        elif step.startswith("💰"):
                            st.success(step)
                        else:
                            st.markdown(step)

    with decision_tab3:
        st.markdown("### Resource Allocation Recommendations")
        st.markdown("**Strategic Investment Priorities Based on ROI**")

        st.markdown("""
        <div style="background: #f0fdf4; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #10b981;">
            <h4 style="color: #065f46; margin-top: 0;">💰 Current System ROI</h4>
            <p style="color: #064e3b; font-size: 16px; line-height: 1.8;">
                <strong>Daily Fraud Prevention:</strong> $2.3M<br>
                <strong>Operating Cost:</strong> ~$59K/day (analysts + infrastructure)<br>
                <strong>ROI:</strong> 39:1 (For every $1 spent, $39 in fraud prevented)<br>
                <strong>Annual Impact:</strong> $839M prevented vs. $21.5M cost = <strong>$817M net benefit</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📊 Recommended Investment Portfolio")

        investments = pd.DataFrame({
            "Initiative": [
                "Additional Analyst Team (4 FTE)",
                "Advanced Behavioral Biometrics",
                "Enhanced VPN/Proxy Detection",
                "Cryptocurrency Transaction Holds",
                "BEC Prevention Training & Tools",
                "IP Intelligence Feeds",
                "2FA Enforcement Infrastructure"
            ],
            "Cost": [
                "$400K/year",
                "$85K + $15K/mo",
                "$45K/year",
                "$0 (policy)",
                "$12K/year",
                "$45K/year",
                "$125K one-time"
            ],
            "Expected Benefit": [
                "$290K/year (reduce resolution time)",
                "$4.1M/year (60% ATO reduction)",
                "$3.4M/year (40% geo fraud reduction)",
                "$10.9M/year (75% crypto fraud reduction)",
                "$5.0M/year (85% BEC reduction)",
                "$3.4M/year (with enhanced detection)",
                "$4.1M/year (supports ATO prevention)"
            ],
            "ROI": ["0.7:1", "22:1", "76:1", "∞", "417:1", "76:1", "33:1"],
            "Priority": ["Medium", "High", "High", "Critical", "Critical", "High", "High"],
            "Timeline": ["Ongoing", "3-4 months", "1 month", "Immediate", "2 weeks", "1 month", "2-3 months"]
        })

        st.dataframe(
            investments,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Priority": st.column_config.TextColumn("Priority", width="small"),
                "Timeline": st.column_config.TextColumn("Timeline", width="small")
            }
        )

        st.markdown("---")

        priority_col1, priority_col2, priority_col3 = st.columns(3)

        with priority_col1:
            st.markdown("""
            <div style="background: #fee2e2; padding: 15px; border-radius: 8px;">
                <h5 style="color: #991b1b; margin-top: 0;">🔴 Critical Priority</h5>
                <ul style="color: #7f1d1d; font-size: 14px;">
                    <li>Crypto holds (Immediate)</li>
                    <li>BEC training (2 weeks)</li>
                </ul>
                <p style="margin: 10px 0 0 0; font-weight: bold; color: #991b1b;">
                    Total: $12K<br>
                    Benefit: $15.9M/year
                </p>
            </div>
            """, unsafe_allow_html=True)

        with priority_col2:
            st.markdown("""
            <div style="background: #fef3c7; padding: 15px; border-radius: 8px;">
                <h5 style="color: #92400e; margin-top: 0;">🟠 High Priority</h5>
                <ul style="color: #78350f; font-size: 14px;">
                    <li>Behavioral biometrics</li>
                    <li>VPN/IP detection</li>
                    <li>2FA enforcement</li>
                </ul>
                <p style="margin: 10px 0 0 0; font-weight: bold; color: #92400e;">
                    Total: $300K<br>
                    Benefit: $10.9M/year
                </p>
            </div>
            """, unsafe_allow_html=True)

        with priority_col3:
            st.markdown("""
            <div style="background: #dbeafe; padding: 15px; border-radius: 8px;">
                <h5 style="color: #1e40af; margin-top: 0;">🔵 Consider</h5>
                <ul style="color: #1e3a8a; font-size: 14px;">
                    <li>Additional analysts</li>
                    <li>Enhanced tools</li>
                    <li>Advanced AI/ML</li>
                </ul>
                <p style="margin: 10px 0 0 0; font-weight: bold; color: #1e40af;">
                    Total: $400K+<br>
                    Benefit: Variable
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # ML Intelligence Executive Summary
        st.markdown("### 🤖 AI/ML Intelligence Summary")
        st.markdown("*Machine learning system performance and business impact*")

        ml_exec_col1, ml_exec_col2, ml_exec_col3, ml_exec_col4 = st.columns(4)

        with ml_exec_col1:
            st.metric("ML Detection Rate", "94.3%", "+2.1%")
        with ml_exec_col2:
            st.metric("False Positive Reduction", "18.5%", "-6.2%")
        with ml_exec_col3:
            st.metric("Cost Avoidance", "$2.3M", "+$450K")
        with ml_exec_col4:
            st.metric("Processing Speed", "12ms", "-3ms")

        ml_viz_col1, ml_viz_col2 = st.columns(2)

        with ml_viz_col1:
            st.markdown("#### 💰 ML ROI Analysis")

            roi_data = pd.DataFrame({
                'Category': ['Fraud Prevented', 'Labor Savings', 'Implementation Cost', 'Operating Cost'],
                'Annual Value': [2300000, 650000, -450000, -180000],
                'Type': ['Revenue', 'Revenue', 'Cost', 'Cost']
            })

            fig_roi = go.Figure()

            colors_roi = [colors['success'] if t == 'Revenue' else colors['danger']
                         for t in roi_data['Type']]

            fig_roi.add_trace(go.Bar(
                x=roi_data['Category'],
                y=roi_data['Annual Value'],
                marker=dict(color=colors_roi),
                text=[f"${abs(v/1000000):.1f}M" for v in roi_data['Annual Value']],
                textposition='outside'
            ))

            fig_roi.update_layout(
                title="AI/ML Annual Financial Impact",
                yaxis_title="Value ($)",
                height=350,
                showlegend=False
            )

            st.plotly_chart(fig_roi, use_container_width=True, key="exec_ml_roi")

            net_benefit = roi_data['Annual Value'].sum()
            roi_percentage = (net_benefit / 630000) * 100

            st.success(f"**Net Annual Benefit: ${net_benefit/1000000:.2f}M | ROI: {roi_percentage:.0f}%**")

        with ml_viz_col2:
            st.markdown("#### 📊 Model Performance vs Manual Review")

            comparison_data = pd.DataFrame({
                'Metric': ['Accuracy', 'Speed (tx/min)', 'Cost per Review', 'False Positives'],
                'ML System': [94.3, 1247, 0.15, 6.2],
                'Manual Only': [87.5, 45, 5.50, 24.8]
            })

            fig_comparison = go.Figure()

            fig_comparison.add_trace(go.Scatter(
                x=comparison_data['Metric'],
                y=comparison_data['ML System'],
                name='AI/ML System',
                mode='lines+markers',
                line=dict(color=colors['primary'], width=3),
                marker=dict(size=12)
            ))

            fig_comparison.add_trace(go.Scatter(
                x=comparison_data['Metric'],
                y=comparison_data['Manual Only'],
                name='Manual Only',
                mode='lines+markers',
                line=dict(color=colors['secondary'], width=3),
                marker=dict(size=12)
            ))

            fig_comparison.update_layout(
                title="Operational Efficiency Comparison",
                yaxis_title="Performance Index",
                height=350,
                hovermode='x unified'
            )

            st.plotly_chart(fig_comparison, use_container_width=True, key="exec_ml_comparison")

        # ML Strategic Insights
        st.markdown("#### 💡 Strategic ML Insights")

        insights_col1, insights_col2, insights_col3 = st.columns(3)

        with insights_col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 15px; border-radius: 10px; color: white; height: 150px;">
                <h5 style="margin-top: 0; color: white;">🎯 Model Accuracy Trend</h5>
                <p style="font-size: 14px;">ML models show consistent improvement with
                94.3% accuracy, up 2.1% QoQ. Fraud detection improving while reducing
                false positives by 6.2%.</p>
            </div>
            """, unsafe_allow_html=True)

        with insights_col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                        padding: 15px; border-radius: 10px; color: white; height: 150px;">
                <h5 style="margin-top: 0; color: white;">💰 Cost Efficiency</h5>
                <p style="font-size: 14px;">AI automation saves $650K annually in labor costs
                while processing 27x more transactions per minute than manual review alone.</p>
            </div>
            """, unsafe_allow_html=True)

        with insights_col3:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        padding: 15px; border-radius: 10px; color: white; height: 150px;">
                <h5 style="margin-top: 0; color: white;">📈 Recommendation</h5>
                <p style="font-size: 14px;">Consider expanding ML deployment to additional
                fraud scenarios. Current ROI of 367% justifies increased investment.</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("### 🎯 90-Day Action Plan")

        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; border: 2px solid #e5e7eb;">
            <h4>Phase 1: Immediate (Week 1-2)</h4>
            <ul style="line-height: 2;">
                <li>✓ Implement cryptocurrency transaction holds (policy change)</li>
                <li>✓ Deploy BEC awareness training for finance team</li>
                <li>✓ Enable California enhanced screening</li>
                <li>✓ Send customer security alerts for account changes</li>
            </ul>

            <h4>Phase 2: Short-term (Week 3-8)</h4>
            <ul style="line-height: 2;">
                <li>⚡ Procure and deploy IP intelligence feeds</li>
                <li>⚡ Begin 2FA enforcement infrastructure build</li>
                <li>⚡ Evaluate behavioral biometrics vendors (RFP)</li>
                <li>⚡ Establish partnerships with carriers for SIM swap alerts</li>
            </ul>

            <h4>Phase 3: Medium-term (Week 9-12)</h4>
            <ul style="line-height: 2;">
                <li>🔄 Deploy behavioral biometrics pilot program</li>
                <li>🔄 Roll out mandatory 2FA for account changes</li>
                <li>🔄 Complete enhanced VPN detection integration</li>
                <li>🔄 Review fraud reduction metrics and adjust strategy</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | **Note:** Using enhanced synthetic data for demonstration")

if __name__ == "__main__":
    render()
