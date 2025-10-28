"""
Risk Analytics Page

Comprehensive fraud analytics with time-series trends, risk distributions,
money saved calculations, and module performance metrics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, Any, List

from streamlit_app.api_client import get_api_client


def format_currency(amount):
    """Format amount as currency"""
    return f"${amount:,.2f}"


def format_number(num):
    """Format large numbers with K/M suffixes"""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(int(num))


def render_kpi_cards(money_saved: Dict[str, Any], overview: Dict[str, Any]):
    """Render top KPI cards"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Money Saved",
            format_currency(money_saved.get("total_amount_saved", 0)),
            help="Total amount of fraudulent transactions prevented"
        )

    with col2:
        st.metric(
            "Prevented Fraud",
            money_saved.get("prevented_fraud_count", 0),
            help="Number of high-risk transactions caught"
        )

    with col3:
        st.metric(
            "Blocked Transactions",
            money_saved.get("blocked_transaction_count", 0),
            help="Transactions explicitly rejected"
        )

    with col4:
        review_rate = overview.get("review_rate", 0) * 100
        st.metric(
            "Review Rate",
            f"{review_rate:.1f}%",
            help="Percentage of transactions requiring manual review"
        )


def render_time_series_chart(time_series_data: Dict[str, Any]):
    """Render time-series trend chart"""
    if not time_series_data or not time_series_data.get("data"):
        st.info("No time-series data available for this period")
        return

    df = pd.DataFrame(time_series_data["data"])

    if df.empty:
        st.info("No transactions in this time period")
        return

    # Create dual-axis chart
    fig = go.Figure()

    # Add transaction count bars
    fig.add_trace(go.Bar(
        x=df["timestamp"],
        y=df["count"],
        name="Transaction Count",
        marker_color='lightblue',
        yaxis='y',
        opacity=0.7
    ))

    # Add average risk score line
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["avg_risk"],
        name="Avg Risk Score",
        line=dict(color='red', width=3),
        yaxis='y2'
    ))

    # Add high risk count line
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["high_risk_count"],
        name="High Risk Count",
        line=dict(color='orange', width=2, dash='dash'),
        yaxis='y'
    ))

    # Update layout with dual y-axes
    fig.update_layout(
        title="Fraud Activity Over Time",
        xaxis=dict(title="Time"),
        yaxis=dict(
            title="Transaction Count",
            side='left'
        ),
        yaxis2=dict(
            title="Average Risk Score",
            overlaying='y',
            side='right',
            range=[0, 1]
        ),
        hovermode='x unified',
        height=400,
        showlegend=True,
        legend=dict(x=0, y=1.1, orientation='h')
    )

    st.plotly_chart(fig, use_container_width=True)


def render_risk_distribution(risk_dist: Dict[str, Any]):
    """Render risk score distribution histogram"""
    if not risk_dist or not risk_dist.get("risk_scores"):
        st.info("No risk data available")
        return

    risk_scores = risk_dist["risk_scores"]

    # Create histogram
    fig = px.histogram(
        risk_scores,
        nbins=20,
        title="Risk Score Distribution",
        labels={"value": "Risk Score", "count": "Frequency"},
        color_discrete_sequence=['#1f77b4']
    )

    # Add vertical lines for thresholds
    fig.add_vline(x=0.3, line_dash="dash", line_color="green",
                  annotation_text="Low Risk Threshold")
    fig.add_vline(x=0.6, line_dash="dash", line_color="orange",
                  annotation_text="High Risk Threshold")

    # Add stats as annotations
    avg_risk = risk_dist.get("avg_risk", 0)
    fig.add_annotation(
        text=f"Average: {avg_risk:.3f}",
        xref="paper", yref="paper",
        x=0.95, y=0.95,
        showarrow=False,
        bgcolor="white",
        bordercolor="black",
        borderwidth=1
    )

    fig.update_layout(
        height=400,
        showlegend=False,
        xaxis_title="Risk Score",
        yaxis_title="Number of Transactions"
    )

    st.plotly_chart(fig, use_container_width=True)


def render_decision_breakdown(time_series_data: Dict[str, Any]):
    """Render pie chart of decision types"""
    if not time_series_data or not time_series_data.get("data"):
        return

    df = pd.DataFrame(time_series_data["data"])

    if df.empty:
        return

    # Sum up decision counts
    total_auto_approve = df["auto_approve_count"].sum()
    total_manual_review = df["manual_review_count"].sum()

    decision_data = pd.DataFrame({
        "Decision": ["Auto-Approved", "Manual Review"],
        "Count": [total_auto_approve, total_manual_review]
    })

    fig = px.pie(
        decision_data,
        values="Count",
        names="Decision",
        title="Transaction Decisions",
        color="Decision",
        color_discrete_map={
            "Auto-Approved": "#90EE90",
            "Manual Review": "#FFB6C1"
        }
    )

    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)


