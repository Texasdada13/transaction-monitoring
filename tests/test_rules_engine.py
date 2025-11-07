# tests/test_rules_engine.py
import pytest
from app.services.rules_engine import (
    Rule,
    RulesEngine,
    create_amount_threshold_rule,
    create_velocity_rule,
    create_new_counterparty_rule,
    create_amount_deviation_rule,
    create_small_deposit_rule,
    create_small_deposit_velocity_rule,
    create_low_activity_large_transfer_rule
)


class TestRule:
    """Test the Rule class."""

    def test_rule_creation(self):
        """Test creating a basic rule."""
        rule = Rule(
            name="test_rule",
            condition_func=lambda tx, ctx: tx.get("amount", 0) > 100,
            description="Test rule",
            weight=1.5
        )

        assert rule.name == "test_rule"
        assert rule.description == "Test rule"
        assert rule.weight == 1.5

    def test_rule_evaluation_true(self):
        """Test rule evaluation when condition is true."""
        rule = Rule(
            name="test_rule",
            condition_func=lambda tx, ctx: tx.get("amount", 0) > 100,
            description="Test rule"
        )

        transaction = {"amount": 150}
        assert rule.evaluate(transaction, {}) is True

    def test_rule_evaluation_false(self):
        """Test rule evaluation when condition is false."""
        rule = Rule(
            name="test_rule",
            condition_func=lambda tx, ctx: tx.get("amount", 0) > 100,
            description="Test rule"
        )

        transaction = {"amount": 50}
        assert rule.evaluate(transaction, {}) is False

    def test_rule_to_dict(self):
        """Test rule serialization."""
        rule = Rule(
            name="test_rule",
            condition_func=lambda tx, ctx: True,
            description="Test description",
            weight=2.0
        )

        rule_dict = rule.to_dict()
        assert rule_dict["name"] == "test_rule"
        assert rule_dict["description"] == "Test description"
        assert rule_dict["weight"] == 2.0


class TestRulesEngine:
    """Test the RulesEngine class."""

    def test_add_rule(self):
        """Test adding a rule to the engine."""
        engine = RulesEngine()
        rule = Rule("test", lambda tx, ctx: True)

        engine.add_rule(rule)
        assert len(engine.rules) == 1
        assert engine.rules[0].name == "test"

    def test_remove_rule(self):
        """Test removing a rule from the engine."""
        engine = RulesEngine()
        rule = Rule("test", lambda tx, ctx: True)

        engine.add_rule(rule)
        assert len(engine.rules) == 1

        result = engine.remove_rule("test")
        assert result is True
        assert len(engine.rules) == 0

    def test_remove_nonexistent_rule(self):
        """Test removing a rule that doesn't exist."""
        engine = RulesEngine()
        result = engine.remove_rule("nonexistent")
        assert result is False

    def test_evaluate_all_no_triggers(self):
        """Test evaluating all rules when none trigger."""
        engine = RulesEngine()
        engine.add_rule(Rule("rule1", lambda tx, ctx: tx.get("amount", 0) > 1000))
        engine.add_rule(Rule("rule2", lambda tx, ctx: tx.get("amount", 0) < 10))

        transaction = {"amount": 500}
        triggered = engine.evaluate_all(transaction, {})

        assert len(triggered) == 0

    def test_evaluate_all_some_triggers(self):
        """Test evaluating all rules when some trigger."""
        engine = RulesEngine()
        engine.add_rule(Rule("rule1", lambda tx, ctx: tx.get("amount", 0) > 1000))
        engine.add_rule(Rule("rule2", lambda tx, ctx: tx.get("amount", 0) > 100))

        transaction = {"amount": 500}
        triggered = engine.evaluate_all(transaction, {})

        assert len(triggered) == 1
        assert "rule2" in triggered

    def test_get_rule(self):
        """Test getting a rule by name."""
        engine = RulesEngine()
        rule = Rule("test", lambda tx, ctx: True)
        engine.add_rule(rule)

        retrieved = engine.get_rule("test")
        assert retrieved is not None
        assert retrieved.name == "test"

    def test_export_rules(self):
        """Test exporting rules."""
        engine = RulesEngine()
        engine.add_rule(Rule("rule1", lambda tx, ctx: True, "Description 1", 1.0))
        engine.add_rule(Rule("rule2", lambda tx, ctx: True, "Description 2", 2.0))

        exported = engine.export_rules()
        assert len(exported) == 2
        assert exported[0]["name"] == "rule1"
        assert exported[1]["weight"] == 2.0


