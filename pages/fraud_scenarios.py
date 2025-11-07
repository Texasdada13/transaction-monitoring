"""Fraud Scenario Analysis Page"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
from datetime import datetime
from app.models.database import get_db, Transaction, RiskAssessment, AccountChangeHistory, BeneficiaryChangeHistory

def show():
    st.header("🔍 Fraud Scenario Analysis")
    st.markdown("Deep dive into different fraud detection scenarios")

    db = next(get_db())
    try:
        # Get all assessments with triggered rules
        assessments = db.query(RiskAssessment).all()
        transactions = db.query(Transaction).all()

        if not assessments:
            st.warning("No risk assessment data available.")
            return

        # Parse triggered rules and categorize by scenario
        scenario_data = {
            'Payroll Fraud': {'count': 0, 'total_risk': 0, 'high_risk': 0, 'rules': []},
            'Beneficiary Fraud': {'count': 0, 'total_risk': 0, 'high_risk': 0, 'rules': []},
            'Check Fraud': {'count': 0, 'total_risk': 0, 'high_risk': 0, 'rules': []},
            'Wire Fraud': {'count': 0, 'total_risk': 0, 'high_risk': 0, 'rules': []},
            'Account Takeover': {'count': 0, 'total_risk': 0, 'high_risk': 0, 'rules': []},
            'Other': {'count': 0, 'total_risk': 0, 'high_risk': 0, 'rules': []}
        }

        for assessment in assessments:
            triggered_rules = json.loads(assessment.triggered_rules) if assessment.triggered_rules else {}

            # Categorize by rule names
            scenario = 'Other'
            for rule_name in triggered_rules.keys():
                if 'payroll' in rule_name.lower():
                    scenario = 'Payroll Fraud'
                    break
                elif 'beneficiary' in rule_name.lower() or 'vendor' in rule_name.lower():
                    scenario = 'Beneficiary Fraud'
                    break
                elif 'check' in rule_name.lower():
                    scenario = 'Check Fraud'
                    break
                elif 'wire' in rule_name.lower():
                    scenario = 'Wire Fraud'
                    break
                elif 'takeover' in rule_name.lower():
                    scenario = 'Account Takeover'
                    break

            scenario_data[scenario]['count'] += 1
            scenario_data[scenario]['total_risk'] += assessment.risk_score
            if assessment.risk_score > 0.6:
                scenario_data[scenario]['high_risk'] += 1
            scenario_data[scenario]['rules'].extend(triggered_rules.keys())

        # Calculate averages
        for scenario in scenario_data.values():
            if scenario['count'] > 0:
                scenario['avg_risk'] = scenario['total_risk'] / scenario['count']
            else:
                scenario['avg_risk'] = 0

        # Display scenario tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Overview",
            "💼 Payroll Fraud",
            "🏢 Beneficiary Fraud",
            "📝 Check Fraud",
            "💸 Wire Fraud",
            "🔐 Account Takeover"
        ])

        with tab1:
            st.subheader("Fraud Scenario Overview")

            # Scenario comparison metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                total_scenarios = sum(s['count'] for s in scenario_data.values())
                st.metric("Total Flagged Transactions", f"{total_scenarios:,}")

            with col2:
                total_high_risk = sum(s['high_risk'] for s in scenario_data.values())
                st.metric("High Risk Cases", f"{total_high_risk:,}")

            with col3:
                overall_avg_risk = sum(s['total_risk'] for s in scenario_data.values()) / max(total_scenarios, 1)
                st.metric("Overall Avg Risk", f"{overall_avg_risk:.3f}")

            # Scenario distribution chart
            st.markdown("---")
            scenario_names = list(scenario_data.keys())
            scenario_counts = [scenario_data[s]['count'] for s in scenario_names]

            col1, col2 = st.columns(2)

            with col1:
                fig = go.Figure(data=[go.Bar(
                    x=scenario_names,
                    y=scenario_counts,
                    marker_color=['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#95a5a6']
                )])
                fig.update_layout(
                    title='Transactions by Fraud Scenario',
                    xaxis_title='Scenario',
                    yaxis_title='Count',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                avg_risks = [scenario_data[s]['avg_risk'] for s in scenario_names]
                fig = go.Figure(data=[go.Bar(
                    x=scenario_names,
                    y=avg_risks,
                    marker_color=['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#95a5a6']
                )])
                fig.update_layout(
                    title='Average Risk Score by Scenario',
                    xaxis_title='Scenario',
                    yaxis_title='Avg Risk Score',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("💼 Payroll Fraud Detection")
            _show_scenario_details(db, 'Payroll Fraud', scenario_data['Payroll Fraud'])

        with tab3:
            st.subheader("🏢 Beneficiary Fraud Detection")
            _show_scenario_details(db, 'Beneficiary Fraud', scenario_data['Beneficiary Fraud'])

        with tab4:
            st.subheader("📝 Check Fraud Detection")
            _show_scenario_details(db, 'Check Fraud', scenario_data['Check Fraud'])

        with tab5:
            st.subheader("💸 Wire Fraud Detection")
            _show_scenario_details(db, 'Wire Fraud', scenario_data['Wire Fraud'])

        with tab6:
            st.subheader("🔐 Account Takeover Detection")
            _show_scenario_details(db, 'Account Takeover', scenario_data['Account Takeover'])

    finally:
        db.close()


def _show_scenario_details(db, scenario_name, scenario_info):
    """Show detailed information for a specific scenario."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Cases", scenario_info['count'])
    with col2:
        st.metric("High Risk", scenario_info['high_risk'])
    with col3:
        st.metric("Avg Risk Score", f"{scenario_info['avg_risk']:.3f}")
    with col4:
        high_risk_pct = (scenario_info['high_risk'] / max(scenario_info['count'], 1) * 100)
        st.metric("High Risk %", f"{high_risk_pct:.1f}%")

    if scenario_info['count'] == 0:
        st.info(f"No {scenario_name} cases detected in the current data.")
        return

    # Show most common rules for this scenario
    st.markdown("---")
    st.subheader("Most Triggered Rules")

    rule_counts = {}
    for rule in scenario_info['rules']:
        rule_counts[rule] = rule_counts.get(rule, 0) + 1

    if rule_counts:
        sorted_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        for i, (rule, count) in enumerate(sorted_rules, 1):
            st.markdown(f"**{i}. {rule}** - Triggered {count} times")
    else:
        st.info("No specific rules available for this scenario.")
