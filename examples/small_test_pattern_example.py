# examples/small_test_pattern_example.py
"""
Example usage of the Small Test - Large Withdrawal pattern detector.

This demonstrates how to detect the fraud pattern where attackers:
1. Test an account with multiple small transactions to verify it works
2. Execute a large withdrawal once they confirm the account is viable

Run this example:
    python examples/small_test_pattern_example.py
"""

from app.models.database import init_db, SessionLocal, Account, Transaction
from app.services.pattern_detectors import create_small_test_pattern_detector
from app.services.rules_engine import RulesEngine, create_small_test_large_withdrawal_rule
from app.services.context_provider import ContextProvider
import datetime
import uuid


def setup_test_scenario(db):
    """
    Create a test scenario with small test transactions followed by large withdrawal.

    Returns:
        tuple: (account_id, large_withdrawal_transaction)
    """
    # Create test account
    account_id = f"TEST_ACC_{uuid.uuid4().hex[:8]}"
    account = Account(
        account_id=account_id,
        risk_tier="medium",
        status="active"
    )
    db.add(account)

    # Create several small test transactions (fraudster testing the account)
    now = datetime.datetime.utcnow()
    small_transactions = [
        Transaction(
            transaction_id=f"TX_SMALL_{i}_{uuid.uuid4().hex[:8]}",
            account_id=account_id,
            counterparty_id="COUNTERPARTY_A",
            amount=amount,
            transaction_type="DEPOSIT",
            timestamp=(now - datetime.timedelta(hours=hours_ago)).isoformat(),
            description="Small test transaction"
        )
        for i, (amount, hours_ago) in enumerate([
            (15.00, 5),
            (25.00, 4),
            (30.00, 3),
            (20.00, 2)
        ])
    ]

    for tx in small_transactions:
        db.add(tx)

    # Create large withdrawal (fraudster moving larger sum)
    large_withdrawal = {
        "transaction_id": f"TX_LARGE_{uuid.uuid4().hex[:8]}",
        "account_id": account_id,
        "counterparty_id": "COUNTERPARTY_B",
        "amount": 2500.00,
        "transaction_type": "WIRE",
        "timestamp": now.isoformat(),
        "description": "Large withdrawal - suspicious!"
    }

    db.commit()

    return account_id, large_withdrawal


