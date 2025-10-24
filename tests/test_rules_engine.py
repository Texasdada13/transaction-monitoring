# tests/test_rules_engine.py
import pytest
from app.services.rules_engine import (
    Rule,
    RulesEngine,
    create_amount_threshold_rule,
    create_velocity_rule,
    create_new_counterparty_rule,
    create_amount_deviation_rule,
    create_low_activity_large_transfer_rule
)


class TestRule:
    """Test the Rule class."""

    def test_rule_initialization(self):
        """Test that a rule can be initialized properly."""
        rule = Rule(
            name="test_rule",
            condition_func=lambda tx, ctx: tx.get("amount", 0) > 1000,
            description="Test rule",
            weight=1.5
        )
        assert rule.name == "test_rule"
        assert rule.description == "Test rule"
        assert rule.weight == 1.5

    def test_rule_evaluate_true(self):
        """Test that a rule correctly evaluates to True."""
        rule = Rule(
            name="test_rule",
            condition_func=lambda tx, ctx: tx.get("amount", 0) > 1000,
            description="Test rule"
        )
        transaction = {"amount": 5000}
        context = {}
        assert rule.evaluate(transaction, context) is True

    def test_rule_evaluate_false(self):
        """Test that a rule correctly evaluates to False."""
        rule = Rule(
            name="test_rule",
            condition_func=lambda tx, ctx: tx.get("amount", 0) > 1000,
            description="Test rule"
        )
        transaction = {"amount": 500}
        context = {}
        assert rule.evaluate(transaction, context) is False


class TestRulesEngine:
    """Test the RulesEngine class."""

    def test_add_rule(self):
        """Test adding rules to the engine."""
        engine = RulesEngine()
        rule = Rule(
            name="test_rule",
            condition_func=lambda tx, ctx: True,
            description="Test"
        )
        engine.add_rule(rule)
        assert len(engine.rules) == 1
        assert engine.rules[0].name == "test_rule"

    def test_remove_rule(self):
        """Test removing rules from the engine."""
        engine = RulesEngine()
        rule = Rule(
            name="test_rule",
            condition_func=lambda tx, ctx: True,
            description="Test"
        )
        engine.add_rule(rule)
        assert len(engine.rules) == 1

        result = engine.remove_rule("test_rule")
        assert result is True
        assert len(engine.rules) == 0

    def test_remove_nonexistent_rule(self):
        """Test removing a rule that doesn't exist."""
        engine = RulesEngine()
        result = engine.remove_rule("nonexistent")
        assert result is False

    def test_evaluate_all_triggered(self):
        """Test evaluating all rules when some are triggered."""
        engine = RulesEngine()

        rule1 = Rule(
            name="rule1",
            condition_func=lambda tx, ctx: tx.get("amount", 0) > 1000,
            description="Amount over 1000"
        )
        rule2 = Rule(
            name="rule2",
            condition_func=lambda tx, ctx: tx.get("account_id") == "acc123",
            description="Specific account"
        )
        rule3 = Rule(
            name="rule3",
            condition_func=lambda tx, ctx: tx.get("amount", 0) > 10000,
            description="Amount over 10000"
        )

        engine.add_rule(rule1)
        engine.add_rule(rule2)
        engine.add_rule(rule3)

        transaction = {"amount": 5000, "account_id": "acc123"}
        context = {}

        triggered = engine.evaluate_all(transaction, context)
        assert len(triggered) == 2
        assert "rule1" in triggered
        assert "rule2" in triggered
        assert "rule3" not in triggered

    def test_get_rule(self):
        """Test retrieving a rule by name."""
        engine = RulesEngine()
        rule = Rule(
            name="test_rule",
            condition_func=lambda tx, ctx: True,
            description="Test"
        )
        engine.add_rule(rule)

        retrieved = engine.get_rule("test_rule")
        assert retrieved is not None
        assert retrieved.name == "test_rule"

        nonexistent = engine.get_rule("nonexistent")
        assert nonexistent is None


