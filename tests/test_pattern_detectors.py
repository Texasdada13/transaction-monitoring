# tests/test_pattern_detectors.py
import unittest
from unittest.mock import MagicMock, patch
import datetime
from app.services.pattern_detectors import SmallTestLargeWithdrawalDetector, create_small_test_pattern_detector


class TestSmallTestLargeWithdrawalDetector(unittest.TestCase):
    """Test suite for SmallTestLargeWithdrawalDetector."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = MagicMock()
        self.detector = SmallTestLargeWithdrawalDetector(
            db=self.mock_db,
            small_amount_threshold=50.0,
            large_amount_threshold=1000.0,
            min_small_transactions=3,
            lookback_hours=24
        )

    def _create_mock_transaction(self, amount, transaction_type, timestamp=None):
        """Helper to create mock transaction objects."""
        mock_tx = MagicMock()
        mock_tx.amount = amount
        mock_tx.transaction_type = transaction_type
        mock_tx.timestamp = timestamp or datetime.datetime.utcnow().isoformat()
        return mock_tx

    def test_pattern_not_detected_small_withdrawal(self):
        """Test that pattern is not detected when withdrawal is too small."""
        transaction = {
            "account_id": "ACC123",
            "amount": 500.0,  # Below threshold
            "transaction_type": "WITHDRAWAL"
        }
        context = {}

        result = self.detector.detect(transaction, context)

        self.assertFalse(result["detected"])
        self.assertEqual(result["confidence"], 0.0)
        self.assertIn("amount too small", result["details"]["reason"].lower())

    def test_pattern_not_detected_not_withdrawal(self):
        """Test that pattern is not detected when transaction is not a withdrawal."""
        transaction = {
            "account_id": "ACC123",
            "amount": 1500.0,
            "transaction_type": "DEPOSIT"  # Not a withdrawal
        }
        context = {}

        result = self.detector.detect(transaction, context)

        self.assertFalse(result["detected"])
        self.assertIn("not a withdrawal", result["details"]["reason"].lower())

    def test_pattern_not_detected_insufficient_small_transactions(self):
        """Test that pattern is not detected with too few small transactions."""
        transaction = {
            "account_id": "ACC123",
            "amount": 1500.0,
            "transaction_type": "WITHDRAWAL"
        }
        context = {}

        # Mock only 2 small transactions (need 3)
        self.mock_db.query.return_value.filter.return_value.all.return_value = [
            self._create_mock_transaction(25.0, "DEPOSIT"),
            self._create_mock_transaction(30.0, "DEPOSIT")
        ]

        result = self.detector.detect(transaction, context)

        self.assertFalse(result["detected"])
        self.assertEqual(result["details"]["small_transaction_count"], 2)
        self.assertIn("only 2 small transactions", result["details"]["reason"].lower())

    def test_pattern_detected_basic(self):
        """Test that pattern is detected with valid conditions."""
        transaction = {
            "account_id": "ACC123",
            "amount": 2000.0,
            "transaction_type": "WIRE"
        }
        context = {}

        # Mock 4 small transactions
        now = datetime.datetime.utcnow()
        self.mock_db.query.return_value.filter.return_value.all.return_value = [
            self._create_mock_transaction(20.0, "DEPOSIT", (now - datetime.timedelta(hours=2)).isoformat()),
            self._create_mock_transaction(30.0, "DEPOSIT", (now - datetime.timedelta(hours=3)).isoformat()),
            self._create_mock_transaction(40.0, "DEPOSIT", (now - datetime.timedelta(hours=4)).isoformat()),
            self._create_mock_transaction(25.0, "DEPOSIT", (now - datetime.timedelta(hours=5)).isoformat())
        ]

        result = self.detector.detect(transaction, context)

        self.assertTrue(result["detected"])
        self.assertGreater(result["confidence"], 0.0)
        self.assertEqual(result["details"]["small_transaction_count"], 4)
        self.assertEqual(result["details"]["large_withdrawal_amount"], 2000.0)

    def test_confidence_calculation_high_ratio(self):
        """Test confidence is higher with larger withdrawal-to-small ratio."""
        transaction = {
            "account_id": "ACC123",
            "amount": 5000.0,  # Very large withdrawal
            "transaction_type": "WITHDRAWAL"
        }
        context = {}

        # Mock 5 very small transactions
        now = datetime.datetime.utcnow()
        self.mock_db.query.return_value.filter.return_value.all.return_value = [
            self._create_mock_transaction(10.0, "DEPOSIT", (now - datetime.timedelta(hours=1)).isoformat()),
            self._create_mock_transaction(15.0, "DEPOSIT", (now - datetime.timedelta(hours=2)).isoformat()),
            self._create_mock_transaction(12.0, "DEPOSIT", (now - datetime.timedelta(hours=3)).isoformat()),
            self._create_mock_transaction(8.0, "DEPOSIT", (now - datetime.timedelta(hours=4)).isoformat()),
            self._create_mock_transaction(10.0, "DEPOSIT", (now - datetime.timedelta(hours=5)).isoformat())
        ]

        result = self.detector.detect(transaction, context)

        self.assertTrue(result["detected"])
        self.assertGreater(result["confidence"], 0.5)
        # Ratio should be very high (5000 / avg ~11)
        self.assertGreater(result["details"]["amount_ratio"], 400)

    def test_confidence_calculation_many_small_transactions(self):
        """Test confidence increases with more small transactions."""
        transaction = {
            "account_id": "ACC123",
            "amount": 1500.0,
            "transaction_type": "WITHDRAWAL"
        }
        context = {}

        # Mock 10 small transactions
        now = datetime.datetime.utcnow()
        small_txs = [
            self._create_mock_transaction(
                amount=25.0 + (i * 2),
                transaction_type="DEPOSIT",
                timestamp=(now - datetime.timedelta(hours=i+1)).isoformat()
            )
            for i in range(10)
        ]
        self.mock_db.query.return_value.filter.return_value.all.return_value = small_txs

        result = self.detector.detect(transaction, context)

        self.assertTrue(result["detected"])
        self.assertEqual(result["details"]["small_transaction_count"], 10)
        # With 10 transactions, count_score should be maxed at 1.0
        self.assertEqual(result["details"]["confidence_breakdown"]["count_score"], 1.0)

    def test_different_withdrawal_types(self):
        """Test pattern detection works with different withdrawal types."""
        withdrawal_types = ["WITHDRAWAL", "WIRE", "ACH_OUT", "TRANSFER_OUT"]

        for withdrawal_type in withdrawal_types:
            with self.subTest(withdrawal_type=withdrawal_type):
                transaction = {
                    "account_id": "ACC123",
                    "amount": 1500.0,
                    "transaction_type": withdrawal_type
                }
                context = {}

                now = datetime.datetime.utcnow()
                self.mock_db.query.return_value.filter.return_value.all.return_value = [
                    self._create_mock_transaction(20.0, "DEPOSIT", (now - datetime.timedelta(hours=1)).isoformat()),
                    self._create_mock_transaction(30.0, "DEPOSIT", (now - datetime.timedelta(hours=2)).isoformat()),
                    self._create_mock_transaction(40.0, "DEPOSIT", (now - datetime.timedelta(hours=3)).isoformat())
                ]

                result = self.detector.detect(transaction, context)
                self.assertTrue(result["detected"], f"Should detect for {withdrawal_type}")

    def test_get_pattern_context(self):
        """Test get_pattern_context returns correct data."""
        account_id = "ACC123"

        now = datetime.datetime.utcnow()
        self.mock_db.query.return_value.filter.return_value.all.return_value = [
            self._create_mock_transaction(20.0, "DEPOSIT", (now - datetime.timedelta(hours=1)).isoformat()),
            self._create_mock_transaction(30.0, "DEPOSIT", (now - datetime.timedelta(hours=2)).isoformat()),
            self._create_mock_transaction(40.0, "DEPOSIT", (now - datetime.timedelta(hours=3)).isoformat())
        ]

        context = self.detector.get_pattern_context(account_id)

        self.assertIn("small_test_pattern", context)
        self.assertEqual(context["small_test_pattern"]["recent_small_tx_count"], 3)
        self.assertEqual(context["small_test_pattern"]["recent_small_tx_sum"], 90.0)
        self.assertEqual(context["small_test_pattern"]["lookback_hours"], 24)

    def test_custom_thresholds(self):
        """Test detector with custom thresholds."""
        detector = SmallTestLargeWithdrawalDetector(
            db=self.mock_db,
            small_amount_threshold=100.0,  # Custom
            large_amount_threshold=5000.0,  # Custom
            min_small_transactions=5,  # Custom
            lookback_hours=48  # Custom
        )

        transaction = {
            "account_id": "ACC123",
            "amount": 6000.0,
            "transaction_type": "WITHDRAWAL"
        }
        context = {}

        # Mock 4 transactions (below min of 5)
        now = datetime.datetime.utcnow()
        self.mock_db.query.return_value.filter.return_value.all.return_value = [
            self._create_mock_transaction(80.0, "DEPOSIT", (now - datetime.timedelta(hours=1)).isoformat()),
            self._create_mock_transaction(90.0, "DEPOSIT", (now - datetime.timedelta(hours=2)).isoformat()),
            self._create_mock_transaction(70.0, "DEPOSIT", (now - datetime.timedelta(hours=3)).isoformat()),
            self._create_mock_transaction(85.0, "DEPOSIT", (now - datetime.timedelta(hours=4)).isoformat())
        ]

        result = detector.detect(transaction, context)

        # Should not detect because only 4 small transactions (need 5)
        self.assertFalse(result["detected"])
        self.assertEqual(result["details"]["small_transaction_count"], 4)

    def test_factory_function(self):
        """Test the factory function creates detector correctly."""
        detector = create_small_test_pattern_detector(
            self.mock_db,
            small_amount_threshold=75.0,
            large_amount_threshold=2000.0,
            min_small_transactions=4
        )

        self.assertIsInstance(detector, SmallTestLargeWithdrawalDetector)
        self.assertEqual(detector.small_amount_threshold, 75.0)
        self.assertEqual(detector.large_amount_threshold, 2000.0)
        self.assertEqual(detector.min_small_transactions, 4)

    def test_no_account_id(self):
        """Test handling of transaction without account ID."""
        transaction = {
            "amount": 1500.0,
            "transaction_type": "WITHDRAWAL"
            # Missing account_id
        }
        context = {}

        result = self.detector.detect(transaction, context)

        self.assertFalse(result["detected"])
        self.assertIn("no account id", result["details"]["reason"].lower())

    def test_time_clustering_score(self):
        """Test that more recent transactions result in higher confidence."""
        transaction = {
            "account_id": "ACC123",
            "amount": 1500.0,
            "transaction_type": "WITHDRAWAL"
        }
        context = {}

        # Mock transactions very recent (last hour)
        now = datetime.datetime.utcnow()
        recent_txs = [
            self._create_mock_transaction(20.0, "DEPOSIT", (now - datetime.timedelta(minutes=10)).isoformat()),
            self._create_mock_transaction(30.0, "DEPOSIT", (now - datetime.timedelta(minutes=20)).isoformat()),
            self._create_mock_transaction(40.0, "DEPOSIT", (now - datetime.timedelta(minutes=30)).isoformat())
        ]

        self.mock_db.query.return_value.filter.return_value.all.return_value = recent_txs
        result_recent = self.detector.detect(transaction, context)

        # Mock transactions older (20 hours ago)
        old_txs = [
            self._create_mock_transaction(20.0, "DEPOSIT", (now - datetime.timedelta(hours=20)).isoformat()),
            self._create_mock_transaction(30.0, "DEPOSIT", (now - datetime.timedelta(hours=21)).isoformat()),
            self._create_mock_transaction(40.0, "DEPOSIT", (now - datetime.timedelta(hours=22)).isoformat())
        ]

        self.mock_db.query.return_value.filter.return_value.all.return_value = old_txs
        result_old = self.detector.detect(transaction, context)

        # Recent transactions should have higher time clustering score
        recent_time_score = result_recent["details"]["confidence_breakdown"]["time_clustering_score"]
        old_time_score = result_old["details"]["confidence_breakdown"]["time_clustering_score"]

        self.assertGreater(recent_time_score, old_time_score)


if __name__ == "__main__":
    unittest.main()
