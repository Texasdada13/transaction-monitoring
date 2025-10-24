# app/services/context_provider.py
from typing import Dict, Any
from sqlalchemy.orm import Session
import json
import datetime
from app.models.database import Transaction, Account, Employee, AccountChangeHistory

class ContextProvider:
    def __init__(self, db: Session):
        """
        Initialize context provider with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
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
        
        return context
    
    def _add_transaction_history(self, context: Dict[str, Any], 
                                account_id: str, 
                                current_tx: Dict[str, Any]) -> None:
        """Add transaction history data to context."""
        # Transaction velocity for different time windows
        timeframes = [1, 6, 24, 168]  # hours (1h, 6h, 24h, 1 week)
        context["tx_count_last_hours"] = {}
        
        now = datetime.datetime.utcnow()
        for hours in timeframes:
            time_threshold = (now - datetime.timedelta(hours=hours)).isoformat()
            
            count = self.db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.timestamp > time_threshold
            ).count()
            
            context["tx_count_last_hours"][hours] = count
        
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