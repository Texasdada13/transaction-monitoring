# app/services/context_provider.py
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import json
import datetime
from app.models.database import Transaction, Account, Employee, AccountChangeHistory, Beneficiary, Blacklist, DeviceSession, VPNProxyIP, HighRiskLocation, BehavioralBiometric
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