def render_module_performance(module_perf: Dict[str, Any]):
    """Render fraud detection module performance table and chart"""
    if not module_perf or not module_perf.get("modules"):
        st.info("No module performance data available")
        return

    modules = module_perf["modules"]

    # Sort by trigger count
    sorted_modules = sorted(modules, key=lambda x: x["trigger_count"], reverse=True)

    # Top 15 modules for chart
    top_modules = sorted_modules[:15]

    # Create horizontal bar chart
    module_names = [m["description"][:50] + "..." if len(m["description"]) > 50
                    else m["description"] for m in top_modules]
    trigger_counts = [m["trigger_count"] for m in top_modules]

    fig = go.Figure(go.Bar(
        x=trigger_counts,
        y=module_names,
        orientation='h',
        marker=dict(
            color=trigger_counts,
            colorscale='Reds',
            showscale=True,
            colorbar=dict(title="Triggers")
        )
    ))

    fig.update_layout(
        title="Top 15 Fraud Detection Modules by Trigger Count",
        xaxis_title="Number of Triggers",
        yaxis_title="Module",
        height=500,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # Detailed table
    with st.expander("📋 View Detailed Module Statistics"):
        df = pd.DataFrame(sorted_modules)

        # Select columns to display
        display_df = df[["description", "trigger_count", "avg_weight",
                        "high_risk_triggers", "confirmed_fraud", "precision"]]

        display_df.columns = ["Module", "Triggers", "Avg Weight",
                             "High Risk", "Confirmed Fraud", "Precision"]

        # Format precision as percentage
        display_df["Precision"] = display_df["Precision"].apply(lambda x: f"{x*100:.1f}%")

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )


def render_scenario_breakdown(scenarios: Dict[str, Any]):
    """Render fraud scenario breakdown"""
    if not scenarios:
        return

    scenario_data = []
    for name, data in scenarios.items():
        if data['count'] > 0:
            scenario_data.append({
                'Scenario': name.replace('_', ' ').title(),
                'Count': data['count'],
                'Avg Risk': data['avg_risk'],
                'High Risk': data['high_risk']
            })

    if not scenario_data:
        st.info("No scenario data available")
        return

    df = pd.DataFrame(scenario_data)

    # Bar chart
    fig = px.bar(
        df,
        x="Scenario",
        y="Count",
        title="Fraud Activity by Scenario Type",
        color="Avg Risk",
        color_continuous_scale="Reds"
    )

    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)


def render():
    """Render the Risk Analytics page"""

    # Header
    st.markdown("# 📊 Risk Analytics")
    st.markdown("Comprehensive fraud detection analytics and trends")

    # Time range selector
    col1, col2, col3 = st.columns([2, 1, 1])

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
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

    with col3:
        st.markdown("")  # Spacing

    st.divider()

    # Fetch data
    client = get_api_client()

    try:
        with st.spinner("Loading analytics data..."):
            # Parallel data fetching
            money_saved = client.get_money_saved(time_range)
            overview = client.get_overview_stats(
                {"1h": 1, "24h": 24, "7d": 168, "30d": 720}[time_range]
            )
            time_series = client.get_time_series_metrics(time_range)
            risk_dist = client.get_risk_distribution(time_range)
            module_perf = client.get_module_performance(time_range)
            scenarios = client.get_scenario_breakdown(
                {"1h": 1, "24h": 24, "7d": 168, "30d": 720}[time_range]
            )

        # Display timestamp
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # KPI Cards
        st.markdown("### 💰 Key Performance Indicators")
        render_kpi_cards(money_saved, overview)

        st.divider()

        # Time series and distribution
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📈 Fraud Trends")
            render_time_series_chart(time_series)

        with col2:
            st.markdown("### 📊 Risk Distribution")
            render_risk_distribution(risk_dist)

        st.divider()

        # Decision breakdown and scenarios
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### ⚖️ Decision Breakdown")
            render_decision_breakdown(time_series)

        with col2:
            st.markdown("### 🎯 Scenario Breakdown")
            render_scenario_breakdown(scenarios)

        st.divider()

        # Module performance
        st.markdown("### 🔍 Fraud Detection Module Performance")
        st.markdown("**Analysis of your 25 fraud detection modules**")
        render_module_performance(module_perf)

        # Additional insights
        st.divider()
        st.markdown("### 💡 Insights")

        insight_col1, insight_col2, insight_col3 = st.columns(3)

        with insight_col1:
            if money_saved.get("prevented_fraud_count", 0) > 0:
                avg_fraud_value = money_saved["total_amount_saved"] / money_saved["prevented_fraud_count"]
                st.info(f"**Average Fraud Value:** {format_currency(avg_fraud_value)}")
            else:
                st.info("**Average Fraud Value:** N/A")

        with insight_col2:
            if overview.get("total_transactions", 0) > 0:
                fraud_rate = (money_saved.get("high_risk_flagged", 0) / overview["total_transactions"]) * 100
                st.warning(f"**Fraud Detection Rate:** {fraud_rate:.2f}%")
            else:
                st.warning("**Fraud Detection Rate:** N/A")

        with insight_col3:
            total_modules = module_perf.get("total_modules", 0)
            st.success(f"**Active Modules:** {total_modules} / 25")

    except Exception as e:
        st.error(f"❌ Error loading analytics: {str(e)}")
        st.exception(e)


if __name__ == "__main__" or True:
    render()