class TestRuleFactories:
    """Test rule factory functions."""

    def test_amount_threshold_rule_triggers(self):
        """Test amount threshold rule when it should trigger."""
        rule = create_amount_threshold_rule(threshold=1000)

        transaction = {"amount": 1500}
        assert rule.evaluate(transaction, {}) is True

    def test_amount_threshold_rule_no_trigger(self):
        """Test amount threshold rule when it should not trigger."""
        rule = create_amount_threshold_rule(threshold=1000)

        transaction = {"amount": 500}
        assert rule.evaluate(transaction, {}) is False

    def test_velocity_rule_triggers(self):
        """Test velocity rule when it should trigger."""
        rule = create_velocity_rule(count=5, timeframe_hours=24)

        transaction = {}
        context = {"tx_count_last_hours": {24: 10}}
        assert rule.evaluate(transaction, context) is True

    def test_velocity_rule_no_trigger(self):
        """Test velocity rule when it should not trigger."""
        rule = create_velocity_rule(count=5, timeframe_hours=24)

        transaction = {}
        context = {"tx_count_last_hours": {24: 3}}
        assert rule.evaluate(transaction, context) is False

    def test_new_counterparty_rule_triggers(self):
        """Test new counterparty rule when it should trigger."""
        rule = create_new_counterparty_rule()

        transaction = {}
        context = {"is_new_counterparty": True}
        assert rule.evaluate(transaction, context) is True

    def test_new_counterparty_rule_no_trigger(self):
        """Test new counterparty rule when it should not trigger."""
        rule = create_new_counterparty_rule()

        transaction = {}
        context = {"is_new_counterparty": False}
        assert rule.evaluate(transaction, context) is False

    def test_amount_deviation_rule_triggers(self):
        """Test amount deviation rule when it should trigger."""
        rule = create_amount_deviation_rule(std_dev_threshold=2.0)

        transaction = {}
        context = {"amount_deviation": 3.5}
        assert rule.evaluate(transaction, context) is True

    def test_amount_deviation_rule_no_trigger(self):
        """Test amount deviation rule when it should not trigger."""
        rule = create_amount_deviation_rule(std_dev_threshold=2.0)

        transaction = {}
        context = {"amount_deviation": 1.5}
        assert rule.evaluate(transaction, context) is False


