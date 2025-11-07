#!/usr/bin/env python3
"""
Generate comprehensive sample data with transactions and risk assessments.
"""
import uuid
import json
from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session

from app.models.database import (
    init_db, get_db, Account, Employee, Beneficiary, Transaction,
    RiskAssessment, AccountChangeHistory, BeneficiaryChangeHistory
)

def generate_comprehensive_data():
    """Generate rich sample data for dashboard visualization."""
    print("\n" + "="*80)
    print("GENERATING COMPREHENSIVE TRANSACTION DATA")
    print("="*80)

    # Initialize database
    init_db()
    db = next(get_db())

    try:
        # Clear existing data
        print("\n[1] Clearing existing data...")
        db.query(RiskAssessment).delete()
        db.query(Transaction).delete()
        db.query(BeneficiaryChangeHistory).delete()
        db.query(AccountChangeHistory).delete()
        db.query(Beneficiary).delete()
        db.query(Employee).delete()
        db.query(Account).delete()
        db.commit()

        # Create accounts
        print("\n[2] Creating accounts...")
        accounts = []
        for i in range(10):
            account = Account(
                account_id=f"ACC_{str(uuid.uuid4())[:8]}",
                creation_date=(datetime.utcnow() - timedelta(days=random.randint(365, 730))).isoformat(),
                risk_tier="standard",
                status="active"
            )
            accounts.append(account)
            db.add(account)
        db.commit()
        print(f"    Created {len(accounts)} accounts")

        # Create employees
        print("\n[3] Creating employees...")
        employees = []
        employee_names = [
            ("Alice Johnson", "Engineering"), ("Bob Smith", "Marketing"),
            ("Carol Davis", "Sales"), ("David Wilson", "Finance"),
            ("Eve Martinez", "Operations"), ("Frank Brown", "IT"),
            ("Grace Lee", "HR"), ("Henry Chen", "Legal")
        ]
        for i, (name, dept) in enumerate(employee_names):
            employee = Employee(
                employee_id=f"EMP_{str(i+1).zfill(3)}",
                account_id=accounts[i % len(accounts)].account_id,
                name=name,
                email=f"{name.lower().replace(' ', '.')}@company.com",
                department=dept,
                hire_date=(datetime.utcnow() - timedelta(days=random.randint(90, 1095))).isoformat(),
                employment_status="active",
                payroll_account_number=f"{random.randint(1000000000, 9999999999)}",
                payroll_routing_number="021000021",
                payroll_bank_name="Original Bank",
                payroll_frequency="biweekly",
                last_payroll_date=(datetime.utcnow() - timedelta(days=14)).isoformat()
            )
            employees.append(employee)
            db.add(employee)
        db.commit()
        print(f"    Created {len(employees)} employees")

        # Create beneficiaries
        print("\n[4] Creating beneficiaries...")
        beneficiaries = []
        beneficiary_names = [
            "ABC Office Supplies Inc.", "XYZ Manufacturing Ltd.",
            "Tech Solutions Corp.", "Global Logistics LLC",
            "Premier Consulting Group", "Digital Services Inc.",
            "Metro Utilities Company", "Professional Services Ltd.",
            "Wholesale Distributors Co.", "Enterprise Software Inc."
        ]
        for i, name in enumerate(beneficiary_names):
            beneficiary = Beneficiary(
                beneficiary_id=f"VENDOR{str(i+1).zfill(3)}",
                account_id=accounts[i % len(accounts)].account_id,
                name=name,
                email=f"billing@{name.lower().replace(' ', '').replace('.', '')[:20]}.com",
                phone=f"555-{random.randint(1000, 9999)}",
                bank_account_number=f"{random.randint(1000000000, 9999999999)}",
                bank_routing_number=f"{random.randint(100000000, 999999999)}",
                bank_name=f"Bank {chr(65 + i)}",
                bank_account_type="checking",
                registration_date=(datetime.utcnow() - timedelta(days=random.randint(30, 730))).isoformat(),
                status="active",
                verified=random.choice([True, True, True, False]),  # 75% verified
                last_payment_date=(datetime.utcnow() - timedelta(days=random.randint(1, 90))).isoformat(),
                total_payments_received=random.randint(5, 50),
                total_amount_received=random.uniform(10000, 500000)
            )
            beneficiaries.append(beneficiary)
            db.add(beneficiary)
        db.commit()
        print(f"    Created {len(beneficiaries)} beneficiaries")

        # Create account changes
        print("\n[5] Creating account changes...")
        change_count = 0
        for i, employee in enumerate(employees[:5]):  # 5 employees with changes
            num_changes = random.randint(1, 3)
            for j in range(num_changes):
                change = AccountChangeHistory(
                    change_id=f"CHG_{str(uuid.uuid4())[:8]}",
                    employee_id=employee.employee_id,
                    account_id=employee.account_id,
                    timestamp=(datetime.utcnow() - timedelta(days=random.randint(1, 60))).isoformat(),
                    change_type="account_number",
                    old_value=f"{random.randint(1000000000, 9999999999)}",
                    new_value=employee.payroll_account_number,
                    change_source=random.choice(["email_request", "phone_request", "secure_portal"]),
                    verified=random.choice([True, False]),
                    flagged_as_suspicious=random.choice([True, False]) if j > 0 else False
                )
                db.add(change)
                change_count += 1
        db.commit()
        print(f"    Created {change_count} account changes")

        # Create beneficiary changes
        print("\n[6] Creating beneficiary changes...")
        ben_change_count = 0
        for i, beneficiary in enumerate(beneficiaries[:4]):  # 4 beneficiaries with changes
            change = BeneficiaryChangeHistory(
                change_id=f"BCHG_{str(uuid.uuid4())[:8]}",
                beneficiary_id=beneficiary.beneficiary_id,
                account_id=beneficiary.account_id,
                timestamp=(datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
                change_type=random.choice(["account_number", "routing_number", "email"]),
                old_value=f"old_value_{i}",
                new_value=f"new_value_{i}",
                change_source=random.choice(["email_request", "phone_request", "portal"]),
                verified=random.choice([True, False]),
                flagged_as_suspicious=random.choice([True, False])
            )
            db.add(change)
            ben_change_count += 1
        db.commit()
        print(f"    Created {ben_change_count} beneficiary changes")

        # Create transactions
        print("\n[7] Creating transactions...")
        transactions = []
        transaction_types = [
            ("direct_deposit", 5000, 10000),  # Payroll
            ("vendor_payment", 2000, 50000),  # Vendor payments
            ("WIRE", 10000, 100000),  # Wires
            ("ACH", 1000, 25000),  # ACH
            ("CHECK_DEPOSIT", 500, 15000),  # Checks
            ("TRANSFER", 100, 50000),  # Transfers
        ]

        # Generate 100 transactions over the past 30 days
        for i in range(100):
            tx_type, min_amt, max_amt = random.choice(transaction_types)
            account = random.choice(accounts)

            # Select appropriate counterparty based on transaction type
            if tx_type == "direct_deposit":
                counterparty_id = "PAYROLL_SYSTEM"
                direction = "credit"
            elif tx_type == "vendor_payment":
                counterparty_id = random.choice(beneficiaries).beneficiary_id
                direction = "debit"
            else:
                counterparty_id = f"PARTY_{random.randint(1000, 9999)}"
                direction = random.choice(["credit", "debit"])

            transaction = Transaction(
                transaction_id=f"TX_{str(uuid.uuid4())[:12]}",
                account_id=account.account_id,
                timestamp=(datetime.utcnow() - timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )).isoformat(),
                amount=random.uniform(min_amt, max_amt),
                direction=direction,
                counterparty_id=counterparty_id,
                transaction_type=tx_type,
                description=f"{tx_type.replace('_', ' ').title()} - Transaction {i+1}",
                tx_metadata=json.dumps({
                    "source": "automated",
                    "reference": f"REF{random.randint(10000, 99999)}"
                })
            )
            transactions.append(transaction)
            db.add(transaction)

        db.commit()
        print(f"    Created {len(transactions)} transactions")

        # Create risk assessments
        print("\n[8] Creating risk assessments...")
        rule_templates = [
            ("payroll_recent_account_change", "Payroll to account changed within 30 days", 3.0),
            ("payroll_unverified_change", "Payroll with unverified banking changes", 4.0),
            ("beneficiary_same_day_payment", "Payment same day as beneficiary change", 4.5),
            ("beneficiary_high_value", "High-value beneficiary payment", 2.5),
            ("check_duplicate", "Potential duplicate check", 3.5),
            ("wire_high_value", "High-value wire transfer", 2.0),
            ("account_takeover_indicator", "Account takeover indicator detected", 4.0),
            ("rapid_transactions", "Rapid succession of transactions", 2.5),
        ]

        for i, transaction in enumerate(transactions):
            # Generate risk score based on transaction characteristics
            base_risk = random.uniform(0.0, 0.3)

            # Add risk for certain transaction types
            if transaction.transaction_type == "direct_deposit":
                base_risk += random.uniform(0.0, 0.5)
            elif transaction.transaction_type == "vendor_payment":
                base_risk += random.uniform(0.0, 0.4)
            elif transaction.transaction_type == "WIRE":
                base_risk += random.uniform(0.0, 0.3)

            # High amounts increase risk
            if transaction.amount > 25000:
                base_risk += 0.15

            risk_score = min(base_risk, 1.0)

            # Select 0-4 triggered rules based on risk score
            num_rules = int(risk_score * 5)
            triggered_rules = {}
            if num_rules > 0:
                selected_rules = random.sample(rule_templates, min(num_rules, len(rule_templates)))
                for rule_name, rule_desc, weight in selected_rules:
                    triggered_rules[rule_name] = {
                        "description": rule_desc,
                        "weight": weight,
                        "triggered": True
                    }

            # Determine decision
            if risk_score < 0.3:
                decision = "auto_approve"
                review_status = "approved"
            elif risk_score < 0.6:
                decision = "manual_review"
                review_status = random.choice(["pending", "approved", "rejected"])
            else:
                decision = "manual_review"
                review_status = random.choice(["pending", "pending", "approved", "rejected"])

            assessment = RiskAssessment(
                assessment_id=f"RISK_{str(uuid.uuid4())[:12]}",
                transaction_id=transaction.transaction_id,
                risk_score=risk_score,
                triggered_rules=json.dumps(triggered_rules),
                decision=decision,
                review_status=review_status,
                review_timestamp=transaction.timestamp
            )
            db.add(assessment)

        db.commit()
        print(f"    Created {len(transactions)} risk assessments")

        # Print final summary
        print("\n" + "="*80)
        print("DATA GENERATION COMPLETE")
        print("="*80)
        print("\nFinal database summary:")
        print(f"  Accounts:              {db.query(Account).count()}")
        print(f"  Employees:             {db.query(Employee).count()}")
        print(f"  Beneficiaries:         {db.query(Beneficiary).count()}")
        print(f"  Account Changes:       {db.query(AccountChangeHistory).count()}")
        print(f"  Beneficiary Changes:   {db.query(BeneficiaryChangeHistory).count()}")
        print(f"  Transactions:          {db.query(Transaction).count()}")
        print(f"  Risk Assessments:      {db.query(RiskAssessment).count()}")

        # Show risk distribution
        print("\nRisk Score Distribution:")
        low_risk = db.query(RiskAssessment).filter(RiskAssessment.risk_score < 0.3).count()
        med_risk = db.query(RiskAssessment).filter(
            RiskAssessment.risk_score >= 0.3,
            RiskAssessment.risk_score < 0.6
        ).count()
        high_risk = db.query(RiskAssessment).filter(RiskAssessment.risk_score >= 0.6).count()

        print(f"  Low Risk (< 0.3):      {low_risk}")
        print(f"  Medium Risk (0.3-0.6): {med_risk}")
        print(f"  High Risk (>= 0.6):    {high_risk}")

        # Show decision distribution
        print("\nDecision Distribution:")
        auto_approved = db.query(RiskAssessment).filter(RiskAssessment.decision == "auto_approve").count()
        manual_review = db.query(RiskAssessment).filter(RiskAssessment.decision == "manual_review").count()

        print(f"  Auto-Approved:         {auto_approved}")
        print(f"  Manual Review:         {manual_review}")

        print("\n" + "="*80)
        print("✓ Database ready for Streamlit dashboard")
        print("="*80 + "\n")

    finally:
        db.close()

if __name__ == "__main__":
    generate_comprehensive_data()
