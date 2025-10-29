"""
High-Value Transaction Monitoring Page

Specialized monitoring for large-value transactions with enhanced risk analysis.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, Any, List

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


def render_high_value_stats(hv_data: Dict[str, Any]):
    """Render high-value transaction statistics"""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "High-Value Transactions",
            hv_data.get("total_transactions", 0)
        )

    with col2:
        st.metric(
            "Total Amount",
            format_currency(hv_data.get("total_amount", 0))
        )

    with col3:
        st.metric(
            "Flagged Amount",
            format_currency(hv_data.get("flagged_amount", 0)),
            f"{(hv_data.get('flagged_amount', 0) / max(hv_data.get('total_amount', 1), 1) * 100):.1f}%"
        )

    with col4:
        st.metric(
            "High-Risk Count",
            hv_data.get("high_risk_count", 0),
            f"{(hv_data.get('high_risk_rate', 0) * 100):.1f}%",
            delta_color="inverse"
        )

    with col5:
        avg_amount = hv_data.get("total_amount", 0) / max(hv_data.get("total_transactions", 1), 1)
        st.metric(
            "Avg Transaction",
            format_currency(avg_amount)
        )


def render_amount_distribution(hv_data: Dict[str, Any]):
    """Render transaction amount distribution"""
    transactions = hv_data.get("transactions", [])

    if not transactions:
        st.info("No high-value transactions in this period")
        return

    amounts = [tx["amount"] for tx in transactions]

    # Create histogram
    fig = px.histogram(
        amounts,
        nbins=30,
        title="High-Value Transaction Amount Distribution",
        labels={"value": "Transaction Amount", "count": "Frequency"},
        color_discrete_sequence=['#1f77b4']
    )

    # Add statistics annotations
    avg_amount = sum(amounts) / len(amounts)
    max_amount = max(amounts)

    fig.add_vline(x=avg_amount, line_dash="dash", line_color="green",
                  annotation_text=f"Average: {format_currency(avg_amount)}")

    fig.add_annotation(
        text=f"Max: {format_currency(max_amount)}",
        xref="paper", yref="paper",
        x=0.95, y=0.95,
        showarrow=False,
        bgcolor="white",
        bordercolor="black",
        borderwidth=1
    )

    fig.update_layout(
        height=350,
        showlegend=False,
        xaxis_title="Transaction Amount ($)",
        yaxis_title="Number of Transactions"
    )

    st.plotly_chart(fig, use_container_width=True)


def render_risk_vs_amount_scatter(hv_data: Dict[str, Any]):
    """Render scatter plot of risk score vs amount"""
    transactions = hv_data.get("transactions", [])

    if not transactions:
        return

    df = pd.DataFrame(transactions)

    # Color by risk level
    df["risk_level"] = df["risk_score"].apply(
        lambda x: "Critical" if x >= 0.8 else "High" if x >= 0.6 else "Medium"
    )

    fig = px.scatter(
        df,
        x="amount",
        y="risk_score",
        color="risk_level",
        hover_name="transaction_id",
        hover_data={
            "amount": ":,.0f",
            "risk_score": ":.3f",
            "transaction_type": True,
            "review_status": True
        },
        color_discrete_map={
            "Critical": "#DC143C",
            "High": "#FF8C00",
            "Medium": "#FFD700"
        },
        title="Risk Score vs Transaction Amount",
        labels={
            "amount": "Transaction Amount ($)",
            "risk_score": "Risk Score",
            "risk_level": "Risk Level"
        }
    )

    # Add risk threshold lines
    fig.add_hline(y=0.6, line_dash="dash", line_color="orange",
                  annotation_text="High Risk Threshold")
    fig.add_hline(y=0.8, line_dash="dash", line_color="red",
                  annotation_text="Critical Risk Threshold")

    fig.update_layout(height=400)

    st.plotly_chart(fig, use_container_width=True)


def render_top_transactions_table(hv_data: Dict[str, Any], limit: int = 20):
    """Render table of top high-value transactions"""
    transactions = hv_data.get("transactions", [])[:limit]

    if not transactions:
        st.info("No high-value transactions found")
        return

    st.markdown(f"### 💰 Top {limit} High-Value Transactions")

    for idx, tx in enumerate(transactions):
        risk_score = tx["risk_score"]

        # Color code by risk level
        if risk_score >= 0.8:
            card_class = "critical"
            risk_badge = "🔴 CRITICAL"
            border_color = "#DC143C"
        elif risk_score >= 0.6:
            card_class = "high"
            risk_badge = "🟠 HIGH"
            border_color = "#FF8C00"
        else:
            card_class = "medium"
            risk_badge = "🟡 MEDIUM"
            border_color = "#FFD700"

        with st.container():
            # Create colored border effect
            st.markdown(f"""
            <div style="border-left: 4px solid {border_color}; padding-left: 10px; margin-bottom: 10px;">
            """, unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

            with col1:
                st.markdown(f"**{tx['transaction_id']}**")
                st.caption(format_timestamp(tx['timestamp']))

            with col2:
                st.markdown(f"**Amount:** {format_currency(tx['amount'])}")
                st.caption(f"Type: {tx['transaction_type']}")

            with col3:
                st.markdown(f"**Risk:** {risk_score:.3f} {risk_badge}")
                st.caption(f"Status: {tx['review_status']}")

            with col4:
                st.markdown(f"**Account:** {tx['account_id']}")
                st.caption(f"{len(tx['triggered_rules'])} rules triggered")

            st.markdown("</div>", unsafe_allow_html=True)

            # Show triggered rules in expander
            if tx['triggered_rules']:
                with st.expander(f"View Rules ({len(tx['triggered_rules'])})"):
                    for rule in tx['triggered_rules']:
                        st.markdown(f"- {rule}")

            st.divider()


def render_transaction_type_breakdown(hv_data: Dict[str, Any]):
    """Render breakdown by transaction type"""
    transactions = hv_data.get("transactions", [])

    if not transactions:
        return

    # Count by type
    type_data = {}
    for tx in transactions:
        tx_type = tx["transaction_type"]
        if tx_type not in type_data:
            type_data[tx_type] = {"count": 0, "total_amount": 0, "high_risk": 0}

        type_data[tx_type]["count"] += 1
        type_data[tx_type]["total_amount"] += tx["amount"]
        if tx["is_high_risk"]:
            type_data[tx_type]["high_risk"] += 1

    # Create bar chart
    df = pd.DataFrame([
        {
            "Type": tx_type,
            "Count": data["count"],
            "Total Amount": data["total_amount"],
            "High Risk Count": data["high_risk"]
        }
        for tx_type, data in type_data.items()
    ])

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["Type"],
        y=df["Count"],
        name="Total Transactions",
        marker_color='lightblue',
        text=df["Count"],
        textposition="auto"
    ))

    fig.add_trace(go.Bar(
        x=df["Type"],
        y=df["High Risk Count"],
        name="High Risk",
        marker_color='red',
        text=df["High Risk Count"],
        textposition="auto"
    ))

    fig.update_layout(
        title="High-Value Transactions by Type",
        xaxis_title="Transaction Type",
        yaxis_title="Count",
        height=350,
        barmode='group'
    )

    st.plotly_chart(fig, use_container_width=True)


def render_time_series(hv_data: Dict[str, Any]):
    """Render time series of high-value transactions"""
    transactions = hv_data.get("transactions", [])

    if not transactions:
        return

    df = pd.DataFrame(transactions)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')

    # Group by hour
    df['hour'] = df['timestamp'].dt.floor('H')
    hourly = df.groupby('hour').agg({
        'amount': ['sum', 'count'],
        'risk_score': 'mean'
    }).reset_index()

    hourly.columns = ['hour', 'total_amount', 'count', 'avg_risk']

    # Create dual-axis chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=hourly['hour'],
        y=hourly['total_amount'],
        name="Total Amount",
        marker_color='lightblue',
        yaxis='y'
    ))

    fig.add_trace(go.Scatter(
        x=hourly['hour'],
        y=hourly['avg_risk'],
        name="Avg Risk Score",
        line=dict(color='red', width=3),
        yaxis='y2'
    ))

    fig.update_layout(
        title="High-Value Transaction Timeline",
        xaxis=dict(title="Time"),
        yaxis=dict(
            title="Total Amount ($)",
            side='left'
        ),
        yaxis2=dict(
            title="Average Risk Score",
            overlaying='y',
            side='right',
            range=[0, 1]
        ),
        hovermode='x unified',
        height=350
    )

    st.plotly_chart(fig, use_container_width=True)


def render():
    """Render the High-Value Transaction Monitoring page"""

    # Header
    st.markdown("# Capital Intelligence Hub")
    st.markdown("Enhanced monitoring and risk analysis for large transactions")

    # Configuration
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        threshold = st.number_input(
            "Amount Threshold ($)",
            min_value=1000.0,
            max_value=1000000.0,
            value=10000.0,
            step=1000.0
        )

    with col2:
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
        with st.spinner("Loading high-value transaction data..."):
            hv_data = client.get_high_value_transactions(
                threshold=threshold,
                time_range=time_range,
                limit=limit
            )

        # Display timestamp
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Overview statistics
        st.markdown("### Capital Flow Performance")
        render_high_value_stats(hv_data)

        st.divider()

        # Charts row 1
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Exposure Distribution")
            render_amount_distribution(hv_data)

        with col2:
            st.markdown("### Instrument Classification & Flow Segmentation")
            render_transaction_type_breakdown(hv_data)

        st.divider()

        # Risk analysis
        st.markdown("### Predictive Risk Intelligence")
        render_risk_vs_amount_scatter(hv_data)

        st.divider()

        # Time series
        st.markdown("### Capital Velocity")
        render_time_series(hv_data)

        st.divider()

        # Transaction list
        render_top_transactions_table(hv_data, limit=20)

        # Insights
        st.divider()
        st.markdown("### Intelligence Insights")

        transactions = hv_data.get("transactions", [])
        if transactions:
            # Find largest transaction
            largest_tx = max(transactions, key=lambda x: x["amount"])
            # Find highest risk transaction
            highest_risk_tx = max(transactions, key=lambda x: x["risk_score"])

            col1, col2, col3 = st.columns(3)

            with col1:
                st.error(f"**Largest Transaction:**\n\n{largest_tx['transaction_id']}\n\n{format_currency(largest_tx['amount'])}")

            with col2:
                st.warning(f"**Highest Risk:**\n\n{highest_risk_tx['transaction_id']}\n\nRisk: {highest_risk_tx['risk_score']:.3f}")

            with col3:
                flagged_pct = hv_data.get('high_risk_rate', 0) * 100
                st.info(f"**Flagged Rate:**\n\n{flagged_pct:.1f}%\n\nRequire review")

    except Exception as e:
        st.error(f"❌ Error loading high-value transactions: {str(e)}")
        st.exception(e)


if __name__ == "__main__" or True:
    render()