class TestRuleFactories:
    """Test the rule factory functions."""

    def test_create_amount_threshold_rule(self):
        """Test the amount threshold rule factory."""
        rule = create_amount_threshold_rule(threshold=10000, weight=2.0)

        # Should trigger for amounts over threshold
        tx_high = {"amount": 15000}
        assert rule.evaluate(tx_high, {}) is True

        # Should not trigger for amounts under threshold
        tx_low = {"amount": 5000}
        assert rule.evaluate(tx_low, {}) is False

        # Check weight
        assert rule.weight == 2.0

    def test_create_velocity_rule(self):
        """Test the velocity rule factory."""
        rule = create_velocity_rule(count=5, timeframe_hours=24, weight=1.5)

        # Should trigger when count exceeds threshold
        context_high = {"tx_count_last_hours": {24: 6}}
        assert rule.evaluate({}, context_high) is True

        # Should not trigger when count is below threshold
        context_low = {"tx_count_last_hours": {24: 3}}
        assert rule.evaluate({}, context_low) is False

    def test_create_new_counterparty_rule(self):
        """Test the new counterparty rule factory."""
        rule = create_new_counterparty_rule(weight=1.0)

        # Should trigger for new counterparty
        context_new = {"is_new_counterparty": True}
        assert rule.evaluate({}, context_new) is True

        # Should not trigger for existing counterparty
        context_existing = {"is_new_counterparty": False}
        assert rule.evaluate({}, context_existing) is False

    def test_create_amount_deviation_rule(self):
        """Test the amount deviation rule factory."""
        rule = create_amount_deviation_rule(std_dev_threshold=3.0, weight=1.5)

        # Should trigger for high deviation
        context_high = {"amount_deviation": 5.0}
        assert rule.evaluate({}, context_high) is True

        # Should not trigger for low deviation
        context_low = {"amount_deviation": 2.0}
        assert rule.evaluate({}, context_low) is False


