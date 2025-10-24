# app/services/context_provider.py
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import json
import datetime
from app.models.database import Transaction, Account, Employee, AccountChangeHistory
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

        # Add chain analysis if enabled
        if self.enable_chain_analysis and self.chain_analyzer:
            chain_analysis = self.chain_analyzer.analyze_transaction_chains(
                account_id, transaction
            )
            context["chain_analysis"] = chain_analysis

        # Add account takeover detection context
        self._add_account_takeover_context(context, account_id, transaction)

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
