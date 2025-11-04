"""
Scenario Analysis Page

Deep dive into specific fraud scenarios with detailed timelines and rule breakdowns.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime


# Complete fraud scenarios dataset
fraud_scenarios = {
    "1. Large Transfer - Low Activity": {
        "title": "Unusually Large Transfer from Low-Activity Account",
        "subtitle": "High-value transaction anomaly detection",
        "risk_score": 89,
        "outcome": "FRAUD CONFIRMED",
        "customer_profile": "Individual - Personal Banking",
        "transaction_type": "Wire Transfer",
        "timeline": [
            {"time": "Oct 15 - Nov 2", "event": "Normal activity: $50-150/week", "status": "normal"},
            {"time": "Nov 3, 2:30 PM", "event": "Sudden $15,000 wire transfer", "status": "critical"},
            {"time": "Nov 3, 2:31 PM", "event": "System flagged for review", "status": "flagged"},
            {"time": "Nov 3, 2:45 PM", "event": "Analyst rejected transaction", "status": "resolved"}
        ],
        "triggered_rules": [
            {"name": "Transaction Amount Anomalies", "weight": 32, "detail": "18,750% above 30-day average", "severity": "critical"},
            {"name": "Transaction Context Anomalies", "weight": 24, "detail": "No prior wire transfers", "severity": "critical"},
            {"name": "Normalized Transaction Amount", "weight": 18, "detail": "Exceeds 95th percentile for profile", "severity": "high"},
            {"name": "High-Risk Transaction Times", "weight": 9, "detail": "Outside typical banking hours", "severity": "medium"},
            {"name": "Recent High-Value Transaction", "weight": 6, "detail": "First transaction over $1000", "severity": "medium"}
        ],
        "metrics": {
            "Average Transaction": "$87",
            "Current Transaction": "$15,000",
            "Standard Deviation": "172.4σ",
            "Account Age": "4 years",
            "Last Large Transaction": "Never"
        },
        "decision": {
            "recommendation": "REJECT",
            "confidence": 98,
            "reasoning": "Extreme deviation from established pattern with no prior authorization",
            "action": "Contact account holder for verification before release"
        },
        "visualization_data": {
            "amounts": [50, 75, 120, 85, 95, 110, 65, 130, 15000],
            "dates": ["Oct 15", "Oct 18", "Oct 21", "Oct 24", "Oct 27", "Oct 30", "Nov 1", "Nov 2", "Nov 3"]
        }
    },
    "2. Account Takeover": {
        "title": "Account Takeover with Phone/SIM Changes",
        "subtitle": "Credential compromise with device manipulation",
        "risk_score": 96,
        "outcome": "FRAUD PREVENTED",
        "customer_profile": "Individual - Mobile Banking",
        "transaction_type": "Large transfer",
        "timeline": [
            {"time": "Oct 1 - Nov 2", "event": "Normal usage: iPhone 13, Dallas TX", "status": "normal"},
            {"time": "Nov 3, 1:45 AM", "event": "Phone number change request", "status": "warning"},
            {"time": "Nov 3, 2:10 AM", "event": "New device login: Android, Lagos", "status": "critical"},
            {"time": "Nov 3, 2:15 AM", "event": "VPN connection detected", "status": "critical"},
            {"time": "Nov 3, 2:18 AM", "event": "$12,000 transfer attempt - BLOCKED", "status": "blocked"}
        ],
        "triggered_rules": [
            {"name": "Device Fingerprinting", "weight": 30, "detail": "100% device profile change", "severity": "critical"},
            {"name": "VPN or Proxy Usage", "weight": 22, "detail": "Masked IP from Lagos, Nigeria", "severity": "critical"},
            {"name": "Geo-Location Flags", "weight": 20, "detail": "High-risk country access", "severity": "critical"},
            {"name": "Behavioral Biometrics", "weight": 15, "detail": "Typing pattern 87% different", "severity": "high"},
            {"name": "High-Risk Transaction Times", "weight": 9, "detail": "2 AM activity (never before)", "severity": "high"}
        ],
        "metrics": {
            "Device Change": "iPhone → Android",
            "Location Change": "Dallas → Lagos (6,147 mi)",
            "Time Gap": "25 minutes",
            "Typing Speed": "68 wpm → 23 wpm",
            "Phone Number Change": "Yes (1:45 AM)"
        },
        "decision": {
            "recommendation": "AUTO-REJECT",
            "confidence": 99,
            "reasoning": "All indicators of account takeover - SIM swap + credential access",
            "action": "Lock account, require in-person identity verification"
        },
        "visualization_data": {
            "device_comparison": {
                "normal": {"device": "iPhone 13", "location": "Dallas, TX", "vpn": "No", "typing_wpm": 68},
                "suspicious": {"device": "Android 12", "location": "Lagos, Nigeria", "vpn": "Yes", "typing_wpm": 23}
            }
        }
    },
    "3. Money Mule": {
        "title": "Account Used as Money Mule",
        "subtitle": "Rapid in-out transaction pattern indicating money laundering",
        "risk_score": 94,
        "outcome": "FRAUD CONFIRMED",
        "customer_profile": "Individual - New Account",
        "transaction_type": "Multiple in/out transfers",
        "timeline": [
            {"time": "Nov 3, 8:15 AM", "event": "Incoming: $500 from Account A", "status": "warning"},
            {"time": "Nov 3, 8:42 AM", "event": "Incoming: $750 from Account B", "status": "warning"},
            {"time": "Nov 3, 9:10 AM", "event": "Incoming: $1,200 from Account C", "status": "warning"},
            {"time": "Nov 3, 9:55 AM", "event": "Outgoing: $2,380 to offshore account", "status": "critical"},
            {"time": "Nov 3, 10:20 AM", "event": "Incoming: $900 from Account D", "status": "critical"}
        ],
        "triggered_rules": [
            {"name": "Transaction Frequency", "weight": 32, "detail": "5 transactions in 2 hours", "severity": "critical"},
            {"name": "Transaction Context Anomalies", "weight": 28, "detail": "Multiple sources, single destination", "severity": "critical"},
            {"name": "Geo-Location Flags", "weight": 20, "detail": "Outbound to high-risk jurisdiction", "severity": "critical"},
            {"name": "Account Age", "weight": 8, "detail": "Account opened 12 days ago", "severity": "high"},
            {"name": "Social Trust Score", "weight": 6, "detail": "No established relationships", "severity": "medium"}
        ],
        "metrics": {
            "Incoming Transactions": "4",
            "Total Incoming": "$3,350",
            "Outgoing Transactions": "1",
            "Total Outgoing": "$2,380",
            "Retention Rate": "29%",
            "Account Age": "12 days"
        },
        "decision": {
            "recommendation": "REJECT & FREEZE",
            "confidence": 97,
            "reasoning": "Clear money mule behavior - rapid pass-through to offshore account",
            "action": "Freeze account, report to financial crimes unit"
        },
        "visualization_data": {
            "flow": {
                "incoming": [500, 750, 1200, 900],
                "outgoing": [2380],
                "sources": ["Account A", "Account B", "Account C", "Account D"],
                "destination": "Offshore Account"
            }
        }
    }
}


def render():
    """Render the Scenario Analysis page"""

    st.header("🔍 Fraud Scenario Deep Dive")
    st.caption("Detailed analysis of specific fraud detection cases")

    # Scenario selector
    scenario_key = st.selectbox(
        "Select a fraud scenario to analyze:",
        options=list(fraud_scenarios.keys()),
        key='scenario_selector'
    )

    scenario = fraud_scenarios[scenario_key]

    # Risk Score Header with Rule Weight Contribution Bar
    st.markdown(f"### {scenario['title']}")
    st.caption(scenario['subtitle'])

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        # Interactive Rule Weight Contribution Bar
        st.markdown("**Risk Score Breakdown:**")

        total_weight = sum(r['weight'] for r in scenario['triggered_rules'])

        # Create stacked bar
        fig_weight_bar = go.Figure()

        cumulative = 0
        for rule in scenario['triggered_rules']:
            fig_weight_bar.add_trace(go.Bar(
                x=[rule['weight']],
                y=['Risk Score'],
                orientation='h',
                name=rule['name'].split()[0],  # Short name
                text=f"+{rule['weight']}",
                textposition='inside',
                hovertemplate=f"<b>{rule['name']}</b><br>Weight: +{rule['weight']}<br>{rule['detail']}<extra></extra>",
                marker_color='#ef4444' if rule['severity'] == 'critical' else
                             '#f97316' if rule['severity'] == 'high' else
                             '#eab308'
            ))
            cumulative += rule['weight']

        fig_weight_bar.update_layout(
            barmode='stack',
            height=100,
            showlegend=False,
            xaxis=dict(title=f"Total Risk Score: {scenario['risk_score']}/100", range=[0, 100]),
            yaxis=dict(showticklabels=False),
            margin=dict(l=0, r=0, t=0, b=40)
        )

        st.plotly_chart(fig_weight_bar, use_container_width=True)

    with col2:
        risk_color = "🔴" if scenario['risk_score'] >= 90 else "🟠" if scenario['risk_score'] >= 75 else "🟡"
        st.metric("Risk Score", f"{scenario['risk_score']}/100 {risk_color}")
    with col3:
        st.metric("Outcome", scenario['outcome'])

    st.markdown("---")

    # Timeline
    st.markdown("### ⏱️ Detection Timeline")
    timeline_df = pd.DataFrame(scenario['timeline'])

    for idx, row in timeline_df.iterrows():
        status_class = {
            'normal': '🟢', 'warning': '🟡', 'flagged': '🟠', 'critical': '🔴',
            'blocked': '🟣', 'review': '🔵', 'resolved': '⚫'
        }.get(row['status'], '⚪')
        st.markdown(f"{status_class} **{row['time']}** - {row['event']}")

    st.markdown("---")

    # Triggered Rules with hover preview
    st.markdown("### 🚨 Triggered Rules")

    rule_df = pd.DataFrame(scenario['triggered_rules']).sort_values('weight', ascending=True)

    fig_rules = go.Figure()
    fig_rules.add_trace(go.Bar(
        y=rule_df['name'],
        x=rule_df['weight'],
        orientation='h',
        marker=dict(
            color=rule_df['severity'].map({
                'critical': '#ef4444', 'high': '#f97316', 'medium': '#eab308', 'low': '#3b82f6'
            })
        ),
        text=rule_df['weight'],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Weight: +%{x}<br>%{customdata}<extra></extra>',
        customdata=rule_df['detail']
    ))

    fig_rules.update_layout(
        title="Rule Weight Contribution",
        xaxis_title="Risk Points Added",
        height=400
    )

    st.plotly_chart(fig_rules, use_container_width=True)

    # Metrics
    st.markdown("### 📈 Key Detection Metrics")
    metrics_cols = st.columns(len(scenario['metrics']))
    for idx, (key, value) in enumerate(scenario['metrics'].items()):
        with metrics_cols[idx]:
            st.metric(key, value)

    # Decision
    st.markdown("---")
    st.markdown("### 🎯 Analyst Decision")

    decision_col1, decision_col2 = st.columns([2, 1])

    with decision_col1:
        st.markdown(f"**Recommendation:** `{scenario['decision']['recommendation']}`")
        st.markdown(f"**Confidence Level:** {scenario['decision']['confidence']}%")
        st.markdown(f"**Reasoning:** {scenario['decision']['reasoning']}")
        st.markdown(f"**Action:** {scenario['decision']['action']}")

    with decision_col2:
        if st.button("🔴 REJECT", key=f"reject_{scenario_key}"):
            st.error("Transaction rejected")
        if st.button("🟡 ESCALATE", key=f"escalate_{scenario_key}"):
            st.warning("Case escalated")
        if st.button("🟢 CLEAR", key=f"clear_{scenario_key}"):
            st.success("Transaction cleared")

    st.markdown("---")
    st.caption(f"💡 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | **Note:** Scenario examples for training and demonstration")