class TestSmallDepositRule:
    """Test small deposit fraud detection rule."""

    def test_small_deposit_triggers_on_penny_deposit(self):
        """Test that rule triggers on very small deposit (pennies)."""
        rule = create_small_deposit_rule(threshold=2.0)

        transaction = {
            "amount": 0.01,
            "transaction_type": "ACH"
        }
        assert rule.evaluate(transaction, {}) is True

    def test_small_deposit_triggers_on_dollar_deposit(self):
        """Test that rule triggers on small deposit ($1-$2)."""
        rule = create_small_deposit_rule(threshold=2.0)

        transaction = {
            "amount": 1.50,
            "transaction_type": "WIRE"
        }
        assert rule.evaluate(transaction, {}) is True

    def test_small_deposit_triggers_on_threshold_amount(self):
        """Test that rule triggers on exact threshold amount."""
        rule = create_small_deposit_rule(threshold=2.0)

        transaction = {
            "amount": 2.0,
            "transaction_type": "DEPOSIT"
        }
        assert rule.evaluate(transaction, {}) is True

    def test_small_deposit_no_trigger_above_threshold(self):
        """Test that rule doesn't trigger for amounts above threshold."""
        rule = create_small_deposit_rule(threshold=2.0)

        transaction = {
            "amount": 5.0,
            "transaction_type": "ACH"
        }
        assert rule.evaluate(transaction, {}) is False

    def test_small_deposit_no_trigger_on_large_amount(self):
        """Test that rule doesn't trigger on large amounts."""
        rule = create_small_deposit_rule(threshold=2.0)

        transaction = {
            "amount": 1000.0,
            "transaction_type": "ACH"
        }
        assert rule.evaluate(transaction, {}) is False

    def test_small_deposit_no_trigger_on_zero_amount(self):
        """Test that rule doesn't trigger on zero amount."""
        rule = create_small_deposit_rule(threshold=2.0)

        transaction = {
            "amount": 0.0,
            "transaction_type": "ACH"
        }
        assert rule.evaluate(transaction, {}) is False

    def test_small_deposit_no_trigger_on_negative_amount(self):
        """Test that rule doesn't trigger on negative amount (withdrawal)."""
        rule = create_small_deposit_rule(threshold=2.0)

        transaction = {
            "amount": -1.0,
            "transaction_type": "ACH"
        }
        assert rule.evaluate(transaction, {}) is False

    def test_small_deposit_only_inbound_transactions(self):
        """Test that rule only triggers on inbound transaction types."""
        rule = create_small_deposit_rule(threshold=2.0)

        # Should trigger on inbound types
        for tx_type in ["ACH", "WIRE", "DEPOSIT", "CREDIT"]:
            transaction = {"amount": 1.0, "transaction_type": tx_type}
            assert rule.evaluate(transaction, {}) is True, f"Should trigger on {tx_type}"

    def test_small_deposit_ignores_outbound_transactions(self):
        """Test that rule ignores outbound transaction types."""
        rule = create_small_deposit_rule(threshold=2.0)

        # Should NOT trigger on outbound or unknown types
        for tx_type in ["DEBIT", "WITHDRAWAL", "PAYMENT", "TRANSFER_OUT"]:
            transaction = {"amount": 1.0, "transaction_type": tx_type}
            assert rule.evaluate(transaction, {}) is False, f"Should not trigger on {tx_type}"

    def test_small_deposit_case_insensitive_type(self):
        """Test that transaction type matching is case-insensitive."""
        rule = create_small_deposit_rule(threshold=2.0)

        for tx_type in ["ach", "ACH", "Ach", "wire", "WIRE", "Wire"]:
            transaction = {"amount": 1.0, "transaction_type": tx_type}
            assert rule.evaluate(transaction, {}) is True, f"Should trigger on {tx_type}"

    def test_small_deposit_custom_threshold(self):
        """Test rule with custom threshold."""
        rule = create_small_deposit_rule(threshold=5.0)

        transaction1 = {"amount": 3.0, "transaction_type": "ACH"}
        assert rule.evaluate(transaction1, {}) is True

        transaction2 = {"amount": 6.0, "transaction_type": "ACH"}
        assert rule.evaluate(transaction2, {}) is False

    def test_small_deposit_custom_weight(self):
        """Test rule has correct custom weight."""
        rule = create_small_deposit_rule(threshold=2.0, weight=2.5)
        assert rule.weight == 2.5

    def test_small_deposit_default_weight(self):
        """Test rule has correct default weight."""
        rule = create_small_deposit_rule(threshold=2.0)
        assert rule.weight == 1.5  # Default elevated weight

    def test_small_deposit_description(self):
        """Test rule has meaningful description."""
        rule = create_small_deposit_rule(threshold=2.0)
        assert "Small deposit" in rule.description
        assert "2" in rule.description


