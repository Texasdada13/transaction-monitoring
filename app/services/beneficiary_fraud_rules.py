# app/services/beneficiary_fraud_rules.py
"""
Fraud detection rules for rapid beneficiary addition patterns.

Detects scenarios where an administrator (potentially compromised) rapidly adds
many new beneficiaries followed by payments - often a sign of scripted fraud.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.database import Beneficiary, Transaction
from app.services.rules_engine import Rule
from config.settings import (
    BENEFICIARY_RAPID_ADDITION_THRESHOLD,
    BENEFICIARY_RAPID_ADDITION_WINDOW_HOURS,
    BENEFICIARY_BULK_ADDITION_THRESHOLD,
    BENEFICIARY_BULK_ADDITION_WINDOW_HOURS,
    BENEFICIARY_RECENT_ADDITION_HOURS,
    BENEFICIARY_NEW_BENEFICIARY_PAYMENT_RATIO
)


def create_rapid_beneficiary_addition_rule(
    db: Session,
    threshold: int = BENEFICIARY_RAPID_ADDITION_THRESHOLD,
    window_hours: int = BENEFICIARY_RAPID_ADDITION_WINDOW_HOURS,
    weight: float = 2.5
) -> Rule:
    """
    Detect when many beneficiaries are added rapidly to an account.

    This pattern suggests:
    - Compromised administrator account
    - Scripted/automated fraud onboarding
    - Preparation for fraudulent payments

    Args:
        db: Database session
        threshold: Minimum number of beneficiaries to trigger alert
        window_hours: Time window to check for rapid additions
        weight: Rule weight for risk scoring

    Returns:
        Rule object for rapid beneficiary addition detection
    """
    def condition(transaction: Dict[str, Any], context: Dict[str, Any]) -> bool:
        # Check context for rapid beneficiary additions
        recent_beneficiaries_count = context.get(f"beneficiaries_added_{window_hours}h", 0)

        if recent_beneficiaries_count >= threshold:
            # Add detailed information to context
            context["rapid_beneficiary_addition_detected"] = True
            context["rapid_beneficiary_count"] = recent_beneficiaries_count
            context["rapid_beneficiary_window_hours"] = window_hours
            return True

        return False

    return Rule(
        name=f"rapid_beneficiary_addition_{window_hours}h",
        description=f"{threshold}+ beneficiaries added within {window_hours} hours",
        condition_func=condition,
        weight=weight
    )


def create_bulk_beneficiary_addition_rule(
    db: Session,
    threshold: int = BENEFICIARY_BULK_ADDITION_THRESHOLD,
    window_hours: int = BENEFICIARY_BULK_ADDITION_WINDOW_HOURS,
    weight: float = 3.0
) -> Rule:
    """
    Detect bulk/scripted beneficiary additions (higher threshold, longer window).

    This pattern indicates large-scale scripted fraud preparation.

    Args:
        db: Database session
        threshold: Minimum number of beneficiaries for bulk detection
        window_hours: Time window to check for bulk additions
        weight: Rule weight for risk scoring

    Returns:
        Rule object for bulk beneficiary addition detection
    """
    def condition(transaction: Dict[str, Any], context: Dict[str, Any]) -> bool:
        # Check context for bulk beneficiary additions
        recent_beneficiaries_count = context.get(f"beneficiaries_added_{window_hours}h", 0)

        if recent_beneficiaries_count >= threshold:
            context["bulk_beneficiary_addition_detected"] = True
            context["bulk_beneficiary_count"] = recent_beneficiaries_count
            context["bulk_beneficiary_window_hours"] = window_hours
            return True

        return False

    return Rule(
        name=f"bulk_beneficiary_addition_{window_hours}h",
        description=f"{threshold}+ beneficiaries added (bulk/scripted) within {window_hours} hours",
        condition_func=condition,
        weight=weight
    )


def create_payment_to_new_beneficiary_rule(
    db: Session,
    recent_hours: int = BENEFICIARY_RECENT_ADDITION_HOURS,
    weight: float = 2.0
) -> Rule:
    """
    Detect payments to recently added beneficiaries.

    When combined with rapid addition patterns, this confirms the fraud scenario.

    Args:
        db: Database session
        recent_hours: Hours to consider beneficiary as "newly added"
        weight: Rule weight for risk scoring

    Returns:
        Rule object for detecting payments to new beneficiaries
    """
    def condition(transaction: Dict[str, Any], context: Dict[str, Any]) -> bool:
        # Only check outgoing transactions (payments)
        if transaction.get("direction") != "debit":
            return False

        # Check if paying to a recently added beneficiary
        is_new_beneficiary = context.get("is_new_beneficiary", False)
        beneficiary_age_hours = context.get("beneficiary_age_hours")

        if is_new_beneficiary and beneficiary_age_hours is not None and beneficiary_age_hours <= recent_hours:
            context["payment_to_new_beneficiary_detected"] = True
            context["beneficiary_age_hours"] = beneficiary_age_hours
            return True

        return False

    return Rule(
        name=f"payment_to_new_beneficiary_{recent_hours}h",
        description=f"Payment to beneficiary added within {recent_hours} hours",
        condition_func=condition,
        weight=weight
    )


def create_high_new_beneficiary_payment_ratio_rule(
    db: Session,
    min_ratio: float = BENEFICIARY_NEW_BENEFICIARY_PAYMENT_RATIO,
    window_hours: int = 24,
    weight: float = 2.5
) -> Rule:
    """
    Detect when most recent payments go to newly added beneficiaries.

    High ratio of payments to new beneficiaries suggests coordinated fraud.

    Args:
        db: Database session
        min_ratio: Minimum ratio of payments to new beneficiaries (0.0-1.0)
        window_hours: Time window to analyze payment patterns
        weight: Rule weight for risk scoring

    Returns:
        Rule object for detecting high new beneficiary payment ratio
    """
    def condition(transaction: Dict[str, Any], context: Dict[str, Any]) -> bool:
        # Only check outgoing transactions
        if transaction.get("direction") != "debit":
            return False

        # Check the ratio of payments to new beneficiaries
        new_beneficiary_payment_ratio = context.get(f"new_beneficiary_payment_ratio_{window_hours}h", 0.0)
        new_beneficiary_payment_count = context.get(f"new_beneficiary_payment_count_{window_hours}h", 0)

        if new_beneficiary_payment_ratio >= min_ratio and new_beneficiary_payment_count >= 3:
            context["high_new_beneficiary_ratio_detected"] = True
            context["new_beneficiary_payment_ratio"] = new_beneficiary_payment_ratio
            context["new_beneficiary_payment_count"] = new_beneficiary_payment_count
            return True

        return False

    return Rule(
        name=f"high_new_beneficiary_payment_ratio_{window_hours}h",
        description=f"{int(min_ratio*100)}%+ of payments to newly added beneficiaries",
        condition_func=condition,
        weight=weight
    )


def create_same_source_bulk_addition_rule(
    db: Session,
    min_count: int = 5,
    window_hours: int = 24,
    weight: float = 3.5
) -> Rule:
    """
    Detect multiple beneficiaries added from the same source/IP in short time.

    Strong indicator of scripted/automated fraud when many beneficiaries
    are added from the same IP address or user.

    Args:
        db: Database session
        min_count: Minimum number of beneficiaries from same source
        window_hours: Time window to check
        weight: Rule weight for risk scoring

    Returns:
        Rule object for detecting same-source bulk additions
    """
    def condition(transaction: Dict[str, Any], context: Dict[str, Any]) -> bool:
        # Check for beneficiaries added from same IP
        same_ip_count = context.get(f"beneficiaries_same_ip_{window_hours}h", 0)
        same_user_count = context.get(f"beneficiaries_same_user_{window_hours}h", 0)
        same_source_ip = context.get("same_source_ip")
        same_source_user = context.get("same_source_user")

        if same_ip_count >= min_count or same_user_count >= min_count:
            context["same_source_bulk_addition_detected"] = True
            context["same_source_beneficiary_count"] = max(same_ip_count, same_user_count)
            if same_ip_count >= min_count:
                context["same_source_type"] = "ip_address"
                context["same_source_value"] = same_source_ip
            else:
                context["same_source_type"] = "user"
                context["same_source_value"] = same_source_user
            return True

        return False

    return Rule(
        name=f"same_source_bulk_addition_{window_hours}h",
        description=f"{min_count}+ beneficiaries from same IP/user within {window_hours} hours",
        condition_func=condition,
        weight=weight
    )


def create_unverified_beneficiary_payment_rule(
    db: Session,
    weight: float = 1.5
) -> Rule:
    """
    Detect payments to unverified beneficiaries.

    Legitimate systems typically require beneficiary verification before payments.
    Skipping verification suggests fraudulent intent.

    Args:
        db: Database session
        weight: Rule weight for risk scoring

    Returns:
        Rule object for detecting payments to unverified beneficiaries
    """
    def condition(transaction: Dict[str, Any], context: Dict[str, Any]) -> bool:
        # Only check outgoing transactions
        if transaction.get("direction") != "debit":
            return False

        # Check if beneficiary is unverified
        is_beneficiary_verified = context.get("is_beneficiary_verified", True)

        if not is_beneficiary_verified:
            context["unverified_beneficiary_payment_detected"] = True
            return True

        return False

    return Rule(
        name="payment_to_unverified_beneficiary",
        description="Payment to unverified beneficiary",
        condition_func=condition,
        weight=weight
    )


def initialize_beneficiary_fraud_rules(db: Session) -> List[Rule]:
    """
    Initialize all beneficiary fraud detection rules.

    Creates a comprehensive ruleset for detecting rapid beneficiary addition
    followed by payments - a common pattern in compromised account fraud.

    Args:
        db: Database session

    Returns:
        List of initialized beneficiary fraud rules
    """
    return [
        # Rapid addition detection
        create_rapid_beneficiary_addition_rule(db),
        create_bulk_beneficiary_addition_rule(db),

        # Payment pattern detection
        create_payment_to_new_beneficiary_rule(db),
        create_high_new_beneficiary_payment_ratio_rule(db),

        # Source analysis
        create_same_source_bulk_addition_rule(db),

        # Verification checks
        create_unverified_beneficiary_payment_rule(db),
    ]
