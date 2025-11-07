"""Executive Summary Dashboard Page"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from app.models.database import get_db, Transaction, RiskAssessment, Account

def show():
    st.header("🏠 Executive Summary")
    st.markdown("High-level overview of transaction monitoring system performance")

    # Get data
    db = next(get_db())
    try:
        # Get all transactions and assessments
        transactions = db.query(Transaction).all()
        assessments = db.query(RiskAssessment).all()
        accounts = db.query(Account).all()

        if not transactions:
            st.warning("No transaction data available. Please run the data generation script.")
            return

        # Convert to DataFrames
        tx_data = [{
            'transaction_id': tx.transaction_id,
            'account_id': tx.account_id,
            'timestamp': datetime.fromisoformat(tx.timestamp),
            'amount': tx.amount,
            'transaction_type': tx.transaction_type,
            'direction': tx.direction
        } for tx in transactions]
        tx_df = pd.DataFrame(tx_data)

        assess_data = [{
            'assessment_id': a.assessment_id,
            'transaction_id': a.transaction_id,
            'risk_score': a.risk_score,
            'decision': a.decision,
            'review_status': a.review_status
        } for a in assessments]
        assess_df = pd.DataFrame(assess_data)

        # Merge data
        df = tx_df.merge(assess_df, on='transaction_id', how='left')

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Transactions",
                f"{len(transactions):,}",
                f"Last 30 days"
            )

        with col2:
            total_value = df['amount'].sum()
            st.metric(
                "Total Value",
                f"${total_value:,.0f}",
                f"Processed"
            )

        with col3:
            auto_approved = df[df['decision'] == 'auto_approve'].shape[0]
            auto_rate = (auto_approved / len(df) * 100) if len(df) > 0 else 0
            st.metric(
                "Auto-Approved",
                f"{auto_approved:,}",
                f"{auto_rate:.1f}%"
            )

        with col4:
            avg_risk = df['risk_score'].mean()
            st.metric(
                "Avg Risk Score",
                f"{avg_risk:.3f}",
                "0-1 scale"
            )

        st.markdown("---")

        # Two column layout for charts
        col1, col2 = st.columns(2)

        with col1:
            # Transaction volume over time
            st.subheader("📈 Transaction Volume Trend")
            df['date'] = df['timestamp'].dt.date
            daily_volume = df.groupby('date').size().reset_index(name='count')

            fig = px.line(
                daily_volume,
                x='date',
                y='count',
                title='Daily Transaction Volume',
                labels={'date': 'Date', 'count': 'Transactions'}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Decision distribution
            st.subheader("🎯 Decision Distribution")
            decision_counts = df['decision'].value_counts()

            fig = go.Figure(data=[go.Pie(
                labels=decision_counts.index,
                values=decision_counts.values,
                hole=0.4,
                marker=dict(colors=['#2ecc71', '#e74c3c'])
            )])
            fig.update_layout(
                title='Auto-Approve vs Manual Review',
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)

        # Second row of charts
        col1, col2 = st.columns(2)

        with col1:
            # Transaction types
            st.subheader("💳 Transaction Types")
            type_counts = df['transaction_type'].value_counts()

            fig = px.bar(
                x=type_counts.index,
                y=type_counts.values,
                title='Transactions by Type',
                labels={'x': 'Transaction Type', 'y': 'Count'},
                color=type_counts.values,
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Risk score distribution
            st.subheader("⚠️ Risk Score Histogram")

            fig = px.histogram(
                df,
                x='risk_score',
                nbins=20,
                title='Risk Score Distribution',
                labels={'risk_score': 'Risk Score', 'count': 'Frequency'},
                color_discrete_sequence=['#3498db']
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

        # Transaction amount analysis
        st.markdown("---")
        st.subheader("💰 Transaction Amount Analysis")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Min Amount", f"${df['amount'].min():,.2f}")
        with col2:
            st.metric("Median Amount", f"${df['amount'].median():,.2f}")
        with col3:
            st.metric("Max Amount", f"${df['amount'].max():,.2f}")

        # Amount distribution by transaction type
        fig = px.box(
            df,
            x='transaction_type',
            y='amount',
            title='Amount Distribution by Transaction Type',
            labels={'transaction_type': 'Type', 'amount': 'Amount ($)'},
            color='transaction_type'
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    finally:
        db.close()
