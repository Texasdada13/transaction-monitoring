#!/usr/bin/env python3
"""
Demonstration of Low-Activity Large Transfer Fraud Detection

This script demonstrates how the fraud detection rule identifies
unusually large transfers from low-activity accounts, which is a
common indicator of account compromise.

Use case: A customer suddenly sends a much larger wire or ACH payment
than they normally do, which can indicate fraud.
"""

from app.services.rules_engine import (
    RulesEngine,
    create_low_activity_large_transfer_rule,
    create_amount_threshold_rule,
    create_velocity_rule
)


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_transaction(tx, context):
    """Print transaction details."""
    print("\nTransaction Details:")
    print(f"  Amount: ${tx.get('amount', 0):,.2f}")
    print(f"  Type: {tx.get('transaction_type', 'N/A')}")
    print(f"  Account ID: {tx.get('account_id', 'N/A')}")
    print(f"  Counterparty: {tx.get('counterparty_id', 'N/A')}")

    print("\nAccount Activity Context:")
    print(f"  Total transactions (90 days): {context.get('total_tx_count_period', 0)}")
    print(f"  Average transaction amount: ${context.get('avg_transaction_amount', 0):,.2f}")
    print(f"  Account age (days): {context.get('account_age_days', 'N/A')}")


def print_evaluation_result(triggered_rules):
    """Print rule evaluation results."""
    print("\n--- FRAUD DETECTION RESULT ---")

    if triggered_rules:
        print(f"  STATUS: FLAGGED - {len(triggered_rules)} rule(s) triggered")
        print("  Action: MANUAL REVIEW REQUIRED\n")

        for rule_name, rule in triggered_rules.items():
            print(f"  Rule: {rule.name}")
            print(f"    Description: {rule.description}")
            print(f"    Risk Weight: {rule.weight}")
    else:
        print("  STATUS: OK - No fraud indicators detected")
        print("  Action: Auto-approve")

    print()


def demo_fraudulent_scenario():
    """Demonstrate detection of a fraudulent transaction."""
    print_header("SCENARIO 1: Fraudulent Large Transfer (SHOULD DETECT)")

    print("\nScenario Description:")
    print("  A customer who typically makes small transactions (~$200-$500)")
    print("  and has only made 2 transactions in the past 90 days")
    print("  suddenly attempts to wire $25,000 to a new recipient.")
    print("  This is a classic account takeover pattern.")

    # Create the fraud detection rule
    engine = RulesEngine()
    fraud_rule = create_low_activity_large_transfer_rule(
        low_activity_threshold=5,      # <= 5 transactions = low activity
        amount_multiplier=3.0,          # 3x average amount
        min_amount=1000.0,              # Minimum $1,000 to flag
        weight=2.0                      # High risk weight
    )
    engine.add_rule(fraud_rule)

    # Simulate a fraudulent transaction
    transaction = {
        "transaction_id": "TX12345",
        "account_id": "ACC-7890",
        "counterparty_id": "COUNTERPARTY-NEW-999",
        "amount": 25000.00,
        "transaction_type": "WIRE",
        "description": "Wire transfer"
    }

    # Context from historical data
    context = {
        "total_tx_count_period": 2,         # Only 2 transactions in 90 days
        "avg_transaction_amount": 350.00,   # Average is $350
        "account_age_days": 45,
        "is_new_counterparty": True
    }

    # Print details
    print_transaction(transaction, context)

    # Evaluate
    triggered = engine.evaluate_all(transaction, context)
    print_evaluation_result(triggered)

    # Calculate risk score
    total_weight = sum(rule.weight for rule in triggered.values())
    print(f"  Total Risk Score: {total_weight}")
    print(f"  Risk Level: HIGH - Account likely compromised")


def demo_legitimate_scenario():
    """Demonstrate a legitimate transaction that should pass."""
    print_header("SCENARIO 2: Legitimate Transaction (SHOULD PASS)")

    print("\nScenario Description:")
    print("  A customer with regular activity (15 transactions in 90 days)")
    print("  and consistent transaction amounts makes a normal")
    print("  $2,500 payment, slightly above their average.")

    # Create the fraud detection rule
    engine = RulesEngine()
    fraud_rule = create_low_activity_large_transfer_rule(
        low_activity_threshold=5,
        amount_multiplier=3.0,
        min_amount=1000.0,
        weight=2.0
    )
    engine.add_rule(fraud_rule)

    # Simulate a legitimate transaction
    transaction = {
        "transaction_id": "TX67890",
        "account_id": "ACC-4321",
        "counterparty_id": "COUNTERPARTY-REG-123",
        "amount": 2500.00,
        "transaction_type": "ACH",
        "description": "Regular payment"
    }

    # Context from historical data
    context = {
        "total_tx_count_period": 15,        # Regular activity
        "avg_transaction_amount": 2000.00,  # Average is $2000
        "account_age_days": 730,
        "is_new_counterparty": False
    }

    # Print details
    print_transaction(transaction, context)

    # Evaluate
    triggered = engine.evaluate_all(transaction, context)
    print_evaluation_result(triggered)


