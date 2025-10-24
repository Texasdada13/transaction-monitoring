# tests/test_beneficiary_fraud.py
"""
Unit tests for beneficiary fraud detection functionality.

Tests rapid addition of beneficiaries followed by payments - a common
pattern in compromised administrator account fraud.
"""
import unittest
from datetime import datetime, timedelta
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.database import (
    Base, Account, Beneficiary, Transaction
)
from app.services.rules_engine import RulesEngine
from app.services.context_provider import ContextProvider
from app.services.risk_scoring import RiskScorer
from app.services.decision_engine import DecisionEngine
from app.services.beneficiary_fraud_rules import (
    initialize_beneficiary_fraud_rules,
)


class TestBeneficiaryFraudDetection(unittest.TestCase):
    """Test cases for beneficiary fraud detection."""

    def setUp(self):
        """Set up test database and components."""
        # Create in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        SessionLocal = sessionmaker(bind=self.engine)
        self.db = SessionLocal()

        # Initialize components
        self.rules_engine = RulesEngine()
        self.context_provider = ContextProvider(self.db, enable_chain_analysis=False)

        # Add beneficiary fraud rules
        beneficiary_rules = initialize_beneficiary_fraud_rules(self.db)
        for rule in beneficiary_rules:
            self.rules_engine.add_rule(rule)

        self.risk_scorer = RiskScorer(self.rules_engine)
        self.decision_engine = DecisionEngine(self.risk_scorer)

    def tearDown(self):
        """Clean up test database."""
        self.db.close()

    def _create_test_account(self) -> Account:
        """Create a test account."""
        account = Account(
            account_id="TEST_ACC_" + str(uuid.uuid4())[:8],
            risk_tier="medium"
        )
        self.db.add(account)
        self.db.commit()
        return account

    def _create_beneficiary(
        self,
        account: Account,
        hours_ago: float = 1.0,
        added_by: str = "ADMIN_001",
        ip_address: str = "192.168.1.100",
        verified: bool = False,
        source: str = "admin_portal"
    ) -> Beneficiary:
        """Create a test beneficiary."""
        added_time = datetime.utcnow() - timedelta(hours=hours_ago)
        beneficiary = Beneficiary(
            beneficiary_id="BEN_" + str(uuid.uuid4())[:8],
            account_id=account.account_id,
            counterparty_id="COUNTERPARTY_" + str(uuid.uuid4())[:8],
            beneficiary_name="Test Beneficiary",
            beneficiary_account_number="9876543210",
            beneficiary_routing_number="021000021",
            beneficiary_type="individual",
            added_timestamp=added_time.isoformat(),
            added_by=added_by,
            addition_source=source,
            ip_address=ip_address,
            verified=verified
        )
        self.db.add(beneficiary)
        self.db.commit()
        return beneficiary

    def _create_payment_transaction(
        self,
        account: Account,
        beneficiary: Beneficiary,
        amount: float = 5000.0
    ) -> dict:
        """Create a test payment transaction."""
        return {
            "transaction_id": str(uuid.uuid4()),
            "account_id": account.account_id,
            "amount": amount,
            "direction": "debit",
            "transaction_type": "ACH",
            "description": "Payment to beneficiary",
            "timestamp": datetime.utcnow().isoformat(),
            "counterparty_id": beneficiary.counterparty_id
        }

    def test_legitimate_beneficiary_low_risk(self):
        """Test that payment to established beneficiary has low risk."""
        account = self._create_test_account()

        # Create beneficiary added 30 days ago (well-established)
        beneficiary = self._create_beneficiary(
            account,
            hours_ago=30*24,  # 30 days
            verified=True
        )

        transaction = self._create_payment_transaction(account, beneficiary)

        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should be low risk
        self.assertLess(result["risk_assessment"]["risk_score"], 0.3)
        self.assertEqual(result["decision"], "auto_approve")

    def test_rapid_beneficiary_addition_detection(self):
        """Test detection of rapid addition of many beneficiaries."""
        account = self._create_test_account()

        # Add 6 beneficiaries in the last 12 hours (exceeds threshold of 5)
        beneficiaries = []
        for i in range(6):
            beneficiary = self._create_beneficiary(
                account,
                hours_ago=12 - i,
                added_by="ADMIN_001"
            )
            beneficiaries.append(beneficiary)

        # Create payment to one of the newly added beneficiaries
        transaction = self._create_payment_transaction(account, beneficiaries[0])

        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should trigger rapid addition detection
        self.assertGreater(result["risk_assessment"]["risk_score"], 0.6)
        self.assertEqual(result["decision"], "manual_review")

        triggered = result["risk_assessment"]["triggered_rules"]
        self.assertIn("rapid_beneficiary_addition_24h", triggered)

    def test_bulk_beneficiary_addition_detection(self):
        """Test detection of bulk/scripted beneficiary additions."""
        account = self._create_test_account()

        # Add 12 beneficiaries in the last 48 hours (bulk threshold)
        beneficiaries = []
        for i in range(12):
            beneficiary = self._create_beneficiary(
                account,
                hours_ago=48 - i*3,
                added_by="ADMIN_001"
            )
            beneficiaries.append(beneficiary)

        transaction = self._create_payment_transaction(account, beneficiaries[0])

        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should trigger bulk addition detection
        self.assertGreaterEqual(result["risk_assessment"]["risk_score"], 0.3)

        triggered = result["risk_assessment"]["triggered_rules"]
        # Should trigger at least one bulk-related rule
        bulk_rules = [k for k in triggered if "bulk" in k or "rapid" in k]
        self.assertGreater(len(bulk_rules), 0)

    def test_payment_to_new_beneficiary_detection(self):
        """Test detection of payments to recently added beneficiaries."""
        account = self._create_test_account()

        # Add beneficiary 24 hours ago (within recent window)
        beneficiary = self._create_beneficiary(
            account,
            hours_ago=24,
            verified=False
        )

        transaction = self._create_payment_transaction(account, beneficiary)

        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should trigger new beneficiary payment detection
        triggered = result["risk_assessment"]["triggered_rules"]
        self.assertIn("payment_to_new_beneficiary_48h", triggered)

    def test_high_new_beneficiary_payment_ratio(self):
        """Test detection when most payments go to new beneficiaries."""
        account = self._create_test_account()

        # Create 5 new beneficiaries (added in last 24 hours)
        new_beneficiaries = []
        for i in range(5):
            beneficiary = self._create_beneficiary(
                account,
                hours_ago=20 - i,
                added_by="ADMIN_001"
            )
            new_beneficiaries.append(beneficiary)

        # Create 1 old beneficiary (added 60 days ago)
        old_beneficiary = self._create_beneficiary(
            account,
            hours_ago=60*24,
            verified=True
        )

        # Create payments to new beneficiaries (4 payments)
        for i in range(4):
            tx = Transaction(
                transaction_id="TX_NEW_" + str(i),
                account_id=account.account_id,
                amount=1000.0,
                direction="debit",
                transaction_type="ACH",
                counterparty_id=new_beneficiaries[i].counterparty_id,
                timestamp=(datetime.utcnow() - timedelta(hours=10-i)).isoformat()
            )
            self.db.add(tx)

        # Create payment to old beneficiary (1 payment)
        tx = Transaction(
            transaction_id="TX_OLD_1",
            account_id=account.account_id,
            amount=1000.0,
            direction="debit",
            transaction_type="ACH",
            counterparty_id=old_beneficiary.counterparty_id,
            timestamp=(datetime.utcnow() - timedelta(hours=5)).isoformat()
        )
        self.db.add(tx)
        self.db.commit()

        # Test current payment to new beneficiary
        # Ratio: 4 to new / 5 total = 80% (exceeds 70% threshold)
        transaction = self._create_payment_transaction(account, new_beneficiaries[4])

        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        triggered = result["risk_assessment"]["triggered_rules"]
        self.assertIn("high_new_beneficiary_payment_ratio_24h", triggered)

    def test_same_source_bulk_addition_detection(self):
        """Test detection of beneficiaries added from same IP/user."""
        account = self._create_test_account()

        # Add 7 beneficiaries from same IP in last 12 hours
        beneficiaries = []
        same_ip = "10.0.0.42"
        for i in range(7):
            beneficiary = self._create_beneficiary(
                account,
                hours_ago=12 - i,
                added_by="ADMIN_001",
                ip_address=same_ip
            )
            beneficiaries.append(beneficiary)

        transaction = self._create_payment_transaction(account, beneficiaries[0])

        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should trigger same-source bulk addition
        triggered = result["risk_assessment"]["triggered_rules"]
        self.assertIn("same_source_bulk_addition_24h", triggered)

        # Verify context contains source information
        self.assertEqual(context["same_source_ip"], same_ip)

    def test_same_user_bulk_addition_detection(self):
        """Test detection of beneficiaries added by same user."""
        account = self._create_test_account()

        # Add 6 beneficiaries by same user from different IPs
        beneficiaries = []
        same_user = "COMPROMISED_ADMIN"
        for i in range(6):
            beneficiary = self._create_beneficiary(
                account,
                hours_ago=18 - i*2,
                added_by=same_user,
                ip_address=f"192.168.1.{100+i}"  # Different IPs
            )
            beneficiaries.append(beneficiary)

        transaction = self._create_payment_transaction(account, beneficiaries[0])

        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should trigger same-user bulk addition
        triggered = result["risk_assessment"]["triggered_rules"]
        self.assertIn("same_source_bulk_addition_24h", triggered)

        # Verify context contains user information
        self.assertEqual(context["same_source_user"], same_user)

    def test_unverified_beneficiary_payment_detection(self):
        """Test detection of payments to unverified beneficiaries."""
        account = self._create_test_account()

        # Create unverified beneficiary
        beneficiary = self._create_beneficiary(
            account,
            hours_ago=10,
            verified=False
        )

        transaction = self._create_payment_transaction(account, beneficiary)

        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should trigger unverified payment detection
        triggered = result["risk_assessment"]["triggered_rules"]
        self.assertIn("payment_to_unverified_beneficiary", triggered)

    def test_combined_fraud_scenario_very_high_risk(self):
        """Test full fraud scenario: rapid additions + payments to new beneficiaries."""
        account = self._create_test_account()

        # Simulate compromised admin account fraud scenario:
        # 1. Rapid addition of 8 beneficiaries in 12 hours
        # 2. All from same IP (scripted)
        # 3. All unverified
        # 4. Followed by payments

        beneficiaries = []
        fraud_ip = "203.0.113.42"
        fraud_admin = "COMPROMISED_ADMIN"

        for i in range(8):
            beneficiary = self._create_beneficiary(
                account,
                hours_ago=12 - i,
                added_by=fraud_admin,
                ip_address=fraud_ip,
                verified=False,
                source="api"  # Suggests scripted addition
            )
            beneficiaries.append(beneficiary)

        # Create payments to several new beneficiaries
        for i in range(5):
            tx = Transaction(
                transaction_id="TX_FRAUD_" + str(i),
                account_id=account.account_id,
                amount=9000.0,  # High value
                direction="debit",
                transaction_type="WIRE",
                counterparty_id=beneficiaries[i].counterparty_id,
                timestamp=(datetime.utcnow() - timedelta(hours=6-i)).isoformat()
            )
            self.db.add(tx)
        self.db.commit()

        # Evaluate current payment
        transaction = self._create_payment_transaction(account, beneficiaries[5], amount=9500.0)

        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should be very high risk
        self.assertGreaterEqual(result["risk_assessment"]["risk_score"], 0.8)
        self.assertEqual(result["decision"], "manual_review")

        # Should trigger multiple rules
        triggered = result["risk_assessment"]["triggered_rules"]
        self.assertIn("rapid_beneficiary_addition_24h", triggered)
        # Note: bulk_beneficiary_addition_72h requires 10+ beneficiaries, we have 8
        self.assertIn("payment_to_new_beneficiary_48h", triggered)
        self.assertIn("same_source_bulk_addition_24h", triggered)
        self.assertIn("payment_to_unverified_beneficiary", triggered)
        self.assertIn("high_new_beneficiary_payment_ratio_24h", triggered)
        # Verify we triggered at least 5 rules (strong fraud signal)
        self.assertGreaterEqual(len(triggered), 5)

    def test_beneficiary_context_provider(self):
        """Test that beneficiary context provider returns correct data."""
        account = self._create_test_account()

        # Add some beneficiaries
        ben1 = self._create_beneficiary(account, hours_ago=10)
        ben2 = self._create_beneficiary(account, hours_ago=15)
        ben3 = self._create_beneficiary(account, hours_ago=50)

        transaction = self._create_payment_transaction(account, ben1)

        context = self.context_provider.get_transaction_context(transaction)

        # Verify context contains expected keys
        self.assertIn("beneficiaries_added_24h", context)
        self.assertEqual(context["beneficiaries_added_24h"], 2)  # ben1 and ben2

        self.assertIn("beneficiaries_added_72h", context)
        self.assertEqual(context["beneficiaries_added_72h"], 3)  # all three

        self.assertIn("is_new_beneficiary", context)
        self.assertTrue(context["is_new_beneficiary"])  # ben1 is < 48h old

        self.assertIn("beneficiary_age_hours", context)
        self.assertLess(context["beneficiary_age_hours"], 12)

    def test_old_beneficiary_not_flagged_as_new(self):
        """Test that old beneficiaries are not flagged as new."""
        account = self._create_test_account()

        # Create beneficiary added 60 days ago
        beneficiary = self._create_beneficiary(
            account,
            hours_ago=60*24,
            verified=True
        )

        transaction = self._create_payment_transaction(account, beneficiary)

        context = self.context_provider.get_transaction_context(transaction)

        # Should not be flagged as new
        self.assertFalse(context["is_new_beneficiary"])
        self.assertGreater(context["beneficiary_age_hours"], 48)

    def test_no_false_positives_for_gradual_additions(self):
        """Test that gradual beneficiary additions don't trigger false positives."""
        account = self._create_test_account()

        # Add 4 beneficiaries over 7 days (gradual, legitimate)
        beneficiaries = []
        for i in range(4):
            beneficiary = self._create_beneficiary(
                account,
                hours_ago=(7-i)*24,
                added_by="ADMIN_001",
                verified=True,
                source="admin_portal"
            )
            beneficiaries.append(beneficiary)

        # Payment to most recently added (but not rapid)
        transaction = self._create_payment_transaction(account, beneficiaries[3])

        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should not trigger rapid addition (only 1 in 24h window)
        triggered = result["risk_assessment"]["triggered_rules"]
        self.assertNotIn("rapid_beneficiary_addition_24h", triggered)
        self.assertNotIn("bulk_beneficiary_addition_72h", triggered)

    def test_verified_beneficiary_lower_risk(self):
        """Test that verified beneficiaries have lower risk."""
        account = self._create_test_account()

        # Create verified beneficiary added recently
        beneficiary = self._create_beneficiary(
            account,
            hours_ago=20,
            verified=True
        )

        transaction = self._create_payment_transaction(account, beneficiary)

        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should not trigger unverified payment rule
        triggered = result["risk_assessment"]["triggered_rules"]
        self.assertNotIn("payment_to_unverified_beneficiary", triggered)


if __name__ == "__main__":
    unittest.main()
