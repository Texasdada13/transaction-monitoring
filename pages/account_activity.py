"""Account Activity Monitoring Page"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from app.models.database import get_db, Account, Employee, Beneficiary, AccountChangeHistory, BeneficiaryChangeHistory

def show():
    st.header("🏦 Account Activity")
    st.markdown("Monitor account modifications, new beneficiaries, and suspicious changes")

    db = next(get_db())
    try:
        accounts = db.query(Account).all()
        employees = db.query(Employee).all()
        beneficiaries = db.query(Beneficiary).all()
        account_changes = db.query(AccountChangeHistory).all()
        beneficiary_changes = db.query(BeneficiaryChangeHistory).all()

        # Top metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Accounts", len(accounts))
        with col2:
            st.metric("Employees", len(employees))
        with col3:
            st.metric("Beneficiaries", len(beneficiaries))
        with col4:
            total_changes = len(account_changes) + len(beneficiary_changes)
            st.metric("Total Changes", total_changes)

        st.markdown("---")

        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📝 Recent Changes",
            "👤 Employee Accounts",
            "🏢 Beneficiaries",
            "🚨 Suspicious Activity"
        ])

        with tab1:
            st.subheader("Recent Account Changes")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Employee Account Changes**")
                if account_changes:
                    changes_df = pd.DataFrame([{
                        'Employee ID': c.employee_id,
                        'Change Type': c.change_type,
                        'Source': c.change_source,
                        'Verified': '✅' if c.verified else '❌',
                        'Flagged': '🚨' if c.flagged_as_suspicious else '✓',
                        'Timestamp': datetime.fromisoformat(c.timestamp).strftime('%Y-%m-%d %H:%M')
                    } for c in sorted(account_changes, key=lambda x: x.timestamp, reverse=True)[:10]])

                    st.dataframe(changes_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No account changes recorded.")

            with col2:
                st.markdown("**Beneficiary Account Changes**")
                if beneficiary_changes:
                    ben_changes_df = pd.DataFrame([{
                        'Beneficiary ID': c.beneficiary_id,
                        'Change Type': c.change_type,
                        'Source': c.change_source,
                        'Verified': '✅' if c.verified else '❌',
                        'Flagged': '🚨' if c.flagged_as_suspicious else '✓',
                        'Timestamp': datetime.fromisoformat(c.timestamp).strftime('%Y-%m-%d %H:%M')
                    } for c in sorted(beneficiary_changes, key=lambda x: x.timestamp, reverse=True)[:10]])

                    st.dataframe(ben_changes_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No beneficiary changes recorded.")

            # Change source distribution
            st.markdown("---")
            st.subheader("Change Source Distribution")

            all_sources = ([c.change_source for c in account_changes] +
                          [c.change_source for c in beneficiary_changes])

            if all_sources:
                source_counts = pd.Series(all_sources).value_counts()

                fig = go.Figure(data=[go.Bar(
                    x=source_counts.index,
                    y=source_counts.values,
                    marker_color=['#3498db', '#e74c3c', '#2ecc71']
                )])
                fig.update_layout(
                    title='Changes by Source',
                    xaxis_title='Source',
                    yaxis_title='Count',
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Employee Account Details")

            if employees:
                emp_df = pd.DataFrame([{
                    'Employee ID': e.employee_id,
                    'Name': e.name,
                    'Department': e.department,
                    'Status': e.employment_status,
                    'Hire Date': datetime.fromisoformat(e.hire_date).strftime('%Y-%m-%d'),
                    'Last Payroll': datetime.fromisoformat(e.last_payroll_date).strftime('%Y-%m-%d') if e.last_payroll_date else 'N/A',
                    'Payroll Frequency': e.payroll_frequency
                } for e in employees])

                st.dataframe(emp_df, use_container_width=True, hide_index=True)

                # Department distribution
                st.markdown("---")
                dept_counts = emp_df['Department'].value_counts()

                fig = px.pie(
                    values=dept_counts.values,
                    names=dept_counts.index,
                    title='Employees by Department'
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No employee data available.")

        with tab3:
            st.subheader("Beneficiary Registry")

            if beneficiaries:
                ben_df = pd.DataFrame([{
                    'Beneficiary ID': b.beneficiary_id,
                    'Name': b.name,
                    'Status': b.status,
                    'Verified': '✅' if b.verified else '❌',
                    'Registration Date': datetime.fromisoformat(b.registration_date).strftime('%Y-%m-%d'),
                    'Total Payments': b.total_payments_received if b.total_payments_received else 0,
                    'Total Amount': f"${b.total_amount_received:,.2f}" if b.total_amount_received else '$0.00',
                    'Last Payment': datetime.fromisoformat(b.last_payment_date).strftime('%Y-%m-%d') if b.last_payment_date else 'Never'
                } for b in beneficiaries])

                st.dataframe(ben_df, use_container_width=True, hide_index=True)

                # Verification status
                st.markdown("---")
                verified_count = sum(1 for b in beneficiaries if b.verified)
                unverified_count = len(beneficiaries) - verified_count

                col1, col2 = st.columns(2)

                with col1:
                    fig = go.Figure(data=[go.Pie(
                        labels=['Verified', 'Unverified'],
                        values=[verified_count, unverified_count],
                        marker=dict(colors=['#2ecc71', '#e74c3c']),
                        hole=0.4
                    )])
                    fig.update_layout(title='Beneficiary Verification Status', height=300)
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    # New vs established beneficiaries
                    from datetime import timedelta
                    now = datetime.utcnow()
                    new_threshold = now - timedelta(days=90)

                    new_beneficiaries = sum(1 for b in beneficiaries
                                           if datetime.fromisoformat(b.registration_date) > new_threshold)
                    established = len(beneficiaries) - new_beneficiaries

                    fig = go.Figure(data=[go.Pie(
                        labels=['Established (>90 days)', 'New (<90 days)'],
                        values=[established, new_beneficiaries],
                        marker=dict(colors=['#3498db', '#f39c12']),
                        hole=0.4
                    )])
                    fig.update_layout(title='Beneficiary Age Distribution', height=300)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No beneficiary data available.")

        with tab4:
            st.subheader("🚨 Suspicious Activity Flags")

            flagged_account_changes = [c for c in account_changes if c.flagged_as_suspicious]
            flagged_ben_changes = [c for c in beneficiary_changes if c.flagged_as_suspicious]
            unverified_changes = [c for c in account_changes + beneficiary_changes if not c.verified]

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Flagged Account Changes", len(flagged_account_changes))
            with col2:
                st.metric("Flagged Beneficiary Changes", len(flagged_ben_changes))
            with col3:
                st.metric("Unverified Changes", len(unverified_changes))

            if flagged_account_changes or flagged_ben_changes:
                st.markdown("---")
                st.markdown("**Flagged Changes Requiring Attention:**")

                # Show flagged account changes
                if flagged_account_changes:
                    st.markdown("*Employee Account Changes:*")
                    for change in flagged_account_changes:
                        with st.expander(f"🚨 {change.employee_id} - {change.change_type} - {datetime.fromisoformat(change.timestamp).strftime('%Y-%m-%d')}"):
                            st.write(f"**Change Type:** {change.change_type}")
                            st.write(f"**Source:** {change.change_source}")
                            st.write(f"**Old Value:** {change.old_value}")
                            st.write(f"**New Value:** {change.new_value}")
                            st.write(f"**Verified:** {'Yes' if change.verified else 'No'}")
                            if change.suspicious_reason:
                                st.warning(f"**Reason:** {change.suspicious_reason}")

                # Show flagged beneficiary changes
                if flagged_ben_changes:
                    st.markdown("*Beneficiary Changes:*")
                    for change in flagged_ben_changes:
                        with st.expander(f"🚨 {change.beneficiary_id} - {change.change_type} - {datetime.fromisoformat(change.timestamp).strftime('%Y-%m-%d')}"):
                            st.write(f"**Change Type:** {change.change_type}")
                            st.write(f"**Source:** {change.change_source}")
                            st.write(f"**Old Value:** {change.old_value}")
                            st.write(f"**New Value:** {change.new_value}")
                            st.write(f"**Verified:** {'Yes' if change.verified else 'No'}")
                            if change.suspicious_reason:
                                st.warning(f"**Reason:** {change.suspicious_reason}")
            else:
                st.success("✅ No suspicious activity detected!")

    finally:
        db.close()
