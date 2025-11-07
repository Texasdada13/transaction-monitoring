"""Transaction Velocity Analysis Page"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from app.models.database import get_db, Transaction

def show():
    st.header("⚡ Transaction Velocity Analysis")
    st.markdown("Analyze transaction patterns, volumes, and temporal anomalies")

    db = next(get_db())
    try:
        transactions = db.query(Transaction).all()

        if not transactions:
            st.warning("No transaction data available.")
            return

        # Convert to DataFrame
        tx_data = [{
            'transaction_id': tx.transaction_id,
            'timestamp': datetime.fromisoformat(tx.timestamp),
            'amount': tx.amount,
            'transaction_type': tx.transaction_type,
            'direction': tx.direction,
            'counterparty_id': tx.counterparty_id,
            'account_id': tx.account_id
        } for tx in transactions]
        df = pd.DataFrame(tx_data)

        # Add temporal features
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_name()

        # Top metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Transactions", f"{len(df):,}")
        with col2:
            daily_avg = len(df) / max(df['date'].nunique(), 1)
            st.metric("Daily Average", f"{daily_avg:.1f}")
        with col3:
            hourly_avg = len(df) / (df['date'].nunique() * 24)
            st.metric("Hourly Average", f"{hourly_avg:.2f}")
        with col4:
            unique_counterparties = df['counterparty_id'].nunique()
            st.metric("Unique Counterparties", unique_counterparties)

        st.markdown("---")

        # Transaction volume over time
        st.subheader("📅 Transaction Volume Trends")

        tab1, tab2, tab3 = st.tabs(["Daily", "Hourly", "Day of Week"])

        with tab1:
            daily_volume = df.groupby('date').agg({
                'transaction_id': 'count',
                'amount': 'sum'
            }).reset_index()
            daily_volume.columns = ['date', 'count', 'total_amount']

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=daily_volume['date'],
                y=daily_volume['count'],
                name='Transaction Count',
                marker_color='#3498db'
            ))
            fig.update_layout(
                title='Daily Transaction Volume',
                xaxis_title='Date',
                yaxis_title='Number of Transactions',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            hourly_volume = df.groupby('hour').size().reset_index(name='count')

            fig = go.Figure(data=[go.Bar(
                x=hourly_volume['hour'],
                y=hourly_volume['count'],
                marker_color='#2ecc71'
            )])
            fig.update_layout(
                title='Transaction Distribution by Hour of Day',
                xaxis_title='Hour (24h)',
                yaxis_title='Number of Transactions',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

            # Highlight off-hours activity
            off_hours = df[(df['hour'] < 6) | (df['hour'] > 22)]
            if len(off_hours) > 0:
                st.warning(f"⚠️ {len(off_hours)} transactions ({len(off_hours)/len(df)*100:.1f}%) occurred during off-hours (10 PM - 6 AM)")

        with tab3:
            # Order days of week
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dow_volume = df.groupby('day_of_week').size().reset_index(name='count')
            dow_volume['day_of_week'] = pd.Categorical(dow_volume['day_of_week'], categories=day_order, ordered=True)
            dow_volume = dow_volume.sort_values('day_of_week')

            fig = go.Figure(data=[go.Bar(
                x=dow_volume['day_of_week'],
                y=dow_volume['count'],
                marker_color=['#3498db' if day not in ['Saturday', 'Sunday'] else '#e74c3c'
                             for day in dow_volume['day_of_week']]
            )])
            fig.update_layout(
                title='Transaction Distribution by Day of Week',
                xaxis_title='Day',
                yaxis_title='Number of Transactions',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

            # Weekend transactions
            weekend_txs = df[df['day_of_week'].isin(['Saturday', 'Sunday'])]
            if len(weekend_txs) > 0:
                st.info(f"ℹ️ {len(weekend_txs)} transactions ({len(weekend_txs)/len(df)*100:.1f}%) occurred on weekends")

        # Velocity metrics
        st.markdown("---")
        st.subheader("⚡ Velocity Metrics")

        col1, col2 = st.columns(2)

        with col1:
            # Transactions per account
            st.markdown("**Top 10 Most Active Accounts**")
            account_velocity = df.groupby('account_id').agg({
                'transaction_id': 'count',
                'amount': 'sum'
            }).reset_index()
            account_velocity.columns = ['account_id', 'tx_count', 'total_amount']
            account_velocity = account_velocity.sort_values('tx_count', ascending=False).head(10)

            fig = go.Figure(data=[go.Bar(
                y=account_velocity['account_id'],
                x=account_velocity['tx_count'],
                orientation='h',
                marker_color='#9b59b6'
            )])
            fig.update_layout(
                title='Transaction Count by Account',
                xaxis_title='Number of Transactions',
                yaxis_title='Account ID',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # New counterparties over time
            st.markdown("**New Counterparties Trend**")
            df_sorted = df.sort_values('timestamp')
            df_sorted['new_counterparty'] = ~df_sorted['counterparty_id'].duplicated()
            daily_new_counterparties = df_sorted[df_sorted['new_counterparty']].groupby('date').size().reset_index(name='new_count')

            fig = go.Figure(data=[go.Scatter(
                x=daily_new_counterparties['date'],
                y=daily_new_counterparties['new_count'],
                mode='lines+markers',
                marker_color='#e74c3c'
            )])
            fig.update_layout(
                title='New Counterparties per Day',
                xaxis_title='Date',
                yaxis_title='New Counterparties',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        # Transaction bursts
        st.markdown("---")
        st.subheader("💥 Transaction Burst Detection")

        # Define burst as 5+ transactions within 1 hour for same account
        df['timestamp_hour'] = df['timestamp'].dt.floor('H')
        hourly_by_account = df.groupby(['account_id', 'timestamp_hour']).size().reset_index(name='count')
        bursts = hourly_by_account[hourly_by_account['count'] >= 5].sort_values('count', ascending=False)

        if len(bursts) > 0:
            st.warning(f"⚠️ Detected {len(bursts)} potential transaction bursts (5+ transactions in 1 hour)")

            burst_df = bursts.head(10).copy()
            burst_df['timestamp_hour'] = burst_df['timestamp_hour'].dt.strftime('%Y-%m-%d %H:%M')
            burst_df.columns = ['Account ID', 'Time Window', 'Transaction Count']

            st.dataframe(burst_df, use_container_width=True, hide_index=True)
        else:
            st.success("✅ No unusual transaction bursts detected")

        # Amount velocity
        st.markdown("---")
        st.subheader("💰 Amount Velocity Analysis")

        daily_amounts = df.groupby('date').agg({
            'amount': ['sum', 'mean', 'max']
        }).reset_index()
        daily_amounts.columns = ['date', 'total', 'average', 'maximum']

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_amounts['date'],
            y=daily_amounts['total'],
            name='Total Daily Amount',
            fill='tozeroy',
            line=dict(color='#3498db')
        ))
        fig.update_layout(
            title='Daily Transaction Amount',
            xaxis_title='Date',
            yaxis_title='Amount ($)',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    finally:
        db.close()
