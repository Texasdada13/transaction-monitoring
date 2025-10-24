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