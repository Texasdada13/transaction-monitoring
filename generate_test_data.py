"""Simple test data generator"""
from datetime import datetime, timedelta
import random
from app.models.database import init_db, get_db, Transaction, RiskAssessment, Account

def generate_data():
    # Initialize database
    init_db()
    db = next(get_db())
    
    # Clear old data
    db.query(RiskAssessment).delete()
    db.query(Transaction).delete()
    db.query(Account).delete()
    db.commit()
    
    print("Generating test data...")
    
    # Create accounts
    accounts = []
    for i in range(10):
        account = Account(
            account_id=f"ACC_{i:04d}",
            creation_date=datetime.utcnow().isoformat(),
            risk_tier="medium",
            status="active"
        )
        db.add(account)
        accounts.append(account)
    
    db.commit()
    print(f"Created {len(accounts)} accounts")
    
    # Create transactions
    for i in range(100):
        account = random.choice(accounts)
        amount = random.uniform(100, 50000)
        
        tx = Transaction(
            transaction_id=f"TX_{i:06d}",
            account_id=account.account_id,
            amount=amount,
            direction=random.choice(["debit", "credit"]),
            transaction_type=random.choice(["wire", "ach", "check", "transfer"]),
            timestamp=(datetime.utcnow() - timedelta(hours=random.randint(0, 24))).isoformat(),
            counterparty_id=f"COUNTER_{random.randint(1, 50):04d}",
            description=f"Test transaction {i}"
        )
        db.add(tx)
        
        # Create risk assessment
        risk_score = random.uniform(0.1, 0.9)
        assessment = RiskAssessment(
            assessment_id=f"RISK_{i:06d}",
            transaction_id=tx.transaction_id,
            risk_score=risk_score,
            decision="manual_review" if risk_score > 0.6 else "auto_approve",
            triggered_rules='{"test_rule": {"weight": 0.3, "description": "Test rule"}}',
            review_status="pending",
            review_timestamp=tx.timestamp
        )
        db.add(assessment)
    
    db.commit()
    print("Created 100 transactions with risk assessments")
    print("Done! Refresh your dashboard to see the data.")

if __name__ == "__main__":
    generate_data()