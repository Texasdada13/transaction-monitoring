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