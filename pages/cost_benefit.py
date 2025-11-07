"""Cost-Benefit Analysis Page"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from app.models.database import get_db, Transaction, RiskAssessment

def show():
    st.header("💰 Cost-Benefit Analysis")
    st.markdown("Analyze the financial impact and ROI of fraud detection")

    db = next(get_db())
    try:
        transactions = db.query(Transaction).all()
        assessments = db.query(RiskAssessment).all()

        if not assessments:
            st.warning("No risk assessment data available.")
            return

        # Configurable parameters
        st.sidebar.markdown("---")
        st.sidebar.subheader("Cost Parameters")

        review_cost = st.sidebar.number_input(
            "Manual Review Cost ($)",
            min_value=1.0,
            max_value=100.0,
            value=18.75,
            step=0.25,
            help="Cost per manual review"
        )

        fraud_prevention_rate = st.sidebar.slider(
            "Fraud Prevention Rate (%)",
            min_value=50,
            max_value=100,
            value=85,
            help="Percentage of fraud caught by manual review"
        )

        # Merge data
        tx_data = [{
            'transaction_id': tx.transaction_id,
            'amount': tx.amount,
            'transaction_type': tx.transaction_type
        } for tx in transactions]
        tx_df = pd.DataFrame(tx_data)

        assess_data = [{
            'transaction_id': a.transaction_id,
            'risk_score': a.risk_score,
            'decision': a.decision
        } for a in assessments]
        assess_df = pd.DataFrame(assess_data)

        df = tx_df.merge(assess_df, on='transaction_id', how='left')

        # Calculate costs and benefits
        total_txs = len(df)
        manual_reviews = len(df[df['decision'] == 'manual_review'])
        auto_approved = len(df[df['decision'] == 'auto_approve'])

        total_review_cost = manual_reviews * review_cost

        # Estimate potential fraud (transactions with risk > 0.6)
        high_risk_txs = df[df['risk_score'] > 0.6]
        potential_fraud_amount = high_risk_txs['amount'].sum()

        # Estimated fraud prevented (only from manual review catches)
        fraud_prevented = potential_fraud_amount * (fraud_prevention_rate / 100)

        net_benefit = fraud_prevented - total_review_cost
        roi = ((net_benefit / max(total_review_cost, 1)) * 100) if total_review_cost > 0 else 0

        # Top level metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Review Cost",
                f"${total_review_cost:,.2f}",
                f"{manual_reviews} reviews"
            )
        with col2:
            st.metric(
                "Fraud Prevented",
                f"${fraud_prevented:,.2f}",
                f"{fraud_prevention_rate}% rate"
            )
        with col3:
            st.metric(
                "Net Benefit",
                f"${net_benefit:,.2f}",
                "Savings"
            )
        with col4:
            st.metric(
                "ROI",
                f"{roi:.1f}%",
                "Return on Investment"
            )

        st.markdown("---")

        # Cost breakdown
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Cost Breakdown")

            cost_data = pd.DataFrame({
                'Category': ['Review Costs', 'Fraud Prevented', 'Net Savings'],
                'Amount': [total_review_cost, fraud_prevented, net_benefit],
                'Color': ['#e74c3c', '#2ecc71', '#3498db']
            })

            fig = go.Figure(data=[go.Bar(
                x=cost_data['Category'],
                y=cost_data['Amount'],
                marker_color=cost_data['Color']
            )])
            fig.update_layout(
                title='Financial Impact',
                yaxis_title='Amount ($)',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("🎯 Decision Distribution")

            decision_data = pd.DataFrame({
                'Decision': ['Auto-Approved', 'Manual Review'],
                'Count': [auto_approved, manual_reviews],
                'Percentage': [
                    f"{auto_approved/total_txs*100:.1f}%",
                    f"{manual_reviews/total_txs*100:.1f}%"
                ]
            })

            fig = go.Figure(data=[go.Pie(
                labels=decision_data['Decision'],
                values=decision_data['Count'],
                marker=dict(colors=['#2ecc71', '#f39c12']),
                hole=0.4,
                textinfo='label+percent'
            )])
            fig.update_layout(
                title='Review Distribution',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        # Cost per risk threshold
        st.markdown("---")
        st.subheader("📈 Cost-Benefit by Risk Threshold")
        st.markdown("Analyze how different risk thresholds affect costs and fraud prevention")

        # Calculate costs for different thresholds
        thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        threshold_analysis = []

        for threshold in thresholds:
            manual_count = len(df[df['risk_score'] >= threshold])
            auto_count = total_txs - manual_count

            cost = manual_count * review_cost

            # Fraud caught (higher threshold = more fraud slips through)
            caught_fraud = df[df['risk_score'] >= threshold]['amount'].sum() * (fraud_prevention_rate / 100)

            # Missed fraud (below threshold)
            missed_fraud = df[(df['risk_score'] >= 0.6) & (df['risk_score'] < threshold)]['amount'].sum()

            net = caught_fraud - cost

            threshold_analysis.append({
                'Threshold': threshold,
                'Manual Reviews': manual_count,
                'Review Cost': cost,
                'Fraud Caught': caught_fraud,
                'Fraud Missed': missed_fraud,
                'Net Benefit': net
            })

        threshold_df = pd.DataFrame(threshold_analysis)

        # Plot threshold analysis
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=threshold_df['Threshold'],
            y=threshold_df['Review Cost'],
            name='Review Cost',
            line=dict(color='#e74c3c', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=threshold_df['Threshold'],
            y=threshold_df['Fraud Caught'],
            name='Fraud Caught',
            line=dict(color='#2ecc71', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=threshold_df['Threshold'],
            y=threshold_df['Net Benefit'],
            name='Net Benefit',
            line=dict(color='#3498db', width=2, dash='dash')
        ))

        fig.update_layout(
            title='Cost-Benefit Analysis by Risk Threshold',
            xaxis_title='Risk Score Threshold',
            yaxis_title='Amount ($)',
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Detailed threshold table
        st.markdown("---")
        st.subheader("📋 Detailed Threshold Analysis")

        display_df = threshold_df.copy()
        display_df['Review Cost'] = display_df['Review Cost'].apply(lambda x: f"${x:,.2f}")
        display_df['Fraud Caught'] = display_df['Fraud Caught'].apply(lambda x: f"${x:,.2f}")
        display_df['Fraud Missed'] = display_df['Fraud Missed'].apply(lambda x: f"${x:,.2f}")
        display_df['Net Benefit'] = display_df['Net Benefit'].apply(lambda x: f"${x:,.2f}")

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Recommendations
        st.markdown("---")
        st.subheader("💡 Recommendations")

        optimal_threshold = threshold_df.loc[threshold_df['Net Benefit'].idxmax(), 'Threshold']

        col1, col2, col3 = st.columns(3)

        with col1:
            st.success(f"**Optimal Threshold:** {optimal_threshold}")
            st.write("Maximizes net benefit")

        with col2:
            current_threshold = 0.6  # Default threshold
            current_benefit = threshold_df[threshold_df['Threshold'] == current_threshold]['Net Benefit'].values[0]
            st.info(f"**Current Threshold:** {current_threshold}")
            st.write(f"Net benefit: ${current_benefit:,.2f}")

        with col3:
            if optimal_threshold != current_threshold:
                improvement = threshold_df.loc[threshold_df['Threshold'] == optimal_threshold, 'Net Benefit'].values[0] - current_benefit
                st.warning(f"**Potential Improvement:** ${improvement:,.2f}")
                st.write(f"By switching to {optimal_threshold}")
            else:
                st.success("**Already Optimal!**")
                st.write("Current threshold is best")

    finally:
        db.close()
