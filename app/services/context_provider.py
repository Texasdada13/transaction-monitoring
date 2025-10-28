# app/services/context_provider.py
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import json
import datetime
from app.models.database import Transaction, Account, Employee, AccountChangeHistory, Beneficiary, Blacklist, DeviceSession, VPNProxyIP, HighRiskLocation, BehavioralBiometric, FraudFlag
from app.services.chain_analyzer import ChainAnalyzer

class ContextProvider:
    def __init__(self, db: Session, enable_chain_analysis: bool = True):
        """
        Initialize context provider with database session.

        Args:
            db: SQLAlchemy database session
            enable_chain_analysis: Whether to enable chain analysis (default True)
        """
        self.db = db
        self.enable_chain_analysis = enable_chain_analysis
        self.chain_analyzer = ChainAnalyzer(db) if enable_chain_analysis else None
    
    def get_transaction_context(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gather contextual information about the account and transaction history.
        
        Args:
            transaction: Transaction data
            
        Returns:
            Context dictionary with historical data
        """
        context = {}
        account_id = transaction.get("account_id")
        
        if not account_id:
            return context
        
        # Get account information
        account = self.db.query(Account).filter(Account.account_id == account_id).first()
        if account:
            # Calculate account age
            creation_date = datetime.datetime.fromisoformat(account.creation_date)
            account_age = (datetime.datetime.utcnow() - creation_date).days
            context["account_age_days"] = account_age
            context["risk_tier"] = account.risk_tier
            
        # Get transaction history
        self._add_transaction_history(context, account_id, transaction)
        
        # Check if counterparty is new
        context["is_new_counterparty"] = self._is_new_counterparty(
            account_id,
            transaction.get("counterparty_id")
        )

        # Add money mule detection context
        self._add_money_mule_context(context, account_id, transaction)

        # Add beneficiary fraud detection context
        self._add_beneficiary_context(context, account_id, transaction)

        # Add chain analysis if enabled
        if self.enable_chain_analysis and self.chain_analyzer:
            chain_analysis = self.chain_analyzer.analyze_transaction_chains(
                account_id, transaction
            )
            context["chain_analysis"] = chain_analysis

        # Add account takeover detection context
        self._add_account_takeover_context(context, account_id, transaction)

        # Add odd hours transaction detection context
        self._add_odd_hours_context(context, account_id, transaction)

        # Add geographic context
        geographic_context = self.get_geographic_context(transaction)
        context.update(geographic_context)

        # Add blacklist detection context
        self._add_blacklist_context(context, transaction)

        # Add device fingerprinting context
        self._add_device_fingerprint_context(context, account_id, transaction)

        # Add VPN/proxy detection context
        self._add_vpn_proxy_context(context, transaction)

        # Add geo-location fraud detection context
        self._add_geolocation_context(context, account_id, transaction)

        # Add behavioral biometrics fraud detection context
        self._add_behavioral_biometric_context(context, account_id, transaction)

        # Add recipient relationship analysis context
        self._add_recipient_relationship_context(context, account_id, transaction)

        # Add social trust score context
        self._add_social_trust_score_context(context, account_id, transaction)

        # Add account age fraud detection context
        self._add_account_age_context(context, account_id, transaction)

        # Add high-risk transaction times fraud detection context
        self._add_high_risk_transaction_times_context(context, account_id, transaction)

        # Add past fraudulent behavior flags detection context
        self._add_past_fraud_flags_context(context, account_id, transaction)

        return context
    
    def _add_transaction_history(self, context: Dict[str, Any],
                                account_id: str,
                                current_tx: Dict[str, Any]) -> None:
        """Add transaction history data to context."""
        # Transaction velocity for different time windows
        timeframes = [1, 6, 24, 168]  # hours (1h, 6h, 24h, 1 week)
        context["tx_count_last_hours"] = {}
        context["small_deposit_count"] = {}

        now = datetime.datetime.utcnow()
        for hours in timeframes:
            time_threshold = (now - datetime.timedelta(hours=hours)).isoformat()

            count = self.db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.timestamp > time_threshold
            ).count()

            context["tx_count_last_hours"][hours] = count

            # Count small deposits (≤ $2.00) for fraud detection
            small_deposit_count = self.db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.timestamp > time_threshold,
                Transaction.amount > 0,
                Transaction.amount <= 2.0,
                Transaction.transaction_type.in_(["ACH", "WIRE", "DEPOSIT", "CREDIT"])
            ).count()

            # Include current transaction if it's a small deposit
            current_amount = current_tx.get("amount", 0)
            current_type = current_tx.get("transaction_type", "").upper()
            if (0 < current_amount <= 2.0 and
                current_type in ["ACH", "WIRE", "DEPOSIT", "CREDIT"]):
                small_deposit_count += 1

            context["small_deposit_count"][hours] = small_deposit_count
        
        # Calculate average transaction amount for this type
        tx_type = current_tx.get("transaction_type")
        if tx_type:
            # Get transactions of same type in last 90 days
            ninety_days_ago = (now - datetime.timedelta(days=90)).isoformat()
            
            similar_txs = self.db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.transaction_type == tx_type,
                Transaction.timestamp > ninety_days_ago
            ).all()
            
            if similar_txs:
                amounts = [tx.amount for tx in similar_txs]
                avg_amount = sum(amounts) / len(amounts)
                context["avg_transaction_amount"] = avg_amount
                
                # Calculate standard deviation
                import math
                variance = sum((x - avg_amount) ** 2 for x in amounts) / len(amounts)
                std_dev = math.sqrt(variance)
                
                # Calculate deviation of current transaction
                current_amount = current_tx.get("amount", 0)
                if std_dev > 0:
                    context["amount_deviation"] = abs(current_amount - avg_amount) / std_dev
                else:
                    # If all historical amounts are identical, use ratio
                    context["amount_deviation"] = abs(current_amount / max(avg_amount, 0.01))
            else:
                # First transaction of this type
                context["avg_transaction_amount"] = 0
                context["amount_deviation"] = 5.0  # High deviation for first transaction
    
    def _is_new_counterparty(self, account_id: str, counterparty_id: str) -> bool:
        """Check if this is a new counterparty for this account."""
        if not counterparty_id:
            return False

        # Look for previous transactions with this counterparty
        previous_tx = self.db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.counterparty_id == counterparty_id
        ).first()

        return previous_tx is None

    def _add_money_mule_context(self, context: Dict[str, Any],
                                account_id: str,
                                current_tx: Dict[str, Any]) -> None:
        """
        Add money mule detection context.

        Money mule pattern: Multiple small incoming payments quickly followed by outgoing transfers.
        """
        now = datetime.datetime.utcnow()

        # Analyze patterns over different time windows
        time_windows = [24, 72, 168]  # 1 day, 3 days, 1 week (hours)

        for hours in time_windows:
            time_threshold = (now - datetime.timedelta(hours=hours)).isoformat()

            # Get incoming transactions (credits)
            incoming_txs = self.db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.direction == "credit",
                Transaction.timestamp > time_threshold
            ).all()

            # Get outgoing transactions (debits)
            outgoing_txs = self.db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.direction == "debit",
                Transaction.timestamp > time_threshold
            ).all()

            # Calculate metrics
            incoming_count = len(incoming_txs)
            outgoing_count = len(outgoing_txs)
            incoming_total = sum(tx.amount for tx in incoming_txs)
            outgoing_total = sum(tx.amount for tx in outgoing_txs)

            # Store in context
            context[f"incoming_count_{hours}h"] = incoming_count
            context[f"outgoing_count_{hours}h"] = outgoing_count
            context[f"incoming_total_{hours}h"] = incoming_total
            context[f"outgoing_total_{hours}h"] = outgoing_total

            # Calculate average incoming transaction amount (for "many small" detection)
            if incoming_count > 0:
                avg_incoming = incoming_total / incoming_count
                context[f"avg_incoming_amount_{hours}h"] = avg_incoming
            else:
                context[f"avg_incoming_amount_{hours}h"] = 0

            # Calculate flow-through ratio (how much incoming is sent out)
            if incoming_total > 0:
                flow_through_ratio = outgoing_total / incoming_total
                context[f"flow_through_ratio_{hours}h"] = flow_through_ratio
            else:
                context[f"flow_through_ratio_{hours}h"] = 0

        # Calculate average time between incoming and outgoing (velocity of moving money)
        # For recent 7-day window
        week_ago = (now - datetime.timedelta(days=7)).isoformat()

        recent_incoming = self.db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.direction == "credit",
            Transaction.timestamp > week_ago
        ).order_by(Transaction.timestamp).all()

        recent_outgoing = self.db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.direction == "debit",
            Transaction.timestamp > week_ago
        ).order_by(Transaction.timestamp).all()

        # Calculate average time from incoming to next outgoing
        if recent_incoming and recent_outgoing:
            time_gaps = []
            for incoming in recent_incoming:
                incoming_time = datetime.datetime.fromisoformat(incoming.timestamp)
                # Find next outgoing after this incoming
                for outgoing in recent_outgoing:
                    outgoing_time = datetime.datetime.fromisoformat(outgoing.timestamp)
                    if outgoing_time > incoming_time:
                        gap_hours = (outgoing_time - incoming_time).total_seconds() / 3600
                        time_gaps.append(gap_hours)
                        break

            if time_gaps:
                avg_time_to_transfer = sum(time_gaps) / len(time_gaps)
                context["avg_hours_to_transfer"] = avg_time_to_transfer
            else:
                context["avg_hours_to_transfer"] = None
        else:
            context["avg_hours_to_transfer"] = None

    def _add_beneficiary_context(self, context: Dict[str, Any],
                                  account_id: str,
                                  current_tx: Dict[str, Any]) -> None:
        """
        Add beneficiary fraud detection context.

        Detects rapid addition of many beneficiaries followed by payments.
        """
        now = datetime.datetime.utcnow()
        counterparty_id = current_tx.get("counterparty_id")

        # Analyze beneficiary additions over time windows
        time_windows = [24, 72, 168]  # 1 day, 3 days, 1 week (hours)

        for hours in time_windows:
            time_threshold = (now - datetime.timedelta(hours=hours)).isoformat()

            # Count beneficiaries added in this window
            beneficiaries_added = self.db.query(Beneficiary).filter(
                Beneficiary.account_id == account_id,
                Beneficiary.registration_date > time_threshold,
                Beneficiary.status == "active"
            ).all()

            context[f"beneficiaries_added_{hours}h"] = len(beneficiaries_added)

            # Track beneficiaries from same IP address
            if beneficiaries_added:
                ip_counts = {}
                user_counts = {}

                for beneficiary in beneficiaries_added:
                    if beneficiary.ip_address:
                        ip_counts[beneficiary.ip_address] = ip_counts.get(beneficiary.ip_address, 0) + 1
                    if beneficiary.added_by:
                        user_counts[beneficiary.added_by] = user_counts.get(beneficiary.added_by, 0) + 1

                # Find most common IP and user
                if ip_counts:
                    most_common_ip = max(ip_counts.items(), key=lambda x: x[1])
                    context[f"beneficiaries_same_ip_{hours}h"] = most_common_ip[1]
                    context["same_source_ip"] = most_common_ip[0]
                else:
                    context[f"beneficiaries_same_ip_{hours}h"] = 0

                if user_counts:
                    most_common_user = max(user_counts.items(), key=lambda x: x[1])
                    context[f"beneficiaries_same_user_{hours}h"] = most_common_user[1]
                    context["same_source_user"] = most_common_user[0]
                else:
                    context[f"beneficiaries_same_user_{hours}h"] = 0

            # Count payments to newly added beneficiaries in this window
            new_beneficiary_ids = [b.counterparty_id for b in beneficiaries_added if b.counterparty_id]

            if new_beneficiary_ids:
                payments_to_new = self.db.query(Transaction).filter(
                    Transaction.account_id == account_id,
                    Transaction.direction == "debit",
                    Transaction.counterparty_id.in_(new_beneficiary_ids),
                    Transaction.timestamp > time_threshold
                ).count()

                total_payments = self.db.query(Transaction).filter(
                    Transaction.account_id == account_id,
                    Transaction.direction == "debit",
                    Transaction.timestamp > time_threshold
                ).count()

                context[f"new_beneficiary_payment_count_{hours}h"] = payments_to_new

                if total_payments > 0:
                    context[f"new_beneficiary_payment_ratio_{hours}h"] = payments_to_new / total_payments
                else:
                    context[f"new_beneficiary_payment_ratio_{hours}h"] = 0.0
            else:
                context[f"new_beneficiary_payment_count_{hours}h"] = 0
                context[f"new_beneficiary_payment_ratio_{hours}h"] = 0.0

        # Check if current transaction is to a recently added beneficiary
        if counterparty_id:
            beneficiary = self.db.query(Beneficiary).filter(
                Beneficiary.account_id == account_id,
                Beneficiary.counterparty_id == counterparty_id,
                Beneficiary.status == "active"
            ).first()

            if beneficiary:
                # Calculate beneficiary age
                added_time = datetime.datetime.fromisoformat(beneficiary.registration_date)
                beneficiary_age_hours = (now - added_time).total_seconds() / 3600

                context["is_new_beneficiary"] = beneficiary_age_hours <= 48  # Less than 48 hours
                context["beneficiary_age_hours"] = beneficiary_age_hours
                context["is_beneficiary_verified"] = beneficiary.verified
                context["beneficiary_addition_source"] = beneficiary.addition_source
                context["beneficiary_flagged"] = beneficiary.flagged_as_suspicious
            else:
                # No beneficiary record - might be first transaction
                context["is_new_beneficiary"] = False
                context["is_beneficiary_verified"] = True  # Assume verified if no record
                context["beneficiary_age_hours"] = None

    def _add_account_takeover_context(self, context: Dict[str, Any],
                                       account_id: str,
                                       current_tx: Dict[str, Any]) -> None:
        """
        Add account takeover detection context.

        Account takeover pattern:
        - Phone number or device changes occur
        - Followed by suspicious outgoing transfers shortly after
        - This prevents legitimate user from getting security alerts
        """
        now = datetime.datetime.utcnow()

        # Check for recent phone/SIM/device changes (within last 48 hours)
        time_windows = [1, 6, 24, 48]  # hours

        for hours in time_windows:
            time_threshold = (now - datetime.timedelta(hours=hours)).isoformat()

            # Query for phone/device changes
            phone_changes = self.db.query(AccountChangeHistory).filter(
                AccountChangeHistory.account_id == account_id,
                AccountChangeHistory.change_type.in_(["phone", "device", "sim", "phone_number"]),
                AccountChangeHistory.timestamp > time_threshold
            ).all()

            context[f"phone_changes_count_{hours}h"] = len(phone_changes)

            if phone_changes:
                # Store details of most recent change in this window
                most_recent = max(phone_changes, key=lambda c: c.timestamp)
                context[f"most_recent_phone_change_{hours}h"] = {
                    "timestamp": most_recent.timestamp,
                    "change_type": most_recent.change_type,
                    "change_source": most_recent.change_source,
                    "verified": most_recent.verified,
                    "old_value": most_recent.old_value,
                    "new_value": most_recent.new_value
                }

                # Check if change was flagged as suspicious
                suspicious_changes = [c for c in phone_changes if c.flagged_as_suspicious]
                context[f"suspicious_phone_changes_{hours}h"] = len(suspicious_changes)

                # Check if changes were unverified
                unverified_changes = [c for c in phone_changes if not c.verified]
                context[f"unverified_phone_changes_{hours}h"] = len(unverified_changes)

        # For outgoing transfers analysis - check if current transaction is outgoing
        is_outgoing = current_tx.get("direction") == "debit"
        context["is_outgoing_transfer"] = is_outgoing

        # If this is an outgoing transfer, calculate time since most recent phone change
        if is_outgoing and context.get("phone_changes_count_48h", 0) > 0:
            # Find the most recent phone change across all windows
            all_changes = self.db.query(AccountChangeHistory).filter(
                AccountChangeHistory.account_id == account_id,
                AccountChangeHistory.change_type.in_(["phone", "device", "sim", "phone_number"])
            ).order_by(AccountChangeHistory.timestamp.desc()).first()

            if all_changes:
                change_time = datetime.datetime.fromisoformat(all_changes.timestamp)
                current_time = datetime.datetime.fromisoformat(
                    current_tx.get("timestamp", now.isoformat())
                )
                hours_since_change = (current_time - change_time).total_seconds() / 3600
                context["hours_since_phone_change"] = hours_since_change

                # Store if this is first outgoing transfer after phone change
                is_first_outgoing = self.db.query(Transaction).filter(
                    Transaction.account_id == account_id,
                    Transaction.direction == "debit",
                    Transaction.timestamp > all_changes.timestamp,
                    Transaction.timestamp < current_tx.get("timestamp", now.isoformat())
                ).count() == 0

                context["is_first_transfer_after_phone_change"] = is_first_outgoing

    def _add_odd_hours_context(self, context: Dict[str, Any],
                                account_id: str,
                                current_tx: Dict[str, Any]) -> None:
        """
        Add odd hours transaction detection context.

        Detects large transactions occurring at unusual times:
        - Outside normal business hours (late night/early morning)
        - Outside the customer's typical transaction timing patterns
        """
        from config.settings import (
            ODD_HOURS_START,
            ODD_HOURS_END,
            ODD_HOURS_LOOKBACK_DAYS,
            ODD_HOURS_MIN_HISTORICAL_TRANSACTIONS
        )

        now = datetime.datetime.utcnow()

        # Get transaction timestamp
        tx_timestamp_str = current_tx.get("timestamp", now.isoformat())
        tx_timestamp = datetime.datetime.fromisoformat(tx_timestamp_str)

        # Extract hour of day (0-23)
        tx_hour = tx_timestamp.hour
        context["transaction_hour"] = tx_hour

        # Check if transaction is during odd hours (10 PM - 6 AM by default)
        is_odd_hours = False
        if ODD_HOURS_START > ODD_HOURS_END:
            # Wraps around midnight (e.g., 22:00 to 06:00)
            is_odd_hours = tx_hour >= ODD_HOURS_START or tx_hour < ODD_HOURS_END
        else:
            # Does not wrap (e.g., 01:00 to 05:00)
            is_odd_hours = ODD_HOURS_START <= tx_hour < ODD_HOURS_END

        context["is_odd_hours"] = is_odd_hours
        context["odd_hours_window"] = f"{ODD_HOURS_START:02d}:00 - {ODD_HOURS_END:02d}:00"

        # Check if it's a weekend
        # Monday=0, Sunday=6
        is_weekend = tx_timestamp.weekday() >= 5
        context["is_weekend"] = is_weekend

        # Analyze historical transaction timing patterns
        lookback_date = (now - datetime.timedelta(days=ODD_HOURS_LOOKBACK_DAYS)).isoformat()

        # Get historical transactions for this account
        historical_txs = self.db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.timestamp > lookback_date
        ).all()

        if len(historical_txs) >= ODD_HOURS_MIN_HISTORICAL_TRANSACTIONS:
            # Analyze timing patterns
            odd_hours_count = 0
            business_hours_count = 0
            weekend_count = 0
            hour_distribution = [0] * 24  # Count per hour

            for tx in historical_txs:
                tx_time = datetime.datetime.fromisoformat(tx.timestamp)
                tx_h = tx_time.hour

                hour_distribution[tx_h] += 1

                # Check if odd hours
                if ODD_HOURS_START > ODD_HOURS_END:
                    if tx_h >= ODD_HOURS_START or tx_h < ODD_HOURS_END:
                        odd_hours_count += 1
                    else:
                        business_hours_count += 1
                else:
                    if ODD_HOURS_START <= tx_h < ODD_HOURS_END:
                        odd_hours_count += 1
                    else:
                        business_hours_count += 1

                # Check if weekend
                if tx_time.weekday() >= 5:
                    weekend_count += 1

            total_count = len(historical_txs)

            # Calculate ratios
            context["historical_odd_hours_ratio"] = odd_hours_count / total_count if total_count > 0 else 0
            context["historical_business_hours_ratio"] = business_hours_count / total_count if total_count > 0 else 0
            context["historical_weekend_ratio"] = weekend_count / total_count if total_count > 0 else 0
            context["historical_transaction_count"] = total_count
            context["hour_distribution"] = hour_distribution

            # Determine if current transaction is unusual based on historical pattern
            # If customer typically transacts during business hours, odd hours transaction is unusual
            context["deviates_from_pattern"] = (
                is_odd_hours and
                context["historical_business_hours_ratio"] > 0.8  # 80%+ of transactions during business hours
            )

            # Check if this specific hour is unusual for the customer
            current_hour_historical_count = hour_distribution[tx_hour]
            avg_hourly_count = total_count / 24

            # If this hour has significantly fewer historical transactions
            context["hour_is_unusual"] = (
                current_hour_historical_count < (avg_hourly_count * 0.5) and
                total_count >= 10  # Need enough data
            )

        else:
            # Not enough historical data
            context["historical_transaction_count"] = len(historical_txs)
            context["insufficient_history"] = True

        # Check for other odd hours transactions in recent period (last 7 days)
        recent_lookback = (now - datetime.timedelta(days=7)).isoformat()
        recent_odd_hours_txs = []

        for tx in self.db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.timestamp > recent_lookback
        ).all():
            tx_time = datetime.datetime.fromisoformat(tx.timestamp)
            tx_h = tx_time.hour

            # Check if odd hours
            if ODD_HOURS_START > ODD_HOURS_END:
                if tx_h >= ODD_HOURS_START or tx_h < ODD_HOURS_END:
                    recent_odd_hours_txs.append(tx)
            else:
                if ODD_HOURS_START <= tx_h < ODD_HOURS_END:
                    recent_odd_hours_txs.append(tx)

        context["recent_odd_hours_transaction_count"] = len(recent_odd_hours_txs)

        # If this is an odd hours transaction, calculate total amount in recent odd hours
        if is_odd_hours and recent_odd_hours_txs:
            recent_odd_hours_total = sum(abs(tx.amount) for tx in recent_odd_hours_txs)
            context["recent_odd_hours_total_amount"] = recent_odd_hours_total

    def get_payroll_context(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get payroll-specific context for fraud detection.

        Args:
            transaction: Transaction data

        Returns:
            Context dictionary with payroll-related information
        """
        context = {}

        # Try to get employee information
        employee = self._get_employee_from_transaction(transaction)
        if not employee:
            return context

        context["employee_id"] = employee.employee_id
        context["employee_name"] = employee.name
        context["employment_status"] = employee.employment_status

        # Get account change history
        account_changes = self.db.query(AccountChangeHistory).filter(
            AccountChangeHistory.employee_id == employee.employee_id
        ).order_by(AccountChangeHistory.timestamp.desc()).all()

        if account_changes:
            context["total_account_changes"] = len(account_changes)

            # Most recent change
            most_recent = account_changes[0]
            context["most_recent_change"] = {
                "timestamp": most_recent.timestamp,
                "change_type": most_recent.change_type,
                "change_source": most_recent.change_source,
                "verified": most_recent.verified,
                "flagged_as_suspicious": most_recent.flagged_as_suspicious
            }

            # Count unverified changes
            unverified_count = sum(1 for c in account_changes if not c.verified)
            context["unverified_changes_count"] = unverified_count

            # Count suspicious-source changes
            suspicious_sources = ["email_request", "phone_request"]
            suspicious_count = sum(
                1 for c in account_changes
                if c.change_source in suspicious_sources
            )
            context["suspicious_source_changes_count"] = suspicious_count

        # Get time since last payroll
        if employee.last_payroll_date:
            last_payroll = datetime.datetime.fromisoformat(employee.last_payroll_date)
            days_since = (datetime.datetime.utcnow() - last_payroll).days
            context["days_since_last_payroll"] = days_since
            context["last_payroll_date"] = employee.last_payroll_date

        # Payroll frequency info
        context["payroll_frequency"] = employee.payroll_frequency

        return context

    def _get_employee_from_transaction(self, transaction: Dict[str, Any]) -> Employee:
        """Get employee record from transaction data."""
        # Try tx_metadata first (also check 'metadata' for backward compatibility)
        tx_metadata = transaction.get("tx_metadata") or transaction.get("metadata")
        if tx_metadata:
            if isinstance(tx_metadata, str):
                try:
                    tx_metadata = json.loads(tx_metadata)
                except:
                    tx_metadata = {}

            employee_id = tx_metadata.get("employee_id")
            if employee_id:
                employee = self.db.query(Employee).filter(
                    Employee.employee_id == employee_id
                ).first()
                if employee:
                    return employee

        # Fallback: try by account
        account_id = transaction.get("account_id")
        if account_id:
            return self.db.query(Employee).filter(
                Employee.account_id == account_id
            ).first()

        return None

    def get_check_context(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get check-specific context for fraud detection.

        This method analyzes check deposit patterns and identifies:
        - Duplicate check deposits (same check deposited multiple times)
        - Rapid check deposit sequences
        - Check amount mismatches (possible alteration)

        Args:
            transaction: Transaction data

        Returns:
            Context dictionary with check-related fraud indicators
        """
        context = {}

        # Extract check information from transaction metadata
        check_info = self._extract_check_info(transaction)
        if not check_info:
            return context  # Not a check transaction or no check data available

        account_id = transaction.get("account_id")
        check_number = check_info.get("check_number")
        check_amount = check_info.get("amount")

        # 1. Check for duplicate check deposits
        if check_number:
            duplicates = self._find_duplicate_checks(
                check_number=check_number,
                check_amount=check_amount,
                routing_number=check_info.get("routing_number"),
                account_number=check_info.get("account_number"),
                exclude_transaction_id=transaction.get("transaction_id")
            )

            if duplicates:
                context["duplicate_checks"] = [
                    {
                        "transaction_id": dup.transaction_id,
                        "account_id": dup.account_id,
                        "timestamp": dup.timestamp,
                        "amount": dup.amount,
                        "check_number": check_number
                    }
                    for dup in duplicates
                ]

        # 2. Count check deposits in the last hour (rapid sequence detection)
        if account_id:
            now = datetime.datetime.utcnow()
            one_hour_ago = (now - datetime.timedelta(hours=1)).isoformat()

            recent_checks = self.db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.timestamp > one_hour_ago,
                Transaction.direction == "credit",
                Transaction.transaction_type.in_([
                    "CHECK", "CHECK_DEPOSIT", "DEPOSIT",
                    "REMOTE_DEPOSIT", "MOBILE_DEPOSIT"
                ])
            ).all()

            context["check_count_1h"] = len(recent_checks)
            context["check_amount_1h"] = sum(tx.amount for tx in recent_checks)

            # Include current transaction if it's a check deposit
            if self._is_check_deposit(transaction):
                context["check_count_1h"] += 1
                context["check_amount_1h"] += transaction.get("amount", 0)

        # 3. Check for amount mismatches (possible check alteration)
        if check_number and check_amount:
            mismatch = self._check_amount_mismatch(
                check_number=check_number,
                current_amount=check_amount,
                routing_number=check_info.get("routing_number")
            )

            if mismatch:
                context["check_amount_mismatch"] = mismatch

        return context

    def _extract_check_info(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract check-specific information from transaction metadata.

        Args:
            transaction: Transaction dictionary

        Returns:
            Dictionary with check information, or empty dict if not available
        """
        metadata_str = transaction.get("tx_metadata", "{}")

        try:
            metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
        except json.JSONDecodeError:
            return {}

        check_info = {}

        # Extract check-specific fields
        if "check_number" in metadata:
            check_info["check_number"] = metadata["check_number"]
        if "check_amount" in metadata:
            check_info["amount"] = float(metadata["check_amount"])
        if "routing_number" in metadata:
            check_info["routing_number"] = metadata["routing_number"]
        if "account_number" in metadata:
            check_info["account_number"] = metadata["account_number"]
        if "payee" in metadata:
            check_info["payee"] = metadata["payee"]
        if "drawer" in metadata:
            check_info["drawer"] = metadata["drawer"]
        if "check_date" in metadata:
            check_info["check_date"] = metadata["check_date"]

        return check_info

    def _is_check_deposit(self, transaction: Dict[str, Any]) -> bool:
        """
        Determine if a transaction is a check deposit.

        Args:
            transaction: Transaction dictionary

        Returns:
            True if transaction is a check deposit, False otherwise
        """
        tx_type = transaction.get("transaction_type", "").upper()
        direction = transaction.get("direction", "").lower()

        return (
            direction == "credit" and
            tx_type in ["CHECK", "CHECK_DEPOSIT", "DEPOSIT", "REMOTE_DEPOSIT", "MOBILE_DEPOSIT"]
        )

    def _find_duplicate_checks(
        self,
        check_number: str,
        check_amount: float = None,
        routing_number: str = None,
        account_number: str = None,
        exclude_transaction_id: str = None,
        lookback_days: int = 90
    ):
        """
        Find previous deposits of the same check.

        A duplicate check is identified by matching:
        - Check number (required)
        - Check amount (if available)
        - Source routing/account numbers (if available)

        Args:
            check_number: The check number to search for
            check_amount: Amount on the check (optional)
            routing_number: Routing number from check (optional)
            account_number: Account number from check (optional)
            exclude_transaction_id: Transaction ID to exclude from results
            lookback_days: How many days to look back (default: 90)

        Returns:
            List of Transaction objects that match (duplicates)
        """
        now = datetime.datetime.utcnow()
        lookback_date = (now - datetime.timedelta(days=lookback_days)).isoformat()

        # Query for check deposits in the lookback period
        query = self.db.query(Transaction).filter(
            Transaction.timestamp > lookback_date,
            Transaction.direction == "credit",
            Transaction.transaction_type.in_([
                "CHECK", "CHECK_DEPOSIT", "DEPOSIT",
                "REMOTE_DEPOSIT", "MOBILE_DEPOSIT"
            ])
        )

        # Exclude the current transaction
        if exclude_transaction_id:
            query = query.filter(Transaction.transaction_id != exclude_transaction_id)

        all_check_txs = query.all()

        # Filter by check number and other attributes in metadata
        duplicates = []
        for tx in all_check_txs:
            try:
                metadata_str = tx.tx_metadata or "{}"
                metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str

                # Check if check number matches
                if metadata.get("check_number") == check_number:
                    # Check for amount match (if provided)
                    if check_amount is not None:
                        tx_check_amount = metadata.get("check_amount")
                        if tx_check_amount is not None:
                            # Amount should match closely (within $0.01 for floating point)
                            if abs(float(tx_check_amount) - check_amount) > 0.01:
                                continue  # Amount doesn't match, not a duplicate

                    # Check for routing number match (if provided)
                    if routing_number is not None:
                        tx_routing = metadata.get("routing_number")
                        if tx_routing is not None and tx_routing != routing_number:
                            continue  # Different bank, might not be duplicate

                    # Check for account number match (if provided)
                    if account_number is not None:
                        tx_account = metadata.get("account_number")
                        if tx_account is not None and tx_account != account_number:
                            continue  # Different account, might not be duplicate

                    # All criteria match - this is a duplicate
                    duplicates.append(tx)

            except (json.JSONDecodeError, ValueError, TypeError):
                # Skip transactions with invalid metadata
                continue

        return duplicates

    def _check_amount_mismatch(
        self,
        check_number: str,
        current_amount: float,
        routing_number: str = None,
        max_deviation_percent: float = 5.0,
        lookback_days: int = 180
    ) -> Dict[str, Any]:
        """
        Check if the check amount differs from previous deposits of the same check.

        This can indicate check alteration fraud.

        Args:
            check_number: The check number
            current_amount: Current transaction amount
            routing_number: Routing number from check (optional)
            max_deviation_percent: Maximum allowed deviation percentage
            lookback_days: How many days to look back

        Returns:
            Dictionary with mismatch details if found, None otherwise
        """
        now = datetime.datetime.utcnow()
        lookback_date = (now - datetime.timedelta(days=lookback_days)).isoformat()

        # Find previous deposits of this check number
        query = self.db.query(Transaction).filter(
            Transaction.timestamp > lookback_date,
            Transaction.direction == "credit",
            Transaction.transaction_type.in_([
                "CHECK", "CHECK_DEPOSIT", "DEPOSIT",
                "REMOTE_DEPOSIT", "MOBILE_DEPOSIT"
            ])
        )

        all_check_txs = query.all()

        # Find matching check numbers
        previous_amounts = []
        for tx in all_check_txs:
            try:
                metadata_str = tx.tx_metadata or "{}"
                metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str

                # Check if check number matches
                if metadata.get("check_number") == check_number:
                    # Check routing number if provided
                    if routing_number:
                        tx_routing = metadata.get("routing_number")
                        if tx_routing and tx_routing != routing_number:
                            continue  # Different bank

                    # Get the amount
                    tx_check_amount = metadata.get("check_amount")
                    if tx_check_amount is not None:
                        previous_amounts.append(float(tx_check_amount))

            except (json.JSONDecodeError, ValueError, TypeError):
                continue

        # Check for amount deviation
        if previous_amounts:
            # Use the most common previous amount as reference
            from collections import Counter
            amount_counts = Counter(previous_amounts)
            most_common_amount = amount_counts.most_common(1)[0][0]

            # Calculate deviation percentage
            if most_common_amount > 0:
                deviation_percent = abs(
                    (current_amount - most_common_amount) / most_common_amount * 100
                )

                if deviation_percent > max_deviation_percent:
                    return {
                        "previous_amount": most_common_amount,
                        "current_amount": current_amount,
                        "deviation_percent": deviation_percent,
                        "occurrences": amount_counts[most_common_amount]
                    }

        return None

    def get_geographic_context(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get geographic context for international payment fraud detection.

        Args:
            transaction: Transaction data

        Returns:
            Context dictionary with geographic information
        """
        context = {}

        # Only process outgoing payments
        if transaction.get("direction") != "debit":
            return context

        account_id = transaction.get("account_id")
        if not account_id:
            return context

        # Check if this is the first international payment
        # Get all previous outgoing transactions
        all_outgoing = self.db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.direction == "debit"
        ).all()

        # Check if any previous transactions were international
        has_previous_international = False
        for tx in all_outgoing:
            if tx.tx_metadata:
                try:
                    metadata = json.loads(tx.tx_metadata) if isinstance(tx.tx_metadata, str) else tx.tx_metadata
                    country = metadata.get("country") or metadata.get("country_code") or \
                              metadata.get("bank_country") or metadata.get("destination_country")
                    if country and str(country).upper()[:2] != "US":
                        has_previous_international = True
                        break
                except (json.JSONDecodeError, AttributeError):
                    pass

        # Check current transaction country
        tx_metadata = transaction.get("tx_metadata") or transaction.get("metadata")
        current_country = None
        if tx_metadata:
            if isinstance(tx_metadata, str):
                try:
                    tx_metadata = json.loads(tx_metadata)
                except json.JSONDecodeError:
                    tx_metadata = {}

            current_country = tx_metadata.get("country") or \
                             tx_metadata.get("country_code") or \
                             tx_metadata.get("bank_country") or \
                             tx_metadata.get("destination_country")

        # Flag if this is first international payment
        if current_country and str(current_country).upper()[:2] != "US":
            context["is_first_international_payment"] = not has_previous_international

        return context

    def _add_blacklist_context(self, context: Dict[str, Any],
                                transaction: Dict[str, Any]) -> None:
        """
        Add blacklist detection context.

        Checks if the counterparty, account, or other identifiers are on the blacklist.

        Args:
            context: Context dictionary to update
            transaction: Transaction data
        """
        counterparty_id = transaction.get("counterparty_id")

        # Initialize blacklist flags
        context["is_blacklisted"] = False
        context["blacklist_matches"] = []

        if not counterparty_id:
            return

        # Check if counterparty is blacklisted
        blacklist_entries = self.db.query(Blacklist).filter(
            Blacklist.status == "active",
            Blacklist.entity_value == counterparty_id
        ).all()

        # Also check by entity type if we have metadata
        tx_metadata = transaction.get("tx_metadata") or transaction.get("metadata")
        if tx_metadata and isinstance(tx_metadata, str):
            try:
                tx_metadata = json.loads(tx_metadata)
            except json.JSONDecodeError:
                tx_metadata = {}

        # Check for additional identifiers in metadata
        additional_checks = []
        if tx_metadata:
            # Check UPI ID
            upi_id = tx_metadata.get("upi_id")
            if upi_id:
                additional_checks.append(("upi", upi_id))

            # Check merchant ID
            merchant_id = tx_metadata.get("merchant_id")
            if merchant_id:
                additional_checks.append(("merchant", merchant_id))

            # Check routing number
            routing_number = tx_metadata.get("routing_number")
            if routing_number:
                additional_checks.append(("routing_number", routing_number))

            # Check email
            email = tx_metadata.get("email") or tx_metadata.get("recipient_email")
            if email:
                additional_checks.append(("email", email))

            # Check phone
            phone = tx_metadata.get("phone") or tx_metadata.get("recipient_phone")
            if phone:
                additional_checks.append(("phone", phone))

        # Query for additional identifier matches
        for entity_type, entity_value in additional_checks:
            matches = self.db.query(Blacklist).filter(
                Blacklist.status == "active",
                Blacklist.entity_type == entity_type,
                Blacklist.entity_value == entity_value
            ).all()
            blacklist_entries.extend(matches)

        # Process blacklist matches
        if blacklist_entries:
            context["is_blacklisted"] = True
            context["blacklist_matches"] = [
                {
                    "entity_type": entry.entity_type,
                    "entity_value": entry.entity_value,
                    "entity_name": entry.entity_name,
                    "reason": entry.reason,
                    "severity": entry.severity,
                    "added_date": entry.added_date,
                    "source": entry.source
                }
                for entry in blacklist_entries
            ]

            # Get highest severity level
            severity_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            max_severity = max(
                (entry.severity for entry in blacklist_entries),
                key=lambda s: severity_order.get(s, 0)
            )
            context["blacklist_max_severity"] = max_severity
            context["blacklist_match_count"] = len(blacklist_entries)

    def _add_device_fingerprint_context(self, context: Dict[str, Any],
                                         account_id: str,
                                         transaction: Dict[str, Any]) -> None:
        """
        Add device fingerprinting context for fraud detection.

        Analyzes device mismatches (device ID, browser, OS, IP) compared to historical sessions.

        Args:
            context: Context dictionary to update
            account_id: Account ID
            transaction: Transaction data
        """
        # Extract device information from transaction metadata
        tx_metadata = transaction.get("tx_metadata") or transaction.get("metadata")
        if tx_metadata and isinstance(tx_metadata, str):
            try:
                tx_metadata = json.loads(tx_metadata)
            except json.JSONDecodeError:
                tx_metadata = {}

        if not tx_metadata:
            context["device_info_available"] = False
            return

        # Extract current device info
        current_device_id = tx_metadata.get("device_id")
        current_browser = tx_metadata.get("browser")
        current_os = tx_metadata.get("os")
        current_ip = tx_metadata.get("ip_address")
        current_user_agent = tx_metadata.get("user_agent")

        context["device_info_available"] = True
        context["current_device_id"] = current_device_id
        context["current_browser"] = current_browser
        context["current_os"] = current_os
        context["current_ip"] = current_ip

        # Get historical device sessions for this account (last 90 days)
        now = datetime.datetime.utcnow()
        ninety_days_ago = (now - datetime.timedelta(days=90)).isoformat()

        historical_sessions = self.db.query(DeviceSession).filter(
            DeviceSession.account_id == account_id,
            DeviceSession.timestamp > ninety_days_ago
        ).order_by(DeviceSession.timestamp.desc()).all()

        if not historical_sessions:
            # No historical device data - first transaction or new tracking
            context["is_new_device"] = True
            context["device_history_count"] = 0
            context["device_mismatch"] = False
            return

        context["device_history_count"] = len(historical_sessions)

        # Check if current device has been seen before
        device_seen_before = False
        matching_device = None

        if current_device_id:
            for session in historical_sessions:
                if session.device_id == current_device_id:
                    device_seen_before = True
                    matching_device = session
                    break

        context["device_seen_before"] = device_seen_before
        context["is_new_device"] = not device_seen_before

        # Analyze device mismatches
        mismatches = []

        # Get most common device attributes from history
        device_ids = [s.device_id for s in historical_sessions if s.device_id]
        browsers = [s.browser for s in historical_sessions if s.browser]
        os_list = [s.os for s in historical_sessions if s.os]
        ips = [s.ip_address for s in historical_sessions if s.ip_address]

        # Check device ID mismatch
        if current_device_id and device_ids:
            if current_device_id not in device_ids:
                mismatches.append({
                    "attribute": "device_id",
                    "current": current_device_id,
                    "expected": device_ids[0] if device_ids else None,
                    "severity": "high"
                })

        # Check browser mismatch
        if current_browser and browsers:
            # Get most common browser
            from collections import Counter
            browser_counts = Counter(browsers)
            most_common_browser = browser_counts.most_common(1)[0][0]

            if current_browser != most_common_browser:
                # Check if this browser has been used before
                if current_browser not in browsers:
                    mismatches.append({
                        "attribute": "browser",
                        "current": current_browser,
                        "expected": most_common_browser,
                        "severity": "medium"
                    })

        # Check OS mismatch
        if current_os and os_list:
            from collections import Counter
            os_counts = Counter(os_list)
            most_common_os = os_counts.most_common(1)[0][0]

            if current_os != most_common_os:
                if current_os not in os_list:
                    mismatches.append({
                        "attribute": "os",
                        "current": current_os,
                        "expected": most_common_os,
                        "severity": "high"
                    })

        # Check IP address mismatch (new IP)
        if current_ip and ips:
            if current_ip not in ips:
                # New IP address - check how many unique IPs historically
                unique_ips = len(set(ips))
                context["unique_ips_historical"] = unique_ips

                # If user typically uses 1-2 IPs, a new one is more suspicious
                if unique_ips <= 2:
                    mismatches.append({
                        "attribute": "ip_address",
                        "current": current_ip,
                        "expected": ips[0] if ips else None,
                        "severity": "medium"
                    })

        context["device_mismatches"] = mismatches
        context["device_mismatch"] = len(mismatches) > 0
        context["device_mismatch_count"] = len(mismatches)

        # Calculate device mismatch severity score
        if mismatches:
            severity_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            max_mismatch_severity = max(
                (m["severity"] for m in mismatches),
                key=lambda s: severity_scores.get(s, 0)
            )
            context["device_mismatch_max_severity"] = max_mismatch_severity

        # Check if device has been flagged as suspicious
        if matching_device and matching_device.flagged_as_suspicious:
            context["device_flagged_suspicious"] = True
            context["device_suspicious_reason"] = matching_device.suspicious_reason
        else:
            context["device_flagged_suspicious"] = False

        # Calculate time since last seen (for known devices)
        if matching_device:
            last_seen_time = datetime.datetime.fromisoformat(matching_device.last_seen)
            hours_since_last_seen = (now - last_seen_time).total_seconds() / 3600
            context["hours_since_device_last_seen"] = hours_since_last_seen
            context["device_session_count"] = matching_device.session_count
            context["device_is_trusted"] = matching_device.is_trusted_device

    def _add_vpn_proxy_context(self, context: Dict[str, Any],
                                transaction: Dict[str, Any]) -> None:
        """
        Add VPN/proxy detection context for fraud detection.

        Flags transactions from masked IP addresses (VPN, proxy, Tor, datacenter IPs).

        Args:
            context: Context dictionary to update
            transaction: Transaction data
        """
        # Extract IP address from transaction metadata
        tx_metadata = transaction.get("tx_metadata") or transaction.get("metadata")
        if tx_metadata and isinstance(tx_metadata, str):
            try:
                tx_metadata = json.loads(tx_metadata)
            except json.JSONDecodeError:
                tx_metadata = {}

        if not tx_metadata:
            context["vpn_proxy_check_available"] = False
            return

        # Get current IP address
        current_ip = tx_metadata.get("ip_address")

        if not current_ip:
            context["vpn_proxy_check_available"] = False
            return

        context["vpn_proxy_check_available"] = True
        context["transaction_ip"] = current_ip

        # Initialize VPN/proxy flags
        context["is_vpn_or_proxy"] = False
        context["vpn_proxy_matches"] = []

        # Check against VPN/proxy IP database
        # 1. Check for exact IP match
        exact_matches = self.db.query(VPNProxyIP).filter(
            VPNProxyIP.status == "active",
            VPNProxyIP.ip_address == current_ip
        ).all()

        # 2. Check for subnet/range matches
        # Note: For production, you'd want proper CIDR matching using ipaddress module
        # This is a simplified check
        subnet_matches = self.db.query(VPNProxyIP).filter(
            VPNProxyIP.status == "active",
            VPNProxyIP.subnet.isnot(None)
        ).all()

        # Simple subnet checking (in production, use ipaddress.ip_address and ip_network)
        range_matches = []
        for entry in subnet_matches:
            if entry.subnet and current_ip.startswith(entry.subnet.split('/')[0].rsplit('.', 1)[0]):
                range_matches.append(entry)

        all_matches = exact_matches + range_matches

        # Check metadata for VPN/proxy indicators
        # Some detection services add flags to metadata
        vpn_detected = tx_metadata.get("is_vpn", False)
        proxy_detected = tx_metadata.get("is_proxy", False)
        tor_detected = tx_metadata.get("is_tor", False)
        datacenter_detected = tx_metadata.get("is_datacenter", False)
        hosting_detected = tx_metadata.get("is_hosting", False)

        metadata_indicators = []
        if vpn_detected:
            metadata_indicators.append("vpn")
        if proxy_detected:
            metadata_indicators.append("proxy")
        if tor_detected:
            metadata_indicators.append("tor")
        if datacenter_detected:
            metadata_indicators.append("datacenter")
        if hosting_detected:
            metadata_indicators.append("hosting")

        context["metadata_vpn_proxy_indicators"] = metadata_indicators

        # Process database matches
        if all_matches:
            context["is_vpn_or_proxy"] = True
            context["vpn_proxy_matches"] = [
                {
                    "service_type": entry.service_type,
                    "service_name": entry.service_name,
                    "provider": entry.provider,
                    "risk_level": entry.risk_level,
                    "is_residential_proxy": entry.is_residential_proxy,
                    "is_mobile_proxy": entry.is_mobile_proxy,
                    "confidence": entry.confidence,
                    "country": entry.country,
                    "source": entry.source
                }
                for entry in all_matches
            ]

            # Get highest risk level
            risk_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            max_risk = max(
                (entry.risk_level for entry in all_matches),
                key=lambda r: risk_order.get(r, 0)
            )
            context["vpn_proxy_max_risk_level"] = max_risk

            # Get highest confidence score
            max_confidence = max(entry.confidence for entry in all_matches)
            context["vpn_proxy_max_confidence"] = max_confidence

            # Identify service types detected
            service_types = list(set(entry.service_type for entry in all_matches if entry.service_type))
            context["vpn_proxy_service_types"] = service_types

            # Check for residential/mobile proxies (harder to detect, more sophisticated)
            has_residential = any(entry.is_residential_proxy for entry in all_matches)
            has_mobile = any(entry.is_mobile_proxy for entry in all_matches)
            context["is_residential_proxy"] = has_residential
            context["is_mobile_proxy"] = has_mobile

            context["vpn_proxy_match_count"] = len(all_matches)

        # Check metadata indicators even if no database match
        elif metadata_indicators:
            context["is_vpn_or_proxy"] = True
            context["vpn_proxy_detection_source"] = "metadata"
            context["vpn_proxy_service_types"] = metadata_indicators

        # Additional context from metadata
        if tx_metadata.get("connection_type"):
            context["connection_type"] = tx_metadata.get("connection_type")

        # ISP information (can help identify datacenter/hosting IPs)
        if tx_metadata.get("isp"):
            context["isp"] = tx_metadata.get("isp")

            # Common datacenter/hosting ISP indicators
            datacenter_keywords = ["amazon", "aws", "google cloud", "azure", "digitalocean",
                                   "linode", "ovh", "hetzner", "vultr", "rackspace"]
            isp_lower = tx_metadata.get("isp", "").lower()

            is_datacenter_isp = any(keyword in isp_lower for keyword in datacenter_keywords)
            if is_datacenter_isp and not context["is_vpn_or_proxy"]:
                context["is_vpn_or_proxy"] = True
                context["vpn_proxy_detection_source"] = "datacenter_isp"
                context["vpn_proxy_service_types"] = ["datacenter"]
                context["vpn_proxy_max_risk_level"] = "medium"

    def _add_geolocation_context(self, context: Dict[str, Any],
                                  account_id: str,
                                  transaction: Dict[str, Any]) -> None:
        """
        Add geo-location fraud detection context.

        Identifies transactions from unusual or high-risk geolocations by:
        - Checking against high-risk countries/cities database
        - Analyzing user's historical location patterns
        - Detecting impossible travel (e.g., US then China in 1 hour)

        Args:
            context: Context dictionary to update
            account_id: Account ID
            transaction: Transaction data
        """
        # Extract location from transaction metadata
        tx_metadata = transaction.get("tx_metadata") or transaction.get("metadata")
        if tx_metadata and isinstance(tx_metadata, str):
            try:
                tx_metadata = json.loads(tx_metadata)
            except json.JSONDecodeError:
                tx_metadata = {}

        if not tx_metadata:
            context["geolocation_check_available"] = False
            return

        # Get current location info
        current_country = tx_metadata.get("country") or tx_metadata.get("country_code")
        current_city = tx_metadata.get("city")
        current_region = tx_metadata.get("region") or tx_metadata.get("state")
        current_continent = tx_metadata.get("continent")
        current_ip = tx_metadata.get("ip_address")
        current_lat = tx_metadata.get("latitude")
        current_lon = tx_metadata.get("longitude")

        if not current_country:
            context["geolocation_check_available"] = False
            return

        context["geolocation_check_available"] = True
        context["transaction_country"] = current_country
        context["transaction_city"] = current_city
        context["transaction_region"] = current_region

        # Initialize flags
        context["is_high_risk_location"] = False
        context["high_risk_location_matches"] = []

        # 1. Check against high-risk locations database
        # Check country-level match
        country_matches = self.db.query(HighRiskLocation).filter(
            HighRiskLocation.status == "active",
            HighRiskLocation.country_code == current_country.upper()[:2]
        ).all()

        # Check city-level match (more specific)
        city_matches = []
        if current_city:
            city_matches = self.db.query(HighRiskLocation).filter(
                HighRiskLocation.status == "active",
                HighRiskLocation.city == current_city
            ).all()

        all_location_matches = country_matches + city_matches

        if all_location_matches:
            context["is_high_risk_location"] = True
            context["high_risk_location_matches"] = [
                {
                    "location_type": "city" if match.city else "country",
                    "country_code": match.country_code,
                    "country_name": match.country_name,
                    "city": match.city,
                    "risk_level": match.risk_level,
                    "risk_category": match.risk_category,
                    "risk_score": match.risk_score,
                    "is_sanctioned": match.is_sanctioned,
                    "is_embargoed": match.is_embargoed,
                    "has_high_fraud_rate": match.has_high_fraud_rate,
                    "has_high_cybercrime_rate": match.has_high_cybercrime_rate,
                    "requires_manual_review": match.requires_manual_review,
                    "requires_enhanced_verification": match.requires_enhanced_verification,
                    "block_by_default": match.block_by_default,
                    "reason": match.reason
                }
                for match in all_location_matches
            ]

            # Get highest risk level
            risk_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            max_risk = max(
                (match.risk_level for match in all_location_matches),
                key=lambda r: risk_order.get(r, 0)
            )
            context["location_max_risk_level"] = max_risk

            # Get highest risk score
            max_risk_score = max(match.risk_score for match in all_location_matches)
            context["location_max_risk_score"] = max_risk_score

            # Check for specific risk types
            context["location_is_sanctioned"] = any(m.is_sanctioned for m in all_location_matches)
            context["location_is_embargoed"] = any(m.is_embargoed for m in all_location_matches)
            context["location_has_high_fraud_rate"] = any(m.has_high_fraud_rate for m in all_location_matches)

            # Action recommendations
            context["location_requires_manual_review"] = any(m.requires_manual_review for m in all_location_matches)
            context["location_requires_enhanced_verification"] = any(m.requires_enhanced_verification for m in all_location_matches)
            context["location_block_by_default"] = any(m.block_by_default for m in all_location_matches)

        # 2. Analyze historical location patterns
        now = datetime.datetime.utcnow()
        ninety_days_ago = (now - datetime.timedelta(days=90)).isoformat()

        # Get historical device sessions with location data (last 90 days)
        historical_sessions = self.db.query(DeviceSession).filter(
            DeviceSession.account_id == account_id,
            DeviceSession.timestamp > ninety_days_ago,
            DeviceSession.ip_country.isnot(None)
        ).order_by(DeviceSession.timestamp.desc()).all()

        if historical_sessions:
            # Get unique countries from history
            historical_countries = [s.ip_country for s in historical_sessions if s.ip_country]
            unique_countries = list(set(historical_countries))

            context["historical_countries_count"] = len(unique_countries)
            context["historical_countries"] = unique_countries

            # Check if current country is new
            is_new_country = current_country.upper()[:2] not in [c.upper()[:2] for c in unique_countries]
            context["is_new_country"] = is_new_country

            # If mostly from one country, flag deviation
            if historical_countries:
                from collections import Counter
                country_counts = Counter(historical_countries)
                most_common_country, count = country_counts.most_common(1)[0]
                primary_country_percentage = (count / len(historical_countries)) * 100

                context["primary_country"] = most_common_country
                context["primary_country_percentage"] = primary_country_percentage

                # If 80%+ transactions from one country, current location elsewhere is suspicious
                if primary_country_percentage >= 80:
                    if current_country.upper()[:2] != most_common_country.upper()[:2]:
                        context["deviates_from_primary_country"] = True
                    else:
                        context["deviates_from_primary_country"] = False
                else:
                    context["deviates_from_primary_country"] = False

            # 3. Impossible travel detection
            # Check if there's a recent transaction from a different location
            recent_sessions = [s for s in historical_sessions if s.ip_country and s.ip_city]

            if recent_sessions and current_lat and current_lon:
                # Get most recent session
                last_session = recent_sessions[0]

                # Extract last location coordinates from metadata if available
                try:
                    last_session_metadata = json.loads(last_session.user_agent) if last_session.user_agent else {}
                    last_lat = last_session_metadata.get("latitude")
                    last_lon = last_session_metadata.get("longitude")
                    last_country = last_session.ip_country
                    last_city = last_session.ip_city

                    if last_lat and last_lon:
                        # Calculate time difference
                        last_time = datetime.datetime.fromisoformat(last_session.timestamp)
                        current_time = datetime.datetime.fromisoformat(
                            transaction.get("timestamp", now.isoformat())
                        )
                        time_diff_hours = (current_time - last_time).total_seconds() / 3600

                        # Calculate distance (simple Haversine formula)
                        import math
                        lat1, lon1 = float(last_lat), float(last_lon)
                        lat2, lon2 = float(current_lat), float(current_lon)

                        # Radius of Earth in km
                        R = 6371

                        # Convert to radians
                        lat1_rad = math.radians(lat1)
                        lat2_rad = math.radians(lat2)
                        delta_lat = math.radians(lat2 - lat1)
                        delta_lon = math.radians(lon2 - lon1)

                        # Haversine formula
                        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
                        c = 2 * math.asin(math.sqrt(a))
                        distance_km = R * c

                        context["distance_from_last_transaction_km"] = distance_km
                        context["hours_since_last_transaction"] = time_diff_hours

                        # Check for impossible travel
                        # Average commercial flight speed ~800 km/h
                        # Allow for 900 km/h to account for time zones, etc.
                        max_possible_speed = 900  # km/h

                        if time_diff_hours > 0:
                            required_speed = distance_km / time_diff_hours
                            context["required_travel_speed_kmh"] = required_speed

                            # Flag if speed would need to exceed max possible
                            if required_speed > max_possible_speed and distance_km > 100:
                                context["impossible_travel_detected"] = True
                                context["impossible_travel_details"] = {
                                    "from_location": f"{last_city}, {last_country}",
                                    "to_location": f"{current_city}, {current_country}",
                                    "distance_km": distance_km,
                                    "time_hours": time_diff_hours,
                                    "required_speed_kmh": required_speed,
                                    "max_possible_speed_kmh": max_possible_speed
                                }
                            else:
                                context["impossible_travel_detected"] = False
                        else:
                            context["impossible_travel_detected"] = False

                except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
                    # If we can't parse metadata or calculate distance, skip impossible travel check
                    pass
        else:
            # No historical location data
            context["is_new_country"] = True
            context["historical_countries_count"] = 0

    def _add_behavioral_biometric_context(self, context: Dict[str, Any],
                                           account_id: str,
                                           transaction: Dict[str, Any]) -> None:
        """
        Add behavioral biometrics fraud detection context.

        Monitors user interaction patterns (typing speed, mouse movement, etc.)
        and detects deviations from typical behavior indicating account takeover.

        Args:
            context: Context dictionary to update
            account_id: Account ID
            transaction: Transaction data
        """
        # Extract behavioral data from transaction metadata
        tx_metadata = transaction.get("tx_metadata") or transaction.get("metadata")
        if tx_metadata and isinstance(tx_metadata, str):
            try:
                tx_metadata = json.loads(tx_metadata)
            except json.JSONDecodeError:
                tx_metadata = {}

        if not tx_metadata:
            context["behavioral_biometric_check_available"] = False
            return

        # Extract behavioral metrics from metadata
        behavioral_data = tx_metadata.get("behavioral_data") or tx_metadata.get("biometrics")

        if not behavioral_data:
            context["behavioral_biometric_check_available"] = False
            return

        context["behavioral_biometric_check_available"] = True

        # Extract current session behavioral metrics
        current_typing_speed = behavioral_data.get("typing_speed_wpm")
        current_mouse_speed = behavioral_data.get("mouse_speed_px_sec")
        current_key_hold_time = behavioral_data.get("key_hold_time_ms")
        current_key_interval = behavioral_data.get("key_interval_ms")
        current_mouse_smoothness = behavioral_data.get("mouse_smoothness")
        current_click_accuracy = behavioral_data.get("click_accuracy")
        current_actions_per_min = behavioral_data.get("actions_per_minute")
        current_paste_frequency = behavioral_data.get("paste_frequency")
        current_uses_autofill = behavioral_data.get("uses_autofill", False)
        current_uses_shortcuts = behavioral_data.get("uses_shortcuts", False)

        # Store current metrics in context
        context["current_behavioral_metrics"] = {
            "typing_speed_wpm": current_typing_speed,
            "mouse_speed_px_sec": current_mouse_speed,
            "key_hold_time_ms": current_key_hold_time,
            "key_interval_ms": current_key_interval,
            "mouse_smoothness": current_mouse_smoothness,
            "click_accuracy": current_click_accuracy,
            "actions_per_minute": current_actions_per_min,
            "paste_frequency": current_paste_frequency,
            "uses_autofill": current_uses_autofill,
            "uses_shortcuts": current_uses_shortcuts
        }

        # Get historical behavioral baseline (last 90 days of normal behavior)
        now = datetime.datetime.utcnow()
        ninety_days_ago = (now - datetime.timedelta(days=90)).isoformat()

        # Get baseline behavioral profiles (excluding anomalous ones)
        baseline_profiles = self.db.query(BehavioralBiometric).filter(
            BehavioralBiometric.account_id == account_id,
            BehavioralBiometric.timestamp > ninety_days_ago,
            BehavioralBiometric.is_anomalous == False,
            BehavioralBiometric.is_baseline == True
        ).all()

        if not baseline_profiles:
            # No baseline - might be new account or first time tracking
            context["has_behavioral_baseline"] = False
            context["behavioral_deviation_detected"] = False
            context["behavioral_profile_count"] = 0
            return

        context["has_behavioral_baseline"] = True
        context["behavioral_profile_count"] = len(baseline_profiles)

        # Calculate baseline averages
        typing_speeds = [p.avg_typing_speed_wpm for p in baseline_profiles if p.avg_typing_speed_wpm is not None]
        mouse_speeds = [p.avg_mouse_speed_px_sec for p in baseline_profiles if p.avg_mouse_speed_px_sec is not None]
        key_hold_times = [p.avg_key_hold_time_ms for p in baseline_profiles if p.avg_key_hold_time_ms is not None]
        key_intervals = [p.avg_key_interval_ms for p in baseline_profiles if p.avg_key_interval_ms is not None]
        mouse_smoothness_values = [p.mouse_movement_smoothness for p in baseline_profiles if p.mouse_movement_smoothness is not None]
        click_accuracies = [p.click_accuracy for p in baseline_profiles if p.click_accuracy is not None]
        actions_per_min = [p.actions_per_minute for p in baseline_profiles if p.actions_per_minute is not None]
        paste_frequencies = [p.paste_frequency for p in baseline_profiles if p.paste_frequency is not None]

        # Calculate historical patterns for autofill and shortcuts
        uses_autofill_count = sum(1 for p in baseline_profiles if p.uses_autofill)
        uses_shortcuts_count = sum(1 for p in baseline_profiles if p.uses_shortcuts)
        total_profiles = len(baseline_profiles)

        # Helper function to calculate mean and std dev
        def calc_stats(values):
            if not values:
                return None, None
            import math
            mean = sum(values) / len(values)
            if len(values) > 1:
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                std_dev = math.sqrt(variance)
            else:
                std_dev = 0
            return mean, std_dev

        # Calculate baseline statistics
        baseline_typing_mean, baseline_typing_std = calc_stats(typing_speeds)
        baseline_mouse_speed_mean, baseline_mouse_speed_std = calc_stats(mouse_speeds)
        baseline_key_hold_mean, baseline_key_hold_std = calc_stats(key_hold_times)
        baseline_key_interval_mean, baseline_key_interval_std = calc_stats(key_intervals)
        baseline_mouse_smooth_mean, baseline_mouse_smooth_std = calc_stats(mouse_smoothness_values)
        baseline_click_acc_mean, baseline_click_acc_std = calc_stats(click_accuracies)
        baseline_actions_mean, baseline_actions_std = calc_stats(actions_per_min)
        baseline_paste_mean, baseline_paste_std = calc_stats(paste_frequencies)

        # Store baseline in context
        context["behavioral_baseline"] = {
            "typing_speed_mean": baseline_typing_mean,
            "mouse_speed_mean": baseline_mouse_speed_mean,
            "key_hold_time_mean": baseline_key_hold_mean,
            "key_interval_mean": baseline_key_interval_mean,
            "mouse_smoothness_mean": baseline_mouse_smooth_mean,
            "click_accuracy_mean": baseline_click_acc_mean,
            "actions_per_minute_mean": baseline_actions_mean,
            "paste_frequency_mean": baseline_paste_mean,
            "uses_autofill_percentage": (uses_autofill_count / total_profiles) * 100 if total_profiles > 0 else 0,
            "uses_shortcuts_percentage": (uses_shortcuts_count / total_profiles) * 100 if total_profiles > 0 else 0
        }

        # Detect behavioral deviations
        deviations = []
        deviation_threshold = 2.0  # Number of standard deviations

        # Check typing speed deviation
        if current_typing_speed and baseline_typing_mean and baseline_typing_std:
            if baseline_typing_std > 0:
                typing_deviation = abs(current_typing_speed - baseline_typing_mean) / baseline_typing_std
                if typing_deviation > deviation_threshold:
                    deviations.append({
                        "metric": "typing_speed",
                        "current": current_typing_speed,
                        "baseline_mean": baseline_typing_mean,
                        "std_deviations": typing_deviation,
                        "severity": "high" if typing_deviation > 3.0 else "medium"
                    })

        # Check mouse speed deviation
        if current_mouse_speed and baseline_mouse_speed_mean and baseline_mouse_speed_std:
            if baseline_mouse_speed_std > 0:
                mouse_deviation = abs(current_mouse_speed - baseline_mouse_speed_mean) / baseline_mouse_speed_std
                if mouse_deviation > deviation_threshold:
                    deviations.append({
                        "metric": "mouse_speed",
                        "current": current_mouse_speed,
                        "baseline_mean": baseline_mouse_speed_mean,
                        "std_deviations": mouse_deviation,
                        "severity": "medium"
                    })

        # Check key hold time deviation
        if current_key_hold_time and baseline_key_hold_mean and baseline_key_hold_std:
            if baseline_key_hold_std > 0:
                key_hold_deviation = abs(current_key_hold_time - baseline_key_hold_mean) / baseline_key_hold_std
                if key_hold_deviation > deviation_threshold:
                    deviations.append({
                        "metric": "key_hold_time",
                        "current": current_key_hold_time,
                        "baseline_mean": baseline_key_hold_mean,
                        "std_deviations": key_hold_deviation,
                        "severity": "high" if key_hold_deviation > 3.0 else "medium"
                    })

        # Check key interval deviation
        if current_key_interval and baseline_key_interval_mean and baseline_key_interval_std:
            if baseline_key_interval_std > 0:
                key_interval_deviation = abs(current_key_interval - baseline_key_interval_mean) / baseline_key_interval_std
                if key_interval_deviation > deviation_threshold:
                    deviations.append({
                        "metric": "key_interval",
                        "current": current_key_interval,
                        "baseline_mean": baseline_key_interval_mean,
                        "std_deviations": key_interval_deviation,
                        "severity": "high" if key_interval_deviation > 3.0 else "medium"
                    })

        # Check mouse smoothness deviation
        if current_mouse_smoothness and baseline_mouse_smooth_mean and baseline_mouse_smooth_std:
            if baseline_mouse_smooth_std > 0:
                smoothness_deviation = abs(current_mouse_smoothness - baseline_mouse_smooth_mean) / baseline_mouse_smooth_std
                if smoothness_deviation > deviation_threshold:
                    deviations.append({
                        "metric": "mouse_smoothness",
                        "current": current_mouse_smoothness,
                        "baseline_mean": baseline_mouse_smooth_mean,
                        "std_deviations": smoothness_deviation,
                        "severity": "medium"
                    })

        # Check click accuracy deviation
        if current_click_accuracy and baseline_click_acc_mean and baseline_click_acc_std:
            if baseline_click_acc_std > 0:
                accuracy_deviation = abs(current_click_accuracy - baseline_click_acc_mean) / baseline_click_acc_std
                if accuracy_deviation > deviation_threshold:
                    deviations.append({
                        "metric": "click_accuracy",
                        "current": current_click_accuracy,
                        "baseline_mean": baseline_click_acc_mean,
                        "std_deviations": accuracy_deviation,
                        "severity": "medium"
                    })

        # Check autofill/shortcuts usage changes
        autofill_percentage = context["behavioral_baseline"]["uses_autofill_percentage"]
        shortcuts_percentage = context["behavioral_baseline"]["uses_shortcuts_percentage"]

        # If user always uses autofill (80%+) but suddenly doesn't, flag it
        if autofill_percentage >= 80 and not current_uses_autofill:
            deviations.append({
                "metric": "autofill_usage",
                "current": False,
                "baseline_percentage": autofill_percentage,
                "severity": "medium"
            })

        # If user never uses autofill (< 20%) but suddenly does, flag it
        if autofill_percentage <= 20 and current_uses_autofill:
            deviations.append({
                "metric": "autofill_usage",
                "current": True,
                "baseline_percentage": autofill_percentage,
                "severity": "low"
            })

        # Similar for shortcuts
        if shortcuts_percentage >= 80 and not current_uses_shortcuts:
            deviations.append({
                "metric": "keyboard_shortcuts",
                "current": False,
                "baseline_percentage": shortcuts_percentage,
                "severity": "medium"
            })

        # Store deviation results
        context["behavioral_deviations"] = deviations
        context["behavioral_deviation_detected"] = len(deviations) > 0
        context["behavioral_deviation_count"] = len(deviations)

        if deviations:
            # Calculate overall anomaly score
            severity_scores = {"low": 0.3, "medium": 0.6, "high": 0.9}
            anomaly_scores = [severity_scores.get(d.get("severity", "medium"), 0.5) for d in deviations]
            overall_anomaly_score = sum(anomaly_scores) / len(anomaly_scores) if anomaly_scores else 0
            context["behavioral_anomaly_score"] = overall_anomaly_score

            # Get max severity
            severity_order = {"low": 1, "medium": 2, "high": 3}
            max_severity = max(
                (d.get("severity", "medium") for d in deviations),
                key=lambda s: severity_order.get(s, 0)
            )
            context["behavioral_max_severity"] = max_severity

            # Flag high-risk behavioral changes
            high_severity_count = sum(1 for d in deviations if d.get("severity") == "high")
            context["behavioral_high_risk"] = high_severity_count >= 2  # 2+ high severity deviations
        else:
            context["behavioral_anomaly_score"] = 0.0
            context["behavioral_high_risk"] = False

    def _add_recipient_relationship_context(self, context: Dict[str, Any],
                                             account_id: str,
                                             transaction: Dict[str, Any]) -> None:
        """
        Add recipient relationship analysis for fraud detection.

        Evaluates:
        - If recipient is a new contact (first time transacting)
        - Time since last transaction with this recipient
        - Transaction frequency with recipient
        - Dormant relationship activation (e.g., no contact for 12 months, suddenly active)

        Args:
            context: Context dictionary to update
            account_id: Account ID
            transaction: Transaction data
        """
        counterparty_id = transaction.get("counterparty_id")

        if not counterparty_id:
            context["recipient_relationship_check_available"] = False
            return

        context["recipient_relationship_check_available"] = True
        context["recipient_id"] = counterparty_id

        now = datetime.datetime.utcnow()
        current_tx_time = datetime.datetime.fromisoformat(
            transaction.get("timestamp", now.isoformat())
        )

        # Get all previous transactions with this counterparty
        previous_txs = self.db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.counterparty_id == counterparty_id,
            Transaction.timestamp < current_tx_time.isoformat()
        ).order_by(Transaction.timestamp.desc()).all()

        # Check if this is a new recipient
        is_new_recipient = len(previous_txs) == 0
        context["is_new_recipient"] = is_new_recipient
        context["previous_transaction_count"] = len(previous_txs)

        if is_new_recipient:
            # New recipient - no historical relationship
            context["days_since_last_transaction"] = None
            context["is_dormant_relationship"] = False
            context["relationship_status"] = "new"
            return

        # Calculate time since last transaction with this recipient
        last_tx = previous_txs[0]  # Most recent
        last_tx_time = datetime.datetime.fromisoformat(last_tx.timestamp)
        time_since_last = current_tx_time - last_tx_time

        days_since_last = time_since_last.days
        hours_since_last = time_since_last.total_seconds() / 3600

        context["days_since_last_transaction"] = days_since_last
        context["hours_since_last_transaction"] = hours_since_last
        context["last_transaction_date"] = last_tx.timestamp
        context["last_transaction_amount"] = last_tx.amount

        # Analyze transaction frequency with this recipient
        if len(previous_txs) > 1:
            # Calculate average time between transactions
            time_gaps = []
            for i in range(len(previous_txs) - 1):
                tx1_time = datetime.datetime.fromisoformat(previous_txs[i].timestamp)
                tx2_time = datetime.datetime.fromisoformat(previous_txs[i + 1].timestamp)
                gap_days = (tx1_time - tx2_time).days
                time_gaps.append(gap_days)

            if time_gaps:
                avg_gap_days = sum(time_gaps) / len(time_gaps)
                context["avg_days_between_transactions"] = avg_gap_days
                context["transaction_frequency"] = "regular" if avg_gap_days <= 30 else "irregular"

                # Calculate standard deviation of gaps
                import math
                if len(time_gaps) > 1:
                    variance = sum((x - avg_gap_days) ** 2 for x in time_gaps) / len(time_gaps)
                    std_dev = math.sqrt(variance)
                    context["transaction_gap_std_dev"] = std_dev

                    # Check if current gap is anomalous
                    if std_dev > 0:
                        gap_deviation = abs(days_since_last - avg_gap_days) / std_dev
                        context["current_gap_deviation"] = gap_deviation

                        # Flag if gap is significantly longer than normal
                        if gap_deviation > 2.0 and days_since_last > avg_gap_days:
                            context["unusually_long_gap"] = True
                            context["gap_deviation_std"] = gap_deviation
                        else:
                            context["unusually_long_gap"] = False
                    else:
                        context["unusually_long_gap"] = False
                else:
                    context["unusually_long_gap"] = False
        else:
            # Only one previous transaction
            context["avg_days_between_transactions"] = days_since_last
            context["transaction_frequency"] = "first_repeat"

        # Classify relationship based on transaction history
        total_txs_with_recipient = len(previous_txs) + 1  # Include current

        if total_txs_with_recipient == 2:
            relationship_status = "new_repeat"  # Second transaction ever
        elif days_since_last <= 30:
            relationship_status = "active"  # Active relationship (< 30 days)
        elif days_since_last <= 90:
            relationship_status = "recent"  # Recent contact (30-90 days)
        elif days_since_last <= 180:
            relationship_status = "inactive"  # Inactive (3-6 months)
        else:
            relationship_status = "dormant"  # Dormant (6+ months)

        context["relationship_status"] = relationship_status

        # Flag dormant relationships (high fraud risk)
        # Dormant = no contact for 6+ months (180 days)
        is_dormant = days_since_last >= 180
        context["is_dormant_relationship"] = is_dormant

        if is_dormant:
            context["dormant_days"] = days_since_last
            context["dormant_risk_level"] = "critical" if days_since_last >= 365 else "high"

        # Analyze amount patterns with this recipient
        previous_amounts = [tx.amount for tx in previous_txs]
        if previous_amounts:
            avg_amount = sum(previous_amounts) / len(previous_amounts)
            max_amount = max(previous_amounts)
            min_amount = min(previous_amounts)

            context["avg_transaction_amount_with_recipient"] = avg_amount
            context["max_transaction_amount_with_recipient"] = max_amount
            context["min_transaction_amount_with_recipient"] = min_amount

            # Check if current amount is unusual for this recipient
            current_amount = transaction.get("amount", 0)

            if len(previous_amounts) > 1:
                import math
                variance = sum((x - avg_amount) ** 2 for x in previous_amounts) / len(previous_amounts)
                std_dev = math.sqrt(variance)

                if std_dev > 0:
                    amount_deviation = abs(current_amount - avg_amount) / std_dev
                    context["amount_deviation_with_recipient"] = amount_deviation

                    # Flag if amount is significantly different
                    if amount_deviation > 2.0:
                        context["unusual_amount_for_recipient"] = True
                        if current_amount > avg_amount:
                            context["unusual_amount_direction"] = "higher_than_normal"
                        else:
                            context["unusual_amount_direction"] = "lower_than_normal"
                    else:
                        context["unusual_amount_for_recipient"] = False
                else:
                    context["unusual_amount_for_recipient"] = False

            # Check if current amount exceeds previous maximum
            if current_amount > max_amount:
                context["exceeds_previous_max"] = True
                context["max_amount_exceeded_by"] = current_amount - max_amount
                context["max_amount_increase_percentage"] = ((current_amount - max_amount) / max_amount * 100) if max_amount > 0 else 0
            else:
                context["exceeds_previous_max"] = False

        # Calculate relationship metrics
        # Get first transaction with this recipient
        first_tx = previous_txs[-1] if previous_txs else None
        if first_tx:
            first_tx_time = datetime.datetime.fromisoformat(first_tx.timestamp)
            relationship_age_days = (current_tx_time - first_tx_time).days
            context["relationship_age_days"] = relationship_age_days

            # Calculate transaction frequency (transactions per month)
            if relationship_age_days > 0:
                txs_per_month = (total_txs_with_recipient / relationship_age_days) * 30
                context["transactions_per_month_with_recipient"] = txs_per_month
            else:
                context["transactions_per_month_with_recipient"] = 0

        # Flag high-risk scenarios
        risk_flags = []

        # 1. Dormant relationship suddenly active
        if is_dormant:
            risk_flags.append("dormant_relationship_reactivated")

        # 2. New recipient with large transaction
        if is_new_recipient and transaction.get("amount", 0) > 10000:
            risk_flags.append("new_recipient_large_amount")

        # 3. Unusual amount for this recipient
        if context.get("unusual_amount_for_recipient"):
            risk_flags.append("unusual_amount_for_recipient")

        # 4. Exceeds previous maximum by significant margin
        if context.get("exceeds_previous_max"):
            if context.get("max_amount_increase_percentage", 0) > 50:  # 50% increase
                risk_flags.append("significant_amount_increase")

        # 5. Very long gap (unusually long)
        if context.get("unusually_long_gap"):
            risk_flags.append("unusually_long_transaction_gap")

        context["recipient_relationship_risk_flags"] = risk_flags
        context["recipient_relationship_risk_count"] = len(risk_flags)
        context["recipient_relationship_high_risk"] = len(risk_flags) >= 2

    def _add_social_trust_score_context(self, context: Dict[str, Any],
                                         account_id: str,
                                         transaction: Dict[str, Any]) -> None:
        """
        Add social trust score for recipient fraud detection.

        Calculates a comprehensive trust score (0-100) based on multiple factors:
        - Presence in beneficiary/contact list
        - Verification status
        - Transaction history length
        - Transaction frequency
        - Relationship age
        - Social signals (mutual connections, endorsements)

        Args:
            context: Context dictionary to update
            account_id: Account ID
            transaction: Transaction data
        """
        counterparty_id = transaction.get("counterparty_id")

        if not counterparty_id:
            context["social_trust_score_available"] = False
            return

        context["social_trust_score_available"] = True

        # Initialize trust score components
        trust_factors = {}
        total_score = 0
        max_possible_score = 100

        # Factor 1: Beneficiary Status (25 points)
        beneficiary = self.db.query(Beneficiary).filter(
            Beneficiary.account_id == account_id,
            Beneficiary.counterparty_id == counterparty_id,
            Beneficiary.status == "active"
        ).first()

        if beneficiary:
            beneficiary_score = 0

            # Base points for being in beneficiary list
            beneficiary_score += 10
            trust_factors["in_beneficiary_list"] = True

            # Verification status
            if beneficiary.verified:
                beneficiary_score += 10
                trust_factors["beneficiary_verified"] = True
            else:
                trust_factors["beneficiary_verified"] = False

            # Not flagged as suspicious
            if not beneficiary.flagged_as_suspicious:
                beneficiary_score += 5
                trust_factors["not_flagged_suspicious"] = True
            else:
                trust_factors["not_flagged_suspicious"] = False
                beneficiary_score -= 5  # Penalty for suspicious flag

            trust_factors["beneficiary_score"] = beneficiary_score
            total_score += beneficiary_score
        else:
            trust_factors["in_beneficiary_list"] = False
            trust_factors["beneficiary_verified"] = False
            trust_factors["beneficiary_score"] = 0

        # Factor 2: Transaction History (30 points)
        now = datetime.datetime.utcnow()
        all_txs = self.db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.counterparty_id == counterparty_id
        ).order_by(Transaction.timestamp.desc()).all()

        transaction_history_score = 0

        if all_txs:
            # Number of previous transactions (up to 15 points)
            tx_count = len(all_txs)
            if tx_count >= 10:
                transaction_history_score += 15
            elif tx_count >= 5:
                transaction_history_score += 10
            elif tx_count >= 2:
                transaction_history_score += 5
            else:  # 1 transaction
                transaction_history_score += 2

            trust_factors["transaction_count"] = tx_count

            # Relationship age (up to 10 points)
            first_tx = all_txs[-1]
            first_tx_time = datetime.datetime.fromisoformat(first_tx.timestamp)
            relationship_age_days = (now - first_tx_time).days

            if relationship_age_days >= 365:  # 1+ years
                transaction_history_score += 10
            elif relationship_age_days >= 180:  # 6+ months
                transaction_history_score += 7
            elif relationship_age_days >= 90:  # 3+ months
                transaction_history_score += 5
            elif relationship_age_days >= 30:  # 1+ month
                transaction_history_score += 3
            else:
                transaction_history_score += 1

            trust_factors["relationship_age_days"] = relationship_age_days

            # Transaction recency (up to 5 points)
            # Penalize if last transaction was too long ago
            last_tx = all_txs[0]
            last_tx_time = datetime.datetime.fromisoformat(last_tx.timestamp)
            days_since_last = (now - last_tx_time).days

            if days_since_last <= 30:  # Recent
                transaction_history_score += 5
            elif days_since_last <= 90:
                transaction_history_score += 3
            elif days_since_last <= 180:
                transaction_history_score += 1
            else:  # Dormant - no bonus, potential risk
                transaction_history_score += 0

            trust_factors["days_since_last_transaction"] = days_since_last
        else:
            # New recipient - low trust
            trust_factors["transaction_count"] = 0
            trust_factors["relationship_age_days"] = 0
            transaction_history_score = 0

        trust_factors["transaction_history_score"] = transaction_history_score
        total_score += transaction_history_score

        # Factor 3: Contact List Presence (15 points)
        # Check transaction metadata for contact list indicators
        tx_metadata = transaction.get("tx_metadata") or transaction.get("metadata")
        if tx_metadata and isinstance(tx_metadata, str):
            try:
                tx_metadata = json.loads(tx_metadata)
            except json.JSONDecodeError:
                tx_metadata = {}

        contact_score = 0

        if tx_metadata:
            # Check if recipient is in contact list
            in_contact_list = tx_metadata.get("in_contact_list", False)
            if in_contact_list:
                contact_score += 10
                trust_factors["in_contact_list"] = True
            else:
                trust_factors["in_contact_list"] = False

            # Check if recipient's contact info is saved
            has_saved_info = tx_metadata.get("has_saved_email") or tx_metadata.get("has_saved_phone")
            if has_saved_info:
                contact_score += 5
                trust_factors["has_saved_contact_info"] = True
            else:
                trust_factors["has_saved_contact_info"] = False
        else:
            trust_factors["in_contact_list"] = False
            trust_factors["has_saved_contact_info"] = False

        trust_factors["contact_score"] = contact_score
        total_score += contact_score

        # Factor 4: Social Signals (15 points)
        social_score = 0

        if tx_metadata:
            # Mutual connections
            mutual_connections = tx_metadata.get("mutual_connections", 0)
            if mutual_connections >= 5:
                social_score += 8
            elif mutual_connections >= 2:
                social_score += 5
            elif mutual_connections >= 1:
                social_score += 3

            trust_factors["mutual_connections"] = mutual_connections

            # Endorsements or references
            has_endorsements = tx_metadata.get("has_endorsements", False)
            if has_endorsements:
                social_score += 5
                trust_factors["has_endorsements"] = True
            else:
                trust_factors["has_endorsements"] = False

            # Known entity (business, verified organization)
            is_known_entity = tx_metadata.get("is_verified_business", False) or tx_metadata.get("is_registered_business", False)
            if is_known_entity:
                social_score += 2
                trust_factors["is_known_entity"] = True
            else:
                trust_factors["is_known_entity"] = False
        else:
            trust_factors["mutual_connections"] = 0
            trust_factors["has_endorsements"] = False
            trust_factors["is_known_entity"] = False

        trust_factors["social_score"] = social_score
        total_score += social_score

        # Factor 5: Transaction Pattern Consistency (15 points)
        pattern_score = 0

        if all_txs and len(all_txs) >= 3:
            # Analyze amount consistency
            amounts = [tx.amount for tx in all_txs]
            avg_amount = sum(amounts) / len(amounts)

            # Calculate coefficient of variation (std dev / mean)
            import math
            if len(amounts) > 1:
                variance = sum((x - avg_amount) ** 2 for x in amounts) / len(amounts)
                std_dev = math.sqrt(variance)

                if avg_amount > 0:
                    coefficient_of_variation = std_dev / avg_amount

                    # Lower variation = more consistent = higher trust
                    if coefficient_of_variation <= 0.3:  # Very consistent
                        pattern_score += 10
                    elif coefficient_of_variation <= 0.6:  # Moderately consistent
                        pattern_score += 6
                    elif coefficient_of_variation <= 1.0:  # Somewhat consistent
                        pattern_score += 3

                    trust_factors["amount_consistency_score"] = 10 - min(coefficient_of_variation * 10, 10)

            # Transaction frequency consistency (if we have enough data)
            if len(all_txs) >= 5:
                time_gaps = []
                for i in range(len(all_txs) - 1):
                    tx1_time = datetime.datetime.fromisoformat(all_txs[i].timestamp)
                    tx2_time = datetime.datetime.fromisoformat(all_txs[i + 1].timestamp)
                    gap_days = (tx1_time - tx2_time).days
                    time_gaps.append(gap_days)

                if time_gaps:
                    avg_gap = sum(time_gaps) / len(time_gaps)
                    gap_variance = sum((x - avg_gap) ** 2 for x in time_gaps) / len(time_gaps)
                    gap_std = math.sqrt(gap_variance)

                    if avg_gap > 0:
                        gap_cv = gap_std / avg_gap

                        # Consistent timing = higher trust
                        if gap_cv <= 0.5:  # Very regular
                            pattern_score += 5
                        elif gap_cv <= 1.0:  # Moderately regular
                            pattern_score += 3

                        trust_factors["timing_consistency_score"] = 5 - min(gap_cv * 5, 5)
        else:
            trust_factors["amount_consistency_score"] = 0
            trust_factors["timing_consistency_score"] = 0

        trust_factors["pattern_score"] = pattern_score
        total_score += pattern_score

        # Calculate final trust score (0-100)
        trust_score = min(total_score, max_possible_score)

        # Normalize to 0.0-1.0 scale as well
        trust_score_normalized = trust_score / 100.0

        # Classify trust level
        if trust_score >= 80:
            trust_level = "high"
        elif trust_score >= 60:
            trust_level = "medium_high"
        elif trust_score >= 40:
            trust_level = "medium"
        elif trust_score >= 20:
            trust_level = "low"
        else:
            trust_level = "very_low"

        # Store in context
        context["social_trust_score"] = trust_score
        context["social_trust_score_normalized"] = trust_score_normalized
        context["social_trust_level"] = trust_level
        context["social_trust_factors"] = trust_factors

        # Flag low trust recipients
        context["is_low_trust_recipient"] = trust_score < 40
        context["is_very_low_trust_recipient"] = trust_score < 20
        context["is_high_trust_recipient"] = trust_score >= 80

        # Calculate trust deficit for low trust recipients
        if trust_score < 60:
            trust_deficit = 60 - trust_score
            context["trust_deficit"] = trust_deficit
            context["requires_additional_verification"] = trust_deficit >= 20

    def _add_account_age_context(self, context: Dict[str, Any],
                                  account_id: str,
                                  transaction: Dict[str, Any]) -> None:
        """
        Add account age analysis for fraud detection.

        Analyzes account maturity and flags newly created accounts performing
        high-risk transactions. New accounts are prime targets for fraud.

        Args:
            context: Context dictionary to update
            account_id: Account ID
            transaction: Transaction data
        """
        # Get account information (already queried earlier but re-fetch for completeness)
        account = self.db.query(Account).filter(Account.account_id == account_id).first()

        if not account:
            context["account_age_check_available"] = False
            return

        context["account_age_check_available"] = True

        # Calculate account age (also calculated earlier, but ensure we have it)
        creation_date = datetime.datetime.fromisoformat(account.creation_date)
        now = datetime.datetime.utcnow()
        account_age_days = (now - creation_date).days
        account_age_hours = (now - creation_date).total_seconds() / 3600

        context["account_creation_date"] = account.creation_date
        context["account_age_days"] = account_age_days
        context["account_age_hours"] = account_age_hours

        # Classify account maturity
        if account_age_days < 1:
            account_maturity = "brand_new"  # Less than 1 day old
        elif account_age_days < 7:
            account_maturity = "very_new"  # Less than 1 week
        elif account_age_days < 30:
            account_maturity = "new"  # Less than 1 month
        elif account_age_days < 90:
            account_maturity = "young"  # Less than 3 months
        elif account_age_days < 180:
            account_maturity = "maturing"  # 3-6 months
        elif account_age_days < 365:
            account_maturity = "established"  # 6-12 months
        else:
            account_maturity = "mature"  # 1+ years

        context["account_maturity"] = account_maturity

        # Flag new accounts
        is_brand_new = account_age_days < 1
        is_very_new = account_age_days < 7
        is_new = account_age_days < 30

        context["is_brand_new_account"] = is_brand_new
        context["is_very_new_account"] = is_very_new
        context["is_new_account"] = is_new

        # Get all transactions for this account
        all_account_txs = self.db.query(Transaction).filter(
            Transaction.account_id == account_id
        ).order_by(Transaction.timestamp).all()

        total_txs = len(all_account_txs)
        context["total_account_transactions"] = total_txs

        # Calculate transaction velocity since account creation
        if account_age_days > 0:
            txs_per_day = total_txs / account_age_days
            context["transactions_per_day_since_creation"] = txs_per_day
        else:
            context["transactions_per_day_since_creation"] = total_txs  # Brand new account

        # Analyze transaction patterns for new accounts
        current_amount = transaction.get("amount", 0)
        current_direction = transaction.get("direction", "")

        # Risk flags for new accounts
        risk_flags = []

        # Flag 1: Brand new account (< 24 hours)
        if is_brand_new:
            risk_flags.append("brand_new_account")

        # Flag 2: Very new account with large transaction
        if is_very_new and current_amount > 5000:
            risk_flags.append("very_new_account_large_amount")

        # Flag 3: New account with very large transaction
        if is_new and current_amount > 10000:
            risk_flags.append("new_account_very_large_amount")

        # Flag 4: New account with high transaction velocity
        if is_new and total_txs >= 10:
            risk_flags.append("new_account_high_velocity")

        # Flag 5: Brand new account with outgoing transfer
        if is_brand_new and current_direction == "debit":
            risk_flags.append("brand_new_account_outgoing_transfer")

        # Flag 6: Very new account with international transaction
        tx_metadata = transaction.get("tx_metadata") or transaction.get("metadata")
        if tx_metadata and isinstance(tx_metadata, str):
            try:
                tx_metadata = json.loads(tx_metadata)
            except json.JSONDecodeError:
                tx_metadata = {}

        if tx_metadata:
            country = tx_metadata.get("country") or tx_metadata.get("country_code")
            if is_very_new and country and country.upper()[:2] != "US":
                risk_flags.append("very_new_account_international")

        # Analyze first transaction timing
        if all_account_txs:
            first_tx = all_account_txs[0]
            first_tx_time = datetime.datetime.fromisoformat(first_tx.timestamp)
            time_to_first_tx = (first_tx_time - creation_date).total_seconds() / 3600  # hours

            context["hours_to_first_transaction"] = time_to_first_tx

            # Flag 7: Immediate first transaction (within 1 hour of account creation)
            if time_to_first_tx < 1:
                risk_flags.append("immediate_first_transaction")

            # Flag 8: First transaction is large
            if first_tx.amount > 5000:
                risk_flags.append("first_transaction_large_amount")

        # Calculate account age vs transaction amount risk score
        # New accounts with large amounts are risky
        account_age_amount_risk = 0

        if current_amount > 0:
            # Risk increases as amount increases and account age decreases
            amount_factor = min(current_amount / 1000, 100)  # Scale amount

            if account_age_days < 1:
                age_multiplier = 10  # Extreme risk
            elif account_age_days < 7:
                age_multiplier = 5  # Very high risk
            elif account_age_days < 30:
                age_multiplier = 3  # High risk
            elif account_age_days < 90:
                age_multiplier = 2  # Moderate risk
            else:
                age_multiplier = 1  # Lower risk

            account_age_amount_risk = amount_factor * age_multiplier

        context["account_age_amount_risk_score"] = min(account_age_amount_risk, 100)

        # Classify risk level based on account age
        if is_brand_new:
            account_age_risk_level = "critical"
        elif is_very_new:
            account_age_risk_level = "high"
        elif is_new:
            account_age_risk_level = "medium"
        elif account_age_days < 90:
            account_age_risk_level = "low"
        else:
            account_age_risk_level = "minimal"

        context["account_age_risk_level"] = account_age_risk_level

        # Store risk flags
        context["account_age_risk_flags"] = risk_flags
        context["account_age_risk_flag_count"] = len(risk_flags)
        context["account_age_high_risk"] = len(risk_flags) >= 2 or is_brand_new

        # Calculate average transaction amount for account
        if all_account_txs:
            amounts = [tx.amount for tx in all_account_txs]
            avg_account_amount = sum(amounts) / len(amounts)
            max_account_amount = max(amounts)

            context["avg_account_transaction_amount"] = avg_account_amount
            context["max_account_transaction_amount"] = max_account_amount

            # Check if current transaction is unusually large for this account
            if current_amount > max_account_amount:
                context["current_exceeds_account_max"] = True
                context["account_max_exceeded_by"] = current_amount - max_account_amount
            else:
                context["current_exceeds_account_max"] = False

            # For new accounts, check if transaction is much larger than average
            if is_new and total_txs >= 3:
                if current_amount > avg_account_amount * 3:  # 3x average
                    risk_flags.append("new_account_amount_spike")
                    context["account_age_risk_flags"] = risk_flags
                    context["account_age_risk_flag_count"] = len(risk_flags)

        # Analyze account activity pattern
        # New accounts with burst activity are suspicious
        if is_new and total_txs > 0:
            # Calculate daily transaction rate
            daily_rate = total_txs / max(account_age_days, 1)

            if daily_rate >= 5:  # 5+ transactions per day
                context["account_high_activity_rate"] = True
                context["account_daily_transaction_rate"] = daily_rate
            else:
                context["account_high_activity_rate"] = False
                context["account_daily_transaction_rate"] = daily_rate
        else:
            context["account_high_activity_rate"] = False

        # Check for account warming pattern
        # Fraudsters often "warm up" accounts with small transactions before fraud
        if is_new and total_txs >= 5:
            small_tx_count = sum(1 for tx in all_account_txs if abs(tx.amount) <= 100)
            small_tx_percentage = (small_tx_count / total_txs) * 100

            # If 50%+ transactions are small, might be warming pattern
            if small_tx_percentage >= 50 and current_amount > 1000:
                risk_flags.append("account_warming_pattern")
                context["account_age_risk_flags"] = risk_flags
                context["account_age_risk_flag_count"] = len(risk_flags)
                context["account_warming_detected"] = True
                context["small_transaction_percentage"] = small_tx_percentage
            else:
                context["account_warming_detected"] = False
        else:
            context["account_warming_detected"] = False

    def _add_high_risk_transaction_times_context(self, context: Dict[str, Any],
                                                   account_id: str,
                                                   transaction: Dict[str, Any]) -> None:
        """
        Add high-risk transaction times detection for fraud analysis.

        Flags transactions occurring during non-business hours, unusual times,
        weekends, holidays, and detects timing pattern anomalies that may
        indicate account takeover or fraudulent activity.

        Args:
            context: Context dictionary to update
            account_id: Account identifier
            transaction: Current transaction data
        """
        import calendar
        from typing import List, Tuple

        now = datetime.datetime.utcnow()

        # Get transaction timestamp
        tx_timestamp_str = transaction.get("timestamp", now.isoformat())
        tx_timestamp = datetime.datetime.fromisoformat(tx_timestamp_str)
        tx_amount = abs(float(transaction.get("amount", 0)))

        # Extract time components
        tx_hour = tx_timestamp.hour
        tx_minute = tx_timestamp.minute
        tx_weekday = tx_timestamp.weekday()  # Monday=0, Sunday=6
        tx_day = tx_timestamp.day

        context["transaction_hour"] = tx_hour
        context["transaction_minute"] = tx_minute
        context["transaction_weekday"] = tx_weekday
        context["transaction_day_of_month"] = tx_day

        # Define time risk windows
        time_windows = {
            "deep_night": (0, 5),      # 12 AM - 5 AM (highest risk)
            "early_morning": (5, 7),   # 5 AM - 7 AM
            "morning": (7, 9),         # 7 AM - 9 AM
            "business_hours": (9, 17), # 9 AM - 5 PM (lowest risk)
            "evening": (17, 22),       # 5 PM - 10 PM
            "late_night": (22, 24)     # 10 PM - 12 AM (high risk)
        }

        # Determine current time window
        current_window = None
        for window_name, (start_hour, end_hour) in time_windows.items():
            if start_hour <= tx_hour < end_hour:
                current_window = window_name
                break

        context["time_window"] = current_window

        # Calculate base time risk score (0-100)
        # Deep night and late night have highest base risk
        time_risk_scores = {
            "deep_night": 85,
            "early_morning": 60,
            "morning": 30,
            "business_hours": 10,
            "evening": 25,
            "late_night": 70
        }

        base_time_risk = time_risk_scores.get(current_window, 50)
        context["base_time_risk_score"] = base_time_risk

        # Check weekend
        is_weekend = tx_weekday >= 5
        context["is_weekend"] = is_weekend

        # Check if holiday (US Federal Holidays for 2024-2025)
        def is_holiday(dt: datetime.datetime) -> Tuple[bool, str]:
            """Check if date is a US federal holiday"""
            year = dt.year
            month = dt.month
            day = dt.day

            # Fixed holidays
            fixed_holidays = {
                (1, 1): "New Year's Day",
                (7, 4): "Independence Day",
                (11, 11): "Veterans Day",
                (12, 25): "Christmas Day"
            }

            if (month, day) in fixed_holidays:
                return True, fixed_holidays[(month, day)]

            # MLK Day - 3rd Monday in January
            if month == 1 and tx_weekday == 0:
                if 15 <= day <= 21:
                    return True, "Martin Luther King Jr. Day"

            # Presidents Day - 3rd Monday in February
            if month == 2 and tx_weekday == 0:
                if 15 <= day <= 21:
                    return True, "Presidents Day"

            # Memorial Day - Last Monday in May
            if month == 5 and tx_weekday == 0:
                last_day = calendar.monthrange(year, 5)[1]
                if day > last_day - 7:
                    return True, "Memorial Day"

            # Labor Day - 1st Monday in September
            if month == 9 and tx_weekday == 0:
                if day <= 7:
                    return True, "Labor Day"

            # Columbus Day - 2nd Monday in October
            if month == 10 and tx_weekday == 0:
                if 8 <= day <= 14:
                    return True, "Columbus Day"

            # Thanksgiving - 4th Thursday in November
            if month == 11 and tx_weekday == 3:
                if 22 <= day <= 28:
                    return True, "Thanksgiving Day"

            return False, ""

        is_holiday_flag, holiday_name = is_holiday(tx_timestamp)
        context["is_holiday"] = is_holiday_flag
        context["holiday_name"] = holiday_name if is_holiday_flag else None

        # End of month pattern (fraudsters often target payroll dates)
        is_end_of_month = day >= 28 or day <= 3
        context["is_end_of_month"] = is_end_of_month

        # Get historical transactions for pattern analysis
        lookback_days = 90
        lookback_date = (now - datetime.timedelta(days=lookback_days)).isoformat()

        historical_txs = self.db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.timestamp > lookback_date
        ).all()

        context["historical_transaction_count_90d"] = len(historical_txs)

        if len(historical_txs) >= 5:  # Need minimum data
            # Analyze hourly patterns
            hour_distribution = [0] * 24
            weekday_distribution = [0] * 7
            weekend_tx_count = 0
            business_hours_count = 0
            non_business_hours_count = 0
            deep_night_count = 0
            holiday_count = 0

            for hist_tx in historical_txs:
                hist_time = datetime.datetime.fromisoformat(hist_tx.timestamp)
                hist_hour = hist_time.hour
                hist_weekday = hist_time.weekday()

                hour_distribution[hist_hour] += 1
                weekday_distribution[hist_weekday] += 1

                # Count weekend transactions
                if hist_weekday >= 5:
                    weekend_tx_count += 1

                # Count business hours vs non-business hours
                if 9 <= hist_hour < 17:
                    business_hours_count += 1
                else:
                    non_business_hours_count += 1

                # Count deep night transactions
                if 0 <= hist_hour < 5:
                    deep_night_count += 1

                # Count holiday transactions
                if is_holiday(hist_time)[0]:
                    holiday_count += 1

            total_hist = len(historical_txs)

            # Calculate pattern ratios
            context["historical_weekend_ratio"] = weekend_tx_count / total_hist
            context["historical_business_hours_ratio"] = business_hours_count / total_hist
            context["historical_non_business_hours_ratio"] = non_business_hours_count / total_hist
            context["historical_deep_night_ratio"] = deep_night_count / total_hist
            context["historical_holiday_ratio"] = holiday_count / total_hist

            # Calculate statistical metrics for timing
            import statistics

            # Convert hour distribution to percentage
            hour_percentages = [(count / total_hist) * 100 for count in hour_distribution]
            current_hour_percentage = hour_percentages[tx_hour]

            context["current_hour_historical_percentage"] = current_hour_percentage
            context["hour_distribution"] = hour_distribution

            # Determine if current time deviates from pattern
            avg_hour_percentage = 100 / 24  # ~4.17%

            # Flag if this hour is historically uncommon (less than 25% of average)
            hour_is_uncommon = current_hour_percentage < (avg_hour_percentage * 0.25)
            context["hour_is_uncommon"] = hour_is_uncommon

            # Flag if user typically transacts during business hours but this is off-hours
            deviates_from_business_hours_pattern = (
                context["historical_business_hours_ratio"] > 0.75 and
                current_window != "business_hours"
            )
            context["deviates_from_business_hours_pattern"] = deviates_from_business_hours_pattern

            # Flag if user rarely transacts on weekends but this is weekend
            deviates_from_weekday_pattern = (
                is_weekend and
                context["historical_weekend_ratio"] < 0.15
            )
            context["deviates_from_weekday_pattern"] = deviates_from_weekday_pattern

            # Detect sudden change in timing patterns (possible account takeover)
            # Look at last 7 days vs prior 83 days
            recent_cutoff = (now - datetime.timedelta(days=7)).isoformat()
            recent_txs = [tx for tx in historical_txs
                         if tx.timestamp > recent_cutoff]
            older_txs = [tx for tx in historical_txs
                        if tx.timestamp <= recent_cutoff]

            if len(recent_txs) >= 3 and len(older_txs) >= 5:
                # Compare timing patterns
                recent_business_hours = sum(1 for tx in recent_txs
                                          if 9 <= datetime.datetime.fromisoformat(tx.timestamp).hour < 17)
                older_business_hours = sum(1 for tx in older_txs
                                         if 9 <= datetime.datetime.fromisoformat(tx.timestamp).hour < 17)

                recent_bh_ratio = recent_business_hours / len(recent_txs)
                older_bh_ratio = older_business_hours / len(older_txs)

                # Significant shift in timing pattern (>40% change)
                timing_pattern_shift = abs(recent_bh_ratio - older_bh_ratio)
                context["timing_pattern_shift"] = timing_pattern_shift
                context["sudden_timing_change"] = timing_pattern_shift > 0.4

                # If recently shifted to odd hours, high risk
                context["shifted_to_odd_hours"] = (
                    recent_bh_ratio < 0.3 and older_bh_ratio > 0.7
                )
            else:
                context["timing_pattern_shift"] = 0
                context["sudden_timing_change"] = False
                context["shifted_to_odd_hours"] = False
        else:
            # Insufficient historical data
            context["insufficient_timing_history"] = True
            context["hour_is_uncommon"] = False
            context["deviates_from_business_hours_pattern"] = False
            context["deviates_from_weekday_pattern"] = False
            context["timing_pattern_shift"] = 0
            context["sudden_timing_change"] = False
            context["shifted_to_odd_hours"] = False

        # Analyze recent velocity at unusual times
        recent_7d_cutoff = (now - datetime.timedelta(days=7)).isoformat()
        recent_7d_txs = self.db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.timestamp > recent_7d_cutoff
        ).all()

        recent_deep_night_txs = []
        recent_weekend_txs = []
        recent_holiday_txs = []

        for tx in recent_7d_txs:
            tx_time = datetime.datetime.fromisoformat(tx.timestamp)
            tx_h = tx_time.hour
            tx_wd = tx_time.weekday()

            if 0 <= tx_h < 5:
                recent_deep_night_txs.append(tx)

            if tx_wd >= 5:
                recent_weekend_txs.append(tx)

            if is_holiday(tx_time)[0]:
                recent_holiday_txs.append(tx)

        context["recent_deep_night_transaction_count"] = len(recent_deep_night_txs)
        context["recent_weekend_transaction_count"] = len(recent_weekend_txs)
        context["recent_holiday_transaction_count"] = len(recent_holiday_txs)

        # Calculate total amounts for unusual times
        if recent_deep_night_txs:
            context["recent_deep_night_total_amount"] = sum(abs(tx.amount) for tx in recent_deep_night_txs)

        if recent_weekend_txs:
            context["recent_weekend_total_amount"] = sum(abs(tx.amount) for tx in recent_weekend_txs)

        if recent_holiday_txs:
            context["recent_holiday_total_amount"] = sum(abs(tx.amount) for tx in recent_holiday_txs)

        # Check for timezone anomalies (rapid location changes)
        # Look for transactions from different time zones in short period
        recent_24h_cutoff = (now - datetime.timedelta(hours=24)).isoformat()
        recent_24h_txs = self.db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.timestamp > recent_24h_cutoff
        ).order_by(Transaction.timestamp).all()

        if len(recent_24h_txs) >= 2:
            # Check if transactions show rapid timezone changes
            # (This is simplified - in production, you'd use actual location data)
            transaction_hours = [datetime.datetime.fromisoformat(tx.timestamp).hour
                               for tx in recent_24h_txs]

            # Look for unusual hour jumping (possible VPN/location spoofing)
            hour_jumps = []
            for i in range(1, len(transaction_hours)):
                jump = abs(transaction_hours[i] - transaction_hours[i-1])
                # Normalize for 24-hour wrap
                if jump > 12:
                    jump = 24 - jump
                hour_jumps.append(jump)

            if hour_jumps:
                max_hour_jump = max(hour_jumps)
                context["max_hour_jump_24h"] = max_hour_jump

                # Significant timezone jump (>6 hours) in 24h period
                context["rapid_timezone_change"] = max_hour_jump > 6
            else:
                context["max_hour_jump_24h"] = 0
                context["rapid_timezone_change"] = False
        else:
            context["max_hour_jump_24h"] = 0
            context["rapid_timezone_change"] = False

        # Generate risk flags
        risk_flags = []

        # Deep night transaction (12 AM - 5 AM)
        if current_window == "deep_night":
            risk_flags.append("deep_night_transaction")

            # Extra flag for midnight hour (12 AM - 1 AM)
            if tx_hour == 0:
                risk_flags.append("midnight_transaction")

        # Late night transaction (10 PM - 12 AM)
        if current_window == "late_night":
            risk_flags.append("late_night_transaction")

        # Weekend large transaction
        if is_weekend and tx_amount > 5000:
            risk_flags.append("weekend_large_transaction")

        # Weekend unusual (if user rarely transacts on weekends)
        if is_weekend and context.get("deviates_from_weekday_pattern", False):
            risk_flags.append("weekend_unusual_for_user")

        # Holiday transaction
        if is_holiday_flag:
            risk_flags.append("holiday_transaction")

            if tx_amount > 5000:
                risk_flags.append("holiday_large_transaction")

        # Outside business hours high value
        if current_window != "business_hours" and tx_amount > 10000:
            risk_flags.append("outside_business_hours_high_value")

        # Unusual time for user
        if context.get("hour_is_uncommon", False):
            risk_flags.append("unusual_time_for_user")

        # Deviates from business hours pattern
        if context.get("deviates_from_business_hours_pattern", False):
            risk_flags.append("deviates_from_typical_hours")

        # Rapid timezone change
        if context.get("rapid_timezone_change", False):
            risk_flags.append("rapid_timezone_change")

        # Sudden timing pattern change (possible account takeover)
        if context.get("sudden_timing_change", False):
            risk_flags.append("sudden_timing_pattern_change")

        # Shifted to odd hours recently
        if context.get("shifted_to_odd_hours", False):
            risk_flags.append("recently_shifted_to_odd_hours")

        # Consistent deep night activity (multiple in recent period)
        if context.get("recent_deep_night_transaction_count", 0) >= 3:
            risk_flags.append("consistent_deep_night_activity")

        # Multiple weekend transactions recently
        if context.get("recent_weekend_transaction_count", 0) >= 3:
            if context.get("historical_weekend_ratio", 1) < 0.2:
                risk_flags.append("unusual_weekend_activity_spike")

        # Early morning high value (5 AM - 7 AM with large amount)
        if current_window == "early_morning" and tx_amount > 7500:
            risk_flags.append("early_morning_high_value")

        context["high_risk_time_flags"] = risk_flags
        context["high_risk_time_flag_count"] = len(risk_flags)

        # Calculate comprehensive time-based risk score (0-100)
        risk_score = base_time_risk

        # Adjust for amount
        if tx_amount > 10000:
            risk_score += 15
        elif tx_amount > 5000:
            risk_score += 10
        elif tx_amount > 2000:
            risk_score += 5

        # Adjust for weekend
        if is_weekend:
            risk_score += 10

        # Adjust for holiday
        if is_holiday_flag:
            risk_score += 15

        # Adjust for pattern deviation
        if context.get("deviates_from_business_hours_pattern", False):
            risk_score += 20

        if context.get("hour_is_uncommon", False):
            risk_score += 15

        # Adjust for timezone anomaly
        if context.get("rapid_timezone_change", False):
            risk_score += 25

        # Adjust for sudden timing change (major red flag)
        if context.get("sudden_timing_change", False):
            risk_score += 30

        # Adjust for shifted to odd hours
        if context.get("shifted_to_odd_hours", False):
            risk_score += 35

        # Cap at 100
        risk_score = min(risk_score, 100)

        context["high_risk_time_score"] = risk_score

        # Risk classification
        if risk_score >= 75:
            time_risk_level = "critical"
        elif risk_score >= 60:
            time_risk_level = "high"
        elif risk_score >= 40:
            time_risk_level = "medium"
        elif risk_score >= 20:
            time_risk_level = "low"
        else:
            time_risk_level = "minimal"

        context["time_risk_level"] = time_risk_level

    def _add_past_fraud_flags_context(self, context: Dict[str, Any],
                                       account_id: str,
                                       transaction: Dict[str, Any]) -> None:
        """
        Add past fraudulent behavior flags detection for fraud analysis.

        Checks if the user or recipient has been flagged for prior fraudulent
        activity, including fraud type, severity, recency, and patterns of
        repeat offenses.

        Args:
            context: Context dictionary to update
            account_id: Account identifier
            transaction: Current transaction data
        """
        now = datetime.datetime.utcnow()
        tx_amount = abs(float(transaction.get("amount", 0)))

        # Get beneficiary/recipient ID
        beneficiary_id = transaction.get("beneficiary_id") or transaction.get("recipient_id")

        # Initialize fraud history containers
        context["account_has_fraud_history"] = False
        context["beneficiary_has_fraud_history"] = False
        context["combined_fraud_risk_score"] = 0

        # Query account fraud flags
        account_fraud_flags = self.db.query(FraudFlag).filter(
            FraudFlag.entity_type == "account",
            FraudFlag.entity_id == account_id
        ).order_by(FraudFlag.incident_date.desc()).all()

        if account_fraud_flags:
            context["account_has_fraud_history"] = True
            context["account_total_fraud_flags"] = len(account_fraud_flags)

            # Categorize by status
            active_flags = [f for f in account_fraud_flags if f.status == "active"]
            confirmed_flags = [f for f in account_fraud_flags if f.disposition == "confirmed_fraud"]
            resolved_flags = [f for f in account_fraud_flags if f.status == "resolved"]
            disputed_flags = [f for f in account_fraud_flags if f.status == "disputed"]

            context["account_active_fraud_flags"] = len(active_flags)
            context["account_confirmed_fraud_flags"] = len(confirmed_flags)
            context["account_resolved_fraud_flags"] = len(resolved_flags)
            context["account_disputed_fraud_flags"] = len(disputed_flags)

            # Categorize by severity
            critical_flags = [f for f in account_fraud_flags if f.severity == "critical"]
            high_flags = [f for f in account_fraud_flags if f.severity == "high"]
            medium_flags = [f for f in account_fraud_flags if f.severity == "medium"]
            low_flags = [f for f in account_fraud_flags if f.severity == "low"]

            context["account_critical_fraud_flags"] = len(critical_flags)
            context["account_high_fraud_flags"] = len(high_flags)
            context["account_medium_fraud_flags"] = len(medium_flags)
            context["account_low_fraud_flags"] = len(low_flags)

            # Get fraud types and categories
            fraud_types = list(set([f.fraud_type for f in account_fraud_flags]))
            fraud_categories = list(set([f.fraud_category for f in account_fraud_flags]))

            context["account_fraud_types"] = fraud_types
            context["account_fraud_categories"] = fraud_categories
            context["account_unique_fraud_types"] = len(fraud_types)

            # Analyze recency of most recent fraud
            most_recent_flag = account_fraud_flags[0]  # Already sorted by incident_date desc
            days_since_last_fraud = (now - most_recent_flag.incident_date).days

            context["account_days_since_last_fraud"] = days_since_last_fraud
            context["account_most_recent_fraud_type"] = most_recent_flag.fraud_type
            context["account_most_recent_fraud_severity"] = most_recent_flag.severity
            context["account_most_recent_fraud_status"] = most_recent_flag.status

            # Recency classification
            if days_since_last_fraud <= 7:
                recency_category = "very_recent"
            elif days_since_last_fraud <= 30:
                recency_category = "recent"
            elif days_since_last_fraud <= 90:
                recency_category = "moderately_recent"
            elif days_since_last_fraud <= 180:
                recency_category = "somewhat_recent"
            elif days_since_last_fraud <= 365:
                recency_category = "past_year"
            else:
                recency_category = "historical"

            context["account_fraud_recency_category"] = recency_category

            # Calculate total amount involved in past fraud
            total_fraud_amount = sum(float(f.amount_involved or 0) for f in account_fraud_flags
                                    if f.amount_involved is not None)
            context["account_total_fraud_amount"] = total_fraud_amount

            # Analyze fraud patterns
            # Check for repeat fraud (multiple incidents within time windows)
            fraud_last_30d = [f for f in account_fraud_flags
                             if (now - f.incident_date).days <= 30]
            fraud_last_90d = [f for f in account_fraud_flags
                             if (now - f.incident_date).days <= 90]
            fraud_last_365d = [f for f in account_fraud_flags
                              if (now - f.incident_date).days <= 365]

            context["account_fraud_flags_last_30d"] = len(fraud_last_30d)
            context["account_fraud_flags_last_90d"] = len(fraud_last_90d)
            context["account_fraud_flags_last_365d"] = len(fraud_last_365d)

            # Check for escalating pattern (increasing severity over time)
            severity_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}

            if len(account_fraud_flags) >= 2:
                # Compare recent vs older incidents
                recent_avg_severity = sum(severity_scores.get(f.severity, 0)
                                        for f in fraud_last_90d) / len(fraud_last_90d) if fraud_last_90d else 0

                older_flags = [f for f in account_fraud_flags
                              if (now - f.incident_date).days > 90]
                older_avg_severity = sum(severity_scores.get(f.severity, 0)
                                       for f in older_flags) / len(older_flags) if older_flags else 0

                escalating_pattern = recent_avg_severity > older_avg_severity and recent_avg_severity >= 2.5
                context["account_fraud_escalating_pattern"] = escalating_pattern
            else:
                context["account_fraud_escalating_pattern"] = False

            # Check if account was previously closed for fraud and reopened
            account_closed_flags = [f for f in account_fraud_flags
                                   if f.resolution_action == "account_closed"]
            context["account_previously_closed_for_fraud"] = len(account_closed_flags) > 0

            # Check for specific high-risk fraud types
            high_risk_fraud_types = [
                "identity_theft",
                "account_takeover",
                "money_laundering",
                "terrorist_financing",
                "synthetic_identity",
                "credit_card_fraud"
            ]

            has_high_risk_type = any(f.fraud_type.lower() in [t.lower() for t in high_risk_fraud_types]
                                    for f in account_fraud_flags)
            context["account_has_high_risk_fraud_type"] = has_high_risk_type

        else:
            # No fraud history for account
            context["account_total_fraud_flags"] = 0
            context["account_active_fraud_flags"] = 0
            context["account_confirmed_fraud_flags"] = 0
            context["account_fraud_types"] = []
            context["account_fraud_categories"] = []
            context["account_days_since_last_fraud"] = None
            context["account_fraud_recency_category"] = "none"
            context["account_total_fraud_amount"] = 0
            context["account_fraud_flags_last_30d"] = 0
            context["account_fraud_flags_last_90d"] = 0
            context["account_fraud_flags_last_365d"] = 0
            context["account_fraud_escalating_pattern"] = False
            context["account_previously_closed_for_fraud"] = False
            context["account_has_high_risk_fraud_type"] = False

        # Query beneficiary/recipient fraud flags
        if beneficiary_id:
            beneficiary_fraud_flags = self.db.query(FraudFlag).filter(
                FraudFlag.entity_type == "beneficiary",
                FraudFlag.entity_id == beneficiary_id
            ).order_by(FraudFlag.incident_date.desc()).all()

            if beneficiary_fraud_flags:
                context["beneficiary_has_fraud_history"] = True
                context["beneficiary_total_fraud_flags"] = len(beneficiary_fraud_flags)

                # Categorize by status
                ben_active_flags = [f for f in beneficiary_fraud_flags if f.status == "active"]
                ben_confirmed_flags = [f for f in beneficiary_fraud_flags if f.disposition == "confirmed_fraud"]

                context["beneficiary_active_fraud_flags"] = len(ben_active_flags)
                context["beneficiary_confirmed_fraud_flags"] = len(ben_confirmed_flags)

                # Categorize by severity
                ben_critical_flags = [f for f in beneficiary_fraud_flags if f.severity == "critical"]
                ben_high_flags = [f for f in beneficiary_fraud_flags if f.severity == "high"]

                context["beneficiary_critical_fraud_flags"] = len(ben_critical_flags)
                context["beneficiary_high_fraud_flags"] = len(ben_high_flags)

                # Get fraud types
                ben_fraud_types = list(set([f.fraud_type for f in beneficiary_fraud_flags]))
                context["beneficiary_fraud_types"] = ben_fraud_types

                # Recency of most recent fraud
                ben_most_recent = beneficiary_fraud_flags[0]
                ben_days_since_last = (now - ben_most_recent.incident_date).days

                context["beneficiary_days_since_last_fraud"] = ben_days_since_last
                context["beneficiary_most_recent_fraud_type"] = ben_most_recent.fraud_type
                context["beneficiary_most_recent_fraud_severity"] = ben_most_recent.severity

                # Recency classification
                if ben_days_since_last <= 30:
                    ben_recency = "recent"
                elif ben_days_since_last <= 90:
                    ben_recency = "moderately_recent"
                elif ben_days_since_last <= 365:
                    ben_recency = "past_year"
                else:
                    ben_recency = "historical"

                context["beneficiary_fraud_recency_category"] = ben_recency

                # Total amount
                ben_total_amount = sum(float(f.amount_involved or 0) for f in beneficiary_fraud_flags
                                      if f.amount_involved is not None)
                context["beneficiary_total_fraud_amount"] = ben_total_amount

                # Recent activity
                ben_fraud_last_90d = [f for f in beneficiary_fraud_flags
                                     if (now - f.incident_date).days <= 90]
                context["beneficiary_fraud_flags_last_90d"] = len(ben_fraud_last_90d)

            else:
                # No fraud history for beneficiary
                context["beneficiary_total_fraud_flags"] = 0
                context["beneficiary_active_fraud_flags"] = 0
                context["beneficiary_confirmed_fraud_flags"] = 0
                context["beneficiary_fraud_types"] = []
                context["beneficiary_days_since_last_fraud"] = None
                context["beneficiary_fraud_recency_category"] = "none"
                context["beneficiary_total_fraud_amount"] = 0
                context["beneficiary_fraud_flags_last_90d"] = 0
        else:
            # No beneficiary in transaction
            context["beneficiary_total_fraud_flags"] = 0
            context["beneficiary_active_fraud_flags"] = 0
            context["beneficiary_fraud_types"] = []
            context["beneficiary_fraud_recency_category"] = "none"

        # Generate combined risk flags
        risk_flags = []

        # Account has active fraud flags
        if context.get("account_active_fraud_flags", 0) > 0:
            risk_flags.append("account_has_active_fraud_flags")

        # Account has confirmed fraud
        if context.get("account_confirmed_fraud_flags", 0) > 0:
            risk_flags.append("account_has_confirmed_fraud")

        # Account has critical severity fraud
        if context.get("account_critical_fraud_flags", 0) > 0:
            risk_flags.append("account_has_critical_fraud")

        # Recent fraud (within 30 days)
        if context.get("account_fraud_recency_category") in ["very_recent", "recent"]:
            risk_flags.append("account_very_recent_fraud")

        # Multiple fraud incidents
        if context.get("account_total_fraud_flags", 0) >= 3:
            risk_flags.append("account_repeat_fraud_offender")

        # Escalating fraud pattern
        if context.get("account_fraud_escalating_pattern", False):
            risk_flags.append("account_fraud_escalating")

        # Previously closed for fraud
        if context.get("account_previously_closed_for_fraud", False):
            risk_flags.append("account_previously_closed_for_fraud")

        # High-risk fraud type
        if context.get("account_has_high_risk_fraud_type", False):
            risk_flags.append("account_high_risk_fraud_type")

        # Recent fraud activity (multiple in 90 days)
        if context.get("account_fraud_flags_last_90d", 0) >= 2:
            risk_flags.append("account_recent_fraud_activity")

        # Beneficiary has active fraud
        if context.get("beneficiary_active_fraud_flags", 0) > 0:
            risk_flags.append("beneficiary_has_active_fraud_flags")

        # Beneficiary has confirmed fraud
        if context.get("beneficiary_confirmed_fraud_flags", 0) > 0:
            risk_flags.append("beneficiary_has_confirmed_fraud")

        # Beneficiary has critical fraud
        if context.get("beneficiary_critical_fraud_flags", 0) > 0:
            risk_flags.append("beneficiary_has_critical_fraud")

        # Beneficiary recent fraud
        if context.get("beneficiary_fraud_recency_category") in ["recent", "moderately_recent"]:
            risk_flags.append("beneficiary_recent_fraud")

        # Both parties have fraud history
        if context.get("account_has_fraud_history") and context.get("beneficiary_has_fraud_history"):
            risk_flags.append("both_parties_have_fraud_history")

        # Large transaction from account with fraud history
        if context.get("account_has_fraud_history") and tx_amount > 5000:
            risk_flags.append("large_transaction_fraud_history_account")

        # Transaction to beneficiary with fraud history
        if context.get("beneficiary_has_fraud_history") and tx_amount > 2000:
            risk_flags.append("transaction_to_fraud_history_beneficiary")

        # Fraud history with similar transaction patterns
        if context.get("account_has_fraud_history"):
            # Check if past fraud involved similar amounts
            account_fraud_amounts = [float(f.amount_involved) for f in account_fraud_flags
                                    if f.amount_involved is not None and float(f.amount_involved) > 0]

            if account_fraud_amounts:
                import statistics
                avg_fraud_amount = statistics.mean(account_fraud_amounts)

                # If current transaction is within 20% of average fraud amount
                if avg_fraud_amount > 0:
                    similarity_ratio = abs(tx_amount - avg_fraud_amount) / avg_fraud_amount
                    if similarity_ratio < 0.2:
                        risk_flags.append("transaction_similar_to_past_fraud_amount")

        context["past_fraud_risk_flags"] = risk_flags
        context["past_fraud_risk_flag_count"] = len(risk_flags)

        # Calculate comprehensive past fraud risk score (0-100)
        risk_score = 0

        # Account fraud history scoring
        if context.get("account_has_fraud_history"):
            # Base score for having fraud history
            risk_score += 20

            # Add for active flags
            risk_score += min(context.get("account_active_fraud_flags", 0) * 15, 45)

            # Add for confirmed fraud
            risk_score += min(context.get("account_confirmed_fraud_flags", 0) * 10, 30)

            # Add for severity
            risk_score += context.get("account_critical_fraud_flags", 0) * 20
            risk_score += context.get("account_high_fraud_flags", 0) * 10

            # Add for recency
            recency_scores = {
                "very_recent": 35,
                "recent": 25,
                "moderately_recent": 15,
                "somewhat_recent": 10,
                "past_year": 5,
                "historical": 2
            }
            risk_score += recency_scores.get(context.get("account_fraud_recency_category"), 0)

            # Add for repeat offenses
            if context.get("account_total_fraud_flags", 0) >= 5:
                risk_score += 25
            elif context.get("account_total_fraud_flags", 0) >= 3:
                risk_score += 15

            # Add for escalating pattern
            if context.get("account_fraud_escalating_pattern", False):
                risk_score += 20

            # Add for previously closed
            if context.get("account_previously_closed_for_fraud", False):
                risk_score += 30

            # Add for high-risk type
            if context.get("account_has_high_risk_fraud_type", False):
                risk_score += 25

        # Beneficiary fraud history scoring
        if context.get("beneficiary_has_fraud_history"):
            # Base score for beneficiary fraud
            risk_score += 15

            # Add for active/confirmed
            risk_score += min(context.get("beneficiary_active_fraud_flags", 0) * 10, 30)
            risk_score += min(context.get("beneficiary_confirmed_fraud_flags", 0) * 8, 24)

            # Add for severity
            risk_score += context.get("beneficiary_critical_fraud_flags", 0) * 15

            # Add for recency
            ben_recency_scores = {
                "recent": 20,
                "moderately_recent": 12,
                "past_year": 6,
                "historical": 2
            }
            risk_score += ben_recency_scores.get(context.get("beneficiary_fraud_recency_category"), 0)

        # Add for both parties having fraud history
        if context.get("account_has_fraud_history") and context.get("beneficiary_has_fraud_history"):
            risk_score += 30

        # Cap at 100
        risk_score = min(risk_score, 100)

        context["past_fraud_risk_score"] = risk_score

        # Risk classification
        if risk_score >= 80:
            fraud_risk_level = "critical"
        elif risk_score >= 60:
            fraud_risk_level = "high"
        elif risk_score >= 40:
            fraud_risk_level = "medium"
        elif risk_score >= 20:
            fraud_risk_level = "low"
        else:
            fraud_risk_level = "minimal"

        context["past_fraud_risk_level"] = fraud_risk_level