def demo_first_large_transaction():
    """Demonstrate detection of first large transaction from inactive account."""
    print_header("SCENARIO 3: First Large Transaction (SHOULD DETECT)")

    print("\nScenario Description:")
    print("  A dormant account with NO transaction history")
    print("  suddenly attempts to send $15,000 via wire transfer.")
    print("  This is highly suspicious and could indicate")
    print("  account takeover or money mule activity.")

    # Create the fraud detection rule
    engine = RulesEngine()
    fraud_rule = create_low_activity_large_transfer_rule(
        low_activity_threshold=5,
        amount_multiplier=3.0,
        min_amount=1000.0,
        weight=2.0
    )
    engine.add_rule(fraud_rule)

    # Simulate first large transaction
    transaction = {
        "transaction_id": "TX99999",
        "account_id": "ACC-0001",
        "counterparty_id": "COUNTERPARTY-UNKNOWN",
        "amount": 15000.00,
        "transaction_type": "WIRE",
        "description": "Wire transfer"
    }

    # Context - no historical data
    context = {
        "total_tx_count_period": 0,         # No history
        "avg_transaction_amount": 0,        # No average
        "account_age_days": 5,
        "is_new_counterparty": True
    }

    # Print details
    print_transaction(transaction, context)

    # Evaluate
    triggered = engine.evaluate_all(transaction, context)
    print_evaluation_result(triggered)


def demo_edge_case():
    """Demonstrate edge case at threshold boundaries."""
    print_header("SCENARIO 4: Edge Case at Threshold (SHOULD DETECT)")

    print("\nScenario Description:")
    print("  An account with exactly 5 transactions (at the threshold)")
    print("  attempts a transaction exactly 3x their average amount.")
    print("  This should still trigger the rule.")

    # Create the fraud detection rule
    engine = RulesEngine()
    fraud_rule = create_low_activity_large_transfer_rule(
        low_activity_threshold=5,
        amount_multiplier=3.0,
        min_amount=1000.0,
        weight=2.0
    )
    engine.add_rule(fraud_rule)

    # Edge case transaction
    transaction = {
        "transaction_id": "TX-EDGE",
        "account_id": "ACC-5555",
        "counterparty_id": "COUNTERPARTY-456",
        "amount": 3000.00,
        "transaction_type": "ACH",
        "description": "ACH payment"
    }

    # Context at exact thresholds
    context = {
        "total_tx_count_period": 5,         # Exactly at threshold
        "avg_transaction_amount": 1000.00,  # Exactly 3x
        "account_age_days": 90,
        "is_new_counterparty": False
    }

    # Print details
    print_transaction(transaction, context)

    # Evaluate
    triggered = engine.evaluate_all(transaction, context)
    print_evaluation_result(triggered)


def demo_multiple_rules():
    """Demonstrate combining multiple fraud detection rules."""
    print_header("SCENARIO 5: Multiple Rules Combined")

    print("\nScenario Description:")
    print("  Demonstrating how multiple fraud detection rules work together")
    print("  to provide comprehensive protection. This transaction triggers")
    print("  multiple indicators of fraud.")

    # Create multiple rules
    engine = RulesEngine()

    # Rule 1: Low activity large transfer
    fraud_rule = create_low_activity_large_transfer_rule(
        low_activity_threshold=5,
        amount_multiplier=3.0,
        min_amount=1000.0,
        weight=2.0
    )
    engine.add_rule(fraud_rule)

    # Rule 2: Large amount threshold
    large_amount_rule = create_amount_threshold_rule(
        threshold=10000.0,
        weight=1.5
    )
    engine.add_rule(large_amount_rule)

    # Rule 3: High velocity
    velocity_rule = create_velocity_rule(
        count=3,
        timeframe_hours=24,
        weight=1.0
    )
    engine.add_rule(velocity_rule)

    # Highly suspicious transaction
    transaction = {
        "transaction_id": "TX-MULTI",
        "account_id": "ACC-9999",
        "counterparty_id": "COUNTERPARTY-SUSPICIOUS",
        "amount": 50000.00,
        "transaction_type": "WIRE",
        "description": "Large wire transfer"
    }

    # Context showing multiple red flags
    context = {
        "total_tx_count_period": 1,         # Very low activity
        "avg_transaction_amount": 500.00,   # Much larger than average
        "tx_count_last_hours": {
            1: 0,
            6: 1,
            24: 4,                          # High velocity
            168: 4
        },
        "account_age_days": 10,
        "is_new_counterparty": True
    }

    # Print details
    print_transaction(transaction, context)

    # Evaluate
    triggered = engine.evaluate_all(transaction, context)
    print_evaluation_result(triggered)

    # Calculate total risk
    total_weight = sum(rule.weight for rule in triggered.values())
    print(f"  Total Risk Score: {total_weight}")
    print(f"  Risk Level: CRITICAL - Multiple fraud indicators")


def main():
    """Run all demonstration scenarios."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  LOW-ACTIVITY LARGE TRANSFER FRAUD DETECTION DEMO".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("║" + "  Detecting unusually large transfers from dormant accounts".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")

    # Run all scenarios
    demo_fraudulent_scenario()
    demo_legitimate_scenario()
    demo_first_large_transaction()
    demo_edge_case()
    demo_multiple_rules()

    # Summary
    print_header("SUMMARY")
    print("\nKey Features of the Low-Activity Large Transfer Rule:")
    print("  ✓ Detects large transfers from accounts with minimal activity")
    print("  ✓ Compares transaction size against historical averages")
    print("  ✓ Configurable thresholds for activity and amount")
    print("  ✓ Handles edge cases like first transactions")
    print("  ✓ Integrates with other fraud detection rules")
    print("\nCommon Fraud Scenarios Detected:")
    print("  • Account takeover (compromised credentials)")
    print("  • Money mule accounts")
    print("  • Dormant account abuse")
    print("  • Wire fraud attempts")
    print("  • Business email compromise (BEC)")
    print("\nFor school projects and experiments, this rule demonstrates:")
    print("  • Statistical analysis of transaction patterns")
    print("  • Threshold-based anomaly detection")
    print("  • Context-aware fraud detection")
    print("  • Configurable rule systems")
    print("  • Real-world fraud prevention techniques")
    print("\n")


if __name__ == "__main__":
    main()
