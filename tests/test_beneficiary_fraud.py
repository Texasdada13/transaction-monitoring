# tests/test_beneficiary_fraud.py
"""
Unit tests for beneficiary/vendor fraud detection functionality.
"""
import unittest
from datetime import datetime, timedelta
import uuid
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.database import (
    Base, Account, Beneficiary, BeneficiaryChangeHistory,
    Transaction, RiskAssessment
)
from app.services.rules_engine import RulesEngine
from app.services.context_provider import ContextProvider
from app.services.risk_scoring import RiskScorer
from app.services.decision_engine import DecisionEngine
from app.services.beneficiary_fraud_rules import (
    initialize_beneficiary_fraud_rules,
    is_beneficiary_payment,
)


class TestBeneficiaryFraudDetection(unittest.TestCase):
    """Test cases for beneficiary/vendor fraud detection."""

    def setUp(self):
        """Set up test database and components."""
        # Create in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        SessionLocal = sessionmaker(bind=self.engine)
        self.db = SessionLocal()

        # Initialize components
        self.rules_engine = RulesEngine()
        self.context_provider = ContextProvider(self.db)

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

    def _create_test_beneficiary(
        self,
        account: Account,
        beneficiary_id: str = None,
        days_since_registration: int = 365,
        last_payment_days_ago: int = 30
    ) -> Beneficiary:
        """Create a test beneficiary."""
        beneficiary = Beneficiary(
            beneficiary_id=beneficiary_id or "VENDOR_" + str(uuid.uuid4())[:8],
            account_id=account.account_id,
            name="Test Supplier Inc.",
            beneficiary_type="supplier",
            email="accounts@supplier.com",
            bank_account_number="9876543210",
            bank_routing_number="021000021",
            bank_name="Test Bank",
            registration_date=(datetime.utcnow() - timedelta(days=days_since_registration)).isoformat(),
            last_payment_date=(datetime.utcnow() - timedelta(days=last_payment_days_ago)).isoformat(),
            total_payments_received=10,
            total_amount_received=100000.0,
            verified=True
        )
        self.db.add(beneficiary)
        self.db.commit()
        return beneficiary

    def _create_beneficiary_change(
        self,
        beneficiary: Beneficiary,
        change_type: str = "account_number",
        change_source: str = "email_request",
        verified: bool = False,
        hours_ago: int = 2
    ) -> BeneficiaryChangeHistory:
        """Create a test beneficiary change record."""
        change = BeneficiaryChangeHistory(
            change_id=str(uuid.uuid4()),
            beneficiary_id=beneficiary.beneficiary_id,
            account_id=beneficiary.account_id,
            change_type=change_type,
            old_value="****1234",
            new_value="****9999",
            change_source=change_source,
            timestamp=(datetime.utcnow() - timedelta(hours=hours_ago)).isoformat(),
            verified=verified,
            requestor_email="attacker@fake.com"
        )
        self.db.add(change)
        self.db.commit()
        return change

    def _create_payment_transaction(
        self,
        account: Account,
        beneficiary: Beneficiary,
        amount: float = 10000.0
    ) -> dict:
        """Create a test payment transaction."""
        return {
            "transaction_id": "TX_" + str(uuid.uuid4())[:8],
            "account_id": account.account_id,
            "counterparty_id": beneficiary.beneficiary_id,
            "amount": amount,
            "direction": "debit",
            "transaction_type": "vendor_payment",
            "description": "Invoice Payment",
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": json.dumps({"beneficiary_id": beneficiary.beneficiary_id})
        }

    # =========================================================================
    # Test: Transaction Type Detection
    # =========================================================================

    def test_is_beneficiary_payment(self):
        """Test that beneficiary payments are correctly identified."""
        # Should be identified as beneficiary payment
        self.assertTrue(is_beneficiary_payment({
            "transaction_type": "vendor_payment",
            "direction": "debit"
        }))

        self.assertTrue(is_beneficiary_payment({
            "transaction_type": "wire_transfer",
            "direction": "debit",
            "description": "Payment to supplier"
        }))

        # Should NOT be identified as beneficiary payment (incoming)
        self.assertFalse(is_beneficiary_payment({
            "transaction_type": "vendor_payment",
            "direction": "credit"
        }))

        # Should NOT be identified as beneficiary payment (wrong type)
        self.assertFalse(is_beneficiary_payment({
            "transaction_type": "deposit",
            "direction": "debit"
        }))

    # =========================================================================
    # Test: Same-Day Payment After Change (CRITICAL)
    # =========================================================================

    def test_same_day_payment_after_change_triggers(self):
        """Test that same-day payment after account change triggers critical rule."""
        account = self._create_test_account()
        beneficiary = self._create_test_beneficiary(account)

        # Create account change 2 hours ago
        self._create_beneficiary_change(
            beneficiary,
            hours_ago=2,
            verified=False,
            change_source="email_request"
        )

        # Create payment transaction
        transaction = self._create_payment_transaction(account, beneficiary, 15000.0)

        # Evaluate
        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should trigger same-day payment rule
        self.assertIn("beneficiary_same_day_payment", result["risk_assessment"]["triggered_rules"])
        self.assertGreater(result["risk_assessment"]["risk_score"], 0.5)
        self.assertEqual(result["decision"], "manual_review")

    def test_same_day_payment_no_change_does_not_trigger(self):
        """Test that payment without recent change doesn't trigger same-day rule."""
        account = self._create_test_account()
        beneficiary = self._create_test_beneficiary(account)

        # No account changes

        # Create payment transaction
        transaction = self._create_payment_transaction(account, beneficiary, 5000.0)

        # Evaluate
        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should NOT trigger same-day payment rule
        self.assertNotIn("beneficiary_same_day_payment", result["risk_assessment"]["triggered_rules"])

    # =========================================================================
    # Test: Recent Account Change Detection
    # =========================================================================

    def test_recent_account_change_within_7_days(self):
        """Test detection of payments within 7 days of account change."""
        account = self._create_test_account()
        beneficiary = self._create_test_beneficiary(account)

        # Create account change 3 days ago (72 hours)
        self._create_beneficiary_change(
            beneficiary,
            hours_ago=72,
            verified=True,
            change_source="phone_request"
        )

        # Create payment transaction
        transaction = self._create_payment_transaction(account, beneficiary, 20000.0)

        # Evaluate
        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should trigger recent change rule
        self.assertIn("beneficiary_recent_account_change", result["risk_assessment"]["triggered_rules"])
        self.assertGreater(result["risk_assessment"]["risk_score"], 0.3)

    def test_old_account_change_does_not_trigger(self):
        """Test that old account changes don't trigger recent change rule."""
        account = self._create_test_account()
        beneficiary = self._create_test_beneficiary(account)

        # Create account change 30 days ago
        self._create_beneficiary_change(
            beneficiary,
            hours_ago=30 * 24,  # 30 days
            verified=True
        )

        # Create payment transaction
        transaction = self._create_payment_transaction(account, beneficiary, 5000.0)

        # Evaluate
        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should NOT trigger recent change rule
        self.assertNotIn("beneficiary_recent_account_change", result["risk_assessment"]["triggered_rules"])

    # =========================================================================
    # Test: Unverified Account Change Detection
    # =========================================================================

    def test_unverified_change_triggers_high_risk(self):
        """Test that unverified account changes trigger high risk."""
        account = self._create_test_account()
        beneficiary = self._create_test_beneficiary(account)

        # Create UNVERIFIED change
        self._create_beneficiary_change(
            beneficiary,
            hours_ago=12,
            verified=False,
            change_source="email_request"
        )

        # Create payment transaction
        transaction = self._create_payment_transaction(account, beneficiary, 10000.0)

        # Evaluate
        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should trigger unverified change rule
        self.assertIn("beneficiary_unverified_account_change", result["risk_assessment"]["triggered_rules"])
        self.assertGreater(result["risk_assessment"]["risk_score"], 0.5)

    # =========================================================================
    # Test: Suspicious Change Source Detection
    # =========================================================================

    def test_email_change_source_triggers_suspicious(self):
        """Test that email-sourced changes are flagged as suspicious."""
        account = self._create_test_account()
        beneficiary = self._create_test_beneficiary(account)

        # Create email-sourced change
        self._create_beneficiary_change(
            beneficiary,
            hours_ago=6,
            change_source="email_request",
            verified=False
        )

        # Create payment transaction
        transaction = self._create_payment_transaction(account, beneficiary, 8000.0)

        # Evaluate
        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should trigger suspicious source rule
        self.assertIn("beneficiary_suspicious_change_source", result["risk_assessment"]["triggered_rules"])

    def test_portal_change_source_not_suspicious(self):
        """Test that portal-sourced changes are not flagged as suspicious source."""
        account = self._create_test_account()
        beneficiary = self._create_test_beneficiary(account)

        # Create portal-sourced change
        self._create_beneficiary_change(
            beneficiary,
            hours_ago=6,
            change_source="ap_portal",  # Not suspicious
            verified=True
        )

        # Create payment transaction
        transaction = self._create_payment_transaction(account, beneficiary, 8000.0)

        # Evaluate
        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should NOT trigger suspicious source rule
        self.assertNotIn("beneficiary_suspicious_change_source", result["risk_assessment"]["triggered_rules"])

    # =========================================================================
    # Test: High-Value Payment Detection
    # =========================================================================

    def test_high_value_payment_triggers(self):
        """Test that high-value payments are flagged."""
        account = self._create_test_account()
        beneficiary = self._create_test_beneficiary(account)

        # Create high-value payment (>= $10,000)
        transaction = self._create_payment_transaction(account, beneficiary, 25000.0)

        # Evaluate
        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should trigger high-value rule
        self.assertIn("beneficiary_high_value_payment", result["risk_assessment"]["triggered_rules"])

    def test_low_value_payment_does_not_trigger(self):
        """Test that low-value payments don't trigger high-value rule."""
        account = self._create_test_account()
        beneficiary = self._create_test_beneficiary(account)

        # Create low-value payment
        transaction = self._create_payment_transaction(account, beneficiary, 500.0)

        # Evaluate
        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should NOT trigger high-value rule
        self.assertNotIn("beneficiary_high_value_payment", result["risk_assessment"]["triggered_rules"])

    # =========================================================================
    # Test: New Beneficiary Detection
    # =========================================================================

    def test_new_beneficiary_within_90_days(self):
        """Test that payments to new beneficiaries are flagged."""
        account = self._create_test_account()

        # Create new beneficiary (registered 45 days ago)
        beneficiary = self._create_test_beneficiary(
            account,
            days_since_registration=45
        )

        # Create payment transaction
        transaction = self._create_payment_transaction(account, beneficiary, 5000.0)

        # Evaluate
        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should trigger new vendor rule
        self.assertIn("beneficiary_new_vendor_payment", result["risk_assessment"]["triggered_rules"])

    def test_established_beneficiary_does_not_trigger(self):
        """Test that payments to established beneficiaries don't trigger new vendor rule."""
        account = self._create_test_account()

        # Create established beneficiary (registered 500 days ago)
        beneficiary = self._create_test_beneficiary(
            account,
            days_since_registration=500
        )

        # Create payment transaction
        transaction = self._create_payment_transaction(account, beneficiary, 5000.0)

        # Evaluate
        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should NOT trigger new vendor rule
        self.assertNotIn("beneficiary_new_vendor_payment", result["risk_assessment"]["triggered_rules"])

    # =========================================================================
    # Test: Multiple Risk Factors (Compound Risk)
    # =========================================================================

    def test_multiple_risk_factors_compound(self):
        """Test that multiple risk factors result in high compound risk score."""
        account = self._create_test_account()
        beneficiary = self._create_test_beneficiary(account, days_since_registration=30)

        # Create UNVERIFIED email change 3 hours ago (multiple red flags)
        self._create_beneficiary_change(
            beneficiary,
            hours_ago=3,
            verified=False,
            change_source="email_request"
        )

        # Create HIGH-VALUE payment
        transaction = self._create_payment_transaction(account, beneficiary, 50000.0)

        # Evaluate
        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should trigger multiple rules
        triggered = result["risk_assessment"]["triggered_rules"]
        self.assertIn("beneficiary_same_day_payment", triggered)
        self.assertIn("beneficiary_unverified_account_change", triggered)
        self.assertIn("beneficiary_suspicious_change_source", triggered)
        self.assertIn("beneficiary_high_value_payment", triggered)
        self.assertIn("beneficiary_new_vendor_payment", triggered)

        # Should have very high risk score
        self.assertGreater(result["risk_assessment"]["risk_score"], 0.7)
        self.assertEqual(result["decision"], "manual_review")

    # =========================================================================
    # Test: Legitimate Transaction (Low Risk)
    # =========================================================================

    def test_legitimate_payment_low_risk(self):
        """Test that legitimate payments have low risk scores."""
        account = self._create_test_account()

        # Established vendor, no recent changes
        beneficiary = self._create_test_beneficiary(
            account,
            days_since_registration=800,
            last_payment_days_ago=30
        )

        # Regular payment, moderate amount
        transaction = self._create_payment_transaction(account, beneficiary, 5000.0)

        # Evaluate
        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should have low risk score
        self.assertLess(result["risk_assessment"]["risk_score"], 0.3)
        self.assertEqual(result["decision"], "auto_approve")

    # =========================================================================
    # Test: Rapid Multiple Changes
    # =========================================================================

    def test_rapid_multiple_changes_triggers(self):
        """Test that multiple rapid account changes are flagged."""
        account = self._create_test_account()
        beneficiary = self._create_test_beneficiary(account)

        # Create multiple changes within 60 days
        for i in range(3):
            change = BeneficiaryChangeHistory(
                change_id=str(uuid.uuid4()),
                beneficiary_id=beneficiary.beneficiary_id,
                account_id=beneficiary.account_id,
                change_type="account_number",
                old_value=f"****{i}000",
                new_value=f"****{i}111",
                change_source="email_request",
                timestamp=(datetime.utcnow() - timedelta(days=i * 15)).isoformat(),
                verified=False
            )
            self.db.add(change)
        self.db.commit()

        # Create payment transaction
        transaction = self._create_payment_transaction(account, beneficiary, 8000.0)

        # Evaluate
        context = self.context_provider.get_transaction_context(transaction)
        result = self.decision_engine.evaluate(transaction, context)

        # Should trigger rapid changes rule
        self.assertIn("beneficiary_rapid_account_changes", result["risk_assessment"]["triggered_rules"])


if __name__ == "__main__":
    unittest.main()
