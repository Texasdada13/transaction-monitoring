"""
Rule Performance Analytics Page

Advanced rule correlation, waterfall analysis, and performance metrics.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime


# Generate synthetic dataset for visualization
np.random.seed(42)

# Rule performance data (20 rules)
rule_names = [
    "Transaction Amount Anomalies", "Transaction Frequency", "Recipient Verification Status",
    "Recipient Blacklist Status", "Device Fingerprinting", "VPN or Proxy Usage",
    "Geo-Location Flags", "Behavioral Biometrics", "Time Since Last Transaction",
    "Social Trust Score", "Account Age", "High-Risk Transaction Times",
    "Past Fraudulent Behavior", "Location-Inconsistent Transactions", "Normalized Transaction Amount",
    "Transaction Context Anomalies", "Fraud Complaints Count", "Merchant Category Mismatch",
    "User Daily Limit Exceeded", "Recent High-Value Transaction"
]

rule_performance_df = pd.DataFrame({
    'rule_name': rule_names,
    'trigger_frequency': np.random.randint(50, 500, 20),
    'precision': np.random.uniform(0.65, 0.98, 20),
    'false_positive_rate': np.random.uniform(0.02, 0.35, 20),
    'avg_contribution': np.random.uniform(5, 35, 20),
    'confirmed_fraud_count': np.random.randint(10, 200, 20),
    'rule_weight': [32, 35, 26, 22, 30, 22, 32, 15, 24, 18, 8, 28, 35, 20, 18, 24, 12, 4, 10, 6]
})

# Rule correlation pairs
rule_correlation_pairs = [
    ('VPN or Proxy Usage', 'Geo-Location Flags', 85),
    ('Device Fingerprinting', 'Behavioral Biometrics', 72),
    ('Transaction Amount Anomalies', 'Transaction Context Anomalies', 68),
    ('Recipient Verification Status', 'Social Trust Score', 78),
    ('High-Risk Transaction Times', 'Transaction Frequency', 65),
    ('Account Age', 'Transaction Amount Anomalies', 55),
    ('Past Fraudulent Behavior', 'Fraud Complaints Count', 80),
    ('Location-Inconsistent Transactions', 'VPN or Proxy Usage', 75),
    ('Recipient Blacklist Status', 'Past Fraudulent Behavior', 70),
    ('User Daily Limit Exceeded', 'Transaction Frequency', 60)
]


def render():
    """Render the Rule Performance Analytics page"""

    st.markdown("# Rule Performance Analytics")
    st.markdown("### Fraud Detection Rule Effectiveness & Optimization Metrics")
    st.caption(f"Last Updated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}")

    st.markdown("---")

    # Rule Performance Heatmap (from summary dashboard)
    st.subheader("🔥 Rule Performance Matrix")
    st.caption("Comprehensive view of rule effectiveness across multiple metrics")

    # Prepare heatmap data
    heatmap_data = rule_performance_df[['rule_name', 'trigger_frequency', 'precision',
                                         'false_positive_rate', 'avg_contribution']].copy()

    # Normalize for better visualization
    heatmap_data['trigger_frequency_norm'] = (heatmap_data['trigger_frequency'] - heatmap_data['trigger_frequency'].min()) / (heatmap_data['trigger_frequency'].max() - heatmap_data['trigger_frequency'].min())
    heatmap_data['precision_norm'] = heatmap_data['precision']
    heatmap_data['fpr_norm'] = 1 - heatmap_data['false_positive_rate']  # Inverted so green is good
    heatmap_data['contribution_norm'] = (heatmap_data['avg_contribution'] - heatmap_data['avg_contribution'].min()) / (heatmap_data['avg_contribution'].max() - heatmap_data['avg_contribution'].min())

    heatmap_matrix = heatmap_data[['rule_name', 'trigger_frequency_norm', 'precision_norm',
                                     'fpr_norm', 'contribution_norm']].set_index('rule_name')

    fig_heatmap = go.Figure(data=go.Heatmap(
        z=heatmap_matrix.values,
        x=['Trigger Frequency', 'Precision', 'False Positive Rate (Inv)', 'Avg Contribution'],
        y=heatmap_matrix.index,
        colorscale='RdYlGn',
        text=np.round(heatmap_matrix.values, 2),
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title="Performance Score")
    ))

    fig_heatmap.update_layout(
        height=600,
        xaxis_title="Performance Metrics",
        yaxis_title="Detection Rules",
        yaxis=dict(autorange='reversed')
    )

    st.plotly_chart(fig_heatmap, use_container_width=True)

    st.markdown("---")

    # Rule Contribution Treemap and Bubble Chart
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🌳 Fraud Detection Impact Analysis")
        st.caption("Treemap showing confirmed fraud catches by rule")

        fig_treemap = go.Figure(go.Treemap(
            labels=rule_performance_df['rule_name'],
            parents=[''] * len(rule_performance_df),
            values=rule_performance_df['confirmed_fraud_count'],
            textinfo='label+value+percent parent',
            marker=dict(
                colorscale='Reds',
                cmid=rule_performance_df['confirmed_fraud_count'].mean()
            ),
            hovertemplate='<b>%{label}</b><br>Fraud Caught: %{value}<br>Percentage: %{percentParent}<extra></extra>'
        ))

        fig_treemap.update_layout(height=500)
        st.plotly_chart(fig_treemap, use_container_width=True)

    with col2:
        st.subheader("🎯 Rule Effectiveness Matrix")
        st.caption("Bubble chart: Trigger Frequency vs Precision (size = weight)")

        fig_bubble = go.Figure()

        fig_bubble.add_trace(go.Scatter(
            x=rule_performance_df['trigger_frequency'],
            y=rule_performance_df['precision'] * 100,
            mode='markers',
            marker=dict(
                size=rule_performance_df['rule_weight'],
                sizemode='diameter',
                sizeref=2,
                color=rule_performance_df['precision'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Precision"),
                line=dict(width=1, color='white')
            ),
            text=rule_performance_df['rule_name'],
            hovertemplate='<b>%{text}</b><br>Frequency: %{x}<br>Precision: %{y:.1f}%<br><extra></extra>'
        ))

        fig_bubble.update_layout(
            xaxis_title="Trigger Frequency",
            yaxis_title="Precision (%)",
            height=500,
            hovermode='closest'
        )

        st.plotly_chart(fig_bubble, use_container_width=True)

    st.markdown("---")

    # Rule Correlation Network
    st.subheader("🔗 Rule Correlation Network")
    st.caption("Shows which rules commonly fire together (typical 5-8 rule patterns)")

    # Create network visualization using scatter plot with connecting lines
    fig_network = go.Figure()

    # Get unique rules from pairs
    unique_rules = list(set([r[0] for r in rule_correlation_pairs] + [r[1] for r in rule_correlation_pairs]))
    rule_positions = {rule: (np.cos(i*2*np.pi/len(unique_rules)), np.sin(i*2*np.pi/len(unique_rules)))
                     for i, rule in enumerate(unique_rules)}

    # Draw edges (correlations)
    for rule1, rule2, strength in rule_correlation_pairs:
        x0, y0 = rule_positions[rule1]
        x1, y1 = rule_positions[rule2]

        # Line thickness based on correlation strength
        width = strength / 20

        fig_network.add_trace(go.Scatter(
            x=[x0, x1],
            y=[y0, y1],
            mode='lines',
            line=dict(
                width=width,
                color=f'rgba(239, 68, 68, {strength/100})'
            ),
            hoverinfo='skip',
            showlegend=False
        ))

    # Draw nodes
    for rule, (x, y) in rule_positions.items():
        fig_network.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode='markers+text',
            marker=dict(size=15, color='#3b82f6', line=dict(width=2, color='white')),
            text=rule.split()[0],  # First word only
            textposition='top center',
            hovertext=rule,
            hoverinfo='text',
            showlegend=False
        ))

    fig_network.update_layout(
        height=600,
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig_network, use_container_width=True)

    # Display correlation pairs
    st.markdown("**High-Correlation Rule Pairs:**")
    correlation_df = pd.DataFrame(rule_correlation_pairs, columns=['Rule 1', 'Rule 2', 'Correlation %'])
    correlation_df = correlation_df.sort_values('Correlation %', ascending=False)
    st.dataframe(correlation_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Rule Contribution Waterfall
    st.subheader("💧 Rule Contribution Waterfall (Sample Transaction)")
    st.caption("Shows how each triggered rule contributes to final risk score")

    # Sample transaction with rules
    sample_rules = [
        {'name': 'Base Score', 'contribution': 0, 'cumulative': 0},
        {'name': 'Amount Anomaly', 'contribution': 25, 'cumulative': 25},
        {'name': 'VPN Usage', 'contribution': 15, 'cumulative': 40},
        {'name': 'Device Mismatch', 'contribution': 22, 'cumulative': 62},
        {'name': 'Geo-Location Flag', 'contribution': 18, 'cumulative': 80},
        {'name': 'High-Risk Time', 'contribution': 9, 'cumulative': 89},
        {'name': 'Final Risk Score', 'contribution': 0, 'cumulative': 89}
    ]

    fig_waterfall = go.Figure(go.Waterfall(
        name="Risk Score",
        orientation="v",
        measure=["absolute"] + ["relative"] * 5 + ["total"],
        x=[r['name'] for r in sample_rules],
        textposition="outside",
        text=[f"+{r['contribution']}" if r['contribution'] > 0 else "" for r in sample_rules],
        y=[r['contribution'] for r in sample_rules],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#ef4444"}},
        decreasing={"marker": {"color": "#10b981"}},
        totals={"marker": {"color": "#6366f1"}}
    ))

    fig_waterfall.update_layout(
        title="Risk Score Build-up for Transaction #TXN-789456",
        yaxis_title="Risk Points",
        height=500
    )

    st.plotly_chart(fig_waterfall, use_container_width=True)

    st.markdown("---")

    # Detailed Rule Performance Table
    st.subheader("📋 Detailed Rule Performance Metrics")

    # Format the dataframe for display
    display_df = rule_performance_df.copy()
    display_df['precision'] = (display_df['precision'] * 100).round(1).astype(str) + '%'
    display_df['false_positive_rate'] = (display_df['false_positive_rate'] * 100).round(1).astype(str) + '%'
    display_df = display_df.rename(columns={
        'rule_name': 'Rule Name',
        'trigger_frequency': 'Trigger Frequency',
        'precision': 'Precision',
        'false_positive_rate': 'False Positive Rate',
        'avg_contribution': 'Avg Contribution',
        'confirmed_fraud_count': 'Fraud Caught',
        'rule_weight': 'Rule Weight'
    })

    st.dataframe(
        display_df[['Rule Name', 'Trigger Frequency', 'Precision', 'False Positive Rate',
                    'Avg Contribution', 'Fraud Caught', 'Rule Weight']],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")
    st.caption(f"💡 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | **Note:** Enhanced analytics with synthetic correlation data")
