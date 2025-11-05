"""
Investigation Tools Page

Deep-dive investigation features for fraud analysts.
Search transactions, investigate accounts, and analyze fraud detection module outputs.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, List

from streamlit_app.api_client import get_api_client


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


# def render_transaction_search():
#     """Render transaction search interface"""
#     st.markdown("### 🔍 Transaction Search")

#     with st.form("transaction_search"):
#         col1, col2 = st.columns(2)

#         with col1:
#             transaction_id = st.text_input("Transaction ID", help="Search by exact or partial transaction ID")
#             account_id = st.text_input("Account ID", help="Filter by account")

#             # Amount range
#             st.markdown("**Amount Range**")
#             amount_col1, amount_col2 = st.columns(2)
#             with amount_col1:
#                 min_amount = st.number_input("Min Amount", min_value=0.0, value=0.0, step=100.0)
#             with amount_col2:
#                 max_amount = st.number_input("Max Amount", min_value=0.0, value=100000.0, step=100.0)

#         with col2:
#             # Date range
#             st.markdown("**Date Range**")
#             date_col1, date_col2 = st.columns(2)
#             with date_col1:
#                 start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
#             with date_col2:
#                 end_date = st.date_input("End Date", value=datetime.now())

#             risk_level = st.selectbox(
#                 "Risk Level",
#                 ["All", "Low", "Medium", "High"],
#                 help="Filter by risk level"
#             )

#             limit = st.number_input("Max Results", min_value=10, max_value=500, value=50, step=10)

#         search_button = st.form_submit_button("🔍 Search", use_container_width=True)

#     if search_button:
#         client = get_api_client()

#         try:
#             with st.spinner("Searching transactions..."):
#                 results = client.search_transactions(
#                     transaction_id=transaction_id if transaction_id else None,
#                     account_id=account_id if account_id else None,
#                     min_amount=min_amount if min_amount > 0 else None,
#                     max_amount=max_amount if max_amount < 100000 else None,
#                     start_date=start_date.isoformat() if start_date else None,
#                     end_date=end_date.isoformat() if end_date else None,
#                     risk_level=risk_level.lower() if risk_level != "All" else None,
#                     limit=limit
#                 )

#             transactions = results.get("transactions", [])

#             if not transactions:
#                 st.info("No transactions found matching your criteria")
#                 return

#             st.success(f"Found {len(transactions)} transaction(s)")

#             # Display results
#             for idx, tx in enumerate(transactions):
#                 with st.expander(
#                     f"**{tx['transaction_id']}** - {format_currency(tx['amount'])} - "
#                     f"{tx.get('transaction_type', 'N/A')} - Risk: {tx.get('risk_score', 0):.2f}",
#                     expanded=(idx == 0)
#                 ):
#                     col1, col2, col3 = st.columns(3)

#                     with col1:
#                         st.markdown("#### Transaction Details")
#                         st.markdown(f"**ID:** {tx['transaction_id']}")
#                         st.markdown(f"**Account:** {tx['account_id']}")
#                         st.markdown(f"**Amount:** {format_currency(tx['amount'])}")
#                         st.markdown(f"**Direction:** {tx.get('direction', 'N/A')}")

#                     with col2:
#                         st.markdown("#### Risk Information")
#                         risk_score = tx.get('risk_score', 0)
#                         st.markdown(f"**Risk Score:** {risk_score:.3f}")
#                         st.markdown(f"**Decision:** {tx.get('decision', 'N/A')}")
#                         st.markdown(f"**Status:** {tx.get('review_status', 'N/A')}")
#                         st.markdown(f"**Rules Triggered:** {tx.get('triggered_rules_count', 0)}")

#                     with col3:
#                         st.markdown("#### Other Info")
#                         st.markdown(f"**Type:** {tx.get('transaction_type', 'N/A')}")
#                         st.markdown(f"**Counterparty:** {tx.get('counterparty_id', 'N/A')}")
#                         st.markdown(f"**Timestamp:** {format_timestamp(tx.get('timestamp', ''))}")

#                     # Action buttons
#                     btn_col1, btn_col2, btn_col3 = st.columns(3)
#                     with btn_col1:
#                         if st.button(f"View Module Breakdown", key=f"modules_{idx}"):
#                             st.session_state.view_module_breakdown = tx['transaction_id']
#                     with btn_col2:
#                         if st.button(f"Investigate Account", key=f"account_{idx}"):
#                             st.session_state.investigate_account = tx['account_id']
#                     with btn_col3:
#                         st.markdown("")  # Spacing

#         except Exception as e:
#             st.error(f"Search failed: {str(e)}")

def render_transaction_search():
    """Render transaction search interface"""
    st.markdown("### 🔍 Transaction Search")

    with st.form("transaction_search"):
        col1, col2 = st.columns(2)

        with col1:
            transaction_id = st.text_input("Transaction ID", help="Search by exact or partial transaction ID")
            account_id = st.text_input("Account ID", help="Filter by account")

            # Amount range
            st.markdown("**Amount Range**")
            amount_col1, amount_col2 = st.columns(2)
            with amount_col1:
                min_amount = st.number_input("Min Amount", min_value=0.0, value=0.0, step=100.0)
            with amount_col2:
                max_amount = st.number_input("Max Amount", min_value=0.0, value=100000.0, step=100.0)

        with col2:
            # Date range
            st.markdown("**Date Range**")
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
            with date_col2:
                end_date = st.date_input("End Date", value=datetime.now())

            risk_level = st.selectbox(
                "Risk Level",
                ["All", "Low", "Medium", "High"],
                help="Filter by risk level"
            )

            limit = st.number_input("Max Results", min_value=10, max_value=500, value=50, step=10)

        search_button = st.form_submit_button("🔍 Search", use_container_width=True)

    if search_button:
        client = get_api_client()

        try:
            with st.spinner("Searching transactions..."):
                results = client.search_transactions(
                    transaction_id=transaction_id if transaction_id else None,
                    account_id=account_id if account_id else None,
                    min_amount=min_amount if min_amount > 0 else None,
                    max_amount=max_amount if max_amount < 100000 else None,
                    start_date=start_date.isoformat() if start_date else None,
                    end_date=end_date.isoformat() if end_date else None,
                    risk_level=risk_level.lower() if risk_level != "All" else None,
                    limit=limit
                )

            transactions = results.get("transactions", [])

            if not transactions:
                st.info("No transactions found matching your criteria")
                return

            st.success(f"Found {len(transactions)} transaction(s)")

            # ===============================
            # 📊 Global Visualizations (NEW)
            # ===============================
            # Extract data safely
            risk_scores = [float(t.get('risk_score', 0) or 0) for t in transactions]
            amounts = [float(t.get('amount', 0) or 0) for t in transactions]
            tx_ids = [t.get('transaction_id', 'N/A') for t in transactions]

            viz_col1, viz_col2 = st.columns(2)

            # Risk Score Distribution (Histogram)
            with viz_col1:
                st.markdown("#### Risk Score Distribution")
                fig_dist = go.Figure()
                fig_dist.add_trace(go.Histogram(
                    x=risk_scores,
                    nbinsx=20,
                    marker_color='#3b82f6',
                    hovertemplate='Risk Score: %{x:.2f}<br>Count: %{y}<extra></extra>'
                ))
                fig_dist.update_layout(
                    xaxis_title="Risk Score",
                    yaxis_title="Transaction Count",
                    height=400,
                    bargap=0.05
                )
                st.plotly_chart(fig_dist, use_container_width=True)

            # Amount vs Risk (Scatter)
            with viz_col2:
                st.markdown("#### Transaction Amount vs Risk Score")
                fig_scatter = go.Figure()
                fig_scatter.add_trace(go.Scatter(
                    x=amounts,
                    y=risk_scores,
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=risk_scores,
                        colorscale='RdYlGn_r',
                        showscale=True,
                        colorbar=dict(title="Risk Score")
                    ),
                    text=tx_ids,
                    hovertemplate='<b>%{text}</b><br>Amount: $%{x:,.2f}<br>Risk: %{y:.2f}<extra></extra>'
                ))
                fig_scatter.update_layout(
                    xaxis_title="Transaction Amount ($)",
                    yaxis_title="Risk Score",
                    height=400,
                    hovermode='closest'
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

            st.divider()
            st.markdown("#### Results")

            # =====================================
            # Existing per-transaction expanders
            # =====================================
            for idx, tx in enumerate(transactions):
                with st.expander(
                    f"**{tx['transaction_id']}** - {format_currency(tx['amount'])} - "
                    f"{tx.get('transaction_type', 'N/A')} - Risk: {tx.get('risk_score', 0):.2f}",
                    expanded=(idx == 0)
                ):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown("#### Transaction Details")
                        st.markdown(f"**ID:** {tx['transaction_id']}")
                        st.markdown(f"**Account:** {tx['account_id']}")
                        st.markdown(f"**Amount:** {format_currency(tx['amount'])}")
                        st.markdown(f"**Direction:** {tx.get('direction', 'N/A')}")

                    with col2:
                        st.markdown("#### Risk Information")
                        risk_score = float(tx.get('risk_score', 0) or 0)
                        st.markdown(f"**Risk Score:** {risk_score:.3f}")
                        st.markdown(f"**Decision:** {tx.get('decision', 'N/A')}")
                        st.markdown(f"**Status:** {tx.get('review_status', 'N/A')}")
                        st.markdown(f"**Rules Triggered:** {tx.get('triggered_rules_count', 0)}")

                    with col3:
                        st.markdown("#### Other Info")
                        st.markdown(f"**Type:** {tx.get('transaction_type', 'N/A')}")
                        st.markdown(f"**Counterparty:** {tx.get('counterparty_id', 'N/A')}")
                        st.markdown(f"**Timestamp:** {format_timestamp(tx.get('timestamp', ''))}")

                    # Action buttons
                    btn_col1, btn_col2, btn_col3 = st.columns(3)
                    with btn_col1:
                        if st.button(f"View Module Breakdown", key=f"modules_{idx}"):
                            st.session_state.view_module_breakdown = tx['transaction_id']
                    with btn_col2:
                        if st.button(f"Investigate Account", key=f"account_{idx}"):
                            st.session_state.investigate_account = tx['account_id']
                    with btn_col3:
                        st.markdown("")  # Spacing

        except Exception as e:
            st.error(f"Search failed: {str(e)}")


def render_module_breakdown(transaction_id: str):
    """Render fraud detection module breakdown"""
    st.markdown(f"### 🔬 Module Breakdown - {transaction_id}")

    client = get_api_client()

    try:
        with st.spinner("Loading module breakdown..."):
            breakdown = client.get_transaction_module_breakdown(transaction_id)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Risk Score", f"{breakdown.get('risk_score', 0):.3f}")
        with col2:
            st.metric("Modules Triggered", f"{breakdown.get('total_modules_triggered', 0)}/25")
        with col3:
            st.metric("Decision", breakdown.get('decision', 'N/A'))
        with col4:
            st.metric("Status", breakdown.get('review_status', 'N/A'))

        st.divider()

        modules = breakdown.get("modules_triggered", [])

        if not modules:
            st.info("No fraud detection modules were triggered for this transaction")
            return

        st.markdown("#### Triggered Fraud Detection Modules")

        # Create DataFrame
        df = pd.DataFrame(modules)

        # Color code by severity
        def get_severity_color(severity):
            colors = {
                "high": "#ff4444",
                "medium": "#ff8800",
                "low": "#ffaa00"
            }
            return colors.get(severity, "#cccccc")

        # Display as colored cards
        for idx, module in enumerate(modules):
            severity = module.get("severity", "low")
            color = get_severity_color(severity)

            st.markdown(
                f"""
                <div style="
                    background-color: {color}15;
                    border-left: 4px solid {color};
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 10px;
                ">
                    <h4 style="margin: 0; color: {color};">
                        {module.get('description', module.get('name', 'Unknown Module'))}
                    </h4>
                    <p style="margin: 5px 0;">
                        <strong>Weight:</strong> {module.get('weight', 0):.3f} |
                        <strong>Category:</strong> {module.get('category', 'general')} |
                        <strong>Severity:</strong> {severity.upper()}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Summary chart
        st.markdown("#### Module Weight Distribution")
        fig = px.bar(
            df,
            x="weight",
            y="description",
            orientation='h',
            color="severity",
            color_discrete_map={
                "high": "#ff4444",
                "medium": "#ff8800",
                "low": "#ffaa00"
            },
            title="Triggered Modules by Weight"
        )
        fig.update_layout(height=400, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to load module breakdown: {str(e)}")


def render_account_risk_timeline(account_id: str, time_range: str = "7d"):
    """Render risk score timeline for an account"""
    client = get_api_client()

    try:
        with st.spinner("Loading risk timeline..."):
            timeline_data = client.get_account_risk_timeline(account_id, time_range)

        timeline = timeline_data.get("timeline", [])
        statistics = timeline_data.get("statistics", {})

        if not timeline:
            st.info("No transaction history available for this time period")
            return

        # Statistics overview
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total Transactions", timeline_data.get("total_transactions", 0))

        with col2:
            st.metric("Avg Risk", f"{statistics.get('average_risk', 0):.3f}")

        with col3:
            st.metric("Current Risk", f"{statistics.get('current_risk', 0):.3f}")

        with col4:
            trend = statistics.get('risk_trend', 'stable')
            trend_emoji = "📈" if trend == "increasing" else "📉"
            st.metric("Trend", f"{trend_emoji} {trend.title()}")

        with col5:
            st.metric("High Risk Count", statistics.get('high_risk_count', 0))

        # Create timeline chart
        df = pd.DataFrame(timeline)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Dual-axis chart: Risk score and moving average
        fig = go.Figure()

        # Add risk score scatter
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['risk_score'],
            name='Risk Score',
            mode='markers+lines',
            marker=dict(
                size=8,
                color=df['risk_score'],
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title="Risk Score")
            ),
            line=dict(color='lightblue', width=1),
            text=df['transaction_id'],
            hovertemplate='<b>%{text}</b><br>Risk: %{y:.3f}<br>Time: %{x}<extra></extra>'
        ))

        # Add moving average line
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['moving_average'],
            name='Moving Average (5 tx)',
            line=dict(color='darkblue', width=3),
            hovertemplate='Moving Avg: %{y:.3f}<extra></extra>'
        ))

        # Add risk threshold lines
        fig.add_hline(y=0.6, line_dash="dash", line_color="orange",
                     annotation_text="High Risk Threshold (0.6)")
        fig.add_hline(y=0.8, line_dash="dash", line_color="red",
                     annotation_text="Critical Risk Threshold (0.8)")

        fig.update_layout(
            title=f"Risk Score Timeline - {account_id}",
            xaxis=dict(title="Date/Time"),
            yaxis=dict(title="Risk Score", range=[0, 1]),
            hovermode='x unified',
            height=400,
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

        # Transaction amount vs risk scatter
        fig2 = go.Figure()

        fig2.add_trace(go.Scatter(
            x=df['amount'],
            y=df['risk_score'],
            mode='markers',
            marker=dict(
                size=10,
                color=df['risk_score'],
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title="Risk")
            ),
            text=df['transaction_type'],
            hovertemplate='<b>%{text}</b><br>Amount: $%{x:,.0f}<br>Risk: %{y:.3f}<extra></extra>'
        ))

        fig2.add_hline(y=0.6, line_dash="dash", line_color="orange")
        fig2.add_hline(y=0.8, line_dash="dash", line_color="red")

        fig2.update_layout(
            title="Risk Score vs Transaction Amount",
            xaxis=dict(title="Transaction Amount ($)"),
            yaxis=dict(title="Risk Score", range=[0, 1]),
            height=350
        )

        st.plotly_chart(fig2, use_container_width=True)

        # Detailed transaction table
        with st.expander("📋 View Detailed Timeline Data"):
            display_df = df[[
                'timestamp', 'transaction_id', 'amount', 'risk_score',
                'moving_average', 'decision', 'review_status', 'triggered_rules_count'
            ]].copy()

            display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            display_df['amount'] = display_df['amount'].apply(format_currency)
            display_df['risk_score'] = display_df['risk_score'].apply(lambda x: f"{x:.3f}")
            display_df['moving_average'] = display_df['moving_average'].apply(lambda x: f"{x:.3f}")

            display_df.columns = [
                'Timestamp', 'Transaction ID', 'Amount', 'Risk Score',
                'Moving Avg', 'Decision', 'Status', 'Rules Triggered'
            ]

            st.dataframe(display_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Failed to load risk timeline: {str(e)}")


def render_account_investigation(account_id: str):
    """Render comprehensive account investigation"""
    st.markdown(f"### 👤 Account Investigation - {account_id}")

    client = get_api_client()

    try:
        with st.spinner("Loading account information..."):
            account_data = client.get_account_investigation(account_id)

        # Account Overview
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("#### Account Info")
            st.markdown(f"**Account ID:** {account_data.get('account_id')}")
            st.markdown(f"**Status:** {account_data.get('status')}")
            st.markdown(f"**Risk Tier:** {account_data.get('risk_tier')}")
            st.markdown(f"**Created:** {format_timestamp(account_data.get('creation_date', ''))}")

        stats = account_data.get("statistics", {})

        with col2:
            st.markdown("#### Transaction Statistics")
            st.metric("Total Transactions", stats.get("total_transactions", 0))
            st.metric("Total Value", format_currency(stats.get("total_value", 0)))

        with col3:
            st.markdown("#### Risk Profile")
            st.metric("Avg Risk Score", f"{stats.get('average_risk_score', 0):.3f}")
            st.metric("High Risk Count", stats.get("high_risk_count", 0))
            high_risk_rate = stats.get("high_risk_rate", 0) * 100
            st.metric("High Risk Rate", f"{high_risk_rate:.1f}%")

        st.divider()

        # Risk Score Timeline
        st.markdown("### 📉 Account Risk Score Timeline")

        # Time range selector for timeline
        timeline_col1, timeline_col2 = st.columns([2, 1])
        with timeline_col1:
            timeline_range = st.selectbox(
                "Timeline Period",
                ["24h", "7d", "30d"],
                index=1,
                format_func=lambda x: {
                    "24h": "Last 24 Hours",
                    "7d": "Last 7 Days",
                    "30d": "Last 30 Days"
                }[x],
                key="timeline_range"
            )
        with timeline_col2:
            st.markdown("")  # Spacing

        render_account_risk_timeline(account_id, timeline_range)

        st.divider()

        # Employees
        employees = account_data.get("employees", [])
        if employees:
            st.markdown("#### Associated Employees")
            emp_df = pd.DataFrame(employees)
            st.dataframe(emp_df, use_container_width=True, hide_index=True)

        st.divider()

        # Recent transactions
        st.markdown("#### Recent Transactions")
        recent_txs = account_data.get("recent_transactions", [])

        if recent_txs:
            tx_df = pd.DataFrame(recent_txs)
            tx_df["amount"] = tx_df["amount"].apply(format_currency)
            tx_df["timestamp"] = tx_df["timestamp"].apply(format_timestamp)
            st.dataframe(tx_df, use_container_width=True, hide_index=True)
        else:
            st.info("No recent transactions")

    except Exception as e:
        st.error(f"Failed to load account information: {str(e)}")


def render():
    """Render the Investigation Tools page"""

    # Header
    st.markdown("# Transaction Monitoring System")
    st.markdown("### Real-Time Fraud Detection & Alert Management")

    st.divider()

    # Check if we need to show specific views
    if "view_module_breakdown" in st.session_state:
        transaction_id = st.session_state.view_module_breakdown
        if st.button("← Back to Search"):
            del st.session_state.view_module_breakdown
            st.rerun()
        render_module_breakdown(transaction_id)
        return

    if "investigate_account" in st.session_state:
        account_id = st.session_state.investigate_account
        if st.button("← Back to Search"):
            del st.session_state.investigate_account
            st.rerun()
        render_account_investigation(account_id)
        return

    # Default view: Transaction search
    render_transaction_search()

    # Quick access section
    st.divider()
    st.markdown("### ⚡ Quick Access")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Recent High-Risk Transactions")
        st.markdown("View the most recent high-risk flagged transactions")
        if st.button("View High-Risk Alerts", use_container_width=True):
            # Trigger search with high risk filter
            st.info("Use the search form above and select 'High' risk level")

    with col2:
        st.markdown("#### Account Lookup")
        account_lookup = st.text_input("Enter Account ID")
        if st.button("Investigate Account", use_container_width=True, key="quick_account"):
            if account_lookup:
                st.session_state.investigate_account = account_lookup
                st.rerun()
            else:
                st.warning("Please enter an account ID")


if __name__ == "__main__" or True:
    render()
