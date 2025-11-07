# app/services/rules_engine.py
from typing import Dict, List, Any, Callable, Optional
import json

class Rule:
    def __init__(self, name: str, condition_func: Callable, description: str = "", weight: float = 1.0):
        """
        Initialize a rule for transaction evaluation.
        
        Args:
            name: Unique identifier for the rule
            condition_func: Function that evaluates transaction and context, returns boolean
            description: Human-readable explanation of the rule
            weight: Importance weight for risk scoring (higher = more important)
        """
        self.name = name
        self.condition_func = condition_func
        self.description = description
        self.weight = weight
    
    def evaluate(self, transaction: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Evaluate the rule against a transaction and its context.
        
        Args:
            transaction: Transaction data
            context: Additional contextual data (account history, etc.)
            
        Returns:
            True if rule is triggered, False otherwise
        """
        return self.condition_func(transaction, context)
    
    def to_dict(self):
        """Convert rule to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "weight": self.weight
        }

class RulesEngine:
    def __init__(self):
        """Initialize rules engine with empty rules list."""
        self.rules: List[Rule] = []
    
    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the engine."""
        self.rules.append(rule)
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rule by name. Returns True if successful."""
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.name != rule_name]
        return len(self.rules) < initial_count
    
    def evaluate_all(self, transaction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Rule]:
        """
        Evaluate all rules against a transaction.
        
        Returns:
            Dictionary of triggered rule names to Rule objects
        """
        triggered = {}
        for rule in self.rules:
            if rule.evaluate(transaction, context):
                triggered[rule.name] = rule
        return triggered
    
    def export_rules(self) -> List[Dict]:
        """Export all rules as dictionaries for serialization."""
        return [rule.to_dict() for rule in self.rules]
    
    def get_rule(self, rule_name: str) -> Optional[Rule]:
        """Get a rule by name."""
        for rule in self.rules:
            if rule.name == rule_name:
                return rule
        return None

# Common rule factories
def create_amount_threshold_rule(threshold: float, rule_name: str = None, weight: float = 1.0):
    """
    Create a rule that triggers when transaction amount exceeds threshold.
    
    Args:
        threshold: Amount threshold in currency units
        rule_name: Optional custom rule name
        weight: Rule importance weight
        
    Returns:
        Rule object
    """
    name = rule_name or f"amount_exceeds_{threshold}"
    return Rule(
        name=name,
        description=f"Transaction amount exceeds ${threshold:,.2f}",
        condition_func=lambda tx, ctx: tx.get("amount", 0) > threshold,
        weight=weight
    )

def create_velocity_rule(count: int, timeframe_hours: int, rule_name: str = None, weight: float = 1.0):
    """
    Create a rule that triggers when transaction velocity exceeds threshold.
    
    Args:
        count: Number of transactions
        timeframe_hours: Time window in hours
        rule_name: Optional custom rule name
        weight: Rule importance weight
        
    Returns:
        Rule object
    """
    name = rule_name or f"velocity_{count}_in_{timeframe_hours}h"
    return Rule(
        name=name,
        description=f"More than {count} transactions in {timeframe_hours} hours",
        condition_func=lambda tx, ctx: ctx.get("tx_count_last_hours", {}).get(timeframe_hours, 0) > count,
        weight=weight
    )

def create_new_counterparty_rule(rule_name: str = "new_counterparty", weight: float = 1.0):
    """
    Create a rule that triggers when counterparty is new.
    
    Args:
        rule_name: Optional custom rule name
        weight: Rule importance weight
        
    Returns:
        Rule object
    """
    return Rule(
        name=rule_name,
        description="Transaction with a new counterparty",
        condition_func=lambda tx, ctx: ctx.get("is_new_counterparty", False),
        weight=weight
    )

def create_amount_deviation_rule(std_dev_threshold: float, rule_name: str = None, weight: float = 1.0):
    """
    Create a rule that triggers when amount deviates significantly from average.

    Args:
        std_dev_threshold: Standard deviation threshold
        rule_name: Optional custom rule name
        weight: Rule importance weight

    Returns:
        Rule object
    """
    name = rule_name or f"amount_deviation_{std_dev_threshold}x"
    return Rule(
        name=name,
        description=f"Transaction amount deviates from average by {std_dev_threshold}x",
        condition_func=lambda tx, ctx: ctx.get("amount_deviation", 1.0) > std_dev_threshold,
        weight=weight
    )

