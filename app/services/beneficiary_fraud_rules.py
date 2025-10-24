# app/services/beneficiary_fraud_rules.py
"""
Beneficiary/Vendor fraud detection rules for identifying suspicious payments to modified accounts.

This module implements detection rules for the following scenario:
A supplier's bank details are changed (often via vendor impersonation/BEC attack) and a
payment is sent to the new account immediately - typically the same day.

Attack Pattern:
1. Attacker impersonates a vendor via email/phone
2. Requests bank account change for "updated banking information"
3. Payment is processed to the fraudulent account shortly after
4. Real vendor never receives payment

This is one of the most common Business Email Compromise (BEC) attack patterns.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.services.rules_engine import Rule
from app.models.database import Beneficiary, BeneficiaryChangeHistory
from config.settings import (
    BENEFICIARY_SAME_DAY_PAYMENT_HOURS,
    BENEFICIARY_CRITICAL_CHANGE_WINDOW_DAYS,
    BENEFICIARY_SUSPICIOUS_CHANGE_WINDOW_DAYS,
    BENEFICIARY_RAPID_CHANGE_THRESHOLD,
    BENEFICIARY_RAPID_CHANGE_WINDOW_DAYS,
    BENEFICIARY_HIGH_VALUE_THRESHOLD,
    BENEFICIARY_NEW_VENDOR_DAYS
)
import json


def is_beneficiary_payment(transaction: Dict[str, Any]) -> bool:
    """Check if transaction is a payment to a beneficiary/vendor."""
    tx_type = transaction.get("transaction_type", "").lower()
    description = transaction.get("description", "").lower()
    direction = transaction.get("direction", "").lower()

    # Must be an outgoing payment
    if direction != "debit":
        return False

    return (
        tx_type in ["ach_debit", "wire_transfer", "payment", "vendor_payment", "supplier_payment"] or
        any(keyword in description for keyword in ["payment", "invoice", "vendor", "supplier", "contractor"])
    )


def get_beneficiary_from_transaction(db: Session, transaction: Dict[str, Any]) -> Beneficiary:
    """Get beneficiary record from transaction data."""
    # Try to get beneficiary from tx_metadata first
    tx_metadata = transaction.get("tx_metadata") or transaction.get("metadata")
    if tx_metadata:
        if isinstance(tx_metadata, str):
            try:
                tx_metadata = json.loads(tx_metadata)
            except:
                tx_metadata = {}

        beneficiary_id = tx_metadata.get("beneficiary_id")
        if beneficiary_id:
            return db.query(Beneficiary).filter(Beneficiary.beneficiary_id == beneficiary_id).first()

    # Fallback: try to match by counterparty_id
    counterparty_id = transaction.get("counterparty_id")
    if counterparty_id:
        return db.query(Beneficiary).filter(Beneficiary.beneficiary_id == counterparty_id).first()

    return None


def create_same_day_payment_after_change_rule(db: Session, weight: float = 5.0) -> Rule:
    """
    Detect payments made on the same day as beneficiary account change.

    This is a CRITICAL risk indicator - the most common pattern in vendor impersonation fraud.
    Attackers often request changes and immediate payment to minimize detection window.
    """
    def condition(transaction: Dict[str, Any], context: Dict[str, Any]) -> bool:
        if not is_beneficiary_payment(transaction):
            return False

        beneficiary = get_beneficiary_from_transaction(db, transaction)
        if not beneficiary:
            return False

        # Check for changes within the same day (24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=BENEFICIARY_SAME_DAY_PAYMENT_HOURS)
        cutoff_iso = cutoff_time.isoformat()

        same_day_changes = db.query(BeneficiaryChangeHistory).filter(
            BeneficiaryChangeHistory.beneficiary_id == beneficiary.beneficiary_id,
            BeneficiaryChangeHistory.change_type.in_(["account_number", "routing_number", "bank_name"]),
            BeneficiaryChangeHistory.timestamp > cutoff_iso
        ).all()

        if same_day_changes:
            hours_since_change = []
            for change in same_day_changes:
                change_time = datetime.fromisoformat(change.timestamp)
                hours_diff = (datetime.utcnow() - change_time).total_seconds() / 3600
                hours_since_change.append(hours_diff)

            context["same_day_beneficiary_changes"] = [
                {
                    "change_id": change.change_id,
                    "timestamp": change.timestamp,
                    "change_type": change.change_type,
                    "verified": change.verified,
                    "change_source": change.change_source,
                    "hours_ago": hours_diff
                }
                for change, hours_diff in zip(same_day_changes, hours_since_change)
            ]
            context["min_hours_since_change"] = min(hours_since_change)
            return True

        return False

    return Rule(
        name="beneficiary_same_day_payment",
        description=f"Payment to beneficiary within {BENEFICIARY_SAME_DAY_PAYMENT_HOURS} hours of account change (CRITICAL)",
        condition_func=condition,
        weight=weight
    )


def create_recent_account_change_payment_rule(db: Session, weight: float = 4.0) -> Rule:
    """
    Detect payments to beneficiaries with recent account changes.

    Payments within 7 days of an account change are high-risk, as attackers
    typically act quickly after compromising vendor communications.
    """
    def condition(transaction: Dict[str, Any], context: Dict[str, Any]) -> bool:
        if not is_beneficiary_payment(transaction):
            return False

        beneficiary = get_beneficiary_from_transaction(db, transaction)
        if not beneficiary:
            return False

        # Check for recent changes within critical window
        cutoff_date = datetime.utcnow() - timedelta(days=BENEFICIARY_CRITICAL_CHANGE_WINDOW_DAYS)
        cutoff_iso = cutoff_date.isoformat()

        recent_changes = db.query(BeneficiaryChangeHistory).filter(
            BeneficiaryChangeHistory.beneficiary_id == beneficiary.beneficiary_id,
            BeneficiaryChangeHistory.change_type.in_(["account_number", "routing_number", "bank_name"]),
            BeneficiaryChangeHistory.timestamp > cutoff_iso
        ).all()

        if recent_changes:
            context["recent_beneficiary_changes"] = [
                {
                    "change_id": change.change_id,
                    "timestamp": change.timestamp,
                    "change_type": change.change_type,
                    "verified": change.verified,
                    "change_source": change.change_source,
                    "requestor_name": change.requestor_name,
                    "requestor_email": change.requestor_email
                }
                for change in recent_changes
            ]
            return True

        return False

    return Rule(
        name="beneficiary_recent_account_change",
        description=f"Payment to beneficiary with account changed within {BENEFICIARY_CRITICAL_CHANGE_WINDOW_DAYS} days",
        condition_func=condition,
        weight=weight
    )


def create_unverified_beneficiary_change_rule(db: Session, weight: float = 4.5) -> Rule:
    """
    Detect payments to beneficiaries with unverified account changes.

    Account changes that haven't been properly verified (callback, in-person, etc.)
    are extremely high risk for fraud.
    """
    def condition(transaction: Dict[str, Any], context: Dict[str, Any]) -> bool:
        if not is_beneficiary_payment(transaction):
            return False

        # Check if we already found recent changes
        recent_changes = context.get("recent_beneficiary_changes", [])
        same_day_changes = context.get("same_day_beneficiary_changes", [])

        all_changes = recent_changes + same_day_changes
        if not all_changes:
            return False

        # Check if any recent changes are unverified
        unverified = [c for c in all_changes if not c.get("verified", False)]

        if unverified:
            context["unverified_beneficiary_changes_count"] = len(unverified)
            context["unverified_beneficiary_changes"] = unverified
            return True

        return False

    return Rule(
        name="beneficiary_unverified_account_change",
        description="Payment to beneficiary with unverified banking information changes",
        condition_func=condition,
        weight=weight
    )


def create_suspicious_change_source_rule(db: Session, weight: float = 3.5) -> Rule:
    """
    Detect beneficiary account changes from suspicious sources.

    Email and phone requests are the primary vectors for vendor impersonation.
    Legitimate changes typically come through authenticated portals or ERP systems.
    """
    def condition(transaction: Dict[str, Any], context: Dict[str, Any]) -> bool:
        if not is_beneficiary_payment(transaction):
            return False

        recent_changes = context.get("recent_beneficiary_changes", [])
        same_day_changes = context.get("same_day_beneficiary_changes", [])

        all_changes = recent_changes + same_day_changes
        if not all_changes:
            return False

        # Email and phone requests are high-risk for BEC attacks
        suspicious_sources = ["email_request", "phone_request", "fax"]
        suspicious = [
            c for c in all_changes
            if c.get("change_source") in suspicious_sources
        ]

        if suspicious:
            context["suspicious_beneficiary_change_sources"] = [
                c.get("change_source") for c in suspicious
            ]
            context["suspicious_change_details"] = suspicious
            return True

        return False

    return Rule(
        name="beneficiary_suspicious_change_source",
        description="Beneficiary account changed via email/phone/fax request (BEC risk)",
        condition_func=condition,
        weight=weight
    )


def create_first_payment_after_change_rule(db: Session, weight: float = 3.0) -> Rule:
    """
    Detect if this is the first payment after a beneficiary account change.

    The first payment to a new account is when fraud is most likely to succeed,
    before the legitimate vendor realizes they haven't been paid.
    """
    def condition(transaction: Dict[str, Any], context: Dict[str, Any]) -> bool:
        if not is_beneficiary_payment(transaction):
            return False

        beneficiary = get_beneficiary_from_transaction(db, transaction)
        if not beneficiary:
            return False

        # Check if there were any account changes since last payment
        if not beneficiary.last_payment_date:
            # No previous payment - could be new vendor
            return False

        last_payment = datetime.fromisoformat(beneficiary.last_payment_date)

        changes_since_payment = db.query(BeneficiaryChangeHistory).filter(
            BeneficiaryChangeHistory.beneficiary_id == beneficiary.beneficiary_id,
            BeneficiaryChangeHistory.change_type.in_(["account_number", "routing_number"]),
            BeneficiaryChangeHistory.timestamp > last_payment.isoformat()
        ).first()

        if changes_since_payment:
            context["first_payment_after_beneficiary_change"] = True
            context["last_payment_date"] = beneficiary.last_payment_date
            context["days_since_last_payment"] = (datetime.utcnow() - last_payment).days
            return True

        return False

    return Rule(
        name="beneficiary_first_payment_after_change",
        description="First payment to beneficiary after account information change",
        condition_func=condition,
        weight=weight
    )


def create_high_value_payment_rule(weight: float = 2.5) -> Rule:
    """
    Flag high-value payments to beneficiaries for additional scrutiny.

    Large payments combined with recent account changes are prime targets for fraud.
    """
    def condition(transaction: Dict[str, Any], context: Dict[str, Any]) -> bool:
        if not is_beneficiary_payment(transaction):
            return False

        amount = transaction.get("amount", 0)
        if amount >= BENEFICIARY_HIGH_VALUE_THRESHOLD:
            context["high_value_beneficiary_payment"] = True
            context["payment_amount"] = amount
            return True

        return False

    return Rule(
        name="beneficiary_high_value_payment",
        description=f"High-value payment to beneficiary (>= ${BENEFICIARY_HIGH_VALUE_THRESHOLD:,.2f})",
        condition_func=condition,
        weight=weight
    )


def create_rapid_account_changes_rule(db: Session, weight: float = 3.5) -> Rule:
    """
    Detect multiple beneficiary account changes in a short period.

    Multiple changes could indicate:
    - Repeated compromise attempts
    - Testing by attackers
    - Confusion that fraudsters can exploit
    """
    def condition(transaction: Dict[str, Any], context: Dict[str, Any]) -> bool:
        if not is_beneficiary_payment(transaction):
            return False

        beneficiary = get_beneficiary_from_transaction(db, transaction)
        if not beneficiary:
            return False

        # Check for multiple changes in the window
        cutoff_date = datetime.utcnow() - timedelta(days=BENEFICIARY_RAPID_CHANGE_WINDOW_DAYS)
        cutoff_iso = cutoff_date.isoformat()

        change_count = db.query(BeneficiaryChangeHistory).filter(
            BeneficiaryChangeHistory.beneficiary_id == beneficiary.beneficiary_id,
            BeneficiaryChangeHistory.change_type.in_(["account_number", "routing_number", "bank_name"]),
            BeneficiaryChangeHistory.timestamp > cutoff_iso
        ).count()

        if change_count >= BENEFICIARY_RAPID_CHANGE_THRESHOLD:
            context["rapid_beneficiary_changes_count"] = change_count
            context["rapid_changes_window_days"] = BENEFICIARY_RAPID_CHANGE_WINDOW_DAYS
            return True

        return False

    return Rule(
        name="beneficiary_rapid_account_changes",
        description=f"Multiple beneficiary account changes ({BENEFICIARY_RAPID_CHANGE_THRESHOLD}+) within {BENEFICIARY_RAPID_CHANGE_WINDOW_DAYS} days",
        condition_func=condition,
        weight=weight
    )


def create_new_beneficiary_payment_rule(db: Session, weight: float = 2.0) -> Rule:
    """
    Detect payments to newly registered beneficiaries.

    New vendors with no payment history deserve extra scrutiny,
    especially if combined with other risk factors.
    """
    def condition(transaction: Dict[str, Any], context: Dict[str, Any]) -> bool:
        if not is_beneficiary_payment(transaction):
            return False

        beneficiary = get_beneficiary_from_transaction(db, transaction)
        if not beneficiary:
            return False

        # Check if beneficiary is newly registered
        registration_date = datetime.fromisoformat(beneficiary.registration_date)
        days_since_registration = (datetime.utcnow() - registration_date).days

        if days_since_registration <= BENEFICIARY_NEW_VENDOR_DAYS:
            context["new_beneficiary"] = True
            context["days_since_registration"] = days_since_registration
            context["total_payments_to_beneficiary"] = beneficiary.total_payments_received
            return True

        return False

    return Rule(
        name="beneficiary_new_vendor_payment",
        description=f"Payment to newly registered beneficiary (within {BENEFICIARY_NEW_VENDOR_DAYS} days)",
        condition_func=condition,
        weight=weight
    )


def create_weekend_change_rule(db: Session, weight: float = 2.0) -> Rule:
    """
    Detect beneficiary account changes made during weekends.

    Weekend changes are unusual for legitimate business operations and may indicate
    fraud attempts when AP staff is unavailable to verify.
    """
    def condition(transaction: Dict[str, Any], context: Dict[str, Any]) -> bool:
        if not is_beneficiary_payment(transaction):
            return False

        recent_changes = context.get("recent_beneficiary_changes", [])
        same_day_changes = context.get("same_day_beneficiary_changes", [])

        all_changes = recent_changes + same_day_changes
        if not all_changes:
            return False

        weekend_changes = []
        for change in all_changes:
            change_time = datetime.fromisoformat(change["timestamp"])
            # Saturday = 5, Sunday = 6
            if change_time.weekday() >= 5:
                weekend_changes.append(change)

        if weekend_changes:
            context["weekend_beneficiary_changes_count"] = len(weekend_changes)
            return True

        return False

    return Rule(
        name="beneficiary_weekend_account_change",
        description="Beneficiary account change made during weekend before payment",
        condition_func=condition,
        weight=weight
    )


def create_off_hours_change_rule(db: Session, weight: float = 1.5) -> Rule:
    """
    Detect beneficiary account changes made during off-hours.

    Changes made between 10 PM and 6 AM are unusual for legitimate business requests.
    """
    def condition(transaction: Dict[str, Any], context: Dict[str, Any]) -> bool:
        if not is_beneficiary_payment(transaction):
            return False

        recent_changes = context.get("recent_beneficiary_changes", [])
        same_day_changes = context.get("same_day_beneficiary_changes", [])

        all_changes = recent_changes + same_day_changes
        if not all_changes:
            return False

        off_hours_changes = []
        for change in all_changes:
            change_time = datetime.fromisoformat(change["timestamp"])
            hour = change_time.hour
            # Off hours: 22:00 - 06:00
            if hour >= 22 or hour < 6:
                off_hours_changes.append(change)

        if off_hours_changes:
            context["off_hours_beneficiary_changes_count"] = len(off_hours_changes)
            return True

        return False

    return Rule(
        name="beneficiary_off_hours_account_change",
        description="Beneficiary account change made during off-hours (10 PM - 6 AM)",
        condition_func=condition,
        weight=weight
    )


def initialize_beneficiary_fraud_rules(db: Session) -> List[Rule]:
    """
    Initialize all beneficiary/vendor fraud detection rules.

    These rules detect vendor impersonation and BEC attacks where supplier
    bank details are changed fraudulently and payments are redirected.

    Returns:
        List of configured Rule objects for beneficiary fraud detection
    """
    return [
        create_same_day_payment_after_change_rule(db),
        create_recent_account_change_payment_rule(db),
        create_unverified_beneficiary_change_rule(db),
        create_suspicious_change_source_rule(db),
        create_first_payment_after_change_rule(db),
        create_high_value_payment_rule(),
        create_rapid_account_changes_rule(db),
        create_new_beneficiary_payment_rule(db),
        create_weekend_change_rule(db),
        create_off_hours_change_rule(db),
    ]
