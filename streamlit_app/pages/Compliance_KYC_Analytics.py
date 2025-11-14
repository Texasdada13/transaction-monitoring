"""
Compliance & KYC Analytics Dashboard

Comprehensive compliance analytics covering:
- Customer compliance lifecycle timelines
- Analyst decision retrospectives
- Rule effectiveness reviews
- Audit trail reporting
- Segment benchmarking
- Risk evolution tracking
- False positive analysis
- Regulatory compliance dashboards
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from pathlib import Path

from streamlit_app.theme import apply_master_theme, render_page_header, get_chart_colors


def load_compliance_data():
    """Load all compliance datasets"""
    try:
        # Use absolute path from project root
        data_dir = Path(__file__).parent.parent.parent / "compliance_dataset"

        if not data_dir.exists():
            st.error(f"Compliance dataset directory not found at: {data_dir}")
            st.info("Run `python generate_compliance_dataset.py` from the project root to generate the dataset.")
            return None

        customers_df = pd.read_csv(str(data_dir / "customer_profiles.csv"))
        transactions_df = pd.read_csv(str(data_dir / "transactions.csv"))
        kyc_events_df = pd.read_csv(str(data_dir / "kyc_events.csv"))
        cdd_events_df = pd.read_csv(str(data_dir / "cdd_events.csv"))
        edd_actions_df = pd.read_csv(str(data_dir / "edd_actions.csv"))
        alerts_df = pd.read_csv(str(data_dir / "alerts_analyst_actions.csv"))
        rule_executions_df = pd.read_csv(str(data_dir / "rule_executions.csv"))
        audit_trail_df = pd.read_csv(str(data_dir / "audit_trail.csv"))

        # Convert date columns
        transactions_df['timestamp'] = pd.to_datetime(transactions_df['timestamp'])
        kyc_events_df['kyc_check_date'] = pd.to_datetime(kyc_events_df['kyc_check_date'])
        cdd_events_df['event_date'] = pd.to_datetime(cdd_events_df['event_date'])
        edd_actions_df['investigation_start'] = pd.to_datetime(edd_actions_df['investigation_start'])
        edd_actions_df['investigation_end'] = pd.to_datetime(edd_actions_df['investigation_end'])
        alerts_df['alert_timestamp'] = pd.to_datetime(alerts_df['alert_timestamp'])
        alerts_df['decision_timestamp'] = pd.to_datetime(alerts_df['decision_timestamp'])
        rule_executions_df['timestamp'] = pd.to_datetime(rule_executions_df['timestamp'])
        audit_trail_df['timestamp'] = pd.to_datetime(audit_trail_df['timestamp'])

        return {
            'customers': customers_df,
            'transactions': transactions_df,
            'kyc_events': kyc_events_df,
            'cdd_events': cdd_events_df,
            'edd_actions': edd_actions_df,
            'alerts': alerts_df,
            'rule_executions': rule_executions_df,
            'audit_trail': audit_trail_df
        }
    except Exception as e:
        st.error(f"Error loading compliance data: {e}")
        st.info("Failed to load compliance data. Please ensure the dataset exists.")
        st.info("Run `python generate_compliance_dataset.py` to generate the dataset.")
        return None


def render_customer_lifecycle_timeline(data, colors):
    """1. Customer Compliance Lifecycle Timelines"""
    st.markdown("## 🔄 Customer Compliance Lifecycle Timeline")
    st.markdown("*Track customer journey through KYC, CDD, and EDD processes*")

    customers_df = data['customers']
    kyc_df = data['kyc_events']
    cdd_df = data['cdd_events']
    edd_df = data['edd_actions']

    # Customer selector
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_customer = st.selectbox(
            "Select Customer to View Lifecycle",
            customers_df['customer_id'].head(50).tolist(),
            format_func=lambda x: f"{x} - {customers_df[customers_df['customer_id']==x]['full_name'].values[0]}"
        )

    customer_info = customers_df[customers_df['customer_id'] == selected_customer].iloc[0]

    with col2:
        st.metric("Current Risk", customer_info['current_risk_level'].upper())
        st.metric("PEP Status", customer_info['PEP_status'])

    # Timeline visualization
    events = []

    # Add onboarding
    events.append({
        'date': pd.to_datetime(customer_info['onboarding_date']),
        'event': 'Customer Onboarding',
        'type': 'Onboarding',
        'details': f"Initial Risk: {customer_info['risk_level_initial']}"
    })

    # Add KYC events
    kyc_customer = kyc_df[kyc_df['customer_id'] == selected_customer]
    for _, kyc in kyc_customer.iterrows():
        events.append({
            'date': kyc['kyc_check_date'],
            'event': f"KYC Check: {kyc['document_type']}",
            'type': 'KYC',
            'details': f"Result: {kyc['result']}"
        })

    # Add CDD events
    cdd_customer = cdd_df[cdd_df['customer_id'] == selected_customer]
    for _, cdd in cdd_customer.iterrows():
        events.append({
            'date': cdd['event_date'],
            'event': f"CDD: {cdd['event_type']}",
            'type': 'CDD',
            'details': cdd['summary']
        })

    # Add EDD events
    edd_customer = edd_df[edd_df['customer_id'] == selected_customer]
    for _, edd in edd_customer.iterrows():
        events.append({
            'date': edd['investigation_start'],
            'event': f"EDD Investigation",
            'type': 'EDD',
            'details': f"Reason: {edd['edd_reason']}, Outcome: {edd['outcome']}"
        })

    timeline_df = pd.DataFrame(events).sort_values('date')

    if len(timeline_df) > 0:
        # Create timeline chart
        fig = px.scatter(timeline_df, x='date', y='type',
                        color='type', hover_data=['event', 'details'],
                        title=f"Compliance Timeline for {customer_info['full_name']}",
                        height=400)

        fig.update_traces(marker=dict(size=15, line=dict(width=2, color='white')))
        fig.update_layout(showlegend=True, hovermode='closest')

        st.plotly_chart(fig, use_container_width=True, key="lifecycle_timeline")

        # Event details table
        st.markdown("### Event History")
        st.dataframe(
            timeline_df[['date', 'event', 'details']].sort_values('date', ascending=False),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No compliance events found for this customer")


def render_analyst_retrospectives(data, colors):
    """2. Analyst Decision Retrospectives"""
    st.markdown("## 👥 Analyst Decision Retrospectives")
    st.markdown("*Analyze analyst performance and decision patterns*")

    alerts_df = data['alerts']

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_decisions = len(alerts_df)
        st.metric("Total Decisions", f"{total_decisions:,}")

    with col2:
        avg_decision_time = alerts_df['time_to_decision_hours'].mean()
        st.metric("Avg Decision Time", f"{avg_decision_time:.1f}h")

    with col3:
        false_positive_rate = (alerts_df['false_positive'].sum() / len(alerts_df)) * 100
        st.metric("False Positive Rate", f"{false_positive_rate:.1f}%")

    with col4:
        unique_analysts = alerts_df['analyst_id'].nunique()
        st.metric("Active Analysts", unique_analysts)

    # Analyst performance comparison
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Decisions by Analyst")
        analyst_decisions = alerts_df.groupby(['analyst_id', 'analyst_decision']).size().unstack(fill_value=0)

        fig = go.Figure()
        for decision in analyst_decisions.columns:
            fig.add_trace(go.Bar(
                name=decision,
                x=analyst_decisions.index,
                y=analyst_decisions[decision]
            ))

        fig.update_layout(
            barmode='stack',
            height=400,
            xaxis_title="Analyst",
            yaxis_title="Number of Decisions",
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True, key="analyst_decisions")

    with col2:
        st.markdown("### Average Decision Time by Analyst")
        analyst_time = alerts_df.groupby('analyst_id')['time_to_decision_hours'].mean().sort_values()

        fig = go.Figure(go.Bar(
            x=analyst_time.values,
            y=analyst_time.index,
            orientation='h',
            marker_color=colors['primary']
        ))

        fig.update_layout(
            height=400,
            xaxis_title="Average Hours",
            yaxis_title="Analyst"
        )

        st.plotly_chart(fig, use_container_width=True, key="analyst_time")

    # Decision accuracy analysis
    st.markdown("### Decision Accuracy Matrix")

    accuracy_data = alerts_df.groupby('analyst_id').agg({
        'alert_id': 'count',
        'false_positive': lambda x: (x.sum() / len(x)) * 100,
        'time_to_decision_hours': 'mean'
    }).round(2)

    accuracy_data.columns = ['Total Decisions', 'False Positive Rate (%)', 'Avg Time (hours)']
    accuracy_data = accuracy_data.sort_values('Total Decisions', ascending=False)

    st.dataframe(
        accuracy_data,
        use_container_width=True,
        column_config={
            'False Positive Rate (%)': st.column_config.ProgressColumn(
                'False Positive Rate (%)',
                min_value=0,
                max_value=100,
                format='%.1f%%'
            )
        }
    )


def render_rule_effectiveness(data, colors):
    """3. Rule Effectiveness Reviews"""
    st.markdown("## ⚖️ Rule Effectiveness Reviews")
    st.markdown("*Evaluate fraud detection rule performance and optimization*")

    rule_df = data['rule_executions']
    alerts_df = data['alerts']

    # Overall rule metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_executions = len(rule_df)
        st.metric("Total Rule Executions", f"{total_executions:,}")

    with col2:
        trigger_rate = (rule_df['rule_triggered'].sum() / len(rule_df)) * 100
        st.metric("Trigger Rate", f"{trigger_rate:.2f}%")

    with col3:
        avg_score = rule_df[rule_df['rule_triggered']]['rule_score'].mean()
        st.metric("Avg Trigger Score", f"{avg_score:.3f}")

    with col4:
        avg_exec_time = rule_df['execution_time_ms'].mean()
        st.metric("Avg Execution Time", f"{avg_exec_time:.1f}ms")

    # Rule trigger frequency
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Top Triggered Rules")
        rule_triggers = rule_df[rule_df['rule_triggered']].groupby('rule_name').size().sort_values(ascending=False).head(15)

        fig = go.Figure(go.Bar(
            x=rule_triggers.values,
            y=rule_triggers.index,
            orientation='h',
            marker_color=colors['warning']
        ))

        fig.update_layout(
            height=500,
            xaxis_title="Trigger Count",
            yaxis_title="Rule Name"
        )

        st.plotly_chart(fig, use_container_width=True, key="rule_triggers")

    with col2:
        st.markdown("### Rule Performance Scores")
        rule_scores = rule_df[rule_df['rule_triggered']].groupby('rule_name')['rule_score'].mean().sort_values(ascending=False).head(15)

        fig = go.Figure(go.Bar(
            x=rule_scores.values,
            y=rule_scores.index,
            orientation='h',
            marker_color=colors['success']
        ))

        fig.update_layout(
            height=500,
            xaxis_title="Average Score",
            yaxis_title="Rule Name"
        )

        st.plotly_chart(fig, use_container_width=True, key="rule_scores")

    # Rule execution time analysis
    st.markdown("### Rule Execution Time Distribution")

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=rule_df['execution_time_ms'],
        nbinsx=50,
        marker_color=colors['primary'],
        opacity=0.7
    ))

    fig.update_layout(
        height=300,
        xaxis_title="Execution Time (ms)",
        yaxis_title="Frequency",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True, key="exec_time_dist")


def render_audit_trail(data, colors):
    """4. Audit Trail Reporting"""
    st.markdown("## 📋 Audit Trail Reporting")
    st.markdown("*Complete audit history with filtering and search*")

    audit_df = data['audit_trail']

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        action_filter = st.multiselect(
            "Filter by Action Type",
            options=audit_df['audit_action'].unique(),
            default=[]
        )

    with col2:
        user_filter = st.multiselect(
            "Filter by User",
            options=audit_df['performed_by'].unique(),
            default=[]
        )

    with col3:
        date_range = st.date_input(
            "Date Range",
            value=(audit_df['timestamp'].min().date(), audit_df['timestamp'].max().date())
        )

    # Apply filters
    filtered_audit = audit_df.copy()
    if action_filter:
        filtered_audit = filtered_audit[filtered_audit['audit_action'].isin(action_filter)]
    if user_filter:
        filtered_audit = filtered_audit[filtered_audit['performed_by'].isin(user_filter)]
    if len(date_range) == 2:
        filtered_audit = filtered_audit[
            (filtered_audit['timestamp'].dt.date >= date_range[0]) &
            (filtered_audit['timestamp'].dt.date <= date_range[1])
        ]

    st.metric("Filtered Audit Entries", f"{len(filtered_audit):,}")

    # Audit timeline
    st.markdown("### Audit Activity Timeline")

    audit_daily = filtered_audit.groupby(filtered_audit['timestamp'].dt.date).size()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=audit_daily.index,
        y=audit_daily.values,
        mode='lines+markers',
        fill='tozeroy',
        marker_color=colors['primary']
    ))

    fig.update_layout(
        height=300,
        xaxis_title="Date",
        yaxis_title="Audit Entries",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True, key="audit_timeline")

    # Audit entries table
    st.markdown("### Recent Audit Entries")

    display_cols = ['timestamp', 'audit_action', 'performed_by', 'entity_type', 'entity_id', 'description']
    st.dataframe(
        filtered_audit[display_cols].sort_values('timestamp', ascending=False).head(100),
        use_container_width=True,
        hide_index=True,
        column_config={
            'timestamp': st.column_config.DatetimeColumn('Timestamp', format='YYYY-MM-DD HH:mm:ss')
        }
    )


def render_segment_benchmarking(data, colors):
    """5. Segment Benchmarking"""
    st.markdown("## 📊 Segment Benchmarking")
    st.markdown("*Compare compliance metrics across customer segments*")

    customers_df = data['customers']
    transactions_df = data['transactions']
    alerts_df = data['alerts']

    # Merge data for segment analysis
    trans_with_segment = transactions_df.merge(
        customers_df[['customer_id', 'segment', 'current_risk_level']],
        on='customer_id'
    )

    # Segment overview
    col1, col2, col3 = st.columns(3)

    segment_counts = customers_df['segment'].value_counts()

    with col1:
        st.markdown("### Retail")
        retail_count = segment_counts.get('Retail', 0)
        st.metric("Customers", f"{retail_count:,}")
        retail_high_risk = customers_df[(customers_df['segment']=='Retail') & (customers_df['current_risk_level']=='high')]
        st.metric("High Risk", f"{len(retail_high_risk)}")

    with col2:
        st.markdown("### Small Business")
        sb_count = segment_counts.get('Small Business', 0)
        st.metric("Customers", f"{sb_count:,}")
        sb_high_risk = customers_df[(customers_df['segment']=='Small Business') & (customers_df['current_risk_level']=='high')]
        st.metric("High Risk", f"{len(sb_high_risk)}")

    with col3:
        st.markdown("### Corporate")
        corp_count = segment_counts.get('Corporate', 0)
        st.metric("Customers", f"{corp_count:,}")
        corp_high_risk = customers_df[(customers_df['segment']=='Corporate') & (customers_df['current_risk_level']=='high')]
        st.metric("High Risk", f"{len(corp_high_risk)}")

    # Risk distribution by segment
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Risk Distribution by Segment")

        risk_by_segment = customers_df.groupby(['segment', 'current_risk_level']).size().unstack(fill_value=0)

        fig = go.Figure()
        for risk_level in ['low', 'medium', 'high']:
            if risk_level in risk_by_segment.columns:
                fig.add_trace(go.Bar(
                    name=risk_level.capitalize(),
                    x=risk_by_segment.index,
                    y=risk_by_segment[risk_level]
                ))

        fig.update_layout(
            barmode='group',
            height=400,
            xaxis_title="Segment",
            yaxis_title="Customer Count"
        )

        st.plotly_chart(fig, use_container_width=True, key="risk_by_segment")

    with col2:
        st.markdown("### Transaction Volume by Segment")

        trans_by_segment = trans_with_segment.groupby('segment').size()

        fig = go.Figure(go.Bar(
            x=trans_by_segment.index,
            y=trans_by_segment.values,
            marker_color=colors['primary']
        ))

        fig.update_layout(
            height=400,
            xaxis_title="Segment",
            yaxis_title="Transaction Count"
        )

        st.plotly_chart(fig, use_container_width=True, key="trans_by_segment")

    # Average transaction amounts
    st.markdown("### Average Transaction Amount by Segment and Risk Level")

    avg_amounts = trans_with_segment.groupby(['segment', 'current_risk_level'])['amount'].mean().round(2).unstack()

    st.dataframe(
        avg_amounts,
        use_container_width=True,
        column_config={
            col: st.column_config.NumberColumn(col.capitalize(), format="$%.2f")
            for col in avg_amounts.columns
        }
    )


def render_risk_evolution(data, colors):
    """6. Risk Evolution Tracking"""
    st.markdown("## 📈 Risk Evolution Tracking")
    st.markdown("*Monitor how customer risk levels change over time*")

    customers_df = data['customers']
    cdd_df = data['cdd_events']

    # Overall risk evolution metrics
    col1, col2, col3 = st.columns(3)

    # Map risk levels to numeric for comparison
    risk_map = {'low': 1, 'medium': 2, 'high': 3}
    customers_df['initial_numeric'] = customers_df['risk_level_initial'].map(risk_map)
    customers_df['current_numeric'] = customers_df['current_risk_level'].map(risk_map)

    with col1:
        risk_increased = customers_df[
            customers_df['initial_numeric'] < customers_df['current_numeric']
        ]
        st.metric("Risk Increased", f"{len(risk_increased)}")

    with col2:
        risk_stable = customers_df[customers_df['risk_level_initial'] == customers_df['current_risk_level']]
        st.metric("Risk Stable", f"{len(risk_stable)}")

    with col3:
        risk_decreased = customers_df[
            customers_df['initial_numeric'] > customers_df['current_numeric']
        ]
        st.metric("Risk Decreased", f"{len(risk_decreased)}")

    # Risk transition matrix
    st.markdown("### Risk Level Transition Matrix")

    transition_matrix = pd.crosstab(
        customers_df['risk_level_initial'],
        customers_df['current_risk_level'],
        margins=True
    )

    st.dataframe(transition_matrix, use_container_width=True)

    # CDD event impact on risk
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Risk Changes Over Time")

        risk_changes = cdd_df[cdd_df['previous_risk_level'] != cdd_df['new_risk_level']]
        risk_changes['month'] = risk_changes['event_date'].dt.to_period('M')
        monthly_changes = risk_changes.groupby('month').size()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[str(m) for m in monthly_changes.index],
            y=monthly_changes.values,
            mode='lines+markers',
            fill='tozeroy',
            marker_color=colors['warning']
        ))

        fig.update_layout(
            height=400,
            xaxis_title="Month",
            yaxis_title="Risk Level Changes",
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True, key="risk_changes_time")

    with col2:
        st.markdown("### CDD Event Types Causing Risk Changes")

        event_types = risk_changes['event_type'].value_counts()

        fig = go.Figure(go.Pie(
            labels=event_types.index,
            values=event_types.values,
            hole=0.4
        ))

        fig.update_layout(height=400)

        st.plotly_chart(fig, use_container_width=True, key="event_types_pie")


def render_false_positive_analysis(data, colors):
    """7. False Positive Analysis"""
    st.markdown("## 🎯 False Positive Analysis")
    st.markdown("*Track and reduce false positive alert rates*")

    alerts_df = data['alerts']

    # Overall FP metrics
    col1, col2, col3, col4 = st.columns(4)

    total_alerts = len(alerts_df)
    false_positives = alerts_df['false_positive'].sum()
    fp_rate = (false_positives / total_alerts) * 100

    with col1:
        st.metric("Total Alerts", f"{total_alerts:,}")

    with col2:
        st.metric("False Positives", f"{false_positives:,}")

    with col3:
        st.metric("FP Rate", f"{fp_rate:.2f}%")

    with col4:
        true_positives = total_alerts - false_positives
        precision = (true_positives / total_alerts) * 100
        st.metric("Precision", f"{precision:.2f}%")

    # FP rate by alert type
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### False Positive Rate by Alert Type")

        fp_by_type = alerts_df.groupby('alert_type').agg({
            'false_positive': ['sum', 'count']
        })
        fp_by_type.columns = ['false_positives', 'total']
        fp_by_type['fp_rate'] = (fp_by_type['false_positives'] / fp_by_type['total'] * 100).round(2)
        fp_by_type = fp_by_type.sort_values('fp_rate', ascending=False)

        fig = go.Figure(go.Bar(
            x=fp_by_type.index,
            y=fp_by_type['fp_rate'],
            marker_color=colors['danger'],
            text=fp_by_type['fp_rate'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside'
        ))

        fig.update_layout(
            height=400,
            xaxis_title="Alert Type",
            yaxis_title="False Positive Rate (%)",
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True, key="fp_by_type")

    with col2:
        st.markdown("### FP Trend Over Time")

        alerts_df['month'] = alerts_df['alert_timestamp'].dt.to_period('M')
        fp_trend = alerts_df.groupby('month').agg({
            'false_positive': ['sum', 'count']
        })
        fp_trend.columns = ['false_positives', 'total']
        fp_trend['fp_rate'] = (fp_trend['false_positives'] / fp_trend['total'] * 100).round(2)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[str(m) for m in fp_trend.index],
            y=fp_trend['fp_rate'],
            mode='lines+markers',
            marker_color=colors['warning'],
            line=dict(width=3)
        ))

        fig.update_layout(
            height=400,
            xaxis_title="Month",
            yaxis_title="False Positive Rate (%)",
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True, key="fp_trend")

    # Detailed FP analysis table
    st.markdown("### False Positive Details by Alert Type")

    fp_details = alerts_df.groupby('alert_type').agg({
        'alert_id': 'count',
        'false_positive': ['sum', lambda x: (x.sum() / len(x) * 100)],
        'time_to_decision_hours': 'mean'
    }).round(2)

    fp_details.columns = ['Total Alerts', 'False Positives', 'FP Rate (%)', 'Avg Decision Time (h)']
    fp_details = fp_details.sort_values('FP Rate (%)', ascending=False)

    st.dataframe(
        fp_details,
        use_container_width=True,
        column_config={
            'FP Rate (%)': st.column_config.ProgressColumn(
                'FP Rate (%)',
                min_value=0,
                max_value=100,
                format='%.1f%%'
            )
        }
    )


def render_regulatory_compliance_dashboard(data, colors):
    """8. Regulatory Compliance Dashboard"""
    st.markdown("## 🏛️ Regulatory Compliance Dashboard")
    st.markdown("*High-level compliance metrics for regulatory reporting*")

    customers_df = data['customers']
    kyc_df = data['kyc_events']
    edd_df = data['edd_actions']
    alerts_df = data['alerts']

    # Key compliance metrics
    st.markdown("### Compliance Metrics Overview")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        kyc_verified = (customers_df['KYC_status'] == 'verified').sum()
        kyc_rate = (kyc_verified / len(customers_df)) * 100
        st.metric("KYC Verified", f"{kyc_rate:.1f}%", f"{kyc_verified:,}/{len(customers_df):,}")

    with col2:
        pep_customers = (customers_df['PEP_status'] == 'Y').sum()
        st.metric("PEP Customers", f"{pep_customers:,}", f"{(pep_customers/len(customers_df)*100):.1f}%")

    with col3:
        high_risk = (customers_df['current_risk_level'] == 'high').sum()
        st.metric("High Risk", f"{high_risk:,}", f"{(high_risk/len(customers_df)*100):.1f}%")

    with col4:
        edd_required = (customers_df['edd_required'] == 'Y').sum()
        st.metric("EDD Required", f"{edd_required:,}", f"{(edd_required/len(customers_df)*100):.1f}%")

    with col5:
        sar_filed = len(alerts_df[alerts_df['analyst_decision'] == 'SAR_filed'])
        st.metric("SARs Filed", f"{sar_filed:,}")

    # KYC status distribution
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### KYC Status Distribution")

        kyc_status = customers_df['KYC_status'].value_counts()

        fig = go.Figure(go.Pie(
            labels=kyc_status.index,
            values=kyc_status.values,
            hole=0.4
        ))

        fig.update_layout(height=350)

        st.plotly_chart(fig, use_container_width=True, key="kyc_status_pie")

    with col2:
        st.markdown("### AML Status Distribution")

        aml_status = customers_df['AML_status'].value_counts()

        fig = go.Figure(go.Pie(
            labels=aml_status.index,
            values=aml_status.values,
            hole=0.4
        ))

        fig.update_layout(height=350)

        st.plotly_chart(fig, use_container_width=True, key="aml_status_pie")

    # EDD investigations summary
    st.markdown("### EDD Investigations Summary")

    col1, col2 = st.columns(2)

    with col1:
        edd_outcomes = edd_df['outcome'].value_counts()

        fig = go.Figure(go.Bar(
            x=edd_outcomes.index,
            y=edd_outcomes.values,
            marker_color=colors['primary']
        ))

        fig.update_layout(
            height=350,
            xaxis_title="Outcome",
            yaxis_title="Count",
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True, key="edd_outcomes")

    with col2:
        edd_reasons = edd_df['edd_reason'].value_counts()

        fig = go.Figure(go.Bar(
            x=edd_reasons.values,
            y=edd_reasons.index,
            orientation='h',
            marker_color=colors['warning']
        ))

        fig.update_layout(
            height=350,
            xaxis_title="Count",
            yaxis_title="Reason"
        )

        st.plotly_chart(fig, use_container_width=True, key="edd_reasons")

    # Compliance review calendar
    st.markdown("### CDD Review Schedule Compliance")

    review_freq = customers_df['cdd_review_frequency'].value_counts()

    st.dataframe(
        pd.DataFrame({
            'Review Frequency': review_freq.index,
            'Customer Count': review_freq.values,
            'Percentage': (review_freq.values / len(customers_df) * 100).round(2)
        }),
        use_container_width=True,
        hide_index=True
    )


def render():
    """Main render function"""

    # Apply theme
    apply_master_theme()

    # Header
    render_page_header(
        title="Compliance & KYC Analytics",
        subtitle="Comprehensive compliance monitoring and regulatory reporting",
        show_logo=False
    )

    # Get colors
    colors = get_chart_colors()

    # Load data
    with st.spinner("Loading compliance data..."):
        data = load_compliance_data()

    if data is None:
        st.error("Failed to load compliance data. Please ensure the dataset exists.")
        st.info("Run `python generate_compliance_dataset.py` to generate the dataset.")
        return

    # Success message
    st.success(f"✅ Loaded {len(data['customers']):,} customers, {len(data['transactions']):,} transactions, and {len(data['alerts']):,} alerts")

    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔄 Lifecycle & Evolution",
        "👥 Analyst & Rules",
        "📊 Segments & Audit",
        "🏛️ Regulatory & FP"
    ])

    with tab1:
        render_customer_lifecycle_timeline(data, colors)
        st.markdown("---")
        render_risk_evolution(data, colors)

    with tab2:
        render_analyst_retrospectives(data, colors)
        st.markdown("---")
        render_rule_effectiveness(data, colors)

    with tab3:
        render_segment_benchmarking(data, colors)
        st.markdown("---")
        render_audit_trail(data, colors)

    with tab4:
        render_regulatory_compliance_dashboard(data, colors)
        st.markdown("---")
        render_false_positive_analysis(data, colors)

    # Footer
    st.markdown("---")
    st.caption("© 2024 Arriba Advisors | Compliance & KYC Analytics Dashboard")


if __name__ == "__main__":
    render()
