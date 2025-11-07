"""
Transaction Review Detail Page

Comprehensive view of transaction risk scoring workflow showing:
- How auto-clear vs manual review decisions are made
- Complete rule evaluation with triggered rules highlighted
- Risk score calculation with visual breakdowns
- Decision thresholds and critical level assignment
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
from typing import Dict, Any, List

from streamlit_app.api_client import get_api_client


def render_workflow_diagram():
    """Render the transaction processing workflow diagram"""
    st.markdown("### 📊 Transaction Processing Workflow")

    # Create a Sankey diagram to show the workflow
    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = [
                "Incoming Transaction",  # 0
                "Rule Engine Check",  # 1
                "Risk Score Calculation",  # 2
                "Threshold Comparison",  # 3
                "Auto-Cleared (< 0.3)",  # 4
                "Manual Review (0.3-0.6)",  # 5
                "High Priority Review (> 0.6)",  # 6
                "Critical Review (> 0.8)"  # 7
            ],
            color = ["#4472C4", "#70AD47", "#FFC000", "#FF6B6B", "#28A745", "#FFC107", "#FF5722", "#DC3545"],
            x = [0.1, 0.3, 0.5, 0.7, 0.95, 0.95, 0.95, 0.95],
            y = [0.5, 0.5, 0.5, 0.5, 0.2, 0.45, 0.7, 0.9]
        ),
        link = dict(
            source = [0, 1, 2, 3, 3, 3, 3],
            target = [1, 2, 3, 4, 5, 6, 7],
            value = [100, 100, 100, 30, 30, 30, 10],
            color = ["#E0E0E0", "#E0E0E0", "#E0E0E0", "#28A745", "#FFC107", "#FF5722", "#DC3545"]
        )
    )])

    fig.update_layout(
        title="Transaction Flow: From Receipt to Decision",
        font=dict(size=12),
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Workflow steps explanation
    with st.expander("📖 Workflow Step Details", expanded=False):
        st.markdown("""
        **Step 1: Incoming Transaction**
        - Transaction received and basic validation performed
        - Transaction details extracted (amount, type, counterparty, etc.)

        **Step 2: Rule Engine Check**
        - Transaction evaluated against ALL configured fraud detection rules
        - Rules checked include:
          - Geographic fraud (high-risk countries, unexpected routing)
          - Account takeover (recent phone changes, unverified changes)
          - Transaction patterns (velocity, amount anomalies, odd hours)
          - Payroll fraud (account changes, suspicious sources)
          - Money laundering (chain detection, layering patterns)

        **Step 3: Risk Score Calculation**
        - Each triggered rule contributes its weight to the total score
        - Total weight is normalized to 0-1 scale
        - Formula: Risk Score = Sum(Triggered Rule Weights) / Sum(All Rule Weights)

        **Step 4: Threshold Comparison**
        - Risk score compared against configured thresholds:
          - **< 0.3**: Auto-cleared (Low Risk)
          - **0.3 - 0.6**: Manual Review Required (Medium Risk)
          - **0.6 - 0.8**: High Priority Review (High Risk)
          - **> 0.8**: Critical Priority Review (Critical Risk)

        **Step 5: Decision Assignment**
        - Transaction assigned to appropriate queue based on risk level
        - Critical level determines review priority and urgency
        """)


def render_transaction_card(transaction: Dict[str, Any]):
    """Render transaction details card"""
    st.markdown("### 💳 Transaction Details")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Transaction ID", transaction['transaction_id'])
        st.caption(f"Time: {format_timestamp(transaction['timestamp'])}")

    with col2:
        st.metric("Amount", f"${transaction['amount']:,.2f}")
        st.caption(f"Type: {transaction['transaction_type']}")

    with col3:
        direction_emoji = "🔴" if transaction['direction'] == 'debit' else "🟢"
        st.metric("Direction", f"{direction_emoji} {transaction['direction'].upper()}")
        st.caption(f"Counterparty: {transaction.get('counterparty_id', 'N/A')}")

    with col4:
        st.metric("Account", transaction['account_id'])
        st.caption(f"Description: {transaction.get('description', 'N/A')[:30]}")


def render_rule_evaluation(assessment: Dict[str, Any], all_rules: List[Dict[str, Any]]):
    """Render detailed rule evaluation showing all rules checked"""
    st.markdown("### 🔍 Rule Evaluation Results")

    triggered_rules = assessment.get('triggered_rules', {})

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Rules Checked", len(all_rules))

    with col2:
        st.metric("Rules Triggered", len(triggered_rules),
                 delta=f"{(len(triggered_rules)/max(len(all_rules), 1)*100):.1f}%",
                 delta_color="inverse")

    with col3:
        total_weight = sum(rule.get('weight', 0) for rule in triggered_rules.values())
        st.metric("Total Weight", f"{total_weight:.2f}")

    with col4:
        max_weight = max([rule.get('weight', 0) for rule in triggered_rules.values()], default=0)
        st.metric("Highest Weight", f"{max_weight:.2f}")

    st.divider()

    # Categorize rules
    rule_categories = {
        "Geographic Fraud": [],
        "Account Takeover": [],
        "Transaction Patterns": [],
        "Payroll Fraud": [],
        "Odd Hours Activity": [],
        "Money Laundering": [],
        "Other": []
    }

    for rule in all_rules:
        rule_name = rule['name']
        is_triggered = rule_name in triggered_rules
        rule_data = triggered_rules.get(rule_name, rule)

        # Categorize based on rule name
        if any(x in rule_name.lower() for x in ['country', 'geographic', 'routing', 'foreign']):
            category = "Geographic Fraud"
        elif any(x in rule_name.lower() for x in ['phone', 'takeover', 'device']):
            category = "Account Takeover"
        elif any(x in rule_name.lower() for x in ['velocity', 'amount', 'deviation', 'threshold']):
            category = "Transaction Patterns"
        elif 'payroll' in rule_name.lower():
            category = "Payroll Fraud"
        elif 'odd_hours' in rule_name.lower() or 'weekend' in rule_name.lower():
            category = "Odd Hours Activity"
        elif any(x in rule_name.lower() for x in ['chain', 'layering', 'mule', 'reversal']):
            category = "Money Laundering"
        else:
            category = "Other"

        rule_categories[category].append({
            'name': rule_name,
            'description': rule_data.get('description', 'No description'),
            'weight': rule_data.get('weight', 0),
            'triggered': is_triggered
        })

    # Display rules by category
    for category, rules in rule_categories.items():
        if not rules:
            continue

        triggered_count = sum(1 for r in rules if r['triggered'])

        with st.expander(f"**{category}** ({triggered_count}/{len(rules)} triggered)",
                        expanded=(triggered_count > 0)):

            # Sort by triggered status, then by weight
            rules.sort(key=lambda x: (not x['triggered'], -x['weight']))

            for rule in rules:
                if rule['triggered']:
                    st.markdown(f"""
                    <div style='background-color: #fee; padding: 10px; border-left: 4px solid #d32f2f; margin-bottom: 10px; border-radius: 5px;'>
                        <strong>🔴 {rule['name']}</strong> (Weight: {rule['weight']:.1f})<br/>
                        <span style='color: #666;'>{rule['description']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='background-color: #f0f0f0; padding: 10px; border-left: 4px solid #4caf50; margin-bottom: 10px; border-radius: 5px;'>
                        <strong>✅ {rule['name']}</strong> (Weight: {rule['weight']:.1f})<br/>
                        <span style='color: #666;'>{rule['description']}</span>
                    </div>
                    """, unsafe_allow_html=True)


def render_risk_score_calculation(assessment: Dict[str, Any], all_rules: List[Dict[str, Any]]):
    """Render visual risk score calculation breakdown"""
    st.markdown("### 📈 Risk Score Calculation")

    triggered_rules = assessment.get('triggered_rules', {})
    risk_score = assessment['risk_score']

    # Calculate components
    total_triggered_weight = sum(rule.get('weight', 0) for rule in triggered_rules.values())
    total_possible_weight = sum(rule.get('weight', 0) for rule in all_rules)

    # Create visualization of score calculation
    col1, col2 = st.columns([2, 1])

    with col1:
        # Waterfall chart showing weight accumulation
        if triggered_rules:
            rule_names = []
            weights = []

            for name, rule in triggered_rules.items():
                rule_names.append(name[:30] + "..." if len(name) > 30 else name)
                weights.append(rule.get('weight', 0))

            # Sort by weight
            sorted_data = sorted(zip(rule_names, weights), key=lambda x: x[1], reverse=True)
            rule_names, weights = zip(*sorted_data) if sorted_data else ([], [])

            fig = go.Figure(go.Waterfall(
                name = "Risk Score",
                orientation = "v",
                measure = ["relative"] * len(weights) + ["total"],
                x = list(rule_names) + ["Final Risk Score"],
                textposition = "outside",
                text = [f"+{w:.2f}" for w in weights] + [f"{risk_score:.3f}"],
                y = list(weights) + [risk_score],
                connector = {"line":{"color":"rgb(63, 63, 63)"}},
            ))

            fig.update_layout(
                title = "Risk Score Accumulation by Rule",
                showlegend = False,
                height = 400,
                yaxis_title = "Weight Contribution"
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("✅ No rules triggered - Clean transaction")

    with col2:
        st.markdown("#### Calculation Formula")
        st.markdown(f"""
        **Triggered Rules Weight:**
        {total_triggered_weight:.2f}

        **Total Possible Weight:**
        {total_possible_weight:.2f}

        **Normalization:**
        ```
        Risk Score =
          {total_triggered_weight:.2f} / {total_possible_weight:.2f}
          = {risk_score:.4f}
        ```

        **Rounded Score:**
        **{risk_score:.2f}**
        """)

        # Gauge chart
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = risk_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            number = {'suffix': "", 'font': {'size': 40}},
            gauge = {
                'axis': {'range': [None, 1], 'tickwidth': 1},
                'bar': {'color': get_risk_color(risk_score)},
                'steps': [
                    {'range': [0, 0.3], 'color': '#E8F5E9'},
                    {'range': [0.3, 0.6], 'color': '#FFF9C4'},
                    {'range': [0.6, 0.8], 'color': '#FFCCBC'},
                    {'range': [0.8, 1], 'color': '#FFCDD2'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 0.6
                }
            }
        ))

        fig.update_layout(height=250, margin=dict(l=20, r=20, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)


def render_threshold_comparison(assessment: Dict[str, Any]):
    """Render threshold comparison visualization"""
    st.markdown("### 🎯 Threshold Comparison & Decision Logic")

    risk_score = assessment['risk_score']
    decision = assessment['decision']

    # Determine risk level and color
    if risk_score < 0.3:
        risk_level = "LOW RISK"
        risk_color = "#28A745"
        critical_level = "Auto-Cleared"
    elif risk_score < 0.6:
        risk_level = "MEDIUM RISK"
        risk_color = "#FFC107"
        critical_level = "Manual Review Required"
    elif risk_score < 0.8:
        risk_level = "HIGH RISK"
        risk_color = "#FF5722"
        critical_level = "High Priority Review"
    else:
        risk_level = "CRITICAL RISK"
        risk_color = "#DC3545"
        critical_level = "Critical Priority Review"

    # Create horizontal bar showing score position
    fig = go.Figure()

    # Add threshold zones
    fig.add_trace(go.Bar(
        y=['Risk Level'],
        x=[0.3],
        name='Auto-Clear Zone',
        orientation='h',
        marker=dict(color='#28A745'),
        text=['Auto-Clear<br>(< 0.3)'],
        textposition='inside',
        hoverinfo='skip'
    ))

    fig.add_trace(go.Bar(
        y=['Risk Level'],
        x=[0.3],
        name='Manual Review Zone',
        orientation='h',
        marker=dict(color='#FFC107'),
        text=['Manual Review<br>(0.3 - 0.6)'],
        textposition='inside',
        hoverinfo='skip'
    ))

    fig.add_trace(go.Bar(
        y=['Risk Level'],
        x=[0.2],
        name='High Priority Zone',
        orientation='h',
        marker=dict(color='#FF5722'),
        text=['High Priority<br>(0.6 - 0.8)'],
        textposition='inside',
        hoverinfo='skip'
    ))

    fig.add_trace(go.Bar(
        y=['Risk Level'],
        x=[0.2],
        name='Critical Zone',
        orientation='h',
        marker=dict(color='#DC3545'),
        text=['Critical<br>(> 0.8)'],
        textposition='inside',
        hoverinfo='skip'
    ))

    # Add marker for current score
    fig.add_trace(go.Scatter(
        x=[risk_score],
        y=['Risk Level'],
        mode='markers+text',
        marker=dict(size=20, color='black', symbol='diamond'),
        text=[f'Score: {risk_score:.2f}'],
        textposition='top center',
        name='Current Transaction',
        hoverinfo='text',
        hovertext=f'Risk Score: {risk_score:.2f}<br>{risk_level}'
    ))

    fig.update_layout(
        barmode='stack',
        height=200,
        showlegend=False,
        xaxis=dict(
            title='Risk Score',
            range=[0, 1],
            tickvals=[0, 0.3, 0.6, 0.8, 1.0]
        ),
        yaxis=dict(showticklabels=False),
        margin=dict(l=0, r=0, t=20, b=50)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Decision explanation
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(f"""
        <div style='background-color: {risk_color}20; padding: 20px; border-radius: 10px; border: 3px solid {risk_color}; text-align: center;'>
            <h2 style='color: {risk_color}; margin: 0;'>{risk_level}</h2>
            <h3 style='margin: 10px 0;'>Risk Score: {risk_score:.2f}</h3>
            <h4 style='margin: 10px 0;'>Decision: {decision.replace('_', ' ').title()}</h4>
            <p style='font-size: 18px; font-weight: bold; margin: 10px 0;'>{critical_level}</p>
        </div>
        """, unsafe_allow_html=True)


def render_decision_explanation(assessment: Dict[str, Any]):
    """Render detailed explanation of why decision was made"""
    st.markdown("### 💡 Decision Explanation")

    risk_score = assessment['risk_score']
    decision = assessment['decision']
    triggered_rules = assessment.get('triggered_rules', {})

    # Build explanation
    explanation_parts = []

    if risk_score < 0.3:
        explanation_parts.append(f"✅ **Transaction Auto-Cleared**: Risk score ({risk_score:.2f}) is below the auto-approve threshold (0.3).")
        if len(triggered_rules) == 0:
            explanation_parts.append("- No fraud detection rules were triggered")
            explanation_parts.append("- Transaction characteristics match normal patterns")
        else:
            explanation_parts.append(f"- Only {len(triggered_rules)} minor rule(s) triggered with low combined weight")
            explanation_parts.append("- Risk level too low to warrant manual review")

    elif risk_score < 0.6:
        explanation_parts.append(f"⚠️ **Manual Review Required**: Risk score ({risk_score:.2f}) is in the manual review range (0.3 - 0.6).")
        explanation_parts.append(f"- {len(triggered_rules)} fraud detection rule(s) triggered")
        explanation_parts.append("- Risk level requires human review for final decision")
        explanation_parts.append("- Transaction should be reviewed before approval")

    elif risk_score < 0.8:
        explanation_parts.append(f"🔴 **High Priority Review**: Risk score ({risk_score:.2f}) indicates high fraud risk (0.6 - 0.8).")
        explanation_parts.append(f"- {len(triggered_rules)} significant fraud indicators detected")
        explanation_parts.append("- Multiple risk factors present")
        explanation_parts.append("- **Immediate review recommended** - high fraud likelihood")

    else:
        explanation_parts.append(f"🚨 **CRITICAL Priority Review**: Risk score ({risk_score:.2f}) indicates critical fraud risk (> 0.8).")
        explanation_parts.append(f"- {len(triggered_rules)} major fraud indicators triggered")
        explanation_parts.append("- Severe risk factors detected")
        explanation_parts.append("- **URGENT REVIEW REQUIRED** - Very high fraud probability")
        explanation_parts.append("- Consider blocking transaction pending review")

    # Add key risk factors
    if triggered_rules:
        explanation_parts.append("\n**Key Risk Factors:**")
        # Sort by weight
        sorted_rules = sorted(
            triggered_rules.items(),
            key=lambda x: x[1].get('weight', 0),
            reverse=True
        )
        for name, rule in sorted_rules[:5]:  # Top 5
            weight = rule.get('weight', 0)
            description = rule.get('description', name)
            explanation_parts.append(f"- [{weight:.1f}] {description}")

    # Display explanation
    for part in explanation_parts:
        st.markdown(part)

    # Review recommendations
    st.markdown("---")
    st.markdown("#### 👨‍💼 Recommended Actions")

    if risk_score < 0.3:
        st.success("✅ Safe to approve - No action required")
    elif risk_score < 0.6:
        st.warning("""
        ⚠️ **Review Actions:**
        1. Verify transaction details with customer
        2. Check for any unusual patterns
        3. Approve if details confirm legitimacy
        4. Reject if suspicious elements found
        """)
    elif risk_score < 0.8:
        st.error("""
        🔴 **High Priority Review Actions:**
        1. **Contact customer immediately** for verification
        2. Review recent account activity for compromise indicators
        3. Check triggered rules for specific fraud patterns
        4. Consider temporary hold on transaction
        5. Escalate to fraud specialist if needed
        """)
    else:
        st.error("""
        🚨 **CRITICAL Review Actions:**
        1. **BLOCK transaction immediately** pending review
        2. **Contact customer urgently** through verified channels
        3. Review complete account history
        4. Check for account takeover indicators
        5. **Escalate to senior fraud analyst immediately**
        6. Consider account suspension if fraud confirmed
        7. File SAR if required by regulations
        """)


def format_timestamp(timestamp_str):
    """Format ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str


def get_risk_color(risk_score):
    """Get color based on risk score"""
    if risk_score < 0.3:
        return "#28A745"
    elif risk_score < 0.6:
        return "#FFC107"
    elif risk_score < 0.8:
        return "#FF5722"
    else:
        return "#DC3545"


def get_mock_all_rules():
    """Get all configured rules for display (mock data for demonstration)"""
    # In production, this would fetch from the API/rules engine
    return [
        # Geographic rules
        {"name": "payment_to_high_risk_country", "description": "Payment routed to high-risk or sanctioned country", "weight": 3.5},
        {"name": "unexpected_country_routing", "description": "Payment routed to unexpected country based on vendor history", "weight": 2.5},
        {"name": "domestic_to_foreign_switch", "description": "Domestic-only vendor suddenly paid through foreign account", "weight": 3.0},
        {"name": "first_international_payment", "description": "First international payment from account", "weight": 1.5},

        # Account takeover rules
        {"name": "immediate_transfer_after_phone_change_1h", "description": "Outgoing transfer within 1 hour(s) of phone change - critical account takeover alert", "weight": 5.0},
        {"name": "phone_change_before_transfer_24h", "description": "Outgoing transfer within 24 hours of phone/device change - possible account takeover", "weight": 3.5},
        {"name": "large_transfer_after_phone_change_5000", "description": "Large transfer (>=$5,000.00) within 48h of phone change - high-risk takeover", "weight": 4.0},

        # Transaction patterns
        {"name": "amount_exceeds_10000", "description": "Transaction amount exceeds $10,000.00", "weight": 2.0},
        {"name": "velocity_5_in_24h", "description": "More than 5 transactions in 24 hours", "weight": 1.5},
        {"name": "amount_deviation_3x", "description": "Transaction amount deviates from average by 3x", "weight": 2.0},
        {"name": "new_counterparty", "description": "Transaction with a new counterparty", "weight": 1.0},

        # Payroll rules
        {"name": "payroll_recent_account_change", "description": "Payroll transaction to bank account changed within 30 days", "weight": 3.0},
        {"name": "payroll_unverified_account_change", "description": "Payroll transaction to account with unverified banking information changes", "weight": 4.0},
        {"name": "payroll_suspicious_change_source", "description": "Account changed via email/phone request rather than secure portal", "weight": 3.5},

        # Odd hours rules
        {"name": "odd_hours_transaction", "description": "Transaction initiated during odd hours (22:00 - 06:00)", "weight": 2.0},
        {"name": "large_odd_hours_transaction_5000", "description": "Large transaction (>= $5,000.00) initiated during odd hours - elevated fraud risk", "weight": 3.5},
        {"name": "odd_hours_pattern_deviation", "description": "Transaction at odd hours deviates significantly from customer's normal activity pattern", "weight": 4.0},

        # Money laundering rules
        {"name": "suspicious_chain_70", "description": "Suspicious transaction chain detected (threshold: 0.7)", "weight": 2.0},
        {"name": "credit_refund_transfer_chain_1", "description": "Credit-Refund-Transfer chain detected (min 1 chains)", "weight": 2.5},
        {"name": "layering_pattern_1", "description": "Layering pattern detected - multiple small credits consolidated (min 1 patterns)", "weight": 2.0},
        {"name": "money_mule_72h", "description": "Money mule pattern detected: 5+ small incoming payments (avg ≤$500.00), 70%+ flow-through, transferred within 48h", "weight": 2.0},
    ]


def render():
    """Main render function for Transaction Review Detail page"""

    st.set_page_config(page_title="Transaction Review Detail", page_icon="🔍", layout="wide")

    # Header
    st.markdown("# 🔍 Transaction Review Detail")
    st.markdown("**Comprehensive Analysis: Auto-Clear vs Manual Review Decision Process**")
    st.divider()

    # Transaction selector
    col1, col2 = st.columns([3, 1])
    with col1:
        transaction_id = st.text_input("Enter Transaction ID to review:", placeholder="TX_000001")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_button = st.button("🔍 Load Transaction", use_container_width=True)

    if transaction_id or search_button:
        # In production, fetch from API
        # For now, show with mock data
        with st.spinner("Loading transaction details..."):
            # Mock data - in production, replace with API call
            transaction = {
                "transaction_id": transaction_id or "TX_000001",
                "amount": 15750.00,
                "transaction_type": "WIRE",
                "direction": "debit",
                "timestamp": "2025-01-15T23:45:30",
                "account_id": "ACC_0001",
                "counterparty_id": "COUNTER_0042",
                "description": "International wire transfer"
            }

            assessment = {
                "assessment_id": "RISK_000001",
                "transaction_id": transaction_id or "TX_000001",
                "risk_score": 0.72,
                "decision": "manual_review",
                "triggered_rules": {
                    "large_odd_hours_transaction_5000": {
                        "description": "Large transaction (>= $5,000.00) initiated during odd hours - elevated fraud risk",
                        "weight": 3.5
                    },
                    "amount_exceeds_10000": {
                        "description": "Transaction amount exceeds $10,000.00",
                        "weight": 2.0
                    },
                    "odd_hours_pattern_deviation": {
                        "description": "Transaction at odd hours deviates significantly from customer's normal activity pattern",
                        "weight": 4.0
                    },
                    "first_international_payment": {
                        "description": "First international payment from account",
                        "weight": 1.5
                    }
                }
            }

            all_rules = get_mock_all_rules()

        # Render workflow diagram
        render_workflow_diagram()
        st.divider()

        # Render transaction details
        render_transaction_card(transaction)
        st.divider()

        # Render rule evaluation
        render_rule_evaluation(assessment, all_rules)
        st.divider()

        # Render risk score calculation
        render_risk_score_calculation(assessment, all_rules)
        st.divider()

        # Render threshold comparison
        render_threshold_comparison(assessment)
        st.divider()

        # Render decision explanation
        render_decision_explanation(assessment)

        # Action buttons
        st.divider()
        st.markdown("### 🎬 Review Actions")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("✅ Approve Transaction", use_container_width=True):
                st.success("Transaction approved!")

        with col2:
            if st.button("❌ Reject Transaction", use_container_width=True):
                st.error("Transaction rejected!")

        with col3:
            if st.button("⏸️ Hold for Investigation", use_container_width=True):
                st.warning("Transaction placed on hold")

        with col4:
            if st.button("📧 Contact Customer", use_container_width=True):
                st.info("Customer verification initiated")

    else:
        st.info("👆 Enter a transaction ID above to view detailed risk analysis")

        # Show example
        st.markdown("---")
        st.markdown("### 📚 Example Use Cases")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            **Low Risk Example**
            - TX_000100
            - $250 ACH transfer
            - 2 PM business hours
            - Known counterparty
            - Risk Score: 0.15
            - ✅ Auto-cleared
            """)

        with col2:
            st.markdown("""
            **Medium Risk Example**
            - TX_000200
            - $5,500 wire transfer
            - New counterparty
            - Risk Score: 0.45
            - ⚠️ Manual review
            """)

        with col3:
            st.markdown("""
            **High Risk Example**
            - TX_000300
            - $25,000 international wire
            - 2 AM transaction time
            - Recent phone change
            - Risk Score: 0.85
            - 🚨 Critical review
            """)


if __name__ == "__main__":
    render()