def create_small_deposit_rule(threshold: float = 2.0, rule_name: str = None, weight: float = 1.5):
    """
    Create a rule that detects small test deposits used to validate accounts.

    Fraudsters often send very small amounts (pennies to a few dollars) to check
    if an account is active before initiating larger fraudulent transactions.

    Args:
        threshold: Maximum amount to consider a "small" deposit (default $2.00)
        rule_name: Optional custom rule name
        weight: Rule importance weight (default 1.5 - elevated due to fraud risk)

    Returns:
        Rule object
    """
    name = rule_name or f"small_deposit_below_{threshold}"

    def condition(tx: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
        amount = tx.get("amount", 0)
        tx_type = tx.get("transaction_type", "").upper()

        # Only flag inbound deposits (ACH, WIRE, etc.)
        # Exclude withdrawals, transfers out, or debits
        is_inbound = tx_type in ["ACH", "WIRE", "DEPOSIT", "CREDIT"]

        # Check if amount is suspiciously small
        is_small = 0 < amount <= threshold

        return is_inbound and is_small

    return Rule(
        name=name,
        description=f"Small deposit (${threshold} or less) - potential account validation test",
        condition_func=condition,
        weight=weight
    )

def create_small_deposit_velocity_rule(
    small_amount_threshold: float = 2.0,
    min_count: int = 2,
    timeframe_hours: int = 24,
    rule_name: str = None,
    weight: float = 2.0
):
    """
    Create a rule that detects multiple small deposits in a short timeframe.

    This pattern is highly indicative of account validation fraud, where fraudsters
    send multiple tiny deposits to confirm an account is active before attempting
    larger theft. Multiple small deposits in a short period is a stronger signal
    than a single small deposit.

    Args:
        small_amount_threshold: Maximum amount to consider "small" (default $2.00)
        min_count: Minimum number of small deposits to trigger (default 2)
        timeframe_hours: Time window in hours (default 24)
        rule_name: Optional custom rule name
        weight: Rule importance weight (default 2.0 - high risk pattern)

    Returns:
        Rule object
    """
    name = rule_name or f"small_deposit_velocity_{min_count}_in_{timeframe_hours}h"

    def condition(tx: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
        amount = tx.get("amount", 0)
        tx_type = tx.get("transaction_type", "").upper()

        # Check if current transaction is a small deposit
        is_inbound = tx_type in ["ACH", "WIRE", "DEPOSIT", "CREDIT"]
        is_small = 0 < amount <= small_amount_threshold

        if not (is_inbound and is_small):
            return False

        # Check context for pattern of multiple small deposits
        # Context should include small_deposit_count for the timeframe
        small_deposit_count = ctx.get("small_deposit_count", {}).get(timeframe_hours, 0)

        # Trigger if we've seen multiple small deposits including this one
        return small_deposit_count >= min_count

    return Rule(
        name=name,
        description=f"Multiple small deposits ({min_count}+ deposits ≤${small_amount_threshold}) in {timeframe_hours}h - likely account validation fraud",
        condition_func=condition,
        weight=weight
    )

def create_money_mule_rule(
    min_incoming_count: int = 5,
    max_avg_incoming: float = 500.0,
    min_flow_through_ratio: float = 0.7,
    max_transfer_hours: float = 48.0,
    time_window_hours: int = 72,
    rule_name: str = None,
    weight: float = 2.0
):
    """
    Create a rule that detects money mule behavior.

    Money mule pattern indicators:
    - Multiple small incoming payments (potential structuring)
    - High percentage of funds quickly transferred out (flow-through)
    - Quick turnaround time between receiving and sending

    Args:
        min_incoming_count: Minimum number of incoming transactions to trigger
        max_avg_incoming: Maximum average incoming amount (to detect "small" payments)
        min_flow_through_ratio: Minimum ratio of outgoing/incoming (0.7 = 70% flows through)
        max_transfer_hours: Maximum average hours to transfer funds out
        time_window_hours: Time window to analyze (default 72 hours)
        rule_name: Optional custom rule name
        weight: Rule importance weight (default 2.0 as this is a serious indicator)

    Returns:
        Rule object
    """
    name = rule_name or f"money_mule_{time_window_hours}h"

    def check_money_mule(tx: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
        """Check if transaction fits money mule pattern."""
        # Get metrics for the specified time window
        incoming_count = ctx.get(f"incoming_count_{time_window_hours}h", 0)
        avg_incoming = ctx.get(f"avg_incoming_amount_{time_window_hours}h", 0)
        flow_through_ratio = ctx.get(f"flow_through_ratio_{time_window_hours}h", 0)
        avg_hours_to_transfer = ctx.get("avg_hours_to_transfer")

        # Check all conditions
        has_many_incoming = incoming_count >= min_incoming_count
        has_small_amounts = 0 < avg_incoming <= max_avg_incoming
        has_high_flow_through = flow_through_ratio >= min_flow_through_ratio

        # Check transfer speed (if data available)
        has_quick_transfers = True
        if avg_hours_to_transfer is not None:
            has_quick_transfers = avg_hours_to_transfer <= max_transfer_hours

        # All conditions must be met
        return (has_many_incoming and
                has_small_amounts and
                has_high_flow_through and
                has_quick_transfers)

    description = (
        f"Money mule pattern detected: {min_incoming_count}+ small incoming payments "
        f"(avg ≤${max_avg_incoming}), {int(min_flow_through_ratio*100)}%+ flow-through, "
        f"transferred within {max_transfer_hours}h"
    )

    return Rule(
        name=name,
        description=description,
        condition_func=check_money_mule,
        weight=weight
    )

def create_small_test_large_withdrawal_rule(
    pattern_detector,
    min_confidence: float = 0.5,
    rule_name: str = None,
    weight: float = 2.0
):
    """
    Create a rule that detects the "small test transactions followed by large withdrawal" pattern.

    This fraud pattern occurs when attackers:
    1. Test an account with multiple small transactions to verify it works
    2. Quickly execute a large withdrawal before detection

    Args:
        pattern_detector: SmallTestLargeWithdrawalDetector instance
        min_confidence: Minimum confidence threshold (0.0-1.0) to trigger rule
        rule_name: Optional custom rule name
        weight: Rule importance weight (default 2.0 - higher due to fraud severity)

    Returns:
        Rule object

    Example:
        from app.services.pattern_detectors import create_small_test_pattern_detector

        detector = create_small_test_pattern_detector(
            db_session,
            small_amount_threshold=50.0,
            large_amount_threshold=1000.0,
            min_small_transactions=3
        )

        rule = create_small_test_large_withdrawal_rule(
            detector,
            min_confidence=0.6,
            weight=2.5
        )
    """
    name = rule_name or "small_test_large_withdrawal_pattern"

    def condition_func(tx: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
        """Evaluate if the pattern is detected with sufficient confidence."""
        # Check if pattern detection result is already in context
        if "pattern_detection" in ctx and "small_test_large_withdrawal" in ctx["pattern_detection"]:
            result = ctx["pattern_detection"]["small_test_large_withdrawal"]
        else:
            # Run pattern detection
            result = pattern_detector.detect(tx, ctx)

            # Store result in context for reuse
            if "pattern_detection" not in ctx:
                ctx["pattern_detection"] = {}
            ctx["pattern_detection"]["small_test_large_withdrawal"] = result

        # Trigger rule if pattern detected with sufficient confidence
        return result["detected"] and result["confidence"] >= min_confidence

    description = (
        f"Multiple small transactions followed by large withdrawal "
        f"(confidence >= {min_confidence:.1%})"
    )

    return Rule(
        name=name,
        description=description,
        condition_func=condition_func,
        weight=weight
    )

def create_low_activity_large_transfer_rule(
    low_activity_threshold: int = 5,
    amount_multiplier: float = 3.0,
    min_amount: float = 1000.0,
    timeframe_days: int = 90,
    rule_name: str = None,
    weight: float = 2.0
):
    """
    Create a rule that detects unusually large transfers from low-activity accounts.

    This rule triggers when:
    1. The account has been relatively inactive (few transactions in the timeframe)
    2. The current transaction amount is significantly larger than historical average
    3. The amount exceeds a minimum threshold

    Common fraud scenario: A compromised account that was dormant suddenly
    sends a large wire or ACH payment.

    Args:
        low_activity_threshold: Max number of transactions in timeframe to be considered low-activity
        amount_multiplier: Current transaction must be this many times larger than average
        min_amount: Minimum transaction amount to trigger (prevents false positives on small amounts)
        timeframe_days: Number of days to look back for activity assessment (default 90)
        rule_name: Optional custom rule name
        weight: Rule importance weight (default 2.0 - high risk)

    Returns:
        Rule object
    """
    name = rule_name or "low_activity_large_transfer"

    def condition(tx: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
        """Check if this is a large transfer from a low-activity account."""
        # Get transaction count in the specified timeframe
        total_tx_count = ctx.get("total_tx_count_period", float('inf'))

        # Check if account is low-activity
        is_low_activity = total_tx_count <= low_activity_threshold

        # Get current and average amounts
        current_amount = tx.get("amount", 0)
        avg_amount = ctx.get("avg_transaction_amount", 0)

        # Check if amount is significantly larger than average
        is_large_transfer = False
        if avg_amount > 0:
            # Compare to historical average
            is_large_transfer = current_amount >= (avg_amount * amount_multiplier)
        else:
            # No history - any transaction above min_amount is suspicious for inactive accounts
            is_large_transfer = current_amount >= min_amount

        # Check minimum amount threshold
        meets_min_amount = current_amount >= min_amount

        # Rule triggers if all conditions are met
        return is_low_activity and is_large_transfer and meets_min_amount

    description = (
        f"Large transfer (${min_amount:,.2f}+, {amount_multiplier}x avg) from "
        f"low-activity account (<={low_activity_threshold} tx in {timeframe_days} days)"
    )

    return Rule(
        name=name,
        description=description,
        condition_func=condition,
        weight=weight
    )