def example_basic_detection():
    """Example 1: Basic pattern detection without rules engine."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Pattern Detection")
    print("="*70)

    # Initialize database
    init_db()
    db = SessionLocal()

    try:
        # Set up test scenario
        account_id, large_withdrawal = setup_test_scenario(db)
        print(f"\n✓ Created test account: {account_id}")
        print(f"✓ Added 4 small test transactions ($15, $25, $30, $20)")
        print(f"✓ Processing large withdrawal: ${large_withdrawal['amount']:,.2f}")

        # Create pattern detector with default settings
        detector = create_small_test_pattern_detector(
            db,
            small_amount_threshold=50.0,
            large_amount_threshold=1000.0,
            min_small_transactions=3,
            lookback_hours=24
        )

        # Detect pattern
        result = detector.detect(large_withdrawal, {})

        # Display results
        print("\n" + "-"*70)
        print("DETECTION RESULTS:")
        print("-"*70)
        print(f"Pattern Detected: {result['detected']}")
        print(f"Confidence Score: {result['confidence']:.2%}")

        if result['detected']:
            details = result['details']
            print(f"\nPattern Details:")
            print(f"  • Small transactions found: {details['small_transaction_count']}")
            print(f"  • Small transaction amounts: ${details['small_transaction_amounts']}")
            print(f"  • Average small amount: ${details['avg_small_amount']:.2f}")
            print(f"  • Large withdrawal amount: ${details['large_withdrawal_amount']:.2f}")
            print(f"  • Amount ratio: {details['amount_ratio']:.1f}x")

            print(f"\nConfidence Breakdown:")
            breakdown = details['confidence_breakdown']
            print(f"  • Count score (40%): {breakdown['count_score']:.3f}")
            print(f"  • Ratio score (40%): {breakdown['ratio_score']:.3f}")
            print(f"  • Time clustering (20%): {breakdown['time_clustering_score']:.3f}")

    finally:
        db.close()


def example_rules_engine_integration():
    """Example 2: Integration with rules engine for automated detection."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Rules Engine Integration")
    print("="*70)

    # Initialize database
    init_db()
    db = SessionLocal()

    try:
        # Set up test scenario
        account_id, large_withdrawal = setup_test_scenario(db)
        print(f"\n✓ Created test account: {account_id}")
        print(f"✓ Processing transaction through rules engine...")

        # Create pattern detector
        detector = create_small_test_pattern_detector(
            db,
            small_amount_threshold=50.0,
            large_amount_threshold=1000.0,
            min_small_transactions=3
        )

        # Create rules engine and add the pattern detection rule
        rules_engine = RulesEngine()

        # Add the small test pattern rule with 60% confidence threshold
        pattern_rule = create_small_test_large_withdrawal_rule(
            detector,
            min_confidence=0.6,
            weight=2.5  # High weight due to fraud severity
        )
        rules_engine.add_rule(pattern_rule)

        # Get transaction context
        context_provider = ContextProvider(db)
        context = context_provider.get_transaction_context(large_withdrawal)

        # Evaluate all rules
        triggered_rules = rules_engine.evaluate_all(large_withdrawal, context)

        # Display results
        print("\n" + "-"*70)
        print("RULES ENGINE RESULTS:")
        print("-"*70)

        if triggered_rules:
            print(f"⚠️  ALERT: {len(triggered_rules)} rule(s) triggered!\n")
            for rule_name, rule in triggered_rules.items():
                print(f"Rule: {rule_name}")
                print(f"  Description: {rule.description}")
                print(f"  Weight: {rule.weight}")

                # Show pattern detection details if available
                if "pattern_detection" in context and "small_test_large_withdrawal" in context["pattern_detection"]:
                    pattern_result = context["pattern_detection"]["small_test_large_withdrawal"]
                    print(f"  Confidence: {pattern_result['confidence']:.2%}")
                    print(f"  Details: {pattern_result['details']['small_transaction_count']} "
                          f"small transactions totaling "
                          f"${sum(pattern_result['details']['small_transaction_amounts']):.2f}")
        else:
            print("✓ No rules triggered - transaction appears normal")

    finally:
        db.close()


def example_custom_thresholds():
    """Example 3: Using custom thresholds for different risk profiles."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Custom Thresholds for High-Risk Accounts")
    print("="*70)

    # Initialize database
    init_db()
    db = SessionLocal()

    try:
        account_id, large_withdrawal = setup_test_scenario(db)
        print(f"\n✓ Created test account: {account_id}")

        # For high-risk accounts, use stricter thresholds
        print("\nApplying stricter thresholds for high-risk account monitoring:")
        print("  • Small amount threshold: $25 (more sensitive)")
        print("  • Large amount threshold: $500 (lower threshold)")
        print("  • Min small transactions: 2 (fewer required)")
        print("  • Lookback window: 48 hours (longer window)")

        detector = create_small_test_pattern_detector(
            db,
            small_amount_threshold=25.0,     # More sensitive
            large_amount_threshold=500.0,    # Lower threshold
            min_small_transactions=2,        # Fewer required
            lookback_hours=48                # Longer window
        )

        result = detector.detect(large_withdrawal, {})

        print("\n" + "-"*70)
        print("DETECTION RESULTS WITH STRICT THRESHOLDS:")
        print("-"*70)
        print(f"Pattern Detected: {result['detected']}")
        print(f"Confidence Score: {result['confidence']:.2%}")

        if result['detected']:
            print("\n⚠️  High-risk pattern detected!")
            print(f"   Small transactions: {result['details']['small_transaction_count']}")
            print(f"   Withdrawal amount: ${result['details']['large_withdrawal_amount']:,.2f}")
        else:
            print(f"\nℹ️  Not detected: {result['details'].get('reason', 'Unknown')}")

    finally:
        db.close()


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("SMALL TEST - LARGE WITHDRAWAL PATTERN DETECTOR")
    print("Fraud Detection Examples")
    print("="*70)

    # Run examples
    example_basic_detection()
    example_rules_engine_integration()
    example_custom_thresholds()

    print("\n" + "="*70)
    print("Examples completed successfully!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
