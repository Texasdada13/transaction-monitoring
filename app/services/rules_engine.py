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