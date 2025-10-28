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

            # Display results
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
                        risk_score = tx.get('risk_score', 0)
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
    st.markdown("# 🔍 Investigation Tools")
    st.markdown("Deep-dive investigation features for fraud analysts")

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
