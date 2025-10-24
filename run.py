#!/usr/bin/env python3
"""
Transaction Monitoring System - Main Entry Point

This is the unified entry point for the transaction monitoring system.
All fraud detection scenarios are integrated here into a single monitoring platform.

Usage:
    python run.py --mode demo          # Run demo scenarios
    python run.py --mode monitor       # Start real-time monitoring
    python run.py --mode dashboard     # Launch web dashboard
"""

import argparse
import sys
from sqlalchemy.orm import Session

from app.models.database import init_db, get_db
from app.services.rules_engine import RulesEngine
from app.services.risk_scoring import RiskScorer
from app.services.decision_engine import DecisionEngine
from app.services.context_provider import ContextProvider

# Import fraud scenario rules
from app.services.payroll_fraud_rules import initialize_payroll_fraud_rules
# TODO: Import other fraud scenarios as they're added
# from app.services.credit_fraud_rules import initialize_credit_fraud_rules
# from app.services.wire_fraud_rules import initialize_wire_fraud_rules


class TransactionMonitor:
    """
    Unified transaction monitoring system.

    Integrates all fraud detection scenarios into a single platform.
    """

    def __init__(self, db: Session):
        self.db = db
        self.rules_engine = RulesEngine()
        self.context_provider = ContextProvider(db)

        # Load ALL fraud detection rules from ALL scenarios
        self._load_all_rules()

        # Initialize scoring and decision engines
        self.risk_scorer = RiskScorer(self.rules_engine)
        self.decision_engine = DecisionEngine(self.risk_scorer)

    def _load_all_rules(self):
        """Load rules from all fraud detection scenarios."""
        print("Loading fraud detection rules...")

        # Payroll fraud rules
        payroll_rules = initialize_payroll_fraud_rules(self.db)
        for rule in payroll_rules:
            self.rules_engine.add_rule(rule)
        print(f"   Loaded {len(payroll_rules)} payroll fraud rules")

        # TODO: Add other fraud scenarios
        # credit_rules = initialize_credit_fraud_rules(self.db)
        # for rule in credit_rules:
        #     self.rules_engine.add_rule(rule)
        # print(f"   Loaded {len(credit_rules)} credit fraud rules")

        print(f"\nTotal active rules: {len(self.rules_engine.rules)}")

    def evaluate_transaction(self, transaction: dict) -> dict:
        """
        Evaluate a transaction against ALL fraud detection rules.

        Args:
            transaction: Transaction data dictionary

        Returns:
            Decision result with risk assessment
        """
        # Get transaction context
        context = self.context_provider.get_transaction_context(transaction)

        # Get scenario-specific context
        payroll_context = self.context_provider.get_payroll_context(transaction)
        context.update(payroll_context)

        # Evaluate against ALL rules from ALL scenarios
        result = self.decision_engine.evaluate(transaction, context)

        return result

    def get_statistics(self) -> dict:
        """Get monitoring statistics."""
        return {
            "total_rules": len(self.rules_engine.rules),
            "scenarios_loaded": ["payroll_fraud"],  # TODO: Add others
            "status": "active"
        }


def run_demo_mode():
    """Run demonstration scenarios."""
    print("\n" + "="*80)
    print("TRANSACTION MONITORING SYSTEM - DEMO MODE")
    print("="*80)

    # Initialize database
    init_db()
    db = next(get_db())

    try:
        # Run payroll fraud demo
        print("\n[1] Running Payroll Fraud Detection Demo...")
        from app.scenarios.payroll_reroute_scenario import main as payroll_demo
        payroll_demo()

        # TODO: Add other scenario demos
        # print("\n[2] Running Credit Card Fraud Detection Demo...")
        # from app.scenarios.credit_fraud_scenario import main as credit_demo
        # credit_demo()

    finally:
        db.close()


def run_monitor_mode():
    """Start real-time monitoring."""
    print("\n" + "="*80)
    print("TRANSACTION MONITORING SYSTEM - MONITOR MODE")
    print("="*80)

    init_db()
    db = next(get_db())

    try:
        monitor = TransactionMonitor(db)
        stats = monitor.get_statistics()

        print(f"\nMonitoring System Active")
        print(f"  Total Rules: {stats['total_rules']}")
        print(f"  Scenarios: {', '.join(stats['scenarios_loaded'])}")
        print(f"\nReady to evaluate transactions...")
        print("(In production, this would listen to a message queue)")

        # Example evaluation
        print("\n" + "-"*80)
        print("Example Transaction Evaluation:")
        print("-"*80)

        example_transaction = {
            "transaction_id": "TX_EXAMPLE_001",
            "account_id": "ACC_12345",
            "amount": 7500.0,
            "transaction_type": "direct_deposit",
            "description": "Payroll - Example Employee",
            "counterparty_id": "PAYROLL_SYSTEM"
        }

        result = monitor.evaluate_transaction(example_transaction)

        print(f"\nTransaction: {example_transaction['transaction_id']}")
        print(f"Amount: ${example_transaction['amount']:,.2f}")
        print(f"Risk Score: {result['risk_assessment']['risk_score']:.2f}")
        print(f"Decision: {result['decision'].upper()}")

        if result['risk_assessment']['triggered_rules']:
            print(f"\nTriggered Rules:")
            for rule_name, rule_info in result['risk_assessment']['triggered_rules'].items():
                print(f"  - {rule_info['description']}")

    finally:
        db.close()


def run_dashboard_mode():
    """Launch web dashboard."""
    print("\n" + "="*80)
    print("TRANSACTION MONITORING SYSTEM - DASHBOARD MODE")
    print("="*80)

    print("\nLaunching web dashboard...")
    print("TODO: Implement dashboard web interface")
    print("\nDashboard would display:")
    print("  - Real-time transaction feed")
    print("  - Risk score distribution")
    print("  - Triggered rules by scenario")
    print("  - Manual review queue")
    print("  - Statistics and metrics")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Transaction Monitoring System - Unified Fraud Detection Platform"
    )
    parser.add_argument(
        "--mode",
        choices=["demo", "monitor", "dashboard"],
        default="demo",
        help="Operating mode: demo (run scenarios), monitor (real-time), dashboard (web UI)"
    )

    args = parser.parse_args()

    if args.mode == "demo":
        run_demo_mode()
    elif args.mode == "monitor":
        run_monitor_mode()
    elif args.mode == "dashboard":
        run_dashboard_mode()


if __name__ == "__main__":
    main()