class TestSmallDepositVelocityRule:
    """Test small deposit velocity fraud detection rule."""

    def test_small_deposit_velocity_triggers_on_multiple_deposits(self):
        """Test that rule triggers when multiple small deposits are detected."""
        rule = create_small_deposit_velocity_rule(
            small_amount_threshold=2.0,
            min_count=2,
            timeframe_hours=24
        )

        transaction = {
            "amount": 1.0,
            "transaction_type": "ACH"
        }
        context = {
            "small_deposit_count": {24: 2}
        }
        assert rule.evaluate(transaction, context) is True

    def test_small_deposit_velocity_triggers_on_exact_threshold_count(self):
        """Test that rule triggers on exact count threshold."""
        rule = create_small_deposit_velocity_rule(
            small_amount_threshold=2.0,
            min_count=3,
            timeframe_hours=24
        )

        transaction = {
            "amount": 0.50,
            "transaction_type": "ACH"
        }
        context = {
            "small_deposit_count": {24: 3}
        }
        assert rule.evaluate(transaction, context) is True

    def test_small_deposit_velocity_no_trigger_below_count(self):
        """Test that rule doesn't trigger when count is below threshold."""
        rule = create_small_deposit_velocity_rule(
            small_amount_threshold=2.0,
            min_count=3,
            timeframe_hours=24
        )

        transaction = {
            "amount": 1.0,
            "transaction_type": "ACH"
        }
        context = {
            "small_deposit_count": {24: 1}
        }
        assert rule.evaluate(transaction, context) is False

    def test_small_deposit_velocity_no_trigger_if_current_not_small(self):
        """Test that rule doesn't trigger if current transaction is not small."""
        rule = create_small_deposit_velocity_rule(
            small_amount_threshold=2.0,
            min_count=2,
            timeframe_hours=24
        )

        # Large current transaction even with high small deposit count
        transaction = {
            "amount": 100.0,
            "transaction_type": "ACH"
        }
        context = {
            "small_deposit_count": {24: 5}
        }
        assert rule.evaluate(transaction, context) is False

    def test_small_deposit_velocity_no_trigger_if_current_not_inbound(self):
        """Test that rule doesn't trigger if current transaction is outbound."""
        rule = create_small_deposit_velocity_rule(
            small_amount_threshold=2.0,
            min_count=2,
            timeframe_hours=24
        )

        # Outbound transaction even with small amount and high count
        transaction = {
            "amount": 1.0,
            "transaction_type": "DEBIT"
        }
        context = {
            "small_deposit_count": {24: 5}
        }
        assert rule.evaluate(transaction, context) is False

    def test_small_deposit_velocity_different_timeframes(self):
        """Test rule with different timeframe windows."""
        # 1 hour window
        rule_1h = create_small_deposit_velocity_rule(
            small_amount_threshold=2.0,
            min_count=2,
            timeframe_hours=1
        )

        transaction = {"amount": 1.0, "transaction_type": "ACH"}
        context = {"small_deposit_count": {1: 3, 24: 3}}
        assert rule_1h.evaluate(transaction, context) is True

        # 24 hour window
        rule_24h = create_small_deposit_velocity_rule(
            small_amount_threshold=2.0,
            min_count=2,
            timeframe_hours=24
        )

        transaction = {"amount": 1.0, "transaction_type": "ACH"}
        context = {"small_deposit_count": {1: 0, 24: 3}}
        assert rule_24h.evaluate(transaction, context) is True

    def test_small_deposit_velocity_high_count_scenario(self):
        """Test rule with many small deposits (strong fraud signal)."""
        rule = create_small_deposit_velocity_rule(
            small_amount_threshold=2.0,
            min_count=2,
            timeframe_hours=24
        )

        transaction = {
            "amount": 0.01,
            "transaction_type": "ACH"
        }
        context = {
            "small_deposit_count": {24: 10}  # 10 small deposits
        }
        assert rule.evaluate(transaction, context) is True

    def test_small_deposit_velocity_custom_amount_threshold(self):
        """Test rule with custom amount threshold."""
        rule = create_small_deposit_velocity_rule(
            small_amount_threshold=5.0,
            min_count=2,
            timeframe_hours=24
        )

        # Amount under custom threshold
        transaction = {"amount": 4.0, "transaction_type": "ACH"}
        context = {"small_deposit_count": {24: 2}}
        assert rule.evaluate(transaction, context) is True

        # Amount over custom threshold
        transaction = {"amount": 6.0, "transaction_type": "ACH"}
        context = {"small_deposit_count": {24: 2}}
        assert rule.evaluate(transaction, context) is False

    def test_small_deposit_velocity_custom_weight(self):
        """Test rule has correct custom weight."""
        rule = create_small_deposit_velocity_rule(
            small_amount_threshold=2.0,
            min_count=2,
            timeframe_hours=24,
            weight=3.0
        )
        assert rule.weight == 3.0

    def test_small_deposit_velocity_default_weight(self):
        """Test rule has correct default weight (higher than single deposit)."""
        rule = create_small_deposit_velocity_rule(
            small_amount_threshold=2.0,
            min_count=2,
            timeframe_hours=24
        )
        assert rule.weight == 2.0  # Higher risk than single deposit

    def test_small_deposit_velocity_description(self):
        """Test rule has meaningful description."""
        rule = create_small_deposit_velocity_rule(
            small_amount_threshold=2.0,
            min_count=2,
            timeframe_hours=24
        )
        assert "Multiple small deposits" in rule.description
        assert "24" in rule.description
        assert "2" in rule.description

    def test_small_deposit_velocity_missing_context(self):
        """Test rule handles missing context gracefully."""
        rule = create_small_deposit_velocity_rule(
            small_amount_threshold=2.0,
            min_count=2,
            timeframe_hours=24
        )

        transaction = {
            "amount": 1.0,
            "transaction_type": "ACH"
        }
        # Empty context
        context = {}
        assert rule.evaluate(transaction, context) is False

    def test_small_deposit_velocity_realistic_fraud_scenario(self):
        """Test realistic fraud scenario: multiple penny tests."""
        rule = create_small_deposit_velocity_rule(
            small_amount_threshold=2.0,
            min_count=3,
            timeframe_hours=6
        )

        # Fraudster sends multiple $0.01 test deposits in 6 hours
        transaction = {
            "amount": 0.01,
            "transaction_type": "ACH",
            "counterparty_id": "unknown_fraudster"
        }
        context = {
            "small_deposit_count": {6: 4}  # 4 penny deposits in 6 hours
        }
        assert rule.evaluate(transaction, context) is True


