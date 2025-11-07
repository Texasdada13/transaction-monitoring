"""Risk Distribution Analysis Page"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from app.models.database import get_db, Transaction, RiskAssessment

def show():
    st.header("⚠️ Risk Distribution Analysis")
    st.markdown("Comprehensive view of risk scores across all transactions")

    db = next(get_db())
    try:
        transactions = db.query(Transaction).all()
        assessments = db.query(RiskAssessment).all()

        if not assessments:
            st.warning("No risk assessment data available.")
            return

        # Convert to DataFrames
        tx_data = [{
            'transaction_id': tx.transaction_id,
            'timestamp': datetime.fromisoformat(tx.timestamp),
            'amount': tx.amount,
            'transaction_type': tx.transaction_type
        } for tx in transactions]
        tx_df = pd.DataFrame(tx_data)

        assess_data = [{
            'transaction_id': a.transaction_id,
            'risk_score': a.risk_score,
            'decision': a.decision,
            'review_status': a.review_status
        } for a in assessments]
        assess_df = pd.DataFrame(assess_data)

        df = tx_df.merge(assess_df, on='transaction_id', how='left')

        # Risk categories
        df['risk_category'] = pd.cut(
            df['risk_score'],
            bins=[0, 0.3, 0.6, 1.0],
            labels=['Low Risk', 'Medium Risk', 'High Risk']
        )

        # Top metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Min Risk Score", f"{df['risk_score'].min():.3f}")
        with col2:
            st.metric("Mean Risk Score", f"{df['risk_score'].mean():.3f}")
        with col3:
            st.metric("Median Risk Score", f"{df['risk_score'].median():.3f}")
        with col4:
            st.metric("Max Risk Score", f"{df['risk_score'].max():.3f}")

        st.markdown("---")

        # Risk category distribution
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Risk Category Distribution")
            category_counts = df['risk_category'].value_counts()

            fig = go.Figure(data=[go.Pie(
                labels=category_counts.index,
                values=category_counts.values,
                marker=dict(colors=['#2ecc71', '#f39c12', '#e74c3c']),
                hole=0.4
            )])
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("📈 Risk Score Histogram")

            fig = px.histogram(
                df,
                x='risk_score',
                nbins=30,
                color_discrete_sequence=['#3498db']
            )
            fig.update_layout(
                xaxis_title='Risk Score',
                yaxis_title='Frequency',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        # Risk over time
        st.markdown("---")
        st.subheader("📅 Risk Trends Over Time")

        df['date'] = df['timestamp'].dt.date
        daily_risk = df.groupby('date').agg({
            'risk_score': ['mean', 'max', 'count']
        }).reset_index()
        daily_risk.columns = ['date', 'avg_risk', 'max_risk', 'count']

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_risk['date'],
            y=daily_risk['avg_risk'],
            mode='lines+markers',
            name='Average Risk',
            line=dict(color='#3498db', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=daily_risk['date'],
            y=daily_risk['max_risk'],
            mode='lines+markers',
            name='Maximum Risk',
            line=dict(color='#e74c3c', width=2)
        ))
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Risk Score',
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Risk by transaction type
        st.markdown("---")
        st.subheader("💳 Risk Distribution by Transaction Type")

        fig = px.box(
            df,
            x='transaction_type',
            y='risk_score',
            color='transaction_type',
            points='outliers'
        )
        fig.update_layout(
            xaxis_title='Transaction Type',
            yaxis_title='Risk Score',
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

        # Risk vs Amount correlation
        st.markdown("---")
        st.subheader("💰 Risk Score vs Transaction Amount")

        fig = px.scatter(
            df,
            x='amount',
            y='risk_score',
            color='risk_category',
            color_discrete_map={
                'Low Risk': '#2ecc71',
                'Medium Risk': '#f39c12',
                'High Risk': '#e74c3c'
            },
            hover_data=['transaction_type']
        )
        fig.update_layout(
            xaxis_title='Transaction Amount ($)',
            yaxis_title='Risk Score',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # High risk transactions detail
        st.markdown("---")
        st.subheader("🚨 High Risk Transactions (Score >= 0.6)")

        high_risk_df = df[df['risk_score'] >= 0.6].sort_values('risk_score', ascending=False)

        if len(high_risk_df) > 0:
            display_df = high_risk_df[['transaction_id', 'timestamp', 'transaction_type', 'amount', 'risk_score', 'decision']].head(20)
            display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:,.2f}")
            display_df['risk_score'] = display_df['risk_score'].apply(lambda x: f"{x:.3f}")

            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.success("No high-risk transactions found!")

    finally:
        db.close()
