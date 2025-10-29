"""
Real-Time Monitoring Page

Live fraud alert monitoring with auto-refresh capability.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

from streamlit_app.api_client import get_api_client
from styles.theme import apply_theme, COLORS

# Apply theme
apply_theme()

def format_currency(amount):
    """Format amount as currency"""
    return f"${amount:,.2f}"


def format_timestamp(timestamp_str):
    """Format ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str


def render_metric_card(label, value, delta=None, delta_color="normal"):
    """Render a metric card"""
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)


def render_overview_stats(stats):
    """Render overview statistics cards"""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        render_metric_card(
            "Total Transactions",
            f"{stats['total_transactions']:,}",
        )

    with col2:
        render_metric_card(
            "Total Value",
            format_currency(stats['total_value']),
        )

    with col3:
        approval_rate = (stats['auto_approved'] / max(stats['total_transactions'], 1)) * 100
        render_metric_card(
            "Auto-Approved",
            f"{stats['auto_approved']:,}",
            f"{approval_rate:.1f}%"
        )

    with col4:
        render_metric_card(
            "Manual Review",
            f"{stats['manual_review']:,}",
            f"{stats['review_rate']*100:.1f}%",
            delta_color="inverse"
        )

    with col5:
        render_metric_card(
            "Avg Risk Score",
            f"{stats['average_risk_score']:.2f}",
        )