class TestLowActivityLargeTransferRule:
    """Test the low activity large transfer fraud detection rule."""

    def test_rule_triggers_on_large_transfer_from_low_activity_account(self):
        """Test that the rule triggers when all conditions are met."""
        rule = create_low_activity_large_transfer_rule(
            low_activity_threshold=5,
            amount_multiplier=3.0,
            min_amount=1000.0,
            weight=2.0
        )

        # Low-activity account (3 transactions) with large transfer
        transaction = {
            "amount": 15000,  # Large amount
            "transaction_type": "WIRE"
        }
        context = {
            "total_tx_count_period": 3,  # Low activity
            "avg_transaction_amount": 1000,  # Average is $1000, current is 15x higher
        }

        assert rule.evaluate(transaction, context) is True

    def test_rule_does_not_trigger_on_active_account(self):
        """Test that the rule doesn't trigger for active accounts."""
        rule = create_low_activity_large_transfer_rule(
            low_activity_threshold=5,
            amount_multiplier=3.0,
            min_amount=1000.0
        )

        # Active account (many transactions)
        transaction = {"amount": 15000}
        context = {
            "total_tx_count_period": 50,  # High activity
            "avg_transaction_amount": 1000,
        }

        assert rule.evaluate(transaction, context) is False

    def test_rule_does_not_trigger_on_normal_amount(self):
        """Test that the rule doesn't trigger for normal-sized transactions."""
        rule = create_low_activity_large_transfer_rule(
            low_activity_threshold=5,
            amount_multiplier=3.0,
            min_amount=1000.0
        )

        # Low-activity account but normal transaction size
        transaction = {"amount": 1500}  # Only 1.5x average
        context = {
            "total_tx_count_period": 3,  # Low activity
            "avg_transaction_amount": 1000,
        }

        assert rule.evaluate(transaction, context) is False

    def test_rule_triggers_on_first_large_transaction(self):
        """Test that the rule triggers for first transaction if large enough."""
        rule = create_low_activity_large_transfer_rule(
            low_activity_threshold=5,
            amount_multiplier=3.0,
            min_amount=1000.0
        )

        # No transaction history, but large amount
        transaction = {"amount": 10000}
        context = {
            "total_tx_count_period": 0,  # No history
            "avg_transaction_amount": 0,  # No average
        }

        assert rule.evaluate(transaction, context) is True

    def test_rule_does_not_trigger_below_min_amount(self):
        """Test that the rule respects minimum amount threshold."""
        rule = create_low_activity_large_transfer_rule(
            low_activity_threshold=5,
            amount_multiplier=3.0,
            min_amount=1000.0
        )

        # Low-activity and high multiplier, but below min_amount
        transaction = {"amount": 500}  # Below $1000 minimum
        context = {
            "total_tx_count_period": 2,  # Low activity
            "avg_transaction_amount": 100,  # 5x average, but still too small
        }

        assert rule.evaluate(transaction, context) is False

    def test_rule_with_custom_parameters(self):
        """Test the rule with custom parameter values."""
        rule = create_low_activity_large_transfer_rule(
            low_activity_threshold=10,  # More lenient activity threshold
            amount_multiplier=5.0,  # Stricter multiplier
            min_amount=5000.0,  # Higher minimum
            weight=2.5
        )

        # Should trigger with these custom parameters
        transaction = {"amount": 30000}
        context = {
            "total_tx_count_period": 8,  # Still low activity
            "avg_transaction_amount": 5000,  # 6x average
        }

        assert rule.evaluate(transaction, context) is True
        assert rule.weight == 2.5

    def test_rule_description_includes_parameters(self):
        """Test that the rule description reflects the parameters."""
        rule = create_low_activity_large_transfer_rule(
            low_activity_threshold=5,
            amount_multiplier=3.0,
            min_amount=1000.0,
            timeframe_days=90
        )

        assert "1,000.00" in rule.description
        assert "3" in rule.description or "3.0" in rule.description
        assert "5" in rule.description
        assert "90" in rule.description

    def test_rule_edge_case_exactly_at_thresholds(self):
        """Test behavior when values are exactly at threshold boundaries."""
        rule = create_low_activity_large_transfer_rule(
            low_activity_threshold=5,
            amount_multiplier=3.0,
            min_amount=1000.0
        )

        # Exactly at activity threshold (5 transactions)
        transaction = {"amount": 3000}  # Exactly 3x average
        context = {
            "total_tx_count_period": 5,  # Exactly at threshold
            "avg_transaction_amount": 1000,  # Exactly 3x
        }

        # Should trigger since we use <= for activity and >= for amount
        assert rule.evaluate(transaction, context) is True

    def test_wire_and_ach_detection(self):
        """Test that the rule works for both WIRE and ACH transactions."""
        rule = create_low_activity_large_transfer_rule(
            low_activity_threshold=5,
            amount_multiplier=3.0,
            min_amount=1000.0
        )

        # Test WIRE transaction
        wire_tx = {
            "amount": 10000,
            "transaction_type": "WIRE"
        }
        context = {
            "total_tx_count_period": 3,
            "avg_transaction_amount": 1000,
        }
        assert rule.evaluate(wire_tx, context) is True

        # Test ACH transaction
        ach_tx = {
            "amount": 10000,
            "transaction_type": "ACH"
        }
        assert rule.evaluate(ach_tx, context) is True

    def test_rule_in_rules_engine(self):
        """Test integrating the rule into the RulesEngine."""
        engine = RulesEngine()
        rule = create_low_activity_large_transfer_rule()
        engine.add_rule(rule)

        # Fraudulent transaction scenario
        fraud_tx = {"amount": 25000, "transaction_type": "WIRE"}
        fraud_context = {
            "total_tx_count_period": 2,
            "avg_transaction_amount": 500,
        }

        triggered = engine.evaluate_all(fraud_tx, fraud_context)
        assert "low_activity_large_transfer" in triggered
        assert triggered["low_activity_large_transfer"].weight == 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
