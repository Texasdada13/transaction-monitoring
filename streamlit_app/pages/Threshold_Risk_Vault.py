"""
Limit Violation Alerts Page

Monitor and manage account limit violations with detailed analysis.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, Any, List, Optional

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


def get_severity_color(severity: str) -> str:
    """Get color for severity level"""
    colors = {
        "critical": "#DC143C",
        "high": "#FF8C00",
        "medium": "#FFD700",
        "low": "#90EE90"
    }
    return colors.get(severity, "#808080")


def get_severity_emoji(severity: str) -> str:
    """Get emoji for severity level"""
    emojis = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢"
    }
    return emojis.get(severity, "⚪")


def render_violation_stats(violation_data: Dict[str, Any]):
    """Render violation statistics"""
    col1, col2, col3, col4 = st.columns(4)

    severity_breakdown = violation_data.get("severity_breakdown", {})

    with col1:
        st.metric(
            "Total Violations",
            violation_data.get("total_violations", 0)
        )

    with col2:
        st.metric(
            "Critical",
            severity_breakdown.get("critical", 0),
            delta_color="inverse"
        )

    with col3:
        st.metric(
            "High",
            severity_breakdown.get("high", 0),
            delta_color="inverse"
        )

    with col4:
        st.metric(
            "Violation Amount",
            format_currency(violation_data.get("total_violation_amount", 0))
        )


def render_severity_distribution(violation_data: Dict[str, Any]):
    """Render severity level distribution"""
    severity_breakdown = violation_data.get("severity_breakdown", {})

    if not severity_breakdown or sum(severity_breakdown.values()) == 0:
        st.info("No violations found")
        return

    # Create pie chart
    labels = []
    values = []
    colors = []

    for severity in ["critical", "high", "medium", "low"]:
        count = severity_breakdown.get(severity, 0)
        if count > 0:
            labels.append(f"{severity.title()} ({count})")
            values.append(count)
            colors.append(get_severity_color(severity))

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.3,
        textinfo='label+percent'
    )])

    fig.update_layout(
        title="Violations by Severity Level",
        height=300
    )

    st.plotly_chart(fig, use_container_width=True)


def render_violation_type_breakdown(violation_data: Dict[str, Any]):
    """Render breakdown by violation type"""
    violations = violation_data.get("violations", [])

    if not violations:
        return

    # Count by type
    type_counts = {}
    for v in violations:
        vtype = v["violation"]["type"]
        if vtype not in type_counts:
            type_counts[vtype] = 0
        type_counts[vtype] += 1

    # Create bar chart
    df = pd.DataFrame([
        {"Type": vtype.replace("_", " ").title(), "Count": count}
        for vtype, count in type_counts.items()
    ])

    fig = px.bar(
        df,
        x="Type",
        y="Count",
        title="Violations by Type",
        color="Count",
        color_continuous_scale="Reds"
    )

    fig.update_layout(height=300, showlegend=False)

    st.plotly_chart(fig, use_container_width=True)


def render_violation_timeline(violation_data: Dict[str, Any]):
    """Render violation timeline"""
    violations = violation_data.get("violations", [])

    if not violations:
        return

    df = pd.DataFrame(violations)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')

    # Group by hour
    df['hour'] = df['timestamp'].dt.floor('H')
    hourly = df.groupby(['hour', 'severity']).size().reset_index(name='count')

    # Create stacked bar chart
    fig = px.bar(
        hourly,
        x='hour',
        y='count',
        color='severity',
        title="Violation Timeline by Severity",
        color_discrete_map={
            "critical": get_severity_color("critical"),
            "high": get_severity_color("high"),
            "medium": get_severity_color("medium"),
            "low": get_severity_color("low")
        },
        labels={
            "hour": "Time",
            "count": "Number of Violations",
            "severity": "Severity"
        }
    )

    fig.update_layout(height=350)

    st.plotly_chart(fig, use_container_width=True)


def render_violation_alerts(violation_data: Dict[str, Any], limit: int = 50):
    """Render violation alert cards"""
    violations = violation_data.get("violations", [])[:limit]

    if not violations:
        st.success("✅ No limit violations detected. All accounts are within their limits!")
        return

    st.markdown(f"### 🚨 Active Violation Alerts ({len(violations)})")

    for idx, violation in enumerate(violations):
        severity = violation["severity"]
        violation_info = violation["violation"]

        # Color code by severity
        border_color = get_severity_color(severity)
        severity_badge = f"{get_severity_emoji(severity)} {severity.upper()}"

        with st.container():
            # Create colored border effect
            st.markdown(f"""
            <div style="border-left: 4px solid {border_color}; padding-left: 10px; margin-bottom: 10px;">
            """, unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

            with col1:
                st.markdown(f"**{violation['violation_id']}**")
                st.caption(f"Transaction: {violation['transaction_id']}")

            with col2:
                st.markdown(f"**Account:** {violation['account_id']}")
                st.caption(format_timestamp(violation['timestamp']))

            with col3:
                st.markdown(f"**Type:** {violation_info['type'].replace('_', ' ').title()}")
                st.caption(f"Severity: {severity_badge}")

            with col4:
                st.markdown(f"**Excess:** {format_currency(violation_info['excess'])}")
                st.caption(f"Risk Score: {violation['risk_score']:.3f}")

            st.markdown("</div>", unsafe_allow_html=True)

            # Show details in expander
            with st.expander("📋 Violation Details"):
                col_a, col_b = st.columns(2)

                with col_a:
                    st.markdown("**Limit Information:**")
                    st.markdown(f"- **Limit:** {format_currency(violation_info['limit'])}")
                    st.markdown(f"- **Actual:** {format_currency(violation_info['actual'])}")
                    st.markdown(f"- **Excess:** {format_currency(violation_info['excess'])}")
                    excess_pct = (violation_info['excess'] / violation_info['limit']) * 100
                    st.markdown(f"- **Over Limit By:** {excess_pct:.1f}%")

                with col_b:
                    st.markdown("**Risk Assessment:**")
                    st.markdown(f"- **Risk Score:** {violation['risk_score']:.3f}")
                    st.markdown(f"- **Review Status:** {violation['review_status']}")
                    st.markdown(f"- **Violation Type:** {violation_info['type']}")

                # Action buttons
                st.markdown("**Actions:**")
                col_btn1, col_btn2, col_btn3 = st.columns(3)

                with col_btn1:
                    if st.button("✅ Approve Exception", key=f"approve_{idx}"):
                        st.success(f"Exception approved for {violation['violation_id']}")

                with col_btn2:
                    if st.button("❌ Reject", key=f"reject_{idx}"):
                        st.error(f"Transaction rejected: {violation['violation_id']}")

                with col_btn3:
                    if st.button("🔍 Investigate", key=f"investigate_{idx}"):
                        st.info(f"Opening investigation for {violation['account_id']}")

            st.divider()


def render_top_violating_accounts(violation_data: Dict[str, Any]):
    """Render table of accounts with most violations"""
    violations = violation_data.get("violations", [])

    if not violations:
        return

    # Count by account
    account_violations = {}
    for v in violations:
        account_id = v["account_id"]
        if account_id not in account_violations:
            account_violations[account_id] = {
                "account_id": account_id,
                "violation_count": 0,
                "total_excess": 0,
                "max_severity": "low",
                "critical_count": 0,
                "high_count": 0
            }

        account_violations[account_id]["violation_count"] += 1
        account_violations[account_id]["total_excess"] += v["violation"]["excess"]

        # Track severity
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        current_severity = severity_order.get(v["severity"], 0)
        max_severity = severity_order.get(account_violations[account_id]["max_severity"], 0)

        if current_severity > max_severity:
            account_violations[account_id]["max_severity"] = v["severity"]

        if v["severity"] == "critical":
            account_violations[account_id]["critical_count"] += 1
        elif v["severity"] == "high":
            account_violations[account_id]["high_count"] += 1

    # Sort by violation count
    sorted_accounts = sorted(
        account_violations.values(),
        key=lambda x: x["violation_count"],
        reverse=True
    )[:20]

    df = pd.DataFrame(sorted_accounts)

    # Format display
    display_df = df.copy()
    display_df["total_excess"] = display_df["total_excess"].apply(format_currency)
    display_df["max_severity"] = display_df["max_severity"].str.title()

    display_df.columns = [
        "Account ID", "Total Violations", "Total Excess Amount",
        "Highest Severity", "Critical", "High"
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


def render():
    """Render the Limit Violation Alerts page"""

    # Header
    st.markdown("# Limit Monitoring & Breach Alerts")
    st.markdown("Real-Time Surveillance of Account Threshold Breaches and High-Risk Spikes")

    # Configuration
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        time_range = st.selectbox(
            "Time Range",
            ["1h", "24h", "7d", "30d"],
            index=1,
            format_func=lambda x: {
                "1h": "Last Hour",
                "24h": "Last 24 Hours",
                "7d": "Last 7 Days",
                "30d": "Last 30 Days"
            }[x]
        )

    with col2:
        severity_filter = st.selectbox(
            "Severity Filter",
            [None, "critical", "high", "medium", "low"],
            format_func=lambda x: "All" if x is None else x.title()
        )

    with col3:
        limit = st.number_input(
            "Max Results",
            min_value=10,
            max_value=500,
            value=100,
            step=10
        )

    with col4:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    st.divider()

    # Fetch data
    client = get_api_client()

    try:
        with st.spinner("Loading violation data..."):
            violation_data = client.get_limit_violations(
                time_range=time_range,
                severity=severity_filter,
                limit=limit
            )

        # Display timestamp
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Overview statistics
        st.markdown("### Breach Summary Statistics")
        render_violation_stats(violation_data)

        st.divider()

        # Charts row
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Violation Spectrum")
            render_severity_distribution(violation_data)

        with col2:
            st.markdown("### Categorized Breachs")
            render_violation_type_breakdown(violation_data)

        st.divider()

        # Timeline
        st.markdown("### Chronology & Spike Detection")
        render_violation_timeline(violation_data)

        st.divider()

        # Violation alerts
        render_violation_alerts(violation_data, limit=50)

        # Top violating accounts
        st.divider()
        with st.expander("📊 View Top Violating Accounts"):
            st.markdown("### Accounts with Most Violations")
            render_top_violating_accounts(violation_data)

        # Insights
        st.divider()
        st.markdown("### Breach Intelligence & Predictive Signals")

        violations = violation_data.get("violations", [])
        severity_breakdown = violation_data.get("severity_breakdown", {})

        if violations:
            col1, col2, col3 = st.columns(3)

            with col1:
                critical_count = severity_breakdown.get("critical", 0)
                if critical_count > 0:
                    st.error(f"**Critical Violations:**\n\n{critical_count} alerts\n\nImmediate action required")
                else:
                    st.success("**No Critical Violations**\n\nAll accounts within limits")

            with col2:
                total_excess = violation_data.get("total_violation_amount", 0)
                st.warning(f"**Total Excess Amount:**\n\n{format_currency(total_excess)}\n\nOver established limits")

            with col3:
                total_violations = len(violations)
                high_severity = severity_breakdown.get("critical", 0) + severity_breakdown.get("high", 0)
                high_pct = (high_severity / total_violations * 100) if total_violations > 0 else 0
                st.info(f"**High-Severity Rate:**\n\n{high_pct:.1f}%\n\nOf all violations")

    except Exception as e:
        st.error(f"❌ Error loading violation data: {str(e)}")
        st.exception(e)


if __name__ == "__main__" or True:
    render()