def render_risk_score_gauge(risk_score):
    """Render risk score as a gauge chart"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, 1]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 0.3], 'color': "lightgreen"},
                {'range': [0.3, 0.6], 'color': "yellow"},
                {'range': [0.6, 1], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 0.6
            }
        }
    ))

    fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
    return fig


def render_alert_queue(alerts):
    """Render the alert queue table"""
    if not alerts:
        st.info("✅ No pending alerts. All transactions processed!")
        return

    st.markdown(f"### 🚨 Active Alerts ({len(alerts)})")

    # Convert to DataFrame
    df_data = []
    for alert in alerts:
        df_data.append({
            "Assessment ID": alert['assessment_id'],
            "Transaction ID": alert['transaction_id'],
            "Amount": alert['amount'],
            "Type": alert['transaction_type'],
            "Risk Score": alert['risk_score'],
            "Rules Triggered": len(alert['triggered_rules']),
            "Timestamp": alert['timestamp']
        })

    df = pd.DataFrame(df_data)

    # Display with formatting
    for idx, alert in enumerate(alerts[:20]):  # Show top 20
        risk_score = alert['risk_score']

        # Color code by risk level
        if risk_score >= 0.8:
            card_class = "alert-high"
            risk_level = "🔴 CRITICAL"
        elif risk_score >= 0.6:
            card_class = "alert-medium"
            risk_level = "🟡 HIGH"
        else:
            card_class = "alert-low"
            risk_level = "🟢 MEDIUM"

        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 3])

            with col1:
                st.markdown(f"**{alert['transaction_id']}**")
                st.caption(format_timestamp(alert['timestamp']))

            with col2:
                st.markdown(f"**Amount:** {format_currency(alert['amount'])}")
                st.caption(f"Type: {alert['transaction_type']}")

            with col3:
                st.markdown(f"**Risk:** {risk_score:.2f} {risk_level}")
                st.caption(f"{len(alert['triggered_rules'])} rules triggered")

            with col4:
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button("✅ Approve", key=f"approve_{idx}"):
                        st.success(f"Approved {alert['transaction_id']}")
                with col_b:
                    if st.button("❌ Reject", key=f"reject_{idx}"):
                        st.error(f"Rejected {alert['transaction_id']}")
                with col_c:
                    if st.button("🔍 Details", key=f"details_{idx}"):
                        show_transaction_details(alert)

            st.divider()


def show_transaction_details(alert):
    """Show detailed transaction information in modal"""
    with st.expander("📋 Transaction Details", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Transaction Info")
            st.markdown(f"**ID:** {alert['transaction_id']}")
            st.markdown(f"**Amount:** {format_currency(alert['amount'])}")
            st.markdown(f"**Type:** {alert['transaction_type']}")
            st.markdown(f"**Time:** {format_timestamp(alert['timestamp'])}")

        with col2:
            st.markdown("#### Risk Assessment")
            st.markdown(f"**Risk Score:** {alert['risk_score']:.2f}")
            st.markdown(f"**Assessment ID:** {alert['assessment_id']}")

        st.markdown("#### Triggered Rules")
        for rule in alert['triggered_rules']:
            st.markdown(f"- {rule}")


def render_top_rules(rules):
    """Render top triggered rules chart"""
    if not rules:
        st.info("No rules triggered in this time period")
        return

    # Prepare data
    rule_names = [rule['description'][:50] + "..." if len(rule['description']) > 50 else rule['description'] for rule in rules[:10]]
    counts = [rule['count'] for rule in rules[:10]]

    # Create bar chart
    fig = px.bar(
        x=counts,
        y=rule_names,
        orientation='h',
        labels={'x': 'Trigger Count', 'y': 'Rule'},
        title='Top 10 Triggered Fraud Detection Rules'
    )

    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def render_scenario_breakdown(scenarios):
    """Render fraud scenario breakdown"""
    if not scenarios:
        st.info("No scenario data available")
        return

    # Prepare data for pie chart
    scenario_data = []
    for name, data in scenarios.items():
        if data['count'] > 0:
            scenario_data.append({
                'Scenario': name.replace('_', ' ').title(),
                'Count': data['count'],
                'Avg Risk': data['avg_risk']
            })

    if not scenario_data:
        st.info("No fraud scenarios triggered")
        return

    df = pd.DataFrame(scenario_data)

    # Pie chart
    fig = px.pie(
        df,
        values='Count',
        names='Scenario',
        title='Fraud Activity by Scenario Type'
    )

    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)


def render():
    """Render the Real-Time Monitoring page"""

    from PIL import Image

   
    # Header
    st.markdown("# Arriba Advisors")

    # Control bar
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        st.markdown("### Live Dashboard")

    with col2:
        auto_refresh = st.toggle("Auto-refresh", value=False, key="auto_refresh_toggle")

    with col3:
        if auto_refresh:
            refresh_interval = st.selectbox("Interval (sec)", [30, 60, 90], key="refresh_interval")
        else:
            refresh_interval = 60

    with col4:
        time_window = st.selectbox("Time Window", [1, 6, 12, 24], format_func=lambda x: f"{x}h", key="time_window")

    st.divider()

    # Create placeholder for dynamic content
    main_placeholder = st.empty()

    # Auto-refresh logic
    if auto_refresh:
        while auto_refresh:
            with main_placeholder.container():
                render_dashboard_content(time_window)

            # Sleep and check if auto-refresh is still enabled
            time.sleep(refresh_interval)

            # Check if toggle was turned off
            if not st.session_state.get("auto_refresh_toggle", False):
                break

            st.rerun()
    else:
        with main_placeholder.container():
            render_dashboard_content(time_window)


def render_dashboard_content(time_window):
    """Render the main dashboard content"""
    client = get_api_client()

    try:
        # Fetch data
        with st.spinner("Loading dashboard data..."):
            stats = client.get_overview_stats(time_window)
            alerts = client.get_live_alerts(limit=100)
            top_rules = client.get_top_triggered_rules(limit=10)
            scenarios = client.get_scenario_breakdown(time_window)

        # Last updated timestamp
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Overview stats
        st.markdown("### Overview Statistics")
        render_overview_stats(stats)

        st.divider()

        # Alert queue and charts
        col1, col2 = st.columns([2, 1])

        with col1:
            # Alert queue
            render_alert_queue(alerts)

        with col2:
            # Top rules
            st.markdown("### 📌 Top Rules")
            render_top_rules(top_rules)

            # Scenario breakdown
            st.markdown("### 🎯 Activity Breakdown")
            render_scenario_breakdown(scenarios)

    except Exception as e:
        st.error(f"❌ Error loading dashboard: {str(e)}")
        st.exception(e)
