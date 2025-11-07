"""Manual Review Queue Page"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
from datetime import datetime
from app.models.database import get_db, Transaction, RiskAssessment

def show():
    st.header("👥 Manual Review Queue")
    st.markdown("Transactions pending manual review and analysis")

    db = next(get_db())
    try:
        # Get all manual review cases
        manual_reviews = db.query(RiskAssessment).filter(
            RiskAssessment.decision == "manual_review"
        ).all()

        if not manual_reviews:
            st.success("✅ No transactions pending manual review!")
            return

        # Get pending vs completed
        pending = [r for r in manual_reviews if r.review_status == "pending"]
        approved = [r for r in manual_reviews if r.review_status == "approved"]
        rejected = [r for r in manual_reviews if r.review_status == "rejected"]

        # Top metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Manual Review", len(manual_reviews))
        with col2:
            st.metric("⏳ Pending", len(pending), delta=f"{len(pending)/max(len(manual_reviews),1)*100:.0f}%")
        with col3:
            st.metric("✅ Approved", len(approved))
        with col4:
            st.metric("❌ Rejected", len(rejected))

        st.markdown("---")

        # Review status distribution
        col1, col2 = st.columns(2)

        with col1:
            status_counts = {
                'Pending': len(pending),
                'Approved': len(approved),
                'Rejected': len(rejected)
            }

            fig = go.Figure(data=[go.Pie(
                labels=list(status_counts.keys()),
                values=list(status_counts.values()),
                marker=dict(colors=['#f39c12', '#2ecc71', '#e74c3c']),
                hole=0.4
            )])
            fig.update_layout(
                title='Review Status Distribution',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Risk score distribution for manual reviews
            risk_scores = [r.risk_score for r in manual_reviews]

            fig = px.histogram(
                x=risk_scores,
                nbins=20,
                color_discrete_sequence=['#e74c3c']
            )
            fig.update_layout(
                title='Risk Score Distribution (Manual Review)',
                xaxis_title='Risk Score',
                yaxis_title='Count',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        # Pending queue details
        if pending:
            st.markdown("---")
            st.subheader("⏳ Pending Review Queue")
            st.markdown(f"**{len(pending)} transactions** require immediate review")

            # Build pending queue table
            queue_data = []
            for assessment in sorted(pending, key=lambda x: x.risk_score, reverse=True):
                tx = db.query(Transaction).filter(
                    Transaction.transaction_id == assessment.transaction_id
                ).first()

                if tx:
                    triggered_rules = json.loads(assessment.triggered_rules) if assessment.triggered_rules else {}

                    queue_data.append({
                        'Transaction ID': tx.transaction_id[:16] + '...',
                        'Type': tx.transaction_type,
                        'Amount': f"${tx.amount:,.2f}",
                        'Risk Score': f"{assessment.risk_score:.3f}",
                        'Triggered Rules': len(triggered_rules),
                        'Timestamp': datetime.fromisoformat(tx.timestamp).strftime('%Y-%m-%d %H:%M')
                    })

            queue_df = pd.DataFrame(queue_data)

            # Color code by risk score
            def highlight_risk(row):
                risk = float(row['Risk Score'])
                if risk >= 0.7:
                    return ['background-color: #ffebee'] * len(row)
                elif risk >= 0.5:
                    return ['background-color: #fff9e6'] * len(row)
                else:
                    return [''] * len(row)

            st.dataframe(
                queue_df.head(20),
                use_container_width=True,
                hide_index=True
            )

            # Detailed view for top priority items
            st.markdown("---")
            st.subheader("🔍 Top Priority Items (Highest Risk)")

            for i, assessment in enumerate(sorted(pending, key=lambda x: x.risk_score, reverse=True)[:5], 1):
                tx = db.query(Transaction).filter(
                    Transaction.transaction_id == assessment.transaction_id
                ).first()

                if tx:
                    with st.expander(f"#{i} - {tx.transaction_id} (Risk: {assessment.risk_score:.3f})"):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("**Transaction Details:**")
                            st.write(f"- Type: {tx.transaction_type}")
                            st.write(f"- Amount: ${tx.amount:,.2f}")
                            st.write(f"- Direction: {tx.direction}")
                            st.write(f"- Counterparty: {tx.counterparty_id}")
                            st.write(f"- Timestamp: {tx.timestamp}")

                        with col2:
                            st.markdown("**Risk Assessment:**")
                            st.write(f"- Risk Score: {assessment.risk_score:.3f}")
                            st.write(f"- Decision: {assessment.decision}")

                            triggered_rules = json.loads(assessment.triggered_rules) if assessment.triggered_rules else {}
                            if triggered_rules:
                                st.markdown("**Triggered Rules:**")
                                for rule_name, rule_info in list(triggered_rules.items())[:5]:
                                    st.write(f"- {rule_info.get('description', rule_name)} (weight: {rule_info.get('weight', 0)})")

        else:
            st.success("✅ All manual review items have been processed!")

    finally:
        db.close()