class TestIntegrationSmallDepositRules:
    """Integration tests for small deposit rules with rules engine."""

    def test_single_small_deposit_rule_in_engine(self):
        """Test single small deposit rule integrated in rules engine."""
        engine = RulesEngine()
        engine.add_rule(create_small_deposit_rule(threshold=2.0))

        transaction = {
            "amount": 0.50,
            "transaction_type": "ACH"
        }
        triggered = engine.evaluate_all(transaction, {})

        assert len(triggered) == 1
        assert "small_deposit_below_2.0" in triggered

    def test_velocity_rule_in_engine(self):
        """Test velocity rule integrated in rules engine."""
        engine = RulesEngine()
        engine.add_rule(create_small_deposit_velocity_rule(
            small_amount_threshold=2.0,
            min_count=2,
            timeframe_hours=24
        ))

        transaction = {
            "amount": 1.0,
            "transaction_type": "ACH"
        }
        context = {
            "small_deposit_count": {24: 3}
        }
        triggered = engine.evaluate_all(transaction, context)

        assert len(triggered) == 1
        assert "small_deposit_velocity_2_in_24h" in triggered

    def test_both_small_deposit_rules_trigger(self):
        """Test both small deposit rules can trigger together."""
        engine = RulesEngine()
        engine.add_rule(create_small_deposit_rule(threshold=2.0))
        engine.add_rule(create_small_deposit_velocity_rule(
            small_amount_threshold=2.0,
            min_count=2,
            timeframe_hours=24
        ))

        transaction = {
            "amount": 0.75,
            "transaction_type": "ACH"
        }
        context = {
            "small_deposit_count": {24: 3}
        }
        triggered = engine.evaluate_all(transaction, context)

        # Both rules should trigger
        assert len(triggered) == 2
        assert "small_deposit_below_2.0" in triggered
        assert "small_deposit_velocity_2_in_24h" in triggered

    def test_combined_weight_high_risk(self):
        """Test combined weight of both rules signals high risk."""
        engine = RulesEngine()
        engine.add_rule(create_small_deposit_rule(threshold=2.0))
        engine.add_rule(create_small_deposit_velocity_rule(
            small_amount_threshold=2.0,
            min_count=2,
            timeframe_hours=24
        ))

        transaction = {
            "amount": 0.01,
            "transaction_type": "ACH"
        }
        context = {
            "small_deposit_count": {24: 5}
        }
        triggered = engine.evaluate_all(transaction, context)

        # Calculate total weight
        total_weight = sum(rule.weight for rule in triggered.values())
        assert total_weight >= 3.0  # 1.5 + 2.0 = high risk

    def test_no_false_positive_on_normal_deposit(self):
        """Test no false positive on normal deposit amounts."""
        engine = RulesEngine()
        engine.add_rule(create_small_deposit_rule(threshold=2.0))
        engine.add_rule(create_small_deposit_velocity_rule(
            small_amount_threshold=2.0,
            min_count=2,
            timeframe_hours=24
        ))

        transaction = {
            "amount": 50.0,  # Normal amount
            "transaction_type": "ACH"
        }
        context = {
            "small_deposit_count": {24: 0}
        }
        triggered = engine.evaluate_all(transaction, context)

        assert len(triggered) == 0
=======
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
>>>>>>> origin/claude/fraud-detection-experiment-011CUSRVUv9aWSBTU1sSRa7c
