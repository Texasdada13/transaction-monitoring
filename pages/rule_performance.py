"""Rule Performance Dashboard Page"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
from collections import Counter
from app.models.database import get_db, RiskAssessment

def show():
    st.header("📋 Rule Performance")
    st.markdown("Analysis of fraud detection rule effectiveness")

    db = next(get_db())
    try:
        assessments = db.query(RiskAssessment).all()

        if not assessments:
            st.warning("No risk assessment data available.")
            return

        # Collect all triggered rules
        all_rules = []
        rule_details = {}

        for assessment in assessments:
            triggered_rules = json.loads(assessment.triggered_rules) if assessment.triggered_rules else {}

            for rule_name, rule_info in triggered_rules.items():
                all_rules.append(rule_name)
                if rule_name not in rule_details:
                    rule_details[rule_name] = {
                        'description': rule_info.get('description', rule_name),
                        'weight': rule_info.get('weight', 0),
                        'count': 0,
                        'avg_risk': 0,
                        'total_risk': 0
                    }
                rule_details[rule_name]['count'] += 1
                rule_details[rule_name]['total_risk'] += assessment.risk_score

        # Calculate averages
        for rule in rule_details.values():
            if rule['count'] > 0:
                rule['avg_risk'] = rule['total_risk'] / rule['count']

        # Top metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Rules", len(rule_details))
        with col2:
            st.metric("Total Triggers", len(all_rules))
        with col3:
            avg_triggers_per_tx = len(all_rules) / max(len(assessments), 1)
            st.metric("Avg Triggers per Transaction", f"{avg_triggers_per_tx:.2f}")

        st.markdown("---")

        # Top triggered rules
        st.subheader("🔝 Top 10 Most Triggered Rules")

        sorted_rules = sorted(
            rule_details.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:10]

        # Create DataFrame for visualization
        top_rules_df = pd.DataFrame([
            {
                'Rule': r[1]['description'][:50] + '...' if len(r[1]['description']) > 50 else r[1]['description'],
                'Trigger Count': r[1]['count'],
                'Weight': r[1]['weight'],
                'Avg Risk': r[1]['avg_risk']
            }
            for r in sorted_rules
        ])

        col1, col2 = st.columns(2)

        with col1:
            fig = go.Figure(data=[go.Bar(
                y=top_rules_df['Rule'],
                x=top_rules_df['Trigger Count'],
                orientation='h',
                marker_color='#3498db'
            )])
            fig.update_layout(
                title='Top Rules by Trigger Count',
                xaxis_title='Number of Triggers',
                yaxis_title='',
                height=500,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = go.Figure(data=[go.Bar(
                y=top_rules_df['Rule'],
                x=top_rules_df['Avg Risk'],
                orientation='h',
                marker_color='#e74c3c'
            )])
            fig.update_layout(
                title='Average Risk Score When Triggered',
                xaxis_title='Average Risk Score',
                yaxis_title='',
                height=500,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig, use_container_width=True)

        # Rule weight distribution
        st.markdown("---")
        st.subheader("⚖️ Rule Weight Distribution")

        weights = [r[1]['weight'] for r in sorted_rules]
        fig = px.histogram(
            x=weights,
            nbins=10,
            title='Distribution of Rule Weights',
            labels={'x': 'Rule Weight', 'count': 'Number of Rules'},
            color_discrete_sequence=['#2ecc71']
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

        # Detailed rule table
        st.markdown("---")
        st.subheader("📊 Detailed Rule Statistics")

        detailed_df = pd.DataFrame([
            {
                'Rule Name': r[0],
                'Description': r[1]['description'],
                'Trigger Count': r[1]['count'],
                'Weight': r[1]['weight'],
                'Avg Risk Score': f"{r[1]['avg_risk']:.3f}"
            }
            for r in sorted_rules
        ])

        st.dataframe(detailed_df, use_container_width=True, hide_index=True)

        # Rule combinations
        st.markdown("---")
        st.subheader("🔗 Common Rule Combinations")

        # Find transactions with multiple rules
        multi_rule_txs = []
        for assessment in assessments:
            triggered_rules = json.loads(assessment.triggered_rules) if assessment.triggered_rules else {}
            if len(triggered_rules) > 1:
                rule_names = sorted(triggered_rules.keys())
                multi_rule_txs.append(tuple(rule_names[:3]))  # Top 3 rules per transaction

        if multi_rule_txs:
            combo_counts = Counter(multi_rule_txs).most_common(5)

            st.markdown("**Top 5 Rule Combinations:**")
            for i, (combo, count) in enumerate(combo_counts, 1):
                combo_str = " + ".join([r.replace('_', ' ').title()[:30] for r in combo])
                st.markdown(f"**{i}.** {combo_str} - {count} occurrences")
        else:
            st.info("No multi-rule combinations found.")

    finally:
        db.close()
