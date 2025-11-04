"""
Transaction Analytics

Detailed transaction analysis with rule breakdowns and visual plots.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

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


def render():
    """Render the Transaction Analytics page"""

    # Header
    st.markdown("# Transaction Analytics")
    st.markdown("### Detailed Transaction Analysis with Rule Breakdowns")
    st.caption(f"Last Updated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}")

    st.markdown("---")

    client = get_api_client()

    # Search filters
    st.markdown("## 🔍 Transaction Search")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        transaction_id = st.text_input("Transaction ID")
    with col2:
        account_id = st.text_input("Account ID")
    with col3:
        min_amount = st.number_input("Min Amount ($)", min_value=0.0, value=0.0)
    with col4:
        max_amount = st.number_input("Max Amount ($)", min_value=0.0, value=100000.0)

    col5, col6, col7 = st.columns(3)

    with col5:
        risk_level = st.selectbox("Risk Level", ["All", "low", "medium", "high", "critical"])
    with col6:
        start_date = st.date_input("Start Date")
    with col7:
        end_date = st.date_input("End Date")

    search_button = st.button("🔍 Search Transactions", type="primary")

    st.markdown("---")

    if search_button or transaction_id or account_id:
        try:
            # Perform search
            with st.spinner("Searching transactions..."):
                results = client.search_transactions(
                    transaction_id=transaction_id if transaction_id else None,
                    account_id=account_id if account_id else None,
                    min_amount=min_amount if min_amount > 0 else None,
                    max_amount=max_amount if max_amount < 100000 else None,
                    risk_level=risk_level if risk_level != "All" else None,
                    start_date=start_date.isoformat() if start_date else None,
                    end_date=end_date.isoformat() if end_date else None,
                    limit=50
                )

            if results and 'transactions' in results:
                transactions = results['transactions']

                st.markdown(f"## 📊 Search Results ({len(transactions)} transactions found)")

                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)

                total_value = sum(t.get('amount', 0) for t in transactions)
                avg_risk = sum(t.get('risk_score', 0) for t in transactions) / max(len(transactions), 1)
                high_risk_count = sum(1 for t in transactions if t.get('risk_score', 0) >= 0.7)

                with col1:
                    st.metric("Total Transactions", len(transactions))
                with col2:
                    st.metric("Total Value", format_currency(total_value))
                with col3:
                    st.metric("Average Risk Score", f"{avg_risk:.2f}")
                with col4:
                    st.metric("High Risk Count", high_risk_count)

                st.markdown("---")

                # Transaction details with expandable sections
                for idx, txn in enumerate(transactions[:20]):  # Show first 20
                    risk_score = txn.get('risk_score', 0)

                    # Determine risk level and color
                    if risk_score >= 0.8:
                        risk_level_str = "🔴 CRITICAL"
                        risk_color = "#ef4444"
                    elif risk_score >= 0.6:
                        risk_level_str = "🟠 HIGH"
                        risk_color = "#f97316"
                    elif risk_score >= 0.3:
                        risk_level_str = "🟡 MEDIUM"
                        risk_color = "#eab308"
                    else:
                        risk_level_str = "🟢 LOW"
                        risk_color = "#10b981"

                    with st.expander(f"{risk_level_str} | {txn.get('transaction_id', 'N/A')} | {format_currency(txn.get('amount', 0))} | {format_timestamp(txn.get('timestamp', ''))}"):
                        col1, col2 = st.columns([1, 1])

                        with col1:
                            st.markdown("### Transaction Details")
                            st.markdown(f"**Transaction ID:** {txn.get('transaction_id', 'N/A')}")
                            st.markdown(f"**Account ID:** {txn.get('account_id', 'N/A')}")
                            st.markdown(f"**Amount:** {format_currency(txn.get('amount', 0))}")
                            st.markdown(f"**Type:** {txn.get('transaction_type', 'N/A')}")
                            st.markdown(f"**Direction:** {txn.get('direction', 'N/A')}")
                            st.markdown(f"**Timestamp:** {format_timestamp(txn.get('timestamp', ''))}")
                            st.markdown(f"**Description:** {txn.get('description', 'N/A')}")

                        with col2:
                            st.markdown("### Risk Assessment")
                            st.markdown(f"**Risk Score:** {risk_score:.2f}")
                            st.markdown(f"**Risk Level:** {risk_level_str}")
                            st.markdown(f"**Decision:** {txn.get('decision', 'N/A').upper()}")
                            st.markdown(f"**Review Status:** {txn.get('review_status', 'N/A')}")

                        # Risk score gauge
                        fig_gauge = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=risk_score,
                            domain={'x': [0, 1], 'y': [0, 1]},
                            gauge={
                                'axis': {'range': [0, 1]},
                                'bar': {'color': risk_color},
                                'steps': [
                                    {'range': [0, 0.3], 'color': "#d1fae5"},
                                    {'range': [0.3, 0.6], 'color': "#fef3c7"},
                                    {'range': [0.6, 1], 'color': "#fee2e2"}
                                ],
                                'threshold': {
                                    'line': {'color': "red", 'width': 4},
                                    'thickness': 0.75,
                                    'value': 0.6
                                }
                            }
                        ))

                        fig_gauge.update_layout(height=200, margin=dict(l=20, r=20, t=20, b=20))
                        st.plotly_chart(fig_gauge, use_container_width=True)

                        # Triggered rules
                        if 'triggered_rules' in txn and txn['triggered_rules']:
                            st.markdown("### 🚨 Triggered Rules")

                            # If triggered_rules is a dict
                            if isinstance(txn['triggered_rules'], dict):
                                for rule_name, rule_data in txn['triggered_rules'].items():
                                    if isinstance(rule_data, dict):
                                        st.markdown(f"- **{rule_name}**: {rule_data.get('detail', 'N/A')}")
                                    else:
                                        st.markdown(f"- **{rule_name}**")
                            # If triggered_rules is a list
                            elif isinstance(txn['triggered_rules'], list):
                                for rule in txn['triggered_rules']:
                                    st.markdown(f"- {rule}")
                        else:
                            st.info("No rules triggered for this transaction")

                # Visualization: Risk Distribution
                st.markdown("---")
                st.markdown("## 📈 Risk Score Distribution")

                risk_scores = [t.get('risk_score', 0) for t in transactions]

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
                    height=400
                )

                st.plotly_chart(fig_dist, use_container_width=True)

                # Amount vs Risk scatter plot
                st.markdown("## 💰 Transaction Amount vs Risk Score")

                amounts = [t.get('amount', 0) for t in transactions]

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
                    text=[t.get('transaction_id', 'N/A') for t in transactions],
                    hovertemplate='<b>%{text}</b><br>Amount: $%{x:,.2f}<br>Risk: %{y:.2f}<extra></extra>'
                ))

                fig_scatter.update_layout(
                    xaxis_title="Transaction Amount ($)",
                    yaxis_title="Risk Score",
                    height=500,
                    hovermode='closest'
                )

                st.plotly_chart(fig_scatter, use_container_width=True)

            else:
                st.info("No transactions found matching your search criteria.")

        except Exception as e:
            st.error(f"❌ Error searching transactions: {str(e)}")
            st.info("Please ensure the FastAPI backend is running at http://localhost:8000")
            st.exception(e)
    else:
        st.info("👆 Enter search criteria above and click 'Search Transactions' to view detailed transaction analytics with rule breakdowns.")

        # Show sample overview
        st.markdown("## 📊 Sample Transaction Overview")
        st.markdown("""
        This page provides comprehensive transaction analytics including:

        - **Transaction Search** - Multi-criteria filtering
        - **Risk Assessment Details** - Complete rule breakdowns
        - **Visual Analytics** - Risk distributions and correlations
        - **Decision History** - Approval/rejection tracking
        - **Rule Impact Analysis** - Which rules contribute most to risk scores

        Use the search filters above to begin analyzing transactions.
        """)

    st.markdown("---")
    st.caption("💡 **Note:** Transaction data is retrieved in real-time from the detection system database.")
